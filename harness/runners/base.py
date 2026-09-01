"""The Runner interface: what the scoring sandbox needs from a language.

The sandbox owns everything that is not language-specific - container limits,
file transfer, network disconnection, batching, aggregation, provenance
auditing. A runner supplies six required pieces and two optional ones:

  discover      which tests exist (the scoring denominator, computed on the host)
  setup         an ordered sequence of shell steps that make the container ready
  batch         how to run one batch of tests
  outcomes      how to read per-test results back
  function_of   how to collapse a parameterised case onto its function
  synthetic_id  a well-formed identifier, so a caller can learn the key shape
  dependencies  which atomic tests an integration test builds on (optional)
  provenance    how to prove the candidate is what got imported (optional)

Installation is one method, not five: a language's setup is inherently ordered
(test framework, then oracle dependencies, then the candidate) and the sandbox
should not have to know that order. Returning a sequence of `Step` keeps the
ordering with the language that owns it and lets a runner insert a step the
others do not need - a toolchain fetch, a build, a codegen pass - without
changing the sandbox.

Oracle layout per language
--------------------------

A suite is `atomic` or `integration`. What that name denotes physically is the
runner's decision, and the shapes differ enough to be worth stating in one
place - a task authored against the wrong shape enumerates zero tests, which
reads as a candidate that implemented nothing:

  python      oracle/test_{suite}.py                      one file per suite
  go          oracle/{suite}/*_test.go                    one module, one package
                                                          per suite; the package
                                                          name must equal the
                                                          suite name, because
                                                          `outcomes` builds ids
                                                          from the Package field
  typescript  oracle/{suite}/*.test.ts                    one package, run from
                                                          the oracle root with
                                                          the suite as a filter
  rust        oracle/{suite}/src/**.rs                    a workspace whose
                                                          member crates are named
                                                          for their suites, for
                                                          the same reason as Go
  java        oracle/src/test/java/{suite}/*.java         one Maven project, one
                                                          package per suite
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Iterable, Optional

#: A test identifier spelled the way the language's own tooling spells it,
#: relative to the oracle directory. Opaque to the sandbox.
TestId = str


@dataclass(frozen=True)
class Step:
    """One shell command in a container preparation sequence.

    ``required=True`` marks a step whose failure is an infrastructure fault
    rather than a candidate fault: installing pytest, fetching a toolchain.
    Such a failure must abort scoring instead of producing a page of zeros that
    would be read as a model that cannot code.

    ``capture=True`` marks a step whose output belongs in the result's install
    log - candidate installation, where the log is the evidence for why an
    import later failed.
    """

    command: str
    timeout: int = 300
    required: bool = False
    capture: bool = False


@dataclass(frozen=True)
class Batch:
    """A command running one batch of tests, and where its report lands.

    ``command`` runs with ``/eval`` as the working directory and no network. It
    must not swallow the test process's exit status: the sandbox appends an
    exit-code marker and reads it to tell a timeout from a collection error.

    ``report`` is a path inside the container, read after the command finishes
    and passed to ``Runner.outcomes``. Leave it ``None`` for tooling that only
    writes to stdout.
    """

    command: str
    report: Optional[str] = None


@dataclass(frozen=True)
class Env:
    """Where things live inside the scoring container, plus what to strip.

    Paths are container paths, fixed by the sandbox. ``target_modules`` names
    the modules the candidate is supposed to provide, and ``shadowing`` names
    distributions that must be removed first because they would let the oracle
    import the real library instead of the candidate.
    """

    workspace: str = "/eval/workspace"
    oracle: str = "/eval/oracle"
    extra_requirements: Optional[str] = None
    target_modules: tuple[str, ...] = ()
    shadowing: tuple[str, ...] = ()

    #: Host-side paths, for deciding which steps are needed at all.
    workspace_host: Optional[Path] = None
    oracle_host: Optional[Path] = None


class Runner(ABC):
    """Language-specific half of the scoring sandbox.

    Implementations are stateless; one instance is reused across tasks.
    """

    #: Value of ``task.json``'s ``language`` field that selects this runner.
    language: ClassVar[str]

    # ── discovery (host side, before the container starts) ────────────────

    @abstractmethod
    def discover(self, oracle_host: Path, suite: str) -> list[TestId]:
        """Tests in ``suite``, in a stable order. This is the denominator.

        Computed on the host from the oracle source, never by asking the
        language's collector inside the container: a candidate whose import
        crashes collection would otherwise shrink its own denominator and score
        higher for being less runnable. An empty list means the suite is absent,
        which is a zero denominator rather than an error.
        """

    # ── container preparation ────────────────────────────────────────────

    @abstractmethod
    def setup(self, env: Env) -> Iterable[Step]:
        """Ordered steps that leave the container ready to run the oracle.

        Covers the test framework, the oracle's dependencies, removal of
        shadowing distributions, and installation of the candidate itself.
        """

    # ── execution ─────────────────────────────────────────────────────────

    @abstractmethod
    def batch(self, suite: str, tests: list[TestId], offset: int, timeout: int) -> Batch:
        """Command running one batch, with a per-batch report."""

    @abstractmethod
    def outcomes(self, report: str, stdout: str) -> Optional[dict[TestId, str]]:
        """Per-test outcomes, or ``None`` when the batch produced no usable report.

        ``None`` is load-bearing: it tells the sandbox to record the batch as
        ``timeout``/``no_report`` for every test in it, rather than counting the
        tests as failures. Outcome strings stay in the language's own vocabulary;
        only ``"passed"`` is interpreted.
        """

    @abstractmethod
    def function_of(self, test: TestId) -> str:
        """Collapse a case identifier onto its function key.

        The benchmark counts functions; a parameterised function passes only when
        every one of its cases passes. Both a case and a plain test must map onto
        the same key.
        """

    @abstractmethod
    def synthetic_id(self, suite: str) -> TestId:
        """A well-formed identifier for a hypothetical test in ``suite``.

        Only its shape matters. It lets a caller learn the prefix
        ``function_of`` gives that suite -- `test_atomic::` in Python,
        `atomic::` in Go -- without a real test to hand, which an empty or
        unreadable suite would not provide.
        """

    # ── optional ──────────────────────────────────────────────────────────

    def dependencies(self, oracle_host: Path) -> dict[str, list[str]]:
        """Which atomic tests each integration test builds on.

        The map is keyed by integration test function name; each value lists
        atomic function names. It is what separates a True Integration Gap
        Event - an integration test failing while every primitive it needs
        passes, so the defect is in the composition - from cascade, where the
        integration test had no chance because a primitive was broken. Without
        it the sandbox reports ``adjusted_gap: null`` and the run carries only
        the raw rate difference, which across the v3 data was negative in 167
        of 486 runs because a broken primitive lowers both layers at once.

        Read on the host from the oracle source, like ``discover``: the
        candidate must not be able to influence the eligible set.

        Default: no dependency information. A language whose oracle has no way
        to express the relation yet is not a defect, so the sandbox degrades to
        the raw gap rather than failing the task.
        """
        return {}

    def provenance(self, env: Env) -> Optional[str]:
        """A command printing where each target module resolved from.

        Default: no audit. A language without observable import provenance is not
        a candidate defect, so the sandbox skips the check rather than failing
        the task.
        """
        return None


def nested_names(
    text: str,
    openers: "list[tuple[int, str]]",
    leaves: "list[tuple[int, str]]",
) -> list[list[str]]:
    """Resolve each leaf's enclosing scope chain by brace depth.

    TypeScript's `describe` blocks and Rust's `mod` blocks nest the same way and
    are read the same way: a regexp finds the openers and the leaves, and the
    text tells which openers a given leaf sits inside. The regexp match carries
    no extent, so depth is what relates them.

    ``openers`` and ``leaves`` are ``(offset, name)`` pairs. Returns one chain
    per leaf, in the order the leaves were given, each chain ending with the
    leaf's own name.

    Depth is accumulated in one pass over the text rather than recounted per
    match: counting braces from the start for every event is quadratic in file
    length, and the largest oracle here carries 168 tests.
    """
    events = sorted(
        [(offset, 0, name) for offset, name in openers]
        + [(offset, 1, name) for offset, name in leaves]
    )
    depths: dict[int, int] = {}
    depth = 0
    cursor = 0
    for offset, _kind, _name in events:
        while cursor < offset:
            character = text[cursor]
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            cursor += 1
        depths[offset] = depth

    chains: list[list[str]] = []
    stack: list[tuple[int, str]] = []
    for offset, kind, name in events:
        at = depths[offset]
        while stack and stack[-1][0] >= at:
            stack.pop()
        if kind == 0:
            stack.append((at, name))
        else:
            chains.append([enclosing for _, enclosing in stack] + [name])
    return chains


#: `// DependsOn: a, b` on one line of a comment block. `;` is accepted as a
#: separator alongside `,` because both read naturally in a sentence.
_DEPENDS_ON = re.compile(r"^\s*//\s*DependsOn:\s*(.+)$")


def depends_on_above(text: str, offset: int) -> list[str]:
    """Names declared by `// DependsOn:` lines in the block just above ``offset``.

    Go, TypeScript and Rust spell a line comment the same way and none of them
    has anywhere to hang a marker the way a pytest decorator does, so all three
    carry the relation in the comment block immediately above the declaration
    and all three read it here. Names come back in source order, deduplicated,
    so repeating one across two lines of the block is not an error.

    ``offset`` is the start of the match a runner's own declaration pattern
    produced, which may begin part-way into its line, so one trailing
    whitespace-only line is dropped before the walk begins. That line is the
    declaration's own indentation when it has any and a blank separator
    otherwise, which is why a declaration at the left margin may keep one blank
    line between itself and the block and an indented one may not.

    The block has to sit above the *whole* declaration, not inside it: each of
    these patterns spans several tokens -- `#[test]` through `fn name`, `it`
    through its title -- and a comment landing in that span stops the pattern
    matching, which removes the test from `discover` and from the denominator
    with it. A `///` doc comment or a `//!` inner comment continues the block
    without naming anything: the marker looks for `DependsOn:` right after the
    two slashes, give or take whitespace, and a third slash or a `!` is
    neither.
    """
    lines = text[:offset].splitlines()
    if lines and not lines[-1].strip():
        lines.pop()
    block: list[str] = []
    for line in reversed(lines):
        if not line.strip().startswith("//"):
            break
        block.append(line)

    names: list[str] = []
    for line in reversed(block):
        found = _DEPENDS_ON.match(line)
        if not found:
            continue
        for name in found.group(1).replace(";", ",").split(","):
            name = name.strip()
            if name and name not in names:
                names.append(name)
    return names
