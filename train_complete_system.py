"""
Complete Training Pipeline for ANN + Hybrid System
==================================================

This script trains the ANN model on the preprocessed MovieLens data
and then demonstrates the complete hybrid recommendation system.
"""

import os
import sys
import pandas as pd
import numpy as np
from models.ann_model import train_ann_model, ANNMoviePredictor
from models.hybrid_system import HybridRecommendationSystem
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_ann_training_demo(sample_size=5000):
    """
    Quick demo of ANN training with a small sample.
    
    Args:
        sample_size: Number of samples to use for training
    """
    print("🚀 QUICK ANN TRAINING DEMO")
    print("=" * 50)
    
    # Check if preprocessed data exists
    csv_path = "processed/preprocessed_movielens10M.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Training data not found at {csv_path}")
        print("Please run the data preprocessing script first.")
        return None
    
    # Train ANN model with small sample
    logger.info(f"Training ANN with {sample_size} samples...")
    predictor = train_ann_model(
        csv_path=csv_path,
        sample_size=sample_size,
        test_size=0.2,
        model_name="ann_movie_predictor_demo"
    )
    
    return predictor

def test_hybrid_system():
    """Test the complete hybrid recommendation system."""
    print("\n🔄 HYBRID SYSTEM TESTING")
    print("=" * 50)
    
    # Create hybrid system
    hybrid_system = HybridRecommendationSystem("ann_movie_predictor_demo")
    
    # Test cases
    test_cases = [
        {
            'name': 'Action Movie Lover',
            'user_prefs': {
                'action': 9.5, 'comedy': 3.0, 'romance': 2.0, 'thriller': 8.0,
                'sci_fi': 7.5, 'drama': 4.0, 'horror': 2.5
            },
            'movie': {
                'title': 'Mad Max: Fury Road',
                'genres': ['Action', 'Thriller'],
                'popularity': 88,
                'year': 2015
            },
            'history': {'liked_ratio': 0.85, 'disliked_ratio': 0.10, 'watch_count': 32}
        },
        {
            'name': 'Romantic Comedy Fan',
            'user_prefs': {
                'action': 2.5, 'comedy': 9.0, 'romance': 8.5, 'thriller': 3.0,
                'sci_fi': 4.0, 'drama': 6.5, 'horror': 1.0
            },
            'movie': {
                'title': 'The Princess Bride',
                'genres': ['Comedy', 'Romance'],
                'popularity': 92,
                'year': 1987
            },
            'history': {'liked_ratio': 0.70, 'disliked_ratio': 0.15, 'watch_count': 18}
        },
        {
            'name': 'Sci-Fi Enthusiast',
            'user_prefs': {
                'action': 7.0, 'comedy': 5.0, 'romance': 3.0, 'thriller': 6.5,
                'sci_fi': 9.5, 'drama': 6.0, 'horror': 4.0
            },
            'movie': {
                'title': 'Blade Runner 2049',
                'genres': ['Sci-Fi', 'Drama', 'Thriller'],
                'popularity': 78,
                'year': 2017
            },
            'history': {'liked_ratio': 0.78, 'disliked_ratio': 0.12, 'watch_count': 45}
        },
        {
            'name': 'New User (Limited History)',
            'user_prefs': {
                'action': 6.0, 'comedy': 7.0, 'romance': 5.0, 'thriller': 5.5,
                'sci_fi': 6.5, 'drama': 5.5, 'horror': 3.0
            },
            'movie': {
                'title': 'The Avengers',
                'genres': ['Action', 'Sci-Fi'],
                'popularity': 95,
                'year': 2012
            },
            'history': {'liked_ratio': 0.60, 'disliked_ratio': 0.20, 'watch_count': 5}
        }
    ]
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        # Get recommendation
        result = hybrid_system.recommend(
            user_preferences=test_case['user_prefs'],
            movie_info=test_case['movie'],
            watch_history=test_case['history'],
            combination_strategy='adaptive'
        )
        
        # Display results
        print(f"🎬 Movie: {test_case['movie']['title']} ({test_case['movie']['year']})")
        print(f"   Genres: {', '.join(test_case['movie']['genres'])}")
        print(f"   Popularity: {test_case['movie']['popularity']}")
        
        print(f"\n📊 Scores:")
        print(f"   Fuzzy: {result['fuzzy_score']:.2f}/10")
        if 'ann_score' in result:
            print(f"   ANN: {result['ann_score']:.2f}/10")
        if 'hybrid_score' in result:
            print(f"   Hybrid: {result['hybrid_score']:.2f}/10")
        
        # Get recommendation level
        final_score = result.get('hybrid_score', result['fuzzy_score'])
        if final_score >= 8:
            level = "🔥 Highly Recommended"
        elif final_score >= 6:
            level = "👍 Recommended"
        elif final_score >= 4:
            level = "🤔 Maybe"
        else:
            level = "👎 Not Recommended"
        
        print(f"\n🎯 Recommendation: {level}")
        
        # Test strategy comparison for first case
        if i == 1:
            print(f"\n🔍 Strategy Comparison for {test_case['name']}:")
            comparison = hybrid_system.compare_strategies(
                test_case['user_prefs'], test_case['movie'], test_case['history']
            )
            
            for strategy, res in comparison.items():
                score = res.get('hybrid_score', res['fuzzy_score'])
                print(f"   {strategy.replace('_', ' ').title()}: {score:.2f}")

