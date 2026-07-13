# Invariant Skill Iteration Report

Date: 2026-06-27

## New Skills

Created and validated:

- `C:\Users\12547\.codex\skills\gap-invariant-task-builder`
- `C:\Users\12547\.codex\skills\gap-fairness-judge`

Both skills pass `quick_validate.py` after installing `PyYAML` into the bundled Codex Python runtime.

The task-builder skill encodes the shared-fact-source rule: system tests should assert cross-component invariants over multiple derived views, not repeat feature checklists.

The judge skill encodes the failure taxonomy: feature, cascade, compositional, evaluator defect, hack, and solved.

## Tooling Change

Updated `tools/generate_deepseek_candidate.py` so direct DeepSeek generation can target:

- `minidynaconf-realrepo-001`
- `minimarkdown-realrepo-001`
- `minipackaging-realrepo-001`

This is only a utility expansion. Formal DeepSeek evidence should still use the OpenHands agent loop, not direct completion.

## MiniDynaconf Redesign

Subagent: task-builder worker.

Changed:

- `task/minidynaconf-realrepo-001/prd.md`
- `task/minidynaconf-realrepo-001/rubric.json`
- `task/minidynaconf-realrepo-001/doc/requirement_map.md`

Scoring after redesign:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| existing Codex subagent | 100.00% | 100.00% | 0.00pp |
| existing OpenHands DeepSeek | 38.89% | 0.00% | 38.89pp |

Judge verdict: `solved` for Codex. OpenHands has a large numeric gap, but it is dominated by feature/cascade roots: PathLike normalization, nested attribute projection, casting, and validator snapshot behavior.

Conclusion: fair invariant redesign, but not accepted as a Codex gap task. Treat as solved for the current Codex population unless the task is materially enriched.

## MiniMarkdown Redesign

Subagent: task-builder worker.

Changed:

- `task/minimarkdown-realrepo-001/prd.md`
- `task/minimarkdown-realrepo-001/rubric.json`
- `task/minimarkdown-realrepo-001/doc/requirement_map.md`
- `runs/minimarkdown-realrepo-001/solution-reference/minimarkdown.py`

Main-thread fixes:

- Fixed malformed multi-line Python strings in system rubric cases.
- Added reference support for heading `attrs["id"]`, HTML heading ids, and `Markdown.toc()`.

Scoring after fixes:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| existing Codex subagent | 38.89% | 33.33% | 5.56pp |
| existing OpenHands DeepSeek | 22.22% | 16.67% | 5.56pp |

Judge verdict: `revise`. The task is not solved, but the observed failures are mostly feature/cascade and evaluator-shape risks rather than clean compositional gap.

Key risks:

- `Markdown(...).renderer` is a private-shape-ish expectation unless public packet states it.
- Canonical token names are heavily scored; the packet should enumerate names or rubrics should use semantic checks.
- System tests crash early on missing primitive shapes, obscuring real composition.

Conclusion: revise unit/schema contract and then add system cases that fire after primitives pass, especially TOC/AST/HTML consistency, plugin dispatch across renderers, table boundary ordering, and parser reuse.

## MiniPackaging Status

Subagent: task-builder worker revised the owned task files and reported that the reference gate was restored to 100/100.

Changed:

- `task/minipackaging-realrepo-001/prd.md`
- `task/minipackaging-realrepo-001/rubric.json`
- `task/minipackaging-realrepo-001/doc/requirement_map.md`

The worker avoided adding a new public `resolve_dependencies` API after an interim reference-gate failure. Dependency-resolution-style checks are now expressed as metadata projections over existing public APIs.

Main-thread scoring after redesign:

| Implementation | Unit | System | Gap |
|---|---:|---:|---:|
| reference | 100.00% | 100.00% | 0.00pp |
| existing Codex subagent | 83.33% | 83.33% | 0.00pp |
| existing OpenHands DeepSeek | 72.22% | 75.00% | -2.78pp |

Judge verdict: reject as gap evidence. Failures are mostly feature-level or formatting cascades, and the system score is equal to or higher than unit score.

Key issue: several system cases fail because `Requirement.__str__` includes non-canonical whitespace even when semantic resolver projections, selected versions, dependency edges, and permutation invariance are correct.

Conclusion: revise before any acceptance. Split semantic resolver/projection assertions from canonical serialization assertions; keep canonical string checks in unit or narrowly labeled serialization cases.

## Current Lessons

1. The new invariant-construction skill successfully pushes tasks toward shared fact sources and derived views.
2. Invariant-shaped tests alone are not sufficient. Strong Codex can fully solve compact coherent tasks, as with MiniDynaconf.
3. Parser tasks easily collapse into token-schema traps. MiniMarkdown needs either explicit token naming in the public packet or more semantic hidden checks.
4. Resolver tasks can accidentally count string serialization defects as system failures. MiniPackaging needs semantic comparisons for resolver/projection invariants.
5. Numeric gap is not enough. OpenHands Dynaconf has 38.89pp, but judge classifies it as cascade/feature failure.
6. Next iteration should prioritize either materially harder shared-state domains or deeper lifecycle workflows where a correct solution requires nontrivial independent projections that cannot be implemented as a compact direct model.

## Next Loop

- Apply judge feedback to MiniMarkdown and MiniPackaging.
- For any candidate with reference 100/100, run a fresh Codex subagent and, if available, a fresh OpenHands DeepSeek agent loop before accepting or marking solved.
