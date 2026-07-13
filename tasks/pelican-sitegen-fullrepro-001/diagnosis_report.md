# Diagnosis Report: pelican-sitegen-fullrepro-001

## Preflight output

Command:

```powershell
python -c "import pelican, os; print(pelican.__file__, flush=True); os._exit(0)"
```

Working directory:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-pelican-specv3-20260701-001\output
```

Literal output:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-pelican-specv3-20260701-001\output\pelican\__init__.py
```

## Verdict

QUALIFIED.

The public-carrier oracle is valid for Stage 5 judgment. The current run resolves `pelican` from the candidate output tree, the reference implementation passes the full public-carrier oracle, the carrier tests are public/spec-driven/behavioral, and the candidate failures are real model failures rather than verifier failures.

No pipeline state, oracle files, score files, candidate records, task package files, or weakness table were modified in this judge pass, per the user's route constraint. This report is the only written artifact.

## Artifact Status

- Pipeline state: `S5_JUDGE`, stage 5, `oracle_count: 56`, `filter_iter: 2`.
- Current scoring oracle: `20260704-public-carrier-v1`, 56 generated public-carrier nodeids in `kept_nodeids.txt`.
- Current candidate score file: `candidate-runs/codex-pelican-specv3-20260701-001/score_result.json`, identical summary to `score_result_public_carrier_wsl_20260704.json`.
- Superseded invalid score: `score_result_superseded_20260704_private_harness.json` records the retired private-harness run with 156 total tests, 11 passed, 120 failed, 8 errors, and 17 collection errors. It is not used for this verdict.

## Hard Checks

### Anti-Cheat

Pass. The mandatory import preflight resolves inside:

```text
G:\research\01_agents\swe-e2e\Bmk-dev\candidate-runs\codex-pelican-specv3-20260701-001\output
```

The candidate prompt contains the public spec and explicit prohibitions against inspecting the original source, tests, filter artifacts, score reports, or previous runs. A scan of the candidate implementation output found no references to `repo-pool`, `spec_test_map`, `kept_nodeids`, score artifacts, or `pelican.tests`. The candidate run directory still contains historical score-work material from the superseded private-harness evaluation, but those files are outside the candidate `output` implementation and are explicitly superseded by the public-carrier WSL score.

### Solvability

Pass. The reference run used the public carrier with scorer isolation (`remove_paths: ["pelican"]`) and passed 56/56. Layer totals:

| layer | reference passed | total |
|---|---:|---:|
| atomic | 29 | 29 |
| integration | 21 | 21 |
| system_e2e | 6 | 6 |

### Score Summary

Candidate score: 40/56 passed, 16 failed, 0 collection errors.

| layer | passed | failed | total |
|---|---:|---:|---:|
| atomic | 18 | 11 | 29 |
| integration | 20 | 1 | 21 |
| system_e2e | 2 | 4 | 6 |

## Fairness Gates

### Gate A: Spec Mapping Spot-Check

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `test_07_parse_arguments_decodes_json_extra_settings` | `-e` parses JSON string and boolean overrides into `args.overrides`. | `Settings` and `Command-Line Workflows` | derivable |
| `test_13_slugify_uses_regex_substitutions_for_url_parts` | `slugify` applies caller-supplied regex substitutions to URL parts. | `Readers` and `URL, Output, and Feed Rules` | derivable |
| `test_18_author_slug_url_and_save_path_agree` | Author wrapper exposes slug, URL, and save path from configured patterns. | `Content Objects` and `Cross-View Invariants` | derivable |
| `test_22_readers_read_markdown_content_and_metadata` | Markdown reader returns content-visible metadata and rendered body. | `Readers` and `Content and Metadata Behavior` | derivable |
| `test_38_static_link_renders_to_site_url` | Rendered `{static}` link agrees with `SITEURL` and copied static path. | `Links, Static Files, and Attachments` and `Cross-View Invariants` | derivable |
| `test_51_feed_entry_uses_same_article_title_as_page` | Feed entry title matches the generated article page title. | `Cross-View Invariants` | derivable |

The map quotes real headings from `spec_v3.md`. The sampled expected outcomes are inferable from those headings' body text and do not require private source knowledge.

### Gate B: Failure Pattern Audit

Pass. The failing tests check public API behavior and generated outputs:

- CLI parsing result or error type.
- Public utility signature/output.
- Public wrapper attributes (`slug`, `url`, `save_as`).
- Reader return contract visible to callers.
- Public paginator constructor/page behavior.
- Rendered links and generated feed files.

No sampled failure depends on private module structure, private helper names, exact repr formatting, exact exception message text, or internal field layout.

### Gate C: Generated Public-Carrier Spot-Check

The map header is `oracle_source: generated_public_carrier`, not the exact `generated_only` value named in the skill. Because every row's source is `generated`, I still sampled generated rows using the generated-only criteria.

