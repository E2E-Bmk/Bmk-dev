from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Iterator, AsyncIterator

import httpx


def test_a01(tmp_path: Path) -> None:
    url = httpx.URL("HTTPS://Example.TEST:443/a/../b?q=hello%20world")
    assert url.scheme == "https" and url.host == "example.test" and url.port == 443
    assert url.copy_with(path="/next").raw_path == b"/next?q=hello%20world"


def test_a02(tmp_path: Path) -> None:
    headers = httpx.Headers([("X-Item", "one"), ("x-item", "two"), ("Content-Type", "text/plain")])
    assert headers.get_list("x-item") == ["one", "two"] and headers["X-ITEM"] == "one, two"
    assert list(headers.multi_items())[:2] == [("x-item", "one"), ("x-item", "two")]


def test_a03(tmp_path: Path) -> None:
    query = httpx.QueryParams([("tag", "a"), ("tag", "b"), ("empty", None)])
    assert query.get_list("tag") == ["a", "b"] and str(query) == "tag=a&tag=b&empty="
    assert query.merge({"page": 2}).get("page") == "2"


def test_a04(tmp_path: Path) -> None:
    cookies = httpx.Cookies()
    cookies.set("session", "alpha", domain="example.test", path="/")
    cookies.set("scoped", "beta", domain="example.test", path="/api")
    request = httpx.Request("GET", "https://example.test/api/items")
    cookies.set_cookie_header(request)
    assert request.headers["cookie"] in {"session=alpha; scoped=beta", "scoped=beta; session=alpha"}


def test_a05(tmp_path: Path) -> None:
    request = httpx.Request("POST", "https://example.test/items", json={"b": 2, "a": 1})
    assert request.method == "POST" and request.url.path == "/items"
    assert json.loads(request.content) == {"a": 1, "b": 2} and request.headers["content-type"] == "application/json"


def test_a06(tmp_path: Path) -> None:
    request = httpx.Request("GET", "https://example.test/data")
    response = httpx.Response(206, headers={"content-type": "application/json; charset=utf-8"},
                              content=b'{"ok":true}', request=request, extensions={"trace": "x"})
    assert response.json() == {"ok": True} and response.request is request
    assert response.is_success and response.extensions["trace"] == "x"


def test_i01(tmp_path: Path) -> None:
    seen: list[httpx.Request] = []
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request); return httpx.Response(200, json={"path": request.url.path})
    with httpx.Client(transport=httpx.MockTransport(handler), base_url="https://example.test/api/") as client:
        response = client.get("items", params={"q": "x"})
    assert response.json() == {"path": "/api/items"} and seen[0].url.query == b"q=x"


def test_i02(tmp_path: Path) -> None:
    seen: list[tuple[str, str | None]] = []
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), request.headers.get("authorization")))
        if request.url.path == "/start": return httpx.Response(302, headers={"location": "https://other.test/end"})
        return httpx.Response(200, text="done")
    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True,
                      headers={"Authorization": "Bearer token"}) as client:
        response = client.get("https://example.test/start")
    assert response.text == "done" and len(response.history) == 1 and seen == [
        ("https://example.test/start", "Bearer token"), ("https://other.test/end", None)]


def test_i03(tmp_path: Path) -> None:
    observed: list[str | None] = []
    def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request.headers.get("cookie"))
        if request.url.path == "/set": return httpx.Response(200, headers={"set-cookie": "sid=abc; Path=/"})
        return httpx.Response(200)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        client.get("https://example.test/set"); client.get("https://example.test/next")
    assert observed == [None, "sid=abc"]


def test_i04(tmp_path: Path) -> None:
    class Body(httpx.SyncByteStream):
        def __init__(self) -> None: self.closed = 0
        def __iter__(self) -> Iterator[bytes]: yield b"a"; yield b"bc"
        def close(self) -> None: self.closed += 1
    body = Body()
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=body))
    with httpx.Client(transport=transport) as client:
        with client.stream("GET", "https://example.test/") as response:
            assert next(response.iter_bytes()) == b"a"
    assert body.closed == 1


def test_i05(tmp_path: Path) -> None:
    direct = httpx.MockTransport(lambda request: httpx.Response(200, text="direct"))
    special = httpx.MockTransport(lambda request: httpx.Response(200, text="special"))
    with httpx.Client(transport=direct, mounts={"https://special.test": special}) as client:
        assert client.get("https://special.test/a").text == "special"
        assert client.get("https://ordinary.test/a").text == "direct"


def test_s01(tmp_path: Path) -> None:
    class ClosingTransport(httpx.BaseTransport):
        def __init__(self) -> None: self.closed = 0; self.calls = 0
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            self.calls += 1; return httpx.Response(200, text="ok")
        def close(self) -> None: self.closed += 1
    transport = ClosingTransport()
    with httpx.Client(transport=transport) as client:
        assert client.get("https://example.test/").text == "ok"
    assert transport.calls == 1 and transport.closed == 1


def test_s02(tmp_path: Path) -> None:
    async def scenario() -> None:
        class AsyncTransport(httpx.AsyncBaseTransport):
            def __init__(self) -> None: self.closed = 0; self.urls: list[str] = []
            async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
                self.urls.append(str(request.url)); return httpx.Response(200, json={"ok": True})
            async def aclose(self) -> None: self.closed += 1
        transport = AsyncTransport()
        async with httpx.AsyncClient(transport=transport, base_url="https://example.test") as client:
            assert (await client.get("/async")).json() == {"ok": True}
        assert transport.urls == ["https://example.test/async"] and transport.closed == 1
    asyncio.run(scenario())


def test_s03(tmp_path: Path) -> None:
    class TwoStepAuth(httpx.Auth):
        def auth_flow(self, request: httpx.Request):
            request.headers["x-attempt"] = "one"
            response = yield request
            if response.status_code == 401:
                request.headers["x-attempt"] = "two"
                yield request
    seen: list[str] = []
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["x-attempt"])
        return httpx.Response(401 if len(seen) == 1 else 200)
    with httpx.Client(transport=httpx.MockTransport(handler), auth=TwoStepAuth()) as client:
        assert client.get("https://example.test/").status_code == 200
    assert seen == ["one", "two"]
