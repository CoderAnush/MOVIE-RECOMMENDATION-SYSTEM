# 🎬 Movie Recommendation System
**AI-Powered Movie Recommendations using Fuzzy Logic + Neural Networks**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15+-orange.svg)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### 🧠 **Hybrid Intelligence System**
- **Fuzzy Logic Engine**: 47 expert rules for genre matching
- **Neural Network (ANN)**: 19-feature deep learning model
- **Hybrid Scoring**: Adaptive combination of both approaches
- **10,681 Movies**: Complete MovieLens 10M dataset

### 🎯 **Smart Genre Filtering**
- Strict preference-based filtering (0-10 scale)
- Automatic disliked genre rejection (< 4/10)
- High preference prioritization (>= 7/10)
- Diversity factor prevents repetitive results

### 🎨 **Beautiful Netflix-Style UI**
- Modern, responsive design
- Real-time genre preference sliders
- Dynamic movie cards with posters
- Smooth animations and transitions

### ⚡ **Performance Optimized**
- Fast loading with parquet format
- In-memory caching (1000 results)
- Async FastAPI backend
- 70+ real movie posters cached

---

## 🚀 Quick Start

### 1️⃣ **Prerequisites**
```bash
Python 3.10+
pip (Python package manager)
```

### 2️⃣ **Installation**
```bash
# Clone the repository
git clone https://github.com/CoderAnush/MOVIE-RECOMMENDATION-SYSTEM.git
cd MOVIE-RECOMMENDATION-SYSTEM/fuzzy-movie-recommender

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ **Start the System**

**Option A: One-Click Start (Windows)**
```bash
START_SYSTEM.bat
```

**Option B: Manual Start**
```bash
python -m uvicorn api:app --host 127.0.0.1 --port 3000
```

### 4️⃣ **Access the Application**
Open your browser to: **http://127.0.0.1:3000**

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Netflix UI)                    │
│              HTML5 + CSS3 + Vanilla JavaScript              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API
┌──────────────────────────┴──────────────────────────────────┐
│                   FastAPI Backend (Port 3000)                │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │  Fuzzy Logic   │  │      ANN       │  │  Performance  │ │
│  │   Engine       │  │     Model      │  │  Optimizer    │ │
│  │  (47 rules)    │  │  (19 features) │  │   (Caching)   │ │
│  └────────┬───────┘  └────────┬───────┘  └───────┬───────┘ │
│           │                   │                   │          │
│           └───────────┬───────┴───────────────────┘          │
│                       │                                      │
│           ┌───────────▼───────────┐                         │
│           │   Hybrid System       │                         │
│           │  (Adaptive Weighting) │                         │
│           └───────────┬───────────┘                         │
└───────────────────────┼─────────────────────────────────────┘
                        │
            ┌───────────▼───────────┐
            │  MovieLens 10M Dataset│
            │    (10,681 movies)    │
            │   Parquet + Cache     │
            └───────────────────────┘
```

---

## 🎯 How It Works

### Genre Preference System (0-10 Scale)

| Score | Meaning | Behavior |
|-------|---------|----------|
| **0-3** | 🚫 **Dislike** | Movies with this genre are completely filtered out |
| **4-6** | 😐 **Neutral** | Movies considered but not prioritized |
| **7-10** | ❤️ **Love** | Movies MUST match at least one high preference |

### Example Usage

**Your Preferences:**
```
Action:   10/10 ⭐ (Love it!)
Sci-Fi:   9/10  ⭐ (Love it!)
Romance:  2/10  ❌ (Dislike)
Horror:   1/10  ❌ (Hate it!)
```

**Results:**
```
✅ The Matrix (Action, Sci-Fi) - 8.9/10
✅ Blade Runner (Sci-Fi, Thriller) - 8.7/10
✅ Mad Max (Action) - 8.5/10

❌ The Notebook (Romance) - Filtered out
❌ The Conjuring (Horror) - Filtered out
```

---

## 🧪 Technical Details

### Fuzzy Logic Engine
- **47 inference rules** for genre matching
- Mamdani fuzzy inference system
- 7 genre categories: Action, Comedy, Romance, Thriller, Sci-Fi, Drama, Horror
- Quality scoring based on rating, awards, box office

### Neural Network Model
**Architecture:**
- Input: 19 features
  - Movie metadata (5): rating, popularity, year, runtime, budget
  - User preferences (7): genre scores 0-10
  - Genre matching (7): one-hot encoded
