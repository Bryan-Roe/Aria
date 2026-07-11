"""Tests for the consolidated auto-merge workflow and eligibility composite action.

Covers:
- Consolidated auto-merge.yml has the correct dual trigger (pull_request + check_run).
- github-actions[bot] PRs are auto-prepared for merge by adding `autofix` and
  marking draft PRs ready for review.
- merge-on-gate-pass job filters on the canonical check name and conclusion.
- enable / disable jobs guard against forks and drafts.
- bot-approve job auto-runs for github-actions[bot] and stays variable-gated for
  other bot actors.
- auto-merge-on-ci.yml is a stub (no longer watches 'AGI smoke' workflow_run).
- check-auto-merge-eligibility composite action has required inputs and outputs.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_auto_merge() -> dict:
    return _load_yaml(WORKFLOWS_DIR / "auto-merge.yml")


def _load_auto_merge_on_ci() -> dict:
    return _load_yaml(WORKFLOWS_DIR / "auto-merge-on-ci.yml")


def _load_eligibility_action() -> dict:
    return _load_yaml(ACTIONS_DIR / "check-auto-merge-eligibility" / "action.yml")


# ---------------------------------------------------------------------------
# Helpers — trigger extraction
# ---------------------------------------------------------------------------


def _get_triggers(wf: dict) -> dict:
    """Return the workflow trigger mapping, handling the YAML 'on' → True quirk.

    PyYAML 5.x parses the bare YAML key ``on`` as boolean ``True`` (YAML 1.1
    core schema); GitHub Actions YAML uses ``on`` as the trigger block key.
    """
    return wf.get(True, wf.get("on", {}))


# ---------------------------------------------------------------------------
# auto-merge.yml — triggers
# ---------------------------------------------------------------------------


def test_auto_merge_has_pull_request_trigger() -> None:
    wf = _load_auto_merge()
    assert "pull_request" in _get_triggers(wf), "auto-merge.yml must trigger on pull_request events"


def test_auto_merge_has_check_run_trigger() -> None:
    wf = _load_auto_merge()
    assert "check_run" in _get_triggers(wf), (
        "auto-merge.yml must trigger on check_run events so it fires when 'All Gates Passed' completes"
    )


def test_auto_merge_has_schedule_trigger() -> None:
    wf = _load_auto_merge()
    assert "schedule" in _get_triggers(wf), "auto-merge.yml must trigger on schedule for open PR finishing sweeps"


def test_auto_merge_has_workflow_dispatch_trigger() -> None:
    wf = _load_auto_merge()
    assert "workflow_dispatch" in _get_triggers(wf), "auto-merge.yml must support manual dispatch for open PR finishing"


def test_auto_merge_check_run_trigger_on_completed() -> None:
    wf = _load_auto_merge()
    check_run = _get_triggers(wf)["check_run"]
    assert "completed" in check_run.get("types", []), "check_run trigger must include the 'completed' type"


def test_auto_merge_pull_request_trigger_includes_labeled_unlabeled() -> None:
    wf = _load_auto_merge()
    pr_types = _get_triggers(wf)["pull_request"].get("types", [])
    assert "labeled" in pr_types, "pull_request trigger must include 'labeled'"
    assert "unlabeled" in pr_types, "pull_request trigger must include 'unlabeled'"


# ---------------------------------------------------------------------------
# auto-merge.yml — jobs present
# ---------------------------------------------------------------------------


def test_auto_merge_has_enable_job() -> None:
    wf = _load_auto_merge()
    assert "enable" in wf["jobs"], "auto-merge.yml must have an 'enable' job"


def test_auto_merge_has_prepare_github_actions_job() -> None:
    wf = _load_auto_merge()
    assert "prepare-github-actions-pr" in wf["jobs"], "auto-merge.yml must prepare github-actions[bot] PRs"


def test_auto_merge_has_disable_job() -> None:
    wf = _load_auto_merge()
    assert "disable" in wf["jobs"], "auto-merge.yml must have a 'disable' job"


def test_auto_merge_has_merge_on_gate_pass_job() -> None:
    wf = _load_auto_merge()
    assert "merge-on-gate-pass" in wf["jobs"], "auto-merge.yml must have a 'merge-on-gate-pass' job"


def test_auto_merge_has_bot_approve_job() -> None:
    wf = _load_auto_merge()
    assert "bot-approve" in wf["jobs"], "auto-merge.yml must have a 'bot-approve' job"


def test_auto_merge_has_finish_open_prs_job() -> None:
    wf = _load_auto_merge()
    assert "finish-open-prs" in wf["jobs"], "auto-merge.yml must have a 'finish-open-prs' job"


# ---------------------------------------------------------------------------
# prepare-github-actions-pr — auto-ready + label for github-actions[bot]
# ---------------------------------------------------------------------------


def test_prepare_job_targets_github_actions_bot() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["prepare-github-actions-pr"].get("if", "")
    assert "github-actions[bot]" in job_if, "prepare job must target github-actions[bot] PR authors"


def test_prepare_job_guards_against_forks() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["prepare-github-actions-pr"].get("if", "")
    assert "head.repo.full_name == github.repository" in job_if, "prepare job must guard against fork PRs"


def test_prepare_job_skips_unlabeled_event_replays() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["prepare-github-actions-pr"].get("if", "")
    assert "github.event.action != 'unlabeled'" in job_if, "prepare job must skip unlabeled events"


def test_prepare_job_adds_autofix_label_and_marks_ready() -> None:
    wf = _load_auto_merge()
    steps = wf["jobs"]["prepare-github-actions-pr"]["steps"]
    script_step = next(step for step in steps if step.get("name") == "Ready PR and apply autofix label")
    script = script_step["with"]["script"]
    assert "labels: ['autofix']" in script, "prepare job must add the autofix label when missing"
    assert "markPullRequestReadyForReview" in script, "prepare job must mark draft PRs ready for review"


# ---------------------------------------------------------------------------
# merge-on-gate-pass — correct check filtering
# ---------------------------------------------------------------------------


def test_merge_on_gate_pass_filters_check_run_event() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["merge-on-gate-pass"].get("if", "")
    assert "github.event_name == 'check_run'" in job_if, (
        "merge-on-gate-pass must filter on github.event_name == 'check_run'"
    )


def test_merge_on_gate_pass_filters_all_gates_passed_name() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["merge-on-gate-pass"].get("if", "")
    assert "All Gates Passed" in job_if, (
        "merge-on-gate-pass must filter on check_run.name == 'All Gates Passed' (the canonical fan-in job name from merge-gate.yml)"
    )


def test_merge_on_gate_pass_filters_success_conclusion() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["merge-on-gate-pass"].get("if", "")
    assert "success" in job_if, "merge-on-gate-pass must only fire when the check_run conclusion is 'success'"


def test_merge_on_gate_pass_has_write_permissions() -> None:
    wf = _load_auto_merge()
    perms = wf["jobs"]["merge-on-gate-pass"].get("permissions", {})
    assert perms.get("contents") == "write", "merge-on-gate-pass needs contents:write to perform merges"
    assert perms.get("pull-requests") == "write", "merge-on-gate-pass needs pull-requests:write to post comments"


# ---------------------------------------------------------------------------
# enable job — fork and draft guards
# ---------------------------------------------------------------------------


def test_enable_job_guards_against_forks() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["enable"].get("if", "")
    assert "head.repo.full_name == github.repository" in job_if, (
        "enable job must guard against fork PRs by checking head.repo.full_name == github.repository"
    )


def test_enable_job_guards_against_drafts() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["enable"].get("if", "")
    assert "draft" in job_if, "enable job must guard against draft PRs"


def test_enable_job_fires_on_pull_request_event() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["enable"].get("if", "")
    assert "github.event_name == 'pull_request'" in job_if, (
        "enable job must check github.event_name == 'pull_request' to avoid running on check_run events"
    )


# ---------------------------------------------------------------------------
# disable job — fork guard and label conditions
# ---------------------------------------------------------------------------


def test_disable_job_guards_against_forks() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["disable"].get("if", "")
    assert "head.repo.full_name == github.repository" in job_if, "disable job must guard against fork PRs"


def test_disable_job_requires_unlabeled_action() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["disable"].get("if", "")
    assert "unlabeled" in job_if, "disable job must check for the 'unlabeled' action"


def test_disable_job_checks_no_remaining_label() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["disable"].get("if", "")
    # Must verify both labels are absent before disabling
    assert "auto-merge" in job_if, "disable job must check that 'auto-merge' label is no longer present"
    assert "autofix" in job_if, "disable job must check that 'autofix' label is no longer present"


# ---------------------------------------------------------------------------
# bot-approve job — variable guard and actor allowlist
# ---------------------------------------------------------------------------


def test_bot_approve_requires_variable_gate_for_other_bots() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["bot-approve"].get("if", "")
    assert "AUTO_MERGE_BOT_APPROVE" in job_if, "bot-approve job must still support the AUTO_MERGE_BOT_APPROVE gate"


def test_bot_approve_auto_runs_for_github_actions_bot() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["bot-approve"].get("if", "")
    assert "github-actions[bot]" in job_if, "bot-approve job must auto-run for github-actions[bot] PRs"


def test_bot_approve_guards_against_forks() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["bot-approve"].get("if", "")
    assert "head.repo.full_name == github.repository" in job_if, "bot-approve must guard against fork PRs"


def test_bot_approve_skips_drafts() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["bot-approve"].get("if", "")
    assert "draft" in job_if, "bot-approve must skip draft PRs"


def test_bot_approve_allowlist_defined_in_env() -> None:
    wf = _load_auto_merge()
    env = wf.get("env", {})
    assert "BOT_APPROVE_ALLOWLIST" in env, "BOT_APPROVE_ALLOWLIST must be declared in the workflow-level env block"
    allowlist = env["BOT_APPROVE_ALLOWLIST"]
    assert "github-actions[bot]" in allowlist, "github-actions[bot] must be in BOT_APPROVE_ALLOWLIST"
    assert "copilot-swe-agent[bot]" in allowlist, "copilot-swe-agent[bot] must be in BOT_APPROVE_ALLOWLIST"


# ---------------------------------------------------------------------------
# finish-open-prs job — scheduled/manual open PR finishing
# ---------------------------------------------------------------------------


def test_finish_open_prs_runs_only_on_schedule_or_dispatch() -> None:
    wf = _load_auto_merge()
    job_if = wf["jobs"]["finish-open-prs"].get("if", "")
    assert "github.event_name == 'schedule'" in job_if, "finish-open-prs must run on schedule events"
    assert "github.event_name == 'workflow_dispatch'" in job_if, "finish-open-prs must run on workflow_dispatch events"


def test_finish_open_prs_merges_via_squash() -> None:
    wf = _load_auto_merge()
    steps = wf["jobs"]["finish-open-prs"]["steps"]
    script_step = next((step for step in steps if step.get("name") == "Merge eligible open PRs"), None)
    assert script_step is not None, "finish-open-prs must include the 'Merge eligible open PRs' step"
    script = script_step["with"]["script"]
    assert "pulls.list" in script, "finish-open-prs must enumerate open pull requests"
    assert "merge_method: 'squash'" in script, "finish-open-prs must squash-merge eligible pull requests"


# ---------------------------------------------------------------------------
# auto-merge-on-ci.yml — is now a stub, not watching AGI smoke
# ---------------------------------------------------------------------------


def test_auto_merge_on_ci_no_longer_watches_agi_smoke() -> None:
    wf = _load_auto_merge_on_ci()
    triggers = wf.get("on", {})
    # The old trigger was workflow_run: ["AGI smoke"].
    # The stub should NOT have a workflow_run trigger pointing at AGI smoke.
    if "workflow_run" in triggers:
        watched = triggers["workflow_run"].get("workflows", [])
        assert "AGI smoke" not in watched, (
            "auto-merge-on-ci.yml must no longer watch 'AGI smoke' via workflow_run; "
            "that logic has moved to merge-on-gate-pass in auto-merge.yml"
        )


def test_auto_merge_on_ci_stub_has_no_automatic_trigger() -> None:
    """The stub must not fire automatically to avoid consuming CI minutes."""
    wf = _load_auto_merge_on_ci()
    triggers = wf.get("on", {})
    automatic_keys = {"push", "pull_request", "workflow_run", "schedule", "check_run", "check_suite"}
    active = automatic_keys & set(triggers.keys())
    assert not active, (
        f"auto-merge-on-ci.yml stub must not have automatic triggers; found: {active}. "
        "The workflow should only be manually dispatchable (workflow_dispatch)."
    )


# ---------------------------------------------------------------------------
# check-auto-merge-eligibility composite action
# ---------------------------------------------------------------------------


def test_eligibility_action_exists() -> None:
    action_path = ACTIONS_DIR / "check-auto-merge-eligibility" / "action.yml"
    assert action_path.exists(), "check-auto-merge-eligibility/action.yml must exist"


def test_eligibility_action_has_pr_number_input() -> None:
    action = _load_eligibility_action()
    inputs = action.get("inputs", {})
    assert "pr-number" in inputs, "eligibility action must define a 'pr-number' input"
    assert inputs["pr-number"].get("required") is True, "'pr-number' input must be required"


def test_eligibility_action_has_github_token_input() -> None:
    action = _load_eligibility_action()
    inputs = action.get("inputs", {})
    assert "github-token" in inputs, "eligibility action must define a 'github-token' input"


def test_eligibility_action_outputs_eligible() -> None:
    action = _load_eligibility_action()
    outputs = action.get("outputs", {})
    assert "eligible" in outputs, "eligibility action must output 'eligible'"


def test_eligibility_action_outputs_reason() -> None:
    action = _load_eligibility_action()
    outputs = action.get("outputs", {})
    assert "reason" in outputs, "eligibility action must output 'reason'"


def test_eligibility_action_is_composite() -> None:
    action = _load_eligibility_action()
    assert action.get("runs", {}).get("using") == "composite", "eligibility action must use 'composite' runner"


def test_eligibility_action_checks_draft() -> None:
    action_path = ACTIONS_DIR / "check-auto-merge-eligibility" / "action.yml"
    content = action_path.read_text(encoding="utf-8")
    assert "draft" in content.lower(), "eligibility action script must check for draft status"


def test_eligibility_action_checks_base_branch() -> None:
    action_path = ACTIONS_DIR / "check-auto-merge-eligibility" / "action.yml"
    content = action_path.read_text(encoding="utf-8")
    assert "main" in content, "eligibility action must verify the PR targets 'main'"


def test_eligibility_action_checks_fork() -> None:
    action_path = ACTIONS_DIR / "check-auto-merge-eligibility" / "action.yml"
    content = action_path.read_text(encoding="utf-8")
    assert "fork" in content.lower(), "eligibility action must guard against fork PRs"


def test_eligibility_action_checks_label() -> None:
    action_path = ACTIONS_DIR / "check-auto-merge-eligibility" / "action.yml"
    content = action_path.read_text(encoding="utf-8")
    assert "auto-merge" in content, "eligibility action must verify the 'auto-merge' label"
    assert "autofix" in content, "eligibility action must verify the 'autofix' label"


def test_eligibility_action_checks_changes_requested() -> None:
    action_path = ACTIONS_DIR / "check-auto-merge-eligibility" / "action.yml"
    content = action_path.read_text(encoding="utf-8")
    assert "CHANGES_REQUESTED" in content, "eligibility action must block on CHANGES_REQUESTED reviews"
