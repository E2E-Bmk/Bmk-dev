from __future__ import annotations

from pathlib import Path
from typing import Any

from griffe import (
    AnalysisWorkspace,
    Attribute,
    Extension,
    SnapshotStore,
)

from .support import write_package


def package_source(root: Path, name: str, body: str, **extra: str) -> Path:
    files = {"__init__.py": body}
    files.update(extra)
    return write_package(root, name, files)


def admit(
    root: Path,
    name: str = "contract_api",
    body: str = "def call(value=1):\n    return value\n",
    *,
    operation: str = "admit-1",
) -> tuple[Any, Any, Path]:
    source = package_source(root / "source", name, body)
    workspace = AnalysisWorkspace(root / "workspace")
    revision = workspace.admit(name, source, operation_id=operation)
    return workspace, revision, source


def admit_snapshot(
    root: Path,
    name: str = "contract_api",
    body: str = "def call(value=1):\n    return value\n",
    *,
    operation: str = "admit-1",
) -> tuple[Any, Any, Any, Any, Path]:
    workspace, revision, source = admit(root, name, body, operation=operation)
    store = SnapshotStore(root / "snapshots")
    snapshot = store.prepare(revision, workspace.open(revision), operation_id=f"snapshot:{operation}")
    store.promote(snapshot, owner_token=revision.owner_token)
    return workspace, revision, store, snapshot, source


def second_revision(
    workspace: Any,
    source: Path,
    name: str,
    body: str,
    *,
    operation: str = "admit-2",
) -> Any:
    (source / "__init__.py").write_text(body, encoding="utf-8", newline="\n")
    return workspace.admit(name, source, operation_id=operation)


class AddMarker(Extension):
    def __init__(self, name: str = "marker", value: str = "2"):
        super().__init__()
        self.name = name
        self.value = value

    def on_package(self, *, pkg, loader, **kwargs) -> None:
        pkg[self.name] = Attribute(self.name, value=self.value, lineno=1, endlineno=1)


class RemoveCall(Extension):
    def on_package(self, *, pkg, loader, **kwargs) -> None:
        del pkg.members["call"]


class FailAfterMarker(Extension):
    def on_package(self, *, pkg, loader, **kwargs) -> None:
        pkg["transient"] = Attribute("transient", value="9", lineno=1, endlineno=1)
        raise RuntimeError("extension failed")
