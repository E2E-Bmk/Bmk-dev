mod utf_8_characters {
use comfy_table::*;
use pretty_assertions::assert_eq;

/// UTF-8 symbols that are longer than a single character are properly handled.
/// This means, that comfy-table detects that they're longer than 1 character and styles/arranges
/// the table accordingly.
#[test]
fn multi_character_utf8_symbols() {
    let mut table = Table::new();
    table
        .set_header(vec!["Header1", "Header2", "Header3"])
        .add_row(vec![
            "This is a text",
            "This is another text",
            "This is the third text",
        ])
        .add_row(vec![
            "This is another text",
            "Now\nadd some\nmulti line stuff",
            "✅",
        ]);

    println!("{table}");
    let expected = "
+----------------------+----------------------+------------------------+
| Header1              | Header2              | Header3                |
+======================================================================+
| This is a text       | This is another text | This is the third text |
|----------------------+----------------------+------------------------|
| This is another text | Now                  | ✅                     |
|                      | add some             |                        |
|                      | multi line stuff     |                        |
+----------------------+----------------------+------------------------+";
    assert_eq!(expected, "\n".to_string() + &table.to_string());
}

#[test]
fn multi_character_utf8_word_splitting() {
    let mut table = Table::new();
    table
        .set_width(8)
        .set_content_arrangement(ContentArrangement::Dynamic)
        .set_header(vec!["test"])
        .add_row(vec!["abc✅def"]);

    println!("{table}");
    let expected = "
+------+
| test |
+======+
| abc  |
| ✅de |
| f    |
+------+";
    println!("{expected}");
    assert_eq!(expected, "\n".to_string() + &table.to_string());
}

#[test]
fn multi_character_cjk_word_splitting() {
    let mut table = Table::new();
    table
        .set_width(8)
        .set_content_arrangement(ContentArrangement::Dynamic)
        .set_header(vec!["test"])
        .add_row(vec!["abc新年快乐edf"]);

    println!("{table}");
    let expected = "
+------+
| test |
+======+
| abc  |
| 新年 |
| 快乐 |
| edf  |
+------+";
    println!("{expected}");
    assert_eq!(expected, "\n".to_string() + &table.to_string());
}

/// Handle emojis that'd joined via the "zero-width joiner" character U+200D and contain variant
/// selectors.
///
/// Those composite emojis should be handled as a single grapheme and thereby have their width
/// calculated based on the grapheme length instead of the individual chars.
///
/// This is also a regression test, as previously emojis were split in the middle of the joiner
/// sequence, resulting in two different emojis on different lines.
#[test]
fn zwj_utf8_word_splitting() {
    let mut table = Table::new();
    table
        .set_width(8)
        .set_content_arrangement(ContentArrangement::Dynamic)
        .set_header(vec!["test"])
        .add_row(vec!["ab🙂‍↕️def"]);

    println!("{table}");
    let expected = "
+------+
| test |
+======+
| ab🙂‍↕️ |
| def  |
+------+";
    println!("{expected}");
    assert_eq!(expected, "\n".to_string() + &table.to_string());
}

}
