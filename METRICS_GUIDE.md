# Metrics Integration Guide

## Overview

The Movie Recommendation API now includes a comprehensive **real-time performance metrics tracking system**. When the model is called, metrics are automatically captured, recorded, and made available through multiple endpoints.

## What Gets Tracked

Each recommendation request tracks the following metrics:

### Per-Request Metrics
- **Total Time**: End-to-end request processing time (ms)
- **Fuzzy Time**: Time spent in fuzzy logic engine (ms)
- **ANN Time**: Time spent in neural network (ms)
- **Combination Time**: Time to merge fuzzy and ANN scores (ms)
- **Fuzzy Score**: Output from fuzzy logic engine (0-1)
- **ANN Score**: Output from neural network (0-1)
- **Hybrid Score**: Final combined recommendation score (0-1)
- **Confidence**: Confidence level in recommendation (0-1)
- **Strategy**: Algorithm combination strategy used
- **ANN Available**: Whether ANN model was used

### System-Wide Metrics
- **Total Requests**: Cumulative requests processed
- **Uptime**: Seconds since system startup
- **Performance Statistics**:
  - Average latency (ms)
  - Min/Max latency (ms)
  - P95/P99 percentile latencies (ms)
- **Score Statistics**:
  - Average fuzzy score
  - Average ANN score
  - Average hybrid score
  - Average confidence
- **Throughput**: Requests per second
- **Strategy Distribution**: How often each strategy is used

## Endpoints

### 1. Recommendation with Metrics
**`POST /recommend`**

Returns recommendation plus real-time metrics.

**Response includes:**
```json
{
  "recommendations": [...],
  "fuzzy_score": 0.85,
  "ann_score": 0.82,
  "hybrid_score": 0.835,
  "confidence": 0.91,
  "strategy": "adaptive",
  "metrics": {
    "total_time_ms": 125.34,
    "fuzzy_time_ms": 45.12,
    "ann_time_ms": 72.89,
    "combination_time_ms": 7.33,
    "fuzzy_score": 0.85,
    "ann_score": 0.82,
    "hybrid_score": 0.835,
    "confidence": 0.91,
    "strategy": "adaptive",
    "ann_available": true
  },
  "system_metrics": {
    "total_requests": 42,
    "uptime_seconds": 156.78,
    "performance": {
      "avg_latency_ms": 118.45,
      "min_latency_ms": 95.23,
      "max_latency_ms": 145.67,
      "p95_latency_ms": 135.89,
      "p99_latency_ms": 142.34
    },
    "scores": {
      "avg_fuzzy_score": 0.823,
      "avg_ann_score": 0.801,
      "avg_hybrid_score": 0.812,
      "avg_confidence": 0.889
    },
    "throughput": {
      "requests_per_sec": 0.268
    }
  }
}
```

### 2. Performance Metrics Endpoint
**`GET /performance-metrics`**

Get accumulated system metrics and recent request history.

**Response:**
```json
{
  "status": "operational",
  "timestamp": 1699564891.234,
  "recommendation_metrics": {
    "total_requests": 42,
    "uptime_seconds": 156.78,
    "performance": {
      "avg_latency_ms": 118.45,
      "min_latency_ms": 95.23,
      "max_latency_ms": 145.67,
      "p95_latency_ms": 135.89,
      "p99_latency_ms": 142.34
    },
    "scores": {
      "avg_fuzzy_score": 0.823,
      "avg_ann_score": 0.801,
      "avg_hybrid_score": 0.812,
      "avg_confidence": 0.889
    },
    "throughput": {
      "requests_per_sec": 0.268
    }
  },
  "recent_requests": [
    {
      "timestamp": 1699564885.123,
      "total_time_ms": 125.34,
      "fuzzy_score": 0.85,
      "ann_score": 0.82,
      "hybrid_score": 0.835,
      "strategy": "adaptive"
    },
    ...
  ],
  "strategy_distribution": {
    "adaptive": 15,
    "fuzzy_dominant": 8,
    "ann_dominant": 10,
    "weighted_average": 5,
    "confidence_weighted": 4
  }
}
```

### 3. Metrics History (Legacy)
**`GET /metrics`**

Returns simple metrics summary.

## How to Use

### 1. Start the API

```bash
python api.py
```

The startup event will:
- Initialize the metrics collector
- Log: `✅ Metrics collector initialized`

### 2. Make a Recommendation Request

```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "movie_id": 100,
    "num_recommendations": 5,
    "strategy": "adaptive"
  }'
```

**Console output will show:**
```
============================================================
                    METRICS DISPLAY
============================================================
Timestamp: 2024-01-15 10:30:45.123456
Request Processing Time: 125.34 ms

  Fuzzy Processing:        45.12 ms
  ANN Processing:          72.89 ms
  Combination:              7.33 ms

Scores:
  Fuzzy Score:             0.8500
  ANN Score:               0.8200
  Hybrid Score:            0.8350
  Confidence:              0.9100

Strategy Used: adaptive
ANN Available: Yes

System Aggregates (42 total requests):
  Avg Latency:            118.45 ms
  P95 Latency:            135.89 ms
  P99 Latency:            142.34 ms
  Throughput:              0.27 req/s

============================================================
```

### 3. Query System Metrics

```bash
curl "http://localhost:8000/performance-metrics"
```

### 4. Run Integration Tests

```bash
python test_metrics_integration.py
```

