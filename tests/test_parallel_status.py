import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = REPO_ROOT / "data_out" / "parallel_training" / "status.json"


def test_parallel_status_structure():
    if not STATUS_PATH.exists():
        pytest.skip("parallel_training status.json missing")
    data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    assert isinstance(data.get("runs"), list), "runs[] missing"
    runs = data["runs"]
    assert data.get("total_runs") == len(runs), "total_runs mismatch"
    for run in runs:
        assert (
            "jobs" in run and isinstance(run["jobs"], list) and run["jobs"]
        ), "run missing jobs list"
        for job in run["jobs"]:
            assert job.get("name"), "job name missing"
            assert job.get("status") in {
                "succeeded",
                "failed",
                "skipped",
                "error",
            }, "unexpected job status"
        ranking = run.get("job_ranking")
        if ranking:
            # Ranking size should not exceed succeeded jobs
            succeeded_jobs = [j for j in run["jobs"] if j.get("status") == "succeeded"]
            assert len(ranking) <= len(succeeded_jobs)
            for entry in ranking:
                assert entry.get("name"), "ranking entry missing name"
                assert entry.get("metric"), "ranking entry missing metric"
                assert "score" in entry, "ranking entry missing score"
                metric = entry["metric"]
                if metric == "distinct_diversity":
                    # diversity_avg must equal score
                    assert entry.get("diversity_avg") == entry.get(
                        "score"
                    ), "alias score mismatch"
                if (
                    metric == "perplexity_improvement"
                    and "perplexity_improvement" in entry
                ):
                    assert (
                        pytest.approx(entry["perplexity_improvement"], rel=1e-3)
                        == entry["score"]
                    ), "improvement score mismatch"
