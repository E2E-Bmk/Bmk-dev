"""
Pure-Linux Docker sandbox for Spec2Repo evaluation.

Architecture — all file transfers use `docker cp`, zero volume mounts:

  Host (any OS)                         Container (Linux)
  ─────────────                         ──────────────────
  workspace dir  ──docker cp──>  /eval/workspace/
  oracle dir     ──docker cp──>  /eval/oracle/
                                 pip install + pytest (batched)
                 <──docker exec──  per-batch pytest-json-report

Security:
  - Scoring network disconnected before pytest runs
  - --memory / --cpus / --pids-limit enforced
  - --security-opt no-new-privileges
  - Oracle tests are copied (not bind-mounted), so no host path leaks

Scoring model (v2):
  - Test functions are enumerated statically (AST) from the oracle files; the
    function list is the scoring denominator. Parameterized expansion never
    inflates a task's weight: a function passes only if every expanded case
    passes.
  - pytest runs in batches of SCORE_BATCH_SIZE functions with a per-batch
    timeout. A hang invalidates one batch, not the whole task.
  - Each batch writes a pytest-json-report; per-test outcomes are returned in
    ScoringResult.tests and persisted by the caller. All downstream gap
    metrics are recomputed from this matrix.
"""

import ast
import json
import logging
import os
import re
import shlex
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("spec2repo.sandbox")

try:
    from harness.runners import Env, get_runner
except ModuleNotFoundError:  # direct execution: python harness/sandbox.py
    from runners import Env, get_runner


def _task_language(task_id: str) -> Optional[str]:
    """The ``language`` field of a task, or ``None`` when it cannot be read.

    ``None`` makes ``get_runner`` fall back to Python. That is the correct
    reading for the interim release, whose tasks predate the field.

    ``SPEC2REPO_TASKS_DIR`` selects an external task pool, the same convention
    ``verify_task.py`` uses. Without it a pool task resolves against the
    in-repo ``tasks/`` directory, reads nothing, and silently scores as Python.
    """
    pool = os.environ.get("SPEC2REPO_TASKS_DIR")
    root = Path(pool) if pool else Path(__file__).resolve().parent.parent / "tasks"
    task_json = root / task_id / "task.json"
    try:
        return json.loads(task_json.read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError):
        return None

SCORE_MEMORY = "1g"  # 512m starved dbt/kedro/sqlalchemy imports; raised to 1g
SCORE_CPUS = "2"
SCORE_PIDS = "256"
SCORE_BATCH_SIZE = 25       # test functions per pytest invocation
SCORE_BATCH_TIMEOUT = 180   # seconds per batch, enforced by timeout(1) in-container
SCORE_SETUP_TIMEOUT = 480   # container lifetime budget for install phase
DEFAULT_IMAGE = "spec2repo-base:latest"

# The scoring image has to carry the toolchain its runner shells out to. This
# is not cosmetic: `cargo nextest` inside the Python base image exits non-zero
# with an empty report, which every downstream reader interprets as "the
# candidate failed every test" rather than "the toolchain was absent".
IMAGE_FOR_LANGUAGE = {
    "go": "spec2repo-go:latest",
    "java": "spec2repo-java:latest",
    "rust": "spec2repo-rust:latest",
    "typescript": "spec2repo-typescript:latest",
}

# Public import roots that must resolve to the candidate workspace. This is
# intentionally independent of distribution names: several projects expose a
# differently named Python package (for example pre-commit -> pre_commit).
# The authoritative import-root table lives in one place, harness/core, so
# the provenance audit here agrees with verify_task.py rather than drifting
# from a second copy.
try:
    from harness.core.target_imports import TARGET_IMPORTS
except ModuleNotFoundError:  # direct execution: python harness/sandbox.py
    from core.target_imports import TARGET_IMPORTS

# Task pools outside tasks/ -- a construction branch under evaluation, a
# candidate batch not yet merged -- carry their own roots. Point
# SPEC2REPO_TARGET_IMPORTS at a JSON object of the same shape to add them
# without editing this file, which would mix an experiment into the release
# configuration. Entries here always win, so an external file cannot silently
# redirect a released task's provenance audit.
_external = os.environ.get("SPEC2REPO_TARGET_IMPORTS")
if _external:
    try:
        _extra = json.loads(Path(_external).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"SPEC2REPO_TARGET_IMPORTS unreadable: {exc}") from exc
    TARGET_IMPORTS = {**_extra, **TARGET_IMPORTS}

