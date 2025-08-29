"""
Local MovieLens Data Loader
Loads data directly from existing .dat files and converts to CSV if needed
"""

import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_local_movielens(data_dir='../data'):
    """
    Load MovieLens data from local .dat files
    
    Args:
        data_dir (str): Path to data directory containing .dat files
        
    Returns:
        tuple: (movies_df, ratings_df) DataFrames
    """
    data_path = Path(data_dir)
    
    logger.info(f"Loading MovieLens data from {data_path}")
    
    # Load movies.dat
    movies_file = data_path / 'movies.dat'
    if not movies_file.exists():
        raise FileNotFoundError(f"Movies file not found: {movies_file}")
    
    logger.info("Loading movies data...")
    movies_df = pd.read_csv(
        movies_file,
        sep='::',
        names=['movie_id', 'title', 'genres'],
        engine='python',
        encoding='latin-1'
    )
    
    # Process movies data
    movies_df['genres'] = movies_df['genres'].str.split('|')
    movies_df['year'] = movies_df['title'].str.extract(r'\((\d{4})\)').astype(float)
    movies_df['title_clean'] = movies_df['title'].str.replace(r'\s*\(\d{4}\)', '', regex=True)
    
    logger.info(f"Loaded {len(movies_df):,} movies")
    
    # Load ratings.dat
    ratings_file = data_path / 'ratings.dat'
    if not ratings_file.exists():
        raise FileNotFoundError(f"Ratings file not found: {ratings_file}")
    
    logger.info("Loading ratings data...")
    ratings_df = pd.read_csv(
        ratings_file,
        sep='::',
        names=['user_id', 'movie_id', 'rating', 'timestamp'],
        engine='python'
    )
    
    # Convert timestamp to datetime
    ratings_df['timestamp'] = pd.to_datetime(ratings_df['timestamp'], unit='s')
    
    logger.info(f"Loaded {len(ratings_df):,} ratings")
    
    # Calculate movie statistics
    logger.info("Calculating movie statistics...")
    rating_stats = ratings_df.groupby('movie_id').agg({
        'rating': ['mean', 'count', 'std']
    }).round(2)
    rating_stats.columns = ['avg_rating', 'rating_count', 'rating_std']
    rating_stats = rating_stats.reset_index()
    
    # Merge with movies
    movies_df = movies_df.merge(rating_stats, on='movie_id', how='left')
    movies_df['avg_rating'] = movies_df['avg_rating'].fillna(0)
    movies_df['rating_count'] = movies_df['rating_count'].fillna(0)
    movies_df['rating_std'] = movies_df['rating_std'].fillna(0)
    
    # Calculate popularity score (rating * log(count + 1))
    movies_df['popularity'] = (movies_df['avg_rating'] * np.log1p(movies_df['rating_count'])).fillna(0)
    
    logger.info("Data processing complete")
    logger.info(f"Final dataset: {len(movies_df):,} movies, {len(ratings_df):,} ratings")
    logger.info(f"Users: {ratings_df['user_id'].nunique():,}")
    logger.info(f"Average rating: {ratings_df['rating'].mean():.2f}")
    
    return movies_df, ratings_df

