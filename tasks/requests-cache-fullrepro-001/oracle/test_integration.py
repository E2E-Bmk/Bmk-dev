"""Integration tests for requests-cache-fullrepro-001.

Each test crosses ≥2 public API boundaries. Even if all atomic tests pass,
these can still fail because component seams don't align.
"""

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
    SQLiteCache,
    FileCache,
    create_key,
    init_backend,
    normalize_url,
)

MOCK_URL = "https://example.test/resource"
MOCK_URL_ALT = "https://example.test/other"


# --- State Consistency: session.get → cache.contains / cache.responses ---


@pytest.mark.depends_on("test_session_first_request_returns_from_cache_false")
def test_cache_hit_returns_same_content_from_cache(requests_mock):
    """Seam: state consistency between session request routing and cache storage."""
    requests_mock.get(MOCK_URL, [{"text": "original"}, {"text": "updated"}])
    session = CachedSession(backend="memory")

    first = session.get(MOCK_URL)
    second = session.get(MOCK_URL)

    assert first.from_cache is False
    assert second.from_cache is True
    assert second.text == "original"
    assert requests_mock.call_count == 1


@pytest.mark.depends_on("test_session_first_request_returns_from_cache_false")
def test_cached_response_visible_in_backend_mapping(requests_mock):
    """Seam: state consistency between session write and backend read."""
    requests_mock.get(MOCK_URL, text="stored")
    session = CachedSession(backend="memory")

    session.get(MOCK_URL)

    assert session.cache.contains(url=MOCK_URL)
    assert len(session.cache.responses) == 1


@pytest.mark.depends_on("test_session_first_request_returns_from_cache_false")
def test_cache_clear_makes_next_request_miss(requests_mock):
    """Seam: state consistency between cache.clear and session request routing."""
    requests_mock.get(MOCK_URL, [{"text": "old"}, {"text": "new"}])
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    session.cache.clear()
    after_clear = session.get(MOCK_URL)

    assert after_clear.from_cache is False
    assert after_clear.text == "new"


@pytest.mark.depends_on("test_session_first_request_returns_from_cache_false")
def test_cache_delete_by_url_makes_next_request_miss(requests_mock):
    """Seam: state consistency between cache.delete and session request routing."""
    requests_mock.get(MOCK_URL, [{"text": "cached"}, {"text": "fresh"}])
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    session.cache.delete(urls=[MOCK_URL])
    after_delete = session.get(MOCK_URL)

    assert after_delete.from_cache is False
    assert after_delete.text == "fresh"


def test_cache_delete_missing_key_is_silently_ignored(requests_mock):
    """Seam: state consistency - delete nonexistent key doesn't corrupt."""
    requests_mock.get(MOCK_URL, text="safe")
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    session.cache.delete("nonexistent-key-12345")

    assert session.cache.contains(url=MOCK_URL)


# --- Protocol Handoff: key generation → cache matching ---


def test_ignored_parameters_affect_both_key_and_stored_url(requests_mock):
    """Seam: protocol handoff between key generation and storage redaction."""
    requests_mock.get("https://example.test/items?id=7&token=abc", text="result")
    session = CachedSession(backend="memory", ignored_parameters=["token"])

    session.get("https://example.test/items?id=7&token=abc")
    hit = session.get("https://example.test/items?id=7&token=different")
    stored = next(iter(session.cache.responses.values()))

    assert hit.from_cache is True
    assert "token=REDACTED" in stored.url


def test_non_ignored_params_create_separate_cache_entries(requests_mock):
    """Seam: protocol handoff - different params → different keys → different entries."""
    requests_mock.get("https://example.test/items?page=1", text="page-one")
    requests_mock.get("https://example.test/items?page=2", text="page-two")
    session = CachedSession(backend="memory")

    session.get("https://example.test/items?page=1")
    session.get("https://example.test/items?page=2")

    assert len(session.cache.responses) == 2


