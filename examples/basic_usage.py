"""Basic example demonstrating SWARM-LITE- usage."""

import asyncio
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import AsyncAgent, CommunicationHub, TaskCoordinator
from src.protocols import Task
from src.core.types import TaskPriority
from src.utils import setup_logging


class ComputeAgent(AsyncAgent):
    """Example agent that performs computation tasks."""

    def __init__(self, name: str):
        """Initialize compute agent."""
        super().__init__(
            name=name,
            agent_type="compute",
            supported_task_types=["add", "multiply", "fibonacci"],
            max_concurrent_tasks=3,
        )

    async def _execute_task(self, task: Task):
        """Execute computation task.

        Args:
            task: Task to execute

        Returns:
            Computation result
        """
        task_type = task.task_type
        payload = task.payload

        if task_type == "add":
            a = payload.get("a", 0)
            b = payload.get("b", 0)
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": a + b, "operation": "add"}

        elif task_type == "multiply":
            a = payload.get("a", 1)
            b = payload.get("b", 1)
            await asyncio.sleep(0.2)  # Simulate work
            return {"result": a * b, "operation": "multiply"}

        elif task_type == "fibonacci":
            n = payload.get("n", 0)
            await asyncio.sleep(0.1)  # Simulate work

            # Compute fibonacci number
            if n <= 1:
                result = n
            else:
                a, b = 0, 1
                for _ in range(n - 1):
                    a, b = b, a + b
                result = b

            return {"result": result, "operation": "fibonacci", "n": n}

        else:
            raise ValueError(f"Unknown task type: {task_type}")


async def main():
    """Run the example."""
    # Setup logging
    logger = setup_logging(log_level="INFO", log_format="text")

    print("=" * 60)
    print("SWARM-LITE- Basic Example")
    print("=" * 60)
    print()

    # Create system components
    print("🔧 Initializing system components...")
    hub = CommunicationHub()
    coordinator = TaskCoordinator(hub)

    # Start components
    await hub.start()
    await coordinator.start()
    print("✓ System components started")
    print()

    # Create and start agents
    print("🤖 Creating and starting agents...")
    agent1 = ComputeAgent("compute-1")
    agent2 = ComputeAgent("compute-2")
    agent3 = ComputeAgent("compute-3")

    await hub.register_agent(agent1)
    await hub.register_agent(agent2)
    await hub.register_agent(agent3)

    await agent1.start()
    await agent2.start()
    await agent3.start()
    print(f"✓ Started {len(hub.get_all_agents())} agents")
    print()

    # Submit various tasks
    print("📝 Submitting tasks...")
    tasks = []

    # Addition tasks
    for i in range(3):
        task = Task(
            task_type="add",
            priority=TaskPriority.NORMAL,
            payload={"a": i * 2, "b": i * 3},
        )
        task_id = await coordinator.submit_task(task)
        tasks.append((task_id, "add", f"{i*2} + {i*3}"))

    # Multiplication tasks
    for i in range(2):
        task = Task(
            task_type="multiply",
            priority=TaskPriority.HIGH,
            payload={"a": i + 2, "b": i + 3},
        )
        task_id = await coordinator.submit_task(task)
        tasks.append((task_id, "multiply", f"{i+2} × {i+3}"))

    # Fibonacci tasks
    for n in [5, 8, 10]:
        task = Task(
            task_type="fibonacci",
            priority=TaskPriority.NORMAL,
            payload={"n": n},
        )
        task_id = await coordinator.submit_task(task)
        tasks.append((task_id, "fibonacci", f"fib({n})"))

    print(f"✓ Submitted {len(tasks)} tasks")
    print()

    # Wait for tasks to complete
    print("⏳ Processing tasks...")
    await asyncio.sleep(2)
    print()

    # Display results
    print("📊 Results:")
    print("-" * 60)
    for task_id, task_type, description in tasks:
        task = coordinator.get_task(task_id)
        if task and task.result:
            result = task.result.get("result")
            print(f"  {description:15} = {result}")
    print()

    # Display statistics
    stats = coordinator.get_statistics()
    print("📈 System Statistics:")
    print("-" * 60)
    print(f"  Total tasks:     {stats['total_tasks']}")
    print(f"  Completed tasks: {stats['completed_tasks']}")
    print(f"  Failed tasks:    {stats['failed_tasks']}")
    print(f"  Active agents:   {stats['active_agents']}")
    print()

    # Display agent information
    print("🤖 Agent Information:")
    print("-" * 60)
    for agent_info in hub.get_all_agents():
        metrics = agent_info.metrics
        print(f"  {agent_info.name:12} | "
              f"State: {agent_info.state.name:12} | "
              f"Active: {metrics.active_tasks} | "
              f"Completed: {metrics.completed_tasks}")
    print()

    # Cleanup
    print("🧹 Shutting down...")
    await agent1.stop()
    await agent2.stop()
    await agent3.stop()
    await coordinator.stop()
    await hub.stop()
    print("✓ System shutdown complete")
    print()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
