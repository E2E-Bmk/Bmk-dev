# Spec2Repo oracle - integration and system_e2e tests for pint-fullrepro-001

from __future__ import annotations

import datetime
import math
import operator
import pickle
import subprocess
import sys

import pytest

import pint
from pint import (
    Context,
    DefinitionSyntaxError,
    DimensionalityError,
    OffsetUnitCalculusError,
    RedefinitionError,
    UndefinedUnitError,
    Unit,
    UnitRegistry,
    get_application_registry,
    pi_theorem,
    register_unit_format,
    set_application_registry,
)


def assert_quantity_close(quantity, magnitude, units):
    assert quantity.magnitude == pytest.approx(magnitude)
    assert quantity.units == units


@pytest.mark.depends_on('test_upstream_get_application_registry_default_unit', 'test_get_application_registry_returns_current_registry_wrapper')
def test_upstream_get_application_registry_default_unit():
    """Verifies: PINT-APP-002."""
    ureg = get_application_registry()
    assert ureg.Quantity(1, "kg").to("gram").magnitude == pytest.approx(1000)

@pytest.mark.depends_on('test_upstream_get_application_registry_default_unit', 'test_get_application_registry_returns_current_registry_wrapper')
def test_upstream_pickled_custom_quantity_requires_application_registry_definition():
    """Verifies: PINT-APP-005."""
    ureg = UnitRegistry(None)
    ureg.define("stage3_pickle_unit = []")
    quantity = ureg.Quantity(123, "stage3_pickle_unit")
    data = pickle.dumps(quantity)
    with pytest.raises(UndefinedUnitError):
        pickle.loads(data)

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_upstream_register_unit_format_custom_and_rejects_duplicate():
    """Verifies: PINT-FMT-011, PINT-FMT-012."""

    @register_unit_format("stage3up")
    def format_custom(unit, registry, **options):
        registry.Unit(unit)
        return "<stage3 unit>"

    ureg = UnitRegistry()
    quantity = 1.0 * ureg.meter
    assert f"{quantity:g#~stage3up}" == "1 <stage3 unit>"
    assert f"{quantity:stage3up}" == "1.0 <stage3 unit>"

    with pytest.raises(ValueError):

        @register_unit_format("stage3up")
        def format_custom_redefined(unit, registry, **options):
            return "<overwritten>"

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_upstream_format_unit_caret_negative_power():
    """Verifies: PINT-FMT-002, PINT-FMT-005."""
    unit = UnitRegistry().Unit("second") ** -1
    assert format(unit, "~^P") == "s⁻¹"
    assert format(unit, "~P") == "1/s"

@pytest.mark.depends_on('test_upstream_get_application_registry_default_unit', 'test_get_application_registry_returns_current_registry_wrapper')
def test_upstream_application_registry_controls_top_level_quantity():
    """Verifies: PINT-APP-001, PINT-APP-003, PINT-INV-007."""
    original = get_application_registry()
    first = UnitRegistry(None)
    first.define("stage3_app_unit = [stage3_app_dim]")
    first.define("stage3_app_half = stage3_app_unit / 2")
    second = UnitRegistry(None)
    second.define("stage3_app_unit = [stage3_app_dim]")
    second.define("stage3_app_half = stage3_app_unit / 3")
    try:
        set_application_registry(first)
        q1 = Unit("stage3_app_half")
        set_application_registry(second)
        q2 = Unit("stage3_app_half")
        assert (1 * q1).to("stage3_app_unit").magnitude == pytest.approx(0.5)
        assert (1 * q2).to("stage3_app_unit").magnitude == pytest.approx(1 / 3)
    finally:
        set_application_registry(original)

@pytest.mark.depends_on('test_default_registry_loads_bundled_units', 'test_quantity_public_magnitude_and_unit_attributes', 'test_to_returns_new_quantity_without_mutating_source')
def test_quantity_tuple_round_trip_preserves_conversion_behavior():
    """Verifies: PINT-QTY-020, PINT-INV-008."""
    ureg = UnitRegistry()
    original = 3 * ureg.meter
    restored = ureg.Quantity.from_tuple(original.to_tuple())
    assert_quantity_close(restored.to("centimeter"), 300, ureg.centimeter)

