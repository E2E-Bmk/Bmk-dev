from __future__ import annotations

import json
from typing import Any

try:  # PyYAML is optional; the package also has a small fallback below.
    import yaml
except ModuleNotFoundError:  # pragma: no cover - depends on environment
    yaml = None

from .errors import SpecError
from .models import JobSpec, RetryPolicy, TaskSpec


def parse_job_spec(text: str, *, fmt: str | None = None) -> JobSpec:
    """Parse YAML or JSON text into a public JobSpec."""
    fmt = (fmt or "").lower()
    try:
        if fmt == "json":
            data = json.loads(text)
        elif fmt in {"yaml", "yml"}:
            data = _load_yaml(text)
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = _load_yaml(text)
    except Exception as exc:  # pragma: no cover - exact parser errors vary
        raise SpecError(f"invalid job spec: {exc}") from exc
    if not isinstance(data, dict):
        raise SpecError("job spec must decode to a mapping")
    return normalize_job_spec(data)


def normalize_job_spec(data: dict) -> JobSpec:
    """Normalize a decoded mapping into JobSpec/TaskSpec records."""
    if "job" in data and isinstance(data["job"], dict):
        data = {**data["job"], **{k: v for k, v in data.items() if k != "job"}}
    tasks = data.get("tasks") or data.get("steps")
    if not isinstance(tasks, list) or not tasks:
        raise SpecError("job spec requires a non-empty tasks list")
    name = str(data.get("name") or data.get("id") or "job")
    return JobSpec(
        name=name,
        tasks=[_normalize_task(item, f"task-{idx + 1}") for idx, item in enumerate(tasks)],
        inputs=dict(data.get("inputs") or {}),
        secrets=dict(data.get("secrets") or {}),
        output=data.get("output"),
        schedule=data.get("schedule"),
    )


def _normalize_task(data: Any, default_name: str) -> TaskSpec:
    if isinstance(data, str):
        data = {"name": default_name, "run": data}
    if not isinstance(data, dict):
        raise SpecError("task entries must be mappings or command strings")
    raw = dict(data)
    if "name" not in data and "id" not in data:
        raise SpecError("task entries require a name")
    name = str(data.get("name") or data.get("id") or default_name)
    run = data.get("run", data.get("command", data.get("cmd")))
    retry = _retry(data.get("retry", data.get("retries")))
    timeout = data.get("timeout_seconds", data.get("timeout"))
    return TaskSpec(
        name=name,
        run=str(run) if run is not None else None,
        var=data.get("var", data.get("variable", data.get("output"))),
        if_expr=data.get("if", data.get("if_expr", data.get("when", data.get("condition")))),
        retry=retry,
        timeout_seconds=int(timeout) if timeout is not None else None,
        parallel=[_normalize_task(item, f"{name}-parallel-{idx + 1}") for idx, item in enumerate(data.get("parallel") or [])],
        each=_normalize_each(data.get("each"), name),
        subjob=data.get("subjob", data.get("job")),
        pre=[_normalize_task(item, f"{name}-pre-{idx + 1}") for idx, item in enumerate(data.get("pre") or data.get("before") or [])],
        post=[_normalize_task(item, f"{name}-post-{idx + 1}") for idx, item in enumerate(data.get("post") or data.get("after") or [])],
        raw=raw,
    )


def _retry(value: Any) -> RetryPolicy | None:
    if value is None or value is False:
        return None
    if value is True:
        return RetryPolicy(limit=1)
    if isinstance(value, int):
        return RetryPolicy(limit=value)
    if isinstance(value, dict):
        limit = value.get("limit", value.get("max", value.get("attempts", value.get("retries", 0))))
        if "attempts" in value and "limit" not in value and "retries" not in value:
            limit = max(int(limit) - 1, 0)
        delay = value.get("delay_seconds", value.get("delay", 0))
        return RetryPolicy(limit=int(limit), delay_seconds=int(delay))
    raise SpecError("retry must be a boolean, integer, or mapping")


def _normalize_each(value: Any, name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return {"items": value, "var": "item"}
    if isinstance(value, dict):
        result = dict(value)
        result.setdefault("var", "item")
        if "items" not in result and "in" in result:
            result["items"] = result["in"]
        if "items" not in result:
            raise SpecError(f"each task {name!r} requires items")
        return result
    raise SpecError("each must be a list or mapping")


def _load_yaml(text: str) -> Any:
    if yaml is not None:
        return yaml.safe_load(text)
    return _simple_yaml(text)


def _simple_yaml(text: str) -> Any:
    """Small YAML subset parser for candidate-visible job specs.

    Supports nested mappings, ``-`` list items, scalars, and JSON-style inline
    values. It is intentionally conservative and raises SpecError for ambiguous
    forms instead of trying to emulate full YAML.
    """
    lines = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    if not lines:
        return {}

    def parse_block(index: int, indent: int):
        is_list = lines[index][1].startswith("- ")
        result: Any = [] if is_list else {}
        while index < len(lines):
            line_indent, content = lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                raise SpecError(f"unexpected indentation near: {content}")
            if is_list:
                if not content.startswith("- "):
                    break
                item_text = content[2:].strip()
                if not item_text:
                    item, index = parse_block(index + 1, _next_indent(index, indent))
                elif ":" in item_text and not item_text.startswith(("'", '"')):
                    key, value = item_text.split(":", 1)
                    item = {key.strip(): _scalar(value.strip())} if value.strip() else {}
                    index += 1
                    if index < len(lines) and lines[index][0] > line_indent:
                        extra, index = parse_block(index, lines[index][0])
                        if isinstance(extra, dict):
                            item.update(extra)
                        else:
                            item[key.strip()] = extra
                else:
                    item = _scalar(item_text)
                    index += 1
                result.append(item)
            else:
                if ":" not in content:
                    raise SpecError(f"expected key/value near: {content}")
                key, value = content.split(":", 1)
                key = key.strip()
                value = value.strip()
                index += 1
                if value:
                    result[key] = _scalar(value)
                elif index < len(lines) and lines[index][0] > line_indent:
                    result[key], index = parse_block(index, lines[index][0])
                else:
                    result[key] = {}
        return result, index

    parsed, _ = parse_block(0, lines[0][0])
    return parsed


def _next_indent(index: int, fallback: int) -> int:
    return fallback + 2 if index >= 0 else fallback


def _scalar(text: str) -> Any:
    if text == "":
        return ""
    low = text.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "none"}:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if (text.startswith("'") and text.endswith("'")) or (text.startswith('"') and text.endswith('"')):
        return text[1:-1]
    try:
        return int(text)
    except ValueError:
        return text
