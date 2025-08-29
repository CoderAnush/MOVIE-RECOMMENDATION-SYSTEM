"""
Unit tests for Flask API endpoints
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app


class TestFlaskAPI:
    """Test cases for Flask API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
    
    def test_user_preferences_endpoint_success(self, client):
        """Test successful user preferences request"""
        request_data = {
            'user_preferences': {
                'Action': 8,
                'Comedy': 6,
                'Drama': 7
            },
            'watched_movies': ['Toy Story', 'Forrest Gump'],
            'top_k': 5
        }
        
        # Mock the recommendation models
        with patch('app.hybrid_model') as mock_hybrid, \
             patch('app.fuzzy_model') as mock_fuzzy, \
             patch('app.ann_model') as mock_ann:
            
            # Mock hybrid model response
            mock_hybrid.predict_batch.return_value = [
                {
                    'movie_id': 1,
                    'title': 'Test Movie 1',
                    'genres': ['Action'],
                    'final_score': 8.5,
                    'fuzzy_score': 8.0,
                    'ann_score': 9.0,
                    'explanation': 'Great action movie'
                }
            ]
            
            response = client.post('/api/user/preferences',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'recommendations' in data
            assert len(data['recommendations']) >= 1
    
    def test_user_preferences_endpoint_missing_data(self, client):
        """Test user preferences endpoint with missing data"""
        request_data = {
            'watched_movies': ['Toy Story']
            # Missing user_preferences
        }
        
        response = client.post('/api/user/preferences',
                             data=json.dumps(request_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_user_preferences_endpoint_invalid_json(self, client):
        """Test user preferences endpoint with invalid JSON"""
        response = client.post('/api/user/preferences',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_movie_details_endpoint_success(self, client):
        """Test successful movie details request"""
        movie_id = 1
        
        with patch('app.movies_df') as mock_movies_df:
            # Mock movie data
            mock_movies_df.__getitem__.return_value = {
                'movie_id': movie_id,
                'title': 'Test Movie',
                'genres': ['Action', 'Adventure'],
                'year': 1995,
                'popularity': 75.5
            }
            mock_movies_df.get.return_value = mock_movies_df.__getitem__.return_value
            
            response = client.get(f'/api/movie/{movie_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['movie_id'] == movie_id
            assert data['title'] == 'Test Movie'
    
    def test_movie_details_endpoint_not_found(self, client):
        """Test movie details endpoint with non-existent movie"""
        movie_id = 99999
        
        with patch('app.movies_df') as mock_movies_df:
            mock_movies_df.get.return_value = None
            
            response = client.get(f'/api/movie/{movie_id}')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_train_ann_endpoint(self, client):
        """Test ANN training endpoint"""
        with patch('app.ann_model') as mock_ann:
            mock_ann.train.return_value = MagicMock()
            mock_ann.train.return_value.history = {'loss': [1.0, 0.5]}
            
            response = client.post('/api/train/ann')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'training_history' in data
    
    def test_train_fuzzy_endpoint(self, client):
        """Test fuzzy model re-initialization endpoint"""
        with patch('app.fuzzy_model') as mock_fuzzy:
            mock_fuzzy.__init__ = MagicMock(return_value=None)
            
            response = client.post('/api/train/fuzzy')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_search_movies_endpoint(self, client):
        """Test movie search endpoint"""
        with patch('app.movies_df') as mock_movies_df:
            # Mock search results
            mock_movies_df.__getitem__.return_value = [
                {'movie_id': 1, 'title': 'Test Movie 1', 'genres': ['Action']},
                {'movie_id': 2, 'title': 'Test Movie 2', 'genres': ['Comedy']}
            ]
            
            response = client.get('/api/search?query=test&limit=10')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'movies' in data
    
    def test_genres_endpoint(self, client):
        """Test genres listing endpoint"""
        with patch('app.movies_df') as mock_movies_df:
            # Mock unique genres
            mock_movies_df['genres'].apply.return_value.sum.return_value = ['Action', 'Comedy', 'Drama']
            
            response = client.get('/api/genres')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'genres' in data
    
    def test_stats_endpoint(self, client):
        """Test statistics endpoint"""
        with patch('app.movies_df') as mock_movies_df, \
             patch('app.ratings_df') as mock_ratings_df:
            
            # Mock dataframe lengths
            mock_movies_df.__len__ = MagicMock(return_value=1000)
            mock_ratings_df.__len__ = MagicMock(return_value=50000)
            mock_ratings_df['user_id'].nunique.return_value = 500
            
            response = client.get('/api/stats')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'total_movies' in data
            assert 'total_ratings' in data
            assert 'total_users' in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/api/health')
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_error_handling_internal_error(self, client):
        """Test internal error handling"""
        with patch('app.hybrid_model') as mock_hybrid:
            mock_hybrid.predict_batch.side_effect = Exception("Internal error")
            
            request_data = {
                'user_preferences': {'Action': 8},
                'watched_movies': [],
                'top_k': 5
            }
            
            response = client.post('/api/user/preferences',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data


class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked models"""
        app = create_app()
        app.config['TESTING'] = True
        
        # Mock all models to avoid loading actual data
        with patch('app.hybrid_model'), \
             patch('app.fuzzy_model'), \
             patch('app.ann_model'), \
             patch('app.movies_df'), \
             patch('app.ratings_df'):
            
            with app.test_client() as client:
                yield client
    
    def test_recommendation_workflow(self, client):
        """Test complete recommendation workflow"""
        # Mock models
        with patch('app.hybrid_model') as mock_hybrid, \
             patch('app.movies_df') as mock_movies:
            
            # Mock recommendation response
            mock_hybrid.predict_batch.return_value = [
                {
                    'movie_id': 1,
                    'title': 'Action Movie',
                    'genres': ['Action'],
                    'final_score': 8.5,
                    'fuzzy_score': 8.0,
                    'ann_score': 9.0,
                    'explanation': 'High action preference match'
                },
                {
                    'movie_id': 2,
                    'title': 'Comedy Movie',
                    'genres': ['Comedy'],
                    'final_score': 7.2,
                    'fuzzy_score': 7.0,
                    'ann_score': 7.4,
                    'explanation': 'Good comedy match'
                }
            ]
            
            # Test recommendation request
            request_data = {
                'user_preferences': {
                    'Action': 9,
                    'Comedy': 6,
                    'Drama': 5
                },
                'watched_movies': ['Toy Story', 'Forrest Gump'],
                'top_k': 2
            }
            
            response = client.post('/api/user/preferences',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify response structure
            assert 'recommendations' in data
            assert len(data['recommendations']) == 2
            
            # Verify first recommendation
            first_rec = data['recommendations'][0]
            assert first_rec['movie_id'] == 1
            assert first_rec['final_score'] == 8.5
            assert 'explanation' in first_rec
    
    def test_model_training_workflow(self, client):
        """Test model training workflow"""
        with patch('app.ann_model') as mock_ann, \
             patch('app.fuzzy_model') as mock_fuzzy:
            
            # Mock training responses
            mock_ann.train.return_value = MagicMock()
            mock_ann.train.return_value.history = {'loss': [1.0, 0.8, 0.6]}
            
            # Test ANN training
            response = client.post('/api/train/ann')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'training_history' in data
            
            # Test fuzzy re-initialization
            response = client.post('/api/train/fuzzy')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__])
