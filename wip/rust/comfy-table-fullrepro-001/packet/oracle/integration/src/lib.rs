use comfy_table::Table;
use unicode_width::UnicodeWidthStr;

include!("all/add_predicate.rs");
include!("all/alignment_test.rs");
include!("all/constraints_test.rs");
include!("all/content_arrangement_test.rs");
include!("all/custom_delimiter_test.rs");
include!("all/hidden_test.rs");
include!("all/inner_style_test.rs");
include!("all/modifiers_test.rs");
include!("all/padding_test.rs");
include!("all/presets_test.rs");
include!("all/simple_test.rs");
include!("all/truncation.rs");
include!("all/utf_8_characters.rs");

pub fn assert_table_line_width(table: &Table, count: usize) {
    for line in table.lines() {
        assert_eq!(line.width(), count);
    }
}
