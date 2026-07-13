# Source Repo Task Builder

Use this skill when constructing a new SWE-E2E task from a real repository,
ProgramBench case, PRDBench case, NL2RepoBench case, or newly found GitHub
repository.

## Goal

Create a fair, isolated, executable task where the candidate agent reconstructs
a complete multi-file project from a public packet, while hidden scoring uses
filtered original tests or deterministic executable rubrics.

## Gate 0: Candidate Fit

Reject or defer candidates that fail these checks:

- Source scale is too small to force project structure, or too large for a
  bounded first pass. Preferred source scale is roughly 3k-20k LOC.
  The first pilot task may be below 3k LOC only to validate the end-to-end
  workflow, but it must still be multi-file and backed by original tests.
- The task can be implemented as one Python file without violating the public
  packet.
- There is no shared fact source with multiple derived views.
- Original tests are absent, unclear, network-bound, or mostly snapshot-only.
- The core behavior is a closed standard or common parser/formatter where a
  strong model can pattern-match the implementation.
- The evaluator would need private implementation details.

Positive signals:

- Durable state, file trees, databases, event logs, templates, indexes, caches,
  or workflow histories.
- Multiple public surfaces over the same facts: CLI, API, export, reports,
  logs, search, graph, stats, or generated artifacts.
- Clear docs, examples, and tests that can be traced to public behavior.
- No mandatory external services; network calls can be mocked or removed.

## Gate 1: Evidence Record

Create `wip/{task}/filter_notes.md` with:

- Source path or URL.
- Commit hash.
- Source LOC and file count.
- Test count, test file list, and dominant test styles.
- Public docs used for the packet.
- Core fact source.
- Derived views to be tested.
- External dependencies and how they will be isolated.
- Initial keep/drop decision.

## Public Packet Rules

The public packet should include:

- Product purpose and target user.
- Required project/package shape.
- Public CLI/API/file contracts.
- Representative examples.
- Behavioral principles and invariants.
- Compatibility boundaries and non-goals.
- Evaluation style, without hidden fixtures or exhaustive checklist tests.

Do not include source architecture, hidden test names, exact fixture values, or
implementation algorithms.

## Oracle Rules

Use original tests where possible, but filter them:

- Keep tests whose expectations are inferable from the public packet or normal
  product behavior.
- Drop private implementation inspections.
- Drop network, platform, editor, shell, or permission assumptions unless the
  harness can make them deterministic.
- Replace brittle exact output checks with structured assertions when the public
  contract does not promise exact formatting.
- Report repeated root causes separately from raw score.

## Candidate Isolation

Candidate-visible materials should contain only:

- `spec.md` or `public_packet.md`
- starter files if intentionally public
- dependency constraints
- output directory instructions

Candidate-visible materials must not contain:

- source repository
- hidden tests
- score reports
- previous model attempts
- trace logs
- oracle fixtures not described in the public packet

## Baseline Runs

Do not promote a task using only weak-model or single-harness evidence.

Required candidate runs:

- weak/contrast baseline: Qwen via OpenHands or mini-swe-agent;
- middle strong baseline: DeepSeek V4 via OpenHands or mini-swe-agent;
- SOTA baseline: a fresh Codex subagent in a clean candidate workspace.

The Codex subagent run is a required acceptance check, not an optional sanity
test. If Codex scores above 80% after fairness audit, mark the task
`too_direct_for_sota` unless the research target explicitly excludes SOTA
agents. If Codex lands in 40-70%, inspect whether failures are independent or
one repeated root before promotion.

## Remote Working Layout

Preferred remote root:

```text
/root/autodl-tmp/swe-e2e/
  Bmk-dev/
  benchmarks/
  repo-pool/
  runs/
```

Clone benchmark repositories and source repositories on the remote machine
instead of transferring large local pools.
