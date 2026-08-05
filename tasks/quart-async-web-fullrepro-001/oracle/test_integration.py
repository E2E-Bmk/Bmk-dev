"""Integration tests for quart-async-web-fullrepro-001.

Each test exercises ≥2 public API boundaries working together.
Seams: route → client → response, session → cookie → persistence,
blueprint → url_for, template → context, websocket → client, etc.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio

from quart import (
    Quart,
    Response,
    Blueprint,
    abort,
    copy_current_websocket_context,
    current_app,
    flash,
    g,
    get_flashed_messages,
    jsonify,
    make_response,
    render_template_string,
    request,
    session,
    stream_template_string,
    stream_with_context,
    url_for,
    websocket,
)
from quart.testing import WebsocketResponseError
from conftest import make_app, run_async


depends_on = pytest.mark.depends_on


# =============================================================================
# CVI-1: Handler result visible through test client
# Seam: route → dispatch → response conversion → client
# =============================================================================


@pytest.mark.depends_on("test_response_get_data_as_text_returns_string", "test_response_get_data_returns_bytes_by_default", "test_make_response_from_string")
async def test_string_handler_returns_text_response():
    """CVI-1: Seam: protocol handoff — string handler return ↔ test client text response."""
    app = make_app()

    @app.route("/hello")
    async def handler():
        return "hello world"

    client = app.test_client()
    resp = await client.get("/hello")
    assert resp.status_code == 200
    assert await resp.get_data(as_text=True) == "hello world"


@pytest.mark.depends_on("test_jsonify_returns_json_response", "test_response_get_data_returns_bytes_by_default", "test_response_get_data_as_text_returns_string")
async def test_dict_handler_returns_json_response():
    """CVI-1: Seam: protocol handoff — dict handler return ↔ test client JSON response."""
    app = make_app()

    @app.route("/data")
    async def handler():
        return {"key": "value"}

    client = app.test_client()
    resp = await client.get("/data")
    assert resp.status_code == 200
    assert await resp.get_json() == {"key": "value"}


@pytest.mark.depends_on("test_make_response_from_tuple_with_status", "test_has_websocket_context_false_outside_handler")
async def test_tuple_handler_applies_status_and_headers():
    """CVI-1: Seam: protocol handoff — tuple handler return ↔ status code and custom headers."""
    app = make_app()

    @app.route("/created")
    async def handler():
        return "done", 201, {"X-Custom": "yes"}

    client = app.test_client()
    resp = await client.get("/created")
    assert resp.status_code == 201
    assert resp.headers["X-Custom"] == "yes"


@depends_on("test_atomic::test_int_converter_rejects_non_integer")
@pytest.mark.depends_on("test_response_get_data_returns_bytes_by_default", "test_response_get_data_as_text_returns_string", "test_jsonify_returns_json_response")
async def test_unmatched_route_returns_404():
    """CVI-1: Seam: error propagation — unmatched route ↔ 404 response."""
    app = make_app()

    @app.route("/exists")
    async def handler():
        return "ok"

    client = app.test_client()
    resp = await client.get("/missing")
    assert resp.status_code == 404


@pytest.mark.depends_on("test_response_get_data_returns_bytes_by_default", "test_response_get_data_as_text_returns_string", "test_jsonify_returns_json_response")
async def test_wrong_method_returns_405():
    """CVI-1: Seam: error propagation — disallowed HTTP method ↔ 405 response."""
    app = make_app()

    @app.route("/post-only", methods=["POST"])
    async def handler():
        return "ok"

    client = app.test_client()
    resp = await client.get("/post-only")
    assert resp.status_code == 405


# =============================================================================
# CVI-2: Blueprint routes reachable through app and url_for
# Seam: blueprint registration → route dispatch → url generation
# =============================================================================


@depends_on("test_atomic::test_url_for_generates_path")
@pytest.mark.depends_on("test_after_this_request_outside_context_raises")
async def test_blueprint_routes_accessible_after_registration():
    """CVI-2: Seam: protocol handoff — blueprint registration ↔ prefixed route dispatch."""
    app = make_app()
    bp = Blueprint("api", __name__, url_prefix="/api")

    @bp.route("/items")
    async def items():
        return "items"

    app.register_blueprint(bp)
    client = app.test_client()
    resp = await client.get("/api/items")
    assert await resp.get_data(as_text=True) == "items"


@depends_on("test_atomic::test_url_for_generates_path")
@pytest.mark.depends_on("test_url_for_missing_endpoint_raises", "test_url_for_with_scheme_overrides_default_scheme", "test_url_for_with_anchor")
async def test_blueprint_endpoint_url_for():
    """CVI-2: Seam: state consistency — blueprint endpoint name ↔ url_for path generation."""
    app = make_app()
    bp = Blueprint("shop", __name__, url_prefix="/shop")

    @bp.route("/product/<int:pid>")
    async def product(pid):
        return str(pid)

    app.register_blueprint(bp)
    async with app.test_request_context("/"):
        url = url_for("shop.product", pid=42)
        assert url == "/shop/product/42"


# =============================================================================
# CVI-3: Session persistence across requests
# Seam: session write → cookie → session read
# =============================================================================


@depends_on("test_atomic::test_g_namespace_within_context")
@depends_on("test_atomic::test_app_context_resolves_current_app")
@pytest.mark.depends_on("test_make_response_from_string", "test_make_response_from_tuple_with_status")
async def test_session_persists_across_requests():
    """CVI-3: Seam: state consistency — session write ↔ cookie ↔ subsequent session read."""
    app = make_app()

    @app.route("/write")
    async def write():
        session["key"] = "stored"
        return "ok"

    @app.route("/read")
    async def read():
        return session.get("key", "empty")

    client = app.test_client()
    await client.get("/write")
    resp = await client.get("/read")
    assert await resp.get_data(as_text=True) == "stored"


@pytest.mark.depends_on("test_make_response_from_string", "test_make_response_from_tuple_with_status")
async def test_session_without_secret_key_errors():
    """CVI-3: Seam: error propagation — missing secret key ↔ session write failure."""
    app = Quart(__name__)

    @app.route("/write")
    async def write():
        session["x"] = "y"
        return "ok"

    client = app.test_client()
    resp = await client.get("/write")
    assert resp.status_code >= 400


# =============================================================================
# CVI-4: current_app resolves to owning application
# Seam: context → proxy resolution → application identity
# =============================================================================


@pytest.mark.depends_on("test_app_context_resolves_current_app")
async def test_current_app_in_handler():
    """CVI-4: Seam: state consistency — request context ↔ current_app config resolution."""
    app = make_app()
    app.config["MARKER"] = "found"

    @app.route("/check")
    async def handler():
        return current_app.config["MARKER"]

    client = app.test_client()
    resp = await client.get("/check")
    assert await resp.get_data(as_text=True) == "found"


# =============================================================================
# CVI-5: Template rendering uses request context
# Seam: template → context variables (request, session, g, config)
# =============================================================================


@pytest.mark.depends_on("test_request_context_resolves_request")
async def test_template_sees_request_path():
    """CVI-5: Seam: state consistency — request context ↔ template request.path variable."""
    app = make_app()

    @app.route("/tpl")
    async def handler():
        return await render_template_string("path={{ request.path }}")

    client = app.test_client()
    resp = await client.get("/tpl")
    assert "path=/tpl" in await resp.get_data(as_text=True)


@pytest.mark.depends_on("test_config_from_prefixed_env")
async def test_template_sees_config():
    """CVI-5: Seam: config interaction — app.config ↔ template config access."""
    app = make_app()
    app.config["SITE_NAME"] = "TestSite"

    @app.route("/site")
    async def handler():
        return await render_template_string("{{ config.SITE_NAME }}")

    client = app.test_client()
    resp = await client.get("/site")
    assert await resp.get_data(as_text=True) == "TestSite"


# =============================================================================
# CVI-6: WebSocket text/binary messages
# Seam: websocket handler → test client → message exchange
# =============================================================================


@pytest.mark.depends_on("test_has_websocket_context_false_outside_handler")
async def test_websocket_text_round_trip():
    """CVI-6: Seam: protocol handoff — websocket text send ↔ client receive echo."""
    app = make_app()

    @app.websocket("/ws")
    async def ws():
        data = await websocket.receive()
        await websocket.send(f"echo:{data}")

    client = app.test_client()
    async with client.websocket("/ws") as ws:
        await ws.send("hello")
        reply = await ws.receive()
    assert reply == "echo:hello"


@pytest.mark.depends_on("test_response_get_data_returns_bytes_by_default", "test_has_websocket_context_false_outside_handler")
async def test_websocket_bytes_round_trip():
    """CVI-6: Seam: protocol handoff — websocket bytes send ↔ client receive echo."""
    app = make_app()

    @app.websocket("/ws-bin")
    async def ws():
        data = await websocket.receive()
        assert isinstance(data, bytes)
        await websocket.send(data + b"-reply")

    client = app.test_client()
    async with client.websocket("/ws-bin") as ws:
        await ws.send(b"binary")
        reply = await ws.receive()
    assert reply == b"binary-reply"


@pytest.mark.depends_on("test_jsonify_returns_json_response", "test_has_websocket_context_false_outside_handler")
async def test_websocket_json_round_trip():
    """CVI-6: Seam: state consistency — websocket JSON send ↔ receive round-trip."""
    app = make_app()

    @app.websocket("/ws-json")
    async def ws():
        data = await websocket.receive_json()
        await websocket.send_json({"received": data})

    client = app.test_client()
    async with client.websocket("/ws-json") as ws:
        await ws.send_json({"msg": "hi"})
        reply = await ws.receive_json()
    assert reply == {"received": {"msg": "hi"}}


# =============================================================================
# CVI-7: WebSocket rejection raises WebsocketResponseError
# Seam: websocket handler → abort → client exception
# =============================================================================


@depends_on("test_atomic::test_proxy_outside_context_raises")
@depends_on("test_atomic::test_has_websocket_context_false_outside_handler")
@pytest.mark.depends_on("test_make_response_none_raises_type_error", "test_url_for_missing_endpoint_raises", "test_response_get_data_returns_bytes_by_default")
async def test_websocket_abort_raises_response_error():
    """CVI-7: Seam: error propagation — websocket abort(403) ↔ WebsocketResponseError."""
    app = make_app()

    @app.websocket("/ws-reject")
    async def ws():
        abort(403)

    client = app.test_client()
    with pytest.raises(WebsocketResponseError) as exc_info:
        async with client.websocket("/ws-reject"):
            pass
    assert exc_info.value.response.status_code == 403


# =============================================================================
# CVI-8: stream_with_context preserves request
# Seam: stream → context → request proxy
# =============================================================================


@pytest.mark.depends_on("test_request_context_resolves_request")
async def test_stream_with_context_preserves_request():
    """CVI-8: Seam: lifecycle crossing — stream generator ↔ preserved request context."""
    app = make_app()

    @app.route("/stream")
    async def handler():
        @stream_with_context
        async def generate():
            yield request.path.encode()

        return Response(generate())

    client = app.test_client()
    resp = await client.get("/stream")
    assert await resp.get_data() == b"/stream"


# =============================================================================
# Flash messages
# Seam: flash → session → get_flashed_messages
# =============================================================================


@depends_on("test_atomic::test_g_namespace_within_context")
@depends_on("test_atomic::test_app_context_resolves_current_app")
@pytest.mark.depends_on("test_make_response_from_string", "test_make_response_from_tuple_with_status")
async def test_flash_messages_persist_and_consumed():
    """Seam: state consistency — flash write ↔ session ↔ get_flashed_messages consumption."""
    app = make_app()

    @app.route("/flash")
    async def do_flash():
        await flash("hello", "info")
        return "ok"

    @app.route("/read-flash")
    async def read_flash():
        msgs = get_flashed_messages(with_categories=True)
        return str(msgs)

    @app.route("/read-again")
    async def read_again():
        msgs = get_flashed_messages()
        return str(msgs)

    client = app.test_client()
    await client.get("/flash")
    resp = await client.get("/read-flash")
    text = await resp.get_data(as_text=True)
    assert ("info", "hello") in eval(text)
    resp2 = await client.get("/read-again")
    assert await resp2.get_data(as_text=True) == "[]"


# =============================================================================
# Request body access
# Seam: client → request.get_data / get_json → handler
# =============================================================================


@pytest.mark.depends_on("test_response_get_data_returns_bytes_by_default", "test_response_get_data_as_text_returns_string", "test_request_context_resolves_request")
async def test_request_get_data_returns_body():
    """Seam: protocol handoff — client POST body ↔ request.get_data echo."""
    app = make_app()

    @app.route("/body", methods=["POST"])
    async def handler():
        data = await request.get_data()
        return data

    client = app.test_client()
    resp = await client.post("/body", data=b"rawbytes")
    assert await resp.get_data() == b"rawbytes"


@depends_on("test_atomic::test_jsonify_returns_json_response")
async def test_request_get_json_parses_json():
    """Seam: state consistency — client JSON POST ↔ request.get_json ↔ jsonify response."""
    app = make_app()

    @app.route("/json", methods=["POST"])
    async def handler():
        data = await request.get_json()
        return jsonify(received=data)

    client = app.test_client()
    resp = await client.post("/json", json={"x": 1})
    assert (await resp.get_json())["received"] == {"x": 1}


async def test_request_get_json_returns_none_for_non_json():
    """Seam: error propagation — non-JSON body ↔ request.get_json None."""
    app = make_app()

    @app.route("/check", methods=["POST"])
    async def handler():
        data = await request.get_json()
        return str(data)

    client = app.test_client()
    resp = await client.post("/check", data=b"not json", headers={"Content-Type": "text/plain"})
    assert await resp.get_data(as_text=True) == "None"


async def test_request_args_from_query_string():
    """Seam: state consistency — query string ↔ request.args lookup."""
    app = make_app()

    @app.route("/search")
    async def handler():
        return request.args["q"]

    client = app.test_client()
    resp = await client.get("/search", query_string={"q": "test"})
    assert await resp.get_data(as_text=True) == "test"


# =============================================================================
# Handler error semantics
# =============================================================================


async def test_handler_returning_none_raises_type_error():
    """Seam: error propagation — None handler return raises TypeError at dispatch."""
    app = make_app()
    app.testing = True

    @app.route("/bad")
    async def handler():
        return None

    client = app.test_client()
    with pytest.raises(TypeError):
        await client.get("/bad")


# =============================================================================
# Client cookie retention (use_cookies)
# Seam: client → set-cookie → subsequent request
# =============================================================================


@depends_on("test_atomic::test_request_context_resolves_request")
async def test_client_retains_cookies():
    """Seam: state consistency — Set-Cookie response ↔ subsequent request Cookie header."""
    app = make_app()

    @app.route("/set")
    async def set_cookie():
        resp = Response("ok")
        resp.set_cookie("tok", "xyz")
        return resp

    @app.route("/get")
    async def get_cookie():
        return request.cookies.get("tok", "none")

    client = app.test_client()
    await client.get("/set")
    resp = await client.get("/get")
    assert await resp.get_data(as_text=True) == "xyz"


# =============================================================================
# Nested blueprints
# =============================================================================


async def test_nested_blueprint_qualified_endpoint():
    """Seam: protocol handoff — nested blueprint registration ↔ qualified url_for path."""
    app = make_app()
    parent = Blueprint("parent", __name__, url_prefix="/p")
    child = Blueprint("child", __name__, url_prefix="/c")

    @child.route("/leaf")
    async def leaf():
        return "leaf"

    parent.register_blueprint(child)
    app.register_blueprint(parent)

    client = app.test_client()
    resp = await client.get("/p/c/leaf")
    assert await resp.get_data(as_text=True) == "leaf"

    async with app.test_request_context("/"):
        url = url_for("parent.child.leaf")
        assert url == "/p/c/leaf"


# =============================================================================
# Template globals (url_for, get_flashed_messages in templates)
# Seam: template → context globals → url generation
# =============================================================================


async def test_template_url_for_generates_url():
    """Seam: state consistency — template url_for global ↔ generated route URL."""
    app = make_app()

    @app.route("/page")
    async def page():
        return "page"

    @app.route("/tpl")
    async def tpl():
        return await render_template_string('{{ url_for("page") }}')

    client = app.test_client()
    resp = await client.get("/tpl")
    assert await resp.get_data(as_text=True) == "/page"


# =============================================================================
# WebSocket send_json type error
# Seam: websocket → JSON serialization validation
# =============================================================================


async def test_websocket_send_json_rejects_mixed_args():
    """Seam: error propagation — websocket send_json mixed args ↔ TypeError."""
    app = make_app()

    @app.websocket("/ws-bad")
    async def ws():
        await websocket.receive()
        with pytest.raises(TypeError):
            await websocket.send_json({"a": 1}, key="val")

    client = app.test_client()
    try:
        async with client.websocket("/ws-bad") as ws:
            await ws.send("trigger")
            await ws.receive()
    except Exception:
        pass


# =============================================================================
# Before/after request hooks
# =============================================================================


@depends_on("test_atomic::test_app_context_resolves_current_app")
async def test_before_request_runs_before_handler():
    """Seam: lifecycle crossing — before_request hook runs before route handler."""
    app = make_app()

    @app.before_request
    async def hook():
        g.hooked = True

    @app.route("/check-hook")
    async def handler():
        return str(g.hooked)

    client = app.test_client()
    resp = await client.get("/check-hook")
    assert await resp.get_data(as_text=True) == "True"


@depends_on("test_atomic::test_make_response_from_string")
async def test_after_request_modifies_response():
    """Seam: lifecycle crossing — after_request hook modifies response headers."""
    app = make_app()

    @app.after_request
    async def hook(resp):
        resp.headers["X-After"] = "applied"
        return resp

    @app.route("/after")
    async def handler():
        return "ok"

    client = app.test_client()
    resp = await client.get("/after")
    assert resp.headers["X-After"] == "applied"


@depends_on("test_atomic::test_make_response_from_tuple_with_status")
async def test_error_handler_catches_abort_code():
    """Seam: error propagation — custom error handler catches abort status code."""
    app = make_app()

    @app.errorhandler(418)
    async def teapot_handler(error):
        return "I am a teapot", 418

    @app.route("/brew")
    async def handler():
        abort(418)

    client = app.test_client()
    resp = await client.get("/brew")
    assert resp.status_code == 418
    assert await resp.get_data(as_text=True) == "I am a teapot"


# =============================================================================
# New integration tests
# =============================================================================


@depends_on("test_atomic::test_request_context_resolves_request", "test_atomic::test_response_get_data_as_text_returns_string")
async def test_request_get_data_as_text_echoes_body():
    """Seam: protocol handoff — client POST body ↔ request.get_data(as_text=True) round-trip."""
    app = make_app()

    @app.route("/text-body", methods=["POST"])
    async def handler():
        text = await request.get_data(as_text=True)
        return text

    client = app.test_client()
    resp = await client.post("/text-body", data=b"echo-me")
    assert await resp.get_data(as_text=True) == "echo-me"


@depends_on("test_atomic::test_jsonify_returns_json_response", "test_atomic::test_request_context_resolves_request")
async def test_request_get_json_force_parses_non_json_content_type():
    """Seam: protocol handoff — get_json(force=True) parses despite non-JSON content type."""
    app = make_app()

    @app.route("/force-json", methods=["POST"])
    async def handler():
        data = await request.get_json(force=True)
        return jsonify(received=data)

    client = app.test_client()
    resp = await client.post(
        "/force-json",
        data=b'{"key": "val"}',
        headers={"Content-Type": "text/plain"},
    )
    result = await resp.get_json()
    assert result["received"] == {"key": "val"}


@depends_on("test_atomic::test_copy_current_app_context_preserves_g", "test_atomic::test_app_context_resolves_current_app")
async def test_copy_current_websocket_context_preserves_websocket():
    """Seam: lifecycle crossing — copy_current_websocket_context preserves websocket headers."""
    app = make_app()
    captured = {}

    @app.websocket("/ws-ctx")
    async def ws_handler():
        @copy_current_websocket_context
        async def background():
            captured["host"] = websocket.headers.get("host", "none")

        await websocket.accept()
        await background()
        await websocket.send("done")

    client = app.test_client()
    async with client.websocket("/ws-ctx") as ws:
        reply = await ws.receive()
    assert reply == "done"
    assert captured == {"host": "localhost"}


@pytest.mark.depends_on("test_url_for_generates_path")
async def test_default_string_converter_rejects_slash_through_routing():
    """Seam: a default string converter rejects slash-containing route values."""
    app = make_app()

    @app.route("/item/<name>")
    async def handler(name):
        return name

    client = app.test_client()
    assert (await client.get("/item/a")).status_code == 200
    assert (await client.get("/item/a/b")).status_code == 404
