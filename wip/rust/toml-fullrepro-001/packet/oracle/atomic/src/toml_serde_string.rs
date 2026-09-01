// Rewritten upstream tests: toml::ser::to_string / to_string_pretty document rendering.
// Source: repo-pool/toml-fullrepro-001 crates/toml/tests/serde/{ser_to_string,ser_to_string_pretty}.rs
// Rewrites: byte-exact output assertions -> parse-back equality round-trip (spec
// TOML-SERDE-020: serialization must re-parse to the identical document; byte identity
// of typed serialization is not spec'd); no_unnecessary_newlines (FMT-011 pretty
// policy) kept verbatim.

mod toml_serde_string {

use serde::{Deserialize, Serialize};

#[track_caller]
fn t(toml: &str) {
    let value: crate::SerdeDocument = crate::from_str(toml).unwrap();
    let result = crate::to_string(&value).unwrap();
    let reparsed: crate::SerdeDocument = crate::from_str(&result).unwrap();
    assert_eq!(reparsed, value);
}

#[track_caller]
fn t_pretty(toml: &str) {
    let value: crate::SerdeDocument = crate::from_str(toml).unwrap();
    let result = crate::to_string_pretty(&value).unwrap();
    let reparsed: crate::SerdeDocument = crate::from_str(&result).unwrap();
    assert_eq!(reparsed, value);
}

// ===== ser_to_string =====

#[test]
fn ser_to_string_no_unnecessary_newlines_array() {
    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct Users {
        pub(crate) user: Vec<User>,
    }

    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct User {
        pub(crate) name: String,
        pub(crate) surname: String,
    }

    assert!(
        !crate::to_string(&Users {
            user: vec![
                User {
                    name: "John".to_owned(),
                    surname: "Doe".to_owned(),
                },
                User {
                    name: "Jane".to_owned(),
                    surname: "Dough".to_owned(),
                },
            ],
        })
        .unwrap()
        .starts_with('\n')
    );
}

#[test]
fn ser_to_string_no_unnecessary_newlines_table() {
    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct TwoUsers {
        pub(crate) user0: User,
        pub(crate) user1: User,
    }

    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct User {
        pub(crate) name: String,
        pub(crate) surname: String,
    }

    assert!(
        !crate::to_string(&TwoUsers {
            user0: User {
                name: "John".to_owned(),
                surname: "Doe".to_owned(),
            },
            user1: User {
                name: "Jane".to_owned(),
                surname: "Dough".to_owned(),
            },
        })
        .unwrap()
        .starts_with('\n')
    );
}

#[test]
fn ser_to_string_basic() {
    t(
        "\
[example]
array = [\"item 1\", \"item 2\"]
empty = []
oneline = \"this has no newlines.\"
text = '''

this is the first line\\nthis is the second line
'''
",
    );
}

#[test]
fn ser_to_string_tricky() {
    t(
        r#"[example]
f = "\f"
glass = """
Nothing too unusual, except that I can eat glass in:
- Greek: Μπορώ να φάω σπασμένα γυαλιά χωρίς να πάθω τίποτα. 
- Polish: Mogę jeść szkło, i mi nie szkodzi. 
- Hindi: मैं काँच खा सकता हूँ, मुझे उस से कोई पीडा नहीं होती. 
- Japanese: 私はガラスを食べられます。それは私を傷つけません。 
"""
r = "\r"
r_newline = """
\r
"""
single = "this is a single line but has '' cuz it's tricky"
single_tricky = "single line with ''' in it"
tabs = """
this is pretty standard
\texcept for some   \ttabs right here
"""
text = """
this is the first line.
This has a ''' in it and ""\" cuz it's tricky yo
Also ' and " because why not
this is the fourth line
"""
"#,
    );
}

#[test]
fn ser_to_string_table_array() {
    t(
        r#"
[abc]
doc = "this is a table"

[[array]]
key = "foo"

[[array]]
key = "bar"

[example]
single = "this is a single line string"
"#,
    );
}

#[test]
fn ser_to_string_empty_table() {
    t(
        r#"[example]
"#,
    );
}

#[test]
fn ser_to_string_implicit_tables() {
    t(
        r#"
authors = []
name = "foo"
version = "0.0.0"

[profile.dev]
debug = true
"#,
    );
}

// ===== ser_to_string_pretty =====

#[test]
fn ser_to_string_pretty_no_unnecessary_newlines_array() {
    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct Users {
        pub(crate) user: Vec<User>,
    }

    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct User {
        pub(crate) name: String,
        pub(crate) surname: String,
    }

    assert!(
        !crate::to_string_pretty(&Users {
            user: vec![
                User {
                    name: "John".to_owned(),
                    surname: "Doe".to_owned(),
                },
                User {
                    name: "Jane".to_owned(),
                    surname: "Dough".to_owned(),
                },
            ],
        })
        .unwrap()
        .starts_with('\n')
    );
}

#[test]
fn ser_to_string_pretty_no_unnecessary_newlines_table() {
    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct TwoUsers {
        pub(crate) user0: User,
        pub(crate) user1: User,
    }

    #[derive(Debug, Clone, Hash, PartialEq, Eq, Serialize, Deserialize)]
    struct User {
        pub(crate) name: String,
        pub(crate) surname: String,
    }

    assert!(
        !crate::to_string_pretty(&TwoUsers {
            user0: User {
                name: "John".to_owned(),
                surname: "Doe".to_owned(),
            },
            user1: User {
                name: "Jane".to_owned(),
                surname: "Dough".to_owned(),
            },
        })
        .unwrap()
        .starts_with('\n')
    );
}

#[test]
fn ser_to_string_pretty_basic() {
    t_pretty(
        "\
[example]
array = [\"item 1\", \"item 2\"]
empty = []
oneline = \"this has no newlines.\"
text = '''

this is the first line\\nthis is the second line
'''
",
    );
}

#[test]
fn ser_to_string_pretty_tricky() {
    t_pretty(
        r#"[example]
f = "\f"
glass = """
Nothing too unusual, except that I can eat glass in:
- Greek: Μπορώ να φάω σπασμένα γυαλιά χωρίς να πάθω τίποτα. 
- Polish: Mogę jeść szkło, i mi nie szkodzi. 
- Hindi: मैं काँच खा सकता हूँ, मुझे उस से कोई पीडा नहीं होती. 
- Japanese: 私はガラスを食べられます。それは私を傷つけません。 
"""
r = "\r"
r_newline = """
\r
"""
single = "this is a single line but has '' cuz it's tricky"
single_tricky = "single line with ''' in it"
tabs = """
this is pretty standard
\texcept for some   \ttabs right here
"""
text = """
this is the first line.
This has a ''' in it and ""\" cuz it's tricky yo
Also ' and " because why not
this is the fourth line
"""
"#,
    );
}

#[test]
fn ser_to_string_pretty_table_array() {
    t_pretty(
        r#"
[abc]
doc = "this is a table"

[[array]]
key = "foo"

[[array]]
key = "bar"

[example]
single = "this is a single line string"
"#,
    );
}

#[test]
fn ser_to_string_pretty_empty_table() {
    t_pretty(
        r#"[example]
"#,
    );
}

#[test]
fn ser_to_string_pretty_implicit_tables() {
    t_pretty(
        r#"
authors = []
name = "foo"
version = "0.0.0"

[profile.dev]
debug = true
"#,
    );
}

}
