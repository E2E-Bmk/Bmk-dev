# Full-Reproduction Layer-1 Restart

Date: 2026-06-28

## Scope

This iteration continues after the mini-task route was judged invalid for SOTA
agents. The active rule is: no new strict task may be a one-file mini clone.
Strict candidates must be full bounded subsystems with cleanroom scoring,
interface-defined public modules, executable hidden checks, and saved traces.

## External Calibration

Network was enabled for candidate and harness refresh. The useful external
calibration is harness-level rather than adding another small domain:

- mini-SWE-agent / ProgramBench style evaluation reinforces cleanroom
  candidate workspaces, hidden external scoring, default no-network runs, and
  trajectory preservation.
- ProgramBench-like low pass rates are not directly comparable to the current
  unit/system split because ProgramBench scores whole-task reconstruction,
  while this benchmark must separate module-local primitive success from
  cross-module invariant failure.

Strict evidence should therefore use a mini-SWE-agent-style cleanroom harness;
OpenHands remains useful for debugging only when its visibility contract is
equivalent.

## Layer-0 Audit Results

| Candidate | Source inspiration | Verdict | Current action |
|---|---|---|---|
| `jobledger-fullrepro-001` | `oban-bg/oban` | `BUILD` | Continue Layer-1. PRD/rubric/starter/harness exist; executable tests and reference implementation are missing. |
| `buildcache-fullrepro-001` | `buchgr/bazel-remote` | `BUILD` | Continue Layer-1 from prospect audit. Needs PRD, requirement map, executable rubric, starter, and reference. |
| `schemaregistry-fullrepro-001` | `confluentinc/schema-registry` | `BUILD_WITH_RESCOPE` | Continue only as a custom schema language and custom API, not Avro/Confluent clone. |
| `BackupRepository` | `kopia/kopia` | `BUILD` reserve | Good full-system candidate, but filesystem-heavy. Keep after queue/cache/schema. |
| `DurableWorkflow` | `cschleiden/go-workflows` | `BUILD` reserve | Strong event-history/replay surface, but harness complexity is higher. |
| `FeatureFlagControlPlane` | `thomaspoignant/go-feature-flag` | `BUILD` reserve | Viable reserve; guard against targeting/bucketing primitive cascade. |
| `DurableAppPlatform` | `restatedev/restate` | `RESCOPE` | Reserve only; overlaps durable workflow/job ledger and can over-expand. |

No additional network-scouted candidate currently outranks JobLedger,
BuildCache, or custom SchemaRegistry under the full-reproduction gate.

## Skill Construction

Layer-1 task-builder skills were created or repaired:

- `skills/minijobledger-task-builder/SKILL.md`
- `skills/minibuildcache-task-builder/SKILL.md`
- `skills/schemaregistry-task-builder/SKILL.md`

Each skill now contains:

- agreement surface and free parameters;
- feature-pure unit test template;
- integration/system test template with cross-feature contracts;
- oracle and contamination boundaries;
- cleanroom harness rules.

Validation:

- `minijobledger-task-builder`: `quick_validate.py` passed with bundled Python.
- `minibuildcache-task-builder`: `quick_validate.py` passed with bundled Python.
- `schemaregistry-task-builder`: `quick_validate.py` passed with bundled Python.

## JobLedger Current State

Existing artifacts:

- `task/jobledger-fullrepro-001/prd.md`
- `task/jobledger-fullrepro-001/rubric.json`
- `task/jobledger-fullrepro-001/doc/requirement_map.md`
- `task/jobledger-fullrepro-001/doc/harness.md`
- `task/jobledger-fullrepro-001/candidate_task/starter/src/jobledger/`

Rubric shape:

- 50 draft check rows total;
- 20 unit rows;
- 15 integration rows;
- 15 system rows.

Blocking gap before model runs:

- rubric rows are check intents, not executable hidden tests;
- no reference implementation exists under the task or run directory;
- reference has not proven unit=100/system=100;
- no strict mini-SWE-agent cleanroom candidate run exists yet.

Do not run Codex, DeepSeek, or Qwen on JobLedger until executable tests and the
reference implementation exist. Running now would only measure prompt-following
against a skeleton, not benchmark difficulty.

## Independent Judge Check

Subagent `Sagan the 2nd` audited JobLedger readiness without modifying files.
Conclusion:

- Layer-0 is mostly satisfied and remains `BUILD`.
- Layer-1 is not satisfied because the rubric is still intent-only and the
  harness is a plan, not a runnable scorer.
- Candidate-visible files have low direct leakage risk.
- The source `candidate_task/public_packet.md` refers to `prd.md`; generated
  cleanroom workspaces include `public_packet/prd.md`, so strict runs should use
  the generated workspace rather than the raw `candidate_task` directory.
- Unit rows are mostly feature-pure; JLU001 wording was tightened from
  model/API constructor to direct model constructor.
- Top blockers: no executable hidden tests, no runnable harness, incomplete raw
  candidate packet, recovery marker setup needs public creation semantics, and
  reference-readiness evidence is missing.

## Cleanroom Smoke

`tools/create_cleanroom_packet.py` was updated for interface-defined tasks:

- copies `candidate_task/public_packet.md` into `public_packet/`;
- copies `candidate_task/starter/` into the visible workspace;
- keeps hidden artifact names out of `cleanroom_manifest.json`.

Smoke workspace:

- `runs/cleanroom/jobledger-cleanroom-smoke-20260628-layer1-v2`

Leakage scan:

- `tools/audit_trace_leakage.py` now scans common text files, not only
  `.log`/`.txt`;
- scan result: 19 files scanned, 0 direct hidden-surface hits, 0 observed
  hidden-surface hits.

## Executable Reference Smoke

A runnable JobLedger reference/scorer prototype now exists, but remains below
the strict full-reproduction scale gate.

Artifacts:

- `runs/jobledger-fullrepro-001/solution-reference/`
- `task/jobledger-fullrepro-001/scoring/run_executable_checks.py`
- `runs/jobledger-fullrepro-001/score_report_reference_executable_smoke_20260628.json`

Current executable score:

- total: 13/13 passing;
- unit: 7/7;
- integration: 3/3;
- system: 3/3;
- includes one reference-vs-reference differential parity check that runs the
  same workflow in separate subprocesses and compares normalized public
  projections.

Current reference scale:

- 15 Python modules;
- 905 source lines under `solution-reference/src/jobledger`;
- still below the 2,000+ non-test LOC target and far below the 50+ executable
  check target.

Newly materialized state surfaces:

- durable attempt ledger;
- history report includes attempts plus event timeline;
- queue/conflict reports moved out of the API facade into report logic;
- retention prune planning/report logic moved into its own module.

This is a useful executable spine, not a promotable task. Do not run model
candidates yet.

## Next Execution Order

1. Expand JobLedger reference from 905 LOC toward 2,000+ LOC by implementing
   PRD-owned surfaces: cron ledger reports, uniqueness window materialization,
   recovery markers, full CLI, diagnostics, import validation, and richer
   retention summaries.
2. Convert the remaining `jobledger-fullrepro-001/rubric.json` rows into at
   least 50 executable checks.
3. Verify reference passes all 50 checks.
4. Run cleanroom trace-leakage audit on the candidate packet.
5. Run mini-SWE-agent-style strict candidates: Codex, DeepSeek/OpenHands only
   if equivalently isolated, then Qwen as weaker contrast.
6. Judge failures by primitive/cascade/evaluator/compositional buckets.

BuildCache should start only after JobLedger has an executable scorer path, so
the pattern is not copied as another non-runnable draft.
