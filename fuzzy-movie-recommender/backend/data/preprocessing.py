"""
Data Preprocessing Module for MovieLens Dataset

This module handles encoding, normalization, and creation of user-item matrices
for the movie recommendation system.
"""

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MovieLensPreprocessor:
    """Preprocesses MovieLens data for recommendation models"""
    
    def __init__(self):
        """Initialize preprocessor"""
        self.genre_encoder = MultiLabelBinarizer()
        self.user_encoder = {}
        self.movie_encoder = {}
        self.scaler = StandardScaler()
        self.genres = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime',
                      'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
                      'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
    
    def compute_movie_popularity(self, ratings_df, movies_df):
        """
        Compute movie popularity score (0-100) based on ratings count and average rating
        
        Args:
            ratings_df (pd.DataFrame): Ratings dataframe
            movies_df (pd.DataFrame): Movies dataframe
            
        Returns:
            pd.Series: Popularity scores for each movie
        """
        # Calculate rating statistics per movie
        movie_stats = ratings_df.groupby('movie_id').agg({
            'rating': ['count', 'mean']
        }).round(2)
        
        movie_stats.columns = ['rating_count', 'avg_rating']
        movie_stats = movie_stats.reset_index()
        
        # Normalize rating count (log scale to handle skewness)
        movie_stats['log_count'] = np.log1p(movie_stats['rating_count'])
        count_min, count_max = movie_stats['log_count'].min(), movie_stats['log_count'].max()
        movie_stats['norm_count'] = (movie_stats['log_count'] - count_min) / (count_max - count_min)
        
        # Normalize average rating (scale 1-5 to 0-1)
        movie_stats['norm_rating'] = (movie_stats['avg_rating'] - 1) / 4
        
        # Compute popularity as weighted combination (60% count, 40% rating)
        movie_stats['popularity'] = (0.6 * movie_stats['norm_count'] + 
                                   0.4 * movie_stats['norm_rating']) * 100
        
        # Ensure popularity is between 0-100
        movie_stats['popularity'] = movie_stats['popularity'].clip(0, 100)
        
        # Merge with movies to get all movies (fill missing with low popularity)
        popularity_series = movies_df[['movie_id']].merge(
            movie_stats[['movie_id', 'popularity']], 
            on='movie_id', 
            how='left'
        )['popularity'].fillna(10.0)  # Default low popularity for unrated movies
        
        return popularity_series
    
    def encode_genres(self, movies_df):
        """
        Create multi-hot encoding for movie genres
        
        Args:
            movies_df (pd.DataFrame): Movies dataframe with 'genres' column
            
        Returns:
            np.ndarray: Multi-hot encoded genres matrix
        """
        # Handle missing genres
        genres_list = movies_df['genres'].fillna('').apply(
            lambda x: x if isinstance(x, list) else []
        )
        
        # Fit and transform genres
        genre_matrix = self.genre_encoder.fit_transform(genres_list)
        
        logger.info(f"Encoded {len(self.genre_encoder.classes_)} unique genres")
        return genre_matrix
    
    def compute_genre_match_score(self, user_preferences, movie_genres_encoded):
        """
        Compute genre match score between user preferences and movie genres
        
        Args:
            user_preferences (dict): User genre preferences {'Action': 'High', ...}
            movie_genres_encoded (np.ndarray): Multi-hot encoded movie genres
            
        Returns:
            np.ndarray: Genre match scores (0-1) for each movie
        """
        # Map preference levels to numeric scores
        pref_mapping = {
            'Very Low': 0.0,
            'Low': 0.25,
            'Medium': 0.5,
            'High': 0.75,
            'Very High': 1.0
        }
        
        # Create user preference vector
        user_pref_vector = np.zeros(len(self.genre_encoder.classes_))
        
        for i, genre in enumerate(self.genre_encoder.classes_):
            if genre in user_preferences:
                user_pref_vector[i] = pref_mapping.get(user_preferences[genre], 0.0)
        
        # Compute cosine similarity between user preferences and movie genres
        # Normalize vectors
        user_norm = np.linalg.norm(user_pref_vector)
        if user_norm == 0:
            return np.zeros(movie_genres_encoded.shape[0])
        
        movie_norms = np.linalg.norm(movie_genres_encoded, axis=1)
        movie_norms[movie_norms == 0] = 1  # Avoid division by zero
        
        # Compute similarity
        similarities = np.dot(movie_genres_encoded, user_pref_vector) / (movie_norms * user_norm)
        
        return np.clip(similarities, 0, 1)
    
    def create_user_item_matrix(self, ratings_df, movies_df):
        """
        Create sparse user-item rating matrix
        
        Args:
            ratings_df (pd.DataFrame): Ratings dataframe
            movies_df (pd.DataFrame): Movies dataframe
            
        Returns:
            tuple: (sparse_matrix, user_to_idx, movie_to_idx, idx_to_user, idx_to_movie)
        """
        # Create user and movie encoders
        unique_users = sorted(ratings_df['user_id'].unique())
        unique_movies = sorted(movies_df['movie_id'].unique())
        
        self.user_encoder = {user: idx for idx, user in enumerate(unique_users)}
        self.movie_encoder = {movie: idx for idx, movie in enumerate(unique_movies)}
        
        # Reverse mappings
        idx_to_user = {idx: user for user, idx in self.user_encoder.items()}
        idx_to_movie = {idx: movie for movie, idx in self.movie_encoder.items()}
        
        # Filter ratings to only include movies in our movie set
        valid_ratings = ratings_df[ratings_df['movie_id'].isin(unique_movies)].copy()
        
        # Map to indices
        valid_ratings['user_idx'] = valid_ratings['user_id'].map(self.user_encoder)
        valid_ratings['movie_idx'] = valid_ratings['movie_id'].map(self.movie_encoder)
        
        # Create sparse matrix
        n_users = len(unique_users)
        n_movies = len(unique_movies)
        
        user_item_matrix = csr_matrix(
            (valid_ratings['rating'], 
             (valid_ratings['user_idx'], valid_ratings['movie_idx'])),
            shape=(n_users, n_movies)
        )
        
        logger.info(f"Created user-item matrix: {n_users} users x {n_movies} movies")
        logger.info(f"Matrix density: {user_item_matrix.nnz / (n_users * n_movies):.4f}")
        
        return user_item_matrix, self.user_encoder, self.movie_encoder, idx_to_user, idx_to_movie
    
    def get_user_watched_movies(self, user_id, ratings_df):
        """
        Get list of movies watched by a user
        
        Args:
            user_id (int): User ID
            ratings_df (pd.DataFrame): Ratings dataframe
            
        Returns:
            list: List of movie IDs watched by user
        """
        user_ratings = ratings_df[ratings_df['user_id'] == user_id]
        return user_ratings['movie_id'].tolist()
    
    def get_user_rating_history(self, user_id, ratings_df, movies_df):
        """
        Get user's rating history with movie details
        
        Args:
            user_id (int): User ID
            ratings_df (pd.DataFrame): Ratings dataframe
            movies_df (pd.DataFrame): Movies dataframe
            
        Returns:
            pd.DataFrame: User's rating history with movie details
        """
        user_ratings = ratings_df[ratings_df['user_id'] == user_id]
        
        # Merge with movie details
        history = user_ratings.merge(movies_df, on='movie_id', how='left')
        
        # Add liked/disliked labels (rating >= 4 is liked)
        history['liked'] = history['rating'] >= 4
        history['disliked'] = history['rating'] <= 2
        
        return history.sort_values('timestamp', ascending=False)
    
    def normalize_ratings(self, ratings_df, scale_to=(0, 10)):
        """
        Normalize ratings to specified scale
        
        Args:
            ratings_df (pd.DataFrame): Ratings dataframe
            scale_to (tuple): Target scale (min, max)
            
        Returns:
            pd.DataFrame: Dataframe with normalized ratings
        """
        ratings_copy = ratings_df.copy()
        
        # Original MovieLens scale is 1-5, normalize to target scale
        old_min, old_max = 1, 5
        new_min, new_max = scale_to
        
        ratings_copy['rating_normalized'] = (
            (ratings_copy['rating'] - old_min) / (old_max - old_min) * 
            (new_max - new_min) + new_min
        )
        
        return ratings_copy
    
    def preprocess_full_dataset(self, movies_df, ratings_df, users_df=None):
        """
        Complete preprocessing pipeline
        
        Args:
            movies_df (pd.DataFrame): Movies dataframe
            ratings_df (pd.DataFrame): Ratings dataframe
            users_df (pd.DataFrame): Users dataframe (optional)
            
        Returns:
            dict: Preprocessed data dictionary
        """
        logger.info("Starting full dataset preprocessing...")
        
        # 1. Compute movie popularity
        logger.info("Computing movie popularity scores...")
        movies_df['popularity'] = self.compute_movie_popularity(ratings_df, movies_df)
        
        # 2. Encode genres
        logger.info("Encoding movie genres...")
        genre_matrix = self.encode_genres(movies_df)
        movies_df['genre_encoded'] = list(genre_matrix)
        
        # 3. Create user-item matrix
        logger.info("Creating user-item matrix...")
        user_item_matrix, user_to_idx, movie_to_idx, idx_to_user, idx_to_movie = \
            self.create_user_item_matrix(ratings_df, movies_df)
        
        # 4. Normalize ratings
        logger.info("Normalizing ratings...")
        ratings_normalized = self.normalize_ratings(ratings_df, scale_to=(0, 10))
        
        # 5. Prepare final data structure
        preprocessed_data = {
            'movies': movies_df,
            'ratings': ratings_df,
            'ratings_normalized': ratings_normalized,
            'users': users_df,
            'user_item_matrix': user_item_matrix,
            'user_to_idx': user_to_idx,
            'movie_to_idx': movie_to_idx,
            'idx_to_user': idx_to_user,
            'idx_to_movie': idx_to_movie,
            'genre_encoder': self.genre_encoder,
            'genre_matrix': genre_matrix,
            'preprocessor': self
        }
        
        logger.info("Preprocessing completed successfully!")
        logger.info(f"Final dataset: {len(movies_df)} movies, {len(ratings_df)} ratings")
        
        return preprocessed_data
    
    def save_preprocessed(self, data, filepath):
        """
        Save preprocessed data to file
        
        Args:
            data (dict): Preprocessed data dictionary
            filepath (str): Output file path
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Preprocessed data saved to {filepath}")
    
    def load_preprocessed(self, filepath):
        """
        Load preprocessed data from file
        
        Args:
            filepath (str): Input file path
            
        Returns:
            dict: Preprocessed data dictionary
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        # Restore preprocessor state
        if 'preprocessor' in data:
            preprocessor = data['preprocessor']
            self.genre_encoder = preprocessor.genre_encoder
            self.user_encoder = preprocessor.user_encoder
            self.movie_encoder = preprocessor.movie_encoder
        
        logger.info(f"Preprocessed data loaded from {filepath}")
        return data


