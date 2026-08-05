# GitHub Requirements And Style Audit

The comparison used cached independent refs and the repository's normative
documents. A live `ls-remote` check was unavailable because the remote request
timed out; cached refs were used and are named explicitly in the peer report.

## Common Requirements

- All 50 packets contain the five logical core files and four audit sidecars.
- All 50 meet the local physical and semantic gate, including the `30/25/60`
  atomic/integration/total floor.
- All 50 specs contain the required semantic sections recognized by
  `harness/verify_task.py`, have no forbidden candidate-visible terms, and
  state the Linux/Python 3.11/no-network environment.
- The publication copy contains no host path in replay logs; placeholders are
  recorded in `UPLOAD_PREP_MANIFEST.json` and all evidence hashes were
  refreshed.

## Style Difference

The current `sync-from-release-and-fix-gates` branch uses a stricter writing
heuristic in addition to the common packet contract. Against that heuristic,
the staged pool reports:

| Signal | Local 50 |
|---|---:|
| Legacy required structure | 50/50 |
| Strict authority phrase | 0/50 |
| `Name / Kind / Role` API table | 10/50 |
| Author-voice Non-Goals bullets | 5/50 |
| Descriptive overview | 33/50 |
| At least two behavior-domain H2 sections | 12/50 |
| Forbidden-term free | 50/50 |
| Candidate-visible process leakage free | 50/50 |
| Complete environment signal | 50/50 |

These strict style signals are not uniform requirements across all independent
branches: `main`, transition, upload, and `beta` use different subsets. The
missing signals are therefore recorded as a review difference, not silently
filled with generic text that would weaken task semantics.

## Decision

The pool is structurally uploadable as `ARTIFACT_ONLY` after human review, but
it must not be described as language-style-identical to the sync branch or as
`QUALIFIED`. A future style pass should add task-specific authority wording,
API catalogs, and behavior-domain sections only when those sections can be
derived from the public contract and independently reviewed.
