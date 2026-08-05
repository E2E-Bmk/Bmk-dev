from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from litestar import (
    Controller,
    HttpMethod,
    Litestar,
    MediaType,
    Request,
    Response,
    Router,
    delete,
    get,
    patch,
    post,
    put,
    route,
)
from litestar.di import NamedDependency, Provide
from litestar.exceptions import NoRouteMatchFoundException, PermissionDeniedException
from litestar.params import FromHeader, FromPath, FromQuery
from litestar.testing import create_test_client

from conftest import Item, body, content_type


def test_typed_path_parameter_is_converted() -> None:
    @get("/items/{item_id:int}", media_type=MediaType.TEXT, sync_to_thread=False)
    def read_item(item_id: FromPath[int]) -> str:
        return str(item_id + 1)

    with create_test_client(read_item) as client:
        response = client.get("/items/4")
    assert response.status_code == 200
    assert response.text == "5"


def test_typed_query_parameter_is_converted() -> None:
    @get("/sum", media_type=MediaType.TEXT, sync_to_thread=False)
    def add_values(first: FromQuery[int], second: FromQuery[int]) -> str:
        return str(first + second)

    with create_test_client(add_values) as client:
        response = client.get("/sum?first=2&second=5")
    assert response.status_code == 200
    assert response.text == "7"


def test_default_query_parameter_is_used() -> None:
    @get("/page", media_type=MediaType.TEXT, sync_to_thread=False)
    def page_number(page: FromQuery[int] = 1) -> str:
        return str(page)

    with create_test_client(page_number) as client:
        response = client.get("/page")
    assert response.status_code == 200
    assert response.text == "1"


def test_repeated_query_values_fill_list() -> None:
    @get("/tags", sync_to_thread=False)
    def tags(values: FromQuery[list[int]]) -> dict[str, Any]:
        return {"values": values}

    with create_test_client(tags) as client:
        response = client.get("/tags?values=2&values=4")
    assert response.status_code == 200
    assert body(response) == {"values": [2, 4]}


def test_invalid_typed_path_returns_bad_request() -> None:
    @get("/items/{item_id:int}", sync_to_thread=False)
    def read_item(item_id: FromPath[int]) -> int:
        return item_id

    with create_test_client(read_item) as client:
        response = client.get("/items/nope")
    assert response.status_code == 404


def test_missing_required_query_returns_bad_request() -> None:
    @get("/search", sync_to_thread=False)
    def search(term: FromQuery[str]) -> dict[str, str]:
        return {"term": term}

    with create_test_client(search) as client:
        response = client.get("/search")
    assert response.status_code == 400


def test_json_body_dataclass_is_parsed() -> None:
    @post("/items", sync_to_thread=False)
    def create_item(data: Item) -> Item:
        return data

    with create_test_client(create_item) as client:
        response = client.post("/items", json={"name": "pen", "quantity": 3})
    assert response.status_code == 201
    assert body(response) == {"name": "pen", "quantity": 3}


def test_invalid_json_body_returns_bad_request() -> None:
    @post("/items", sync_to_thread=False)
    def create_item(data: Item) -> Item:
        return data

    with create_test_client(create_item) as client:
        response = client.post("/items", content=b"{")
    assert response.status_code == 400


def test_request_headers_are_injected() -> None:
    @get("/header", media_type=MediaType.TEXT, sync_to_thread=False)
    def read_header(token: FromHeader[str]) -> str:
        return token

    with create_test_client(read_header) as client:
        response = client.get("/header", headers={"token": "abc"})
    assert response.status_code == 200
    assert response.text == "abc"


def test_request_object_exposes_path() -> None:
    @get("/inspect", media_type=MediaType.TEXT, sync_to_thread=False)
    def inspect_request(request: Request[Any, Any, Any]) -> str:
        return request.url.path

    with create_test_client(inspect_request) as client:
        response = client.get("/inspect")
    assert response.status_code == 200
    assert response.text == "/inspect"


def test_get_defaults_to_ok() -> None:
    @get("/read", sync_to_thread=False)
    def read() -> dict[str, bool]:
        return {"ok": True}

    with create_test_client(read) as client:
        response = client.get("/read")
    assert response.status_code == 200


