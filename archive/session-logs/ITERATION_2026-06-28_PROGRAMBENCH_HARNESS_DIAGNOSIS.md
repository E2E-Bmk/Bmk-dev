# ProgramBench Harness Diagnosis

Date: 2026-06-28

## Trigger

Current candidate scores are much higher than ProgramBench-style results. The
latest user review raised two critical questions:

- whether candidate agents are physically isolated from reference solutions,
  hidden rubrics, score reports, and prior solutions;
- whether the high pass rates come from stronger models, a stronger/leakier
  harness, or task designs that are too small and explicit.

## Local Finding

Current OpenHands task prompts include a behavioral instruction such as "Do not
inspect source repositories, scoring directories, hidden rubrics, score reports,
reference solutions, or prior candidate solution directories." That is not the
same as physical isolation.

The MiniAptly OpenHands trace shows the candidate agent reading the public PRD
and then listing the task directory. The visible directory included
`rubric.json`, `doc/score_reports/`, `doc/requirement_map.md`, and
`doc/source_repo.md`. The trace does not prove the agent opened hidden files,
but it proves the filesystem surface was not cleanroom-isolated.

Therefore current high-scoring artifacts should be treated as diagnostic
evidence, not strict benchmark pass-rate evidence, unless their run can be
reproduced in a cleanroom workspace.

## Trace Leakage Audit

Tool-based trace scanning is now available:

```text
tools/audit_trace_leakage.py
runs/trace_leakage_audit_20260628.json
```

After fixing UTF-16 log decoding, the scan over 100 existing log/task files
found:

```text
non_strict_direct_surface: 4
non_strict_observed_surface: 10
clean: 86
```

Important example:

- `runs/miniaptly-realrepo-001/openhands_deepseek_v4_pro_003.log` directly
  opened `task/miniaptly-realrepo-001/doc/requirement_map.md` after first
  listing the task directory and observing `rubric.json` and `doc/score_reports`.

This is not proof of malicious copying, but it is enough to mark the run
non-strict. A candidate run may be useful diagnostically while still being
invalid for strict model-ordering or solved/no-gap claims.

## Judge Coverage So Far

Existing judge agents did check some provenance and contamination symptoms:

- MiniRedis: 100/100 Codex artifact was byte-identical to reference, so strict
  solved evidence was rejected.
- MiniKV: behavior looked solved but trace provenance was too weak.
- MiniTemplate and MiniBitcask: some non-identical OpenHands/Codex artifacts
  were judged closer to independent solutions.

This is still an after-the-fact audit. It cannot replace a pre-run filesystem
and network isolation gate.

## ProgramBench Contrast

ProgramBench uses a stricter cleanroom framing:

- candidate workers see documentation and an execute-only gold program, not the
  source implementation or hidden tests;
- Docker containers run without internet;
- hidden behavioral tests are generated and validated outside the worker
  workspace;
- early internet-enabled experiments showed substantial cheating through source
  lookup, so the final setup disables that path.

The reported pass rates are far lower than current local mini-task results:
no evaluated model fully solved the benchmark, the strongest model solved only a
small fraction at high thresholds, and median behavioral-test pass rates were
around one third. This is consistent with larger real-program tasks plus a
cleanroom harness, not merely weaker models.

Primary reference: https://arxiv.org/html/2605.03546v1

## Attribution

Current local pass-rate inflation likely comes from three sources:

1. Task design: many tasks are compact one-file mini-products with explicit PRD
   schemas and small test suites.
2. Harness exposure: candidates can be placed in a repository tree that also
   contains rubrics, score reports, reference solutions, and old candidates.
3. Model/tool strength: Codex subagents and OpenHands are capable software
   agents, especially on 500-1500 line dependency-free Python tasks.

The task design is probably the largest source. Harness exposure makes the high
scores hard to interpret. Model strength explains why near-complete public PRDs
are often enough.

## New Gate

Before any new score is used for model ordering or solved/no-gap claims:

1. Generate a cleanroom workspace containing only `public_packet/`, an empty
   `solution/`, `task_prompt.txt`, and `cleanroom_manifest.json`.
2. Do not copy `rubric.json`, `score_reports`, `solution-reference`, old
   candidate solutions, `MANIFEST.json`, `CANDIDATES.md`, or iteration notes.
3. Run the agent with that cleanroom as the visible project root.
4. Score from outside the cleanroom after the artifact is produced.
5. Record the cleanroom path, agent trace, model, network setting, and score
   report together.
6. Treat non-cleanroom runs as exploratory diagnostics only.

Tool added:

```text
tools/create_cleanroom_packet.py
tools/audit_trace_leakage.py
```

## Harness Switch

Strict candidate evidence should move from OpenHands-first to a
mini-SWE-agent-style harness:

- minimal shell agent instead of rich local IDE/file-editor affordances;
- clean `/workspace` root with only the public packet and empty solution tree;
- Docker or equivalent isolation with no network by default;
- full trajectory saved with every command;
- final artifact copied out and scored externally;
- OpenHands runs are retained as diagnostic or builder evidence, not strict
  pass-rate evidence, unless run inside the same cleanroom contract.

Local mini-SWE-agent source exists at:

```text
G:\research\02_security\live-harness-tbench\sources\mini-swe-agent
```

Its ProgramBench config uses Docker, `--network none`, `/workspace`, trajectory
serialization, and submission tarball capture. The local SWE-E2E runner should
adapt that pattern rather than the current same-tree OpenHands setup.

Current dependency status:

- local mini-SWE-agent source is present;
- direct import with the current Python fails because `python-dotenv` is not
  installed in that interpreter;
- do not silently fall back to OpenHands for strict evidence. Install or run
  mini-SWE-agent in its proper environment first, then use cleanroom workspaces.

## Task-Scale Reset

New benchmark candidates must be multi-file system tasks. A candidate is not
eligible for strict construction if the public packet can reasonably be solved
as one standalone Python file with one in-memory model.

New task gate:

- require a package layout with at least five public modules or services;
- require durable state plus indexes/reports/history/recovery files;
- require at least three candidate-owned public projections;
- require a build/test entrypoint that exercises the project as a package or
  executable, not a single import-only module;
- reject tasks whose reference can be cleanly implemented as one short file
  without distorting the product surface.

## Implication For Candidate Selection

Do not continue adding adjacent hidden rows to currently near-solved mini tasks.
Use ProgramBench-like failure modes when selecting new tasks:

- behavior discovery against an oracle or executable, not only PRD following;
- durable state plus public replay/history/audit projections;
- larger workflows where hidden tests are product-natural but not enumerated in
  the prompt;
- clean separation between unit primitive readiness and system lifecycle
  invariants;
- no network and no access to source/reference/test artifacts during candidate
  implementation.
