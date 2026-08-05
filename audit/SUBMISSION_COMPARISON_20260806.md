# LiandZhang Submission Comparison

## Scope And Standard

This report compares two submissions:

- Previous submission: `origin/LiandZhang` at `5a08f45`, containing 21 tasks.
- Current submission task payload: `LiandZhang50-artifact-only` at `c253198`,
  containing 50 tasks; the final audit head is `cf82944`.

Independent comparison refs are `origin/main`, `origin/beta`,
`origin/repo_status`, `origin/codex/transitions-fullrepro-001`, and
`origin/sync-from-release-and-fix-gates`. The 21 task trees on
`origin/upload/native-batch-16-20260720` that are byte-for-byte identical to
the previous submission are excluded as independent evidence.

Two standards are kept separate:

1. **Branch convention:** files and language patterns that actually occur on
   independent GitHub branches.
2. **Strict current gate:** the rules and validator on
   `sync-from-release-and-fix-gates`, plus the trusted Stage 4 requirement.

Matching an old branch convention is not proof of trusted black-box ability.

## Executive Comparison

| Check | Previous 21 | Current 50 | Best independent comparison |
|---|---:|---:|---:|
| Task directories | 21 | 50 | sync: 60 |
| Current nested Gate 0 packet complete | 20/21 | 50/50 | sync: 60/60 |
| Current `30/25/60` physical floor | 3/21 | 50/50 | sync: 60/60 |
| Current static validator | 0/21 | 50/50, 0 warnings | sync: 60/60, 17 ledger warnings |
| Status | 21 `QUALIFIED` | 50 `ARTIFACT_ONLY` | mixed by branch |
| Usable numeric candidate score | 21/21 | 0/50 | sync: 25/60 |
| Explicit trusted Stage 4 attestation | 0/21 | 0/50 | 0 in inspected refs |
| Recognized external signature artifact | 0/21 | 0/50 | 0 in inspected refs |
| Absolute local paths in `task.json` | 54 | 0 | sync: 5 |
| Included local replay files | 0 task-local `logs/` | 50/50, 199 files | 0 tasks on inspected refs |
| Exact task-tree overlap with peers | 21/21 with upload | 0/50 | n/a |

The current submission is materially stronger as a construction artifact. It
is not stronger as a trusted scored benchmark because it intentionally has no
candidate score or external attestation.

## Previous Submission Defects

### 1. The `QUALIFIED` Claim Is Not Supported By Its Trust Boundary

All 21 tasks are marked `QUALIFIED`, and all 21 carry a numeric candidate
score. However:

- none has a `stage4` trust record or `stage4_attestation`;
- none has a recognized external signature artifact;
- the candidate-score provenance is self-submitted local metadata;
- 54 metadata values expose absolute paths under local workspaces;
- only 4/21 `task.json` candidate evidence paths resolve to an included
  relative evidence file; most scores are inline summaries or point to local
  paths that do not exist after cloning the branch.

Every per-task DeepSeek review returns `PASS`, but the same reviews explicitly
state that pytest and the candidate share a process/filesystem and that the
result is not adversarial black-box proof. They nevertheless recommend
`QUALIFIED` or `QUALIFIED_WITH_CAVEATS`. Under the strict trust requirement,
that policy decision is invalid: the caveat is a qualification blocker, not a
non-blocking note.

### 2. It Fails The Current Static Gate

Running the current sync validator against the previous 21 packets gives
`0/21` statically valid tasks. The aggregate failures are:

| Failure class | Affected/error count |
|---|---:|
| Missing required semantic sections | 75 section errors |
| Taxonomy keys differ from physical tests | 20 tasks |
| `depends_on` coverage below 50% | 20 tasks |
| Invalid atomic/integration taxonomy layers | 19 tasks each |
| Layer floor below `30/25` | 17 tasks |
| Metadata layer counts below physical functions | 6 tasks |
| Candidate-visible forbidden terms | 3 errors across 2 tasks |
| Atomic positive-share/no-check problems | 2 tasks |
| Total scoreable cases below 60 | 1 task |
| Missing oracle test files | 1 task |

Only `cerberus`, `pycparser`, and `pyyaml` meet the current physical
`30 atomic / 25 integration / 60 total` floor.

### 3. Per-Task Hard Defects Under The Current Gate

