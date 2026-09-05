use std::any::{Any, TypeId};
use std::borrow::Cow;
use std::cmp;
use std::error::Error as StdError;
use std::fmt;
use std::ops::{Deref, Range, RangeInclusive};
use std::panic::Location;
use std::sync::{Arc, OnceLock};

#[cfg(feature = "derive")]
pub use miette_derive::Diagnostic;

pub type ByteOffset = usize;
pub type Error = Report;
pub type ErrReport = Report;
pub type EyreContext = dyn ReportHandler;
pub type Result<T, E = Report> = core::result::Result<T, E>;
pub type ErrorHook = Box<dyn Fn(&dyn Diagnostic) -> Box<dyn ReportHandler> + Send + Sync + 'static>;

pub trait Diagnostic: StdError + Any {
    fn code<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        None
    }

    fn severity(&self) -> Option<Severity> {
        None
    }

    fn help<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        None
    }

    fn url<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        None
    }

    fn source_code(&self) -> Option<&dyn SourceCode> {
        None
    }

    fn labels(&self) -> Option<Box<dyn Iterator<Item = LabeledSpan> + '_>> {
        None
    }

    fn related(&self) -> Option<Box<dyn Iterator<Item = &dyn Diagnostic> + '_>> {
        None
    }

    fn diagnostic_source(&self) -> Option<&dyn Diagnostic> {
        None
    }
}

#[derive(Copy, Clone, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Severity {
    #[default]
    Advice,
    Warning,
    Error,
}

impl fmt::Display for Severity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Advice => "advice",
            Self::Warning => "warning",
            Self::Error => "error",
        })
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SourceOffset(usize);

impl SourceOffset {
    pub fn from_location(source: &str, line: usize, column: usize) -> Self {
        let mut cur_line = 1usize;
        let mut cur_col = 1usize;
        for (idx, ch) in source.char_indices() {
            if cur_line == line && cur_col == column {
                return Self(idx);
            }
            if ch == '\n' {
                cur_line += 1;
                cur_col = 1;
            } else {
                cur_col += 1;
            }
        }
        if cur_line == line && cur_col == column {
            Self(source.len())
        } else {
            Self(source.len())
        }
    }

    #[track_caller]
    pub fn from_current_location() -> Result<Self, MietteError> {
        let loc = Location::caller();
        let source = std::fs::read_to_string(loc.file()).map_err(MietteError::IoError)?;
        Ok(Self::from_location(
            &source,
            loc.line() as usize,
            loc.column() as usize,
        ))
    }

    pub fn offset(&self) -> usize {
        self.0
    }
}

impl From<usize> for SourceOffset {
    fn from(value: usize) -> Self {
        Self(value)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SourceSpan {
    offset: SourceOffset,
    len: usize,
}

impl SourceSpan {
    pub fn new(offset: impl Into<SourceOffset>, len: usize) -> Self {
        Self {
            offset: offset.into(),
            len,
        }
    }

    pub fn offset(&self) -> usize {
        self.offset.offset()
    }

    pub fn len(&self) -> usize {
        self.len
    }

    pub fn is_empty(&self) -> bool {
        self.len == 0
    }
}

impl From<(usize, usize)> for SourceSpan {
    fn from((offset, len): (usize, usize)) -> Self {
        Self::new(SourceOffset::from(offset), len)
    }
}

impl From<(SourceOffset, usize)> for SourceSpan {
    fn from((offset, len): (SourceOffset, usize)) -> Self {
        Self::new(offset, len)
    }
}

impl From<Range<usize>> for SourceSpan {
    fn from(range: Range<usize>) -> Self {
        Self::new(
            SourceOffset::from(range.start),
            range.end.saturating_sub(range.start),
        )
    }
}

impl From<RangeInclusive<usize>> for SourceSpan {
    fn from(range: RangeInclusive<usize>) -> Self {
        let start = *range.start();
        let end = *range.end();
        let len = end
            .checked_sub(start)
            .and_then(|v| v.checked_add(1))
            .expect("inclusive source span length overflowed");
        Self::new(SourceOffset::from(start), len)
    }
}

impl From<SourceOffset> for SourceSpan {
    fn from(offset: SourceOffset) -> Self {
        Self::new(offset, 0)
    }
}

impl From<usize> for SourceSpan {
    fn from(offset: usize) -> Self {
        Self::new(SourceOffset::from(offset), 0)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct LabeledSpan {
    label: Option<String>,
    span: SourceSpan,
    primary: bool,
}

impl LabeledSpan {
    pub fn new(label: Option<String>, offset: usize, len: usize) -> Self {
        Self {
            label,
            span: SourceSpan::new(SourceOffset::from(offset), len),
            primary: false,
        }
    }

    pub fn new_with_span(label: Option<String>, span: impl Into<SourceSpan>) -> Self {
        Self {
            label,
            span: span.into(),
            primary: false,
        }
    }

    pub fn new_primary_with_span(label: Option<String>, span: impl Into<SourceSpan>) -> Self {
        Self {
            label,
            span: span.into(),
            primary: true,
        }
    }

    pub fn at(span: impl Into<SourceSpan>, label: impl Into<String>) -> Self {
        Self::new_with_span(Some(label.into()), span)
    }

    pub fn at_offset(offset: usize, label: impl Into<String>) -> Self {
        Self::new_with_span(Some(label.into()), offset)
    }

    pub fn underline(span: impl Into<SourceSpan>) -> Self {
        Self::new_with_span(None, span)
    }

    pub fn set_label(&mut self, label: Option<String>) {
        self.label = label;
    }

    pub fn label(&self) -> Option<&str> {
        self.label.as_deref()
    }

    pub fn inner(&self) -> &SourceSpan {
        &self.span
    }

    pub fn offset(&self) -> usize {
        self.span.offset()
    }

    pub fn len(&self) -> usize {
        self.span.len()
    }

    pub fn is_empty(&self) -> bool {
        self.span.is_empty()
    }

    pub fn primary(&self) -> bool {
        self.primary
    }
}

impl From<SourceSpan> for LabeledSpan {
    fn from(value: SourceSpan) -> Self {
        Self::underline(value)
    }
}

impl From<(usize, usize)> for LabeledSpan {
    fn from(value: (usize, usize)) -> Self {
        Self::underline(SourceSpan::from(value))
    }
}

impl From<Range<usize>> for LabeledSpan {
    fn from(value: Range<usize>) -> Self {
        Self::underline(SourceSpan::from(value))
    }
}

pub trait SpanContents<'a>: fmt::Debug + Send + Sync {
    fn data(&self) -> &'a [u8];
    fn span(&self) -> &SourceSpan;
    fn name(&self) -> Option<&str>;
    fn line(&self) -> usize;
    fn column(&self) -> usize;
    fn line_count(&self) -> usize;
    fn language(&self) -> Option<&str>;
}

pub trait SourceCode: Send + Sync {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError>;
}

#[derive(Debug)]
pub struct MietteSpanContents<'a> {
    data: &'a [u8],
    span: SourceSpan,
    name: Option<String>,
    line: usize,
    column: usize,
    line_count: usize,
    language: Option<String>,
}

impl<'a> MietteSpanContents<'a> {
    pub fn new(
        data: &'a [u8],
        span: SourceSpan,
        line: usize,
        column: usize,
        line_count: usize,
    ) -> Self {
        Self {
            data,
            span,
            name: None,
            line,
            column,
            line_count,
            language: None,
        }
    }

    pub fn new_named(
        name: String,
        data: &'a [u8],
        span: SourceSpan,
        line: usize,
        column: usize,
        line_count: usize,
    ) -> Self {
        Self {
            data,
            span,
            name: Some(name),
            line,
            column,
            line_count,
            language: None,
        }
    }

    pub fn with_language(mut self, language: impl Into<String>) -> Self {
        self.language = Some(language.into());
        self
    }
}

impl<'a> SpanContents<'a> for MietteSpanContents<'a> {
    fn data(&self) -> &'a [u8] {
        self.data
    }

    fn span(&self) -> &SourceSpan {
        &self.span
    }

    fn name(&self) -> Option<&str> {
        self.name.as_deref()
    }

    fn line(&self) -> usize {
        self.line
    }

    fn column(&self) -> usize {
        self.column
    }

    fn line_count(&self) -> usize {
        self.line_count
    }

    fn language(&self) -> Option<&str> {
        self.language.as_deref()
    }
}

#[derive(Clone, Debug)]
pub struct NamedSource<S> {
    name: String,
    inner: S,
    language: Option<String>,
}

impl<S: SourceCode + 'static> NamedSource<S> {
    pub fn new(name: impl Into<String>, inner: S) -> Self {
        Self {
            name: name.into(),
            inner,
            language: None,
        }
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn inner(&self) -> &S {
        &self.inner
    }

    pub fn with_language(mut self, language: impl Into<String>) -> Self {
        self.language = Some(language.into());
        self
    }
}

impl<S: SourceCode + 'static> SourceCode for NamedSource<S> {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        let contents = self
            .inner
            .read_span(span, context_lines_before, context_lines_after)?;
        let mut named = MietteSpanContents::new_named(
            self.name.clone(),
            contents.data(),
            *contents.span(),
            contents.line(),
            contents.column(),
            contents.line_count(),
        );
        if let Some(language) = &self.language {
            named = named.with_language(language.clone());
        } else if let Some(language) = contents.language() {
            named = named.with_language(language.to_string());
        }
        Ok(Box::new(named))
    }
}

impl SourceCode for str {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        read_bytes(
            self.as_bytes(),
            span,
            context_lines_before,
            context_lines_after,
            None,
            None,
        )
    }
}

impl SourceCode for String {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        self.as_str()
            .read_span(span, context_lines_before, context_lines_after)
    }
}

