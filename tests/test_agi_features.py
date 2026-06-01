from __future__ import annotations

import json
import sys
import threading
import types
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from core.agents.goal_evolution_agent import GoalEvolutionAgent
from core.agents.human_feedback_agent import HumanFeedbackAgent
from core.agents.llm_agent import LLMAgent
from core.agents.tool_agent import ToolRegistry
from core.agents.training_agent import TrainingAgent
from core.bus import AgentBus
from core.ingestion.pipeline import (
    DataQualityValidator,
    FileDataSource,
    HttpDataSource,
    IngestionPipeline,
)
from core.knowledge.graph import ConceptLinker, KnowledgeGraph, OntologyLoader
from core.llm.client import LLMClient
from core.memory.store import MemoryStore
from core.notifications import NotificationAdapter
from core.registry import AgentRegistry
from core.router import TaskRouter
from core.runner import AriaRunner
from core.task import Task


def _artifact_path(name: str) -> Path:
    root = Path(__file__).resolve().parent / "_artifacts"
    root.mkdir(exist_ok=True)
    return root / f"{name}-{uuid.uuid4().hex}"


class _JsonHandler(BaseHTTPRequestHandler):
    responses = {"GET": {"ok": True}, "POST": {"ok": True}}
    seen_headers = []
    seen_bodies = []

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(self.responses["GET"]).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        type(self).seen_headers.append(dict(self.headers))
        type(self).seen_bodies.append(body)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(self.responses["POST"]).encode("utf-8"))

    def log_message(self, format, *args):
        return


