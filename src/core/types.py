from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

class AgentStatus(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    SHUTDOWN = "shutdown"

@dataclass
class AgentCapabilities:
    compute: float = 1.0  # Relative compute power
    memory: float = 1.0   # Available memory in GB
    tasks: List[str] = field(default_factory=list)  # Supported task types
    
@dataclass
class AgentMetrics:
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    task_count: int = 0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
@dataclass
class Message:
    id: str
    type: str
    sender: str
    receiver: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: int = 1
