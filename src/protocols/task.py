"""Task protocol definitions for SWARM-LITE-."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from ..core.types import TaskInfo, TaskPriority, TaskRequirements, TaskState


@dataclass
class Task:
    """Task definition with execution context."""
    task_id: UUID = field(default_factory=uuid4)
    task_type: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    state: TaskState = TaskState.PENDING
    requirements: TaskRequirements = field(default_factory=TaskRequirements)
    payload: Dict[str, Any] = field(default_factory=dict)
    assigned_agent_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_info(self) -> TaskInfo:
        """Convert to TaskInfo."""
        return TaskInfo(
            task_id=self.task_id,
            task_type=self.task_type,
            priority=self.priority,
            state=self.state,
            requirements=self.requirements,
            assigned_agent_id=self.assigned_agent_id,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            result=self.result,
            error=self.error,
            metadata=self.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": str(self.task_id),
            "task_type": self.task_type,
            "priority": self.priority.name,
            "state": self.state.name,
            "requirements": self.requirements.to_dict(),
            "payload": self.payload,
            "assigned_agent_id": str(self.assigned_agent_id) if self.assigned_agent_id else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary."""
        return cls(
            task_id=UUID(data["task_id"]) if "task_id" in data else uuid4(),
            task_type=data.get("task_type", ""),
            priority=TaskPriority[data["priority"]] if "priority" in data else TaskPriority.NORMAL,
            state=TaskState[data["state"]] if "state" in data else TaskState.PENDING,
            requirements=TaskRequirements(**data["requirements"]) if "requirements" in data else TaskRequirements(),
            payload=data.get("payload", {}),
            assigned_agent_id=UUID(data["assigned_agent_id"]) if data.get("assigned_agent_id") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result=data.get("result"),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds"),
            metadata=data.get("metadata", {}),
        )

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.state == TaskState.FAILED

    def is_timeout(self) -> bool:
        """Check if task has timed out."""
        if self.timeout_seconds is None or self.started_at is None:
            return False
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        return elapsed > self.timeout_seconds

    def is_complete(self) -> bool:
        """Check if task is in a final state."""
        return self.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED, TaskState.TIMEOUT]


@dataclass
class TaskDependency:
    """Task dependency specification."""
    task_id: UUID
    dependent_task_id: UUID
    dependency_type: str = "blocking"  # blocking, soft, data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": str(self.task_id),
            "dependent_task_id": str(self.dependent_task_id),
            "dependency_type": self.dependency_type,
            "metadata": self.metadata,
        }


@dataclass
class TaskBatch:
    """Batch of related tasks."""
    batch_id: UUID = field(default_factory=uuid4)
    tasks: List[Task] = field(default_factory=list)
    dependencies: List[TaskDependency] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add task to batch."""
        self.tasks.append(task)

    def add_dependency(self, task_id: UUID, dependent_task_id: UUID, dependency_type: str = "blocking") -> None:
        """Add task dependency."""
        self.dependencies.append(
            TaskDependency(
                task_id=task_id,
                dependent_task_id=dependent_task_id,
                dependency_type=dependency_type,
            )
        )

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (no pending dependencies)."""
        completed_task_ids = {t.task_id for t in self.tasks if t.is_complete()}
        ready_tasks = []

        for task in self.tasks:
            if task.state != TaskState.PENDING:
                continue

            # Check if all dependencies are completed
            blocking_deps = [
                dep for dep in self.dependencies
                if dep.dependent_task_id == task.task_id and dep.dependency_type == "blocking"
            ]

            if all(dep.task_id in completed_task_ids for dep in blocking_deps):
                ready_tasks.append(task)

        return ready_tasks

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "batch_id": str(self.batch_id),
            "tasks": [t.to_dict() for t in self.tasks],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
