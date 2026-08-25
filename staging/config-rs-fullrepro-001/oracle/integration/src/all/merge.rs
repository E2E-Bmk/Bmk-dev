mod merge {
use std::collections::BTreeMap;

use config::{Config, File, FileFormat};
use serde::Deserialize;

#[test]
fn test_merge() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "debug": true,
  "production": false,
  "place": {
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
        .add_source(File::from_str(
            r#"
{
  "debug": false,
  "production": true,
  "place": {
    "rating": 4.9,
    "creator": {
      "name": "Somebody New"
    }
  }
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    assert_eq!(c.get("debug").ok(), Some(false));
    assert_eq!(c.get("production").ok(), Some(true));
    assert_eq!(c.get("place.rating").ok(), Some(4.9));

    // The later layer replaces only the leaf it names; siblings survive.
    assert_eq!(
        c.get("place.creator.name").ok(),
        Some("Somebody New".to_owned())
    );
    assert_eq!(
        c.get("place.creator.username").ok(),
        Some("jsmith".to_owned())
    );
    assert_eq!(
        c.get("place.creator.email").ok(),
        Some("jsmith@localhost".to_owned())
    );
}

#[test]
fn test_merge_whole_config() {
    let builder1 = Config::builder().set_override("x", 10).unwrap();
    let builder2 = Config::builder().set_override("y", 25).unwrap();

    let config1 = builder1.build_cloned().unwrap();
    let config2 = builder2.build_cloned().unwrap();

    assert_eq!(config1.get("x").ok(), Some(10));
    assert_eq!(config2.get::<()>("x").ok(), None);

    assert_eq!(config2.get("y").ok(), Some(25));
    assert_eq!(config1.get::<()>("y").ok(), None);

    let config3 = builder1.add_source(config2).build().unwrap();

    assert_eq!(config3.get("x").ok(), Some(10));
    assert_eq!(config3.get("y").ok(), Some(25));
}

#[derive(Debug, Deserialize)]
struct ProfileSettings {
    profile: BTreeMap<String, Profile>,
}

#[derive(Debug, Default, Deserialize)]
struct Profile {
    name: Option<String>,
}

fn merged(first: &str, second: &str) -> ProfileSettings {
    Config::builder()
        .add_source(File::from_str(first, FileFormat::Json))
        .add_source(File::from_str(second, FileFormat::Json))
        .build()
        .unwrap()
        .try_deserialize::<ProfileSettings>()
        .unwrap()
}

#[test]
fn test_merge_missing_and_empty_maps() {
    // missing -> empty map
    let s = merged(
        r#"{ "profile": {} }"#,
        r#"{ "profile": { "missing_to_empty": {} } }"#,
    );
    assert_eq!(s.profile.len(), 1);
    assert!(s.profile["missing_to_empty"].name.is_none());

    // missing -> map with k/v
    let s = merged(
        r#"{ "profile": {} }"#,
        r#"{ "profile": { "missing_to_non_empty": { "name": "bar" } } }"#,
    );
    assert_eq!(
        s.profile["missing_to_non_empty"].name.as_deref(),
        Some("bar")
    );

    // empty map -> empty map
    let s = merged(
        r#"{ "profile": { "empty_to_empty": {} } }"#,
        r#"{ "profile": { "empty_to_empty": {} } }"#,
    );
    assert!(s.profile["empty_to_empty"].name.is_none());

    // empty map -> map with k/v
    let s = merged(
        r#"{ "profile": { "empty_to_non_empty": {} } }"#,
        r#"{ "profile": { "empty_to_non_empty": { "name": "bar" } } }"#,
    );
    assert_eq!(
        s.profile["empty_to_non_empty"].name.as_deref(),
        Some("bar")
    );
}

#[test]
fn test_merge_populated_and_null_maps() {
    // map with k/v -> empty map: populated content survives a key-wise merge
    let s = merged(
        r#"{ "profile": { "non_empty_to_empty": { "name": "foo" } } }"#,
        r#"{ "profile": { "non_empty_to_empty": {} } }"#,
    );
    assert_eq!(
        s.profile["non_empty_to_empty"].name.as_deref(),
        Some("foo")
    );

    // map with k/v -> map with k/v (override)
    let s = merged(
        r#"{ "profile": { "non_empty_to_non_empty": { "name": "foo" } } }"#,
        r#"{ "profile": { "non_empty_to_non_empty": { "name": "bar" } } }"#,
    );
    assert_eq!(
        s.profile["non_empty_to_non_empty"].name.as_deref(),
        Some("bar")
    );

    // null -> empty map
    let s = merged(
        r#"{ "profile": { "null_to_empty": null } }"#,
        r#"{ "profile": { "null_to_empty": {} } }"#,
    );
    assert!(s.profile["null_to_empty"].name.is_none());

    // null -> map with k/v
    let s = merged(
        r#"{ "profile": { "null_to_non_empty": null } }"#,
        r#"{ "profile": { "null_to_non_empty": { "name": "bar" } } }"#,
    );
    assert_eq!(
        s.profile["null_to_non_empty"].name.as_deref(),
        Some("bar")
    );
}
}
