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
from typing import Dict, List, Optional, Tuple
import uvicorn
import logging
import time
from pathlib import Path
import sys
import json
import threading

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
from models.enhanced_ann_model import EnhancedANNModel, SimpleANNModel
from models.hybrid_system import HybridRecommendationSystem as FinalHybridSystem
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

# Global system instances
hybrid_system = None
optimized_system = None
recommendation_cache = RecommendationCache()
DATASET_SUMMARY = load_dataset_summary()

# Pydantic models for request/response
class UserPreferences(BaseModel):
    action: float = Field(ge=0, le=10, description="Action preference (0-10)")
    comedy: float = Field(ge=0, le=10, description="Comedy preference (0-10)")
    romance: float = Field(ge=0, le=10, description="Romance preference (0-10)")
    thriller: float = Field(ge=0, le=10, description="Thriller preference (0-10)")
    sci_fi: float = Field(ge=0, le=10, description="Sci-Fi preference (0-10)")
    drama: float = Field(ge=0, le=10, description="Drama preference (0-10)")
    horror: float = Field(ge=0, le=10, description="Horror preference (0-10)")

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
    rating: float
    runtime: int
    predicted_rating: float
    confidence: float
    explanation: str
    popularity: int

class EnhancedRecommendationRequest(BaseModel):
    user_preferences: UserPreferences
    num_recommendations: int = Field(default=10, ge=1, le=20)

class EnhancedBatchResponse(BaseModel):
    recommendations: List[EnhancedRecommendationResponse]
    total_movies: int
    processing_time_ms: float
    average_rating: float

@app.on_event("startup")
async def startup_event():
    """Initialize the hybrid recommendation system on startup."""
    global hybrid_system, optimized_system
    try:
        logger.info("🚀 Initializing Movie Recommendation API...")
        hybrid_system = FinalHybridSystem()
        
        # Initialize performance optimization
        optimized_system = initialize_optimized_system(
            hybrid_system,
            cache_size=1000,  # Cache up to 1000 recommendations
            cache_ttl=3600    # Cache for 1 hour
        )
        
        logger.info("✅ Hybrid recommendation system with optimization initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
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
    if not hybrid_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        return SystemStatus(
            fuzzy_engine_status="operational" if hybrid_system.fuzzy_engine else "error",
            ann_model_status="operational" if hybrid_system.ann_available else "unavailable",
            total_fuzzy_rules=len(hybrid_system.fuzzy_engine.rules) if hybrid_system.fuzzy_engine else 0,
            ann_parameters=hybrid_system.ann_model.count_params() if hybrid_system.ann_available else None,
            movies_available=len(REAL_MOVIES_DATABASE),
            system_ready=True
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@app.get("/metrics")
async def get_metrics():
    """Return comprehensive system metrics including performance statistics."""
    dataset_summary = DATASET_SUMMARY or {}
    
    # Get enhanced database info
    db_stats = DATABASE_STATS
    
    base_metrics = {
        "dataset_stats": {
            "movies": db_stats.get('total_movies', len(REAL_MOVIES_DATABASE)),
            "movies_with_posters": db_stats.get('movies_with_posters', 0),
            "poster_success_rate": db_stats.get('poster_success_rate', 0),
            "ratings": "10M+ (MovieLens 10M)",
            "users": "71K+ (MovieLens 10M)",
            "average_rating": db_stats.get('average_rating', 7.0),
            "year_range": f"{db_stats.get('year_range', (1995, 2024))[0]}-{db_stats.get('year_range', (1995, 2024))[1]}",
            "available_genres": len(db_stats.get('available_genres', [])),
            "data_sources": db_stats.get('data_sources', 'MovieLens + Enhanced Metadata'),
            "last_updated": db_stats.get('last_updated', 'Unknown')
        },
        "training_metrics": TRAINING_METRICS,
        "last_updated": time.time()
    }
    
    # Add performance metrics if optimized system is available
    if optimized_system:
        performance_stats = optimized_system.get_performance_stats()
        base_metrics.update(performance_stats)
    
    return base_metrics

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendation(request: RecommendationRequest):
    """Get a single movie recommendation with optimization."""
    if not hybrid_system or not optimized_system:
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
    if not hybrid_system or not optimized_system:
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
        
        # Use the enhanced recommendation engine
        user_prefs = request.user_preferences.dict()
        
        # Get recommendations using multiple algorithms
        algorithm = request.dict().get('algorithm', 'hybrid_scoring')
        recommendations = get_enhanced_recommendations(
            user_prefs, 
            algorithm=algorithm, 
            num_recommendations=request.num_recommendations
        )
        
        # Convert recommendations to API format
        enhanced_recommendations = []
        for movie in recommendations:
            try:
                # Ensure all required fields are present and convert types correctly
                enhanced_rec = {
                    'id': int(movie.get('id', 0)),
                    'title': str(movie.get('title', 'Unknown Title')),
                    'year': int(movie.get('year', 2000)),
                    'genres': list(movie.get('genres', [])),
                    'poster_url': str(movie.get('poster', 'https://via.placeholder.com/500x750?text=No+Poster')),
                    'description': str(movie.get('description', 'No description available')),
                    'director': str(movie.get('director', 'Unknown Director')),
                    'cast': list(movie.get('cast', []))[:3],  # Top 3 cast members
                    'rating': float(movie.get('rating', 7.0)),
                    'runtime': int(movie.get('runtime', 120)),
                    'predicted_rating': float(movie.get('prediction_score', 0.7)) * 10,  # Convert to 10 scale
                    'confidence': float(movie.get('confidence', 0.6)),
                    'explanation': str(movie.get('explanation', 'AI recommendation based on your preferences')),
                    'popularity': int(float(movie.get('popularity', 70)))  # Convert float to int
                }
                enhanced_recommendations.append(enhanced_rec)
            except Exception as rec_error:
                logger.warning(f"Error processing recommendation {movie.get('title', 'Unknown')}: {rec_error}")
                continue
        
        # Calculate average rating
        valid_ratings = [r['predicted_rating'] for r in enhanced_recommendations if r.get('predicted_rating')]
        avg_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 7.0
        
        processing_time = (time.time() - start_time) * 1000
        
        return EnhancedBatchResponse(
            recommendations=[EnhancedRecommendationResponse(**rec) for rec in enhanced_recommendations],
            total_movies=DATABASE_STATS.get('total_movies', len(REAL_MOVIES_DATABASE)),
            processing_time_ms=round(processing_time, 2),
            average_rating=round(avg_rating, 1)
        )
        
    except Exception as e:
        logger.error(f"Error processing enhanced recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced recommendation failed: {str(e)}")

def calculate_simple_confidence(user_prefs: Dict[str, float], movie: Dict) -> float:
    """Calculate simple confidence score based on genre matching."""
    # Find user's favorite genres (score > 6)
    favorite_genres = {k: v for k, v in user_prefs.items() if v > 6}
    
    if not favorite_genres:
        return 0.5  # Neutral confidence
    
    # Check genre matches
    movie_genres = [g.lower() for g in movie['genres']]
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

if __name__ == "__main__":
    # Run the API server on port 3000
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=3000,
        reload=False,  # Disable reload to prevent shutdown issues
        log_level="info"
    )