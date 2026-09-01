import importlib.util
import json
import multiprocessing.connection as mpc
import os
from pathlib import Path
import ssl
import subprocess
import sys

import pytest


def _python312_compatibility():
    for public, private in (
        ("CHALLENGE", "_CHALLENGE"),
        ("WELCOME", "_WELCOME"),
        ("FAILURE", "_FAILURE"),
    ):
        if not hasattr(mpc, public) and hasattr(mpc, private):
            setattr(mpc, public, getattr(mpc, private))
    if not hasattr(ssl, "wrap_socket"):
        ssl.wrap_socket = lambda *args, **kwargs: None


def pytest_configure(config):
    _python312_compatibility()
    for variable, module_name in (
        ("CURIO_V7_REFERENCE_PATCH", "curio_v7_reference_patch"),
        ("CURIO_V7_INCOMPLETE_PATCH", "curio_v7_incomplete_patch"),
    ):
        patch_path = os.environ.get(variable)
        if not patch_path:
            continue
        path = Path(patch_path).resolve()
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.install()


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    """Run each behavioral root in a killable evaluator-owned child process.

    A candidate deadlock is a semantic miss, not an outer scorer timeout.  The
    outer pytest call waits only for this fixed deadline and converts expiry to
    an ordinary call-phase failure.  The inner run bypasses this hook so there
    is exactly one bounded child per scored root.
    """
    if os.environ.get("CURIO_V7_INNER_ROOT") == "1":
        return None
    deadline = float(os.environ.get("CURIO_V7_SEMANTIC_DEADLINE", "4.0"))
    env = os.environ.copy()
    env["CURIO_V7_INNER_ROOT"] = "1"
    env.pop("CURIO_V7_ROOT_REPORT", None)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        pyfuncitem.nodeid,
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            capture_output=True,
            text=True,
            timeout=deadline,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"candidate behavior exceeded evaluator semantic deadline ({deadline:.1f}s)",
            pytrace=False,
        )
    if completed.returncode != 0:
        diagnostic = (completed.stdout + "\n" + completed.stderr)[-6000:]
        pytest.fail("bounded behavioral root failed:\n" + diagnostic, pytrace=False)
    return True


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is None:
        report.curio_v7_exception_type = None
    else:
        cls = call.excinfo.type
        report.curio_v7_exception_type = f"{cls.__module__}.{cls.__qualname__}"


def pytest_runtest_logreport(report):
    report_path = os.environ.get("CURIO_V7_ROOT_REPORT")
    if not report_path:
        return
    record = {
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": report.outcome,
        "exception_type": getattr(report, "curio_v7_exception_type", None),
        "longrepr": str(report.longrepr) if report.failed else None,
    }
    with Path(report_path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
