from __future__ import annotations

from .datastore import WorkflowStore
from .models import QueueItem
from .planner import runnable_tasks, rollup_job_state


def recover(store: WorkflowStore, *, now: int) -> dict:
    """Rebuild queue/projections from durable state and return a public report."""
    recovered: list[QueueItem] = []
    reset_running = 0
    completed_jobs = 0
    for job in store.list_jobs():
        tasks = store.list_tasks(job.id)
        if job.state in {"COMPLETED", "FAILED", "CANCELED"}:
            continue
        for task in tasks:
            if task.state == "RUNNING":
                task.state = "QUEUED"
                reset_running += 1
                store.save_task(task)
            if task.state == "QUEUED":
                recovered.append(QueueItem(task_id=task.id, job_id=job.id, available_at=now, attempt=len(task.attempts) + 1))
        for task in runnable_tasks(job, store.list_tasks(job.id)):
            task.state = "QUEUED"
            task.progress = max(task.progress, 0.01)
            store.save_task(task)
            recovered.append(QueueItem(task_id=task.id, job_id=job.id, available_at=now, attempt=len(task.attempts) + 1))
        job = rollup_job_state(job, store.list_tasks(job.id))
        job.updated_at = now
        if job.state == "COMPLETED":
            completed_jobs += 1
        store.save_job(job)
    store.replace_queue(recovered)
    store.save_clock(now)
    return {
        "recovered_queue_count": len(recovered),
        "recovered": len(recovered),
        "queued": len(recovered),
        "reset_running_count": reset_running,
        "completed_jobs": completed_jobs,
        "queue": [item.__dict__ for item in recovered],
    }
