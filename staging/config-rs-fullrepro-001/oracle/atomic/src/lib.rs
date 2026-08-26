// Oracle atomic tests for the layered configuration engine reconstruction task.
#![cfg(test)]
#![allow(clippy::all)]

use config::{Config, ConfigError, Environment, File, FileFormat, Map, Source, Value};
use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------- lookups

#[test]
fn test_not_found() {
    let c = Config::builder()
        .add_source(File::from_str("{}", FileFormat::Json))
        .build()
        .unwrap();
    let res = c.get::<bool>("not_found");

    assert!(matches!(
        res,
        Err(ConfigError::NotFound(key)) if key == "not_found"
    ));
}

#[test]
fn test_scalar() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
    "debug": true,
    "production": false
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    assert_eq!(c.get("debug").ok(), Some(true));
    assert_eq!(c.get("production").ok(), Some(false));
}

#[test]
fn test_scalar_type_loose() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
    "debug": true,
    "debug_s": "true",
    "production": false,
    "production_s": "false"
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    assert_eq!(c.get("debug").ok(), Some(true));
    assert_eq!(c.get("debug").ok(), Some("true".to_owned()));
    assert_eq!(c.get("debug").ok(), Some(1));
    assert_eq!(c.get("debug").ok(), Some(1.0));

    assert_eq!(c.get("debug_s").ok(), Some(true));
    assert_eq!(c.get("debug_s").ok(), Some("true".to_owned()));
    assert_eq!(c.get("debug_s").ok(), Some(1));
    assert_eq!(c.get("debug_s").ok(), Some(1.0));

    assert_eq!(c.get("production").ok(), Some(false));
    assert_eq!(c.get("production").ok(), Some("false".to_owned()));
    assert_eq!(c.get("production").ok(), Some(0));
    assert_eq!(c.get("production").ok(), Some(0.0));

    assert_eq!(c.get("production_s").ok(), Some(false));
    assert_eq!(c.get("production_s").ok(), Some("false".to_owned()));
    assert_eq!(c.get("production_s").ok(), Some(0));
    assert_eq!(c.get("production_s").ok(), Some(0.0));
}

#[test]
fn test_get_scalar_path() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "place": {
    "favorite": false,
    "creator": {
      "name": "John Smith"
    }
  }
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    assert_eq!(c.get("place.favorite").ok(), Some(false));
    assert_eq!(
        c.get("place.creator.name").ok(),
        Some("John Smith".to_owned())
    );
}

#[test]
fn test_get_scalar_path_subscript() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "arr": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "items": [
    { "name": "1" },
    { "name": "2" }
  ]
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    assert_eq!(c.get("arr[2]").ok(), Some(3));
    assert_eq!(c.get("items[0].name").ok(), Some("1".to_owned()));
    assert_eq!(c.get("items[1].name").ok(), Some("2".to_owned()));
    assert_eq!(c.get("items[-1].name").ok(), Some("2".to_owned()));
    assert_eq!(c.get("items[-2].name").ok(), Some("1".to_owned()));
}

#[test]
fn test_map() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "place": {
    "number": 1,
    "name": "Torre di Pisa",
    "longitude": 43.7224985,
    "latitude": 10.3970522,
    "favorite": false,
    "reviews": 3866,
    "rating": 4.5,
    "creator": {
      "name": "John Smith",
      "username": "jsmith",
      "email": "jsmith@localhost"
    }
  }
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let m: Map<String, Value> = c.get("place").unwrap();

    assert_eq!(m.len(), 8);
    assert_eq!(
        m["name"].clone().into_string().unwrap(),
        "Torre di Pisa".to_owned()
    );
    assert_eq!(m["reviews"].clone().into_int().unwrap(), 3866);
}

#[test]
fn test_map_str() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "place": {
    "creator": {
      "name": "John Smith",
      "username": "jsmith",
      "email": "jsmith@localhost"
    }
  }
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let m: Map<String, String> = c.get("place.creator").unwrap();

    assert_eq!(m.len(), 3);
    assert_eq!(m["name"], "John Smith".to_owned());
}

#[test]
fn test_array_scalar() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "arr": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let arr: Vec<i64> = c.get("arr").unwrap();

    assert_eq!(arr.len(), 10);
    assert_eq!(arr[3], 4);
}

