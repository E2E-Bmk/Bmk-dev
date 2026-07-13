# Spec2Repo oracle - atomic tests for vcrpy-fullrepro-001
import pytest

from vcr import matchers
from vcr.request import Request
from vcr.serialize import deserialize, serialize


class IdentitySerializer:
    @staticmethod
    def serialize(data):
        return data

    @staticmethod
    def deserialize(data):
        return data


def test_request_exposes_normalized_uri_components_and_aliases():
    request = Request(
        "GET",
        "https://Example.test:8443/b?z=2&a=1",
        None,
        {},
    )

    assert request.uri == "https://Example.test:8443/b?z=2&a=1"
    assert request.url == request.uri
    assert request.scheme == "https"
    assert request.protocol == request.scheme
    assert request.host == "example.test"
    assert request.port == 8443
    assert request.path == "/b"
    assert request.query == [("a", "1"), ("z", "2")]


def test_request_applies_default_http_and_https_ports():
    http_request = Request("GET", "http://example.test/path", None, {})
    https_request = Request("GET", "https://example.test/path", None, {})

    assert http_request.port == 80
    assert https_request.port == 443


def test_request_query_preserves_repeated_values_in_sorted_order():
    request = Request("GET", "http://example.test/?b=2&a=3&a=1", None, {})

    assert request.query == [("a", "1"), ("a", "3"), ("b", "2")]


def test_uri_matcher_accepts_equal_uri_and_rejects_different_uri():
    first = Request("GET", "http://example.test/items?a=1", None, {})
    same_uri = Request("POST", "http://example.test/items?a=1", b"body", {})
    different_uri = Request("GET", "http://example.test/items?a=2", None, {})

    assert matchers.uri(first, same_uri) is None
    with pytest.raises(AssertionError):
        matchers.uri(first, different_uri)


def test_headers_matcher_is_case_insensitive_and_detects_value_changes():
    first = Request("GET", "http://example.test/", None, {"X-Token": "secret"})
    same_headers = Request("GET", "http://example.test/", None, {"x-token": "secret"})
    different_headers = Request("GET", "http://example.test/", None, {"X-Token": "changed"})

    assert matchers.headers(first, same_headers) is None
    with pytest.raises(AssertionError):
        matchers.headers(first, different_headers)


def test_body_matcher_compares_json_semantically():
    headers = {"Content-Type": "application/json"}
    first = Request("POST", "http://example.test/", b'{"a": 1, "b": 2}', headers)
    same_json = Request("POST", "http://example.test/", b'{"b": 2, "a": 1}', headers)
    different_json = Request("POST", "http://example.test/", b'{"a": 2, "b": 2}', headers)

    assert matchers.body(first, same_json) is None
    with pytest.raises(AssertionError):
        matchers.body(first, different_json)


def test_serialize_projects_ordered_request_response_interactions():
    requests = [
        Request("GET", "http://example.test/first", None, {}),
        Request("POST", "http://example.test/second", b"payload", {"X-Test": "yes"}),
    ]
    responses = [
        {"status": {"code": 200, "message": "OK"}, "body": {"string": b"first"}, "headers": {}},
        {"status": {"code": 201, "message": "Created"}, "body": {"string": b"second"}, "headers": {}},
    ]

    data = serialize({"requests": requests, "responses": responses}, IdentitySerializer)

    assert data["version"] == 1
    assert [item["request"]["uri"] for item in data["interactions"]] == [
        "http://example.test/first",
        "http://example.test/second",
    ]
    assert [item["response"]["status"]["code"] for item in data["interactions"]] == [200, 201]


def test_deserialize_reconstructs_request_and_response_from_interaction():
    data = {
        "version": 1,
        "interactions": [
            {
                "request": {
                    "method": "POST",
                    "uri": "https://example.test/items?b=2&a=1",
                    "body": "payload",
                    "headers": {"Content-Type": ["text/plain"]},
                },
                "response": {
                    "status": {"code": 202, "message": "Accepted"},
                    "body": {"string": "stored"},
                    "headers": {"Content-Type": ["text/plain"]},
                },
            }
        ],
    }

    requests, responses = deserialize(data, IdentitySerializer)

    assert len(requests) == len(responses) == 1
    assert requests[0].method == "POST"
    assert requests[0].uri == "https://example.test/items?b=2&a=1"
    assert requests[0].url == requests[0].uri
    assert requests[0].query == [("a", "1"), ("b", "2")]
    assert requests[0].body == b"payload"
    assert responses[0]["status"]["code"] == 202
    assert responses[0]["body"]["string"] == b"stored"
