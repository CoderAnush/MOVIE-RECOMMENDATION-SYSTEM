"""
Utility Functions for Movie Recommendation System

This module provides helper functions for metrics calculation, 
model saving/loading, and other common operations.
"""

import numpy as np
import pandas as pd
import pickle
import logging
import json
from pathlib import Path
from sklearn.metrics import mean_squared_error, mean_absolute_error
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level
        log_file (str): Optional log file path
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if log_file:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(level=log_level, format=log_format)

def calculate_recommendation_metrics(y_true, y_pred):
    """
    Calculate recommendation system metrics
    
    Args:
        y_true (array-like): True ratings
        y_pred (array-like): Predicted ratings
        
    Returns:
        dict: Dictionary of metrics
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Basic regression metrics
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    
    # Additional metrics
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = 1 - (np.sum((y_true - y_pred) ** 2) / np.sum((y_true - np.mean(y_true)) ** 2))
    
    return {
        'mse': mse,
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'r2': r2
    }

def calculate_ranking_metrics(y_true, y_pred, k=10):
    """
    Calculate ranking-based metrics for recommendation systems
    
    Args:
        y_true (array-like): True ratings
        y_pred (array-like): Predicted ratings
        k (int): Top-k for metrics calculation
        
    Returns:
        dict: Dictionary of ranking metrics
    """
    # Convert to numpy arrays
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Get top-k predictions
    top_k_indices = np.argsort(y_pred)[-k:][::-1]
    
    # Calculate precision@k (simplified - assumes ratings >= 4 are relevant)
    relevant_threshold = 4.0
    relevant_items = y_true >= relevant_threshold
    recommended_relevant = np.sum(relevant_items[top_k_indices])
    
    precision_at_k = recommended_relevant / k if k > 0 else 0
    
    # Calculate recall@k
    total_relevant = np.sum(relevant_items)
    recall_at_k = recommended_relevant / total_relevant if total_relevant > 0 else 0
    
    # Calculate F1@k
    f1_at_k = (2 * precision_at_k * recall_at_k) / (precision_at_k + recall_at_k) \
              if (precision_at_k + recall_at_k) > 0 else 0
    
    return {
        f'precision@{k}': precision_at_k,
        f'recall@{k}': recall_at_k,
        f'f1@{k}': f1_at_k
    }

def save_model_metadata(model_info, filepath):
    """
    Save model metadata to JSON file
    
    Args:
        model_info (dict): Model information dictionary
        filepath (str): Path to save metadata
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        return obj
    
    model_info_serializable = convert_numpy_types(model_info)
    
    with open(filepath, 'w') as f:
        json.dump(model_info_serializable, f, indent=2)
    
    logger.info(f"Model metadata saved to {filepath}")

def load_model_metadata(filepath):
    """
    Load model metadata from JSON file
    
    Args:
        filepath (str): Path to metadata file
        
    Returns:
        dict: Model information dictionary
    """
    with open(filepath, 'r') as f:
        model_info = json.load(f)
    
    logger.info(f"Model metadata loaded from {filepath}")
    return model_info

