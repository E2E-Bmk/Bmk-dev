repo: jrnl-org/jrnl
source_path: G:\research\01_agents\swe-e2e\repo-pool\jrnl-org__jrnl
commit: 93e19d9541149c72c12537c09c9bf95623f286a4
src_loc: 4168
test_functions: 303 behavioral cases (78 pytest unit test functions + 225 pytest-bdd scenarios)
test_files: 35 spec files (13 tests/unit/test_*.py, 1 tests/bdd/test_features.py, 21 tests/bdd/features/*.feature); 22 Python test/support files including helpers
dominant_test_styles: pytest unit tests plus pytest-bdd CLI/integration scenarios; behavior-heavy exact CLI/file-output assertions, not snapshot-golden dominated
public_docs: README.md; docs/overview.md; docs/usage.md; docs/reference-command-line.md; docs/reference-config-file.md; docs/journal-types.md; docs/formats.md; docs/encryption.md; docs/advanced.md; docs/external-editors.md; docs/tips-and-tricks.md
core_fact_source: durable journal entries and configuration stored as local files/folders, including single-file journals, folder journals, DayOne Classic folders, encrypted journal files, templates, and exported data files
derived_views: jrnl CLI read/write/search/edit/delete/change-time/import/encrypt/decrypt/list surfaces; on-disk journal/config/template/export files; public documented formats including pretty, short, JSON, Markdown, text, XML, YAML, tags, and date reports; package-level public journal/exporter/importer objects exposed by jrnl.journals and jrnl.plugins
external_deps: runtime dependencies are local Python libraries (colorama, cryptography, keyring, parsedatetime, python-dateutil, pyxdg, ruamel.yaml, rich, tzlocal); isolation plan is install from lock/pyproject, use fixture-provided/mocked keyring backends, keep subprocess editor calls mocked in tests, avoid docs-only npx/pa11y tasks, and use local filesystem fixtures with no mandatory external network
test_import_audit: clean - mandated grep for module-level "from jrnl._" or "import jrnl._" matched 0/22 Python test/support files (0%). Additional non-blocking note: 3/22 files (13.6%) import underscore-named symbols from non-underscore modules.
docs_test_alignment: aligned - official docs cover the dominant CLI/config/journal-file/search/export/encryption projections exercised by the BDD suite; some upstream unit tests touch internal helper symbols and should be filtered or rewritten in Stage 3 rather than used as spec authority
contamination_note: jrnl@v4.3, released 2026-02-24 from local git tag v4.3, relative to training cutoff: after
decision: keep
reason: jrnl is a durable file-backed CLI application with documented behavior across writing, searching, configuration, journal storage types, encryption, and multiple export views, giving enough public evidence for a fair reconstruction task.
risks: A minority of unit tests exercise internal helper functions or exact terminal phrasing; keyring/encryption/editor behavior needs controlled fixtures; release is post-cutoff but public docs/changelog are available; Stage 3 should prefer BDD/public CLI-file projections and filter or rewrite internal-helper unit tests.
