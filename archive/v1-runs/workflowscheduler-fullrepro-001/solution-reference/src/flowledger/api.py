"""Integrated FlowLedger facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import queue as queue_mod
from .export import export_snapshot, import_snapshot
from .history import history_report, next_runs_report, status_report
from .logs import append_event, append_log, event_stream, log_stream
from .models import FlowLedgerError, utc
from .recovery import recover as recover_state
from .retry import retry_decision
from .runner import run_action
from .scheduler import apply_overlap, due_slots
from .spec import load_spec, spec_to_dict
from .store import JsonStore


TERMINAL_RUNS = {"succeeded", "failed", "cancelled"}
TERMINAL_STEPS = {"succeeded", "failed", "skipped", "cancelled"}

class FlowLedger:
    """Durable local workflow scheduler facade."""

    def __init__(self, store_path: str | Path):
        self.store = JsonStore(store_path)
        self.store.init()

    def init(self) -> dict[str, Any]:
        self.store.init()
        return {"initialized": True, "store": str(self.store.path)}

    def put_spec(self, spec: dict[str, Any] | str | Path) -> dict[str, Any]:
        self.store.load()
        loaded = load_spec(spec)
        public = spec_to_dict(loaded)
        self.store.data["specs"][loaded.name] = public
        if loaded.schedule is not None:
            self.store.data["schedules"].setdefault(loaded.name, {"last_slot": None})
        elif loaded.name in self.store.data["schedules"]:
            self.store.data["schedules"].pop(loaded.name, None)
        self.store.save()
        return {"stored": True, "spec": public}

    def tick(self, now: str) -> dict[str, Any]:
        self.store.load()
        now = utc(now)
        recovery = recover_state(self.store, now)
        materialized: list[dict[str, Any]] = []
        cancelled: list[str] = []
        for name, spec_data in sorted(self.store.data["specs"].items()):
            spec = load_spec(spec_data)
            if not spec.schedule:
                continue
            schedule_state = self.store.data["schedules"].setdefault(name, {"last_slot": None})
            slots = due_slots(spec, schedule_state.get("last_slot"), now)
            if not slots:
                continue
            active_ids = [
                run["id"]
                for run in self.store.data["runs"].values()
                if run.get("workflow") == name and run.get("status") not in TERMINAL_RUNS
            ]
            queued_ids = [
                run["id"]
                for run in self.store.data["runs"].values()
                if run.get("workflow") == name and run.get("status") == "queued" and run.get("scheduled_slot")
            ]
            decision = apply_overlap(spec.schedule.get("overlap", "skip"), active_ids, queued_ids, slots)
            for run_id in decision["cancel_run_ids"]:
                run = self.store.data["runs"].get(run_id)
                if not run:
                    continue
                run["status"] = "cancelled"
                run["updated_at"] = now
                for step in self.store.data["steps"].get(run_id, {}).values():
                    if step.get("status") not in TERMINAL_STEPS:
                        step["status"] = "cancelled"
                        step["updated_at"] = now
                for item in self.store.data["queue"]:
                    if item.get("run_id") == run_id and item.get("status") in {"queued", "leased"}:
                        item["status"] = "cancelled"
                        item["cancelled_at"] = now
                append_event(self.store, {"recorded_at": now, "type": "run_cancelled", "run_id": run_id, "workflow": run["workflow"]})
                cancelled.append(run_id)
            for slot in decision["enqueue_slots"]:
                materialized.append(self._create_run(spec, now, params=None, scheduled_slot=slot))
            schedule_state["last_slot"] = slots[-1]
        self.store.save()
        return {"now": now, "materialized": materialized, "cancelled_run_ids": cancelled, "recovery": recovery}

    def start(self, workflow: str, now: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.store.load()
        spec = self._spec(workflow)
        result = self._create_run(spec, utc(now), params=params, scheduled_slot=None)
        self.store.save()
        return result

    def claim(self, queue: str, worker_id: str, now: str, lease_seconds: int = 60) -> dict[str, Any] | None:
        self.store.load()
        item = queue_mod.claim(self.store, queue, worker_id, utc(now), lease_seconds)
        if item is None:
            return None
        mutable = self._queue_item(item["id"])
        if item.get("type") == "step":
            run = self.store.data["runs"].get(item["run_id"])
            step = self.store.data["steps"][item["run_id"]][item["step_id"]]
            spec_step = self._spec_step(run["workflow"], item["step_id"]) if run else None
            step["status"] = "running"
            step["attempt_count"] = int(step.get("attempt_count", 0)) + 1
            step["updated_at"] = utc(now)
            attempt = {
                "run_id": item["run_id"],
                "step_id": item["step_id"],
                "attempt": step["attempt_count"],
                "status": "running",
                "started_at": utc(now),
                "finished_at": None,
                "output": None,
                "error": None,
                "queue_item_id": item["id"],
            }
            self.store.data["attempts"].append(attempt)
            if run and run.get("status") == "queued":
                run["status"] = "running"
            if run:
                run["updated_at"] = utc(now)
            append_event(self.store, {"recorded_at": utc(now), "type": "step_claimed", "run_id": item["run_id"], "step_id": item["step_id"], "item_id": item["id"], "worker_id": worker_id})
            item = {**item, "action": spec_step.action if spec_step else None, "with": dict(spec_step.with_args) if spec_step else {}}
            if spec_step:
                item["execution"] = run_action(spec_step.action, spec_step.with_args, utc(now))
        elif item.get("type") == "run":
            append_event(self.store, {"recorded_at": utc(now), "type": "run_claimed", "run_id": item["run_id"], "item_id": item["id"], "worker_id": worker_id})
        mutable.update({k: v for k, v in item.items() if k in mutable})
        self.store.save()
        return item

    def complete(self, item_id: str, worker_id: str, now: str, output: Any = None) -> dict[str, Any]:
        self.store.load()
        now = utc(now)
        item = self._queue_item(item_id)
        queue_mod.ack(self.store, item_id, worker_id, now)
        if item.get("type") == "run":
            run = self._run(item["run_id"])
            run["status"] = "running"
            run["updated_at"] = now
            append_event(self.store, {"recorded_at": now, "type": "run_started", "run_id": run["id"], "workflow": run["workflow"]})
            self._enqueue_ready_steps(run["id"], now)
            self._refresh_run_status(run["id"], now)
            self.store.save()
            return self.status(run_id=run["id"])
        if item.get("type") != "step":
            raise FlowLedgerError("invalid_queue_item", "unknown queue item type", {"item_id": item_id})
        run = self._run(item["run_id"])
        step = self.store.data["steps"][run["id"]][item["step_id"]]
        spec_step = self._spec_step(run["workflow"], item["step_id"])
        result = run_action(spec_step.action, spec_step.with_args, now)
        if result["status"] == "failed":
            report = self._record_step_failure(run["id"], item["step_id"], now, result["error"])
            self.store.save()
            return report
        if result["status"] == "waiting":
            step["status"] = "queued"
            step["updated_at"] = now
            step["next_attempt_at"] = result["until"]
            self._finish_attempt(run["id"], item["step_id"], item_id, "queued", now, {"waiting_until": result["until"]}, None)
            for event in result.get("events", []):
                append_event(self.store, {"recorded_at": now, "run_id": run["id"], "step_id": item["step_id"], **event})
            queue_mod.enqueue(self.store, {"type": "step", "workflow": run["workflow"], "run_id": run["id"], "step_id": item["step_id"], "queue": step.get("queue", "default"), "created_at": now, "visible_at": result["until"]})
            self.store.save()
            return self.status(run_id=run["id"])
        final_output = output if output is not None else result.get("output")
        for log in result.get("logs", []):
            append_log(self.store, {"recorded_at": now, "run_id": run["id"], "step_id": item["step_id"], **log})
        step["status"] = "succeeded"
        step["output"] = final_output
        step["updated_at"] = now
        step["next_attempt_at"] = None
        self._finish_attempt(run["id"], item["step_id"], item_id, "succeeded", now, final_output, None)
        append_event(self.store, {"recorded_at": now, "type": "step_succeeded", "run_id": run["id"], "step_id": item["step_id"], "item_id": item_id})
        self._enqueue_ready_steps(run["id"], now)
        self._refresh_run_status(run["id"], now)
        self.store.save()
        return self.status(run_id=run["id"])

    def fail(self, item_id: str, worker_id: str, now: str, error: dict[str, Any]) -> dict[str, Any]:
        self.store.load()
        now = utc(now)
        item = self._queue_item(item_id)
        queue_mod.ack(self.store, item_id, worker_id, now)
        if item.get("type") == "run":
            run = self._run(item["run_id"])
            run["status"] = "failed"
            run["updated_at"] = now
            append_event(self.store, {"recorded_at": now, "type": "run_failed", "run_id": run["id"], "error": dict(error)})
            self.store.save()
            return self.status(run_id=run["id"])
        if item.get("type") != "step":
            raise FlowLedgerError("invalid_queue_item", "unknown queue item type", {"item_id": item_id})
        result = self._record_step_failure(item["run_id"], item["step_id"], now, dict(error))
        self.store.save()
        return result

    def cancel(self, run_id: str, now: str) -> dict[str, Any]:
        self.store.load()
        now = utc(now)
        run = self._run(run_id)
        run["status"] = "cancelled"
        run["updated_at"] = now
        for step in self.store.data["steps"].get(run_id, {}).values():
            if step.get("status") not in TERMINAL_STEPS:
                step["status"] = "cancelled"
                step["updated_at"] = now
        for item in self.store.data["queue"]:
            if item.get("run_id") == run_id and item.get("status") in {"queued", "leased"}:
                item["status"] = "cancelled"
                item["cancelled_at"] = now
        append_event(self.store, {"recorded_at": now, "type": "run_cancelled", "run_id": run_id, "workflow": run["workflow"]})
        self.store.save()
        return status_report(self.store, run_id=run_id)

    def status(self, workflow: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        self.store.load()
        return status_report(self.store, workflow, run_id)

    def history(self, workflow: str | None = None) -> dict[str, Any]:
        self.store.load()
        return history_report(self.store, workflow)

    def queue(self) -> dict[str, Any]:
        self.store.load()
        return queue_mod.queue_report(self.store)

    def next_runs(self, now: str) -> dict[str, Any]:
        self.store.load()
        return next_runs_report(self.store, utc(now))

    def logs(self, run_id: str | None = None) -> list[dict[str, Any]]:
        self.store.load()
        return log_stream(self.store, run_id)

    def events(self, run_id: str | None = None) -> list[dict[str, Any]]:
        self.store.load()
        return event_stream(self.store, run_id)

    def recover(self, now: str) -> dict[str, Any]:
        self.store.load()
        result = recover_state(self.store, utc(now))
        self.store.save()
        return result

    def export(self) -> dict[str, Any]:
        self.store.load()
        return export_snapshot(self.store)

    def import_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        self.store.load()
        return import_snapshot(self.store, snapshot)

    def _spec(self, workflow: str):
        if workflow not in self.store.data["specs"]:
            raise FlowLedgerError("not_found", "workflow spec not found", {"workflow": workflow})
        return load_spec(self.store.data["specs"][workflow])

    def _spec_step(self, workflow: str, step_id: str):
        spec = self._spec(workflow)
        for step in spec.steps:
            if step.id == step_id:
                return step
        raise FlowLedgerError("not_found", "step spec not found", {"workflow": workflow, "step_id": step_id})

    def _run(self, run_id: str) -> dict[str, Any]:
        run = self.store.data["runs"].get(run_id)
        if not run:
            raise FlowLedgerError("not_found", "run not found", {"run_id": run_id})
        return run

    def _queue_item(self, item_id: str) -> dict[str, Any]:
        for item in self.store.data["queue"]:
            if item.get("id") == item_id:
                return item
        raise FlowLedgerError("not_found", "queue item not found", {"item_id": item_id})

    def _create_run(self, spec, now: str, params: dict[str, Any] | None, scheduled_slot: str | None) -> dict[str, Any]:
        run_id = self.store.next_id("run")
        merged_params = dict(spec.params)
        if params:
            merged_params.update(params)
        run = {
            "id": run_id,
            "workflow": spec.name,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "params": merged_params,
            "scheduled_slot": scheduled_slot,
        }
        self.store.data["runs"][run_id] = run
        self.store.data["steps"][run_id] = {}
        previous_id: str | None = None
        for index, step in enumerate(spec.steps):
            depends = [previous_id] if spec.mode == "chain" and previous_id else list(step.depends)
            self.store.data["steps"][run_id][step.id] = {
                "run_id": run_id,
                "step_id": step.id,
                "status": "pending",
                "order": index,
                "depends": depends,
                "queue": spec.queue,
                "attempt_count": 0,
                "next_attempt_at": None,
                "output": None,
                "error": None,
                "updated_at": now,
            }
            previous_id = step.id
        item = queue_mod.enqueue(self.store, {"type": "run", "workflow": spec.name, "run_id": run_id, "queue": spec.queue, "created_at": now, "visible_at": now})
        append_event(self.store, {"recorded_at": now, "type": "run_queued", "run_id": run_id, "workflow": spec.name, "scheduled_slot": scheduled_slot, "item_id": item["id"]})
        return {"run": dict(run), "queue_item": item}

    def _enqueue_ready_steps(self, run_id: str, now: str) -> list[dict[str, Any]]:
        run = self._run(run_id)
        if run.get("status") in TERMINAL_RUNS:
            return []
        steps = self.store.data["steps"][run_id]
        enqueued: list[dict[str, Any]] = []
        existing = {
            item.get("step_id")
            for item in self.store.data["queue"]
            if item.get("run_id") == run_id and item.get("type") == "step" and item.get("status") in {"queued", "leased"}
        }
        for step_id, step in sorted(steps.items(), key=lambda pair: pair[1].get("order", 0)):
            if step.get("status") != "pending" or step_id in existing:
                continue
            if all(steps[dep]["status"] == "succeeded" for dep in step.get("depends", [])):
                step["status"] = "queued"
                step["updated_at"] = now
                item = queue_mod.enqueue(self.store, {"type": "step", "workflow": run["workflow"], "run_id": run_id, "step_id": step_id, "queue": step.get("queue", "default"), "created_at": now, "visible_at": now})
                append_event(self.store, {"recorded_at": now, "type": "step_queued", "run_id": run_id, "step_id": step_id, "item_id": item["id"]})
                enqueued.append(item)
        return enqueued

    def _finish_attempt(self, run_id: str, step_id: str, item_id: str, status: str, now: str, output: Any, error: dict[str, Any] | None) -> None:
        for attempt in reversed(self.store.data["attempts"]):
            if attempt.get("run_id") == run_id and attempt.get("step_id") == step_id and attempt.get("queue_item_id") == item_id:
                attempt["status"] = status
                attempt["finished_at"] = now
                attempt["output"] = output
                attempt["error"] = error
                return
        self.store.data["attempts"].append({"run_id": run_id, "step_id": step_id, "attempt": 1, "status": status, "started_at": None, "finished_at": now, "output": output, "error": error, "queue_item_id": item_id})

    def _record_step_failure(self, run_id: str, step_id: str, now: str, error: dict[str, Any]) -> dict[str, Any]:
        run = self._run(run_id)
        step = self.store.data["steps"][run_id][step_id]
        spec_step = self._spec_step(run["workflow"], step_id)
        failed_item_id = None
        for item in reversed(self.store.data["queue"]):
            if item.get("run_id") == run_id and item.get("step_id") == step_id and item.get("status") == "acked":
                failed_item_id = item.get("id")
                break
        self._finish_attempt(run_id, step_id, failed_item_id or "", "failed", now, None, error)
        failure_count = len([a for a in self.store.data["attempts"] if a.get("run_id") == run_id and a.get("step_id") == step_id and a.get("status") == "failed"])
        decision = retry_decision(spec_step.retry, failure_count, now)
        step["error"] = error
        step["updated_at"] = now
        if decision["decision"] == "retry_wait":
            step["status"] = "retry_wait"
            step["next_attempt_at"] = decision["next_attempt_at"]
            run["status"] = "running"
            run["updated_at"] = now
            append_event(self.store, {"recorded_at": now, "type": "step_retry_scheduled", "run_id": run_id, "step_id": step_id, "next_attempt_at": decision["next_attempt_at"], "error": error})
        else:
            step["status"] = "failed"
            step["next_attempt_at"] = None
            append_event(self.store, {"recorded_at": now, "type": "step_failed", "run_id": run_id, "step_id": step_id, "error": error})
            for other in self.store.data["steps"][run_id].values():
                if other.get("status") in {"pending", "queued", "retry_wait"}:
                    other["status"] = "skipped"
                    other["updated_at"] = now
            run["status"] = "failed"
            run["updated_at"] = now
            append_event(self.store, {"recorded_at": now, "type": "run_failed", "run_id": run_id, "workflow": run["workflow"]})
        self._refresh_run_status(run_id, now)
        return self.status(run_id=run_id)

    def _refresh_run_status(self, run_id: str, now: str) -> None:
        run = self._run(run_id)
        if run.get("status") in {"cancelled", "failed"}:
            return
        steps = list(self.store.data["steps"][run_id].values())
        if steps and all(step.get("status") == "succeeded" for step in steps):
            run["status"] = "succeeded"
            run["updated_at"] = now
            append_event(self.store, {"recorded_at": now, "type": "run_succeeded", "run_id": run_id, "workflow": run["workflow"]})
        elif any(step.get("status") in {"running", "queued", "retry_wait"} for step in steps):
            run["status"] = "running"
            run["updated_at"] = now
