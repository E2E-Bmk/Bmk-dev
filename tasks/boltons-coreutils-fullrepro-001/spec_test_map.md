# Stage 3 Spec Test Map: boltons-coreutils-fullrepro-001

oracle_version: 20260704-expanded-86
oracle_source: upstream_rescoped_plus_generated_public_carriers
source_nodeids_collected: 212 upstream plus 172 generated carrier tests
active_kept_nodeids: 86
active_excluded_nodeids: 174 upstream; 124 generated not selected for active scoring
spec_file: spec/spec_v4.md
scorer_isolation: isolated oracle carrier under tmp/boltons_oracle86_20260704; candidate/reference supplied by PYTHONPATH, with no boltons package in carrier

## Merge Rationale

The active oracle keeps the strict v2 38-test upstream cacheutils/dictutils subset and adds 48 generated public-carrier tests. The generated additions import only public names from `boltons.cacheutils`, `boltons.dictutils`, `boltons.iterutils`, and `boltons.urlutils`; they avoid private regexes, out-of-scope `boltons.namedutils` carriers, exact error-message assertions, and internal state checks. This repairs the prior sub-50 oracle and adds direct coverage for the judge-flagged `Cache Key Construction`, `FrozenDict`, iterutils, and urlutils surfaces.

## Covered Tests

