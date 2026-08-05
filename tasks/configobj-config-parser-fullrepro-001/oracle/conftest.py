from __future__ import annotations

from pathlib import Path

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): integration workflows depend on atomic contracts",
    )


def as_plain(value):
    if isinstance(value, dict):
        return {key: as_plain(value[key]) for key in value}
    if isinstance(value, list):
        return [as_plain(item) for item in value]
    if isinstance(value, tuple):
        return tuple(as_plain(item) for item in value)
    return value


def make_config(lines, **options):
    from configobj import ConfigObj

    return ConfigObj(lines, **options)


def make_config_with_spec(values, spec, **options):
    from configobj import ConfigObj

    return ConfigObj(values, configspec=spec, **options)


def basic_lines():
    return [
        "# application settings",
        "name = example",
        "ports = 8000, 8001, 8002",
        "[service]",
        "enabled = yes",
        "[[limits]]",
        "low = 1",
        "high = 5",
    ]


def validation_spec():
    return [
        "port = integer(1, 65535, default=8080)",
        "enabled = boolean(default=True)",
        "mode = option('safe', 'fast', default='safe')",
        "labels = string_list(default=list('one', 'two'))",
        "[database]",
        "host = string(default='localhost')",
        "retries = integer(0, 5, default=2)",
    ]


@pytest.fixture
def parsed_config():
    return make_config(basic_lines())


@pytest.fixture
def validation_config():
    return make_config_with_spec(
        ["port = 9000", "[database]", "retries = 1"],
        validation_spec(),
    )


@pytest.fixture
def local_config_lines():
    return [
        "# header",
        "title = Demo",
        "items = one, two, three",
        "[server] # server settings",
        "# host comment",
        "host = localhost # inline host",
        "port = 8080",
        "[[tls]]",
        "enabled = yes",
    ]


def write_config(path: Path, lines, encoding="utf-8"):
    path.write_text("\n".join(lines) + "\n", encoding=encoding)
    return path
