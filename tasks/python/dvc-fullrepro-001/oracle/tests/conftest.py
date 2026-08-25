"""Portable helpers for the DVC v3 durable-workflow gate."""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

import pytest
import yaml

from scorer_support import ScorerInfrastructureError


def _apply_reference_patch() -> None:
    configured = os.environ.get("DVC_V3_REFERENCE_PATCH")
    if not configured or "dvc.durable" in sys.modules:
        return
    patch_path = Path(configured).resolve()
    if not patch_path.is_file():
        raise ScorerInfrastructureError(f"DVC_V3_REFERENCE_PATCH is not a file: {patch_path}")
    spec = importlib.util.spec_from_file_location("dvc_v3_reference_patch", patch_path)
    if spec is None or spec.loader is None:
        raise ScorerInfrastructureError(f"cannot load DVC v3 reference patch: {patch_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply()


_apply_reference_patch()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is None:
        report.dvc_v3_exception_type = None
    else:
        cls = call.excinfo.type
        report.dvc_v3_exception_type = f"{cls.__module__}.{cls.__qualname__}"


def pytest_runtest_logreport(report):
    report_path = os.environ.get("DVC_V3_ROOT_REPORT")
    if not report_path:
        return
    record = {
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": report.outcome,
        "exception_type": getattr(report, "dvc_v3_exception_type", None),
        "longrepr": str(report.longrepr) if report.failed else None,
    }
    with Path(report_path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def _make_writable(path) -> None:
    candidate = Path(path)
    try:
        candidate.chmod(candidate.stat().st_mode | stat.S_IWRITE | stat.S_IREAD)
    except FileNotFoundError:
        pass


def _rmtree_onerror(function, path, exc_info):  # noqa: ARG001
    _make_writable(path)
    function(path)


def remove_owned_tree(path: Path) -> None:
    path = path.resolve()
    if path.exists():
        shutil.rmtree(path, onerror=_rmtree_onerror)


@contextlib.contextmanager
def case_root(label: str):
    configured = os.environ.get("DVC_GATE_ASCII_TMP")
    base = Path(configured) if configured else Path(tempfile.gettempdir())
    base = base.resolve()
    base.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix=f"dvc_c_{label}_", dir=base)).resolve()
    if root.parent != base:
        remove_owned_tree(root)
        raise RuntimeError(f"unsafe DVC fixture root: {root}")
    previous = os.environ.get("DVC_SITE_CACHE_DIR")
    os.environ["DVC_SITE_CACHE_DIR"] = os.fspath(root / "site-cache")
    try:
        yield root
    finally:
        if previous is None:
            os.environ.pop("DVC_SITE_CACHE_DIR", None)
        else:
            os.environ["DVC_SITE_CACHE_DIR"] = previous
        remove_owned_tree(root)


@contextlib.contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def dvc_command() -> list[str]:
    configured = os.environ.get("DVC_EXPECTED_PYTHON")
    if not configured:
        raise ScorerInfrastructureError("scorer did not provide DVC_EXPECTED_PYTHON")
    expected = Path(configured).resolve()
    if not expected.is_file():
        raise ScorerInfrastructureError(f"attested DVC Python is missing: {expected}")
    return [os.fspath(expected), "-B", "-m", "dvc"]


def run_dvc(cwd: Path, *arguments, check: bool = True):
    env = os.environ.copy()
    env.update(
        {
            "DVC_TEST": "true",
            "DVC_NO_ANALYTICS": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    completed = subprocess.run(
        [*dvc_command(), *(os.fspath(arg) for arg in arguments)],
        cwd=os.fspath(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="strict",
        capture_output=True,
        timeout=120,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"DVC command returned {completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def init_project(path: Path):
    from dvc.repo import Repo

    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(root_dir=os.fspath(path), no_scm=True)
    repo.close()
    return path


def open_repo(path: Path, *, uninitialized: bool = False):
    from dvc.repo import Repo

    return Repo(os.fspath(path), uninitialized=uninitialized)


def python_command(script: Path) -> str:
    return subprocess.list2cmdline([sys.executable, os.fspath(script)])


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def declare(project: Path, name: str, script: Path, *, deps=(), outs=()):
    with working_directory(project):
        with open_repo(project) as repo:
            return repo.run(
                name=name,
                cmd=python_command(script),
                deps=list(deps),
                outs=list(outs),
                no_exec=True,
            )


def durable_graph(root: Path, name="build"):
    from dvc.durable import GraphDeclarations

    graph = GraphDeclarations(root)
    receipt = graph.declare(name, f"python {name}.py", deps=(f"{name}.in",), outs=(f"{name}.out",))
    return graph, receipt


def durable_execution(root: Path, graph_receipt: dict, transaction="tx-main"):
    from dvc.durable import ExecutionJournal

    execution = ExecutionJournal(root)
    execution.begin(transaction, graph_receipt)
    execution.record(transaction, "command", "completed")
    return execution, execution.commit(transaction)


def durable_content(root: Path, execution_receipt: dict, data=b"payload-v3"):
    from dvc.durable import ContentLineage

    content = ContentLineage(root)
    prepared = content.prepare(data, execution_receipt)
    published = content.publish(prepared)
    return content, content.acknowledge(published)


def durable_remote(root: Path, content_receipt: dict, remote_root: Path, data=b"payload-v3"):
    from dvc.durable import RemoteOutbox

    outbox = RemoteOutbox(root)
    enqueued = outbox.enqueue(content_receipt, data)
    delivered = outbox.deliver(enqueued, remote_root)
    return outbox, outbox.acknowledge(delivered)

