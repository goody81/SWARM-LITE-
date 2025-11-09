# tests/test_sworms_lite.py
"""
Tests for SWORMS Lite system
"""
import pytest
import asyncio
from src.sworms_lite import SWORMSLiteCoordinator, AgentMessage, AgentStatus

@pytest.fixture
async def coordinator():
    """Create a test coordinator instance"""
    coord = SWORMSLiteCoordinator()
    agent_configs = [
        {"id": "test_agent_1", "capabilities": ["test"]},
        {"id": "test_agent_2", "capabilities": ["test"]}
    ]
    await coord.initialize_agents(agent_configs)
    return coord

@pytest.mark.asyncio
async def test_agent_initialization(coordinator):
    """Test that agents are properly initialized"""
    status = await coordinator.get_system_status()
    assert status["total_agents"] == 2
    assert len(status["agents"]) == 2
    assert "test_agent_1" in status["agents"]
    assert "test_agent_2" in status["agents"]

@pytest.mark.asyncio
async def test_task_assignment(coordinator):
    """Test task assignment functionality"""
    success = await coordinator.assign_task("test", {"data": "test_data"})
    assert success is True

@pytest.mark.asyncio
async def test_message_passing():
    """Test basic message passing"""
    coord = SWORMSLiteCoordinator()
    await coord.initialize_agents([{"id": "sender", "capabilities": ["test"]}])
    
    message = AgentMessage(
        sender_id="sender",
        receiver_id="sender",  # Send to self for testing
        message_type="test",
        content={"test": "data"}
    )
    
    success = await coord.hub.send_message(message)
    assert success is True

@pytest.mark.asyncio
async def test_system_status(coordinator):
    """Test system status reporting"""
    status = await coordinator.get_system_status()
    assert "timestamp" in status
    assert "total_agents" in status
    assert status["total_agents"] == 2

def test_agent_message_creation():
    """Test agent message creation"""
    msg = AgentMessage(
        sender_id="test",
        receiver_id="test",
        message_type="test",
        content={"data": "test"}
    )
    assert msg.sender_id == "test"
    assert msg.message_type == "test"

if __name__ == "__main__":
    pytest.main([__file__])