# These verifier dependencies pull the reference distribution transitively.
# Remove it before installing the candidate while retaining the supporting
# package (for example dbt-duckdb) needed by the public workflow.
#
# packaging is special: pytest itself depends on the real `packaging` dist,
# so it is present in site-packages before the candidate installs. It cannot
# be uninstalled up front (pytest needs *a* packaging at run time); instead
# the candidate install must shadow it, and provenance verifies the shadowing
# actually happened.
REFERENCE_DISTRIBUTIONS = {
    "dbt-core-fullrepro-001": ["dbt-core"],
    "nbformat-notebook-fullrepro-001": ["nbformat"],
    "sqlalchemy-fullrepro-001": ["SQLAlchemy"],
    "packaging-core-fullrepro-001": ["packaging"],
}

# Tasks whose target package is also a runtime dependency of the verifier
# toolchain (pytest -> packaging). For these, uninstalling the reference copy
# must happen and the candidate must be importable afterwards, otherwise the
# toolchain itself breaks.
TOOLCHAIN_COUPLED = {"packaging-core-fullrepro-001"}

AGENT_DOCKER_RUN_ARGS = [
    "--network=none",
    "--memory=1g",
    "--cpus=2",
    "--pids-limit=512",
    "--security-opt=no-new-privileges",
]


@dataclass
class ScoringResult:
    task_id: str
    platform: str = "Linux/Docker"
    atomic_passed: int = 0
    atomic_total: int = 0
    integration_passed: int = 0
    integration_total: int = 0
    atomic_pass_rate: float = 0.0
    integration_pass_rate: float = 0.0
    integration_gap: float = 0.0
    elapsed_seconds: float = 0.0
    install_log: str = ""
    provenance_log: str = ""
    error: Optional[str] = None
    raw_stdout: str = ""
    raw_stderr: str = ""
    # v2 fields
    count_unit: str = "functions"
    tests: dict = field(default_factory=dict)     # function key -> outcome
    cases: dict = field(default_factory=dict)     # expanded nodeid -> outcome
    batches: list = field(default_factory=list)   # per-batch execution metadata
    # v3 fields - cascade-filtered composition metrics
    adjusted_gap: Optional[float] = None
    adjusted_integ_passed: int = 0
    adjusted_integ_total: int = 0
    adjusted_integ_rate: Optional[float] = None
    gap_confidence: str = "high"  # "high" | "low (cascade risk)" | "no depends_on"


