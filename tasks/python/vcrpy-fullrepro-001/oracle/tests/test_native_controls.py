from __future__ import annotations

from pathlib import Path

import vcr

from .native_support import decoded_view, expect_assertion, request_view, response


def test_a01(tmp_path: Path) -> None:
    assert vcr.VCR is vcr.config.VCR
    assert vcr.mode is vcr.record_mode.RecordMode
    assert type(vcr.default_vcr) is vcr.config.VCR
    assert vcr.use_cassette.__self__ is vcr.default_vcr
    assert vcr.use_cassette.__func__ is vcr.config.VCR.use_cassette
    assert vcr.request.Request and vcr.cassette.Cassette and vcr.matchers and vcr.serialize
    assert {item.value for item in vcr.record_mode.RecordMode} >= {"once", "none", "new_episodes", "all", "any"}


def test_a02(tmp_path: Path) -> None:
    request = vcr.request.Request("post", "HTTP://Example.COM:80/a%20b?z=2", b"x", {})
    assert request.uri == request.url == "HTTP://Example.COM:80/a%20b?z=2"
    assert (request.scheme, request.protocol, request.host, request.port, request.path) == ("http", "http", "example.com", 80, "/a%20b")
    assert request.method == "post" and request.body == b"x"


def test_a03(tmp_path: Path) -> None:
    request = vcr.request.Request("GET", "http://example.test/p?z=2&blank=&z=1", None, {"X-Test": ["one", "two"]})
    assert request.query == [("z", "1"), ("z", "2")]
    assert dict(request.headers) == {"X-Test": "one"}


def test_a04(tmp_path: Path) -> None:
    base = vcr.request.Request("GET", "http://host.test:81/p?a=1&a=2", None, {})
    reordered = vcr.request.Request("GET", "http://host.test:81/p?a=2&a=1", None, {})
    assert vcr.matchers.query(base, reordered) is None
    expect_assertion(lambda: vcr.matchers.method(base, vcr.request.Request("POST", base.uri, None, {})))
    expect_assertion(lambda: vcr.matchers.host(base, vcr.request.Request("GET", "http://other.test:81/p?a=1&a=2", None, {})))


def test_a05(tmp_path: Path) -> None:
    raw = vcr.request.Request("POST", "http://body.test/", b"abc", {"Content-Type": ["text/plain"]})
    assert vcr.matchers.body(raw, raw) is None
    expect_assertion(lambda: vcr.matchers.body(raw, vcr.request.Request("POST", raw.uri, b"abd", {"Content-Type": ["text/plain"]})))
    left = vcr.request.Request("POST", raw.uri, b'{"a":1,"b":[2]}', {"Content-Type": ["application/json"]})
    right = vcr.request.Request("POST", raw.uri, b'{"b":[2],"a":1}', {"Content-Type": ["application/json; charset=utf-8"]})
    assert vcr.matchers.body(left, right) is None


def test_a06(tmp_path: Path) -> None:
    cassette = vcr.cassette.Cassette(str(tmp_path / "unused.json"), serializer=vcr.serializers.jsonserializer, persister=vcr.persisters.filesystem.FilesystemPersister)
    one = vcr.request.Request("GET", "http://example.test/one", None, {})
    two = vcr.request.Request("GET", "http://example.test/two", b"two", {})
    cassette.append(one, response(b"one", 201)); cassette.append(two, response(b"two", 202))
    assert cassette.requests == [one, two]
    assert [item["status"]["code"] for item in cassette.responses] == [201, 202]
    assert cassette.play_count == 0


def test_a07(tmp_path: Path) -> None:
    cassette = vcr.cassette.Cassette(str(tmp_path / "unused.json"), serializer=vcr.serializers.jsonserializer, persister=vcr.persisters.filesystem.FilesystemPersister)
    request = vcr.request.Request("GET", "http://example.test/one", None, {})
    cassette.append(request, response(b"first", 201)); cassette.append(request, response(b"second", 202))
    assert cassette.play_response(request)["body"]["string"] == b"first"
    assert cassette.play_response(request)["body"]["string"] == b"second"
    assert cassette.play_count == 2
    cassette.rewind(); assert cassette.play_count == 0


