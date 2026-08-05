from __future__ import annotations

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
from litestar.exceptions import NotFoundException, PermissionDeniedException
from litestar.params import FromHeader, FromPath, FromQuery
from litestar.testing import TestClient, create_test_client

from conftest import Item, body, content_type


@pytest.mark.depends_on(
    "test_json_body_dataclass_is_parsed",
    "test_typed_path_parameter_is_converted",
    "test_delete_defaults_to_no_content",
)
def test_crud_state_workflow() -> None:
    records: dict[int, Item] = {1: Item("existing", 1)}

    @get("/items/{item_id:int}", sync_to_thread=False)
    def read(item_id: FromPath[int]) -> Item:
        try:
            return records[item_id]
        except KeyError as exc:
            raise NotFoundException() from exc

    @post("/items", sync_to_thread=False)
    def create(data: Item) -> Item:
        item_id = max(records, default=0) + 1
        records[item_id] = data
        return data

    @delete("/items/{item_id:int}", sync_to_thread=False)
    def remove(item_id: FromPath[int]) -> None:
        records.pop(item_id, None)

    with create_test_client([read, create, remove]) as client:
        created = client.post("/items", json={"name": "new", "quantity": 2})
        read_back = client.get("/items/2")
        removed = client.delete("/items/2")
        missing = client.get("/items/2")
    assert created.status_code == 201
    assert body(read_back) == {"name": "new", "quantity": 2}
    assert removed.status_code == 204
    assert missing.status_code == 404


@pytest.mark.depends_on(
    "test_nested_router_prefixes_are_composed",
    "test_controller_prefix_is_applied",
    "test_route_handler_name_is_reversible",
)
def test_nested_router_controller_reverse_and_http() -> None:
    class UserController(Controller):
        path = "/users"

        @get("/{user_id:int}", name="user-detail", sync_to_thread=False)
        def detail(self, user_id: FromPath[int]) -> dict[str, int]:
            return {"id": user_id}

    api = Router("/api", route_handlers=[UserController])
    app = Litestar(route_handlers=[Router("/v1", route_handlers=[api])])
    path = app.route_reverse("user-detail", user_id=12)
    with TestClient(app) as client:
        response = client.get(path)
    assert path == "/v1/api/users/12"
    assert response.status_code == 200
    assert body(response) == {"id": 12}


@pytest.mark.depends_on(
    "test_typed_query_parameter_is_converted",
    "test_invalid_typed_path_returns_bad_request",
    "test_missing_required_query_returns_bad_request",
)
def test_typed_request_validation_workflow() -> None:
    @get("/reports/{report_id:int}", sync_to_thread=False)
    def report(
        report_id: FromPath[int],
        limit: FromQuery[int],
    ) -> dict[str, int]:
        return {"report_id": report_id, "limit": limit}

    with create_test_client(report) as client:
        valid = client.get("/reports/9?limit=3")
        bad_path = client.get("/reports/nope?limit=3")
        missing_query = client.get("/reports/9")
    assert valid.status_code == 200
    assert body(valid) == {"report_id": 9, "limit": 3}
    assert bad_path.status_code == 404
    assert missing_query.status_code == 400


@pytest.mark.depends_on(
    "test_guard_allows_authorized_request",
    "test_guard_denies_unauthorized_request",
    "test_controller_exposes_multiple_methods",
)
def test_guarded_read_write_workflow() -> None:
    def admin_guard(connection: Any, route_handler: Any) -> None:
        if connection.headers.get("x-role") != "admin":
            raise PermissionDeniedException()

    @get("/settings", guards=[admin_guard], sync_to_thread=False)
    def settings() -> dict[str, str]:
        return {"mode": "private"}

    @post("/settings", guards=[admin_guard], sync_to_thread=False)
    def update_settings() -> dict[str, str]:
        return {"updated": "yes"}

    with create_test_client([settings, update_settings]) as client:
        denied = client.get("/settings")
        read = client.get("/settings", headers={"x-role": "admin"})
        write = client.post("/settings", headers={"x-role": "admin"})
    assert denied.status_code == 403
    assert body(read) == {"mode": "private"}
    assert write.status_code == 201
    assert body(write) == {"updated": "yes"}


