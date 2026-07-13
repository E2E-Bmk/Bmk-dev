from __future__ import annotations

from dataclasses import dataclass
import re

from .clock import FakeClock
from .models import TaskRecord


@dataclass
class RuntimeResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    progress: int | None = None
    duration_seconds: int = 0


class LocalRuntime:
    """Deterministic local runtime. It may be fake-command based or bounded shell."""

    def __init__(self, clock: FakeClock | None = None) -> None:
        self.clock = clock

    def run(self, task: TaskRecord, context: dict) -> RuntimeResult:
        command = _render(task.run or "", context).strip()
        if not command:
            return RuntimeResult(exit_code=0)

        verb, _, rest = command.partition(" ")
        verb = verb.strip()
        rest = rest.strip()

        if verb == "echo":
            return RuntimeResult(exit_code=0, stdout=rest)
        if verb == "fail":
            return RuntimeResult(exit_code=1, stderr=rest or "failed")
        if verb == "set-progress":
            try:
                progress = int(rest)
            except ValueError:
                return RuntimeResult(exit_code=1, stderr=f"invalid progress: {rest}")
            progress = max(0, min(100, progress))
            return RuntimeResult(exit_code=0, progress=progress)
        if verb == "sleep":
            try:
                seconds = int(rest)
            except ValueError:
                return RuntimeResult(exit_code=1, stderr=f"invalid sleep duration: {rest}")
            if seconds < 0:
                return RuntimeResult(exit_code=1, stderr="sleep duration must be non-negative")
            if self.clock is not None:
                self.clock.advance(seconds)
            return RuntimeResult(exit_code=0, duration_seconds=seconds)

        return RuntimeResult(exit_code=127, stderr=f"unsupported command: {verb}")


def _render(command: str, context: dict) -> str:
    values = dict(context.get("inputs", {}))
    values.update(context.get("outputs", {}))
    values.update(context.get("vars", {}))
    values.update(context.get("item", {}))

    def repl(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2)
        if key.startswith("outputs."):
            key = key.split(".", 1)[1]
        if key.startswith("inputs."):
            key = key.split(".", 1)[1]
        if key.startswith("tasks."):
            key = key.split(".", 1)[1]
        value = values.get(key, "")
        return str(value)

    return re.sub(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}|\$\{([A-Za-z0-9_.-]+)\}", repl, command)
