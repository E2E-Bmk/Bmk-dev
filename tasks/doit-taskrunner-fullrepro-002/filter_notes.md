repo: pydoit__doit
source_path: G:\research\01_agents\swe-e2e\repo-pool\pydoit__doit
commit: 1f9cbbce78a93f96a35abf2db5425361e2abf142
src_loc: 5587
test_functions: 545
test_files: 34 Python test files under tests/
dominant_test_styles: unit/integration behavioral tests over task/action/dependency/runner/CLI command APIs; no snapshot/golden-test framework detected; some exact stdout/stderr and repr checks exist but are not dominant
public_docs: README.rst; doc/index.rst; doc/tutorial-1.rst; doc/tasks.rst; doc/dependencies.rst; doc/uptodate.rst; doc/cmd-run.rst; doc/cmd-other.rst; doc/configuration.rst; doc/extending.rst; doc/globals.rst; doc/tools.rst
core_fact_source: dodo task definitions plus dependency/result state stored in dep files/backends (dbm/json/sqlite), file dependencies, targets, task graph, action outputs, saved values/results, and execution status
derived_views: CLI commands (run/list/info/clean/forget/ignore/reset-dep/dumpdb/strace/help/completion); public Python entry points (doit.run, doit.api.run_tasks, ModuleTaskLoader, DoitMain); public task/action objects and dict task definitions; dependency DB backends and persisted dep/result files; generated target files and action stdout/stderr; reporter output including console/json-style projections; plugin/loader/reporter extension APIs
external_deps: Runtime dependencies are empty in pyproject.toml. Optional cloudpickle only affects multiprocessing pickling behavior and can be skipped or isolated; tomli is only for older Python TOML support. Tests use stdlib dbm/sqlite/subprocess/multiprocessing and skip strace on Windows or when unavailable. Isolation plan: keep generated dodo files, dep DBs, temp targets, subprocess helpers, and optional-backend tests in temp directories; filter OS-specific strace/dbm edge cases if not portable.
test_import_audit: clean - mandated grep for module-level `from doit._` or `import doit._` matched 0/34 test files (0%)
docs_test_alignment: aligned - official docs cover task dictionaries, actions, dependencies/uptodate/result state, dep DB backends, CLI commands, Python API entry points, loaders, plugins, reporters, globals, and tools; Stage 3 should filter or rewrite tests that assert undocumented runner/control internals, private attributes, or exact repr details
contamination_note: doit@0.38.0.dev0, released unreleased; commit date 2026-02-12 and latest released tag 0.37.0 on 2026-02-09, relative to training cutoff: after
decision: keep
reason: Meets Stage 1 hard gates with >3k LOC, broad documented behavior, durable task/dependency/run state, and multiple public projections across CLI, Python APIs, persisted DB/files, and reporter/output views.
risks: Stage 3 likely needs careful filtering because upstream tests include many direct imports of public-but-low-level modules (runner/control/cmd_base/dependency) and some exact stdout/repr/private-attribute assertions; Windows portability around dbm, multiprocessing, and strace must be handled.
