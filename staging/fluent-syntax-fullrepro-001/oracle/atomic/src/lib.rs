// Oracle atomic tests for the FTL grammar engine
#![cfg(test)]
#![allow(clippy::all)]

use std::borrow::Cow;

use fluent_syntax::ast::{
    Attribute, CallArguments, Comment, Entry, Expression, Identifier, InlineExpression, Message,
    NamedArgument, Pattern, PatternElement, Resource, Term, Variant, VariantKey,
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

fn term_at<'a>(r: &'a Resource<&'a str>, i: usize) -> &'a Term<&'a str> {
    match &r.body[i] {
        Entry::Term(t) => t,
        e => panic!("expected term at body[{i}], got {e:?}"),
    }
}

/// Text elements as strings; placeables marked.
fn texts<'a>(p: &'a Pattern<&'a str>) -> Vec<&'a str> {
    p.elements
        .iter()
        .map(|e| match e {
            PatternElement::TextElement { value } => *value,
            PatternElement::Placeable { .. } => "<placeable>",
        })
        .collect()
}

fn value_texts<'a>(m: &'a Message<&'a str>) -> Vec<&'a str> {
    texts(m.value.as_ref().expect("message should carry a value"))
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

fn select_parts<'a>(
    p: &'a Pattern<&'a str>,
) -> (&'a InlineExpression<&'a str>, &'a Vec<Variant<&'a str>>) {
    match &p.elements[0] {
        PatternElement::Placeable {
            expression: Expression::Select { selector, variants },
        } => (selector, variants),
        e => panic!("expected select placeable, got {e:?}"),
    }
}

// ---------------------------------------------------------------------------
// Entry grammar
// ---------------------------------------------------------------------------

#[test]
fn generated_message_ast_shape() {
    let r = ok("berth-status = All lanes clear\n");
    assert_eq!(
        r.body[0],
        Entry::Message(Message {
            id: Identifier { name: "berth-status" },
            value: Some(Pattern {
                elements: vec![text("All lanes clear")],
            }),
            attributes: vec![],
            comment: None,
        }),
    );
}

#[test]
fn generated_term_ast_shape() {
    let r = ok("-station-name = Meridian Spur\n");
    assert_eq!(
        r.body[0],
        Entry::Term(Term {
            id: Identifier { name: "station-name" },
            value: Pattern {
                elements: vec![text("Meridian Spur")],
            },
            attributes: vec![],
            comment: None,
        }),
    );
}

#[test]
fn generated_identifier_charset() {
    let r = ok("crew_count-9 = ready\n");
    assert_eq!(msg(&r, 0).id.name, "crew_count-9");

    // Identifiers must start with an ASCII letter.
    let (r, errs) = bad("9lives = no\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(
        errs[0].kind,
        ErrorKind::ExpectedCharRange { range: "a-zA-Z".to_string() },
    );
    assert_eq!(r.body[0], Entry::Junk { content: "9lives = no\n" });
}

#[test]
fn generated_message_attributes_only() {
    let r = ok("portal =\n    .tone = low\n");
    let m = msg(&r, 0);
    assert_eq!(m.value, None);
    assert_eq!(
        m.attributes,
        vec![Attribute {
            id: Identifier { name: "tone" },
            value: Pattern { elements: vec![text("low")] },
        }],
    );
}

#[test]
fn generated_attributes_in_order_varied_indent() {
    let r = ok("gate = open\n    .north = yes\n  .south = no\n");
    let m = msg(&r, 0);
    assert_eq!(value_texts(m), vec!["open"]);
    let names: Vec<&str> = m.attributes.iter().map(|a| a.id.name).collect();
    assert_eq!(names, vec!["north", "south"]);
    assert_eq!(texts(&m.attributes[1].value), vec!["no"]);
}

#[test]
fn generated_empty_and_blank_inputs() {
    assert_eq!(ok("").body.len(), 0);
    assert_eq!(ok("\n\n   \n").body.len(), 0);
}

#[test]
fn generated_entries_in_order() {
    let r = ok("alpha = one\n-beta = two\ngamma = three\n");
    assert_eq!(r.body.len(), 3);
    assert_eq!(msg(&r, 0).id.name, "alpha");
    assert_eq!(term_at(&r, 1).id.name, "beta");
    assert_eq!(msg(&r, 2).id.name, "gamma");
}

