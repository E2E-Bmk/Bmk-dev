"""Shared helpers and fixtures for griffe oracle tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from textwrap import dedent

from griffe import (
    DataclassesExtension,
    Extension,
    Module,
    load,
    load_extensions,
    visit,
)


def write_package(root: Path, name: str, files: dict[str, str]) -> Path:
    """Create a package directory with the given source files."""
    package = root / name
    package.mkdir()
    for relative, content in files.items():
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return package


def init_git_repository(repository: Path) -> None:
    """Initialize a minimal git repository with one commit."""
    commands = (
        ["git", "init"],
        ["git", "config", "user.email", "track-b@example.invalid"],
        ["git", "config", "user.name", "Track B"],
        ["git", "add", "."],
        ["git", "commit", "-m", "initial"],
    )
    for command in commands:
        subprocess.run(
            command, cwd=repository, check=True, capture_output=True, text=True
        )


class AddMarker(Extension):
    """Test extension that renames attribute 'x' to 'added' with value '7'."""

    def on_package(self, *, pkg, loader, **kwargs):
        added = pkg["x"]
        added.name = "added"
        added.value = "7"
        pkg.set_member("added", added)
        del pkg["x"]


def _visit(
    code: str, *, name: str = "module", extensions=None, docstring_parser=None
) -> Module:
    """Statically analyze a code snippet and return the Module."""
    return visit(
        name,
        Path(f"{name}.py"),
        dedent(code),
        extensions=extensions,
        docstring_parser=docstring_parser,
    )


def _load_package(
    tmp_path: Path, code: str, *, extensions=None, docstring_parser=None
) -> Module:
    """Create a temporary package and load it."""
    package = tmp_path / "pkg"
    package.mkdir()
    package.joinpath("__init__.py").write_text(dedent(code), encoding="utf-8")
    return load(
        "pkg",
        search_paths=[tmp_path],
        extensions=extensions,
        docstring_parser=docstring_parser,
    )


def _dataclass_module(tmp_path: Path, code: str) -> Module:
    """Create and load a package with DataclassesExtension enabled."""
    return _load_package(
        tmp_path, code, extensions=load_extensions(DataclassesExtension())
    )
