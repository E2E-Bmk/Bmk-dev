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


def test_session_get_caches_second_equivalent_request(requests_mock):
    requests_mock.get(URL, [{"text": "first"}, {"text": "second"}])
    session = CachedSession(backend="memory")

    first = session.get(URL)
    second = session.get(URL)

    assert first.from_cache is False
    assert second.from_cache is True
    assert second.text == "first"
    assert requests_mock.call_count == 1


def test_cached_response_is_visible_in_cache_mapping(requests_mock):
    requests_mock.get(URL, text="visible")
    session = CachedSession(backend="memory")

    response = session.get(URL)

    assert session.cache.contains(url=URL)
    assert response.cache_key in session.cache.responses


def test_cache_clear_removes_response_and_next_request_misses(requests_mock):
    requests_mock.get(URL, [{"text": "one"}, {"text": "two"}])
    session = CachedSession(backend="memory")
    session.get(URL)

    session.cache.clear()
    second = session.get(URL)

    assert second.from_cache is False
    assert second.text == "two"
    assert requests_mock.call_count == 2


def test_cache_delete_by_url_removes_matching_response(requests_mock):
    requests_mock.get(URL, [{"text": "one"}, {"text": "two"}])
    session = CachedSession(backend="memory")
    session.get(URL)

    session.cache.delete(urls=[URL])
    second = session.get(URL)

    assert second.from_cache is False
    assert second.text == "two"


def test_cache_delete_missing_key_is_ignored(requests_mock):
    requests_mock.get(URL, text="ok")
    session = CachedSession(backend="memory")
    session.get(URL)

    session.cache.delete("missing-cache-key")

    assert session.cache.contains(url=URL)


def test_cache_contains_request_uses_same_key_settings(requests_mock):
    requests_mock.get("https://example.test/items?a=1&token=x", text="ok")
    session = CachedSession(backend="memory", ignored_parameters=["token"])
    response = session.get("https://example.test/items?a=1&token=x")

    request = requests.Request("GET", "https://example.test/items?token=y&a=1").prepare()

    assert session.cache.contains(request=request)
    assert response.cache_key == session.cache.create_key(request)


def test_only_if_cached_miss_returns_504_without_origin_call(requests_mock):
    requests_mock.get(URL, text="should-not-be-used")
    session = CachedSession(backend="memory")

    response = session.get(URL, only_if_cached=True)

    assert response.status_code == 504
    assert response.reason == "Not Cached"
    assert requests_mock.call_count == 0


def test_force_refresh_overwrites_existing_cache_entry(requests_mock):
    requests_mock.get(URL, [{"text": "old"}, {"text": "new"}])
    session = CachedSession(backend="memory")
    session.get(URL)

    refreshed = session.get(URL, force_refresh=True)
    cached = session.get(URL)

    assert refreshed.from_cache is False
    assert cached.from_cache is True
    assert cached.text == "new"
    assert requests_mock.call_count == 2


def test_only_if_cached_hit_returns_cached_response(requests_mock):
    requests_mock.get(URL, text="cached")
    session = CachedSession(backend="memory")
    session.get(URL)

    cached = session.get(URL, only_if_cached=True)

    assert cached.from_cache is True
    assert cached.text == "cached"
    assert requests_mock.call_count == 1


def test_read_only_session_reads_existing_cache_but_does_not_write_misses(requests_mock):
    requests_mock.get(URL, [{"text": "seed"}, {"text": "miss"}])
    requests_mock.get("https://example.test/miss", text="miss")
    seed = CachedSession(backend="memory")
    seed.get(URL)

    readonly = CachedSession(backend=seed.cache, read_only=True)
    hit = readonly.get(URL)
    miss = readonly.get("https://example.test/miss")

    assert hit.from_cache is True
    assert miss.from_cache is False
    assert not readonly.cache.contains(url="https://example.test/miss")


