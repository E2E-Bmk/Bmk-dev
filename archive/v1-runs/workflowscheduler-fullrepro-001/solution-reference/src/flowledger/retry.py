"""Retry policy primitives."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import utc
from .store import state_of


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(utc(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _ts(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def retry_decision(policy: dict, failure_count: int, failed_at: str) -> dict:
    """Return retry_wait or exhausted decision for a failed step."""
    policy = dict(policy or {})
    limit = int(policy.get("limit", 0))
    delay = int(policy.get("delay_seconds", 0))
    failed_at = utc(failed_at)
    if failure_count <= limit:
        return {
            "decision": "retry_wait",
            "next_attempt_at": _ts(_dt(failed_at) + timedelta(seconds=delay)),
            "retries_remaining": limit - failure_count + 1,
        }
    return {"decision": "exhausted", "next_attempt_at": None, "retries_remaining": 0}


def due_retries(store, now: str) -> list[dict]:
    """Return retry records due at `now`."""
    data = state_of(store)
    now = utc(now)
    due: list[dict] = []
    for run_id, steps in data.get("steps", {}).items():
        for step_id, step in steps.items():
            next_at = step.get("next_attempt_at")
            if step.get("status") == "retry_wait" and next_at and utc(next_at) <= now:
                due.append({"run_id": run_id, "step_id": step_id, "next_attempt_at": utc(next_at), "attempt": step.get("attempt_count", 0) + 1})
    return sorted(due, key=lambda r: (r["next_attempt_at"], r["run_id"], r["step_id"]))
