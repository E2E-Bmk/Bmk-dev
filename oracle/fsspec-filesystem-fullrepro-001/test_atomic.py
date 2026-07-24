# Spec2Repo oracle - atomic tests for fsspec-filesystem-fullrepro-001
import os
import pickle
import posixpath
import uuid
import zipfile
from pathlib import Path

import pytest

import fsspec
from fsspec.core import OpenFile, OpenFiles, get_fs_token_paths, url_to_fs
from fsspec.mapping import FSMap, get_mapper
from fsspec.registry import get_filesystem_class, register_implementation


def test_top_level_public_exports_and_protocols():
    required = {
        "AbstractFileSystem",
        "FSTimeoutError",
        "FSMap",
        "filesystem",
        "register_implementation",
        "get_filesystem_class",
        "get_fs_token_paths",
        "get_mapper",
        "open",
        "open_files",
        "open_local",
        "registry",
        "caching",
        "Callback",
        "available_protocols",
        "available_compressions",
        "url_to_fs",
    }
    assert all(hasattr(fsspec, name) for name in required)
    protocols = set(fsspec.available_protocols())
    assert {"file", "local", "memory", "dir", "zip", "simplecache", "filecache"} <= protocols


def test_unknown_protocol_raises_value_error():
    with pytest.raises(ValueError):
        fsspec.get_filesystem_class("definitely-not-a-protocol")
    with pytest.raises(ValueError):
        fsspec.filesystem("definitely-not-a-protocol")


def test_openfile_is_lazy_context_manager(tmp_path):
    path = tmp_path / "lazy.txt"
    of = fsspec.open(str(path), "wb")
    assert not path.exists()
    with of as f:
        f.write(b"created")
    assert path.read_bytes() == b"created"
    with fsspec.open(str(path), "rb") as f:
        assert f.read() == b"created"


def test_open_files_write_rejects_multiple_stars(tmp_path):
    with pytest.raises(ValueError):
        fsspec.open_files(str(tmp_path / "*" / "*.bin"), "wb", num=2)


def test_fsmap_getitems_error_modes():
    mapper = fsspec.get_mapper("memory:///multi", create=True)
    mapper.setitems({"a": b"A", "b": b"B"})
    assert mapper.getitems(["a", "b"]) == {"a": b"A", "b": b"B"}
    assert mapper.getitems(["a", "missing"], on_error="omit") == {"a": b"A"}
    returned = mapper.getitems(["a", "missing"], on_error="return")
    assert returned["a"] == b"A"
    assert isinstance(returned["missing"], KeyError)
    with pytest.raises(KeyError):
        mapper.getitems(["missing"])


def test_fsmap_value_conversion_for_buffer_protocol():
    import array

    mapper = fsspec.get_mapper("memory:///convert", create=True)
    mapper["bytes"] = bytearray(b"abc")
    mapper["array"] = array.array("B", [1, 2, 3])
    assert mapper["bytes"] == b"abc"
    assert mapper["array"] == b"\x01\x02\x03"


def test_fsmap_local_leading_slash_key_equivalence(tmp_path):
    (tmp_path / "a").write_bytes(b"data")
    mapper = fsspec.get_mapper(f"file://{tmp_path}")
    assert mapper["a"] == b"data"
    assert mapper["/a"] == b"data"


def test_openfile_pickle_reopens_read_location(tmp_path):
    path = tmp_path / "pickle.txt"
    path.write_bytes(b"abcdef")
    of = fsspec.open(str(path), "rb")
    restored = pickle.loads(pickle.dumps(of))
    with restored as f:
        assert f.read(3) == b"abc"


def _protocol_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex}"


def test_registry_registers_class_for_factory_and_lookup():
    name = _protocol_name("registered")

    class RegisteredFileSystem(fsspec.AbstractFileSystem):
        protocol = name

    register_implementation(name, RegisteredFileSystem)

    assert get_filesystem_class(name) is RegisteredFileSystem
    assert isinstance(fsspec.filesystem(name), RegisteredFileSystem)


def test_registry_rejects_different_class_without_clobber():
    name = _protocol_name("conflict")

    class FirstFileSystem(fsspec.AbstractFileSystem):
        protocol = name

    class SecondFileSystem(fsspec.AbstractFileSystem):
        protocol = name

    register_implementation(name, FirstFileSystem)

    with pytest.raises(ValueError):
        register_implementation(name, SecondFileSystem)

    assert get_filesystem_class(name) is FirstFileSystem


