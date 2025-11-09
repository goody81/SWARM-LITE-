"""Core data types and enums for SWARM-LITE-."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class AgentState(Enum):
    """Agent lifecycle states."""
    INITIALIZING = auto()
    IDLE = auto()
    BUSY = auto()
    WAITING = auto()
    ERROR = auto()
    SHUTTING_DOWN = auto()
    OFFLINE = auto()


class AgentStatus(Enum):
    """Agent health and operational status."""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()


class MessageType(Enum):
    """Types of messages in the system."""
    TASK_REQUEST = auto()
    TASK_RESPONSE = auto()
    TASK_UPDATE = auto()
    HEARTBEAT = auto()
    REGISTER = auto()
    UNREGISTER = auto()
    STATE_UPDATE = auto()
    ERROR = auto()
    BROADCAST = auto()
    DIRECT = auto()
    SYSTEM_EVENT = auto()


class TaskState(Enum):
    """Task lifecycle states."""
    PENDING = auto()
    QUEUED = auto()
    ASSIGNED = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    TIMEOUT = auto()


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class SystemEvent(Enum):
    """System-level events."""
    AGENT_REGISTERED = auto()
    AGENT_UNREGISTERED = auto()
    AGENT_FAILED = auto()
    TASK_CREATED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    SYSTEM_OVERLOAD = auto()
    SYSTEM_RECOVERY = auto()


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    message_queue_size: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "memory_percent": self.memory_percent,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "message_queue_size": self.message_queue_size,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentCapabilities:
    """Agent capabilities and constraints."""
    agent_id: UUID
    agent_type: str
    max_concurrent_tasks: int = 5
    supported_task_types: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    custom_capabilities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": str(self.agent_id),
            "agent_type": self.agent_type,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "supported_task_types": self.supported_task_types,
            "resource_limits": self.resource_limits,
            "custom_capabilities": self.custom_capabilities,
        }


@dataclass
class AgentInfo:
    """Complete agent information."""
    agent_id: UUID
    name: str
    state: AgentState
    status: AgentStatus
    capabilities: AgentCapabilities
    metrics: ResourceMetrics
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": str(self.agent_id),
            "name": self.name,
            "state": self.state.name,
            "status": self.status.name,
            "capabilities": self.capabilities.to_dict(),
            "metrics": self.metrics.to_dict(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class TaskRequirements:
    """Task resource and capability requirements."""
    required_capabilities: List[str] = field(default_factory=list)
    min_memory_mb: float = 0.0
    min_cpu_percent: float = 0.0
    estimated_duration_seconds: Optional[float] = None
    dependencies: List[UUID] = field(default_factory=list)
    custom_requirements: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "required_capabilities": self.required_capabilities,
            "min_memory_mb": self.min_memory_mb,
            "min_cpu_percent": self.min_cpu_percent,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "dependencies": [str(d) for d in self.dependencies],
            "custom_requirements": self.custom_requirements,
        }


@dataclass
class TaskInfo:
    """Complete task information."""
    task_id: UUID = field(default_factory=uuid4)
    task_type: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.PENDING
    requirements: TaskRequirements = field(default_factory=TaskRequirements)
    assigned_agent_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": str(self.task_id),
            "task_type": self.task_type,
            "priority": self.priority.name,
            "state": self.state.name,
            "requirements": self.requirements.to_dict(),
            "assigned_agent_id": str(self.assigned_agent_id) if self.assigned_agent_id else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }
