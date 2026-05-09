from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

_SUCCESS_STATUSES = {"success", "complete", "completed", "ok", "passed"}


@dataclass(frozen=True)
class Vote:
    """Single agent vote for a choice.

    Attributes:
        agent_id: Unique identifier for the voter.
        choice: Candidate label selected by the voter.
        confidence: Confidence score in [0.0, 1.0].
        weight: Additional static weight multiplier for the voter.
    """

    agent_id: str
    choice: str
    confidence: float = 1.0
    weight: float = 1.0


@dataclass(frozen=True)
class ConsensusConfig:
    """Configuration for weighted consensus calculations."""

    min_votes: int = 1
    approval_threshold: float = 0.60
    tie_tolerance: float = 1e-9


@dataclass(frozen=True)
class ConsensusResult:
    """Outcome of consensus aggregation."""

    reached: bool
    winner: Optional[str]
    winner_ratio: float
    total_weight: float
    support_count: int
    vote_count: int
    scores: Dict[str, float] = field(default_factory=dict)
    ranking: List[Tuple[str, float]] = field(default_factory=list)
    reason: str = ""


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def _normalized_vote_weight(vote: Vote) -> float:
    confidence = _bounded(float(vote.confidence), 0.0, 1.0)
    weight = max(0.0, float(vote.weight))
    return confidence * weight


def compute_consensus(
    votes: Iterable[Vote],
    config: ConsensusConfig | None = None,
) -> ConsensusResult:
    """Compute weighted consensus over votes.

    Consensus is reached when:
      1) vote_count >= min_votes
      2) a unique winner exists
      3) winner_ratio >= approval_threshold
    """

    cfg = config or ConsensusConfig()
    vote_list = list(votes)

    if len(vote_list) < cfg.min_votes:
        return ConsensusResult(
            reached=False,
            winner=None,
            winner_ratio=0.0,
            total_weight=0.0,
            support_count=0,
            vote_count=len(vote_list),
            reason="insufficient_votes",
        )

    scores: Dict[str, float] = {}
    support_counts: Dict[str, int] = {}

    for vote in vote_list:
        if not vote.choice:
            continue
        norm_choice = vote.choice.strip()
        if not norm_choice:
            continue
        weighted_score = _normalized_vote_weight(vote)
        scores[norm_choice] = scores.get(norm_choice, 0.0) + weighted_score
        support_counts[norm_choice] = support_counts.get(norm_choice, 0) + 1

    if not scores:
        return ConsensusResult(
            reached=False,
            winner=None,
            winner_ratio=0.0,
            total_weight=0.0,
            support_count=0,
            vote_count=len(vote_list),
            reason="no_valid_votes",
        )

    ranking = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    winner, winner_score = ranking[0]
    total_weight = sum(scores.values())

    if total_weight <= cfg.tie_tolerance:
        return ConsensusResult(
            reached=False,
            winner=None,
            winner_ratio=0.0,
            total_weight=total_weight,
            support_count=0,
            vote_count=len(vote_list),
            scores=scores,
            ranking=ranking,
            reason="zero_total_weight",
        )

    # Check for ties at top score within tolerance.
    tied = [
        choice
        for choice, score in ranking
        if abs(score - winner_score) <= cfg.tie_tolerance
    ]
    if len(tied) > 1:
        return ConsensusResult(
            reached=False,
            winner=None,
            winner_ratio=winner_score / total_weight,
            total_weight=total_weight,
            support_count=0,
            vote_count=len(vote_list),
            scores=scores,
            ranking=ranking,
            reason="tie",
        )

    winner_ratio = winner_score / total_weight
    reached = winner_ratio >= cfg.approval_threshold

    return ConsensusResult(
        reached=reached,
        winner=winner if reached else None,
        winner_ratio=winner_ratio,
        total_weight=total_weight,
        support_count=support_counts.get(winner, 0),
        vote_count=len(vote_list),
        scores=scores,
        ranking=ranking,
        reason="ok" if reached else "below_threshold",
    )


def consensus_from_task_results(
    task_results: Dict[str, Dict[str, str]],
    *,
    success_label: str = "success",
    failure_label: str = "failure",
    config: ConsensusConfig | None = None,
) -> ConsensusResult:
    """Build a binary consensus (success/failure) from multi-agent task results.

    Expected task_results shape:
                {
                        "agent_1": {"status": "success"|"complete"|"failed"|...},
                        ...
                }

        Status values in ``_SUCCESS_STATUSES`` are normalized to ``success_label``.
        All other values are treated as ``failure_label``.
    """

    votes: List[Vote] = []
    for agent, result in task_results.items():
        status = str(result.get("status", "")).lower()
        choice = success_label if status in _SUCCESS_STATUSES else failure_label
        votes.append(Vote(agent_id=agent, choice=choice, confidence=1.0, weight=1.0))

    return compute_consensus(votes, config=config)