// ------------------------------------------------------- defaults/overrides

#[test]
fn test_set_override_scalar() {
    let config = Config::builder()
        .set_override("value", true)
        .and_then(|b| b.build())
        .unwrap();

    assert_eq!(config.get("value").ok(), Some(true));
}

#[test]
fn test_set_scalar_default() {
    let config = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "debug": true
}
"#,
            FileFormat::Json,
        ))
        .set_default("debug", false)
        .unwrap()
        .set_default("staging", false)
        .unwrap()
        .build()
        .unwrap();

    assert_eq!(config.get("debug").ok(), Some(true));
    assert_eq!(config.get("staging").ok(), Some(false));
}

#[test]
fn test_set_scalar_path() {
    let config = Config::builder()
        .set_override("first.second.third", true)
        .unwrap()
        .add_source(File::from_str(
            r#"
{
  "place": {
    "favorite": false
  }
}
"#,
            FileFormat::Json,
        ))
        .set_default("place.favorite", true)
        .unwrap()
        .set_default("place.blocked", true)
        .unwrap()
        .build()
        .unwrap();

    assert_eq!(config.get("first.second.third").ok(), Some(true));
    assert_eq!(config.get("place.favorite").ok(), Some(false));
    assert_eq!(config.get("place.blocked").ok(), Some(true));
}

