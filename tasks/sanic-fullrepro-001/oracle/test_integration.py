from __future__ import annotations

import base64

import pytest

from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.config import Config, DetailedConverter
from sanic.response import empty, file, html, json, raw, redirect, text

from conftest import make_app, run_asgi, write_text


class PairConverter:
    def __call__(self, value: str):
        if ":" not in value:
            raise ValueError
        left, right = value.split(":", 1)
        return {"host": left, "port": int(right)}


class DefaultsCastConverter(DetailedConverter):
    def __call__(
        self, full_key: str, config_key: str, value: str, defaults: dict
    ):
        if config_key not in defaults:
            raise ValueError
        return type(defaults[config_key])(value)


class ObjectSettings:
    OBJECT_VALUE = "object"
    lower_value = "ignored"

    @property
    def DERIVED_VALUE(self):
        return "derived"


@pytest.mark.depends_on(
    "test_config_loads_uppercase_from_file",
    "test_url_for_builds_query_and_anchor_paths",
)
def test_config_file_load_and_route_reads_setting(tmp_path):
    settings = write_text(
        tmp_path / "settings.py",
        "GREETING = 'hello'\nSTATUS_CODE = 202\n",
    )
    app = make_app("integration_config_file_load_and_route_reads_setting")
    app.update_config(settings)

    @app.get("/hello")
    async def hello(request):
        return json(
            {
                "greeting": request.app.config.GREETING,
                "path": request.app.url_for("hello"),
            },
            status=request.app.config.STATUS_CODE,
        )

    _, response = run_asgi(app, "get", app.url_for("hello"))

    assert response.status == 202
    assert response.json == {"greeting": "hello", "path": "/hello"}


@pytest.mark.depends_on(
    "test_config_env_casts_basic_types",
    "test_config_detailed_converter_uses_defaults",
    "test_request_json_body_args_token_and_path",
)
def test_env_config_and_detailed_converter_drive_handler_response(
    monkeypatch,
):
    monkeypatch.setenv("SANIC_PORT", "7010")
    config = Config(
        defaults={"PORT": 7000},
        converters=[DefaultsCastConverter()],
    )
    app = Sanic(
        "integration_env_config_and_detailed_converter_drive_handler_response",
        config=config,
        configure_logging=False,
    )
    app.config.USE_UVLOOP = False

    @app.post("/scale")
    async def scale(request):
        return json(
            {
                "base": request.json["base"],
                "port": request.app.config.PORT,
                "token": request.token,
            }
        )

    _, response = run_asgi(
        app,
        "post",
        "/scale",
        json={"base": 5},
        headers={"Authorization": "Bearer visible"},
    )

    assert response.json == {"base": 5, "port": 7010, "token": "visible"}


@pytest.mark.depends_on(
    "test_blueprint_group_merges_prefixes_and_name_prefix",
    "test_blueprint_route_prefix_and_name_lookup",
)
def test_blueprint_group_route_names_and_asgi_client_calls():
    app = make_app("integration_blueprint_group_route_names")
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

    alpha_path = app.url_for("bundle_one.alpha")
    beta_path = app.url_for("bundle_two.beta")
    _, alpha_response = run_asgi(app, "get", alpha_path)
    _, beta_response = run_asgi(app, "get", beta_path)

    assert (alpha_path, alpha_response.text) == ("/api/one/alpha", "alpha")
    assert (beta_path, beta_response.text) == ("/api/two/beta", "beta")


