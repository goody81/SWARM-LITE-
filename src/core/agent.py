"""Agent module for SWARM-LITE system"""
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentCapabilities:
    """Agent capabilities specification"""
    compute: float
    memory: float
    tasks: List[str]


class Agent:
    """Agent in the SWARM-LITE system"""
    
    def __init__(self, agent_id: str, capabilities: AgentCapabilities):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.message_queue: Optional[asyncio.Queue] = None
        self._running = False
        self._task = None
        
    def set_message_queue(self, queue: asyncio.Queue):
        """Set the message queue for this agent"""
        self.message_queue = queue
        
    async def start(self):
        """Start the agent"""
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Agent {self.agent_id} started")
        
    async def stop(self):
        """Stop the agent"""
        self._running = False
        if self._task:
            await self._task
        logger.info(f"Agent {self.agent_id} stopped")
        
    async def _run(self):
        """Agent main loop"""
        while self._running:
            try:
                if self.message_queue:
                    try:
                        message = await asyncio.wait_for(
                            self.message_queue.get(),
                            timeout=1.0
                        )
                        await self._process_message(message)
                    except asyncio.TimeoutError:
                        pass
                else:
                    await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Error in agent {self.agent_id}: {e}")
                
    async def _process_message(self, message):
        """Process incoming message"""
        # Basic message processing
        logger.debug(f"Agent {self.agent_id} processing message: {message}")
