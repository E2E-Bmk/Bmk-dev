# afero Layered Filesystems Reimplementation Specification

## Product Overview

Reimplement the core of `github.com/spf13/afero`, a composable filesystem abstraction for Go. The module must provide an in-memory filesystem and the BasePath, read-only, copy-on-write, and cache-on-read wrappers. Correctness is defined by observable filesystem behavior, including open flags, shared file state, directory iteration, path confinement, overlay precedence, copy-up, caching, and error identity. No operating-system-backed, network, archive, or internal implementation is required.

The module path and package name must be `github.com/spf13/afero` and `afero`.

## Scope

The required surface is the in-memory filesystem and the BasePath, read-only, copy-on-write, and cache-on-read wrappers described below. Operating-system-backed, network, archive, and undocumented helper surfaces are excluded.

## Context and Orientation

`Fs` is the common filesystem interface and `File` is its open-handle interface. `MemMapFs` stores a hierarchy in memory. Multiple handles to one path share file contents and metadata but have independent seek and directory-enumeration offsets. Wrappers compose any `Fs`: `BasePathFs` confines names below a prefix, `ReadOnlyFs` rejects mutation, `CopyOnWriteFs` reads a base plus a writable overlay, and `CacheOnReadFs` lazily mirrors base data into a cache layer.

## Representative Workflows

Representative workflows include building a tree in `MemMapFs`, opening and editing files using ordinary `os` flags, exposing a subtree using `BasePathFs`, protecting any filesystem with `ReadOnlyFs`, editing a read-only base through `CopyOnWriteFs`, and reading remote-like base data through `CacheOnReadFs` with expiration.

## Behavior

### Interfaces, sentinels, and names

`File` must implement `io.Closer`, `io.Reader`, `io.ReaderAt`, `io.Seeker`, `io.Writer`, and `io.WriterAt`, plus `Name`, `Readdir`, `Readdirnames`, `Stat`, `Sync`, `Truncate`, and `WriteString`. `Fs` exposes `Create`, `Mkdir`, `MkdirAll`, `Open`, `OpenFile`, `Remove`, `RemoveAll`, `Rename`, `Stat`, `Name`, `Chmod`, `Chown`, and `Chtimes` with the signatures in the API catalog.

Export `ErrFileClosed`, `ErrOutOfRange`, `ErrTooLarge`, `ErrFileNotFound`, `ErrFileExists`, and `ErrDestinationExists`. Conditions corresponding to missing/existing paths must be recognizable by `os.IsNotExist`/`os.IsExist` and `errors.Is` where appropriate. Path errors must identify the relevant operation and path; tests do not require an exact message.

`NewMemMapFs`, `NewBasePathFs`, `NewReadOnlyFs`, `NewCopyOnWriteFs`, and `NewCacheOnReadFs` return usable `Fs` values. Their names are respectively `MemMapFS`, `BasePathFs`, `ReadOnlyFilter`, `CopyOnWriteFs`, and `CacheOnReadFs`.

### MemMapFs paths and directories

The memory filesystem starts with a root directory. Clean equivalent names consistently: repeated separators and `.` components resolve normally, and relative and rooted spellings which clean to the same location identify the same node. Parent traversal is cleaned using `filepath.Clean`; tests use portable relative paths and the platform separator.

`Mkdir` creates the named directory and any absent parent nodes needed by the in-memory tree; it fails when the target already exists. `MkdirAll` has the same recursive creation effect, succeeds when the directory already exists, and preserves existing nodes. Directory permission bits supplied at creation are observable through `Stat`; the directory bit is set.

`Stat` and handle `Stat` report base name, size, mode, modification time, and directory status. File size is the logical content length. `Chmod` replaces permission bits while preserving file type. `Chtimes` updates modification time to the supplied `mtime`; access time need not be reported. `Chown` must accept an existing path; ownership values are not inspected.

`Remove` unregisters and removes the named node and reports a missing path. For a directory it removes that directory entry even when descendants exist; callers use `RemoveAll` when recursive deletion is required. `RemoveAll` recursively removes a tree, succeeds for a missing target, and does not remove siblings. `Rename` moves a file or complete directory subtree, preserves contents and metadata, and rejects a missing source.

### Opening, contents, and handle state

`Create` is equivalent to opening with create, truncate, and read/write flags using mode `0666`. It creates a missing file, truncates an existing regular file, and fails when the parent is missing or the target is a directory.

