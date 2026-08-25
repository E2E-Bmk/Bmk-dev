# Clause IDs — memfs-inmemory-fs-fullrepro-001 (spec_v1)

## Volumes And Snapshots (MFS-VOL)
- MFS-VOL-001 — new Volume() creates an empty volume with only root `/`.
- MFS-VOL-002 — Volume.fromJSON creates files from flat path->content map; intermediate dirs auto-created.
- MFS-VOL-003 — null value in fromJSON creates an empty directory.
- MFS-VOL-004 — vol.fromJSON(json, cwd) resolves relative keys against cwd.
- MFS-VOL-005 — Volume.fromNestedJSON accepts nested objects as directories.
- MFS-VOL-006 — toJSON returns flat absolute-path->string map; empty dirs appear with null.
- MFS-VOL-007 — symlinks do not appear in toJSON; hard-linked names appear as independent keys with same content.
- MFS-VOL-008 — toJSON(path) restricts to subtree.
- MFS-VOL-009 — reset() empties volume: toJSON {} and prior paths gone.
- MFS-VOL-010 — package exports vol (default Volume) and fs bound to it; top-level named exports bound to vol.
- MFS-VOL-011 — memfs(json) returns { fs, vol } seeded from json.
- MFS-VOL-012 — createFsFromVolume(volume) wraps existing volume; mutations visible both ways.
- MFS-VOL-013 — distinct Volume instances are isolated.
- MFS-VOL-014 — fromJSON accepts Buffer values.
- MFS-VOL-015 — restoring a snapshot yields plain independent files (links not round-tripped).

## Files And Directories (MFS-FIL)
- MFS-FIL-001 — writeFileSync creates/replaces; accepts string or Buffer.
- MFS-FIL-002 — writeFileSync options: encoding decodes string data (base64/hex); flag "a" appends.
- MFS-FIL-003 — readFileSync returns Buffer; encoding (string or options) returns decoded string.
- MFS-FIL-004 — appendFileSync appends and creates when missing.
- MFS-FIL-005 — writeFileSync missing parent -> ENOENT; non-terminal file component -> ENOTDIR; readFileSync on dir -> EISDIR.
- MFS-FIL-006 — mkdirSync non-recursive: missing parent ENOENT; existing EEXIST.
- MFS-FIL-007 — mkdirSync recursive creates ancestors; existing target not an error; returns full target path string when created, undefined when existed.
- MFS-FIL-008 — mkdirSync mode option sets permission bits.
- MFS-FIL-009 — mkdtempSync returns prefix + exactly 6 random alphanumeric chars; creates directory.
- MFS-FIL-010 — readdirSync returns lexicographically sorted names.
- MFS-FIL-011 — readdirSync withFileTypes returns Dirent with name, parentPath, path, kind predicates.
- MFS-FIL-012 — readdirSync recursive returns descendant paths relative to listed dir.
- MFS-FIL-013 — readdirSync on file ENOTDIR; missing ENOENT.
- MFS-FIL-014 — unlinkSync removes file or symlink name; on directory EPERM.
- MFS-FIL-015 — rmdirSync removes empty dir; non-empty ENOTEMPTY; on file ENOTDIR.
- MFS-FIL-016 — rmSync recursive removes subtree; missing ENOENT unless force; dir without recursive ERR_FS_EISDIR.
- MFS-FIL-017 — renameSync moves files/subtrees; replaces existing dest; preserves ino; missing source or dest parent ENOENT.
- MFS-FIL-018 — copyFileSync copies content; copy gets default file mode; COPYFILE_EXCL + existing dest EEXIST.
- MFS-FIL-019 — cpSync recursive copies trees deeply; dir without recursive EISDIR; force:false+errorOnExist EEXIST; default overwrites.
- MFS-FIL-020 — truncateSync cuts to length; extending pads with zero bytes.
- MFS-FIL-021 — existsSync returns boolean, never throws.
- MFS-FIL-022 — accessSync undefined on accessible path; ENOENT when missing.

