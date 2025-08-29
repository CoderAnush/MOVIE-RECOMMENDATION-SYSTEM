"""
Unit tests for Hybrid Recommender Model
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.hybrid import HybridRecommender


class TestHybridRecommender:
    """Test cases for Hybrid Recommender"""
    
    @pytest.fixture
    def mock_fuzzy_model(self):
        """Create mock fuzzy model"""
        mock = MagicMock()
        mock.predict_single_movie.return_value = {
            'movie_id': 1,
            'fuzzy_score': 7.5,
            'genre_match_score': 0.8,
            'fired_rules': ['high_action_preference'],
            'explanation': 'Strong action preference match'
        }
        return mock
    
    @pytest.fixture
    def mock_ann_model(self):
        """Create mock ANN model"""
        mock = MagicMock()
        mock.predict_batch.return_value = [8.2]
        return mock
    
    @pytest.fixture
    def hybrid_model(self, mock_fuzzy_model, mock_ann_model):
        """Create hybrid recommender instance"""
        return HybridRecommender(mock_fuzzy_model, mock_ann_model)
    
    @pytest.fixture
    def sample_movie_data(self):
        """Sample movie data"""
        return {
            'movie_id': 1,
            'title': 'Test Action Movie',
            'genres': ['Action', 'Adventure'],
            'popularity': 75.5,
            'year': 1995
        }
    
    @pytest.fixture
    def sample_user_history(self):
        """Sample user history"""
        return pd.DataFrame({
            'movie_id': [1, 2, 3],
            'title': ['Movie 1', 'Movie 2', 'Movie 3'],
            'genres': [['Action'], ['Comedy'], ['Drama']],
            'rating': [4.5, 3.8, 4.2]
        })
    
    def test_initialization(self, hybrid_model):
        """Test hybrid model initialization"""
        assert hybrid_model.fuzzy_model is not None
        assert hybrid_model.ann_model is not None
        assert hybrid_model.fuzzy_weight == 0.6
        assert hybrid_model.ann_weight == 0.4
    
    def test_weighted_fusion_default_weights(self, hybrid_model):
        """Test weighted fusion with default weights"""
        fuzzy_score = 7.5
        ann_score = 8.2
        
        result = hybrid_model.weighted_fusion(fuzzy_score, ann_score)
        expected = 0.6 * 7.5 + 0.4 * 8.2
        
        assert abs(result - expected) < 0.001
    
    def test_weighted_fusion_custom_weights(self, hybrid_model):
        """Test weighted fusion with custom weights"""
        fuzzy_score = 7.5
        ann_score = 8.2
        alpha, beta = 0.7, 0.3
        
        result = hybrid_model.weighted_fusion(fuzzy_score, ann_score, alpha, beta)
        expected = 0.7 * 7.5 + 0.3 * 8.2
        
        assert abs(result - expected) < 0.001
    
    def test_apply_hybrid_rules_high_scores(self, hybrid_model):
        """Test hybrid rules with high scores"""
        fuzzy_score = 8.5
        ann_score = 8.8
        
        result = hybrid_model.apply_hybrid_rules(fuzzy_score, ann_score)
        
        assert result['rule_score'] >= 8.0  # Should be high
        assert 'both_high' in result['rule_explanation']
    
    def test_apply_hybrid_rules_low_scores(self, hybrid_model):
        """Test hybrid rules with low scores"""
        fuzzy_score = 3.2
        ann_score = 2.8
        
        result = hybrid_model.apply_hybrid_rules(fuzzy_score, ann_score)
        
        assert result['rule_score'] <= 4.0  # Should be low
        assert 'both_low' in result['rule_explanation']
    
    def test_apply_hybrid_rules_mixed_scores(self, hybrid_model):
        """Test hybrid rules with mixed scores"""
        fuzzy_score = 8.0
        ann_score = 4.0
        
        result = hybrid_model.apply_hybrid_rules(fuzzy_score, ann_score)
        
        assert 4.0 < result['rule_score'] < 8.0  # Should be between
        assert 'fuzzy_higher' in result['rule_explanation']
    
    def test_compute_adaptive_weights_popular_movie(self, hybrid_model, sample_movie_data):
        """Test adaptive weights for popular movie"""
        sample_movie_data['popularity'] = 90.0  # High popularity
        user_history_size = 50
        
        alpha, beta = hybrid_model.compute_adaptive_weights(sample_movie_data, user_history_size)
        
        # For popular movies, should favor ANN more
        assert beta > 0.4  # ANN weight should increase
        assert alpha + beta == 1.0  # Weights should sum to 1
    
    def test_compute_adaptive_weights_niche_movie(self, hybrid_model, sample_movie_data):
        """Test adaptive weights for niche movie"""
        sample_movie_data['popularity'] = 20.0  # Low popularity
        user_history_size = 10
        
        alpha, beta = hybrid_model.compute_adaptive_weights(sample_movie_data, user_history_size)
        
        # For niche movies, should favor fuzzy more
        assert alpha > 0.6  # Fuzzy weight should increase
        assert alpha + beta == 1.0  # Weights should sum to 1
    
    def test_predict_single_movie_weighted(self, hybrid_model, sample_movie_data, sample_user_history):
        """Test single movie prediction with weighted method"""
        user_id = 1
        user_preferences = {'Action': 8, 'Adventure': 7}
        
        result = hybrid_model.predict_single_movie(
            user_id, user_preferences, sample_movie_data, 
            sample_user_history, method='weighted'
        )
        
        assert 'movie_id' in result
        assert 'final_score' in result
        assert 'fuzzy_score' in result
        assert 'ann_score' in result
        assert 'explanation' in result
        assert result['movie_id'] == 1
    
    def test_predict_single_movie_rule_based(self, hybrid_model, sample_movie_data, sample_user_history):
        """Test single movie prediction with rule-based method"""
        user_id = 1
        user_preferences = {'Action': 8, 'Adventure': 7}
        
        result = hybrid_model.predict_single_movie(
            user_id, user_preferences, sample_movie_data, 
            sample_user_history, method='rule'
        )
        
        assert 'movie_id' in result
        assert 'final_score' in result
        assert 'combination_method' in result
        assert result['combination_method'] == 'rule'
    
    def test_predict_single_movie_adaptive(self, hybrid_model, sample_movie_data, sample_user_history):
        """Test single movie prediction with adaptive method"""
        user_id = 1
        user_preferences = {'Action': 8, 'Adventure': 7}
        
        result = hybrid_model.predict_single_movie(
            user_id, user_preferences, sample_movie_data, 
            sample_user_history, method='adaptive'
        )
        
        assert 'movie_id' in result
        assert 'final_score' in result
        assert 'combination_method' in result
        assert result['combination_method'] == 'adaptive'
        assert 'adaptive_weights' in result
    
    def test_predict_batch(self, hybrid_model, sample_user_history):
        """Test batch prediction"""
        user_id = 1
        user_preferences = {'Action': 8, 'Comedy': 6}
        movies_data = [
            {'movie_id': 1, 'title': 'Action Movie', 'genres': ['Action'], 'popularity': 80},
            {'movie_id': 2, 'title': 'Comedy Movie', 'genres': ['Comedy'], 'popularity': 60}
        ]
        
        # Mock fuzzy model to return different scores
        hybrid_model.fuzzy_model.predict_single_movie.side_effect = [
            {'movie_id': 1, 'fuzzy_score': 8.0, 'explanation': 'Action match'},
            {'movie_id': 2, 'fuzzy_score': 6.5, 'explanation': 'Comedy match'}
        ]
        
        # Mock ANN model to return different scores
        hybrid_model.ann_model.predict_batch.return_value = [8.5, 7.0]
        
        results = hybrid_model.predict_batch(
            user_id, user_preferences, movies_data, 
            sample_user_history, top_k=2
        )
        
        assert len(results) == 2
        assert all('final_score' in result for result in results)
        
        # Results should be sorted by final score (descending)
        scores = [result['final_score'] for result in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_generate_hybrid_explanation(self, hybrid_model):
        """Test hybrid explanation generation"""
        fuzzy_score = 7.5
        ann_score = 8.2
        final_score = 7.8
        fuzzy_explanation = "Strong action preference"
        combination_explanation = "Weighted average of fuzzy and ANN"
        
        explanation = hybrid_model._generate_hybrid_explanation(
            fuzzy_score, ann_score, final_score, 
            fuzzy_explanation, combination_explanation
        )
        
        assert isinstance(explanation, str)
        assert str(fuzzy_score) in explanation
        assert str(ann_score) in explanation
        assert str(final_score) in explanation
        assert fuzzy_explanation in explanation
    
    def test_empty_user_history_handling(self, hybrid_model, sample_movie_data):
        """Test handling of empty user history"""
        user_id = 1
        user_preferences = {'Action': 8}
        
        result = hybrid_model.predict_single_movie(
            user_id, user_preferences, sample_movie_data, 
            user_history=None
        )
        
        assert 'final_score' in result
        # Should still work without user history
    
    def test_score_bounds(self, hybrid_model, sample_movie_data, sample_user_history):
        """Test that final scores are within reasonable bounds"""
        user_id = 1
        user_preferences = {'Action': 8}
        
        # Test with extreme fuzzy and ANN scores
        hybrid_model.fuzzy_model.predict_single_movie.return_value = {
            'movie_id': 1, 'fuzzy_score': 10.0, 'explanation': 'Perfect match'
        }
        hybrid_model.ann_model.predict_batch.return_value = [0.0]
        
        result = hybrid_model.predict_single_movie(
            user_id, user_preferences, sample_movie_data, sample_user_history
        )
        
        # Final score should be reasonable (not extreme)
        assert 0 <= result['final_score'] <= 10
    
    def test_consistency_across_methods(self, hybrid_model, sample_movie_data, sample_user_history):
        """Test that different methods produce consistent results"""
        user_id = 1
        user_preferences = {'Action': 8}
        
        # Get predictions with different methods
        result_weighted = hybrid_model.predict_single_movie(
            user_id, user_preferences, sample_movie_data, 
            sample_user_history, method='weighted'
        )
        
        result_adaptive = hybrid_model.predict_single_movie(
            user_id, user_preferences, sample_movie_data, 
            sample_user_history, method='adaptive'
        )
        
        # Fuzzy and ANN scores should be the same
        assert result_weighted['fuzzy_score'] == result_adaptive['fuzzy_score']
        assert result_weighted['ann_score'] == result_adaptive['ann_score']
        
        # Final scores may differ but should be reasonable
        assert abs(result_weighted['final_score'] - result_adaptive['final_score']) < 3.0


if __name__ == '__main__':
    pytest.main([__file__])