class ScoringSandbox:
    """
    Score candidate code against oracle tests inside a Docker container.

    All file I/O uses `docker cp` — no volume mounts, no host-path leaks.
    """

    def __init__(self, image: Optional[str] = None, timeout: int = SCORE_BATCH_TIMEOUT):
        # ``None`` means "pick from the task's language". An explicit image
        # still wins, which is what the language probes in tests rely on.
        self.image = image
        self.batch_timeout = timeout

    def score(
        self,
        task_id: str,
        workspace_path: Path,
        oracle_path: Path,
        extra_requirements: Optional[Path] = None,
        language: Optional[str] = None,
    ) -> ScoringResult:
        """Score one candidate.

        ``language`` selects the test runner. It defaults to the ``language``
        field of the task's ``task.json``, and to Python when that field is
        absent, which is how every task in the interim release is scored.
        """
        start = time.time()
        cid = f"s2r-score-{task_id[:20]}-{uuid.uuid4().hex[:6]}"

        try:
            language = language or _task_language(task_id)
            runner = get_runner(language)
        except KeyError as exc:
            return ScoringResult(task_id=task_id, elapsed_seconds=time.time() - start,
                                 error=str(exc))

        image = self.image or IMAGE_FOR_LANGUAGE.get(language or "python", DEFAULT_IMAGE)

        try:
            return self._run(cid, task_id, workspace_path, oracle_path, extra_requirements,
                             start, runner, image)
        except subprocess.TimeoutExpired:
            return ScoringResult(task_id=task_id, elapsed_seconds=time.time() - start, error="timeout")
        except Exception as e:
            logger.exception("Scoring failed for %s", task_id)
            return ScoringResult(task_id=task_id, elapsed_seconds=time.time() - start,
                                 error=f"{type(e).__name__}: {e}")
        finally:
            _cleanup(cid)

    def _run(self, cid, task_id, workspace_path, oracle_path, extra_requirements, start,
             runner, image):
        # 0. Enumerate test functions statically — this is the denominator.
        suites = {}
        for suite in ("atomic", "integration"):
            suites[suite] = runner.discover(oracle_path, suite)
        n_batches = sum(
            (len(ids) + SCORE_BATCH_SIZE - 1) // SCORE_BATCH_SIZE for ids in suites.values()
        )

        # The runner's view of the container, built before the container exists
        # because the setup steps it implies are what size the container's life.
        env = Env(
            extra_requirements=(
                "/eval/extra-requirements.txt" if extra_requirements is not None else None
            ),
            target_modules=tuple(TARGET_IMPORTS.get(task_id, [])),
            shadowing=tuple(REFERENCE_DISTRIBUTIONS.get(task_id, [])),
            workspace_host=workspace_path,
            oracle_host=oracle_path,
        )

        # Container lifetime is a hard ceiling on the whole run: PID 1 is a
        # `sleep`, and once it exits every remaining batch produces a zero-byte
        # report and `outcomes` returns None — the same shape as a candidate
        # that implemented nothing.
        #
        # A constant can only size the setup half for the language it was
        # written for. Python's two setup steps sum to exactly
        # SCORE_SETUP_TIMEOUT; every compiled language declares far more (rust
        # 2280s, typescript 2160s, java 1920s, go 1020s) and a single rust step
        # is allowed 900s — almost twice the whole constant. A slow candidate
        # therefore exhausts the container during setup and scores zero for a
        # reason that has nothing to do with the code it wrote. Ask the runner
        # what it intends to spend rather than assuming Python's answer.
        setup_budget = max(
            SCORE_SETUP_TIMEOUT,
            sum(step.timeout for step in runner.setup(env)),
        )
        lifetime = setup_budget + n_batches * (self.batch_timeout + 60)

        # 1. Create container (bridge network for pip install)
        _docker("run", "-d", "--name", cid,
                "--memory", SCORE_MEMORY,
                f"--cpus={SCORE_CPUS}",
                "--pids-limit", SCORE_PIDS,
                "--security-opt", "no-new-privileges",
                "-w", "/eval",
                image, "sleep", str(lifetime),
                timeout=30)

        # 2. Copy files INTO container via docker cp (no host paths leak)
        _docker_cp(str(workspace_path), f"{cid}:/eval/workspace", timeout=120)
        _docker_cp(str(oracle_path), f"{cid}:/eval/oracle", timeout=30)
        if extra_requirements is not None:
            if not extra_requirements.is_file():
                raise FileNotFoundError(
                    f"extra requirements file not found: {extra_requirements}"
                )
            _docker_cp(
                str(extra_requirements), f"{cid}:/eval/extra-requirements.txt", timeout=30
            )

        # 3. Prepare the container (with network). The runner owns the order;
        #    a step marked `required` is infrastructure and aborts on failure,
        #    a step marked `capture` contributes to the install log.
        install_log = ""
        for step in runner.setup(env):
            out = _exec(cid, step.command, timeout=step.timeout, check=step.required)
            if step.capture:
                install_log += out

        # Install the candidate package. The spec promises: "Declare runtime
        # dependencies in a standard requirements.txt or pyproject.toml at the
        # project root. All declared dependencies will be installed before
        # assessment." Honor both halves — a requirements.txt-only candidate
        # must not lose its dependencies because packaging metadata is absent.
        # 4. Disconnect network BEFORE running tests
        _docker("network", "disconnect", "bridge", cid, timeout=15, check=False)

        provenance_log, provenance_error = _check_provenance(cid, task_id, runner, env)
        if provenance_error:
            return ScoringResult(
                task_id=task_id,
                elapsed_seconds=time.time() - start,
                install_log=install_log,
                provenance_log=provenance_log,
                error=provenance_error,
            )

        # 5. Run pytest in batches with NO NETWORK; each batch has an
        #    independent timeout so a hang invalidates one batch only.
        tests, cases, batches, raw = {}, {}, [], []
        for suite in ("atomic", "integration"):
            s_tests, s_cases, s_batches, s_raw = self._run_suite(
                cid, suite, suites[suite], runner
            )
            tests.update(s_tests)
            cases.update(s_cases)
            batches.extend(s_batches)
            raw.append(s_raw)

        # 6. Aggregate per function (a function passes iff all its expanded
        #    cases pass; a batch timeout marks its functions as 'timeout').
        #
        # The suite prefix is the runner's, not pytest's: Python keys a function
        # as `test_atomic::name` and Go as `atomic::TestName`. Hardcoding the
        # Python form counted zero passes for a Go task whose every test passed,
        # which reads as a candidate that implemented nothing.
        atomic_prefix = f"{_suite_prefix(runner, 'atomic')}::"
        integration_prefix = f"{_suite_prefix(runner, 'integration')}::"
        ap = sum(1 for k, v in tests.items() if k.startswith(atomic_prefix) and v == "passed")
        at = len(suites["atomic"])
        ip = sum(1 for k, v in tests.items() if k.startswith(integration_prefix) and v == "passed")
        it = len(suites["integration"])
        ar = ap / max(at, 1)
        ir = ip / max(it, 1)

        # 7. Compute adjusted_gap: among integration tests whose atomic
        #    prerequisites passed, measure the remaining composition failure
        #    rate. This removes failures caused by missing primitives.
        adj_gap, adj_ip, adj_it, adj_ir, gap_conf = _compute_adjusted_gap(
            oracle_path, tests, ar, runner
        )

        parse_errors = []
        if at == 0:
            parse_errors.append("atomic test count is zero")
        if it == 0:
            parse_errors.append("integration test count is zero")
        parse_errors.extend(_batch_execution_errors(batches))

        return ScoringResult(
            task_id=task_id,
            atomic_passed=ap, atomic_total=at,
            integration_passed=ip, integration_total=it,
            atomic_pass_rate=round(ar, 4),
            integration_pass_rate=round(ir, 4),
            integration_gap=round(ar - ir, 4),
            elapsed_seconds=time.time() - start,
            install_log=install_log,
            provenance_log=provenance_log,
            error="; ".join(parse_errors) or None,
            raw_stdout="\n---\n".join(raw),
            count_unit="functions",
            tests=tests,
            cases=cases,
            batches=batches,
            adjusted_gap=adj_gap,
            adjusted_integ_passed=adj_ip,
            adjusted_integ_total=adj_it,
            adjusted_integ_rate=adj_ir,
            gap_confidence=gap_conf,
        )

    def _run_suite(self, cid, suite, node_ids, runner):
        """Run one oracle suite in batches. Returns (functions, cases, batches, raw)."""
        tests: dict = {}
        cases: dict = {}
        batches: list = []
        raw_parts: list = []
        for bi in range(0, len(node_ids), SCORE_BATCH_SIZE):
            batch = node_ids[bi:bi + SCORE_BATCH_SIZE]
            invocation = runner.batch(suite, batch, bi, self.batch_timeout)
            out = _exec(cid, f"{invocation.command}; echo __RC__=$?",
                        timeout=self.batch_timeout + 45)
            raw_parts.append(out[-4000:])
            m = re.search(r"__RC__=(\d+)", out)
            rc = int(m.group(1)) if m else -1

            report_text = ""
            if invocation.report:
                report_text = _exec(
                    cid, f"cat {shlex.quote(invocation.report)} 2>/dev/null", timeout=30
                )
            batch_outcomes = runner.outcomes(report_text, out)

            if batch_outcomes is None:
                status = "timeout" if rc == 124 else "no_report"
                for n in batch:
                    tests[runner.function_of(n)] = status
                batches.append({"suite": suite, "offset": bi, "size": len(batch),
                                "rc": rc, "status": status})
                continue

            # Case-level records + function-level aggregation: a function is
            # "passed" only if every one of its expanded cases passed.
            for nodeid, outcome in batch_outcomes.items():
                cases[nodeid] = outcome
            per_fn = _aggregate_function_outcomes(batch_outcomes, runner.function_of)
            for n in batch:
                key = runner.function_of(n)
                tests[key] = per_fn.get(key, "not_collected")
            status = (
                "timeout" if rc == 124
                else "collect_error" if not batch_outcomes or rc in {2, 3, 4, 5}
                else "ok"
            )
            batches.append({"suite": suite, "offset": bi, "size": len(batch),
                            "rc": rc, "status": status})
        return tests, cases, batches, "\n".join(raw_parts)