impl SourceCode for [u8] {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        read_bytes(
            self,
            span,
            context_lines_before,
            context_lines_after,
            None,
            None,
        )
    }
}

impl SourceCode for Vec<u8> {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        self.as_slice()
            .read_span(span, context_lines_before, context_lines_after)
    }
}

impl<'s> SourceCode for &'s str {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        (*self).read_span(span, context_lines_before, context_lines_after)
    }
}

impl<'s> SourceCode for &'s [u8] {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        (*self).read_span(span, context_lines_before, context_lines_after)
    }
}

impl<T: SourceCode + ?Sized> SourceCode for Arc<T> {
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        (**self).read_span(span, context_lines_before, context_lines_after)
    }
}

impl<'c, T> SourceCode for Cow<'c, T>
where
    T: SourceCode + ToOwned + ?Sized,
    <T as ToOwned>::Owned: SourceCode + Send + Sync,
{
    fn read_span<'a>(
        &'a self,
        span: &SourceSpan,
        context_lines_before: usize,
        context_lines_after: usize,
    ) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
        self.as_ref()
            .read_span(span, context_lines_before, context_lines_after)
    }
}

fn read_bytes<'a>(
    bytes: &'a [u8],
    span: &SourceSpan,
    context_lines_before: usize,
    context_lines_after: usize,
    name: Option<String>,
    language: Option<String>,
) -> Result<Box<dyn SpanContents<'a> + 'a>, MietteError> {
    let offset = span.offset();
    let end = offset
        .checked_add(span.len())
        .ok_or(MietteError::OutOfBounds)?;
    if offset > bytes.len() || end > bytes.len() {
        return Err(MietteError::OutOfBounds);
    }

    let starts = line_starts(bytes);
    let start_line = line_of_offset(&starts, offset);
    let mut end_line = line_of_offset(&starts, end);
    if span.len() > 0 && end > 0 && starts.binary_search(&end).is_ok() && end_line > 0 {
        end_line -= 1;
    }

    let (slice_start, slice_end, line, column, line_count) =
        if context_lines_before > 0 || context_lines_after > 0 {
            let ctx_start_line = start_line.saturating_sub(context_lines_before);
            let ctx_end_line = cmp::min(
                starts.len().saturating_sub(1),
                end_line + context_lines_after,
            );
            let slice_start = starts[ctx_start_line];
            let slice_end = if ctx_end_line + 1 < starts.len() {
                starts[ctx_end_line + 1]
            } else {
                bytes.len()
            };
            (
                slice_start,
                slice_end,
                ctx_start_line,
                0usize,
                ctx_end_line.saturating_sub(ctx_start_line) + 1,
            )
        } else {
            let (_, column) = byte_line_column(bytes, offset);
            (
                offset,
                end,
                start_line,
                column,
                end_line.saturating_sub(start_line) + 1,
            )
        };

    let mut contents = MietteSpanContents::new(
        &bytes[slice_start..slice_end],
        SourceSpan::new(SourceOffset::from(slice_start), slice_end - slice_start),
        line,
        column,
        line_count,
    );
    contents.name = name;
    contents.language = language;
    Ok(Box::new(contents))
}

fn line_starts(bytes: &[u8]) -> Vec<usize> {
    let mut starts = vec![0usize];
    let mut i = 0usize;
    while i < bytes.len() {
        match bytes[i] {
            b'\r' if i + 1 < bytes.len() && bytes[i + 1] == b'\n' => {
                i += 2;
                if i <= bytes.len() {
                    starts.push(i);
                }
            }
            b'\n' | b'\r' => {
                i += 1;
                if i <= bytes.len() {
                    starts.push(i);
                }
            }
            _ => i += 1,
        }
    }
    if *starts.last().unwrap() == bytes.len() && bytes.len() > 0 {
        starts.pop();
    }
    starts
}

fn line_of_offset(starts: &[usize], offset: usize) -> usize {
    match starts.binary_search(&offset) {
        Ok(idx) => idx,
        Err(idx) => idx.saturating_sub(1),
    }
}

fn byte_line_column(bytes: &[u8], offset: usize) -> (usize, usize) {
    let mut line = 0usize;
    let mut col = 0usize;
    let mut i = 0usize;
    while i < offset && i < bytes.len() {
        match bytes[i] {
            b'\r' if i + 1 < bytes.len() && bytes[i + 1] == b'\n' => {
                line += 1;
                col = 0;
                i += 2;
            }
            b'\n' | b'\r' => {
                line += 1;
                col = 0;
                i += 1;
            }
            _ => {
                col += 1;
                i += 1;
            }
        }
    }
    (line, col)
}

#[derive(Debug)]
pub enum MietteError {
    IoError(std::io::Error),
    OutOfBounds,
}

impl fmt::Display for MietteError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::IoError(err) => fmt::Display::fmt(err, f),
            Self::OutOfBounds => write!(f, "Source span is out of bounds"),
        }
    }
}

impl StdError for MietteError {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        match self {
            Self::IoError(err) => Some(err),
            Self::OutOfBounds => None,
        }
    }
}

impl Diagnostic for MietteError {
    fn code<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        match self {
            Self::IoError(_) => Some(Box::new("miette::io_error")),
            Self::OutOfBounds => Some(Box::new("miette::span_out_of_bounds")),
        }
    }

    fn help<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        match self {
            Self::IoError(_) => None,
            Self::OutOfBounds => Some(Box::new(
                "Check that source spans use valid byte offsets and are not off by one.",
            )),
        }
    }

    fn url<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        match self {
            Self::IoError(_) => Some(Box::new(
                "https://docs.rs/miette/latest/miette/enum.MietteError.html#variant.IoError",
            )),
            Self::OutOfBounds => Some(Box::new(
                "https://docs.rs/miette/latest/miette/enum.MietteError.html#variant.OutOfBounds",
            )),
        }
    }
}

impl From<std::io::Error> for MietteError {
    fn from(value: std::io::Error) -> Self {
        Self::IoError(value)
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MietteDiagnostic {
    pub message: String,
    pub code: Option<String>,
    pub severity: Option<Severity>,
    pub help: Option<String>,
    pub url: Option<String>,
    pub labels: Option<Vec<LabeledSpan>>,
}

impl MietteDiagnostic {
    pub fn new(message: impl fmt::Display) -> Self {
        Self {
            message: message.to_string(),
            code: None,
            severity: None,
            help: None,
            url: None,
            labels: None,
        }
    }

    pub fn with_code(mut self, code: impl fmt::Display) -> Self {
        self.code = Some(code.to_string());
        self
    }

    pub fn with_severity(mut self, severity: Severity) -> Self {
        self.severity = Some(severity);
        self
    }

    pub fn with_help(mut self, help: impl fmt::Display) -> Self {
        self.help = Some(help.to_string());
        self
    }

    pub fn with_url(mut self, url: impl fmt::Display) -> Self {
        self.url = Some(url.to_string());
        self
    }

    pub fn with_label(mut self, label: LabeledSpan) -> Self {
        self.labels = Some(vec![label]);
        self
    }

    pub fn with_labels<I>(mut self, labels: I) -> Self
    where
        I: IntoIterator<Item = LabeledSpan>,
    {
        self.labels = Some(labels.into_iter().collect());
        self
    }

    pub fn and_label(mut self, label: LabeledSpan) -> Self {
        self.labels.get_or_insert_with(Vec::new).push(label);
        self
    }

    pub fn and_labels<I>(mut self, labels: I) -> Self
    where
        I: IntoIterator<Item = LabeledSpan>,
    {
        self.labels.get_or_insert_with(Vec::new).extend(labels);
        self
    }
}

impl fmt::Display for MietteDiagnostic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}

impl StdError for MietteDiagnostic {}

impl Diagnostic for MietteDiagnostic {
    fn code<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.code
            .as_ref()
            .map(|value| Box::new(value.as_str()) as Box<dyn fmt::Display + 'a>)
    }

    fn severity(&self) -> Option<Severity> {
        self.severity
    }

    fn help<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.help
            .as_ref()
            .map(|value| Box::new(value.as_str()) as Box<dyn fmt::Display + 'a>)
    }

    fn url<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.url
            .as_ref()
            .map(|value| Box::new(value.as_str()) as Box<dyn fmt::Display + 'a>)
    }

    fn labels(&self) -> Option<Box<dyn Iterator<Item = LabeledSpan> + '_>> {
        self.labels.as_ref().map(|labels| {
            Box::new(labels.clone().into_iter()) as Box<dyn Iterator<Item = LabeledSpan> + '_>
        })
    }
}

#[derive(Clone)]
struct AnonymousDiagnostic(String);

impl fmt::Display for AnonymousDiagnostic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl fmt::Debug for AnonymousDiagnostic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl StdError for AnonymousDiagnostic {}
impl Diagnostic for AnonymousDiagnostic {}

impl From<String> for Box<dyn Diagnostic + Send + Sync> {
    fn from(value: String) -> Self {
        Box::new(AnonymousDiagnostic(value))
    }
}

impl From<&str> for Box<dyn Diagnostic + Send + Sync> {
    fn from(value: &str) -> Self {
        Box::new(AnonymousDiagnostic(value.to_string()))
    }
}

impl From<String> for Box<dyn Diagnostic> {
    fn from(value: String) -> Self {
        Box::new(AnonymousDiagnostic(value))
    }
}

impl From<&str> for Box<dyn Diagnostic> {
    fn from(value: &str) -> Self {
        Box::new(AnonymousDiagnostic(value.to_string()))
    }
}

#[derive(Debug)]
struct ErrorDiagnostic<E> {
    error: E,
}

impl<E: fmt::Display> fmt::Display for ErrorDiagnostic<E> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.error, f)
    }
}

