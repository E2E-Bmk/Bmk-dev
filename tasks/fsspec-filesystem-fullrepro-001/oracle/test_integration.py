# Spec2Repo oracle - integration tests for fsspec-filesystem-fullrepro-001
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


def test_memory_write_read_info_and_listing_views_agree():
    fs = MemoryFileSystem()
    with fs.open("/alpha/data.txt", "wb") as f:
        f.write(b"hello world")
    assert fs.cat("/alpha/data.txt") == b"hello world"
    assert fs.open("/alpha/data.txt", "rb").read() == b"hello world"
    assert fs.read_bytes("/alpha/data.txt") == b"hello world"
    assert fs.info("/alpha/data.txt")["size"] == 11
    assert fs.exists("/alpha/data.txt")
    assert fs.isfile("/alpha/data.txt")
    assert not fs.isdir("/alpha/data.txt")
    assert fs.ls("/alpha", detail=False) == ["/alpha/data.txt"]
    assert fs.ls("/alpha", detail=True)[0]["type"] == "file"


def test_memory_global_store_shared_between_instances():
    one = MemoryFileSystem()
    two = MemoryFileSystem()
    one.pipe("/shared/a.bin", b"one")
    assert two.cat("/shared/a.bin") == b"one"
    two.pipe("/shared/b.bin", b"two")
    assert sorted(one.find("/shared")) == ["/shared/a.bin", "/shared/b.bin"]


def test_memory_path_protocol_stripping_and_url_to_fs():
    fs, path = fsspec.core.url_to_fs("memory://bucket/file.txt")
    assert isinstance(fs, MemoryFileSystem)
    assert path == "/bucket/file.txt"
    fs.pipe(path, b"payload")
    assert fsspec.open("memory://bucket/file.txt", "rb").open().read() == b"payload"
    plain_fs, plain_path = fsspec.core.url_to_fs("memory://plain")
    assert isinstance(plain_fs, MemoryFileSystem)
    assert plain_path == "/plain"
    plain_fs.pipe(plain_path, b"plain")
    with fsspec.open("memory://plain", "rb") as f:
        assert f.read() == b"plain"


def test_memory_mkdir_parent_and_error_semantics():
    fs = MemoryFileSystem()
    fs.mkdir("/a/b/c")
    assert fs.isdir("/a")
    assert fs.isdir("/a/b")
    assert fs.isdir("/a/b/c")
    with pytest.raises(FileExistsError):
        fs.mkdir("/a/b/c")
    fs.pipe("/a/file", b"x")
    with pytest.raises(NotADirectoryError):
        fs.mkdir("/a/file/child")
    with pytest.raises(OSError):
        fs.rmdir("/a")
    fs.rmdir("/a/b/c")
    assert not fs.exists("/a/b/c")


def test_memory_touch_and_rm_update_all_views():
    fs = MemoryFileSystem()
    fs.touch("/tmp/empty")
    assert fs.exists("/tmp/empty")
    assert fs.cat("/tmp/empty") == b""
    fs.rm("/tmp/empty")
    assert not fs.exists("/tmp/empty")
    assert "/tmp/empty" not in fs.find("/tmp")
    with pytest.raises(FileNotFoundError):
        fs.cat("/tmp/empty")


def test_memory_find_walk_and_du_nested_tree():
    fs = MemoryFileSystem()
    fs.pipe("/tree/a.txt", b"a")
    fs.pipe("/tree/inner/b.txt", b"bb")
    fs.pipe("/tree/inner/deeper/c.txt", b"ccc")
    assert fs.find("/tree") == [
        "/tree/a.txt",
        "/tree/inner/b.txt",
        "/tree/inner/deeper/c.txt",
    ]
    assert fs.find("/tree", maxdepth=1) == ["/tree/a.txt"]
    assert fs.du("/tree") == 6
    assert fs.du("/tree", total=False, withdirs=True) == {
        "/tree": 0,
        "/tree/a.txt": 1,
        "/tree/inner": 0,
        "/tree/inner/b.txt": 2,
        "/tree/inner/deeper": 0,
        "/tree/inner/deeper/c.txt": 3,
    }
    assert list(fs.walk("/tree", maxdepth=1)) == [("/tree", ["inner"], ["a.txt"])]
    with pytest.raises(ValueError):
        list(fs.walk("/tree", maxdepth=0))


