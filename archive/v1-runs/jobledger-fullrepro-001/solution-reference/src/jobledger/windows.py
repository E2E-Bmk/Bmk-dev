from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import JobRecord, UniquePolicy, to_epoch
from .uniqueness import uniqueness_key


@dataclass(frozen=True)
class WindowRecord:
    key: str
    job_id: str
    queue: str
    kind: str
    created_at: str
    expires_at: str
    policy: UniquePolicy
    replaced_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "job_id": self.job_id,
            "queue": self.queue,
            "kind": self.kind,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "policy": self.policy.to_dict(),
            "replaced_by": self.replaced_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WindowRecord":
        return cls(
            key=str(data["key"]),
            job_id=str(data["job_id"]),
            queue=str(data["queue"]),
            kind=str(data["kind"]),
            created_at=str(data["created_at"]),
            expires_at=str(data["expires_at"]),
            policy=UniquePolicy.from_value(data["policy"]) or UniquePolicy(),
            replaced_by=data.get("replaced_by"),
        )


def build_window(job: JobRecord, policy: UniquePolicy, now: str | int | None = None) -> WindowRecord:
    created = to_epoch(now if now is not None else job.created_at)
    return WindowRecord(
        key=uniqueness_key(job, policy),
        job_id=job.id,
        queue=job.queue,
        kind=job.kind,
        created_at=str(created),
        expires_at=str(created + policy.period_seconds),
        policy=policy,
    )


def is_window_active(window: WindowRecord, jobs_by_id: dict[str, JobRecord], now: str | int | None) -> bool:
    if window.replaced_by is not None:
        return False
    if to_epoch(now) >= to_epoch(window.expires_at):
        return False
    job = jobs_by_id.get(window.job_id)
    if job is None:
        return False
    return job.state in window.policy.states


def find_window_conflict(
    candidate: JobRecord,
    windows: list[WindowRecord],
    jobs: list[JobRecord],
    now: str | int | None,
) -> WindowRecord | None:
    if candidate.unique is None:
        return None
    key = uniqueness_key(candidate, candidate.unique)
    jobs_by_id = {job.id: job for job in jobs}
    for window in windows:
        if window.key != key:
            continue
        if is_window_active(window, jobs_by_id, now):
            return window
    return None


def replace_window(windows: list[WindowRecord], old_job_id: str, new_job_id: str) -> list[WindowRecord]:
    result: list[WindowRecord] = []
    for window in windows:
        if window.job_id == old_job_id and window.replaced_by is None:
            result.append(
                WindowRecord(
                    key=window.key,
                    job_id=window.job_id,
                    queue=window.queue,
                    kind=window.kind,
                    created_at=window.created_at,
                    expires_at=window.expires_at,
                    policy=window.policy,
                    replaced_by=new_job_id,
                )
            )
        else:
            result.append(window)
    return result


def window_report(windows: list[WindowRecord], jobs: list[JobRecord], now: str | int | None = None) -> dict[str, Any]:
    jobs_by_id = {job.id: job for job in jobs}
    rows = []
    active = 0
    for window in sorted(windows, key=lambda item: (item.key, item.job_id)):
        is_active = is_window_active(window, jobs_by_id, now)
        if is_active:
            active += 1
        rows.append({**window.to_dict(), "active": is_active})
    return {"windows": rows, "total": len(rows), "active": active}
