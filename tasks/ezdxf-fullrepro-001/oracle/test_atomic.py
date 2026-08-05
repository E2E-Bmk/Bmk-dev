from __future__ import annotations

import io

import pytest

from conftest import ascii_text


def test_new_document_uses_requested_version_and_units():
    import ezdxf

    doc = ezdxf.new("R2010", units=6)

    assert doc.dxfversion == "AC1024"
    assert doc.units == 6


def test_new_document_sets_metric_measurement_header():
    import ezdxf

    doc = ezdxf.new("R2010", units=6)

    assert doc.header["$MEASUREMENT"] == 1


def test_new_document_exposes_modelspace():
    import ezdxf

    doc = ezdxf.new()
    msp = doc.modelspace()

    assert msp.name == "Model"
    assert msp.is_modelspace
    assert msp.is_any_layout


def test_new_document_setup_populates_requested_standard_tables():
    import ezdxf

    doc = ezdxf.new(setup=["linetypes", "styles"])

    assert len(doc.linetypes) > 3
    assert len(doc.styles) > 1


def test_header_user_integer_and_float_values_are_mutable():
    import ezdxf

    doc = ezdxf.new()
    doc.header["$USERI1"] = 17
    doc.header["$USERR1"] = 2.5

    assert doc.header["$USERI1"] == 17
    assert doc.header["$USERR1"] == 2.5


def test_layer_table_adds_colored_layer_and_supports_case_insensitive_lookup(document):
    layer = document.layers.get("design")

    assert layer is not None
    assert layer.dxf.name == "DESIGN"
    assert layer.dxf.color == 2


def test_layer_dxf_attributes_can_be_mutated(document):
    layer = document.layers.get("DESIGN")

    layer.dxf.color = 6
    layer.dxf.lineweight = 25

    assert layer.dxf.color == 6
    assert layer.dxf.lineweight == 25


def test_linetype_table_exposes_continuous_linetype(document):
    linetype = document.linetypes.get("continuous")

    assert linetype is not None
    assert linetype.dxf.name == "Continuous"


def test_appid_table_registers_custom_application(document):
    appid = document.appids.get("APPTEST")

    assert appid is not None
    assert appid.dxf.name == "APPTEST"


def test_default_paperspace_is_available(document):
    psp = document.paperspace()

    assert psp.name == "Layout1"
    assert psp.is_any_paperspace
    assert not psp.is_modelspace


def test_layout_manager_creates_named_paperspace(document):
    layout = document.layouts.new("SheetA")

    assert layout.name == "SheetA"
    assert document.paperspace("sheeta") is layout


def test_block_table_creates_named_block_and_entity_space(document):
    block = document.blocks.new("SYMBOL", base_point=(1, 2, 0))
    line = block.add_line((0, 0), (2, 0))

    assert block.name == "SYMBOL"
    assert block.base_point == (1.0, 2.0, 0.0)
    assert len(block) == 1
    assert line in block


def test_line_factory_stores_start_end_and_layer(modelspace):
    line = modelspace.add_line(
        (1, 2, 3),
        (4, 5, 6),
        dxfattribs={"layer": "DESIGN", "color": 2},
    )

    assert line.dxftype() == "LINE"
    assert tuple(line.dxf.start) == (1.0, 2.0, 3.0)
    assert tuple(line.dxf.end) == (4.0, 5.0, 6.0)
    assert line.dxf.layer == "DESIGN"


def test_circle_factory_stores_center_radius_and_color(modelspace):
    circle = modelspace.add_circle(
        (2, 3, 4),
        5,
        dxfattribs={"layer": "DESIGN", "color": 3},
    )

    assert circle.dxftype() == "CIRCLE"
    assert tuple(circle.dxf.center) == (2.0, 3.0, 4.0)
    assert circle.dxf.radius == 5.0
    assert circle.dxf.color == 3


def test_arc_factory_stores_angles(modelspace):
    arc = modelspace.add_arc((0, 0), 3, 10, 70)

    assert arc.dxftype() == "ARC"
    assert arc.dxf.radius == 3.0
    assert arc.dxf.start_angle == 10.0
    assert arc.dxf.end_angle == 70.0


def test_point_factory_stores_three_dimensional_location(modelspace):
    point = modelspace.add_point((3, 4, 5))

    assert point.dxftype() == "POINT"
    assert tuple(point.dxf.location) == (3.0, 4.0, 5.0)