@pytest.mark.depends_on('test_iterable_definitions_add_custom_unit_and_plural_alias', 'test_attribute_item_and_parse_units_return_same_bound_unit')
def test_custom_definition_visible_across_lookup_parse_quantity_and_conversion():
    """Verifies: PINT-INV-001, PINT-REG-004."""
    ureg = UnitRegistry()
    ureg.define("stage3_stride = 0.75 * meter = st3stride")
    assert "stage3_stride" in ureg
    assert ureg["stage3_stride"].units == ureg.stage3_stride
    assert ureg.parse_units("st3stride") == ureg.stage3_stride
    assert_quantity_close((4 * ureg.stage3_stride).to("meter"), 3, ureg.meter)
    assert format(ureg.stage3_stride, "~") == "st3stride"

@pytest.mark.depends_on('test_iterable_definitions_add_custom_unit_and_plural_alias', 'test_attribute_item_and_parse_units_return_same_bound_unit')
def test_loaded_definition_file_mutates_existing_registry(tmp_path):
    """Verifies: PINT-REG-004, PINT-INV-001."""
    path = tmp_path / "defs.txt"
    path.write_text("stage3_step = 2 * meter = st3step\n", encoding="utf-8")
    ureg = UnitRegistry()
    parsed = ureg.load_definitions(path)
    assert parsed is not None
    assert_quantity_close((3 * ureg.stage3_step).to("meter"), 6, ureg.meter)

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_context_allows_one_off_cross_dimensional_conversion():
    """Verifies: PINT-CTX-005, PINT-INV-005."""
    ureg = UnitRegistry()
    wavelength = 530 * ureg.nanometer
    frequency = wavelength.to("hertz", "spectroscopy")
    round_trip = frequency.to("nanometer", "spectroscopy")
    assert round_trip.magnitude == pytest.approx(530)
    assert round_trip.units == ureg.nanometer

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_context_manager_restores_previous_dimensionality_rules():
    """Verifies: PINT-CTX-006, PINT-INV-005."""
    ureg = UnitRegistry()
    frequency = (530 * ureg.nanometer).to("hertz", "spectroscopy")
    with ureg.context("spectroscopy"):
        assert frequency.is_compatible_with("nanometer")
    assert not frequency.is_compatible_with("nanometer")

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_enable_and_disable_contexts_control_later_conversions():
    """Verifies: PINT-CTX-007, PINT-INV-005."""
    ureg = UnitRegistry()
    frequency = (530 * ureg.nanometer).to("hertz", "spectroscopy")
    ureg.enable_contexts("spectroscopy")
    try:
        assert frequency.to("nanometer").magnitude == pytest.approx(530)
    finally:
        ureg.disable_contexts()
    with pytest.raises(DimensionalityError):
        frequency.to("nanometer")

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_context_parameters_override_default_values():
    """Verifies: PINT-CTX-011."""
    ureg = UnitRegistry()
    frequency = (530 * ureg.nanometer).to("hertz", "spectroscopy")
    in_medium = frequency.to("nanometer", "spectroscopy", n=1.33)
    assert in_medium.magnitude == pytest.approx(398.4962406015037)
    assert in_medium.units == ureg.nanometer

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_custom_context_transformation_uses_public_context_api():
    """Verifies: PINT-CTX-001, PINT-CTX-002, PINT-CTX-004."""
    ureg = UnitRegistry()
    context = Context("stage3_double")
    context.add_transformation("[length]", "[time]", lambda registry, value: value.magnitude * 2 * registry.second)
    ureg.add_context(context)
    assert_quantity_close((3 * ureg.meter).to("second", "stage3_double"), 6, ureg.second)

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_later_enabled_context_takes_precedence_for_same_pair():
    """Verifies: PINT-CTX-008."""
    ureg = UnitRegistry()
    first = Context("stage3_first")
    first.add_transformation("[length]", "[time]", lambda registry, value: value.magnitude * registry.second)
    second = Context("stage3_second")
    second.add_transformation("[length]", "[time]", lambda registry, value: value.magnitude * 10 * registry.second)
    ureg.add_context(first)
    ureg.add_context(second)
    ureg.enable_contexts("stage3_first")
    ureg.enable_contexts("stage3_second")
    try:
        assert_quantity_close((2 * ureg.meter).to("second"), 20, ureg.second)
    finally:
        ureg.disable_contexts()

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_unknown_context_name_raises_key_error():
    """Verifies: PINT-CTX-009, PINT-ERR-011."""
    ureg = UnitRegistry()
    with pytest.raises(KeyError):
        (1 * ureg.meter).to("second", "stage3_missing_context")

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_context_transformation_exception_is_propagated():
    """Verifies: PINT-CTX-010."""
    ureg = UnitRegistry()
    context = Context("stage3_raises")

    def transform(registry, value):
        raise RuntimeError("stage3 transform failed")

    context.add_transformation("[length]", "[time]", transform)
    ureg.add_context(context)
    with pytest.raises(RuntimeError):
        (1 * ureg.meter).to("second", "stage3_raises")

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_is_compatible_with_accepts_compatible_strings')
def test_invalid_context_redefinition_is_rejected():
    """Verifies: PINT-CTX-015."""
    ureg = UnitRegistry()
    context = Context("stage3_bad_redefinition")
    context.redefine("meter = 2 * meter")
    ureg.add_context(context)
    with pytest.raises(ValueError):
        ureg.enable_contexts("stage3_bad_redefinition")

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_to_base_units_accepts_explicit_system')
def test_system_projection_exposes_member_units():
    """Verifies: PINT-SYS-001, PINT-INV-009."""
    ureg = UnitRegistry()
    assert ureg.sys.mks.meter == ureg.meter
    assert "meter" in dir(ureg.sys.mks)

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_to_base_units_accepts_explicit_system')
def test_default_system_changes_later_base_unit_conversion():
    """Verifies: PINT-SYS-002, PINT-SYS-003, PINT-INV-004."""
    ureg = UnitRegistry()
    before = (1 * ureg.newton).to_base_units()
    ureg.default_system = "cgs"
    after = (1 * ureg.newton).to_base_units()
    assert before.units == ureg.kilogram * ureg.meter / ureg.second**2
    assert after.units == ureg.gram * ureg.centimeter / ureg.second**2
    assert after.magnitude == pytest.approx(100000)

