# 📊 Metrics System - Visual Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER REQUEST FLOW                           │
└─────────────────────────────────────────────────────────────────┘

                          Client
                             │
                             │ POST /recommend
                             │ {user_id, movie_id, num_recommendations}
                             ▼
                    ┌─────────────────┐
                    │   API Gateway   │
                    │   (FastAPI)     │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌───────────────────┐    ┌──────────────────┐
        │ /recommend        │    │ /performance-    │
        │ Endpoint          │    │ metrics          │
        │ (POST)            │    │ Endpoint (GET)   │
        └────────┬──────────┘    └────────┬─────────┘
                 │                        │
                 │                        │ Query accumulated
                 │ Start timing           │ statistics
                 ▼                        │
         ┌──────────────────┐             │
         │ Request Start    │             │
         │ Timer            │             │
         └─────────┬────────┘             │
                   │                      │
                   │ Call recommendation  │
                   │ engine               │
                   ▼                      │
         ┌──────────────────┐             │
         │ Fuzzy Logic      │             │
         │ ├─ Score: 0.85   │             │
         │ └─ Time: 45.12ms │             │
         └────────┬─────────┘             │
                  │                       │
                  ├─ +                    │
                  │  ▼                    │
         ┌──────────────────┐             │
         │ ANN Neural Net   │             │
         │ ├─ Score: 0.82   │             │
         │ └─ Time: 72.89ms │             │
         └────────┬─────────┘             │
                  │                       │
                  │ Combine scores        │
                  ▼                       │
         ┌──────────────────┐             │
         │ Merge Results    │             │
         │ ├─ Hybrid: 0.835 │             │
         │ ├─ Confidence: 91%│            │
         │ └─ Time: 7.33ms  │             │
         └────────┬─────────┘             │
                  │                       │
         Calculate Total Time             │
         (time.now() - start) * 1000      │
         └─ Total: 125.34ms ─────┐        │
                                 │        │
                ┌────────────────┘        │
                │ Create RequestMetrics   │
                │                         │
                ▼                         │
    ┌──────────────────────────┐          │
    │ RequestMetrics Object    │          │
    ├─ timestamp: 1699564885.123         │
    ├─ total_time_ms: 125.34  │          │
    ├─ fuzzy_time_ms: 45.12   │          │
    ├─ ann_time_ms: 72.89     │          │
    ├─ combination_time_ms: 7.33         │
    ├─ fuzzy_score: 0.85      │          │
    ├─ ann_score: 0.82        │          │
    ├─ hybrid_score: 0.835    │          │
    ├─ confidence: 0.91       │          │
    ├─ strategy: "adaptive"   │          │
    └─ ann_available: true    │          │
                 │            │          │
                 │ Record in  │          │
                 ▼            │          │
    ┌──────────────────────────┐          │
    │   MetricsCollector       │          │
    │   (Thread-Safe)          │          │
    │ ┌──────────────────────┐ │          │
    │ │ Metrics Deque        │ │          │
    │ │ maxlen=1000          │ │          │
    │ │ [Request1, Req2, ..] │ │          │
    │ └──────────────────────┘ │          │
    │ ┌──────────────────────┐ │          │
    │ │ Lock (threading)     │ │          │
    │ │ Thread-Safe Ops      │ │          │
    │ └──────────────────────┘ │          │
    │ ┌──────────────────────┐ │          │
    │ │ Aggregation Logic    │ │          │
    │ │ ├─ avg_latency_ms    │ │          │
    │ │ ├─ p95_latency_ms    │ │          │
    │ │ ├─ p99_latency_ms    │ │          │
    │ │ └─ throughput        │ │          │
    │ └──────────────────────┘ │          │
    └──────────┬───────────────┘          │
               │                          │
               │ Calculate Aggregates     │
               ▼                          │
    ┌──────────────────────────┐          │
    │ System Metrics           │          │
    │ ├─ total_requests: 42    │          │
    │ ├─ uptime_seconds: 156.78│          │
    │ ├─ Performance:          │          │
    │ │  ├─ avg_latency: 118.45│          │
    │ │  ├─ min_latency: 95.23 │          │
    │ │  ├─ max_latency: 145.67│          │
    │ │  ├─ p95: 135.89        │          │
    │ │  └─ p99: 142.34        │          │
    │ ├─ Scores:               │          │
    │ │  ├─ avg_fuzzy: 0.823   │          │
    │ │  ├─ avg_ann: 0.801     │          │
    │ │  ├─ avg_hybrid: 0.812  │          │
    │ │  └─ avg_confidence: 0.89│         │
    │ ├─ Throughput: 0.27 req/s│         │
    │ └─ Strategy Distribution │          │
    └──────────┬───────────────┘          │
               │                          │
               │                          │ Query aggregates
               │                          │ (no params)
               │                          ▼
               │              ┌──────────────────────┐
               │              │ Get Performance      │
               │              │ Summary from         │
               │              │ MetricsCollector     │
               │              └──────────┬───────────┘
               │                         │
            Log Formatted Display        │
               │                         │
               │        ┌────────────────┘
               │        │
               │        ▼
        ┌──────┴──────────────────────┐
        │ Create Response Object      │
        ├─ recommendations: [...]     │
        ├─ hybrid_score: 0.835        │
        ├─ confidence: 0.91           │
        ├─ metrics:                   │ ◄─── NEW!
        │ │ ├─ total_time_ms: 125.34  │
        │ │ ├─ fuzzy_time_ms: 45.12   │
        │ │ ├─ ann_time_ms: 72.89     │
        │ │ ├─ fuzzy_score: 0.85      │
        │ │ ├─ ann_score: 0.82        │
        │ │ ├─ hybrid_score: 0.835    │
        │ │ ├─ confidence: 0.91       │
        │ │ └─ strategy: "adaptive"   │
        │ └─ system_metrics:          │ ◄─── NEW!
        │   ├─ total_requests: 42     │
        │   ├─ uptime_seconds: 156.78 │
        │   ├─ performance: {...}     │
        │   ├─ scores: {...}          │
        │   └─ throughput: {...}      │
        └──────┬─────────────────────┘
               │
        HTTP 200 OK
               │
               ▼
        ┌──────────────────────────┐
        │ Client receives response │
        │ with full metrics data   │
        └──────────────────────────┘

        For /performance-metrics:
               │
               ├─ status: "operational"
               ├─ timestamp: 1699564891.234
               ├─ recommendation_metrics: (full summary)
               ├─ recent_requests: (last 10)
               └─ strategy_distribution: (usage counts)
