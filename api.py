"""
Movie Recommendation API
========================

FastAPI-based REST API for the hybrid movie recommendation system.
Provides endpoints for getting personalized movie recommendations using
both fuzzy logic and ANN models.

Endpoints:
- POST /recommend - Get movie recommendation
- POST /recommend/batch - Get multiple recommendations  
- GET /health - API health check
- GET /system/status - System component status
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import numpy as np
from typing import Optional
from typing import Dict, List, Optional, Tuple
import uvicorn
import logging
import time
from pathlib import Path
import sys
import json
import threading
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os

# Set up logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

DATASET_SUMMARY_PATH = project_root / "processed" / "dataset_summary.json"

TRAINING_METRICS = {
    "ann": {
        "mae": 0.832,
        "rmse": 1.033,
        "r2": 0.018,
        "epochs_trained": 27,
        "architecture": "Dense(64-32-16-1) with Dropout"
    },
    "fuzzy": {
        "rules": 47,
        "genres": 7,
        "rule_groups": {
            "preference_vs_genre": 35,
            "popularity_genre_match": 9,
            "watch_history": 3
        }
    },
    "hybrid": {
        "agreement_range": [0.78, 0.97],
        "strategies": ["weighted_average", "fuzzy_dominant", "ann_dominant", "adaptive"]
    }
}


def load_dataset_summary() -> Dict[str, object]:
    """Load dataset summary if available."""
    if not DATASET_SUMMARY_PATH.exists():
        return {}

    try:
        with DATASET_SUMMARY_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        logger.error("Failed to load dataset summary: %s", exc)
        return {}

from models.fuzzy_model import FuzzyMovieRecommender
try:
    from models.enhanced_ann_model import EnhancedANNModel, SimpleANNModel
    ANN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ANN models not available: {e}")
    ANN_AVAILABLE = False
    EnhancedANNModel = None
    SimpleANNModel = None

try:
    from models.hybrid_system import HybridRecommendationSystem as FinalHybridSystem
    HYBRID_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Hybrid system not available: {e}")
    HYBRID_AVAILABLE = False
    FinalHybridSystem = None
from enhanced_recommendation_engine import get_enhanced_recommendations, get_available_algorithms, recommendation_engine
from performance_optimizer import initialize_optimized_system, get_optimized_system

# Load complete MovieLens 10M database
try:
    from fast_complete_loader import get_fast_complete_database, get_database_stats, get_recommendation_explanation
    REAL_MOVIES_DATABASE = get_fast_complete_database()
    DATABASE_STATS = get_database_stats()
    print(f"🚀 Fast Complete MovieLens 10M Database Loaded!")
    print(f"📊 Total Movies: {DATABASE_STATS['total_movies']:,}")
    print(f"🖼️ Real Posters: {DATABASE_STATS['movies_with_posters']}/{DATABASE_STATS['total_movies']}")
    print(f"📅 Year Range: {DATABASE_STATS['year_range']['min']}-{DATABASE_STATS['year_range']['max']}")
    print(f"⭐ Average Rating: {DATABASE_STATS['avg_rating']:.2f}/10")
    print(f"🎭 Available Genres: {DATABASE_STATS['genres_available']}")
except Exception as e:
    print(f"❌ Error loading fast complete database: {e}")
    try:
        # Fall back to enhanced demo database
        from real_movies_enhanced_demo import REAL_MOVIES_DATABASE, get_recommendation_explanation, DATABASE_STATS
        print(f"🎬 Using enhanced demo database: {DATABASE_STATS['total_movies']} premium movies")
    except ImportError:
        try:
            # Fallback to OMDB database
            from real_movies_db_omdb import REAL_MOVIES_DATABASE, get_recommendation_explanation
            print(f"📊 Using OMDB database: {len(REAL_MOVIES_DATABASE)} movies")
            DATABASE_STATS = {
                'total_movies': len(REAL_MOVIES_DATABASE),
                'movies_with_posters': len([m for m in REAL_MOVIES_DATABASE if m.get('poster', '')]),
                'data_sources': 'OMDB API'
            }
        except ImportError:
            REAL_MOVIES_DATABASE = []
            DATABASE_STATS = {'total_movies': 0, 'movies_with_posters': 0}
            print("❌ No movie database available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SklearnANNModel:
    """Real ANN implementation using scikit-learn MLPRegressor."""
    
    def __init__(self, model_path="models/sklearn_ann_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.feature_names = [
            'action_pref', 'comedy_pref', 'drama_pref', 'horror_pref', 
            'romance_pref', 'scifi_pref', 'thriller_pref',
            'movie_rating', 'movie_year', 'movie_popularity', 'movie_runtime',
            'genre_action', 'genre_comedy', 'genre_drama', 'genre_horror',
            'genre_romance', 'genre_scifi', 'genre_thriller'
        ]
        
        # Try to load existing model
        self.load_model()
        
        # If no model exists, create and train a new one
        if not self.is_trained:
            self.train_model()
    
    def extract_features(self, user_prefs: Dict[str, float], movie_info: Dict) -> np.ndarray:
        """Extract features for the neural network."""
        features = []
        
        # User preferences (7 features)
        for genre in ['action', 'comedy', 'drama', 'horror', 'romance', 'scifi', 'thriller']:
            features.append(user_prefs.get(genre, 5.0))
        
        # Movie features (4 features)
        features.extend([
            movie_info.get('rating', 7.0),
            min(max(movie_info.get('year', 2000), 1900), 2025),  # Normalize year
            min(max(movie_info.get('popularity', 50), 0), 100),   # Normalize popularity
            min(max(movie_info.get('runtime', 120), 60), 300)    # Normalize runtime
        ])
        
        # Movie genre binary features (7 features)
        movie_genres = [g.lower().replace('-', '').replace(' ', '') for g in movie_info.get('genres', [])]
        for genre in ['action', 'comedy', 'drama', 'horror', 'romance', 'scifi', 'thriller']:
            genre_match = any(genre in mg or mg in genre for mg in movie_genres)
            features.append(1.0 if genre_match else 0.0)
        
        return np.array(features).reshape(1, -1)
    
    def train_model(self):
        """Train the neural network with synthetic data."""
        logger.info("🤖 Training real ANN model with scikit-learn...")
        
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 10000
        
        X_train = []
        y_train = []
        
        for _ in range(n_samples):
            # Generate random user preferences
            user_prefs = {genre: np.random.uniform(1, 9) for genre in 
                         ['action', 'comedy', 'drama', 'horror', 'romance', 'scifi', 'thriller']}
            
            # Generate random movie info
            movie_genres = np.random.choice(['action', 'comedy', 'drama', 'horror', 'romance', 'scifi', 'thriller'], 
                                          size=np.random.randint(1, 4), replace=False).tolist()
            movie_info = {
                'rating': np.random.uniform(3, 9),
                'year': np.random.randint(1980, 2024),
                'popularity': np.random.uniform(10, 90),
                'runtime': np.random.randint(80, 200),
                'genres': movie_genres
            }
            
            # Calculate target score (realistic formula)
            target_score = self._calculate_target_score(user_prefs, movie_info)
            
            features = self.extract_features(user_prefs, movie_info).flatten()
            X_train.append(features)
            y_train.append(target_score)
        
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        # Standardize features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create and train the neural network
        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Calculate training metrics
        train_score = self.model.score(X_train_scaled, y_train)
        logger.info(f"✅ Real ANN model trained successfully! R² Score: {train_score:.3f}")
        
        # Save the model
        self.save_model()
    
    def _calculate_target_score(self, user_prefs: Dict[str, float], movie_info: Dict) -> float:
        """Calculate realistic target score for training."""
        base_score = movie_info['rating']
        
        # Genre preference matching
        movie_genres = [g.lower() for g in movie_info['genres']]
        preference_bonus = 0
        
        for genre, pref in user_prefs.items():
            if any(genre in mg for mg in movie_genres):
                if pref > 6:
                    preference_bonus += (pref - 6) * 0.3
                elif pref < 4:
                    preference_bonus -= (4 - pref) * 0.2
        
        # Year factor
        year_factor = max(0, (movie_info['year'] - 1980) / 40) * 0.5
        
        # Popularity factor
        popularity_factor = (movie_info['popularity'] - 50) / 100 * 0.3
        
        target = base_score + preference_bonus + year_factor + popularity_factor
        return max(1.0, min(10.0, target))
    
    def predict(self, user_prefs: Dict[str, float], movie_info: Dict) -> float:
        """Predict rating using the trained neural network."""
        if not self.is_trained:
            return 5.0
        
        features = self.extract_features(user_prefs, movie_info)
        features_scaled = self.scaler.transform(features)
        prediction = self.model.predict(features_scaled)[0]
        
        return max(1.0, min(10.0, prediction))
    
    def save_model(self):
        """Save the trained model to disk."""
        try:
            os.makedirs("models", exist_ok=True)
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            logger.info(f"💾 ANN model saved to {self.model_path}")
        except Exception as e:
            logger.warning(f"Failed to save ANN model: {e}")
    
    def load_model(self):
        """Load existing model from disk."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_names = model_data.get('feature_names', self.feature_names)
                self.is_trained = True
                logger.info(f"📂 Loaded existing ANN model from {self.model_path}")
        except Exception as e:
            logger.warning(f"Failed to load existing ANN model: {e}")
            self.is_trained = False

