"""Go: `go test -json`, one package per suite.

Go's tooling reports per-test results natively as a JSON event stream, so no
plugin is needed. Two properties of `go test` shape this runner:

* it is package-oriented, not file-oriented - a suite is a package directory and
  a batch selects tests within it by regexp, not by file path;
* it compiles before running, so a candidate that does not build produces no test
  events at all. That is reported as an unusable batch rather than as failures,
  the same treatment a Python collection error receives.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Iterator, Optional

from harness.runners.base import Batch, Env, Runner, Step, TestId

#: `func TestXxx(t *testing.T)` at the top level of a file.
_TEST_FUNC = re.compile(r"^func\s+(Test\w*)\s*\(\s*\w+\s+\*testing\.[TB]\s*\)", re.M)


class GoRunner(Runner):
    language = "go"

    # ── discovery ─────────────────────────────────────────────────────────

    def discover(self, oracle_host: Path, suite: str) -> list[TestId]:
        """`Test*` functions in the suite's package, as ``pkg::TestName``.

        Read from source with a regexp rather than asked of `go test -list`,
        because `-list` needs a successful compile and the denominator must not
        depend on whether the candidate builds.
        """
        package = oracle_host / suite
        if not package.is_dir():
            return []
        ids: list[TestId] = []
        for source in sorted(package.glob("*_test.go")):
            text = source.read_text(encoding="utf-8", errors="replace")
            ids += [f"{suite}::{name}" for name in _TEST_FUNC.findall(text)]
        return ids

    # ── container preparation ─────────────────────────────────────────────

    def setup(self, env: Env) -> Iterator[Step]:
        """Wire the oracle module to the candidate, then vendor dependencies.

        The oracle is a separate module that imports the candidate by its module
        path. A `replace` directive pointed at the workspace is what makes the
        candidate - rather than a published version of the same path - the thing
        under test; it is the Go equivalent of the Python provenance concern.
        """
        yield Step("go version", timeout=60, required=True)

        module = env.target_modules[0] if env.target_modules else ""
        if module:
            yield Step(
                f"cd {env.oracle} && go mod edit "
                f"-replace={shlex.quote(module)}={env.workspace}",
                timeout=60,
                required=True,
            )

        # `go mod tidy` needs the network and must run before it is cut. Its
        # output is the evidence for a later build failure, so it is captured.
        yield Step(f"cd {env.workspace} && go mod tidy 2>&1", capture=True)
        yield Step(f"cd {env.oracle} && go mod tidy 2>&1", capture=True)

        # Build once, with network, so a compile failure is attributable here
        # instead of surfacing as every batch producing no events.
        yield Step(f"cd {env.workspace} && go build ./... 2>&1", capture=True)

    # ── execution ─────────────────────────────────────────────────────────

    def batch(self, suite: str, tests: list[TestId], offset: int, timeout: int) -> Batch:
        """Run the named tests via an anchored `-run` alternation.

        Anchors matter: without them `-run TestGet` would also select
        `TestGetMissing`, so a batch would run tests belonging to another batch
        and their outcomes would be recorded twice.
        """
        names = "|".join(f"^{re.escape(t.split('::', 1)[-1])}$" for t in tests)
        report = f"/eval/rb_{suite}_{offset}.json"
        return Batch(
            command=(
                f"cd {shlex.quote(f'/eval/oracle/{suite}')} && "
                f"timeout {timeout} go test -json -count=1 "
                f"-timeout {timeout}s -run {shlex.quote(names)} ./... "
                f"> {report} 2>&1"
            ),
            report=report,
        )

    def outcomes(self, report: str, stdout: str) -> Optional[dict[TestId, str]]:
        """Fold the `go test -json` event stream into one outcome per test.

        The stream carries an event per test per action; the last terminal action
        wins. Subtests (``TestX/case``) are separate events and are kept as
        separate ids - ``function_of`` collapses them onto the parent, matching
        how a parameterised Python function is counted once.

        Returns ``None`` when no event names a test: a compile error, a vet
        failure or a timeout kill all produce output with no test events, and
        that is an unusable batch rather than a set of failures.
        """
        translate = {"pass": "passed", "fail": "failed", "skip": "skipped"}
        results: dict[TestId, str] = {}
        for line in (report or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            name, action = event.get("Test"), event.get("Action")
            if not name or action not in translate:
                continue
            package = (event.get("Package") or "").rsplit("/", 1)[-1]
            results[f"{package}::{name}" if package else name] = translate[action]
        return results or None

    def function_of(self, test: TestId) -> str:
        """``pkg::TestName``, with subtest paths folded onto the parent."""
        package, _, name = test.rpartition("::")
        return f"{package}::{name.split('/', 1)[0]}" if package else name.split("/", 1)[0]

    def synthetic_id(self, suite: str) -> TestId:
        return f"{suite}::TestPlaceholder"

    # ── provenance ────────────────────────────────────────────────────────

    def provenance(self, env: Env) -> Optional[str]:
        """Show where the oracle's build resolved the candidate module to.

        `go list -m` prints the module's resolved directory. The sandbox then
        checks that the path is inside the workspace, so a `replace` directive
        that silently failed to apply - leaving a published version in play -
        is caught before the scores are believed.
        """
        if not env.target_modules:
            return None
        module = env.target_modules[0]
        script = (
            "import json, subprocess, sys\n"
            f"module = {module!r}\n"
            f"oracle = {env.oracle!r}\n"
            "rows = []\n"
            "try:\n"
            "    out = subprocess.run(['go', 'list', '-m', '-f', '{{.Dir}}', module],\n"
            "                         cwd=oracle, capture_output=True, text=True, timeout=60)\n"
            "    path = out.stdout.strip()\n"
            "    rows.append({'name': module, 'paths': [path] if path else [],\n"
            "                 'error': out.stderr.strip() or None, 'direct_urls': []})\n"
            "except Exception as exc:\n"
            "    rows.append({'name': module, 'paths': [], 'direct_urls': [],\n"
            "                 'error': f'{type(exc).__name__}: {exc}'})\n"
            "print('__PROVENANCE__' + json.dumps(rows, sort_keys=True))\n"
        )
        return f"python3 -c {shlex.quote(script)}"
