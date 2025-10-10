"""
Complete ANN Model for Movie Recommendation System
=================================================

This module implements the Artificial Neural Network component that works
alongside the fuzzy logic system to provide hybrid recommendations.

The ANN predicts a numeric rating (0-10) based on:
- User preferences per genre (7 features)
- Movie genre vector (7 features, one-hot)
- Movie popularity (1 feature)
- Watch history statistics (3 features)
🏗️ SYSTEM ARCHITECTURE
==================================================

    📊 Data Processing Layer
    ├── MovieLens 10M Dataset (10M ratings, 10K movies, 70K users)
    ├── Data Preprocessing Pipeline (scripts/prepare_dataset.py)
    └── Feature Engineering (genre encoding, user preferences, popularity)

    🧠 Recommendation Engines
    ├── Fuzzy Logic System (models/fuzzy_model.py)
    │   ├── User Preference vs Genre Rules
    │   ├── Popularity & Genre Match Rules
    │   ├── Watch History Rules
    │   └── Triangular Membership Functions
    │
    └── ANN Predictor (models/ann_model.py)
        ├── Dense Feed-Forward Network (64→32→16→1)
        ├── 18+ Engineered Features
        ├── Dropout Regularization
        └── Regression Output (0-10 scale)

    🔄 Hybrid Integration (models/hybrid_system.py)
    ├── Multiple Combination Strategies
    ├── Adaptive Weighting
    ├── Confidence-Based Adjustments
    └── Context-Aware Blending

    🌐 Integration Layer (integration_demo.py)
    ├── User Preference Extraction
    ├── Movie Information Processing
    ├── Watch History Analysis
    └── Real-time Recommendation API


🤖 REAL ANN IMPLEMENTATION PLAN
==================================================

   

Total: ~18 numeric features → 1 output score (0-10)
"""

import numpy as np
import pandas as pd
import tensorflow as tf
import keras
from keras import layers, callbacks, optimizers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import json
from typing import Dict, List, Tuple, Optional, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