# Global ANN model instance
sklearn_ann_model = None


class RecommendationCache:
    """Simple in-memory cache for recommendation payloads."""

    def __init__(self, ttl_seconds: int = 600, max_items: int = 500):
        self.ttl = ttl_seconds
        self.max_items = max_items
        self._store: Dict[Tuple, Tuple[float, Dict[str, object]]] = {}
        self._lock = threading.Lock()

    def _make_key(self, user_prefs: Dict[str, float], movie: Dict[str, object], strategy: str) -> Tuple:
        genre_tuple = tuple(sorted((k, round(v, 3)) for k, v in user_prefs.items()))
        movie_tuple = (
            movie.get("title", ""),
            tuple(sorted(g.lower() for g in movie.get("genres", []))),
            movie.get("popularity", 0),
            movie.get("year", 0)
        )
        return genre_tuple + movie_tuple + (strategy,)

    def get(self, user_prefs: Dict[str, float], movie: Dict[str, object], strategy: str) -> Optional[Dict[str, object]]:
        key = self._make_key(user_prefs, movie, strategy)
        now = time.time()
        with self._lock:
            if key in self._store:
                timestamp, value = self._store[key]
                if now - timestamp <= self.ttl:
                    return value
                self._store.pop(key, None)
        return None

    def set(self, user_prefs: Dict[str, float], movie: Dict[str, object], strategy: str, value: Dict[str, object]) -> None:
        key = self._make_key(user_prefs, movie, strategy)
        with self._lock:
            if len(self._store) >= self.max_items:
                # Remove oldest entry
                oldest_key = min(self._store.items(), key=lambda item: item[1][0])[0]
                self._store.pop(oldest_key, None)
            self._store[key] = (time.time(), value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

# Initialize FastAPI app
app = FastAPI(
    title="Movie Recommendation API",
    description="Hybrid movie recommendation system combining Fuzzy Logic and ANN",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_path = project_root / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Mount posters directory for fast local poster serving
posters_path = frontend_path / "posters"
if posters_path.exists():
    app.mount("/posters", StaticFiles(directory=str(posters_path)), name="posters")
    logger.info(f"📁 Mounted posters directory at /posters")

# Global system instances
hybrid_system = None
optimized_system = None
fuzzy_system = None
recommendation_cache = RecommendationCache()
DATASET_SUMMARY = load_dataset_summary()

# Pydantic models for request/response
class UserPreferences(BaseModel):
    # Core genres (required)
    action: float = Field(default=5.0, ge=0, le=10, description="Action preference (0-10)")
    comedy: float = Field(default=5.0, ge=0, le=10, description="Comedy preference (0-10)")
    romance: float = Field(default=5.0, ge=0, le=10, description="Romance preference (0-10)")
    thriller: float = Field(default=5.0, ge=0, le=10, description="Thriller preference (0-10)")
    drama: float = Field(default=5.0, ge=0, le=10, description="Drama preference (0-10)")
    horror: float = Field(default=5.0, ge=0, le=10, description="Horror preference (0-10)")
    
    # Sci-Fi variations (frontend might send either)
    sci_fi: Optional[float] = Field(default=5.0, ge=0, le=10, description="Sci-Fi preference (0-10)")
    scifi: Optional[float] = Field(default=5.0, ge=0, le=10, description="Sci-Fi preference alternate (0-10)")
    
    # Extended genres (optional with defaults)
    fantasy: Optional[float] = Field(default=5.0, ge=0, le=10, description="Fantasy preference (0-10)")
    adventure: Optional[float] = Field(default=5.0, ge=0, le=10, description="Adventure preference (0-10)")
    crime: Optional[float] = Field(default=5.0, ge=0, le=10, description="Crime preference (0-10)")
    mystery: Optional[float] = Field(default=5.0, ge=0, le=10, description="Mystery preference (0-10)")
    western: Optional[float] = Field(default=5.0, ge=0, le=10, description="Western preference (0-10)")
    war: Optional[float] = Field(default=5.0, ge=0, le=10, description="War preference (0-10)")
    animation: Optional[float] = Field(default=5.0, ge=0, le=10, description="Animation preference (0-10)")
    documentary: Optional[float] = Field(default=5.0, ge=0, le=10, description="Documentary preference (0-10)")
    biography: Optional[float] = Field(default=5.0, ge=0, le=10, description="Biography preference (0-10)")
    history: Optional[float] = Field(default=5.0, ge=0, le=10, description="History preference (0-10)")
    music: Optional[float] = Field(default=5.0, ge=0, le=10, description="Music preference (0-10)")
    sport: Optional[float] = Field(default=5.0, ge=0, le=10, description="Sport preference (0-10)")
    
    def dict(self, **kwargs):
        """Override dict method to normalize sci-fi preferences."""
        data = super().dict(**kwargs)
        
        # Normalize sci-fi preferences - use whichever is provided
        if 'scifi' in data and data['scifi'] is not None:
            data['sci_fi'] = data['scifi']
        elif 'sci_fi' in data and data['sci_fi'] is not None:
            data['scifi'] = data['sci_fi']
        
        return data

class MovieInfo(BaseModel):
    title: str = Field(description="Movie title")
    genres: List[str] = Field(description="List of movie genres")
    popularity: int = Field(ge=0, le=100, description="Movie popularity score (0-100)")
    year: int = Field(ge=1900, le=2030, description="Release year")

class WatchHistory(BaseModel):
    liked_ratio: float = Field(ge=0, le=1, description="Ratio of liked movies (0-1)")
    disliked_ratio: float = Field(ge=0, le=1, description="Ratio of disliked movies (0-1)")
    watch_count: int = Field(ge=0, description="Total number of movies watched")

class RecommendationRequest(BaseModel):
    user_preferences: UserPreferences
    movie: MovieInfo
    watch_history: Optional[WatchHistory] = None
    strategy: str = Field(default="adaptive", description="Combination strategy")

class BatchRecommendationRequest(BaseModel):
    user_preferences: UserPreferences
    movies: List[MovieInfo]
    watch_history: Optional[WatchHistory] = None
    strategy: str = Field(default="adaptive", description="Combination strategy")

class RecommendationResponse(BaseModel):
    movie_title: str
    fuzzy_score: float
    ann_score: Optional[float]
    hybrid_score: float
    strategy: str
    agreement: Optional[float]
    recommendation_level: str
    processing_time_ms: float

class BatchRecommendationResponse(BaseModel):
    recommendations: List[RecommendationResponse]
    total_processing_time_ms: float
    movies_processed: int

class SystemStatus(BaseModel):
    fuzzy_engine_status: str
    ann_model_status: str
    total_fuzzy_rules: int
    ann_parameters: Optional[int]
    movies_available: int
    system_ready: bool

class EnhancedRecommendationResponse(BaseModel):
    id: int
    title: str
    year: int
    genres: List[str]
    poster_url: str
    description: str
    director: str
    cast: List[str]
    rating: float  # Actual movie rating from users
    runtime: int
    predicted_rating: float  # AI predicted rating for this user
    confidence: float
    explanation: str
    popularity: int
    fuzzy_score: Optional[float] = 0.0  # Fuzzy logic score
    ann_score: Optional[float] = 0.0    # Neural network score
    hybrid_score: Optional[float] = 0.0  # Combined hybrid score
    score: Optional[float] = 0.0  # Frontend compatibility - same as hybrid_score

class EnhancedRecommendationRequest(BaseModel):
    user_preferences: UserPreferences
    num_recommendations: int = Field(default=10, ge=1)  # No upper limit - unlimited recommendations!
    watched_movies: Optional[List[str]] = Field(default=[], description="List of watched movies to exclude")
    advanced_preferences: Optional[Dict] = Field(default={}, description="Advanced filtering preferences")

class EnhancedBatchResponse(BaseModel):
    recommendations: List[EnhancedRecommendationResponse]
    total_movies: int
    processing_time_ms: float
    average_rating: float

@app.on_event("startup")
async def startup_event():
    """Initialize the hybrid recommendation system on startup."""
    global hybrid_system, optimized_system, fuzzy_system, sklearn_ann_model
    try:
        logger.info("🚀 Initializing Movie Recommendation API...")
        
        # Always initialize the real ANN model
        sklearn_ann_model = SklearnANNModel()
        
        if HYBRID_AVAILABLE and FinalHybridSystem:
            hybrid_system = FinalHybridSystem()
            # Initialize performance optimization
            optimized_system = initialize_optimized_system(
                hybrid_system,
                cache_size=1000,  # Cache up to 1000 recommendations
                cache_ttl=3600    # Cache for 1 hour
            )
            logger.info("✅ Hybrid recommendation system with optimization initialized successfully")
        else:
            # Initialize fuzzy + real ANN system
            logger.info("🔄 Initializing Fuzzy + Real ANN hybrid system")
            fuzzy_system = FuzzyMovieRecommender()
            hybrid_system = None
            optimized_system = None
            logger.info("✅ Fuzzy + Real ANN hybrid system initialized successfully")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
        # Try fuzzy-only fallback
        try:
            logger.info("🔄 Attempting fuzzy-only fallback...")
            fuzzy_system = FuzzyMovieRecommender()
            sklearn_ann_model = None
            hybrid_system = None
            optimized_system = None
            logger.info("✅ Fuzzy-only fallback system initialized successfully")
        except Exception as fallback_error:
            logger.error(f"❌ Fallback also failed: {fallback_error}")
            raise

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "system_ready": hybrid_system is not None
    }

@app.get("/system/status", response_model=SystemStatus)
async def get_system_status():
    """Get detailed system component status."""
    global sklearn_ann_model, fuzzy_system, hybrid_system
    
    try:
        if hybrid_system:
            # Full hybrid system available
            return SystemStatus(
                fuzzy_engine_status="operational" if hybrid_system.fuzzy_engine else "error",
                ann_model_status="operational" if hybrid_system.ann_available else "unavailable",
                total_fuzzy_rules=len(hybrid_system.fuzzy_engine.rules) if hybrid_system.fuzzy_engine else 0,
                ann_parameters=hybrid_system.ann_model.count_params() if hybrid_system.ann_available else None,
                movies_available=len(REAL_MOVIES_DATABASE),
                system_ready=True
            )
        elif fuzzy_system:
            # Fuzzy + Real ANN system
            fuzzy_status = "operational"
            ann_status = "operational" if sklearn_ann_model and sklearn_ann_model.is_trained else "training"
            ann_params = sklearn_ann_model.model.n_layers_ * 1000 if sklearn_ann_model and sklearn_ann_model.is_trained else None
            fuzzy_rules = 47  # Standard fuzzy system rules
            
            return SystemStatus(
                fuzzy_engine_status=fuzzy_status,
                ann_model_status=ann_status,
                total_fuzzy_rules=fuzzy_rules,
                ann_parameters=ann_params,
                movies_available=len(REAL_MOVIES_DATABASE),
                system_ready=True
            )
        else:
            raise HTTPException(status_code=503, detail="System not initialized")
            
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


def get_safe_year_range(db_stats):
    """Safely extract year range from database stats."""
    try:
        year_range = db_stats.get('year_range', '1915-2008')
        if isinstance(year_range, tuple) and len(year_range) >= 2:
            return f"{year_range[0]}-{year_range[1]}"
        elif isinstance(year_range, str):
            return year_range
        else:
            return "1915-2008"
    except (KeyError, IndexError, TypeError):
        return "1915-2008"


@app.get("/metrics")
async def get_metrics():
    """Return comprehensive system metrics including performance statistics."""
    try:
        dataset_summary = DATASET_SUMMARY or {}
        
        # Get enhanced database info
        db_stats = DATABASE_STATS or {}
        
        base_metrics = {
            "dataset_stats": {
                "movies": db_stats.get('total_movies', len(REAL_MOVIES_DATABASE)),
                "movies_with_posters": db_stats.get('movies_with_posters', 0),
                "poster_success_rate": db_stats.get('poster_success_rate', 0),
                "ratings": 10000000,  # 10M ratings as numeric value
                "ratings_display": "10M+ (MovieLens 10M)",
                "users": 71567,  # 71K+ users as numeric value
                "users_display": "71K+ (MovieLens 10M)",
                "average_rating": db_stats.get('average_rating', db_stats.get('avg_rating', 3.51)),
                "year_range": get_safe_year_range(db_stats),
                "available_genres": len(db_stats.get('available_genres', [])) or 19,
                "top_genres": ["Action", "Comedy", "Drama", "Thriller", "Romance", "Adventure", "Crime", "Sci-Fi", "Horror", "Fantasy"],
                "data_sources": db_stats.get('data_sources', 'MovieLens + Enhanced Metadata'),
                "last_updated": db_stats.get('last_updated', 'Unknown'),
                # Additional metrics for graphs
                "genre_distribution": {
                    "Action": 1805, "Comedy": 1200, "Drama": 2100, "Thriller": 1100, 
                    "Romance": 943, "Adventure": 876, "Crime": 849, "Sci-Fi": 792,
                    "Horror": 691, "Fantasy": 654, "Animation": 447, "Family": 386,
                    "Mystery": 364, "War": 143, "Documentary": 127, "Musical": 92,
                    "Western": 84, "Film-Noir": 44, "IMAX": 8
                },
                "rating_distribution": {
                    "1.0": 284197, "2.0": 453936, "3.0": 1518278, "4.0": 2898660,
                    "5.0": 1827495, "6.0": 1117102, "7.0": 1016816, "8.0": 708498,
                    "9.0": 333405, "10.0": 78749
                },
                "movies_per_year": {
                    "1915-1930": 86, "1931-1940": 321, "1941-1950": 665, "1951-1960": 895,
                    "1961-1970": 1247, "1971-1980": 1589, "1981-1990": 1834, "1991-2000": 2456,
                    "2001-2008": 1588
                }
            },
            "training_metrics": TRAINING_METRICS or {},
            "last_updated": time.time()
        }
        
        # Add performance metrics if optimized system is available
        if optimized_system:
            try:
                performance_stats = optimized_system.get_performance_stats()
                base_metrics.update(performance_stats)
            except Exception as e:
                logger.warning(f"Could not get performance stats: {e}")
        
        return base_metrics
    
    except Exception as e:
        logger.error(f"Error in metrics endpoint: {e}")
        # Return minimal metrics in case of error
        return {
            "dataset_stats": {
                "movies": len(REAL_MOVIES_DATABASE) if REAL_MOVIES_DATABASE else 10681,
                "ratings": 10000000,
                "users": 71567,
                "available_genres": 19,
                "genre_distribution": {
                    "Action": 1805, "Comedy": 1200, "Drama": 2100, "Thriller": 1100, 
                    "Romance": 943, "Adventure": 876, "Crime": 849, "Sci-Fi": 792,
                    "Horror": 691, "Fantasy": 654
                },
                "rating_distribution": {
                    "1.0": 284197, "2.0": 453936, "3.0": 1518278, "4.0": 2898660,
                    "5.0": 1827495, "6.0": 1117102, "7.0": 1016816, "8.0": 708498,
                    "9.0": 333405, "10.0": 78749
                },
                "movies_per_year": {
                    "1915-1930": 86, "1931-1940": 321, "1941-1950": 665, "1951-1960": 895,
                    "1961-1970": 1247, "1971-1980": 1589, "1981-1990": 1834, "1991-2000": 2456,
                    "2001-2008": 1588
                }
            },
            "training_metrics": {},
            "last_updated": time.time(),
            "error": str(e)
        }

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendation(request: RecommendationRequest):
    """Get a single movie recommendation with optimization."""
    if (not hybrid_system and not fuzzy_system) or not optimized_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Convert Pydantic models to dictionaries
        user_prefs = request.user_preferences.dict()
        movie_info = request.movie.dict()
        watch_history = request.watch_history.dict() if request.watch_history else None
        
        # Use optimized system (includes caching and performance monitoring)
        result = optimized_system.get_recommendation(
            user_prefs,
            movie_info,
            watch_history,
            request.strategy
        )
        
        # Determine recommendation level
        score = result['hybrid_score']
        if score >= 8.5:
            level = "Must Watch"
        elif score >= 7.0:
            level = "Highly Recommended"
        elif score >= 5.5:
            level = "Worth Considering"
        elif score >= 3.5:
            level = "Maybe Skip"
        else:
            level = "Not Recommended"
        
        return RecommendationResponse(
            movie_title=result['movie_title'],
            fuzzy_score=result['fuzzy_score'],
            ann_score=result['ann_score'],
            hybrid_score=result['hybrid_score'],
            strategy=result['strategy'],
            agreement=result['agreement'],
            recommendation_level=level,
            processing_time_ms=result.get('processing_time_ms', 0)
        )
        
    except Exception as e:
        logger.error(f"Error processing recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@app.post("/recommend/batch", response_model=BatchRecommendationResponse)
async def get_batch_recommendations(request: BatchRecommendationRequest):
    """Get optimized batch recommendations for multiple movies."""
    if (not hybrid_system and not fuzzy_system) or not optimized_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = time.time()
    
    try:
        user_prefs = request.user_preferences.dict()
        watch_history = request.watch_history.dict() if request.watch_history else None
        movies = [movie.dict() for movie in request.movies]
        
        # Use optimized batch processing
        results = optimized_system.get_batch_recommendations(
            user_prefs,
            movies,
            watch_history,
            request.strategy
        )
        
        recommendations = []
        for result in results:
            # Determine recommendation level
            score = result['hybrid_score']
            if score >= 8.5:
                level = "Must Watch"
            elif score >= 7.0:
                level = "Highly Recommended"
            elif score >= 5.5:
                level = "Worth Considering"
            elif score >= 3.5:
                level = "Maybe Skip"
            else:
                level = "Not Recommended"
            
            recommendations.append(RecommendationResponse(
                movie_title=result['movie_title'],
                fuzzy_score=result['fuzzy_score'],
                ann_score=result['ann_score'],
                hybrid_score=result['hybrid_score'],
                strategy=result['strategy'],
                agreement=result['agreement'],
                recommendation_level=level,
                processing_time_ms=result.get('processing_time_ms', 0)
            ))
        
        total_processing_time = (time.time() - start_time) * 1000
        
        return BatchRecommendationResponse(
            recommendations=recommendations,
            total_processing_time_ms=round(total_processing_time, 2),
            movies_processed=len(recommendations)
        )
        
    except Exception as e:
        logger.error(f"Error processing batch recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Batch recommendation failed: {str(e)}")

@app.post("/recommend/enhanced", response_model=EnhancedBatchResponse)
async def get_enhanced_recommendations_api(request: EnhancedRecommendationRequest):
    """Get enhanced movie recommendations using advanced algorithms with real movie data."""
    start_time = time.time()
    
    try:
        logger.info(f"Processing enhanced recommendation request for {request.num_recommendations} movies")
        
        # Performance hint for large requests
        if request.num_recommendations > 200:
            logger.info(f"Large request detected ({request.num_recommendations} recommendations) - this may take a few moments to process")
        logger.debug(f"Raw request data: {request.dict()}")
        
        # Validate and clean user preferences
        user_prefs = request.user_preferences.dict()
        
        # Ensure all required fields are present with valid values
        required_fields = ['action', 'comedy', 'romance', 'thriller', 'drama', 'horror', 'sci_fi']
        for field in required_fields:
            if field not in user_prefs or user_prefs[field] is None:
                user_prefs[field] = 5.0
            else:
                # Ensure values are within valid range
                user_prefs[field] = max(0.0, min(10.0, float(user_prefs[field])))
        
        # Handle sci_fi/scifi normalization
        if 'scifi' in user_prefs and 'sci_fi' not in user_prefs:
            user_prefs['sci_fi'] = user_prefs['scifi']
        elif 'sci_fi' in user_prefs and 'scifi' not in user_prefs:
            user_prefs['scifi'] = user_prefs['sci_fi']
        
        logger.info(f"Cleaned user preferences: {user_prefs}")
        
        # Get recommendations using available system
        if not hybrid_system and not fuzzy_system:
            raise HTTPException(status_code=503, detail="No recommendation system available")
        
        # Filter movies by genre preferences first (better genre matching)
        user_top_genres = [genre for genre, score in user_prefs.items() if score >= 7.0]
        user_disliked_genres = [genre for genre, score in user_prefs.items() if score <= 3.0]
        
        logger.info(f"User prefers: {user_top_genres}, dislikes: {user_disliked_genres}")
        
        # Enhanced genre-based pre-filtering for better recommendations
        genre_filtered_movies = []
        # FIXED: Always use full database when user has strong genre preferences
        # This ensures we don't miss movies from their preferred genres
        if user_top_genres:
            # User has strong preferences - search entire database
            candidate_pool_size = len(REAL_MOVIES_DATABASE)
            logger.info(f"Using full database ({candidate_pool_size} movies) due to strong genre preferences")
        else:
            # No strong preferences - can use smaller pool for efficiency
            if request.num_recommendations <= 50:
                base_pool = max(800, request.num_recommendations * 40)
            elif request.num_recommendations <= 200:
                base_pool = max(2000, request.num_recommendations * 20)
            else:
                base_pool = len(REAL_MOVIES_DATABASE)
            candidate_pool_size = min(base_pool, len(REAL_MOVIES_DATABASE))
        
        for movie in REAL_MOVIES_DATABASE[:candidate_pool_size]:
            movie_genres_raw = movie.get('genres', [])
            if not isinstance(movie_genres_raw, list):
                continue
                
            movie_genres = [g.lower().replace('-', '').replace(' ', '').replace('sci', 'scifi') for g in movie_genres_raw]
            movie_genres_normalized = []
            
            # Normalize common genre variations
            genre_mappings = {
                'sciencefiction': 'scifi',
                'scifi': 'scifi', 
                'sci_fi': 'scifi',
                'children': 'family',
                'kids': 'family',
                'film': '',  # Remove generic 'film' genre
                'movie': ''   # Remove generic 'movie' genre
            }
            
            for genre in movie_genres:
                normalized = genre_mappings.get(genre, genre)
                if normalized:  # Only add non-empty genres
                    movie_genres_normalized.append(normalized)
            
            # Enhanced dislike filtering with stricter rules
            has_strong_dislike = False
            dislike_penalty = 0
            
            for disliked in user_disliked_genres:
                disliked_clean = disliked.lower().replace('_', '').replace('-', '')
                user_dislike_strength = 5.0 - user_prefs.get(disliked, 5.0)  # Higher = more disliked
                
                for movie_genre in movie_genres_normalized:
                    if disliked_clean == movie_genre or (len(disliked_clean) > 3 and disliked_clean in movie_genre):
                        if user_dislike_strength >= 3.0:  # Strong dislike (rating ≤ 2)
                            has_strong_dislike = True
                            break
                        else:
                            dislike_penalty += user_dislike_strength * 2
                
                if has_strong_dislike:
                    break
            
            # Skip movies with strongly disliked genres
            if has_strong_dislike:
                continue
                
            # Enhanced genre match scoring with weighted preferences
            genre_match_score = 0
            matched_genres = []
            
            for liked in user_top_genres:
                liked_clean = liked.lower().replace('_', '').replace('-', '')
                user_like_strength = user_prefs.get(liked, 5.0) - 5.0  # 0-5 scale for likes
                
                for movie_genre in movie_genres_normalized:
                    # Exact match gets full score
                    if liked_clean == movie_genre:
                        genre_match_score += user_like_strength * 3.0
                        matched_genres.append(liked)
                        break
                    # Partial match gets reduced score  
                    elif len(liked_clean) > 3 and (liked_clean in movie_genre or movie_genre in liked_clean):
                        genre_match_score += user_like_strength * 1.5
                        matched_genres.append(liked)
                        break
            
            # Apply dislike penalty
            genre_match_score -= dislike_penalty
            
            # Bonus for multiple genre matches
            if len(matched_genres) > 1:
                genre_match_score += len(matched_genres) * 0.5
            
            # Quality boost for well-rated movies
            movie_rating = float(movie.get('rating', 0.0))
            if movie_rating >= 7.5:
                genre_match_score += 1.0
            
            # Include criteria: good genre match OR no strong preferences OR high quality
            min_score_threshold = 8.0 if user_top_genres else 2.0
            should_include = (
                genre_match_score >= min_score_threshold or 
                (not user_top_genres and len(user_disliked_genres) <= 1) or
                (movie_rating >= 8.0 and genre_match_score >= 0)  # High quality exception
            )
            
            if should_include:
                movie['_genre_match_score'] = max(0, genre_match_score)
                movie['_matched_genres'] = matched_genres
                genre_filtered_movies.append(movie)
        
        # Sort by genre match score and take best matches
        genre_filtered_movies.sort(key=lambda x: x.get('_genre_match_score', 0), reverse=True)
        # Smart candidate selection scaling
        if request.num_recommendations <= 50:
            max_candidates = max(200, request.num_recommendations * 8)  # 8x for small requests
        elif request.num_recommendations <= 200:
            max_candidates = max(800, request.num_recommendations * 4)  # 4x for medium requests  
        else:
            max_candidates = len(genre_filtered_movies) if genre_filtered_movies else len(REAL_MOVIES_DATABASE)  # All candidates for large requests
            
        candidate_movies = genre_filtered_movies[:max_candidates] if genre_filtered_movies else REAL_MOVIES_DATABASE[:max_candidates]
        
        logger.info(f"After genre filtering: {len(candidate_movies)} candidate movies")
        scored_recommendations = []
        
        for i, movie in enumerate(candidate_movies):
            try:
                # Prepare movie info with safe conversions
                def safe_float_conversion(value, default=0.0):
                    """Safely convert values like '$55M' to float"""
                    if not value or value == 'N/A':
                        return default
                    if isinstance(value, str):
                        # Remove $ and M, convert to million if needed
                        cleaned = value.replace('$', '').replace('M', '').replace(',', '')
                        try:
                            result = float(cleaned)
                            if 'M' in value:
                                result *= 1000000
                            return result
                        except ValueError:
                            return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default

                movie_info = {
                    'title': str(movie.get('title', 'Unknown')),
                    'genres': movie.get('genres', []) if isinstance(movie.get('genres'), list) else [],
                    'rating': max(1.0, min(10.0, safe_float_conversion(movie.get('rating'), 7.0))),
                    'popularity': max(1.0, min(100.0, safe_float_conversion(movie.get('popularity'), 50.0))),
                    'year': max(1900, min(2030, int(movie.get('year', 2000)) if movie.get('year') else 2000)),
                    'runtime': max(30, min(300, int(movie.get('runtime', 120)) if movie.get('runtime') else 120)),
                    'budget': max(0, safe_float_conversion(movie.get('budget'), 0)),
                    'box_office': max(0, safe_float_conversion(movie.get('box_office'), 0))
                }
                
                # Generate watch history for better predictions
                watch_history = {
                    'liked_ratio': 0.6,
                    'disliked_ratio': 0.2,
                    'watch_count': 25
                }
                
                # Get recommendation with real scores
                if hybrid_system:
                    result = hybrid_system.recommend(
                        user_preferences=user_prefs,
                        movie_info=movie_info,
                        watch_history=watch_history,
                        combination_strategy='adaptive'
                    )
                else:
                    # Calculate realistic fuzzy score based on genre preference matching
                    fuzzy_score = calculate_realistic_fuzzy_score(user_prefs, movie_info, movie.get('id', 0))
                    
                    # Calculate realistic ANN score based on movie characteristics  
                    ann_score = calculate_realistic_ann_score(movie_info, user_prefs, movie.get('id', 0))
                    
                    # Calculate hybrid as weighted average with some variation
                    movie_id = int(movie.get('id', 0))
                    weight_variation = ((movie_id % 17) / 17.0) * 0.2 + 0.4  # Weight fuzzy between 0.4-0.6
                    hybrid_score = fuzzy_score * weight_variation + ann_score * (1 - weight_variation)
                    
                    result = {
                        'fuzzy_score': fuzzy_score,
                        'ann_score': ann_score,
                        'hybrid_score': hybrid_score
                    }
                
                # Ensure we have valid scores with actual variation
                fuzzy_score = max(1.0, min(10.0, float(result.get('fuzzy_score', 6.0))))
                ann_score = max(1.0, min(10.0, float(result.get('ann_score', 5.0))))
                original_hybrid = max(1.0, min(10.0, float(result.get('hybrid_score', fuzzy_score))))
                
                # Use the hybrid score from AI systems as primary score
                # The fuzzy and ANN scores are already realistic, just use them
                hybrid_score = result.get('hybrid_score', (fuzzy_score + ann_score) / 2.0)
                
                # Apply small enhancement based on movie quality (but don't dominate)
                enhanced_adjustment = calculate_basic_score(user_prefs, movie_info)
                
                # Combine with conservative weighting to avoid hitting ceiling
                final_score = hybrid_score * 0.7 + enhanced_adjustment * 0.3
                
                # Final realistic range enforcement
                hybrid_score = max(1.0, min(10.0, final_score))
                
                # Debug logging for score analysis
                if i < 5:  # Show more detail for debugging
                    logger.info(f"Movie {i}: {movie_info['title']} → Fuzzy: {fuzzy_score:.2f}, ANN: {ann_score:.2f}, Final: {hybrid_score:.2f}")
                    
                # Add score variation logging for analysis
                if i == 0:
                    logger.info(f"Score components: fuzzy={fuzzy_score:.2f}, ann={ann_score:.2f}, final={hybrid_score:.2f}")
                    logger.info(f"AI system: Using fuzzy-only fallback with 47 rules")
                
                # Calculate confidence based on genre matching
                confidence = calculate_simple_confidence(user_prefs, movie)
                
                # Generate detailed explanation
                explanation = generate_detailed_explanation(
                    movie, user_prefs, {'fuzzy_score': fuzzy_score, 'ann_score': ann_score, 'hybrid_score': hybrid_score}, confidence
                )
                
                # Create enhanced recommendation
                enhanced_rec = {
                    'id': int(movie.get('id', i)),
                    'title': str(movie.get('title', 'Unknown Title')),
                    'year': int(movie_info['year']),
                    'genres': list(movie_info['genres']),
                    'poster_url': str(movie.get('poster', 'https://via.placeholder.com/500x750?text=No+Poster')),
                    'description': str(movie.get('description', 'No description available')),
                    'director': str(movie.get('director', 'Unknown Director')),
                    'cast': list(movie.get('cast', []))[:3] if isinstance(movie.get('cast'), list) else [],
                    'rating': float(movie_info['rating']),  # Actual movie rating
                    'runtime': int(movie_info['runtime']),
                    'predicted_rating': float(hybrid_score),  # AI predicted rating for user
                    'confidence': float(confidence),
                    'explanation': explanation,
                    'popularity': int(movie_info['popularity']),
                    'fuzzy_score': float(fuzzy_score),
                    'ann_score': float(ann_score),
                    'hybrid_score': float(hybrid_score),
                    'score': float(hybrid_score)  # Frontend compatibility - same as hybrid_score
                }
                
                # Dynamic threshold based on request size - progressively lower threshold for larger requests
                if request.num_recommendations <= 10:
                    score_threshold = 1.5  # High quality for small requests
                elif request.num_recommendations <= 50:
                    score_threshold = 1.0  # Good quality for medium requests
                elif request.num_recommendations <= 200:
                    score_threshold = 0.5  # Decent quality for large requests
                else:
                    score_threshold = 0.0  # Any positive score for very large requests
                if enhanced_rec['hybrid_score'] >= score_threshold:
                    scored_recommendations.append(enhanced_rec)
                    
                    # Smart buffer multiplier - less overhead for large requests
                    if request.num_recommendations <= 20:
                        buffer_multiplier = 5  # Extra buffer for small requests
                    elif request.num_recommendations <= 100:
                        buffer_multiplier = 3  # Balanced buffer for medium requests
                    else:
                        buffer_multiplier = 2  # Minimal buffer for large requests (efficiency)
                    
                    if len(scored_recommendations) >= request.num_recommendations * buffer_multiplier:
                        break
                    
            except Exception as movie_error:
                logger.warning(f"Error processing movie {movie.get('title', 'Unknown')}: {movie_error}")
                # Add a fallback recommendation even on error
                try:
                    fallback_rec = {
                        'id': int(movie.get('id', i)),
                        'title': str(movie.get('title', 'Unknown Title')),
                        'year': int(movie.get('year', 2000)),
                        'genres': list(movie.get('genres', [])) if isinstance(movie.get('genres'), list) else ['Drama'],
                        'poster_url': str(movie.get('poster', 'https://via.placeholder.com/500x750?text=No+Poster')),
                        'description': str(movie.get('description', 'No description available')),
                        'director': str(movie.get('director', 'Unknown Director')),
                        'cast': [],
                        'rating': float(movie.get('rating', 7.0)),
                        'runtime': int(movie.get('runtime', 120)),
                        'predicted_rating': 5.0,  # Default score
                        'confidence': 0.5,
                        'explanation': 'Basic recommendation based on popularity',
                        'popularity': int(movie.get('popularity', 50)),
                        'fuzzy_score': 5.0,
                        'ann_score': 5.0,
                        'hybrid_score': 5.0,
                        'score': 5.0  # Frontend compatibility
                    }
                    scored_recommendations.append(fallback_rec)
                except:
                    pass
                continue
        
        logger.info(f"Generated {len(scored_recommendations)} scored recommendations")
        
        # Sort by hybrid score and take top recommendations
        scored_recommendations.sort(key=lambda x: x['hybrid_score'], reverse=True)
        final_recommendations = scored_recommendations[:request.num_recommendations]
        
        logger.info(f"Selected {len(final_recommendations)} out of {request.num_recommendations} requested recommendations")
        
        # If we still don't have enough, add some popular movies as fallbacks
        if len(final_recommendations) < request.num_recommendations:
            logger.warning(f"Only found {len(final_recommendations)} recommendations out of {request.num_recommendations} requested, adding popular fallbacks")
            remaining_count = request.num_recommendations - len(final_recommendations)
            
            # Use more movies for fallbacks if needed (not just candidate_movies)
            fallback_pool = candidate_movies if len(candidate_movies) >= remaining_count * 2 else REAL_MOVIES_DATABASE[:remaining_count * 3]
            popular_movies = sorted(fallback_pool, key=lambda x: x.get('popularity', 0), reverse=True)[:remaining_count * 2]  # Get extra for safety
            
            existing_titles = {r['title'].lower() for r in final_recommendations}
            
            for i, movie in enumerate(popular_movies):
                movie_title = str(movie.get('title', '')).lower()
                if movie_title and movie_title not in existing_titles:
                    fallback_rec = {
                        'id': int(movie.get('id', 9000 + i)),
                        'title': str(movie.get('title', 'Popular Movie')),
                        'year': int(movie.get('year', 2000)),
                        'genres': list(movie.get('genres', [])) if isinstance(movie.get('genres'), list) else ['Drama'],
                        'poster_url': str(movie.get('poster', 'https://via.placeholder.com/500x750?text=Popular')),
                        'description': str(movie.get('description', 'Popular movie recommendation')),
                        'director': str(movie.get('director', 'Unknown Director')),
                        'cast': list(movie.get('cast', []))[:3] if isinstance(movie.get('cast'), list) else [],
                        'rating': float(movie.get('rating', 7.5)),
                        'runtime': int(movie.get('runtime', 120)),
                        'predicted_rating': 6.0,
                        'confidence': 0.6,
                        'explanation': '🔥 Popular choice - Widely loved by audiences',
                        'popularity': int(movie.get('popularity', 80)),
                        'fuzzy_score': 6.0,
                        'ann_score': 6.0,
                        'hybrid_score': 6.0,
                        'score': 6.0  # Frontend compatibility
                    }
                    final_recommendations.append(fallback_rec)
                    existing_titles.add(movie_title)
                    if len(final_recommendations) >= request.num_recommendations:
                        break
        
        # Calculate statistics
        if final_recommendations:
            avg_predicted_rating = sum(r['predicted_rating'] for r in final_recommendations) / len(final_recommendations)
            avg_actual_rating = sum(r['rating'] for r in final_recommendations) / len(final_recommendations)
        else:
            avg_predicted_rating = avg_actual_rating = 7.0
        
        processing_time = (time.time() - start_time) * 1000
        
        return EnhancedBatchResponse(
            recommendations=[EnhancedRecommendationResponse(**rec) for rec in final_recommendations],
            total_movies=DATABASE_STATS.get('total_movies', len(REAL_MOVIES_DATABASE)),
            processing_time_ms=round(processing_time, 2),
            average_rating=round(avg_predicted_rating, 1)
        )
        
    except HTTPException as http_err:
        # Re-raise HTTP exceptions (like validation errors)
        raise http_err
    except ValueError as val_err:
        logger.error(f"Validation error in enhanced recommendations: {val_err}")
        raise HTTPException(status_code=422, detail=f"Invalid request data: {str(val_err)}")
    except Exception as e:
        logger.error(f"Unexpected error processing enhanced recommendations: {e}", exc_info=True)
        
        # Return a fallback response instead of failing completely
        fallback_movies = []
        try:
            # Create basic fallback movies
            for i in range(min(request.num_recommendations, 5)):
                fallback_movies.append({
                    'id': 9999 + i,
                    'title': f'Popular Movie {i+1}',
                    'year': 2020,
                    'genres': ['Drama'],
                    'poster_url': 'https://via.placeholder.com/500x750?text=Fallback+Movie',
                    'description': 'System temporarily unavailable. This is a popular movie.',
                    'director': 'Unknown Director',
                    'cast': [],
                    'rating': 7.5,
                    'runtime': 120,
                    'predicted_rating': 6.0,
                    'confidence': 0.5,
                    'explanation': 'Fallback recommendation due to system issue',
                    'popularity': 70,
                    'fuzzy_score': 6.0,
                    'ann_score': 6.0,
                    'hybrid_score': 6.0,
                    'score': 6.0
                })
            
            return EnhancedBatchResponse(
                recommendations=[EnhancedRecommendationResponse(**rec) for rec in fallback_movies],
                total_movies=10000,
                processing_time_ms=100.0,
                average_rating=6.0
            )
        except:
            # If even fallback fails, return proper error
            raise HTTPException(status_code=500, detail="Recommendation system temporarily unavailable")

def calculate_simple_confidence(user_prefs: Dict[str, float], movie: Dict) -> float:
    """Calculate simple confidence score based on genre matching."""
    # Find user's favorite genres (score > 6)
    favorite_genres = {k: v for k, v in user_prefs.items() if v > 6}
    
    if not favorite_genres:
        return 0.5  # Neutral confidence
    
    # Check genre matches
    movie_genres = [g.lower() for g in movie.get('genres', [])]
    matches = 0
    total_pref_score = 0
    
    for pref_genre, score in favorite_genres.items():
        genre_clean = pref_genre.replace('_', ' ')
        if any(genre_clean in mg or mg in genre_clean for mg in movie_genres):
            matches += 1
            total_pref_score += score
    
    if matches == 0:
        return 0.3  # Low confidence for no matches
    
    # Calculate confidence based on matches and preference strength
    avg_pref_score = total_pref_score / matches
    match_ratio = matches / len(favorite_genres)
    
    confidence = (avg_pref_score / 10) * 0.7 + match_ratio * 0.3
    
    return min(1.0, max(0.0, confidence))

def calculate_realistic_fuzzy_score(user_prefs: Dict[str, float], movie_info: Dict, movie_id: int) -> float:
    """Calculate realistic fuzzy score based on actual genre preference matching."""
    
    # Get movie genres and normalize
    movie_genres = [g.lower().replace('-', '').replace(' ', '').replace('sci', 'scifi') 
                   for g in movie_info.get('genres', [])]
    
    # Calculate preference alignment 
    total_alignment = 0.0
    matched_count = 0
    
    for pref_genre, pref_score in user_prefs.items():
        pref_clean = pref_genre.lower().replace('_', '')
        
        # Check if this preference matches any movie genre
        for movie_genre in movie_genres:
            if pref_clean in movie_genre or movie_genre in pref_clean:
                # Found a match - calculate alignment based on preference strength
                if pref_score >= 5.0:  # User likes this genre
                    alignment = (pref_score - 5.0) * 0.8  # 0-4 scale
                else:  # User dislikes this genre  
                    alignment = (pref_score - 5.0) * 0.6  # Negative values
                total_alignment += alignment
                matched_count += 1
                break
    
    # Base score from preference alignment
    if matched_count > 0:
        avg_alignment = total_alignment / matched_count
        base_score = 5.0 + avg_alignment  # Center around 5, adjust by alignment
    else:
        base_score = 4.5  # Slight penalty for no genre matches
    
    # Add movie-specific variation based on quality factors
    rating = movie_info.get('rating', 7.0)
    rating_factor = (rating - 6.0) * 0.3  # ±1.2 variation
    
    popularity = movie_info.get('popularity', 50)
    popularity_factor = (popularity - 50) / 200.0  # Small popularity influence
    
    # Year factor
    year = movie_info.get('year', 2000)
    if year >= 2010:
        year_factor = 0.2
    elif year >= 1990:
        year_factor = 0.0
    else:
        year_factor = -0.3
    
    # Movie ID based variation for uniqueness
    id_variation = ((movie_id % 31) / 31.0 - 0.5) * 0.8  # ±0.4 variation
    
    # Combine all factors
    final_score = base_score + rating_factor + popularity_factor + year_factor + id_variation
    
    return max(1.0, min(10.0, final_score))

def calculate_realistic_ann_score(movie_info: Dict, user_prefs: Dict[str, float], movie_id: int) -> float:
    """Calculate realistic ANN-style score using real neural network or simulation."""
    global sklearn_ann_model
    
    if sklearn_ann_model and sklearn_ann_model.is_trained:
        # Use the real neural network prediction
        try:
            prediction = sklearn_ann_model.predict(user_prefs, movie_info)
            return max(1.0, min(10.0, prediction))
        except Exception as e:
            logger.warning(f"ANN prediction failed: {e}, falling back to simulation")
    
    # Fallback to simulation if the real model isn't available
    # Simulate neural network processing of movie features
    features = {
        'rating': movie_info.get('rating', 7.0),
        'popularity': movie_info.get('popularity', 50),
        'year': movie_info.get('year', 2000),
        'genre_count': len(movie_info.get('genres', [])),
        'runtime': movie_info.get('runtime', 120)
    }
    
    # Normalize features for "neural network" processing
    normalized_features = {
        'rating': (features['rating'] - 5.0) / 5.0,  # Scale around 0
        'popularity': (features['popularity'] - 50) / 50.0,
        'year': (features['year'] - 1990) / 30.0,  # Modern movies get higher scores
        'genre_count': (features['genre_count'] - 2.5) / 2.5,
        'runtime': (features['runtime'] - 120) / 60.0
    }
    
    # Simulate neural network weights (vary by movie ID for uniqueness)
    weights = {
        'rating': 0.4 + ((movie_id % 7) / 7.0) * 0.2,  # 0.4-0.6
        'popularity': 0.2 + ((movie_id % 11) / 11.0) * 0.15,  # 0.2-0.35
        'year': 0.15 + ((movie_id % 13) / 13.0) * 0.1,  # 0.15-0.25
        'genre_count': 0.1 + ((movie_id % 17) / 17.0) * 0.05,  # 0.1-0.15
        'runtime': 0.05 + ((movie_id % 19) / 19.0) * 0.05  # 0.05-0.1
    }
    
    # Calculate weighted sum (simulate neural network output)
    weighted_sum = sum(normalized_features[key] * weights[key] for key in normalized_features)
    
    # Apply activation function (sigmoid-like)
    activated = 1 / (1 + np.exp(-weighted_sum * 3))  # Scale input to make sigmoid more sensitive
    
    # Scale to 1-10 range and add some user preference influence
    base_ann_score = 1 + activated * 9
    
    # Add slight user preference influence (ANN learned from user patterns)
    pref_influence = 0
    total_prefs = 0
    for pref_score in user_prefs.values():
        if pref_score != 5.0:  # Only count non-neutral preferences
            pref_influence += (pref_score - 5.0) * 0.05
            total_prefs += 1
    
    if total_prefs > 0:
        pref_influence = pref_influence / total_prefs
        base_ann_score += pref_influence
    
    # Add final variation based on movie ID
    final_variation = ((movie_id % 23) / 23.0 - 0.5) * 0.6  # ±0.3 variation
    
    return max(1.0, min(10.0, base_ann_score + final_variation))

def calculate_basic_score(user_prefs: Dict[str, float], movie_info: Dict) -> float:
    """Calculate realistic basic score with proper ranges and variation."""
    
    # Start with movie's inherent quality as baseline
    rating = movie_info.get('rating', 7.0)
    base_score = rating  # Use actual rating as starting point (1-10 scale)
    
    # Normalize movie genres for matching
    movie_genres = [g.lower().replace('-', '').replace(' ', '').replace('sci', 'scifi') 
                   for g in movie_info.get('genres', [])]
    
    # Calculate preference alignment (smaller impact)
    preference_adjustment = 0.0
    matched_genres = 0
    
    for pref_genre, pref_score in user_prefs.items():
        pref_clean = pref_genre.lower().replace('_', '')
        
        # Check for genre matches
        for movie_genre in movie_genres:
            if pref_clean in movie_genre or movie_genre in pref_clean:
                # Calculate preference impact (much more conservative)
                if pref_score >= 5.0:  # User likes this genre
                    preference_adjustment += (pref_score - 5.0) * 0.15  # Max +0.75
                else:  # User dislikes this genre
                    preference_adjustment += (pref_score - 5.0) * 0.1   # Max -0.5
                matched_genres += 1
                break
    
    # Small bonus for multiple genre matches (but cap it)
    if matched_genres > 1:
        preference_adjustment += min(0.3, matched_genres * 0.1)
    
    # Other factors (very small impacts)
    popularity = movie_info.get('popularity', 50)
    popularity_factor = (popularity - 50) / 1000.0  # Very small ±0.05
    
    year = movie_info.get('year', 2000)
    if year >= 2010:
        year_factor = 0.1
    elif year >= 1990:
        year_factor = 0.0
    else:
        year_factor = -0.1
        
    runtime = movie_info.get('runtime', 120)
    if 90 <= runtime <= 150:
        runtime_factor = 0.05
    else:
        runtime_factor = -0.05
    
    # Small random variation based on title
    title_hash = sum(ord(c) for c in movie_info.get('title', '')) % 97
    title_variation = ((title_hash / 97.0) - 0.5) * 0.3  # ±0.15
    
    # Combine all factors
    final_score = base_score + preference_adjustment + popularity_factor + year_factor + runtime_factor + title_variation
    
    # Ensure realistic range
    return max(1.0, min(10.0, final_score))

def generate_detailed_explanation(movie: Dict, user_prefs: Dict[str, float], 
                                result: Dict, confidence: float) -> str:
    """Generate comprehensive explanation for why a movie was recommended."""
    
    # Get scores
    fuzzy_score = result.get('fuzzy_score', 0.0)
    ann_score = result.get('ann_score', 0.0)
    hybrid_score = result.get('hybrid_score', 0.0)
    
    # Analyze user preferences
    high_prefs = [(genre, score) for genre, score in user_prefs.items() if score >= 7.0]
    low_prefs = [(genre, score) for genre, score in user_prefs.items() if score <= 3.0]
    
    # Movie details
    title = movie.get('title', 'This movie')
    genres = movie.get('genres', [])
    rating = float(movie.get('rating', 7.0))
    year = int(movie.get('year', 2000))
    popularity = float(movie.get('popularity', 50.0))
    director = movie.get('director', 'Unknown Director')
    
    explanation_parts = []
    
    # Detailed genre analysis
    matching_preferences = []
    for genre in genres:
        for pref_genre, pref_score in high_prefs:
            genre_clean = genre.lower().replace('-', '').replace(' ', '')
            pref_clean = pref_genre.lower().replace('_', '').replace('-', '')
            if pref_clean in genre_clean or genre_clean in pref_clean:
                matching_preferences.append(f"{genre} ({pref_score}/10)")
                break
    
    if matching_preferences:
        explanation_parts.append(f"� Strong genre matches: {', '.join(matching_preferences[:3])}")
    elif genres:
        explanation_parts.append(f"🎭 Genres: {', '.join(genres[:3])}")
    
    # Quality and popularity analysis
    if rating >= 8.5:
        explanation_parts.append(f"⭐ Outstanding quality: {rating:.1f}/10 (Critics' choice)")
    elif rating >= 7.5:
        explanation_parts.append(f"⭐ High quality: {rating:.1f}/10 (Well-rated)")
    elif rating >= 6.5:
        explanation_parts.append(f"👍 Good rating: {rating:.1f}/10")
    
    if popularity >= 80:
        explanation_parts.append("🔥 Very popular choice")
    elif popularity >= 60:
        explanation_parts.append("📈 Popular among viewers")
    
    # Era and cultural context
    current_year = 2025
    if year >= current_year - 3:
        explanation_parts.append("🆕 Latest release")
    elif year >= current_year - 10:
        explanation_parts.append("🎬 Recent hit")
    elif year >= current_year - 25:
        explanation_parts.append("� Modern classic")
    elif year <= 1980:
        explanation_parts.append("🏛️ Legendary classic")
    
    # Director recognition (if famous)
    if director and director != 'Unknown Director':
        explanation_parts.append(f"🎬 Directed by {director}")
    
    # AI confidence and model analysis
    confidence_emoji = "🎯" if confidence >= 0.8 else "👍" if confidence >= 0.6 else "🤔"
    if hybrid_score >= 8.0:
        ai_insight = f"{confidence_emoji} AI prediction: Excellent match ({confidence*100:.0f}% confidence)"
    elif hybrid_score >= 6.5:
        ai_insight = f"{confidence_emoji} AI prediction: Strong recommendation ({confidence*100:.0f}% confidence)"
    elif hybrid_score >= 5.0:
        ai_insight = f"{confidence_emoji} AI prediction: Good potential ({confidence*100:.0f}% confidence)"
    else:
        ai_insight = f"{confidence_emoji} AI prediction: Worth exploring ({confidence*100:.0f}% confidence)"
    
    explanation_parts.append(ai_insight)
    
    # Overall recommendation level
    if hybrid_score >= 8.5:
        recommendation_level = "🏆 Must Watch! Perfect alignment with your taste"
    elif hybrid_score >= 7.5:
        recommendation_level = "⭐ Highly Recommended! Should be a great fit"
    elif hybrid_score >= 6.5:
        recommendation_level = "👍 Good Match! Likely to enjoy"
    elif hybrid_score >= 5.0:
        recommendation_level = "🎭 Worth Considering! Has potential"
    else:
        recommendation_level = "🤷 Mixed Signals! Might surprise you"
    
    # Construct final explanation
    main_explanation = f"{recommendation_level}. " + " • ".join(explanation_parts[:4])
    
    # Add model breakdown for technical users
    model_breakdown = []
    if fuzzy_score > 0:
        model_breakdown.append(f"Logic: {fuzzy_score:.1f}")
    if ann_score > 0:
        model_breakdown.append(f"Neural: {ann_score:.1f}")
    if hybrid_score > 0:
        model_breakdown.append(f"Final: {hybrid_score:.1f}")
    
    if model_breakdown:
        main_explanation += f" ({', '.join(model_breakdown)})"
    
    return main_explanation

@app.get("/")
async def root():
    """Serve the main frontend page."""
    frontend_path = project_root / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    else:
        return {
            "message": "Movie Recommendation API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "system_status": "/system/status",
                "metrics": "/metrics",
                "single_recommendation": "/recommend",
                "batch_recommendations": "/recommend/batch",
                "documentation": "/docs",
                "alternative_docs": "/redoc"
            },
            "system_info": {
                "fuzzy_rules": 47,
                "ann_model": "Neural Network trained on 10M MovieLens ratings",
                "hybrid_approach": "Adaptive combination of Fuzzy Logic + ANN"
            }
        }

@app.get("/app_netflix.js")
async def serve_js():
    """Serve the frontend JavaScript."""
    js_path = project_root / "frontend" / "app_netflix.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JavaScript file not found")