- Hidden layers: 2 layers with dropout
- Output: Single score (0-10 prediction)
- Parameters: 3,905 trainable

**Training:**
- Dataset: MovieLens 10M ratings
- Loss: Mean Squared Error
- Optimizer: Adam
- Metrics: MAE, RMSE, R²

### Hybrid Scoring
```python
# Adaptive weighting based on context
if high_agreement:
    score = 0.5 * fuzzy + 0.5 * ann
elif low_agreement:
    score = confidence_weighted(fuzzy, ann, context)
else:
    score = 0.6 * fuzzy + 0.4 * ann

# Add diversity factor
score += random(0, 0.05)
```

---

## 📁 Project Structure

```
fuzzy-movie-recommender/
├── api.py                              # FastAPI backend
├── enhanced_recommendation_engine.py   # Recommendation algorithms
├── fast_complete_loader.py            # Dataset loader
├── performance_optimizer.py            # Caching & optimization
├── real_movies_db_omdb.py             # Movie database
├── requirements.txt                    # Python dependencies
├── START_SYSTEM.bat                   # Windows startup script
├── .env.example                       # Environment variables template
│
├── models/
│   ├── fuzzy_model.py                 # Fuzzy logic engine
│   ├── hybrid_system.py               # Hybrid scoring system
│   ├── enhanced_ann_model.py          # ANN wrapper
│   ├── simple_ann_model.keras         # Trained neural network
│   └── enhanced_ann_model.keras       # Enhanced neural network
│
├── frontend/
│   ├── index.html                     # Main UI
│   ├── netflix_style.css              # Styling
│   └── app_netflix.js                 # Frontend logic
│
├── processed/
│   ├── movies_enriched.parquet        # Preprocessed movie data
│   ├── fast_movie_posters.json        # Cached movie posters
│   └── dataset_summary.json           # Dataset statistics
│
└── docs/
    ├── QUICK_START.md                 # Quick start guide
    ├── SYSTEM_READY.md                # System overview
    ├── GENRE_FILTERING_FIXED.md       # Genre filtering docs
    └── FINAL_SETUP.md                 # Setup documentation
```

---

## 🛠️ API Endpoints

### Main Endpoints
- `GET /` - Serve frontend UI
- `GET /health` - Health check
- `GET /system/status` - System status and metrics
- `POST /recommend/enhanced` - Get movie recommendations

### API Documentation
- **Swagger UI**: http://127.0.0.1:3000/docs
- **ReDoc**: http://127.0.0.1:3000/redoc

### Example Request
```bash
curl -X POST "http://127.0.0.1:3000/recommend/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "user_preferences": {
      "action": 9.0,
      "comedy": 3.0,
      "romance": 2.0,
      "thriller": 7.0,
      "sci_fi": 10.0,
      "drama": 5.0,
      "horror": 1.0
    },
    "num_recommendations": 10
  }'
```

---

## 📊 Performance Metrics

- **Startup Time**: ~30-35 seconds (loads 10M dataset)
- **Recommendation Time**: <100ms per movie (with caching)
- **Memory Usage**: ~500MB (dataset + models in memory)
- **Cache Size**: 1,000 results with 1-hour TTL
- **Concurrent Requests**: Unlimited (async FastAPI)

---

## 🧪 Testing

```bash
# Test dataset loading
python test_dataset.py

# Test ANN model
python test_ann_working.py

# Run all tests
python run_tests.py
```

---

## 🔧 Configuration

Create a `.env` file (copy from `.env.example`):
```env
# API Configuration
API_HOST=127.0.0.1
API_PORT=3000

# Cache Configuration
CACHE_SIZE=1000
CACHE_TTL=3600

# Model Configuration
ANN_MODEL_PATH=models/simple_ann_model.keras
```

---

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
- **[System Overview](SYSTEM_READY.md)** - Complete system documentation
- **[Genre Filtering](GENRE_FILTERING_FIXED.md)** - How genre filtering works
- **[Setup Guide](FINAL_SETUP.md)** - Detailed setup instructions

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Anush** - [CoderAnush](https://github.com/CoderAnush)

---

## 🙏 Acknowledgments

- **MovieLens 10M Dataset** - GroupLens Research
- **FastAPI** - Modern, fast web framework
- **TensorFlow/Keras** - Deep learning framework
- **scikit-fuzzy** - Fuzzy logic toolkit

---

## 📞 Support

For support, please open an issue on GitHub or contact the maintainers.

---

**Made with ❤️ using Fuzzy Logic + Neural Networks**
