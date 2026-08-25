//! Oracle "integration" crate for toml-fullrepro-001.
//!
//! Exercises cross-crate serde mappings: the toml crate's general serde
//! mapping (general_toml), the toml_edit crate's serde mapping
//! (general_toml_edit), and cross-document toml_edit operations
//! (edit_integration). As in upstream toml_edit's tests, the shared
//! Value/Table test types are the toml crate's (`toml_types` alias), while
//! the entry points exercised are toml_edit's (`from_str_edit`,
//! `to_string_edit`, ...). Each test file is a self-contained `mod <stem>`
//! block spliced at crate root, so the compiled path
//! `integration::<stem>::<fn>` equals the discovery chain `<stem>::<fn>`.

#![allow(dead_code)]

use serde::de::DeserializeOwned;
use serde::Serialize;

pub use toml::value::Date;
pub use toml::value::Datetime;
pub use toml::value::Time;
pub use toml::Table as SerdeDocument;
pub use toml::Table as SerdeTable;
pub use toml::Value as SerdeValue;

// ---- toml crate entry points (upstream crates/toml/tests/serde/main.rs) ----

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

// ---- toml_edit entry points (upstream crates/toml_edit/tests/serde/main.rs) ----

/// Deserialize a TOML document through toml_edit.
pub(crate) fn from_str_edit<T>(s: &'_ str) -> Result<T, toml_edit::de::Error>
where
    T: DeserializeOwned,
{
    toml_edit::de::from_str(s)
}

/// Serialize a TOML document through toml_edit.
pub(crate) fn to_string_edit<T>(value: &T) -> Result<String, toml_edit::ser::Error>
where
    T: Serialize + ?Sized,
{
    toml_edit::ser::to_string(value)
}

/// Serialize a "pretty" TOML document through toml_edit.
pub(crate) fn to_string_pretty_edit<T>(value: &T) -> Result<String, toml_edit::ser::Error>
where
    T: Serialize + ?Sized,
{
    toml_edit::ser::to_string_pretty(value)
}

/// Deserialize a TOML value through toml_edit::de::ValueDeserializer.
pub(crate) fn value_from_str_edit<T>(s: &'_ str) -> Result<T, toml_edit::de::Error>
where
    T: DeserializeOwned,
{
    T::deserialize(s.parse::<toml_edit::de::ValueDeserializer>()?)
}

/// Serialize to a TOML value string via toml_edit::ser::ValueSerializer.
pub(crate) fn to_string_value_edit<T>(value: &T) -> Result<String, toml_edit::ser::Error>
where
    T: Serialize + ?Sized,
{
    let serializer = toml_edit::ser::ValueSerializer::new();
    let value = value.serialize(serializer)?;
    Ok(value.to_string())
}

include!("general_toml.rs");
include!("general_toml_edit.rs");
include!("edit_integration.rs");
