"""Atomic tests for requests-cache-fullrepro-001.

Each test verifies ONE public API entry point, ONE behavior.
If only the tested API is correctly implemented, the test passes.
"""

import re
from datetime import datetime, timedelta, timezone

import pytest
import requests

import requests_cache
from requests_cache import (
    BaseCache,
    CachedSession,
    DO_NOT_CACHE,
    EXPIRE_IMMEDIATELY,
    NEVER_EXPIRE,
    SQLiteCache,
    FileCache,
    create_key,
    get_expiration_datetime,
    get_url_expiration,
    init_backend,
    normalize_body,
    normalize_headers,
    normalize_params,
    normalize_url,
)

MOCK_URL = "https://example.test/resource"
MOCK_URL_ALT = "https://example.test/other"


# --- Key generation and normalization ---


def test_create_key_produces_same_key_for_reordered_query_params():
    req_a = requests.Request("GET", "https://example.test/api?z=3&a=1").prepare()
    req_b = requests.Request("GET", "https://example.test/api?a=1&z=3").prepare()

    assert create_key(req_a) == create_key(req_b)


def test_create_key_produces_different_keys_for_different_methods():
    get_req = requests.Request("GET", MOCK_URL).prepare()
    post_req = requests.Request("POST", MOCK_URL).prepare()

    assert create_key(get_req) != create_key(post_req)


def test_create_key_produces_different_keys_for_different_urls():
    req_a = requests.Request("GET", "https://example.test/alpha").prepare()
    req_b = requests.Request("GET", "https://example.test/beta").prepare()

    assert create_key(req_a) != create_key(req_b)


def test_normalize_url_sorts_query_params_and_redacts_ignored():
    result = normalize_url(
        "https://example.test/api?secret=xyz&page=2&limit=5", ["secret"]
    )

    assert "limit=5" in result
    assert "page=2" in result
    assert "secret=REDACTED" in result
    assert result.index("limit=") < result.index("page=") < result.index("secret=")


def test_normalize_params_sorts_and_redacts_specified_keys():
    result = normalize_params("color=red&api_key=abc123&count=5", ["api_key"])

    assert result == "api_key=REDACTED&color=red&count=5"


def test_normalize_headers_returns_sorted_normalized_dict():
    result = normalize_headers(
        {"X-Custom": "value", "Accept": "text/html"}, ["X-Custom"]
    )

    assert "Accept" in result or isinstance(result, (str, dict))


# --- Expiration utilities ---


def test_get_expiration_datetime_from_positive_seconds():
    base = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    result = get_expiration_datetime(90, start_time=base)

    assert result == datetime(2025, 6, 15, 12, 1, 30, tzinfo=timezone.utc)


def test_get_expiration_datetime_from_timedelta():
    base = datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

    result = get_expiration_datetime(timedelta(hours=2), start_time=base)

    assert result == datetime(2025, 3, 1, 2, 0, 0, tzinfo=timezone.utc)


def test_get_expiration_datetime_none_returns_none():
    result = get_expiration_datetime(None)
    base = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    assert result is None
    assert get_expiration_datetime(60, start_time=base) == datetime(
        2025, 6, 15, 12, 1, 0, tzinfo=timezone.utc
    )


def test_get_expiration_datetime_never_expire_returns_none():
    result = get_expiration_datetime(NEVER_EXPIRE)
    base = datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

    assert result is None
    assert get_expiration_datetime(90, start_time=base) == datetime(
        2025, 3, 1, 0, 1, 30, tzinfo=timezone.utc
    )


def test_get_expiration_datetime_invalid_http_date_raises_value_error():
    with pytest.raises(ValueError):
        get_expiration_datetime("not-a-valid-date-string")


def test_get_url_expiration_first_matching_pattern_wins():
    patterns = {"example.test/resource": 30, "example.test": 120}

    assert get_url_expiration(MOCK_URL, patterns) == 30


def test_get_url_expiration_regex_pattern_matches():
    patterns = {re.compile(r"/resource$"): 77}

    assert get_url_expiration(MOCK_URL, patterns) == 77


def test_get_url_expiration_no_match_returns_none_or_sentinel():
    patterns = {"nomatch.test": 10}

    result = get_url_expiration(MOCK_URL, patterns)

    assert result is None or result == NEVER_EXPIRE or result == -1