def test_memory_copy_move_and_aliases():
    fs = MemoryFileSystem()
    fs.pipe("/source.txt", b"abc")
    fs.cp("/source.txt", "/copy.txt")
    assert fs.cat("/copy.txt") == b"abc"
    fs.move("/copy.txt", "/moved.txt")
    assert not fs.exists("/copy.txt")
    assert fs.stat("/moved.txt")["size"] == 3
    fs.delete("/moved.txt")
    assert not fs.exists("/moved.txt")


def test_memory_recursive_get_put_round_trip(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "one.txt").write_bytes(b"one")
    (src / "sub").mkdir()
    (src / "sub" / "two.txt").write_bytes(b"two")
    fs = MemoryFileSystem()
    fs.put(str(src), "/remote", recursive=True)
    assert sorted(fs.find("/remote")) == ["/remote/one.txt", "/remote/sub/two.txt"]
    dst = tmp_path / "dst"
    fs.get("/remote", str(dst), recursive=True)
    assert (dst / "one.txt").read_bytes() == b"one"
    assert (dst / "sub" / "two.txt").read_bytes() == b"two"


def test_local_auto_mkdir_and_recursive_remove(tmp_path):
    fs = LocalFileSystem(auto_mkdir=True)
    target = tmp_path / "a" / "b" / "file.txt"
    fs.write_text(str(target), "hello", encoding="utf-8")
    assert target.read_text() == "hello"
    assert fs.cat(str(target)) == b"hello"
    assert fs.info(str(target))["type"] == "file"
    with pytest.raises(ValueError):
        fs.rm(str(tmp_path / "a"), recursive=False)
    fs.rm(str(tmp_path / "a"), recursive=True)
    assert not (tmp_path / "a").exists()


def test_local_copy_move_touch_and_listing(tmp_path):
    fs = LocalFileSystem(auto_mkdir=True)
    src = tmp_path / "src.txt"
    dst = tmp_path / "nested" / "dst.txt"
    src.write_bytes(b"payload")
    fs.copy(str(src), str(dst))
    assert fs.cat(str(dst)) == b"payload"
    moved = tmp_path / "moved.txt"
    fs.mv(str(dst), str(moved))
    assert fs.exists(str(moved))
    fs.touch(str(dst))
    assert fs.exists(str(dst))
    names = {Path(p).name for p in fs.ls(str(tmp_path), detail=False)}
    assert {"src.txt", "moved.txt", "nested"} <= names


def test_open_text_mode_and_compression(tmp_path):
    path = tmp_path / "data.txt.gz"
    with fsspec.open(str(path), "wt", compression="gzip", encoding="utf-8") as f:
        f.write("compressed text")
    with fsspec.open(str(path), "rt", compression="gzip", encoding="utf-8") as f:
        assert f.read() == "compressed text"


def test_open_files_read_glob_and_write_expansion(tmp_path):
    for name, content in {"a.txt": b"A", "b.txt": b"B"}.items():
        (tmp_path / name).write_bytes(content)
    ofs = fsspec.open_files(str(tmp_path / "*.txt"), "rb")
    with ofs as files:
        assert sorted(f.name for f in files) == sorted(str(p) for p in tmp_path.glob("*.txt"))
    out = fsspec.open_files(str(tmp_path / "part-*.bin"), "wb", num=3)
    with out as files:
        for index, f in enumerate(files):
            f.write(str(index).encode())
    assert sorted(p.name for p in tmp_path.glob("part-*.bin")) == [
        "part-0.bin",
        "part-1.bin",
        "part-2.bin",
    ]


