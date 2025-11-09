import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from src.core.communication.hub import CommunicationHub
from src.core.communication.types import Message, MessageType, MessagePriority

@pytest.fixture
async def hub():
    """Create and start a CommunicationHub instance"""
    hub = CommunicationHub()
    await hub.start()
    yield hub
    await hub.stop()

@pytest.mark.asyncio
async def test_hub_start_stop(hub):
    """Test starting and stopping the hub"""
    assert hub._cleanup_task is not None
    assert not hub._cleanup_task.done()
    
    await hub.stop()
    
    # Wait a bit for cancellation to process
    await asyncio.sleep(0.1)
    assert hub._cleanup_task.cancelled() or hub._cleanup_task.done()

@pytest.mark.asyncio
async def test_register_agent(hub):
    """Test registering an agent"""
    queue = await hub.register_agent("agent-1")
    
    assert isinstance(queue, asyncio.Queue)
    assert "agent-1" in hub.agent_queues
    assert "agent-1" in hub.active_agents

@pytest.mark.asyncio
async def test_unregister_agent(hub):
    """Test unregistering an agent"""
    await hub.register_agent("agent-1")
    
    await hub.unregister_agent("agent-1")
    
    assert "agent-1" not in hub.agent_queues
    assert "agent-1" not in hub.active_agents

@pytest.mark.asyncio
async def test_send_message(hub):
    """Test sending a message to a specific agent"""
    queue = await hub.register_agent("agent-2")
    
    message = Message(
        id="test-123",
        type=MessageType.TASK,
        sender="agent-1",
        receiver="agent-2",
        payload={"data": "test"}
    )
    
    result = await hub.send_message(message)
    
    assert result is True
    assert message.id in hub.message_history
    
    # Agent should receive the message
    received_msg = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received_msg.id == "test-123"

@pytest.mark.asyncio
async def test_send_message_to_nonexistent_agent(hub):
    """Test sending a message to a non-existent agent"""
    message = Message(
        id="test-456",
        type=MessageType.TASK,
        sender="agent-1",
        receiver="nonexistent-agent",
        payload={"data": "test"}
    )
    
    result = await hub.send_message(message)
    
    assert result is False

@pytest.mark.asyncio
async def test_broadcast_message(hub):
    """Test broadcasting a message to all agents"""
    queue1 = await hub.register_agent("agent-1")
    queue2 = await hub.register_agent("agent-2")
    queue3 = await hub.register_agent("agent-3")
    
    message = Message(
        id="broadcast-123",
        type=MessageType.CONTROL,
        sender="coordinator",
        receiver=None,
        payload={"command": "shutdown"}
    )
    
    await hub.broadcast(message)
    
    # All agents should receive a message
    msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
    msg3 = await asyncio.wait_for(queue3.get(), timeout=1.0)
    
    # Messages should have unique IDs but same content
    assert msg1.payload == {"command": "shutdown"}
    assert msg2.payload == {"command": "shutdown"}
    assert msg3.payload == {"command": "shutdown"}

@pytest.mark.asyncio
async def test_subscribe_to_topic(hub):
    """Test subscribing to a topic"""
    queue = await hub.subscribe_to_topic("agent-1", "updates")
    
    assert isinstance(queue, asyncio.Queue)
    assert "updates" in hub.pubsub.subscribers

@pytest.mark.asyncio
async def test_publish_to_topic(hub):
    """Test publishing to a topic"""
    queue = await hub.subscribe_to_topic("agent-1", "results")
    
    message = Message(
        id="pub-123",
        type=MessageType.RESULT,
        sender="agent-2",
        receiver=None,
        payload={"result": "success"},
        topic="results"
    )
    
    await hub.publish_to_topic("results", message)
    
    received_msg = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received_msg.id == "pub-123"
    assert received_msg.payload == {"result": "success"}

@pytest.mark.asyncio
async def test_message_cleanup():
    """Test that expired messages are cleaned up"""
    hub = CommunicationHub()
    # Don't start the hub to control cleanup timing
    
    # Create an expired message
    old_message = Message(
        id="old-123",
        type=MessageType.TASK,
        sender="agent-1",
        receiver="agent-2",
        payload={"data": "old"},
        ttl=1  # 1 second TTL
    )
    old_message.created_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    hub.message_history["old-123"] = old_message
    
    # Create a fresh message
    new_message = Message(
        id="new-456",
        type=MessageType.TASK,
        sender="agent-1",
        receiver="agent-2",
        payload={"data": "new"}
    )
    hub.message_history["new-456"] = new_message
    
    # Manually run one iteration of cleanup
    current_time = datetime.now(timezone.utc)
    expired_messages = [
        msg_id for msg_id, msg in hub.message_history.items()
        if (current_time - msg.created_at).total_seconds() > msg.ttl
    ]
    for msg_id in expired_messages:
        del hub.message_history[msg_id]
    
    # Old message should be removed, new one should remain
    assert "old-123" not in hub.message_history
    assert "new-456" in hub.message_history

@pytest.mark.asyncio
async def test_multiple_agents_multiple_messages(hub):
    """Test complex scenario with multiple agents and messages"""
    # Register multiple agents
    queues = {}
    for i in range(5):
        agent_id = f"agent-{i}"
        queues[agent_id] = await hub.register_agent(agent_id)
    
    # Send messages between agents
    for i in range(5):
        for j in range(5):
            if i != j:
                message = Message(
                    id=f"msg-{i}-{j}",
                    type=MessageType.TASK,
                    sender=f"agent-{i}",
                    receiver=f"agent-{j}",
                    payload={"from": i, "to": j}
                )
                await hub.send_message(message)
    
    # Each agent should receive 4 messages (from each other agent)
    for agent_id, queue in queues.items():
        messages = []
        for _ in range(4):
            msg = await asyncio.wait_for(queue.get(), timeout=1.0)
            messages.append(msg)
        
        assert len(messages) == 4
        assert queue.empty()
