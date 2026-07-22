"""Shared helpers for prompt_toolkit oracle tests."""
from __future__ import annotations

import os
from contextlib import contextmanager

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.output import DummyOutput


def _document_fixture() -> Document:
    return Document(
        "line 1\n" + "line 2\n" + "line 3\n" + "line 4\n", len("line 1\n" + "lin")
    )


@contextmanager
def _chdir(directory):
    old = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(old)


def _write_test_files(test_dir, names=None):
    for name in names or range(10):
        (test_dir / str(name)).write_bytes(b"")


async def _load_history(history):
    result = []
    async for item in history.load():
        result.append(item)
    return result


class _Capture:
    def __init__(self):
        self._data = []

    def write(self, data):
        self._data.append(data)

    @property
    def data(self):
        return "".join(self._data)

    def flush(self):
        pass

    def isatty(self):
        return True

    def fileno(self):
        return -1


class CaptureOutput(DummyOutput):
    def __init__(self):
        self.data: list[str] = []

    def write(self, data: str) -> None:
        self.data.append(data)

    def write_raw(self, data: str) -> None:
        self.data.append(data)

    def flush(self) -> None:
        pass


class SmallCompleter(Completer):
    def get_completions(self, document, complete_event):
        yield Completion("abc", start_position=-1)
        yield Completion("ax", start_position=-1)


class FormattedObject:
    def __pt_formatted_text__(self):
        return [("class:object", "OBJ")]
