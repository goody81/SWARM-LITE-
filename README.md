# SWARM-LITE- Core Implementation

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A lightweight implementation of a multi-agent communication and coordination framework.

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🏗️ Architecture

The system consists of three main components:

### Core Components

#### 1. AsyncAgent (`src/core/agent.py`)
Base class for asynchronous agents with:
- Async task execution with timeout support
- State management (7 lifecycle states)
- Resource monitoring and metrics
- Message handling and queuing
- Automatic health checks
- Heartbeat system

**Usage:**
```python
from src.core import AsyncAgent
from src.protocols import Task

class MyAgent(AsyncAgent):
    def __init__(self):
        super().__init__(
            name="my-agent",
            agent_type="worker",
            supported_task_types=["process", "analyze"]
        )
    
    async def _execute_task(self, task: Task):
        # Implement your task logic
        return {"result": "success"}
```

#### 2. CommunicationHub (`src/core/communication.py`)
Central message routing system with:
- Async message routing
- Agent registration/deregistration
- Message queuing with backpressure control
- Pub/sub system for topics
- Connection state management

**Features:**
- Direct messaging between agents
- Broadcast messaging to all agents
- Topic-based pub/sub
- Automatic message expiration (TTL)
- Queue size monitoring and backpressure

#### 3. TaskCoordinator (`src/core/coordinator.py`)
Task distribution and coordination with:
- Priority-based task queuing
- Load balancing strategies (least_loaded, round_robin)
- Agent capability matching
- Automatic failure recovery
- Task retry mechanism
- Dependency management via TaskBatch

**Load Balancing:**
- Matches tasks to agents based on capabilities
- Distributes load across available agents
- Handles agent failures gracefully
- Retries failed tasks automatically

## 🔧 Configuration

Configuration is managed through environment variables or a config file:

```python
from src.utils import SwarmConfig, set_config

# From environment
config = SwarmConfig.from_env()

# From file
config = SwarmConfig.from_file("config.json")

# Programmatically
config = SwarmConfig(
    agent_max_concurrent_tasks=10,
    task_default_timeout_seconds=300,
    log_level="DEBUG"
)
set_config(config)
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `SWARM_SYSTEM_NAME` | SWARM-LITE | System name |
| `SWARM_ENVIRONMENT` | development | Environment (development/staging/production) |
| `SWARM_LOG_LEVEL` | INFO | Logging level |
| `SWARM_AGENT_MAX_CONCURRENT_TASKS` | 5 | Max tasks per agent |
| `SWARM_TASK_DEFAULT_TIMEOUT_SECONDS` | 600 | Default task timeout |
| `SWARM_MESSAGE_QUEUE_MAX_SIZE` | 1000 | Max message queue size |

## 📊 Monitoring

### Logging

Structured logging with JSON format:

```python
from src.utils import setup_logging, get_logger

# Setup logging
logger = setup_logging(
    log_level="INFO",
    log_format="json",
    log_file="swarm.log"
)

# Use logger
logger = get_logger("my-component")
logger.info("Task completed", task_id="123", duration=1.5)
```

### Metrics

Built-in metrics collection:

```python
from src.utils import get_metrics_collector

metrics = get_metrics_collector()
await metrics.start()

# Metrics are automatically collected:
# - System CPU and memory
# - Task completion rates
# - Message queue sizes
# - Agent states

# Get current metrics
resource_metrics = metrics.get_resource_metrics()
print(f"CPU: {resource_metrics.cpu_percent}%")
print(f"Active tasks: {resource_metrics.active_tasks}")
```

## 📝 Data Types

### Agent States
- `INITIALIZING`: Agent is starting up
- `IDLE`: Agent is ready for tasks
- `BUSY`: Agent is executing tasks
- `WAITING`: Agent is waiting for resources
- `ERROR`: Agent encountered an error
- `SHUTTING_DOWN`: Agent is stopping
- `OFFLINE`: Agent is not running

### Task States
- `PENDING`: Task created but not queued
- `QUEUED`: Task in coordinator queue
- `ASSIGNED`: Task assigned to agent
- `RUNNING`: Task being executed
- `PAUSED`: Task temporarily paused
- `COMPLETED`: Task finished successfully
- `FAILED`: Task failed with error
- `CANCELLED`: Task was cancelled
- `TIMEOUT`: Task exceeded timeout

### Task Priorities
- `CRITICAL` (0): Highest priority
- `HIGH` (1)
- `NORMAL` (2): Default
- `LOW` (3)
- `BACKGROUND` (4): Lowest priority

## 🚀 Quick Start

```python
import asyncio
from src.core import AsyncAgent, CommunicationHub, TaskCoordinator
from src.protocols import Task
from src.core.types import TaskPriority

# Define your agent
class WorkerAgent(AsyncAgent):
    def __init__(self, name):
        super().__init__(
            name=name,
            agent_type="worker",
            supported_task_types=["compute"]
        )
    
    async def _execute_task(self, task: Task):
        # Your task logic here
        return f"Processed by {self.name}"

async def main():
    # Create system components
    hub = CommunicationHub()
    coordinator = TaskCoordinator(hub)
    
    # Start components
    await hub.start()
    await coordinator.start()
    
    # Create and start agents
    agent1 = WorkerAgent("worker-1")
    agent2 = WorkerAgent("worker-2")
    
    await hub.register_agent(agent1)
    await hub.register_agent(agent2)
    
    await agent1.start()
    await agent2.start()
    
    # Submit tasks
    for i in range(5):
        task = Task(
            task_type="compute",
            priority=TaskPriority.NORMAL,
            payload={"data": i}
        )
        await coordinator.submit_task(task)
    
    # Wait for completion
    await asyncio.sleep(2)
    
    # Get statistics
    stats = coordinator.get_statistics()
    print(f"Completed: {stats['completed_tasks']}/{stats['total_tasks']}")
    
    # Cleanup
    await agent1.stop()
    await agent2.stop()
    await coordinator.stop()
    await hub.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Testing

Run the basic test:

```bash
python3 -c "import sys; sys.path.insert(0, '.'); import src; print(f'Version: {src.__version__}')"
```

## 📋 Requirements

- Python 3.8+
- psutil >= 5.9.0

## 🔍 Key Features

- ✅ **Async/await throughout**: Full async support for scalability
- ✅ **Type hints**: Complete type annotations for better IDE support
- ✅ **Structured logging**: JSON logging with context
- ✅ **Metrics collection**: Built-in performance monitoring
- ✅ **Error handling**: Comprehensive error handling and recovery
- ✅ **Backpressure control**: Prevents message queue overflows
- ✅ **Task retry**: Automatic retry on failure
- ✅ **Health checks**: Automatic agent health monitoring
- ✅ **Configuration**: Environment-based configuration
- ✅ **Pub/sub**: Topic-based messaging

## 📚 API Reference

See individual module documentation:
- [Core Types](src/core/types.py) - Data structures and enums
- [Agent](src/core/agent.py) - AsyncAgent base class
- [Communication](src/core/communication.py) - CommunicationHub
- [Coordinator](src/core/coordinator.py) - TaskCoordinator
- [Messages](src/protocols/message.py) - Message protocols
- [Tasks](src/protocols/task.py) - Task protocols

## 🤝 Contributing

This is a core implementation designed for extension. To extend:

1. Create custom agent types by subclassing `AsyncAgent`
2. Define custom task types with specific requirements
3. Implement custom message handlers
4. Add custom metrics collectors

## 📄 License

MIT License - See LICENSE file for details
