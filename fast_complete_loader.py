"""
Fast Complete MovieLens Loader - Optimized for Production Use
Uses pre-processed parquet files for instant loading of full 10M dataset
"""

import os
import json
import math
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FastCompleteMovieLensLoader:
    """Optimized loader for complete MovieLens dataset using processed files"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.processed_dir = os.path.join(self.base_dir, 'processed')
        self.data_summary = None
        
    def load_dataset_summary(self):
        """Load pre-computed dataset statistics"""
        summary_file = os.path.join(self.processed_dir, 'dataset_summary.json')
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                self.data_summary = json.load(f)
                return self.data_summary
        return None
        
    def get_fast_movie_database(self) -> List[Dict[str, Any]]:
        """Load complete movie database using optimized processed data"""
        print("🚀 Loading Complete MovieLens 10M Database (Fast Mode)...")
        
        # Check for optimized parquet files
        movies_parquet = os.path.join(self.processed_dir, 'movies_enriched.parquet')
        
        if os.path.exists(movies_parquet):
            return self._load_from_parquet()
        else:
            return self._load_from_csv_optimized()
            
    def _load_from_parquet(self) -> List[Dict[str, Any]]:
        """Load from optimized parquet files"""
        print("📊 Using optimized parquet data...")
        
        movies_parquet = os.path.join(self.processed_dir, 'movies_enriched.parquet')
        movies_df = pd.read_parquet(movies_parquet)
        
        print(f"✅ Loaded {len(movies_df)} movies from parquet")
        
        movie_database = []
        poster_urls = self._get_poster_mapping()
        
        print(f"🚀 Generating metadata for {len(movies_df)} movies...")
        
        for idx, (_, row) in enumerate(movies_df.iterrows()):
            if idx % 1000 == 0:
                print(f"Processed {idx}/{len(movies_df)} movies...")
                
            title = str(row.get('title', row.get('Title', 'Unknown Movie')))
            year = str(row.get('year', row.get('Year', '2000')))
            genres = row.get('genres', row.get('GenresList', ['Drama']))
            
            # Ensure genres is a list
            if isinstance(genres, str):
                genres = [g.strip() for g in genres.split('|') if g.strip()]
            elif not isinstance(genres, list):
                genres = ['Drama']

            # Handle NaN values and normalize rating to 10-point scale
            raw_rating = row.get('avg_rating', row.get('rating', 3.5))
            if pd.isna(raw_rating) or raw_rating is None:
                raw_rating = 3.5
            rating = round(min(10.0, max(1.0, float(raw_rating) * 2.0)), 1)
                
            num_ratings = row.get('rating_count', row.get('num_ratings', 100))
            if pd.isna(num_ratings) or num_ratings is None:
                num_ratings = 100
            num_ratings = int(num_ratings)

            movie_id = int(row.get('MovieID', row.get('id', idx + 1)))

            # Popularity score rewards frequently rated, well-liked films
            popularity = round(
                min(100.0, (math.log1p(num_ratings) * 10) + (rating * 2.5)),
                2
            )

            poster_url = poster_urls.get(title) or poster_urls.get(movie_id) or self._get_placeholder_poster()

            box_office = self._generate_box_office_fast(rating)
            budget = self._generate_budget_fast(rating, popularity)
                
            movie_data = {
                'id': movie_id,
                'title': title,
                'year': year,
                'genres': genres,
                'rating': rating,
                'num_ratings': num_ratings,
                'rating_count': num_ratings,
                'popularity': popularity,
                'poster': poster_url,
                'poster_url': poster_url,
                'description': self._generate_description_fast(title, genres, rating),
                'director': self._generate_director_fast(movie_id if movie_id else idx),
                'cast': self._generate_cast_fast(movie_id if movie_id else idx),
                'runtime': self._generate_runtime_fast(genres),
                'awards': self._generate_awards_fast(rating),
                'box_office': box_office,
                'budget': budget
            }
            movie_database.append(movie_data)
            
        return movie_database
        
    def _load_from_csv_optimized(self) -> List[Dict[str, Any]]:
        """Fallback to CSV with optimizations"""
        print("📁 Loading from CSV files (optimized)...")
        
        # Load movies data
        movies_file = os.path.join(self.base_dir, 'data', 'ml-10M100K', 'movies.dat')
        if not os.path.exists(movies_file):
            movies_file = os.path.join(self.base_dir, 'data', 'ml-1m', 'movies.dat')
            
        if not os.path.exists(movies_file):
            raise FileNotFoundError("No movies.dat file found")
            
        # Read movies
        movies_df = pd.read_csv(movies_file, sep='::', names=['MovieID', 'Title', 'Genres'], engine='python')
        
        # Sample ratings for statistics (much faster than full dataset)
        ratings_file = movies_file.replace('movies.dat', 'ratings.dat')
        if os.path.exists(ratings_file):
            print("📈 Sampling ratings for statistics...")
            # Read only first 100k ratings for speed
            ratings_sample = pd.read_csv(ratings_file, sep='::', names=['UserID', 'MovieID', 'Rating', 'Timestamp'], 
                                       engine='python', nrows=100000)
            
            # Calculate basic stats
            movie_stats = ratings_sample.groupby('MovieID').agg({
                'Rating': ['mean', 'count']
            }).round(2)
            movie_stats.columns = ['avg_rating', 'rating_count']
        else:
            movie_stats = pd.DataFrame()
            
        print(f"🎬 Processing {len(movies_df)} movies...")
        
        movie_database = []
        poster_urls = self._get_poster_mapping()
        
        for _, row in movies_df.iterrows():
            movie_id = int(row['MovieID'])
            title_parts = row['Title'].rsplit(' (', 1)
            title = title_parts[0].strip()
            year = title_parts[1].replace(')', '').strip() if len(title_parts) > 1 else "2000"
            
            if not year.isdigit():
                year = "2000"
                
            genres = [g.strip() for g in row['Genres'].split('|') if g.strip()]
            
            # Get stats from sample
            if movie_id in movie_stats.index:
                rating = float(movie_stats.loc[movie_id, 'avg_rating'])
                rating_count = int(movie_stats.loc[movie_id, 'rating_count'])
            else:
                rating = np.random.uniform(6.0, 8.0)  # Realistic default
                rating_count = np.random.randint(50, 500)
                
            movie_data = {
                'id': movie_id,
                'title': title,
                'year': year,
                'genres': genres,
                'rating': round(rating, 1),
                'num_ratings': rating_count,
                'poster': poster_urls.get(title, self._get_placeholder_poster()),
                'description': self._generate_description(title, genres, rating),
                'director': self._generate_director(title),
                'cast': self._generate_cast(),
                'runtime': self._generate_runtime(genres),
                'awards': self._generate_awards(rating),
                'box_office': self._generate_box_office(rating)
            }
            movie_database.append(movie_data)
            
        print(f"✅ Generated database with {len(movie_database)} movies")
        return movie_database
        
    def _get_poster_mapping(self) -> Dict[str, str]:
        """Get high-quality poster URLs for popular movies from cached file"""
        poster_file = os.path.join(self.processed_dir, 'fast_movie_posters.json')
        
        if os.path.exists(poster_file):
            try:
                with open(poster_file, 'r', encoding='utf-8') as f:
                    poster_data = json.load(f)
                    poster_map = {}
                    
                    # Create mapping by both title and ID
                    for movie in poster_data.get('movies', []):
                        movie_id = movie.get('id')
                        title = movie.get('title')
                        poster_url = movie.get('poster') or movie.get('poster_url')
                        
                        if poster_url and 'placeholder' not in poster_url.lower():
                            if title:
                                poster_map[title] = poster_url
                            if movie_id:
                                poster_map[movie_id] = poster_url
                    
                    print(f"✅ Loaded {len(poster_map)} real movie posters from cache")
                    return poster_map
            except Exception as e:
                print(f"⚠️ Error loading poster cache: {e}")
        
        # Fallback to basic mapping
        return {
            "Toy Story": "https://m.media-amazon.com/images/M/MV5BMDU2ZWJlMjktMTRhMy00ZTA5LWEzNDgtYmNmZTEwZTViZWJkXkEyXkFqcGdeQXVyNDQ2OTk4MzI@._V1_SX300.jpg",
            "Jumanji": "https://m.media-amazon.com/images/M/MV5BZTk2ZmUwYmEtNTcwZS00YmMyLWFkYjMtNTRmZDA3YWExMjc2XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg",
            "Grumpier Old Men": "https://m.media-amazon.com/images/M/MV5BMjQxM2YyNjMtZjUxYy00OGYyLTg0MmQtNGE2YzNjYmUyZTY1XkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg",
            "Waiting to Exhale": "https://m.media-amazon.com/images/M/MV5BYzRkMjg2NTctN2E4Ni00YWZlLTkwYTEtMDQ3YzI0ZWYyY2Q5XkEyXkFqcGdeQXVyNjUwNzk3NDc@._V1_SX300.jpg",
            "Father of the Bride Part II": "https://m.media-amazon.com/images/M/MV5BMjE1MTY0Mzk3N15BMl5BanBnXkFtZTcwMTc1MDA0MQ@@._V1_SX300.jpg",
            "Heat": "https://m.media-amazon.com/images/M/MV5BNDc0MGE4NDQtZmFkNy00MmU2LTg3Y2MtZDgzMmQ4MDBmYmI4XkEyXkFqcGdeQXVyODkzNTgxMDg@._V1_SX300.jpg",
            "Sabrina": "https://m.media-amazon.com/images/M/MV5BNjI4NzE0MzMtMzBmNC00NDI3LWFmZjMtNzI0YjkyN2NkNzgzXkEyXkFqcGdeQXVyNTI4MjkwNjA@._V1_SX300.jpg",
            "Tom and Huck": "https://m.media-amazon.com/images/M/MV5BMTcwODI2NzM5N15BMl5BanBnXkFtZTcwMDA4MDI0MQ@@._V1_SX300.jpg",
            "Sudden Death": "https://m.media-amazon.com/images/M/MV5BMTQwNTgyNTEzM15BMl5BanBnXkFtZTcwNDE0MTQ0MQ@@._V1_SX300.jpg",
            "GoldenEye": "https://m.media-amazon.com/images/M/MV5BMzk2OTg4MTk1NF5BMl5BanBnXkFtZTcwNjExNTgzNA@@._V1_SX300.jpg",
            "The American President": "https://m.media-amazon.com/images/M/MV5BNDJhYzlhMDAtMzk2Yi00Y2QxLWI5OTctZmI0ZmZkMWViZjJmXkEyXkFqcGdeQXVyMTAwMzUyOTc@._V1_SX300.jpg",
            "Dracula: Dead and Loving It": "https://m.media-amazon.com/images/M/MV5BOGQzYzZhNDMtNzE4My00ZGE2LWFkYmUtZjY3MzEwYzFmNzYxXkEyXkFqcGdeQXVyNTE1NjY5Mg@@._V1_SX300.jpg",
            "Balto": "https://m.media-amazon.com/images/M/MV5BYTJkYWE2Y2ItZjY2YS00MWY3LTliZmMtMGYzZTgwOTgyODY5XkEyXkFqcGdeQXVyNzI1NzMxNzM@._V1_SX300.jpg"
        }
        
    def _get_placeholder_poster(self) -> str:
        """Get placeholder poster URL"""
        return "https://via.placeholder.com/300x450/1a1a1a/ffffff?text=Movie+Poster"
        
    def _generate_description(self, title: str, genres: List[str], rating: float) -> str:
        """Generate movie description"""
        if not genres:
            return f"A captivating film that has earned a rating of {rating:.1f}/10 from audiences."
            
        primary_genre = genres[0].lower()
        
        if rating >= 8.5:
            quality = "masterful"
        elif rating >= 7.5:
            quality = "excellent"
        elif rating >= 6.5:
            quality = "compelling"
        else:
            quality = "interesting"
            
        descriptions = {
            'action': f"An {quality} action-packed thriller with intense sequences and spectacular stunts.",
            'adventure': f"An {quality} adventure that takes audiences on an exciting journey.",
            'animation': f"A {quality} animated film with stunning visuals and engaging storytelling.",
            'comedy': f"A {quality} comedy that delivers laughs with wit and memorable characters.",
            'crime': f"A {quality} crime drama exploring the underworld with complex characters.",
            'drama': f"A {quality} dramatic story that explores deep human emotions and relationships.",
            'fantasy': f"A {quality} fantasy epic that transports viewers to extraordinary worlds.",
            'horror': f"A {quality} horror film that will keep you on the edge of your seat.",
            'romance': f"A {quality} romantic story about love and human connection.",
            'sci-fi': f"A {quality} science fiction epic that explores the boundaries of imagination.",
            'thriller': f"A {quality} thriller that keeps audiences guessing until the end.",
            'western': f"A {quality} western adventure set in the American frontier."
        }
        
        return descriptions.get(primary_genre, f"A {quality} cinematic experience that captivates audiences.")
        
    def _generate_director(self, title: str) -> str:
        """Generate director name"""
        directors = [
            "Christopher Nolan", "Steven Spielberg", "Martin Scorsese", "Quentin Tarantino",
            "David Fincher", "Ridley Scott", "James Cameron", "George Lucas", 
            "Peter Jackson", "Tim Burton", "Guillermo del Toro", "Denis Villeneuve"
        ]
        # Use title hash for consistency
        return directors[hash(title) % len(directors)]
        
    def _generate_cast(self) -> List[str]:
        """Generate cast list"""
        actors = [
            "Leonardo DiCaprio", "Robert De Niro", "Meryl Streep", "Tom Hanks",
            "Scarlett Johansson", "Brad Pitt", "Jennifer Lawrence", "Christian Bale",
            "Natalie Portman", "Ryan Gosling", "Emma Stone", "Oscar Isaac"
        ]
        return np.random.choice(actors, size=3, replace=False).tolist()
        
    def _generate_runtime(self, genres: List[str]) -> int:
        """Generate realistic runtime based on genres"""
        if 'drama' in [g.lower() for g in genres]:
            return np.random.randint(120, 180)
        elif 'action' in [g.lower() for g in genres]:
            return np.random.randint(100, 140)
        elif 'comedy' in [g.lower() for g in genres]:
            return np.random.randint(90, 120)
        else:
            return np.random.randint(95, 135)
            
    def _generate_awards(self, rating: float) -> str:
        """Generate awards based on rating"""
        if rating >= 9.0:
            return "Academy Award Winner - Best Picture. Golden Globe Winner."
        elif rating >= 8.5:
            return "Academy Award Nominee. Critics' Choice Award Winner."
        elif rating >= 8.0:
            return "Golden Globe Nominee. SAG Award Winner."
        elif rating >= 7.5:
            return "Critics' Choice Award Nominee. Festival Winner."
        elif rating >= 7.0:
            return "Independent Spirit Award Nominee."
        else:
            return "Audience Choice Award."
            
    def _generate_box_office(self, rating: float) -> str:
        """Generate box office based on rating"""
        if rating >= 8.5:
            revenue = np.random.randint(200, 800)
            return f"${revenue}M worldwide"
        elif rating >= 7.5:
            revenue = np.random.randint(100, 400)
            return f"${revenue}M worldwide"
        elif rating >= 6.5:
            revenue = np.random.randint(50, 200)
            return f"${revenue}M worldwide"
        else:
            revenue = np.random.randint(10, 100)
            return f"${revenue}M worldwide"
            
    # Fast generation methods (pre-computed for speed)
    def _generate_description_fast(self, title: str, genres: List[str], rating: float) -> str:
        """Fast description generation"""
        primary_genre = genres[0].lower() if genres else 'drama'
        quality = "excellent" if rating >= 7.5 else "compelling"
        return f"A {quality} {primary_genre} film that has earned a {rating:.1f}/10 rating."
        
    def _generate_director_fast(self, idx: int) -> str:
        """Fast director generation using index"""
        directors = ["Christopher Nolan", "Steven Spielberg", "Martin Scorsese", "Quentin Tarantino", 
                    "David Fincher", "Ridley Scott", "James Cameron", "George Lucas"]
        return directors[idx % len(directors)]
        
    def _generate_cast_fast(self, idx: int) -> List[str]:
        """Fast cast generation using index"""
        actors = ["Leonardo DiCaprio", "Robert De Niro", "Meryl Streep", "Tom Hanks",
                 "Scarlett Johansson", "Brad Pitt", "Jennifer Lawrence", "Christian Bale"]
        start_idx = (idx * 3) % len(actors)
        return [actors[(start_idx + i) % len(actors)] for i in range(3)]
        
    def _generate_runtime_fast(self, genres: List[str]) -> int:
        """Fast runtime generation"""
        return 120 if 'drama' in [g.lower() for g in genres] else 105
        
    def _generate_awards_fast(self, rating: float) -> str:
        """Fast awards generation"""
        if rating >= 8.5:
            return "Academy Award Winner"
        elif rating >= 8.0:
            return "Golden Globe Winner"
        elif rating >= 7.5:
            return "Critics' Choice Award"
        else:
            return "Audience Choice Award"
            
    def _generate_box_office_fast(self, rating: float) -> str:
        """Fast box office generation"""
        revenue = int(rating * 50) if rating >= 7.0 else int(rating * 25)
        return f"${revenue}M worldwide"

    def _generate_budget_fast(self, rating: float, popularity: float) -> str:
        """Estimate production budget using rating and popularity"""
        # Higher popularity and rating generally indicate larger budgets
        base_budget = max(10, popularity / 2)
        quality_boost = 15 if rating >= 8.0 else 5 if rating >= 7.0 else 0
        estimated_budget = int(min(250, base_budget + quality_boost))
        return f"${estimated_budget}M"

# Global instance and convenience functions
_fast_loader = None

def get_fast_complete_database() -> List[Dict[str, Any]]:
    """Get complete MovieLens database using fast loader"""
    global _fast_loader
    if _fast_loader is None:
        _fast_loader = FastCompleteMovieLensLoader()
    return _fast_loader.get_fast_movie_database()

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    global _fast_loader
    if _fast_loader is None:
        _fast_loader = FastCompleteMovieLensLoader()
    
    summary = _fast_loader.load_dataset_summary()
    if summary:
        return {
            'total_movies': summary.get('movies', 10681),
            'total_ratings': summary.get('ratings', 10000054),
            'avg_rating': summary.get('average_rating', 3.51),
            'genres_available': len(summary.get('genres', [])),
            'year_range': {'min': 1915, 'max': 2008},
            'movies_with_posters': 16
        }
    else:
        return {
            'total_movies': 10681,
            'total_ratings': 10000054,
            'avg_rating': 3.51,
            'genres_available': 19,
            'year_range': {'min': 1915, 'max': 2008},
            'movies_with_posters': 16
        }

def get_recommendation_explanation(preferences: Dict[str, float], movie: Dict[str, Any], scores: Dict[str, float]) -> str:
    """Generate recommendation explanation"""
    explanation = f"Recommended '{movie['title']}' because:\n"
    
    # Genre matching
    user_genres = [genre for genre, score in preferences.items() if score >= 7]
    movie_genres = [g.lower().replace('-', '_') for g in movie.get('genres', [])]
    matching_genres = [g for g in user_genres if g in movie_genres]
    
    if matching_genres:
        explanation += f"• Matches your preferred genres: {', '.join(matching_genres)}\n"
    
    # Rating quality
    rating = movie.get('rating', 0)
    if rating >= 8.0:
        explanation += f"• High quality film with {rating:.1}/10 rating\n"
    elif rating >= 7.0:
        explanation += f"• Well-rated film with {rating:.1}/10 rating\n"
        
    # Recommendation scores
    hybrid_score = scores.get('hybrid', 0)
    if hybrid_score >= 8.5:
        explanation += f"• Excellent match (Score: {hybrid_score:.1f}/10)\n"
    elif hybrid_score >= 7.5:
        explanation += f"• Good match (Score: {hybrid_score:.1f}/10)\n"
        
    return explanation.strip()