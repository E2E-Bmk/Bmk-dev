# spec_test_map — mobx-reactivity-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::a plain object converts to a new observable proxy reference | atomic | positive | section Observable State | covered | MOBX-OBS-001 |
| atomic::arrays convert to observable arrays that are still real arrays | atomic | positive | section Observable State | covered | MOBX-OBS-001 |
| atomic::maps and sets convert without being instanceof the built-ins | atomic | positive | section Observable State | covered | MOBX-OBS-001 |
| atomic::primitives convert to boxed observables | atomic | positive | section Observable State | covered | MOBX-OBS-001 |
| atomic::explicit factory forms and collection constructors agree with the predicates | atomic | positive | section Observable State | covered | MOBX-OBS-001 |
| atomic::conversion is deep by default | atomic | positive | section Observable State | covered | MOBX-OBS-002 |
| atomic::deep false keeps stored values unconverted | atomic | positive | section Observable State | covered | MOBX-OBS-002 |
| atomic::a box tracks reads and an equals comparer suppresses equal sets | atomic | positive | section Observable State | covered | MOBX-OBS-003 |
| atomic::adding a property by assignment is an observable structure change | atomic | positive | section Observable State | covered | MOBX-OBS-004 |
| atomic::the delete keyword removes a property reactively | atomic | positive | section Observable State | covered | MOBX-OBS-004 |
| atomic::a same-value write does not propagate | atomic | positive | section Observable State | covered | MOBX-OBS-006 |
| atomic::JSON serialization matches the plain counterpart | atomic | positive | section Observable State | covered | MOBX-OBS-006 |
| atomic::isObservableProp distinguishes observable members from plain ones | atomic | positive | section Observable State | covered | MOBX-OBS-005 |
| atomic::makeObservable wires fields, getters and methods per the annotation map | atomic | positive | section Class Annotations | covered | MOBX-ANN-001 |
| atomic::observableRef tracks reassignment only and never converts the value | atomic | positive | section Class Annotations | covered | MOBX-ANN-001 |
| atomic::observableShallow converts one level only | atomic | positive | section Class Annotations | covered | MOBX-ANN-001 |
| atomic::observableStruct suppresses structurally equal reassignment | atomic | positive | section Class Annotations | covered | MOBX-ANN-001 |
| atomic::makeAutoObservable infers members and honors false overrides | atomic | positive | section Class Annotations | covered | MOBX-ANN-002 |
| atomic::makeAutoObservable rejects classes with a superclass | atomic | failure_path | section Class Annotations + section Error Semantics | covered | MOBX-ANN-003, MOBX-ERR-002 |
| atomic::actionBound methods survive detachment while plain action methods do not | atomic | positive | section Class Annotations | covered | MOBX-ANN-004 |
| atomic::a getter in an observable literal becomes computed | atomic | positive | section Class Annotations | covered | MOBX-ANN-005 |
| atomic::annotating a missing field or re-annotating an annotated member throws | atomic | failure_path | section Class Annotations + section Error Semantics | covered | MOBX-ANN-006, MOBX-ERR-002 |
| atomic::a computed is lazy until first read | atomic | positive | section Derived Values | covered | MOBX-CMP-002 |
| atomic::while observed a computed caches between dependency changes | atomic | positive | section Derived Values | covered | MOBX-CMP-002 |
| atomic::while unobserved a computed evaluates on every read | atomic | positive | section Derived Values | covered | MOBX-CMP-002 |
| atomic::a computed equals option cuts off propagation | atomic | positive | section Derived Values | covered | MOBX-CMP-003 |
| atomic::the four comparers implement their documented equality | atomic | positive | section Derived Values | covered | MOBX-CMP-003 |
| atomic::computedStruct compares results structurally in a class | atomic | positive | section Derived Values + section Class Annotations | covered | MOBX-CMP-003, MOBX-ANN-001 |
| atomic::a computed cycle raises an error at read | atomic | failure_path | section Derived Values + section Error Semantics | covered | MOBX-CMP-004, MOBX-ERR-001 |
| atomic::untracked reads do not create dependencies | atomic | positive | section Derived Values | covered | MOBX-CMP-005 |
| atomic::autorun runs immediately exactly once | atomic | positive | section Effects | covered | MOBX-EFF-001 |
| atomic::autorun re-runs on tracked changes and ignores untracked properties | atomic | positive | section Effects | covered | MOBX-EFF-001, MOBX-EFF-004 |
| atomic::autorun re-records dependencies from scratch on each run | atomic | positive | section Effects | covered | MOBX-EFF-001 |
| atomic::a disposed autorun never runs again | atomic | positive | section Effects + section Error Semantics | covered | MOBX-EFF-001, MOBX-EFF-004, MOBX-ERR-004 |
| atomic::reaction skips the initial run and passes new and old values | atomic | positive | section Effects | covered | MOBX-EFF-002 |
| atomic::fireImmediately runs the effect once with undefined as the previous value | atomic | positive | section Effects | covered | MOBX-EFF-002 |
| atomic::the reaction handle disposes from inside the effect | atomic | positive | section Effects | covered | MOBX-EFF-002 |
| atomic::a reaction equals option compares expression results | atomic | positive | section Effects | covered | MOBX-EFF-002 |
| atomic::when runs its effect exactly once and then disposes | atomic | positive | section Effects | covered | MOBX-EFF-003 |
| atomic::the when promise resolves when the predicate turns true | atomic | positive | section Effects | covered | MOBX-EFF-003 |
| atomic::cancelling a when promise rejects with WHEN_CANCELLED | atomic | failure_path | section Effects + section Error Semantics | covered | MOBX-EFF-003, MOBX-ERR-003 |
| atomic::an action batches several writes into one effect run | atomic | positive | section Actions And Batching | covered | MOBX-ACT-001 |
| atomic::unbatched writes propagate at each statement | atomic | positive | section Actions And Batching | covered | MOBX-ACT-001 |
| atomic::runInAction executes immediately, batches and returns the result | atomic | positive | section Actions And Batching | covered | MOBX-ACT-002, MOBX-ACT-001 |
| atomic::transaction batches without marking the function as an action | atomic | positive | section Actions And Batching | covered | MOBX-ACT-002 |
| atomic::nested actions flush once at the outermost end | atomic | positive | section Actions And Batching | covered | MOBX-ACT-001 |
| atomic::a net-reverted change suppresses reactions but re-runs autorun | atomic | positive | section Actions And Batching | covered | MOBX-ACT-001 |
| atomic::isAction distinguishes wrapped functions and names them | atomic | positive | section Actions And Batching | covered | MOBX-ACT-002 |
| atomic::an enforceActions violation warns and still applies the write | atomic | positive | section Actions And Batching + section Error Semantics | covered | MOBX-ACT-003, MOBX-ERR-004 |
| atomic::array index writes and length are tracked | atomic | positive | section Collections | covered | MOBX-COL-001 |
| atomic::out-of-bounds reads return undefined and writes extend the array | atomic | positive | section Collections | covered | MOBX-COL-001 |
| atomic::array search results are tracked | atomic | positive | section Collections | covered | MOBX-COL-001 |
| atomic::replace, remove, clear and splice return their documented values | atomic | positive | section Collections | covered | MOBX-COL-002 |
| atomic::map reads and size are tracked with Map semantics | atomic | positive | section Collections | covered | MOBX-COL-003 |
| atomic::map merge, replace and toJSON operate on entries | atomic | positive | section Collections | covered | MOBX-COL-003 |
| atomic::a has reader re-runs when the missing key appears | atomic | positive | section Collections | covered | MOBX-COL-003 |
| atomic::map iteration readers re-run on structural change | atomic | positive | section Collections | covered | MOBX-COL-003 |
| atomic::sets track membership and re-adding a present element is not a change | atomic | positive | section Collections | covered | MOBX-COL-004 |
| atomic::the generic collection API operates uniformly on objects | atomic | positive | section Collections | covered | MOBX-COL-005 |
| atomic::the generic collection API reaches arrays and maps too | atomic | positive | section Collections | covered | MOBX-COL-005 |
| atomic::a keys reader tracks structure changes | atomic | positive | section Collections + section Observable State | covered | MOBX-COL-005, MOBX-OBS-004 |
| atomic::object observers see update, add and remove events with their fields | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-001 |
| atomic::array observers see update and splice events | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-001 |
| atomic::map observers see add, update and delete events | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-001 |
| atomic::set observers see add and delete events | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-001 |
| atomic::box observers see update events | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-001 |
| atomic::a property observer fires only for its property | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-002 |
| atomic::an interceptor veto leaves no trace | atomic | positive | section Mutation Events And Interception + section Cross-View Invariants | covered | MOBX-EVT-003, MOBX-INV-003 |
| atomic::an interceptor rewrite stores the rewritten value | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-003 |
| atomic::a whole-object interceptor vetoes property additions | atomic | positive | section Mutation Events And Interception | covered | MOBX-EVT-003 |
| atomic::toJS produces deep plain data including built-in Map and Set | atomic | positive | section Snapshots And Introspection | covered | MOBX-SNP-001 |
| atomic::the predicate family classifies each kind and never throws on plain input | atomic | positive | section Snapshots And Introspection | covered | MOBX-SNP-002 |
| atomic::isObservableProp and isComputedProp classify annotated members | atomic | positive | section Snapshots And Introspection | covered | MOBX-SNP-002 |
| atomic::hooks fire on every observer-count transition | atomic | positive | section Observability Lifecycle | covered | MOBX-LFC-001 |
| atomic::computed suspension is visible through its dependency's hooks | atomic | positive | section Observability Lifecycle + section Derived Values | covered | MOBX-LFC-001, MOBX-CMP-002 |
| integration::one mutation is reflected identically in every projection | integration | positive | section Cross-View Invariants + section Mutation Events And Interception + section Snapshots And Introspection | covered | MOBX-INV-001, MOBX-EVT-001, MOBX-SNP-001; Seam: effects x events x snapshots x generic views |
| integration::a comparer-equal write is invisible in every projection | integration | positive | section Cross-View Invariants + section Observable State + section Mutation Events And Interception | covered | MOBX-INV-002, MOBX-OBS-003, MOBX-EVT-001; Seam: comparers x effects x events |
| integration::a vetoed map addition never reaches computeds, effects or snapshots | integration | positive | section Cross-View Invariants + section Mutation Events And Interception + section Collections | covered | MOBX-INV-003, MOBX-EVT-003, MOBX-COL-003; Seam: interception x derivation x snapshots |
| integration::computed evaluation counts follow observation state and batching | integration | positive | section Cross-View Invariants + section Derived Values + section Actions And Batching | covered | MOBX-INV-004, MOBX-CMP-002, MOBX-ACT-001; Seam: derivation cache x actions |
| integration::nested actions flush once through a computed into a reaction | integration | positive | section Cross-View Invariants + section Actions And Batching + section Derived Values | covered | MOBX-INV-005, MOBX-ACT-001, MOBX-CMP-002; Seam: nested batching x derivation x reaction |
| integration::toJS snapshots serialize identically to the live store | integration | positive | section Cross-View Invariants + section Snapshots And Introspection | covered | MOBX-INV-006, MOBX-SNP-001; Seam: snapshots x live proxies |
| integration::disposal is total and the lifecycle hooks witness the release | integration | positive | section Cross-View Invariants + section Observability Lifecycle + section Effects | covered | MOBX-INV-007, MOBX-LFC-001, MOBX-EFF-004; Seam: effects x lifecycle hooks |
| integration::an explicit class store routes actions through computeds into reactions | integration | positive | section Class Annotations + section Derived Values + section Actions And Batching + section Effects | covered | MOBX-ANN-001, MOBX-CMP-002, MOBX-ACT-001, MOBX-EFF-002; Seam: annotations x derivation x batching x reaction |
| integration::an inferred store keeps working through a detached bound action | integration | positive | section Class Annotations + section Derived Values | covered | MOBX-ANN-002, MOBX-ANN-004, MOBX-CMP-002; Seam: inference x binding x derivation |
| integration::class property interception rewrites and audits through observe | integration | positive | section Mutation Events And Interception + section Class Annotations | covered | MOBX-EVT-002, MOBX-EVT-003, MOBX-ANN-001; Seam: interception x events x annotations |
| integration::a structural computed in the middle of a chain cuts propagation | integration | positive | section Derived Values + section Class Annotations | covered | MOBX-CMP-003, MOBX-CMP-002, MOBX-ANN-001; Seam: derivation chain x comparers |
| integration::a map catalog stays consistent across merge, replace, events and effects | integration | positive | section Collections + section Mutation Events And Interception + section Effects | covered | MOBX-COL-003, MOBX-EVT-001, MOBX-EFF-001; Seam: map API x events x effects |
| integration::an array pipeline aggregates through computed while events audit each step | integration | positive | section Collections + section Mutation Events And Interception + section Derived Values | covered | MOBX-COL-002, MOBX-EVT-001, MOBX-CMP-002; Seam: array extras x events x derivation |
| integration::when observes a threshold crossed by a batched action | integration | positive | section Effects + section Actions And Batching + section Derived Values | covered | MOBX-EFF-003, MOBX-ACT-001, MOBX-CMP-002; Seam: one-shot effects x batching x derivation |
| integration::deep stores react to nested mutation while shallow stores do not | integration | positive | section Observable State + section Effects + section Class Annotations | covered | MOBX-OBS-002, MOBX-EFF-001, MOBX-ANN-001; Seam: conversion depth x effects |
| integration::dynamic object shape flows through the generic API and the event stream | integration | positive | section Observable State + section Collections + section Mutation Events And Interception | covered | MOBX-OBS-004, MOBX-COL-005, MOBX-EVT-001; Seam: dynamic shape x generic views x events |
| integration::same-value writes across containers emit no events and no runs | integration | positive | section Observable State + section Collections + section Mutation Events And Interception | covered | MOBX-OBS-006, MOBX-COL-004, MOBX-EVT-001; Seam: change detection x containers x events |
| integration::untracked sections keep reaction expressions selective | integration | positive | section Derived Values + section Effects | covered | MOBX-CMP-005, MOBX-EFF-002; Seam: tracking exemption x reactions |
| integration::enforceActions observed only warns for writes to observed state | integration | positive | section Actions And Batching + section Effects | covered | MOBX-ACT-003, MOBX-EFF-001; Seam: write policy x observation state |
| integration::a self-disposing reaction stops mid-stream while observers keep auditing | integration | positive | section Effects + section Mutation Events And Interception | covered | MOBX-EFF-002, MOBX-EVT-001, MOBX-EFF-004; Seam: reaction lifecycle x event stream |
| integration::a structurally compared box coordinates events and lifecycle hooks | integration | positive | section Observable State + section Mutation Events And Interception + section Observability Lifecycle | covered | MOBX-OBS-003, MOBX-EVT-001, MOBX-LFC-001; Seam: comparers x events x lifecycle |
| integration::an inventory store lifecycle keeps every projection in agreement | system_e2e | positive | section Class Annotations + section Actions And Batching + section Derived Values + section Mutation Events And Interception + section Snapshots And Introspection + section Cross-View Invariants | covered | MOBX-ANN-001, MOBX-ACT-001, MOBX-CMP-002, MOBX-EVT-001, MOBX-SNP-001, MOBX-INV-001; Seam: annotations x actions x derivation x events x snapshots |
| integration::a guarded ledger enforces rules through interception while a promise watches the balance | system_e2e | positive | section Mutation Events And Interception + section Effects + section Actions And Batching + section Cross-View Invariants | covered | MOBX-EVT-003, MOBX-EVT-002, MOBX-EFF-003, MOBX-ACT-001, MOBX-INV-003; Seam: interception x events x one-shot effects x batching |
| integration::a catalog sync propagates one source of truth across map, set and array views | system_e2e | positive | section Collections + section Effects + section Actions And Batching + section Cross-View Invariants | covered | MOBX-COL-003, MOBX-COL-004, MOBX-EFF-002, MOBX-ACT-001, MOBX-INV-001; Seam: containers x reactions x batching |
| integration::a demand-driven cache suspends and resumes across observation cycles | system_e2e | positive | section Derived Values + section Observability Lifecycle + section Cross-View Invariants | covered | MOBX-CMP-002, MOBX-LFC-001, MOBX-CMP-005, MOBX-INV-004, MOBX-INV-007; Seam: derivation cache x lifecycle hooks x tracking exemption |

Total: 100 | kept (covered): 100 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 100

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
