from __future__ import annotations

from dataclasses import dataclass

import pytest

from deepdiff import DeepDiff


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): document atomic coverage dependencies")


@dataclass
class Box:
    name: str
    value: int


def diff_dict(left, right, **kwargs):
    return DeepDiff(left, right, **kwargs).to_dict()


def changed_paths(result, category):
    return set(result.get(category, {}))


def apply_delta(left, right, **kwargs):
    from deepdiff import Delta

    return Delta(DeepDiff(left, right, **kwargs)) + left
