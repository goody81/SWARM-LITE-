"""Communication module for SWARM-LITE system"""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message types"""
    TASK = "task"
    STATUS = "status"
    RESULT = "result"
    ERROR = "error"


class MessagePriority(Enum):
    """Message priorities"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Message:
    """Message structure"""
    sender: str
    receiver: str
    type: MessageType
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None


class CommunicationHub:
    """Central communication hub for agent coordination"""
    
    def __init__(self):
        self.agent_queues: Dict[str, asyncio.Queue] = {}
        self._running = False
        
    async def start(self):
        """Start the communication hub"""
        self._running = True
        logger.info("CommunicationHub started")
        
    async def stop(self):
        """Stop the communication hub"""
        self._running = False
        logger.info("CommunicationHub stopped")
        
    async def register_agent(self, agent_id: str) -> asyncio.Queue:
        """Register an agent and create its message queue"""
        queue = asyncio.Queue()
        self.agent_queues[agent_id] = queue
        logger.info(f"Agent {agent_id} registered with CommunicationHub")
        return queue
        
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agent_queues:
            del self.agent_queues[agent_id]
            logger.info(f"Agent {agent_id} unregistered from CommunicationHub")
            
    async def send_message(self, message: Message) -> bool:
        """Send a message to an agent"""
        if message.receiver not in self.agent_queues:
            logger.error(f"Receiver {message.receiver} not found")
            return False
            
        try:
            await self.agent_queues[message.receiver].put(message)
            logger.debug(f"Message sent from {message.sender} to {message.receiver}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    async def broadcast(self, message: Message):
        """Broadcast a message to all agents"""
        for agent_id in self.agent_queues:
            if agent_id != message.sender:
                msg = Message(
                    sender=message.sender,
                    receiver=agent_id,
                    type=message.type,
                    payload=message.payload,
                    priority=message.priority,
                    correlation_id=message.correlation_id
                )
                await self.send_message(msg)
