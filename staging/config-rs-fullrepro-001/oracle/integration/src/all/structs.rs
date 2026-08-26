mod structs {
use std::collections::HashSet;

use config::{Config, File, FileFormat, Map, Value};
use serde::Deserialize;

const PLACE_JSON: &str = r#"
{
  "debug": true,
  "production": false,
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
"#;

fn approx(a: f64, b: f64) -> bool {
    (a - b).abs() < 1e-9
}

#[test]
fn test_map_struct() {
    #[derive(Debug, Deserialize)]
    struct Settings {
        place: Map<String, Value>,
    }

    let c = Config::builder()
        .add_source(File::from_str(PLACE_JSON, FileFormat::Json))
        .build()
        .unwrap();

    let s: Settings = c.try_deserialize().unwrap();

    assert_eq!(s.place.len(), 8);
    assert_eq!(
        s.place["name"].clone().into_string().unwrap(),
        "Torre di Pisa".to_owned()
    );
    assert_eq!(s.place["reviews"].clone().into_int().unwrap(), 3866);
}

#[test]
fn test_file_struct() {
    #[derive(Debug, Deserialize)]
    struct Settings {
        debug: f64,
        production: Option<String>,
        place: Place,
    }

    #[derive(Debug, Deserialize)]
    struct Place {
        name: String,
        longitude: f64,
        latitude: f64,
        favorite: bool,
        telephone: Option<String>,
        reviews: u64,
        rating: Option<f32>,
    }

    let c = Config::builder()
        .add_source(File::from_str(PLACE_JSON, FileFormat::Json))
        .build()
        .unwrap();

    // Deserialize the entire document as a single struct
    let s: Settings = c.try_deserialize().unwrap();

    assert!(approx(s.debug, 1.0));
    assert_eq!(s.production, Some("false".to_owned()));
    assert_eq!(s.place.name, "Torre di Pisa");
    assert!(approx(s.place.longitude, 43.722_498_5));
    assert!(approx(s.place.latitude, 10.397_052_2));
    assert!(!s.place.favorite);
    assert_eq!(s.place.reviews, 3866);
    assert_eq!(s.place.rating, Some(4.5));
    assert_eq!(s.place.telephone, None);
}

#[test]
fn test_scalar_struct() {
    #[derive(Debug, Deserialize)]
    struct Place {
        name: String,
        longitude: f64,
        latitude: f64,
        favorite: bool,
        telephone: Option<String>,
        reviews: u64,
        rating: Option<f32>,
    }

    let c = Config::builder()
        .add_source(File::from_str(PLACE_JSON, FileFormat::Json))
        .build()
        .unwrap();

    // Deserialize a scalar struct that has lots of different data types
    let p: Place = c.get("place").unwrap();

    assert_eq!(p.name, "Torre di Pisa");
    assert!(approx(p.longitude, 43.722_498_5));
    assert!(approx(p.latitude, 10.397_052_2));
    assert!(!p.favorite);
    assert_eq!(p.reviews, 3866);
    assert_eq!(p.rating, Some(4.5));
    assert_eq!(p.telephone, None);
}

#[test]
fn test_struct_array() {
    #[derive(Debug, Deserialize)]
    struct Settings {
        #[serde(rename = "arr")]
        elements: Vec<String>,
    }

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

    let s: Settings = c.try_deserialize().unwrap();

    assert_eq!(s.elements.len(), 10);
    assert_eq!(s.elements[3], "4".to_owned());
}

#[test]
fn test_enum() {
    #[derive(Debug, Deserialize)]
    struct Settings {
        diodes: Map<String, Diode>,
    }

    #[derive(Debug, Deserialize, PartialEq, Eq)]
    #[serde(rename_all = "lowercase")]
    enum Diode {
        Off,
        Brightness(i32),
        Blinking(i32, i32),
        Pattern { name: String, infinite: bool },
    }
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "diodes": {
    "green": "off",
    "red": {
      "brightness": 100
    },
    "blue": {
      "blinking": [300, 700]
    },
    "white": {
      "pattern": {
        "name": "christmas",
        "infinite": true
      }
    }
  }
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let s: Settings = c.try_deserialize().unwrap();

    assert_eq!(s.diodes["green"], Diode::Off);
    assert_eq!(s.diodes["red"], Diode::Brightness(100));
    assert_eq!(s.diodes["blue"], Diode::Blinking(300, 700));
    assert_eq!(
        s.diodes["white"],
        Diode::Pattern {
            name: "christmas".into(),
            infinite: true,
        }
    );
}

#[test]
fn test_enum_key() {
    #[derive(Debug, Deserialize)]
    struct Settings {
        proton: Map<Quark, usize>,
        // Just to make sure that set keys work too.
        quarks: HashSet<Quark>,
    }

    #[derive(Debug, Deserialize, PartialEq, Eq, Hash)]
    #[serde(rename_all = "lowercase")]
    enum Quark {
        Up,
        Down,
        Strange,
        Charm,
        Bottom,
        Top,
    }

    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "quarks": ["up", "down", "strange", "charm", "bottom", "top"],
  "proton": {
    "up": 2,
    "down": 1
  }
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let s: Settings = c.try_deserialize().unwrap();

    assert_eq!(s.proton[&Quark::Up], 2);
    assert_eq!(s.quarks.len(), 6);
}

#[test]
fn test_int_key() {
    #[derive(Debug, Deserialize, PartialEq, Eq)]
    struct Settings {
        divisors: Map<u32, u32>,
    }

    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "divisors": {
    "1": 1,
    "2": 2,
    "4": 3,
    "5": 2
  }
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    let s: Settings = c.try_deserialize().unwrap();
    assert_eq!(s.divisors[&4], 3);
    assert_eq!(s.divisors.len(), 4);
}

#[test]
fn respect_field_case() {
    #[derive(Deserialize, Debug)]
    #[allow(non_snake_case)]
    #[allow(dead_code)]
    struct Kafka {
        broker: String,
        topic: String,
        pollSleep: u64,
    }

    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "broker": "localhost:29092",
  "topic": "rust",
  "pollSleep": 1000
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    c.try_deserialize::<Kafka>().unwrap();
}

#[test]
fn respect_renamed_field() {
    #[derive(Deserialize, Debug)]
    #[allow(dead_code)]
    struct MyConfig {
        #[serde(rename = "FooBar")]
        foo_bar: String,
    }

    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "FooBar": "Hello, world!"
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    c.try_deserialize::<MyConfig>().unwrap();
}

#[test]
fn respect_path_case() {
    let c = Config::builder()
        .add_source(File::from_str(
            r#"
{
  "Student": [
    { "Name": "1" },
    { "Name": "2" }
  ]
}
"#,
            FileFormat::Json,
        ))
        .build()
        .unwrap();

    c.get_string("Student[0].Name").unwrap();
}
}
