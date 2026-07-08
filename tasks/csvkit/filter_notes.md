repo: csvkit
source_path: /Users/zijian/Bmk-dev-main/repo-pool/csvkit-master
commit: unknown (local candidate copy is not a git checkout; no .git metadata under repo-pool/csvkit-master)
src_loc: 3485 physical Python source lines under csvkit/ across 23 files (2684 nonblank/noncomment; borderline if strict SLOC is used)
test_functions: 321 AST-discovered test methods/functions under tests/ (311 in test_*.py modules; includes shared mixin definitions and performance.py)
test_files: 23 Python files under tests/; 18 test_*.py modules; 20 files define test functions
dominant_test_styles: unittest-style CLI utility tests instantiated through CSVKitTestCase; exact CSV/JSON/SQL/markdown output comparisons; small unit tests for helper functions; local SQLite integration
public_docs: README.rst; docs/index.rst; docs/cli.rst; docs/common_arguments.rst; docs/tutorial/*.rst; docs/scripts/*.rst; man/*.1; CHANGELOG.rst
core_fact_source: tabular rows, columns, schemas, inferred types, and dialect options from local CSV/TSV/XLS/XLSX/JSON/NDJSON/DBF/fixed-width inputs plus optional SQLAlchemy/SQLite tables
derived_views: CLI stdout CSV transformations via in2csv/csvcut/csvgrep/csvsort/csvjoin/csvstack/csvclean/csvformat; JSON/GeoJSON via csvjson; SQL DDL/query CSV via csvsql/sql2csv; Markdown-like tables via csvlook; statistics via csvstat; legacy csvkit reader/writer facade over agate
external_deps: agate, agate-excel, agate-dbf, agate-sql, openpyxl, SQLAlchemy, xlrd; optional zstandard; tests use local files and SQLite, no mandatory external services; docs/examples mention GitHub/PostgreSQL but those paths can be omitted or isolated
test_import_audit: clean - skill grep `from csvkit\._\|import csvkit\._` over tests/ found 0 matches; 0/23 test Python files and 0/18 test_*.py modules affected (0%)
docs_test_alignment: aligned with concerns - official docs cover the CLI projection and most existing tests exercise those CLI semantics via public utility classes; mismatch risk remains for helper tests importing csvkit.cli, csvkit.cleanup, csvkit.grep, and csvkit.convert.fixed without API reference docs
contamination_note: csvkit@2.2.0, released December 15, 2025 per CHANGELOG.rst, relative to training cutoff: after; exact commit hash unavailable locally
decision: keep
reason: Passes Stage 1 hard gates on physical Python LOC, public CLI documentation, multi-projection tabular behavior, local-only tests, and clean private-import audit.
risks: Physical LOC is only 485 lines above the 3000-line threshold and strict nonblank/noncomment SLOC would be 2684; 191/311 test_*.py test methods (61.4%) are exact-output style; current tests instantiate utility classes and include small undocumented helper APIs, so later stages should derive verifier coverage from public CLI/docs instead of retaining private-ish helper expectations wholesale; local source copy lacks commit metadata.

hard_gate_audit:
- LOC: pass by physical Python source LOC (3485), but borderline by stricter nonblank/noncomment count (2684).
- single_file_implementable: pass - 23 package modules and 14 console entry points cover conversions, SQL, statistics, formatting, and shared CLI parsing; collapsing into one file would not preserve the public module/entrypoint packet.
- shared_fact_source_public_projections: pass - one tabular-data fact source is projected as normalized CSV, filtered/sorted/joined/stacked CSV, JSON/GeoJSON, SQL DDL/query output, Markdown-like tables, and statistics.
- test_suite_risk: pass with risk - suite is present and local; exact-output-like tests are about 61.4% of test_*.py methods, below the 70% hard rejection line.
- closed_standard_or_high_saturation: pass with risk - CSV parsing itself is common and delegated to agate/Python csv, but csvkit combines multiple documented transformations and formats beyond a single closed-standard reimplementation.
- private_implementation_dependency: pass with concern - no underscore-private csvkit imports; some public-path helper imports are undocumented.
- docs_test_projection_match: pass with concern - docs cover CLI behavior that dominates the tests, but a minority of helper/API unit tests are not directly traceable to docs.

soft_gate_audit:
- durable_state: partial - local input/output file trees and SQLite database files are used; no long-lived application state.
- multiple_surfaces: positive - many public CLI tools and output projections over the same tabular facts; Python API docs are weak.
- documentation_coverage: positive for CLI/reference/tutorial/man pages; weak for helper APIs.
- external_services: positive - no mandatory external service; SQLite/file-based tests are local, while PostgreSQL/GitHub examples are optional/documentation-only.
- public_api_tests: positive with concern - module-level imports use non-underscore csvkit paths, but helper-level assertions should be reviewed before retaining.
