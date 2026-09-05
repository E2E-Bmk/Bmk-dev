# miette Diagnostic Reporting Specification

> Specification Authority: This document is the complete contract for the crate. Implementations are evaluated against the behavior described here, not against any external package.

## Context

### Product Overview

`miette` is a Rust diagnostic reporting library for turning ordinary errors into structured diagnostics with codes, severity, help text, source snippets, related diagnostics, and configurable report renderers.

The crate exposes a public protocol centered on `Diagnostic`, `SourceCode`, `SourceSpan`, `LabeledSpan`, `Report`, derive support, and report handlers. A program uses these pieces to attach structured context to errors, wrap lower-level failures while preserving downcasts, and print the same diagnostic graph through debug, JSON, narrated, or graphical views.

### Non-Goals

- This specification does not require byte-for-byte reproduction of decorative terminal art, ANSI escape sequences, or line wrapping beyond the semantic placement rules below.
- This specification does not require support for private modules, hidden macro helper modules, internal pointer machinery, or compile-fail tests for implementation internals.
- This specification does not define a command-line interface.
- This specification does not require network access, live terminal probing, operating-system specific backtrace formatting, or exact panic-hook text.

## Orientation

### Representative Workflows

#### Derive a Rich Domain Error

A library author defines an error type that implements `Debug`, `Display`, `Error`, and derives `Diagnostic`. Attributes on the type and fields provide a code, severity, help text, URL, source code storage, related diagnostics, and one or more labels. Calling the generated `Diagnostic` methods returns owned display values or iterators that reflect those attributes without consuming the error value.

#### Wrap and Report an Application Failure

An application converts an ordinary `Result<T, E>` into `miette::Result<T>` with `IntoDiagnostic`, adds human context with `WrapErr`, and returns the result from `main`. The resulting `Report` preserves the original error chain, exposes downcasts to both the original error and added context values, and delegates display formatting to the report handler captured at report construction.

#### Render One Diagnostic Through Multiple Views

A caller configures a handler through `MietteHandlerOpts` or constructs a concrete handler directly. The same diagnostic graph is then rendered as debug text, JSON, narrated text, or graphical text. Each view reports the same message, code, severity, help text, URL, related diagnostics, and source-label relationships while using its own representation.

## Behavior

### Diagnostic Protocol

#### Diagnostic Metadata

When a type implements `Diagnostic`, it also implements `std::error::Error`.

When `code` is not overridden, it returns no code.

When `severity` is not overridden, renderers and structured projections treat the diagnostic as `Severity::Advice`.

When `help` is not overridden, it returns no help text.

When `url` is not overridden, it returns no URL.

When `source_code` is not overridden, it returns no source code object.

When `labels` is not overridden, it returns no labels.

When `related` is not overridden, it returns no related diagnostics.

When `diagnostic_source` is not overridden, the diagnostic chain uses the ordinary `std::error::Error::source` chain.

`Severity` has exactly the variants `Advice`, `Warning`, and `Error`. Ordering and equality treat those variants as distinct values. Its default value is `Advice`.

Boxed diagnostic trait objects forward the ordinary error `source` call to the boxed value.

String and string-slice conversions into boxed diagnostic trait objects create anonymous diagnostics whose display and debug text are the string content.

`MietteError` has exactly the variants `IoError` carrying `std::io::Error` and `OutOfBounds`. `IoError` displays the wrapped I/O error, delegates `source` to the wrapped I/O error, reports code `miette::io_error`, and has no help text. `OutOfBounds` displays a span-bounds message, exposes no source, reports code `miette::span_out_of_bounds`, and reports help text telling the caller to check spans for off-by-one errors. Both variants expose documentation URLs for their own variant pages. `MietteError` converts from `std::io::Error` by producing the `IoError` variant.

#### Source Coordinates

`ByteOffset` is an alias for `usize`.

`SourceOffset` stores an absolute byte offset from the beginning of a source. It converts from `usize`, exposes its raw offset, and derives copy, clone, debug, equality, ordering, and hashing.

