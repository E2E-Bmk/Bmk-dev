"""Restart recovery classification and repair."""

from __future__ import annotations

from .models import utc
from .queue import expire_leases
from .retry import due_retries
from .store import save_if_possible, state_of

def recovery_report(store, now: str) -> dict:
    """Classify recoverable state without hiding history."""
    data = state_of(store)
    now = utc(now)
    expired = []
    for item in data.get("queue", []):
        if item.get("status") != "leased" or not item.get("leased_at"):
            continue
        from datetime import datetime, timedelta, timezone

        leased = datetime.fromisoformat(utc(item["leased_at"]).replace("Z", "+00:00")).astimezone(timezone.utc)
        deadline = leased + timedelta(seconds=int(item.get("lease_seconds", 0)))
        if deadline.isoformat(timespec="seconds").replace("+00:00", "Z") <= now:
            expired.append(dict(item))

    live_step_leases = {
        (item.get("run_id"), item.get("step_id"))
        for item in data.get("queue", [])
        if item.get("type") == "step" and item.get("status") == "leased"
    }
    orphan_running_steps = []
    for run_id, steps in data.get("steps", {}).items():
        for step_id, step in steps.items():
            if step.get("status") == "running" and (run_id, step_id) not in live_step_leases:
                orphan_running_steps.append({"run_id": run_id, "step_id": step_id})

    missing_run_items = [
        dict(item)
        for item in data.get("queue", [])
        if item.get("status") in {"queued", "leased"} and item.get("run_id") and item.get("run_id") not in data.get("runs", {})
    ]
    retries = due_retries(store, now)
    partial_records = [
        {"kind": "event", "index": idx}
        for idx, event in enumerate(data.get("events", []))
        if not event.get("recorded_at") or not event.get("sequence")
    ] + [
        {"kind": "log", "index": idx}
        for idx, log in enumerate(data.get("logs", []))
        if not log.get("recorded_at") or not log.get("sequence")
    ]
    return {
        "now": now,
        "expired_leases": expired,
        "running_steps_without_live_leases": orphan_running_steps,
        "queued_items_missing_runs": missing_run_items,
        "due_retries": retries,
        "partial_records": partial_records,
    }


def recover(store, now: str) -> dict:
    """Apply public recovery actions and return a report."""
    data = state_of(store)
    report = recovery_report(store, now)
    now = utc(now)
    timed_out = expire_leases(store, now)

    repaired: list[dict] = []
    for item in timed_out:
        if item.get("run_id") not in data.get("runs", {}):
            continue
        if item.get("type") == "step":
            step = data["steps"].get(item["run_id"], {}).get(item.get("step_id"))
            if step and step.get("status") in {"running", "queued"}:
                step["status"] = "queued"
                new_item = dict(item)
                for key in ["id", "worker_id", "leased_at", "lease_seconds", "acked_at", "cancelled_at", "timed_out_at"]:
                    new_item.pop(key, None)
                new_item["status"] = "queued"
                new_item["visible_at"] = now
                from .queue import enqueue

                repaired.append({"action": "requeued_timed_out_step", "item": enqueue(store, new_item)})
        elif item.get("type") == "run":
            run = data["runs"].get(item["run_id"])
            if run and run.get("status") == "queued":
                new_item = dict(item)
                for key in ["id", "worker_id", "leased_at", "lease_seconds", "acked_at", "cancelled_at", "timed_out_at"]:
                    new_item.pop(key, None)
                new_item["status"] = "queued"
                new_item["visible_at"] = now
                from .queue import enqueue

                repaired.append({"action": "requeued_timed_out_run", "item": enqueue(store, new_item)})

    from .queue import enqueue

    for orphan in report["running_steps_without_live_leases"]:
        run = data["runs"].get(orphan["run_id"])
        if not run:
            continue
        step = data["steps"][orphan["run_id"]][orphan["step_id"]]
        step["status"] = "queued"
        item = enqueue(
            store,
            {
                "type": "step",
                "workflow": run["workflow"],
                "run_id": orphan["run_id"],
                "step_id": orphan["step_id"],
                "queue": step.get("queue", "default"),
                "created_at": now,
                "visible_at": now,
            },
        )
        repaired.append({"action": "requeued_orphan_running_step", "item": item})

    for retry in report["due_retries"]:
        run = data["runs"].get(retry["run_id"])
        if not run:
            continue
        step = data["steps"][retry["run_id"]][retry["step_id"]]
        if step.get("status") == "retry_wait":
            step["status"] = "queued"
            step["next_attempt_at"] = None
            item = enqueue(
                store,
                {
                    "type": "step",
                    "workflow": run["workflow"],
                    "run_id": retry["run_id"],
                    "step_id": retry["step_id"],
                    "queue": step.get("queue", "default"),
                    "created_at": now,
                    "visible_at": now,
                },
            )
            repaired.append({"action": "queued_due_retry", "item": item})

    for item in data.get("queue", []):
        if item.get("status") in {"queued", "leased"} and item.get("run_id") and item.get("run_id") not in data.get("runs", {}):
            item["status"] = "cancelled"
            item["cancelled_at"] = now
            repaired.append({"action": "cancelled_missing_run_item", "item_id": item.get("id")})

    data.setdefault("recovery_markers", []).append({"recorded_at": now, "report": report, "repaired": repaired})
    save_if_possible(store)
    return {**report, "repaired": repaired}
