# fsspec Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`fsspec` provides a uniform Python filesystem interface over byte-addressed storage. The covered package lets callers open files from URL strings, instantiate filesystem objects by protocol, manipulate hierarchical file namespaces, view a filesystem subtree as a mutable mapping, wrap a directory prefix as its own filesystem, read and write ZIP archives as filesystems, and cache files through a local whole-file cache.

The implementation must focus on user-visible behavior. Internal cache dictionaries, object identities, implementation helper names, and exact representation strings are not part of this contract.

## Non-Goals

- This specification does not require Remote credentials, real HTTP range requests, cloud object stores, pyarrow interoperability, parquet metadata, async coroutine execution, GUI controls, FUSE mounting, Dask worker filesystems, SMB/SFTP/FTP servers, WebHDFS, DBFS, hosted repository APIs, external protocol packages, or exact internal metadata layouts.

- This specification does not require Exact exception message wording, exact object representation strings, private attributes, helper modules under test packages, or hidden cache metadata file formats.

## Representative Workflows

```python
import fsspec

fs = fsspec.filesystem("memory")
fs.pipe("/project/raw/a.txt", b"alpha")
fs.pipe("/project/raw/b.txt", b"beta")

mapper = fsspec.get_mapper("memory:///project/raw")
assert mapper["a.txt"] == b"alpha"
mapper["c.txt"] = b"gamma"

subfs, root = fsspec.core.url_to_fs("dir::memory:///project/raw")
assert root == "/project/raw"
assert sorted(subfs.find("")) == ["a.txt", "b.txt", "c.txt"]

with fsspec.open("memory:///project/raw/a.txt", "rb") as f:
    assert f.read() == b"alpha"

fs.rm("/project/raw/b.txt")
assert "b.txt" not in mapper
```

Files written via the filesystem `pipe` method are immediately visible through the `FSMap` mapping view, the `DirFileSystem` prefix view, and the `open` URL helper. Removing a file through the filesystem makes it disappear from the mapper's key membership, confirming cross-view consistency.

```python
import fsspec
from fsspec.implementations.zip import ZipFileSystem
import tempfile, os

with tempfile.TemporaryDirectory() as tmp:
    archive_path = os.path.join(tmp, "data.zip")
    with ZipFileSystem(archive_path, mode="w") as zfs:
        zfs.pipe_file("docs/readme.txt", b"hello world")
        zfs.pipe_file("docs/notes.txt", b"some notes")

    with ZipFileSystem(archive_path, mode="r") as zfs:
        assert zfs.cat("docs/readme.txt") == b"hello world"
        assert sorted(zfs.find("")) == ["docs/notes.txt", "docs/readme.txt"]
        assert zfs.info("docs/readme.txt")["type"] == "file"
        assert zfs.isdir("docs")
```

The `ZipFileSystem` writes archive members in write mode. After closing and reopening in read mode, `cat` returns exact bytes, `find` lists all members sorted, `info` reports the correct file type, and `isdir` recognizes implied directories.

## Memory and Local Filesystems

The memory and local filesystem implementations provide the foundational storage backends for in-process and OS-level file operations.

**Memory filesystem scope.** `MemoryFileSystem` stores bytes in a process-global in-memory namespace. Separate `MemoryFileSystem()` instances must see the same memory files. Memory paths may be written with or without a `memory://` prefix; the stored form must behave like absolute slash paths such as `/alpha/data.txt`.

**Read and write operations.** `open(path, "wb")`, `pipe_file`, `pipe`, and `write_bytes` must write bytes. `open(path, "rb")`, `cat_file`, `cat`, and `read_bytes` must return bytes. Text modes through `open`, `read_text`, and `write_text` must encode and decode with the requested encoding.

**Directory operations.** `mkdir(path)` must create pseudo-directories. When `create_parents` is true, missing parents must be created. It must raise `FileExistsError` if the target file or directory already exists, and `NotADirectoryError` if a parent path is a file. `rmdir(path)` must remove an empty pseudo-directory, must not remove a non-empty directory, and must raise `FileNotFoundError` for a missing directory.

**Listing and metadata.** `ls(path, detail=False)` must return sorted child paths for a directory and a single path for an exact file. With `detail` set to true, it must return dictionaries whose user-visible keys include `name`, `size`, and `type`, with type `"file"` or `"directory"`. `info(path)` must return file or directory metadata. `exists`, `isfile`, and `isdir` must agree with `info` and `ls`.

**Byte slicing.** `cat_file(path)` returns file contents. When `start` or `end` is provided, it must slice bytes using Python slice semantics. It must raise `FileNotFoundError` for a missing file.

**Removal.** `rm(path, recursive=False)` must remove files and, when `recursive` is true, directories and their contents. It must raise for missing direct files unless expansion proves the path is an implied empty directory. Memory filesystem also supports `touch`, `copy` (aliased as `cp`), `move` (aliased as `mv`), `delete`, and `stat` operations.

