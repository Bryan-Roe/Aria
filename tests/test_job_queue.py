"""Unit tests for scripts/job_queue.py — JobQueue priority, lifecycle, persistence."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loader (registers in sys.modules so @dataclass works under Python 3.14)
# ---------------------------------------------------------------------------


def _load() -> object:
    mod_name = "job_queue"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = Path(__file__).parent.parent / "scripts" / "job_queue.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def m():
    """Module fixture shared across all tests."""
    return _load()


@pytest.fixture()
def queue(m, tmp_path):
    """Fresh JobQueue backed by a temp file."""
    return m.JobQueue(str(tmp_path / "queue.json"))


# ---------------------------------------------------------------------------
# TestJobPriority
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJobPriority:
    def test_values_exist(self, m):
        p = m.JobPriority
        assert p.LOW.value == 1
        assert p.NORMAL.value == 2
        assert p.HIGH.value == 3
        assert p.CRITICAL.value == 4

    def test_ordering_low_lt_normal(self, m):
        assert m.JobPriority.LOW.value < m.JobPriority.NORMAL.value

    def test_ordering_high_lt_critical(self, m):
        assert m.JobPriority.HIGH.value < m.JobPriority.CRITICAL.value

    def test_all_four_members(self, m):
        names = {p.name for p in m.JobPriority}
        assert names == {"LOW", "NORMAL", "HIGH", "CRITICAL"}


# ---------------------------------------------------------------------------
# TestJobStatus
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJobStatus:
    def test_pending_value(self, m):
        assert m.JobStatus.PENDING.value == "pending"

    def test_running_value(self, m):
        assert m.JobStatus.RUNNING.value == "running"

    def test_completed_value(self, m):
        assert m.JobStatus.COMPLETED.value == "completed"

    def test_failed_value(self, m):
        assert m.JobStatus.FAILED.value == "failed"

    def test_blocked_value(self, m):
        assert m.JobStatus.BLOCKED.value == "blocked"

    def test_cancelled_value(self, m):
        assert m.JobStatus.CANCELLED.value == "cancelled"


# ---------------------------------------------------------------------------
# TestQueuedJob
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestQueuedJob:
    def _make(self, m, priority=None, created_at="2024-01-01T00:00:00"):
        p = priority or m.JobPriority.NORMAL
        return m.QueuedJob(
            id="test-job",
            name="test",
            config={},
            priority=p,
            status=m.JobStatus.PENDING,
            created_at=created_at,
        )

    def test_post_init_sets_empty_dependencies(self, m):
        job = self._make(m)
        assert job.dependencies == []

    def test_post_init_sets_empty_tags(self, m):
        job = self._make(m)
        assert job.tags == []

    def test_post_init_keeps_provided_dependencies(self, m):
        job = m.QueuedJob(
            id="j",
            name="n",
            config={},
            priority=m.JobPriority.NORMAL,
            status=m.JobStatus.PENDING,
            created_at="2024-01-01T00:00:00",
            dependencies=["dep1"],
        )
        assert job.dependencies == ["dep1"]

    def test_lt_higher_priority_is_less_than(self, m):
        """Higher-priority job should sort first in a min-heap."""
        critical = self._make(m, priority=m.JobPriority.CRITICAL)
        low = self._make(m, priority=m.JobPriority.LOW)
        assert critical < low  # CRITICAL comes out of heap first

    def test_lt_same_priority_earlier_created_is_less_than(self, m):
        earlier = self._make(m, created_at="2024-01-01T00:00:00")
        later = self._make(m, created_at="2024-01-02T00:00:00")
        assert earlier < later  # FIFO within same priority

    def test_lt_not_reflexive_when_different_priority(self, m):
        critical = self._make(m, priority=m.JobPriority.CRITICAL)
        low = self._make(m, priority=m.JobPriority.LOW)
        # critical < low is True, low < critical is False
        assert not (low < critical)


# ---------------------------------------------------------------------------
# TestJobQueueAddAndGet
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJobQueueAddAndGet:
    def test_add_job_returns_string_id(self, queue, m):
        jid = queue.add_job(name="my-job", config={"k": "v"})
        assert isinstance(jid, str)
        assert jid.startswith("job_")

    def test_add_job_stored_in_jobs_dict(self, queue, m):
        jid = queue.add_job(name="stored-job", config={})
        assert jid in queue.jobs

    def test_add_job_default_status_pending(self, queue, m):
        jid = queue.add_job(name="pending-job", config={})
        assert queue.jobs[jid].status == m.JobStatus.PENDING

    def test_add_job_default_priority_normal(self, queue, m):
        jid = queue.add_job(name="n-job", config={})
        assert queue.jobs[jid].priority == m.JobPriority.NORMAL

    def test_add_job_respects_priority(self, queue, m):
        jid = queue.add_job(name="hi-job", config={}, priority=m.JobPriority.HIGH)
        assert queue.jobs[jid].priority == m.JobPriority.HIGH

    def test_add_job_with_tags(self, queue, m):
        jid = queue.add_job(name="tagged", config={}, tags=["t1", "t2"])
        assert "t1" in queue.jobs[jid].tags

    def test_get_next_job_returns_job(self, queue, m):
        queue.add_job(name="first", config={})
        job = queue.get_next_job()
        assert job is not None
        assert job.name == "first"

    def test_get_next_job_respects_priority_order(self, queue, m):
        queue.add_job(name="low-prio", config={}, priority=m.JobPriority.LOW)
        time.sleep(0.001)  # ensure distinct timestamps
        queue.add_job(name="high-prio", config={}, priority=m.JobPriority.HIGH)
        job = queue.get_next_job()
        assert job is not None
        assert job.name == "high-prio"

    def test_get_next_job_empty_queue_returns_none(self, queue, m):
        result = queue.get_next_job()
        assert result is None

    def test_get_next_job_blocks_job_with_missing_dep(self, queue, m):
        queue.add_job(name="dep-job", config={}, dependencies=["nonexistent"])
        result = queue.get_next_job()
        assert result is None
        # The job should now be BLOCKED
        blocked = [j for j in queue.jobs.values() if j.status == m.JobStatus.BLOCKED]
        assert len(blocked) == 1


# ---------------------------------------------------------------------------
# TestJobQueueLifecycle
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJobQueueLifecycle:
    def test_start_job_sets_running(self, queue, m):
        jid = queue.add_job(name="j", config={})
        queue.start_job(jid)
        assert queue.jobs[jid].status == m.JobStatus.RUNNING
        assert queue.jobs[jid].started_at is not None

    def test_complete_job_success_sets_completed(self, queue, m):
        jid = queue.add_job(name="j", config={})
        queue.start_job(jid)
        queue.complete_job(jid, success=True)
        assert queue.jobs[jid].status == m.JobStatus.COMPLETED
        assert queue.jobs[jid].completed_at is not None

    def test_complete_job_failure_increments_retry(self, queue, m):
        jid = queue.add_job(
            name="j",
            config={},
        )
        queue.start_job(jid)
        queue.complete_job(jid, success=False, error="boom")
        assert queue.jobs[jid].retry_count == 1
        assert queue.jobs[jid].status == m.JobStatus.PENDING

    def test_complete_job_failure_exhausts_retries(self, queue, m):
        """When retry_count reaches max_retries the job becomes FAILED."""
        jid = queue.add_job(name="j", config={})
        job = queue.jobs[jid]
        # Fast-forward: set retry_count to just below limit
        job.max_retries = 1
        queue.start_job(jid)
        queue.complete_job(jid, success=False, error="first-fail")
        # retry_count is now 1 == max_retries → should be FAILED now
        assert queue.jobs[jid].status == m.JobStatus.FAILED

    def test_complete_job_failure_stores_error(self, queue, m):
        jid = queue.add_job(name="j", config={})
        queue.start_job(jid)
        queue.complete_job(jid, success=False, error="err-msg")
        assert queue.jobs[jid].error_message is not None

    def test_cancel_pending_job_returns_true(self, queue, m):
        jid = queue.add_job(name="j", config={})
        result = queue.cancel_job(jid)
        assert result is True
        assert queue.jobs[jid].status == m.JobStatus.CANCELLED

    def test_cancel_running_job_returns_false(self, queue, m):
        jid = queue.add_job(name="j", config={})
        queue.start_job(jid)
        result = queue.cancel_job(jid)
        assert result is False
        assert queue.jobs[jid].status == m.JobStatus.RUNNING

    def test_cancel_nonexistent_job_returns_false(self, queue, m):
        result = queue.cancel_job("no-such-id")
        assert result is False

    def test_unblock_dependent_jobs(self, queue, m):
        jid1 = queue.add_job(name="base", config={})
        jid2 = queue.add_job(name="dep", config={}, dependencies=[jid1])
        # Consume the heap so job2 gets BLOCKED
        queue.get_next_job()  # returns jid1
        queue.start_job(jid1)
        queue.get_next_job()  # jid2 should get BLOCKED here
        # Complete jid1 — should unblock jid2
        queue.complete_job(jid1, success=True)
        assert queue.jobs[jid2].status == m.JobStatus.PENDING


# ---------------------------------------------------------------------------
# TestJobQueueStatus
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJobQueueStatus:
    def test_get_queue_status_keys(self, queue, m):
        status = queue.get_queue_status()
        expected = {
            "total_jobs",
            "pending",
            "running",
            "completed",
            "failed",
            "blocked",
            "cancelled",
            "queue_length",
            "estimated_total_time",
        }
        assert expected.issubset(set(status.keys()))

    def test_get_queue_status_counts(self, queue, m):
        jid = queue.add_job(name="j1", config={})
        time.sleep(0.002)
        queue.add_job(name="j2", config={})
        s = queue.get_queue_status()
        assert s["total_jobs"] == 2
        assert s["pending"] == 2

    def test_get_queue_status_after_completion(self, queue, m):
        jid = queue.add_job(name="j", config={})
        queue.start_job(jid)
        queue.complete_job(jid, success=True)
        s = queue.get_queue_status()
        assert s["completed"] == 1
        assert s["running"] == 0

    def test_get_job_details_returns_dict(self, queue, m):
        jid = queue.add_job(name="detail-job", config={"x": 1})
        details = queue.get_job_details(jid)
        assert isinstance(details, dict)
        for key in ("id", "name", "config", "priority", "status", "created_at"):
            assert key in details

    def test_get_job_details_unknown_id_returns_none(self, queue, m):
        assert queue.get_job_details("ghost") is None


# ---------------------------------------------------------------------------
# TestJobQueueListAndClear
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJobQueueListAndClear:
    def test_list_jobs_returns_all_when_no_filter(self, queue, m):
        queue.add_job(name="j1", config={})
        time.sleep(0.002)
        queue.add_job(name="j2", config={})
        assert len(queue.list_jobs()) == 2

    def test_list_jobs_filter_by_status(self, queue, m):
        jid = queue.add_job(name="j1", config={})
        time.sleep(0.002)
        queue.add_job(name="j2", config={})
        queue.start_job(jid)
        queue.complete_job(jid, success=True)
        completed = queue.list_jobs(status=m.JobStatus.COMPLETED)
        assert len(completed) == 1
        assert completed[0]["name"] == "j1"

    def test_list_jobs_filter_by_tags(self, queue, m):
        queue.add_job(name="tagged", config={}, tags=["ml"])
        time.sleep(0.002)
        queue.add_job(name="other", config={}, tags=["ops"])
        ml_jobs = queue.list_jobs(tags=["ml"])
        assert len(ml_jobs) == 1
        assert ml_jobs[0]["name"] == "tagged"

    def test_list_jobs_tag_filter_supports_overlap(self, queue, m):
        queue.add_job(name="both", config={}, tags=["ml", "quick"])
        time.sleep(0.002)
        queue.add_job(name="neither", config={}, tags=["ops"])
        result = queue.list_jobs(tags=["quick"])
        assert len(result) == 1

    def test_clear_completed_removes_finished_jobs(self, queue, m):
        jid = queue.add_job(name="done", config={})
        time.sleep(0.002)
        queue.add_job(name="still-pending", config={})
        queue.start_job(jid)
        queue.complete_job(jid, success=True)
        queue.clear_completed()
        assert jid not in queue.jobs
        assert len(queue.jobs) == 1

    def test_clear_completed_keeps_pending_and_running(self, queue, m):
        jid1 = queue.add_job(name="p", config={})
        time.sleep(0.002)
        jid2 = queue.add_job(name="r", config={})
        queue.start_job(jid2)
        queue.clear_completed()
        assert jid1 in queue.jobs
        assert jid2 in queue.jobs


# ---------------------------------------------------------------------------
# TestJobQueuePersistence
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJobQueuePersistence:
    def test_save_creates_file(self, m, tmp_path):
        qfile = tmp_path / "q.json"
        q = m.JobQueue(str(qfile))
        q.add_job(name="persist-me", config={"k": "v"})
        assert qfile.exists()

    def test_load_restores_jobs(self, m, tmp_path):
        qfile = tmp_path / "q.json"
        q1 = m.JobQueue(str(qfile))
        jid = q1.add_job(name="restored", config={})
        # Create a second queue from the same file
        q2 = m.JobQueue(str(qfile))
        assert jid in q2.jobs
        assert q2.jobs[jid].name == "restored"

    def test_load_handles_missing_file_gracefully(self, m, tmp_path):
        """No exception when queue file doesn't exist yet."""
        q = m.JobQueue(str(tmp_path / "new_queue.json"))
        assert len(q.jobs) == 0

    def test_load_restores_priority_enum(self, m, tmp_path):
        qfile = tmp_path / "q.json"
        q1 = m.JobQueue(str(qfile))
        jid = q1.add_job(name="hi", config={}, priority=m.JobPriority.HIGH)
        q2 = m.JobQueue(str(qfile))
        assert q2.jobs[jid].priority == m.JobPriority.HIGH

    def test_load_restores_status_enum(self, m, tmp_path):
        qfile = tmp_path / "q.json"
        q1 = m.JobQueue(str(qfile))
        jid = q1.add_job(name="sj", config={})
        q1.start_job(jid)
        q1.complete_job(jid, success=True)
        q2 = m.JobQueue(str(qfile))
        assert q2.jobs[jid].status == m.JobStatus.COMPLETED


# ---------------------------------------------------------------------------
# TestCheckDependencies
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCheckDependencies:
    def test_no_dependencies_returns_true(self, queue, m):
        jid = queue.add_job(name="no-deps", config={})
        job = queue.jobs[jid]
        assert queue.check_dependencies(job) is True

    def test_completed_dependency_returns_true(self, queue, m):
        jid1 = queue.add_job(name="dep", config={})
        queue.start_job(jid1)
        queue.complete_job(jid1, success=True)
        jid2 = queue.add_job(name="consumer", config={}, dependencies=[jid1])
        job2 = queue.jobs[jid2]
        assert queue.check_dependencies(job2) is True

    def test_pending_dependency_returns_false(self, queue, m):
        jid1 = queue.add_job(name="not-done", config={})
        jid2 = queue.add_job(name="consumer", config={}, dependencies=[jid1])
        job2 = queue.jobs[jid2]
        assert queue.check_dependencies(job2) is False

    def test_unknown_dependency_returns_false(self, queue, m):
        jid = queue.add_job(name="consumer", config={}, dependencies=["ghost-id"])
        job = queue.jobs[jid]
        assert queue.check_dependencies(job) is False
