from __future__ import annotations

import asyncio
import importlib
from pathlib import Path


def q():
    return importlib.import_module("quart")


def test_a01(tmp_path: Path) -> None:
    quart = q(); app = quart.Quart("native-a01"); blueprint = quart.Blueprint("bp", "native-a01-bp"); response = quart.Response("body", status=202)
    assert app.name == "native-a01" and blueprint.name == "bp" and response.status_code == 202


def test_a02(tmp_path: Path) -> None:
    quart = q(); app = quart.Quart("native-a02"); app.config.from_mapping(ALPHA=1, NESTED={"enabled": True})
    testing = importlib.import_module("quart.testing")
    assert app.config["ALPHA"] == 1 and app.config["NESTED"] == {"enabled": True} and isinstance(app.test_client(), testing.QuartClient)


def test_a03(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); response = quart.Response(b"payload", status=207, headers={"X-Mode": "native"})
        assert await response.get_data() == b"payload" and await response.get_data(as_text=True) == "payload"
        assert response.status_code == 207 and response.headers["X-Mode"] == "native"
    asyncio.run(scenario())


def test_a04(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-a04")
        async with app.app_context():
            response = quart.jsonify({"items": [1, 2], "ok": True})
            assert await response.get_json() == {"items": [1, 2], "ok": True} and response.content_type.startswith("application/json")
    asyncio.run(scenario())


def test_a05(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-a05"); assert not quart.has_app_context() and not quart.has_request_context()
        async with app.app_context(): quart.g.marker = "owned"; assert quart.current_app.name == app.name and quart.g.marker == "owned"
        assert not quart.has_app_context()
    asyncio.run(scenario())


def test_a06(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-a06")
        @app.route("/item/<int:item_id>")
        async def item(item_id: int): return str(item_id)
        async with app.test_request_context("/"): assert quart.url_for("item", item_id=7) == "/item/7"
    asyncio.run(scenario())


def test_a07(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-a07")
        async with app.app_context(): assert await quart.render_template_string("{{ title }}:{{ values|join('-') }}", title="T", values=[2, 3]) == "T:2-3"
    asyncio.run(scenario())


def test_a08(tmp_path: Path) -> None:
    quart = q(); app = quart.Quart("native-a08")
    async def handler(): return "ok"
    assert app.route("/ok")(handler) is handler and app.websocket("/socket")(handler) is handler
    assert callable(app.before_request) and callable(app.after_request) and callable(app.errorhandler)


def test_i01(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-i01"); trace: list[str] = []
        @app.before_request
        async def before(): trace.append("before")
        @app.after_request
        async def after(response): trace.append("after"); response.headers["X-Trace"] = "done"; return response
        @app.errorhandler(418)
        async def teapot(error): trace.append("error"); return {"kind": "teapot"}, 418
        @app.route("/bad")
        async def bad(): trace.append("handler"); quart.abort(418)
        response = await app.test_client().get("/bad")
        assert response.status_code == 418 and await response.get_json() == {"kind": "teapot"}
        assert response.headers["X-Trace"] == "done" and trace == ["before", "handler", "error", "after"]
    asyncio.run(scenario())


def test_i02(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-i02"); bp = quart.Blueprint("api", "native-i02-bp")
        @bp.route("/items/<name>")
        async def item(name: str): return {"name": name, "endpoint": quart.url_for("api.item", name=name)}
        app.register_blueprint(bp, url_prefix="/v2"); response = await app.test_client().get("/v2/items/alpha")
        assert response.status_code == 200 and await response.get_json() == {"name": "alpha", "endpoint": "/v2/items/alpha"}
    asyncio.run(scenario())


def test_i03(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-i03"); app.secret_key = "secret"
        @app.route("/count")
        async def count(): quart.session["n"] = quart.session.get("n", 0) + 1; return {"n": quart.session["n"]}
        client = app.test_client(); assert await (await client.get("/count")).get_json() == {"n": 1}
        assert await (await client.get("/count")).get_json() == {"n": 2}
    asyncio.run(scenario())


def test_i04(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-i04")
        @app.websocket("/echo")
        async def echo(): value = await quart.websocket.receive_json(); await quart.websocket.send_json({"echo": value})
        async with app.test_client().websocket("/echo") as connection:
            await connection.send_json(["x", 4]); assert await connection.receive_json() == {"echo": ["x", 4]}
    asyncio.run(scenario())


def test_s01(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); app = quart.Quart("native-s01"); app.secret_key = "secret"; seen: list[str] = []
        @app.before_request
        async def before(): quart.g.request_id = quart.request.headers.get("X-Request", "none"); seen.append(quart.request.path)
        @app.route("/workflow/<int:value>", methods=["POST"])
        async def workflow(value: int):
            body = await quart.request.get_json(); quart.session["last"] = value
            text = await quart.render_template_string("{{ g.request_id }}:{{ value }}:{{ body.name }}", value=value, body=body)
            return {"rendered": text, "path": quart.url_for("workflow", value=value)}
        client = app.test_client(); response = await client.post("/workflow/9", json={"name": "alpha"}, headers={"X-Request": "r1"})
        assert response.status_code == 200 and await response.get_json() == {"rendered": "r1:9:alpha", "path": "/workflow/9"}
        assert seen == ["/workflow/9"]
        async with client.session_transaction() as stored: assert stored["last"] == 9
    asyncio.run(scenario())


def test_s02(tmp_path: Path) -> None:
    async def scenario() -> None:
        quart = q(); first = quart.Quart("native-s02-shared"); second = quart.Quart("native-s02-shared")
        @first.route("/owner")
        async def first_owner(): return {"owner": "first", "app": quart.current_app.name}
        @second.route("/owner")
        async def second_owner(): return {"owner": "second", "app": quart.current_app.name}
        @first.websocket("/socket")
        async def socket(): await quart.websocket.send("first-socket")
        one = await first.test_client().get("/owner"); two = await second.test_client().get("/owner")
        assert (await one.get_json())["owner"] == "first" and (await two.get_json())["owner"] == "second"
        async with first.test_client().websocket("/socket") as connection: assert await connection.receive() == "first-socket"
        assert (await second.test_client().get("/socket")).status_code == 404
    asyncio.run(scenario())
