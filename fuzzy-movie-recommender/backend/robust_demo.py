"""
Robust Demo Server - Fuzzy Movie Recommendation System
Enhanced error handling and debugging
"""

import json
import random
import math
import traceback
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

# Simple fuzzy logic implementation
class SimpleFuzzyRecommender:
    def __init__(self):
        self.genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller', 'Adventure']
    
    def triangular_membership(self, x, a, b, c):
        """Triangular membership function"""
        try:
            if x <= a or x >= c:
                return 0.0
            elif a < x <= b:
                return (x - a) / (b - a)
            else:
                return (c - x) / (c - b)
        except:
            return 0.0
    
    def predict_movie(self, user_preferences, movie_data):
        """Predict score for a single movie using fuzzy logic"""
        try:
            movie_genres = movie_data.get('genres', [])
            
            # Calculate genre match score
            genre_scores = []
            for genre in movie_genres:
                if genre in user_preferences:
                    pref_score = float(user_preferences[genre])
                    # Apply triangular membership functions
                    low_mem = self.triangular_membership(pref_score, 0, 0, 5)
                    med_mem = self.triangular_membership(pref_score, 3, 5, 7)
                    high_mem = self.triangular_membership(pref_score, 5, 10, 10)
                    
                    # Simple rule: if high preference, boost score
                    if high_mem > 0.5:
                        genre_scores.append(8.0 + random.uniform(0, 1.5))
                    elif med_mem > 0.5:
                        genre_scores.append(6.0 + random.uniform(0, 2))
                    else:
                        genre_scores.append(4.0 + random.uniform(0, 2))
            
            if not genre_scores:
                base_score = 5.0
            else:
                base_score = sum(genre_scores) / len(genre_scores)
            
            # Add some randomness and popularity factor
            popularity_factor = movie_data.get('popularity', 50) / 100.0
            final_score = base_score * (0.8 + 0.2 * popularity_factor) + random.uniform(-0.5, 0.5)
            final_score = max(1.0, min(10.0, final_score))  # Clamp between 1-10
            
            return {
                'movie_id': movie_data['movie_id'],
                'title': movie_data['title'],
                'genres': movie_genres,
                'fuzzy_score': round(final_score, 2),
                'ann_score': round(final_score + random.uniform(-1, 1), 2),
                'final_score': round(final_score, 2),
                'explanation': f"Genre match for {', '.join(movie_genres)} with your preferences"
            }
        except Exception as e:
            print(f"Error in predict_movie: {e}")
            return {
                'movie_id': movie_data.get('movie_id', 0),
                'title': movie_data.get('title', 'Unknown'),
                'genres': [],
                'fuzzy_score': 5.0,
                'ann_score': 5.0,
                'final_score': 5.0,
                'explanation': 'Error in prediction'
            }

# Sample movie data
SAMPLE_MOVIES = [
    {'movie_id': 1, 'title': 'Action Hero', 'genres': ['Action', 'Adventure'], 'popularity': 85},
    {'movie_id': 2, 'title': 'Funny Business', 'genres': ['Comedy'], 'popularity': 70},
    {'movie_id': 3, 'title': 'Love Story', 'genres': ['Romance', 'Drama'], 'popularity': 60},
    {'movie_id': 4, 'title': 'Space Wars', 'genres': ['Sci-Fi', 'Action'], 'popularity': 90},
    {'movie_id': 5, 'title': 'Horror Night', 'genres': ['Horror', 'Thriller'], 'popularity': 55},
    {'movie_id': 6, 'title': 'Comedy Gold', 'genres': ['Comedy'], 'popularity': 75},
    {'movie_id': 7, 'title': 'Drama Queen', 'genres': ['Drama'], 'popularity': 65},
    {'movie_id': 8, 'title': 'Thriller Chase', 'genres': ['Thriller', 'Action'], 'popularity': 80},
    {'movie_id': 9, 'title': 'Romantic Comedy', 'genres': ['Romance', 'Comedy'], 'popularity': 70},
    {'movie_id': 10, 'title': 'Adventure Quest', 'genres': ['Adventure', 'Action'], 'popularity': 85}
]

# Initialize recommender
recommender = SimpleFuzzyRecommender()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    allow_reuse_address = True

class MovieRecommendationHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        try:
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        except Exception as e:
            print(f"Error setting headers: {e}")
    
    def do_OPTIONS(self):
        try:
            self._set_headers()
        except Exception as e:
            print(f"Error in OPTIONS: {e}")
    
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            print(f"GET request: {path}")
            
            if path == '/' or path == '/api/health':
                self._set_headers()
                response = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0-robust-demo',
                    'message': 'Fuzzy Movie Recommendation System is running!'
                }
                self.wfile.write(json.dumps(response, indent=2).encode())
            
            elif path.startswith('/api/movie/'):
                try:
                    movie_id = int(path.split('/')[-1])
                    movie = next((m for m in SAMPLE_MOVIES if m['movie_id'] == movie_id), None)
                    
                    if movie:
                        self._set_headers()
                        self.wfile.write(json.dumps(movie, indent=2).encode())
                    else:
                        self._set_headers(404)
                        self.wfile.write(json.dumps({'error': 'Movie not found'}).encode())
                except ValueError:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'Invalid movie ID'}).encode())
            
            elif path == '/api/genres':
                self._set_headers()
                all_genres = set()
                for movie in SAMPLE_MOVIES:
                    all_genres.update(movie['genres'])
                response = {'genres': sorted(list(all_genres))}
                self.wfile.write(json.dumps(response, indent=2).encode())
            
            elif path == '/api/stats':
                self._set_headers()
                response = {
                    'total_movies': len(SAMPLE_MOVIES),
                    'total_ratings': 1000,
                    'total_users': 50,
                    'mode': 'robust-demo'
                }
                self.wfile.write(json.dumps(response, indent=2).encode())
            
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': f'Endpoint not found: {path}'}).encode())
                
        except Exception as e:
            print(f"Error in GET handler: {e}")
            traceback.print_exc()
            try:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': f'Server error: {str(e)}'}).encode())
            except:
                pass
    
    def do_POST(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            print(f"POST request: {path}")
            
            if path == '/api/user/preferences':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    user_preferences = data.get('user_preferences', {})
                    top_k = min(int(data.get('top_k', 5)), len(SAMPLE_MOVIES))
                    
                    print(f"User preferences: {user_preferences}")
                    
                    if not user_preferences:
                        self._set_headers(400)
                        self.wfile.write(json.dumps({'error': 'user_preferences required'}).encode())
                        return
                    
                    # Get recommendations
                    recommendations = []
                    for movie in SAMPLE_MOVIES:
                        prediction = recommender.predict_movie(user_preferences, movie)
                        recommendations.append(prediction)
                    
                    # Sort by score and take top_k
                    recommendations.sort(key=lambda x: x['final_score'], reverse=True)
                    recommendations = recommendations[:top_k]
                    
                    response = {
                        'recommendations': recommendations,
                        'total_movies_considered': len(SAMPLE_MOVIES),
                        'user_preferences': user_preferences,
                        'processing_time': 0.1
                    }
                    
                    self._set_headers()
                    self.wfile.write(json.dumps(response, indent=2).encode())
                    print(f"Sent {len(recommendations)} recommendations")
                    
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
            
            elif path == '/api/train/ann':
                self._set_headers()
                response = {
                    'status': 'success',
                    'message': 'Training completed (demo mode)',
                    'training_history': {'loss': [1.0, 0.8, 0.6]}
                }
                self.wfile.write(json.dumps(response, indent=2).encode())
            
            elif path == '/api/train/fuzzy':
                self._set_headers()
                response = {
                    'status': 'success',
                    'message': 'Fuzzy model re-initialized'
                }
                self.wfile.write(json.dumps(response, indent=2).encode())
            
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': f'Endpoint not found: {path}'}).encode())
                
        except Exception as e:
            print(f"Error in POST handler: {e}")
            traceback.print_exc()
            try:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': f'Server error: {str(e)}'}).encode())
            except:
                pass
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def run_server(port=5000):
    try:
        server_address = ('', port)
        httpd = ThreadedHTTPServer(server_address, MovieRecommendationHandler)
        
        print("=" * 60)
        print("🚀 FUZZY MOVIE RECOMMENDATION SYSTEM - ROBUST DEMO")
        print("=" * 60)
        print(f"🌐 Server URL: http://localhost:{port}")
        print(f"🏥 Health Check: http://localhost:{port}/api/health")
        print(f"📊 Stats: http://localhost:{port}/api/stats")
        print(f"🎬 Genres: http://localhost:{port}/api/genres")
        print(f"📱 Frontend: Open frontend/index.html in your browser")
        print("=" * 60)
        print(f"📈 Loaded {len(SAMPLE_MOVIES)} sample movies")
        print(f"🎯 Available genres: {', '.join(recommender.genres)}")
        print("=" * 60)
        print("🔥 Server is running! Press Ctrl+C to stop")
        print("=" * 60)
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        httpd.server_close()
    except Exception as e:
        print(f"❌ Server error: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    run_server()
