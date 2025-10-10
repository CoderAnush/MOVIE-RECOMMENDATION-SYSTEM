"""
Integration Script: Fuzzy Recommendation System with Preprocessed MovieLens Data
==============================================================================

This script demonstrates how to use the fuzzy recommendation system with 
the preprocessed MovieLens 10M dataset.
"""

import pandas as pd
import numpy as np
from models.fuzzy_model import FuzzyMovieRecommender, recommend_with_fuzzy
import json
import os

class MovieRecommendationSystem:
    """Complete movie recommendation system using fuzzy logic."""
    
    def __init__(self, data_path="processed/"):
        """Initialize the system with preprocessed data."""
        self.data_path = data_path
        self.fuzzy_engine = FuzzyMovieRecommender()
        self.movies_df = None
        self.ratings_df = None
        self.user_stats_df = None
        self.dataset_info = None
        
        self._load_data()
    
    def _load_data(self):
        """Load all preprocessed data files."""
        try:
            # Load movies
            movies_path = os.path.join(self.data_path, "movies_enriched.parquet")
            if os.path.exists(movies_path):
                self.movies_df = pd.read_parquet(movies_path)
                print(f"✅ Loaded {len(self.movies_df)} movies")
            
            # Load ratings
            ratings_path = os.path.join(self.data_path, "ratings.parquet")
            if os.path.exists(ratings_path):
                self.ratings_df = pd.read_parquet(ratings_path)
                print(f"✅ Loaded {len(self.ratings_df)} ratings")
            
            # Load user stats
            user_stats_path = os.path.join(self.data_path, "user_stats.parquet")
            if os.path.exists(user_stats_path):
                self.user_stats_df = pd.read_parquet(user_stats_path)
                print(f"✅ Loaded {len(self.user_stats_df)} user profiles")
            
            # Load dataset summary
            summary_path = os.path.join(self.data_path, "dataset_summary.json")
            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    self.dataset_info = json.load(f)
                print(f"✅ Loaded dataset summary")
            
        except Exception as e:
            print(f"⚠️ Error loading data: {e}")
    
    def get_user_preferences_from_history(self, user_id, sample_size=50):
        """
        Extract user genre preferences from their rating history.
        
        Args:
            user_id: User ID to analyze
            sample_size: Number of recent ratings to consider
            
        Returns:
            Dict with genre preferences (0-10 scale)
        """
        if self.ratings_df is None or self.movies_df is None:
            return {genre: 5.0 for genre in self.fuzzy_engine.genres}
        
        # Get user's ratings
        user_ratings = self.ratings_df[
            self.ratings_df['user_id'] == user_id
        ].head(sample_size)
        
        if len(user_ratings) == 0:
            return {genre: 5.0 for genre in self.fuzzy_engine.genres}
        
        # Merge with movie genres
        user_movies = user_ratings.merge(
            self.movies_df, 
            on='movie_id', 
            how='left'
        )
        
        # Calculate preferences based on ratings
        preferences = {}
        genre_columns = [col for col in self.movies_df.columns if col.startswith('genre_')]
        
        for genre_col in genre_columns:
            genre_name = genre_col.replace('genre_', '')
            
            # Get ratings for movies with this genre
            genre_ratings = user_movies[user_movies[genre_col] == 1]['rating']
            
            if len(genre_ratings) > 0:
                # Convert average rating to 0-10 scale preference
                avg_rating = genre_ratings.mean()
                preference = min(10, max(0, (avg_rating - 0.5) * 2))  # Scale 0.5-5 to 0-10
                preferences[genre_name] = preference
            else:
                preferences[genre_name] = 5.0  # Neutral for unknown genres
        
        return preferences
    
    def get_movie_info(self, movie_id):
        """Get movie information including genres and popularity."""
        if self.movies_df is None:
            return None
        
        movie_row = self.movies_df[
            self.movies_df['movie_id'] == movie_id
        ].iloc[0]
        
        # Extract genres
        genre_columns = [col for col in self.movies_df.columns if col.startswith('genre_')]
        genres = []
        for genre_col in genre_columns:
            if movie_row[genre_col] == 1:
                genre_name = genre_col.replace('genre_', '').replace('_', ' ').title()
                genres.append(genre_name)
        
        # Calculate popularity (simplified - based on number of ratings)
        if self.ratings_df is not None:
            rating_count = len(self.ratings_df[
                self.ratings_df['movie_id'] == movie_id
            ])
            # Normalize to 0-100 scale (log scale for wide distribution)
            popularity = min(100, max(0, np.log10(rating_count + 1) * 25))
        else:
            popularity = 50  # Default
        
        return {
            'title': movie_row.get('title', 'Unknown'),
            'genres': genres,
            'popularity': popularity,
            'year': movie_row.get('year', 'Unknown')
        }
    
    def get_user_watch_history(self, user_id, movie_genres):
        """Get user's watch history sentiment for similar genres."""
        if self.ratings_df is None or self.movies_df is None:
            return {}
        
        # Get user's ratings
        user_ratings = self.ratings_df[
            self.ratings_df['user_id'] == user_id
        ]
        
        if len(user_ratings) == 0:
            return {}
        
        # Merge with movies to get genres
        user_movies = user_ratings.merge(
            self.movies_df, 
            on='movie_id', 
            how='left'
        )
        
        # Filter for similar genres
        genre_columns = [f"genre_{g.lower().replace(' ', '_')}" 
                        for g in movie_genres if f"genre_{g.lower().replace(' ', '_')}" in self.movies_df.columns]
        
        if genre_columns:
            # Movies with at least one matching genre
            similar_movies = user_movies[
                user_movies[genre_columns].sum(axis=1) > 0
            ]
        else:
            similar_movies = user_movies
        
        if len(similar_movies) == 0:
            return {}
        
        # Calculate sentiment
        total_count = len(similar_movies)
        liked_count = len(similar_movies[similar_movies['rating'] >= 4])
        disliked_count = len(similar_movies[similar_movies['rating'] <= 2])
        
        return {
            'watch_count': total_count,
            'liked_ratio': liked_count / total_count,
            'disliked_ratio': disliked_count / total_count
        }
    
    def recommend_for_user(self, user_id, movie_id, ann_score=None):
        """
        Get fuzzy recommendation for a specific user and movie.
        
        Args:
            user_id: Encoded user ID
            movie_id: Encoded movie ID
            ann_score: Optional ANN prediction score
            
        Returns:
            Recommendation result with score and explanation
        """
        # Get user preferences from history
        user_prefs = self.get_user_preferences_from_history(user_id)
        
        # Get movie information
        movie_info = self.get_movie_info(movie_id)
        if movie_info is None:
            return {'error': 'Movie not found'}
        
        # Get watch history
        watch_history = self.get_user_watch_history(user_id, movie_info['genres'])
        
        # Get fuzzy recommendation
        result = recommend_with_fuzzy(
            self.fuzzy_engine,
            user_prefs,
            movie_info,
            watch_history,
            ann_score
        )
        
        # Add movie details
        result['movie_title'] = movie_info['title']
        result['movie_year'] = movie_info['year']
        result['user_preferences'] = user_prefs
        result['watch_history'] = watch_history
        
        return result
    
    def get_sample_recommendations(self, num_samples=5):
        """Get sample recommendations for testing."""
        if self.ratings_df is None or self.movies_df is None:
            print("❌ Data not loaded")
            return
        
        print("\n🎬 SAMPLE FUZZY RECOMMENDATIONS")
        print("=" * 60)
        
        # Get random user-movie pairs
        sample_ratings = self.ratings_df.sample(n=num_samples, random_state=42)
        
        for i, (_, rating_row) in enumerate(sample_ratings.iterrows(), 1):
            user_id = rating_row['user_id']
            movie_id = rating_row['movie_id']
            actual_rating = rating_row['rating']
            
            # Get recommendation
            result = self.recommend_for_user(user_id, movie_id, ann_score=actual_rating*2)
            
            print(f"\n📋 Sample {i}: {result['movie_title']} ({result['movie_year']})")
            print(f"   Genres: {', '.join(result['movie_genres'])}")
            print(f"   Actual Rating: {actual_rating}/5")
            print(f"   Fuzzy Score: {result['fuzzy_score']}/10")
            if 'hybrid_score' in result:
                print(f"   Hybrid Score: {result['hybrid_score']}/10")
            print(f"   User Preferences (Top 3): {dict(sorted(result['user_preferences'].items(), key=lambda x: x[1], reverse=True)[:3])}")


def main():
    """Main function to demonstrate the integrated system."""
    print("🎯 FUZZY MOVIE RECOMMENDATION SYSTEM - INTEGRATION DEMO")
    print("=" * 70)
    
    # Initialize system
    system = MovieRecommendationSystem()
    
    # Show dataset info
    if system.dataset_info:
        print(f"\n📊 Dataset Information:")
        for key, value in system.dataset_info.items():
            print(f"   {key}: {value:,}" if isinstance(value, (int, float)) else f"   {key}: {value}")
    
    # Get sample recommendations
    system.get_sample_recommendations(5)
    
    print("\n" + "=" * 70)
    print("✅ INTEGRATION DEMO COMPLETED!")
    print("💡 The fuzzy system is successfully integrated with preprocessed data.")
    print("🔗 Ready for frontend integration and real-time recommendations.")
    print("=" * 70)


if __name__ == "__main__":
    main()