def _start_server(get_payload=None, post_payload=None):
    handler = type(
        "TestJsonHandler",
        (_JsonHandler,),
        {
            "responses": {
                "GET": get_payload or {"ok": True},
                "POST": post_payload or {"ok": True},
            },
            "seen_headers": [],
            "seen_bodies": [],
        },
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, handler


def test_memory_store_persists_events_with_sqlite_backend() -> None:
    db_path = _artifact_path("memory-store").with_suffix(".sqlite")
    try:
        memory = MemoryStore(db_path=str(db_path))
        event_id = memory.write("goal_created", {"goal": "persist this"})

        reloaded = MemoryStore(db_path=str(db_path))
        restored = reloaded.get(event_id)

        assert restored is not None
        assert restored["data"]["goal"] == "persist this"
    finally:
        if db_path.exists():
            db_path.unlink()


def test_ingestion_pipeline_supports_file_and_http_sources() -> None:
    jsonl_path = _artifact_path("ingestion").with_suffix(".jsonl")
    jsonl_path.write_text(
        '{"id": 1, "name": "alpha"}\n{"id": 2}\n',
        encoding="utf-8",
    )
    server, _handler = _start_server(get_payload=[{"id": 3, "name": "beta"}])
    try:
        memory = MemoryStore()
        validator = DataQualityValidator().required_fields(["id", "name"])
        pipeline = IngestionPipeline(
            sources=[
                FileDataSource(str(jsonl_path)),
                HttpDataSource(f"http://127.0.0.1:{server.server_port}"),
            ],
            memory=memory,
            validator=validator,
        )

        result = pipeline.run()

        assert result == {"ingested": 2, "rejected": 1}
        assert len(memory.query(event_type="ingested_record")) == 2
    finally:
        server.shutdown()
        server.server_close()
        if jsonl_path.exists():
            jsonl_path.unlink()


def test_knowledge_graph_linking_and_ontology_loading() -> None:
    memory = MemoryStore()
    memory.write("goal_created", {"goal": "improve planning"})
    graph = KnowledgeGraph()
    ConceptLinker(graph, memory).link_recent(5)

    ontology_path = _artifact_path("ontology").with_suffix(".json")
    ontology_path.write_text(
        json.dumps(
            {
                "entities": ["planner", {"name": "agent", "properties": {"kind": "runtime"}}],
                "relationships": [{"source": "planner", "target": "agent", "relation": "instance_of"}],
            }
        ),
        encoding="utf-8",
    )
    try:
        loader = OntologyLoader()
        loader.apply_to_graph(graph, loader.load(str(ontology_path)))

        assert "improve planning" in graph.neighbors("goal_created")
        assert graph.shortest_path("planner", "agent") == ["planner", "agent"]
        assert "improve planning" in graph.find_related("goal_created")
    finally:
        if ontology_path.exists():
            ontology_path.unlink()


def test_training_agent_self_assess_and_lora_dispatch() -> None:
    log_path = Path("logs") / "lora_signals.jsonl"
    original = log_path.read_text(encoding="utf-8") if log_path.exists() else None
    try:
        agent = TrainingAgent()
        train_result = agent.execute(Task(type="train", payload={"goal": "improve"}))
        eval_result = agent.execute(Task(type="evaluate", payload={"score": 0.4}))
        assessment = agent.self_assess(target_score=0.7)

        assert train_result["result"]["ack"] == "training signal recorded"
        assert eval_result["result"]["needs_retraining"] is True
        assert assessment["needs_retraining"] is True
        assert log_path.exists()
        assert '"goal": "improve"' in log_path.read_text(encoding="utf-8")
    finally:
        if original is None:
            if log_path.exists():
                log_path.unlink()
        else:
            log_path.write_text(original, encoding="utf-8")


def test_planner_agent_assigns_priority_metadata() -> None:
    router = TaskRouter(AgentRegistry())
    assert router.classify_intent("please plan this") == "plan"

    planner = AriaRunner(config={"sleep_seconds": 0}).registry.get("planner_agent")
    assert planner is not None

    plan = planner.execute(Task(type="plan", payload={"goal": "inspect context and answer"}))["plan"]
    assert all("confidence" in step and "risk" in step and "priority" in step for step in plan)
    assert plan[0]["priority"] >= plan[-1]["priority"]


def test_goal_evolution_agent_tracks_horizon() -> None:
    memory = MemoryStore()
    memory.write("task_result", {"message": "recent failure"})
    agent = GoalEvolutionAgent(memory, goal_horizon="short_term")

    result = agent.execute(Task(type="goal_evolve", payload={"horizon": "long_term"}))

    assert result["goal_horizon"] == "long_term"
    assert memory.last_of_type("goal_evolved")["data"]["goal_horizon"] == "long_term"


def test_llm_agent_reasoning_mode_returns_reasoning_chain() -> None:
    agent = LLMAgent()

    result = agent.execute(Task(type="reason", payload={"prompt": "Explain plan", "reasoning_mode": True}))

    assert result["reasoning_chain"]
    assert result["reasoning_chain"][0]["name"] == "analyze"
    assert result["output"] == "Simulated result for: Explain plan"


def test_llm_client_can_use_stubbed_real_provider(monkeypatch) -> None:
    stub = types.ModuleType("agi_provider")

    class _Provider:
        def complete(self, messages, stream=False):
            assert stream is False
            return "real provider response"

    stub.create_agi_provider = lambda model=None: _Provider()
    monkeypatch.setitem(sys.modules, "agi_provider", stub)
    monkeypatch.setenv("ARIA_USE_REAL_LLM", "1")

    client = LLMClient()

    assert client.complete([{"role": "user", "content": "hello"}]) == "real provider response"


def test_bus_feedback_router_notifications_and_remote_tool() -> None:
    bus = AgentBus()
    seen = []

    def _listener(message):
        seen.append(message["message"])
        return "ok"

    bus.subscribe("human_feedback", _listener)
    memory = MemoryStore()
    agent = HumanFeedbackAgent(memory, bus)
    feedback_result = agent.execute(Task(type="human_feedback", payload={"message": "looks good", "rating": 5}))
    bus.unsubscribe("human_feedback", _listener)

    registry = AgentRegistry()
    registry.register(agent)
    routed = TaskRouter(registry).route_text("feedback: keep going", {"message": "feedback: keep going"})

    server, handler = _start_server(post_payload={"status": "ok"})
    try:
        notifier = NotificationAdapter(f"http://127.0.0.1:{server.server_port}")
        notify_result = notifier.notify("cycle complete", {"ok": True})

        tool_registry = ToolRegistry()
        tool_registry.register_remote("remote_echo", f"http://127.0.0.1:{server.server_port}")
        remote_result = tool_registry.get("remote_echo")(message="hello")

        assert feedback_result["status"] == "recorded"
        assert seen == ["looks good"]
        assert routed["agent"] == "human_feedback_agent"
        assert notify_result["status"] == "sent"
        assert remote_result == {"status": "ok"}
        assert any("application/json" in headers.get("Content-Type", "") for headers in handler.seen_headers)
    finally:
        server.shutdown()
        server.server_close()


def test_runner_registers_knowledge_tools_and_self_assessment() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0, "target_score": 0.8})
    training_agent = runner.registry.get("training_agent")
    assert training_agent is not None
    training_agent.execute(Task(type="evaluate", payload={"score": 0.5}))

    result = runner.run_once()

    tool_agent = runner.registry.get("tool_agent")
    assert tool_agent is not None
    assert tool_agent.registry.has("knowledge_neighbors")
    assert "self_assessment" in result
    assert runner.memory.last_of_type("training_self_assessment") is not None

    related = tool_agent.execute(
        Task(type="tool", payload={"tool": "knowledge_related", "args": {"entity": "goal_created"}})
    )
    assert related["tool"] == "knowledge_related"


