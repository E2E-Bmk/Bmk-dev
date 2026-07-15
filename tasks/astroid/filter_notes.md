repo: astroid
source_path: /Users/zijian/bench/repo-pool/astroid-main/
commit: unknown - candidate directory is not a git repository
src_loc: 30479 raw Python LOC under astroid/*.py
test_functions: 1605 pytest test functions/methods by `rg "^\s*(async\s+)?def test_" tests | wc -l`
test_files: 63 test*.py files under tests/
dominant_test_styles: unit/API behavior tests over parsing, inference, nodes, managers, transforms, brains, and helpers; some integration/file-system tests over testdata imports; 4 benchmark tests clone external primer repos and should be excluded or regenerated; not snapshot/exact-output dominated.
public_docs: README.rst; doc/index.rst; doc/inference.rst; doc/extending.rst; doc/api/index.rst; doc/api/general.rst; doc/api/astroid.nodes.rst; doc/api/base_nodes.rst; doc/api/astroid.exceptions.rst; doc/changelog.rst
core_fact_source: Python source text and imported modules are built into astroid's public node graph/inference model, with AstroidManager cache/import state as the shared analysis state.
derived_views: public Python API (`astroid.parse`, `extract_node`, `MANAGER`, node lookup/infer/as_string/repr_tree APIs); CLI projection (`python -m astroid ast FILE` prints `repr_tree()`); import/file projections via `AstroidManager.ast_from_file` and testdata package/module resolution; documented node and exception API surfaces.
external_deps: Runtime dependency is only `typing-extensions>=4` on Python < 3.11; test/dev deps include pytest, coverage, mypy, pylint, attrs, numpy, python-dateutil, PyQt6, regex, setuptools<82, six, urllib3, pytest-benchmark/codspeed-style benchmark fixture. Isolation plan: retain pure local API/import tests first; drop or rewrite `tests/benchmarks/test_bench_endtoend.py` because it performs `git clone` of Flask/Black; filter optional GUI/numpy/dateutil tests unless dependencies are installed locally.
test_import_audit: clean - required command `grep -rn "from astroid\._\|import astroid\._" tests/` returned 0 matches, so 0/63 test files affected (0%). Broader internal-symbol risk exists in about 11/63 files via imports such as `_extract_single_node`, `_filter_stmts`, `astroid.interpreter._import`, and private brain/node helpers.
docs_test_alignment: aligned - public docs cover the same API projection families tested by the suite: parsing, inference, nodes, transforms/extenders, manager-backed imports, and documented node/exception classes; Stage 3 must still remove tests that assert private helper or implementation-only semantics.
contamination_note: astroid@4.2.0b4, released TBA/unreleased in local ChangeLog, relative to training cutoff: after/unknown (local snapshot dated 2026-07 with unreleased 4.2.0 ChangeLog)
decision: keep
reason: Large documented static-analysis library with shared AST/inference facts exposed through public API, CLI, node renderings, file/import manager behavior, and a broad mostly local behavioral test suite.
risks: No git commit provenance in candidate directory; source appears unreleased/TBA; some upstream tests import private helpers or internal modules and will need Stage 3 filtering/rewrite; benchmark tests are network-bound; optional dependency/platform tests (PyQt6, numpy, dateutil, regex, pylint subprocess) need isolation.
