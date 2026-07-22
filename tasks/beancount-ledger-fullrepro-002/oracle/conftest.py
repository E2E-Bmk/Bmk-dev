"""Shared helpers for Beancount oracle tests."""
from __future__ import annotations

import textwrap
from pathlib import Path


def write_ledger(tmp_path: Path, name: str, contents: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")
    return path