class ANNMoviePredictor:
    """
    Complete ANN model for movie rating prediction.
    
    Features:
    - Dense feed-forward architecture
    - User preference + movie metadata inputs
    - Regression output (0-10 rating scale)
    - Integration with fuzzy logic system
    """
    
    def __init__(self, model_path="models/"):
        """Initialize the ANN predictor."""
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_columns = []
        self.genres = ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror']
        self.history = None
        
        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)
    
    def prepare_features(self, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for ANN training/prediction.
        
        Args:
            data_df: DataFrame with user ratings, movie info, and preferences
            
        Returns:
            DataFrame with engineered features ready for ML
        """
        logger.info("🔧 Preparing features for ANN...")
        
        features_df = data_df.copy()
        
        # 1. User Preferences (7 features: 0-10 scale)
        # These should be calculated from user rating history
        for genre in self.genres:
            pref_col = f'{genre}_pref'
            if pref_col not in features_df.columns:
                # Default to neutral preference if not available
                features_df[pref_col] = 5.0
        
        # 2. Movie Genre Vector (7 features: one-hot encoded)
        for genre in self.genres:
            genre_col = f'genre_{genre}'
            if genre_col not in features_df.columns:
                features_df[genre_col] = 0
        
        # 3. Movie Popularity (1 feature: normalized 0-1)
        if 'popularity' not in features_df.columns:
            # Calculate popularity from rating count if not available
            if 'movie_id_encoded' in features_df.columns:
                popularity = features_df.groupby('movie_id_encoded').size()
                popularity = np.log10(popularity + 1) * 25  # Log scale
                popularity = np.clip(popularity, 0, 100) / 100  # Normalize to 0-1
                features_df['popularity'] = features_df['movie_id_encoded'].map(popularity).fillna(0.5)
            else:
                features_df['popularity'] = 0.5  # Default
        else:
            # Normalize existing popularity to 0-1
            features_df['popularity'] = np.clip(features_df['popularity'], 0, 100) / 100
        
        # 4. Watch History Features (3 features: ratios and scaled count)
        if 'liked_ratio' not in features_df.columns:
            features_df['liked_ratio'] = 0.5  # Default neutral
        if 'disliked_ratio' not in features_df.columns:
            features_df['disliked_ratio'] = 0.3  # Default slight negative
        if 'watch_count' not in features_df.columns:
            features_df['watch_count'] = 1  # Minimal history
        
        # Normalize watch count to 0-1 scale (log scale for wide distribution)
        features_df['watch_count_norm'] = np.clip(
            np.log10(features_df['watch_count'] + 1) / 2, 0, 1
        )
        
        # 5. Optional: Movie Year (normalized)
        if 'year' in features_df.columns:
            # Normalize year to 0-1 (1900-2030 range)
            features_df['year_norm'] = np.clip(
                (features_df['year'] - 1900) / 130, 0, 1
            )
        else:
            features_df['year_norm'] = 0.7  # Default to ~2010
        
        # Define feature columns in order
        self.feature_columns = (
            # User preferences (7 features)
            [f'{genre}_pref' for genre in self.genres] +
            # Movie genres (7 features)
            [f'genre_{genre}' for genre in self.genres] +
            # Movie metadata (2 features)
            ['popularity', 'year_norm'] +
            # Watch history (3 features)
            ['liked_ratio', 'disliked_ratio', 'watch_count_norm']
        )
        
        logger.info(f"✅ Prepared {len(self.feature_columns)} features: {self.feature_columns}")
        return features_df
    
    def calculate_user_preferences(self, ratings_df: pd.DataFrame, 
                                 movies_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate user genre preferences from rating history.
        
        Args:
            ratings_df: User ratings data
            movies_df: Movie metadata with genre columns
            
        Returns:
            DataFrame with user preferences per genre
        """
        logger.info("🎭 Calculating user genre preferences...")
        
        # Merge ratings with movie genres
        merged = ratings_df.merge(movies_df, on='movie_id_encoded', how='left')
        
        user_prefs = []
        
        for user_id in merged['user_id_encoded'].unique():
            user_data = merged[merged['user_id_encoded'] == user_id]
            prefs = {'user_id_encoded': user_id}
            
            for genre in self.genres:
                genre_col = f'genre_{genre}'
                if genre_col in user_data.columns:
                    # Get ratings for movies with this genre
                    genre_movies = user_data[user_data[genre_col] == 1]
                    
                    if len(genre_movies) > 0:
                        # Convert average rating to 0-10 preference scale
                        avg_rating = genre_movies['rating'].mean()
                        # Scale from 0.5-5.0 rating to 0-10 preference
                        preference = max(0, min(10, (avg_rating - 0.5) * 2.22))
                    else:
                        preference = 5.0  # Neutral for unknown genres
                else:
                    preference = 5.0
                
                prefs[f'{genre}_pref'] = preference
            
            user_prefs.append(prefs)
        
        user_prefs_df = pd.DataFrame(user_prefs)
        logger.info(f"✅ Calculated preferences for {len(user_prefs_df)} users")
        return user_prefs_df
    
    def calculate_watch_history(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate watch history statistics per user.
        
        Args:
            ratings_df: User ratings data
            
        Returns:
            DataFrame with watch history features per user
        """
        logger.info("📚 Calculating watch history statistics...")
        
        history_stats = []
        
        for user_id in ratings_df['user_id_encoded'].unique():
            user_ratings = ratings_df[ratings_df['user_id_encoded'] == user_id]
            
            total_count = len(user_ratings)
            liked_count = len(user_ratings[user_ratings['rating'] >= 4])
            disliked_count = len(user_ratings[user_ratings['rating'] <= 2])
            
            stats = {
                'user_id_encoded': user_id,
                'watch_count': total_count,
                'liked_ratio': liked_count / max(total_count, 1),
                'disliked_ratio': disliked_count / max(total_count, 1)
            }
            history_stats.append(stats)
        
        history_df = pd.DataFrame(history_stats)
        logger.info(f"✅ Calculated history for {len(history_df)} users")
        return history_df
    
    def prepare_training_data(self, csv_path: str, sample_size: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from preprocessed CSV.
        
        Args:
            csv_path: Path to preprocessed MovieLens CSV
            sample_size: Optional limit on number of samples (for testing)
            
        Returns:
            Tuple of (X, y) arrays ready for training
        """
        logger.info(f"📊 Loading training data from {csv_path}")
        
        # Load the preprocessed data
        data = pd.read_csv(csv_path)
        logger.info(f"📈 Loaded {len(data)} ratings")
        
        if sample_size and len(data) > sample_size:
            data = data.sample(n=sample_size, random_state=42)
            logger.info(f"📉 Sampled down to {len(data)} ratings")
        
        # Separate movie and user data
        movies_df = data[['movie_id_encoded', 'year'] + 
                        [col for col in data.columns if col.startswith('genre_')]].drop_duplicates()
        ratings_df = data[['user_id_encoded', 'movie_id_encoded', 'rating']]
        
        # Calculate user preferences
        user_prefs_df = self.calculate_user_preferences(ratings_df, movies_df)
        
        # Calculate watch history
        history_df = self.calculate_watch_history(ratings_df)
        
        # Calculate movie popularity
        movie_popularity = ratings_df.groupby('movie_id_encoded').size().reset_index(name='rating_count')
        movie_popularity['popularity'] = np.log10(movie_popularity['rating_count'] + 1) * 25
        movie_popularity['popularity'] = np.clip(movie_popularity['popularity'], 0, 100)
        
        # Merge all features
        full_data = ratings_df.copy()
        full_data = full_data.merge(user_prefs_df, on='user_id_encoded', how='left')
        full_data = full_data.merge(history_df, on='user_id_encoded', how='left')
        full_data = full_data.merge(movies_df, on='movie_id_encoded', how='left')
        full_data = full_data.merge(movie_popularity[['movie_id_encoded', 'popularity']], 
                                  on='movie_id_encoded', how='left')
        
        # Prepare features
        full_data = self.prepare_features(full_data)
        
        # Extract features and target
        X = full_data[self.feature_columns].values
        y = full_data['rating'].values
        
        # Handle any NaN values
        X = np.nan_to_num(X, nan=0.5)
        y = np.nan_to_num(y, nan=3.0)
        
        # Scale target to 0-1 for training (will scale back for predictions)
        y = y / 5.0  # Scale 0-5 to 0-1
        
        logger.info(f"✅ Prepared training data: X shape {X.shape}, y shape {y.shape}")
        logger.info(f"📊 Feature ranges - X: [{X.min():.3f}, {X.max():.3f}], y: [{y.min():.3f}, {y.max():.3f}]")
        
        return X, y
    
    def build_model(self, input_dim: int) -> keras.Model:
        """
        Build the ANN architecture.
        
        Args:
            input_dim: Number of input features
            
        Returns:
            Compiled Keras model
        """
        logger.info(f"🏗️ Building ANN model with {input_dim} input features...")
        
        model = keras.Sequential([
            # Input layer
            layers.Input(shape=(input_dim,)),
            
            # Hidden layers with dropout for regularization
            layers.Dense(64, activation='relu', name='hidden_1'),
            layers.Dropout(0.2),
            
            layers.Dense(32, activation='relu', name='hidden_2'),
            layers.Dropout(0.15),
            
            layers.Dense(16, activation='relu', name='hidden_3'),
            layers.Dropout(0.1),
            
            # Output layer (regression)
            layers.Dense(1, activation='linear', name='output')
        ])
        
        # Compile model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info("✅ Model compiled successfully")
        model.summary()
        
        return model
    
    def train(self, X: np.ndarray, y: np.ndarray, 
              validation_split: float = 0.2,
              epochs: int = 100, 
              batch_size: int = 64,
              early_stopping_patience: int = 15) -> keras.callbacks.History:
        """
        Train the ANN model.
        
        Args:
            X: Feature matrix
            y: Target vector (0-1 scale)
            validation_split: Fraction for validation
            epochs: Maximum training epochs
            batch_size: Training batch size
            early_stopping_patience: Early stopping patience
            
        Returns:
            Training history
        """
        logger.info(f"🎯 Training ANN model...")
        
        # Build model
        self.model = self.build_model(X.shape[1])
        
        # Setup callbacks
        callbacks_list = [
            callbacks.EarlyStopping(
                monitor='val_loss',
                patience=early_stopping_patience,
                restore_best_weights=True,
                verbose=1
            ),
            callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=8,
                min_lr=1e-6,
                verbose=1
            )
        ]
        
        # Train model
        logger.info(f"🚀 Starting training: {epochs} epochs, batch size {batch_size}")
        self.history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list,
            verbose=1,
            shuffle=True
        )
        
        logger.info("✅ Training completed!")
        return self.history
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate the trained model.
        
        Args:
            X_test: Test features
            y_test: Test targets (0-1 scale)
            
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        logger.info("📊 Evaluating model performance...")
        
        # Get predictions
        y_pred = self.model.predict(X_test, verbose=0)
        
        # Scale back to 0-5 for evaluation
        y_test_scaled = y_test * 5.0
        y_pred_scaled = y_pred.flatten() * 5.0
        
        # Calculate metrics
        mse = mean_squared_error(y_test_scaled, y_pred_scaled)
        mae = mean_absolute_error(y_test_scaled, y_pred_scaled)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test_scaled, y_pred_scaled)
        
        metrics = {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'r2_score': r2
        }
        
        logger.info(f"📈 Model Performance (0-5 scale):")
        logger.info(f"   MAE: {mae:.3f}")
        logger.info(f"   RMSE: {rmse:.3f}")
        logger.info(f"   R²: {r2:.3f}")
        
        return metrics
    
    def predict(self, user_preferences: Dict[str, float],
                movie_info: Dict[str, Any],
                watch_history: Optional[Dict[str, float]] = None) -> float:
        """
        Predict rating for a single user-movie pair.
        
        Args:
            user_preferences: Dict with genre preferences (0-10)
            movie_info: Dict with movie metadata
            watch_history: Optional watch history stats
            
        Returns:
            Predicted rating (0-10 scale)
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Prepare features
        features = {}
        
        # User preferences
        for genre in self.genres:
            features[f'{genre}_pref'] = user_preferences.get(genre, 5.0)
        
        # Movie genres
        movie_genres = movie_info.get('genres', [])
        for genre in self.genres:
            genre_present = any(g.lower().replace(' ', '_') == genre 
                              for g in movie_genres)
            features[f'genre_{genre}'] = 1 if genre_present else 0
        
        # Movie metadata
        features['popularity'] = movie_info.get('popularity', 50) / 100  # Normalize
        features['year_norm'] = max(0, min(1, (movie_info.get('year', 2010) - 1900) / 130))
        
        # Watch history
        if watch_history:
            features['liked_ratio'] = watch_history.get('liked_ratio', 0.5)
            features['disliked_ratio'] = watch_history.get('disliked_ratio', 0.3)
            features['watch_count_norm'] = min(1, np.log10(watch_history.get('watch_count', 1) + 1) / 2)
        else:
            features['liked_ratio'] = 0.5
            features['disliked_ratio'] = 0.3
            features['watch_count_norm'] = 0.1
        
        # Create feature vector
        X = np.array([[features[col] for col in self.feature_columns]])
        
        # Predict (returns 0-1, scale to 0-10)
        prediction = self.model.predict(X, verbose=0)[0][0]
        rating = np.clip(prediction * 10, 0, 10)  # Scale to 0-10
        
        return float(rating)
    
    def save_model(self, model_name: str = "ann_movie_predictor"):
        """Save the trained model and scaler."""
        if self.model is None:
            raise ValueError("No model to save!")
        
        model_file = os.path.join(self.model_path, f"{model_name}.h5")
        features_file = os.path.join(self.model_path, f"{model_name}_features.json")
        
        # Save model
        self.model.save(model_file)
        
        # Save feature columns
        with open(features_file, 'w') as f:
            json.dump({
                'feature_columns': self.feature_columns,
                'genres': self.genres
            }, f, indent=2)
        
        logger.info(f"💾 Model saved to {model_file}")
    
    def load_model(self, model_name: str = "ann_movie_predictor"):
        """Load a saved model."""
        model_file = os.path.join(self.model_path, f"{model_name}.h5")
        features_file = os.path.join(self.model_path, f"{model_name}_features.json")
        
        if not os.path.exists(model_file):
            raise FileNotFoundError(f"Model file not found: {model_file}")
        
        # Load model
        self.model = keras.models.load_model(model_file)
        
        # Load feature columns
        if os.path.exists(features_file):
            with open(features_file, 'r') as f:
                config = json.load(f)
                self.feature_columns = config['feature_columns']
                self.genres = config['genres']
        
        logger.info(f"📂 Model loaded from {model_file}")
    
    def plot_training_history(self, save_path: Optional[str] = None):
        """Plot training history."""
        if self.history is None:
            logger.warning("No training history available")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss plot
        ax1.plot(self.history.history['loss'], label='Training Loss')
        ax1.plot(self.history.history['val_loss'], label='Validation Loss')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss (MSE)')
        ax1.legend()
        ax1.grid(True)
        
        # MAE plot
        ax1.plot(self.history.history['mae'], label='Training MAE')
        ax1.plot(self.history.history['val_mae'], label='Validation MAE')
        ax2.set_title('Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"📊 Training plots saved to {save_path}")
        
        plt.show()


def train_ann_model(csv_path: str, 
                   sample_size: Optional[int] = None,
                   test_size: float = 0.2,
                   model_name: str = "ann_movie_predictor") -> ANNMoviePredictor:
    """
    Complete training pipeline for the ANN model.
    
    Args:
        csv_path: Path to preprocessed training data
        sample_size: Optional limit on training samples
        test_size: Fraction for test set
        model_name: Name for saving the model
        
    Returns:
        Trained ANNMoviePredictor instance
    """
    logger.info("🎬 Starting ANN Movie Predictor Training Pipeline")
    logger.info("=" * 60)
    
    # Initialize predictor
    predictor = ANNMoviePredictor()
    
    # Prepare data
    X, y = predictor.prepare_training_data(csv_path, sample_size)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=True
    )
    
    logger.info(f"📊 Data split: Train {X_train.shape[0]}, Test {X_test.shape[0]}")
    
    # Train model
    predictor.train(X_train, y_train, epochs=100, batch_size=64)
    
    # Evaluate
    metrics = predictor.evaluate(X_test, y_test)
    
    # Save model
    predictor.save_model(model_name)
    
    logger.info("✅ ANN Training Pipeline Completed!")
    logger.info("=" * 60)
    
    return predictor


# Example usage and testing
if __name__ == "__main__":
    # Test with preprocessed data
    csv_path = "processed/preprocessed_movielens10M.csv"
    
    if os.path.exists(csv_path):
        # Train model (use sample for quick testing)
        predictor = train_ann_model(csv_path, sample_size=10000)
        
        # Test prediction
        user_prefs = {
            'action': 8.5,
            'comedy': 6.0,
            'romance': 3.0,
            'thriller': 7.5,
            'sci_fi': 8.0,
            'drama': 5.5,
            'horror': 2.0
        }
        
        movie_info = {
            'genres': ['Action', 'Sci-Fi'],
            'popularity': 85,
            'year': 2019
        }
        
        watch_history = {
            'liked_ratio': 0.75,
            'disliked_ratio': 0.15,
            'watch_count': 25
        }
        
        prediction = predictor.predict(user_prefs, movie_info, watch_history)
        print(f"\n🎯 Test Prediction: {prediction:.2f}/10")
        
    else:
        print(f"❌ Training data not found at {csv_path}")
        print("Please run the data preprocessing script first.")