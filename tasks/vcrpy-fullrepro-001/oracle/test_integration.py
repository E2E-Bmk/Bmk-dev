"""Integration-layer oracle tests for vcrpy-fullrepro-001.

Each test verifies ≥2 different public API boundaries cooperating.
Composition dependency: even if all atomic tests pass, a test here can
still fail because the component seams don't align.
"""
import json
import os
from urllib.request import urlopen

import pytest
import requests as requests_lib

import vcr
from vcr.cassette import Cassette
from vcr.errors import CannotOverwriteExistingCassetteException
from vcr.persisters.filesystem import CassetteDecodeError, CassetteNotFoundError

from conftest import patched_dns


# ═══════════════════════════════════════════════════════════════
# Record → Replay Lifecycle  (CVI 1, 6)
#   seam: HTTP interception ↔ Cassette storage ↔ replay lookup
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_cassette_append_adds_interaction_and_updates_length",
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_urllib_record_then_replay_returns_same_body(tmp_path, httpbin):
    """CVI-1: Seam: state consistency — recorded urllib response body ↔ replayed body."""
    tape = str(tmp_path / "urllib-roundtrip.yaml")
    with vcr.use_cassette(tape) as cass:
        body_record = urlopen(httpbin.url).read()
        assert len(cass) >= 1
    with vcr.use_cassette(tape) as cass:
        body_replay = urlopen(httpbin.url).read()
        assert cass.play_count >= 1
    assert body_record == body_replay


