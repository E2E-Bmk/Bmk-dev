# memfs Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`memfs` is an in-memory file-system library for Node.js. It implements the familiar `fs`-style API — synchronous calls, error-first callbacks, promises, file descriptors, and streams — entirely over volatile process memory, with no disk access. A `Volume` owns a tree of nodes (files, directories, symbolic links) together with an open-file-descriptor table; every API surface is a projection of that single tree.

The library serves testing, sandboxing, and virtual-file-tree use cases: a caller seeds a volume from a plain JSON object mapping paths to file contents, mutates it through ordinary file operations, and snapshots it back to JSON at any point. Multiple independent volumes coexist in one process, and a default volume backs a ready-made `fs`-shaped export for drop-in use.

The installable package name is `memfs`. It is a pure library with no CLI.

## Non-Goals

- This specification does not require watching APIs to be functional beyond existence: `watch`, `watchFile`, `unwatchFile`, `StatWatcher`, and `FSWatcher` are not covered.
- This specification does not require pattern matching (`glob`, `globSync`), directory handles (`opendir`, `Dir`), file-system statistics (`statfs`), or `openAsBlob`.
- This specification does not require detection of circular symbolic-link chains; resolving a self-referential chain has undefined behavior.
- This specification does not define ownership enforcement: `chown`-family calls must be accepted but user/group tracking is not covered.
- This specification does not require vectorized I/O (`readv`, `writev`) or `lchmod`/`lchown`/`lutimes` semantics beyond call acceptance.
- This specification does not define persistence: volumes live in process memory only and vanish with the process.
- This specification does not require mirroring any real operating system's quirks; behavior is defined solely by this document.

## Representative Workflows

**Seed, mutate, snapshot.** A test fixture materializes from JSON, is edited through normal file calls, and is captured back as JSON:

```ts
import { memfs } from 'memfs';

const { fs, vol } = memfs({
  '/app/config.json': '{"debug":false}',
  '/app/src/index.ts': 'export {};',
});

fs.mkdirSync('/app/logs');
fs.writeFileSync('/app/logs/run.log', 'started\n');
fs.appendFileSync('/app/logs/run.log', 'done\n');

vol.toJSON();
// {
//   '/app/config.json': '{"debug":false}',
//   '/app/src/index.ts': 'export {};',
//   '/app/logs/run.log': 'started\ndone\n',
// }
```

**Isolated volumes and low-level access.** Independent volumes never share state; descriptors and streams operate on the same tree as the path calls:

```ts
import { Volume, createFsFromVolume } from 'memfs';

const vol = Volume.fromJSON({ '/data/report.txt': 'draft' });
const fs = createFsFromVolume(vol);

const fd = fs.openSync('/data/report.txt', 'r+');
fs.writeSync(fd, 'FINAL', 0);
fs.closeSync(fd);

await fs.promises.readFile('/data/report.txt', 'utf8'); // 'FINAL'

const other = Volume.fromJSON({});
other.existsSync('/data/report.txt'); // false — volumes are isolated
```

## Volumes And Snapshots

A volume is the unit of state: one node tree plus one descriptor table, exposed through several equivalent construction paths and a JSON snapshot projection.

**Construction.** `new Volume()` creates an empty volume containing only the root directory `/`. The static method `Volume.fromJSON(json)` creates a volume and populates it from a flat object whose keys are paths and whose values are file contents (strings or `Buffer`s); intermediate directories are created automatically. WHEN a value in the JSON object is `null`, THEN the key is created as an empty directory instead of a file. The instance method `vol.fromJSON(json, cwd)` populates an existing volume, resolving relative keys against the `cwd` argument. `Volume.fromNestedJSON(json)` accepts nested objects: an inner object is a directory whose own keys are entries, and string leaves are file contents.

**Snapshot.** `vol.toJSON()` returns a flat object mapping absolute file paths to their contents as strings. Directories that contain any entry are represented implicitly through their children's paths; an empty directory appears explicitly with value `null`. Symbolic links do not appear in the snapshot — a path reachable only through a symbolic link is reported under its resolved target path only, and hard-linked names each appear as an independent key carrying the same content. `vol.toJSON(path)` restricts the snapshot to paths under the given subtree. Restoring a snapshot with `fromJSON` therefore produces plain independent files: link relationships are not round-tripped.

**Reset.** `vol.reset()` discards every node and open descriptor, returning the volume to the empty state: after a reset, `toJSON()` returns an empty object and previously existing paths no longer exist.