| nodeid | assertion summary | spec_section | verdict |
|---|---|---|---|
| `test_04_read_settings_applies_explicit_override` | Explicit override wins in `read_settings`. | `Settings` | spec-driven, behavioral |
| `test_09_parse_arguments_rejects_missing_equals` | Invalid extra-setting syntax raises `ValueError`. | `Error Semantics` | spec-driven, behavioral |
| `test_24_public_signal_namespaces_share_generation_signal` | Package and plugin signal namespaces expose the same generation signal. | `Plugins and Signals` | spec-driven, behavioral |
| `test_30_generated_article_uses_configured_save_path` | Article output is written to configured `ARTICLE_SAVE_AS`. | `Site Generation` and `URL, Output, and Feed Rules` | spec-driven, behavioral |
| `test_42_hidden_article_is_not_listed_on_index` | Hidden article is output but excluded from index view. | `Content and Metadata Behavior` and `Cross-View Invariants` | spec-driven, behavioral |
| `test_56_cli_and_programmatic_settings_describe_same_site_name` | CLI and programmatic overrides agree for the same site name. | `Cross-View Invariants` | spec-driven, behavioral |

No circular or internal-shape row was found.

### Gate D: Coverage Gap Audit

Coverage verdict: PARTIAL, acceptable. All core invariant sections are covered, including `Error Semantics`, `Cross-View Invariants`, and the main state/output lifecycle sections (`Settings`, `Site Generation`, `Content and Metadata Behavior`, `URL, Output, and Feed Rules`, `Command-Line Workflows`). The uncovered headings are either non-behavioral framing sections or a behavior section whose static-link behavior is covered through mapped cross-view tests.

| spec section | uncovered behaviors | impact | recommendation |
|---|---|---|---|
| `Product Overview` | Framing section, no discrete assertion required. | none | no action |
| `Scope` | Framing section, no discrete assertion required. | none | no action |
| `Public API` | Parent heading; child H3 sections are covered. | none | no action |
| `Links, Static Files, and Attachments` | No row maps directly to this heading, though `{static}` link/copy behavior is tested under `Cross-View Invariants`. | low | future map cleanup could dual-map static-link rows here |
| `Representative Workflow` | Narrative example; its behaviors are covered by generation and cross-view rows. | none | no action |
| `Non-Goals` | Negative scope section. | none | no action |
| `Evaluation Notes` | Evaluation framing section. | none | no action |

## Real Failure Clusters

| cluster | affected tests | layer | dimension | diagnosis |
|---|---:|---|---|---|
| CLI `--extra-settings` accepts only one value per `-e` occurrence. | 2 | atomic | atomic-behavior | `parse_arguments` uses `action="append"` without allowing the trailing `KEY=VALUE` items that the spec requires, so later overrides are rejected as unknown arguments. |
| `slugify` public signature omits `regex_subs` and `preserve_case`. | 2 | atomic | api-surface | The candidate only accepts a settings dict and therefore rejects documented direct keyword options. |
| URL wrapper objects do not compute `url` and `save_as`. | 3 | atomic | cross-view-consistency | `Author`, `Category`, and `Tag` expose `slug` but not the configured URL/save-as projections required for object/template/generated-view agreement. |
| `Readers.read_file` returns a raw tuple rather than a content object. | 1 | atomic | api-surface | Public reader callers cannot access `.metadata` and `.content` as specified. |
| `Paginator` constructor and page API do not match public compatibility behavior. | 3 | atomic | api-surface | The implementation expects `(object_list, per_page, orphans)` instead of the public Pelican argument shape and also exposes `has_next`/`has_previous` as booleans rather than methods. |
| Static link rendering leaves the article link relative and escaped. | 1 | integration | cross-view-consistency | The static file is copied, but the rendered article body does not convert `{static}` Markdown links into a `SITEURL`-qualified href. |
| Feed output is incomplete/non-compatible. | 4 | system_e2e | workflow-completeness | The candidate writes an all-articles feed file, but its Atom XML lacks the expected namespace for entry discovery and it does not generate the configured category feed. |

Cascade analysis: 16 observed failures reduce to 7 root clusters. Most atomic failures are independent public API surface gaps. The four system failures share the feed-generation root, and the one integration failure is a separate static-link cross-view defect. This run provides both API-surface and cross-view/workflow signal rather than a collection-error cascade.

## Labels

- `discriminating`: the candidate passes many public behaviors but misses specific API and cross-view details.
- `public-carrier-repaired`: the retired private test-harness oracle has been replaced by public carrier tests.
- `api-surface-signal`: several failures are public signature/return-shape mismatches.
- `cross-view-consistency-signal`: static links and feed/article projections expose multi-view drift.
