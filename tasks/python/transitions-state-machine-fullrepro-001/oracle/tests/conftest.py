from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def pytest_configure(config: pytest.Config) -> None:
    patch_path = os.environ.get("TRANSITIONS_V4_REFERENCE_PATCH")
    if patch_path:
        import importlib.util

        spec = importlib.util.spec_from_file_location("transitions_v4_reference_patch", patch_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load reference patch: {patch_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.install(os.environ.get("TRANSITIONS_V4_CONTROL", "complete"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    phase_path = os.environ.get("TRANSITIONS_V4_PHASE_FILE")
    if not phase_path:
        return
    path = Path(phase_path)
    payload = {"nodeid": item.nodeid, "phases": {}}
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    payload["phases"][report.when] = {"outcome": report.outcome, "duration_s": report.duration}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


@pytest.fixture
def api():
    import transitions

    def resolve(name: str):
        value = getattr(transitions, name, None)
        assert value is not None, f"public API {name!r} is unavailable"
        return value

    return resolve


@pytest.fixture
def fresh_process():
    def run(code: str) -> dict:
        env = os.environ.copy()
        patch_path = env.get("TRANSITIONS_V4_REFERENCE_PATCH")
        prefix = ""
        if patch_path:
            prefix = (
                "import importlib.util, os;"
                "s=importlib.util.spec_from_file_location('transitions_v4_reference_patch',"
                + repr(patch_path)
                + ");m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                "m.install(os.environ.get('TRANSITIONS_V4_CONTROL','complete'));"
            )
        result = subprocess.run(
            [sys.executable, "-c", prefix + code],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
        assert result.returncode == 0, result.stdout
        return json.loads(result.stdout.strip().splitlines()[-1])
    return run
