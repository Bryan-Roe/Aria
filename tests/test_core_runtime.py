"""Focused tests for the lightweight core runtime package."""

from __future__ import annotations

import pytest

from core.agents.goal_evolution_agent import GoalEvolutionAgent
from core.agents.llm_agent import LLMAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.tool_agent import ToolAgent, ToolRegistry
from core.agents.training_agent import TrainingAgent
from core.memory.store import MemoryStore
from core.queue import TaskQueue
from core.registry import AgentRegistry
from core.router import TaskRouter
from core.runner import AriaRunner
from core.task import Task


def test_task_defaults_and_validation() -> None:
    task = Task(type="llm", payload={"prompt": "hello"})

    assert task.id
    assert task.priority == 0
    assert task.to_dict()["payload"] == {"prompt": "hello"}

    with pytest.raises(ValueError):
        Task(type="  ")


def test_agent_registry_rejects_duplicate_names() -> None:
    memory = MemoryStore()
    registry = AgentRegistry()

    registry.register(PlannerAgent(memory))

    with pytest.raises(ValueError):
        registry.register(PlannerAgent(memory))


def test_planner_agent_returns_structured_plan() -> None:
    memory = MemoryStore()
    memory.write("goal_created", {"goal": "improve local tool execution"})
    agent = PlannerAgent(memory)

    result = agent.execute(Task(type="plan", payload={"goal": "Use a tool to inspect files"}))
    plan = result["plan"]

    assert len(plan) >= 2
    assert all(step["id"] for step in plan)
    assert {step["type"] for step in plan} >= {"llm", "tool"}


def test_planner_agent_reports_missing_goal_without_invalid_steps() -> None:
    memory = MemoryStore()
    agent = PlannerAgent(memory)

    result = agent.execute(Task(type="plan", payload={}))

    assert result["error"] == "No goal provided"
    assert result["plan"] == []
    assert memory.last_of_type("plan_created")["data"]["error"] == "No goal provided"


def test_goal_evolution_agent_returns_goal() -> None:
    memory = MemoryStore()
    memory.write("plan_created", {"plan": [{"type": "llm"}]})
    agent = GoalEvolutionAgent(memory)

    result = agent.execute(Task(type="goal_evolve"))

    assert result["goal"]
    assert isinstance(result["goal"], str)


def test_llm_agent_uses_structured_core_client_output() -> None:
    agent = LLMAgent()

    result = agent.execute(Task(type="llm", payload={"prompt": "Verify this design"}))

    assert result["output"] == "Simulated result for: Verify this design"
    assert result["analysis"] == "Processed: Verify this design"
    assert "execute_solution" in result["steps"]


def test_tool_agent_reports_available_tools_on_error() -> None:
    registry = ToolRegistry()
    registry.register("echo", lambda text: text)
    agent = ToolAgent(registry)

    result = agent.execute(Task(type="tool", payload={"tool": "missing", "args": {}}))

    assert result["error"] == "Tool not found: missing"
    assert result["available_tools"] == ["echo"]


def test_tool_agent_rejects_non_mapping_args() -> None:
    agent = ToolAgent()

    result = agent.execute(Task(type="tool", payload={"tool": "anything", "args": ["x"]}))

    assert result["error"] == "Tool args must be a dictionary"


def test_router_prioritizes_matching_agent_types() -> None:
    memory = MemoryStore()
    registry = AgentRegistry()
    planner = PlannerAgent(memory)
    llm = LLMAgent()
    registry.register(planner)
    registry.register(llm)
    router = TaskRouter(registry)

    result = router.route(Task(type="plan", payload={"goal": "Investigate files"}))

    assert result["agent"] == "planner_agent"
    assert result["candidates"][0]["agent"] == "planner_agent"


def test_training_agent_summary_tracks_signal_counts() -> None:
    agent = TrainingAgent()

    train_result = agent.execute(Task(type="train", payload={"goal": "improve"}))
    eval_result = agent.execute(Task(type="evaluate", payload={"score": 0.8}))

    assert train_result["summary"]["counts"]["train"] == 1
    assert eval_result["summary"]["counts"]["train"] == 1
    assert eval_result["summary"]["counts"]["evaluate"] == 1
    assert eval_result["summary"]["latest_signal"] == "evaluate"


def test_runner_run_once_executes_cycle_and_records_memory() -> None:
    runner = AriaRunner(config={"max_cycles": 1, "sleep_seconds": 0})

    result = runner.run_once()

    assert result["goal"]
    assert result["plan_length"] >= 1
    assert result["executed_steps"] == len(result["results"])
    assert runner.memory.last_of_type("cycle_completed") is not None


def test_runner_registers_default_tooling() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    tool_agent = runner.registry.get("tool_agent")

    assert tool_agent is not None
    assert tool_agent.registry.has("inspect_context")
    assert tool_agent.registry.has("recent_events")


def test_runner_default_inspect_context_tool_uses_memory() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    runner.memory.write("goal_created", {"goal": "improve runtime"})
    tool_agent = runner.registry.get("tool_agent")

    assert tool_agent is not None
    result = tool_agent.execute(
        Task(
            type="tool",
            payload={"tool": "inspect_context", "args": {"goal": "check status"}},
        )
    )

    assert result["tool"] == "inspect_context"
    assert result["output"]["goal"] == "check status"
    assert result["output"]["event_counts"]["goal_created"] == 1


def test_runner_skips_invalid_plan_steps_and_records_reason() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    planner = runner.registry.get("planner_agent")

    assert planner is not None

    def _bad_plan(_task: Task) -> dict:
        return {
            "agent": "planner_agent",
            "task_id": "planner",
            "goal": "bad plan",
            "plan": [{"payload": {}}, "oops", {"type": "llm", "payload": {"prompt": "ok"}}],
        }

    planner.execute = _bad_plan  # type: ignore[method-assign]

    result = runner.run_once()

    assert result["executed_steps"] >= 1
    assert result["skipped_steps"] == 2
    assert runner.memory.last_of_type("plan_step_skipped") is not None


@pytest.mark.asyncio
async def test_task_queue_processes_tasks_and_stops_cleanly() -> None:
    queue = TaskQueue(max_workers=2)
    processed: list[str] = []

    async def handler(task: str) -> None:
        processed.append(task)

    await queue.start(handler)
    await queue.add_task("a")
    await queue.add_task("b")
    await queue.stop()

    assert sorted(processed) == ["a", "b"]
    assert queue.pending_count() == 0
