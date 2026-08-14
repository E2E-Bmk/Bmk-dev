#!/usr/bin/env python3
"""Build Docker images for Spec2Repo evaluation.

Image kinds:
  spec2repo-base:latest           python:3.11-slim + pytest toolchain
  spec2repo-agent-<task>:latest   base + task oracle requirements, target
                                  package removed - what the AGENT sees
  spec2repo-<task>:latest         optional scorer image with oracle baked in
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKER_DIR = REPO_ROOT / "docker"
ORACLE_DIR = REPO_ROOT / "oracle"

sys.path.insert(0, str(REPO_ROOT))
# single source of truth for target imports / reference distributions
from harness.sandbox import (
    TARGET_IMPORTS,
    REFERENCE_DISTRIBUTIONS,
    TOOLCHAIN_COUPLED,
)

BASE_IMAGE = "spec2repo-base:latest"


def build_base():
    """Build the base Docker image."""
    print(f"Building base image: {BASE_IMAGE}")
    subprocess.run(
        ["docker", "build", "-t", BASE_IMAGE, "-f", str(DOCKER_DIR / "Dockerfile.base"), str(DOCKER_DIR)],
        check=True,
    )
    print(f"Base image built: {BASE_IMAGE}")


def build_task(task_id: str):
    """Build a task-specific Docker image."""
    oracle_path = ORACLE_DIR / task_id
    if not oracle_path.exists():
        print(f"WARNING: No oracle directory for {task_id}, skipping")
        return

    image_tag = f"spec2repo-{task_id}:latest"
    print(f"Building task image: {image_tag}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shutil.copytree(oracle_path, tmp / "oracle")
        shutil.copy(DOCKER_DIR / "Dockerfile.task.template", tmp / "Dockerfile")
        
        # Replace template reference
        dockerfile = tmp / "Dockerfile"
        content = dockerfile.read_text()
        content = content.replace("ARG BASE_IMAGE=spec2repo-base:latest", f"ARG BASE_IMAGE={BASE_IMAGE}")
        dockerfile.write_text(content)

        subprocess.run(
            ["docker", "build", "-t", image_tag, str(tmp)],
            check=True,
        )
    print(f"Task image built: {image_tag}")


def agent_requirements(task_id: str) -> list[str]:
    """Oracle requirements minus lines that name the target package itself."""
    req_path = ORACLE_DIR / task_id / "requirements.txt"
    if not req_path.exists():
        return []
    target_names = set()
    for imp in TARGET_IMPORTS.get(task_id, []):
        target_names.add(imp.lower().replace("_", "-"))
    # instance-id stem is usually the distribution name (e.g. vcrpy, dbt-core)
    stem = task_id.rsplit("-fullrepro-", 1)[0]
    target_names.add(stem.lower())
    lines = []
    for raw in req_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pkg = (
            line.split(";")[0].split("==")[0].split(">=")[0].split("<=")[0]
            .split("<")[0].split(">")[0].split("[")[0].split("~=")[0]
            .strip().lower().replace("_", "-")
        )
        if pkg in target_names:
            continue
        lines.append(line)
    return lines


def agent_image_tag(task_id: str) -> str:
    return f"spec2repo-agent-{task_id}:latest"


def build_agent_image(task_id: str) -> str:
    """Build the per-task AGENT image. Returns the image tag to use
    (falls back to the base image for pure-stdlib tasks)."""
    reqs = agent_requirements(task_id)
    if not reqs:
        print(f"{task_id}: no third-party test deps - agent uses {BASE_IMAGE}")
        return BASE_IMAGE

    tag = agent_image_tag(task_id)
    strip_parts = []
    ref_dists = REFERENCE_DISTRIBUTIONS.get(task_id, [])
    if ref_dists:
        strip_parts.append("--dists " + " ".join(ref_dists))
    # toolchain-coupled targets (pytest -> packaging) cannot be removed from
    # any Python environment; skip the resolve check for them
    verify_imports = [] if task_id in TOOLCHAIN_COUPLED else TARGET_IMPORTS.get(task_id, [])
    strip_parts.append("-- " + " ".join(verify_imports) if verify_imports else "--")
    strip_args = " ".join(strip_parts)
    print(f"Building agent image: {tag} (deps={len(reqs)}, strip='{strip_args}')")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "requirements.txt").write_text("\n".join(reqs) + "\n", encoding="utf-8")
        shutil.copy(DOCKER_DIR / "uninstall_targets.py", tmp / "uninstall_targets.py")
        shutil.copy(DOCKER_DIR / "Dockerfile.agent.template", tmp / "Dockerfile")
        subprocess.run(
            ["docker", "build", "-t", tag,
             "--build-arg", f"BASE_IMAGE={BASE_IMAGE}",
             "--build-arg", f"STRIP_ARGS={strip_args}",
             str(tmp)],
            check=True,
        )
    print(f"Agent image built: {tag}")
    return tag


def main():
    parser = argparse.ArgumentParser(description="Build Spec2Repo Docker images")
    parser.add_argument("--task", help="Build only a specific task image")
    parser.add_argument("--all-task-images", action="store_true",
                        help="Build optional scorer images containing each oracle")
    parser.add_argument("--agent-images", action="store_true",
                        help="Build per-task agent images (oracle deps, target stripped)")
    parser.add_argument("--skip-base", action="store_true", help="Skip building base image")
    args = parser.parse_args()

    if not args.skip_base:
        build_base()

    if args.agent_images:
        task_ids = [args.task] if args.task else sorted(
            d.name for d in ORACLE_DIR.iterdir() if d.is_dir())
        print(f"Building agent images for {len(task_ids)} tasks...")
        failures = []
        for task_id in task_ids:
            try:
                build_agent_image(task_id)
            except subprocess.CalledProcessError as e:
                failures.append(task_id)
                print(f"FAILED: {task_id}: {e}")
        if failures:
            print(f"\nAgent image failures ({len(failures)}): {failures}")
            sys.exit(1)
    elif args.task:
        build_task(args.task)
    elif args.all_task_images:
        task_ids = sorted(d.name for d in ORACLE_DIR.iterdir() if d.is_dir())
        print(f"Building images for {len(task_ids)} tasks...")
        for task_id in task_ids:
            build_task(task_id)

    print("Done.")


if __name__ == "__main__":
    main()
