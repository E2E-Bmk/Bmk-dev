# Spec2Repo oracle - atomic tests for pint-fullrepro-001

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


def test_upstream_pi_theorem_simple_movement():
    """Verifies: PINT-UTIL-001, PINT-UTIL-003."""
    assert pi_theorem({"V": "m/s", "T": "s", "L": "m"}) == [
        {"V": 1, "T": 1, "L": -1}
    ]
    assert pi_theorem({"T": "s", "M": "grams", "L": "m", "g": "m/s**2"}) == [
        {"g": 1, "T": 2, "L": -1}
    ]

def test_upstream_registry_pi_theorem_accepts_public_dimensional_inputs():
    """Verifies: PINT-UTIL-002, PINT-UTIL-003."""
    ureg = UnitRegistry()
    inputs = {
        "as_strings": ("km/hour", "ms", "cm"),
        "as_quantities": (
            ureg.Quantity(1, "km/hour"),
            ureg.Quantity(1, "ms"),
            ureg.Quantity(1, "cm"),
        ),
        "as_units": (
            ureg.Quantity(1, "km/hour").units,
            ureg.Quantity(1, "ms").units,
            ureg.Quantity(1, "cm").units,
        ),
        "as_dimensionality": (
            ureg.Quantity(1, "km/hour").dimensionality,
            ureg.Quantity(1, "ms").dimensionality,
            ureg.Quantity(1, "cm").dimensionality,
        ),
    }
    for velocity, time, length in inputs.values():
        assert ureg.pi_theorem({"V": velocity, "T": time, "L": length}) == [
            {"V": 1.0, "T": 1.0, "L": -1.0}
        ]

def test_upstream_quantity_creation_from_public_inputs():
    """Verifies: PINT-QTY-001, PINT-QTY-003."""
    ureg = UnitRegistry(autoconvert_offset_to_baseunit=False)
    constructors = (
        (4.2, "meter"),
        (4.2, ureg.meter),
        ("4.2*meter",),
        ("4.2/meter**(-1)",),
        (ureg.Quantity(4.2, "meter"),),
    )
    for args in constructors:
        quantity = ureg.Quantity(*args)
        assert quantity.magnitude == pytest.approx(4.2)
        assert quantity.units == ureg.meter

    dimensionless = ureg.Quantity(4.2, None)
    assert dimensionless.magnitude == pytest.approx(4.2)
    assert dimensionless.unitless

def test_upstream_quantity_comparison_converts_compatible_units():
    """Verifies: PINT-QTY-008."""
    ureg = UnitRegistry(autoconvert_offset_to_baseunit=False)
    assert ureg.Quantity(1000, "millimeter") == ureg.Quantity(1, "meter")
    assert ureg.Quantity(1000, "millimeter/min") == ureg.Quantity(
        1000 / 60, "millimeter/s"
    )
    assert ureg.Quantity(10, "meter") < ureg.Quantity(5, "kilometer")
    assert ureg.Quantity(0, "meter") != ureg.Quantity(0, "second")

def test_upstream_cross_registry_operations_raise_value_error():
    """Verifies: PINT-QTY-009."""
    q1 = 1 * UnitRegistry().meter
    q2 = 1 * UnitRegistry().meter
    for operation in (
        operator.add,
        operator.iadd,
        operator.sub,
        operator.isub,
        operator.mul,
        operator.imul,
        operator.floordiv,
        operator.ifloordiv,
        operator.truediv,
        operator.itruediv,
    ):
        with pytest.raises(ValueError):
            operation(q1, q2)

def test_upstream_unit_multiplication_creates_quantities():
    """Verifies: PINT-QTY-002, PINT-QTY-004."""
    ureg = UnitRegistry()
    unit = ureg.Unit("m")
    assert unit * 1 == ureg.Quantity(1, "m")
    assert unit * 0.5 == ureg.Quantity(0.5, "m")
    assert unit * ureg.Quantity(1, "m") == ureg.Quantity(1, "m**2")
    assert 1 * unit == ureg.Quantity(1, "m")