def save_pickle(obj, filepath):
    """
    Save object to pickle file
    
    Args:
        obj: Object to save
        filepath (str): Path to save file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'wb') as f:
        pickle.dump(obj, f)
    
    logger.info(f"Object saved to {filepath}")

def load_pickle(filepath):
    """
    Load object from pickle file
    
    Args:
        filepath (str): Path to pickle file
        
    Returns:
        object: Loaded object
    """
    with open(filepath, 'rb') as f:
        obj = pickle.load(f)
    
    logger.info(f"Object loaded from {filepath}")
    return obj

def create_user_movie_matrix(ratings_df, fill_value=0):
    """
    Create user-movie rating matrix from ratings dataframe
    
    Args:
        ratings_df (pd.DataFrame): Ratings dataframe
        fill_value (float): Value to fill missing ratings
        
    Returns:
        pd.DataFrame: User-movie matrix
    """
    user_movie_matrix = ratings_df.pivot_table(
        index='user_id',
        columns='movie_id',
        values='rating',
        fill_value=fill_value
    )
    
    logger.info(f"Created user-movie matrix: {user_movie_matrix.shape}")
    return user_movie_matrix

def get_movie_stats(ratings_df, movies_df):
    """
    Calculate movie statistics
    
    Args:
        ratings_df (pd.DataFrame): Ratings dataframe
        movies_df (pd.DataFrame): Movies dataframe
        
    Returns:
        pd.DataFrame: Movie statistics
    """
    movie_stats = ratings_df.groupby('movie_id').agg({
        'rating': ['count', 'mean', 'std'],
        'user_id': 'nunique'
    }).round(3)
    
    movie_stats.columns = ['rating_count', 'avg_rating', 'rating_std', 'user_count']
    movie_stats = movie_stats.reset_index()
    
    # Merge with movie information
    movie_stats = movie_stats.merge(movies_df[['movie_id', 'title', 'genres']], 
                                   on='movie_id', how='left')
    
    return movie_stats

def get_user_stats(ratings_df):
    """
    Calculate user statistics
    
    Args:
        ratings_df (pd.DataFrame): Ratings dataframe
        
    Returns:
        pd.DataFrame: User statistics
    """
    user_stats = ratings_df.groupby('user_id').agg({
        'rating': ['count', 'mean', 'std'],
        'movie_id': 'nunique'
    }).round(3)
    
    user_stats.columns = ['rating_count', 'avg_rating', 'rating_std', 'movie_count']
    user_stats = user_stats.reset_index()
    
    return user_stats

def filter_sparse_data(ratings_df, min_user_ratings=10, min_movie_ratings=5):
    """
    Filter out sparse users and movies
    
    Args:
        ratings_df (pd.DataFrame): Ratings dataframe
        min_user_ratings (int): Minimum ratings per user
        min_movie_ratings (int): Minimum ratings per movie
        
    Returns:
        pd.DataFrame: Filtered ratings dataframe
    """
    original_size = len(ratings_df)
    
    # Filter users with too few ratings
    user_counts = ratings_df['user_id'].value_counts()
    valid_users = user_counts[user_counts >= min_user_ratings].index
    ratings_filtered = ratings_df[ratings_df['user_id'].isin(valid_users)]
    
    # Filter movies with too few ratings
    movie_counts = ratings_filtered['movie_id'].value_counts()
    valid_movies = movie_counts[movie_counts >= min_movie_ratings].index
    ratings_filtered = ratings_filtered[ratings_filtered['movie_id'].isin(valid_movies)]
    
    logger.info(f"Filtered ratings: {original_size} -> {len(ratings_filtered)} "
               f"({len(ratings_filtered)/original_size*100:.1f}%)")
    
    return ratings_filtered

def normalize_ratings(ratings, old_range=(1, 5), new_range=(0, 10)):
    """
    Normalize ratings to new range
    
    Args:
        ratings (array-like): Original ratings
        old_range (tuple): Original rating range (min, max)
        new_range (tuple): Target rating range (min, max)
        
    Returns:
        np.array: Normalized ratings
    """
    ratings = np.array(ratings)
    old_min, old_max = old_range
    new_min, new_max = new_range
    
    normalized = (ratings - old_min) / (old_max - old_min) * (new_max - new_min) + new_min
    
    return normalized

def denormalize_ratings(ratings, old_range=(0, 10), new_range=(1, 5)):
    """
    Denormalize ratings back to original range
    
    Args:
        ratings (array-like): Normalized ratings
        old_range (tuple): Current rating range (min, max)
        new_range (tuple): Target rating range (min, max)
        
    Returns:
        np.array: Denormalized ratings
    """
    return normalize_ratings(ratings, old_range, new_range)

def get_genre_distribution(movies_df):
    """
    Get genre distribution statistics
    
    Args:
        movies_df (pd.DataFrame): Movies dataframe with genres column
        
    Returns:
        pd.Series: Genre counts
    """
    all_genres = []
    for genres in movies_df['genres'].dropna():
        if isinstance(genres, list):
            all_genres.extend(genres)
        elif isinstance(genres, str):
            all_genres.extend(genres.split('|'))
    
    genre_counts = pd.Series(all_genres).value_counts()
    
    logger.info(f"Found {len(genre_counts)} unique genres")
    return genre_counts

def create_train_test_split_by_user(ratings_df, test_size=0.2, random_state=42):
    """
    Create train-test split ensuring each user appears in both sets
    
    Args:
        ratings_df (pd.DataFrame): Ratings dataframe
        test_size (float): Proportion of test data
        random_state (int): Random seed
        
    Returns:
        tuple: (train_df, test_df)
    """
    np.random.seed(random_state)
    
    train_data = []
    test_data = []
    
    for user_id in ratings_df['user_id'].unique():
        user_ratings = ratings_df[ratings_df['user_id'] == user_id]
        
        if len(user_ratings) == 1:
            # If user has only one rating, put it in training
            train_data.append(user_ratings)
        else:
            # Split user's ratings
            n_test = max(1, int(len(user_ratings) * test_size))
            test_indices = np.random.choice(user_ratings.index, n_test, replace=False)
            
            user_test = user_ratings.loc[test_indices]
            user_train = user_ratings.drop(test_indices)
            
            train_data.append(user_train)
            test_data.append(user_test)
    
    train_df = pd.concat(train_data, ignore_index=True)
    test_df = pd.concat(test_data, ignore_index=True)
    
    logger.info(f"Train-test split: {len(train_df)} train, {len(test_df)} test")
    
    return train_df, test_df

def format_recommendation_response(recommendations, movies_df):
    """
    Format recommendation results for API response
    
    Args:
        recommendations (list): List of recommendation dictionaries
        movies_df (pd.DataFrame): Movies dataframe for additional info
        
    Returns:
        list: Formatted recommendation list
    """
    formatted = []
    
    for rec in recommendations:
        movie_id = rec['movie_id']
        
        # Get movie info
        movie_info = movies_df[movies_df['movie_id'] == movie_id]
        
        if not movie_info.empty:
            movie_row = movie_info.iloc[0]
            
            formatted_rec = {
                'movie_id': movie_id,
                'title': movie_row.get('title', 'Unknown'),
                'genres': movie_row.get('genres', []),
                'year': movie_row.get('year', None),
                'final_score': rec.get('final_score', 0),
                'ann_score': rec.get('ann_score', 0),
                'fuzzy_score': rec.get('fuzzy_score', 0),
                'explanation': rec.get('explanation', ''),
                'popularity': movie_row.get('popularity', 0)
            }
            
            formatted.append(formatted_rec)
    
    return formatted

def validate_user_preferences(preferences):
    """
    Validate user preference input
    
    Args:
        preferences (dict): User preferences dictionary
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid_genres = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime',
                   'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical',
                   'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
    
    valid_levels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
    
    if not isinstance(preferences, dict):
        return False, "Preferences must be a dictionary"
    
    for genre, level in preferences.items():
        if genre not in valid_genres:
            return False, f"Invalid genre: {genre}"
        
        if level not in valid_levels:
            return False, f"Invalid preference level: {level}"
    
    return True, "Valid preferences"

