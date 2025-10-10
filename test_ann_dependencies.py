"""
Simple ANN Model Test - Check Dependencies
==========================================

Test if we can create a basic ANN model with available dependencies.
"""

import numpy as np
import pandas as pd

# Test TensorFlow import
try:
    import tensorflow as tf
    print(f"✅ TensorFlow version: {tf.__version__}")
    
    # Try importing keras
    try:
        from tensorflow import keras
        print("✅ Keras imported from TensorFlow")
    except ImportError:
        try:
            import keras
            print("✅ Keras imported standalone")
        except ImportError:
            print("❌ Keras not available")
            keras = None
    
    # Test basic model creation
    if keras:
        model = keras.Sequential([
            keras.layers.Dense(32, activation='relu', input_shape=(10,)),
            keras.layers.Dense(1, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse')
        print("✅ Basic model created successfully")
        
        # Test with dummy data
        X_test = np.random.random((100, 10))
        y_test = np.random.random((100, 1))
        
        # Test prediction
        predictions = model.predict(X_test, verbose=0)
        print(f"✅ Model prediction test: shape {predictions.shape}")
        
except ImportError as e:
    print(f"❌ TensorFlow import failed: {e}")
    keras = None

# Test other dependencies
try:
    from sklearn.model_selection import train_test_split
    print("✅ scikit-learn available")
except ImportError:
    print("❌ scikit-learn import failed")

# Test if we have the data
import os
csv_path = "processed/preprocessed_movielens10M.csv"
if os.path.exists(csv_path):
    print(f"✅ Training data found: {csv_path}")
    
    # Load a small sample to test
    try:
        data = pd.read_csv(csv_path, nrows=1000)
        print(f"✅ Sample data loaded: {data.shape}")
        print(f"   Columns: {list(data.columns)}")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
else:
    print(f"❌ Training data not found: {csv_path}")

print("\n" + "="*50)
if keras:
    print("✅ Ready to create ANN model!")
else:
    print("❌ Cannot create ANN model - missing dependencies")
print("="*50)