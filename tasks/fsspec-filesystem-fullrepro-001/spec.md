# fsspec Specification

## Product Overview

`fsspec` provides a uniform Python filesystem interface over byte-addressed storage. The covered package lets callers open files from URL strings, instantiate filesystem objects by protocol, manipulate hierarchical file namespaces, view a filesystem subtree as a mutable mapping, wrap a directory prefix as its own filesystem, read and write ZIP archives as filesystems, and cache files through a local whole-file cache.

The implementation must focus on user-visible behavior. Internal cache dictionaries, object identities, implementation helper names, and exact representation strings are not part of this contract.

## Scope

The covered behavior includes:

- the public package exports listed in `fsspec.__all__`
- protocol lookup and registration for local, memory, dir, zip, simplecache/filecache, and custom in-process implementations
- `AbstractFileSystem`-style synchronous filesystem operations for local and memory storage
- top-level helpers `filesystem`, `get_filesystem_class`, `available_protocols`, `register_implementation`, `open`, `open_files`, `open_local`, `url_to_fs`, `get_fs_token_paths`, and `get_mapper`
- the `FSMap` mutable mapping view
- `DirFileSystem` relative path wrapping
- `ZipFileSystem` archive reading and writing
- `SimpleCacheFileSystem` and `WholeFileCacheFileSystem` whole-file cache behavior over local or memory targets
- transactions for filesystems that expose the `transaction` context

Remote object stores, network servers, FUSE mounting, GUI widgets, asynchronous event-loop behavior, pyarrow wrappers, parquet helpers, GitHub/Gist/DBFS/WebHDFS/SMB/SFTP/FTP backends, and optional dependency import failures are not required.

## Installable Surface

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

## Public API

`filesystem(protocol, **storage_options)` returns a filesystem instance for the named protocol. `protocol=None` or a missing protocol must resolve to the local file protocol. For the covered protocols, `file` and `local` create `LocalFileSystem`, `memory` creates `MemoryFileSystem`, `dir` creates `DirFileSystem`, `zip` creates `ZipFileSystem`, `simplecache` creates `SimpleCacheFileSystem`, and `filecache` creates `WholeFileCacheFileSystem`.

`get_filesystem_class(protocol)` returns the class for a protocol and raises `ValueError` when the protocol is unknown. `register_implementation(name, cls, clobber=False, errtxt=None)` registers a protocol class or deferred class path. It must raise `ValueError` when registering a different class for an existing name without `clobber=True`.

`available_protocols()` returns a list containing the known protocol names.

`open(urlpath, mode="rb", compression=None, encoding=None, **kwargs)` returns an `OpenFile` object. The underlying file must not be opened until the `OpenFile` is entered or opened. Entering it must return a binary or text file object according to the requested mode, compression, and encoding.

`open_files(urlpath, mode="rb", num=1, name_function=None, **kwargs)` returns an `OpenFiles` list-like object. In read mode it must expand glob patterns to existing files. In write mode a single `*` in the target path must expand to `num` generated paths.

`open_local(urlpath, mode="rb", **kwargs)` returns a local filesystem path for local-file compatible targets. For the covered local and simplecache protocols, the returned path must point to readable local bytes.

`url_to_fs(url, **kwargs)` returns `(filesystem_instance, stripped_path)` using the protocol embedded in the URL. For `memory://a.txt` the stripped path is `/a.txt`. For local file URLs the stripped path is the local absolute path.

`get_fs_token_paths(urlpath, mode="rb", num=1, name_function=None, storage_options=None, protocol=None, expand=True)` returns `(fs, token, paths)`. `fs` is the filesystem instance, `token` is a deterministic string for that filesystem instance, and `paths` is a list of stripped paths. It must reject a non-empty sequence whose members resolve to different protocols.

`get_mapper(url="", check=False, create=False, missing_exceptions=None, alternate_root=None, **kwargs)` returns an `FSMap` rooted at the URL or alternate root.

`AbstractFileSystem` subclasses must expose these synchronous methods when supported by the backend:

```python
open(path, mode="rb", **kwargs)
ls(path, detail=True, **kwargs)
info(path, **kwargs)
exists(path)
isfile(path)
isdir(path)
mkdir(path, create_parents=True, **kwargs)
makedirs(path, exist_ok=False)
rmdir(path)
touch(path, truncate=True, **kwargs)
cat(path, recursive=False, on_error="raise", **kwargs)
cat_file(path, start=None, end=None, **kwargs)
pipe(path, value=None, **kwargs)
pipe_file(path, value, mode="overwrite", **kwargs)
copy(path1, path2, recursive=False, **kwargs)
cp(path1, path2, **kwargs)
mv(path1, path2, **kwargs)
move(path1, path2, **kwargs)
rm(path, recursive=False, maxdepth=None)
find(path, maxdepth=None, withdirs=False, detail=False, **kwargs)
walk(path, maxdepth=None, topdown=True, on_error="omit", **kwargs)
du(path, total=True, maxdepth=None, withdirs=False, **kwargs)
read_text(path, encoding=None, errors=None, newline=None)
write_text(path, value, encoding=None, errors=None, newline=None)
read_bytes(path, start=None, end=None, **kwargs)
write_bytes(path, value, **kwargs)
```

