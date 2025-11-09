"""Performance metrics tracking for SWARM-LITE-."""

import asyncio
import psutil
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, DefaultDict, Deque, Dict, List, Optional
from uuid import UUID

from ..core.types import ResourceMetrics
from .config import get_config
from .logging import get_logger

logger = get_logger("metrics")


@dataclass
class MetricDataPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels,
        }


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    count: int = 0
    sum: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    mean: float = 0.0
    last_value: float = 0.0
    last_timestamp: Optional[datetime] = None

    def update(self, value: float, timestamp: datetime) -> None:
        """Update summary with new value."""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.mean = self.sum / self.count
        self.last_value = value
        self.last_timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "sum": self.sum,
            "min": self.min if self.min != float("inf") else 0.0,
            "max": self.max if self.max != float("-inf") else 0.0,
            "mean": self.mean,
            "last_value": self.last_value,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
        }


class MetricsCollector:
    """Collects and tracks system metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.config = get_config()
        self._metrics: DefaultDict[str, Deque[MetricDataPoint]] = defaultdict(lambda: deque(maxlen=1000))
        self._summaries: DefaultDict[str, MetricSummary] = defaultdict(MetricSummary)
        self._counters: DefaultDict[str, int] = defaultdict(int)
        self._gauges: DefaultDict[str, float] = defaultdict(float)
        self._task = None
        self._running = False

    async def start(self) -> None:
        """Start metrics collection."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collection started")

    async def stop(self) -> None:
        """Stop metrics collection."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collection stopped")

    async def _collection_loop(self) -> None:
        """Background loop for collecting metrics."""
        while self._running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.config.metrics_collection_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}", exc_info=True)

    async def _collect_system_metrics(self) -> None:
        """Collect system-level metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.record_gauge("system.cpu.percent", cpu_percent)

            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_gauge("system.memory.percent", memory.percent)
            self.record_gauge("system.memory.used_mb", memory.used / (1024 * 1024))
            self.record_gauge("system.memory.available_mb", memory.available / (1024 * 1024))

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            self.record_gauge("process.memory.rss_mb", process_memory.rss / (1024 * 1024))
            self.record_gauge("process.memory.vms_mb", process_memory.vms / (1024 * 1024))
            self.record_gauge("process.cpu.percent", process.cpu_percent())

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def record_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a counter metric.

        Args:
            name: Metric name
            value: Counter increment value
            labels: Optional labels for the metric
        """
        key = self._make_key(name, labels)
        self._counters[key] += value

        # Also record as time series
        self._record_metric(name, float(value), labels)

    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels for the metric
        """
        key = self._make_key(name, labels)
        self._gauges[key] = value

        # Also record as time series
        self._record_metric(name, value, labels)

    def record_timing(self, name: str, duration_seconds: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric.

        Args:
            name: Metric name
            duration_seconds: Duration in seconds
            labels: Optional labels for the metric
        """
        self._record_metric(name, duration_seconds, labels)

    def _record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric data point."""
        timestamp = datetime.utcnow()
        data_point = MetricDataPoint(timestamp=timestamp, value=value, labels=labels or {})

        # Add to time series
        self._metrics[name].append(data_point)

        # Update summary
        self._summaries[name].update(value, timestamp)

        # Clean old data
        self._cleanup_old_metrics()

    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.config.metrics_retention_hours)

        for name, points in self._metrics.items():
            while points and points[0].timestamp < cutoff:
                points.popleft()

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Make a unique key for a metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_summary(self, name: str) -> Optional[MetricSummary]:
        """Get metric summary."""
        return self._summaries.get(name)

    def get_time_series(self, name: str, since: Optional[datetime] = None) -> List[MetricDataPoint]:
        """Get time series data for a metric.

        Args:
            name: Metric name
            since: Optional start time

        Returns:
            List of data points
        """
        points = self._metrics.get(name, deque())
        if since:
            return [p for p in points if p.timestamp >= since]
        return list(points)

    def get_resource_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        return ResourceMetrics(
            cpu_percent=self.get_gauge("system.cpu.percent"),
            memory_mb=self.get_gauge("system.memory.used_mb"),
            memory_percent=self.get_gauge("system.memory.percent"),
            active_tasks=int(self.get_gauge("swarm.tasks.active")),
            completed_tasks=self.get_counter("swarm.tasks.completed"),
            failed_tasks=self.get_counter("swarm.tasks.failed"),
            message_queue_size=int(self.get_gauge("swarm.messages.queue_size")),
        )

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "summaries": {name: summary.to_dict() for name, summary in self._summaries.items()},
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()
        self._summaries.clear()
        self._counters.clear()
        self._gauges.clear()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector() -> None:
    """Reset global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector:
        _metrics_collector.reset()
    _metrics_collector = None
