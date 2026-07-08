# SQLFluff Stage 3 Rework Notes

Stage 5 Gate C failed because several generated-only tests asserted reference implementation shape rather than public behavior. This rework keeps the oracle generated-only and does not patch the spec.

Changes made:

- Dialect metadata tests no longer assert exact display names, root inheritance sentinels, or expanded dialect object `.name` values. They now check documented tuple fields, label presence/sorting, readout consistency, and selector acceptance.
- Parse tests no longer require the exact `file.statement.select_statement.select_clause.keyword` path. They check successful parse, serializable nonempty output, CLI `filepath`, non-null `segments`, and observable SQL text content.
- Lexer coverage no longer requires a minimum segment count. It checks no lexing violations and downstream parseability.
- Render tests no longer assert `RenderedFile.templated_variants` or variant `.templated_str`. Jinja, Python, and placeholder coverage now uses public CLI render output.
- CLI render no longer requires an exact decorative trailing blank line; it checks rendered SQL content after trailing newlines are removed.
- The pyproject TOML rule-section test no longer checks intermediate config dictionary flattening. It verifies the observable linting effect of `[tool.sqlfluff.core]` plus `[tool.sqlfluff.rules.capitalisation.keywords]`.

No Stage 2 spec patch is recommended. The remaining behaviors are testable through public API/CLI effects without expanding the public contract.

Regenerated artifacts before graduation; the final task artifacts live under `tasks/sqlfluff/`.

Verification:

- Reference gate: `PYTHONPATH=repo-pool/sqlfluff-main/src:candidate-runs/gpt-5.5-sqlfluff-spec_v1-20260701-run1/score_shims python -m pytest -q tasks/sqlfluff/generated_tests.py` -> `40 passed, 1 warning`.
- Dummy gate: `PYTHONPATH=/tmp/sqlfluff_dummy_pkg python -m pytest -q tasks/sqlfluff/generated_tests.py` -> `40 failed, 1 warning`.
- Scorer reference gate: `harness/score_pytest_original.py` with `kept_nodeids.txt` and `taxonomy.jsonl` -> `40 passed / 40 total`, with layer counts atomic 17, integration 18, system_e2e 5.
- `kept_nodeids.txt`: 40 tests.
- `taxonomy.jsonl`: atomic 17, integration 18, system_e2e 5; no unknown layer.
- Covered-row forbidden-pattern scan: no hits for the Stage 5 implementation-shape patterns.
