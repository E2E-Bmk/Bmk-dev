// Rewritten upstream tests: toml::de serde mapping (de_enum, de_errors, de_key).
// Source: repo-pool/toml-fullrepro-001 crates/toml/tests/serde/{de_enum,de_errors,de_key}.rs
// Rewrites: snapbox/to_debug asserts -> assert_eq on PartialEq values; exact error
// message text -> error-type-only is_err (spec Error Semantics: error categories, not
// text); all entry points in spec Import Surface (toml::from_str, toml::de::ValueDeserializer).
// Helpers (from_str, value_from_str, t!) are defined at crate root (see lib.rs).

mod toml_serde_de {

use std::collections::BTreeMap;
use std::fmt;

use serde::Deserialize;
use serde::de;

// ===== de_enum =====

#[derive(Debug, Deserialize, PartialEq)]
struct OuterStruct {
    inner: TheEnum,
}

#[derive(Debug, Deserialize, PartialEq)]
enum TheEnum {
    Plain,
    Tuple(i64, bool),
    NewType(String),
    Struct { value: i64 },
}

#[derive(Debug, Deserialize, PartialEq)]
struct Val {
    val: TheEnum,
}

#[derive(Debug, Deserialize, PartialEq)]
struct Multi {
    enums: Vec<TheEnum>,
}

#[test]
fn de_enum_invalid_variant_returns_error_string() {
    let input = "\"NonExistent\"";
    assert!(crate::value_from_str::<TheEnum>(input).is_err());

    let input = "val = \"NonExistent\"";
    assert!(crate::from_str::<Val>(input).is_err());
}

#[test]
fn de_enum_invalid_variant_returns_error_inline_table() {
    let input = "{ NonExistent = {} }";
    assert!(crate::value_from_str::<TheEnum>(input).is_err());

    let input = "val = { NonExistent = {} }";
    assert!(crate::from_str::<Val>(input).is_err());
}

#[test]
fn de_enum_unit_value_from_str() {
    let input = "\"Plain\"";
    assert_eq!(
        crate::value_from_str::<TheEnum>(input).unwrap(),
        TheEnum::Plain
    );
}

#[test]
fn de_enum_unit_from_str() {
    let input = "val = \"Plain\"";
    assert_eq!(
        crate::from_str::<Val>(input).unwrap(),
        Val {
            val: TheEnum::Plain
        }
    );
}

#[test]
fn de_enum_unit_from_inline_table() {
    let input = "val = { Plain = {} }";
    assert_eq!(
        crate::from_str::<Val>(input).unwrap(),
        Val {
            val: TheEnum::Plain
        }
    );
}

#[test]
fn de_enum_unit_extra_field_returns_error() {
    let input = "{ Plain = { extra_field = 404 } }";
    assert!(crate::value_from_str::<TheEnum>(input).is_err());

    let input = "val = { Plain = { extra_field = 404 } }";
    assert!(crate::from_str::<Val>(input).is_err());
}

#[test]
fn de_enum_tuple_from_inline_table() {
    let input = "val = { Tuple = { 0 = -123, 1 = true } }";
    assert_eq!(
        crate::from_str::<Val>(input).unwrap(),
        Val {
            val: TheEnum::Tuple(-123, true)
        }
    );
}

#[test]
fn de_enum_tuple_from_std_table() {
    let input = r#"[Tuple]
                0 = -123
                1 = true
                "#;
    assert_eq!(
        crate::from_str::<TheEnum>(input).unwrap(),
        TheEnum::Tuple(-123, true)
    );
}

#[test]
fn de_enum_newtype_from_inline_table() {
    let input = r#"val = { NewType = "value" }"#;
    assert_eq!(
        crate::from_str::<Val>(input).unwrap(),
        Val {
            val: TheEnum::NewType("value".to_owned())
        }
    );
}

#[test]
fn de_enum_newtype_from_std_table() {
    let result = crate::from_str::<TheEnum>(r#"NewType = "value""#);
    assert_eq!(result.unwrap(), TheEnum::NewType("value".to_owned()));

    let result = crate::from_str::<Val>(
        r#"[val]
                NewType = "value"
                "#,
    );
    assert_eq!(
        result.unwrap(),
        Val {
            val: TheEnum::NewType("value".to_owned())
        }
    );
}

#[test]
fn de_enum_struct_from_std_table() {
    let input = r#"[Struct]
                value = -123
                "#;
    assert_eq!(
        crate::from_str::<TheEnum>(input).unwrap(),
        TheEnum::Struct { value: -123 }
    );
}

#[test]
fn de_enum_struct_from_nested_std_table() {
    let input = r#"[inner.Struct]
                value = -123
                "#;
    assert_eq!(
        crate::from_str::<OuterStruct>(input).unwrap(),
        OuterStruct {
            inner: TheEnum::Struct { value: -123 }
        }
    );
}

#[test]
fn de_enum_struct_extra_field_returns_error() {
    let input = "{ Struct = { value = 123, extra_0 = 0, extra_1 = 1 } }";
    assert!(crate::value_from_str::<TheEnum>(input).is_err());

    let input = "val = { Struct = { value = 123, extra_0 = 0, extra_1 = 1 } }";
    assert!(crate::from_str::<Val>(input).is_err());
}

#[test]
fn de_enum_array_from_std_table() {
    let input = r#"[[enums]]
            Plain = {}

            [[enums]]
            Tuple = { 0 = -123, 1 = true }

            [[enums]]
            NewType = "value"

            [[enums]]
            Struct = { value = -123 }
            "#;
    assert_eq!(
        crate::from_str::<Multi>(input).unwrap(),
        Multi {
            enums: vec![
                TheEnum::Plain,
                TheEnum::Tuple(-123, true),
                TheEnum::NewType("value".to_owned()),
                TheEnum::Struct { value: -123 },
            ],
        }
    );
}

// ===== de_errors =====

#[track_caller]
fn bad<T: de::DeserializeOwned + fmt::Debug>(toml: &str) {
    match crate::from_str::<T>(toml) {
        Ok(s) => panic!("parsed to: {s:#?}"),
        Err(_) => {}
    }
}

#[derive(Debug, Deserialize, PartialEq)]
struct Parent<T> {
    p_a: T,
    p_b: Vec<Child<T>>,
}

#[derive(Debug, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
struct Child<T> {
    c_a: T,
    c_b: T,
}

#[derive(Debug, PartialEq)]
enum CasedString {
    Lowercase(String),
    Uppercase(String),
}

impl<'de> Deserialize<'de> for CasedString {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: de::Deserializer<'de>,
    {
        struct CasedStringVisitor;

        impl de::Visitor<'_> for CasedStringVisitor {
            type Value = CasedString;

            fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str("a string")
            }

            fn visit_str<E>(self, s: &str) -> Result<Self::Value, E>
            where
                E: de::Error,
            {
                if s.is_empty() {
                    Err(de::Error::invalid_length(0, &"a non-empty string"))
                } else if s.chars().all(|x| x.is_ascii_lowercase()) {
                    Ok(CasedString::Lowercase(s.to_owned()))
                } else if s.chars().all(|x| x.is_ascii_uppercase()) {
                    Ok(CasedString::Uppercase(s.to_owned()))
                } else {
                    Err(de::Error::invalid_value(
                        de::Unexpected::Str(s),
                        &"all lowercase or all uppercase",
                    ))
                }
            }
        }

        deserializer.deserialize_any(CasedStringVisitor)
    }
}

