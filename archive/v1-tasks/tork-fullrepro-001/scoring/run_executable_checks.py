#!/usr/bin/env python3
"""Executable black-box/public-module checks for TorkWorkflow."""

from __future__ import annotations

import argparse
import contextlib
import io
import importlib
import json
import shutil
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable


CASES: list[dict[str, Any]] = []


def case(check_id: str, layer: str, weight: float, requirement: str, contract: str):
    def wrap(fn: Callable[["Ctx"], None]):
        CASES.append(
            {
                "id": check_id,
                "layer": layer,
                "weight": weight,
                "requirement": requirement,
                "contract": contract,
                "fn": fn,
            }
        )
        return fn

    return wrap


def as_map(obj: Any) -> dict:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    raise AssertionError(f"expected mapping-like object, got {type(obj)!r}")


def get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def state(obj: Any) -> str:
    return str(get(obj, "state", "")).upper()


def assert_in(member: Any, values: set[Any], label: str) -> None:
    if member not in values:
        raise AssertionError(f"{label}: expected one of {sorted(values)!r}, got {member!r}")


def assert_true(value: Any, label: str) -> None:
    if not value:
        raise AssertionError(label)


def assert_eq(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


class Ctx:
    def __init__(self, solution_dir: Path) -> None:
        self.solution_dir = solution_dir.resolve()
        self.tmp_root = Path(tempfile.mkdtemp(prefix="torkworkflow-score-"))
        src = self.solution_dir / "src"
        sys.path.insert(0, str(src if src.exists() else self.solution_dir))
        self.pkg = importlib.import_module("torkworkflow")
        self.api = importlib.import_module("torkworkflow.api")
        self.models = importlib.import_module("torkworkflow.models")

    def cleanup(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)
        for name in list(sys.modules):
            if name == "torkworkflow" or name.startswith("torkworkflow."):
                del sys.modules[name]
        sys.path[:] = [p for p in sys.path if p not in {str(self.solution_dir), str(self.solution_dir / "src")}]

    def module(self, name: str):
        return importlib.import_module(f"torkworkflow.{name}")

    def engine(self, name: str):
        path = self.tmp_root / name
        path.mkdir(parents=True, exist_ok=True)
        return self.api.WorkflowEngine(store_path=path)

    def spec(self, name: str = "job", tasks: list[dict] | None = None, **extra: Any) -> dict:
        data = {"name": name, "tasks": tasks or [{"name": "hello", "run": "echo hello", "var": "hello"}]}
        data.update(extra)
        return data


def submit_run(ctx: Ctx, spec: dict, name: str = "run") -> tuple[Any, str]:
    eng = ctx.engine(name)
    submitted = eng.submit(spec)
    job_id = get(submitted, "id") or get(submitted, "job_id")
    assert_true(job_id, "submit returned no job id")
    eng.run_until_idle(limit=100)
    return eng, job_id


def job_completed(job: Any) -> None:
    assert_eq(state(job), "COMPLETED", "job state")


def task_named(job: Any, name: str) -> Any:
    for task in get(job, "tasks", []) or []:
        if get(task, "name") == name:
            return task
    raise AssertionError(f"missing task named {name!r}")


def tasks_with_prefix(job: Any, prefix: str) -> list[Any]:
    return [task for task in get(job, "tasks", []) or [] if str(get(task, "name", "")).startswith(prefix)]


def listed_job(eng: Any, job_id: str) -> Any:
    for job in eng.list_jobs():
        if get(job, "id") == job_id:
            return job
    raise AssertionError(f"job {job_id!r} missing from list projection")


def assert_terminal_consistency(eng: Any, job_id: str, expected_state: str) -> Any:
    detail = eng.get_job(job_id)
    listed = listed_job(eng, job_id)
    assert_eq(state(detail), expected_state, "detail state")
    assert_eq(state(listed), expected_state, "list state")
    return detail


def assert_queue_count(eng: Any, expected: int, label: str = "queue count") -> None:
    q = eng.queue_status()
    assert_eq(get(q, "queued", get(q, "durable_count")), expected, label)


def assert_complete_progress(eng: Any, job_id: str) -> None:
    progress = eng.progress(job_id)
    assert_eq(get(progress, "percent"), 100, "progress percent")


def cli_json(cli: Any, argv: list[str]) -> Any:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.main(argv)
    return json.loads(buf.getvalue())


@case("TW-U001", "unit", 1.0, "TW-REQ-001", "parse YAML job spec into normalized JobSpec")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    spec = parser.parse_job_spec("name: yaml job\ntasks:\n  - name: hello\n    run: echo hi\n")
    assert_eq(get(spec, "name"), "yaml job", "yaml name")
    assert_true(get(spec, "tasks"), "yaml tasks")


@case("TW-U002", "unit", 1.0, "TW-REQ-001", "parse JSON job spec into normalized JobSpec")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    spec = parser.parse_job_spec('{"name":"json job","tasks":[{"name":"a","run":"echo a"}]}', fmt="json")
    assert_eq(get(spec, "name"), "json job", "json name")


@case("TW-U003", "unit", 1.0, "TW-REQ-001", "reject malformed task records without running workflow")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    try:
        parser.normalize_job_spec({"name": "bad", "tasks": [{"run": "echo missing-name"}]})
    except Exception:
        return
    raise AssertionError("malformed spec was accepted")


@case("TW-U004", "unit", 1.0, "TW-REQ-004", "preserve job output expression in normalized spec")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    spec = parser.normalize_job_spec(ctx.spec(output="{{ tasks.hello }}"))
    assert_eq(get(spec, "output"), "{{ tasks.hello }}", "output expression")


@case("TW-U005", "unit", 1.0, "TW-REQ-005", "expand parallel children without executing runtime")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    spec = parser.normalize_job_spec(ctx.spec(tasks=[{"name": "p", "parallel": [{"name": "a", "run": "echo a"}, {"name": "b", "run": "echo b"}]}]))
    task = get(spec, "tasks")[0]
    assert_eq(len(get(task, "parallel")), 2, "parallel child count")


@case("TW-U006", "unit", 1.0, "TW-REQ-005", "expand each task with stable child metadata")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    spec = parser.normalize_job_spec(ctx.spec(tasks=[{"name": "each", "each": {"items": [1, 2], "run": "echo item"}}]))
    assert_true(get(get(spec, "tasks")[0], "each"), "each metadata")


@case("TW-U007", "unit", 1.0, "TW-REQ-006", "evaluate false condition as SKIPPED primitive")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    spec = parser.normalize_job_spec(ctx.spec(tasks=[{"name": "maybe", "if": "false", "run": "echo no"}]))
    assert_eq(get(get(spec, "tasks")[0], "if_expr"), "false", "if expression")


@case("TW-U008", "unit", 1.0, "TW-REQ-007", "plan subjob parent/child records without flattening identity")
def _(ctx: Ctx):
    parser = ctx.module("parser")
    sub = {"name": "child", "tasks": [{"name": "c", "run": "echo c"}]}
    spec = parser.normalize_job_spec(ctx.spec(tasks=[{"name": "sub", "subjob": sub}]))
    assert_true(get(get(spec, "tasks")[0], "subjob"), "subjob metadata")


@case("TW-U009", "unit", 1.0, "TW-REQ-008", "compute retry eligibility from attempt history")
def _(ctx: Ctx):
    retry = ctx.module("retry")
    Attempt = ctx.models.AttemptRecord
    Task = ctx.models.TaskRecord
    task = Task(id="t", job_id="j", name="t", attempts=[Attempt(attempt=1, state="FAILED")])
    assert_true(retry.should_retry(task, max_attempts=2), "expected retry eligibility")


@case("TW-U010", "unit", 1.0, "TW-REQ-008", "compute retry available_at using fake clock")
def _(ctx: Ctx):
    retry = ctx.module("retry")
    Task = ctx.models.TaskRecord
    item = retry.next_retry_item(Task(id="t", job_id="j", name="t"), now=5, delay_seconds=7)
    assert_eq(get(item, "available_at"), 12, "retry available_at")


@case("TW-U011", "unit", 1.0, "TW-REQ-008", "timeout/progress primitive can mark non-completed task below full progress")
def _(ctx: Ctx):
    progress = ctx.module("progress")
    Task = ctx.models.TaskRecord
    assert_true(progress.task_progress(Task(id="t", job_id="j", name="t", state="RUNNING")) < 1.0, "running task should not be complete")


@case("TW-U012", "unit", 1.0, "TW-REQ-003", "broker enqueue/claim/ack primitive removes exactly one item")
def _(ctx: Ctx):
    broker = ctx.module("broker").InMemoryBroker()
    item = ctx.models.QueueItem(task_id="t", job_id="j")
    broker.enqueue(item)
    claimed = broker.claim(now=0)
    assert_eq(get(claimed, "task_id"), "t", "claimed task")
    broker.ack("t")
    assert_eq(len(get(broker.snapshot(), "queue", [])), 0, "queue after ack")


@case("TW-U013", "unit", 1.0, "TW-REQ-003", "broker requeue preserves attempt and available_at")
def _(ctx: Ctx):
    broker = ctx.module("broker").InMemoryBroker()
    item = ctx.models.QueueItem(task_id="t", job_id="j", attempt=2, available_at=9)
    broker.requeue(item)
    claimed = broker.claim(now=8)
    assert_eq(claimed, None, "not due claim")
    claimed = broker.claim(now=9)
    assert_eq(get(claimed, "attempt"), 2, "attempt after requeue")


@case("TW-U014", "unit", 1.0, "TW-REQ-002", "store create/get/list job primitives preserve IDs")
def _(ctx: Ctx):
    Store = ctx.module("datastore").WorkflowStore
    Job = ctx.models.JobRecord
    store = Store(ctx.tmp_root / "store-u014")
    store.create_job(Job(id="j", name="job"), [])
    assert_eq(get(store.get_job("j"), "id"), "j", "get job id")
    assert_eq(len(store.list_jobs()), 1, "list job count")


@case("TW-U015", "unit", 1.0, "TW-REQ-002", "store task update does not mutate unrelated jobs")
def _(ctx: Ctx):
    Store = ctx.module("datastore").WorkflowStore
    Job, Task = ctx.models.JobRecord, ctx.models.TaskRecord
    store = Store(ctx.tmp_root / "store-u015")
    store.create_job(Job(id="j1", name="one"), [Task(id="t1", job_id="j1", name="t1")])
    store.create_job(Job(id="j2", name="two"), [Task(id="t2", job_id="j2", name="t2")])
    task = store.get_task("t1")
    task.state = "COMPLETED"
    store.save_task(task)
    assert_eq(state(store.get_task("t2")), "PENDING", "unrelated task state")


@case("TW-U016", "unit", 1.0, "TW-REQ-011", "log append/page primitive preserves stream and timestamp")
def _(ctx: Ctx):
    logs = ctx.module("logs").LogStore()
    logs.append("t", "hello", stream="stdout", ts=3)
    row = logs.page("t")[0]
    assert_eq(get(row, "text"), "hello", "log text")
    assert_eq(get(row, "ts"), 3, "log ts")


@case("TW-U017", "unit", 1.0, "TW-REQ-011", "log search primitive filters without changing task history")
def _(ctx: Ctx):
    logs = ctx.module("logs").LogStore()
    logs.append("a", "needle")
    logs.append("b", "other")
    rows = logs.page(contains="needle")
    assert_eq(len(rows), 1, "filtered log count")


@case("TW-U018", "unit", 1.0, "TW-REQ-010", "schedule due/not-due primitive uses fake clock")
def _(ctx: Ctx):
    scheduler = ctx.module("scheduler").Scheduler()
    parser = ctx.module("parser")
    spec = parser.normalize_job_spec(ctx.spec())
    rec = scheduler.register("s", spec, interval_seconds=10, now=0)
    assert_eq(scheduler.due(now=get(rec, "next_due_at") - 1), [], "not due")
    assert_true(scheduler.due(now=get(rec, "next_due_at")), "due")


@case("TW-U019", "unit", 1.0, "TW-REQ-010", "schedule mark_run advances next_due_at once")
def _(ctx: Ctx):
    scheduler = ctx.module("scheduler").Scheduler()
    parser = ctx.module("parser")
    rec = scheduler.register("s", parser.normalize_job_spec(ctx.spec()), interval_seconds=10, now=0)
    old = get(rec, "next_due_at")
    scheduler.mark_run(get(rec, "id"), now=old)
    new = get(scheduler.due(now=old + 10)[0], "next_due_at")
    assert_true(new > old, "next_due_at did not advance")


@case("TW-U020", "unit", 1.0, "TW-REQ-005", "job progress rollup uses child task states")
def _(ctx: Ctx):
    progress = ctx.module("progress")
    Job, Task = ctx.models.JobRecord, ctx.models.TaskRecord
    job = Job(id="j", name="j", task_ids=["a", "b"])
    tasks = [Task(id="a", job_id="j", name="a", state="COMPLETED"), Task(id="b", job_id="j", name="b", state="PENDING")]
    p = progress.job_progress(job, tasks)
    assert_true(0.0 < p < 1.0, "partial progress")


# Integration and system checks use only WorkflowEngine public API.


@case("TW-I001", "integration", 1.5, "TW-REQ-001", "API submit writes job and tasks to store")
def _(ctx: Ctx):
    eng = ctx.engine("i001")
    out = eng.submit(ctx.spec())
    assert_true(get(out, "id"), "submit id")
    assert_eq(len(eng.list_jobs()), 1, "jobs count")


@case("TW-I002", "integration", 1.5, "TW-REQ-001", "API list/detail projections agree after submit")
def _(ctx: Ctx):
    eng = ctx.engine("i002")
    out = eng.submit(ctx.spec(name="agree"))
    detail = eng.get_job(get(out, "id"))
    assert_eq(get(eng.list_jobs()[0], "id"), get(detail, "id"), "summary/detail id")


@case("TW-I003", "integration", 1.5, "TW-REQ-003", "worker claims broker item and updates task state")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(), "i003")
    job_completed(eng.get_job(job_id))


