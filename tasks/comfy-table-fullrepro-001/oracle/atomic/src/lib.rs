use comfy_table::{
    presets::*, Cell, CellAlignment, Column, ColumnConstraint, ContentArrangement,
    ContentLineStyle, LineStyle, Row, Table, TableStyle, Width,
};

#[test]
fn generated_column_padding_width_sums_both_sides() {
    let mut column = Column::new(2);
    column.set_padding((4, 7));
    assert_eq!(column.padding_width(), 11);
}

#[test]
fn generated_column_padding_width_saturates() {
    let mut column = Column::new(0);
    column.set_padding((u16::MAX, 2));
    assert_eq!(column.padding_width(), u16::MAX);
}

#[test]
fn generated_column_new_exposes_index_and_defaults() {
    let column = Column::new(9);
    assert_eq!(column.index, 9);
    assert_eq!(column.padding_width(), 2);
    assert_eq!(column.constraint(), None);
    assert!(!column.is_hidden());
}

#[test]
fn generated_column_hidden_constraint_controls_is_hidden() {
    let mut column = Column::new(0);
    column.set_constraint(ColumnConstraint::Hidden);
    assert!(column.is_hidden());
    assert_eq!(column.constraint(), Some(&ColumnConstraint::Hidden));
}

#[test]
fn generated_column_constraint_round_trip_content_width() {
    let mut column = Column::new(0);
    column.set_constraint(ColumnConstraint::ContentWidth);
    assert_eq!(column.constraint(), Some(&ColumnConstraint::ContentWidth));
}

#[test]
fn generated_column_constraint_round_trip_boundaries() {
    let mut column = Column::new(0);
    let constraint = ColumnConstraint::Boundaries {
        lower: Width::Fixed(3),
        upper: Width::Percentage(40),
    };
    column.set_constraint(constraint);
    assert_eq!(column.constraint(), Some(&constraint));
}

#[test]
fn generated_table_explicit_width_round_trip() {
    let mut table = Table::new();
    assert_eq!(table.width(), None);
    table.set_width(42);
    assert_eq!(table.width(), Some(42));
}

#[test]
fn generated_table_arrangement_round_trip_dynamic() {
    let mut table = Table::new();
    assert_eq!(std::mem::discriminant(&table.content_arrangement()), std::mem::discriminant(&ContentArrangement::Disabled));
    table.set_content_arrangement(ContentArrangement::Dynamic);
    assert_eq!(std::mem::discriminant(&table.content_arrangement()), std::mem::discriminant(&ContentArrangement::Dynamic));
}

#[test]
fn generated_table_arrangement_round_trip_full_width() {
    let mut table = Table::new();
    table.set_content_arrangement(ContentArrangement::DynamicFullWidth);
    assert_eq!(std::mem::discriminant(&table.content_arrangement()), std::mem::discriminant(&ContentArrangement::DynamicFullWidth));
}

#[test]
fn generated_table_style_mut_changes_visible_style_value() {
    let mut table = Table::new();
    table.load_style(NOTHING);
    table.style_mut().top_border = LineStyle::new('<', '=', '+', '>');
    assert_eq!(table.style().top_border.left, Some('<'));
    assert_eq!(table.style().top_border.fill, Some('='));
    assert_eq!(table.style().top_border.right, Some('>'));
}

#[test]
fn generated_table_set_constraints_ignores_extra_values() {
    let mut table = Table::new();
    table.add_row(["a", "b"]);
    table.set_constraints([
        ColumnConstraint::Absolute(Width::Fixed(3)),
        ColumnConstraint::UpperBoundary(Width::Fixed(4)),
        ColumnConstraint::Hidden,
    ]);
    assert_eq!(table.column(0).unwrap().constraint(), Some(&ColumnConstraint::Absolute(Width::Fixed(3))));
    assert_eq!(table.column(1).unwrap().constraint(), Some(&ColumnConstraint::UpperBoundary(Width::Fixed(4))));
    assert!(table.column(2).is_none());
}

#[test]
fn generated_discover_columns_after_row_mutation() {
    let mut table = Table::new();
    table.add_row(["a"]);
    table.row_mut(0).unwrap().add_cell(Cell::new("b"));
    table.discover_columns();
    assert_eq!(table.column_count(), 2);
}

#[test]
fn generated_column_cells_iter_marks_missing_cells() {
    let mut table = Table::new();
    table.add_row(["a", "b"]);
    table.add_row(["c"]);
    let values: Vec<_> = table.column_cells_iter(1).map(|cell| cell.is_some()).collect();
    assert_eq!(values, vec![true, false]);
}

#[test]
fn generated_column_cells_with_header_iter_includes_header_first() {
    let mut table = Table::new();
    table.set_header(["h0", "h1"]);
    table.add_row(["a"]);
    let values: Vec<_> = table
        .column_cells_with_header_iter(1)
        .map(|cell| cell.map(|c| c.content()))
        .collect();
    assert_eq!(values, vec![Some("h1".to_string()), None]);
}

#[test]
fn generated_column_max_content_widths_uses_unicode_display_width() {
    let mut table = Table::new();
    table.add_row(["新年", "abc"]);
    assert_eq!(table.column_max_content_widths(), vec![4, 3]);
}

#[test]
fn generated_row_max_height_zero_is_one_in_rendering() {
    let mut row = Row::from(["first\nsecond"]);
    row.max_height(0);
    let mut table = Table::new();
    table.add_row(row);
    let rendered = table.to_string();
    assert!(rendered.contains("first"));
    assert!(!rendered.contains("second"));
}

