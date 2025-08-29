"""
Unit tests for ANN Collaborative Filtering Model
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.ann_model import ANNCollaborativeFilteringModel


class TestANNModel:
    """Test cases for ANN Collaborative Filtering Model"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        n_users, n_movies = 100, 50
        
        # Generate sample ratings
        user_ids = np.random.randint(0, n_users, 1000)
        movie_ids = np.random.randint(0, n_movies, 1000)
        ratings = np.random.uniform(1, 5, 1000)
        
        ratings_df = pd.DataFrame({
            'user_id': user_ids,
            'movie_id': movie_ids,
            'rating': ratings
        })
        
        return ratings_df, n_users, n_movies
    
    @pytest.fixture
    def ann_model(self, sample_data):
        """Create ANN model instance"""
        _, n_users, n_movies = sample_data
        return ANNCollaborativeFilteringModel(
            n_users=n_users,
            n_movies=n_movies,
            embedding_dim=8,
            hidden_dims=[16, 8],
            dropout_rate=0.2
        )
    
    def test_model_initialization(self, ann_model):
        """Test model initialization"""
        assert ann_model.n_users == 100
        assert ann_model.n_movies == 50
        assert ann_model.embedding_dim == 8
        assert ann_model.hidden_dims == [16, 8]
        assert ann_model.dropout_rate == 0.2
        assert ann_model.model is not None
    
    def test_model_architecture(self, ann_model):
        """Test model architecture"""
        model = ann_model.model
        
        # Check input shapes
        assert len(model.inputs) == 2
        assert model.inputs[0].shape[1:] == ()  # user_id input
        assert model.inputs[1].shape[1:] == ()  # movie_id input
        
        # Check output shape
        assert model.outputs[0].shape[1:] == (1,)
    
    def test_prepare_training_data(self, ann_model, sample_data):
        """Test training data preparation"""
        ratings_df, _, _ = sample_data
        
        X, y = ann_model.prepare_training_data(ratings_df)
        
        assert len(X) == 2  # user_ids and movie_ids
        assert len(X[0]) == len(ratings_df)
        assert len(X[1]) == len(ratings_df)
        assert len(y) == len(ratings_df)
        
        # Check data types
        assert X[0].dtype == np.int32
        assert X[1].dtype == np.int32
        assert y.dtype == np.float32
    
    def test_train_model(self, ann_model, sample_data):
        """Test model training"""
        ratings_df, _, _ = sample_data
        
        # Mock the model fit method to avoid actual training
        with patch.object(ann_model.model, 'fit') as mock_fit:
            mock_fit.return_value = MagicMock()
            mock_fit.return_value.history = {'loss': [1.0, 0.8, 0.6]}
            
            history = ann_model.train(ratings_df, epochs=3, batch_size=32, validation_split=0.2)
            
            # Check that fit was called
            mock_fit.assert_called_once()
            assert 'loss' in history.history
    
    def test_predict_batch(self, ann_model):
        """Test batch prediction"""
        user_ids = [1, 2, 3]
        movie_ids = [10, 20, 30]
        
        # Mock the model predict method
        with patch.object(ann_model.model, 'predict') as mock_predict:
            mock_predict.return_value = np.array([[4.5], [3.2], [4.8]])
            
            predictions = ann_model.predict_batch(user_ids, movie_ids)
            
            assert len(predictions) == 3
            assert all(isinstance(p, float) for p in predictions)
            mock_predict.assert_called_once()
    
    def test_predict_for_user(self, ann_model):
        """Test user-specific predictions"""
        user_id = 1
        movie_ids = [10, 20, 30, 40, 50]
        
        # Mock the model predict method
        with patch.object(ann_model.model, 'predict') as mock_predict:
            mock_predict.return_value = np.array([[4.5], [3.2], [4.8], [2.1], [3.9]])
            
            top_movies = ann_model.predict_for_user(user_id, movie_ids, top_k=3)
            
            assert len(top_movies) == 3
            assert all('movie_id' in movie and 'predicted_rating' in movie for movie in top_movies)
            
            # Check that movies are sorted by predicted rating (descending)
            ratings = [movie['predicted_rating'] for movie in top_movies]
            assert ratings == sorted(ratings, reverse=True)
    
    def test_evaluate_model(self, ann_model, sample_data):
        """Test model evaluation"""
        ratings_df, _, _ = sample_data
        
        # Mock the model evaluate method
        with patch.object(ann_model.model, 'evaluate') as mock_evaluate:
            mock_evaluate.return_value = [1.2, 0.8]  # [loss, mae]
            
            X, y = ann_model.prepare_training_data(ratings_df)
            metrics = ann_model.evaluate(X, y)
            
            assert 'mse' in metrics
            assert 'mae' in metrics
            assert 'rmse' in metrics
            mock_evaluate.assert_called_once()
    
    def test_save_and_load_model(self, ann_model):
        """Test model saving and loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, 'test_model')
            
            # Mock the model save method
            with patch.object(ann_model.model, 'save_weights') as mock_save:
                ann_model.save_model(model_path)
                mock_save.assert_called_once()
            
            # Test loading
            with patch.object(ann_model.model, 'load_weights') as mock_load:
                ann_model.load_model(model_path)
                mock_load.assert_called_once()
    
    def test_get_user_embedding(self, ann_model):
        """Test user embedding extraction"""
        user_id = 5
        
        # Mock the embedding layer
        with patch.object(ann_model.model, 'get_layer') as mock_get_layer:
            mock_embedding_layer = MagicMock()
            mock_embedding_layer.get_weights.return_value = [np.random.rand(100, 8)]
            mock_get_layer.return_value = mock_embedding_layer
            
            embedding = ann_model.get_user_embedding(user_id)
            
            assert embedding.shape == (8,)  # embedding_dim
    
    def test_get_movie_embedding(self, ann_model):
        """Test movie embedding extraction"""
        movie_id = 15
        
        # Mock the embedding layer
        with patch.object(ann_model.model, 'get_layer') as mock_get_layer:
            mock_embedding_layer = MagicMock()
            mock_embedding_layer.get_weights.return_value = [np.random.rand(50, 8)]
            mock_get_layer.return_value = mock_embedding_layer
            
            embedding = ann_model.get_movie_embedding(movie_id)
            
            assert embedding.shape == (8,)  # embedding_dim
    
    def test_prediction_bounds(self, ann_model):
        """Test that predictions are within expected bounds"""
        user_ids = [1, 2, 3]
        movie_ids = [10, 20, 30]
        
        # Mock realistic predictions
        with patch.object(ann_model.model, 'predict') as mock_predict:
            mock_predict.return_value = np.array([[4.5], [3.2], [4.8]])
            
            predictions = ann_model.predict_batch(user_ids, movie_ids)
            
            # Predictions should be between 0 and 10 (scaled output)
            assert all(0 <= p <= 10 for p in predictions)
    
    def test_empty_input_handling(self, ann_model):
        """Test handling of empty inputs"""
        predictions = ann_model.predict_batch([], [])
        assert len(predictions) == 0
        
        top_movies = ann_model.predict_for_user(1, [], top_k=5)
        assert len(top_movies) == 0


class TestANNModelIntegration:
    """Integration tests for ANN model"""
    
    def test_full_training_pipeline(self):
        """Test complete training pipeline with mock data"""
        # Create small dataset
        np.random.seed(42)
        ratings_data = {
            'user_id': [0, 0, 1, 1, 2, 2] * 10,
            'movie_id': [0, 1, 0, 2, 1, 2] * 10,
            'rating': np.random.uniform(1, 5, 60)
        }
        ratings_df = pd.DataFrame(ratings_data)
        
        # Initialize model
        model = ANNCollaborativeFilteringModel(
            n_users=3,
            n_movies=3,
            embedding_dim=4,
            hidden_dims=[8],
            dropout_rate=0.1
        )
        
        # Mock training to avoid actual computation
        with patch.object(model.model, 'fit') as mock_fit:
            mock_fit.return_value = MagicMock()
            mock_fit.return_value.history = {'loss': [1.0, 0.5]}
            
            # Train model
            history = model.train(ratings_df, epochs=2, batch_size=16)
            
            # Verify training was called
            assert mock_fit.called
            assert 'loss' in history.history
    
    def test_recommendation_consistency(self):
        """Test that recommendations are consistent"""
        model = ANNCollaborativeFilteringModel(
            n_users=10,
            n_movies=10,
            embedding_dim=4
        )
        
        user_id = 1
        movie_ids = list(range(10))
        
        # Mock consistent predictions
        with patch.object(model.model, 'predict') as mock_predict:
            mock_predict.return_value = np.array([[i] for i in range(10)])
            
            # Get recommendations twice
            recs1 = model.predict_for_user(user_id, movie_ids, top_k=5)
            recs2 = model.predict_for_user(user_id, movie_ids, top_k=5)
            
            # Should be identical
            assert recs1 == recs2


if __name__ == '__main__':
    pytest.main([__file__])