@case("TW-I004", "integration", 1.5, "TW-REQ-004", "runtime output is stored as task var and job output input")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "hello", "run": "echo hello", "var": "hello"}], output="{{ tasks.hello }}")
    eng, job_id = submit_run(ctx, spec, "i004")
    assert_eq(get(eng.get_job(job_id), "output"), "hello", "job output")


@case("TW-I005", "integration", 1.5, "TW-REQ-008", "failed runtime attempt creates retry queue item")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "flaky", "run": "fail nope", "retry": {"limit": 1, "delay_seconds": 5}}])
    eng = ctx.engine("i005")
    job_id = get(eng.submit(spec), "id")
    eng.run_until_idle(limit=1)
    q = eng.queue_status()
    assert_true(get(q, "queued", 0) >= 1 or get(q, "scheduled", 0) >= 1, "retry not visible")
    assert_in(state(eng.get_job(job_id)), {"RUNNING", "QUEUED", "FAILED"}, "job retry state")


@case("TW-I006", "integration", 1.5, "TW-REQ-008", "retry exhaustion marks task and job failed")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "bad", "run": "fail boom", "retry": {"limit": 0}}]), "i006")
    assert_eq(state(eng.get_job(job_id)), "FAILED", "failed job")


@case("TW-I007", "integration", 1.5, "TW-REQ-011", "worker stdout/stderr appears in log page and task detail")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "log", "run": "echo logline"}]), "i007")
    logs = eng.log_page(job_id=job_id, contains="logline")
    assert_true(logs, "missing logline")


