"""Shared fixtures, helpers, and constants for curio oracle tests."""
import pytest

from curio import Event, run, sleep, spawn


async def async_value(value):
    """Return a value from a coroutine."""
    return value


async def async_failure():
    """Raise a ValueError from a coroutine."""
    raise ValueError("child failure")


async def wait_for_event(event):
    """Wait for an event and return a sentinel."""
    await event.wait()
    return "released"
