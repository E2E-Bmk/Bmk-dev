# mvdan sh Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in interface design, parameter naming, behavioral edge cases, and error semantics.
> Implementations derived from memory of external codebases will fail the evaluation.

# Context

## Product Overview

`mvdan.cc/sh/v3` is a Go shell-language toolkit that parses, walks, formats, expands, and interprets POSIX-like shell programs. The syntax tree is shared by the parser, printer, expansion engine, interpreter, `shfmt`, and `gosh`, which makes source locations and language variants part of one behavioral contract.

Execution is caller controlled. Environment, directory, parameters, standard streams, filesystem operations, and command dispatch enter through explicit runner options and handlers.

## Non-Goals

- This specification does not require delegation to a host shell, unrestricted process execution, network commands, or system startup files.
- This specification does not define byte identity for source programs that differ only by accepted formatting.
- This specification does not require undocumented syntax nodes, internal parser tables, or host-global environment changes.

# Orientation

## Representative Workflows

### Workflow 1: Parse, format, and reparse

1. Create a `syntax.Parser` with a language variant and comment policy.
2. Parse a program into a `syntax.File`, walk its statements and words, and observe positions.
3. Print the file with a configured `syntax.Printer`.
4. Parse the printed program again with the same variant.
5. Run both trees with isolated environments and writers, then compare exit state and observable effects.

### Workflow 2: Expand and execute in a sandbox

1. Create an `expand.Environ` and configure expansion with controlled directory, command substitution, and filesystem callbacks.
2. Expand words containing parameters, quoting, globs, arithmetic, and command substitution.
3. Create an `interp.Runner` with the same environment, directory, parameters, streams, and caller-owned handlers.
4. Run functions, pipelines, redirections, substitutions, and exit status changes.
5. Reset the runner and execute a second program, confirming that retained options and reset execution state follow the public lifecycle.

### Workflow 3: Capture a coherent shell receipt

1. Create a `receipt.ShellPlan`, select one named source, and enable the syntax, formatted, expansion, and execution projections required by the caller.
2. Parse and print with one language variant, expand with one environment generation, and run with caller-controlled effect handlers.
3. Record filesystem and command effects in a caller-owned `receipt.EffectJournal` in observation order.
4. Call `receipt.Capture` only after the requested projections are complete; a failure in any requested projection publishes no partial receipt.
5. Validate the receipt, compare it with a later generation, and use `receipt.Diff` to identify semantic changes without treating temporary paths or timing as behavior.

# Behavior

## Domain 1: Syntax Trees and Formatting

This domain defines language variants, source positions, tree structure, walking, and stable printing.

**Parsing.** When `Parser.Parse` reads valid input, it must return a `File` whose statements, commands, assignments, redirects, words, functions, substitutions, and positions preserve source order. Where `Variant`, `KeepComments`, `StopAt`, or `RecoverErrors` is present, parsing must apply that option to the complete input family. If syntax is invalid for the selected `LangVariant`, then parsing must return `ParseError` or `LangError`; `IsIncomplete` must distinguish an unfinished construct from a complete invalid construct.

**Walking and positions.** When `Walk` visits a tree, it must visit each reachable node in lexical tree order and stop descending below a node when the callback returns false. Every valid `Pos` must report stable offset, line, and column values for the original source. If a caller passes a nil node, then walking must return without a callback invocation.

**Printing.** When `Printer.Print` receives a valid node, it must preserve the selected language semantics while applying indentation, binary-line, switch-case, redirect-spacing, minification, and function-line options. Reprinting reparsed output with identical options must return identical bytes. If the writer fails, then printing must return that error without reporting success.

## Domain 2: Expansion, Patterns, and Environments

This domain defines how syntax words become fields, literals, documents, arithmetic values, and regular expressions.

