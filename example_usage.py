"""
Example demonstrating the Communication Hub usage.

This example shows:
1. Creating a Communication Hub
2. Registering agents
3. Sending direct messages between agents
4. Broadcasting messages to all agents
5. Using the pub/sub system for topic-based messaging
"""

import asyncio
from src.core.communication import CommunicationHub, Message, MessageType, MessagePriority


async def agent_worker(hub, agent_id, queue):
    """Simulate an agent receiving and processing messages"""
    print(f"[{agent_id}] Starting...")
    
    # Process messages for a short time
    try:
        for _ in range(3):
            message = await asyncio.wait_for(queue.get(), timeout=2.0)
            print(f"[{agent_id}] Received message: {message.id} from {message.sender}")
            print(f"[{agent_id}]   Type: {message.type.value}, Priority: {message.priority.name}")
            print(f"[{agent_id}]   Payload: {message.payload}")
    except asyncio.TimeoutError:
        print(f"[{agent_id}] No more messages")
    
    print(f"[{agent_id}] Shutting down")


async def main():
    """Main example function"""
    print("=== Communication Hub Example ===\n")
    
    # Create and start the hub
    hub = CommunicationHub()
    await hub.start()
    print("Communication Hub started\n")
    
    # Register three agents
    print("Registering agents...")
    queue1 = await hub.register_agent("agent-1")
    queue2 = await hub.register_agent("agent-2")
    queue3 = await hub.register_agent("agent-3")
    print("Agents registered\n")
    
    # Start agent workers
    workers = [
        asyncio.create_task(agent_worker(hub, "agent-1", queue1)),
        asyncio.create_task(agent_worker(hub, "agent-2", queue2)),
        asyncio.create_task(agent_worker(hub, "agent-3", queue3)),
    ]
    
    await asyncio.sleep(0.1)  # Let agents start
    
    # Example 1: Send a direct message
    print("\n--- Example 1: Direct Message ---")
    message1 = Message(
        id="msg-001",
        type=MessageType.TASK,
        sender="agent-1",
        receiver="agent-2",
        payload={"task": "process_data", "data": [1, 2, 3]},
        priority=MessagePriority.HIGH
    )
    await hub.send_message(message1)
    print(f"Sent direct message from agent-1 to agent-2\n")
    
    await asyncio.sleep(0.5)
    
    # Example 2: Broadcast a message
    print("\n--- Example 2: Broadcast Message ---")
    broadcast_msg = Message(
        id="broadcast-001",
        type=MessageType.CONTROL,
        sender="coordinator",
        receiver=None,
        payload={"command": "status_check"},
        priority=MessagePriority.NORMAL
    )
    await hub.broadcast(broadcast_msg)
    print(f"Broadcasted message to all agents\n")
    
    await asyncio.sleep(0.5)
    
    # Example 3: Pub/Sub messaging
    print("\n--- Example 3: Pub/Sub Messaging ---")
    topic_queue = await hub.subscribe_to_topic("agent-3", "results")
    print("Agent-3 subscribed to 'results' topic")
    
    result_msg = Message(
        id="result-001",
        type=MessageType.RESULT,
        sender="agent-1",
        receiver=None,
        payload={"status": "completed", "result": 42},
        topic="results"
    )
    await hub.publish_to_topic("results", result_msg)
    print("Published result to 'results' topic")
    
    # Agent-3 receives the message
    received = await asyncio.wait_for(topic_queue.get(), timeout=1.0)
    print(f"Agent-3 received from topic: {received.payload}\n")
    
    # Wait for all agents to finish
    await asyncio.gather(*workers)
    
    # Cleanup
    print("\n--- Cleanup ---")
    await hub.unregister_agent("agent-1")
    await hub.unregister_agent("agent-2")
    await hub.unregister_agent("agent-3")
    await hub.stop()
    print("Communication Hub stopped")
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
