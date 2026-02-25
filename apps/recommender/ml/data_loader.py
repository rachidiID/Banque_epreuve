"""
Data Loader for training the NCF model
Prepares interaction data from database for PyTorch training
"""
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model
from apps.core.models import Interaction, Epreuve
from sklearn.model_selection import train_test_split

User = get_user_model()


class InteractionDataset(Dataset):
    """
    PyTorch Dataset for user-item interactions
    """
    
    def __init__(self, user_ids, item_ids, ratings):
        """
        Initialize dataset
        
        Args:
            user_ids (numpy.array): Array of user indices
            item_ids (numpy.array): Array of item indices
            ratings (numpy.array): Array of ratings/scores
        """
        self.user_ids = torch.LongTensor(user_ids)
        self.item_ids = torch.LongTensor(item_ids)
        self.ratings = torch.FloatTensor(ratings)
    
    def __len__(self):
        return len(self.user_ids)
    
    def __getitem__(self, idx):
        return {
            'user_id': self.user_ids[idx],
            'item_id': self.item_ids[idx],
            'rating': self.ratings[idx]
        }


class NCFDataLoader:
    """
    Data loader for NCF model training
    Handles data extraction, preprocessing, and negative sampling
    """
    
    def __init__(self, test_size=0.2, val_size=0.1, negative_samples=4, random_state=42):
        """
        Initialize data loader
        
        Args:
            test_size (float): Proportion of data for testing
            val_size (float): Proportion of training data for validation
            negative_samples (int): Number of negative samples per positive sample
            random_state (int): Random seed for reproducibility
        """
        self.test_size = test_size
        self.val_size = val_size
        self.negative_samples = negative_samples
        self.random_state = random_state
        
        # Mappings between database IDs and model indices
        self.user_id_to_idx = {}
        self.idx_to_user_id = {}
        self.item_id_to_idx = {}
        self.idx_to_item_id = {}
        
        self.num_users = 0
        self.num_items = 0
    
    def load_data_from_db(self):
        """
        Load interaction data from database
        
        Returns:
            pandas.DataFrame: DataFrame with columns [user_id, item_id, rating, timestamp]
        """
        # Get all interactions
        interactions = Interaction.objects.select_related('user', 'epreuve').all()
        
        data = []
        for interaction in interactions:
            # Convert interaction type to implicit rating
            rating = self._interaction_to_rating(interaction.action_type)
            
            data.append({
                'user_id': interaction.user.id,
                'item_id': interaction.epreuve.id,
                'rating': rating,
                'timestamp': interaction.timestamp
            })
        
        df = pd.DataFrame(data)
        
        # Create user and item mappings
        self._create_mappings(df)
        
        return df
    
    def _interaction_to_rating(self, action_type):
        """
        Convert interaction type to implicit rating
        
        Args:
            action_type (str): Type of interaction (VIEW, DOWNLOAD, CLICK, RATE)
        
        Returns:
            float: Implicit rating score
        """
        rating_map = {
            'VIEW': 1.0,
            'CLICK': 2.0,
            'DOWNLOAD': 3.0,
            'RATE': 4.0,
        }
        return rating_map.get(action_type, 1.0)
    
    def _create_mappings(self, df):
        """
        Create mappings between database IDs and model indices
        
        Args:
            df (pandas.DataFrame): Interaction dataframe
        """
        # Get unique users and items
        unique_users = df['user_id'].unique()
        unique_items = df['item_id'].unique()
        
        # Create user mappings
        for idx, user_id in enumerate(sorted(unique_users)):
            self.user_id_to_idx[user_id] = idx
            self.idx_to_user_id[idx] = user_id
        
        # Create item mappings
        for idx, item_id in enumerate(sorted(unique_items)):
            self.item_id_to_idx[item_id] = idx
            self.idx_to_item_id[idx] = item_id
        
        self.num_users = len(unique_users)
        self.num_items = len(unique_items)
    
    def prepare_data(self, df):
        """
        Prepare data for training with negative sampling
        
        Args:
            df (pandas.DataFrame): Raw interaction dataframe
        
        Returns:
            tuple: (user_indices, item_indices, ratings)
        """
        # Map database IDs to indices
        df['user_idx'] = df['user_id'].map(self.user_id_to_idx)
        df['item_idx'] = df['item_id'].map(self.item_id_to_idx)
        
        # Aggregate multiple interactions (keep max rating per user-item pair)
        df_agg = df.groupby(['user_idx', 'item_idx'])['rating'].max().reset_index()
        
        # Normalize ratings to [0, 1]
        df_agg['rating'] = df_agg['rating'] / df_agg['rating'].max()
        
        # Generate negative samples
        positive_pairs = set(zip(df_agg['user_idx'], df_agg['item_idx']))
        negative_samples = self._generate_negative_samples(positive_pairs)
        
        # Combine positive and negative samples
        all_user_ids = list(df_agg['user_idx']) + [u for u, _ in negative_samples]
        all_item_ids = list(df_agg['item_idx']) + [i for _, i in negative_samples]
        all_ratings = list(df_agg['rating']) + [0.0] * len(negative_samples)
        
        return np.array(all_user_ids), np.array(all_item_ids), np.array(all_ratings)
    
    def _generate_negative_samples(self, positive_pairs):
        """
        Generate negative samples (user-item pairs with no interaction)
        
        Args:
            positive_pairs (set): Set of (user_idx, item_idx) positive pairs
        
        Returns:
            list: List of negative (user_idx, item_idx) pairs
        """
        negative_samples = []
        num_negatives = len(positive_pairs) * self.negative_samples
        
        np.random.seed(self.random_state)
        
        while len(negative_samples) < num_negatives:
            user_idx = np.random.randint(0, self.num_users)
            item_idx = np.random.randint(0, self.num_items)
            
            if (user_idx, item_idx) not in positive_pairs:
                negative_samples.append((user_idx, item_idx))
        
        return negative_samples
    
    def split_data(self, user_ids, item_ids, ratings):
        """
        Split data into train, validation, and test sets
        
        Args:
            user_ids (numpy.array): User indices
            item_ids (numpy.array): Item indices
            ratings (numpy.array): Ratings
        
        Returns:
            tuple: (train_data, val_data, test_data) where each is (users, items, ratings)
        """
        # First split: train+val vs test
        X = np.column_stack([user_ids, item_ids])
        y = ratings
        
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, shuffle=True
        )
        
        # Second split: train vs val
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=self.val_size, random_state=self.random_state, shuffle=True
        )
        
        # Extract user and item IDs
        train_data = (X_train[:, 0], X_train[:, 1], y_train)
        val_data = (X_val[:, 0], X_val[:, 1], y_val)
        test_data = (X_test[:, 0], X_test[:, 1], y_test)
        
        return train_data, val_data, test_data
    
    def create_dataloaders(self, train_data, val_data, test_data, batch_size=256):
        """
        Create PyTorch DataLoaders
        
        Args:
            train_data (tuple): Training data (users, items, ratings)
            val_data (tuple): Validation data
            test_data (tuple): Test data
            batch_size (int): Batch size for training
        
        Returns:
            tuple: (train_loader, val_loader, test_loader)
        """
        train_dataset = InteractionDataset(*train_data)
        val_dataset = InteractionDataset(*val_data)
        test_dataset = InteractionDataset(*test_data)
        
        train_loader = DataLoader(
            train_dataset, 
            batch_size=batch_size, 
            shuffle=True, 
            num_workers=0
        )
        
        val_loader = DataLoader(
            val_dataset, 
            batch_size=batch_size, 
            shuffle=False, 
            num_workers=0
        )
        
        test_loader = DataLoader(
            test_dataset, 
            batch_size=batch_size, 
            shuffle=False, 
            num_workers=0
        )
        
        return train_loader, val_loader, test_loader
    
    def get_all_items_for_user(self, user_db_id):
        """
        Get all item indices that can be recommended to a user
        
        Args:
            user_db_id (int): Database user ID
        
        Returns:
            list: List of all item indices
        """
        return list(range(self.num_items))
    
    def user_db_id_to_idx(self, user_db_id):
        """Convert database user ID to model index"""
        return self.user_id_to_idx.get(user_db_id)
    
    def item_db_id_to_idx(self, item_db_id):
        """Convert database item ID to model index"""
        return self.item_id_to_idx.get(item_db_id)
    
    def user_idx_to_db_id(self, user_idx):
        """Convert model user index to database ID"""
        return self.idx_to_user_id.get(user_idx)
    
    def item_idx_to_db_id(self, item_idx):
        """Convert model item index to database ID"""
        return self.idx_to_item_id.get(item_idx)
