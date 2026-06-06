# Case Summary: `zk-realrepo-001`

## Result

- V1 score: 84.00%
- Expanded/audited score: 70.00%
- Decision: accept as a provisional target-band case, with a repeated-root-cause caveat.

## What Was Reasonable

- The public packet described a compact product, not a source-code implementation.
- Hidden rubrics evaluated workflows: init, create, parse, list, tag, graph, config, notebook discovery, links, backlinks, and errors.
- Reference implementation passed 100%, showing the scorer is executable and internally coherent.
- Candidate failures were traceable to explicit public requirements, not hidden implementation details.

## Caveat

The expanded target-band score is partly caused by repeated sort-suffix failures:

- note sort `title+`;
- note sort `path-`;
- note sort `word-count-`;
- tag sort `note-count-`.

These are legitimate but clustered. Reporting should distinguish the aggregate score from the diversity of failed capabilities.

## Lesson For PRD-Rubric Design

Stateful notebook tasks are much healthier than one-shot parser/formatter CLIs. ZK-style cases create separability because the candidate must maintain and query a derived model over files:

- note metadata parsing;
- link graph resolution;
- tag expression logic;
- command/config interaction;
- multi-command lifecycle workflows.

A reasonable PRD-rubric pair here is still traceable but non-isomorphic: the PRD names user workflows and command contracts, while hidden tests compose them into notebooks whose derived relationships must be correct across several commands.

The scoring lesson is to report repeated-root clusters explicitly. A benchmark can be target-band numerically but still less informative if many failed points are one parser bug expressed repeatedly.
