| model | task | dimension | description | affected_tests |
|-------|------|-----------|-------------|----------------|
| rq-001-specv1-manual-20260716-001 | rq-001 | state-management | Jobs remain in created state or lose metadata instead of persisting queued, scheduled, deferred, canceled, and saved-meta lifecycle state across queue and fetch views. | 6 |
| rq-001-specv1-manual-20260716-001 | rq-001 | workflow-completeness | Worker execution fails while saving jobs with missing created_at, cascading through success, failure, sync execution, dependency, retry, result-history, serializer, and worker-priority workflows. | 18 |
| rq-001-specv1-manual-20260716-001 | rq-001 | atomic-behavior | Retry and Repeat configuration objects do not expose the documented interval-list fields used by scheduling and retry workflows. | 2 |
