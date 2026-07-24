"""Shared fixtures, helpers, and constants for kedro-pipeline-fullrepro-001 oracle."""
from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from kedro.io import AbstractDataset, DataCatalog, MemoryDataset
from kedro.pipeline import Pipeline, node

os.environ.setdefault("KEDRO_DISABLE_TELEMETRY", "1")


# ---------------------------------------------------------------------------
# Reusable callables
# ---------------------------------------------------------------------------

def add_one(x):
    return x + 1


def double(x):
    return x * 2


def to_text(x):
    return str(x)


def sum_values(a, b):
    return a + b


def split_pair(x):
    return x, x + 1


def return_mapping(x):
    return {"left": x, "right": x + 1}


# ---------------------------------------------------------------------------
# Helper datasets
# ---------------------------------------------------------------------------

class ConfirmableMemoryDataset(MemoryDataset):
    def __init__(self, data=None):
        super().__init__(data)
        self.confirmed = False

    def confirm(self):
        self.confirmed = True


class BrokenLoadDataset(AbstractDataset):
    def _load(self):
        raise RuntimeError("load failure")

    def _save(self, data):
        self.data = data

    def _describe(self):
        return {}


class BrokenSaveDataset(AbstractDataset):
    def _load(self):
        return None

    def _save(self, data):
        raise RuntimeError("save failure")

    def _describe(self):
        return {}


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def make_three_step_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(add_one, "raw", "clean", name="clean", tags="prep"),
            node(double, "clean", "model", name="model", tags="train"),
            node(to_text, "model", "report", name="report", tags={"report"}),
        ]
    )


# ---------------------------------------------------------------------------
# Kedro project scaffolding for session/CLI tests
# ---------------------------------------------------------------------------

def write_kedro_project(tmp_path: Path, *, base_value=2, env_value=None) -> Path:
    """Create a minimal Kedro project and return the marker file path."""
    package_name = "project_" + str(abs(hash(str(tmp_path))))
    source = tmp_path / "src" / package_name
    source.mkdir(parents=True)
    (tmp_path / "conf" / "base").mkdir(parents=True)
    (tmp_path / "conf" / "local").mkdir(parents=True)
    (source / "__init__.py").write_text('__version__ = "0.1"\n', encoding="utf-8")
    (source / "settings.py").write_text(
        'CONFIG_LOADER_ARGS = {"base_env": "base", "default_run_env": "local"}\n',
        encoding="utf-8",
    )
    (source / "pipeline_registry.py").write_text(
        textwrap.dedent("""
            from pathlib import Path
            from kedro.pipeline import Pipeline, node

            def add_one(value, marker):
                Path(marker).write_text(f"first:{value}", encoding="utf-8")
                return value + 1

            def double(value, marker):
                with Path(marker).open("a", encoding="utf-8") as stream:
                    stream.write(f"|second:{value}")
                return value * 2

            def register_pipelines():
                first = node(add_one, ["params:value", "params:marker"], "intermediate", name="add_one", tags="first")
                second = node(double, ["intermediate", "params:marker"], "result", name="double", tags="second")
                complete = Pipeline([first, second])
                return {"__default__": complete, "math": complete, "first_only": Pipeline([first])}
        """).lstrip(),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(f"""
            [tool.kedro]
            package_name = "{package_name}"
            project_name = "Oracle Project"
            kedro_init_version = "1.5.0"
            source_dir = "src"
        """).lstrip(),
        encoding="utf-8",
    )
    marker = tmp_path / "run.txt"
    (tmp_path / "conf" / "base" / "parameters.yml").write_text(
        f"value: {base_value}\nmarker: {marker.as_posix()}\n", encoding="utf-8"
    )
    (tmp_path / "conf" / "base" / "catalog.yml").write_text(
        "intermediate:\n  type: MemoryDataset\nresult:\n  type: MemoryDataset\n",
        encoding="utf-8",
    )
    if env_value is not None:
        env_dir = tmp_path / "conf" / "special"
        env_dir.mkdir(parents=True)
        (env_dir / "parameters.yml").write_text(f"value: {env_value}\n", encoding="utf-8")
    return marker
