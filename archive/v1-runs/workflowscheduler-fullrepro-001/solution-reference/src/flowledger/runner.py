"""Deterministic fake action runner."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import FlowLedgerError, utc


def _lte(a: str, b: str) -> bool:
    da = datetime.fromisoformat(utc(a).replace("Z", "+00:00")).astimezone(timezone.utc)
    db = datetime.fromisoformat(utc(b).replace("Z", "+00:00")).astimezone(timezone.utc)
    return da <= db

def run_action(action: str, with_args: dict, now: str) -> dict:
    """Run public fake actions: ok, fail, emit, wait."""
    now = utc(now)
    with_args = dict(with_args or {})
    if action == "ok":
        return {"status": "succeeded", "output": None, "logs": [], "events": []}
    if action == "fail":
        return {
            "status": "failed",
            "error": {"error": "action_failed", "message": str(with_args.get("message", "fake action failed")), "details": {}},
            "logs": [],
            "events": [],
        }
    if action == "emit":
        message = str(with_args.get("message", ""))
        return {
            "status": "succeeded",
            "output": {"message": message},
            "logs": [{"message": message}],
            "events": [],
        }
    if action == "wait":
        until = with_args.get("until")
        if not until:
            raise FlowLedgerError("invalid_action", "wait action requires until")
        until = utc(str(until))
        if _lte(until, now):
            return {"status": "succeeded", "output": {"waited_until": until}, "logs": [], "events": []}
        return {"status": "waiting", "until": until, "logs": [], "events": [{"type": "step_waiting", "until": until}]}
    raise FlowLedgerError("invalid_action", "unknown fake action", {"action": action})
