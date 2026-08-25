// Rewritten upstream tests: toml::ser serde mapping (ser_enum, ser_key, ser_tables_last).
// Source: repo-pool/toml-fullrepro-001 crates/toml/tests/serde/{ser_enum,ser_key,ser_tables_last}.rs
// Rewrites: snapbox asserts -> assert_eq with exact strings observed from the reference
// implementation (document renderings pinned by spec FMT-003/008/009/011); round-trip
// parse-back equality + serde_json cross-check retained. Helpers at crate root.

mod toml_serde_ser {

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize, Serialize, PartialEq)]
enum TheEnum {
    Plain,
    Tuple(i64, bool),
    NewType(String),
    Struct { value: i64 },
}

#[derive(Debug, Deserialize, Serialize, PartialEq)]
struct Val {
    val: TheEnum,
}

#[derive(Debug, Deserialize, Serialize, PartialEq)]
struct Multi {
    enums: Vec<TheEnum>,
}

// ===== ser_enum =====

mod ser_enum_unit {
    use super::*;

    #[test]
    fn to_string_value() {
        let input = TheEnum::Plain;
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "\"Plain\"");
        let roundtrip = crate::value_from_str::<TheEnum>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_value_str::<TheEnum>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_value() {
        let input = Val {
            val: TheEnum::Plain,
        };
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "{ val = \"Plain\" }");
        let roundtrip = crate::value_from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_value_str::<Val>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string() {
        let input = Val {
            val: TheEnum::Plain,
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "val = \"Plain\"\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_pretty() {
        let input = Val {
            val: TheEnum::Plain,
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "val = \"Plain\"\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }
}

mod ser_enum_tuple {
    use super::*;

    #[test]
    fn nested_to_string() {
        let input = Val {
            val: TheEnum::Tuple(-123, true),
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "[val]\nTuple = [-123, true]\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_pretty() {
        let input = Val {
            val: TheEnum::Tuple(-123, true),
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "[val]\nTuple = [\n    -123,\n    true,\n]\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }
}

mod ser_enum_newtype {
    use super::*;

    #[test]
    fn nested_to_string() {
        let input = Val {
            val: TheEnum::NewType("value".to_owned()),
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "[val]\nNewType = \"value\"\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_pretty() {
        let input = Val {
            val: TheEnum::NewType("value".to_owned()),
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "[val]\nNewType = \"value\"\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }
}

mod ser_enum_struct {
    use super::*;

    #[test]
    fn to_string() {
        let input = TheEnum::Struct { value: -123 };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "[Struct]\nvalue = -123\n");
        let roundtrip = crate::from_str::<TheEnum>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<TheEnum>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string_pretty() {
        let input = TheEnum::Struct { value: -123 };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "[Struct]\nvalue = -123\n");
        let roundtrip = crate::from_str::<TheEnum>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<TheEnum>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string() {
        let input = Val {
            val: TheEnum::Struct { value: -123 },
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "[val.Struct]\nvalue = -123\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_pretty() {
        let input = Val {
            val: TheEnum::Struct { value: -123 },
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "[val.Struct]\nvalue = -123\n");
        let roundtrip = crate::from_str::<Val>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Val>(&toml);
        assert_eq!(json, input);
    }
}

mod ser_enum_array {
    use super::*;

    #[test]
    fn to_string() {
        let input = Multi {
            enums: vec![
                TheEnum::Plain,
                TheEnum::Tuple(-123, true),
                TheEnum::NewType("value".to_owned()),
                TheEnum::Struct { value: -123 },
            ],
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(
            &toml,
            "enums = [\"Plain\", { Tuple = [-123, true] }, { NewType = \"value\" }, { Struct = { value = -123 } }]\n"
        );
        let roundtrip = crate::from_str::<Multi>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Multi>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string_pretty() {
        let input = Multi {
            enums: vec![
                TheEnum::Plain,
                TheEnum::Tuple(-123, true),
                TheEnum::NewType("value".to_owned()),
                TheEnum::Struct { value: -123 },
            ],
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(
            &toml,
            "enums = [\n    \"Plain\",\n    { Tuple = [\n    -123,\n    true,\n] },\n    { NewType = \"value\" },\n    { Struct = { value = -123 } },\n]\n"
        );
        let roundtrip = crate::from_str::<Multi>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = crate::json_from_toml_str::<Multi>(&toml);
        assert_eq!(json, input);
    }
}

// ===== ser_key =====

type Map<K> = std::collections::BTreeMap<K, String>;

#[derive(Debug, Deserialize, Serialize, PartialEq)]
struct Document<K: Ord> {
    map: Map<K>,
}

fn json_from_toml_value_str<T>(s: &'_ str) -> T
where
    T: serde::de::DeserializeOwned,
{
    let value = crate::value_from_str::<crate::SerdeValue>(s).unwrap();
    let value = value.try_into::<serde_json::Value>().unwrap();
    let json = serde_json::to_string_pretty(&value).unwrap();
    serde_json::from_str::<T>(&json).unwrap()
}

fn json_from_toml_str<T>(s: &'_ str) -> T
where
    T: serde::de::DeserializeOwned,
{
    let value = crate::from_str::<crate::SerdeTable>(s).unwrap();
    let value = value.try_into::<serde_json::Value>().unwrap();
    let json = serde_json::to_string_pretty(&value).unwrap();
    serde_json::from_str::<T>(&json).unwrap()
}

mod ser_key_str {
    use super::*;

    type Map = super::Map<String>;
    type Document = super::Document<String>;

    fn key() -> String {
        "key".to_owned()
    }

    #[test]
    fn to_string_value() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "{ key = \"value\" }");
        let roundtrip = crate::value_from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_value_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "key = \"value\"\n");
        let roundtrip = crate::from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string_pretty() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "key = \"value\"\n");
        let roundtrip = crate::from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_value() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "{ map = { key = \"value\" } }");
        let roundtrip = crate::value_from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_value_str::<Document>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "[map]\nkey = \"value\"\n");
        let roundtrip = crate::from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Document>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_pretty() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "[map]\nkey = \"value\"\n");
        let roundtrip = crate::from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Document>(&toml);
        assert_eq!(json, input);
    }
}

mod ser_key_variant {
    use super::*;

    #[derive(Debug, Deserialize, Serialize, PartialEq, Eq, PartialOrd, Ord)]
    enum Keys {
        #[allow(non_camel_case_types)]
        key,
    }

    type Map = super::Map<Keys>;
    type Document = super::Document<Keys>;

    fn key() -> Keys {
        Keys::key
    }

    #[test]
    fn to_string_value() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "{ key = \"value\" }");
        let roundtrip = crate::value_from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_value_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "key = \"value\"\n");
        let roundtrip = crate::from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string_pretty() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "key = \"value\"\n");
        let roundtrip = crate::from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_value() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "{ map = { key = \"value\" } }");
        let roundtrip = crate::value_from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_value_str::<Document>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "[map]\nkey = \"value\"\n");
        let roundtrip = crate::from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Document>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_pretty() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "[map]\nkey = \"value\"\n");
        let roundtrip = crate::from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Document>(&toml);
        assert_eq!(json, input);
    }
}

mod ser_key_bool {
    use super::*;

