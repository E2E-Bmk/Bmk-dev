from __future__ import annotations

import asyncio
import json as stdjson

import pytest

from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.config import Config, DetailedConverter
from sanic.exceptions import URLBuildError
from sanic.response import empty, file, html, json, raw, redirect, text

from conftest import make_app, run_asgi, write_text


class ObjectSettings:
    OBJECT_VALUE = "loaded"
    lower_value = "ignored"

    @property
    def DERIVED_VALUE(self):
        return "derived"


class PairConverter:
    def __call__(self, value: str):
        if ":" not in value:
            raise ValueError
        left, right = value.split(":", 1)
        return left, int(right)


class DefaultsCastConverter(DetailedConverter):
    def __call__(
        self, full_key: str, config_key: str, value: str, defaults: dict
    ):
        if config_key not in defaults:
            raise ValueError
        return type(defaults[config_key])(value)


def test_config_env_casts_basic_types(monkeypatch):
    monkeypatch.setenv("SANIC_LIMIT", "7")
    monkeypatch.setenv("SANIC_ENABLED", "true")
    monkeypatch.setenv("SANIC_RATIO", "3.5")

    app = make_app("config_env_casts_basic_types")

    assert app.config.LIMIT == 7
    assert app.config.ENABLED is True
    assert app.config.RATIO == 3.5


def test_config_custom_env_prefix(monkeypatch):
    monkeypatch.setenv("MYAPP_LIMIT", "9")
    monkeypatch.setenv("SANIC_LIMIT", "11")

    app = Sanic(
        "config_custom_env_prefix",
        env_prefix="MYAPP_",
        configure_logging=False,
    )
    app.config.USE_UVLOOP = False

    assert app.config.LIMIT == 9


def test_config_env_prefix_none_disables_autoload(monkeypatch):
    monkeypatch.setenv("SANIC_DISABLED_VALUE", "1")

    app = Sanic(
        "config_env_prefix_none_disables_autoload",
        env_prefix=None,
        configure_logging=False,
    )
    app.config.USE_UVLOOP = False

    assert getattr(app.config, "DISABLED_VALUE", None) is None


def test_config_loads_uppercase_from_mapping_and_instance():
    app = make_app("config_loads_uppercase_from_mapping_and_instance")

    app.config.load({"MAPPING_VALUE": "mapping", "lower": "ignored"})
    app.config.load(ObjectSettings())

    assert app.config.MAPPING_VALUE == "mapping"
    assert app.config.OBJECT_VALUE == "loaded"
    assert app.config.DERIVED_VALUE == "derived"
    assert "lower" not in app.config
    assert "lower_value" not in app.config


def test_config_loads_uppercase_from_file(tmp_path):
    path = write_text(
        tmp_path / "settings.py",
        "FILE_VALUE = 'from-file'\n"
        "condition = True\n"
        "if condition:\n"
        "    CONDITIONAL_VALUE = 12\n",
    )
    app = make_app("config_loads_uppercase_from_file")

    app.update_config(path)

    assert app.config.FILE_VALUE == "from-file"
    assert app.config.CONDITIONAL_VALUE == 12
    assert "condition" not in app.config


def test_config_register_type_casts_custom_value(monkeypatch):
    monkeypatch.setenv("SANIC_ENDPOINT", "api:8080")
    config = Config(converters=[PairConverter()])
    app = Sanic(
        "config_register_type_casts_custom_value",
        config=config,
        configure_logging=False,
    )
    app.config.USE_UVLOOP = False

    assert app.config.ENDPOINT == ("api", 8080)


def test_config_detailed_converter_uses_defaults(monkeypatch):
    monkeypatch.setenv("SANIC_PORT", "9001")
    config = Config(
        defaults={"PORT": 9000},
        converters=[DefaultsCastConverter()],
    )
    app = Sanic(
        "config_detailed_converter_uses_defaults",
        config=config,
        configure_logging=False,
    )
    app.config.USE_UVLOOP = False

    assert app.config.PORT == 9001
    assert isinstance(app.config.PORT, int)


def test_config_update_config_only_keeps_uppercase_and_setters():
    cfg = Config()

    cfg.update_config({"KEEP_ALIVE": False, "lower": "ignored"})

    assert cfg.KEEP_ALIVE is False
    assert "lower" not in cfg


def test_request_json_body_args_token_and_path():
    app = make_app("request_json_body_args_token_and_path")

    @app.post("/payload")
    async def payload(request):
        return text(
            "|".join(
                [
                    request.json["name"],
                    request.args.get("page"),
                    request.token,
                    request.path,
                ]
            )
        )

    _, response = run_asgi(
        app,
        "post",
        "/payload?page=2",
        json={"name": "sanic"},
        headers={"Authorization": "Bearer public-token"},
    )

    assert response.text == "sanic|2|public-token|/payload"


