# 🚀 **All Ways to Run the Movie Recommendation System**

## 🎯 **1. FULL WEB APPLICATION (Recommended for Users)**

### **Method 1A: Batch File (Easiest)**
```batch
# Double-click this file
START_SYSTEM.bat
```
- ✅ **One-click startup**
- ✅ **Auto-opens browser**
- ✅ **Full web interface**

### **Method 1B: Direct API Launch**
```powershell
cd "c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender"
python api.py
```
- 🌐 **Access at:** `http://127.0.0.1:3000`
- ⭐ **Features:** Netflix-style UI, 40+ controls, real-time recommendations

### **Method 1C: Uvicorn Command**
```powershell
cd "c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender"
uvicorn api:app --host 127.0.0.1 --port 3000
```
- 🔧 **More control over server settings**
- 📊 **Better logging and debugging**

---

## 🧪 **2. INDIVIDUAL AI COMPONENT TESTING**

### **Method 2A: Fuzzy Logic System Only**
```powershell
cd "c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender"
python -c "from models.fuzzy_model import FuzzyMovieRecommender; engine = FuzzyMovieRecommender(); print('Fuzzy system ready!')"
```
**OR run the built-in test:**
```powershell
python models/fuzzy_model.py
```
- 🧠 **Tests:** 47 fuzzy rules
- 📊 **Output:** Rule evaluation examples
- ⚡ **Fast:** No neural network loading

### **Method 2B: Neural Network (ANN) Only**
```powershell
python models/ann_model.py
```
- 🤖 **Tests:** Enhanced ANN model (14,209 parameters)
- 📈 **Output:** Score predictions and accuracy
- 🎯 **Purpose:** Validate neural network training

### **Method 2C: Hybrid System Test**
```powershell
python models/hybrid_system.py
```
- 🔄 **Tests:** Fuzzy + Neural combination
- ⚖️ **Balance:** 60% fuzzy + 40% neural
- 📊 **Output:** Comparative scores from both systems

---

## 🎬 **3. RECOMMENDATION ENGINE TESTING**

### **Method 3A: Enhanced Engine Test**
```powershell
python enhanced_recommendation_engine.py
```
- 🎪 **Tests all algorithms:** Fuzzy, ANN, Hybrid, Content-based
- 📋 **Output:** Algorithm comparison with sample recommendations
- 🔍 **Purpose:** Validate all recommendation methods

### **Method 3B: Custom Algorithm Test**
```python
from enhanced_recommendation_engine import get_enhanced_recommendations

# Test specific algorithm
user_prefs = {'action': 9, 'comedy': 5, 'thriller': 8}
recs = get_enhanced_recommendations(user_prefs, 'hybrid_fuzzy_ann', 5)
print(recs)
```

---

## 🚀 **4. ADVANCED SERVER CONFIGURATIONS**

### **Method 4A: Development Mode (Auto-reload)**
```powershell
uvicorn api:app --host 127.0.0.1 --port 3000 --reload
```
- 🔄 **Auto-restart** when files change
- 🛠️ **Best for development**

### **Method 4B: Production Mode (Multiple Workers)**
```powershell
uvicorn api:app --host 0.0.0.0 --port 3000 --workers 4
```
- 🏭 **Multiple worker processes**
- 🌐 **Accept external connections**
- ⚡ **Better performance**

### **Method 4C: Custom Port**
```powershell
uvicorn api:app --host 127.0.0.1 --port 8080
```
- 🔌 **Use different port** (if 3000 is busy)
- 🌐 **Access at:** `http://127.0.0.1:8080`

### **Method 4D: Debug Mode**
```powershell
uvicorn api:app --host 127.0.0.1 --port 3000 --log-level debug
```
- 🔍 **Verbose logging**
- 🐛 **Better error tracking**

---

## 📱 **5. COMMAND LINE QUICK TESTS**

### **Method 5A: Health Check**
```powershell
python -c "
import requests
response = requests.get('http://127.0.0.1:3000/health')
print('System Status:', response.json())
"
```

### **Method 5B: Quick Recommendation Test**
```powershell
python -c "
import requests
prefs = {'action': 9, 'comedy': 5}
response = requests.post('http://127.0.0.1:3000/recommend/hybrid', json={'user_preferences': prefs})
print('Sample Recommendations:', response.json()[:2])
"
```

### **Method 5C: Database Stats**
```powershell
python -c "from fast_complete_loader import get_database_stats; print(get_database_stats())"
```

---

## 🔧 **6. SPECIALIZED DEPLOYMENT OPTIONS**

### **Method 6A: Docker (If Available)**
```dockerfile
# Create Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["python", "api.py"]
```

### **Method 6B: Background Service (Windows)**
```powershell
# Run in background (detached)
Start-Process powershell -ArgumentList "-Command", "cd 'c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender'; python api.py" -WindowStyle Hidden
```

### **Method 6C: Scheduled Auto-Start**
```powershell
# Create Windows Task Scheduler entry
schtasks /create /tn "MovieRecommender" /tr "python c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender\api.py" /sc onstart
```

---

## ⚡ **QUICK REFERENCE COMMANDS**

| **Purpose** | **Command** | **Access URL** |
|-------------|-------------|----------------|
| **Full App** | `python api.py` | `http://127.0.0.1:3000` |
| **API Docs** | `python api.py` | `http://127.0.0.1:3000/docs` |
| **Fuzzy Test** | `python models/fuzzy_model.py` | Terminal output |
| **ANN Test** | `python models/ann_model.py` | Terminal output |
| **Hybrid Test** | `python models/hybrid_system.py` | Terminal output |
| **All Algorithms** | `python enhanced_recommendation_engine.py` | Terminal output |

---

## 🎯 **CHOOSING THE RIGHT METHOD**

### **🎬 For Regular Use:**
- Use `START_SYSTEM.bat` or `python api.py`
- Full web interface with all features

### **🧪 For Testing/Development:**
- Individual model files for component testing
- Enhanced engine for algorithm comparison

### **🚀 For Production:**
- Uvicorn with multiple workers
- Custom configuration options

### **🔍 For Debugging:**
- Debug mode with verbose logging
- Individual component testing

**Ready to explore movies with AI? Pick your preferred method and start discovering! 🍿✨**