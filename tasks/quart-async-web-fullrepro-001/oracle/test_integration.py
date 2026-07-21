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
@pytest.mark.parametrize(("path", "method"), [("/", "GET"), ("/sync", "GET")])
async def test_index(path: str, method: str) -> None:
    app = Quart(__name__)

    @app.route("/")
    async def async_index() -> str:
        return "async endpoint"

    @app.route("/sync")
    def sync_index() -> str:
        return "sync endpoint"

    response = await app.test_client().open(path, method=method)
    assert await response.get_data(as_text=True) in {"async endpoint", "sync endpoint"}


async def test_iri() -> None:
    app = Quart(__name__)

    @app.route("/heart")
    async def heart() -> str:
        return "heart response"

    response = await app.test_client().get("/heart")
    assert await response.get_data(as_text=True) == "heart response"


async def test_json() -> None:
    app = Quart(__name__)

    @app.route("/json", methods=["POST"])
    async def echo_json() -> Response:
        return jsonify(await request.get_json())

    response = await app.test_client().post("/json", json={"name": "Ada"})
    assert await response.get_json() == {"name": "Ada"}


async def test_implicit_json() -> None:
    app = Quart(__name__)

    @app.route("/object", methods=["POST"])
    async def object_result() -> dict[str, str]:
        return await request.get_json()

    response = await app.test_client().post("/object", json={"kind": "object"})
    assert await response.get_json() == {"kind": "object"}


async def test_implicit_json_list() -> None:
    app = Quart(__name__)

    @app.route("/list", methods=["POST"])
    async def list_result() -> list[object]:
        return await request.get_json()

    response = await app.test_client().post("/list", json=["item", 2])
    assert await response.get_json() == ["item", 2]


async def test_not_found_error() -> None:
    response = await Quart(__name__).test_client().get("/missing")
    assert response.status_code == 404


async def test_websocket() -> None:
    app = Quart(__name__)

    @app.websocket("/echo")
    async def echo() -> None:
        received = await websocket.receive()
        await websocket.send(received)

    payload = b"binary payload"
    async with app.test_client().websocket("/echo") as connection:
        await connection.send(payload)
        assert await connection.receive() == payload


async def test_websocket_abort() -> None:
    app = Quart(__name__)

    @app.websocket("/denied")
    async def denied() -> None:
        abort(401)

    with pytest.raises(WebsocketResponseError) as error:
        async with app.test_client().websocket("/denied") as connection:
            await connection.receive()
    assert error.value.response.status_code == 401


async def test_stream() -> None:
    app = Quart(__name__)

    @app.route("/stream")
    async def stream() -> object:
        async def chunks():
            yield "first "
            yield "second"

        return chunks()

    response = await app.test_client().get("/stream")
    assert await response.get_data(as_text=True) == "first second"


async def test_has_request_context() -> None:
    app = Quart(__name__)
    assert not has_request_context()
    assert not has_app_context()

    async with app.test_request_context("/context"):
        assert has_request_context()
        assert has_app_context()
        assert request.path == "/context"

    assert not has_request_context()
    assert not has_app_context()


async def test_copy_current_app_context() -> None:
    app = Quart(__name__)

    @app.route("/copied-app")
    async def copied_app() -> str:
        g.answer = "available"

        @copy_current_app_context
        async def inspect_context() -> str:
            return g.answer

        return await asyncio.create_task(inspect_context())

    response = await app.test_client().get("/copied-app")
    assert await response.get_data(as_text=True) == "available"


async def test_copy_current_request_context() -> None:
    app = Quart(__name__)

    @app.route("/copied-request")
    async def copied_request() -> str:
        @copy_current_request_context
        async def inspect_context() -> str:
            return request.path

        return await asyncio.create_task(inspect_context())

    response = await app.test_client().get("/copied-request")
    assert await response.get_data(as_text=True) == "/copied-request"


async def test_copy_current_websocket_context() -> None:
    app = Quart(__name__)

    @app.websocket("/copied-websocket")
    async def copied_websocket() -> None:
        @copy_current_websocket_context
        async def inspect_context() -> str:
            return websocket.headers["X-Context-Token"]

        await websocket.send(await asyncio.create_task(inspect_context()))

    async with app.test_client().websocket(
        "/copied-websocket", headers={"X-Context-Token": "copied"}
    ) as connection:
        assert await connection.receive() == "copied"