```

---

## Data Structure Diagram

```
RequestMetrics (Dataclass)
├─ timestamp: float
│  └─ ISO timestamp when request completed
│
├─ total_time_ms: float
│  └─ Total request processing time
│
├─ fuzzy_time_ms: float
│  └─ Time in fuzzy logic engine
│
├─ ann_time_ms: float
│  └─ Time in neural network
│
├─ combination_time_ms: float
│  └─ Time to merge fuzzy + ANN scores
│
├─ fuzzy_score: float
│  └─ Output from fuzzy engine (0-1)
│
├─ ann_score: float
│  └─ Output from neural network (0-1)
│
├─ hybrid_score: float
│  └─ Final recommendation score (0-1)
│
├─ confidence: float
│  └─ Confidence in recommendation (0-1)
│
├─ strategy: str
│  └─ "adaptive" | "fuzzy_dominant" | "ann_dominant" | ...
│
└─ ann_available: bool
   └─ true if ANN model was used


MetricsCollector (Thread-Safe)
├─ metrics: deque[RequestMetrics]
│  └─ Circular buffer with maxlen=1000
│
├─ lock: threading.Lock
│  └─ Protects all operations
│
├─ Methods:
│  ├─ record_request(metric: RequestMetrics)
│  │  └─ Add new metric to deque
│  │
│  ├─ get_performance_summary() → Dict
│  │  └─ Calculate all aggregates
│  │
│  ├─ get_recent_metrics(n: int) → List
│  │  └─ Get last N requests
│  │
│  └─ get_strategy_distribution() → Dict
│     └─ Count strategies used
│
└─ Properties:
   ├─ request_count: int
   ├─ uptime_seconds: float
   └─ performance stats calculated on demand


