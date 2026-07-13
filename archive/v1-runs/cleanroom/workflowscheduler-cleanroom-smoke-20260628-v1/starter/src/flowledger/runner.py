"""Deterministic fake action runner."""

from __future__ import annotations


def run_action(action: str, with_args: dict, now: str) -> dict:
    """Run public fake actions: ok, fail, emit, wait."""
    raise NotImplementedError