@pytest.mark.depends_on(
    "test_static_serves_file_with_content_type",
    "test_url_for_builds_static_filename_path",
)
def test_static_file_url_for_and_content_round_trip(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    write_text(root / "asset.txt", "asset-body")
    app = make_app("integration_static_file_url_for_and_content")
    app.static("/assets", root)

    asset_url = app.url_for("static", filename="asset.txt")
    _, response = run_asgi(app, "get", asset_url)

    assert asset_url == "/assets/asset.txt"
    assert response.text == "asset-body"
    assert response.headers.get("content-type").startswith("text/plain")


@pytest.mark.depends_on(
    "test_request_json_body_args_token_and_path",
    "test_response_text_html_json_raw_helpers",
)
def test_request_and_response_helpers_work_together():
    app = make_app("integration_request_and_response_helpers")

    @app.post("/echo/<name>")
    async def echo(request, name):
        return json(
            {
                "name": name,
                "body": request.json["body"],
                "page": request.args.get("page"),
                "token": request.token,
            },
            status=201,
        )

    _, response = run_asgi(
        app,
        "post",
        "/echo/sanic?page=3",
        json={"body": "payload"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status == 201
    assert response.json == {
        "name": "sanic",
        "body": "payload",
        "page": "3",
        "token": "token",
    }


@pytest.mark.depends_on(
    "test_request_form_fields_and_file_upload",
    "test_response_add_and_delete_cookie_headers",
)
def test_form_upload_and_response_cookie_workflow(tmp_path):
    upload = write_text(tmp_path / "payload.txt", "uploaded")
    app = make_app("integration_form_upload_and_response_cookie")

    @app.post("/upload")
    async def upload_route(request):
        uploaded = request.files.get("upload")
        response = text(
            f"{request.form.get('label')}|"
            f"{uploaded.name}|{uploaded.body.decode()}"
        )
        response.add_cookie("upload", "accepted", path="/")
        return response

    with upload.open("rb") as stream:
        _, response = run_asgi(
            app,
            "post",
            "/upload",
            data={"label": "asset"},
            files={"upload": stream},
        )

    assert response.text == "asset|payload.txt|uploaded"
    assert "upload=accepted" in response.headers.get("set-cookie")


@pytest.mark.depends_on(
    "test_request_and_response_middleware_run_in_order",
    "test_request_middleware_can_short_circuit_with_response",
)
def test_middleware_gate_and_header_workflow():
    app = make_app("integration_middleware_gate_and_header")

    @app.on_request
    async def gate(request):
        if request.headers.get("x-allow") != "yes":
            return text("denied", status=401)
        request.ctx.allowed = "yes"

    @app.on_response
    async def add_header(request, response):
        if hasattr(request.ctx, "allowed"):
            response.headers["x-allowed"] = request.ctx.allowed

    @app.get("/protected")
    async def protected(request):
        return text("allowed")

    _, denied = run_asgi(app, "get", "/protected")
    _, allowed = run_asgi(app, "get", "/protected", headers={"X-Allow": "yes"})

    assert denied.status == 401
    assert denied.text == "denied"
    assert allowed.text == "allowed"
    assert allowed.headers.get("x-allowed") == "yes"


@pytest.mark.depends_on(
    "test_listener_hooks_run_around_asgi_request",
    "test_multiple_middleware_priorities_affect_order",
)
def test_listener_and_middleware_order_with_multiple_requests():
    order = []
    app = make_app("integration_listener_and_middleware_order")

    @app.before_server_start
    async def before(app):
        order.append("before")

    @app.after_server_stop
    async def after(app):
        order.append("after")

    @app.on_request(priority=99)
    async def high(request):
        order.append("high")

    @app.on_request(priority=0)
    async def low(request):
        order.append("low")

    @app.get("/order")
    async def order_route(request):
        order.append("handler")
        return text(",".join(order[-3:]))

    _, first = run_asgi(app, "get", "/order")
    _, second = run_asgi(app, "get", "/order")

    assert first.text == "high,low,handler"
    assert second.text == "high,low,handler"
    assert order == [
        "before",
        "high",
        "low",
        "handler",
        "after",
        "before",
        "high",
        "low",
        "handler",
        "after",
    ]


@pytest.mark.depends_on(
    "test_blueprint_middleware_modifies_headers",
    "test_blueprint_route_prefix_and_name_lookup",
)
def test_blueprint_middleware_applies_to_blueprint_route_only():
    app = make_app("integration_blueprint_middleware_route_only")
    bp = Blueprint("section", url_prefix="/section")

    @bp.middleware("response")
    async def bp_header(request, response):
        response.headers["x-section"] = "only"

    @bp.get("/inside")
    async def inside(request):
        return text("inside")

    @app.get("/outside")
    async def outside(request):
        return text("outside")

    app.blueprint(bp)
    _, inside_response = run_asgi(app, "get", "/section/inside")
    _, outside_response = run_asgi(app, "get", "/outside")

    assert inside_response.headers.get("x-section") == "only"
    assert outside_response.headers.get("x-section") is None


@pytest.mark.depends_on(
    "test_url_for_builds_query_and_anchor_paths",
    "test_blueprint_route_prefix_and_name_lookup",
    "test_url_for_builds_static_filename_path",
)
def test_url_for_query_blueprint_and_static_paths_from_one_app(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    write_text(root / "asset.txt", "asset")
    app = make_app("integration_url_for_query_blueprint_static")
    app.static("/files", root)
    bp = Blueprint("links", url_prefix="/links")

    @app.get("/search")
    async def search(request):
        return text("search")

    @bp.get("/target")
    async def target(request):
        return text("target")

    app.blueprint(bp)

    assert app.url_for("search", query="x", _anchor="top") == (
        "/search?query=x#top"
    )
    assert app.url_for("links.target") == "/links/target"
    assert app.url_for("static", filename="asset.txt") == "/files/asset.txt"


@pytest.mark.depends_on(
    "test_config_register_type_casts_custom_value",
    "test_request_json_body_args_token_and_path",
)
def test_config_custom_converter_and_handler_json_workflow(monkeypatch):
    monkeypatch.setenv("SANIC_ENDPOINT", "api:443")
    config = Config(converters=[PairConverter()])
    app = Sanic(
        "integration_config_custom_converter_handler_json",
        config=config,
        configure_logging=False,
    )
    app.config.USE_UVLOOP = False

    @app.post("/endpoint")
    async def endpoint(request):
        return json(
            {
                "endpoint": request.app.config.ENDPOINT,
                "payload": request.json["payload"],
            }
        )

    _, response = run_asgi(
        app,
        "post",
        "/endpoint",
        json={"payload": "ok"},
    )

    assert response.json == {
        "endpoint": {"host": "api", "port": 443},
        "payload": "ok",
    }


@pytest.mark.depends_on(
    "test_config_loads_uppercase_from_mapping_and_instance",
    "test_config_loads_uppercase_from_file",
)
def test_config_file_and_instance_merge_before_request(tmp_path):
    settings = write_text(tmp_path / "settings.py", "FILE_VALUE = 'file'\n")
    app = make_app("integration_config_file_and_instance_merge")
    app.update_config(settings)
    app.config.load(ObjectSettings())

    @app.get("/settings")
    async def settings_route(request):
        return json(
            {
                "file": request.app.config.FILE_VALUE,
                "object": request.app.config.OBJECT_VALUE,
                "derived": request.app.config.DERIVED_VALUE,
                "lower": "lower_value" in request.app.config,
            }
        )

    _, response = run_asgi(app, "get", "/settings")

    assert response.json == {
        "file": "file",
        "object": "object",
        "derived": "derived",
        "lower": False,
    }


@pytest.mark.depends_on(
    "test_response_json_mutators_update_array_and_object",
    "test_request_json_body_args_token_and_path",
)
def test_response_json_mutation_survives_handler_round_trip():
    app = make_app("integration_response_json_mutation_round_trip")

    @app.post("/list")
    async def list_route(request):
        response = json([request.json["start"]])
        response.append("middle")
        response.extend(["end"])
        return response

    _, response = run_asgi(app, "post", "/list", json={"start": "begin"})

    assert response.json == ["begin", "middle", "end"]


@pytest.mark.depends_on(
    "test_response_empty_and_redirect_helpers",
    "test_route_get_post_and_method_not_allowed",
)
def test_empty_and_redirect_endpoints_share_route_table():
    app = make_app("integration_empty_and_redirect_endpoints")

    @app.get("/empty")
    async def empty_route(request):
        return empty()

    @app.get("/jump")
    async def jump(request):
        return redirect("/empty")

    _, empty_response = run_asgi(app, "get", "/empty")
    _, redirect_response = run_asgi(app, "get", "/jump")

    assert empty_response.status == 204
    assert redirect_response.status == 302
    assert redirect_response.headers.get("location") == "/empty"


@pytest.mark.depends_on(
    "test_static_directory_serves_multiple_files",
    "test_url_for_builds_static_filename_path",
)
def test_static_directory_serves_multiple_entries_by_url_for(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    write_text(root / "one.txt", "one")
    write_text(root / "two.txt", "two")
    app = make_app("integration_static_directory_multiple_entries")
    app.static("/assets", root)

    one_url = app.url_for("static", filename="one.txt")
    two_url = app.url_for("static", filename="two.txt")
    _, one_response = run_asgi(app, "get", one_url)
    _, two_response = run_asgi(app, "get", two_url)

    assert one_url == "/assets/one.txt"
    assert two_url == "/assets/two.txt"
    assert (one_response.text, two_response.text) == ("one", "two")


@pytest.mark.depends_on(
    "test_request_raw_body_and_headers",
    "test_request_ip_method_and_safe_flags",
)
def test_request_fields_and_raw_body_available_in_handler():
    app = make_app("integration_request_fields_and_raw_body")

    @app.post("/inspect")
    async def inspect(request):
        return json(
            {
                "body": request.body.decode(),
                "header": request.headers.get("x-contract"),
                "ip": request.ip,
                "method": request.method,
                "safe": request.is_safe,
            }
        )

    _, response = run_asgi(
        app,
        "post",
        "/inspect",
        content=b"body",
        headers={"X-Contract": "visible"},
    )

    assert response.json == {
        "body": "body",
        "header": "visible",
        "ip": "mockserver",
        "method": "POST",
        "safe": False,
    }


@pytest.mark.depends_on(
    "test_blueprint_route_prefix_and_name_lookup",
    "test_url_for_builds_query_and_anchor_paths",
)
def test_blueprint_route_and_request_url_for_projection():
    app = make_app("integration_blueprint_route_request_url_for")
    bp = Blueprint("catalog", url_prefix="/catalog")

    @bp.get("/item")
    async def item(request):
        return text(request.url_for("catalog.item"))

    app.blueprint(bp)
    _, response = run_asgi(app, "get", app.url_for("catalog.item"))

    assert response.text.endswith("/catalog/item")
    assert "://" in response.text


@pytest.mark.depends_on(
    "test_response_add_and_delete_cookie_headers",
    "test_response_file_helper_reads_local_path",
)
def test_file_response_can_set_cookie_header(tmp_path):
    asset = write_text(tmp_path / "asset.txt", "download")
    app = make_app("integration_file_response_cookie")

    @app.get("/download")
    async def download(request):
        response = await file(asset)
        response.add_cookie("download", "ready", path="/")
        return response

    _, response = run_asgi(app, "get", "/download")

    assert response.text == "download"
    assert response.headers.get("content-type").startswith("text/plain")
    assert "download=ready" in response.headers.get("set-cookie")


@pytest.mark.depends_on(
    "test_config_update_config_only_keeps_uppercase_and_setters",
    "test_request_and_response_middleware_run_in_order",
)
def test_multiple_routes_use_shared_config_and_request_context():
    app = make_app("integration_multiple_routes_shared_config_ctx")
    app.update_config({"USER_LABEL": "tester", "lower": "ignored"})

    @app.on_request
    async def attach_user(request):
        request.ctx.user = request.app.config.USER_LABEL

    @app.on_response
    async def tag_response(request, response):
        response.headers["x-user"] = request.ctx.user

    @app.get("/who")
    async def who(request):
        return text(request.ctx.user)

    @app.get("/where")
    async def where(request):
        return text(f"{request.ctx.user}@{request.path}")

    _, who_response = run_asgi(app, "get", "/who")
    _, where_response = run_asgi(app, "get", "/where")

    assert who_response.text == "tester"
    assert where_response.text == "tester@/where"
    assert who_response.headers.get("x-user") == "tester"
    assert "lower" not in app.config


@pytest.mark.depends_on(
    "test_blueprint_group_merges_prefixes_and_name_prefix",
    "test_static_serves_file_with_content_type",
)
def test_nested_blueprint_and_static_routes_coexist(tmp_path):
    root = tmp_path / "public"
    root.mkdir()
    write_text(root / "asset.txt", "asset")
    app = make_app("integration_nested_blueprint_and_static_routes")
    app.static("/files", root)
    bp = Blueprint("one", url_prefix="/one")

    @bp.get("/alpha")
    async def alpha(request):
        return text("alpha")

    app.blueprint(
        Blueprint.group(bp, url_prefix="/api", name_prefix="bundle")
    )

    bp_url = app.url_for("bundle_one.alpha")
    static_url = app.url_for("static", filename="asset.txt")
    _, bp_response = run_asgi(app, "get", bp_url)
    _, static_response = run_asgi(app, "get", static_url)

    assert bp_url == "/api/one/alpha"
    assert static_url == "/files/asset.txt"
    assert bp_response.text == "alpha"
    assert static_response.text == "asset"


@pytest.mark.depends_on(
    "test_response_add_and_delete_cookie_headers",
    "test_request_raw_body_and_headers",
)
def test_cookie_response_and_followup_request_round_trip():
    app = make_app("integration_cookie_followup_round_trip")

    @app.get("/set")
    async def set_cookie(request):
        response = text("set")
        response.add_cookie("theme", "dark", path="/", secure=False)
        return response

    @app.get("/read")
    async def read_cookie(request):
        return text(request.cookies.get("theme", "missing"))

    _, first = run_asgi(app, "get", "/set")
    cookie = first.headers.get("set-cookie").split(";", 1)[0]
    _, second = run_asgi(app, "get", "/read", headers={"Cookie": cookie})

    assert first.text == "set"
    assert second.text == "dark"


@pytest.mark.depends_on(
    "test_request_query_lists_and_path_parameters",
    "test_blueprint_route_prefix_and_name_lookup",
)
def test_dynamic_route_url_generation_and_match_info_agree():
    app = make_app("integration_dynamic_route_match_info")

    @app.get("/items/<item>", name="item_detail")
    async def item_detail(request, item):
        return json(
            {
                "argument": item,
                "match": request.match_info["item"],
                "url": request.url_for("item_detail", item=item),
            }
        )

    path = app.url_for("item_detail", item="blue")
    _, response = run_asgi(app, "get", path)

    assert path == "/items/blue"
    assert response.json["argument"] == response.json["match"] == "blue"
    assert response.json["url"].endswith("/items/blue")
    assert "://" in response.json["url"]


@pytest.mark.depends_on(
    "test_request_json_body_args_token_and_path",
    "test_response_text_html_json_raw_helpers",
)
def test_accept_and_content_type_drive_handler_representation():
    app = make_app("integration_accept_content_type_projection")

    @app.post("/negotiate")
    async def negotiate(request):
        match = request.accept.match("application/json", "text/plain")
        return json(
            {
                "content_type": request.content_type,
                "accepted": match.mime,
                "payload": request.json["value"],
            }
        )

    _, response = run_asgi(
        app,
        "post",
        "/negotiate",
        json={"value": "ok"},
        headers={"Accept": "text/plain;q=0.4, application/json"},
    )

    assert response.json == {
        "content_type": "application/json",
        "accepted": "application/json",
        "payload": "ok",
    }


@pytest.mark.depends_on(
    "test_request_json_body_args_token_and_path",
    "test_request_ip_method_and_safe_flags",
)
def test_basic_credentials_and_route_name_project_into_response():
    app = make_app("integration_credentials_and_route_name")

    @app.get("/identity", name="identity")
    async def identity(request):
        return json(
            {
                "auth_type": request.credentials.auth_type,
                "username": request.credentials.username,
                "password": request.credentials.password,
                "name": request.name,
                "endpoint": request.endpoint,
            }
        )

    encoded = base64.b64encode(b"ada:secret").decode("ascii")
    _, response = run_asgi(
        app,
        "get",
        "/identity",
        headers={"Authorization": f"Basic {encoded}"},
    )

    assert response.json == {
        "auth_type": "Basic",
        "username": "ada",
        "password": "secret",
        "name": "integration_credentials_and_route_name.identity",
        "endpoint": "integration_credentials_and_route_name.identity",
    }


@pytest.mark.depends_on("test_request_and_response_middleware_run_in_order")
def test_exception_handler_projects_public_error_response():
    app = make_app("integration_exception_handler_projection")

    @app.exception(ValueError)
    async def handle_value_error(request, exception):
        return json({"error": str(exception)}, status=422)

    @app.get("/fail")
    async def fail(request):
        raise ValueError("bad value")

    _, response = run_asgi(app, "get", "/fail")

    assert response.status == 422
    assert response.json == {"error": "bad value"}


@pytest.mark.depends_on(
    "test_request_query_lists_and_path_parameters",
    "test_request_raw_body_and_headers",
)
def test_query_args_keep_blank_values_and_order_in_handler():
    app = make_app("integration_query_args_keep_blank_values")

    @app.get("/query")
    async def query(request):
        return json(
            {
                "grouped": request.get_args(keep_blank_values=True),
                "ordered": request.get_query_args(keep_blank_values=True),
            }
        )

    _, response = run_asgi(app, "get", "/query?tag=&tag=two&empty=")

    assert response.json == {
        "grouped": {"tag": ["", "two"], "empty": [""]},
        "ordered": [["tag", ""], ["tag", "two"], ["empty", ""]],
    }


@pytest.mark.depends_on(
    "test_route_get_post_and_method_not_allowed",
    "test_url_for_builds_query_and_anchor_paths",
)
def test_patch_and_delete_named_routes_share_url_projection():
    app = make_app("integration_patch_delete_named_routes")

    @app.patch("/records/<record>", name="update_record")
    async def update_record(request, record):
        return text(f"patch:{record}")

    @app.delete("/records/<record>", name="remove_record")
    async def remove_record(request, record):
        return text(f"delete:{record}")

    update_path = app.url_for("update_record", record="r1")
    remove_path = app.url_for("remove_record", record="r1")
    _, update_response = run_asgi(app, "patch", update_path)
    _, remove_response = run_asgi(app, "delete", remove_path)

    assert update_path == remove_path == "/records/r1"
    assert update_response.text == "patch:r1"
    assert remove_response.text == "delete:r1"


@pytest.mark.depends_on(
    "test_blueprint_route_prefix_and_name_lookup",
    "test_config_update_config_only_keeps_uppercase_and_setters",
)
def test_blueprint_route_reads_app_config_and_request_context():
    app = make_app("integration_blueprint_config_context")
    app.config.update_config({"LABEL": "catalog"})
    bp = Blueprint("catalog", url_prefix="/catalog")

    @bp.get("/<item>")
    async def item(request, item):
        request.ctx.seen = f"{request.app.config.LABEL}:{item}"
        return text(request.ctx.seen)

    app.blueprint(bp)
    path = app.url_for("catalog.item", item="book")
    _, response = run_asgi(app, "get", path)

    assert path == "/catalog/book"
    assert response.text == "catalog:book"


@pytest.mark.depends_on(
    "test_response_text_html_json_raw_helpers",
    "test_route_get_post_and_method_not_allowed",
)
def test_html_and_raw_endpoints_preserve_semantic_response_fields():
    app = make_app("integration_html_raw_response_fields")

    @app.get("/html")
    async def html_route(request):
        return html("<strong>ok</strong>")

    @app.get("/raw")
    async def raw_route(request):
        return raw(b"\x00\x01", content_type="application/octet-stream")

    _, html_response = run_asgi(app, "get", "/html")
    _, raw_response = run_asgi(app, "get", "/raw")

    assert html_response.text == "<strong>ok</strong>"
    assert html_response.headers.get("content-type").startswith("text/html")
    assert raw_response.content == b"\x00\x01"
    assert raw_response.headers.get("content-type") == "application/octet-stream"


@pytest.mark.depends_on(
    "test_request_query_lists_and_path_parameters",
    "test_request_ip_method_and_safe_flags",
)
def test_typed_route_projects_method_flags_and_uri_template():
    app = make_app("integration_typed_route_method_flags")

    @app.put("/items/<item:int>")
    async def replace_item(request, item):
        return json(
            {
                "item": item,
                "method": request.method,
                "safe": request.is_safe,
                "idempotent": request.is_idempotent,
                "cacheable": request.is_cacheable,
                "template": request.uri_template,
            }
        )

    _, response = run_asgi(app, "put", "/items/42")

    assert response.json == {
        "item": 42,
        "method": "PUT",
        "safe": False,
        "idempotent": True,
        "cacheable": False,
        "template": "/items/<item:int>",
    }
