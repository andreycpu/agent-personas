"""
Health monitoring system for persona framework components.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
import threading
import psutil
import gc
from datetime import datetime, timedelta
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of components to monitor."""
    CORE = "core"
    DATABASE = "database"
    CACHE = "cache"
    PLUGIN = "plugin"
    STORAGE = "storage"
    EXTERNAL = "external"


@dataclass
class HealthCheck:
    """Represents a health check."""
    name: str
    component_type: ComponentType
    check_function: Callable[[], Dict[str, Any]]
    interval_seconds: float = 60.0
    timeout_seconds: float = 10.0
    enabled: bool = True
    critical: bool = False
    last_check: Optional[datetime] = None
    last_status: HealthStatus = HealthStatus.UNKNOWN
    failure_count: int = 0
    max_failures: int = 3


@dataclass
class HealthResult:
    """Result of a health check."""
    check_name: str
    status: HealthStatus
    timestamp: datetime
    response_time_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class HealthMonitor:
    """
    Comprehensive health monitoring system.
    
    Monitors system health, component status, and performance metrics
    with configurable checks and alerting.
    """
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_results: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.system_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize built-in health checks
        self._register_builtin_checks()
        
        # Health thresholds
        self.thresholds = {
            "memory_usage_percent": 85.0,
            "cpu_usage_percent": 90.0,
            "disk_usage_percent": 90.0,
            "response_time_ms": 5000.0,
            "error_rate_percent": 5.0
        }
    
    def _register_builtin_checks(self):
        """Register built-in system health checks."""
        # Memory check
        self.register_health_check(HealthCheck(
            name="system_memory",
            component_type=ComponentType.CORE,
            check_function=self._check_memory_usage,
            interval_seconds=30.0,
            critical=True
        ))
        
        # CPU check
        self.register_health_check(HealthCheck(
            name="system_cpu",
            component_type=ComponentType.CORE,
            check_function=self._check_cpu_usage,
            interval_seconds=30.0,
            critical=True
        ))
        
        # Disk check
        self.register_health_check(HealthCheck(
            name="system_disk",
            component_type=ComponentType.CORE,
            check_function=self._check_disk_usage,
            interval_seconds=60.0,
            critical=True
        ))
        
        # Python GC check
        self.register_health_check(HealthCheck(
            name="garbage_collection",
            component_type=ComponentType.CORE,
            check_function=self._check_garbage_collection,
            interval_seconds=120.0,
            critical=False
        ))
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check."""
        with self._lock:
            self.health_checks[health_check.name] = health_check
        
        self.logger.info(f"Registered health check: {health_check.name}")
    
    def unregister_health_check(self, check_name: str) -> bool:
        """Unregister a health check."""
        with self._lock:
            if check_name in self.health_checks:
                del self.health_checks[check_name]
                self.logger.info(f"Unregistered health check: {check_name}")
                return True
        return False
    
    def run_health_check(self, check_name: str) -> Optional[HealthResult]:
        """Run a specific health check manually."""
        with self._lock:
            if check_name not in self.health_checks:
                self.logger.error(f"Health check not found: {check_name}")
                return None
            
            health_check = self.health_checks[check_name]
        
        return self._execute_health_check(health_check)
    
    def _execute_health_check(self, health_check: HealthCheck) -> HealthResult:
        """Execute a health check and return the result."""
        start_time = time.time()
        timestamp = datetime.now()
        
        try:
            # Run the health check function
            check_result = health_check.check_function()
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine status
            status = HealthStatus(check_result.get("status", "unknown"))
            message = check_result.get("message", "")
            details = check_result.get("details", {})
            
            # Create result
            result = HealthResult(
                check_name=health_check.name,
                status=status,
                timestamp=timestamp,
                response_time_ms=response_time_ms,
                message=message,
                details=details
            )
            
            # Update health check tracking
            health_check.last_check = timestamp
            health_check.last_status = status
            
            if status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                health_check.failure_count += 1
            else:
                health_check.failure_count = 0
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            result = HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                timestamp=timestamp,
                response_time_ms=response_time_ms,
                message="Health check failed",
                error=str(e)
            )
            
            health_check.last_check = timestamp
            health_check.last_status = HealthStatus.CRITICAL
            health_check.failure_count += 1
            
            self.logger.error(f"Health check {health_check.name} failed: {e}")
        
        # Store result
        self.health_results[health_check.name].append(result)
        
        return result
    
    def run_all_health_checks(self) -> Dict[str, HealthResult]:
        """Run all enabled health checks."""
        results = {}
        
        with self._lock:
            checks_to_run = list(self.health_checks.values())
        
        for health_check in checks_to_run:
            if health_check.enabled:
                result = self._execute_health_check(health_check)
                results[health_check.name] = result
        
        return results
    
    def get_overall_health_status(self) -> HealthStatus:
        """Get overall system health status."""
        critical_checks = []
        warning_checks = []
        
        with self._lock:
            for health_check in self.health_checks.values():
                if health_check.enabled and health_check.last_status:
                    if health_check.last_status == HealthStatus.CRITICAL:
                        critical_checks.append(health_check.name)
                    elif health_check.last_status == HealthStatus.WARNING:
                        warning_checks.append(health_check.name)
        
        if critical_checks:
            return HealthStatus.CRITICAL
        elif warning_checks:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health."""
        overall_status = self.get_overall_health_status()
        
        status_counts = defaultdict(int)
        component_status = defaultdict(list)
        
        with self._lock:
            for health_check in self.health_checks.values():
                if health_check.enabled:
                    status = health_check.last_status
                    status_counts[status.value] += 1
                    component_status[health_check.component_type.value].append({
                        "name": health_check.name,
                        "status": status.value,
                        "last_check": health_check.last_check.isoformat() if health_check.last_check else None,
                        "failure_count": health_check.failure_count
                    })
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(self.health_checks),
            "enabled_checks": sum(1 for hc in self.health_checks.values() if hc.enabled),
            "status_counts": dict(status_counts),
            "component_status": dict(component_status)
        }
    
    def start_monitoring(self):
        """Start background health monitoring."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self.logger.warning("Health monitoring already started")
            return
        
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        self.logger.info("Started health monitoring")
    
    def stop_monitoring(self):
        """Stop background health monitoring."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._stop_monitoring.set()
            self._monitoring_thread.join(timeout=5.0)
            self.logger.info("Stopped health monitoring")
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while not self._stop_monitoring.wait(self.check_interval):
            try:
                self._run_scheduled_checks()
                self._collect_system_metrics()
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    def _run_scheduled_checks(self):
        """Run health checks that are due."""
        current_time = datetime.now()
        
        with self._lock:
            checks_to_run = []
            
            for health_check in self.health_checks.values():
                if not health_check.enabled:
                    continue
                
                # Check if it's time to run this check
                if (health_check.last_check is None or 
                    current_time - health_check.last_check >= 
                    timedelta(seconds=health_check.interval_seconds)):
                    checks_to_run.append(health_check)
        
        # Run checks outside of lock
        for health_check in checks_to_run:
            self._execute_health_check(health_check)
    
    def _collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            timestamp = datetime.now()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.system_metrics["memory_percent"].append({
                "timestamp": timestamp,
                "value": memory.percent
            })
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_metrics["cpu_percent"].append({
                "timestamp": timestamp,
                "value": cpu_percent
            })
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_metrics["disk_percent"].append({
                "timestamp": timestamp,
                "value": disk_percent
            })
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def get_metrics_history(self, metric_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metrics history for a specific metric."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if metric_name not in self.system_metrics:
            return []
        
        return [
            metric for metric in self.system_metrics[metric_name]
            if metric["timestamp"] >= cutoff_time
        ]
    
    # Built-in health check functions
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent >= self.thresholds["memory_usage_percent"]:
                status = "critical"
                message = f"High memory usage: {usage_percent:.1f}%"
            elif usage_percent >= self.thresholds["memory_usage_percent"] * 0.8:
                status = "warning"
                message = f"Elevated memory usage: {usage_percent:.1f}%"
            else:
                status = "healthy"
                message = f"Memory usage normal: {usage_percent:.1f}%"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "total_gb": round(memory.total / 1024**3, 2),
                    "available_gb": round(memory.available / 1024**3, 2),
                    "used_gb": round(memory.used / 1024**3, 2),
                    "percent": usage_percent
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Failed to check memory: {e}"
            }
    
    def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check system CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent >= self.thresholds["cpu_usage_percent"]:
                status = "critical"
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent >= self.thresholds["cpu_usage_percent"] * 0.8:
                status = "warning" 
                message = f"Elevated CPU usage: {cpu_percent:.1f}%"
            else:
                status = "healthy"
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "cpu_percent": cpu_percent,
                    "cpu_count": psutil.cpu_count(),
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Failed to check CPU: {e}"
            }
    
    def _check_disk_usage(self) -> Dict[str, Any]:
        """Check system disk usage."""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent >= self.thresholds["disk_usage_percent"]:
                status = "critical"
                message = f"High disk usage: {usage_percent:.1f}%"
            elif usage_percent >= self.thresholds["disk_usage_percent"] * 0.8:
                status = "warning"
                message = f"Elevated disk usage: {usage_percent:.1f}%"
            else:
                status = "healthy"
                message = f"Disk usage normal: {usage_percent:.1f}%"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "total_gb": round(disk.total / 1024**3, 2),
                    "used_gb": round(disk.used / 1024**3, 2),
                    "free_gb": round(disk.free / 1024**3, 2),
                    "percent": usage_percent
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Failed to check disk: {e}"
            }
    
    def _check_garbage_collection(self) -> Dict[str, Any]:
        """Check Python garbage collection statistics."""
        try:
            # Get GC stats
            gc_stats = gc.get_stats()
            total_collections = sum(stat.get('collections', 0) for stat in gc_stats)
            total_collected = sum(stat.get('collected', 0) for stat in gc_stats)
            total_uncollectable = sum(stat.get('uncollectable', 0) for stat in gc_stats)
            
            # Check if there are too many uncollectable objects
            uncollectable_ratio = total_uncollectable / max(total_collected, 1)
            
            if uncollectable_ratio > 0.1:
                status = "warning"
                message = f"High uncollectable objects ratio: {uncollectable_ratio:.2%}"
            else:
                status = "healthy"
                message = f"Garbage collection normal"
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "total_collections": total_collections,
                    "total_collected": total_collected,
                    "total_uncollectable": total_uncollectable,
                    "uncollectable_ratio": uncollectable_ratio,
                    "gc_stats": gc_stats
                }
            }
            
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Failed to check garbage collection: {e}"
            }