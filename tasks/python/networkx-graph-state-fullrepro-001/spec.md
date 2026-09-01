# NetworkX versioned graph workspace

NetworkX retains its ordinary public graph classes, views, conversions, and
algorithms.  This extension adds `networkx.workspace`, a local durable
coordination layer for graph generations.  It is deliberately expressed as
behavioral families: callers may vary node labels, edge keys, attribute values,
operation identifiers, branch names, owners, and order while the same laws
continue to hold.

## Public records and errors

The module exports `WorkspaceError`, `ConflictError`, `OwnershipError`,
`IntegrityError`, and immutable records `Transaction`, `Revision`, `Snapshot`,
`ViewLease`, `AlgorithmResult`, `MergeRecord`, `CompensationRecord`, and
`AuditRecord`. Records compare by value and do not expose mutable internal
mappings. Deterministic collections are tuples ordered by canonical textual
node/key representation.

`GraphWorkspace(path, *, directed=False, multigraph=True)` owns one durable
workspace. Reopening the same path reconstructs committed state, generations,
branches, leases, snapshots, algorithm cache, merge history, and compensation
history. Different paths and owners never alias. Corrupt or truncated durable
state is rejected by `IntegrityError`, rather than silently reset.

## Transactions and generations

`begin(owner, *, branch="main", operation_id)` captures the branch head and
returns an open `Transaction`. Operation identifiers are idempotency keys:
exact replay returns the committed result, while reuse with different input is
a conflict. `add_node`, `remove_node`, `add_edge`, `remove_edge`, and
`set_graph_attr` stage changes only inside the transaction. Failed staging and
`abort` leave every committed projection unchanged.

`commit(transaction, *, operation_id)` is compare-and-swap against its captured
branch head. A successful non-empty commit creates exactly one next generation,
appends exactly one chained journal record, and advances only that branch.
Empty commits are stable idempotent observations and do not invent a new graph
generation. A stale transaction conflicts without partial publication.
Simple graphs update an existing edge; multigraphs preserve distinct keys and
allocate the lowest unused non-negative integer key when none is supplied.
Undirected edge identity is endpoint-order independent; directed identity is
not.

## Temporal snapshots and integrity

`snapshot(generation=None, *, branch="main")` returns an immutable `Snapshot`
containing canonical nodes, keyed edges, graph attributes, generation,
predecessor digest, and content digest. Historical snapshots never track later
mutation. Equal logical graphs yield equal content digests regardless of input
mapping order, while ancestry remains visible in the journal chain.

`verify()` validates every predecessor link, record digest, referenced
generation, branch head, cache provenance, merge reference, and compensation
reference. It returns an `AuditRecord`; structural disagreement raises
`IntegrityError`. `history(branch)` is ordered and does not expose mutable
state.

## Owned multigraph views

`lease_view(owner, *, branch="main", nodes=None, reverse=False,
operation_id)` returns a fenced `ViewLease` tied to a branch generation and an
optional node selection. Reading a lease projects the exact leased generation;
it is not a live alias. In a directed workspace, reverse swaps endpoints while
preserving multigraph keys and attributes. A node filter keeps only induced
edges. A lease may be `handoff` to another owner, incrementing its fence; stale
or foreign leases are rejected. `refresh` advances a current owned lease to the
branch head and increments its fence. Leases from one workspace cannot be used
in another even when names match.

`apply_view(lease, owner, changes, *, operation_id)` applies a transaction
against the leased generation. It validates owner, fence, branch, node scope,
and reverse-edge mapping before committing. Any invalid change or stale lease
rolls back the whole set. Successful application returns both the new revision
and a refreshed lease.

## Branch, federation, merge, and compensation

`fork(name, *, from_branch="main", generation=None, operation_id)` creates a
branch at an existing generation. Exact replay is idempotent. `merge(target,
sources, *, owner, policy, operation_id)` treats sources as a federation of
independent heads. `policy` is `"strict"`, `"ours"`, or `"theirs"`. Strict
merge rejects conflicting node attributes, graph attributes, and same keyed
edge values. The other policies resolve conflicts consistently, without
discarding non-conflicting contributions. Source order cannot change a strict
result; duplicate and unknown sources are rejected. A successful merge creates
one generation and one `MergeRecord` containing all input heads and the chosen
resolutions.

`compensate(merge, *, owner, reason, operation_id)` creates a new generation
that restores the exact target snapshot from immediately before that merge.
It never rewrites history. A foreign owner, stale merge, already-compensated
merge, or reused operation identifier conflicts without mutation. The returned
`CompensationRecord` links the merge, restored digest, and new generation.

## Algorithm provenance and cache

`run_algorithm(lease, owner, algorithm, *, parameters=(), operation_id)` runs
against the immutable leased snapshot. Required algorithms are `degree`,
`reachable`, and `shortest_path`; parameters are canonical `(name, value)`
pairs. Results include the workspace identity, snapshot digest, branch,
generation, lease fence, algorithm, canonical parameters, deterministic value,
and result digest. Directedness, multigraph parallel edges, and reverse or
filtered view semantics must match ordinary NetworkX behavior.

Cache identity includes every provenance field that can affect the answer.
Exact calls reuse the same result record; a new generation, refreshed lease,
different filter/reverse flag, parameters, directedness, or algorithm cannot
alias an older cache entry. A failed algorithm call publishes nothing.

## Cross-view recovery workflow

Transactions, leases, algorithms, merge, and compensation are separate
projections joined by recorded identities, not a single mutable dictionary.
After reopen, old snapshots and results remain inspectable, current owned
leases may be refreshed, stale leases stay fenced, and `verify` reconciles all
projections. A workflow that applies a filtered or reversed view change,
computes algorithms, merges branches, compensates, and reopens must restore the
pre-merge graph while retaining auditable later generations and non-aliasing
historical results.

The contract does not require private NetworkX implementation details, a
particular JSON layout, exact exception messages, timing, thread scheduling, or
evaluator-specific constants.
