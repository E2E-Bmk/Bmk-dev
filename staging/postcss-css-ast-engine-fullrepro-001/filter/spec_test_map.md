# spec_test_map — postcss-css-ast-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-26

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::parsing and input::parse returns a Root and reproduces the input byte for byte | atomic | positive | section Parsing And Input + section Stringification + section Cross-View Invariants | covered | PC-PAR-001, PC-STR-001, PC-CVI-001 |
| atomic::parsing and input::parse is reachable as a method of the default export | atomic | positive | section Parsing And Input | covered | PC-PAR-011 |
| atomic::parsing and input::the from option records the absolute file path | atomic | positive | section Parsing And Input | covered | PC-PAR-002 |
| atomic::parsing and input::without from the input synthesizes an identifier and file is undefined | atomic | positive | section Parsing And Input | covered | PC-PAR-003 |
| atomic::parsing and input::all nodes of one tree share the same Input carrying the css text | atomic | positive | section Parsing And Input | covered | PC-PAR-004 |
| atomic::parsing and input::a byte-order mark is stripped from css, flagged, and re-emitted | atomic | positive | section Parsing And Input | covered | PC-PAR-005 |
| atomic::parsing and input::source positions carry 1-based line and column and 0-based offsets | atomic | positive | section Parsing And Input | covered | PC-PAR-006 |
| atomic::parsing and input::whitespace between nodes lives in the following node's raws.before | atomic | positive | section Parsing And Input | covered | PC-PAR-007 |
| atomic::parsing and input::bodyless at-rules have no nodes property while empty blocks have an empty array | atomic | positive | section Parsing And Input | covered | PC-PAR-008 |
| atomic::parsing and input::custom property declarations keep their value verbatim and set variable | atomic | positive | section Parsing And Input | covered | PC-PAR-009 |
| atomic::parsing and input::CRLF line endings round-trip and are captured into raws | atomic | positive | section Parsing And Input + section Stringification | covered | PC-PAR-010, PC-STR-001 |
| atomic::parsing and input::Input is directly constructible | atomic | positive | section Parsing And Input | covered | PC-PAR-011 |
| atomic::node model and raws::each node type exposes its value properties | atomic | positive | section Node Model And Raws | covered | PC-NOD-001 |
| atomic::node model and raws::parent links exist inside a tree and detached nodes have none | atomic | positive | section Node Model And Raws | covered | PC-NOD-002 |
| atomic::node model and raws::raws capture the exact formatting fragments | atomic | positive | section Node Model And Raws | covered | PC-NOD-003 |
| atomic::node model and raws::comment raws record the inner whitespace | atomic | positive | section Node Model And Raws | covered | PC-NOD-003 |
| atomic::node model and raws::a commented selector is cached as raw plus cleaned value | atomic | positive | section Node Model And Raws | covered | PC-NOD-004 |
| atomic::node model and raws::a commented value is cached and reassignment prints the new value | atomic | positive | section Node Model And Raws + section Cross-View Invariants | covered | PC-NOD-004, PC-NOD-005, PC-CVI-005 |
| atomic::node model and raws::nonstandard important fragments are kept in raws.important | atomic | positive | section Node Model And Raws + section Values And Selectors | covered | PC-NOD-006, PC-VAL-004 |
| atomic::node model and raws::raw resolves captured fragments and synthesizes defaults | atomic | positive | section Node Model And Raws | covered | PC-NOD-007 |
| atomic::node model and raws::cleanRaws reprints the subtree with default formatting | atomic | positive | section Node Model And Raws | covered | PC-NOD-008 |
| atomic::node model and raws::assign applies several properties and returns the node | atomic | positive | section Node Model And Raws | covered | PC-NOD-009 |
| atomic::stringification::stringify drives the builder with parts and container markers | atomic | positive | section Stringification | covered | PC-STR-002 |
| atomic::stringification::constructed declarations and rules use documented default formatting | atomic | positive | section Stringification | covered | PC-STR-003 |
| atomic::stringification::constructed children indent four spaces and separate with semicolons | atomic | positive | section Stringification | covered | PC-STR-004 |
| atomic::stringification::nested constructed containers indent per level | atomic | positive | section Stringification | covered | PC-STR-004 |
| atomic::stringification::bodyless at-rules, comments, and root-level declarations print with defaults | atomic | positive | section Stringification | covered | PC-STR-005 |
| atomic::stringification::insertion into a parsed tree inherits indentation and semicolon style | atomic | positive | section Stringification | covered | PC-STR-006 |
| atomic::stringification::a document concatenates its roots and reparents them | atomic | positive | section Stringification | covered | PC-STR-007 |
| atomic::building trees::factories build detached typed nodes | atomic | positive | section Building Trees | covered | PC-BLD-001 |
| atomic::building trees::factory helpers are also reachable from the default export | atomic | positive | section Building Trees | covered | PC-BLD-001 |
| atomic::building trees::classes are constructible with properties objects and subclass Node | atomic | positive | section Building Trees | covered | PC-BLD-001 |
| atomic::building trees::append accepts strings, arrays, and nodes and returns the container | atomic | positive | section Building Trees | covered | PC-BLD-002 |
| atomic::building trees::descriptor shapes select the node type | atomic | positive | section Building Trees | covered | PC-BLD-002 |
| atomic::building trees::prepend puts nodes at the front in argument order | atomic | positive | section Building Trees | covered | PC-BLD-002 |
| atomic::building trees::a declaration descriptor without a value throws | atomic | failure_path | section Building Trees | covered | PC-BLD-003 |
| atomic::building trees::an unrecognized descriptor shape throws | atomic | failure_path | section Building Trees | covered | PC-BLD-004 |
| atomic::building trees::insertBefore and insertAfter splice relative to a child or index | atomic | positive | section Building Trees | covered | PC-BLD-005 |
| atomic::building trees::inserting a node owned by another tree removes it there first | atomic | positive | section Building Trees | covered | PC-BLD-006 |
| atomic::traversal and mutation::walk visits every descendant depth-first in document order | atomic | positive | section Traversal And Mutation | covered | PC-TRV-003 |
| atomic::traversal and mutation::typed walks visit their node type anywhere in the subtree | atomic | positive | section Traversal And Mutation | covered | PC-TRV-004 |
| atomic::traversal and mutation::string filters match exactly and regexps are tested | atomic | positive | section Traversal And Mutation | covered | PC-TRV-004 |
| atomic::traversal and mutation::returning false halts a walk and is returned | atomic | positive | section Traversal And Mutation | covered | PC-TRV-002 |
| atomic::traversal and mutation::each iterates direct children with indexes and stops on false | atomic | positive | section Traversal And Mutation | covered | PC-TRV-001, PC-TRV-002 |
| atomic::traversal and mutation::each keeps visiting after inserts and removals during iteration | atomic | positive | section Traversal And Mutation | covered | PC-TRV-001 |
| atomic::traversal and mutation::every and some evaluate predicates over direct children | atomic | positive | section Traversal And Mutation | covered | PC-TRV-008 |
| atomic::traversal and mutation::structural reads: first, last, index, next, prev, root | atomic | positive | section Traversal And Mutation + section Cross-View Invariants | covered | PC-TRV-005, PC-CVI-003 |
| atomic::traversal and mutation::replaceWith substitutes nodes and descriptors in place | atomic | positive | section Traversal And Mutation | covered | PC-TRV-006 |
| atomic::traversal and mutation::remove, removeChild, and removeAll detach nodes | atomic | positive | section Traversal And Mutation | covered | PC-TRV-007 |
| atomic::values and selectors::selectors splits on commas with trimming | atomic | positive | section Values And Selectors | covered | PC-VAL-001 |
| atomic::values and selectors::assigning selectors reuses the existing separator style | atomic | positive | section Values And Selectors | covered | PC-VAL-001 |
| atomic::values and selectors::list.space splits on top-level whitespace only | atomic | positive | section Values And Selectors | covered | PC-VAL-002 |
| atomic::values and selectors::list.comma splits on top-level commas only | atomic | positive | section Values And Selectors | covered | PC-VAL-002 |
| atomic::values and selectors::list.split honors the trailing-item flag | atomic | positive | section Values And Selectors | covered | PC-VAL-003 |
| atomic::values and selectors::canonical important parses to true and reprints | atomic | positive | section Values And Selectors | covered | PC-VAL-004 |
| atomic::cloning and json::clone returns a detached deep copy applying overrides | atomic | positive | section Cloning And JSON Round Trips | covered | PC-CLN-001 |
| atomic::cloning and json::a clone of an unmodified node prints identically | atomic | positive | section Cloning And JSON Round Trips + section Cross-View Invariants | covered | PC-CLN-001, PC-CVI-006 |
| atomic::cloning and json::cloneBefore and cloneAfter insert the copy and return it | atomic | positive | section Cloning And JSON Round Trips | covered | PC-CLN-002 |
| atomic::cloning and json::toJSON produces plain data with a root-level inputs array | atomic | positive | section Cloning And JSON Round Trips | covered | PC-CLN-003 |
| atomic::cloning and json::fromJSON revives nodes that print identically with working sources | atomic | positive | section Cloning And JSON Round Trips + section Cross-View Invariants | covered | PC-CLN-004, PC-CVI-001 |
| atomic::processor construction::the default export builds a Processor from plugins or arrays | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-001 |
| atomic::processor construction::Processor is constructible and use appends plugins | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-001 |
| atomic::processor construction::version reports a version string | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-001 |
| atomic::processor construction::a creator function with postcss=true is invoked without arguments | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-002 |
| atomic::processor construction::prepare returns listeners scoped to the run | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-003 |
| atomic::lazy result lifecycle::awaiting a processed run resolves to a Result | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-004 |
| atomic::lazy result lifecycle::synchronous reads run the pipeline and sync/async return the Result | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-004 |
| atomic::lazy result lifecycle::reading root synchronously exposes the processed tree | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-004 |
| atomic::lazy result lifecycle::an asynchronous plugin forbids synchronous access but awaits fine | atomic | failure_path | section Processors And The Plugin Pipeline | covered | PC-PRC-005 |
| atomic::lazy result lifecycle::the plugin-free fast path returns input text without parsing | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-006 |
| atomic::lazy result lifecycle::the plugin-free fast path still resolves to a full Result | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-006 |
| atomic::lazy result lifecycle::process accepts an existing Root without reparsing | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-013 |
| atomic::lazy result lifecycle::process accepts any object with a toString method | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-013 |
| atomic::visitor events::Once fires before per-node events, exits after children, OnceExit last | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-007 |
| atomic::visitor events::AtRule and Comment listeners fire for their node types | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-007 |
| atomic::visitor events::keyed Declaration listeners fire alongside the star listener | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-008 |
| atomic::visitor events::keyed AtRule listeners match by name | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-008 |
| atomic::visitor events::listeners receive a helper object carrying the result | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-009 |
| atomic::visitor events::a mutated declaration is revisited in the same run | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-010 |
| atomic::visitor events::nodes inserted during the run are visited | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-010 |
| atomic::visitor events::toResult produces a synchronous Result over the same root | atomic | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-011 |
| atomic::visitor events::a node error thrown inside a listener carries the plugin name | atomic | failure_path | section Processors And The Plugin Pipeline | covered | PC-PRC-012 |
| atomic::results, warnings, and messages::result exposes css, content alias, root, opts, processor, toString | atomic | positive | section Results, Warnings, And Messages | covered | PC-RES-001 |
| atomic::results, warnings, and messages::warnings returns exactly the messages typed warning | atomic | positive | section Results, Warnings, And Messages + section Cross-View Invariants | covered | PC-RES-002, PC-CVI-002 |
| atomic::results, warnings, and messages::node.warn anchors a Warning with positions narrowed by word | atomic | positive | section Results, Warnings, And Messages | covered | PC-RES-003, PC-RES-004 |
| atomic::results, warnings, and messages::a result-level warning has no position fields | atomic | positive | section Results, Warnings, And Messages | covered | PC-RES-003, PC-RES-005 |
| atomic::results, warnings, and messages::Warning toString includes plugin, position identifier, and text | atomic | positive | section Results, Warnings, And Messages | covered | PC-RES-006 |
| atomic::positions and error construction::positionBy resolves word, index, and default positions | atomic | positive | section Positions And Error Construction + section Cross-View Invariants | covered | PC-POS-001, PC-CVI-004 |
| atomic::positions and error construction::rangeBy covers a word exactly or the whole node | atomic | positive | section Positions And Error Construction + section Cross-View Invariants | covered | PC-POS-002, PC-CVI-004 |
| atomic::positions and error construction::fromOffset converts offsets to line and col | atomic | positive | section Positions And Error Construction + section Cross-View Invariants | covered | PC-POS-003, PC-CVI-004 |
| atomic::positions and error construction::node.error returns a positioned CssSyntaxError without throwing | atomic | positive | section Positions And Error Construction | covered | PC-POS-004 |
| atomic::positions and error construction::input.error builds an error at an explicit position | atomic | positive | section Positions And Error Construction | covered | PC-POS-005 |
| atomic::positions and error construction::a sourceless node still manufactures an error without positions | atomic | positive | section Positions And Error Construction | covered | PC-POS-006 |
| atomic::parse errors::unclosed block | atomic | failure_path | section Error Semantics | covered | PC-ERR-001 |
| atomic::parse errors::stray closing brace, unclosed comment, unclosed string, unknown word | atomic | failure_path | section Error Semantics | covered | PC-ERR-001 |
| atomic::parse errors::error anatomy: message combines identifier, position, and reason | atomic | failure_path | section Error Semantics | covered | PC-ERR-002 |
| atomic::parse errors::a ranged parse error carries end coordinates | atomic | failure_path | section Error Semantics | covered | PC-ERR-002 |
| atomic::parse errors::showSourceCode renders an uncolored frame and toString embeds it | atomic | failure_path | section Error Semantics | covered | PC-ERR-003 |
| integration::round trips::a complex stylesheet survives parse, JSON, and revival byte for byte | integration | positive | section Cross-View Invariants + section Cloning And JSON Round Trips | covered | PC-CVI-001, PC-CLN-003, PC-CLN-004 |
| integration::round trips::read-only traversal never changes the printed output | integration | positive | section Cross-View Invariants + section Traversal And Mutation | covered | PC-CVI-001, PC-TRV-003, PC-TRV-004 |
| integration::round trips::a revived tree accepts further edits and reprints correctly | integration | positive | section Cloning And JSON Round Trips + section Node Model And Raws + section Cross-View Invariants | covered | PC-CLN-004, PC-NOD-005, PC-CVI-001 |
| integration::cross-view consistency::pipeline css equals the final tree's own print after mutations | integration | positive | section Cross-View Invariants + section Processors And The Plugin Pipeline | covered | PC-CVI-002, PC-PRC-010 |
| integration::cross-view consistency::warning positions agree with the anchor node's own projections | integration | positive | section Cross-View Invariants + section Results, Warnings, And Messages + section Positions And Error Construction | covered | PC-CVI-002, PC-RES-004, PC-POS-001, PC-POS-002 |
| integration::cross-view consistency::every walked node agrees on root, parent, and index | integration | positive | section Cross-View Invariants + section Traversal And Mutation | covered | PC-CVI-003, PC-TRV-005 |
| integration::cross-view consistency::positions project consistently across start, positionBy, and fromOffset | integration | positive | section Cross-View Invariants + section Parsing And Input + section Positions And Error Construction | covered | PC-CVI-004, PC-PAR-006, PC-POS-003 |
| integration::cross-view consistency::editing one declaration keeps sibling raws and selector caches verbatim | integration | positive | section Cross-View Invariants + section Node Model And Raws | covered | PC-CVI-005, PC-NOD-004 |
| integration::cross-view consistency::clones stay equivalent while originals move on | integration | positive | section Cross-View Invariants + section Cloning And JSON Round Trips + section Traversal And Mutation | covered | PC-CVI-006, PC-CLN-001, PC-TRV-007 |
| integration::cross-view consistency::one run delivers every node of the final tree including inserted ones | integration | positive | section Cross-View Invariants + section Processors And The Plugin Pipeline | covered | PC-CVI-007, PC-PRC-010 |
| integration::pipeline workflows::plugins visit each node in registration order | integration | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-007, PC-PRC-001 |
| integration::pipeline workflows::an async pipeline mutates, warns, and resolves coherently | integration | positive | section Processors And The Plugin Pipeline + section Results, Warnings, And Messages + section Cross-View Invariants | covered | PC-PRC-005, PC-RES-002, PC-CVI-002 |
| integration::pipeline workflows::creator, prepare, and plain object plugins compose in one processor | integration | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-002, PC-PRC-003, PC-PRC-001 |
| integration::pipeline workflows::a plugin error rejects the awaited pipeline with plugin identity | integration | failure_path | section Processors And The Plugin Pipeline + section Error Semantics | covered | PC-PRC-012, PC-ERR-002 |
| integration::pipeline workflows::the fast path and a plugin run agree on printed css for valid input | integration | positive | section Processors And The Plugin Pipeline | covered | PC-PRC-006, PC-PRC-004 |
| integration::editing workflows::nodes move between trees keeping their original source input | integration | positive | section Building Trees + section Parsing And Input + section Stringification | covered | PC-BLD-006, PC-PAR-002, PC-STR-001 |
| integration::editing workflows::a walk-driven rewrite touches only matched declarations | integration | positive | section Traversal And Mutation + section Cross-View Invariants | covered | PC-TRV-004, PC-CVI-005 |
| integration::editing workflows::unwrapping an at-rule with replaceWith preserves children order | integration | positive | section Traversal And Mutation + section Stringification | covered | PC-TRV-006, PC-STR-001 |
| integration::editing workflows::factories, insertion, and formatting inheritance build one stylesheet | integration | positive | section Building Trees + section Stringification | covered | PC-BLD-001, PC-STR-004, PC-STR-006 |
| integration::editing workflows::selector rewrites and structural inserts compose | integration | positive | section Values And Selectors + section Building Trees | covered | PC-VAL-001, PC-BLD-005 |
| integration::editing workflows::a document collects parsed roots and prints their concatenation | integration | positive | section Stringification + section Cross-View Invariants | covered | PC-STR-007, PC-CVI-001 |
| integration::editing workflows::each-driven pruning with mixed removals prints the survivors | integration | positive | section Traversal And Mutation | covered | PC-TRV-001, PC-TRV-007 |
| integration::system workflows::a lint-and-fix session: warnings, fixes, and coherent output | system_e2e | positive | section Processors And The Plugin Pipeline + section Results, Warnings, And Messages + section Cross-View Invariants | covered | PC-PRC-004, PC-RES-002, PC-RES-004, PC-CVI-002, PC-CVI-007 |
| integration::system workflows::a refactor session: move, clone, edit, and serialize one stylesheet | system_e2e | positive | section Cross-View Invariants + section Building Trees + section Cloning And JSON Round Trips | covered | PC-CVI-001, PC-CVI-005, PC-CVI-006, PC-BLD-006, PC-CLN-004 |
| integration::system workflows::a scratch build processed end to end through a processor | system_e2e | positive | section Building Trees + section Stringification + section Processors And The Plugin Pipeline + section Cross-View Invariants | covered | PC-BLD-001, PC-STR-004, PC-PRC-011, PC-CVI-002 |
| integration::system workflows::an error recovery session: diagnose a broken file, fix it, process it | system_e2e | failure_path | section Error Semantics + section Processors And The Plugin Pipeline | covered | PC-ERR-001, PC-ERR-002, PC-ERR-003, PC-PRC-006 |
| integration::system workflows::a multi-file session: one document aggregates independently parsed sheets | system_e2e | positive | section Stringification + section Parsing And Input + section Cross-View Invariants | covered | PC-STR-007, PC-PAR-002, PC-CVI-003 |

Total: 125 | kept (covered): 125 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 125

Layers: atomic 98 | integration 22 | system_e2e 5
Assertion kinds: positive 114 (91%) | failure_path 11 | shape 0 | no_check 0
Atomic positive share: 91%
