# spec_test_map — prosemirror-model-doc-tree-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::compiled schema exposes type tables, top node, and spec | atomic | positive | section Schemas And Node Types | covered | PM-SCH-001 |
| atomic::topNode option selects the top-level type | atomic | positive | section Schemas And Node Types | covered | PM-SCH-001 |
| atomic::node type flags reflect inline/block/text/leaf/textblock roles | atomic | positive | section Schemas And Node Types | covered | PM-SCH-004 |
| atomic::atom spec flag marks a non-leaf node atomic | atomic | positive | section Schemas And Node Types | covered | PM-SCH-004 |
| atomic::null attribute argument fills defaults and nulls | atomic | positive | section Schemas And Node Types | covered | PM-SCH-005 |
| atomic::attribute object omitting a required attribute raises RangeError | atomic | positive | section Schemas And Node Types + section Error Semantics | covered | PM-SCH-006, PM-ERR-001 |
| atomic::undeclared attribute names are dropped from created values | atomic | positive | section Schemas And Node Types | covered | PM-SCH-006 |
| atomic::hasRequiredAttrs reflects presence of default-less attributes | atomic | positive | section Schemas And Node Types | covered | PM-SCH-007 |
| atomic::schema.node accepts a name or NodeType and several content forms | atomic | positive | section Schemas And Node Types | covered | PM-SCH-008 |
| atomic::unknown node type name raises RangeError | atomic | failure_path | section Schemas And Node Types + section Error Semantics | covered | PM-SCH-008, PM-ERR-001 |
| atomic::schema.text builds text nodes and rejects empty text | atomic | positive | section Schemas And Node Types + section Error Semantics | covered | PM-SCH-009, PM-ERR-001 |
| atomic::schema.mark builds marks from a name or MarkType | atomic | positive | section Schemas And Node Types | covered | PM-SCH-010 |
| atomic::create skips content validation while createChecked enforces it | atomic | positive | section Schemas And Node Types + section Error Semantics | covered | PM-SCH-011, PM-ERR-001 |
| atomic::createAndFill synthesizes required content | atomic | positive | section Schemas And Node Types + section Content Rules | covered | PM-SCH-011, PM-CNT-005 |
| atomic::validContent reports content-rule satisfaction | atomic | positive | section Schemas And Node Types | covered | PM-SCH-012 |
| atomic::compatibleContent detects shared allowed content | atomic | positive | section Schemas And Node Types | covered | PM-SCH-013 |
| atomic::marks spec strings and defaults govern allowsMarkType | atomic | positive | section Schemas And Node Types | covered | PM-SCH-003, PM-SCH-014 |
| atomic::allowedMarks filters a set down to permitted marks | atomic | positive | section Schemas And Node Types | covered | PM-SCH-014 |
| atomic::mixing inline and block content raises SyntaxError at construction | atomic | failure_path | section Schemas And Node Types + section Error Semantics | covered | PM-SCH-015, PM-ERR-001 |
| atomic::non-generatable type in a required position raises SyntaxError | atomic | failure_path | section Schemas And Node Types + section Error Semantics | covered | PM-SCH-016, PM-ERR-001 |
| atomic::node anatomy exposes type, attrs, content, marks, and text | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-001 |
| atomic::child access distinguishes throwing and null-returning forms | atomic | positive | section Documents, Nodes, And Fragments + section Error Semantics | covered | PM-DOC-002, PM-ERR-001 |
| atomic::forEach passes each child with offset and index | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-002 |
| atomic::descendants visits positions and honors early exit | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-003 |
| atomic::nodesBetween visits the nodes touching a range | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-003 |
| atomic::nodeSize arithmetic: text length, leaf 1, container +2 | atomic | positive | section Documents, Nodes, And Fragments + section Cross-View Invariants | covered | PM-DOC-004, PM-CVI-002; CVI-002 |
| atomic::node flags mirror type flags on instances | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-005 |
| atomic::textContent and textBetween project text with separators and leaf text | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-006 |
| atomic::copy keeps markup while replacing content | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-007 |
| atomic::node.mark replaces the mark set | atomic | positive | section Documents, Nodes, And Fragments + section Marks | covered | PM-DOC-007, PM-MRK-005 |
| atomic::cut on a text node slices the string and keeps marks | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-007 |
| atomic::eq, sameMarkup, and hasMarkup compare at different depths | atomic | positive | section Documents, Nodes, And Fragments + section Cross-View Invariants | covered | PM-DOC-008, PM-CVI-005; CVI-005 |
| atomic::toString renders the debugging tree with mark wrappers | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-008 |
| atomic::Fragment.from accepts null, node, array, and fragment | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-009 |
| atomic::adjacent text nodes with identical marks merge | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-010 |
| atomic::fragment operations produce expected sequences | atomic | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-011 |
| atomic::findDiffStart and findDiffEnd locate divergence | atomic | positive | section Documents, Nodes, And Fragments + section Cross-View Invariants | covered | PM-DOC-012, PM-CVI-005; CVI-005 |
| atomic::check passes valid trees and rejects invalid content | atomic | failure_path | section Documents, Nodes, And Fragments + section Error Semantics | covered | PM-DOC-013, PM-ERR-001 |
| atomic::nodeAt maps positions to covering nodes | atomic | positive | section Positions And Resolution | covered | PM-POS-001, PM-POS-002 |
| atomic::childAfter and childBefore report direct children with offsets | atomic | positive | section Positions And Resolution | covered | PM-POS-002 |
| atomic::resolve rejects out-of-range positions | atomic | failure_path | section Positions And Resolution + section Error Semantics | covered | PM-POS-003, PM-ERR-001 |
| atomic::resolved position exposes depth, parent, offsets | atomic | positive | section Positions And Resolution | covered | PM-POS-004, PM-POS-006 |
| atomic::start, end, before, after work across depths | atomic | positive | section Positions And Resolution | covered | PM-POS-004 |
| atomic::before and after at depth 0 raise RangeError | atomic | failure_path | section Positions And Resolution + section Error Semantics | covered | PM-POS-005, PM-ERR-001 |
| atomic::nodeBefore and nodeAfter split text at the position | atomic | positive | section Positions And Resolution | covered | PM-POS-007 |
| atomic::index, indexAfter, and posAtIndex map between views | atomic | positive | section Positions And Resolution + section Cross-View Invariants | covered | PM-POS-008, PM-CVI-007; CVI-007 |
| atomic::marks() reports the inline marks at a position | atomic | positive | section Positions And Resolution | covered | PM-POS-009 |
| atomic::sameParent, sharedDepth, min, and max relate positions | atomic | positive | section Positions And Resolution | covered | PM-POS-010 |
| atomic::blockRange and NodeRange expose block-level spans | atomic | positive | section Positions And Resolution | covered | PM-POS-011 |
| atomic::slice records open depths and size | atomic | positive | section Slices And Replacement | covered | PM-SLC-001, PM-SLC-002, PM-SLC-003 |
| atomic::Slice.empty and Slice.maxOpen bound openness | atomic | positive | section Slices And Replacement | covered | PM-SLC-003, PM-SLC-004 |
| atomic::slice JSON round trip and empty-slice null form | atomic | positive | section Slices And Replacement + section JSON Serialization | covered | PM-SLC-005, PM-JSN-001 |
| atomic::replace splices closed slices into text ranges | atomic | positive | section Slices And Replacement | covered | PM-SLC-006 |
| atomic::replacing a range with its own slice is identity | atomic | positive | section Slices And Replacement + section Cross-View Invariants | covered | PM-SLC-007, PM-CVI-003; CVI-003 |
| atomic::invalid replacements raise ReplaceError | atomic | failure_path | section Slices And Replacement + section Error Semantics | covered | PM-SLC-008, PM-ERR-001 |
| atomic::canReplace, canReplaceWith, and canAppend answer feasibility | atomic | positive | section Slices And Replacement | covered | PM-SLC-009 |
| atomic::cut returns the standalone region between positions | atomic | positive | section Slices And Replacement + section Cross-View Invariants | covered | PM-SLC-010, PM-CVI-003; CVI-003 |
| atomic::match automaton walks the doc content expression | atomic | positive | section Content Rules | covered | PM-CNT-002 |
| atomic::sequenced expression tracks required members | atomic | positive | section Content Rules | covered | PM-CNT-002 |
| atomic::matchFragment consumes whole fragments | atomic | positive | section Content Rules | covered | PM-CNT-002 |
| atomic::defaultType, edgeCount, edge, and contentMatchAt inspect states | atomic | positive | section Content Rules | covered | PM-CNT-003 |
| atomic::fillBefore synthesizes completing fragments | atomic | positive | section Content Rules | covered | PM-CNT-004 |
| atomic::findWrapping computes wrapper chains or null | atomic | positive | section Content Rules | covered | PM-CNT-004 |
| atomic::counted range modifiers bound repetition | atomic | positive | section Content Rules | covered | PM-CNT-001 |
| atomic::alternation and optional groups admit either branch once | atomic | positive | section Content Rules | covered | PM-CNT-001 |
| atomic::createAndFill completes structured content and skips optional non-generatable slots | atomic | positive | section Content Rules | covered | PM-CNT-005 |
| atomic::mark creation defaults attributes and enforces required ones | atomic | positive | section Marks + section Error Semantics | covered | PM-MRK-001, PM-ERR-001 |
| atomic::addToSet keeps schema order and deduplicates | atomic | positive | section Marks | covered | PM-MRK-002 |
| atomic::Mark.none, setFrom, and sameSet handle set construction | atomic | positive | section Marks | covered | PM-MRK-003 |
| atomic::exclusion removes expelled marks and blocks excluded additions | atomic | positive | section Marks | covered | PM-MRK-004 |
| atomic::mark constraints are enforced by createChecked, check, and rangeHasMark | atomic | positive | section Marks + section Error Semantics | covered | PM-MRK-005, PM-ERR-001 |
| atomic::mark JSON round trips through the schema | atomic | positive | section JSON Serialization | covered | PM-JSN-001, PM-JSN-002 |
| atomic::node JSON carries type, attrs, content, marks, and text | atomic | positive | section JSON Serialization | covered | PM-JSN-001 |
| atomic::fromJSON rebuilds nodes and fragments equal to the originals | atomic | positive | section JSON Serialization + section Cross-View Invariants | covered | PM-JSN-002, PM-CVI-001; CVI-001 |
| integration::JSON round trip preserves equality for a marked multi-block document | integration | positive | section Cross-View Invariants + section JSON Serialization | covered | PM-CVI-001, PM-JSN-002; CVI-001 |
| integration::descendants positions agree with nodeAt and size arithmetic | integration | positive | section Cross-View Invariants | covered | PM-CVI-002; CVI-002 |
| integration::slice then replace reproduces the document over every block range | integration | positive | section Cross-View Invariants + section Slices And Replacement | covered | PM-CVI-003, PM-SLC-007; CVI-003 |
| integration::cut agrees with the content captured by slice | integration | positive | section Cross-View Invariants + section Slices And Replacement | covered | PM-CVI-003, PM-SLC-010; CVI-003 |
| integration::automaton, createChecked, and check agree on validity | integration | positive | section Cross-View Invariants + section Content Rules + section Documents, Nodes, And Fragments | covered | PM-CVI-004, PM-CNT-002, PM-DOC-013; CVI-004 |
| integration::diffing agrees with equality across fragment edits | integration | positive | section Cross-View Invariants + section Documents, Nodes, And Fragments | covered | PM-CVI-005, PM-DOC-012; CVI-005 |
| integration::mark sets agree between construction, node marks, resolver, and rangeHasMark | integration | positive | section Cross-View Invariants + section Marks + section Positions And Resolution | covered | PM-CVI-006, PM-MRK-002, PM-POS-009; CVI-006 |
| integration::resolution agrees with child access at every depth | integration | positive | section Cross-View Invariants + section Positions And Resolution | covered | PM-CVI-007, PM-POS-004, PM-POS-008; CVI-007 |
| integration::open slice paste splits and merges paragraph halves | integration | positive | section Slices And Replacement | covered | PM-SLC-006, PM-SLC-001 |
| integration::slice cut from a nested context splices into a flat paragraph | integration | positive | section Slices And Replacement | covered | PM-SLC-001, PM-SLC-006 |
| integration::deleting a block range found through blockRange | integration | positive | section Positions And Resolution + section Slices And Replacement | covered | PM-POS-011, PM-SLC-006 |
| integration::wrapping a node according to findWrapping produces valid content | integration | positive | section Content Rules + section Documents, Nodes, And Fragments | covered | PM-CNT-004, PM-DOC-013 |
| integration::fillBefore output completes a partial section into checked validity | integration | positive | section Content Rules + section Cross-View Invariants | covered | PM-CNT-004, PM-CVI-004; CVI-004 |
| integration::replace failures leave clear error taxonomy while valid edits pass check | integration | positive | section Slices And Replacement + section Error Semantics + section Documents, Nodes, And Fragments | covered | PM-SLC-008, PM-ERR-001, PM-DOC-013 |
| integration::structural sharing keeps untouched branches identical after replace | integration | positive | section Slices And Replacement + section Documents, Nodes, And Fragments | covered | PM-SLC-006, PM-DOC-007 |
| integration::mark exclusion plays through document construction and checking | integration | positive | section Marks + section Cross-View Invariants | covered | PM-MRK-004, PM-MRK-005, PM-CVI-006; CVI-006 |
| integration::text projections agree with slices over the same range | integration | positive | section Documents, Nodes, And Fragments + section Slices And Replacement | covered | PM-DOC-006, PM-SLC-001 |
| integration::NodeRange constructed directly matches blockRange discovery | integration | positive | section Positions And Resolution | covered | PM-POS-011 |
| integration::counted expressions guide fill and reject overflow through replace | integration | positive | section Content Rules + section Slices And Replacement | covered | PM-CNT-001, PM-CNT-005, PM-SLC-008 |
| integration::copy and mark derive new nodes without touching originals | integration | positive | section Documents, Nodes, And Fragments | covered | PM-DOC-007, PM-DOC-008 |
| integration::author, navigate, edit, validate, and persist a document | system_e2e | positive | section Cross-View Invariants + section Positions And Resolution + section Slices And Replacement + section Documents, Nodes, And Fragments | covered | PM-CVI-001, PM-CVI-003, PM-POS-004, PM-SLC-006, PM-DOC-013; CVI-001 |
| integration::split a paragraph, then join it back through open slices | system_e2e | positive | section Slices And Replacement + section Cross-View Invariants | covered | PM-SLC-006, PM-SLC-007, PM-CVI-003; CVI-003 |
| integration::schema-driven synthesis composes a valid document from automaton hints | system_e2e | positive | section Content Rules + section Cross-View Invariants | covered | PM-CNT-003, PM-CNT-005, PM-CVI-004; CVI-004 |
| integration::diff-guided reconciliation converges two documents | system_e2e | positive | section Cross-View Invariants + section Documents, Nodes, And Fragments + section Slices And Replacement | covered | PM-CVI-005, PM-DOC-012, PM-SLC-006; CVI-005 |
| integration::full multi-projection sweep stays consistent on a nested document | system_e2e | positive | section Cross-View Invariants | covered | PM-CVI-001, PM-CVI-002, PM-CVI-006, PM-CVI-007; CVI-001 |
| integration::template completion pipeline: fill, verify, serialize, restore, re-verify | system_e2e | positive | section Content Rules + section Cross-View Invariants + section JSON Serialization | covered | PM-CNT-005, PM-CVI-001, PM-CVI-004, PM-JSN-002; CVI-001 |

Total: 100 | kept (covered): 100 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 100

Track A note: every upstream suite builds documents through prosemirror-test-builder,
a published helper package that itself depends on the real prosemirror-model, so
installing it beside a candidate breaks scorer isolation; the oracle is Track B
generated from the spec with expected values observed by executing the pinned
reference release (prosemirror-model@1.25.11, probes under wip/probe/pm).