| Task | Main blocking defects |
|---|---|
| `arrow` | atomic 14; missing assessment/evaluation section; taxonomy and dependency map fail |
| `babel` | integration 14; missing assessment/evaluation section; taxonomy and dependency map fail |
| `cerberus` | missing state/workflow/invocation/environment sections; metadata counts below physical tests |
| `chardet` | integration 8; missing assessment/evaluation section; taxonomy and dependency map fail |
| `cleo` | atomic 29, integration 11; missing environment/evaluation sections |
| `click` | atomic 13; seven semantic sections missing |
| `dateutil` | atomic 12, integration 8; seven semantic sections missing |
| `gunicorn` | atomic 24; layer metadata disagrees with physical files |
| `hy` | atomic 25, integration 15; eight semantic sections missing |
| `hypercorn` | integration 18 and total 52; layer metadata mismatch |
| `jsonpickle` | atomic 12; layer metadata mismatch |
| `jsonschema` | atomic 8; eight semantic sections missing; layer metadata mismatch |
| `lark` | atomic 16; positive assertions 4/16; twelve atomic tests classified no-check |
| `markdown` | no current-style `test_` functions detected; positive share 0/30; semantic sections missing |
| `markdown-it-py` | atomic 12, integration 21; eight semantic sections missing |
| `parso` | atomic 20, integration 14; seven semantic sections missing |
| `pgpy` | atomic 9, integration 12; candidate-visible `scoring` term |
| `pycparser` | physical floor passes, but state/environment/evaluation, taxonomy, and dependency map fail |
| `pyparsing` | atomic 4, integration 12; state/environment/evaluation missing |
| `pyyaml` | physical floor passes, but environment, forbidden terms, taxonomy, and dependency map fail |
| `sqlparse` | both nested oracle test files missing; declared total is only 59 |

### 4. Branch And Inventory Defects

- `origin/LiandZhang` is an orphan commit with no parent, so it cannot be
  reviewed as a normal additive PR against `main` without unrelated-history
  handling.
- `REPO_STATUS.md` says 34 tasks are complete while the branch contains 21.
- The README points to a golden `httpcore` task that is absent from the branch.
- The branch-native ledger validator reports 155 ledger errors; some come from
  the old repo-name/task-id namespace bug, but the committed inventory is still
  visibly stale and contradictory.
- All 21 task trees exactly match trees already present on the upload branch,
  so that branch cannot provide an independent second review.

### 5. Language And Packet Style Defects

Against the deterministic style audit:

- current semantic/legacy structure: 0/21;
- authority disclaimer: 0/21;
- `Name | Kind | Role` API catalog: 0/21;
- sync-specific standardized Non-Goals bullet wording: 0/21;
- complete standardized environment signal: 0/21;
- forbidden-term free: 19/21.

These style signals are not all universal historical hard gates, but they show
that the previous branch is an older packet generation and cannot be described
as equivalent to the current sync standard. A broader heuristic finds general
author/first-person wording in 7/21 specs; the `0/21` figure above is the exact
sync-style requirement that every bullet begin with `This specification does
not require` or `This specification does not define`.

## Current Submission Defects

### 1. It Is Not A Qualified Benchmark Release

The current 50 correctly avoid the previous false claim, but promotion is
blocked by design:

- trusted candidate score: 0/50;
- independent signed Stage 4 attestation: 0/50;
- promotion/judge record: 0/50;
- strict black-box proof: 0/50;
- hard network-isolation proof: 0/50;
- `same_process_private_evaluator=true`: 50/50;
- Docker replay: false for 50/50.

The 199 replay files and their hashes prove local reproducibility only. They do
not prove that an untrusted candidate could not read or alter the evaluator.

### 2. The Runner Security Defect Is Still Present

The previous submission, current submission, main, sync, beta, codex, and
upload branches all use the same `harness/run.py`; they also share the same
Docker wrapper. In the current scorer:

- pytest is launched with the candidate solution on `PYTHONPATH`;
- the copied oracle/source worktree is the pytest working directory;
- candidate code executes inside the pytest interpreter and can inspect test
  modules, process state, and the visible filesystem;
- `run_in_docker.sh` does not add Docker `--network none`;
- results are written locally and are not signed by an external owner-controlled
  service.

This is a repository-wide Stage 4 defect. The current branch documents it
honestly but does not fix it.

### 3. It Is A Standalone Replacement Tree, Not An Additive PR

The current branch is based on sync commit `0737fb3`, whose task tree contains
60 tasks. The branch removes all 60 and adds 50 different task directories,
with zero names retained. Merging it directly into `main` or sync would delete
the existing task set. It is safe as a standalone review branch only.

The root inventory is internally consistent, but minimal:

- `REPO_STATUS.md` only states that 50 artifacts exist;
- `CANDIDATES.md` has no per-task registry;
- reviewers must use `UPLOAD_PREP_MANIFEST.json` instead of the normal project
  inventory tables.

### 4. Metadata Is Valid For Artifact Review But Incomplete For Promotion

