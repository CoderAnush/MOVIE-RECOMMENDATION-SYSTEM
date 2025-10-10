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
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
import uvicorn
import logging
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from models.fuzzy_model import FuzzyMovieRecommender
from final_hybrid_demo import FinalHybridSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Global system instance
hybrid_system = None

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
    system_ready: bool

@app.on_event("startup")
async def startup_event():
    """Initialize the hybrid recommendation system on startup."""
    global hybrid_system
    try:
        logger.info("🚀 Initializing Movie Recommendation API...")
        hybrid_system = FinalHybridSystem()
        logger.info("✅ Hybrid recommendation system initialized successfully")
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
            system_ready=True
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@app.post("/recommend", response_model=RecommendationResponse)
async def get_recommendation(request: RecommendationRequest):
    """Get a single movie recommendation."""
    if not hybrid_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = time.time()
    
    try:
        # Convert Pydantic models to dictionaries
        user_prefs = request.user_preferences.dict()
        movie_info = request.movie.dict()
        watch_history = request.watch_history.dict() if request.watch_history else None
        
        # Get recommendation
        result = hybrid_system.recommend(
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
        
        processing_time = (time.time() - start_time) * 1000
        
        return RecommendationResponse(
            movie_title=result['movie_title'],
            fuzzy_score=result['fuzzy_score'],
            ann_score=result['ann_score'],
            hybrid_score=result['hybrid_score'],
            strategy=result['strategy'],
            agreement=result['agreement'],
            recommendation_level=level,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error processing recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@app.post("/recommend/batch", response_model=BatchRecommendationResponse)
async def get_batch_recommendations(request: BatchRecommendationRequest):
    """Get recommendations for multiple movies."""
    if not hybrid_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = time.time()
    recommendations = []
    
    try:
        user_prefs = request.user_preferences.dict()
        watch_history = request.watch_history.dict() if request.watch_history else None
        
        for movie in request.movies:
            movie_start_time = time.time()
            movie_info = movie.dict()
            
            # Get recommendation
            result = hybrid_system.recommend(
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
            
            movie_processing_time = (time.time() - movie_start_time) * 1000
            
            recommendations.append(RecommendationResponse(
                movie_title=result['movie_title'],
                fuzzy_score=result['fuzzy_score'],
                ann_score=result['ann_score'],
                hybrid_score=result['hybrid_score'],
                strategy=result['strategy'],
                agreement=result['agreement'],
                recommendation_level=level,
                processing_time_ms=round(movie_processing_time, 2)
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

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Movie Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "system_status": "/system/status",
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

if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )