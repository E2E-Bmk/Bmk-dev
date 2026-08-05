from __future__ import annotations

import io

import pytest

from conftest import roundtrip_from_file, roundtrip_from_stream


@pytest.mark.depends_on(
    "test_new_document_exposes_modelspace",
    "test_line_factory_stores_start_end_and_layer",
    "test_document_write_produces_readable_ascii_stream",
)
def test_new_document_entities_survive_text_stream_round_trip(document):
    import ezdxf

    document.modelspace().add_line((1, 2), (3, 4), dxfattribs={"layer": "DESIGN"})
    stream = io.StringIO()
    document.write(stream)
    stream.seek(0)
    loaded = ezdxf.read(stream)

    assert loaded.dxfversion == document.dxfversion
    assert len(loaded.modelspace().query("LINE")) == 1
    assert tuple(loaded.modelspace()[0].dxf.start) == (1.0, 2.0, 0.0)
    assert loaded.modelspace()[0].dxf.layer == "DESIGN"


@pytest.mark.depends_on(
    "test_default_paperspace_is_available",
    "test_layout_manager_creates_named_paperspace",
    "test_viewport_factory_is_available_in_paperspace",
)
def test_modelspace_and_named_paperspace_survive_file_round_trip(document, tmp_path):
    import ezdxf

    document.modelspace().add_circle((0, 0), 2)
    sheet = document.layouts.new("SheetA")
    sheet.add_line((0, 0), (10, 10))
    sheet.add_viewport((5, 5), (10, 8), (0, 0), 20)
    document.layouts.set_active_layout("SheetA")

    loaded = roundtrip_from_file(document, tmp_path)

    assert len(loaded.modelspace()) == 1
    assert len(loaded.paperspace("SheetA")) == 2
    assert loaded.active_layout().name == "SheetA"
    assert loaded.paperspace("SheetA")[0].dxf.paperspace == 1


@pytest.mark.depends_on(
    "test_block_table_creates_named_block_and_entity_space",
    "test_block_reference_factory_stores_insert_transform",
)
def test_block_definition_and_reference_survive_file_round_trip(
    block_document,
    tmp_path,
):
    document = block_document
    document.modelspace().add_blockref(
        "SYMBOL",
        (10, 20),
        dxfattribs={"xscale": 2, "rotation": 15},
    )

    loaded = roundtrip_from_file(document, tmp_path)

    block = loaded.blocks.get("SYMBOL")
    insert = loaded.modelspace().query("INSERT")[0]
    assert len(block) == 3
    assert insert.dxf.name == "SYMBOL"
    assert tuple(insert.dxf.insert) == (10.0, 20.0, 0.0)
    assert insert.dxf.xscale == 2.0
    assert insert.dxf.rotation == 15.0


@pytest.mark.depends_on(
    "test_block_reference_attribute_can_be_added_and_placed",
    "test_block_table_creates_named_block_and_entity_space",
)
def test_block_attribute_template_and_value_survive_round_trip(
    block_document,
    tmp_path,
):
    insert = block_document.modelspace().add_blockref("SYMBOL", (10, 20))
    insert.add_auto_attribs({"LABEL": "Filled"})

    loaded = roundtrip_from_file(block_document, tmp_path)
    loaded_insert = loaded.modelspace().query("INSERT")[0]

    assert len(loaded_insert.attribs) == 1
    assert loaded_insert.attribs[0].dxf.tag == "LABEL"
    assert loaded_insert.attribs[0].dxf.text == "Filled"


@pytest.mark.depends_on(
    "test_layer_table_adds_colored_layer_and_supports_case_insensitive_lookup",
    "test_query_attribute_filter_selects_layer",
    "test_layout_groupby_groups_entities_by_layer",
)
def test_layer_assignment_query_and_groupby_agree_after_round_trip(
    populated_document,
    tmp_path,
):
    loaded = roundtrip_from_file(populated_document, tmp_path)
    msp = loaded.modelspace()
    groups = msp.groupby("layer")

    assert len(msp.query('*[layer=="DESIGN"]')) == len(groups["DESIGN"])
    assert len(msp.query('*[layer=="ANNOTATION"]')) == len(groups["ANNOTATION"])
    assert sorted(groups) == ["ANNOTATION", "DESIGN"]