def test_upstream_unit_division_creates_quantities():
    """Verifies: PINT-QTY-002, PINT-QTY-004."""
    ureg = UnitRegistry()
    unit = ureg.Unit("m")
    assert unit / 1 == ureg.Quantity(1, "m")
    assert unit / 0.5 == ureg.Quantity(2.0, "m")
    assert unit / ureg.Quantity(1, "m") == ureg.Quantity(1)
    assert 1 / unit == ureg.Quantity(1, "1/m")

def test_upstream_unit_power_accepts_numeric_and_rejects_mapping():
    """Verifies: PINT-QTY-004."""
    ureg = UnitRegistry()
    unit = ureg.Unit("m")
    assert unit**2 == ureg.Unit("m**2")
    with pytest.raises(TypeError):
        unit ** {}

def test_upstream_unit_is_compatible_with_public_inputs():
    """Verifies: PINT-QTY-024."""
    ureg = UnitRegistry()
    unit = ureg.Unit("m")
    assert unit.is_compatible_with("m")
    assert not unit.is_compatible_with("m**2")
    assert unit.is_compatible_with(ureg.Unit("m"))
    assert not unit.is_compatible_with(ureg.Unit("m**2"))
    assert ureg.Unit("").is_compatible_with(0.5)

def test_default_registry_loads_bundled_units():
    """Verifies: PINT-REG-002, PINT-REG-015."""
    ureg = UnitRegistry()
    assert "meter" in ureg
    assert ureg.meter == ureg.parse_units("meter")
    assert ureg["meter"].units == ureg.meter

def test_empty_registry_rejects_unknown_default_unit():
    """Verifies: PINT-REG-003, PINT-ERR-001."""
    ureg = UnitRegistry(None)
    with pytest.raises(UndefinedUnitError):
        ureg.parse_units("meter")

def test_iterable_definitions_add_custom_unit_and_plural_alias():
    """Verifies: PINT-REG-001, PINT-REG-004, PINT-INV-001."""
    ureg = UnitRegistry(["day = [time]", "dog_year = 52 * day = dy"])
    dog_age = (520 * ureg.day).to("dog_years")
    assert "dog_year" in ureg
    assert_quantity_close(dog_age, 10, ureg.dog_year)

def test_invalid_definition_line_raises_definition_syntax_error():
    """Verifies: PINT-REG-005, PINT-ERR-005."""
    ureg = UnitRegistry()
    with pytest.raises((DefinitionSyntaxError, TypeError)):
        ureg.define("not valid definition syntax")

def test_redefinition_policy_raise_rejects_reused_name():
    """Verifies: PINT-REG-006, PINT-ERR-006."""
    ureg = UnitRegistry(on_redefinition="raise")
    ureg.define("stage3_foo = 1 * meter")
    with pytest.raises(RedefinitionError):
        ureg.define("stage3_foo = 2 * meter")

def test_redefinition_policy_ignore_replaces_definition():
    """Verifies: PINT-REG-007."""
    ureg = UnitRegistry(on_redefinition="ignore")
    ureg.define("stage3_bar = 1 * meter")
    ureg.define("stage3_bar = 2 * meter")
    assert_quantity_close(ureg("1 stage3_bar").to("meter"), 2, ureg.meter)

def test_symbol_placeholder_allows_alias_without_symbol():
    """Verifies: PINT-REG-008, PINT-REG-009."""
    ureg = UnitRegistry()
    ureg.define("stage3_widget = 2 * meter = _ = stage3_gadget")
    assert ureg.parse_units("stage3_gadget") == ureg.stage3_widget
    assert_quantity_close((3 * ureg.stage3_gadget).to("meter"), 6, ureg.meter)