def get_agent_docker_run_args(extra: list[str] | None = None) -> list[str]:
    args = list(AGENT_DOCKER_RUN_ARGS)
    if extra:
        args.extend(extra)
    return args


def _aggregate_function_outcomes(
    batch_outcomes: dict[str, str], key_of=None
) -> dict[str, str]:
    """Reduce expanded cases without allowing report order to hide failures.

    ``key_of`` maps a case identifier onto its function key and defaults to the
    Python convention, so existing callers keep working unchanged.
    """
    key_of = key_of or _fn_key
    grouped: dict[str, list[str]] = {}
    for nodeid, outcome in batch_outcomes.items():
        grouped.setdefault(key_of(nodeid), []).append(outcome)

    priority = ("xpassed", "skipped", "xfailed")
    result: dict[str, str] = {}
    for key, outcomes in grouped.items():
        if any(outcome in {"failed", "error"} for outcome in outcomes):
            result[key] = "failed"
        elif all(outcome == "passed" for outcome in outcomes):
            result[key] = "passed"
        else:
            result[key] = next(
                (outcome for outcome in priority if outcome in outcomes),
                next(outcome for outcome in outcomes if outcome != "passed"),
            )
    return result


def _batch_execution_errors(batches: list[dict]) -> list[str]:
    """Promote incomplete pytest execution to a top-level scoring error."""
    errors = []
    timed_out = [batch for batch in batches if batch.get("status") == "timeout"]
    if timed_out:
        errors.append(f"{len(timed_out)}/{len(batches)} batches timed out (partial score)")
    invalid = [
        batch
        for batch in batches
        if batch.get("status") in {"no_report", "collect_error"}
    ]
    if invalid:
        errors.append(
            f"{len(invalid)}/{len(batches)} batches had collection/report errors "
            "(invalid score)"
        )
    return errors


