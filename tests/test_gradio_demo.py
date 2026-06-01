import importlib.util
import os
import json
import sys


def load_module():
    path = os.path.join(os.path.dirname(__file__), "..", "scripts", "gradio_demo.py")
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location("gradio_demo", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gradio_demo module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_chat_providers_module():
    path = os.path.join(os.path.dirname(__file__), "..", "ai-projects", "chat-cli", "src", "chat_providers.py")
    path = os.path.abspath(path)
    spec = importlib.util.spec_from_file_location("chat_providers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load chat_providers module")
    module = importlib.util.module_from_spec(spec)
    # Temporarily register under the canonical name so any self-referential
    # imports resolve during execution, then restore the original entry. This
    # prevents clobbering the shared `chat_providers` module that other tests
    # import at module load time and patch via `unittest.mock.patch`; replacing
    # it here would silently break those patches (test pollution).
    original = sys.modules.get(spec.name)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if original is not None:
            sys.modules[spec.name] = original
        else:
            sys.modules.pop(spec.name, None)
    return module


def test_save_and_load(tmp_path):
    m = load_module()
    conv_dir = tmp_path / "conv"
    # Point module to a temp conv dir
    m.CONV_DIR = str(conv_dir)
    m.LATEST_PATH = os.path.join(m.CONV_DIR, "latest.json")
    hist = [{"user": "hi", "assistant": "hello", "user_ts": "u", "assistant_ts": "a"}]
    fname = m.save_conversation_json(hist, "testsession")
    assert os.path.exists(fname)
    # load latest via helper
    display, loaded = m.load_latest_conversation()
    assert loaded == hist
    assert isinstance(display, list)
    assert display and "hi" in display[0][0]
    # Latest path should exist
    assert os.path.exists(m.LATEST_PATH)


def test_respond_simulation():
    m = load_module()
    # call respond directly in simulation mode
    chat_history: list = []
    hist_state: list = []
    import types
    gen = m.respond("hello", chat_history, hist_state, True, "auto", None, 0.5, 256, "English", "Aria", False, 100, "test")
    # respond is a generator-function (contains yield); collect final output
    if isinstance(gen, types.GeneratorType):
        last = None
        try:
            while True:
                last = next(gen)
        except StopIteration as e:
            if hasattr(e, 'value') and e.value is not None:
                last = e.value
        out = last
    else:
        out = gen
    assert isinstance(out, tuple)
    chatbot, cleared_input, new_hist_state, provider_info, status = out
    assert cleared_input == ""
    assert isinstance(new_hist_state, list)
    assert new_hist_state and new_hist_state[-1]["assistant"].startswith("[Aria-")


def test_default_provider_prefers_qai_when_quantum_model_is_configured(monkeypatch):
    m = load_module()
    monkeypatch.setenv("QAI_QUANTUM_MODEL_PATH", "data_out/quantum_llm_training")
    assert m.default_provider_choice() == "qai"


def test_default_provider_stays_auto_without_quantum_model(monkeypatch):
    m = load_module()
    monkeypatch.delenv("QAI_QUANTUM_MODEL_PATH", raising=False)
    monkeypatch.delenv("QAI_QUANTUM_MODEL", raising=False)
    assert m.default_provider_choice() == "auto"


def test_provider_readiness_note_reflects_quantum_configuration(monkeypatch):
    m = load_module()
    monkeypatch.setenv("QAI_QUANTUM_MODEL_PATH", "data_out/qai_quantum")
    assert m.provider_readiness_note() == "QAI quantum backend ready: data_out/qai_quantum"


def test_provider_readiness_note_reflects_missing_configuration(monkeypatch):
    m = load_module()
    monkeypatch.delenv("QAI_QUANTUM_MODEL_PATH", raising=False)
    monkeypatch.delenv("QAI_QUANTUM_MODEL", raising=False)
    assert m.provider_readiness_note() == "QAI quantum backend not configured. Set QAI_QUANTUM_MODEL_PATH or choose auto."


def test_provider_diagnostics_summary_reflects_qai_configuration(monkeypatch):
    m = load_module()
    monkeypatch.setenv("QAI_QUANTUM_MODEL_PATH", "data_out/qai_quantum")
    assert m.provider_diagnostics_summary() == "Provider: QAI quantum alias active · QAI quantum backend ready: data_out/qai_quantum"


def test_provider_diagnostics_summary_reflects_auto_mode(monkeypatch):
    m = load_module()
    monkeypatch.delenv("QAI_QUANTUM_MODEL_PATH", raising=False)
    monkeypatch.delenv("QAI_QUANTUM_MODEL", raising=False)
    assert m.provider_diagnostics_summary() == "Provider: auto · QAI quantum backend not configured. Set QAI_QUANTUM_MODEL_PATH or choose auto."


def test_qai_provider_alias_maps_to_quantum_provider():
    chat_providers = load_chat_providers_module()
    assert chat_providers._PROVIDER_ALIASES["qai"] == "quantum"
    assert "qai" in chat_providers._KNOWN_PROVIDER_CHOICES


def test_repo_automation_status_summary_reflects_live_status(monkeypatch):
    m = load_module()
    monkeypatch.setattr(
        m,
        "load_repo_automation_status",
        lambda: {
            "components_running": {"aria": True, "training": True, "quantum": False},
            "errors": ["example error"],
            "uptime_seconds": 3661,
            "generated_at": "2026-05-31T23:50:00Z",
            "config_paths": {"quantum": "config/quantum/quantum_autorun.yaml"},
        },
    )

    summary = m.repo_automation_status_summary()
    assert "Repo automation: 2/3 components running" in summary
    assert "uptime 1:01:01" in summary
    assert "errors 1" in summary
    assert "active: aria, training" in summary
    assert "updated: 2026-05-31T23:50:00Z" in summary
    assert "quantum: config/quantum/quantum_autorun.yaml" in summary


def test_repo_automation_status_summary_handles_missing_status(monkeypatch):
    m = load_module()
    monkeypatch.setattr(m, "load_repo_automation_status", lambda: None)

    assert m.repo_automation_status_summary().startswith("Repo automation: no status available.")


def test_repo_automation_actions_markdown_lists_supported_commands():
    m = load_module()

    actions = m.repo_automation_actions_markdown()
    assert "--start" in actions
    assert "--status" in actions
    assert "--stop" in actions
    assert "--validate" in actions


def test_repo_automation_next_step_reflects_status(monkeypatch):
    m = load_module()
    monkeypatch.setattr(
        m,
        "load_repo_automation_status",
        lambda: {
            "components_running": {"aria": True, "training": True, "quantum": False},
            "errors": [],
        },
    )

    assert "remaining components online" in m.repo_automation_next_step()


def test_repo_automation_next_step_reflects_validation_when_errors_present(monkeypatch):
    m = load_module()
    monkeypatch.setattr(
        m,
        "load_repo_automation_status",
        lambda: {
            "components_running": {"aria": True, "training": True, "quantum": True},
            "errors": ["problem"],
        },
    )

    assert "--validate" in m.repo_automation_next_step()


def test_run_repo_automation_command_formats_stdout(monkeypatch):
    m = load_module()

    class Result:
        returncode = 0
        stdout = "Repository Automation Status\nStarted: 2026-05-31T23:50:00Z"
        stderr = ""

    monkeypatch.setattr(m.subprocess, "run", lambda *args, **kwargs: Result())

    output = m.run_repo_automation_command("--status")
    assert "python scripts/repo_automation.py --status" in output
    assert "Exit code: `0`" in output
    assert "Repository Automation Status" in output


def test_run_repo_automation_command_formats_stderr(monkeypatch):
    m = load_module()

    class Result:
        returncode = 1
        stdout = ""
        stderr = "validation failed"

    monkeypatch.setattr(m.subprocess, "run", lambda *args, **kwargs: Result())

    output = m.run_repo_automation_command("--validate")
    assert "Repo automation command failed." in output
    assert "Exit code: `1`" in output
    assert "validation failed" in output
