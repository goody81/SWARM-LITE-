import pytest
from datetime import datetime
from src.core.communication.types import Message, MessageType, MessagePriority

def test_message_priority_enum():
    """Test MessagePriority enum values"""
    assert MessagePriority.LOW.value == 0
    assert MessagePriority.NORMAL.value == 1
    assert MessagePriority.HIGH.value == 2
    assert MessagePriority.CRITICAL.value == 3

def test_message_type_enum():
    """Test MessageType enum values"""
    assert MessageType.TASK.value == "task"
    assert MessageType.RESULT.value == "result"
    assert MessageType.HEARTBEAT.value == "heartbeat"
    assert MessageType.CONTROL.value == "control"
    assert MessageType.ERROR.value == "error"

def test_message_creation():
    """Test Message dataclass creation"""
    message = Message(
        id="test-123",
        type=MessageType.TASK,
        sender="agent-1",
        receiver="agent-2",
        payload={"data": "test"}
    )
    
    assert message.id == "test-123"
    assert message.type == MessageType.TASK
    assert message.sender == "agent-1"
    assert message.receiver == "agent-2"
    assert message.payload == {"data": "test"}
    assert message.priority == MessagePriority.NORMAL
    assert message.ttl == 300
    assert message.topic is None
    assert isinstance(message.created_at, datetime)

def test_message_with_custom_priority():
    """Test Message with custom priority"""
    message = Message(
        id="test-456",
        type=MessageType.ERROR,
        sender="agent-1",
        receiver="agent-2",
        payload={"error": "test error"},
        priority=MessagePriority.CRITICAL
    )
    
    assert message.priority == MessagePriority.CRITICAL

def test_message_with_topic():
    """Test Message with topic for pub/sub"""
    message = Message(
        id="test-789",
        type=MessageType.RESULT,
        sender="agent-1",
        receiver=None,
        payload={"result": "success"},
        topic="results"
    )
    
    assert message.topic == "results"
    assert message.receiver is None

def test_message_with_custom_ttl():
    """Test Message with custom TTL"""
    message = Message(
        id="test-999",
        type=MessageType.HEARTBEAT,
        sender="agent-1",
        receiver=None,
        payload={},
        ttl=60
    )
    
    assert message.ttl == 60
