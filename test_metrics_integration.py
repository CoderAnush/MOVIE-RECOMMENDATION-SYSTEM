#!/usr/bin/env python
"""
Test script to verify metrics integration is working correctly.
"""

import sys
import os
import json
import requests
from time import sleep

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = 1
MOVIE_ID = 1

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test that API is running."""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is running!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Make sure API is running at {BASE_URL}")
        return False

def test_recommendation():
    """Test recommendation endpoint and metrics."""
    print_section("2. Test Recommendation with Metrics")
    try:
        payload = {
            "user_id": USER_ID,
            "movie_id": MOVIE_ID,
            "num_recommendations": 5,
            "strategy": "adaptive"
        }
        
        print(f"Sending request:\n{json.dumps(payload, indent=2)}\n")
        response = requests.post(f"{BASE_URL}/recommend", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Recommendation request successful!")
            
            # Display main results
            print(f"\n📽️  Recommendations:")
            if "recommendations" in result:
                for i, movie in enumerate(result["recommendations"][:3], 1):
                    print(f"   {i}. {movie.get('title', 'Unknown')} (Score: {movie.get('score', 0):.2f})")
            
            # Display per-request metrics
            if "metrics" in result and result["metrics"]:
                print(f"\n⏱️  Per-Request Metrics:")
                metrics = result["metrics"]
                print(f"   Total Time: {metrics.get('total_time_ms', 0):.2f} ms")
                print(f"   Fuzzy Time: {metrics.get('fuzzy_time_ms', 0):.2f} ms")
                print(f"   ANN Time: {metrics.get('ann_time_ms', 0):.2f} ms")
                print(f"   Combination Time: {metrics.get('combination_time_ms', 0):.2f} ms")
                print(f"   Fuzzy Score: {metrics.get('fuzzy_score', 0):.4f}")
                print(f"   ANN Score: {metrics.get('ann_score', 0):.4f}")
                print(f"   Hybrid Score: {metrics.get('hybrid_score', 0):.4f}")
                print(f"   Confidence: {metrics.get('confidence', 0):.4f}")
                print(f"   Strategy: {metrics.get('strategy', 'N/A')}")
            
            # Display system metrics
            if "system_metrics" in result and result["system_metrics"]:
                print(f"\n📊 System Metrics:")
                sys_metrics = result["system_metrics"]
                print(f"   Total Requests: {sys_metrics.get('total_requests', 0)}")
                if "performance" in sys_metrics:
                    perf = sys_metrics["performance"]
                    print(f"   Avg Latency: {perf.get('avg_latency_ms', 0):.2f} ms")
                    print(f"   P95 Latency: {perf.get('p95_latency_ms', 0):.2f} ms")
                    print(f"   P99 Latency: {perf.get('p99_latency_ms', 0):.2f} ms")
                    print(f"   Max Latency: {perf.get('max_latency_ms', 0):.2f} ms")
                if "scores" in sys_metrics:
                    scores = sys_metrics["scores"]
                    print(f"   Avg Hybrid Score: {scores.get('avg_hybrid_score', 0):.4f}")
                    print(f"   Avg Confidence: {scores.get('avg_confidence', 0):.4f}")
            
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during recommendation: {e}")
        return False

def test_performance_metrics_endpoint():
    """Test the dedicated metrics endpoint."""
    print_section("3. Test Performance Metrics Endpoint")
    try:
        print("Querying /performance-metrics endpoint...\n")
        response = requests.get(f"{BASE_URL}/performance-metrics")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Performance metrics endpoint successful!")
            
            print(f"\n📈 Accumulated System Metrics:")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            
            if "recommendation_metrics" in result:
                metrics = result["recommendation_metrics"]
                print(f"\n   Request Statistics:")
                print(f"      Total Requests: {metrics.get('total_requests', 0)}")
                print(f"      Uptime: {metrics.get('uptime_seconds', 0):.1f} seconds")
                
                if "performance" in metrics:
                    perf = metrics["performance"]
                    print(f"\n   Latency Statistics:")
                    print(f"      Avg: {perf.get('avg_latency_ms', 0):.2f} ms")
                    print(f"      Min: {perf.get('min_latency_ms', 0):.2f} ms")
                    print(f"      Max: {perf.get('max_latency_ms', 0):.2f} ms")
                    print(f"      P95: {perf.get('p95_latency_ms', 0):.2f} ms")
                    print(f"      P99: {perf.get('p99_latency_ms', 0):.2f} ms")
                
                if "scores" in metrics:
                    scores = metrics["scores"]
                    print(f"\n   Score Statistics:")
                    print(f"      Avg Fuzzy: {scores.get('avg_fuzzy_score', 0):.4f}")
                    print(f"      Avg ANN: {scores.get('avg_ann_score', 0):.4f}")
                    print(f"      Avg Hybrid: {scores.get('avg_hybrid_score', 0):.4f}")
                
                if "throughput" in metrics:
                    throughput = metrics["throughput"]
                    print(f"\n   Throughput:")
                    print(f"      Requests/sec: {throughput.get('requests_per_sec', 0):.2f}")
            
            if "strategy_distribution" in result:
                print(f"\n   Strategy Distribution:")
                for strategy, count in result["strategy_distribution"].items():
                    print(f"      {strategy}: {count} requests")
            
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error querying metrics: {e}")
        return False

def test_multiple_recommendations():
    """Make multiple recommendations to test aggregation."""
    print_section("4. Test Metrics Aggregation (5 requests)")
    try:
        for i in range(5):
            payload = {
                "user_id": (USER_ID + i) % 100,
                "movie_id": (MOVIE_ID + i) % 100,
                "num_recommendations": 3,
                "strategy": ["adaptive", "fuzzy_dominant", "ann_dominant", "weighted_average", "confidence_weighted"][i % 5]
            }
            response = requests.post(f"{BASE_URL}/recommend", json=payload)
            if response.status_code == 200:
                print(f"✅ Request {i+1}/5 successful")
                sleep(0.1)  # Small delay between requests
            else:
                print(f"❌ Request {i+1}/5 failed: {response.status_code}")
                return False
        
        print("\n✅ All requests completed! Querying aggregated metrics...\n")
        sleep(0.5)  # Let metrics settle
        return test_performance_metrics_endpoint()
    except Exception as e:
        print(f"❌ Error during multiple requests: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  METRICS INTEGRATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    
    if results[-1][1]:  # Only continue if API is running
        results.append(("Recommendation with Metrics", test_recommendation()))
        results.append(("Performance Metrics Endpoint", test_performance_metrics_endpoint()))
        results.append(("Metrics Aggregation", test_multiple_recommendations()))
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Metrics integration is working correctly!\n")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