def test_fsmap_basic_mutation_reflects_underlying_memory_fs():
    fs = MemoryFileSystem()
    mapper = FSMap("/dataset", fs, create=True)
    mapper["a"] = b"alpha"
    assert mapper["a"] == b"alpha"
    assert fs.cat("/dataset/a") == b"alpha"
    fs.pipe("/dataset/b", b"beta")
    assert mapper["b"] == b"beta"
    assert sorted(mapper) == ["a", "b"]
    assert "a" in mapper
    del mapper["a"]
    assert not fs.exists("/dataset/a")


def test_get_mapper_memory_and_pickle_round_trip():
    mapper = fsspec.get_mapper("memory:///store", create=True)
    mapper["key"] = b"value"
    restored = pickle.loads(pickle.dumps(mapper))
    assert restored["key"] == b"value"
    restored["other"] = b"two"
    assert mapper["other"] == b"two"


def test_dirfs_relative_view_reads_and_writes_under_root():
    base = MemoryFileSystem()
    base.pipe("/root/original.txt", b"old")
    view = DirFileSystem("/root", base)
    assert view.cat("original.txt") == b"old"
    view.pipe("nested/new.txt", b"new")
    assert base.cat("/root/nested/new.txt") == b"new"
    assert view.info("nested/new.txt")["name"] == "nested/new.txt"
    assert view.find("") == ["nested/new.txt", "original.txt"]


def test_dirfs_listing_detail_and_cat_list_are_relative():
    base = MemoryFileSystem()
    base.pipe("/root/a.txt", b"A")
    base.pipe("/root/b.txt", b"B")
    view = DirFileSystem("/root", base)
    assert view.ls("", detail=False) == ["a.txt", "b.txt"]
    assert {row["name"] for row in view.ls("", detail=True)} == {"a.txt", "b.txt"}
    assert view.cat(["a.txt", "b.txt"]) == {"a.txt": b"A", "b.txt": b"B"}


def test_dirfs_find_walk_glob_and_du_translate_paths():
    base = MemoryFileSystem()
    base.pipe("/root/one.txt", b"1")
    base.pipe("/root/sub/two.txt", b"22")
    view = DirFileSystem("/root", base)
    assert view.find("") == ["one.txt", "sub/two.txt"]
    assert list(view.walk("")) == [("", ["sub"], ["one.txt"]), ("sub", [], ["two.txt"])]
    assert view.glob("*.txt") == ["one.txt"]
    assert view.du("", total=False, withdirs=True) == {"": 0, "one.txt": 1, "sub": 0, "sub/two.txt": 2}


def test_url_to_fs_dir_chain_memory_relative_view():
    MemoryFileSystem().pipe("/inner/file", b"data")
    fs, root = fsspec.core.url_to_fs("dir::memory://inner")
    assert root == "/inner"
    assert isinstance(fs, DirFileSystem)
    assert fs.cat("file") == b"data"
    assert fs.ls("", detail=False) == ["file"]


def test_zip_write_close_and_read_members(tmp_path):
    archive = tmp_path / "sample.zip"
    zfs = ZipFileSystem(str(archive), mode="w")
    zfs.pipe_file("folder/a.txt", b"alpha")
    with zfs.open("folder/b.txt", "wb") as f:
        f.write(b"beta")
    zfs.close()
    readfs = ZipFileSystem(str(archive), mode="r")
    try:
        assert readfs.cat("folder/a.txt") == b"alpha"
        assert readfs.open("folder/b.txt", "rb").read() == b"beta"
        assert readfs.info("folder/a.txt")["size"] == 5
        assert readfs.isdir("folder")
        assert readfs.isfile("folder/a.txt")
    finally:
        readfs.close()