def test_session_cache_disabled_bypasses_read_and_write(requests_mock):
    requests_mock.get(URL, [{"text": "one"}, {"text": "two"}, {"text": "three"}])
    session = CachedSession(backend="memory")
    session.get(URL)

    with session.cache_disabled():
        bypassed = session.get(URL)
    cached = session.get(URL)

    assert bypassed.from_cache is False
    assert bypassed.text == "two"
    assert cached.from_cache is True
    assert cached.text == "one"


def test_default_policy_does_not_cache_post_or_404(requests_mock):
    requests_mock.post("https://example.test/post", text="posted")
    requests_mock.get("https://example.test/missing", status_code=404, text="missing")
    session = CachedSession(backend="memory")

    session.post("https://example.test/post")
    session.get("https://example.test/missing")

    assert len(session.cache.responses) == 0


def test_custom_policy_caches_post_and_404(requests_mock):
    requests_mock.post("https://example.test/post", [{"text": "posted"}, {"text": "changed"}])
    requests_mock.get("https://example.test/missing", status_code=404, text="missing")
    session = CachedSession(
        backend="memory", allowable_methods=("GET", "POST"), allowable_codes=(200, 404)
    )

    first = session.post("https://example.test/post")
    second = session.post("https://example.test/post")
    missing = session.get("https://example.test/missing")

    assert first.from_cache is False
    assert second.from_cache is True
    assert second.text == "posted"
    assert missing.status_code == 404
    assert len(session.cache.responses) == 2


def test_filter_fn_false_prevents_cache_write(requests_mock):
    requests_mock.get(URL, text="reject")
    session = CachedSession(backend="memory", filter_fn=lambda response: False)

    response = session.get(URL)

    assert response.from_cache is False
    assert len(session.cache.responses) == 0


def test_filter_fn_deletes_previous_cached_response(requests_mock):
    requests_mock.get(URL, [{"text": "keep"}, {"text": "drop"}])
    session = CachedSession(backend="memory")
    session.get(URL)
    session.settings.filter_fn = lambda response: False

    response = session.get(URL, force_refresh=True)

    assert response.text == "drop"
    assert not session.cache.contains(url=URL)


def test_ignored_query_parameter_shares_cache_entry_and_redacts_url(requests_mock):
    requests_mock.get("https://example.test/items?id=1&token=a", text="first")
    requests_mock.get("https://example.test/items?id=1&token=b", text="second")
    session = CachedSession(backend="memory", ignored_parameters=["token"])

    first = session.get("https://example.test/items?id=1&token=a")
    second = session.get("https://example.test/items?id=1&token=b")
    stored = next(iter(session.cache.responses.values()))

    assert first.from_cache is False
    assert second.from_cache is True
    assert second.text == "first"
    assert "token=REDACTED" in stored.url


def test_non_ignored_query_parameter_makes_distinct_entries(requests_mock):
    requests_mock.get("https://example.test/items?id=1", text="one")
    requests_mock.get("https://example.test/items?id=2", text="two")
    session = CachedSession(backend="memory", ignored_parameters=[])

    one = session.get("https://example.test/items?id=1")
    two = session.get("https://example.test/items?id=2")

    assert one.text == "one"
    assert two.text == "two"
    assert len(session.cache.responses) == 2


def test_query_parameter_order_normalizes_to_same_key():
    req1 = requests.Request("GET", "https://example.test/items?b=2&a=1").prepare()
    req2 = requests.Request("GET", "https://example.test/items?a=1&b=2").prepare()

    assert create_key(req1) == create_key(req2)


def test_match_headers_list_differentiates_selected_header(requests_mock):
    requests_mock.get(URL, [{"text": "json"}, {"text": "html"}])
    session = CachedSession(backend="memory", match_headers=["Accept"])

    json_response = session.get(URL, headers={"Accept": "application/json"})
    html_response = session.get(URL, headers={"Accept": "text/html"})

    assert json_response.text == "json"
    assert html_response.text == "html"
    assert len(session.cache.responses) == 2