impl<E: StdError + 'static> StdError for ErrorDiagnostic<E> {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        self.error.source()
    }
}

impl<E: StdError + Send + Sync + 'static> Diagnostic for ErrorDiagnostic<E> {}

#[derive(Debug)]
struct MessageDiagnostic<C> {
    context: C,
}

impl<C: fmt::Display> fmt::Display for MessageDiagnostic<C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.context, f)
    }
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> StdError for MessageDiagnostic<C> {}
impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> Diagnostic for MessageDiagnostic<C> {}

#[derive(Debug)]
struct ContextDiagnostic<C> {
    context: C,
    source: Report,
}

impl<C: fmt::Display> fmt::Display for ContextDiagnostic<C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.context, f)
    }
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> StdError for ContextDiagnostic<C> {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        Some(&self.source)
    }
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> Diagnostic for ContextDiagnostic<C> {}

trait ReportFrame: fmt::Debug + fmt::Display + StdError + Send + Sync + 'static {
    fn as_diagnostic(&self) -> &dyn Diagnostic;
    fn value_any(&self) -> &dyn Any;
    fn value_any_mut(&mut self) -> &mut dyn Any;
    fn into_value_any(self: Box<Self>) -> Box<dyn Any + Send + Sync>;
    fn source_report_mut(&mut self) -> Option<&mut Report> {
        None
    }
    fn into_source_report(self: Box<Self>) -> Option<Report>;
}

#[derive(Debug)]
struct DiagnosticFrame<D> {
    diagnostic: D,
}

impl<D: Diagnostic + Send + Sync + 'static> fmt::Display for DiagnosticFrame<D> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.diagnostic, f)
    }
}

impl<D: Diagnostic + Send + Sync + 'static> StdError for DiagnosticFrame<D> {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        self.diagnostic.source()
    }
}

impl<D: Diagnostic + Send + Sync + 'static> ReportFrame for DiagnosticFrame<D> {
    fn as_diagnostic(&self) -> &dyn Diagnostic {
        &self.diagnostic
    }

    fn value_any(&self) -> &dyn Any {
        &self.diagnostic
    }

    fn value_any_mut(&mut self) -> &mut dyn Any {
        &mut self.diagnostic
    }

    fn into_value_any(self: Box<Self>) -> Box<dyn Any + Send + Sync> {
        Box::new(self.diagnostic)
    }

    fn into_source_report(self: Box<Self>) -> Option<Report> {
        None
    }
}

impl<D: Diagnostic + Send + Sync + 'static> Diagnostic for DiagnosticFrame<D> {
    fn code<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.diagnostic.code()
    }

    fn severity(&self) -> Option<Severity> {
        self.diagnostic.severity()
    }

    fn help<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.diagnostic.help()
    }

    fn url<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.diagnostic.url()
    }

    fn source_code(&self) -> Option<&dyn SourceCode> {
        self.diagnostic.source_code()
    }

    fn labels(&self) -> Option<Box<dyn Iterator<Item = LabeledSpan> + '_>> {
        self.diagnostic.labels()
    }

    fn related(&self) -> Option<Box<dyn Iterator<Item = &dyn Diagnostic> + '_>> {
        self.diagnostic.related()
    }

    fn diagnostic_source(&self) -> Option<&dyn Diagnostic> {
        self.diagnostic.diagnostic_source()
    }
}

#[derive(Debug)]
struct BoxedDiagnosticFrame {
    diagnostic: Box<dyn Diagnostic + Send + Sync>,
}

impl fmt::Display for BoxedDiagnosticFrame {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&*self.diagnostic, f)
    }
}

impl StdError for BoxedDiagnosticFrame {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        (&*self.diagnostic as &(dyn StdError + 'static)).source()
    }
}

impl Diagnostic for BoxedDiagnosticFrame {
    fn code<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        (&*self.diagnostic).code()
    }

    fn severity(&self) -> Option<Severity> {
        (&*self.diagnostic).severity()
    }

    fn help<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        (&*self.diagnostic).help()
    }

    fn url<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        (&*self.diagnostic).url()
    }

    fn source_code(&self) -> Option<&dyn SourceCode> {
        (&*self.diagnostic).source_code()
    }

    fn labels(&self) -> Option<Box<dyn Iterator<Item = LabeledSpan> + '_>> {
        (&*self.diagnostic).labels()
    }

    fn related(&self) -> Option<Box<dyn Iterator<Item = &dyn Diagnostic> + '_>> {
        (&*self.diagnostic).related()
    }

    fn diagnostic_source(&self) -> Option<&dyn Diagnostic> {
        (&*self.diagnostic).diagnostic_source()
    }
}

impl ReportFrame for BoxedDiagnosticFrame {
    fn as_diagnostic(&self) -> &dyn Diagnostic {
        self
    }

    fn value_any(&self) -> &dyn Any {
        &*self.diagnostic
    }

    fn value_any_mut(&mut self) -> &mut dyn Any {
        &mut *self.diagnostic
    }

    fn into_value_any(self: Box<Self>) -> Box<dyn Any + Send + Sync> {
        self.diagnostic
    }

    fn into_source_report(self: Box<Self>) -> Option<Report> {
        None
    }
}

#[derive(Debug)]
struct ErrorFrame<E> {
    diagnostic: ErrorDiagnostic<E>,
}

impl<E: StdError + Send + Sync + 'static> fmt::Display for ErrorFrame<E> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.diagnostic, f)
    }
}

impl<E: StdError + Send + Sync + 'static> StdError for ErrorFrame<E> {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        self.diagnostic.source()
    }
}

impl<E: StdError + Send + Sync + 'static> Diagnostic for ErrorFrame<E> {}

impl<E: StdError + Send + Sync + 'static> ReportFrame for ErrorFrame<E> {
    fn as_diagnostic(&self) -> &dyn Diagnostic {
        self
    }

    fn value_any(&self) -> &dyn Any {
        &self.diagnostic.error
    }

    fn value_any_mut(&mut self) -> &mut dyn Any {
        &mut self.diagnostic.error
    }

    fn into_value_any(self: Box<Self>) -> Box<dyn Any + Send + Sync> {
        Box::new(self.diagnostic.error)
    }

    fn into_source_report(self: Box<Self>) -> Option<Report> {
        None
    }
}

#[derive(Debug)]
struct MessageFrame<C> {
    diagnostic: MessageDiagnostic<C>,
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> fmt::Display for MessageFrame<C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.diagnostic, f)
    }
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> StdError for MessageFrame<C> {}
impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> Diagnostic for MessageFrame<C> {}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> ReportFrame for MessageFrame<C> {
    fn as_diagnostic(&self) -> &dyn Diagnostic {
        self
    }

    fn value_any(&self) -> &dyn Any {
        &self.diagnostic.context
    }

    fn value_any_mut(&mut self) -> &mut dyn Any {
        &mut self.diagnostic.context
    }

    fn into_value_any(self: Box<Self>) -> Box<dyn Any + Send + Sync> {
        Box::new(self.diagnostic.context)
    }

    fn into_source_report(self: Box<Self>) -> Option<Report> {
        None
    }
}

#[derive(Debug)]
struct ContextFrame<C> {
    diagnostic: ContextDiagnostic<C>,
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> fmt::Display for ContextFrame<C> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.diagnostic, f)
    }
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> StdError for ContextFrame<C> {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        self.diagnostic.source()
    }
}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> Diagnostic for ContextFrame<C> {}

impl<C: fmt::Debug + fmt::Display + Send + Sync + 'static> ReportFrame for ContextFrame<C> {
    fn as_diagnostic(&self) -> &dyn Diagnostic {
        self
    }

    fn value_any(&self) -> &dyn Any {
        &self.diagnostic.context
    }

    fn value_any_mut(&mut self) -> &mut dyn Any {
        &mut self.diagnostic.context
    }

    fn into_value_any(self: Box<Self>) -> Box<dyn Any + Send + Sync> {
        Box::new(self.diagnostic.context)
    }

    fn source_report_mut(&mut self) -> Option<&mut Report> {
        Some(&mut self.diagnostic.source)
    }

    fn into_source_report(self: Box<Self>) -> Option<Report> {
        Some(self.diagnostic.source)
    }
}

struct SourceOverrideFrame {
    inner: Box<dyn ReportFrame>,
    source_code: Arc<dyn SourceCode>,
}

impl fmt::Debug for SourceOverrideFrame {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SourceOverrideFrame")
            .field("inner", &self.inner)
            .field("source_code", &"<source>")
            .finish()
    }
}

impl fmt::Display for SourceOverrideFrame {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(&self.inner, f)
    }
}

impl StdError for SourceOverrideFrame {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        self.inner.source()
    }
}

impl Diagnostic for SourceOverrideFrame {
    fn code<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.inner.as_diagnostic().code()
    }

    fn severity(&self) -> Option<Severity> {
        self.inner.as_diagnostic().severity()
    }

    fn help<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.inner.as_diagnostic().help()
    }

    fn url<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
        self.inner.as_diagnostic().url()
    }

    fn source_code(&self) -> Option<&dyn SourceCode> {
        Some(self.source_code.as_ref())
    }

    fn labels(&self) -> Option<Box<dyn Iterator<Item = LabeledSpan> + '_>> {
        self.inner.as_diagnostic().labels()
    }

    fn related(&self) -> Option<Box<dyn Iterator<Item = &dyn Diagnostic> + '_>> {
        self.inner.as_diagnostic().related()
    }

    fn diagnostic_source(&self) -> Option<&dyn Diagnostic> {
        self.inner.as_diagnostic().diagnostic_source()
    }
}

impl ReportFrame for SourceOverrideFrame {
    fn as_diagnostic(&self) -> &dyn Diagnostic {
        self
    }

