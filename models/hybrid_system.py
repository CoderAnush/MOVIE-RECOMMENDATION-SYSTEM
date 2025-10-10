"""
Hybrid Recommendation System: Fuzzy Logic + ANN
===============================================

This module combines the fuzzy logic system with the ANN model to create
a powerful hybrid recommendation engine.

Features:
- Seamless integration of fuzzy and neural network predictions
- Weighted combination strategies
- Advanced hybrid fuzzy rules for combining scores
- Performance comparison and analysis tools
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from models.fuzzy_model import FuzzyMovieRecommender, recommend_with_fuzzy
from models.ann_model import ANNMoviePredictor
import logging

logger = logging.getLogger(__name__)

class HybridRecommendationSystem:
    """
    Complete hybrid system combining fuzzy logic and ANN predictions.
    """
    
    def __init__(self, ann_model_name: str = "ann_movie_predictor"):
        """
        Initialize the hybrid system.
        
        Args:
            ann_model_name: Name of the saved ANN model to load
        """
        self.fuzzy_engine = FuzzyMovieRecommender()
        self.ann_predictor = ANNMoviePredictor()
        
        # Try to load ANN model
        try:
            self.ann_predictor.load_model(ann_model_name)
            self.ann_available = True
            logger.info("✅ ANN model loaded successfully")
        except FileNotFoundError:
            self.ann_available = False
            logger.warning("⚠️ ANN model not found. Using fuzzy-only predictions.")
        
        # Combination strategies
        self.combination_strategies = {
            'weighted_average': self._weighted_average,
            'fuzzy_dominant': self._fuzzy_dominant,
            'ann_dominant': self._ann_dominant,
            'confidence_weighted': self._confidence_weighted,
            'adaptive': self._adaptive_combination
        }
    
    def _weighted_average(self, fuzzy_score: float, ann_score: float, 
                         context: Dict[str, Any]) -> float:
        """Simple weighted average combination."""
        fuzzy_weight = context.get('fuzzy_weight', 0.6)
        ann_weight = 1 - fuzzy_weight
        return fuzzy_score * fuzzy_weight + ann_score * ann_weight
    
    def _fuzzy_dominant(self, fuzzy_score: float, ann_score: float,
                       context: Dict[str, Any]) -> float:
        """Fuzzy-dominant combination (70% fuzzy, 30% ANN)."""
        return fuzzy_score * 0.7 + ann_score * 0.3
    
    def _ann_dominant(self, fuzzy_score: float, ann_score: float,
                     context: Dict[str, Any]) -> float:
        """ANN-dominant combination (30% fuzzy, 70% ANN)."""
        return fuzzy_score * 0.3 + ann_score * 0.7
    
    def _confidence_weighted(self, fuzzy_score: float, ann_score: float,
                           context: Dict[str, Any]) -> float:
        """
        Confidence-weighted combination based on user history and genre match.
        """
        # Default equal weights
        fuzzy_weight = 0.5
        ann_weight = 0.5
        
        # Adjust based on user history
        watch_history = context.get('watch_history', {})
        watch_count = watch_history.get('watch_count', 0)
        
        if watch_count > 50:
            # Lots of history - trust ANN more
            ann_weight = 0.7
            fuzzy_weight = 0.3
        elif watch_count < 10:
            # Little history - trust fuzzy more
            fuzzy_weight = 0.7
            ann_weight = 0.3
        
        # Adjust based on genre match
        genre_match = context.get('genre_match', 0.5)
        if genre_match > 0.8:
            # Strong genre match - trust fuzzy more
            fuzzy_weight += 0.1
            ann_weight -= 0.1
        elif genre_match < 0.3:
            # Poor genre match - trust ANN more
            ann_weight += 0.1
            fuzzy_weight -= 0.1
        
        # Normalize weights
        total_weight = fuzzy_weight + ann_weight
        fuzzy_weight /= total_weight
        ann_weight /= total_weight
        
        return fuzzy_score * fuzzy_weight + ann_score * ann_weight
    
    def _adaptive_combination(self, fuzzy_score: float, ann_score: float,
                            context: Dict[str, Any]) -> float:
        """
        Adaptive combination that considers score confidence and agreement.
        """
        # Calculate agreement between scores
        score_diff = abs(fuzzy_score - ann_score)
        agreement = 1 - (score_diff / 10)  # Higher agreement = closer scores
        
        # Base weights
        if agreement > 0.8:
            # High agreement - average them
            return (fuzzy_score + ann_score) / 2
        elif agreement < 0.4:
            # Low agreement - use confidence-based weighting
            return self._confidence_weighted(fuzzy_score, ann_score, context)
        else:
            # Medium agreement - slight fuzzy preference
            return fuzzy_score * 0.6 + ann_score * 0.4
    
    def calculate_genre_match(self, user_preferences: Dict[str, float], 
                            movie_genres: List[str]) -> float:
        """Calculate genre match score for context."""
        return self.fuzzy_engine.calculate_genre_match(user_preferences, movie_genres)
    
    def recommend(self, user_preferences: Dict[str, float],
                 movie_info: Dict[str, Any],
                 watch_history: Optional[Dict[str, float]] = None,
                 combination_strategy: str = 'adaptive') -> Dict[str, Any]:
        """
        Get hybrid recommendation combining fuzzy and ANN predictions.
        
        Args:
            user_preferences: User genre preferences (0-10)
            movie_info: Movie metadata dict
            watch_history: Optional watch history stats
            combination_strategy: Strategy for combining scores
            
        Returns:
            Dict with fuzzy, ANN, hybrid scores and explanation
        """
        # Get fuzzy score
        fuzzy_result = recommend_with_fuzzy(
            self.fuzzy_engine, user_preferences, movie_info, watch_history
        )
        fuzzy_score = fuzzy_result['fuzzy_score']
        
        # Prepare result
        result = {
            'fuzzy_score': fuzzy_score,
            'movie_info': movie_info,
            'combination_strategy': combination_strategy,
            'explanation': f"Fuzzy logic score: {fuzzy_score:.2f}"
        }
        
        # Get ANN score if available
        if self.ann_available:
            try:
                ann_score = self.ann_predictor.predict(
                    user_preferences, movie_info, watch_history
                )
                result['ann_score'] = ann_score
                result['explanation'] += f", ANN score: {ann_score:.2f}"
                
                # Calculate hybrid score
                context = {
                    'watch_history': watch_history or {},
                    'genre_match': self.calculate_genre_match(
                        user_preferences, movie_info.get('genres', [])
                    ),
                    'fuzzy_weight': 0.6  # Default weight
                }
                
                if combination_strategy in self.combination_strategies:
                    hybrid_score = self.combination_strategies[combination_strategy](
                        fuzzy_score, ann_score, context
                    )
                else:
                    # Default to weighted average
                    hybrid_score = self._weighted_average(fuzzy_score, ann_score, context)
                
                result['hybrid_score'] = round(hybrid_score, 2)
                result['explanation'] += f" → Hybrid ({combination_strategy}): {hybrid_score:.2f}"
                
            except Exception as e:
                logger.warning(f"ANN prediction failed: {e}")
                result['hybrid_score'] = fuzzy_score
                result['explanation'] += " (ANN failed, using fuzzy only)"
        else:
            # No ANN available
            result['hybrid_score'] = fuzzy_score
            result['explanation'] += " (ANN not available, using fuzzy only)"
        
        return result
    
    def batch_recommend(self, recommendations_list: List[Dict],
                       combination_strategy: str = 'adaptive') -> List[Dict]:
        """
        Batch process multiple recommendations.
        
        Args:
            recommendations_list: List of recommendation requests
            combination_strategy: Strategy for combining scores
            
        Returns:
            List of recommendation results
        """
        results = []
        
        for req in recommendations_list:
            result = self.recommend(
                user_preferences=req['user_preferences'],
                movie_info=req['movie_info'],
                watch_history=req.get('watch_history'),
                combination_strategy=combination_strategy
            )
            result['request_id'] = req.get('id', len(results))
            results.append(result)
        
        return results
    
    def compare_strategies(self, user_preferences: Dict[str, float],
                          movie_info: Dict[str, Any],
                          watch_history: Optional[Dict[str, float]] = None) -> Dict[str, Dict]:
        """
        Compare all combination strategies for a single recommendation.
        
        Args:
            user_preferences: User genre preferences
            movie_info: Movie metadata
            watch_history: Optional watch history
            
        Returns:
            Dict with results for each strategy
        """
        comparison = {}
        
        for strategy_name in self.combination_strategies.keys():
            result = self.recommend(
                user_preferences, movie_info, watch_history, strategy_name
            )
            comparison[strategy_name] = result
        
        return comparison
    
    def get_recommendation_explanation(self, result: Dict[str, Any]) -> str:
        """
        Generate detailed explanation for a recommendation.
        
        Args:
            result: Recommendation result dict
            
        Returns:
            Detailed explanation string
        """
        explanation = []
        
        # Movie info
        movie_info = result['movie_info']
        explanation.append(f"🎬 Movie: {movie_info.get('title', 'Unknown')}")
        explanation.append(f"   Genres: {', '.join(movie_info.get('genres', []))}")
        explanation.append(f"   Popularity: {movie_info.get('popularity', 'Unknown')}")
        
        # Scores
        explanation.append(f"\n📊 Recommendation Scores:")
        explanation.append(f"   Fuzzy Logic: {result['fuzzy_score']:.2f}/10")
        
        if 'ann_score' in result:
            explanation.append(f"   Neural Network: {result['ann_score']:.2f}/10")
        
        if 'hybrid_score' in result:
            strategy = result.get('combination_strategy', 'unknown')
            explanation.append(f"   Hybrid ({strategy}): {result['hybrid_score']:.2f}/10")
        
        # Recommendation level
        final_score = result.get('hybrid_score', result['fuzzy_score'])
        if final_score >= 8:
            level = "🔥 Highly Recommended"
        elif final_score >= 6:
            level = "👍 Recommended"
        elif final_score >= 4:
            level = "🤔 Maybe"
        else:
            level = "👎 Not Recommended"
        
        explanation.append(f"\n🎯 Recommendation: {level}")
        
        return '\n'.join(explanation)


def create_hybrid_system(ann_model_name: str = "ann_movie_predictor") -> HybridRecommendationSystem:
    """
    Factory function to create a hybrid recommendation system.
    
    Args:
        ann_model_name: Name of the ANN model to load
        
    Returns:
        Configured HybridRecommendationSystem
    """
    return HybridRecommendationSystem(ann_model_name)


# Example usage and testing
if __name__ == "__main__":
    print("🔄 HYBRID RECOMMENDATION SYSTEM - TEST")
    print("=" * 50)
    
    # Create hybrid system
    hybrid_system = HybridRecommendationSystem()
    
    # Test data
    user_prefs = {
        'action': 9.0,
        'comedy': 4.0,
        'romance': 2.0,
        'thriller': 8.5,
        'sci_fi': 7.0,
        'drama': 5.0,
        'horror': 1.0
    }
    
    movie_info = {
        'title': 'The Matrix',
        'genres': ['Action', 'Sci-Fi', 'Thriller'],
        'popularity': 95,
        'year': 1999
    }
    
    watch_history = {
        'liked_ratio': 0.8,
        'disliked_ratio': 0.1,
        'watch_count': 45
    }
    
    # Test recommendation
    result = hybrid_system.recommend(user_prefs, movie_info, watch_history)
    
    print("\n📋 Test Recommendation Result:")
    print(hybrid_system.get_recommendation_explanation(result))
    
    # Compare strategies
    print("\n🔍 Strategy Comparison:")
    comparison = hybrid_system.compare_strategies(user_prefs, movie_info, watch_history)
    
    for strategy, res in comparison.items():
        score = res.get('hybrid_score', res['fuzzy_score'])
        print(f"   {strategy}: {score:.2f}")
    
    print("\n✅ Hybrid system test completed!")