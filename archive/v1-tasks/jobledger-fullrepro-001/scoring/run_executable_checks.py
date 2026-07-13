from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Callable


SOLUTION = Path(os.environ["JOBLEDGER_SOLUTION_PATH"]).resolve()
REFERENCE = Path(os.environ.get("JOBLEDGER_REFERENCE_PATH", str(SOLUTION))).resolve()
SRC = SOLUTION / "src"
sys.path.insert(0, str(SRC))

from jobledger.api import JobLedger
from jobledger.cron import due_slots, next_slot
from jobledger.events import event_totals, make_event
from jobledger.export import canonical_export
from jobledger.metrics import metrics_from_events
from jobledger.models import CronEntry, JobLedgerError, JobRecord, UniquePolicy
from jobledger.retry import decide_retry, retry_delay_seconds
from jobledger.retention import plan_prune
from jobledger.reports import queue_report_from_jobs
from jobledger.scheduler import claim_order, is_due
from jobledger.uniqueness import find_conflict, uniqueness_key


Check = Callable[[Path], None]


DIFFERENTIAL_PROGRAM = r"""
import json
import tempfile
from pathlib import Path
from jobledger.api import JobLedger
from jobledger.models import JobLedgerError

def normalize(projection):
    jobs = projection["jobs"]
    ordered = sorted(jobs, key=lambda item: (int(item.get("created_at") or 0), item["kind"], item["queue"]))
    mapping = {job["id"]: f"J{idx + 1}" for idx, job in enumerate(ordered)}

    def norm_obj(value):
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if key == "id" and item in mapping:
                    result[key] = mapping[item]
                elif key == "job_id" and item in mapping:
                    result[key] = mapping[item]
                elif key in {"candidate"} and isinstance(item, dict):
                    rewritten = norm_obj(item)
                    rewritten["id"] = "<candidate>"
                    result[key] = rewritten
                else:
                    result[key] = norm_obj(item)
            return result
        if isinstance(value, list):
            return [norm_obj(item) for item in value]
        return value

    projection = norm_obj(projection)
    projection["jobs"] = sorted(projection["jobs"], key=lambda item: item["id"])
    projection["events"] = sorted(projection["events"], key=lambda item: item["seq"])
    projection["export"]["jobs"] = sorted(projection["export"]["jobs"], key=lambda item: item["id"])
    projection["export"]["events"] = sorted(projection["export"]["events"], key=lambda item: item["seq"])
    return projection

with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    ledger = JobLedger(root / "ledger")
    policy = {"fields": ["kind", "queue", "args"], "period_seconds": 100, "on_conflict": "reject"}
    first = ledger.enqueue("email", {"to": "a"}, queue="mail", unique=policy, now=1)
    ledger.claim("mail", worker="w1", now=2)
    ledger.fail(first["id"], "temporary", now=3)
    ledger.claim("mail", worker="w1", now=20)
    ledger.complete(first["id"], {"ok": True}, now=21)
    try:
        ledger.enqueue("email", {"to": "a"}, queue="mail", unique=policy, now=30)
    except JobLedgerError:
        pass
    ledger.configure_cron("pulse", 10, "heartbeat", {"n": 1}, queue="ops")
    ledger.tick(25)
    exported = ledger.export_state()
    imported = JobLedger.import_state(root / "imported", exported)
    projection = {
        "jobs": ledger.jobs(),
        "queue_report": ledger.queue_report(),
        "metrics": ledger.metrics(),
        "events": ledger.events(),
        "conflict_report": ledger.conflict_report(),
        "export": exported,
        "imported_queue_report": imported.queue_report(),
        "imported_metrics": imported.metrics(),
    }
    print(json.dumps(normalize(projection), sort_keys=True))
"""


