"""Python: pytest with a per-batch JSON report.

Behaviour is the interim release's scoring behaviour, moved out of the sandbox
unchanged. Any divergence from the released harness is a bug in this file.
"""

from __future__ import annotations

import ast
import json
import shlex
from pathlib import Path
from typing import Iterator, Optional

try:
    from harness.runners.base import Batch, Env, Runner, Step, TestId
except ImportError:  # direct execution of a harness script
    from runners.base import Batch, Env, Runner, Step, TestId

PIP = "pip install --no-cache-dir"


class PythonRunner(Runner):
    language = "python"

    # ── discovery ─────────────────────────────────────────────────────────

    def discover(self, oracle_host: Path, suite: str) -> list[TestId]:
        source = oracle_host / f"test_{suite}.py"
        if not source.exists():
            return []
        try:
            # utf-8-sig, not utf-8: several oracle files carry a BOM, and a plain
            # utf-8 read turns the first byte into a syntax error, silently
            # enumerating zero tests and zeroing the denominator.
            tree = ast.parse(
                source.read_text(encoding="utf-8-sig", errors="replace"),
                filename=str(source),
            )
        except SyntaxError:
            return []

        def is_test(node) -> bool:
            return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test")

        ids: list[TestId] = []
        for node in tree.body:
            if is_test(node):
                ids.append(f"{source.name}::{node.name}")
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                ids += [f"{source.name}::{node.name}::{m.name}" for m in node.body if is_test(m)]
        return ids

    # ── container preparation ─────────────────────────────────────────────

    def setup(self, env: Env) -> Iterator[Step]:
        yield Step(
            f"{PIP} pytest pytest-timeout pytest-json-report pytest-asyncio -q",
            timeout=180,
            required=True,
        )

        if env.oracle_host is not None and (env.oracle_host / "requirements.txt").exists():
            yield Step(f"{PIP} -r {env.oracle}/requirements.txt -q", required=True)

        if env.extra_requirements:
            yield Step(f"{PIP} -r {shlex.quote(env.extra_requirements)} -q", required=True)

        if env.shadowing:
            # A genuine upstream distribution arrived as a transitive dependency
            # of the oracle's requirements; left in place the oracle would import
            # the real library instead of the candidate.
            yield Step(f"pip uninstall -y {' '.join(env.shadowing)}", timeout=60)

        yield from self._install_candidate(env)

    def _install_candidate(self, env: Env) -> Iterator[Step]:
        """Declared dependencies first, then the candidate itself.

        Both halves of the spec's promise are honoured. A candidate that declares
        dependencies only in ``requirements.txt`` must not lose them for shipping
        no packaging metadata, and a candidate with no metadata at all still
        becomes importable through a ``.pth`` entry - a missing manifest is a
        packaging omission, not grounds for scoring every test as failed.
        """
        if env.workspace_host is not None and (env.workspace_host / "requirements.txt").exists():
            yield Step(f"{PIP} -r {env.workspace}/requirements.txt -q 2>&1", capture=True)

        site = "$(python3 -c 'import site; print(site.getsitepackages()[0])')"
        pth = f"echo {env.workspace} > {site}/ws.pth"
        yield Step(
            f"cd {env.workspace} && "
            "if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f setup.cfg ]; then "
            f"{PIP} -e . -q 2>&1 || {PIP} . -q 2>&1 || "
            f"({pth} && echo 'fallback: sys.path pth'); "
            f"else {pth} && echo 'no packaging metadata: sys.path pth'; fi",
            capture=True,
        )

    # ── execution ─────────────────────────────────────────────────────────

    def batch(self, suite: str, tests: list[TestId], offset: int, timeout: int) -> Batch:
        report = f"/eval/rb_{suite}_{offset}.json"
        args = " ".join(shlex.quote(f"/eval/oracle/{t}") for t in tests)
        return Batch(
            command=(
                f"cd /eval && timeout {timeout} python3 -m pytest {args} "
                f"-q --no-header --timeout=30 -p no:cacheprovider "
                f"-o asyncio_mode=auto "
                f"-o 'markers=depends_on(*names): atomic test prerequisites' "
                f"--json-report --json-report-file={report} "
                f"--json-report-omit collectors log traceback streams warnings 2>&1"
            ),
            report=report,
        )

    def outcomes(self, report: str, stdout: str) -> Optional[dict[TestId, str]]:
        text = (report or "").strip()
        if not text:
            return None
        try:
            data = json.loads(text)
        except ValueError:
            return None
        # Setup and teardown failures arrive as outcome "error"; the xfail family
        # is kept verbatim so the sandbox sees what pytest actually decided.
        return {
            entry.get("nodeid", ""): entry.get("outcome", "error")
            for entry in data.get("tests", [])
        }

    def function_of(self, test: TestId) -> str:
        """``file_stem::[Class.]name``.

        A class method joins with a dot rather than ``::`` - this is the form
        already used as the key of ``score.tests`` in every published
        ``result.json``, and the two must not diverge.
        """
        parts = test.split("[", 1)[0].replace("\\", "/").split("::")
        stem = parts[0].rsplit("/", 1)[-1]
        stem = stem[:-3] if stem.endswith(".py") else stem
        return f"{stem}::{'.'.join(parts[1:])}"

    def synthetic_id(self, suite: str) -> TestId:
        return f"test_{suite}.py::test_placeholder"

    # ── dependencies ──────────────────────────────────────────────────────

    def dependencies(self, oracle_host: Path) -> dict[str, list[str]]:
        """`@pytest.mark.depends_on(...)` markers on the integration suite.

        Both the qualified form and a module-level alias
        (``depends_on = pytest.mark.depends_on``) are recognised. Dependencies
        are bare atomic function names; the legacy ``test_atomic::`` prefix is
        accepted and normalised away.
        """
        source = oracle_host / "test_integration.py"
        if not source.exists():
            return {}
        try:
            tree = ast.parse(
                source.read_text(encoding="utf-8-sig", errors="replace"),
                filename=str(source),
            )
        except SyntaxError:
            return {}

        aliases = {"pytest.mark.depends_on"}
        for statement in tree.body:
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                continue
            if _dotted_name(statement.value) != "pytest.mark.depends_on":
                continue
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            aliases.update(t.id for t in targets if isinstance(t, ast.Name))

        result: dict[str, list[str]] = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            dependencies: list[str] = []
            for decorator in node.decorator_list:
                for dependency in _depends_on_args(decorator, aliases):
                    if dependency not in dependencies:
                        dependencies.append(dependency)
            if dependencies:
                result[node.name] = dependencies
        return result

    # ── provenance ────────────────────────────────────────────────────────

    def provenance(self, env: Env) -> Optional[str]:
        """Report every resolved path for each target module, JSON on one line.

        Primary evidence is the module's own ``__file__``/``__path__``, because
        that is what the test run will execute. It survives editable installs,
        whose importlib metadata reports finder-hook strings rather than paths.
        The ``__PROVENANCE__`` marker lets the sandbox tell a completed probe
        from a probe that died before printing.
        """
        if not env.target_modules:
            return None
        names = list(env.target_modules)
        probe = (
            "import json, os\n"
            "import importlib.metadata as md\n"
        f"names = {names!r}\n"
            "rows = []\n"
            "provider_map = md.packages_distributions()\n"
            "for n in names:\n"
            "    row = {'name': n, 'paths': [], 'error': None, 'direct_urls': []}\n"
            "    try:\n"
            "        m = __import__(n)\n"
            "        f = getattr(m, '__file__', None)\n"
            "        if f:\n"
            "            row['paths'].append(os.path.realpath(f))\n"
            "        for p in list(getattr(m, '__path__', []) or []):\n"
            "            row['paths'].append(os.path.realpath(str(p)))\n"
            "        # PEP 610: a non-editable `pip install /eval/workspace` copies\n"
            "        # code into site-packages but records its source in\n"
            "        # direct_url.json - that is still candidate code.\n"
            "        for dist_name in provider_map.get(n, []):\n"
            "            try:\n"
            "                dist = md.distribution(dist_name)\n"
            "                raw = dist.read_text('direct_url.json')\n"
            "                if raw:\n"
            "                    row['direct_urls'].append(json.loads(raw).get('url', ''))\n"
            "            except Exception:\n"
            "                pass\n"
            "    except BaseException as e:\n"
            "        row['error'] = f'{type(e).__name__}: {e}'\n"
            "    rows.append(row)\n"
            "print('__PROVENANCE__' + json.dumps(rows, sort_keys=True))\n"
        )
        return f"python3 -c {shlex.quote(probe)}"


# ── AST helpers for dependency markers ───────────────────────────────────────


def _dotted_name(node) -> str:
    """The dotted name a Name/Attribute node spells, or ``""``."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return ""
    parts.append(node.id)
    return ".".join(reversed(parts))


def _depends_on_args(decorator, aliases: set[str]) -> list[str]:
    """String arguments of a recognised dependency marker, prefix stripped."""
    if not isinstance(decorator, ast.Call):
        return []
    if _dotted_name(decorator.func) not in aliases:
        return []
    names = []
    for arg in decorator.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            names.append(arg.value.removeprefix("test_atomic::"))
    return names
