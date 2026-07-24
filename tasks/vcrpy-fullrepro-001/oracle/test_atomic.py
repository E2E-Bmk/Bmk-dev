"""Atomic-layer oracle tests for vcrpy-fullrepro-001.

Each test verifies ONE public API entry's ONE behaviour.
Independent solvability: if only the tested API is correctly implemented
(everything else is a stub), the test must pass.
"""
import pytest

import vcr
from vcr import matchers
from vcr.cassette import Cassette
from vcr.errors import CannotOverwriteExistingCassetteException
from vcr.persisters.filesystem import (
    CassetteDecodeError,
    CassetteNotFoundError,
    FilesystemPersister,
)
from vcr.request import Request
from vcr.serialize import deserialize, serialize

from conftest import IdentitySerializer, InMemoryJsonSerializer, make_response


# ═══════════════════════════════════════════════════════════════
# Request — URI Components
# ═══════════════════════════════════════════════════════════════

def test_request_uri_preserves_original_value():
    req = Request("PUT", "https://Demo.Example.test:9443/api/v2?z=3&a=1", None, {})
    assert req.uri == "https://Demo.Example.test:9443/api/v2?z=3&a=1"


def test_request_url_is_backward_compatible_alias_for_uri():
    req = Request("DELETE", "http://shop.example.test/cart/7", None, {})
    assert req.url is not None
    assert req.url == req.uri


def test_request_scheme_and_protocol_normalized_lowercase():
    req = Request("GET", "HTTPS://Foo.example.test/", None, {})
    assert req.scheme == "https"
    assert req.protocol == req.scheme


def test_request_host_normalized_lowercase():
    req = Request("GET", "http://Shop.EXAMPLE.test/items", None, {})
    assert req.host == "shop.example.test"


def test_request_port_uses_explicit_value():
    req = Request("GET", "http://api.example.test:7080/data", None, {})
    assert req.port == 7080


def test_request_port_defaults_http_80_and_https_443():
    http_req = Request("GET", "http://api.example.test/x", None, {})
    https_req = Request("GET", "https://api.example.test/x", None, {})
    assert http_req.port == 80
    assert https_req.port == 443


def test_request_path_excludes_query_string():
    req = Request("GET", "http://api.example.test/items/42?detail=true", None, {})
    assert req.path == "/items/42"


def test_request_query_sorted_with_duplicate_keys_preserved():
    req = Request(
        "GET", "http://api.example.test/?color=red&size=lg&color=blue", None, {}
    )
    assert req.query == [("color", "blue"), ("color", "red"), ("size", "lg")]


# ═══════════════════════════════════════════════════════════════
# Request — Body and Method
# ═══════════════════════════════════════════════════════════════

def test_request_method_returns_http_verb():
    req = Request("PATCH", "http://api.example.test/items/5", b"update-data", {})
    assert req.method == "PATCH"


def test_request_body_returns_bytes_or_none():
    with_body = Request("POST", "http://api.example.test/", b"sample-data", {})
    assert with_body.body == b"sample-data"
    without_body = Request("GET", "http://api.example.test/", None, {})
    assert without_body.body is None


# ═══════════════════════════════════════════════════════════════
# Request Matching — Component Matchers
# ═══════════════════════════════════════════════════════════════

