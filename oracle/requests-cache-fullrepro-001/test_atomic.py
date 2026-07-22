# Spec2Repo oracle - atomic tests for requests-cache-fullrepro-001
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests

import requests_cache
from requests_cache import (
    BaseCache,
    CachedSession,
    DO_NOT_CACHE,
    EXPIRE_IMMEDIATELY,
    NEVER_EXPIRE,
    SerializerPipeline,
    Stage,
    create_key,
    get_expiration_datetime,
    get_url_expiration,
    init_backend,
    normalize_params,
    normalize_url,
)


URL = "https://example.test/data"


@pytest.fixture(autouse=True)
def cleanup_patcher():
    requests_cache.uninstall_cache()
    yield
    requests_cache.uninstall_cache()


def test_only_if_cached_miss_returns_504_without_origin_call(requests_mock):
    requests_mock.get(URL, text="should-not-be-used")
    session = CachedSession(backend="memory")

    response = session.get(URL, only_if_cached=True)

    assert response.status_code == 504
    assert response.reason == "Not Cached"
    assert requests_mock.call_count == 0


def test_only_if_cached_hit_returns_cached_response(requests_mock):
    requests_mock.get(URL, text="cached")
    session = CachedSession(backend="memory")
    session.get(URL)

    cached = session.get(URL, only_if_cached=True)

    assert cached.from_cache is True
    assert cached.text == "cached"
    assert requests_mock.call_count == 1


def test_query_parameter_order_normalizes_to_same_key():
    req1 = requests.Request("GET", "https://example.test/items?b=2&a=1").prepare()
    req2 = requests.Request("GET", "https://example.test/items?a=1&b=2").prepare()

    assert create_key(req1) == create_key(req2)


def test_normalize_url_redacts_ignored_parameters():
    normalized = normalize_url("https://example.test/items?token=abc&id=1", ["token"])

    assert normalized == "https://example.test/items?id=1&token=REDACTED"


def test_normalize_params_sorts_and_redacts_values():
    normalized = normalize_params("b=2&token=abc&a=1", ["token"])

    assert normalized == "a=1&b=2&token=REDACTED"


def test_expire_after_positive_seconds_sets_future_expiration(requests_mock):
    requests_mock.get(URL, text="expires")
    session = CachedSession(backend="memory", expire_after=60)

    session.get(URL)
    response = session.get(URL)

    assert response.expires is not None
    assert 0 < response.expires_delta <= 60


def test_never_expire_has_no_expiration_datetime(requests_mock):
    requests_mock.get(URL, text="forever")
    session = CachedSession(backend="memory", expire_after=NEVER_EXPIRE)

    response = session.get(URL)

    assert response.expires is None
    assert response.is_expired is False


def test_expire_immediately_creates_expired_cached_response(requests_mock):
    requests_mock.get(URL, text="expired")
    session = CachedSession(backend="memory", expire_after=EXPIRE_IMMEDIATELY)

    response = session.get(URL)

    assert response.from_cache is False
    assert len(session.cache.responses) == 0


def test_url_expiration_overrides_session_expiration(requests_mock):
    requests_mock.get(URL, text="url-expiration")
    session = CachedSession(backend="memory", expire_after=60, urls_expire_after={"example.test": 120})

    session.get(URL)
    response = session.get(URL)

    assert 100 <= response.expires_delta <= 120


def test_first_matching_url_expiration_pattern_wins():
    patterns = {"example.test": 10, "example.test/data": 20}

    assert get_url_expiration(URL, patterns) == 10


def test_regex_url_expiration_pattern_matches():
    import re

    patterns = {re.compile(r"/data$"): 33}

    assert get_url_expiration(URL, patterns) == 33


def test_get_expiration_datetime_accepts_timedelta():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    expires = get_expiration_datetime(timedelta(seconds=5), start_time=start)

    assert expires == datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc)


def test_get_expiration_datetime_invalid_http_date_raises_value_error():
    with pytest.raises(ValueError):
        get_expiration_datetime("not an http date")


def test_reset_expiration_updates_cached_response_state(requests_mock):
    requests_mock.get(URL, text="reset")
    session = CachedSession(backend="memory", expire_after=NEVER_EXPIRE)
    session.get(URL)
    response = session.get(URL)

    expired = response.reset_expiration(EXPIRE_IMMEDIATELY)

    assert expired is True
    assert response.is_expired is True


def test_stage_wraps_object_dump_and_load_methods():
    class Codec:
        def dumps(self, value):
            return f"encoded:{value}"

        def loads(self, value):
            return value.removeprefix("encoded:")

    stage = Stage(Codec())

    assert stage.dumps("value") == "encoded:value"
    assert stage.loads("encoded:value") == "value"


def test_serializer_pipeline_runs_dumps_and_loads_in_order():
    class Prefix:
        def dumps(self, value):
            return f"p:{value}"

        def loads(self, value):
            return value.removeprefix("p:")

    class Suffix:
        def dumps(self, value):
            return f"{value}:s"

        def loads(self, value):
            return value.removesuffix(":s")

    pipeline = SerializerPipeline([Stage(Prefix()), Stage(Suffix())])

    encoded = pipeline.dumps("value")

    assert encoded == "p:value:s"
    assert pipeline.loads(encoded) == "value"


def test_serializer_pipeline_copy_preserves_behavior():
    pipeline = SerializerPipeline([Stage(dumps=lambda value: value.upper(), loads=lambda value: value.lower())])
    copied = pipeline.copy()

    assert copied is not pipeline
    assert copied.dumps("abc") == "ABC"
    assert copied.loads("ABC") == "abc"


def test_cached_response_size_reports_body_length(requests_mock):
    requests_mock.get(URL, content=b"12345")
    session = CachedSession(backend="memory")

    session.get(URL)
    cached = session.get(URL)

    assert cached.size == 5


def test_recreate_keys_keeps_response_reachable(requests_mock):
    requests_mock.get(URL, text="rekey")
    session = CachedSession(backend="memory")
    session.get(URL)

    session.cache.recreate_keys()

    assert session.get(URL).from_cache is True


def test_response_hook_runs_for_cached_response(requests_mock):
    calls = []
    requests_mock.get(URL, text="hook")
    session = CachedSession(backend="memory")
    session.get(URL, hooks={"response": lambda response, *args, **kwargs: calls.append(response)})
    session.get(URL, hooks={"response": lambda response, *args, **kwargs: calls.append(response)})

    assert len(calls) >= 2
    assert calls[-1].from_cache is True
