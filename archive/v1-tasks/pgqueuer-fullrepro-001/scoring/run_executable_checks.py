#!/usr/bin/env python3
"""Executable hidden checks for PgQueueLedger.

Run from outside a candidate workspace:

    python run_executable_checks.py --solution-dir <path> --json-out report.json
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Callable


Check = Callable[[dict], None]


def load(solution_dir: Path) -> dict:
    src = solution_dir / "src"
    sys.path.insert(0, str(src if src.exists() else solution_dir))
    return {
        "api": importlib.import_module("queueledger.api"),
        "models": importlib.import_module("queueledger.models"),
        "store": importlib.import_module("queueledger.store"),
        "entrypoints": importlib.import_module("queueledger.entrypoints"),
        "scheduler": importlib.import_module("queueledger.scheduler"),
        "worker": importlib.import_module("queueledger.worker"),
        "retry": importlib.import_module("queueledger.retry"),
        "completion": importlib.import_module("queueledger.completion"),
        "metrics": importlib.import_module("queueledger.metrics"),
        "recovery": importlib.import_module("queueledger.recovery"),
        "cli": importlib.import_module("queueledger.cli"),
    }


def new_ledger(ctx: dict):
    return ctx["api"].QueueLedger.in_memory()


def assert_eq(actual, expected, message: str = "") -> None:
    if actual != expected:
        raise AssertionError(message or f"expected {expected!r}, got {actual!r}")


def assert_true(value, message: str = "") -> None:
    if not value:
        raise AssertionError(message or f"expected truthy value, got {value!r}")


def terminal_statuses(ctx: dict) -> set[str]:
    return {"successful", "exception", "failed", "canceled", "deleted"}


def make_job(ctx: dict, job_id: str = "j1", entrypoint: str = "alpha", now: float = 1.0):
    return ctx["models"].Job(id=job_id, entrypoint=entrypoint, payload=b"x", created_at=now, updated_at=now)


def check_imports(ctx: dict) -> None:
    assert_true(ctx["api"].QueueLedger)


def check_status_enum(ctx: dict) -> None:
    statuses = {s.value for s in ctx["models"].JobStatus}
    assert_true({"queued", "picked", "successful", "exception", "failed", "canceled", "deleted"} <= statuses)


def check_job_defaults(ctx: dict) -> None:
    job = make_job(ctx)
    assert_eq(job.status.value, "queued")
    assert_eq(job.attempts, 0)


def check_schedule_defaults(ctx: dict) -> None:
    schedule = ctx["models"].Schedule("s1", "alpha", 10)
    assert_true(schedule.enabled)
    assert_eq(schedule.last_run_at, None)


def check_inmemory_put_get(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    job = store.put_job(make_job(ctx))
    assert_eq(store.get_job(job.id), job)


def check_inmemory_sorted_jobs(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(make_job(ctx, "b", now=2))
    store.put_job(make_job(ctx, "a", now=1))
    assert_eq([j.id for j in store.list_jobs()], ["a", "b"])


def check_replace_jobs(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(make_job(ctx, "a"))
    store.replace_jobs([make_job(ctx, "b")])
    assert_eq([j.id for j in store.list_jobs()], ["b"])


def check_queue_report_empty(ctx: dict) -> None:
    report = ctx["store"].InMemoryStore().queue_report()
    assert_eq((report.queued, report.picked, report.terminal), (0, 0, 0))


def check_queue_report_by_entrypoint(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(make_job(ctx, "a", "alpha", now=1))
    store.put_job(make_job(ctx, "b", "beta", now=2))
    report = store.queue_report()
    assert_eq(report.by_entrypoint, {"alpha": 1, "beta": 1})


def check_retry_initial_delay(ctx: dict) -> None:
    policy = ctx["retry"].RetryPolicy(max_attempts=3, delay_seconds=2, backoff=2)
    assert_eq(ctx["retry"].next_retry_delay(policy, 1), 2)


def check_retry_backoff(ctx: dict) -> None:
    policy = ctx["retry"].RetryPolicy(max_attempts=4, delay_seconds=2, backoff=3)
    assert_eq(ctx["retry"].next_retry_delay(policy, 3), 18)


def check_retry_exhaustion(ctx: dict) -> None:
    policy = ctx["retry"].RetryPolicy(max_attempts=2)
    assert_eq(ctx["retry"].next_retry_delay(policy, 2), None)


def check_registry_register_get(ctx: dict) -> None:
    reg = ctx["entrypoints"].EntrypointRegistry()
    reg.register("alpha", lambda payload: payload)
    assert_eq(reg.get("alpha")(b"x"), b"x")


def check_registry_limit(ctx: dict) -> None:
    reg = ctx["entrypoints"].EntrypointRegistry()
    reg.register("alpha", lambda payload: payload, concurrency_limit=2)
    assert_eq(reg.concurrency_limit("alpha"), 2)


def check_registry_rejects_negative_limit(ctx: dict) -> None:
    reg = ctx["entrypoints"].EntrypointRegistry()
    try:
        reg.register("alpha", lambda payload: payload, concurrency_limit=-1)
    except ValueError:
        return
    raise AssertionError("negative concurrency limit accepted")


def check_api_enqueue(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("alpha", b"x", now=5)
    assert_true(job.id)
    assert_eq((job.entrypoint, job.execute_after, ledger.get_job(job.id).payload), ("alpha", 5, b"x"))


def check_api_list_jobs(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    ledger.enqueue("alpha", b"x", now=5)
    assert_eq(len(ledger.list_jobs()), 1)


def check_transaction_commit(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    tx = ledger.transaction()
    tx.enqueue("alpha", b"x", now=1)
    assert_eq(len(ledger.list_jobs()), 0)
    tx.commit()
    assert_eq(len(ledger.list_jobs()), 1)


def check_transaction_rollback(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    tx = ledger.transaction()
    tx.enqueue("alpha", b"x", now=1)
    tx.rollback()
    assert_eq(len(ledger.list_jobs()), 0)


def check_worker_claim_basic(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(make_job(ctx, "a", "alpha", now=1))
    claimed = ctx["worker"].Worker(store, worker_id="w1").claim(["alpha"], now=2)
    assert_eq((len(claimed), claimed[0].status.value), (1, "picked"))


def check_worker_claim_filters_entrypoint(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(make_job(ctx, "a", "alpha", now=1))
    assert_eq(ctx["worker"].Worker(store, worker_id="w1").claim(["beta"], now=2), [])


def check_worker_claim_respects_execute_after(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(replace(make_job(ctx, "a", "alpha", now=1), execute_after=10))
    assert_eq(ctx["worker"].Worker(store, worker_id="w1").claim(["alpha"], now=2), [])


def check_worker_claim_priority(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(replace(make_job(ctx, "low", "alpha", now=1), priority=0))
    store.put_job(replace(make_job(ctx, "high", "alpha", now=2), priority=10))
    assert_eq(ctx["worker"].Worker(store, worker_id="w1").claim(["alpha"], now=3, limit=1)[0].id, "high")


def check_worker_claim_limit(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(make_job(ctx, "a", "alpha", now=1))
    store.put_job(make_job(ctx, "b", "alpha", now=2))
    assert_eq(len(ctx["worker"].Worker(store, worker_id="w1").claim(["alpha"], now=3, limit=1)), 1)


def check_heartbeat_updates(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    job = store.put_job(make_job(ctx, "a", "alpha", now=1))
    worker = ctx["worker"].Worker(store, worker_id="w1")
    worker.claim(["alpha"], now=2)
    worker.heartbeat([job.id], now=7)
    assert_eq(store.get_job(job.id).heartbeat, 7)


def check_complete_terminal(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    job = store.put_job(make_job(ctx, "a", "alpha", now=1))
    worker = ctx["worker"].Worker(store, worker_id="w1")
    worker.claim(["alpha"], now=2)
    assert_eq(worker.complete(job.id, now=3).status.value, "successful")


def check_cancel_terminal(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    job = store.put_job(make_job(ctx, "a", "alpha", now=1))
    assert_eq(ctx["worker"].Worker(store, worker_id="w1").cancel(job.id, now=2).status.value, "canceled")


def check_fail_requeues(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    job = store.put_job(make_job(ctx, "a", "alpha", now=1))
    worker = ctx["worker"].Worker(store, worker_id="w1")
    worker.claim(["alpha"], now=2)
    failed = worker.fail(job.id, "boom", now=3)
    assert_eq((failed.status.value, failed.attempts, failed.execute_after), ("queued", 1, 4.0))


def check_fail_terminal_after_attempts(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    job = store.put_job(replace(make_job(ctx, "a", "alpha", now=1), max_attempts=1))
    worker = ctx["worker"].Worker(store, worker_id="w1")
    worker.claim(["alpha"], now=2)
    failed = worker.fail(job.id, "boom", now=3)
    assert_eq(failed.status.value, "failed")


def check_completion_after_success(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    job = store.put_job(make_job(ctx, "a", "alpha", now=1))
    worker = ctx["worker"].Worker(store, worker_id="w1")
    worker.claim(["alpha"], now=2)
    worker.complete(job.id, now=3)
    assert_eq(ctx["completion"].CompletionWatcher(store).poll()[0].job_id, job.id)


def check_completion_offset(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    j1 = store.put_job(make_job(ctx, "a", "alpha", now=1))
    j2 = store.put_job(make_job(ctx, "b", "alpha", now=1))
    worker = ctx["worker"].Worker(store, worker_id="w1")
    worker.claim(["alpha"], now=2, limit=2)
    worker.complete(j1.id, now=3)
    worker.complete(j2.id, now=4)
    assert_eq([e.job_id for e in ctx["completion"].CompletionWatcher(store).poll(1)], [j2.id])


def check_metrics_snapshot(ctx: dict) -> None:
    store = ctx["store"].InMemoryStore()
    store.put_job(make_job(ctx, "a", "alpha", now=1))
    metrics = ctx["metrics"].metrics_snapshot(store)
    assert_eq((metrics["jobs.queued"], metrics["jobs.total"], metrics["entrypoint.alpha"]), (1, 1, 1))


def check_entrypoint_concurrency_limit(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    ledger.register_entrypoint("alpha", lambda payload: payload, concurrency_limit=1)
    ledger.enqueue("alpha", b"1", now=1)
    ledger.enqueue("alpha", b"2", now=2)
    worker = ledger.worker("w1")
    assert_eq(len(worker.claim(["alpha"], now=3, limit=2)), 1)


def check_global_concurrency_limit(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    ledger.enqueue("alpha", b"1", now=1)
    ledger.enqueue("beta", b"2", now=2)
    worker = ledger.worker("w1", global_concurrency_limit=1)
    assert_eq(len(worker.claim(["alpha", "beta"], now=3, limit=2)), 1)


def check_scheduler_register(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    schedule = ctx["models"].Schedule("s1", "alpha", 10)
    ledger.register_schedule(schedule)
    assert_eq(ledger.list_schedules()[0].id, "s1")


def check_scheduler_rejects_bad_interval(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    try:
        ledger.register_schedule(ctx["models"].Schedule("s1", "alpha", 0))
    except ValueError:
        return
    raise AssertionError("bad interval accepted")


def check_scheduler_tick_creates_job(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    ledger.register_schedule(ctx["models"].Schedule("s1", "alpha", 10, b"x"))
    assert_eq(ledger.tick(10)[0].entrypoint, "alpha")


def check_scheduler_not_due(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    ledger.register_schedule(ctx["models"].Schedule("s1", "alpha", 10))
    ledger.tick(10)
    assert_eq(ledger.tick(15), [])


def check_scheduler_due_again(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    ledger.register_schedule(ctx["models"].Schedule("s1", "alpha", 10))
    ledger.tick(10)
    assert_eq(len(ledger.tick(20)), 1)


def check_recovery_requeues_stale(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("alpha", b"x", now=1)
    ledger.worker("w1").claim(["alpha"], now=2)
    report = ledger.recover(now=10, heartbeat_timeout=5)
    assert_eq((report.recovered, ledger.get_job(job.id).status.value), ([job.id], "queued"))


def check_recovery_keeps_live(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("alpha", b"x", now=1)
    ledger.worker("w1").claim(["alpha"], now=8)
    report = ledger.recover(now=10, heartbeat_timeout=5)
    assert_eq((report.recovered, ledger.get_job(job.id).status.value), ([], "picked"))


def check_file_store_persists_job(ctx: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = ctx["api"].QueueLedger.file(tmp)
        job = ledger.enqueue("alpha", b"x", now=1)
        reopened = ctx["api"].QueueLedger.file(tmp)
        assert_eq(reopened.get_job(job.id).payload, b"x")


def check_file_store_persists_schedule(ctx: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = ctx["api"].QueueLedger.file(tmp)
        ledger.register_schedule(ctx["models"].Schedule("s1", "alpha", 10))
        reopened = ctx["api"].QueueLedger.file(tmp)
        assert_eq(reopened.list_schedules()[0].id, "s1")


def check_file_store_persists_completion(ctx: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = ctx["api"].QueueLedger.file(tmp)
        job = ledger.enqueue("alpha", b"x", now=1)
        ledger.worker("w1").claim(["alpha"], now=2)
        ledger.worker("w1").complete(job.id, now=3)
        reopened = ctx["api"].QueueLedger.file(tmp)
        assert_eq(reopened.completion_watcher().poll()[0].job_id, job.id)


def check_cli_enqueue(ctx: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        old = sys.argv[:]
        sys.argv = ["queueledger", "--store", tmp, "enqueue", "alpha", "payload", "--now", "1"]
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                ctx["cli"].main()
        finally:
            sys.argv = old
        data = json.loads(out.getvalue())
        assert_eq(data["status"], "queued")


def check_cli_report(ctx: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        for argv in [
            ["queueledger", "--store", tmp, "enqueue", "alpha", "payload", "--now", "1"],
            ["queueledger", "--store", tmp, "report"],
        ]:
            old = sys.argv[:]
            sys.argv = argv
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out):
                    ctx["cli"].main()
            finally:
                sys.argv = old
        data = json.loads(out.getvalue())
        assert_eq(data["queued"], 1)


def check_system_success_projections(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("email", b"x", now=1)
    ledger.worker("w1").claim(["email"], now=2)
    ledger.worker("w1").complete(job.id, now=3)
    assert_eq((ledger.queue_report().terminal, ledger.metrics_snapshot()["jobs.terminal"], ledger.completion_watcher().poll()[0].status.value), (1, 1, "successful"))


def check_system_retry_projection(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("email", b"x", now=1)
    ledger.worker("w1").claim(["email"], now=2)
    ledger.worker("w1").fail(job.id, "boom", now=3)
    assert_eq((ledger.queue_report().queued, ledger.get_job(job.id).attempts), (1, 1))


def check_system_retry_then_success(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("email", b"x", now=1)
    worker = ledger.worker("w1")
    worker.claim(["email"], now=2)
    worker.fail(job.id, "boom", now=3)
    worker.claim(["email"], now=5)
    worker.complete(job.id, now=6)
    assert_eq((ledger.get_job(job.id).status.value, ledger.queue_report().terminal), ("successful", 1))


def check_system_cancel_projection(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("email", b"x", now=1)
    ledger.worker("w1").cancel(job.id, now=2)
    assert_eq((ledger.queue_report().terminal, ledger.completion_watcher().poll()[0].status.value), (1, "canceled"))


def check_system_schedule_dashboard(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    ledger.register_schedule(ctx["models"].Schedule("hourly", "report", 60))
    ledger.tick(60)
    assert_eq((ledger.queue_report().queued, ledger.metrics_snapshot()["entrypoint.report"]), (1, 1))


def check_system_recovery_dashboard(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    job = ledger.enqueue("email", b"x", now=1)
    ledger.worker("w1").claim(["email"], now=2)
    ledger.recover(now=20, heartbeat_timeout=5)
    assert_eq((ledger.get_job(job.id).status.value, ledger.queue_report().queued), ("queued", 1))


def check_system_transaction_rollback_projections(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    tx = ledger.transaction()
    tx.enqueue("email", b"x", now=1)
    tx.rollback()
    assert_eq((ledger.queue_report().queued, ledger.metrics_snapshot()["jobs.total"]), (0, 0))


def check_system_transaction_commit_projections(ctx: dict) -> None:
    ledger = new_ledger(ctx)
    tx = ledger.transaction()
    tx.enqueue("email", b"x", now=1)
    tx.commit()
    assert_eq((ledger.queue_report().queued, ledger.metrics_snapshot()["jobs.total"]), (1, 1))


def check_system_file_reopen_projection(ctx: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = ctx["api"].QueueLedger.file(tmp)
        job = ledger.enqueue("email", b"x", now=1)
        ledger.worker("w1").claim(["email"], now=2)
        ledger.worker("w1").complete(job.id, now=3)
        reopened = ctx["api"].QueueLedger.file(tmp)
        assert_eq((reopened.queue_report().terminal, reopened.completion_watcher().poll()[0].job_id), (1, job.id))


CHECKS: list[tuple[str, str, str, Check]] = [
    ("PQL-U001", "unit", "imports", check_imports),
    ("PQL-U002", "unit", "status enum contract", check_status_enum),
    ("PQL-U003", "unit", "job defaults", check_job_defaults),
    ("PQL-U004", "unit", "schedule defaults", check_schedule_defaults),
    ("PQL-U005", "unit", "in-memory put/get", check_inmemory_put_get),
    ("PQL-U006", "unit", "in-memory sorted jobs", check_inmemory_sorted_jobs),
    ("PQL-U007", "unit", "replace jobs", check_replace_jobs),
    ("PQL-U008", "unit", "empty report", check_queue_report_empty),
    ("PQL-U009", "unit", "entrypoint report", check_queue_report_by_entrypoint),
    ("PQL-U010", "unit", "retry initial delay", check_retry_initial_delay),
    ("PQL-U011", "unit", "retry backoff", check_retry_backoff),
    ("PQL-U012", "unit", "retry exhaustion", check_retry_exhaustion),
    ("PQL-U013", "unit", "registry get", check_registry_register_get),
    ("PQL-U014", "unit", "registry limit", check_registry_limit),
    ("PQL-U015", "unit", "registry rejects bad limit", check_registry_rejects_negative_limit),
    ("PQL-I013", "integration", "api enqueue", check_api_enqueue),
    ("PQL-I014", "integration", "api list jobs", check_api_list_jobs),
    ("PQL-I015", "integration", "transaction commit primitive", check_transaction_commit),
    ("PQL-I016", "integration", "transaction rollback primitive", check_transaction_rollback),
    ("PQL-U020", "unit", "worker claim", check_worker_claim_basic),
    ("PQL-U021", "unit", "claim filters entrypoint", check_worker_claim_filters_entrypoint),
    ("PQL-U022", "unit", "claim respects execute_after", check_worker_claim_respects_execute_after),
    ("PQL-U023", "unit", "claim priority", check_worker_claim_priority),
    ("PQL-U024", "unit", "claim limit", check_worker_claim_limit),
    ("PQL-U025", "unit", "heartbeat update", check_heartbeat_updates),
    ("PQL-U026", "unit", "complete terminal", check_complete_terminal),
    ("PQL-U027", "unit", "cancel terminal", check_cancel_terminal),
    ("PQL-U028", "unit", "fail requeues", check_fail_requeues),
    ("PQL-U029", "unit", "fail terminal", check_fail_terminal_after_attempts),
    ("PQL-U030", "unit", "completion success", check_completion_after_success),
    ("PQL-U031", "unit", "completion offset", check_completion_offset),
    ("PQL-U032", "unit", "metrics snapshot", check_metrics_snapshot),
    ("PQL-I017", "integration", "entrypoint concurrency limit", check_entrypoint_concurrency_limit),
    ("PQL-I018", "integration", "global concurrency limit", check_global_concurrency_limit),
    ("PQL-I001", "integration", "schedule register", check_scheduler_register),
    ("PQL-I002", "integration", "bad schedule interval", check_scheduler_rejects_bad_interval),
    ("PQL-I003", "integration", "schedule tick creates job", check_scheduler_tick_creates_job),
    ("PQL-I004", "integration", "schedule not due", check_scheduler_not_due),
    ("PQL-I005", "integration", "schedule due again", check_scheduler_due_again),
    ("PQL-I006", "integration", "recovery requeues stale", check_recovery_requeues_stale),
    ("PQL-I007", "integration", "recovery keeps live", check_recovery_keeps_live),
    ("PQL-I008", "integration", "file store persists job", check_file_store_persists_job),
    ("PQL-I009", "integration", "file store persists schedule", check_file_store_persists_schedule),
    ("PQL-I010", "integration", "file store persists completion", check_file_store_persists_completion),
    ("PQL-I011", "integration", "cli enqueue", check_cli_enqueue),
    ("PQL-I012", "integration", "cli report", check_cli_report),
    ("PQL-S001", "system", "success projections agree", check_system_success_projections),
    ("PQL-S002", "system", "retry projections agree", check_system_retry_projection),
    ("PQL-S003", "system", "retry then success", check_system_retry_then_success),
    ("PQL-S004", "system", "cancel projections agree", check_system_cancel_projection),
    ("PQL-S005", "system", "schedule dashboard agrees", check_system_schedule_dashboard),
    ("PQL-S006", "system", "recovery dashboard agrees", check_system_recovery_dashboard),
    ("PQL-S007", "system", "rollback projections agree", check_system_transaction_rollback_projections),
    ("PQL-S008", "system", "commit projections agree", check_system_transaction_commit_projections),
    ("PQL-S009", "system", "file reopen projections agree", check_system_file_reopen_projection),
]


def run_checks(solution_dir: Path) -> dict:
    ctx = load(solution_dir)
    rows = []
    for check_id, layer, name, fn in CHECKS:
        try:
            fn(ctx)
            rows.append({"id": check_id, "layer": layer, "name": name, "passed": True})
        except Exception as exc:
            rows.append({"id": check_id, "layer": layer, "name": name, "passed": False, "error": f"{type(exc).__name__}: {exc}"})
    by_layer: dict[str, dict[str, int]] = {}
    for row in rows:
        stats = by_layer.setdefault(row["layer"], {"passed": 0, "total": 0})
        stats["total"] += 1
        stats["passed"] += int(row["passed"])
    return {
        "task": "pgqueuer-fullrepro-001",
        "solution_dir": str(solution_dir),
        "passed": sum(int(r["passed"]) for r in rows),
        "total": len(rows),
        "score": round(100 * sum(int(r["passed"]) for r in rows) / len(rows), 2),
        "by_layer": by_layer,
        "results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution-dir", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = run_checks(args.solution_dir.resolve())
    rendered = json.dumps(report, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