async def test_default_template_context() -> None:
    app = Quart(__name__)
    app.secret_key = "test secret"

    async with app.app_context():
        g.value = "app context"
        assert await render_template_string("{{ g.value }}") == "app context"

    async with app.test_request_context("/template"):
        session["value"] = "session context"
        rendered = await render_template_string(
            "{{ request.method }}|{{ request.path }}|{{ session.value }}"
        )
    assert rendered == "GET|/template|session context"


async def test_simple_stream() -> None:
    app = Quart(__name__)

    @app.route("/template-stream")
    async def template_stream() -> object:
        return await stream_template_string("stream {{ value }}", value="content")

    response = await app.test_client().get("/template-stream")
    assert await response.get_data(as_text=True) == "stream content"


async def test_methods() -> None:
    app = Quart(__name__)
    methods = ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT", "TRACE")

    @app.route("/method", methods=list(methods))
    async def echo_method() -> str:
        return request.method

    client = app.test_client()
    for method in methods:
        response = await getattr(client, method.lower())("/method")
        assert await response.get_data(as_text=True) == method


async def test_testing_json() -> None:
    app = Quart(__name__)

    @app.route("/echo-json", methods=["POST"])
    async def echo_json() -> Response:
        return jsonify(await request.get_json())

    response = await app.test_client().post("/echo-json", json={"key": "value"})
    assert await response.get_json() == {"key": "value"}


async def test_data() -> None:
    app = Quart(__name__)

    @app.route("/body", methods=["POST"])
    async def body() -> bytes:
        return await request.get_data()

    payload = b"opaque request body"
    response = await app.test_client().post("/body", data=payload)
    assert await response.get_data() == payload


async def test_query_string() -> None:
    app = Quart(__name__)

    @app.route("/query")
    async def query() -> Response:
        return jsonify(value=request.args["value"])

    response = await app.test_client().get("/query", query_string={"value": "found"})
    assert await response.get_json() == {"value": "found"}


async def test_cookie_jar() -> None:
    app = Quart(__name__)
    app.secret_key = "test secret"

    @app.route("/session")
    async def session_value() -> Response:
        previous = session.get("counter")
        session["counter"] = "persisted"
        return jsonify(previous=previous)

    client = app.test_client()
    assert await (await client.get("/session")).get_json() == {"previous": None}
    assert await (await client.get("/session")).get_json() == {"previous": "persisted"}


async def test_websocket_bad_request() -> None:
    app = Quart(__name__)

    @app.websocket("/http-only")
    async def reject_websocket() -> Response:
        return Response("not a websocket", status=418)

    with pytest.raises(WebsocketResponseError) as error:
        async with app.test_client().websocket("/http-only"):
            pass
    assert error.value.response.status_code == 418
    assert await error.value.response.get_data(as_text=True) == "not a websocket"


async def test_websocket_json() -> None:
    app = Quart(__name__)

    @app.websocket("/json-echo")
    async def json_echo() -> None:
        await websocket.send_json(await websocket.receive_json())

    payload = {"event": "hello", "values": [1, 2]}
    async with app.test_client().websocket("/json-echo") as connection:
        await connection.send_json(payload)
        assert await connection.receive_json() == payload


async def test_disallowed_http_method_returns_405():
    app = Quart(__name__)

    @app.route("/created", methods=["POST"])
    async def created():
        return "created"

    response = await app.test_client().get("/created")

    assert response.status_code == 405


async def test_int_converter_rejects_non_integer_path_text():
    app = Quart(__name__)

    @app.route("/items/<int:item_id>")
    async def item(item_id):
        return {"item_id": item_id}

    response = await app.test_client().get("/items/not-an-int")

    assert response.status_code == 404


async def test_path_converter_accepts_slashes():
    app = Quart(__name__)

    @app.route("/files/<path:filename>")
    async def file_name(filename):
        return filename

    response = await app.test_client().get("/files/a/nested/file.txt")

    assert await response.get_data(as_text=True) == "a/nested/file.txt"