@pytest.mark.depends_on(
    "test_entity_query_assignment_updates_supported_entities",
    "test_entity_dxf_namespace_supports_assignment_and_set",
)
def test_query_mutation_is_reflected_in_serialized_entities(document, tmp_path):
    msp = document.modelspace()
    msp.add_line((0, 0), (1, 0), dxfattribs={"layer": "DESIGN"})
    msp.add_circle((2, 0), 1, dxfattribs={"layer": "DESIGN"})
    selected = msp.query("LINE CIRCLE")
    selected.layer = "UPDATED"

    loaded = roundtrip_from_file(document, tmp_path)

    assert len(loaded.modelspace().query('*[layer=="UPDATED"]')) == 2
    assert not loaded.modelspace().query('*[layer=="DESIGN"]')


@pytest.mark.depends_on(
    "test_query_attribute_filter_can_ignore_case",
    "test_layout_groupby_accepts_a_public_key_function",
    "test_rgb_integer_helpers_round_trip",
)
def test_case_insensitive_query_and_color_grouping_share_entity_selection(
    populated_document,
):
    msp = populated_document.modelspace()
    selected = msp.query('*[layer=="design"]i')
    groups = selected.groupby(key=lambda entity: entity.dxf.color)

    assert len(selected) == 5
    assert sum(len(entities) for entities in groups.values()) == 5
    assert set(groups) == {2, 256}


@pytest.mark.depends_on(
    "test_xdata_high_level_methods_store_and_replace_tags",
    "test_appdata_high_level_methods_store_and_discard_tags",
)
def test_appdata_and_xdata_survive_stream_round_trip(document):
    line = document.modelspace().add_line((0, 0), (1, 0))
    line.set_app_data("APPTEST", [(1, "application")])
    line.set_xdata("APPTEST", [(1000, "extended"), (1040, 4.5)])

    loaded = roundtrip_from_stream(document)
    loaded_line = loaded.modelspace().query("LINE")[0]

    assert loaded_line.has_app_data("APPTEST")
    assert loaded_line.has_xdata("APPTEST")
    assert [(tag.code, tag.value) for tag in loaded_line.get_app_data("APPTEST")] == [
        (1, "application")
    ]
    assert [tag.value for tag in loaded_line.get_xdata("APPTEST")] == [
        "extended",
        4.5,
    ]


@pytest.mark.depends_on(
    "test_user_xdata_list_commits_supported_values",
    "test_user_xdata_dict_commits_mapping_values",
)
def test_user_xdata_list_and_dict_survive_file_round_trip(document, tmp_path):
    from ezdxf.entities.xdata import XDataUserDict, XDataUserList

    line = document.modelspace().add_line((0, 0), (1, 0))
    with XDataUserList.entity(line, name="VALUES", appid="APPTEST") as values:
        values.append("one")
        values.append(2)
    with XDataUserDict.entity(line, name="META", appid="APPTEST") as metadata:
        metadata["label"] = "sample"
        metadata["count"] = 3

    loaded_line = roundtrip_from_file(document, tmp_path).modelspace()[0]
    with XDataUserList.entity(loaded_line, name="VALUES", appid="APPTEST") as values:
        assert list(values) == ["one", 2]
    with XDataUserDict.entity(loaded_line, name="META", appid="APPTEST") as metadata:
        assert dict(metadata) == {"label": "sample", "count": 3}


@pytest.mark.depends_on(
    "test_extension_dictionary_xrecord_exposes_public_tag_storage",
)
def test_extension_dictionary_xrecord_survives_file_round_trip(document, tmp_path):
    point = document.modelspace().add_point((1, 2))
    extension_dict = point.new_extension_dict()
    record = extension_dict.add_xrecord("DATA")
    record.extend([(1, "text"), (40, 3.5)])

    loaded_point = roundtrip_from_file(document, tmp_path).modelspace()[0]
    loaded_record = loaded_point.get_extension_dict().get("DATA")

    assert loaded_point.has_extension_dict
    assert [(tag.code, tag.value) for tag in loaded_record.tags] == [
        (1, "text"),
        (40, 3.5),
    ]


