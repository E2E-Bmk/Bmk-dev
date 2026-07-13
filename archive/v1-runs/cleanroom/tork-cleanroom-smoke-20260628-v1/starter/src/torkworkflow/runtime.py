from __future__ import annotations

from dataclasses import dataclass

from .models import TaskRecord


@dataclass
class RuntimeResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class LocalRuntime:
    """Deterministic local runtime. It may be fake-command based or bounded shell."""

    def run(self, task: TaskRecord, context: dict) -> RuntimeResult:
        raise NotImplementedError
