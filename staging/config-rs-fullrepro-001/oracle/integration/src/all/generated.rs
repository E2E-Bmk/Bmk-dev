mod generated {
use config::{Config, Environment, File, FileFormat, Map, Source};
use serde::{Deserialize, Serialize};

#[test]
fn generated_cross_format_agreement() {
    // The same logical document in three syntaxes must agree on every
    // shared path through typed lookups.
    let toml = Config::builder()
        .add_source(File::from_str(
            "enabled = \"true\"\ncount = \"27\"\n[zone]\nname = \"east\"\n",
            FileFormat::Toml,
        ))
        .build()
        .unwrap();
    let json = Config::builder()
        .add_source(File::from_str(
            r#"{ "enabled": "true", "count": "27", "zone": { "name": "east" } }"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();
    let ini = Config::builder()
        .add_source(File::from_str(
            "enabled = true\ncount = 27\n[zone]\nname = east\n",
            FileFormat::Ini,
        ))
        .build()
        .unwrap();

    for c in [&toml, &json, &ini] {
        assert_eq!(c.get_bool("enabled").unwrap(), true);
        assert_eq!(c.get_int("count").unwrap(), 27);
        assert_eq!(c.get_string("zone.name").unwrap(), "east");
    }
}

#[test]
fn generated_layer_precedence_chain() {
    // defaults < first source < second source < overrides, per key.
    let c = Config::builder()
        .set_default("a", "default")
        .unwrap()
        .set_default("b", "default")
        .unwrap()
        .set_default("c", "default")
        .unwrap()
        .set_default("d", "default")
        .unwrap()
        .add_source(File::from_str(
            r#"{ "a": "first", "b": "first", "c": "first" }"#,
            FileFormat::Json,
        ))
        .add_source(File::from_str(
            r#"{ "a": "second", "b": "second" }"#,
            FileFormat::Json,
        ))
        .set_override("a", "override")
        .unwrap()
        .build()
        .unwrap();

    assert_eq!(c.get_string("a").unwrap(), "override");
    assert_eq!(c.get_string("b").unwrap(), "second");
    assert_eq!(c.get_string("c").unwrap(), "first");
    assert_eq!(c.get_string("d").unwrap(), "default");
}

#[test]
fn generated_config_as_source_reproduces_keys() {
    let inner = Config::builder()
        .set_override("service.port", 4130)
        .unwrap()
        .set_override("service.name", "relay")
        .unwrap()
        .build()
        .unwrap();

    let outer = Config::builder()
        .set_default("service.port", 1)
        .unwrap()
        .add_source(inner)
        .build()
        .unwrap();

    assert_eq!(outer.get_int("service.port").unwrap(), 4130);
    assert_eq!(outer.get_string("service.name").unwrap(), "relay");
}

#[test]
fn generated_try_from_roundtrip() {
    #[derive(Debug, Serialize, Deserialize, PartialEq)]
    struct Limits {
        floor: i64,
        ceiling: i64,
        label: String,
    }

    let original = Limits {
        floor: -4,
        ceiling: 93,
        label: String::from("band"),
    };

    let c = Config::try_from(&original).unwrap();
    assert_eq!(c.get_int("ceiling").unwrap(), 93);

    let round: Limits = c.try_deserialize().unwrap();
    assert_eq!(round, original);
}

#[test]
fn generated_env_collect_matches_built_lookup() {
    // What Source::collect exposes is exactly what a build merges.
    let mut vars = Map::new();
    vars.insert("SVC_HOST_NAME".to_owned(), "worker-3".to_owned());
    vars.insert("SVC_HOST_PORT".to_owned(), "8140".to_owned());

    let environment = Environment::with_prefix("SVC")
        .separator("_")
        .try_parsing(true)
        .source(Some(vars));

    let collected = environment.collect().unwrap();
    assert_eq!(
        collected["host.name"].clone().into_string().unwrap(),
        "worker-3"
    );
    assert_eq!(collected["host.port"].clone().into_int().unwrap(), 8140);

    let c = Config::builder()
        .add_source(environment)
        .build()
        .unwrap();
    assert_eq!(c.get_string("host.name").unwrap(), "worker-3");
    assert_eq!(c.get_int("host.port").unwrap(), 8140);
}

#[test]
fn generated_clone_reads_independently() {
    let c = Config::builder()
        .set_override("shared.key", 55)
        .unwrap()
        .build()
        .unwrap();
    let cloned = c.clone();

    assert_eq!(c.get_int("shared.key").unwrap(), 55);
    assert_eq!(cloned.get_int("shared.key").unwrap(), 55);

    #[derive(Debug, Deserialize)]
    struct Shared {
        shared: Inner,
    }
    #[derive(Debug, Deserialize)]
    struct Inner {
        key: i64,
    }

    let s: Shared = cloned.try_deserialize().unwrap();
    assert_eq!(s.shared.key, 55);
    // the original is still usable after the clone was consumed
    assert_eq!(c.get_int("shared.key").unwrap(), 55);
}
}
