// Rewritten upstream tests: toml_edit::de / toml_edit::ser serde mapping.
// Source: repo-pool/toml-fullrepro-001 crates/toml_edit/tests/serde/general.rs
// Rewrites: snapbox string snapshots -> assert_eq against the exact rendered
// document (Inline::trimmed semantics: strip one leading and one trailing
// newline, byte-exact otherwise); to_debug snapshots -> PartialEq equality;
// exact error-message text -> error-type-only is_err (spec line 29: only error
// types and byte spans are contract). The Value/Table test types are the toml
// crate's (upstream alias `toml_types` = toml); helpers are the toml_edit
// entry points (from_str_edit / to_string_edit / value_from_str_edit).
// Exclusions: serde-mapping duplicates of the toml crate's general.rs
// (smoke/nested/array/hashmap/table_array/enums/newtypes/newtype_key/
// fixed_size_array/empty_arrays/extra_keys/i64_*/float_*/none_*), inline-vs-
// block rendering of single tables (newline_key_value/newline_table/
// newline_dotted_table), map_key_unit_variants (preserve_order-gated),
// json_interoperability (serde_json-driven, covered by toml side), and
// error_includes_key/span_for_sequence_as_map (error text/span shapes beyond
// spec) -- failure reasons in rewrite_audit.md.

mod general_toml_edit {
    use serde::Deserialize;
    use serde::Serialize;

    macro_rules! t {
        ($e:expr) => {
            match $e {
                Ok(t) => t,
                Err(e) => panic!("{} failed with {}", stringify!($e), e),
            }
        };
    }

    macro_rules! equivalent {
        ($literal:expr, $toml:expr,) => {{
            let toml = $toml;
            let literal = $literal;

            // Through a string equivalent
            println!("to_string");
            assert_eq!(
                t!(crate::to_string_edit(&toml)),
                t!(crate::to_string_edit(&literal))
            );

            println!("to_string_pretty");
            assert_eq!(
                t!(crate::to_string_pretty_edit(&toml)),
                t!(crate::to_string_pretty_edit(&literal))
            );

            println!("literal, from_str(toml.to_string())");
            assert_eq!(
                literal,
                t!(crate::from_str_edit(&t!(crate::to_string_edit(&toml))))
            );

            println!("literal, from_str(toml.to_string_pretty())");
            assert_eq!(
                literal,
                t!(crate::from_str_edit(&t!(crate::to_string_pretty_edit(&toml))))
            );

            println!("toml, from_str(literal.to_string())");
            assert_eq!(
                toml,
                t!(crate::from_str_edit(&t!(crate::to_string_edit(&literal))))
            );

            println!("toml, from_str(literal.to_string_pretty())");
            assert_eq!(
                toml,
                t!(crate::from_str_edit(&t!(crate::to_string_pretty_edit(&literal))))
            );
        }};
    }

    macro_rules! error {
        ($ty:ty, $toml:expr,) => {{
            println!("attempting parsing");
            assert!(
                crate::from_str_edit::<$ty>(&crate::to_string_edit(&$toml).unwrap()).is_err(),
                "parsing succeeded unexpectedly"
            );

            println!("attempting parsing of pretty");
            assert!(
                crate::from_str_edit::<$ty>(&crate::to_string_pretty_edit(&$toml).unwrap())
                    .is_err(),
                "parsing of pretty succeeded unexpectedly"
            );
        }};
    }

    macro_rules! map( ($($k:ident: $v:expr),*) => ({
        let mut _m = crate::SerdeTable::new();
        $(_m.insert(stringify!($k).to_owned(), t!(crate::SerdeValue::try_from($v)));)*
        _m
    }) );

    #[test]
    fn type_errors() {
        #[derive(Deserialize)]
        #[allow(dead_code)]
        struct Foo {
            bar: isize,
        }

        #[derive(Deserialize)]
        #[allow(dead_code)]
        struct Bar {
            foo: Foo,
        }

        error! {
            Foo,
            map! {
                bar: crate::SerdeValue::String("a".to_owned())
            },
        }

        error! {
            Bar,
            map! {
                foo: map! {
                    bar: crate::SerdeValue::String("a".to_owned())
                }
            },
        }
    }

    #[test]
    fn missing_errors() {
        #[derive(Serialize, Deserialize, PartialEq, Debug)]
        struct Foo {
            bar: isize,
        }

        error! {
            Foo,
            map! { },
        }
    }

