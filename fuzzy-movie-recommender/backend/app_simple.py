"""
Simple Flask App for Movie Recommendations
Uses existing MovieLens data with minimal dependencies
"""

import os
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables
movies_df = None
ratings_df = None

def load_data():
    """Load MovieLens data from .dat files"""
    global movies_df, ratings_df
    
    try:
        # Try multiple possible data locations
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'data'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'),
            'C:\\Users\\anush\\OneDrive\\Desktop\\MOVIE RECOMMENDATION\\data'
        ]
        
        data_dir = None
        for path in possible_paths:
            if os.path.exists(os.path.join(path, 'movies.dat')):
                data_dir = path
                break
        
        if not data_dir:
            raise FileNotFoundError("Could not find movies.dat in any expected location")
        
        # Load movies
        movies_file = os.path.join(data_dir, 'movies.dat')
        movies_df = pd.read_csv(
            movies_file,
            sep='::',
            names=['movie_id', 'title', 'genres'],
            engine='python',
            encoding='latin-1'
        )
        movies_df['genres'] = movies_df['genres'].str.split('|')
        movies_df['year'] = movies_df['title'].str.extract(r'\((\d{4})\)').astype(float)
        
        # Load ratings
        ratings_file = os.path.join(data_dir, 'ratings.dat')
        ratings_df = pd.read_csv(
            ratings_file,
            sep='::',
            names=['user_id', 'movie_id', 'rating', 'timestamp'],
            engine='python'
        )
        
        # Calculate movie stats
        movie_stats = ratings_df.groupby('movie_id').agg({
            'rating': ['mean', 'count']
        }).round(2)
        movie_stats.columns = ['avg_rating', 'rating_count']
        movie_stats = movie_stats.reset_index()
        
        # Merge with movies
        movies_df = movies_df.merge(movie_stats, on='movie_id', how='left')
        movies_df['avg_rating'] = movies_df['avg_rating'].fillna(0)
        movies_df['rating_count'] = movies_df['rating_count'].fillna(0)
        movies_df['popularity'] = movies_df['avg_rating'] * np.log1p(movies_df['rating_count'])
        
        logger.info(f"Loaded {len(movies_df)} movies and {len(ratings_df)} ratings")
        return True
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return False

# Load data on startup
data_loaded = load_data()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if data_loaded else 'error',
        'movies': len(movies_df) if movies_df is not None else 0,
        'ratings': len(ratings_df) if ratings_df is not None else 0
    })

@app.route('/api/user/preferences', methods=['POST'])
def get_recommendations():
    """Get movie recommendations"""
    if not data_loaded:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        data = request.get_json()
        user_preferences = data.get('user_preferences', {})
        top_k = min(int(data.get('top_k', 10)), 50)
        
        # Simple recommendation logic
        recommendations = []
        
        # Use all movies for recommendations
        candidate_movies = movies_df.copy()
        
        # Filter out watched movies if provided
        watched_movies = data.get('watched_movies', [])
        if watched_movies:
            for watched_title in watched_movies:
                matches = candidate_movies[candidate_movies['title'].str.contains(
                    watched_title, case=False, na=False, regex=False
                )]
                if not matches.empty:
                    candidate_movies = candidate_movies[~candidate_movies['movie_id'].isin(matches['movie_id'])]
        
        # Calculate genre-based scores for all movies
        scored_movies = []
        for _, movie in candidate_movies.iterrows():
            movie_genres = movie['genres'] if isinstance(movie['genres'], list) else []
            genre_score = 0
            genre_matches = 0
            
            for genre in movie_genres:
                for pref_genre, pref_value in user_preferences.items():
                    if genre.lower() == pref_genre.lower():
                        if isinstance(pref_value, (int, float)):
                            genre_score += pref_value
                        else:
                            genre_score += 5  # Default value
                        genre_matches += 1
            
            # Average genre score
            if genre_matches > 0:
                genre_score = genre_score / genre_matches
            else:
                # If no genre matches, use a neutral score
                genre_score = 3
            
            # Combine genre preference with movie quality (rating and popularity)
            quality_score = movie['avg_rating'] if movie['avg_rating'] > 0 else 2.5
            popularity_factor = min(np.log1p(movie['rating_count']) / 10, 1)  # Normalize popularity
            
            # Final score: 50% genre preference, 30% quality, 20% popularity
            final_score = (0.5 * genre_score + 0.3 * quality_score + 0.2 * popularity_factor * 5) * 2
            
            scored_movies.append({
                'movie': movie,
                'score': final_score,
                'genre_score': genre_score,
                'quality_score': quality_score
            })
        
        # Sort by score and take top_k
        scored_movies.sort(key=lambda x: x['score'], reverse=True)
        top_movies = scored_movies[:top_k]
        
        # Build recommendations from scored movies
        for item in top_movies:
            movie = item['movie']
            movie_genres = movie['genres'] if isinstance(movie['genres'], list) else []
            
            rec = {
                'movie_id': int(movie['movie_id']),
                'title': movie['title'],
                'genres': movie_genres,
                'year': int(movie['year']) if pd.notna(movie['year']) else None,
                'score': round(item['score'], 2),
                'fuzzy_score': round(item['genre_score'], 2),
                'ann_score': round(item['quality_score'], 2),
                'avg_rating': round(movie['avg_rating'], 2),
                'rating_count': int(movie['rating_count']),
                'explanation': f"Recommended based on your {', '.join(movie_genres[:2])} preferences with {movie['avg_rating']:.1f}★ rating"
            }
            recommendations.append(rec)
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'recommendations': recommendations,
            'total_movies_considered': len(top_movies),
            'user_preferences': user_preferences
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/movie/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    """Get movie details"""
    if not data_loaded:
        return jsonify({'error': 'Data not loaded'}), 500
    
    movie = movies_df[movies_df['movie_id'] == movie_id]
    if movie.empty:
        return jsonify({'error': 'Movie not found'}), 404
    
    movie_data = movie.iloc[0].to_dict()
    
    # Convert numpy types
    for key, value in movie_data.items():
        if pd.isna(value):
            movie_data[key] = None
        elif isinstance(value, (np.integer, np.int64)):
            movie_data[key] = int(value)
        elif isinstance(value, (np.floating, np.float64)):
            movie_data[key] = float(value)
    
    return jsonify(movie_data)