Performance Summary (Dict)
├─ request_count: int
│
├─ uptime_seconds: float
│
├─ performance: Dict
│  ├─ avg_latency_ms: float
│  ├─ min_latency_ms: float
│  ├─ max_latency_ms: float
│  ├─ p95_latency_ms: float
│  └─ p99_latency_ms: float
│
├─ scores: Dict
│  ├─ avg_fuzzy_score: float
│  ├─ avg_ann_score: float
│  ├─ avg_hybrid_score: float
│  └─ avg_confidence: float
│
└─ throughput: Dict
   └─ requests_per_second: float
```

---

## Request/Response Timeline

```
Time │ Action                           │ Component
─────┼──────────────────────────────────┼─────────────────
  0  │ Client sends POST /recommend     │ Network
     │ {user_id: 1, movie_id: 100}     │
     │                                  │
  1  │ API receives request             │ FastAPI
     │                                  │
  2  │ START timing (request_start)     │ api.py
     │ T0 = time.time()                │
     │                                  │
  3  │ Validate input                   │ api.py
     │                                  │
  4  │ Call fuzzy recommender           │ Fuzzy Engine
     │ Process: 45.12ms                │
     │ Output: score=0.85              │
     │                                  │
  49 │ Call ANN model                   │ Neural Network
     │ Process: 72.89ms                │
     │ Output: score=0.82              │
     │                                  │
 122 │ Combine scores                   │ Hybrid System
     │ Process: 7.33ms                 │
     │ Output: score=0.835, conf=0.91  │
     │                                  │
 130 │ STOP timing                      │ api.py
     │ T1 = time.time()                │
     │ Total = (T1 - T0) * 1000        │
     │ Total = 125.34ms                │
     │                                  │
 131 │ Create RequestMetrics            │ models/metrics.py
     │ All fields populated            │
     │                                  │
 132 │ Record in MetricsCollector       │ MetricsCollector
     │ Add to deque                    │
     │ Calculate aggregates            │
     │                                  │
 133 │ Get system metrics               │ models/metrics.py
     │ Calculate summary stats         │
     │                                  │
 134 │ Log formatted display            │ Console Log
     │ Pretty-printed metrics          │
     │                                  │
 135 │ Build response                   │ api.py
     │ Include metrics field           │
     │ Include system_metrics field    │
     │                                  │
 136 │ Return 200 OK                    │ HTTP
     │ JSON response with metrics      │
     │                                  │
 137 │ Client receives response         │ Client
     │ All metrics data available      │
```

---

## Metrics Collection Flow

```
INPUT: Every POST /recommend request

    ↓

TIMING TRACKING:
├─ request_start = time.time()
├─ Call engine (contains fuzzy_time, ann_time)
├─ request_end = time.time()
└─ total_time = (request_end - request_start) * 1000

    ↓

METRICS CREATION:
├─ RequestMetrics(
│  ├─ timestamp=time.time()
│  ├─ total_time_ms=125.34
│  ├─ fuzzy_time_ms=45.12
│  ├─ ann_time_ms=72.89
│  ├─ combination_time_ms=7.33
│  ├─ fuzzy_score=0.85
│  ├─ ann_score=0.82
│  ├─ hybrid_score=0.835
│  ├─ confidence=0.91
│  ├─ strategy="adaptive"
│  └─ ann_available=true
│ )

    ↓

THREAD-SAFE RECORDING:
├─ collector.lock.acquire()
├─ collector.metrics.append(metric)
├─ Update aggregation state
└─ collector.lock.release()

    ↓

AGGREGATION (on demand):
├─ Loop through all metrics
├─ Calculate statistics:
│  ├─ Sum for averaging
│  ├─ Min/Max tracking
│  ├─ Sort for percentiles
│  └─ Count strategies
└─ Return performance_summary

    ↓

OUTPUT:
├─ Include in response (metrics field)
├─ Include system metrics (system_metrics field)
├─ Log formatted display
└─ Available via /performance-metrics endpoint
```

---

## Memory Layout

```
MetricsCollector Object (RAM)
├─ metrics: deque[RequestMetrics]
│  │
│  ├─ Slot 1: RequestMetrics
│  │  └─ Size: ~100-150 bytes
│  │
│  ├─ Slot 2: RequestMetrics
│  │  └─ Size: ~100-150 bytes
│  │
│  ├─ Slot 3: RequestMetrics
│  │  └─ Size: ~100-150 bytes
│  │
│  ...
│
│  ├─ Slot 999: RequestMetrics
│  │  └─ Size: ~100-150 bytes
│  │
│  └─ Slot 1000: RequestMetrics
│     └─ Size: ~100-150 bytes
│     (maxlen=1000, oldest drops when full)
│
├─ lock: threading.Lock
│  └─ Size: ~200 bytes
│
└─ TOTAL MEMORY: ~500 KB (1000 requests)
   Per-request overhead: ~500 bytes
   Circular buffer prevents unlimited growth