async def test_default_string_converter_does_not_accept_slashes():
    app = Quart(__name__)

    @app.route("/names/<name>")
    async def name(name):
        return name

    response = await app.test_client().get("/names/a/b")

    assert response.status_code == 404


async def test_string_handler_result_becomes_text_response():
    app = Quart(__name__)

    @app.route("/text")
    async def text():
        return "hello"

    response = await app.test_client().get("/text")

    assert await response.get_data(as_text=True) == "hello"


async def test_dict_handler_result_becomes_json_response():
    app = Quart(__name__)

    @app.route("/object")
    async def object_response():
        return {"answer": 42}

    response = await app.test_client().get("/object")

    assert await response.get_json() == {"answer": 42}


async def test_list_handler_result_becomes_json_response():
    app = Quart(__name__)

    @app.route("/values")
    async def values():
        return ["one", 2]

    response = await app.test_client().get("/values")

    assert await response.get_json() == ["one", 2]


async def test_tuple_response_applies_status_and_headers():
    app = Quart(__name__)

    @app.route("/created")
    async def created():
        return "saved", 201, {"X-Result": "created"}

    response = await app.test_client().get("/created")

    assert response.status_code == 201
    assert response.headers["X-Result"] == "created"
    assert await response.get_data(as_text=True) == "saved"


async def test_request_get_data_returns_text_when_requested():
    app = Quart(__name__)

    @app.route("/read", methods=["POST"])
    async def read():
        return await request.get_data(as_text=True)

    response = await app.test_client().post("/read", data=b"payload")

    assert await response.get_data(as_text=True) == "payload"


async def test_request_cache_false_drains_subsequent_body_access():
    app = Quart(__name__)

    @app.route("/drain", methods=["POST"])
    async def drain():
        first = await request.get_data(cache=False, as_text=True)
        second = await request.get_data(as_text=True)
        return {"first": first, "second": second}

    response = await app.test_client().post("/drain", data=b"payload")

    assert await response.get_json() == {"first": "payload", "second": ""}


async def test_request_non_json_body_returns_none_without_force():
    app = Quart(__name__)

    @app.route("/json", methods=["POST"])
    async def json_value():
        return {"value": await request.get_json()}

    response = await app.test_client().post("/json", data=b"plain text")

    assert await response.get_json() == {"value": None}


async def test_request_malformed_json_returns_none_when_silent():
    app = Quart(__name__)

    @app.route("/json", methods=["POST"])
    async def json_value():
        return {"value": await request.get_json(silent=True)}

    response = await app.test_client().post(
        "/json", data=b"not-json", headers={"content-type": "application/json"}
    )

    assert await response.get_json() == {"value": None}


async def test_url_for_honors_external_scheme_and_anchor():
    app = Quart(__name__)
    app.config["SERVER_NAME"] = "example.test"

    @app.route("/items/<int:item_id>")
    async def item(item_id):
        return str(item_id)

    async with app.app_context():
        generated = url_for(
            "item", item_id=3, _external=True, _scheme="https", _anchor="details"
        )

    assert generated == "https://example.test/items/3#details"


async def test_url_for_missing_required_value_raises():
    app = Quart(__name__)
    app.config["SERVER_NAME"] = "example.test"

    @app.route("/items/<int:item_id>")
    async def item(item_id):
        return str(item_id)

    async with app.app_context():
        with pytest.raises(Exception):
            url_for("item")


async def test_blueprint_registration_exposes_handler_and_qualified_url():
    app = Quart(__name__)
    blueprint = Blueprint("api", __name__)

    @blueprint.route("/ping")
    async def ping():
        return url_for(".ping")

    app.register_blueprint(blueprint, url_prefix="/api")
    response = await app.test_client().get("/api/ping")

    assert await response.get_data(as_text=True) == "/api/ping"


async def test_cookie_preserving_client_keeps_session_across_requests():
    app = Quart(__name__)
    app.secret_key = "test-secret"

    @app.route("/save")
    async def save():
        session["last_item"] = 3
        return "saved"

    @app.route("/load")
    async def load():
        return {"last_item": session.get("last_item")}

    client = app.test_client()
    await client.get("/save")
    response = await client.get("/load")

    assert await response.get_json() == {"last_item": 3}