#[test]
fn generated_spaces_around_equals() {
    let r = ok("pier   =   staffed\n");
    let m = msg(&r, 0);
    assert_eq!(m.id.name, "pier");
    assert_eq!(value_texts(m), vec!["staffed"]);
}

// ---------------------------------------------------------------------------
// Pattern text: lines, indentation, dedent
// ---------------------------------------------------------------------------

#[test]
fn generated_common_indent_excess() {
    let r = ok("deck =\n    line one\n      line two\n    line three\n");
    assert_eq!(
        value_texts(msg(&r, 0)),
        vec!["line one\n", "  line two\n", "line three"],
    );

    // Deeper first line, shallower later line: the minimum wins.
    let r = ok("hull =\n        deep\n    shallow\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["    deep\n", "shallow"]);
}

#[test]
fn generated_blank_line_element() {
    let r = ok("log =\n    first\n\n    last\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["first\n", "\n", "last"]);
}

#[test]
fn generated_blank_line_excess_spaces() {
    // The blank line carries six spaces against a common indent of four:
    // two survive ahead of the line feed.
    let r = ok("log =\n    a\n      \n    b\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["a\n", "  \n", "b"]);

    // Fewer spaces than the common indent: bare line feed.
    let r = ok("log =\n    a\n  \n    b\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["a\n", "\n", "b"]);
}

#[test]
fn generated_inline_then_continuation() {
    let r = ok("note = head\n    tail\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["head\n", "tail"]);

    // The inline first line is kept verbatim; continuation lines dedent
    // by their own common indent.
    let r = ok("memo = first\n      indented\n    normal\n");
    assert_eq!(
        value_texts(msg(&r, 0)),
        vec!["first\n", "  indented\n", "normal"],
    );
}

#[test]
fn generated_trailing_trim() {
    let r = ok("memo =\n    only\n\n\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["only"]);

    let r = ok("memo = padded   ");
    assert_eq!(value_texts(msg(&r, 0)), vec!["padded"]);
}

#[test]
fn generated_zero_column_placeable_continues() {
    // `{` at column zero continues the pattern and pins the common indent
    // to zero, so the following text line keeps its two spaces.
    let r = ok("sign =\n{ \"S\" }\n  txt\n");
    let p = msg(&r, 0).value.as_ref().unwrap();
    assert_eq!(texts(p), vec!["<placeable>", "\n", "  txt"]);
    assert_eq!(
        p.elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::StringLiteral { value: "S" }),
        },
    );
}

#[test]
fn generated_zero_column_text_breaks() {
    let r = ok("k =\n    x\nplain = z\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["x"]);
    assert_eq!(msg(&r, 1).id.name, "plain");
}

#[test]
fn generated_bracket_line_breaks_pattern() {
    // An indented `[` line ends the pattern; the leftover line is junk.
    let (r, errs) = bad("key = a\n    [x] b\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["a"]);
    assert_eq!(r.body[1], Entry::Junk { content: "    [x] b\n" });
    assert_eq!(errs.len(), 1);
    assert_eq!(
        errs[0].kind,
        ErrorKind::ExpectedCharRange { range: "a-zA-Z".to_string() },
    );
}

#[test]
fn generated_placeable_line_indent_dropped() {
    // Indentation before a line-leading `{` vanishes and does not join the
    // common indent, which comes from the text line alone.
    let r = ok("art =\n        { \"x\" } tail\n    body\n");
    assert_eq!(
        value_texts(msg(&r, 0)),
        vec!["<placeable>", " tail\n", "body"],
    );
}

#[test]
fn generated_crlf_element_split() {
    let r = ok("win =\r\n    aa\r\n    bb\r\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["aa", "\n", "bb"]);

    let r = ok("helm = a\r\nkeel = b\r\n");
    assert_eq!(value_texts(msg(&r, 0)), vec!["a"]);
    assert_eq!(msg(&r, 1).id.name, "keel");
}

#[test]
fn generated_text_around_placeable() {
    let r = ok("route = via { $lane } only\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements,
        vec![text("via "), var("lane"), text(" only")],
    );
}

// ---------------------------------------------------------------------------
// Placeables and expressions
// ---------------------------------------------------------------------------

#[test]
fn generated_variable_reference_ast() {
    let r = ok("k = { $cargo }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements,
        vec![var("cargo")],
    );
}

#[test]
fn generated_string_literal_raw() {
    // The stored value keeps escape sequences intact.
    let r = ok("k = { \"tide\\\\mark\" }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::StringLiteral {
                value: "tide\\\\mark",
            }),
        },
    );

    let r = ok("k = { \"say \\\"aye\\\" twice\" }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::StringLiteral {
                value: "say \\\"aye\\\" twice",
            }),
        },
    );
}

#[test]
fn generated_number_literal_raw() {
    let r = ok("k = { 007 } { -0.50 }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements,
        vec![
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::NumberLiteral { value: "007" }),
            },
            text(" "),
            PatternElement::Placeable {
                expression: Expression::Inline(InlineExpression::NumberLiteral { value: "-0.50" }),
            },
        ],
    );
}