**Ready-made instances.** The package exports `vol`, a default `Volume` instance, and `fs`, an `fs`-shaped object bound to that default volume. Every file-operation method described in this document is also available as a top-level named export of the package, bound to the default volume, so `readFileSync` imported from the package reads from `vol`. The helper `memfs(json)` creates a fresh pair: it returns an object with an `fs` property (an `fs`-shaped object) and a `vol` property (the underlying new `Volume`), seeded from the optional JSON argument. `createFsFromVolume(volume)` returns an `fs`-shaped object bound to an existing volume; mutations made through the returned object and through the volume itself observe each other.

**Isolation.** Distinct `Volume` instances share nothing. WHEN a path is created on one volume, THEN every other volume, including the default `vol`, must report it absent.

## Files And Directories

Path-based operations mutate and query the tree. Every operation exists in synchronous form (`opSync`), error-first callback form (`op`), and promise form (`vol.promises.op` / `fs.promises.op`); this section describes semantics once, using the synchronous names.

**Writing and reading files.** `writeFileSync(path, data)` creates or replaces a file; `data` is a string or `Buffer`. An options argument accepts `encoding` (applied when `data` is a string; `"base64"` and `"hex"` decode the string to bytes) and `flag` (default `"w"`; the flag `"a"` appends instead of replacing). `readFileSync(path)` returns a `Buffer`; passing an encoding — as a string or as an options object with `encoding` — returns a decoded string. `appendFileSync(path, data)` appends to an existing file and creates the file when it does not exist. If the parent directory of the target path does not exist, then `writeFileSync` must throw an error with code `ENOENT`; if a non-terminal component of the path is an existing file, then the error code must be `ENOTDIR`; if the path names an existing directory, then reading it with `readFileSync` must throw with code `EISDIR`.

**Creating directories.** `mkdirSync(path)` creates a single directory. WHEN called without `recursive` and the parent does not exist, THEN it must throw with code `ENOENT`; WHEN the path already exists, THEN it must throw with code `EEXIST`. WHEN called with the option `recursive: true`, THEN all missing ancestors are created, an existing target is not an error, and the return value is the full target path as a string when anything was created, or `undefined` when the target already existed. An optional `mode` sets the permission bits of the created directory. `mkdtempSync(prefix)` creates a directory whose name is the prefix followed by exactly six random alphanumeric characters and returns its path.

**Listing directories.** `readdirSync(path)` returns the entry names of a directory sorted lexicographically. With `withFileTypes: true` it returns `Dirent` objects exposing `name`, the parent directory path via both `parentPath` and `path`, and the kind predicates `isFile()`, `isDirectory()`, and `isSymbolicLink()`. With `recursive: true` it returns paths of all descendants relative to the listed directory (child entries of a subdirectory appear as `sub/name`). If the path names a file, then `readdirSync` must throw with code `ENOTDIR`; if it names a missing path, the code must be `ENOENT`.

**Removing.** `unlinkSync(path)` removes a file or symbolic-link name. If the path names a directory, then `unlinkSync` must throw with code `EPERM`. `rmdirSync(path)` removes an empty directory; if the directory has entries, then it must throw with code `ENOTEMPTY`, and if the path names a file, the code must be `ENOTDIR`. `rmSync(path, options)` is the general remover: WHEN given `recursive: true`, THEN it removes a directory and its whole subtree; WHEN the path is missing, THEN it must throw with code `ENOENT` unless `force: true` is given, in which case a missing path is silently ignored; WHEN the path names a directory and `recursive` was not given, THEN it must throw with code `ERR_FS_EISDIR`.