**Environment ownership.** When `ListEnviron` or `FuncEnviron` creates an environment, `Get` and `Each` must expose the same variable names, values, kinds, and flags. Where a `WriteEnviron` is present, assignment must update that environment according to export, readonly, scalar, indexed, and associative semantics. If assignment targets a readonly variable or invalid name, then it must return an error without changing the prior value.

**Word expansion.** When `expand.Fields` processes words, it must apply parameter expansion, command substitution, arithmetic, field splitting, globbing, and quote removal in shell-language order. `Literal`, `Document`, and `Pattern` must project the same syntax word for their narrower documented contexts. If an unset parameter is required or command substitution lacks a callback, then expansion must return `UnsetParameterError` or `UnexpectedCommandError`.

**Patterns and braces.** When `pattern.Regexp` receives a valid shell pattern and mode, it must return a regular expression with matching shell semantics; `HasMeta` and `QuoteMeta` must agree about active metacharacters. When `Braces` or `SplitBraces` handles a brace expression, it must preserve sequence and alternative order. If syntax is invalid, then pattern conversion must return `SyntaxError` or `NegExtGlobError`.

## Domain 3: Interpreter State and Controlled Effects

This domain defines runner lifecycle, function scope, pipelines, substitutions, handlers, streams, and exit status.

**Runner construction and reset.** When `interp.New` receives `Env`, `Dir`, `Params`, `StdIO`, and handler options, the resulting `Runner` must use those values for each run. When `Reset` is called, execution-local variables, functions, directory changes, and exit state must reset while constructor options remain. If an option is invalid, then `New` must return an error and no runner.

**Execution and scope.** When `Runner.Run` executes a syntax node, it must apply assignments, functions, conditionals, loops, pipelines, redirections, substitutions, builtins, and exit status according to the selected syntax. Function-local state must not overwrite caller scope after return except through documented global assignment. A subshell or pipeline branch must isolate environment and directory changes from its parent while preserving output and exit status.

**Controlled effects.** When execution opens a path, lists a directory, checks file state, or dispatches a command, it must call the supplied `OpenHandler`, `ReadDirHandler2`, `StatHandler`, or `ExecHandler`. If a handler rejects an effect, returns an error, or the context is canceled, then `Run` must return that error and stop later commands in the affected control path.

**Exit status.** When a program completes normally, `Run` must return nil for status zero and an error recognized by `IsExitStatus` for nonzero status. `NewExitStatus` must construct the same public status form. Where shell control flow consumes a status, boolean lists, conditionals, and pipelines must use that status without converting it into an unrelated infrastructure error.

## Domain 4: Shell Plans, Effect Journals, and Receipts

This domain defines the public `mvdan.cc/sh/v3/receipt` package. It binds syntax, formatting, expansion, execution, and controlled effects into a single independently verifiable generation instead of exposing a bag of unrelated snapshots.

**Plans and selection.** `receipt.NewShellPlan` must create an immutable empty plan. `ShellPlan.SelectSource` must return a new plan containing one stable logical source name, source bytes, and language variant; it must reject an empty name or an invalid variant without changing the prior plan. `IncludeSyntax`, `IncludeFormatted`, `IncludeExpansion`, and `IncludeExecution` must return new plans and must retain every earlier selection and option. A plan that requests expansion or execution without a selected source is invalid.

**Facts and capture.** `receipt.Capture` must produce one `ShellReceipt` from the requested plan projections. `SyntaxFact` identifies the selected variant and structural source extent; `FormatFact` contains stable formatted bytes; `ExpansionFact` contains ordered fields and the environment generation used to derive them; `ExecutionFact` contains stdout, stderr, exit status, final directory, and ordered effects. `EffectFact` records sequence, operation, logical target, and outcome. Capture must either return a complete coherent generation or an error and no receipt. It must not publish syntax from one source with formatting, expansion, or execution from another.

**Journal ownership.** `receipt.NewEffectJournal` must return an empty journal. `EffectJournal.Record` must append one effect with a strictly increasing sequence number and must make caller input ownership unobservable. `EffectJournal.Entries` must return an ordered caller-owned snapshot; changing the returned slice or its byte fields must not change the journal or a previously captured receipt.

