from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest


@pytest.mark.depends_on("test_distribution_path_discovers_installed_distribution", "test_metadata_mapping_exposes_common_fields")
def test_distribution_metadata_agrees_with_serialized_metadata_file(installed_tree):
    from distlib.database import DistributionPath
    from distlib.metadata import Metadata

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    metadata = Metadata(path=str(installed_tree["info"] / "METADATA"), scheme="legacy")

    assert (dist.name, dist.version, dist.metadata.summary) == (metadata.name, metadata.version, metadata.summary)


@pytest.mark.depends_on("test_list_installed_files_reads_record_rows", "test_check_installed_files_accepts_matching_hashes_and_sizes")
def test_record_rows_distinfo_files_and_integrity_check_share_same_distribution(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    installed_paths = {row[0] for row in dist.list_installed_files()}
    distinfo_paths = {Path(path).relative_to(installed_tree["site"]).as_posix() for path in dist.list_distinfo_files()}

    assert dist.check_installed_files() == []
    assert distinfo_paths < installed_paths
    assert "acme_widgets/data/config.json" in installed_paths


@pytest.mark.depends_on("test_get_resource_path_resolves_resources_csv_entry", "test_resource_finder_identifies_container_and_file")
def test_resource_csv_path_and_resource_finder_read_same_bytes(installed_tree):
    from distlib.database import DistributionPath
    from distlib.resources import finder_for_path

    env = DistributionPath([str(installed_tree["site"])])
    resource_path = Path(env.get_file_path("acme-widgets", "data/config.json"))
    finder = finder_for_path(str(installed_tree["site"]))
    resource = finder.find("acme_widgets/data/config.json")

    assert resource_path.read_bytes() == resource.bytes
    assert json.loads(resource.bytes.decode("utf-8")) == {"color": "blue", "count": 3}


@pytest.mark.depends_on("test_exports_json_returns_named_export_entries", "test_distribution_path_discovers_installed_distribution")
def test_distribution_exports_match_environment_export_lookup(installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(installed_tree["site"])])
    dist = env.get_distribution("acme-widgets")
    direct = dist.exports["console_scripts"]["acme-widget"]
    exported = list(env.get_exported_entries("console_scripts", "acme-widget"))

    assert exported == [direct]
    assert exported[0].suffix == "make_value"


@pytest.mark.depends_on("test_distribution_provides_includes_self_and_metadata_alias", "test_distribution_matches_requirement_with_version_constraints")
def test_provides_distribution_and_requirement_matching_project_same_alias(installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(installed_tree["site"])])
    provider = list(env.provides_distribution("acme-alias", "==1.2.3"))[0]

    assert provider.matches_requirement("acme-widgets (==1.2.3)")
    assert provider.metadata.provides == provider.provides


@pytest.mark.depends_on("test_get_distribution_is_case_insensitive", "test_distribution_path_discovers_installed_distribution")
def test_distribution_cache_clear_keeps_public_lookup_consistent(second_installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(second_installed_tree["site"])])
    first_names = sorted(dist.name for dist in env.get_distributions())
    env.clear_cache()
    second_names = sorted(dist.name for dist in env.get_distributions())

    assert first_names == second_names == ["acme-widgets", "other-pkg"]
    assert env.get_distribution("OTHER-PKG").version == "0.5"


