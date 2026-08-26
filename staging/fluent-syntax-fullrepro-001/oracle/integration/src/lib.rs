// Oracle integration tests for the FTL grammar engine
#![cfg(test)]
#![allow(clippy::all)]

use std::borrow::Cow;

use fluent_syntax::ast::{
    Attribute, CallArguments, Comment, Entry, Expression, Identifier, InlineExpression, Message,
    NamedArgument, Pattern, PatternElement, Resource, Term, VariantKey,
};
use fluent_syntax::parser::{parse, parse_runtime, ErrorKind, ParserError};
use fluent_syntax::serializer::{serialize, serialize_with_options, Options};
use fluent_syntax::unicode::{unescape_unicode, unescape_unicode_to_string};

fn ok(input: &str) -> Resource<&str> {
    parse(input).expect("expected a clean parse")
}

fn bad(input: &str) -> (Resource<&str>, Vec<ParserError>) {
    parse(input).expect_err("expected parse errors")
}

fn msg<'a>(r: &'a Resource<&'a str>, i: usize) -> &'a Message<&'a str> {
    match &r.body[i] {
        Entry::Message(m) => m,
        e => panic!("expected message at body[{i}], got {e:?}"),
    }
}

fn text(value: &str) -> PatternElement<&str> {
    PatternElement::TextElement { value }
}

fn var(name: &str) -> PatternElement<&str> {
    PatternElement::Placeable {
        expression: Expression::Inline(InlineExpression::VariableReference {
            id: Identifier { name },
        }),
    }
}

/// Concatenated text of a pattern with placeables rendered as a marker.
fn flat_text(p: &Pattern<&str>) -> String {
    let mut out = String::new();
    for e in &p.elements {
        match e {
            PatternElement::TextElement { value } => out.push_str(value),
            PatternElement::Placeable { .. } => out.push('\u{0001}'),
        }
    }
    out
}

include!("all/round_trip.rs");
include!("all/modes.rs");
include!("all/recovery.rs");
include!("all/grammar_compose.rs");
include!("all/unicode_binding.rs");