def test_post_defaults_to_created() -> None:
    @post("/create", sync_to_thread=False)
    def create() -> dict[str, bool]:
        return {"created": True}

    with create_test_client(create) as client:
        response = client.post("/create")
    assert response.status_code == 201


def test_put_defaults_to_ok() -> None:
    @put("/replace", sync_to_thread=False)
    def replace() -> dict[str, bool]:
        return {"replaced": True}

    with create_test_client(replace) as client:
        response = client.put("/replace")
    assert response.status_code == 200


def test_patch_defaults_to_ok() -> None:
    @patch("/change", sync_to_thread=False)
    def change() -> dict[str, bool]:
        return {"changed": True}

    with create_test_client(change) as client:
        response = client.patch("/change")
    assert response.status_code == 200


def test_delete_defaults_to_no_content() -> None:
    @delete("/remove", sync_to_thread=False)
    def remove() -> None:
        return None

    with create_test_client(remove) as client:
        response = client.delete("/remove")
    assert response.status_code == 204
    assert response.content == b""


def test_dict_return_is_json() -> None:
    @get("/json", sync_to_thread=False)
    def json_result() -> dict[str, Any]:
        return {"answer": 42}

    with create_test_client(json_result) as client:
        response = client.get("/json")
    assert content_type(response) == "application/json"
    assert body(response) == {"answer": 42}


def test_text_media_type_sets_plain_content() -> None:
    @get("/text", media_type=MediaType.TEXT, sync_to_thread=False)
    def text_result() -> str:
        return "ready"

    with create_test_client(text_result) as client:
        response = client.get("/text")
    assert content_type(response) == "text/plain"
    assert response.text == "ready"


def test_html_media_type_sets_html_content() -> None:
    @get("/page", media_type=MediaType.HTML, sync_to_thread=False)
    def html_result() -> str:
        return "<p>ready</p>"

    with create_test_client(html_result) as client:
        response = client.get("/page")
    assert content_type(response) == "text/html"
    assert response.text == "<p>ready</p>"


def test_explicit_response_preserves_status_and_header() -> None:
    @get("/custom", sync_to_thread=False)
    def custom() -> Response[dict[str, str]]:
        return Response(
            content={"state": "ready"},
            status_code=202,
            headers={"x-state": "custom"},
        )

    with create_test_client(custom) as client:
        response = client.get("/custom")
    assert response.status_code == 202
    assert response.headers["x-state"] == "custom"
    assert body(response) == {"state": "ready"}


def test_named_dependency_is_injected() -> None:
    def supply() -> str:
        return "provided"

    @get("/dependency", sync_to_thread=False)
    def dependency(value: NamedDependency[str]) -> dict[str, str]:
        return {"value": value}

    with create_test_client(
        dependency,
        dependencies={"value": Provide(supply, sync_to_thread=False)},
    ) as client:
        response = client.get("/dependency")
    assert body(response) == {"value": "provided"}


def test_dependency_receives_query_value() -> None:
    def supply(prefix: FromQuery[str]) -> str:
        return prefix + "-suffix"

    @get("/dependency", media_type=MediaType.TEXT, sync_to_thread=False)
    def dependency(value: NamedDependency[str]) -> str:
        return value

    with create_test_client(
        dependency,
        dependencies={"value": Provide(supply, sync_to_thread=False)},
    ) as client:
        response = client.get("/dependency?prefix=base")
    assert response.text == "base-suffix"


def test_router_dependency_is_injected() -> None:
    def supply() -> str:
        return "router"

    @get("/value", sync_to_thread=False)
    def value(source: NamedDependency[str]) -> dict[str, str]:
        return {"source": source}

    router = Router(
        "/api",
        route_handlers=[value],
        dependencies={"source": Provide(supply, sync_to_thread=False)},
    )
    with create_test_client(router) as client:
        response = client.get("/api/value")
    assert body(response) == {"source": "router"}


def test_guard_allows_authorized_request() -> None:
    def guard(connection: Any, route_handler: Any) -> None:
        if connection.headers.get("x-role") != "admin":
            raise PermissionDeniedException()

    @get("/secure", guards=[guard], sync_to_thread=False)
    def secure() -> str:
        return "ok"

    with create_test_client(secure) as client:
        response = client.get("/secure", headers={"x-role": "admin"})
    assert response.status_code == 200
    assert response.text == "ok"


