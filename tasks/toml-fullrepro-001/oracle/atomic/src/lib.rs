//! Oracle "atomic" crate for toml-fullrepro-001.
//!
//! Exercises single-crate contracts: the toml crate's serde mapping
//! (toml_serde_de / toml_serde_ser / toml_serde_string / toml_serde_spanned),
//! toml::Table / toml::Value Display rendering (toml_value_display), and
//! toml_edit document editing (edit_document). Each test file is a
//! self-contained `mod <stem>` block spliced at crate root, so the compiled
//! path `atomic::<stem>::<fn>` equals the discovery chain `<stem>::<fn>` and
//! the nextest-reported path minus the `atomic::atomic$` prefix.
//!
//! Helpers mirror the upstream test-binary root
//! (crates/toml/tests/serde/main.rs): toml::from_str (borrowing),
//! toml::ser::to_string(_pretty), toml::de::ValueDeserializer::parse,
//! toml::ser::ValueSerializer, the toml_types aliases (Table/Value), and a
//! serde_json round-trip cross-check used by the ser-side tests.

#![allow(dead_code)]

use serde::de::DeserializeOwned;
use serde::Serialize;

pub use toml::value::Date;
pub use toml::value::Datetime;
pub use toml::value::Time;
pub use toml::Table as SerdeDocument;
pub use toml::Table as SerdeTable;
pub use toml::Value as SerdeValue;

/// Deserialize a TOML document. `T: Deserialize<'de>` so borrowed `&str`
/// fields (e.g. `BTreeMap<&str, &str>`) are supported.
pub(crate) fn from_str<'de, T>(s: &'de str) -> Result<T, toml::de::Error>
where
    T: serde::de::Deserialize<'de>,
{
    toml::from_str(s)
}

/// Deserialize a TOML value (no document shape required).
pub(crate) fn value_from_str<T>(s: &'_ str) -> Result<T, toml::de::Error>
where
    T: DeserializeOwned,
{
    T::deserialize(toml::de::ValueDeserializer::parse(s)?)
}

/// Serialize a TOML document.
pub(crate) fn to_string<T>(value: &T) -> Result<String, toml::ser::Error>
where
    T: Serialize + ?Sized,
{
    toml::to_string(value)
}

/// Serialize a "pretty" TOML document.
pub(crate) fn to_string_pretty<T>(value: &T) -> Result<String, toml::ser::Error>
where
    T: Serialize + ?Sized,
{
    toml::to_string_pretty(value)
}

/// Serialize to a TOML value string via toml::ser::ValueSerializer.
pub(crate) fn to_string_value<T>(value: &T) -> Result<String, toml::ser::Error>
where
    T: Serialize + ?Sized,
{
    let mut output = String::new();
    let serializer = toml::ser::ValueSerializer::new(&mut output);
    value.serialize(serializer)?;
    Ok(output)
}

/// Round-trip a TOML document through serde_json and deserialize `T`.
pub(crate) fn json_from_toml_str<T>(s: &str) -> T
where
    T: DeserializeOwned,
{
    let value: SerdeDocument = from_str(s).unwrap();
    let json = serde_json::to_value(&value).unwrap();
    serde_json::from_value(json).unwrap()
}

/// Round-trip a TOML value through serde_json and deserialize `T`.
pub(crate) fn json_from_toml_value_str<T>(s: &str) -> T
where
    T: DeserializeOwned,
{
    let value: SerdeValue = value_from_str(s).unwrap();
    let json = serde_json::to_value(&value).unwrap();
    serde_json::from_value(json).unwrap()
}

include!("toml_serde_de.rs");
include!("toml_serde_ser.rs");
include!("toml_serde_string.rs");
include!("toml_serde_spanned.rs");
include!("toml_value_display.rs");
include!("edit_document.rs");
