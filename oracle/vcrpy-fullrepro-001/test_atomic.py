# Spec2Repo oracle - atomic tests for vcrpy-fullrepro-001
import pytest

from vcr import matchers
from vcr.cassette import Cassette
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


def test_request_preserves_method_body_and_normalized_location():
    request = Request("POST", "https://Example.test:9443/items", b"payload", {})

    assert request.method == "POST"
    assert request.body == b"payload"
    assert request.scheme == "https"
    assert request.host == "example.test"
    assert request.port == 9443
    assert request.path == "/items"


def test_method_matcher_accepts_equal_methods_and_rejects_different_methods():
    first = Request("GET", "http://example.test/first", None, {})
    equal = Request("GET", "http://example.test/second", b"body", {})
    different = Request("POST", "http://example.test/first", None, {})

    assert matchers.method(first, equal) is None
    with pytest.raises(AssertionError):
        matchers.method(first, different)


def test_scheme_matcher_uses_normalized_request_scheme():
    http = Request("GET", "http://example.test/path", None, {})
    same = Request("POST", "http://other.test/", None, {})
    https = Request("GET", "https://example.test/path", None, {})

    assert matchers.scheme(http, same) is None
    with pytest.raises(AssertionError):
        matchers.scheme(http, https)


def test_host_matcher_uses_normalized_request_host():
    first = Request("GET", "http://Example.test/one", None, {})
    same = Request("POST", "https://example.test/two", None, {})
    different = Request("GET", "http://other.test/one", None, {})

    assert matchers.host(first, same) is None
    with pytest.raises(AssertionError):
        matchers.host(first, different)


def test_port_matcher_distinguishes_effective_ports():
    first = Request("GET", "http://example.test/path", None, {})
    same = Request("POST", "http://other.test/", None, {})
    different = Request("GET", "http://example.test:8080/path", None, {})

    assert matchers.port(first, same) is None
    with pytest.raises(AssertionError):
        matchers.port(first, different)


def test_path_matcher_ignores_other_request_components():
    first = Request("GET", "http://example.test/items?a=1", None, {})
    same = Request("POST", "https://other.test/items?a=2", b"body", {})
    different = Request("GET", "http://example.test/other?a=1", None, {})

    assert matchers.path(first, same) is None
    with pytest.raises(AssertionError):
        matchers.path(first, different)


def test_query_matcher_compares_normalized_query_pairs():
    first = Request("GET", "http://example.test/?b=2&a=1", None, {})
    same = Request("POST", "https://other.test/?a=1&b=2", None, {})
    different = Request("GET", "http://example.test/?a=2&b=2", None, {})

    assert matchers.query(first, same) is None
    with pytest.raises(AssertionError):
        matchers.query(first, different)


def test_raw_body_matcher_compares_request_bytes():
    first = Request("POST", "http://example.test/one", b"payload", {})
    same = Request("PUT", "http://other.test/two", b"payload", {})
    different = Request("POST", "http://example.test/one", b"changed", {})

    assert matchers.raw_body(first, same) is None
    with pytest.raises(AssertionError):
        matchers.raw_body(first, different)


def test_new_cassette_exposes_empty_public_projections():
    cassette = Cassette("unused.yaml")

    assert len(cassette) == 0
    assert cassette.requests == []
    assert cassette.responses == []
    assert cassette.play_count == 0
    assert cassette.all_played is True


def _response(body=b"ok", status=200):
    return {
        "status": {"code": status, "message": "OK"},
        "headers": {},
        "body": {"string": body},
    }


def test_cassette_responses_of_preserves_matching_response_order():
    request = Request("GET", "http://example.test/items", None, {})
    cassette = Cassette("unused.yaml")
    cassette.append(request, _response(b"first"))
    cassette.append(request, _response(b"second"))

    assert [response["body"]["string"] for response in cassette.responses_of(request)] == [
        b"first",
        b"second",
    ]
    assert cassette.requests == [request, request]
    assert len(cassette) == 2


def test_cassette_rewind_resets_public_playback_bookkeeping():
    request = Request("GET", "http://example.test/items", None, {})
    cassette = Cassette("unused.yaml")
    cassette.append(request, _response())

    assert cassette.play_response(request)["body"]["string"] == b"ok"
    assert cassette.play_count == 1
    assert cassette.all_played is True
    cassette.rewind()
    assert cassette.play_count == 0
    assert cassette.all_played is False


def test_cassette_allow_playback_repeats_reuses_matching_response():
    request = Request("GET", "http://example.test/items", None, {})
    cassette = Cassette("unused.yaml", allow_playback_repeats=True)
    cassette.append(request, _response())

    assert cassette.play_response(request)["body"]["string"] == b"ok"
    assert cassette.play_response(request)["body"]["string"] == b"ok"
    assert cassette.play_count == 2


def test_ensure_suffix_adds_suffix_once():
    import vcr

    ensure_yaml = vcr.VCR.ensure_suffix(".yaml")

    assert ensure_yaml("recording") == "recording.yaml"
    assert ensure_yaml("recording.yaml") == "recording.yaml"
