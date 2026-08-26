# Clauses — chevrotain-parser-toolkit-fullrepro-001 (spec_v1)

Clause ID → section anchor + paraphrased contract (verbatim quotes in spec_v1.md).

## Token Definitions (CHEV-TOK)

- CHEV-TOK-001 — createToken accepts { name, pattern } and returns a token type exposing name and PATTERN.
- CHEV-TOK-002 — pattern forms: regex, literal string, custom function, Lexer.NA.
- CHEV-TOK-003 — optional keys: label, categories, longer_alt, group, push_mode, pop_mode, line_breaks.
- CHEV-TOK-004 — tokenMatcher true for own type or transitive category, false otherwise.
- CHEV-TOK-005 — Lexer.NA token type never matched from text; acts as pure category.
- CHEV-TOK-006 — tokenLabel returns label else name; tokenName returns name.
- CHEV-TOK-007 — createTokenInstance builds a token with the eight explicit fields.
- CHEV-TOK-008 — EOF token type; end-of-input recognition errors carry an EOF token with empty image.
- CHEV-TOK-009 — first-match-wins by definition order; no implicit longest-match.
- CHEV-TOK-010 — longer_alt: strictly longer alternative match at same offset wins.
- CHEV-TOK-011 — without longer_alt, earlier keyword pattern splits identifier-prefixed text.

## Tokenization (CHEV-LEX)

- CHEV-LEX-001 — Lexer(array) single mode; Lexer({ modes, defaultMode }) multi-mode.
- CHEV-LEX-002 — config: positionTracking full|onlyStart|onlyOffset (default full), deferDefinitionErrorsHandling (default false).
- CHEV-LEX-003 — /g or /m pattern flags: constructor throws Error naming the token type.
- CHEV-LEX-004 — deferDefinitionErrorsHandling true: no throw, problems on lexerDefinitionErrors.
- CHEV-LEX-005 — tokenize returns { tokens, groups, errors }.
- CHEV-LEX-006 — token fields: image, startOffset, endOffset inclusive (eo-so+1 = image length), 1-based line/column fields, tokenType.
- CHEV-LEX-007 — onlyStart populates only startOffset/startLine/startColumn; onlyOffset populates only startOffset; image and tokenType always present.
- CHEV-LEX-008 — group SKIPPED drops matches entirely.
- CHEV-LEX-009 — string group diverts matches to groups[name] in input order, not in tokens.
- CHEV-LEX-010 — every named group key present in groups even when empty.
- CHEV-LEX-011 — unmatchable input: error { offset, line, column, length, message }, lexer skips and continues; consecutive bad chars merge into one error.
- CHEV-LEX-012 — only active-mode token types match; push_mode/pop_mode switch modes as a stack.
- CHEV-LEX-013 — tokenize(text, initialMode) starts in the named mode.
- CHEV-LEX-014 — custom pattern fn(text, offset) → null | [matched]; payload property lands on token.payload; line_breaks required.

## Grammar Definition (CHEV-GRM)

- CHEV-GRM-001 — subclass CstParser or EmbeddedActionsParser; super(vocab, config?); RULE(name, impl); performSelfAnalysis() after rules.
- CHEV-GRM-002 — rule implementations run once during self-analysis with no arguments (recording).
- CHEV-GRM-003 — CONSUME matches one token of the type (category matches count).
- CHEV-GRM-004 — numbered variants distinguish repeated occurrences within a rule body.
- CHEV-GRM-005 — SUBRULE options: LABEL renames CST key; ARGS passes arguments to callee.
- CHEV-GRM-006 — direct rule method invocation passes arguments to the implementation.
- CHEV-GRM-007 — OR applies first matching alternative in document order.
- CHEV-GRM-008 — GATE predicate: alternative participates only while gate returns true.
- CHEV-GRM-009 — EMPTY_ALT builds an always-applicable empty alternative.
- CHEV-GRM-010 — alternatives distinguished within maxLookahead tokens (default 3).
- CHEV-GRM-011 — OPTION zero-or-one; MANY zero-or-more; AT_LEAST_ONE one-or-more (EarlyExit on zero).
- CHEV-GRM-012 — MANY_SEP / AT_LEAST_ONE_SEP parse separated lists with SEP between DEF repetitions.
- CHEV-GRM-013 — parser config: maxLookahead 3, recoveryEnabled false, nodeLocationTracking "none", skipValidations false.

## Grammar Validation (CHEV-VAL)

- CHEV-VAL-001 — definition errors: performSelfAnalysis throws Error starting "Parser Definition Errors detected" describing all problems.
- CHEV-VAL-002 — duplicate rule name is a definition error.
- CHEV-VAL-003 — left recursion is a definition error.
- CHEV-VAL-004 — ambiguous alternatives within maxLookahead is a definition error; lowering maxLookahead can induce it.
- CHEV-VAL-005 — skipValidations true skips ambiguity analysis; duplicates still throw.
- CHEV-VAL-006 — consuming a token type absent from the vocabulary is not a definition error; surfaces at parse time as recognition error.

## Parsing And CST Construction (CHEV-CST)