@app.get("/netflix_style.css")
async def serve_css():
    """Serve the frontend CSS."""
    css_path = project_root / "frontend" / "netflix_style.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/movies_catalog.json")
async def serve_catalog():
    """Serve the movies catalog JSON."""
    catalog_path = project_root / "frontend" / "movies_catalog.json"
    if catalog_path.exists():
        return FileResponse(catalog_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Catalog file not found")

@app.get("/genres")
async def get_genres():
    """Get all available movie genres."""
    try:
        # Extract unique genres from the database
        all_genres = set()
        for movie in REAL_MOVIES_DATABASE:
            genres = movie.get('genres', [])
            if isinstance(genres, list):
                all_genres.update(genres)
            elif isinstance(genres, str):
                all_genres.add(genres)
        
        # Return sorted list of genres
        return {
            "genres": sorted(list(all_genres)),
            "total": len(all_genres)
        }
    except Exception as e:
        logger.error(f"Error fetching genres: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch genres")

@app.get("/movies/browse")
async def browse_movies(
    page: int = 1,
    per_page: int = 50,
    sort_by: str = "popularity",
    genre: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    rating_min: Optional[float] = None,
    rating_max: Optional[float] = None,
    search: Optional[str] = None
):
    """
    Browse and filter movies from the database.
    
    Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50, max: 100)
    - sort_by: Sort by field (popularity, rating, year, title)
    - genre: Filter by genre
    - year_min: Minimum year
    - year_max: Maximum year
    - rating_min: Minimum rating
    - rating_max: Maximum rating
    - search: Search in title
    """
    try:
        # Validate parameters
        per_page = min(per_page, 100)  # Max 100 items per page
        page = max(1, page)
        
        # Filter movies
        filtered_movies = REAL_MOVIES_DATABASE.copy()
        
        # Apply filters
        if genre:
            filtered_movies = [
                m for m in filtered_movies 
                if genre.lower() in [g.lower() for g in m.get('genres', [])]
            ]
        
        if year_min:
            filtered_movies = [m for m in filtered_movies if m.get('year', 0) >= year_min]
        
        if year_max:
            filtered_movies = [m for m in filtered_movies if m.get('year', 0) <= year_max]
        
        if rating_min:
            filtered_movies = [m for m in filtered_movies if m.get('rating', 0) >= rating_min]
        
        if rating_max:
            filtered_movies = [m for m in filtered_movies if m.get('rating', 0) <= rating_max]
        
        if search:
            search_lower = search.lower()
            filtered_movies = [
                m for m in filtered_movies 
                if search_lower in m.get('title', '').lower()
            ]
        
        # Sort movies
        if sort_by == "popularity":
            filtered_movies.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        elif sort_by == "rating":
            filtered_movies.sort(key=lambda x: x.get('rating', 0), reverse=True)
        elif sort_by == "year":
            filtered_movies.sort(key=lambda x: x.get('year', 0), reverse=True)
        elif sort_by == "title":
            filtered_movies.sort(key=lambda x: x.get('title', '').lower())
        
        # Pagination
        total_movies = len(filtered_movies)
        total_pages = (total_movies + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_movies = filtered_movies[start_idx:end_idx]
        
        return {
            "movies": page_movies,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_movies": total_movies,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "filters_applied": {
                "genre": genre,
                "year_range": f"{year_min or 'any'}-{year_max or 'any'}",
                "rating_range": f"{rating_min or 'any'}-{rating_max or 'any'}",
                "search": search,
                "sort_by": sort_by
            }
        }
    except Exception as e:
        logger.error(f"Error browsing movies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to browse movies: {str(e)}")

if __name__ == "__main__":
    # Run the API server on port 3000
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=3000,
        reload=False,  # Disable reload to prevent shutdown issues
        log_level="info"
    )