def test_match_headers_list_creates_separate_entries_per_header_value(requests_mock):
    """Seam: protocol handoff between header matching config and key generation."""
    requests_mock.get(MOCK_URL, [{"text": "json-data"}, {"text": "xml-data"}])
    session = CachedSession(backend="memory", match_headers=["Accept"])

    session.get(MOCK_URL, headers={"Accept": "application/json"})
    session.get(MOCK_URL, headers={"Accept": "application/xml"})

    assert len(session.cache.responses) == 2


def test_match_headers_false_shares_entry_regardless_of_headers(requests_mock):
    """Seam: protocol handoff - disabled header matching shares key."""
    requests_mock.get(MOCK_URL, [{"text": "first"}, {"text": "second"}])
    session = CachedSession(backend="memory", match_headers=False)

    session.get(MOCK_URL, headers={"Accept": "text/plain"})
    hit = session.get(MOCK_URL, headers={"Accept": "image/png"})

    assert hit.from_cache is True
    assert hit.text == "first"


def test_contains_request_uses_same_key_settings_as_session(requests_mock):
    """Seam: protocol handoff between session key config and contains() lookup."""
    requests_mock.get("https://example.test/items?id=5&auth=xyz", text="ok")
    session = CachedSession(backend="memory", ignored_parameters=["auth"])
    session.get("https://example.test/items?id=5&auth=xyz")

    lookup_req = requests.Request(
        "GET", "https://example.test/items?auth=other&id=5"
    ).prepare()

    assert session.cache.contains(request=lookup_req)


# --- Error Propagation ---


def test_stale_if_error_returns_expired_cache_on_origin_failure(requests_mock):
    """Seam: error propagation from origin failure through stale policy."""
    requests_mock.get(MOCK_URL, text="stale-data")
    session = CachedSession(
        backend="memory", expire_after=NEVER_EXPIRE, stale_if_error=True
    )
    session.get(MOCK_URL)
    session.get(MOCK_URL).reset_expiration(EXPIRE_IMMEDIATELY)
    requests_mock.reset()
    requests_mock.get(MOCK_URL, exc=requests.exceptions.ConnectionError)

    response = session.get(MOCK_URL)

    assert response.from_cache is True
    assert response.text == "stale-data"


def test_stale_if_error_false_propagates_origin_exception(requests_mock):
    """Seam: error propagation - disabled stale policy re-raises."""
    requests_mock.get(MOCK_URL, text="will-expire")
    session = CachedSession(
        backend="memory", expire_after=NEVER_EXPIRE, stale_if_error=False
    )
    session.get(MOCK_URL)
    session.get(MOCK_URL).reset_expiration(EXPIRE_IMMEDIATELY)
    requests_mock.reset()
    requests_mock.get(MOCK_URL, exc=requests.exceptions.ConnectionError)

    with pytest.raises(requests.exceptions.ConnectionError):
        session.get(MOCK_URL)


# --- Config Interaction ---


def test_force_refresh_overwrites_existing_cached_entry(requests_mock):
    """Seam: config interaction between force_refresh and cache write."""
    requests_mock.get(MOCK_URL, [{"text": "stale"}, {"text": "fresh"}])
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    refreshed = session.get(MOCK_URL, force_refresh=True)
    after_refresh = session.get(MOCK_URL)

    assert refreshed.from_cache is False
    assert after_refresh.from_cache is True
    assert after_refresh.text == "fresh"


def test_read_only_session_serves_hits_but_does_not_write_misses(requests_mock):
    """Seam: config interaction between read_only mode and cache write policy."""
    requests_mock.get(MOCK_URL, text="seed")
    requests_mock.get(MOCK_URL_ALT, text="miss")
    seed = CachedSession(backend="memory")
    seed.get(MOCK_URL)

    readonly = CachedSession(backend=seed.cache, read_only=True)
    hit = readonly.get(MOCK_URL)
    miss = readonly.get(MOCK_URL_ALT)

    assert hit.from_cache is True
    assert miss.from_cache is False
    assert not readonly.cache.contains(url=MOCK_URL_ALT)


