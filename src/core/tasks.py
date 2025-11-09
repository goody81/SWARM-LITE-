"""Task management module for SWARM-LITE system"""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priorities"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskRequirements:
    """Task resource requirements"""
    min_cpu: float
    min_memory: float
    capabilities: List[str]


@dataclass
class Task:
    """Task definition"""
    id: str
    type: str
    payload: Dict[str, Any]
    requirements: TaskRequirements
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class TaskCoordinator:
    """Task coordination and scheduling"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.agents: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._coordinator_task = None
        self.result_events: Dict[str, asyncio.Event] = {}
        
    async def start(self):
        """Start the task coordinator"""
        self._running = True
        self._coordinator_task = asyncio.create_task(self._coordinate())
        logger.info("TaskCoordinator started")
        
    async def stop(self):
        """Stop the task coordinator"""
        self._running = False
        if self._coordinator_task:
            await self._coordinator_task
        logger.info("TaskCoordinator stopped")
        
    async def register_agent(self, agent_id: str, capabilities: Dict[str, Any]):
        """Register an agent with the coordinator"""
        self.agents[agent_id] = {
            "id": agent_id,
            "capabilities": capabilities,
            "available": True,
            "current_task": None
        }
        logger.info(f"Agent {agent_id} registered with TaskCoordinator")
        
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered from TaskCoordinator")
            
    async def submit_task(self, task: Task) -> str:
        """Submit a new task"""
        self.tasks[task.id] = task
        await self.task_queue.put(task)
        self.result_events[task.id] = asyncio.Event()
        logger.info(f"Task {task.id} submitted")
        return task.id
        
    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get task result (waits until complete)"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
            
        # Wait for task completion
        if task_id in self.result_events:
            await self.result_events[task_id].wait()
            
        task = self.tasks[task_id]
        if task.status == TaskStatus.COMPLETED:
            return task.result or {}
        elif task.status == TaskStatus.FAILED:
            return {"error": "Task failed"}
        else:
            return {"status": task.status.value}
            
    async def _coordinate(self):
        """Main coordination loop"""
        while self._running:
            try:
                # Try to get a task from the queue
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                    await self._assign_task(task)
                except asyncio.TimeoutError:
                    pass
            except Exception as e:
                logger.error(f"Error in task coordination: {e}")
                
    async def _assign_task(self, task: Task):
        """Assign a task to an available agent"""
        # Find suitable agent
        suitable_agent = None
        for agent_id, agent_info in self.agents.items():
            if agent_info["available"]:
                # Check if agent meets requirements
                caps = agent_info["capabilities"]
                if (caps.get("cpu", 0) >= task.requirements.min_cpu and
                    caps.get("memory", 0) >= task.requirements.min_memory):
                    # Check capability match
                    agent_caps = caps.get("capabilities", [])
                    if any(req_cap in agent_caps for req_cap in task.requirements.capabilities):
                        suitable_agent = agent_id
                        break
                        
        if suitable_agent:
            task.status = TaskStatus.ASSIGNED
            task.assigned_agent = suitable_agent
            self.agents[suitable_agent]["available"] = False
            self.agents[suitable_agent]["current_task"] = task.id
            logger.info(f"Task {task.id} assigned to agent {suitable_agent}")
            
            # Simulate task execution
            asyncio.create_task(self._execute_task(task, suitable_agent))
        else:
            # Put task back in queue
            await self.task_queue.put(task)
            logger.warning(f"No suitable agent found for task {task.id}")
            
    async def _execute_task(self, task: Task, agent_id: str):
        """Execute a task (simulated)"""
        try:
            task.status = TaskStatus.RUNNING
            # Simulate work
            await asyncio.sleep(0.5)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.result = {
                "task_id": task.id,
                "agent_id": agent_id,
                "output": f"Processed {task.type} task",
                "payload": task.payload
            }
            
            # Notify result available
            if task.id in self.result_events:
                self.result_events[task.id].set()
                
            logger.info(f"Task {task.id} completed by agent {agent_id}")
        except Exception as e:
            task.status = TaskStatus.FAILED
            logger.error(f"Task {task.id} failed: {e}")
            if task.id in self.result_events:
                self.result_events[task.id].set()
        finally:
            # Free up the agent
            if agent_id in self.agents:
                self.agents[agent_id]["available"] = True
                self.agents[agent_id]["current_task"] = None