def test_prefix_definition_applies_during_parsing():
    """Verifies: PINT-REG-010."""
    ureg = UnitRegistry(None)
    ureg.define("[stage3_length]")
    ureg.define("stage3foo = [stage3_length]")
    ureg.define("kilo- = 1000 = k-")
    assert_quantity_close((1 * ureg.kstage3foo).to("stage3foo"), 1000, ureg.stage3foo)

def test_dimension_definition_supports_derived_dimension():
    """Verifies: PINT-REG-011."""
    ureg = UnitRegistry(None)
    ureg.define("[stage3_length]")
    ureg.define("[stage3_area] = [stage3_length] ** 2")
    ureg.define("stage3meter = [stage3_length]")
    q = 4 * ureg.stage3meter**2
    assert q.dimensionality == ureg.get_dimensionality("[stage3_area]")

def test_alias_directive_adds_lookup_name_to_existing_unit():
    """Verifies: PINT-REG-012, PINT-INV-001."""
    ureg = UnitRegistry()
    ureg.define("stage3_span = 2 * meter")
    ureg.define("@alias stage3_span = stage3_span_alias")
    assert_quantity_close((5 * ureg.stage3_span_alias).to("meter"), 10, ureg.meter)

def test_attribute_item_and_parse_units_return_same_bound_unit():
    """Verifies: PINT-REG-015."""
    ureg = UnitRegistry()
    assert ureg.meter == ureg.parse_units("meter")
    assert ureg["meter"].units == ureg.meter

def test_calling_registry_parses_quantity_expression():
    """Verifies: PINT-REG-016, PINT-QTY-001."""
    ureg = UnitRegistry()
    quantity = ureg("2.5 meter / second")
    assert_quantity_close(quantity, 2.5, ureg.meter / ureg.second)

def test_parse_expression_supports_numbers_powers_and_parentheses():
    """Verifies: PINT-REG-017."""
    ureg = UnitRegistry()
    quantity = ureg.parse_expression("8 * meter ** 2 / (2 * second)")
    assert_quantity_close(quantity, 4, ureg.meter**2 / ureg.second)

def test_parse_expression_supports_implicit_multiplication():
    """Verifies: PINT-REG-017, PINT-REG-018."""
    ureg = UnitRegistry()
    quantity = ureg.parse_expression("2 meter second")
    assert_quantity_close(quantity, 2, ureg.meter * ureg.second)

def test_parse_expression_supports_nan_and_infinity():
    """Verifies: PINT-REG-017."""
    ureg = UnitRegistry()
    assert math.isnan(ureg("nan meter").magnitude)
    assert math.isinf(ureg("infinity second").magnitude)

def test_parse_expression_supports_dimensionless():
    """Verifies: PINT-REG-017."""
    ureg = UnitRegistry()
    quantity = ureg("3 dimensionless")
    assert quantity.dimensionless
    assert quantity.unitless

def test_parse_units_rejects_scale_factor():
    """Verifies: PINT-REG-019."""
    ureg = UnitRegistry()
    with pytest.raises(ValueError):
        ureg.parse_units("2 meter")

def test_unknown_unit_token_raises_undefined_unit_error():
    """Verifies: PINT-REG-020, PINT-ERR-001."""
    ureg = UnitRegistry()
    with pytest.raises(UndefinedUnitError):
        ureg.parse_expression("1 stage3_unknown_unit")

def test_case_insensitive_registry_resolves_unit_names():
    """Verifies: PINT-REG-021."""
    ureg = UnitRegistry(case_sensitive=False)
    assert ureg.parse_units("METER") == ureg.meter

def test_preprocessor_rewrites_expression_before_parsing():
    """Verifies: PINT-REG-027."""
    ureg = UnitRegistry(preprocessors=[lambda value: value.replace("bucks", "meter")])
    assert_quantity_close(ureg("5 bucks"), 5, ureg.meter)

