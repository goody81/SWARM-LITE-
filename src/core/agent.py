"""Base agent class for SWARM-LITE-."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, Set
from uuid import UUID, uuid4

from ..protocols.message import Message, MessageType, HeartbeatMessage, StateUpdateMessage
from ..protocols.task import Task
from .types import (
    AgentCapabilities,
    AgentInfo,
    AgentState,
    AgentStatus,
    ResourceMetrics,
    TaskState,
)
from ..utils.config import get_config
from ..utils.logging import get_logger
from ..utils.metrics import get_metrics_collector

logger = get_logger("agent")


class AsyncAgent(ABC):
    """Base class for asynchronous agents."""

    def __init__(
        self,
        agent_id: Optional[UUID] = None,
        name: Optional[str] = None,
        agent_type: str = "generic",
        max_concurrent_tasks: Optional[int] = None,
        supported_task_types: Optional[list] = None,
    ):
        """Initialize agent.

        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            agent_type: Type of agent
            max_concurrent_tasks: Maximum concurrent tasks
            supported_task_types: List of supported task types
        """
        self.config = get_config()
        self.metrics = get_metrics_collector()

        self.agent_id = agent_id or uuid4()
        self.name = name or f"{agent_type}_{self.agent_id.hex[:8]}"
        self.agent_type = agent_type

        # State management
        self._state = AgentState.INITIALIZING
        self._status = AgentStatus.UNKNOWN
        self._last_heartbeat = datetime.utcnow()

        # Task management
        self._active_tasks: Dict[UUID, Task] = {}
        self._task_semaphore = asyncio.Semaphore(
            max_concurrent_tasks or self.config.agent_max_concurrent_tasks
        )

        # Capabilities
        self._capabilities = AgentCapabilities(
            agent_id=self.agent_id,
            agent_type=agent_type,
            max_concurrent_tasks=max_concurrent_tasks or self.config.agent_max_concurrent_tasks,
            supported_task_types=supported_task_types or [],
        )

        # Resource tracking
        self._resource_metrics = ResourceMetrics()

        # Communication
        self._message_queue: asyncio.Queue[Message] = asyncio.Queue(
            maxsize=self.config.message_queue_max_size
        )
        self._communication_hub = None

        # Lifecycle management
        self._running = False
        self._tasks: Set[asyncio.Task] = set()

        logger.info(f"Agent initialized", extra={"extra_fields": {"agent_id": str(self.agent_id), "name": self.name}})

    @property
    def state(self) -> AgentState:
        """Get current agent state."""
        return self._state

    @property
    def status(self) -> AgentStatus:
        """Get current agent status."""
        return self._status

    @property
    def capabilities(self) -> AgentCapabilities:
        """Get agent capabilities."""
        return self._capabilities

    @property
    def info(self) -> AgentInfo:
        """Get complete agent information."""
        return AgentInfo(
            agent_id=self.agent_id,
            name=self.name,
            state=self._state,
            status=self._status,
            capabilities=self._capabilities,
            metrics=self._resource_metrics,
            last_heartbeat=self._last_heartbeat,
        )

    async def start(self) -> None:
        """Start the agent."""
        if self._running:
            logger.warning("Agent already running", agent_id=str(self.agent_id))
            return

        logger.info("Starting agent", agent_id=str(self.agent_id))
        self._running = True
        self._state = AgentState.IDLE

        # Start background tasks
        self._tasks.add(asyncio.create_task(self._message_loop()))
        self._tasks.add(asyncio.create_task(self._heartbeat_loop()))
        self._tasks.add(asyncio.create_task(self._health_check_loop()))

        # Call subclass initialization
        await self._on_start()

        self._status = AgentStatus.HEALTHY
        logger.info("Agent started", agent_id=str(self.agent_id))

    async def stop(self) -> None:
        """Stop the agent."""
        if not self._running:
            return

        logger.info("Stopping agent", agent_id=str(self.agent_id))
        self._running = False
        self._state = AgentState.SHUTTING_DOWN

        # Cancel active tasks
        for task_id in list(self._active_tasks.keys()):
            await self.cancel_task(task_id)

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Call subclass cleanup
        await self._on_stop()

        self._state = AgentState.OFFLINE
        logger.info("Agent stopped", agent_id=str(self.agent_id))

    async def execute_task(self, task: Task) -> Any:
        """Execute a task.

        Args:
            task: Task to execute

        Returns:
            Task result

        Raises:
            Exception: If task execution fails
        """
        if not self._running:
            raise RuntimeError("Agent is not running")

        if task.task_type not in self._capabilities.supported_task_types:
            raise ValueError(f"Task type {task.task_type} not supported by agent")

        # Wait for available slot
        async with self._task_semaphore:
            logger.info(f"Executing task", task_id=str(task.task_id), agent_id=str(self.agent_id))

            self._active_tasks[task.task_id] = task
            task.state = TaskState.RUNNING
            task.started_at = datetime.utcnow()
            task.assigned_agent_id = self.agent_id

            self._update_state()
            self.metrics.record_gauge("swarm.tasks.active", len(self._active_tasks))

            try:
                # Execute task with timeout
                timeout = task.timeout_seconds or self.config.task_default_timeout_seconds
                result = await asyncio.wait_for(
                    self._execute_task(task),
                    timeout=timeout
                )

                task.state = TaskState.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result

                self.metrics.record_counter("swarm.tasks.completed")
                logger.info(f"Task completed", task_id=str(task.task_id))

                return result

            except asyncio.TimeoutError:
                task.state = TaskState.TIMEOUT
                task.completed_at = datetime.utcnow()
                task.error = "Task execution timeout"

                self.metrics.record_counter("swarm.tasks.timeout")
                logger.error(f"Task timeout", task_id=str(task.task_id))
                raise

            except Exception as e:
                task.state = TaskState.FAILED
                task.completed_at = datetime.utcnow()
                task.error = str(e)

                self.metrics.record_counter("swarm.tasks.failed")
                logger.error(f"Task failed", task_id=str(task.task_id), error=str(e), exc_info=True)
                raise

            finally:
                self._active_tasks.pop(task.task_id, None)
                self._update_state()
                self.metrics.record_gauge("swarm.tasks.active", len(self._active_tasks))

    async def cancel_task(self, task_id: UUID) -> bool:
        """Cancel a running task.

        Args:
            task_id: Task identifier

        Returns:
            True if task was cancelled
        """
        task = self._active_tasks.get(task_id)
        if not task:
            return False

        task.state = TaskState.CANCELLED
        task.completed_at = datetime.utcnow()
        self._active_tasks.pop(task_id, None)

        self.metrics.record_counter("swarm.tasks.cancelled")
        logger.info(f"Task cancelled", task_id=str(task_id))

        return True

    async def handle_message(self, message: Message) -> None:
        """Handle incoming message.

        Args:
            message: Message to handle
        """
        try:
            await self._message_queue.put(message)
        except asyncio.QueueFull:
            logger.warning("Message queue full, dropping message", message_id=str(message.message_id))
            self.metrics.record_counter("swarm.messages.dropped")

    async def send_message(self, message: Message) -> None:
        """Send a message.

        Args:
            message: Message to send
        """
        if self._communication_hub:
            await self._communication_hub.send_message(message)
        else:
            logger.warning("No communication hub registered")

    def set_communication_hub(self, hub: Any) -> None:
        """Set the communication hub.

        Args:
            hub: Communication hub instance
        """
        self._communication_hub = hub

    async def _message_loop(self) -> None:
        """Background loop for processing messages."""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                await self._process_message(message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    async def _heartbeat_loop(self) -> None:
        """Background loop for sending heartbeats."""
        while self._running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.config.heartbeat_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}", exc_info=True)

    async def _health_check_loop(self) -> None:
        """Background loop for health checks."""
        while self._running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.agent_health_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error performing health check: {e}", exc_info=True)

    async def _send_heartbeat(self) -> None:
        """Send heartbeat message."""
        self._last_heartbeat = datetime.utcnow()

        message = HeartbeatMessage(
            sender_id=self.agent_id,
            payload={
                "state": self._state.name,
                "status": self._status.name,
                "active_tasks": len(self._active_tasks),
            }
        )

        await self.send_message(message)

    async def _perform_health_check(self) -> None:
        """Perform agent health check."""
        try:
            # Update resource metrics
            self._resource_metrics = self.metrics.get_resource_metrics()
            self._resource_metrics.active_tasks = len(self._active_tasks)

            # Check health
            is_healthy = await self._check_health()
            self._status = AgentStatus.HEALTHY if is_healthy else AgentStatus.DEGRADED

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            self._status = AgentStatus.UNHEALTHY

    def _update_state(self) -> None:
        """Update agent state based on active tasks."""
        if not self._running:
            return

        if len(self._active_tasks) == 0:
            self._state = AgentState.IDLE
        elif len(self._active_tasks) >= self._capabilities.max_concurrent_tasks:
            self._state = AgentState.BUSY
        else:
            self._state = AgentState.BUSY

    async def _process_message(self, message: Message) -> None:
        """Process incoming message.

        Args:
            message: Message to process
        """
        try:
            await self._on_message(message)
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    @abstractmethod
    async def _execute_task(self, task: Task) -> Any:
        """Execute task implementation (to be overridden by subclasses).

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        pass

    async def _on_start(self) -> None:
        """Called when agent starts (can be overridden by subclasses)."""
        pass

    async def _on_stop(self) -> None:
        """Called when agent stops (can be overridden by subclasses)."""
        pass

    async def _on_message(self, message: Message) -> None:
        """Called when message is received (can be overridden by subclasses).

        Args:
            message: Received message
        """
        pass

    async def _check_health(self) -> bool:
        """Check agent health (can be overridden by subclasses).

        Returns:
            True if agent is healthy
        """
        return True
