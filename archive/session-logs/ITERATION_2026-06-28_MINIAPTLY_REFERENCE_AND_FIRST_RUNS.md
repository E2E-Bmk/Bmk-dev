# MiniAptly Reference And First Runs

Date: 2026-06-28

## Scope

MiniAptly was advanced from `candidate/prd-draft` into the first runnable reference/candidate gate.

## Artifacts Added

- `runs/miniaptly-realrepo-001/solution-reference/miniaptly.py`
- `task/miniaptly-realrepo-001/doc/score_reports/score_report_reference_unit_system_v1.json`
- `skills/miniaptly-task-builder/SKILL.md`
- `runs/miniaptly-realrepo-001/openhands_deepseek_v4_pro_001_task.txt`
- `runs/miniaptly-realrepo-001/openhands_deepseek_v4_pro_002_task.txt`
- `runs/miniaptly-realrepo-001/openhands_deepseek_v4_pro_003_task.txt`

## Reference Gate

Reference implementation passes the current executable rubric:

- `score_report_reference_unit_system_v4_fairness.json`
- Unit: 100.00%
- System: 100.00%

## Candidate Runs

### Codex Subagent

Fresh Codex worker saw only the public MiniAptly PRD and wrote:

- `runs/miniaptly-realrepo-001/solution-codex-subagent-001/miniaptly.py`

Current score:

- `score_report_codex_subagent_001_unit_system_v4_fairness.json`
- Unit: 100.00%
- System: 100.00%
- Raw gap: 0.00pp

### OpenHands + DeepSeek V4 Pro

Two launch/config failures were preserved:

- `openhands_deepseek_v4_pro_001_launchfail_gbk.log`: Windows GBK stdout encoding failed before model action.
- `openhands_deepseek_v4_pro_001_authfail_openai_endpoint.log`: DeepSeek key was sent to OpenAI endpoint because no base URL was set.
- `openhands_deepseek_v4_pro_002.log`: `deepseek-v4-pro` without provider prefix failed LiteLLM provider routing before action.

Scoreable run:

- `openhands_deepseek_v4_pro_003.log`
- Conversation ID: `d53cb1b9-a71a-4a37-acbf-c8310096f8be`
- Artifact: `runs/miniaptly-realrepo-001/solution-openhands-deepseek-v4-pro-003/miniaptly.py`
- Score report: `score_report_openhands_deepseek_v4_pro_003_unit_system_v4_fairness.json`
- Unit: 80.00%
- System: 60.00%
- Raw gap: 20.00pp

## Fairness Revisions Applied

The initial executable rubric over-constrained several public schema choices:

- zero-argument constructor was not explicit enough for durable-root implementations;
- dependency field was compared as list-only;
- recovery prefix separator was compared exactly;
- graph prefix/type and package identity formatting were too narrow;
- `snapshot_diff.changed` shape was compared as `before/after` only;
- `add()` return value was used even though the PRD did not require it;
- `cleanup.keep` was compared as a reason dictionary only.

The PRD and rubric now normalize these equivalent public representations. These revisions turned Codex from raw 80/40 to 100/100, confirming that earlier Codex failures were evaluator/schema issues.

## Open Judge Gate

The remaining OpenHands DeepSeek failures are under independent judge review:

- `MAU002`: malformed parser primitive, likely non-compositional.
- `MAU009`: pending recovery visibility and cleanup blocking after failed switch.
- `MAS001`: `snapshot_diff.changed` does not report version replacement while old snapshot/publish/graph mostly remain coherent.
- `MAS004`: failed `publish_switch(..., fail_at='after_publish_record')` exposes new published state before recovery and cleanup is not blocked.

Pending question: after clustering primitive/evaluator roots, does residual compositional gap remain at least 15pp?
