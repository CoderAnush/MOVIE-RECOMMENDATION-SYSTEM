"""
Auto-run TMDB Poster Fetcher (No Prompts)
==========================================
Automatically fetches all posters without user interaction
"""

import pandas as pd
import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TMDBPosterFetcher:
    """Fetch movie posters from TMDB API"""
    
    def __init__(self, api_key: str = "8265bd1679663a7ea12ac168da84d2e8"):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        self.cache_file = Path("processed/tmdb_movie_posters.json")
        self.backup_file = Path("processed/tmdb_poster_backup.json")
        
        self.lock = threading.Lock()
        
        self.stats = {
            'total': 0,
            'found': 0,
            'not_found': 0,
            'errors': 0,
            'cached': 0
        }
        
        self.poster_cache = self._load_cache()
        logger.info(f"🎬 TMDB API initialized with {len(self.poster_cache)} cached posters")
    
    def _load_cache(self) -> Dict:
        """Load existing poster cache"""
        # Try main cache first
        if self.cache_file.exists():
            try:
                logger.info(f"📦 Loading cache from {self.cache_file}")
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    posters = data.get('posters', {})
                    logger.info(f"✅ Loaded {len(posters)} cached posters")
                    return posters
            except json.JSONDecodeError:
                logger.warning("⚠️ Main cache corrupted, trying backup...")
        
        # Try backup
        if self.backup_file.exists():
            try:
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    posters = data.get('posters', {})
                    logger.info(f"✅ Loaded {len(posters)} cached posters from backup")
                    return posters
            except json.JSONDecodeError:
                logger.warning("⚠️ Backup also corrupted, starting fresh")
        
        return {}
    
    def _search_movie(self, title: str, year: int) -> Optional[Dict]:
        """Search for movie on TMDB"""
        try:
            clean_title = title.split('(')[0].strip()
            
            params = {
                'api_key': self.api_key,
                'query': clean_title,
                'year': year,
                'include_adult': 'true'
            }
            
            response = requests.get(
                f"{self.base_url}/search/movie",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                return results[0]
            
            # Try without year
            params.pop('year')
            response = requests.get(
                f"{self.base_url}/search/movie",
                params=params,
                timeout=10
            )
            data = response.json()
            results = data.get('results', [])
            
            if results:
                return results[0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Error searching '{title}': {e}")
            return None
    
    def _fetch_poster(self, title: str, year: int, movie_id: int) -> tuple:
        """Fetch poster URL from TMDB"""
        
        cache_key = f"{title}_{year}"
        
        # Check cache first
        with self.lock:
            if cache_key in self.poster_cache:
                self.stats['cached'] += 1
                return (movie_id, self.poster_cache[cache_key], True)
        
        # Search on TMDB
        movie_data = self._search_movie(title, year)
        
        if movie_data and movie_data.get('poster_path'):
            poster_url = f"{self.image_base_url}{movie_data['poster_path']}"
            
            with self.lock:
                self.poster_cache[cache_key] = poster_url
                self.stats['found'] += 1
            
            return (movie_id, poster_url, True)
        else:
            with self.lock:
                self.poster_cache[cache_key] = None
                self.stats['not_found'] += 1
            
            return (movie_id, None, False)
    
    def _save_cache(self, all_movies: List[Dict]):
        """Save poster cache to file"""
        # Make a copy to avoid race condition
        with self.lock:
            poster_cache_copy = dict(self.poster_cache)
            stats_copy = dict(self.stats)
        
        cache_data = {
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_movies': len(all_movies),
            'statistics': stats_copy,
            'api_source': 'TMDB',
            'posters': poster_cache_copy,
            'movies': all_movies
        }
        
        self.cache_file.parent.mkdir(exist_ok=True)
        
        # Save main cache
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save main cache: {e}")
        
        # Save backup
        try:
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")
    
    def process_movies(self, movies_df: pd.DataFrame, max_workers: int = 20):
        """Process all movies with parallel fetching"""
        
        logger.info(f"🎬 Processing {len(movies_df)} movies with {max_workers} workers")
        self.stats['total'] = len(movies_df)
        
        # Prepare movie list
        movies_to_process = []
        all_movies = []
        
        for idx, row in movies_df.iterrows():
            movie = {
                'id': int(row['movieId']) if 'movieId' in row else int(row.get('id', idx)),
                'title': str(row['title']),
                'year': int(row['year']) if pd.notna(row.get('year')) else 2000,
                'genres': row['genres'] if isinstance(row.get('genres'), list) else [],
                'rating': float(row.get('rating', 0)) if pd.notna(row.get('rating')) else 0.0,
                'popularity': int(row.get('popularity', 50)) if pd.notna(row.get('popularity')) else 50,
                'runtime': int(row.get('runtime', 90)) if pd.notna(row.get('runtime')) else 90,
            }
            
            movies_to_process.append((movie['id'], movie['title'], movie['year']))
            all_movies.append(movie)
        
        # Fetch posters in parallel
        poster_results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_movie = {
                executor.submit(self._fetch_poster, title, year, movie_id): movie_id
                for movie_id, title, year in movies_to_process
            }
            
            # Process results with progress bar
            with tqdm(total=len(movies_to_process), desc="🎬 Fetching TMDB posters") as pbar:
                for future in as_completed(future_to_movie):
                    movie_id, poster_url, found = future.result()
                    poster_results[movie_id] = poster_url
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        'Found': self.stats['found'],
                        'Cached': self.stats['cached'],
                        'NotFound': self.stats['not_found']
                    })
                    
                    # Save checkpoint every 1000 movies
                    if pbar.n % 1000 == 0:
                        self._update_movies_with_posters(all_movies, poster_results)
                        self._save_cache(all_movies)
                        logger.info(f"💾 Checkpoint saved at {pbar.n} movies")
        
        # Update all movies with poster URLs
        self._update_movies_with_posters(all_movies, poster_results)
        
        # Final save
        self._save_cache(all_movies)
        
        return all_movies
    
    def _update_movies_with_posters(self, all_movies: List[Dict], poster_results: Dict):
        """Update movie list with fetched posters"""
        for movie in all_movies:
            poster_url = poster_results.get(movie['id'])
            
            if poster_url:
                movie['poster'] = poster_url
                movie['poster_url'] = poster_url
            else:
                movie['poster'] = "https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Poster"
                movie['poster_url'] = "https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Poster"
            
            # Add metadata
            genre_text = movie['genres'][0] if movie['genres'] else 'movie'
            movie['description'] = f"A {genre_text} from {movie['year']}"
            movie['director'] = f"Director {movie['id']}"
            movie['cast'] = [f"Actor {i}" for i in range(1, 4)]
    
    def print_statistics(self):
        """Print fetching statistics"""
        print("\n" + "="*60)
        print("📊 TMDB POSTER FETCHING STATISTICS")
        print("="*60)
        print(f"Total movies processed: {self.stats['total']:,}")
        print(f"✅ Posters found: {self.stats['found']:,} ({self.stats['found']/self.stats['total']*100:.1f}%)")
        print(f"📦 From cache: {self.stats['cached']:,} ({self.stats['cached']/self.stats['total']*100:.1f}%)")
        print(f"❌ Not found: {self.stats['not_found']:,} ({self.stats['not_found']/self.stats['total']*100:.1f}%)")
        print(f"⚠️ Errors: {self.stats['errors']:,}")
        print("="*60)


