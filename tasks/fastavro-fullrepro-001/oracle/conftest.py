# Spec2Repo oracle - shared fixtures for fastavro-fullrepro-001

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic tests that must work before an integration seam is meaningful",
    )


def make_user_schema(name: str = "Profile") -> dict:
    return {
        "type": "record",
        "name": name,
        "namespace": "demo.people",
        "fields": [
            {"name": "id", "type": "long"},
            {"name": "name", "type": "string"},
            {"name": "active", "type": "boolean", "default": True},
            {"name": "score", "type": ["null", "double"], "default": None},
            {"name": "tags", "type": {"type": "array", "items": "string"}, "default": []},
        ],
    }


def make_user_records() -> list[dict]:
    return [
        {"id": 31, "name": "Ada", "active": True, "score": 8.5, "tags": ["core", "blue"]},
        {"id": 32, "name": "Ben", "active": False, "score": None, "tags": []},
        {"id": 33, "name": "Cy", "active": True, "score": 6.25, "tags": ["edge"]},
    ]


def write_avro_bytes(schema: dict, records, **kwargs) -> bytes:
    import fastavro

    bio = io.BytesIO()
    fastavro.writer(bio, schema, records, **kwargs)
    return bio.getvalue()


def write_avro_file(tmp_path: Path, schema: dict, records, name: str = "sample.avro", **kwargs) -> Path:
    path = tmp_path / name
    path.write_bytes(write_avro_bytes(schema, records, **kwargs))
    return path


def run_fastavro_cli(args, *, input_bytes: bytes | None = None):
    command = [sys.executable, "-m", "fastavro", *map(str, args)]
    return subprocess.run(
        command,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def json_lines(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


@pytest.fixture
def user_schema() -> dict:
    return make_user_schema()


@pytest.fixture
def user_records() -> list[dict]:
    return make_user_records()
