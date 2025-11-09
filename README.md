# SWARM-LITE - Communication Hub

A robust, async communication system for multi-agent coordination.

## Overview

The Communication Hub is the critical component that enables agent communication and message routing in SWARM-LITE. It provides efficient message routing, topic-based pub/sub messaging, and automatic resource cleanup.

## Features

- **Async Message Handling**: Non-blocking, high-performance message routing
- **Direct Messaging**: Send messages to specific agents
- **Broadcast Messaging**: Send messages to all active agents
- **Pub/Sub System**: Topic-based messaging for flexible communication patterns
- **Message Prioritization**: Support for LOW, NORMAL, HIGH, and CRITICAL priorities
- **Automatic Cleanup**: Expired messages and inactive agents are automatically cleaned up
- **Message History**: Track sent messages with configurable TTL

## Architecture

```
src/core/communication/
├── __init__.py       # Module exports
├── types.py          # Message types and enums
├── pubsub.py         # Publish/Subscribe system
└── hub.py            # Main CommunicationHub class
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
import asyncio
from src.core.communication import CommunicationHub, Message, MessageType, MessagePriority

async def main():
    # Create and start the hub
    hub = CommunicationHub()
    await hub.start()
    
    # Register agents
    queue1 = await hub.register_agent("agent-1")
    queue2 = await hub.register_agent("agent-2")
    
    # Send a message
    message = Message(
        id="msg-001",
        type=MessageType.TASK,
        sender="agent-1",
        receiver="agent-2",
        payload={"task": "process_data"},
        priority=MessagePriority.HIGH
    )
    await hub.send_message(message)
    
    # Receive the message
    received = await queue2.get()
    print(f"Received: {received.payload}")
    
    # Cleanup
    await hub.stop()

asyncio.run(main())
```

## Core Components

### Message Types

The system supports five message types:

- **TASK**: Task assignment messages
- **RESULT**: Task result messages
- **HEARTBEAT**: Agent health check messages
- **CONTROL**: System control messages
- **ERROR**: Error notification messages

### Message Priorities

Messages can have four priority levels:

- **LOW** (0): Background tasks
- **NORMAL** (1): Standard messages
- **HIGH** (2): Important messages
- **CRITICAL** (3): Urgent system messages

### Message Structure

```python
@dataclass
class Message:
    id: str                           # Unique message identifier
    type: MessageType                 # Message type
    sender: str                       # Sender agent ID
    receiver: Optional[str]           # Receiver agent ID (None for broadcast)
    payload: Dict[str, Any]           # Message data
    priority: MessagePriority         # Message priority (default: NORMAL)
    created_at: datetime              # Creation timestamp
    ttl: int                          # Time to live in seconds (default: 300)
    topic: Optional[str]              # Topic for pub/sub messages
```

## Communication Patterns

### 1. Direct Messaging

Send a message to a specific agent:

```python
message = Message(
    id="msg-001",
    type=MessageType.TASK,
    sender="agent-1",
    receiver="agent-2",
    payload={"data": "example"}
)
await hub.send_message(message)
```

### 2. Broadcasting

Send a message to all active agents:

```python
message = Message(
    id="broadcast-001",
    type=MessageType.CONTROL,
    sender="coordinator",
    receiver=None,
    payload={"command": "shutdown"}
)
await hub.broadcast(message)
```

### 3. Pub/Sub Messaging

Topic-based messaging for flexible communication:

```python
# Subscribe to a topic
queue = await hub.subscribe_to_topic("agent-1", "results")

# Publish to the topic
message = Message(
    id="pub-001",
    type=MessageType.RESULT,
    sender="agent-2",
    receiver=None,
    payload={"result": 42},
    topic="results"
)
await hub.publish_to_topic("results", message)

# Receive from topic
received = await queue.get()
```

## API Reference

### CommunicationHub

#### Methods

- `async start()`: Start the communication hub
- `async stop()`: Stop the communication hub
- `async register_agent(agent_id: str) -> asyncio.Queue`: Register an agent
- `async unregister_agent(agent_id: str)`: Unregister an agent
- `async send_message(message: Message) -> bool`: Send a message to a specific agent
- `async broadcast(message: Message)`: Broadcast a message to all active agents
- `async subscribe_to_topic(agent_id: str, topic: str) -> asyncio.Queue`: Subscribe to a topic
- `async publish_to_topic(topic: str, message: Message)`: Publish to a topic

### PubSubSystem

#### Methods

- `async subscribe(topic: str) -> asyncio.Queue`: Subscribe to a topic
- `async unsubscribe(topic: str, queue: asyncio.Queue)`: Unsubscribe from a topic
- `async publish(topic: str, message: Message)`: Publish a message to all topic subscribers

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run a specific test file:

```bash
pytest tests/core/communication/test_hub.py -v
```

## Example

See `example_usage.py` for a complete working example demonstrating:
- Agent registration
- Direct messaging
- Broadcasting
- Pub/sub messaging

Run the example:

```bash
python example_usage.py
```

## Performance Characteristics

- **Async/Non-blocking**: All operations are async for high concurrency
- **Efficient Routing**: O(1) lookup for direct messages
- **Scalable Pub/Sub**: Efficient fan-out for topic-based messaging
- **Memory Management**: Automatic cleanup of expired messages every 60 seconds

## Design Principles

1. **Fast**: Async message handling for high throughput
2. **Reliable**: Message delivery tracking and error handling
3. **Scalable**: Efficient pub/sub for many-to-many communication
4. **Clean**: Automatic resource cleanup prevents memory leaks
5. **Simple**: Clean API for easy integration

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
