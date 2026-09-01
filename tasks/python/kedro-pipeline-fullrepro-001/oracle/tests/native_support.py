from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable


def add_one(value: int) -> int:
    return value + 1


def double(value: int) -> int:
    return value * 2


def combine(left: int, right: int) -> int:
    return left + right


def expect(error: type[BaseException], call: Callable[[], Any]) -> BaseException:
    try:
        call()
    except error as exc:
        return exc
    raise AssertionError(f"expected {error.__name__}")


def api() -> SimpleNamespace:
    pipeline = importlib.import_module("kedro.pipeline")
    errors = importlib.import_module("kedro.pipeline.pipeline")
    io = importlib.import_module("kedro.io")
    config = importlib.import_module("kedro.config")
    runner = importlib.import_module("kedro.runner")
    return SimpleNamespace(
        pipeline_module=pipeline,
        io_module=io,
        config_module=config,
        runner_module=runner,
        Node=pipeline.Node,
        Pipeline=pipeline.Pipeline,
        node=pipeline.node,
        pipeline=pipeline.pipeline,
        DataCatalog=io.DataCatalog,
        MemoryDataset=io.MemoryDataset,
        DatasetError=io.DatasetError,
        DatasetNotFoundError=io.DatasetNotFoundError,
        OmegaConfigLoader=config.OmegaConfigLoader,
        SequentialRunner=runner.SequentialRunner,
        OutputNotUniqueError=errors.OutputNotUniqueError,
        CircularDependencyError=errors.CircularDependencyError,
    )


def write_config(root: Path, *, value: int, increment: int = 1) -> Path:
    base = root / "base"
    base.mkdir(parents=True)
    (base / "parameters.yml").write_text(
        f"value: {value}\nincrement: {increment}\n", encoding="utf-8"
    )
    (base / "catalog.yml").write_text(
        "seed:\n  type: MemoryDataset\n  data: 4\n", encoding="utf-8"
    )
    return root