**Local filesystem.** `LocalFileSystem` must expose the local OS filesystem. When `auto_mkdir` is set to true, parent directories must be created before opening, touching, copying, or moving a written target. Local `ls`, `info`, `exists`, `isfile`, `isdir`, `cat`, `pipe`, `get`, `put`, `copy`, `mv`, `rm`, `touch`, and text helpers must reflect actual local files. `rm(directory, recursive=False)` must raise `ValueError`; recursive removal must remove a directory tree but must not delete the current working directory.

## Tree Operations

Tree operations traverse filesystem hierarchies to list, search, copy, and measure directory contents.

**Walking.** `walk(path)` returns `(root, dirs, files)` tuples. When `topdown` is true (the default), parents are yielded before children. With `detail` set to false, `dirs` and `files` contain entry names relative to each root. When `topdown` is true, a caller may mutate the yielded `dirs` list before iteration continues, and removed names must not be recursed into. When `topdown` is false, children are yielded before their parent.

When `maxdepth` is provided, `walk` must limit recursion depth and must raise `ValueError` when `maxdepth` is less than `1`. When `on_error` is `"omit"`, a missing path produces no entries. When `on_error` is `"raise"`, the underlying exception is raised. When `on_error` is a callable, the callable receives the exception and iteration stops.

**Finding.** `find(path)` returns sorted paths below `path`. It must include files by default. When `withdirs` is true, it must include directories. If `path` is an exact file, it must return that file. When `detail` is true, it returns a mapping from path to metadata. When `maxdepth` is provided, it must limit returned depth and must raise `ValueError` when `maxdepth` is less than `1`.

**Disk usage.** `du(path)` returns total file bytes below `path`. When `total` is false, it returns per-path sizes. When `withdirs` is true, directory entries are included with size `0` when the backend has directory entries. When `maxdepth` is `0`, it must raise `ValueError`.

**Transfers.** `copy`, `get`, and `put` must support file-to-file and recursive directory transfers where both source and target backend support the operation. Recursive transfers must preserve byte contents and relative child names.

## URL and OpenFile Behavior

URL parsing and OpenFile objects bridge between string-based file references and filesystem operations, supporting protocol chaining and lazy file access.

**Protocol parsing.** Protocol parsing must use the portion before `://` as a protocol when the prefix has more than one character. Plain paths and single-letter Windows drive prefixes must be treated as local file paths, not remote protocols.

Chained URLs use `::` to wrap filesystems from right to left. For the covered behavior, `zip://inner.txt::file:///path/archive.zip` must open `inner.txt` from a ZIP archive stored in a local file, and `simplecache::file:///path/data.bin` must read a local target through a cache filesystem.

`OpenFile` objects from `open` must be lazy, pickleable when their filesystem and parameters are pickleable, and usable as context managers. Entering an `OpenFile` must open the target. Exiting the context must close it.

`OpenFiles` objects from `open_files` must preserve a list of `OpenFile` entries. Entering an `OpenFiles` context must open all entries and return open file objects; exiting must close them.

When a write URL contains exactly one `*`, `open_files(..., mode="wb", num=N)` must create N paths by replacing `*` with generated names that sort in partition order. More than one `*` in a write path must raise `ValueError`.

When a read URL contains glob metacharacters, `open_files` and `get_fs_token_paths` must expand it through the resolved filesystem. Paths without glob metacharacters must remain single paths.

## FSMap Mapping View

The FSMap mapping view exposes a filesystem subtree as a mutable Python mapping from string keys to byte values.

**Construction.** `FSMap` accepts a `root` path and an `fs` filesystem instance, with options for `check`, `create`, and `missing_exceptions`. It exposes files below the root as a mutable mapping from keys to bytes. `get_mapper` must construct the filesystem from the URL and return this mapping.

**Write operations.** `m[key] = value` must write bytes below the root, creating parent directories as needed. Values that expose the buffer protocol, including `bytearray`, `array.array`, and NumPy arrays when NumPy is installed, must be converted to bytes before storage.

**Read operations.** `m[key]` must read bytes and raise `KeyError` for missing keys whose underlying exception is listed in `missing_exceptions`. `m.pop(key, default)` must return the default for a missing key. `key in m`, `len(m)`, iteration, `keys()`, `items()`, and `clear()` must reflect the current files below the root.

**Batch operations.** `getitems(keys)` must return a dict for multiple keys. When `on_error` is `"raise"`, a missing key raises `KeyError`. When `on_error` is `"omit"`, missing keys are absent from the result. When `on_error` is `"return"`, every requested key appears, and missing keys map to `KeyError` instances. `setitems(values_dict)` and `delitems(keys)` must perform multi-key writes and deletes.

