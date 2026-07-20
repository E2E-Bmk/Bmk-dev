"""Public-API rewrites of the covered upstream Quart behaviors.

Each test constructs its application through ``Quart`` and exercises it through
documented contexts or the in-process client.  This file deliberately has no
dependency on Quart's source-tree test fixtures or implementation modules.
"""

from __future__ import annotations

import asyncio

import pytest

from quart import (
    Quart,
    Response,
    abort,
    copy_current_app_context,
    copy_current_request_context,
    copy_current_websocket_context,
    g,
    has_app_context,
    has_request_context,
    has_websocket_context,
    jsonify,
    render_template_string,
    request,
    session,
    stream_template_string,
    websocket,
)
from quart.testing import WebsocketResponseError

import pytest

from quart import (
    Blueprint,
    Quart,
    abort,
    current_app,
    flash,
    get_flashed_messages,
    g,
    has_app_context,
    has_request_context,
    has_websocket_context,
    jsonify,
    make_response,
    render_template_string,
    request,
    session,
    stream_with_context,
    url_for,
    websocket,
)
from quart.testing import WebsocketResponseError

"""Public Configuration behavior generated from the Quart specification."""

from quart import Quart
async def test_make_response_str() -> None:
    app = Quart(__name__)

    plain = await app.make_response("plain body")
    with_status = await app.make_response(("status body", 202))
    with_headers = await app.make_response(("header body", {"X-Mode": "public"}))
    full = await app.make_response(("full body", 204, {"X-Mode": "complete"}))

    assert await plain.get_data(as_text=True) == "plain body"
    assert with_status.status_code == 202
    assert await with_status.get_data(as_text=True) == "status body"
    assert with_headers.headers["X-Mode"] == "public"
    assert full.status_code == 204
    assert full.headers["X-Mode"] == "complete"


async def test_make_response_response() -> None:
    app = Quart(__name__)

    direct = await app.make_response(Response("direct body"))
    with_headers = await app.make_response((Response("header body"), {"X-Mode": "response"}))
    full = await app.make_response((Response("full body"), 203, {"X-Mode": "full"}))

    assert await direct.get_data(as_text=True) == "direct body"
    assert await with_headers.get_data(as_text=True) == "header body"
    assert with_headers.headers["X-Mode"] == "response"
    assert full.status_code == 203
    assert full.headers["X-Mode"] == "full"


async def test_make_response_errors() -> None:
    app = Quart(__name__)
    invalid_values = [None, ("only value",), ("body", 200, {}, "extra")]

    for value in invalid_values:
        with pytest.raises(TypeError):
            await app.make_response(value)  # type: ignore[arg-type]


async def test_has_app_context() -> None:
    app = Quart(__name__)
    assert not has_app_context()

    async with app.app_context():
        assert has_app_context()
        assert not has_request_context()

    assert not has_app_context()


async def test_template_render() -> None:
    app = Quart(__name__)
    async with app.app_context():
        rendered = await render_template_string("Hello {{ person }}", person="Ada")
    assert rendered == "Hello Ada"


async def test_unmatched_http_rule_returns_404():
    app = Quart(__name__)

    response = await app.test_client().get("/missing")

    assert response.status_code == 404


async def test_jsonify_returns_json_response():
    app = Quart(__name__)

    async with app.app_context():
        response = jsonify("one", 2)

    assert await response.get_json() == ["one", 2]


async def test_make_response_rejects_none_value():
    app = Quart(__name__)

    async with app.app_context():
        with pytest.raises(TypeError):
            await make_response(None)


async def test_make_response_rejects_invalid_length_tuple():
    app = Quart(__name__)

    async with app.app_context():
        with pytest.raises(TypeError):
            await make_response(("body", 200, {}, "extra"))


async def test_app_context_exposes_current_app_and_g():
    app = Quart(__name__)

    assert not has_app_context()
    async with app.app_context():
        g.answer = 42
        assert has_app_context()
        assert current_app == app
        assert g.answer == 42
    assert not has_app_context()


async def test_request_context_exposes_request_and_ends_cleanly():
    app = Quart(__name__)

    assert not has_request_context()
    async with app.test_request_context("/context", method="PATCH"):
        assert has_request_context()
        assert request.path == "/context"
        assert request.method == "PATCH"
    assert not has_request_context()
    with pytest.raises(RuntimeError):
        request.path


def test_from_prefixed_env_applies_loads_to_prefixed_values(monkeypatch):
    app = Quart(__name__)
    monkeypatch.setenv("SWE_CONFIG_ENABLED", "true")

    app.config.from_prefixed_env(prefix="SWE_CONFIG")

    assert app.config["ENABLED"] is True


def test_from_prefixed_env_keeps_original_string_when_loads_fails(monkeypatch):
    app = Quart(__name__)
    monkeypatch.setenv("SWE_CONFIG_VALUE", "unparsed")

    def rejecting_loads(value):
        raise ValueError("invalid configuration value")

    app.config.from_prefixed_env(prefix="SWE_CONFIG", loads=rejecting_loads)

    assert app.config["VALUE"] == "unparsed"


def test_from_prefixed_env_creates_nested_keys_and_ignores_other_prefixes(monkeypatch):
    app = Quart(__name__)
    app.config["UNCHANGED"] = "original"
    monkeypatch.setenv("SWE_CONFIG_PARENT__CHILD", '"nested"')
    monkeypatch.setenv("UNRELATED_CONFIG_UNCHANGED", '"replacement"')

    app.config.from_prefixed_env(prefix="SWE_CONFIG")

    assert app.config["PARENT"]["CHILD"] == "nested"
    assert app.config["UNCHANGED"] == "original"