#[test]
fn generated_message_reference_forms() {
    let r = ok("k = { fleet } { fleet.size }\n");
    let elems = &msg(&r, 0).value.as_ref().unwrap().elements;
    assert_eq!(
        elems[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::MessageReference {
                id: Identifier { name: "fleet" },
                attribute: None,
            }),
        },
    );
    assert_eq!(
        elems[2],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::MessageReference {
                id: Identifier { name: "fleet" },
                attribute: Some(Identifier { name: "size" }),
            }),
        },
    );
}

#[test]
fn generated_term_reference_args() {
    let r = ok("k = { -dock(side: \"east\") }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::TermReference {
                id: Identifier { name: "dock" },
                attribute: None,
                arguments: Some(CallArguments {
                    positional: vec![],
                    named: vec![NamedArgument {
                        name: Identifier { name: "side" },
                        value: InlineExpression::StringLiteral { value: "east" },
                    }],
                }),
            }),
        },
    );
}

#[test]
fn generated_function_reference() {
    let r = ok("k = { DATETIME($when, hour12: 2) }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::FunctionReference {
                id: Identifier { name: "DATETIME" },
                arguments: CallArguments {
                    positional: vec![InlineExpression::VariableReference {
                        id: Identifier { name: "when" },
                    }],
                    named: vec![NamedArgument {
                        name: Identifier { name: "hour12" },
                        value: InlineExpression::NumberLiteral { value: "2" },
                    }],
                },
            }),
        },
    );
}

#[test]
fn generated_nested_placeable_ast() {
    let r = ok("k = {{ $depth }}\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::Placeable {
                expression: Box::new(Expression::Inline(
                    InlineExpression::VariableReference { id: Identifier { name: "depth" } },
                )),
            }),
        },
    );
}

#[test]
fn generated_callee_case_rule() {
    let (_, errs) = bad("k = { datetime($x) }\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(errs[0].kind, ErrorKind::ForbiddenCallee);

    // Uppercase letters, digits, `_`, and `-` are all legal callee material.
    let r = ok("k = { GRID-2($x) }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::FunctionReference {
                id: Identifier { name: "GRID-2" },
                arguments: CallArguments {
                    positional: vec![InlineExpression::VariableReference {
                        id: Identifier { name: "x" },
                    }],
                    named: vec![],
                },
            }),
        },
    );
}

#[test]
fn generated_named_arg_literal_only() {
    let (_, errs) = bad("k = { FMT(width: $w) }\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(errs[0].kind, ErrorKind::ExpectedLiteral);

    let r = ok("k = { FMT(width: 4) }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::FunctionReference {
                id: Identifier { name: "FMT" },
                arguments: CallArguments {
                    positional: vec![],
                    named: vec![NamedArgument {
                        name: Identifier { name: "width" },
                        value: InlineExpression::NumberLiteral { value: "4" },
                    }],
                },
            }),
        },
    );
}

