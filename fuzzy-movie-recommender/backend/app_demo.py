"""
Demo Flask App - Fuzzy Movie Recommendation System
This version works without TensorFlow for immediate testing
"""

import os
import sys
import logging
from datetime import datetime
import json
import traceback
import numpy as np
import pandas as pd

from flask import Flask, request, jsonify
from flask_cors import CORS

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.fuzzy_model import FuzzyMovieRecommender
from utils import setup_logging, log_performance

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    return app

app = create_app()

# Mock ANN Model for demo
class MockANNModel:
    def __init__(self):
        self.is_trained = False
        
    def predict_batch(self, user_ids, movie_ids):
        # Return mock predictions based on movie_id
        return [5.0 + (mid % 5) for mid in movie_ids]
    
    def predict_for_user(self, user_id, movie_ids, top_k=10):
        predictions = self.predict_batch([user_id] * len(movie_ids), movie_ids)
        results = []
        for mid, pred in zip(movie_ids, predictions):
            results.append({
                'movie_id': mid,
                'predicted_rating': pred
            })
        return sorted(results, key=lambda x: x['predicted_rating'], reverse=True)[:top_k]
    
    def train(self, *args, **kwargs):
        self.is_trained = True
        class MockHistory:
            def __init__(self):
                self.history = {'loss': [1.0, 0.8, 0.6, 0.4, 0.3]}
        return MockHistory()

# Mock Hybrid Model for demo
class MockHybridModel:
    def __init__(self, fuzzy_model, ann_model):
        self.fuzzy_model = fuzzy_model
        self.ann_model = ann_model
    
    def predict_single_movie(self, user_id, user_preferences, movie_data, user_history=None, method='adaptive'):
        # Get fuzzy prediction
        fuzzy_result = self.fuzzy_model.predict_single_movie(user_preferences, movie_data, user_history)
        
        # Get mock ANN prediction
        ann_score = self.ann_model.predict_batch([user_id], [movie_data['movie_id']])[0]
        
        # Simple weighted combination
        final_score = 0.6 * fuzzy_result['fuzzy_score'] + 0.4 * ann_score
        
        return {
            'movie_id': movie_data['movie_id'],
            'title': movie_data.get('title', f"Movie {movie_data['movie_id']}"),
            'genres': movie_data.get('genres', []),
            'final_score': round(final_score, 2),
            'fuzzy_score': fuzzy_result['fuzzy_score'],
            'ann_score': round(ann_score, 2),
            'explanation': f"Fuzzy: {fuzzy_result['explanation']} | ANN: Predicted rating {ann_score:.1f}",
            'combination_method': method
        }
    
    def predict_batch(self, user_id, user_preferences, movies_data, user_history=None, top_k=10, method='adaptive'):
        results = []
        for movie_data in movies_data:
            result = self.predict_single_movie(user_id, user_preferences, movie_data, user_history, method)
            results.append(result)
        
        # Sort by final score and return top_k
        results.sort(key=lambda x: x['final_score'], reverse=True)
        return results[:top_k]

# Create sample movie data
def create_sample_data():
    """Create sample movie data for demo"""
    genres_list = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller', 'Adventure']
    
    movies_data = []
    for i in range(1, 101):  # 100 sample movies
        movie = {
            'movie_id': i,
            'title': f"Sample Movie {i}",
            'genres': np.random.choice(genres_list, size=np.random.randint(1, 4), replace=False).tolist(),
            'popularity': np.random.uniform(10, 90),
            'year': np.random.randint(1990, 2024)
        }
        movies_data.append(movie)
    
    return pd.DataFrame(movies_data)

# Initialize models and data
logger.info("Initializing demo models and data...")

try:
    # Create sample data
    movies_df = create_sample_data()
    logger.info(f"Created {len(movies_df)} sample movies")
    
    # Initialize models
    fuzzy_model = FuzzyMovieRecommender()
    ann_model = MockANNModel()
    hybrid_model = MockHybridModel(fuzzy_model, ann_model)
    
    logger.info("Demo models initialized successfully")
    