    fn value_any(&self) -> &dyn Any {
        self.inner.value_any()
    }

    fn value_any_mut(&mut self) -> &mut dyn Any {
        self.inner.value_any_mut()
    }

    fn into_value_any(self: Box<Self>) -> Box<dyn Any + Send + Sync> {
        self.inner.into_value_any()
    }

    fn source_report_mut(&mut self) -> Option<&mut Report> {
        self.inner.source_report_mut()
    }

    fn into_source_report(self: Box<Self>) -> Option<Report> {
        self.inner.into_source_report()
    }
}

static HOOK: OnceLock<ErrorHook> = OnceLock::new();

#[derive(Debug)]
pub struct InstallError {
    _private: (),
}

impl fmt::Display for InstallError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("a miette report hook has already been installed")
    }
}

impl StdError for InstallError {}

pub fn set_hook(hook: ErrorHook) -> core::result::Result<(), InstallError> {
    HOOK.set(hook).map_err(|_| InstallError { _private: () })
}

pub struct Report {
    frame: Box<dyn ReportFrame>,
    handler: Box<dyn ReportHandler>,
}

impl Report {
    pub fn new<D>(diagnostic: D) -> Self
    where
        D: Diagnostic + Send + Sync + 'static,
    {
        let frame: Box<dyn ReportFrame> = Box::new(DiagnosticFrame { diagnostic });
        Self::from_frame(frame)
    }

    pub fn msg(message: impl fmt::Display) -> Self {
        Self::new(MietteDiagnostic::new(message))
    }

    fn from_context<C>(context: C) -> Self
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
    {
        let frame: Box<dyn ReportFrame> = Box::new(MessageFrame {
            diagnostic: MessageDiagnostic { context },
        });
        Self::from_frame(frame)
    }

    pub fn new_boxed(diagnostic: Box<dyn Diagnostic + Send + Sync>) -> Self {
        let frame: Box<dyn ReportFrame> = Box::new(BoxedDiagnosticFrame { diagnostic });
        Self::from_frame(frame)
    }

    pub fn from_err<E>(error: E) -> Self
    where
        E: StdError + Send + Sync + 'static,
    {
        let boxed: Box<dyn Any + Send + Sync> = Box::new(error);
        match boxed.downcast::<Report>() {
            Ok(report) => *report,
            Err(boxed) => {
                let error = *boxed.downcast::<E>().ok().expect("type was just boxed");
                let frame: Box<dyn ReportFrame> = Box::new(ErrorFrame {
                    diagnostic: ErrorDiagnostic { error },
                });
                Self::from_frame(frame)
            }
        }
    }

    fn from_frame(frame: Box<dyn ReportFrame>) -> Self {
        let handler = if let Some(hook) = HOOK.get() {
            hook(frame.as_diagnostic())
        } else {
            default_handler()
        };
        Self { frame, handler }
    }

    pub fn wrap_err<C>(self, context: C) -> Self
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
    {
        let frame: Box<dyn ReportFrame> = Box::new(ContextFrame {
            diagnostic: ContextDiagnostic {
                context,
                source: self,
            },
        });
        Self::from_frame(frame)
    }

    pub fn with_source_code<S>(mut self, source_code: S) -> Self
    where
        S: SourceCode + 'static,
    {
        self.frame = Box::new(SourceOverrideFrame {
            inner: self.frame,
            source_code: Arc::new(source_code),
        });
        self
    }

    pub fn is<T: Any + Send + Sync + 'static>(&self) -> bool {
        self.find_value::<T>().is_some()
    }

    pub fn downcast_ref<T: Any + Send + Sync + 'static>(&self) -> Option<&T> {
        self.find_value::<T>()
    }

    pub fn downcast_mut<T: Any + Send + Sync + 'static>(&mut self) -> Option<&mut T> {
        if self.frame.value_any().is::<T>() {
            return self.frame.value_any_mut().downcast_mut::<T>();
        }
        if self.frame.value_any().is::<Report>() {
            let report = self
                .frame
                .value_any_mut()
                .downcast_mut::<Report>()
                .expect("type checked before downcast");
            return report.downcast_mut::<T>();
        }
        if let Some(report) = self.frame.source_report_mut() {
            if let Some(value) = report.downcast_mut::<T>() {
                return Some(value);
            }
        }
        None
    }

    pub fn downcast<T: Any + Send + Sync + 'static>(self) -> core::result::Result<T, Self> {
        if !self.is::<T>() {
            return Err(self);
        }
        Ok(self.into_downcast::<T>())
    }

    fn into_downcast<T: Any + Send + Sync + 'static>(self) -> T {
        if self.frame.value_any().is::<T>() {
            return *self
                .frame
                .into_value_any()
                .downcast::<T>()
                .ok()
                .expect("type checked before downcast");
        }
        if self.frame.value_any().is::<Report>() {
            let report = *self
                .frame
                .into_value_any()
                .downcast::<Report>()
                .ok()
                .expect("type checked before downcast");
            return report.into_downcast::<T>();
        }
        if let Some(source) = self.frame.into_source_report() {
            return source.into_downcast::<T>();
        }
        unreachable!("downcast pre-check found a value");
    }

    fn find_value<T: Any + Send + Sync + 'static>(&self) -> Option<&T> {
        if let Some(value) = self.frame.value_any().downcast_ref::<T>() {
            return Some(value);
        }
        if let Some(report) = self.frame.value_any().downcast_ref::<Report>() {
            if let Some(value) = report.downcast_ref::<T>() {
                return Some(value);
            }
        }
        let mut next = self.frame.source();
        while let Some(error) = next {
            if let Some(report) = error.downcast_ref::<Report>() {
                if let Some(value) = report.downcast_ref::<T>() {
                    return Some(value);
                }
            }
            next = error.source();
        }
        None
    }

    pub fn chain(&self) -> Chain<'_> {
        Chain { next: Some(self) }
    }

    pub fn root_cause(&self) -> &(dyn StdError + 'static) {
        let mut last: &(dyn StdError + 'static) = self;
        let mut next = self.source();
        while let Some(error) = next {
            last = error;
            next = error.source();
        }
        last
    }
}

impl Deref for Report {
    type Target = dyn Diagnostic;

    fn deref(&self) -> &Self::Target {
        self.frame.as_diagnostic()
    }
}

impl fmt::Display for Report {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.handler.display(self.frame.as_diagnostic(), f)
    }
}

impl fmt::Debug for Report {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.handler.debug(self.frame.as_diagnostic(), f)
    }
}

impl StdError for Report {
    fn source(&self) -> Option<&(dyn StdError + 'static)> {
        self.frame.source()
    }
}

impl<D> From<D> for Report
where
    D: Diagnostic + Send + Sync + 'static,
{
    fn from(value: D) -> Self {
        Self::new(value)
    }
}

impl From<Box<dyn Diagnostic + Send + Sync>> for Report {
    fn from(value: Box<dyn Diagnostic + Send + Sync>) -> Self {
        Self::new_boxed(value)
    }
}

pub struct Chain<'a> {
    next: Option<&'a (dyn StdError + 'static)>,
}

impl<'a> Iterator for Chain<'a> {
    type Item = &'a (dyn StdError + 'static);

    fn next(&mut self) -> Option<Self::Item> {
        let current = self.next?;
        self.next = current.source();
        Some(current)
    }
}

pub trait IntoDiagnostic<T> {
    fn into_diagnostic(self) -> Result<T>;
}

impl<T, E> IntoDiagnostic<T> for core::result::Result<T, E>
where
    E: StdError + Send + Sync + 'static,
{
    fn into_diagnostic(self) -> Result<T> {
        self.map_err(Report::from_err)
    }
}

pub trait WrapErr<T>: Sized {
    fn wrap_err<C>(self, context: C) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static;

    fn wrap_err_with<C, F>(self, context: F) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
        F: FnOnce() -> C;

    fn context<C>(self, context: C) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
    {
        self.wrap_err(context)
    }

    fn with_context<C, F>(self, context: F) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
        F: FnOnce() -> C,
    {
        self.wrap_err_with(context)
    }
}

pub use WrapErr as Context;

pub trait WrapErrMarker {}
impl<T> WrapErrMarker for T {}

impl<T> WrapErr<T> for Option<T> {
    fn wrap_err<C>(self, context: C) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
    {
        self.ok_or_else(|| Report::from_context(context))
    }

    fn wrap_err_with<C, F>(self, context: F) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
        F: FnOnce() -> C,
    {
        self.ok_or_else(|| Report::from_context(context()))
    }
}

impl<T, E> WrapErr<T> for core::result::Result<T, E>
where
    E: StdError + Send + Sync + 'static,
{
    fn wrap_err<C>(self, context: C) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
    {
        self.map_err(|error| Report::from_err(error).wrap_err(context))
    }

    fn wrap_err_with<C, F>(self, context: F) -> Result<T>
    where
        C: fmt::Debug + fmt::Display + Send + Sync + 'static,
        F: FnOnce() -> C,
    {
        self.map_err(|error| Report::from_err(error).wrap_err(context()))
    }
}

pub trait ReportHandler: Any + Send + Sync {
    fn debug(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result;

    fn display(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{diagnostic}")?;
        if f.alternate() {
            let mut next = diagnostic.source();
            while let Some(source) = next {
                write!(f, ": {source}")?;
                next = source.source();
            }
        }
        Ok(())
    }

    fn track_caller(&mut self, _location: &'static Location<'static>) {}
}

impl dyn ReportHandler {
    pub fn is<T: ReportHandler + 'static>(&self) -> bool {
        (self as &dyn Any).is::<T>()
    }

    pub fn downcast_ref<T: ReportHandler + 'static>(&self) -> Option<&T> {
        (self as &dyn Any).downcast_ref::<T>()
    }

    pub fn downcast_mut<T: ReportHandler + 'static>(&mut self) -> Option<&mut T> {
        (self as &mut dyn Any).downcast_mut::<T>()
    }
}