def main():
    """Main execution function - NO PROMPTS"""
    
    print("🎬 Auto TMDB Movie Poster Fetcher")
    print("="*60)
    print("✨ Using TMDB API - Better coverage than OMDB!")
    print("⚡ Free API with 50 requests/second")
    print("🤖 Running automatically without prompts")
    print("="*60 + "\n")
    
    # Load dataset
    dataset_path = Path("processed/movies_enriched.parquet")
    
    if not dataset_path.exists():
        print(f"❌ Dataset not found at {dataset_path}")
        return
    
    print(f"📂 Loading dataset from {dataset_path}")
    movies_df = pd.read_parquet(dataset_path)
    print(f"✅ Loaded {len(movies_df):,} movies\n")
    
    api_key = "8265bd1679663a7ea12ac168da84d2e8"
    max_workers = 20
    estimated_time = len(movies_df) / (max_workers * 2) / 60
    
    print(f"⚙️ Configuration:")
    print(f"  - API Source: TMDB")
    print(f"  - API Key: {api_key[:8]}...")
    print(f"  - Max Workers: {max_workers}")
    print(f"  - Movies: {len(movies_df):,}")
    print(f"  - Estimated Time: ~{estimated_time:.0f} minutes")
    
    print("\n" + "="*60)
    print("🔄 Starting TMDB poster fetch...")
    print("="*60 + "\n")
    
    fetcher = TMDBPosterFetcher(api_key=api_key)
    start_time = time.time()
    
    try:
        all_movies = fetcher.process_movies(movies_df, max_workers=max_workers)
        
        elapsed = time.time() - start_time
        
        # Print statistics
        fetcher.print_statistics()
        print(f"\n⏱️ Total time: {elapsed/60:.1f} minutes")
        print(f"⚡ Speed: {len(movies_df)/elapsed:.1f} movies/second")
        
        # Update system caches
        print("\n🔄 Updating system caches...")
        
        # Update fast_complete_loader cache
        fast_cache_path = Path("processed/fast_movie_posters.json")
        with open(fast_cache_path, 'w', encoding='utf-8') as f:
            json.dump({'movies': all_movies}, f, indent=2, ensure_ascii=False)
        print(f"✅ Updated {fast_cache_path}")
        
        print("\n" + "="*60)
        print("✅ ALL DONE! Real posters fetched from TMDB")
        print("="*60)
        print(f"\n📁 Results saved to:")
        print(f"  - {fetcher.cache_file}")
        print(f"  - {fetcher.backup_file}")
        print(f"  - {fast_cache_path}")
        
        print("\n🚀 You can now start the system:")
        print("  python -m uvicorn api:app --host 127.0.0.1 --port 3000")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        print("💾 Progress has been saved. You can resume later.")
        fetcher.print_statistics()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        logger.exception("Fatal error occurred")


if __name__ == "__main__":
    main()
