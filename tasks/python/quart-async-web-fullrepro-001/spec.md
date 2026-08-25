# Recoverable Quart/ASGI workflow extension

`quart_workflow` adds durable coordination primitives for asynchronous Quart deployments. It does not replace Quart. The public module exports `WorkflowError`, `IntegrityError`, `OwnershipError`, `TransitionError`, `ConflictError`, immutable `Receipt`, `value`, six owner classes, and `QuartWorkflow`.

## Common receipts and persistence

Each owner is constructed with a filesystem root. A committed transition returns an immutable receipt carrying domain, logical key, operation identity, positive generation, owner, state, payload, ordered history, and a content digest. Reconstructing an owner at the same root must recover the same committed state.

Operation identifiers are idempotency keys. Repeating the same beginning operation returns the existing equivalent receipt; reusing it for different content is a conflict. A transition must compare its input with the current generation, reject altered or stale receipts, write atomically, and never damage the last committed value on failure. `current`, `recover`, and `verify` expose current state, operation recovery, and integrity checking. Recovery is owner-fenced.

## Lifespan supervision

`LifespanSupervisor.open(app, startup, shutdown, owner=..., operation_id=...)` validates unique startup components and a matching shutdown set. `started` accepts startup steps in declared order. `fail` records startup failure and begins compensation. `stopped` discharges only the reverse order of components that actually started. A fully started application may shut down normally; a partial startup compensates only entered components. Closing and failure remain recoverable.

## Context ownership

`ContextBroker.open(scope_id, kind, task_id, owner=..., operation_id=..., parent=None)` binds an app, request, or websocket scope to one asynchronous task, optionally recording a parent receipt digest. `assert_task` rejects use from another task. `handoff` creates a fresh generation for a new task and owner, fencing the prior view. `close` is permitted only to the bound task. Parent lineage survives reopen.

## Streaming response flow control

`StreamChannel.open(stream_id, window, owner=..., operation_id=...)` creates positive bounded credit. `send` records the exact chunk identity but cannot exceed unacknowledged credit. `acknowledge` advances delivered credit without treating enqueue as delivery. `cancel` is terminal for new sends and permits cleanup of outstanding chunks. `close` requires either all chunks acknowledged or explicit cancellation. Reopen preserves credit, cancellation, and chunk order.

## ASGI transcript

`ASGITranscript.open(exchange_id, scope_type, owner=..., operation_id=...)` supports HTTP, websocket, and lifespan scopes. `receive` and `send` enforce protocol-family event ordering. HTTP body cannot precede response start, a terminal body completes the response, disconnect is terminal, websocket accept/send/close remain distinct, and lifespan completion or failure remains distinct from the triggering receive. `close` requires a terminal protocol state. Event order and terminal state are durable.

## Sessions and blueprint routing

`SessionCoordinator.open(session_id, expected_generation, owner=..., operation_id=...)` admits staged work only against the current generation. `set` changes the staged mapping; `commit` makes it the committed generation and `rollback` discards staged values. Stale generations cannot overwrite newer work.

`BlueprintRouter.register(name, prefix, routes, errors, owner=..., operation_id=...)` stores a normalized route/method family and blueprint-local error handlers. `resolve(receipt, method, path)` returns blueprint identity and local path only from the current receipt. `error_handler` resolves the registered status owner. Re-registration creates a generation and fences old prefixes.

## Cross-owner workflows

`QuartWorkflow(root)` exposes the six owners. `begin(workflow_id, owner=..., operation_id=...)` creates one linked HTTP workflow with independent owner receipts. `succeed(parts, body=b"ok")` completes startup, context use, ASGI response, flow-controlled body delivery, session commit, context retirement, and reverse shutdown. `verify(parts)` requires every supplied receipt to be the unaltered current receipt of the matching owner.

Applications must also behave coherently when these primitives are composed manually: startup failure pairs with a lifespan failure response and compensation; disconnect cancels or rolls back unfinished work; request and websocket contexts do not leak across tasks; streamed response completion follows downstream acknowledgement; session changes commit only with a terminal response; blueprint error ownership stays local; owner handoff fences stale work; and fresh-process recovery resumes the same generation without duplicate delivery.

The design is deterministic for JSON-compatible payloads and bytes. It must preserve non-ASCII values, reject unsupported transitions without partial visibility, and must not derive behavior from test order or caller path names.
