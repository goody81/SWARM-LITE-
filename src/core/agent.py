import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from .types import AgentStatus, AgentCapabilities, AgentMetrics, Message

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, agent_id: str, capabilities: AgentCapabilities):
        self.id = agent_id
        self.capabilities = capabilities
        self.status = AgentStatus.INITIALIZING
        self.metrics = AgentMetrics()
        self._message_queue = asyncio.Queue()
        self._task_queue = asyncio.Queue()
        self._last_heartbeat = datetime.now(timezone.utc)
        
    async def start(self):
        """Start the agent's main processing loops"""
        self.status = AgentStatus.READY
        await asyncio.gather(
            self._process_messages(),
            self._process_tasks(),
            self._update_metrics()
        )
    
    async def _process_messages(self):
        """Process incoming messages"""
        while True:
            msg = await self._message_queue.get()
            try:
                await self._handle_message(msg)
            except Exception as e:
                logger.error(f"Error processing message {msg.id}: {e}")
            finally:
                self._message_queue.task_done()
    
    async def _process_tasks(self):
        """Process assigned tasks"""
        while True:
            task = await self._task_queue.get()
            try:
                self.status = AgentStatus.BUSY
                await self._execute_task(task)
            except Exception as e:
                logger.error(f"Error executing task {task.id}: {e}")
                self.status = AgentStatus.ERROR
            else:
                self.status = AgentStatus.READY
            finally:
                self._task_queue.task_done()
    
    async def _update_metrics(self):
        """Update agent metrics periodically"""
        while True:
            self.metrics.last_update = datetime.now(timezone.utc)
            # Update CPU and memory metrics
            self.metrics.cpu_usage = await self._get_cpu_usage()
            self.metrics.memory_usage = await self._get_memory_usage()
            await asyncio.sleep(1)  # Update every second
    
    async def _handle_message(self, msg: Message):
        """Handle a received message"""
        logger.info(f"Agent {self.id} handling message {msg.id} from {msg.sender}")
        # Default message handling implementation
        # Override this method in subclasses for custom behavior
        pass
    
    async def _execute_task(self, task):
        """Execute a task"""
        logger.info(f"Agent {self.id} executing task {task.id}")
        # Default task execution implementation
        # Override this method in subclasses for custom behavior
        self.metrics.task_count += 1
        await asyncio.sleep(0.1)  # Simulate task execution
    
    async def _get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        # Placeholder implementation - can be replaced with actual CPU monitoring
        return 0.0
    
    async def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        # Placeholder implementation - can be replaced with actual memory monitoring
        return 0.0