def test_guard_denies_unauthorized_request() -> None:
    def guard(connection: Any, route_handler: Any) -> None:
        if connection.headers.get("x-role") != "admin":
            raise PermissionDeniedException()

    @get("/secure", guards=[guard], sync_to_thread=False)
    def secure() -> str:
        return "ok"

    with create_test_client(secure) as client:
        response = client.get("/secure")
    assert response.status_code == 403


def test_router_prefix_is_applied() -> None:
    @get("/health", sync_to_thread=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    router = Router("/v1", route_handlers=[health])
    with create_test_client(router) as client:
        response = client.get("/v1/health")
    assert response.status_code == 200
    assert body(response) == {"status": "ok"}


def test_controller_prefix_is_applied() -> None:
    class HealthController(Controller):
        path = "/system"

        @get("/health", sync_to_thread=False)
        def health(self) -> dict[str, str]:
            return {"status": "ok"}

    with create_test_client(HealthController) as client:
        response = client.get("/system/health")
    assert response.status_code == 200


def test_nested_router_prefixes_are_composed() -> None:
    @get("/ready", sync_to_thread=False)
    def ready() -> str:
        return "ready"

    inner = Router("/inner", route_handlers=[ready])
    outer = Router("/outer", route_handlers=[inner])
    with create_test_client(outer) as client:
        response = client.get("/outer/inner/ready")
    assert response.status_code == 200
    assert response.text == "ready"


def test_controller_exposes_multiple_methods() -> None:
    class ResourceController(Controller):
        path = "/resource"

        @get(sync_to_thread=False)
        def read(self) -> dict[str, str]:
            return {"method": "get"}

        @post(sync_to_thread=False)
        def create(self) -> dict[str, str]:
            return {"method": "post"}

    with create_test_client(ResourceController) as client:
        get_response = client.get("/resource")
        post_response = client.post("/resource")
    assert body(get_response) == {"method": "get"}
    assert body(post_response) == {"method": "post"}


def test_controller_class_can_be_reused() -> None:
    class MessageController(Controller):
        path = "/messages"

        @get(sync_to_thread=False)
        def list_messages(self) -> dict[str, str]:
            return {"source": "controller"}

    first = Router("/first", route_handlers=[MessageController])
    second = Router("/second", route_handlers=[MessageController])
    with create_test_client([first, second]) as client:
        first_response = client.get("/first/messages")
        second_response = client.get("/second/messages")
    assert first_response.status_code == 200
    assert second_response.status_code == 200


def test_multiple_route_paths_are_served() -> None:
    @get(["/one", "/two"], sync_to_thread=False)
    def multi() -> dict[str, bool]:
        return {"ok": True}

    with create_test_client(multi) as client:
        first = client.get("/one")
        second = client.get("/two")
    assert first.status_code == 200
    assert second.status_code == 200


def test_path_mismatch_returns_not_found() -> None:
    @get("/expected", sync_to_thread=False)
    def expected() -> str:
        return "ok"

    with create_test_client(expected) as client:
        response = client.get("/other")
    assert response.status_code == 404


def test_unsupported_method_returns_method_not_allowed() -> None:
    @get("/method", sync_to_thread=False)
    def method() -> str:
        return "ok"

    with create_test_client(method) as client:
        response = client.post("/method")
    assert response.status_code == 405
    assert "GET" in response.headers.get("allow", "")


def test_auto_options_advertises_methods() -> None:
    @get("/options", sync_to_thread=False)
    def options() -> str:
        return "ok"

    with create_test_client(options) as client:
        response = client.options("/options")
    assert response.status_code == 204
    assert "GET" in response.headers.get("allow", "")


def test_route_handler_name_is_reversible() -> None:
    @get("/users/{user_id:int}", name="user-detail", sync_to_thread=False)
    def user_detail(user_id: FromPath[int]) -> dict[str, int]:
        return {"id": user_id}

    app = Litestar(route_handlers=[user_detail])
    assert app.route_reverse("user-detail", user_id=8) == "/users/8"


def test_route_reverse_accepts_handler() -> None:
    @get("/health", sync_to_thread=False)
    def health() -> str:
        return "ok"

    app = Litestar(route_handlers=[health])
    assert app.route_reverse(health) == "/health"


def test_route_reverse_rejects_missing_parameter() -> None:
    @get("/users/{user_id:int}", name="user-detail", sync_to_thread=False)
    def user_detail(user_id: FromPath[int]) -> None:
        return None

    app = Litestar(route_handlers=[user_detail])
    with pytest.raises(NoRouteMatchFoundException):
        app.route_reverse("user-detail")


def test_route_reverse_rejects_wrong_parameter_type() -> None:
    @get("/users/{user_id:int}", name="user-detail", sync_to_thread=False)
    def user_detail(user_id: FromPath[int]) -> None:
        return None

    app = Litestar(route_handlers=[user_detail])
    with pytest.raises(NoRouteMatchFoundException):
        app.route_reverse("user-detail", user_id="not-an-int")


def test_public_routes_expose_registered_paths() -> None:
    @get("/one", sync_to_thread=False)
    def one() -> str:
        return "one"

    @post("/two", sync_to_thread=False)
    def two() -> str:
        return "two"

    app = Litestar(route_handlers=[one, two], openapi_config=None)
    paths = {route_item.path for route_item in app.routes}
    assert "/one" in paths
    assert "/two" in paths


def test_openapi_contains_typed_path_parameter() -> None:
    @get("/users/{user_id:int}", sync_to_thread=False)
    def user(user_id: FromPath[int]) -> dict[str, int]:
        return {"id": user_id}

    schema = Litestar(route_handlers=[user]).openapi_schema.to_schema()
    operation = schema["paths"]["/users/{user_id}"]["get"]
    parameter = next(item for item in operation["parameters"] if item["name"] == "user_id")
    assert parameter["in"] == "path"
    assert parameter["schema"]["type"] == "integer"


def test_openapi_contains_query_parameter() -> None:
    @get("/search", sync_to_thread=False)
    def search(term: FromQuery[str]) -> dict[str, str]:
        return {"term": term}

    schema = Litestar(route_handlers=[search]).openapi_schema.to_schema()
    operation = schema["paths"]["/search"]["get"]
    parameter = next(item for item in operation["parameters"] if item["name"] == "term")
    assert parameter["in"] == "query"
    assert parameter["required"] is True


def test_openapi_contains_response_media_type() -> None:
    @get("/plain", media_type=MediaType.TEXT, sync_to_thread=False)
    def plain() -> str:
        return "plain"

    schema = Litestar(route_handlers=[plain]).openapi_schema.to_schema()
    content = schema["paths"]["/plain"]["get"]["responses"]["200"]["content"]
    assert "text/plain" in content


def test_openapi_hides_excluded_route() -> None:
    @get("/visible", sync_to_thread=False)
    def visible() -> str:
        return "visible"

    @get("/hidden", include_in_schema=False, sync_to_thread=False)
    def hidden() -> str:
        return "hidden"

    schema = Litestar(route_handlers=[visible, hidden]).openapi_schema.to_schema()
    assert "/visible" in schema["paths"]
    assert "/hidden" not in schema["paths"]


def test_openapi_uses_custom_title_and_version() -> None:
    @get("/versioned", sync_to_thread=False)
    def versioned() -> str:
        return "ok"

    from litestar.openapi.config import OpenAPIConfig

    app = Litestar(
        route_handlers=[versioned],
        openapi_config=OpenAPIConfig(title="Catalog", version="2.1"),
    )
    schema = app.openapi_schema.to_schema()
    assert schema["info"]["title"] == "Catalog"
    assert schema["info"]["version"] == "2.1"


def test_route_decorator_combines_methods() -> None:
    @route(
        "/same",
        http_method=[HttpMethod.GET, HttpMethod.POST],
        status_code=200,
        sync_to_thread=False,
    )
    def same() -> dict[str, str]:
        return {"ok": "yes"}

    with create_test_client(same) as client:
        get_response = client.get("/same")
        post_response = client.post("/same")
    assert get_response.status_code == 200
    assert post_response.status_code == 200
