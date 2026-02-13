"""
Performance monitoring utilities.
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ExecutionStats:
    """Statistics for function execution."""
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, execution_time: float):
        """Update statistics with new execution time."""
        self.total_calls += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.total_calls
        self.recent_times.append(execution_time)
    
    def get_recent_avg(self, window: int = 10) -> float:
        """Get average execution time for recent calls."""
        recent = list(self.recent_times)[-window:]
        return sum(recent) / len(recent) if recent else 0.0


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.execution_stats: Dict[str, ExecutionStats] = defaultdict(ExecutionStats)
        self.memory_samples: deque = deque(maxlen=1000)
        self.cpu_samples: deque = deque(maxlen=1000)
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self, interval: float = 1.0):
        """Start background monitoring of system resources."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_system,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_system(self, interval: float):
        """Background system monitoring loop."""
        while self._monitoring:
            try:
                # Collect memory usage
                memory_info = psutil.virtual_memory()
                self.memory_samples.append({
                    'timestamp': time.time(),
                    'percent': memory_info.percent,
                    'available': memory_info.available,
                    'used': memory_info.used
                })
                
                # Collect CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.cpu_samples.append({
                    'timestamp': time.time(),
                    'percent': cpu_percent
                })
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(interval)
    
    def record_metric(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.metrics[name].append(metric)
        
        # Limit metric history
        if len(self.metrics[name]) > 10000:
            self.metrics[name] = self.metrics[name][-5000:]
    
    def record_execution(self, function_name: str, execution_time: float):
        """Record function execution time."""
        self.execution_stats[function_name].update(execution_time)
        self.record_metric(f"execution_time_{function_name}", execution_time)
    
    def get_stats(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        if metric_name:
            metrics = self.metrics.get(metric_name, [])
            if not metrics:
                return {}
            
            values = [m.value for m in metrics]
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'recent_avg': sum(values[-100:]) / min(len(values), 100)
            }
        
        # Return all stats
        stats = {}
        for name, metrics in self.metrics.items():
            values = [m.value for m in metrics]
            if values:
                stats[name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'recent_avg': sum(values[-100:]) / min(len(values), 100)
                }
        
        return stats
    
    def get_execution_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get function execution statistics."""
        return {
            name: {
                'total_calls': stats.total_calls,
                'total_time': stats.total_time,
                'min_time': stats.min_time,
                'max_time': stats.max_time,
                'avg_time': stats.avg_time,
                'recent_avg': stats.get_recent_avg()
            }
            for name, stats in self.execution_stats.items()
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        stats = {}
        
        # Memory stats
        if self.memory_samples:
            recent_memory = list(self.memory_samples)[-10:]
            stats['memory'] = {
                'current_percent': recent_memory[-1]['percent'],
                'avg_percent': sum(m['percent'] for m in recent_memory) / len(recent_memory),
                'available_mb': recent_memory[-1]['available'] / (1024 * 1024)
            }
        
        # CPU stats
        if self.cpu_samples:
            recent_cpu = list(self.cpu_samples)[-10:]
            stats['cpu'] = {
                'current_percent': recent_cpu[-1]['percent'],
                'avg_percent': sum(c['percent'] for c in recent_cpu) / len(recent_cpu)
            }
        
        return stats


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def track_execution_time(function_name: Optional[str] = None):
    """Decorator to track function execution time."""
    def decorator(func: Callable) -> Callable:
        import functools
        name = function_name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                _performance_monitor.record_execution(name, execution_time)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                _performance_monitor.record_execution(f"{name}_error", execution_time)
                raise
        
        return wrapper
    return decorator


def memory_usage_monitor(func: Callable) -> Callable:
    """Decorator to monitor memory usage during function execution."""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        try:
            result = func(*args, **kwargs)
            
            # Get final memory usage
            final_memory = process.memory_info().rss
            memory_delta = final_memory - initial_memory
            
            _performance_monitor.record_metric(
                f"memory_usage_{func.__name__}",
                memory_delta,
                {'initial_mb': initial_memory / (1024 * 1024),
                 'final_mb': final_memory / (1024 * 1024)}
            )
            
            return result
            
        except Exception as e:
            final_memory = process.memory_info().rss
            memory_delta = final_memory - initial_memory
            _performance_monitor.record_metric(
                f"memory_usage_{func.__name__}_error",
                memory_delta
            )
            raise
    
    return wrapper


def performance_report() -> str:
    """Generate a performance report."""
    stats = _performance_monitor.get_stats()
    exec_stats = _performance_monitor.get_execution_stats()
    system_stats = _performance_monitor.get_system_stats()
    
    report = []
    report.append("=== Performance Report ===")
    report.append(f"Generated at: {datetime.now().isoformat()}")
    report.append("")
    
    # System stats
    if system_stats:
        report.append("System Statistics:")
        if 'memory' in system_stats:
            mem = system_stats['memory']
            report.append(f"  Memory: {mem['current_percent']:.1f}% used, {mem['available_mb']:.0f} MB available")
        if 'cpu' in system_stats:
            cpu = system_stats['cpu']
            report.append(f"  CPU: {cpu['current_percent']:.1f}% current, {cpu['avg_percent']:.1f}% average")
        report.append("")
    
    # Execution stats
    if exec_stats:
        report.append("Function Execution Statistics:")
        for func_name, stats in sorted(exec_stats.items()):
            report.append(f"  {func_name}:")
            report.append(f"    Calls: {stats['total_calls']}")
            report.append(f"    Total time: {stats['total_time']:.3f}s")
            report.append(f"    Avg time: {stats['avg_time']:.3f}s")
            report.append(f"    Recent avg: {stats['recent_avg']:.3f}s")
        report.append("")
    
    # Custom metrics
    if stats:
        report.append("Custom Metrics:")
        for metric_name, metric_stats in sorted(stats.items()):
            if not metric_name.startswith('execution_time_'):
                report.append(f"  {metric_name}:")
                report.append(f"    Count: {metric_stats['count']}")
                report.append(f"    Avg: {metric_stats['avg']:.3f}")
                report.append(f"    Min/Max: {metric_stats['min']:.3f}/{metric_stats['max']:.3f}")
    
    return "\n".join(report)