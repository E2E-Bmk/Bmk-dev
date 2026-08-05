from __future__ import annotations

import contextlib
import io
import json
from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class FireObservation:
    result: object
    stdout: str
    stderr: str
    exit_code: int | None


class Widget:
    category = "instrument"

    def __init__(self, name: str = "seed", size: int = 2):
        self.name = name
        self.size = size

    @property
    def high_score(self) -> int:
        return self.size * 10

    @property
    def score_card(self) -> dict[str, object]:
        return {"name": self.name, "score": self.high_score}

    def greet(self, punctuation: str = "!") -> str:
        return f"{self.name}{punctuation}"

    def combine(self, left: str, right: str = "tail") -> str:
        return f"{self.name}:{left}:{right}"

    def __call__(self, value: str = "x") -> str:
        return f"{self.name}:{value}"


class PlainRecord:
    def __init__(self, name: str = "record", size: int = 1):
        self.name = name
        self.size = size

    @property
    def high_score(self) -> int:
        return self.size * 10


def double(value=0):
    return 2 * value


def typed_values(a: int, b: float, flag=False, none=None):
    return {"a": a, "b": b, "flag": flag, "none": none}


def display(arg1, arg2="!"):
    return arg1 + arg2


def collect(*items):
    return "|".join(items)


def choose(value):
    return value


def pair(left, right="R"):
    return (left, right)


def make_widget(name="made", size=5):
    return Widget(name=name, size=size)


def table():
    return [
        {"name": "Ada", "score": 8},
        {"name": "Lin", "score": 13},
    ]


def stable_serializer(value):
    if isinstance(value, Widget):
        return f"Widget<{value.name}:{value.size}>"
    return json.dumps(value, sort_keys=True)


@pytest.fixture
def cli_component():
    return {
        "double": double,
        "typed": typed_values,
        "display": display,
        "collect": collect,
        "choose": choose,
        "pair": pair,
        "maker": make_widget,
        "widget": Widget,
        "record": PlainRecord,
        "instance": Widget("ready", 4),
        "data": {
            "alpha": [3, {"nested-key": "value"}],
            "spaced key": "space value",
            "numbers": (5, 8, 13),
        },
        "table": table,
    }


@pytest.fixture
def run_fire():
    def invoke(component, command=None, name="tool", serialize=None):
        import fire

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                result = fire.Fire(
                    component,
                    command=command,
                    name=name,
                    serialize=serialize,
                )
            except SystemExit as exc:
                return FireObservation(None, stdout.getvalue(), stderr.getvalue(), exc.code)
        return FireObservation(result, stdout.getvalue(), stderr.getvalue(), None)

    return invoke


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public atomic dependency metadata")