@pytest.mark.depends_on(
    "test_rgb_and_rgba_public_classes_round_trip_hex_and_floats",
    "test_transparency_helpers_preserve_endpoints",
    "test_layer_dxf_attributes_can_be_mutated",
)
def test_color_projections_survive_entity_and_layer_round_trip(document, tmp_path):
    from ezdxf import colors

    layer = document.layers.get("DESIGN")
    layer.dxf.true_color = colors.rgb2int((12, 34, 56))
    line = document.modelspace().add_line(
        (0, 0),
        (1, 0),
        dxfattribs={
            "layer": "DESIGN",
            "color": colors.YELLOW,
            "transparency": colors.float2transparency(0.25),
        },
    )
    line.dxf.true_color = colors.rgb2int((90, 80, 70))

    loaded = roundtrip_from_file(document, tmp_path)
    loaded_layer = loaded.layers.get("DESIGN")
    loaded_line = loaded.modelspace().query("LINE")[0]

    assert loaded_layer.dxf.true_color == colors.rgb2int((12, 34, 56))
    assert loaded_line.dxf.color == colors.YELLOW
    assert loaded_line.dxf.true_color == colors.rgb2int((90, 80, 70))
    assert colors.transparency2float(loaded_line.dxf.transparency) == pytest.approx(
        0.25,
        abs=1 / 255,
    )


@pytest.mark.depends_on(
    "test_entity_dxf_namespace_supports_assignment_and_set",
    "test_document_write_produces_readable_ascii_stream",
)
def test_line_geometry_mutation_survives_stream_round_trip(document):
    line = document.modelspace().add_line((0, 0), (1, 0))
    line.dxf.start = (2, 3, 4)
    line.dxf.end = (5, 6, 7)
    loaded_line = roundtrip_from_stream(document).modelspace().query("LINE")[0]

    assert tuple(loaded_line.dxf.start) == (2.0, 3.0, 4.0)
    assert tuple(loaded_line.dxf.end) == (5.0, 6.0, 7.0)


@pytest.mark.depends_on(
    "test_line_factory_stores_start_end_and_layer",
    "test_circle_factory_stores_center_radius_and_color",
    "test_arc_factory_stores_angles",
    "test_point_factory_stores_three_dimensional_location",
    "test_mtext_factory_stores_content_and_height",
)
def test_common_entity_factory_set_preserves_types_and_attributes(
    populated_document,
    tmp_path,
):
    loaded = roundtrip_from_file(populated_document, tmp_path)
    types = [entity.dxftype() for entity in loaded.modelspace()]

    assert types.count("LINE") == 1
    assert types.count("CIRCLE") == 1
    assert types.count("ARC") == 1
    assert types.count("POINT") == 1
    assert types.count("TEXT") == 1
    assert types.count("MTEXT") == 1
    assert types.count("LWPOLYLINE") == 1


@pytest.mark.depends_on(
    "test_lwpolyline_factory_stores_vertices_and_closed_flag",
    "test_polyline3d_factory_stores_vertices",
    "test_spline_factory_stores_fit_points",
)
def test_polyline_and_spline_geometry_survives_round_trip(document, tmp_path):
    msp = document.modelspace()
    lwpolyline = msp.add_lwpolyline([(0, 0), (1, 1), (2, 0)], close=True)
    polyline = msp.add_polyline3d([(0, 0, 0), (0, 1, 2), (0, 2, 4)])
    spline = msp.add_spline([(0, 0), (1, 2), (2, 0)])

    loaded = roundtrip_from_file(document, tmp_path).modelspace()

    loaded_lw = loaded.query("LWPOLYLINE")[0]
    loaded_poly = loaded.query("POLYLINE")[0]
    loaded_spline = loaded.query("SPLINE")[0]
    assert loaded_lw.closed
    assert len(loaded_lw) == 3
    assert len(list(loaded_poly.vertices)) == 3
    assert len(loaded_spline.fit_points) == 3


@pytest.mark.depends_on(
    "test_text_factory_and_public_placement_enum",
    "test_mtext_factory_stores_content_and_height",
)
def test_text_and_mtext_public_content_and_placement_survive_round_trip(
    document,
    tmp_path,
):
    from ezdxf.enums import TextEntityAlignment

    text = document.modelspace().add_text("Title", height=2)
    text.set_placement((3, 4), align=TextEntityAlignment.TOP_CENTER)
    mtext = document.modelspace().add_mtext("Body\\PMore")
    mtext.dxf.char_height = 1.25

    loaded = roundtrip_from_file(document, tmp_path).modelspace()
    loaded_text = loaded.query("TEXT")[0]
    loaded_mtext = loaded.query("MTEXT")[0]
    alignment, insert, _ = loaded_text.get_placement()

    assert loaded_text.dxf.text == "Title"
    assert alignment is TextEntityAlignment.TOP_CENTER
    assert tuple(insert) == (3.0, 4.0, 0.0)
    assert loaded_mtext.text == "Body\\PMore"
    assert loaded_mtext.dxf.char_height == 1.25