- CHEV-CST-001 — assigning input resets parser state including errors.
- CHEV-CST-002 — rule methods callable; entry rule returns CstNode.
- CHEV-CST-003 — leftover tokens: NotAllInputParsedException recorded; prefix CST still returned.
- CHEV-CST-004 — parser reusable across inputs.
- CHEV-CST-005 — CstNode { name, children }; token children under token type name; subrule children under rule name.
- CHEV-CST-006 — LABEL replaces the default key.
- CHEV-CST-007 — children values are arrays in input order; numbered variants merge into one key.
- CHEV-CST-008 — keys for untaken constructs are absent.
- CHEV-CST-009 — recovery disabled + recognition error → invocation returns undefined, errors populated.
- CHEV-CST-010 — nodeLocationTracking full: location { startOffset, startLine, startColumn, endOffset, endLine, endColumn } spanning first..last token; none: not populated.

## CST Visitors (CHEV-VIS)

- CHEV-VIS-001 — getBaseCstVisitorConstructor: subclass has one method per rule (children, param?) → value.
- CHEV-VIS-002 — visit(node) dispatches by rule name and returns method result; visit(array) visits first element.
- CHEV-VIS-003 — getBaseCstVisitorConstructorWithDefaults: default traversal for unimplemented rules, returns nothing.
- CHEV-VIS-004 — validateVisitor throws Error naming missing methods for plain-base visitors; defaults-based validates with any subset.

## Error Handling And Recovery (CHEV-REC)

- CHEV-REC-001 — parser.errors accumulates recognition exceptions since input assignment.
- CHEV-REC-002 — exception fields: name, message, token, resyncedTokens, context.ruleStack (outermost first), context.ruleOccurrenceStack.
- CHEV-REC-003 — end-of-input failures carry an EOF-matching token with empty image.
- CHEV-REC-004 — isRecognitionException true for recognition exceptions, false otherwise.
- CHEV-REC-005 — four kinds: MismatchedTokenException, NoViableAltException, NotAllInputParsedException, EarlyExitException; instance .name equals class name.
- CHEV-REC-006 — recoveryEnabled: single-token deletion, single-token insertion, re-sync collecting resyncedTokens.
- CHEV-REC-007 — inserted token: empty image, all positions -1, isInsertedInRecovery true.
- CHEV-REC-008 — recovered parse returns CST alongside recorded errors; one error per fault either way.

## Grammar Introspection And Generated Types (CHEV-GAST)

- CHEV-GAST-001 — getGAstProductions: rule name → Rule instance; Rule { name, definition }.
- CHEV-GAST-002 — node classes exported: Terminal { terminalType, idx }, NonTerminal { nonTerminalName, referencedRule }, Option, Alternation (definition of Alternative), Alternative, Repetition, RepetitionMandatory, RepetitionWithSeparator { separator }, RepetitionMandatoryWithSeparator { separator }.
- CHEV-GAST-003 — composite nodes hold children in grammar order in definition.
- CHEV-GAST-004 — serialized node: type = class name; Rule { name, orgText, definition }; Terminal { name, label, idx, pattern (regex source) }; NonTerminal { name, idx } no nested definition; composites { idx, definition }.
- CHEV-GAST-005 — serializeGrammar(rules) / serializeProduction(node); serializeGrammar of productions equals getSerializedGastProductions.
- CHEV-GAST-006 — GAstVisitor: visit dispatches once by node kind; no auto recursion.
- CHEV-GAST-007 — generateCstDts: per rule an interface {Pascal}CstNode extends CstNode with literal name and children; a {Pascal}CstChildren type with a property per child key; token keys IToken[]; conditional keys optional; ICstNodeVisitor with a method per rule.

## Embedded Actions (CHEV-EMB)

- CHEV-EMB-001 — EmbeddedActionsParser: CONSUME returns the token; SUBRULE returns the callee's value; rule method returns the implementation's value; no CST.
- CHEV-EMB-002 — DSL, validation, errors, recovery semantics identical to CstParser.
- CHEV-EMB-003 — failed rule invocation (recovery off) does not yield a computed result; errors authoritative.

## Error Semantics (CHEV-ERR)

- CHEV-ERR-001 — the condition → outcome table (lexer definition, lexing runtime, three parser definition kinds, four recognition kinds, visitor validation).
- CHEV-ERR-002 — recognition exceptions recorded not thrown; undefined result for failed chain without recovery.

## Cross-View Invariants (CHEV-INV)

- CHEV-INV-001 — CST leaf tokens flattened by startOffset equal the lexer token vector exactly.
- CHEV-INV-002 — Terminals reference vocabulary token types by identity; NonTerminal.referencedRule is the registered Rule.
- CHEV-INV-003 — serializeGrammar(productions) equals getSerializedGastProductions; serialized names callable on the parser.
- CHEV-INV-004 — observed CST child keys appear in generateCstDts children type; absent-capable keys optional.
- CHEV-INV-005 — recovery off: non-empty errors ⇔ undefined result; recovery on: CST returned, fabricated tokens flagged isInsertedInRecovery with empty image.
- CHEV-INV-006 — real tokens: endOffset - startOffset + 1 = image.length; full tracking line/column agree with offsets.
- CHEV-INV-007 — same input twice through same parser: equal CSTs, errors, introspection — grammar immutable after analysis.