    type Map = super::Map<bool>;
    type Document = super::Document<bool>;

    fn key() -> bool {
        false
    }

    #[test]
    fn to_string_value() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "{ false = \"value\" }");
        let roundtrip = crate::value_from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_value_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "false = \"value\"\n");
        let roundtrip = crate::from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn to_string_pretty() {
        let input = [(key(), "value".to_owned())].into_iter().collect::<Map>();
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "false = \"value\"\n");
        let roundtrip = crate::from_str::<Map>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Map>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_value() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string_value(&input).unwrap();
        assert_eq!(&toml, "{ map = { false = \"value\" } }");
        let roundtrip = crate::value_from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_value_str::<Document>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string(&input).unwrap();
        assert_eq!(&toml, "[map]\nfalse = \"value\"\n");
        let roundtrip = crate::from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Document>(&toml);
        assert_eq!(json, input);
    }

    #[test]
    fn nested_to_string_pretty() {
        let input = Document {
            map: [(key(), "value".to_owned())].into_iter().collect::<Map>(),
        };
        let toml = crate::to_string_pretty(&input).unwrap();
        assert_eq!(&toml, "[map]\nfalse = \"value\"\n");
        let roundtrip = crate::from_str::<Document>(&toml);
        assert_eq!(roundtrip.unwrap(), input);
        let json = json_from_toml_str::<Document>(&toml);
        assert_eq!(json, input);
    }
}