@pytest.mark.depends_on(
    "test_ocs_converts_points_to_and_from_wcs",
    "test_circle_factory_stores_center_radius_and_color",
)
def test_ocs_circle_projection_agrees_before_and_after_round_trip(document, tmp_path):
    circle = document.modelspace().add_circle((1, 2, 3), 2)
    circle.dxf.extrusion = (0, 1, 0)
    before = circle.ocs().to_wcs(circle.dxf.center)

    loaded_circle = roundtrip_from_file(document, tmp_path).modelspace().query("CIRCLE")[0]
    after = loaded_circle.ocs().to_wcs(loaded_circle.dxf.center)

    assert before.isclose(after)
    assert loaded_circle.ocs().from_wcs(after).isclose(loaded_circle.dxf.center)


@pytest.mark.depends_on(
    "test_ucs_converts_points_to_and_from_wcs",
    "test_point_factory_stores_three_dimensional_location",
)
def test_ucs_converted_point_can_be_stored_and_reloaded(document, tmp_path):
    from ezdxf.math import UCS

    ucs = UCS(origin=(10, 20, 30))
    wcs_point = ucs.to_wcs((1, 2, 3))
    document.modelspace().add_point(wcs_point)

    loaded_point = roundtrip_from_file(document, tmp_path).modelspace().query("POINT")[0]

    assert tuple(loaded_point.dxf.location) == (11.0, 22.0, 33.0)
    assert ucs.from_wcs(loaded_point.dxf.location).isclose((1, 2, 3))


@pytest.mark.depends_on(
    "test_matrix44_translation_transforms_a_point",
    "test_line_factory_stores_start_end_and_layer",
)
def test_matrix_transform_mutates_line_geometry_and_round_trips(document, tmp_path):
    from ezdxf.math import Matrix44

    line = document.modelspace().add_line((0, 0, 0), (1, 0, 0))
    line.transform(Matrix44.translate(5, 6, 7))
    loaded_line = roundtrip_from_file(document, tmp_path).modelspace().query("LINE")[0]

    assert tuple(loaded_line.dxf.start) == (5.0, 6.0, 7.0)
    assert tuple(loaded_line.dxf.end) == (6.0, 6.0, 7.0)


@pytest.mark.depends_on(
    "test_destroyed_entity_is_removed_by_layout_purge",
    "test_paperspace_viewport_and_layout_entities_have_distinct_storage",
)
def test_destroy_and_purge_changes_query_and_round_trip_state(document, tmp_path):
    msp = document.modelspace()
    kept = msp.add_line((0, 0), (1, 0))
    removed = msp.add_point((2, 2))
    removed.destroy()
    msp.purge()

    loaded = roundtrip_from_file(document, tmp_path)

    assert kept.is_alive
    assert len(loaded.modelspace()) == 1
    assert len(loaded.modelspace().query("POINT")) == 0


@pytest.mark.depends_on(
    "test_block_reference_factory_stores_insert_transform",
    "test_block_reference_attribute_can_be_added_and_placed",
)
def test_multiple_block_references_keep_independent_transforms_and_attributes(
    block_document,
    tmp_path,
):
    msp = block_document.modelspace()
    first = msp.add_blockref("SYMBOL", (0, 0), dxfattribs={"rotation": 10})
    second = msp.add_blockref("SYMBOL", (10, 0), dxfattribs={"rotation": 20})
    first.add_auto_attribs({"LABEL": "First"})
    second.add_auto_attribs({"LABEL": "Second"})

    loaded = roundtrip_from_file(block_document, tmp_path)
    inserts = list(loaded.modelspace().query("INSERT"))

    assert len(inserts) == 2
    assert [insert.dxf.rotation for insert in inserts] == [10.0, 20.0]
    assert [insert.attribs[0].dxf.text for insert in inserts] == ["First", "Second"]


