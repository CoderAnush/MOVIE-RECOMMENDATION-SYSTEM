"""
Unit tests for the Fuzzy Logic Movie Recommendation System

Tests cover:
- Membership function calculations
- Rule evaluation logic
- Fuzzy inference process
- Edge cases and boundary conditions
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.fuzzy_model import (
    FuzzyMovieRecommender,
    FuzzyMembershipFunctions,
    FuzzyRuleEngine,
    triangular
)

class TestTriangularMembershipFunction:
    """Test the triangular membership function"""
    
    def test_triangular_basic(self):
        """Test basic triangular function behavior"""
        # Test peak
        assert triangular(5, 3, 5, 7) == 1.0
        
        # Test left slope
        assert triangular(4, 3, 5, 7) == 0.5
        
        # Test right slope
        assert triangular(6, 3, 5, 7) == 0.5
        
        # Test outside range
        assert triangular(2, 3, 5, 7) == 0.0
        assert triangular(8, 3, 5, 7) == 0.0
    
    def test_triangular_edge_cases(self):
        """Test edge cases for triangular function"""
        # Test at boundaries
        assert triangular(3, 3, 5, 7) == 0.0
        assert triangular(7, 3, 5, 7) == 0.0
        
        # Test degenerate triangle (all points same)
        assert triangular(5, 5, 5, 5) == 1.0
        assert triangular(4, 5, 5, 5) == 0.0

class TestFuzzyMembershipFunctions:
    """Test fuzzy membership functions"""
    
    def setUp(self):
        self.membership_funcs = FuzzyMembershipFunctions()
    
    def test_user_preference_membership(self):
        """Test user preference membership functions"""
        membership_funcs = FuzzyMembershipFunctions()
        
        # Test Very Low preference
        result = membership_funcs.user_preference(1.0)
        assert result['Very Low'] == 1.0
        assert result['Low'] == 0.0
        
        # Test boundary between Low and Medium
        result = membership_funcs.user_preference(3.5)
        assert result['Low'] > 0
        assert result['Medium'] > 0
        
        # Test Very High preference
        result = membership_funcs.user_preference(9.0)
        assert result['Very High'] == 1.0
    
    def test_popularity_membership(self):
        """Test popularity membership functions"""
        membership_funcs = FuzzyMembershipFunctions()
        
        # Test Low popularity
        result = membership_funcs.popularity(20)
        assert result['Low'] == 1.0
        
        # Test High popularity
        result = membership_funcs.popularity(80)
        assert result['High'] == 1.0
        
        # Test boundary case
        result = membership_funcs.popularity(50)
        assert result['Medium'] == 1.0
    
    def test_genre_match_membership(self):
        """Test genre match membership functions"""
        membership_funcs = FuzzyMembershipFunctions()
        
        # Test Poor match
        result = membership_funcs.genre_match(0.2)
        assert result['Poor'] == 1.0
        
        # Test Excellent match
        result = membership_funcs.genre_match(0.8)
        assert result['Excellent'] == 1.0
        
        # Test boundary case
        result = membership_funcs.genre_match(0.5)
        assert result['Average'] == 1.0

class TestFuzzyRuleEngine:
    """Test fuzzy rule engine"""
    
    def setUp(self):
        self.rule_engine = FuzzyRuleEngine()
    
    def test_genre_preference_rules(self):
        """Test genre preference rule evaluation"""
        rule_engine = FuzzyRuleEngine()
        
        user_preferences = {'Action': 'Very High', 'Comedy': 'Low'}
        movie_genres = ['Action', 'Thriller']
        
        result = rule_engine.evaluate_genre_preference_rules(
            user_preferences, movie_genres, 1
        )
        
        # Should have high activation for Very High Action preference
        assert result['Very High'][0] > 0.8
        assert len(rule_engine.fired_rules) > 0
    
    def test_popularity_genre_match_rules(self):
        """Test popularity and genre match rules"""
        rule_engine = FuzzyRuleEngine()
        
        # High popularity + Excellent genre match should give Very High
        result = rule_engine.evaluate_popularity_genre_match_rules(
            popularity=85, genre_match_score=0.9
        )
        
        assert result['Very High'][0] > 0.8
        assert len(rule_engine.fired_rules) > 0
    
    def test_rule_aggregation(self):
        """Test rule activation aggregation"""
        rule_engine = FuzzyRuleEngine()
        
        rule_dict1 = {'High': [0.7, 0.5], 'Medium': [0.3]}
        rule_dict2 = {'High': [0.6], 'Low': [0.8]}
        
        aggregated = rule_engine.aggregate_rule_activations(rule_dict1, rule_dict2)
        
        # Should take maximum of High activations
        assert aggregated['High'] == 0.7
        assert aggregated['Medium'] == 0.3
        assert aggregated['Low'] == 0.8
    
    def test_defuzzification(self):
        """Test centroid defuzzification"""
        rule_engine = FuzzyRuleEngine()
        
        # Test case with clear high activation
        activations = {
            'Very Low': 0.0,
            'Low': 0.0,
            'Medium': 0.1,
            'High': 0.9,
            'Very High': 0.2
        }
        
        result = rule_engine.defuzzify_centroid(activations)
        
        # Should be closer to High (7.5) than other values
        assert 6.5 < result < 8.5
        
        # Test case with no activations
        empty_activations = {
            'Very Low': 0.0,
            'Low': 0.0,
            'Medium': 0.0,
            'High': 0.0,
            'Very High': 0.0
        }
        
        result = rule_engine.defuzzify_centroid(empty_activations)
        assert result == 5.0  # Default medium score

class TestFuzzyMovieRecommender:
    """Test the complete fuzzy movie recommender"""
    
    def setUp(self):
        self.recommender = FuzzyMovieRecommender()
    
    def test_single_movie_prediction(self):
        """Test prediction for a single movie"""
        recommender = FuzzyMovieRecommender()
        
        user_preferences = {
            'Action': 'Very High',
            'Comedy': 'Medium',
            'Romance': 'Low'
        }
        
        movie_data = {
            'movie_id': 1,
            'title': 'Test Action Movie',
            'genres': ['Action', 'Thriller'],
            'popularity': 80
        }
        
        result = recommender.predict_single_movie(user_preferences, movie_data)
        
        # Verify result structure
        assert 'movie_id' in result
        assert 'fuzzy_score' in result
        assert 'explanation' in result
        assert 'fired_rules' in result
        
        # Score should be reasonable for high Action preference
        assert 6.0 <= result['fuzzy_score'] <= 10.0
        
        # Should have fired some rules
        assert len(result['fired_rules']) > 0
    
    def test_batch_prediction(self):
        """Test batch prediction for multiple movies"""
        recommender = FuzzyMovieRecommender()
        
        user_preferences = {'Action': 'High', 'Comedy': 'Low'}
        
        movies_data = [
            {'movie_id': 1, 'title': 'Action Movie', 'genres': ['Action'], 'popularity': 80},
            {'movie_id': 2, 'title': 'Comedy Movie', 'genres': ['Comedy'], 'popularity': 70}
        ]
        
        results = recommender.predict_batch(user_preferences, movies_data)
        
        assert len(results) == 2
        
        # Action movie should score higher than comedy movie
        action_score = next(r['fuzzy_score'] for r in results if r['movie_id'] == 1)
        comedy_score = next(r['fuzzy_score'] for r in results if r['movie_id'] == 2)
        
        assert action_score > comedy_score
    
    def test_genre_match_computation(self):
        """Test genre match score computation"""
        recommender = FuzzyMovieRecommender()
        
        user_preferences = {
            'Action': 'Very High',
            'Comedy': 'Low'
        }
        
        # Perfect match
        perfect_match = recommender._compute_genre_match(user_preferences, ['Action'])
        assert perfect_match > 0.7
        
        # Poor match
        poor_match = recommender._compute_genre_match(user_preferences, ['Comedy'])
        assert poor_match < 0.3
        
        # No match
        no_match = recommender._compute_genre_match(user_preferences, ['Horror'])
        assert no_match == 0.0
        
        # Empty genres
        empty_match = recommender._compute_genre_match(user_preferences, [])
        assert empty_match == 0.0
    
    def test_user_history_processing(self):
        """Test user history statistics computation"""
        recommender = FuzzyMovieRecommender()
        
        # Create sample user history
        user_history = pd.DataFrame({
            'movie_id': [1, 2, 3, 4],
            'title': ['Movie 1', 'Movie 2', 'Movie 3', 'Movie 4'],
            'genres': [['Action'], ['Action'], ['Comedy'], ['Action']],
            'rating': [5, 4, 2, 5]
        })
        
        genre_stats = recommender.compute_user_genre_history(user_history)
        
        # Check Action genre stats
        assert 'Action' in genre_stats
        assert genre_stats['Action']['watched_count'] == 3
        assert genre_stats['Action']['liked_count'] == 3  # ratings >= 4
        assert genre_stats['Action']['liked_ratio'] == 1.0
        
        # Check Comedy genre stats
        assert 'Comedy' in genre_stats
        assert genre_stats['Comedy']['watched_count'] == 1
        assert genre_stats['Comedy']['liked_count'] == 0  # rating = 2
        assert genre_stats['Comedy']['liked_ratio'] == 0.0

class TestFuzzySystemIntegration:
    """Integration tests for the fuzzy system"""
    
    def test_preference_sensitivity(self):
        """Test that system responds appropriately to preference changes"""
        recommender = FuzzyMovieRecommender()
        
        movie_data = {
            'movie_id': 1,
            'title': 'Action Movie',
            'genres': ['Action'],
            'popularity': 75
        }
        
        # Test with Very High Action preference
        high_prefs = {'Action': 'Very High'}
        high_result = recommender.predict_single_movie(high_prefs, movie_data)
        
        # Test with Very Low Action preference
        low_prefs = {'Action': 'Very Low'}
        low_result = recommender.predict_single_movie(low_prefs, movie_data)
        
        # High preference should give higher score
        assert high_result['fuzzy_score'] > low_result['fuzzy_score']
        
        # Difference should be significant
        assert high_result['fuzzy_score'] - low_result['fuzzy_score'] > 2.0
    
    def test_popularity_influence(self):
        """Test that popularity influences recommendations"""
        recommender = FuzzyMovieRecommender()
        
        user_preferences = {'Action': 'Medium'}
        
        # High popularity movie
        high_pop_movie = {
            'movie_id': 1,
            'title': 'Popular Action Movie',
            'genres': ['Action'],
            'popularity': 90
        }
        
        # Low popularity movie
        low_pop_movie = {
            'movie_id': 2,
            'title': 'Obscure Action Movie',
            'genres': ['Action'],
            'popularity': 20
        }
        
        high_result = recommender.predict_single_movie(user_preferences, high_pop_movie)
        low_result = recommender.predict_single_movie(user_preferences, low_pop_movie)
        
        # Popular movie should generally score higher
        assert high_result['fuzzy_score'] >= low_result['fuzzy_score']
    
    def test_multi_genre_movies(self):
        """Test handling of movies with multiple genres"""
        recommender = FuzzyMovieRecommender()
        
        user_preferences = {
            'Action': 'Very High',
            'Comedy': 'Very Low'
        }
        
        # Movie with both preferred and non-preferred genres
        mixed_movie = {
            'movie_id': 1,
            'title': 'Action Comedy',
            'genres': ['Action', 'Comedy'],
            'popularity': 75
        }
        
        result = recommender.predict_single_movie(user_preferences, mixed_movie)
        
        # Should get a moderate score (not highest, not lowest)
        assert 4.0 <= result['fuzzy_score'] <= 8.0
        
        # Should have fired rules for both genres
        fired_genres = [rule.get('genre') for rule in result['fired_rules'] 
                       if rule.get('rule_type') == 'genre_preference']
        assert 'Action' in fired_genres
        assert 'Comedy' in fired_genres


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
