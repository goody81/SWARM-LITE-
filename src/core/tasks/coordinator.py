import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
from .scheduler import TaskScheduler
from .types import Task, TaskStatus
import logging

logger = logging.getLogger(__name__)


class TaskCoordinator:
    def __init__(self):
        self.scheduler = TaskScheduler()
        self.agent_capabilities: Dict[str, Dict[str, Any]] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the task coordinator"""
        self._monitoring_task = asyncio.create_task(self._monitor_tasks())
        logger.info("Task coordinator started")

    async def stop(self):
        """Stop the task coordinator"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        logger.info("Task coordinator stopped")

    async def register_agent(
        self, agent_id: str, capabilities: Dict[str, Any]
    ):
        """Register an agent with its capabilities"""
        self.agent_capabilities[agent_id] = capabilities
        logger.info(
            f"Agent {agent_id} registered with capabilities: {capabilities}"
        )

    async def submit_task(self, task: Task) -> str:
        """Submit a new task for execution"""
        await self.scheduler.add_task(task)
        return task.id

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed task"""
        return self.task_results.get(task_id)

    async def update_task_status(
        self, task_id: str, status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update task status and store results"""
        task = self.scheduler.running_tasks.get(task_id)
        if task:
            task.status = status
            task.completed_at = datetime.utcnow()
            if result:
                task.result = result
                self.task_results[task_id] = result
            if error:
                task.error = error
            logger.info(f"Task {task_id} updated to status {status}")

    async def _monitor_tasks(self):
        """Monitor task execution and handle timeouts"""
        while True:
            current_time = datetime.utcnow()
            for task_id, task in self.scheduler.running_tasks.items():
                if (task.status == TaskStatus.RUNNING and
                        task.started_at and
                        (current_time - task.started_at).total_seconds() > 300):
                    # 5 min timeout
                    await self.update_task_status(
                        task_id,
                        TaskStatus.FAILED,
                        error="Task execution timeout"
                    )
            await asyncio.sleep(60)  # Check every minute
