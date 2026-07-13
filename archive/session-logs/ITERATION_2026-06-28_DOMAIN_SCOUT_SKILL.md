# Domain Scout Skill Iteration

Date: 2026-06-28

## Why This Iteration Happened

The loop stalled because later mini-product tasks were being enriched after no-gap evidence instead of being rejected earlier. The first accepted tasks, SQLite, ZK, and MiniURLUtils, have durable product state with several public projections that can drift. Many later tasks collapse to one obvious typed store, config tree, token tree, dependency graph, template environment, or append log.

## Skill Changes

Created:

- `C:\Users\12547\.codex\skills\gap-domain-scout\SKILL.md`
- `C:\Users\12547\.codex\skills\gap-domain-scout\agents\openai.yaml`

Updated:

- `C:\Users\12547\.codex\skills\gap-benchmark-iteration\SKILL.md`
- `C:\Users\12547\.codex\skills\gap-opportunity-auditor\SKILL.md`
- `C:\Users\12547\.codex\skills\gap-fairness-judge\SKILL.md`

The new workflow adds a pre-PRD domain gate and an explicit residual-gap gate:

- run `$gap-domain-scout` before building or materially rescoping a task;
- reject domains that fail the obvious-architecture or one-shot recomputation tests;
- treat raw `unit - system` as a judging trigger only;
- accept a gap only if at least 15pp remains after clustering primitive, cascade, evaluator, completion/provider, contaminated, and narrow-metadata roots.

## Validation

`quick_validate.py` could not run because the local skill-creator Python environment lacks `PyYAML`:

`ModuleNotFoundError: No module named 'yaml'`

A fallback structural check confirmed the edited skill files have frontmatter, names, descriptions, no TODO placeholders, and the new skill has `agents/openai.yaml`.

## Forward-Test Subagents

Two read-only explorer subagents were launched with the new skill and raw benchmark artifacts only.

### Current Candidate Audit

Verdicts:

- `MiniRedis`: reject current surface; one typed store solves after parser/glob/arity cascades are moved out.
- `MiniKV`: solved-audit/provenance repair; one typed namespace plus persistence replay solves current system.
- `MiniTemplate`: solved-audit/retire; shared environment/parser-render architecture is obvious and solved.
- `MiniDynaconf`: build only with fresh-run requirement; design has real lifecycle potential, but old scores are primitive-cascade capped.
- `MiniPackaging`: materially rescope; active resolver rows are one dependency graph with direct projections, while `MetadataIndex` lifecycle is not covered.
- `MiniMarkdown`: materially rescope only beyond workspace-v4; current workspace surface is near-solved below gate.
- `MiniBitcask`: solved-audit/retire; append log plus replay/keydir solves current public lifecycle.

### Next-Domain Scout

Most promising directions:

- `MiniPackaging` material rescope to `MetadataIndex + lock lifecycle`.
- SQLite/Alembic-style migration manager.
- DVC-like data pipeline workspace.
- Maildir/notmuch-like local mail index.
- Incremental build cache system, if cache/artifact lifecycle is public.
- Calendar recurrence store only with a tightly bounded recurrence subset.

## Next Action

Proceed with MiniPackaging first because it is already built, has a clear gap in current coverage, and both scouts independently identified `MetadataIndex + lock lifecycle` as the highest-confidence material rescope. Do not add more resolver-only rows.