**Serialization.** A mapper must be pickleable when the underlying filesystem is pickleable, and the unpickled mapper must access the same underlying files.

For a local filesystem, keys with and without a leading slash must refer to the same file below the mapper root. For the memory filesystem, `/a` and `a` are distinct mapping keys because memory paths are absolute slash paths.

## DirFileSystem Prefix View

`DirFileSystem(path, fs)` wraps another filesystem so every relative path is resolved under `path`. If `fs` is not supplied, `target_protocol` and `target_options` must create the wrapped filesystem.

All covered operations must translate input paths by joining them to the root before delegating to the wrapped filesystem, and must translate returned paths back to relative names. This includes `open`, `cat`, `pipe`, `ls`, `info`, `exists`, `isfile`, `isdir`, `find`, `walk`, `glob`, `du`, `mkdir`, `makedirs`, `touch`, `rm`, `copy`, `mv`, `get`, and `put`.

For a local filesystem target, paths that would escape the root through leading `..` segments must raise `ValueError`. Paths that stay inside the root, including `foo/../bar`, must be allowed. For non-local targets, `..` is a literal path segment and must not be rejected.

`url_to_fs("dir::memory://inner")` must create a `DirFileSystem` rooted at `/inner` over a memory filesystem, return `/inner` as the stripped root path, and expose relative names through operations on the returned filesystem.

## Zip Filesystem

The Zip filesystem exposes a ZIP archive as a read-only or write-only filesystem interface.

**Construction.** `ZipFileSystem` accepts a file reference through `fo`, which may be a local path, a URL opened through `fsspec.open`, or a file-like object. The `mode` argument controls whether the archive is opened for reading, writing, or appending. Additional options include `target_protocol`, `target_options`, `compression`, `allowZip64`, and `compresslevel`.

In read mode, `ls`, `find`, `info`, `exists`, `isfile`, `isdir`, `open`, `cat`, and `cat_file` must expose archive members using relative slash paths without a leading slash. Directory entries implied by member paths must appear as directories. Opening a missing archive member for reading must raise `KeyError`.

In write or append mode, `pipe_file` and `open(path, "wb")` must create archive members. Closing the filesystem must commit the ZIP file. A ZIP filesystem opened in read mode must not allow writing, and a ZIP filesystem opened in write/append mode must not allow reading existing entries through the same instance.

`find(path, maxdepth=N)` must limit returned member paths by relative depth. `find(path, withdirs=True)` must include directory entries. If `path` names an exact file, `find(path)` must return only that file.

## Cache Filesystems

`SimpleCacheFileSystem` and `WholeFileCacheFileSystem` wrap a target filesystem and store whole file bytes in a local cache directory. They may be created directly with `target_protocol` and `target_options`, or through chained URLs such as `simplecache::file:///tmp/data.bin`.

Reading a file through a simple cache must copy the target bytes into the cache on first access, then return the same bytes through the local cached copy on later reads. With `same_names=True`, cached file names use the original basename. Without it, cache filenames may be hashed.

`SimpleCacheFileSystem` must support writes. A normal write must upload the local temporary file to the target when the file is closed. During a transaction, writes must be visible through that cache filesystem's `ls` and `info` projections before commit, but the target filesystem must not expose them until the transaction completes. If the transaction exits with an exception, the target must remain unchanged.

`open_local` for a simplecache-wrapped URL must return a local path to the cached file after ensuring the target has been cached.

## Transactions

Every filesystem instance exposes `.transaction`. Entering the transaction context must defer writes for filesystems that support transactional writes. Exiting normally must commit all deferred files. Exiting with an exception must discard them.

For `MemoryFileSystem`, files written inside a transaction must not be visible through a fresh filesystem read before the transaction commits. After normal exit, they must be readable by path. After exception exit, they must not exist.

For `SimpleCacheFileSystem`, transaction writes must upload to the wrapped target only on normal exit.

## State Model

The shared state is a hierarchy of byte-valued files and directory entries. The same facts are visible through these projections:

- filesystem methods such as `open`, `cat`, `ls`, `info`, `find`, `walk`, `du`, `rm`, and `copy`
- top-level URL helpers such as `fsspec.open`, `open_files`, `url_to_fs`, and `get_fs_token_paths`
- mapping views from `FSMap`
- prefix views from `DirFileSystem`
- archive views from `ZipFileSystem`
- local cache views from `SimpleCacheFileSystem`

A file write must create or replace bytes at a path. A directory listing must expose the same path as a file entry. Reading through any projection must return the bytes last committed through a compatible projection. Removing a path must make existence, listing, mapping membership, and direct reads agree that the path is gone.

## Error Semantics

Unknown protocols must raise `ValueError`.

Registering a conflicting protocol without `clobber=True` must raise `ValueError`.

