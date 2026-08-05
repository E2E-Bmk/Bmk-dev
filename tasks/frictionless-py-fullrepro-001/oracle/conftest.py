from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

from frictionless import (
    Analyzer,
    Detector,
    Dialect,
    Error,
    Field,
    Package,
    Pipeline,
    Report,
    Resource,
    Schema,
    describe,
    extract,
    transform,
    validate,
)
from frictionless import fields, steps


VALID_CSV = (
    "id,name,active,score\n"
    "1,Ada,true,2.5\n"
    "2,Bob,false,3.0\n"
    "3,Cleo,true,4.25\n"
)

INVALID_CSV = (
    "id,name,score\n"
    "1,Ada,2.5\n"
    "bad,Bob,not-a-number\n"
)


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


def write_local(tmp_path: Path, filename: str, content: str) -> str:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    return filename


def write_json(tmp_path: Path, filename: str, value: Any) -> str:
    path = tmp_path / filename
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return filename


def local_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    filename: str = "table.csv",
    content: str = VALID_CSV,
) -> str:
    monkeypatch.chdir(tmp_path)
    return write_local(tmp_path, filename, content)


def rows_as_dicts(resource: Resource) -> list[dict[str, Any]]:
    return [
        {field_name: row[field_name] for field_name in row.field_names}
        for row in resource.read_rows()
    ]


def normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: normalize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_value(item) for item in value]
    return value


def normalized_rows(resource: Resource) -> list[dict[str, Any]]:
    return normalize_value(rows_as_dicts(resource))


def structured_error(error: Error) -> dict[str, Any]:
    descriptor = error.to_descriptor()
    keys = (
        "type",
        "rowNumber",
        "fieldName",
        "fieldNumber",
        "cell",
        "code",
        "resourceName",
        "fieldNames",
        "referenceName",
    )
    return {key: descriptor[key] for key in keys if key in descriptor}


def report_projection(report: Report) -> dict[str, Any]:
    return {
        "valid": report.valid,
        "stats": {
            key: report.stats[key]
            for key in ("tasks", "errors", "warnings")
            if key in report.stats
        },
        "warnings": list(report.warnings),
        "errors": [structured_error(error) for error in report.errors],
        "tasks": [
            {
                "name": task.name,
                "type": task.type,
                "valid": task.valid,
                "labels": list(task.labels),
                "stats": {
                    key: task.stats[key]
                    for key in ("errors", "warnings", "fields", "rows")
                    if key in task.stats
                },
                "warnings": list(task.warnings),
                "errors": [structured_error(error) for error in task.errors],
            }
            for task in report.tasks
        ],
    }


def simple_schema() -> Schema:
    return Schema.from_descriptor(
        {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
                {"name": "score", "type": "number"},
            ]
        }
    )


def typed_inline_resource() -> Resource:
    return Resource(
        name="scores",
        data=[
            ["id", "name", "score"],
            [1, "Ada", "2.5"],
            [2, "Bob", "3.0"],
        ],
    )


def valid_resource_with_schema() -> Resource:
    return Resource(
        name="scores",
        data=[
            ["id", "name", "score"],
            [1, "Ada", "2.5"],
            [2, "Bob", "3.0"],
        ],
        schema=simple_schema(),
    )


__all__ = [
    "Analyzer",
    "Detector",
    "Dialect",
    "Error",
    "Field",
    "Package",
    "Pipeline",
    "Report",
    "Resource",
    "Schema",
    "VALID_CSV",
    "INVALID_CSV",
    "describe",
    "extract",
    "fields",
    "local_csv",
    "normalize_value",
    "normalized_rows",
    "report_projection",
    "rows_as_dicts",
    "simple_schema",
    "steps",
    "transform",
    "typed_inline_resource",
    "valid_resource_with_schema",
    "validate",
    "write_json",
    "write_local",
]