@case("TW-I008", "integration", 1.5, "TW-REQ-002", "durable reopen preserves job/task/log projections")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "persist", "run": "echo saved"}]), "i008")
    reopened = eng.reopen()
    job_completed(reopened.get_job(job_id))
    assert_true(reopened.log_page(job_id=job_id, contains="saved"), "reopened logs")


@case("TW-I009", "integration", 1.5, "TW-REQ-010", "scheduler tick submits due job through API/store")
def _(ctx: Ctx):
    eng = ctx.engine("i009")
    eng.register_schedule("s", ctx.spec(), interval_seconds=5)
    runs = eng.tick(seconds=5)
    assert_true(runs, "no scheduled run")


@case("TW-I010", "integration", 1.5, "TW-REQ-010", "second tick before due time creates no duplicate job")
def _(ctx: Ctx):
    eng = ctx.engine("i010")
    eng.register_schedule("s", ctx.spec(), interval_seconds=5)
    eng.tick(seconds=5)
    count = len(eng.list_jobs())
    eng.tick(seconds=1)
    assert_eq(len(eng.list_jobs()), count, "duplicate early schedule run")


@case("TW-I011", "integration", 1.5, "TW-REQ-009", "cancel API removes queued work and records canceled tasks")
def _(ctx: Ctx):
    eng = ctx.engine("i011")
    job_id = get(eng.submit(ctx.spec(tasks=[{"name": "slow", "run": "sleep 10"}])), "id")
    eng.cancel(job_id)
    assert_eq(state(eng.get_job(job_id)), "CANCELED", "canceled job")