Opening or reading a missing file must raise `FileNotFoundError`.

Creating an existing file or directory with an exclusive mode or mkdir-style operation must raise `FileExistsError`.

Removing a non-empty directory with `rmdir` must raise `OSError`.

Removing a local directory with `recursive=False` must raise `ValueError`.

`walk(maxdepth=0)`, `find(maxdepth=0)`, or `du(maxdepth=0)` must raise `ValueError`.

`FSMap` missing-key reads must raise `KeyError` unless a default or non-raising `getitems` mode is used.

`DirFileSystem` over a local filesystem must raise `ValueError` for relative paths that escape the root through `..`.

`ZipFileSystem` must raise `ValueError` for modes other than `r`, `w`, or `a`. It must raise `OSError` when an operation tries to read and write through the same ZIP instance in an unsupported direction.

## Cross-View Invariants

- Bytes written through `fs.open(path, "wb")` must be returned by `fs.cat(path)`, `fs.open(path, "rb").read()`, `fs.read_bytes(path)`, and `fs.info(path)["size"]`.
- A file created through `FSMap` must appear in the underlying filesystem's `find`, `ls`, `cat`, and `exists` projections.
- A file written through a filesystem method below a mapper root must appear as a mapping key with the same bytes.
- A file visible through `DirFileSystem` must map to the wrapped filesystem path under the configured root, and mutations through either view must be visible through the other view.
- A ZIP member written through `ZipFileSystem` must be readable through a chained `fsspec.open("zip://member::file://archive.zip")` URL after the archive is closed.
- A file read through `simplecache` must return the same bytes as the wrapped target and must remain available through `open_local`.
- A transaction commit must make all deferred writes visible together through `exists`, `cat`, `ls`, `find`, and mapping views.
- A transaction rollback must leave all projections reporting that the deferred files do not exist.
- `url_to_fs`, `get_fs_token_paths`, and `open` must agree on the filesystem protocol and stripped path for the same URL.
- Removing a file through any covered deletion API must make direct reads fail and must remove the path from listings and mapper membership.

## Public Interface

### Import Surface

The package must be importable as `fsspec`. These top-level names must be available:

```python
AbstractFileSystem
FSTimeoutError
FSMap
filesystem
register_implementation
get_filesystem_class
get_fs_token_paths
get_mapper
open
open_files
open_local
registry
caching
Callback
available_protocols
available_compressions
url_to_fs
```

Covered filesystem implementations are selected through the public protocol factory:

```python
import fsspec

memory_fs = fsspec.filesystem("memory")
local_fs = fsspec.filesystem("file")
directory_view = fsspec.filesystem("dir", path="/root", fs=memory_fs)
zip_fs = fsspec.filesystem("zip", fo="archive.zip")
cached_fs = fsspec.filesystem("simplecache", target_protocol="file")

from fsspec.core import OpenFile, OpenFiles, get_fs_token_paths, url_to_fs
from fsspec.mapping import FSMap, get_mapper
from fsspec.registry import register_implementation, get_filesystem_class, available_protocols
```

The internal module path used to implement a protocol is not part of this contract.

`python -m fsspec` is not supported.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| `filesystem` | function | Construct a filesystem instance for a protocol name |
| `get_filesystem_class` | function | Return the class registered for a protocol |
| `register_implementation` | function | Register a protocol implementation class |
| `available_protocols` | function | List known protocol names |
| `open` | function | Return a lazy `OpenFile` handle for one URL |
| `open_files` | function | Return an `OpenFiles` collection for one or many URLs |
| `open_local` | function | Return a local filesystem path for a readable URL |
| `url_to_fs` | function | Parse a URL into a filesystem instance and stripped path |
| `get_fs_token_paths` | function | Resolve a URL into filesystem, token, and path list |
| `get_mapper` | function | Return an `FSMap` view for a URL |
| `AbstractFileSystem` | class | Base synchronous filesystem interface |
| `FSMap` | class | Mutable mapping view over a filesystem subtree |
| `OpenFile` | class | Lazy single-file opener |
| `OpenFiles` | class | Lazy multi-file opener collection |
| `Callback` | class | Progress callback helper |
| `FSTimeoutError` | exception | Raised when filesystem operations time out |
| `registry` | module | Protocol registration namespace |
| `caching` | module | Cache filesystem helpers namespace |
| `available_compressions` | function | List supported compression names |

### CLI Entry Points

There is no required console script for the covered task. `python -m fsspec` is not supported.

| invocation | expected behavior |
|---|---|
| `import fsspec` | succeeds and exposes the Installable Surface |
| `python -m fsspec` | not supported |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

An implementation may choose any internal module layout while preserving the public filesystem behavior described above. Local-only backends are sufficient for this scope; network services and optional remote storage packages are not required.
