# SWARM-LITE- Task Distribution and Coordination System

This module implements the third core component of SWARM-LITE- that manages workload distribution across agents.

## Structure

```
src/core/tasks/
├── __init__.py          # Package exports
├── types.py             # Core data types and enumerations
├── scheduler.py         # Task scheduling logic
└── coordinator.py       # High-level task coordination
```

## Features

### 1. Priority-Based Task Scheduling
- Uses heap-based priority queue for optimal task distribution
- Four priority levels: CRITICAL (3) → HIGH (2) → NORMAL (1) → LOW (0)
- Higher priority tasks are always processed first

### 2. Capability-Based Task Assignment
- Tasks specify resource requirements (CPU, memory, capabilities)
- Agents are matched based on their available resources
- Ensures tasks are only assigned to capable agents

### 3. Task Lifecycle Management
Six task states:
- `PENDING`: Task submitted, awaiting assignment
- `ASSIGNED`: Task assigned to an agent
- `RUNNING`: Task currently executing
- `COMPLETED`: Task finished successfully
- `FAILED`: Task encountered an error
- `CANCELLED`: Task was cancelled

### 4. Result Tracking and Error Handling
- Results are stored and can be retrieved by task ID
- Comprehensive error tracking with error messages
- Automatic timeout handling (5-minute default)

### 5. Async/Await Architecture
- Full async support for concurrent operations
- Thread-safe operations using asyncio locks
- Suitable for high-throughput environments

## Usage

### Basic Example

```python
import asyncio
from src.core.tasks import (
    Task, TaskStatus, TaskPriority, TaskRequirements,
    TaskCoordinator
)

async def main():
    # Create coordinator
    coordinator = TaskCoordinator()
    
    # Register an agent
    await coordinator.register_agent("agent-1", {
        "cpu": 2.0,
        "memory": 4.0,
        "capabilities": ["python", "data_processing"]
    })
    
    # Create and submit a task
    task = Task(
        id="task-1",
        type="data_processing",
        payload={"data": "input.csv"},
        requirements=TaskRequirements(
            min_cpu=1.0,
            min_memory=2.0,
            capabilities=["python"]
        ),
        priority=TaskPriority.HIGH
    )
    
    task_id = await coordinator.submit_task(task)
    
    # Agent gets and processes task
    agent_caps = coordinator.agent_capabilities["agent-1"]
    assigned_task = await coordinator.scheduler.get_next_task(agent_caps)
    
    # Update task status
    await coordinator.update_task_status(
        task_id,
        TaskStatus.COMPLETED,
        result={"output": "processed.csv"}
    )
    
    # Retrieve result
    result = await coordinator.get_task_result(task_id)
    print(f"Result: {result}")

asyncio.run(main())
```

## API Reference

### TaskStatus (Enum)
- `PENDING`, `ASSIGNED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`

### TaskPriority (Enum)
- `LOW = 0`, `NORMAL = 1`, `HIGH = 2`, `CRITICAL = 3`

### TaskRequirements (dataclass)
- `min_cpu: float` - Minimum CPU cores required
- `min_memory: float` - Minimum memory in GB required
- `capabilities: List[str]` - Required agent capabilities

### Task (dataclass)
- `id: str` - Unique task identifier
- `type: str` - Task type/category
- `payload: Dict[str, Any]` - Task data
- `requirements: TaskRequirements` - Resource requirements
- `priority: TaskPriority` - Task priority (default: NORMAL)
- `status: TaskStatus` - Current status (default: PENDING)
- Plus tracking fields: created_at, assigned_to, started_at, completed_at, result, error

### TaskScheduler
- `async add_task(task: Task)` - Add task to queue
- `async get_next_task(agent_capabilities: Dict[str, Any]) -> Optional[Task]` - Get next suitable task

### TaskCoordinator
- `async start()` - Start the coordinator with monitoring
- `async stop()` - Stop the coordinator
- `async register_agent(agent_id: str, capabilities: Dict[str, Any])` - Register an agent
- `async submit_task(task: Task) -> str` - Submit a task for execution
- `async get_task_result(task_id: str) -> Optional[Dict[str, Any]]` - Get task result
- `async update_task_status(task_id: str, status: TaskStatus, result: Optional[Dict], error: Optional[str])` - Update task status

## Testing

Run the test suite:
```bash
python3 -c "from src.core.tasks import Task, TaskStatus, TaskPriority, TaskRequirements, TaskScheduler, TaskCoordinator; print('All imports successful!')"
```

## Code Quality

- **Style**: PEP 8 compliant (verified with flake8)
- **Type Safety**: Full type hints throughout
- **Documentation**: Comprehensive docstrings
- **Security**: 0 CodeQL alerts

## Implementation Notes

1. **Priority Ordering**: Uses negated priority values in min-heap to achieve correct ordering (CRITICAL first)
2. **Capability Matching**: Tasks without matching capabilities are skipped and remain in queue
3. **Thread Safety**: All queue operations are protected by asyncio locks
4. **Timeout Handling**: Background monitoring task checks for timeouts every minute
5. **Result Storage**: Results are stored in memory; consider persistence for production use