@pytest.mark.depends_on(
    "test_paperspace_viewport_and_layout_entities_have_distinct_storage",
    "test_block_table_creates_named_block_and_entity_space",
)
def test_owner_queries_include_modelspace_paperspace_and_block_entities(
    document,
):
    msp = document.modelspace()
    psp = document.paperspace()
    block = document.blocks.new("QUERY_BLOCK")
    msp.add_line((0, 0), (1, 0))
    psp.add_line((0, 0), (0, 1))
    block.add_line((0, 0), (0, 2))

    assert len(document.query("LINE")) == 3
    assert len(msp.query("LINE")) == 1
    assert len(psp.query("LINE")) == 1
    assert len(block.query("LINE")) == 1


@pytest.mark.depends_on(
    "test_layout_groupby_groups_entities_by_layer",
    "test_modelspace_query_selects_by_entity_type",
)
def test_document_groupby_combines_entities_from_all_public_layouts(document):
    msp = document.modelspace()
    psp = document.paperspace()
    block = document.blocks.new("GROUP_BLOCK")
    msp.add_line((0, 0), (1, 0), dxfattribs={"layer": "DESIGN"})
    psp.add_line((0, 0), (0, 1), dxfattribs={"layer": "ANNOTATION"})
    block.add_circle((0, 0), 1, dxfattribs={"layer": "DESIGN"})

    groups = document.groupby("layer")

    assert len(groups["DESIGN"]) == 2
    assert len(groups["ANNOTATION"]) == 1


@pytest.mark.depends_on(
    "test_document_ascii_projection_contains_selected_public_entity_facts",
    "test_default_paperspace_is_available",
)
def test_read_stream_can_be_reused_for_equivalent_public_projections(document):
    document.modelspace().add_line((0, 0), (1, 1))
    text = io.StringIO()
    document.write(text)
    payload = text.getvalue()

    import ezdxf

    first = ezdxf.read(io.StringIO(payload))
    second = ezdxf.read(io.StringIO(payload))

    assert first.dxfversion == second.dxfversion
    assert len(first.modelspace()) == len(second.modelspace()) == 1
    assert tuple(first.modelspace()[0].dxf.end) == tuple(
        second.modelspace()[0].dxf.end
    )


@pytest.mark.depends_on(
    "test_document_write_produces_readable_ascii_stream",
    "test_text_factory_and_public_placement_enum",
)
def test_unicode_text_survives_readfile_without_snapshot_comparison(document, tmp_path):
    document.modelspace().add_text("Café 東京")

    loaded = roundtrip_from_file(document, tmp_path)

    assert loaded.modelspace().query("TEXT")[0].dxf.text == "Café 東京"


@pytest.mark.depends_on(
    "test_new_document_setup_populates_requested_standard_tables",
    "test_linetype_table_exposes_continuous_linetype",
)
def test_setup_tables_and_entity_linetype_assignment_survive_round_trip(tmp_path):
    import ezdxf

    document = ezdxf.new("R2010", setup=["linetypes", "styles"])
    line = document.modelspace().add_line(
        (0, 0),
        (1, 0),
        dxfattribs={"linetype": "DASHED"},
    )
    loaded = roundtrip_from_file(document, tmp_path)

    assert len(loaded.linetypes) >= len(document.linetypes)
    assert loaded.modelspace().query("LINE")[0].dxf.linetype == "DASHED"


@pytest.mark.depends_on(
    "test_header_user_integer_and_float_values_are_mutable",
    "test_document_write_produces_readable_ascii_stream",
)
def test_header_user_values_survive_file_round_trip(document, tmp_path):
    document.header["$USERI1"] = 99
    document.header["$USERR1"] = 4.25

    loaded = roundtrip_from_file(document, tmp_path)

    assert loaded.header["$USERI1"] == 99
    assert loaded.header["$USERR1"] == 4.25


@pytest.mark.depends_on(
    "test_layer_dxf_attributes_can_be_mutated",
    "test_entity_dxf_namespace_supports_assignment_and_set",
)
def test_layer_mutation_and_entity_reassignment_survive_round_trip(document, tmp_path):
    layer = document.layers.get("DESIGN")
    layer.dxf.color = 5
    line = document.modelspace().add_line((0, 0), (1, 0))
    line.dxf.layer = "DESIGN"
    line.dxf.color = 6

    loaded = roundtrip_from_file(document, tmp_path)

    assert loaded.layers.get("DESIGN").dxf.color == 5
    assert loaded.modelspace().query("LINE")[0].dxf.layer == "DESIGN"
    assert loaded.modelspace().query("LINE")[0].dxf.color == 6