def test_a08(tmp_path: Path) -> None:
    request = vcr.request.Request("POST", "http://example.test/two", b"body", {"X": ["1"]})
    value = {"requests": [request], "responses": [response(b"two", 201)]}
    encoded = vcr.serialize.serialize(value, vcr.serializers.jsonserializer)
    assert decoded_view(vcr.serialize.deserialize(encoded, vcr.serializers.jsonserializer)) == {"requests": [request_view(request)], "responses": [response(b"two", 201)]}


def test_i01(tmp_path: Path) -> None:
    values = ["method"]
    owner = vcr.VCR(match_on=values); sibling = vcr.VCR()
    values.append("host")
    assert owner.match_on == ["method", "host"]
    assert sibling.match_on != owner.match_on
    assert vcr.VCR.ensure_suffix(".yaml")("name") == "name.yaml"


def test_i02(tmp_path: Path) -> None:
    request = vcr.request.Request("GET", "http://filter.test/p?keep=1&secret=2", None, {"Secret": ["s"], "Keep": ["k"]})
    filtered = vcr.filters.remove_headers(request, ["secret"])
    filtered = vcr.filters.remove_query_parameters(filtered, ["secret"])
    assert dict(filtered.headers) == {"Keep": "k"}
    assert filtered.query == [("keep", "1")]


def test_i03(tmp_path: Path) -> None:
    request = vcr.request.Request("POST", "http://format.test/p?a=1", b"payload", {"X": ["1"]})
    value = {"requests": [request], "responses": [response(b"reply")]}
    json_value = decoded_view(vcr.serialize.deserialize(vcr.serialize.serialize(value, vcr.serializers.jsonserializer), vcr.serializers.jsonserializer))
    yaml_value = decoded_view(vcr.serialize.deserialize(vcr.serialize.serialize(value, vcr.serializers.yamlserializer), vcr.serializers.yamlserializer))
    assert json_value == yaml_value


def test_i04(tmp_path: Path) -> None:
    path = tmp_path / "new" / "nested" / "cassette.json"
    request = vcr.request.Request("GET", "http://example.test/one", None, {})
    value = {"requests": [request], "responses": [response(b"one")]}
    vcr.persisters.filesystem.FilesystemPersister.save_cassette(str(path), value, vcr.serializers.jsonserializer)
    restored = vcr.persisters.filesystem.FilesystemPersister.load_cassette(str(path), vcr.serializers.jsonserializer)
    assert request_view(restored[0][0]) == request_view(request) and restored[1][0]["body"]["string"] == b"one"


def test_s01(tmp_path: Path) -> None:
    request = vcr.request.Request("GET", "http://system.test/item", None, {})
    value = {"requests": [request, request], "responses": [response(b"one"), response(b"two")]}
    restored = vcr.serialize.deserialize(vcr.serialize.serialize(value, vcr.serializers.jsonserializer), vcr.serializers.jsonserializer)
    cassette = vcr.cassette.Cassette(str(tmp_path / "unused.json"), serializer=vcr.serializers.jsonserializer, persister=vcr.persisters.filesystem.FilesystemPersister)
    for req, reply in zip(*restored): cassette.append(req, reply)
    assert [cassette.play_response(request)["body"]["string"] for _ in range(2)] == [b"one", b"two"]
    cassette.rewind(); assert cassette.play_response(request)["body"]["string"] == b"one"


def test_s02(tmp_path: Path) -> None:
    path = tmp_path / "filtered.json"
    request = vcr.request.Request("GET", "http://system.test/p?keep=1&secret=2", None, {"Secret": ["x"], "Keep": ["y"]})
    filtered = vcr.filters.remove_query_parameters(vcr.filters.remove_headers(request, ["secret"]), ["secret"])
    value = {"requests": [filtered], "responses": [response(b"ok")]}
    vcr.persisters.filesystem.FilesystemPersister.save_cassette(str(path), value, vcr.serializers.jsonserializer)
    restored = vcr.persisters.filesystem.FilesystemPersister.load_cassette(str(path), vcr.serializers.jsonserializer)
    assert request_view(restored[0][0]) == request_view(filtered) and restored[1][0]["body"]["string"] == b"ok"
