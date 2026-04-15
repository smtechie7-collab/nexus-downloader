from typing import Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json
from monitoring.logger import get_logger

logger = get_logger("Metrics")

class MetricsCollector:
    """
    Collects and aggregates performance metrics across the system.
    Tracks: success/failure rates, throughput, latency, resource usage.
    """
    
    def __init__(self, window_size_seconds: int = 3600):
        """
        Initialize metrics collector.
        
        Args:
            window_size_seconds: Time window for metric aggregation (default: 1 hour)
        """
        self.window_size = timedelta(seconds=window_size_seconds)
        
        # Global counters
        self.total_requests = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_bytes_downloaded = 0
        
        # Per-domain metrics
        self.domain_metrics: Dict[str, Dict] = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_latency': 0,
            'min_latency': float('inf'),
            'max_latency': 0,
        })
        
        # Per-engine metrics
        self.engine_metrics: Dict[str, Dict] = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'avg_extraction_time': 0,
        })
        
        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # Timeline events for detailed analysis
        self.events = []
        self.start_time = datetime.now()
    
    def record_request(self, domain: str, engine: str, success: bool, 
                      latency_ms: float, bytes_downloaded: int = 0, 
                      error_type: str = None):
        """Records a request metric."""
        timestamp = datetime.now()
        
        # Update global metrics
        self.total_requests += 1
        self.total_bytes_downloaded += bytes_downloaded
        
        if success:
            self.total_successes += 1
        else:
            self.total_failures += 1
            if error_type:
                self.error_counts[error_type] += 1
        
        # Update domain metrics
        domain_metric = self.domain_metrics[domain]
        domain_metric['requests'] += 1
        if success:
            domain_metric['successes'] += 1
        else:
            domain_metric['failures'] += 1
        domain_metric['total_latency'] += latency_ms
        domain_metric['min_latency'] = min(domain_metric['min_latency'], latency_ms)
        domain_metric['max_latency'] = max(domain_metric['max_latency'], latency_ms)
        
        # Update engine metrics
        engine_metric = self.engine_metrics[engine]
        engine_metric['requests'] += 1
        if success:
            engine_metric['successes'] += 1
        else:
            engine_metric['failures'] += 1
        engine_metric['avg_extraction_time'] = (
            (engine_metric['avg_extraction_time'] * (engine_metric['requests'] - 1) + latency_ms) / 
            engine_metric['requests']
        )
        
        # Record event
        self.events.append({
            'timestamp': timestamp,
            'domain': domain,
            'engine': engine,
            'success': success,
            'latency_ms': latency_ms,
            'bytes': bytes_downloaded,
            'error_type': error_type
        })
        
        logger.debug("Metric recorded", extra={
            "context": {
                "domain": domain,
                "engine": engine,
                "latency_ms": round(latency_ms, 2),
                "success": success
            }
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Returns a comprehensive metrics summary."""
        uptime = datetime.now() - self.start_time
        hours_running = uptime.total_seconds() / 3600
        
        success_rate = (
            (self.total_successes / self.total_requests * 100) 
            if self.total_requests > 0 else 0
        )
        
        avg_throughput = (
            self.total_bytes_downloaded / hours_running / (1024 * 1024)  # MB/hour
            if hours_running > 0 else 0
        )
        
        summary = {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": self.total_requests,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate_percent": round(success_rate, 2),
            "total_bytes_downloaded": self.total_bytes_downloaded,
            "avg_throughput_mbh": round(avg_throughput, 2),
            "total_errors": dict(self.error_counts),
        }
        
        return summary
    
    def get_domain_stats(self, domain: str = None) -> Dict:
        """Gets statistics for specific domain or all domains."""
        if domain:
            if domain not in self.domain_metrics:
                return {}
            
            metrics = self.domain_metrics[domain]
            success_rate = (
                (metrics['successes'] / metrics['requests'] * 100)
                if metrics['requests'] > 0 else 0
            )
            
            return {
                "domain": domain,
                "requests": metrics['requests'],
                "successes": metrics['successes'],
                "failures": metrics['failures'],
                "success_rate_percent": round(success_rate, 2),
                "avg_latency_ms": round(
                    metrics['total_latency'] / metrics['requests'],
                    2
                ) if metrics['requests'] > 0 else 0,
                "min_latency_ms": round(metrics['min_latency'], 2),
                "max_latency_ms": round(metrics['max_latency'], 2),
            }
        else:
            return {
                domain: self.get_domain_stats(domain)
                for domain in self.domain_metrics.keys()
            }
    
    def get_engine_stats(self, engine: str = None) -> Dict:
        """Gets statistics for specific engine or all engines."""
        if engine:
            if engine not in self.engine_metrics:
                return {}
            
            metrics = self.engine_metrics[engine]
            success_rate = (
                (metrics['successes'] / metrics['requests'] * 100)
                if metrics['requests'] > 0 else 0
            )
            
            return {
                "engine": engine,
                "requests": metrics['requests'],
                "successes": metrics['successes'],
                "failures": metrics['failures'],
                "success_rate_percent": round(success_rate, 2),
                "avg_extraction_time_ms": round(metrics['avg_extraction_time'], 2),
            }
        else:
            return {
                engine: self.get_engine_stats(engine)
                for engine in self.engine_metrics.keys()
            }
    
    def get_recent_events(self, limit: int = 100, 
                         failures_only: bool = False) -> list:
        """Gets recent events for debugging."""
        events = self.events[-limit:] if limit > 0 else self.events
        
        if failures_only:
            events = [e for e in events if not e['success']]
        
        # Convert datetime to ISO format for JSON serialization
        return [
            {
                **e,
                'timestamp': e['timestamp'].isoformat()
            }
            for e in events
        ]
    
    def export_metrics(self) -> str:
        """Exports all metrics as JSON string."""
        data = {
            "summary": self.get_summary(),
            "domains": self.get_domain_stats(),
            "engines": self.get_engine_stats(),
            "recent_errors": self.get_recent_events(failures_only=True),
        }
        
        return json.dumps(data, indent=2)
    
    def reset(self):
        """Resets all metrics."""
        self.total_requests = 0
        self.total_successes = 0
        self.total_failures = 0
        self.total_bytes_downloaded = 0
        self.domain_metrics.clear()
        self.engine_metrics.clear()
        self.error_counts.clear()
        self.events.clear()
        self.start_time = datetime.now()
        
        logger.info("Metrics reset")


# Global metrics instance
_metrics_instance = None

def get_metrics() -> MetricsCollector:
    """Gets the global metrics collector instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
