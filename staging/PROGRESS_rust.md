# Rust Stage 1–3 packet production — progress

Worker branch: `cursor/8-26-50tasks-rust-a9d6`. Quota: 15 ACCEPTABLE Rust
Stage 1–3 task packets under `staging/{task_id}/`.

## Deliverable definition (Definition A)

Each packet contains:

- `spec.md` — candidate-visible 6-layer spec (internal header included in the
  staging copy; stripped only when a packet graduates).
- `oracle/` — Rust oracle workspace in the style of the existing Rust tasks
  under `tasks/` (rhai / comfy-table / toml / cargo-generate):
  `Cargo.toml` (workspace) + `Cargo.lock` + `atomic/` crate + `integration/`
  crate + `depends_on.json`, runnable by `harness/runners/rust.py` and
  `harness/score_language.py`.
- `filter/spec_test_map.md`, `filter/kept_nodeids.txt`, `filter/taxonomy.jsonl`,
  `filter/rewrite_audit.md`, `filter/lint_result.txt` (first line `LINT_PASS`,
  newer than every oracle test file), `filter/reference_score.json` (pinned
  reference at 100%).
- `task.json` with `language: "rust"`, `target_crates`, taxonomy, stats.
- `PIPELINE_STATE.md` (state machine instance, through `S3_DONE`).
- `filter_notes.md` (Stage 1 screening evidence).

`oracle/requirements.txt` is not part of the Rust convention: none of the four
merged Rust tasks under `tasks/` carries one, so it is omitted here.

## Infrastructure notes

- `harness/oracle_import_lint.py` gained a Rust branch: target roots come from
  `task.json.target_crates` (staging or tasks layout), every `use root::...`
  and inline `root::seg::Name` path in the oracle sources must name symbols
  the spec text declares, and each reached crate root must appear in the
  spec's Public Interface section. Verified against the merged Rust tasks:
  comfy-table passes; toml reports one genuine undeclared symbol
  (`from_iter`), confirming the check is not vacuous.
- Reference runs use `harness/score_language.py` with the pinned upstream
  checkout as `--solution-dir`; upstream checkouts live outside the repo tree
  (`/tmp/refs/`).
- Rust dummy-gate note: a stub crate whose public functions all
  `unimplemented!()` panics on first call, so any test that calls the target
  crate and asserts a produced value fails against it. The per-task filter
  notes record the static audit that every kept test calls the target crate
  and no `#[should_panic]` tests are kept.

## Repo bans (dupes of prior task sources on any branch)

rhai, comfy-table, toml-rs (toml/toml_edit/taplo), cargo-generate, gitoxide
(all gix-*), fjall/lsm-tree, sanakirja, guppy, egglog, pest.

## Task ledger

| # | task_id | repo | state | notes |
|---|---------|------|-------|-------|

(rows appended as tasks complete)