When `SourceOffset::from_location` receives a string and a one-based line and column, it walks Unicode scalar values and returns the byte offset at that location. Newline advances to the next line and resets the column. If the requested location is past the end, it returns the final byte offset of the source.

`SourceSpan` stores a starting `SourceOffset` and a byte length. It derives copy, clone, debug, equality, ordering, and hashing. It constructs from an offset plus length, from a `(usize, usize)` pair, from a `(SourceOffset, usize)` pair, from a byte range, from an inclusive byte range, from a `SourceOffset`, and from a `usize`. A single offset creates an empty span at that byte. A range creates a span with the range start and byte length. An inclusive range includes both endpoints and panics only when the represented length overflows `usize`. `SourceSpan::offset` returns the starting byte offset as `usize`. `SourceSpan::len` returns the byte length as `usize`. `SourceSpan::is_empty` returns whether the byte length is zero.

`LabeledSpan` stores an optional label string, a `SourceSpan`, and a primary flag. `new`, `new_with_span`, and `new_primary_with_span` construct explicit labels. `at` constructs a non-primary label from a span-like value and text. `at_offset` constructs an empty non-primary label at a byte offset. `underline` constructs a non-primary label with no text. `set_label` replaces the optional label text. `label` returns the optional label text by reference. `inner` returns the contained `SourceSpan` by reference. `offset` and `len` return the span offset and length as `usize`. `is_empty` returns whether the contained span has zero length. `primary` returns the primary flag.

#### Source Reading

`SourceCode` is object-safe, `Send`, and `Sync`. Its required operation reads a span plus a requested number of context lines before and after the span and returns boxed `SpanContents` or `MietteError`.

`SpanContents` exposes the borrowed bytes, covered span, optional name, zero-based start line, zero-based start column, line count, and optional language name.

`MietteSpanContents` is the basic span-contents implementation. `new` accepts borrowed bytes, a `SourceSpan`, a zero-based start line, a zero-based start column, and a line count, and creates unnamed contents. `new_named` accepts a `String` name before the same bytes, `SourceSpan`, line, column, and line-count values, and creates named contents. `with_language` returns contents with a language tag. Its trait methods return the exact values stored at construction.

Strings, string slices, byte slices, byte vectors, `Arc<T>` where `T: SourceCode`, and `Cow<T>` over a `SourceCode` target implement `SourceCode`. Text implementations operate on UTF-8 bytes for spans and compute line and column positions by scanning bytes. CRLF counts as one line break. If the requested span extends beyond the available bytes, reading returns `MietteError::OutOfBounds`.

When context lines are requested, source reading extends the returned byte slice to full surrounding lines. The returned span describes the full byte slice actually returned, while line and column identify where that returned slice begins.

`NamedSource<S>` wraps any `S: SourceCode + 'static`, stores a display name, and optionally stores a language. It exposes `new`, `name`, `inner`, and `with_language`. Its `SourceCode` implementation delegates reading to the inner source, then returns `MietteSpanContents` that carries the wrapper name and language while preserving the inner data, covered span, line, column, and line count.

### Diagnostic Construction

#### Dynamic Diagnostics

`MietteDiagnostic` is a cloneable, comparable diagnostic value with public fields `message`, `code`, `severity`, `help`, `url`, and `labels`.

`MietteDiagnostic::new` stores the display message and leaves all optional fields empty.

`with_code`, `with_severity`, `with_help`, and `with_url` return updated diagnostics with the corresponding optional field set.

`with_label` replaces the label list with a one-element list. `with_labels` replaces the label list with the provided labels in iteration order. `and_label` appends one label to the existing list or creates a new list. `and_labels` appends all provided labels in iteration order.

The `Diagnostic` implementation for `MietteDiagnostic` returns display boxes for `code`, `help`, and `url`, returns its stored severity, and returns a cloned iterator over stored labels.

#### Derive Macro

With the default `derive` feature, the crate re-exports a derive macro named `Diagnostic`.

