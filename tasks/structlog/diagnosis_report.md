# Stage 5 Diagnosis — structlog v3 cleanroom run

## Verdict

**QUALIFIED** — the cleanroom run, solvability evidence, and fairness audit all pass. Labels: `near-ceiling-candidate-score`, `mixed-public-oracle`, and `stdlib-configuration-edge`.

## Anti-cheat and provenance

The mandatory import preflight was run from `/private/tmp`, outside both the candidate directory and the oracle worktree, with only candidate `output/` on `PYTHONPATH`.

```bash
PYTHONPATH=/Users/zijian/bench/Bmk-dev/candidate-runs/cleanroom-structlog-v3-20260714-001/output python3 -c 'import structlog; print(structlog.__file__)'
```

### Preflight output

```
/Users/zijian/bench/Bmk-dev/candidate-runs/cleanroom-structlog-v3-20260714-001/output/structlog/__init__.py
```

This resolves to the candidate solution rather than an oracle or installed package. The Stage 4 Linux record independently records the same provenance under `/work/.../output/structlog/__init__.py`, Docker Linux `python:3.11-slim`, and scorer isolation with `--remove-path structlog`.

The candidate packet contains only `task_prompt.txt`, `pyproject.toml`, and the candidate `structlog` implementation. A forbidden-pattern scan of that output found no reference to `repo-pool/`, an oracle worktree, score artifacts, `spec_test_map.md`, `kept_nodeids.txt`, or target-package installation. The run directory does not retain an agent command transcript beyond this packet and the evaluator artifacts; the recorded cleanroom boundary says the agent received only the public task prompt. No recorded evidence of forbidden access was found.

## Solvability

The isolated reference scorer passed **64/64 (100%)**: atomic 23/23, integration 38/38, and system_e2e 3/3. Its three groups were 8/8 v3 additions, 50/50 generated base cases, and 6/6 rewritten upstream cases. A fresh judge rerun of the isolated scorer reproduced 64/64 with `--remove-path structlog`. The candidate was scored in Docker Linux with the same 64-nodeid oracle. There are no collection errors or dependency failures, so the oracle ceiling is valid and exceeds the 95% requirement.

## Candidate score and failure analysis

The candidate passed **63/64 (98.44%)**: atomic 22/23, integration 38/38, and system_e2e 3/3. A fresh isolated scorer rerun reproduced the same layer totals and one failure.

The only failure is atomic: `filter/generated_additions.py::test_recreate_defaults_configures_standard_logging_at_requested_level`. It maps to **Standard-Library and Development Namespaces**. That specification explicitly requires `stdlib.recreate_defaults(log_level=<integer>)` to configure standard-library logging to `sys.stdout` at that requested level. The test checks the public root logger level and subsequent public logging delivery; it does not inspect private state, `repr`, layout, or an error string.

The candidate left an already configured root logger at `WARNING` (30) after a request for `INFO` (20). A direct candidate-only reproduction with an existing root handler and level `WARNING` also printed `30`. The reference passes the same oracle case. Therefore Q-A is **No** (the candidate diverges from the explicit spec) and this is a real model failure, not a factual spec error or fairness issue.

Root cause: configuration did not replace an existing standard-library root logger threshold. Dimension: **atomic-behavior**. It affects one atomic case and produces **one root cause with zero cascaded failures**.

## Fairness Gate A — mapping spot-check

Eight covered rows were checked against their named specification clauses:

| sampled test | mapped section | result |
|---|---|---|
| `test_getLogger_passes_factory_args_and_initial_values_to_the_event` | Installable Surface; Configuration and Logger Construction; Bound Loggers | Correct: public alias, lazy factory args, initial context, and `ReturnLogger` delivery are specified. |
| `test_bind_is_immutable_and_merges_values` | Cross-View Invariants; Bound Loggers | Correct: source context remains unchanged and returned logger gains the value. |
| `test_processor_chain_passes_result_to_delivery` | Processors and Rendering | Correct: processor successor value must be delivered to the wrapped logger. |
| `test_merge_contextvars_preserves_event_precedence` | Cross-View Invariants; Bound Loggers | Correct: event keys win and absent context-local keys are added. |
| `test_capture_logs_records_normalized_method` | Output and Testing Utilities | Correct: capture must add normalized `log_level` to the assembled event. |
| `test_rewrite_drop_event_returns_none` | Error Semantics; Processors and Rendering | Correct: `DropEvent` prevents delivery and returns `None`. |
| `test_representative_context_to_capture_workflow[r1]` | Representative Workflow; Cross-View Invariants; Context-Local Context | Correct: the asserted captured fields and INFO filtering are the supplied public workflow. |
| `test_recreate_defaults_configures_standard_logging_at_requested_level` | Standard-Library and Development Namespaces | Correct: requested standard-library level and public output delivery are explicit v3 postconditions. |

All sampled tests are spec-driven and behavioral. No mapping correction is needed.

## Fairness Gate B — failure pattern audit

There is one failure cluster. It has an explicit spec heading, asserts an observable standard-library logging configuration outcome, and the reference passes it. It is not an internal-shape, exact-format, private-attribute, or error-message assertion. Gate B passes; no filter correction request is required.

## Fairness Gate C — generated-only check

**Not applicable.** `spec_test_map.md` declares `oracle_source: upstream_rewrites_plus_generated`, not `generated_only`. The oracle includes six independently rewritten public upstream cases, so the generated-only trigger is absent.

## Gate D — Coverage Gap Audit

All executable H2/H3 contract sections have at least one `covered` row:

| spec section | covered mappings |
|---|---:|
| Installable Surface | 3 |
| Configuration and Logger Construction | 8 |
| Bound Loggers and Product State Model | 28 |
| Processors and Rendering | 9 |
| Context-Local Context | 6 |
| Output and Testing Utilities | 11 |
| Standard-Library and Development Namespaces | 5 |
| Error Semantics | 5 |
| Cross-View Invariants | 11 |
| Representative Workflow | 3 |

**Coverage verdict: FULL.** There are zero executable contract sections with zero coverage, including the core invariant and error sections.

`Product Overview` describes the product rather than an independent assertion; `Scope` is an inclusion boundary; `Public API` is the parent of the covered H3 contracts; `Non-Goals` prohibits requirements; and `Evaluation Notes` describes evaluation policy. These non-executable boundary sections intentionally have no standalone tests and do not count as coverage gaps.

## Protocol issues and disposition

No protocol issue, spec gap, spec error, filter error, cheat signal, or coverage gap was found. The earlier Docker-daemon diagnostic is superseded by the successful provenance preflight above. The task remains in `wip/structlog/`; this judge does not migrate it or update `tasks/` or `CANDIDATES.md`.