# ─── Adjusted Gap computation ────────────────────────────────────────────────

def _compute_adjusted_gap(
    oracle_path: Path,
    tests: dict,
    atomic_rate: float,
    runner,
) -> tuple[Optional[float], int, int, Optional[float], str]:
    """
    Compute the cascade-filtered composition failure rate.

    ``adjusted_gap`` is ``1 - adjusted_integration_rate``. The eligible set
    contains only marked integration tests whose atomic prerequisites passed.

    The dependency relation comes from the runner, because its notation is
    language-specific: a pytest marker in Python, and something else wherever
    decorators do not exist. A runner reporting none degrades this to the raw
    gap rather than failing the run.

    Returns (adjusted_gap, adj_passed, adj_total, adj_rate, confidence).
    """
    deps_map = runner.dependencies(oracle_path)

    if not deps_map:
        # Two different situations share this branch. A language whose oracle
        # cannot express the relation yet reports nothing, and so does a Python
        # oracle with no markers. Neither is scoreable, and a low atomic rate
        # means the raw gap is the one number that must not be read as
        # composition evidence.
        if atomic_rate < 0.70:
            return None, 0, 0, None, "low (cascade risk)"
        return None, 0, 0, None, "no depends_on"

    # The suite prefix of a function key is the runner's, not pytest's: Python
    # yields `test_atomic::name` and Go `atomic::TestName`. Deriving it from
    # what the runner discovered keeps this free of per-language names.
    atomic_prefix = _suite_prefix(runner, "atomic")
    integration_prefix = _suite_prefix(runner, "integration")

    atomic_outcomes, atomic_ambiguous = _suite_outcomes_by_name(tests, atomic_prefix)
    integration_outcomes, integration_ambiguous = _suite_outcomes_by_name(
        tests, integration_prefix
    )
    if atomic_ambiguous or integration_ambiguous:
        return None, 0, 0, None, "ambiguous test names"

    known_atomic = set(atomic_outcomes)
    referenced_atomic = {dep for deps in deps_map.values() for dep in deps}
    if not referenced_atomic <= known_atomic:
        return None, 0, 0, None, "invalid depends_on"

    integration_total = len(integration_outcomes)
    dependency_coverage = len(deps_map) / max(integration_total, 1)

    eligible_passed = 0
    eligible_total = 0

    for integ_fn, dep_atomics in deps_map.items():
        if integ_fn not in integration_outcomes:
            continue

        all_deps_pass = all(
            atomic_outcomes.get(dep) == "passed"
            for dep in dep_atomics
        )
        if not all_deps_pass:
            continue

        eligible_total += 1
        if integration_outcomes[integ_fn] == "passed":
            eligible_passed += 1

    if eligible_total == 0:
        if atomic_rate < 0.70:
            return None, 0, 0, None, "low (cascade risk)"
        return None, 0, 0, None, "no eligible"

    adj_rate = eligible_passed / eligible_total
    adj_gap = round(1.0 - adj_rate, 4)
    confidence = "high" if dependency_coverage >= 0.50 else "low (depends_on coverage)"
    return adj_gap, eligible_passed, eligible_total, round(adj_rate, 4), confidence