The derive macro accepts `#[diagnostic(...)]` attributes with `code`, `severity`, `help`, `url`, `transparent`, and `forward(...)` options. It also accepts field attributes `#[source_code]`, `#[label]`, `#[related]`, `#[help]`, and `#[diagnostic_source]`.

For structs, the derive macro generates one `Diagnostic` implementation for the struct type while preserving generics and where-clauses. For enums, it generates one implementation that matches on variants and uses each variant's attributes or forwarded field.

A `code` option stores a displayable diagnostic code. A `severity` option maps an identifier to the matching `Severity` variant. A `help` option stores either literal help text or a display expression from a field. A `url` option stores either a literal URL, an automatic documentation URL for the item, or a display expression from a field.

A `#[source_code]` field supplies the source object returned by `source_code`. A `#[label]` field supplies one label or a collection of labels returned by `labels`. Accepted label field values include `SourceSpan`, `LabeledSpan`, optional label values, and iterable collections of label values; a bare `SourceSpan` becomes an underline label, or a text label when the field attribute provides label text. A `#[related]` field supplies related diagnostics. A `#[diagnostic_source]` field supplies the diagnostic chain source. A `#[help]` field supplies dynamic help text.

`#[diagnostic(transparent)]` delegates all diagnostic metadata methods to the single wrapped diagnostic field. Transparent unit structs and unit variants are compile errors.

`#[diagnostic(forward(field))]` delegates diagnostic metadata methods to the named or indexed field while retaining the outer error identity. Explicit metadata attributes on the same item override forwarded values for their own methods.

Duplicate fields for source code, related diagnostics, diagnostic source, or same-purpose labels are compile errors. Unknown diagnostic options are compile errors.

### Reports and Context

#### Report Lifecycle

`Report` is a `Send` and `Sync` owning diagnostic wrapper. `Error`, `ErrReport`, `EyreContext`, and `Context` are compatibility aliases for `Report`, `Report`, `ReportHandler`, and `WrapErr` respectively. `Result<T, E = Report>` aliases `core::result::Result<T, E>`.

`Report::new` accepts a `Diagnostic + Send + Sync + 'static` value and captures the active report handler at construction.

`Report::msg` and `miette!` create anonymous diagnostics from displayable messages. `Report::new_boxed` accepts a boxed diagnostic trait object. `Report::from_err` and `IntoDiagnostic` convert ordinary error results by wrapping the source error as a diagnostic that retains the ordinary source chain.

`Report::wrap_err` consumes an existing report and returns a report whose outer display is the supplied context message and whose source remains the consumed report. `Report` dereferences to `dyn Diagnostic`, so borrowed reports are accepted wherever a diagnostic trait object is required.

`set_hook` installs a single global hook that maps diagnostics to boxed report handlers. The first successful call installs the hook. Later calls return `InstallError`. Reports created before a hook change keep their captured handler. Reports created after installation use the installed hook.

The default handler is `MietteHandler` when the `fancy-base` feature is active and `DebugReportHandler` otherwise.

`Report` implements `Display` through its handler display method and `Debug` through its handler debug method. Alternate display includes the ordinary cause chain when the handler display method uses the default behavior.

#### Wrapping and Downcasting

`WrapErr` is implemented for `Result<T, E>` where the error converts into report context and for `Option<T>`. It exposes `wrap_err`, `wrap_err_with`, `context`, and `with_context`. The lazy forms evaluate their closure only when the value is an error or `None`.

For `Option<T>`, `Some` returns `Ok(T)`. `None` returns a `Report` built from the supplied display message.

For `Result<T, E>`, `Ok` returns `Ok(T)`. `Err` returns a `Report` whose outer display is the added context and whose source is the original error or report.

Wrapping a report or diagnostic preserves downcasts to the original error type and to each added context type. `is`, `downcast`, `downcast_ref`, and `downcast_mut` traverse the stored error stack. A successful consuming `downcast` returns the requested value; an unsuccessful consuming downcast returns the original report.

