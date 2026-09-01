# templ Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in interface design, parameter naming, behavioral edge cases, and error semantics.
> Implementations derived from memory of external codebases will fail the evaluation.

# Context

## Product Overview

`templ` is a Go template compiler and rendering library that turns component source into formatted Go code and context-safe HTML. Its public workflow joins parsing, diagnostics, deterministic generation, Go compilation, component composition, attribute handling, and writer-based rendering.

The source language embeds Go expressions in HTML-shaped components. Generated functions return `templ.Component` values, so generated and hand-written components share the same rendering, context, and error contracts.

## Non-Goals

- This specification does not require language-server features, editor integration, browser automation, or JavaScript package tooling.
- This specification does not define byte identity for semantically equivalent source formatting.
- This specification does not require undocumented parser nodes, generator helpers, or process-global state.

# Orientation

## Representative Workflows

### Workflow 1: Format, generate, compile, and render

1. Place component source in a temporary Go module and parse it with `parser.Parse`.
2. Diagnose the resulting `parser.TemplateFile`, then format the source with `templ fmt`.
3. Generate Go source with `generator.Generate` or `templ generate`, then compile the module.
4. Invoke the generated component and render it to an `io.Writer` with a caller-supplied context.
5. Reparse the formatted source and regenerate it to confirm stable semantics and stable generated file ownership.

### Workflow 2: Compose dynamic content safely

1. Construct a component that combines nested children, dynamic text, ordered attributes, URL values, script data, and style values.
2. Supply children with `WithChildren`, attributes with `Attributes` or `OrderedAttributes`, and trusted escape hatches only through their explicit safe types.
3. Render the component directly and through `Handler`.
4. Cancel the context or return a writer error during a later render and observe the returned error without a successful completion result.
5. Capture parsing, generation, direct rendering, and HTTP rendering into one `receipt.RenderReceipt`, then compare it with an equivalent source generation.

# Behavior

## Domain 1: Source Parsing, Diagnostics, and Formatting

This domain defines how component source becomes a stable syntax projection before code generation.

**Parsing and source locations.** When `Parse` reads a file name, the parser must read that file and return one `TemplateFile` whose package declaration, component declarations, Go expressions, elements, attributes, and ranges preserve source order. When `ParseString` receives source text, the parser must apply the same grammar without file acquisition. If source is malformed or uses the legacy format, then parsing must return a descriptive error, including `ErrLegacyFileFormat` where that sentinel applies, and must not return a publishable partial file.

**Diagnostics.** When `Diagnose` receives a parsed file, it must return diagnostics tied to source ranges for invalid component constructs. If the file is structurally invalid, then diagnosis must return an error and must not invent repaired nodes.

**Formatting.** When `templ fmt` receives valid source, the command must preserve component meaning while normalizing whitespace, Go-expression layout, element indentation, and attribute layout. When formatted output is formatted again, the command must return identical bytes. If input is invalid, then the command must exit nonzero, report a source location, and leave any destination file unchanged.

## Domain 2: Code Generation and Compilation

This domain defines the boundary from a parsed component file to Go source that the standard compiler accepts.

**Generation ownership.** When `generator.Generate` receives a `TemplateFile` and writer, it must emit Go declarations in the source package, preserve component parameter order, and return `GeneratorOutput` metadata describing generated Go and text artifacts. Where `WithVersion`, `WithTimestamp`, `WithFileName`, or `WithSkipCodeGeneratedComment` is present, generation must apply that option without changing component behavior.

**Imports and determinism.** When component expressions require imports, generation must emit a valid, deduplicated import set. When identical semantic input and identical generation options are supplied, generated Go and artifact ownership must be stable. If generation encounters an invalid expression or writer failure, then it must return the error and must not report a successful artifact set.

**Compilation boundary.** When generated code is placed in its declared module and package, the Go 1.25 compiler must accept it together with the runtime import. Generated functions must return `Component` values whose `Render` method obeys Domain 3. If compilation rejects generated code, then the generation workflow must be treated as failed rather than as a renderable state.

## Domain 3: Context-Safe Rendering and Composition

This domain defines the observable HTML, context propagation, attribute order, and failure behavior of components.

