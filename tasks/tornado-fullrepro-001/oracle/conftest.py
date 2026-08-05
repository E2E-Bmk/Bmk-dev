from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest
from tornado.httputil import (
    HTTPHeaders,
    HTTPServerRequest,
    RequestStartLine,
    parse_body_arguments,
)
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): public atomic behavior required by an integration workflow",
    )


def quiet_log(handler: RequestHandler) -> None:
    return None


class DummyConnection:
    def __init__(self, remote_ip: str = "127.0.0.1", protocol: str = "http") -> None:
        self.context = SimpleNamespace(remote_ip=remote_ip, protocol=protocol)
        self.close_callback: Callable[[], None] | None = None

    def set_close_callback(self, callback: Callable[[], None]) -> None:
        self.close_callback = callback


def make_request(
    *,
    method: str = "GET",
    uri: str = "/",
    headers: dict[str, str] | HTTPHeaders | None = None,
    body: bytes = b"",
    host: str = "example.com",
) -> HTTPServerRequest:
    request_headers = HTTPHeaders(headers or {})
    if "Host" not in request_headers:
        request_headers["Host"] = host
    request = HTTPServerRequest(
        connection=DummyConnection(),
        start_line=RequestStartLine(method, uri, "HTTP/1.1"),
        headers=request_headers,
        body=body,
    )
    content_type = request_headers.get("Content-Type", "")
    if body and content_type.startswith("application/x-www-form-urlencoded"):
        parse_body_arguments(
            content_type,
            body,
            request.body_arguments,
            request.files,
            request_headers,
        )
        for name, values in request.body_arguments.items():
            request.arguments.setdefault(name, []).extend(values)
    return request


def make_app(routes: list[Any] | None = None, **settings: Any) -> Application:
    settings.setdefault("log_function", quiet_log)
    return Application(routes or [], **settings)


def make_handler(
    handler_class: type[RequestHandler] = RequestHandler,
    *,
    app: Application | None = None,
    method: str = "GET",
    uri: str = "/",
    headers: dict[str, str] | HTTPHeaders | None = None,
    body: bytes = b"",
    host: str = "example.com",
    **kwargs: Any,
) -> RequestHandler:
    application = app if app is not None else make_app()
    request = make_request(
        method=method,
        uri=uri,
        headers=headers,
        body=body,
        host=host,
    )
    return handler_class(application, request, **kwargs)


class LocalHTTPCase(AsyncHTTPTestCase):
    def __init__(self, app_factory: Callable[[], Application]) -> None:
        self.app_factory = app_factory
        self.application: Application | None = None
        super().__init__(methodName="runTest")

    def get_app(self) -> Application:
        self.application = self.app_factory()
        return self.application


@contextmanager
def running_http_case(app_factory: Callable[[], Application]) -> Iterator[LocalHTTPCase]:
    case = LocalHTTPCase(app_factory)
    case.setUp()
    try:
        yield case
    finally:
        case.tearDown()
