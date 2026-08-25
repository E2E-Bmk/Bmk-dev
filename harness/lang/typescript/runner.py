"""TypeScript: vitest with a per-batch JSON report.

Two properties of vitest shape this runner:

* `--reporter=json` writes one object per run, with a `testResults` entry per
  file and an `assertionResults` entry per test. `fullName` joins the describe
  chain and the title with spaces, so it is not a parseable path -- the id is
  built from `ancestorTitles` and `title` instead.
* `-t` selects by substring and reports everything it did not select as
  `skipped` rather than omitting it. Folding the report wholesale would record
  the rest of the suite as skipped on every batch, so `outcomes` returns only
  the tests the batch asked for.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Iterator, Optional

from harness.runners.base import (
    Batch,
    Env,
    Runner,
    Step,
    TestId,
    depends_on_above,
    nested_names,
)

# `it("name")`, `test("name")`, and the `.each` / `.only` / `.skip` variants.
_TEST_CALL = re.compile(
    r"""\b(?:it|test)\s*(?:\.\s*\w+\s*(?:\([^)]*\)\s*)?)*\(\s*(['"`])(.+?)\1""",
    re.DOTALL,
)
_DESCRIBE_CALL = re.compile(
    r"""\bdescribe\s*(?:\.\s*\w+\s*)?\(\s*(['"`])(.+?)\1""", re.DOTALL
)


class TypeScriptRunner(Runner):
    language = "typescript"

    # ── discovery ─────────────────────────────────────────────────────────

    def discover(self, oracle_host: Path, suite: str) -> list[TestId]:
        """`{suite}::{describe chain}::{title}` for every test in the suite.

        Read from source with a regexp rather than from `vitest list`, because
        listing needs the project's dependencies installed and a working
        transform: the denominator must not depend on whether the candidate
        builds.

        The describe chain is tracked by brace depth. A title built by template
        interpolation cannot be recovered statically and is skipped here; the
        oracle is authored with literal titles for that reason.
        """
        directory = oracle_host / suite
        if not directory.is_dir():
            return []
        ids: list[TestId] = []
        for source in sorted(directory.rglob("*.test.ts")):
            ids += self._ids_in_file(source, suite)
        return ids

    def _ids_in_file(self, source: Path, suite: str) -> list[TestId]:
        text = source.read_text(encoding="utf-8-sig", errors="replace")
        chains = nested_names(
            text,
            [(m.start(), m.group(2)) for m in _DESCRIBE_CALL.finditer(text)],
            [(m.start(), m.group(2)) for m in _TEST_CALL.finditer(text)],
        )
        return ["::".join([suite, *chain]) for chain in chains]

    def dependencies(self, oracle_host: Path) -> dict[str, list[str]]:
        """`// DependsOn:` comments above each integration test's call.

        A key is the test's own title, not its describe chain: that is the leaf
        of the `{suite}::{chain}::{title}` id `discover` builds, and the leaf is
        what both the sandbox and `verify_task` index the relation by. Values
        are atomic titles read the same way.

        The title is passed through `function_of` first. A `.each` test's source
        title is `handles factor %i` while the run reports `handles factor 0`,
        and the folded form is the one the outcome map is keyed by -- an
        unfolded key would name a function that never appears in the results.

        Read from source on the host, like `discover`, so the candidate cannot
        influence the eligible set.
        """
        directory = oracle_host / "integration"
        if not directory.is_dir():
            return {}
        result: dict[str, list[str]] = {}
        for source in sorted(directory.rglob("*.test.ts")):
            text = source.read_text(encoding="utf-8-sig", errors="replace")
            for match in _TEST_CALL.finditer(text):
                names = depends_on_above(text, match.start())
                if names:
                    result[self.function_of(match.group(2))] = names
        return result

    # ── container preparation ─────────────────────────────────────────────

    def setup(self, env: Env) -> Iterator[Step]:
        """Install the candidate, then the oracle's own dev dependencies.

        The oracle is a separate package that imports the candidate by name. A
        `file:` dependency resolved through `npm install` is what makes the
        candidate -- rather than a published package of the same name -- the
        thing under test, and it is what `provenance` later verifies.
        """
        yield Step("node --version && npm --version", timeout=60, required=True)

        # The candidate's own dependencies first: a delivery may declare them in
        # package.json without having been installed.
        yield Step(
            f"cd {env.workspace} && "
            "if [ -f package.json ]; then npm install --no-audit --no-fund 2>&1; fi",
            timeout=600,
            capture=True,
        )

        # The oracle's own dependencies must be installed BEFORE the candidate
        # is linked in. `npm install --no-save` deliberately leaves the
        # candidate out of package.json, so a bare `npm install` afterwards
        # sees it as extraneous and prunes it -- the oracle then fails to
        # resolve the package under test at all. Order is load-bearing here.
        yield Step(
            f"cd {env.oracle} && npm install --no-audit --no-fund 2>&1",
            timeout=900,
            capture=True,
        )

        for module in env.target_modules:
            yield Step(
                f"cd {env.oracle} && npm install --no-save "
                f"{shlex.quote(f'{module}@file:{env.workspace}')} 2>&1",
                timeout=600,
                capture=True,
            )

    # ── execution ─────────────────────────────────────────────────────────

    def batch(self, suite: str, tests: list[TestId], offset: int, timeout: int) -> Batch:
        """Select the batch's tests by an alternation of their full names.

        `-t` takes one regexp and matches it against the full name as a
        substring. The pattern is anchored at the start but deliberately not at
        the end: a `.each` test's source title is `param %i` while its cases run
        as `param 1` and `param 2`, so an end-anchored pattern selects neither
        and the cases arrive as pending. Leaving the tail open selects the whole
        family, which is what counting a parameterised test once requires.

        The start anchor still does the work anchoring is for -- `^Grouped a`
        does not select a test named `Grouped ab` from another batch -- and the
        one case it cannot separate, a title that is a strict prefix of a
        sibling, is resolved by `outcomes` returning only the ids asked for.
        """
        # The folded form is what the pattern is built from: it drops the
        # `%i` a source title carries, leaving the stem both the template and
        # every expanded case share.
        names = "|".join(
            sorted({f"^{re.escape(self._full_name(self.function_of(t)))}" for t in tests})
        )
        report = f"/eval/rb_{suite}_{offset}.json"
        return Batch(
            command=(
                # Run from the oracle root with the suite as a path filter, so a
                # relative import inside a test resolves the same way it does
                # when the whole oracle runs. `batch` has no Env, so the path is
                # the sandbox's fixed mount point, as in the Go runner.
                f"cd /eval/oracle && "
                f"timeout {timeout} npx vitest run --reporter=json "
                f"--outputFile={report} -t {shlex.quote(names)} "
                f"{shlex.quote(suite)} > /dev/null 2>&1"
            ),
            report=report,
        )

    def outcomes(self, report: str, stdout: str) -> Optional[dict[TestId, str]]:
        """Per-test outcomes, keyed as `{suite}::{chain}::{title}`.

        A `.each` case arrives with its value already interpolated into the
        title, so the id here is the expanded one (`param 1`) while `discover`
        produced the template (`param %i`). `function_of` folds both onto the
        same key, which is where the two are reconciled -- the same arrangement
        as a parameterised pytest function.

        Only tests whose status vitest actually decided are returned. Everything
        `-t` filtered out arrives as `skipped`, and returning those would let one
        batch overwrite another batch's results with a skip.
        """
        text = (report or "").strip()
        if not text:
            return None
        try:
            data = json.loads(text)
        except ValueError:
            return None

        results: dict[TestId, str] = {}
        for file_result in data.get("testResults", []):
            suite = _suite_of(file_result.get("name") or "", data)
            for assertion in file_result.get("assertionResults", []):
                status = assertion.get("status")
                if status == "skipped":
                    continue
                chain = assertion.get("ancestorTitles") or []
                title = assertion.get("title") or ""
                key = "::".join([suite, *chain, title]) if suite else title
                results[key] = "passed" if status == "passed" else (status or "failed")
        return results or None

    def function_of(self, test: TestId) -> str:
        """Collapse a `.each` case onto the test that generated it.

        This is the one place the two sides meet. `discover` reads the source
        and sees the template title (`param %i`); the report carries the title
        with the case interpolated (`param 1`). Stripping a trailing printf
        placeholder, a trailing `$name` token, a bracketed index or a trailing
        integer maps both onto `param`, so a parameterised test is counted once
        and its cases all have to pass for it to count as passing.
        """
        head, _, leaf = test.rpartition("::")
        leaf = re.sub(r"\s*\[\d+\]\s*$", "", leaf)
        leaf = re.sub(r"\s*(?:%[#a-zA-Z]|\$\w+|-?\d+(?:\.\d+)?)\s*$", "", leaf)
        return f"{head}::{leaf.rstrip()}" if head else leaf.rstrip()

    def synthetic_id(self, suite: str) -> TestId:
        return f"{suite}::placeholder"

    # ── provenance ────────────────────────────────────────────────────────

    def provenance(self, env: Env) -> Optional[str]:
        """Report where the oracle resolves each target module from.

        `require.resolve` answers with the file Node would load, which is what
        the test run will execute. The sandbox then checks the path is inside the
        workspace, catching a `file:` dependency that silently resolved to a
        registry copy instead.
        """
        if not env.target_modules:
            return None
        names = list(env.target_modules)
        probe = (
            "const rows = [];\n"
            f"for (const name of {json.dumps(names)}) {{\n"
            "  const row = {name, paths: [], direct_urls: [], error: null};\n"
            "  try { row.paths.push(require.resolve(name, {paths: [process.cwd()]})); }\n"
            "  catch (e) { row.error = `${e.code || e.name}: ${e.message}`; }\n"
            "  rows.push(row);\n"
            "}\n"
            "console.log('__PROVENANCE__' + JSON.stringify(rows));\n"
        )
        return f"cd {env.oracle} && node -e {shlex.quote(probe)}"

    # ── helpers ───────────────────────────────────────────────────────────

    def _full_name(self, test: TestId) -> str:
        """vitest's own `fullName`: the describe chain and title, space-joined."""
        return " ".join(test.split("::")[1:])


def _suite_of(file_path: str, report: dict) -> str:
    """The suite a report entry belongs to: its first path segment under the run root.

    vitest reports an absolute path and does not name the root it ran from, so
    the root is taken to be the sandbox's oracle mount. Matching on a path
    segment called `oracle` instead would break the moment a task's own
    directory tree contains one.
    """
    path = Path(file_path)
    for root in ("/eval/oracle",):
        try:
            return path.relative_to(root).parts[0]
        except ValueError:
            continue
    parts = path.parts
    return parts[1] if len(parts) > 1 else ""
