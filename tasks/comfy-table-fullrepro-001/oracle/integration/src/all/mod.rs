use comfy_table::Table;
use unicode_width::UnicodeWidthStr;

mod add_predicate;
mod alignment_test;
#[cfg(feature = "tty")]
// combined_test excluded: exact ANSI color-code assertions are console-version-sensitive.

mod constraints_test;
mod content_arrangement_test;
// counts is excluded after dummy gate: count-only tests passed the minimal dummy.

mod custom_delimiter_test;
// edge_cases is excluded from Track A because its tests have no assertions.
mod hidden_test;
#[cfg(feature = "custom_styling")]
mod inner_style_test;
mod modifiers_test;
mod padding_test;
mod presets_test;
// property_test is excluded from Track A: it reads PROPTEST_CASES and has
// cfg(_integration_test) private-helper branches. Public deterministic
// invariant coverage belongs in Track B.
mod simple_test;
#[cfg(feature = "tty")]
// styling_test excluded: exact ANSI color-code assertions are console-version-sensitive.

mod truncation;
mod utf_8_characters;

pub fn assert_table_line_width(table: &Table, count: usize) {
    for line in table.lines() {
        assert_eq!(line.width(), count);
    }
}