**Validation, identity, and change.** `ShellReceipt.Validate` must reject a missing selected source, requested-but-absent projection, duplicate or decreasing effect sequence, expansion from a different environment generation, and execution facts that contradict their effect journal. `Digest` and `Equivalent` must cover language variant, structural syntax, stable formatting, ordered expansion fields, stdout, stderr, exit status, final logical directory, and ordered semantic effects. They must ignore wall-clock timing and caller-specific temporary path prefixes. `receipt.Diff` must return a `ChangeReceipt` whose changes are deterministically ordered by projection and logical identity. Equivalent receipts must produce no changes; a dialect, order, field, effect, output, status, or logical-directory change must remain observable.

# Contract

## State Model

Source moves through **unread**, **parsed**, **walked**, **printed**, and **reparsed** states. Expansion moves a syntax word and environment snapshot to fields or an error. A runner moves through **configured**, **running**, **completed**, **exited nonzero**, **canceled**, and **reset** states. Subshells and pipeline branches derive isolated execution states from a parent runner.

Public projections are syntax nodes and positions, printed source, expanded fields, environment variables, filesystem-handler calls, command-handler calls, standard output, standard error, current directory, function visibility, and exit status. Each completed run must present one coherent effect history.

## Error Semantics

| Condition | Required result |
|---|---|
| Invalid or incomplete source | Parsing must return `ParseError` or `LangError`, with `IsIncomplete` identifying unfinished input. |
| Printer writer failure | `Printer.Print` must return the writer error. |
| Required unset parameter | Expansion must return `UnsetParameterError`. |
| Missing command-substitution callback | Expansion must return `UnexpectedCommandError`. |
| Invalid shell pattern | `pattern.Regexp` must return `SyntaxError` or `NegExtGlobError`. |
| Rejected filesystem or command effect | `Runner.Run` must return the handler error. |
| Canceled execution | `Runner.Run` must return the context error and stop later effects. |
| Nonzero shell completion | `Runner.Run` must return an error recognized by `IsExitStatus`. |

## Cross-View Invariants

1. Parsed positions, walked nodes, and printed source must describe the same statement, word, and function relationships.
2. Printed-and-reparsed syntax and original syntax must produce the same expansion and interpreter effects under identical options.
3. Parser language variants and printer language behavior must agree on accepted constructs and their rendering.
4. Expansion environment reads and interpreter variable reads must agree for the same environment generation.
5. Expanded command words and command-handler arguments must agree after quoting, splitting, globbing, and substitution.
6. Subshell, pipeline, and function-scope isolation must agree across environment, directory, filesystem effects, output, and exit status.
7. API execution through `Runner.Run` and command execution through `gosh` must expose equivalent stdout, stderr, effects, and status.
8. API printing through `Printer.Print` and command formatting through `shfmt` must preserve identical syntax semantics and stable formatting.
9. A `receipt.ShellReceipt` must describe the same selected source, language variant, formatted program, expansion environment, execution output, status, directory, and effects as the native views from which it was captured.
10. Receipt digest, equivalence, and change reporting must agree across fresh captures: normalization removes only timing and temporary-path prefixes, never dialect, ordering, fields, effects, output, status, or logical directory.

# Reference

## Public Interface

### Import Surface

