// Spec2Repo oracle - integration tests for miette-fullrepro-001

use std::error::Error as StdError;
use std::fmt::{self, Debug, Display};
use std::sync::Arc;

use miette::{
    bail, diagnostic, ensure, Diagnostic, IntoDiagnostic, JSONReportHandler, LabeledSpan,
    MietteDiagnostic, MietteError, MietteHandlerOpts, NamedSource, NarratableReportHandler, Report,
    ReportHandler, Result, Severity, SourceCode, SourceOffset, SourceSpan, SpanContents, WrapErr,
};
use serde_json::Value;
use thiserror::Error;

#[derive(Debug)]
struct BasicDiag {
    message: &'static str,
    code: Option<&'static str>,
    severity: Option<Severity>,
    help: Option<&'static str>,
    url: Option<&'static str>,
    labels: Vec<LabeledSpan>,
    source: Option<NamedSource<String>>,
    related: Vec<BasicDiag>,
    diagnostic_source: Option<Box<BasicDiag>>,
}

impl BasicDiag {
    fn new(message: &'static str) -> Self {
        Self {
            message,
            code: None,
            severity: None,
            help: None,
            url: None,
            labels: Vec::new(),
            source: None,
            related: Vec::new(),
            diagnostic_source: None,
        }
    }

    fn with_source(mut self) -> Self {
        self.source = Some(NamedSource::new("input.rs", "alpha\nbeta\ngamma\n".to_string()));
        self
    }
}

impl Display for BasicDiag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.message)
    }
}

impl StdError for BasicDiag {}

impl Diagnostic for BasicDiag {
    fn code<'a>(&'a self) -> Option<Box<dyn Display + 'a>> {
        self.code.map(|c| Box::new(c) as Box<dyn Display>)
    }

    fn severity(&self) -> Option<Severity> {
        self.severity
    }

    fn help<'a>(&'a self) -> Option<Box<dyn Display + 'a>> {
        self.help.map(|h| Box::new(h) as Box<dyn Display>)
    }

    fn url<'a>(&'a self) -> Option<Box<dyn Display + 'a>> {
        self.url.map(|u| Box::new(u) as Box<dyn Display>)
    }

    fn source_code(&self) -> Option<&dyn SourceCode> {
        self.source.as_ref().map(|s| s as &dyn SourceCode)
    }

    fn labels(&self) -> Option<Box<dyn Iterator<Item = LabeledSpan> + '_>> {
        if self.labels.is_empty() {
            None
        } else {
            Some(Box::new(self.labels.iter().cloned()))
        }
    }

    fn related<'a>(&'a self) -> Option<Box<dyn Iterator<Item = &'a dyn Diagnostic> + 'a>> {
        if self.related.is_empty() {
            None
        } else {
            Some(Box::new(self.related.iter().map(|d| d as &dyn Diagnostic)))
        }
    }

    fn diagnostic_source(&self) -> Option<&dyn Diagnostic> {
        self.diagnostic_source
            .as_deref()
            .map(|d| d as &dyn Diagnostic)
    }
}

#[derive(Debug, Error, Diagnostic)]
#[error("leaf exploded")]
struct LeafError;

#[derive(Debug)]
struct PlainError(&'static str);

impl Display for PlainError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.0)
    }
}

impl StdError for PlainError {}

fn render_json(diag: &dyn Diagnostic) -> Value {
    let mut out = String::new();
    JSONReportHandler::new()
        .render_report(&mut out, diag)
        .expect("json render");
    serde_json::from_str(&out).expect("valid json")
}

fn render_narrated(diag: &dyn Diagnostic) -> String {
    let mut out = String::new();
    NarratableReportHandler::new()
        .render_report(&mut out, diag)
        .expect("narrated render");
    out
}

#[allow(dead_code)]
fn severity_default_is_advice() {
    // Verifies: MIETTE-DIAG-004, MIETTE-CONTRACT-007
    // MUTATED: MUT-SEVERITY-DEFAULT
    assert_eq!(Severity::default(), Severity::Advice);
}

#[allow(dead_code)]
fn severity_variants_are_distinct() {
    // Verifies: MIETTE-DIAG-003
    assert_ne!(Severity::Advice, Severity::Warning);
    assert_ne!(Severity::Warning, Severity::Error);
}

#[allow(dead_code)]
fn source_offset_from_usize_exposes_raw_offset() {
    // Verifies: MIETTE-SRC-001
    assert_eq!(SourceOffset::from(7usize).offset(), 7);
}

#[allow(dead_code)]
fn source_offset_from_location_uses_one_based_line_column() {
    // Verifies: MIETTE-SRC-002
    let offset = SourceOffset::from_location("a\nxy\nz", 2, 2);
    assert_eq!(offset.offset(), 3);
}

#[allow(dead_code)]
fn source_offset_from_location_clamps_to_end() {
    // Verifies: MIETTE-SRC-003
    let source = "abc";
    assert_eq!(SourceOffset::from_location(source, 9, 1).offset(), source.len());
}

#[allow(dead_code)]
fn source_span_from_offset_is_empty() {
    // Verifies: MIETTE-SRC-005
    let span = SourceSpan::from(9usize);
    assert_eq!(span.offset(), 9);
    assert_eq!(span.len(), 0);
    assert!(span.is_empty());
}