**Components and context.** When a `Component` renders, it must write to the supplied writer in component order and return the first render or writer error. When the supplied context is canceled, nested generated and hand-written components must stop at the next context-aware boundary and return the cancellation error. Where children or a nonce are present in the context, `GetChildren` and `GetNonce` must return the values installed by `WithChildren` and `WithNonce`; `ClearChildren` must prevent inherited children from reaching deeper composition.

**Escaping and trusted values.** When dynamic text is rendered, it must be HTML escaped. When a dynamic URL, script value, CSS property, or attribute is rendered, it must use the policy for that syntactic context. `SafeURL`, `SafeCSS`, `SafeCSSProperty`, `JSExpression`, and `Raw` must bypass only the protection named by their public contract. If an unsafe URL fails sanitization, then `URL` must return `FailedSanitizationURL`.

**Attributes and composition.** When `Attributes` is rendered, keys must be emitted in deterministic key order; when `OrderedAttributes` is rendered, entries must retain caller order. Boolean attributes must appear only for enabled values. `Join` must render components in argument order and stop at the first error. `JSONScript` and `JSONString` must encode data as JSON suitable for their documented HTML contexts and must return an error when JSON encoding fails.

**HTTP projection.** When `Handler` serves a component, it must apply configured status, content type, error handler, streaming, and fragment selection. Without streaming, a render error must not publish an apparently complete response body. With streaming enabled, already-written bytes remain observable and the error handler must receive the render error.

## Domain 4: Render Receipts and Projection Reconciliation

This domain defines a stable public observation layer spanning component source, generated artifacts, writer output, and HTTP behavior.

**Capture plans.** `receipt.NewRenderPlan` must return an empty caller-owned plan. `RenderPlan.SelectSource` must associate a stable name with parsed source, while `IncludeGenerated`, `IncludeDirectRender`, and `IncludeHTTPRender` must select complete projections. Repeating a name must replace its value without changing its original position. Empty names, nil inputs, or conflicting selections must return an error without changing the preceding plan.

**Render capture.** `receipt.Capture` must execute one plan and return a complete `RenderReceipt`. `SourceFact` must preserve component declarations, ranges, expressions, elements, and contextual attribute ownership. `GeneratedFact` must preserve exported declarations, imports, source-map ownership, and generated artifact identity without requiring byte-identical formatting. `RenderFact` and `HTTPFact` must preserve committed bytes, status, headers, fragments, errors, and streaming disposition from fresh observations. A failed selected projection must return an error and no partial receipt.

**Writer journal and stability.** `receipt.NewWriterJournal` must create an empty journal. `Record` must append one caller-owned write or failure fact with a strictly increasing sequence, and `Entries` must return an independent snapshot. `RenderReceipt.Validate` must reject contradictions among source, generated, direct, HTTP, and journal facts. `Digest` must ignore temporary paths, elapsed time, and harmless formatting while preserving semantic order, escaping, and failure boundaries. `Equivalent` and `receipt.Diff` must compare normalized generations without changing either input.

# Contract

## State Model

A source unit moves through **unread**, **parsed**, **diagnosed**, **formatted**, **generated**, **compiled**, and **rendered** states. Parsing or formatting failure retains the preceding valid source. Generation failure produces no successful artifact receipt. Compilation failure produces no callable component. A component render is an invocation state rather than persistent library state: context values and once-handles belong to that invocation.

Public projections are the syntax tree and ranges, formatted source, generated artifact metadata, compiled component signature, rendered writer bytes, HTTP response, and returned error. Each successful transition must describe one coherent source generation.

## Error Semantics

| Condition | Required result |
|---|---|
| Missing source file | `Parse` must return the file acquisition error. |
| Legacy or malformed component syntax | Parsing must return the applicable sentinel or descriptive syntax error and no publishable file. |
| Invalid component construct | `Diagnose` or generation must return an error tied to source position. |
| Generated-output writer failure | Generation must return the writer error and no successful artifact receipt. |
| Render writer failure | `Component.Render` must return the first writer error. |
| Canceled render context | Rendering must return the context cancellation error at the next context-aware boundary. |
| JSON encoding failure | `JSONString` or `JSONScriptElement.Render` must return the encoding error. |
| Unsafe dynamic URL | `URL` must return `FailedSanitizationURL`. |

