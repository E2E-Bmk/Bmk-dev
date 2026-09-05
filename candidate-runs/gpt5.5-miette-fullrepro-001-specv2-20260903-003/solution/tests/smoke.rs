use std::error::Error as StdError;
use std::fmt;

use miette::{Diagnostic, LabeledSpan, SourceCode, SourceSpan, WrapErr};

#[derive(Debug, Diagnostic)]
#[diagnostic(code(example::bad), severity(Warning), help("bad field {span:?}"))]
struct MyDiag {
    #[source_code]
    src: String,
    #[label("here")]
    span: SourceSpan,
}

impl fmt::Display for MyDiag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("my diag")
    }
}

impl StdError for MyDiag {}

#[derive(Debug, Diagnostic)]
enum EnumDiag {
    #[diagnostic(code(enum_diag::a))]
    A {
        #[label("enum label")]
        span: SourceSpan,
    },
    #[diagnostic(transparent)]
    B(MyDiag),
}

impl fmt::Display for EnumDiag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::A { .. } => f.write_str("enum a"),
            Self::B(inner) => fmt::Display::fmt(inner, f),
        }
    }
}

impl StdError for EnumDiag {}

#[test]
fn derive_and_source_work() {
    let diag = MyDiag {
        src: "a\nbc\n".to_string(),
        span: (2, 2).into(),
    };
    assert_eq!(diag.code().unwrap().to_string(), "example::bad");
    assert_eq!(diag.severity(), Some(miette::Severity::Warning));
    assert!(diag.help().unwrap().to_string().contains("SourceSpan"));
    assert_eq!(diag.labels().unwrap().next().unwrap().label(), Some("here"));
    let contents = diag.src.read_span(&(2, 2).into(), 1, 0).unwrap();
    assert_eq!(contents.line(), 0);
    assert_eq!(contents.name(), None);
    drop(contents);
    let report: miette::Report = diag.into();
    assert!(report.downcast_ref::<MyDiag>().is_some());
}

#[test]
fn wrapping_preserves_context_downcast() {
    let report = Option::<u8>::None.wrap_err("missing").unwrap_err();
    assert_eq!(report.to_string(), "missing");
    assert!(report.downcast_ref::<&'static str>().is_some());
    let report = report.wrap_err(String::from("outer"));
    assert!(report.downcast_ref::<String>().is_some());
    assert_eq!(report.root_cause().to_string(), "missing");
}

#[test]
fn dynamic_diagnostic_labels() {
    let diagnostic = miette::diagnostic!(
        code = "x",
        severity = miette::Severity::Error,
        labels = vec![LabeledSpan::at((1, 2), "label")],
        "message {}",
        1
    );
    assert_eq!(diagnostic.to_string(), "message 1");
    assert_eq!(diagnostic.code().unwrap().to_string(), "x");
}

#[test]
fn source_override_is_visible_through_deref() {
    let diagnostic =
        miette::diagnostic!(labels = vec![LabeledSpan::at((0, 1), "first")], "message");
    let report = miette::Report::new(diagnostic)
        .with_source_code(miette::NamedSource::new("input.rs", "abc"));
    assert!(report.source_code().is_some());
    let mut json = String::new();
    miette::JSONReportHandler::new()
        .render_report(&mut json, &*report)
        .unwrap();
    assert!(json.contains("input.rs"));
}

#[test]
fn boxed_diagnostic_downcasts() {
    let boxed: Box<dyn Diagnostic + Send + Sync> = Box::new(MyDiag {
        src: "abc".to_string(),
        span: (0, 1).into(),
    });
    let report = miette::Report::new_boxed(boxed);
    assert!(report.downcast_ref::<MyDiag>().is_some());
    let value = report.downcast::<MyDiag>().unwrap();
    assert_eq!(value.span.offset(), 0);
}

#[test]
fn enum_derive_handles_variant_fields_and_transparent() {
    let diag = EnumDiag::A {
        span: (3, 4).into(),
    };
    assert_eq!(diag.code().unwrap().to_string(), "enum_diag::a");
    assert_eq!(
        diag.labels().unwrap().next().unwrap().label(),
        Some("enum label")
    );

    let inner = MyDiag {
        src: "abc".to_string(),
        span: (0, 1).into(),
    };
    let diag = EnumDiag::B(inner);
    assert_eq!(diag.code().unwrap().to_string(), "example::bad");
}
