"""Rust: cargo-nextest emitting the libtest JSON event stream.

`cargo test -- --format json` is nightly-only, so the runner uses nextest, whose
`--message-format libtest-json` produces the same event shape on stable. Three
properties of that toolchain shape this runner:

* nextest prints one JSON object per line to stdout, one per test per action,
  the same fold-the-last-terminal-action arrangement as `go test -json`;
* `-q` suppresses that stream entirely, so the batch command must not use it;
* a test's reported name is `{crate}::{binary}${module path}::{name}`, while a
  filter expression names only the part after the `$`. The two forms are not
  interchangeable and `function_of` normalises onto the reported one.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Iterator, Optional

from harness.runners.base import Batch, Env, Runner, Step, TestId, depends_on_above, nested_names

_TEST_FN = re.compile(
    r"#\[(?:test|tokio::test)[^\]]*\](?:\s*#\[[^\]]*\])*\s*(?:async\s+)?fn\s+(\w+)"
)
_MOD_DECL = re.compile(r"\bmod\s+(\w+)\s*\{")


def _workspace_packages(root: Path) -> list[dict[str, str]]:
    """`{name, rel}` for every package reachable from a workspace root.

    Covers the shapes the runner sees: a package manifest at the root, a
    virtual root with ``members`` (globs included, e.g. ``crates/*``), and
    members that are themselves workspaces. ``rel`` is the manifest directory
    relative to ``root``, ready to join onto the container workspace path.
    """
    import tomllib

    found: list[dict[str, str]] = []

    def walk(manifest_dir: Path) -> None:
        data = tomllib.loads(
            (manifest_dir / "Cargo.toml").read_text(encoding="utf-8", errors="replace")
        )
        name = data.get("package", {}).get("name")
        if name:
            found.append({
                "name": name,
                "rel": str(manifest_dir.relative_to(root)),
                "version": str(data.get("package", {}).get("version") or ""),
            })
        for member in data.get("workspace", {}).get("members", []):
            if any(ch in member for ch in "*?["):
                for child in sorted(manifest_dir.glob(member)):
                    if child.is_dir() and (child / "Cargo.toml").is_file():
                        walk(child)
            else:
                child = manifest_dir / member
                if child.is_dir() and (child / "Cargo.toml").is_file():
                    walk(child)

    walk(root)
    return found


class RustRunner(Runner):
    language = "rust"

    # ── discovery ─────────────────────────────────────────────────────────

    def discover(self, oracle_host: Path, suite: str) -> list[TestId]:
        """`{suite}::{module path}::{fn}` for every `#[test]` in the suite.

        Read from source with a regexp rather than from `nextest list`, which
        needs a successful compile: the denominator must not depend on whether
        the candidate builds.

        Module nesting is tracked by brace depth, because a `#[test]` inside
        `mod tests { mod nested { ... } }` is reported as
        `tests::nested::name` and the filter expression has to name it that way.
        """
        directory = oracle_host / suite
        if not directory.is_dir():
            return []
        ids: list[TestId] = []
        for source in sorted(directory.rglob("*.rs")):
            ids += [f"{suite}::{path}" for path in self._paths_in_file(source)]
        return ids

    def _paths_in_file(self, source: Path) -> list[str]:
        text = source.read_text(encoding="utf-8-sig", errors="replace")
        chains = nested_names(
            text,
            [(m.start(), m.group(1)) for m in _MOD_DECL.finditer(text)],
            [(m.start(), m.group(1)) for m in _TEST_FN.finditer(text)],
        )
        return ["::".join(chain) for chain in chains]

    # ── container preparation ─────────────────────────────────────────────

    def setup(self, env: Env) -> Iterator[Step]:
        """Point the oracle crate at the candidate, then warm the build.

        The oracle is a separate crate that depends on the candidate by name. A
        `[patch]` entry pointing at the workspace is what makes the candidate --
        rather than a published crate of the same name -- the thing under test;
        it is the Rust equivalent of the Python provenance concern.

        Fetching and building happen here, while the network is still connected,
        so a compile failure is attributable to this step instead of surfacing
        later as every batch producing no events.
        """
        yield Step("cargo --version && cargo nextest --version", timeout=120, required=True)

        if env.target_modules:
            # `[patch.crates-io]` is appended rather than edited in place:
            # cargo has no `cargo add --patch`, and a duplicate section is a
            # manifest error, so the oracle ships without one.
            patch_paths = self._patch_paths(env)
            lines = ["", "[patch.crates-io]"]
            lines.extend(
                f'{crate} = {{ path = "{patch_paths[crate]}" }}'
                for crate in env.target_modules
            )
            patch = "\n".join(lines) + "\n"
            yield Step(
                f"cd {env.oracle} && printf %s {shlex.quote(patch)} >> Cargo.toml",
                timeout=60,
                required=True,
            )
            versions = self._patch_versions(env)
            packages = " && ".join(
                (
                    f"cargo update -p {shlex.quote(crate)} --precise "
                    f"{shlex.quote(versions[crate])} 2>&1"
                )
                if versions.get(crate)
                else f"cargo update -p {shlex.quote(crate)} 2>&1"
                for crate in env.target_modules
            )
            yield Step(f"cd {env.oracle} && {packages}", timeout=600, capture=True)

        yield Step(f"cd {env.workspace} && cargo fetch 2>&1", timeout=600, capture=True)
        yield Step(f"cd {env.oracle} && cargo fetch 2>&1", timeout=600, capture=True)
        yield Step(
            f"cd {env.oracle} && cargo nextest run --no-run 2>&1",
            timeout=900,
            capture=True,
            # required: a candidate the oracle cannot compile against is a
            # setup failure (setup_error outcomes), not silent no_report
            # evidence. The reference/behavior-empty controls compile, so a
            # failure here is candidate-side, and must be surfaced.
            required=True,
        )

    def _patch_paths(self, env: Env) -> dict[str, str]:
        """Container path per target crate inside the solution workspace.

        Single-crate solutions carry the package manifest at the workspace
        root, so patching the root works (the historic behavior). Virtual
        workspaces (e.g. ``crates/toml`` members) need one path per member: a
        `[patch.crates-io]` entry must point at a package manifest, and cargo
        rejects a virtual root. Resolution runs host-side from
        ``workspace_host``; anything unreadable falls back to the root.
        """
        fallback = {crate: env.workspace for crate in env.target_modules}
        host = env.workspace_host
        if host is None or not (host / "Cargo.toml").is_file():
            return fallback
        try:
            packages = _workspace_packages(host)
        except Exception:
            return fallback
        by_name = {pkg["name"]: pkg["rel"] for pkg in packages}
        return {
            crate: f"{env.workspace}/{by_name[crate]}" if crate in by_name else env.workspace
            for crate in env.target_modules
        }

    def _patch_versions(self, env: Env) -> dict[str, str]:
        """Candidate package version per target crate, when host metadata is readable."""
        host = env.workspace_host
        if host is None or not (host / "Cargo.toml").is_file():
            return {}
        try:
            packages = _workspace_packages(host)
        except Exception:
            return {}
        return {
            pkg["name"]: pkg.get("version", "")
            for pkg in packages
            if pkg["name"] in env.target_modules and pkg.get("version")
        }

    # ── execution ─────────────────────────────────────────────────────────

    def batch(self, suite: str, tests: list[TestId], offset: int, timeout: int) -> Batch:
        """Run the named tests through one nextest filter expression.

        `test(=name)` is an exact match, so unlike a substring filter it cannot
        pull in a sibling whose name merely starts the same way. Terms are
        combined with `+`, nextest's union operator.

        `-q` is deliberately absent: it suppresses the JSON stream, leaving a
        batch that looks like a total failure rather than a set of outcomes.
        """
        names = " + ".join(
            f"test(={self._filter_name(t)})" for t in sorted(set(tests))
        )
        report = f"/eval/rb_{suite}_{offset}.json"
        return Batch(
            command=(
                f"cd {shlex.quote(f'/eval/oracle/{suite}')} && "
                f"NEXTEST_EXPERIMENTAL_LIBTEST_JSON=1 timeout {timeout} "
                f"cargo nextest run --message-format libtest-json "
                f"-E {shlex.quote(names)} "
                f"> {report} 2>/dev/null"
            ),
            report=report,
        )

    def outcomes(self, report: str, stdout: str) -> Optional[dict[TestId, str]]:
        """Fold the event stream into one outcome per test.

        Reported names carry a `{crate}::{binary}$` prefix that the filter
        expression does not use; it is dropped here so the ids match what
        `discover` produced.

        Returns ``None`` when no event names a test: a compile error or a
        timeout kill produces output with no test events, and that is an
        unusable batch rather than a set of failures.
        """
        translate = {"ok": "passed", "failed": "failed", "ignored": "skipped"}
        results: dict[TestId, str] = {}
        for line in (report or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") != "test":
                continue
            action = event.get("event")
            name = event.get("name")
            if not name or action not in translate:
                continue
            results[self._reported_to_id(name)] = translate[action]
        return results or None

    def function_of(self, test: TestId) -> str:
        """Rust has no parameterised-test form in the standard harness.

        A `#[test]` is one function and runs once, so a case identifier and a
        function key are the same string. A macro that generates several tests
        generates several distinct functions, which is what should be counted.
        """
        return test

    def synthetic_id(self, suite: str) -> TestId:
        return f"{suite}::placeholder"

    def dependencies(self, oracle_host: Path) -> dict[str, list[str]]:
        """`// DependsOn:` comments above each integration `#[test]`.

        Keyed by the test's own function name -- the leaf of the
        `{suite}::{module path}::{fn}` id `discover` builds -- because that leaf
        is what both the sandbox and `verify_task` index the relation by. Values
        are atomic function names, read the same way. Read from source on the
        host, like `discover`, so the candidate cannot influence the eligible
        set.
        """
        directory = oracle_host / "integration"
        if not directory.is_dir():
            return {}
        result: dict[str, list[str]] = {}
        for source in sorted(directory.rglob("*.rs")):
            text = source.read_text(encoding="utf-8-sig", errors="replace")
            for match in _TEST_FN.finditer(text):
                names = depends_on_above(text, match.start())
                if names:
                    result[self.function_of(match.group(1))] = names
        return result

    # ── provenance ────────────────────────────────────────────────────────

    def provenance(self, env: Env) -> Optional[str]:
        """Report where the oracle's build resolved each target crate to.

        `cargo metadata` prints the manifest path of every resolved package.
        The sandbox then checks the path is inside the workspace, so a `[patch]`
        entry that silently failed to apply -- leaving a registry copy in play --
        is caught before the scores are believed.

        Rust has no interpreter to run a probe in, so the JSON is reshaped by
        Python, which the image carries for this purpose.
        """
        if not env.target_modules:
            return None
        names = list(env.target_modules)
        reshape = (
            "import json, sys\n"
            f"names = {names!r}\n"
            "packages = {p['name']: p for p in json.load(sys.stdin).get('packages', [])}\n"
            "rows = [{'name': n,\n"
            "         'paths': [packages[n]['manifest_path']] if n in packages else [],\n"
            "         'direct_urls': [],\n"
            "         'error': None if n in packages else 'absent from cargo metadata'}\n"
            "        for n in names]\n"
            "print('__PROVENANCE__' + json.dumps(rows, sort_keys=True))\n"
        )
        return (
            f"cd {shlex.quote(env.oracle)} && cargo metadata --format-version 1 2>/dev/null"
            f" | python3 -c {shlex.quote(reshape)}"
        )

    # ── helpers ───────────────────────────────────────────────────────────

    def _filter_name(self, test: TestId) -> str:
        """The module path nextest's `test(=...)` predicate matches on."""
        return test.split("::", 1)[1] if "::" in test else test

    def _reported_to_id(self, reported: str) -> TestId:
        """`{crate}::{binary}${path}` from the stream back to `{suite}::{path}`.

        The suite name is taken from the crate, which requires the oracle's
        per-suite crate to be named for its suite. `outcomes` is handed a report
        and no context, so there is nowhere else for it to come from; the
        convention is stated in the task layout the design describes.
        """
        crate = reported.split("::", 1)[0] if "::" in reported else ""
        path = reported.split("$", 1)[1] if "$" in reported else reported
        return f"{crate}::{path}" if crate else path