def test_registry_clobber_replaces_registered_class():
    name = _protocol_name("clobber")

    class FirstFileSystem(fsspec.AbstractFileSystem):
        protocol = name

    class ReplacementFileSystem(fsspec.AbstractFileSystem):
        protocol = name

    register_implementation(name, FirstFileSystem)
    register_implementation(name, ReplacementFileSystem, clobber=True)

    assert get_filesystem_class(name) is ReplacementFileSystem
    assert isinstance(fsspec.filesystem(name), ReplacementFileSystem)


def test_url_to_fs_plain_path_preserves_local_absolute_path(tmp_path):
    path = tmp_path / "plain-local.bin"

    fs, stripped = url_to_fs(str(path))

    assert stripped == str(path)
    assert isinstance(fs, get_filesystem_class("file"))


def test_get_fs_token_paths_is_deterministic_for_single_url():
    _, first_token, first_paths = get_fs_token_paths(
        "memory:///token/single.bin"
    )
    _, second_token, second_paths = get_fs_token_paths(
        "memory:///token/single.bin"
    )

    assert isinstance(first_token, str) and first_token
    assert first_token == second_token
    assert first_paths == second_paths == ["/token/single.bin"]


def test_get_fs_token_paths_rejects_mixed_protocol_sequence(tmp_path):
    _, token, paths = get_fs_token_paths(["memory:///only-memory.bin"])
    assert isinstance(token, str) and token
    assert paths == ["/only-memory.bin"]

    with pytest.raises(ValueError):
        get_fs_token_paths(["memory:///one.bin", (tmp_path / "two.bin").as_uri()])


def test_open_returns_documented_openfile_type():
    opened = fsspec.open("memory:///surface/openfile.bin", "wb")

    assert isinstance(opened, OpenFile)


def test_open_files_returns_documented_list_and_entry_types():
    opened = fsspec.open_files(
        "memory:///surface/partition-*.bin", mode="wb", num=3
    )

    assert isinstance(opened, OpenFiles)
    assert len(opened) == 3
    assert all(isinstance(entry, OpenFile) for entry in opened)


def test_open_missing_file_raises_when_entered():
    opened = fsspec.open(
        f"memory:///missing/{uuid.uuid4().hex}.bin", mode="rb"
    )
    assert isinstance(opened, OpenFile)

    with pytest.raises(FileNotFoundError):
        with opened:
            pass


def test_fsmap_setitems_and_delitems_update_multiple_keys():
    mapper = get_mapper(f"memory:///batch-map/{uuid.uuid4().hex}", create=True)

    mapper.setitems({"a": b"A", "nested/b": b"B"})
    assert mapper["a"] == b"A"
    assert mapper["nested/b"] == b"B"

    mapper.delitems(["a", "nested/b"])
    assert "a" not in mapper
    assert "nested/b" not in mapper


def test_fsmap_iteration_items_len_and_clear_follow_files():
    mapper = get_mapper(f"memory:///view-map/{uuid.uuid4().hex}", create=True)
    mapper.setitems({"b": b"B", "a": b"A"})

    assert len(mapper) == 2
    assert set(mapper) == {"a", "b"}
    assert dict(mapper.items()) == {"a": b"A", "b": b"B"}

    mapper.clear()
    assert len(mapper) == 0
    assert list(mapper) == []


def test_memory_cat_file_uses_python_slice_semantics():
    fs = fsspec.filesystem("memory")
    path = f"/slice/{uuid.uuid4().hex}.bin"
    fs.pipe_file(path, b"abcdef")

    assert fs.cat_file(path, start=1, end=4) == b"bcd"
    assert fs.cat_file(path, start=-3) == b"def"


def test_walk_rejects_zero_maxdepth():
    fs = fsspec.filesystem("memory")

    with pytest.raises(ValueError):
        list(fs.walk("/", maxdepth=0))


def test_find_rejects_zero_maxdepth():
    fs = fsspec.filesystem("memory")

    with pytest.raises(ValueError):
        fs.find("/", maxdepth=0)


def test_du_rejects_zero_maxdepth():
    fs = fsspec.filesystem("memory")

    with pytest.raises(ValueError):
        fs.du("/", maxdepth=0)