#[derive(Clone, Debug, Default)]
pub struct DebugReportHandler;

impl DebugReportHandler {
    pub fn new() -> Self {
        Self
    }

    pub fn render_report(
        &self,
        f: &mut fmt::Formatter<'_>,
        diagnostic: &dyn Diagnostic,
    ) -> fmt::Result {
        render_debug_to_formatter(f, diagnostic)
    }
}

impl ReportHandler for DebugReportHandler {
    fn debug(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.render_report(f, diagnostic)
    }
}

fn render_debug_to_formatter(
    f: &mut fmt::Formatter<'_>,
    diagnostic: &dyn Diagnostic,
) -> fmt::Result {
    write!(f, "{diagnostic}")?;
    let causes = collect_causes(diagnostic);
    if !causes.is_empty() {
        write!(f, "\n\nCaused by:")?;
        for (idx, cause) in causes.iter().enumerate() {
            write!(f, "\n    {}: {}", idx, cause)?;
        }
    }
    if let Some(code) = diagnostic.code() {
        write!(f, "\n\n  code: {code}")?;
    }
    write!(
        f,
        "\n  severity: {:?}",
        diagnostic.severity().unwrap_or_default()
    )?;
    if let Some(help) = diagnostic.help() {
        write!(f, "\n  help: {help}")?;
    }
    if let Some(url) = diagnostic.url() {
        write!(f, "\n  url: {url}")?;
    }
    if let Some(labels) = diagnostic.labels() {
        let labels: Vec<_> = labels.collect();
        if !labels.is_empty() {
            write!(f, "\n  labels: {:?}", labels)?;
        }
    }
    if diagnostic.source_code().is_some() {
        write!(f, "\n  source: available")?;
    }
    if let Some(related) = diagnostic.related() {
        let related: Vec<String> = related.map(|d| d.to_string()).collect();
        if !related.is_empty() {
            write!(f, "\n  related: {:?}", related)?;
        }
    }
    if let Some(source) = diagnostic.diagnostic_source() {
        write!(f, "\n  diagnostic_source: {source}")?;
    }
    Ok(())
}

#[derive(Clone, Debug, Default)]
pub struct JSONReportHandler;

impl JSONReportHandler {
    pub fn new() -> Self {
        Self
    }

    pub fn render_report<W: fmt::Write>(
        &self,
        f: &mut W,
        diagnostic: &dyn Diagnostic,
    ) -> fmt::Result {
        render_json(f, diagnostic, None)
    }
}

impl ReportHandler for JSONReportHandler {
    fn debug(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut out = String::new();
        self.render_report(&mut out, diagnostic)?;
        f.write_str(&out)
    }

    fn display(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.debug(diagnostic, f)
    }
}

fn render_json<W: fmt::Write>(
    f: &mut W,
    diagnostic: &dyn Diagnostic,
    inherited_source: Option<&dyn SourceCode>,
) -> fmt::Result {
    let source = diagnostic.source_code().or(inherited_source);
    write!(f, "{{")?;
    write_json_field(f, "message", &diagnostic.to_string(), false)?;
    write!(
        f,
        ",\"severity\":\"{}\"",
        severity_text(diagnostic.severity())
    )?;

    if let Some(code) = diagnostic.code() {
        write!(f, ",\"code\":\"{}\"", json_escape(&code.to_string()))?;
    }
    if let Some(url) = diagnostic.url() {
        write!(f, ",\"url\":\"{}\"", json_escape(&url.to_string()))?;
    }
    if let Some(help) = diagnostic.help() {
        write!(f, ",\"help\":\"{}\"", json_escape(&help.to_string()))?;
    }

    let labels = diagnostic
        .labels()
        .map(|labels| labels.collect::<Vec<_>>())
        .unwrap_or_default();
    if source.is_some() {
        let filename = labels
            .first()
            .and_then(|label| source.and_then(|src| src.read_span(label.inner(), 0, 0).ok()))
            .and_then(|contents| contents.name().map(ToString::to_string))
            .unwrap_or_default();
        write!(f, ",\"filename\":\"{}\"", json_escape(&filename))?;
    }

    write!(f, ",\"causes\":[")?;
    let causes = collect_diagnostic_causes(diagnostic);
    for (idx, cause) in causes.iter().enumerate() {
        if idx > 0 {
            write!(f, ",")?;
        }
        write!(f, "\"{}\"", json_escape(cause))?;
    }
    write!(f, "]")?;

    write!(f, ",\"labels\":[")?;
    for (idx, label) in labels.iter().enumerate() {
        if idx > 0 {
            write!(f, ",")?;
        }
        write!(f, "{{")?;
        if let Some(text) = label.label() {
            write!(f, "\"label\":\"{}\",", json_escape(text))?;
        }
        write!(
            f,
            "\"span\":{{\"offset\":{},\"length\":{}}}",
            label.offset(),
            label.len()
        )?;
        write!(f, "}}")?;
    }
    write!(f, "]")?;

    write!(f, ",\"related\":[")?;
    if let Some(related) = diagnostic.related() {
        for (idx, rel) in related.enumerate() {
            if idx > 0 {
                write!(f, ",")?;
            }
            render_json(f, rel, source)?;
        }
    }
    write!(f, "]")?;

    write!(f, "}}")
}

fn write_json_field<W: fmt::Write>(
    f: &mut W,
    name: &str,
    value: &str,
    needs_comma: bool,
) -> fmt::Result {
    if needs_comma {
        write!(f, ",")?;
    }
    write!(f, "\"{name}\":\"{}\"", json_escape(value))
}

fn json_escape(input: &str) -> String {
    let mut out = String::with_capacity(input.len());
    for ch in input.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\t' => out.push_str("\\t"),
            '\r' => out.push_str("\\r"),
            '\n' => out.push_str("\\n"),
            '\x08' => out.push_str("\\b"),
            '\x0c' => out.push_str("\\f"),
            c => out.push(c),
        }
    }
    out
}

fn severity_text(severity: Option<Severity>) -> &'static str {
    match severity.unwrap_or_default() {
        Severity::Error => "error",
        Severity::Warning => "warning",
        Severity::Advice => "advice",
    }
}

