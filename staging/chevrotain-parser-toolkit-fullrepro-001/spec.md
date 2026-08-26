# chevrotain Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`chevrotain` is a parser building toolkit for JavaScript and TypeScript. A caller defines token types with `createToken`, groups them into a `Lexer` that turns text into a token stream, and writes grammar rules as ordinary methods inside a parser subclass. The toolkit interprets those rules directly — there is no code generation step — analyzing the grammar once at construction time to compute lookahead decisions, validate the grammar, and expose it for introspection.

One grammar definition projects into several public views: the token stream (with token groups, skipped content, and structured lexing errors); a concrete syntax tree built automatically by `CstParser` and traversable through generated visitor base classes; a structured parse-error list with typed recognition exceptions and optional fault-tolerant recovery; a grammar introspection surface of production objects and their JSON serialization; and generated TypeScript declaration text describing the exact CST shape of every rule.

The installable package name is `chevrotain`. All functionality is reachable through named exports of the package root.

## Non-Goals

- This specification does not require rendering railroad or syntax diagrams, nor any HTML generation.
- This specification does not require custom lookahead strategies, exposure of lookahead path computation, or global cache management utilities.
- This specification does not define backtracking predicates or scanner-less parsing.
- This specification does not define customization of error message text through provider objects; only the structured fields of errors described here are contractual.
- This specification does not require performance-oriented options (optimization hints, character-set hints, safe mode) to have any observable effect beyond accepting their configuration keys.
- This specification does not define incremental, streaming, or asynchronous lexing or parsing.
- This specification does not require a command-line interface.

## Representative Workflows

Tokens, a lexer, a parser and a visitor cooperate over one grammar; the CST is produced automatically.

```ts
import { createToken, Lexer, CstParser } from "chevrotain";

const WhiteSpace = createToken({ name: "WhiteSpace", pattern: /\s+/, group: Lexer.SKIPPED });
const Comma      = createToken({ name: "Comma", pattern: /,/ });
const Integer    = createToken({ name: "Integer", pattern: /\d+/ });
const allTokens  = [WhiteSpace, Comma, Integer];
const lexer      = new Lexer(allTokens);

class ListParser extends CstParser {
  constructor() {
    super(allTokens);
    const $ = this;
    $.RULE("list", () => {
      $.AT_LEAST_ONE_SEP({ SEP: Comma, DEF: () => $.CONSUME(Integer) });
    });
    this.performSelfAnalysis();
  }
}

const parser = new ListParser();
const lexed = lexer.tokenize("4, 8, 15");
parser.input = lexed.tokens;
const cst = parser.list();          // CstNode { name: "list", children: { Integer: [...], Comma: [...] } }
parser.errors;                       // []

const BaseVisitor = parser.getBaseCstVisitorConstructor();
class SumVisitor extends BaseVisitor {
  constructor() { super(); this.validateVisitor(); }
  list(children) {
    return children.Integer.reduce((acc, tok) => acc + Number(tok.image), 0);
  }
}
new SumVisitor().visit(cst);         // 27
```

The same grammar answers introspection queries, reports structured errors, and recovers from faults when enabled:

```ts
import { generateCstDts, isRecognitionException } from "chevrotain";

parser.getGAstProductions();             // { list: Rule { ... } }
generateCstDts(parser.getGAstProductions()); // "...interface ListCstNode extends CstNode..."

parser.input = lexer.tokenize("4, , 15").tokens;
parser.list();                           // undefined — recovery is off by default
isRecognitionException(parser.errors[0]) // true
parser.errors[0].name                    // "MismatchedTokenException"
```

## Token Definitions

Token types are the vocabulary shared by the lexer and the parser; each is created once and referenced everywhere by identity.

**Creating token types.** `createToken` accepts a configuration object with a required `name` (a unique string) and a `pattern`, and returns a token type object exposing `name` and `PATTERN` properties. The `pattern` is a regular expression, a literal string (matched verbatim), a custom matcher function, or the special value `Lexer.NA`. Optional keys refine behavior: `label` (a human-readable alias), `categories` (one token type or an array of token types this type also matches as), `longer_alt` (one alternative token type, or an array of them, to prefer when it matches a longer prefix at the same position), `group` (either `Lexer.SKIPPED` or a string group name), `push_mode` and `pop_mode` (lexer mode switching), and `line_breaks` (declares whether the pattern matches line terminators; required for custom matcher functions).

