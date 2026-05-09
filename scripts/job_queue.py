"""Job Queue Management System for QAI Training"""

import heapq
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class JobPriority(Enum):
    """Job priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class JobStatus(Enum):
    """Job execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class QueuedJob:
    """Represents a job in the queue"""

    id: str
    name: str
    config: Dict
    priority: JobPriority
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    dependencies: List[str] = None
    tags: List[str] = None
    estimated_duration: int = 0  # seconds
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []

    def __lt__(self, other):
        """For priority queue ordering (higher priority first)"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class JobQueue:
    """Manages training job queue with priorities and dependencies"""

    def __init__(self, queue_file: str = "data_out/job_queue.json"):
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        self.jobs: Dict[str, QueuedJob] = {}
        self.priority_queue = []

        self.load_queue()

    def load_queue(self):
        """Load queue from disk"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r") as f:
                    data = json.load(f)

                for job_data in data.get("jobs", []):
                    job = QueuedJob(
                        id=job_data["id"],
                        name=job_data["name"],
                        config=job_data["config"],
                        priority=JobPriority[job_data["priority"]],
                        status=JobStatus(job_data["status"]),
                        created_at=job_data["created_at"],
                        started_at=job_data.get("started_at"),
                        completed_at=job_data.get("completed_at"),
                        dependencies=job_data.get("dependencies", []),
                        tags=job_data.get("tags", []),
                        estimated_duration=job_data.get("estimated_duration", 0),
                        retry_count=job_data.get("retry_count", 0),
                        max_retries=job_data.get("max_retries", 3),
                        error_message=job_data.get("error_message"),
                    )
                    self.jobs[job.id] = job

                    if job.status == JobStatus.PENDING:
                        heapq.heappush(self.priority_queue, job)

                print(f"Loaded {len(self.jobs)} jobs from queue")
            except Exception as e:
                print(f"Error loading queue: {e}")

    def save_queue(self):
        """Save queue to disk"""
        try:
            data = {
                "jobs": [asdict(job) for job in self.jobs.values()],
                "updated_at": datetime.now().isoformat(),
            }

            # Convert enums to strings for JSON
            for job_data in data["jobs"]:
                job_data["priority"] = job_data["priority"].name
                job_data["status"] = job_data["status"].value

            with open(self.queue_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving queue: {e}")

    def add_job(
        self,
        name: str,
        config: Dict,
        priority: JobPriority = JobPriority.NORMAL,
        dependencies: List[str] = None,
        tags: List[str] = None,
        estimated_duration: int = 0,
    ) -> str:
        """Add a new job to the queue"""
        job_id = f"job_{uuid.uuid4().hex[:16]}"

        job = QueuedJob(
            id=job_id,
            name=name,
            config=config,
            priority=priority,
            status=JobStatus.PENDING,
            created_at=datetime.now().isoformat(),
            dependencies=dependencies or [],
            tags=tags or [],
            estimated_duration=estimated_duration,
        )

        self.jobs[job_id] = job
        heapq.heappush(self.priority_queue, job)

        self.save_queue()

        print(f"Added job {job_id}: {name} (priority: {priority.name})")
        return job_id

    def get_next_job(self) -> Optional[QueuedJob]:
        """Get the next job to execute (considering dependencies)"""
        while self.priority_queue:
            job = heapq.heappop(self.priority_queue)

            # Check if job still exists and is pending
            if job.id not in self.jobs or self.jobs[job.id].status != JobStatus.PENDING:
                continue

            # Check dependencies
            if self.check_dependencies(job):
                return job
            else:
                # Dependencies not met, mark as blocked
                job.status = JobStatus.BLOCKED
                self.save_queue()

        return None

    def check_dependencies(self, job: QueuedJob) -> bool:
        """Check if all job dependencies are completed"""
        if not job.dependencies:
            return True

        for dep_id in job.dependencies:
            if dep_id not in self.jobs:
                return False

            dep_job = self.jobs[dep_id]
            if dep_job.status != JobStatus.COMPLETED:
                return False

        return True

    def start_job(self, job_id: str):
        """Mark job as running"""
        if job_id in self.jobs:
            self.jobs[job_id].status = JobStatus.RUNNING
            self.jobs[job_id].started_at = datetime.now().isoformat()
            self.save_queue()
            print(f"Started job {job_id}")

    def complete_job(self, job_id: str, success: bool = True, error: str = None):
        """Mark job as completed or failed"""
        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]

        if success:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()
            print(f"Completed job {job_id}")

            # Unblock dependent jobs
            self.unblock_dependent_jobs(job_id)
        else:
            job.retry_count += 1

            if job.retry_count < job.max_retries:
                job.status = JobStatus.PENDING
                job.error_message = error
                heapq.heappush(self.priority_queue, job)
                print(
                    f"Retrying job {job_id} (attempt {job.retry_count + 1}/{job.max_retries})"
                )
            else:
                job.status = JobStatus.FAILED
                job.error_message = error
                print(f"Failed job {job_id}: {error}")

        self.save_queue()

    def unblock_dependent_jobs(self, completed_job_id: str):
        """Unblock jobs that were waiting for this job"""
        for job in self.jobs.values():
            if (
                job.status == JobStatus.BLOCKED
                and completed_job_id in job.dependencies
                and self.check_dependencies(job)
            ):

                job.status = JobStatus.PENDING
                heapq.heappush(self.priority_queue, job)
                print(f"Unblocked job {job.id}")

    def cancel_job(self, job_id: str):
        """Cancel a pending or blocked job"""
        CANCELLABLE_STATUSES = {JobStatus.PENDING, JobStatus.BLOCKED}  # O(1) set lookup
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status in CANCELLABLE_STATUSES:
                job.status = JobStatus.CANCELLED
                self.save_queue()
                print(f"Cancelled job {job_id}")
                return True
        return False

    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        # Single-pass aggregation for efficiency
        ACTIVE_STATUSES = {JobStatus.PENDING, JobStatus.BLOCKED}
        counts = {
            "total_jobs": len(self.jobs),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "blocked": 0,
            "cancelled": 0,
            "estimated_total_time": 0,
        }

        for job in self.jobs.values():
            # Count by status
            if job.status == JobStatus.PENDING:
                counts["pending"] += 1
            elif job.status == JobStatus.RUNNING:
                counts["running"] += 1
            elif job.status == JobStatus.COMPLETED:
                counts["completed"] += 1
            elif job.status == JobStatus.FAILED:
                counts["failed"] += 1
            elif job.status == JobStatus.BLOCKED:
                counts["blocked"] += 1
            elif job.status == JobStatus.CANCELLED:
                counts["cancelled"] += 1

            # Sum estimated time for active jobs
            if job.status in ACTIVE_STATUSES:
                counts["estimated_total_time"] += job.estimated_duration

        counts["queue_length"] = len(self.priority_queue)
        return counts

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Get detailed information about a job"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            return {
                "id": job.id,
                "name": job.name,
                "config": job.config,
                "priority": job.priority.name,
                "status": job.status.value,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "dependencies": job.dependencies,
                "tags": job.tags,
                "estimated_duration": job.estimated_duration,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
                "error_message": job.error_message,
            }
        return None

    def list_jobs(
        self, status: Optional[JobStatus] = None, tags: List[str] = None
    ) -> List[Dict]:
        """List all jobs, optionally filtered by status or tags"""
        jobs = list(self.jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        if tags:
            # Set intersection optimization: convert to sets for O(n) instead of O(n²) lookup
            tags_set = set(tags)
            jobs = [j for j in jobs if set(j.tags) & tags_set]

        return [self.get_job_details(j.id) for j in jobs]

    def clear_completed(self):
        """Remove completed and cancelled jobs from queue"""
        REMOVABLE_STATUSES = {
            JobStatus.COMPLETED,
            JobStatus.CANCELLED,
        }  # O(1) set lookup
        to_remove = [
            job_id
            for job_id, job in self.jobs.items()
            if job.status in REMOVABLE_STATUSES
        ]

        for job_id in to_remove:
            del self.jobs[job_id]

        self.save_queue()
        print(f"Cleared {len(to_remove)} completed/cancelled jobs")


# Example usage
if __name__ == "__main__":
    queue = JobQueue()

    # Example: Add jobs with dependencies
    job1 = queue.add_job(
        name="preprocess_data",
        config={"dataset": "mixed_chat", "action": "preprocess"},
        priority=JobPriority.HIGH,
        tags=["preprocessing"],
        estimated_duration=300,  # 5 minutes
    )

    job2 = queue.add_job(
        name="train_model_v1",
        config={"epochs": 3, "dataset": "mixed_chat"},
        priority=JobPriority.NORMAL,
        dependencies=[job1],  # Depends on preprocessing
        tags=["training", "v1"],
        estimated_duration=1800,  # 30 minutes
    )

    job3 = queue.add_job(
        name="evaluate_model",
        config={"model": "v1", "test_set": "test.json"},
        priority=JobPriority.NORMAL,
        dependencies=[job2],  # Depends on training
        tags=["evaluation"],
        estimated_duration=600,  # 10 minutes
    )

    # Print queue status
    status = queue.get_queue_status()
    print("\nQueue Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # List pending jobs
    print("\nPending Jobs:")
    for job in queue.list_jobs(status=JobStatus.PENDING):
        print(
            f"  - {job['name']} (priority: {job['priority']}, deps: {job['dependencies']})"
        )
