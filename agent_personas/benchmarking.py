"""
Benchmarking utilities for performance testing and optimization.
"""

import time
import statistics
import psutil
import gc
import functools
from typing import Callable, Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict
import threading
from contextlib import contextmanager
from .exceptions import PersonaError


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    function_name: str
    total_runs: int
    total_time: float
    min_time: float
    max_time: float
    mean_time: float
    median_time: float
    std_dev: float
    runs_per_second: float
    memory_usage: Optional[float] = None
    memory_peak: Optional[float] = None
    errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics during benchmark."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_io_read: int
    disk_io_write: int
    timestamp: float = field(default_factory=time.time)


class Benchmarker:
    """Comprehensive benchmarking tool."""
    
    def __init__(self, warmup_runs: int = 5, collect_gc: bool = True):
        """
        Initialize benchmarker.
        
        Args:
            warmup_runs: Number of warmup runs before measurement
            collect_gc: Whether to run garbage collection before benchmarks
        """
        self.warmup_runs = warmup_runs
        self.collect_gc = collect_gc
        self.results: Dict[str, BenchmarkResult] = {}
        self.system_metrics: List[SystemMetrics] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
    
    def benchmark(
        self,
        func: Callable,
        runs: int = 100,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        monitor_memory: bool = True
    ) -> BenchmarkResult:
        """
        Benchmark a function.
        
        Args:
            func: Function to benchmark
            runs: Number of benchmark runs
            args: Function arguments
            kwargs: Function keyword arguments
            name: Custom name for benchmark
            monitor_memory: Whether to monitor memory usage
        
        Returns:
            Benchmark results
        """
        if kwargs is None:
            kwargs = {}
        
        function_name = name or func.__name__
        
        # Garbage collection
        if self.collect_gc:
            gc.collect()
        
        # Warmup runs
        for _ in range(self.warmup_runs):
            try:
                func(*args, **kwargs)
            except Exception:
                pass  # Ignore errors in warmup
        
        # Start system monitoring
        if monitor_memory:
            self._start_monitoring()
        
        # Benchmark runs
        times = []
        errors = 0
        memory_usage = []
        
        initial_memory = self._get_memory_usage() if monitor_memory else None
        
        for _ in range(runs):
            start_memory = self._get_memory_usage() if monitor_memory else None
            
            start_time = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception:
                errors += 1
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            times.append(execution_time)
            
            if monitor_memory and start_memory is not None:
                end_memory = self._get_memory_usage()
                memory_usage.append(end_memory - start_memory)
        
        # Stop monitoring
        if monitor_memory:
            self._stop_monitoring()
        
        # Calculate statistics
        if not times:
            raise PersonaError(f"All benchmark runs failed for {function_name}")
        
        total_time = sum(times)
        mean_time = statistics.mean(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        
        result = BenchmarkResult(
            function_name=function_name,
            total_runs=runs,
            total_time=total_time,
            min_time=min(times),
            max_time=max(times),
            mean_time=mean_time,
            median_time=median_time,
            std_dev=std_dev,
            runs_per_second=runs / total_time,
            memory_usage=statistics.mean(memory_usage) if memory_usage else None,
            memory_peak=max(memory_usage) if memory_usage else None,
            errors=errors
        )
        
        self.results[function_name] = result
        return result
    
    def compare_functions(
        self,
        functions: List[Callable],
        runs: int = 100,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, BenchmarkResult]:
        """
        Compare multiple functions with the same inputs.
        
        Args:
            functions: List of functions to compare
            runs: Number of runs for each function
            args: Function arguments
            kwargs: Function keyword arguments
        
        Returns:
            Dictionary of benchmark results
        """
        results = {}
        
        for func in functions:
            result = self.benchmark(func, runs, args, kwargs)
            results[func.__name__] = result
        
        return results
    
    def benchmark_suite(
        self,
        suite: Dict[str, Dict[str, Any]]
    ) -> Dict[str, BenchmarkResult]:
        """
        Run a suite of benchmarks.
        
        Args:
            suite: Dictionary with benchmark configurations
                   {"name": {"func": callable, "args": tuple, "kwargs": dict, "runs": int}}
        
        Returns:
            Dictionary of benchmark results
        """
        results = {}
        
        for name, config in suite.items():
            func = config['func']
            args = config.get('args', ())
            kwargs = config.get('kwargs', {})
            runs = config.get('runs', 100)
            
            result = self.benchmark(func, runs, args, kwargs, name)
            results[name] = result
        
        return results
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def _start_monitoring(self):
        """Start system monitoring thread."""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._monitoring_thread = threading.Thread(target=self._monitor_system)
            self._monitoring_thread.daemon = True
            self._monitoring_thread.start()
    
    def _stop_monitoring(self):
        """Stop system monitoring thread."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=1.0)
    
    def _monitor_system(self):
        """Monitor system resources."""
        while self._monitoring_active:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                
                metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_available_mb=memory.available / (1024 * 1024),
                    disk_io_read=disk_io.read_bytes if disk_io else 0,
                    disk_io_write=disk_io.write_bytes if disk_io else 0
                )
                
                self.system_metrics.append(metrics)
                
                time.sleep(0.1)
                
            except Exception:
                break
    
    def get_report(self, format_type: str = 'text') -> str:
        """
        Generate benchmark report.
        
        Args:
            format_type: Report format ('text', 'markdown', 'csv')
        
        Returns:
            Formatted report string
        """
        if format_type == 'text':
            return self._generate_text_report()
        elif format_type == 'markdown':
            return self._generate_markdown_report()
        elif format_type == 'csv':
            return self._generate_csv_report()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _generate_text_report(self) -> str:
        """Generate text format report."""
        lines = ["Benchmark Results", "=" * 50, ""]
        
        for name, result in self.results.items():
            lines.append(f"Function: {name}")
            lines.append(f"  Total runs: {result.total_runs}")
            lines.append(f"  Total time: {result.total_time:.4f}s")
            lines.append(f"  Mean time: {result.mean_time:.6f}s")
            lines.append(f"  Median time: {result.median_time:.6f}s")
            lines.append(f"  Min/Max: {result.min_time:.6f}s / {result.max_time:.6f}s")
            lines.append(f"  Std dev: {result.std_dev:.6f}s")
            lines.append(f"  Runs/sec: {result.runs_per_second:.2f}")
            
            if result.memory_usage is not None:
                lines.append(f"  Memory usage: {result.memory_usage:.2f} MB (peak: {result.memory_peak:.2f} MB)")
            
            if result.errors > 0:
                lines.append(f"  Errors: {result.errors}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown format report."""
        lines = ["# Benchmark Results", ""]
        
        # Summary table
        lines.append("| Function | Runs | Mean Time | Runs/sec | Memory (MB) | Errors |")
        lines.append("|----------|------|-----------|----------|-------------|--------|")
        
        for name, result in self.results.items():
            memory_str = f"{result.memory_usage:.2f}" if result.memory_usage else "N/A"
            lines.append(
                f"| {name} | {result.total_runs} | {result.mean_time:.6f}s | "
                f"{result.runs_per_second:.2f} | {memory_str} | {result.errors} |"
            )
        
        lines.append("")
        
        # Detailed results
        for name, result in self.results.items():
            lines.append(f"## {name}")
            lines.append(f"- **Total time:** {result.total_time:.4f}s")
            lines.append(f"- **Mean time:** {result.mean_time:.6f}s")
            lines.append(f"- **Median time:** {result.median_time:.6f}s")
            lines.append(f"- **Min/Max:** {result.min_time:.6f}s / {result.max_time:.6f}s")
            lines.append(f"- **Standard deviation:** {result.std_dev:.6f}s")
            lines.append(f"- **Throughput:** {result.runs_per_second:.2f} runs/sec")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_csv_report(self) -> str:
        """Generate CSV format report."""
        lines = ["function,runs,total_time,mean_time,median_time,min_time,max_time,std_dev,runs_per_sec,memory_usage,errors"]
        
        for name, result in self.results.items():
            memory_usage = result.memory_usage or ""
            lines.append(
                f"{name},{result.total_runs},{result.total_time},{result.mean_time},"
                f"{result.median_time},{result.min_time},{result.max_time},{result.std_dev},"
                f"{result.runs_per_second},{memory_usage},{result.errors}"
            )
        
        return "\n".join(lines)


# Decorators for easy benchmarking

def benchmark(runs: int = 100, warmup_runs: int = 5):
    """Decorator to benchmark a function."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            benchmarker = Benchmarker(warmup_runs=warmup_runs)
            result = benchmarker.benchmark(func, runs, args, kwargs)
            print(f"Benchmark for {func.__name__}: {result.mean_time:.6f}s avg ({result.runs_per_second:.2f} runs/sec)")
            return func(*args, **kwargs)
        
        # Add benchmark method
        wrapper.benchmark = lambda r=runs: Benchmarker().benchmark(func, r)
        return wrapper
    
    return decorator


@contextmanager
def time_block(name: str = "block", print_result: bool = True):
    """Context manager for timing code blocks."""
    start_time = time.perf_counter()
    start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
    
    try:
        yield
    finally:
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        execution_time = end_time - start_time
        memory_diff = end_memory - start_memory
        
        if print_result:
            print(f"{name}: {execution_time:.4f}s (memory: {memory_diff:+.2f} MB)")


def profile_memory(func: Callable) -> Callable:
    """Decorator to profile memory usage of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        start_memory = process.memory_info().rss / (1024 * 1024)
        
        result = func(*args, **kwargs)
        
        end_memory = process.memory_info().rss / (1024 * 1024)
        memory_diff = end_memory - start_memory
        
        print(f"{func.__name__} memory usage: {memory_diff:+.2f} MB")
        return result
    
    return wrapper


# Performance testing utilities

class PerformanceTest:
    """Performance testing framework."""
    
    def __init__(self):
        """Initialize performance test."""
        self.benchmarker = Benchmarker()
        self.test_cases = []
    
    def add_test(self, name: str, func: Callable, args: tuple = (), kwargs: Optional[Dict] = None, runs: int = 100):
        """Add a performance test case."""
        self.test_cases.append({
            'name': name,
            'func': func,
            'args': args,
            'kwargs': kwargs or {},
            'runs': runs
        })
    
    def run_tests(self) -> Dict[str, BenchmarkResult]:
        """Run all performance tests."""
        results = {}
        
        for test_case in self.test_cases:
            print(f"Running test: {test_case['name']}")
            
            result = self.benchmarker.benchmark(
                test_case['func'],
                test_case['runs'],
                test_case['args'],
                test_case['kwargs'],
                test_case['name']
            )
            
            results[test_case['name']] = result
        
        return results
    
    def generate_report(self, format_type: str = 'text') -> str:
        """Generate performance test report."""
        return self.benchmarker.get_report(format_type)


# Quick benchmark functions

def quick_benchmark(func: Callable, *args, runs: int = 100, **kwargs) -> float:
    """Quick benchmark of a function, returns mean execution time."""
    benchmarker = Benchmarker(warmup_runs=5)
    result = benchmarker.benchmark(func, runs, args, kwargs)
    return result.mean_time


def compare_performance(func1: Callable, func2: Callable, *args, runs: int = 100, **kwargs) -> Dict[str, float]:
    """Compare performance of two functions."""
    benchmarker = Benchmarker()
    results = benchmarker.compare_functions([func1, func2], runs, args, kwargs)
    
    return {
        func1.__name__: results[func1.__name__].mean_time,
        func2.__name__: results[func2.__name__].mean_time
    }