`chain` iterates the ordinary error chain from outermost to root. `root_cause` returns the last ordinary source in that chain. `with_source_code` returns a report whose top-level diagnostic exposes the provided source code for label rendering.

The crate converts any `Diagnostic + Send + Sync + 'static` value into `Report`, preserving the diagnostic value as the report payload and preserving ordinary source traversal.

#### Report Macros

The `miette!` macro accepts display-format arguments and returns a `Report` built from the formatted message.

The `diagnostic!` macro accepts display-format arguments and returns a `MietteDiagnostic` built from the formatted message. Before the message arguments, it accepts named options including `code = value`, `severity = Severity::<variant>`, `help = value`, `url = value`, and `labels = value`. Named options set the matching diagnostic metadata on the returned value.

### Report Rendering

#### Handler Protocol

`ReportHandler` is `Any + Send + Sync`. Its required method is `debug`, which receives a diagnostic trait object and a formatter and renders the diagnostic for debug formatting. Its display method renders ordinary display text and, for alternate display, appends the ordinary source chain separated by colon text. Its caller-tracking method records the construction location when the platform supplies caller locations.

Trait-object `ReportHandler` values expose `is`, `downcast_ref`, and `downcast_mut` for concrete handler types.

`DebugReportHandler`, `JSONReportHandler`, `NarratableReportHandler`, `GraphicalReportHandler`, and `MietteHandler` each implement `ReportHandler`.

#### Debug and JSON Views

`DebugReportHandler::new` creates a stateless handler. Its `render_report` operation accepts a mutable `fmt::Formatter` target and a diagnostic trait object, then writes the diagnostic display text. If the diagnostic has a source chain, it writes a `Caused by` section in ordinary chain order. If the diagnostic has metadata, it writes fields for code, severity, help, URL, labels, source availability, related diagnostics, and diagnostic source in a debug-oriented representation.

`JSONReportHandler::new` creates a stateless handler. Its `render_report` operation accepts a mutable `fmt::Write` target and a diagnostic trait object, then writes one JSON object. The object always includes `message`, `severity`, `causes`, `labels`, and `related`. It includes `code`, `url`, `help`, and `filename` when those values exist or a source is available. Messages, code, help, labels, filenames, and cause strings are JSON-escaped for quotes, backslashes, tabs, carriage returns, newlines, backspace, and form feed.

When JSON renders severity, `Severity::Error` becomes `error`, `Severity::Warning` becomes `warning`, and `Severity::Advice` or an absent severity becomes `advice`.

When JSON renders causes, `diagnostic_source` takes precedence over the ordinary source chain. Each cause is represented by its display string. When neither chain exists, `causes` is an empty array.

When JSON renders labels, each label object contains its text when present and its span offset and length. The `primary` flag is not emitted in JSON labels. The filename is read from the first label's source span using zero context lines. If no filename is available, filename is an empty string.

Related diagnostics render recursively as JSON objects. A related diagnostic without its own source inherits the parent source for filename extraction and labels.

#### Narrated and Graphical Views

`NarratableReportHandler::new` creates a text handler for environments that do not use graphical source snippets. Its `render_report` operation accepts a mutable `fmt::Write` target and a diagnostic trait object. It exposes builder methods for footer, context lines, cause-chain inclusion, cause-chain exclusion, and nested related diagnostics. Rendering reports the diagnostic message, code, severity, help, URL, causes, source names, labels, and related diagnostics in readable sections.

`GraphicalReportHandler::new` creates a graphical handler using the default graphical theme. Its `render_report` operation accepts a mutable `fmt::Write` target and a diagnostic trait object. `new_themed` uses the supplied theme. Builder methods configure tab width, links, cause-chain inclusion, cause-chain exclusion, primary-span-start display, URL display, theme, width, line wrapping, word breaking, word separator, word splitter, footer, context lines, related-diagnostic nesting, syntax highlighting, and link display text.

