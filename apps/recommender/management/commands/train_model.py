"""
Django management command to train the NCF model
Usage: python manage.py train_model
"""
import os
import pickle
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.recommender.ml.ncf_model import NCFModel
from apps.recommender.ml.data_loader import NCFDataLoader
from apps.recommender.ml.trainer import NCFTrainer
from apps.recommender.models import ModelMetadata, TrainingLog
import torch


class Command(BaseCommand):
    help = 'Train the NCF recommendation model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs',
            type=int,
            default=50,
            help='Number of training epochs (default: 50)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=256,
            help='Batch size for training (default: 256)'
        )
        parser.add_argument(
            '--embedding-dim',
            type=int,
            default=64,
            help='Embedding dimension (default: 64)'
        )
        parser.add_argument(
            '--learning-rate',
            type=float,
            default=0.001,
            help='Learning rate (default: 0.001)'
        )
        parser.add_argument(
            '--device',
            type=str,
            default='cpu',
            choices=['cpu', 'cuda'],
            help='Device to use for training (default: cpu)'
        )
        parser.add_argument(
            '--model-version',
            type=str,
            default=None,
            help='Model version name (default: auto-generated)'
        )
        parser.add_argument(
            '--negative-samples',
            type=int,
            default=4,
            help='Number of negative samples per positive sample (default: 4)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('  Training NCF Recommendation Model'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        # Extract options
        epochs = options['epochs']
        batch_size = options['batch_size']
        embedding_dim = options['embedding_dim']
        learning_rate = options['learning_rate']
        device = options['device']
        version = options['model_version']
        negative_samples = options['negative_samples']
        
        # Display configuration
        self.stdout.write(self.style.WARNING('Configuration:'))
        self.stdout.write(f'  Epochs: {epochs}')
        self.stdout.write(f'  Batch size: {batch_size}')
        self.stdout.write(f'  Embedding dimension: {embedding_dim}')
        self.stdout.write(f'  Learning rate: {learning_rate}')
        self.stdout.write(f'  Device: {device}')
        self.stdout.write(f'  Negative samples: {negative_samples}')
        self.stdout.write('')
        
        # Step 1: Load data
        self.stdout.write(self.style.WARNING('Step 1/5: Loading interaction data from database...'))
        data_loader = NCFDataLoader(negative_samples=negative_samples)
        df = data_loader.load_data_from_db()
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Loaded {len(df)} interactions'))
        self.stdout.write(f'  ✓ Users: {data_loader.num_users}')
        self.stdout.write(f'  ✓ Items: {data_loader.num_items}')
        self.stdout.write('')
        
        # Step 2: Prepare data
        self.stdout.write(self.style.WARNING('Step 2/5: Preparing data with negative sampling...'))
        user_ids, item_ids, ratings = data_loader.prepare_data(df)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Total samples (with negatives): {len(user_ids)}'))
        self.stdout.write('')
        
        # Step 3: Split data
        self.stdout.write(self.style.WARNING('Step 3/5: Splitting data into train/val/test...'))
        train_data, val_data, test_data = data_loader.split_data(user_ids, item_ids, ratings)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Train samples: {len(train_data[0])}'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Validation samples: {len(val_data[0])}'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Test samples: {len(test_data[0])}'))
        self.stdout.write('')
        
        # Create data loaders
        train_loader, val_loader, test_loader = data_loader.create_dataloaders(
            train_data, val_data, test_data, batch_size=batch_size
        )
        
        # Step 4: Initialize and train model
        self.stdout.write(self.style.WARNING('Step 4/5: Training NCF model...'))
        self.stdout.write('')
        
        model = NCFModel(
            num_users=data_loader.num_users,
            num_items=data_loader.num_items,
            embedding_dim=embedding_dim
        )
        
        trainer = NCFTrainer(
            model=model,
            device=device,
            learning_rate=learning_rate
        )
        
        # Train
        import time
        start_time = time.time()
        
        history = trainer.train(
            train_loader=train_loader,
            val_loader=val_loader,
            epochs=epochs,
            early_stopping_patience=10,
            verbose=True
        )
        
        training_duration = int(time.time() - start_time)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'  ✓ Training completed in {training_duration}s'))
        self.stdout.write('')
        
        # Step 5: Evaluate model
        self.stdout.write(self.style.WARNING('Step 5/5: Evaluating model on test set...'))
        metrics = trainer.evaluate(test_loader)
        
        self.stdout.write(self.style.SUCCESS('  Test Metrics:'))
        self.stdout.write(f'    RMSE: {metrics["rmse"]:.4f}')
        self.stdout.write(f'    Precision: {metrics["precision"]:.4f}')
        self.stdout.write(f'    Recall: {metrics["recall"]:.4f}')
        self.stdout.write('')
        
        # Save model
        self.stdout.write(self.style.WARNING('Saving model...'))
        
        # Create ml_models directory if it doesn't exist
        ml_models_dir = Path(settings.BASE_DIR) / 'ml_models'
        ml_models_dir.mkdir(exist_ok=True)
        
        # Generate version name
        if version is None:
            from datetime import datetime
            version = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save model
        model_filename = f'ncf_model_{version}.pth'
        model_path = ml_models_dir / model_filename
        trainer.save_model(model_path)
        
        # Save as latest
        latest_path = ml_models_dir / 'ncf_model_latest.pth'
        import shutil
        shutil.copy(model_path, latest_path)
        
        # Save ID mappings
        mappings = {
            'user_id_to_idx': data_loader.user_id_to_idx,
            'idx_to_user_id': data_loader.idx_to_user_id,
            'item_id_to_idx': data_loader.item_id_to_idx,
            'idx_to_item_id': data_loader.idx_to_item_id,
        }
        
        mappings_path = ml_models_dir / 'id_mappings.pkl'
        with open(mappings_path, 'wb') as f:
            pickle.dump(mappings, f)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Model saved to {model_path}'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Latest model: {latest_path}'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ ID mappings saved to {mappings_path}'))
        self.stdout.write('')
        
        # Save metadata to database
        self.stdout.write(self.style.WARNING('Saving training metadata to database...'))
        
        # Deactivate previous models
        ModelMetadata.objects.filter(is_active=True).update(is_active=False)
        
        # Create new model metadata
        model_metadata = ModelMetadata.objects.create(
            version=version,
            description=f'NCF model trained on {len(df)} interactions',
            model_path=str(model_path),
            architecture='NCF',
            is_active=True,
            hyperparameters={
                'embedding_dim': embedding_dim,
                'learning_rate': learning_rate,
                'batch_size': batch_size,
                'epochs': epochs,
                'negative_samples': negative_samples,
            }
        )
        
        # Create training log
        TrainingLog.objects.create(
            model_version=model_metadata,
            training_duration=training_duration,
            nb_interactions=len(df),
            nb_users=data_loader.num_users,
            nb_epreuves=data_loader.num_items,
            train_loss=history['train_loss'][-1],
            val_loss=history['best_val_loss'],
            test_loss=metrics['test_loss'],
            rmse=metrics['rmse'],
            precision_at_10=metrics['precision'],
            recall_at_10=metrics['recall'],
            notes=f'Trained with {epochs} epochs, stopped at epoch {len(history["train_loss"])}'
        )
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Metadata saved to database'))
        self.stdout.write('')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('  Training Summary'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Model Version: {version}')
        self.stdout.write(f'  Training Time: {training_duration}s')
        self.stdout.write(f'  Best Val Loss: {history["best_val_loss"]:.4f}')
        self.stdout.write(f'  Test RMSE: {metrics["rmse"]:.4f}')
        self.stdout.write(f'  Precision@10: {metrics["precision"]:.4f}')
        self.stdout.write(f'  Recall@10: {metrics["recall"]:.4f}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('  Model is ready for production!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