def _suite_prefix(runner, suite: str) -> str:
    """The prefix a runner's function keys carry for ``suite``.

    Asked of the runner by way of a synthetic identifier rather than assumed,
    because the shape is the runner's: `test_atomic::name` in Python,
    `atomic::TestName` in Go. Deriving it from a discovered test instead would
    make the prefix depend on the suite being non-empty, and an empty suite is
    exactly when the outcome lookup must still address the right keys.
    """
    key = runner.function_of(runner.synthetic_id(suite))
    head, sep, _ = key.partition("::")
    return head if sep else suite


def _suite_outcomes_by_name(
    tests: dict[str, str], suite: str
) -> tuple[dict[str, str], set[str]]:
    """Index function outcomes by leaf name, rejecting class-name collisions.

    The leaf is taken the way `verify_task._leaf_keys` takes it, and for the
    same reason the two must agree: this map is looked up with names a runner's
    `dependencies()` produced, and that gate already accepted them. Splitting on
    `.` alone was written when Python was the only language, where a class
    method is the sole nesting form. Java nests as `Class::method`, Rust as
    `mod::fn` and TypeScript as `describe::title`, so a `.`-only split returns
    the whole path and every lookup misses -- `adjusted_gap` came back
    `invalid depends_on` for all three regardless of how the oracle was written.
    """
    prefix = f"{suite}::"
    outcomes: dict[str, str] = {}
    ambiguous: set[str] = set()
    for key, outcome in tests.items():
        if not key.startswith(prefix):
            continue
        name = key.removeprefix(prefix).rsplit(".", 1)[-1].rsplit("::", 1)[-1]
        if name in outcomes:
            ambiguous.add(name)
        else:
            outcomes[name] = outcome
    return outcomes, ambiguous


# ─── Static test enumeration ─────────────────────────────────────────────────

def _test_node_ids(test_file: Path) -> list[str]:
    """Enumerate function-level pytest node ids (File::Class::method) via AST."""
    tree = ast.parse(test_file.read_text(encoding="utf-8-sig", errors="replace"),
                     filename=str(test_file))
    ids = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            ids.append(f"{test_file.name}::{node.name}")
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test"):
                    ids.append(f"{test_file.name}::{node.name}::{sub.name}")
    return ids