Aliases must call the same behavior: `cp` is `copy`, `move` and `rename` are `mv`, `delete` is `rm`, `stat` is `info`, `listdir` is `ls`, `mkdirs` is `makedirs`, `read_bytes` is `cat_file`, and `write_bytes` is `pipe_file`.

## Product State Model

The shared state is a hierarchy of byte-valued files and directory entries. The same facts are visible through these projections:

- filesystem methods such as `open`, `cat`, `ls`, `info`, `find`, `walk`, `du`, `rm`, and `copy`
- top-level URL helpers such as `fsspec.open`, `open_files`, `url_to_fs`, and `get_fs_token_paths`
- mapping views from `FSMap`
- prefix views from `DirFileSystem`
- archive views from `ZipFileSystem`
- local cache views from `SimpleCacheFileSystem`

A file write must create or replace bytes at a path. A directory listing must expose the same path as a file entry. Reading through any projection must return the bytes last committed through a compatible projection. Removing a path must make existence, listing, mapping membership, and direct reads agree that the path is gone.

## Memory and Local Filesystems

`MemoryFileSystem` stores bytes in a process-global in-memory namespace. Separate `MemoryFileSystem()` instances must see the same memory files. Memory paths may be written with or without a `memory://` prefix; the stored form must behave like absolute slash paths such as `/alpha/data.txt`.

`MemoryFileSystem.open(path, "wb")`, `pipe_file`, `pipe`, and `write_bytes` must write bytes. `open(path, "rb")`, `cat_file`, `cat`, and `read_bytes` must return bytes. Text modes through `open`, `read_text`, and `write_text` must encode and decode with the requested encoding.

`MemoryFileSystem.mkdir(path)` must create pseudo-directories. When `create_parents=True`, missing parents must be created. It must raise `FileExistsError` if the target file or directory already exists, and `NotADirectoryError` if a parent path is a file. `rmdir(path)` must remove an empty pseudo-directory, must not remove a non-empty directory, and must raise `FileNotFoundError` for a missing directory.

`MemoryFileSystem.ls(path, detail=False)` must return sorted child paths for a directory and a single path for an exact file. With `detail=True`, it must return dictionaries whose user-visible keys include `name`, `size`, and `type`, with type `"file"` or `"directory"`.

`MemoryFileSystem.info(path)` must return file or directory metadata. `exists`, `isfile`, and `isdir` must agree with `info` and `ls`.

`MemoryFileSystem.cat_file(path, start=None, end=None)` must slice bytes using Python slice semantics. It must raise `FileNotFoundError` for a missing file.

`MemoryFileSystem.rm(path, recursive=False, maxdepth=None)` must remove files and, when recursive expansion is requested, directories and their contents. It must raise for missing direct files unless expansion proves the path is an implied empty directory.

`LocalFileSystem` must expose the local OS filesystem. `auto_mkdir=True` must create parent directories before opening, touching, copying, or moving a written target. Local `ls`, `info`, `exists`, `isfile`, `isdir`, `cat`, `pipe`, `get`, `put`, `copy`, `mv`, `rm`, `touch`, and text helpers must reflect actual local files. `rm(directory, recursive=False)` must raise `ValueError`; recursive removal must remove a directory tree but must not delete the current working directory.

## Tree Operations

`walk(path, topdown=True)` returns `(root, dirs, files)` tuples. With `detail=False`, `dirs` and `files` contain entry names relative to each root. With `topdown=True`, a caller may mutate the yielded `dirs` list before iteration continues, and removed names must not be recursed into. With `topdown=False`, children are yielded before their parent.

`walk(path, maxdepth=N)` must limit recursion depth and must raise `ValueError` when `maxdepth < 1`. With `on_error="omit"`, a missing path produces no entries. With `on_error="raise"`, the underlying exception is raised. With a callable `on_error`, the callable receives the exception and iteration stops.

`find(path, detail=False, withdirs=False, maxdepth=None)` returns sorted paths below `path`. It must include files by default. It must include directories when `withdirs=True`. If `path` is an exact file, it must return that file. With `detail=True`, it returns a mapping from path to metadata.

`du(path, total=True)` returns total file bytes below `path`. With `total=False`, it returns per-path sizes. With `withdirs=True`, directory entries are included with size `0` when the backend has directory entries.

`copy`, `get`, and `put` must support file-to-file and recursive directory transfers where both source and target backend support the operation. Recursive transfers must preserve byte contents and relative child names.

