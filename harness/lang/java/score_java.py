#!/usr/bin/env python3
"""Score Java task candidates through :class:`JavaRunner` in Docker."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform as host_platform
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

# Direct execution puts this file's own directory on the import path rather than
# the repository root, so the absolute `harness.` imports below would not
# resolve. Adding the root keeps the script form and the module form equivalent.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from harness.runners import Env, Runner, get_runner


LAYERS = ("atomic", "integration", "system_e2e")


class ConfigError(ValueError):
    """The task packet cannot be scored without changing its meaning."""


@dataclass(frozen=True)
class Mount:
    host: Path
    container: str
    read_only: bool = False


@dataclass(frozen=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


class DockerExecutor:
    def __init__(self, image: str):
        self.image = image

    def command_args(
        self, command: str, mounts: list[Mount], *, network: bool
    ) -> list[str]:
        args = ["docker", "run", "--rm"]
        if not network:
            args.extend(["--network", "none"])
        for mount in mounts:
            specification = (
                f"type=bind,source={mount.host.resolve()},target={mount.container}"
            )
            if mount.read_only:
                specification += ",readonly"
            args.extend(["--mount", specification])
        args.extend([self.image, "sh", "-lc", command])
        return args

    def run(
        self,
        command: str,
        mounts: list[Mount],
        *,
        network: bool,
        timeout: int,
    ) -> CommandResult:
        args = self.command_args(command, mounts, network=network)
        try:
            completed = subprocess.run(
                args,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            return CommandResult(
                command=command,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        except subprocess.TimeoutExpired as error:
            return CommandResult(
                command=command,
                returncode=124,
                stdout=error.stdout or "",
                stderr=error.stderr or "timeout",
                timed_out=True,
            )
        except OSError as error:
            raise ConfigError(f"Docker executable is unavailable: {error}") from error

    def seed_maven_repository(self, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        try:
            created = subprocess.run(
                ["docker", "create", self.image, "true"],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError as error:
            raise ConfigError(f"Docker executable is unavailable: {error}") from error
        if created.returncode != 0:
            raise ConfigError(
                f"cannot create Docker container from {self.image}: {created.stderr.strip()}"
            )
        container = created.stdout.strip()
        try:
            copied = subprocess.run(
                ["docker", "cp", f"{container}:/root/.m2/.", str(destination)],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if copied.returncode != 0:
                raise ConfigError(
                    f"cannot seed Maven repository from {self.image}: {copied.stderr.strip()}"
                )
        finally:
            subprocess.run(
                ["docker", "rm", "-f", container],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )


@dataclass(frozen=True)
class ScoreConfig:
    task_dir: Path
    solution_dir: Path
    run_dir: Path
    oracle_dir: Path
    scoring_dir: Path
    result_path: Path
    taxonomy_path: Path | None
    taxonomy_inline: Mapping[str, str] | None
    coordinate: str
    image: str
    batch_size: int
    timeout: int
    reference: bool
    overwrite: bool
    task_id: str
    source_repo: str | None


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def resolve_config(args: argparse.Namespace) -> ScoreConfig:
    task_dir = _resolved(args.task_dir)
    solution_dir = _resolved(args.solution_dir)
    run_dir = _resolved(args.run_dir)
    if not task_dir.is_dir():
        raise ConfigError(f"task directory does not exist: {task_dir}")
    if not solution_dir.is_dir() or not (solution_dir / "pom.xml").is_file():
        raise ConfigError(f"solution must contain pom.xml: {solution_dir}")

    metadata_path = task_dir / "task.json"
    metadata: dict[str, Any] = {}
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        language = str(metadata.get("language", "")).lower()
        if language != "java":
            raise ConfigError(f"task language must be java, got {language or 'missing'}")

    oracle_dir = _resolved(args.oracle_dir) if args.oracle_dir else task_dir / "oracle"
    if not oracle_dir.is_dir() or not (oracle_dir / "pom.xml").is_file():
        raise ConfigError(f"oracle must contain pom.xml: {oracle_dir}")

    coordinate = args.maven_coordinate or metadata.get("maven_coordinates")
    if not coordinate or str(coordinate).count(":") != 1:
        raise ConfigError("a groupId:artifactId Maven coordinate is required")

    taxonomy_path = _resolved(args.taxonomy) if args.taxonomy else None
    taxonomy_inline = metadata.get("taxonomy") if isinstance(metadata.get("taxonomy"), dict) else None
    if taxonomy_path is None and taxonomy_inline is None:
        candidate = task_dir / "filter" / "taxonomy.jsonl"
        if candidate.is_file():
            taxonomy_path = candidate.resolve()
    if taxonomy_path is not None and not taxonomy_path.is_file():
        raise ConfigError(f"taxonomy file does not exist: {taxonomy_path}")
    if taxonomy_path is None and taxonomy_inline is None:
        raise ConfigError("taxonomy is required in task.json or filter/taxonomy.jsonl")

    result_path = (
        _resolved(args.json_out)
        if args.json_out
        else run_dir / ("reference_score.json" if args.reference else "score_result.json")
    )
    if args.batch_size <= 0 or args.timeout <= 0:
        raise ConfigError("batch size and timeout must be positive")
    return ScoreConfig(
        task_dir=task_dir,
        solution_dir=solution_dir,
        run_dir=run_dir,
        oracle_dir=oracle_dir.resolve(),
        scoring_dir=run_dir / "scoring",
        result_path=result_path,
        taxonomy_path=taxonomy_path,
        taxonomy_inline=taxonomy_inline,
        coordinate=str(coordinate),
        image=args.image,
        batch_size=args.batch_size,
        timeout=args.timeout,
        reference=args.reference,
        overwrite=args.overwrite,
        task_id=str(metadata.get("instance_id") or task_dir.name),
        source_repo=metadata.get("source_path"),
    )


def load_effective_taxonomy(config: ScoreConfig) -> dict[str, str]:
    if config.taxonomy_inline is not None and config.taxonomy_path is None:
        return {str(key): str(value) for key, value in config.taxonomy_inline.items()}
    assert config.taxonomy_path is not None
    result: dict[str, str] = {}
    for raw in config.taxonomy_path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        key = row.get("taxonomy_key") or row.get("nodeid")
        layer = row.get("layer")
        if not key or layer not in LAYERS:
            raise ConfigError(f"invalid taxonomy row: {row!r}")
        result[str(key)] = str(layer)
    return result


def collapse_outcomes(runner: Runner, parsed: Mapping[str, str]) -> dict[str, str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for test_id, outcome in parsed.items():
        grouped[runner.function_of(test_id)].append(outcome)
    collapsed: dict[str, str] = {}
    for test_id, outcomes in grouped.items():
        collapsed[test_id] = "passed" if all(value == "passed" for value in outcomes) else next(
            value for value in outcomes if value != "passed"
        )
    return collapsed


def summarize(
    nodeids: list[str], outcomes: Mapping[str, str], taxonomy: Mapping[str, str]
) -> dict[str, Any]:
    expected = set(nodeids)
    actual = set(taxonomy)
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ConfigError(f"taxonomy does not match denominator; missing={missing}, extra={extra}")

    summary: dict[str, int] = defaultdict(int)
    by_layer: dict[str, dict[str, int]] = {layer: defaultdict(int) for layer in LAYERS}
    cases = []
    for nodeid in nodeids:
        outcome = outcomes.get(nodeid, "not_collected")
        layer = taxonomy[nodeid]
        summary[outcome] += 1
        summary["total"] += 1
        by_layer[layer][outcome] += 1
        by_layer[layer]["total"] += 1
        cases.append(
            {
                "nodeid": nodeid,
                "base_nodeid": nodeid,
                "layer": layer,
                "outcome": outcome,
                "call": {},
            }
        )
    passed = summary.get("passed", 0)
    skipped = summary.get("skipped", 0)
    effective_total = max(1, summary["total"] - skipped)
    return {
        "summary": dict(sorted(summary.items())),
        "pass_rate_excluding_skips": passed / effective_total,
        "by_layer": {
            layer: dict(sorted(counts.items())) for layer, counts in by_layer.items()
        },
        "cases": cases,
    }


def compute_integration_gap(
    cases: list[Mapping[str, Any]], dependencies: Mapping[str, list[str]]
) -> dict[str, Any]:
    atomic = [case for case in cases if case["layer"] == "atomic"]
    non_atomic = [case for case in cases if case["layer"] != "atomic"]
    atomic_rate = sum(case["outcome"] == "passed" for case in atomic) / max(1, len(atomic))
    non_atomic_rate = sum(case["outcome"] == "passed" for case in non_atomic) / max(
        1, len(non_atomic)
    )
    atomic_by_method = {
        str(case["nodeid"]).rsplit("::", 1)[-1]: case["outcome"] == "passed"
        for case in atomic
    }
    eligible = []
    for case in non_atomic:
        method = str(case["nodeid"]).rsplit("::", 1)[-1]
        required = dependencies.get(method, [])
        if required and all(atomic_by_method.get(name, False) for name in required):
            eligible.append(case)
    conditional_rate = (
        sum(case["outcome"] == "passed" for case in eligible) / len(eligible)
        if eligible
        else None
    )
    return {
        "atomic_rate": atomic_rate,
        "non_atomic_rate": non_atomic_rate,
        "raw_gap": atomic_rate - non_atomic_rate,
        "eligible_non_atomic_tests": len(eligible),
        "conditional_non_atomic_rate": conditional_rate,
        "adjusted_gap": atomic_rate - conditional_rate if conditional_rate is not None else None,
        "true_gap_events": [
            case["nodeid"] for case in eligible if case["outcome"] != "passed"
        ],
    }


def validate_reference_lint(config: ScoreConfig) -> None:
    if not config.reference:
        return
    lint = config.task_dir / "filter" / "lint_result.txt"
    if not lint.is_file():
        raise ConfigError(f"reference scoring requires lint result: {lint}")
    first_line = lint.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not first_line or first_line[0].strip() != "LINT_PASS":
        raise ConfigError("reference lint result must begin with LINT_PASS")
    lint_time = lint.stat().st_mtime_ns
    newer_sources = [
        source
        for source in config.oracle_dir.rglob("*.java")
        if source.stat().st_mtime_ns >= lint_time
    ]
    if newer_sources:
        raise ConfigError(
            "reference lint result is stale relative to oracle: "
            + ", ".join(str(path) for path in newer_sources[:5])
        )


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(temporary, path)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in {"target", ".git", "__pycache__"}
        or name.endswith((".pyc", ".pyo"))
    }


def _prepare_scoring(config: ScoreConfig) -> tuple[Path, Path, Path]:
    if config.result_path.exists() and not config.overwrite:
        raise ConfigError(f"result already exists; use --overwrite: {config.result_path}")
    preserved_maven = config.run_dir / ".m2-overwrite-cache"
    if config.scoring_dir.exists():
        if not config.overwrite:
            raise ConfigError(
                f"scoring evidence already exists; use --overwrite: {config.scoring_dir}"
            )
        resolved_scoring = config.scoring_dir.resolve()
        if resolved_scoring.parent != config.run_dir.resolve():
            raise ConfigError("refusing to remove scoring directory outside run directory")
        existing_maven = resolved_scoring / "m2"
        if existing_maven.is_dir():
            if preserved_maven.exists():
                shutil.rmtree(preserved_maven)
            existing_maven.replace(preserved_maven)
        shutil.rmtree(resolved_scoring)
    config.scoring_dir.mkdir(parents=True)
    candidate = config.scoring_dir / "candidate"
    oracle = config.scoring_dir / "oracle"
    maven = config.scoring_dir / "m2"
    if preserved_maven.is_dir():
        preserved_maven.replace(maven)
    shutil.copytree(config.solution_dir, candidate, ignore=_copy_ignore)
    shutil.copytree(config.oracle_dir, oracle, ignore=_copy_ignore)
    return candidate, oracle, maven


def _result_dict(result: CommandResult) -> dict[str, Any]:
    return {
        "command": result.command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": result.timed_out,
    }


def _write_log(scoring: Path, name: str, result: CommandResult) -> str:
    path = scoring / name
    path.write_text(result.stdout + result.stderr, encoding="utf-8")
    return str(path)


def _artifact_path(maven: Path, coordinate: str, version: str) -> Path:
    group, artifact = coordinate.split(":", 1)
    return maven.joinpath(
        "repository", *group.split("."), artifact, version, f"{artifact}-{version}.jar"
    )


def _installed_artifact(maven: Path, coordinate: str, version: str) -> Path:
    if version:
        return _artifact_path(maven, coordinate, version)
    group, artifact = coordinate.split(":", 1)
    artifact_root = maven.joinpath("repository", *group.split("."), artifact)
    candidates = [
        version_dir / f"{artifact}-{version_dir.name}.jar"
        for version_dir in artifact_root.iterdir()
        if version_dir.is_dir()
        and (version_dir / f"{artifact}-{version_dir.name}.jar").is_file()
    ] if artifact_root.is_dir() else []
    return candidates[0] if len(candidates) == 1 else Path()


def _legacy_system_artifact_path(oracle: Path) -> Path | None:
    pom = oracle / "pom.xml"
    root = ET.parse(pom).getroot()
    namespace = {"m": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    findall = lambda path: root.findall(path, namespace) if namespace else root.findall(path)
    find = (
        (lambda parent, tag: parent.find(f"m:{tag}", namespace))
        if namespace
        else (lambda parent, tag: parent.find(tag))
    )
    properties_node = find(root, "properties")
    properties = {
        child.tag.rsplit("}", 1)[-1]: (child.text or "").strip()
        for child in (list(properties_node) if properties_node is not None else [])
    }
    dependencies = findall(".//m:dependency" if namespace else ".//dependency")
    paths: list[Path] = []
    for dependency in dependencies:
        scope = find(dependency, "scope")
        system_path = find(dependency, "systemPath")
        if scope is None or (scope.text or "").strip() != "system" or system_path is None:
            continue
        value = (system_path.text or "").strip()
        for _ in range(len(properties) + 2):
            previous = value
            value = value.replace("${project.basedir}", str(oracle))
            for name, replacement in properties.items():
                value = value.replace(f"${{{name}}}", replacement)
            if value == previous:
                break
        if "${" in value:
            raise ConfigError(f"unresolved oracle systemPath: {value}")
        path = Path(value)
        if not path.is_absolute():
            path = oracle / path
        resolved = path.resolve()
        if not resolved.is_relative_to(oracle.resolve()):
            raise ConfigError(f"oracle systemPath escapes oracle directory: {resolved}")
        paths.append(resolved)
    if len(paths) > 1:
        raise ConfigError("multiple oracle systemPath dependencies are ambiguous")
    return paths[0] if paths else None


def _provenance_payload(text: str) -> list[dict[str, Any]]:
    marker = "__PROVENANCE__"
    for line in text.splitlines():
        if marker in line:
            return json.loads(line.split(marker, 1)[1])
    return []


def score(config: ScoreConfig, executor: DockerExecutor | None = None) -> int:
    validate_reference_lint(config)
    runner = get_runner("java")
    taxonomy = load_effective_taxonomy(config)
    candidate, oracle, maven = _prepare_scoring(config)
    executor = executor or DockerExecutor(config.image)
    executor.seed_maven_repository(maven)

    group, artifact = config.coordinate.split(":", 1)
    target_cache = maven.joinpath("repository", *group.split("."), artifact)
    if target_cache.exists():
        shutil.rmtree(target_cache)

    discovered = {
        suite: runner.discover(oracle, suite) for suite in ("atomic", "integration")
    }
    nodeids = discovered["atomic"] + discovered["integration"]
    if not nodeids:
        raise ConfigError("JavaRunner discovered zero oracle tests")
    summarize(nodeids, {}, taxonomy)  # denominator/taxonomy preflight
    nodeids_path = config.scoring_dir / "nodeids.txt"
    nodeids_path.write_text("\n".join(nodeids) + "\n", encoding="utf-8")
    taxonomy_evidence = config.scoring_dir / "taxonomy.jsonl"
    taxonomy_evidence.write_text(
        "".join(
            json.dumps({"taxonomy_key": key, "layer": taxonomy[key]}) + "\n"
            for key in nodeids
        ),
        encoding="utf-8",
    )

    workspace_mount = Mount(candidate, "/eval/workspace")
    workspace_readonly = Mount(candidate, "/eval/workspace", read_only=True)
    oracle_mount = Mount(oracle, "/eval/oracle")
    maven_mount = Mount(maven, "/root/.m2")
    environment = Env(
        workspace="/eval/workspace",
        oracle="/eval/oracle",
        target_modules=(config.coordinate,),
        workspace_host=candidate,
        oracle_host=oracle,
    )

    platform_result = executor.run("uname -a", [], network=False, timeout=120)
    java_result = executor.run("java -version", [], network=False, timeout=120)
    maven_result = executor.run("mvn --version", [], network=False, timeout=120)
    _write_log(config.scoring_dir, "platform.txt", platform_result)
    _write_log(config.scoring_dir, "java-version.log", java_result)
    _write_log(config.scoring_dir, "maven-version.log", maven_result)
    if any(
        result.returncode != 0
        for result in (platform_result, java_result, maven_result)
    ):
        raise ConfigError("Java scorer image toolchain preflight failed")

    setup_steps = list(runner.setup(environment))
    if len(setup_steps) < 4:
        raise ConfigError("JavaRunner setup contract must provide four ordered steps")
    setup_results: list[CommandResult] = [maven_result]
    candidate_install = executor.run(
        setup_steps[1].command,
        [workspace_mount, maven_mount],
        network=True,
        timeout=setup_steps[1].timeout,
    )
    setup_results.append(candidate_install)
    _write_log(config.scoring_dir, "candidate-install.log", candidate_install)

    outcomes: dict[str, str] = {}
    grouped_results: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []
    valid = True
    installed_hash: str | None = None
    resolved_hash: str | None = None
    resolved_path: str | None = None
    provenance_status = "not_run"

    if candidate_install.returncode != 0:
        outcomes = {nodeid: "build_error" for nodeid in nodeids}
        provenance_status = "not_run_candidate_build_failed"
        warnings.append("candidate Maven install failed; scored as candidate failure")
    else:
        version_probe = executor.run(
            setup_steps[2].command,
            [workspace_readonly, oracle_mount],
            network=False,
            timeout=setup_steps[2].timeout,
        )
        setup_results.append(version_probe)
        _write_log(config.scoring_dir, "candidate-version.log", version_probe)
        if version_probe.returncode != 0:
            valid = False
            errors.append("candidate version probe failed")
        version_file = oracle / ".candidate-version"
        version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else ""
        artifact_path = _installed_artifact(maven, config.coordinate, version)
        installed_hash = sha256_file(artifact_path)
        system_artifact_path = _legacy_system_artifact_path(oracle)
        if not installed_hash:
            valid = False
            errors.append("candidate artifact was not installed at the declared coordinate")
        elif system_artifact_path:
            system_artifact_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(artifact_path, system_artifact_path)

        if valid:
            oracle_compile = executor.run(
                setup_steps[3].command,
                [oracle_mount, maven_mount],
                network=True,
                timeout=setup_steps[3].timeout,
            )
            setup_results.append(oracle_compile)
            _write_log(config.scoring_dir, "oracle-test-compile.log", oracle_compile)
            after_compile_hash = sha256_file(artifact_path)
            if after_compile_hash != installed_hash:
                valid = False
                errors.append("oracle setup replaced the candidate artifact")
            elif system_artifact_path and sha256_file(system_artifact_path) != installed_hash:
                valid = False
                errors.append("oracle setup replaced the candidate systemPath artifact")
            elif oracle_compile.returncode != 0:
                diagnostics = oracle_compile.stdout + oracle_compile.stderr
                dependency_failure = any(
                    marker in diagnostics
                    for marker in ("DependencyResolutionException", "PluginResolutionException", "Could not resolve")
                )
                if dependency_failure:
                    valid = False
                    errors.append("oracle dependency or plugin resolution failed")
                else:
                    outcomes = {nodeid: "collection_error" for nodeid in nodeids}
                    warnings.append("oracle testCompile failed against candidate API")

        raw_dir = config.scoring_dir / "raw-surefire"
        raw_dir.mkdir()
        if valid and not outcomes:
            for suite in ("atomic", "integration"):
                tests = discovered[suite]
                for offset in range(0, len(tests), config.batch_size):
                    selected = tests[offset : offset + config.batch_size]
                    batch = runner.batch(suite, selected, offset, config.timeout)
                    result = executor.run(
                        batch.command,
                        [oracle_mount, maven_mount],
                        network=False,
                        timeout=config.timeout + 60,
                    )
                    parsed = runner.outcomes("", result.stdout)
                    normalized = collapse_outcomes(runner, parsed) if parsed is not None else None
                    current = (
                        {test: "timeout" if result.timed_out else "no_report" for test in selected}
                        if normalized is None
                        else {test: normalized.get(test, "not_collected") for test in selected}
                    )
                    outcomes.update(current)
                    stem = f"{suite}-{offset:03d}"
                    log_path = _write_log(config.scoring_dir, f"batch-{stem}.log", result)
                    reports = []
                    report_dir = oracle / "target" / "surefire-reports"
                    if report_dir.is_dir():
                        for source in sorted(report_dir.glob("TEST-*.xml")):
                            destination = raw_dir / f"{stem}-{source.name}"
                            shutil.copy2(source, destination)
                            reports.append(str(destination))
                    grouped_results[stem] = {
                        **_result_dict(result),
                        "json_report": {
                            "tests": [
                                {"nodeid": test, "outcome": current[test]} for test in selected
                            ]
                        },
                        "surefire_reports": reports,
                        "raw_log": log_path,
                    }

        if valid:
            provenance_command = runner.provenance(environment)
            if provenance_command:
                provenance_result = executor.run(
                    provenance_command,
                    [oracle_mount, maven_mount, workspace_readonly],
                    network=False,
                    timeout=300,
                )
                _write_log(config.scoring_dir, "provenance.log", provenance_result)
                rows = _provenance_payload(provenance_result.stdout)
                matching = next(
                    (row for row in rows if row.get("name") == config.coordinate), None
                )
                if matching and matching.get("paths"):
                    resolved_path = str(matching["paths"][0])
                    prefix = "/root/.m2/"
                    resolved_host = (
                        maven / resolved_path.removeprefix(prefix)
                        if resolved_path.startswith(prefix)
                        else (
                            oracle / resolved_path.removeprefix("/eval/oracle/")
                            if resolved_path.startswith("/eval/oracle/")
                            else Path()
                        )
                    )
                    resolved_hash = sha256_file(resolved_host)
                provenance_ok = bool(
                    provenance_result.returncode == 0
                    and matching
                    and matching.get("direct_urls")
                    and installed_hash
                    and resolved_hash == installed_hash
                )
                provenance_status = "passed" if provenance_ok else "failed"
                if not provenance_ok:
                    valid = False
                    errors.append("candidate artifact provenance failed")

    summary = summarize(nodeids, outcomes, taxonomy)
    gap = compute_integration_gap(summary["cases"], runner.dependencies(oracle))
    payload = {
        "valid": valid,
        "platform": platform_result.stdout.strip(),
        "host_platform": host_platform.platform(),
        "java_version": (java_result.stdout + java_result.stderr).strip().splitlines()[0],
        "maven_version": maven_result.stdout.strip().splitlines()[0],
        "timeout_seconds": config.timeout,
        "remove_coordinates": [config.coordinate],
        "source_repo": config.source_repo,
        "solution_dir": str(config.solution_dir),
        "oracle_dir": str(oracle),
        "nodeids": str(nodeids_path),
        "taxonomy": str(taxonomy_evidence),
        "run_dir": str(config.run_dir),
        "grouped_results": grouped_results,
        **summary,
        "provenance": {
            "status": provenance_status,
            "coordinate": config.coordinate,
            "resolved_path": resolved_path,
            "candidate_sha256": installed_hash,
            "resolved_sha256": resolved_hash,
        },
        "integration_gap": gap,
        "setup_results": [_result_dict(result) for result in setup_results],
        "errors": errors,
        "warnings": warnings,
    }
    atomic_write_json(config.result_path, payload)
    if not valid:
        return 2
    if config.reference and summary["pass_rate_excluding_skips"] != 1.0:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score a Java task candidate with JavaRunner in Docker"
    )
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--solution-dir", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--oracle-dir", type=Path)
    parser.add_argument("--taxonomy", type=Path)
    parser.add_argument("--maven-coordinate")
    parser.add_argument("--image", default="spec2repo-java:latest")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--reference", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        config = resolve_config(build_parser().parse_args(argv))
        return score(config)
    except ConfigError as error:
        print(f"JAVA_SCORE_INVALID: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
