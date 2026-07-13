# TorkWorkflow System Projection Matrix v3

Date: 2026-06-28

Each system row must compare at least three public projections derived from the
same durable workflow history.

| Check | Cross-feature contract | Public projections compared |
| --- | --- | --- |
| TW-S001 | submit -> worker -> completion | job detail, job list, task detail, logs, progress, queue |
| TW-S002 | task output feeds downstream expression | job detail output, downstream task output, logs, progress |
| TW-S003 | retry exhaustion consistency | job detail, job list, task attempts, logs, progress, queue |
| TW-S004 | timeout terminal failure | job detail, job list, task detail, logs, progress, queue |
| TW-S005 | cancel queued work | job detail, job list, task detail, queue, logs |
| TW-S006 | restart preserves old history and creates new run | old job detail/list, new job detail/list, queue |
| TW-S007 | parallel parent rollup | job detail/list, parent task, child tasks, logs, progress |
| TW-S008 | each expansion rollup | job detail/list, parent task, child tasks, logs, progress |
| TW-S009 | conditional skip dependency advancement | job detail/list, skipped task, downstream task, logs, progress |
| TW-S010 | subjob parent/child output | job detail/list, parent task, child task, logs, progress |
| TW-S011 | schedule tick provenance | schedules, job detail metadata, job list, queue |
| TW-S012 | not-due schedule duplicate prevention | schedules, job list, queue |
| TW-S013 | worker-loss recovery queue rebuild | recovery report, queue status, job detail, task detail, job list |
| TW-S014 | durable reopen completion preservation | reopened job detail/list, task detail, logs, progress, queue |
| TW-S015 | failure logs and attempts | job detail/list, task attempts, logs, progress, queue |
| TW-S016 | single-completion queue safety | job detail/list, task attempts, logs, progress, queue |
| TW-S017 | job isolation | two job details, job list, job-scoped logs, progress |
| TW-S018 | pre-step failure propagation | job detail/list, failed pre task, absent main log, queue |
| TW-S019 | recovery report/detail/queue agreement | recovery report, queue status, job detail, task detail, job list |
| TW-S020 | CLI/API facade agreement | CLI job list, CLI job detail, CLI progress, CLI logs |