async def test_session_write_without_secret_key_is_error_response():
    app = Quart(__name__)

    @app.route("/save")
    async def save():
        session["value"] = "not-persisted"
        return "saved"

    response = await app.test_client().get("/save")

    assert response.status_code >= 400


async def test_flash_messages_are_consumed_by_a_later_request():
    app = Quart(__name__)
    app.secret_key = "test-secret"

    @app.route("/put")
    async def put():
        await flash("hello", "notice")
        return "stored"

    @app.route("/take")
    async def take():
        return {"messages": get_flashed_messages(with_categories=True)}

    client = app.test_client()
    await client.get("/put")
    first = await client.get("/take")
    second = await client.get("/take")

    assert await first.get_json() == {"messages": [["notice", "hello"]]}
    assert await second.get_json() == {"messages": []}


async def test_template_receives_request_g_and_config_values():
    app = Quart(__name__)
    app.config["SERVER_NAME"] = "example.test"

    @app.route("/template")
    async def template():
        g.marker = "from-g"
        return await render_template_string(
            "{{ request.path }}|{{ g.marker }}|{{ config['SERVER_NAME'] }}"
        )

    response = await app.test_client().get("/template")

    assert await response.get_data(as_text=True) == "/template|from-g|example.test"


async def test_stream_with_context_keeps_request_available_during_iteration():
    app = Quart(__name__)

    @app.route("/stream")
    async def stream():
        async def generate():
            yield request.path

        return stream_with_context(generate)()

    response = await app.test_client().get("/stream")

    assert await response.get_data(as_text=True) == "/stream"


async def test_websocket_text_round_trip_preserves_text_kind():
    app = Quart(__name__)

    @app.websocket("/echo")
    async def echo():
        value = await websocket.receive()
        await websocket.send(value)

    async with app.test_client().websocket("/echo") as connection:
        await connection.send("hello")
        assert await connection.receive() == "hello"


async def test_websocket_binary_round_trip_preserves_binary_kind():
    app = Quart(__name__)

    @app.websocket("/echo")
    async def echo():
        value = await websocket.receive()
        await websocket.send(value)

    async with app.test_client().websocket("/echo") as connection:
        await connection.send(b"binary")
        assert await connection.receive() == b"binary"


async def test_websocket_json_round_trip_decodes_json_value():
    app = Quart(__name__)

    @app.websocket("/json")
    async def json_echo():
        value = await websocket.receive_json()
        await websocket.send_json(value)

    async with app.test_client().websocket("/json") as connection:
        await connection.send_json({"answer": [1, 2]})
        assert await connection.receive_json() == {"answer": [1, 2]}


async def test_websocket_abort_before_accept_returns_public_rejection_response():
    app = Quart(__name__)

    @app.websocket("/abort")
    async def rejected():
        abort(418)

    with pytest.raises(WebsocketResponseError) as error:
        async with app.test_client().websocket("/abort"):
            pass

    assert error.value.response.status_code == 418


async def test_websocket_http_response_raises_websocket_response_error():
    app = Quart(__name__)

    @app.websocket("/respond")
    async def rejected():
        return "not-upgraded", 409

    with pytest.raises(WebsocketResponseError) as error:
        async with app.test_client().websocket("/respond"):
            pass

    assert error.value.response.status_code == 409


async def test_representative_workflow_combines_json_routing_session_and_url_for():
    app = Quart(__name__)
    app.secret_key = "test-secret"

    @app.route("/items/<int:item_id>", methods=["POST"])
    async def save_item(item_id):
        payload = await request.get_json()
        session["last_item"] = item_id
        return jsonify(item=payload["name"], detail=url_for("item", item_id=item_id)), 201

    @app.route("/items/<int:item_id>")
    async def item(item_id):
        return {"item_id": item_id, "last_item": session.get("last_item")}

    client = app.test_client()
    created = await client.post("/items/3", json={"name": "book"})
    fetched = await client.get("/items/3")

    assert created.status_code == 201
    assert await created.get_json() == {"detail": "/items/3", "item": "book"}
    assert await fetched.get_json() == {"item_id": 3, "last_item": 3}
