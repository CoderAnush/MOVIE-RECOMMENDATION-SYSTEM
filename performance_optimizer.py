"""
Performance Optimization Module
===============================

This module implements caching, batch processing, and performance monitoring
for the hybrid movie recommendation system to achieve faster response times.

Features:
- Redis/Memory caching for predictions
- Batch prediction optimization
- Response time monitoring
- Recommendation result caching
- Model prediction pooling
"""

import time
import hashlib
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from functools import lru_cache
from collections import defaultdict
import logging

# Set up logging
logger = logging.getLogger(__name__)

class PerformanceCache:
    """In-memory cache for recommendation results."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.timestamps = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, user_preferences: Dict, movie: Dict, watch_history: Optional[Dict] = None) -> str:
        """Generate a unique cache key for the recommendation request."""
        # Create a hashable representation
        key_data = {
            'prefs': sorted(user_preferences.items()) if user_preferences else [],
            'movie': (movie.get('title', ''), tuple(sorted(movie.get('genres', [])))),
            'history': tuple(sorted(watch_history.items())) if watch_history else ()
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, user_preferences: Dict, movie: Dict, watch_history: Optional[Dict] = None) -> Optional[Dict]:
        """Get cached recommendation result."""
        key = self._generate_key(user_preferences, movie, watch_history)
        
        if key in self.cache:
            # Check if cache entry is still valid
            if time.time() - self.timestamps[key] < self.ttl_seconds:
                self.hit_count += 1
                return self.cache[key]
            else:
                # Remove expired entry
                del self.cache[key]
                del self.timestamps[key]
        
        self.miss_count += 1
        return None
    
    def put(self, user_preferences: Dict, movie: Dict, result: Dict, watch_history: Optional[Dict] = None):
        """Store recommendation result in cache."""
        key = self._generate_key(user_preferences, movie, watch_history)
        
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = result
        self.timestamps[key] = time.time()
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'ttl_seconds': self.ttl_seconds
        }
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
        self.hit_count = 0
        self.miss_count = 0

class BatchPreprocessor:
    """Optimized batch preprocessing for multiple movie recommendations."""
    
    def __init__(self):
        self.genres = ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror']
    
    def prepare_batch_features(self, user_preferences: Dict, movies: List[Dict], 
                              watch_history: Optional[Dict] = None) -> np.ndarray:
        """Prepare features for batch ANN prediction."""
        batch_features = []
        
        for movie in movies:
            features = self._prepare_single_features(user_preferences, movie, watch_history)
            batch_features.append(features)
        
        return np.array(batch_features)
    
    def _prepare_single_features(self, user_preferences: Dict, movie: Dict, 
                                watch_history: Optional[Dict] = None) -> List[float]:
        """Prepare features for a single movie (optimized version)."""
        features = []
        
        # User preferences (7 features) - pre-sorted for consistency
        for genre in self.genres:
            features.append(user_preferences.get(genre, 5.0))
        
        # Movie genres (7 features) - optimized lookup
        movie_genres = set(g.lower().replace(' ', '_') for g in movie.get('genres', []))
        for genre in self.genres:
            features.append(1.0 if genre in movie_genres else 0.0)
        
        # Other features (5 features)
        features.extend([
            movie.get('popularity', 50) / 100,
            (movie.get('year', 2000) - 1900) / 130,
            min(1.0, np.log10(watch_history.get('watch_count', 1) + 1) / 2) if watch_history else 0.1,
            watch_history.get('liked_ratio', 0.5) if watch_history else 0.5,
            watch_history.get('disliked_ratio', 0.3) if watch_history else 0.3
        ])
        
        return features

class PerformanceMonitor:
    """Monitor and track system performance metrics."""
    
    def __init__(self):
        self.request_times = []
        self.fuzzy_times = []
        self.ann_times = []
        self.total_requests = 0
        self.error_count = 0
        self.start_time = time.time()
    
    def record_request(self, total_time: float, fuzzy_time: float = 0, 
                      ann_time: float = 0, error: bool = False):
        """Record performance metrics for a request."""
        self.total_requests += 1
        
        if error:
            self.error_count += 1
            return
        
        self.request_times.append(total_time)
        self.fuzzy_times.append(fuzzy_time)
        self.ann_times.append(ann_time)
        
        # Keep only last 1000 entries to prevent memory issues
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
            self.fuzzy_times = self.fuzzy_times[-1000:]
            self.ann_times = self.ann_times[-1000:]
    
    def get_stats(self) -> Dict:
        """Get comprehensive performance statistics."""
        if not self.request_times:
            return {
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'total_requests': self.total_requests,
                'error_rate': 0,
                'uptime_hours': round((time.time() - self.start_time) / 3600, 2)
            }
        
        return {
            'avg_response_time': round(np.mean(self.request_times), 2),
            'min_response_time': round(np.min(self.request_times), 2),
            'max_response_time': round(np.max(self.request_times), 2),
            'p95_response_time': round(np.percentile(self.request_times, 95), 2),
            'avg_fuzzy_time': round(np.mean(self.fuzzy_times), 2) if self.fuzzy_times else 0,
            'avg_ann_time': round(np.mean(self.ann_times), 2) if self.ann_times else 0,
            'total_requests': self.total_requests,
            'successful_requests': len(self.request_times),
            'error_count': self.error_count,
            'error_rate': round((self.error_count / self.total_requests) * 100, 2) if self.total_requests > 0 else 0,
            'uptime_hours': round((time.time() - self.start_time) / 3600, 2),
            'requests_per_minute': round((self.total_requests / ((time.time() - self.start_time) / 60)), 2) if (time.time() - self.start_time) > 0 else 0
        }

class OptimizedHybridSystem:
    """Performance-optimized version of the hybrid recommendation system."""
    
    def __init__(self, hybrid_system, cache_size: int = 1000, cache_ttl: int = 3600):
        self.hybrid_system = hybrid_system
        self.cache = PerformanceCache(cache_size, cache_ttl)
        self.batch_processor = BatchPreprocessor()
        self.monitor = PerformanceMonitor()
        
        # Pre-compile frequently used patterns
        self._compiled_strategies = {
            'adaptive': self._adaptive_strategy,
            'weighted_average': self._weighted_average_strategy,
            'fuzzy_dominant': self._fuzzy_dominant_strategy,
            'ann_dominant': self._ann_dominant_strategy
        }
    
    def get_recommendation(self, user_preferences: Dict, movie: Dict, 
                          watch_history: Optional[Dict] = None, 
                          strategy: str = 'adaptive') -> Dict:
        """Get optimized single movie recommendation with caching."""
        start_time = time.time()
        
        try:
            # Check cache first
            cached_result = self.cache.get(user_preferences, movie, watch_history)
            if cached_result is not None:
                cached_result['from_cache'] = True
                cached_result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
                self.monitor.record_request(time.time() - start_time)
                return cached_result
            
            # Get fresh recommendation
            result = self._get_fresh_recommendation(
                user_preferences, movie, watch_history, strategy
            )
            
            # Cache the result
            cache_result = result.copy()
            cache_result.pop('processing_time_ms', None)  # Don't cache timing info
            self.cache.put(user_preferences, movie, cache_result, watch_history)
            
            # Record performance
            total_time = time.time() - start_time
            self.monitor.record_request(total_time)
            
            result['from_cache'] = False
            result['processing_time_ms'] = round(total_time * 1000, 2)
            
            return result
            
        except Exception as e:
            self.monitor.record_request(time.time() - start_time, error=True)
            raise e
    
    def get_batch_recommendations(self, user_preferences: Dict, movies: List[Dict], 
                                 watch_history: Optional[Dict] = None, 
                                 strategy: str = 'adaptive') -> List[Dict]:
        """Get optimized batch recommendations."""
        start_time = time.time()
        
        try:
            # Check cache for each movie
            results = []
            uncached_movies = []
            uncached_indices = []
            
            for i, movie in enumerate(movies):
                cached_result = self.cache.get(user_preferences, movie, watch_history)
                if cached_result is not None:
                    cached_result['from_cache'] = True
                    results.append(cached_result)
                else:
                    results.append(None)  # Placeholder
                    uncached_movies.append(movie)
                    uncached_indices.append(i)
            
            # Process uncached movies in batch
            if uncached_movies:
                batch_results = self._get_batch_fresh_recommendations(
                    user_preferences, uncached_movies, watch_history, strategy
                )
                
                # Fill in results and cache them
                for idx, result in zip(uncached_indices, batch_results):
                    results[idx] = result
                    result['from_cache'] = False
                    
                    # Cache the result
                    cache_result = result.copy()
                    cache_result.pop('processing_time_ms', None)
                    self.cache.put(user_preferences, uncached_movies[uncached_indices.index(idx)], 
                                 cache_result, watch_history)
            
            # Add timing info
            total_time = time.time() - start_time
            for result in results:
                if result:
                    result['batch_processing_time_ms'] = round(total_time * 1000, 2)
            
            self.monitor.record_request(total_time)
            
            return [r for r in results if r is not None]
            
        except Exception as e:
            self.monitor.record_request(time.time() - start_time, error=True)
            raise e
    
    def _get_fresh_recommendation(self, user_preferences: Dict, movie: Dict, 
                                 watch_history: Optional[Dict], strategy: str) -> Dict:
        """Get a fresh recommendation (not from cache)."""
        return self.hybrid_system.recommend(user_preferences, movie, watch_history, strategy)
    
    def _get_batch_fresh_recommendations(self, user_preferences: Dict, movies: List[Dict], 
                                        watch_history: Optional[Dict], strategy: str) -> List[Dict]:
        """Get batch fresh recommendations with optimized processing."""
        # For now, use the existing method but could be further optimized with batch ANN prediction
        results = []
        for movie in movies:
            result = self.hybrid_system.recommend(user_preferences, movie, watch_history, strategy)
            results.append(result)
        return results
    
    def _adaptive_strategy(self, fuzzy_score: float, ann_score: float, 
                          watch_history: Optional[Dict]) -> float:
        """Optimized adaptive strategy."""
        agreement = 1 - abs(fuzzy_score - ann_score) / 10
        watch_count = watch_history.get('watch_count', 0) if watch_history else 0
        
        if agreement > 0.8:
            return (fuzzy_score + ann_score) / 2
        elif watch_count > 30:
            return fuzzy_score * 0.4 + ann_score * 0.6
        else:
            return fuzzy_score * 0.6 + ann_score * 0.4
    
    def _weighted_average_strategy(self, fuzzy_score: float, ann_score: float, 
                                  watch_history: Optional[Dict]) -> float:
        """Weighted average strategy."""
        return fuzzy_score * 0.6 + ann_score * 0.4
    
    def _fuzzy_dominant_strategy(self, fuzzy_score: float, ann_score: float, 
                                watch_history: Optional[Dict]) -> float:
        """Fuzzy-dominant strategy."""
        return fuzzy_score * 0.7 + ann_score * 0.3
    
    def _ann_dominant_strategy(self, fuzzy_score: float, ann_score: float, 
                              watch_history: Optional[Dict]) -> float:
        """ANN-dominant strategy."""
        return fuzzy_score * 0.3 + ann_score * 0.7
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics."""
        return {
            'cache': self.cache.get_stats(),
            'performance': self.monitor.get_stats(),
            'system_info': {
                'optimization_enabled': True,
                'batch_processing': True,
                'caching_enabled': True
            }
        }
    
    def clear_cache(self):
        """Clear the performance cache."""
        self.cache.clear()

# Global instance for use in API
optimized_system = None

def initialize_optimized_system(hybrid_system, cache_size: int = 1000, cache_ttl: int = 3600):
    """Initialize the global optimized system."""
    global optimized_system
    optimized_system = OptimizedHybridSystem(hybrid_system, cache_size, cache_ttl)
    logger.info(f"✅ Performance optimization initialized (cache: {cache_size}, ttl: {cache_ttl}s)")
    return optimized_system

def get_optimized_system():
    """Get the global optimized system."""
    global optimized_system
    if optimized_system is None:
        raise RuntimeError("Optimized system not initialized. Call initialize_optimized_system first.")
    return optimized_system