@pytest.mark.depends_on(
    "test_cassette_append_adds_interaction_and_updates_length",
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_requests_lib_record_then_replay_preserves_status(tmp_path, httpbin):
    """CVI-1: Seam: state consistency — recorded HTTP status ↔ replayed status code."""
    tape = str(tmp_path / "requests-roundtrip.yaml")
    url = httpbin.url + "/"
    with vcr.use_cassette(tape):
        status_record = requests_lib.get(url).status_code
    with vcr.use_cassette(tape):
        status_replay = requests_lib.get(url).status_code
    assert status_record == status_replay


@pytest.mark.depends_on(
    "test_request_uri_preserves_original_value",
    "test_cassette_append_adds_interaction_and_updates_length",
)
def test_redirect_chain_records_all_request_response_pairs(tmp_path, httpbin):
    """Seam: lifecycle crossing — redirect chain ↔ multiple cassette interactions."""
    tape = str(tmp_path / "redirect-chain.yaml")
    with vcr.use_cassette(tape) as cass:
        urlopen(httpbin.url + "/redirect/2")
    assert len(cass) >= 3
    assert cass.requests[0].uri.endswith("/redirect/2")


# ═══════════════════════════════════════════════════════════════
# VCR Config Propagation  (CVI 8)
#   seam: VCR defaults ↔ cassette file path resolution ↔ filesystem
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on("test_vcr_default_match_on_includes_standard_components")
def test_cassette_library_dir_resolves_relative_path(tmp_path, httpbin):
    """CVI-8: Seam: config interaction — VCR cassette_library_dir ↔ filesystem path resolution."""
    lib_dir = str(tmp_path / "tapes")
    recorder = vcr.VCR(cassette_library_dir=lib_dir)
    with recorder.use_cassette("resolve-test.yaml"):
        urlopen(httpbin.url)
    assert os.path.exists(os.path.join(lib_dir, "resolve-test.yaml"))


@pytest.mark.depends_on("test_vcr_default_match_on_includes_standard_components")
def test_use_cassette_overrides_vcr_library_dir(tmp_path, httpbin):
    """CVI-8: Seam: config interaction — per-cassette library_dir ↔ override of VCR default."""
    default_dir = str(tmp_path / "default")
    override_dir = str(tmp_path / "override")
    recorder = vcr.VCR(cassette_library_dir=default_dir)
    with recorder.use_cassette("override-test.yaml", cassette_library_dir=override_dir):
        urlopen(httpbin.url)
    assert os.path.exists(os.path.join(override_dir, "override-test.yaml"))
    assert not os.path.exists(os.path.join(default_dir, "override-test.yaml"))


@pytest.mark.depends_on(
    "test_method_matcher_compares_http_methods",
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_vcr_match_on_propagates_to_replay(tmp_path, httpbin):
    """Seam: config interaction — VCR match_on setting ↔ replay matching behavior."""
    recorder = vcr.VCR(match_on=["method"])
    tape = str(tmp_path / "match-on-prop.yaml")
    with recorder.use_cassette(tape):
        urlopen(httpbin.url)
    with recorder.use_cassette(tape) as cass:
        urlopen(httpbin.url)
    assert len(cass) == 1
    assert cass.play_count == 1


# ═══════════════════════════════════════════════════════════════
# Record Mode Agreement  (CVI 2)
#   seam: mode decision ↔ cassette existence ↔ match result ↔ save
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_mode_constants_are_importable_attributes",
    "test_error_types_are_distinct_exception_classes",
)
def test_once_mode_records_then_replays_and_rejects_new(tmp_path, httpbin):
    """CVI-2: Seam: lifecycle crossing — ONCE mode record ↔ replay ↔ reject new interaction."""
    tape = str(tmp_path / "once-mode.yaml")
    with vcr.use_cassette(tape, record_mode=vcr.mode.ONCE):
        urlopen(httpbin.url).read()
    with vcr.use_cassette(tape, record_mode=vcr.mode.ONCE):
        urlopen(httpbin.url).read()
        with pytest.raises(CannotOverwriteExistingCassetteException):
            urlopen(httpbin.url + "/get").read()


@pytest.mark.depends_on("test_error_types_are_distinct_exception_classes")
def test_none_mode_rejects_all_without_cassette(tmp_path, httpbin):
    """CVI-2: Seam: error propagation — NONE mode empty cassette ↔ CannotOverwriteExistingCassetteException."""
    tape = str(tmp_path / "none-empty.yaml")
    with vcr.use_cassette(tape, record_mode=vcr.mode.NONE), \
         pytest.raises(CannotOverwriteExistingCassetteException):
        urlopen(httpbin.url).read()


@pytest.mark.depends_on(
    "test_cassette_play_response_returns_matching_and_increments_count",
    "test_error_types_are_distinct_exception_classes",
)
def test_none_mode_replays_existing_and_rejects_new(tmp_path, httpbin):
    """CVI-2: Seam: lifecycle crossing — NONE mode existing cassette ↔ replay and reject new."""
    tape = str(tmp_path / "none-existing.yaml")
    with vcr.use_cassette(tape, record_mode=vcr.mode.ALL):
        urlopen(httpbin.url).read()
    with vcr.use_cassette(tape, record_mode=vcr.mode.NONE) as cass:
        urlopen(httpbin.url).read()
        assert cass.play_count == 1
        with pytest.raises(CannotOverwriteExistingCassetteException):
            urlopen(httpbin.url + "/get").read()


@pytest.mark.depends_on(
    "test_cassette_play_response_returns_matching_and_increments_count",
    "test_cassette_append_adds_interaction_and_updates_length",
)
def test_new_episodes_replays_existing_records_new(tmp_path, httpbin):
    """CVI-2: Seam: lifecycle crossing — NEW_EPISODES ↔ replay existing and record new interaction."""
    tape = str(tmp_path / "new-episodes.yaml")
    with vcr.use_cassette(tape, record_mode=vcr.mode.NEW_EPISODES):
        urlopen(httpbin.url).read()
    with vcr.use_cassette(tape, record_mode=vcr.mode.NEW_EPISODES) as cass:
        urlopen(httpbin.url).read()
        urlopen(httpbin.url + "/get").read()
        assert cass.play_count == 1
        assert len(cass) == 2


@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_all_mode_records_all_never_replays(tmp_path, httpbin):
    """CVI-2: Seam: state consistency — ALL mode ↔ always record and never replay."""
    tape = str(tmp_path / "all-mode.yaml")
    with vcr.use_cassette(tape, record_mode=vcr.mode.ALL):
        urlopen(httpbin.url).read()
    with vcr.use_cassette(tape, record_mode=vcr.mode.ALL) as cass:
        urlopen(httpbin.url).read()
        assert cass.play_count == 0


# ═══════════════════════════════════════════════════════════════
# Serializer Round-Trip  (CVI 3)
#   seam: VCR lifecycle ↔ custom serializer ↔ cassette save/load
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on("test_serialize_produces_version_1_interaction_list")
def test_custom_serializer_invoked_during_save_and_load(tmp_path):
    """CVI-3: Seam: protocol handoff — custom serializer ↔ cassette save/load lifecycle."""
    class TrackingSerializer:
        def __init__(self):
            self.did_deserialize = False
            self.did_serialize = False
            self.raw_data = None

        def deserialize(self, raw):
            self.did_deserialize = True
            self.raw_data = raw
            return {"interactions": []}

        def serialize(self, data):
            self.did_serialize = True
            return ""

    tracker = TrackingSerializer()
    recorder = vcr.VCR()
    recorder.register_serializer("tracker", tracker)
    (tmp_path / "track.tracker").write_text("placeholder-content")
    with recorder.use_cassette(str(tmp_path / "track.tracker"), serializer="tracker"):
        assert tracker.did_deserialize is True
        assert tracker.raw_data == "placeholder-content"
    assert tracker.did_serialize is True


@pytest.mark.depends_on(
    "test_serialize_produces_version_1_interaction_list",
    "test_deserialize_reconstructs_request_objects_and_responses",
)
def test_cassette_load_restores_interactions_from_file(tmp_path, httpbin):
    """CVI-3: Seam: state consistency — cassette file on disk ↔ Cassette.load interactions."""
    tape = str(tmp_path / "loadable.yaml")
    with vcr.use_cassette(tape):
        urlopen(httpbin.url).read()
    loaded = Cassette.load(path=tape)
    assert len(loaded) >= 1
    assert loaded.requests[0].uri == httpbin.url


@pytest.mark.depends_on("test_serialize_produces_version_1_interaction_list")
def test_json_serializer_produces_loadable_cassette(tmp_path, httpbin):
    """CVI-3: Seam: state consistency — JSON serializer ↔ record/replay body round-trip."""
    tape = str(tmp_path / "roundtrip.json")
    with vcr.use_cassette(tape, serializer="json"):
        body_record = urlopen(httpbin.url).read()
    with vcr.use_cassette(tape, serializer="json"):
        body_replay = urlopen(httpbin.url).read()
    assert body_record == body_replay


# ═══════════════════════════════════════════════════════════════
# Custom Persister  (CVI 3)
#   seam: VCR lifecycle ↔ persister error handling ↔ cassette state
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_filesystem_persister_load_missing_raises_cassette_not_found_error",
    "test_filesystem_persister_load_malformed_raises_cassette_decode_error",
)
def test_custom_persister_swallows_expected_errors_propagates_others():
    """CVI-3: Seam: error propagation — persister load errors ↔ empty cassette vs RuntimeError."""
    class ErrorPersister:
        @staticmethod
        def load_cassette(path, serializer):
            if "absent" in path:
                raise CassetteNotFoundError()
            if "garbled" in path:
                raise CassetteDecodeError()
            raise RuntimeError("persister-bug")

        @staticmethod
        def save_cassette(path, data, serializer):
            pass

    recorder = vcr.VCR()
    recorder.register_persister(ErrorPersister)
    with recorder.use_cassette("absent-tape") as cass:
        assert len(cass) == 0
    with recorder.use_cassette("garbled-tape") as cass:
        assert len(cass) == 0
    with pytest.raises(RuntimeError):
        with recorder.use_cassette("fatal-tape"):
            pass