#[test]
fn test_set_arr_path() {
    let config = Config::builder()
        .set_override("present[0].name", "Ivan")
        .unwrap()
        .set_override("absent[0].things[1].name", "foo")
        .unwrap()
        .set_override("absent[0].things[1].value", 42)
        .unwrap()
        .set_override("absent[1]", 0)
        .unwrap()
        .set_override("present[2]", "George")
        .unwrap()
        .set_override("reverse[-1]", "Bob")
        .unwrap()
        .set_override("reverse[-2]", "Alice")
        .unwrap()
        .set_override("empty[-1]", "Bob")
        .unwrap()
        .set_override("empty[-2]", "Alice")
        .unwrap()
        .add_source(File::from_str(
            r#"
{
  "present": [
    {
      "name": "1"
    },
    {
      "name": "2"
    }
  ],
  "reverse": [
    {
      "name": "l1"
    },
    {
      "name": "l2"
    }
  ],
  "empty": []
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    assert_eq!(config.get("present[0].name").ok(), Some("Ivan".to_owned()));
    assert_eq!(
        config.get("absent[0].things[1].name").ok(),
        Some("foo".to_owned())
    );
    assert_eq!(config.get("absent[0].things[1].value").ok(), Some(42));
    assert_eq!(config.get("absent[1]").ok(), Some(0));
    assert_eq!(config.get("present[2]").ok(), Some("George".to_owned()));
    assert_eq!(config.get("reverse[1]").ok(), Some("Bob".to_owned()));
    assert_eq!(config.get("reverse[0]").ok(), Some("Alice".to_owned()));
    assert_eq!(config.get("empty[1]").ok(), Some("Bob".to_owned()));
    assert_eq!(config.get("empty[0]").ok(), Some("Alice".to_owned()));
}

#[test]
fn test_set_capital() {
    let config = Config::builder()
        .set_default("this", false)
        .unwrap()
        .set_override("ThAt", true)
        .unwrap()
        .add_source(File::from_str("{\"logLevel\": 5}", FileFormat::Json))
        .build()
        .unwrap();

    assert_eq!(config.get::<bool>("this").unwrap(), false);
    assert_eq!(config.get::<bool>("ThAt").unwrap(), true);
    assert_eq!(config.get::<usize>("logLevel").unwrap(), 5);
}

#[test]
fn generated_set_default_path_parse_error() {
    let res = Config::builder().set_default("outer..inner", 7);
    assert!(matches!(res, Err(ConfigError::PathParse { .. })));

    let res = Config::builder().set_override("outer..inner", 7);
    assert!(matches!(res, Err(ConfigError::PathParse { .. })));
}

// ------------------------------------------------------------ deserialization

#[derive(Debug, Serialize, Deserialize)]
#[serde(default)]
pub struct DefaultedSettings {
    pub db_host: String,
}

impl Default for DefaultedSettings {
    fn default() -> Self {
        Self {
            db_host: String::from("default"),
        }
    }
}

#[test]
fn set_defaults() {
    let c = Config::default();
    let s: DefaultedSettings = c.try_deserialize().expect("Deserialization failed");

    assert_eq!(s.db_host, "default");
}

#[test]
fn try_from_defaults() {
    let c = Config::try_from(&DefaultedSettings::default()).expect("Serialization failed");
    let s: DefaultedSettings = c.try_deserialize().expect("Deserialization failed");
    assert_eq!(s.db_host, "default");
}

#[test]
fn empty_deserializes() {
    #[derive(Debug, Serialize, Deserialize)]
    struct Settings {
        #[serde(skip)]
        foo: isize,
        #[serde(skip)]
        bar: u8,
    }

    let s: Settings = Config::default()
        .try_deserialize()
        .expect("Deserialization failed");
    assert_eq!(s.foo, 0);
    assert_eq!(s.bar, 0);
}

// --------------------------------------------------------------- weird keys

fn config_as<'a, T>(config: &str, format: FileFormat) -> T
where
    T: Deserialize<'a> + std::fmt::Debug,
{
    let cfg = config::Config::builder()
        .add_source(File::from_str(config, format))
        .build();

    assert!(cfg.is_ok(), "Config could not be built");
    let cfg = cfg.unwrap().try_deserialize();

    assert!(cfg.is_ok(), "Config could not be transformed");
    let cfg: T = cfg.unwrap();
    cfg
}

#[test]
fn test_colon_key_json() {
    #[derive(Debug, Serialize, Deserialize)]
    struct SettingsColon {
        #[serde(rename = "foo:foo")]
        foo: u8,

        bar: u8,
    }

    let config = r#" {"foo:foo": 8, "bar": 12 } "#;

    let cfg = config_as::<SettingsColon>(config, FileFormat::Json);
    assert_eq!(cfg.foo, 8);
    assert_eq!(cfg.bar, 12);
}

#[test]
fn test_slash_key_json() {
    #[derive(Debug, Serialize, Deserialize)]
    struct SettingsSlash {
        #[serde(rename = "foo/foo")]
        foo: u8,
        bar: u8,
    }

    let config = r#" {"foo/foo": 8, "bar": 12 } "#;

    let cfg = config_as::<SettingsSlash>(config, FileFormat::Json);
    assert_eq!(cfg.foo, 8);
    assert_eq!(cfg.bar, 12);
}

#[test]
fn test_doublebackslash_key_json() {
    #[derive(Debug, Serialize, Deserialize)]
    struct SettingsDoubleBackslash {
        #[serde(rename = "foo\\foo")]
        foo: u8,
        bar: u8,
    }

    let config = r#" {"foo\\foo": 8, "bar": 12 } "#;

    let cfg = config_as::<SettingsDoubleBackslash>(config, FileFormat::Json);
    assert_eq!(cfg.foo, 8);
    assert_eq!(cfg.bar, 12);
}

// ------------------------------------------------------------ integer range

#[test]
fn wrapping_u16() {
    let c = Config::builder()
        .add_source(config::File::from_str(
            r#"
{
    "settings": {
        "port": 66000
    }
}
"#,
            config::FileFormat::Json,
        ))
        .build()
        .unwrap();

    let res = c.get::<u16>("settings.port");
    assert!(matches!(res, Err(ConfigError::Type { .. })));
}

#[test]
fn nonwrapping_u32() {
    let c = Config::builder()
        .add_source(config::File::from_str(
            r#"
{
    "settings": {
        "port": 66000
    }
}
"#,
            config::FileFormat::Json,
        ))
        .build()
        .unwrap();

    let port: u32 = c.get("settings.port").unwrap();
    assert_eq!(port, 66000);
}

#[test]
fn invalid_signedness() {
    let c = Config::builder()
        .add_source(config::File::from_str(
            r#"
{
    "settings": {
        "port": -1
    }
}
"#,
            config::FileFormat::Json,
        ))
        .build()
        .unwrap();

    let res = c.get::<u32>("settings.port");
    assert!(matches!(res, Err(ConfigError::Type { .. })));
}

#[test]
fn test_deser_unsigned_int_hm() {
    #[derive(serde::Deserialize, Eq, PartialEq, Debug)]
    struct Container<T> {
        inner: T,
    }

    #[derive(serde::Deserialize, Eq, PartialEq, Debug)]
    struct Unsigned {
        unsigned: u16,
    }

    impl Default for Unsigned {
        fn default() -> Self {
            Self { unsigned: 128 }
        }
    }

    impl From<Unsigned> for config::ValueKind {
        fn from(unsigned: Unsigned) -> Self {
            let mut properties = std::collections::HashMap::new();
            properties.insert(
                "unsigned".to_owned(),
                config::Value::from(unsigned.unsigned),
            );

            Self::Table(properties)
        }
    }

    let container = Container {
        inner: Unsigned::default(),
    };

    let built = config::Config::builder()
        .set_default("inner", Unsigned::default())
        .unwrap()
        .build()
        .unwrap()
        .try_deserialize::<Container<Unsigned>>()
        .unwrap();

    assert_eq!(container, built);
}

// -------------------------------------------------- environment normalization
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
fn env_default_lowercases_keys() {
    let environment = Environment::default().source(env_of(&[("A_B_C", "abc")]));

    assert!(environment.collect().unwrap().contains_key("a_b_c"));
}

#[test]
fn env_prefix_is_removed_from_key() {
    let environment = Environment::with_prefix("B").source(env_of(&[("B_A_C", "abc")]));

    assert!(environment.collect().unwrap().contains_key("a_c"));
}

#[test]
fn env_prefix_matches_variant_spellings() {
    let environment = Environment::with_prefix("a").source(env_of(&[("a_A_C", "abc")]));
    assert!(environment.collect().unwrap().contains_key("a_c"));

    let environment = Environment::with_prefix("aB").source(env_of(&[("aB_A_C", "abc")]));
    assert!(environment.collect().unwrap().contains_key("a_c"));

    let environment = Environment::with_prefix("ab").source(env_of(&[("Ab_A_C", "abc")]));
    assert!(environment.collect().unwrap().contains_key("a_c"));
}

#[test]
fn env_separator_nests_keys() {
    let environment = Environment::with_prefix("C")
        .separator("_")
        .source(env_of(&[("C_B_A", "abc")]));

    assert!(environment.collect().unwrap().contains_key("b.a"));
}

#[test]
fn env_empty_value_is_ignored() {
    let environment = Environment::default()
        .ignore_empty(true)
        .source(env_of(&[("C_A_B", "")]));

    assert!(!environment.collect().unwrap().contains_key("c_a_b"));
}

#[test]
fn env_keep_prefix() {
    let pairs = &[("C_A_B", "")];

    // Do not keep the prefix
    let environment = Environment::with_prefix("C").source(env_of(pairs));
    assert!(environment.collect().unwrap().contains_key("a_b"));

    let environment = Environment::with_prefix("C")
        .keep_prefix(false)
        .source(env_of(pairs));
    assert!(environment.collect().unwrap().contains_key("a_b"));

    // Keep the prefix
    let environment = Environment::with_prefix("C")
        .keep_prefix(true)
        .source(env_of(pairs));
    assert!(environment.collect().unwrap().contains_key("c_a_b"));
}

#[test]
fn env_custom_separator() {
    let environment = Environment::with_prefix("C")
        .separator(".")
        .source(env_of(&[("C.B.A", "abc")]));

    assert!(environment.collect().unwrap().contains_key("b.a"));
}

#[test]
fn env_custom_prefix_separator() {
    let environment = Environment::with_prefix("C")
        .separator(".")
        .prefix_separator("-")
        .source(env_of(&[("C-B.A", "abc")]));

    assert!(environment.collect().unwrap().contains_key("b.a"));
}

#[test]
fn generated_env_nonmatching_prefix_skips_key() {
    let environment = Environment::with_prefix("APP").source(env_of(&[
        ("APP_PORT", "1024"),
        ("OTHER_PORT", "9"),
    ]));

    let collected = environment.collect().unwrap();
    assert!(collected.contains_key("port"));
    assert!(!collected.contains_key("other_port"));
    assert_eq!(collected.len(), 1);
}

#[test]
fn generated_env_without_parsing_keeps_strings() {
    let environment = Environment::default().source(env_of(&[("COUNT", "31")]));

    let collected = environment.collect().unwrap();
    assert_eq!(
        collected["count"].clone().into_string().unwrap(),
        "31".to_owned()
    );
}

// -------------------------------------------------------- generated: typed access

#[test]
fn generated_typed_get_forms_agree() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "flag": true,
  "count": 17,
  "ratio": 2.25,
  "label": "seventeen"
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    assert_eq!(c.get_bool("flag").unwrap(), true);
    assert_eq!(c.get_int("count").unwrap(), 17);
    assert_eq!(c.get_float("ratio").unwrap(), 2.25);
    assert_eq!(c.get_string("label").unwrap(), "seventeen");

    // coercing forms
    assert_eq!(c.get_string("flag").unwrap(), "true");
    assert_eq!(c.get_string("count").unwrap(), "17");
    assert_eq!(c.get_int("flag").unwrap(), 1);
    assert_eq!(c.get_float("count").unwrap(), 17.0);
    assert_eq!(c.get_bool("count").unwrap(), true);
}

#[test]
fn generated_get_table_and_array() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "limits": { "low": 2, "high": 11 },
  "steps": [3, 5, 8]
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let table = c.get_table("limits").unwrap();
    assert_eq!(table.len(), 2);
    assert_eq!(table["high"].clone().into_int().unwrap(), 11);

    let array = c.get_array("steps").unwrap();
    assert_eq!(array.len(), 3);
    assert_eq!(array[2].clone().into_int().unwrap(), 8);

    // scalars do not become tables or arrays
    assert!(matches!(
        c.get_table("steps"),
        Err(ConfigError::Type { .. })
    ));
    assert!(matches!(
        c.get_array("limits"),
        Err(ConfigError::Type { .. })
    ));
}

#[test]
fn generated_value_coercion_rules() {
    // string -> bool words
    let yes: Value = "on".into();
    assert_eq!(yes.into_bool().unwrap(), true);
    let no: Value = "No".into();
    assert_eq!(no.into_bool().unwrap(), false);
    let bad: Value = "definitely".into();
    assert!(matches!(bad.into_bool(), Err(ConfigError::Type { .. })));

    // string -> int words and digits
    let v: Value = "yes".into();
    assert_eq!(v.into_int().unwrap(), 1);
    let v: Value = "-41".into();
    assert_eq!(v.into_int().unwrap(), -41);

    // float -> int rounds to nearest
    let v: Value = 2.5_f64.into();
    assert_eq!(v.into_int().unwrap(), 3);
    let v: Value = (-2.5_f64).into();
    assert_eq!(v.into_int().unwrap(), -3);

    // bool -> float / string
    let v: Value = true.into();
    assert_eq!(v.into_float().unwrap(), 1.0);
    let v: Value = false.into();
    assert_eq!(v.into_string().unwrap(), "false");

    // string -> float
    let v: Value = "6.5".into();
    assert_eq!(v.into_float().unwrap(), 6.5);
    let v: Value = "off".into();
    assert_eq!(v.into_float().unwrap(), 0.0);
}

#[test]
fn generated_ini_values_are_string_leaves() {
    let c = Config::builder()
        .add_source(File::from_str(
            "\nenabled = true\ncount = 12\n[inner]\nname = pisa tower\n",
            FileFormat::Ini,
        ))
        .build()
        .unwrap();

    // INI leaves are strings; typing is recovered by coercion.
    assert_eq!(c.get_string("enabled").unwrap(), "true");
    assert_eq!(c.get_bool("enabled").unwrap(), true);
    assert_eq!(c.get_int("count").unwrap(), 12);
    assert_eq!(c.get_string("inner.name").unwrap(), "pisa tower");
}

#[test]
fn generated_lookup_kind_mismatch_is_not_found() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"{ "scalar": 4, "arr": [1, 2] }"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    // stepping through the wrong kind resolves to not-found
    assert!(matches!(
        c.get::<i64>("scalar.inner"),
        Err(ConfigError::NotFound(_))
    ));
    // out-of-bounds subscripts resolve to not-found, carrying the key
    assert!(matches!(
        c.get::<i64>("arr[5]"),
        Err(ConfigError::NotFound(key)) if key == "arr[5]"
    ));
    assert!(matches!(
        c.get::<i64>("arr[-3]"),
        Err(ConfigError::NotFound(key)) if key == "arr[-3]"
    ));
}
