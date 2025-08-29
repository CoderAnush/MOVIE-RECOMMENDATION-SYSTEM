"""
Hybrid Movie Recommendation System

This module combines Fuzzy Logic and ANN predictions to create a hybrid
recommendation system with both rule-based and weighted fusion approaches.

Hybrid Rules Implementation:
===========================

D) Hybrid (Fuzzy + ANN) Rules:
- IF Fuzzy Recommendation is Very High AND ANN Predicted Score is High THEN Final Recommendation Score is Very High
- IF Fuzzy Recommendation is High AND ANN Predicted Score is High THEN Final Recommendation Score is High
- IF Fuzzy Recommendation is Medium AND ANN Predicted Score is Medium THEN Final Recommendation Score is Medium
- IF Fuzzy Recommendation is Low AND ANN Predicted Score is Medium THEN Final Recommendation Score is Medium
- IF Fuzzy Recommendation is High AND ANN Predicted Score is Low THEN Final Recommendation Score is Medium
- IF Fuzzy Recommendation is Low AND ANN Predicted Score is Low THEN Final Recommendation Score is Very Low
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class HybridRecommender:
    """Combines Fuzzy Logic and ANN predictions for movie recommendations"""
    
    def __init__(self, fuzzy_model, ann_model, alpha=0.6, beta=0.4):
        """
        Initialize hybrid recommender
        
        Args:
            fuzzy_model: Trained fuzzy logic model
            ann_model: Trained ANN model
            alpha (float): Weight for ANN predictions (0-1)
            beta (float): Weight for fuzzy predictions (0-1)
        """
        self.fuzzy_model = fuzzy_model
        self.ann_model = ann_model
        self.alpha = alpha  # ANN weight
        self.beta = beta    # Fuzzy weight
        
        # Ensure weights sum to 1
        total_weight = alpha + beta
        if total_weight != 1.0:
            self.alpha = alpha / total_weight
            self.beta = beta / total_weight
            logger.info(f"Normalized weights - ANN: {self.alpha:.3f}, Fuzzy: {self.beta:.3f}")
    
    def compute_adaptive_weights(self, movie_data, user_history_size=0):
        """
        Compute adaptive weights based on data quality and availability
        
        Args:
            movie_data (dict): Movie information
            user_history_size (int): Number of ratings in user's history
            
        Returns:
            tuple: (alpha, beta) adaptive weights
        """
        # Base weights
        alpha = self.alpha
        beta = self.beta
        
        # Adjust based on movie popularity (more popular = trust ANN more)
        popularity = movie_data.get('popularity', 50)
        if popularity > 70:
            alpha += 0.1  # Trust ANN more for popular movies
        elif popularity < 30:
            beta += 0.1   # Trust fuzzy more for unpopular movies
        
        # Adjust based on user history size (more history = trust ANN more)
        if user_history_size > 50:
            alpha += 0.1  # User has lots of history, ANN can learn better
        elif user_history_size < 10:
            beta += 0.1   # Limited history, rely more on fuzzy rules
        
        # Normalize weights
        total = alpha + beta
        alpha /= total
        beta /= total
        
        return alpha, beta
    
    def linguistic_to_numeric(self, linguistic_term):
        """
        Convert linguistic terms to numeric values
        
        Args:
            linguistic_term (str): Linguistic term
            
        Returns:
            float: Numeric value (0-10)
        """
        mapping = {
            'Very Low': 1.0,
            'Low': 2.5,
            'Medium': 5.0,
            'High': 7.5,
            'Very High': 9.0
        }
        return mapping.get(linguistic_term, 5.0)
    
    def numeric_to_linguistic(self, numeric_value):
        """
        Convert numeric values to linguistic terms
        
        Args:
            numeric_value (float): Numeric value (0-10)
            
        Returns:
            str: Linguistic term
        """
        if numeric_value <= 2:
            return 'Very Low'
        elif numeric_value <= 4:
            return 'Low'
        elif numeric_value <= 6:
            return 'Medium'
        elif numeric_value <= 8:
            return 'High'
        else:
            return 'Very High'
    
    def apply_hybrid_rules(self, fuzzy_score, ann_score):
        """
        Apply rule-based hybrid combination
        
        Args:
            fuzzy_score (float): Fuzzy logic score (0-10)
            ann_score (float): ANN predicted score (0-10)
            
        Returns:
            dict: Rule-based combination result
        """
        # Convert to linguistic terms
        fuzzy_term = self.numeric_to_linguistic(fuzzy_score)
        ann_term = self.numeric_to_linguistic(ann_score)
        
        # Define hybrid rules
        hybrid_rules = {
            ('Very High', 'Very High'): 'Very High',
            ('Very High', 'High'): 'Very High',
            ('Very High', 'Medium'): 'High',
            ('Very High', 'Low'): 'Medium',
            ('Very High', 'Very Low'): 'Medium',
            
            ('High', 'Very High'): 'Very High',
            ('High', 'High'): 'High',
            ('High', 'Medium'): 'High',
            ('High', 'Low'): 'Medium',
            ('High', 'Very Low'): 'Low',
            
            ('Medium', 'Very High'): 'High',
            ('Medium', 'High'): 'High',
            ('Medium', 'Medium'): 'Medium',
            ('Medium', 'Low'): 'Medium',
            ('Medium', 'Very Low'): 'Low',
            
            ('Low', 'Very High'): 'Medium',
            ('Low', 'High'): 'Medium',
            ('Low', 'Medium'): 'Medium',
            ('Low', 'Low'): 'Low',
            ('Low', 'Very Low'): 'Very Low',
            
            ('Very Low', 'Very High'): 'Low',
            ('Very Low', 'High'): 'Low',
            ('Very Low', 'Medium'): 'Low',
            ('Very Low', 'Low'): 'Very Low',
            ('Very Low', 'Very Low'): 'Very Low',
        }
        
        # Apply rule
        rule_key = (fuzzy_term, ann_term)
        output_term = hybrid_rules.get(rule_key, 'Medium')
        rule_score = self.linguistic_to_numeric(output_term)
        
        return {
            'rule_score': rule_score,
            'output_term': output_term,
            'fuzzy_term': fuzzy_term,
            'ann_term': ann_term,
            'fired_rule': f"IF Fuzzy is {fuzzy_term} AND ANN is {ann_term} THEN Final is {output_term}"
        }
    
    def weighted_fusion(self, fuzzy_score, ann_score, alpha=None, beta=None):
        """
        Apply weighted fusion of fuzzy and ANN scores
        
        Args:
            fuzzy_score (float): Fuzzy logic score (0-10)
            ann_score (float): ANN predicted score (0-10)
            alpha (float): ANN weight (optional, uses instance default)
            beta (float): Fuzzy weight (optional, uses instance default)
            
        Returns:
            float: Weighted combined score
        """
        if alpha is None:
            alpha = self.alpha
        if beta is None:
            beta = self.beta
        
        # Normalize scores to 0-1 range for combination
        fuzzy_norm = fuzzy_score / 10.0
        ann_norm = ann_score / 10.0
        
        # Weighted combination
        combined_norm = alpha * ann_norm + beta * fuzzy_norm
        
        # Scale back to 0-10
        combined_score = combined_norm * 10.0
        
        return combined_score
    
    def predict_single_movie(self, user_id, user_preferences, movie_data, 
                           user_history=None, method='adaptive'):
        """
        Predict recommendation score for a single movie using hybrid approach
        
        Args:
            user_id (int): User ID
            user_preferences (dict): User genre preferences
            movie_data (dict): Movie information
            user_history (pd.DataFrame): User's rating history
            method (str): Combination method ('rule', 'weighted', 'adaptive')
            
        Returns:
            dict: Hybrid prediction result
        """
        movie_id = movie_data['movie_id']
        
        try:
            # Get fuzzy prediction
            fuzzy_result = self.fuzzy_model.predict_single_movie(
                user_preferences, movie_data, user_history
            )
            fuzzy_score = fuzzy_result['fuzzy_score']
            fuzzy_explanation = fuzzy_result['explanation']
            
        except Exception as e:
            logger.warning(f"Fuzzy prediction failed for movie {movie_id}: {e}")
            fuzzy_score = 5.0
            fuzzy_explanation = "Fuzzy prediction unavailable"
        
        try:
            # Get ANN prediction
            if user_id in self.ann_model.user_to_idx and movie_id in self.ann_model.movie_to_idx:
                ann_predictions = self.ann_model.predict_batch([user_id], [movie_id])
                ann_score = ann_predictions[0]
            else:
                ann_score = 5.0  # Default for unknown user/movie
            
        except Exception as e:
            logger.warning(f"ANN prediction failed for movie {movie_id}: {e}")
            ann_score = 5.0
        
        # Combine predictions based on method
        if method == 'rule':
            # Rule-based combination
            rule_result = self.apply_hybrid_rules(fuzzy_score, ann_score)
            final_score = rule_result['rule_score']
            combination_explanation = f"Rule: {rule_result['fired_rule']}"
            
        elif method == 'weighted':
            # Weighted fusion
            final_score = self.weighted_fusion(fuzzy_score, ann_score)
            combination_explanation = f"Weighted: {self.alpha:.2f}*ANN + {self.beta:.2f}*Fuzzy"
            
        elif method == 'adaptive':
            # Adaptive weighted fusion
            user_history_size = len(user_history) if user_history is not None else 0
            alpha, beta = self.compute_adaptive_weights(movie_data, user_history_size)
            final_score = self.weighted_fusion(fuzzy_score, ann_score, alpha, beta)
            combination_explanation = f"Adaptive: {alpha:.2f}*ANN + {beta:.2f}*Fuzzy"
            
        else:
            raise ValueError(f"Unknown combination method: {method}")
        
        # Ensure score is in valid range
        final_score = np.clip(final_score, 0, 10)
        
        # Generate comprehensive explanation
        explanation = self._generate_hybrid_explanation(
            fuzzy_score, ann_score, final_score, 
            fuzzy_explanation, combination_explanation
        )
        
        return {
            'movie_id': movie_id,
            'final_score': round(final_score, 2),
            'fuzzy_score': round(fuzzy_score, 2),
            'ann_score': round(ann_score, 2),
            'explanation': explanation,
            'method': method,
            'fuzzy_explanation': fuzzy_explanation,
            'combination_explanation': combination_explanation
        }
    
    def predict_batch(self, user_id, user_preferences, movies_data, 
                     user_history=None, method='adaptive', top_k=10):
        """
        Predict recommendation scores for multiple movies
        
        Args:
            user_id (int): User ID
            user_preferences (dict): User genre preferences
            movies_data (list): List of movie dictionaries
            user_history (pd.DataFrame): User's rating history
            method (str): Combination method
            top_k (int): Number of top recommendations to return
            
        Returns:
            list: List of hybrid prediction results, sorted by final score
        """
        results = []
        
        for movie_data in movies_data:
            try:
                result = self.predict_single_movie(
                    user_id, user_preferences, movie_data, 
                    user_history, method
                )
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Hybrid prediction failed for movie {movie_data.get('movie_id')}: {e}")
                # Add default result
                results.append({
                    'movie_id': movie_data.get('movie_id'),
                    'final_score': 5.0,
                    'fuzzy_score': 5.0,
                    'ann_score': 5.0,
                    'explanation': "Hybrid prediction failed",
                    'method': method
                })
        
        # Sort by final score (descending)
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results[:top_k]
    
    def _generate_hybrid_explanation(self, fuzzy_score, ann_score, final_score, 
                                   fuzzy_explanation, combination_explanation):
        """
        Generate comprehensive explanation for hybrid recommendation
        
        Args:
            fuzzy_score (float): Fuzzy score
            ann_score (float): ANN score
            final_score (float): Final hybrid score
            fuzzy_explanation (str): Fuzzy explanation
            combination_explanation (str): Combination method explanation
            
        Returns:
            str: Comprehensive explanation
        """
        # Extract fuzzy explanation (remove "Fuzzy: X.X — " prefix if present)
        clean_fuzzy = fuzzy_explanation
        if " — " in fuzzy_explanation:
            clean_fuzzy = fuzzy_explanation.split(" — ", 1)[1]
        
        # Generate ANN explanation
        if ann_score >= 7.5:
            ann_explanation = "users similar to you rated it highly"
        elif ann_score >= 6.0:
            ann_explanation = "predicted as a good match"
        elif ann_score >= 4.0:
            ann_explanation = "moderate prediction from user patterns"
        else:
            ann_explanation = "low prediction from user patterns"
        
        # Combine explanations
        explanation = (
            f"Fuzzy: {fuzzy_score:.1f} — {clean_fuzzy}; "
            f"ANN: {ann_score:.1f} — {ann_explanation}. "
            f"Final: {final_score:.1f}"
        )
        
        return explanation
    
    def get_model_confidence(self, fuzzy_score, ann_score, movie_popularity):
        """
        Compute confidence score for the hybrid prediction
        
        Args:
            fuzzy_score (float): Fuzzy score
            ann_score (float): ANN score
            movie_popularity (float): Movie popularity
            
        Returns:
            float: Confidence score (0-1)
        """
        # Agreement between models
        score_diff = abs(fuzzy_score - ann_score)
        agreement = 1.0 - (score_diff / 10.0)  # Normalize to 0-1
        
        # Movie popularity factor (more popular = more confident)
        popularity_factor = movie_popularity / 100.0
        
        # Combined confidence
        confidence = 0.7 * agreement + 0.3 * popularity_factor
        
        return np.clip(confidence, 0, 1)
    
    def explain_recommendation(self, prediction_result):
        """
        Generate detailed explanation for a recommendation
        
        Args:
            prediction_result (dict): Prediction result from predict_single_movie
            
        Returns:
            dict: Detailed explanation components
        """
        fuzzy_score = prediction_result['fuzzy_score']
        ann_score = prediction_result['ann_score']
        final_score = prediction_result['final_score']
        
        return {
            'fuzzy_component': {
                'score': fuzzy_score,
                'interpretation': self.numeric_to_linguistic(fuzzy_score),
                'explanation': prediction_result.get('fuzzy_explanation', '')
            },
            'ann_component': {
                'score': ann_score,
                'interpretation': self.numeric_to_linguistic(ann_score),
                'explanation': f"Neural network prediction based on user patterns"
            },
            'hybrid_result': {
                'score': final_score,
                'interpretation': self.numeric_to_linguistic(final_score),
                'method': prediction_result['method'],
                'combination': prediction_result.get('combination_explanation', '')
            },
            'overall_explanation': prediction_result['explanation']
        }


def main():
    """Example usage of hybrid recommender"""
    # This would typically be used with trained fuzzy and ANN models
    print("Hybrid Movie Recommender")
    print("This module combines fuzzy logic and ANN predictions")
    print("Use with trained fuzzy_model and ann_model instances")


if __name__ == '__main__':
    main()
