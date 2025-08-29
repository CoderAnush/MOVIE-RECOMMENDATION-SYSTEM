"""
Fuzzy Logic Movie Recommendation System

This module implements a complete fuzzy inference system for movie recommendations
using Mamdani-style inference with triangular membership functions.

Fuzzy Rules Implementation:
==========================

A) User Preference vs. Genre Rules:
1. Action Genre:
   - IF Action preference is Very High AND Movie genre is Action THEN Recommendation Score is Very High
   - IF Action preference is High AND Movie genre is Action THEN Recommendation Score is High
   - IF Action preference is Medium AND Movie genre is Action THEN Recommendation Score is Medium
   - IF Action preference is Low AND Movie genre is Action THEN Recommendation Score is Low
   - IF Action preference is Very Low AND Movie genre is Action THEN Recommendation Score is Very Low

2. Comedy Genre:
   - IF Comedy preference is Very High AND Movie genre is Comedy THEN Recommendation Score is Very High
   - IF Comedy preference is High AND Movie genre is Comedy THEN Recommendation Score is High
   - IF Comedy preference is Medium AND Movie genre is Comedy THEN Recommendation Score is Medium
   - IF Comedy preference is Low AND Movie genre is Comedy THEN Recommendation Score is Low
   - IF Comedy preference is Very Low AND Movie genre is Comedy THEN Recommendation Score is Very Low

[Similar rules apply for Romance, Thriller, Sci-Fi, Drama, Horror genres]

B) Popularity & Genre Match Rules:
   - IF Popularity is High AND Genre Match is Excellent THEN Recommendation Score is Very High
   - IF Popularity is Medium AND Genre Match is Excellent THEN Recommendation Score is High
   - IF Popularity is Low AND Genre Match is Excellent THEN Recommendation Score is Medium
   - IF Popularity is High AND Genre Match is Average THEN Recommendation Score is High
   - IF Popularity is Medium AND Genre Match is Average THEN Recommendation Score is Medium
   - IF Popularity is Low AND Genre Match is Average THEN Recommendation Score is Low
   - IF Popularity is High AND Genre Match is Poor THEN Recommendation Score is Medium
   - IF Popularity is Medium AND Genre Match is Poor THEN Recommendation Score is Low
   - IF Popularity is Low AND Genre Match is Poor THEN Recommendation Score is Very Low

C) User Watch History Rules:
   - IF User has watched the movie AND Liked it THEN Recommendation Score is High for similar movies
   - IF User has watched the movie AND Disliked it THEN Recommendation Score is Very Low
   - IF User has not watched similar genre movies AND Preference is High THEN Recommendation Score is Medium
   - IF User has not watched similar genre movies AND Preference is Medium THEN Recommendation Score is Low
   - IF User has watched similar genre movies AND Mostly Liked them THEN Recommendation Score is High
   - IF User has watched similar genre movies AND Mostly Disliked them THEN Recommendation Score is Low
   - IF User has watched many movies in the genre AND Preference is Very High THEN Recommendation Score is Very High
   - IF User has watched many movies in the genre AND Preference is Low THEN Recommendation Score is Medium
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

def triangular(x, a, b, c):
    """
    Triangular membership function
    
    Args:
        x (float): Input value
        a (float): Left point
        b (float): Peak point
        c (float): Right point
        
    Returns:
        float: Membership degree (0-1)
    """
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)

class FuzzyMembershipFunctions:
    """Defines all membership functions for the fuzzy system"""
    
    @staticmethod
    def user_preference(x):
        """
        User preference membership functions (0-10 scale)
        
        Args:
            x (float): Input preference value
            
        Returns:
            dict: Membership degrees for each linguistic term
        """
        return {
            'Very Low': triangular(x, 0, 1, 2),
            'Low': triangular(x, 1, 2.5, 4),
            'Medium': triangular(x, 3, 5, 7),
            'High': triangular(x, 6, 7.5, 9),
            'Very High': triangular(x, 8, 9, 10)
        }
    
    @staticmethod
    def popularity(x):
        """
        Movie popularity membership functions (0-100 scale)
        
        Args:
            x (float): Input popularity value
            
        Returns:
            dict: Membership degrees for each linguistic term
        """
        return {
            'Low': triangular(x, 0, 20, 40),
            'Medium': triangular(x, 30, 50, 70),
            'High': triangular(x, 60, 80, 100)
        }
    
    @staticmethod
    def genre_match(x):
        """
        Genre match membership functions (0-1 scale)
        
        Args:
            x (float): Input genre match value
            
        Returns:
            dict: Membership degrees for each linguistic term
        """
        return {
            'Poor': triangular(x, 0, 0.2, 0.4),
            'Average': triangular(x, 0.3, 0.5, 0.7),
            'Excellent': triangular(x, 0.6, 0.8, 1.0)
        }
    
    @staticmethod
    def recommendation_score(x):
        """
        Recommendation score membership functions (0-10 scale)
        
        Args:
            x (float): Input recommendation score
            
        Returns:
            dict: Membership degrees for each linguistic term
        """
        return {
            'Very Low': triangular(x, 0, 1, 2),
            'Low': triangular(x, 1, 2.5, 4),
            'Medium': triangular(x, 3, 5, 7),
            'High': triangular(x, 6, 7.5, 9),
            'Very High': triangular(x, 8, 9, 10)
        }

class FuzzyRuleEngine:
    """Implements fuzzy rule evaluation and inference"""
    
    def __init__(self):
        """Initialize rule engine"""
        self.genres = ['Action', 'Comedy', 'Romance', 'Thriller', 'Sci-Fi', 'Drama', 'Horror']
        self.membership_functions = FuzzyMembershipFunctions()
        self.fired_rules = []
    
    def evaluate_genre_preference_rules(self, user_preferences, movie_genres, movie_id):
        """
        Evaluate genre preference rules for a movie
        
        Args:
            user_preferences (dict): User genre preferences
            movie_genres (list): Movie genres
            movie_id (int): Movie ID for explanation
            
        Returns:
            dict: Rule activations for each output linguistic term
        """
        rule_activations = {
            'Very Low': [],
            'Low': [],
            'Medium': [],
            'High': [],
            'Very High': []
        }
        
        # Convert preference levels to numeric values
        pref_mapping = {
            'Very Low': 1, 'Low': 2.5, 'Medium': 5, 'High': 7.5, 'Very High': 9
        }
        
        for genre in self.genres:
            if genre in movie_genres and genre in user_preferences:
                # Get numeric preference value
                pref_level = user_preferences[genre]
                pref_value = pref_mapping.get(pref_level, 5)
                
                # Get membership degrees for user preference
                pref_memberships = self.membership_functions.user_preference(pref_value)
                
                # Apply genre preference rules
                for pref_term, pref_degree in pref_memberships.items():
                    if pref_degree > 0:
                        # Rule: IF genre preference is X AND movie has genre THEN recommendation is X
                        activation = min(pref_degree, 1.0)  # Movie has genre = 1.0
                        rule_activations[pref_term].append(activation)
                        
                        # Record fired rule for explanation
                        self.fired_rules.append({
                            'rule_type': 'genre_preference',
                            'genre': genre,
                            'user_pref': pref_term,
                            'activation': activation,
                            'explanation': f"{genre} preference is {pref_term} and movie has {genre} genre"
                        })
        
        return rule_activations
    
    def evaluate_popularity_genre_match_rules(self, popularity, genre_match_score):
        """
        Evaluate popularity and genre match rules
        
        Args:
            popularity (float): Movie popularity (0-100)
            genre_match_score (float): Genre match score (0-1)
            
        Returns:
            dict: Rule activations for each output linguistic term
        """
        rule_activations = {
            'Very Low': [],
            'Low': [],
            'Medium': [],
            'High': [],
            'Very High': []
        }
        
        # Get membership degrees
        pop_memberships = self.membership_functions.popularity(popularity)
        genre_memberships = self.membership_functions.genre_match(genre_match_score)
        
        # Define popularity-genre match rules
        rules = [
            ('High', 'Excellent', 'Very High'),
            ('Medium', 'Excellent', 'High'),
            ('Low', 'Excellent', 'Medium'),
            ('High', 'Average', 'High'),
            ('Medium', 'Average', 'Medium'),
            ('Low', 'Average', 'Low'),
            ('High', 'Poor', 'Medium'),
            ('Medium', 'Poor', 'Low'),
            ('Low', 'Poor', 'Very Low')
        ]
        
        for pop_term, genre_term, output_term in rules:
            pop_degree = pop_memberships.get(pop_term, 0)
            genre_degree = genre_memberships.get(genre_term, 0)
            
            if pop_degree > 0 and genre_degree > 0:
                activation = min(pop_degree, genre_degree)
                rule_activations[output_term].append(activation)
                
                # Record fired rule for explanation
                self.fired_rules.append({
                    'rule_type': 'popularity_genre',
                    'popularity': pop_term,
                    'genre_match': genre_term,
                    'activation': activation,
                    'explanation': f"Popularity is {pop_term} and genre match is {genre_term}"
                })
        
        return rule_activations
    
    def evaluate_watch_history_rules(self, user_history, movie_genres, similar_movies_liked):
        """
        Evaluate user watch history rules
        
        Args:
            user_history (dict): User's watch history statistics
            movie_genres (list): Current movie genres
            similar_movies_liked (float): Ratio of similar movies liked (0-1)
            
        Returns:
            dict: Rule activations for each output linguistic term
        """
        rule_activations = {
            'Very Low': [],
            'Low': [],
            'Medium': [],
            'High': [],
            'Very High': []
        }
        
        # Rule: If user has watched many movies in genre and mostly liked them
        for genre in movie_genres:
            if genre in user_history:
                genre_stats = user_history[genre]
                watched_count = genre_stats.get('watched_count', 0)
                liked_ratio = genre_stats.get('liked_ratio', 0)
                
                if watched_count >= 5:  # Many movies watched
                    if liked_ratio >= 0.7:  # Mostly liked
                        rule_activations['Very High'].append(0.9)
                        self.fired_rules.append({
                            'rule_type': 'watch_history',
                            'activation': 0.9,
                            'explanation': f"User watched many {genre} movies and liked most of them"
                        })
                    elif liked_ratio <= 0.3:  # Mostly disliked
                        rule_activations['Low'].append(0.8)
                        self.fired_rules.append({
                            'rule_type': 'watch_history',
                            'activation': 0.8,
                            'explanation': f"User watched many {genre} movies but disliked most"
                        })
                elif watched_count >= 2:  # Some movies watched
                    if liked_ratio >= 0.6:
                        rule_activations['High'].append(0.7)
                        self.fired_rules.append({
                            'rule_type': 'watch_history',
                            'activation': 0.7,
                            'explanation': f"User liked similar {genre} movies before"
                        })
                    elif liked_ratio <= 0.4:
                        rule_activations['Low'].append(0.6)
                        self.fired_rules.append({
                            'rule_type': 'watch_history',
                            'activation': 0.6,
                            'explanation': f"User disliked similar {genre} movies before"
                        })
        
        return rule_activations
    
    def aggregate_rule_activations(self, *rule_activation_dicts):
        """
        Aggregate rule activations using max operator
        
        Args:
            *rule_activation_dicts: Variable number of rule activation dictionaries
            
        Returns:
            dict: Aggregated activations for each output term
        """
        aggregated = {
            'Very Low': 0,
            'Low': 0,
            'Medium': 0,
            'High': 0,
            'Very High': 0
        }
        
        for rule_dict in rule_activation_dicts:
            for term, activations in rule_dict.items():
                if activations:
                    aggregated[term] = max(aggregated[term], max(activations))
        
        return aggregated
    
    def defuzzify_centroid(self, aggregated_activations):
        """
        Defuzzify using centroid method
        
        Args:
            aggregated_activations (dict): Aggregated rule activations
            
        Returns:
            float: Crisp output value (0-10)
        """
        # Define output membership function centers
        centers = {
            'Very Low': 1,
            'Low': 2.5,
            'Medium': 5,
            'High': 7.5,
            'Very High': 9
        }
        
        numerator = 0
        denominator = 0
        
        for term, activation in aggregated_activations.items():
            if activation > 0:
                numerator += centers[term] * activation
                denominator += activation
        
        if denominator == 0:
            return 5.0  # Default medium score
        
        return numerator / denominator

class FuzzyMovieRecommender:
    """Main fuzzy recommendation system"""
    
    def __init__(self):
        """Initialize fuzzy recommender"""
        self.rule_engine = FuzzyRuleEngine()
        self.membership_functions = FuzzyMembershipFunctions()
    
    def compute_user_genre_history(self, user_ratings_history):
        """
        Compute user's genre-wise watch history statistics
        
        Args:
            user_ratings_history (pd.DataFrame): User's rating history
            
        Returns:
            dict: Genre-wise statistics
        """
        genre_stats = {}
        
        if user_ratings_history.empty:
            return genre_stats
        
        # Process each genre
        for _, row in user_ratings_history.iterrows():
            genres = row.get('genres', [])
            rating = row.get('rating', 3)
            liked = rating >= 4
            
            for genre in genres:
                if genre not in genre_stats:
                    genre_stats[genre] = {
                        'watched_count': 0,
                        'total_ratings': 0,
                        'liked_count': 0
                    }
                
                genre_stats[genre]['watched_count'] += 1
                genre_stats[genre]['total_ratings'] += rating
                if liked:
                    genre_stats[genre]['liked_count'] += 1
        
        # Compute ratios
        for genre in genre_stats:
            stats = genre_stats[genre]
            stats['avg_rating'] = stats['total_ratings'] / stats['watched_count']
            stats['liked_ratio'] = stats['liked_count'] / stats['watched_count']
        
        return genre_stats
    
    def predict_single_movie(self, user_preferences, movie_data, user_history=None):
        """
        Predict recommendation score for a single movie
        
        Args:
            user_preferences (dict): User genre preferences
            movie_data (dict): Movie information
            user_history (pd.DataFrame): User's rating history
            
        Returns:
            dict: Prediction result with score and explanation
        """
        # Reset fired rules
        self.rule_engine.fired_rules = []
        
        # Extract movie information
        movie_id = movie_data['movie_id']
        movie_genres = movie_data.get('genres', [])
        popularity = movie_data.get('popularity', 50)
        
        # Compute genre match score
        genre_match_score = self._compute_genre_match(user_preferences, movie_genres)
        
        # Compute user history statistics
        user_genre_history = {}
        if user_history is not None and not user_history.empty:
            user_genre_history = self.compute_user_genre_history(user_history)
        
        # Evaluate different rule sets
        genre_rules = self.rule_engine.evaluate_genre_preference_rules(
            user_preferences, movie_genres, movie_id
        )
        
        popularity_rules = self.rule_engine.evaluate_popularity_genre_match_rules(
            popularity, genre_match_score
        )
        
        history_rules = self.rule_engine.evaluate_watch_history_rules(
            user_genre_history, movie_genres, 0.5  # Default similar movies ratio
        )
        
        # Aggregate all rule activations
        aggregated = self.rule_engine.aggregate_rule_activations(
            genre_rules, popularity_rules, history_rules
        )
        
        # Defuzzify to get crisp score
        fuzzy_score = self.rule_engine.defuzzify_centroid(aggregated)
        
        # Generate explanation
        explanation = self._generate_explanation(
            self.rule_engine.fired_rules, fuzzy_score, movie_genres
        )
        
        return {
            'movie_id': movie_id,
            'fuzzy_score': round(fuzzy_score, 2),
            'genre_match_score': round(genre_match_score, 3),
            'fired_rules': self.rule_engine.fired_rules.copy(),
            'explanation': explanation,
            'aggregated_activations': aggregated
        }
    
    def predict_batch(self, user_preferences, movies_data, user_history=None):
        """
        Predict recommendation scores for multiple movies
        
        Args:
            user_preferences (dict): User genre preferences
            movies_data (list): List of movie dictionaries
            user_history (pd.DataFrame): User's rating history
            
        Returns:
            list: List of prediction results
        """
        results = []
        
        for movie_data in movies_data:
            try:
                result = self.predict_single_movie(
                    user_preferences, movie_data, user_history
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Error predicting for movie {movie_data.get('movie_id')}: {e}")
                # Add default result
                results.append({
                    'movie_id': movie_data.get('movie_id'),
                    'fuzzy_score': 5.0,
                    'genre_match_score': 0.0,
                    'fired_rules': [],
                    'explanation': "Error in fuzzy prediction",
                    'aggregated_activations': {}
                })
        
        return results
    
    def _compute_genre_match(self, user_preferences, movie_genres):
        """
        Compute genre match score between user preferences and movie
        
        Args:
            user_preferences (dict): User genre preferences
            movie_genres (list): Movie genres
            
        Returns:
            float: Genre match score (0-1)
        """
        if not movie_genres:
            return 0.0
        
        # Map preference levels to scores
        pref_mapping = {
            'Very Low': 0.0,
            'Low': 0.25,
            'Medium': 0.5,
            'High': 0.75,
            'Very High': 1.0
        }
        
        # Calculate weighted average of genre preferences
        total_score = 0
        matched_genres = 0
        
        for genre in movie_genres:
            if genre in user_preferences:
                pref_level = user_preferences[genre]
                score = pref_mapping.get(pref_level, 0.5)
                total_score += score
                matched_genres += 1
        
        if matched_genres == 0:
            return 0.0
        
        return total_score / matched_genres
    
    def _generate_explanation(self, fired_rules, fuzzy_score, movie_genres):
        """
        Generate human-readable explanation for the recommendation
        
        Args:
            fired_rules (list): List of fired rules
            fuzzy_score (float): Final fuzzy score
            movie_genres (list): Movie genres
            
        Returns:
            str: Explanation text
        """
        if not fired_rules:
            return f"Fuzzy score: {fuzzy_score:.1f} (default recommendation)"
        
        # Group rules by type
        genre_rules = [r for r in fired_rules if r['rule_type'] == 'genre_preference']
        popularity_rules = [r for r in fired_rules if r['rule_type'] == 'popularity_genre']
        history_rules = [r for r in fired_rules if r['rule_type'] == 'watch_history']
        
        explanation_parts = []
        
        # Genre preference explanation
        if genre_rules:
            top_genre_rule = max(genre_rules, key=lambda x: x['activation'])
            explanation_parts.append(
                f"Genre match: {top_genre_rule['explanation']}"
            )
        
        # Popularity explanation
        if popularity_rules:
            top_pop_rule = max(popularity_rules, key=lambda x: x['activation'])
            explanation_parts.append(
                f"Popularity: {top_pop_rule['explanation']}"
            )
        
        # History explanation
        if history_rules:
            top_history_rule = max(history_rules, key=lambda x: x['activation'])
            explanation_parts.append(
                f"History: {top_history_rule['explanation']}"
            )
        
        # Combine explanations
        if explanation_parts:
            explanation = "; ".join(explanation_parts)
        else:
            explanation = f"Moderate recommendation for {', '.join(movie_genres)} movie"
        
        return f"Fuzzy: {fuzzy_score:.1f} — {explanation}"


def main():
    """Example usage of fuzzy recommender"""
    # Initialize recommender
    recommender = FuzzyMovieRecommender()
    
    # Example user preferences
    user_preferences = {
        'Action': 'High',
        'Comedy': 'Medium',
        'Romance': 'Low',
        'Thriller': 'High',
        'Sci-Fi': 'Very High',
        'Drama': 'Medium',
        'Horror': 'Very Low'
    }
    
    # Example movie
    movie_data = {
        'movie_id': 1,
        'title': 'Interstellar',
        'genres': ['Sci-Fi', 'Drama'],
        'popularity': 85
    }
    
    # Get prediction
    result = recommender.predict_single_movie(user_preferences, movie_data)
    
    print(f"Movie: {movie_data['title']}")
    print(f"Fuzzy Score: {result['fuzzy_score']}")
    print(f"Explanation: {result['explanation']}")
    print(f"Fired Rules: {len(result['fired_rules'])}")


if __name__ == '__main__':
    main()
