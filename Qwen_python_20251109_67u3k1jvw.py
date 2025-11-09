# src/sworms_lite.py
"""
SWORMS Lite - Lightweight Multi-Agent Communication System
A simplified version of the advanced SWORMS collective intelligence system
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    COMMUNICATING = "communicating"
    ERROR = "error"

@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    sender_id: str
    receiver_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: float = time.time()
    correlation_id: Optional[str] = None

@dataclass
class AgentState:
    """Current state of an agent"""
    agent_id: str
    status: AgentStatus
    last_update: float
    capabilities: List[str]
    resources: Dict[str, float]

class CommunicationHub:
    """Central communication hub for agent coordination"""
    
    def __init__(self):
        self.agents: Dict[str, AgentState] = {}
        self.message_queue = asyncio.Queue()
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.comm_latency = 0.05  # 50ms simulated latency
        
    async def register_agent(self, agent_id: str, capabilities: List[str]) -> AgentState:
        """Register a new agent with the hub"""
        state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            last_update=time.time(),
            capabilities=capabilities,
            resources={"cpu": 1.0, "memory": 1.0, "bandwidth": 1.0}
        )
        self.agents[agent_id] = state
        logger.info(f"Agent {agent_id} registered with capabilities: {capabilities}")
        return state
    
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message between agents"""
        if message.receiver_id not in self.agents:
            logger.error(f"Receiver {message.receiver_id} not found")
            return False
            
        # Simulate communication latency
        await asyncio.sleep(self.comm_latency)
        
        # Add to message queue for processing
        await self.message_queue.put(message)
        logger.debug(f"Message sent from {message.sender_id} to {message.receiver_id}")
        return True
    
    async def broadcast_message(self, sender_id: str, message_type: str, content: Dict[str, Any]):
        """Broadcast message to all agents"""
        for agent_id in self.agents:
            if agent_id != sender_id:
                message = AgentMessage(
                    sender_id=sender_id,
                    receiver_id=agent_id,
                    message_type=message_type,
                    content=content
                )
                await self.send_message(message)
    
    async def get_messages_for_agent(self, agent_id: str) -> List[AgentMessage]:
        """Get pending messages for an agent"""
        messages = []
        while not self.message_queue.empty():
            message = await self.message_queue.get()
            if message.receiver_id == agent_id:
                messages.append(message)
            else:
                # Put back if not for this agent
                await self.message_queue.put(message)
        return messages