def test_summarizer_agent_summarizes_free_text() -> None:
    from core.agents.summarizer_agent import SummarizerAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    agent = SummarizerAgent(memory)

    result = agent.execute(
        Task(type="summarize", payload={"text": "The system processed 10 goals and completed 8 tasks."})
    )

    assert result["agent"] == "summarizer_agent"
    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert result["summary"]
    assert memory.last_of_type("summary_created") is not None


def test_summarizer_agent_summarizes_memory_events() -> None:
    from core.agents.summarizer_agent import SummarizerAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    memory.write("goal_created", {"goal": "improve accuracy"})
    memory.write("task_result", {"output": "done"})
    agent = SummarizerAgent(memory)

    result = agent.execute(Task(type="summarize", payload={}))

    assert result["agent"] == "summarizer_agent"
    assert isinstance(result["summary"], str)
    assert result["summary"]


def test_summarizer_agent_empty_memory_returns_default() -> None:
    from core.agents.summarizer_agent import SummarizerAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    agent = SummarizerAgent(memory)

    result = agent.execute(Task(type="summarize", payload={}))

    assert result["summary"] == "No context to summarize."


def test_summarizer_agent_can_handle_types() -> None:
    from core.agents.summarizer_agent import SummarizerAgent
    from core.memory.store import MemoryStore

    agent = SummarizerAgent(MemoryStore())
    for t in ("summarize", "compress", "condense"):
        assert agent.can_handle(Task(type=t, payload={}))
    assert not agent.can_handle(Task(type="plan", payload={}))


def test_critique_agent_evaluates_response() -> None:
    from core.agents.critique_agent import CritiqueAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    agent = CritiqueAgent(memory)

    result = agent.execute(
        Task(
            type="critique",
            payload={"response": "The model achieves 95% accuracy on the test set with minimal overfitting."},
        )
    )

    assert result["agent"] == "critique_agent"
    assert "score" in result
    assert 0.0 <= result["score"] <= 1.0
    assert isinstance(result["issues"], list)
    assert isinstance(result["suggestions"], list)
    assert "passed" in result
    assert isinstance(result["passed"], bool)
    assert memory.last_of_type("critique_created") is not None


def test_critique_agent_evaluates_plan() -> None:
    from core.agents.critique_agent import CritiqueAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    agent = CritiqueAgent(memory)
    plan = [{"type": "llm", "payload": {"prompt": "improve model"}}, {"type": "train", "payload": {}}]

    result = agent.execute(Task(type="critique", payload={"plan": plan}))

    assert result["agent"] == "critique_agent"
    assert "score" in result


