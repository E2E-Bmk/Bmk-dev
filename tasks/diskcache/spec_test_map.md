# DiskCache Spec Test Map

| test_nodeid | layer | spec_section | status | notes |
|---|---|---|---|---|
| oracle/test_atomic.py::test_core__init | atomic | ### Cache | covered | constructor/settings public attributes |
| oracle/test_atomic.py::test_core__init_path | atomic | ### Cache | covered | constructor/settings public attributes |
| oracle/test_atomic.py::test_core__init_disk | atomic | ### Cache | covered | constructor/settings public attributes |
| oracle/test_integration.py::test_core__custom_disk | integration | ### Disk And JSONDisk | covered | public disk serialization/customization behavior |
| oracle/test_atomic.py::test_core__getsetdel | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__get_keyerror1 | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| oracle/test_integration.py::test_core__read | integration | ### Cache | covered | file-backed read/read=True behavior |
| oracle/test_atomic.py::test_core__read_keyerror | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| oracle/test_atomic.py::test_core__set_twice | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__raw | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__get | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_integration.py::test_core__get_expired_fast_path | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| oracle/test_integration.py::test_core__get_expired_slow_path | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| oracle/test_atomic.py::test_core__pop | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__delete | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__del | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__del_expired | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| oracle/test_integration.py::test_core__stats | integration | ### Cache | covered | public statistics counters |
| oracle/test_integration.py::test_core__path | integration | ### Cache | covered | file-backed read/read=True behavior |
| oracle/test_integration.py::test_core__expire_rows | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| oracle/test_integration.py::test_core__least_recently_stored | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| oracle/test_integration.py::test_core__least_recently_used | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| oracle/test_integration.py::test_core__least_frequently_used | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| oracle/test_integration.py::test_core__expire | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| oracle/test_atomic.py::test_core__tag_index | atomic | ### Cache | covered | constructor/settings public attributes |
| oracle/test_integration.py::test_core__evict | integration | ## Cache Behavior | covered | tag metadata and tag eviction |
| oracle/test_atomic.py::test_core__clear | atomic | ### Cache | covered | clear removes entries and reports count |
| oracle/test_integration.py::test_core__tag | integration | ## Cache Behavior | covered | tag metadata and tag eviction |
| oracle/test_integration.py::test_core__with | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or serialized cache handles |
| oracle/test_atomic.py::test_core__contains | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__touch | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__add | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__add_large_value | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__incr | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__incr_insert_keyerror | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| oracle/test_atomic.py::test_core__incr_update_keyerror | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| oracle/test_atomic.py::test_core__decr | atomic | ### Cache | covered | core mapping/add/get/pop/delete/counter behavior |
| oracle/test_atomic.py::test_core__iter | atomic | ### Cache | covered | mapping iteration order views |
| oracle/test_integration.py::test_core__iter_expire | integration | ## Cache Behavior | covered | expiration and lazy cleanup behavior |
| oracle/test_atomic.py::test_core__iter_error | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| oracle/test_atomic.py::test_core__reversed | atomic | ### Cache | covered | mapping iteration order views |
| oracle/test_atomic.py::test_core__reversed_error | atomic | ## Error Semantics | covered | public missing-key or iterator error behavior |
| oracle/test_integration.py::test_core__push_pull | integration | ### Cache | covered | queue helpers and generated keys |
| oracle/test_integration.py::test_core__push_pull_prefix | integration | ### Cache | covered | queue helpers and generated keys |
| oracle/test_atomic.py::test_core__peekitem_extras | atomic | ### Cache | covered | public Cache behavior |
| oracle/test_integration.py::test_core__iterkeys | integration | ### Cache | covered | queue helpers and generated keys |
| oracle/test_integration.py::test_core__pickle | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or serialized cache handles |
| oracle/test_integration.py::test_core__size_limit_with_files | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| oracle/test_integration.py::test_core__size_limit_with_database | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| oracle/test_integration.py::test_core__cull_eviction_policy_none | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| oracle/test_integration.py::test_core__cull_size_limit_0 | integration | ## Cache Behavior | covered | public culling and eviction policy effects |
| oracle/test_integration.py::test_core__key_roundtrip | integration | ### Disk And JSONDisk | covered | public disk serialization/customization behavior |
| oracle/test_integration.py::test_core__copy | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or serialized cache handles |
| oracle/test_integration.py::test_core__lru_incr | integration | ## Cache Behavior | covered | counter operations under LRU policy |
| oracle/test_integration.py::test_core__memoize | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| oracle/test_integration.py::test_core__memoize_kwargs | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| oracle/test_integration.py::test_core__memoize_ignore | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| oracle/test_integration.py::test_core__memoize_iter | integration | ### Cache | covered | memoize decorator public behavior and wrapper cache keys |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__simple | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__default_used_when_none_is_set | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__add | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__prefix | integration | ### DjangoCache | covered | key transform prefix/version/custom-key consistency isolates logical keys |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__non_existent | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__get_many | atomic | ### DjangoCache | covered | multi-key behavior: get_many returns found live keys and omits missing keys |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__delete | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__delete_nonexistent | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__has_key | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__in | atomic | ### DjangoCache | covered | containment is a public live-key lookup view equivalent to has_key |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__incr | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__decr | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__close | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__data_types | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__expiration | integration | ### DjangoCache | covered | Django timeout conversion and expiration behavior |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__touch | integration | ### DjangoCache | covered | Django timeout conversion and expiration behavior |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__unicode | atomic | ### DjangoCache | covered | multi-key behavior covers set_many storage for unicode values |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__binary_string | atomic | ### DjangoCache | covered | multi-key behavior covers set_many storage for binary values |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__set_many | atomic | ### DjangoCache | covered | multi-key behavior: set_many stores every key/value pair |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__set_many_returns_empty_list_on_success | atomic | ### DjangoCache | covered | multi-key behavior: set_many returns empty list when all writes succeed |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__set_many_expiration | integration | ### DjangoCache | covered | multi-key behavior: set_many applies timeout conversion to every pair |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__delete_many | atomic | ### DjangoCache | covered | multi-key behavior: delete_many deletes requested keys and ignores missing keys |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__clear | atomic | ### DjangoCache | covered | Django-compatible public cache operations |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__long_timeout | integration | ### DjangoCache | covered | timeout conversion applies to set_many and long timeouts use backend semantics |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__forever_timeout | integration | ### DjangoCache | covered | timeout conversion applies to set_many and timeout=None stores without expiration |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__zero_timeout | integration | ### DjangoCache | covered | timeout conversion applies to set_many and timeout=0 stores already expired |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__float_timeout | integration | ### DjangoCache | covered | Django timeout conversion and expiration behavior |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__cache_versioning_get_set | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__cache_versioning_add | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__cache_versioning_has_key | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__cache_versioning_delete | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__cache_versioning_incr_decr | integration | ### DjangoCache | covered | Django key prefix/version isolation |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__cache_versioning_get_set_many | integration | ### DjangoCache | covered | key transform prefix/version/custom-key consistency applies to multi-key methods |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__incr_version | integration | ### DjangoCache | covered | version-changing methods move live values to incremented version and delete old key |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__decr_version | integration | ### DjangoCache | covered | version-changing methods move live values to decremented version and delete old key |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__custom_key_func | integration | ### DjangoCache | covered | key transform prefix/version/custom-key consistency isolates custom key functions |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__add_fail_on_pickleerror | atomic | ### DjangoCache | covered | serialization error propagation from add for unserializable values |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__set_fail_on_pickleerror | atomic | ### DjangoCache | covered | serialization error propagation from set for unserializable values |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__get_or_set | atomic | ### DjangoCache | covered | get_or_set stores and returns missing defaults including stored None values |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__get_or_set_callable | atomic | ### DjangoCache | covered | get_or_set evaluates callable defaults and stores the result |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__creates_cache_dir_if_nonexistent | integration | ### DjangoCache | covered | backend directory lifecycle behavior |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__clear_does_not_remove_cache_dir | integration | ### DjangoCache | covered | backend directory lifecycle behavior |
| oracle/test_atomic.py::TestDjangoCache::test_djangocache__cache_write_unpicklable_type | atomic | ### DjangoCache | covered | pickleable value storage behavior |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__read | integration | ### DjangoCache | covered | file-backed read support |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__expire | integration | ### DjangoCache | covered | DiskCache extension methods exposed by Django backend |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__evict | integration | ### DjangoCache | covered | DiskCache extension methods exposed by Django backend |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__pop | integration | ### DjangoCache | covered | DiskCache extension methods exposed by Django backend |
| oracle/test_integration.py::TestDjangoCache::test_djangocache__memoize | integration | ### DjangoCache | covered | DjangoCache memoize behavior |
| oracle/test_atomic.py::test_fanout__init | atomic | ### FanoutCache | covered | constructor/settings public attributes |
| oracle/test_atomic.py::test_fanout__init_path | atomic | ### FanoutCache | covered | constructor/settings public attributes |
| oracle/test_integration.py::test_fanout__set_get_delete | system_e2e | ### FanoutCache | covered | core fanout mapping workflow across shards |
| oracle/test_atomic.py::test_fanout__touch | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| oracle/test_atomic.py::test_fanout__add | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| oracle/test_integration.py::test_fanout__add_concurrent | system_e2e | ## Sharding Behavior | covered | public concurrent operations through fanout |
| oracle/test_integration.py::test_fanout__incr_concurrent | system_e2e | ## Sharding Behavior | covered | public concurrent operations through fanout |
| oracle/test_integration.py::test_fanout__getsetdel | system_e2e | ### FanoutCache | covered | core fanout mapping workflow across shards |
| oracle/test_atomic.py::test_fanout__pop | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| oracle/test_atomic.py::test_fanout__delitem | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| oracle/test_atomic.py::test_fanout__delitem_keyerror | atomic | ## Error Semantics | covered | public missing-key behavior |
| oracle/test_integration.py::test_fanout__tag_index | integration | ## Sharding Behavior | covered | aggregate tag index and eviction behavior |
| oracle/test_integration.py::test_fanout__read | integration | ### FanoutCache | covered | file-backed read behavior via FanoutCache |
| oracle/test_atomic.py::test_fanout__read_keyerror | atomic | ## Error Semantics | covered | public missing-key behavior |
| oracle/test_atomic.py::test_fanout__getitem_keyerror | atomic | ## Error Semantics | covered | public missing-key behavior |
| oracle/test_integration.py::test_fanout__expire | integration | ## Sharding Behavior | covered | aggregate expiration across shards |
| oracle/test_integration.py::test_fanout__evict | integration | ## Sharding Behavior | covered | aggregate tag index and eviction behavior |
| oracle/test_integration.py::test_fanout__size_limit_with_files | integration | ## Sharding Behavior | covered | size limit divided across shards |
| oracle/test_integration.py::test_fanout__size_limit_with_database | integration | ## Sharding Behavior | covered | size limit divided across shards |
| oracle/test_atomic.py::test_fanout__clear | atomic | ### FanoutCache | covered | public cache operation mirrors Cache |
| oracle/test_integration.py::test_fanout__stats | integration | ## Sharding Behavior | covered | aggregate stats across shards |
| oracle/test_atomic.py::test_fanout__iter | atomic | ## Sharding Behavior | covered | aggregate iteration views |
| oracle/test_integration.py::test_fanout__iter_expire | integration | ## Sharding Behavior | covered | aggregate expiration across shards |
| oracle/test_atomic.py::test_fanout__reversed | atomic | ## Sharding Behavior | covered | aggregate iteration views |
| oracle/test_integration.py::test_fanout__pickle | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or pickled fanout cache |
| oracle/test_integration.py::test_fanout__memoize | integration | ### FanoutCache | covered | fanout memoize behavior |
| oracle/test_integration.py::test_fanout__copy | system_e2e | ## Cross-View Invariants | covered | persistence across cache instances or pickled fanout cache |
| oracle/test_integration.py::test_index__init | system_e2e | ### Index | covered | persistent construction/pickle behavior |
| oracle/test_atomic.py::test_index__getsetdel | atomic | ### Index | covered | public mapping/order behavior |
| oracle/test_atomic.py::test_index__pop | atomic | ### Index | covered | public mapping/order behavior |
| oracle/test_atomic.py::test_index__pop_keyerror | atomic | ## Error Semantics | covered | public Index missing-key behavior |
| oracle/test_atomic.py::test_index__popitem | atomic | ### Index | covered | public mapping/order behavior |
| oracle/test_atomic.py::test_index__popitem_keyerror | atomic | ## Error Semantics | covered | public Index missing-key behavior |
| oracle/test_atomic.py::test_index__setdefault | atomic | ### Index | covered | public mapping/order behavior |
| oracle/test_atomic.py::test_index__iter | atomic | ### Index | covered | public mapping/order behavior |
| oracle/test_atomic.py::test_index__reversed | atomic | ### Index | covered | public mapping/order behavior |
| oracle/test_integration.py::test_index__state | system_e2e | ### Index | covered | persistent construction/pickle behavior |
| oracle/test_atomic.py::test_recipes__averager | atomic | ### Recipes | covered | public recipe behavior |
| oracle/test_integration.py::test_recipes__lock | system_e2e | ### Recipes | covered | recipe coordination across threads |
| oracle/test_integration.py::test_recipes__rlock | system_e2e | ### Recipes | covered | recipe coordination across threads |
| oracle/test_integration.py::test_recipes__semaphore | system_e2e | ### Recipes | covered | recipe coordination across threads |
| oracle/test_atomic.py::test_recipes__memoize_stampede | atomic | ### Recipes | covered | public recipe behavior |