#[test]
fn generated_arg_ordering_rules() {
    let (_, errs) = bad("k = { FMT(side: 1, $x) }\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(errs[0].kind, ErrorKind::PositionalArgumentFollowsNamed);

    let (_, errs) = bad("k = { FMT(side: 1, side: 2) }\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(
        errs[0].kind,
        ErrorKind::DuplicatedNamedArgument("side".to_string()),
    );
}

#[test]
fn generated_trailing_comma_empty_args() {
    let r = ok("k = { SUM(1, 2,) } { NOW() }\n");
    let elems = &msg(&r, 0).value.as_ref().unwrap().elements;
    assert_eq!(
        elems[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::FunctionReference {
                id: Identifier { name: "SUM" },
                arguments: CallArguments {
                    positional: vec![
                        InlineExpression::NumberLiteral { value: "1" },
                        InlineExpression::NumberLiteral { value: "2" },
                    ],
                    named: vec![],
                },
            }),
        },
    );
    assert_eq!(
        elems[2],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::FunctionReference {
                id: Identifier { name: "NOW" },
                arguments: CallArguments { positional: vec![], named: vec![] },
            }),
        },
    );
}

#[test]
fn generated_term_attr_placeable_error() {
    let (_, errs) = bad("k = { -dock.side }\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(errs[0].kind, ErrorKind::TermAttributeAsPlaceable);

    // Message attributes are fine as placeables.
    let r = ok("k = { dock.side }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::MessageReference {
                id: Identifier { name: "dock" },
                attribute: Some(Identifier { name: "side" }),
            }),
        },
    );
}

// ---------------------------------------------------------------------------
// String literal escapes (parser side)
// ---------------------------------------------------------------------------

#[test]
fn generated_string_escapes_accepted() {
    // All five escape forms parse and are stored raw.
    let r = ok("k = { \"a\\\\b \\\"c\\\" \\{ \\u0394 \\U01F680\" }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::StringLiteral {
                value: "a\\\\b \\\"c\\\" \\{ \\u0394 \\U01F680",
            }),
        },
    );
}

#[test]
fn generated_unknown_escape_err() {
    let (r, errs) = bad("k = { \"a\\p\" }\n");
    assert_eq!(errs.len(), 1);
    assert!(matches!(errs[0].kind, ErrorKind::UnknownEscapeSequence(_)));
    assert_eq!(r.body[0], Entry::Junk { content: "k = { \"a\\p\" }\n" });

    let r = ok("k = { \"a\\\\p\" }\n");
    assert_eq!(
        msg(&r, 0).value.as_ref().unwrap().elements[0],
        PatternElement::Placeable {
            expression: Expression::Inline(InlineExpression::StringLiteral { value: "a\\\\p" }),
        },
    );
}

#[test]
fn generated_bad_unicode_and_unterminated() {
    let (_, errs) = bad("k = { \"a\\uQQ11\" }\n");
    assert_eq!(errs.len(), 1);
    assert!(matches!(
        errs[0].kind,
        ErrorKind::InvalidUnicodeEscapeSequence(_),
    ));

    let (_, errs) = bad("k = { \"open\nnext = fine\n");
    assert_eq!(errs[0].kind, ErrorKind::UnterminatedStringLiteral);
}

// ---------------------------------------------------------------------------
// Select expressions
// ---------------------------------------------------------------------------

#[test]
fn generated_select_ast() {
    let r = ok("crates = { $count ->\n    [one] One crate\n   *[other] Many crates\n}\n");
    let (selector, variants) = select_parts(msg(&r, 0).value.as_ref().unwrap());
    assert_eq!(
        selector,
        &InlineExpression::VariableReference { id: Identifier { name: "count" } },
    );
    assert_eq!(
        variants,
        &vec![
            Variant {
                key: VariantKey::Identifier { name: "one" },
                value: Pattern { elements: vec![text("One crate")] },
                default: false,
            },
            Variant {
                key: VariantKey::Identifier { name: "other" },
                value: Pattern { elements: vec![text("Many crates")] },
                default: true,
            },
        ],
    );
}

#[test]
fn generated_variant_number_keys() {
    let r = ok("k = { $n ->\n    [-2] under\n    [1.5] frac\n   *[ 0 ] zero\n}\n");
    let (_, variants) = select_parts(msg(&r, 0).value.as_ref().unwrap());
    assert_eq!(variants[0].key, VariantKey::NumberLiteral { value: "-2" });
    assert_eq!(variants[1].key, VariantKey::NumberLiteral { value: "1.5" });
    assert_eq!(variants[2].key, VariantKey::NumberLiteral { value: "0" });
    assert!(variants[2].default);
}