#[allow(dead_code)]
fn source_span_from_range_uses_start_and_len() {
    // Verifies: MIETTE-SRC-004, MIETTE-SRC-013
    let span = SourceSpan::from(3usize..8usize);
    assert_eq!(span.offset(), 3);
    assert_eq!(span.len(), 5);
}

#[allow(dead_code)]
fn source_span_from_inclusive_range_includes_endpoint() {
    // Verifies: MIETTE-SRC-004, MIETTE-SRC-013
    let span = SourceSpan::from(3usize..=8usize);
    assert_eq!(span.offset(), 3);
    assert_eq!(span.len(), 6);
}

#[allow(dead_code)]
fn labeled_span_at_sets_label_offset_and_length() {
    // Verifies: MIETTE-SRC-006
    let label = LabeledSpan::at(2usize..5usize, "name");
    assert_eq!(label.label(), Some("name"));
    assert_eq!(label.offset(), 2);
    assert_eq!(label.len(), 3);
    assert!(!label.primary());
}

#[allow(dead_code)]
fn labeled_span_primary_constructor_marks_primary() {
    // Verifies: MIETTE-SRC-006
    let label = LabeledSpan::new_primary_with_span(Some("main".to_string()), (1usize, 4usize));
    assert_eq!(label.label(), Some("main"));
    assert!(label.primary());
}

#[allow(dead_code)]
fn labeled_span_at_offset_is_empty_span() {
    // Verifies: MIETTE-SRC-006
    let label = LabeledSpan::at_offset(4, "point");
    assert_eq!(label.offset(), 4);
    assert_eq!(label.len(), 0);
    assert!(label.is_empty());
}

#[allow(dead_code)]
fn labeled_span_underline_has_no_label_text() {
    // Verifies: MIETTE-SRC-006
    let label = LabeledSpan::underline(1usize..4usize);
    assert_eq!(label.label(), None);
    assert_eq!(label.inner().offset(), 1);
    assert_eq!(label.inner().len(), 3);
}

#[allow(dead_code)]
fn labeled_span_set_label_replaces_text() {
    // Verifies: MIETTE-SRC-006
    let mut label = LabeledSpan::underline(1usize..4usize);
    label.set_label(Some("replacement".to_string()));
    assert_eq!(label.label(), Some("replacement"));
}

#[allow(dead_code)]
fn miette_span_contents_returns_stored_values() {
    // Verifies: MIETTE-SRC-004, MIETTE-SRC-013
    let bytes = b"abcdef";
    let contents = miette::MietteSpanContents::new(bytes, (1usize, 3usize).into(), 4, 5, 6);
    assert_eq!(contents.data(), bytes);
    assert_eq!(contents.span().offset(), 1);
    assert_eq!(contents.line(), 4);
    assert_eq!(contents.column(), 5);
    assert_eq!(contents.line_count(), 6);
}

#[allow(dead_code)]
fn miette_span_contents_named_language_is_reported() {
    // Verifies: MIETTE-SRC-008, MIETTE-SRC-013
    let contents =
        miette::MietteSpanContents::new_named("file.rs".to_string(), b"abc", (0usize, 3usize).into(), 0, 0, 1)
            .with_language("Rust");
    assert_eq!(contents.name(), Some("file.rs"));
    assert_eq!(contents.language(), Some("Rust"));
}

#[allow(dead_code)]
fn string_source_reads_selected_span() -> std::result::Result<(), MietteError> {
    // Verifies: MIETTE-SRC-007
    let source = "first\nsecond\nthird".to_string();
    let contents = source.read_span(&(6usize, 6usize).into(), 0, 0)?;
    assert_eq!(std::str::from_utf8(contents.data()).unwrap(), "second");
    assert_eq!(contents.line(), 1);
    assert_eq!(contents.column(), 0);
    Ok(())
}

#[allow(dead_code)]
fn string_source_reads_context_lines() -> std::result::Result<(), MietteError> {
    // Verifies: MIETTE-SRC-007
    let source = "zero\none\ntwo\nthree\n".to_string();
    let contents = source.read_span(&(9usize, 3usize).into(), 1, 1)?;
    assert_eq!(std::str::from_utf8(contents.data()).unwrap(), "one\ntwo\nthree\n");
    assert_eq!(contents.line(), 1);
    Ok(())
}

#[allow(dead_code)]
fn byte_source_out_of_bounds_returns_miette_error() {
    // Verifies: MIETTE-SRC-007, MIETTE-CONTRACT-004
    let bytes = b"abc".to_vec();
    assert!(matches!(
        bytes.read_span(&(10usize, 1usize).into(), 0, 0),
        Err(MietteError::OutOfBounds)
    ));
}

#[allow(dead_code)]
fn named_source_adds_name_to_span_contents() -> std::result::Result<(), MietteError> {
    // Verifies: MIETTE-SRC-008, MIETTE-SRC-013
    let source = NamedSource::new("demo.txt", "hello".to_string());
    let contents = source.read_span(&(0usize, 5usize).into(), 0, 0)?;
    assert_eq!(contents.name(), Some("demo.txt"));
    assert_eq!(std::str::from_utf8(contents.data()).unwrap(), "hello");
    Ok(())
}

