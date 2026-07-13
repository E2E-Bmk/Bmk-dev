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


def test_requirement_parses_url_extras_and_marker_together():
    from packaging.requirements import Requirement

    req = Requirement("Demo[PDF] @ https://example.com/demo.whl ; python_version >= '3.11'")

    assert req.name == "Demo"
    assert req.extras == {"PDF"}
    assert req.url == "https://example.com/demo.whl"
    assert "python_version" in str(req.marker)


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


def test_direct_url_round_trips_archive_info_to_json():
    from packaging.direct_url import ArchiveInfo, DirectUrl

    direct = DirectUrl(url="https://example.com/pkg.tar.gz", archive_info=ArchiveInfo(hashes={"sha256": "abc"}))
    data = direct.to_dict()
    restored = DirectUrl.from_dict(data)

    assert data["url"] == "https://example.com/pkg.tar.gz"
    assert data["archive_info"]["hashes"] == {"sha256": "abc"}
    assert restored == direct


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


def test_cross_component_requirement_marker_and_specifier_agree():
    from packaging.requirements import Requirement
    from packaging.version import Version

    req = Requirement("demo>=1.0; python_version >= '3.8'")

    assert Version("1.2") in req.specifier
    assert req.marker.evaluate({"python_version": "3.11"})
    assert not req.marker.evaluate({"python_version": "3.7"})


def test_requirement_version_and_marker_form_one_acceptance_decision():
    from packaging.requirements import Requirement
    from packaging.version import Version

    req = Requirement("demo>=1.0,<2; python_version >= '3.10'")
    assert Version("1.8") in req.specifier and req.marker.evaluate({"python_version": "3.12"})
    assert Version("2.0") not in req.specifier
    assert not req.marker.evaluate({"python_version": "3.9"})


def test_requirement_extra_marker_and_version_gate_compose():
    from packaging.requirements import Requirement
    from packaging.version import Version

    req = Requirement("demo[PDF]>=2; extra == 'pdf'")
    assert req.extras == {"PDF"}
    assert Version("2.3") in req.specifier
    assert req.marker.evaluate({"extra": "PDF"})
    assert not req.marker.evaluate({"extra": "docs"})


def test_prerelease_ordering_respects_specifier_policy():
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    versions = [Version(value) for value in ("2.0", "1.5", "2.0rc1", "1.0")]
    allowed = SpecifierSet(">=1,<2")
    assert sorted(versions) == [Version("1.0"), Version("1.5"), Version("2.0rc1"), Version("2.0")]
    assert [value for value in versions if value in allowed] == [Version("1.5"), Version("1.0")]


def test_compatible_release_and_platform_marker_agree():
    from packaging.markers import Marker
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    versions = SpecifierSet("~=3.11.2")
    platform = Marker("sys_platform == 'linux'")
    assert Version("3.11.9") in versions
    assert Version("3.12.0") not in versions
    assert platform.evaluate({"sys_platform": "linux"})
    assert not platform.evaluate({"sys_platform": "win32"})


def test_metadata_requirements_drive_marker_and_version_checks():
    from packaging.metadata import Metadata
    from packaging.requirements import Requirement
    from packaging.version import Version

    metadata = Metadata.from_raw({"metadata_version": "2.1", "name": "demo", "version": "1.0", "requires_dist": ["dep>=2; python_version >= '3.10'"]})
    dependency = metadata.requires_dist[0]
    assert isinstance(dependency, Requirement)
    assert Version("2.4") in dependency.specifier
    assert dependency.marker.evaluate({"python_version": "3.11"})
    assert not dependency.marker.evaluate({"python_version": "3.9"})


def test_wheel_filename_projects_name_version_build_and_tags():
    from packaging.tags import Tag
    from packaging.utils import parse_wheel_filename
    from packaging.version import Version

    name, version, build, tags = parse_wheel_filename("Demo_Pkg-1.2-3-py3-none-any.whl")
    assert name == "demo-pkg"
    assert version == Version("1.2")
    assert build == (3, "")
    assert Tag("py3", "none", "any") in tags


def test_sdist_filename_projects_canonical_name_and_ordered_version():
    from packaging.utils import canonicalize_name, parse_sdist_filename
    from packaging.version import Version

    name, version = parse_sdist_filename("Demo_Pkg-1.4.tar.gz")
    assert name == canonicalize_name("Demo_Pkg")
    assert version == Version("1.4")
    assert Version("1.3") < version < Version("2")


def test_requirement_name_canonicalization_preserves_specifier_semantics():
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    from packaging.version import Version

    req = Requirement("Demo_Pkg!=1.5,>=1")
    assert canonicalize_name(req.name) == "demo-pkg"
    assert Version("1.4") in req.specifier
    assert Version("1.5") not in req.specifier


def test_marker_boolean_expression_controls_requirement_applicability():
    from packaging.requirements import Requirement
    from packaging.version import Version

    req = Requirement("demo>=1; (python_version >= '3.10' and platform_machine == 'x86_64') or sys_platform == 'darwin'")
    assert Version("1.1") in req.specifier
    assert req.marker.evaluate({"python_version": "3.11", "platform_machine": "x86_64", "sys_platform": "linux"})
    assert req.marker.evaluate({"python_version": "3.8", "platform_machine": "arm64", "sys_platform": "darwin"})
    assert not req.marker.evaluate({"python_version": "3.8", "platform_machine": "arm64", "sys_platform": "linux"})


def test_requirement_url_extras_and_environment_remain_consistent():
    from packaging.requirements import Requirement

    req = Requirement("Demo[fast] @ https://example.invalid/demo-1.0.whl ; os_name == 'posix'")
    assert req.name == "Demo"
    assert req.extras == {"fast"}
    assert req.url.endswith("demo-1.0.whl")
    assert req.marker.evaluate({"os_name": "posix"})
    assert not req.marker.evaluate({"os_name": "nt"})