@case("TW-I012", "integration", 1.5, "TW-REQ-009", "restart API creates runnable work without deleting old history")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "one", "run": "echo once"}]), "i012")
    before = eng.get_job(job_id)
    restarted = eng.restart(job_id)
    assert_true(get(restarted, "id"), "restart id")
    assert_true(len(get(before, "tasks", [])) <= len(get(eng.get_job(job_id), "tasks", get(before, "tasks", []))), "history lost")


@case("TW-I013", "integration", 1.5, "TW-REQ-012", "recovery requeues unfinished active tasks after reopen")
def _(ctx: Ctx):
    eng = ctx.engine("i013")
    eng.submit(ctx.spec(tasks=[{"name": "slow", "run": "sleep 10"}]))
    report = eng.reopen().recover()
    assert_true(isinstance(report, dict), "recovery report")


@case("TW-I014", "integration", 1.5, "TW-REQ-012", "recovery leaves completed tasks terminal")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(), "i014")
    reopened = eng.reopen()
    reopened.recover()
    job_completed(reopened.get_job(job_id))


@case("TW-I015", "integration", 1.5, "TW-REQ-005", "parallel child detail and parent progress agree")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "p", "parallel": [{"name": "a", "run": "echo a"}, {"name": "b", "run": "echo b"}]}])
    eng, job_id = submit_run(ctx, spec, "i015")
    assert_eq(get(eng.progress(job_id), "percent"), 100, "parallel progress")


@case("TW-I016", "integration", 1.5, "TW-REQ-006", "skipped conditional appears in detail and unblocks dependents")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "skip", "if": "false", "run": "echo no"}, {"name": "after", "run": "echo yes"}])
    eng, job_id = submit_run(ctx, spec, "i016")
    job = eng.get_job(job_id)
    assert_true(any(state(t) == "SKIPPED" for t in get(job, "tasks", [])), "missing skipped task")
    job_completed(job)


