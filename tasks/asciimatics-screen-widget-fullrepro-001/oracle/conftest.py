from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest


class RecordingScreen:
    """Small local screen double for public effect and Canvas calls."""

    width = 40
    height = 12
    colours = 8
    unicode_aware = False
    start_line = 0

    def __init__(self, width=40, height=12):
        self.width = width
        self.height = height
        self.calls = []

    @property
    def dimensions(self):
        return self.height, self.width

    def is_visible(self, x, y):
        return 0 <= x < self.width and self.start_line <= y < self.start_line + self.height

    def print_at(self, text, x, y, colour=7, attr=0, bg=0, transparent=False):
        self.calls.append(("print_at", text, x, y, colour, attr, bg, transparent))

    def clear_buffer(self, fg, attr, bg, x=0, y=0, w=None, h=None):
        self.calls.append(("clear_buffer", fg, attr, bg, x, y, w, h))

    def paint(self, text, x, y, colour=7, attr=0, bg=0, transparent=False, colour_map=None):
        self.calls.append(("paint", text, x, y, colour, attr, bg, transparent, colour_map))

    def centre(self, text, y, colour=7, attr=0, colour_map=None):
        self.calls.append(("centre", text, y, colour, attr, colour_map))

    def scroll(self, lines=1):
        self.calls.append(("scroll", lines))

    def highlight(self, x, y, w, h, fg=None, bg=None, blend=100):
        self.calls.append(("highlight", x, y, w, h, fg, bg, blend))

    def block_transfer(self, buffer, x, y):
        self.calls.append(("block_transfer", x, y, buffer.width, buffer.height))


class SpyEffect:
    def __init__(self, screen=None, stop_frame=4, swallow=False):
        self._screen = screen
        self._stop_frame = stop_frame
        self._scene = None
        self._delete_count = None
        self.swallow = swallow
        self.reset_count = 0
        self.update_frames = []
        self.events = []
        self.saved = 0

    @property
    def stop_frame(self):
        return self._stop_frame

    @property
    def screen(self):
        return self._screen

    @property
    def scene(self):
        return self._scene

    @property
    def delete_count(self):
        return self._delete_count

    @delete_count.setter
    def delete_count(self, value):
        self._delete_count = value

    @property
    def frame_update_count(self):
        return 1

    @property
    def safe_to_default_unhandled_input(self):
        return True

    def register_scene(self, scene):
        self._scene = scene

    def update(self, frame_no):
        if frame_no >= 0 and (self._stop_frame == 0 or frame_no < self._stop_frame):
            self._update(frame_no)

    def reset(self):
        self.reset_count += 1

    def _update(self, frame_no):
        self.update_frames.append(frame_no)

    def process_event(self, event):
        self.events.append(event)
        return None if self.swallow else event

    def save(self):
        self.saved += 1


@pytest.fixture
def screen():
    return RecordingScreen()


@pytest.fixture
def canvas(screen):
    from asciimatics.screen import Canvas

    return Canvas(screen, 10, 30, 2, 1)


@pytest.fixture
def simple_frame(screen):
    from asciimatics.widgets import Frame, Layout

    frame = Frame(screen, 10, 30, has_border=False, can_scroll=False)
    layout = Layout([1], fill_frame=True)
    frame.add_layout(layout)
    return frame, layout


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the asciimatics package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic public behaviors used by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return
    target_root = Path(configured_root).resolve()
    for name in list(sys.modules):
        if name == "asciimatics" or name.startswith("asciimatics."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))
