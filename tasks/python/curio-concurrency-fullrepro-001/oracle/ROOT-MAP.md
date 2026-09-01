# Curio v7 root and dependency map

The evaluator has 60 independent roots: 20 Atomic, 32 Integration, and 8
System/E2E.  There are 42 preregistered synthetic roots (10 Atomic, 24
Integration, 8 System/E2E).  Parameter cases remain inside their behavioral
root and do not add weight.

| Root | Layer | Capability or seam | depends_on | Mutation |
|---|---|---|---|---|
| A01 | Atomic | run exact value and exact top-level failure | - | - |
| A02 | Atomic | spawned task join result | - | - |
| A03 | Atomic | TaskError exact child cause | - | - |
| A04 | Atomic | explicit cancellation object identity | - | - |
| A05 | Atomic | Event set/clear lifecycle | - | - |
| A06 | Atomic | Queue FIFO and unfinished obligations | - | - |
| A07 | Atomic | Lock ownership projection | - | - |
| A08 | Atomic | zero timeout expiry | - | - |
| A09 | Atomic | UniversalQueue thread visibility | - | - |
| A10 | Atomic | Result unwrap value and error | - | - |
| A11 | Atomic | real socket fd and one framed transfer | - | M-SOCKET |
| A12 | Atomic | socket send-half EOF with reverse direction open | - | M-SOCKET |
| A13 | Atomic | directional frame-credit backpressure projection | - | M-SOCKET |
| A14 | Atomic | bounded pool executes in a real thread | - | M-WORKER |
| A15 | Atomic | worker cancellation publication and late result retirement | - | M-WORKER |
| A16 | Atomic | worker admission captures TaskLocal context | - | M-WORKER,M-CONTEXT |
| A17 | Atomic | default task context inheritance and sibling isolation | - | M-CONTEXT |
| A18 | Atomic | async generator finalizes once | - | M-FINALIZE |
| A19 | Atomic | resource stack LIFO and one-shot close | - | M-CLEANUP |
| A20 | Atomic | workflow id, lease, ack, result, and snapshot | - | M-WORKFLOW |
| I01 | Integration | TaskGroup child results after structured exit | A02 | - |
| I02 | Integration | cancelled Event waiter followed by reuse | A04,A05 | - |
| I03 | Integration | cancelled bounded Queue put leaves no ghost | A04,A06 | - |
| I04 | Integration | thread-to-Curio UniversalQueue transfer and ack | A06,A09 | - |
| I05 | Integration | pending cancellation crosses a cancellation mask | A04,A08 | - |
| I06 | Integration | child failure waits sibling finalizer and preserves identity | A03,A05 | - |
| I07 | Integration | run_in_thread returns ordinary worker result | A02 | - |
| I08 | Integration | explicit ContextTask child snapshot isolation | A02 | - |
| I09 | Integration | duplex socket frames keep directions independent | A11 | M-SOCKET |
| I10 | Integration | multiple admitted frames drain before half-close EOF | A11,A12 | M-SOCKET |
| I11 | Integration | cancelled receive followed by receive-generation restart | A04,A11 | M-SOCKET |
| I12 | Integration | cancelled backpressured sender commits no ghost frame | A04,A13 | M-SOCKET |
| I13 | Integration | receive teardown wakes blocked peer sender as broken | A13 | M-SOCKET |
| I14 | Integration | receive restart advances generation without replacing fd | A11 | M-SOCKET |
| I15 | Integration | TaskGroup request/response relay over one duplex socket | A02,A11 | M-SOCKET |
| I16 | Integration | resource stack closes both real socket endpoints | A11,A19 | M-SOCKET,M-CLEANUP |
| I17 | Integration | pool limit backpressures submitter until slot retirement | A14 | M-WORKER |
| I18 | Integration | cancelled worker's late value cannot replace publication | A15 | M-WORKER |
| I19 | Integration | worker failure is wrapped with exact cause | A14 | M-WORKER |
| I20 | Integration | worker observes admission context, not later caller update | A16 | M-WORKER,M-CONTEXT |
| I21 | Integration | job ownership persists until pool close | A14 | M-WORKER |
| I22 | Integration | pool close waits for a retiring real thread | A15 | M-WORKER |
| I23 | Integration | closed pool restarts in a new generation | A14 | M-WORKER |
| I24 | Integration | UniversalQueue item is transformed by bounded worker and acked | A09,A14 | M-WORKER |
| I25 | Integration | nested TaskLocal bindings restore across isolated siblings | A17 | M-CONTEXT |
| I26 | Integration | explicit immutable context snapshot overrides worker caller | A16 | M-CONTEXT,M-WORKER |
| I27 | Integration | task cancellation triggers generator-scope finalization | A04,A18 | M-FINALIZE |
| I28 | Integration | nested generator registrations finalize in reverse order and context | A17,A18 | M-CONTEXT,M-FINALIZE |
| I29 | Integration | multiple generator failures aggregate in attempt order | A18 | M-FINALIZE |
| I30 | Integration | TaskGroup child failure waits sibling generator finalizer | A03,A18 | M-FINALIZE |
| I31 | Integration | socket request crosses worker and returns on reverse direction | A11,A14 | M-SOCKET,M-WORKER |
| I32 | Integration | retired workflow lease retries through worker and publishes once | A14,A20 | M-WORKER,M-WORKFLOW |
| S01 | System/E2E | foreign submit -> lease -> socket -> worker -> result -> cleanup | A09,A11,A14,A19,A20 | M-SOCKET,M-WORKER,M-CLEANUP,M-WORKFLOW |
| S02 | System/E2E | backpressure cancellation -> receive restart -> worker recovery | A11,A13,A14,A18 | M-SOCKET,M-WORKER,M-FINALIZE |
| S03 | System/E2E | worker cancellation -> late retirement -> lease retry -> socket response | A11,A15,A20 | M-SOCKET,M-WORKER,M-WORKFLOW |
| S04 | System/E2E | nested task context -> failed supervisor -> generator/resource cleanup | A03,A17,A18,A19 | M-CONTEXT,M-FINALIZE,M-CLEANUP |
| S05 | System/E2E | TaskGroup framed pipeline -> bounded workers -> half-close drain | A11,A12,A14,A19 | M-SOCKET,M-WORKER,M-CLEANUP |
| S06 | System/E2E | asyncio-thread universal submit -> Curio worker -> coordinator result | A09,A14,A20 | M-WORKER,M-WORKFLOW |
| S07 | System/E2E | socket and pool shutdown complete before deterministic cleanup errors | A11,A14,A19 | M-SOCKET,M-WORKER,M-CLEANUP |
| S08 | System/E2E | failed generation retires lease and worker, restarts all surfaces once | A11,A15,A17,A18,A20 | M-SOCKET,M-WORKER,M-CONTEXT,M-FINALIZE,M-WORKFLOW |

For every composition row, a candidate can pass all named Atomic prerequisites
while failing the stated handoff, ordering, rollback, context, retirement, or
cross-view invariant.