`Open` opens read-only and fails for a missing path. `OpenFile` implements `os.O_RDONLY`, `O_WRONLY`, `O_RDWR`, `O_CREATE`, `O_EXCL`, and `O_TRUNC`. `O_EXCL|O_CREATE` fails for an existing path. Creation applies the requested permission bits. Truncation requires write access. `O_APPEND` is accepted, but the in-memory handle writes at its current seek offset rather than forcibly relocating every write to end. Writes through a read-only handle fail.

`Read` advances the handle offset and returns `io.EOF` at end; a zero-length read returns zero without advancing. `ReadAt` reads at its explicit offset without changing the seek offset and follows `io.ReaderAt` short-read rules. `Seek` supports start/current/end, permits seeking beyond end, rejects a negative resulting offset, and does not change contents. `Write` writes at the current offset and extends with zero bytes across a gap. `WriteAt` writes at its explicit offset without changing the seek offset and rejects a negative offset. `WriteString` matches `Write`.

`Truncate` resizes a writable file, discarding a suffix or extending with zeros, without changing the current seek offset. Negative sizes fail. `Sync` succeeds for an open memory file. After `Close`, data operations and a second `Close` fail with a closed-file error whose text equals `ErrFileClosed.Error()`; sentinel identity is not required because the public and memory implementation errors are equivalent by message.

Separate open handles have independent offsets. They observe shared writes, truncation, rename-preserved node identity, and metadata changes. Removing a path prevents new opens while an already-open regular-file handle remains a valid view of its node.

### Directory handles

Opening a directory returns a `File` whose `Readdir` and `Readdirnames` enumerate immediate children only, ordered lexicographically by name. For positive `n`, at most `n` results are returned and repeated calls continue from the handle's directory offset; exhaustion returns an empty result with `io.EOF`. For non-positive `n`, all remaining entries are returned and exhaustion is not required to return `io.EOF`. Each independently opened directory starts at the beginning. `Readdir` on a regular file fails.

Directory entries and `Stat` must agree on names, types, sizes, and modes. Mutating a directory while it is open must not panic; a subsequent newly opened directory sees the current tree.

### BasePathFs confinement

`NewBasePathFs(source, root)` exposes `root` as its virtual root. All filesystem operations translate names below that root, and opened files report virtual rather than backing paths from `Name`. Root spellings `.` and the separator address the configured root. Nested BasePath wrappers compose correctly.

Absolute paths, cleaned `..` escapes, and names whose resolved path is outside the configured root must fail and must not mutate the source. Renames require both paths to remain confined. Regular errors remain compatible with `os.IsNotExist` and `os.IsExist`. Creating, reading, statting, renaming, removing, chmodding, and time changes through the wrapper affect the corresponding backing node only.

### ReadOnlyFs

The read-only wrapper forwards `Open`, read-only `OpenFile`, `Stat`, directory enumeration, and reads. Every mutating filesystem method returns a permission error: `Create`, `Mkdir`, `MkdirAll`, `Remove`, `RemoveAll`, `Rename`, `Chmod`, `Chown`, and `Chtimes`. `OpenFile` rejects any flag set containing write-only, read/write, append, create, truncate, or exclusive-create intent. Files returned by read-only open operations must reject `Write`, `WriteAt`, `WriteString`, and `Truncate`, even if the underlying file implementation would permit them.

### CopyOnWriteFs

The copy-on-write wrapper reads overlay nodes before base nodes. An overlay file or directory shadows the same base path. When both layers contain a directory, opening it yields the union of their immediate entries, ordered by name with duplicates emitted once and the overlay entry winning.

Opening a base-only regular file for reading must not copy it. Opening it with any mutating flag copies its current content and mode into the overlay first, then applies the requested open semantics. Subsequent writes, truncation, chmod, and time changes affect only the overlay; the base remains byte-for-byte and metadata unchanged. Creating a new path writes only to the overlay and creates overlay parent directories when the corresponding base parents are directories.

Removing or renaming a base-only node must fail because this wrapper has no whiteout representation; the failure may classify as permission denied or not-exist depending on the overlay's missing-path error. Removing an overlay node reveals a same-named base node again. Renaming an overlay node affects only the overlay. `MkdirAll` succeeds for existing base directories and creates missing paths in the overlay. Failed operations must not partly modify either layer.

### CacheOnReadFs

The cache-on-read wrapper has an authoritative base and cache layer. A read-only `Open` or read-only `OpenFile` of a base regular file absent from the cache populates the cache with its metadata and bytes, then serves a result consistent with the base. `Stat` reports the authoritative base entry on a cache miss without being required to populate it. Opening a base-only directory may serve it directly; once both layers contain it, enumeration is a union. Populating a nested file creates cache parents. Cache population does not modify the base.

