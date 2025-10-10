"""
Simplified ANN Training Script for Movie Recommendation System
=============================================================

This script trains the ANN model using the preprocessed MovieLens data.
It handles the full pipeline from data loading to model training and evaluation.
🎯 Sample Prediction Test:
   Predicted Rating: 3.64/5.0
   Actual Rating: 5.00/5.0
   Difference: 1.36

✅ ANN Training Completed Successfully!
📊 Final Metrics:
   MAE: 0.832
   RMSE: 1.033
   R²: 0.018

User preference features (_pref): 7

action_pref

comedy_pref

romance_pref

thriller_pref

sci_fi_pref

drama_pref

horror_pref

Movie genre features (genre_): 7

genre_action

genre_comedy

genre_romance

genre_thriller

genre_sci_fi

genre_drama

genre_horror

Other numeric features: 5

popularity

year_norm

watch_count_norm

liked_ratio

disliked_ratio

OUTPUT:
Predicted Rating: 3.64/5.0
Actual Rating: 5.00/5.0
"""

import os
import pandas as pd
import numpy as np
import tensorflow as tf
import keras
from keras import layers, callbacks, optimizers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

class SimpleANNTrainer:
    """Simplified ANN trainer for movie recommendations."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.genres = ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror']
        self.feature_columns = []
        self.history = None
    
    def load_and_prepare_data(self, csv_path, sample_size=50000):
        """Load and prepare training data from CSV."""
        logger.info(f"📊 Loading data from {csv_path}")
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Data file not found: {csv_path}")
        
        # Load data with sampling for manageable training
        data = pd.read_csv(csv_path, nrows=sample_size)
        logger.info(f"📈 Loaded {len(data)} samples")
        
        # Basic feature engineering
        features_df = self._engineer_features(data)
        
        # Extract features and target
        X = features_df[self.feature_columns].values
        y = features_df['rating'].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.5)
        y = np.nan_to_num(y, nan=3.0)
        
        # Scale features
        X = self.scaler.fit_transform(X)
        
        # Scale target to 0-1 for training
        y = (y - 0.5) / 4.5  # Scale 0.5-5.0 to 0-1
        
        logger.info(f"✅ Prepared data: X shape {X.shape}, y shape {y.shape}")
        return X, y
    
    def _engineer_features(self, data):
        """Engineer features from raw data."""
        logger.info("🔧 Engineering features...")
        
        # Create basic features - we'll use what's available in the CSV
        features = data.copy()
        
        # Movie genre features (use genre columns if they exist)
        genre_cols = [col for col in data.columns if col.startswith('genre_')]
        if not genre_cols:
            # Create dummy genre features if not present
            for genre in self.genres:
                features[f'genre_{genre}'] = np.random.randint(0, 2, len(data))
        
        # User preference features (simulate from user's average ratings)
        if 'user_id' in data.columns:
            user_avg_ratings = data.groupby('user_id')['rating'].mean()
            for genre in self.genres:
                # Simulate user preferences based on their average rating
                pref_col = f'{genre}_pref'
                features[pref_col] = features['user_id'].map(user_avg_ratings).fillna(3.0) * 2
        else:
            # Create dummy preferences
            for genre in self.genres:
                features[f'{genre}_pref'] = np.random.uniform(2, 8, len(data))
        
        # Movie popularity (based on how many times it appears)
        if 'movie_id' in data.columns:
            movie_counts = data['movie_id'].value_counts()
            features['popularity'] = features['movie_id'].map(movie_counts).fillna(1)
            features['popularity'] = np.log10(features['popularity'] + 1) / 4  # Normalize
        else:
            features['popularity'] = np.random.uniform(0.1, 1.0, len(data))
        
        # Watch history features (simulate)
        features['watch_count_norm'] = np.random.uniform(0.1, 1.0, len(data))
        features['liked_ratio'] = np.random.uniform(0.3, 0.9, len(data))
        features['disliked_ratio'] = np.random.uniform(0.1, 0.4, len(data))
        
        # Year feature (if available)
        if 'year' in data.columns:
            features['year_norm'] = (features['year'] - 1900) / 130
        else:
            features['year_norm'] = np.random.uniform(0.5, 1.0, len(data))
        
        # Define feature columns
        self.feature_columns = (
            [f'{genre}_pref' for genre in self.genres] +
            [f'genre_{genre}' for genre in self.genres] +
            ['popularity', 'year_norm', 'watch_count_norm', 'liked_ratio', 'disliked_ratio']
        )
        
        logger.info(f"✅ Created {len(self.feature_columns)} features")
        return features
    
    def build_model(self, input_dim):
        """Build the ANN model."""
        logger.info(f"🏗️ Building ANN model with {input_dim} features...")
        
        model = keras.Sequential([
            layers.Input(shape=(input_dim,)),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.15),
            layers.Dense(16, activation='relu'),
            layers.Dropout(0.1),
            layers.Dense(1, activation='sigmoid')  # sigmoid for 0-1 output
        ])
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info("✅ Model built and compiled")
        model.summary()
        return model
    
    def train(self, X, y, epochs=50, batch_size=64, validation_split=0.2):
        """Train the model."""
        logger.info("🚀 Starting model training...")
        
        self.model = self.build_model(X.shape[1])
        
        # Setup callbacks
        callbacks_list = [
            callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                verbose=1
            )
        ]
        
        # Train the model
        self.history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list,
            verbose=1
        )
        
        logger.info("✅ Training completed!")
        return self.history
    
    def evaluate(self, X_test, y_test):
        """Evaluate the model."""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        logger.info("📊 Evaluating model...")
        
        # Get predictions
        y_pred = self.model.predict(X_test, verbose=0)
        
        # Scale back to 0.5-5.0 rating scale
        y_test_scaled = y_test * 4.5 + 0.5
        y_pred_scaled = y_pred.flatten() * 4.5 + 0.5
        
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
        
        logger.info(f"📈 Model Performance (0.5-5.0 scale):")
        logger.info(f"   MAE: {mae:.3f}")
        logger.info(f"   RMSE: {rmse:.3f}")
        logger.info(f"   R²: {r2:.3f}")
        
        return metrics
    
    def save_model(self, model_name="simple_ann_predictor"):
        """Save the trained model."""
        if self.model is None:
            raise ValueError("No model to save!")
        
        os.makedirs("models", exist_ok=True)
        model_file = f"models/{model_name}.h5"
        
        self.model.save(model_file)
        logger.info(f"💾 Model saved to {model_file}")
    
    def predict_sample(self, X_sample):
        """Make a sample prediction."""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Scale the input
        X_scaled = self.scaler.transform(X_sample.reshape(1, -1))
        
        # Predict (0-1 scale)
        pred_scaled = self.model.predict(X_scaled, verbose=0)[0][0]
        
        # Convert back to 0.5-5.0 rating scale
        rating = pred_scaled * 4.5 + 0.5
        
        return max(0.5, min(5.0, rating))


def train_simple_ann(csv_path="processed/preprocessed_movielens10M.csv", 
                    sample_size=50000):
    """Main training function."""
    print("🤖 SIMPLIFIED ANN TRAINING FOR MOVIE RECOMMENDATIONS")
    print("=" * 60)
    
    try:
        # Initialize trainer
        trainer = SimpleANNTrainer()
        
        # Load and prepare data
        X, y = trainer.load_and_prepare_data(csv_path, sample_size)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        logger.info(f"📊 Data split: Train {X_train.shape[0]}, Test {X_test.shape[0]}")
        
        # Train model
        trainer.train(X_train, y_train, epochs=30, batch_size=64)
        
        # Evaluate model
        metrics = trainer.evaluate(X_test, y_test)
        
        # Save model
        trainer.save_model("movie_ann_model")
        
        # Test sample prediction
        sample_features = X_test[0]
        sample_rating = trainer.predict_sample(sample_features)
        actual_rating = y_test[0] * 4.5 + 0.5
        
        print(f"\n🎯 Sample Prediction Test:")
        print(f"   Predicted Rating: {sample_rating:.2f}/5.0")
        print(f"   Actual Rating: {actual_rating:.2f}/5.0")
        print(f"   Difference: {abs(sample_rating - actual_rating):.2f}")
        
        print(f"\n✅ ANN Training Completed Successfully!")
        print(f"📊 Final Metrics:")
        print(f"   MAE: {metrics['mae']:.3f}")
        print(f"   RMSE: {metrics['rmse']:.3f}")
        print(f"   R²: {metrics['r2_score']:.3f}")
        
        return trainer
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Check if data exists
    csv_path = "processed/preprocessed_movielens10M.csv"
    
    if os.path.exists(csv_path):
        trainer = train_simple_ann(csv_path, sample_size=10000)  # Small sample for testing
    else:
        print(f"❌ Training data not found at: {csv_path}")
        print("Please ensure the data preprocessing has been completed first.")