def test_zip_find_withdirs_maxdepth_and_exact_file(tmp_path):
    archive = tmp_path / "tree.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("a.txt", b"A")
        z.writestr("dir/b.txt", b"B")
        z.writestr("dir/deep/c.txt", b"C")
    zfs = ZipFileSystem(str(archive), mode="r")
    try:
        assert zfs.find("") == ["a.txt", "dir/b.txt", "dir/deep/c.txt"]
        assert zfs.find("", maxdepth=1) == ["a.txt"]
        assert "dir" in zfs.find("", withdirs=True)
        assert zfs.find("dir/b.txt") == ["dir/b.txt"]
    finally:
        zfs.close()


def test_zip_chained_open_reads_archive_member(tmp_path):
    archive = tmp_path / "chain.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("inside.txt", b"inside")
    with fsspec.open(f"zip://inside.txt::file://{archive}", "rb") as f:
        assert f.read() == b"inside"


def test_simplecache_chained_read_populates_local_cache(tmp_path):
    source = tmp_path / "source.txt"
    cache = tmp_path / "cache"
    source.write_bytes(b"cached bytes")
    of = fsspec.open(f"simplecache::file://{source}", simplecache={"cache_storage": str(cache), "same_names": True})
    with of as f:
        assert f.read() == b"cached bytes"
    assert (cache / "source.txt").read_bytes() == b"cached bytes"
    source.write_bytes(b"changed")
    with fsspec.open(f"simplecache::file://{source}", simplecache={"cache_storage": str(cache), "same_names": True}) as f:
        assert f.read() == b"cached bytes"


def test_open_local_simplecache_returns_cached_local_path(tmp_path):
    source = tmp_path / "data.txt"
    cache = tmp_path / "cache"
    source.write_bytes(b"local path")
    local_path = fsspec.open_local(
        f"simplecache::file://{source}",
        simplecache={"cache_storage": str(cache), "same_names": True},
    )
    assert Path(local_path).read_bytes() == b"local path"
    assert Path(local_path).parent == cache


def test_simplecache_write_uploads_to_target_on_close(tmp_path):
    target = tmp_path / "target.txt"
    cache = tmp_path / "cache"
    fs = SimpleCacheFileSystem(target_protocol="file", cache_storage=str(cache), same_names=True)
    with fs.open(str(target), "wb") as f:
        f.write(b"written")
    assert target.read_bytes() == b"written"


def test_simplecache_transaction_defers_target_visibility(tmp_path):
    target = tmp_path / "txn.txt"
    cache = tmp_path / "cache"
    fs = SimpleCacheFileSystem(target_protocol="file", cache_storage=str(cache), same_names=True)
    with fs.transaction:
        with fs.open(str(target), "wb") as f:
            f.write(b"deferred")
        assert not target.exists()
        assert fs.info(str(target))["size"] == 8
    assert target.read_bytes() == b"deferred"


def test_simplecache_transaction_rollback_discards_target_write(tmp_path):
    target = tmp_path / "rollback.txt"
    cache = tmp_path / "cache"
    fs = SimpleCacheFileSystem(target_protocol="file", cache_storage=str(cache), same_names=True)
    with pytest.raises(RuntimeError):
        with fs.transaction:
            with fs.open(str(target), "wb") as f:
                f.write(b"discard")
            raise RuntimeError("abort")
    assert not target.exists()


def test_wholefilecache_cat_populates_same_name_cache(tmp_path):
    source = tmp_path / "source.bin"
    cache = tmp_path / "cache"
    source.write_bytes(b"abcdef")
    fs = WholeFileCacheFileSystem(target_protocol="file", cache_storage=str(cache), same_names=True)
    assert fs.cat(str(source)) == b"abcdef"
    assert (cache / "source.bin").read_bytes() == b"abcdef"
    source.write_bytes(b"changed")
    assert fs.open(str(source), "rb").read() == b"abcdef"


