"""Restart recovery classification and repair."""

from __future__ import annotations


def recovery_report(store, now: str) -> dict:
    """Classify recoverable state without hiding history."""
    raise NotImplementedError


def recover(store, now: str) -> dict:
    """Apply public recovery actions and return a report."""
    raise NotImplementedError
