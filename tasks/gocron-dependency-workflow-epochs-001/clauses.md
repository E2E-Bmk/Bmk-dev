# Clause Traceability

| Clause ID | Section | Verbatim contract |
|---|---|---|
| GCWF-GRAPH-001 | Graph Registration and Mutation | `NewWorkflow` must reject a nil scheduler with `ErrWorkflowSchedulerRequired`. |
| GCWF-GRAPH-002 | Graph Registration and Mutation | `NewWorkflow` must reject an empty workflow name with `ErrWorkflowNameRequired`. |
| GCWF-GRAPH-003 | Graph Registration and Mutation | `Name` returns the construction name unchanged. |
| GCWF-GRAPH-004 | Graph Registration and Mutation | `Add` must reject an empty node name with `ErrWorkflowNodeNameRequired`. |
| GCWF-GRAPH-005 | Graph Registration and Mutation | `Add` must reject a duplicate name with `ErrWorkflowNodeExists`. |
| GCWF-GRAPH-006 | Graph Registration and Mutation | `Add` and `Update` must reject absent dependencies with `ErrWorkflowDependencyNotFound`. |
| GCWF-GRAPH-007 | Graph Registration and Mutation | Duplicate dependency names must collapse to one edge. |
| GCWF-GRAPH-008 | Graph Registration and Mutation | A direct or transitive dependency cycle must return `ErrWorkflowCycle`. |
| GCWF-GRAPH-009 | Graph Registration and Mutation | A rejected graph mutation must leave the previous graph and job usable. |
| GCWF-GRAPH-010 | Graph Registration and Mutation | `Nodes` returns nodes sorted by name. |
| GCWF-GRAPH-011 | Graph Registration and Mutation | `Nodes` must return copied dependency slices. |
| GCWF-GRAPH-012 | Graph Registration and Mutation | `Update` must preserve the scheduler job UUID. |
| GCWF-GRAPH-013 | Graph Registration and Mutation | `Remove` must reject a referenced node with `ErrWorkflowNodeHasDependents`. |
| GCWF-GRAPH-014 | Graph Registration and Mutation | `Remove` must delete an unreferenced node and its scheduler job. |
| GCWF-GRAPH-015 | Graph Registration and Mutation | Graph mutation during an active epoch must return `ErrWorkflowBusy`. |
| GCWF-EPOCH-001 | Epoch Scheduling and Dependency Release | `RunNow` must reject an empty workflow with `ErrWorkflowEmpty`. |
| GCWF-EPOCH-002 | Epoch Scheduling and Dependency Release | `RunNow` must reject a scheduler that has not started with `ErrWorkflowSchedulerStopped`. |
| GCWF-EPOCH-003 | Epoch Scheduling and Dependency Release | `RunNow` returns a handle before task completion. |
| GCWF-EPOCH-004 | Epoch Scheduling and Dependency Release | Epoch IDs are positive and monotonically increasing within a workflow. |
| GCWF-EPOCH-005 | Epoch Scheduling and Dependency Release | Root nodes become eligible at epoch start. |
| GCWF-EPOCH-006 | Epoch Scheduling and Dependency Release | A child starts only after every direct dependency in the same epoch succeeds. |
| GCWF-EPOCH-007 | Epoch Scheduling and Dependency Release | Independent ready nodes are eligible to execute concurrently. |
| GCWF-EPOCH-008 | Epoch Scheduling and Dependency Release | A diamond join executes exactly once after both parents succeed. |
| GCWF-EPOCH-009 | Epoch Scheduling and Dependency Release | Distinct active epochs keep independent task contexts and node results. |
| GCWF-EPOCH-010 | Epoch Scheduling and Dependency Release | A task whose first parameter is `context.Context` receives the epoch context. |
| GCWF-EPOCH-011 | Epoch Scheduling and Dependency Release | Other `NewTask` parameters and error-return behavior remain compatible with scheduler jobs. |
| GCWF-RESULT-001 | Results, Failures, and Cancellation | `Snapshot` returns a copied result map. |
| GCWF-RESULT-002 | Results, Failures, and Cancellation | A wait-context deadline does not cancel the epoch. |
| GCWF-RESULT-003 | Results, Failures, and Cancellation | Repeated waits after completion return equivalent terminal data. |
| GCWF-RESULT-004 | Results, Failures, and Cancellation | Successful nodes end in `WorkflowNodeSucceeded` with terminal timestamps. |
| GCWF-RESULT-005 | Results, Failures, and Cancellation | Task errors mark their node failed and make `Wait` return `ErrWorkflowFailed`. |
| GCWF-RESULT-006 | Results, Failures, and Cancellation | A recovered panic marks its node failed and remains discoverable as `ErrPanicRecovered`. |
| GCWF-RESULT-007 | Results, Failures, and Cancellation | A failed node blocks all not-yet-started descendants with `ErrWorkflowDependencyFailed`. |
| GCWF-RESULT-008 | Results, Failures, and Cancellation | Failure in one branch does not prevent unrelated branches from completing. |
| GCWF-RESULT-009 | Results, Failures, and Cancellation | Canceling a run affects that epoch only and cancels unreleased nodes. |
| GCWF-RESULT-010 | Results, Failures, and Cancellation | `Stop` cancels every active epoch and waits for terminal run handles. |
| GCWF-SCHED-001 | Scheduler Interactions and Lifecycle | Workflow nodes execute through their registered scheduler jobs. |
| GCWF-SCHED-002 | Scheduler Interactions and Lifecycle | Success, error, panic, and lock listeners must remain observable. |
| GCWF-SCHED-003 | Scheduler Interactions and Lifecycle | A lock acquisition error fails the node without invoking its task. |
| GCWF-SCHED-004 | Scheduler Interactions and Lifecycle | `LimitModeWait` bounds ready-node concurrency without losing nodes. |
| GCWF-SCHED-005 | Scheduler Interactions and Lifecycle | The same workflow node executes serially across overlapping epochs. |
| GCWF-SCHED-006 | Scheduler Interactions and Lifecycle | `WithLimitedRuns` remains effective for a workflow node. |
| GCWF-LIFE-001 | Scheduler Interactions and Lifecycle | `Shutdown` is idempotent and closes the workflow. |
| GCWF-LIFE-002 | Scheduler Interactions and Lifecycle | Workflow shutdown removes workflow-owned scheduler jobs. |
| GCWF-LIFE-003 | Scheduler Interactions and Lifecycle | Workflow shutdown must not remove unrelated scheduler jobs or shut down the scheduler. |
| GCWF-LIFE-004 | Scheduler Interactions and Lifecycle | Operations after workflow shutdown return `ErrWorkflowClosed` where specified. |

## Combined behavioral coverage

`TestDiamondJoinRemainsPendingUntilBlockedParentCompletes` composes `GCWF-EPOCH-006`, `GCWF-EPOCH-008`, and `GCWF-RESULT-004`: after one direct parent has succeeded while another remains running, the join remains pending and does not execute; after the remaining parent succeeds, the join executes once.