This will:
- ✅ Check API health
- ✅ Make a recommendation request and display metrics
- ✅ Query the metrics endpoint
- ✅ Make 5 more requests to test aggregation
- ✅ Display summary statistics

## Implementation Details

### File: `models/metrics.py`

**Key Components:**

1. **RequestMetrics Dataclass** (Lines 22-33)
   - Data structure for a single request's metrics
   - 11 fields tracking all timing and score information
   - Immutable and thread-safe

2. **MetricsCollector Class** (Lines 36-259)
   - Thread-safe metrics collection with Lock
   - Deque-based circular history (default: 1000 requests)
   - Automatic aggregation of statistics
   - Methods:
     - `record_metric(metric)` - Add a new metric
     - `get_performance_summary()` - Get aggregated stats
     - `get_recent_metrics(n)` - Get last N requests
     - `get_strategy_distribution()` - Strategy usage breakdown

3. **Module Functions**
   - `initialize_metrics()` - Create global collector on startup
   - `get_metrics_collector()` - Access the collector
   - `record_recommendation_metrics(...)` - Record a request
   - `get_system_metrics()` - Get summary snapshot
   - `format_metrics_display()` - Pretty-print formatting

### File: `api.py` (Modified)

**Changes Made:**

1. **Startup Event** (Line ~529)
   - Added metrics initialization on startup

2. **Response Models** (Lines ~461-475)
   - `RecommendationResponse`: Added `metrics` and `system_metrics` fields
   - `BatchRecommendationResponse`: Added `system_metrics` field

3. **POST /recommend Endpoint** (Lines ~743-825)
   - Added timing: `request_start = time.time()`
   - Calculate total time
   - Extract component times from result
   - Record metrics: `record_recommendation_metrics(...)`
   - Get system metrics: `get_system_metrics()`
   - Log formatted display: `logger.info(format_metrics_display())`
   - Include metrics in response

4. **GET /performance-metrics Endpoint** (Lines ~615-650)
   - New endpoint for metrics queries
   - Returns accumulated statistics
   - Includes recent requests and strategy distribution

## Performance Characteristics

- **Memory Usage**: ~500 KB for 1000-request history (configurable)
- **Latency Overhead**: <1 ms per request (metrics recording)
- **Thread Safety**: All operations protected with Lock
- **Circular Buffer**: Automatically evicts oldest metrics when full

## Customization

### Change History Size

In `api.py` startup event:
```python
from models.metrics import get_metrics_collector
collector = get_metrics_collector()
# Collector has default max_history of 1000
```

### Access Raw Metrics

```python
from models.metrics import get_metrics_collector

collector = get_metrics_collector()

# Get recent 10 requests
recent = collector.get_recent_metrics(10)

# Get performance summary
summary = collector.get_performance_summary()

# Get strategy usage
strategies = collector.get_strategy_distribution()
```

### Custom Metrics Processing

```python
from models.metrics import get_metrics_collector
import json

collector = get_metrics_collector()
metrics_history = collector.metrics

# Export to JSON
metrics_list = [json.loads(json.dumps(asdict(m))) for m in metrics_history]
with open('metrics_export.json', 'w') as f:
    json.dump(metrics_list, f, indent=2)
```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Latency**
   - Alert if P95 > 200ms
   - Alert if P99 > 300ms

2. **Throughput**
   - Expected: 5-10 req/sec for production
   - Alert if < 1 req/sec (system degradation)

3. **Confidence**
   - Alert if avg_confidence < 0.70
   - Indicates model uncertainty

4. **ANN Availability**
   - Alert if falling back to fuzzy-only
   - Indicates ANN issues

### Example: Simple Monitoring Script

```python
import requests
import time

while True:
    response = requests.get("http://localhost:8000/performance-metrics")
    metrics = response.json()
    
    perf = metrics["recommendation_metrics"]["performance"]
    
    if perf["p95_latency_ms"] > 200:
        print("⚠️  P95 Latency HIGH:", perf["p95_latency_ms"])
    
    if metrics["recommendation_metrics"]["throughput"]["requests_per_sec"] < 1:
        print("⚠️  Throughput LOW:", metrics["recommendation_metrics"]["throughput"])
    
    time.sleep(60)
```

## Troubleshooting

### Metrics Not Appearing in Response

1. Check that `initialize_metrics()` is called in startup
2. Check `models/metrics.py` exists and imports correctly
3. Check for import errors in logs

### High Latency

1. Check `ann_time_ms` vs `fuzzy_time_ms`
   - High ANN time → neural network bottleneck
   - High fuzzy time → fuzzy engine bottleneck
2. Check system resources (CPU, memory)
3. Check data size (num_recommendations)

### Strategy Not Changing

1. Strategy selection is automatic based on data quality
2. Check `strategy_distribution` to see actual usage
3. Fuzzy takes priority if ANN unavailable
4. Adaptive chooses based on confidence scores

## Next Steps

Potential enhancements:

1. **WebSocket Streaming**
   - Real-time metrics push to clients
   - Live dashboard updates

2. **Metrics Export**
   - CSV/JSON export endpoints
   - Prometheus metrics format

3. **Alerts System**
   - Threshold-based alerting
   - Email/Slack notifications

4. **Dashboard**
   - Web UI for metrics visualization
   - Graphs and charts

5. **Metrics Reset**
   - Endpoint to clear history
   - Periodic auto-reset option
