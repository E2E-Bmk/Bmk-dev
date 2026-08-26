repo: streamich/memfs
source_path: https://github.com/streamich/memfs (wip/repo-cache/memfs-src, packages/memfs + fs-core + fs-node)
commit: d1703ac2110c39fe6c574bba5bab7a01db0e846b (npm memfs@4.68.1 tag v4.68.1)
language: typescript
src_loc: 6306 (packages/{memfs,fs-node,fs-core}/src/**/*.ts excl. __tests__; 12819 across all workspace packages)
test_functions: ~1206 (it/test callbacks across the monorepo)
test_files: 99 (packages/*/src/**/__tests__/*.test.ts)
dominant_test_styles: unit + integration over one Volume instance; behavioral assertions via jest expect
public_docs: https://github.com/streamich/memfs README, docs/node/usage.md, docs/node/api-status.md, Node.js fs API docs (the package implements the node fs contract)
core_fact_source: an in-memory superblock — an inode table (files, directories, symlinks with content, mode, timestamps, nlink) plus an open-file-descriptor table, owned by a Volume
derived_views: (1) synchronous fs API projection (readFileSync/statSync/readdirSync/... over the same inode table);
  (2) callback fs API projection (same ops, error-first callbacks);
  (3) promise fs API projection (fs.promises / FileHandle);
  (4) JSON snapshot projection (vol.toJSON() flattening the tree; Volume.fromJSON()/fromNestedJSON() materializing it);
  (5) metadata projection (Stats objects: kind predicates, size, ino/nlink identity; Dirent objects from readdir withFileTypes);
  (6) link projection (symlink/readlink/realpath resolution; hardlink nlink/ino sharing);
  (7) byte-stream projection (createReadStream/createWriteStream over file content);
  (8) low-level fd projection (open/read/write/close with flags and positional I/O).
external_deps: runtime deps are @jsonjoy.com/* workspace packages (bundled in the npm release); tests need only vitest
test_import_audit: HIGH_RISK for Track A portability — upstream tests import '../index', '..' and workspace packages '@jsonjoy.com/fs-core' (monorepo-relative, not the published package root); effectively 100% of suites affected -> Track A discarded, oracle generated (Track B)
docs_test_alignment: aligned — README/usage docs cover exactly the projections the tests exercise (snapshot API, node fs ops, links, fds, streams, errors)
contamination_note: memfs@4.68.1, released 2026-08-10, relative to training cutoff: after (likely) — the 4.68 line is a fresh monorepo restructure (@jsonjoy.com/fs-* packages); memorized knowledge covers the pre-split single-package layout
decision: keep
reason: rule-engine reimplementation (POSIX path resolution, errno taxonomy, fd table, link semantics) with >=8 public projections over one inode-table fact source, 6.3k core LOC, very active suite (1206 tests).
risks: (1) upstream tests non-portable -> generated_only oracle; mitigated by probing the pinned release for every asserted behavior;
  (2) fs surface is huge (~90 exports) -> scope to the core subset the spec can honestly specify; exclude watch/watchFile (timing), glob/opendir/statfs/openAsBlob (peripheral);
  (3) error-message text is an implementation detail -> assert err.code / exception class, never message sentences;
  (4) relative-path resolution depends on process.cwd() -> all oracle paths absolute.
scope_plan: target_subdomain=Volume + snapshots (fromJSON/fromNestedJSON/toJSON/reset/memfs()/createFsFromVolume), core file & directory ops (write/read/append/mkdir/mkdtemp/readdir/unlink/rmdir/rm/rename/copyFile/cp/truncate/exists/access), metadata (stat/lstat/fstat, Stats predicates & fields, chmod/utimes), links & resolution (symlink/readlink/realpath/link/lstat), fd I/O (open flags/read/write/close/ftruncate), promises API + FileHandle subset, streams (createReadStream/createWriteStream), errno semantics; expected_oracle_max=100
excluded: watch/watchFile/unwatchFile/StatWatcher/FSWatcher (timing-dependent), glob/globSync, opendir/Dir iteration, statfs, openAsBlob, chown family beyond acceptance, fdatasync/fsync semantics beyond acceptance, readv/writev, lchmod/lchown/lutimes, X_OK permission enforcement details, mount/relative-cwd behavior, print/snapshot/casfs/crudfs companion packages
