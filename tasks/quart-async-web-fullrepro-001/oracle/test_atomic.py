"""Atomic tests for quart-async-web-fullrepro-001.

Each test exercises ONE public API with ONE behavior.
"""
from __future__ import annotations

import pytest
from werkzeug.routing import BuildError

from quart import (
    Quart,
    Response,
    abort,
    copy_current_app_context,
    copy_current_request_context,
    copy_current_websocket_context,
    current_app,
    g,
    has_app_context,
    has_request_context,
    has_websocket_context,
    jsonify,
    make_response,
    render_template_string,
    request,
    session,
    url_for,
    websocket,
    Blueprint,
    flash,
    get_flashed_messages,
    stream_template_string,
    stream_with_context,
)
from conftest import make_app, run_async


# =============================================================================
# make_response
# =============================================================================


async def test_make_response_from_string():
    app = make_app()
    async with app.app_context():
        resp = await make_response("hello")
        assert resp.status_code == 200
        assert await resp.get_data(as_text=True) == "hello"


async def test_make_response_from_tuple_with_status():
    app = make_app()
    async with app.app_context():
        resp = await make_response(("created", 201))
        assert resp.status_code == 201
        assert await resp.get_data(as_text=True) == "created"


async def test_make_response_from_response_passthrough():
    app = make_app()
    async with app.app_context():
        original = Response("body", status=202)
        resp = await make_response(original)
        assert resp is original


async def test_make_response_none_raises_type_error():
    app = make_app()
    async with app.app_context():
        with pytest.raises(TypeError):
            await make_response(None)


# =============================================================================
# jsonify
# =============================================================================


async def test_jsonify_returns_json_response():
    app = make_app()
    async with app.app_context():
        resp = await jsonify(key="val")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"
        data = await resp.get_json()
        assert data == {"key": "val"}


async def test_jsonify_positional_args_produce_array():
    app = make_app()
    async with app.app_context():
        resp = await jsonify(1, 2, 3)
        data = await resp.get_json()
        assert data == [1, 2, 3]


# =============================================================================
# Application and request context
# =============================================================================


async def test_app_context_resolves_current_app():
    app = make_app()
    async with app.app_context():
        assert has_app_context() is True
        assert current_app._get_current_object() is app


async def test_outside_context_has_app_context_false():
    assert has_app_context() is False
    assert has_request_context() is False


async def test_request_context_resolves_request():
    app = make_app()
    async with app.test_request_context("/test-path", method="POST"):
        assert has_request_context() is True
        assert request.path == "/test-path"
        assert request.method == "POST"


async def test_request_context_also_establishes_app_context():
    app = make_app()
    async with app.test_request_context("/"):
        assert has_app_context() is True
        assert has_request_context() is True
        assert request.path == "/"


async def test_g_namespace_within_context():
    app = make_app()
    async with app.app_context():
        g.answer = 42
        assert g.answer == 42


async def test_proxy_outside_context_raises():
    app = make_app()
    async with app.app_context():
        pass
    with pytest.raises(RuntimeError):
        _ = current_app.name


# =============================================================================
# URL generation
# =============================================================================


async def test_url_for_generates_path():
    app = make_app()

    @app.route("/items/<int:item_id>")
    async def item(item_id):
        return ""

    async with app.test_request_context("/"):
        result = url_for("item", item_id=7)
        assert result == "/items/7"


async def test_url_for_missing_endpoint_raises():
    app = make_app()
    async with app.test_request_context("/"):
        with pytest.raises(BuildError):
            url_for("nonexistent")


async def test_url_for_external_with_server_name():
    app = make_app()
    app.config["SERVER_NAME"] = "api.test"

    @app.route("/page")
    async def page():
        return ""

    async with app.test_request_context("/"):
        result = url_for("page", _external=True)
        assert "api.test" in result


async def test_url_for_with_anchor():
    app = make_app()

    @app.route("/doc")
    async def doc():
        return ""

    async with app.test_request_context("/"):
        result = url_for("doc", _anchor="section")
        assert result.endswith("#section")


# =============================================================================
# Route converters
# =============================================================================


async def test_int_converter_passes_integer():
    app = make_app()

    @app.route("/num/<int:n>")
    async def handler(n):
        return str(type(n).__name__)

    client = app.test_client()
    resp = await client.get("/num/5")
    assert await resp.get_data(as_text=True) == "int"


async def test_int_converter_rejects_non_integer():
    app = make_app()

    @app.route("/num/<int:n>")
    async def handler(n):
        return "ok"

    client = app.test_client()
    resp = await client.get("/num/abc")
    assert resp.status_code == 404


async def test_path_converter_includes_slashes():
    app = make_app()

    @app.route("/files/<path:filepath>")
    async def handler(filepath):
        return filepath

    client = app.test_client()
    resp = await client.get("/files/a/b/c.txt")
    assert await resp.get_data(as_text=True) == "a/b/c.txt"


# =============================================================================
# Context copying
# =============================================================================


async def test_copy_current_app_context_preserves_g():
    app = make_app()

    async with app.app_context():
        g.val = "captured"

        @copy_current_app_context
        async def task():
            return g.val

        assert await task() == "captured"


async def test_copy_current_request_context_preserves_request():
    app = make_app()

    async with app.test_request_context("/ctx-path"):

        @copy_current_request_context
        async def task():
            return request.path

        assert await task() == "/ctx-path"


async def test_copy_current_app_context_outside_raises():
    with pytest.raises(RuntimeError):
        @copy_current_app_context
        async def task():
            pass


# =============================================================================
# Configuration
# =============================================================================


async def test_config_from_prefixed_env(monkeypatch):
    app = make_app()
    monkeypatch.setenv("MYAPP_DEBUG", "true")
    monkeypatch.setenv("MYAPP_PORT", "8080")
    monkeypatch.setenv("OTHER_VAR", "ignored")
    app.config.from_prefixed_env("MYAPP")
    assert app.config["DEBUG"] == True
    assert app.config["PORT"] == 8080
    assert "OTHER_VAR" not in app.config


# =============================================================================
# after_this_request
# =============================================================================


async def test_after_this_request_outside_context_raises():
    from quart import after_this_request
    with pytest.raises(RuntimeError):
        after_this_request(lambda resp: resp)
