# ProgramBench and Local Evaluation Cost Estimate

Date: 2026-07-13

Source: ProgramBench paper, arXiv:2605.03546, especially Table 2 and Appendix A.1.

## ProgramBench Main Evaluation

Table 2 reports average API calls and API cost per task for each of nine models. Each model is evaluated on 200 tasks.

| Model | Calls per task | Cost per task | Cost for 200 tasks |
|---|---:|---:|---:|
| Claude Opus 4.7 | 93 | $3.81 | $762 |
| Claude Opus 4.6 | 260 | $11.38 | $2,276 |
| Claude Sonnet 4.6 | 475 | $27.09 | $5,418 |
| Claude Haiku 4.5 | 124 | $0.80 | $160 |
| Gemini 3.1 Pro | 94 | $1.51 | $302 |
| Gemini 3 Flash | 89 | $0.33 | $66 |
| GPT 5.4 | 16 | $0.33 | $66 |
| GPT 5.4 mini | 18 | $0.04 | $8 |
| GPT 5 mini | 15 | $0.03 | $6 |
| **Total** | **1,184** | **$45.32** | **$9,064** |

Therefore, the directly reported main evaluation scale is:

- 1,800 model-task runs.
- Approximately 236,800 API calls.
- **$9,064 API cost.**

## ProgramBench Construction and Extended Experiments

Appendix A.1 states that task construction uses three SWE-agent stages and caps each stage at $3, or $9 per completed task. For 200 completed tasks, the explicit upper bound is **$1,800**. This excludes unknown spend on candidate repositories that failed before becoming final benchmark tasks.

The paper also reports two extended experiment families:

1. Different-language ablation across the nine-model evaluation matrix. Applying 0.75x-1.25x of the main-run cost gives **$6.8k-$11.3k**.
2. Internet-enabled runs for Claude Opus 4.6, Claude Sonnet 4.6, Gemini 3 Flash, and GPT 5 mini. Their default Table 2 costs sum to $38.83 per task, or $7,766 for 200 tasks. Allowing for changed trajectory lengths gives **$6.2k-$10.1k**.

Cheat detection covers 786 trajectories with nine judges each, or 7,074 judge calls. Since the paper does not report judge token counts or cost, a broad $0.25-$2.00 per full-trajectory judgment gives **$1.8k-$14.1k**.

| Scope | Estimated API cost |
|---|---:|
| Main nine-model evaluation | $9,064 (reported) |
| Construction of final 200 tasks | <= $1,800 (reported cap) |
| Different-language ablation | $6.8k-$11.3k |
| Internet-enabled model runs | $6.2k-$10.1k |
| Nine-judge cheat detection | $1.8k-$14.1k |
| **Estimated published experimental campaign** | **approximately $24k-$46k** |

A practical all-in planning range is **$25k-$50k**, allowing modest room for failed collection attempts and unreported reruns. Human review, compute, container execution, storage, and engineering labor are not API costs and are excluded.

## Local Nine-Task Evaluation Allocation

The user reports $100 of aggregate spend for the whole session between 16:00 and 19:00. It must not be assigned entirely to the nine scoring tasks. The session also includes main-agent coordination, repeated skill and state reads, test/spec auditing, invalid environment attempts, artifact verification, reporting, ProgramBench paper analysis, and user interaction.

An effort-based session allocation is:

| Session component | Estimated cost | Share |
|---|---:|---:|
| Nine successful scoring agents | $47 | 47% |
| Main-agent evaluation orchestration and real test/spec audit | $26 | 26% |
| Invalid or redundant evaluation/environment attempts | $7 | 7% |
| Evaluation artifact verification and summary generation | $5 | 5% |
| ProgramBench PDF and cost analysis | $5 | 5% |
| Other main-thread interaction and long-context overhead | $10 | 10% |
| **Total** | **$100** | **100%** |

Under this allocation:

- Estimated main-agent spend is approximately **$46**: $26 evaluation work, $5 artifact/report work, $5 ProgramBench analysis, and $10 other context/interaction overhead.
- Direct successful scoring-agent spend is approximately **$47**, averaging **$5.22 per task**.
- Fully-loaded nine-task evaluation spend is approximately **$85** after adding evaluation-related main-agent work, failed attempts, and reporting, averaging **$9.44 per task**.
- The remaining **$15** is attributed to ProgramBench research and other non-evaluation session work.
- Total executed pytest cases: 569. Fully-loaded evaluation spend per executed case is approximately **$0.149**, although agent cost does not scale linearly with test count.

The following task allocation applies the same observed effort weights to both the $47 direct-agent pool and the $85 fully-loaded evaluation pool. It is an accounting estimate, not per-thread telemetry.

