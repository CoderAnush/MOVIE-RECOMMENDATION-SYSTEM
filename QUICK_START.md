# 🎬 Movie Recommendation System - Quick Start Guide

## ✅ System Overview

**Full MovieLens 10M Dataset** with:
- ✅ 10,681 movies with real ratings
- ✅ 70+ real movie posters (auto-loaded from cache)
- ✅ Enhanced recommendation scores using Fuzzy Logic + ANN hybrid system
- ✅ Professional Netflix-style frontend interface
- ✅ FastAPI backend with comprehensive endpoints

## 🚀 Quick Start (Easiest Method)

### Option 1: Double-click `START_SYSTEM.bat`
1. Double-click `START_SYSTEM.bat` in this folder
2. Wait 30 seconds for the backend to load the full 10M dataset
3. Browser will open automatically to http://127.0.0.1:3000
4. Start getting recommendations!

### Option 2: Manual Start (More Control)

#### Step 1: Start Backend API (Terminal 1)
```powershell
cd "c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender"
python -m uvicorn api:app --host 127.0.0.1 --port 8080
```

**Wait for this message:**
```
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

This takes ~25-30 seconds as it loads 10,681 movies with metadata.

#### Step 2: Start Frontend Server (Terminal 2)
```powershell
cd "c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender\frontend"
python -m http.server 3000 --bind 127.0.0.1
```

#### Step 3: Open Browser
Navigate to: **http://127.0.0.1:3000**

## 📊 System Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://127.0.0.1:3000 | Main user interface |
| **Backend API** | http://127.0.0.1:8080 | REST API endpoints |
| **API Docs** | http://127.0.0.1:8080/docs | Interactive Swagger documentation |
| **Health Check** | http://127.0.0.1:8080/health | System status |
| **Metrics** | http://127.0.0.1:8080/metrics | Dataset & performance stats |

## 🎯 Features

### Frontend Features
- 🎭 Genre preference sliders (Action, Comedy, Drama, Horror, Romance, Sci-Fi, Thriller)
- 🎨 Quick presets (Action Lover, Comedy Fan, Drama Enthusiast, etc.)
- 🎬 Movie cards with posters, ratings, genres, and descriptions
- 📊 Real-time recommendation scores and confidence levels
- 🔍 Sort by rating, popularity, or recommendation score
- 🎨 Netflix-style dark theme interface

### Backend Features
- **Full 10M Dataset**: 10,681 movies from MovieLens with real ratings
- **Real Posters**: 70+ movies with authentic poster URLs loaded from cache
- **Hybrid Recommendations**: Fuzzy Logic (47 rules) + ANN neural network
- **Smart Scoring**: Genre matching, quality indicators, popularity factors
- **Enhanced Descriptions**: Auto-generated based on genres and ratings
- **Performance Optimization**: Caching system with 1000-item cache
- **Batch Processing**: Get multiple recommendations efficiently

## 🧪 Testing the System

### Test 1: Verify Dataset Loaded
```powershell
python test_dataset.py
```

Expected output:
```
✅ SUCCESS: 10681 movies loaded
📊 Total Movies: 10,681
⭐ Average Rating: 3.51
✅ Real Poster: https://m.media-amazon.com/images/...
```

### Test 2: API Health Check
```powershell
curl http://127.0.0.1:8080/health
```

Expected output:
```json
{
  "status": "healthy",
  "system_ready": true
}
```

### Test 3: Get Recommendation
```powershell
$body = @{
    user_preferences = @{
        action = 9
        comedy = 3
        romance = 2
        thriller = 8
        sci_fi = 7
        drama = 6
        horror = 1
    }
    movie = @{
        title = "The Matrix"
        year = 1999
        genres = @("Action", "Sci-Fi")
        rating = 8.7
        popularity = 95
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://127.0.0.1:8080/recommend" -Method POST -Body $body -ContentType "application/json"
```

## 📁 Key Files

- **`api.py`** - Backend FastAPI server (port 8080)
- **`fast_complete_loader.py`** - Loads full 10M dataset with posters
- **`frontend/index.html`** - Main web interface
- **`frontend/app_netflix.js`** - Frontend JavaScript (connects to port 8080)
- **`frontend/netflix_style.css`** - Netflix-style UI styling
- **`processed/movies_enriched.parquet`** - Full 10M dataset (fast loading)
- **`processed/fast_movie_posters.json`** - Real movie poster URLs (70+ movies)
- **`models/fuzzy_model.py`** - 47-rule fuzzy logic engine
- **`models/hybrid_system.py`** - Hybrid recommendation system
- **`START_SYSTEM.bat`** - One-click startup script

## ⚙️ Configuration

### Backend Port
Currently configured for port **8080** (defined in `api.py` and `run_local.py`)

### Frontend API Connection
Frontend connects to: `http://127.0.0.1:8080` (defined in `frontend/app_netflix.js`)

### Cache Settings
- Cache size: 1000 recommendations
- TTL: 3600 seconds (1 hour)
- Defined in `api.py` line 285

## 🐛 Troubleshooting

### Backend won't start
- **Issue**: ModuleNotFoundError
- **Fix**: Ensure all dependencies installed: `pip install -r requirements.txt`

### Dataset loading slowly
- **Expected**: Takes 25-30 seconds to load 10,681 movies
- **Check**: Look for "✅ Loaded 10681 movies from parquet" message

### Frontend can't connect to backend
- **Issue**: Connection refused
- **Fix**: Ensure backend is running on port 8080
- **Verify**: Visit http://127.0.0.1:8080/health

### No real posters showing
- **Current Status**: 70+ movies have real posters
- **Check**: `processed/fast_movie_posters.json` exists
- **Note**: Other movies use placeholder posters

## 📈 Performance Stats

- **Movies**: 10,681 from MovieLens 10M
- **Real Posters**: 70+ (expandable)
- **Ratings**: Based on 10M+ user ratings
- **Genres**: 20 different genres
- **Year Range**: 1915-2008
- **Average Rating**: 3.51 (normalized to 10-point scale)
- **Recommendation Speed**: ~100ms per movie with caching
- **Fuzzy Rules**: 47 comprehensive rules
- **Cache Hit Rate**: Improves with usage

## 🎬 Usage Example

1. **Open the website**: http://127.0.0.1:3000
2. **Set your preferences**: 
   - Action: 9/10
   - Sci-Fi: 8/10
   - Drama: 7/10
   - Comedy: 3/10
3. **Click "Get AI Recommendations"**
4. **View results**: Movies sorted by recommendation score
5. **Click a movie card**: See detailed information

## 🔧 Advanced Usage

### Get Enhanced Recommendations (API)
```powershell
$body = @{
    user_preferences = @{
        action = 9
        comedy = 3
        romance = 2
        thriller = 8
        sci_fi = 7
        drama = 6
        horror = 1
    }
    num_recommendations = 10
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://127.0.0.1:8080/recommend/enhanced" -Method POST -Body $body -ContentType "application/json"
```

### View System Metrics
Visit: http://127.0.0.1:8080/metrics

Returns:
- Dataset statistics
- Training metrics
- Performance stats
- Cache statistics

## ✅ System Status

- ✅ Full 10M MovieLens dataset loaded
- ✅ Real movie posters (70+ movies, expandable)
- ✅ Enhanced recommendation scores (Fuzzy + ANN hybrid)
- ✅ Professional Netflix-style UI
- ✅ Backend API on port 8080
- ✅ Frontend on port 3000
- ✅ Performance optimization with caching
- ✅ Comprehensive API documentation

## 🎉 You're All Set!

Your complete end-to-end movie recommendation system is ready with:
- Full 10M dataset
- Real movie posters
- Accurate recommendation scores
- Professional web interface

Just run `START_SYSTEM.bat` or follow the manual startup steps above!

---

**Built with ❤️ using FastAPI, Scikit-Fuzzy, TensorFlow, and MovieLens 10M dataset**