#[test]
fn generated_selector_legality() {
    let (_, errs) = bad("k = { fleet ->\n   *[a] b\n}\n");
    assert_eq!(errs[0].kind, ErrorKind::MessageReferenceAsSelector);

    let (_, errs) = bad("k = { fleet.size ->\n   *[a] b\n}\n");
    assert_eq!(errs[0].kind, ErrorKind::MessageAttributeAsSelector);

    let (_, errs) = bad("k = { -dock ->\n   *[a] b\n}\n");
    assert_eq!(errs[0].kind, ErrorKind::TermReferenceAsSelector);

    // A term reference WITH an attribute is a legal selector.
    let r = ok("k = { -dock.side ->\n   *[a] b\n}\n");
    let (selector, _) = select_parts(msg(&r, 0).value.as_ref().unwrap());
    assert_eq!(
        selector,
        &InlineExpression::TermReference {
            id: Identifier { name: "dock" },
            attribute: Some(Identifier { name: "side" }),
            arguments: None,
        },
    );
}

#[test]
fn generated_default_rules() {
    let (_, errs) = bad("k = { $n ->\n    [one] a\n}\n");
    assert_eq!(errs[0].kind, ErrorKind::MissingDefaultVariant);

    let (_, errs) = bad("k = { $n ->\n   *[one] a\n   *[two] b\n}\n");
    assert_eq!(errs[0].kind, ErrorKind::MultipleDefaultVariants);
}

#[test]
fn generated_variant_order_preserved() {
    let r = ok("k = { $n ->\n   *[zero] z\n    [one] o\n    [two] t\n}\n");
    let (_, variants) = select_parts(msg(&r, 0).value.as_ref().unwrap());
    let order: Vec<(bool, &VariantKey<&str>)> =
        variants.iter().map(|v| (v.default, &v.key)).collect();
    assert_eq!(
        order,
        vec![
            (true, &VariantKey::Identifier { name: "zero" }),
            (false, &VariantKey::Identifier { name: "one" }),
            (false, &VariantKey::Identifier { name: "two" }),
        ],
    );
}

#[test]
fn generated_selector_line_end_required() {
    let (_, errs) = bad("k = { $n -> *[a] b }\n");
    assert_eq!(
        errs[0].kind,
        ErrorKind::ExpectedCharRange { range: "\n | \r\n".to_string() },
    );
}

#[test]
fn generated_variant_missing_value() {
    let (_, errs) = bad("k = { $n ->\n   *[a]\n}\n");
    assert_eq!(errs[0].kind, ErrorKind::MissingValue);
}

// ---------------------------------------------------------------------------
// Comments and attachment
// ---------------------------------------------------------------------------

#[test]
fn generated_comment_levels() {
    let r = ok("# plain\n\n## grouped\n\n### top\n\nanchor = set\n");
    assert_eq!(r.body[0], Entry::Comment(Comment { content: vec!["plain"] }));
    assert_eq!(r.body[1], Entry::GroupComment(Comment { content: vec!["grouped"] }));
    assert_eq!(r.body[2], Entry::ResourceComment(Comment { content: vec!["top"] }));
    assert_eq!(msg(&r, 3).comment, None);
}

#[test]
fn generated_comment_attaches() {
    let r = ok("# fresh paint\ndock-a = wet\n");
    assert_eq!(r.body.len(), 1);
    assert_eq!(
        msg(&r, 0).comment,
        Some(Comment { content: vec!["fresh paint"] }),
    );

    // Terms attach too.
    let r = ok("# house term\n-yard = Stern Yard\n");
    assert_eq!(r.body.len(), 1);
    assert_eq!(
        term_at(&r, 0).comment,
        Some(Comment { content: vec!["house term"] }),
    );
}

#[test]
fn generated_blank_line_detaches() {
    let r = ok("# adrift\n\ndock-b = dry\n");
    assert_eq!(r.body[0], Entry::Comment(Comment { content: vec!["adrift"] }));
    assert_eq!(msg(&r, 1).comment, None);
}

#[test]
fn generated_group_resource_never_attach() {
    let r = ok("## section\nmast = up\n");
    assert_eq!(r.body[0], Entry::GroupComment(Comment { content: vec!["section"] }));
    assert_eq!(msg(&r, 1).comment, None);

    let r = ok("### file\nmast = up\n");
    assert_eq!(r.body[0], Entry::ResourceComment(Comment { content: vec!["file"] }));
    assert_eq!(msg(&r, 1).comment, None);
}