def _fn_key(nodeid: str) -> str:
    """Normalize a nodeid to the canonical function key: file_stem::[Cls.]name."""
    nodeid = nodeid.split("[", 1)[0]
    parts = nodeid.replace("\\", "/").split("::")
    stem = parts[0].rsplit("/", 1)[-1]
    stem = stem[:-3] if stem.endswith(".py") else stem
    qual = ".".join(parts[1:])
    return f"{stem}::{qual}"


def _parse_json_report(text: str) -> Optional[dict]:
    """Extract {nodeid: outcome} from a pytest-json-report payload."""
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    outcomes = {}
    for t in data.get("tests", []):
        nodeid = t.get("nodeid", "")
        outcome = t.get("outcome", "error")
        # setup/teardown errors surface as outcome "error"; xfail family kept verbatim
        outcomes[nodeid] = outcome
    return outcomes


# ─── Low-level helpers ───────────────────────────────────────────────────────

def _docker(*args: str, timeout: int = 60, check: bool = True) -> str:
    cmd = ["docker", *args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"docker {args[0]} failed (rc={r.returncode}): {r.stderr[:500]}")
    return r.stdout + r.stderr


def _docker_cp(src: str, dst: str, timeout: int = 60):
    """Copy files between the host and a container without rewriting paths.

    `-L` dereferences a symlinked source. Without it `docker cp` copies the
    link itself, so a pool assembled by symlinking -- `oracle-root/<id>` ->
    `tasks/<id>/oracle`, which is how the Java pool is laid out -- arrives as
    a dangling link to a host path the container cannot see. The copy still
    reports success, and the failure only surfaces later as `cd: /eval/oracle:
    No such file or directory`, which reads like a missing oracle rather than
    a copied symlink.
    """
    subprocess.run(["docker", "cp", "-L", src, dst],
                   check=True, capture_output=True, timeout=timeout)


def _exec(cid: str, cmd: str, timeout: int = 60, check: bool = False) -> str:
    r = subprocess.run(
        ["docker", "exec", cid, "bash", "-c", cmd],
        capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )
    if check and r.returncode != 0:
        raise RuntimeError(f"container command failed (rc={r.returncode}): {r.stderr[:500]}")
    return r.stdout + r.stderr


def _check_provenance(cid: str, task_id: str, runner, env) -> tuple[str, Optional[str]]:
    """
    Verify every target module resolves inside the candidate workspace.

    The probe command comes from the runner, because import provenance is
    language-specific. A runner returning ``None`` has no observable provenance;
    the audit is then skipped rather than failed, since that is a property of the
    language and not a defect in the candidate.

    Primary evidence is the imported module's own __file__ / __path__ — this is
    what the test run will actually execute. It is robust to editable installs,
    whose importlib metadata reports finder hook strings rather than paths
    (origin=None, locations like '__editable__.pkg...__path_hook__').
    A module passes if ANY resolved filesystem path is inside the workspace;
    it fails if it cannot be imported or resolves only outside the workspace.
    """
    if not env.target_modules:
        return "", f"no target import roots configured for {task_id}"

    probe = runner.provenance(env)
    if probe is None:
        return "provenance audit not available for this language", None

    output = _exec(cid, probe, timeout=60)
    marker = "__PROVENANCE__"
    if marker not in output:
        return output, "candidate import provenance probe failed"
    try:
        rows = json.loads(output.split(marker, 1)[1].strip().splitlines()[0])
    except (ValueError, IndexError):
        return output, "candidate import provenance output is invalid"

    workspace = "/eval/workspace"
    bad = []
    for row in rows:
        if row.get("error"):
            bad.append(f"{row.get('name')} import failed: {row['error']}")
            continue
        paths = [p for p in row.get("paths", []) if p]
        inside = [p for p in paths if p == workspace or p.startswith(workspace + "/")]
        from_workspace_install = any(
            u.startswith(f"file://{workspace}") for u in row.get("direct_urls", [])
        )
        if not inside and not from_workspace_install:
            bad.append(f"{row.get('name')}={paths or ['missing']}")
    if bad:
        return output, "target import resolved outside candidate workspace: " + "; ".join(bad)
    return output, None


def _cleanup(cid: str):
    try:
        subprocess.run(["docker", "rm", "-f", cid],
                       capture_output=True, timeout=15)
    except Exception:
        pass