class SWORMSLiteAgent:
    """Individual agent in the SWORMS Lite system"""
    
    def __init__(self, agent_id: str, hub: CommunicationHub, capabilities: List[str]):
        self.agent_id = agent_id
        self.hub = hub
        self.capabilities = capabilities
        self.state = AgentState(
            agent_id=agent_id,
            status=AgentStatus.IDLE,
            last_update=time.time(),
            capabilities=capabilities,
            resources={"cpu": 1.0, "memory": 1.0, "bandwidth": 1.0}
        )
        self.task_queue = asyncio.Queue()
        
    async def start(self):
        """Start the agent's main loop"""
        logger.info(f"Starting agent {self.agent_id}")
        self.state.status = AgentStatus.WORKING
        self.state.last_update = time.time()
        
        # Main agent loop
        while True:
            try:
                # Check for incoming messages
                messages = await self.hub.get_messages_for_agent(self.agent_id)
                for message in messages:
                    await self.handle_message(message)
                
                # Process any pending tasks
                if not self.task_queue.empty():
                    task = await self.task_queue.get()
                    await self.execute_task(task)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in agent {self.agent_id}: {e}")
                self.state.status = AgentStatus.ERROR
                break
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages"""
        logger.info(f"Agent {self.agent_id} received {message.message_type} from {message.sender_id}")
        
        if message.message_type == "task_assignment":
            await self.task_queue.put(message.content)
        elif message.message_type == "status_request":
            status_response = {
                "agent_id": self.agent_id,
                "status": self.state.status.value,
                "capabilities": self.state.capabilities,
                "resources": self.state.resources
            }
            response = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type="status_response",
                content=status_response
            )
            await self.hub.send_message(response)
    
    async def execute_task(self, task: Dict[str, Any]):
        """Execute a task assigned to this agent"""
        task_type = task.get("type", "unknown")
        logger.info(f"Agent {self.agent_id} executing {task_type} task")
        
        # Simulate task execution
        await asyncio.sleep(0.5)  # Simulate work
        
        # Update state
        self.state.status = AgentStatus.WORKING
        self.state.last_update = time.time()
        
        # Send completion message
        completion_msg = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=task.get("assigned_by", "coordinator"),
            message_type="task_completed",
            content={
                "task_id": task.get("task_id"),
                "result": f"Task completed by {self.agent_id}",
                "timestamp": time.time()
            }
        )
        await self.hub.send_message(completion_msg)
        
        self.state.status = AgentStatus.IDLE

class SWORMSLiteCoordinator:
    """Main coordinator for the SWORMS Lite system"""
    
    def __init__(self):
        self.hub = CommunicationHub()
        self.agents: Dict[str, SWORMSLiteAgent] = {}
        
    async def initialize_agents(self, agent_configs: List[Dict[str, Any]]):
        """Initialize all agents in the system"""
        for config in agent_configs:
            agent_id = config["id"]
            capabilities = config["capabilities"]
            
            agent = SWORMSLiteAgent(agent_id, self.hub, capabilities)
            await self.hub.register_agent(agent_id, capabilities)
            self.agents[agent_id] = agent
            
            # Start agent in background
            asyncio.create_task(agent.start())
            
        logger.info(f"Initialized {len(self.agents)} agents")
    
    async def assign_task(self, task_type: str, task_content: Dict[str, Any]):
        """Assign a task to available agents"""
        available_agents = [
            agent_id for agent_id, agent in self.agents.items()
            if agent.state.status == AgentStatus.IDLE
        ]
        
        if not available_agents:
            logger.warning("No available agents for task assignment")
            return False
            
        # Assign to first available agent (simplified load balancing)
        target_agent = available_agents[0]
        task_assignment = {
            "type": task_type,
            "content": task_content,
            "task_id": f"task_{int(time.time())}",
            "assigned_by": "coordinator"
        }
        
        message = AgentMessage(
            sender_id="coordinator",
            receiver_id=target_agent,
            message_type="task_assignment",
            content=task_assignment
        )
        
        success = await self.hub.send_message(message)
        if success:
            logger.info(f"Task assigned to {target_agent}")
        
        return success
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        status = {
            "timestamp": time.time(),
            "total_agents": len(self.agents),
            "active_agents": len([a for a in self.agents.values() if a.state.status != AgentStatus.IDLE]),
            "idle_agents": len([a for a in self.agents.values() if a.state.status == AgentStatus.IDLE]),
            "pending_messages": self.hub.message_queue.qsize(),
            "agents": {}
        }
        
        for agent_id, agent in self.agents.items():
            status["agents"][agent_id] = {
                "status": agent.state.status.value,
                "last_update": agent.state.last_update,
                "capabilities": agent.state.capabilities,
                "resources": agent.state.resources
            }
        
        return status

# Example usage
async def main():
    """Example usage of SWORMS Lite"""
    coordinator = SWORMSLiteCoordinator()
    
    # Define agent configurations
    agent_configs = [
        {
            "id": "agent_1",
            "capabilities": ["computation", "analysis"]
        },
        {
            "id": "agent_2", 
            "capabilities": ["communication", "coordination"]
        },
        {
            "id": "agent_3",
            "capabilities": ["data_processing", "storage"]
        }
    ]
    
    # Initialize the system
    await coordinator.initialize_agents(agent_configs)
    
    # Assign some tasks
    await coordinator.assign_task("computation", {"operation": "add", "values": [1, 2, 3, 4, 5]})
    await coordinator.assign_task("analysis", {"data": "sample_data", "type": "statistical"})
    
    # Wait a bit for processing
    await asyncio.sleep(2)
    
    # Get system status
    status = await coordinator.get_system_status()
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    asyncio.run(main())