**Category matching.** `tokenMatcher(token, tokenType)` returns `true` when the token's own type is `tokenType` or when `tokenType` appears in the token type's category chain (categories apply transitively), and `false` otherwise. A token type whose pattern is `Lexer.NA` is never matched from text; it exists purely as a category. `tokenLabel(tokenType)` returns the `label` when one was configured and the `name` otherwise; `tokenName(tokenType)` returns the `name`.

**Manual tokens.** `createTokenInstance(tokenType, image, startOffset, endOffset, startLine, endLine, startColumn, endColumn)` builds a single token object with exactly those fields, usable wherever lexer-produced tokens are. The exported `EOF` token type represents end of input; recognition errors raised at end of input carry a token matching `EOF` whose `image` is the empty string.

**Keyword versus identifier.** Token order in the lexer definition decides ties: the first token type whose pattern matches at the current offset wins, even if a later type would match a longer prefix. WHEN a token type declares `longer_alt` and one of the named alternatives matches a strictly longer prefix at the same offset, THEN the lexer must emit the longer alternative's token instead. Without `longer_alt`, a keyword pattern listed before an identifier pattern must split identifier-prefixed text (for example `let` followed by `tuce`) rather than yield the longer identifier.

## Tokenization

A `Lexer` turns text into the token-stream projection: matched tokens, named groups, and structured errors, with configurable position tracking.

**Construction.** `new Lexer(tokenTypes)` accepts an array of token types (single mode). `new Lexer({ modes, defaultMode })` accepts a multi-mode definition: `modes` maps mode names to token type arrays and `defaultMode` names the starting mode. A second config argument accepts `positionTracking` (`"full"`, the default; `"onlyStart"`; or `"onlyOffset"`) and `deferDefinitionErrorsHandling` (defaults to `false`).

**Definition validation.** WHEN a token type's regular expression pattern uses the global or multiline flags, THEN the `Lexer` constructor must throw an `Error` whose message identifies the offending token type. Where `deferDefinitionErrorsHandling` is `true`, the constructor must not throw; the same problems are exposed on the instance's `lexerDefinitionErrors` array instead.

**Tokenizing.** `tokenize(text)` returns an object with `tokens`, `groups`, and `errors`. Under the default `"full"` position tracking each token carries `image` (the matched text), `startOffset` and `endOffset` (zero-based; `endOffset` is the offset of the last character, so `endOffset - startOffset + 1` equals the image length), `startLine`, `endLine`, `startColumn`, `endColumn` (all one-based), and `tokenType` (the matching token type object). Under `positionTracking: "onlyStart"` only the start fields are populated: `startOffset`, `startLine`, and `startColumn` (no end fields). Under `"onlyOffset"` only `startOffset` is populated among the position fields. `image` and `tokenType` are always populated.

**Groups and skipping.** WHEN a token type's `group` is `Lexer.SKIPPED`, THEN its matches are dropped: they appear in neither `tokens` nor `groups`. WHEN `group` is a string, THEN its matches are diverted into `groups[name]` (in input order) and do not appear in `tokens`. Every string group named by any token type in the definition must be present as a key of `groups`, with an empty array when nothing matched.

**Lexing errors.** WHEN no token type matches at the current offset, THEN the lexer must record an error object with `offset`, `line`, `column`, `length`, and `message` fields, skip ahead, and continue tokenizing; the surrounding matchable text must still be returned in `tokens`. Consecutive unmatchable characters are merged into a single error whose `length` covers them.

**Modes.** In a multi-mode lexer, only the token types of the active mode participate in matching. WHEN a matched token type declares `push_mode`, THEN the named mode becomes active for subsequent input; WHEN it declares `pop_mode: true`, THEN the lexer returns to the previous mode on the stack. `tokenize(text, initialMode)` accepts a mode name as its second argument and starts in that mode instead of `defaultMode`.

**Custom patterns.** A pattern function receives the full text and the current offset and must return `null` for no match or an array whose first element is the matched string. WHEN the returned array carries a `payload` property, THEN the emitted token exposes that value as its `payload` field. Custom-pattern token types must declare `line_breaks`.

## Grammar Definition

A grammar is declared inside a parser subclass as methods that call the parsing DSL; construction records and analyzes the grammar once.

**Parser subclass protocol.** A parser extends `CstParser` (automatic CST building) or `EmbeddedActionsParser` (rules return values). The subclass constructor must call `super(tokenVocabulary, config?)` with the token types (an array, or the same structure given to the lexer), define each rule as `this.RULE(name, implementation)` which returns the callable rule, and call `this.performSelfAnalysis()` after all rules are defined. Rule implementations run once during self-analysis with no arguments to record the grammar, so logic inside them must tolerate absent arguments.