@pytest.mark.depends_on(
    "test_named_dependency_is_injected",
    "test_dependency_receives_query_value",
    "test_dict_return_is_json",
)
def test_dependency_query_and_response_workflow() -> None:
    def prefix_value(prefix: FromQuery[str]) -> str:
        return prefix.upper()

    @get("/welcome", sync_to_thread=False)
    def welcome(value: NamedDependency[str]) -> dict[str, str]:
        return {"message": value + " welcome"}

    with create_test_client(
        welcome,
        dependencies={"value": Provide(prefix_value, sync_to_thread=False)},
    ) as client:
        first = client.get("/welcome?prefix=hello")
        second = client.get("/welcome?prefix=goodbye")
    assert body(first) == {"message": "HELLO welcome"}
    assert body(second) == {"message": "GOODBYE welcome"}


@pytest.mark.depends_on(
    "test_get_defaults_to_ok",
    "test_post_defaults_to_created",
    "test_put_defaults_to_ok",
    "test_patch_defaults_to_ok",
    "test_delete_defaults_to_no_content",
)
def test_response_defaults_across_resource_operations() -> None:
    @get("/resource", sync_to_thread=False)
    def read() -> dict[str, str]:
        return {"action": "read"}

    @post("/resource", sync_to_thread=False)
    def create() -> dict[str, str]:
        return {"action": "create"}

    @put("/resource", sync_to_thread=False)
    def replace() -> dict[str, str]:
        return {"action": "replace"}

    @patch("/resource", sync_to_thread=False)
    def change() -> dict[str, str]:
        return {"action": "change"}

    @delete("/resource", sync_to_thread=False)
    def remove() -> None:
        return None

    with create_test_client([read, create, replace, change, remove]) as client:
        responses = [
            client.get("/resource"),
            client.post("/resource"),
            client.put("/resource"),
            client.patch("/resource"),
            client.delete("/resource"),
        ]
    assert [response.status_code for response in responses] == [200, 201, 200, 200, 204]


@pytest.mark.depends_on(
    "test_route_decorator_combines_methods",
    "test_auto_options_advertises_methods",
    "test_unsupported_method_returns_method_not_allowed",
)
def test_multi_method_route_and_options_workflow() -> None:
    @route(
        "/multi",
        http_method=[HttpMethod.GET, HttpMethod.POST],
        status_code=200,
        sync_to_thread=False,
    )
    def multi() -> dict[str, str]:
        return {"ok": "yes"}

    with create_test_client(multi) as client:
        get_response = client.get("/multi")
        post_response = client.post("/multi")
        options_response = client.options("/multi")
        rejected = client.delete("/multi")
    assert get_response.status_code == 200
    assert post_response.status_code == 200
    assert options_response.status_code == 204
    assert "GET" in options_response.headers.get("allow", "")
    assert rejected.status_code == 405


@pytest.mark.depends_on(
    "test_typed_path_parameter_is_converted",
    "test_openapi_contains_typed_path_parameter",
    "test_route_handler_name_is_reversible",
)
def test_openapi_matches_live_typed_route() -> None:
    @get("/products/{product_id:int}", name="product", sync_to_thread=False)
    def product(product_id: FromPath[int]) -> dict[str, int]:
        return {"product_id": product_id}

    app = Litestar(route_handlers=[product])
    schema = app.openapi_schema.to_schema()
    with TestClient(app) as client:
        response = client.get(app.route_reverse("product", product_id=5))
    operation = schema["paths"]["/products/{product_id}"]["get"]
    parameter = next(item for item in operation["parameters"] if item["name"] == "product_id")
    assert response.status_code == 200
    assert "200" in operation["responses"]
    assert parameter["schema"]["type"] == "integer"
    assert body(response) == {"product_id": 5}


@pytest.mark.depends_on(
    "test_nested_router_prefixes_are_composed",
    "test_route_handler_name_is_reversible",
    "test_openapi_contains_typed_path_parameter",
)
def test_openapi_nested_route_matches_reverse() -> None:
    @get("/orders/{order_id:int}", name="order", sync_to_thread=False)
    def order(order_id: FromPath[int]) -> dict[str, int]:
        return {"order_id": order_id}

    app = Litestar(route_handlers=[Router("/api", route_handlers=[order])])
    schema = app.openapi_schema.to_schema()
    reversed_path = app.route_reverse("order", order_id=4)
    with TestClient(app) as client:
        response = client.get(reversed_path)
    assert reversed_path == "/api/orders/4"
    assert "/api/orders/{order_id}" in schema["paths"]
    assert response.status_code == 200


