import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.consensus_engine import (ConsensusConfig, Vote, compute_consensus,
                                     consensus_from_task_results)


def test_compute_consensus_majority_reached() -> None:
    votes = [
        Vote(agent_id="a1", choice="approve", confidence=0.9),
        Vote(agent_id="a2", choice="approve", confidence=0.8),
        Vote(agent_id="a3", choice="reject", confidence=0.2),
    ]

    result = compute_consensus(votes)

    assert result.reached is True
    assert result.winner == "approve"
    assert result.reason == "ok"
    assert result.winner_ratio > 0.6


def test_compute_consensus_below_threshold() -> None:
    votes = [
        Vote(agent_id="a1", choice="approve", confidence=0.51),
        Vote(agent_id="a2", choice="reject", confidence=0.49),
    ]

    result = compute_consensus(
        votes,
        config=ConsensusConfig(min_votes=2, approval_threshold=0.75),
    )

    assert result.reached is False
    assert result.winner is None
    assert result.reason == "below_threshold"


def test_compute_consensus_tie_detected() -> None:
    votes = [
        Vote(agent_id="a1", choice="approve", confidence=1.0),
        Vote(agent_id="a2", choice="reject", confidence=1.0),
    ]

    result = compute_consensus(
        votes,
        config=ConsensusConfig(min_votes=2, approval_threshold=0.5),
    )

    assert result.reached is False
    assert result.winner is None
    assert result.reason == "tie"


def test_compute_consensus_insufficient_votes() -> None:
    result = compute_consensus(
        [Vote(agent_id="a1", choice="approve", confidence=0.9)],
        config=ConsensusConfig(min_votes=2, approval_threshold=0.6),
    )

    assert result.reached is False
    assert result.reason == "insufficient_votes"


def test_compute_consensus_no_valid_votes() -> None:
    votes = [
        Vote(agent_id="a1", choice="", confidence=1.0),
        Vote(agent_id="a2", choice="   ", confidence=0.7),
    ]

    result = compute_consensus(votes)

    assert result.reached is False
    assert result.winner is None
    assert result.vote_count == 2
    assert result.reason == "no_valid_votes"


def test_compute_consensus_zero_total_weight() -> None:
    votes = [
        Vote(agent_id="a1", choice="approve", confidence=0.0, weight=1.0),
        Vote(agent_id="a2", choice="reject", confidence=0.4, weight=0.0),
    ]

    result = compute_consensus(votes)

    assert result.reached is False
    assert result.winner is None
    assert result.total_weight == 0.0
    assert result.reason == "zero_total_weight"


def test_consensus_from_task_results_success() -> None:
    task_results = {
        "agent_1": {"status": "success"},
        "agent_2": {"status": "success"},
        "agent_3": {"status": "failed"},
    }

    result = consensus_from_task_results(task_results)

    assert result.reached is True
    assert result.winner == "success"
    assert result.reason == "ok"


def test_consensus_from_task_results_failure() -> None:
    task_results = {
        "agent_1": {"status": "failed"},
        "agent_2": {"status": "failed"},
        "agent_3": {"status": "success"},
    }

    result = consensus_from_task_results(task_results)

    assert result.reached is True
    assert result.winner == "failure"
    assert result.reason == "ok"


def test_consensus_from_task_results_complete_status_counts_as_success() -> None:
    task_results = {
        "agent_1": {"status": "complete"},
        "agent_2": {"status": "completed"},
        "agent_3": {"status": "failed"},
    }

    result = consensus_from_task_results(task_results)

    assert result.reached is True
    assert result.winner == "success"
    assert result.reason == "ok"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
