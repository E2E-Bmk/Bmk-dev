mod env_pipeline {
use config::{Config, Environment, Map};
use serde::Deserialize;

// Snapshots are injected through Environment::source so no process state is
// touched; upstream exercised the same pipeline through temp-env.
fn env_of(pairs: &[(&str, &str)]) -> Option<Map<String, String>> {
    let mut m = Map::new();
    for (k, v) in pairs {
        m.insert((*k).to_owned(), (*v).to_owned());
    }
    Some(m)
}

#[test]
fn test_parse_int() {
    // using a struct in an enum here to make serde use `deserialize_any`
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestIntEnum {
        Int(TestInt),
    }

    #[derive(Deserialize, Debug)]
    struct TestInt {
        int_val: i32,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[("INT_VAL", "42")]));

    let config = Config::builder()
        .set_default("tag", "Int")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestIntEnum = config.try_deserialize().unwrap();

    assert!(matches!(config, TestIntEnum::Int(TestInt { int_val: 42 })));
}

#[test]
fn test_parse_uint() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestUintEnum {
        Uint(TestUint),
    }

    #[derive(Deserialize, Debug)]
    struct TestUint {
        int_val: u32,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[("INT_VAL", "42")]));

    let config = Config::builder()
        .set_default("tag", "Uint")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestUintEnum = config.try_deserialize().unwrap();

    assert!(matches!(
        config,
        TestUintEnum::Uint(TestUint { int_val: 42 })
    ));
}

#[test]
fn test_parse_float() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestFloatEnum {
        Float(TestFloat),
    }

    #[derive(Deserialize, Debug)]
    struct TestFloat {
        float_val: f64,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[("FLOAT_VAL", "42.3")]));

    let config = Config::builder()
        .set_default("tag", "Float")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestFloatEnum = config.try_deserialize().unwrap();

    match config {
        TestFloatEnum::Float(TestFloat { float_val }) => {
            assert!((float_val - 42.3).abs() < 1e-12);
        }
    }
}

#[test]
fn test_parse_bool() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestBoolEnum {
        Bool(TestBool),
    }

    #[derive(Deserialize, Debug)]
    struct TestBool {
        bool_val: bool,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[("BOOL_VAL", "true")]));

    let config = Config::builder()
        .set_default("tag", "Bool")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestBoolEnum = config.try_deserialize().unwrap();

    assert!(matches!(
        config,
        TestBoolEnum::Bool(TestBool { bool_val: true })
    ));
}

#[test]
fn test_parse_off_int() {
    // Without try_parsing the value stays a string, and a self-describing
    // target does not coerce it into an integer.
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestIntEnum {
        #[allow(dead_code)]
        Int(TestInt),
    }

    #[derive(Deserialize, Debug)]
    struct TestInt {
        #[allow(dead_code)]
        int_val_1: i32,
    }

    let environment = Environment::default()
        .try_parsing(false)
        .source(env_of(&[("INT_VAL_1", "42")]));

    let config = Config::builder()
        .set_default("tag", "Int")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    assert!(config.try_deserialize::<TestIntEnum>().is_err());
}

#[test]
fn test_parse_off_float() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestFloatEnum {
        #[allow(dead_code)]
        Float(TestFloat),
    }

    #[derive(Deserialize, Debug)]
    struct TestFloat {
        #[allow(dead_code)]
        float_val_1: f64,
    }

    let environment = Environment::default()
        .try_parsing(false)
        .source(env_of(&[("FLOAT_VAL_1", "42.3")]));

    let config = Config::builder()
        .set_default("tag", "Float")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    assert!(config.try_deserialize::<TestFloatEnum>().is_err());
}

#[test]
fn test_parse_off_bool() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestBoolEnum {
        #[allow(dead_code)]
        Bool(TestBool),
    }

    #[derive(Deserialize, Debug)]
    struct TestBool {
        #[allow(dead_code)]
        bool_val_1: bool,
    }

    let environment = Environment::default()
        .try_parsing(false)
        .source(env_of(&[("BOOL_VAL_1", "true")]));

    let config = Config::builder()
        .set_default("tag", "Bool")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    assert!(config.try_deserialize::<TestBoolEnum>().is_err());
}

#[test]
fn test_parse_int_fail() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestIntEnum {
        #[allow(dead_code)]
        Int(TestInt),
    }

    #[derive(Deserialize, Debug)]
    struct TestInt {
        #[allow(dead_code)]
        int_val_2: i32,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[("INT_VAL_2", "not an int")]));

    let config = Config::builder()
        .set_default("tag", "Int")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    assert!(config.try_deserialize::<TestIntEnum>().is_err());
}

