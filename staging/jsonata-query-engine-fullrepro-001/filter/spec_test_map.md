# spec_test_map — jsonata-query-engine-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::jsonata compiles a reusable expression object without evaluating it | atomic | positive | section Expression Compilation And Errors | covered | JN-CMP-001, JN-CMP-005 |
| atomic::an unclosed group throws S0203 with position and (end) token | atomic | failure_path | section Expression Compilation And Errors | covered | JN-CMP-002 |
| atomic::dangling dots and stray operator characters are syntax errors | atomic | failure_path | section Expression Compilation And Errors | covered | JN-CMP-002 |
| atomic::no ** power operator and no infix ^ outside sort | atomic | failure_path | section Expression Compilation And Errors | covered | JN-CMP-002 |
| atomic::evaluate returns a promise and empty selections resolve undefined | atomic | positive | section Expression Compilation And Errors | covered | JN-CMP-003 |
| atomic::runtime failures reject with code, position, and token but no Error prototype | atomic | failure_path | section Expression Compilation And Errors | covered | JN-CMP-004 |
| atomic::ast exposes path steps and binary operator structure | atomic | positive | section Expression Compilation And Errors | covered | JN-CMP-006 |
| atomic::name steps select fields and singleton sequences collapse to the bare value | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-001, JN-PATH-004 |
| atomic::selecting a missing field resolves undefined, not null | atomic | positive | section Path Navigation And Sequences + section Error Semantics | covered | JN-PATH-001, JN-ERR-002 |
| atomic::steps over arrays map and flatten one level | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-002 |
| atomic::the [] suffix keeps array form for single-item results | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-003 |
| atomic::numeric predicates select by position, zero-based and negative from the end | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-008 |
| atomic::boolean predicates filter with sequence-rule results | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-008, JN-PATH-001 |
| atomic::wildcard * selects all field values of the context object | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-009 |
| atomic::descendant ** selects values at any depth | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-009 |
| atomic::$ is the current context and $$ is always the root input | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-004 |
| atomic::parenthesized step expressions map over the context sequence | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-005 |
| atomic::the parent operator % reaches the enclosing object | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-006 |
| atomic::#$var binds zero-based position and @$var binds the context item | atomic | positive | section Path Navigation And Sequences | covered | JN-PATH-007 |
| atomic::arithmetic follows conventional precedence with % and unary minus | atomic | positive | section Operators | covered | JN-OP-001 |
| atomic::arithmetic on a defined non-number rejects T2001, on undefined resolves undefined | atomic | positive | section Operators + section Error Semantics | covered | JN-OP-001, JN-ERR-002 |
| atomic::order comparisons work on two numbers or two strings and reject mixed types | atomic | positive | section Operators | covered | JN-OP-002 |
| atomic::= and != are deep structural equality and mixed types compare unequal | atomic | positive | section Operators | covered | JN-OP-003 |
| atomic::in tests array membership by primitive value only | atomic | positive | section Operators | covered | JN-OP-004 |
| atomic::range expressions expand inclusive integer sequences inside array constructors | atomic | positive | section Operators | covered | JN-OP-005 |
| atomic::& concatenates the string forms of both operands | atomic | positive | section Operators | covered | JN-OP-006 |
| atomic::and/or apply effective-boolean coercion to their operands | atomic | positive | section Operators | covered | JN-OP-007 |
| atomic::conditionals return undefined when a false test has no else branch | atomic | positive | section Operators | covered | JN-OP-008 |
| atomic::?: defaults on falsy values while ?? defaults only on undefined | atomic | positive | section Operators | covered | JN-OP-009 |
| atomic::~> chains pass the left value as first argument, composing left to right | atomic | positive | section Operators | covered | JN-OP-010 |
| atomic::array constructors preserve nesting and object keys may be computed | atomic | positive | section Constructors And Reshaping | covered | JN-CON-001 |
| atomic::a duplicate key inside one object constructor rejects D1009 | atomic | failure_path | section Constructors And Reshaping | covered | JN-CON-002 |
| atomic::grouping aggregates values sharing a key with singletons kept bare | atomic | positive | section Constructors And Reshaping | covered | JN-CON-003 |
| atomic::two grouping pairs producing the same key reject D1009 | atomic | failure_path | section Constructors And Reshaping | covered | JN-CON-002 |
| atomic::^ sorts ascending by default with > descending and later terms breaking ties | atomic | positive | section Constructors And Reshaping | covered | JN-CON-004 |
| atomic::sorting mixed-type term values rejects T2007 | atomic | failure_path | section Constructors And Reshaping | covered | JN-CON-004 |
| atomic::the transform operator merges updates into matched objects on a deep copy | atomic | positive | section Constructors And Reshaping | covered | JN-CON-005 |
| atomic::transform deletions strip listed names from matched objects | atomic | positive | section Constructors And Reshaping | covered | JN-CON-005 |
| atomic:::= binds a value and a block returns its last statement | atomic | positive | section Variables, Blocks, And Functions | covered | JN-FUN-001 |
| atomic::blocks form child scopes so inner rebinding stays local | atomic | positive | section Variables, Blocks, And Functions | covered | JN-FUN-002 |
| atomic::unbound variables read as undefined but calling a non-function rejects T1006 | atomic | positive | section Variables, Blocks, And Functions | covered | JN-FUN-003 |
| atomic::lambdas apply, recurse through their binding, and close over scope | atomic | positive | section Variables, Blocks, And Functions | covered | JN-FUN-004 |
| atomic::higher-order library functions pass value and index to lambdas | atomic | positive | section Variables, Blocks, And Functions + section Function Library | covered | JN-FUN-004, JN-LIB-014 |
| atomic::lambda signatures validate argument types and reject T0410 at the function name | atomic | positive | section Variables, Blocks, And Functions | covered | JN-FUN-005 |
| atomic::built-in functions enforce their signatures the same way | atomic | failure_path | section Variables, Blocks, And Functions | covered | JN-FUN-005 |
| atomic::$string renders JSON text for structures and 15-digit decimals for numbers | atomic | positive | section Function Library | covered | JN-LIB-001 |
| atomic::$length counts characters and $substring supports negative starts | atomic | positive | section Function Library | covered | JN-LIB-002 |
| atomic::$substringBefore/After split at the first separator occurrence | atomic | positive | section Function Library | covered | JN-LIB-002 |
| atomic::case mapping, whitespace trimming, and two-sided padding | atomic | positive | section Function Library | covered | JN-LIB-003 |
| atomic::$contains, $split, and $join accept strings or regexes | atomic | positive | section Function Library | covered | JN-LIB-004 |
| atomic::$match returns match records with index and captured groups | atomic | positive | section Function Library | covered | JN-LIB-005 |
| atomic::$replace supports group references, replacement functions, and limits | atomic | positive | section Function Library | covered | JN-LIB-005 |
| atomic::base64 and URL-component codecs round-trip text | atomic | positive | section Function Library | covered | JN-LIB-006 |
| atomic::$eval evaluates a JSONata source string against an optional context | atomic | positive | section Function Library | covered | JN-LIB-006 |
| atomic::$number converts numeric strings, hex, and booleans and rejects D3030 otherwise | atomic | positive | section Function Library | covered | JN-LIB-007 |
| atomic::$abs, $floor, $ceil, and half-to-even $round with precision | atomic | positive | section Function Library | covered | JN-LIB-008 |
| atomic::$power and $sqrt compute, $sqrt of a negative rejects D3060, $random stays in [0,1) | atomic | positive | section Function Library | covered | JN-LIB-009 |
| atomic::number formatting pictures, radix formatting, and word-form integers | atomic | positive | section Function Library | covered | JN-LIB-010 |
| atomic::aggregators reduce numeric arrays and treat a bare number as its own aggregate | atomic | positive | section Function Library | covered | JN-LIB-011 |
| atomic::$count reports array length, 1 for a bare value, and 0 for no value | atomic | positive | section Function Library | covered | JN-LIB-012 |
| atomic::$append concatenates, treating non-arrays as singletons | atomic | positive | section Function Library | covered | JN-LIB-013 |
| atomic::$sort defaults ascending with an optional out-of-order comparator | atomic | positive | section Function Library | covered | JN-LIB-013 |
| atomic::$reverse, $distinct with deep equality, and $zip stopping at the shortest input | atomic | positive | section Function Library | covered | JN-LIB-013 |
| atomic::$filter, $reduce with optional init, and $single's unique-match contract | atomic | positive | section Function Library | covered | JN-LIB-014 |
| atomic::$each maps entries to values and $sift filters entries by predicate | atomic | positive | section Function Library | covered | JN-LIB-014 |
| atomic::$keys unions over arrays, $lookup gathers across arrays, $merge lets later keys win | atomic | positive | section Function Library | covered | JN-LIB-015 |
| atomic::$type names the seven value kinds | atomic | positive | section Function Library | covered | JN-LIB-016 |
| atomic::$exists distinguishes null from absence and $boolean applies effective-boolean rules | atomic | positive | section Function Library | covered | JN-LIB-016 |
| atomic::null is a value: equal to itself, storable, and never equal to absence | atomic | positive | section Function Library + section Operators | covered | JN-LIB-016, JN-OP-003 |
| atomic::$error rejects D3137 and $assert rejects D3141 only on a false condition | atomic | positive | section Function Library | covered | JN-LIB-017 |
| atomic::$fromMillis renders ISO UTC by default and honors pictures with timezones | atomic | positive | section Date And Time | covered | JN-DT-001 |
| atomic::$toMillis parses ISO or picture-described text and rejects D3110 otherwise | atomic | positive | section Date And Time | covered | JN-DT-002 |
| atomic::$now and $millis observe the same instant within one evaluation | atomic | positive | section Date And Time | covered | JN-DT-003 |
| atomic::the bindings argument of evaluate provides per-call variables | atomic | positive | section Bindings And Host Integration | covered | JN-BND-001 |
| atomic::assign persists bindings across evaluations of the same expression | atomic | positive | section Bindings And Host Integration | covered | JN-BND-002 |
| atomic::evaluate-time bindings take precedence over assigned bindings | atomic | positive | section Bindings And Host Integration | covered | JN-BND-002 |
| atomic::registerFunction binds host functions and enforces their signatures | atomic | positive | section Bindings And Host Integration | covered | JN-BND-003 |
| atomic::promise-returning host functions are awaited before use | atomic | positive | section Bindings And Host Integration | covered | JN-BND-003 |
| atomic::host functions see the evaluation timestamp and input through this | atomic | positive | section Bindings And Host Integration | covered | JN-BND-004 |
| integration::an order analytics report groups line revenue per sku and counts group sizes | integration | positive | section Constructors And Reshaping + section Path Navigation And Sequences + section Function Library | covered | JN-CON-003, JN-PATH-005, JN-LIB-011, JN-PATH-002 |
| integration::a discount pipeline transforms the catalog copy and leaves the source untouched | integration | positive | section Constructors And Reshaping + section Variables, Blocks, And Functions + section Function Library + section Operators | covered | JN-CON-005, JN-FUN-001, JN-LIB-011, JN-OP-010 |
| integration::a registered scoring function drives predicates and descending sort end to end | integration | positive | section Bindings And Host Integration + section Path Navigation And Sequences + section Constructors And Reshaping | covered | JN-BND-003, JN-PATH-008, JN-CON-004 |
| integration::recursive lambdas fold a tree with existence guards and aggregation | integration | positive | section Variables, Blocks, And Functions + section Function Library + section Operators | covered | JN-FUN-004, JN-LIB-016, JN-LIB-014, JN-LIB-011, JN-OP-008 |
| integration::a slug pipeline chains case mapping, splitting, and joining | integration | positive | section Operators + section Function Library | covered | JN-OP-010, JN-LIB-003, JN-LIB-004 |
| integration::a regex replacement function converts and re-renders numbers in place | integration | positive | section Function Library | covered | JN-LIB-005, JN-LIB-007, JN-LIB-001 |
| integration::datetime values survive picture-driven round trips | integration | positive | section Date And Time | covered | JN-DT-001, JN-DT-002 |
| integration::a paginated projection combines positional binds, predicates, and sequence rules | integration | positive | section Path Navigation And Sequences + section Variables, Blocks, And Functions | covered | JN-PATH-007, JN-PATH-008, JN-PATH-001, JN-FUN-001 |
| integration::parent references feed a grouping that indexes products by order | integration | positive | section Path Navigation And Sequences + section Constructors And Reshaping | covered | JN-PATH-006, JN-CON-003, JN-CON-001 |
| integration::dynamically composed sources evaluate through $eval | integration | positive | section Function Library + section Operators | covered | JN-LIB-006, JN-OP-006, JN-LIB-012, JN-OP-005 |
| integration::async and sync host functions combine with library calls in one expression | integration | positive | section Bindings And Host Integration + section Function Library + section Operators | covered | JN-BND-003, JN-LIB-011, JN-OP-001 |
| integration::one compiled expression serves many inputs while call bindings stay per-call | integration | positive | section Expression Compilation And Errors + section Bindings And Host Integration | covered | JN-CMP-005, JN-BND-001, JN-BND-002 |
| integration::a configuration is filtered, remapped, and merged through object combinators | integration | positive | section Function Library + section Constructors And Reshaping + section Variables, Blocks, And Functions | covered | JN-LIB-014, JN-LIB-015, JN-CON-001, JN-FUN-004 |
| integration::a sorted distinct union of arrays reproduces an integer range | integration | positive | section Function Library + section Operators | covered | JN-LIB-013, JN-OP-005, JN-OP-003 |
| integration::guarded defaults keep a report total while assertions reject bad documents | integration | positive | section Operators + section Function Library + section Error Semantics | covered | JN-OP-009, JN-LIB-017, JN-ERR-001 |
| integration::sequence rules hold identically across paths, predicates, and library filters | integration | positive | section Cross-View Invariants | covered | JN-CVI-001; CVI-001 |
| integration::descendant projections agree with explicit paths under aggregation | integration | positive | section Cross-View Invariants + section Path Navigation And Sequences + section Function Library | covered | JN-CVI-001, JN-PATH-009, JN-PATH-002, JN-LIB-011; CVI-001 |
| integration::every subsystem reports failures as code, position, and token triples | integration | failure_path | section Cross-View Invariants + section Expression Compilation And Errors + section Error Semantics | covered | JN-CVI-002, JN-CMP-002, JN-CMP-004, JN-ERR-001; CVI-002 |
| integration::one effective-boolean rule governs conditionals, and, ?:, and $boolean | integration | positive | section Cross-View Invariants + section Operators + section Function Library | covered | JN-CVI-003, JN-OP-007, JN-OP-009, JN-LIB-016; CVI-003 |
| integration::names bound via :=, assign, and evaluate bindings are indistinguishable at lookup | integration | positive | section Cross-View Invariants + section Bindings And Host Integration + section Variables, Blocks, And Functions | covered | JN-CVI-004, JN-BND-001, JN-BND-002, JN-FUN-001; CVI-004 |
| integration::structural equality agrees between = and $distinct while in stays primitive | integration | positive | section Cross-View Invariants + section Operators + section Function Library | covered | JN-CVI-005, JN-OP-003, JN-OP-004, JN-LIB-013; CVI-005 |
| integration::chaining through ~> matches direct application for library functions | integration | positive | section Cross-View Invariants + section Operators | covered | JN-CVI-006, JN-OP-010; CVI-006 |
| integration::ast structure describes exactly what evaluation executes | integration | positive | section Cross-View Invariants + section Expression Compilation And Errors | covered | JN-CVI-007, JN-CMP-006; CVI-007 |
| integration::an invoice document is aggregated, grouped, ranked, and rendered in one pass | system_e2e | positive | section Constructors And Reshaping + section Function Library + section Path Navigation And Sequences | covered | JN-CON-003, JN-CON-004, JN-LIB-010, JN-LIB-011, JN-PATH-005, JN-PATH-008 |
| integration::a full enrichment pipeline transforms, regroups, formats, and stamps a document | system_e2e | positive | section Constructors And Reshaping + section Date And Time + section Bindings And Host Integration + section Operators | covered | JN-CON-005, JN-CON-003, JN-DT-003, JN-DT-002, JN-BND-001, JN-OP-010 |

Total: 104 | kept (covered): 104 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 104

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
