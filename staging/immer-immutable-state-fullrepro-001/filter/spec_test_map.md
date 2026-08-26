# spec_test_map — immer-immutable-state-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-26

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::producing state::produce returns the next state and never mutates the base | atomic | positive | section Producing State | covered | IMM-PROD-001 |
| atomic::producing state::a recipe that changes nothing returns the base by reference | atomic | positive | section Producing State | covered | IMM-PROD-002 |
| atomic::producing state::changed branches are new objects while untouched branches keep identity | atomic | positive | section Producing State | covered | IMM-PROD-003 |
| atomic::producing state::primitive and null bases pass through the producer | atomic | positive | section Producing State | covered | IMM-PROD-004 |
| atomic::producing state::producing over a non-draftable object base throws | atomic | failure_path | section Producing State + section Error Semantics | covered | IMM-PROD-005 |
| atomic::producing state::produced results are deeply frozen by default and reject strict-mode mutation | atomic | positive | section Producing State + section Error Semantics | covered | IMM-PROD-009 |
| atomic::producing state::a pre-frozen base is a legal input | atomic | positive | section Producing State | covered | IMM-PROD-010 |
| atomic::producing state::nested reads inside a recipe are drafts and mutations are visible immediately | atomic | positive | section Producing State | covered | IMM-PROD-011, IMM-LIFE-006 |
| atomic::producing state::a draft that escapes its recipe is revoked | atomic | failure_path | section Producing State + section Error Semantics | covered | IMM-PROD-012 |
| atomic::producing state::nested produce composes with the outer draft | atomic | positive | section Producing State | covered | IMM-PROD-013 |
| atomic::recipe return rules::returning undefined finalizes the draft | atomic | positive | section Producing State | covered | IMM-PROD-006 |
| atomic::recipe return rules::returning a fresh value replaces the state | atomic | positive | section Producing State | covered | IMM-PROD-014 |
| atomic::recipe return rules::returning the modified draft itself is allowed | atomic | positive | section Producing State | covered | IMM-PROD-006 |
| atomic::recipe return rules::modifying the draft and returning a new value throws | atomic | failure_path | section Producing State + section Error Semantics | covered | IMM-PROD-007 |
| atomic::recipe return rules::returning a promise while modifying the draft throws | atomic | failure_path | section Producing State + section Error Semantics + section Non-Goals | covered | IMM-PROD-007 |
| atomic::recipe return rules::returning nothing produces undefined | atomic | positive | section Producing State | covered | IMM-PROD-008 |
| atomic::curried producers::currying returns a reusable producer that forwards extra arguments | atomic | positive | section Curried Producers | covered | IMM-CURRY-001, IMM-CURRY-002 |
| atomic::curried producers::a curried producer with a default state uses it for an undefined base | atomic | positive | section Curried Producers | covered | IMM-CURRY-003 |
| atomic::curried producers::an explicit base overrides the curried default | atomic | positive | section Curried Producers | covered | IMM-CURRY-003 |
| atomic::curried producers::curried produceWithPatches returns the state-and-patches triple | atomic | positive | section Curried Producers + section Patches | covered | IMM-CURRY-004 |
| atomic::manual draft lifecycle::createDraft opens a live draft that records mutations | atomic | positive | section Draft Lifecycle And Inspection | covered | IMM-LIFE-001 |
| atomic::manual draft lifecycle::finishDraft finalizes with produce identity, sharing, and freezing rules | atomic | positive | section Draft Lifecycle And Inspection | covered | IMM-LIFE-002 |
| atomic::manual draft lifecycle::finishDraft reports patches through its listener | atomic | positive | section Draft Lifecycle And Inspection + section Patches | covered | IMM-LIFE-003 |
| atomic::manual draft lifecycle::a finished draft is revoked | atomic | failure_path | section Draft Lifecycle And Inspection + section Error Semantics | covered | IMM-LIFE-004 |
| atomic::manual draft lifecycle::createDraft and finishDraft reject invalid arguments | atomic | failure_path | section Draft Lifecycle And Inspection + section Error Semantics | covered | IMM-LIFE-005 |
| atomic::snapshots and originals::current returns an unfrozen finalized snapshot of the draft so far | atomic | positive | section Draft Lifecycle And Inspection | covered | IMM-LIFE-007 |
| atomic::snapshots and originals::a snapshot is decoupled from later draft mutations | atomic | positive | section Draft Lifecycle And Inspection | covered | IMM-LIFE-007 |
| atomic::snapshots and originals::current on a non-draft throws | atomic | failure_path | section Draft Lifecycle And Inspection + section Error Semantics | covered | IMM-LIFE-008 |
| atomic::snapshots and originals::original returns the underlying base with reference identity | atomic | positive | section Draft Lifecycle And Inspection | covered | IMM-LIFE-010 |
| atomic::snapshots and originals::original on a non-draft throws | atomic | failure_path | section Draft Lifecycle And Inspection + section Error Semantics | covered | IMM-LIFE-011 |
| atomic::snapshots and originals::symbol-keyed children stay drafts in snapshots unless strict iteration is on | atomic | positive | section Draft Lifecycle And Inspection + section Configuration | covered | IMM-LIFE-009, IMM-CFG-005 |
| atomic::draftability and freezing::isDraftable accepts plain objects, arrays, maps, sets, and null-prototype objects | atomic | positive | section Draftability And Freezing | covered | IMM-DRAFT-001 |
| atomic::draftability and freezing::the immerable marker makes class instances draftable with prototypes preserved | atomic | positive | section Draftability And Freezing | covered | IMM-DRAFT-002, IMM-DRAFT-003 |
| atomic::draftability and freezing::marking the prototype works the same as marking the class | atomic | positive | section Draftability And Freezing | covered | IMM-DRAFT-002 |
| atomic::draftability and freezing::an unmarked class instance is not draftable | atomic | failure_path | section Draftability And Freezing + section Error Semantics | covered | IMM-DRAFT-001, IMM-PROD-005 |
| atomic::draftability and freezing::freeze is shallow by default and deep on request | atomic | positive | section Draftability And Freezing | covered | IMM-DRAFT-004 |
| atomic::draftability and freezing::cast helpers return their argument unchanged | atomic | positive | section Draftability And Freezing | covered | IMM-DRAFT-005 |
| atomic::patch records::object mutations record add, replace, and remove operations | atomic | positive | section Patches | covered | IMM-PATCH-002, IMM-PATCH-003 |
| atomic::patch records::array appends record add patches at the new indices | atomic | positive | section Patches | covered | IMM-PATCH-004 |
| atomic::patch records::array length truncation records remove patches for dropped indices | atomic | positive | section Patches | covered | IMM-PATCH-004 |
| atomic::patch records::splice records patches that round-trip | atomic | positive | section Patches + section Cross-View Invariants | covered | IMM-PATCH-003, IMM-CVI-001 |
| atomic::patch records::replacing the whole state records one empty-path replace patch | atomic | positive | section Patches | covered | IMM-PATCH-006 |
| atomic::patch records::producing undefined via nothing records an empty-path replace with undefined | atomic | positive | section Patches | covered | IMM-PATCH-006 |
| atomic::patch records::the patch listener of produce sees the same streams as produceWithPatches | atomic | positive | section Patches + section Cross-View Invariants | covered | IMM-PATCH-007, IMM-CVI-004 |
| atomic::patch records::a production that changes nothing emits empty patch streams | atomic | positive | section Patches + section Cross-View Invariants | covered | IMM-CVI-003 |
| atomic::patch application::applyPatches builds a new frozen state and leaves the base untouched | atomic | positive | section Patches | covered | IMM-PATCH-008 |
| atomic::patch application::add on an array index inserts and the dash index appends | atomic | positive | section Patches | covered | IMM-PATCH-009 |
| atomic::patch application::an empty-path replace substitutes the whole state | atomic | positive | section Patches | covered | IMM-PATCH-010 |
| atomic::patch application::removing a missing key is a no-op | atomic | positive | section Patches | covered | IMM-PATCH-011 |
| atomic::patch application::an unresolvable path throws | atomic | failure_path | section Patches + section Error Semantics | covered | IMM-PATCH-012 |
| atomic::patch application::an unsupported op throws | atomic | failure_path | section Patches + section Error Semantics | covered | IMM-PATCH-012 |
| atomic::patch application::applying patches to a live draft mutates it in place and returns it | atomic | positive | section Patches | covered | IMM-PATCH-013 |
| atomic::map and set drafts::map drafts support reads, writes, deletes, and clear while the base stays intact | atomic | positive | section Map And Set Drafts | covered | IMM-MAPSET-002 |
| atomic::map and set drafts::map get returns drafts so nested mutation is recorded | atomic | positive | section Map And Set Drafts | covered | IMM-MAPSET-003 |
| atomic::map and set drafts::finalized maps preserve insertion order and are instances of Map | atomic | positive | section Map And Set Drafts | covered | IMM-MAPSET-004 |
| atomic::map and set drafts::a finalized frozen map rejects mutation | atomic | positive | section Map And Set Drafts + section Error Semantics | covered | IMM-MAPSET-004 |
| atomic::map and set drafts::map and set productions that change nothing return the base | atomic | positive | section Map And Set Drafts | covered | IMM-MAPSET-005 |
| atomic::map and set drafts::set drafts record membership changes without touching the base | atomic | positive | section Map And Set Drafts | covered | IMM-MAPSET-006 |
| atomic::map and set drafts::iterating a set draft yields drafts whose mutations are recorded | atomic | positive | section Map And Set Drafts | covered | IMM-MAPSET-006 |
| atomic::map and set drafts::map patches are keyed by map key and round-trip | atomic | positive | section Map And Set Drafts + section Patches | covered | IMM-MAPSET-007 |
| atomic::map and set drafts::current and original work on map drafts | atomic | positive | section Map And Set Drafts + section Draft Lifecycle And Inspection | covered | IMM-MAPSET-009 |
| atomic::array methods plugin::search callbacks receive stored values, not fresh drafts | atomic | positive | section Array Methods Plugin | covered | IMM-ARR-002 |
| atomic::array methods plugin::find returns a draft whose mutation is recorded | atomic | positive | section Array Methods Plugin | covered | IMM-ARR-003 |
| atomic::array methods plugin::filter and slice return arrays of drafts | atomic | positive | section Array Methods Plugin | covered | IMM-ARR-003 |
| atomic::array methods plugin::concat and flat return non-draft structures | atomic | positive | section Array Methods Plugin | covered | IMM-ARR-004 |
| atomic::array methods plugin::primitive-returning methods yield ordinary values | atomic | positive | section Array Methods Plugin | covered | IMM-ARR-005 |
| atomic::array methods plugin::mutating methods behave like the standard implementations | atomic | positive | section Array Methods Plugin | covered | IMM-ARR-006 |
| atomic::configuration::setAutoFreeze disables freezing of later productions | atomic | positive | section Configuration | covered | IMM-CFG-001 |
| atomic::configuration::loose copying drops non-enumerable own properties and flattens getters | atomic | positive | section Configuration | covered | IMM-CFG-002 |
| atomic::configuration::strict copying preserves non-enumerable own properties | atomic | positive | section Configuration | covered | IMM-CFG-003 |
| atomic::configuration::class_only strict copying applies to marked classes but not plain objects | atomic | positive | section Configuration | covered | IMM-CFG-004 |
| atomic::configuration::an Immer instance isolates autoFreeze from the package-level engine | atomic | positive | section Configuration | covered | IMM-CFG-006, IMM-CFG-007 |
| atomic::configuration::an Immer instance exposes the full production surface with its own config | atomic | positive | section Configuration | covered | IMM-CFG-006 |
| atomic::plugin gating::produceWithPatches throws before the patches plugin is loaded | atomic | failure_path | section Patches + section Map And Set Drafts + section Error Semantics | covered | IMM-PATCH-001 |
| atomic::plugin gating::applyPatches throws before the patches plugin is loaded | atomic | failure_path | section Patches + section Map And Set Drafts + section Error Semantics | covered | IMM-PATCH-001 |
| atomic::plugin gating::a patch listener on produce throws before the patches plugin is loaded | atomic | failure_path | section Patches + section Map And Set Drafts + section Error Semantics | covered | IMM-PATCH-001 |
| atomic::plugin gating::producing over a Map throws before the map-set plugin is loaded | atomic | failure_path | section Patches + section Map And Set Drafts + section Error Semantics | covered | IMM-MAPSET-001 |
| atomic::plugin gating::producing over a Set throws before the map-set plugin is loaded | atomic | failure_path | section Patches + section Map And Set Drafts + section Error Semantics | covered | IMM-MAPSET-001 |
| atomic::plugin gating::without the array-methods plugin search callbacks receive drafts | atomic | positive | section Array Methods Plugin | covered | IMM-ARR-001 |
| integration::plugin gating across projections::every patch and container entry point gates on its plugin uniformly | integration | failure_path | section Cross-View Invariants + section Error Semantics | covered | IMM-CVI-005, IMM-PATCH-001, IMM-MAPSET-001 |
| integration::immutable update workflows::a store evolves through produce steps with sharing preserved at every step | integration | positive | section Producing State + section State Model | covered | IMM-PROD-002, IMM-PROD-003 |
| integration::immutable update workflows::inverse patches implement undo and forward patches implement redo | integration | positive | section Patches + section Cross-View Invariants | covered | IMM-CVI-001 |
| integration::immutable update workflows::patch replay composes with an open manual draft | integration | positive | section Patches + section Draft Lifecycle And Inspection | covered | IMM-PATCH-013, IMM-LIFE-003 |
| integration::immutable update workflows::curried producers drive a reducer loop | integration | positive | section Curried Producers + section Producing State | covered | IMM-CURRY-002, IMM-PROD-009 |
| integration::immutable update workflows::a marked class graph produces new instances with prototypes and patches intact | integration | positive | section Draftability And Freezing + section Patches | covered | IMM-DRAFT-003, IMM-CVI-001 |
| integration::immutable update workflows::nested containers draft through map values into sets | integration | positive | section Map And Set Drafts | covered | IMM-MAPSET-003, IMM-MAPSET-006 |
| integration::immutable update workflows::array-method mutations are recorded as patches that replay | integration | positive | section Array Methods Plugin + section Patches | covered | IMM-ARR-003, IMM-CVI-001 |
| integration::immutable update workflows::a nested produce precomputes a branch that outer patches capture | integration | positive | section Producing State + section Patches | covered | IMM-PROD-013, IMM-CVI-001 |
| integration::immutable update workflows::producing nothing round-trips through patches on optional state | integration | positive | section Producing State + section Patches | covered | IMM-PROD-008, IMM-PATCH-006, IMM-PATCH-010 |
| integration::immutable update workflows::class_only strict copying differentiates classes from plain objects in one tree | integration | positive | section Configuration + section Draftability And Freezing | covered | IMM-CFG-004 |
| integration::immutable update workflows::manual drafts and producers work independently over one base | integration | positive | section Draft Lifecycle And Inspection + section Producing State | covered | IMM-LIFE-001, IMM-LIFE-002, IMM-PROD-003 |
| integration::immutable update workflows::a patch log replays onto a diverged base when its paths still resolve | integration | positive | section Patches | covered | IMM-PATCH-008, IMM-PATCH-009 |
| integration::immutable update workflows::primitive set membership flows through snapshots and patches | integration | positive | section Map And Set Drafts + section Draft Lifecycle And Inspection + section Patches | covered | IMM-MAPSET-006, IMM-LIFE-007, IMM-MAPSET-008 |
| integration::immutable update workflows::a marked class with container fields drafts through both plugins | integration | positive | section Draftability And Freezing + section Map And Set Drafts | covered | IMM-DRAFT-003, IMM-MAPSET-003, IMM-MAPSET-006 |
| integration::immutable update workflows::map productions share untouched values by reference | integration | positive | section Map And Set Drafts + section Producing State | covered | IMM-PROD-003, IMM-MAPSET-007 |
| integration::cross-view invariants::patches and inverse patches round-trip one mixed production | integration | positive | section Cross-View Invariants | covered | IMM-CVI-001 |
| integration::cross-view invariants::mid-recipe snapshots equal the eventual finalization | integration | positive | section Cross-View Invariants | covered | IMM-CVI-002 |
| integration::cross-view invariants::no effective change means base identity and empty patches in every projection | integration | positive | section Cross-View Invariants | covered | IMM-CVI-003 |
| integration::cross-view invariants::listener streams equal the produceWithPatches triple for a complex change set | integration | positive | section Cross-View Invariants | covered | IMM-CVI-004 |
| integration::cross-view invariants::freezing follows the finalizing engine's configuration in all projections | integration | positive | section Cross-View Invariants | covered | IMM-CVI-006 |
| integration::cross-view invariants::no live drafts leak into results, snapshots, or patch values | integration | positive | section Cross-View Invariants | covered | IMM-CVI-007 |
| integration::end to end::a document editing session with staged patches, undo, and redo | system_e2e | positive | section State Model + section Cross-View Invariants | covered | IMM-LIFE-001..004, IMM-CVI-001 |
| integration::end to end::a mixed-container store replays its full patch log onto the original base | system_e2e | positive | section State Model + section Cross-View Invariants | covered | IMM-CVI-001, IMM-MAPSET-007, IMM-DRAFT-003 |
| integration::end to end::two engines process one base with configuration-scoped results that interoperate | system_e2e | positive | section State Model + section Cross-View Invariants | covered | IMM-CFG-007, IMM-CVI-006, IMM-PROD-010 |

Total: 104 | kept (covered): 104 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 104