#[test]
fn test_parse_string_and_list() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestStringEnum {
        String(TestString),
    }

    #[derive(Deserialize, Debug)]
    struct TestString {
        string_val: String,
        string_list: Vec<String>,
    }

    let environment = Environment::default()
        .prefix("LIST")
        .list_separator(",")
        .with_list_parse_key("string_list")
        .try_parsing(true)
        .source(env_of(&[
            ("LIST_STRING_LIST", "test,string"),
            ("LIST_STRING_VAL", "test,string"),
        ]));

    let config = Config::builder()
        .set_default("tag", "String")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestStringEnum = config.try_deserialize().unwrap();

    match config {
        TestStringEnum::String(TestString {
            string_val,
            string_list,
        }) => {
            assert_eq!(String::from("test,string"), string_val);
            assert_eq!(
                vec![String::from("test"), String::from("string")],
                string_list
            );
        }
    }
}

#[test]
fn test_parse_string_and_list_ignores_list_parse_key_case() {
    // The registered list key is compared against the normalized
    // (lowercased) key, so an upper-case registration matches nothing.
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    #[allow(dead_code)]
    enum TestStringEnum {
        String(TestString),
    }

    #[derive(Deserialize, Debug)]
    #[allow(dead_code)]
    struct TestString {
        string_val: String,
        string_list: Vec<String>,
    }

    let environment = Environment::default()
        .prefix("LIST")
        .list_separator(",")
        .with_list_parse_key("STRING_LIST")
        .try_parsing(true)
        .source(env_of(&[
            ("LIST_STRING_LIST", "test,string"),
            ("LIST_STRING_VAL", "test,string"),
        ]));

    let config = Config::builder()
        .set_default("tag", "String")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let res = config.try_deserialize::<TestStringEnum>();
    assert!(res.is_err());
}

#[test]
fn test_parse_string() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestStringEnum {
        String(TestString),
    }

    #[derive(Deserialize, Debug)]
    struct TestString {
        string_val: String,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[("STRING_VAL", "test string")]));

    let config = Config::builder()
        .set_default("tag", "String")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestStringEnum = config.try_deserialize().unwrap();

    let test_string = String::from("test string");

    match config {
        TestStringEnum::String(TestString { string_val }) => {
            assert_eq!(test_string, string_val);
        }
    }
}

#[test]
fn test_parse_string_list() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestListEnum {
        StringList(TestList),
    }

    #[derive(Deserialize, Debug)]
    struct TestList {
        string_list: Vec<String>,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .list_separator(" ")
        .source(env_of(&[("STRING_LIST", "test string")]));

    let config = Config::builder()
        .set_default("tag", "StringList")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestListEnum = config.try_deserialize().unwrap();

    let test_string = vec![String::from("test"), String::from("string")];

    match config {
        TestListEnum::StringList(TestList { string_list }) => {
            assert_eq!(test_string, string_list);
        }
    }
}

#[test]
fn test_parse_off_string() {
    #[derive(Deserialize, Debug)]
    #[serde(tag = "tag")]
    enum TestStringEnum {
        String(TestString),
    }

    #[derive(Deserialize, Debug)]
    struct TestString {
        string_val_1: String,
    }

    let environment = Environment::default()
        .try_parsing(false)
        .source(env_of(&[("STRING_VAL_1", "test string")]));

    let config = Config::builder()
        .set_default("tag", "String")
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestStringEnum = config.try_deserialize().unwrap();

    let test_string = String::from("test string");

    match config {
        TestStringEnum::String(TestString { string_val_1 }) => {
            assert_eq!(test_string, string_val_1);
        }
    }
}

#[test]
fn test_parse_int_default() {
    #[derive(Deserialize, Debug)]
    struct TestInt {
        int_val: i32,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[]));

    let config = Config::builder()
        .set_default("int_val", 42_i32)
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestInt = config.try_deserialize().unwrap();
    assert_eq!(config.int_val, 42);
}

#[test]
fn test_parse_uint_default() {
    #[derive(Deserialize, Debug)]
    struct TestUint {
        int_val: u32,
    }

    let environment = Environment::default()
        .try_parsing(true)
        .source(env_of(&[]));

    let config = Config::builder()
        .set_default("int_val", 42_u32)
        .unwrap()
        .add_source(environment)
        .build()
        .unwrap();

    let config: TestUint = config.try_deserialize().unwrap();
    assert_eq!(config.int_val, 42);
}
}
