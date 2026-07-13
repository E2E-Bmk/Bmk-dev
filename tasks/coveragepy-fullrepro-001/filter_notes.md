repo: nedbat__coveragepy
source_path: G:\research\01_agents\swe-e2e\repo-pool\nedbat__coveragepy
commit: 787af5ff90e8a73bfd8cba7d5661b4930cc53ce5
src_loc: 12100 nonblank/noncomment Python LOC under coverage/*.py (excluding tests, docs, lab)
test_functions: 1152
test_files: 100 Python test files under tests/
dominant_test_styles: integration-heavy pytest suite with CLI/API data-file workflows, report generation assertions, configuration parsing, plugin behavior, and unit tests for parsing/report internals; many upstream tests inherit from tests.coveragetest.CoverageTest and use helper fixtures.
public_docs:
  - README.rst
  - doc/index.rst
  - doc/api.rst
  - doc/api_coverage.rst
  - doc/api_coveragedata.rst
  - doc/api_exceptions.rst
  - doc/commands/cmd_run.rst
  - doc/commands/cmd_report.rst
  - doc/commands/cmd_json.rst
  - doc/commands/cmd_html.rst
  - doc/commands/cmd_xml.rst
  - doc/commands/cmd_combine.rst
  - doc/config.rst
  - doc/branch.rst
  - doc/contexts.rst
  - doc/dbschema.rst
core_fact_source: coverage measurement data collected from executing Python programs and persisted in .coverage data files, including measured files, executable statements, executed lines, branch arcs, contexts, and configuration.
derived_views: public CLI commands (coverage run/report/json/html/xml/combine/debug/erase), Python API (coverage.Coverage and coverage.CoverageData), .coverage SQLite data file, text report totals, JSON/XML/HTML outputs, and configuration files.
external_deps: primarily Python stdlib plus pytest for tests; optional extras include toml/config parsing, greenlet/concurrency and plugins. Candidate task can be scoped to stdlib-local execution, file outputs, CLI/API/data/report behavior, and avoid external services.
test_import_audit: clean - 0/100 test files have module-level `from coverage._...` or `import coverage._...`; note that many tests import public-looking internal modules such as coverage.files, coverage.misc, coverage.sqldata and shared tests.* helpers, so Stage 3 must rewrite/filter aggressively and will likely trigger Track B.
docs_test_alignment: aligned - public docs cover the same major projection types exercised by tests: CLI execution, configuration files, data collection, Coverage/CoverageData API, reports, JSON/XML/HTML output, branch/context behavior, and data schema. Some upstream unit tests cover unsupported internals and should be excluded or replaced by generated behavioral tests.
contamination_note: nedbat__coveragepy@787af5ff90e8a73bfd8cba7d5661b4930cc53ce5, commit date 2026-06-28; relative to model training cutoff: after/unknown. Use source/docs only to construct benchmark artifacts, and ensure candidate packet contains public spec body only.
decision: keep
reason: coverage.py has durable measured execution state with multiple documented public projections across CLI, API, data files, and reports, large enough source/tests, clean private underscore pre-screen, and no mandatory network service.
risks: upstream tests rely on tests.coveragetest helpers and many public-looking but unsupported modules; exact report text/HTML snapshots and Python-version-specific tracing details must be filtered; C extension/tracing core and concurrency plugins may need to be non-goals or generated-only behavioral coverage.
