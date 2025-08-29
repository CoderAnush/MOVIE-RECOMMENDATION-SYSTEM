"""
Artificial Neural Network (ANN) Collaborative Filtering Model

This module implements a neural collaborative filtering model using TensorFlow/Keras
for movie recommendations. The model uses embedding layers for users and movies
followed by dense layers for rating prediction.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model, callbacks
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pickle
import logging
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

class ANNCollaborativeFilteringModel:
    """Neural Collaborative Filtering Model for Movie Recommendations"""
    
    def __init__(self, n_users, n_movies, embedding_dim=32, hidden_dims=[64, 32], 
                 dropout_rate=0.2, learning_rate=0.001):
        """
        Initialize ANN model
        
        Args:
            n_users (int): Number of unique users
            n_movies (int): Number of unique movies
            embedding_dim (int): Embedding dimension for users and movies
            hidden_dims (list): Hidden layer dimensions
            dropout_rate (float): Dropout rate for regularization
            learning_rate (float): Learning rate for optimizer
        """
        self.n_users = n_users
        self.n_movies = n_movies
        self.embedding_dim = embedding_dim
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        
        self.model = None
        self.user_to_idx = None
        self.movie_to_idx = None
        self.idx_to_user = None
        self.idx_to_movie = None
        self.training_history = None
        
        # Build model
        self._build_model()
    
    def _build_model(self):
        """Build the neural collaborative filtering model"""
        
        # Input layers
        user_input = layers.Input(shape=(), name='user_id')
        movie_input = layers.Input(shape=(), name='movie_id')
        
        # Embedding layers
        user_embedding = layers.Embedding(
            input_dim=self.n_users,
            output_dim=self.embedding_dim,
            name='user_embedding',
            embeddings_regularizer=keras.regularizers.l2(1e-6)
        )(user_input)
        
        movie_embedding = layers.Embedding(
            input_dim=self.n_movies,
            output_dim=self.embedding_dim,
            name='movie_embedding',
            embeddings_regularizer=keras.regularizers.l2(1e-6)
        )(movie_input)
        
        # Flatten embeddings
        user_vec = layers.Flatten(name='user_flatten')(user_embedding)
        movie_vec = layers.Flatten(name='movie_flatten')(movie_embedding)
        
        # Concatenate user and movie embeddings
        concat = layers.Concatenate(name='concat')([user_vec, movie_vec])
        
        # Dense layers with dropout
        x = concat
        for i, hidden_dim in enumerate(self.hidden_dims):
            x = layers.Dense(
                hidden_dim,
                activation='relu',
                name=f'dense_{i+1}',
                kernel_regularizer=keras.regularizers.l2(1e-6)
            )(x)
            x = layers.Dropout(self.dropout_rate, name=f'dropout_{i+1}')(x)
        
        # Output layer - single neuron for rating prediction
        # Using sigmoid activation and scaling to 0-10 range
        output = layers.Dense(1, activation='sigmoid', name='rating_output')(x)
        output = layers.Lambda(lambda x: x * 10, name='scale_output')(output)
        
        # Create model
        self.model = Model(inputs=[user_input, movie_input], outputs=output)
        
        # Compile model
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info(f"Built ANN model with {self.model.count_params()} parameters")
        logger.info("Model architecture:")
        self.model.summary(print_fn=logger.info)
    
    def prepare_training_data(self, ratings_df, user_to_idx, movie_to_idx, 
                            test_size=0.2, random_state=42):
        """
        Prepare training and validation data
        
        Args:
            ratings_df (pd.DataFrame): Ratings dataframe
            user_to_idx (dict): User ID to index mapping
            movie_to_idx (dict): Movie ID to index mapping
            test_size (float): Test set proportion
            random_state (int): Random seed
            
        Returns:
            tuple: (X_train, X_val, y_train, y_val)
        """
        # Store mappings
        self.user_to_idx = user_to_idx
        self.movie_to_idx = movie_to_idx
        self.idx_to_user = {idx: user for user, idx in user_to_idx.items()}
        self.idx_to_movie = {idx: movie for movie, idx in movie_to_idx.items()}
        
        # Filter ratings to only include users and movies in our mappings
        valid_ratings = ratings_df[
            (ratings_df['user_id'].isin(user_to_idx.keys())) &
            (ratings_df['movie_id'].isin(movie_to_idx.keys()))
        ].copy()
        
        # Map to indices
        valid_ratings['user_idx'] = valid_ratings['user_id'].map(user_to_idx)
        valid_ratings['movie_idx'] = valid_ratings['movie_id'].map(movie_to_idx)
        
        # Prepare features and targets
        X = {
            'user_id': valid_ratings['user_idx'].values,
            'movie_id': valid_ratings['movie_idx'].values
        }
        
        # Scale ratings from 1-5 to 0-10
        y = ((valid_ratings['rating'].values - 1) / 4) * 10
        
        # Train-validation split
        X_train, X_val, y_train, y_val = train_test_split(
            [X['user_id'], X['movie_id']], y,
            test_size=test_size,
            random_state=random_state,
            stratify=None
        )
        
        # Reshape for model input
        X_train = {'user_id': X_train[0], 'movie_id': X_train[1]}
        X_val = {'user_id': X_val[0], 'movie_id': X_val[1]}
        
        logger.info(f"Training data: {len(y_train)} samples")
        logger.info(f"Validation data: {len(y_val)} samples")
        
        return X_train, X_val, y_train, y_val
    
    def train(self, X_train, X_val, y_train, y_val, epochs=100, batch_size=256, 
              patience=10, verbose=1):
        """
        Train the ANN model
        
        Args:
            X_train (dict): Training features
            X_val (dict): Validation features
            y_train (np.array): Training targets
            y_val (np.array): Validation targets
            epochs (int): Maximum number of epochs
            batch_size (int): Batch size
            patience (int): Early stopping patience
            verbose (int): Verbosity level
            
        Returns:
            dict: Training history
        """
        # Callbacks
        early_stopping = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=patience,
            restore_best_weights=True,
            verbose=verbose
        )
        
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=verbose
        )
        
        # Train model
        logger.info("Starting ANN model training...")
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping, reduce_lr],
            verbose=verbose
        )
        
        self.training_history = history.history
        
        # Evaluate final performance
        train_loss, train_mae = self.model.evaluate(X_train, y_train, verbose=0)
        val_loss, val_mae = self.model.evaluate(X_val, y_val, verbose=0)
        
        logger.info(f"Training completed!")
        logger.info(f"Final Training - Loss: {train_loss:.4f}, MAE: {train_mae:.4f}")
        logger.info(f"Final Validation - Loss: {val_loss:.4f}, MAE: {val_mae:.4f}")
        
        return self.training_history
    
    def predict_for_user(self, user_id, candidate_movie_ids=None, top_k=20):
        """
        Predict ratings for a user on candidate movies
        
        Args:
            user_id (int): User ID
            candidate_movie_ids (list): List of movie IDs to predict for
            top_k (int): Number of top recommendations to return
            
        Returns:
            list: List of (movie_id, predicted_rating) tuples
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        if user_id not in self.user_to_idx:
            logger.warning(f"User {user_id} not in training data")
            return []
        
        user_idx = self.user_to_idx[user_id]
        
        # If no candidate movies specified, use all movies
        if candidate_movie_ids is None:
            candidate_movie_ids = list(self.movie_to_idx.keys())
        
        # Filter to movies in our vocabulary
        valid_movie_ids = [mid for mid in candidate_movie_ids if mid in self.movie_to_idx]
        
        if not valid_movie_ids:
            logger.warning("No valid candidate movies found")
            return []
        
        # Prepare prediction data
        user_indices = np.array([user_idx] * len(valid_movie_ids))
        movie_indices = np.array([self.movie_to_idx[mid] for mid in valid_movie_ids])
        
        # Predict ratings
        predictions = self.model.predict({
            'user_id': user_indices,
            'movie_id': movie_indices
        }, verbose=0)
        
        # Combine with movie IDs and sort
        movie_predictions = list(zip(valid_movie_ids, predictions.flatten()))
        movie_predictions.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k
        return movie_predictions[:top_k]
    
    def predict_batch(self, user_ids, movie_ids):
        """
        Predict ratings for multiple user-movie pairs
        
        Args:
            user_ids (list): List of user IDs
            movie_ids (list): List of movie IDs
            
        Returns:
            np.array: Predicted ratings
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        # Map to indices
        user_indices = []
        movie_indices = []
        valid_pairs = []
        
        for i, (user_id, movie_id) in enumerate(zip(user_ids, movie_ids)):
            if user_id in self.user_to_idx and movie_id in self.movie_to_idx:
                user_indices.append(self.user_to_idx[user_id])
                movie_indices.append(self.movie_to_idx[movie_id])
                valid_pairs.append(i)
        
        if not valid_pairs:
            return np.array([])
        
        # Predict
        predictions = self.model.predict({
            'user_id': np.array(user_indices),
            'movie_id': np.array(movie_indices)
        }, verbose=0)
        
        # Create full prediction array with defaults for invalid pairs
        full_predictions = np.full(len(user_ids), 5.0)  # Default rating
        full_predictions[valid_pairs] = predictions.flatten()
        
        return full_predictions
    
    def evaluate_model(self, X_test, y_test):
        """
        Evaluate model performance
        
        Args:
            X_test (dict): Test features
            y_test (np.array): Test targets
            
        Returns:
            dict: Evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        # Predict
        y_pred = self.model.predict(X_test, verbose=0).flatten()
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        metrics = {
            'mse': mse,
            'mae': mae,
            'rmse': rmse
        }
        
        logger.info(f"Model Evaluation - RMSE: {rmse:.4f}, MAE: {mae:.4f}")
        
        return metrics
    
    def save_model(self, filepath):
        """
        Save trained model and mappings
        
        Args:
            filepath (str): Path to save model
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model weights
        model_path = filepath.with_suffix('.h5')
        self.model.save_weights(str(model_path))
        
        # Save metadata and mappings
        metadata = {
            'n_users': self.n_users,
            'n_movies': self.n_movies,
            'embedding_dim': self.embedding_dim,
            'hidden_dims': self.hidden_dims,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'user_to_idx': self.user_to_idx,
            'movie_to_idx': self.movie_to_idx,
            'idx_to_user': self.idx_to_user,
            'idx_to_movie': self.idx_to_movie,
            'training_history': self.training_history
        }
        
        metadata_path = filepath.with_suffix('.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Model saved to {model_path}")
        logger.info(f"Metadata saved to {metadata_path}")
    
    def load_model(self, filepath):
        """
        Load trained model and mappings
        
        Args:
            filepath (str): Path to load model from
        """
        filepath = Path(filepath)
        
        # Load metadata
        metadata_path = filepath.with_suffix('.pkl')
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        # Restore model parameters
        self.n_users = metadata['n_users']
        self.n_movies = metadata['n_movies']
        self.embedding_dim = metadata['embedding_dim']
        self.hidden_dims = metadata['hidden_dims']
        self.dropout_rate = metadata['dropout_rate']
        self.learning_rate = metadata['learning_rate']
        self.user_to_idx = metadata['user_to_idx']
        self.movie_to_idx = metadata['movie_to_idx']
        self.idx_to_user = metadata['idx_to_user']
        self.idx_to_movie = metadata['idx_to_movie']
        self.training_history = metadata.get('training_history')
        
        # Rebuild and load model
        self._build_model()
        model_path = filepath.with_suffix('.h5')
        self.model.load_weights(str(model_path))
        
        logger.info(f"Model loaded from {model_path}")
    
    def plot_training_history(self, save_path=None):
        """
        Plot training history
        
        Args:
            save_path (str): Path to save plot (optional)
        """
        if self.training_history is None:
            logger.warning("No training history available")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss plot
        ax1.plot(self.training_history['loss'], label='Training Loss')
        ax1.plot(self.training_history['val_loss'], label='Validation Loss')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # MAE plot
        ax2.plot(self.training_history['mae'], label='Training MAE')
        ax2.plot(self.training_history['val_mae'], label='Validation MAE')
        ax2.set_title('Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Training history plot saved to {save_path}")
        
        plt.show()


def train_ann_model(data_path, model_save_path, sample_size=None):
    """
    Train ANN model from preprocessed data
    
    Args:
        data_path (str): Path to preprocessed data
        model_save_path (str): Path to save trained model
        sample_size (int): Sample size for training (for testing)
    """
    logger.info("Loading preprocessed data...")
    with open(data_path, 'rb') as f:
        data = pickle.load(f)
    
    ratings_df = data['ratings_normalized']
    user_to_idx = data['user_to_idx']
    movie_to_idx = data['movie_to_idx']
    
    # Sample data if requested
    if sample_size and len(ratings_df) > sample_size:
        logger.info(f"Sampling {sample_size} ratings for training")
        ratings_df = ratings_df.sample(n=sample_size, random_state=42)
    
    # Initialize model
    n_users = len(user_to_idx)
    n_movies = len(movie_to_idx)
    
    logger.info(f"Initializing ANN model for {n_users} users and {n_movies} movies")
    
    model = ANNCollaborativeFilteringModel(
        n_users=n_users,
        n_movies=n_movies,
        embedding_dim=32,
        hidden_dims=[64, 32],
        dropout_rate=0.2,
        learning_rate=0.001
    )
    
    # Prepare training data
    X_train, X_val, y_train, y_val = model.prepare_training_data(
        ratings_df, user_to_idx, movie_to_idx
    )
    
    # Train model
    history = model.train(
        X_train, X_val, y_train, y_val,
        epochs=50,  # Reduced for demo
        batch_size=256,
        patience=10,
        verbose=1
    )
    
    # Evaluate model
    metrics = model.evaluate_model(X_val, y_val)
    
    # Save model
    model.save_model(model_save_path)
    
    logger.info(f"ANN model training completed!")
    logger.info(f"Final RMSE: {metrics['rmse']:.4f}")
    logger.info(f"Final MAE: {metrics['mae']:.4f}")
    
    return model, metrics


def main():
    """Main function for command line training"""
    parser = argparse.ArgumentParser(description='Train ANN collaborative filtering model')
    parser.add_argument('--data', type=str, required=True,
                       help='Path to preprocessed data pickle file')
    parser.add_argument('--output', type=str, default='./models/ann_model',
                       help='Output path for trained model')
    parser.add_argument('--sample', type=int, default=None,
                       help='Sample size for training (for testing)')
    parser.add_argument('--train', action='store_true',
                       help='Train the model')
    
    args = parser.parse_args()
    
    if args.train:
        train_ann_model(args.data, args.output, args.sample)
    else:
        print("Use --train flag to start training")


if __name__ == '__main__':
    main()
