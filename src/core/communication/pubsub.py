import asyncio
from typing import Dict, Set, Optional
from .types import Message
import logging

logger = logging.getLogger(__name__)

class PubSubSystem:
    def __init__(self):
        self.subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        
    async def subscribe(self, topic: str) -> asyncio.Queue:
        """Subscribe to a topic and get a message queue"""
        queue = asyncio.Queue()
        async with self._lock:
            if topic not in self.subscribers:
                self.subscribers[topic] = set()
            self.subscribers[topic].add(queue)
        logger.info(f"New subscription to topic {topic}")
        return queue
        
    async def unsubscribe(self, topic: str, queue: asyncio.Queue):
        """Unsubscribe from a topic"""
        async with self._lock:
            if topic in self.subscribers:
                self.subscribers[topic].discard(queue)
                if not self.subscribers[topic]:
                    del self.subscribers[topic]
        
    async def publish(self, topic: str, message: Message):
        """Publish a message to all topic subscribers"""
        if topic in self.subscribers:
            for queue in self.subscribers[topic]:
                try:
                    await queue.put(message)
                except Exception as e:
                    logger.error(f"Failed to publish to subscriber: {e}")