def expect_raises(exc_type: type[BaseException], fn: Callable[[], object]) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def run_projection(solution_path: Path) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(solution_path / "src")
    result = subprocess.run(
        [sys.executable, "-c", DIFFERENTIAL_PROGRAM],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def check_unit_job_defaults_and_validation(_: Path) -> None:
    job = JobRecord(id="j1", queue="default", kind="email", args={"to": "a"})
    assert job.to_dict()["state"] == "available"
    assert job.to_dict()["max_attempts"] == 3
    expect_raises(JobLedgerError, lambda: JobRecord(id="j2", queue="", kind="email"))
    expect_raises(JobLedgerError, lambda: JobRecord(id="j3", queue="default", kind="email", args=[]))  # type: ignore[arg-type]


def check_unit_scheduler_due_and_claim_order(_: Path) -> None:
    due = JobRecord(id="b", queue="q", kind="k", priority=1, scheduled_at="10", created_at="1", state="scheduled")
    early = JobRecord(id="a", queue="q", kind="k", priority=0, created_at="20")
    late = JobRecord(id="c", queue="q", kind="k", priority=0, scheduled_at="30", state="scheduled")
    assert is_due(due, 10)
    assert not is_due(late, 20)
    assert [job.id for job in claim_order([due, late, early])] == ["a", "c", "b"]


def check_unit_retry_policy_edges(_: Path) -> None:
    assert retry_delay_seconds(1) == 10
    assert retry_delay_seconds(3) == 40
    assert decide_retry(1, 3).state == "retryable"
    assert decide_retry(3, 3).state == "discarded"


def check_unit_uniqueness_key_and_conflict_expiry(_: Path) -> None:
    policy = UniquePolicy(fields=("kind", "queue", "args"), period_seconds=10)
    first = JobRecord(id="j1", queue="q", kind="email", args={"a": 1}, created_at="100", unique=policy)
    second = JobRecord(id="j2", queue="q", kind="email", args={"a": 1}, created_at="105", unique=policy)
    assert uniqueness_key(first, policy) == uniqueness_key(second, policy)
    assert find_conflict(second, [first], now=105) == first
    assert find_conflict(second, [first], now=111) is None


def check_unit_cron_slots(_: Path) -> None:
    entry = CronEntry(name="hourly", every_seconds=10, kind="sync")
    assert next_slot(entry, 0) == 10
    assert due_slots(entry, None, 35) == [10, 20, 30]
    assert due_slots(entry, 20, 35) == [30]


def check_unit_events_metrics_and_export(_: Path) -> None:
    events = [
        make_event(1, "enqueued", at="1", job_id="j1", data={"queue": "q"}),
        make_event(2, "completed", at="2", job_id="j1", data={"queue": "q"}),
    ]
    assert event_totals(events) == {"enqueued": 1, "completed": 1}
    metrics = metrics_from_events(events)
    assert metrics["totals"]["enqueued"] == 1
    assert metrics["by_queue"]["q"]["completed"] == 1
    payload = canonical_export({"jobs": [], "attempts": [], "events": [e.to_dict() for e in events], "cron": [], "uniqueness_windows": [], "recovery_markers": []})
    assert [event["seq"] for event in payload["events"]] == [1, 2]


def check_unit_reports_and_retention(_: Path) -> None:
    jobs = [
        JobRecord(id="a", queue="q1", kind="k", state="completed", created_at="1", updated_at="10"),
        JobRecord(id="b", queue="q1", kind="k", state="available", created_at="20", updated_at="20"),
        JobRecord(id="c", queue="q2", kind="k", state="scheduled", scheduled_at="100", created_at="30", updated_at="30"),
    ]
    report = queue_report_from_jobs(jobs, now=50)
    assert report["by_queue"]["q1"]["completed"] == 1
    assert report["claimable"]["q1"] == 1
    decision = plan_prune(jobs, 20, now=40)
    assert decision.pruned_ids() == ["a"]
    assert [job.id for job in decision.keep] == ["b", "c"]


def check_integration_api_lifecycle_reports(root: Path) -> None:
    ledger = JobLedger(root / "ledger")
    job = ledger.enqueue("email", {"to": "a"}, queue="mail", priority=1, now=100)
    claimed = ledger.claim("mail", worker="w1", now=101)
    assert [item["id"] for item in claimed] == [job["id"]]
    completed = ledger.complete(job["id"], {"ok": True}, now=102)
    assert completed["state"] == "completed"
    assert ledger.queue_report()["by_state"]["completed"] == 1
    assert ledger.metrics()["totals"]["completed"] == 1
    assert [event["type"] for event in ledger.history(job["id"])["events"]] == ["enqueued", "claimed", "completed"]


def check_integration_retry_and_reopen_persistence(root: Path) -> None:
    ledger = JobLedger(root / "ledger")
    job = ledger.enqueue("work", {}, now=10)
    claimed = ledger.claim(now=11)[0]
    retryable = ledger.fail(claimed["id"], "boom", now=12)
    assert retryable["state"] == "retryable"
    assert retryable["scheduled_at"] == "22"
    reopened = JobLedger(root / "ledger")
    assert reopened.jobs({"state": "retryable"})[0]["id"] == job["id"]
    assert reopened.history(job["id"])["attempts"][0]["error"] == "boom"
    assert reopened.metrics()["totals"]["retry_scheduled"] == 1


def check_integration_cli_and_api_see_same_ledger(root: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    ledger_path = root / "ledger"
    cmd = [sys.executable, "-m", "jobledger.cli", "enqueue", str(ledger_path), "--kind", "email", "--args", "{\"to\":\"b\"}", "--queue", "mail", "--now", "5"]
    result = subprocess.run(cmd, env=env, check=True, text=True, capture_output=True)
    cli_job = json.loads(result.stdout)
    api = JobLedger(ledger_path)
    assert api.jobs()[0]["id"] == cli_job["id"]
    assert api.queue_report()["claimable"]["mail"] == 1


def check_system_export_import_replay_consistency(root: Path) -> None:
    original = JobLedger(root / "original")
    first = original.enqueue("email", {"to": "a"}, queue="mail", now=1)
    original.claim("mail", now=2)
    original.complete(first["id"], now=3)
    original.configure_cron("pulse", 10, "heartbeat", queue="ops")
    original.tick(25)
    exported = original.export_state()
    imported = JobLedger.import_state(root / "imported", exported)
    assert imported.export_state() == exported
    assert imported.metrics() == original.metrics()
    assert imported.queue_report() == original.queue_report()


def check_system_uniqueness_reject_keeps_reports_consistent(root: Path) -> None:
    policy = {"fields": ["kind", "queue", "args"], "period_seconds": 100, "on_conflict": "reject"}
    ledger = JobLedger(root / "ledger")
    ledger.enqueue("email", {"to": "a"}, queue="mail", unique=policy, now=10)
    expect_raises(JobLedgerError, lambda: ledger.enqueue("email", {"to": "a"}, queue="mail", unique=policy, now=20))
    assert ledger.queue_report()["claimable"]["mail"] == 1
    assert ledger.conflict_report()["count"] == 1
    assert ledger.metrics()["totals"]["unique_conflicts"] == 1


def check_system_reference_candidate_parity(_: Path) -> None:
    expected = run_projection(REFERENCE)
    actual = run_projection(SOLUTION)
    assert actual == expected


CHECKS: list[tuple[str, str, Check]] = [
    ("JLU001", "unit", check_unit_job_defaults_and_validation),
    ("JLU004_JLU005", "unit", check_unit_scheduler_due_and_claim_order),
    ("JLU006_JLU007", "unit", check_unit_retry_policy_edges),
    ("JLU008_JLU009", "unit", check_unit_uniqueness_key_and_conflict_expiry),
    ("JLU011", "unit", check_unit_cron_slots),
    ("JLU013_JLU015_JLU018", "unit", check_unit_events_metrics_and_export),
    ("JLU_REPORT_RETENTION", "unit", check_unit_reports_and_retention),
    ("JLI003_JLI004", "integration", check_integration_api_lifecycle_reports),
    ("JLI005_JLI011", "integration", check_integration_retry_and_reopen_persistence),
    ("JLI001", "integration", check_integration_cli_and_api_see_same_ledger),
    ("JLS001_JLS011", "system", check_system_export_import_replay_consistency),
    ("JLS005", "system", check_system_uniqueness_reject_keeps_reports_consistent),
    ("JLS_PARITY_001", "system", check_system_reference_candidate_parity),
]


def main() -> int:
    json_out: Path | None = None
    if "--json-out" in sys.argv:
        index = sys.argv.index("--json-out")
        try:
            json_out = Path(sys.argv[index + 1])
        except IndexError as exc:
            raise SystemExit("--json-out requires a path") from exc
        del sys.argv[index : index + 2]

    results = []
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        for check_id, layer, fn in CHECKS:
            root = base / check_id
            root.mkdir()
            try:
                fn(root)
                results.append({"id": check_id, "layer": layer, "status": "pass"})
            except Exception as exc:
                results.append(
                    {
                        "id": check_id,
                        "layer": layer,
                        "status": "fail",
                        "error": str(exc),
                        "traceback": traceback.format_exc(limit=8),
                    }
                )
    summary: dict[str, object] = {"total": len(results), "passed": sum(1 for item in results if item["status"] == "pass")}
    by_layer: dict[str, dict[str, int]] = {}
    for item in results:
        layer = str(item["layer"])
        by_layer.setdefault(layer, {"total": 0, "passed": 0})
        by_layer[layer]["total"] += 1
        if item["status"] == "pass":
            by_layer[layer]["passed"] += 1
    summary["by_layer"] = by_layer
    output = {"summary": summary, "results": results}
    rendered = json.dumps(output, indent=2, sort_keys=True)
    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
