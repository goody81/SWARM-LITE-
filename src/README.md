# SWARM-LITE- Foundational Core

This directory contains the foundational core implementation of SWARM-LITE-, a lightweight multi-agent system.

## Structure

```
src/
├── __init__.py          # Package initialization
├── config.py            # System configuration management
└── core/
    ├── __init__.py      # Core package initialization
    ├── types.py         # Core data types and enums
    └── agent.py         # Agent implementation
```

## Components

### config.py
Configuration management with environment variable support. Default values can be overridden using `SWARM_LITE_*` environment variables.

**Example:**
```python
from src.config import Config

heartbeat = Config.get('AGENT_HEARTBEAT_INTERVAL')  # Returns 5 (default)
# Override with: export SWARM_LITE_AGENT_HEARTBEAT_INTERVAL=10
```

### core/types.py
Core data types for the agent system:

- **AgentStatus**: Enum with states (INITIALIZING, READY, BUSY, WAITING, ERROR, SHUTDOWN)
- **AgentCapabilities**: Agent resource specifications (compute, memory, supported tasks)
- **AgentMetrics**: Performance metrics (CPU, memory usage, task count)
- **Message**: Inter-agent communication structure

**Example:**
```python
from src.core.types import AgentCapabilities, Message

caps = AgentCapabilities(compute=2.0, memory=8.0, tasks=["process", "analyze"])
msg = Message(id="m1", type="task", sender="a1", receiver="a2", payload={"data": "test"})
```

### core/agent.py
Agent implementation with async processing capabilities:

- Message queue processing
- Task queue processing
- Periodic metrics updates
- Extensible handlers for custom behavior

**Example:**
```python
from src.core.agent import Agent
from src.core.types import AgentCapabilities
import asyncio

caps = AgentCapabilities(compute=1.0, memory=2.0, tasks=["compute"])
agent = Agent("worker_1", caps)

# For custom behavior, subclass Agent and override methods:
# - _handle_message(msg): Custom message handling
# - _execute_task(task): Custom task execution
# - _get_cpu_usage(): Custom CPU monitoring
# - _get_memory_usage(): Custom memory monitoring
```

## Features

✓ **Async Processing**: Built on asyncio for efficient concurrent operations  
✓ **Type Safety**: Full type hints throughout the codebase  
✓ **Extensibility**: Easy to extend through method overriding  
✓ **Configuration**: Environment-aware configuration system  
✓ **Metrics**: Built-in performance monitoring  
✓ **Clean Design**: Separation of concerns with modular structure

## Usage

All modules can be imported from the src package:

```python
from src.config import Config
from src.core.types import AgentStatus, AgentCapabilities, AgentMetrics, Message
from src.core.agent import Agent
```

## Testing

The implementation has been tested with:
- Syntax validation
- Import verification
- Unit tests for all components
- Integration tests for multi-agent scenarios
- Security scanning (CodeQL)

All tests pass successfully.
