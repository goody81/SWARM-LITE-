import asyncio
from typing import Dict, List, Optional, Any
from .types import Task, TaskStatus
import heapq
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def add_task(self, task: Task) -> None:
        """Add a task to the scheduler"""
        async with self._lock:
            # Negate priority for min-heap (higher priority = lower number)
            heapq.heappush(
                self.task_queue,
                (-task.priority.value, task.created_at, task)
            )
            logger.info(
                f"Task {task.id} added to queue with priority {task.priority}"
            )

    async def get_next_task(
        self, agent_capabilities: Dict[str, Any]
    ) -> Optional[Task]:
        """Get the next suitable task for an agent"""
        async with self._lock:
            checked_tasks = []
            result_task = None

            while self.task_queue:
                _, _, task = heapq.heappop(self.task_queue)
                if self._can_handle_task(task, agent_capabilities):
                    task.status = TaskStatus.ASSIGNED
                    self.running_tasks[task.id] = task
                    result_task = task
                    break
                else:
                    checked_tasks.append(
                        (-task.priority.value, task.created_at, task)
                    )

            # Re-add tasks that couldn't be handled
            for task_tuple in checked_tasks:
                heapq.heappush(self.task_queue, task_tuple)

            return result_task

    def _can_handle_task(
        self, task: Task, capabilities: Dict[str, Any]
    ) -> bool:
        """Check if an agent can handle a task"""
        return (
            capabilities.get("cpu", 0) >= task.requirements.min_cpu and
            capabilities.get("memory", 0) >= task.requirements.min_memory and
            all(cap in capabilities.get("capabilities", [])
                for cap in task.requirements.capabilities)
        )
