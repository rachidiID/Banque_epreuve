"""
Predictor for making recommendations in production
Handles model loading and inference
"""
import torch
import pickle
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from apps.core.models import Epreuve, Interaction
from .ncf_model import NCFModel
import logging

logger = logging.getLogger(__name__)


class NCFPredictor:
    """
    Production predictor for NCF model
    Handles model loading, caching, and recommendations
    """
    
    def __init__(self, model_path=None, mappings_path=None):
        """
        Initialize predictor
        
        Args:
            model_path (str): Path to the trained model
            mappings_path (str): Path to the ID mappings file
        """
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # ID mappings
        self.user_id_to_idx = {}
        self.idx_to_user_id = {}
        self.item_id_to_idx = {}
        self.idx_to_item_id = {}
        
        # Paths
        self.model_path = model_path or self._get_default_model_path()
        self.mappings_path = mappings_path or self._get_default_mappings_path()
        
        # Cache settings
        self.cache_timeout = 3600  # 1 hour
        self.cache_enabled = True
    
    def _get_default_model_path(self):
        """Get default model path from settings"""
        return Path(settings.BASE_DIR) / settings.ML_MODEL_PATH
    
    def _get_default_mappings_path(self):
        """Get default mappings path"""
        model_dir = Path(settings.BASE_DIR) / 'ml_models'
        return model_dir / 'id_mappings.pkl'
    
    def load_model(self):
        """
        Load trained model and mappings
        """
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        # Load checkpoint
        checkpoint = torch.load(self.model_path, map_location=self.device)
        
        # Initialize model
        num_users = checkpoint['num_users']
        num_items = checkpoint['num_items']
        embedding_dim = checkpoint['embedding_dim']
        
        self.model = NCFModel(num_users, num_items, embedding_dim)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        # Load ID mappings
        if self.mappings_path.exists():
            with open(self.mappings_path, 'rb') as f:
                mappings = pickle.load(f)
                self.user_id_to_idx = mappings['user_id_to_idx']
                self.idx_to_user_id = mappings['idx_to_user_id']
                self.item_id_to_idx = mappings['item_id_to_idx']
                self.idx_to_item_id = mappings['idx_to_item_id']
        else:
            logger.warning(f"Mappings file not found at {self.mappings_path}")
        
        logger.info(f"Model loaded successfully from {self.model_path}")
    
    def is_model_loaded(self):
        """Check if model is loaded"""
        return self.model is not None
    
    def predict_rating(self, user_db_id, item_db_id):
        """
        Predict rating for a user-item pair
        
        Args:
            user_db_id (int): Database user ID
            item_db_id (int): Database item ID
        
        Returns:
            float: Predicted rating
        """
        if not self.is_model_loaded():
            self.load_model()
        
        # Convert database IDs to indices
        user_idx = self.user_id_to_idx.get(user_db_id)
        item_idx = self.item_id_to_idx.get(item_db_id)
        
        if user_idx is None or item_idx is None:
            return 0.0  # Return default score for unknown users/items
        
        # Make prediction
        with torch.no_grad():
            user_tensor = torch.tensor([user_idx], dtype=torch.long).to(self.device)
            item_tensor = torch.tensor([item_idx], dtype=torch.long).to(self.device)
            
            prediction = self.model(user_tensor, item_tensor)
            score = prediction.item()
        
        return score
    
    def recommend_for_user(self, user_db_id, top_k=10, exclude_seen=True, filter_by_niveau=True):
        """
        Generate top-K recommendations for a user
        
        Args:
            user_db_id (int): Database user ID
            top_k (int): Number of recommendations to return
            exclude_seen (bool): Exclude items the user has already interacted with
            filter_by_niveau (bool): Filter recommendations by user's niveau
        
        Returns:
            list: List of tuples (epreuve_id, score, epreuve_obj)
        """
        # Check cache first
        cache_key = f"recommendations:user_{user_db_id}:k_{top_k}"
        if self.cache_enabled:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        if not self.is_model_loaded():
            self.load_model()
        
        # Convert user ID
        user_idx = self.user_id_to_idx.get(user_db_id)
        if user_idx is None:
            # New user - return popular items
            return self._get_popular_items(top_k, user_db_id if filter_by_niveau else None)
        
        # Get all available items
        all_item_indices = list(self.item_id_to_idx.values())
        
        # Get items to exclude
        excluded_items = set()
        if exclude_seen:
            seen_epreuves = Interaction.objects.filter(
                user_id=user_db_id
            ).values_list('epreuve_id', flat=True)
            
            excluded_items = {
                self.item_id_to_idx.get(epreuve_id) 
                for epreuve_id in seen_epreuves 
                if self.item_id_to_idx.get(epreuve_id) is not None
            }
        
        # Filter items
        candidate_items = [idx for idx in all_item_indices if idx not in excluded_items]
        
        if not candidate_items:
            # All items seen, return popular unseen ones or just popular
            return self._get_popular_items(top_k, user_db_id if filter_by_niveau else None)
        
        # Make predictions
        with torch.no_grad():
            user_tensor = torch.tensor([user_idx] * len(candidate_items), dtype=torch.long).to(self.device)
            item_tensor = torch.tensor(candidate_items, dtype=torch.long).to(self.device)
            
            predictions = self.model(user_tensor, item_tensor).squeeze()
            
            if len(candidate_items) == 1:
                predictions = predictions.unsqueeze(0)
        
        # Get top-K
        k = min(top_k, len(predictions))
        top_scores, top_indices = torch.topk(predictions, k)
        
        # Convert indices to database IDs
        recommendations = []
        for idx, score in zip(top_indices.cpu().numpy(), top_scores.cpu().numpy()):
            item_idx = candidate_items[idx]
            epreuve_id = self.idx_to_item_id.get(item_idx)
            
            if epreuve_id:
                try:
                    epreuve = Epreuve.objects.get(id=epreuve_id)
                    
                    # Filter by niveau if requested
                    if filter_by_niveau:
                        from apps.core.models import User
                        user = User.objects.get(id=user_db_id)
                        if user.niveau and epreuve.niveau > user.niveau:
                            continue
                    
                    recommendations.append((epreuve_id, float(score), epreuve))
                except Epreuve.DoesNotExist:
                    continue
        
        # If not enough recommendations, add popular items
        if len(recommendations) < top_k:
            popular = self._get_popular_items(
                top_k - len(recommendations), 
                user_db_id if filter_by_niveau else None
            )
            recommendations.extend(popular)
        
        # Cache results
        if self.cache_enabled:
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations[:top_k]
    
    def recommend_similar_items(self, item_db_id, top_k=10):
        """
        Find similar items based on embeddings
        
        Args:
            item_db_id (int): Database item ID
            top_k (int): Number of similar items to return
        
        Returns:
            list: List of similar epreuve IDs with similarity scores
        """
        if not self.is_model_loaded():
            self.load_model()
        
        item_idx = self.item_id_to_idx.get(item_db_id)
        if item_idx is None:
            return []
        
        # Get item embedding
        target_embedding = self.model.get_item_embedding(item_idx).to(self.device)
        
        # Get all item embeddings
        all_item_indices = list(self.item_id_to_idx.values())
        similarities = []
        
        with torch.no_grad():
            for idx in all_item_indices:
                if idx == item_idx:
                    continue
                
                item_embedding = self.model.get_item_embedding(idx).to(self.device)
                
                # Cosine similarity
                similarity = torch.nn.functional.cosine_similarity(
                    target_embedding.unsqueeze(0), 
                    item_embedding.unsqueeze(0)
                ).item()
                
                similarities.append((idx, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to database IDs
        similar_items = []
        for item_idx, score in similarities[:top_k]:
            epreuve_id = self.idx_to_item_id.get(item_idx)
            if epreuve_id:
                try:
                    epreuve = Epreuve.objects.get(id=epreuve_id)
                    similar_items.append((epreuve_id, score, epreuve))
                except Epreuve.DoesNotExist:
                    continue
        
        return similar_items
    
    def _get_popular_items(self, top_k, user_db_id=None):
        """
        Get popular items as fallback
        
        Args:
            top_k (int): Number of items to return
            user_db_id (int, optional): User ID for niveau filtering
        
        Returns:
            list: List of popular epreuves
        """
        queryset = Epreuve.objects.all()
        
        # Filter by niveau if user provided
        if user_db_id:
            try:
                from apps.core.models import User
                user = User.objects.get(id=user_db_id)
                if user.niveau:
                    queryset = queryset.filter(niveau__lte=user.niveau)
            except User.DoesNotExist:
                pass
        
        # Order by popularity
        popular_epreuves = queryset.order_by('-nb_telechargements', '-nb_vues')[:top_k]
        
        results = []
        for epreuve in popular_epreuves:
            # Use a default score based on popularity
            score = (epreuve.nb_telechargements * 2 + epreuve.nb_vues) / 100.0
            results.append((epreuve.id, score, epreuve))
        
        return results
    
    def invalidate_cache(self, user_db_id=None):
        """
        Invalidate recommendations cache
        
        Args:
            user_db_id (int, optional): Specific user to invalidate, or None for all
        """
        if user_db_id:
            # Invalidate specific user's cache
            cache_pattern = f"recommendations:user_{user_db_id}:*"
            cache.delete_pattern(cache_pattern)
        else:
            # Invalidate all recommendation caches
            cache.delete_pattern("recommendations:*")
        
        logger.info(f"Cache invalidated for user {user_db_id or 'all'}")


# Singleton instance
_predictor_instance = None


def get_predictor():
    """
    Get singleton predictor instance
    
    Returns:
        NCFPredictor: Predictor instance
    """
    global _predictor_instance
    
    if _predictor_instance is None:
        _predictor_instance = NCFPredictor()
    
    return _predictor_instance