@app.route('/api/search', methods=['GET'])
def search_movies():
    """Search movies"""
    if not data_loaded:
        return jsonify({'error': 'Data not loaded'}), 500
    
    query = request.args.get('query', '').lower()
    limit = min(int(request.args.get('limit', 20)), 100)
    
    if not query:
        return jsonify({'movies': []})
    
    # Search in titles
    results = movies_df[movies_df['title'].str.contains(query, case=False, na=False)]
    results = results.nlargest(limit, 'popularity')
    
    movies_list = []
    for _, movie in results.iterrows():
        movie_dict = {
            'movie_id': int(movie['movie_id']),
            'title': movie['title'],
            'genres': movie['genres'],
            'year': int(movie['year']) if pd.notna(movie['year']) else None,
            'avg_rating': float(movie['avg_rating']),
            'rating_count': int(movie['rating_count'])
        }
        movies_list.append(movie_dict)
    
    return jsonify({'movies': movies_list})

@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Get all genres"""
    if not data_loaded:
        return jsonify({'error': 'Data not loaded'}), 500
    
    all_genres = set()
    for genres_list in movies_df['genres'].dropna():
        if isinstance(genres_list, list):
            all_genres.update(genres_list)
    
    return jsonify({'genres': sorted(list(all_genres))})

@app.route('/api/movies/browse', methods=['GET'])
def browse_movies():
    """Browse all movies with pagination and filtering"""
    if not data_loaded:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)  # Max 100 per page
        sort_by = request.args.get('sort_by', 'popularity')  # popularity, title, year, rating
        genre_filter = request.args.get('genre', '')
        year_min = request.args.get('year_min', type=int)
        year_max = request.args.get('year_max', type=int)
        rating_min = request.args.get('rating_min', type=float)
        
        # Start with all movies
        filtered_movies = movies_df.copy()
        
        # Apply filters
        if genre_filter:
            filtered_movies = filtered_movies[
                filtered_movies['genres'].apply(
                    lambda x: genre_filter.lower() in [g.lower() for g in x] if isinstance(x, list) else False
                )
            ]
        
        if year_min:
            filtered_movies = filtered_movies[filtered_movies['year'] >= year_min]
        if year_max:
            filtered_movies = filtered_movies[filtered_movies['year'] <= year_max]
        if rating_min:
            filtered_movies = filtered_movies[filtered_movies['avg_rating'] >= rating_min]
        
        # Sort movies
        if sort_by == 'title':
            filtered_movies = filtered_movies.sort_values('title')
        elif sort_by == 'year':
            filtered_movies = filtered_movies.sort_values('year', ascending=False, na_position='last')
        elif sort_by == 'rating':
            filtered_movies = filtered_movies.sort_values('avg_rating', ascending=False)
        else:  # popularity (default)
            filtered_movies = filtered_movies.sort_values('popularity', ascending=False)
        
        # Calculate pagination
        total_movies = len(filtered_movies)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get page of movies
        page_movies = filtered_movies.iloc[start_idx:end_idx]
        
        # Format movies for response
        movies_list = []
        for _, movie in page_movies.iterrows():
            movie_dict = {
                'movie_id': int(movie['movie_id']),
                'title': movie['title'],
                'genres': movie['genres'] if isinstance(movie['genres'], list) else [],
                'year': int(movie['year']) if pd.notna(movie['year']) else None,
                'avg_rating': round(float(movie['avg_rating']), 2),
                'rating_count': int(movie['rating_count']),
                'popularity': round(float(movie['popularity']), 2)
            }
            movies_list.append(movie_dict)
        
        return jsonify({
            'movies': movies_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_movies': total_movies,
                'total_pages': (total_movies + per_page - 1) // per_page,
                'has_next': end_idx < total_movies,
                'has_prev': page > 1
            },
            'filters': {
                'sort_by': sort_by,
                'genre': genre_filter,
                'year_min': year_min,
                'year_max': year_max,
                'rating_min': rating_min
            }
        })
        
    except Exception as e:
        logger.error(f"Error browsing movies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dataset stats"""
    if not data_loaded:
        return jsonify({'error': 'Data not loaded'}), 500
    
    return jsonify({
        'total_movies': len(movies_df),
        'total_ratings': len(ratings_df),
        'total_users': ratings_df['user_id'].nunique(),
        'avg_rating': float(ratings_df['rating'].mean()),
        'year_range': {
            'min': int(movies_df['year'].min()) if pd.notna(movies_df['year'].min()) else None,
            'max': int(movies_df['year'].max()) if pd.notna(movies_df['year'].max()) else None
        },
        'top_genres': movies_df['genres'].explode().value_counts().head(10).to_dict(),
        'system': 'Simple MovieLens System'
    })

if __name__ == '__main__':
    if data_loaded:
        logger.info("🎬 Simple MovieLens System starting on port 5000")
        logger.info(f"📊 {len(movies_df)} movies, {len(ratings_df)} ratings")
        logger.info("🌐 Open frontend/index_netflix.html in browser")
    else:
        logger.error("❌ Failed to load data")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
