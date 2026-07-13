"""Workflow spec loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .models import FlowLedgerError, StepSpec, WorkflowSpec


def _scalar(text: str) -> Any:
    text = text.strip()
    if text == "":
        return ""
    if text in {"null", "Null", "NULL", "~"}:
        return None
    if text in {"true", "True", "TRUE"}:
        return True
    if text in {"false", "False", "FALSE"}:
        return False
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part.strip()) for part in inner.split(",")]
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            result: dict[str, Any] = {}
            inner = text[1:-1].strip()
            if not inner:
                return result
            for part in inner.split(","):
                key, value = part.split(":", 1)
                result[str(_scalar(key.strip()))] = _scalar(value.strip())
            return result
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def _yaml_lines(text: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        line = raw.split(" #", 1)[0].rstrip()
        indent = len(line) - len(line.lstrip(" "))
        rows.append((indent, line.strip()))
    return rows


def _parse_yaml_block(rows: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(rows):
        return {}, index
    if rows[index][1].startswith("- "):
        result: list[Any] = []
        while index < len(rows) and rows[index][0] == indent and rows[index][1].startswith("- "):
            body = rows[index][1][2:].strip()
            index += 1
            if body and ":" in body:
                key, value = body.split(":", 1)
                item: dict[str, Any] = {}
                if value.strip():
                    item[key.strip()] = _scalar(value.strip())
                elif index < len(rows) and rows[index][0] > indent:
                    nested, index = _parse_yaml_block(rows, index, rows[index][0])
                    item[key.strip()] = nested
                if index < len(rows) and rows[index][0] > indent:
                    nested, index = _parse_yaml_block(rows, index, rows[index][0])
                    if isinstance(nested, dict):
                        item.update(nested)
                result.append(item)
            elif body:
                result.append(_scalar(body))
            elif index < len(rows) and rows[index][0] > indent:
                nested, index = _parse_yaml_block(rows, index, rows[index][0])
                result.append(nested)
            else:
                result.append(None)
        return result, index

    result: dict[str, Any] = {}
    while index < len(rows) and rows[index][0] == indent and not rows[index][1].startswith("- "):
        key, value = rows[index][1].split(":", 1)
        index += 1
        if value.strip():
            result[key.strip()] = _scalar(value.strip())
        elif index < len(rows) and rows[index][0] > indent:
            nested, index = _parse_yaml_block(rows, index, rows[index][0])
            result[key.strip()] = nested
        else:
            result[key.strip()] = {}
    return result, index


def _simple_yaml_load(text: str) -> Any:
    rows = _yaml_lines(text)
    if not rows:
        return {}
    value, index = _parse_yaml_block(rows, 0, rows[0][0])
    if index != len(rows):
        raise FlowLedgerError("invalid_spec", "could not parse YAML spec")
    return value


def load_spec(data: dict[str, Any] | str | Path) -> WorkflowSpec:
    """Load and normalize a workflow spec from a mapping, JSON/YAML text, or path."""
    raw: Any = data
    if isinstance(data, Path):
        raw = data.read_text(encoding="utf-8")
    elif isinstance(data, str):
        text = data.strip()
        looks_like_document = text.startswith("{") or text.startswith("[") or "\n" in data or ":" in data
        if not looks_like_document:
            try:
                path = Path(data)
                if path.exists():
                    raw = path.read_text(encoding="utf-8")
            except OSError:
                pass
    if isinstance(raw, str):
        raw = raw.lstrip("\ufeff")
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            try:
                import yaml  # type: ignore
            except Exception as exc:
                raw = _simple_yaml_load(raw)
            else:
                raw = yaml.safe_load(raw)
    if not isinstance(raw, dict):
        raise FlowLedgerError("invalid_spec", "workflow spec must be an object")

    steps = []
    for item in raw.get("steps", []):
        if not isinstance(item, dict):
            raise FlowLedgerError("invalid_spec", "each step must be an object")
        steps.append(
            StepSpec(
                id=str(item.get("id", "")),
                action=str(item.get("action", "ok")),
                depends=list(item.get("depends", []) or []),
                with_args=dict(item.get("with", {}) or {}),
                retry=dict(item.get("retry", {}) or {}),
            )
        )
    spec = WorkflowSpec(
        name=str(raw.get("name", "")),
        mode=str(raw.get("mode", "graph")),
        params=dict(raw.get("params", {}) or {}),
        queue=str(raw.get("queue", "default")),
        max_active_runs=int(raw.get("max_active_runs", 1)),
        schedule=dict(raw["schedule"]) if raw.get("schedule") is not None else None,
        steps=steps,
    )
    validate_spec(spec)
    return spec


def validate_spec(spec: WorkflowSpec) -> None:
    """Validate a spec without writing durable state."""
    if not spec.name:
        raise FlowLedgerError("invalid_spec", "workflow name is required")
    if spec.mode not in {"graph", "chain"}:
        raise FlowLedgerError("invalid_spec", "mode must be graph or chain", {"mode": spec.mode})
    if not isinstance(spec.params, dict):
        raise FlowLedgerError("invalid_spec", "params must be an object")
    if not spec.queue:
        raise FlowLedgerError("invalid_spec", "queue must be non-empty")
    if not isinstance(spec.max_active_runs, int) or spec.max_active_runs < 1:
        raise FlowLedgerError("invalid_spec", "max_active_runs must be a positive integer")
    if not spec.steps:
        raise FlowLedgerError("invalid_spec", "steps must be non-empty")

    ids: set[str] = set()
    for step in spec.steps:
        if not step.id:
            raise FlowLedgerError("invalid_spec", "step id is required")
        if step.id in ids:
            raise FlowLedgerError("invalid_spec", "step ids must be unique", {"step_id": step.id})
        ids.add(step.id)
        if step.action not in {"ok", "fail", "emit", "wait"}:
            raise FlowLedgerError("invalid_spec", "unknown step action", {"step_id": step.id, "action": step.action})
        if not isinstance(step.with_args, dict):
            raise FlowLedgerError("invalid_spec", "step with must be an object", {"step_id": step.id})
        if not isinstance(step.retry, dict):
            raise FlowLedgerError("invalid_spec", "step retry must be an object", {"step_id": step.id})
        if step.retry:
            if int(step.retry.get("limit", 0)) < 0 or int(step.retry.get("delay_seconds", 0)) < 0:
                raise FlowLedgerError("invalid_spec", "retry limit and delay_seconds must be non-negative", {"step_id": step.id})
        if spec.mode == "chain" and step.depends:
            raise FlowLedgerError("invalid_spec", "chain mode does not allow explicit depends", {"step_id": step.id})
    if spec.mode == "graph":
        for step in spec.steps:
            for dep in step.depends:
                if dep not in ids:
                    raise FlowLedgerError("invalid_spec", "step depends on an unknown step", {"step_id": step.id, "depends": dep})
        visiting: set[str] = set()
        visited: set[str] = set()
        by_id = {s.id: s for s in spec.steps}

        def visit(step_id: str) -> None:
            if step_id in visited:
                return
            if step_id in visiting:
                raise FlowLedgerError("invalid_spec", "step dependency cycle detected", {"step_id": step_id})
            visiting.add(step_id)
            for dep_id in by_id[step_id].depends:
                visit(dep_id)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in ids:
            visit(step_id)
    if spec.schedule is not None:
        schedule = spec.schedule
        every = int(schedule.get("every_seconds", 0))
        if every <= 0:
            raise FlowLedgerError("invalid_spec", "schedule every_seconds must be positive")
        if schedule.get("catchup", "latest") not in {"skip", "latest", "all"}:
            raise FlowLedgerError("invalid_spec", "schedule catchup must be skip, latest, or all")
        if schedule.get("overlap", "skip") not in {"skip", "latest", "all"}:
            raise FlowLedgerError("invalid_spec", "schedule overlap must be skip, latest, or all")


def spec_to_dict(spec: WorkflowSpec) -> dict[str, Any]:
    """Return a deterministic JSON-compatible public spec."""
    return {
        "name": spec.name,
        "mode": spec.mode,
        "params": dict(spec.params),
        "queue": spec.queue,
        "max_active_runs": spec.max_active_runs,
        "schedule": dict(spec.schedule) if spec.schedule is not None else None,
        "steps": [
            {
                "id": step.id,
                "depends": list(step.depends),
                "action": step.action,
                "with": dict(step.with_args),
                "retry": dict(step.retry),
            }
            for step in spec.steps
        ],
    }
