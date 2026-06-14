"""
Async semaphore pool for concurrent task management (up to 5000 concurrent tasks)
"""

import asyncio
from typing import Callable, Any, List, Optional
from src.core.constants import DEFAULT_SEMAPHORE_LIMIT, MAX_CONCURRENT_TASKS
import structlog

logger = structlog.get_logger(__name__)


class AsyncSemaphorePool:
    """Manages concurrent tasks with semaphore-based rate limiting"""
    
    def __init__(self, max_concurrent: int = DEFAULT_SEMAPHORE_LIMIT):
        if max_concurrent > MAX_CONCURRENT_TASKS:
            max_concurrent = MAX_CONCURRENT_TASKS
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
    
    async def run_task(
        self,
        task: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Run a single task with semaphore protection"""
        async with self.semaphore:
            self.active_tasks += 1
            try:
                result = await task(*args, **kwargs)
                self.completed_tasks += 1
                return result
            except Exception as e:
                self.failed_tasks += 1
                await logger.aerror(
                    "Task failed in semaphore pool",
                    error=str(e),
                    active_tasks=self.active_tasks
                )
                raise
            finally:
                self.active_tasks -= 1
    
    async def run_tasks(
        self,
        tasks: List[tuple],
        return_exceptions: bool = True
    ) -> List[Any]:
        """Run multiple tasks concurrently with semaphore control
        
        tasks: List of (callable, args, kwargs) tuples
        """
        async def wrapped_task(task_tuple):
            if len(task_tuple) == 3:
                task_func, args, kwargs = task_tuple
            elif len(task_tuple) == 2:
                task_func, args = task_tuple
                kwargs = {}
            else:
                task_func = task_tuple[0]
                args = ()
                kwargs = {}
            
            return await self.run_task(task_func, *args, **kwargs)
        
        await logger.ainfo(
            "Starting concurrent tasks",
            total_tasks=len(tasks),
            max_concurrent=self.max_concurrent
        )
        
        results = await asyncio.gather(
            *[wrapped_task(t) for t in tasks],
            return_exceptions=return_exceptions
        )
        
        await logger.ainfo(
            "Concurrent tasks completed",
            completed=self.completed_tasks,
            failed=self.failed_tasks,
            total=len(tasks)
        )
        
        return results
    
    def get_stats(self) -> dict:
        """Get pool statistics"""
        return {
            "max_concurrent": self.max_concurrent,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_tasks": self.completed_tasks + self.failed_tasks
        }