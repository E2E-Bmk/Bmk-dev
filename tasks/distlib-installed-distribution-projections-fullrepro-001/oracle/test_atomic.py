from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest


def test_distinfo_dirname_normalizes_project_dash():
    from distlib.database import DistributionPath

    assert DistributionPath.distinfo_dirname("acme-widgets", "1.2.3") == "acme_widgets-1.2.3.dist-info"


def test_distribution_path_discovers_installed_distribution(installed_tree):
    from distlib.database import DistributionPath, InstalledDistribution

    found = list(DistributionPath([str(installed_tree["site"])]).get_distributions())

    assert len(found) == 1
    assert isinstance(found[0], InstalledDistribution)


def test_get_distribution_is_case_insensitive(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("Acme-Widgets")

    assert dist.name == "acme-widgets"
    assert dist.version == "1.2.3"


def test_installed_distribution_string_uses_name_and_version(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert str(dist) == "acme-widgets 1.2.3"
    assert dist.name_and_version == "acme-widgets (1.2.3)"


def test_requested_file_sets_requested_flag(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert dist.requested is True


def test_list_installed_files_reads_record_rows(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    rows = list(dist.list_installed_files())
    paths = [row[0] for row in rows]

    assert "acme_widgets/core.py" in paths
    assert "acme_widgets-1.2.3.dist-info/RECORD" in paths
    assert all(len(row) == 3 for row in rows)


def test_check_installed_files_accepts_matching_hashes_and_sizes(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert dist.check_installed_files() == []


def test_list_distinfo_files_filters_record_to_metadata_directory(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    relpaths = {Path(path).name for path in dist.list_distinfo_files()}

    assert {"pydist.json", "METADATA", "INSTALLER", "REQUESTED", "RESOURCES", "pydist-exports.json", "RECORD"} <= relpaths
    assert "core.py" not in relpaths


def test_get_distinfo_file_returns_file_under_distribution_metadata(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert Path(dist.get_distinfo_file("pydist.json")) == installed_tree["info"] / "pydist.json"


def test_get_distinfo_resource_reads_metadata_bytes(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    resource = dist.get_distinfo_resource("pydist.json")

    assert resource.bytes.startswith(b"{")
    assert b"acme-widgets" in resource.bytes
    assert resource.size == len(resource.bytes)


def test_get_resource_path_resolves_resources_csv_entry(installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(installed_tree["site"])])

    assert Path(env.get_file_path("acme-widgets", "data/config.json")) == installed_tree["data_file"]


def test_exports_json_returns_named_export_entries(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    entry = dist.exports["console_scripts"]["acme-widget"]

    assert entry.name == "acme-widget"
    assert entry.prefix == "acme_widgets.core"
    assert entry.suffix == "make_value"
    assert entry.flags == ["gui=false"]


def test_distribution_provides_includes_self_and_metadata_alias(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert "acme-widgets (1.2.3)" in dist.provides
    assert "acme-alias (1.2.3)" in dist.provides


def test_distribution_matches_requirement_with_version_constraints(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert dist.matches_requirement("acme-widgets (>=1.0)")
    assert not dist.matches_requirement("acme-widgets (<1.0)")


def test_distribution_path_provides_distribution_finds_alias(installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(installed_tree["site"])])
    providers = list(env.provides_distribution("acme-alias", "==1.2.3"))

    assert [dist.name for dist in providers] == ["acme-widgets"]


def test_metadata_mapping_exposes_common_fields():
    from distlib.metadata import Metadata

    metadata = Metadata(
        mapping={
            "metadata_version": "2.0",
            "name": "sample-project",
            "version": "4.5",
            "summary": "A sample",
            "license": "MIT",
        }
    )

    assert metadata.name == "sample-project"
    assert metadata.name_and_version == "sample-project-4.5"
    assert metadata.todict()["summary"] == "A sample"


def test_metadata_keywords_string_becomes_list():
    from distlib.metadata import Metadata

    metadata = Metadata(mapping={"metadata_version": "2.0", "name": "kwdemo", "version": "1", "summary": "Keywords"})
    metadata.keywords = "packaging wheels metadata"

    assert metadata.keywords == ["packaging", "wheels", "metadata"]


def test_metadata_get_requirements_filters_extras():
    from distlib.metadata import Metadata

    metadata = Metadata(
        mapping={
            "metadata_version": "2.0",
            "name": "requires-demo",
            "version": "1",
            "summary": "Requirements",
            "extras": ["cli"],
            "run_requires": [
                {"requires": ["base-lib (>=1.0)"]},
                {"extra": "cli", "requires": ["click (>=8)"]},
                {"extra": "docs", "requires": ["sphinx"]},
            ],
        }
    )

    assert metadata.get_requirements(metadata.run_requires, extras=["cli"]) == ["base-lib (>=1.0)", "click (>=8)"]


def test_metadata_write_json_round_trips_mapping(tmp_path):
    from distlib.metadata import Metadata

    metadata = Metadata(mapping={"metadata_version": "2.0", "name": "json-demo", "version": "2", "summary": "JSON"})
    path = tmp_path / "pydist.json"
    metadata.write(path=str(path))

    loaded = Metadata(path=str(path))

    assert loaded.dictionary == metadata.dictionary


def test_manifest_findall_discovers_local_files(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    relpaths = {Path(path).relative_to(manifest_tree).as_posix() for path in manifest.allfiles}

    assert {"README.txt", "LICENSE", ".hidden", "pkg/module.py", "pkg/data/config.json"} <= relpaths


def test_manifest_include_adds_matching_top_level_file(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    manifest.process_directive("include README.txt LICENSE")

    assert {Path(path).name for path in manifest.files} == {"README.txt", "LICENSE"}


def test_manifest_recursive_include_and_exclude_filter_tree(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    manifest.process_directive("recursive-include pkg *.py *.json")
    manifest.process_directive("recursive-exclude pkg *.json")
    relpaths = {Path(path).relative_to(manifest_tree).as_posix() for path in manifest.files}

    assert relpaths == {"pkg/__init__.py", "pkg/module.py"}


def test_manifest_graft_and_prune_control_subtrees(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    manifest.process_directive("graft pkg")
    manifest.process_directive("prune pkg/data")
    relpaths = {Path(path).relative_to(manifest_tree).as_posix() for path in manifest.files}

    assert relpaths == {"pkg/__init__.py", "pkg/module.py"}


def test_manifest_add_many_and_sorted_can_include_directories(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.add_many(["pkg/module.py", "docs/index.rst"])
    relpaths = [Path(path).relative_to(manifest_tree).as_posix() for path in manifest.sorted(wantdirs=True)]

    assert relpaths[0] == "."
    assert set(relpaths) == {".", "docs", "docs/index.rst", "pkg", "pkg/module.py"}


def test_manifest_clear_removes_file_sets(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    manifest.add("README.txt")
    manifest.clear()

    assert manifest.files == set()
    assert manifest.allfiles == []


def test_resource_finder_identifies_container_and_file(installed_tree):
    from distlib.resources import finder_for_path

    finder = finder_for_path(str(installed_tree["site"]))
    container = finder.find("acme_widgets")
    resource = finder.find("acme_widgets/data/config.json")

    assert container.is_container is True
    assert "core.py" in container.resources
    assert resource.is_container is False
    assert resource.bytes.startswith(b"{")


def test_resource_finder_iterator_walks_nested_resources(installed_tree):
    from distlib.resources import finder_for_path

    finder = finder_for_path(str(installed_tree["site"]))
    names = {resource.name for resource in finder.iterator("acme_widgets")}

    assert {"acme_widgets/__init__.py", "acme_widgets/core.py", "acme_widgets/data/config.json"} <= names


def test_wheel_filename_and_tags_parse_from_filename(wheel_file):
    from distlib.wheel import Wheel

    wheel = Wheel(str(wheel_file))

    assert wheel.name == "acme_wheel"
    assert wheel.version == "2.0"
    assert wheel.filename == wheel_file.name
    assert list(wheel.tags) == [("py3", "none", "any")]


def test_wheel_process_shebang_normalizes_existing_interpreter(wheel_file):
    from distlib.wheel import Wheel

    wheel = Wheel(str(wheel_file))
    data = wheel.process_shebang(b"#!/usr/bin/python -O\nprint('x')\n")

    assert data == b"#!python -O\nprint('x')\n"


def test_wheel_get_hash_returns_named_digest(wheel_file):
    from distlib.wheel import Wheel

    wheel = Wheel(str(wheel_file))
    kind, digest = wheel.get_hash(b"payload")

    assert kind == "sha256"
    assert isinstance(digest, str)
    assert len(digest) > 20