def test_match_headers_false_ignores_header_differences(requests_mock):
    requests_mock.get(URL, [{"text": "json"}, {"text": "html"}])
    session = CachedSession(backend="memory", match_headers=False)

    first = session.get(URL, headers={"Accept": "application/json"})
    second = session.get(URL, headers={"Accept": "text/html"})

    assert first.from_cache is False
    assert second.from_cache is True
    assert second.text == "json"


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


def test_do_not_cache_prevents_storage_for_session(requests_mock):
    requests_mock.get(URL, text="skip")
    session = CachedSession(backend="memory", expire_after=DO_NOT_CACHE)

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


def test_stale_if_error_returns_expired_cached_response(requests_mock):
    requests_mock.get(URL, text="stale")
    session = CachedSession(backend="memory", expire_after=NEVER_EXPIRE, stale_if_error=True)
    session.get(URL)
    session.get(URL).reset_expiration(EXPIRE_IMMEDIATELY)
    requests_mock.reset()
    requests_mock.get(URL, exc=requests.exceptions.ConnectTimeout)

    response = session.get(URL)

    assert response.from_cache is True
    assert response.text == "stale"


def test_stale_if_error_false_reraises_origin_error(requests_mock):
    requests_mock.get(URL, text="stale")
    session = CachedSession(backend="memory", expire_after=NEVER_EXPIRE, stale_if_error=False)
    session.get(URL)
    session.get(URL).reset_expiration(EXPIRE_IMMEDIATELY)
    requests_mock.reset()
    requests_mock.get(URL, exc=requests.exceptions.ConnectTimeout)

    with pytest.raises(requests.exceptions.ConnectTimeout):
        session.get(URL)


def test_init_backend_memory_returns_base_cache():
    cache = init_backend("name", backend="memory")

    assert isinstance(cache, BaseCache)
    assert cache.cache_name == "name"


def test_init_backend_instance_returns_same_object():
    cache = BaseCache("shared")

    assert init_backend("http_cache", backend=cache) is cache


def test_init_backend_unknown_alias_raises_value_error():
    with pytest.raises(ValueError):
        init_backend("name", backend="unknown-backend")


def test_sqlite_backend_persists_across_sessions(tmp_path, requests_mock):
    cache_name = str(tmp_path / "http_cache")
    requests_mock.get(URL, text="persisted")
    first = CachedSession(cache_name, backend="sqlite")
    first.get(URL)
    first.close()

    second = CachedSession(cache_name, backend="sqlite")
    response = second.get(URL)
    second.close()

    assert response.from_cache is True
    assert Path(cache_name + ".sqlite").exists()


def test_filesystem_backend_persists_across_sessions(tmp_path, requests_mock):
    cache_dir = str(tmp_path / "fs_cache")
    requests_mock.get(URL, text="file-persisted")
    first = CachedSession(cache_dir, backend="filesystem", serializer="json")
    first.get(URL)
    first.close()

    second = CachedSession(cache_dir, backend="filesystem", serializer="json")
    response = second.get(URL)
    second.close()

    assert response.from_cache is True
    assert any(Path(cache_dir).rglob("*"))


def test_backend_filter_yields_valid_cached_response(requests_mock):
    requests_mock.get(URL, text="filter")
    session = CachedSession(backend="memory")
    session.get(URL)

    results = list(session.cache.filter(valid=True, expired=False))

    assert len(results) == 1
    assert results[0].url == URL


def test_backend_filter_with_all_false_yields_nothing(requests_mock):
    requests_mock.get(URL, text="filter")
    session = CachedSession(backend="memory")
    session.get(URL)

    assert list(session.cache.filter(valid=False, expired=False, invalid=False)) == []


