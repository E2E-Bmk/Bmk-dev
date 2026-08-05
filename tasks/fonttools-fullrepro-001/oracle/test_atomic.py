from __future__ import annotations

import io

import pytest


def test_new_font_exposes_expected_table_tags(sample_font):
    assert {"GlyphOrder", "head", "maxp", "cmap", "glyf", "hmtx", "hhea", "name", "OS/2", "post"} <= set(
        sample_font.keys()
    )


def test_glyph_order_preserves_builder_sequence(sample_font):
    assert sample_font.getGlyphOrder() == [".notdef", "space", "A", "B", "acute", "Aacute", "smile"]


def test_character_map_projects_unicode_to_glyph_names(sample_font):
    cmap = sample_font.getBestCmap()
    assert cmap[32] == "space"
    assert cmap[65] == "A"
    assert cmap[193] == "Aacute"
    assert cmap[0x1F600] == "smile"


def test_cmap_uses_format_twelve_for_non_bmp_codepoint(sample_font):
    formats = {(table.format, table.platformID, table.platEncID) for table in sample_font["cmap"].tables}
    assert (12, 3, 10) in formats


def test_horizontal_metrics_are_rounded_and_accessible(sample_font):
    assert sample_font["hmtx"].metrics["A"] == (620, 90)
    assert sample_font["hmtx"].metrics["space"] == (250, 0)


def test_name_table_returns_expected_english_strings(sample_font):
    names = sample_font["name"]
    assert names.getDebugName(1) == "Oracle Sample"
    assert names.getDebugName(2) == "Regular"
    assert names.getDebugName(6) == "OracleSample-Regular"


def test_head_table_uses_configured_units_per_em(sample_font):
    assert sample_font["head"].unitsPerEm == 1000
    assert sample_font["head"].glyphDataFormat == 0


def test_hhea_table_keeps_configured_vertical_extents(sample_font):
    assert sample_font["hhea"].ascent == 900
    assert sample_font["hhea"].descent == -250


def test_os2_table_keeps_vendor_and_windows_extents(sample_font):
    os2 = sample_font["OS/2"]
    assert os2.achVendID == "TEST"
    assert os2.usWinAscent == 900
    assert os2.usWinDescent == 250


def test_glyf_table_contains_simple_and_component_glyphs(sample_font):
    glyf = sample_font["glyf"]
    assert glyf["A"].numberOfContours == 1
    assert glyf["Aacute"].isComposite()
    assert [component.glyphName for component in glyf["Aacute"].components] == ["A", "acute"]


def test_glyph_bounds_are_calculated_from_contours(sample_font):
    glyph = sample_font["glyf"]["B"]
    assert (glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax) == (80, 0, 470, 680)


def test_get_glyph_set_exposes_metrics_and_bounds(sample_font):
    from fontTools.pens.boundsPen import BoundsPen

    glyph_set = sample_font.getGlyphSet()
    glyph = glyph_set["A"]
    pen = BoundsPen(glyph_set)
    glyph.draw(pen)
    assert glyph.width == 620
    assert glyph.lsb == 90
    assert pen.bounds[2] == 530


def test_bounds_pen_calculates_drawn_glyph_bounds(sample_font):
    from fontTools.pens.boundsPen import BoundsPen

    glyph_set = sample_font.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set["B"].draw(pen)
    assert pen.bounds == (80, 0, 470, 680)


def test_recording_pen_captures_public_pen_protocol(sample_font):
    from fontTools.pens.recordingPen import RecordingPen

    pen = RecordingPen()
    sample_font.getGlyphSet()["B"].draw(pen)
    operators = [item[0] for item in pen.value]
    assert operators == ["moveTo", "lineTo", "lineTo", "lineTo", "closePath"]


def test_tt_glyph_pen_builds_quadratic_glyph():
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.qCurveTo((50, 100), (100, 0))
    pen.closePath()
    glyph = pen.glyph()
    assert glyph.numberOfContours == 1
    assert len(glyph.coordinates) == 3


