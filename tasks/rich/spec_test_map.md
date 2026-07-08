# Stage 3 spec-test map: rich

filter/oracle_source: upstream_only
collection_method: pytest collection succeeded with `python -m pytest --collect-only -q` in the Rich candidate repo; full raw output saved to `filter/collection.txt`.
filter_policy: Track A only. Track B not triggered because retained upstream nodeids exceed 30 and include integration/system_e2e coverage.

| test_nodeid | layer | spec_section | status | notes |
|-------------|-------|--------------|--------|-------|
| tests/test_align.py::test_bad_align_legal | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_repr | atomic | - | source-only | repr call has no behavioral assertion |
| tests/test_align.py::test_align_left | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_center | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_right | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_top | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_middle | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_bottom | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_center_middle | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_fit | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_right_style | atomic | - | source-only | asserts exact ANSI byte sequence for background styling |
| tests/test_align.py::test_measure | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_no_pad | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_align_width | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_shortcuts | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_align.py::test_vertical_center | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_ansi.py::test_decode | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_decode_example | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_decode_issue_2688[\x1b[31mFound 4 errors in 2 files (checked 18 source files)\x1b(B\x1b[m\n-Found 4 errors in 2 files (checked 18 source files)\n] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_decode_issue_2688[Hallo-Hallo] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_decode_issue_2688[\x1b(BHallo-Hallo] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_decode_issue_2688[\x1b(JHallo-Hallo] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_decode_issue_2688[\x1b(BHal\x1b(Jlo-Hallo] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[0] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[1] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[2] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[3] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[4] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[5] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[6] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[7] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[8] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[9] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[:] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[;] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[<] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[=] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[>] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_strip_private_escape_sequences[?] | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_ansi.py::test_decode_newlines | atomic | - | source-only | tests rich.ansi.AnsiDecoder and private escape handling not specified as public surface |
| tests/test_bar.py::test_init | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_bar.py::test_update | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_bar.py::test_render | atomic | - | source-only | asserts exact ANSI byte sequence for progress bar drawing |
| tests/test_bar.py::test_measure | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_bar.py::test_zero_total | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_bar.py::test_pulse | atomic | - | source-only | asserts exact ANSI byte sequence for pulse gradient |
| tests/test_bar.py::test_get_pulse_segments | atomic | - | excluded | accesses ProgressBar._get_pulse_segments private helper |
| tests/test_block_bar.py::test_repr | atomic | - | source-only | asserts exact repr string |
| tests/test_block_bar.py::test_render | atomic | - | source-only | asserts exact ANSI byte sequence for bar drawing |
| tests/test_block_bar.py::test_measure | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_block_bar.py::test_zero_total | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_box.py::test_str | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_box.py::test_repr | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_box.py::test_get_top | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_box.py::test_get_row | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_box.py::test_get_bottom | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_box.py::test_box_substitute_for_same_box | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_box.py::test_box_substitute_for_different_box_legacy_windows | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_box.py::test_box_substitute_for_different_box_ascii_encoding | atomic | - | source-only | asserts Box helper/string internals rather than table/panel public rendering contract |
| tests/test_card.py::test_card_render | atomic | - | source-only | asserts exact demo-card artifact via rich.__main__.make_test_card |
| tests/test_cells.py::test_get_character_cell_size[\x00-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_get_character_cell_size[\u200d-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_get_character_cell_size[a-1] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_get_character_cell_size[\U0001f4a9-2] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_get_character_cell_size[\U000e01f0-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_cell_len_long_string | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_cell_len_short_string | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_set_cell_size | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_set_cell_size_infinite | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[--1--] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[x--1--x] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[x-1-x-] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[x-2-x-] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[-0--] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[-1--] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[a-0--a] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[a-1-a-] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9-0--\U0001f4a9] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9-1- - ] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9-2-\U0001f4a9-] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9x-1- - x] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9x-2-\U0001f4a9-x] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9x-3-\U0001f4a9x-] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f469\u200d\U0001f527-0--\U0001f469\u200d\U0001f527] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f469\u200d\U0001f527-1- - ] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f469\u200d\U0001f527-2-\U0001f469\u200d\U0001f527-] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f469\u200d\U0001f527x-1- - x] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f469\u200d\U0001f527x-2-\U0001f469\u200d\U0001f527-x] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f469\u200d\U0001f527x-3-\U0001f469\u200d\U0001f527x-] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[xxxxxxxxxxxxxxx\U0001f4a9\U0001f4a9-10-xxxxxxxxxx-xxxxx\U0001f4a9\U0001f4a9] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[xxxxxxxxxxxxxxx\U0001f4a9\U0001f4a9-15-xxxxxxxxxxxxxxx-\U0001f4a9\U0001f4a9] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[xxxxxxxxxxxxxxx\U0001f4a9\U0001f4a9-16-xxxxxxxxxxxxxxx - \U0001f4a9] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9\U0001f4a9-3-\U0001f4a9 - ] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9\U0001f4a9xxxxxxxxxx-2-\U0001f4a9-\U0001f4a9xxxxxxxxxx] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9\U0001f4a9xxxxxxxxxx-3-\U0001f4a9 - xxxxxxxxxx] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_text[\U0001f4a9\U0001f4a9xxxxxxxxxx-4-\U0001f4a9\U0001f4a9-xxxxxxxxxx] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells_double_width_boundary | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells_mixed_width | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells_zero_width[-expected0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells_zero_width[\x1b-expected1] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells_zero_width[\x1b\x1b-expected2] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells_zero_width[\x1b\x1b\x1b-expected3] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_chop_cells_zero_width[\x1b\x1b\x1b\x1b-expected4] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_is_single_cell_widths | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[-expected_spans0-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[a-expected_spans1-1] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[ab-expected_spans2-2] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\U0001f4a9-expected_spans3-2] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u308f\u3055\u3073-expected_spans4-6] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\U0001f469\u200d\U0001f527-expected_spans5-2] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[a\U0001f469\u200d\U0001f527-expected_spans6-3] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[a\U0001f469\u200d\U0001f527b-expected_spans7-4] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u2b07-expected_spans8-1] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u2b07\ufe0f-expected_spans9-2] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u267b-expected_spans10-1] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u267b\ufe0f-expected_spans11-2] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u267b\u267b\ufe0f-expected_spans12-3] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\x1b-expected_spans13-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\x1b\x1b-expected_spans14-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\ufe0f-expected_spans15-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\ufe0f\ufe0f-expected_spans16-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u200d-expected_spans17-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u200d\u200d-expected_spans18-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\x1b\ufe0f-expected_spans19-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_split_graphemes[\u200d\ufe0f-expected_spans20-0] | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_nerd_font | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_zwj | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_cells.py::test_non_printable | atomic | - | excluded | top-level import includes rich.cells._is_single_cell_widths |
| tests/test_color.py::test_str | atomic | - | source-only | asserts exact Color string/repr formatting |
| tests/test_color.py::test_repr | atomic | - | source-only | asserts exact Color repr formatting |
| tests/test_color.py::test_color_system_repr | atomic | - | source-only | asserts enum repr formatting |
| tests/test_color.py::test_rich | atomic | - | source-only | asserts exact Color.__rich__ presentation string and spans |
| tests/test_color.py::test_system | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_windows | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_truecolor | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_parse_success | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_from_triplet | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_from_rgb | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_from_ansi | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_default | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_parse_error | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_get_ansi_codes | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_downgrade | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_color.py::test_parse_rgb_hex | atomic | - | source-only | helper function is not specified in the public contract |
| tests/test_color.py::test_blend_rgb | atomic | - | source-only | helper function is not specified in the public contract |
| tests/test_color_triplet.py::test_hex | atomic | - | source-only | ColorTriplet helper formatting is not in the spec |
| tests/test_color_triplet.py::test_rgb | atomic | - | source-only | ColorTriplet helper formatting is not in the spec |
| tests/test_color_triplet.py::test_normalized | atomic | - | source-only | ColorTriplet helper formatting is not in the spec |
| tests/test_columns.py::test_render | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_columns_align.py::test_align | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_console.py::test_dumb_terminal | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_soft_wrap | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_16color_terminal | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_truecolor_terminal | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_kitty_terminal | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_console_options_update | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_console_options_update_height | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_init | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size_can_fall_back_to_std_descriptors[True-no_descriptor_size0-ValueError-ValueError-ValueError-expected_size0] | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size_can_fall_back_to_std_descriptors[False-no_descriptor_size1-ValueError-ValueError-ValueError-expected_size1] | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size_can_fall_back_to_std_descriptors[False-ValueError-stdin_size2-ValueError-ValueError-expected_size2] | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size_can_fall_back_to_std_descriptors[False-ValueError-ValueError-stdout_size3-ValueError-expected_size3] | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size_can_fall_back_to_std_descriptors[False-ValueError-ValueError-ValueError-stderr_size4-expected_size4] | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size_can_fall_back_to_std_descriptors[False-ValueError-ValueError-ValueError-ValueError-expected_size5] | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_repr | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_empty_with_end | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_multiple | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_text | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_text_multiple | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_json | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_json_error | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_json_data | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_json_ensure_ascii | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_json_with_default_ensure_ascii | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_json_indent_none | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_console_null_file | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_log | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_log_milliseconds | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_empty | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_markup_highlight | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_style | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_show_cursor | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_clear | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_clear_no_terminal | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_get_style | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_get_style_default | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_get_style_error | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_render_error | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_control | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_capture | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_input | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_input_password | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_status | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_none | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_left | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_center | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_right | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_renderable_none | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_renderable_left | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_renderable_center | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_justify_renderable_right | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_render_broken_renderable | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_export_text | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_export_html | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_export_html_inline | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_export_svg | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_export_svg_specified_unique_id | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_save_svg | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_save_text | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_save_html | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_no_wrap | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_unicode_error | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_bell | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_pager | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_out | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_render_group | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_render_group_fit | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_get_time | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_console_style | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_no_color | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_quiet | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_screen | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_screen_update | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_height | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_columns_env | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_lines_env | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_screen_update_class | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_is_alt_screen | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_set_console_title | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_update_screen | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_update_screen_lines | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_update_options_markup | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_width_zero | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_size_properties | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_print_newline_start | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_is_terminal_broken_file | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_detect_color_system | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_reset_height | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_render_lines_height_minus_vertical_pad_is_negative | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_recording_no_stdout_and_no_stderr_files | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_capturing_no_stdout_and_no_stderr_files | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_force_color | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_force_color_jupyter | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_reenable_highlighting | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_brokenpipeerror | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_capture_and_record | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_tty_interactive | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_console.py::test_tty_compatible | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_constrain.py::test_width_of_none | atomic | - | source-only | Constrain helper behavior is not included in the selected spec surface |
| tests/test_containers.py::test_renderables_measure | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_containers.py::test_renderables_empty | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_containers.py::test_lines_rich_console | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_containers.py::test_lines_justify | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_control.py::test_control | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_control.py::test_strip_control_codes | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_control.py::test_escape_control_codes | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_control.py::test_control_move_to | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_control.py::test_control_move | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_control.py::test_move_to_column | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_control.py::test_title | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_emoji.py::test_no_emoji | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_emoji.py::test_str_repr | atomic | - | source-only | asserts exact Emoji repr formatting |
| tests/test_emoji.py::test_replace | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_emoji.py::test_render | integration | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_emoji.py::test_variant | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_emoji.py::test_variant_non_default | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_file_proxy.py::test_empty_bytes | atomic | - | source-only | FileProxy is not in the specified public behavior surface |
| tests/test_file_proxy.py::test_flush | atomic | - | source-only | FileProxy is not in the specified public behavior surface |
| tests/test_file_proxy.py::test_new_lines | atomic | - | source-only | FileProxy is not in the specified public behavior surface |
| tests/test_file_proxy.py::test_isatty | atomic | - | source-only | FileProxy is not in the specified public behavior surface |
| tests/test_filesize.py::test_traditional | atomic | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_filesize.py::test_pick_unit_and_suffix | atomic | - | source-only | helper function is not specified; public contract is decimal() |
| tests/test_getfileno.py::test_get_fileno | atomic | - | excluded | top-level import from rich._fileno |
| tests/test_getfileno.py::test_get_fileno_missing | atomic | - | excluded | top-level import from rich._fileno |
| tests/test_getfileno.py::test_get_fileno_broken | atomic | - | excluded | top-level import from rich._fileno |
| tests/test_highlighter.py::test_wrong_type | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[-spans0] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ -spans1] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[<foo>-spans2] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[<foo: 23>-spans3] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[<foo: <bar: 23>>-spans4] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[False True None-spans5] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[foo=bar-spans6] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[foo="bar"-spans7] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[<Permission.WRITE\|READ: 3>-spans8] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[( )-spans9] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[[ ]-spans10] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[{ }-spans11] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ 1 -spans12] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ 1.2 -spans13] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ 0xff -spans14] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ 1e10 -spans15] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ 1j -spans16] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ 3.14j -spans17] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ (3.14+2.06j) -spans18] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ (3+2j) -spans19] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ (123456.4321-1234.5678j) -spans20] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ (-123123-2.1312342342423422e+25j) -spans21] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ /foo -spans22] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ /foo/bar.html -spans23] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[01-23-45-67-89-AB-spans24] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[01-23-45-FF-FE-67-89-AB-spans25] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[01:23:45:67:89:AB-spans26] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[01:23:45:FF:FE:67:89:AB-spans27] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[0123.4567.89AB-spans28] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[0123.45FF.FE67.89AB-spans29] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ed-ed-ed-ed-ed-ed-spans30] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ED-ED-ED-ED-ED-ED-spans31] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[Ed-Ed-Ed-Ed-Ed-Ed-spans32] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[0-00-1-01-2-02-spans33] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ https://example.org -spans34] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ http://example.org -spans35] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ http://example.org/index.html -spans36] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ http://example.org/index.html#anchor -spans37] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[https://www.youtube.com/@LinusTechTips-spans38] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ http://example.org/index.html?param1=value1 -spans39] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[ http://example.org/~folder -spans40] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[No place like 127.0.0.1-spans41] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[''-spans42] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex['hello'-spans43] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex['''hello'''-spans44] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[""-spans45] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex["hello"-spans46] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex["""hello"""-spans47] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[\\'foo'-spans48] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[it's no 'string'-spans49] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_regex[78351748-9b32-4e08-ad3e-7e9ff124d541-spans50] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_json_with_indent | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_json_string_only | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_json_empty_string_only | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_json_no_indent | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-08-spans0] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-08-30-spans1] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[20080830-spans2] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-243-spans3] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008243-spans4] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-W35-spans5] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008W35-spans6] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-W35-6-spans7] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008W356-spans8] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[17:21-spans9] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[1721-spans10] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[172159-spans11] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[Z-spans12] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[+07-spans13] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[+07:00-spans14] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[17:21:59+07:00-spans15] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[172159+0700-spans16] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[172159+07-spans17] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-08-30 17:21:59-spans18] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[20080830 172159-spans19] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-08-30-spans20] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-08-30+07:00-spans21] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[01:45:36-spans22] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[01:45:36.123+07:00-spans23] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[01:45:36.123+07:00-spans24] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-08-30T01:45:36-spans25] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_highlighter.py::test_highlight_iso8601_regex[2008-08-30T01:45:36.123Z-spans26] | atomic | - | source-only | asserts exact regex/span tables for highlighter internals |
| tests/test_inspect.py::test_render | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_text | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_empty_dict | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_builtin_function_except_python311 | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_builtin_function_only_python311 | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_coroutine | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_integer | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_integer_with_value | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_integer_with_methods_python38_and_python39 | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_integer_with_methods_python310only | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_integer_with_methods_python311 | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_broken_call_attr | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_swig_edge_case | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_inspect_module_with_class | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_qualname_in_slots | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_can_handle_special_characters_in_docstrings[\x07-\\a] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_can_handle_special_characters_in_docstrings[\x08-\\b] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_can_handle_special_characters_in_docstrings[\x0c-\\f] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_can_handle_special_characters_in_docstrings[\r-\\r] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_can_handle_special_characters_in_docstrings[\x0b-\\v] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[object-expected_result0] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[obj1-expected_result1] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[hi-expected_result2] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[str-expected_result3] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[obj4-expected_result4] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[Foo-expected_result5] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[obj6-expected_result6] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro[FooSubclass-expected_result7] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro_as_strings[hi-expected_result0] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro_as_strings[str-expected_result1] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro_as_strings[obj2-expected_result2] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro_as_strings[Foo-expected_result3] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro_as_strings[obj4-expected_result4] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_types_mro_as_strings[FooSubclass-expected_result5] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[hi-types0-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[str-types1-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[hi-types2-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[str-types3-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[obj4-types4-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[Foo-types5-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[obj6-types6-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[Foo-types7-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[obj8-types8-False] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[Foo-types9-False] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[obj10-types10-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_inspect.py::test_object_is_one_of_types[Foo-types11-True] | atomic | - | excluded | top-level import from rich._inspect |
| tests/test_json.py::test_print_json_data_with_default | integration | ### Structured Renderables | covered |  |
| tests/test_jupyter.py::test_jupyter | atomic | ### Console Rendering and I/O | covered |  |
| tests/test_jupyter.py::test_jupyter_columns_env | atomic | ### Console Rendering and I/O | covered |  |
| tests/test_jupyter.py::test_jupyter_lines_env | atomic | ### Console Rendering and I/O | covered |  |
| tests/test_layout.py::test_no_layout | atomic | - | source-only | asserts Layout helper tree/map/render internals outside the selected public surface |
| tests/test_layout.py::test_add_split | atomic | - | source-only | asserts Layout helper tree/map/render internals outside the selected public surface |
| tests/test_layout.py::test_unsplit | atomic | - | source-only | asserts Layout helper tree/map/render internals outside the selected public surface |
| tests/test_layout.py::test_render | atomic | - | excluded | accesses private attribute/helper _renderable |
| tests/test_layout.py::test_tree | atomic | - | source-only | asserts Layout helper tree/map/render internals outside the selected public surface |
| tests/test_layout.py::test_refresh_screen | atomic | - | source-only | asserts Layout helper tree/map/render internals outside the selected public surface |
| tests/test_live.py::test_live_state | atomic | - | excluded | accesses private attribute/helper _started |
| tests/test_live.py::test_growing_display | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_growing_display_transient | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_growing_display_overflow_ellipsis | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_growing_display_overflow_crop | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_growing_display_overflow_visible | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_growing_display_autorefresh | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_growing_display_console_redirect | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_growing_display_file_console | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_live_screen | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live.py::test_live_empty | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_live_render.py::test_renderable | atomic | - | source-only | LiveRender is an internal live-display renderer shape |
| tests/test_live_render.py::test_position_cursor | atomic | - | excluded | accesses private attribute/helper _shape |
| tests/test_live_render.py::test_restore_cursor | atomic | - | excluded | accesses private attribute/helper _shape |
| tests/test_live_render.py::test_rich_console | atomic | - | source-only | LiveRender is an internal live-display renderer shape |
| tests/test_log.py::test_log | atomic | - | source-only | asserts full ANSI log rendering with source-line artifact |
| tests/test_log.py::test_log_caller_frame_info | atomic | - | excluded | accesses Console._caller_frame_info private helper |
| tests/test_log.py::test_justify | atomic | ### Console Rendering and I/O | covered |  |
| tests/test_logging.py::test_exception | atomic | - | excluded | platform-specific traceback/log rendering skip |
| tests/test_logging.py::test_exception_with_extra_lines | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_logging.py::test_stderr_and_stdout_are_none | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_logging.py::test_markup_and_highlight | system_e2e | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_markdown.py::test_markdown_render | atomic | - | source-only | asserts full ANSI Markdown fixture including theme details |
| tests/test_markdown.py::test_inline_code | atomic | - | source-only | asserts exact Pygments ANSI styling for inline code |
| tests/test_markdown.py::test_markdown_table | atomic | - | source-only | asserts exact ANSI table rendering for large Markdown fixture |
| tests/test_markdown.py::test_inline_styles_in_table | atomic | - | source-only | asserts exact ANSI styling/layout for Markdown table |
| tests/test_markdown.py::test_inline_styles_with_justification | atomic | - | source-only | asserts exact ANSI styling/layout for Markdown table |
| tests/test_markdown.py::test_partial_table | atomic | - | source-only | asserts exact ANSI table skeleton for partial Markdown input |
| tests/test_markdown.py::test_table_with_empty_cells | integration | ### Structured Renderables | covered |  |
| tests/test_markdown.py::test_inline_code_in_table_cells | atomic | - | source-only | asserts exact Pygments ANSI styling in Markdown table |
| tests/test_markdown_no_hyperlinks.py::test_markdown_render | atomic | - | source-only | asserts a full ANSI Markdown fixture, including theme/template details |
| tests/test_markup.py::test_re_no_match | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_re_match | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_escape | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_escape_backslash_end | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_escape | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_parse | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_parse_link | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_not_tags | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_link | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_combine | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_overlap | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_adjoint | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_close | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_close_ambiguous | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_markup_error | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_markup_escape | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_escape_escape | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_events | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_events_broken | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_markup.py::test_render_meta | atomic | - | excluded | top-level import includes rich.markup._parse |
| tests/test_measure.py::test_span | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_measure.py::test_no_renderable | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_measure.py::test_measure_renderables | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_measure.py::test_clamp | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_null_file.py::test_null_file | atomic | - | excluded | top-level import from rich._null_file |
| tests/test_padding.py::test_repr | atomic | - | source-only | repr formatting is not a stable behavioral contract |
| tests/test_padding.py::test_indent | atomic | ### Tables and Layout Renderables | covered |  |
| tests/test_padding.py::test_unpack | atomic | ### Tables and Layout Renderables | covered |  |
| tests/test_padding.py::test_expand_false | atomic | ### Tables and Layout Renderables | covered |  |
| tests/test_padding.py::test_rich_console | atomic | ### Tables and Layout Renderables | covered |  |
| tests/test_palette.py::test_rich_cast | atomic | - | excluded | top-level import from rich._palettes |
| tests/test_panel.py::test_render_panel[panel0-\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502Hello, World                                    \u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_panel.py::test_render_panel[panel1-\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502Hello, World\u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_panel.py::test_render_panel[panel2-\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502Hello, World\u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_panel.py::test_render_panel[panel3-\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502Hello,\u2502\n\u2502World \u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_panel.py::test_render_panel[panel4-\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\u2502\n\u2502\u2502Hello, World                                  \u2502\u2502\n\u2502\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_panel.py::test_render_panel[panel5-\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 FOO \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502Hello, World                                    \u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_panel.py::test_render_panel[panel6-\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502Hello, World                                    \u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 FOO \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_panel.py::test_console_width | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_panel.py::test_fixed_width | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_panel.py::test_render_size | atomic | - | source-only | asserts exact internal Segment list shape |
| tests/test_panel.py::test_title_text | atomic | - | source-only | asserts exact ANSI byte sequence for panel title styling |
| tests/test_panel.py::test_title_text_with_border_color | atomic | - | source-only | asserts exact ANSI byte sequence for panel border/title styling |
| tests/test_panel.py::test_title_text_with_panel_background | atomic | - | source-only | asserts exact ANSI byte sequence for panel background styling |
| tests/test_pick.py::test_pick_bool | atomic | - | excluded | top-level import from rich._pick |
| tests/test_pretty.py::test_install | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_install_max_depth | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_ipy_display_hook__repr_html | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_ipy_display_hook__multiple_special_reprs | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_ipy_display_hook__no_special_repr_methods | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_ipy_display_hook__special_repr_raises_exception | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_ipy_display_hook__console_renderables_on_newline | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty_dataclass | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_empty_dataclass | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty_namedtuple | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty_namedtuple_length_one_no_trailing_comma | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty_namedtuple_empty | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty_namedtuple_custom_repr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty_namedtuple_fields_invalid_type | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pretty_namedtuple_max_depth | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_small_width | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_ansi_in_pretty_repr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_broken_repr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_broken_getattr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_reference_cycle_container | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_reference_cycle_namedtuple | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_reference_cycle_dataclass | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_reference_cycle_attrs | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_reference_cycle_custom_repr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_max_depth | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_max_depth_rich_repr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_max_depth_attrs | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_max_depth_dataclass | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_defaultdict | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_deque | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_array | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_tuple_of_one | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_node | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_indent_lines | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pprint | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pprint_max_values | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pprint_max_items | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_pprint_max_string | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_tuples | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_newline | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_empty_repr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_attrs | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_attrs_empty | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_attrs_broken | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_attrs_broken_310 | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_user_dict | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_lying_attribute | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_measure_pretty | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_tuple_rich_repr | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_tuple_rich_repr_default | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_pretty.py::test_dataclass_no_attribute | atomic | - | excluded | top-level import includes rich.pretty._ipy_display_hook |
| tests/test_progress.py::test_bar_columns | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_text_column | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_time_elapsed_column | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_time_remaining_column | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_compact_time_remaining_column[None---:--] | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_compact_time_remaining_column[0-00:00] | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_compact_time_remaining_column[59-00:59] | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_compact_time_remaining_column[71-01:11] | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_compact_time_remaining_column[4210-1:10:10] | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_time_remaining_column_elapsed_when_finished | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_renderable_column | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_spinner_column | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_download_progress_uses_decimal_units | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_download_progress_uses_binary_units | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_task_ids | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_finished | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_expand_bar | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_progress_with_none_total_renders_a_pulsing_bar | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_render | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_track | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_progress_track | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_columns | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_using_default_columns | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_task_create | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_task_start | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_task_zero_total | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_progress_create | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_track_thread | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_reset | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_progress_max_refresh | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_live_is_started_if_progress_is_enabled | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_live_is_not_started_if_progress_is_disabled | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_no_output_if_progress_is_disabled | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_no_output_if_progress_is_disabled_non_interactive | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_open | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_open_text_mode | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_wrap_file | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_wrap_file_task_total | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_progress.py::test_task_progress_column_speed | atomic | - | excluded | top-level import includes rich.progress._TrackThread |
| tests/test_prompt.py::test_prompt_str | atomic | - | source-only | asserts exact validation message text |
| tests/test_prompt.py::test_prompt_str_case_insensitive | atomic | - | source-only | asserts exact validation message text |
| tests/test_prompt.py::test_prompt_str_default | atomic | - | source-only | asserts exact prompt text formatting |
| tests/test_prompt.py::test_prompt_int | atomic | - | source-only | asserts exact validation message text |
| tests/test_prompt.py::test_prompt_confirm_no | atomic | - | source-only | asserts exact validation message text |
| tests/test_prompt.py::test_prompt_confirm_yes | atomic | - | source-only | asserts exact validation message text |
| tests/test_prompt.py::test_prompt_confirm_default | atomic | - | source-only | asserts exact validation message text |
| tests/test_prompt.py::test_prompt_confirm_markup | atomic | - | source-only | asserts exact validation message text |
| tests/test_protocol.py::test_rich_cast | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_protocol.py::test_rich_cast_fake | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_protocol.py::test_rich_cast_container | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_protocol.py::test_abc | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_protocol.py::test_cast_deep | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_protocol.py::test_cast_recursive | atomic | - | source-only | recursive __rich__ cycle fallback is not specified |
| tests/test_ratio.py::test_ratio_reduce[20-ratios0-maximums0-values0-result0] | atomic | - | excluded | top-level import from rich._ratio |
| tests/test_ratio.py::test_ratio_reduce[20-ratios1-maximums1-values1-result1] | atomic | - | excluded | top-level import from rich._ratio |
| tests/test_ratio.py::test_ratio_reduce[20-ratios2-maximums2-values2-result2] | atomic | - | excluded | top-level import from rich._ratio |
| tests/test_ratio.py::test_ratio_reduce[3-ratios3-maximums3-values3-result3] | atomic | - | excluded | top-level import from rich._ratio |
| tests/test_ratio.py::test_ratio_reduce[3-ratios4-maximums4-values4-result4] | atomic | - | excluded | top-level import from rich._ratio |
| tests/test_ratio.py::test_ratio_reduce[3-ratios5-maximums5-values5-result5] | atomic | - | excluded | top-level import from rich._ratio |
| tests/test_ratio.py::test_ratio_resolve | atomic | - | excluded | top-level import from rich._ratio |
| tests/test_repr.py::test_rich_repr | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_repr.py::test_rich_repr_positional_only | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_repr.py::test_rich_angular | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_repr.py::test_rich_repr_auto | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_repr.py::test_rich_repr_auto_angular | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_repr.py::test_broken_egg | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_repr.py::test_rich_pretty | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_repr.py::test_rich_pretty_angular | atomic | - | source-only | asserts exact repr strings, which are implementation-specific |
| tests/test_rich_print.py::test_get_console | integration | ## Public API | covered |  |
| tests/test_rich_print.py::test_reconfigure_console | integration | ## Public API | covered |  |
| tests/test_rich_print.py::test_rich_print | integration | ## Public API | covered |  |
| tests/test_rich_print.py::test_rich_print_json | integration | ## Public API | covered |  |
| tests/test_rich_print.py::test_rich_print_json_round_trip | system_e2e | ## Public API | covered |  |
| tests/test_rich_print.py::test_rich_print_json_no_truncation | integration | ## Public API | covered |  |
| tests/test_rich_print.py::test_rich_print_X | integration | ## Public API | covered |  |
| tests/test_rule.py::test_rule | atomic | - | source-only | asserts exact ANSI byte sequence for rule styling |
| tests/test_rule.py::test_rule_error | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule.py::test_rule_align | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule.py::test_rule_cjk | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule.py::test_rule_not_enough_space_for_title_text[center-\u2500\u2500\u2500\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_rule.py::test_rule_not_enough_space_for_title_text[left-\u2026 \u2500\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_rule.py::test_rule_not_enough_space_for_title_text[right-\u2500 \u2026\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_rule.py::test_rule_center_aligned_title_not_enough_space_for_rule | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule.py::test_rule_side_aligned_not_enough_space_for_rule[left] | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule.py::test_rule_side_aligned_not_enough_space_for_rule[right] | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule.py::test_rule_just_enough_width_available_for_title[center-\u2500 \u2026 \u2500\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_rule.py::test_rule_just_enough_width_available_for_title[left-AB\u2026 \u2500\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_rule.py::test_rule_just_enough_width_available_for_title[right-\u2500 AB\u2026\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_rule.py::test_characters | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule.py::test_repr | atomic | - | source-only | asserts repr formatting |
| tests/test_rule.py::test_error | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_rule_in_table.py::test_rule_in_unexpanded_table[expand_kwarg0] | integration | ### Tables and Layout Renderables + ## Cross-View Invariants | covered |  |
| tests/test_rule_in_table.py::test_rule_in_unexpanded_table[expand_kwarg1] | integration | ### Tables and Layout Renderables + ## Cross-View Invariants | covered |  |
| tests/test_rule_in_table.py::test_rule_in_expanded_table | system_e2e | ### Tables and Layout Renderables + ## Cross-View Invariants | covered |  |
| tests/test_rule_in_table.py::test_rule_in_ratio_table | system_e2e | ### Tables and Layout Renderables + ## Cross-View Invariants | covered |  |
| tests/test_screen.py::test_screen | atomic | - | source-only | Screen renderable is not included in the selected spec surface |
| tests/test_segment.py::test_repr | atomic | - | source-only | asserts exact Segment repr formatting |
| tests/test_segment.py::test_line | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_apply_style | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_lines | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_lines_terminator | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_lines_terminator_single_line | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_and_crop_lines | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_adjust_line_length | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_get_line_length | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_get_shape | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_set_shape | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_simplify | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_filter_control | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_strip_styles | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_strip_links | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_remove_color | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_is_control | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_segments_renderable | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_divide | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_divide_complex | atomic | - | source-only | asserts exact ANSI byte soup for a regression fixture |
| tests/test_segment.py::test_divide_emoji | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_divide_edge | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_divide_edge_2 | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XX-4-result0] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X-1-result1] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[\U0001f4a9-1-result2] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XY-1-result3] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[\U0001f4a9X-1-result4] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[\U0001f4a9\U0001f4a9-1-result5] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X\U0001f4a9Y-2-result6] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X\U0001f4a9YZ-2-result7] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X\U0001f4a9\U0001f4a9Z-2-result8] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X\U0001f4a9\U0001f4a9Z-3-result9] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X\U0001f4a9\U0001f4a9Z-4-result10] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X\U0001f4a9\U0001f4a9Z-5-result11] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[X\U0001f4a9\U0001f4a9Z-6-result12] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XYZABC\U0001f4a9\U0001f4a9-6-result13] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XYZABC\U0001f4a9\U0001f4a9-7-result14] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XYZABC\U0001f4a9\U0001f4a9-8-result15] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XYZABC\U0001f4a9\U0001f4a9-9-result16] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XYZABC\U0001f4a9\U0001f4a9-10-result17] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[\U0001f4a9\U0001f4a9\U0001f4a9\U0001f4a9\U0001f4a9-3-result18] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[\U0001f4a9\U0001f4a9\U0001f4a9\U0001f4a9\U0001f4a9-4-result19] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[\U0001f4a9X\U0001f4a9Y\U0001f4a9Z\U0001f4a9A\U0001f4a9-4-result20] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XYZABC-4-result21] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[XYZABC-5-result22] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_emoji[a1\u3042\uff11\uff11bcdaef-9-result23] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment0] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment1] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment2] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment3] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment4] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment5] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment6] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_mixed[segment7] | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_doubles | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_split_cells_single | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_segment_lines_renderable | integration | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_align_top | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_align_middle | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_segment.py::test_align_bottom | atomic | ### Rendering Protocol and Segments | covered |  |
| tests/test_spinner.py::test_spinner_create | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_spinner.py::test_spinner_render | integration | ### Progress, Status, and Live Displays | covered |  |
| tests/test_spinner.py::test_spinner_update | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_spinner.py::test_rich_measure | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_spinner.py::test_spinner_markup | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_stack.py::test_stack | atomic | - | excluded | top-level import from rich._stack |
| tests/test_status.py::test_status | atomic | ### Progress, Status, and Live Displays | covered |  |
| tests/test_status.py::test_renderable | integration | ### Progress, Status, and Live Displays | covered |  |
| tests/test_style.py::test_str | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_ansi_codes | atomic | - | excluded | accesses Style._make_ansi_codes private helper |
| tests/test_style.py::test_repr | atomic | - | source-only | asserts exact Style repr formatting |
| tests/test_style.py::test_eq | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_hash | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_empty | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_bool | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_color_property | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_bgcolor_property | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_parse | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_link_id | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_get_html_style | atomic | - | source-only | asserts exact CSS serialization/order |
| tests/test_style.py::test_chain | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_copy | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_render | integration | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_test | atomic | - | source-only | no oracle beyond smoke/no exception |
| tests/test_style.py::test_add | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_iadd | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_style_stack | atomic | - | source-only | StyleStack helper is not in the specified public contract |
| tests/test_style.py::test_pick_first | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_background_style | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_without_color | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_meta | atomic | - | source-only | includes exact Style repr formatting |
| tests/test_style.py::test_from_meta | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_on | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_clear_meta_and_links | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_style.py::test_clear_meta_and_links_clears_hash | atomic | - | excluded | asserts private _hash cache state |
| tests/test_styled.py::test_styled | atomic | - | source-only | asserts exact ANSI byte sequence for Styled wrapper |
| tests/test_syntax.py::test_blank_lines | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_python_render | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_python_render_simple | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_python_render_simple_passing_lexer_instance | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_python_render_simple_indent_guides | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_python_render_line_range_indent_guides | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_python_render_indent_guides | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_pygments_syntax_theme_non_str | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_pygments_syntax_theme | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_get_line_color_none | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_highlight_background_color | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_get_number_styles | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_get_style_for_token | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_option_no_wrap | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_syntax_highlight_ranges | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_ansi_theme | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_from_path | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_from_path_unknown_lexer | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_from_path_lexer_override | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_from_path_lexer_override_invalid_lexer | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_syntax_guess_lexer | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_syntax_padding | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_syntax_measure | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_background_color_override_includes_padding | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_syntax.py::test_padding_plus_wrap | atomic | - | excluded | top-level import includes rich.syntax._SyntaxHighlightRange |
| tests/test_table.py::test_render_table | atomic | - | source-only | asserts a very large exact table rendering fixture |
| tests/test_table.py::test_not_renderable | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_table.py::test_init_append_column | atomic | - | source-only | constructs Column with private _index |
| tests/test_table.py::test_rich_measure | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_table.py::test_min_width | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_table.py::test_no_columns | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_table.py::test_get_row_style | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_table.py::test_vertical_align_top | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_table.py::test_table_show_header_false_substitution[None- 1  2 \n 3  4 \n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_table.py::test_table_show_header_false_substitution[box1-\u250c\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2510\n\u2502 1 \u2502 2 \u2502\n\u2502 3 \u2502 4 \u2502\n\u2514\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2518\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_table.py::test_table_show_header_false_substitution[box2-\u250c\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2510\n\u2502 1 \u2502 2 \u2502\n\u2502 3 \u2502 4 \u2502\n\u2514\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2518\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_table.py::test_table_show_header_false_substitution[box3-    \u2577    \n  1 \u2502 2  \n  3 \u2502 4  \n    \u2575    \n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_table.py::test_table_show_header_false_substitution[box4-    \u2577    \n  1 \u2502 2  \n  3 \u2502 4  \n    \u2575    \n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_table.py::test_table_show_header_false_substitution[box5-+---+---+\n\| 1 \| 2 \|\n\| 3 \| 4 \|\n+---+---+\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_table.py::test_section | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_table.py::test_placement_table_box_elements[False-False-abbbbbcbbbbbbbbbcbbbbcbbbbbd\n1Dec  2Skywalker2275M2375M 3\n4May  5Solo     5275M5393M 6\nijjjjjkjjjjjjjjjkjjjjkjjjjjl\n7Dec  8Last Jedi8262M81333M9\nqrrrrrsrrrrrrrrrsrrrrsrrrrrt\n] | atomic | - | excluded | mutates table.box.__dict__ private implementation shape |
| tests/test_table.py::test_placement_table_box_elements[True-False-abbbbbcbbbbbbbbbcbbbbcbbbbbd\n1Month2Nickname 2Cost2Gross3\nefffffgfffffffffgffffgfffffh\n4Dec  5Skywalker5275M5375M 6\n4May  5Solo     5275M5393M 6\nijjjjjkjjjjjjjjjkjjjjkjjjjjl\n7Dec  8Last Jedi8262M81333M9\nqrrrrrsrrrrrrrrrsrrrrsrrrrrt\n] | atomic | - | excluded | mutates table.box.__dict__ private implementation shape |
| tests/test_table.py::test_placement_table_box_elements[False-True-abbbbbcbbbbbbbbbcbbbbcbbbbbd\n1Dec  2Skywalker2275M2375M 3\n4May  5Solo     5275M5393M 6\nijjjjjkjjjjjjjjjkjjjjkjjjjjl\n4Dec  5Last Jedi5262M51333M6\nmnnnnnonnnnnnnnnonnnnonnnnnp\n7MONTH8NICKNAME 8COST8GROSS9\nqrrrrrsrrrrrrrrrsrrrrsrrrrrt\n] | atomic | - | excluded | mutates table.box.__dict__ private implementation shape |
| tests/test_table.py::test_placement_table_box_elements[True-True-abbbbbcbbbbbbbbbcbbbbcbbbbbd\n1Month2Nickname 2Cost2Gross3\nefffffgfffffffffgffffgfffffh\n4Dec  5Skywalker5275M5375M 6\n4May  5Solo     5275M5393M 6\nijjjjjkjjjjjjjjjkjjjjkjjjjjl\n4Dec  5Last Jedi5262M51333M6\nmnnnnnonnnnnnnnnonnnnonnnnnp\n7MONTH8NICKNAME 8COST8GROSS9\nqrrrrrsrrrrrrrrrsrrrrsrrrrrt\n] | atomic | - | excluded | mutates table.box.__dict__ private implementation shape |
| tests/test_table.py::test_columns_highlight_added_by_add_row | atomic | - | source-only | asserts exact ANSI byte sequence and internal highlight propagation |
| tests/test_table.py::test_padding_width | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_text.py::test_span | atomic | ### Text | covered |  |
| tests/test_text.py::test_span_split | atomic | ### Text | covered |  |
| tests/test_text.py::test_span_move | atomic | ### Text | covered |  |
| tests/test_text.py::test_span_right_crop | atomic | ### Text | covered |  |
| tests/test_text.py::test_len | atomic | ### Text | covered |  |
| tests/test_text.py::test_cell_len | atomic | ### Text | covered |  |
| tests/test_text.py::test_bool | atomic | ### Text | covered |  |
| tests/test_text.py::test_str | atomic | ### Text | covered |  |
| tests/test_text.py::test_repr | atomic | - | source-only | repr formatting is not a stable behavioral contract |
| tests/test_text.py::test_add | atomic | ### Text | covered |  |
| tests/test_text.py::test_eq | atomic | ### Text | covered |  |
| tests/test_text.py::test_contain | atomic | ### Text | covered |  |
| tests/test_text.py::test_plain_property | atomic | ### Text | covered |  |
| tests/test_text.py::test_plain_property_setter | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_from_markup | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_from_ansi | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_copy | atomic | ### Text | covered |  |
| tests/test_text.py::test_rstrip | atomic | ### Text | covered |  |
| tests/test_text.py::test_rstrip_end | atomic | ### Text | covered |  |
| tests/test_text.py::test_stylize | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_stylize_before | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_stylize_negative_index | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_highlight_regex | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_highlight_regex_callable | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_highlight_words | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_set_length | atomic | ### Text | covered |  |
| tests/test_text.py::test_console_width | atomic | ### Text | covered |  |
| tests/test_text.py::test_join | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_trim_spans | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_pad_left | atomic | ### Text | covered |  |
| tests/test_text.py::test_pad_right | atomic | ### Text | covered |  |
| tests/test_text.py::test_append | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_append_text | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_end | atomic | ### Text | covered |  |
| tests/test_text.py::test_split | atomic | ### Text | covered |  |
| tests/test_text.py::test_split_spans | atomic | ### Text | covered |  |
| tests/test_text.py::test_divide | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_right_crop | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_wrap_3 | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_4 | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_wrapped_word_length_greater_than_available_width | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_cjk | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_cjk_width_mid_character | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_cjk_mixed | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_long | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_long_multi_codepoint | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_overflow | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_overflow_long | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_long_words | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_long_words_2 | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_long_words_followed_by_other_words | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_long_word_preceeded_by_word_of_full_line_length | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_multiple_consecutive_spaces | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_multi_codepoint | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_wrap_long_words_justify_left | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_leading_and_trailing_whitespace | atomic | - | excluded | accesses private attribute/helper _lines |
| tests/test_text.py::test_no_wrap_no_crop | atomic | ### Text | covered |  |
| tests/test_text.py::test_fit | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_tabs | atomic | ### Text | covered |  |
| tests/test_text.py::test_render | integration | ### Text | covered |  |
| tests/test_text.py::test_render_simple | integration | ### Text | covered |  |
| tests/test_text.py::test_print[.-.\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_text.py::test_print[print_text1-. .\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_text.py::test_print[print_text2-Hello World !\n] | atomic | - | source-only | line-unsafe parameterized nodeid with newline/carriage escape and exact output oracle |
| tests/test_text.py::test_print_sep_end[.-.X] | integration | ### Text | covered |  |
| tests/test_text.py::test_print_sep_end[print_text1-..X] | integration | ### Text | covered |  |
| tests/test_text.py::test_print_sep_end[print_text2-HelloWorld!X] | integration | ### Text | covered |  |
| tests/test_text.py::test_tabs_to_spaces | atomic | ### Text | covered |  |
| tests/test_text.py::test_tabs_to_spaces_spans[-4--expected_spans0] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[\t-4-    -expected_spans1] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[\tbar-4-    bar-expected_spans2] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[foo\tbar-4-foo bar-expected_spans3] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[foo\nbar\nbaz-4-foo\nbar\nbaz-expected_spans4] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[[bold]foo\tbar-4-foo bar-expected_spans5] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[[bold]\tbar-4-    bar-expected_spans6] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[\t[bold]bar-4-    bar-expected_spans7] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[[red]foo\tbar\n[green]egg\tbaz-8-foo     bar\negg     baz-expected_spans8] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[[bold]X\tY-8-X       Y-expected_spans9] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[[bold]\U0001f4a9\t\U0001f4a9-8-\U0001f4a9      \U0001f4a9-expected_spans10] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_tabs_to_spaces_spans[[bold]\U0001f4a9\U0001f4a9\U0001f4a9\U0001f4a9\t\U0001f4a9-8-\U0001f4a9\U0001f4a9\U0001f4a9\U0001f4a9        \U0001f4a9-expected_spans11] | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_markup_switch | atomic | ### Text | covered |  |
| tests/test_text.py::test_emoji | atomic | ### Text | covered |  |
| tests/test_text.py::test_emoji_switch | atomic | ### Text | covered |  |
| tests/test_text.py::test_assemble | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_assemble_meta | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_styled | atomic | - | excluded | accesses private attribute/helper _spans |
| tests/test_text.py::test_strip_control_codes | atomic | ### Text | covered |  |
| tests/test_text.py::test_get_style_at_offset | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis[Hello-10-Hello] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis[Hello-5-Hello] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis[Hello-4-Hel\u2026] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis[Hello-3-He\u2026] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis[Hello-2-H\u2026] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis[Hello-1-\u2026] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis_pad[Hello-5-Hello] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis_pad[Hello-10-Hello     ] | atomic | ### Text | covered |  |
| tests/test_text.py::test_truncate_ellipsis_pad[Hello-3-He\u2026] | atomic | ### Text | covered |  |
| tests/test_text.py::test_pad | atomic | ### Text | covered |  |
| tests/test_text.py::test_align_left | atomic | ### Text | covered |  |
| tests/test_text.py::test_align_right | atomic | ### Text | covered |  |
| tests/test_text.py::test_align_center | atomic | ### Text | covered |  |
| tests/test_text.py::test_detect_indentation | atomic | ### Text | covered |  |
| tests/test_text.py::test_indentation_guides | atomic | ### Text | covered |  |
| tests/test_text.py::test_slice | atomic | ### Text | covered |  |
| tests/test_text.py::test_wrap_invalid_style | atomic | ### Text | covered |  |
| tests/test_text.py::test_apply_meta | atomic | ### Text | covered |  |
| tests/test_text.py::test_on | atomic | ### Text | covered |  |
| tests/test_text.py::test_markup_property | atomic | ### Text | covered |  |
| tests/test_text.py::test_extend_style | atomic | ### Text | covered |  |
| tests/test_text.py::test_append_tokens | atomic | ### Text | covered |  |
| tests/test_text.py::test_append_loop_regression | atomic | ### Text | covered |  |
| tests/test_text.py::test_soft_wrap | atomic | ### Text | covered |  |
| tests/test_text.py::test_soft_wrap_styled | atomic | ### Text | covered |  |
| tests/test_theme.py::test_inherit | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_theme.py::test_config | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_theme.py::test_from_file | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_theme.py::test_read | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_theme.py::test_theme_stack | atomic | ### Styles, Colors, Themes, Markup, and Highlighting | covered |  |
| tests/test_tools.py::test_loop_first | atomic | - | excluded | top-level imports from rich._loop and rich._ratio |
| tests/test_tools.py::test_loop_last | atomic | - | excluded | top-level imports from rich._loop and rich._ratio |
| tests/test_tools.py::test_loop_first_last | atomic | - | excluded | top-level imports from rich._loop and rich._ratio |
| tests/test_tools.py::test_ratio_distribute | atomic | - | excluded | top-level imports from rich._loop and rich._ratio |
| tests/test_traceback.py::test_handler | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_capture | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_no_exception | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_print_exception | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_print_exception_no_msg | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_print_exception_locals | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_syntax_error | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_nested_exception | system_e2e | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_caused_exception | system_e2e | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_filename_with_bracket | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_filename_not_a_file | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_traceback_console_theme_applies | atomic | - | source-only | repr formatting is not a stable behavioral contract |
| tests/test_traceback.py::test_broken_str | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_guess_lexer | atomic | - | excluded | accesses Traceback._guess_lexer private helper |
| tests/test_traceback.py::test_guess_lexer_yaml_j2 | atomic | - | excluded | accesses Traceback._guess_lexer private helper |
| tests/test_traceback.py::test_recursive | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_suppress | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_rich_traceback_omit_optional_local_flag[True-3-expected_frame_names0] | atomic | - | excluded | depends on private _rich_traceback_omit local-name convention |
| tests/test_traceback.py::test_rich_traceback_omit_optional_local_flag[False-4-expected_frame_names1] | atomic | - | excluded | depends on private _rich_traceback_omit local-name convention |
| tests/test_traceback.py::test_traceback_finely_grained_missing | atomic | - | excluded | version-specific internal last_instruction shape |
| tests/test_traceback.py::test_traceback_finely_grained | atomic | - | excluded | version-specific internal last_instruction shape |
| tests/test_traceback.py::test_notes | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_traceback.py::test_recursive_exception | integration | ### Logging, Tracebacks, Prompts, and Utilities | covered |  |
| tests/test_tree.py::test_render_single_node | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_tree.py::test_render_single_branch | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_tree.py::test_render_double_branch | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_tree.py::test_render_ascii | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_tree.py::test_render_tree_non_win32 | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_tree.py::test_render_tree_win32 | atomic | - | excluded | Windows-specific platform dependency / not scoreable on current host |
| tests/test_tree.py::test_render_tree_hide_root_non_win32 | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_tree.py::test_render_tree_hide_root_win32 | atomic | - | excluded | Windows-specific platform dependency / not scoreable on current host |
| tests/test_tree.py::test_tree_measure | integration | ### Tables and Layout Renderables | covered |  |
| tests/test_unicode_data.py::test_load | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_parse_version[1-version_tuple0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_parse_version[1.0-version_tuple1] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_parse_version[1.2-version_tuple2] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_parse_version[1.2.3-version_tuple3] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[0-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[1-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[1.0-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[1.0.0-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[4.0.0-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[4.0.2-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[4.1.0-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[4.1.1-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[4.2.1-4.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[5-5.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[5.0-5.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[5.0.0-5.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[5.0.1-5.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[5.1.0-5.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[5.1.1-5.1.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[17.0.0-17.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[17.0.1-17.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[17.1.0-17.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version[18.0.0-17.0.0] | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_unicode_data.py::test_load_version_invalid | atomic | - | excluded | top-level import from rich._unicode_data |
| tests/test_windows_renderer.py::test_text_only | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_text_multiple_segments | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_text_with_style | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_cursor_move_to | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_carriage_return | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_home | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_cursor_single_cell_movement[9-move_cursor_up] | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_cursor_single_cell_movement[10-move_cursor_down] | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_cursor_single_cell_movement[11-move_cursor_forward] | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_cursor_single_cell_movement[12-move_cursor_backward] | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_erase_line[0-erase_end_of_line] | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_erase_line[1-erase_start_of_line] | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_erase_line[2-erase_line] | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_show_cursor | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_hide_cursor | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_cursor_move_to_column | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |
| tests/test_windows_renderer.py::test_control_set_terminal_window_title | atomic | - | excluded | top-level imports from rich._win32_console and rich._windows_renderer |

Total: 981 | kept (covered): 293 | spec_gap: 0 | source-only: 214 | excluded: 474 | final scoreable: 293