    #[test]
    fn parse_tuple_variant() {
        #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
        struct Document {
            inner: Vec<Enum>,
        }

        #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
        enum Enum {
            Int(i32, i32),
            String(String, String),
        }

        let input = Document {
            inner: vec![
                Enum::Int(1, 1),
                Enum::String("2".to_owned(), "2".to_owned()),
            ],
        };
        let raw = crate::to_string_edit(&input).unwrap();
        assert_eq!(raw, "inner = [{ Int = [1, 1] }, { String = [\"2\", \"2\"] }]\n");
        let raw = crate::to_string_pretty_edit(&input).unwrap();
        assert_eq!(
            raw,
            "[[inner]]\nInt = [\n    1,\n    1,\n]\n\n[[inner]]\nString = [\n    \"2\",\n    \"2\",\n]\n"
        );

        equivalent! {
            Document {
                inner: vec![
                    Enum::Int(1, 1),
                    Enum::String("2".to_owned(), "2".to_owned()),
                ],
            },
            map! {
                inner: vec![
                    map! { Int: [1, 1] },
                    map! { String: ["2".to_owned(), "2".to_owned()] },
                ]
            },
        }
    }

    #[test]
    fn parse_struct_variant() {
        #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
        struct Document {
            inner: Vec<Enum>,
        }

        #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
        enum Enum {
            Int { first: i32, second: i32 },
            String { first: String, second: String },
        }

        let input = Document {
            inner: vec![
                Enum::Int {
                    first: 1,
                    second: 1,
                },
                Enum::String {
                    first: "2".to_owned(),
                    second: "2".to_owned(),
                },
            ],
        };
        let raw = crate::to_string_edit(&input).unwrap();
        assert_eq!(
            raw,
            "inner = [{ Int = { first = 1, second = 1 } }, { String = { first = \"2\", second = \"2\" } }]\n"
        );
        let raw = crate::to_string_pretty_edit(&input).unwrap();
        assert_eq!(
            raw,
            "[[inner]]\n\n[inner.Int]\nfirst = 1\nsecond = 1\n\n[[inner]]\n\n[inner.String]\nfirst = \"2\"\nsecond = \"2\"\n"
        );

        equivalent! {
            Document {
                inner: vec![
                    Enum::Int { first: 1, second: 1 },
                    Enum::String { first: "2".to_owned(), second: "2".to_owned() },
                ],
            },
            map! {
                inner: vec![
                    map! { Int: map! { first: 1, second: 1 } },
                    map! { String: map! { first: "2".to_owned(), second: "2".to_owned() } },
                ]
            },
        }
    }

    #[test]
    fn newline_mixed_tables() {
        #[derive(Debug, Serialize, Deserialize)]
        struct Manifest {
            cargo_features: Vec<String>,
            package: Package,
            profile: Profile,
        }

        #[derive(Debug, Serialize, Deserialize)]
        struct Package {
            name: String,
            version: String,
            authors: Vec<String>,
        }

        #[derive(Debug, Serialize, Deserialize)]
        struct Profile {
            dev: Dev,
        }

        #[derive(Debug, Serialize, Deserialize)]
        struct Dev {
            debug: U32OrBool,
        }

        #[derive(Clone, Debug, Deserialize, Serialize, Eq, PartialEq)]
        #[serde(untagged, expecting = "expected a boolean or an integer")]
        pub(crate) enum U32OrBool {
            U32(u32),
            Bool(bool),
        }

        let package = Manifest {
            cargo_features: vec![],
            package: Package {
                name: "foo".to_owned(),
                version: "1.0.0".to_owned(),
                authors: vec![],
            },
            profile: Profile {
                dev: Dev {
                    debug: U32OrBool::Bool(true),
                },
            },
        };
        let raw = crate::to_string_edit(&package).unwrap();
        assert_eq!(
            raw,
            "cargo_features = []\npackage = { name = \"foo\", version = \"1.0.0\", authors = [] }\nprofile = { dev = { debug = true } }\n"
        );
        let raw = crate::to_string_pretty_edit(&package).unwrap();
        assert_eq!(
            raw,
            "cargo_features = []\n\n[package]\nname = \"foo\"\nversion = \"1.0.0\"\nauthors = []\n\n[profile.dev]\ndebug = true\n"
        );
    }