#[test]
fn de_errors_custom_errors() {
    let input = "
            p_a = 'a'
            p_b = [{c_a = 'a', c_b = 'c'}]
        ";
    crate::from_str::<Parent<CasedString>>(input).unwrap();

    // Custom error at p_b value.
    bad::<Parent<CasedString>>(
        "
            p_a = ''
        ",
    );

    // Missing field in table.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
        ",
    );

    // Invalid type in p_b.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            p_b = 1
        ",
    );

    // Sub-table in Vec is missing a field.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            p_b = [
                {c_a = 'a'}
            ]
        ",
    );

    // Sub-table in Vec has a field with a bad value.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            p_b = [
                {c_a = 'a', c_b = '*'}
            ]
        ",
    );

    // Sub-table in Vec is missing a field.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            p_b = [
                {c_a = 'a', c_b = 'b'},
                {c_a = 'aa'}
            ]
        ",
    );

    // Sub-table in the middle of a Vec is missing a field.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            p_b = [
                {c_a = 'a', c_b = 'b'},
                {c_a = 'aa'},
                {c_a = 'aaa', c_b = 'bbb'},
            ]
        ",
    );

    // Sub-table in the middle of a Vec has a field with a bad value.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            p_b = [
                {c_a = 'a', c_b = 'b'},
                {c_a = 'aa', c_b = 1},
                {c_a = 'aaa', c_b = 'bbb'},
            ]
        ",
    );

    // Sub-table in the middle of a Vec has an extra field.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            p_b = [
                {c_a = 'a', c_b = 'b'},
                {c_a = 'aa', c_b = 'bb', c_d = 'd'},
                {c_a = 'aaa', c_b = 'bbb'},
                {c_a = 'aaaa', c_b = 'bbbb'},
            ]
        ",
    );

    // Sub-table in the middle of a Vec is missing a field.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            [[p_b]]
            c_a = 'a'
            c_b = 'b'
            [[p_b]]
            c_a = 'aa'
            [[p_b]]
            c_a = 'aaa'
            c_b = 'bbb'
            [[p_b]]
            c_a = 'aaaa'
            c_b = 'bbbb'
        ",
    );

    // Sub-table in the middle of a Vec has a field with a bad value.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            [[p_b]]
            c_a = 'a'
            c_b = 'b'
            [[p_b]]
            c_a = 'aa'
            c_b = '*'
            [[p_b]]
            c_a = 'aaa'
            c_b = 'bbb'
        ",
    );

    // Sub-table in the middle of a Vec has an extra field.
    bad::<Parent<CasedString>>(
        "
            p_a = 'a'
            [[p_b]]
            c_a = 'a'
            c_b = 'b'
            [[p_b]]
            c_a = 'aa'
            c_d = 'dd' # unknown field
            [[p_b]]
            c_a = 'aaa'
            c_b = 'bbb'
            [[p_b]]
            c_a = 'aaaa'
            c_b = 'bbbb'
        ",
    );
}

