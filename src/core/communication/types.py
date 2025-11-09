from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    HEARTBEAT = "heartbeat"
    CONTROL = "control"
    ERROR = "error"

@dataclass
class Message:
    id: str
    type: MessageType
    sender: str
    receiver: Optional[str]
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: int = 300  # Time to live in seconds
    topic: Optional[str] = None  # For pub/sub messages