## Cross-View Invariants

1. The parsed syntax projection and formatted source must preserve the same component declarations, parameter order, Go expressions, and element relationships.
2. The formatted source and generated Go projection must describe the same component call graph and attribute contexts.
3. Generated function signatures and runtime component invocation must agree on parameter order and package ownership.
4. Direct rendering and HTTP rendering must apply identical escaping, child propagation, attribute ordering, and component order before HTTP-specific status handling.
5. URL, script, style, text, and attribute projections must apply the protection owned by their syntactic context.
6. A generation or compilation failure must leave no artifact that reports itself as successfully renderable.
7. Context cancellation and writer failure must propagate across generated calls, nested components, joined components, and HTTP handling.
8. Repeated formatting and repeated generation with identical options must preserve stable source and artifact projections.
9. A render receipt must reconcile source, generated, direct writer, and HTTP projections under one component generation.
10. Equivalent component generations must produce equal receipt digests across temporary paths and independent render invocations.

# Reference

## Public Interface

### Import Surface

- `github.com/a-h/templ`: `Component`, `ComponentFunc`, `ComponentHandler`, `Handler`, `WithStatus`, `WithContentType`, `WithErrorHandler`, `WithStreaming`, `WithFragments`, `Join`, `WithChildren`, `GetChildren`, `ClearChildren`, `WithNonce`, `GetNonce`, `EscapeString`, `Raw`, `URL`, `SafeURL`, `FailedSanitizationURL`, `SafeCSS`, `SafeCSSProperty`, `SanitizeCSS`, `Attributes`, `OrderedAttributes`, `RenderAttributes`, `KV`, `ComponentScript`, `JSExpression`, `JSFuncCall`, `JSUnsafeFuncCall`, `SafeScript`, `SafeScriptInline`, `JSONScript`, `JSONScriptElement`, `JSONString`, `Error`
- `github.com/a-h/templ/parser/v2`: `Parse`, `ParseString`, `Diagnose`, `TemplateFile`, `Diagnostic`, `Position`, `Range`, `Node`, `Element`, `Attribute`, `ErrLegacyFileFormat`, `ErrTemplateNotFound`
- `github.com/a-h/templ/generator`: `Generate`, `GenerateOpt`, `WithVersion`, `WithTimestamp`, `WithFileName`, `WithSkipCodeGeneratedComment`, `GeneratorOutput`, `HasGoChanged`, `HasTextChanged`
- `github.com/a-h/templ/receipt`: `RenderPlan`, `NewRenderPlan`, `SourceFact`, `GeneratedFact`, `RenderFact`, `HTTPFact`, `WriterFact`, `WriterJournal`, `NewWriterJournal`, `RenderReceipt`, `ChangeReceipt`, `Capture`, `Diff`

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `templ.Component`, `ComponentFunc` | interface and function type | Render content to a writer with a context. |
| `templ.Handler`, `ComponentHandler` | function and type | Project component rendering through HTTP. |
| `templ.WithStatus`, `WithContentType`, `WithErrorHandler`, `WithStreaming`, `WithFragments` | functions | Configure the HTTP projection. |
| `templ.Join` | function | Compose components in argument order. |
| `templ.WithChildren`, `GetChildren`, `ClearChildren` | functions | Manage nested component content in a context. |
| `templ.WithNonce`, `GetNonce` | functions | Manage a rendering nonce in a context. |
| `templ.EscapeString`, `Raw` | functions | Escape dynamic text or mark trusted HTML. |
| `templ.URL`, `SafeURL`, `FailedSanitizationURL` | function, type, and constant | Sanitize URL values and represent explicit trust. |
| `templ.SafeCSS`, `SafeCSSProperty`, `SanitizeCSS` | types and function | Represent or sanitize dynamic CSS. |
| `templ.Attributes`, `OrderedAttributes`, `RenderAttributes`, `KV` | types and functions | Represent and render attribute collections. |
| `templ.ComponentScript`, `JSExpression`, `JSFuncCall`, `JSUnsafeFuncCall`, `SafeScript`, `SafeScriptInline` | types and functions | Represent dynamic script calls and explicit trust. |
| `templ.JSONScript`, `JSONScriptElement`, `JSONString` | functions and type | Encode values for JSON script or attribute contexts. |
| `templ.Error` | error type | Wrap a render error with component location context. |
| `parser.Parse`, `ParseString`, `Diagnose` | functions | Create and validate a source projection. |
| `parser.TemplateFile`, `Diagnostic`, `Position`, `Range`, `Node`, `Element`, `Attribute` | types | Expose parsed declarations, diagnostics, and source locations. |
| `parser.ErrLegacyFileFormat`, `ErrTemplateNotFound` | error values | Identify documented parse failures. |
| `generator.Generate`, `GenerateOpt` | function and option type | Generate Go artifacts from a parsed file. |
| `generator.WithVersion`, `WithTimestamp`, `WithFileName`, `WithSkipCodeGeneratedComment` | functions | Configure generated artifact metadata. |
| `generator.GeneratorOutput`, `HasGoChanged`, `HasTextChanged` | type and functions | Report and compare generated artifacts. |