#[test]
fn de_errors_serde_derive_deserialize_errors() {
    bad::<Parent<String>>(
        "
            p_a = ''
        ",
    );

    bad::<Parent<String>>(
        "
            p_a = ''
            p_b = [
                {c_a = ''}
            ]
        ",
    );

    bad::<Parent<String>>(
        "
            p_a = ''
            p_b = [
                {c_a = '', c_b = 1}
            ]
        ",
    );

    bad::<Parent<String>>(
        "
            p_a = ''
            p_b = [
                {c_a = '', c_b = '', c_d = ''},
            ]
        ",
    );

    bad::<Parent<String>>(
        "
            p_a = 'a'
            p_b = [
                {c_a = '', c_b = 1, c_d = ''},
            ]
        ",
    );
}

// ===== de_key =====

type Map<K> = BTreeMap<K, String>;

#[derive(Debug, Deserialize, PartialEq)]
struct Document<K: Ord> {
    map: Map<K>,
}

mod de_key_string {
    use super::*;

    type Map = super::Map<String>;
    type Document = super::Document<String>;

    #[test]
    fn from_str() {
        let input = "key = 'value'";
        let expected = [("key".to_owned(), "value".to_owned())]
            .into_iter()
            .collect::<Map>();
        assert_eq!(crate::from_str::<Map>(input).unwrap(), expected);
    }

    #[test]
    fn value_from_inline_table() {
        let input = "{ key = 'value' }";
        let expected = [("key".to_owned(), "value".to_owned())]
            .into_iter()
            .collect::<Map>();
        assert_eq!(crate::value_from_str::<Map>(input).unwrap(), expected);
    }

    #[test]
    fn from_inline_table() {
        let input = "map = { key = 'value' }";
        let expected = Document {
            map: [("key".to_owned(), "value".to_owned())]
                .into_iter()
                .collect::<Map>(),
        };
        assert_eq!(crate::from_str::<Document>(input).unwrap(), expected);
    }

    #[test]
    fn from_std_table() {
        let input = "[map]
key = 'value'";
        let expected = Document {
            map: [("key".to_owned(), "value".to_owned())]
                .into_iter()
                .collect::<Map>(),
        };
        assert_eq!(crate::from_str::<Document>(input).unwrap(), expected);
    }
}

mod de_key_bool {
    use super::*;

    type Map = super::Map<bool>;
    type Document = super::Document<bool>;

    #[test]
    fn from_str() {
        let input = "'false' = 'value'";
        let expected = [(false, "value".to_owned())].into_iter().collect::<Map>();
        assert_eq!(crate::from_str::<Map>(input).unwrap(), expected);
    }

    #[test]
    fn value_from_inline_table() {
        let input = "{ 'false' = 'value' }";
        let expected = [(false, "value".to_owned())].into_iter().collect::<Map>();
        assert_eq!(crate::value_from_str::<Map>(input).unwrap(), expected);
    }

    #[test]
    fn from_inline_table() {
        let input = "map = { 'false' = 'value' }";
        let expected = Document {
            map: [(false, "value".to_owned())].into_iter().collect::<Map>(),
        };
        assert_eq!(crate::from_str::<Document>(input).unwrap(), expected);
    }

    #[test]
    fn from_std_table() {
        let input = "[map]
'false' = 'value'";
        let expected = Document {
            map: [(false, "value".to_owned())].into_iter().collect::<Map>(),
        };
        assert_eq!(crate::from_str::<Document>(input).unwrap(), expected);
    }
}

mod de_key_i16 {
    use super::*;

    type Map = super::Map<i16>;
    type Document = super::Document<i16>;

    #[test]
    fn from_str() {
        let input = "'42' = 'value'";
        let expected = [(42i16, "value".to_owned())].into_iter().collect::<Map>();
        assert_eq!(crate::from_str::<Map>(input).unwrap(), expected);
    }

    #[test]
    fn value_from_inline_table() {
        let input = "{ '42' = 'value' }";
        let expected = [(42i16, "value".to_owned())].into_iter().collect::<Map>();
        assert_eq!(crate::value_from_str::<Map>(input).unwrap(), expected);
    }

    #[test]
    fn from_inline_table() {
        let input = "map = { '42' = 'value' }";
        let expected = Document {
            map: [(42i16, "value".to_owned())].into_iter().collect::<Map>(),
        };
        assert_eq!(crate::from_str::<Document>(input).unwrap(), expected);
    }

    #[test]
    fn from_std_table() {
        let input = "[map]
'42' = 'value'";
        let expected = Document {
            map: [(42i16, "value".to_owned())].into_iter().collect::<Map>(),
        };
        assert_eq!(crate::from_str::<Document>(input).unwrap(), expected);
    }
}

}