#[test]
fn generated_cell_alignment_overrides_column_alignment() {
    let mut table = Table::new();
    table.add_row([Cell::new("x").set_alignment(CellAlignment::Right)]);
    table.column_mut(0).unwrap().set_cell_alignment(CellAlignment::Left);
    let rendered = table.to_string();
    assert!(rendered.contains("| x |") || rendered.contains("|  x |"));
}

#[test]
fn generated_cell_delimiter_overrides_table_delimiter() {
    let mut table = Table::new();
    table
        .set_width(7)
        .set_content_arrangement(ContentArrangement::Dynamic)
        .set_delimiter('|')
        .add_row([Cell::new("aa-bb").set_delimiter('-')]);
    let rendered = table.to_string();
    assert!(rendered.contains("aa"));
    assert!(rendered.contains("bb"));
}

#[test]
fn generated_line_style_new_sets_all_parts() {
    let line = LineStyle::new('a', 'b', 'c', 'd');
    assert_eq!((line.left, line.fill, line.junction, line.right), (Some('a'), Some('b'), Some('c'), Some('d')));
}

#[test]
fn generated_line_style_builders_preserve_other_parts() {
    let line = LineStyle::none().left('l').fill('f').junction('j').right('r');
    assert_eq!((line.left, line.fill, line.junction, line.right), (Some('l'), Some('f'), Some('j'), Some('r')));
}

#[test]
fn generated_content_line_style_new_sets_all_parts() {
    let line = ContentLineStyle::new('l', 'j', 'r');
    assert_eq!((line.left, line.junction, line.right), (Some('l'), Some('j'), Some('r')));
}

#[test]
fn generated_content_line_style_builders_preserve_other_parts() {
    let line = ContentLineStyle::none().left('l').junction('j').right('r');
    assert_eq!((line.left, line.junction, line.right), (Some('l'), Some('j'), Some('r')));
}

#[test]
fn generated_table_style_builder_replaces_all_components() {
    let style = TableStyle::new()
        .top_border(LineStyle::new('a', 'b', 'c', 'd'))
        .header_lines(ContentLineStyle::new('e', 'f', 'g'))
        .header_separator(LineStyle::new('h', 'i', 'j', 'k'))
        .content_lines(ContentLineStyle::new('l', 'm', 'n'))
        .row_separator(LineStyle::new('o', 'p', 'q', 'r'))
        .bottom_border(LineStyle::new('s', 't', 'u', 'v'));
    assert_eq!(style.top_border.left, Some('a'));
    assert_eq!(style.header_lines.junction, Some('f'));
    assert_eq!(style.header_separator.fill, Some('i'));
    assert_eq!(style.content_lines.right, Some('n'));
    assert_eq!(style.row_separator.junction, Some('q'));
    assert_eq!(style.bottom_border.right, Some('v'));
}

#[test]
fn generated_rounded_corners_change_only_outer_corners() {
    let style = UTF8_FULL.with_rounded_corners();
    assert_eq!(style.top_border.left, Some('╭'));
    assert_eq!(style.top_border.right, Some('╮'));
    assert_eq!(style.bottom_border.left, Some('╰'));
    assert_eq!(style.bottom_border.right, Some('╯'));
    assert_eq!(style.header_lines, UTF8_FULL.header_lines);
}

#[test]
fn generated_solid_inner_borders_change_inner_parts() {
    let style = UTF8_FULL.with_solid_inner_borders();
    assert_eq!(style.header_lines.junction, Some('│'));
    assert_eq!(style.content_lines.junction, Some('│'));
    assert_eq!(style.row_separator.fill, Some('─'));
    assert_eq!(style.top_border, UTF8_FULL.top_border);
}

#[test]
fn generated_ascii_markdown_has_no_outer_borders() {
    assert_eq!(ASCII_MARKDOWN.top_border, LineStyle::none());
    assert_eq!(ASCII_MARKDOWN.bottom_border, LineStyle::none());
    assert_eq!(ASCII_MARKDOWN.header_lines.left, Some('|'));
}

#[test]
fn generated_utf8_full_uses_box_drawing_top_border() {
    assert_eq!(UTF8_FULL.top_border.left, Some('┌'));
    assert_eq!(UTF8_FULL.top_border.fill, Some('─'));
    assert_eq!(UTF8_FULL.top_border.junction, Some('┬'));
    assert_eq!(UTF8_FULL.top_border.right, Some('┐'));
}

#[test]
fn generated_cell_new_preserves_numeric_to_string_content() {
    assert_eq!(Cell::new(42_u32).content(), "42");
}

#[test]
fn generated_cell_new_preserves_newline_content() {
    assert_eq!(Cell::new("top\nbottom").content(), "top\nbottom");
}

#[test]
fn generated_row_add_cell_increases_cell_count() {
    let mut row = Row::new();
    row.add_cell(Cell::new("a")).add_cell(Cell::new("b"));
    assert_eq!(row.cell_count(), 2);
}

#[test]
fn generated_row_from_iterable_preserves_cell_order() {
    let row = Row::from(["left", "right"]);
    let content: Vec<_> = row.cell_iter().map(|cell| cell.content()).collect();
    assert_eq!(content, vec!["left".to_string(), "right".to_string()]);
}

#[test]
fn generated_table_header_accessor_returns_header_content() {
    let mut table = Table::new();
    table.set_header(["h0", "h1"]);
    let header = table.header().unwrap();
    let content: Vec<_> = header.cell_iter().map(|cell| cell.content()).collect();
    assert_eq!(content, vec!["h0".to_string(), "h1".to_string()]);
}
