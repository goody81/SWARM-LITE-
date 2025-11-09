import asyncio
import logging
import uuid
from typing import List, Dict
from core.agent import Agent, AgentCapabilities
from core.communication import CommunicationHub, Message, MessageType, MessagePriority
from core.tasks import TaskCoordinator, Task, TaskRequirements, TaskPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SwarmLite:
    def __init__(self):
        self.hub = CommunicationHub()
        self.coordinator = TaskCoordinator()
        self.agents: Dict[str, Agent] = {}
        
    async def start(self):
        """Start the SWARM-LITE system"""
        await self.hub.start()
        await self.coordinator.start()
        logger.info("SWARM-LITE system started")
        
    async def stop(self):
        """Stop the SWARM-LITE system"""
        await self.hub.stop()
        await self.coordinator.stop()
        logger.info("SWARM-LITE system stopped")
        
    async def create_agent(self, capabilities: AgentCapabilities) -> str:
        """Create and register a new agent"""
        agent_id = str(uuid.uuid4())
        agent = Agent(agent_id, capabilities)
        
        # Register with communication hub
        queue = await self.hub.register_agent(agent_id)
        agent.set_message_queue(queue)
        
        # Register with task coordinator
        await self.coordinator.register_agent(agent_id, {
            "cpu": capabilities.compute,
            "memory": capabilities.memory,
            "capabilities": capabilities.tasks
        })
        
        self.agents[agent_id] = agent
        await agent.start()
        logger.info(f"Agent {agent_id} created and started")
        return agent_id
        
    async def submit_task(self, task_type: str, payload: Dict,
                         requirements: TaskRequirements,
                         priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Submit a new task to the system"""
        task = Task(
            id=str(uuid.uuid4()),
            type=task_type,
            payload=payload,
            requirements=requirements,
            priority=priority
        )
        task_id = await self.coordinator.submit_task(task)
        logger.info(f"Task {task_id} submitted")
        return task_id
        
    async def get_task_result(self, task_id: str) -> Dict:
        """Get the result of a task"""
        return await self.coordinator.get_task_result(task_id)

async def main():
    # Create and start the system
    system = SwarmLite()
    await system.start()
    
    try:
        # Create some agents
        agent_ids = []
        for i in range(3):
            capabilities = AgentCapabilities(
                compute=1.0,
                memory=2.0,
                tasks=["process", "analyze"]
            )
            agent_id = await system.create_agent(capabilities)
            agent_ids.append(agent_id)
            
        # Submit some tasks
        task_ids = []
        for i in range(5):
            requirements = TaskRequirements(
                min_cpu=0.5,
                min_memory=1.0,
                capabilities=["process"]
            )
            task_id = await system.submit_task(
                task_type="process",
                payload={"data": f"sample_{i}"},
                requirements=requirements,
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
            
        # Wait for results
        for task_id in task_ids:
            result = await system.get_task_result(task_id)
            logger.info(f"Task {task_id} result: {result}")
            
        # Keep system running
        await asyncio.sleep(3600)  # Run for an hour
            
    finally:
        await system.stop()

if __name__ == "__main__":
    asyncio.run(main())
