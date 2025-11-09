"""Task coordination and distribution for SWARM-LITE-."""

import asyncio
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Callable, DefaultDict, Deque, Dict, List, Optional, Set
from uuid import UUID

from ..protocols.task import Task, TaskBatch
from .types import (
    AgentCapabilities,
    AgentInfo,
    AgentState,
    AgentStatus,
    TaskPriority,
    TaskState,
    SystemEvent,
)
from ..utils.config import get_config
from ..utils.logging import get_logger
from ..utils.metrics import get_metrics_collector

logger = get_logger("coordinator")


class TaskCoordinator:
    """Coordinates task distribution and execution across agents."""

    def __init__(self, communication_hub: Any):
        """Initialize task coordinator.

        Args:
            communication_hub: Communication hub instance
        """
        self.config = get_config()
        self.metrics = get_metrics_collector()
        self.hub = communication_hub

        # Task management
        self._tasks: Dict[UUID, Task] = {}
        self._task_queue: Deque[Task] = deque()
        self._task_batches: Dict[UUID, TaskBatch] = {}

        # Agent tracking
        self._agent_tasks: DefaultDict[UUID, Set[UUID]] = defaultdict(set)
        self._agent_capabilities: Dict[UUID, AgentCapabilities] = {}

        # Load balancing strategy
        self._load_balancing_strategy = self.config.coordinator_load_balancing_strategy

        # Scheduling
        self._running = False
        self._scheduling_task: Optional[asyncio.Task] = None
        self._failure_recovery_task: Optional[asyncio.Task] = None

        logger.info("Task coordinator initialized")

    async def start(self) -> None:
        """Start the task coordinator."""
        if self._running:
            logger.warning("Task coordinator already running")
            return

        logger.info("Starting task coordinator")
        self._running = True

        # Start background tasks
        self._scheduling_task = asyncio.create_task(self._scheduling_loop())
        self._failure_recovery_task = asyncio.create_task(self._failure_recovery_loop())

        logger.info("Task coordinator started")

    async def stop(self) -> None:
        """Stop the task coordinator."""
        if not self._running:
            return

        logger.info("Stopping task coordinator")
        self._running = False

        # Cancel background tasks
        if self._scheduling_task:
            self._scheduling_task.cancel()
            try:
                await self._scheduling_task
            except asyncio.CancelledError:
                pass

        if self._failure_recovery_task:
            self._failure_recovery_task.cancel()
            try:
                await self._failure_recovery_task
            except asyncio.CancelledError:
                pass

        logger.info("Task coordinator stopped")

    async def submit_task(self, task: Task) -> UUID:
        """Submit a task for execution.

        Args:
            task: Task to submit

        Returns:
            Task identifier
        """
        if not self._running:
            raise RuntimeError("Task coordinator not running")

        # Validate task
        if not task.task_type:
            raise ValueError("Task type is required")

        # Store task
        self._tasks[task.task_id] = task
        task.state = TaskState.QUEUED

        # Add to priority queue
        self._enqueue_task(task)

        self.metrics.record_counter("swarm.tasks.submitted")
        self.metrics.record_gauge("swarm.tasks.queued", len(self._task_queue))

        logger.info(f"Task submitted", task_id=str(task.task_id), task_type=task.task_type)

        # Notify system event
        await self.hub.publish(
            "system.events.task_created",
            {"task_id": str(task.task_id), "task_type": task.task_type},
        )

        return task.task_id

    async def submit_batch(self, batch: TaskBatch) -> UUID:
        """Submit a batch of tasks.

        Args:
            batch: Task batch to submit

        Returns:
            Batch identifier
        """
        if not self._running:
            raise RuntimeError("Task coordinator not running")

        # Store batch
        self._task_batches[batch.batch_id] = batch

        # Submit all tasks
        for task in batch.tasks:
            await self.submit_task(task)

        logger.info(f"Task batch submitted", batch_id=str(batch.batch_id), task_count=len(batch.tasks))

        return batch.batch_id

    async def cancel_task(self, task_id: UUID) -> bool:
        """Cancel a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
            return False

        # Remove from queue if pending
        if task.state == TaskState.QUEUED:
            try:
                self._task_queue.remove(task)
            except ValueError:
                pass

        # Cancel on agent if running
        if task.state == TaskState.RUNNING and task.assigned_agent_id:
            agent = self.hub._agents.get(task.assigned_agent_id)
            if agent:
                await agent.cancel_task(task_id)

        task.state = TaskState.CANCELLED
        task.completed_at = datetime.utcnow()

        self.metrics.record_counter("swarm.tasks.cancelled")
        logger.info(f"Task cancelled", task_id=str(task_id))

        return True

    def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get task information.

        Args:
            task_id: Task identifier

        Returns:
            Task or None
        """
        return self._tasks.get(task_id)

    def get_task_state(self, task_id: UUID) -> Optional[TaskState]:
        """Get task state.

        Args:
            task_id: Task identifier

        Returns:
            Task state or None
        """
        task = self._tasks.get(task_id)
        return task.state if task else None

    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks.

        Returns:
            List of pending tasks
        """
        return list(self._task_queue)

    def get_active_tasks(self) -> List[Task]:
        """Get all active (running) tasks.

        Returns:
            List of active tasks
        """
        return [t for t in self._tasks.values() if t.state == TaskState.RUNNING]

    async def _scheduling_loop(self) -> None:
        """Background loop for task scheduling."""
        while self._running:
            try:
                await self._schedule_tasks()
                await asyncio.sleep(self.config.coordinator_scheduling_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}", exc_info=True)

    async def _schedule_tasks(self) -> None:
        """Schedule pending tasks to available agents."""
        if not self._task_queue:
            return

        # Get available agents
        agents = self.hub.get_all_agents()
        available_agents = [
            agent for agent in agents
            if agent.state in [AgentState.IDLE, AgentState.BUSY]
            and agent.status == AgentStatus.HEALTHY
        ]

        if not available_agents:
            return

        # Try to schedule tasks
        scheduled_count = 0
        while self._task_queue and scheduled_count < len(available_agents):
            task = self._task_queue[0]

            # Find suitable agent
            agent = self._find_suitable_agent(task, available_agents)
            if not agent:
                # Can't schedule this task yet, move to next
                self._task_queue.rotate(-1)
                break

            # Remove task from queue
            self._task_queue.popleft()

            # Assign task to agent
            await self._assign_task(task, agent)
            scheduled_count += 1

        if scheduled_count > 0:
            self.metrics.record_counter("swarm.tasks.scheduled", scheduled_count)
            self.metrics.record_gauge("swarm.tasks.queued", len(self._task_queue))
            logger.debug(f"Scheduled {scheduled_count} tasks")

    def _find_suitable_agent(self, task: Task, agents: List[AgentInfo]) -> Optional[AgentInfo]:
        """Find suitable agent for task based on capabilities and load.

        Args:
            task: Task to schedule
            agents: List of available agents

        Returns:
            Selected agent or None
        """
        # Filter by capabilities
        capable_agents = []
        for agent in agents:
            # Check if agent supports task type
            if task.task_type not in agent.capabilities.supported_task_types:
                continue

            # Check if agent has capacity
            active_tasks = len(self._agent_tasks.get(agent.agent_id, set()))
            if active_tasks >= agent.capabilities.max_concurrent_tasks:
                continue

            capable_agents.append(agent)

        if not capable_agents:
            return None

        # Apply load balancing strategy
        if self._load_balancing_strategy == "least_loaded":
            return self._select_least_loaded_agent(capable_agents)
        elif self._load_balancing_strategy == "round_robin":
            return capable_agents[0]
        else:
            return capable_agents[0]

    def _select_least_loaded_agent(self, agents: List[AgentInfo]) -> Optional[AgentInfo]:
        """Select agent with least load.

        Args:
            agents: List of capable agents

        Returns:
            Selected agent
        """
        if not agents:
            return None

        # Find agent with fewest active tasks
        min_load = float("inf")
        selected_agent = None

        for agent in agents:
            active_tasks = len(self._agent_tasks.get(agent.agent_id, set()))
            if active_tasks < min_load:
                min_load = active_tasks
                selected_agent = agent

        return selected_agent

    async def _assign_task(self, task: Task, agent_info: AgentInfo) -> None:
        """Assign task to agent.

        Args:
            task: Task to assign
            agent_info: Agent information
        """
        agent = self.hub._agents.get(agent_info.agent_id)
        if not agent:
            logger.warning(f"Agent not found", agent_id=str(agent_info.agent_id))
            # Re-queue task
            self._task_queue.append(task)
            return

        task.state = TaskState.ASSIGNED
        task.assigned_agent_id = agent_info.agent_id
        self._agent_tasks[agent_info.agent_id].add(task.task_id)

        logger.info(
            f"Task assigned",
            task_id=str(task.task_id),
            agent_id=str(agent_info.agent_id),
        )

        # Execute task on agent (non-blocking)
        asyncio.create_task(self._execute_task_on_agent(task, agent))

    async def _execute_task_on_agent(self, task: Task, agent: Any) -> None:
        """Execute task on agent and handle result.

        Args:
            task: Task to execute
            agent: Agent instance
        """
        try:
            result = await agent.execute_task(task)

            # Task completed successfully
            await self.hub.publish(
                "system.events.task_completed",
                {
                    "task_id": str(task.task_id),
                    "agent_id": str(agent.agent_id),
                    "duration_seconds": (task.completed_at - task.started_at).total_seconds()
                    if task.completed_at and task.started_at else None,
                },
            )

        except Exception as e:
            logger.error(
                f"Task execution failed",
                task_id=str(task.task_id),
                agent_id=str(agent.agent_id),
                error=str(e),
            )

            # Task failed
            await self.hub.publish(
                "system.events.task_failed",
                {
                    "task_id": str(task.task_id),
                    "agent_id": str(agent.agent_id),
                    "error": str(e),
                },
            )

            # Retry if possible
            if task.can_retry():
                task.retry_count += 1
                task.state = TaskState.PENDING
                task.assigned_agent_id = None
                self._enqueue_task(task)
                logger.info(f"Task queued for retry", task_id=str(task.task_id), retry_count=task.retry_count)

        finally:
            # Clean up agent tracking
            if task.assigned_agent_id:
                self._agent_tasks[task.assigned_agent_id].discard(task.task_id)

    def _enqueue_task(self, task: Task) -> None:
        """Add task to priority queue.

        Args:
            task: Task to enqueue
        """
        # Simple priority-based insertion
        # Tasks are ordered by priority (lower value = higher priority)
        inserted = False
        for i, queued_task in enumerate(self._task_queue):
            if task.priority.value < queued_task.priority.value:
                self._task_queue.insert(i, task)
                inserted = True
                break

        if not inserted:
            self._task_queue.append(task)

    async def _failure_recovery_loop(self) -> None:
        """Background loop for handling failures and timeouts."""
        while self._running:
            try:
                await self._check_for_failures()
                await asyncio.sleep(10.0)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in failure recovery loop: {e}", exc_info=True)

    async def _check_for_failures(self) -> None:
        """Check for task timeouts and agent failures."""
        # Check for task timeouts
        for task in list(self._tasks.values()):
            if task.state == TaskState.RUNNING and task.is_timeout():
                logger.warning(f"Task timeout detected", task_id=str(task.task_id))

                task.state = TaskState.TIMEOUT
                task.completed_at = datetime.utcnow()

                # Retry if possible
                if task.can_retry():
                    task.retry_count += 1
                    task.state = TaskState.PENDING
                    task.assigned_agent_id = None
                    self._enqueue_task(task)

        # Check for unresponsive agents
        agents = self.hub.get_all_agents()
        for agent_info in agents:
            if agent_info.status == AgentStatus.UNHEALTHY:
                # Re-queue tasks from unhealthy agent
                agent_tasks = self._agent_tasks.get(agent_info.agent_id, set())
                for task_id in list(agent_tasks):
                    task = self._tasks.get(task_id)
                    if task and task.state == TaskState.RUNNING:
                        logger.warning(
                            f"Re-queuing task from unhealthy agent",
                            task_id=str(task_id),
                            agent_id=str(agent_info.agent_id),
                        )

                        task.state = TaskState.PENDING
                        task.assigned_agent_id = None
                        self._enqueue_task(task)
                        agent_tasks.discard(task_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get coordinator statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_tasks": len(self._tasks),
            "queued_tasks": len(self._task_queue),
            "active_tasks": len([t for t in self._tasks.values() if t.state == TaskState.RUNNING]),
            "completed_tasks": len([t for t in self._tasks.values() if t.state == TaskState.COMPLETED]),
            "failed_tasks": len([t for t in self._tasks.values() if t.state == TaskState.FAILED]),
            "active_agents": len(self.hub.get_all_agents()),
        }
