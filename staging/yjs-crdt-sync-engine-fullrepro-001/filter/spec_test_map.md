# spec_test_map — yjs-crdt-sync-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-26

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::update exchange::a full update replays the document on a fresh replica | atomic | positive | section Update Exchange | covered | YJS-UPD-001, YJS-UPD-002 |
| atomic::update exchange::encoding against a state vector yields only the missing changes | atomic | positive | section Update Exchange | covered | YJS-UPD-001, YJS-UPD-003 |
| atomic::update exchange::encodeStateVector returns a binary version descriptor | atomic | positive | section Update Exchange | covered | YJS-UPD-003 |
| atomic::update exchange::applying the same update twice has no second effect | atomic | positive | section Update Exchange | covered | YJS-UPD-005 |
| atomic::update exchange::a malformed update payload throws | atomic | failure_path | section Update Exchange + section Error Semantics | covered | YJS-UPD-004, YJS-ERR-006 |
| atomic::update exchange::mergeUpdates combines payloads into one equivalent update | atomic | positive | section Update Exchange | covered | YJS-UPD-008 |
| atomic::update exchange::encodeStateVectorFromUpdate matches the source document's state vector | atomic | positive | section Update Exchange | covered | YJS-UPD-009 |
| atomic::update exchange::diffUpdate extracts the changes a state vector is missing | atomic | positive | section Update Exchange | covered | YJS-UPD-010 |
| atomic::update exchange::the v2 encoding replays identically | atomic | positive | section Update Exchange | covered | YJS-UPD-011 |
| atomic::update exchange::format conversions preserve replay in both directions | atomic | positive | section Update Exchange | covered | YJS-UPD-012 |
| atomic::events and observation::observe fires once per transaction with the event and transaction | atomic | positive | section Events And Observation | covered | YJS-EVT-001 |
| atomic::events and observation::unobserve stops event delivery | atomic | positive | section Events And Observation | covered | YJS-EVT-001 |
| atomic::events and observation::map events report add, update, and delete actions with old values | atomic | positive | section Events And Observation | covered | YJS-EVT-005 |
| atomic::events and observation::key records describe the net transaction effect from its start state | atomic | positive | section Events And Observation | covered | YJS-EVT-006 |
| atomic::events and observation::keysChanged names the affected keys | atomic | positive | section Events And Observation | covered | YJS-EVT-007 |
| atomic::events and observation::array events expose a retain/insert/delete delta | atomic | positive | section Events And Observation | covered | YJS-EVT-008, YJS-EVT-009 |
| atomic::events and observation::text events carry string inserts with attributes | atomic | positive | section Events And Observation | covered | YJS-EVT-008, YJS-EVT-009 |
| atomic::events and observation::reading changes or delta after the handler returns throws | atomic | failure_path | section Events And Observation + section Error Semantics | covered | YJS-EVT-004, YJS-ERR-007 |
| atomic::events and observation::a directly observed type reports itself with an empty path | atomic | positive | section Events And Observation | covered | YJS-EVT-003 |
| atomic::events and observation::transactions report origin and local for local edits | atomic | positive | section Events And Observation + section Documents And Root Types | covered | YJS-EVT-010, YJS-DOC-007 |
| atomic::undo and redo::canUndo and canRedo reflect stack availability | atomic | positive | section Undo And Redo | covered | YJS-UNDO-006 |
| atomic::undo and redo::undo reverts and redo restores content | atomic | positive | section Undo And Redo | covered | YJS-UNDO-005 |
| atomic::undo and redo::clear empties both stacks | atomic | positive | section Undo And Redo | covered | YJS-UNDO-006 |
| atomic::undo and redo::captureTimeout zero keeps each transaction as its own entry | atomic | positive | section Undo And Redo | covered | YJS-UNDO-003 |
| atomic::undo and redo::rapid edits merge into a single entry by default | atomic | positive | section Undo And Redo | covered | YJS-UNDO-003 |
| atomic::undo and redo::stopCapturing starts a fresh entry | atomic | positive | section Undo And Redo | covered | YJS-UNDO-004 |
| atomic::undo and redo::trackedOrigins limits tracking to the listed origins | atomic | positive | section Undo And Redo | covered | YJS-UNDO-001, YJS-UNDO-002 |
| atomic::undo and redo::by default only untagged transactions are tracked | atomic | positive | section Undo And Redo | covered | YJS-UNDO-002 |
| atomic::undo and redo::a new tracked edit clears the redo stack | atomic | positive | section Undo And Redo | covered | YJS-UNDO-007 |
| atomic::undo and redo::undoing map changes restores previous values | atomic | positive | section Undo And Redo | covered | YJS-UNDO-008 |
| atomic::undo and redo::multi-scope managers revert entries across their types | atomic | positive | section Undo And Redo | covered | YJS-UNDO-001 |
| atomic::snapshots::snapshots encode, decode, and compare by version | atomic | positive | section Snapshots | covered | YJS-SNAP-001, YJS-SNAP-002, YJS-SNAP-003 |
| atomic::snapshots::createDocFromSnapshot restores the captured content | atomic | positive | section Snapshots | covered | YJS-SNAP-004 |
| atomic::snapshots::restoring from a gc-enabled document throws | atomic | failure_path | section Snapshots + section Error Semantics | covered | YJS-SNAP-005, YJS-ERR-008 |
| atomic::snapshots::snapshotContainsUpdate distinguishes covered from uncovered updates | atomic | positive | section Snapshots | covered | YJS-SNAP-006 |
| atomic::relative positions::a position resolves to its index and anchored type | atomic | positive | section Relative Positions | covered | YJS-POS-001, YJS-POS-002 |
| atomic::relative positions::left-associated positions resolve at the same static index | atomic | positive | section Relative Positions | covered | YJS-POS-001 |
| atomic::relative positions::JSON round trips compare equal | atomic | positive | section Relative Positions | covered | YJS-POS-005 |
| atomic::relative positions::binary round trips resolve to the same absolute position | atomic | positive | section Relative Positions | covered | YJS-POS-006 |
| atomic::relative positions::resolving against an unrelated replica returns null | atomic | failure_path | section Relative Positions | covered | YJS-POS-002 |
| atomic::relative positions::a position whose anchor was deleted collapses to the removal point | atomic | positive | section Relative Positions | covered | YJS-POS-004 |
| atomic::documents::clientID is numeric and differs between instances | atomic | positive | section Documents And Root Types | covered | YJS-DOC-002 |
| atomic::documents::guid option is honored and defaults to a string | atomic | positive | section Documents And Root Types | covered | YJS-DOC-001, YJS-DOC-003 |
| atomic::documents::root accessors create on first access and cache the instance | atomic | positive | section Documents And Root Types | covered | YJS-DOC-004 |
| atomic::documents::re-declaring a root name with a different type throws | atomic | failure_path | section Documents And Root Types + section Error Semantics | covered | YJS-DOC-005, YJS-ERR-001 |
| atomic::documents::transact returns the callback's return value | atomic | positive | section Documents And Root Types | covered | YJS-DOC-006 |
| atomic::documents::a transaction batches mutations into one update event | atomic | positive | section Documents And Root Types | covered | YJS-DOC-006, YJS-DOC-010 |
| atomic::documents::nested transact calls flatten into the outer transaction | atomic | positive | section Documents And Root Types | covered | YJS-DOC-008 |
| atomic::documents::a transaction without effective change emits no update event | atomic | positive | section Documents And Root Types | covered | YJS-DOC-009, YJS-DOC-010 |
| atomic::documents::destroy emits the destroy event and flags the doc | atomic | positive | section Documents And Root Types | covered | YJS-DOC-012 |
| atomic::documents::off unregisters and once fires a single time | atomic | positive | section Documents And Root Types | covered | YJS-DOC-013 |
| atomic::shared maps::set returns the value and get reads it back | atomic | positive | section Shared Maps | covered | YJS-MAP-001 |
| atomic::shared maps::has, delete, and size track current entries | atomic | positive | section Shared Maps | covered | YJS-MAP-002 |
| atomic::shared maps::clear removes every entry | atomic | positive | section Shared Maps | covered | YJS-MAP-002 |
| atomic::shared maps::null values are preserved and distinct from absence | atomic | positive | section Shared Maps | covered | YJS-MAP-003 |
| atomic::shared maps::iterators visit every current entry exactly once | atomic | positive | section Shared Maps | covered | YJS-MAP-008 |
| atomic::shared maps::forEach passes value, key, and the map | atomic | positive | section Shared Maps | covered | YJS-MAP-008 |
| atomic::shared maps::toJSON converts nested shared types recursively | atomic | positive | section Shared Maps | covered | YJS-MAP-009 |
| atomic::shared maps::clone returns an unintegrated copy with the same entries | atomic | positive | section Shared Maps | covered | YJS-MAP-010 |
| atomic::shared maps::the constructor seeds entries from an iterable | atomic | positive | section Shared Maps | covered | YJS-MAP-011 |
| atomic::shared maps::pre-integration mutations become observable after insertion | atomic | positive | section Shared Maps | covered | YJS-MAP-012, YJS-MAP-013 |
| atomic::shared maps::inserting an integrated type at a second location throws | atomic | failure_path | section Shared Maps + section Error Semantics | covered | YJS-MAP-014, YJS-ERR-005 |
| atomic::shared maps::storing a function throws | atomic | failure_path | section Shared Maps + section Error Semantics | covered | YJS-MAP-007, YJS-ERR-004 |
| atomic::shared maps::plain objects and arrays replicate as plain deep-equal values | atomic | positive | section Shared Maps | covered | YJS-MAP-005 |
| atomic::shared maps::Uint8Array values replicate with identical bytes | atomic | positive | section Shared Maps | covered | YJS-MAP-006 |
| atomic::shared arrays::insert, push, and unshift place items in order | atomic | positive | section Shared Arrays | covered | YJS-ARR-001 |
| atomic::shared arrays::delete removes one item by default and a count when given | atomic | positive | section Shared Arrays | covered | YJS-ARR-002 |
| atomic::shared arrays::get and length address current items | atomic | positive | section Shared Arrays | covered | YJS-ARR-003 |
| atomic::shared arrays::slice returns end-exclusive plain-array copies | atomic | positive | section Shared Arrays | covered | YJS-ARR-003 |
| atomic::shared arrays::insert past the end throws | atomic | failure_path | section Shared Arrays + section Error Semantics | covered | YJS-ARR-004, YJS-ERR-002 |
| atomic::shared arrays::delete past the end throws | atomic | failure_path | section Shared Arrays + section Error Semantics | covered | YJS-ARR-004, YJS-ERR-003 |
| atomic::shared arrays::toArray and toJSON convert content, toJSON recursing into shared types | atomic | positive | section Shared Arrays | covered | YJS-ARR-005 |
| atomic::shared arrays::map, forEach, and iteration walk items in index order | atomic | positive | section Shared Arrays | covered | YJS-ARR-006 |
| atomic::shared arrays::Array.from seeds a standalone array | atomic | positive | section Shared Arrays | covered | YJS-ARR-007 |
| atomic::shared arrays::nested standalone types integrate through array insertion | atomic | positive | section Shared Arrays | covered | YJS-ARR-008 |
| atomic::shared text::insert places text at a character index | atomic | positive | section Shared Text | covered | YJS-TXT-001 |
| atomic::shared text::insert beyond the current length appends at the end | atomic | positive | section Shared Text | covered | YJS-TXT-001 |
| atomic::shared text::delete removes a range and clamps past the end | atomic | positive | section Shared Text | covered | YJS-TXT-002 |
| atomic::shared text::format applies attributes visible in toDelta | atomic | positive | section Shared Text | covered | YJS-TXT-003, YJS-TXT-007 |
| atomic::shared text::formatting with a null value removes the attribute | atomic | positive | section Shared Text | covered | YJS-TXT-003 |
| atomic::shared text::insert accepts attributes for the inserted run | atomic | positive | section Shared Text | covered | YJS-TXT-001, YJS-TXT-007 |
| atomic::shared text::embeds occupy one length unit and are skipped by toString | atomic | positive | section Shared Text | covered | YJS-TXT-004, YJS-TXT-005, YJS-TXT-006 |
| atomic::shared text::toJSON returns the same string as toString | atomic | positive | section Shared Text | covered | YJS-TXT-006 |
| atomic::shared text::adjacent runs with identical formatting merge into one op | atomic | positive | section Shared Text | covered | YJS-TXT-007 |
| atomic::shared text::applyDelta inserts plain and formatted runs | atomic | positive | section Shared Text | covered | YJS-TXT-008 |
| atomic::shared text::applyDelta retain and delete edit existing content | atomic | positive | section Shared Text | covered | YJS-TXT-008, YJS-TXT-009 |
| atomic::shared text::applyDelta retain with attributes formats the retained range | atomic | positive | section Shared Text | covered | YJS-TXT-008 |
| atomic::shared text::a seeded standalone text materializes on integration | atomic | positive | section Shared Text | covered | YJS-TXT-010 |
| integration::replica convergence::bidirectional update exchange converges text replicas | integration | positive | section Cross-View Invariants + section Shared Text | covered | YJS-CVI-001, YJS-TXT-011 |
| integration::replica convergence::concurrent same-position text inserts stay intact and converge | integration | positive | section Shared Text + section Cross-View Invariants | covered | YJS-TXT-011, YJS-CVI-001 |
| integration::replica convergence::concurrent map writes converge on one of the written values | integration | positive | section Shared Maps | covered | YJS-MAP-004 |
| integration::replica convergence::concurrent array insertions preserve every item exactly once | integration | positive | section Shared Arrays + section Cross-View Invariants | covered | YJS-ARR-009, YJS-CVI-001 |
| integration::replica convergence::an update with missing dependencies is buffered until they arrive | integration | positive | section Update Exchange | covered | YJS-UPD-007 |
| integration::replica convergence::shuffled and duplicated update sets converge to the same content | integration | positive | section Update Exchange + section Cross-View Invariants | covered | YJS-UPD-006, YJS-CVI-001 |
| integration::replica convergence::state-vector diff exchange syncs two diverged replicas minimally | integration | positive | section Update Exchange + section Cross-View Invariants | covered | YJS-UPD-001, YJS-UPD-003, YJS-CVI-007 |
| integration::replica convergence::merge and diff over per-transaction updates equal direct replay | integration | positive | section Update Exchange + section Cross-View Invariants | covered | YJS-UPD-008, YJS-UPD-009, YJS-UPD-010, YJS-CVI-002 |
| integration::replica convergence::v1 and v2 histories replay to identical replicas | integration | positive | section Update Exchange + section Cross-View Invariants | covered | YJS-UPD-011, YJS-UPD-012, YJS-CVI-002 |
| integration::replica convergence::per-transaction update events replayed in order rebuild the peer | integration | positive | section Documents And Root Types | covered | YJS-DOC-010, YJS-DOC-011 |
| integration::events across replicas and nesting::remote transactions fire observers with local false and the applyUpdate origin | integration | positive | section Events And Observation | covered | YJS-EVT-010, YJS-EVT-011 |
| integration::events across replicas and nesting::observeDeep reports paths across map and array nesting | integration | positive | section Events And Observation | covered | YJS-EVT-002, YJS-EVT-003 |
| integration::events across replicas and nesting::unobserveDeep stops nested delivery | integration | positive | section Events And Observation | covered | YJS-EVT-002 |
| integration::events across replicas and nesting::an array event delta replayed over the pre-state yields the post-state | integration | positive | section Cross-View Invariants + section Events And Observation | covered | YJS-CVI-003, YJS-EVT-008 |
| integration::events across replicas and nesting::map key records agree with pre- and post-transaction values | integration | positive | section Cross-View Invariants + section Events And Observation | covered | YJS-CVI-003, YJS-EVT-006 |
| integration::events across replicas and nesting::nested standalone types replicate wholesale through one update | integration | positive | section Shared Maps + section Shared Arrays + section Cross-View Invariants | covered | YJS-MAP-009, YJS-ARR-005, YJS-CVI-001 |
| integration::events across replicas and nesting::formatting applied on one replica appears in the peer's delta view | integration | positive | section Shared Text + section Cross-View Invariants | covered | YJS-TXT-012, YJS-CVI-001 |
| integration::undo, snapshots, and positions across documents::undo reverts local content while preserving interleaved remote content | integration | positive | section Undo And Redo + section Cross-View Invariants | covered | YJS-UNDO-009, YJS-CVI-004 |
| integration::undo, snapshots, and positions across documents::undone state propagates to peers like any other edit | integration | positive | section Cross-View Invariants | covered | YJS-CVI-004 |
| integration::undo, snapshots, and positions across documents::tracked origins separate user edits from provider updates | integration | positive | section Undo And Redo | covered | YJS-UNDO-002, YJS-UNDO-009 |
| integration::undo, snapshots, and positions across documents::stack item meta persists from added to popped for cursor restoration | integration | positive | section Undo And Redo + section Relative Positions | covered | YJS-UNDO-010, YJS-UNDO-011, YJS-POS-003 |
| integration::undo, snapshots, and positions across documents::snapshot restoration reproduces the version while history moves on | integration | positive | section Snapshots + section Cross-View Invariants | covered | YJS-SNAP-004, YJS-SNAP-006, YJS-CVI-005 |
| integration::undo, snapshots, and positions across documents::relative positions track their character across remote edits and codecs | integration | positive | section Relative Positions + section Cross-View Invariants | covered | YJS-POS-003, YJS-CVI-006 |
| integration::undo, snapshots, and positions across documents::map undo interleaved with remote updates keeps remote keys | integration | positive | section Undo And Redo | covered | YJS-UNDO-009, YJS-UNDO-008 |
| integration::collaborative sessions end to end::two clients edit, sync, and undo with cursors surviving | system_e2e | positive | section Cross-View Invariants | covered | YJS-CVI-001, YJS-CVI-004, YJS-CVI-006 |
| integration::collaborative sessions end to end::offline client catches up through a merging relay | system_e2e | positive | section Cross-View Invariants + section Update Exchange | covered | YJS-CVI-001, YJS-CVI-002, YJS-UPD-007 |
| integration::collaborative sessions end to end::a versioned document restores an old release while editing continues | system_e2e | positive | section Cross-View Invariants + section Snapshots | covered | YJS-CVI-005, YJS-SNAP-003, YJS-SNAP-006 |
| integration::collaborative sessions end to end::a shared board converges across three replicas with deep observers | system_e2e | positive | section Cross-View Invariants + section Events And Observation | covered | YJS-CVI-001, YJS-CVI-003, YJS-EVT-002 |

Total: 116 | kept (covered): 116 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 116

Layers: atomic 88 | integration 24 | system_e2e 4
Assertion kinds: positive 107 (92%) | failure_path 9 | shape 0 | no_check 0
Atomic positive share: 90%
