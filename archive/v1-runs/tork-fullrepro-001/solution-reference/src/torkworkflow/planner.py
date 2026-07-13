from __future__ import annotations

from copy import deepcopy

from .models import JobRecord, JobSpec, TaskRecord
from .progress import job_progress


def build_records(spec: JobSpec, *, job_id: str, now: int) -> tuple[JobRecord, list[TaskRecord]]:
    """Create initial job and task records from a JobSpec."""
    tasks: list[TaskRecord] = []
    prior_roots: list[str] = []
    counter = 0

    def next_id(name: str) -> str:
        nonlocal counter
        counter += 1
        safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-") or "task"
        return f"{job_id}-t{counter:04d}-{safe[:32]}"

    def add_task(task_spec, deps: list[str], parent_id: str | None = None, meta: dict | None = None) -> list[str]:
        nonlocal counter
        created: list[str] = []
        all_deps = list(deps)
        for pre in task_spec.pre:
            pre_ids = add_task(pre, all_deps, parent_id=parent_id)
            all_deps = pre_ids or all_deps

        child_specs = list(task_spec.parallel)
        if task_spec.each is not None:
            items = task_spec.each.get("items", [])
            var_name = task_spec.each.get("var", "item")
            template = task_spec.each.get("task")
            for idx, item in enumerate(items):
                if template is None:
                    child = deepcopy(task_spec)
                    child.pre = []
                    child.post = []
                    child.parallel = []
                    child.each = None
                    child.name = f"{task_spec.name}[{idx}]"
                    child.run = task_spec.each.get("run", child.run)
                    child.var = task_spec.each.get("var", child.var)
                else:
                    from .parser import _normalize_task

                    child = _normalize_task(template, f"{task_spec.name}[{idx}]")
                child.raw = dict(child.raw)
                child.raw["_each"] = {"var": var_name, "value": item, "index": idx}
                child_specs.append(child)
        if task_spec.subjob:
            sub_tasks = task_spec.subjob.get("tasks") or task_spec.subjob.get("steps") or []
            for idx, item in enumerate(sub_tasks):
                from .parser import _normalize_task

                child_specs.append(_normalize_task(item, f"{task_spec.name}-subjob-{idx + 1}"))

        if child_specs:
            task_id = next_id(task_spec.name)
            record = TaskRecord(
                id=task_id,
                job_id=job_id,
                name=task_spec.name,
                parent_id=parent_id,
                run=task_spec.run,
                var=task_spec.var,
                if_expr=task_spec.if_expr,
                retry_limit=task_spec.retry.limit if task_spec.retry else 0,
                retry_delay_seconds=task_spec.retry.delay_seconds if task_spec.retry else 0,
                timeout_seconds=task_spec.timeout_seconds,
                depends_on=list(all_deps),
                index=counter,
                kind="group",
                metadata=_group_meta(task_spec, meta),
            )
            tasks.append(record)
            child_terminal_ids: list[str] = []
            for child in child_specs:
                child_ids = add_task(child, all_deps, parent_id=task_id, meta=_item_meta(child))
                child_terminal_ids.extend(child_ids)
            record.children = [task.id for task in tasks if task.parent_id == task_id]
            created = child_terminal_ids or [task_id]
            if task_spec.run:
                run_id = next_id(f"{task_spec.name}-self")
                run_record = _record_from_spec(task_spec, job_id, run_id, all_deps + child_terminal_ids, parent_id, counter, meta)
                tasks.append(run_record)
                created = [run_id]
        else:
            task_id = next_id(task_spec.name)
            record = _record_from_spec(task_spec, job_id, task_id, all_deps, parent_id, counter, meta or _item_meta(task_spec))
            tasks.append(record)
            created = [task_id]

        post_deps = created
        for post in task_spec.post:
            post_deps = add_task(post, post_deps, parent_id=parent_id)
        return post_deps or created

    for task_spec in spec.tasks:
        prior_roots = add_task(task_spec, prior_roots)

    job = JobRecord(
        id=job_id,
        name=spec.name,
        created_at=now,
        updated_at=now,
        task_ids=[task.id for task in tasks],
        metadata={"inputs": spec.inputs, "secrets": spec.secrets, "output": spec.output, "outputs": {}},
    )
    return job, tasks


def _item_meta(task_spec) -> dict:
    each = task_spec.raw.get("_each") if getattr(task_spec, "raw", None) else None
    if not each:
        return {}
    return {"item": {each["var"]: each["value"], "item": each["value"], "index": each["index"]}}


def _record_from_spec(task_spec, job_id: str, task_id: str, deps: list[str], parent_id: str | None, index: int, meta: dict | None) -> TaskRecord:
    return TaskRecord(
        id=task_id,
        job_id=job_id,
        name=task_spec.name,
        parent_id=parent_id,
        run=task_spec.run,
        var=task_spec.var,
        if_expr=task_spec.if_expr,
        retry_limit=task_spec.retry.limit if task_spec.retry else 0,
        retry_delay_seconds=task_spec.retry.delay_seconds if task_spec.retry else 0,
        timeout_seconds=task_spec.timeout_seconds,
        depends_on=list(deps),
        index=index,
        kind="task",
        metadata=dict(meta or {}),
    )


def runnable_tasks(job: JobRecord, tasks: list[TaskRecord]) -> list[TaskRecord]:
    """Return tasks whose dependencies are satisfied."""
    by_id = {task.id: task for task in tasks}
    runnable = []
    if job.state in {"FAILED", "CANCELED", "COMPLETED"}:
        return runnable
    for task in tasks:
        if task.state != "PENDING" or task.kind == "group":
            continue
        if all(by_id[dep].state in {"COMPLETED", "SKIPPED"} for dep in task.depends_on if dep in by_id):
            runnable.append(task)
    return sorted(runnable, key=lambda task: (task.index, task.id))


def rollup_job_state(job: JobRecord, tasks: list[TaskRecord]) -> JobRecord:
    """Update job state/output/progress from task records."""
    if job.state == "CANCELED":
        return job
    if any(task.state == "FAILED" for task in tasks):
        job.state = "FAILED"
    elif all(task.state in {"COMPLETED", "SKIPPED"} for task in tasks):
        job.state = "COMPLETED"
    elif any(task.state == "RUNNING" for task in tasks):
        job.state = "RUNNING"
    elif any(task.state == "QUEUED" for task in tasks):
        job.state = "QUEUED"
    else:
        job.state = "QUEUED"
    outputs = dict(job.metadata.get("outputs", {}))
    completed = [task for task in tasks if task.state == "COMPLETED" and task.output is not None]
    for task in completed:
        outputs.setdefault(task.name, task.output)
        if task.var:
            outputs[task.var] = task.output
    job.metadata["outputs"] = outputs
    wanted_output = job.metadata.get("output")
    if wanted_output:
        job.output = _resolve_output(wanted_output, outputs, job.output)
    elif completed:
        job.output = completed[-1].output
    job.metadata["progress"] = job_progress(job, tasks)
    return job


def _group_meta(task_spec, meta: dict | None) -> dict:
    result = dict(meta or {})
    if task_spec.subjob and isinstance(task_spec.subjob, dict) and task_spec.subjob.get("output"):
        result["output"] = task_spec.subjob.get("output")
    return result


def _resolve_output(expr: str, outputs: dict, default=None):
    text = str(expr).strip()
    if text.startswith("{{") and text.endswith("}}"):
        text = text[2:-2].strip()
    if text.startswith("tasks."):
        text = text.split(".", 1)[1]
    if text.startswith("outputs."):
        text = text.split(".", 1)[1]
    return outputs.get(text, default)
