# spec_test_map — memfs-inmemory-fs-fullrepro-001

filter/oracle_source: generated_only
oracle_version: 2026-08-25

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|-------------|-------|----------------|--------------|--------|-------|
| atomic::a new volume is empty apart from the root directory | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-001 |
| atomic::fromJSON materializes files, parents, and Buffer contents | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-002, MFS-VOL-014 |
| atomic::a null value in fromJSON creates an empty directory | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-003 |
| atomic::instance fromJSON resolves relative keys against the cwd argument | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-004 |
| atomic::fromNestedJSON treats inner objects as directories | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-005 |
| atomic::toJSON flattens files, marks empty dirs null, and filters by subtree | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-006, MFS-VOL-008 |
| atomic::reset discards every node | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-009 |
| atomic::the default volume backs the fs export and top-level named exports | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-010 |
| atomic::memfs() returns a seeded fs and vol pair | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-011 |
| atomic::createFsFromVolume wraps an existing volume in both directions | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-012 |
| atomic::distinct volumes share no state | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-013 |
| atomic::symbolic links are absent from toJSON while hard links appear per name | atomic | positive | section Volumes And Snapshots | covered | MFS-VOL-007 |
| atomic::writeFileSync stores strings readable back through either encoding form | atomic | positive | section Files And Directories | covered | MFS-FIL-001, MFS-FIL-003 |
| atomic::readFileSync without encoding returns a Buffer | atomic | positive | section Files And Directories | covered | MFS-FIL-001, MFS-FIL-003 |
| atomic::writeFileSync decodes string data through the encoding option | atomic | positive | section Files And Directories | covered | MFS-FIL-002 |
| atomic::writeFileSync with flag a appends instead of replacing | atomic | positive | section Files And Directories | covered | MFS-FIL-002 |
| atomic::appendFileSync appends to existing files and creates missing ones | atomic | positive | section Files And Directories | covered | MFS-FIL-004 |
| atomic::writes reject missing parents and file path components | atomic | failure_path | section Files And Directories | covered | MFS-FIL-005 |
| atomic::reading a directory as a file raises EISDIR | atomic | failure_path | section Files And Directories | covered | MFS-FIL-005 |
| atomic::non-recursive mkdir rejects missing parents and existing targets | atomic | positive | section Files And Directories | covered | MFS-FIL-006 |
| atomic::recursive mkdir returns the full target path or undefined when present | atomic | positive | section Files And Directories | covered | MFS-FIL-007 |
| atomic::mkdtempSync appends six alphanumeric characters to the prefix | atomic | positive | section Files And Directories | covered | MFS-FIL-009 |
| atomic::readdirSync lists entry names lexicographically sorted | atomic | positive | section Files And Directories | covered | MFS-FIL-010 |
| atomic::withFileTypes returns Dirent objects with parent paths and predicates | atomic | positive | section Files And Directories | covered | MFS-FIL-011 |
| atomic::recursive readdir returns descendant paths relative to the directory | atomic | positive | section Files And Directories | covered | MFS-FIL-012 |
| atomic::readdirSync rejects files with ENOTDIR and missing paths with ENOENT | atomic | failure_path | section Files And Directories | covered | MFS-FIL-013 |
| atomic::unlinkSync removes files but rejects directories with EPERM | atomic | positive | section Files And Directories | covered | MFS-FIL-014 |
| atomic::rmdirSync removes empty directories only | atomic | positive | section Files And Directories | covered | MFS-FIL-015 |
| atomic::rmSync with recursive removes a whole subtree | atomic | positive | section Files And Directories | covered | MFS-FIL-016 |
| atomic::rmSync guards: missing path, force, and directory without recursive | atomic | failure_path | section Files And Directories | covered | MFS-FIL-016 |
| atomic::renameSync replaces destinations and rejects missing endpoints | atomic | positive | section Files And Directories | covered | MFS-FIL-017 |
| atomic::renameSync moves a directory subtree and preserves node identity | atomic | positive | section Files And Directories | covered | MFS-FIL-017 |
| atomic::copyFileSync copies content into a default-mode node and honors COPYFILE_EXCL | atomic | positive | section Files And Directories | covered | MFS-FIL-018 |
| atomic::cpSync recursive performs a deep copy of a tree | atomic | positive | section Files And Directories | covered | MFS-FIL-019 |
| atomic::cpSync guards: directory without recursive and errorOnExist | atomic | positive | section Files And Directories | covered | MFS-FIL-019 |
| atomic::truncateSync shrinks and zero-extends file content | atomic | positive | section Files And Directories | covered | MFS-FIL-020 |
| atomic::existence checks report booleans and access raises ENOENT when missing | atomic | positive | section Files And Directories | covered | MFS-FIL-021, MFS-FIL-022 |
| atomic::stats expose size, kind predicates, identity and timestamps | atomic | positive | section Metadata And Permissions | covered | MFS-MET-001 |
| atomic::fstatSync reports on an open descriptor | atomic | positive | section Metadata And Permissions | covered | MFS-MET-002 |
| atomic::stat options: bigint fields and throwIfNoEntry | atomic | positive | section Metadata And Permissions | covered | MFS-MET-003, MFS-MET-004 |
| atomic::size tracks writes, appends and truncation | atomic | positive | section Metadata And Permissions | covered | MFS-MET-005 |
| atomic::created nodes carry the default permission bits | atomic | positive | section Metadata And Permissions | covered | MFS-MET-006 |
| atomic::explicit mode options are honored on creation | atomic | positive | section Metadata And Permissions | covered | MFS-MET-006 |
| atomic::chmod feeds accessSync capability checks | atomic | positive | section Metadata And Permissions | covered | MFS-MET-007, MFS-MET-008 |
| atomic::reading a mode-denied file raises EACCES | atomic | positive | section Metadata And Permissions | covered | MFS-MET-009 |
| atomic::utimesSync and futimesSync store the given times | atomic | positive | section Metadata And Permissions | covered | MFS-MET-010 |
| atomic::symlinkSync stores a target returned verbatim by readlinkSync | atomic | positive | section Links And Path Resolution | covered | MFS-LNK-001 |
| atomic::links resolve at intermediate path components | atomic | positive | section Links And Path Resolution | covered | MFS-LNK-002 |
| atomic::statSync follows links while lstatSync reports the link node | atomic | positive | section Links And Path Resolution | covered | MFS-LNK-003 |
| atomic::realpathSync follows chains of links transitively | atomic | positive | section Links And Path Resolution | covered | MFS-LNK-004 |
| atomic::readlinkSync on a regular file raises EINVAL | atomic | failure_path | section Links And Path Resolution | covered | MFS-LNK-005 |
| atomic::a dangling link hides from exists until its target appears | atomic | positive | section Links And Path Resolution | covered | MFS-LNK-006, MFS-LNK-007 |
| atomic::unlinking a symlink leaves its target intact | atomic | positive | section Links And Path Resolution | covered | MFS-LNK-008 |
| atomic::hard links share identity and content in both directions | atomic | positive | section Links And Path Resolution | covered | MFS-LNK-009 |
| atomic::linkSync rejects an existing destination and a missing source | atomic | failure_path | section Links And Path Resolution | covered | MFS-LNK-010 |
| atomic::openSync returns distinct numeric descriptors | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-001 |
| atomic::open flag guards: r and r+ need the file, wx refuses it, w truncates | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-002 |
| atomic::flag a appends every write at the end | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-002 |
| atomic::readSync copies bytes at an absolute position and reports the count | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-003 |
| atomic::null-position reads advance the descriptor position sequentially | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-003 |
| atomic::writeSync reports bytes written and overwrites at a position | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-004 |
| atomic::ftruncateSync truncates through the descriptor | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-005 |
| atomic::descriptor writes are immediately visible to path reads | atomic | positive | section File Descriptors And Low-Level I/O | covered | MFS-FD-006 |
| atomic::stale descriptors raise EBADF everywhere | atomic | failure_path | section File Descriptors And Low-Level I/O | covered | MFS-FD-007 |
| atomic::callbacks deliver values on success and codes on failure | atomic | positive | section Callbacks, Promises, And Streams | covered | MFS-ASY-001 |
| atomic::callback writes and mkdirs mutate the tree | atomic | positive | section Callbacks, Promises, And Streams | covered | MFS-ASY-001 |
| atomic::exists delivers a single boolean to its callback | atomic | positive | section Callbacks, Promises, And Streams | covered | MFS-ASY-002 |
| atomic::the promises API mirrors operations and rejection codes | atomic | positive | section Callbacks, Promises, And Streams | covered | MFS-ASY-003 |
| atomic::a FileHandle reads, stats and closes | atomic | positive | section Callbacks, Promises, And Streams | covered | MFS-ASY-004 |
| atomic::FileHandle writes report bytesWritten and store the bytes | atomic | positive | section Callbacks, Promises, And Streams | covered | MFS-ASY-004 |
| atomic::write streams persist on finish and read streams honor encoding | atomic | positive | section Callbacks, Promises, And Streams | covered | MFS-ASY-005 |
| atomic::a read stream for a missing path emits ENOENT | atomic | failure_path | section Callbacks, Promises, And Streams | covered | MFS-ASY-006 |
| atomic::failures carry code and path properties | atomic | failure_path | section Error Semantics | covered | MFS-ERR-001, MFS-ERR-002 |
| integration::a tree built by operations snapshots and restores faithfully | integration | positive | section Cross-View Invariants | covered | MFS-INV-001, MFS-INV-006 |
| integration::every toJSON path reads back exactly and every plain file appears | integration | positive | section Cross-View Invariants | covered | MFS-INV-001 |
| integration::restoring a snapshot flattens links into independent plain files | integration | positive | section Cross-View Invariants + section Volumes And Snapshots | covered | MFS-INV-006, MFS-VOL-015 |
| integration::nested and flat construction of the same tree agree in every view | integration | positive | section Volumes And Snapshots + section Cross-View Invariants | covered | MFS-VOL-005, MFS-VOL-006, MFS-INV-001 |
| integration::bytes written through one projection are identical through all readers | integration | positive | section Cross-View Invariants | covered | MFS-INV-002 |
| integration::positional descriptor patches are seen by snapshot, promise and stat views | integration | positive | section File Descriptors And Low-Level I/O + section Cross-View Invariants | covered | MFS-FD-004, MFS-FD-006, MFS-INV-002 |
| integration::truncate, append and descriptor writes keep sizes consistent everywhere | integration | positive | section Metadata And Permissions + section Cross-View Invariants | covered | MFS-MET-005, MFS-INV-002 |
| integration::piping a read stream into a write stream copies a file | integration | positive | section Callbacks, Promises, And Streams + section Cross-View Invariants | covered | MFS-ASY-005, MFS-INV-002 |
| integration::one file written by wrapper, promise and callback stays coherent | integration | positive | section Callbacks, Promises, And Streams + section Cross-View Invariants | covered | MFS-ASY-001, MFS-ASY-003, MFS-INV-002 |
| integration::readdir names, dirents and lstat predicates agree | integration | positive | section Cross-View Invariants | covered | MFS-INV-003 |
| integration::hard-linked names agree across stats, reads and listings | integration | positive | section Cross-View Invariants | covered | MFS-INV-004 |
| integration::a rename is observed atomically by every projection | integration | positive | section Cross-View Invariants | covered | MFS-INV-005 |
| integration::permission changes gate every read projection consistently | integration | positive | section Metadata And Permissions + section Cross-View Invariants | covered | MFS-MET-008, MFS-MET-009, MFS-INV-007 |
| integration::sync, callback and promise forms report the same missing-path code | integration | failure_path | section Cross-View Invariants | covered | MFS-INV-007 |
| integration::writes through a directory symlink land in the real tree | integration | positive | section Links And Path Resolution + section Cross-View Invariants | covered | MFS-LNK-002, MFS-INV-001 |
| integration::a dangling link joins the tree when its target arrives via promises | integration | positive | section Links And Path Resolution + section Callbacks, Promises, And Streams | covered | MFS-LNK-006, MFS-LNK-007, MFS-ASY-003 |
| integration::hardlink content flows both ways across sync and promise writers | integration | positive | section Links And Path Resolution + section Cross-View Invariants | covered | MFS-LNK-009, MFS-INV-004 |
| integration::memfs pairs, wrappers and the default volume stay independent | integration | positive | section Volumes And Snapshots | covered | MFS-VOL-011, MFS-VOL-012, MFS-VOL-013 |
| integration::a deep copy between volumes via snapshot has independent state | integration | positive | section Volumes And Snapshots | covered | MFS-VOL-002, MFS-VOL-006, MFS-VOL-013 |
| integration::cp recursive inside one volume then divergence leaves the copy alone | integration | positive | section Files And Directories + section Cross-View Invariants | covered | MFS-FIL-019, MFS-INV-001 |
| integration::mkdtemp workspaces live a full create-use-destroy cycle | integration | positive | section Files And Directories + section Cross-View Invariants | covered | MFS-FIL-009, MFS-FIL-016, MFS-INV-001 |
| integration::mixed failure codes surface correctly across one populated tree | integration | failure_path | section Error Semantics | covered | MFS-ERR-002 |
| integration::a project scaffold is built, linked, verified and snapshotted | system_e2e | positive | section Cross-View Invariants + section Links And Path Resolution | covered | MFS-INV-001, MFS-INV-003, MFS-INV-004, MFS-LNK-004 |
| integration::an editor session mixes descriptors, promises, truncation and streams | system_e2e | positive | section File Descriptors And Low-Level I/O + section Callbacks, Promises, And Streams + section Cross-View Invariants | covered | MFS-FD-003, MFS-FD-004, MFS-FD-005, MFS-ASY-003, MFS-ASY-005, MFS-INV-002 |
| integration::a backup is exported, reorganized in a second volume and verified | system_e2e | positive | section Volumes And Snapshots + section Cross-View Invariants + section Files And Directories | covered | MFS-VOL-004, MFS-INV-005, MFS-INV-006, MFS-FIL-017 |
| integration::a content pipeline decodes, guards and republishes across projections | system_e2e | positive | section Files And Directories + section Metadata And Permissions + section Cross-View Invariants | covered | MFS-FIL-002, MFS-FIL-018, MFS-MET-008, MFS-MET-009, MFS-INV-002 |

Total: 99 | kept (covered): 99 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 99

Track A note: upstream tests import monorepo-relative source paths and are not
portable to a clean package install; the oracle is Track B generated from the
spec with expected values observed by executing the pinned reference release.