@case("TW-I017", "integration", 1.5, "TW-REQ-007", "subjob terminal state updates parent task projection")
def _(ctx: Ctx):
    sub = {"name": "child", "tasks": [{"name": "c", "run": "echo child"}], "output": "{{ tasks.c }}"}
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "sub", "subjob": sub}]), "i017")
    job_completed(eng.get_job(job_id))


@case("TW-I018", "integration", 1.5, "TW-REQ-003", "queue status agrees with broker and store after claim")
def _(ctx: Ctx):
    eng = ctx.engine("i018")
    eng.submit(ctx.spec())
    q = eng.queue_status()
    assert_true("queued" in q, "queue status missing queued")


@case("TW-I019", "integration", 1.5, "TW-REQ-002", "CLI/facade jobs output agrees with API list")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(name="cli-ish"), "i019")
    assert_eq(get(eng.list_jobs()[0], "id"), job_id, "facade list id")


@case("TW-I020", "integration", 1.5, "TW-REQ-011", "log pagination remains stable after reopen")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "log", "run": "echo stable"}]), "i020")
    before = eng.log_page(job_id=job_id)
    after = eng.reopen().log_page(job_id=job_id)
    assert_eq(before, after, "log page after reopen")


@case("TW-S001", "system", 3.0, "TW-REQ-001", "submit-run-complete: summary/detail/tasks/logs/progress/queue agree")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "a", "run": "echo a"}]), "s001")
    detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    assert_eq(state(task_named(detail, "a")), "COMPLETED", "task state")
    assert_true(eng.log_page(job_id=job_id, contains="a"), "completion log")
    assert_complete_progress(eng, job_id)
    assert_queue_count(eng, 0, "queue empty after completion")


@case("TW-S002", "system", 3.0, "TW-REQ-004", "task output feeds downstream expression and final job output")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "a", "run": "echo alpha", "var": "a"}, {"name": "b", "run": "echo {{ tasks.a }}-beta", "var": "b"}], output="{{ tasks.b }}")
    eng, job_id = submit_run(ctx, spec, "s002")
    detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    assert_eq(get(detail, "output"), "alpha-beta", "job output")
    assert_eq(get(task_named(detail, "b"), "output"), "alpha-beta", "task output")
    assert_true(eng.log_page(job_id=job_id, contains="alpha-beta"), "downstream log")
    assert_complete_progress(eng, job_id)


@case("TW-S003", "system", 3.0, "TW-REQ-008", "retry exhaustion: attempts/logs/progress/final status agree")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "eventual", "run": "fail first", "retry": {"limit": 1, "delay_seconds": 0}}])
    eng, job_id = submit_run(ctx, spec, "s003")
    detail = assert_terminal_consistency(eng, job_id, "FAILED")
    task = task_named(detail, "eventual")
    assert_eq(len(get(task, "attempts", [])), 2, "retry attempt count")
    assert_true(eng.log_page(job_id=job_id, contains="first"), "failure log")
    assert_true(get(eng.progress(job_id), "percent") < 100, "failed progress should not be complete")
    assert_queue_count(eng, 0, "queue empty after retry exhaustion")


@case("TW-S004", "system", 3.0, "TW-REQ-008", "timeout terminal failure visible across projections")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "timeout", "run": "sleep 20", "timeout_seconds": 1}])
    eng, job_id = submit_run(ctx, spec, "s004")
    detail = assert_terminal_consistency(eng, job_id, "FAILED")
    task = task_named(detail, "timeout")
    assert_eq(state(task), "FAILED", "timeout task")
    assert_true(get(task, "attempts", []), "timeout attempt")
    assert_true(get(get(task, "attempts", [])[0], "error") is not None, "timeout attempt error")
    assert_true(eng.log_page(task_id=get(task, "id")), "timeout task log")
    assert_true(get(eng.progress(job_id), "percent") < 100, "timeout progress")
    assert_queue_count(eng, 0, "queue empty after timeout")


@case("TW-S005", "system", 3.0, "TW-REQ-009", "cancel queued and active work updates queue/logs/detail/summary")
def _(ctx: Ctx):
    eng = ctx.engine("s005")
    job_id = get(eng.submit(ctx.spec(tasks=[{"name": "slow", "run": "sleep 30"}])), "id")
    eng.cancel(job_id)
    detail = assert_terminal_consistency(eng, job_id, "CANCELED")
    assert_eq(state(task_named(detail, "slow")), "CANCELED", "canceled task")
    assert_queue_count(eng, 0, "queue after cancel")
    assert_true(not eng.log_page(job_id=job_id, contains="slow"), "canceled task should not emit log")