def test_request_form_fields_and_file_upload(tmp_path):
    upload = write_text(tmp_path / "payload.txt", "uploaded")
    app = make_app("request_form_fields_and_file_upload")

    @app.post("/form")
    async def form(request):
        file_item = request.files.get("upload")
        return text(
            f"{request.form.get('label')}|"
            f"{request.form.getlist('label')}|"
            f"{file_item.name}|{file_item.body.decode()}"
        )

    with upload.open("rb") as stream:
        _, response = run_asgi(
            app,
            "post",
            "/form",
            data={"label": ["one", "two"]},
            files={"upload": stream},
        )

    assert response.text == "one|['one', 'two']|payload.txt|uploaded"


def test_request_raw_body_and_headers():
    app = make_app("request_raw_body_and_headers")

    @app.post("/raw")
    async def raw_route(request):
        return text(
            f"{request.body.decode()}|{request.headers.get('x-contract')}"
        )

    _, response = run_asgi(
        app,
        "post",
        "/raw",
        content=b"raw-bytes",
        headers={"X-Contract": "visible"},
    )

    assert response.text == "raw-bytes|visible"


def test_request_query_lists_and_path_parameters():
    app = make_app("request_query_lists_and_path_parameters")

    @app.get("/items/<item>")
    async def item_route(request, item):
        return text(f"{item}|{request.args.getlist('tag')}|{request.path}")

    _, response = run_asgi(
        app,
        "get",
        "/items/alpha?tag=one&tag=two",
    )

    assert response.text == "alpha|['one', 'two']|/items/alpha"


def test_request_ip_method_and_safe_flags():
    app = make_app("request_ip_method_and_safe_flags")

    @app.get("/safe")
    async def safe(request):
        return text(f"{request.ip}|{request.method}|{request.is_safe}")

    _, response = run_asgi(app, "get", "/safe")

    assert response.text == "mockserver|GET|True"


def test_response_text_html_json_raw_helpers():
    text_response = text("hello")
    html_response = html("<p>hello</p>")
    json_response = json({"hello": "world"})
    raw_response = raw(b"\x00\x01")

    assert text_response.body == b"hello"
    assert text_response.content_type.startswith("text/plain")
    assert html_response.body == b"<p>hello</p>"
    assert html_response.content_type.startswith("text/html")
    assert stdjson.loads(json_response.body) == {"hello": "world"}
    assert json_response.content_type == "application/json"
    assert raw_response.body == b"\x00\x01"
    assert raw_response.content_type == "application/octet-stream"


def test_response_empty_and_redirect_helpers():
    empty_response = empty()
    redirect_response = redirect("/target")

    assert empty_response.status == 204
    assert redirect_response.status == 302
    assert redirect_response.headers["Location"] == "/target"


def test_response_json_mutators_update_array_and_object():
    object_response = json({"name": "sanic"})
    list_response = json(["alpha"])

    object_response.update({"version": 25})
    list_response.append("beta")
    list_response.extend(["gamma"])

    assert stdjson.loads(object_response.body) == {
        "name": "sanic",
        "version": 25,
    }
    assert stdjson.loads(list_response.body) == ["alpha", "beta", "gamma"]


def test_response_file_helper_reads_local_path(tmp_path):
    path = write_text(tmp_path / "asset.txt", "file-body")

    response = asyncio.run(file(path))

    assert response.body == b"file-body"
    assert response.content_type.startswith("text/plain")


def test_response_add_and_delete_cookie_headers():
    response = text("cookies")

    response.add_cookie("theme", "dark", path="/")
    response.delete_cookie("gone", path="/")
    theme = response.cookies.get_cookie("theme")
    gone = response.cookies.get_cookie("gone")

    assert response.cookies.has_cookie("theme")
    assert theme.value == "dark"
    assert theme.path == "/"
    assert gone.value == ""
    assert gone.max_age == 0


def test_route_get_post_and_method_not_allowed():
    app = make_app("route_get_post_and_method_not_allowed")

    @app.get("/items")
    async def get_items(request):
        return text("get")

    @app.post("/items")
    async def post_items(request):
        return text("post")

    _, get_response = run_asgi(app, "get", "/items")
    _, post_response = run_asgi(app, "post", "/items")
    _, put_response = run_asgi(app, "put", "/items")

    assert get_response.text == "get"
    assert post_response.text == "post"
    assert put_response.status == 405


def test_blueprint_route_prefix_and_name_lookup():
    app = make_app("blueprint_route_prefix_and_name_lookup")
    bp = Blueprint("catalog", url_prefix="/catalog")

    @bp.get("/item")
    async def item(request):
        return text("blueprint")

    app.blueprint(bp)

    assert app.url_for("catalog.item") == "/catalog/item"
    _, response = run_asgi(app, "get", "/catalog/item")
    assert response.text == "blueprint"


