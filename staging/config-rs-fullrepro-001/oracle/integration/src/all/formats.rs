mod formats {
use config::{Config, ConfigError, Environment, File, FileFormat, Map, Value};
use serde::Deserialize;

fn approx(a: f64, b: f64) -> bool {
    (a - b).abs() < 1e-9
}

#[test]
fn toml_file_full() {
    #[derive(Debug, Deserialize)]
    struct Settings {
        debug: f64,
        production: Option<String>,
        code: AsciiCode,
        place: Place,
        #[serde(rename = "arr")]
        elements: Vec<String>,
    }

    #[derive(Debug, Deserialize)]
    struct Place {
        number: PlaceNumber,
        name: String,
        longitude: f64,
        latitude: f64,
        favorite: bool,
        telephone: Option<String>,
        reviews: u64,
        creator: Map<String, Value>,
        rating: Option<f32>,
    }

    #[derive(Debug, Deserialize, PartialEq, Eq)]
    struct PlaceNumber(u8);

    #[derive(Debug, Deserialize, PartialEq, Eq)]
    struct AsciiCode(i8);

    let c = Config::builder()
        .add_source(File::from_str(
            r#"
debug = true
production = false
code = 53

arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

[place]
number = 1
name = "Torre di Pisa"
longitude = 43.7224985
latitude = 10.3970522
favorite = false
reviews = 3866
rating = 4.5

[place.creator]
name = "John Smith"
username = "jsmith"
email = "jsmith@localhost"
"#,
            FileFormat::Toml,
        ))
        .build()
        .unwrap();

    let s: Settings = c.try_deserialize().unwrap();

    assert!(approx(s.debug, 1.0));
    assert_eq!(s.production, Some("false".to_owned()));
    assert_eq!(s.code, AsciiCode(53));
    assert_eq!(s.place.number, PlaceNumber(1));
    assert_eq!(s.place.name, "Torre di Pisa");
    assert!(approx(s.place.longitude, 43.722_498_5));
    assert!(approx(s.place.latitude, 10.397_052_2));
    assert!(!s.place.favorite);
    assert_eq!(s.place.reviews, 3866);
    assert_eq!(s.place.rating, Some(4.5));
    assert_eq!(s.place.telephone, None);
    assert_eq!(s.elements.len(), 10);
    assert_eq!(s.elements[3], "4".to_owned());
    assert_eq!(
        s.place.creator["name"].clone().into_string().unwrap(),
        "John Smith".to_owned()
    );
}

#[test]
fn ini_file_full() {
    #[derive(Debug, Deserialize, PartialEq)]
    struct Settings {
        debug: f64,
        place: Place,
    }

    #[derive(Debug, Deserialize, PartialEq)]
    struct Place {
        name: String,
        longitude: f64,
        latitude: f64,
        favorite: bool,
        reviews: u64,
        rating: Option<f32>,
    }

    let c = Config::builder()
        .add_source(File::from_str(
            r#"
debug = true
production = false
[place]
name = Torre di Pisa
longitude = 43.7224985
latitude = 10.3970522
favorite = false
reviews = 3866
rating = 4.5
"#,
            FileFormat::Ini,
        ))
        .build()
        .unwrap();
    let s: Settings = c.try_deserialize().unwrap();
    assert_eq!(
        s,
        Settings {
            debug: 1.0,
            place: Place {
                name: String::from("Torre di Pisa"),
                longitude: 43.722_498_5,
                latitude: 10.397_052_2,
                favorite: false,
                reviews: 3866,
                rating: Some(4.5),
            },
        }
    );
}

#[test]
fn toml_parse_error() {
    let res = Config::builder()
        .add_source(File::from_str(
            r#"
ok = true
error = tru
"#,
            FileFormat::Toml,
        ))
        .build();

    assert!(matches!(res, Err(ConfigError::FileParse { uri: None, .. })));
}

#[test]
fn json_parse_error() {
    let res = Config::builder()
        .add_source(File::from_str(
            r#"{ "ok": true, "error": }"#,
            FileFormat::Json,
        ))
        .build();

    assert!(matches!(res, Err(ConfigError::FileParse { uri: None, .. })));
}

#[test]
fn ini_parse_error() {
    let res = Config::builder()
        .add_source(File::from_str(
            r#"
ok : true,
error
"#,
            FileFormat::Ini,
        ))
        .build();

    assert!(res.is_err());
}

#[test]
fn env_overrides_file_value() {
    // A later environment layer shadows a file value under the separator
    // translation; sibling keys survive.
    #[derive(Debug, Deserialize, PartialEq)]
    struct StructSettings {
        foo: String,
        bar: String,
    }

    let mut vars = Map::new();
    vars.insert("APP_FOO".to_owned(), "replacement value".to_owned());

    let cfg = Config::builder()
        .add_source(File::from_str(
            r#"
foo = FOO should be overridden
bar = I am bar
"#,
            FileFormat::Ini,
        ))
        .add_source(
            Environment::with_prefix("APP")
                .separator("_")
                .source(Some(vars)),
        )
        .build()
        .unwrap();

    let settings = cfg.try_deserialize::<StructSettings>().unwrap();
    assert_eq!(
        settings,
        StructSettings {
            foo: String::from("replacement value"),
            bar: String::from("I am bar"),
        }
    );
}

#[test]
fn get_invalid_type_carries_key() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"{ "boolean_s_parse": "fals" }"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let res = c.get::<bool>("boolean_s_parse");
    assert!(matches!(
        res,
        Err(ConfigError::Type { key: Some(key), .. }) if key == "boolean_s_parse"
    ));
}

#[test]
fn deserialize_invalid_type_is_error() {
    #[derive(Debug, Deserialize)]
    #[allow(dead_code)]
    struct Output {
        ok: bool,
        boolean_s_parse: bool,
    }

    let c = Config::builder()
        .add_source(File::from_str(
            r#"{ "ok": true, "boolean_s_parse": "fals" }"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let res = c.try_deserialize::<Output>();
    assert!(res.is_err());
}
}
