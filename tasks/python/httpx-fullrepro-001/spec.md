# HTTPX orchestration journal

HTTPX applications sometimes need a durable layer above a transport: routes are selected, credentials and cookies evolve across redirects, attempts consume shared budgets, streamed bodies are either committed or rolled back, and cache entries survive process restarts. This extension provides that coordination without replacing HTTPX request and response types.

The public module is `httpx.orchestration`. It exposes immutable records and a `ClientJournal` rooted at a caller-owned directory. Mutating methods accept an `operation_id`; replaying the same operation with the same intent is idempotent, while reusing it for different intent is a conflict. Records carry an integrity receipt that can be verified after reopening.

## Routes and leases

A named route describes an origin and optional proxy/TLS boundary. Re-registering unchanged intent is idempotent. A changed route advances its generation. Capacity is represented by owner-bound leases that capture the route generation and a monotonically increasing fence. Handoff advances the fence. Operations using an old owner, fence, or route generation are rejected without changing durable state. Direct, forward-proxy, and tunneled routes retain distinct connection partitions and boundary ownership.

## Request provenance

A request transaction retains its method, target, route generation, lease fence, credential origin, cookie provenance, attempt counters, and causal history. Redirects resolve relative locations, enforce a redirect budget, strip origin credentials at trust-boundary changes, and apply cookies according to their recorded scope. Each hop is linked to the preceding request; rejected hops leave the prior transaction recoverable.

Retry admission is separate from redirect admission. Attempt, route, and circuit budgets are consumed atomically. Retryable failures may produce a new attempt only while all applicable budgets and the circuit permit it. Successful completion heals the circuit according to its generation; stale success cannot heal a newer-open circuit.

## Streaming and rollback

Response streams have an explicit receive window, delivered offset, and cleanup ownership. Data cannot be admitted beyond available capacity. Consumption returns capacity. Cancellation, decode failure, or premature close retires the stream, rolls back partial publication and cache state, and preserves enough journal state for deterministic cleanup. A partial body is never reusable or publishable. Sibling streams and unrelated routes are isolated.

Proxy connection, tunnel, TLS, response, and cache layers are discharged by their owning boundary in inside-out order. Duplicate discharge is idempotent; out-of-order or foreign-owner discharge is rejected.

## Cache generations

Only a complete response may create a cache generation. Entries retain validators, request provenance, body digest, and source route generation. Revalidation may preserve a body while advancing validation metadata, replace it with a new complete body, or invalidate it. A stale revalidation result cannot overwrite a newer generation. Failed or cancelled transactions leave the previously committed entry visible.

## Publication, reopen, and reconciliation

Publishing a complete transaction creates a route-scoped generation linking request, response, cleanup, and optional cache evidence. `current`, `cached`, and `recover` are projections of one journal rather than independent stores. Reopening reconstructs the same records and detects malformed or digest-invalid journal data. Reconciliation checks cross-view references, generations, fences, budgets, and cache/publication ancestry; it reports a stable snapshot only when all invariants hold.

All failures specific to this module derive from `OrchestrationError`; conflict, ownership, budget, incomplete-state, and integrity failures are distinguishable subclasses. A failed operation is atomic.