def test_text_factory_and_public_placement_enum(modelspace):
    from ezdxf.enums import TextEntityAlignment

    text = modelspace.add_text("Hello", height=2)
    text.set_placement((5, 6), align=TextEntityAlignment.MIDDLE_CENTER)

    placement = text.get_placement()
    assert text.dxftype() == "TEXT"
    assert text.dxf.text == "Hello"
    assert text.dxf.height == 2.0
    assert placement[0] is TextEntityAlignment.MIDDLE_CENTER
    assert tuple(placement[1]) == (5.0, 6.0, 0.0)


def test_mtext_factory_stores_content_and_height(modelspace):
    mtext = modelspace.add_mtext("Line one\\PLine two")
    mtext.dxf.char_height = 1.5

    assert mtext.dxftype() == "MTEXT"
    assert mtext.text == "Line one\\PLine two"
    assert mtext.dxf.char_height == 1.5


def test_lwpolyline_factory_stores_vertices_and_closed_flag(modelspace):
    polyline = modelspace.add_lwpolyline(
        [(0, 0), (2, 0, 0.25, 0.0, 0.0), (2, 2)],
        close=True,
    )

    assert polyline.dxftype() == "LWPOLYLINE"
    assert polyline.closed
    assert len(polyline) == 3
    assert tuple(polyline[1][:2]) == (2.0, 0.0)


def test_polyline3d_factory_stores_vertices(modelspace):
    polyline = modelspace.add_polyline3d(
        [(0, 0, 0), (1, 2, 3), (4, 5, 6)],
        close=True,
    )

    assert polyline.dxftype() == "POLYLINE"
    assert polyline.is_3d_polyline
    assert polyline.is_closed
    assert len(list(polyline.vertices)) == 3


def test_ellipse_factory_stores_center_axis_and_ratio(modelspace):
    ellipse = modelspace.add_ellipse((1, 2, 3), (4, 0, 0), 0.5)

    assert ellipse.dxftype() == "ELLIPSE"
    assert tuple(ellipse.dxf.center) == (1.0, 2.0, 3.0)
    assert tuple(ellipse.dxf.major_axis) == (4.0, 0.0, 0.0)
    assert ellipse.dxf.ratio == 0.5


def test_spline_factory_stores_fit_points(modelspace):
    spline = modelspace.add_spline([(0, 0), (1, 2), (3, 1)])

    assert spline.dxftype() == "SPLINE"
    assert len(spline.fit_points) == 3
    assert tuple(spline.fit_points[1]) == (1.0, 2.0, 0.0)


def test_ray_and_xline_factories_store_direction_vectors(modelspace):
    ray = modelspace.add_ray((1, 2, 3), (0, 1, 0))
    xline = modelspace.add_xline((4, 5, 6), (1, 0, 0))

    assert tuple(ray.dxf.start) == (1.0, 2.0, 3.0)
    assert tuple(ray.dxf.unit_vector) == (0.0, 1.0, 0.0)
    assert tuple(xline.dxf.start) == (4.0, 5.0, 6.0)
    assert tuple(xline.dxf.unit_vector) == (1.0, 0.0, 0.0)


def test_solid_trace_and_face_factories_create_expected_types(modelspace):
    solid = modelspace.add_solid([(0, 0), (1, 0), (1, 1), (0, 1)])
    trace = modelspace.add_trace([(0, 0), (1, 0), (1, 1), (0, 1)])
    face = modelspace.add_3dface(
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    )

    assert [entity.dxftype() for entity in (solid, trace, face)] == [
        "SOLID",
        "TRACE",
        "3DFACE",
    ]


def test_entity_dxf_namespace_supports_assignment_and_set(modelspace):
    line = modelspace.add_line((0, 0), (1, 0))

    line.dxf.layer = "DESIGN"
    line.dxf.set("color", 5)

    assert line.dxf.layer == "DESIGN"
    assert line.dxf.color == 5
    assert not line.dxf.is_supported("text")


def test_modelspace_query_selects_by_entity_type(populated_document):
    msp = populated_document.modelspace()

    assert len(msp.query("LINE")) == 1
    assert len(msp.query("CIRCLE ARC")) == 2


def test_query_attribute_filter_selects_layer(populated_document):
    result = populated_document.modelspace().query('*[layer=="DESIGN"]')

    assert len(result) == 5
    assert all(entity.dxf.layer == "DESIGN" for entity in result)