| test_nodeid | layer | source | spec_section | status | notes |
|-------------|-------|--------|--------------|--------|-------|
| tests/test_cacheutils.py::test_lru_add | integration | upstream | ### `LRU` | covered | Exercises capacity eviction through public mapping assignment and membership. |
| tests/test_cacheutils.py::test_lri | system_e2e | upstream | ### `LRI` | covered | Exercises on-miss generation, capacity, insertion order, and reinsertion eviction semantics. |
| tests/test_cacheutils.py::test_lri_cache_eviction | system_e2e | upstream | ### `LRI` | covered | Regression for repeated assignment preserving max-size observable behavior. |
| tests/test_cacheutils.py::test_lru_basic | system_e2e | upstream | ### `LRU` | covered | Exercises public mapping operations, eviction, copy/equality, update, setdefault, and clear. |
| tests/test_cacheutils.py::test_lru_dict_replacement[LRU] | system_e2e | upstream | ### `LRU` | covered | Verifies replacing an existing key updates the visible value without duplicate observable entries. |
| tests/test_cacheutils.py::test_lru_dict_replacement[LRI] | system_e2e | upstream | ### `LRI` | covered | Verifies replacing an existing key updates the visible value without duplicate observable entries. |
| tests/test_cacheutils.py::test_cached_dec | system_e2e | upstream | ### `cached` | covered | Verifies cache hits suppress repeated calls and distinct arguments create distinct cached results. |
| tests/test_cacheutils.py::test_unscoped_cached_dec | system_e2e | upstream | ### `cached` | covered | Verifies scoped decorator keys keep different wrapped functions from colliding in a shared cache. |
| tests/test_cacheutils.py::test_callable_cached_dec | system_e2e | upstream | ### `cached` | covered | Verifies callable cache providers and non-crashing public wrapper representation. |
| tests/test_cacheutils.py::test_cachedmethod | system_e2e | upstream | ### `cachedmethod` | covered | Exercises attribute-name, callable-provider, shared-cache unscoped behavior, unbound calls, and representation. |
| tests/test_cacheutils.py::test_cachedmethod_maintains_func_abstraction | system_e2e | upstream | ### `cachedmethod` | covered | Verifies descriptor wrapping preserves abstract method behavior. |
| tests/test_cacheutils.py::test_cachedproperty | system_e2e | upstream | ### `cachedproperty` | covered | Verifies first access stores the value, later access reuses it, deletion clears it, and class access exposes descriptor metadata. |
| tests/test_cacheutils.py::test_cachedproperty_maintains_func_abstraction | system_e2e | upstream | ### `cachedproperty` | covered | Verifies cachedproperty preserves abstract property behavior through the descriptor. |
| tests/test_cacheutils.py::test_min_id_map | system_e2e | upstream | ### `MinIDMap` | covered | Exercises stable compact ids, drop behavior, live-object iteration, and iteritems. |
| tests/test_cacheutils.py::test_threshold_counter | system_e2e | upstream | ### `ThresholdCounter` | covered | Exercises threshold compaction, common/uncommon counts, containment, element iteration, and most_common ordering. |
| tests/test_dictutils.py::test_dict_init | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies construction from mapping, lookup, len, getlist, and flattened equality. |
| tests/test_dictutils.py::test_todict | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies todict multi-value preservation and flattened latest-value behavior. |
| tests/test_dictutils.py::test_eq | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies equality with ordered multi-dicts and normal mappings. |
| tests/test_dictutils.py::test_copy | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies independent copies preserve all pairs and diverge after mutation. |
| tests/test_dictutils.py::test_omd_pickle | system_e2e | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies pickle round trips preserve repeated values and order. |
| tests/test_dictutils.py::test_clear | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies clear removes all pairs and leaves the mapping reusable. |
| tests/test_dictutils.py::test_multi_correctness | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies iteritems multi and flattened modes expose values in documented order. |
| tests/test_dictutils.py::test_kv_consistency | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies items, keys, and values views agree for flattened and multi-pair modes. |
| tests/test_dictutils.py::test_update_basic | system_e2e | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies update replaces existing values and copies remain independent. |
| tests/test_dictutils.py::test_update | system_e2e | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies update matches flattened dict update semantics and self-update is visibly idempotent. |
| tests/test_dictutils.py::test_update_extend | system_e2e | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies update_extend appends incoming values while preserving existing keys. |
| tests/test_dictutils.py::test_invert | system_e2e | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies inverted preserves the count of stored pairs and exposes original values as keys. |
| tests/test_dictutils.py::test_poplast | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies poplast returns the last inserted value. |
| tests/test_dictutils.py::test_pop | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies pop removes all values for a key, handles defaults, and raises KeyError when appropriate. |
| tests/test_dictutils.py::test_addlist | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies addlist appends iterable values and ignores empty iterable additions. |
| tests/test_dictutils.py::test_pop_all | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies popall returns all values and honors defaults for missing keys. |
| tests/test_dictutils.py::test_reversed | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies reverse iteration over unique keys follows reverse first-insertion order. |
| tests/test_dictutils.py::test_setdefault | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies setdefault stores and returns defaults without replacing existing values. |
| tests/test_dictutils.py::test_ior | integration | upstream | ### `OrderedMultiDict`, `OMD`, and `MultiDict` | covered | Verifies in-place union behaves as an in-place update for ordered multi-dicts. |
| tests/test_dictutils.py::test_subdict | integration | upstream | ### `subdict` | covered | Verifies keep and drop select keys without mutating the original mapping. |
| tests/test_dictutils.py::test_subdict_keep_type | integration | upstream | ### `subdict` | covered | Verifies the returned mapping preserves type(d) for ordered multi-dicts. |
| tests/test_dictutils.py::test_one_to_one | system_e2e | upstream | ### `OneToOne` | covered | Exercises forward/inverse consistency through assignment, inverse assignment, deletion, pop, setdefault, update, and unique validation. |
| tests/test_dictutils.py::test_many_to_many | system_e2e | upstream | ### `ManyToMany` | covered | Exercises bidirectional relation consistency, inverse mutation, replacement, iteration, equality, and visible representation sanity. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_make_cache_key_single_fast_arg | atomic | generated | ### Cache Key Construction | covered | Verifies a single fast positional argument can be used directly as the key. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_make_cache_key_kwargs_are_order_independent | atomic | generated | ### Cache Key Construction | covered | Verifies keyword order does not change the constructed key. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_make_cache_key_typed_distinguishes_equal_values | atomic | generated | ### Cache Key Construction | covered | Verifies typed keys distinguish equal values with different types. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_frozendict_mapping_and_updated_copy | integration | generated | ### `FrozenDict` and `FrozenHashError` | covered | Verifies mapping reads and updated copy creation without mutating the original. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_frozendict_rejects_mutation | atomic | generated | ### `FrozenDict` and `FrozenHashError` | covered | Verifies item assignment raises TypeError for immutable mappings. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_frozendict_hash_error_for_unhashable_values | atomic | generated | ### `FrozenDict` and `FrozenHashError` | covered | Verifies hashing a mapping with unhashable values raises FrozenHashError. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_is_iterable_list | atomic | generated | ### Type Checks | covered | Verifies list objects are iterable. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_is_scalar_string | atomic | generated | ### Type Checks | covered | Verifies strings are treated as scalar values. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_is_collection_list | atomic | generated | ### Type Checks | covered | Verifies lists are collections. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_split_basic_sep | atomic | generated | ### Splitting and Stripping | covered | Verifies split separates list groups on a literal separator. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_split_callable_sep | atomic | generated | ### Splitting and Stripping | covered | Verifies callable separators split when the predicate is true. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_lstrip_removes_leading | atomic | generated | ### Splitting and Stripping | covered | Verifies leading strip values are removed. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_strip_both_ends | atomic | generated | ### Splitting and Stripping | covered | Verifies strip removes matching values from both ends. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_chunked_basic | atomic | generated | ### Chunking and Windows | covered | Verifies chunked groups an iterable into fixed-size chunks. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_chunk_ranges_basic | atomic | generated | ### Chunking and Windows | covered | Verifies chunk_ranges emits contiguous half-open ranges. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_pairwise_basic | atomic | generated | ### Chunking and Windows | covered | Verifies pairwise emits adjacent pairs. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_windowed_basic | atomic | generated | ### Chunking and Windows | covered | Verifies windowed emits overlapping fixed-size windows. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_xfrange_basic | atomic | generated | ### Numeric Sequences and Backoff | covered | Verifies xfrange starts at zero and emits the expected count. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_frange_basic | atomic | generated | ### Numeric Sequences and Backoff | covered | Verifies frange returns a list form of the numeric sequence. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_backoff_basic | atomic | generated | ### Numeric Sequences and Backoff | covered | Verifies backoff starts and stops at the configured bounds. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_bucketize_basic | atomic | generated | ### Grouping, Uniqueness, and Reduction | covered | Verifies bucketize groups items by a callable key. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_partition_multiple_keys | atomic | generated | ### Grouping, Uniqueness, and Reduction | covered | Verifies partition returns one bucket per predicate plus a residual bucket. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_unique_basic | atomic | generated | ### Grouping, Uniqueness, and Reduction | covered | Verifies unique preserves first occurrence order. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_redundant_basic | atomic | generated | ### Grouping, Uniqueness, and Reduction | covered | Verifies redundant returns values observed more than once. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_one_single_match | atomic | generated | ### Grouping, Uniqueness, and Reduction | covered | Verifies one returns the sole matching element. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_same_not_equal | atomic | generated | ### Grouping, Uniqueness, and Reduction | covered | Verifies same returns False when values differ. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_flatten_nested | atomic | generated | ### Flattening and Nested Traversal | covered | Verifies nested lists flatten to a single list of scalar leaves. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_remap_basic | integration | generated | ### Flattening and Nested Traversal | covered | Verifies remap preserves nested mapping/list structure with default callbacks. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_get_path_nested_dict | atomic | generated | ### Flattening and Nested Traversal | covered | Verifies get_path resolves a tuple path through nested mappings. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_research_basic | integration | generated | ### Flattening and Nested Traversal | covered | Verifies research returns matching path/value pairs from nested data. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_guiderator_yields_strings | atomic | generated | ### GUID Generators | covered | Verifies GUIDerator yields fixed-length string ids. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_sequential_guiderator_deterministic | atomic | generated | ### GUID Generators | covered | Verifies SequentialGUIDerator can be reseeded and continues yielding strings. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_url_parse_error | atomic | generated | ### Public Constants and Exceptions | covered | Verifies invalid port text raises URLParseError. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_quote_path_part_basic | atomic | generated | ### Text Conversion and Quoting | covered | Verifies path quoting removes raw spaces. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_unquote_basic | atomic | generated | ### Text Conversion and Quoting | covered | Verifies percent-encoded text decodes to Unicode text. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_to_unicode_bytes | atomic | generated | ### Text Conversion and Quoting | covered | Verifies byte input converts to text. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_parse_url_basic | atomic | generated | ### Parsing Helpers | covered | Verifies parse_url exposes scheme and host fields. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_parse_host_plain | atomic | generated | ### Parsing Helpers | covered | Verifies plain host parsing returns the host with no socket family. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_parse_qsl_basic | atomic | generated | ### Parsing Helpers | covered | Verifies query-string parsing returns key/value pairs. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_resolve_path_parts_dot | atomic | generated | ### Parsing Helpers | covered | Verifies dot path segments are resolved away. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_query_param_dict_from_text | integration | generated | ### `QueryParamDict` | covered | Verifies repeated query keys preserve all values. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_query_param_dict_to_text | atomic | generated | ### `QueryParamDict` | covered | Verifies query parameters serialize to key=value text. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_url_basic_parse | integration | generated | ### `URL` | covered | Verifies URL construction exposes scheme, host, path, and fragment. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_url_normalize | system_e2e | generated | ### `URL` | covered | Verifies normalization lowercases scheme/host and resolves path segments. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_url_navigate_relative | system_e2e | generated | ### `URL` | covered | Verifies relative navigation resolves against the base URL path. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_url_from_parts | integration | generated | ### `URL` | covered | Verifies from_parts builds text with host and path components. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_find_all_links_basic | integration | generated | ### Link Extraction | covered | Verifies link extraction returns URL objects for links in surrounding text. |
| wip/boltons-coreutils-fullrepro-001/filter/generated_tests.py::test_find_all_links_with_text | system_e2e | generated | ### Link Extraction | covered | Verifies link extraction can preserve surrounding text tokens with URL objects. |

## Exclusion Summary

The upstream v2 exclusion audit remains in `excluded_nodeids_v2.tsv` and `filter_correction_request.md`. Excluded upstream nodeids still include private linked-list assertions, exact inheritance/API-shape checks, exact error-message checks, private `_URL_RE` carriers, and original files that collect only with out-of-scope modules. Generated tests not selected for this active oracle are left as non-scoring coverage context; selection favored compact, public, spec-mapped behavior across the previously uncovered headings.

Total: 86 | kept (covered): 86 | spec_gap: 0 | source-only: 0 | excluded: 174 upstream + 124 generated not selected | final scoreable: 86
