"""
MovieLens Dataset Loader and Downloader

This module handles downloading and loading the MovieLens dataset.
Supports both MovieLens 10M and 1M datasets with sample options.
"""

import os
import sys
import argparse
import requests
import zipfile
import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovieLensLoader:
    """Handles downloading and loading MovieLens datasets"""
    
    DATASETS = {
        '10M': {
            'url': 'https://files.grouplens.org/datasets/movielens/ml-10m.zip',
            'folder': 'ml-10M100K',
            'files': {
                'movies': 'movies.dat',
                'ratings': 'ratings.dat',
                'tags': 'tags.dat'
            }
        },
        '1M': {
            'url': 'https://files.grouplens.org/datasets/movielens/ml-1m.zip',
            'folder': 'ml-1m',
            'files': {
                'movies': 'movies.dat',
                'ratings': 'ratings.dat',
                'users': 'users.dat'
            }
        }
    }
    
    def __init__(self, data_dir='./data'):
        """Initialize loader with data directory"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def download_dataset(self, dataset='10M', force_download=False):
        """
        Download MovieLens dataset
        
        Args:
            dataset (str): Dataset version ('10M' or '1M')
            force_download (bool): Force re-download if exists
            
        Returns:
            Path: Path to extracted dataset folder
        """
        if dataset not in self.DATASETS:
            raise ValueError(f"Dataset {dataset} not supported. Use '10M' or '1M'")
        
        config = self.DATASETS[dataset]
        zip_path = self.data_dir / f"ml-{dataset.lower()}.zip"
        extract_path = self.data_dir / config['folder']
        
        # Check if already exists
        if extract_path.exists() and not force_download:
            logger.info(f"Dataset {dataset} already exists at {extract_path}")
            return extract_path
        
        # Download dataset
        logger.info(f"Downloading MovieLens {dataset} dataset...")
        response = requests.get(config['url'], stream=True)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract dataset
        logger.info(f"Extracting dataset to {extract_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.data_dir)
        
        # Clean up zip file
        zip_path.unlink()
        
        logger.info(f"Dataset {dataset} downloaded and extracted successfully")
        return extract_path
    
    def load_movies(self, dataset_path, dataset='10M'):
        """
        Load movies data
        
        Args:
            dataset_path (Path): Path to dataset folder
            dataset (str): Dataset version
            
        Returns:
            pd.DataFrame: Movies dataframe
        """
        config = self.DATASETS[dataset]
        movies_file = dataset_path / config['files']['movies']
        
        if dataset == '10M':
            # MovieLens 10M format: MovieID::Title::Genres
            movies = pd.read_csv(
                movies_file,
                sep='::',
                names=['movie_id', 'title', 'genres'],
                engine='python',
                encoding='latin-1'
            )
        else:  # 1M
            # MovieLens 1M format: MovieID::Title::Genres
            movies = pd.read_csv(
                movies_file,
                sep='::',
                names=['movie_id', 'title', 'genres'],
                engine='python',
                encoding='latin-1'
            )
        
        # Process genres into list
        movies['genres'] = movies['genres'].str.split('|')
        
        # Extract year from title
        movies['year'] = movies['title'].str.extract(r'\((\d{4})\)').astype(float)
        movies['title_clean'] = movies['title'].str.replace(r'\s*\(\d{4}\)', '', regex=True)
        
        logger.info(f"Loaded {len(movies)} movies")
        return movies
    
    def load_ratings(self, dataset_path, dataset='10M', sample_size=None):
        """
        Load ratings data
        
        Args:
            dataset_path (Path): Path to dataset folder
            dataset (str): Dataset version
            sample_size (int): Number of ratings to sample (for testing)
            
        Returns:
            pd.DataFrame: Ratings dataframe
        """
        config = self.DATASETS[dataset]
        ratings_file = dataset_path / config['files']['ratings']
        
        if dataset == '10M':
            # MovieLens 10M format: UserID::MovieID::Rating::Timestamp
            ratings = pd.read_csv(
                ratings_file,
                sep='::',
                names=['user_id', 'movie_id', 'rating', 'timestamp'],
                engine='python'
            )
        else:  # 1M
            # MovieLens 1M format: UserID::MovieID::Rating::Timestamp
            ratings = pd.read_csv(
                ratings_file,
                sep='::',
                names=['user_id', 'movie_id', 'rating', 'timestamp'],
                engine='python'
            )
        
        # Convert timestamp to datetime
        ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')
        
        # Sample if requested
        if sample_size and len(ratings) > sample_size:
            logger.info(f"Sampling {sample_size} ratings from {len(ratings)} total")
            ratings = ratings.sample(n=sample_size, random_state=42)
        
        logger.info(f"Loaded {len(ratings)} ratings")
        return ratings
    
    def load_users(self, dataset_path, dataset='1M'):
        """
        Load users data (only available in 1M dataset)
        
        Args:
            dataset_path (Path): Path to dataset folder
            dataset (str): Dataset version
            
        Returns:
            pd.DataFrame: Users dataframe or None if not available
        """
        if dataset != '1M':
            logger.warning("Users data only available in MovieLens 1M dataset")
            return None
        
        config = self.DATASETS[dataset]
        users_file = dataset_path / config['files']['users']
        
        # MovieLens 1M format: UserID::Gender::Age::Occupation::Zip-code
        users = pd.read_csv(
            users_file,
            sep='::',
            names=['user_id', 'gender', 'age', 'occupation', 'zip_code'],
            engine='python'
        )
        
        logger.info(f"Loaded {len(users)} users")
        return users
    
    def create_sample_dataset(self, output_path, n_users=1000, n_movies=500):
        """
        Create a small sample dataset for testing
        
        Args:
            output_path (str): Path to save sample dataset
            n_users (int): Number of users to include
            n_movies (int): Number of movies to include
        """
        logger.info(f"Creating sample dataset with {n_users} users and {n_movies} movies")
        
        # Create sample movies
        sample_movies = pd.DataFrame({
            'movie_id': range(1, n_movies + 1),
            'title': [f'Sample Movie {i}' for i in range(1, n_movies + 1)],
            'genres': [['Action', 'Comedy', 'Drama', 'Thriller', 'Sci-Fi', 'Romance', 'Horror'][i % 7] 
                      for i in range(n_movies)],
            'year': np.random.randint(1990, 2024, n_movies)
        })
        
        # Create sample ratings
        np.random.seed(42)
        n_ratings = n_users * 20  # Average 20 ratings per user
        sample_ratings = pd.DataFrame({
            'user_id': np.random.randint(1, n_users + 1, n_ratings),
            'movie_id': np.random.randint(1, n_movies + 1, n_ratings),
            'rating': np.random.choice([1, 2, 3, 4, 5], n_ratings, p=[0.1, 0.1, 0.2, 0.3, 0.3]),
            'timestamp': pd.date_range('2020-01-01', periods=n_ratings, freq='H')
        })
        
        # Remove duplicates
        sample_ratings = sample_ratings.drop_duplicates(['user_id', 'movie_id'])
        
        # Save sample dataset
        sample_data = {
            'movies': sample_movies,
            'ratings': sample_ratings
        }
        
        pd.to_pickle(sample_data, output_path)
        logger.info(f"Sample dataset saved to {output_path}")
        return sample_data


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Download and load MovieLens dataset')
    parser.add_argument('--dataset', choices=['10M', '1M'], default='10M',
                       help='Dataset version to download')
    parser.add_argument('--out', type=str, default='./data/preprocessed.pkl',
                       help='Output path for preprocessed data')
    parser.add_argument('--sample', type=int, default=None,
                       help='Sample size for ratings (for testing)')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create small sample dataset instead of downloading')
    parser.add_argument('--force-download', action='store_true',
                       help='Force re-download even if exists')
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = MovieLensLoader()
    
    if args.create_sample:
        # Create sample dataset
        loader.create_sample_dataset(args.out)
        return
    
    try:
        # Download dataset
        dataset_path = loader.download_dataset(args.dataset, args.force_download)
        
        # Load data
        movies = loader.load_movies(dataset_path, args.dataset)
        ratings = loader.load_ratings(dataset_path, args.dataset, args.sample)
        users = loader.load_users(dataset_path, args.dataset)
        
        # Combine into single structure
        data = {
            'movies': movies,
            'ratings': ratings,
            'users': users
        }
        
        # Save preprocessed data
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.to_pickle(data, output_path)
        
        logger.info(f"Preprocessed data saved to {output_path}")
        logger.info(f"Movies: {len(movies)}, Ratings: {len(ratings)}")
        if users is not None:
            logger.info(f"Users: {len(users)}")
        
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        sys.exit(1)


# Convenience functions for direct import
def download_movielens_10m(data_dir='./data'):
    """Download MovieLens 10M dataset"""
    loader = MovieLensLoader(data_dir)
    return loader.download_dataset('10M')

def load_movielens_10m(data_dir='./data', sample_size=None):
    """Load MovieLens 10M dataset"""
    loader = MovieLensLoader(data_dir)
    
    # Download if not exists
    dataset_path = loader.download_dataset('10M')
    
    # Load data
    movies = loader.load_movies(dataset_path, '10M')
    ratings = loader.load_ratings(dataset_path, '10M', sample_size)
    
    # Add movie statistics
    rating_stats = ratings.groupby('movie_id').agg({
        'rating': ['mean', 'count', 'std']
    }).round(2)
    rating_stats.columns = ['avg_rating', 'rating_count', 'rating_std']
    rating_stats = rating_stats.reset_index()
    
    # Merge with movies
    movies = movies.merge(rating_stats, on='movie_id', how='left')
    movies['avg_rating'] = movies['avg_rating'].fillna(0)
    movies['rating_count'] = movies['rating_count'].fillna(0)
    movies['rating_std'] = movies['rating_std'].fillna(0)
    
    # Calculate popularity score
    movies['popularity'] = (movies['avg_rating'] * np.log1p(movies['rating_count'])).fillna(0)
    
    return movies, ratings

if __name__ == '__main__':
    main()