def test_query_attribute_filter_can_ignore_case(populated_document):
    result = populated_document.modelspace().query('*[layer=="design"]i')

    assert len(result) == 5


def test_entity_query_assignment_updates_supported_entities(populated_document):
    result = populated_document.modelspace().query("LINE CIRCLE")

    result.layer = "UPDATED"

    assert [entity.dxf.layer for entity in result] == ["UPDATED", "UPDATED"]


def test_entity_query_slice_and_attribute_selection_are_sequence_views(populated_document):
    result = populated_document.modelspace().query("*")
    first_two = result[:2]

    assert len(first_two) == 2
    assert first_two[0] is result[0]
    assert len(result["layer"] == "DESIGN") == 5


def test_layout_groupby_groups_entities_by_layer(populated_document):
    groups = populated_document.modelspace().groupby("layer")

    assert {name: len(entities) for name, entities in groups.items()} == {
        "DESIGN": 5,
        "ANNOTATION": 2,
    }


def test_layout_groupby_accepts_a_public_key_function(populated_document):
    groups = populated_document.modelspace().groupby(
        key=lambda entity: entity.dxf.layer,
    )

    assert sorted(groups) == ["ANNOTATION", "DESIGN"]
    assert sum(len(entities) for entities in groups.values()) == 7


def test_rgb_integer_helpers_round_trip():
    from ezdxf import colors

    rgb = colors.RGB(12, 34, 56)

    assert colors.int2rgb(colors.rgb2int(rgb)) == rgb


def test_rgb_and_rgba_public_classes_round_trip_hex_and_floats():
    from ezdxf import colors

    rgb = colors.RGB.from_hex("#0a141e")
    rgba = colors.RGBA.from_hex("#0a141e80")

    assert rgb.to_hex() == "#0a141e"
    assert colors.RGB.from_floats(rgb.to_floats()) == rgb
    assert rgba.to_hex() == "#0a141e80"
    assert colors.RGBA.from_floats(rgba.to_floats()) == rgba


def test_transparency_helpers_preserve_endpoints():
    from ezdxf import colors

    opaque = colors.float2transparency(0.0)
    transparent = colors.float2transparency(1.0)

    assert colors.transparency2float(opaque) == 0.0
    assert colors.transparency2float(transparent) == 1.0


def test_vec3_arithmetic_and_distance_are_public():
    from ezdxf.math import Vec3, distance

    left = Vec3(1, 2, 3)
    right = Vec3(4, 6, 3)

    assert left + right == Vec3(5, 8, 6)
    assert distance(left, right) == 5.0


def test_ucs_converts_points_to_and_from_wcs():
    from ezdxf.math import UCS, Vec3

    ucs = UCS(origin=(10, 20, 30))
    local = Vec3(1, 2, 3)

    assert ucs.to_wcs(local) == Vec3(11, 22, 33)
    assert ucs.from_wcs(ucs.to_wcs(local)).isclose(local)


def test_ocs_converts_points_to_and_from_wcs():
    from ezdxf.math import OCS, Vec3

    ocs = OCS((0, 1, 0))
    local = Vec3(1, 2, 3)

    assert ocs.from_wcs(ocs.to_wcs(local)).isclose(local)


def test_matrix44_translation_transforms_a_point():
    from ezdxf.math import Matrix44

    matrix = Matrix44.translate(1, 2, 3)

    assert matrix.transform((4, 5, 6)) == (5.0, 7.0, 9.0)


def test_appdata_high_level_methods_store_and_discard_tags(modelspace):
    line = modelspace.add_line((0, 0), (1, 0))

    line.set_app_data("APPTEST", [(1, "value")])

    assert line.has_app_data("APPTEST")
    assert [(tag.code, tag.value) for tag in line.get_app_data("APPTEST")] == [
        (1, "value")
    ]
    line.discard_app_data("APPTEST")
    assert not line.has_app_data("APPTEST")


def test_xdata_high_level_methods_store_and_replace_tags(modelspace):
    line = modelspace.add_line((0, 0), (1, 0))

    line.set_xdata("APPTEST", [(1000, "first"), (1040, 2.5)])
    assert line.has_xdata("APPTEST")
    assert [tag.value for tag in line.get_xdata("APPTEST")] == ["first", 2.5]
    line.set_xdata("APPTEST", [(1000, "second")])

    assert [tag.value for tag in line.get_xdata("APPTEST")] == ["second"]


