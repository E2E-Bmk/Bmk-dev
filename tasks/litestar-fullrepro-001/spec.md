# Litestar Public Route Application Behavior

## Product Overview

Build the public Litestar application layer for HTTP route handlers. The implementation must support decorated typed route handlers, routers, controllers, in-process testing clients, request parsing, response generation, reverse routing, deterministic dependency and guard behavior, and generated OpenAPI projections for the same route facts.

## Scope

The required surface is the documented public API exposed from `litestar`, `litestar.testing`, `litestar.di`, `litestar.params`, `litestar.openapi.config`, and `litestar.exceptions`. Route handlers may be registered directly, through nested `Router` instances, or through `Controller` subclasses. The same configured application facts must be visible through HTTP requests, public route metadata, `route_reverse()`, and OpenAPI schema dictionaries.

## Public Import Surface

The package root `litestar` exposes `Litestar`, `Router`, `Controller`,
`Request`, `Response`, `MediaType`, `HttpMethod`, and the HTTP decorators `get`,
`post`, `put`, `patch`, and `delete`. Dependency declarations use `Provide` and
`NamedDependency` from `litestar.di`; typed parameters use `FromHeader`,
`FromPath`, and `FromQuery` from `litestar.params`; local application probes use
`create_test_client` from `litestar.testing`. OpenAPI configuration is provided
by `OpenAPIConfig` from `litestar.openapi.config`. Documented HTTP failures
include `NoRouteMatchFoundException` and `PermissionDeniedException` from
`litestar.exceptions`. Private modules and source repository helpers are
outside the required surface.

## Product State Model

An application is a deterministic graph of handlers mounted under paths and HTTP methods. Path prefixes compose from the application, routers, and controllers. Handler definitions include names, typed path/query/header/body parameters, media type, status defaults, optional guards, optional dependencies, inclusion in schema output, and custom OpenAPI metadata.

## Error Semantics

Type conversion and routing errors must produce stable HTTP status behavior: missing required query values are bad requests, path patterns that cannot match are not found, unsupported methods are method-not-allowed, guard denial is forbidden, and explicit public HTTP exceptions become HTTP responses. Tests check status classes and selected stable fields, not whole response payload snapshots.

## Cross-View Invariants

For a route that is registered once, the HTTP client, public route list, reverse routing, and OpenAPI path entry must agree on path composition and parameter names. Hidden routes remain callable but are absent from OpenAPI paths. Media type configuration must affect both response headers and the OpenAPI response content entry.

## Representative Workflows

Representative workflows include creating and deleting in-memory resources, accessing nested controller routes through generated paths, combining guard and dependency resolution, exercising all main HTTP method defaults on a resource path, checking OPTIONS and method rejection, and comparing live client behavior with OpenAPI parameter projections.

## Non-Goals

Do not implement live ASGI servers, external network access, database integrations, file services, background workers, timing-sensitive behavior, sleeps, host-state inspection, exact complete OpenAPI documents, or complete response snapshots. Do not depend on private framework internals or import the source checkout test suite.

## Invocation Protocol

Install the listed requirements, place the candidate package on `PYTHONPATH`, and run `test_atomic.py` and `test_integration.py` with pytest. Disable pytest cache writes if desired. The tests use only in-process clients and local memory state.

## Environment

Run on Linux with Python 3.11 without network access. The target package is not pre-installed; the implementation under test is supplied on `PYTHONPATH`. Required packages are `pytest`, `pytest-json-report`, `httpx`, `anyio`, `msgspec`, `multidict`, `multipart`, `sniffio`, `typing-extensions`, and `pydantic`.

## Evaluation Notes

Assertions focus on public, deterministic behavior: selected status codes, selected response bodies and headers, selected route paths, selected reverse routes, selected dependency and guard outcomes, and selected OpenAPI dictionary entries. They intentionally avoid private state, brittle full-document comparisons, host paths, network use, sleeps, and timing assumptions.
