repo: diskcache
source_path: /Users/zijian/Bmk-dev-main/repo-pool/python-diskcache-master
commit: unknown (local candidate directory is readable but has no .git metadata)
src_loc: 4150
test_functions: 256
test_files: 7 test_*.py files: test_core.py, test_deque.py, test_djangocache.py, test_doctest.py, test_fanout.py, test_index.py, test_recipes.py
dominant_test_styles: pytest unit/integration tests over public Python APIs, Django TestCase coverage for DjangoCache, doctest checks for modules and docs/tutorial.rst; no snapshot/exact-output dominant pattern observed
public_docs: README.rst, docs/index.rst, docs/tutorial.rst, docs/api.rst, docs/cache-benchmarks.rst, docs/djangocache-benchmarks.rst, docs/development.rst
core_fact_source: durable disk-backed cache state stored in a cache directory with SQLite metadata plus file-backed value storage
derived_views: Cache mapping API, FanoutCache sharded API, DjangoCache backend API, Deque sequence API, Index mapping API, cache directory/file state, SQLite-backed settings/statistics/volume/check projections
external_deps: runtime install_requires is empty; tests require pytest, pytest-django, Django 4.2.*, pytest-xdist/coverage in tox; benchmark-only files reference redis, pylibmc, django_redis, sqlitedict, pickleDB and should remain ignored; rsync is used by copy/rsync tests and should be skipped or guarded if unavailable
test_import_audit: clean — grep -rn "from diskcache\._\|import diskcache\._" tests/ returned no matches, 0/7 test files affected
docs_test_alignment: aligned — official tutorial/API docs cover the same public Python API and DjangoCache surfaces exercised by most tests; later filtering should remove or rewrite assertions that inspect private attributes or call private helpers such as _disk, _sql, _shards, _cache, and Django request internals
contamination_note: diskcache@5.6.3, released unknown, relative to training cutoff: unknown
decision: keep
reason: Substantial pure-Python persistent cache library with durable SQLite/filesystem state, multiple documented public projections, a broad non-snapshot test suite, and clean module-level private-import pre-screen.
risks: Local candidate snapshot has no git metadata, so exact upstream commit is unavailable; some upstream tests touch private attributes/helpers and external tools such as rsync, so later filtering or benchmark-owned public verifier tests will be needed.