def test_user_xdata_list_commits_supported_values(modelspace):
    from ezdxf.entities.xdata import XDataUserList
    from ezdxf.math import Vec3

    line = modelspace.add_line((0, 0), (1, 0))
    with XDataUserList.entity(line, name="VALUES", appid="APPTEST") as values:
        values.append("one")
        values.append(2)
        values.append(Vec3(1, 2, 3))

    with XDataUserList.entity(line, name="VALUES", appid="APPTEST") as values:
        assert list(values) == ["one", 2, Vec3(1, 2, 3)]


def test_user_xdata_dict_commits_mapping_values(modelspace):
    from ezdxf.entities.xdata import XDataUserDict

    line = modelspace.add_line((0, 0), (1, 0))
    with XDataUserDict.entity(line, name="META", appid="APPTEST") as metadata:
        metadata["label"] = "sample"
        metadata["count"] = 3

    with XDataUserDict.entity(line, name="META", appid="APPTEST") as metadata:
        assert dict(metadata) == {"label": "sample", "count": 3}


def test_extension_dictionary_xrecord_exposes_public_tag_storage(modelspace):
    point = modelspace.add_point((1, 2))
    extension_dict = point.new_extension_dict()
    record = extension_dict.add_xrecord("DATA")
    record.extend([(1, "text"), (40, 3.5)])

    assert point.has_extension_dict
    assert [(tag.code, tag.value) for tag in record.tags] == [
        (1, "text"),
        (40, 3.5),
    ]


def test_destroyed_entity_is_removed_by_layout_purge(modelspace):
    point = modelspace.add_point((9, 9))

    point.destroy()
    assert not point.is_alive
    assert len(modelspace) == 1
    modelspace.purge()

    assert len(modelspace) == 0


def test_viewport_factory_is_available_in_paperspace(paperspace):
    viewport = paperspace.add_viewport(
        center=(5, 5),
        size=(10, 8),
        view_center_point=(0, 0),
        view_height=20,
    )

    assert viewport.dxftype() == "VIEWPORT"
    assert tuple(viewport.dxf.center) == (5.0, 5.0, 0.0)
    assert viewport.dxf.height == 8.0


def test_block_reference_factory_stores_insert_transform(block_document):
    insert = block_document.modelspace().add_blockref(
        "SYMBOL",
        (10, 20, 0),
        dxfattribs={"xscale": 2, "yscale": 3, "rotation": 30},
    )

    assert insert.dxftype() == "INSERT"
    assert insert.dxf.name == "SYMBOL"
    assert tuple(insert.dxf.insert) == (10.0, 20.0, 0.0)
    assert insert.dxf.xscale == 2.0
    assert insert.dxf.yscale == 3.0
    assert insert.dxf.rotation == 30.0


def test_block_reference_attribute_can_be_added_and_placed(block_document):
    from ezdxf.enums import TextEntityAlignment

    insert = block_document.modelspace().add_blockref("SYMBOL", (10, 20))
    attrib = insert.add_attrib("LABEL", "Value")
    attrib.set_placement((11, 22), align=TextEntityAlignment.LEFT)

    assert len(insert.attribs) == 1
    assert insert.attribs[0].dxf.tag == "LABEL"
    assert insert.attribs[0].dxf.text == "Value"
    assert tuple(insert.attribs[0].dxf.insert) == (11.0, 22.0, 0.0)


def test_paperspace_viewport_and_layout_entities_have_distinct_storage(document):
    msp = document.modelspace()
    psp = document.paperspace()
    msp.add_line((0, 0), (1, 0))
    psp.add_line((0, 0), (0, 1))

    assert len(msp) == 1
    assert len(psp) == 1
    assert msp[0].dxf.paperspace == 0
    assert psp[0].dxf.paperspace == 1


def test_document_write_produces_readable_ascii_stream(document):
    document.modelspace().add_line((0, 0), (1, 1))
    stream = io.StringIO()

    document.write(stream)

    assert stream.getvalue().startswith("  0\nSECTION")
    assert "ENTITIES" in stream.getvalue()


def test_document_ascii_projection_contains_selected_public_entity_facts(populated_document):
    text = ascii_text(populated_document)

    assert "DESIGN" in text
    assert "ANNOTATION" in text
    assert "First" in text
    assert "LWPOLYLINE" in text