def test_non_int_type_controls_parsed_decimal_magnitudes():
    """Verifies: PINT-REG-028."""
    from decimal import Decimal

    ureg = UnitRegistry(non_int_type=Decimal)
    quantity = ureg("1.1 meter")
    assert isinstance(quantity.magnitude, Decimal)
    assert quantity.magnitude == Decimal("1.1")

def test_quantity_public_magnitude_and_unit_attributes():
    """Verifies: PINT-QTY-001, PINT-QTY-003."""
    ureg = UnitRegistry()
    quantity = ureg.Quantity(7, "meter")
    assert quantity.magnitude == quantity.m == 7
    assert quantity.units == quantity.u == ureg.meter
    assert not quantity.dimensionless

def test_number_multiplied_by_unit_returns_quantity():
    """Verifies: PINT-QTY-002."""
    ureg = UnitRegistry()
    quantity = 4 * ureg.second
    assert_quantity_close(quantity, 4, ureg.second)

def test_unit_arithmetic_combines_unit_expressions():
    """Verifies: PINT-QTY-004."""
    ureg = UnitRegistry()
    assert ureg.meter / ureg.second == ureg.parse_units("meter / second")
    assert ureg.meter**2 == ureg.parse_units("meter ** 2")

def test_quantity_multiplication_division_and_power_combine_units():
    """Verifies: PINT-QTY-007."""
    ureg = UnitRegistry()
    force = (2 * ureg.kilogram) * (3 * ureg.meter / ureg.second**2)
    assert_quantity_close(force, 6, ureg.kilogram * ureg.meter / ureg.second**2)

def test_addition_converts_compatible_operands():
    """Verifies: PINT-QTY-008."""
    ureg = UnitRegistry()
    total = 1 * ureg.meter + 50 * ureg.centimeter
    assert_quantity_close(total, 1.5, ureg.meter)

def test_comparison_converts_compatible_operands():
    """Verifies: PINT-QTY-008."""
    ureg = UnitRegistry()
    assert 100 * ureg.centimeter == 1 * ureg.meter
    assert 2 * ureg.meter > 150 * ureg.centimeter

def test_cross_registry_arithmetic_raises_value_error():
    """Verifies: PINT-QTY-009."""
    left = UnitRegistry()
    right = UnitRegistry()
    with pytest.raises(ValueError):
        _ = 1 * left.meter + 1 * right.meter

def test_incompatible_addition_raises_dimensionality_error():
    """Verifies: PINT-QTY-010, PINT-ERR-002."""
    ureg = UnitRegistry()
    with pytest.raises(DimensionalityError):
        _ = 1 * ureg.meter + 1 * ureg.second

def test_ambiguous_offset_arithmetic_raises_offset_error():
    """Verifies: PINT-QTY-011, PINT-ERR-003."""
    ureg = UnitRegistry()
    with pytest.raises(OffsetUnitCalculusError):
        _ = (1 * ureg.degC) * 2

def test_to_returns_new_quantity_without_mutating_source():
    """Verifies: PINT-QTY-012, PINT-INV-003."""
    ureg = UnitRegistry()
    original = 1 * ureg.meter
    converted = original.to("centimeter")
    assert_quantity_close(converted, 100, ureg.centimeter)
    assert_quantity_close(original, 1, ureg.meter)
    assert converted is not original

def test_ito_mutates_quantity_and_returns_none():
    """Verifies: PINT-QTY-012, PINT-INV-003."""
    ureg = UnitRegistry()
    quantity = 1 * ureg.meter
    result = quantity.ito("centimeter")
    assert result is None
    assert_quantity_close(quantity, 100, ureg.centimeter)

def test_to_base_units_uses_registry_default_system():
    """Verifies: PINT-QTY-013, PINT-SYS-002."""
    ureg = UnitRegistry()
    converted = (1 * ureg.inch).to_base_units()
    assert_quantity_close(converted, 0.0254, ureg.meter)