- `candidate_score` is explicitly `null` in 47 tasks and absent in `fastavro`,
  `jupytext`, and `kombu`; this is a minor schema inconsistency.
- `source_meta` is populated in only 8/50 tasks.
- `weaknesses` is absent in 50/50 tasks.
- `stage4_attestation` is absent in 50/50 tasks.
- `target_imports` is absent in `glom` and `xlsxwriter`.
- no committed per-task fresh `lint_result.txt` exists, so the non-negotiable
  lint state transition cannot be independently replayed from the branch.

Several of these fields are inconsistent on peer branches too and are not
enforced by the current static validator. They remain promotion-readiness and
auditability gaps, not reasons to reject an explicitly artifact-only branch.

### 5. Language Style Is Not Sync-Equivalent

All 50 pass the current semantic validator, are forbidden-term free, and carry
the complete environment signal. Against the stricter sync writing style:

| Signal | Current 50 | Sync comparison |
|---|---:|---:|
| Authority disclaimer | 0/50 | 60/60 |
| `Name | Kind | Role` API catalog | 10/50 | 60/60 |
| Standard Non-Goals author voice | 5/50 | 30/60 |
| Descriptive overview | 33/50 | 41/60 |
| At least two behavior-domain H2 sections | 12/50 | 60/60 |
| Forbidden-term free | 50/50 | 60/60 |

This is a real style gap, but not a universal branch-format violation. Any
rewrite must be task-specific; adding generic boilerplate merely to satisfy a
counter would reduce spec quality.

### 6. No Automatic GitHub Gate

The current branch has no `.github/workflows` gate. None of the inspected peer
refs has one either, so this is systemic rather than unique. A pushed commit can
therefore drift from the recorded local audit unless a reviewer reruns the
validator and evidence-hash checks.

## Defects In The Comparison Branches

The peer branches are useful conventions, not a clean gold standard:

- `main` and `repo_status` have incomplete nested packets and conflicting
  documentation about skill/oracle locations.
- `beta` uses the legacy `MANIFEST.json` format and cannot define the current
  `task.json` contract.
- `codex` and upload use older root-level skills and older packet layouts.
- upload contains all 21 previous task trees exactly and is not independent for
  those tasks.
- sync is the strongest current structural comparator, but still has 17 ledger
  warnings and no external Stage 4 attestation.
- no inspected branch contains recognized signed runner evidence, and all use
  the same candidate/evaluator boundary.

Therefore, “other branches also say QUALIFIED” cannot validate either of our
submissions under the stricter trust requirement.

## Required Disposition

### Previous 21

Treat as **legacy untrusted / revalidation required**, not as 21 trusted
`QUALIFIED` tasks. Retain the branch only for history unless all packets are
migrated through the current static gate and an independent Stage 4 runner.

### Current 50

Keep as **ARTIFACT_ONLY REVIEW BRANCH**. It is structurally reviewable and
substantially cleaner than the previous branch, but it must not be merged as a
replacement task tree or promoted to `QUALIFIED`.

## Remediation Order

1. Mark the previous 21-task branch as legacy/revalidation-required and stop
   citing its local DeepSeek PASS reviews as qualification evidence.
2. Rebase or reconstruct an additive delivery branch so existing main/sync
   tasks are not deleted.
3. Normalize current metadata and complete task-specific style review.
4. Publish reproducible lint/static/CI evidence for every task.
5. Run candidate generation in a candidate-only environment, then transfer an
   immutable artifact to a separate evaluator that does not expose the oracle.
6. Disable evaluator network access at the kernel/container boundary, isolate
   process/user/mount namespaces, and prevent candidate writes to evaluator
   state.
7. Have an owner-controlled service sign the candidate artifact digest,
   evaluator image digest, oracle digest, score, and policy result.
8. Only after signature verification and judge/promotion records exist should
   any task become `QUALIFIED`.

## Machine Evidence

- `submission_branch_audit_20260806.json`: branch inventories, status/score
  counts, exact tree overlaps, absolute metadata paths, and evidence-reference
  resolution.
- `previous_against_current_validator_20260806.txt`: the previous 21 packets
  evaluated by the current sync validator (`0/21`).
- `current_validator_20260806.txt`: the current branch's direct validator output
  (`50/50`, zero warnings).
- `previous_native_validator_20260806.txt`: the previous branch's own ledger
  validator output (155 legacy ledger errors).
- `GITHUB_REQUIREMENTS_STYLE_AUDIT.md`: deterministic branch/style comparison.
- `deepseek_submission_comparison_20260806.json`: independent review of this
  report and the supporting machine evidence.
