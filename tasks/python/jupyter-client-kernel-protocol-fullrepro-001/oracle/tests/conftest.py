import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


GATE_ROOT = Path(__file__).resolve().parent.parent
if str(GATE_ROOT) not in sys.path:
    sys.path.insert(0, str(GATE_ROOT))


def pytest_configure(config):
    patch_path = os.environ.get("JUPYTER_CLIENT_V4_REFERENCE_PATCH")
    if patch_path:
        path = Path(patch_path).resolve()
        spec = importlib.util.spec_from_file_location("jupyter_client_v4_reference_patch", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.install(os.environ.get("JUPYTER_CLIENT_V4_CONTROL"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is None:
        report.jupyter_client_v4_exception_type = None
    else:
        cls = call.excinfo.type
        report.jupyter_client_v4_exception_type = f"{cls.__module__}.{cls.__qualname__}"


def pytest_runtest_logreport(report):
    report_path = os.environ.get("JUPYTER_CLIENT_V4_ROOT_REPORT")
    if not report_path:
        return
    record = {
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": report.outcome,
        "exception_type": getattr(report, "jupyter_client_v4_exception_type", None),
        "longrepr": str(report.longrepr) if report.failed else None,
    }
    path = Path(report_path)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
