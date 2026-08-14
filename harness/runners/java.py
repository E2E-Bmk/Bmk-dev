"""Java: Maven Surefire, whose report is XML rather than JSON.

Java is the one supported language with no machine-readable JSON test report, so
this runner parses Surefire's per-class XML. Three properties of that toolchain
shape it:

* Surefire writes one `TEST-{class}.xml` per test class into
  `target/surefire-reports/`, with a `testcase` element per test and a child
  element (`failure`, `error`, `skipped`) only when the test did not pass;
* `-Dtest="Class#a+b"` selects exactly those methods, and the ones it did not
  select are absent from the XML rather than reported as skipped -- the same
  arrangement as `go test -run`, and the opposite of vitest's `-t`;
* a `@ParameterizedTest` expands to `method(signature)[index]`, so the case
  marker is structural and `function_of` can strip it.
"""

from __future__ import annotations

import re
import shlex
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator, Optional

try:
    from harness.runners.base import Batch, Env, Runner, Step, TestId
except ImportError:  # direct execution of a harness script
    from runners.base import Batch, Env, Runner, Step, TestId

_CLASS_DECL = re.compile(r"\b(?:public\s+|final\s+|abstract\s+)*class\s+(\w+)")
# A test annotation, then any further annotations (`@ValueSource`,
# `@DisplayName`, ...), then the declaration. Both layouts occur in real code --
# annotation and signature on one line, or the annotation on its own line -- so
# the pattern spans whitespace rather than anchoring to a newline. An earlier
# attempt that required a newline silently dropped every `@ParameterizedTest`
# from the denominator.
_TEST_METHOD = re.compile(
    r"@(?:Test|ParameterizedTest|RepeatedTest|TestFactory)\b\s*(?:\([^)]*\))?"
    r"(?:\s*@\w+\s*(?:\([^)]*\))?)*"
    r"\s*(?:(?:public|private|protected|static|final|abstract|synchronized)\s+)*"
    r"[\w.<>\[\],\s]+?\s+(\w+)\s*\(",
    re.DOTALL,
)


