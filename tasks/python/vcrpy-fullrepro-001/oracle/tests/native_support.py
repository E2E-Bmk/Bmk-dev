from __future__ import annotations

from typing import Any


def response(body: bytes, status: int = 200) -> dict[str, Any]:
    return {
        "status": {"code": status, "message": "OK"},
        "headers": {"Content-Type": ["text/plain"], "Content-Length": [str(len(body))]},
        "body": {"string": body},
    }


def request_view(request: Any) -> dict[str, Any]:
    return {"method": request.method, "uri": request.uri, "body": request.body, "headers": dict(request.headers)}


def decoded_view(value: Any) -> dict[str, Any]:
    requests, responses = value
    return {"requests": [request_view(item) for item in requests], "responses": responses}


def expect_assertion(function: Any) -> None:
    try:
        function()
    except AssertionError:
        return
    raise AssertionError("controlled mismatch was accepted")
