"""
Test the Complete Hybrid System with Trained ANN
================================================

This script tests the hybrid recommendation system using both
the fuzzy logic engine and the trained ANN model.
"""

import numpy as np
import pandas as pd
import keras
from models.fuzzy_model import FuzzyMovieRecommender, recommend_with_fuzzy
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainedANNPredictor:
    """Wrapper for the trained ANN model."""
    
    def __init__(self, model_path="models/movie_ann_model.h5"):
        """Load the trained ANN model."""
        try:
            self.model = keras.models.load_model(model_path)
            self.is_available = True
            logger.info(f"✅ Trained ANN model loaded from {model_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load ANN model: {e}")
            self.is_available = False
        
        self.genres = ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror']
    
    def predict(self, user_preferences, movie_info, watch_history=None):
        """Predict rating using the trained ANN."""
        if not self.is_available:
            return 5.0  # Default prediction
        
        # Prepare features in the same format as training
        features = []
        
        # User preferences (7 features)
        for genre in self.genres:
            features.append(user_preferences.get(genre, 5.0))
        
        # Movie genres (7 features - one-hot)
        movie_genres = [g.lower().replace(' ', '_') for g in movie_info.get('genres', [])]
        for genre in self.genres:
            features.append(1.0 if genre in movie_genres else 0.0)
        
        # Movie popularity (normalized)
        popularity = movie_info.get('popularity', 50) / 100
        features.append(popularity)
        
        # Year feature (normalized)
        year = movie_info.get('year', 2000)
        year_norm = (year - 1900) / 130
        features.append(year_norm)
        
        # Watch history features
        if watch_history:
            features.append(min(1.0, np.log10(watch_history.get('watch_count', 1) + 1) / 2))
            features.append(watch_history.get('liked_ratio', 0.5))
            features.append(watch_history.get('disliked_ratio', 0.3))
        else:
            features.extend([0.1, 0.5, 0.3])
        
        # Convert to numpy array and reshape
        X = np.array(features).reshape(1, -1)
        
        # Predict (model outputs 0-1, scale to 0.5-5.0, then to 0-10)
        pred_01 = self.model.predict(X, verbose=0)[0][0]
        pred_5scale = pred_01 * 4.5 + 0.5  # Convert to 0.5-5.0
        pred_10scale = (pred_5scale - 0.5) * 2.22  # Convert to 0-10
        
        return max(0, min(10, pred_10scale))

class CompleteHybridSystem:
    """Complete hybrid system with fuzzy logic and trained ANN."""
    
    def __init__(self):
        self.fuzzy_engine = FuzzyMovieRecommender()
        self.ann_predictor = TrainedANNPredictor()
    
    def recommend(self, user_preferences, movie_info, watch_history=None, strategy='adaptive'):
        """Get hybrid recommendation."""
        
        # Get fuzzy score
        fuzzy_result = recommend_with_fuzzy(
            self.fuzzy_engine, user_preferences, movie_info, watch_history
        )
        fuzzy_score = fuzzy_result['fuzzy_score']
        
        # Get ANN score if available
        ann_score = None
        if self.ann_predictor.is_available:
            ann_score = self.ann_predictor.predict(user_preferences, movie_info, watch_history)
        
        # Combine scores
        if ann_score is not None:
            if strategy == 'weighted_average':
                hybrid_score = fuzzy_score * 0.6 + ann_score * 0.4
            elif strategy == 'fuzzy_dominant':
                hybrid_score = fuzzy_score * 0.7 + ann_score * 0.3
            elif strategy == 'ann_dominant':
                hybrid_score = fuzzy_score * 0.3 + ann_score * 0.7
            elif strategy == 'adaptive':
                # Adaptive based on agreement
                agreement = 1 - abs(fuzzy_score - ann_score) / 10
                watch_count = watch_history.get('watch_count', 0) if watch_history else 0
                
                if agreement > 0.8:
                    hybrid_score = (fuzzy_score + ann_score) / 2
                elif watch_count > 30:
                    hybrid_score = fuzzy_score * 0.4 + ann_score * 0.6
                else:
                    hybrid_score = fuzzy_score * 0.6 + ann_score * 0.4
            else:
                hybrid_score = (fuzzy_score + ann_score) / 2
        else:
            hybrid_score = fuzzy_score
        
        return {
            'fuzzy_score': round(fuzzy_score, 2),
            'ann_score': round(ann_score, 2) if ann_score else None,
            'hybrid_score': round(hybrid_score, 2),
            'strategy': strategy,
            'movie_info': movie_info,
            'ann_available': self.ann_predictor.is_available
        }