#[allow(dead_code)]
fn named_source_adds_language_to_span_contents() -> std::result::Result<(), MietteError> {
    // Verifies: MIETTE-SRC-008, MIETTE-SRC-013
    let source = NamedSource::new("demo.rs", "fn main() {}".to_string()).with_language("Rust");
    let contents = source.read_span(&(0usize, 2usize).into(), 0, 0)?;
    assert_eq!(contents.language(), Some("Rust"));
    Ok(())
}

#[allow(dead_code)]
fn miette_error_out_of_bounds_has_code_and_help() {
    // Verifies: MIETTE-DIAG-005
    let error = MietteError::OutOfBounds;
    assert_eq!(error.code().unwrap().to_string(), "miette::span_out_of_bounds");
    assert!(error.help().is_some());
    assert!(error.source().is_none());
}

#[allow(dead_code)]
fn miette_error_io_preserves_source() {
    // Verifies: MIETTE-DIAG-005
    let inner = std::io::Error::new(std::io::ErrorKind::Other, PlainError("inner"));
    let error = MietteError::from(inner);
    assert_eq!(error.code().unwrap().to_string(), "miette::io_error");
    assert_eq!(error.to_string(), "inner");
    assert!(error.help().is_none());
}

#[allow(dead_code)]
fn miette_diagnostic_new_sets_message_only() {
    // Verifies: MIETTE-DYN-002
    let diag = MietteDiagnostic::new("hello");
    assert_eq!(diag.message, "hello");
    assert_eq!(diag.code, None);
    assert_eq!(diag.severity, None);
}

#[allow(dead_code)]
fn miette_diagnostic_builders_set_metadata() {
    // Verifies: MIETTE-DYN-001
    let diag = MietteDiagnostic::new("hello")
        .with_code("demo::code")
        .with_severity(Severity::Warning)
        .with_help("fix it")
        .with_url("https://example.test");
    assert_eq!(diag.code().unwrap().to_string(), "demo::code");
    assert_eq!(diag.severity(), Some(Severity::Warning));
    assert_eq!(diag.help().unwrap().to_string(), "fix it");
    assert_eq!(diag.url().unwrap().to_string(), "https://example.test");
}

#[allow(dead_code)]
fn miette_diagnostic_with_label_replaces_labels() {
    // Verifies: MIETTE-DYN-003
    let diag = MietteDiagnostic::new("labels")
        .with_labels([LabeledSpan::at(0usize..1usize, "old")])
        .with_label(LabeledSpan::at(2usize..3usize, "new"));
    let labels: Vec<_> = diag.labels().unwrap().collect();
    assert_eq!(labels.len(), 1);
    assert_eq!(labels[0].label(), Some("new"));
}

#[allow(dead_code)]
fn miette_diagnostic_and_label_appends() {
    // Verifies: MIETTE-DYN-004
    let diag = MietteDiagnostic::new("labels")
        .and_label(LabeledSpan::at(0usize..1usize, "a"))
        .and_label(LabeledSpan::at(1usize..2usize, "b"));
    let labels: Vec<_> = diag.labels().unwrap().collect();
    assert_eq!(labels.iter().map(|l| l.label()).collect::<Vec<_>>(), vec![Some("a"), Some("b")]);
}

#[allow(dead_code)]
fn report_is_send_and_sync() {
    // Verifies: MIETTE-REPORT-001
    fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<Report>();
}

#[allow(dead_code)]
fn rgb_colors_default_is_never() {
    // Verifies: MIETTE-OPTS-001
    assert_eq!(miette::RgbColors::default(), miette::RgbColors::Never);
}

#[allow(dead_code)]
fn handler_opts_build_returns_miette_handler() {
    // Verifies: MIETTE-OPTS-002, MIETTE-OPTS-003
    let handler = MietteHandlerOpts::new().force_narrated(true).build();
    let as_trait: &dyn ReportHandler = &handler;
    assert!(as_trait.is::<miette::MietteHandler>());
}

#[allow(dead_code)]
fn graphical_theme_has_public_parts() {
    // Verifies: MIETTE-THEME-001
    let theme = miette::GraphicalTheme::none();
    assert_eq!(theme.characters.error, "x");
    assert!(theme.styles.highlights.len() >= 1);
}

#[allow(dead_code)]
fn theme_styles_none_has_one_highlight_style() {
    // Verifies: MIETTE-THEME-002
    let styles = miette::ThemeStyles::none();
    assert_eq!(styles.highlights.len(), 1);
}

#[allow(dead_code)]
fn theme_characters_ascii_uses_ascii_severity_symbols() {
    // Verifies: MIETTE-THEME-003
    let chars = miette::ThemeCharacters::ascii();
    assert_eq!(chars.error, "x");
    assert_eq!(chars.warning, "!");
}

#[derive(Debug, Error, Diagnostic)]
#[error("coded")]
#[diagnostic(code(demo::coded), severity(Warning), help("try again"), url("https://example.test/coded"))]
struct CodedDiag;

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn derive_struct_static_metadata() {
    // Verifies: MIETTE-DERIVE-001, MIETTE-DERIVE-002
    let diag = CodedDiag;
    assert_eq!(diag.code().unwrap().to_string(), "demo::coded");
    assert_eq!(diag.severity(), Some(Severity::Warning));
    assert_eq!(diag.help().unwrap().to_string(), "try again");
    assert_eq!(diag.url().unwrap().to_string(), "https://example.test/coded");
}

