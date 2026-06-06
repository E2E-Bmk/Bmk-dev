# Attempt Report

## Candidate

- Candidate directory: `G:/research/swe-e2e/runs/zk-realrepo-001/solution-agent-001`
- Candidate file: `zmini.py`
- Isolation instruction: candidate was given only `candidate_task/public_packet.md` and the output directory. It was instructed not to inspect source, scoring, source checkouts, ProgramBench samples, or hidden files.

## Candidate Summary

The candidate implemented:

- `init`, `new`, `list`, `tag list`, and `graph`;
- notebook discovery through upward `.zk`, `--notebook-dir`, and `ZK_NOTEBOOK_DIR`;
- Markdown title, frontmatter, tag, and link parsing;
- JSON, JSONL, path, title, and short output modes;
- tag expressions with AND/OR/NOT;
- link filters, recursive traversal, orphan and missing-backlink filters;
- config note defaults and named filters;
- graph JSON nodes/edges;
- errors for missing notebooks, invalid regexes, missing linked targets, and duplicate paths.

## V1 Raw Score

- Rubric: `scoring/rubrics.json`
- Raw report: `score_report_agent_001_raw.json`
- Passed cases: 12 / 14
- Weighted score: 84 / 100
- Percentage: 84.00%

Failures:

- `ZKI001`: rejected `--sort title+`.
- `ZKI002`: tag expression `inbox OR later, NOT done` incorrectly included `b.md`.

Both failures are valid under the public packet. No fairness relaxation was applied.

## Expanded / Audited Score

- Rubric: `scoring/rubrics_audited.json`
- Report: `score_report_agent_001_audited.json`
- Passed cases: 12 / 17
- Weighted score: 84 / 120
- Percentage: 70.00%

Additional public-supported failures in the expanded rubric:

- `ZKX001`: rejected `--sort path-`.
- `ZKX002`: rejected `--sort word-count-`.
- `ZKX003`: rejected `tag list --sort note-count-`.

## Fairness Audit

The expanded tests are fair because the public packet explicitly states:

- `list --sort path|title|created|modified|word-count`, with optional `+` or `-`;
- `tag list --sort name|note-count`, with optional `+` or `-`;
- tag expressions should support comma/AND, `OR`/`|`, and `NOT`/`-` in a practical way.

However, failures are clustered:

- Four failed cases share a sort-suffix parsing root cause across list/tag command surfaces.
- One failed case is a separate tag-expression composition error.

This means the 70.00% score is target-band but upper-edge and somewhat concentrated. It is still more credible than `htmlq` or `dust` because the failures come from explicit, stateful product behavior rather than evaluator ambiguity.

## Interpretation

`zk-realrepo-001` is the first additional scale-out case in this batch that plausibly meets the target-band criterion after audit, though it should be marked as "accepted with clustering caveat." Its difficulty comes from durable notebook state plus derived relationships and compositional CLI filters.