- `mvdan.cc/sh/v3/syntax`: `Node`, `File`, `Stmt`, `Command`, `Assign`, `Redirect`, `CallExpr`, `FuncDecl`, `Word`, `WordPart`, `Pos`, `Parser`, `NewParser`, `ParserOption`, `KeepComments`, `Variant`, `StopAt`, `RecoverErrors`, `LangVariant`, `LangBash`, `LangPOSIX`, `LangMirBSDKorn`, `ParseError`, `LangError`, `IsIncomplete`, `Walk`, `Printer`, `NewPrinter`, `PrinterOption`, `Indent`, `BinaryNextLine`, `SwitchCaseIndent`, `SpaceRedirects`, `Minify`, `FunctionNextLine`, `Quote`, `Simplify`
- `mvdan.cc/sh/v3/expand`: `Environ`, `WriteEnviron`, `Variable`, `ValueKind`, `Config`, `ListEnviron`, `FuncEnviron`, `Fields`, `Literal`, `Document`, `Pattern`, `Arithm`, `Braces`, `UnsetParameterError`, `UnexpectedCommandError`
- `mvdan.cc/sh/v3/pattern`: `Mode`, `Regexp`, `HasMeta`, `QuoteMeta`, `SyntaxError`, `NegExtGlobError`
- `mvdan.cc/sh/v3/interp`: `Runner`, `RunnerOption`, `New`, `Env`, `Dir`, `Params`, `StdIO`, `CallHandler`, `ExecHandler`, `OpenHandler`, `ReadDirHandler2`, `StatHandler`, `HandlerCtx`, `HandlerContext`, `ExitStatus`, `NewExitStatus`, `IsExitStatus`, `DefaultExecHandler`, `DefaultOpenHandler`, `DefaultReadDirHandler2`, `DefaultStatHandler`
- `mvdan.cc/sh/v3/shell`: `Expand`, `Fields`
- `mvdan.cc/sh/v3/receipt`: `ShellPlan`, `NewShellPlan`, `SyntaxFact`, `FormatFact`, `ExpansionFact`, `ExecutionFact`, `EffectFact`, `EffectJournal`, `NewEffectJournal`, `ShellReceipt`, `Capture`, `ChangeReceipt`, `Diff`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `syntax.Node`, `File`, `Stmt`, `Command`, `Assign`, `Redirect`, `CallExpr`, `FuncDecl`, `Word`, `WordPart` | interfaces and types | Represent the public syntax tree. |
| `syntax.Pos` | type | Expose source offset, line, and column. |
| `syntax.Parser`, `NewParser`, `ParserOption` | type, function, and option type | Parse shell-language source. |
| `syntax.KeepComments`, `Variant`, `StopAt`, `RecoverErrors` | functions | Configure parser behavior. |
| `syntax.LangVariant`, `LangBash`, `LangPOSIX`, `LangMirBSDKorn` | type and constants | Select a shell-language grammar. |
| `syntax.ParseError`, `LangError`, `IsIncomplete` | error types and function | Describe source and language failures. |
| `syntax.Walk`, `Simplify`, `Quote` | functions | Traverse or normalize syntax values. |
| `syntax.Printer`, `NewPrinter`, `PrinterOption` | type, function, and option type | Print syntax nodes. |
| `syntax.Indent`, `BinaryNextLine`, `SwitchCaseIndent`, `SpaceRedirects`, `Minify`, `FunctionNextLine` | functions | Configure formatting. |
| `expand.Environ`, `WriteEnviron`, `Variable`, `ValueKind`, `Config` | interfaces and types | Represent expansion state. |
| `expand.ListEnviron`, `FuncEnviron` | functions | Create environment projections. |
| `expand.Fields`, `Literal`, `Document`, `Pattern`, `Arithm`, `Braces` | functions | Expand syntax values. |
| `expand.UnsetParameterError`, `UnexpectedCommandError` | error types | Identify required expansion failures. |
| `pattern.Mode`, `Regexp`, `HasMeta`, `QuoteMeta` | type and functions | Convert and inspect shell patterns. |
| `pattern.SyntaxError`, `NegExtGlobError` | error types | Identify invalid pattern forms. |
| `interp.Runner`, `RunnerOption`, `New` | type, option type, and function | Configure and run syntax nodes. |
| `interp.Env`, `Dir`, `Params`, `StdIO` | functions | Configure runner state and streams. |
| `interp.CallHandler`, `ExecHandler`, `OpenHandler`, `ReadDirHandler2`, `StatHandler` | functions | Install effect handlers. |
| `interp.HandlerCtx`, `HandlerContext` | function and type | Expose the current handler invocation. |
| `interp.ExitStatus`, `NewExitStatus`, `IsExitStatus` | type and functions | Represent shell completion status. |
| `interp.DefaultExecHandler`, `DefaultOpenHandler`, `DefaultReadDirHandler2`, `DefaultStatHandler` | functions | Provide documented host-backed handlers. |
| `shell.Expand`, `Fields` | functions | Expand source strings with a simple environment callback. |
| `receipt.ShellPlan`, `receipt.NewShellPlan` | type and function | Build an immutable multi-view shell capture plan. |
| `receipt.ShellPlan.SelectSource`, `receipt.ShellPlan.IncludeSyntax`, `receipt.ShellPlan.IncludeFormatted`, `receipt.ShellPlan.IncludeExpansion`, `receipt.ShellPlan.IncludeExecution` | methods | Select a logical source and enable receipt projections without mutating earlier plans. |
| `receipt.SyntaxFact`, `receipt.FormatFact`, `receipt.ExpansionFact`, `receipt.ExecutionFact`, `receipt.EffectFact` | types | Represent coherent syntax, formatting, expansion, execution, and effect facts. |
| `receipt.EffectJournal`, `receipt.NewEffectJournal` | type and function | Record ordered caller-owned effect observations. |
| `receipt.EffectJournal.Record`, `receipt.EffectJournal.Entries` | methods | Append an effect and return an isolated ordered snapshot. |
| `receipt.ShellReceipt`, `receipt.Capture` | type and function | Publish one complete shell observation generation. |
| `receipt.ShellReceipt.Validate`, `receipt.ShellReceipt.Digest`, `receipt.ShellReceipt.Equivalent` | methods | Validate, identify, and compare receipt generations. |
| `receipt.ChangeReceipt`, `receipt.Diff` | type and function | Report deterministic semantic changes between generations. |

