from __future__ import annotations

import pytest

from core.agents.goal_evolution_agent import GoalEvolutionAgent
from core.agents.planner_agent import PlannerAgent
from core.memory.store import MemoryStore
from core.runner import AriaRunner
from core.task import Task

pytestmark = pytest.mark.unit


def test_runner_registers_expected_core_agents():
    runner = AriaRunner()

    assert set(runner.registry.names()) == {
        "planner_agent",
        "llm_agent",
        "tool_agent",
        "training_agent",
        "goal_evolution_agent",
    }


def test_goal_evolution_agent_returns_structured_goal():
    memory = MemoryStore()
    memory.write("task_result", {"status": "ok"})
    agent = GoalEvolutionAgent(memory)

    result = agent.execute(Task(type="goal_evolve"))

    assert result["agent"] == "goal_evolution_agent"
    assert result["goal"]
    assert memory.query("goal_evolved")


def test_planner_agent_returns_steps_with_ids():
    memory = MemoryStore()
    agent = PlannerAgent(memory)

    result = agent.execute(Task(type="plan", payload={"goal": "Draft a response"}))

    assert result["agent"] == "planner_agent"
    assert result["plan"]
    assert all(step["id"] for step in result["plan"])
    assert all(step["type"] for step in result["plan"])


def test_autonomous_cycle_records_goal_plan_and_execution():
    runner = AriaRunner()

    runner._autonomous_cycle()

    assert runner.memory.query("goal_created")
    assert runner.memory.query("plan_received")
    task_results = runner.memory.query("task_result")
    assert task_results
    assert task_results[-1]["data"]["result"]["agent"] == "llm_agent"