#[test]
fn generated_comment_block_merge_split() {
    let r = ok("# first line\n# second line\nkeel = deep\n");
    assert_eq!(
        msg(&r, 0).comment,
        Some(Comment { content: vec!["first line", "second line"] }),
    );

    // A level change splits the block; neither part attaches.
    let r = ok("# solo\n## section\nkeel = deep\n");
    assert_eq!(r.body[0], Entry::Comment(Comment { content: vec!["solo"] }));
    assert_eq!(r.body[1], Entry::GroupComment(Comment { content: vec!["section"] }));
    assert_eq!(msg(&r, 2).comment, None);
}

#[test]
fn generated_empty_comment_lines() {
    let r = ok("#\n# body\nk = v\n");
    assert_eq!(
        msg(&r, 0).comment,
        Some(Comment { content: vec!["", "body"] }),
    );

    let r = ok("###\nk = v\n");
    assert_eq!(r.body[0], Entry::ResourceComment(Comment { content: vec![""] }));
}

#[test]
fn generated_malformed_comment_junk() {
    let (r, errs) = bad("#skew\nmast = up\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(errs[0].kind, ErrorKind::ExpectedToken(' '));
    assert_eq!(errs[0].pos, 1..2);
    assert_eq!(errs[0].slice, Some(0..6));
    assert_eq!(r.body[0], Entry::Junk { content: "#skew\n" });
    assert_eq!(msg(&r, 1).id.name, "mast");
}

// ---------------------------------------------------------------------------
// Runtime mode
// ---------------------------------------------------------------------------

#[test]
fn generated_runtime_strips_comments() {
    let r: Resource<&str> = parse_runtime("### file\n## section\n# note\nhold = full\n")
        .expect("clean runtime parse");
    assert_eq!(r.body.len(), 1);
    assert_eq!(
        r.body[0],
        Entry::Message(Message {
            id: Identifier { name: "hold" },
            value: Some(Pattern { elements: vec![text("full")] }),
            attributes: vec![],
            comment: None,
        }),
    );
}

#[test]
fn generated_runtime_skips_malformed_comment() {
    // The same line that junks the full parser vanishes silently here.
    let r: Resource<&str> = parse_runtime("#skew\nmast = up\n").expect("runtime parse is clean");
    assert_eq!(r.body.len(), 1);
    assert_eq!(msg(&r, 0).id.name, "mast");
}

// ---------------------------------------------------------------------------
// Error recovery and junk
// ---------------------------------------------------------------------------

#[test]
fn generated_missing_equals_error() {
    let (r, errs) = bad("moor = fast\nslip 44\nwake = low\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(errs[0].kind, ErrorKind::ExpectedToken('='));
    assert_eq!(errs[0].pos, 17..18);
    assert_eq!(errs[0].slice, Some(12..20));
    assert_eq!(msg(&r, 0).id.name, "moor");
    assert_eq!(r.body[1], Entry::Junk { content: "slip 44\n" });
    assert_eq!(msg(&r, 2).id.name, "wake");
}

#[test]
fn generated_junk_absorbs_trailing_blanks() {
    let (r, errs) = bad("helm = set\n\n?adrift line\n\n\nkeel = deep\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(
        errs[0].kind,
        ErrorKind::ExpectedCharRange { range: "a-zA-Z".to_string() },
    );
    assert_eq!(errs[0].pos, 12..13);
    assert_eq!(errs[0].slice, Some(12..27));
    assert_eq!(r.body[1], Entry::Junk { content: "?adrift line\n\n\n" });
    assert_eq!(msg(&r, 2).id.name, "keel");
}

#[test]
fn generated_junk_stops_at_entry_starters() {
    // A `#` line ends the junk span, and the comment then attaches ahead.
    let (r, errs) = bad("!wreck\n# salvage\nspar = new\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(r.body[0], Entry::Junk { content: "!wreck\n" });
    assert_eq!(
        msg(&r, 1).comment,
        Some(Comment { content: vec!["salvage"] }),
    );

    // A `-` line ends the junk span too.
    let (r, _) = bad("!wreck\n-buoy = red\n");
    assert_eq!(r.body[0], Entry::Junk { content: "!wreck\n" });
    assert_eq!(term_at(&r, 1).id.name, "buoy");
}

#[test]
fn generated_missing_field_errors() {
    let (r, errs) = bad("hollow =\n\nsound = on\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(
        errs[0].kind,
        ErrorKind::ExpectedMessageField { entry_id: "hollow".to_string() },
    );
    assert_eq!(errs[0].pos, 0..10);
    assert_eq!(errs[0].slice, Some(0..10));
    assert_eq!(r.body[0], Entry::Junk { content: "hollow =\n\n" });
    assert_eq!(msg(&r, 1).id.name, "sound");

    // A term with attributes but no value still fails.
    let (r, errs) = bad("-flag =\n    .hue = red\n");
    assert_eq!(
        errs[0].kind,
        ErrorKind::ExpectedTermField { entry_id: "flag".to_string() },
    );
    assert_eq!(r.body[0], Entry::Junk { content: "-flag =\n    .hue = red\n" });
}

#[test]
fn generated_unbalanced_brace() {
    let (r, errs) = bad("k = a } b\n");
    assert_eq!(errs.len(), 1);
    assert_eq!(errs[0].kind, ErrorKind::UnbalancedClosingBrace);
    assert_eq!(r.body[0], Entry::Junk { content: "k = a } b\n" });
}

#[test]
fn generated_error_records_eq_clone() {
    let (_, errs) = bad("moor = fast\nslip 44\nwake = low\n");
    let expected = ParserError {
        pos: 17..18,
        slice: Some(12..20),
        kind: ErrorKind::ExpectedToken('='),
    };
    assert_eq!(errs[0], expected);
    assert_eq!(errs[0].clone(), expected);
    assert_ne!(
        errs[0].kind,
        ErrorKind::ExpectedToken('}'),
    );
}

// ---------------------------------------------------------------------------
// Serialization
// ---------------------------------------------------------------------------

#[test]
fn generated_serialize_message_term_canonical() {
    let canonical = "berth = clear\n-slipway = Long Reach\n";
    let r = ok(canonical);
    assert_eq!(serialize(&r), canonical);
}

#[test]
fn generated_serialize_normalizes_spacing() {
    assert_eq!(serialize(&ok("pier=docked\n")), "pier = docked\n");
    assert_eq!(serialize(&ok("quay =   trimmed\n")), "quay = trimmed\n");
    assert_eq!(serialize(&ok("crane = lifting")), "crane = lifting\n");
}

#[test]
fn generated_serialize_multiline_form() {
    let canonical = "cargo =\n    crates stacked\n    nets furled\n";
    assert_eq!(serialize(&ok(canonical)), canonical);

    // Two-space indentation normalizes to four.
    let r = ok("cargo =\n  crates stacked\n  nets furled\n");
    assert_eq!(serialize(&r), canonical);
}

#[test]
fn generated_serialize_attributes() {
    let canonical = "gate = open\n    .north = yes\n    .south = no\n";
    assert_eq!(serialize(&ok(canonical)), canonical);

    let attr_only = "portal =\n    .tone = low\n";
    assert_eq!(serialize(&ok(attr_only)), attr_only);
}

#[test]
fn generated_serialize_select_star_indent() {
    let canonical = "cargo-report =\n    { $crates ->\n        [one] One crate\n       *[other] { $crates } crates\n    }\n";
    assert_eq!(serialize(&ok(canonical)), canonical);
}

#[test]
fn generated_serialize_placeable_forms() {
    assert_eq!(serialize(&ok("k = {$tug}\n")), "k = { $tug }\n");
    assert_eq!(serialize(&ok("k = {{ $tug }}\n")), "k = {{ $tug }}\n");
    assert_eq!(serialize(&ok("k = a{ $tug }b\n")), "k = a{ $tug }b\n");
}

#[test]
fn generated_serialize_references() {
    let canonical =
        "k = { \"raw\\u0394\" } { -0.5 } { fleet.size } { -dock(side: \"east\", n: 2) } { SUM(1, top: 3) }\n";
    assert_eq!(serialize(&ok(canonical)), canonical);
}

#[test]
fn generated_serialize_junk_toggle() {
    let (r, _) = bad("keep = 1\n!junked\nalso = 2\n");
    assert_eq!(serialize(&r), "keep = 1\nalso = 2\n");
    assert_eq!(
        serialize_with_options(&r, Options { with_junk: true }),
        "keep = 1\n!junked\nalso = 2\n",
    );

    // Options surface: Default, Copy, PartialEq.
    let d = Options::default();
    let copy = d;
    assert_eq!(copy, Options { with_junk: false });
    assert_ne!(copy, Options { with_junk: true });
}

#[test]
fn generated_serialize_comment_framing() {
    // Attached comments hug their entry.
    let attached = "# wet paint\ndock-a = wet\n";
    assert_eq!(serialize(&ok(attached)), attached);

    // Free comments are framed by blank lines.
    let r = ok("a = 1\n\n# drift one\n# drift two\n\nb = 2\n");
    assert_eq!(serialize(&r), "a = 1\n\n# drift one\n# drift two\n\nb = 2\n");

    // A trailing free comment gains its frame.
    let r = ok("a = 1\n# tail\n");
    assert_eq!(serialize(&r), "a = 1\n\n# tail\n\n");

    // Empty comment lines render as the bare marker.
    let r = ok("#\n# text\nk = v\n");
    assert_eq!(serialize(&r), "#\n# text\nk = v\n");
}

#[test]
fn generated_serialize_handbuilt_ast() {
    let resource: Resource<&str> = Resource {
        body: vec![Entry::Message(Message {
            id: Identifier { name: "beacon" },
            value: Some(Pattern {
                elements: vec![text("Signal "), var("level")],
            }),
            attributes: vec![Attribute {
                id: Identifier { name: "tone" },
                value: Pattern { elements: vec![text("harsh")] },
            }],
            comment: None,
        })],
    };
    assert_eq!(
        serialize(&resource),
        "beacon = Signal { $level }\n    .tone = harsh\n",
    );
}

// ---------------------------------------------------------------------------
// Unicode unescaping
// ---------------------------------------------------------------------------

#[test]
fn generated_unescape_basic() {
    assert_eq!(
        unescape_unicode_to_string("keel \\\\ over"),
        "keel \\ over",
    );
    assert_eq!(
        unescape_unicode_to_string("say \\\"aye\\\""),
        "say \"aye\"",
    );
}

#[test]
fn generated_unescape_four_and_six() {
    assert_eq!(unescape_unicode_to_string("delta \\u0394 wave"), "delta Δ wave");
    assert_eq!(unescape_unicode_to_string("lift \\U01F680 off"), "lift 🚀 off");
    assert_eq!(unescape_unicode_to_string("\\u0041\\u0043"), "AC");
}

#[test]
fn generated_unescape_replacement_rules() {
    // Unknown escape consumes the escaped character.
    assert_eq!(unescape_unicode_to_string("a\\pb"), "a\u{FFFD}b");
    // The parser-legal `\{` is unknown to the unescaper.
    assert_eq!(unescape_unicode_to_string("a\\{b"), "a\u{FFFD}b");
    // Bad hex digits.
    assert_eq!(unescape_unicode_to_string("a\\uG1G1b"), "a\u{FFFD}b");
    // Value outside the scalar range.
    assert_eq!(unescape_unicode_to_string("a\\U110000b"), "a\u{FFFD}b");
    // Truncated at end of input.
    assert_eq!(unescape_unicode_to_string("a\\u4A"), "a\u{FFFD}");
    // Lone trailing backslash.
    assert_eq!(unescape_unicode_to_string("a\\"), "a\u{FFFD}");
}

#[test]
fn generated_unescape_cow() {
    let untouched = unescape_unicode_to_string("no escapes aboard");
    assert!(matches!(untouched, Cow::Borrowed(_)));
    assert_eq!(untouched, "no escapes aboard");

    let owned = unescape_unicode_to_string("one \\\\ here");
    assert!(matches!(owned, Cow::Owned(_)));
    assert_eq!(owned, "one \\ here");
}

#[test]
fn generated_unescape_writer() {
    let mut out = String::new();
    unescape_unicode(&mut out, "port \\u03A9 side").expect("write to String cannot fail");
    assert_eq!(out, "port Ω side");
}