fn collect_causes(error: &(dyn StdError + 'static)) -> Vec<String> {
    let mut out = Vec::new();
    let mut next = error.source();
    while let Some(source) = next {
        out.push(source.to_string());
        next = source.source();
    }
    out
}

fn collect_diagnostic_causes(diagnostic: &dyn Diagnostic) -> Vec<String> {
    if let Some(source) = diagnostic.diagnostic_source() {
        let mut out = vec![source.to_string()];
        let mut next = source.diagnostic_source();
        while let Some(source) = next {
            out.push(source.to_string());
            next = source.diagnostic_source();
        }
        return out;
    }
    collect_causes(diagnostic)
}

#[derive(Clone, Debug)]
pub struct NarratableReportHandler {
    footer: Option<String>,
    context_lines: usize,
    causes: bool,
    nested_related: bool,
}

impl NarratableReportHandler {
    pub fn new() -> Self {
        Self {
            footer: None,
            context_lines: 0,
            causes: true,
            nested_related: false,
        }
    }

    pub fn with_footer(mut self, footer: impl Into<String>) -> Self {
        self.footer = Some(footer.into());
        self
    }

    pub fn footer(self, footer: impl Into<String>) -> Self {
        self.with_footer(footer)
    }

    pub fn context_lines(mut self, lines: usize) -> Self {
        self.context_lines = lines;
        self
    }

    pub fn with_context_lines(self, lines: usize) -> Self {
        self.context_lines(lines)
    }

    pub fn with_cause_chain(mut self) -> Self {
        self.causes = true;
        self
    }

    pub fn without_cause_chain(mut self) -> Self {
        self.causes = false;
        self
    }

    pub fn show_related_as_nested(mut self) -> Self {
        self.nested_related = true;
        self
    }

    pub fn show_related_as_siblings(mut self) -> Self {
        self.nested_related = false;
        self
    }

    pub fn show_related_errors_as_nested(self) -> Self {
        self.show_related_as_nested()
    }

    pub fn show_related_errors_as_siblings(self) -> Self {
        self.show_related_as_siblings()
    }

    pub fn render_report<W: fmt::Write>(
        &self,
        f: &mut W,
        diagnostic: &dyn Diagnostic,
    ) -> fmt::Result {
        render_text_report(
            f,
            diagnostic,
            TextRenderOptions {
                context_lines: self.context_lines,
                causes: self.causes,
                footer: self.footer.as_deref(),
                graphical: false,
            },
        )
    }
}

impl Default for NarratableReportHandler {
    fn default() -> Self {
        Self::new()
    }
}

impl ReportHandler for NarratableReportHandler {
    fn debug(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut out = String::new();
        self.render_report(&mut out, diagnostic)?;
        f.write_str(&out)
    }
}

#[derive(Clone, Debug)]
pub struct GraphicalReportHandler {
    theme: GraphicalTheme,
    tab_width: usize,
    width: Option<usize>,
    context_lines: usize,
    causes: bool,
    footer: Option<String>,
    _links: bool,
    _show_primary_span_start: bool,
    _show_urls: bool,
    _wrap_lines: bool,
    _break_words: bool,
    _nested_related: bool,
    _syntax_highlighting: bool,
    _link_display_text: Option<String>,
}

impl GraphicalReportHandler {
    pub fn new() -> Self {
        Self::new_themed(GraphicalTheme::default())
    }

    pub fn new_themed(theme: GraphicalTheme) -> Self {
        Self {
            theme,
            tab_width: 4,
            width: None,
            context_lines: 0,
            causes: true,
            footer: None,
            _links: false,
            _show_primary_span_start: false,
            _show_urls: true,
            _wrap_lines: false,
            _break_words: false,
            _nested_related: false,
            _syntax_highlighting: true,
            _link_display_text: None,
        }
    }

    pub fn tab_width(mut self, width: usize) -> Self {
        self.tab_width = width.max(1);
        self
    }

    pub fn with_tab_width(self, width: usize) -> Self {
        self.tab_width(width)
    }

    pub fn with_links(mut self, links: bool) -> Self {
        self._links = links;
        self
    }

    pub fn links(self, links: bool) -> Self {
        self.with_links(links)
    }

    pub fn with_cause_chain(mut self) -> Self {
        self.causes = true;
        self
    }

    pub fn without_cause_chain(mut self) -> Self {
        self.causes = false;
        self
    }

    pub fn with_primary_span_start(mut self, show: bool) -> Self {
        self._show_primary_span_start = show;
        self
    }

    pub fn with_urls(mut self, show: bool) -> Self {
        self._show_urls = show;
        self
    }

    pub fn theme(mut self, theme: GraphicalTheme) -> Self {
        self.theme = theme;
        self
    }

    pub fn width(mut self, width: usize) -> Self {
        self.width = Some(width);
        self
    }

    pub fn with_width(self, width: usize) -> Self {
        self.width(width)
    }

    pub fn wrap_lines(mut self, yes: bool) -> Self {
        self._wrap_lines = yes;
        self
    }

    pub fn break_words(mut self, yes: bool) -> Self {
        self._break_words = yes;
        self
    }

    pub fn word_separator<T>(self, _separator: T) -> Self {
        self
    }

    pub fn word_splitter<T>(self, _splitter: T) -> Self {
        self
    }

    pub fn footer(mut self, footer: impl Into<String>) -> Self {
        self.footer = Some(footer.into());
        self
    }

    pub fn with_footer(self, footer: impl Into<String>) -> Self {
        self.footer(footer)
    }

    pub fn context_lines(mut self, lines: usize) -> Self {
        self.context_lines = lines;
        self
    }

    pub fn with_context_lines(self, lines: usize) -> Self {
        self.context_lines(lines)
    }

    pub fn show_related_as_nested(mut self) -> Self {
        self._nested_related = true;
        self
    }

    pub fn show_related_as_siblings(mut self) -> Self {
        self._nested_related = false;
        self
    }

    pub fn show_related_errors_as_nested(self) -> Self {
        self.show_related_as_nested()
    }

    pub fn show_related_errors_as_siblings(self) -> Self {
        self.show_related_as_siblings()
    }

    pub fn with_syntax_highlighting(mut self, enabled: bool) -> Self {
        self._syntax_highlighting = enabled;
        self
    }

    pub fn without_syntax_highlighting(mut self) -> Self {
        self._syntax_highlighting = false;
        self
    }

    pub fn syntax_highlighter<T>(self, _highlighter: T) -> Self {
        self
    }

    pub fn link_display_text(mut self, text: impl Into<String>) -> Self {
        self._link_display_text = Some(text.into());
        self
    }

    pub fn render_report<W: fmt::Write>(
        &self,
        f: &mut W,
        diagnostic: &dyn Diagnostic,
    ) -> fmt::Result {
        let _ = (&self.theme, self.tab_width, self.width);
        render_text_report(
            f,
            diagnostic,
            TextRenderOptions {
                context_lines: self.context_lines,
                causes: self.causes,
                footer: self.footer.as_deref(),
                graphical: true,
            },
        )
    }
}

impl Default for GraphicalReportHandler {
    fn default() -> Self {
        Self::new()
    }
}

impl ReportHandler for GraphicalReportHandler {
    fn debug(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut out = String::new();
        self.render_report(&mut out, diagnostic)?;
        f.write_str(&out)
    }
}

struct TextRenderOptions<'a> {
    context_lines: usize,
    causes: bool,
    footer: Option<&'a str>,
    graphical: bool,
}

fn render_text_report<W: fmt::Write>(
    f: &mut W,
    diagnostic: &dyn Diagnostic,
    opts: TextRenderOptions<'_>,
) -> fmt::Result {
    let severity = diagnostic.severity().unwrap_or_default();
    if opts.graphical {
        write!(f, "{}: ", severity_text(Some(severity)))?;
    }
    write!(f, "{diagnostic}")?;
    if let Some(code) = diagnostic.code() {
        write!(f, "\ncode: {code}")?;
    }
    write!(f, "\nseverity: {}", severity_text(Some(severity)))?;
    if let Some(help) = diagnostic.help() {
        write!(f, "\nhelp: {help}")?;
    }
    if let Some(url) = diagnostic.url() {
        write!(f, "\nurl: {url}")?;
    }

    if opts.causes {
        let causes = collect_diagnostic_causes(diagnostic);
        if !causes.is_empty() {
            write!(f, "\ncaused by:")?;
            for cause in causes {
                write!(f, "\n  - {cause}")?;
            }
        }
    }

    if let Some(labels) = diagnostic.labels() {
        let labels: Vec<_> = labels.collect();
        if !labels.is_empty() {
            write!(f, "\nlabels:")?;
            for label in &labels {
                write!(
                    f,
                    "\n  - {}..{}",
                    label.offset(),
                    label.offset() + label.len()
                )?;
                if let Some(text) = label.label() {
                    write!(f, ": {text}")?;
                }
                if label.primary() {
                    write!(f, " (primary)")?;
                }
            }
        }
        if let Some(source) = diagnostic.source_code() {
            for label in labels {
                if let Ok(contents) =
                    source.read_span(label.inner(), opts.context_lines, opts.context_lines)
                {
                    if let Some(name) = contents.name() {
                        write!(f, "\nsource: {name}")?;
                    } else {
                        write!(f, "\nsource:")?;
                    }
                    let snippet = String::from_utf8_lossy(contents.data()).replace('\t', "    ");
                    if !snippet.is_empty() {
                        write!(f, "\n{snippet}")?;
                    }
                }
            }
        }
    }

    if let Some(related) = diagnostic.related() {
        let related: Vec<_> = related.collect();
        if !related.is_empty() {
            write!(f, "\nrelated:")?;
            for rel in related {
                write!(f, "\n  - {rel}")?;
            }
        }
    }

    if let Some(footer) = opts.footer {
        write!(f, "\n{footer}")?;
    }
    Ok(())
}

#[derive(Clone, Debug)]
pub enum HandlerKind {
    Debug(DebugReportHandler),
    Json(JSONReportHandler),
    Narratable(NarratableReportHandler),
    Graphical(GraphicalReportHandler),
}

#[derive(Clone, Debug)]
pub struct MietteHandler {
    inner: HandlerKind,
}

impl MietteHandler {
    pub fn new() -> Self {
        Self {
            inner: HandlerKind::Narratable(NarratableReportHandler::new()),
        }
    }

    pub fn debug() -> Self {
        Self {
            inner: HandlerKind::Debug(DebugReportHandler::new()),
        }
    }

    pub fn json() -> Self {
        Self {
            inner: HandlerKind::Json(JSONReportHandler::new()),
        }
    }

    pub fn narratable() -> Self {
        Self::new()
    }

    pub fn graphical() -> Self {
        Self {
            inner: HandlerKind::Graphical(GraphicalReportHandler::new()),
        }
    }
}

impl Default for MietteHandler {
    fn default() -> Self {
        Self::new()
    }
}

impl ReportHandler for MietteHandler {
    fn debug(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match &self.inner {
            HandlerKind::Debug(handler) => handler.debug(diagnostic, f),
            HandlerKind::Json(handler) => handler.debug(diagnostic, f),
            HandlerKind::Narratable(handler) => handler.debug(diagnostic, f),
            HandlerKind::Graphical(handler) => handler.debug(diagnostic, f),
        }
    }

    fn display(&self, diagnostic: &dyn Diagnostic, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match &self.inner {
            HandlerKind::Json(handler) => handler.display(diagnostic, f),
            HandlerKind::Debug(_) | HandlerKind::Narratable(_) | HandlerKind::Graphical(_) => {
                write!(f, "{diagnostic}")?;
                if f.alternate() {
                    for cause in collect_diagnostic_causes(diagnostic) {
                        write!(f, ": {cause}")?;
                    }
                }
                Ok(())
            }
        }
    }
}

fn default_handler() -> Box<dyn ReportHandler> {
    #[cfg(feature = "fancy-base")]
    {
        Box::new(MietteHandler::default())
    }
    #[cfg(not(feature = "fancy-base"))]
    {
        Box::new(DebugReportHandler::new())
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum RgbColors {
    Always,
    Preferred,
    #[default]
    Never,
}

pub trait Highlighter: fmt::Debug + Send + Sync {
    fn start_highlighter_state<'h>(
        &'h self,
        _language: Option<&str>,
    ) -> Box<dyn HighlighterState + 'h>;
}

pub trait HighlighterState: fmt::Debug {
    fn highlight_line(&mut self, _line: &str) -> Vec<(usize, usize, String)> {
        Vec::new()
    }
}

#[derive(Clone, Debug, Default)]
pub struct BlankHighlighter;

impl BlankHighlighter {
    pub fn new() -> Self {
        Self
    }
}

impl Highlighter for BlankHighlighter {
    fn start_highlighter_state<'h>(
        &'h self,
        _language: Option<&str>,
    ) -> Box<dyn HighlighterState + 'h> {
        Box::new(BlankHighlighterState)
    }
}

#[derive(Clone, Debug, Default)]
pub struct BlankHighlighterState;

impl HighlighterState for BlankHighlighterState {}

#[derive(Clone, Debug, Default)]
pub struct SyntectHighlighter;