**Renaming and copying.** `renameSync(oldPath, newPath)` moves a file or an entire directory subtree; an existing file at the destination is replaced, and node identity is preserved — a file's `ino` value is the same before and after the move. If the source is missing, or the destination's parent directory is missing, then `renameSync` must throw with code `ENOENT`. `copyFileSync(src, dest)` copies file content; the copy is a new independent node created with the default file mode (the source's permission bits are not carried over). WHEN the constant `constants.COPYFILE_EXCL` is passed as the third argument and the destination exists, THEN it must throw with code `EEXIST`. `cpSync(src, dest, options)` copies files, and with `recursive: true` whole trees; WHEN the source is a directory and `recursive` was not given, THEN it must throw with code `EISDIR`; by default existing destination files are overwritten, and WHEN `force: false, errorOnExist: true` is given and a destination file exists, THEN it must throw with code `EEXIST`. A recursive copy is deep: later edits to the source subtree must not affect the copy.

**Truncating.** `truncateSync(path, length)` cuts the file to `length` bytes; WHEN `length` exceeds the current size, THEN the file is extended and the new tail bytes are zero.

**Existence.** `existsSync(path)` returns `true` or `false` and never throws. `accessSync(path)` returns `undefined` for an accessible path and must throw with code `ENOENT` when the path is missing (permission-related failures are described under Metadata And Permissions).

## Metadata And Permissions

Every node carries metadata — kind, size, permission bits, timestamps, link count, and an identity number — projected through stat calls and enforced by access checks.

**Stats objects.** `statSync(path)` returns a `Stats` object with kind predicates `isFile()`, `isDirectory()`, and `isSymbolicLink()`, byte `size`, permission-carrying `mode`, hard-link count `nlink`, node identity `ino`, and timestamps exposed both as `Date` objects (`atime`, `mtime`, `ctime`) and as numeric milliseconds (`atimeMs`, `mtimeMs`, `ctimeMs`). `statSync` follows symbolic links; `lstatSync` reports the link node itself. `fstatSync(fd)` reports on an open descriptor's file. WHEN the option `bigint: true` is given, THEN numeric fields are `BigInt` values. WHEN the option `throwIfNoEntry: false` is given and the path is missing, THEN `statSync` returns `undefined` instead of throwing; without it a missing path must raise an error with code `ENOENT`. A file's `size` reflects its current content length across all mutation paths (writes, appends, truncations, descriptor writes).

**Permission bits.** A file created by content-writing calls receives mode `0o666` and a directory created by `mkdirSync` receives `0o777`, before any explicit `mode` option; `mkdirSync` and `openSync` accept a `mode` argument that sets the created node's permission bits exactly. `chmodSync(path, mode)` replaces the permission bits, observable as `stats.mode & 0o777`.

**Access checks.** `accessSync(path, mode)` verifies the requested capability using the constants `F_OK` (existence, the default), `R_OK` (read), `W_OK` (write), and `X_OK` (execute), which are exported both at the top level and on `constants`. If the node's permission bits do not grant a requested capability — for example `W_OK` on a mode-`0o444` file or `R_OK` on a mode-`0o000` file — then `accessSync` must throw with code `EACCES`. Read enforcement extends to content reads: reading a file whose mode denies reading must throw with code `EACCES`.

**Timestamps.** `utimesSync(path, atime, mtime)` sets access and modification times; each argument is a `Date` or a number of seconds since the epoch, and the stored value is observable through `atimeMs`/`mtimeMs` in milliseconds. `futimesSync(fd, atime, mtime)` does the same through a descriptor.

## Links And Path Resolution

Two link kinds project one node under several names: symbolic links store a target path resolved at traversal time, hard links bind an additional directory name to an existing file node.

**Symbolic links.** `symlinkSync(target, path)` creates a link node at `path` whose stored target is returned verbatim by `readlinkSync(path)`. Path resolution follows link nodes both at the final component and at intermediate components, so a link to a directory makes `linkpath/child` reach the target's child. `statSync` reports the resolved target while `lstatSync` reports the link node (its `isSymbolicLink()` is `true`). `realpathSync(path)` returns the fully resolved absolute path with every link component replaced, following chains of links transitively. If `readlinkSync` is called on a node that is not a symbolic link, then it must throw with code `EINVAL`.

**Dangling links.** A link's target path need not exist when the link is created. While the target is absent, `existsSync` on the link returns `false`, and reading or resolving through it must raise an error with code `ENOENT`, though `lstatSync` still reports the link node. WHEN a file is later created at the target path, THEN the link becomes traversable and reads return the new file's content.

**Removing links.** `unlinkSync` on a symbolic-link name removes only the link node; the target is untouched.

**Hard links.** `linkSync(existingPath, newPath)` adds a second name for an existing file node: both names report the same `ino` and content, `nlink` on the shared node increments to reflect the number of names, and a write through either name is visible through the other. WHEN one name is removed with `unlinkSync`, THEN the remaining name still reaches the content and `nlink` decrements. If `newPath` already exists, then `linkSync` must throw with code `EEXIST`; if `existingPath` is missing, the code must be `ENOENT`.

## File Descriptors And Low-Level I/O

Descriptors give byte-level access to file nodes through an open-file table that tracks a per-descriptor position.

**Opening.** `openSync(path, flags, mode)` returns a numeric descriptor; concurrently open descriptors have distinct numbers. The flag strings define creation and truncation behavior: `"r"` and `"r+"` require the file to exist and must throw with code `ENOENT` when it does not; `"w"` creates or truncates to empty; `"wx"` creates and must throw with code `EEXIST` when the path already exists; `"a"` opens for appending, creating when missing, and every write lands at the end; `"w+"` and `"r+"` allow both reading and writing. The optional `mode` sets the permission bits when the call creates the file.

**Reading and writing.** `readSync(fd, buffer, offset, length, position)` copies up to `length` bytes into `buffer` starting at `offset`, returns the number of bytes read, and interprets `position` as the absolute byte position to read from; WHEN `position` is `null`, THEN the read starts at the descriptor's current position and advances it, so consecutive `null`-position reads walk the file sequentially. `writeSync(fd, data)` writes a string or buffer at the current position and returns the number of bytes written; `writeSync(fd, data, position)` writes at the given absolute position, overwriting in place without shifting later bytes. `ftruncateSync(fd, length)` truncates the open file. Descriptor operations and path operations observe each other immediately: bytes written through a descriptor are visible to `readFileSync` before the descriptor is closed.

**Closing.** `closeSync(fd)` releases the descriptor. If a released or never-issued descriptor number is passed to `readSync`, `writeSync`, or `closeSync`, then the call must throw with code `EBADF`.

## Callbacks, Promises, And Streams

The same tree is reachable through error-first callbacks, a promise API, file handles, and byte streams; results and error codes match the synchronous projection.

**Callback form.** Every operation named in this document has a callback form named without the `Sync` suffix — `readFile(path, options, callback)`, `writeFile`, `mkdir`, `readdir`, `stat`, `unlink`, `rename`, and so on — that delivers `(error, result)` where exactly one of the two is meaningful. WHEN the operation succeeds, THEN `error` is `null` and `result` carries the value the synchronous form would have returned; WHEN it fails, THEN `error` carries the same `code` the synchronous form would have thrown. The `exists(path, callback)` operation is the single exception to the error-first shape: its callback receives only a boolean.

**Promise form.** `vol.promises` (and the `promises` property of any `fs`-shaped object) exposes promise-returning versions of the same operations. A rejected promise carries the same error `code` as the synchronous throw. `promises.open(path, flags)` resolves to a `FileHandle` owning a numeric `fd`; the handle's methods `readFile(options)`, `writeFile(data)`, `write(buffer)`, `stat()`, and `close()` operate on the open file, and `write(buffer)` resolves to an object with `bytesWritten` and `buffer` properties.

**Streams.** `createWriteStream(path)` returns a writable stream; data written through it is stored in the file once the stream finishes. `createReadStream(path)` returns a readable stream over the file's bytes honoring an `encoding` option, and piping a read stream into a write stream copies content between paths. WHEN a read stream is created for a missing path, THEN the stream emits an `error` event whose error carries code `ENOENT`.

## State Model

The core state is a per-volume superblock with two tables:

- **Node tree** — the root directory and its descendants. Each node is a file (byte content), a directory (named entries), or a symbolic link (stored target path). Every node carries mode bits, timestamps, an identity number `ino`, and a name count `nlink`.
- **Descriptor table** — open descriptors, each binding a numeric id to a node and a current byte position.

Public projections of that state:

1. **Path API** — synchronous, callback, and promise operations addressing nodes by path, with symbolic-link resolution applied per component.
2. **Snapshot** — `toJSON()` flattening files (and empty directories) into a path-to-content object; `fromJSON`/`fromNestedJSON` materializing trees from objects.
3. **Metadata** — `Stats` from `statSync`/`lstatSync`/`fstatSync`, `Dirent` entries from `readdirSync`, permission enforcement through `accessSync`.
4. **Descriptors** — numeric fds and `FileHandle`s with positional byte I/O.
5. **Streams** — readable and writable byte streams over file nodes.

All projections read and write the same tables: a mutation made through any one is immediately observable through every other.

## Error Semantics

Failed operations throw (or deliver via callback/rejection) an `Error` whose `code` property identifies the condition; the `path` property carries the offending path when one applies. Message text is not part of this contract.

| Condition | code |
|---|---|
| Path or ancestor does not exist (read, stat, open `"r"`/`"r+"`, unlink, rename source or destination parent, mkdir parent, access, rm without force, link source, realpath or read through a dangling link) | `ENOENT` |
| Creating a node where one exists (mkdir without recursive, open `"wx"`, `linkSync` destination, `COPYFILE_EXCL` destination, `cpSync` with `errorOnExist`) | `EEXIST` |
| Reading a directory as a file | `EISDIR` |
| `rmSync` on a directory without `recursive: true` | `ERR_FS_EISDIR` |
| `cpSync` on a directory without `recursive: true` | `EISDIR` |
| Directory operation on a file (`readdirSync`, `rmdirSync`), or a non-terminal path component is a file | `ENOTDIR` |
| `unlinkSync` on a directory | `EPERM` |
| `rmdirSync` on a non-empty directory | `ENOTEMPTY` |
| Permission bits deny a requested or implied capability | `EACCES` |
| Descriptor number not currently open | `EBADF` |
| `readlinkSync` on a non-link node | `EINVAL` |

## Cross-View Invariants

1. For every file path reported by `toJSON()`, `readFileSync` at that path must return exactly the reported content, and every file reachable by path traversal that is not shadowed by link indirection must appear in `toJSON()` under its resolved path.
2. A byte sequence written through any projection — `writeFileSync`, a descriptor `writeSync`, a `FileHandle`, or a write stream — must be returned identically by every reading projection: `readFileSync`, positional `readSync`, `promises.readFile`, a read stream, and the file's `size` in every `Stats` view must equal the byte length of that sequence.
3. The entry names returned by `readdirSync(path)` must equal the `name` fields of `readdirSync(path, { withFileTypes: true })` in the same order, and each `Dirent` kind predicate must agree with the `Stats` predicates obtained by `lstatSync` on the joined path.
4. Hard-linked names must agree in every metadata view — same `ino`, same `size`, same content through every read projection — and `nlink` must equal the number of directory names currently bound to the node.
5. After `renameSync`, every projection must observe the move atomically: the old path is absent from path reads, `toJSON()`, and directory listings, while the new path reports the same content, the same `ino`, and the same descendant structure as before.
6. A volume restored via `Volume.fromJSON(vol.toJSON())` must satisfy: reading any snapshot path on the restored volume returns the same content as on the original, and paths reachable on the original only through symbolic links are either materialized as plain files (hard links) or absent (symbolic links) on the restored volume.
7. The synchronous, callback, and promise forms of the same failing operation must report the same error `code`.

## Public Interface

### Import Surface

```ts
import {
  memfs, Volume, vol, fs, createFsFromVolume,
  Stats, Dirent, constants,
  F_OK, R_OK, W_OK, X_OK,
} from 'memfs';
```

Every file-operation method of the `fs`-shaped surface (for example `readFileSync`, `writeFile`, `mkdirSync`) is also importable as a top-level named export bound to the default volume `vol`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `memfs` | function | Creates a fresh `{ fs, vol }` pair, optionally seeded from a JSON object |
| `Volume` | class | The state owner: node tree plus descriptor table; `fromJSON`/`fromNestedJSON` constructors, `toJSON`, `reset`, `promises`, and all file operations as methods |
| `vol` | object | Default `Volume` instance backing the top-level exports |
| `fs` | object | `fs`-shaped API bound to `vol` |
| `createFsFromVolume` | function | Wraps an existing `Volume` in an `fs`-shaped object |
| `Stats` | class | Metadata projection returned by `statSync`, `lstatSync`, `fstatSync` |
| `Dirent` | class | Directory-entry projection returned by `readdirSync` with `withFileTypes` |
| `constants` | object | Numeric flag constants including `F_OK`, `R_OK`, `W_OK`, `X_OK`, `COPYFILE_EXCL` |
| `F_OK` / `R_OK` / `W_OK` / `X_OK` | constants | Access-check capability masks |

### CLI Entry Points

There is no console script for this package. Programmatic use is through TypeScript/JavaScript imports.

## Appendix A: Environment

The working environment runs Node.js 22 on Linux without network access. The test toolchain is `vitest` with TypeScript; tests import the package under test by its package name `memfs`. No other third-party runtime packages are available or needed.

The project must declare its packaging metadata in a standard `package.json` at the project root, exposing the package's public entry point under the name `memfs`, so the test suite can resolve `import { ... } from 'memfs'`.

## Appendix B: Assessment Notes

Assessment exercises the public surface described in this document across several dimensions: volume construction and snapshot agreement; path operations and their error codes; metadata, permissions, and timestamps; symbolic- and hard-link semantics; descriptor-level positional I/O; the callback, promise, handle, and stream projections; and cross-projection consistency of one mutated tree. Tests are split into an atomic tier, each verifying a single behavior, and an integration tier composing several projections against shared state. Expected values in tests were produced by executing this specification's reference behavior — matching the letter of this document is the only reliable strategy.
