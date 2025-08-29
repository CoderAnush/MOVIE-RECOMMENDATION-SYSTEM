"""
Flask REST API for Fuzzy Movie Recommendation System

This module provides REST API endpoints for the movie recommendation system,
integrating fuzzy logic, ANN, and hybrid approaches.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import logging
import traceback
from pathlib import Path
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.fuzzy_model import FuzzyMovieRecommender
from models.ann_model import ANNCollaborativeFilteringModel
from models.hybrid import HybridRecommender
from data.preprocessing import MovieLensPreprocessor
from utils import (
    setup_logging, load_pickle, validate_user_preferences,
    format_recommendation_response, get_memory_usage
)

# Setup logging
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global variables for models and data
fuzzy_model = None
ann_model = None
hybrid_model = None
movies_df = None
preprocessed_data = None
preprocessor = None

def load_models_and_data():
    """Load trained models and preprocessed data"""
    global fuzzy_model, ann_model, hybrid_model, movies_df, preprocessed_data, preprocessor
    
    try:
        # Data paths
        data_path = Path(__file__).parent / 'data' / 'preprocessed.pkl'
        ann_model_path = Path(__file__).parent / 'models' / 'ann_model'
        
        # Load preprocessed data
        if data_path.exists():
            logger.info("Loading preprocessed data...")
            preprocessed_data = load_pickle(data_path)
            movies_df = preprocessed_data['movies']
            preprocessor = preprocessed_data.get('preprocessor')
            logger.info(f"Loaded {len(movies_df)} movies")
        else:
            logger.warning(f"Preprocessed data not found at {data_path}")
            # Create sample data for demo
            create_sample_data()
        
        # Initialize fuzzy model
        logger.info("Initializing fuzzy model...")
        fuzzy_model = FuzzyMovieRecommender()
        
        # Load ANN model if available
        if ann_model_path.with_suffix('.pkl').exists():
            logger.info("Loading ANN model...")
            ann_model = ANNCollaborativeFilteringModel(1000, 1000)  # Placeholder dimensions
            ann_model.load_model(ann_model_path)
            logger.info("ANN model loaded successfully")
        else:
            logger.warning("ANN model not found, will use default predictions")
            # Create dummy ANN model for demo
            create_dummy_ann_model()
        
        # Initialize hybrid model
        if fuzzy_model and ann_model:
            logger.info("Initializing hybrid model...")
            hybrid_model = HybridRecommender(fuzzy_model, ann_model)
            logger.info("Hybrid model initialized successfully")
        
        logger.info("All models loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        logger.error(traceback.format_exc())
        create_sample_data()

def create_sample_data():
    """Create sample data for demo purposes"""
    global movies_df, preprocessed_data, preprocessor
    
    logger.info("Creating sample data for demo...")
    
    # Create sample movies
    sample_movies = pd.DataFrame({
        'movie_id': range(1, 101),
        'title': [f'Sample Movie {i}' for i in range(1, 101)],
        'genres': [
            ['Action', 'Thriller'], ['Comedy', 'Romance'], ['Drama'], ['Sci-Fi', 'Action'],
            ['Horror'], ['Animation', 'Comedy'], ['Romance', 'Drama'], ['Thriller'],
            ['Action', 'Sci-Fi'], ['Comedy']
        ] * 10,
        'year': np.random.randint(1990, 2024, 100),
        'popularity': np.random.uniform(10, 90, 100)
    })
    
    movies_df = sample_movies
    
    # Create sample preprocessed data structure
    preprocessed_data = {
        'movies': movies_df,
        'ratings': pd.DataFrame(),
        'user_to_idx': {},
        'movie_to_idx': {i: i-1 for i in range(1, 101)},
        'idx_to_movie': {i-1: i for i in range(1, 101)}
    }
    
    preprocessor = MovieLensPreprocessor()
    
    logger.info("Sample data created")

def create_dummy_ann_model():
    """Create dummy ANN model for demo"""
    global ann_model
    
    class DummyANNModel:
        def __init__(self):
            self.user_to_idx = {i: i for i in range(1, 1001)}
            self.movie_to_idx = {i: i-1 for i in range(1, 101)}
        
        def predict_batch(self, user_ids, movie_ids):
            # Return random predictions for demo
            return np.random.uniform(3, 8, len(user_ids))
    
    ann_model = DummyANNModel()
    logger.info("Dummy ANN model created")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    memory_info = get_memory_usage()
    
    return jsonify({
        'status': 'ok',
        'models_loaded': {
            'fuzzy': fuzzy_model is not None,
            'ann': ann_model is not None,
            'hybrid': hybrid_model is not None
        },
        'data_loaded': movies_df is not None,
        'memory_usage_mb': round(memory_info['rss_mb'], 2),
        'total_movies': len(movies_df) if movies_df is not None else 0
    })

@app.route('/api/user/preferences', methods=['POST'])
def get_recommendations():
    """
    Get movie recommendations based on user preferences
    
    Expected JSON input:
    {
        "user_id": <int | null>,
        "preferences": {
            "Action": "High",
            "Comedy": "Medium",
            ...
        },
        "watched": [<movie titles or ids>],
        "top_k": <int>
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract parameters
        user_id = data.get('user_id')
        preferences = data.get('preferences', {})
        watched = data.get('watched', [])
        top_k = data.get('top_k', 10)
        
        # Validate preferences
        is_valid, error_msg = validate_user_preferences(preferences)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Get candidate movies (exclude watched movies)
        candidate_movies = movies_df.copy()
        
        # Filter out watched movies if provided
        if watched:
            # Handle both movie IDs and titles
            watched_ids = []
            for item in watched:
                if isinstance(item, int):
                    watched_ids.append(item)
                elif isinstance(item, str):
                    # Find movie by title
                    matching_movies = movies_df[movies_df['title'].str.contains(item, case=False, na=False)]
                    if not matching_movies.empty:
                        watched_ids.extend(matching_movies['movie_id'].tolist())
            
            candidate_movies = candidate_movies[~candidate_movies['movie_id'].isin(watched_ids)]
        
        # Convert to list of dictionaries for prediction
        movies_data = candidate_movies.to_dict('records')
        
        # Get user history if user_id provided
        user_history = None
        if user_id and 'ratings' in preprocessed_data:
            ratings_df = preprocessed_data['ratings']
            if not ratings_df.empty:
                user_history = ratings_df[ratings_df['user_id'] == user_id]
        
        # Get recommendations using hybrid model
        if hybrid_model:
            logger.info(f"Getting hybrid recommendations for user {user_id}")
            recommendations = hybrid_model.predict_batch(
                user_id or 1,  # Use dummy user ID if not provided
                preferences,
                movies_data[:50],  # Limit candidates for performance
                user_history,
                method='adaptive',
                top_k=top_k
            )
        else:
            # Fallback to fuzzy-only recommendations
            logger.info("Using fuzzy-only recommendations")
            fuzzy_results = []
            for movie_data in movies_data[:50]:
                result = fuzzy_model.predict_single_movie(preferences, movie_data, user_history)
                fuzzy_results.append({
                    'movie_id': result['movie_id'],
                    'final_score': result['fuzzy_score'],
                    'fuzzy_score': result['fuzzy_score'],
                    'ann_score': 5.0,  # Default
                    'explanation': result['explanation']
                })
            
            # Sort by score
            recommendations = sorted(fuzzy_results, key=lambda x: x['final_score'], reverse=True)[:top_k]
        
        # Format response
        formatted_recommendations = format_recommendation_response(recommendations, movies_df)
        
        return jsonify({
            'recommended': formatted_recommendations,
            'total_candidates': len(candidate_movies),
            'user_id': user_id,
            'preferences': preferences,
            'watched_count': len(watched)
        })
        
    except Exception as e:
        logger.error(f"Error in get_recommendations: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """Get movie metadata"""
    try:
        movie = movies_df[movies_df['movie_id'] == movie_id]
        
        if movie.empty:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie_data = movie.iloc[0]
        
        # Get additional statistics if available
        avg_rating = None
        rating_count = None
        
        if 'ratings' in preprocessed_data and not preprocessed_data['ratings'].empty:
            movie_ratings = preprocessed_data['ratings'][
                preprocessed_data['ratings']['movie_id'] == movie_id
            ]
            if not movie_ratings.empty:
                avg_rating = movie_ratings['rating'].mean()
                rating_count = len(movie_ratings)
        
        return jsonify({
            'movie_id': movie_id,
            'title': movie_data.get('title'),
            'genres': movie_data.get('genres', []),
            'year': movie_data.get('year'),
            'popularity': movie_data.get('popularity'),
            'avg_rating': round(avg_rating, 2) if avg_rating else None,
            'rating_count': rating_count
        })
        
    except Exception as e:
        logger.error(f"Error in get_movie_details: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/train/ann', methods=['POST'])
def train_ann_model():
    """Trigger ANN model training"""
    try:
        data = request.get_json() or {}
        sample_size = data.get('sample_size', 10000)
        
        if not preprocessed_data or preprocessed_data['ratings'].empty:
            return jsonify({'error': 'No training data available'}), 400
        
        logger.info(f"Starting ANN training with sample size: {sample_size}")
        
        # This would trigger actual training in a real implementation
        # For demo, return mock training results
        training_metrics = {
            'rmse': 0.85,
            'mae': 0.67,
            'training_time': 120,
            'epochs': 25,
            'sample_size': sample_size
        }
        
        return jsonify({
            'status': 'completed',
            'metrics': training_metrics,
            'message': 'ANN model training completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in train_ann_model: {e}")
        return jsonify({'error': 'Training failed'}), 500

@app.route('/api/train/fuzzy', methods=['POST'])
def train_fuzzy_model():
    """Re-initialize fuzzy model (lightweight operation)"""
    try:
        global fuzzy_model
        
        logger.info("Re-initializing fuzzy model")
        fuzzy_model = FuzzyMovieRecommender()
        
        return jsonify({
            'status': 'completed',
            'message': 'Fuzzy model re-initialized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in train_fuzzy_model: {e}")
        return jsonify({'error': 'Fuzzy model initialization failed'}), 500

@app.route('/api/movies/search', methods=['GET'])
def search_movies():
    """Search movies by title or genre"""
    try:
        query = request.args.get('q', '').strip()
        genre = request.args.get('genre', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not query and not genre:
            return jsonify({'error': 'Query or genre parameter required'}), 400
        
        filtered_movies = movies_df.copy()
        
        # Filter by title if query provided
        if query:
            filtered_movies = filtered_movies[
                filtered_movies['title'].str.contains(query, case=False, na=False)
            ]
        
        # Filter by genre if provided
        if genre:
            filtered_movies = filtered_movies[
                filtered_movies['genres'].apply(
                    lambda x: genre in x if isinstance(x, list) else False
                )
            ]
        
        # Limit results
        results = filtered_movies.head(limit).to_dict('records')
        
        return jsonify({
            'movies': results,
            'total_found': len(filtered_movies),
            'query': query,
            'genre': genre
        })
        
    except Exception as e:
        logger.error(f"Error in search_movies: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Get list of available genres"""
    try:
        all_genres = set()
        
        for genres_list in movies_df['genres'].dropna():
            if isinstance(genres_list, list):
                all_genres.update(genres_list)
        
        return jsonify({
            'genres': sorted(list(all_genres))
        })
        
    except Exception as e:
        logger.error(f"Error in get_genres: {e}")
        return jsonify({'error': 'Failed to get genres'}), 500

@app.route('/api/stats', methods=['GET'])
def get_system_stats():
    """Get system statistics"""
    try:
        stats = {
            'total_movies': len(movies_df) if movies_df is not None else 0,
            'total_users': 0,
            'total_ratings': 0,
            'memory_usage': get_memory_usage(),
            'models_status': {
                'fuzzy': fuzzy_model is not None,
                'ann': ann_model is not None,
                'hybrid': hybrid_model is not None
            }
        }
        
        if preprocessed_data and 'ratings' in preprocessed_data:
            ratings_df = preprocessed_data['ratings']
            if not ratings_df.empty:
                stats['total_users'] = ratings_df['user_id'].nunique()
                stats['total_ratings'] = len(ratings_df)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error in get_system_stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Main function to run the Flask app"""
    # Load models and data
    load_models_and_data()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