// ===== ser_tables_last =====

fn t<D: Serialize + serde::de::DeserializeOwned>(val: &D) {
    let s = crate::to_string_pretty(&val).unwrap();
    let _roundtrip: D = crate::from_str(&s).unwrap();
}

#[test]
fn ser_tables_last_always_works() {
    #[derive(Deserialize, Serialize)]
    struct A {
        vals: HashMap<String, Value>,
    }

    #[derive(Deserialize, Serialize)]
    #[serde(untagged)]
    enum Value {
        Map(HashMap<String, String>),
        Int(i32),
    }

    let mut a = A {
        vals: HashMap::new(),
    };
    a.vals.insert("foo".to_owned(), Value::Int(0));

    let mut sub = HashMap::new();
    sub.insert("foo".to_owned(), "bar".to_owned());
    a.vals.insert("bar".to_owned(), Value::Map(sub));

    t(&a);
}

#[test]
fn ser_tables_last_vec_of_vec_issue_387() {
    #[derive(Deserialize, Serialize, Debug)]
    struct Glyph {
        components: Vec<Component>,
        contours: Vec<Contour>,
    }

    #[derive(Deserialize, Serialize, Debug)]
    struct Point {
        x: f64,
        y: f64,
        pt_type: String,
    }

    type Contour = Vec<Point>;

    #[derive(Deserialize, Serialize, Debug)]
    struct Component {
        base: String,
        transform: (f64, f64, f64, f64, f64, f64),
    }

    let comp1 = Component {
        base: "b".to_owned(),
        transform: (1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    };
    let comp2 = Component {
        base: "c".to_owned(),
        transform: (1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    };
    let components = vec![comp1, comp2];

    let contours = vec![
        vec![
            Point {
                x: 3.0,
                y: 4.0,
                pt_type: "line".to_owned(),
            },
            Point {
                x: 5.0,
                y: 6.0,
                pt_type: "line".to_owned(),
            },
        ],
        vec![
            Point {
                x: 0.0,
                y: 0.0,
                pt_type: "move".to_owned(),
            },
            Point {
                x: 7.0,
                y: 9.0,
                pt_type: "offcurve".to_owned(),
            },
            Point {
                x: 8.0,
                y: 10.0,
                pt_type: "offcurve".to_owned(),
            },
            Point {
                x: 11.0,
                y: 12.0,
                pt_type: "curve".to_owned(),
            },
        ],
    ];
    let g1 = Glyph {
        components,
        contours,
    };

    t(&g1);
}

#[test]
fn ser_tables_last_vec_order_issue_356() {
    #[derive(Serialize, Deserialize)]
    struct Outer {
        v1: Vec<Inner>,
        v2: Vec<Inner>,
    }

    #[derive(Serialize, Deserialize)]
    struct Inner {}

    let outer = Outer {
        v1: vec![Inner {}],
        v2: vec![],
    };
    t(&outer);
}

#[test]
fn ser_tables_last_values_before_tables_issue_403() {
    #[derive(Serialize, Deserialize)]
    struct A {
        a: String,
        b: String,
    }

    #[derive(Serialize, Deserialize)]
    struct B {
        a: String,
        b: Vec<String>,
    }

    #[derive(Serialize, Deserialize)]
    struct C {
        a: A,
        b: Vec<String>,
        c: Vec<B>,
    }
    let c = C {
        a: A {
            a: "aa".to_owned(),
            b: "ab".to_owned(),
        },
        b: vec!["b".to_owned()],
        c: vec![B {
            a: "cba".to_owned(),
            b: vec!["cbb".to_owned()],
        }],
    };
    t(&c);
}

}
