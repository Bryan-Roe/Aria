"""
Aria Core Runner (Autonomous Runtime)
Transforms Aria into a self-planning, self-improving multi-agent system.
"""

from typing import Dict, Any
import time

from core.task import Task
from core.registry import AgentRegistry
from core.router import TaskRouter
from core.memory.store import MemoryStore

from core.agents.llm_agent import LLMAgent
from core.agents.tool_agent import ToolAgent
from core.agents.training_agent import TrainingAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.goal_evolution_agent import GoalEvolutionAgent


class AriaRunner:
    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

        self.memory = MemoryStore()
        self.registry = AgentRegistry()
        self.router = TaskRouter(self.registry)

        self._setup_agents()

    def _setup_agents(self):
        planner = PlannerAgent(self.memory)
        llm = LLMAgent()
        tool = ToolAgent()
        training = TrainingAgent()
        goal = GoalEvolutionAgent(self.memory)

        self.registry.register(planner)
        self.registry.register(llm)
        self.registry.register(tool)
        self.registry.register(training)
        self.registry.register(goal)

    def _run_task(self, task: Task):
        result = self.router.route(task)
        self.memory.write("task_result", {
            "task_id": task.id,
            "result": result,
        })
        return result

    def _generate_goal(self) -> str:
        """Now delegated to GoalEvolutionAgent via routing."""

        task = Task(
            id="goal_evolve",
            type="goal_evolve",
            payload={}
        )

        result = self.router.route(task)
        return result.get("result", {}).get("goal", "improve system performance")

    def _autonomous_cycle(self):
        goal = self._generate_goal()

        self.memory.write("goal_created", {"goal": goal})

        planner_task = Task(
            id="planner",
            type="plan",
            payload={"goal": goal},
        )

        plan_result = self.router.route(planner_task)
        plan = plan_result.get("result", {}).get("plan", [])

        self.memory.write("plan_received", {"plan": plan})

        for step in plan:
            task = Task(
                id=step.get("id"),
                type=step.get("type"),
                payload=step.get("payload", {}),
            )

            self._run_task(task)

    def run(self):
        print("[Aria] Autonomous self-improving runtime started.")

        while True:
            try:
                self._autonomous_cycle()
                time.sleep(2)
            except KeyboardInterrupt:
                print("[Aria] Shutdown requested.")
                break
            except Exception as e:
                print("[Aria] Error in cycle:", e)
                time.sleep(2)


if __name__ == "__main__":
    AriaRunner().run()
