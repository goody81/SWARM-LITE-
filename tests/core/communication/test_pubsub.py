import pytest
import asyncio
from src.core.communication.pubsub import PubSubSystem
from src.core.communication.types import Message, MessageType, MessagePriority

@pytest.fixture
def pubsub():
    """Create a PubSubSystem instance"""
    return PubSubSystem()

@pytest.mark.asyncio
async def test_subscribe_to_topic(pubsub):
    """Test subscribing to a topic"""
    queue = await pubsub.subscribe("test-topic")
    
    assert isinstance(queue, asyncio.Queue)
    assert "test-topic" in pubsub.subscribers
    assert queue in pubsub.subscribers["test-topic"]

@pytest.mark.asyncio
async def test_multiple_subscriptions(pubsub):
    """Test multiple subscriptions to the same topic"""
    queue1 = await pubsub.subscribe("test-topic")
    queue2 = await pubsub.subscribe("test-topic")
    
    assert queue1 in pubsub.subscribers["test-topic"]
    assert queue2 in pubsub.subscribers["test-topic"]
    assert len(pubsub.subscribers["test-topic"]) == 2

@pytest.mark.asyncio
async def test_publish_to_subscribers(pubsub):
    """Test publishing a message to subscribers"""
    queue1 = await pubsub.subscribe("test-topic")
    queue2 = await pubsub.subscribe("test-topic")
    
    message = Message(
        id="test-123",
        type=MessageType.TASK,
        sender="agent-1",
        receiver=None,
        payload={"data": "test"}
    )
    
    await pubsub.publish("test-topic", message)
    
    # Both queues should receive the message
    msg1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    msg2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
    
    assert msg1.id == "test-123"
    assert msg2.id == "test-123"

@pytest.mark.asyncio
async def test_unsubscribe_from_topic(pubsub):
    """Test unsubscribing from a topic"""
    queue = await pubsub.subscribe("test-topic")
    
    assert "test-topic" in pubsub.subscribers
    
    await pubsub.unsubscribe("test-topic", queue)
    
    # Topic should be removed if no subscribers
    assert "test-topic" not in pubsub.subscribers

@pytest.mark.asyncio
async def test_unsubscribe_with_remaining_subscribers(pubsub):
    """Test unsubscribing with other subscribers remaining"""
    queue1 = await pubsub.subscribe("test-topic")
    queue2 = await pubsub.subscribe("test-topic")
    
    await pubsub.unsubscribe("test-topic", queue1)
    
    # Topic should still exist with remaining subscriber
    assert "test-topic" in pubsub.subscribers
    assert queue2 in pubsub.subscribers["test-topic"]
    assert queue1 not in pubsub.subscribers["test-topic"]

@pytest.mark.asyncio
async def test_publish_to_nonexistent_topic(pubsub):
    """Test publishing to a topic with no subscribers"""
    message = Message(
        id="test-456",
        type=MessageType.TASK,
        sender="agent-1",
        receiver=None,
        payload={"data": "test"}
    )
    
    # Should not raise an error
    await pubsub.publish("nonexistent-topic", message)