# ═══════════════════════════════════════════════════════════════
# Filter Effects  (CVI 4)
#   seam: filter config ↔ request mutation ↔ cassette storage
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_request_body_returns_bytes_or_none",
    "test_cassette_append_adds_interaction_and_updates_length",
)
def test_filter_post_data_removes_from_stored_request(tmp_path, httpbin):
    """CVI-4: Seam: config interaction — filter_post_data_parameters ↔ stored request body."""
    tape = str(tmp_path / "filtered-post.yaml")
    url = httpbin.url + "/post"
    with vcr.use_cassette(tape, filter_post_data_parameters=["secret"]) as cass:
        requests_lib.post(url, data={"secret": "s3cret", "visible": "open"})
    assert b"secret=s3cret" not in cass.requests[0].body


@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_before_record_request_callback_can_skip_interaction(tmp_path, httpbin):
    """CVI-4: Seam: lifecycle crossing — before_record_request callback ↔ cassette contents."""
    def skip_get(request):
        if "/get" in request.path:
            return None
        return request

    tape = str(tmp_path / "skip-callback.yaml")
    with vcr.use_cassette(tape, before_record_request=skip_get) as cass:
        urlopen(httpbin.url + "/get")
        urlopen(httpbin.url + "/")
    paths = [r.path for r in cass.requests]
    assert "/get" not in paths
    assert len(cass) >= 1