def test_memory_transaction_commit_updates_all_views():
    fs = MemoryFileSystem()
    with fs.transaction:
        with fs.open("/txn/a.txt", "wb") as f:
            f.write(b"A")
        with fs.open("/txn/b.txt", "wb") as f:
            f.write(b"B")
        assert not MemoryFileSystem().exists("/txn/a.txt")
    assert fs.cat("/txn/a.txt") == b"A"
    assert fs.cat("/txn/b.txt") == b"B"
    mapper = fsspec.get_mapper("memory:///txn")
    assert dict(mapper.items()) == {"a.txt": b"A", "b.txt": b"B"}


def test_memory_transaction_exception_rolls_back_all_writes():
    fs = MemoryFileSystem()
    with pytest.raises(RuntimeError):
        with fs.transaction:
            with fs.open("/txn/a.txt", "wb") as f:
                f.write(b"A")
            with fs.open("/txn/b.txt", "wb") as f:
                f.write(b"B")
            raise RuntimeError("abort")
    assert not fs.exists("/txn/a.txt")
    assert not fs.exists("/txn/b.txt")


def test_remove_file_updates_mapper_and_listing_views():
    mapper = fsspec.get_mapper("memory:///remove", create=True)
    mapper["gone.txt"] = b"bye"
    fs = MemoryFileSystem()
    assert "/remove/gone.txt" in fs.find("/remove")
    fs.rm("/remove/gone.txt")
    assert "gone.txt" not in mapper
    assert fs.find("/remove") == []
    with pytest.raises(KeyError):
        mapper["gone.txt"]


def test_cross_view_url_token_open_and_mapper_agree():
    fs = MemoryFileSystem()
    fs.pipe("/agree/data.txt", b"same")
    url_fs, stripped = fsspec.core.url_to_fs("memory://agree/data.txt")
    token_fs, token, paths = fsspec.core.get_fs_token_paths("memory://agree/data.txt")
    mapper = fsspec.get_mapper("memory:///agree")
    assert isinstance(url_fs, MemoryFileSystem)
    assert isinstance(token_fs, MemoryFileSystem)
    assert stripped == paths[0] == "/agree/data.txt"
    assert isinstance(token, str)
    assert fsspec.open("memory://agree/data.txt", "rb").open().read() == mapper["data.txt"]


def test_copy_between_dirfs_view_and_base_memory_view():
    base = MemoryFileSystem()
    base.pipe("/root/a.txt", b"A")
    view = DirFileSystem("/root", base)
    view.copy("a.txt", "b.txt")
    assert base.cat("/root/b.txt") == b"A"
    base.pipe("/root/c.txt", b"C")
    assert view.cat("c.txt") == b"C"


def test_zip_member_written_then_opened_through_top_level_helper(tmp_path):
    archive = tmp_path / "workflow.zip"
    zfs = ZipFileSystem(str(archive), mode="w")
    try:
        zfs.pipe_file("member.txt", b"payload")
    finally:
        zfs.close()
    with fsspec.open(f"zip://member.txt::file://{archive}", "rb") as f:
        assert f.read() == b"payload"


def test_cache_read_matches_target_and_open_local_path(tmp_path):
    target = tmp_path / "target.bin"
    cache = tmp_path / "cache"
    target.write_bytes(b"target bytes")
    cached_url = f"simplecache::file://{target}"
    with fsspec.open(cached_url, simplecache={"cache_storage": str(cache), "same_names": True}) as f:
        assert f.read() == b"target bytes"
    local = fsspec.open_local(cached_url, simplecache={"cache_storage": str(cache), "same_names": True})
    assert Path(local).read_bytes() == target.read_bytes()


def test_open_files_context_closes_all_files(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"a")
    (tmp_path / "b.txt").write_bytes(b"b")
    ofs = fsspec.open_files(str(tmp_path / "*.txt"), "rb")
    with ofs as files:
        assert [f.read() for f in files] == [b"a", b"b"]
    assert all(f.closed for f in files)
