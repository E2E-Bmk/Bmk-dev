# spec_test_map — chevrotain-parser-toolkit-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::createToken returns a token type usable by a lexer | atomic | positive | section Token Definitions | covered | CHEV-TOK-001 |
| atomic::a literal string pattern matches verbatim text | atomic | positive | section Token Definitions | covered | CHEV-TOK-002 |
| atomic::tokenMatcher honors the token's own type and transitive categories | atomic | positive | section Token Definitions | covered | CHEV-TOK-004 |
| atomic::a token type in several categories matches each of them | atomic | positive | section Token Definitions | covered | CHEV-TOK-003, CHEV-TOK-004 |
| atomic::a Lexer.NA token type is never produced from text | atomic | positive | section Token Definitions | covered | CHEV-TOK-005 |
| atomic::tokenLabel falls back to the name and tokenName returns the name | atomic | positive | section Token Definitions | covered | CHEV-TOK-006 |
| atomic::createTokenInstance builds a token with the eight explicit fields | atomic | positive | section Token Definitions | covered | CHEV-TOK-007 |
| atomic::earlier token types win at the same offset regardless of match length | atomic | positive | section Token Definitions | covered | CHEV-TOK-009, CHEV-TOK-011 |
| atomic::longer_alt yields the longer alternative when it matches more text | atomic | positive | section Token Definitions | covered | CHEV-TOK-010 |
| atomic::an array of longer_alt candidates is honored | atomic | positive | section Token Definitions | covered | CHEV-TOK-010 |
| atomic::end-of-input recognition errors carry an EOF token with empty image | atomic | positive | section Token Definitions + section Error Handling And Recovery | covered | CHEV-TOK-008, CHEV-REC-003 |
| atomic::tokenize returns tokens with inclusive offsets and one-based positions | atomic | positive | section Tokenization | covered | CHEV-LEX-005, CHEV-LEX-006 |
| atomic::line and column advance across newlines under full tracking | atomic | positive | section Tokenization | covered | CHEV-LEX-006 |
| atomic::onlyStart tracking populates only the start fields | atomic | positive | section Tokenization | covered | CHEV-LEX-002, CHEV-LEX-007 |
| atomic::onlyOffset tracking populates only startOffset among positions | atomic | positive | section Tokenization | covered | CHEV-LEX-002, CHEV-LEX-007 |
| atomic::SKIPPED matches appear in neither tokens nor groups | atomic | positive | section Tokenization | covered | CHEV-LEX-008 |
| atomic::a string group diverts matches out of the main token stream | atomic | positive | section Tokenization | covered | CHEV-LEX-009 |
| atomic::declared group keys are present even when nothing matched | atomic | positive | section Tokenization | covered | CHEV-LEX-010 |
| atomic::an unmatchable character produces a structured error and lexing continues | atomic | positive | section Tokenization | covered | CHEV-LEX-011 |
| atomic::consecutive unmatchable characters merge into one error with their length | atomic | positive | section Tokenization | covered | CHEV-LEX-011 |
| atomic::push_mode and pop_mode drive a mode stack | atomic | positive | section Tokenization | covered | CHEV-LEX-001, CHEV-LEX-012 |
| atomic::a token type outside the active mode does not match | atomic | positive | section Tokenization | covered | CHEV-LEX-012 |
| atomic::tokenize accepts an initial mode name | atomic | positive | section Tokenization | covered | CHEV-LEX-013 |
| atomic::a custom pattern function matches text and returns null for no match | atomic | positive | section Tokenization | covered | CHEV-LEX-014 |
| atomic::a custom pattern's payload lands on the emitted token | atomic | positive | section Tokenization | covered | CHEV-LEX-014 |
| atomic::a global-flag pattern makes the Lexer constructor throw | atomic | failure_path | section Tokenization | covered | CHEV-LEX-003 |
| atomic::deferDefinitionErrorsHandling collects problems instead of throwing | atomic | positive | section Tokenization | covered | CHEV-LEX-004 |
| atomic::a rule invocation returns a CstNode named after the rule | atomic | positive | section Parsing And CST Construction | covered | CHEV-CST-002, CHEV-CST-005 |
| atomic::tokens key under their token type name and subrules under the rule name | atomic | positive | section Parsing And CST Construction | covered | CHEV-CST-005 |
| atomic::a LABEL replaces the default child key | atomic | positive | section Parsing And CST Construction | covered | CHEV-CST-006 |
| atomic::repeated occurrences merge into one key in input order | atomic | positive | section Parsing And CST Construction + section Grammar Definition | covered | CHEV-CST-007, CHEV-GRM-004 |
| atomic::keys for untaken options are absent from children | atomic | positive | section Parsing And CST Construction | covered | CHEV-CST-008 |
| atomic::MANY parses zero and several repetitions | atomic | positive | section Grammar Definition | covered | CHEV-GRM-011 |
| atomic::MANY_SEP consumes separators between repetitions | atomic | positive | section Grammar Definition | covered | CHEV-GRM-012 |
| atomic::AT_LEAST_ONE_SEP accepts one element and rejects zero | atomic | positive | section Grammar Definition | covered | CHEV-GRM-011, CHEV-GRM-012 |
| atomic::OR applies the first alternative whose lookahead matches | atomic | positive | section Grammar Definition | covered | CHEV-GRM-007 |
| atomic::a GATE excludes its alternative while false | atomic | positive | section Grammar Definition | covered | CHEV-GRM-008 |
| atomic::EMPTY_ALT supplies an always-applicable default branch | atomic | positive | section Grammar Definition | covered | CHEV-GRM-009 |
| atomic::the default lookahead distinguishes alternatives needing three tokens | atomic | positive | section Grammar Definition | covered | CHEV-GRM-010 |
| atomic::arguments flow to rules through direct invocation and SUBRULE ARGS | atomic | positive | section Grammar Definition | covered | CHEV-GRM-005, CHEV-GRM-006 |
| atomic::assigning input resets accumulated errors | atomic | positive | section Parsing And CST Construction | covered | CHEV-CST-001 |
| atomic::a parser is reusable across independent inputs | atomic | positive | section Parsing And CST Construction | covered | CHEV-CST-004 |
| atomic::full node location tracking spans the first through last token | atomic | positive | section Parsing And CST Construction | covered | CHEV-CST-010 |
| atomic::a duplicate rule name fails self-analysis with an aggregate error | atomic | failure_path | section Grammar Validation | covered | CHEV-VAL-001, CHEV-VAL-002 |
| atomic::left recursion fails self-analysis | atomic | failure_path | section Grammar Validation | covered | CHEV-VAL-001, CHEV-VAL-003 |
| atomic::alternatives sharing a full lookahead prefix fail as ambiguous | atomic | failure_path | section Grammar Validation | covered | CHEV-VAL-001, CHEV-VAL-004 |
| atomic::the same grammar constructs when maxLookahead suffices | atomic | positive | section Grammar Validation + section Grammar Definition | covered | CHEV-VAL-004, CHEV-GRM-013 |
| atomic::skipValidations skips ambiguity analysis but not duplicate rules | atomic | positive | section Grammar Validation | covered | CHEV-VAL-005 |
| atomic::consuming a token type outside the vocabulary surfaces at parse time | atomic | positive | section Grammar Validation | covered | CHEV-VAL-006 |
| atomic::a visitor dispatches by rule name and returns method results | atomic | positive | section CST Visitors | covered | CHEV-VIS-001, CHEV-VIS-002 |
| atomic::visit on an array dispatches to the first element | atomic | positive | section CST Visitors | covered | CHEV-VIS-002 |
| atomic::validateVisitor rejects a plain-base visitor missing rule methods | atomic | failure_path | section CST Visitors | covered | CHEV-VIS-004 |
| atomic::a defaults-based visitor accepts a method subset | atomic | positive | section CST Visitors | covered | CHEV-VIS-003, CHEV-VIS-004 |
| atomic::a wrong token at CONSUME records a MismatchedTokenException with context | atomic | positive | section Error Handling And Recovery | covered | CHEV-REC-001, CHEV-REC-002, CHEV-REC-005 |
| atomic::no viable OR alternative records a NoViableAltException | atomic | positive | section Error Handling And Recovery | covered | CHEV-REC-005 |
| atomic::leftover input records NotAllInputParsed and keeps the prefix CST | atomic | positive | section Parsing And CST Construction + section Error Handling And Recovery | covered | CHEV-CST-003, CHEV-REC-005 |
| atomic::an empty mandatory repetition records an EarlyExitException | atomic | positive | section Error Handling And Recovery | covered | CHEV-REC-005 |
| atomic::isRecognitionException separates recognition errors from other values | atomic | positive | section Error Handling And Recovery | covered | CHEV-REC-004 |
| atomic::without recovery a failing rule chain returns undefined | atomic | positive | section Parsing And CST Construction + section Error Handling And Recovery | covered | CHEV-CST-009, CHEV-REC-008 |
| atomic::recovery inserts a missing token flagged isInsertedInRecovery | atomic | positive | section Error Handling And Recovery | covered | CHEV-REC-006, CHEV-REC-007 |
| atomic::recovery deletes an unexpected extra token and completes the parse | atomic | positive | section Error Handling And Recovery | covered | CHEV-REC-006, CHEV-REC-008 |
| atomic::re-synchronization collects skipped tokens into resyncedTokens | atomic | positive | section Error Handling And Recovery | covered | CHEV-REC-006 |
| atomic::getGAstProductions maps each rule name to a Rule instance | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-001 |
| atomic::terminals and non-terminals reference their definitions by identity | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-002, CHEV-GAST-003 |
| atomic::alternations hold one Alternative node per branch | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-002 |
| atomic::separator repetitions expose their separator token type | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-002 |
| atomic::serialized rules carry type, name and nested definitions | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-004 |
| atomic::serializeGrammar agrees with the parser's serialized productions | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-005 |
| atomic::GAstVisitor dispatches once per node kind without recursing | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-006 |
| atomic::generateCstDts declares node and children types per rule | atomic | positive | section Grammar Introspection And Generated Types | covered | CHEV-GAST-007 |
| atomic::embedded rules return computed values instead of CST nodes | atomic | positive | section Embedded Actions | covered | CHEV-EMB-001 |
| atomic::CONSUME returns the matched token inside embedded rules | atomic | positive | section Embedded Actions | covered | CHEV-EMB-001 |
| atomic::embedded parsing failures record the same recognition errors | atomic | positive | section Embedded Actions | covered | CHEV-EMB-002, CHEV-EMB-003 |
| integration::a parser consuming a category accepts every concrete member | integration | positive | section Token Definitions + section Grammar Definition | covered | CHEV-TOK-004, CHEV-GRM-003; Seam: token categories x parser consumption |
| integration::skipped and grouped content flows around the parser untouched | integration | positive | section Tokenization + section Parsing And CST Construction | covered | CHEV-LEX-008, CHEV-LEX-009, CHEV-CST-002; Seam: lexer groups x parse |
| integration::a keyword with longer_alt parses cleanly next to identifiers | integration | positive | section Token Definitions + section Grammar Definition | covered | CHEV-TOK-010, CHEV-GRM-007; Seam: keyword disambiguation x alternation |
| integration::mode-switched tokens parse into one CST across mode boundaries | integration | positive | section Tokenization + section Parsing And CST Construction | covered | CHEV-LEX-012, CHEV-CST-005; Seam: lexer modes x parser |
| integration::custom pattern payloads survive into CST tokens | integration | positive | section Tokenization + section Parsing And CST Construction | covered | CHEV-LEX-014, CHEV-CST-005; Seam: custom pattern x CST |
| integration::lexer groups, errors and tokens partition one noisy input | integration | positive | section Tokenization | covered | CHEV-LEX-009, CHEV-LEX-011, CHEV-LEX-005; Seam: three lexer outputs x one input |
| integration::the same fault yields undefined strictly and a repaired CST tolerantly | integration | positive | section Cross-View Invariants + section Error Handling And Recovery + section Parsing And CST Construction | covered | CHEV-INV-005, CHEV-REC-006, CHEV-CST-009; CVI-5 |
| integration::error context names the rule stack outermost first at the failure point | integration | positive | section Error Handling And Recovery | covered | CHEV-REC-002; Seam: nested rules x error context |
| integration::a prefix CST plus NotAllInputParsed still projects consistent tokens | integration | positive | section Parsing And CST Construction + section Cross-View Invariants | covered | CHEV-CST-003, CHEV-INV-001; Seam: partial parse x round trip |
| integration::recovery mixes insertion and re-sync across several statements | integration | positive | section Error Handling And Recovery | covered | CHEV-REC-006, CHEV-REC-007, CHEV-REC-008; Seam: multi-fault recovery |
| integration::every grammar terminal is a vocabulary token type by identity | integration | positive | section Cross-View Invariants + section Grammar Introspection And Generated Types | covered | CHEV-INV-002, CHEV-GAST-006; CVI-2 |
| integration::serialized productions agree with live ones and name callable rules | integration | positive | section Cross-View Invariants + section Grammar Introspection And Generated Types | covered | CHEV-INV-003, CHEV-GAST-005; CVI-3 |
| integration::observed CST keys all appear in the generated declaration text | integration | positive | section Cross-View Invariants + section Grammar Introspection And Generated Types | covered | CHEV-INV-004, CHEV-GAST-007; CVI-4 |
| integration::optionality in declarations mirrors actual absence across parses | integration | positive | section Grammar Introspection And Generated Types + section Parsing And CST Construction | covered | CHEV-GAST-007, CHEV-CST-008; Seam: dts optionality x CST presence |
| integration::one grammar drives identical repeated parses and stable introspection | integration | positive | section Cross-View Invariants | covered | CHEV-INV-007; CVI-7 |
| integration::token offsets and images agree across lexer, CST and locations | integration | positive | section Cross-View Invariants + section Parsing And CST Construction | covered | CHEV-INV-001, CHEV-INV-006, CHEV-CST-010; CVI-1 |
| integration::an embedded-actions parser and a CST visitor compute the same value | integration | positive | section Embedded Actions + section CST Visitors | covered | CHEV-EMB-001, CHEV-VIS-001; Seam: two computation projections of one grammar |
| integration::visitor parameters thread through nested visits | integration | positive | section CST Visitors | covered | CHEV-VIS-001, CHEV-VIS-002; Seam: visitor params x nested CST |
| integration::gated alternatives steer the same rule differently per invocation | integration | positive | section Grammar Definition | covered | CHEV-GRM-008, CHEV-GRM-005; Seam: ARGS x GATE across invocations |
| integration::an embedded parser aggregates values from labeled subrules | integration | positive | section Embedded Actions + section Grammar Definition | covered | CHEV-EMB-001, CHEV-GRM-012; Seam: embedded values x separated lists |
| integration::a failing embedded parse reports errors while a fresh input computes again | integration | positive | section Embedded Actions + section Parsing And CST Construction | covered | CHEV-EMB-002, CHEV-EMB-003, CHEV-CST-001; Seam: embedded errors x parser reset |
| integration::a manifest language runs from tokens through CST, visitor and introspection | system_e2e | positive | section Cross-View Invariants + section CST Visitors + section Grammar Introspection And Generated Types | covered | CHEV-INV-001, CHEV-INV-002, CHEV-VIS-001, CHEV-GAST-007; CVI-1 |
| integration::an editor-style pass collects every fault yet renders a usable tree | system_e2e | positive | section Cross-View Invariants + section Error Handling And Recovery + section Tokenization | covered | CHEV-INV-005, CHEV-REC-006, CHEV-REC-002, CHEV-LEX-011; CVI-5 |
| integration::a calculator ships twice: embedded values and visited CST stay in lockstep | system_e2e | positive | section Embedded Actions + section CST Visitors + section Grammar Definition + section Cross-View Invariants | covered | CHEV-EMB-001, CHEV-VIS-001, CHEV-GRM-007, CHEV-INV-007; CVI-7 |
| integration::grammar-as-data: one definition audited through every projection | system_e2e | positive | section Cross-View Invariants + section Grammar Introspection And Generated Types | covered | CHEV-INV-002, CHEV-INV-003, CHEV-INV-004, CHEV-GAST-006; CVI-2 |

Total: 98 | kept (covered): 98 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 98

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