def test_blueprint_group_merges_prefixes_and_name_prefix():
    app = make_app("blueprint_group_merges_prefixes_and_name_prefix")
    one = Blueprint("one", url_prefix="/one")
    two = Blueprint("two", url_prefix="/two")

    @one.get("/alpha")
    async def alpha(request):
        return text("alpha")

    @two.get("/beta")
    async def beta(request):
        return text("beta")

    app.blueprint(
        Blueprint.group(one, two, url_prefix="/api", name_prefix="bundle")
    )

    assert app.url_for("bundle_one.alpha") == "/api/one/alpha"
    assert app.url_for("bundle_two.beta") == "/api/two/beta"


def test_url_for_builds_query_and_anchor_paths():
    app = make_app("url_for_builds_query_and_anchor_paths")

    @app.get("/search")
    async def search(request):
        return text("search")

    assert (
        app.url_for("search", query="sanic", page=2, _anchor="top")
        == "/search?query=sanic&page=2#top"
    )


def test_url_for_builds_static_filename_path(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    write_text(root / "asset.txt", "asset")
    app = make_app("url_for_builds_static_filename_path")

    app.static("/files", root)

    assert app.url_for("static", filename="asset.txt") == "/files/asset.txt"


def test_static_serves_file_with_content_type(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    write_text(root / "asset.txt", "asset")
    app = make_app("static_serves_file_with_content_type")
    app.static("/files", root)

    _, response = run_asgi(app, "get", "/files/asset.txt")

    assert response.text == "asset"
    assert response.headers.get("content-type").startswith("text/plain")


def test_static_directory_serves_multiple_files(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    write_text(root / "one.txt", "one")
    write_text(root / "page.html", "<h1>Page</h1>")
    app = make_app("static_directory_serves_multiple_files")
    app.static("/", root)

    _, text_response = run_asgi(app, "get", "/one.txt")
    _, html_response = run_asgi(app, "get", "/page.html")

    assert text_response.text == "one"
    assert text_response.headers.get("content-type").startswith("text/plain")
    assert html_response.text == "<h1>Page</h1>"
    assert html_response.headers.get("content-type").startswith("text/html")


def test_request_and_response_middleware_run_in_order():
    order = []
    app = make_app("request_and_response_middleware_run_in_order")

    @app.on_request
    async def first_request(request):
        order.append("request-1")
        request.ctx.flag = "ctx"

    @app.on_request
    async def second_request(request):
        order.append("request-2")

    @app.on_response
    async def first_response(request, response):
        order.append("response-1")
        response.headers["x-first"] = request.ctx.flag

    @app.on_response
    async def second_response(request, response):
        order.append("response-2")

    @app.get("/chain")
    async def chain(request):
        order.append("handler")
        return text(request.ctx.flag)

    _, response = run_asgi(app, "get", "/chain")

    assert response.text == "ctx"
    assert response.headers.get("x-first") == "ctx"
    assert order == [
        "request-1",
        "request-2",
        "handler",
        "response-2",
        "response-1",
    ]


def test_request_middleware_can_short_circuit_with_response():
    order = []
    app = make_app("request_middleware_can_short_circuit_with_response")

    @app.on_request
    async def gate(request):
        order.append("gate")
        return text("blocked", status=403)

    @app.get("/blocked")
    async def blocked(request):
        order.append("handler")
        return text("allowed")

    _, response = run_asgi(app, "get", "/blocked")

    assert response.status == 403
    assert response.text == "blocked"
    assert order == ["gate"]


def test_listener_hooks_run_around_asgi_request():
    order = []
    app = make_app("listener_hooks_run_around_asgi_request")

    @app.before_server_start
    async def before(app):
        order.append("before")
        app.ctx.ready = True

    @app.after_server_stop
    async def after(app):
        order.append("after")

    @app.get("/ready")
    async def ready(request):
        order.append("handler")
        return text(str(request.app.ctx.ready))

    _, response = run_asgi(app, "get", "/ready")

    assert response.text == "True"
    assert order == ["before", "handler", "after"]


def test_blueprint_middleware_modifies_headers():
    app = make_app("blueprint_middleware_modifies_headers")
    bp = Blueprint("guarded", url_prefix="/guarded")

    @bp.middleware("request")
    async def set_state(request):
        request.ctx.bp_state = "blueprint"

    @bp.middleware("response")
    async def add_header(request, response):
        response.headers["x-bp-state"] = request.ctx.bp_state

    @bp.get("/route")
    async def route(request):
        return text(request.ctx.bp_state)

    app.blueprint(bp)
    _, response = run_asgi(app, "get", "/guarded/route")

    assert response.text == "blueprint"
    assert response.headers.get("x-bp-state") == "blueprint"


def test_multiple_middleware_priorities_affect_order():
    order = []
    app = make_app("multiple_middleware_priorities_affect_order")

    @app.on_request(priority=0)
    async def low_priority(request):
        order.append("low")

    @app.on_request(priority=99)
    async def high_priority(request):
        order.append("high")

    @app.get("/priority")
    async def priority(request):
        order.append("handler")
        return text(",".join(order))

    _, response = run_asgi(app, "get", "/priority")

    assert response.text == "high,low,handler"
    assert order == ["high", "low", "handler"]
