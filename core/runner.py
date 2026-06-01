"""
Aria Core Runner (Autonomous Runtime)
Transforms Aria into a self-planning, self-improving multi-agent system.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from core.agents.goal_evolution_agent import GoalEvolutionAgent
from core.agents.human_feedback_agent import HumanFeedbackAgent
from core.agents.llm_agent import LLMAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.summarizer_agent import SummarizerAgent
from core.agents.critique_agent import CritiqueAgent
from core.agents.reasoning_agent import ReasoningAgent
from core.agents.debate_agent import DebateAgent
from core.agents.tool_agent import ToolAgent
from core.agents.training_agent import TrainingAgent
from core.bus import AgentBus
from core.knowledge.graph import ConceptLinker, KnowledgeGraph
from core.memory.store import MemoryStore
from core.registry import AgentRegistry
from core.router import TaskRouter
from core.task import Task


class AriaRunner:
    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.sleep_seconds = float(self.config.get("sleep_seconds", 2))
        self.max_cycles = self.config.get("max_cycles")

        self.memory = MemoryStore(db_path=self.config.get("memory_db_path"))
        self.registry = AgentRegistry()
        self.router = TaskRouter(self.registry)
        self.bus = AgentBus()
        self.knowledge_graph = KnowledgeGraph()
        self.concept_linker = ConceptLinker(self.knowledge_graph, self.memory)

        self._setup_agents()

    def _setup_agents(self):
        planner = PlannerAgent(self.memory)
        llm = LLMAgent()
        tool = ToolAgent()
        training = TrainingAgent()
        goal = GoalEvolutionAgent(self.memory)
        feedback = HumanFeedbackAgent(self.memory, self.bus)
        summarizer = SummarizerAgent(self.memory)
        critique = CritiqueAgent(self.memory)
        reasoning = ReasoningAgent(self.memory)
        debate = DebateAgent(self.memory)

        tool.registry.register("inspect_context", self._inspect_context)
        tool.registry.register("recent_events", self._recent_events)
        tool.registry.register("knowledge_neighbors", self._knowledge_neighbors)
        tool.registry.register("knowledge_related", self._knowledge_related)
        tool.registry.register("knowledge_path", self._knowledge_path)

        self.registry.register(planner)
        self.registry.register(llm)
        self.registry.register(tool)
        self.registry.register(training)
        self.registry.register(goal)
        self.registry.register(feedback)
        self.registry.register(summarizer)
        self.registry.register(critique)
        self.registry.register(reasoning)
        self.registry.register(debate)

    def _inspect_context(self, goal: str = "") -> Dict[str, Any]:
        return {"goal": goal, "event_counts": self.memory.count_by_type(), "recent_events": self.memory.last(5)}

    def _recent_events(self, limit: int = 5) -> Dict[str, Any]:
        return {"events": self.memory.last(limit)}

    def _knowledge_neighbors(self, entity: str) -> Dict[str, Any]:
        return {"entity": entity, "neighbors": self.knowledge_graph.neighbors(entity)}

    def _knowledge_related(self, entity: str, max_depth: int = 2) -> Dict[str, Any]:
        return {"entity": entity, "related": self.knowledge_graph.find_related(entity, max_depth=max_depth)}

    def _knowledge_path(self, source: str, target: str) -> Dict[str, Any]:
        return {"source": source, "target": target, "path": self.knowledge_graph.shortest_path(source, target)}

    def _run_task(self, task: Task):
        result = self.router.route(task)
        self.memory.write("task_result", {"task_id": task.id, "task_type": task.type, "result": result})
        return result

    def _normalize_plan_step(self, step: Any, index: int) -> tuple[Task | None, Dict[str, Any] | None]:
        if not isinstance(step, dict):
            return None, {"index": index, "error": "Plan step must be a dictionary"}

        step_type = step.get("type")
        if not isinstance(step_type, str) or not step_type.strip():
            return None, {"index": index, "error": "Plan step is missing a valid type"}

        payload = step.get("payload", {})
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return None, {"index": index, "error": "Plan step payload must be a dictionary"}

        try:
            task = Task(id=step.get("id"), type=step_type, payload=payload, priority=int(step.get("priority", 0)))
        except Exception as exc:
            return None, {"index": index, "error": str(exc)}
        return task, None

    def _generate_goal(self) -> str:
        task = Task(id="goal_evolve", type="goal_evolve", payload={})
        result = self.router.route(task)
        return result.get("result", {}).get("goal", "improve system performance")

    def _run_self_assess_loop(self, goal: str) -> Dict[str, Any] | None:
        training_agent = self.registry.get("training_agent")
        if training_agent is None:
            return None
        assessor = getattr(training_agent, "self_assess", None)
        if not callable(assessor):
            return None
        assessment = assessor(target_score=float(self.config.get("target_score", 0.7)))
        self.memory.write("training_self_assessment", {"goal": goal, **assessment})
        if assessment.get("needs_retraining"):
            retrain_task = Task(type="train", payload={"goal": goal, "source": "self_assess"})
            retrain_result = self.router.route(retrain_task)
            assessment = dict(assessment)
            assessment["retrain_result"] = retrain_result
        return assessment

    def _autonomous_cycle(self):
        goal = self._generate_goal()
        self.memory.write("goal_created", {"goal": goal})

        planner_task = Task(id="planner", type="plan", payload={"goal": goal})
        plan_result = self.router.route(planner_task)
        plan = plan_result.get("result", {}).get("plan", [])
        plan_error = plan_result.get("result", {}).get("error")

        self.memory.write("plan_received", {"plan": plan})

        executed = []
        skipped = []
        for index, step in enumerate(plan):
            task, skip_reason = self._normalize_plan_step(step, index)
            if skip_reason:
                skipped.append(skip_reason)
                self.memory.write("plan_step_skipped", skip_reason)
                continue
            executed.append(self._run_task(task))

        self.concept_linker.link_recent(10)
        assessment = self._run_self_assess_loop(goal)

        cycle_summary = {
            "goal": goal,
            "plan_length": len(plan),
            "executed_steps": len(executed),
            "skipped_steps": len(skipped),
            "skipped": skipped,
            "plan_error": plan_error,
            "results": executed,
        }
        if assessment is not None:
            cycle_summary["self_assessment"] = assessment
        self.memory.write("cycle_completed", cycle_summary)
        return cycle_summary

    def run_once(self) -> Dict[str, Any]:
        return self._autonomous_cycle()

    def run(self):
        print("[Aria] Autonomous self-improving runtime started.")

        cycle_count = 0
        while True:
            try:
                self._autonomous_cycle()
                cycle_count += 1
                if self.max_cycles is not None and cycle_count >= int(self.max_cycles):
                    break
                time.sleep(self.sleep_seconds)
            except KeyboardInterrupt:
                print("[Aria] Shutdown requested.")
                break
            except Exception as e:
                print("[Aria] Error in cycle:", e)
                time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    AriaRunner().run()