@pytest.mark.depends_on("test_list_installed_files_reads_record_rows", "test_check_installed_files_accepts_matching_hashes_and_sizes")
def test_write_installed_files_rebuilds_record_and_check_uses_new_rows(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    selected = [installed_tree["core_file"], installed_tree["data_file"], installed_tree["info"] / "METADATA"]
    record_path = dist.write_installed_files([str(path) for path in selected], prefix=str(installed_tree["site"]))
    rows = list(dist.list_installed_files())

    assert record_path == "acme_widgets-1.2.3.dist-info/RECORD"
    assert {row[0] for row in rows} == {
        "acme_widgets/core.py",
        "acme_widgets/data/config.json",
        "acme_widgets-1.2.3.dist-info/METADATA",
        "acme_widgets-1.2.3.dist-info/RECORD",
    }
    assert dist.check_installed_files() == []


@pytest.mark.depends_on("test_get_distinfo_file_returns_file_under_distribution_metadata", "test_requested_file_sets_requested_flag")
def test_shared_locations_write_and_property_project_same_paths(installed_tree, tmp_path):
    from distlib.database import DistributionPath

    paths = {}
    for key in ("prefix", "lib", "headers", "scripts", "data"):
        paths[key] = str(tmp_path / key)
        Path(paths[key]).mkdir()
    paths["namespace"] = [str(tmp_path / "ns1"), str(tmp_path / "ns2")]
    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    shared_path = dist.write_shared_locations(paths)
    reloaded = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert Path(shared_path) == installed_tree["info"] / "SHARED"
    assert reloaded.shared_locations["scripts"] == paths["scripts"]
    assert reloaded.shared_locations["namespace"] == paths["namespace"]


@pytest.mark.depends_on("test_metadata_write_json_round_trips_mapping", "test_distribution_provides_includes_self_and_metadata_alias")
def test_json_metadata_can_construct_installed_distribution_projection(installed_tree, tmp_path):
    from distlib.database import InstalledDistribution
    from distlib.metadata import Metadata

    metadata = Metadata(
        mapping={"metadata_version": "2.0", "name": "json-dist", "version": "7.0", "summary": "JSON dist"}
    )
    path = tmp_path / "pydist.json"
    metadata.write(path=str(path))
    loaded = Metadata(path=str(path))
    dist = InstalledDistribution(str(installed_tree["info"]), metadata=loaded)

    assert dist.name_and_version == "json-dist (7.0)"
    assert "json-dist (7.0)" in dist.provides


@pytest.mark.depends_on("test_metadata_mapping_exposes_common_fields", "test_metadata_write_json_round_trips_mapping")
def test_legacy_metadata_write_round_trips_to_public_dictionary(tmp_path):
    from distlib.metadata import Metadata

    metadata = Metadata(
        mapping={
            "metadata_version": "2.0",
            "name": "legacy-json",
            "version": "3.1",
            "summary": "Legacy projection",
            "extensions": {
                "python.project": {
                    "project_urls": {"Home": "https://example.invalid/legacy-json"},
                    "contacts": [{"name": "Legacy Author"}],
                }
            },
            "run_requires": [{"requires": ["dep-one (>=1)"]}],
        }
    )
    path = tmp_path / "METADATA"
    metadata.write(path=str(path), legacy=True)
    loaded = Metadata(path=str(path), scheme="legacy")

    assert loaded.dictionary["name"] == "legacy-json"
    assert loaded.dictionary["run_requires"] == [{"requires": ["dep-one (>=1)"]}]


@pytest.mark.depends_on("test_manifest_findall_discovers_local_files", "test_manifest_recursive_include_and_exclude_filter_tree")
def test_manifest_file_selection_matches_filesystem_projection(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    manifest.process_directive("recursive-include pkg *.py *.json")
    rel_manifest = {Path(path).relative_to(manifest_tree).as_posix() for path in manifest.files}
    rel_filesystem = {
        path.relative_to(manifest_tree).as_posix()
        for path in manifest_tree.joinpath("pkg").rglob("*")
        if path.is_file()
    }

    assert rel_manifest == rel_filesystem


@pytest.mark.depends_on("test_manifest_add_many_and_sorted_can_include_directories", "test_manifest_graft_and_prune_control_subtrees")
def test_manifest_sorted_with_dirs_preserves_parent_paths_for_selected_files(manifest_tree):
    from distlib.manifest import Manifest

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    manifest.process_directive("graft pkg")
    manifest.process_directive("prune pkg/data")
    relpaths = [Path(path).relative_to(manifest_tree).as_posix() for path in manifest.sorted(wantdirs=True)]

    assert relpaths == [".", "pkg", "pkg/__init__.py", "pkg/module.py"]


@pytest.mark.depends_on("test_resource_finder_identifies_container_and_file", "test_resource_finder_iterator_walks_nested_resources")
def test_package_resource_finder_matches_imported_filesystem_package(tmp_path):
    from distlib.resources import finder

    package = tmp_path / "pkgres"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "data.txt").write_text("resource-data\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    try:
        __import__("pkgres")
        resource_finder = finder("pkgres")
        container = resource_finder.find("")
        resource = resource_finder.find("data.txt")
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("pkgres", None)

    assert container.is_container is True
    assert "data.txt" in container.resources
    assert resource.bytes == b"resource-data\n"


@pytest.mark.depends_on("test_resource_finder_identifies_container_and_file", "test_resource_finder_iterator_walks_nested_resources")
def test_zip_package_resource_finder_projects_archive_members(tmp_path):
    from distlib.resources import finder

    archive = tmp_path / "zipdemo.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("zipdemo/__init__.py", "")
        zf.writestr("zipdemo/data/value.txt", "zip-resource\n")
    sys.path.insert(0, str(archive))
    try:
        __import__("zipdemo")
        resource_finder = finder("zipdemo")
        names = {resource.name for resource in resource_finder.iterator("")}
        data = resource_finder.find("data/value.txt").bytes
    finally:
        sys.path.remove(str(archive))
        sys.modules.pop("zipdemo", None)

    assert {"data/value.txt", "__init__.py"} <= names
    assert data == b"zip-resource\n"


@pytest.mark.depends_on("test_wheel_filename_and_tags_parse_from_filename", "test_wheel_get_hash_returns_named_digest")
def test_wheel_info_metadata_and_verify_agree_with_archive_record(wheel_file):
    from distlib.wheel import Wheel

    wheel = Wheel(str(wheel_file))
    with zipfile.ZipFile(wheel_file) as zf:
        archive_names = set(zf.namelist())
        record_text = zf.read("acme_wheel-2.0.dist-info/RECORD").decode("utf-8")

    wheel.verify()

    assert wheel.info["Wheel-Version"] == "1.1"
    assert wheel.metadata.name == "acme-wheel"
    assert set(row[0] for row in csv.reader(io.StringIO(record_text))) == archive_names


@pytest.mark.depends_on("test_wheel_filename_and_tags_parse_from_filename", "test_resource_finder_iterator_walks_nested_resources")
def test_wheel_mount_exposes_package_resource_and_unmount_removes_path(wheel_file):
    from distlib.resources import finder
    from distlib.wheel import Wheel

    wheel = Wheel(str(wheel_file))
    wheel.mount()
    try:
        import acme_wheel

        resource = finder("acme_wheel").find("data.txt")
        wheel_path_present = str(wheel_file.resolve()) in sys.path
    finally:
        wheel.unmount()
        sys.modules.pop("acme_wheel", None)

    assert acme_wheel.VALUE == "wheel"
    assert resource.bytes == b"wheel-data\n"
    assert wheel_path_present is True
    assert str(wheel_file.resolve()) not in sys.path


@pytest.mark.depends_on("test_wheel_process_shebang_normalizes_existing_interpreter", "test_wheel_get_hash_returns_named_digest")
def test_wheel_shebang_and_hash_match_recordable_script_content(wheel_file):
    from distlib.wheel import Wheel

    wheel = Wheel(str(wheel_file))
    script = wheel.process_shebang(b"print('hello')\n")
    kind, digest = wheel.get_hash(script)
    record_value = f"{kind}={digest}"

    assert script.startswith(b"#!python\n")
    assert record_value == f"sha256={digest}"


@pytest.mark.depends_on("test_get_resource_path_resolves_resources_csv_entry", "test_get_distinfo_resource_reads_metadata_bytes")
def test_file_path_resource_and_metadata_resource_share_distribution_context(installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(installed_tree["site"])])
    dist = env.get_distribution("acme-widgets")
    resource_path = env.get_file_path("acme-widgets", "data/config.json")
    metadata_resource = dist.get_distinfo_resource("pydist.json")

    assert Path(resource_path).read_text(encoding="utf-8") == installed_tree["data_file"].read_text(encoding="utf-8")
    assert dist.metadata.name.encode("utf-8") in metadata_resource.bytes


@pytest.mark.depends_on("test_exports_json_returns_named_export_entries", "test_get_resource_path_resolves_resources_csv_entry")
def test_named_and_category_export_lookups_return_same_public_entries(installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(installed_tree["site"])])
    named = list(env.get_exported_entries("distlib.demo", "plugin"))
    category = list(env.get_exported_entries("distlib.demo"))

    assert named == category
    assert named[0].prefix == "acme_widgets.core"