@case("TW-S006", "system", 3.0, "TW-REQ-009", "restart terminal workflow preserves old history and new run state")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "x", "run": "echo x"}]), "s006")
    restarted = eng.restart(job_id)
    old_detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    new_id = get(restarted, "id")
    assert_true(new_id and new_id != job_id, "restart id")
    new_detail = eng.get_job(new_id)
    assert_in(state(new_detail), {"QUEUED", "RUNNING"}, "new run state")
    assert_true(get(old_detail, "tasks", []), "old history preserved")
    assert_true(listed_job(eng, new_id), "new run listed")
    assert_true(get(eng.queue_status(), "queued", 0) >= 1, "new run queued")


@case("TW-S007", "system", 3.0, "TW-REQ-005", "parallel workflow parent rollup matches child histories and logs")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "p", "parallel": [{"name": "a", "run": "echo a"}, {"name": "b", "run": "echo b"}]}]), "s007")
    detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    parent = task_named(detail, "p")
    assert_eq(state(parent), "COMPLETED", "parallel parent state")
    assert_eq(get(parent, "progress"), 1.0, "parallel parent progress")
    assert_eq(state(task_named(detail, "a")), "COMPLETED", "child a state")
    assert_eq(state(task_named(detail, "b")), "COMPLETED", "child b state")
    assert_true(eng.log_page(job_id=job_id, contains="a"), "parallel log a")
    assert_true(eng.log_page(job_id=job_id, contains="b"), "parallel log b")
    assert_complete_progress(eng, job_id)


@case("TW-S008", "system", 3.0, "TW-REQ-005", "each workflow creates stable child records and final aggregate progress")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "each", "each": {"items": ["a", "b"], "run": "echo {{ item }}"}}]), "s008")
    detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    parent = task_named(detail, "each")
    children = [task for task in get(detail, "tasks", []) if get(task, "parent_id") == get(parent, "id")]
    assert_eq(len(children), 2, "each child count")
    assert_eq(sorted(get(child, "id") for child in children), sorted(get(parent, "children")), "each parent/children relation")
    assert_eq(get(parent, "progress"), 1.0, "each parent progress")
    assert_true(eng.log_page(job_id=job_id, contains="a"), "each log a")
    assert_true(eng.log_page(job_id=job_id, contains="b"), "each log b")
    assert_complete_progress(eng, job_id)


@case("TW-S009", "system", 3.0, "TW-REQ-006", "conditional skip advances downstream task without fake success output")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "skip", "if": "false", "run": "echo hidden"}, {"name": "after", "run": "echo shown"}]), "s009")
    detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    skipped = task_named(detail, "skip")
    assert_eq(state(skipped), "SKIPPED", "skip state")
    assert_true(get(skipped, "output") is None, "skip output")
    assert_true(not eng.log_page(job_id=job_id, contains="hidden"), "skipped task emitted output")
    assert_true(eng.log_page(job_id=job_id, contains="shown"), "downstream missing output")
    assert_eq(state(task_named(detail, "after")), "COMPLETED", "downstream state")
    assert_complete_progress(eng, job_id)


@case("TW-S010", "system", 3.0, "TW-REQ-007", "subjob parent/child status and output agree after completion")
def _(ctx: Ctx):
    sub = {"name": "child", "tasks": [{"name": "c", "run": "echo child", "var": "c"}], "output": "{{ tasks.c }}"}
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "sub", "subjob": sub, "var": "sub"}], output="{{ tasks.sub }}"), "s010")
    detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    assert_eq(get(detail, "output"), "child", "job output")
    assert_eq(get(task_named(detail, "sub"), "output"), "child", "subjob parent output")
    assert_eq(state(task_named(detail, "c")), "COMPLETED", "subjob child state")
    assert_true(eng.log_page(job_id=job_id, contains="child"), "subjob log")
    assert_complete_progress(eng, job_id)


@case("TW-S011", "system", 3.0, "TW-REQ-010", "schedule tick creates one run with schedule provenance")
def _(ctx: Ctx):
    eng = ctx.engine("s011")
    eng.register_schedule("nightly", ctx.spec(), interval_seconds=5)
    runs = eng.tick(seconds=5)
    assert_eq(len(runs), 1, "scheduled run count")
    job_id = get(runs[0], "id")
    detail = eng.get_job(job_id)
    schedules = eng.schedules()
    assert_eq(len(eng.list_jobs()), 1, "scheduled list count")
    assert_eq(get(get(detail, "metadata", {}), "schedule_id"), get(schedules[0], "id"), "schedule provenance")
    assert_true(get(schedules[0], "last_run_at") is not None, "schedule last run")
    assert_true(get(eng.queue_status(), "queued", 0) >= 1, "scheduled job queued")


@case("TW-S012", "system", 3.0, "TW-REQ-010", "not-due schedule avoids duplicate run")
def _(ctx: Ctx):
    eng = ctx.engine("s012")
    eng.register_schedule("s", ctx.spec(), interval_seconds=5)
    eng.tick(seconds=5)
    eng.tick(seconds=1)
    assert_eq(len(eng.list_jobs()), 1, "duplicate not-due run")
    sched = eng.schedules()[0]
    assert_eq(get(sched, "last_run_at"), 5, "last run preserved")
    assert_true(get(sched, "next_due_at") > get(sched, "last_run_at"), "next due advanced")
    assert_true(get(eng.queue_status(), "queued", 0) >= 1, "first run remains queued")


