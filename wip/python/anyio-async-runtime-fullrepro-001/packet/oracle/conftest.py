"""Shared fixtures, helpers, and constants for anyio oracle tests."""
from __future__ import annotations

import pytest

import anyio
from anyio import (
    BrokenResourceError,
    BusyResourceError,
    CapacityLimiter,
    ClosedResourceError,
    Condition,
    EndOfStream,
    Event,
    IncompleteRead,
    Lock,
    NoEventLoopError,
    ResourceGuard,
    Semaphore,
    WouldBlock,
    create_memory_object_stream,
    create_task_group,
    current_effective_deadline,
    current_time,
    fail_after,
    move_on_after,
    open_file,
    run,
    sleep,
    sleep_until,
    to_thread,
    wait_all_tasks_blocked,
    wrap_file,
)
from anyio.abc import TaskStatus
from anyio.functools import cache, lru_cache, reduce
from anyio.lowlevel import RunVar, checkpoint, current_token
from anyio.streams.buffered import BufferedByteReceiveStream
from anyio.streams.stapled import StapledObjectStream
from anyio.streams.text import TextReceiveStream, TextSendStream
from anyio import Path as AsyncPath
