# All-Branch Requirements And Tone Audit

## Scope

This audit covers the cached GitHub branch family and the current submitted
branch:

- `origin/main`
- `origin/repo_status`
- `origin/sync-from-release-and-fix-gates`
- `origin/codex/transitions-fullrepro-001`
- `origin/upload/native-batch-16-20260720`
- `origin/LiandZhang`
- `origin/beta`
- `LiandZhang50-artifact-only`

The 21 task trees shared by `LiandZhang` and the upload branch are not treated
as independent quality evidence. The comparison uses `sync-from-release-and-fix-gates`
as the current normative reference, while recording historical conventions
separately.

## Rule Authority

The repository contains three overlapping rule generations:

| Rule generation | Representative branches | Skill path | Meaning |
|---|---|---|---|
| Current normative | `main`, `repo_status`, `sync` | `dev/skills/` | Current constitution, spec, oracle and acceptance documents |
| Historical task branch | `codex`, `upload`, `LiandZhang` | `skills/` | Older packet and qualification workflow |
| Legacy active-workbench | `beta` | `skills/` | Older `MANIFEST.json` and workflow-first process |

`main` itself is not fully internally consistent: its README refers to root
`skills/` while active skills are under `dev/skills/`, and its documents discuss
both top-level and nested oracle layouts. The sync branch is the clearest current
interpretation because it removes the duplicate oracle tree and its
`QUALITY_GATE.md` matches the nested packet used by the current 50.

## Branch Composition

| Branch | Tasks | Metadata carrier | Oracle layout | Skill root | Normative docs | Status voice |
|---|---:|---|---|---|---|---|
| `main` | 61 | `task.json` | mixed root/nested | `dev/skills` | 5/5 | mixed `QUALIFIED`, `REOPENED_S3`, `REVALIDATION-REQUIRED` |
| `repo_status` | 61 | `task.json` | mixed root/nested | `dev/skills` | 5/5 | same mixed status vocabulary |
| `sync` | 60 | `task.json` | nested `tasks/<id>/oracle` | `dev/skills` | 5/5 | explicit status versus static-gate distinction |
| `codex` | 34 | `task.json` | nested packet | `skills` | 0/5 | mostly definitive `QUALIFIED` language |
| `upload` | 70 | `task.json` | nested packet | `skills` | 0/5 | mostly definitive `QUALIFIED` language |
| `LiandZhang` | 21 | `task.json` | nested packet | `skills` | 0/5 | all 21 `QUALIFIED` |
| `beta` | 11 | legacy `MANIFEST.json` | legacy packet | `skills` | 0/5 | process/workbench language; task status often absent |
| current 50 | 50 | `task.json` + upload manifest | nested packet | `dev/skills` | 5/5 | explicit `ARTIFACT_ONLY` and blocker language |

### Common Logical Packet

The current logical Gate 0 packet is:

```text
spec.md
task.json
oracle/test_atomic.py
oracle/test_integration.py
oracle/requirements.txt
```

The current 50 contain this set in `50/50`. The sync branch contains it in
`60/60`. Historical branches do not share the same physical layout: `main` and
`repo_status` mix top-level and nested oracle trees, `codex` and upload use older
sidecar conventions, and beta uses `MANIFEST.json` instead of `task.json`.

Supplementary files are not universal requirements. `conftest.py`,
`kept_nodeids.txt`, `taxonomy.jsonl`, `spec_test_map.md`, `clauses.md`, review
files, score files, and manifests vary by branch and pipeline stage. The newer
Oracle Standard treats `conftest.py` as a hard oracle requirement, while older
branch checklists do not consistently carry it.

## Root-File Tone And Purpose

| File | `main/repo_status/sync` | `codex/upload/LiandZhang` | `beta` | current 50 |
|---|---|---|---|---|
| `README.md` | Formal Chinese project handbook; describes SpecBench and a golden task | Same older formal handbook; wording implies shipped tasks are qualified | Imperative workflow guide: read skills in sequence and use human-in-the-loop checks | Short English release-preparation note; explicitly says `ARTIFACT_ONLY` and names blockers |
| `AGENTS.md` | Five concise non-negotiable imperative rules | Minimal `DO NOT send optional commentary` stub | Same minimal stub | Inherits the five current non-negotiable rules |
| `REPO_STATUS.md` | Inventory tables; sync additionally explains `Status` is separate from static validity | Older stale table describing completed tasks and test counts | Not present; uses `REPO_POOL`/workflow files | One-sentence inventory; exact task details are delegated to the manifest |
| `CANDIDATES.md` | Large historical ledger with selected/qualified/retired transitions | Large historical ledger, but stale relative to the 21 task tree | Smaller legacy candidate list | Minimal statement that 50 are pending score and judge review |
| `docs/QUALITY_GATE.md` | Present; main has path/layout contradictions | Absent from committed branch | Absent | Present and inherited from sync |

### Tone Findings

1. **Current normative tone:** factual, procedural and status-aware. Sync
   explicitly says status is a pipeline state, not static proof, and records
   `REVALIDATION-REQUIRED` instead of silently treating every packet as done.
2. **Historical qualified tone:** definitive and publication-oriented. The
   words `QUALIFIED` and `已合格` are used as final labels even where the
   branch does not carry an external Stage 4 trust artifact.
3. **Beta tone:** instructional and operational. It tells contributors which
   skills to read and emphasizes human review, but its legacy file format cannot
   be used as the current packet contract.
4. **Current 50 tone:** deliberately cautious and epistemically correct. It
   distinguishes local replay/reproducibility from trusted scoring and names
   promotion blockers. Its weakness is that the root inventory is too terse for
   a multi-contributor repository.

## Spec Language Comparison

The following are deterministic style signals, not universal semantic gates:

| Branch/pool | Legacy structure | Authority phrase | API table | Author-voice Non-Goals | Descriptive overview | Two behavior H2 | Forbidden-term free |
|---|---:|---:|---:|---:|---:|---:|---:|
| `main` | 29/61 | 9/61 | 9/61 | 10/61 | 38/61 | 43/61 | 56/61 |
| `repo_status` | 29/61 | 9/61 | 9/61 | 10/61 | 38/61 | 43/61 | 56/61 |
| `sync` | 0/60 | 60/60 | 60/60 | 30/60 | 41/60 | 60/60 | 60/60 |
| `codex` | 0/34 | 0/34 | 0/34 | 0/34 | 20/34 | 27/34 | 21/34 |
| `upload` | 6/70 | 0/70 | 0/70 | 2/70 | 35/70 | 45/70 | 53/70 |
| previous `LiandZhang` | 0/21 | 0/21 | 0/21 | 0/21 | 9/21 | 14/21 | 19/21 |
| current 50 | 50/50 | 0/50 | 10/50 | 5/50 | 33/50 | 12/50 | 50/50 |

Interpretation:

- Current 50 are structurally accepted by the validator and have clean
  candidate-visible prose, but their writing is not sync-equivalent.
- All 50 lack the sync authority phrase; 40 lack the `Name | Kind | Role` API
  table; 45 lack the exact author-voice Non-Goals pattern; 38 lack two
  behavior-domain H2 sections.
- Previous `LiandZhang` is older in both structure and tone. Its 19/21
  forbidden-term-free result is weaker than current 50's 50/50.
- Main and repo_status are not a clean style gold standard either. Sync is the
  only branch with consistent current authority/API/domain signals.
- These heuristics must not be satisfied with generic boilerplate. Missing
  sections should be added only when they describe real task behavior.

## Requirements And Defects By Branch

### `main`

- Uses the current `dev/skills` root and normative documents, but README and
  quality-gate text disagree about skill and oracle paths.
- 61 tasks are present, but only 58 contain the complete nested core packet in
  the cached inventory.
- Statuses mix `QUALIFIED`, `REOPENED_S3`, and `REVALIDATION-REQUIRED`.
- It has numeric candidate scores but no recognized external Stage 4 signature.

### `repo_status`

- Shares main's mixed layout and documentation contradictions.
- Its purpose is inventory/status synchronization, not an independent trusted
  evaluator.
- It carries the same historical qualification language without an external
  trust anchor.

### `sync-from-release-and-fix-gates`

- Best current structural and language reference: 60/60 current validator pass
  in the cached run and complete nested core packets.
- Its ledger still has 17 warnings.
- It still does not contain an owner-controlled signed Stage 4 attestation, so
  its `QUALIFIED` statuses cannot establish real adversarial black-box proof.

### `codex/transitions-fullrepro-001`

- Uses the older root `skills` convention and carries no current normative docs.
- Uses older task language and metadata expectations.
- 33/34 integration files and 0/34 sync-style authority/API/Non-Goals signals.
- Its `QUALIFIED` labels are historical workflow output, not trusted proof.

### `upload/native-batch-16-20260720`

- Uses the older root `skills` convention and mixed historical packet quality.
- It contains the previous `LiandZhang` 21 task trees exactly, so it is not an
  independent comparator for those tasks.
- It has many `QUALIFIED` labels and numeric scores but no signed external
  attestation.

### `LiandZhang`

- Uses old root skills, old spec tone and old packet gates.
- 21/21 are labelled `QUALIFIED`, but the current validator finds 0/21 valid;
  its inventory also has stale root documentation.
- Its per-task reviews acknowledge same-process limitations while still
  recommending qualification.

### `beta`

- Is a legacy workbench, not a current task-packet reference.
- Uses `MANIFEST.json` and does not provide the current `task.json` contract.
- Its imperative workflow tone is useful for process documentation, but its
  files cannot be copied as the current release layout.

### `LiandZhang50-artifact-only`

- Uses the current `dev/skills`, nested packet and current validator.
- 50/50 packets pass the current static gate with zero warnings and all carry
  explicit artifact-only status.
- The root prose is intentionally cautious but too minimal for a full project
  inventory; reviewers must consult `UPLOAD_PREP_MANIFEST.json`.
- It lacks trusted scores, signatures, judge/promotion records and an isolated
  runner; this is correctly reflected in its tone and status.
- It is a standalone replacement tree: it removes the 60 sync task directories
  and adds 50 new ones, so it must not be merged directly as an additive PR.

## Cross-Branch Stage 4 Finding

The task and root-file tone differences do not change the central trust issue.
The inspected branches share the same basic candidate/evaluator execution
model. Candidate code can run in the pytest process with the oracle worktree as
the working directory, and the Docker wrapper does not itself prove
`--network none`. No inspected branch contains a recognized owner-controlled
signature binding candidate digest, evaluator image, oracle digest and score.

Therefore:

- historical `QUALIFIED` wording is stronger than the evidence supports;
- current `ARTIFACT_ONLY` wording is the most accurate status;
- matching peer filenames or prose cannot replace an external trusted runner.

## Recommended Canonical Style

For future work, use sync's current structure and tone:

1. Keep `dev/skills/` and the five normative documents as the rule source.
2. Use nested self-contained task packets with `task.json` as metadata.
3. Write specs in the current authority/API/domain style only where behavior
   supports it; preserve precise task-specific language.
4. Keep status language explicit: `SELECTED`, `REVALIDATION-REQUIRED`,
   `ARTIFACT_ONLY`, or `QUALIFIED` only when its evidence contract is met.
5. Maintain a generated per-task inventory and direct lint/static evidence.
6. Treat trusted Stage 4 attestation as a separate requirement from local
   replay and DeepSeek review.
