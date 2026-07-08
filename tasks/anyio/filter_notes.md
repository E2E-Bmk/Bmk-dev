repo: anyio
source_path: /Users/zijian/bench/repo-pool/anyio-master/
commit: unknown (local tree is not a git checkout)
src_loc: 15453 raw Python LOC under src/anyio
test_functions: 257
test_files: 27 test*.py files
dominant_test_styles: unit/integration behavioral pytest tests across async backends; local socket/process/thread/file/TLS integration; pytest-plugin self-tests; limited exact-value assertions but no snapshot/golden-file dominance
public_docs: README.rst; docs/index.rst; docs/api.rst; docs/basics.rst; docs/tasks.rst; docs/cancellation.rst; docs/synchronization.rst; docs/streams.rst; docs/networking.rst; docs/threads.rst; docs/subprocesses.rst; docs/fileio.rst; docs/tempfile.rst; docs/testing.rst; docs/versionhistory.rst
core_fact_source: public async runtime/resource state: event-loop backend selection, task groups/cancel scopes/deadlines, stream buffers/statistics, socket/process/file resources, worker thread/process/interpreter limiters, and pytest plugin backend fixture state
derived_views: Python public API return values and exceptions; public ABC/extra-attribute/statistics objects; filesystem effects from async file and tempfile APIs; subprocess stdout/stderr/exit status; socket/TLS stream behavior; pytest plugin collection/execution outcomes
external_deps: trio optional backend, pytest/pytest-mock/hypothesis/trustme/truststore/psutil/blockbuster, uvloop/winloop platform extras; isolate by running local-only tests, skipping 4 @pytest.mark.network cases, mocking DNS/socket where needed, and filtering platform/backend-specific subprocess/thread/TLS cases in Stage 3
test_import_audit: clean — required grep found 6 total private-import matches; module-level private imports in 2/27 test files (7.4%) plus tests/conftest.py, below the 30% HIGH_RISK threshold
docs_test_alignment: aligned — public docs and API reference cover the same Python API, stream, networking, subprocess, file/tempfile, task/cancellation, threading, and pytest-plugin projections exercised by most tests
contamination_note: anyio@unreleased local master, released unknown, relative to training cutoff: unknown
decision: keep
reason: Large documented public async framework with multiple public projections over shared runtime/resource state and a low module-level private import rate.
risks: Local candidate tree has no git commit metadata; release date/version relation is unknown; several tests are platform/backend/timing/network sensitive; Stage 3 must filter or rewrite private backend/eventloop imports, exact scheduler/introspection assumptions, network-marked tests, and tests requiring optional Trio/uvloop/winloop or subprocess/TLS environment details.