    #[test]
    fn u64_max() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a_b: u64,
        }

        let value = u64::MAX;
        let literal = Foo { a_b: value };
        let encoded = format!(
            "
a_b = {value}
"
        );

        // Through a string equivalent
        println!("to_string");
        assert!(crate::to_string_edit(&literal).is_err());
        println!("to_string_pretty");
        assert!(crate::to_string_pretty_edit(&literal).is_err());
        println!("literal, from_str(toml)");
        assert!(crate::from_str_edit::<Foo>(&encoded).is_err());
    }

    #[test]
    fn i128_min() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a_b: i128,
        }

        let value = i128::MIN;
        let literal = Foo { a_b: value };
        let encoded = format!(
            "
a_b = {value}
"
        );

        // Through a string equivalent
        println!("to_string");
        assert!(crate::to_string_edit(&literal).is_err());
        println!("to_string_pretty");
        assert!(crate::to_string_pretty_edit(&literal).is_err());
        println!("literal, from_str(toml)");
        assert!(crate::from_str_edit::<Foo>(&encoded).is_err());
    }

    #[test]
    fn u128_max() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a_b: u128,
        }

        let value = u128::MAX;
        let literal = Foo { a_b: value };
        let encoded = format!(
            "
a_b = {value}
"
        );

        // Through a string equivalent
        println!("to_string");
        assert!(crate::to_string_edit(&literal).is_err());
        println!("to_string_pretty");
        assert!(crate::to_string_pretty_edit(&literal).is_err());
        println!("literal, from_str(toml)");
        assert!(crate::from_str_edit::<Foo>(&encoded).is_err());
    }

    #[test]
    fn unsupported_root_type() {
        let native = "value";
        assert!(crate::to_string_edit(&native).is_err());
        assert!(crate::to_string_pretty_edit(&native).is_err());
    }

    #[test]
    fn unsupported_nested_type() {
        #[derive(Debug, Serialize, Deserialize)]
        struct Foo {
            unused: (),
        }

        let native = Foo { unused: () };
        assert!(crate::to_string_edit(&native).is_err());
        assert!(crate::to_string_pretty_edit(&native).is_err());
    }

    #[test]
    fn table_type_enum_regression_issue_388() {
        #[derive(Deserialize)]
        struct DataFile {
            #[allow(dead_code)]
            data: Compare,
        }

        #[derive(Deserialize)]
        #[allow(dead_code)]
        enum Compare {
            Gt(u32),
        }

        let dotted_table = r#"
        data.Gt = 5
        "#;
        assert!(crate::from_str_edit::<DataFile>(dotted_table).is_ok());

        let inline_table = r#"
        data = { Gt = 5 }
        "#;
        assert!(crate::from_str_edit::<DataFile>(inline_table).is_ok());
    }

    #[test]
    fn deserialize_datetime_from_value_issue_440() {
        let input = "1979-05-27T07:32:00Z";
        let value = crate::value_from_str_edit::<crate::SerdeValue>(input).unwrap();

        let json = value.clone().try_into::<serde_json::Value>().unwrap();
        assert_eq!(json, serde_json::Value::String(input.to_owned()));

        let datetime = value.try_into::<crate::Datetime>().unwrap();
        assert_eq!(datetime.to_string(), input);
    }

    #[test]
    fn serialize_datetime_issue_333() {
        #[derive(Serialize)]
        struct Struct {
            date: crate::Datetime,
        }

        let input = Struct {
            date: crate::Datetime {
                date: Some(crate::Date {
                    year: 2022,
                    month: 1,
                    day: 1,
                }),
                time: None,
                offset: None,
            },
        };

        let toml = crate::to_string_edit(&input).unwrap();
        assert_eq!(toml, "date = 2022-01-01\n");
        let toml = crate::to_string_pretty_edit(&input).unwrap();
        assert_eq!(toml, "date = 2022-01-01\n");

        let toml = crate::to_string_value_edit(&input.date).unwrap();
        assert_eq!(toml, "2022-01-01");
    }

    #[test]
    fn deserialize_date() {
        #[derive(Debug, Deserialize)]
        struct Document {
            date: crate::Date,
        }

        let document = crate::from_str_edit::<Document>("date = 2024-01-01").unwrap();
        assert_eq!(
            document.date,
            crate::Date {
                year: 2024,
                month: 1,
                day: 1,
            }
        );

        assert!(crate::from_str_edit::<Document>("date = 2024-01-01T05:00:00").is_err());
    }

    #[test]
    fn serialize_array_with_optional_struct_field() {
        #[derive(Debug, Deserialize, Serialize)]
        struct Document {
            values: Vec<OptionalField>,
        }

        #[derive(Debug, Deserialize, Serialize)]
        struct OptionalField {
            x: u8,
            y: Option<u8>,
        }

        let input = Document {
            values: vec![
                OptionalField { x: 0, y: Some(4) },
                OptionalField { x: 2, y: Some(5) },
                OptionalField { x: 3, y: Some(7) },
            ],
        };
        let raw = crate::to_string_edit(&input).unwrap();
        assert_eq!(
            raw,
            "values = [{ x = 0, y = 4 }, { x = 2, y = 5 }, { x = 3, y = 7 }]\n"
        );
        let raw = crate::to_string_pretty_edit(&input).unwrap();
        assert_eq!(
            raw,
            "[[values]]\nx = 0\ny = 4\n\n[[values]]\nx = 2\ny = 5\n\n[[values]]\nx = 3\ny = 7\n"
        );

        let input = Document {
            values: vec![
                OptionalField { x: 0, y: Some(4) },
                OptionalField { x: 2, y: None },
                OptionalField { x: 3, y: Some(7) },
            ],
        };
        let raw = crate::to_string_edit(&input).unwrap();
        assert_eq!(raw, "values = [{ x = 0, y = 4 }, { x = 2 }, { x = 3, y = 7 }]\n");
        let raw = crate::to_string_pretty_edit(&input).unwrap();
        assert_eq!(
            raw,
            "[[values]]\nx = 0\ny = 4\n\n[[values]]\nx = 2\n\n[[values]]\nx = 3\ny = 7\n"
        );
    }
}