Graphical rendering uses source snippets for labels when a source exists. It groups labels by source, honors primary labels as the lead focus for a diagnostic, renders unlabeled spans as underlines without label text, includes requested context lines, expands tabs according to the configured tab width, and renders related diagnostics according to the nested-versus-sibling configuration.

Graphical and narrated renderers use `Advice` presentation when severity is absent.

#### Handler Options and Themes

`RgbColors` has exactly the variants `Always`, `Preferred`, and `Never`; its default is `Never`.

`MietteHandlerOpts::new` creates an empty builder. Builder methods store terminal links, graphical theme, syntax highlighter, disabled syntax highlighting, width, line wrapping, word breaking, word separator, word splitter, cause-chain inclusion, cause-chain exclusion, related-error placement, color, RGB color policy, Unicode choice, forced graphical mode, forced narrated mode, footer, context line count, and tab width. `build` returns a `MietteHandler`.

When `force_narrated(true)` is set, `build` returns a `MietteHandler` backed by `NarratableReportHandler`. When graphical mode is selected, `build` returns a handler backed by `GraphicalReportHandler`. Otherwise it returns a narrated handler. Explicit options override terminal auto-detection.

`GraphicalTheme` has public fields `characters` and `styles`. `ascii`, `unicode`, `unicode_nocolor`, and `none` construct predefined themes. The default theme uses `none` when stdout or stderr is not a terminal, uses `unicode_nocolor` when `NO_COLOR` is set to a value other than `0`, and uses `unicode` otherwise.

`ThemeStyles` has public fields `error`, `warning`, `advice`, `help`, `link`, `linum`, and `highlights`. `rgb`, `ansi`, and `none` construct RGB, ANSI, and unstyled palettes.

`ThemeCharacters` has public drawing fields for horizontal bars, vertical bars, intersections, arrows, box corners, crosses, underline markers, and severity symbols. Each public drawing field is a string value, including one-character symbols and multi-character labels. `unicode`, `emoji`, and `ascii` construct predefined character sets.

## Contract

### State Model

The crate stores only two global states: the once-installed report hook and any environment-derived handler defaults read while building a handler. Report values own their diagnostic stack, optional source-code override, and captured handler.

Source objects and diagnostics are borrowed through trait objects during rendering. Rendering does not consume the diagnostic, labels, related diagnostic collection, or source object.

Builder types are immutable-by-return: each option method consumes the builder value and returns the updated value.

### Error Semantics

Span reading errors are reported as `MietteError`. Out-of-bounds spans never panic.

Inclusive range conversion for `SourceSpan` panics only for length overflow.

`SourceOffset::from_current_location` returns an I/O error if the source file at the caller location is unavailable.

Duplicate global hook installation returns `InstallError` and leaves the original hook active.

Derive macro misuse is reported as Rust compile errors at the invalid attribute or item.

### Cross-View Invariants

Diagnostic metadata returned by manual implementations, dynamic diagnostics, derive-generated implementations, reports, and context wrappers is the same metadata rendered by every handler.

An absent severity is `Advice` in all projections: `Severity::default`, JSON severity text, narrated severity text, graphical severity styling, and any handler options that select severity presentation.

Labels always refer to `SourceSpan` byte offsets and lengths. Source readers, JSON filename extraction, narrated snippets, and graphical snippets use the same span values.

Related diagnostics preserve their identity and metadata when rendered recursively. Related diagnostics without their own source reuse the nearest parent source for label projection.

`diagnostic_source` and the ordinary error source chain are distinct relationships. A renderer that displays diagnostic causes uses `diagnostic_source` first and otherwise uses the ordinary error source chain.

Wrapping with context changes the outer display message and leaves the original error available for `source`, `chain`, `root_cause`, and downcast traversal.

Reports capture their handler at construction. Later hook installation does not alter existing reports.

## Reference

### Public Interface

#### Import Surface

The crate root exports the diagnostic protocol types, report/context types, macros, handlers, themes, and derive macro described in this document. Feature-gated exports appear only when their feature is active.