| `syntax.Parser.Parse`, `Stmts`, `Interactive`, `Words`, `Document`, `Arithmetic`, `Incomplete` | methods | Parse complete or specialized shell-language inputs. |
| `syntax.Printer.Print` | method | Write a syntax node with configured formatting. |
| `syntax.Node.Pos`, `End` | methods | Expose the source extent of a syntax node. |
| `syntax.Pos.Offset`, `Line`, `Col`, `IsValid` | methods | Expose source coordinates. |
| `expand.Environ.Get`, `Each` | methods | Read and enumerate environment variables. |
| `expand.WriteEnviron.Set` | method | Publish a variable change under environment rules. |
| `interp.Runner.Run`, `Reset`, `Subshell`, `Exited` | methods | Execute, reset, derive, and inspect runner lifecycle. |
| `interp.HandlerContext.Builtin` | method | Dispatch a documented builtin under the active handler context. |

### CLI Entry Points

| Command | Role | Success | Failure |
|---|---|---|---|
| `shfmt` | Parse and format shell-language files or standard input. | Exit 0 with valid formatted output or completed writes. | Exit nonzero on source, file, or writer failure. |
| `gosh` | Parse and interpret shell-language input. | Exit with the completed shell status. | Exit nonzero on parse, effect, context, or shell-status failure. |

# Meta

## Appendix A: Environment

The working environment runs Go 1.25 on Linux without network access. Programs execute in caller-created temporary directories with explicit environments, streams, and effect handlers. No host shell or unrestricted external command path is available.

## Appendix B: Assessment Notes

Conformance is assessed across language variants, syntax locations, parse/print stability, printer options, environment forms, quoting, field expansion, patterns, arithmetic, functions, pipelines, substitutions, redirections, sandboxed filesystem effects, cancellation, reset, exit status, and CLI/API parity. Exact temporary paths, process scheduling, and undocumented tree fields have no contractual meaning.