#[derive(Debug, Error, Diagnostic)]
enum EnumDiag {
    #[error("one")]
    #[diagnostic(code(demo::one), severity(Advice))]
    One,
    #[error("two")]
    #[diagnostic(code(demo::two), severity(Error))]
    Two,
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn derive_enum_variant_metadata() {
    // Verifies: MIETTE-DERIVE-002
    assert_eq!(EnumDiag::One.code().unwrap().to_string(), "demo::one");
    assert_eq!(EnumDiag::One.severity(), Some(Severity::Advice));
    assert_eq!(EnumDiag::Two.code().unwrap().to_string(), "demo::two");
    assert_eq!(EnumDiag::Two.severity(), Some(Severity::Error));
}

#[derive(Debug, Error, Diagnostic)]
#[error("source carrier")]
struct SourceCarrier {
    #[source_code]
    src: NamedSource<String>,
    #[label("here")]
    span: SourceSpan,
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn derive_source_code_and_label_fields() {
    // Verifies: MIETTE-DERIVE-003, MIETTE-DERIVE-004
    let diag = SourceCarrier {
        src: NamedSource::new("input.txt", "abcd".to_string()),
        span: (1usize, 2usize).into(),
    };
    assert!(diag.source_code().is_some());
    let labels: Vec<_> = diag.labels().unwrap().collect();
    assert_eq!(labels[0].label(), Some("here"));
    assert_eq!(labels[0].offset(), 1);
}

#[derive(Debug, Error, Diagnostic)]
#[error(transparent)]
#[diagnostic(transparent)]
struct TransparentDiag(#[from] CodedDiag);

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn derive_transparent_delegates_metadata() {
    // Verifies: MIETTE-DERIVE-005
    let diag = TransparentDiag(CodedDiag);
    assert_eq!(diag.code().unwrap().to_string(), "demo::coded");
    assert_eq!(diag.severity(), Some(Severity::Warning));
}

#[derive(Debug, Error, Diagnostic)]
#[error("outer")]
#[diagnostic(forward(inner), severity(Error))]
struct ForwardDiag {
    inner: CodedDiag,
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn derive_forward_uses_inner_and_allows_override() {
    // Verifies: MIETTE-DERIVE-006
    let diag = ForwardDiag { inner: CodedDiag };
    assert_eq!(diag.code().unwrap().to_string(), "demo::coded");
    assert_eq!(diag.severity(), Some(Severity::Error));
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_absent_severity_renders_advice() {
    // Verifies: MIETTE-JSON-003, MIETTE-CONTRACT-007
    // MUTATED: MUT-SEVERITY-DEFAULT
    let json = render_json(&BasicDiag::new("plain"));
    assert_eq!(json["severity"], "advice");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_explicit_severity_renders_lowercase() {
    // Verifies: MIETTE-JSON-003
    let mut diag = BasicDiag::new("warn");
    diag.severity = Some(Severity::Warning);
    let json = render_json(&diag);
    assert_eq!(json["severity"], "warning");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_includes_code_help_and_url() {
    // Verifies: MIETTE-JSON-002
    let mut diag = BasicDiag::new("rich");
    diag.code = Some("demo::rich");
    diag.help = Some("fix");
    diag.url = Some("https://example.test/rich");
    let json = render_json(&diag);
    assert_eq!(json["message"], "rich");
    assert_eq!(json["code"], "demo::rich");
    assert_eq!(json["help"], "fix");
    assert_eq!(json["url"], "https://example.test/rich");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_escapes_strings() {
    // Verifies: MIETTE-JSON-002
    let json = render_json(&BasicDiag::new("a\nb\\c\"d"));
    assert_eq!(json["message"], "a\nb\\c\"d");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_label_contains_span_without_primary_flag() {
    // Verifies: MIETTE-JSON-005
    let mut diag = BasicDiag::new("label").with_source();
    diag.labels.push(LabeledSpan::new_primary_with_span(Some("main".to_string()), (6usize, 4usize)));
    let json = render_json(&diag);
    assert_eq!(json["labels"][0]["label"], "main");
    assert_eq!(json["labels"][0]["span"]["offset"], 6);
    assert_eq!(json["labels"][0]["span"]["length"], 4);
    assert!(json["labels"][0].get("primary").is_none());
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_filename_comes_from_first_label_source() {
    // Verifies: MIETTE-JSON-002
    let mut diag = BasicDiag::new("label").with_source();
    diag.labels.push(LabeledSpan::at(6usize..10usize, "main"));
    let json = render_json(&diag);
    assert_eq!(json["filename"], "input.rs");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_causes_use_diagnostic_source_first() {
    // Verifies: MIETTE-JSON-004, MIETTE-CONTRACT-010
    let mut diag = BasicDiag::new("outer");
    diag.diagnostic_source = Some(Box::new(BasicDiag::new("diagnostic cause")));
    let json = render_json(&diag);
    assert_eq!(json["causes"][0], "diagnostic cause");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_related_renders_recursively() {
    // Verifies: MIETTE-JSON-006
    let mut diag = BasicDiag::new("outer");
    diag.related.push(BasicDiag::new("related one"));
    let json = render_json(&diag);
    assert_eq!(json["related"][0]["message"], "related one");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn json_related_inherits_parent_source_for_filename() {
    // Verifies: MIETTE-JSON-006
    let mut related = BasicDiag::new("related");
    related.labels.push(LabeledSpan::at(0usize..5usize, "rel"));
    let mut diag = BasicDiag::new("outer").with_source();
    diag.related.push(related);
    let json = render_json(&diag);
    assert_eq!(json["related"][0]["filename"], "input.rs");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn narrated_absent_severity_renders_advice() {
    // Verifies: MIETTE-GRAPH-002, MIETTE-CONTRACT-007
    // MUTATED: MUT-SEVERITY-DEFAULT
    let text = render_narrated(&BasicDiag::new("plain"));
    assert!(text.contains("Diagnostic severity: advice"));
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn narrated_includes_help_code_and_url() {
    // Verifies: MIETTE-RENDER-002
    let mut diag = BasicDiag::new("rich");
    diag.code = Some("demo::rich");
    diag.help = Some("fix this");
    diag.url = Some("https://example.test/rich");
    let text = render_narrated(&diag);
    assert!(text.contains("diagnostic code: demo::rich"));
    assert!(text.contains("diagnostic help: fix this"));
    assert!(text.contains("https://example.test/rich"));
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn narrated_includes_source_label_text() {
    // Verifies: MIETTE-GRAPH-001
    let mut diag = BasicDiag::new("source").with_source();
    diag.labels.push(LabeledSpan::at(6usize..10usize, "beta label"));
    let text = render_narrated(&diag);
    assert!(text.contains("input.rs"));
    assert!(text.contains("beta label"));
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn narrated_related_diagnostic_is_rendered() {
    // Verifies: MIETTE-CONTRACT-009
    let mut diag = BasicDiag::new("outer");
    diag.related.push(BasicDiag::new("child"));
    let text = render_narrated(&diag);
    assert!(text.contains("child"));
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn report_new_derefs_to_diagnostic_metadata() {
    // Verifies: MIETTE-REPORT-002, MIETTE-CONTRACT-006
    let mut diag = BasicDiag::new("report");
    diag.code = Some("demo::report");
    let report = Report::new(diag);
    assert_eq!(report.code().unwrap().to_string(), "demo::report");
}

#[allow(dead_code)]
fn report_msg_downcasts_to_message_type() {
    // Verifies: MIETTE-WRAP-004
    let report = Report::msg("message");
    assert!(report.is::<&'static str>());
    assert_eq!(*report.downcast_ref::<&'static str>().unwrap(), "message");
}

#[allow(dead_code)]
fn report_new_boxed_preserves_display() {
    // Verifies: MIETTE-REPORT-002
    let report = Report::new_boxed(Box::new(BasicDiag::new("boxed")));
    assert_eq!(report.to_string(), "boxed");
}

#[allow(dead_code)]
fn into_diagnostic_converts_plain_error_result() {
    // Verifies: MIETTE-REPORT-003
    let result: std::result::Result<(), PlainError> = Err(PlainError("plain"));
    let report = result.into_diagnostic().unwrap_err();
    assert_eq!(report.to_string(), "plain");
}

#[allow(dead_code)]
fn option_wrap_err_none_creates_report() {
    // Verifies: MIETTE-WRAP-002, MIETTE-WRAP-003
    let report = Option::<u8>::None.wrap_err("missing").unwrap_err();
    assert_eq!(report.to_string(), "missing");
}

#[allow(dead_code)]
fn option_wrap_err_some_returns_value() -> Result<()> {
    // Verifies: MIETTE-WRAP-002
    assert_eq!(Some(4u8).wrap_err("missing")?, 4);
    Ok(())
}

#[allow(dead_code)]
fn wrap_err_lazy_closure_runs_only_on_error() {
    // Verifies: MIETTE-WRAP-001
    let mut called = false;
    let value: std::result::Result<u8, LeafError> = Ok(3);
    let out = value.wrap_err_with(|| {
        called = true;
        "context"
    });
    assert_eq!(out.unwrap(), 3);
    assert!(!called);
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn wrapping_preserves_original_downcast() {
    // Verifies: MIETTE-WRAP-004
    let result: std::result::Result<(), LeafError> = Err(LeafError);
    let report = result.wrap_err("top context").unwrap_err();
    assert!(report.downcast_ref::<LeafError>().is_some());
    assert_eq!(report.downcast_ref::<&'static str>(), Some(&"top context"));
}

#[allow(dead_code)]
fn consuming_downcast_returns_original_value() {
    // Verifies: MIETTE-WRAP-004
    let report = Report::new(LeafError);
    let leaf = report.downcast::<LeafError>().unwrap();
    assert_eq!(leaf.to_string(), "leaf exploded");
}

#[allow(dead_code)]
fn unsuccessful_downcast_returns_report() {
    // Verifies: MIETTE-WRAP-004
    let report = Report::new(LeafError);
    assert!(report.downcast::<PlainError>().is_err());
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn chain_iterates_outer_to_root() {
    // Verifies: MIETTE-WRAP-005, MIETTE-CONTRACT-011
    let report = std::result::Result::<(), LeafError>::Err(LeafError)
        .wrap_err("middle")
        .unwrap_err()
        .wrap_err("outer");
    let messages: Vec<_> = report.chain().map(ToString::to_string).collect();
    assert_eq!(messages, vec!["outer", "middle", "leaf exploded"]);
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn root_cause_returns_last_chain_error() {
    // Verifies: MIETTE-WRAP-005
    let report = std::result::Result::<(), LeafError>::Err(LeafError)
        .wrap_err("middle")
        .unwrap_err();
    assert_eq!(report.root_cause().to_string(), "leaf exploded");
}

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
#[test]
fn with_source_code_supplies_source_for_report_labels() {
    // Verifies: MIETTE-CONTRACT-006, MIETTE-CONTRACT-008
    let diag = MietteDiagnostic::new("bad").with_label(LabeledSpan::at(0usize..5usize, "name"));
    let report = Report::new(diag).with_source_code(NamedSource::new("override.txt", "hello".to_string()));
    let json = render_json(&*report);
    assert_eq!(json["filename"], "override.txt");
}

#[allow(dead_code)]
fn diagnostic_macro_sets_dynamic_metadata() {
    // Verifies: MIETTE-DYN-001
    let diag = diagnostic!(
        code = "demo::macro",
        severity = Severity::Warning,
        help = "macro help",
        "macro message"
    );
    assert_eq!(diag.to_string(), "macro message");
    assert_eq!(diag.code().unwrap().to_string(), "demo::macro");
    assert_eq!(diag.severity(), Some(Severity::Warning));
    assert_eq!(diag.help().unwrap().to_string(), "macro help");
}

#[allow(dead_code)]
fn miette_macro_builds_report_message() {
    // Verifies: MIETTE-REPORT-003
    let report = miette::miette!("macro report");
    assert_eq!(report.to_string(), "macro report");
}

#[allow(dead_code)]
fn bail_macro_returns_report_early() {
    // Verifies: MIETTE-PUBLIC-001
    fn run() -> Result<()> {
        bail!("stop now");
    }
    assert_eq!(run().unwrap_err().to_string(), "stop now");
}

#[allow(dead_code)]
fn ensure_macro_passes_true_condition() -> Result<()> {
    // Verifies: MIETTE-PUBLIC-001
    ensure!(2 + 2 == 4, "math broke");
    Ok(())
}

#[allow(dead_code)]
fn ensure_macro_returns_error_for_false_condition() {
    // Verifies: MIETTE-PUBLIC-001
    fn run() -> Result<()> {
        ensure!(false, "nope");
        Ok(())
    }
    assert_eq!(run().unwrap_err().to_string(), "nope");
}

#[allow(dead_code)]
fn report_handler_trait_object_downcasts_to_concrete_handler() {
    // Verifies: MIETTE-RENDER-001
    let handler: Box<dyn ReportHandler> = Box::new(JSONReportHandler::new());
    assert!(handler.is::<JSONReportHandler>());
    assert!(handler.downcast_ref::<JSONReportHandler>().is_some());
}

#[allow(dead_code)]
fn arc_source_code_delegates_to_inner_source() -> std::result::Result<(), MietteError> {
    // Verifies: MIETTE-SRC-007
    let source = Arc::new("abcdef".to_string());
    let contents = source.read_span(&(2usize, 3usize).into(), 0, 0)?;
    assert_eq!(std::str::from_utf8(contents.data()).unwrap(), "cde");
    Ok(())
}

#[allow(dead_code)]
fn diagnostic_related_iterator_preserves_order() {
    // Verifies: MIETTE-CONTRACT-009
    let mut diag = BasicDiag::new("outer");
    diag.related.push(BasicDiag::new("first"));
    diag.related.push(BasicDiag::new("second"));
    let names: Vec<_> = diag.related().unwrap().map(ToString::to_string).collect();
    assert_eq!(names, vec!["first", "second"]);
}

mod generated_track_b {
    use std::error::Error as StdError;
    use std::fmt::{self, Display};

    use miette::{
        diagnostic, Diagnostic, JSONReportHandler, LabeledSpan, MietteDiagnostic, MietteError,
        NamedSource, Report, Severity, SourceCode, SourceOffset, SourceSpan, WrapErr,
    };
    use serde_json::Value;
    use thiserror::Error;

    #[derive(Debug)]
    struct MetaDiag {
        message: &'static str,
        code: Option<&'static str>,
        severity: Option<Severity>,
        help: Option<&'static str>,
        url: Option<&'static str>,
        labels: Vec<LabeledSpan>,
        source: Option<NamedSource<String>>,
    }

    impl MetaDiag {
        fn rich() -> Self {
            Self {
                message: "rich",
                code: Some("demo::rich"),
                severity: Some(Severity::Warning),
                help: Some("repair"),
                url: Some("https://example.test/rich"),
                labels: vec![LabeledSpan::at(6usize..10usize, "label")],
                source: Some(NamedSource::new("demo.txt", "alpha\nbeta\ngamma\n".to_string())),
            }
        }
    }

    impl Display for MetaDiag {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            f.write_str(self.message)
        }
    }

    impl StdError for MetaDiag {}

    impl Diagnostic for MetaDiag {
        fn code<'a>(&'a self) -> Option<Box<dyn Display + 'a>> {
            self.code.map(|v| Box::new(v) as Box<dyn Display>)
        }
        fn severity(&self) -> Option<Severity> {
            self.severity
        }
        fn help<'a>(&'a self) -> Option<Box<dyn Display + 'a>> {
            self.help.map(|v| Box::new(v) as Box<dyn Display>)
        }
        fn url<'a>(&'a self) -> Option<Box<dyn Display + 'a>> {
            self.url.map(|v| Box::new(v) as Box<dyn Display>)
        }
        fn source_code(&self) -> Option<&dyn SourceCode> {
            self.source.as_ref().map(|s| s as &dyn SourceCode)
        }
        fn labels(&self) -> Option<Box<dyn Iterator<Item = LabeledSpan> + '_>> {
            Some(Box::new(self.labels.iter().cloned()))
        }
    }

    #[derive(Debug, Error, Diagnostic)]
    #[error("leaf")]
    #[diagnostic(code(demo::leaf), help("leaf help"))]
    struct Leaf;

    fn render_json(diag: &dyn Diagnostic) -> Value {
        let mut out = String::new();
        JSONReportHandler::new().render_report(&mut out, diag).unwrap();
        serde_json::from_str(&out).unwrap()
    }

    #[allow(dead_code)]
    fn generated_source_offset_counts_utf8_bytes() {
        // Verifies: MIETTE-SRC-002
        let offset = SourceOffset::from_location("é\nz", 2, 1);
        assert_eq!(offset.offset(), 3);
    }

    #[allow(dead_code)]
    fn generated_source_span_inclusive_singleton_has_length_one() {
        // Verifies: MIETTE-SRC-004, MIETTE-SRC-013
        let span = SourceSpan::from(4usize..=4usize);
        assert_eq!(span.offset(), 4);
        assert_eq!(span.len(), 1);
    }

    #[allow(dead_code)]
    fn generated_source_read_middle_of_line_reports_column() -> std::result::Result<(), MietteError> {
        // Verifies: MIETTE-SRC-007
        let source = "abc\ndefghi\njkl".to_string();
        let contents = source.read_span(&(6usize, 3usize).into(), 0, 0)?;
        assert_eq!(std::str::from_utf8(contents.data()).unwrap(), "fgh");
        assert_eq!(contents.line(), 1);
        assert_eq!(contents.column(), 2);
        Ok(())
    }

    #[allow(dead_code)]
    fn generated_source_read_crlf_counts_one_line_break() -> std::result::Result<(), MietteError> {
        // Verifies: MIETTE-SRC-007
        let source = "aa\r\nbb\r\ncc".to_string();
        let contents = source.read_span(&(4usize, 2usize).into(), 0, 0)?;
        assert_eq!(std::str::from_utf8(contents.data()).unwrap(), "bb");
        assert_eq!(contents.line(), 1);
        assert_eq!(contents.column(), 0);
        Ok(())
    }

    #[allow(dead_code)]
    fn generated_source_offset_after_crlf_uses_single_line_increment() {
        // Verifies: MIETTE-SRC-002
        let source = "aa\r\nbb\r\ncc";
        let offset = SourceOffset::from_location(source, 3, 1);
        assert_eq!(offset.offset(), 8);
    }

    #[allow(dead_code)]
    fn generated_source_read_zero_length_span_returns_empty_slice() -> std::result::Result<(), MietteError> {
        // Verifies: MIETTE-SRC-007
        let source = "abcdef".to_string();
        let contents = source.read_span(&(3usize, 0usize).into(), 0, 0)?;
        assert_eq!(contents.data(), b"");
        assert_eq!(contents.line(), 0);
        assert_eq!(contents.column(), 3);
        Ok(())
    }

    #[allow(dead_code)]
    fn generated_source_context_updates_returned_span_offset() -> std::result::Result<(), MietteError> {
        // Verifies: MIETTE-SRC-007
        let source = "zero\none\ntwo\nthree\nfour\n".to_string();
        let contents = source.read_span(&(13usize, 5usize).into(), 1, 1)?;
        assert_eq!(contents.span().offset(), 9);
        assert_eq!(contents.line(), 2);
        assert!(std::str::from_utf8(contents.data()).unwrap().starts_with("two\n"));
        Ok(())
    }

    #[allow(dead_code)]
    fn generated_vec_source_out_of_bounds_returns_error() {
        // Verifies: MIETTE-CONTRACT-004
        let data = vec![1u8, 2, 3, 4];
        assert!(matches!(
            data.read_span(&(5usize, 1usize).into(), 0, 0),
            Err(MietteError::OutOfBounds)
        ));
    }

    #[allow(dead_code)]
    fn generated_out_of_bounds_display_is_protocol_message() {
        // Verifies: MIETTE-DIAG-005
        assert_eq!(
            MietteError::OutOfBounds.to_string(),
            "The given offset is outside the bounds of its Source"
        );
    }

    #[allow(dead_code)]
    fn generated_out_of_bounds_url_names_variant() {
        // Verifies: MIETTE-DIAG-005
        let url = MietteError::OutOfBounds.url().unwrap().to_string();
        assert!(url.contains("enum.MietteError.html#variant.OutOfBounds"));
    }

    #[allow(dead_code)]
    fn generated_io_error_url_names_variant() {
        // Verifies: MIETTE-DIAG-005
        let err = MietteError::from(std::io::Error::new(std::io::ErrorKind::Other, "io"));
        let url = err.url().unwrap().to_string();
        assert!(url.contains("enum.MietteError.html#variant.IoError"));
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_report_new_preserves_diagnostic_code() {
        // Verifies: MIETTE-CONTRACT-006
        let report = Report::new(MetaDiag::rich());
        assert_eq!(report.code().unwrap().to_string(), "demo::rich");
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_report_new_boxed_preserves_diagnostic_help() {
        // Verifies: MIETTE-CONTRACT-006
        let report = Report::new_boxed(Box::new(MetaDiag::rich()));
        assert_eq!(report.help().unwrap().to_string(), "repair");
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_report_wrap_err_forwards_inner_code() {
        // Verifies: MIETTE-CONTRACT-006, MIETTE-CONTRACT-011
        let report = Report::new(MetaDiag::rich()).wrap_err("outer");
        assert_eq!(report.to_string(), "outer");
        assert_eq!(report.code().unwrap().to_string(), "demo::rich");
    }

    #[allow(dead_code)]
    fn generated_diagnostic_macro_sets_url() {
        // Verifies: MIETTE-DYN-001, MIETTE-MACRO-003
        let diag = diagnostic!(url = "https://example.test/doc", "message");
        assert_eq!(diag.url().unwrap().to_string(), "https://example.test/doc");
    }

    #[allow(dead_code)]
    fn generated_diagnostic_macro_sets_labels() {
        // Verifies: MIETTE-DYN-001, MIETTE-MACRO-003
        let diag = diagnostic!(
            labels = vec![LabeledSpan::at(2usize..4usize, "macro label")],
            "message"
        );
        let labels: Vec<_> = diag.labels().unwrap().collect();
        assert_eq!(labels[0].label(), Some("macro label"));
        assert_eq!(labels[0].offset(), 2);
    }

    #[derive(Debug, Error, Diagnostic)]
    #[error("dynamic help")]
    struct DynamicHelp<'a> {
        #[help]
        help: &'a str,
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_derive_help_field_is_dynamic() {
        // Verifies: MIETTE-DERIVE-002
        let diag = DynamicHelp { help: "from field" };
        assert_eq!(diag.help().unwrap().to_string(), "from field");
    }

    #[derive(Debug, Error, Diagnostic)]
    #[error("has related")]
    struct HasRelated {
        #[related]
        related: Vec<Leaf>,
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_derive_related_field_returns_children() {
        // Verifies: MIETTE-DERIVE-004, MIETTE-CONTRACT-009
        let diag = HasRelated { related: vec![Leaf] };
        let children: Vec<_> = diag.related().unwrap().map(ToString::to_string).collect();
        assert_eq!(children, vec!["leaf"]);
    }

    #[derive(Debug, Error, Diagnostic)]
    #[error("has source")]
    struct HasDiagnosticSource {
        #[diagnostic_source]
        source: Leaf,
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_derive_diagnostic_source_is_json_cause() {
        // Verifies: MIETTE-DERIVE-002, MIETTE-JSON-004
        let json = render_json(&HasDiagnosticSource { source: Leaf });
        assert_eq!(json["causes"][0], "leaf");
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_json_report_uses_diagnostic_source_before_std_source() {
        // Verifies: MIETTE-JSON-004, MIETTE-CONTRACT-010
        #[derive(Debug)]
        struct DualSource;
        impl Display for DualSource {
            fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("dual")
            }
        }
        impl StdError for DualSource {
            fn source(&self) -> Option<&(dyn StdError + 'static)> {
                Some(&Leaf)
            }
        }
        impl Diagnostic for DualSource {
            fn diagnostic_source(&self) -> Option<&dyn Diagnostic> {
                Some(&Leaf)
            }
        }
        let json = render_json(&DualSource);
        assert_eq!(json["causes"], serde_json::json!(["leaf"]));
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_json_report_projects_source_label_and_metadata_together() {
        // Verifies: MIETTE-JSON-002, MIETTE-CONTRACT-008
        let json = render_json(&MetaDiag::rich());
        assert_eq!(json["message"], "rich");
        assert_eq!(json["filename"], "demo.txt");
        assert_eq!(json["labels"][0]["span"]["offset"], 6);
        assert_eq!(json["severity"], "warning");
    }

// DependsOn: arc_source_code_delegates_to_inner_source, byte_source_out_of_bounds_returns_miette_error, consuming_downcast_returns_original_value
    #[test]
    fn generated_context_chain_preserves_middle_and_leaf_downcasts() {
        // Verifies: MIETTE-WRAP-004, MIETTE-CONTRACT-011
        let report = std::result::Result::<(), Leaf>::Err(Leaf)
            .wrap_err(MietteDiagnostic::new("middle"))
            .unwrap_err()
            .wrap_err("outer");
        assert!(report.downcast_ref::<Leaf>().is_some());
        assert!(report.downcast_ref::<MietteDiagnostic>().is_some());
        assert_eq!(report.to_string(), "outer");
    }
}
