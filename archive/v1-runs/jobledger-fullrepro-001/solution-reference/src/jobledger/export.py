from __future__ import annotations

from copy import deepcopy

from .models import JobLedgerError

REQUIRED_KEYS = {"jobs", "attempts", "events", "cron", "uniqueness_windows", "recovery_markers"}


def validate_export(data: dict[str, object]) -> None:
    if not isinstance(data, dict) or not REQUIRED_KEYS.issubset(data):
        raise JobLedgerError("invalid export payload")
    for key in REQUIRED_KEYS:
        if not isinstance(data[key], list):
            raise JobLedgerError(f"invalid export section {key}")


def canonical_export(data: dict[str, object]) -> dict[str, object]:
    validate_export(data)
    result = deepcopy(data)
    result["jobs"] = sorted(result["jobs"], key=lambda item: item["id"])  # type: ignore[index]
    result["events"] = sorted(result["events"], key=lambda item: item["seq"])  # type: ignore[index]
    result["cron"] = sorted(result["cron"], key=lambda item: item["name"])  # type: ignore[index]
    result["uniqueness_windows"] = sorted(result["uniqueness_windows"], key=lambda item: (item["key"], item["job_id"]))  # type: ignore[index]
    return result