def test_cache_disabled_context_bypasses_reads_and_writes(requests_mock):
    """Seam: config interaction between cache_disabled and cache state."""
    requests_mock.get(MOCK_URL, [{"text": "cached"}, {"text": "bypass"}, {"text": "third"}])
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    with session.cache_disabled():
        bypassed = session.get(MOCK_URL)
    still_cached = session.get(MOCK_URL)

    assert bypassed.from_cache is False
    assert bypassed.text == "bypass"
    assert still_cached.from_cache is True
    assert still_cached.text == "cached"


def test_filter_fn_false_prevents_cache_storage(requests_mock):
    """Seam: config interaction between filter_fn and cache write."""
    requests_mock.get(MOCK_URL, text="rejected")
    session = CachedSession(backend="memory", filter_fn=lambda r: False)

    response = session.get(MOCK_URL)

    assert response.from_cache is False
    assert len(session.cache.responses) == 0


def test_allowable_methods_controls_which_methods_are_cached(requests_mock):
    """Seam: config interaction between allowable_methods and write policy."""
    requests_mock.post(MOCK_URL, [{"text": "posted"}, {"text": "again"}])
    session = CachedSession(backend="memory", allowable_methods=("GET", "POST"))

    first = session.post(MOCK_URL)
    second = session.post(MOCK_URL)

    assert first.from_cache is False
    assert second.from_cache is True
    assert second.text == "posted"


def test_default_policy_does_not_cache_post_or_non_200(requests_mock):
    """Seam: config interaction between default methods/codes and cache state."""
    requests_mock.post(MOCK_URL, text="post-response")
    requests_mock.get(MOCK_URL_ALT, status_code=404, text="not found")
    session = CachedSession(backend="memory")

    session.post(MOCK_URL)
    session.get(MOCK_URL_ALT)

    assert len(session.cache.responses) == 0


def test_url_expiration_overrides_session_level_expiration(requests_mock):
    """Seam: config interaction between url rules and session expiration."""
    requests_mock.get(MOCK_URL, text="url-rule")
    session = CachedSession(
        backend="memory",
        expire_after=30,
        urls_expire_after={"example.test/resource": 180},
    )

    session.get(MOCK_URL)
    cached = session.get(MOCK_URL)

    assert cached.from_cache is True
    assert 150 <= cached.expires_delta <= 180


# --- Lifecycle Crossing: persistence ---


def test_sqlite_backend_persists_across_session_close_reopen(tmp_path, requests_mock):
    """Seam: lifecycle crossing between session close and backend persistence."""
    cache_path = str(tmp_path / "persist_cache")
    requests_mock.get(MOCK_URL, text="persistent-data")

    first = CachedSession(cache_path, backend="sqlite")
    first.get(MOCK_URL)
    first.close()

    second = CachedSession(cache_path, backend="sqlite")
    response = second.get(MOCK_URL)
    second.close()

    assert response.from_cache is True
    assert response.text == "persistent-data"
    assert Path(cache_path + ".sqlite").exists()


def test_filesystem_backend_persists_across_session_close_reopen(
    tmp_path, requests_mock
):
    """Seam: lifecycle crossing between filesystem session close and reopen."""
    cache_dir = str(tmp_path / "fs_persist")
    requests_mock.get(MOCK_URL, text="fs-data")

    first = CachedSession(cache_dir, backend="filesystem", serializer="json")
    first.get(MOCK_URL)
    first.close()

    second = CachedSession(cache_dir, backend="filesystem", serializer="json")
    response = second.get(MOCK_URL)
    second.close()

    assert response.from_cache is True
    assert response.text == "fs-data"


def test_sqlite_db_path_adds_sqlite_extension(tmp_path, requests_mock):
    """Seam: lifecycle - backend creates file with correct extension."""
    db_name = tmp_path / "named_cache"
    requests_mock.get(MOCK_URL, text="check-path")
    session = CachedSession(backend=SQLiteCache(db_name))
    session.get(MOCK_URL)

    assert Path(session.cache.db_path).suffix == ".sqlite"
    session.close()


# --- Patcher integration: install → requests → cache ---