@pytest.mark.depends_on(
    "test_block_reference_factory_stores_insert_transform",
    "test_query_attribute_filter_selects_layer",
)
def test_insert_query_and_block_definition_remain_connected_after_round_trip(
    block_document,
    tmp_path,
):
    block_document.modelspace().add_blockref(
        "SYMBOL",
        (3, 4),
        dxfattribs={"layer": "DESIGN"},
    )

    loaded = roundtrip_from_file(block_document, tmp_path)
    insert = loaded.modelspace().query('*[layer=="DESIGN"]')[0]
    block = loaded.blocks.get(insert.dxf.name)

    assert insert.dxf.name == "SYMBOL"
    assert block is not None
    assert len(block.query("LINE CIRCLE ATTDEF")) == 3


@pytest.mark.depends_on(
    "test_entity_query_slice_and_attribute_selection_are_sequence_views",
    "test_layout_groupby_accepts_a_public_key_function",
)
def test_query_selection_can_be_grouped_and_serialized_as_one_workflow(
    populated_document,
    tmp_path,
):
    selected = populated_document.modelspace().query("LINE CIRCLE")
    selected["color"] = 5
    selected.layer = "FOCUS"
    groups = selected.groupby("layer")

    loaded = roundtrip_from_file(populated_document, tmp_path)
    focused = loaded.modelspace().query('*[layer=="FOCUS"]')

    assert len(groups["FOCUS"]) == 2
    assert len(focused) == 2
    assert all(entity.dxf.color == 5 for entity in focused)


@pytest.mark.depends_on(
    "test_new_document_uses_requested_version_and_units",
    "test_line_factory_stores_start_end_and_layer",
)
def test_r2000_line_round_trip_preserves_version_and_basic_geometry(tmp_path):
    import ezdxf

    document = ezdxf.new("R2000", units=1)
    document.modelspace().add_line((1, 2), (3, 4))

    loaded = roundtrip_from_file(document, tmp_path)

    assert loaded.dxfversion == "AC1015"
    assert loaded.units == 1
    assert tuple(loaded.modelspace()[0].dxf.start) == (1.0, 2.0, 0.0)
    assert tuple(loaded.modelspace()[0].dxf.end) == (3.0, 4.0, 0.0)


@pytest.mark.depends_on(
    "test_document_ascii_projection_contains_selected_public_entity_facts",
    "test_extension_dictionary_xrecord_exposes_public_tag_storage",
    "test_block_reference_factory_stores_insert_transform",
    "test_viewport_factory_is_available_in_paperspace",
)
def test_full_public_workflow_connects_entities_blocks_layouts_and_custom_data(
    document,
    tmp_path,
):
    from ezdxf.enums import TextEntityAlignment

    block = document.blocks.new("WORKFLOW")
    block.add_circle((0, 0), 1, dxfattribs={"layer": "DESIGN"})
    block.add_attdef("CODE", insert=(0, 2), text="Default")
    line = document.modelspace().add_line(
        (0, 0),
        (3, 0),
        dxfattribs={"layer": "DESIGN", "color": 2},
    )
    line.set_app_data("APPTEST", [(1, "workflow")])
    line.set_xdata("APPTEST", [(1000, "payload")])
    text = document.modelspace().add_text("Workflow")
    text.set_placement((2, 3), align=TextEntityAlignment.LEFT)
    insert = document.modelspace().add_blockref("WORKFLOW", (10, 20))
    insert.add_auto_attribs({"CODE": "A-17"})
    sheet = document.layouts.new("WorkflowSheet")
    sheet.add_viewport((5, 5), (10, 8), (0, 0), 20)

    loaded = roundtrip_from_file(document, tmp_path)
    loaded_line = loaded.modelspace().query("LINE")[0]
    loaded_insert = loaded.modelspace().query("INSERT")[0]

    assert loaded_line.has_app_data("APPTEST")
    assert loaded_line.has_xdata("APPTEST")
    assert loaded_insert.attribs[0].dxf.text == "A-17"
    assert len(loaded.blocks.get("WORKFLOW").query("CIRCLE ATTDEF")) == 2
    assert len(loaded.paperspace("WorkflowSheet").query("VIEWPORT")) == 1
    assert loaded.modelspace().query("TEXT")[0].dxf.text == "Workflow"
