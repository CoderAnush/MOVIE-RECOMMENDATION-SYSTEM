#!/usr/bin/env python3
"""
Simple test to verify metrics are being logged and displayed
Run this while the API is running on port 3000
"""

import requests
import json
import time

API_URL = "http://localhost:3000"

def test_enhanced_recommend():
    """Test the /recommend/enhanced endpoint"""
    print("\n" + "="*60)
    print("🚀 Testing /recommend/enhanced endpoint")
    print("="*60)
    
    payload = {
        "user_preferences": {
            "action": 8,
            "comedy": 7,
            "romance": 6,
            "thriller": 7,
            "drama": 8,
            "horror": 5,
            "sci_fi": 8,
            "fantasy": 7,
            "adventure": 8
        },
        "num_recommendations": 5
    }
    
    try:
        print(f"\n📤 Sending POST request to {API_URL}/recommend/enhanced")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}\n")
        
        response = requests.post(
            f"{API_URL}/recommend/enhanced",
            json=payload,
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Results:")
            print(f"   Total recommendations: {data.get('total_movies')}")
            print(f"   Processing time: {data.get('processing_time_ms')}ms")
            print(f"   Average rating: {data.get('average_rating')}")
            
            if data.get('recommendations'):
                print(f"\n🎬 Top 3 Recommendations:")
                for i, rec in enumerate(data['recommendations'][:3], 1):
                    print(f"   {i}. {rec.get('title')} (Score: {rec.get('score'):.2f})")
            
            print(f"\n✅ SUCCESS! Check the API console (Terminal 1) for formatted metrics display")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_recommend_endpoint():
    """Test the /recommend endpoint with proper schema"""
    print("\n" + "="*60)
    print("🚀 Testing /recommend endpoint")
    print("="*60)
    
    payload = {
        "user_preferences": {
            "action": 8,
            "comedy": 7,
            "romance": 6,
            "thriller": 7,
            "drama": 8,
            "horror": 5,
            "sci_fi": 8
        },
        "movie": {
            "title": "Test Action Movie",
            "genres": ["Action", "Thriller"],
            "popularity": 85,
            "year": 2023
        },
        "strategy": "adaptive"
    }
    
    try:
        print(f"\n📤 Sending POST request to {API_URL}/recommend")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}\n")
        
        response = requests.post(
            f"{API_URL}/recommend",
            json=payload,
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Results:")
            print(f"   Movie Title: {data.get('movie_title')}")
            print(f"   Fuzzy Score: {data.get('fuzzy_score'):.2f}")
            print(f"   ANN Score: {data.get('ann_score'):.2f}")
            print(f"   Hybrid Score: {data.get('hybrid_score'):.2f}")
            print(f"   Processing Time: {data.get('processing_time_ms')}ms")
            
            print(f"\n✅ SUCCESS! Check the API console (Terminal 1) for formatted metrics display")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_performance_metrics():
    """Query accumulated metrics from /performance-metrics endpoint"""
    print("\n" + "="*60)
    print("📈 Fetching accumulated performance metrics")
    print("="*60)
    
    try:
        print(f"\n📤 Sending GET request to {API_URL}/performance-metrics\n")
        
        response = requests.get(
            f"{API_URL}/performance-metrics",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metrics Summary:")
            print(f"   Total Requests: {data.get('total_requests')}")
            print(f"   Avg Processing Time: {data.get('avg_processing_time_ms'):.2f}ms")
            print(f"   Avg Fuzzy Score: {data.get('avg_fuzzy_score'):.2f}")
            print(f"   Avg ANN Score: {data.get('avg_ann_score'):.2f}")
            print(f"   Avg Hybrid Score: {data.get('avg_hybrid_score'):.2f}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 MOVIE RECOMMENDATION METRICS TEST")
    print("="*60)
    print("\n⚠️  Make sure the API is running: python api.py")
    print("💡 This test will send requests and show metrics display\n")
    
    # Test enhanced endpoint (most reliable)
    if test_enhanced_recommend():
        print("\n✅ Enhanced endpoint working!")
        time.sleep(1)
    else:
        print("\n❌ Enhanced endpoint failed")
    
    # Test regular endpoint (for single recommendations)
    print("\n" + "-"*60)
    if test_recommend_endpoint():
        print("\n✅ Regular endpoint working!")
        time.sleep(1)
    else:
        print("\n❌ Regular endpoint failed (this is optional)")
    
    # Show accumulated metrics
    print("\n" + "-"*60)
    if test_performance_metrics():
        print("\n✅ Metrics accumulated successfully!")
    else:
        print("\n⚠️  Could not fetch metrics")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE!")
    print("="*60)
    print("\n👉 Check the API console (Terminal 1) for formatted metrics display!")
    print("   Look for metric blocks like:")
    print("   ╔═══════════════════════════════════════╗")
    print("   ║      📊 RECOMMENDATION METRICS        ║")
    print("   ║═══════════════════════════════════════║")
    print("   └───────────────────────────────────────┘\n")