With a positive cache duration, a cached entry younger than the duration is used. Once stale, a subsequent read refreshes it from the base, including changed contents and modification time. With duration zero, an existing cached entry is used without time-based expiration. Tests use modification times separated from the duration and do not depend on scheduling races.

Mutating operations (`Create`, write-capable `OpenFile`, `Mkdir`, `MkdirAll`, `Remove`, `RemoveAll`, `Rename`, `Chmod`, `Chown`, `Chtimes`) are applied so that later wrapper reads and the authoritative base agree. A successful write must not leave an older cache value visible. Directory reads merge/refresh consistently without duplicate names.

## Contract

## State Model

Path lookup, `Stat`, and directory enumeration must describe one coherent tree. File handles have independent cursor state but share node state. Wrapper composition must preserve the contracts of the wrapped `Fs` while adding confinement, immutability, overlay, or cache rules. No wrapper may mutate a lower layer during a read unless cache population is its documented purpose.

## Error Semantics

Errors may be wrapped in `*os.PathError`, but sentinel identity and `os.IsNotExist`, `os.IsExist`, and `os.IsPermission` classification must remain useful. Callback-free APIs must return errors rather than panic for ordinary invalid paths, flags, offsets, closed handles, and type mismatches.

## Cross-View Invariants

- Path lookup, `Stat`, and directory enumeration must agree on the same visible tree.
- Independent handles must observe shared content and metadata while retaining independent cursor positions.
- Wrapper reads and writes must agree with the documented authoritative, overlay, or cache layer after each successful operation.
- A failed wrapper operation must leave every underlying layer unchanged.

### Concurrency

`MemMapFs` must safely support concurrent operations on distinct paths and concurrent independent handles to the same regular file. Tests coordinate goroutines deterministically and do not require an ordering between simultaneous writes to the same byte range. Wrapper values must be safe when their underlying filesystems are safe. A single handle is not required to support simultaneous cursor operations.

## Public Interface

The installable module and import path are `github.com/spf13/afero`; all required declarations below belong to package `afero`.

```go
type File interface {
    io.Closer; io.Reader; io.ReaderAt; io.Seeker; io.Writer; io.WriterAt
    Name() string
    Readdir(count int) ([]os.FileInfo, error)
    Readdirnames(n int) ([]string, error)
    Stat() (os.FileInfo, error)
    Sync() error
    Truncate(size int64) error
    WriteString(s string) (int, error)
}

type Fs interface {
    Create(string) (File, error)
    Mkdir(string, os.FileMode) error
    MkdirAll(string, os.FileMode) error
    Open(string) (File, error)
    OpenFile(string, int, os.FileMode) (File, error)
    Remove(string) error
    RemoveAll(string) error
    Rename(string, string) error
    Stat(string) (os.FileInfo, error)
    Name() string
    Chmod(string, os.FileMode) error
    Chown(string, int, int) error
    Chtimes(string, time.Time, time.Time) error
}

func NewMemMapFs() Fs
func NewBasePathFs(source Fs, path string) Fs
func NewReadOnlyFs(source Fs) Fs
func NewCopyOnWriteFs(base Fs, layer Fs) Fs
func NewCacheOnReadFs(base Fs, layer Fs, cacheTime time.Duration) Fs
```

The exported concrete wrapper types `MemMapFs`, `BasePathFs`, `ReadOnlyFs`, `CopyOnWriteFs`, and `CacheOnReadFs` must exist. Implementation-private tree, inode, cache, locking, and union-directory representation is unconstrained.

## Non-Goals

Acceptance covers only the interfaces, constructors, sentinels, concrete types, and behaviors stated here. It excludes `OsFs`, HTTP/IOFS adapters, regexp filters, symlink extensions, glob/walk/util helpers, archive/network filesystems, exact error strings, inode numbers, ownership reporting, nanosecond timing precision, OS-specific separators beyond `filepath` behavior, and performance matching.

Implementations may use any in-memory representation and any synchronization design. They must build offline with no external dependencies.

## Environment

The submission must be a Go module with module path `github.com/spf13/afero`. It must build and test offline on Linux with the configured Go toolchain and may use only the Go standard library.

## Assessment Notes

Acceptance checks exercise only the documented interfaces, constructors, sentinels, concrete types, and observable filesystem behavior. They do not inspect private storage, locking, inode, or cache representations, nor exact error strings where only error classification is specified.