except Exception as e:
    logger.error(f"Error initializing models: {e}")
    traceback.print_exc()

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0-demo',
        'mode': 'demo'
    })

@app.route('/api/user/preferences', methods=['POST'])
@log_performance
def get_user_recommendations():
    """Get personalized movie recommendations"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract request parameters
        user_preferences = data.get('user_preferences', {})
        watched_movies = data.get('watched_movies', [])
        top_k = data.get('top_k', 10)
        
        if not user_preferences:
            return jsonify({'error': 'user_preferences is required'}), 400
        
        # Create mock user history from watched movies
        user_history = None
        if watched_movies:
            # Find movies in our sample data that match watched titles
            matched_movies = movies_df[movies_df['title'].str.contains('|'.join(watched_movies), case=False, na=False)]
            if not matched_movies.empty:
                user_history = matched_movies.copy()
                user_history['rating'] = np.random.uniform(3.5, 5.0, len(matched_movies))
        
        # Get all movies for recommendation
        movies_data = movies_df.to_dict('records')
        
        # Get recommendations using hybrid model
        recommendations = hybrid_model.predict_batch(
            user_id=1,  # Mock user ID
            user_preferences=user_preferences,
            movies_data=movies_data,
            user_history=user_history,
            top_k=top_k
        )
        
        return jsonify({
            'recommendations': recommendations,
            'total_movies_considered': len(movies_data),
            'user_preferences': user_preferences,
            'watched_movies': watched_movies,
            'processing_time': 0.1  # Mock processing time
        })
        
    except Exception as e:
        logger.error(f"Error in get_user_recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """Get details for a specific movie"""
    try:
        movie = movies_df[movies_df['movie_id'] == movie_id]
        
        if movie.empty:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie_data = movie.iloc[0].to_dict()
        return jsonify(movie_data)
        
    except Exception as e:
        logger.error(f"Error in get_movie_details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/train/ann', methods=['POST'])
def train_ann_model():
    """Trigger ANN model training (mock for demo)"""
    try:
        history = ann_model.train()
        
        return jsonify({
            'status': 'success',
            'message': 'ANN model training completed (demo mode)',
            'training_history': history.history
        })
        
    except Exception as e:
        logger.error(f"Error in train_ann_model: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/train/fuzzy', methods=['POST'])
def reinitialize_fuzzy_model():
    """Re-initialize fuzzy model"""
    try:
        global fuzzy_model
        fuzzy_model = FuzzyMovieRecommender()
        
        return jsonify({
            'status': 'success',
            'message': 'Fuzzy model re-initialized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in reinitialize_fuzzy_model: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_movies():
    """Search for movies"""
    try:
        query = request.args.get('query', '').lower()
        limit = int(request.args.get('limit', 20))
        
        if not query:
            return jsonify({'movies': []})
        
        # Simple search in movie titles
        filtered_movies = movies_df[movies_df['title'].str.contains(query, case=False, na=False)]
        results = filtered_movies.head(limit).to_dict('records')
        
        return jsonify({'movies': results})
        
    except Exception as e:
        logger.error(f"Error in search_movies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Get list of all genres"""
    try:
        all_genres = set()
        for genres_list in movies_df['genres']:
            all_genres.update(genres_list)
        
        return jsonify({'genres': sorted(list(all_genres))})
        
    except Exception as e:
        logger.error(f"Error in get_genres: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dataset statistics"""
    try:
        stats = {
            'total_movies': len(movies_df),
            'total_ratings': 5000,  # Mock
            'total_users': 100,     # Mock
            'avg_rating': 3.8,      # Mock
            'mode': 'demo'
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Fuzzy Movie Recommendation System (Demo Mode)")
    logger.info(f"Server running on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