def test_critique_agent_threshold_passed_flag() -> None:
    from core.agents.critique_agent import CritiqueAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    high_threshold_agent = CritiqueAgent(memory, threshold=0.99)

    result = high_threshold_agent.execute(Task(type="critique", payload={"response": "some content"}))

    # The simulated score is 0.75, which is below 0.99.
    assert result["passed"] is False

    low_threshold_agent = CritiqueAgent(MemoryStore(), threshold=0.0)
    result2 = low_threshold_agent.execute(Task(type="critique", payload={"response": "some content"}))
    assert result2["passed"] is True


def test_critique_agent_can_handle_types() -> None:
    from core.agents.critique_agent import CritiqueAgent
    from core.memory.store import MemoryStore

    agent = CritiqueAgent(MemoryStore())
    for t in ("critique", "evaluate_response", "assess_quality"):
        assert agent.can_handle(Task(type=t, payload={}))
    assert not agent.can_handle(Task(type="plan", payload={}))


def test_router_classifies_summarize_and_critique_intents() -> None:
    from core.registry import AgentRegistry
    from core.router import TaskRouter

    router = TaskRouter(AgentRegistry())
    assert router.classify_intent("please summarize the recent events") == "summarize"
    assert router.classify_intent("compress this context") == "summarize"
    assert router.classify_intent("critique the following response") == "critique"
    assert router.classify_intent("assess quality of this output") == "critique"


def test_runner_registers_summarizer_and_critique_agents() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    assert runner.registry.get("summarizer_agent") is not None
    assert runner.registry.get("critique_agent") is not None


def test_runner_routes_summarize_task() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    runner.memory.write("goal_created", {"goal": "reduce latency"})

    result = runner.router.route(Task(type="summarize", payload={"text": "System ran 5 cycles with 3 successes."}))

    assert result["agent"] == "summarizer_agent"
    assert "summary" in result["result"]


def test_runner_routes_critique_task() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})

    result = runner.router.route(Task(type="critique", payload={"response": "Model accuracy is 0.9."}))

    assert result["agent"] == "critique_agent"
    assert "score" in result["result"]


# ---------------------------------------------------------------------------
# ReasoningAgent tests
# ---------------------------------------------------------------------------


def test_reasoning_agent_free_text() -> None:
    from core.agents.reasoning_agent import ReasoningAgent
    from core.memory.store import MemoryStore

    agent = ReasoningAgent(MemoryStore())
    task = Task(type="reason", payload={"question": "Why is the sky blue?"})
    result = agent.execute(task)

    assert result["agent"] == "reasoning_agent"
    assert isinstance(result["steps"], list)
    assert len(result["steps"]) >= 1
    assert isinstance(result["conclusion"], str) and result["conclusion"]
    assert 0.0 <= result["confidence"] <= 1.0


def test_reasoning_agent_empty_question_fallback() -> None:
    from core.agents.reasoning_agent import ReasoningAgent
    from core.memory.store import MemoryStore

    agent = ReasoningAgent(MemoryStore())
    result = agent.execute(Task(type="reason", payload={}))

    assert result["agent"] == "reasoning_agent"
    assert result["steps"] == []
    assert "No question provided" in result["conclusion"]
    assert result["confidence"] == 0.0


def test_reasoning_agent_alternate_payload_keys() -> None:
    from core.agents.reasoning_agent import ReasoningAgent
    from core.memory.store import MemoryStore

    agent = ReasoningAgent(MemoryStore())
    result = agent.execute(Task(type="explain", payload={"prompt": "Explain gradient descent."}))

    assert result["agent"] == "reasoning_agent"
    assert isinstance(result["steps"], list)
    assert isinstance(result["conclusion"], str)


