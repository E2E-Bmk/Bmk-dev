# Spec2Repo oracle - atomic tests for fsspec-filesystem-fullrepro-001
import os
import pickle
import posixpath
import zipfile
from pathlib import Path

import pytest

import fsspec
from fsspec.implementations.cached import SimpleCacheFileSystem, WholeFileCacheFileSystem
from fsspec.implementations.dirfs import DirFileSystem
from fsspec.implementations.local import LocalFileSystem
from fsspec.implementations.memory import MemoryFileSystem
from fsspec.implementations.zip import ZipFileSystem
from fsspec.mapping import FSMap


_MEMORY_CLEANUP_PATHS = [
    "/alpha",
    "/shared",
    "/bucket",
    "/plain",
    "/notes",
    "/a",
    "/b",
    "/slice.bin",
    "/tmp",
    "/tree",
    "/root//a",
    "/root",
    "/source.txt",
    "/copy.txt",
    "/moved.txt",
    "/remote",
    "/dataset",
    "/store",
    "/multi",
    "/ops",
    "/convert",
    "/inner",
    "/txn",
    "/remove",
    "/agree",
    "/exact",
    "/depth",
]


def _clean_memory_public_paths():
    fs = MemoryFileSystem()
    for path in sorted(_MEMORY_CLEANUP_PATHS, key=len, reverse=True):
        try:
            if fs.exists(path):
                fs.rm(path, recursive=True)
        except FileNotFoundError:
            pass


@pytest.fixture(autouse=True)
def clean_memory():
    _clean_memory_public_paths()
    yield
    _clean_memory_public_paths()


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
    assert required <= set(fsspec.__all__)
    protocols = set(fsspec.available_protocols())
    assert {"file", "local", "memory", "dir", "zip", "simplecache", "filecache"} <= protocols


def test_filesystem_factory_returns_expected_builtin_classes(tmp_path):
    assert isinstance(fsspec.filesystem("memory"), MemoryFileSystem)
    assert isinstance(fsspec.filesystem("file"), LocalFileSystem)
    assert isinstance(fsspec.filesystem("local"), LocalFileSystem)
    assert isinstance(fsspec.filesystem(None), LocalFileSystem)
    zpath = tmp_path / "archive.zip"
    zfs = ZipFileSystem(str(zpath), mode="w")
    zfs.close()
    assert fsspec.get_filesystem_class("memory") is MemoryFileSystem
    assert fsspec.get_filesystem_class("file") is LocalFileSystem


def test_register_custom_filesystem_and_clobber_behavior():
    class CustomMemory(MemoryFileSystem):
        protocol = "custom-memory-behavior"

    fsspec.register_implementation("custom-memory-behavior", CustomMemory, clobber=True)
    assert fsspec.get_filesystem_class("custom-memory-behavior") is CustomMemory
    assert isinstance(fsspec.filesystem("custom-memory-behavior"), CustomMemory)

    class OtherMemory(MemoryFileSystem):
        protocol = "custom-memory-behavior"

    with pytest.raises(ValueError):
        fsspec.register_implementation("custom-memory-behavior", OtherMemory)
    fsspec.register_implementation("custom-memory-behavior", OtherMemory, clobber=True)
    assert fsspec.get_filesystem_class("custom-memory-behavior") is OtherMemory


def test_unknown_protocol_raises_value_error():
    with pytest.raises(ValueError):
        fsspec.get_filesystem_class("definitely-not-a-protocol")
    with pytest.raises(ValueError):
        fsspec.filesystem("definitely-not-a-protocol")


def test_memory_text_helpers_round_trip_unicode():
    fs = MemoryFileSystem()
    fs.write_text("/notes/latin.txt", "cafe", encoding="utf-8")
    assert fs.read_text("/notes/latin.txt", encoding="utf-8") == "cafe"
    with fs.open("/notes/other.txt", "w", encoding="utf-8") as f:
        f.write("line one\nline two")
    assert fs.open("/notes/other.txt", "r", encoding="utf-8").read() == "line one\nline two"


def test_memory_cat_file_slicing_and_missing_error():
    fs = MemoryFileSystem()
    fs.pipe("/slice.bin", b"abcdef")
    assert fs.cat_file("/slice.bin", 1, 4) == b"bcd"
    assert fs.cat_file("/slice.bin", None, 3) == b"abc"
    assert fs.cat_file("/slice.bin", 3, None) == b"def"
    with pytest.raises(FileNotFoundError):
        fs.cat_file("/missing.bin")


def test_memory_pipe_multiple_and_cat_multiple():
    fs = MemoryFileSystem()
    data = {"/a": b"one", "/b": b"two"}
    fs.pipe(data)
    assert fs.cat(["/a", "/b"]) == data