def test_method_matcher_compares_http_methods():
    r1 = Request("PUT", "http://a.test/x", None, {})
    r2 = Request("PUT", "http://b.test/y", b"d", {})
    r3 = Request("DELETE", "http://a.test/x", None, {})
    assert matchers.method(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.method(r1, r3)


def test_uri_matcher_compares_full_uri():
    r1 = Request("GET", "http://shop.test/cart?id=5", None, {})
    r2 = Request("POST", "http://shop.test/cart?id=5", b"x", {})
    r3 = Request("GET", "http://shop.test/cart?id=6", None, {})
    assert matchers.uri(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.uri(r1, r3)


def test_scheme_matcher_compares_normalized_scheme():
    r1 = Request("GET", "http://a.test/x", None, {})
    r2 = Request("POST", "http://b.test/y", None, {})
    r3 = Request("GET", "https://a.test/x", None, {})
    assert matchers.scheme(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.scheme(r1, r3)


def test_host_matcher_compares_normalized_host():
    r1 = Request("GET", "http://Shop.Example.test/a", None, {})
    r2 = Request("POST", "https://shop.example.test/b", None, {})
    r3 = Request("GET", "http://other.test/a", None, {})
    assert matchers.host(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.host(r1, r3)


def test_port_matcher_compares_effective_port():
    r1 = Request("GET", "http://a.test/x", None, {})
    r2 = Request("POST", "http://b.test/y", None, {})
    r3 = Request("GET", "http://a.test:9090/x", None, {})
    assert matchers.port(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.port(r1, r3)


def test_path_matcher_ignores_scheme_host_port_query():
    r1 = Request("GET", "http://a.test/items?x=1", None, {})
    r2 = Request("POST", "https://b.test:9090/items?y=2", b"body", {})
    r3 = Request("GET", "http://a.test/other?x=1", None, {})
    assert matchers.path(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.path(r1, r3)


def test_query_matcher_compares_sorted_pairs():
    r1 = Request("GET", "http://a.test/?z=3&m=1", None, {})
    r2 = Request("POST", "https://b.test/?m=1&z=3", None, {})
    r3 = Request("GET", "http://a.test/?z=3&m=2", None, {})
    assert matchers.query(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.query(r1, r3)


# ═══════════════════════════════════════════════════════════════
# Request Matching — Body Matchers
# ═══════════════════════════════════════════════════════════════

def test_raw_body_matcher_compares_bytes_directly():
    r1 = Request("POST", "http://a.test/", b"alpha-body", {})
    r2 = Request("PUT", "http://b.test/", b"alpha-body", {})
    r3 = Request("POST", "http://a.test/", b"beta-body", {})
    assert matchers.raw_body(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.raw_body(r1, r3)


def test_body_matcher_json_comparison_is_key_order_independent():
    hdrs = {"Content-Type": "application/json"}
    r1 = Request("POST", "http://a.test/", b'{"x": 10, "y": 20}', hdrs)
    r2 = Request("POST", "http://a.test/", b'{"y": 20, "x": 10}', hdrs)
    r3 = Request("POST", "http://a.test/", b'{"x": 10, "y": 99}', hdrs)
    assert matchers.body(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.body(r1, r3)


def test_body_matcher_falls_back_to_raw_bytes_for_plain_content():
    hdrs = {"Content-Type": "text/plain"}
    r1 = Request("POST", "http://a.test/", b"same-text", hdrs)
    r2 = Request("POST", "http://a.test/", b"same-text", hdrs)
    r3 = Request("POST", "http://a.test/", b"diff-text", hdrs)
    assert matchers.body(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.body(r1, r3)


# ═══════════════════════════════════════════════════════════════
# Request Matching — Header Matcher
# ═══════════════════════════════════════════════════════════════

def test_headers_matcher_case_insensitive_names_detects_value_change():
    r1 = Request("GET", "http://a.test/", None, {"X-Custom-Auth": "abc123"})
    r2 = Request("GET", "http://a.test/", None, {"x-custom-auth": "abc123"})
    r3 = Request("GET", "http://a.test/", None, {"X-Custom-Auth": "xyz789"})
    assert matchers.headers(r1, r2) is None
    with pytest.raises(AssertionError):
        matchers.headers(r1, r3)


# ═══════════════════════════════════════════════════════════════
# Cassette Bookkeeping
# ═══════════════════════════════════════════════════════════════

def test_new_cassette_has_zero_length_empty_lists_zero_play_count():
    cass = Cassette("fresh.yaml")
    assert len(cass) == 0
    assert cass.requests == []
    assert cass.responses == []
    assert cass.play_count == 0
    assert cass.all_played is True


def test_cassette_append_adds_interaction_and_updates_length():
    cass = Cassette("append.yaml")
    req = Request("GET", "http://api.example.test/items", None, {})
    resp = make_response(b"item-list", 200)
    cass.append(req, resp)
    assert len(cass) == 1
    assert cass.requests == [req]


def test_cassette_play_response_returns_matching_and_increments_count():
    cass = Cassette("play.yaml")
    req = Request("GET", "http://api.example.test/data", None, {})
    resp = make_response(b"data-here", 200)
    cass.append(req, resp)
    played = cass.play_response(req)
    assert played["body"]["string"] == b"data-here"
    assert played["status"]["code"] == 200
    assert cass.play_count == 1


def test_cassette_all_played_reflects_exhaustion():
    cass = Cassette("exhaust.yaml")
    req = Request("GET", "http://api.example.test/resource", None, {})
    cass.append(req, make_response())
    assert cass.all_played is False
    cass.play_response(req)
    assert cass.all_played is True


def test_cassette_rewind_resets_play_count_and_all_played():
    cass = Cassette("rewind.yaml")
    req = Request("GET", "http://api.example.test/list", None, {})
    cass.append(req, make_response(b"list-data"))
    cass.play_response(req)
    assert cass.play_count == 1
    assert cass.all_played is True
    cass.rewind()
    assert cass.play_count == 0
    assert cass.all_played is False


def test_cassette_responses_of_returns_all_matches_in_order():
    cass = Cassette("multi.yaml")
    req = Request("GET", "http://api.example.test/things", None, {})
    cass.append(req, make_response(b"first-thing"))
    cass.append(req, make_response(b"second-thing"))
    bodies = [r["body"]["string"] for r in cass.responses_of(req)]
    assert bodies == [b"first-thing", b"second-thing"]


def test_cassette_playback_repeats_enabled():
    cass = Cassette("repeat.yaml", allow_playback_repeats=True)
    req = Request("GET", "http://api.example.test/status", None, {})
    cass.append(req, make_response(b"alive"))
    assert cass.play_response(req)["body"]["string"] == b"alive"
    assert cass.play_response(req)["body"]["string"] == b"alive"
    assert cass.play_count == 2


# ═══════════════════════════════════════════════════════════════
# Serialization and Cassette Format
# ═══════════════════════════════════════════════════════════════

def test_serialize_produces_version_1_interaction_list():
    reqs = [
        Request("GET", "http://api.example.test/alpha", None, {}),
        Request("POST", "http://api.example.test/beta", b"body-data", {"X-Req": "yes"}),
    ]
    resps = [
        make_response(b"resp-alpha", 200),
        make_response(b"resp-beta", 201, "Created"),
    ]
    data = serialize({"requests": reqs, "responses": resps}, IdentitySerializer)
    assert data["version"] == 1
    assert len(data["interactions"]) == 2
    assert data["interactions"][0]["request"]["uri"] == "http://api.example.test/alpha"
    assert data["interactions"][0]["request"]["method"] == "GET"
    assert data["interactions"][1]["response"]["status"]["code"] == 201


def test_deserialize_reconstructs_request_objects_and_responses():
    data = {
        "version": 1,
        "interactions": [
            {
                "request": {
                    "method": "PATCH",
                    "uri": "https://demo.example.test/items/9?rev=2",
                    "body": "patch-payload",
                    "headers": {"Accept": ["application/json"]},
                },
                "response": {
                    "status": {"code": 200, "message": "OK"},
                    "body": {"string": "updated"},
                    "headers": {"Content-Type": ["application/json"]},
                },
            }
        ],
    }
    reqs, resps = deserialize(data, IdentitySerializer)
    assert len(reqs) == 1
    assert reqs[0].method == "PATCH"
    assert reqs[0].uri == "https://demo.example.test/items/9?rev=2"
    assert reqs[0].query == [("rev", "2")]
    assert resps[0]["status"]["code"] == 200


def test_deserialize_converts_string_body_to_bytes():
    data = {
        "version": 1,
        "interactions": [
            {
                "request": {
                    "method": "POST",
                    "uri": "http://api.example.test/submit",
                    "body": "string-body-value",
                    "headers": {},
                },
                "response": {
                    "status": {"code": 202, "message": "Accepted"},
                    "body": {"string": "response-text"},
                    "headers": {},
                },
            }
        ],
    }
    reqs, _resps = deserialize(data, IdentitySerializer)
    assert isinstance(reqs[0].body, bytes)
    assert reqs[0].body == b"string-body-value"


# ═══════════════════════════════════════════════════════════════
# Mode Constants
# ═══════════════════════════════════════════════════════════════

def test_mode_constants_are_importable_attributes():
    import vcr.mode as mode_mod
    for name in ("ONCE", "NONE", "NEW_EPISODES", "ALL"):
        assert hasattr(mode_mod, name), f"vcr.mode.{name} missing"


def test_mode_constants_are_distinct_values():
    import vcr.mode as m
    values = {m.ONCE, m.NONE, m.NEW_EPISODES, m.ALL}
    assert len(values) == 4


# ═══════════════════════════════════════════════════════════════
# VCR.ensure_suffix
# ═══════════════════════════════════════════════════════════════

def test_ensure_suffix_appends_when_missing():
    transformer = vcr.VCR.ensure_suffix(".yml")
    assert transformer("recording") == "recording.yml"


def test_ensure_suffix_preserves_when_present():
    transformer = vcr.VCR.ensure_suffix(".yml")
    assert transformer("recording.yml") == "recording.yml"


# ═══════════════════════════════════════════════════════════════
# Filesystem Persister
# ═══════════════════════════════════════════════════════════════

def test_filesystem_persister_save_creates_parent_directories(tmp_path):
    deep = tmp_path / "a" / "b" / "c" / "tape.json"
    FilesystemPersister.save_cassette(
        str(deep),
        {"version": 1, "interactions": []},
        InMemoryJsonSerializer,
    )
    assert deep.exists()


def test_filesystem_persister_load_missing_raises_cassette_not_found_error(tmp_path):
    with pytest.raises(CassetteNotFoundError):
        FilesystemPersister.load_cassette(
            str(tmp_path / "does-not-exist.json"), InMemoryJsonSerializer
        )


def test_filesystem_persister_load_malformed_raises_cassette_decode_error(tmp_path):
    bad = tmp_path / "corrupt.json"
    bad.write_bytes(b"\xfe\xed")
    with pytest.raises(CassetteDecodeError):
        FilesystemPersister.load_cassette(str(bad), InMemoryJsonSerializer)


# ═══════════════════════════════════════════════════════════════
# Error Types
# ═══════════════════════════════════════════════════════════════

def test_error_types_are_distinct_exception_classes():
    assert issubclass(CannotOverwriteExistingCassetteException, Exception)
    assert issubclass(CassetteNotFoundError, Exception)
    assert issubclass(CassetteDecodeError, Exception)
    assert CannotOverwriteExistingCassetteException is not CassetteNotFoundError
    assert CassetteNotFoundError is not CassetteDecodeError


def test_cannot_overwrite_exception_can_be_raised_and_caught():
    with pytest.raises(CannotOverwriteExistingCassetteException):
        raise CannotOverwriteExistingCassetteException()


# ═══════════════════════════════════════════════════════════════
# VCR Configuration Defaults
# ═══════════════════════════════════════════════════════════════

def test_vcr_default_match_on_includes_standard_components():
    recorder = vcr.VCR()
    expected = {"method", "scheme", "host", "port", "path", "query"}
    assert set(recorder.match_on) == expected