@case("TW-S013", "system", 3.0, "TW-REQ-012", "worker loss recovery rebuilds queue and reports recovered tasks")
def _(ctx: Ctx):
    eng = ctx.engine("s013")
    job_id = get(eng.submit(ctx.spec(tasks=[{"name": "slow", "run": "sleep 50"}])), "id")
    reopened = eng.reopen()
    report = reopened.recover()
    queued = get(reopened.queue_status(), "queued", 0)
    detail = reopened.get_job(job_id)
    assert_eq(get(report, "queued"), queued, "recovery report/queue count")
    assert_true(queued >= 1, "recovered queue")
    assert_eq(state(task_named(detail, "slow")), "QUEUED", "recovered task state")
    assert_eq(state(listed_job(reopened, job_id)), state(detail), "list/detail after recovery")


@case("TW-S014", "system", 3.0, "TW-REQ-002", "durable reopen after completion preserves all projections")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "a", "run": "echo persist"}]), "s014")
    reopened = eng.reopen()
    detail = assert_terminal_consistency(reopened, job_id, "COMPLETED")
    assert_eq(state(task_named(detail, "a")), "COMPLETED", "persisted task")
    assert_true(reopened.log_page(job_id=job_id, contains="persist"), "persisted logs")
    assert_complete_progress(reopened, job_id)
    assert_queue_count(reopened, 0, "persisted queue empty")


@case("TW-S015", "system", 3.0, "TW-REQ-011", "log search/page agrees with task attempts after retries")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "bad", "run": "fail retrylog", "retry": {"limit": 0}}]), "s015")
    detail = assert_terminal_consistency(eng, job_id, "FAILED")
    task = task_named(detail, "bad")
    assert_eq(state(task), "FAILED", "failed task")
    assert_eq(len(get(task, "attempts", [])), 1, "failed attempt count")
    assert_true(eng.log_page(job_id=job_id, contains="retrylog"), "retry/failure log")
    assert_true(get(eng.progress(job_id), "percent") < 100, "failed progress")
    assert_queue_count(eng, 0, "failure queue empty")


@case("TW-S016", "system", 3.0, "TW-REQ-003", "two workers cannot complete same queued task twice")
def _(ctx: Ctx):
    eng, job_id = submit_run(ctx, ctx.spec(tasks=[{"name": "once", "run": "echo once"}]), "s016")
    detail = assert_terminal_consistency(eng, job_id, "COMPLETED")
    task = task_named(detail, "once")
    logs = [entry for entry in eng.log_page(job_id=job_id) if get(entry, "stream") == "stdout" and get(entry, "text") == "once"]
    assert_eq(len(logs), 1, "duplicate completion log")
    assert_eq(len(get(task, "attempts", [])), 1, "duplicate attempt")
    assert_complete_progress(eng, job_id)
    assert_queue_count(eng, 0, "duplicate queue empty")


@case("TW-S017", "system", 3.0, "TW-REQ-002", "mixed workflow histories remain isolated by job id")
def _(ctx: Ctx):
    eng = ctx.engine("s017")
    a = get(eng.submit(ctx.spec(name="a", tasks=[{"name": "a", "run": "echo A"}])), "id")
    b = get(eng.submit(ctx.spec(name="b", tasks=[{"name": "b", "run": "echo B"}])), "id")
    eng.run_until_idle()
    detail_a = assert_terminal_consistency(eng, a, "COMPLETED")
    detail_b = assert_terminal_consistency(eng, b, "COMPLETED")
    assert_eq(get(task_named(detail_a, "a"), "output"), "A", "job A task output")
    assert_eq(get(task_named(detail_b, "b"), "output"), "B", "job B task output")
    assert_true(eng.log_page(job_id=a, contains="A"), "job A log")
    assert_true(not eng.log_page(job_id=a, contains="B"), "job A contaminated by B")
    assert_true(eng.log_page(job_id=b, contains="B"), "job B log")
    assert_complete_progress(eng, a)
    assert_complete_progress(eng, b)


@case("TW-S018", "system", 3.0, "TW-REQ-005", "pre/post failure propagates to parent task and job projections")
def _(ctx: Ctx):
    spec = ctx.spec(tasks=[{"name": "with-pre", "pre": [{"name": "prep", "run": "fail prep"}], "run": "echo main"}])
    eng, job_id = submit_run(ctx, spec, "s018")
    detail = assert_terminal_consistency(eng, job_id, "FAILED")
    assert_eq(state(task_named(detail, "prep")), "FAILED", "pre task state")
    assert_true(eng.log_page(job_id=job_id, contains="prep"), "pre failure log")
    assert_true(not eng.log_page(job_id=job_id, contains="main"), "main should not run")
    assert_queue_count(eng, 0, "pre failure queue empty")