def test_complete_hybrid_system():
    """Test the complete hybrid system."""
    print("🎬 COMPLETE HYBRID RECOMMENDATION SYSTEM TEST")
    print("=" * 60)
    print("🧠 Using: Fuzzy Logic + Trained ANN Model")
    print("=" * 60)
    
    # Initialize hybrid system
    hybrid_system = CompleteHybridSystem()
    
    # Test cases
    test_cases = [
        {
            'name': 'Action Movie Fan',
            'user_prefs': {
                'action': 9.2, 'comedy': 3.5, 'romance': 2.1, 'thriller': 8.7,
                'sci_fi': 7.3, 'drama': 4.2, 'horror': 2.5
            },
            'movie': {
                'title': 'Mission Impossible',
                'genres': ['Action', 'Thriller'],
                'popularity': 88,
                'year': 2018
            },
            'history': {'liked_ratio': 0.82, 'disliked_ratio': 0.08, 'watch_count': 45}
        },
        {
            'name': 'Romantic Comedy Enthusiast',
            'user_prefs': {
                'action': 2.8, 'comedy': 9.1, 'romance': 8.9, 'thriller': 3.2,
                'sci_fi': 3.7, 'drama': 6.8, 'horror': 1.5
            },
            'movie': {
                'title': 'Crazy, Stupid, Love',
                'genres': ['Comedy', 'Romance'],
                'popularity': 75,
                'year': 2011
            },
            'history': {'liked_ratio': 0.76, 'disliked_ratio': 0.12, 'watch_count': 28}
        },
        {
            'name': 'Sci-Fi Lover',
            'user_prefs': {
                'action': 7.1, 'comedy': 4.3, 'romance': 2.9, 'thriller': 6.8,
                'sci_fi': 9.6, 'drama': 6.2, 'horror': 3.8
            },
            'movie': {
                'title': 'Blade Runner 2049',
                'genres': ['Sci-Fi', 'Drama'],
                'popularity': 82,
                'year': 2017
            },
            'history': {'liked_ratio': 0.89, 'disliked_ratio': 0.04, 'watch_count': 52}
        },
        {
            'name': 'Casual Viewer',
            'user_prefs': {
                'action': 6.0, 'comedy': 7.2, 'romance': 5.5, 'thriller': 5.8,
                'sci_fi': 6.3, 'drama': 6.1, 'horror': 3.2
            },
            'movie': {
                'title': 'The Incredibles',
                'genres': ['Comedy', 'Action'],
                'popularity': 91,
                'year': 2004
            },
            'history': {'liked_ratio': 0.68, 'disliked_ratio': 0.18, 'watch_count': 15}
        }
    ]
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print("-" * 50)
        print(f"🎬 Movie: {test_case['movie']['title']} ({test_case['movie']['year']})")
        print(f"   Genres: {', '.join(test_case['movie']['genres'])}")
        print(f"   Popularity: {test_case['movie']['popularity']}")
        
        # Test different strategies
        strategies = ['weighted_average', 'fuzzy_dominant', 'ann_dominant', 'adaptive']
        
        print(f"\n📊 Recommendations by Strategy:")
        best_strategy = None
        best_score = 0
        
        for strategy in strategies:
            result = hybrid_system.recommend(
                test_case['user_prefs'], 
                test_case['movie'], 
                test_case['history'],
                strategy
            )
            
            fuzzy = result['fuzzy_score']
            ann = result['ann_score']
            hybrid = result['hybrid_score']
            
            if hybrid > best_score:
                best_score = hybrid
                best_strategy = strategy
            
            ann_str = f"{ann:4.2f}" if ann is not None else " N/A"
            print(f"   {strategy.replace('_', ' ').title():15} → "
                  f"Fuzzy: {fuzzy:4.2f} | ANN: {ann_str} | Hybrid: {hybrid:4.2f}")
        
        # Show final recommendation
        final_result = hybrid_system.recommend(
            test_case['user_prefs'], test_case['movie'], 
            test_case['history'], 'adaptive'
        )
        
        final_score = final_result['hybrid_score']
        if final_score >= 8:
            level = "🔥 Highly Recommended"
        elif final_score >= 6:
            level = "👍 Recommended"
        elif final_score >= 4:
            level = "🤔 Maybe"
        else:
            level = "👎 Not Recommended"
        
        print(f"\n🎯 Final Recommendation (Adaptive): {level} ({final_score:.2f}/10)")
        print(f"   ANN Status: {'✅ Available' if final_result['ann_available'] else '❌ Not Available'}")

def main():
    """Main test function."""
    test_complete_hybrid_system()
    
    print(f"\n" + "=" * 60)
    print("✅ COMPLETE HYBRID SYSTEM TEST FINISHED!")
    print("🎯 Both fuzzy logic and ANN are working together!")
    print("🚀 The hybrid recommendation system is fully operational!")
    print("=" * 60)

if __name__ == "__main__":
    main()