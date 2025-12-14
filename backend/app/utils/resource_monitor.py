"""
Resource monitoring utility for tracking CPU, memory, and database usage.
"""

import psutil
import time
import asyncio
import inspect
from typing import Dict, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor system and process resource usage."""

    @staticmethod
    def get_process_metrics() -> Dict[str, float]:
        """Get current process resource metrics."""
        process = psutil.Process()

        return {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(interval=1),
            "num_threads": process.num_threads(),
        }

    @staticmethod
    def get_system_metrics() -> Dict[str, float]:
        """Get system-wide resource metrics."""
        memory = psutil.virtual_memory()

        return {
            "total_memory_mb": memory.total / 1024 / 1024,
            "available_memory_mb": memory.available / 1024 / 1024,
            "memory_percent": memory.percent,
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
        }

    @staticmethod
    def log_resource_usage(operation: str, extra_data: Optional[Dict] = None):
        """Log current resource usage for a specific operation."""
        process_metrics = ResourceMonitor.get_process_metrics()
        system_metrics = ResourceMonitor.get_system_metrics()

        log_data = {
            "operation": operation,
            "process": process_metrics,
            "system": system_metrics,
        }

        if extra_data:
            log_data.update(extra_data)

        logger.info(
            f"Resource usage during {operation}: "
            f"Process RAM={process_metrics['memory_mb']:.2f}MB "
            f"({process_metrics['memory_percent']:.1f}%), "
            f"Process CPU={process_metrics['cpu_percent']:.1f}%, "
            f"System RAM={system_metrics['memory_percent']:.1f}%, "
            f"System CPU={system_metrics['cpu_percent']:.1f}%"
        )

        return log_data


def monitor_resources(operation_name: str):
    """
    Decorator to monitor resource usage for both sync and async functions.

    Automatically detects whether the decorated function is async or sync
    and applies the appropriate wrapper.

    Args:
        operation_name: Name to identify this operation in logs

    Example:
        @monitor_resources("Data Ingestion")
        async def fetch_data():
            ...
    """
    def decorator(func):
        # Detect if function is async using inspect module
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                ResourceMonitor.log_resource_usage(f"{operation_name} - START")

                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    ResourceMonitor.log_resource_usage(
                        f"{operation_name} - END",
                        {"duration_seconds": duration}
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    ResourceMonitor.log_resource_usage(
                        f"{operation_name} - ERROR",
                        {"duration_seconds": duration, "error": str(e)}
                    )
                    raise

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                ResourceMonitor.log_resource_usage(f"{operation_name} - START")

                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    ResourceMonitor.log_resource_usage(
                        f"{operation_name} - END",
                        {"duration_seconds": duration}
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    ResourceMonitor.log_resource_usage(
                        f"{operation_name} - ERROR",
                        {"duration_seconds": duration, "error": str(e)}
                    )
                    raise

            return sync_wrapper

    return decorator
