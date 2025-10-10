"""
Enhanced ANN Model for Real Movie Recommendations
===============================================

This module provides an enhanced ANN model that works with real movie data,
providing detailed predictions and explanations.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import joblib
import json
import os
from typing import Dict, List, Optional, Tuple

# Try to import from fast_complete_loader, fallback to other sources
try:
    from fast_complete_loader import get_fast_complete_database, get_recommendation_explanation
    REAL_MOVIES_DATABASE = None  # Will be loaded on demand
    GENRE_MAPPING = {
        'action': 'Action', 'comedy': 'Comedy', 'drama': 'Drama',
        'horror': 'Horror', 'romance': 'Romance', 'sci_fi': 'Sci-Fi',
        'thriller': 'Thriller'
    }
except ImportError:
    try:
        from real_movies_db import REAL_MOVIES_DATABASE, GENRE_MAPPING, get_recommendation_explanation
    except ImportError:
        REAL_MOVIES_DATABASE = []
        GENRE_MAPPING = {}
        def get_recommendation_explanation(*args, **kwargs):
            return "Recommendation based on your preferences"

class EnhancedANNModel:
    """Enhanced ANN model for movie recommendations with real data."""
    
    def __init__(self, model_path='models/enhanced_ann_model.keras'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.is_loaded = False
        
    def load_model(self):
        """Load the trained model and preprocessing components."""
        try:
            # Load model
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
            else:
                print(f"⚠️ Enhanced ANN model not found at {self.model_path}")
                print("   Please run train_enhanced_ann.py first")
                return False
            
            # Load scaler
            scaler_path = self.model_path.replace('.keras', '_scaler.joblib')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            else:
                print(f"⚠️ Scaler not found at {scaler_path}")
                return False
            
            # Load features
            feature_path = self.model_path.replace('.keras', '_features.json')
            if os.path.exists(feature_path):
                with open(feature_path, 'r') as f:
                    data = json.load(f)
                    self.feature_columns = data['feature_columns']
            else:
                print(f"⚠️ Features not found at {feature_path}")
                return False
            
            self.is_loaded = True
            print(f"✅ Enhanced ANN model loaded successfully")
            print(f"   Features: {len(self.feature_columns)}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading enhanced ANN model: {e}")
            return False
    
    def predict_rating(self, user_preferences: Dict[str, float], movie: Dict) -> Optional[float]:
        """Predict rating for a movie based on user preferences."""
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        try:
            # Prepare feature vector
            features = self._prepare_features(user_preferences, movie)
            
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Make prediction
            prediction = self.model.predict(features_scaled, verbose=0)[0][0]
            
            # Clamp to valid range
            return max(1.0, min(10.0, float(prediction)))
            
        except Exception as e:
            print(f"❌ Error predicting rating: {e}")
            return None
    
    def _prepare_features(self, user_prefs: Dict[str, float], movie: Dict) -> List[float]:
        """Prepare feature vector for prediction."""
        features = {}
        
        # Movie features
        features['movie_rating'] = movie.get('rating', 7.0)
        features['movie_popularity'] = movie.get('popularity', 80)
        features['movie_year'] = movie.get('year', 2000)
        features['movie_runtime'] = movie.get('runtime', 120)
        features['movie_budget'] = movie.get('budget', 50000000)
        features['movie_box_office'] = movie.get('box_office', 100000000)
        
        # User preference features
        for pref in ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror']:
            features[f'user_{pref}'] = user_prefs.get(pref, 5.0)
        
        # Genre features (one-hot encoding)
        movie_genres = movie.get('genres', [])
        for genre_key, genre_list in GENRE_MAPPING.items():
            features[f'movie_genre_{genre_key}'] = int(
                any(g in movie_genres for g in genre_list)
            )
        
        # Convert to list in correct order
        feature_vector = []
        for col in self.feature_columns:
            feature_vector.append(features.get(col, 0.0))
        
        return feature_vector
    
    def get_top_recommendations(self, user_preferences: Dict[str, float], 
                              num_recommendations: int = 10) -> List[Dict]:
        """Get top movie recommendations with detailed information."""
        if not self.is_loaded:
            if not self.load_model():
                return []
        
        recommendations = []
        
        for movie in REAL_MOVIES_DATABASE:
            # Predict rating
            predicted_rating = self.predict_rating(user_preferences, movie)
            
            if predicted_rating is not None:
                # Calculate confidence based on genre match
                confidence = self._calculate_confidence(user_preferences, movie)
                
                # Generate explanation
                scores = {
                    'ann_score': predicted_rating,
                    'confidence': confidence
                }
                explanation = get_recommendation_explanation(user_preferences, movie, scores)
                
                recommendation = {
                    'id': movie['id'],
                    'title': movie['title'],
                    'year': movie['year'],
                    'genres': movie['genres'],
                    'poster_url': movie['poster_url'],
                    'description': movie['description'],
                    'director': movie['director'],
                    'cast': movie['cast'][:3],  # Top 3 cast members
                    'rating': movie['rating'],
                    'runtime': movie['runtime'],
                    'predicted_rating': predicted_rating,
                    'confidence': confidence,
                    'explanation': explanation,
                    'popularity': movie['popularity']
                }
                
                recommendations.append(recommendation)
        
        # Sort by predicted rating
        recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
        
        return recommendations[:num_recommendations]
    
    def _calculate_confidence(self, user_prefs: Dict[str, float], movie: Dict) -> float:
        """Calculate confidence score based on genre matching."""
        # Find user's favorite genres (score > 6)
        favorite_genres = {k: v for k, v in user_prefs.items() if v > 6}
        
        if not favorite_genres:
            return 0.5  # Neutral confidence
        
        # Check genre matches
        movie_genres = [g.lower() for g in movie['genres']]
        matches = 0
        total_pref_score = 0
        
        for pref_genre, score in favorite_genres.items():
            genre_clean = pref_genre.replace('_', ' ')
            if any(genre_clean in mg or mg in genre_clean for mg in movie_genres):
                matches += 1
                total_pref_score += score
        
        if matches == 0:
            return 0.3  # Low confidence for no matches
        
        # Calculate confidence based on matches and preference strength
        avg_pref_score = total_pref_score / matches
        match_ratio = matches / len(favorite_genres)
        
        confidence = (avg_pref_score / 10) * 0.7 + match_ratio * 0.3
        
        return min(1.0, max(0.0, confidence))
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_path": self.model_path,
            "num_features": len(self.feature_columns) if self.feature_columns else 0,
            "features": self.feature_columns[:10] if self.feature_columns else [],  # First 10 features
            "model_summary": str(self.model.summary()) if self.model else None
        }


# Fallback simple ANN for compatibility
class SimpleANNModel:
    """Simple ANN model for basic compatibility."""
    
    def __init__(self):
        self.is_loaded = False
    
    def load_model(self):
        """Simulate loading for compatibility."""
        self.is_loaded = True
        return True
    
    def predict_rating(self, user_preferences: Dict[str, float], movie: Dict) -> float:
        """Simple prediction based on genre matching."""
        # Simple genre-based prediction
        movie_genres = [g.lower() for g in movie.get('genres', [])]
        
        score = 5.0  # Base score
        
        # Check genre preferences
        for pref, value in user_preferences.items():
            pref_clean = pref.replace('_', ' ')
            if any(pref_clean in mg or mg in pref_clean for mg in movie_genres):
                score += (value - 5) * 0.3
        
        # Add movie quality influence
        if 'rating' in movie:
            score += (movie['rating'] - 7) * 0.4
        
        return max(1.0, min(10.0, score))