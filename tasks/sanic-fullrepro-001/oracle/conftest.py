from __future__ import annotations

import asyncio
import warnings
from pathlib import Path

import pytest

from sanic import Sanic


warnings.filterwarnings(
    "ignore",
    message=r"websockets\.legacy is deprecated.*",
    category=DeprecationWarning,
)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): integration tests depend on physical atomic contracts",
    )


def make_app(name: str) -> Sanic:
    app = Sanic(name, configure_logging=False)
    app.config.USE_UVLOOP = False
    return app


def run_asgi(app: Sanic, method: str, path: str, **kwargs):
    async def invoke():
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"websockets\.legacy is deprecated.*",
                category=DeprecationWarning,
            )
            client = getattr(app.asgi_client, method)
        return await client(path, **kwargs)

    return asyncio.run(invoke())


def write_text(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path