def test_backend_delete_expired_removes_only_expired_entries(requests_mock):
    requests_mock.get("https://example.test/expired", text="old")
    requests_mock.get("https://example.test/fresh", text="new")
    expired_session = CachedSession(backend="memory", expire_after=EXPIRE_IMMEDIATELY)
    expired_session.get("https://example.test/expired")
    expired_session.settings.expire_after = NEVER_EXPIRE
    expired_session.get("https://example.test/fresh")

    expired_session.cache.delete(expired=True)

    assert not expired_session.cache.contains(url="https://example.test/expired")
    assert expired_session.cache.contains(url="https://example.test/fresh")


def test_patcher_install_and_uninstall_changes_installed_state():
    assert requests_cache.is_installed() is False

    requests_cache.install_cache(backend="memory")
    assert requests_cache.is_installed() is True
    assert isinstance(requests.Session(), CachedSession)

    requests_cache.uninstall_cache()
    assert requests_cache.is_installed() is False


def test_enabled_context_restores_uninstalled_state():
    with requests_cache.enabled(backend="memory"):
        assert requests_cache.is_installed() is True
        assert requests_cache.get_cache() is not None

    assert requests_cache.is_installed() is False


def test_disabled_context_temporarily_uninstalls_and_restores():
    requests_cache.install_cache(backend="memory")
    assert requests_cache.is_installed() is True

    with requests_cache.disabled():
        assert requests_cache.is_installed() is False
    assert requests_cache.is_installed() is True


def test_top_level_clear_operates_on_installed_cache(requests_mock):
    requests_mock.get(URL, text="clear")
    requests_cache.install_cache(backend="memory")
    requests.get(URL)

    requests_cache.clear()

    assert requests_cache.get_cache() is not None
    assert len(requests_cache.get_cache().responses) == 0


def test_top_level_delete_operates_on_installed_cache(requests_mock):
    requests_mock.get(URL, text="delete")
    requests_cache.install_cache(backend="memory")
    requests.get(URL)

    requests_cache.delete(urls=[URL])

    assert not requests_cache.get_cache().contains(url=URL)


def test_get_cache_returns_none_when_uninstalled():
    requests_cache.uninstall_cache()

    assert requests_cache.get_cache() is None


def test_cached_session_pickle_state_raises_not_implemented():
    session = CachedSession(backend="memory")

    with pytest.raises(NotImplementedError):
        session.__getstate__()


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


def test_json_serializer_round_trips_cached_response(tmp_path, requests_mock):
    requests_mock.get(URL, text="json")
    cache_dir = str(tmp_path / "json_cache")
    first = CachedSession(cache_dir, backend="filesystem", serializer="json")
    first.get(URL)
    first.close()

    second = CachedSession(cache_dir, backend="filesystem", serializer="json")
    response = second.get(URL)
    second.close()

    assert response.from_cache is True
    assert response.text == "json"


def test_cached_response_size_reports_body_length(requests_mock):
    requests_mock.get(URL, content=b"12345")
    session = CachedSession(backend="memory")

    session.get(URL)
    cached = session.get(URL)

    assert cached.size == 5


def test_redirect_alias_returns_final_cached_response(requests_mock):
    requests_mock.get("https://example.test/start", status_code=302, headers={"Location": URL})
    requests_mock.get(URL, text="final")
    session = CachedSession(backend="memory")

    first = session.get("https://example.test/start")
    second = session.get("https://example.test/start")

    assert first.text == "final"
    assert second.from_cache is True
    assert second.url == URL


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


def test_sqlite_cache_db_path_property_has_sqlite_suffix(tmp_path, requests_mock):
    db_path = tmp_path / "alias_cache"
    requests_mock.get(URL, text="alias")
    session = CachedSession(backend=requests_cache.SQLiteCache(db_path))

    response = session.get(URL)
    actual_path = Path(session.cache.db_path)
    session.close()

    assert response.from_cache is False
    assert actual_path.name == "alias_cache.sqlite"
    assert actual_path.exists()