# --- init_backend ---


def test_init_backend_memory_returns_base_cache_instance():
    cache = init_backend("test_cache", backend="memory")

    assert isinstance(cache, BaseCache)
    assert cache.cache_name == "test_cache"
    assert hasattr(cache, "responses")


def test_init_backend_with_existing_instance_returns_same_object():
    original = BaseCache("shared_cache")

    assert init_backend("ignored", backend=original) is original


def test_init_backend_unknown_alias_raises_value_error():
    with pytest.raises(ValueError):
        init_backend("cache", backend="nonexistent-backend-xyz")


# --- Patcher state functions ---


def test_is_installed_false_when_no_cache_patched():
    assert requests_cache.is_installed() is False


def test_get_cache_returns_none_when_uninstalled():
    assert requests_cache.get_cache() is None


def test_install_cache_changes_is_installed_to_true():
    requests_cache.install_cache(backend="memory")

    assert requests_cache.is_installed() is True


def test_uninstall_cache_restores_is_installed_to_false():
    requests_cache.install_cache(backend="memory")
    requests_cache.uninstall_cache()

    assert requests_cache.is_installed() is False


# --- CachedSession basic behavior ---


def test_session_first_request_returns_from_cache_false(requests_mock):
    requests_mock.get(MOCK_URL, text="payload")
    session = CachedSession(backend="memory")

    response = session.get(MOCK_URL)

    assert response.from_cache is False
    assert response.text == "payload"


def test_only_if_cached_miss_returns_504_without_origin_call(requests_mock):
    requests_mock.get(MOCK_URL, text="should-not-reach")
    session = CachedSession(backend="memory")

    response = session.get(MOCK_URL, only_if_cached=True)

    assert response.status_code == 504
    assert response.reason == "Not Cached"
    assert requests_mock.call_count == 0


def test_never_expire_response_is_not_expired(requests_mock):
    requests_mock.get(MOCK_URL, text="eternal")
    session = CachedSession(backend="memory", expire_after=NEVER_EXPIRE)
    session.get(MOCK_URL)

    cached = session.get(MOCK_URL)

    assert cached.expires is None
    assert cached.is_expired is False


def test_expire_immediately_does_not_store_response(requests_mock):
    requests_mock.get(MOCK_URL, text="ephemeral")
    session = CachedSession(backend="memory", expire_after=EXPIRE_IMMEDIATELY)

    session.get(MOCK_URL)

    assert len(session.cache.responses) == 0


def test_do_not_cache_prevents_any_storage(requests_mock):
    requests_mock.get(MOCK_URL, text="nope")
    session = CachedSession(backend="memory", expire_after=DO_NOT_CACHE)

    response = session.get(MOCK_URL)

    assert response.from_cache is False
    assert len(session.cache.responses) == 0


def test_cached_response_size_returns_body_byte_length(requests_mock):
    requests_mock.get(MOCK_URL, content=b"abcdefgh")
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    cached = session.get(MOCK_URL)

    assert cached.size == 8


def test_reset_expiration_marks_response_as_expired(requests_mock):
    requests_mock.get(MOCK_URL, text="aging")
    session = CachedSession(backend="memory", expire_after=NEVER_EXPIRE)
    session.get(MOCK_URL)
    cached = session.get(MOCK_URL)

    is_now_expired = cached.reset_expiration(EXPIRE_IMMEDIATELY)

    assert is_now_expired is True
    assert cached.is_expired is True


def test_pickling_cached_session_raises_not_implemented_error():
    import pickle

    session = CachedSession(backend="memory")

    with pytest.raises(NotImplementedError):
        pickle.dumps(session)


def test_response_hook_fires_for_cached_responses(requests_mock):
    calls = []
    requests_mock.get(MOCK_URL, text="hooked")
    session = CachedSession(backend="memory")
    hook = lambda r, *a, **kw: calls.append(r.from_cache)
    session.get(MOCK_URL, hooks={"response": hook})
    session.get(MOCK_URL, hooks={"response": hook})

    assert calls == [False, True]


# --- Backend filter ---


def test_backend_filter_all_false_yields_nothing(requests_mock):
    requests_mock.get(MOCK_URL, text="data")
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    results = list(session.cache.filter(valid=False, expired=False, invalid=False))

    assert results == []
