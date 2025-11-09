# SWARM-LITE

A lightweight multi-agent task coordination system.

## Overview

SWARM-LITE provides a simple but powerful framework for coordinating multiple agents to process tasks in a distributed manner. The system includes:

- **Agent Management**: Create and manage autonomous agents with specific capabilities
- **Task Coordination**: Intelligent task assignment based on agent capabilities and resources
- **Communication Hub**: Centralized message routing between agents
- **Docker Support**: Easy containerization and deployment

## Architecture

The system consists of three core modules:

1. **core.agent**: Agent implementation with capability management
2. **core.communication**: Message passing and agent communication
3. **core.tasks**: Task coordination and scheduling

## Quick Start

### Running Locally

```bash
cd src
python main.py
```

### Running with Docker

Build and run:
```bash
docker build -t swarm-lite .
docker run swarm-lite
```

### Running with Docker Compose

Start the system:
```bash
docker-compose up -d
```

Scale workers:
```bash
docker-compose up -d --scale worker=5
```

Monitor logs:
```bash
docker-compose logs -f
```

Stop the system:
```bash
docker-compose down
```

## Usage Example

```python
from core.agent import AgentCapabilities
from core.tasks import TaskRequirements, TaskPriority
from main import SwarmLite

async def example():
    # Create system
    system = SwarmLite()
    await system.start()
    
    # Create agents
    capabilities = AgentCapabilities(
        compute=1.0,
        memory=2.0,
        tasks=["process", "analyze"]
    )
    agent_id = await system.create_agent(capabilities)
    
    # Submit a task
    requirements = TaskRequirements(
        min_cpu=0.5,
        min_memory=1.0,
        capabilities=["process"]
    )
    task_id = await system.submit_task(
        task_type="process",
        payload={"data": "sample"},
        requirements=requirements,
        priority=TaskPriority.NORMAL
    )
    
    # Get result
    result = await system.get_task_result(task_id)
    print(f"Result: {result}")
    
    await system.stop()
```

## Configuration

Environment variables:
- `SWARM_LITE_LOG_LEVEL`: Logging level (default: INFO)
- `SWARM_LITE_MAX_AGENTS`: Maximum number of agents (default: 10)
- `SWARM_LITE_MAX_TASK_QUEUE_SIZE`: Maximum task queue size (default: 1000)

## Requirements

- Python 3.11+
- All dependencies are part of Python standard library

## License

MIT