impl SyntectHighlighter {
    pub fn new() -> Self {
        Self
    }
}

impl Highlighter for SyntectHighlighter {
    fn start_highlighter_state<'h>(
        &'h self,
        _language: Option<&str>,
    ) -> Box<dyn HighlighterState + 'h> {
        Box::new(BlankHighlighterState)
    }
}

#[derive(Clone, Debug)]
pub struct MietteHandlerOpts {
    force_graphical: Option<bool>,
    force_narrated: Option<bool>,
    theme: Option<GraphicalTheme>,
    footer: Option<String>,
    context_lines: usize,
    tab_width: usize,
    width: Option<usize>,
    causes: bool,
    color: Option<bool>,
    unicode: Option<bool>,
    rgb_colors: RgbColors,
}

impl MietteHandlerOpts {
    pub fn new() -> Self {
        Self {
            force_graphical: None,
            force_narrated: None,
            theme: None,
            footer: None,
            context_lines: 0,
            tab_width: 4,
            width: None,
            causes: true,
            color: None,
            unicode: None,
            rgb_colors: RgbColors::Never,
        }
    }

    pub fn terminal_links(self, _links: bool) -> Self {
        self
    }

    pub fn with_links(self, _links: bool) -> Self {
        self
    }

    pub fn graphical_theme(mut self, theme: GraphicalTheme) -> Self {
        self.theme = Some(theme);
        self
    }

    pub fn theme(self, theme: GraphicalTheme) -> Self {
        self.graphical_theme(theme)
    }

    pub fn with_theme(self, theme: GraphicalTheme) -> Self {
        self.graphical_theme(theme)
    }

    pub fn syntax_highlighter<T>(self, _highlighter: T) -> Self {
        self
    }

    pub fn highlighter<T>(self, _highlighter: T) -> Self {
        self
    }

    pub fn with_syntax_highlighting(self, _enabled: bool) -> Self {
        self
    }

    pub fn without_syntax_highlighting(self) -> Self {
        self
    }

    pub fn width(mut self, width: usize) -> Self {
        self.width = Some(width);
        self
    }

    pub fn with_width(self, width: usize) -> Self {
        self.width(width)
    }

    pub fn wrap_lines(self, _wrap: bool) -> Self {
        self
    }

    pub fn with_wrap_lines(self, wrap: bool) -> Self {
        self.wrap_lines(wrap)
    }

    pub fn break_words(self, _break: bool) -> Self {
        self
    }

    pub fn with_break_words(self, value: bool) -> Self {
        self.break_words(value)
    }

    pub fn word_separator<T>(self, _separator: T) -> Self {
        self
    }

    pub fn with_word_separator<T>(self, separator: T) -> Self {
        self.word_separator(separator)
    }

    pub fn word_splitter<T>(self, _splitter: T) -> Self {
        self
    }

    pub fn with_word_splitter<T>(self, splitter: T) -> Self {
        self.word_splitter(splitter)
    }

    pub fn with_cause_chain(mut self) -> Self {
        self.causes = true;
        self
    }

    pub fn without_cause_chain(mut self) -> Self {
        self.causes = false;
        self
    }

    pub fn show_related_as_nested(self) -> Self {
        self
    }

    pub fn show_related_as_siblings(self) -> Self {
        self
    }

    pub fn show_related_errors_as_nested(self) -> Self {
        self.show_related_as_nested()
    }

    pub fn show_related_errors_as_siblings(self) -> Self {
        self.show_related_as_siblings()
    }

    pub fn color(mut self, color: bool) -> Self {
        self.color = Some(color);
        self
    }

    pub fn rgb_colors(mut self, colors: RgbColors) -> Self {
        self.rgb_colors = colors;
        self
    }

    pub fn unicode(mut self, unicode: bool) -> Self {
        self.unicode = Some(unicode);
        self
    }

    pub fn force_graphical(mut self, graphical: bool) -> Self {
        self.force_graphical = Some(graphical);
        self
    }

    pub fn force_narrated(mut self, narrated: bool) -> Self {
        self.force_narrated = Some(narrated);
        self
    }

    pub fn footer(mut self, footer: impl Into<String>) -> Self {
        self.footer = Some(footer.into());
        self
    }

    pub fn with_footer(self, footer: impl Into<String>) -> Self {
        self.footer(footer)
    }

    pub fn context_lines(mut self, lines: usize) -> Self {
        self.context_lines = lines;
        self
    }

    pub fn with_context_lines(self, lines: usize) -> Self {
        self.context_lines(lines)
    }

    pub fn tab_width(mut self, width: usize) -> Self {
        self.tab_width = width.max(1);
        self
    }

    pub fn with_tab_width(self, width: usize) -> Self {
        self.tab_width(width)
    }

    pub fn build(self) -> MietteHandler {
        if self.force_narrated.unwrap_or(false) {
            let mut h = NarratableReportHandler::new().context_lines(self.context_lines);
            if !self.causes {
                h = h.without_cause_chain();
            }
            if let Some(footer) = self.footer {
                h = h.footer(footer);
            }
            return MietteHandler {
                inner: HandlerKind::Narratable(h),
            };
        }

        if self.force_graphical.unwrap_or(false) {
            let theme = self.theme.unwrap_or_default();
            let mut h = GraphicalReportHandler::new_themed(theme)
                .context_lines(self.context_lines)
                .tab_width(self.tab_width);
            if let Some(width) = self.width {
                h = h.width(width);
            }
            if !self.causes {
                h = h.without_cause_chain();
            }
            if let Some(footer) = self.footer {
                h = h.footer(footer);
            }
            return MietteHandler {
                inner: HandlerKind::Graphical(h),
            };
        }

        MietteHandler {
            inner: HandlerKind::Narratable(
                NarratableReportHandler::new().context_lines(self.context_lines),
            ),
        }
    }
}

impl Default for MietteHandlerOpts {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GraphicalTheme {
    pub characters: ThemeCharacters,
    pub styles: ThemeStyles,
}

impl GraphicalTheme {
    pub fn ascii() -> Self {
        Self {
            characters: ThemeCharacters::ascii(),
            styles: ThemeStyles::ansi(),
        }
    }

    pub fn unicode() -> Self {
        Self {
            characters: ThemeCharacters::unicode(),
            styles: ThemeStyles::ansi(),
        }
    }

    pub fn unicode_nocolor() -> Self {
        Self {
            characters: ThemeCharacters::unicode(),
            styles: ThemeStyles::none(),
        }
    }

    pub fn none() -> Self {
        Self {
            characters: ThemeCharacters::ascii(),
            styles: ThemeStyles::none(),
        }
    }
}

impl Default for GraphicalTheme {
    fn default() -> Self {
        use std::io::IsTerminal;
        if !std::io::stdout().is_terminal() || !std::io::stderr().is_terminal() {
            return Self::none();
        }
        match std::env::var("NO_COLOR") {
            Ok(value) if value != "0" => Self::unicode_nocolor(),
            _ => Self::unicode(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ThemeStyles {
    pub error: String,
    pub warning: String,
    pub advice: String,
    pub help: String,
    pub link: String,
    pub linum: String,
    pub highlights: Vec<String>,
}

impl ThemeStyles {
    pub fn rgb() -> Self {
        Self {
            error: "rgb-error".into(),
            warning: "rgb-warning".into(),
            advice: "rgb-advice".into(),
            help: "rgb-help".into(),
            link: "rgb-link".into(),
            linum: "rgb-linum".into(),
            highlights: vec!["rgb-highlight".into()],
        }
    }

    pub fn ansi() -> Self {
        Self {
            error: "ansi-error".into(),
            warning: "ansi-warning".into(),
            advice: "ansi-advice".into(),
            help: "ansi-help".into(),
            link: "ansi-link".into(),
            linum: "ansi-linum".into(),
            highlights: vec!["ansi-highlight".into()],
        }
    }

    pub fn none() -> Self {
        Self {
            error: String::new(),
            warning: String::new(),
            advice: String::new(),
            help: String::new(),
            link: String::new(),
            linum: String::new(),
            highlights: Vec::new(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ThemeCharacters {
    pub hbar: String,
    pub vbar: String,
    pub xbar: String,
    pub vbar_break: String,
    pub uarrow: String,
    pub rarrow: String,
    pub ltop: String,
    pub mtop: String,
    pub lbot: String,
    pub rbot: String,
    pub mbot: String,
    pub underbar: String,
    pub underline: String,
    pub error: String,
    pub warning: String,
    pub advice: String,
    pub help: String,
}

impl ThemeCharacters {
    pub fn unicode() -> Self {
        Self {
            hbar: "─".into(),
            vbar: "│".into(),
            xbar: "├".into(),
            vbar_break: "·".into(),
            uarrow: "▲".into(),
            rarrow: "▶".into(),
            ltop: "╭".into(),
            mtop: "┬".into(),
            lbot: "╰".into(),
            rbot: "╯".into(),
            mbot: "┴".into(),
            underbar: "─".into(),
            underline: "─".into(),
            error: "error".into(),
            warning: "warning".into(),
            advice: "advice".into(),
            help: "help".into(),
        }
    }

    pub fn emoji() -> Self {
        let mut chars = Self::unicode();
        chars.error = "error".into();
        chars.warning = "warning".into();
        chars.advice = "advice".into();
        chars.help = "help".into();
        chars
    }

    pub fn ascii() -> Self {
        Self {
            hbar: "-".into(),
            vbar: "|".into(),
            xbar: "+".into(),
            vbar_break: ":".into(),
            uarrow: "^".into(),
            rarrow: ">".into(),
            ltop: "+".into(),
            mtop: "+".into(),
            lbot: "+".into(),
            rbot: "+".into(),
            mbot: "+".into(),
            underbar: "-".into(),
            underline: "^".into(),
            error: "error".into(),
            warning: "warning".into(),
            advice: "advice".into(),
            help: "help".into(),
        }
    }
}

#[macro_export]
macro_rules! miette {
    ($($arg:tt)*) => {
        $crate::Report::msg(format!($($arg)*))
    };
}

#[macro_export]
macro_rules! diagnostic {
    (code = $code:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [.with_code($code)] $($rest)+)
    };
    (severity = $severity:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [.with_severity($severity)] $($rest)+)
    };
    (help = $help:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [.with_help($help)] $($rest)+)
    };
    (url = $url:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [.with_url($url)] $($rest)+)
    };
    (labels = $labels:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [.with_labels($labels)] $($rest)+)
    };
    (@acc [$($mods:tt)*] code = $code:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [$($mods)* .with_code($code)] $($rest)+)
    };
    (@acc [$($mods:tt)*] severity = $severity:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [$($mods)* .with_severity($severity)] $($rest)+)
    };
    (@acc [$($mods:tt)*] help = $help:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [$($mods)* .with_help($help)] $($rest)+)
    };
    (@acc [$($mods:tt)*] url = $url:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [$($mods)* .with_url($url)] $($rest)+)
    };
    (@acc [$($mods:tt)*] labels = $labels:expr, $($rest:tt)+) => {
        $crate::diagnostic!(@acc [$($mods)* .with_labels($labels)] $($rest)+)
    };
    (@acc [$($mods:tt)*] $($msg:tt)+) => {{
        let diagnostic = $crate::MietteDiagnostic::new(format!($($msg)+));
        diagnostic $($mods)*
    }};
    ($($msg:tt)+) => {
        $crate::MietteDiagnostic::new(format!($($msg)+))
    };
}