Public Rust names, enum variants, trait method sets, struct fields declared public, constructors, builder methods, conversions, trait implementations, and type aliases described here are contractual. Private fields remain private even when their accessors are contractual.

#### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Diagnostic` | trait | Structured metadata extension for errors |
| `Severity` | enum | Diagnostic severity value |
| `SourceCode` | trait | Span-based source reader |
| `SpanContents` | trait | Borrowed snippet metadata |
| `MietteSpanContents` | struct | Basic span contents implementation |
| `SourceSpan` | struct | Byte span in a source |
| `SourceOffset` | struct | Byte offset in a source |
| `ByteOffset` | type alias | Raw byte offset |
| `LabeledSpan` | struct | Label attached to a source span |
| `NamedSource` | struct | Named wrapper around source code |
| `MietteError` | enum | Protocol error type |
| `MietteDiagnostic` | struct | Runtime-built diagnostic |
| `Report` | struct | Owning report wrapper |
| `Result` | type alias | Result alias using `Report` by default |
| `Error`, `ErrReport` | type alias | Compatibility names for `Report` |
| `EyreContext` | type alias | Compatibility name for `ReportHandler` |
| `Context` | type alias | Compatibility name for `WrapErr` |
| `ErrorHook` | type alias | Global report-handler factory |
| `InstallError` | struct | Duplicate hook installation error |
| `set_hook` | function | Installs the global report hook |
| `IntoDiagnostic` | trait | Converts ordinary error results |
| `WrapErr` | trait | Adds context to options and results |
| `ReportHandler` | trait | Formatting backend for reports |
| `DebugReportHandler` | struct | Debug text renderer |
| `JSONReportHandler` | struct | JSON renderer |
| `NarratableReportHandler` | struct | Narrated text renderer |
| `GraphicalReportHandler` | struct | Source-snippet text renderer |
| `MietteHandlerOpts` | struct | Handler builder |
| `MietteHandler` | struct | Auto-selected report handler |
| `RgbColors` | enum | RGB color policy |
| `GraphicalTheme` | struct | Graphical renderer theme |
| `ThemeStyles` | struct | Style palette for themes |
| `ThemeCharacters` | struct | Drawing character set for themes |
| `Highlighter` | trait | Feature-gated syntax highlighter interface |
| `HighlighterState` | trait | Feature-gated highlighting state |
| `BlankHighlighter` | struct | Feature-gated no-color highlighter |
| `BlankHighlighterState` | struct | Feature-gated no-color highlighter state |
| `SyntectHighlighter` | struct | Feature-gated syntect-backed highlighter |
| `miette!` | macro | Builds anonymous reports and diagnostics |
| `diagnostic!` | macro | Builds dynamic diagnostics |
| `bail!` | macro | Returns an error report early |
| `ensure!` | macro | Validates a condition or returns an error report |
| `Diagnostic` derive | proc macro | Generates diagnostic implementations |

#### CLI Entry Points

This crate is a pure Rust library. It exposes no executable command, subcommand, environment-variable protocol, or file-format interface beyond the library API.

## Meta

### Appendix A: Environment

The crate targets Rust 1.82 or newer and edition 2018.

The default feature set includes derive support. The `derive` feature exposes the derive macro. The `fancy-base` feature exposes graphical/narrated handler infrastructure and highlighter interfaces. The `fancy` feature additionally enables panic-hook support. The `syntect-highlighter` feature enables a syntect-backed highlighter. The `serde` feature enables serialization and deserialization for supported value types.

Handlers that inspect terminal capabilities use local process state only. A deterministic implementation accepts explicit handler options to bypass terminal auto-detection.

### Appendix B: Assessment Notes

Correct implementations preserve public Rust type shapes and trait method sets. In a statically typed Rust crate, missing variants, missing public fields, missing trait methods, or incompatible builder methods are contract failures even if an example workflow appears to run.

Exact decorative renderer output is intentionally outside the contract. Semantic content, source span relationships, chain order, related diagnostic structure, and the mutated absent-severity behavior are inside the contract.