## Metadata And Permissions (MFS-MET)
- MFS-MET-001 — Stats: kind predicates, size, mode, nlink, ino, Date + Ms timestamps.
- MFS-MET-002 — statSync follows symlinks; lstatSync reports link node; fstatSync via fd.
- MFS-MET-003 — bigint:true yields BigInt fields.
- MFS-MET-004 — throwIfNoEntry:false returns undefined for missing; otherwise ENOENT.
- MFS-MET-005 — size reflects content length across all mutation paths.
- MFS-MET-006 — default modes: file 0o666, dir 0o777; mode option on mkdirSync/openSync sets bits exactly.
- MFS-MET-007 — chmodSync replaces permission bits observable via stats.mode & 0o777.
- MFS-MET-008 — accessSync mode checks F_OK/R_OK/W_OK/X_OK; denial -> EACCES.
- MFS-MET-009 — read enforcement: reading mode-denied file -> EACCES.
- MFS-MET-010 — utimesSync accepts Date or seconds; observable in ms fields; futimesSync via fd.

## Links And Path Resolution (MFS-LNK)
- MFS-LNK-001 — symlinkSync stores target; readlinkSync returns it verbatim.
- MFS-LNK-002 — resolution follows links at final and intermediate components.
- MFS-LNK-003 — statSync resolves target; lstatSync isSymbolicLink true.
- MFS-LNK-004 — realpathSync returns fully resolved path, following chains.
- MFS-LNK-005 — readlinkSync on non-link EINVAL.
- MFS-LNK-006 — dangling link: existsSync false, read/realpath ENOENT, lstat works.
- MFS-LNK-007 — creating target later makes dangling link traversable.
- MFS-LNK-008 — unlinkSync on symlink removes only the link.
- MFS-LNK-009 — linkSync: shared ino/content, nlink counts names, writes visible both ways, unlink decrements.
- MFS-LNK-010 — linkSync existing newPath EEXIST; missing existingPath ENOENT.

## File Descriptors (MFS-FD)
- MFS-FD-001 — openSync returns numeric fd; concurrent fds distinct.
- MFS-FD-002 — flags: r/r+ missing ENOENT; w truncates; wx existing EEXIST; a appends; mode sets bits on create.
- MFS-FD-003 — readSync copies bytes, returns count; absolute position or null for sequential advance.
- MFS-FD-004 — writeSync returns bytes written; positional write overwrites in place.
- MFS-FD-005 — ftruncateSync truncates open file.
- MFS-FD-006 — descriptor and path operations observe each other immediately.
- MFS-FD-007 — closed/never-issued fd -> EBADF on read/write/close.

## Callbacks, Promises, Streams (MFS-ASY)
- MFS-ASY-001 — callback form (error, result), error null on success, same code on failure.
- MFS-ASY-002 — exists callback receives only a boolean.
- MFS-ASY-003 — promises API mirrors ops; rejection carries same code.
- MFS-ASY-004 — promises.open resolves FileHandle with fd; readFile/writeFile/write/stat/close; write(buffer) -> { bytesWritten, buffer }.
- MFS-ASY-005 — createWriteStream stores data on finish; createReadStream reads bytes honoring encoding; pipe copies.
- MFS-ASY-006 — read stream for missing path emits error with ENOENT.

## Error Semantics (MFS-ERR)
- MFS-ERR-001 — errors carry code property; path property when applicable; message text not contractual.
- MFS-ERR-002 — condition->code table (ENOENT/EEXIST/EISDIR/ERR_FS_EISDIR/ENOTDIR/EPERM/ENOTEMPTY/EACCES/EBADF/EINVAL).

## Cross-View Invariants (MFS-INV)
- MFS-INV-001 — toJSON paths readable with exact content; traversable files appear in toJSON.
- MFS-INV-002 — bytes written via any projection identical through every reader; size agrees.
- MFS-INV-003 — readdir names == dirent names in order; dirent predicates agree with lstat.
- MFS-INV-004 — hard links agree in every metadata view; nlink == number of names.
- MFS-INV-005 — rename observed atomically by all projections; ino and structure preserved.
- MFS-INV-006 — fromJSON(toJSON()) restores content; symlink-only paths absent; hard links materialized.
- MFS-INV-007 — sync/callback/promise forms report same error code.
