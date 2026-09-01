"""Private phase reporter for one manifest-bound root process."""

from __future__ import annotations

import json
import os
from pathlib import Path


_REPORTS = {}


def pytest_runtest_logreport(report):
    if report.when in {"setup", "call", "teardown"}:
        _REPORTS.setdefault(report.nodeid, {})[report.when] = {
            "outcome": report.outcome,
            "longrepr": str(report.longrepr) if report.failed else "",
            "wasxfail": str(getattr(report, "wasxfail", "")),
        }


def pytest_sessionfinish(session, exitstatus):
    target = os.environ.get("S2R_PHASE_REPORT")
    if target:
        Path(target).write_text(
            json.dumps(_REPORTS, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