@pytest.mark.depends_on('test_to_base_units_uses_registry_default_system', 'test_to_base_units_accepts_explicit_system')
def test_unknown_default_system_raises_value_error():
    """Verifies: PINT-SYS-004, PINT-ERR-012."""
    ureg = UnitRegistry()
    with pytest.raises(ValueError):
        ureg.default_system = "stage3_missing_system"

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_format_short_modifier_uses_unit_symbols():
    """Verifies: PINT-FMT-002, PINT-FMT-004."""
    ureg = UnitRegistry()
    assert format(ureg.meter / ureg.second, "~P") == "m/s"

@pytest.mark.depends_on('test_default_registry_loads_bundled_units', 'test_quantity_public_magnitude_and_unit_attributes', 'test_to_returns_new_quantity_without_mutating_source')
def test_format_negative_exponent_modifier_moves_denominator():
    """Verifies: PINT-FMT-002, PINT-FMT-005."""
    ureg = UnitRegistry()
    assert format(ureg.meter / ureg.second, "~^") == "m * s ** -1"

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_format_compact_modifier_compacts_quantity_before_formatting():
    """Verifies: PINT-FMT-002, PINT-FMT-006."""
    ureg = UnitRegistry()
    assert format(1500 * ureg.meter, "#~") == "1.5 km"

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_invalid_format_specification_raises_value_error():
    """Verifies: PINT-FMT-007."""
    ureg = UnitRegistry()
    with pytest.raises(ValueError):
        format(1 * ureg.meter, "stage3_bad_format")

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_registry_default_format_affects_later_string_projection():
    """Verifies: PINT-FMT-001, PINT-FMT-008, PINT-INV-006."""
    ureg = UnitRegistry()
    ureg.formatter.default_format = "~P"
    assert str(1 * ureg.meter / ureg.second) == "1.0 m/s"

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_top_level_formatter_formats_numerator_and_denominator_terms():
    """Verifies: PINT-FMT-013."""
    assert pint.formatter([("meter", 1)], [("second", 2)], as_ratio=True) == "meter / second ** 2"