def get_memory_usage():
    """
    Get current memory usage information
    
    Returns:
        dict: Memory usage statistics
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
        'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
        'percent': process.memory_percent()
    }

def log_performance_metrics(func_name, execution_time, memory_before, memory_after):
    """
    Log performance metrics for a function
    
    Args:
        func_name (str): Function name
        execution_time (float): Execution time in seconds
        memory_before (dict): Memory usage before execution
        memory_after (dict): Memory usage after execution
    """
    memory_diff = memory_after['rss_mb'] - memory_before['rss_mb']
    
    logger.info(f"Performance - {func_name}:")
    logger.info(f"  Execution time: {execution_time:.3f}s")
    logger.info(f"  Memory usage: {memory_diff:+.2f}MB")
    logger.info(f"  Final memory: {memory_after['rss_mb']:.2f}MB ({memory_after['percent']:.1f}%)")

class PerformanceTimer:
    """Context manager for timing code execution"""
    
    def __init__(self, name="Operation"):
        self.name = name
        self.start_time = None
        self.memory_before = None
    
    def __enter__(self):
        self.memory_before = get_memory_usage()
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        memory_after = get_memory_usage()
        log_performance_metrics(self.name, execution_time, self.memory_before, memory_after)

import time
from functools import wraps

def log_performance(func):
    """
    Decorator to log function performance metrics
    
    Args:
        func: Function to wrap
        
    Returns:
        function: Wrapped function with performance logging
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            memory_before = get_memory_usage()
        except:
            memory_before = {'rss_mb': 0, 'vms_mb': 0, 'percent': 0}
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            try:
                memory_after = get_memory_usage()
            except:
                memory_after = {'rss_mb': 0, 'vms_mb': 0, 'percent': 0}
            
            log_performance_metrics(func.__name__, execution_time, memory_before, memory_after)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper
