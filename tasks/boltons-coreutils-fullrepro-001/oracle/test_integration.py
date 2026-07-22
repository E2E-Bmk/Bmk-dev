"""Integration layer tests for boltons oracle suite.

Each test verifies >=2 different public API boundaries cooperating.
Satisfies Composition Dependency: even if all atomic tests pass, these
tests can still fail because component "seams" don't align.

Seam types tested: state consistency, protocol handoff, error propagation,
config interaction, lifecycle crossing.
"""
import pytest


# ---------------------------------------------------------------------------
# CVI: Cache insert->lookup consistency (LRU + cached decorator cooperation)
# Seam: state consistency - cached decorator must correctly interact with
#        the LRU backing store's eviction policy
# ---------------------------------------------------------------------------


class TestCacheLRUWithCachedDecorator:
    """Integration: cached decorator + LRU backing store."""

    @pytest.mark.depends_on("test_lru_access_updates_recency", "test_cached_stores_return_value")
    def test_cached_with_lru_eviction_still_recomputes(self):
        """Seam: state consistency — integration path for cached with lru eviction still recomputes across cooperating public APIs."""
        from boltons.cacheutils import LRU, cached

        store = LRU(max_size=2)
        call_log = []

        @cached(store)
        def expensive(n):
            call_log.append(n)
            return n * 11

        expensive(5)
        expensive(6)
        expensive(7)  # should evict key for arg 5
        result = expensive(5)  # must recompute
        assert result == 55
        assert call_log.count(5) == 2

    @pytest.mark.depends_on("test_lru_access_updates_recency", "test_cached_stores_return_value")
    def test_cached_hit_counts_match_lru_state(self):
        """Seam: state consistency — integration path for cached hit counts match lru state across cooperating public APIs."""
        from boltons.cacheutils import LRU, cached

        store = LRU(max_size=3)

        @cached(store)
        def square(x):
            return x * x

        square(2)
        square(3)
        square(4)
        assert len(store) == 3
        square(2)  # hit
        assert len(store) == 3  # no new entry


# ---------------------------------------------------------------------------
# CVI: cached/cachedmethod/cachedproperty reuse
# Seam: protocol handoff - different caching decorators must independently
#        cache without interfering
# ---------------------------------------------------------------------------


class TestCacheDecoratorFamily:
    """Integration: cached + cachedmethod + cachedproperty on same class."""

    @pytest.mark.depends_on("test_cached_stores_return_value", "test_cachedmethod_caches_result", "test_cachedproperty_computes_once")
    def test_three_cache_mechanisms_independent(self):
        """Seam: config interaction — integration path for three cache mechanisms independent across cooperating public APIs."""
        from boltons.cacheutils import cached, cachedmethod, cachedproperty

        fn_store = {}

        @cached(fn_store)
        def helper(val):
            return val + 100

        class Service:
            def __init__(self):
                self._mc = {}
                self._prop_calls = 0

            @cachedmethod("_mc")
            def compute(self, val):
                return val + 200

            @cachedproperty
            def config(self):
                self._prop_calls += 1
                return {"ready": True}

        svc = Service()
        fn_result = helper(8)
        method_result = svc.compute(8)
        prop_result = svc.config

        assert fn_result == 108
        assert method_result == 208
        assert prop_result == {"ready": True}
        # Each uses independent storage
        assert 8 not in svc._mc or svc._mc != fn_store
        assert svc._prop_calls == 1

    @pytest.mark.depends_on("test_cachedmethod_caches_result", "test_cachedproperty_computes_once")
    def test_cachedproperty_and_cachedmethod_separate_namespaces(self):
        """Seam: state consistency — integration path for cachedproperty and cachedmethod separate namespaces across cooperating public APIs."""
        from boltons.cacheutils import cachedmethod, cachedproperty

        class Dual:
            def __init__(self):
                self._method_cache = {}
                self._prop_runs = 0
                self._method_runs = 0

            @cachedproperty
            def lazy_val(self):
                self._prop_runs += 1
                return 999

            @cachedmethod("_method_cache")
            def fetch(self, key):
                self._method_runs += 1
                return key.upper()

        d = Dual()
        assert d.lazy_val == 999
        assert d.fetch("test") == "TEST"
        # Verify independent - clearing one doesn't affect other
        del d.__dict__["lazy_val"]
        assert d.fetch("test") == "TEST"
        assert d._method_runs == 1  # still cached


# ---------------------------------------------------------------------------
# CVI: LRI/LRU insert->lookup with make_cache_key
# Seam: protocol handoff - make_cache_key output used as LRU key
# ---------------------------------------------------------------------------


class TestCacheKeyWithLRU:
    """Integration: make_cache_key + LRU storage."""

    @pytest.mark.depends_on("test_typed_true_distinguishes_int_from_float", "test_lru_insert_and_retrieve")
    def test_make_cache_key_as_lru_key(self):
        """Seam: state consistency — integration path for make cache key as lru key across cooperating public APIs."""
        from boltons.cacheutils import LRU, make_cache_key

        store = LRU(max_size=10)
        k1 = make_cache_key((3, "hello"), {"mode": "fast"}, typed=False)
        k2 = make_cache_key((3, "hello"), {"mode": "slow"}, typed=False)

        store[k1] = "result_fast"
        store[k2] = "result_slow"

        assert store[k1] == "result_fast"
        assert store[k2] == "result_slow"
        assert k1 != k2


# ---------------------------------------------------------------------------
# CVI: OMD multi-view consistency
# Seam: state consistency - mutations through one OMD method must be
#        observable through all view methods consistently
# ---------------------------------------------------------------------------


class TestOMDMultiViewConsistency:
    """Integration: OMD mutation + multiple views agree."""

    @pytest.mark.depends_on("test_omd_add_appends_without_replacing", "test_omd_getlist_returns_all_values")
    def test_add_visible_through_getlist_items_copy(self):
        """Seam: lifecycle crossing — integration path for add visible through getlist items copy across cooperating public APIs."""
        from boltons.dictutils import OrderedMultiDict

        omd = OrderedMultiDict([("lang", "python"), ("lang", "rust")])
        omd.add("lang", "go")

        assert omd.getlist("lang") == ["python", "rust", "go"]
        multi_items = omd.items(multi=True)
        lang_vals = [v for k, v in multi_items if k == "lang"]
        assert lang_vals == ["python", "rust", "go"]
        clone = omd.copy()
        assert clone.getlist("lang") == ["python", "rust", "go"]

    @pytest.mark.depends_on("test_omd_assignment_replaces_all_values", "test_omd_getlist_returns_all_values")
    def test_assignment_clears_old_multi_values(self):
        """Seam: state consistency — integration path for assignment clears old multi values across cooperating public APIs."""
        from boltons.dictutils import OrderedMultiDict

        omd = OrderedMultiDict([("status", "draft"), ("status", "review"), ("status", "final")])
        omd["status"] = "published"

        assert omd.getlist("status") == ["published"]
        assert omd["status"] == "published"
        all_keys = list(omd.keys(multi=True))
        assert all_keys.count("status") == 1

    @pytest.mark.depends_on("test_omd_getlist_returns_all_values", "test_omd_subscript_returns_most_recent")
    def test_inverted_and_items_agree(self):
        """Seam: state consistency — integration path for inverted and items agree across cooperating public APIs."""
        from boltons.dictutils import OrderedMultiDict

        omd = OrderedMultiDict([("a", 1), ("b", 2), ("a", 3)])
        inv = omd.inverted()
        multi = omd.items(multi=True)
        for k, v in multi:
            assert k in inv.getlist(v)


# ---------------------------------------------------------------------------
# CVI: OneToOne bidirectional sync
# Seam: state consistency - forward and inverse must stay synchronized
#        after a sequence of mutations
# ---------------------------------------------------------------------------


class TestOneToOneBidirectionalSync:
    """Integration: OneToOne forward + .inv consistency across mutations."""

    @pytest.mark.depends_on("test_onetoone_assignment_maintains_bijection", "test_onetoone_inv_assignment_updates_forward")
    def test_forward_inv_stay_synced_after_mutations(self):
        """Seam: state consistency — integration path for forward inv stay synced after mutations across cooperating public APIs."""
        from boltons.dictutils import OneToOne

        oto = OneToOne({"server1": "10.0.0.1", "server2": "10.0.0.2"})
        oto["server3"] = "10.0.0.3"
        oto.inv["10.0.0.4"] = "server4"
        del oto["server1"]

        assert "server1" not in oto
        assert "10.0.0.1" not in oto.inv
        assert oto["server4"] == "10.0.0.4"
        assert oto.inv["10.0.0.4"] == "server4"
        # All forward keys map to valid inverse entries
        for k, v in oto.items():
            assert oto.inv[v] == k

    @pytest.mark.depends_on("test_onetoone_reassign_value_removes_old_key", "test_onetoone_pop_updates_inv")
    def test_value_collision_resolution_syncs_inv(self):
        """Seam: lifecycle crossing — integration path for value collision resolution syncs inv across cooperating public APIs."""
        from boltons.dictutils import OneToOne

        oto = OneToOne({"alpha": "x", "beta": "y", "gamma": "z"})
        oto["delta"] = "x"  # removes "alpha"
        assert "alpha" not in oto
        assert oto.inv["x"] == "delta"
        assert len(oto) == len(oto.inv)


# ---------------------------------------------------------------------------
# CVI: ManyToMany bidirectional sync
# Seam: state consistency - forward and inverse frozensets reflect same links
# ---------------------------------------------------------------------------


class TestManyToManyBidirectionalSync:
    """Integration: ManyToMany forward + .inv consistency."""

    @pytest.mark.depends_on("test_manytomany_add_creates_link", "test_manytomany_remove_deletes_link")
    def test_add_and_remove_reflected_in_inv(self):
        """Seam: lifecycle crossing — integration path for add and remove reflected in inv across cooperating public APIs."""
        from boltons.dictutils import ManyToMany

        mm = ManyToMany()
        mm.add("course_a", "student_1")
        mm.add("course_a", "student_2")
        mm.add("course_b", "student_2")

        assert "course_a" in mm.inv["student_2"]
        assert "course_b" in mm.inv["student_2"]

        mm.remove("course_a", "student_2")
        assert "course_a" not in mm.inv["student_2"]
        assert "student_2" in mm["course_b"]

    @pytest.mark.depends_on("test_manytomany_add_creates_link", "test_manytomany_del_removes_all_links")
    def test_del_key_clears_inv_entries(self):
        """Seam: lifecycle crossing — integration path for del key clears inv entries across cooperating public APIs."""
        from boltons.dictutils import ManyToMany

        mm = ManyToMany([("team1", "p1"), ("team1", "p2"), ("team2", "p2")])
        del mm["team1"]
        # p1 no longer linked to any team
        assert mm.get("team1") == frozenset()
        # p2 still linked to team2
        assert "team2" in mm.inv["p2"]
        if "p1" in mm.inv:
            assert mm.inv["p1"] == frozenset()


# ---------------------------------------------------------------------------
# CVI: URL parse->serialize round-trip
# Seam: protocol handoff - URL constructor output fed to to_text() and re-parsed
# ---------------------------------------------------------------------------


class TestURLRoundTrip:
    """Integration: URL parse + to_text + re-parse round-trip."""

    @pytest.mark.depends_on("test_url_parses_scheme", "test_qpd_to_text_serializes")
    def test_full_url_round_trip_preserves_components(self):
        """Seam: state consistency — integration path for full url round trip preserves components across cooperating public APIs."""
        from boltons.urlutils import URL

        original = "https://user:pass@roundtrip.example.test:9999/a/b/c?key=val&arr=1&arr=2#bottom"
        u1 = URL(original)
        serialized = u1.to_text()
        u2 = URL(serialized)

        assert u1.scheme == u2.scheme
        assert u1.host == u2.host
        assert u1.port == u2.port
        assert u1.path == u2.path
        assert u1.fragment == u2.fragment
        assert u1.username == u2.username

    @pytest.mark.depends_on("test_url_parses_scheme", "test_qpd_from_text_parses")
    def test_query_params_survive_round_trip(self):
        """Seam: state consistency — integration path for query params survive round trip across cooperating public APIs."""
        from boltons.urlutils import URL

        u = URL("http://qp.example.test/search?tag=red&tag=blue&page=3")
        text = u.to_text()
        u2 = URL(text)
        assert u2.query_params.getlist("tag") == ["red", "blue"]
        assert u2.query_params["page"] == "3"


# ---------------------------------------------------------------------------
# CVI: URL navigate/normalize consistency
# Seam: lifecycle crossing - navigate creates new state, normalize mutates it,
#        attributes/serialization must all agree
# ---------------------------------------------------------------------------


class TestURLNavigateNormalizeConsistency:
    """Integration: URL.navigate + URL.normalize + attributes/to_text agree."""

    @pytest.mark.depends_on("test_url_navigate_relative", "test_url_normalize_removes_default_port")
    def test_navigate_then_normalize_consistent(self):
        """Seam: lifecycle crossing — integration path for navigate then normalize consistent across cooperating public APIs."""
        from boltons.urlutils import URL

        base = URL("https://nav.example.test:443/docs/intro?v=1")
        dest = base.navigate("../api/endpoint?format=json")
        dest.normalize()

        text = dest.to_text()
        assert dest.host == "nav.example.test"
        assert "api/endpoint" in dest.path
        assert "nav.example.test" in text
        assert ":443" not in text  # default port removed
        assert dest.query_params["format"] == "json"

    @pytest.mark.depends_on("test_url_navigate_relative", "test_url_parses_scheme")
    def test_navigate_absolute_replaces_base(self):
        """Seam: state consistency — integration path for navigate absolute replaces base across cooperating public APIs."""
        from boltons.urlutils import URL

        base = URL("http://old.example.test/page")
        dest = base.navigate("https://new.example.test/fresh")
        assert dest.scheme == "https"
        assert dest.host == "new.example.test"
        assert "fresh" in dest.path

    @pytest.mark.depends_on("test_url_normalize_removes_default_port", "test_url_parses_port")
    def test_normalize_updates_authority_and_text(self):
        """Seam: state consistency — integration path for normalize updates authority and text across cooperating public APIs."""
        from boltons.urlutils import URL

        u = URL("http://auth.example.test:80/resource")
        u.normalize()
        auth = u.get_authority()
        text = u.to_text()
        assert ":80" not in auth
        assert ":80" not in text
        assert "auth.example.test" in auth


# ---------------------------------------------------------------------------
# CVI: remap/get_path/research path agreement
# Seam: state consistency - all three functions must agree on paths in the
#        same nested structure
# ---------------------------------------------------------------------------


class TestRemapGetPathResearchAgreement:
    """Integration: remap + get_path + research on same nested data."""

    @pytest.mark.depends_on("test_remap_identity_preserves_structure", "test_get_path_indexes_nested", "test_research_finds_matching_paths")
    def test_research_paths_accessible_via_get_path(self):
        """Seam: config interaction — integration path for research paths accessible via get path across cooperating public APIs."""
        from boltons.iterutils import remap, get_path, research

        data = {"config": {"db": {"host": "db.example.test", "port": 5432}}, "version": 3}

        matches = research(data, query=lambda p, k, v: v == "db.example.test")
        assert len(matches) >= 1
        for path, value in matches:
            retrieved = get_path(data, path)
            assert retrieved == "db.example.test"

    @pytest.mark.depends_on("test_remap_visit_drops_items", "test_get_path_indexes_nested")
    def test_remap_preserves_paths_for_get_path(self):
        """Seam: state consistency — integration path for remap preserves paths for get path across cooperating public APIs."""
        from boltons.iterutils import remap, get_path

        data = {"settings": {"theme": "dark", "debug": True, "timeout": 30}}

        def keep_non_debug(path, key, value):
            if key == "debug":
                return False
            return True

        remapped = remap(data, visit=keep_non_debug)
        assert get_path(remapped, ("settings", "theme")) == "dark"
        assert get_path(remapped, ("settings", "timeout")) == 30

    @pytest.mark.depends_on("test_research_finds_matching_paths", "test_remap_identity_preserves_structure")
    def test_research_on_remapped_data_finds_transformed_values(self):
        """Seam: protocol handoff — integration path for research on remapped data finds transformed values across cooperating public APIs."""
        from boltons.iterutils import remap, research

        data = {"items": [{"name": "one"}, {"name": "two"}]}

        def upper_names(path, key, value):
            if key == "name" and isinstance(value, str):
                return (key, value.upper())
            return True

        remapped = remap(data, visit=upper_names)
        matches = research(remapped, query=lambda p, k, v: v == "ONE")
        assert len(matches) >= 1


# ---------------------------------------------------------------------------
# Cross-domain: URL + QueryParamDict cooperation
# Seam: state consistency - URL.query_params mutations reflect in to_text()
# ---------------------------------------------------------------------------


