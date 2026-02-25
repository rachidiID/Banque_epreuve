"""
Neural Collaborative Filtering (NCF) Model
Combines Matrix Factorization and Multi-Layer Perceptron for recommendations
"""
import torch
import torch.nn as nn


class NCFModel(nn.Module):
    """
    Neural Collaborative Filtering model combining GMF and MLP
    
    Architecture:
    - GMF (Generalized Matrix Factorization): element-wise product of user/item embeddings
    - MLP (Multi-Layer Perceptron): deep neural network on concatenated embeddings
    - NeuMF: combination of GMF and MLP predictions
    """
    
    def __init__(self, num_users, num_items, embedding_dim=64, mlp_layers=[128, 64, 32], dropout=0.2):
        """
        Initialize NCF model
        
        Args:
            num_users (int): Total number of users
            num_items (int): Total number of items (epreuves)
            embedding_dim (int): Dimension of embeddings (default: 64)
            mlp_layers (list): List of hidden layer sizes for MLP (default: [128, 64, 32])
            dropout (float): Dropout rate (default: 0.2)
        """
        super(NCFModel, self).__init__()
        
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        
        # GMF part - Generalized Matrix Factorization
        self.user_embedding_gmf = nn.Embedding(num_users, embedding_dim)
        self.item_embedding_gmf = nn.Embedding(num_items, embedding_dim)
        
        # MLP part - Multi-Layer Perceptron
        self.user_embedding_mlp = nn.Embedding(num_users, embedding_dim)
        self.item_embedding_mlp = nn.Embedding(num_items, embedding_dim)
        
        # MLP layers
        self.mlp_layers = nn.ModuleList()
        input_size = embedding_dim * 2  # Concatenation of user and item embeddings
        
        for i, layer_size in enumerate(mlp_layers):
            self.mlp_layers.append(nn.Linear(input_size, layer_size))
            self.mlp_layers.append(nn.ReLU())
            self.mlp_layers.append(nn.Dropout(dropout))
            input_size = layer_size
        
        # Final prediction layer
        # Combines GMF and MLP outputs
        self.final_layer = nn.Linear(embedding_dim + mlp_layers[-1], 1)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize model weights using Xavier uniform initialization"""
        nn.init.xavier_uniform_(self.user_embedding_gmf.weight)
        nn.init.xavier_uniform_(self.item_embedding_gmf.weight)
        nn.init.xavier_uniform_(self.user_embedding_mlp.weight)
        nn.init.xavier_uniform_(self.item_embedding_mlp.weight)
        
        for layer in self.mlp_layers:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.zeros_(layer.bias)
        
        nn.init.xavier_uniform_(self.final_layer.weight)
        nn.init.zeros_(self.final_layer.bias)
    
    def forward(self, user_ids, item_ids):
        """
        Forward pass
        
        Args:
            user_ids (torch.Tensor): User IDs tensor of shape (batch_size,)
            item_ids (torch.Tensor): Item IDs tensor of shape (batch_size,)
        
        Returns:
            torch.Tensor: Predicted ratings of shape (batch_size, 1)
        """
        # GMF part
        user_emb_gmf = self.user_embedding_gmf(user_ids)
        item_emb_gmf = self.item_embedding_gmf(item_ids)
        gmf_output = user_emb_gmf * item_emb_gmf  # Element-wise product
        
        # MLP part
        user_emb_mlp = self.user_embedding_mlp(user_ids)
        item_emb_mlp = self.item_embedding_mlp(item_ids)
        mlp_input = torch.cat([user_emb_mlp, item_emb_mlp], dim=-1)
        
        mlp_output = mlp_input
        for layer in self.mlp_layers:
            mlp_output = layer(mlp_output)
        
        # Combine GMF and MLP
        combined = torch.cat([gmf_output, mlp_output], dim=-1)
        
        # Final prediction
        prediction = self.final_layer(combined)
        
        return prediction
    
    def predict(self, user_ids, item_ids):
        """
        Make predictions (for inference)
        
        Args:
            user_ids (torch.Tensor): User IDs
            item_ids (torch.Tensor): Item IDs
        
        Returns:
            torch.Tensor: Predicted ratings
        """
        self.eval()
        with torch.no_grad():
            predictions = self.forward(user_ids, item_ids)
        return predictions.squeeze()
    
    def get_user_embedding(self, user_id):
        """
        Get combined user embedding
        
        Args:
            user_id (int): User ID
        
        Returns:
            torch.Tensor: User embedding vector
        """
        self.eval()
        with torch.no_grad():
            user_tensor = torch.tensor([user_id], dtype=torch.long)
            gmf_emb = self.user_embedding_gmf(user_tensor)
            mlp_emb = self.user_embedding_mlp(user_tensor)
            combined = torch.cat([gmf_emb, mlp_emb], dim=-1)
        return combined.squeeze()
    
    def get_item_embedding(self, item_id):
        """
        Get combined item embedding
        
        Args:
            item_id (int): Item ID
        
        Returns:
            torch.Tensor: Item embedding vector
        """
        self.eval()
        with torch.no_grad():
            item_tensor = torch.tensor([item_id], dtype=torch.long)
            gmf_emb = self.item_embedding_gmf(item_tensor)
            mlp_emb = self.item_embedding_mlp(item_tensor)
            combined = torch.cat([gmf_emb, mlp_emb], dim=-1)
        return combined.squeeze()
    
    def recommend_for_user(self, user_id, all_item_ids, top_k=10):
        """
        Generate top-K recommendations for a user
        
        Args:
            user_id (int): User ID
            all_item_ids (list or torch.Tensor): List of all available item IDs
            top_k (int): Number of recommendations to return
        
        Returns:
            tuple: (top_item_ids, top_scores)
        """
        self.eval()
        with torch.no_grad():
            user_tensor = torch.tensor([user_id] * len(all_item_ids), dtype=torch.long)
            item_tensor = torch.tensor(all_item_ids, dtype=torch.long)
            
            predictions = self.forward(user_tensor, item_tensor).squeeze()
            
            # Get top-K items
            top_scores, top_indices = torch.topk(predictions, min(top_k, len(predictions)))
            top_item_ids = [all_item_ids[idx] for idx in top_indices.tolist()]
        
        return top_item_ids, top_scores.tolist()


class SimpleMFModel(nn.Module):
    """
    Simplified Matrix Factorization model for baseline comparison
    """
    
    def __init__(self, num_users, num_items, embedding_dim=64):
        super(SimpleMFModel, self).__init__()
        
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        self.user_bias = nn.Embedding(num_users, 1)
        self.item_bias = nn.Embedding(num_items, 1)
        self.global_bias = nn.Parameter(torch.zeros(1))
        
        # Initialize
        nn.init.xavier_uniform_(self.user_embedding.weight)
        nn.init.xavier_uniform_(self.item_embedding.weight)
        nn.init.zeros_(self.user_bias.weight)
        nn.init.zeros_(self.item_bias.weight)
    
    def forward(self, user_ids, item_ids):
        user_emb = self.user_embedding(user_ids)
        item_emb = self.item_embedding(item_ids)
        
        dot_product = (user_emb * item_emb).sum(dim=-1, keepdim=True)
        
        user_b = self.user_bias(user_ids)
        item_b = self.item_bias(item_ids)
        
        prediction = dot_product + user_b + item_b + self.global_bias
        
        return prediction
