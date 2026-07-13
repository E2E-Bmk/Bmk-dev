#!/usr/bin/env python3
"""Executable hidden checks for the FlowLedger SWE-E2E task.

The scorer is intentionally public-surface oriented: it imports only the
starter-declared ``flowledger`` modules, drives ``FlowLedger`` and
``python -m flowledger.cli``, and inspects JSON-compatible reports.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import json
import os
import subprocess
import sys
import tempfile
import traceback
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
CHECKS: dict[str, Callable[[], None]] = {}
CTX: dict[str, Any] = {}


class CheckFail(AssertionError):
    pass


class SkipCheck(Exception):
    pass


class PublicStore(dict):
    """Flexible direct-fixture store for feature-pure module checks."""

    def __init__(self, path: str | Path):
        super().__init__()
        self.path = Path(path)
        self.root = self.path
        self.store_path = self.path
        self.queue_items: list[dict[str, Any]] = []
        self.items = self.queue_items
        self.queue = self.queue_items
        self.runs: dict[str, dict[str, Any]] = {}
        self.steps: dict[str, dict[str, dict[str, Any]]] = {}
        self.attempts: list[dict[str, Any]] = []
        self.logs: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.specs: dict[str, Any] = {}
        self.schedules: dict[str, Any] = {}
        self.retries: list[dict[str, Any]] = []
        self.update(
            {
                "path": str(self.path),
                "queue_items": self.queue_items,
                "items": self.queue_items,
                "queue": self.queue_items,
                "runs": self.runs,
                "steps": self.steps,
                "attempts": self.attempts,
                "logs": self.logs,
                "events": self.events,
                "specs": self.specs,
                "schedules": self.schedules,
                "retries": self.retries,
            }
        )


def check(check_id: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    def wrap(fn: Callable[[], None]) -> Callable[[], None]:
        CHECKS[check_id] = fn
        return fn

    return wrap


def ensure(condition: Any, message: str) -> None:
    if not condition:
        raise CheckFail(message)


def utc(hours: float = 0, seconds: float = 0) -> str:
    return (BASE + timedelta(hours=hours, seconds=seconds)).isoformat().replace("+00:00", "Z")


def normalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return normalize(dataclasses.asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in dict.items(value)}
    if isinstance(value, (list, tuple, set)):
        return [normalize(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return normalize(value.to_dict())
    if hasattr(value, "__dict__") and value.__class__.__module__.startswith("flowledger"):
        return normalize(vars(value))
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def blob(value: Any) -> str:
    return json.dumps(normalize(value), sort_keys=True, default=str).lower()


def all_dicts(value: Any) -> list[dict[str, Any]]:
    value = normalize(value)
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(all_dicts(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(all_dicts(child))
    return found


def values_for_key(value: Any, key: str) -> list[Any]:
    vals: list[Any] = []
    for dct in all_dicts(value):
        for k, v in dct.items():
            if k == key or k.lower() == key.lower():
                vals.append(v)
    return vals


def first_mapping(value: Any, key: str) -> Any:
    vals = values_for_key(value, key)
    return vals[0] if vals else None


def has_text(value: Any, *needles: str) -> bool:
    text = blob(value)
    return all(needle.lower() in text for needle in needles)


def count_text(value: Any, needle: str) -> int:
    return blob(value).count(needle.lower())


def status_values(value: Any) -> list[str]:
    return [str(v).lower() for v in values_for_key(value, "status")]


def require_status(value: Any, status: str) -> None:
    ensure(status.lower() in status_values(value) or f'"{status.lower()}"' in blob(value), f"missing status {status}")


def first_id(value: Any, preferred: tuple[str, ...] = ("run_id", "id", "item_id", "queue_item_id")) -> str:
    data = normalize(value)
    for key in preferred:
        vals = values_for_key(data, key)
        for val in vals:
            if isinstance(val, str) and val:
                return val
    raise CheckFail(f"could not find any id key in {preferred}")


def item_id(item: Any) -> str:
    return first_id(item, ("item_id", "queue_item_id", "id"))


def import_mod(name: str):
    return importlib.import_module(f"flowledger.{name}")


def spec_module_dict(spec_obj: Any) -> dict[str, Any]:
    spec = import_mod("spec")
    try:
        return normalize(spec.spec_to_dict(spec_obj))
    except Exception:
        data = normalize(spec_obj)
        ensure(isinstance(data, dict), "spec object is not JSON-like")
        return data


def minimal_spec(
    name: str = "wf",
    *,
    mode: str = "graph",
    steps: list[dict[str, Any]] | None = None,
    schedule: dict[str, Any] | None = None,
    max_active_runs: int = 1,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "name": name,
        "mode": mode,
        "params": {"ENV": "test"},
        "queue": "default",
        "max_active_runs": max_active_runs,
        "steps": steps or [{"id": "a", "action": "ok"}],
    }
    if schedule is not None:
        doc["schedule"] = schedule
    return doc


def load_spec_doc(doc: dict[str, Any]) -> Any:
    return import_mod("spec").load_spec(deepcopy(doc))


def assert_raises(fn: Callable[[], Any], label: str) -> Any:
    try:
        fn()
    except NotImplementedError:
        raise
    except Exception as exc:  # noqa: BLE001 - public error type may vary.
        return exc
    raise CheckFail(f"{label} did not raise")


def tmp_store() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="flowledger-score-")


class ApiHarness:
    def __init__(self) -> None:
        self.tmp = tmp_store()
        self.store = Path(self.tmp.name)
        self.api = import_mod("api").FlowLedger(self.store)
        init = getattr(self.api, "init", None)
        if callable(init):
            init()

    def close(self) -> None:
        self.tmp.cleanup()

    def put(self, doc: dict[str, Any]) -> dict[str, Any]:
        return normalize(self.api.put_spec(deepcopy(doc)))

    def start(self, workflow: str, now: str = utc(), params: dict[str, Any] | None = None) -> dict[str, Any]:
        return normalize(self.api.start(workflow, now, params))

    def tick(self, now: str) -> dict[str, Any]:
        return normalize(self.api.tick(now))

    def claim(self, worker: str = "worker-a", now: str = utc(), lease: int = 60) -> dict[str, Any] | None:
        claimed = self.api.claim("default", worker, now, lease)
        return normalize(claimed) if claimed is not None else None

    def complete(self, claimed: dict[str, Any], worker: str = "worker-a", now: str = utc(), output: Any = None) -> dict[str, Any]:
        return normalize(self.api.complete(item_id(claimed), worker, now, output))

    def fail(self, claimed: dict[str, Any], worker: str = "worker-a", now: str = utc(), error: dict[str, Any] | None = None) -> dict[str, Any]:
        return normalize(self.api.fail(item_id(claimed), worker, now, error or {"error": "boom", "message": "boom"}))

    def cancel(self, run_id: str, now: str = utc()) -> dict[str, Any]:
        return normalize(self.api.cancel(run_id, now))

    def reports(self, workflow: str | None = None, now: str = utc()) -> dict[str, Any]:
        return {
            "status": normalize(self.api.status(workflow=workflow)),
            "history": normalize(self.api.history(workflow=workflow)),
            "queue": normalize(self.api.queue()),
            "next_runs": normalize(self.api.next_runs(now)),
            "logs": normalize(self.api.logs()),
            "events": normalize(self.api.events()),
        }


def drain_success(api: ApiHarness, *, limit: int = 12, output: Any = None) -> list[dict[str, Any]]:
    claimed: list[dict[str, Any]] = []
    for index in range(limit):
        item = api.claim(worker="worker-a", now=utc(seconds=index), lease=30)
        if item is None:
            break
        claimed.append(item)
        api.complete(item, worker="worker-a", now=utc(seconds=index + 0.5), output=output)
    return claimed


def projection_subset(api: ApiHarness, workflow: str | None = None) -> dict[str, Any]:
    reports = api.reports(workflow=workflow, now=utc(10))
    return normalize(reports)


def cli_env(candidate_root: Path) -> dict[str, str]:
    src = candidate_root / "src"
    pp = str(src if src.exists() else candidate_root)
    env = os.environ.copy()
    env["PYTHONPATH"] = pp + os.pathsep + env.get("PYTHONPATH", "")
    return env


def parse_cli_json(proc: subprocess.CompletedProcess[str], argv: list[str]) -> Any:
    if proc.returncode != 0:
        raise CheckFail(f"CLI failed ({proc.returncode}) for {' '.join(argv)}: {proc.stderr.strip() or proc.stdout.strip()}")
    text = proc.stdout.strip()
    ensure(text, f"CLI produced no JSON for {' '.join(argv)}")
    try:
        return normalize(json.loads(text))
    except json.JSONDecodeError as exc:
        raise CheckFail(f"CLI output was not JSON for {' '.join(argv)}: {text[:300]}") from exc


def run_cli(store: Path, command: str, args: list[str] | None = None, stdin: Any = None) -> Any:
    candidate = CTX["candidate_root"]
    args = args or []
    stdin_text = None if stdin is None else json.dumps(stdin)
    variants = [
        [sys.executable, "-m", "flowledger.cli", command, "--store", str(store), *args],
        [sys.executable, "-m", "flowledger.cli", "--store", str(store), command, *args],
    ]
    errors: list[str] = []
    for argv in variants:
        proc = subprocess.run(
            argv,
            input=stdin_text,
            text=True,
            capture_output=True,
            timeout=15,
            env=cli_env(candidate),
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return parse_cli_json(proc, argv)
        errors.append(proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}")
    raise CheckFail(f"CLI command {command!r} failed in supported forms: {' | '.join(errors)}")


def cli_put_spec(store: Path, doc: dict[str, Any]) -> Any:
    spec_path = store / "spec.json"
    spec_path.write_text(json.dumps(doc), encoding="utf-8")
    variants = [
        ["put-spec", ["--spec", str(spec_path)], None],
        ["put-spec", ["--file", str(spec_path)], None],
        ["put-spec", [str(spec_path)], None],
        ["put-spec", [], doc],
    ]
    errors = []
    for cmd, args, stdin in variants:
        try:
            return run_cli(store, cmd, args, stdin)
        except Exception as exc:  # noqa: BLE001 - try public CLI variants.
            errors.append(str(exc))
    raise CheckFail("CLI put-spec failed in supported forms: " + " | ".join(errors[:3]))


def load_rubric() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parent.parent / "rubric.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["items"]


# ----------------------------- unit checks -----------------------------


@check("WSU001")
def _() -> None:
    doc = {"name": "minimal", "steps": [{"id": "only", "action": "ok"}]}
    out = spec_module_dict(load_spec_doc(doc))
    ensure(out.get("name") == "minimal", "minimal spec name not preserved")
    ensure(out.get("mode") == "graph", "graph mode default missing")
    ensure(out.get("queue") == "default", "default queue missing")
    ensure(out.get("max_active_runs") == 1, "max_active_runs default missing")
    ensure(isinstance(out.get("params"), dict), "params default is not an object")
    ensure(has_text(out, "only", "ok"), "step id/action missing after normalization")


@check("WSU002")
def _() -> None:
    dup = minimal_spec(steps=[{"id": "a", "action": "ok"}, {"id": "a", "action": "ok"}])
    bad_dep = minimal_spec(steps=[{"id": "a", "action": "ok", "depends": ["missing"]}])
    assert_raises(lambda: load_spec_doc(dup), "duplicate step ids")
    assert_raises(lambda: load_spec_doc(bad_dep), "unknown dependency")
    valid = load_spec_doc(minimal_spec(name="still-valid"))
    ensure(spec_module_dict(valid).get("name") == "still-valid", "validation failure poisoned later load")


@check("WSU003")
def _() -> None:
    graph = spec_module_dict(load_spec_doc(minimal_spec(steps=[{"id": "a", "action": "ok"}, {"id": "b", "action": "ok", "depends": ["a"]}])))
    ensure(has_text(graph, "depends", "a", "b"), "graph dependency not preserved")
    assert_raises(
        lambda: load_spec_doc(minimal_spec(mode="chain", steps=[{"id": "a", "action": "ok"}, {"id": "b", "action": "ok", "depends": ["a"]}])),
        "chain explicit depends",
    )
    chain = spec_module_dict(load_spec_doc(minimal_spec(mode="chain", steps=[{"id": "a", "action": "ok"}, {"id": "b", "action": "ok"}])))
    ensure(chain.get("mode") == "chain" and blob(chain).find('"a"') < blob(chain).find('"b"'), "chain order not preserved")


@check("WSU004")
def _() -> None:
    assert_raises(lambda: load_spec_doc(minimal_spec(steps=[{"id": "bad", "action": "shell"}])), "unknown action")
    emit = spec_module_dict(load_spec_doc(minimal_spec(steps=[{"id": "e", "action": "emit", "with": {"message": "hello"}}])))
    wait = spec_module_dict(load_spec_doc(minimal_spec(steps=[{"id": "w", "action": "wait", "with": {"until": utc(1)}}])))
    ensure(has_text(emit, "emit", "hello"), "emit action args not normalized")
    ensure(has_text(wait, "wait", utc(1)), "wait action args not normalized")


def scheduler_spec(catchup: str) -> Any:
    return load_spec_doc(minimal_spec(schedule={"every_seconds": 3600, "catchup": catchup, "overlap": "all"}))


@check("WSU005")
def _() -> None:
    slots = normalize(import_mod("scheduler").due_slots(scheduler_spec("skip"), utc(0), utc(1)))
    ensure(len(slots) <= 1, "catchup skip materialized multiple missed slots")
    ensure(not has_text(slots, utc(0)), "catchup skip rematerialized last slot")
    ensure(has_text(slots, utc(1)) or slots == [], "catchup skip did not make a deterministic due/no-due decision at now")


@check("WSU006")
def _() -> None:
    slots = normalize(import_mod("scheduler").due_slots(scheduler_spec("latest"), utc(0), utc(3, seconds=1800)))
    ensure(len(slots) == 1, "catchup latest must materialize exactly one missed slot")
    ensure(has_text(slots, utc(3)) and not has_text(slots, utc(1), utc(2)), "catchup latest did not choose latest missed slot")


@check("WSU007")
def _() -> None:
    slots = normalize(import_mod("scheduler").due_slots(scheduler_spec("all"), utc(0), utc(3, seconds=1800)))
    ensure(len(slots) == 3, "catchup all must materialize every missed slot")
    ensure(all(has_text(slots, utc(h)) for h in (1, 2, 3)), "catchup all missing one or more expected slots")


@check("WSU008")
def _() -> None:
    sched = import_mod("scheduler")
    skip = normalize(sched.apply_overlap("skip", ["active"], [], ["slot-a"]))
    allp = normalize(sched.apply_overlap("all", ["active"], ["queued"], ["slot-a", "slot-b"]))
    latest = normalize(sched.apply_overlap("latest", [], ["old-run"], ["old-slot", "new-slot"]))
    ensure(not has_text(skip, "slot-a") or has_text(skip, "skip"), "overlap skip enqueued while active")
    ensure(has_text(first_mapping(allp, "enqueue_slots"), "slot-a", "slot-b") and first_mapping(allp, "cancel_run_ids") in ([], None), "overlap all did not keep all slots")
    ensure(has_text(latest, "new-slot") and has_text(latest, "cancel"), "overlap latest did not keep newest and cancel older queued work")


@check("WSU009")
def _() -> None:
    q = import_mod("queue")
    with tmp_store() as td:
        store = PublicStore(td)
        item = q.enqueue(store, {"id": "q1", "queue": "default", "kind": "step", "run_id": "r1", "created_at": utc()})
        claimed = normalize(q.claim(store, "default", "worker-a", utc(), 30))
    ensure(has_text(item, "q1"), "enqueue did not return public queue item")
    require_status(claimed, "leased")
    ensure(has_text(claimed, "worker-a") and has_text(claimed, "30"), "lease metadata missing from claim")


@check("WSU010")
def _() -> None:
    q = import_mod("queue")
    with tmp_store() as td:
        store = PublicStore(td)
        q.enqueue(store, {"id": "q1", "queue": "default", "created_at": utc()})
        q.claim(store, "default", "owner", utc(), 60)
        before = normalize(q.queue_report(store))
        assert_raises(lambda: q.ack(store, "q1", "intruder", utc(seconds=1)), "ack by non-owner")
        after = normalize(q.queue_report(store))
    ensure(blob(before) == blob(after) or (has_text(after, "leased", "owner") and not has_text(after, "acked")), "wrong-worker ack changed lease state")


@check("WSU011")
def _() -> None:
    q = import_mod("queue")
    with tmp_store() as td:
        store = PublicStore(td)
        q.enqueue(store, {"id": "q1", "queue": "default", "created_at": utc()})
        q.claim(store, "default", "worker-a", utc(), 10)
        expired = normalize(q.expire_leases(store, utc(seconds=11)))
        report = normalize(q.queue_report(store))
    ensure(has_text(expired, "q1") and (has_text(expired, "timed_out") or has_text(report, "timed_out")), "expired lease not reported as timed_out")


@check("WSU012")
def _() -> None:
    decision = normalize(import_mod("retry").retry_decision({"limit": 2, "delay_seconds": 10}, 1, utc()))
    ensure(has_text(decision, "retry_wait") and has_text(decision, utc(seconds=10)), "retry decision did not schedule retry_wait with delay")


@check("WSU013")
def _() -> None:
    decision = normalize(import_mod("retry").retry_decision({"limit": 2, "delay_seconds": 10}, 3, utc()))
    ensure(has_text(decision, "exhaust") or has_text(decision, "failed"), "exhausted retry did not produce terminal decision")
    ensure(not has_text(decision, "retry_wait"), "exhausted retry still scheduled retry_wait")


@check("WSU014")
def _() -> None:
    runner = import_mod("runner")
    ok = normalize(runner.run_action("ok", {}, utc()))
    fail = normalize(runner.run_action("fail", {}, utc()))
    emit = normalize(runner.run_action("emit", {"message": "hello"}, utc()))
    wait = normalize(runner.run_action("wait", {"until": utc(1)}, utc()))
    ensure(has_text(ok, "succeed") or has_text(ok, "ok"), "ok action did not succeed")
    ensure(has_text(fail, "fail") or has_text(fail, "error"), "fail action did not fail publicly")
    ensure(has_text(emit, "hello"), "emit action did not return message")
    ensure(has_text(wait, "wait") and has_text(wait, utc(1)), "wait action did not expose waiting-until state")


@check("WSU015")
def _() -> None:
    logs = import_mod("logs")
    with tmp_store() as td:
        store = PublicStore(td)
        logs.append_log(store, {"run_id": "r", "message": "third", "recorded_at": utc(1), "sequence": 3})
        logs.append_log(store, {"run_id": "r", "message": "first", "recorded_at": utc(0), "sequence": 1})
        logs.append_event(store, {"run_id": "r", "type": "a", "recorded_at": utc(1)})
        logs.append_event(store, {"run_id": "r", "type": "b", "recorded_at": utc(1)})
        stream = normalize({"logs": logs.log_stream(store), "events": logs.event_stream(store)})
    text = blob(stream)
    ensure(text.find("first") < text.find("third"), "logs not ordered by recorded_at/sequence")
    ensure(text.find('"a"') < text.find('"b"'), "events not ordered by sequence for timestamp tie")


@check("WSU016")
def _() -> None:
    hist = import_mod("history")
    with tmp_store() as td:
        store = PublicStore(td)
        store["runs"]["r1"] = {"id": "r1", "workflow": "wf", "status": "failed", "created_at": utc(), "updated_at": utc()}
        store["steps"]["r1"] = {
            "a": {"run_id": "r1", "step_id": "a", "status": "succeeded", "order": 0},
            "b": {"run_id": "r1", "step_id": "b", "status": "failed", "order": 1},
        }
        store.attempts.append({"run_id": "r1", "step_id": "a", "attempt": 1, "status": "succeeded"})
        store.attempts.append({"run_id": "r1", "step_id": "b", "attempt": 1, "status": "failed"})
        report = normalize(hist.status_report(store, workflow="wf"))
    require_status(report, "failed")
    ensure(has_text(report, "r1", "a", "b"), "status rollup missing run/step facts")


@check("WSU017")
def _() -> None:
    hist = import_mod("history")
    spec_obj = load_spec_doc(minimal_spec(name="scheduled", schedule={"every_seconds": 3600, "catchup": "latest", "overlap": "all"}))
    with tmp_store() as td:
        store = PublicStore(td)
        store.specs["scheduled"] = spec_module_dict(spec_obj)
        store.schedules["scheduled"] = {"last_slot": utc(0)}
        report = normalize(hist.next_runs_report(store, utc(1)))
    ensure(has_text(report, "scheduled", utc(1)), "next-runs report did not agree with schedule ledger")


@check("WSU018")
def _() -> None:
    rec = import_mod("recovery")
    with tmp_store() as td:
        store = PublicStore(td)
        store.queue_items.append({"id": "lease1", "queue": "default", "status": "leased", "leased_at": utc(), "lease_seconds": 5, "created_at": utc()})
        store.queue_items.append({"id": "orphan1", "queue": "default", "status": "queued", "run_id": "missing", "created_at": utc()})
        store["runs"]["r1"] = {"id": "r1", "workflow": "wf", "status": "running", "created_at": utc(), "updated_at": utc()}
        store["steps"]["r1"] = {"a": {"run_id": "r1", "step_id": "a", "status": "retry_wait", "next_attempt_at": utc(1), "order": 0}}
        report = normalize(rec.recovery_report(store, utc(2)))
    ensure(has_text(report, "lease") and has_text(report, "retry") and has_text(report, "orphan"), "recovery did not classify expired leases, due retries, and orphan queue rows")


@check("WSU019")
def _() -> None:
    exp = import_mod("export")
    with tmp_store() as td:
        store = PublicStore(td)
        store.specs["wf"] = {"name": "wf"}
        before = normalize(store)
        assert_raises(lambda: exp.import_snapshot(store, {"specs": {"other": {"name": "other"}}}), "import into non-empty store")
        after = normalize(store)
    ensure(blob(before) == blob(after), "failed import into non-empty store was not atomic")


@check("WSU020")
def _() -> None:
    err = import_mod("models").FlowLedgerError("bad_code", "Bad message", {"field": "name"})
    data = normalize(err.to_dict())
    ensure(data == {"error": "bad_code", "message": "Bad message", "details": {"field": "name"}}, "FlowLedgerError to_dict is not deterministic")
    json.dumps(data, sort_keys=True)


# -------------------------- integration checks --------------------------


@check("WSI001")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="persisted"))
        reports = api.reports("persisted")
        api2 = import_mod("api").FlowLedger(api.store)
        reports2 = normalize(api2.status(workflow="persisted"))
    finally:
        api.close()
    ensure(has_text(reports, "persisted", "queued") or has_text(reports, "persisted", "pending"), "put-spec status missing normalized workflow")
    ensure(has_text(reports2, "persisted"), "workflow did not persist across facade instances")


@check("WSI002")
def _() -> None:
    with tmp_store() as td:
        store = Path(td)
        run_cli(store, "init")
        cli_put_spec(store, minimal_spec(name="cli_spec"))
        api_status = normalize(import_mod("api").FlowLedger(store).status(workflow="cli_spec"))
    ensure(has_text(api_status, "cli_spec"), "CLI put-spec not visible through API status")


@check("WSI003")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="sched", schedule={"every_seconds": 3600, "catchup": "latest", "overlap": "all"}))
        tick = api.tick(utc(3, seconds=1800))
        reports = api.reports("sched", now=utc(3, seconds=1800))
    finally:
        api.close()
    ensure(has_text({"tick": tick, **reports}, "sched"), "tick did not materialize scheduled workflow facts")
    ensure(has_text(reports["queue"], "queued") and has_text(reports["next_runs"], "sched"), "scheduled queue and next-run reports disagree")


@check("WSI004")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="overlap_skip", schedule={"every_seconds": 3600, "catchup": "all", "overlap": "skip"}))
        api.tick(utc(1))
        before = api.reports("overlap_skip")["queue"]
        api.tick(utc(2))
        after = api.reports("overlap_skip")["queue"]
        events = api.reports("overlap_skip")["events"]
    finally:
        api.close()
    ensure(count_text(after, "queued") <= max(1, count_text(before, "queued")), "overlap skip created duplicate visible queue work while active")
    ensure(has_text(events, "skip") or blob(before) == blob(after), "overlap skip did not record or preserve skipped due slot")


@check("WSI005")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="run_ok", steps=[{"id": "a", "action": "ok"}]))
        api.start("run_ok", utc())
        item = api.claim()
        ensure(item is not None, "start did not expose claimable work")
        api.complete(item, output={"ok": True})
        reports = api.reports("run_ok")
    finally:
        api.close()
    require_status(reports, "succeeded")
    ensure(has_text(reports["queue"], "acked") or not has_text(reports["queue"], "leased"), "queue lease not acked/cleared after complete")
    ensure(has_text(reports["history"], "a"), "attempt history missing completed step")


@check("WSI006")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="retrying", steps=[{"id": "a", "action": "fail", "retry": {"limit": 2, "delay_seconds": 10}}]))
        api.start("retrying", utc())
        item = api.claim()
        ensure(item is not None, "no item to fail")
        api.fail(item, now=utc(), error={"error": "boom", "message": "first failure"})
        reports = api.reports("retrying", now=utc())
    finally:
        api.close()
    require_status(reports, "retry_wait")
    ensure(has_text(reports, "retry", utc(seconds=10)), "retry event/timestamp missing after failure")


@check("WSI007")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="retry_due", steps=[{"id": "a", "action": "fail", "retry": {"limit": 2, "delay_seconds": 10}}]))
        api.start("retry_due", utc())
        item = api.claim()
        ensure(item is not None, "no item to fail")
        api.fail(item, now=utc())
        before = api.reports("retry_due")["history"]
        api.tick(utc(seconds=11))
        queue = api.reports("retry_due")["queue"]
        after = api.reports("retry_due")["history"]
    finally:
        api.close()
    ensure(has_text(queue, "queued", "a"), "due retry was not returned to queue")
    ensure(count_text(after, "attempt") >= count_text(before, "attempt"), "prior attempt history was not preserved")


@check("WSI008")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="cancel_me"))
        start = api.start("cancel_me", utc())
        rid = first_id(start, ("run_id", "id"))
        api.cancel(rid, utc(seconds=1))
        reports = api.reports("cancel_me")
    finally:
        api.close()
    require_status(reports, "cancelled")
    ensure(not has_text(reports["queue"], "queued") or has_text(reports["queue"], "cancelled"), "cancel left visible queued work")
    ensure(has_text(reports["events"], "cancel"), "cancel event missing")


@check("WSI009")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="emit_flow", steps=[{"id": "say", "action": "emit", "with": {"message": "hello-log"}}]))
        api.start("emit_flow", utc())
        item = api.claim()
        ensure(item is not None, "no emit item to complete")
        api.complete(item, output={"message": "hello-log"})
        reports = api.reports("emit_flow")
    finally:
        api.close()
    ensure(has_text(reports["logs"], "hello-log") and has_text(reports["history"], "hello-log"), "emit output not projected to logs and history")


@check("WSI010")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="recover_lease"))
        api.start("recover_lease", utc())
        item = api.claim(lease=5)
        ensure(item is not None, "no leased item to recover")
        api2 = import_mod("api").FlowLedger(api.store)
        report = normalize(api2.recover(utc(seconds=6)))
        queue = normalize(api2.queue())
    finally:
        api.close()
    ensure(has_text(report, "lease") and has_text(report, "expired"), "recover did not report expired lease")
    ensure(has_text(queue, "queued") or has_text(queue, "timed_out"), "expired lease was not requeued or timed out visibly")


@check("WSI011")
def _() -> None:
    src = ApiHarness()
    dst = ApiHarness()
    try:
        src.put(minimal_spec(name="roundtrip", schedule={"every_seconds": 3600, "catchup": "latest", "overlap": "all"}))
        src.start("roundtrip", utc())
        drain_success(src, output={"message": "done"})
        snap = normalize(src.api.export())
        dst.api.import_snapshot(snap)
        left = projection_subset(src, "roundtrip")
        right = projection_subset(dst, "roundtrip")
    finally:
        src.close()
        dst.close()
    ensure(blob(left) == blob(right), "export/import did not preserve public projections")


@check("WSI012")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="atomic_complete"))
        api.start("atomic_complete", utc())
        item = api.claim(worker="owner")
        ensure(item is not None, "no item to test wrong-worker complete")
        before = projection_subset(api, "atomic_complete")
        assert_raises(lambda: api.complete(item, worker="intruder", now=utc(seconds=1)), "wrong-worker complete")
        after = projection_subset(api, "atomic_complete")
    finally:
        api.close()
    ensure(blob(before) == blob(after), "wrong-worker complete changed public projections")


@check("WSI013")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="chain_flow", mode="chain", steps=[{"id": "first", "action": "ok"}, {"id": "second", "action": "ok"}]))
        api.start("chain_flow", utc())
        first = api.claim()
        ensure(first is not None and has_text(first, "first") and not has_text(first, "second"), "chain did not expose only first step")
        api.complete(first)
        second = api.claim(now=utc(seconds=1))
    finally:
        api.close()
    ensure(second is not None and has_text(second, "second"), "chain did not expose second step after first success")


@check("WSI014")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="graph_flow", steps=[{"id": "a", "action": "ok"}, {"id": "b", "action": "ok"}, {"id": "c", "action": "ok", "depends": ["a", "b"]}]))
        api.start("graph_flow", utc())
        first = api.claim(worker="w1")
        second = api.claim(worker="w2")
        ensure(first is not None and second is not None, "graph did not expose both independent steps")
        ensure(not has_text([first, second], "c"), "dependent step exposed before prerequisites")
        api.complete(first, worker="w1")
        none_or_not_c = api.claim(worker="w3", now=utc(seconds=1))
        ensure(none_or_not_c is None or not has_text(none_or_not_c, "c"), "dependent step exposed before all prerequisites")
        api.complete(second, worker="w2", now=utc(seconds=2))
        dep = api.claim(worker="w4", now=utc(seconds=3))
    finally:
        api.close()
    ensure(dep is not None and has_text(dep, "c"), "dependent graph step not queued after prerequisites")


@check("WSI015")
def _() -> None:
    with tmp_store() as td:
        store = Path(td)
        run_cli(store, "init")
        cli_put_spec(store, minimal_spec(name="cli_recover"))
        run_cli(store, "start", ["cli_recover", "--now", utc()])
        run_cli(store, "claim", ["--queue", "default", "--worker-id", "worker-a", "--now", utc(), "--lease-seconds", "5"])
        cli_report = run_cli(store, "recover", ["--now", utc(seconds=6)])
        api_report = normalize(import_mod("api").FlowLedger(store).recover(utc(seconds=6)))
    ensure(has_text(cli_report, "lease") and has_text(api_report, "lease"), "CLI/API recover did not expose equivalent lease recovery facts")


# ---------------------------- system checks -----------------------------


@check("WSS001")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="system_success", steps=[{"id": "a", "action": "emit", "with": {"message": "alpha"}}, {"id": "b", "action": "ok", "depends": ["a"]}]))
        api.start("system_success", utc())
        drain_success(api, output={"message": "alpha"})
        reports = api.reports("system_success")
    finally:
        api.close()
    require_status(reports, "succeeded")
    ensure(has_text(reports["history"], "a", "b") and has_text(reports["logs"], "alpha") and not has_text(reports["queue"], "leased"), "successful workflow projections are incoherent")


@check("WSS002")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="retry_then_ok", steps=[{"id": "a", "action": "fail", "retry": {"limit": 2, "delay_seconds": 10}}]))
        api.start("retry_then_ok", utc())
        first = api.claim()
        ensure(first is not None, "no first attempt")
        api.fail(first, now=utc())
        api.tick(utc(seconds=11))
        second = api.claim(now=utc(seconds=12))
        ensure(second is not None, "retry attempt not claimable")
        api.complete(second, now=utc(seconds=13), output={"message": "recovered"})
        reports = api.reports("retry_then_ok")
    finally:
        api.close()
    require_status(reports, "succeeded")
    ensure(count_text(reports["history"], "attempt") >= 2 and has_text(reports["events"], "retry"), "retry lifecycle history/events incomplete")


@check("WSS003")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="retry_exhaust", steps=[{"id": "a", "action": "fail", "retry": {"limit": 1, "delay_seconds": 5}}]))
        api.start("retry_exhaust", utc())
        first = api.claim()
        ensure(first is not None, "no first attempt")
        api.fail(first, now=utc())
        api.tick(utc(seconds=6))
        second = api.claim(now=utc(seconds=7))
        ensure(second is not None, "no retry attempt")
        api.fail(second, now=utc(seconds=8))
        reports = api.reports("retry_exhaust")
    finally:
        api.close()
    require_status(reports, "failed")
    ensure(not has_text(reports["queue"], "queued") and has_text(reports["history"], "boom"), "retry exhaustion left queue work or lost errors")


@check("WSS004")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="catch_latest", schedule={"every_seconds": 3600, "catchup": "latest", "overlap": "all"}))
        api.tick(utc(5, seconds=1800))
        reports = api.reports("catch_latest", now=utc(5, seconds=1800))
    finally:
        api.close()
    ensure(count_text(reports["queue"], "queued") == 1 and has_text(reports["next_runs"], "catch_latest"), "catchup latest did not materialize exactly one due run with next-run view")


@check("WSS005")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="catch_all", schedule={"every_seconds": 3600, "catchup": "all", "overlap": "all"}))
        api.tick(utc(4, seconds=1800))
        queue = api.reports("catch_all")["queue"]
    finally:
        api.close()
    ensure(count_text(queue, "queued") >= 4, "catchup all did not materialize every missed slot")
    ensure(count_text(queue, utc(1)) <= 1 and count_text(queue, utc(2)) <= 1, "catchup all duplicated slot ids")


@check("WSS006")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="latest_overlap", schedule={"every_seconds": 3600, "catchup": "all", "overlap": "latest"}))
        api.tick(utc(1))
        api.tick(utc(2))
        reports = api.reports("latest_overlap")
    finally:
        api.close()
    ensure(count_text(reports["queue"], "queued") == 1 and has_text(reports["events"], "cancel"), "overlap latest did not cancel older queued due run and keep newest visible")


@check("WSS007")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="lease_restart", steps=[{"id": "a", "action": "emit", "with": {"message": "before-restart"}}]))
        api.start("lease_restart", utc())
        item = api.claim(lease=5)
        ensure(item is not None, "no lease to expire")
        api2 = import_mod("api").FlowLedger(api.store)
        report = normalize(api2.recover(utc(seconds=6)))
        reports = {
            "recovery": report,
            "queue": normalize(api2.queue()),
            "history": normalize(api2.history(workflow="lease_restart")),
            "logs": normalize(api2.logs()),
        }
    finally:
        api.close()
    ensure(has_text(reports, "expired", "lease") and not has_text(reports["history"], "deleted"), "restart recovery lost history or missed expired lease")


@check("WSS008")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="cancel_running", steps=[{"id": "a", "action": "wait", "with": {"until": utc(5)}}, {"id": "b", "action": "ok", "depends": ["a"]}]))
        start = api.start("cancel_running", utc())
        rid = first_id(start, ("run_id", "id"))
        claimed = api.claim(lease=60)
        ensure(claimed is not None, "no running item")
        api.cancel(rid, utc(seconds=1))
        reports = api.reports("cancel_running")
    finally:
        api.close()
    require_status(reports, "cancelled")
    ensure(has_text(reports["history"], "cancelled") and not has_text(reports["queue"], "leased"), "cancelling running workflow did not propagate to attempts/queue")


@check("WSS009")
def _() -> None:
    src = ApiHarness()
    dst = ApiHarness()
    try:
        src.put(minimal_spec(name="mixed_replay", schedule={"every_seconds": 3600, "catchup": "latest", "overlap": "all"}, steps=[{"id": "a", "action": "emit", "with": {"message": "loggy"}, "retry": {"limit": 1, "delay_seconds": 5}}]))
        src.tick(utc(2))
        item = src.claim()
        ensure(item is not None, "no scheduled item")
        src.fail(item, now=utc(2))
        src.tick(utc(2, seconds=6))
        retry_item = src.claim(now=utc(2, seconds=7))
        if retry_item is not None:
            src.complete(retry_item, now=utc(2, seconds=8), output={"message": "loggy"})
        snap = normalize(src.api.export())
        dst.api.import_snapshot(snap)
        left = projection_subset(src, "mixed_replay")
        right = projection_subset(dst, "mixed_replay")
    finally:
        src.close()
        dst.close()
    ensure(blob(left) == blob(right), "mixed schedule/retry/log export-import replay changed public projections")


@check("WSS010")
def _() -> None:
    with tmp_store() as td:
        store = Path(td)
        run_cli(store, "init")
        cli_put_spec(store, minimal_spec(name="cli_parity", steps=[{"id": "a", "action": "ok"}]))
        run_cli(store, "start", ["cli_parity", "--now", utc()])
        claim = run_cli(store, "claim", ["--queue", "default", "--worker-id", "worker-a", "--now", utc(), "--lease-seconds", "60"])
        run_cli(store, "complete", [item_id(claim), "--worker-id", "worker-a", "--now", utc(seconds=1)])
        cli_status = run_cli(store, "status", ["--workflow", "cli_parity"])
        api_status = normalize(import_mod("api").FlowLedger(store).status(workflow="cli_parity"))
    ensure(blob(cli_status) == blob(api_status) or (has_text(cli_status, "succeeded") and has_text(api_status, "succeeded")), "CLI-driven workflow final report differs from API report")


@check("WSS011")
def _() -> None:
    chain = ApiHarness()
    graph = ApiHarness()
    try:
        steps_chain = [{"id": "a", "action": "emit", "with": {"message": "same"}}, {"id": "b", "action": "ok"}]
        steps_graph = [{"id": "a", "action": "emit", "with": {"message": "same"}}, {"id": "b", "action": "ok", "depends": ["a"]}]
        chain.put(minimal_spec(name="chain_equiv", mode="chain", steps=steps_chain))
        graph.put(minimal_spec(name="graph_equiv", mode="graph", steps=steps_graph))
        chain.start("chain_equiv", utc())
        graph.start("graph_equiv", utc())
        first_chain = chain.claim()
        first_graph = graph.claim()
        drain_success(chain, output={"message": "same"})
        drain_success(graph, output={"message": "same"})
        chain_reports = chain.reports("chain_equiv")
        graph_reports = graph.reports("graph_equiv")
    finally:
        chain.close()
        graph.close()
    ensure(has_text(first_chain, "a") and has_text(first_graph, "a"), "chain/graph first legal queue item unexpected")
    ensure(has_text(chain_reports, "same", "succeeded") and has_text(graph_reports, "same", "succeeded"), "equivalent chain/graph terminal output not preserved")


@check("WSS012")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="wait_flow", steps=[{"id": "waiter", "action": "wait", "with": {"until": utc(2)}}, {"id": "after", "action": "ok", "depends": ["waiter"]}]))
        api.start("wait_flow", utc())
        first = api.claim(now=utc())
        ensure(first is not None and has_text(first, "waiter"), "wait step not claimable")
        api.complete(first, now=utc(), output={"waiting_until": utc(2)})
        before = api.claim(now=utc(1))
        api.tick(utc(2))
        after = api.claim(now=utc(2, seconds=1))
    finally:
        api.close()
    ensure(before is None or not has_text(before, "after"), "dependent step ran before wait time")
    ensure(after is not None and has_text(after, "after"), "dependent step did not resume after virtual time advanced")


@check("WSS013")
def _() -> None:
    raise SkipCheck("No public API exists to create a partial log/event write marker without inspecting private storage layout.")


@check("WSS014")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="limited", max_active_runs=1, schedule={"every_seconds": 3600, "catchup": "all", "overlap": "all"}))
        api.tick(utc(1))
        api.tick(utc(2))
        reports = api.reports("limited", now=utc(2))
    finally:
        api.close()
    active_count = count_text(reports["status"], "running") + count_text(reports["status"], "queued")
    ensure(active_count <= 1 or has_text(reports["events"], "max_active"), "max_active_runs allowed excess active runs without public audit")
    ensure(has_text(reports["next_runs"], "limited") and has_text(reports["queue"], "limited"), "concurrency limit broke queue/history/next-run coherence")


@check("WSS015")
def _() -> None:
    api = ApiHarness()
    try:
        api.put(minimal_spec(name="import_atomic"))
        api.start("import_atomic", utc())
        before = projection_subset(api, "import_atomic")
        assert_raises(lambda: api.api.import_snapshot({"specs": {"other": {"name": "other"}}}), "import into non-empty ledger")
        after = projection_subset(api, "import_atomic")
    finally:
        api.close()
    ensure(blob(before) == blob(after), "failed import into non-empty ledger changed public projections")


def prepare_candidate(candidate: Path) -> None:
    root = candidate.resolve()
    src = root / "src"
    sys.path.insert(0, str(src if src.exists() else root))
    CTX["candidate_root"] = root
    importlib.invalidate_caches()
    for name in list(sys.modules):
        if name == "flowledger" or name.startswith("flowledger."):
            del sys.modules[name]
    importlib.import_module("flowledger")


def result_counts(results: list[dict[str, Any]], rubric: list[dict[str, Any]]) -> dict[str, Any]:
    weights = {item["id"]: item.get("weight", 1) for item in rubric}
    layers = sorted({item["layer"] for item in rubric})
    by_layer: dict[str, Any] = {}
    for layer in layers:
        ids = [item["id"] for item in rubric if item["layer"] == layer]
        rows = [r for r in results if r["id"] in ids]
        executable = [r for r in rows if r["status"] != "skip"]
        passed = [r for r in rows if r["status"] == "pass"]
        failed = [r for r in rows if r["status"] == "fail"]
        skipped = [r for r in rows if r["status"] == "skip"]
        by_layer[layer] = {
            "total": len(rows),
            "executable": len(executable),
            "passed": len(passed),
            "failed": len(failed),
            "skipped": len(skipped),
            "percent_executable_passed": round(100 * len(passed) / len(executable), 2) if executable else 0.0,
            "percent_total_passed": round(100 * len(passed) / len(rows), 2) if rows else 0.0,
        }
    executable = [r for r in results if r["status"] != "skip"]
    passed = [r for r in results if r["status"] == "pass"]
    total_weight = sum(weights.get(r["id"], 1) for r in results)
    executable_weight = sum(weights.get(r["id"], 1) for r in executable)
    passed_weight = sum(weights.get(r["id"], 1) for r in passed)
    return {
        "total_checks": len(results),
        "executable_checks": len(executable),
        "passed": len(passed),
        "failed": len([r for r in results if r["status"] == "fail"]),
        "skipped": len([r for r in results if r["status"] == "skip"]),
        "percent_executable_passed": round(100 * len(passed) / len(executable), 2) if executable else 0.0,
        "percent_total_passed": round(100 * len(passed) / len(results), 2) if results else 0.0,
        "weighted_percent_executable_passed": round(100 * passed_weight / executable_weight, 2) if executable_weight else 0.0,
        "weighted_percent_total_passed": round(100 * passed_weight / total_weight, 2) if total_weight else 0.0,
        "by_layer": by_layer,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run executable FlowLedger hidden checks.")
    parser.add_argument("candidate", help="Candidate package root or solution directory.")
    parser.add_argument("--output", help="Optional path to write JSON report.")
    parser.add_argument("--tracebacks", action="store_true", help="Include Python tracebacks for failed checks.")
    args = parser.parse_args(argv)

    rubric = load_rubric()
    prepare_candidate(Path(args.candidate))

    results: list[dict[str, Any]] = []
    for item in rubric:
        check_id = item["id"]
        row = {
            "id": check_id,
            "layer": item["layer"],
            "category": item.get("category"),
            "weight": item.get("weight", 1),
            "description": item.get("description"),
            "requirement_refs": item.get("requirement_refs", []),
            "feature_pure_notes": item.get("feature_pure_notes"),
            "status": "fail",
            "message": "",
        }
        fn = CHECKS.get(check_id)
        if fn is None:
            row["status"] = "skip"
            row["message"] = "No executable check registered."
        else:
            try:
                fn()
                row["status"] = "pass"
                row["message"] = "passed"
            except SkipCheck as exc:
                row["status"] = "skip"
                row["message"] = str(exc)
            except Exception as exc:  # noqa: BLE001 - scorer reports every failure.
                row["status"] = "fail"
                row["message"] = str(exc) or exc.__class__.__name__
                if args.tracebacks:
                    row["traceback"] = traceback.format_exc()
        results.append(row)

    report = {
        "task_id": "workflowscheduler-fullrepro-001",
        "candidate": str(Path(args.candidate).resolve()),
        "summary": result_counts(results, rubric),
        "checks": results,
        "non_executable_rows": [
            {"id": r["id"], "layer": r["layer"], "reason": r["message"]}
            for r in results
            if r["status"] == "skip"
        ],
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
