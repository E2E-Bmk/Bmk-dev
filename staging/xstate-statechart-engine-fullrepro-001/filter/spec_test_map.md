# spec_test_map — xstate-statechart-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::a machine interprets from a plain configuration object | atomic | positive | section Machine Definitions + section Actors And Snapshots | covered | XSTA-DEF-001, XSTA-ACT-001 |
| atomic::named guards resolve from the second createMachine argument | atomic | positive | section Machine Definitions + section Guards | covered | XSTA-DEF-002, XSTA-GRD-001 |
| atomic::provide returns a machine with overriding implementations | atomic | positive | section Machine Definitions | covered | XSTA-DEF-002 |
| atomic::setup binds named actions and guards with params | atomic | positive | section Machine Definitions + section Actions And Context + section Guards | covered | XSTA-DEF-002, XSTA-AXN-002, XSTA-GRD-001 |
| atomic::an invalid transition target throws at machine creation | atomic | failure_path | section Machine Definitions + section Error Semantics | covered | XSTA-DEF-004, XSTA-ERR-001 |
| atomic::a compound state without an initial key throws at machine creation | atomic | failure_path | section Machine Definitions + section Error Semantics | covered | XSTA-DEF-005, XSTA-ERR-002 |
| atomic::a context factory receives the actor input | atomic | positive | section Machine Definitions + section Actors And Snapshots | covered | XSTA-DEF-001, XSTA-ACT-007 |
| atomic::send transitions and updates the snapshot | atomic | positive | section Actors And Snapshots | covered | XSTA-ACT-002, XSTA-ACT-005 |
| atomic::event payload properties reach guards and actions | atomic | positive | section Actors And Snapshots + section Actions And Context | covered | XSTA-ACT-002, XSTA-AXN-003 |
| atomic::events with no matching transition are ignored | atomic | failure_path | section Actors And Snapshots + section Error Semantics | covered | XSTA-ACT-004, XSTA-ERR-003 |
| atomic::stop freezes the actor with a stopped status | atomic | failure_path | section Actors And Snapshots | covered | XSTA-ACT-003 |
| atomic::matches accepts full and partial state values | atomic | positive | section Actors And Snapshots + section Hierarchy, Parallel And History | covered | XSTA-ACT-006, XSTA-HPH-002 |
| atomic::can reports whether an event would select a transition | atomic | positive | section Actors And Snapshots + section Guards | covered | XSTA-ACT-006, XSTA-GRD-003 |
| atomic::hasTag reflects tags of active states | atomic | positive | section Actors And Snapshots | covered | XSTA-ACT-006 |
| atomic::matchesState tests refinement of plain state values | atomic | positive | section Actors And Snapshots | covered | XSTA-ACT-006 |
| atomic::a top-level leaf renders a string value and a compound renders an object | atomic | positive | section Actors And Snapshots + section Hierarchy, Parallel And History | covered | XSTA-ACT-005, XSTA-HPH-001 |
| atomic::each step returns a fresh snapshot object | atomic | positive | section Actors And Snapshots | covered | XSTA-ACT-005 |
| atomic::an exact descriptor matches its event type | atomic | positive | section Transition Selection | covered | XSTA-TRN-001 |
| atomic::descriptor specificity ranks exact over partial wildcard over star | atomic | positive | section Transition Selection | covered | XSTA-TRN-001 |
| atomic::candidates evaluate in document order with guard fall-through | atomic | positive | section Transition Selection | covered | XSTA-TRN-002 |
| atomic::an active child transition overrides the ancestor for the same event | atomic | positive | section Transition Selection | covered | XSTA-TRN-003 |
| atomic::an ancestor handles events no descendant handles | atomic | positive | section Transition Selection | covered | XSTA-TRN-003 |
| atomic::a bare string target names a sibling state | atomic | positive | section Transition Selection | covered | XSTA-TRN-004 |
| atomic::a dot-prefixed target names a child of the source | atomic | positive | section Transition Selection | covered | XSTA-TRN-004 |
| atomic::a hash-prefixed target resolves by absolute id | atomic | positive | section Transition Selection + section Machine Definitions | covered | XSTA-TRN-004, XSTA-DEF-003 |
| atomic::a targetless transition runs actions without changing state | atomic | positive | section Transition Selection | covered | XSTA-TRN-005 |
| atomic::a self-targeting transition does not re-enter by default | atomic | positive | section Transition Selection | covered | XSTA-TRN-006 |
| atomic::reenter true forces exit and re-entry of the source | atomic | positive | section Transition Selection | covered | XSTA-TRN-006 |
| atomic::always transitions resolve immediately on entry | atomic | positive | section Transition Selection | covered | XSTA-TRN-007 |
| atomic::raise enqueues an internal event processed before external events | atomic | positive | section Transition Selection | covered | XSTA-TRN-008 |
| atomic::multiple raised events process in first-in first-out order | atomic | positive | section Transition Selection | covered | XSTA-TRN-008 |
| atomic::actions run as exit then transition then entry | atomic | positive | section Actions And Context | covered | XSTA-AXN-001 |
| atomic::start runs entry actions from the machine node inward | atomic | positive | section Actors And Snapshots + section Actions And Context | covered | XSTA-ACT-001, XSTA-AXN-001 |
| atomic::assign accepts property updaters and plain values | atomic | positive | section Actions And Context | covered | XSTA-AXN-003 |
| atomic::assign accepts a single function returning partial context | atomic | positive | section Actions And Context | covered | XSTA-AXN-003 |
| atomic::sequential assigns each see the previous result | atomic | positive | section Actions And Context | covered | XSTA-AXN-003 |
| atomic::an exit assign is visible to transition and entry actions | atomic | positive | section Actions And Context | covered | XSTA-AXN-003, XSTA-AXN-001 |
| atomic::entry actions observe the event that caused the entry | atomic | positive | section Actions And Context | covered | XSTA-AXN-002 |
| atomic::raised event payloads reach the triggered transition | atomic | positive | section Actions And Context + section Transition Selection | covered | XSTA-AXN-004, XSTA-TRN-008 |
| atomic::an inline guard blocks the transition when false | atomic | positive | section Guards | covered | XSTA-GRD-001, XSTA-GRD-003 |
| atomic::guards read the event payload | atomic | positive | section Guards | covered | XSTA-GRD-001 |
| atomic::and or and not combine guards | atomic | positive | section Guards | covered | XSTA-GRD-002 |
| atomic::stateIn gates a transition on another parallel region | atomic | positive | section Guards + section Hierarchy, Parallel And History | covered | XSTA-GRD-002, XSTA-HPH-003 |
| atomic::stateIn accepts an absolute id string | atomic | positive | section Guards + section Machine Definitions | covered | XSTA-GRD-002, XSTA-DEF-003 |
| atomic::can returns false when every candidate is guarded off | atomic | positive | section Guards | covered | XSTA-GRD-003 |
| atomic::entering a compound state descends through initial defaults | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-001 |
| atomic::matches accepts every prefix of the active path | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-002 |
| atomic::a parallel state activates every region | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-003 |
| atomic::a finished region keeps its final key while others continue | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-004 |
| atomic::shallow history re-enters the remembered child through its initial defaults | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-005 |
| atomic::deep history restores the remembered leaf configuration | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-005 |
| atomic::history without a stored configuration enters the default initial path | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-005 |
| atomic::history memory updates on every parent exit | atomic | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-005 |
| atomic::a top-level final state completes the machine | atomic | positive | section Final States And Output | covered | XSTA-FIN-001 |
| atomic::a compound onDone fires when its child reaches final | atomic | positive | section Final States And Output | covered | XSTA-FIN-002 |
| atomic::a parallel onDone fires only when every region is final | atomic | positive | section Final States And Output + section Hierarchy, Parallel And History | covered | XSTA-FIN-002, XSTA-HPH-004 |
| atomic::a final state's output reaches onDone as event.output | atomic | positive | section Final States And Output | covered | XSTA-FIN-003 |
| atomic::machine output maps the completion event and defaults to undefined | atomic | positive | section Final States And Output | covered | XSTA-FIN-004 |
| atomic::toPromise resolves with the snapshot output at completion | atomic | positive | section Final States And Output | covered | XSTA-FIN-005 |
| atomic::an after transition fires at its threshold and not before | atomic | positive | section Timed Transitions | covered | XSTA-TMR-001, XSTA-TMR-002 |
| atomic::delays accumulate across several increments | atomic | positive | section Timed Transitions | covered | XSTA-TMR-002 |
| atomic::exiting a state cancels its pending timer | atomic | positive | section Timed Transitions | covered | XSTA-TMR-001 |
| atomic::re-entering a state re-arms its timer from zero | atomic | positive | section Timed Transitions | covered | XSTA-TMR-001 |
| atomic::one large increment advances a delayed chain by a single step | atomic | positive | section Timed Transitions | covered | XSTA-TMR-002 |
| atomic::getInitialSnapshot resolves the initial configuration and context | atomic | positive | section Pure Stepping And Persistence | covered | XSTA-PUR-001 |
| atomic::getInitialSnapshot passes input to the context factory | atomic | positive | section Pure Stepping And Persistence | covered | XSTA-PUR-001 |
| atomic::getNextSnapshot returns the successor without mutating its input | atomic | positive | section Pure Stepping And Persistence | covered | XSTA-PUR-001, XSTA-PUR-002 |
| atomic::pure steps apply assigns but never run side-effecting actions | atomic | positive | section Pure Stepping And Persistence | covered | XSTA-PUR-002 |
| atomic::pure steps process raised events and always transitions to quiescence | atomic | positive | section Pure Stepping And Persistence + section Transition Selection | covered | XSTA-PUR-001, XSTA-TRN-007, XSTA-TRN-008 |
| atomic::stepping a done snapshot keeps it done and unchanged | atomic | positive | section Pure Stepping And Persistence | covered | XSTA-PUR-003 |
| atomic::a persisted snapshot restores value and context in a new actor | atomic | positive | section Pure Stepping And Persistence | covered | XSTA-PUR-004 |
| integration::actor interpretation and pure stepping agree over a mixed event sequence | integration | positive | section Cross-View Invariants + section Pure Stepping And Persistence + section Transition Selection | covered | XSTA-INV-001, XSTA-PUR-001, XSTA-TRN-008; Seam: actor loop x pure step functions |
| integration::a false can implies the event leaves value and context unchanged | integration | positive | section Cross-View Invariants + section Guards + section Actors And Snapshots | covered | XSTA-INV-002, XSTA-GRD-003, XSTA-ACT-006; Seam: query surface x interpretation |
| integration::matches agrees with matchesState across a nested run | integration | positive | section Cross-View Invariants + section Actors And Snapshots + section Hierarchy, Parallel And History | covered | XSTA-INV-003, XSTA-ACT-006, XSTA-HPH-002; Seam: snapshot query x value utility |
| integration::a resumed actor continues exactly like the original | integration | positive | section Cross-View Invariants + section Pure Stepping And Persistence | covered | XSTA-INV-004, XSTA-PUR-004; Seam: persistence x interpretation |
| integration::a triage machine routes by combinator guards over payload and context | integration | positive | section Guards + section Transition Selection + section Actions And Context | covered | XSTA-GRD-002, XSTA-TRN-002, XSTA-AXN-003; Seam: guard combinators x candidate order x context |
| integration::provide swaps a named guard without touching the source machine | integration | positive | section Machine Definitions + section Guards | covered | XSTA-DEF-002, XSTA-GRD-001; Seam: implementation resolution x interpretation |
| integration::wildcard descriptors and child precedence route a hierarchical dispatcher | integration | positive | section Transition Selection | covered | XSTA-TRN-001, XSTA-TRN-003; Seam: descriptor matching x hierarchy |
| integration::raised events cascade through guards to a quiescent state | integration | positive | section Transition Selection + section Actions And Context | covered | XSTA-TRN-008, XSTA-AXN-004, XSTA-TRN-007; Seam: internal queue x guards x eventless transitions |
| integration::stateIn gates one region on another across a workflow | integration | positive | section Guards + section Hierarchy, Parallel And History | covered | XSTA-GRD-002, XSTA-HPH-003; Seam: parallel regions x cross-region guards |
| integration::regions finish independently and onDone fires only at full completion | integration | positive | section Hierarchy, Parallel And History + section Final States And Output | covered | XSTA-HPH-004, XSTA-FIN-002; Seam: parallel completion x final states |
| integration::independent timers in parallel regions fire from one simulated clock | integration | positive | section Timed Transitions + section Hierarchy, Parallel And History | covered | XSTA-TMR-001, XSTA-TMR-002, XSTA-HPH-003; Seam: delayed transitions x parallel regions |
| integration::shallow and deep history nodes in one parent restore different depths | integration | positive | section Hierarchy, Parallel And History | covered | XSTA-HPH-005; Seam: history resolution x nested hierarchy |
| integration::deep history memory survives a persistence round trip | integration | positive | section Hierarchy, Parallel And History + section Pure Stepping And Persistence | covered | XSTA-HPH-005, XSTA-PUR-004; Seam: history x persistence |
| integration::a reenter self-transition re-arms the timer while a plain one does not | integration | positive | section Transition Selection + section Timed Transitions | covered | XSTA-TRN-006, XSTA-TMR-001; Seam: self-transition semantics x timers |
| integration::an escalation ladder climbs one rung per accumulated threshold | integration | positive | section Timed Transitions + section Cross-View Invariants + section Actions And Context | covered | XSTA-TMR-002, XSTA-INV-005, XSTA-AXN-001; Seam: chained delays x entry actions |
| integration::final output routes through guarded onDone into machine output | integration | positive | section Final States And Output | covered | XSTA-FIN-003, XSTA-FIN-004, XSTA-FIN-002; Seam: final output x onDone guards x machine output |
| integration::toPromise observes a completion driven by raised events | integration | positive | section Final States And Output + section Transition Selection | covered | XSTA-FIN-005, XSTA-TRN-008; Seam: promise projection x internal queue |
| integration::input shapes context and the completion output derives from it | integration | positive | section Actors And Snapshots + section Final States And Output + section Actions And Context | covered | XSTA-ACT-007, XSTA-FIN-004, XSTA-AXN-003; Seam: input x context factory x output |
| integration::a pure fold reaches done with computed output | integration | positive | section Pure Stepping And Persistence + section Final States And Output | covered | XSTA-PUR-001, XSTA-PUR-003, XSTA-FIN-004; Seam: pure step x completion |
| integration::pure steps replay a raise pipeline applying assigns but no effects | integration | positive | section Pure Stepping And Persistence + section Transition Selection + section Actions And Context | covered | XSTA-PUR-002, XSTA-TRN-008, XSTA-AXN-004; Seam: pure step x internal queue x actions |
| integration::a restored snapshot answers tags, can and matches like the original | integration | positive | section Pure Stepping And Persistence + section Actors And Snapshots | covered | XSTA-PUR-004, XSTA-ACT-006; Seam: persistence x query surface |
| integration::an order fulfilment machine runs from input to completion across every projection | system_e2e | positive | section Actors And Snapshots + section Guards + section Actions And Context + section Hierarchy, Parallel And History + section Final States And Output | covered | XSTA-ACT-007, XSTA-GRD-001, XSTA-AXN-003, XSTA-HPH-001, XSTA-FIN-002, XSTA-FIN-004, XSTA-FIN-005, XSTA-ACT-006; Seam: input x guards x hierarchy x completion x promise |
| integration::a batch pipeline persists mid-flight and finishes on a simulated clock | system_e2e | positive | section Pure Stepping And Persistence + section Cross-View Invariants + section Timed Transitions + section Final States And Output | covered | XSTA-PUR-004, XSTA-INV-004, XSTA-TMR-001, XSTA-TMR-002, XSTA-FIN-004; Seam: persistence x timers x completion |
| integration::a launch checklist coordinates parallel regions, timers and completion output | system_e2e | positive | section Hierarchy, Parallel And History + section Guards + section Timed Transitions + section Final States And Output | covered | XSTA-HPH-003, XSTA-GRD-002, XSTA-TMR-001, XSTA-FIN-002, XSTA-FIN-003, XSTA-FIN-004; Seam: parallel x stateIn x timers x completion |
| integration::pure stepping replays an actor's full run to an identical terminal snapshot | system_e2e | positive | section Cross-View Invariants + section Pure Stepping And Persistence + section Final States And Output | covered | XSTA-INV-001, XSTA-PUR-001, XSTA-PUR-003, XSTA-FIN-004; Seam: pure step x actor loop x completion |

Total: 96 | kept (covered): 96 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 96

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