@pytest.mark.depends_on("test_get_distinfo_resource_reads_metadata_bytes", "test_metadata_mapping_exposes_common_fields")
def test_distinfo_resource_stream_can_feed_metadata_reader(installed_tree):
    from distlib.database import DistributionPath
    from distlib.metadata import Metadata

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    resource = dist.get_distinfo_resource("pydist.json")
    with resource.as_stream() as stream:
        metadata = Metadata(fileobj=stream, scheme="legacy")

    assert metadata.name == dist.name
    assert metadata.version == dist.version


@pytest.mark.depends_on("test_check_installed_files_accepts_matching_hashes_and_sizes", "test_list_installed_files_reads_record_rows")
def test_installed_file_integrity_detects_changed_file_through_record_projection(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    installed_tree["core_file"].write_text("def make_value():\n    return 'changed-widgets'\n", encoding="utf-8")
    mismatches = dist.check_installed_files()

    assert len(mismatches) == 1
    assert Path(mismatches[0][0]).name == "core.py"
    assert mismatches[0][1] in {"size", "hash"}


@pytest.mark.depends_on("test_manifest_findall_discovers_local_files", "test_list_installed_files_reads_record_rows")
def test_manifest_over_installed_tree_contains_distribution_record_files(installed_tree):
    from distlib.database import DistributionPath
    from distlib.manifest import Manifest

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    manifest = Manifest(str(installed_tree["site"]))
    manifest.findall()
    manifest_relpaths = {Path(path).relative_to(installed_tree["site"]).as_posix() for path in manifest.allfiles}
    record_relpaths = {row[0] for row in dist.list_installed_files()}

    assert record_relpaths <= manifest_relpaths | {"acme_widgets-1.2.3.dist-info/RECORD"}


@pytest.mark.depends_on("test_metadata_get_requirements_filters_extras", "test_distribution_matches_requirement_with_version_constraints")
def test_distribution_run_requires_projects_legacy_metadata_requirements(installed_tree):
    from distlib.database import DistributionPath

    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")

    assert dist.run_requires == {"base-lib (>=1.0)"}
    assert dist.matches_requirement("acme-alias (==1.2.3)")


@pytest.mark.depends_on("test_wheel_filename_and_tags_parse_from_filename", "test_distribution_path_discovers_installed_distribution")
def test_wheel_metadata_can_be_used_as_installed_distribution_metadata(installed_tree, wheel_file):
    from distlib.database import InstalledDistribution
    from distlib.wheel import Wheel

    wheel = Wheel(str(wheel_file))
    dist = InstalledDistribution(str(installed_tree["info"]), metadata=wheel.metadata)

    assert dist.name == "acme-wheel"
    assert dist.version == "2.0"
    assert dist.get_hash(b"payload").startswith("sha256=")


@pytest.mark.depends_on("test_manifest_include_adds_matching_top_level_file", "test_resource_finder_identifies_container_and_file")
def test_manifest_selected_files_can_be_read_through_resource_finder(manifest_tree):
    from distlib.manifest import Manifest
    from distlib.resources import finder_for_path

    manifest = Manifest(str(manifest_tree))
    manifest.findall()
    manifest.process_directive("include README.txt")
    resource = finder_for_path(str(manifest_tree)).find("README.txt")
    selected = next(iter(manifest.files))

    assert Path(selected).read_bytes() == resource.bytes


@pytest.mark.depends_on("test_metadata_write_json_round_trips_mapping", "test_wheel_get_hash_returns_named_digest")
def test_metadata_json_written_into_wheel_archive_round_trips_with_wheel_reader(tmp_path):
    from distlib.metadata import Metadata
    from distlib.wheel import Wheel

    metadata = Metadata(mapping={"metadata_version": "2.0", "name": "jsonwheel", "version": "1.0", "summary": "JW"})
    metadata_path = tmp_path / "metadata.json"
    metadata.write(path=str(metadata_path))
    wheel_path = tmp_path / "jsonwheel-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("jsonwheel/__init__.py", "")
        zf.writestr("jsonwheel-1.0.dist-info/WHEEL", "Wheel-Version: 1.1\nTag: py3-none-any\n\n")
        zf.write(metadata_path, "jsonwheel-1.0.dist-info/metadata.json")
        zf.writestr("jsonwheel-1.0.dist-info/RECORD", "jsonwheel-1.0.dist-info/RECORD,,\n")

    wheel = Wheel(str(wheel_path))

    assert wheel.metadata.dictionary == metadata.dictionary
    assert wheel.exists is True


@pytest.mark.depends_on("test_distribution_path_provides_distribution_finds_alias", "test_get_distribution_is_case_insensitive")
def test_distribution_path_get_distribution_and_provides_distribution_share_object(installed_tree):
    from distlib.database import DistributionPath

    env = DistributionPath([str(installed_tree["site"])])
    by_name = env.get_distribution("acme-widgets")
    by_alias = list(env.provides_distribution("acme-alias"))[0]

    assert by_name is by_alias
    assert by_name.path == str(installed_tree["info"])


@pytest.mark.depends_on("test_get_distinfo_resource_reads_metadata_bytes", "test_get_distinfo_file_returns_file_under_distribution_metadata")
def test_shared_locations_file_resource_and_property_agree_after_write(installed_tree, tmp_path):
    from distlib.database import DistributionPath

    locations = {}
    for key in ("prefix", "lib", "headers", "scripts", "data"):
        location = tmp_path / key
        location.mkdir()
        locations[key] = str(location)
    locations["namespace"] = [str(tmp_path / "namespace_one"), str(tmp_path / "namespace_two")]
    dist = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    dist.write_shared_locations(locations)
    reloaded = DistributionPath([str(installed_tree["site"])]).get_distribution("acme-widgets")
    resource = reloaded.get_distinfo_resource("SHARED")

    with resource.as_stream() as stream:
        shared_text = stream.read().decode("utf-8")

    assert reloaded.shared_locations["prefix"] == locations["prefix"]
    assert reloaded.shared_locations["namespace"] == locations["namespace"]
    assert f"scripts={locations['scripts']}" in shared_text.splitlines()


@pytest.mark.depends_on("test_resource_finder_identifies_container_and_file", "test_resource_finder_iterator_walks_nested_resources")
def test_zip_package_resource_stream_size_and_iterator_agree(tmp_path):
    from distlib.resources import finder

    archive = tmp_path / "zipstreamdemo.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("zipstreamdemo/__init__.py", "")
        zf.writestr("zipstreamdemo/assets/value.txt", "streamed zip data\n")
    sys.path.insert(0, str(archive))
    try:
        __import__("zipstreamdemo")
        resource_finder = finder("zipstreamdemo")
        resource = resource_finder.find("assets/value.txt")
        names = {item.name for item in resource_finder.iterator("")}
        with resource.as_stream() as stream:
            streamed = stream.read()
    finally:
        sys.path.remove(str(archive))
        sys.modules.pop("zipstreamdemo", None)

    assert "assets/value.txt" in names
    assert streamed == resource.bytes == b"streamed zip data\n"
    assert resource.size == len(streamed)


@pytest.mark.depends_on("test_metadata_write_json_round_trips_mapping", "test_wheel_filename_and_tags_parse_from_filename")
def test_json_wheel_metadata_can_seed_installed_distribution_requirements(installed_tree, tmp_path):
    from distlib.database import InstalledDistribution
    from distlib.metadata import Metadata
    from distlib.wheel import Wheel

    metadata = Metadata(
        mapping={
            "metadata_version": "2.0",
            "name": "jsonwheel-alias",
            "version": "1.0",
            "summary": "JSON wheel metadata",
            "run_requires": [{"requires": ["dep-json (>=2)"]}],
            "provides": ["jsonwheel-provider (1.0)"],
        }
    )
    metadata_path = tmp_path / "metadata.json"
    metadata.write(path=str(metadata_path))
    wheel_path = tmp_path / "jsonwheel_alias-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("jsonwheel_alias/__init__.py", "")
        zf.writestr("jsonwheel_alias-1.0.dist-info/WHEEL", "Wheel-Version: 1.1\nTag: py3-none-any\n\n")
        zf.write(metadata_path, "jsonwheel_alias-1.0.dist-info/metadata.json")
        zf.writestr("jsonwheel_alias-1.0.dist-info/RECORD", "jsonwheel_alias-1.0.dist-info/RECORD,,\n")

    dist = InstalledDistribution(str(installed_tree["info"]), metadata=Wheel(str(wheel_path)).metadata)

    assert dist.run_requires == {"dep-json (>=2)"}
    assert "jsonwheel-provider (1.0)" in dist.provides
    assert dist.matches_requirement("jsonwheel-alias (==1.0)")
