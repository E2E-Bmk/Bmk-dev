from __future__ import annotations

from dataclasses import dataclass, field

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): public integration behavior dependencies",
    )


@dataclass
class Address:
    city: str
    postal_code: int


@dataclass
class User:
    user_id: int
    name: str
    active: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass
class UserWithAddress:
    user: User
    address: Address


@dataclass
class Defaults:
    count: int = 0
    note: str | None = None


def make_user_data() -> dict:
    return {
        "user_id": 17,
        "name": "Nia",
        "active": False,
        "tags": ["green", "edge"],
    }


@pytest.fixture
def user_data() -> dict:
    return make_user_data()


@pytest.fixture
def user() -> User:
    return User(17, "Nia", False, ["green", "edge"])


@pytest.fixture
def nested_data() -> dict:
    return {
        "user": make_user_data(),
        "address": {"city": "Oslo", "postal_code": 4481},
    }
