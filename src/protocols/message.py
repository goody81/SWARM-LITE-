"""Message protocol definitions for SWARM-LITE-."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from ..core.types import MessageType


@dataclass
class Message:
    """Base message class for all communication."""
    message_id: UUID = field(default_factory=uuid4)
    message_type: MessageType = MessageType.DIRECT
    sender_id: Optional[UUID] = None
    recipient_id: Optional[UUID] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[UUID] = None
    reply_to: Optional[UUID] = None
    ttl_seconds: Optional[int] = None
    priority: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": str(self.message_id),
            "message_type": self.message_type.name,
            "sender_id": str(self.sender_id) if self.sender_id else None,
            "recipient_id": str(self.recipient_id) if self.recipient_id else None,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "reply_to": str(self.reply_to) if self.reply_to else None,
            "ttl_seconds": self.ttl_seconds,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            message_id=UUID(data["message_id"]) if "message_id" in data else uuid4(),
            message_type=MessageType[data["message_type"]] if "message_type" in data else MessageType.DIRECT,
            sender_id=UUID(data["sender_id"]) if data.get("sender_id") else None,
            recipient_id=UUID(data["recipient_id"]) if data.get("recipient_id") else None,
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            payload=data.get("payload", {}),
            correlation_id=UUID(data["correlation_id"]) if data.get("correlation_id") else None,
            reply_to=UUID(data["reply_to"]) if data.get("reply_to") else None,
            ttl_seconds=data.get("ttl_seconds"),
            priority=data.get("priority", 5),
        )

    def is_expired(self) -> bool:
        """Check if message has expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        age = (datetime.utcnow() - self.timestamp).total_seconds()
        return age > self.ttl_seconds


@dataclass
class TaskRequestMessage(Message):
    """Message for task assignment requests."""
    message_type: MessageType = MessageType.TASK_REQUEST

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.TASK_REQUEST


@dataclass
class TaskResponseMessage(Message):
    """Message for task execution responses."""
    message_type: MessageType = MessageType.TASK_RESPONSE

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.TASK_RESPONSE


@dataclass
class TaskUpdateMessage(Message):
    """Message for task status updates."""
    message_type: MessageType = MessageType.TASK_UPDATE

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.TASK_UPDATE


@dataclass
class HeartbeatMessage(Message):
    """Heartbeat message for health checks."""
    message_type: MessageType = MessageType.HEARTBEAT

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.HEARTBEAT


@dataclass
class RegisterMessage(Message):
    """Message for agent registration."""
    message_type: MessageType = MessageType.REGISTER

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.REGISTER


@dataclass
class UnregisterMessage(Message):
    """Message for agent deregistration."""
    message_type: MessageType = MessageType.UNREGISTER

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.UNREGISTER


@dataclass
class StateUpdateMessage(Message):
    """Message for state updates."""
    message_type: MessageType = MessageType.STATE_UPDATE

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.STATE_UPDATE


@dataclass
class ErrorMessage(Message):
    """Message for error notifications."""
    message_type: MessageType = MessageType.ERROR

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.ERROR


@dataclass
class BroadcastMessage(Message):
    """Message for broadcasting to all agents."""
    message_type: MessageType = MessageType.BROADCAST

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.BROADCAST
        self.recipient_id = None  # Broadcasts have no specific recipient


@dataclass
class SystemEventMessage(Message):
    """Message for system events."""
    message_type: MessageType = MessageType.SYSTEM_EVENT

    def __post_init__(self):
        """Ensure message type is correct."""
        self.message_type = MessageType.SYSTEM_EVENT