class JavaRunner(Runner):
    language = "java"

    # ── discovery ─────────────────────────────────────────────────────────

    def discover(self, oracle_host: Path, suite: str) -> list[TestId]:
        """`{suite}::{Class}::{method}` for every annotated method in the suite.

        Read from source with a regexp rather than by asking Maven to list
        tests, which needs a successful compile of the candidate: the
        denominator must not depend on whether the candidate builds.
        """
        directory = oracle_host / "src" / "test" / "java" / suite
        if not directory.is_dir():
            return []
        ids: list[TestId] = []
        for source in sorted(directory.rglob("*.java")):
            class_match = _CLASS_DECL.search(
                source.read_text(encoding="utf-8-sig", errors="replace")
            )
            class_name = class_match.group(1) if class_match else source.stem
            text = source.read_text(encoding="utf-8-sig", errors="replace")
            for match in _TEST_METHOD.finditer(text):
                ids.append(f"{suite}::{class_name}::{match.group(1)}")
        return ids

    # ── container preparation ─────────────────────────────────────────────

    def setup(self, env: Env) -> Iterator[Step]:
        """Install the candidate into the local repository, then resolve offline.

        The oracle is a separate Maven project that declares the candidate as a
        dependency. `mvn install` on the candidate is what puts it in the local
        repository where the oracle's coordinates resolve to it, rather than to
        a published artifact of the same coordinates; `provenance` later checks
        which one actually won.

        Resolution happens here, while the network is still connected. The image
        ships a warmed `~/.m2` for the oracle's own plugins and JUnit, because
        scoring runs with the network disconnected and an unresolvable plugin
        would fail every batch identically.
        """
        yield Step("mvn --version", timeout=120, required=True)

        yield Step(
            f"cd {env.workspace} && "
            "if [ -f pom.xml ]; then mvn -B -DskipTests install 2>&1; fi",
            timeout=900,
            capture=True,
        )

        yield Step(
            f"cd {env.oracle} && mvn -B -DskipTests test-compile 2>&1",
            timeout=900,
            capture=True,
        )

    # ── execution ─────────────────────────────────────────────────────────

    def batch(self, suite: str, tests: list[TestId], offset: int, timeout: int) -> Batch:
        """Select the batch's methods with one `-Dtest` expression.

        The expression groups by class -- `A#m1+m2,B#m3` -- because Surefire's
        syntax attaches methods to the class before the `#`. Selection is by
        exact method name, so a sibling whose name merely starts the same way is
        not pulled in.

        `-DfailIfNoSpecifiedTests=false` keeps a batch whose methods all live in
        one class from failing the build when another class contributes none.
        The reports directory is wiped first so a previous batch's XML cannot be
        read as this one's.

        The lifecycle phase `test` is used rather than the `surefire:test` goal.
        Resolving a plugin prefix needs the network, which scoring runs without,
        so `-o surefire:test` fails with "No plugin found for prefix". `setup`
        has already run `test-compile`, so the recompilation here is incremental.
        """
        by_class: dict[str, list[str]] = {}
        for test in tests:
            parts = test.split("::")
            if len(parts) < 3:
                continue
            by_class.setdefault(parts[1], []).append(parts[2])
        selector = ",".join(
            f"{cls}#{'+'.join(sorted(set(methods)))}" for cls, methods in sorted(by_class.items())
        )
        reports = "target/surefire-reports"
        return Batch(
            command=(
                f"cd {shlex.quote(f'/eval/oracle')} && rm -rf {reports} && "
                f"timeout {timeout} mvn -B -o test "
                f"-Dtest={shlex.quote(selector)} "
                f"-DfailIfNoSpecifiedTests=false -Dsurefire.failIfNoSpecifiedTests=false "
                f"> /dev/null 2>&1; "
                # The XML is many files; the report handed to `outcomes` is their
                # concatenation inside one root element so it parses as one
                # document.
                f"printf '<reports>' && cat {reports}/TEST-*.xml 2>/dev/null "
                f"| sed 's|<?xml[^>]*?>||g' && printf '</reports>'"
            ),
            report=None,
        )

    def outcomes(self, report: str, stdout: str) -> Optional[dict[TestId, str]]:
        """Per-test outcomes, from the concatenated Surefire XML on stdout.

        The batch has no report file: Surefire writes a directory of XML, so the
        command emits them wrapped in one element and this reads stdout.

        A `testcase` with no child element passed. `skipped`, `failure` and
        `error` are distinguished because an error is a broken test rather than a
        failed assertion, and the sandbox reports anything that is not `passed`
        as not passed either way.

        Returns ``None`` when the document parses to no test cases: a compile
        failure produces no XML, and that is an unusable batch rather than a set
        of failures.
        """
        text = report or stdout or ""
        # The sandbox appends `; echo __RC__=$?` to every batch command, so the
        # stream is the document followed by that marker. Slicing to the wrapper
        # element is what keeps the trailing text -- and any Maven output the
        # redirect did not catch -- out of the parser.
        start = text.find("<reports>")
        end = text.rfind("</reports>")
        if start == -1 or end == -1:
            return None
        try:
            root = ET.fromstring(text[start : end + len("</reports>")])
        except ET.ParseError:
            return None

        results: dict[TestId, str] = {}
        for case in root.iter("testcase"):
            name = case.get("name") or ""
            classname = case.get("classname") or ""
            if not name:
                continue
            suite, _, simple = classname.rpartition(".")
            key = f"{suite}::{simple}::{name}" if suite else f"{simple}::{name}"
            outcome = "passed"
            for child in case:
                tag = child.tag.rsplit("}", 1)[-1]
                if tag in {"failure", "error"}:
                    outcome = "failed"
                    break
                if tag == "skipped":
                    outcome = "skipped"
                    break
            results[key] = outcome
        return results or None

    def function_of(self, test: TestId) -> str:
        """Collapse a `@ParameterizedTest` case onto its method.

        Surefire reports a case as `method(signature)[index]`, so the marker is
        structural rather than interpolated into a title as it is in vitest.
        Stripping the argument list and the index maps every case of a method
        onto one key, which is what counting a parameterised test once requires.
        """
        head, _, leaf = test.rpartition("::")
        leaf = re.sub(r"\(.*?\)", "", leaf)
        leaf = re.sub(r"\[[^\]]*\]\s*$", "", leaf)
        return f"{head}::{leaf.strip()}" if head else leaf.strip()

    def synthetic_id(self, suite: str) -> TestId:
        return f"{suite}::Placeholder::placeholder"

    # ── provenance ────────────────────────────────────────────────────────

    def provenance(self, env: Env) -> Optional[str]:
        """Report which artifact each target coordinate resolved to, and its origin.

        `dependency:list -DoutputAbsoluteArtifactFilename` prints
        `group:artifact:jar:version:scope:/path`. Unlike Go, Rust and
        TypeScript, that path is never inside the workspace: Maven resolves
        through the local repository, so a candidate reaches the oracle as
        `~/.m2/repository/.../x.jar` even when `setup` installed it from
        `/eval/workspace` moments earlier.

        The sandbox already has a second channel for exactly this shape -- it
        accepts a module whose `direct_urls` name the workspace, which is how a
        Python editable install passes. So the probe also reads the candidate's
        own coordinates out of its POM and, when they match the resolved
        artifact, reports the workspace as the origin. A published artifact of
        different coordinates, or one the install did not overwrite, produces no
        such match and the audit fails as it should.

        `mvn -o` is required: resolving a plugin prefix needs the network, which
        scoring runs without. The image's local repository is warmed with
        `dependency:list` for that reason.
        """
        if not env.target_modules:
            return None
        names = list(env.target_modules)
        reshape = (
            "import json, re, sys, xml.etree.ElementTree as ET\n"
            f"names = {names!r}\n"
            f"workspace = {env.workspace!r}\n"
            "found = {}\n"
            "for line in sys.stdin:\n"
            "    match = re.search(r'([\\w.\\-]+):([\\w.\\-]+):[\\w.\\-]+:[\\w.\\-]+:[\\w.\\-]+:(/\\S+)', line)\n"
            "    if match:\n"
            "        group, artifact, path = match.groups()\n"
            "        found.setdefault(artifact, path)\n"
            "        found.setdefault(f'{group}:{artifact}', path)\n"
            # The candidate's own coordinates. A match means the artifact the
            # oracle resolved is the one this workspace declares, which is the
            # evidence the install took.
            "own = set()\n"
            "try:\n"
            "    root = ET.parse(f'{workspace}/pom.xml').getroot()\n"
            "    ns = {'m': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}\n"
            "    find = (lambda t: root.find(f'm:{t}', ns)) if ns else (lambda t: root.find(t))\n"
            "    group = find('groupId')\n"
            "    artifact = find('artifactId')\n"
            "    if artifact is not None and artifact.text:\n"
            "        own.add(artifact.text.strip())\n"
            "        if group is not None and group.text:\n"
            "            own.add(f'{group.text.strip()}:{artifact.text.strip()}')\n"
            "except Exception:\n"
            "    pass\n"
            "rows = []\n"
            "for n in names:\n"
            "    path = found.get(n)\n"
            "    rows.append({'name': n,\n"
            "                 'paths': [path] if path else [],\n"
            "                 'direct_urls': ([f'file://{workspace}']\n"
            "                                 if path and n in own else []),\n"
            "                 'error': None if path else 'absent from dependency:list'})\n"
            "print('__PROVENANCE__' + json.dumps(rows, sort_keys=True))\n"
        )
        return (
            f"cd {shlex.quote(env.oracle)} && "
            "mvn -B -o dependency:list -DoutputAbsoluteArtifactFilename=true 2>/dev/null"
            f" | python3 -c {shlex.quote(reshape)}"
        )
