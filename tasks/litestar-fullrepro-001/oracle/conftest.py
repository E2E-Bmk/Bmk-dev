from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import warnings

import pytest
from litestar.exceptions import LitestarDeprecationWarning


def pytest_configure(config: pytest.Config) -> None:
    warnings.filterwarnings("ignore", category=LitestarDeprecationWarning)
    config.addinivalue_line(
        "filterwarnings",
        "ignore::litestar.exceptions.LitestarDeprecationWarning",
    )
    config.addinivalue_line(
        "markers",
        "depends_on(*names): integration tests depend on public atomic contracts",
    )


@dataclass
class Item:
    name: str
    quantity: int


def body(response: Any) -> Any:
    return response.json()


def content_type(response: Any) -> str:
    return response.headers.get("content-type", "").split(";", 1)[0]


__all__ = ("Item", "body", "content_type")