@pytest.mark.depends_on(
    "test_openapi_hides_excluded_route",
    "test_path_mismatch_returns_not_found",
    "test_dict_return_is_json",
)
def test_hidden_route_live_but_schema_excluded() -> None:
    @get("/public", sync_to_thread=False)
    def public() -> dict[str, bool]:
        return {"public": True}

    @get("/internal", include_in_schema=False, sync_to_thread=False)
    def internal() -> dict[str, bool]:
        return {"internal": True}

    app = Litestar(route_handlers=[public, internal])
    schema = app.openapi_schema.to_schema()
    with TestClient(app) as client:
        public_response = client.get("/public")
        internal_response = client.get("/internal")
    assert public_response.status_code == 200
    assert internal_response.status_code == 200
    assert "/public" in schema["paths"]
    assert "/internal" not in schema["paths"]


@pytest.mark.depends_on(
    "test_controller_class_can_be_reused",
    "test_router_prefix_is_applied",
    "test_controller_prefix_is_applied",
)
def test_controller_reused_under_two_prefixes() -> None:
    class CatalogController(Controller):
        path = "/catalog"

        @get("/count", media_type=MediaType.TEXT, sync_to_thread=False)
        def count(self) -> str:
            return "2"

    app = Litestar(
        route_handlers=[
            Router("/first", route_handlers=[CatalogController]),
            Router("/second", route_handlers=[CatalogController]),
        ]
    )
    with TestClient(app) as client:
        first = client.get("/first/catalog/count")
        second = client.get("/second/catalog/count")
    assert first.text == "2"
    assert second.text == "2"


@pytest.mark.depends_on(
    "test_multiple_route_paths_are_served",
    "test_route_handler_name_is_reversible",
    "test_route_reverse_accepts_handler",
)
def test_multi_path_handler_and_reverse_workflow() -> None:
    @get(["/alias", "/canonical"], name="alias", sync_to_thread=False)
    def alias() -> dict[str, str]:
        return {"path": "shared"}

    app = Litestar(route_handlers=[alias])
    with TestClient(app) as client:
        first = client.get("/alias")
        second = client.get("/canonical")
    assert app.route_reverse("alias") in {"/alias", "/canonical"}
    assert first.status_code == 200
    assert second.status_code == 200
    assert body(first) == body(second) == {"path": "shared"}


@pytest.mark.depends_on(
    "test_request_headers_are_injected",
    "test_request_object_exposes_path",
    "test_text_media_type_sets_plain_content",
)
def test_request_header_to_response_workflow() -> None:
    @get("/echo", media_type=MediaType.TEXT, sync_to_thread=False)
    def echo(request: Request[Any, Any, Any], trace: FromHeader[str]) -> str:
        return request.url.path + ":" + trace

    with create_test_client(echo) as client:
        response = client.get("/echo", headers={"trace": "abc"})
    assert response.status_code == 200
    assert content_type(response) == "text/plain"
    assert response.text == "/echo:abc"


@pytest.mark.depends_on(
    "test_router_dependency_is_injected",
    "test_named_dependency_is_injected",
    "test_nested_router_prefixes_are_composed",
)
def test_router_and_app_dependencies_combine() -> None:
    def app_value() -> str:
        return "app"

    def router_value() -> str:
        return "router"

    @get("/values", sync_to_thread=False)
    def values(
        app_source: NamedDependency[str],
        router_source: NamedDependency[str],
    ) -> dict[str, str]:
        return {"app": app_source, "router": router_source}

    router = Router(
        "/api",
        route_handlers=[values],
        dependencies={"router_source": Provide(router_value, sync_to_thread=False)},
    )
    app = Litestar(
        route_handlers=[router],
        dependencies={"app_source": Provide(app_value, sync_to_thread=False)},
    )
    with TestClient(app) as client:
        response = client.get("/api/values")
    assert body(response) == {"app": "app", "router": "router"}


