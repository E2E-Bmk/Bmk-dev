# Go task submission batch

This branch contains six complete Go reconstruction task packets:

| Task | Upstream repository | Oracle | Candidate model | Candidate score |
| --- | --- | ---: | --- | ---: |
| `expr-rule-engine-fullrepro-001` | `expr-lang/expr` | 74/74 | `deepseek-v4-pro[1m]` | 66/74 (89.19%) |
| `validator-struct-rules-fullrepro-001` | `go-playground/validator` | 65/65 | `deepseek-v4-pro[1m]` | 61/65 (93.85%) |
| `casbin-policy-enforcement-fullrepro-001` | `casbin/casbin` | 60/60 | `deepseek-v4-pro[1m]` | 59/60 (98.33%) |
| `nutsdb-transactional-collections-fullrepro-001` | `nutsdb/nutsdb` | 67/67 | `deepseek-v4-pro[1m]` | 66/67 (98.51%) |
| `afero-layered-filesystems-fullrepro-001` | `spf13/afero` | 64/64 | `deepseek-v4-pro[1m]` | 62/64 (96.88%) |
| `bbolt-transactional-kv-fullrepro-001` | `etcd-io/bbolt` | 65/65 | `deepseek-v4-pro[1m]` | 65/65 (100%) |

Each directory includes the public specification, oracle tests, specification-to-test map, taxonomy metadata, and task metadata. Candidate solutions are not included.

The reference implementation passes all oracle tests. Candidate scoring was performed in a clean Linux/WSL environment with dependencies prepared before offline evaluation. The candidate pass rates are higher than the preferred calibration range, so these are submitted transparently as complete backup tasks rather than claimed as final difficulty-calibrated tasks. Harder tasks and revisions can follow separately.

Static validation commands:

```powershell
python harness/verify_task.py <task-id>
python harness/validate_ledger.py <task-id>
```

Incomplete work, including the current gojq task, is intentionally excluded from this batch.
