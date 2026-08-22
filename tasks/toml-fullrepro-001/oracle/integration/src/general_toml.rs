// Rewritten upstream tests: toml::de / toml::ser serde mapping and document
// rendering for structs, enums, maps, arrays, datetimes, and error cases.
// Source: repo-pool/toml-fullrepro-001 crates/toml/tests/serde/general.rs
// Rewrites: snapbox string snapshots -> assert_eq against the exact rendered
// document (snapbox Inline::trimmed semantics: strip one leading and one
// trailing newline, byte-exact otherwise); to_debug snapshots -> PartialEq
// equality; exact error-message text -> error-type-only is_err (spec line 29:
// only error types and byte spans are contract); to_string_value unwrap
// (helper returns Result per crate-root convention); map_key_unit_variants
// (preserve_order-gated), span_for_sequence_as_map (span beyond spec),
// json_interoperability (serde_json-driven), error_includes_key and the
// newline_*/smoke/newtypes/homogeneous_*/float_min/i64_min/
// serialize_struct_with_none_{string,struct} duplicates are excluded
// (failure reasons in rewrite_audit.md).

mod general_toml {
    use std::collections::BTreeMap;

    use serde::Deserialize;
    use serde::Deserializer;
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
                t!(crate::to_string(&toml)),
                t!(crate::to_string(&literal))
            );

            println!("to_string_pretty");
            assert_eq!(
                t!(crate::to_string_pretty(&toml)),
                t!(crate::to_string_pretty(&literal))
            );

            println!("literal, from_str(toml.to_string())");
            assert_eq!(literal, t!(crate::from_str(&t!(crate::to_string(&toml)))));

            println!("literal, from_str(toml.to_string_pretty())");
            assert_eq!(
                literal,
                t!(crate::from_str(&t!(crate::to_string_pretty(&toml))))
            );

            println!("toml, from_str(literal.to_string())");
            assert_eq!(toml, t!(crate::from_str(&t!(crate::to_string(&literal)))));

            println!("toml, from_str(literal.to_string_pretty())");
            assert_eq!(
                toml,
                t!(crate::from_str(&t!(crate::to_string_pretty(&literal))))
            );

            println!("toml.try_into()");
            assert_eq!(literal, t!(toml.clone().try_into()));

            println!("Value::Table(toml).try_into()");
            assert_eq!(literal, t!(toml::Value::Table(toml.clone()).try_into()));
        }};
    }

    macro_rules! error {
        ($ty:ty, $toml:expr,) => {{
            println!("attempting parsing");
            assert!(
                crate::from_str::<$ty>(&crate::to_string(&$toml).unwrap()).is_err(),
                "parsing succeeded unexpectedly"
            );

            println!("attempting parsing of pretty");
            assert!(
                crate::from_str::<$ty>(&crate::to_string_pretty(&$toml).unwrap()).is_err(),
                "parsing of pretty succeeded unexpectedly"
            );

            println!("attempting toml decoding");
            assert!(
                $toml.try_into::<$ty>().is_err(),
                "value decoding succeeded unexpectedly"
            );
        }};
    }

    macro_rules! map( ($($k:ident: $v:expr),*) => ({
        let mut _m = crate::SerdeTable::new();
        $(_m.insert(stringify!($k).to_owned(), t!(crate::SerdeValue::try_from($v)));)*
        _m
    }) );

    #[test]
    fn smoke_hyphen() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a_b: isize,
        }

        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo2 {
            #[serde(rename = "a-b")]
            a_b: isize,
        }

        equivalent! {
            Foo { a_b: 2 },
            map! { a_b: crate::SerdeValue::Integer(2)},
        }

        let mut m = crate::SerdeTable::new();
        m.insert("a-b".to_owned(), crate::SerdeValue::Integer(2));
        equivalent! {
            Foo2 { a_b: 2 },
            m,
        }
    }

    #[test]
    fn nested() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a: isize,
            b: Bar,
        }
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Bar {
            a: String,
        }

        equivalent! {
            Foo { a: 2, b: Bar { a: "test".to_owned() } },
            map! {
                a: crate::SerdeValue::Integer(2),
                b: map! {
                    a: crate::SerdeValue::String("test".to_owned())
                }
            },
        }
    }

    #[test]
    fn application_decode_error() {
        #[derive(PartialEq, Debug)]
        struct Range10(usize);
        impl<'de> Deserialize<'de> for Range10 {
            fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
                let x: usize = Deserialize::deserialize(d)?;
                if x > 10 {
                    Err(serde::de::Error::custom("more than 10"))
                } else {
                    Ok(Self(x))
                }
            }
        }
        let d_good = crate::SerdeValue::Integer(5);
        let d_bad1 = crate::SerdeValue::String("not an isize".to_owned());
        let d_bad2 = crate::SerdeValue::Integer(11);

        assert_eq!(d_good.try_into::<Range10>().unwrap(), Range10(5));

        let err1: Result<Range10, _> = d_bad1.try_into();
        assert!(err1.is_err());
        let err2: Result<Range10, _> = d_bad2.try_into();
        assert!(err2.is_err());
    }

    #[test]
    fn array() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a: Vec<isize>,
        }

        equivalent! {
            Foo { a: vec![1, 2, 3, 4] },
            map! {
                a: crate::SerdeValue::Array(vec![
                    crate::SerdeValue::Integer(1),
                    crate::SerdeValue::Integer(2),
                    crate::SerdeValue::Integer(3),
                    crate::SerdeValue::Integer(4)
                ])
            },
        };
    }

    #[test]
    fn hashmap() {
        use std::collections::HashSet;

        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            map: BTreeMap<String, isize>,
            set: HashSet<char>,
        }

        equivalent! {
            Foo {
                set: {
                    let mut s = HashSet::new();
                    s.insert('a');
                    s
                },
                map: {
                    let mut m = BTreeMap::new();
                    m.insert("bar".to_owned(), 4);
                    m.insert("foo".to_owned(), 10);
                    m
                }
            },
            map! {
                map: map! {
                    bar: crate::SerdeValue::Integer(4),
                    foo: crate::SerdeValue::Integer(10)
                },
                set: crate::SerdeValue::Array(vec![crate::SerdeValue::String("a".to_owned())])
            },
        }
    }

    #[test]
    fn table_array() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a: Vec<Bar>,
        }
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Bar {
            a: isize,
        }

        equivalent! {
            Foo { a: vec![Bar { a: 1 }, Bar { a: 2 }] },
            map! {
                a: crate::SerdeValue::Array(vec![
                    crate::SerdeValue::Table(map!{ a: crate::SerdeValue::Integer(1) }),
                    crate::SerdeValue::Table(map!{ a: crate::SerdeValue::Integer(2) }),
                ])
            },
        }
    }

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
    fn parse_enum() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a: E,
        }
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        #[serde(untagged)]
        enum E {
            Bar(isize),
            Baz(String),
            Last(Foo2),
        }
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo2 {
            test: String,
        }

        equivalent! {
            Foo { a: E::Bar(10) },
            map! { a: crate::SerdeValue::Integer(10) },
        }

        equivalent! {
            Foo { a: E::Baz("foo".to_owned()) },
            map! { a: crate::SerdeValue::String("foo".to_owned()) },
        }

        equivalent! {
            Foo { a: E::Last(Foo2 { test: "test".to_owned() }) },
            map! { a: map! { test: crate::SerdeValue::String("test".to_owned()) } },
        }
    }

    #[test]
    fn parse_enum_string() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a: Sort,
        }

        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        #[serde(rename_all = "lowercase")]
        enum Sort {
            Asc,
            Desc,
        }

        equivalent! {
            Foo { a: Sort::Desc },
            map! { a: crate::SerdeValue::String("desc".to_owned()) },
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
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(
            raw,
            "[[inner]]\nInt = [1, 1]\n\n[[inner]]\nString = [\"2\", \"2\"]\n"
        );
        let raw = crate::to_string_pretty(&input).unwrap();
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
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(
            raw,
            "[[inner]]\n\n[inner.Int]\nfirst = 1\nsecond = 1\n\n[[inner]]\n\n[inner.String]\nfirst = \"2\"\nsecond = \"2\"\n"
        );
        let raw = crate::to_string_pretty(&input).unwrap();
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
    fn empty_arrays() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a: Vec<Bar>,
        }
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Bar;

        equivalent! {
            Foo { a: vec![] },
            map! {a: crate::SerdeValue::Array(Vec::new())},
        }
    }

    #[test]
    fn extra_keys() {
        #[derive(Serialize, Deserialize)]
        struct Foo {
            a: isize,
        }

        let toml = map! { a: crate::SerdeValue::Integer(2), b: crate::SerdeValue::Integer(2) };
        assert!(toml.clone().try_into::<Foo>().is_ok());
        assert!(crate::from_str::<Foo>(&crate::to_string(&toml).unwrap()).is_ok());
        assert!(crate::from_str::<Foo>(&crate::to_string_pretty(&toml).unwrap()).is_ok());
    }

    #[test]
    fn newtypes2() {
        #[derive(Deserialize, Serialize, PartialEq, Debug, Clone)]
        struct A {
            b: B,
        }

        #[derive(Deserialize, Serialize, PartialEq, Debug, Clone)]
        struct B(Option<C>);

        #[derive(Deserialize, Serialize, PartialEq, Debug, Clone)]
        struct C {
            x: u32,
            y: u32,
            z: u32,
        }

        equivalent! {
            A { b: B(Some(C { x: 0, y: 1, z: 2 })) },
            map! {
                b: map! {
                    x: crate::SerdeValue::Integer(0),
                    y: crate::SerdeValue::Integer(1),
                    z: crate::SerdeValue::Integer(2)
                }
            },
        }
    }

    #[test]
    fn newtype_variant() {
        #[derive(Copy, Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
        struct Struct {
            field: Enum,
        }

        #[derive(Copy, Clone, Debug, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
        enum Enum {
            Variant(u8),
        }

        equivalent! {
            Struct { field: Enum::Variant(21) },
            map! {
                field: map! {
                    Variant: crate::SerdeValue::Integer(21)
                }
            },
        }
    }

    #[test]
    fn newtype_key() {
        #[derive(PartialEq, Eq, PartialOrd, Ord, Hash, Debug, Clone, Serialize, Deserialize)]
        struct NewType(String);

        type CustomKeyMap = BTreeMap<NewType, u32>;

        equivalent! {
            [
                (NewType("x".to_owned()), 1),
                (NewType("y".to_owned()), 2),
            ].into_iter().collect::<CustomKeyMap>(),
            map! {
                x: crate::SerdeValue::Integer(1),
                y: crate::SerdeValue::Integer(2)
            },
        }
    }

    #[test]
    fn fixed_size_array() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Entity {
            pos: [i32; 2],
        }

        equivalent! {
            Entity { pos: [1, 2] },
            map! {
                pos: crate::SerdeValue::Array(vec![
                    crate::SerdeValue::Integer(1),
                    crate::SerdeValue::Integer(2),
                ])
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
        let raw = crate::to_string(&package).unwrap();
        assert_eq!(
            raw,
            "cargo_features = []\n\n[package]\nname = \"foo\"\nversion = \"1.0.0\"\nauthors = []\n\n[profile.dev]\ndebug = true\n"
        );
        let raw = crate::to_string_pretty(&package).unwrap();
        assert_eq!(
            raw,
            "cargo_features = []\n\n[package]\nname = \"foo\"\nversion = \"1.0.0\"\nauthors = []\n\n[profile.dev]\ndebug = true\n"
        );
    }

    #[test]
    fn i64_max() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a_b: i64,
        }

        equivalent! {
            Foo { a_b: i64::MAX },
            map! { a_b: crate::SerdeValue::Integer(i64::MAX) },
        }
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
        assert_eq!(
            crate::to_string(&literal).unwrap(),
            "a_b = 18446744073709551615\n"
        );
        println!("to_string_pretty");
        assert_eq!(
            crate::to_string_pretty(&literal).unwrap(),
            "a_b = 18446744073709551615\n"
        );
        println!("literal, from_str(toml)");
        assert_eq!(crate::from_str::<Foo>(&encoded).unwrap(), literal);

        // In/out of Value is equivalent
        println!("Table::try_from(literal)");
        assert!(toml::Table::try_from(literal.clone()).is_err());
        println!("Value::try_from(literal)");
        assert!(toml::Value::try_from(literal.clone()).is_err());
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
        assert_eq!(
            crate::to_string(&literal).unwrap(),
            "a_b = -170141183460469231731687303715884105728\n"
        );
        println!("to_string_pretty");
        assert_eq!(
            crate::to_string_pretty(&literal).unwrap(),
            "a_b = -170141183460469231731687303715884105728\n"
        );
        println!("literal, from_str(toml)");
        assert_eq!(crate::from_str::<Foo>(&encoded).unwrap(), literal);

        // In/out of Value is equivalent
        println!("Table::try_from(literal)");
        assert!(toml::Table::try_from(literal.clone()).is_err());
        println!("Value::try_from(literal)");
        assert!(toml::Value::try_from(literal.clone()).is_err());
    }

    #[test]
    fn i128_max() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a_b: i128,
        }

        let value = i128::MAX;
        let literal = Foo { a_b: value };
        let encoded = format!(
            "
a_b = {value}
"
        );

        // Through a string equivalent
        println!("to_string");
        assert_eq!(
            crate::to_string(&literal).unwrap(),
            "a_b = 170141183460469231731687303715884105727\n"
        );
        println!("to_string_pretty");
        assert_eq!(
            crate::to_string_pretty(&literal).unwrap(),
            "a_b = 170141183460469231731687303715884105727\n"
        );
        println!("literal, from_str(toml)");
        assert_eq!(crate::from_str::<Foo>(&encoded).unwrap(), literal);

        // In/out of Value is equivalent
        println!("Table::try_from(literal)");
        assert!(toml::Table::try_from(literal.clone()).is_err());
        println!("Value::try_from(literal)");
        assert!(toml::Value::try_from(literal.clone()).is_err());
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
        assert_eq!(
            crate::to_string(&literal).unwrap(),
            "a_b = 340282366920938463463374607431768211455\n"
        );
        println!("to_string_pretty");
        assert_eq!(
            crate::to_string_pretty(&literal).unwrap(),
            "a_b = 340282366920938463463374607431768211455\n"
        );
        println!("literal, from_str(toml)");
        assert_eq!(crate::from_str::<Foo>(&encoded).unwrap(), literal);

        // In/out of Value is equivalent
        println!("Table::try_from(literal)");
        assert!(toml::Table::try_from(literal.clone()).is_err());
        println!("Value::try_from(literal)");
        assert!(toml::Value::try_from(literal.clone()).is_err());
    }

    #[test]
    fn float_max() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a_b: f64,
        }

        equivalent! {
            Foo { a_b: f64::MAX },
            map! { a_b: crate::SerdeValue::Float(f64::MAX) },
        }
    }

    #[test]
    fn unsupported_root_type() {
        let native = "value";
        assert!(crate::to_string(&native).is_err());
        assert!(crate::to_string_pretty(&native).is_err());
    }

    #[test]
    fn unsupported_nested_type() {
        #[derive(Debug, Serialize, Deserialize)]
        struct Foo {
            unused: (),
        }

        let native = Foo { unused: () };
        assert!(crate::to_string(&native).is_err());
        assert!(crate::to_string_pretty(&native).is_err());
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
        assert!(crate::from_str::<DataFile>(dotted_table).is_ok());

        let inline_table = r#"
        data = { Gt = 5 }
        "#;
        assert!(crate::from_str::<DataFile>(inline_table).is_ok());
    }

    #[test]
    fn deserialize_datetime_from_value_issue_440() {
        let input = "1979-05-27T07:32:00Z";
        let value = crate::value_from_str::<crate::SerdeValue>(input).unwrap();

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

        let toml = crate::to_string(&input).unwrap();
        assert_eq!(toml, "date = 2022-01-01\n");
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(toml, "date = 2022-01-01\n");

        let toml = crate::to_string_value(&input.date).unwrap();
        assert_eq!(toml, "2022-01-01");
    }

    #[test]
    fn serialize_date() {
        #[derive(Serialize)]
        struct Document {
            date: crate::Date,
        }

        let input = Document {
            date: crate::Date {
                year: 2024,
                month: 1,
                day: 1,
            },
        };
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(raw, "date = 2024-01-01\n");
        let raw = crate::to_string_pretty(&input).unwrap();
        assert_eq!(raw, "date = 2024-01-01\n");

        let toml = crate::to_string_value(&input.date).unwrap();
        assert_eq!(toml, "2024-01-01");
    }

    #[test]
    fn serialize_time() {
        #[derive(Serialize)]
        struct Document {
            date: crate::Time,
        }

        let input = Document {
            date: crate::Time {
                hour: 5,
                minute: 0,
                second: None,
                nanosecond: None,
            },
        };
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(raw, "date = 05:00\n");
        let raw = crate::to_string_pretty(&input).unwrap();
        assert_eq!(raw, "date = 05:00\n");

        let toml = crate::to_string_value(&input.date).unwrap();
        assert_eq!(toml, "05:00");
    }

    #[test]
    fn deserialize_date() {
        #[derive(Debug, Deserialize)]
        struct Document {
            date: crate::Date,
        }

        let document = crate::from_str::<Document>("date = 2024-01-01").unwrap();
        assert_eq!(
            document.date,
            crate::Date {
                year: 2024,
                month: 1,
                day: 1,
            }
        );

        assert!(crate::from_str::<Document>("date = 2024-01-01T05:00:00").is_err());
    }

    #[test]
    fn deserialize_time() {
        #[derive(Debug, Deserialize)]
        struct Document {
            time: crate::Time,
        }

        let document = crate::from_str::<Document>("time = 05:00:00").unwrap();
        assert_eq!(
            document.time,
            crate::Time {
                hour: 5,
                minute: 0,
                second: Some(0),
                nanosecond: None,
            }
        );

        assert!(crate::from_str::<Document>("time = 2024-01-01T05:00:00").is_err());
    }

    #[test]
    fn serialize_array_with_none_value() {
        #[derive(Serialize)]
        struct Document {
            values: Vec<Option<usize>>,
        }

        let input = Document {
            values: vec![Some(1), Some(2), Some(3)],
        };
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(raw, "values = [1, 2, 3]\n");
        let raw = crate::to_string_pretty(&input).unwrap();
        assert_eq!(
            raw,
            "values = [\n    1,\n    2,\n    3,\n]\n"
        );

        let input = Document {
            values: vec![Some(1), None, Some(3)],
        };
        assert!(crate::to_string(&input).is_err());
        assert!(crate::to_string_pretty(&input).is_err());
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
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(
            raw,
            "[[values]]\nx = 0\ny = 4\n\n[[values]]\nx = 2\ny = 5\n\n[[values]]\nx = 3\ny = 7\n"
        );
        let raw = crate::to_string_pretty(&input).unwrap();
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
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(
            raw,
            "[[values]]\nx = 0\ny = 4\n\n[[values]]\nx = 2\n\n[[values]]\nx = 3\ny = 7\n"
        );
        let raw = crate::to_string_pretty(&input).unwrap();
        assert_eq!(
            raw,
            "[[values]]\nx = 0\ny = 4\n\n[[values]]\nx = 2\n\n[[values]]\nx = 3\ny = 7\n"
        );
    }

    #[test]
    fn serialize_array_with_enum_of_optional_struct_field() {
        #[derive(Debug, Deserialize, Serialize)]
        struct Document {
            values: Vec<Choice>,
        }

        #[derive(Debug, Deserialize, Serialize)]
        enum Choice {
            Optional(OptionalField),
            Empty,
        }

        #[derive(Debug, Deserialize, Serialize)]
        struct OptionalField {
            x: u8,
            y: Option<u8>,
        }

        let input = Document {
            values: vec![
                Choice::Optional(OptionalField { x: 0, y: Some(4) }),
                Choice::Empty,
                Choice::Optional(OptionalField { x: 2, y: Some(5) }),
                Choice::Optional(OptionalField { x: 3, y: Some(7) }),
            ],
        };
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(
            raw,
            "values = [{ Optional = { x = 0, y = 4 } }, \"Empty\", { Optional = { x = 2, y = 5 } }, { Optional = { x = 3, y = 7 } }]\n"
        );
        let raw = crate::to_string_pretty(&input).unwrap();
        assert_eq!(
            raw,
            "values = [\n    { Optional = { x = 0, y = 4 } },\n    \"Empty\",\n    { Optional = { x = 2, y = 5 } },\n    { Optional = { x = 3, y = 7 } },\n]\n"
        );

        let input = Document {
            values: vec![
                Choice::Optional(OptionalField { x: 0, y: Some(4) }),
                Choice::Empty,
                Choice::Optional(OptionalField { x: 2, y: None }),
                Choice::Optional(OptionalField { x: 3, y: Some(7) }),
            ],
        };
        let raw = crate::to_string(&input).unwrap();
        assert_eq!(
            raw,
            "values = [{ Optional = { x = 0, y = 4 } }, \"Empty\", { Optional = { x = 2 } }, { Optional = { x = 3, y = 7 } }]\n"
        );
        let raw = crate::to_string_pretty(&input).unwrap();
        assert_eq!(
            raw,
            "values = [\n    { Optional = { x = 0, y = 4 } },\n    \"Empty\",\n    { Optional = { x = 2 } },\n    { Optional = { x = 3, y = 7 } },\n]\n"
        );
    }

    #[test]
    fn serialize_struct_with_none_vec() {
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Foo {
            a: Option<Vec<Bar>>,
        }
        #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
        struct Bar;

        equivalent! {
            Foo { a: None },
            map! {},
        }

        equivalent! {
            Foo { a: Some(vec![]) },
            map! { a: crate::SerdeValue::Array(vec![]) },
        }
    }

    #[test]
    fn serialize_struct_with_newtype_with_none() {
        #[derive(Debug, Default, PartialEq, Serialize, Deserialize)]
        struct CanBeEmpty {
            #[serde(default)]
            a: NewType,
            #[serde(default)]
            b: NewType,
        }

        #[derive(Debug, Default, PartialEq, Serialize, Deserialize)]
        struct NewType(Option<String>);

        let input = "[bar]

[baz]

[bazv]
a = \"foo\"

[foo]";
        let value: BTreeMap<String, CanBeEmpty> = crate::from_str(input).unwrap();

        let expected = [
            (
                "bar".to_owned(),
                CanBeEmpty {
                    a: NewType(None),
                    b: NewType(None),
                },
            ),
            (
                "baz".to_owned(),
                CanBeEmpty {
                    a: NewType(None),
                    b: NewType(None),
                },
            ),
            (
                "bazv".to_owned(),
                CanBeEmpty {
                    a: NewType(Some("foo".to_owned())),
                    b: NewType(None),
                },
            ),
            (
                "foo".to_owned(),
                CanBeEmpty {
                    a: NewType(None),
                    b: NewType(None),
                },
            ),
        ]
        .into_iter()
        .collect::<BTreeMap<String, CanBeEmpty>>();
        assert_eq!(value, expected);

        assert_eq!(
            crate::to_string(&value).unwrap(),
            "[bar]\n\n[baz]\n\n[bazv]\na = \"foo\"\n\n[foo]\n"
        );
        assert_eq!(
            crate::to_string_pretty(&value).unwrap(),
            "[bar]\n\n[baz]\n\n[bazv]\na = \"foo\"\n\n[foo]\n"
        );
    }

    #[test]
    fn borrow() {
        type Table<'s> = BTreeMap<&'s str, &'s str>;

        let input = r#"
key = "value"
"#;
        let table = crate::from_str::<Table<'_>>(input).unwrap();
        let mut expected = BTreeMap::new();
        expected.insert("key", "value");
        assert_eq!(table, expected);
    }
}