@pytest.mark.depends_on(
    "test_guard_allows_authorized_request",
    "test_named_dependency_is_injected",
    "test_guard_denies_unauthorized_request",
)
def test_guard_and_dependency_order_workflow() -> None:
    def guard(connection: Any, route_handler: Any) -> None:
        if connection.headers.get("x-token") != "let-me-in":
            raise PermissionDeniedException()

    def label() -> str:
        return "guarded"

    @get("/entry", guards=[guard], sync_to_thread=False)
    def entry(value: NamedDependency[str]) -> dict[str, str]:
        return {"value": value}

    with create_test_client(
        entry,
        dependencies={"value": Provide(label, sync_to_thread=False)},
    ) as client:
        denied = client.get("/entry")
        allowed = client.get("/entry", headers={"x-token": "let-me-in"})
    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert body(allowed) == {"value": "guarded"}


@pytest.mark.depends_on(
    "test_missing_required_query_returns_bad_request",
    "test_path_mismatch_returns_not_found",
    "test_unsupported_method_returns_method_not_allowed",
)
def test_error_surface_workflow() -> None:
    @get("/lookup", sync_to_thread=False)
    def lookup(key: FromQuery[str]) -> dict[str, str]:
        return {"key": key}

    with create_test_client(lookup) as client:
        bad_request = client.get("/lookup")
        not_found = client.get("/missing")
        not_allowed = client.post("/lookup")
    assert bad_request.status_code == 400
    assert not_found.status_code == 404
    assert not_allowed.status_code == 405


@pytest.mark.depends_on(
    "test_explicit_response_preserves_status_and_header",
    "test_openapi_contains_response_media_type",
    "test_get_defaults_to_ok",
)
def test_custom_response_and_openapi_status_workflow() -> None:
    @get("/accepted", name="accepted", sync_to_thread=False)
    def accepted() -> Response[dict[str, str]]:
        return Response(
            content={"state": "queued"},
            status_code=202,
            headers={"x-state": "queued"},
        )

    app = Litestar(route_handlers=[accepted])
    schema = app.openapi_schema.to_schema()
    with TestClient(app) as client:
        response = client.get("/accepted")
    assert response.status_code == 202
    assert response.headers["x-state"] == "queued"
    assert "200" in schema["paths"]["/accepted"]["get"]["responses"]


@pytest.mark.depends_on(
    "test_json_body_dataclass_is_parsed",
    "test_dict_return_is_json",
    "test_post_defaults_to_created",
)
def test_json_body_round_trip_workflow() -> None:
    received: list[Item] = []

    @post("/payload", sync_to_thread=False)
    def payload(data: Item) -> dict[str, Any]:
        received.append(data)
        return {"name": data.name, "quantity": data.quantity}

    with create_test_client(payload) as client:
        first = client.post("/payload", json={"name": "a", "quantity": 1})
        second = client.post("/payload", json={"name": "b", "quantity": 2})
    assert first.status_code == 201
    assert second.status_code == 201
    assert [item.name for item in received] == ["a", "b"]
    assert body(second) == {"name": "b", "quantity": 2}


@pytest.mark.depends_on(
    "test_typed_query_parameter_is_converted",
    "test_default_query_parameter_is_used",
    "test_repeated_query_values_fill_list",
)
def test_query_filter_pagination_workflow() -> None:
    values = ["alpha", "beta", "gamma", "delta"]

    @get("/values", sync_to_thread=False)
    def filtered(
        tags: FromQuery[list[str]],
        prefix: FromQuery[str] = "",
        limit: FromQuery[int] = 2,
    ) -> dict[str, Any]:
        selected = [value for value in values if value.startswith(prefix)]
        return {"items": selected[:limit], "tags": tags}

    with create_test_client(filtered) as client:
        defaulted = client.get("/values?prefix=&tags=one&tags=two")
        narrowed = client.get("/values?prefix=g&limit=1&tags=solo")
    assert body(defaulted) == {"items": ["alpha", "beta"], "tags": ["one", "two"]}
    assert body(narrowed) == {"items": ["gamma"], "tags": ["solo"]}


@pytest.mark.depends_on(
    "test_controller_prefix_is_applied",
    "test_typed_path_parameter_is_converted",
    "test_route_reverse_accepts_handler",
)
def test_controller_path_parameter_workflow() -> None:
    class AccountController(Controller):
        path = "/accounts"

        @get("/{account_id:int}", name="account", sync_to_thread=False)
        def account(self, account_id: FromPath[int]) -> dict[str, int]:
            return {"account_id": account_id}

    app = Litestar(route_handlers=[AccountController])
    with TestClient(app) as client:
        first = client.get("/accounts/3")
        second = client.get(app.route_reverse("account", account_id=4))
    assert body(first) == {"account_id": 3}
    assert body(second) == {"account_id": 4}


