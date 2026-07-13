# Spec2Repo oracle - atomic tests for packaging-core-fullrepro-001
import json

import pytest


def test_package_shape_exposes_public_modules_and_version():
    import packaging
    from packaging import markers, metadata, requirements, specifiers, tags, utils, version

    assert isinstance(packaging.__version__, str)
    assert callable(version.parse)
    assert hasattr(specifiers, "SpecifierSet")
    assert hasattr(markers, "Marker")
    assert hasattr(requirements, "Requirement")
    assert hasattr(tags, "Tag")
    assert hasattr(utils, "canonicalize_name")
    assert hasattr(metadata, "Metadata")


def test_marker_extra_evaluation_normalizes_requested_extra():
    from packaging.markers import Marker

    marker = Marker("extra == 'PDF-Export'")

    assert marker.evaluate({"extra": "pdf_export"})
    assert not marker.evaluate({"extra": "docs"})


def test_marker_missing_environment_name_raises_public_error():
    from packaging.markers import InvalidMarker, Marker

    with pytest.raises(InvalidMarker):
        Marker("unknown_name == 'x'")


def test_tag_object_and_parse_tag_round_trip_public_values():
    from packaging.tags import Tag, parse_tag

    parsed = parse_tag("cp311-cp311-win_amd64")
    expected = Tag("cp311", "cp311", "win_amd64")

    assert expected in parsed
    assert str(expected) == "cp311-cp311-win_amd64"
    assert expected == Tag("cp311", "cp311", "win_amd64")


def test_metadata_parse_email_reports_unparsed_fields_as_errors():
    from packaging.metadata import parse_email

    raw, unparsed = parse_email("Metadata-Version: 2.1\nName: demo\nVersion: 1.0\nRequires-Dist: demo>=1\n")

    assert raw["name"] == "demo"
    assert raw["version"] == "1.0"
    assert raw["requires_dist"] == ["demo>=1"]
    assert unparsed == {}


def test_metadata_from_raw_validates_required_core_fields():
    from packaging.errors import ExceptionGroup
    from packaging.metadata import Metadata

    with pytest.raises(ExceptionGroup):
        Metadata.from_raw({"name": "demo"})


def test_direct_url_rejects_missing_info_section():
    from packaging.direct_url import DirectUrl, DirectUrlValidationError

    with pytest.raises(DirectUrlValidationError):
        DirectUrl.from_dict({"url": "https://example.com/pkg.tar.gz"})


def test_license_expression_canonicalizes_spdx_operators():
    from packaging.licenses import canonicalize_license_expression

    assert canonicalize_license_expression("mit or apache-2.0") == "MIT OR Apache-2.0"


def test_invalid_license_expression_raises_public_error():
    from packaging.licenses import InvalidLicenseExpression, canonicalize_license_expression

    with pytest.raises(InvalidLicenseExpression):
        canonicalize_license_expression("MIT AND")


def test_error_helper_exception_group_collects_public_errors():
    from packaging.errors import ExceptionGroup
    from packaging.version import InvalidVersion

    group = ExceptionGroup("many", [InvalidVersion("bad")])

    assert isinstance(group.exceptions[0], InvalidVersion)
    assert "many" in str(group)
