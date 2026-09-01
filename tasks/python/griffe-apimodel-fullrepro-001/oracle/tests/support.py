from __future__ import annotations

import json
from pathlib import Path
import subprocess

from griffe import Module, visit


def write_package(root: Path, name: str, files: dict[str, str]) -> Path:
    package = root / name
    package.mkdir(parents=True, exist_ok=True)
    for relative, content in files.items():
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    return package


def visit_code(code: str, *, name: str = "api", root: Path | None = None) -> Module:
    filepath = (root or Path.cwd()) / f"{name}.py"
    return visit(name, filepath=filepath, code=code)


def semantic_graph(module: Module) -> dict:
    return json.loads(module.as_json(full=False, sort_keys=True))


def init_git_repository(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "gate@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Gate"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
