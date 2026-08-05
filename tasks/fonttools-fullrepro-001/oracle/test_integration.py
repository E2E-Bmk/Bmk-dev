from __future__ import annotations

import io

import pytest


@pytest.mark.depends_on("test_font_bytes_can_reload_with_ttfont", "test_glyph_order_preserves_builder_sequence")
def test_saved_font_reloads_same_glyph_order_and_table_set(sample_font, reloaded_font):
    assert reloaded_font.getGlyphOrder() == sample_font.getGlyphOrder()
    assert set(reloaded_font.keys()) == set(sample_font.keys())


@pytest.mark.depends_on("test_character_map_projects_unicode_to_glyph_names", "test_font_bytes_can_reload_with_ttfont")
def test_saved_font_reloads_same_best_cmap(sample_font, reloaded_font):
    assert reloaded_font.getBestCmap() == sample_font.getBestCmap()


@pytest.mark.depends_on("test_horizontal_metrics_are_rounded_and_accessible", "test_font_bytes_can_reload_with_ttfont")
def test_saved_font_reloads_same_horizontal_metrics(sample_font, reloaded_font):
    assert reloaded_font["hmtx"].metrics == sample_font["hmtx"].metrics


@pytest.mark.depends_on("test_name_table_returns_expected_english_strings", "test_font_bytes_can_reload_with_ttfont")
def test_saved_font_reloads_name_strings(reloaded_font):
    names = reloaded_font["name"]
    assert names.getDebugName(1) == "Oracle Sample"
    assert names.getDebugName(4) == "Oracle Sample Regular"


@pytest.mark.depends_on("test_save_xml_can_emit_selected_tables", "test_ttfont_import_xml_accepts_generated_selected_table")
def test_xml_export_import_preserves_head_units(sample_font, tmp_path):
    from fontTools.ttLib import TTFont

    path = tmp_path / "head.ttx"
    sample_font.saveXML(path, tables=["head"])
    imported = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    imported.importXML(path)
    assert imported["head"].unitsPerEm == sample_font["head"].unitsPerEm


@pytest.mark.depends_on("test_save_xml_can_emit_selected_tables", "test_name_table_returns_expected_english_strings")
def test_xml_export_import_preserves_name_table(sample_font, tmp_path):
    from fontTools.ttLib import TTFont

    path = tmp_path / "name.ttx"
    sample_font.saveXML(path, tables=["name"])
    imported = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    imported.importXML(path)
    assert imported["name"].getDebugName(6) == "OracleSample-Regular"


@pytest.mark.depends_on("test_bounds_pen_calculates_drawn_glyph_bounds", "test_get_glyph_set_exposes_metrics_and_bounds")
def test_glyph_set_draw_bounds_match_glyf_bounds(reloaded_font):
    from fontTools.pens.boundsPen import BoundsPen

    glyph_set = reloaded_font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set["B"].draw(pen)
    glyph = reloaded_font["glyf"]["B"]
    assert pen.bounds == (glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax)


@pytest.mark.depends_on("test_recording_pen_captures_public_pen_protocol", "test_glyf_table_contains_simple_and_component_glyphs")
def test_component_glyph_draw_records_component_references(reloaded_font):
    from fontTools.pens.recordingPen import RecordingPen

    pen = RecordingPen()
    reloaded_font.getGlyphSet()["Aacute"].draw(pen)
    operators = [entry[0] for entry in pen.value]
    assert operators == ["addComponent", "addComponent"]


@pytest.mark.depends_on("test_subset_options_default_to_recommended_glyph_names", "test_subsetter_populate_records_unicode_and_glyph_requests")
def test_subsetter_reduces_font_to_requested_text_and_components(sample_font):
    from fontTools.subset import Options, Subsetter

    options = Options()
    options.name_IDs = ["*"]
    subsetter = Subsetter(options=options)
    subsetter.populate(text="A")
    subsetter.subset(sample_font)
    order = sample_font.getGlyphOrder()
    assert "A" in order
    assert "B" not in order
    assert "space" not in order


