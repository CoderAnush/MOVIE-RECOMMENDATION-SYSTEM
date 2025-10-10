"""
Optimize Movie Posters for Fast Loading
========================================
This script:
1. Downloads all posters locally
2. Optimizes and compresses images
3. Creates WebP versions for faster loading
4. Updates all references to use local files
"""

import requests
import json
from pathlib import Path
from PIL import Image
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PosterOptimizer:
    """Download and optimize posters for fast loading"""
    
    def __init__(self):
        self.poster_dir = Path("frontend/posters")
        self.poster_dir.mkdir(exist_ok=True, parents=True)
        
        self.stats = {
            'downloaded': 0,
            'cached': 0,
            'failed': 0,
            'optimized': 0
        }
    
    def _download_and_optimize(self, movie_id: int, poster_url: str) -> tuple:
        """Download and optimize a single poster"""
        
        if not poster_url or 'placeholder' in poster_url:
            return (movie_id, None, 'placeholder')
        
        filename = f"poster_{movie_id}.webp"
        filepath = self.poster_dir / filename
        
        # Check if already exists
        if filepath.exists():
            self.stats['cached'] += 1
            return (movie_id, f"/posters/{filename}", 'cached')
        
        try:
            # Download image
            response = requests.get(poster_url, timeout=10)
            response.raise_for_status()
            
            # Open and optimize with PIL
            img = Image.open(io.BytesIO(response.content))
            
            # Resize if too large (max width 300px)
            if img.width > 300:
                ratio = 300 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((300, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Save as WebP (better compression)
            img.save(filepath, 'WEBP', quality=85, method=6)
            
            self.stats['downloaded'] += 1
            self.stats['optimized'] += 1
            
            return (movie_id, f"/posters/{filename}", 'downloaded')
            
        except Exception as e:
            logger.debug(f"Failed to download poster {movie_id}: {e}")
            self.stats['failed'] += 1
            return (movie_id, None, 'failed')
    
    def optimize_all_posters(self, movies: list, max_workers: int = 20):
        """Download and optimize all posters"""
        
        logger.info(f"🎨 Optimizing {len(movies)} posters with {max_workers} workers")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._download_and_optimize,
                    movie['id'],
                    movie.get('poster_url') or movie.get('poster')
                ): movie['id']
                for movie in movies
            }
            
            with tqdm(total=len(futures), desc="🎨 Optimizing posters") as pbar:
                for future in as_completed(futures):
                    movie_id, local_path, status = future.result()
                    results[movie_id] = local_path
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        'Downloaded': self.stats['downloaded'],
                        'Cached': self.stats['cached'],
                        'Failed': self.stats['failed']
                    })
        
        return results
    
    def update_movies_with_local_paths(self, movies: list, local_paths: dict):
        """Update movie list with local poster paths"""
        for movie in movies:
            local_path = local_paths.get(movie['id'])
            if local_path:
                movie['poster'] = local_path
                movie['poster_url'] = local_path
            else:
                # Use placeholder
                movie['poster'] = "https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Poster"
                movie['poster_url'] = "https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Poster"
    
    def print_stats(self):
        """Print optimization statistics"""
        print("\n" + "="*60)
        print("📊 POSTER OPTIMIZATION STATISTICS")
        print("="*60)
        print(f"✅ Downloaded: {self.stats['downloaded']:,}")
        print(f"📦 Cached: {self.stats['cached']:,}")
        print(f"🎨 Optimized: {self.stats['optimized']:,}")
        print(f"❌ Failed: {self.stats['failed']:,}")
        print(f"💾 Saved to: {self.poster_dir}")
        print("="*60)


def main():
    """Main function"""
    
    print("🎨 Movie Poster Optimizer")
    print("="*60)
    print("✨ Downloads and optimizes all posters locally")
    print("⚡ WebP format for 70% smaller file sizes")
    print("🚀 Much faster loading in browser")
    print("="*60 + "\n")
    
    # Load movie data
    cache_file = Path("processed/fast_movie_posters.json")
    
    if not cache_file.exists():
        print("❌ Movie cache not found")
        return
    
    print(f"📂 Loading movies from {cache_file}")
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        movies = data.get('movies', [])
    
    print(f"✅ Loaded {len(movies):,} movies\n")
    
    # Count posters to download
    to_download = sum(1 for m in movies if m.get('poster_url') and 'placeholder' not in m.get('poster_url', ''))
    print(f"📊 Posters to process: {to_download:,}")
    print(f"⏱️ Estimated time: ~{to_download/20/60:.1f} minutes\n")
    
    confirm = input("🚀 Start optimization? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    print("\n" + "="*60)
    print("🔄 Starting poster optimization...")
    print("="*60 + "\n")
    
    # Optimize posters
    optimizer = PosterOptimizer()
    local_paths = optimizer.optimize_all_posters(movies, max_workers=20)
    
    # Update movies with local paths
    optimizer.update_movies_with_local_paths(movies, local_paths)
    
    # Save updated cache
    print("\n💾 Saving updated cache...")
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump({'movies': movies}, f, indent=2, ensure_ascii=False)
    
    # Print stats
    optimizer.print_stats()
    
    print("\n✅ DONE! Posters optimized for fast loading")
    print("\n🚀 Restart your system:")
    print("  python -m uvicorn api:app --host 127.0.0.1 --port 3000")


if __name__ == "__main__":
    main()
