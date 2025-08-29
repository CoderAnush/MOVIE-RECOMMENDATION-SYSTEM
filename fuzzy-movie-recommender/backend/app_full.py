"""
CineAI - Full Production Flask App with MovieLens 10M Dataset
Enhanced version with real TensorFlow models and professional features
"""

import os
import sys
import logging
import traceback
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.load_movielens import load_movielens_10m, download_movielens_10m
from data.preprocessing import preprocess_ratings, create_user_movie_matrix
from models.fuzzy_model import FuzzyMovieRecommender
from models.ann_model import ANNCollaborativeFilteringModel
from models.hybrid import HybridRecommender
from utils import setup_logging, log_performance

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask application with enhanced configuration"""
    app = Flask(__name__)
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:8080'])
    
    # Enhanced configuration
    app.config.update(
        JSON_SORT_KEYS=False,
        JSONIFY_PRETTYPRINT_REGULAR=True,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max request size
    )
    
    return app

app = create_app()

# Global variables for models and data
movies_df = None
ratings_df = None
fuzzy_model = None
ann_model = None
hybrid_model = None
user_movie_matrix = None

def initialize_system():
    """Initialize the full recommendation system"""
    global movies_df, ratings_df, fuzzy_model, ann_model, hybrid_model, user_movie_matrix
    
    logger.info("🚀 Initializing CineAI Full Production System...")
    
    try:
        # Step 1: Load MovieLens 10M dataset
        logger.info("📊 Loading MovieLens 10M dataset...")
        
        # Check if data exists, if not download it
        data_dir = os.path.join(os.path.dirname(__file__), 'data', 'ml-10M100K')
        if not os.path.exists(data_dir):
            logger.info("📥 Downloading MovieLens 10M dataset...")
            download_movielens_10m()
        
        # Load the dataset
        movies_df, ratings_df = load_movielens_10m()
        logger.info(f"✅ Loaded {len(movies_df):,} movies and {len(ratings_df):,} ratings")
        
        # Step 2: Preprocess data
        logger.info("🔄 Preprocessing data...")
        ratings_df = preprocess_ratings(ratings_df)
        user_movie_matrix = create_user_movie_matrix(ratings_df)
        logger.info(f"✅ Created user-movie matrix: {user_movie_matrix.shape}")
        
        # Step 3: Initialize Fuzzy Logic Model
        logger.info("🧠 Initializing Fuzzy Logic Recommender...")
        fuzzy_model = FuzzyMovieRecommender()
        logger.info("✅ Fuzzy Logic Recommender initialized")
        
        # Step 4: Initialize ANN Model
        logger.info("🤖 Initializing ANN Collaborative Filtering Model...")
        n_users = ratings_df['user_id'].nunique()
        n_movies = ratings_df['movie_id'].nunique()
        
        ann_model = ANNCollaborativeFilteringModel(
            n_users=n_users,
            n_movies=n_movies,
            embedding_dim=64,
            hidden_dims=[128, 64, 32],
            dropout_rate=0.3
        )
        
        # Check if pre-trained model exists
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'saved_models', 'ann_model.h5')
        if os.path.exists(model_path):
            logger.info("📂 Loading pre-trained ANN model...")
            ann_model.load_model(model_path)
            logger.info("✅ Pre-trained ANN model loaded")
        else:
            logger.info("🎯 Training ANN model on MovieLens data...")
            # Sample data for faster training in demo
            sample_ratings = ratings_df.sample(min(1000000, len(ratings_df)), random_state=42)
            history = ann_model.train(sample_ratings, epochs=10, batch_size=1024, validation_split=0.2)
            
            # Save the trained model
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            ann_model.save_model(model_path)
            logger.info("✅ ANN model trained and saved")
        
        # Step 5: Initialize Hybrid Model
        logger.info("🎯 Initializing Hybrid Recommender...")
        hybrid_model = HybridRecommender(fuzzy_model, ann_model)
        logger.info("✅ Hybrid Recommender initialized")
        
        logger.info("🎉 CineAI Full Production System initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing system: {e}")
        traceback.print_exc()
        return False

# Initialize system on startup
system_initialized = initialize_system()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    return jsonify({
        'status': 'healthy' if system_initialized else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0-production',
        'system': 'CineAI Full Production',
        'components': {
            'fuzzy_model': fuzzy_model is not None,
            'ann_model': ann_model is not None,
            'hybrid_model': hybrid_model is not None,
            'dataset': movies_df is not None and ratings_df is not None
        },
        'dataset_stats': {
            'movies': len(movies_df) if movies_df is not None else 0,
            'ratings': len(ratings_df) if ratings_df is not None else 0,
            'users': ratings_df['user_id'].nunique() if ratings_df is not None else 0
        } if system_initialized else None
    })

@app.route('/api/user/preferences', methods=['POST'])
@log_performance
def get_user_recommendations():
    """Get personalized movie recommendations using full system"""
    if not system_initialized:
        return jsonify({'error': 'System not initialized. Please check server logs.'}), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract request parameters
        user_preferences = data.get('user_preferences', {})
        watched_movies = data.get('watched_movies', [])
        top_k = min(int(data.get('top_k', 10)), 50)  # Cap at 50
        
        if not user_preferences:
            return jsonify({'error': 'user_preferences is required'}), 400
        
        logger.info(f"🎯 Getting recommendations for preferences: {user_preferences}")
        
        # Create mock user history from watched movies
        user_history = None
        excluded_movie_ids = set()
        
        if watched_movies:
            # Find movies in dataset that match watched titles
            watched_matches = []
            for watched_title in watched_movies:
                matches = movies_df[movies_df['title'].str.contains(
                    watched_title, case=False, na=False, regex=False
                )]
                if not matches.empty:
                    # Take the most popular match
                    best_match = matches.loc[matches['popularity'].idxmax()]
                    watched_matches.append(best_match)
                    excluded_movie_ids.add(best_match['movie_id'])
            
            if watched_matches:
                user_history = pd.DataFrame(watched_matches)
                user_history['rating'] = np.random.uniform(3.5, 5.0, len(watched_matches))
        
        # Get candidate movies (exclude watched movies)
        candidate_movies = movies_df[~movies_df['movie_id'].isin(excluded_movie_ids)]
        
        # Sample movies for faster processing (top 1000 by popularity)
        if len(candidate_movies) > 1000:
            candidate_movies = candidate_movies.nlargest(1000, 'popularity')
        
        movies_data = candidate_movies.to_dict('records')
        
        # Get recommendations using hybrid model
        start_time = datetime.now()
        
        recommendations = hybrid_model.predict_batch(
            user_id=1,  # Mock user ID
            user_preferences=user_preferences,
            movies_data=movies_data,
            user_history=user_history,
            top_k=top_k,
            method='adaptive'
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Enhance recommendations with additional movie data
        enhanced_recommendations = []
        for rec in recommendations:
            movie_data = movies_df[movies_df['movie_id'] == rec['movie_id']]
            if not movie_data.empty:
                movie_info = movie_data.iloc[0]
                rec.update({
                    'year': int(movie_info.get('year', 0)) if pd.notna(movie_info.get('year')) else None,
                    'popularity': float(movie_info.get('popularity', 0)),
                    'avg_rating': float(movie_info.get('avg_rating', 0)) if pd.notna(movie_info.get('avg_rating')) else None,
                    'rating_count': int(movie_info.get('rating_count', 0)) if pd.notna(movie_info.get('rating_count')) else None
                })
            enhanced_recommendations.append(rec)
        
        logger.info(f"✅ Generated {len(enhanced_recommendations)} recommendations in {processing_time:.2f}s")
        
        return jsonify({
            'recommendations': enhanced_recommendations,
            'total_movies_considered': len(movies_data),
            'user_preferences': user_preferences,
            'watched_movies': watched_movies,
            'excluded_count': len(excluded_movie_ids),
            'processing_time': processing_time,
            'model_info': {
                'fuzzy_weight': hybrid_model.fuzzy_weight,
                'ann_weight': hybrid_model.ann_weight,
                'combination_method': 'adaptive'
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_user_recommendations: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """Get detailed information for a specific movie"""
    if not system_initialized:
        return jsonify({'error': 'System not initialized'}), 503
    
    try:
        movie = movies_df[movies_df['movie_id'] == movie_id]
        
        if movie.empty:
            return jsonify({'error': 'Movie not found'}), 404
        
        movie_data = movie.iloc[0].to_dict()
        
        # Convert numpy types to Python types for JSON serialization
        for key, value in movie_data.items():
            if pd.isna(value):
                movie_data[key] = None
            elif isinstance(value, (np.integer, np.int64)):
                movie_data[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                movie_data[key] = float(value)
        
        # Add additional statistics if available
        movie_ratings = ratings_df[ratings_df['movie_id'] == movie_id]
        if not movie_ratings.empty:
            movie_data.update({
                'rating_stats': {
                    'mean': float(movie_ratings['rating'].mean()),
                    'std': float(movie_ratings['rating'].std()),
                    'count': int(len(movie_ratings)),
                    'distribution': movie_ratings['rating'].value_counts().sort_index().to_dict()
                }
            })
        
        return jsonify(movie_data)
        
    except Exception as e:
        logger.error(f"❌ Error in get_movie_details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/train/ann', methods=['POST'])
def train_ann_model():
    """Trigger ANN model training with real data"""
    if not system_initialized:
        return jsonify({'error': 'System not initialized'}), 503
    
    try:
        logger.info("🎯 Starting ANN model training...")
        
        # Get training parameters from request
        data = request.get_json() or {}
        epochs = min(int(data.get('epochs', 20)), 100)  # Cap at 100
        batch_size = int(data.get('batch_size', 1024))
        sample_size = min(int(data.get('sample_size', 1000000)), len(ratings_df))
        
        # Sample data for training
        sample_ratings = ratings_df.sample(sample_size, random_state=42)
        
        # Train the model
        start_time = datetime.now()
        history = ann_model.train(
            sample_ratings, 
            epochs=epochs, 
            batch_size=batch_size, 
            validation_split=0.2
        )
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Save the trained model
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'saved_models', 'ann_model.h5')
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        ann_model.save_model(model_path)
        
        logger.info(f"✅ ANN model training completed in {training_time:.2f}s")
        
        return jsonify({
            'status': 'success',
            'message': f'ANN model training completed successfully',
            'training_info': {
                'epochs': epochs,
                'batch_size': batch_size,
                'sample_size': sample_size,
                'training_time': training_time
            },
            'training_history': {
                'loss': history.history.get('loss', []),
                'val_loss': history.history.get('val_loss', []),
                'mae': history.history.get('mae', []),
                'val_mae': history.history.get('val_mae', [])
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in train_ann_model: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_movies():
    """Search for movies with enhanced filtering"""
    if not system_initialized:
        return jsonify({'error': 'System not initialized'}), 503
    
    try:
        query = request.args.get('query', '').lower().strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        genre_filter = request.args.get('genre', '').strip()
        min_year = request.args.get('min_year', type=int)
        max_year = request.args.get('max_year', type=int)
        min_rating = request.args.get('min_rating', type=float)
        
        if not query and not genre_filter:
            return jsonify({'movies': []})
        
        # Start with all movies
        filtered_movies = movies_df.copy()
        
        # Apply text search
        if query:
            filtered_movies = filtered_movies[
                filtered_movies['title'].str.contains(query, case=False, na=False)
            ]
        
        # Apply genre filter
        if genre_filter:
            filtered_movies = filtered_movies[
                filtered_movies['genres'].apply(
                    lambda x: genre_filter.lower() in [g.lower() for g in x] if isinstance(x, list) else False
                )
            ]
        
        # Apply year filters
        if min_year:
            filtered_movies = filtered_movies[filtered_movies['year'] >= min_year]
        if max_year:
            filtered_movies = filtered_movies[filtered_movies['year'] <= max_year]
        
        # Apply rating filter
        if min_rating:
            filtered_movies = filtered_movies[filtered_movies['avg_rating'] >= min_rating]
        
        # Sort by popularity and limit results
        results = filtered_movies.nlargest(limit, 'popularity')
        
        # Convert to JSON-serializable format
        movies_list = []
        for _, movie in results.iterrows():
            movie_dict = movie.to_dict()
            # Handle NaN values and numpy types
            for key, value in movie_dict.items():
                if pd.isna(value):
                    movie_dict[key] = None
                elif isinstance(value, (np.integer, np.int64)):
                    movie_dict[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    movie_dict[key] = float(value)
            movies_list.append(movie_dict)
        
        return jsonify({
            'movies': movies_list,
            'total_found': len(filtered_movies),
            'returned': len(movies_list),
            'query': query,
            'filters': {
                'genre': genre_filter,
                'min_year': min_year,
                'max_year': max_year,
                'min_rating': min_rating
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in search_movies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Get list of all available genres"""
    if not system_initialized:
        return jsonify({'error': 'System not initialized'}), 503
    
    try:
        all_genres = set()
        for genres_list in movies_df['genres'].dropna():
            if isinstance(genres_list, list):
                all_genres.update(genres_list)
        
        return jsonify({
            'genres': sorted(list(all_genres)),
            'count': len(all_genres)
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_genres: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get comprehensive dataset statistics"""
    if not system_initialized:
        return jsonify({'error': 'System not initialized'}), 503
    
    try:
        stats = {
            'dataset': 'MovieLens 10M',
            'total_movies': int(len(movies_df)),
            'total_ratings': int(len(ratings_df)),
            'total_users': int(ratings_df['user_id'].nunique()),
            'avg_rating': float(ratings_df['rating'].mean()),
            'rating_distribution': ratings_df['rating'].value_counts().sort_index().to_dict(),
            'year_range': {
                'min': int(movies_df['year'].min()) if pd.notna(movies_df['year'].min()) else None,
                'max': int(movies_df['year'].max()) if pd.notna(movies_df['year'].max()) else None
            },
            'top_genres': movies_df['genres'].explode().value_counts().head(10).to_dict(),
            'system_info': {
                'version': '2.0.0-production',
                'models_loaded': {
                    'fuzzy': fuzzy_model is not None,
                    'ann': ann_model is not None,
                    'hybrid': hybrid_model is not None
                }
            }
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Error in get_stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    if system_initialized:
        logger.info(f"🎬 CineAI Full Production System starting on port {port}")
        logger.info(f"📊 Dataset: {len(movies_df):,} movies, {len(ratings_df):,} ratings")
        logger.info(f"🧠 Models: Fuzzy Logic + ANN + Hybrid")
        logger.info(f"🌐 Frontend: Open frontend/index_pro.html")
    else:
        logger.error("❌ System failed to initialize. Check logs for details.")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
