# Spec2Repo oracle shared fixtures for mashumaro-fullrepro-001
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from typing import NamedTuple

import pytest

from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig
from mashumaro.types import SerializationStrategy


class Tone(Enum):
    calm = "calm"
    bright = "bright"


class Priority(IntEnum):
    low = 1
    high = 9


class Point(NamedTuple):
    x: int
    y: int


class DecimalAsCents(SerializationStrategy):
    def serialize(self, value: Decimal) -> int:
        return int(value * 100)

    def deserialize(self, value: int) -> Decimal:
        return Decimal(value) / 100


class DateAsCompactString(SerializationStrategy):
    def serialize(self, value: date) -> str:
        return value.strftime("%Y%m%d")

    def deserialize(self, value: str) -> date:
        return datetime.strptime(value, "%Y%m%d").date()


class EnumNameStrategy(SerializationStrategy, match_subclasses=True):
    def serialize(self, value: Enum) -> str:
        return value.name

    def deserialize(self, value: str) -> Enum:
        return Tone[value]


class Coordinate:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Coordinate) and (self.x, self.y) == (
            other.x,
            other.y,
        )


class SerializableCoordinate(SerializationStrategy):
    def serialize(self, value: Coordinate) -> list[int]:
        return [value.x, value.y]

    def deserialize(self, value: list[int]) -> Coordinate:
        return Coordinate(value[0], value[1])


class DateBox:
    def __init__(self, value: date):
        self.value = value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DateBox) and self.value == other.value


class DateBoxStrategy(SerializationStrategy, use_annotations=True):
    def serialize(self, value: DateBox) -> date:
        return value.value

    def deserialize(self, value: date) -> DateBox:
        return DateBox(value)


@dataclass
class Leaf(DataClassDictMixin):
    code: str
    count: int


@dataclass
class PrimitiveBox(DataClassDictMixin):
    flag: bool
    total: int
    label: str


@dataclass
class User:
    id: object
    name: str


@dataclass
class Metric:
    score: object


@dataclass
class Account:
    id: object


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "depends_on(*names): declares logical atomic dependencies")


@dataclass
class NestedBox(DataClassDictMixin):
    leaf: Leaf
    tags: list[str]


@pytest.fixture
def leaf() -> Leaf:
    return Leaf("cedar", 7)
