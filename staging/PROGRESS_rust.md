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
| 1 | evalexpr-fullrepro-001 | ISibboI/evalexpr @ 92d99f4 (v13.1.0) | S3_DONE | 56 tests (29 atomic / 27 integration incl. 5 generated); reference 56/56; LINT_PASS |
| 2 | config-rs-fullrepro-001 | rust-cli/config-rs @ 532ab4d (v0.15.11) | S3_DONE | 82 tests (39 atomic / 43 integration incl. 14 generated); reference 82/82; LINT_PASS; Cargo.lock pins indexmap 2.7.1 / hashbrown 0.15.5 for rustc 1.83 |
| 3 | similar-fullrepro-001 | mitsuhiko/similar @ 28c146b (v2.7.0) | S3_DONE | 91 tests (64 atomic / 27 integration; 33 upstream-derived, 58 generated); reference 91/91; LINT_PASS; Cargo.lock pins unicode-segmentation 1.12.0 for rustc 1.83 |
| 4 | ropey-fullrepro-001 | cessen/ropey @ d41ee24 (v1.6.1) | S3_DONE | 91 tests (58 atomic / 33 integration; generated-only, upstream as checklist); reference 91/91 (patched path + registry lock); LINT_PASS; no dependency pins needed |
| 5 | fst-fullrepro-001 | BurntSushi/fst @ 5907b47 (v0.4.7) | S3_DONE | 105 tests (68 atomic / 37 integration; generated-only, upstream as checklist); reference 105/105; LINT_PASS; zero transitive deps |
| 6 | textwrap-fullrepro-001 | mgeisler/textwrap @ 4770e55 (v0.16.2) | S3_DONE | 111 tests (79 atomic / 32 integration; generated-only, upstream as checklist); reference 111/111 (patched + registry lock); LINT_PASS; smawk pinned =0.3.2 for cargo 1.83 |
| 7 | petgraph-fullrepro-001 | petgraph/petgraph @ 1629035 (v0.8.3) | S3_DONE | 129 tests (95 atomic / 34 integration; generated-only, upstream as checklist); reference 129/129 (patched + registry lock); LINT_PASS; indexmap pinned =2.7.1 for cargo 1.83 |
| 8 | ignore-fullrepro-001 | BurntSushi/ripgrep (crates/ignore) @ ac02f54 (ignore-0.4.23) | S3_DONE | 106 tests (75 atomic / 31 integration; generated-only, upstream as checklist); reference 106/106 (patched + registry lock); LINT_PASS; ignore =0.4.23 + globset =0.4.15 pinned for cargo 1.83 |
