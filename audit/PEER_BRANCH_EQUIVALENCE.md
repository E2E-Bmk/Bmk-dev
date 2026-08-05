# Independent Peer Branch Equivalence

This review excludes `origin/LiandZhang` and the 21 exact task-tree mirrors
on `origin/upload/native-batch-16-20260720` from the independent baseline.

## Result

The 50 staged tasks are **core-packet compatible** with the independent
branch family after migration into `tasks/<task-id>/`. They are not status or
evidence-equivalent to published `QUALIFIED` tasks.

| Check | Result |
|---|---:|
| Selected task directories | 50/50 |
| Core packet files | 50/50 |
| Audit sidecars | 50/50 |
| Referenced replay files | 199/199 |
| Static validator | 50/50, 0 warnings |
| Candidate scores with passed/total | 0/50 |
| `ARTIFACT_ONLY` status | 50/50 |
| Trusted Stage 4 attestations | 0/50 |

Independent references checked: `main`, `repo_status`,
`sync-from-release-and-fix-gates`, `codex/transitions-fullrepro-001`, the
non-mirrored upload tasks, and `beta`.

The independent branches do not share one universal optional-file policy:
`source_nodeid_map.json`, per-task DeepSeek files, replay logs, and judge
sidecars are inconsistent across them. The common structural requirement is
the logical task packet. The local pool exceeds that structural floor with
task-local replay evidence, while explicitly retaining `ARTIFACT_ONLY`.

## Qualification Difference

Published `QUALIFIED` tasks generally have a usable candidate score and a
promotion/judge record. The staged pool has neither. Local reference and dummy
replays are same-process reproducibility artifacts and cannot establish a
trusted black-box score or external Stage 4 attestation.

**Conclusion:** suitable for an explicitly artifact-only review branch;
not equivalent to a qualified release branch.