| Task | Weight | Direct scoring-agent estimate | Fully-loaded evaluation estimate | Reason |
|---|---:|---:|---:|---|
| dbt-core | 8% | $3.8 | $6.8 | Fast score diagnosis; one fixture cascade explains all outcomes. |
| Starlette | 12% | $5.6 | $10.2 | Invalid Python 3.8 attempt, environment rebuild, then final rerun. |
| h2 | 10% | $4.7 | $8.5 | Nine failures required seven-root analysis. |
| Luigi | 9% | $4.2 | $7.7 | Five independent failure clusters and spec checks. |
| HTTPX | 12% | $5.6 | $10.2 | Missing-dependency false failures required a repaired rerun. |
| Bandit | 9% | $4.2 | $7.7 | High-score provenance and SARIF failure audit. |
| Kedro | 9% | $4.2 | $7.7 | Reopened oracle and candidate-selection checks. |
| nbformat | 15% | $7.1 | $12.8 | Long isolated-agent run, environment correction, 100% saturation audit. |
| pgqueuer | 16% | $7.5 | $13.6 | Long isolated-agent run, candidate selection, parameterized-case and cascade audit. |
| **Total** | **100%** | **approximately $47** | **approximately $85** | Evaluation scope only. |

## Billing-Column Ambiguity

The earlier daily dashboard entry reports 1,997 requests, 277.57M provider-counted tokens, $18.14 actual cost, and $316 standard cost. The actual-to-standard ratio is 5.74%.

The reported $100 for 16:00-19:00 cannot be an actual-cost subset of the same daily $18.14 total. Therefore one of the following must differ: billing column, provider group, time zone, or dashboard scope.

- If $100 is actual charged spend, the session allocation above applies directly: approximately $85 for the nine-task evaluation and $15 for other work.
- If $100 is standard/list-price spend, applying the daily 5.74% ratio gives about **$5.74 actual session cost**. Under the same allocation, the nine-task evaluation would be about **$4.88 actual total** or **$0.54 fully-loaded actual cost per task**; direct scoring-agent cost would be about **$0.30 per task**.

Per-task costs should not be presented as telemetry until the backend exports usage grouped by thread or request.

## Six-Model Projection for 120 Local-Style Tasks

This projection uses the observed 2026-07-13 local workflow as the workload baseline. It does not use ProgramBench's task-worker costs and excludes all Stage 5 judges.

The afternoon session completed nine comparable Stage 4 tasks for approximately $100 of total session spend. The effort allocation above attributes approximately $85 to scoring-related work, giving a fully-loaded GPT-5.6-sol baseline of $9.44 per task. Assigning the entire $100 to scoring gives a conservative upper baseline of $11.11 per task.

The six-model matrix contains 120 tasks x 6 models = 720 model-task runs. Price ratios assume a long-running agent token mix of approximately 5% uncached input, 90% cache hits, and 5% output. This approximates the repeated-context pattern observed in the backend; it does not assume ProgramBench trajectory lengths.

| Model | Official short-context prices: input / cache / output per MTok | Blended ratio vs GPT-5.6-sol | Cost per local-style task | Cost for 120 tasks |
|---|---:|---:|---:|---:|
| GPT-5.5 | $5.00 / $0.50 / $30.00 | 1.00x | $9.44-$11.11 | $1,133-$1,333 |
| Claude Opus 4.8 | $5.00 / $0.50 / $25.00 | 0.89x | $8.40-$9.89 | $1,008-$1,187 |
| Gemini 3.1 Pro | $2.00 / $0.20 / $12.00 | 0.40x | $3.78-$4.44 | $453-$533 |
| GLM-5.2 | $1.40 / $0.26 / $4.40 | 0.24x | $2.27-$2.67 | $272-$320 |
| DeepSeek-V4-Pro | $0.435 / $0.003625 / $0.87 | 0.031x | $0.29-$0.34 | $35-$41 |
| Kimi K2.6 | approximately $0.90 / $0.15 / $3.75 | 0.17x | $1.60-$1.89 | $192-$227 |
| **Total main matrix** |  |  | **$25.78-$30.34 per six-model task row** | **approximately $3,093-$3,641** |

The main matrix estimate assumes identical workload shape and controlled limits across models. Natural model behavior can change request counts materially, so a practical no-judge budget is **$3.5k-$4.5k** for the 720-run main evaluation.

### Subset Ablations

Costs scale approximately with the fraction of task-model cells rerun:

| Additional experiment | Added runs | Added API estimate |
|---|---:|---:|
| One 25% subset ablation: 30 tasks x 6 models | 180 | $773-$910 |
| One 50% subset ablation: 60 tasks x 6 models | 360 | $1,547-$1,821 |
| One full 120-task ablation | 720 | $3,093-$3,641 |
| Two separate 25% subset ablations | 360 | $1,547-$1,821 |
| Three separate 25% subset ablations | 540 | $2,320-$2,731 |

A representative plan consisting of the full main matrix, two 25% subset ablations, and a 10% retry reserve costs approximately **$5.1k-$6.0k**. A conservative procurement budget is **$6k-$7k**, excluding Judge calls, local compute, and storage.