```

---

## Thread Safety Diagram

```
Thread 1                     Thread 2
Request A                    Request B
    │                            │
    │                            │
    ▼                            ▼
try:                         try:
  lock.acquire()      ├──>    wait...
    │                 │         │
    │<────────────────┤         │
    │                 │         │
  append(metric_a)    │         ▼
    │                 │    (lock acquired)
    │                 │     append(metric_b)
  calculate()         │         │
    │                 │    calculate()
  lock.release()      │         │
finally:              │    lock.release()
  ✅ Safe             │    finally:
                      └──>    ✅ Safe

No race conditions!
Operations are atomic.
Metrics always consistent.
```

---

## Console Output Format

```
════════════════════════════════════════════════════════════════════
📊 SYSTEM PERFORMANCE METRICS
════════════════════════════════════════════════════════════════════
📈 Total Requests: 42
⏱️  Uptime: 156s
🚀 Throughput: 0.27 req/sec

────────────────────────────────────────────────────────────────────
⚡ LATENCY METRICS (milliseconds)
  Total: 118.45ms avg (95.23-145.67ms) p95: 135.89ms p99: 142.34ms
  Fuzzy: 45.12ms avg
  ANN: 72.89ms avg (42 calls)

────────────────────────────────────────────────────────────────────
🎯 SCORE STATISTICS
  Fuzzy: 0.82 avg (0.70-0.95)
  Hybrid: 0.81 avg (0.72-0.96)
  Confidence: 0.89 avg

════════════════════════════════════════════════════════════════════

Components:
├─ Separators: 4 horizontal lines (for visual clarity)
├─ Sections: 3 main sections (Counts, Latency, Scores)
├─ Emojis: 7 different emojis (for visual interest)
├─ Values: All metrics displayed with appropriate units
└─ Ranges: Min/max shown where applicable
```

---

## Integration Points

```
api.py
├─ Line ~529: startup_event()
│  └─ Call: initialize_metrics()
│
├─ Line ~461: RecommendationResponse
│  └─ Add: metrics: Optional[Dict] = None
│  └─ Add: system_metrics: Optional[Dict] = None
│
├─ Line ~743: @app.post("/recommend")
│  ├─ Add: timing tracking
│  ├─ Add: metrics recording
│  ├─ Add: system metrics aggregation
│  ├─ Add: formatted logging
│  └─ Return: response with metrics fields
│
└─ Line ~615: @app.get("/performance-metrics")
   └─ New endpoint returning accumulated metrics


models/metrics.py
├─ RequestMetrics (dataclass)
├─ MetricsCollector (class with thread-safety)
├─ Module functions:
│  ├─ initialize_metrics()
│  ├─ get_metrics_collector()
│  ├─ record_recommendation_metrics(...)
│  ├─ get_system_metrics()
│  └─ format_metrics_display()
└─ Global state: _metrics_collector
```

---

## Percentile Calculation

```
Request Latencies (sorted):
│
├─ 95.23 ms  ◄─── min_latency
├─ 100.45 ms
├─ 102.30 ms
├─ 105.67 ms
├─ 108.92 ms
├─ 110.34 ms
├─ 115.67 ms
├─ 118.45 ms  ◄─── avg_latency (sum / count)
├─ 120.23 ms
├─ 122.56 ms
├─ 125.34 ms
├─ 128.90 ms
├─ 130.45 ms
├─ 132.78 ms
├─ 135.89 ms  ◄─── p95_latency (95th percentile)
├─ 138.23 ms
├─ 140.56 ms
├─ 142.34 ms  ◄─── p99_latency (99th percentile)
├─ 143.90 ms
└─ 145.67 ms  ◄─── max_latency

P95 = 95th percentile means 95% of requests are faster
P99 = 99th percentile means 99% of requests are faster
```

---

This completes the visual architecture documentation!