#[macro_export]
macro_rules! bail {
    ($($arg:tt)*) => {
        return Err(::core::convert::Into::into($crate::miette!($($arg)*)))
    };
}

#[macro_export]
macro_rules! ensure {
    ($condition:expr, $($arg:tt)*) => {
        if !$condition {
            $crate::bail!($($arg)*);
        }
    };
}

pub mod __private {
    use super::*;

    pub trait AsSourceCode {
        fn as_source_code(&self) -> Option<&dyn SourceCode>;
    }

    impl<T: SourceCode> AsSourceCode for T {
        fn as_source_code(&self) -> Option<&dyn SourceCode> {
            Some(self)
        }
    }

    impl<T: SourceCode> AsSourceCode for Option<T> {
        fn as_source_code(&self) -> Option<&dyn SourceCode> {
            self.as_ref().map(|value| value as &dyn SourceCode)
        }
    }

    impl AsSourceCode for Box<dyn SourceCode> {
        fn as_source_code(&self) -> Option<&dyn SourceCode> {
            Some(&**self)
        }
    }

    impl AsSourceCode for Box<dyn SourceCode + Send + Sync> {
        fn as_source_code(&self) -> Option<&dyn SourceCode> {
            Some(&**self)
        }
    }

    pub trait AsLabels {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>>;
    }

    impl AsLabels for SourceSpan {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(vec![LabeledSpan::new_with_span(
                text.map(ToString::to_string),
                *self,
            )])
        }
    }

    impl AsLabels for SourceOffset {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(vec![LabeledSpan::new_with_span(
                text.map(ToString::to_string),
                *self,
            )])
        }
    }

    impl AsLabels for usize {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(vec![LabeledSpan::new_with_span(
                text.map(ToString::to_string),
                *self,
            )])
        }
    }

    impl AsLabels for (usize, usize) {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(vec![LabeledSpan::new_with_span(
                text.map(ToString::to_string),
                *self,
            )])
        }
    }

    impl AsLabels for std::ops::Range<usize> {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(vec![LabeledSpan::new_with_span(
                text.map(ToString::to_string),
                self.clone(),
            )])
        }
    }

    impl AsLabels for std::ops::RangeInclusive<usize> {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(vec![LabeledSpan::new_with_span(
                text.map(ToString::to_string),
                self.clone(),
            )])
        }
    }

    impl AsLabels for LabeledSpan {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            let mut label = self.clone();
            if let Some(text) = text {
                label.set_label(Some(text.to_string()));
            }
            Some(vec![label])
        }
    }

    impl AsLabels for Vec<SourceSpan> {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(
                self.iter()
                    .copied()
                    .map(|span| LabeledSpan::new_with_span(text.map(ToString::to_string), span))
                    .collect(),
            )
        }
    }

    impl AsLabels for Vec<LabeledSpan> {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            let mut labels = self.clone();
            if let Some(text) = text {
                for label in &mut labels {
                    label.set_label(Some(text.to_string()));
                }
            }
            Some(labels)
        }
    }

    impl AsLabels for Vec<(usize, usize)> {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(
                self.iter()
                    .copied()
                    .map(|span| LabeledSpan::new_with_span(text.map(ToString::to_string), span))
                    .collect(),
            )
        }
    }

    impl<const N: usize> AsLabels for [SourceSpan; N] {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(
                self.iter()
                    .copied()
                    .map(|span| LabeledSpan::new_with_span(text.map(ToString::to_string), span))
                    .collect(),
            )
        }
    }

    impl<const N: usize> AsLabels for [LabeledSpan; N] {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            let mut labels = self.to_vec();
            if let Some(text) = text {
                for label in &mut labels {
                    label.set_label(Some(text.to_string()));
                }
            }
            Some(labels)
        }
    }

    impl<const N: usize> AsLabels for [(usize, usize); N] {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            Some(
                self.iter()
                    .copied()
                    .map(|span| LabeledSpan::new_with_span(text.map(ToString::to_string), span))
                    .collect(),
            )
        }
    }

    impl<T: AsLabels> AsLabels for Option<T> {
        fn as_labels(&self, text: Option<&str>) -> Option<Vec<LabeledSpan>> {
            self.as_ref().and_then(|value| value.as_labels(text))
        }
    }

    pub trait AsDisplay {
        fn as_display<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>>;
    }

    impl<T: fmt::Display> AsDisplay for Option<T> {
        fn as_display<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
            self.as_ref()
                .map(|value| Box::new(value) as Box<dyn fmt::Display + 'a>)
        }
    }

    macro_rules! impl_as_display {
        ($($ty:ty),* $(,)?) => {
            $(
                impl AsDisplay for $ty {
                    fn as_display<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
                        Some(Box::new(self))
                    }
                }
            )*
        };
    }

    impl_as_display!(
        String, str, bool, char, usize, u8, u16, u32, u64, u128, isize, i8, i16, i32, i64, i128,
        f32, f64
    );

    impl<'s> AsDisplay for &'s str {
        fn as_display<'a>(&'a self) -> Option<Box<dyn fmt::Display + 'a>> {
            Some(Box::new(self))
        }
    }

    pub trait AsDiagnosticSource {
        fn as_diagnostic_source(&self) -> Option<&dyn Diagnostic>;
    }

    impl<T: Diagnostic> AsDiagnosticSource for T {
        fn as_diagnostic_source(&self) -> Option<&dyn Diagnostic> {
            Some(self)
        }
    }

    impl<T: Diagnostic> AsDiagnosticSource for Option<T> {
        fn as_diagnostic_source(&self) -> Option<&dyn Diagnostic> {
            self.as_ref().map(|value| value as &dyn Diagnostic)
        }
    }

    impl AsDiagnosticSource for Box<dyn Diagnostic> {
        fn as_diagnostic_source(&self) -> Option<&dyn Diagnostic> {
            Some(&**self)
        }
    }

    impl AsDiagnosticSource for Box<dyn Diagnostic + Send + Sync> {
        fn as_diagnostic_source(&self) -> Option<&dyn Diagnostic> {
            Some(&**self)
        }
    }

    pub trait AsRelated {
        fn as_related(&self) -> Vec<&dyn Diagnostic>;
    }

    impl<T: Diagnostic> AsRelated for Vec<T> {
        fn as_related(&self) -> Vec<&dyn Diagnostic> {
            self.iter().map(|value| value as &dyn Diagnostic).collect()
        }
    }

    impl<T: Diagnostic> AsRelated for Option<T> {
        fn as_related(&self) -> Vec<&dyn Diagnostic> {
            self.as_ref()
                .map(|value| vec![value as &dyn Diagnostic])
                .unwrap_or_default()
        }
    }

    impl<T: Diagnostic> AsRelated for Box<T> {
        fn as_related(&self) -> Vec<&dyn Diagnostic> {
            vec![&**self]
        }
    }

    impl AsRelated for Box<dyn Diagnostic> {
        fn as_related(&self) -> Vec<&dyn Diagnostic> {
            vec![&**self]
        }
    }

    impl AsRelated for Box<dyn Diagnostic + Send + Sync> {
        fn as_related(&self) -> Vec<&dyn Diagnostic> {
            vec![&**self]
        }
    }

    impl AsRelated for Vec<Box<dyn Diagnostic>> {
        fn as_related(&self) -> Vec<&dyn Diagnostic> {
            self.iter()
                .map(|value| &**value as &dyn Diagnostic)
                .collect()
        }
    }

    impl AsRelated for Vec<Box<dyn Diagnostic + Send + Sync>> {
        fn as_related(&self) -> Vec<&dyn Diagnostic> {
            self.iter()
                .map(|value| &**value as &dyn Diagnostic)
                .collect()
        }
    }

    pub fn code_from_static(value: &'static str) -> Option<Box<dyn fmt::Display>> {
        Some(Box::new(value))
    }

    pub fn normalize_code(value: &str) -> String {
        value.replace(' ', "")
    }

    pub fn type_id_of<T: Any>() -> TypeId {
        TypeId::of::<T>()
    }
}