## URL and OpenFile Behavior

Protocol parsing must use the portion before `://` as a protocol when the prefix has more than one character. Plain paths and single-letter Windows drive prefixes must be treated as local file paths, not remote protocols.

Chained URLs use `::` to wrap filesystems from right to left. For the covered behavior, `zip://inner.txt::file:///path/archive.zip` must open `inner.txt` from a ZIP archive stored in a local file, and `simplecache::file:///path/data.bin` must read a local target through a cache filesystem.

`OpenFile` objects from `open` must be lazy, pickleable when their filesystem and parameters are pickleable, and usable as context managers. Entering an `OpenFile` must open the target. Exiting the context must close it.

`OpenFiles` objects from `open_files` must preserve a list of `OpenFile` entries. Entering an `OpenFiles` context must open all entries and return open file objects; exiting must close them.

When a write URL contains exactly one `*`, `open_files(..., mode="wb", num=N)` must create N paths by replacing `*` with generated names that sort in partition order. More than one `*` in a write path must raise `ValueError`.

When a read URL contains glob metacharacters, `open_files` and `get_fs_token_paths` must expand it through the resolved filesystem. Paths without glob metacharacters must remain single paths.

## FSMap Mapping View

`FSMap(root, fs, check=False, create=False, missing_exceptions=None)` exposes files below `root` as a mutable mapping from keys to bytes. `get_mapper` must construct the filesystem from the URL and return this mapping.

`m[key] = value` must write bytes below the root, creating parent directories as needed. Values that expose the buffer protocol, including `bytearray`, `array.array`, and NumPy arrays when NumPy is installed, must be converted to bytes before storage.

`m[key]` must read bytes and raise `KeyError` for missing keys whose underlying exception is listed in `missing_exceptions`. `m.pop(key, default)` must return the default for a missing key. `key in m`, `len(m)`, iteration, `keys()`, `items()`, and `clear()` must reflect the current files below the root.

`getitems(keys, on_error="raise")` must return a dict for multiple keys. With `"raise"`, a missing key raises `KeyError`. With `"omit"`, missing keys are absent from the result. With `"return"`, every requested key appears, and missing keys map to `KeyError` instances.

`setitems(values_dict)` and `delitems(keys)` must perform multi-key writes and deletes. A mapper must be pickleable when the underlying filesystem is pickleable, and the unpickled mapper must access the same underlying files.

For a local filesystem, keys with and without a leading slash must refer to the same file below the mapper root. For the memory filesystem, `/a` and `a` are distinct mapping keys because memory paths are absolute slash paths.

## DirFileSystem Prefix View

`DirFileSystem(path, fs)` wraps another filesystem so every relative path is resolved under `path`. If `fs` is not supplied, `target_protocol` and `target_options` must create the wrapped filesystem.

All covered operations must translate input paths by joining them to the root before delegating to the wrapped filesystem, and must translate returned paths back to relative names. This includes `open`, `cat`, `pipe`, `ls`, `info`, `exists`, `isfile`, `isdir`, `find`, `walk`, `glob`, `du`, `mkdir`, `makedirs`, `touch`, `rm`, `copy`, `mv`, `get`, and `put`.

For a local filesystem target, paths that would escape the root through leading `..` segments must raise `ValueError`. Paths that stay inside the root, including `foo/../bar`, must be allowed. For non-local targets, `..` is a literal path segment and must not be rejected.

`url_to_fs("dir::memory://inner")` must create a `DirFileSystem` rooted at `/inner` over a memory filesystem, return `/inner` as the stripped root path, and expose relative names through operations on the returned filesystem.

## Zip Filesystem

`ZipFileSystem(fo, mode="r", target_protocol=None, target_options=None, compression=..., allowZip64=True, compresslevel=None)` exposes a ZIP archive as a filesystem. `fo` may be a local path, a URL opened through `fsspec.open`, or a file-like object.

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

## Representative Workflow

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

## Non-Goals

The implementation does not need to support remote credentials, real HTTP range requests, cloud object stores, pyarrow interoperability, parquet metadata, async coroutine execution, GUI controls, FUSE mounting, Dask worker filesystems, SMB/SFTP/FTP servers, WebHDFS, DBFS, GitHub/Gist APIs, external protocol packages, or exact internal metadata layouts.

Exact exception message wording, exact object representation strings, private attributes, helper modules under `fsspec.tests`, and hidden cache metadata file formats are not part of the public contract.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Invocation Protocol

There is no required console script for the covered task. `python -m fsspec` is not supported.

| invocation | expected behavior |
|---|---|
| `import fsspec` | succeeds and exposes the Installable Surface |
| `python -m fsspec` | not supported |

## Implementation Guidance

An implementation may choose any internal module layout while preserving the public filesystem behavior described above. Local-only backends are sufficient for this scope; network services and optional remote storage packages are not required.