@pytest.mark.depends_on('test_format_negative_exponent_modifier_moves_denominator', 'test_format_short_modifier_uses_unit_symbols')
def test_register_unit_format_rejects_existing_name():
    """Verifies: PINT-FMT-012, PINT-ERR-009."""
    with pytest.raises(ValueError):
        register_unit_format("D")(lambda unit, registry, **options: "unused")

@pytest.mark.depends_on('test_upstream_get_application_registry_default_unit', 'test_get_application_registry_returns_current_registry_wrapper')
def test_application_registry_controls_top_level_quantity_constructor():
    """Verifies: PINT-APP-001, PINT-APP-003, PINT-INV-007."""
    previous = get_application_registry()
    ureg = UnitRegistry()
    try:
        set_application_registry(ureg)
        quantity = pint.Quantity(2, "meter")
        assert_quantity_close(quantity, 2, ureg.meter)
    finally:
        set_application_registry(previous)

@pytest.mark.depends_on('test_upstream_get_application_registry_default_unit', 'test_get_application_registry_returns_current_registry_wrapper')
def test_get_application_registry_returns_current_registry_wrapper():
    """Verifies: PINT-APP-002."""
    registry = get_application_registry()
    assert registry is not None
    assert hasattr(registry, "meter")

@pytest.mark.depends_on('test_upstream_get_application_registry_default_unit', 'test_get_application_registry_returns_current_registry_wrapper')
def test_set_application_registry_rejects_non_registry_object():
    """Verifies: PINT-APP-004, PINT-ERR-010."""
    with pytest.raises(TypeError):
        set_application_registry(object())

@pytest.mark.depends_on('test_upstream_get_application_registry_default_unit', 'test_get_application_registry_returns_current_registry_wrapper')
def test_pickled_quantity_uses_application_registry_on_load():
    """Verifies: PINT-APP-005, PINT-INV-007."""
    previous = get_application_registry()
    ureg = UnitRegistry()
    try:
        set_application_registry(ureg)
        restored = pickle.loads(pickle.dumps(3 * ureg.meter))
        assert_quantity_close(restored, 3, ureg.meter)
    finally:
        set_application_registry(previous)

@pytest.mark.depends_on('test_calling_registry_parses_quantity_expression', 'test_to_base_units_uses_registry_default_system')
def test_cli_converts_quantity_to_requested_units():
    """Verifies: PINT-CLI-001, PINT-CLI-010, PINT-CLI-011, PINT-INV-010."""
    result = subprocess.run(
        [sys.executable, "-m", "pint.pint_convert", "3 meter", "centimeter"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "3 meter = 300 cm"

@pytest.mark.depends_on('test_calling_registry_parses_quantity_expression', 'test_to_base_units_uses_registry_default_system')
def test_cli_uses_magnitude_one_when_input_has_only_units():
    """Verifies: PINT-CLI-012."""
    result = subprocess.run(
        [sys.executable, "-m", "pint.pint_convert", "meter", "centimeter"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "1 meter = 100 cm"

@pytest.mark.depends_on('test_calling_registry_parses_quantity_expression', 'test_to_base_units_uses_registry_default_system')
def test_cli_without_destination_converts_to_base_units():
    """Verifies: PINT-CLI-002, PINT-CLI-003, PINT-CLI-009."""
    result = subprocess.run(
        [sys.executable, "-m", "pint.pint_convert", "1 inch"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert "0.0254 m" in result.stdout

@pytest.mark.depends_on('test_calling_registry_parses_quantity_expression', 'test_to_base_units_uses_registry_default_system')
def test_cli_precision_option_controls_significant_digits():
    """Verifies: PINT-CLI-004."""
    result = subprocess.run(
        [sys.executable, "-m", "pint.pint_convert", "--prec", "3", "1 meter", "inch"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "1 meter = 39.4 in"

@pytest.mark.depends_on('test_calling_registry_parses_quantity_expression', 'test_to_base_units_uses_registry_default_system')
def test_cli_argument_error_exits_with_usage_status():
    """Verifies: PINT-CLI-008, PINT-ERR-013."""
    result = subprocess.run(
        [sys.executable, "-m", "pint.pint_convert"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 2
    assert "Unit converter" in result.stdout
