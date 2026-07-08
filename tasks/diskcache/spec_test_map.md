# DiskCache Stage 3 Test Filter

spec_version: spec_v3
oracle_source: upstream_only
collection_note: pytest collection required `-o addopts=` because tox.ini references unavailable plugins; Django is not installed, so tests/test_djangocache.py and tests/test_doctest.py were statically parsed. Django inherited BaseCacheTests methods are represented as DiskCacheTests nodeids.
rerun_note: Stage 3 was rerun against spec_v3 after the FanoutCache lifecycle/context-manager patch; FanoutCache covered rows remain spec-driven behavioral checks, and no FanoutCache lifecycle rows are spec_gap.
track_b: not_triggered because Track A kept >= 30 nodeids with atomic, integration, and system_e2e coverage.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| tests/test_core.py::test_init | atomic | ### Cache | covered | constructor/settings public attributes |
| tests/test_core.py::test_init_path | atomic | ### Cache | covered | constructor/settings public attributes |
| tests/test_core.py::test_init_disk | atomic | ### Cache | covered | constructor/settings public attributes |
| tests/test_core.py::test_disk_reset | atomic | - | excluded | asserts cache._disk private attributes |
| tests/test_core.py::test_disk_valueerror | atomic | - | source-only | constructor misuse error is not specified by public contract |
| tests/test_core.py::test_custom_disk | integration | ### Disk And JSONDisk | covered | public disk serialization/customization behavior |
| tests/test_core.py::test_custom_filename_disk | atomic | - | source-only | custom Disk uses private _directory and asserts exact file path/layout |
| tests/test_core.py::test_init_makedirs | atomic | - | source-only | exact os.makedirs failure propagation is not specified |
| tests/test_core.py::test_pragma_error | atomic | - | excluded | mocks private connection/local state and SQLite pragma retry internals |
| tests/test_core.py::test_close_error | atomic | - | excluded | mocks private thread-local connection state |
| tests/test_core.py::test_getsetdel | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_get_keyerror1 | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| tests/test_core.py::test_get_keyerror4 | atomic | - | excluded | patches diskcache.core.open to force private file IO error path |
| tests/test_core.py::test_read | integration | ### Cache | covered | file-backed read/read=True behavior |
| tests/test_core.py::test_read_keyerror | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| tests/test_core.py::test_set_twice | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_set_timeout | atomic | - | excluded | mocks private _local connection state |
| tests/test_core.py::test_raw | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_get | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_get_expired_fast_path | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| tests/test_core.py::test_get_ioerror_fast_path | atomic | - | excluded | mocks cache._disk private internals |
| tests/test_core.py::test_get_expired_slow_path | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| tests/test_core.py::test_pop | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_pop_ioerror | atomic | - | excluded | mocks cache._disk private internals |
| tests/test_core.py::test_delete | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_del | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_del_expired | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| tests/test_core.py::test_stats | integration | ### Cache | covered | public statistics counters |
| tests/test_core.py::test_path | integration | ### Cache | covered | file-backed read/read=True behavior |
| tests/test_core.py::test_expire_rows | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| tests/test_core.py::test_least_recently_stored | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| tests/test_core.py::test_least_recently_used | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| tests/test_core.py::test_least_frequently_used | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| tests/test_core.py::test_check | atomic | - | excluded | uses cache._sql and corrupts private SQLite rows |
| tests/test_core.py::test_integrity_check | atomic | - | excluded | mutates internal cache.db bytes directly |
| tests/test_core.py::test_expire | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| tests/test_core.py::test_tag_index | atomic | ### Cache | covered | constructor/settings public attributes |
| tests/test_core.py::test_evict | integration | ## Cache Behavior | covered | tag metadata and tag eviction |
| tests/test_core.py::test_clear | atomic | ### Cache | covered | clear removes entries and reports count |
| tests/test_core.py::test_clear_timeout | atomic | - | excluded | mocks private _transact |
| tests/test_core.py::test_tag | integration | ## Cache Behavior | covered | tag metadata and tag eviction |
| tests/test_core.py::test_with | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or serialized cache handles |
| tests/test_core.py::test_contains | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_touch | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_add | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_add_large_value | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_add_timeout | atomic | - | excluded | mocks private _local connection state |
| tests/test_core.py::test_incr | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_incr_insert_keyerror | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| tests/test_core.py::test_incr_update_keyerror | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| tests/test_core.py::test_decr | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| tests/test_core.py::test_iter | atomic | ### Cache | covered | mapping iteration order views |
| tests/test_core.py::test_iter_expire | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| tests/test_core.py::test_iter_error | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| tests/test_core.py::test_reversed | atomic | ### Cache | covered | mapping iteration order views |
| tests/test_core.py::test_reversed_error | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| tests/test_core.py::test_push_pull | integration | ### Cache | covered | queue helpers and generated keys |
| tests/test_core.py::test_push_pull_prefix | integration | ### Cache | covered | queue helpers and generated keys |
| tests/test_core.py::test_push_pull_extras | atomic | - | source-only | asserts exact generated queue key number not specified by spec |
| tests/test_core.py::test_push_pull_expire | atomic | - | source-only | asserts exact generated queue key number not specified by spec |
| tests/test_core.py::test_push_peek_expire | atomic | - | source-only | asserts exact generated queue key number not specified by spec |
| tests/test_core.py::test_push_pull_large_value | atomic | - | source-only | asserts exact generated queue key number not specified by spec |
| tests/test_core.py::test_push_peek_large_value | atomic | - | source-only | asserts exact generated queue key number not specified by spec |
| tests/test_core.py::test_pull_ioerror | atomic | - | excluded | mocks cache._disk private internals |
| tests/test_core.py::test_peek_ioerror | atomic | - | excluded | mocks cache._disk private internals |
| tests/test_core.py::test_peekitem_extras | atomic | ### Cache | covered | public Cache behavior |
| tests/test_core.py::test_peekitem_ioerror | atomic | - | excluded | mocks cache._disk private internals |
| tests/test_core.py::test_iterkeys | integration | ### Cache | covered | queue helpers and generated keys |
| tests/test_core.py::test_pickle | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or serialized cache handles |
| tests/test_core.py::test_pragmas | atomic | - | excluded | asserts SQLite pragma/internal _sql shape |
| tests/test_core.py::test_size_limit_with_files | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| tests/test_core.py::test_size_limit_with_database | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| tests/test_core.py::test_cull_eviction_policy_none | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| tests/test_core.py::test_cull_size_limit_0 | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| tests/test_core.py::test_cull_timeout | atomic | - | excluded | mocks private _transact internals |
| tests/test_core.py::test_key_roundtrip | integration | ### Disk And JSONDisk | covered | public disk serialization/customization behavior |
| tests/test_core.py::test_constant | atomic | - | source-only | checks exact sentinel repr string |
| tests/test_core.py::test_copy | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or serialized cache handles |
| tests/test_core.py::test_rsync | atomic | - | excluded | depends on external rsync executable and filesystem synchronization tool |
| tests/test_core.py::test_custom_eviction_policy | atomic | - | source-only | depends on custom SQL eviction-policy internals not in spec |
| tests/test_core.py::test_lru_incr | integration | ## Cache Behavior | covered | counter operations under LRU policy |
| tests/test_core.py::test_memoize | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| tests/test_core.py::test_memoize_kwargs | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| tests/test_core.py::test_cleanup_dirs | atomic | - | source-only | asserts internal file cleanup/count layout |
| tests/test_core.py::test_disk_write_os_error | atomic | - | excluded | mocks module open path to force private write path |
| tests/test_core.py::test_memoize_ignore | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| tests/test_core.py::test_memoize_iter | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| tests/test_deque.py::test_init | system_e2e | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_getsetdel | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_append | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_appendleft | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_index_positive | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_index_negative | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_index_out_of_range | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_iter_keyerror | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_reversed | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_reversed_keyerror | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_state | system_e2e | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_compare | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_indexerror_negative | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_indexerror | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_repr | atomic | - | source-only | checks exact repr string |
| tests/test_deque.py::test_copy | system_e2e | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_count | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_extend | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_extendleft | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_pop | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_pop_indexerror | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_popleft | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_popleft_indexerror | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_remove | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_remove_valueerror | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_remove_keyerror | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_reverse | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_rotate_typeerror | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_rotate | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_rotate_negative | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_deque.py::test_rotate_indexerror | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_rotate_indexerror_negative | atomic | - | excluded | mocks deque._cache private internals |
| tests/test_deque.py::test_peek | atomic | - | source-only | upstream file has top-level import from undocumented diskcache.core; no public-surface rewrite provided |
| tests/test_djangocache.py::DiskCacheTests::test_simple | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_default_used_when_none_is_set | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_add | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_prefix | integration | ### DjangoCache | covered | key transform prefix/version/custom-key consistency isolates logical keys |
| tests/test_djangocache.py::DiskCacheTests::test_non_existent | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_get_many | atomic | ### DjangoCache | covered | multi-key behavior: get_many returns found live keys and omits missing keys |
| tests/test_djangocache.py::DiskCacheTests::test_delete | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_delete_nonexistent | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_has_key | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_in | atomic | ### DjangoCache | covered | containment is a public live-key lookup view equivalent to has_key |
| tests/test_djangocache.py::DiskCacheTests::test_incr | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_decr | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_close | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_data_types | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_cache_read_for_model_instance | atomic | - | source-only | Django model default side-effect behavior is outside diskcache spec |
| tests/test_djangocache.py::DiskCacheTests::test_cache_write_for_model_instance_with_deferred | atomic | - | source-only | Django QuerySet deferred-field side effect is outside diskcache spec |
| tests/test_djangocache.py::DiskCacheTests::test_cache_read_for_model_instance_with_deferred | atomic | - | source-only | Django QuerySet deferred-field side effect is outside diskcache spec |
| tests/test_djangocache.py::DiskCacheTests::test_expiration | integration | ### DjangoCache | covered | Django timeout conversion and expiration behavior |
| tests/test_djangocache.py::DiskCacheTests::test_touch | integration | ### DjangoCache | covered | Django timeout conversion and expiration behavior |
| tests/test_djangocache.py::DiskCacheTests::test_unicode | atomic | ### DjangoCache | covered | multi-key behavior covers set_many storage for unicode values |
| tests/test_djangocache.py::DiskCacheTests::test_binary_string | atomic | ### DjangoCache | covered | multi-key behavior covers set_many storage for binary values |
| tests/test_djangocache.py::DiskCacheTests::test_set_many | atomic | ### DjangoCache | covered | multi-key behavior: set_many stores every key/value pair |
| tests/test_djangocache.py::DiskCacheTests::test_set_many_returns_empty_list_on_success | atomic | ### DjangoCache | covered | multi-key behavior: set_many returns empty list when all writes succeed |
| tests/test_djangocache.py::DiskCacheTests::test_set_many_expiration | integration | ### DjangoCache | covered | multi-key behavior: set_many applies timeout conversion to every pair |
| tests/test_djangocache.py::DiskCacheTests::test_delete_many | atomic | ### DjangoCache | covered | multi-key behavior: delete_many deletes requested keys and ignores missing keys |
| tests/test_djangocache.py::DiskCacheTests::test_clear | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| tests/test_djangocache.py::DiskCacheTests::test_long_timeout | integration | ### DjangoCache | covered | timeout conversion applies to set_many and long timeouts use backend semantics |
| tests/test_djangocache.py::DiskCacheTests::test_forever_timeout | integration | ### DjangoCache | covered | timeout conversion applies to set_many and timeout=None stores without expiration |
| tests/test_djangocache.py::DiskCacheTests::test_zero_timeout | integration | ### DjangoCache | covered | timeout conversion applies to set_many and timeout=0 stores already expired |
| tests/test_djangocache.py::DiskCacheTests::test_float_timeout | integration | ### DjangoCache | covered | Django timeout conversion and expiration behavior |
| tests/test_djangocache.py::DiskCacheTests::test_cull_delete_when_store_empty | atomic | - | excluded | mutates _max_entries private internal state |
| tests/test_djangocache.py::DiskCacheTests::test_cache_versioning_get_set | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| tests/test_djangocache.py::DiskCacheTests::test_cache_versioning_add | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| tests/test_djangocache.py::DiskCacheTests::test_cache_versioning_has_key | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| tests/test_djangocache.py::DiskCacheTests::test_cache_versioning_delete | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| tests/test_djangocache.py::DiskCacheTests::test_cache_versioning_incr_decr | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| tests/test_djangocache.py::DiskCacheTests::test_cache_versioning_get_set_many | integration | ### DjangoCache | covered | key transform prefix/version/custom-key consistency applies to multi-key methods |
| tests/test_djangocache.py::DiskCacheTests::test_incr_version | integration | ### DjangoCache | covered | version-changing methods move live values to incremented version and delete old key |
| tests/test_djangocache.py::DiskCacheTests::test_decr_version | integration | ### DjangoCache | covered | version-changing methods move live values to decremented version and delete old key |
| tests/test_djangocache.py::DiskCacheTests::test_custom_key_func | integration | ### DjangoCache | covered | key transform prefix/version/custom-key consistency isolates custom key functions |
| tests/test_djangocache.py::DiskCacheTests::test_cache_write_unpicklable_object | atomic | - | excluded | uses Django middleware request._cache_update_cache internal state |
| tests/test_djangocache.py::DiskCacheTests::test_add_fail_on_pickleerror | atomic | ### DjangoCache | covered | serialization error propagation from add for unserializable values |
| tests/test_djangocache.py::DiskCacheTests::test_set_fail_on_pickleerror | atomic | ### DjangoCache | covered | serialization error propagation from set for unserializable values |
| tests/test_djangocache.py::DiskCacheTests::test_get_or_set | atomic | ### DjangoCache | covered | get_or_set stores and returns missing defaults including stored None values |
| tests/test_djangocache.py::DiskCacheTests::test_get_or_set_callable | atomic | ### DjangoCache | covered | get_or_set evaluates callable defaults and stores the result |
| tests/test_djangocache.py::DiskCacheTests::test_get_or_set_version | atomic | - | source-only | checks exact TypeError message text |
| tests/test_djangocache.py::DiskCacheTests::test_get_or_set_racing | atomic | - | source-only | mocks backend add to force Django BaseCache race path not specified here |
| tests/test_djangocache.py::DiskCacheTests::test_ignores_non_cache_files | atomic | - | source-only | asserts treatment of arbitrary non-cache files in backend directory |
| tests/test_djangocache.py::DiskCacheTests::test_creates_cache_dir_if_nonexistent | integration | ### DjangoCache | covered | backend directory lifecycle behavior |
| tests/test_djangocache.py::DiskCacheTests::test_clear_does_not_remove_cache_dir | integration | ### DjangoCache | covered | backend directory lifecycle behavior |
| tests/test_djangocache.py::DiskCacheTests::test_cache_write_unpicklable_type | atomic | ### DjangoCache | covered | pickleable value storage behavior |
| tests/test_djangocache.py::DiskCacheTests::test_cull | atomic | - | excluded | dummy-pass override with no behavioral assertion |
| tests/test_djangocache.py::DiskCacheTests::test_zero_cull | atomic | - | excluded | dummy-pass override with no assertion |
| tests/test_djangocache.py::DiskCacheTests::test_invalid_key_characters | atomic | - | excluded | dummy-pass override with no assertion |
| tests/test_djangocache.py::DiskCacheTests::test_invalid_key_length | atomic | - | excluded | dummy-pass override with no assertion |
| tests/test_djangocache.py::DiskCacheTests::test_directory | atomic | - | source-only | asserts environment-specific temporary path fragment |
| tests/test_djangocache.py::DiskCacheTests::test_read | integration | ### DjangoCache | covered | file-backed read support |
| tests/test_djangocache.py::DiskCacheTests::test_expire | integration | ### DjangoCache | covered | DiskCache extension methods exposed by Django backend |
| tests/test_djangocache.py::DiskCacheTests::test_evict | integration | ### DjangoCache | covered | DiskCache extension methods exposed by Django backend |
| tests/test_djangocache.py::DiskCacheTests::test_pop | integration | ### DjangoCache | covered | DiskCache extension methods exposed by Django backend |
| tests/test_djangocache.py::DiskCacheTests::test_cache | atomic | - | source-only | asserts exact named subcache directory layout |
| tests/test_djangocache.py::DiskCacheTests::test_deque | atomic | - | source-only | asserts exact named deque directory layout |
| tests/test_djangocache.py::DiskCacheTests::test_index | atomic | - | source-only | asserts exact named index directory layout |
| tests/test_djangocache.py::DiskCacheTests::test_memoize | integration | ### DjangoCache | covered | DjangoCache memoize behavior |
| tests/test_doctest.py::test_core | atomic | - | source-only | doctest aggregate is not an atomic spec-mappable behavioral nodeid |
| tests/test_doctest.py::test_djangocache | atomic | - | source-only | doctest aggregate is not an atomic spec-mappable behavioral nodeid |
| tests/test_doctest.py::test_fanout | atomic | - | source-only | doctest aggregate is not an atomic spec-mappable behavioral nodeid |
| tests/test_doctest.py::test_persistent | atomic | - | source-only | doctest aggregate is not an atomic spec-mappable behavioral nodeid |
| tests/test_doctest.py::test_recipes | atomic | - | source-only | doctest aggregate is not an atomic spec-mappable behavioral nodeid |
| tests/test_doctest.py::test_tutorial | atomic | - | source-only | doctest aggregate is not an atomic spec-mappable behavioral nodeid |
| tests/test_fanout.py::test_init | atomic | ### FanoutCache | covered | constructor/settings public attributes |
| tests/test_fanout.py::test_init_path | atomic | ### FanoutCache | covered | constructor/settings public attributes |
| tests/test_fanout.py::test_set_get_delete | system_e2e | ### FanoutCache | covered | core fanout mapping workflow across shards |
| tests/test_fanout.py::test_set_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_touch | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| tests/test_fanout.py::test_touch_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_add | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| tests/test_fanout.py::test_add_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_add_concurrent | system_e2e | ## Sharding Behavior | covered | public concurrent operations through fanout |
| tests/test_fanout.py::test_incr | atomic | - | source-only | dummy-pass nodeid: expression result is not asserted |
| tests/test_fanout.py::test_incr_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_decr | atomic | - | source-only | dummy-pass nodeid: expression result is not asserted |
| tests/test_fanout.py::test_decr_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_incr_concurrent | system_e2e | ## Sharding Behavior | covered | public concurrent operations through fanout |
| tests/test_fanout.py::test_getsetdel | system_e2e | ### FanoutCache | covered | core fanout mapping workflow across shards |
| tests/test_fanout.py::test_get_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_pop | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| tests/test_fanout.py::test_pop_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_delete_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_delitem | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| tests/test_fanout.py::test_delitem_keyerror | atomic | ## Error Semantics | covered | public missing-key behavior |
| tests/test_fanout.py::test_tag_index | integration | ## Sharding Behavior | covered | aggregate tag index and eviction behavior |
| tests/test_fanout.py::test_read | integration | ### FanoutCache | covered | file-backed read behavior via FanoutCache |
| tests/test_fanout.py::test_read_keyerror | atomic | ## Error Semantics | covered | public missing-key behavior |
| tests/test_fanout.py::test_getitem_keyerror | atomic | ## Error Semantics | covered | public missing-key behavior |
| tests/test_fanout.py::test_expire | integration | ## Sharding Behavior | covered | aggregate expiration across shards |
| tests/test_fanout.py::test_evict | integration | ## Sharding Behavior | covered | aggregate tag index and eviction behavior |
| tests/test_fanout.py::test_size_limit_with_files | integration | ## Sharding Behavior | covered | size limit divided across shards |
| tests/test_fanout.py::test_size_limit_with_database | integration | ## Sharding Behavior | covered | size limit divided across shards |
| tests/test_fanout.py::test_clear | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| tests/test_fanout.py::test_remove_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_reset_timeout | atomic | - | excluded | mocks _shards private internals |
| tests/test_fanout.py::test_stats | integration | ## Sharding Behavior | covered | aggregate stats across shards |
| tests/test_fanout.py::test_volume | atomic | - | excluded | asserts cache._shards private composition |
| tests/test_fanout.py::test_iter | atomic | ## Sharding Behavior | covered | aggregate iteration views |
| tests/test_fanout.py::test_iter_expire | integration | ## Sharding Behavior | covered | aggregate expiration across shards |
| tests/test_fanout.py::test_reversed | atomic | ## Sharding Behavior | covered | aggregate iteration views |
| tests/test_fanout.py::test_pickle | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or pickled fanout cache |
| tests/test_fanout.py::test_memoize | integration | ### FanoutCache | covered | fanout memoize behavior |
| tests/test_fanout.py::test_copy | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or pickled fanout cache |
| tests/test_fanout.py::test_rsync | atomic | - | excluded | depends on external rsync executable and filesystem synchronization tool |
| tests/test_fanout.py::test_custom_filename_disk | atomic | - | source-only | asserts exact shard directory and file path layout |
| tests/test_index.py::test_init | system_e2e | ### Index | covered | persistent construction/pickle behavior |
| tests/test_index.py::test_getsetdel | atomic | ### Index | covered | public mapping/order behavior |
| tests/test_index.py::test_pop | atomic | ### Index | covered | public mapping/order behavior |
| tests/test_index.py::test_pop_keyerror | atomic | ## Error Semantics | covered | public Index missing-key behavior |
| tests/test_index.py::test_popitem | atomic | ### Index | covered | public mapping/order behavior |
| tests/test_index.py::test_popitem_keyerror | atomic | ## Error Semantics | covered | public Index missing-key behavior |
| tests/test_index.py::test_setdefault | atomic | ### Index | covered | public mapping/order behavior |
| tests/test_index.py::test_iter | atomic | ### Index | covered | public mapping/order behavior |
| tests/test_index.py::test_reversed | atomic | ### Index | covered | public mapping/order behavior |
| tests/test_index.py::test_state | system_e2e | ### Index | covered | persistent construction/pickle behavior |
| tests/test_index.py::test_memoize | atomic | - | excluded | asserts index._cache private statistics |
| tests/test_index.py::test_repr | atomic | - | source-only | checks exact repr prefix |
| tests/test_recipes.py::test_averager | atomic | ### Recipes | covered | public recipe behavior |
| tests/test_recipes.py::test_lock | system_e2e | ### Recipes | covered | recipe coordination across threads |
| tests/test_recipes.py::test_rlock | system_e2e | ### Recipes | covered | recipe coordination across threads |
| tests/test_recipes.py::test_semaphore | system_e2e | ### Recipes | covered | recipe coordination across threads |
| tests/test_recipes.py::test_memoize_stampede | atomic | ### Recipes | covered | public recipe behavior |

Total: 249 | kept (covered): 148 | spec_gap: 0 | source-only: 56 | excluded: 45 | final scoreable: 148
Layer counts: atomic: 74 | integration: 60 | system_e2e: 14
