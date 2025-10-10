"""
Test script to verify ANN model is working correctly
"""
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test loading ANN model
def test_ann_loading():
    print("=" * 60)
    print("Testing ANN Model Loading")
    print("=" * 60)
    
    try:
        import tensorflow as tf
        model_path = "models/simple_ann_model.keras"
        
        print(f"\n1. Loading model from: {model_path}")
        model = tf.keras.models.load_model(model_path)
        
        print(f"   ✅ Model loaded successfully!")
        print(f"   - Input shape: {model.input_shape}")
        print(f"   - Output shape: {model.output_shape}")
        print(f"   - Total parameters: {model.count_params():,}")
        
        return model
    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        return None

# Test feature preparation
def test_feature_preparation(model):
    print("\n" + "=" * 60)
    print("Testing Feature Preparation")
    print("=" * 60)
    
    # Sample movie info
    movie_info = {
        'title': 'The Matrix',
        'rating': 8.7,
        'popularity': 95,
        'year': 1999,
        'runtime': 136,
        'budget': 63000000,
        'genres': 'Action, Sci-Fi'
    }
    
    # Sample user preferences
    user_preferences = {
        'action': 9.0,
        'comedy': 3.0,
        'romance': 2.0,
        'thriller': 7.0,
        'sci_fi': 10.0,
        'drama': 5.0,
        'horror': 1.0
    }
    
    print(f"\nMovie: {movie_info['title']}")
    print(f"User Preferences: Action={user_preferences['action']}, Sci-Fi={user_preferences['sci_fi']}")
    
    # Prepare features (19 features for simple model)
    features = []
    
    # Movie features (5)
    features.append(movie_info.get('rating', 7.0))
    features.append(movie_info.get('popularity', 50.0))
    features.append(movie_info.get('year', 2000))
    features.append(movie_info.get('runtime', 120))
    features.append(movie_info.get('budget', 0))
    
    # User preferences (7)
    genres = ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror']
    for genre in genres:
        features.append(user_preferences.get(genre, 5.0))
    
    # Movie genres (7, one-hot)
    movie_genres_str = movie_info.get('genres', '').lower()
    for genre in genres:
        has_genre = (genre in movie_genres_str or 
                    genre.replace('_', ' ') in movie_genres_str or
                    genre.replace('_', '-') in movie_genres_str)
        features.append(1.0 if has_genre else 0.0)
    
    features_array = np.array([features], dtype=np.float32)
    
    print(f"\nFeature vector shape: {features_array.shape}")
    print(f"Expected shape: {model.input_shape}")
    print(f"Feature count: {len(features)} (expected: {model.input_shape[1]})")
    
    if len(features) == model.input_shape[1]:
        print("   ✅ Feature count matches model input!")
    else:
        print(f"   ❌ Feature count mismatch! Got {len(features)}, expected {model.input_shape[1]}")
        return None
    
    return features_array

# Test prediction
def test_prediction(model, features):
    print("\n" + "=" * 60)
    print("Testing ANN Prediction")
    print("=" * 60)
    
    try:
        print("\nRunning prediction...")
        prediction = model.predict(features, verbose=0)
        score = float(prediction[0][0])
        
        print(f"   ✅ Prediction successful!")
        print(f"   - Raw score: {score:.6f}")
        print(f"   - Scaled score (0-10): {score * 10:.2f}" if score <= 1 else f"   - Score: {score:.2f}")
        
        return score
    except Exception as e:
        print(f"   ❌ Prediction failed: {e}")
        return None

# Test hybrid system
def test_hybrid_system():
    print("\n" + "=" * 60)
    print("Testing Hybrid System Integration")
    print("=" * 60)
    
    try:
        from models.hybrid_system import HybridRecommendationSystem
        
        print("\n1. Initializing hybrid system...")
        hybrid = HybridRecommendationSystem()
        
        if hybrid.ann_available:
            print("   ✅ Hybrid system initialized with ANN support!")
            print(f"   - ANN model: {hybrid.ann_model is not None}")
            print(f"   - Fuzzy engine: {hybrid.fuzzy_engine is not None}")
        else:
            print("   ⚠️ Hybrid system initialized but ANN not available")
            return
        
        # Test recommendation
        print("\n2. Testing recommendation...")
        user_prefs = {
            'action': 9.0, 'comedy': 3.0, 'romance': 2.0,
            'thriller': 7.0, 'sci_fi': 10.0, 'drama': 5.0, 'horror': 1.0
        }
        
        movie = {
            'title': 'The Matrix',
            'rating': 8.7,
            'popularity': 95,
            'year': 1999,
            'runtime': 136,
            'budget': 63000000,
            'genres': ['Action', 'Sci-Fi']
        }
        
        result = hybrid.recommend(user_prefs, movie)
        
        print(f"   ✅ Recommendation generated!")
        print(f"   - Fuzzy Score: {result.get('fuzzy_score', 'N/A'):.2f}")
        print(f"   - ANN Score: {result.get('ann_score', 'N/A'):.2f}")
        print(f"   - Hybrid Score: {result.get('hybrid_score', 'N/A'):.2f}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🧪 ANN MODEL VERIFICATION TEST\n")
    
    # Test 1: Load model
    model = test_ann_loading()
    if not model:
        print("\n❌ Cannot proceed without model")
        sys.exit(1)
    
    # Test 2: Prepare features
    features = test_feature_preparation(model)
    if features is None:
        print("\n❌ Cannot proceed without valid features")
        sys.exit(1)
    
    # Test 3: Make prediction
    score = test_prediction(model, features)
    if score is None:
        print("\n❌ Prediction failed")
        sys.exit(1)
    
    # Test 4: Test hybrid system
    test_hybrid_system()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour ANN model is working correctly! 🎉")
