# Append-free linearizable reads

Applications often keep their queryable state in the FSM behind a Raft node.
Before serving a linearizable read, a leader must establish that it still has a
voting quorum and that its local FSM has consumed the committed state covered
by that confirmation. Writing a barrier entry for every read provides a similar
ordering point, but adds avoidable log and replication traffic.

The `raft` package adds this public surface:

```go
type ReadIndexFuture interface {
    Future
    Index() uint64
}

func (r *Raft) ReadIndex(timeout time.Duration) ReadIndexFuture
```

`ReadIndex` starts an append-free linearizable-read boundary. As with other
Raft futures, callers wait with `Error` before inspecting the result. After a
nil error, `Index` is the committed boundary established by the operation, and
the local application FSM has finished consuming every committed command
through that index. The caller may then query its FSM at that linearization
point.

Success requires confirmation from a voting quorum while the receiving node is
the leader. A single-voter cluster confirms itself. Nonvoters participate in
replication but do not replace a voter in the quorum. A follower or candidate
returns an error matching `ErrNotLeader`; loss of leadership during
confirmation returns the library's ordinary leadership-loss error. Shutdown
and admission timeout use the same error conventions as existing futures.

The boundary is taken from committed state, not merely the last stored log or
the latest entry queued toward the FSM. Work already committed when quorum
confirmation completes is included. Concurrent work ordered after that point
need not be included. A slow application therefore delays successful completion
even when exported progress counters have advanced.

The operation is read-only with respect to the replicated protocol. It does not
append a command, no-op, barrier, or configuration entry, and does not trigger a
snapshot. Ordinary leader election may already have appended its normal no-op;
that unrelated entry is outside the read operation.

Snapshot restore, log replay, batching, and ordinary command application retain
their existing order. A read boundary that meets any of them completes only
after the preceding committed FSM work has completed. Once a quorum-confirmed
boundary has entered the local FSM stream, a later leadership change does not
undo the already established linearization point.

`Index` is meaningful after `Error` returns nil. Failed operations make no
claim about it. Repeated and concurrent calls are independent and do not alter
the result or lifecycle of existing `Apply`, `Barrier`, `VerifyLeader`,
snapshot, configuration, or leadership-transfer operations.