def test_reasoning_agent_can_handle_types() -> None:
    from core.agents.reasoning_agent import ReasoningAgent
    from core.memory.store import MemoryStore

    agent = ReasoningAgent(MemoryStore())
    for t in ("reason", "explain", "chain_of_thought"):
        assert agent.can_handle(Task(type=t, payload={}))
    assert not agent.can_handle(Task(type="plan", payload={}))


def test_reasoning_agent_writes_to_memory() -> None:
    from core.agents.reasoning_agent import ReasoningAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    agent = ReasoningAgent(memory)
    agent.execute(Task(type="reason", payload={"question": "What is AGI?"}))

    events = memory.last(5)
    types_seen = [e.get("type") for e in events]
    assert "reasoning_completed" in types_seen


# ---------------------------------------------------------------------------
# DebateAgent tests
# ---------------------------------------------------------------------------


def test_debate_agent_basic_challenge() -> None:
    from core.agents.debate_agent import DebateAgent
    from core.memory.store import MemoryStore

    agent = DebateAgent(MemoryStore())
    result = agent.execute(Task(type="debate", payload={"claim": "AGI will be achieved within 10 years."}))

    assert result["agent"] == "debate_agent"
    assert isinstance(result["counter_arguments"], list)
    assert len(result["counter_arguments"]) >= 1
    assert isinstance(result["weaknesses"], list)
    assert isinstance(result["verdict"], str) and result["verdict"]


def test_debate_agent_with_steelman() -> None:
    from core.agents.debate_agent import DebateAgent
    from core.memory.store import MemoryStore

    agent = DebateAgent(MemoryStore())
    result = agent.execute(Task(type="debate", payload={"claim": "Open-source models are safer.", "steelman": True}))

    assert isinstance(result["steelman"], str) and result["steelman"]


def test_debate_agent_without_steelman() -> None:
    from core.agents.debate_agent import DebateAgent
    from core.memory.store import MemoryStore

    agent = DebateAgent(MemoryStore())
    result = agent.execute(
        Task(type="stress_test", payload={"text": "Caching always improves performance.", "steelman": False})
    )

    assert result["agent"] == "debate_agent"
    assert result["steelman"] == ""


def test_debate_agent_empty_claim_fallback() -> None:
    from core.agents.debate_agent import DebateAgent
    from core.memory.store import MemoryStore

    agent = DebateAgent(MemoryStore())
    result = agent.execute(Task(type="debate", payload={}))

    assert result["agent"] == "debate_agent"
    assert result["counter_arguments"] == []
    assert "No claim provided" in result["verdict"]


def test_debate_agent_can_handle_types() -> None:
    from core.agents.debate_agent import DebateAgent
    from core.memory.store import MemoryStore

    agent = DebateAgent(MemoryStore())
    for t in ("debate", "challenge", "stress_test"):
        assert agent.can_handle(Task(type=t, payload={}))
    assert not agent.can_handle(Task(type="critique", payload={}))


def test_debate_agent_writes_to_memory() -> None:
    from core.agents.debate_agent import DebateAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    agent = DebateAgent(memory)
    agent.execute(Task(type="challenge", payload={"proposal": "All data should be public."}))

    events = memory.last(5)
    types_seen = [e.get("type") for e in events]
    assert "debate_completed" in types_seen


# ---------------------------------------------------------------------------
# Router intent classification for reasoning and debate
# ---------------------------------------------------------------------------


def test_router_classifies_reason_and_debate_intents() -> None:
    from core.registry import AgentRegistry
    from core.router import TaskRouter

    router = TaskRouter(AgentRegistry())
    assert router.classify_intent("reason through this problem") == "reason"
    assert router.classify_intent("explain how neural networks work") == "reason"
    assert router.classify_intent("chain of thought for this question") == "reason"
    assert router.classify_intent("debate whether AGI is near") == "debate"
    assert router.classify_intent("challenge this proposal") == "debate"
    assert router.classify_intent("stress test this design") == "debate"


# ---------------------------------------------------------------------------
# Runner integration — registration and routing
# ---------------------------------------------------------------------------