**Consuming and invoking.** Inside a rule, `CONSUME(tokenType)` matches one token of that type (a token also matches by category). `SUBRULE(ruleRef)` invokes another rule. Both have numbered variants (`CONSUME1`…, `SUBRULE1`…) that distinguish repeated uses of the same token type or rule within one rule body; each syntactic occurrence in a rule must use a distinct number. `SUBRULE` accepts an options object with `LABEL` (renames the CST key) and `ARGS` (an array of arguments passed to the callee's implementation). Invoking a rule method directly on the parser passes its arguments straight to the implementation.

**Alternation.** `OR(alternatives)` takes an array of `{ ALT }` objects and applies the first alternative whose lookahead matches, in document order. An alternative with a `GATE` predicate participates only while the gate returns `true`. `EMPTY_ALT(value)` builds an always-applicable empty alternative for trailing default cases. Alternatives are distinguished by at most `maxLookahead` tokens of lookahead (a parser config key defaulting to 3).

**Repetition and options.** `OPTION(fn)` parses its content zero or one time. `MANY(fn)` parses zero or more repetitions. `AT_LEAST_ONE(fn)` parses one or more and fails with a recognition error on zero. `MANY_SEP({ SEP, DEF })` and `AT_LEAST_ONE_SEP({ SEP, DEF })` parse separated lists, consuming the separator token type between repetitions of `DEF`.

**Parser configuration.** The `CstParser` and `EmbeddedActionsParser` constructors accept a config object with `maxLookahead` (defaults to 3), `recoveryEnabled` (defaults to `false`), `nodeLocationTracking` (`"none"`, the default; `"onlyOffset"`; or `"full"`), and `skipValidations` (defaults to `false`).

## Grammar Validation

Self-analysis validates the recorded grammar and refuses to build a defective parser.

**Aggregate failure.** WHEN the grammar contains definition errors, THEN `performSelfAnalysis` must throw an `Error` whose message begins with `Parser Definition Errors detected` and describes every detected problem.

**Detected defects.** Each of the following is a definition error: two rules defined with the same name (the message names the duplicated rule); a rule that reaches itself without first consuming a token, directly or through other rules (left recursion, with the cycle participants named); and an alternation whose alternatives cannot be distinguished within `maxLookahead` tokens (ambiguous alternatives, with the colliding alternative numbers and the common token prefix named). Lowering `maxLookahead` below what the grammar needs turns an otherwise valid alternation into an ambiguity error.

**Validation scope.** Where `skipValidations` is `true`, ambiguity analysis is skipped and such a parser constructs successfully; structural defects (duplicate rule names) must still throw. Consuming a token type absent from the parser's token vocabulary is not a definition error: it surfaces at parse time as a recognition error on the first attempt to match it.

## Parsing And CST Construction

A `CstParser` builds a concrete syntax tree automatically from the rule structure; the tree mirrors the grammar, not the implementation.

**Feeding input and invoking.** Assigning a token array to the parser's `input` property resets all parser state, including the `errors` list. Each rule defined with `RULE` is callable as a method; calling the entry rule parses the whole input and returns a `CstNode`. WHEN tokens remain after the entry rule completes, THEN the parser must record a recognition error of kind `NotAllInputParsedException` (the CST for the parsed prefix is still returned). A parser instance is reusable: assigning fresh `input` starts an independent parse.

**CST shape.** A `CstNode` has `name` (the rule name) and `children` (an object). Every token consumed in the rule appears under its token type name; every subrule result appears under the invoked rule's name; a `LABEL` on `CONSUME` or `SUBRULE` replaces the default key with the label. All values are arrays in input order, and numbered occurrence variants of the same token type or rule merge into the same key unless labeled apart. Keys for constructs not taken in this parse (an option not entered, a repetition with zero iterations) are absent from `children`.

**Failure result.** WHEN recovery is disabled and a recognition error occurs inside a rule invocation, THEN the invocation returns `undefined` and `errors` holds the failure; no partial CST is produced for the failed rule chain.

**Node locations.** Where `nodeLocationTracking` is `"full"`, every `CstNode` exposes a `location` object with `startOffset`, `startLine`, `startColumn`, `endOffset`, `endLine`, and `endColumn` spanning the node's first through last consumed token. Where it is `"none"` (the default), `location` is not populated.

## CST Visitors

Visitor base classes generated from the grammar traverse CSTs with one method per rule.

**Obtaining a base class.** `getBaseCstVisitorConstructor()` returns a class whose subclasses implement one method per grammar rule; each method receives the node's `children` object and an optional parameter, and returns any value. `visit(cstNode)` dispatches to the method named by the node's rule and returns its result; `visit` also accepts an array of nodes, visiting the first element. `getBaseCstVisitorConstructorWithDefaults()` returns a base class that supplies a default traversal for every rule the subclass does not implement (the default visits children and returns nothing).

**Visitor validation.** `validateVisitor()` checks the subclass against the grammar. WHEN a visitor obtained from the plain base class is missing a method for any grammar rule, THEN `validateVisitor` must throw an `Error` naming each missing method. A defaults-based visitor validates successfully with any subset of methods.

## Error Handling And Recovery

Parse failures are structured values on the parser, and an opt-in recovery mode repairs the token stream to keep parsing.

**The errors list.** `parser.errors` is an array of recognition exceptions accumulated since `input` was last assigned. Every recognition exception carries `name` (its kind), `message`, `token` (the offending token; a token matching `EOF` with empty `image` when the failure is at end of input), `resyncedTokens` (tokens skipped during recovery), and `context` with `ruleStack` (the rule names active at failure, outermost first) and `ruleOccurrenceStack`. `isRecognitionException(err)` returns `true` for recognition exceptions and `false` for other values.

**Exception kinds.** `MismatchedTokenException` — a `CONSUME` saw a token of the wrong type; `NoViableAltException` — no `OR` alternative matched the lookahead; `NotAllInputParsedException` — input remained after the entry rule; `EarlyExitException` — an `AT_LEAST_ONE` or `AT_LEAST_ONE_SEP` matched zero iterations. The exception classes are exported under these names, and each instance's `name` field equals its class name.

**Recovery.** Where `recoveryEnabled` is `true`, the parser attempts fault-tolerant repair instead of aborting the rule chain: single-token deletion (skip one unexpected token and continue), single-token insertion (fabricate the missing token and continue), and re-synchronization (skip tokens — collected into `resyncedTokens` — until a follow-set token appears). An inserted token has empty `image`, all position fields set to `-1`, and `isInsertedInRecovery: true`. A recovered parse returns a CST covering the repaired input alongside the recorded errors. Errors are recorded exactly once per fault whether or not recovery is enabled.

## Grammar Introspection And Generated Types

The analyzed grammar is itself data: production objects, their JSON serialization, and generated TypeScript declarations all describe the same rules.

**Production objects.** `getGAstProductions()` returns an object mapping each rule name to a `Rule` instance. A `Rule` has `name` and `definition` (an array of grammar nodes). The node classes are exported: `Terminal` (with `terminalType` referencing the consumed token type and `idx` for the occurrence number), `NonTerminal` (with `nonTerminalName` and `referencedRule`), `Option`, `Alternation` (whose `definition` holds `Alternative` nodes, one per `ALT`), `Alternative`, `Repetition`, `RepetitionMandatory`, `RepetitionWithSeparator` and `RepetitionMandatoryWithSeparator` (both with `separator` referencing the separator token type). Each composite node's `definition` array holds its child nodes in grammar order.

**Serialization.** `getSerializedGastProductions()` returns an array of plain JSON objects, one per rule, in definition order. A serialized node carries `type` (the node class name), plus per kind: `Rule` — `name`, `orgText`, `definition`; `Terminal` — `name` (the token type name), `label`, `idx`, and `pattern` (the regular expression source text when the pattern is a regular expression); `NonTerminal` — `name` (the referenced rule name) and `idx`, with no nested `definition`; composite kinds — `idx` and nested `definition`. `serializeGrammar(rules)` maps `Rule` instances to the same serialized forms; `serializeProduction(node)` serializes a single node. The serialization of `getGAstProductions()`'s values equals `getSerializedGastProductions()`.

**Grammar walking.** `GAstVisitor` is an exported base class for single-node dispatch over grammar nodes: `visit(node)` calls the subclass method for the node's kind (`visitTerminal`, `visitNonTerminal`, `visitOption`, `visitAlternation`, `visitAlternative`, `visitRepetition`, `visitRepetitionMandatory`, `visitRepetitionWithSeparator`, `visitRepetitionMandatoryWithSeparator`, `visitRule`). `visit` does not recurse into `definition` arrays on its own; traversal order is the caller's choice.

**Generated declarations.** `generateCstDts(productions)` returns TypeScript source text describing the CST of every rule: for each rule an interface named by the PascalCased rule name suffixed with `CstNode` (extending `CstNode`, with a literal `name` and a `children` field), and a children type suffixed with `CstChildren` containing one property per possible child key — token keys typed as `IToken[]`, subrule keys as the child rule's node type array, labeled keys under their label. WHEN a child key is not guaranteed to be present on every parse of the rule (it originates inside an option, repetition, or a non-covering alternation branch), THEN its property must be marked optional. The output also declares an `ICstNodeVisitor` interface with one method per rule.

## Embedded Actions

`EmbeddedActionsParser` trades automatic CST building for direct computation inside the rules.

**Return values.** In an `EmbeddedActionsParser` subclass, `CONSUME` returns the matched token, `SUBRULE` returns the invoked rule's return value, and the value returned by a rule's implementation function is returned by the rule method itself. No CST is constructed. The DSL, validation, `errors`, and recovery semantics are the same as for `CstParser`. WHEN a recognition error occurs with recovery disabled, THEN the failed rule invocation's return value is not a computed result (the recorded recognition error in `errors` is authoritative).

## State Model

The core state is the token vocabulary plus the recorded grammar, both fixed at construction time. Per parse, the mutable state is the assigned token vector, the current position, and the accumulated errors — all reset when `input` is assigned.

Public projections of one grammar definition:

1. **Token stream** — `Lexer.tokenize` with `tokens`, `groups`, and `errors`.
2. **Concrete syntax tree** — `CstParser` rule invocation with automatic child keying.
3. **Computed values** — `EmbeddedActionsParser` rule invocation returning embedded results.
4. **Structured failures** — `parser.errors` with typed recognition exceptions and recovery artifacts.
5. **Grammar data** — `getGAstProductions`, serialized productions, and `GAstVisitor` dispatch.
6. **Declaration text** — `generateCstDts` describing every rule's CST shape.

## Error Semantics

| Condition | Outcome |
|---|---|
| Token pattern uses global or multiline regex flags | `Lexer` constructor throws an `Error` naming the token type (or records it in `lexerDefinitionErrors` under `deferDefinitionErrorsHandling`) |
| No token type matches at an offset during `tokenize` | error object appended to the result's `errors` with `offset`, `line`, `column`, `length`, `message`; lexing continues |
| Duplicate rule name | `performSelfAnalysis` throws an `Error` beginning `Parser Definition Errors detected` |
| Left-recursive rule | same aggregate `Error` |
| Alternatives indistinguishable within `maxLookahead` | same aggregate `Error` (skipped under `skipValidations`) |
| `CONSUME` sees a token of the wrong type | `MismatchedTokenException` appended to `parser.errors` |
| No `OR` alternative matches | `NoViableAltException` appended to `parser.errors` |
| Tokens remain after the entry rule | `NotAllInputParsedException` appended to `parser.errors` |
| `AT_LEAST_ONE`/`AT_LEAST_ONE_SEP` matches zero iterations | `EarlyExitException` appended to `parser.errors` |
| Visitor from the plain base class missing a rule method | `validateVisitor` throws an `Error` naming the missing methods |

Recognition exceptions are recorded, not thrown, during parsing; rule invocation returns `undefined` for the failed chain when recovery is disabled.

## Cross-View Invariants

1. For any successful parse, the tokens reachable in the CST (all `children` leaf arrays, flattened and ordered by `startOffset`) must be exactly the token vector produced by the lexer — same images, same offsets, no token duplicated or dropped.
2. Every `Terminal` in `getGAstProductions()` must reference a token type from the parser's vocabulary by identity, and every `NonTerminal`'s `referencedRule` must be the `Rule` object registered under its `nonTerminalName` — the grammar data projection is closed over the definition.
3. `JSON`-serializing the values of `getGAstProductions()` via `serializeGrammar` must equal `getSerializedGastProductions()`, and each serialized rule's `name` must be callable as a rule method on the parser.
4. For every rule, the child keys observed in any CST it produces must appear as properties of that rule's children type in `generateCstDts` output, and keys not guaranteed present must be optional there.
5. WHEN recovery is disabled, a non-empty `errors` after an entry-rule invocation must coincide with an `undefined` result; WHEN recovery is enabled for the same grammar and input, the invocation must return a CST and every fabricated token in it must carry `isInsertedInRecovery: true` and an empty `image`.
6. For every real (non-inserted) token produced under full position tracking, `endOffset - startOffset + 1` must equal `image.length`, and the line/column fields must agree with the offsets given the line terminators in the input.
7. Driving the same input through the same parser twice (reassigning `input` between runs) must produce equal CSTs, equal `errors`, and equal introspection output — parses are independent and the grammar is immutable after analysis.

## Public Interface

### Import Surface

```ts
import {
  createToken,
  createTokenInstance,
  tokenMatcher,
  tokenLabel,
  tokenName,
  EOF,
  Lexer,
  CstParser,
  EmbeddedActionsParser,
  EMPTY_ALT,
  isRecognitionException,
  MismatchedTokenException,
  NoViableAltException,
  NotAllInputParsedException,
  EarlyExitException,
  GAstVisitor,
  Rule,
  Terminal,
  NonTerminal,
  Option,
  Alternation,
  Alternative,
  Repetition,
  RepetitionMandatory,
  RepetitionWithSeparator,
  RepetitionMandatoryWithSeparator,
  serializeGrammar,
  serializeProduction,
  generateCstDts,
} from "chevrotain";
```

`Lexer.SKIPPED` and `Lexer.NA` are static properties of the `Lexer` class.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `createToken` | function | Build a token type from a configuration object |
| `createTokenInstance` | function | Build a single token object with explicit fields |
| `tokenMatcher` | function | Test a token against a token type, honoring categories |
| `tokenLabel` | function | A token type's label, falling back to its name |
| `tokenName` | function | A token type's name |
| `EOF` | token type | End-of-input token type carried by errors at end of input |
| `Lexer` | class | Tokenize text into tokens, groups, and errors |
| `CstParser` | class | Parser base class with automatic CST building |
| `EmbeddedActionsParser` | class | Parser base class whose rules return computed values |
| `EMPTY_ALT` | function | Always-applicable empty alternative for `OR` |
| `isRecognitionException` | function | Test whether a value is a recognition exception |
| `MismatchedTokenException` | class | Wrong token type at a `CONSUME` |
| `NoViableAltException` | class | No alternative matched at an `OR` |
| `NotAllInputParsedException` | class | Input remained after the entry rule |
| `EarlyExitException` | class | Mandatory repetition matched zero iterations |
| `GAstVisitor` | class | Single-node dispatch visitor over grammar nodes |
| `Rule` | class | Grammar production: rule name plus definition nodes |
| `Terminal` | class | Grammar node: token consumption |
| `NonTerminal` | class | Grammar node: rule invocation |
| `Option` | class | Grammar node: optional group |
| `Alternation` | class | Grammar node: alternative set |
| `Alternative` | class | Grammar node: one branch of an alternation |
| `Repetition` | class | Grammar node: zero-or-more group |
| `RepetitionMandatory` | class | Grammar node: one-or-more group |
| `RepetitionWithSeparator` | class | Grammar node: zero-or-more with separator |
| `RepetitionMandatoryWithSeparator` | class | Grammar node: one-or-more with separator |
| `serializeGrammar` | function | JSON forms of an array of `Rule` objects |
| `serializeProduction` | function | JSON form of one grammar node |
| `generateCstDts` | function | TypeScript declaration text for every rule's CST shape |

### CLI Entry Points

There is no console script for this package. Programmatic use is through the package's named exports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. Tests execute with `vitest` under TypeScript (`typescript`, `@types/node` available). No third-party runtime dependencies are required or available to the implementation at runtime; the package must function self-contained.

The project must be an installable npm package named `chevrotain` whose root entry point provides the named exports listed in Public Interface, resolvable by Node.js under both ESM `import` and TypeScript `NodeNext` resolution. The assessment environment provides the same runtime and module resolution.

## Appendix B: Assessment Notes

Assessment exercises the public API only, in three dimensions: (1) atomic behavior — token type creation and category matching, tokenize output fields and position tracking modes, groups and skipping, lexer modes, custom patterns and payloads, lexer and parser definition errors, the parsing DSL and its CST keying, recognition exception kinds and their structured fields, visitor generation and validation, grammar introspection objects and serialized forms, and generated declaration text; (2) integration — combinations that span projections, such as lexer-to-parser pipelines with categories and modes, fault-tolerant parses compared against strict parses, grammar data agreeing with observed CST shapes, and embedded-actions results agreeing with CST-derived computation; (3) end-to-end workflows — full pipelines from token definition through lexing, parsing, error recovery, visiting, and introspection over one grammar. Expected values are concrete token fields, CST child keys, error kinds, and serialized grammar structures computed from the rules in this document. Each test is assessed independently.
