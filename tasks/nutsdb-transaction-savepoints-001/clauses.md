# Clause Index

| Clause ID | Section | Verbatim contract |
|---|---|---|
| NUT-SP-001 | Savepoint Lifecycle | When `Savepoint` succeeds, the transaction must return a non-zero `SavepointID`, append a live savepoint, and capture every mutation staged before the call. |
| NUT-SP-002 | Savepoint Lifecycle | IDs returned by later calls in the same transaction must be greater than earlier IDs. |
| NUT-SP-003 | Savepoint Lifecycle | A consumed ID must not be reused. |
| NUT-SP-004 | Savepoint Lifecycle | When `SavepointDepth` is called on an open transaction, it must return the number of live savepoints. |
| NUT-SP-005 | Savepoint Lifecycle | When `ReleaseSavepoint` names the most recent live savepoint, it must remove that savepoint without changing staged mutations. |
| NUT-SP-006 | Savepoint Lifecycle | If release names a live savepoint below a newer savepoint, then it must return `ErrSavepointNotTopmost` and leave state and depth unchanged. |
| NUT-SP-007 | Savepoint Lifecycle | If rollback or release names an unknown or consumed ID, then it must return `ErrSavepointNotFound`. |
| NUT-RB-001 | Rollback Boundaries | When `RollbackTo` names a live savepoint, the transaction must restore the exact staged mutations and accounting state captured at creation. |
| NUT-RB-002 | Rollback Boundaries | Rollback-to must consume the target and every newer savepoint. |
| NUT-RB-003 | Rollback Boundaries | When rollback targets an inner savepoint, mutations staged before that boundary must remain and older savepoints must remain live. |
| NUT-RB-004 | Rollback Boundaries | After successful rollback-to, the transaction must accept later transaction operations under their normal contracts. |
| NUT-DS-001 | Data Structures, Buckets, and Expiration | When rollback removes a staged key/value or TTL mutation, reads must expose the restored prefix. |
| NUT-DS-002 | Data Structures, Buckets, and Expiration | When rollback removes staged list, set, or sorted-set operations, those operations must not appear after commit. |
| NUT-DS-003 | Data Structures, Buckets, and Expiration | When rollback removes staged bucket creation or deletion, commit must behave as though it was never staged. |
| NUT-TX-001 | Commit, Watch, and Failure Semantics | When commit follows savepoint operations, only current staged state must persist. |
| NUT-TX-002 | Commit, Watch, and Failure Semantics | After commit or full rollback, every savepoint method must return `ErrTxClosed`. |
| NUT-TX-003 | Commit, Watch, and Failure Semantics | When commit follows rollback-to, callbacks must receive events only for mutations still staged at commit. |
| NUT-TX-004 | Commit, Watch, and Failure Semantics | If a savepoint mutation method is called on an open read-only transaction, then it must return `ErrTxNotWritable` without changing depth. |
| NUT-CV-001 | Cross-View Invariants | Savepoint depth and ID validity must describe the same live stack. |
| NUT-CV-002 | Cross-View Invariants | Transaction reads after rollback-to and database reads after commit must expose the same restored key/value prefix. |
| NUT-CV-003 | Cross-View Invariants | Collection views after commit must omit discarded mutations while retaining mutations before the boundary. |
| NUT-CV-004 | Cross-View Invariants | Bucket existence and writes through restored buckets must agree with the restored lifecycle. |
| NUT-CV-005 | Cross-View Invariants | TTL after commit must belong to the retained write. |
| NUT-CV-006 | Cross-View Invariants | Watch callbacks and durable reads after commit must describe the same retained mutation set. |
| NUT-CV-007 | Cross-View Invariants | IDs must remain transaction-local. |
