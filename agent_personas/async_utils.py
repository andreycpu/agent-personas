"""
Asynchronous utilities for agent_personas package.
"""

import asyncio
import functools
import time
import threading
from typing import Any, Callable, Awaitable, Optional, List, Dict, Union
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from .exceptions import PersonaError
from .monitoring import PerformanceMonitor


@dataclass
class AsyncTaskResult:
    """Result from an async task."""
    task_id: str
    result: Any
    error: Optional[Exception]
    start_time: float
    end_time: float
    
    @property
    def duration(self) -> float:
        """Get task duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def success(self) -> bool:
        """Check if task was successful."""
        return self.error is None


class AsyncTaskManager:
    """Manager for asynchronous tasks."""
    
    def __init__(self, max_workers: int = 10):
        """Initialize async task manager."""
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, Future] = {}
        self.results: Dict[str, AsyncTaskResult] = {}
        self.performance_monitor = PerformanceMonitor()
        self._task_counter = 0
        self._lock = threading.Lock()
    
    def submit_task(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for async execution.
        
        Args:
            func: Function to execute
            *args: Function arguments
            task_id: Custom task ID (auto-generated if None)
            **kwargs: Function keyword arguments
        
        Returns:
            Task ID
        """
        if task_id is None:
            with self._lock:
                self._task_counter += 1
                task_id = f"task_{self._task_counter}"
        
        start_time = time.time()
        
        def wrapped_func():
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                
                task_result = AsyncTaskResult(
                    task_id=task_id,
                    result=result,
                    error=None,
                    start_time=start_time,
                    end_time=end_time
                )
                
                self.results[task_id] = task_result
                self.performance_monitor.record_execution(f"async_task_{func.__name__}", task_result.duration)
                
                return result
                
            except Exception as e:
                end_time = time.time()
                
                task_result = AsyncTaskResult(
                    task_id=task_id,
                    result=None,
                    error=e,
                    start_time=start_time,
                    end_time=end_time
                )
                
                self.results[task_id] = task_result
                self.performance_monitor.record_execution(f"async_task_{func.__name__}_error", task_result.duration)
                
                raise
        
        future = self.executor.submit(wrapped_func)
        self.tasks[task_id] = future
        
        return task_id
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> AsyncTaskResult:
        """
        Get result of a task.
        
        Args:
            task_id: Task identifier
            timeout: Maximum wait time in seconds
        
        Returns:
            Task result
        
        Raises:
            PersonaError: If task not found or failed
        """
        if task_id not in self.tasks:
            raise PersonaError(f"Task {task_id} not found")
        
        future = self.tasks[task_id]
        
        try:
            # Wait for completion
            future.result(timeout=timeout)
        except Exception:
            pass  # Error will be in the result object
        
        if task_id in self.results:
            return self.results[task_id]
        else:
            raise PersonaError(f"Task {task_id} result not available")
    
    def wait_for_completion(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """
        Wait for task completion.
        
        Args:
            task_id: Task identifier
            timeout: Maximum wait time in seconds
        
        Returns:
            True if task completed, False if timeout
        """
        if task_id not in self.tasks:
            return False
        
        future = self.tasks[task_id]
        
        try:
            future.result(timeout=timeout)
            return True
        except Exception:
            return True  # Completed with error
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            True if successfully cancelled
        """
        if task_id not in self.tasks:
            return False
        
        future = self.tasks[task_id]
        cancelled = future.cancel()
        
        if cancelled:
            # Clean up
            del self.tasks[task_id]
            if task_id in self.results:
                del self.results[task_id]
        
        return cancelled
    
    def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs."""
        active = []
        for task_id, future in list(self.tasks.items()):
            if not future.done():
                active.append(task_id)
        return active
    
    def get_completed_tasks(self) -> List[str]:
        """Get list of completed task IDs."""
        completed = []
        for task_id, future in list(self.tasks.items()):
            if future.done():
                completed.append(task_id)
        return completed
    
    def cleanup_completed_tasks(self):
        """Clean up completed tasks to free memory."""
        completed_tasks = []
        
        for task_id, future in list(self.tasks.items()):
            if future.done():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.tasks[task_id]
            # Keep results for later retrieval
    
    def shutdown(self, wait: bool = True):
        """Shutdown the task manager."""
        self.executor.shutdown(wait=wait)


# Global task manager instance
_global_task_manager = AsyncTaskManager()


def async_task(task_id: Optional[str] = None):
    """Decorator to make a function run asynchronously."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return _global_task_manager.submit_task(func, *args, task_id=task_id, **kwargs)
        
        return wrapper
    
    return decorator


def run_async(func: Callable, *args, **kwargs) -> str:
    """Run a function asynchronously and return task ID."""
    return _global_task_manager.submit_task(func, *args, **kwargs)


def get_async_result(task_id: str, timeout: Optional[float] = None) -> AsyncTaskResult:
    """Get result from an async task."""
    return _global_task_manager.get_result(task_id, timeout)


def wait_for_task(task_id: str, timeout: Optional[float] = None) -> bool:
    """Wait for an async task to complete."""
    return _global_task_manager.wait_for_completion(task_id, timeout)


class AsyncBatch:
    """Batch processor for multiple async operations."""
    
    def __init__(self, max_concurrent: int = 10):
        """Initialize batch processor."""
        self.max_concurrent = max_concurrent
        self.task_manager = AsyncTaskManager(max_workers=max_concurrent)
        self.batch_tasks: List[str] = []
    
    def add_task(self, func: Callable, *args, **kwargs) -> str:
        """Add a task to the batch."""
        task_id = self.task_manager.submit_task(func, *args, **kwargs)
        self.batch_tasks.append(task_id)
        return task_id
    
    def wait_all(self, timeout: Optional[float] = None) -> Dict[str, AsyncTaskResult]:
        """Wait for all tasks to complete."""
        results = {}
        
        for task_id in self.batch_tasks:
            try:
                result = self.task_manager.get_result(task_id, timeout)
                results[task_id] = result
            except Exception as e:
                # Create error result
                results[task_id] = AsyncTaskResult(
                    task_id=task_id,
                    result=None,
                    error=e,
                    start_time=time.time(),
                    end_time=time.time()
                )
        
        return results
    
    def get_successful_results(self) -> Dict[str, Any]:
        """Get only successful task results."""
        all_results = self.wait_all()
        successful = {}
        
        for task_id, result in all_results.items():
            if result.success:
                successful[task_id] = result.result
        
        return successful
    
    def get_failed_tasks(self) -> Dict[str, Exception]:
        """Get failed tasks and their errors."""
        all_results = self.wait_all()
        failed = {}
        
        for task_id, result in all_results.items():
            if not result.success:
                failed[task_id] = result.error
        
        return failed


class RateLimitedAsyncExecutor:
    """Async executor with rate limiting."""
    
    def __init__(self, max_rate: float, time_window: float = 1.0):
        """
        Initialize rate limited executor.
        
        Args:
            max_rate: Maximum operations per time window
            time_window: Time window in seconds
        """
        self.max_rate = max_rate
        self.time_window = time_window
        self.task_times: List[float] = []
        self.task_manager = AsyncTaskManager()
        self._lock = threading.Lock()
    
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit task with rate limiting."""
        with self._lock:
            current_time = time.time()
            
            # Remove old task times outside the window
            self.task_times = [
                t for t in self.task_times
                if current_time - t < self.time_window
            ]
            
            # Check if we're at the rate limit
            if len(self.task_times) >= self.max_rate:
                # Calculate how long to wait
                oldest_task_time = min(self.task_times)
                wait_time = self.time_window - (current_time - oldest_task_time)
                
                if wait_time > 0:
                    time.sleep(wait_time)
                    current_time = time.time()
            
            # Record this task time
            self.task_times.append(current_time)
        
        return self.task_manager.submit_task(func, *args, **kwargs)


# Async convenience functions

async def async_map(func: Callable, iterable, max_concurrent: int = 10) -> List[Any]:
    """
    Asynchronous map function.
    
    Args:
        func: Function to apply
        iterable: Items to process
        max_concurrent: Maximum concurrent operations
    
    Returns:
        List of results
    """
    batch = AsyncBatch(max_concurrent)
    
    # Submit all tasks
    for item in iterable:
        batch.add_task(func, item)
    
    # Wait for results
    results = batch.wait_all()
    
    # Return results in order
    ordered_results = []
    for task_id in batch.batch_tasks:
        if task_id in results and results[task_id].success:
            ordered_results.append(results[task_id].result)
        else:
            ordered_results.append(None)  # Failed tasks return None
    
    return ordered_results


def parallel_process(func: Callable, items: List[Any], max_workers: int = 10) -> List[Any]:
    """
    Process items in parallel.
    
    Args:
        func: Function to apply to each item
        items: List of items to process
        max_workers: Maximum worker threads
    
    Returns:
        List of results in same order as input
    """
    batch = AsyncBatch(max_workers)
    
    # Submit tasks
    task_ids = []
    for item in items:
        task_id = batch.add_task(func, item)
        task_ids.append(task_id)
    
    # Get results
    results = batch.wait_all()
    
    # Return in order
    ordered_results = []
    for task_id in task_ids:
        if task_id in results and results[task_id].success:
            ordered_results.append(results[task_id].result)
        else:
            error = results[task_id].error if task_id in results else Exception("Unknown error")
            ordered_results.append(error)
    
    return ordered_results


def timeout_wrapper(timeout: float):
    """Decorator to add timeout to function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            task_manager = AsyncTaskManager(max_workers=1)
            task_id = task_manager.submit_task(func, *args, **kwargs)
            
            try:
                result = task_manager.get_result(task_id, timeout=timeout)
                if result.success:
                    return result.result
                else:
                    raise result.error
            except Exception as e:
                task_manager.cancel_task(task_id)
                raise PersonaError(f"Function {func.__name__} timed out after {timeout}s") from e
            finally:
                task_manager.shutdown()
        
        return wrapper
    
    return decorator


# Context managers for async operations

class AsyncContext:
    """Context manager for async operations."""
    
    def __init__(self, max_workers: int = 10):
        """Initialize async context."""
        self.task_manager = AsyncTaskManager(max_workers)
        self.submitted_tasks: List[str] = []
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and clean up."""
        # Wait for all submitted tasks to complete
        for task_id in self.submitted_tasks:
            try:
                self.task_manager.wait_for_completion(task_id, timeout=30)
            except:
                pass  # Ignore errors on cleanup
        
        self.task_manager.shutdown()
    
    def submit(self, func: Callable, *args, **kwargs) -> str:
        """Submit task in this context."""
        task_id = self.task_manager.submit_task(func, *args, **kwargs)
        self.submitted_tasks.append(task_id)
        return task_id
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> AsyncTaskResult:
        """Get task result."""
        return self.task_manager.get_result(task_id, timeout)


# Usage example
def example_async_usage():
    """Example of how to use async utilities."""
    
    # Using context manager
    with AsyncContext(max_workers=5) as ctx:
        # Submit multiple tasks
        task1 = ctx.submit(lambda x: x * 2, 10)
        task2 = ctx.submit(lambda x: x ** 2, 5)
        
        # Get results
        result1 = ctx.get_result(task1)
        result2 = ctx.get_result(task2)
        
        print(f"Results: {result1.result}, {result2.result}")
    
    # Using batch processing
    def process_item(item):
        time.sleep(0.1)  # Simulate work
        return item * 2
    
    items = list(range(10))
    results = parallel_process(process_item, items, max_workers=3)
    print(f"Parallel results: {results}")
    
    # Using decorators
    @async_task()
    def background_task(value):
        time.sleep(1)
        return value * 3
    
    task_id = background_task(15)
    result = get_async_result(task_id, timeout=2)
    print(f"Background task result: {result.result}")