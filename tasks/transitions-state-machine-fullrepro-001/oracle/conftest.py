"""Shared fixtures, helpers, and constants for transitions oracle tests."""
from __future__ import annotations

import asyncio
import importlib

import pytest

from transitions import Machine, MachineError, State, Transition


def make_model(**attrs):
    """Create a minimal fresh model object with optional preset attributes."""
    obj = type("Obj", (), {})()
    for k, v in attrs.items():
        setattr(obj, k, v)
    return obj


def run_async(coro):
    """Execute an async coroutine to completion and return its result."""
    return asyncio.run(coro)


@pytest.fixture
def fresh_model():
    """Provide a clean model object for each test."""
    return make_model()


HAS_GRAPH_BACKEND = (
    importlib.util.find_spec("pygraphviz") is not None
    or importlib.util.find_spec("graphviz") is not None
)