def test_runner_registers_reasoning_and_debate_agents() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    assert runner.registry.get("reasoning_agent") is not None
    assert runner.registry.get("debate_agent") is not None


def test_runner_routes_reason_task() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})

    result = runner.router.route(Task(type="reason", payload={"question": "Why does gradient descent converge?"}))

    assert result["agent"] == "reasoning_agent"
    assert "steps" in result["result"]
    assert "conclusion" in result["result"]


def test_runner_routes_debate_task() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})

    result = runner.router.route(Task(type="debate", payload={"claim": "Transformers will replace all classical NLP."}))

    assert result["agent"] == "debate_agent"
    assert "counter_arguments" in result["result"]
    assert "verdict" in result["result"]


# ---------------------------------------------------------------------------
# HypothesisAgent tests
# ---------------------------------------------------------------------------


def test_hypothesis_agent_from_observation() -> None:
    from core.agents.hypothesis_agent import HypothesisAgent
    from core.memory.store import MemoryStore

    agent = HypothesisAgent(MemoryStore())
    result = agent.execute(
        Task(
            type="hypothesize",
            payload={"observation": "Cycles with >5 steps complete faster than those with <3 steps."},
        )
    )

    assert result["agent"] == "hypothesis_agent"
    assert isinstance(result["hypotheses"], list)
    assert len(result["hypotheses"]) >= 1
    h = result["hypotheses"][0]
    assert "statement" in h and isinstance(h["statement"], str)
    assert "rationale" in h and isinstance(h["rationale"], str)
    assert "testable" in h and isinstance(h["testable"], bool)
    assert isinstance(result["summary"], str) and result["summary"]


def test_hypothesis_agent_from_memory_events() -> None:
    from core.agents.hypothesis_agent import HypothesisAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    memory.write("cycle_completed", {"goal": "reduce latency", "executed_steps": 4, "skipped_steps": 1})
    memory.write("cycle_completed", {"goal": "improve accuracy", "executed_steps": 3, "skipped_steps": 0})

    agent = HypothesisAgent(memory)
    result = agent.execute(Task(type="hypothesize", payload={}))

    assert result["agent"] == "hypothesis_agent"
    assert isinstance(result["hypotheses"], list)


def test_hypothesis_agent_empty_memory_fallback() -> None:
    from core.agents.hypothesis_agent import HypothesisAgent
    from core.memory.store import MemoryStore

    agent = HypothesisAgent(MemoryStore())
    result = agent.execute(Task(type="infer", payload={}))

    assert result["agent"] == "hypothesis_agent"
    assert result["hypotheses"] == []
    assert "No observations available" in result["summary"]


def test_hypothesis_agent_can_handle_types() -> None:
    from core.agents.hypothesis_agent import HypothesisAgent
    from core.memory.store import MemoryStore

    agent = HypothesisAgent(MemoryStore())
    for t in ("hypothesize", "infer", "generate_hypothesis"):
        assert agent.can_handle(Task(type=t, payload={}))
    assert not agent.can_handle(Task(type="plan", payload={}))


def test_hypothesis_agent_writes_to_memory() -> None:
    from core.agents.hypothesis_agent import HypothesisAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    agent = HypothesisAgent(memory)
    agent.execute(Task(type="hypothesize", payload={"observation": "Short cycles skip fewer steps."}))

    events = memory.last(5)
    assert any(e.get("type") == "hypothesis_generated" for e in events)


# ---------------------------------------------------------------------------
# ReflectionAgent tests
# ---------------------------------------------------------------------------


def test_reflection_agent_from_cycle_history() -> None:
    from core.agents.reflection_agent import ReflectionAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    for i in range(3):
        memory.write(
            "cycle_completed",
            {
                "goal": f"goal_{i}",
                "executed_steps": 4,
                "skipped_steps": 1,
                "self_assessment": {"score": 0.7 + i * 0.05},
            },
        )

    agent = ReflectionAgent(memory)
    result = agent.execute(Task(type="retrospect", payload={}))

    assert result["agent"] == "reflection_agent"
    assert isinstance(result["lessons"], list) and len(result["lessons"]) >= 1
    assert isinstance(result["patterns"], list)
    assert isinstance(result["adjustments"], list)
    assert isinstance(result["overall"], str) and result["overall"]


