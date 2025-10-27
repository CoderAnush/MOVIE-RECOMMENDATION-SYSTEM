"""
Performance Metrics Tracking System
====================================

This module provides real-time metrics tracking for the recommendation system,
including latency, accuracy, and component performance statistics.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
from threading import Lock
import json

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single recommendation request."""
    timestamp: float
    total_time_ms: float
    fuzzy_time_ms: float
    ann_time_ms: float
    combination_time_ms: float
    fuzzy_score: float
    ann_score: float
    hybrid_score: float
    confidence: float
    strategy: str
    ann_available: bool


class MetricsCollector:
    """Collects and aggregates system performance metrics."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.lock = Lock()
        self._fuzzy_times: deque = deque(maxlen=max_history)
        self._ann_times: deque = deque(maxlen=max_history)
        self._hybrid_times: deque = deque(maxlen=max_history)
        self._start_time = time.time()
    
    def record_request(self, metrics: RequestMetrics) -> None:
        """Record a single request's metrics."""
        with self.lock:
            self.metrics.append(metrics)
            self._fuzzy_times.append(metrics.fuzzy_time_ms)
            if metrics.ann_available:
                self._ann_times.append(metrics.ann_time_ms)
            self._hybrid_times.append(metrics.total_time_ms)
    
    def get_performance_summary(self) -> Dict:
        """Get current performance metrics summary."""
        with self.lock:
            if not self.metrics:
                return self._get_empty_summary()
            
            # Extract timing data
            total_times = [m.total_time_ms for m in self.metrics]
            fuzzy_times = [m.fuzzy_time_ms for m in self.metrics]
            ann_times = [m.ann_time_ms for m in self.metrics if m.ann_available]
            
            # Extract scores
            fuzzy_scores = [m.fuzzy_score for m in self.metrics]
            hybrid_scores = [m.hybrid_score for m in self.metrics]
            confidences = [m.confidence for m in self.metrics]
            
            return {
                "request_count": len(self.metrics),
                "uptime_seconds": time.time() - self._start_time,
                "performance": {
                    "total_latency_ms": {
                        "avg": sum(total_times) / len(total_times),
                        "min": min(total_times),
                        "max": max(total_times),
                        "p95": self._percentile(total_times, 95),
                        "p99": self._percentile(total_times, 99)
                    },
                    "fuzzy_latency_ms": {
                        "avg": sum(fuzzy_times) / len(fuzzy_times) if fuzzy_times else 0,
                        "min": min(fuzzy_times) if fuzzy_times else 0,
                        "max": max(fuzzy_times) if fuzzy_times else 0
                    },
                    "ann_latency_ms": {
                        "avg": sum(ann_times) / len(ann_times) if ann_times else 0,
                        "min": min(ann_times) if ann_times else 0,
                        "max": max(ann_times) if ann_times else 0,
                        "calls": len(ann_times)
                    }
                },
                "scores": {
                    "fuzzy": {
                        "avg": sum(fuzzy_scores) / len(fuzzy_scores),
                        "min": min(fuzzy_scores),
                        "max": max(fuzzy_scores)
                    },
                    "hybrid": {
                        "avg": sum(hybrid_scores) / len(hybrid_scores),
                        "min": min(hybrid_scores),
                        "max": max(hybrid_scores)
                    },
                    "confidence": {
                        "avg": sum(confidences) / len(confidences),
                        "min": min(confidences),
                        "max": max(confidences)
                    }
                },
                "throughput": {
                    "requests_per_second": len(self.metrics) / max(1, time.time() - self._start_time)
                }
            }
    
    def get_recent_metrics(self, count: int = 10) -> List[Dict]:
        """Get the most recent N metrics."""
        with self.lock:
            recent = list(self.metrics)[-count:]
            return [asdict(m) for m in recent]
    
    def get_strategy_stats(self) -> Dict[str, int]:
        """Get statistics about combination strategies used."""
        with self.lock:
            strategies = {}
            for m in self.metrics:
                strategies[m.strategy] = strategies.get(m.strategy, 0) + 1
            return strategies
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        with self.lock:
            self.metrics.clear()
            self._fuzzy_times.clear()
            self._ann_times.clear()
            self._hybrid_times.clear()
            self._start_time = time.time()
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile from list of values."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    @staticmethod
    def _get_empty_summary() -> Dict:
        """Get empty summary template."""
        return {
            "request_count": 0,
            "uptime_seconds": 0,
            "performance": {
                "total_latency_ms": {"avg": 0, "min": 0, "max": 0, "p95": 0, "p99": 0},
                "fuzzy_latency_ms": {"avg": 0, "min": 0, "max": 0},
                "ann_latency_ms": {"avg": 0, "min": 0, "max": 0, "calls": 0}
            },
            "scores": {
                "fuzzy": {"avg": 0, "min": 0, "max": 0},
                "hybrid": {"avg": 0, "min": 0, "max": 0},
                "confidence": {"avg": 0, "min": 0, "max": 0}
            },
            "throughput": {"requests_per_second": 0}
        }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def initialize_metrics() -> MetricsCollector:
    """Initialize the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        logger.info("✅ Metrics collector initialized")
    return _metrics_collector


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_recommendation_metrics(
    total_time: float,
    fuzzy_time: float,
    ann_time: float,
    fuzzy_score: float,
    ann_score: float,
    hybrid_score: float,
    confidence: float,
    strategy: str,
    ann_available: bool
) -> None:
    """Record metrics for a single recommendation request."""
    collector = get_metrics_collector()
    metrics = RequestMetrics(
        timestamp=time.time(),
        total_time_ms=total_time,
        fuzzy_time_ms=fuzzy_time,
        ann_time_ms=ann_time,
        combination_time_ms=total_time - fuzzy_time - ann_time,
        fuzzy_score=fuzzy_score,
        ann_score=ann_score,
        hybrid_score=hybrid_score,
        confidence=confidence,
        strategy=strategy,
        ann_available=ann_available
    )
    collector.record_request(metrics)


def get_system_metrics() -> Dict:
    """Get all current system metrics."""
    collector = get_metrics_collector()
    return collector.get_performance_summary()


def format_metrics_display() -> str:
    """Format metrics as a nice display string."""
    metrics = get_system_metrics()
    
    display = "\n" + "="*70 + "\n"
    display += "📊 SYSTEM PERFORMANCE METRICS\n"
    display += "="*70 + "\n"
    
    display += f"📈 Total Requests: {metrics['request_count']}\n"
    display += f"⏱️  Uptime: {int(metrics['uptime_seconds'])}s\n"
    display += f"🚀 Throughput: {metrics['throughput']['requests_per_second']:.2f} req/sec\n"
    display += "\n" + "-"*70 + "\n"
    
    perf = metrics['performance']
    display += "⚡ LATENCY METRICS (milliseconds)\n"
    display += f"  Total: {perf['total_latency_ms']['avg']:.2f}ms avg "
    display += f"({perf['total_latency_ms']['min']:.2f}-{perf['total_latency_ms']['max']:.2f}ms) "
    display += f"p95: {perf['total_latency_ms']['p95']:.2f}ms p99: {perf['total_latency_ms']['p99']:.2f}ms\n"
    
    display += f"  Fuzzy: {perf['fuzzy_latency_ms']['avg']:.2f}ms avg\n"
    
    if perf['ann_latency_ms']['calls'] > 0:
        display += f"  ANN: {perf['ann_latency_ms']['avg']:.2f}ms avg ({perf['ann_latency_ms']['calls']} calls)\n"
    
    display += "\n" + "-"*70 + "\n"
    
    scores = metrics['scores']
    display += "🎯 SCORE STATISTICS\n"
    display += f"  Fuzzy: {scores['fuzzy']['avg']:.2f} avg "
    display += f"({scores['fuzzy']['min']:.2f}-{scores['fuzzy']['max']:.2f})\n"
    display += f"  Hybrid: {scores['hybrid']['avg']:.2f} avg "
    display += f"({scores['hybrid']['min']:.2f}-{scores['hybrid']['max']:.2f})\n"
    display += f"  Confidence: {scores['confidence']['avg']:.2f} avg\n"
    
    display += "\n" + "="*70 + "\n"
    
    return display