| `templ.Component.Render` | method | Render one component to a writer with a context. |
| `templ.ComponentHandler.ServeHTTP` | method | Serve the configured component as an HTTP response. |
| `templ.Attributes.Items`, `templ.OrderedAttributes.Items` | methods | Return attribute entries under map-sorted or caller order. |
| `templ.JSONScriptElement.Render`, `WithType`, `WithNonceFromString`, `WithNonceFrom` | methods | Render and configure a JSON script element. |
| `parser.TemplateFile.Write`, `Visit` | methods | Write or traverse a parsed component file. |
| `parser.SourceMap.TargetPositionFromSource`, `SourcePositionFromTarget` | methods | Translate positions between component and generated source. |
| `generator.GeneratorOutput.Options`, `SourceMap`, `Literals` | fields | Publish generation metadata, position mapping, and text artifacts. |
| `receipt.RenderPlan`, `receipt.NewRenderPlan` | type and function | Select named source and complete generation and rendering projections. |
| `receipt.RenderPlan.SelectSource`, `receipt.RenderPlan.IncludeGenerated`, `receipt.RenderPlan.IncludeDirectRender`, `receipt.RenderPlan.IncludeHTTPRender` | methods | Build a stable caller-owned render observation plan. |
| `receipt.SourceFact`, `receipt.GeneratedFact`, `receipt.RenderFact`, `receipt.HTTPFact`, `receipt.WriterFact` | records | Normalize syntax, generation, writer, and HTTP observations. |
| `receipt.WriterJournal`, `receipt.NewWriterJournal` | type and function | Own ordered writer bytes and failure boundaries. |
| `receipt.WriterJournal.Record`, `receipt.WriterJournal.Entries` | methods | Append write outcomes and return independent ordered snapshots. |
| `receipt.RenderReceipt`, `receipt.Capture` | type and function | Capture one complete component generation across selected projections. |
| `receipt.RenderReceipt.Validate`, `receipt.RenderReceipt.Digest`, `receipt.RenderReceipt.Equivalent` | methods | Reconcile and compare normalized render generations. |
| `receipt.ChangeReceipt`, `receipt.Diff` | type and function | Describe semantic additions removals and changes between receipts. |

### CLI Entry Points

| Command | Role | Success | Failure |
|---|---|---|---|
| `templ generate` | Generate Go files from component source. | Exit 0 after every selected source is generated. | Exit nonzero with a source or generation diagnostic. |
| `templ fmt` | Format component source or standard input. | Exit 0 after valid formatted output is produced. | Exit nonzero with a source diagnostic and no successful replacement. |

# Meta

## Appendix A: Environment

The working environment runs Go 1.25 on Linux without network access. The module cache and repository-provided dependency snapshot are available locally. Source files, generated files, and compiled artifacts must remain under caller-created temporary directories. The standard Go compiler is available; editor servers, browsers, Node.js packages, and remote services are absent.

## Appendix B: Assessment Notes

Conformance is assessed across source grammar families, Go-expression boundaries, contextual escaping, attribute forms, formatting stability, generated import ownership, compiler acceptance, component composition, cancellation, writer failures, and CLI/API parity. Exact temporary paths, scheduling latency, and undocumented implementation structure have no contractual meaning.