# ═══════════════════════════════════════════════════════════════
# Context / Decorator Equivalence  (CVI 5)
#   seam: decorator mechanism ↔ context manager ↔ cassette lifecycle
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_cassette_append_adds_interaction_and_updates_length",
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_decorator_and_context_manager_produce_equivalent_cassettes(tmp_path, httpbin):
    """CVI-5: Seam: state consistency — decorator ↔ context manager cassette equivalence."""
    ctx_tape = str(tmp_path / "ctx.yaml")
    dec_tape = str(tmp_path / "dec.yaml")

    with vcr.use_cassette(ctx_tape) as ctx_cass:
        urlopen(httpbin.url).read()
    ctx_len = len(ctx_cass)

    @vcr.use_cassette(dec_tape)
    def decorated():
        urlopen(httpbin.url).read()

    decorated()
    dec_loaded = Cassette.load(path=dec_tape)
    assert len(dec_loaded) == ctx_len


# ═══════════════════════════════════════════════════════════════
# Patch Lifecycle  (CVI 6)
#   seam: HTTP patch activation ↔ cassette context exit ↔ restore
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_unpatching_after_context_exit_restores_http(tmp_path, httpbin):
    """CVI-6: Seam: lifecycle crossing — cassette context exit ↔ HTTP patch restore."""
    tape = str(tmp_path / "unpatch.yaml")
    with vcr.use_cassette(tape) as cass:
        urlopen(httpbin.url).read()
    urlopen(httpbin.url).read()
    assert cass.play_count == 0


@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_custom_patches_active_inside_restored_outside(tmp_path):
    """CVI-6: Seam: lifecycle crossing — custom_patches active inside context ↔ restored outside."""
    class Holder:
        flag = "before"

    holder = Holder()
    recorder = vcr.VCR(custom_patches=((holder, "flag", "during"),))
    with recorder.use_cassette(str(tmp_path / "custom-patch.yaml")):
        assert holder.flag == "during"
    assert holder.flag == "before"


# ═══════════════════════════════════════════════════════════════
# Playback Bookkeeping  (CVI 7)
#   seam: play_count/all_played ↔ actual replay ↔ saved cassette
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_cassette_append_adds_interaction_and_updates_length",
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_drop_unused_requests_removes_unplayed_interactions(tmp_path, httpbin):
    """CVI-7: Seam: state consistency — drop_unused_requests ↔ pruned saved cassette."""
    recorder = vcr.VCR(drop_unused_requests=True)
    tape = str(tmp_path / "drop-unused.yaml")
    with recorder.use_cassette(tape):
        urlopen(httpbin.url)
        urlopen(httpbin.url + "/get")
    assert len(Cassette.load(path=tape)) == 2
    with recorder.use_cassette(tape):
        urlopen(httpbin.url)
    assert len(Cassette.load(path=tape)) == 1


@pytest.mark.depends_on(
    "test_cassette_play_response_returns_matching_and_increments_count",
    "test_cassette_all_played_reflects_exhaustion",
)
def test_play_count_tracks_replayed_interactions(tmp_path, httpbin):
    """CVI-7: Seam: state consistency — play_count ↔ replayed interactions and all_played flag."""
    tape = str(tmp_path / "play-count.yaml")
    with vcr.use_cassette(tape):
        urlopen(httpbin.url)
        urlopen(httpbin.url + "/get")
    with vcr.use_cassette(tape) as cass:
        urlopen(httpbin.url)
        urlopen(httpbin.url + "/get")
        assert cass.play_count == 2
        assert cass.all_played is True


# ═══════════════════════════════════════════════════════════════
# Exception Handling
#   seam: record_on_exception ↔ cassette save decision ↔ file system
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_record_on_exception_false_skips_save_on_error(tmp_path, httpbin):
    """Seam: lifecycle crossing — record_on_exception=False ↔ no cassette file on error."""
    recorder = vcr.VCR(record_on_exception=False)
    tape = tmp_path / "no-save-on-error.yaml"
    with pytest.raises(RuntimeError):
        with recorder.use_cassette(str(tape)):
            urlopen(httpbin.url).read()
            raise RuntimeError("intentional")
    assert not tape.exists()


@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_default_saves_cassette_even_on_exception(tmp_path, httpbin):
    """Seam: lifecycle crossing — default record_on_exception ↔ cassette saved despite error."""
    tape = tmp_path / "save-on-error.yaml"
    with pytest.raises(RuntimeError):
        with vcr.use_cassette(str(tape)):
            urlopen(httpbin.url).read()
            raise RuntimeError("intentional")
    assert tape.exists()
    assert len(Cassette.load(path=str(tape))) >= 1


# ═══════════════════════════════════════════════════════════════
# Ignore Hosts
#   seam: ignore config ↔ HTTP interception ↔ cassette recording
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_ignore_localhost_excludes_local_requests(tmp_path, httpbin):
    """Seam: config interaction — ignore_localhost ↔ excluded localhost recording."""
    tape = str(tmp_path / "ignore-local.yaml")
    with vcr.use_cassette(tape, ignore_localhost=True) as cass:
        urlopen(f"http://localhost:{httpbin.port}/")
        assert len(cass) == 0


