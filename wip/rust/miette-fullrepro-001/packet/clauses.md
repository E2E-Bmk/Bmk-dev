# Clause Map - miette-fullrepro-001 spec_v2

MIETTE-DIAG-001: When a type implements `Diagnostic`, it also implements `std::error::Error`.
MIETTE-DIAG-002: When `severity` is not overridden, renderers and structured projections treat the diagnostic as `Severity::Advice`.
MIETTE-DIAG-003: `Severity` has exactly the variants `Advice`, `Warning`, and `Error`.
MIETTE-DIAG-004: Its default value is `Advice`.
MIETTE-DIAG-005: `MietteError` has exactly the variants `IoError` carrying `std::io::Error` and `OutOfBounds`.
MIETTE-DIAG-006: `MietteError` converts from `std::io::Error` by producing the `IoError` variant.
MIETTE-SRC-001: `ByteOffset` is an alias for `usize`.
MIETTE-SRC-002: When `SourceOffset::from_location` receives a string and a one-based line and column, it walks Unicode scalar values and returns the byte offset at that location.
MIETTE-SRC-003: If the requested location is past the end, it returns the final byte offset of the source.
MIETTE-SRC-004: `SourceSpan` stores a starting `SourceOffset` and a byte length.
MIETTE-SRC-005: A single offset creates an empty span at that byte.
MIETTE-SRC-006: `LabeledSpan` stores an optional label string, a `SourceSpan`, and a primary flag.
MIETTE-SRC-007: If the requested span extends beyond the available bytes, reading returns `MietteError::OutOfBounds`.
MIETTE-SRC-008: `NamedSource<S>` wraps any `S: SourceCode + 'static`, stores a display name, and optionally stores a language.
MIETTE-SRC-009: `SourceSpan::offset` returns the starting byte offset as `usize`.
MIETTE-SRC-010: `SourceSpan::len` returns the byte length as `usize`.
MIETTE-SRC-011: `LabeledSpan::inner` returns the contained `SourceSpan` by reference.
MIETTE-SRC-012: `LabeledSpan::offset` and `LabeledSpan::len` return the span offset and length as `usize`.
MIETTE-SRC-013: `MietteSpanContents::new` accepts borrowed bytes, a `SourceSpan`, a zero-based start line, a zero-based start column, and a line count; `new_named` accepts a `String` name before those same values.
MIETTE-DYN-001: `MietteDiagnostic` is a cloneable, comparable diagnostic value with public fields `message`, `code`, `severity`, `help`, `url`, and `labels`.
MIETTE-DYN-002: `MietteDiagnostic::new` stores the display message and leaves all optional fields empty.
MIETTE-DYN-003: `with_label` replaces the label list with a one-element list.
MIETTE-DYN-004: `and_label` appends one label to the existing list or creates a new list.
MIETTE-DERIVE-001: With the default `derive` feature, the crate re-exports a derive macro named `Diagnostic`.
MIETTE-DERIVE-002: The derive macro accepts `#[diagnostic(...)]` attributes with `code`, `severity`, `help`, `url`, `transparent`, and `forward(...)` options.
MIETTE-DERIVE-003: A `#[source_code]` field supplies the source object returned by `source_code`.
MIETTE-DERIVE-004: A `#[label]` field supplies one label or a collection of labels returned by `labels`.
MIETTE-DERIVE-007: Accepted label field values include `SourceSpan`, `LabeledSpan`, optional label values, and iterable collections of label values.
MIETTE-DERIVE-005: `#[diagnostic(transparent)]` delegates all diagnostic metadata methods to the single wrapped diagnostic field.
MIETTE-DERIVE-006: Explicit metadata attributes on the same item override forwarded values for their own methods.
MIETTE-REPORT-001: `Report` is a `Send` and `Sync` owning diagnostic wrapper.
MIETTE-REPORT-002: `Report::new` accepts a `Diagnostic + Send + Sync + 'static` value and captures the active report handler at construction.
MIETTE-REPORT-006: `Report::wrap_err` consumes an existing report and returns a report whose outer display is the supplied context message and whose source remains the consumed report.
MIETTE-REPORT-007: `Report` dereferences to `dyn Diagnostic`, so borrowed reports are accepted wherever a diagnostic trait object is required.
MIETTE-REPORT-008: The crate converts any `Diagnostic + Send + Sync + 'static` value into `Report`.
MIETTE-REPORT-003: The first successful call installs the hook.
MIETTE-REPORT-004: Later calls return `InstallError`.
MIETTE-REPORT-005: Reports created before a hook change keep their captured handler.
MIETTE-WRAP-001: The lazy forms evaluate their closure only when the value is an error or `None`.
MIETTE-WRAP-002: For `Option<T>`, `Some` returns `Ok(T)`.
MIETTE-WRAP-003: `None` returns a `Report` built from the supplied display message.
MIETTE-WRAP-004: Wrapping a report or diagnostic preserves downcasts to the original error type and to each added context type.
MIETTE-WRAP-005: `chain` iterates the ordinary error chain from outermost to root.
MIETTE-MACRO-001: The `miette!` macro accepts display-format arguments and returns a `Report` built from the formatted message.
MIETTE-MACRO-002: The `diagnostic!` macro accepts display-format arguments and returns a `MietteDiagnostic` built from the formatted message.
MIETTE-MACRO-003: Before the message arguments, `diagnostic!` accepts named options including `code = value`, `severity = Severity::<variant>`, `help = value`, `url = value`, and `labels = value`.
MIETTE-RENDER-001: `ReportHandler` is `Any + Send + Sync`.
MIETTE-RENDER-003: `ReportHandler`'s required method is `debug`, which receives a diagnostic trait object and a formatter and renders the diagnostic for debug formatting.
MIETTE-RENDER-002: `DebugReportHandler`, `JSONReportHandler`, `NarratableReportHandler`, `GraphicalReportHandler`, and `MietteHandler` each implement `ReportHandler`.
MIETTE-RENDER-004: `DebugReportHandler::render_report` accepts a mutable `fmt::Formatter` target and a diagnostic trait object; `JSONReportHandler::render_report`, `NarratableReportHandler::render_report`, and `GraphicalReportHandler::render_report` accept a mutable `fmt::Write` target and a diagnostic trait object.
MIETTE-JSON-001: `JSONReportHandler::new` creates a stateless handler.
MIETTE-JSON-002: The object always includes `message`, `severity`, `causes`, `labels`, and `related`.
MIETTE-JSON-003: When JSON renders severity, `Severity::Error` becomes `error`, `Severity::Warning` becomes `warning`, and `Severity::Advice` or an absent severity becomes `advice`.
MIETTE-JSON-004: When JSON renders causes, `diagnostic_source` takes precedence over the ordinary source chain.
MIETTE-JSON-005: The `primary` flag is not emitted in JSON labels.
MIETTE-JSON-006: Related diagnostics render recursively as JSON objects.
MIETTE-GRAPH-001: Graphical rendering uses source snippets for labels when a source exists.
MIETTE-GRAPH-002: Graphical and narrated renderers use `Advice` presentation when severity is absent.
MIETTE-OPTS-001: `RgbColors` has exactly the variants `Always`, `Preferred`, and `Never`; its default is `Never`.
MIETTE-OPTS-002: `MietteHandlerOpts::new` creates an empty builder.
MIETTE-OPTS-003: `build` returns a `MietteHandler`.
MIETTE-OPTS-004: Explicit options override terminal auto-detection.
MIETTE-THEME-001: `GraphicalTheme` has public fields `characters` and `styles`.
MIETTE-THEME-002: `ThemeStyles` has public fields `error`, `warning`, `advice`, `help`, `link`, `linum`, and `highlights`.
MIETTE-THEME-003: `ThemeCharacters` has public drawing fields for horizontal bars, vertical bars, intersections, arrows, box corners, crosses, underline markers, and severity symbols.
MIETTE-THEME-004: Each public `ThemeCharacters` drawing field is a string value, including one-character symbols and multi-character labels.
MIETTE-CONTRACT-001: Rendering does not consume the diagnostic, labels, related diagnostic collection, or source object.
MIETTE-CONTRACT-002: Builder types are immutable-by-return: each option method consumes the builder value and returns the updated value.
MIETTE-CONTRACT-003: Span reading errors are reported as `MietteError`.
MIETTE-CONTRACT-004: Out-of-bounds spans never panic.
MIETTE-CONTRACT-005: Duplicate global hook installation returns `InstallError` and leaves the original hook active.
MIETTE-CONTRACT-006: Diagnostic metadata returned by manual implementations, dynamic diagnostics, derive-generated implementations, reports, and context wrappers is the same metadata rendered by every handler.
MIETTE-CONTRACT-007: An absent severity is `Advice` in all projections: `Severity::default`, JSON severity text, narrated severity text, graphical severity styling, and any handler options that select severity presentation.
MIETTE-CONTRACT-008: Labels always refer to `SourceSpan` byte offsets and lengths.
MIETTE-CONTRACT-009: Related diagnostics preserve their identity and metadata when rendered recursively.
MIETTE-CONTRACT-010: `diagnostic_source` and the ordinary error source chain are distinct relationships.
MIETTE-CONTRACT-011: Wrapping with context changes the outer display message and leaves the original error available for `source`, `chain`, `root_cause`, and downcast traversal.
MIETTE-CONTRACT-012: Reports capture their handler at construction.
MIETTE-PUBLIC-001: Public Rust names, enum variants, trait method sets, struct fields declared public, constructors, builder methods, conversions, trait implementations, and type aliases described here are contractual.
MIETTE-PUBLIC-002: This crate is a pure Rust library.