def demonstrate_system_capabilities():
    """Demonstrate the full capabilities of the system."""
    print("\n🎯 SYSTEM CAPABILITIES DEMONSTRATION")
    print("=" * 60)
    
    capabilities = [
        "✅ Fuzzy Logic Recommendation Engine",
        "   • User preference vs genre matching",
        "   • Popularity and genre match rules",
        "   • Watch history sentiment analysis", 
        "   • Triangular membership functions",
        "",
        "✅ Artificial Neural Network Predictor",
        "   • Dense feed-forward architecture",
        "   • 18+ engineered features",
        "   • Regression output (0-10 scale)",
        "   • Dropout regularization",
        "",
        "✅ Hybrid Recommendation System",
        "   • Multiple combination strategies",
        "   • Adaptive weighting based on context",
        "   • Confidence-based adjustments",
        "   • Batch processing support",
        "",
        "✅ Advanced Features",
        "   • Strategy comparison tools",
        "   • Detailed explanations",
        "   • Model persistence",
        "   • Comprehensive evaluation metrics"
    ]
    
    for capability in capabilities:
        print(capability)
    
    print("\n💡 Integration Ready:")
    print("   • Web API endpoints")
    print("   • Real-time recommendations")
    print("   • User preference learning")
    print("   • A/B testing support")

def run_complete_demo():
    """Run the complete demonstration."""
    print("🎬 COMPLETE ANN + HYBRID RECOMMENDATION SYSTEM")
    print("=" * 70)
    
    try:
        # Step 1: Quick ANN training
        predictor = quick_ann_training_demo(sample_size=5000)
        
        if predictor is None:
            print("❌ Could not complete ANN training demo")
            return
        
        # Step 2: Test hybrid system
        test_hybrid_system()
        
        # Step 3: Show capabilities
        demonstrate_system_capabilities()
        
        print("\n" + "=" * 70)
        print("✅ COMPLETE SYSTEM DEMONSTRATION FINISHED!")
        print("🚀 The hybrid recommendation system is ready for deployment!")
        print("💻 Integration points:")
        print("   • models/fuzzy_model.py - Fuzzy logic engine")
        print("   • models/ann_model.py - Neural network predictor")
        print("   • models/hybrid_system.py - Complete hybrid system")
        print("   • integration_demo.py - Data integration example")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_complete_demo()