@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_ignore_hosts_list_excludes_named_host(tmp_path, httpbin):
    """Seam: config interaction — ignore_hosts list ↔ selective host exclusion from cassette."""
    with patched_dns({"custom-api.test": "127.0.0.1"}):
        tape = str(tmp_path / "ignore-named.yaml")
        with vcr.use_cassette(
            tape, ignore_hosts=["custom-api.test"]
        ) as cass:
            urlopen(f"http://custom-api.test:{httpbin.port}/")
            assert len(cass) == 0
            urlopen(f"http://localhost:{httpbin.port}/")
            assert len(cass) == 1


# ═══════════════════════════════════════════════════════════════
# Mode Constants Interchangeability  (CVI 9)
#   seam: mode constant ↔ string equivalent ↔ cassette behaviour
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on("test_mode_constants_are_importable_attributes")
def test_mode_string_and_constant_produce_same_behavior(tmp_path, httpbin):
    """CVI-9: Seam: state consistency — mode constant ↔ string equivalent record behavior."""
    tape_const = str(tmp_path / "mode-const.yaml")
    tape_str = str(tmp_path / "mode-str.yaml")
    with vcr.use_cassette(tape_const, record_mode=vcr.mode.ALL) as c1:
        urlopen(httpbin.url).read()
    with vcr.use_cassette(tape_str, record_mode="all") as c2:
        urlopen(httpbin.url).read()
    assert c1.play_count == c2.play_count == 0
    assert len(c1) >= 1
    assert len(c2) >= 1


# ═══════════════════════════════════════════════════════════════
# Filesystem Directory Creation  (CVI 3)
#   seam: VCR save → FilesystemPersister mkdir → write
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on("test_filesystem_persister_save_creates_parent_directories")
def test_nonexistent_directory_created_on_cassette_save(tmp_path, httpbin):
    """CVI-3: Seam: lifecycle crossing — cassette save ↔ parent directory auto-creation."""
    nested = tmp_path / "deep" / "nested"
    tape = str(nested / "auto-dir.yaml")
    assert not nested.exists()
    with vcr.use_cassette(tape):
        urlopen(httpbin.url).read()
    assert os.path.exists(tape)


# ═══════════════════════════════════════════════════════════════
# Custom Matcher  (CVI 1)
#   seam: register_matcher → match_on config → replay decision
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_registered_custom_matcher_controls_replay(tmp_path, httpbin):
    """Seam: config interaction — register_matcher ↔ match_on replay decision."""
    def always_match(r1, r2):
        return True

    recorder = vcr.VCR()
    recorder.register_matcher("always", always_match)
    tape = str(tmp_path / "custom-matcher.yaml")
    with recorder.use_cassette(tape, match_on=["always"]):
        urlopen(httpbin.url)
    with recorder.use_cassette(tape, match_on=["always"]) as cass:
        urlopen(httpbin.url + "/get")
    assert cass.play_count >= 1


@pytest.mark.depends_on(
    "test_cassette_play_response_returns_matching_and_increments_count",
)
def test_false_custom_matcher_prevents_replay(tmp_path, httpbin):
    """Seam: config interaction — never-match matcher ↔ no replay match on second request."""
    def never_match(r1, r2):
        return False

    recorder = vcr.VCR()
    recorder.register_matcher("never", never_match)
    tape = str(tmp_path / "false-matcher.yaml")
    with recorder.use_cassette(tape, match_on=["never"]):
        urlopen(httpbin.url)
        urlopen(httpbin.url)
    assert len(Cassette.load(path=tape)) == 2


# ═══════════════════════════════════════════════════════════════
# Multiple Response Headers  (CVI 1)
#   seam: HTTP response capture ↔ cassette storage ↔ replay
# ═══════════════════════════════════════════════════════════════

@pytest.mark.depends_on("test_cassette_append_adds_interaction_and_updates_length")
def test_multiple_response_header_values_preserved(tmp_path, httpbin):
    """Seam: state consistency — HTTP multi-value headers ↔ cassette storage and replay."""
    tape = str(tmp_path / "multi-header.yaml")
    url = httpbin.url + "/response-headers?foo=bar&foo=baz"
    with vcr.use_cassette(tape) as cass:
        urlopen(url)
    assert len(cass) == 1
    assert cass.responses[0]["headers"]["foo"] == ["bar", "baz"]