def test_reflection_agent_falls_back_to_general_events() -> None:
    from core.agents.reflection_agent import ReflectionAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    memory.write("goal_created", {"goal": "improve throughput"})
    memory.write("plan_created", {"plan": []})

    agent = ReflectionAgent(memory)
    result = agent.execute(Task(type="meta_learn", payload={}))

    assert result["agent"] == "reflection_agent"
    assert isinstance(result["lessons"], list)


def test_reflection_agent_empty_memory_fallback() -> None:
    from core.agents.reflection_agent import ReflectionAgent
    from core.memory.store import MemoryStore

    agent = ReflectionAgent(MemoryStore())
    result = agent.execute(Task(type="reflect", payload={}))

    assert result["agent"] == "reflection_agent"
    assert result["lessons"] == []
    assert "No cycle history available" in result["overall"]


def test_reflection_agent_can_handle_types() -> None:
    from core.agents.reflection_agent import ReflectionAgent
    from core.memory.store import MemoryStore

    agent = ReflectionAgent(MemoryStore())
    for t in ("reflect", "retrospect", "meta_learn"):
        assert agent.can_handle(Task(type=t, payload={}))
    assert not agent.can_handle(Task(type="plan", payload={}))


def test_reflection_agent_writes_to_memory() -> None:
    from core.agents.reflection_agent import ReflectionAgent
    from core.memory.store import MemoryStore

    memory = MemoryStore()
    memory.write("cycle_completed", {"goal": "reduce errors", "executed_steps": 5, "skipped_steps": 0})
    agent = ReflectionAgent(memory)
    agent.execute(Task(type="retrospect", payload={}))

    events = memory.last(10)
    assert any(e.get("type") == "reflection_completed" for e in events)


# ---------------------------------------------------------------------------
# Router intent classification for hypothesis and reflection
# ---------------------------------------------------------------------------


def test_router_classifies_hypothesis_and_retrospect_intents() -> None:
    from core.registry import AgentRegistry
    from core.router import TaskRouter

    router = TaskRouter(AgentRegistry())
    assert router.classify_intent("hypothesize why cycles are slow") == "hypothesize"
    assert router.classify_intent("generate hypothesis from patterns") == "hypothesize"
    assert router.classify_intent("infer pattern from data") == "hypothesize"
    assert router.classify_intent("retrospect on last cycle") == "retrospect"
    assert router.classify_intent("meta learn from history") == "retrospect"
    assert router.classify_intent("meta-learn from past cycles") == "retrospect"


# ---------------------------------------------------------------------------
# Runner integration — registration and routing
# ---------------------------------------------------------------------------


def test_runner_registers_hypothesis_and_reflection_agents() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    assert runner.registry.get("hypothesis_agent") is not None
    assert runner.registry.get("reflection_agent") is not None


def test_runner_routes_hypothesize_task() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    runner.memory.write("cycle_completed", {"goal": "reduce latency", "executed_steps": 4, "skipped_steps": 1})

    result = runner.router.route(Task(type="hypothesize", payload={"observation": "Latency spikes after step 3."}))

    assert result["agent"] == "hypothesis_agent"
    assert "hypotheses" in result["result"]
    assert "summary" in result["result"]


def test_runner_routes_retrospect_task() -> None:
    runner = AriaRunner(config={"sleep_seconds": 0})
    runner.memory.write(
        "cycle_completed",
        {"goal": "improve accuracy", "executed_steps": 6, "skipped_steps": 0},
    )

    result = runner.router.route(Task(type="retrospect", payload={}))

    assert result["agent"] == "reflection_agent"
    assert "lessons" in result["result"]
    assert "overall" in result["result"]
