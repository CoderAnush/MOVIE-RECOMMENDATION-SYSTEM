#!/usr/bin/env python3
"""
Enhanced Recommendation Engine with Real Scoring
===============================================
Advanced recommendation system with multiple algorithms and real scoring
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

def safe_float(value, default=0.0):
    """Safely convert a value to float"""
    try:
        return float(value) if value not in (None, '', 'N/A') else default
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Safely convert a value to int"""
    try:
        return int(value) if value not in (None, '', 'N/A') else default
    except (ValueError, TypeError):
        return default

class EnhancedRecommendationEngine:
    """Advanced movie recommendation engine with multiple algorithms"""
    
    def __init__(self, movies_db_path="real_movies_complete_db.py"):
        self.movies_db_path = movies_db_path
        self.movies = []
        self.genre_preferences = {}
        self.user_history = []
        self.recommendation_cache = {}
        
        # Load movies database
        self.load_movies_database()
        
        # Initialize recommendation algorithms
        self.initialize_algorithms()
    
    def load_movies_database(self):
        """Load the complete movies database"""
        try:
            from fast_complete_loader import get_fast_complete_database
            self.movies = get_fast_complete_database()
            logger.info(f"🚀 Loaded fast complete MovieLens 10M database: {len(self.movies)} movies")
        except Exception as e:
            logger.error(f"Error loading fast complete database: {e}")
            try:
                # Fallback to enhanced demo database
                from real_movies_enhanced_demo import REAL_MOVIES_DATABASE
                self.movies = REAL_MOVIES_DATABASE
                logger.warning(f"Using enhanced demo database with {len(self.movies)} movies")
            except ImportError:
                # Final fallback to OMDB database
                from real_movies_db_omdb import REAL_MOVIES_DATABASE
                self.movies = REAL_MOVIES_DATABASE
                logger.warning(f"Using fallback database with {len(self.movies)} movies")
        except Exception as e:
            logger.error(f"Error loading movies database: {e}")
            self.movies = []
    
    def initialize_algorithms(self):
        """Initialize various recommendation algorithms"""
        self.algorithms = {
            'content_based': self.content_based_filtering,
            'popularity_based': self.popularity_based_filtering,
            'genre_matching': self.genre_matching_algorithm,
            'hybrid_scoring': self.hybrid_scoring_algorithm,
            'advanced_similarity': self.advanced_similarity_algorithm
        }
    
    def content_based_filtering(self, user_prefs: Dict[str, float], num_recommendations: int = 10) -> List[Dict]:
        """Advanced content-based filtering with multiple factors"""
        recommendations = []
        
        for movie in self.movies:
            score = self.calculate_content_score(user_prefs, movie)
            
            # Higher threshold - only recommend well-matching movies
            if score > 0.5:  # Increased from 0.3 to filter better
                movie_copy = movie.copy()
                movie_copy['prediction_score'] = score
                movie_copy['confidence'] = self.calculate_confidence(user_prefs, movie)
                movie_copy['algorithm'] = 'Content-Based'
                recommendations.append(movie_copy)
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['prediction_score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def calculate_content_score(self, user_prefs: Dict[str, float], movie: Dict) -> float:
        """Calculate detailed content-based score"""
        score_components = {}
        
        # 1. Genre matching (40% weight)
        genre_score = self.calculate_genre_score(user_prefs, movie)
        score_components['genre'] = genre_score * 0.4
        
        # 2. Quality indicators (25% weight) 
        quality_score = self.calculate_quality_score(movie)
        score_components['quality'] = quality_score * 0.25
        
        # 3. Popularity factor (20% weight)
        popularity_score = safe_float(movie.get('popularity', 50), 50.0) / 100.0
        score_components['popularity'] = popularity_score * 0.2
        
        # 4. Recency factor (15% weight)
        recency_score = self.calculate_recency_score(movie)
        score_components['recency'] = recency_score * 0.15
        
        # Store breakdown for explanations
        movie['score_breakdown'] = score_components
        
        return sum(score_components.values())
    
    def calculate_genre_score(self, user_prefs: Dict[str, float], movie: Dict) -> float:
        """Calculate genre matching score with strict preference filtering"""
        movie_genres = [g.lower().replace('-', '_').replace(' ', '_') for g in movie.get('genres', [])]
        
        if not movie_genres:
            return 0.0  # Reject movies without genre info
        
        # Get user's high preferences (>= 7) and dislikes (< 4)
        high_prefs = {k: v for k, v in user_prefs.items() if v >= 7.0}
        dislikes = {k: v for k, v in user_prefs.items() if v < 4.0}
        
        # Check if movie has any disliked genres - penalize heavily
        for disliked_genre, score in dislikes.items():
            disliked_clean = disliked_genre.lower().replace('_', '').replace('-', '')
            for movie_genre in movie_genres:
                movie_genre_clean = movie_genre.replace('_', '').replace('-', '')
                if disliked_clean in movie_genre_clean or movie_genre_clean in disliked_clean:
                    # Strong penalty for disliked genres
                    return 0.1 * (score / 10.0)  # Very low score
        
        # Calculate weighted genre match focusing on high preferences
        total_weight = 0
        weighted_sum = 0
        has_strong_match = False
        
        for pref_genre, pref_score in user_prefs.items():
            pref_genre_clean = pref_genre.lower().replace('_', '').replace('-', '')
            
            # Check for exact and partial matches
            match_strength = 0
            for movie_genre in movie_genres:
                movie_genre_clean = movie_genre.replace('_', '').replace('-', '')
                
                if pref_genre_clean == movie_genre_clean:
                    match_strength = 1.0  # Perfect match
                    if pref_score >= 7.0:
                        has_strong_match = True
                    break
                elif pref_genre_clean in movie_genre_clean or movie_genre_clean in pref_genre_clean:
                    match_strength = max(match_strength, 0.7)  # Partial match
                    if pref_score >= 7.0:
                        has_strong_match = True
            
            if match_strength > 0:
                weighted_sum += (pref_score / 10.0) * match_strength
                total_weight += pref_score / 10.0
        
        # If user has high preferences but movie doesn't match any, return very low score
        if high_prefs and not has_strong_match:
            return 0.2
        
        return weighted_sum / total_weight if total_weight > 0 else 0.1
    
    def calculate_quality_score(self, movie: Dict) -> float:
        """Calculate movie quality score based on multiple indicators"""
        quality_factors = []
        
        # Rating factor
        rating = safe_float(movie.get('rating', 7.0), 7.0)
        rating_score = min(rating / 10.0, 1.0)
        quality_factors.append(rating_score)
        
        # Awards factor
        awards = movie.get('awards', '').lower()
        if 'academy award' in awards or 'oscar' in awards:
            quality_factors.append(1.0)
        elif 'golden globe' in awards:
            quality_factors.append(0.8)
        elif 'festival' in awards or 'nominated' in awards:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.4)
        
        # Box office factor (normalized)
        box_office = movie.get('box_office', '')
        if isinstance(box_office, str) and '$' in box_office:
            try:
                amount = float(box_office.replace('$', '').replace('M', '').replace(',', ''))
                if amount >= 200:
                    quality_factors.append(0.9)
                elif amount >= 100:
                    quality_factors.append(0.7)
                elif amount >= 50:
                    quality_factors.append(0.5)
                else:
                    quality_factors.append(0.3)
            except:
                quality_factors.append(0.4)
        else:
            quality_factors.append(0.4)
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
    
    def calculate_recency_score(self, movie: Dict) -> float:
        """Calculate recency score favoring newer movies slightly"""
        year = safe_int(movie.get('year', 2000), 2000)
        current_year = datetime.now().year
        
        if year >= current_year - 5:  # Last 5 years
            return 1.0
        elif year >= current_year - 10:  # 5-10 years ago
            return 0.8
        elif year >= current_year - 20:  # 10-20 years ago
            return 0.6
        elif year >= current_year - 40:  # 20-40 years ago
            return 0.5
        else:  # Older than 40 years
            return 0.3
    
    def popularity_based_filtering(self, user_prefs: Dict[str, float], num_recommendations: int = 10) -> List[Dict]:
        """Popularity-based recommendations with user preference weighting"""
        recommendations = []
        
        for movie in self.movies:
            # Base popularity score (ensure numeric)
            popularity = safe_float(movie.get('popularity', 50), 50.0)
            rating = safe_float(movie.get('rating', 7.0), 7.0)
            
            # Genre alignment factor
            genre_alignment = self.calculate_genre_score(user_prefs, movie)
            
            # Combined score
            score = (popularity * 0.4 + rating * 6.0 + genre_alignment * 10.0) / 20.0
            
            # Higher threshold and require good genre match
            if score > 0.5 and genre_alignment > 0.4:  # Stricter filtering
                movie_copy = movie.copy()
                movie_copy['prediction_score'] = score
                movie_copy['confidence'] = min(0.9, popularity / 100.0 + 0.1)
                movie_copy['algorithm'] = 'Popularity-Based'
                recommendations.append(movie_copy)
        
        recommendations.sort(key=lambda x: x['prediction_score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def genre_matching_algorithm(self, user_prefs: Dict[str, float], num_recommendations: int = 10) -> List[Dict]:
        """Pure genre-based matching with sophisticated scoring"""
        recommendations = []
        
        # Get user's preferred genres (score >= 7) and dislikes (< 4)
        preferred_genres = {k: v for k, v in user_prefs.items() if v >= 7.0}
        disliked_genres = {k: v for k, v in user_prefs.items() if v < 4.0}
        
        if not preferred_genres:
            return self.popularity_based_filtering(user_prefs, num_recommendations)
        
        for movie in self.movies:
            # Skip movies with disliked genres
            movie_genres = [g.lower().replace('-', '_').replace(' ', '_') for g in movie.get('genres', [])]
            has_disliked = False
            
            for disliked in disliked_genres.keys():
                disliked_clean = disliked.lower().replace('_', '').replace('-', '')
                for mg in movie_genres:
                    if disliked_clean in mg.replace('_', '').replace('-', ''):
                        has_disliked = True
                        break
                if has_disliked:
                    break
            
            if has_disliked:
                continue  # Skip this movie entirely
            
            # Calculate genre match precision - must match preferred genres
            genre_score = self.calculate_advanced_genre_match(preferred_genres, movie)
            
            # Only recommend if there's a strong genre match
            if genre_score > 0.6:  # Increased threshold from 0.5
                # Boost score with movie quality
                quality_boost = self.calculate_quality_score(movie) * 0.3
                final_score = genre_score + quality_boost
                
                movie_copy = movie.copy()
                movie_copy['prediction_score'] = min(1.0, final_score)
                movie_copy['confidence'] = genre_score
                movie_copy['algorithm'] = 'Genre-Matching'
                recommendations.append(movie_copy)
        
        recommendations.sort(key=lambda x: x['prediction_score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def calculate_advanced_genre_match(self, preferred_genres: Dict[str, float], movie: Dict) -> float:
        """Advanced genre matching with semantic understanding"""
        movie_genres = [g.lower().replace('-', '_').replace(' ', '_') for g in movie.get('genres', [])]
        
        if not movie_genres:
            return 0.0
        
        # Genre similarity mapping for semantic matching
        genre_similarity = {
            'action': ['adventure', 'thriller', 'crime'],
            'comedy': ['romance', 'family', 'animation'],
            'drama': ['romance', 'biography', 'history'],
            'thriller': ['action', 'crime', 'mystery'],
            'sci_fi': ['fantasy', 'adventure', 'action'],
            'horror': ['thriller', 'mystery', 'supernatural'],
            'romance': ['drama', 'comedy', 'family'],
            'adventure': ['action', 'fantasy', 'family']
        }
        
        total_score = 0
        max_possible_score = 0
        
        for pref_genre, pref_value in preferred_genres.items():
            pref_genre_clean = pref_genre.lower()
            max_possible_score += pref_value
            
            # Direct match
            if pref_genre_clean in movie_genres:
                total_score += pref_value
            else:
                # Semantic similarity match
                similar_genres = genre_similarity.get(pref_genre_clean, [])
                for movie_genre in movie_genres:
                    if movie_genre in similar_genres:
                        total_score += pref_value * 0.6  # 60% score for similar genres
                        break
        
        return total_score / max_possible_score if max_possible_score > 0 else 0.0
    
    def hybrid_scoring_algorithm(self, user_prefs: Dict[str, float], num_recommendations: int = 10) -> List[Dict]:
        """Hybrid algorithm combining multiple recommendation strategies"""
        
        # Get recommendations from different algorithms
        content_recs = self.content_based_filtering(user_prefs, num_recommendations * 2)
        popularity_recs = self.popularity_based_filtering(user_prefs, num_recommendations * 2)
        genre_recs = self.genre_matching_algorithm(user_prefs, num_recommendations * 2)
        
        # Combine and re-score
        all_movies = {}
        
        # Weight different algorithms
        algorithm_weights = {
            'Content-Based': 0.4,
            'Popularity-Based': 0.3,
            'Genre-Matching': 0.3
        }
        
        for recs, weight in [(content_recs, 0.4), (popularity_recs, 0.3), (genre_recs, 0.3)]:
            for movie in recs:
                movie_id = movie['id']
                
                if movie_id not in all_movies:
                    all_movies[movie_id] = movie.copy()
                    all_movies[movie_id]['hybrid_score'] = 0
                    all_movies[movie_id]['algorithm_votes'] = []
                
                # Add weighted score
                all_movies[movie_id]['hybrid_score'] += movie['prediction_score'] * weight
                all_movies[movie_id]['algorithm_votes'].append(movie['algorithm'])
        
        # Convert to list and add final scores
        hybrid_recommendations = []
        for movie in all_movies.values():
            # Boost movies recommended by multiple algorithms
            algorithm_count = len(set(movie['algorithm_votes']))
            consensus_boost = (algorithm_count - 1) * 0.1
            
            # Add small random factor for diversity (0-0.05)
            import random
            diversity_factor = random.uniform(0, 0.05)
            
            movie['prediction_score'] = min(1.0, movie['hybrid_score'] + consensus_boost + diversity_factor)
            movie['confidence'] = min(0.95, algorithm_count / 3.0 + 0.3)
            movie['algorithm'] = 'Hybrid (Multi-Algorithm)'
            
            hybrid_recommendations.append(movie)
        
        # Sort by score with some randomness for variety
        hybrid_recommendations.sort(key=lambda x: (x['prediction_score'], random.random()), reverse=True)
        return hybrid_recommendations[:num_recommendations]
    
    def advanced_similarity_algorithm(self, user_prefs: Dict[str, float], num_recommendations: int = 10) -> List[Dict]:
        """Advanced similarity-based recommendations using movie features"""
        recommendations = []
        
        # Create feature vectors for movies
        for movie in self.movies:
            feature_vector = self.create_movie_feature_vector(movie)
            user_vector = self.create_user_feature_vector(user_prefs)
            
            # Calculate cosine similarity
            similarity = self.cosine_similarity(user_vector, feature_vector)
            
            if similarity > 0.2:
                movie_copy = movie.copy()
                movie_copy['prediction_score'] = similarity
                movie_copy['confidence'] = similarity * 0.9
                movie_copy['algorithm'] = 'Similarity-Based'
                recommendations.append(movie_copy)
        
        recommendations.sort(key=lambda x: x['prediction_score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def create_movie_feature_vector(self, movie: Dict) -> np.ndarray:
        """Create a feature vector for a movie"""
        features = []
        
        # Genre features (one-hot encoding for main genres)
        main_genres = ['action', 'comedy', 'drama', 'romance', 'thriller', 'sci-fi', 'horror', 'adventure']
        movie_genres = [g.lower().replace('-', '_').replace(' ', '_') for g in movie.get('genres', [])]
        
        for genre in main_genres:
            features.append(1.0 if genre in movie_genres else 0.0)
        
        # Numerical features (normalized)
        features.append(movie.get('rating', 7.0) / 10.0)  # Rating
        features.append(movie.get('popularity', 50) / 100.0)  # Popularity
        features.append(min(movie.get('year', 2000) / 2024.0, 1.0))  # Year (normalized)
        
        # Runtime feature
        runtime = movie.get('runtime', 120)
        if isinstance(runtime, (int, float)):
            features.append(min(runtime / 180.0, 1.0))  # Runtime normalized to 3 hours max
        else:
            features.append(0.67)  # Average runtime
        
        return np.array(features)
    
    def create_user_feature_vector(self, user_prefs: Dict[str, float]) -> np.ndarray:
        """Create a feature vector for user preferences"""
        features = []
        
        # Genre preferences
        main_genres = ['action', 'comedy', 'drama', 'romance', 'thriller', 'sci_fi', 'horror', 'adventure']
        
        for genre in main_genres:
            pref_value = user_prefs.get(genre, 5.0) / 10.0
            features.append(pref_value)
        
        # Additional user preference features
        avg_pref = sum(user_prefs.values()) / len(user_prefs) if user_prefs else 5.0
        features.extend([
            avg_pref / 10.0,  # Average preference
            0.8,  # Popularity preference (default high)
            0.7,  # Recency preference (default medium-high)
            0.67   # Runtime preference (default average)
        ])
        
        return np.array(features)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def calculate_confidence(self, user_prefs: Dict[str, float], movie: Dict) -> float:
        """Calculate recommendation confidence based on various factors"""
        confidence_factors = []
        
        # Genre match confidence
        genre_score = self.calculate_genre_score(user_prefs, movie)
        confidence_factors.append(genre_score)
        
        # Quality confidence (higher rated movies = more confident)
        rating = movie.get('rating', 7.0)
        if isinstance(rating, (int, float)):
            rating_confidence = min(rating / 10.0, 1.0)
            confidence_factors.append(rating_confidence)
        
        # Popularity confidence
        popularity = movie.get('popularity', 50)
        popularity_confidence = min(popularity / 100.0, 0.9)
        confidence_factors.append(popularity_confidence)
        
        # Data completeness confidence
        data_completeness = 0.5  # Base
        if movie.get('description'):
            data_completeness += 0.1
        if movie.get('director'):
            data_completeness += 0.1
        if movie.get('cast'):
            data_completeness += 0.1
        if movie.get('awards'):
            data_completeness += 0.1
        if movie.get('poster'):
            data_completeness += 0.1
        
        confidence_factors.append(data_completeness)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def get_recommendations(self, user_prefs: Dict[str, float], algorithm: str = 'hybrid', 
                          num_recommendations: int = 10) -> List[Dict]:
        """Get recommendations using specified algorithm"""
        
        if algorithm not in self.algorithms:
            algorithm = 'hybrid_scoring'  # Default to hybrid
        
        try:
            recommendations = self.algorithms[algorithm](user_prefs, num_recommendations)
            
            # Add enhanced explanations
            for rec in recommendations:
                rec['explanation'] = self.generate_explanation(user_prefs, rec)
                rec['recommendation_timestamp'] = datetime.now().isoformat()
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations with {algorithm}: {e}")
            # Fallback to simple content-based
            return self.content_based_filtering(user_prefs, num_recommendations)
    
    def generate_explanation(self, user_prefs: Dict[str, float], movie: Dict) -> str:
        """Generate detailed recommendation explanation"""
        explanations = []
        
        # Algorithm explanation
        algorithm = movie.get('algorithm', 'Unknown')
        explanations.append(f"🤖 {algorithm} recommendation")
        
        # Score breakdown if available
        if 'score_breakdown' in movie:
            breakdown = movie['score_breakdown']
            top_factor = max(breakdown.items(), key=lambda x: x[1])
            explanations.append(f"📊 Top factor: {top_factor[0].title()} ({top_factor[1]:.2f})")
        
        # Confidence level
        confidence = movie.get('confidence', 0.5)
        if confidence >= 0.8:
            explanations.append(f"🎯 High confidence ({confidence*100:.0f}%)")
        elif confidence >= 0.6:
            explanations.append(f"👍 Good match ({confidence*100:.0f}%)")
        else:
            explanations.append(f"🤔 Moderate confidence ({confidence*100:.0f}%)")
        
        # Genre matching
        user_genres = {k: v for k, v in user_prefs.items() if v >= 7}
        movie_genres = movie.get('genres', [])
        matching_genres = []
        
        for genre in movie_genres:
            genre_key = genre.lower().replace('-', '_').replace(' ', '_')
            if genre_key in user_genres:
                matching_genres.append(f"{genre} ({user_genres[genre_key]}/10)")
        
        if matching_genres:
            explanations.append(f"🎭 Genre match: {', '.join(matching_genres[:2])}")
        
        # Quality indicators
        rating = safe_float(movie.get('rating', 0), 0.0)
        
        if rating >= 8.5:
            explanations.append(f"⭐ Exceptional ({rating:.1f}/10)")
        elif rating >= 8.0:
            explanations.append(f"🌟 Outstanding ({rating:.1f}/10)")
        elif rating >= 7.5:
            explanations.append(f"👍 Great quality ({rating:.1f}/10)")
        
        return " • ".join(explanations)

# Create global instance
recommendation_engine = EnhancedRecommendationEngine()

def get_enhanced_recommendations(user_prefs: Dict[str, float], algorithm: str = 'hybrid', 
                               num_recommendations: int = 10) -> List[Dict]:
    """Main function to get enhanced recommendations"""
    return recommendation_engine.get_recommendations(user_prefs, algorithm, num_recommendations)

def get_available_algorithms() -> List[str]:
    """Get list of available recommendation algorithms"""
    return list(recommendation_engine.algorithms.keys())

if __name__ == "__main__":
    # Test the recommendation engine
    test_prefs = {
        'action': 9.0,
        'thriller': 8.0,
        'comedy': 6.0,
        'romance': 4.0,
        'drama': 7.0
    }
    
    print("🎬 Enhanced Recommendation Engine Test")
    print("=" * 50)
    
    for algorithm in get_available_algorithms():
        print(f"\n📋 Testing {algorithm.replace('_', ' ').title()} Algorithm:")
        recs = get_enhanced_recommendations(test_prefs, algorithm, 3)
        
        for i, movie in enumerate(recs[:3], 1):
            print(f"  {i}. {movie['title']} ({movie.get('year', 'N/A')}) - {movie['prediction_score']:.3f}")
            print(f"     {movie.get('explanation', 'No explanation available')}")