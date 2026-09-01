"""Per-language test runners for the scoring sandbox.

One module per language under `harness/lang/<language>/runner.py`, each
implementing `Runner` (see `base`). Add a language by writing that module and
listing it in `_RUNNERS`.

Dispatch is on the `language` field of `task.json`. A task without the field is
scored as Python, which is how every task in the interim release predates it.
"""

from __future__ import annotations

from harness.lang.go.runner import GoRunner
from harness.lang.java.runner import JavaRunner
from harness.lang.python.runner import PythonRunner
from harness.lang.rust.runner import RustRunner
from harness.lang.typescript.runner import TypeScriptRunner
from harness.runners.base import Batch, Env, Runner, Step, TestId

DEFAULT_LANGUAGE = "python"

_RUNNERS: tuple[type[Runner], ...] = (
    PythonRunner,
    GoRunner,
    TypeScriptRunner,
    RustRunner,
    JavaRunner,
)

REGISTRY: dict[str, Runner] = {cls.language: cls() for cls in _RUNNERS}


def get_runner(language: str | None) -> Runner:
    """The runner for a language, defaulting to Python.

    A named-but-unimplemented language raises, listing what is supported: a task
    built for a runner that does not exist yet must fail loudly at scoring time
    rather than be scored under the wrong toolchain.
    """
    name = (language or DEFAULT_LANGUAGE).lower()
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"no runner for language {name!r}; supported: {', '.join(sorted(REGISTRY))}"
        ) from None


__all__ = ["Batch", "Env", "Runner", "Step", "TestId",
           "PythonRunner", "GoRunner", "TypeScriptRunner", "RustRunner", "JavaRunner",
           "REGISTRY", "DEFAULT_LANGUAGE", "get_runner"]
