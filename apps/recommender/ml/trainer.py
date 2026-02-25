"""
Training pipeline for NCF model
Handles model training, validation, and evaluation
"""
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import time
import numpy as np
from sklearn.metrics import mean_squared_error, precision_score, recall_score
import logging

logger = logging.getLogger(__name__)


class NCFTrainer:
    """
    Trainer for Neural Collaborative Filtering model
    """
    
    def __init__(self, model, device='cpu', learning_rate=0.001, weight_decay=1e-5):
        """
        Initialize trainer
        
        Args:
            model: NCF model instance
            device (str): Device to use ('cpu' or 'cuda')
            learning_rate (float): Learning rate for optimizer
            weight_decay (float): L2 regularization weight
        """
        self.model = model
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(
            model.parameters(), 
            lr=learning_rate, 
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, 
            mode='min', 
            factor=0.5, 
            patience=5, 
            verbose=True
        )
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'learning_rate': []
        }
    
    def train_epoch(self, train_loader):
        """
        Train model for one epoch
        
        Args:
            train_loader: DataLoader for training data
        
        Returns:
            float: Average training loss for the epoch
        """
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch in train_loader:
            user_ids = batch['user_id'].to(self.device)
            item_ids = batch['item_id'].to(self.device)
            ratings = batch['rating'].to(self.device).unsqueeze(1)
            
            # Forward pass
            predictions = self.model(user_ids, item_ids)
            
            # Compute loss
            loss = self.criterion(predictions, ratings)
            
            # Backward pass and optimization
            self.optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def validate(self, val_loader):
        """
        Validate model
        
        Args:
            val_loader: DataLoader for validation data
        
        Returns:
            float: Average validation loss
        """
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in val_loader:
                user_ids = batch['user_id'].to(self.device)
                item_ids = batch['item_id'].to(self.device)
                ratings = batch['rating'].to(self.device).unsqueeze(1)
                
                predictions = self.model(user_ids, item_ids)
                loss = self.criterion(predictions, ratings)
                
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    def train(self, train_loader, val_loader, epochs=50, early_stopping_patience=10, verbose=True):
        """
        Full training loop with early stopping
        
        Args:
            train_loader: DataLoader for training
            val_loader: DataLoader for validation
            epochs (int): Maximum number of epochs
            early_stopping_patience (int): Patience for early stopping
            verbose (bool): Print training progress
        
        Returns:
            dict: Training history
        """
        best_val_loss = float('inf')
        patience_counter = 0
        
        start_time = time.time()
        
        for epoch in range(epochs):
            epoch_start = time.time()
            
            # Train
            train_loss = self.train_epoch(train_loader)
            
            # Validate
            val_loss = self.validate(val_loader)
            
            # Update learning rate
            self.scheduler.step(val_loss)
            
            # Record history
            current_lr = self.optimizer.param_groups[0]['lr']
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['learning_rate'].append(current_lr)
            
            epoch_time = time.time() - epoch_start
            
            if verbose:
                print(f"Epoch {epoch+1}/{epochs} - {epoch_time:.2f}s - "
                      f"Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f} - "
                      f"LR: {current_lr:.6f}")
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                self.best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
                
                if patience_counter >= early_stopping_patience:
                    if verbose:
                        print(f"Early stopping triggered after {epoch+1} epochs")
                    break
        
        total_time = time.time() - start_time
        
        # Restore best model
        if hasattr(self, 'best_model_state'):
            self.model.load_state_dict(self.best_model_state)
        
        if verbose:
            print(f"\nTraining completed in {total_time:.2f}s")
            print(f"Best validation loss: {best_val_loss:.4f}")
        
        self.history['total_training_time'] = total_time
        self.history['best_val_loss'] = best_val_loss
        
        return self.history
    
    def evaluate(self, test_loader):
        """
        Evaluate model on test set
        
        Args:
            test_loader: DataLoader for test data
        
        Returns:
            dict: Evaluation metrics
        """
        self.model.eval()
        
        all_predictions = []
        all_ratings = []
        
        with torch.no_grad():
            for batch in test_loader:
                user_ids = batch['user_id'].to(self.device)
                item_ids = batch['item_id'].to(self.device)
                ratings = batch['rating'].to(self.device)
                
                predictions = self.model(user_ids, item_ids).squeeze()
                
                all_predictions.extend(predictions.cpu().numpy())
                all_ratings.extend(ratings.cpu().numpy())
        
        all_predictions = np.array(all_predictions)
        all_ratings = np.array(all_ratings)
        
        # Compute metrics
        mse = mean_squared_error(all_ratings, all_predictions)
        rmse = np.sqrt(mse)
        
        # Precision and Recall @ K (treating as binary classification)
        threshold = 0.5
        pred_binary = (all_predictions >= threshold).astype(int)
        true_binary = (all_ratings >= threshold).astype(int)
        
        precision = precision_score(true_binary, pred_binary, zero_division=0)
        recall = recall_score(true_binary, pred_binary, zero_division=0)
        
        metrics = {
            'test_loss': mse,
            'rmse': rmse,
            'precision': precision,
            'recall': recall,
        }
        
        return metrics
    
    def compute_precision_recall_at_k(self, user_item_pairs, k=10):
        """
        Compute Precision@K and Recall@K for recommendations
        
        Args:
            user_item_pairs (list): List of (user_idx, relevant_item_indices)
            k (int): Top-K recommendations
        
        Returns:
            tuple: (precision_at_k, recall_at_k)
        """
        precisions = []
        recalls = []
        
        self.model.eval()
        with torch.no_grad():
            for user_idx, relevant_items in user_item_pairs:
                # Get all items
                all_items = list(range(self.model.num_items))
                
                # Predict scores
                user_tensor = torch.tensor([user_idx] * len(all_items), dtype=torch.long).to(self.device)
                item_tensor = torch.tensor(all_items, dtype=torch.long).to(self.device)
                
                predictions = self.model(user_tensor, item_tensor).squeeze()
                
                # Get top-K
                _, top_k_indices = torch.topk(predictions, k)
                recommended_items = set([all_items[idx] for idx in top_k_indices.cpu().numpy()])
                
                # Compute precision and recall
                relevant_set = set(relevant_items)
                hits = recommended_items & relevant_set
                
                if len(recommended_items) > 0:
                    precision = len(hits) / len(recommended_items)
                else:
                    precision = 0.0
                
                if len(relevant_set) > 0:
                    recall = len(hits) / len(relevant_set)
                else:
                    recall = 0.0
                
                precisions.append(precision)
                recalls.append(recall)
        
        avg_precision = np.mean(precisions)
        avg_recall = np.mean(recalls)
        
        return avg_precision, avg_recall
    
    def save_model(self, save_path):
        """
        Save model to disk
        
        Args:
            save_path (str or Path): Path to save the model
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'num_users': self.model.num_users,
            'num_items': self.model.num_items,
            'embedding_dim': self.model.embedding_dim,
            'history': self.history
        }
        
        torch.save(checkpoint, save_path)
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, load_path):
        """
        Load model from disk
        
        Args:
            load_path (str or Path): Path to load the model from
        """
        checkpoint = torch.load(load_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint.get('history', {})
        
        logger.info(f"Model loaded from {load_path}")