def main():
    """Example usage of preprocessor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess MovieLens dataset')
    parser.add_argument('--input', type=str, required=True,
                       help='Input pickle file with raw data')
    parser.add_argument('--output', type=str, required=True,
                       help='Output pickle file for preprocessed data')
    
    args = parser.parse_args()
    
    # Load raw data
    with open(args.input, 'rb') as f:
        raw_data = pickle.load(f)
    
    # Initialize preprocessor
    preprocessor = MovieLensPreprocessor()
    
    # Preprocess data
    preprocessed_data = preprocessor.preprocess_full_dataset(
        raw_data['movies'],
        raw_data['ratings'],
        raw_data.get('users')
    )
    
    # Save preprocessed data
    preprocessor.save_preprocessed(preprocessed_data, args.output)


# Convenience functions for direct import
def preprocess_ratings(ratings_df):
    """
    Basic preprocessing of ratings data
    
    Args:
        ratings_df (pd.DataFrame): Raw ratings dataframe
        
    Returns:
        pd.DataFrame: Preprocessed ratings dataframe
    """
    ratings_processed = ratings_df.copy()
    
    # Ensure proper data types
    ratings_processed['user_id'] = ratings_processed['user_id'].astype(int)
    ratings_processed['movie_id'] = ratings_processed['movie_id'].astype(int)
    ratings_processed['rating'] = ratings_processed['rating'].astype(float)
    
    # Remove any invalid ratings
    ratings_processed = ratings_processed[
        (ratings_processed['rating'] >= 0.5) & 
        (ratings_processed['rating'] <= 5.0)
    ]
    
    # Sort by timestamp if available
    if 'timestamp' in ratings_processed.columns:
        ratings_processed = ratings_processed.sort_values('timestamp')
    
    logger.info(f"Preprocessed {len(ratings_processed):,} ratings")
    return ratings_processed

def create_user_movie_matrix(ratings_df):
    """
    Create user-movie rating matrix
    
    Args:
        ratings_df (pd.DataFrame): Ratings dataframe
        
    Returns:
        csr_matrix: Sparse user-movie matrix
    """
    # Get unique users and movies
    users = sorted(ratings_df['user_id'].unique())
    movies = sorted(ratings_df['movie_id'].unique())
    
    # Create mappings
    user_to_idx = {user: idx for idx, user in enumerate(users)}
    movie_to_idx = {movie: idx for idx, movie in enumerate(movies)}
    
    # Map ratings to indices
    user_indices = ratings_df['user_id'].map(user_to_idx)
    movie_indices = ratings_df['movie_id'].map(movie_to_idx)
    
    # Create sparse matrix
    matrix = csr_matrix(
        (ratings_df['rating'], (user_indices, movie_indices)),
        shape=(len(users), len(movies))
    )
    
    logger.info(f"Created user-movie matrix: {len(users)} users x {len(movies)} movies")
    logger.info(f"Matrix density: {matrix.nnz / (len(users) * len(movies)):.4f}")
    
    return matrix

if __name__ == '__main__':
    main()