def test_to_base_units_accepts_explicit_system():
    """Verifies: PINT-QTY-013, PINT-SYS-004."""
    ureg = UnitRegistry()
    converted = (1 * ureg.newton).to_base_units(system="cgs")
    assert converted.magnitude == pytest.approx(100000)
    assert converted.units == ureg.gram * ureg.centimeter / ureg.second**2

def test_to_root_units_uses_primitive_definition_units():
    """Verifies: PINT-QTY-014."""
    ureg = UnitRegistry()
    converted = (1 * ureg.newton).to_root_units()
    assert converted.magnitude == pytest.approx(1000)
    assert converted.units == ureg.gram * ureg.meter / ureg.second**2

def test_to_reduced_units_keeps_named_derived_unit_when_already_reduced():
    """Verifies: PINT-QTY-015."""
    ureg = UnitRegistry()
    quantity = (1 * ureg.joule / ureg.newton).to_reduced_units()
    assert_quantity_close(quantity, 1, ureg.joule / ureg.newton)

def test_to_compact_chooses_human_readable_prefix():
    """Verifies: PINT-QTY-016."""
    ureg = UnitRegistry()
    assert_quantity_close((1500 * ureg.meter).to_compact(), 1.5, ureg.kilometer)

def test_to_compact_restricted_to_unit_family():
    """Verifies: PINT-QTY-016."""
    ureg = UnitRegistry()
    compact = (0.003 * ureg.meter).to_compact("millimeter")
    assert_quantity_close(compact, 3, ureg.millimeter)

def test_to_unprefixed_removes_si_prefix():
    """Verifies: PINT-QTY-017."""
    ureg = UnitRegistry()
    assert_quantity_close((2 * ureg.kilometer).to_unprefixed(), 2000, ureg.meter)

def test_to_preferred_uses_caller_supplied_preferred_units():
    """Verifies: PINT-QTY-018."""
    ureg = UnitRegistry()
    assert_quantity_close((120 * ureg.second).to_preferred([ureg.minute]), 2, ureg.minute)

def test_unknown_conversion_target_raises_undefined_unit_error():
    """Verifies: PINT-QTY-019, PINT-ERR-001."""
    ureg = UnitRegistry()
    with pytest.raises(UndefinedUnitError):
        (1 * ureg.meter).to("stage3_missing_unit")

def test_m_as_returns_converted_magnitude_only():
    """Verifies: PINT-QTY-022."""
    ureg = UnitRegistry()
    assert (250 * ureg.centimeter).m_as("meter") == pytest.approx(2.5)

def test_to_timedelta_converts_time_quantities():
    """Verifies: PINT-QTY-021."""
    ureg = UnitRegistry()
    assert (90 * ureg.second).to_timedelta() == datetime.timedelta(seconds=90)

def test_to_timedelta_rejects_non_time_dimensions():
    """Verifies: PINT-QTY-021, PINT-ERR-002."""
    ureg = UnitRegistry()
    with pytest.raises(DimensionalityError):
        (1 * ureg.meter).to_timedelta()

def test_is_compatible_with_accepts_compatible_strings():
    """Verifies: PINT-QTY-024."""
    ureg = UnitRegistry()
    assert (1 * ureg.meter).is_compatible_with("inch")
    assert not (1 * ureg.meter).is_compatible_with("second")

def test_pi_theorem_returns_dimensionless_products():
    """Verifies: PINT-UTIL-001, PINT-UTIL-003."""
    result = pi_theorem(
        {"F": "[mass] * [length] / [time] ** 2", "m": "[mass]", "a": "[length] / [time] ** 2"}
    )
    assert result == [{"F": -1.0, "m": 1.0, "a": 1.0}]

def test_registry_pi_theorem_resolves_units_through_registry():
    """Verifies: PINT-UTIL-002."""
    ureg = UnitRegistry()
    result = ureg.pi_theorem({"speed": "meter/second", "time": "second", "distance": "meter"})
    assert result == [{"speed": 1.0, "time": 1.0, "distance": -1.0}]
