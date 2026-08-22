// Rewritten upstream tests: toml::Table / toml::Value Display rendering.
// Source: repo-pool/toml-fullrepro-001 crates/toml/tests/testsuite/{table,value}.rs
// Rewrites: snapbox asserts -> assert_eq with exact strings observed from the
// reference implementation (document rendering pinned by spec FMT-003/008, inline
// forms FMT-009, datetime display VAL-008).

mod toml_value_display {

use toml::Value::{Array, Boolean, Float, Integer, String, Table};
use toml::map::Map;

macro_rules! map( ($($k:expr => $v:expr),*) => ({
    let mut _m = Map::new();
    $(_m.insert($k.to_owned(), $v);)*
    _m
}) );

#[test]
fn table_display() {
    assert_eq!(map! {}.to_string(), "");
    assert_eq!(
        map! {
        "test" => Integer(2),
        "test2" => Integer(3) }
        .to_string(),
        "test = 2\ntest2 = 3\n"
    );
    assert_eq!(
        map! {
             "test" => Integer(2),
             "test2" => Table(map! {
                 "test" => String("wut".to_owned())
             })
        }
        .to_string(),
        "test = 2\n\n[test2]\ntest = \"wut\"\n"
    );
    assert_eq!(
        map! {
             "test" => Integer(2),
             "test2" => Array(vec![Table(map! {
                 "test" => String("wut".to_owned())
             })])
        }
        .to_string(),
        "test = 2\n\n[[test2]]\ntest = \"wut\"\n"
    );
}

#[test]
fn table_datetime_offset_issue_496() {
    let original = "value = 1911-01-01T10:11:12-00:36\n";
    let toml = original.parse::<toml::Table>().unwrap();
    let output = toml.to_string();
    assert_eq!(output, original);
}

#[test]
fn value_display() {
    assert_eq!(String("foo".to_owned()).to_string(), "\"foo\"");
    assert_eq!(Integer(10).to_string(), "10");
    assert_eq!(Float(10.0).to_string(), "10.0");
    assert_eq!(Float(2.4).to_string(), "2.4");
    assert_eq!(Boolean(true).to_string(), "true");
    assert_eq!(Array(vec![]).to_string(), "[]");
    assert_eq!(Array(vec![Integer(1), Integer(2)]).to_string(), "[1, 2]");
    assert_eq!(
        Table(map! {"test" => Integer (2), "test2" => Integer(3)}).to_string(),
        "{ test = 2, test2 = 3 }"
    );
}

}