def convert_to_csv(data_dir='../data', output_dir=None):
    """
    Convert .dat files to CSV format for easier processing
    
    Args:
        data_dir (str): Path to data directory containing .dat files
        output_dir (str): Path to output directory (defaults to data_dir/csv)
    """
    data_path = Path(data_dir)
    
    if output_dir is None:
        output_path = data_path / 'csv'
    else:
        output_path = Path(output_dir)
    
    output_path.mkdir(exist_ok=True)
    
    logger.info(f"Converting .dat files to CSV in {output_path}")
    
    # Convert movies.dat
    movies_file = data_path / 'movies.dat'
    if movies_file.exists():
        logger.info("Converting movies.dat to CSV...")
        movies_df = pd.read_csv(
            movies_file,
            sep='::',
            names=['movie_id', 'title', 'genres'],
            engine='python',
            encoding='latin-1'
        )
        movies_df.to_csv(output_path / 'movies.csv', index=False)
        logger.info(f"Saved {len(movies_df):,} movies to movies.csv")
    
    # Convert ratings.dat
    ratings_file = data_path / 'ratings.dat'
    if ratings_file.exists():
        logger.info("Converting ratings.dat to CSV...")
        ratings_df = pd.read_csv(
            ratings_file,
            sep='::',
            names=['user_id', 'movie_id', 'rating', 'timestamp'],
            engine='python'
        )
        ratings_df.to_csv(output_path / 'ratings.csv', index=False)
        logger.info(f"Saved {len(ratings_df):,} ratings to ratings.csv")
    
    # Convert tags.dat if exists
    tags_file = data_path / 'tags.dat'
    if tags_file.exists():
        logger.info("Converting tags.dat to CSV...")
        try:
            tags_df = pd.read_csv(
                tags_file,
                sep='::',
                names=['user_id', 'movie_id', 'tag', 'timestamp'],
                engine='python',
                encoding='latin-1'
            )
            tags_df.to_csv(output_path / 'tags.csv', index=False)
            logger.info(f"Saved {len(tags_df):,} tags to tags.csv")
        except Exception as e:
            logger.warning(f"Could not convert tags.dat: {e}")
    
    logger.info("CSV conversion complete")
    return output_path

def create_sample_dataset(movies_df, ratings_df, n_movies=1000, n_users=5000, output_path=None):
    """
    Create a smaller sample dataset for faster testing
    
    Args:
        movies_df (pd.DataFrame): Full movies dataset
        ratings_df (pd.DataFrame): Full ratings dataset  
        n_movies (int): Number of movies to include
        n_users (int): Number of users to include
        output_path (str): Path to save sample data
        
    Returns:
        tuple: (sample_movies_df, sample_ratings_df)
    """
    logger.info(f"Creating sample dataset with {n_movies} movies and {n_users} users")
    
    # Get most popular movies
    popular_movies = movies_df.nlargest(n_movies, 'popularity')
    movie_ids = set(popular_movies['movie_id'])
    
    # Get active users who rated these movies
    movie_ratings = ratings_df[ratings_df['movie_id'].isin(movie_ids)]
    user_counts = movie_ratings['user_id'].value_counts()
    active_users = user_counts.head(n_users).index
    
    # Filter ratings
    sample_ratings = ratings_df[
        (ratings_df['movie_id'].isin(movie_ids)) & 
        (ratings_df['user_id'].isin(active_users))
    ]
    
    # Filter movies to only those with ratings
    rated_movie_ids = set(sample_ratings['movie_id'])
    sample_movies = movies_df[movies_df['movie_id'].isin(rated_movie_ids)]
    
    logger.info(f"Sample dataset: {len(sample_movies)} movies, {len(sample_ratings)} ratings")
    logger.info(f"Users: {sample_ratings['user_id'].nunique()}")
    
    if output_path:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        sample_movies.to_csv(output_path / 'sample_movies.csv', index=False)
        sample_ratings.to_csv(output_path / 'sample_ratings.csv', index=False)
        
        logger.info(f"Sample dataset saved to {output_path}")
    
    return sample_movies, sample_ratings

if __name__ == '__main__':
    # Test the loader
    try:
        movies, ratings = load_local_movielens()
        print(f"Successfully loaded {len(movies)} movies and {len(ratings)} ratings")
        
        # Convert to CSV
        csv_dir = convert_to_csv()
        print(f"CSV files saved to {csv_dir}")
        
        # Create sample dataset
        sample_movies, sample_ratings = create_sample_dataset(
            movies, ratings, 
            n_movies=500, 
            n_users=1000,
            output_path='../data/sample'
        )
        print(f"Sample dataset created with {len(sample_movies)} movies and {len(sample_ratings)} ratings")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