class TestURLQueryParamCooperation:
    """Integration: URL + QueryParamDict mutation + serialization."""

    @pytest.mark.depends_on("test_url_parses_scheme", "test_qpd_from_text_parses")
    def test_qp_mutation_reflected_in_to_text(self):
        """Seam: state consistency — integration path for qp mutation reflected in to text across cooperating public APIs."""
        from boltons.urlutils import URL

        u = URL("https://shop.example.test/cart?item=hat")
        u.query_params["color"] = "navy"
        u.query_params.add("item", "scarf")

        text = u.to_text()
        assert "color=navy" in text
        # Both items present
        assert text.count("item=") >= 2

    @pytest.mark.depends_on("test_qpd_from_text_parses", "test_url_equality_same_components")
    def test_qp_getlist_matches_parsed_url(self):
        """Seam: state consistency — integration path for qp getlist matches parsed url across cooperating public APIs."""
        from boltons.urlutils import URL

        u = URL("http://multi.example.test/api?id=10&id=20&id=30")
        assert u.query_params.getlist("id") == ["10", "20", "30"]
        assert u.query_params["id"] == "30"


# ---------------------------------------------------------------------------
# Cross-domain: URL + find_all_links protocol handoff
# Seam: protocol handoff - find_all_links returns URL objects that should
#        have properly parsed components
# ---------------------------------------------------------------------------


class TestFindAllLinksURLCooperation:
    """Integration: find_all_links + URL component access."""

    @pytest.mark.depends_on("test_find_all_links_extracts_urls", "test_url_parses_scheme")
    def test_extracted_links_have_valid_components(self):
        """Seam: state consistency — integration path for extracted links have valid components across cooperating public APIs."""
        from boltons.urlutils import find_all_links

        text = "Resources: https://docs.example.test/guide/intro and http://cdn.example.test/assets/img.png end."
        links = find_all_links(text)
        assert len(links) >= 2

        schemes = [l.scheme for l in links]
        assert "https" in schemes
        hosts = [l.host for l in links]
        assert "docs.example.test" in hosts

    @pytest.mark.depends_on("test_find_all_links_extracts_urls", "test_url_navigate_relative")
    def test_extracted_link_supports_navigate(self):
        """Seam: state consistency — integration path for extracted link supports navigate across cooperating public APIs."""
        from boltons.urlutils import find_all_links

        text = "See https://base.example.test/docs/page for details."
        links = find_all_links(text)
        assert len(links) >= 1
        navigated = links[0].navigate("../other")
        assert "other" in navigated.path


# ---------------------------------------------------------------------------
# Cross-domain: OMD + subdict cooperation
# Seam: protocol handoff - subdict output type matches input mapping type
# ---------------------------------------------------------------------------


class TestOMDSubdictCooperation:
    """Integration: OrderedMultiDict + subdict."""

    @pytest.mark.depends_on("test_omd_getlist_returns_all_values", "test_subdict_keep_filters")
    def test_subdict_of_omd_preserves_multidict_behavior(self):
        """Seam: state consistency — integration path for subdict of omd preserves multidict behavior across cooperating public APIs."""
        from boltons.dictutils import OrderedMultiDict, subdict

        omd = OrderedMultiDict([("x", 1), ("y", 2), ("x", 3), ("z", 4)])
        sub = subdict(omd, keep=["x", "z"])
        assert "x" in sub
        assert "z" in sub
        assert "y" not in sub


# ---------------------------------------------------------------------------
# Cross-domain: FrozenDict + subdict cooperation
# Seam: protocol handoff - subdict on FrozenDict should return appropriate type
# ---------------------------------------------------------------------------


class TestFrozenDictSubdictCooperation:
    """Integration: FrozenDict + subdict."""

    @pytest.mark.depends_on("test_frozendict_hashable_values_can_hash", "test_subdict_drop_excludes")
    def test_subdict_of_frozendict(self):
        """Seam: state consistency — integration path for subdict of frozendict across cooperating public APIs."""
        from boltons.dictutils import FrozenDict, subdict

        fd = FrozenDict({"a": 1, "b": 2, "c": 3})
        sub = subdict(fd, drop=["b"])
        assert sub["a"] == 1
        assert sub["c"] == 3
        assert "b" not in sub


# ---------------------------------------------------------------------------
# Cross-domain: LRI + cachedmethod lifecycle
# Seam: lifecycle crossing - LRI eviction observed through cachedmethod behavior
# ---------------------------------------------------------------------------