def test_memory_walk_topdown_can_prune_directories():
    fs = MemoryFileSystem()
    fs.pipe("/root/keep/a.txt", b"a")
    fs.pipe("/root/drop/b.txt", b"b")
    seen = []
    for root, dirs, files in fs.walk("/root", topdown=True):
        seen.append((root, sorted(dirs), sorted(files)))
        if "drop" in dirs:
            dirs.remove("drop")
    assert seen == [
        ("/root", ["drop", "keep"], []),
        ("/root/keep", [], ["a.txt"]),
    ]


def test_memory_walk_error_modes():
    fs = MemoryFileSystem()
    assert list(fs.walk("/missing")) == []
    with pytest.raises(FileNotFoundError):
        list(fs.walk("/missing", on_error="raise"))
    calls = []
    assert list(fs.walk("/missing", on_error=calls.append)) == []
    assert isinstance(calls[0], FileNotFoundError)


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


def test_get_fs_token_paths_list_and_protocol_mismatch(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    fs, token, paths = fsspec.core.get_fs_token_paths([str(a), str(b)])
    assert isinstance(fs, LocalFileSystem)
    assert isinstance(token, str)
    assert paths == [str(a), str(b)]
    with pytest.raises(ValueError):
        fsspec.core.get_fs_token_paths([str(a), "memory://x"])


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


def test_fsmap_pop_clear_len_keys_items_and_defaults():
    mapper = fsspec.get_mapper("memory:///ops", create=True)
    assert mapper.pop("missing", b"default") == b"default"
    mapper["a"] = b"A"
    mapper["b"] = b"B"
    fs = MemoryFileSystem()
    assert fs.cat("/ops/a") == b"A"
    assert fs.cat("/ops/b") == b"B"
    assert len(mapper) == 2
    assert set(mapper.keys()) == {"a", "b"}
    assert dict(mapper.items()) == {"a": b"A", "b": b"B"}
    assert mapper.pop("a") == b"A"
    assert not fs.exists("/ops/a")
    mapper.clear()
    assert len(mapper) == 0
    assert fs.find("/ops") == []


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


def test_fsmap_memory_leading_slash_key_distinction():
    mapper = fsspec.get_mapper("memory:///root", create=True)
    mapper["a"] = b"plain"
    mapper["/a"] = b"slash"
    assert mapper["a"] == b"plain"
    assert mapper["/a"] == b"slash"
    fs = MemoryFileSystem()
    assert fs.cat("/root/a") == b"plain"
    assert fs.cat("/root//a") == b"slash"


def test_dirfs_local_rejects_paths_escaping_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    view = DirFileSystem(str(root), LocalFileSystem())
    for path in ["..", "../secret", "foo/../../secret", "/../secret"]:
        with pytest.raises(ValueError):
            view.exists(path)
        with pytest.raises(ValueError):
            view.pipe(path, b"blocked")
        with pytest.raises(ValueError):
            view.cat(path)
    view.mkdir("foo")
    view.pipe("foo/../bar", b"inside")
    assert view.cat("bar") == b"inside"
    assert not (tmp_path / "secret").exists()


def test_dirfs_non_local_keeps_dotdot_literal():
    view = DirFileSystem("/root", MemoryFileSystem())
    view.pipe("../literal.txt", b"ok")
    assert MemoryFileSystem().cat("/root/../literal.txt") == b"ok"


def test_zip_missing_member_and_invalid_mode_errors(tmp_path):
    archive = tmp_path / "errors.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("present.txt", b"present")
    with pytest.raises(ValueError):
        ZipFileSystem(str(archive), mode="x")
    zfs = ZipFileSystem(str(archive), mode="r")
    try:
        with pytest.raises(KeyError):
            zfs.open("missing.txt", "rb")
        with pytest.raises(OSError):
            zfs.open("new.txt", "wb")
    finally:
        zfs.close()


def test_find_exact_file_and_withdirs_child_behavior():
    fs = MemoryFileSystem()
    fs.pipe("/exact/file.txt", b"x")
    assert fs.find("/exact/file.txt") == ["/exact/file.txt"]
    withdirs = fs.find("/exact", withdirs=True)
    assert "/exact/file.txt" in withdirs
    assert all(posixpath.normpath(path).startswith("/exact") for path in withdirs)


def test_du_and_find_maxdepth_reject_zero():
    fs = MemoryFileSystem()
    fs.pipe("/depth/a.txt", b"a")
    with pytest.raises(ValueError):
        fs.find("/depth", maxdepth=0)
    with pytest.raises(ValueError):
        fs.du("/depth", maxdepth=0)


def test_openfile_pickle_reopens_read_location(tmp_path):
    path = tmp_path / "pickle.txt"
    path.write_bytes(b"abcdef")
    of = fsspec.open(str(path), "rb")
    restored = pickle.loads(pickle.dumps(of))
    with restored as f:
        assert f.read(3) == b"abc"
