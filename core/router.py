"""
Aria Intelligent Router
Scores agents dynamically and selects best execution target.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.agent import BaseAgent
from core.registry import AgentRegistry
from core.task import Task


_REFLECTION_TOKENS = (
    "reflect",
    "postmortem",
)
_RETROSPECT_TOKENS = (
    "retrospect",
    "meta learn",
    "meta-learn",
)
_PLAN_TOKENS = ("plan", "decompose", "strategy")
_TRAIN_TOKENS = ("train", "retrain", "fine-tune", "optimize model")
_FEEDBACK_TOKENS = ("feedback", "review", "rating")
_TOOL_TOKENS = ("tool", "run", "execute", "inspect")
_GOAL_TOKENS = ("goal", "improve next", "next goal")
_SUMMARIZE_TOKENS = ("summarize", "compress", "condense")
_CRITIQUE_TOKENS = (
    "critique",
    "evaluate response",
    "assess quality",
)
_REASON_TOKENS = (
    "reason",
    "explain",
    "chain of thought",
    "think through",
)
_DEBATE_TOKENS = ("debate", "challenge", "stress test", "counter")
_HYPOTHESIS_TOKENS = (
    "hypothesize",
    "generate hypothesis",
    "infer pattern",
)


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


class TaskRouter:
    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    def classify_intent(self, text: str) -> str:
        normalized = (text or "").lower()
        if _contains_any(normalized, _RETROSPECT_TOKENS):
            return "retrospect"
        if _contains_any(normalized, _REFLECTION_TOKENS):
            return "reflect"
        if _contains_any(normalized, _PLAN_TOKENS):
            return "plan"
        if _contains_any(normalized, _TRAIN_TOKENS):
            return "train"
        if _contains_any(normalized, _FEEDBACK_TOKENS):
            return "feedback"
        if _contains_any(normalized, _TOOL_TOKENS):
            return "tool"
        if _contains_any(normalized, _GOAL_TOKENS):
            return "goal_evolve"
        if _contains_any(normalized, _SUMMARIZE_TOKENS):
            return "summarize"
        if _contains_any(normalized, _CRITIQUE_TOKENS):
            return "critique"
        if _contains_any(normalized, _REASON_TOKENS):
            return "reason"
        if _contains_any(normalized, _DEBATE_TOKENS):
            return "debate"
        if _contains_any(normalized, _HYPOTHESIS_TOKENS):
            return "hypothesize"
        return "llm"

    def route_text(
        self,
        text: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        task_type = self.classify_intent(text)
        merged_payload: Dict[str, Any] = dict(payload or {})
        if task_type == "plan":
            merged_payload.setdefault("goal", text)
        elif task_type in {"feedback", "human_feedback"}:
            merged_payload.setdefault("message", text)
        elif task_type == "tool":
            merged_payload.setdefault("tool", text)
            merged_payload.setdefault("args", {})
        else:
            merged_payload.setdefault("prompt", text)
        return self.route(Task(type=task_type, payload=merged_payload))

    def route(self, task: Task) -> Dict[str, Any]:
        candidates = []

        for agent in self.registry.get_agents():
            score = self._score(agent, task)
            if score > 0:
                candidates.append((score, agent))

        if not candidates:
            return {
                "agent": None,
                "result": {"error": "No suitable agent found"},
            }

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_agent = candidates[0]
        result = best_agent.execute(task)

        return {
            "agent": best_agent.name,
            "score": best_score,
            "candidates": [
                {"agent": agent.name, "score": score}
                for score, agent in candidates
            ],
            "result": result,
        }

    def _score(self, agent: BaseAgent, task: Task) -> float:
        base = 0.0

        if hasattr(agent, "can_handle") and agent.can_handle(task):
            base = 1.0
        else:
            return 0.0

        if (
            task.type in {"llm", "chat", "reason"}
            and agent.name == "llm_agent"
        ):
            base += 0.5

        if (
            task.type in {"tool", "execute", "action"}
            and agent.name == "tool_agent"
        ):
            base += 0.5

        if (
            task.type in {"train", "feedback", "evaluate"}
            and agent.name == "training_agent"
        ):
            base += 0.5

        if (
            task.type in {"feedback", "human_feedback", "review"}
            and agent.name == "human_feedback_agent"
        ):
            base += 0.55

        if (
            task.type in {"plan", "goal", "decompose"}
            and agent.name == "planner_agent"
        ):
            base += 0.6

        if (
            task.type in {"goal_evolve", "new_goal"}
            and agent.name == "goal_evolution_agent"
        ):
            base += 0.6

        if (
            task.type in {"summarize", "compress", "condense"}
            and agent.name == "summarizer_agent"
        ):
            base += 0.6

        if (
            task.type in {"critique", "evaluate_response", "assess_quality"}
            and agent.name == "critique_agent"
        ):
            base += 0.6

        if (
            task.type in {"reason", "explain", "chain_of_thought"}
            and agent.name == "reasoning_agent"
        ):
            base += 0.6

        if (
            task.type in {"debate", "challenge", "stress_test"}
            and agent.name == "debate_agent"
        ):
            base += 0.6

        if (
            task.type in {"hypothesize", "infer", "generate_hypothesis"}
            and agent.name == "hypothesis_agent"
        ):
            base += 0.6

        if (
            task.type in {"retrospect", "meta_learn"}
            and agent.name == "reflection_agent"
        ):
            base += 0.6

        if task.type == "reflect" and agent.name == "reflection_agent":
            base += 0.55

        if task.type == "reflect" and agent.name == "goal_evolution_agent":
            base += 0.3

        if task.priority > 0:
            base += min(task.priority * 0.05, 0.25)

        return base