@pytest.mark.depends_on(
    "test_request_object_exposes_path",
    "test_route_handler_name_is_reversible",
    "test_dict_return_is_json",
)
def test_route_name_used_inside_handler() -> None:
    @get("/target/{target_id:int}", name="target", sync_to_thread=False)
    def target(target_id: FromPath[int]) -> dict[str, int]:
        return {"id": target_id}

    @get("/link", sync_to_thread=False)
    def link(request: Request[Any, Any, Any]) -> dict[str, str]:
        return {"url": request.app.route_reverse("target", target_id=9)}

    app = Litestar(route_handlers=[target, link])
    with TestClient(app) as client:
        response = client.get("/link")
        target_response = client.get("/target/9")
    assert body(response) == {"url": "/target/9"}
    assert body(target_response) == {"id": 9}


@pytest.mark.depends_on(
    "test_openapi_contains_query_parameter",
    "test_openapi_uses_custom_title_and_version",
    "test_dict_return_is_json",
)
def test_openapi_operation_metadata_workflow() -> None:
    @get(
        "/search",
        summary="Search records",
        description="Searches the catalog",
        sync_to_thread=False,
    )
    def search(term: FromQuery[str]) -> dict[str, str]:
        return {"term": term}

    from litestar.openapi.config import OpenAPIConfig

    app = Litestar(
        route_handlers=[search],
        openapi_config=OpenAPIConfig(title="Search API", version="1"),
    )
    schema = app.openapi_schema.to_schema()
    operation = schema["paths"]["/search"]["get"]
    with TestClient(app) as client:
        response = client.get("/search?term=books")
    assert response.status_code == 200
    assert operation["summary"] == "Search records"
    assert operation["description"] == "Searches the catalog"
    assert schema["info"]["title"] == "Search API"


@pytest.mark.depends_on(
    "test_text_media_type_sets_plain_content",
    "test_html_media_type_sets_html_content",
    "test_dict_return_is_json",
)
def test_different_media_types_workflow() -> None:
    @get("/json", sync_to_thread=False)
    def json_value() -> dict[str, str]:
        return {"kind": "json"}

    @get("/text", media_type=MediaType.TEXT, sync_to_thread=False)
    def text_value() -> str:
        return "text"

    @get("/html", media_type=MediaType.HTML, sync_to_thread=False)
    def html_value() -> str:
        return "<strong>html</strong>"

    with create_test_client([json_value, text_value, html_value]) as client:
        responses = [client.get("/json"), client.get("/text"), client.get("/html")]
    assert [content_type(response) for response in responses] == [
        "application/json",
        "text/plain",
        "text/html",
    ]
    assert body(responses[0]) == {"kind": "json"}
    assert responses[1].text == "text"
    assert responses[2].text == "<strong>html</strong>"


@pytest.mark.depends_on(
    "test_public_routes_expose_registered_paths",
    "test_router_prefix_is_applied",
    "test_controller_prefix_is_applied",
)
def test_router_registration_public_paths_workflow() -> None:
    class StatusController(Controller):
        path = "/status"

        @get(sync_to_thread=False)
        def read(self) -> str:
            return "controller"

    @get("/health", sync_to_thread=False)
    def health() -> str:
        return "router"

    app = Litestar(route_handlers=[Router("/api", route_handlers=[health, StatusController])])
    paths = {route_item.path for route_item in app.routes}
    with TestClient(app) as client:
        health_response = client.get("/api/health")
        status_response = client.get("/api/status")
    assert "/api/health" in paths
    assert "/api/status" in paths
    assert health_response.text == "router"
    assert status_response.text == "controller"


@pytest.mark.depends_on(
    "test_route_reverse_accepts_handler",
    "test_typed_path_parameter_is_converted",
    "test_controller_prefix_is_applied",
)
def test_app_route_reverse_and_client_agree() -> None:
    @get("/files/{file_id:int}", name="file", sync_to_thread=False)
    def file(file_id: FromPath[int]) -> dict[str, int]:
        return {"file_id": file_id}

    app = Litestar(route_handlers=[file])
    generated = app.route_reverse("file", file_id=21)
    with TestClient(app) as client:
        response = client.get(generated)
    assert generated == "/files/21"
    assert response.status_code == 200
    assert body(response) == {"file_id": 21}
