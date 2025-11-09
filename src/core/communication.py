"""Communication hub implementation for SWARM-LITE-."""

import asyncio
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Callable, DefaultDict, Deque, Dict, List, Optional, Set
from uuid import UUID

from ..protocols.message import Message, MessageType
from .types import AgentInfo, SystemEvent
from ..utils.config import get_config
from ..utils.logging import get_logger
from ..utils.metrics import get_metrics_collector

logger = get_logger("communication")


class CommunicationHub:
    """Central communication hub for agent message routing."""

    def __init__(self):
        """Initialize communication hub."""
        self.config = get_config()
        self.metrics = get_metrics_collector()

        # Agent registry
        self._agents: Dict[UUID, Any] = {}  # agent_id -> agent instance
        self._agent_info: Dict[UUID, AgentInfo] = {}

        # Message routing
        self._message_queues: DefaultDict[UUID, Deque[Message]] = defaultdict(
            lambda: deque(maxlen=self.config.message_queue_max_size)
        )

        # Pub/sub system
        self._subscribers: DefaultDict[str, Set[UUID]] = defaultdict(set)
        self._topic_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Backpressure management
        self._backpressure_threshold = self.config.max_backpressure_size

        # Connection state
        self._running = False
        self._routing_task: Optional[asyncio.Task] = None

        logger.info("Communication hub initialized")

    async def start(self) -> None:
        """Start the communication hub."""
        if self._running:
            logger.warning("Communication hub already running")
            return

        logger.info("Starting communication hub")
        self._running = True

        # Start message routing loop
        self._routing_task = asyncio.create_task(self._routing_loop())

        logger.info("Communication hub started")

    async def stop(self) -> None:
        """Stop the communication hub."""
        if not self._running:
            return

        logger.info("Stopping communication hub")
        self._running = False

        # Cancel routing task
        if self._routing_task:
            self._routing_task.cancel()
            try:
                await self._routing_task
            except asyncio.CancelledError:
                pass

        logger.info("Communication hub stopped")

    async def register_agent(self, agent: Any) -> None:
        """Register an agent with the hub.

        Args:
            agent: Agent instance to register
        """
        agent_id = agent.agent_id

        if agent_id in self._agents:
            logger.warning(f"Agent already registered", agent_id=str(agent_id))
            return

        self._agents[agent_id] = agent
        self._agent_info[agent_id] = agent.info
        agent.set_communication_hub(self)

        self.metrics.record_counter("swarm.agents.registered")
        self.metrics.record_gauge("swarm.agents.active", len(self._agents))

        logger.info(f"Agent registered", agent_id=str(agent_id), name=agent.name)

        # Notify subscribers
        await self._publish_system_event(SystemEvent.AGENT_REGISTERED, {
            "agent_id": str(agent_id),
            "name": agent.name,
        })

    async def unregister_agent(self, agent_id: UUID) -> None:
        """Unregister an agent from the hub.

        Args:
            agent_id: Agent identifier
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent not registered", agent_id=str(agent_id))
            return

        agent = self._agents.pop(agent_id)
        self._agent_info.pop(agent_id, None)
        self._message_queues.pop(agent_id, None)

        # Remove from all subscriptions
        for subscribers in self._subscribers.values():
            subscribers.discard(agent_id)

        self.metrics.record_counter("swarm.agents.unregistered")
        self.metrics.record_gauge("swarm.agents.active", len(self._agents))

        logger.info(f"Agent unregistered", agent_id=str(agent_id))

        # Notify subscribers
        await self._publish_system_event(SystemEvent.AGENT_UNREGISTERED, {
            "agent_id": str(agent_id),
        })

    async def send_message(self, message: Message) -> bool:
        """Send a message through the hub.

        Args:
            message: Message to send

        Returns:
            True if message was queued successfully
        """
        if not self._running:
            logger.warning("Communication hub not running")
            return False

        # Check if message is expired
        if message.is_expired():
            logger.warning(f"Message expired", message_id=str(message.message_id))
            self.metrics.record_counter("swarm.messages.expired")
            return False

        # Route based on message type
        if message.message_type == MessageType.BROADCAST:
            return await self._broadcast_message(message)
        elif message.recipient_id:
            return await self._route_direct_message(message)
        else:
            logger.warning(f"Message has no recipient", message_id=str(message.message_id))
            return False

    async def _route_direct_message(self, message: Message) -> bool:
        """Route a direct message to recipient.

        Args:
            message: Message to route

        Returns:
            True if message was queued
        """
        recipient_id = message.recipient_id
        if recipient_id not in self._agents:
            logger.warning(f"Recipient not found", recipient_id=str(recipient_id))
            self.metrics.record_counter("swarm.messages.undeliverable")
            return False

        # Check backpressure
        queue = self._message_queues[recipient_id]
        if len(queue) >= self._backpressure_threshold:
            logger.warning(f"Backpressure threshold reached", recipient_id=str(recipient_id))
            self.metrics.record_counter("swarm.messages.backpressure")
            return False

        # Add to queue
        queue.append(message)
        self.metrics.record_counter("swarm.messages.queued")
        self.metrics.record_gauge("swarm.messages.queue_size", sum(len(q) for q in self._message_queues.values()))

        return True

    async def _broadcast_message(self, message: Message) -> bool:
        """Broadcast message to all agents.

        Args:
            message: Message to broadcast

        Returns:
            True if message was queued to at least one agent
        """
        success_count = 0

        for agent_id in self._agents.keys():
            msg_copy = Message(
                message_type=message.message_type,
                sender_id=message.sender_id,
                recipient_id=agent_id,
                payload=message.payload.copy(),
                correlation_id=message.correlation_id,
                ttl_seconds=message.ttl_seconds,
                priority=message.priority,
            )

            if await self._route_direct_message(msg_copy):
                success_count += 1

        self.metrics.record_counter("swarm.messages.broadcast")
        logger.debug(f"Broadcast message to {success_count} agents")

        return success_count > 0

    async def _routing_loop(self) -> None:
        """Background loop for routing queued messages."""
        while self._running:
            try:
                await self._deliver_queued_messages()
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in routing loop: {e}", exc_info=True)

    async def _deliver_queued_messages(self) -> None:
        """Deliver queued messages to agents."""
        for agent_id, queue in list(self._message_queues.items()):
            if not queue:
                continue

            agent = self._agents.get(agent_id)
            if not agent:
                continue

            # Deliver messages
            while queue:
                message = queue.popleft()

                try:
                    await agent.handle_message(message)
                    self.metrics.record_counter("swarm.messages.delivered")
                except Exception as e:
                    logger.error(f"Error delivering message: {e}", message_id=str(message.message_id), exc_info=True)
                    self.metrics.record_counter("swarm.messages.delivery_failed")

        # Update queue size metric
        self.metrics.record_gauge("swarm.messages.queue_size", sum(len(q) for q in self._message_queues.values()))

    async def subscribe(self, topic: str, agent_id: UUID) -> None:
        """Subscribe an agent to a topic.

        Args:
            topic: Topic name
            agent_id: Agent identifier
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent not registered", agent_id=str(agent_id))
            return

        self._subscribers[topic].add(agent_id)
        logger.info(f"Agent subscribed to topic", agent_id=str(agent_id), topic=topic)

    async def unsubscribe(self, topic: str, agent_id: UUID) -> None:
        """Unsubscribe an agent from a topic.

        Args:
            topic: Topic name
            agent_id: Agent identifier
        """
        self._subscribers[topic].discard(agent_id)
        logger.info(f"Agent unsubscribed from topic", agent_id=str(agent_id), topic=topic)

    async def publish(self, topic: str, payload: Dict[str, Any], sender_id: Optional[UUID] = None) -> None:
        """Publish a message to a topic.

        Args:
            topic: Topic name
            payload: Message payload
            sender_id: Optional sender identifier
        """
        subscribers = self._subscribers.get(topic, set())

        if not subscribers:
            logger.debug(f"No subscribers for topic", topic=topic)
            return

        # Create and send messages to subscribers
        for agent_id in subscribers:
            message = Message(
                message_type=MessageType.BROADCAST,
                sender_id=sender_id,
                recipient_id=agent_id,
                payload={"topic": topic, "data": payload},
            )
            await self.send_message(message)

        self.metrics.record_counter("swarm.messages.published")
        logger.debug(f"Published to topic", topic=topic, subscribers=len(subscribers))

    async def _publish_system_event(self, event: SystemEvent, payload: Dict[str, Any]) -> None:
        """Publish a system event.

        Args:
            event: System event type
            payload: Event payload
        """
        await self.publish(f"system.events.{event.name.lower()}", payload)

    def get_agent_info(self, agent_id: UUID) -> Optional[AgentInfo]:
        """Get agent information.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent information or None
        """
        agent = self._agents.get(agent_id)
        if agent:
            return agent.info
        return None

    def get_all_agents(self) -> List[AgentInfo]:
        """Get information for all registered agents.

        Returns:
            List of agent information
        """
        return [agent.info for agent in self._agents.values()]

    def get_queue_size(self, agent_id: UUID) -> int:
        """Get message queue size for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Queue size
        """
        return len(self._message_queues.get(agent_id, deque()))

    def get_total_queue_size(self) -> int:
        """Get total message queue size across all agents.

        Returns:
            Total queue size
        """
        return sum(len(q) for q in self._message_queues.values())

    def is_healthy(self) -> bool:
        """Check if communication hub is healthy.

        Returns:
            True if healthy
        """
        if not self._running:
            return False

        # Check for excessive backpressure
        total_queue_size = self.get_total_queue_size()
        if total_queue_size > self._backpressure_threshold * len(self._agents):
            return False

        return True