@pytest.mark.depends_on("test_subsetter_populate_records_unicode_and_glyph_requests", "test_glyf_table_contains_simple_and_component_glyphs")
def test_subsetter_keeps_component_dependencies_for_aacute(sample_font):
    from fontTools.subset import Subsetter

    subsetter = Subsetter()
    subsetter.populate(unicodes=[193])
    subsetter.subset(sample_font)
    order = sample_font.getGlyphOrder()
    assert {"Aacute", "A", "acute"} <= set(order)
    assert "B" not in order


@pytest.mark.depends_on("test_font_save_to_bytes_produces_sfnt_header", "test_get_best_cmap_prefers_unicode_mapping")
def test_subset_font_saves_and_reloads_with_filtered_cmap(sample_font):
    from fontTools.subset import Subsetter
    from fontTools.ttLib import TTFont

    subsetter = Subsetter()
    subsetter.populate(text="B")
    subsetter.subset(sample_font)
    stream = io.BytesIO()
    sample_font.save(stream)
    reloaded = TTFont(io.BytesIO(stream.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    assert reloaded.getBestCmap() == {66: "B"}


@pytest.mark.depends_on("test_new_table_can_create_and_attach_meta_table", "test_font_save_to_bytes_produces_sfnt_header")
def test_added_meta_table_survives_binary_round_trip(sample_font):
    from fontTools.ttLib import TTFont, newTable

    meta = newTable("meta")
    meta.data = {"dlng": "Latn"}
    sample_font["meta"] = meta
    stream = io.BytesIO()
    sample_font.save(stream)
    reloaded = TTFont(io.BytesIO(stream.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    assert reloaded["meta"].data["dlng"] == "Latn"


@pytest.mark.depends_on("test_sorted_tag_list_orders_font_tables", "test_reorder_font_tables_moves_glyph_order_first")
def test_sorted_table_projection_contains_same_tags_after_reload(reloaded_font):
    from fontTools.ttLib import sortedTagList

    assert set(sortedTagList(reloaded_font.keys())) == set(reloaded_font.keys())


@pytest.mark.depends_on("test_xml_tag_conversion_round_trips_public_tag", "test_save_xml_can_emit_selected_tables")
def test_xml_tag_conversion_matches_emitted_table_name(sample_font, tmp_path):
    from fontTools.ttLib import tagToXML

    path = tmp_path / "os2.ttx"
    sample_font.saveXML(path, tables=["OS/2"])
    assert f"<{tagToXML('OS/2')}>" in path.read_text(encoding="utf-8")


@pytest.mark.depends_on("test_get_best_cmap_prefers_unicode_mapping", "test_subsetter_populate_records_unicode_and_glyph_requests")
def test_text_subset_only_retains_requested_unicode_mapping(sample_font):
    from fontTools.subset import Subsetter

    subsetter = Subsetter()
    subsetter.populate(text="AB")
    subsetter.subset(sample_font)
    assert sample_font.getBestCmap() == {65: "A", 66: "B"}


@pytest.mark.depends_on("test_glyph_bounds_are_calculated_from_contours", "test_font_bytes_can_reload_with_ttfont")
def test_reloaded_glyph_bounds_match_original(sample_font, reloaded_font):
    for name in ["A", "B", "acute", "smile"]:
        original = sample_font["glyf"][name]
        reloaded = reloaded_font["glyf"][name]
        assert (reloaded.xMin, reloaded.yMin, reloaded.xMax, reloaded.yMax) == (
            original.xMin,
            original.yMin,
            original.xMax,
            original.yMax,
        )


@pytest.mark.depends_on("test_ttfont_import_xml_accepts_generated_selected_table", "test_font_save_to_bytes_produces_sfnt_header")
def test_imported_xml_table_can_be_saved_with_generated_font(sample_font, tmp_path):
    from fontTools.ttLib import TTFont

    path = tmp_path / "head.ttx"
    sample_font.saveXML(path, tables=["head"])
    imported = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    imported.importXML(path)
    sample_font["head"] = imported["head"]
    stream = io.BytesIO()
    sample_font.save(stream)
    assert stream.getvalue()[:4] == b"\x00\x01\x00\x00"


@pytest.mark.depends_on("test_ttfont_set_glyph_order_updates_ordered_projection", "test_get_best_cmap_prefers_unicode_mapping")
def test_glyph_order_change_preserves_existing_cmap_names(sample_font):
    sample_font.setGlyphOrder([".notdef", "space", "B", "A", "acute", "Aacute", "smile"])
    assert sample_font.getGlyphOrder()[2:4] == ["B", "A"]
    assert sample_font.getBestCmap()[65] == "A"


@pytest.mark.depends_on("test_tt_glyph_pen_builds_quadratic_glyph", "test_get_glyph_set_exposes_metrics_and_bounds")
def test_added_pen_glyph_can_be_addressed_through_glyph_set(sample_font):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen(None)
    pen.moveTo((10, 10))
    pen.lineTo((210, 10))
    pen.lineTo((210, 210))
    pen.closePath()
    sample_font.setGlyphOrder(sample_font.getGlyphOrder() + ["C"])
    sample_font["glyf"].glyphs["C"] = pen.glyph()
    sample_font["glyf"]["C"].recalcBounds(sample_font["glyf"])
    sample_font["hmtx"].metrics["C"] = (400, 10)
    glyph = sample_font.getGlyphSet()["C"]
    bounds_pen = BoundsPen(sample_font.getGlyphSet())
    glyph.draw(bounds_pen)
    assert glyph.width == 400
    assert bounds_pen.bounds[2] == 210


@pytest.mark.depends_on("test_os2_table_keeps_vendor_and_windows_extents", "test_hhea_table_keeps_configured_vertical_extents")
def test_vertical_metric_tables_remain_consistent_after_reload(reloaded_font):
    assert reloaded_font["OS/2"].sTypoAscender == reloaded_font["hhea"].ascent
    assert reloaded_font["OS/2"].sTypoDescender == reloaded_font["hhea"].descent


@pytest.mark.depends_on("test_xml_writer_includes_fonttools_root_element", "test_font_bytes_can_reload_with_ttfont")
def test_binary_to_xml_to_binary_preserves_name_projection(sample_font, tmp_path):
    from fontTools.ttLib import TTFont

    binary = io.BytesIO()
    sample_font.save(binary)
    reloaded_sample = TTFont(io.BytesIO(binary.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    xml_path = tmp_path / "sample.ttx"
    reloaded_sample.saveXML(xml_path)
    compiled = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    compiled.importXML(xml_path)
    stream = io.BytesIO()
    compiled.save(stream)
    reloaded = TTFont(io.BytesIO(stream.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    assert reloaded["name"].getDebugName(1) == "Oracle Sample"


@pytest.mark.depends_on("test_subset_options_default_to_recommended_glyph_names", "test_name_table_returns_expected_english_strings")
def test_subset_options_can_retain_requested_name_records(sample_font):
    from fontTools.subset import Options, Subsetter

    options = Options()
    options.name_IDs = [1, 2, 6]
    subsetter = Subsetter(options=options)
    subsetter.populate(text="A")
    subsetter.subset(sample_font)
    assert sample_font["name"].getDebugName(1) == "Oracle Sample"
    assert sample_font["name"].getDebugName(6) == "OracleSample-Regular"


@pytest.mark.depends_on(
    "test_recording_pen_captures_public_pen_protocol",
    "test_subsetter_populate_records_unicode_and_glyph_requests",
    "test_glyf_table_contains_simple_and_component_glyphs",
)
def test_subset_component_glyph_draws_after_dependency_closure(sample_font):
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.subset import Subsetter

    subsetter = Subsetter()
    subsetter.populate(unicodes=[193])
    subsetter.subset(sample_font)
    pen = RecordingPen()
    sample_font.getGlyphSet()["Aacute"].draw(pen)
    assert [entry[0] for entry in pen.value] == ["addComponent", "addComponent"]


@pytest.mark.depends_on("test_new_table_can_create_and_attach_meta_table", "test_save_xml_can_emit_selected_tables")
def test_meta_table_can_be_exported_after_binary_reload(sample_font, tmp_path):
    from fontTools.ttLib import TTFont, newTable

    meta = newTable("meta")
    meta.data = {"slng": "Latn"}
    sample_font["meta"] = meta
    stream = io.BytesIO()
    sample_font.save(stream)
    reloaded = TTFont(io.BytesIO(stream.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    path = tmp_path / "meta.ttx"
    reloaded.saveXML(path, tables=["meta"])
    assert '<text tag="slng">' in path.read_text(encoding="utf-8")


@pytest.mark.depends_on("test_cmap_uses_format_twelve_for_non_bmp_codepoint", "test_subsetter_populate_records_unicode_and_glyph_requests")
def test_non_bmp_subset_retains_format_twelve_mapping(sample_font):
    from fontTools.subset import Subsetter

    subsetter = Subsetter()
    subsetter.populate(unicodes=[0x1F600])
    subsetter.subset(sample_font)
    assert sample_font.getBestCmap() == {0x1F600: "smile"}
    assert any(table.format == 12 for table in sample_font["cmap"].tables)


@pytest.mark.depends_on("test_ttfont_set_glyph_order_updates_ordered_projection", "test_font_save_to_bytes_produces_sfnt_header")
def test_reordered_glyph_order_survives_binary_round_trip(sample_font):
    from fontTools.ttLib import TTFont

    reordered_names = [".notdef", "space", "B", "A", "acute", "Aacute", "smile"]
    sample_font.setGlyphOrder(reordered_names)
    stream = io.BytesIO()
    sample_font.save(stream)
    reloaded = TTFont(io.BytesIO(stream.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    assert reloaded.getGlyphOrder() == reordered_names
    assert reloaded.getBestCmap()[65] == "A"


@pytest.mark.depends_on("test_glyf_table_contains_simple_and_component_glyphs", "test_font_bytes_can_reload_with_ttfont")
def test_component_data_survives_binary_round_trip(reloaded_font):
    components = reloaded_font["glyf"]["Aacute"].components
    assert [(component.glyphName, component.x, component.y) for component in components] == [
        ("A", 0, 0),
        ("acute", 220, 0),
    ]


@pytest.mark.depends_on("test_subsetter_populate_records_unicode_and_glyph_requests", "test_glyf_table_contains_simple_and_component_glyphs")
def test_glyph_name_subset_keeps_component_closure_after_reload(sample_font):
    from fontTools.subset import Options, Subsetter
    from fontTools.ttLib import TTFont

    options = Options()
    options.glyph_names = True
    subsetter = Subsetter(options=options)
    subsetter.populate(glyphs=["Aacute"])
    subsetter.subset(sample_font)
    stream = io.BytesIO()
    sample_font.save(stream)
    reloaded = TTFont(io.BytesIO(stream.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    assert {"Aacute", "A", "acute"} <= set(reloaded.getGlyphOrder())
    assert "B" not in reloaded.getGlyphOrder()
    assert reloaded.getBestCmap() == {193: "Aacute"}


@pytest.mark.depends_on("test_save_xml_can_emit_selected_tables", "test_hhea_table_keeps_configured_vertical_extents", "test_os2_table_keeps_vendor_and_windows_extents")
def test_xml_export_import_preserves_horizontal_metric_tables(sample_font, tmp_path):
    from fontTools.ttLib import TTFont

    path = tmp_path / "metrics.ttx"
    sample_font.saveXML(path, tables=["hhea", "OS/2"])
    imported = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    imported.importXML(path)
    assert imported["hhea"].ascent == sample_font["hhea"].ascent
    assert imported["hhea"].descent == sample_font["hhea"].descent
    assert imported["OS/2"].achVendID == sample_font["OS/2"].achVendID
    assert imported["OS/2"].usWinDescent == sample_font["OS/2"].usWinDescent


@pytest.mark.depends_on("test_subsetter_populate_records_unicode_and_glyph_requests", "test_get_glyph_set_exposes_metrics_and_bounds")
def test_subset_glyph_remains_drawable_with_original_metrics(sample_font):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.subset import Subsetter

    subsetter = Subsetter()
    subsetter.populate(text="A")
    subsetter.subset(sample_font)
    glyph_set = sample_font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set["A"].draw(pen)
    assert glyph_set["A"].width == 620
    assert pen.bounds == (90, 0, 530, 700)
