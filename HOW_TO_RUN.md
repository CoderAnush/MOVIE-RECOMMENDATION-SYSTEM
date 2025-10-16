# 🎬 How to Run the Movie Recommendation System

## ✅ **QUICK START - Easiest Method**

### **Method 1: Use the Batch File (Recommended)**
1. **Double-click** `START_SYSTEM.bat` in the main folder
2. **Wait 30-45 seconds** for the system to load (it loads 10,681 movies!)
3. **Browser opens automatically** at `http://127.0.0.1:3000`
4. **Start getting recommendations!** 🎯

### **Method 2: Manual Command Line**
1. **Open PowerShell/Command Prompt**
2. **Navigate to the project folder:**
   ```powershell
   cd "c:\Users\anush\Desktop\MOVIE RECOMMENDATION\fuzzy-movie-recommender"
   ```
3. **Run the system:**
   ```powershell
   python api.py
   ```
4. **Wait for this message:**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:3000 (Press CTRL+C to quit)
   ```
5. **Open browser and go to:** `http://127.0.0.1:3000`

---

## 🖥️ **What You'll See During Startup**

**Loading Process (30-45 seconds):**
```
🚀 Loading Complete MovieLens 10M Database (Fast Mode)...
📊 Using optimized parquet data...
✅ Loaded 10681 movies from parquet
✅ Loaded 20804 real movie posters from cache
🚀 Generating metadata for 10681 movies...
Processed 1000/10681 movies...
Processed 2000/10681 movies...
...
INFO: ✅ Fuzzy control system built with 47 rules
INFO: ✅ Enhanced ANN model and scaler loaded
INFO: ✅ Performance optimization initialized
INFO: Uvicorn running on http://127.0.0.1:3000
```

---

## 🌐 **Access Points**

| **Service** | **URL** | **Description** |
|-------------|---------|-----------------|
| **Main App** | `http://127.0.0.1:3000` | Netflix-style interface |
| **API Docs** | `http://127.0.0.1:3000/docs` | Interactive API documentation |
| **Health Check** | `http://127.0.0.1:3000/health` | System status |

---

## 🎯 **Features Available**

### **✨ User Interface**
- 🎨 **Netflix-style design** with dark theme
- 🎛️ **40+ preference controls** (genre sliders, mood buttons)
- 🎭 **19 movie genres** with intelligent mapping
- 🔍 **Smart search** with filters
- 📱 **Responsive design** (works on mobile)

### **🤖 AI Recommendation Engine**
- 🧠 **Hybrid AI System:** Fuzzy Logic + Neural Network
- 📊 **Real Data:** MovieLens 10M dataset (10,000,054+ ratings)
- ⚡ **Performance Optimized:** Caching with 3600s TTL
- 🎪 **Advanced Algorithms:** Mood matching, genre compatibility

### **📊 Real Movie Database**
- 🎬 **10,681 authentic movies** (1915-2008)
- ⭐ **Real user ratings** from 69,878 users
- 🖼️ **20,804+ movie posters** from TMDB
- 🏷️ **Rich metadata:** Cast, directors, popularity scores

---

## 🔧 **Troubleshooting**

### **❌ Port Already in Use Error**
```bash
Error: [Errno 48] Address already in use
```
**Solution:** Stop any existing process on port 3000:
```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### **❌ Module Import Errors**
```bash
ModuleNotFoundError: No module named 'fastapi'
```
**Solution:** Install dependencies:
```powershell
pip install -r requirements.txt
```

### **❌ Slow Loading**
**Expected:** First startup takes 30-45 seconds to load 10,681 movies  
**Normal:** Subsequent requests are cached and much faster

---

## 🚀 **System Requirements**

- **Python 3.8+**
- **4GB+ RAM** (for loading 10M dataset)
- **1GB+ disk space** (for models and data)
- **Modern browser** (Chrome, Firefox, Safari, Edge)

---

## 🎬 **Quick Test**

1. **Start system:** `python api.py`
2. **Wait for:** `Uvicorn running on http://127.0.0.1:3000`
3. **Open browser:** `http://127.0.0.1:3000`
4. **Test recommendation:** Set some preferences and click "Get Recommendations"
5. **Enjoy your personalized movie suggestions!** 🍿

---

## 🆘 **Need Help?**

- **Check logs** in the terminal for error messages
- **Verify all files** are in the correct folder structure
- **Ensure Python dependencies** are installed (`pip install -r requirements.txt`)
- **Check system resources** (RAM usage during startup)

**Ready to discover your next favorite movie?** 🎬✨