def test_installed_patcher_makes_requests_use_cache(requests_mock):
    """Seam: state consistency between patcher and requests.Session."""
    requests_mock.get(MOCK_URL, [{"text": "first"}, {"text": "second"}])
    requests_cache.install_cache(backend="memory")

    first = requests.get(MOCK_URL)
    second = requests.get(MOCK_URL)

    assert first.from_cache is False
    assert second.from_cache is True


def test_enabled_context_installs_and_restores_on_exit(requests_mock):
    """Seam: lifecycle crossing between context manager and patcher state."""
    requests_mock.get(MOCK_URL, text="in-context")

    with requests_cache.enabled(backend="memory"):
        assert requests_cache.is_installed() is True
        response = requests.get(MOCK_URL)

    assert requests_cache.is_installed() is False
    assert response.text == "in-context"


def test_disabled_context_uninstalls_and_restores_on_exit(requests_mock):
    """Seam: lifecycle crossing between disabled() and installed state."""
    requests_mock.get(MOCK_URL, [{"text": "cached"}, {"text": "direct"}])
    requests_cache.install_cache(backend="memory")
    requests.get(MOCK_URL)

    with requests_cache.disabled():
        assert requests_cache.is_installed() is False
        bypassed = requests.get(MOCK_URL)

    assert requests_cache.is_installed() is True
    assert bypassed.text == "direct"


def test_top_level_clear_operates_on_installed_cache(requests_mock):
    """Seam: state consistency between top-level clear and installed cache."""
    requests_mock.get(MOCK_URL, text="clearable")
    requests_cache.install_cache(backend="memory")
    requests.get(MOCK_URL)

    requests_cache.clear()

    assert len(requests_cache.get_cache().responses) == 0


def test_top_level_delete_removes_url_from_installed_cache(requests_mock):
    """Seam: state consistency between top-level delete and installed cache."""
    requests_mock.get(MOCK_URL, text="deletable")
    requests_cache.install_cache(backend="memory")
    requests.get(MOCK_URL)

    requests_cache.delete(urls=[MOCK_URL])

    assert not requests_cache.get_cache().contains(url=MOCK_URL)


# --- Redirect aliases ---


def test_redirect_alias_returns_final_response_from_cache(requests_mock):
    """Seam: protocol handoff between redirect tracking and cache lookup."""
    requests_mock.get(
        "https://example.test/old",
        status_code=302,
        headers={"Location": MOCK_URL},
    )
    requests_mock.get(MOCK_URL, text="final-dest")
    session = CachedSession(backend="memory")

    first = session.get("https://example.test/old")
    second = session.get("https://example.test/old")

    assert first.text == "final-dest"
    assert second.from_cache is True
    assert second.url == MOCK_URL


# --- recreate_keys ---


def test_recreate_keys_keeps_responses_accessible(requests_mock):
    """Seam: protocol handoff between key recreation and cache lookup."""
    requests_mock.get(MOCK_URL, text="keyed")
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    session.cache.recreate_keys()

    assert session.get(MOCK_URL).from_cache is True


# --- Backend filter integration ---


def test_backend_filter_valid_yields_stored_responses(requests_mock):
    """Seam: state consistency between session write and filter read."""
    requests_mock.get(MOCK_URL, text="filterable")
    session = CachedSession(backend="memory")
    session.get(MOCK_URL)

    results = list(session.cache.filter(valid=True, expired=False))

    assert len(results) == 1


def test_backend_delete_expired_preserves_fresh_entries(requests_mock):
    """Seam: config interaction between expiration and delete(expired=True)."""
    requests_mock.get("https://example.test/short", text="short-lived")
    requests_mock.get("https://example.test/long", text="long-lived")
    session = CachedSession(backend="memory", expire_after=EXPIRE_IMMEDIATELY)
    session.get("https://example.test/short")
    session.settings.expire_after = NEVER_EXPIRE
    session.get("https://example.test/long")

    session.cache.delete(expired=True)

    assert not session.cache.contains(url="https://example.test/short")
    assert session.cache.contains(url="https://example.test/long")