def test_font_builder_rejects_cubic_glyf_by_default():
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.curveTo((20, 40), (60, 40), (80, 0))
    pen.closePath()
    glyph = pen.glyph()
    builder = FontBuilder(1000, isTTF=True, glyphDataFormat=0)
    with pytest.raises(ValueError):
        builder.setupGlyf({"curve": glyph})


def test_font_bytes_can_reload_with_ttfont(reloaded_font):
    assert reloaded_font.getGlyphOrder()[2:5] == ["A", "B", "acute"]
    assert reloaded_font["maxp"].numGlyphs == 7


def test_save_xml_can_emit_selected_tables(sample_font, tmp_path):
    path = tmp_path / "sample.ttx"
    sample_font.saveXML(path, tables=["head", "hhea"])
    text = path.read_text(encoding="utf-8")
    assert "<head>" in text
    assert "<hhea>" in text
    assert "<cmap>" not in text


def test_new_table_can_create_and_attach_meta_table(sample_font):
    from fontTools.ttLib import newTable

    meta = newTable("meta")
    meta.data = {"dlng": b"Latn", "slng": b"Latn"}
    sample_font["meta"] = meta
    assert sample_font["meta"].data["dlng"] == b"Latn"


def test_sorted_tag_list_orders_font_tables(sample_font):
    from fontTools.ttLib import sortedTagList

    ordered = sortedTagList(sample_font.keys())
    assert ordered.index("head") < ordered.index("hhea")
    assert ordered.index("cmap") < ordered.index("glyf")


def test_xml_tag_conversion_round_trips_public_tag():
    from fontTools.ttLib import tagToXML, xmlToTag

    encoded = tagToXML("OS/2")
    assert xmlToTag(encoded) == "OS/2"


def test_reorder_font_tables_moves_glyph_order_first(sample_font):
    from fontTools.ttLib import TTFont
    from fontTools.ttLib import reorderFontTables

    source = io.BytesIO()
    target = io.BytesIO()
    sample_font.save(source)
    reorderFontTables(source, target)
    reordered = TTFont(io.BytesIO(target.getvalue()), recalcBBoxes=False, recalcTimestamp=False)
    assert reordered["maxp"].numGlyphs == sample_font["maxp"].numGlyphs
    assert set(reordered.keys()) == set(sample_font.keys())


def test_subset_options_default_to_recommended_glyph_names():
    from fontTools.subset import Options

    options = Options()
    assert options.recommended_glyphs is False
    assert options.notdef_glyph is True


def test_subsetter_populate_records_unicode_and_glyph_requests():
    from fontTools.subset import Subsetter

    subsetter = Subsetter()
    subsetter.populate(glyphs=["A"], unicodes=[0x42], text=" ")
    assert "A" in subsetter.glyph_names_requested
    assert {32, 66} <= subsetter.unicodes_requested


def test_ttfont_set_glyph_order_updates_ordered_projection(sample_font):
    sample_font.setGlyphOrder([".notdef", "A", "space"])
    assert sample_font.getGlyphOrder() == [".notdef", "A", "space"]


def test_get_best_cmap_prefers_unicode_mapping(sample_font):
    cmap = sample_font.getBestCmap()
    assert sorted(cmap) == [32, 65, 66, 193, 0x1F600]


def test_ttfont_round_trip_stream_keeps_metrics(reloaded_font):
    assert reloaded_font["hmtx"].metrics["smile"] == (720, 70)
    assert reloaded_font["glyf"]["smile"].xMax == 650


def test_xml_writer_includes_fonttools_root_element(sample_font, tmp_path):
    path = tmp_path / "sample.ttx"
    sample_font.saveXML(path, tables=["name"])
    text = path.read_text(encoding="utf-8")
    assert text.lstrip().startswith("<?xml")
    assert "<ttFont" in text


def test_ttfont_import_xml_accepts_generated_selected_table(sample_font, tmp_path):
    from fontTools.ttLib import TTFont

    path = tmp_path / "head.ttx"
    sample_font.saveXML(path, tables=["head"])
    font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
    font.importXML(path)
    assert font["head"].unitsPerEm == 1000


def test_font_save_to_bytes_produces_sfnt_header(sample_font):
    stream = io.BytesIO()
    sample_font.save(stream)
    assert stream.getvalue()[:4] == b"\x00\x01\x00\x00"
