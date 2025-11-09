import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Set
from .types import Message, MessagePriority, MessageType
from .pubsub import PubSubSystem
import logging

logger = logging.getLogger(__name__)

class CommunicationHub:
    def __init__(self):
        self.agent_queues: Dict[str, asyncio.Queue] = {}
        self.pubsub = PubSubSystem()
        self.message_history: Dict[str, Message] = {}
        self.active_agents: Set[str] = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the communication hub"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Communication hub started")
        
    async def stop(self):
        """Stop the communication hub"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("Communication hub stopped")
        
    async def register_agent(self, agent_id: str) -> asyncio.Queue:
        """Register an agent and get its message queue"""
        queue = asyncio.Queue()
        self.agent_queues[agent_id] = queue
        self.active_agents.add(agent_id)
        logger.info(f"Agent {agent_id} registered")
        return queue
        
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agent_queues:
            del self.agent_queues[agent_id]
        self.active_agents.discard(agent_id)
        logger.info(f"Agent {agent_id} unregistered")
        
    async def send_message(self, message: Message) -> bool:
        """Send a message to a specific agent"""
        if message.receiver and message.receiver in self.agent_queues:
            try:
                await self.agent_queues[message.receiver].put(message)
                self.message_history[message.id] = message
                logger.info(f"Message {message.id} sent to {message.receiver}")
                return True
            except Exception as e:
                logger.error(f"Failed to send message {message.id}: {e}")
        return False
        
    async def broadcast(self, message: Message):
        """Broadcast a message to all active agents"""
        for agent_id in self.active_agents:
            message_copy = Message(
                id=str(uuid.uuid4()),
                type=message.type,
                sender=message.sender,
                receiver=agent_id,
                payload=message.payload,
                priority=message.priority
            )
            await self.send_message(message_copy)
            
    async def subscribe_to_topic(self, agent_id: str, topic: str) -> asyncio.Queue:
        """Subscribe an agent to a topic"""
        return await self.pubsub.subscribe(topic)
        
    async def publish_to_topic(self, topic: str, message: Message):
        """Publish a message to a topic"""
        await self.pubsub.publish(topic, message)
        
    async def _cleanup_loop(self):
        """Clean up expired messages and inactive agents"""
        while True:
            current_time = datetime.now(timezone.utc)
            # Clean up expired messages
            expired_messages = [
                msg_id for msg_id, msg in self.message_history.items()
                if (current_time - msg.created_at).total_seconds() > msg.ttl
            ]
            for msg_id in expired_messages:
                del self.message_history[msg_id]
                
            # Check for inactive agents
            for agent_id in list(self.active_agents):
                if agent_id not in self.agent_queues:
                    self.active_agents.discard(agent_id)
                    
            await asyncio.sleep(60)  # Run cleanup every minute