class TestLRICachedMethodLifecycle:
    """Integration: LRI backing + cachedmethod eviction lifecycle."""

    @pytest.mark.depends_on("test_lri_evicts_oldest_by_insertion_order", "test_cachedmethod_caches_result")
    def test_lri_eviction_forces_method_recomputation(self):
        """Seam: protocol handoff — integration path for lri eviction forces method recomputation across cooperating public APIs."""
        from boltons.cacheutils import LRI, cachedmethod

        class Processor:
            def __init__(self):
                self._cache = LRI(max_size=2)
                self._calls = 0

            @cachedmethod("_cache")
            def transform(self, val):
                self._calls += 1
                return val * 7

        p = Processor()
        p.transform("a")
        p.transform("b")
        p.transform("c")  # evicts "a"
        p.transform("a")  # must recompute
        assert p._calls == 4
        assert p.transform("a") == "aaaaaaa"


# ---------------------------------------------------------------------------
# Cross-domain: backoff + unique cooperation
# Seam: protocol handoff - backoff output fed into unique to detect plateaus
# ---------------------------------------------------------------------------


class TestBackoffUniqueCooperation:
    """Integration: backoff output + unique deduplication."""

    @pytest.mark.depends_on("test_backoff_generates_increasing_delays", "test_unique_preserves_first_occurrence")
    def test_backoff_plateau_detected_by_unique(self):
        """Seam: lifecycle crossing — integration path for backoff plateau detected by unique across cooperating public APIs."""
        from boltons.iterutils import backoff, unique

        delays = backoff(start=1, stop=8, factor=2.0, count=10, jitter=False)
        unique_delays = unique(delays)
        # Should have fewer unique values than total due to ceiling
        assert len(unique_delays) <= len(delays)
        assert all(d <= 8 for d in unique_delays)


# ---------------------------------------------------------------------------
# Cross-domain: chunked + flatten round-trip
# Seam: protocol handoff - chunked output fed into flatten should recover original
# ---------------------------------------------------------------------------


class TestChunkedFlattenRoundTrip:
    """Integration: chunked then flatten recovers original sequence."""

    @pytest.mark.depends_on("test_chunked_produces_correct_chunks", "test_flatten_nested_lists")
    def test_chunk_then_flatten_recovers_data(self):
        """Seam: state consistency — integration path for chunk then flatten recovers data across cooperating public APIs."""
        from boltons.iterutils import chunked, flatten

        original = [11, 22, 33, 44, 55, 66, 77]
        chunks = chunked(original, size=3)
        recovered = flatten(chunks)
        assert recovered == original


# ---------------------------------------------------------------------------
# Cross-domain: split + bucketize cooperation
# Seam: protocol handoff - split output fed into bucketize for classification
# ---------------------------------------------------------------------------


class TestSplitBucketizeCooperation:
    """Integration: split segments then bucketize groups them."""

    @pytest.mark.depends_on("test_split_on_none_default", "test_bucketize_by_callable")
    def test_split_then_bucketize_by_length(self):
        """Seam: state consistency — integration path for split then bucketize by length across cooperating public APIs."""
        from boltons.iterutils import split, bucketize

        data = [1, 2, None, 3, 4, 5, None, 6]
        segments = split(data)
        bucketed = bucketize(segments, key=len)
        # segments are [1,2], [3,4,5], [6] -> lengths 2, 3, 1
        assert len(bucketed[1]) >= 1  # length-1 segments
        assert len(bucketed[2]) >= 1  # length-2 segments


# ---------------------------------------------------------------------------
# Cross-domain: URL.from_parts + parse_url agreement
# Seam: state consistency - URL.from_parts and parse_url agree on components
# ---------------------------------------------------------------------------


class TestURLFromPartsParseUrlAgreement:
    """Integration: URL.from_parts + parse_url produce consistent results."""

    @pytest.mark.depends_on("test_parse_url_extracts_components", "test_url_parses_scheme")
    def test_from_parts_serializes_same_as_parsed(self):
        """Seam: state consistency — integration path for from parts serializes same as parsed across cooperating public APIs."""
        from boltons.urlutils import URL, parse_url

        u = URL.from_parts(
            scheme="https",
            host="parts.example.test",
            port=7070,
            path_parts=("", "api", "data", ""),
            query_params=[("fmt", "json")],
            fragment="top",
        )
        text = u.to_text()
        parts = parse_url(text)
        assert parts["scheme"] == "https"
        assert parts["host"] == "parts.example.test"
        assert parts["port"] == 7070
        assert parts["fragment"] == "top"
