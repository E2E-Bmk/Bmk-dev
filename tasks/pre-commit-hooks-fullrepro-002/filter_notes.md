repo: pre-commit__pre-commit
source_path: G:\research\01_agents\swe-e2e\repo-pool\pre-commit__pre-commit
commit: 1553b465fd7ea42321ae0d04d1b41e706b89ae45
src_loc: 5577
test_functions: 679
test_files: 59 Python test files under tests/
dominant_test_styles: unit and integration tests over CLI commands, YAML config/manifest validation, git repository state, hook installation, hook execution, cache/store behavior, and language runner workflows; not predominantly snapshot tests.
public_docs: README.md; command-line argparse surface in pre_commit/main.py; official user documentation referenced by README at https://pre-commit.com/ for Stage 2 public behavior derivation.
core_fact_source: a git working tree plus .pre-commit-config.yaml, .pre-commit-hooks.yaml manifests, installed git hook files, and pre-commit's cache/store directories.
derived_views: CLI command results and exit codes; config/manifest validation APIs; installed hook scripts in .git/hooks; git staged/all-file selections; repository cache/store state; hook execution output.
external_deps: git executable required; many language backends exist but can be isolated by focusing on local/system/python/meta hooks and avoiding network-bound language installation in Stage 3.
test_import_audit: clean - `rg "from pre_commit\._|import pre_commit\._" tests` returned no matches; 0/59 test files import private pre_commit modules at module level.
docs_test_alignment: aligned with risk - public docs and CLI/config surfaces cover the same user-facing projections as many tests, but Stage 3 must rewrite tests that rely on repository-local `testing.*` fixtures and avoid language backends requiring external tools or network.
contamination_note: pre-commit__pre-commit@1553b465fd7ea42321ae0d04d1b41e706b89ae45, committed 2026-05-19, relative to training cutoff: after.
decision: keep
reason: pre-commit has durable git/config/cache state with multiple public projections across CLI, config validation, hook files, git state, and hook execution, while passing LOC and private-import hard gates.
risks: tests use repository-local `testing.*` helpers heavily; some language runner tests require external runtimes or network and should be excluded or rewritten; official detailed docs may need to be fetched from pre-commit.com during Stage 2 and checked against this commit.