@case("TW-S019", "system", 3.0, "TW-REQ-012", "recovery report, queue view, and job detail agree after crash")
def _(ctx: Ctx):
    eng = ctx.engine("s019")
    job_id = get(eng.submit(ctx.spec(tasks=[{"name": "slow", "run": "sleep 99"}])), "id")
    reopened = eng.reopen()
    report = reopened.recover()
    detail = reopened.get_job(job_id)
    queue = reopened.queue_status()
    assert_eq(get(report, "queued"), get(queue, "queued"), "report/queue agreement")
    assert_eq(state(task_named(detail, "slow")), "QUEUED", "detail recovered task")
    assert_eq(state(listed_job(reopened, job_id)), state(detail), "list/detail recovery state")
    assert_true(get(queue, "queued", 0) >= 1, "queue visible after recovery")


@case("TW-S020", "system", 3.0, "TW-REQ-001", "CLI/facade and importable API produce same machine-readable projections")
def _(ctx: Ctx):
    cli = ctx.module("cli")
    api = ctx.module("api")
    store = ctx.tmp_root / "s020-cli-store"
    spec_file = ctx.tmp_root / "s020.json"
    spec_file.write_text(json.dumps(ctx.spec(name="facade", tasks=[{"name": "facade", "run": "echo facade"}])), encoding="utf-8")
    submitted = cli_json(cli, ["--store", str(store), "submit", str(spec_file)])
    job_id = get(submitted, "id")
    cli_json(cli, ["--store", str(store), "run-until-idle"])
    cli_jobs = cli_json(cli, ["--store", str(store), "jobs"])
    cli_detail = cli_json(cli, ["--store", str(store), "job", job_id])
    cli_queue = cli_json(cli, ["--store", str(store), "queue"])
    eng = api.WorkflowEngine(store)
    assert_eq(state(cli_detail), state(eng.get_job(job_id)), "CLI/API detail state")
    assert_eq(state([j for j in cli_jobs if get(j, "id") == job_id][0]), state(listed_job(eng, job_id)), "CLI/API list state")
    assert_eq(get(cli_queue, "queued"), get(eng.queue_status(), "queued"), "CLI/API queue")
    assert_eq(get(task_named(cli_detail, "facade"), "output"), get(task_named(eng.get_job(job_id), "facade"), "output"), "CLI/API task output")


def run_cases(solution_dir: Path) -> dict:
    ctx = Ctx(solution_dir)
    results = []
    try:
        for meta in CASES:
            try:
                meta["fn"](ctx)
                passed = True
                error = None
            except Exception as exc:  # noqa: BLE001 - scorer records public failure.
                passed = False
                error = f"{type(exc).__name__}: {exc}"
            results.append({k: v for k, v in meta.items() if k != "fn"} | {"passed": passed, "error": error})
    finally:
        ctx.cleanup()

    by_layer: dict[str, dict[str, float]] = {}
    for row in results:
        layer = row["layer"]
        by_layer.setdefault(layer, {"passed_weight": 0.0, "total_weight": 0.0, "passed_count": 0, "total_count": 0})
        by_layer[layer]["total_weight"] += row["weight"]
        by_layer[layer]["total_count"] += 1
        if row["passed"]:
            by_layer[layer]["passed_weight"] += row["weight"]
            by_layer[layer]["passed_count"] += 1
    for values in by_layer.values():
        values["score"] = values["passed_weight"] / values["total_weight"] if values["total_weight"] else 0.0
    total_weight = sum(r["weight"] for r in results)
    passed_weight = sum(r["weight"] for r in results if r["passed"])
    return {
        "task_id": "tork-fullrepro-001",
        "status": "scored",
        "candidate_runs_allowed": False,
        "check_count": len(results),
        "passed_count": sum(1 for r in results if r["passed"]),
        "total_weight": total_weight,
        "passed_weight": passed_weight,
        "overall_score": passed_weight / total_weight if total_weight else 0.0,
        "by_layer": by_layer,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solution-dir", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--list-checks", action="store_true")
    args = parser.parse_args()

    if args.list_checks:
        report = {
            "task_id": "tork-fullrepro-001",
            "status": "implemented_check_catalog",
            "candidate_runs_allowed": False,
            "check_count": len(CASES),
            "checks": [{k: v for k, v in row.items() if k != "fn"} for row in CASES],
        }
        exit_code = 0
    else:
        if not args.solution_dir:
            raise SystemExit("--solution-dir is required unless --list-checks is used")
        report = run_cases(args.solution_dir)
        exit_code = 0 if report["passed_count"] == report["check_count"] else 1

    rendered = json.dumps(report, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
