# Rust 候选筛查（S1 screening, 2026-08-21）

> Complements the **Rust** section of `CANDIDATES_MULTILANG.md`. Everything below was
> **measured**, not recalled: repos were shallow-cloned into `/tmp/rust_scout/` and counted
> with `/tmp/rust_scout/metrics.py`. No `cargo`/`tokei` in this environment, so LOC is a
> line counter, not `cargo`-derived, and **no test was executed** — every entry carries an
> explicit "run this in `spec2repo-rust:latest`" item at the end.

**Counting rules used everywhere in this file**

| quantity | definition |
|---|---|
| `src LOC` | non-blank, non-comment lines under the crate's own `src/`, with `#[cfg(test)] mod …{…}` blocks removed by brace matching. Excludes `tests/`, `benches/`, `examples/`, generated files |
| `external tests` | `#[test]` / `#[tokio::test]` occurrences under the crate's `tests/` directory (integration targets, `pub`-surface only) |
| `inline tests` | same attributes inside `src/` |
| `snapshot asserts` | `insta::assert*` \| `assert_*_snapshot` \| `expect![` \| `expect_file!` \| `assert_data_eq!` \| `expectorate` under `tests/` |
| private reach | in Rust, `use crate::` inside an integration target refers to **the test crate's own root**, not the library — so the Python-style private-import grep does not transfer. Reach was judged by (a) the ratio inline-vs-external tests and (b) whether `tests/` can only see `pub` items (it can, by construction) |

Repo HEADs used: `gitoxide 227619ad (2026-08-19)`, `apollo-rs eca97fc4 (2026-08-18)`,
`toml f42dcad6 (2026-08-20)`, `rattler ba83a78f (2026-08-21)`, `oxc-resolver 9bfa27ab (2026-08-20)`,
`tracing d9d4c542 (2026-05-30)`, plus the reject-table repos listed in their rows.

---

## 1. `gix-ref` — git reference store

| field | content |
|---|---|
| name / crate | `gix-ref` (workspace member of GitoxideLabs/gitoxide) |
| repo | https://github.com/GitoxideLabs/gitoxide |
| version / release | **0.66.0, published 2026-07-23** (crates.io); HEAD `227619ad`, 2026-08-19 |
| src LOC | **5 004** across 41 files (130 lines of inline tests removed) |
| test functions | **144 external** — 143 under `tests/refs/` (23 files, one integration target rooted at `tests/refs/main.rs`) + 1 in `tests/transaction_fd_limit.rs`. Inline: 31 in 4 `#[cfg(test)]` blocks |
| private reach | **clean**. All 144 live in integration targets and can only see `pub` items; the 31 inline ones are ~6 % of a rewritten crate's surface and are dropped with `src/`. `use crate::…` hits are references to the test crate's own helper modules (`crate::file::store()`, `crate::hex_to_id`), verified by reading them |
| assertion style | 452 plain `assert*` vs **3 snapshot asserts** — the cleanest structural-assertion suite of everything screened |
| fixtures / offline | `tests/fixtures/` = 13 `make_*.sh` generators **plus 22 pre-generated `.tar` archives (23 MB) committed in-tree** (`.gitattributes` marks them `filter=lfs-disabled`, so a plain clone gets real bytes). `gix-testtools` extracts the archive and only re-runs the shell script if the script hash drifts → **no network, no daemon**; `git`+`bash` needed only in the fallback path |
| external deps | `gix-{features,fs,path,hash,object,utils,validate,actor,lock,tempfile}` (all published on crates.io with matching versions), `thiserror`, `memmap2`, optional `serde`. **No C toolchain, no system libs, no git deps.** edition 2024, MSRV 1.85 (image has 1.95) |
| dev-dep hazard | `gix-testtools` is pulled with `default-features = false`, which **disables the `repo-snapshot` feature that would otherwise depend on `gix-ref` itself** — no candidate↔harness cycle. (crates.io only has `gix-testtools 0.19.0` vs `0.20.0` in-tree — pin or vendor it) |
| memorizable standard | **Mostly no.** The recitable part is `git check-ref-format` naming rules. Not recitable: loose-vs-`packed-refs` precedence and overlay iteration, the `.lock`-file transaction protocol with `PreviousValue` preconditions, reflog line format and `@{n}` lookup, `refs/namespaces/` forwarding, worktree-private ref routing (`worktree/`, `main-worktree/`), symbolic-ref chain following with cycle abort. Git's man pages describe *effects*, not this algorithm |
| objects per scenario | **7+** for one realistic scenario ("update a branch that is packed, through a transaction, and read it back peeled"): `file::Store` → `file::Transaction` → `RefEdit`/`Change`/`PreviousValue` → `packed::Buffer` (+ `packed::Transaction`) → `Reference`/`Target::{Object,Symbolic}` → `ReferenceExt::{follow, peel_to_id_in_place}` (needs an object-lookup closure) → `log::Line`/reflog iterator; names go through `FullName`/`PartialName`/`Category` |
| difficulty | **hard** — a lazily resolved reference graph (symbolic targets resolved on demand, chain following with `peel::Error::Cycle`), an equivalence judgement (loose and packed views must agree, and a transaction must leave no half-applied prefix), and a factor product (loose × packed × namespaced × worktree × sha1/sha256) |
| decision | **keep — rank 1** |
| risks | 23 MB of fixture archives must travel with the oracle; sha256 fixtures double several cases; the crate is a hot dependency of the whole gix ecosystem so contamination is real (49.7 M downloads), but the algorithm itself is not documented anywhere reciteable |

## 2. `gix-odb` — object database (loose + packs + alternates)

| field | content |
|---|---|
| name / crate | `gix-odb` |
| repo | https://github.com/GitoxideLabs/gitoxide |
| version / release | **0.83.0, 2026-07-23**; HEAD `227619ad` |
| src LOC | **4 442** across 29 files (42 lines inline tests removed) |
| test functions | **71 external** in 13 files (`tests/odb/main.rs` target: `alternate.rs`, `find.rs`, `header.rs`, `memory.rs`, `regression.rs`, `sink.rs`, `store/…`) + a `tests/doctest.rs` helper `include!`d by the lib docs. Inline: **3** in 2 blocks |
| private reach | **clean** (3 inline tests total) |
| assertion style | 216 plain asserts, **0 snapshot asserts** |
| fixtures / offline | 5 committed archives, 5.8 MB, 4 generator scripts; 1 `Command::new` and 1 `cfg(unix)` gate in the suite. No network |
| external deps | `gix-features`, `gix-zlib`, `gix-hashtable`, `gix-hash`, `gix-path`, `gix-quote`, `gix-object`, `gix-pack`, `gix-fs`, `tempfile`, `arc-swap`, `parking_lot`, `memmap2`, `thiserror`, optional `serde` (verified from `Cargo.toml`). All crates.io, pure Rust |
| memorizable standard | **No.** Loose-object layout (`aa/bbbb…`, zlib) is recitable in one paragraph, but that is a small share of the crate. The bulk is gitoxide's *own* dynamic `Store`: index slot loading, refresh-on-miss policy, handle generations that invalidate cached indices when packs are repacked away, alternates-file parsing **with cycle detection and relative-path resolution**, multi-pack-index promotion, prefix (short-hash) disambiguation across all sources |
| objects per scenario | **6+**: `Store` → `Handle` (with `RefreshMode` + object cache) → `store_impls::loose::Store` → `gix_pack::Bundle`/`multi_index::File` → `alternate` chain → `traits::{Find, Header, Write}` + `Sink`/`memory::Proxy` decorators |
| difficulty | **hard** — textbook lazily-resolved graph: the same `Handle` answers differently before and after a refresh, a miss must trigger exactly one reload, and alternates form a graph that must not loop. Equivalence judgement is present too (`header()` must agree with `find()` without decoding) |
| decision | **keep — rank 2** |
| risks | `gix-pack` is a dependency, so a spec must draw the line at "packs are provided by a published dependency, you implement the store/handle/refresh layer"; the multithreaded `parallel` feature should be excluded from the delivery to keep behaviour deterministic |

## 3. `gix-index` — the git index file

| field | content |
|---|---|
| name / crate | `gix-index` |
| repo | https://github.com/GitoxideLabs/gitoxide |
| version / release | **0.54.0, 2026-07-23**; HEAD `227619ad` |
| src LOC | **3 445** across 35 files |
| test functions | **90 external** in 15 files (`tests/index/main.rs`: `access.rs`, `entry/`, `file/`, `fs.rs`, `fuzzed.rs`, `init.rs`). Inline: **4** in 3 blocks |
| private reach | **clean** |
| assertion style | 270 plain asserts, **4 snapshot asserts** (`insta` with filters, used for a couple of tree-extension dumps) |
| fixtures / offline | **39 committed archives, 3.3 MB**, 3 generator scripts, plus fuzzed corpora. No network, no `Command::new` |
| external deps | `gix-features`, `gix-hash`, `gix-bitmap`, `gix-object`, `gix-validate`, `gix-traverse`, `gix-lock`, `gix-fs`, `gix-utils`, `hashbrown`, `fnv`, `memmap2`, `filetime`, `bstr`, `smallvec`, `itoa`, `bitflags`, `thiserror`, `rustix`/`libc` (unix), optional `serde` (verified from `Cargo.toml`). All crates.io |
| memorizable standard | **Partially yes** — `gitformat-index(5)` documents the on-disk layout and the `TREE`/`REUC`/`UNTR`/`link`/`EOIE`/`sdir` extension byte formats. A strong model can plausibly recall the header and entry layout. Not recitable: extension interplay (split index `link` + `replace/delete` bitmaps applied over a shared index), sparse-directory entries, stat-data truncation and racy-timestamp handling, write-back ordering that must reproduce byte-identical output |
| objects per scenario | **5+**: `File`/`State` → `Entry` + `entry::{Flags, Mode, Stat}` → `extension::{Tree, Link, UntrackedCache, ResolveUndo, Sparse, EndOfIndexEntry}` → `decode::Options` → `write::Options` → `verify` |
| difficulty | **medium-hard** — round-trip equivalence (decode → mutate → encode must byte-match, extension-by-extension) is the crate's whole point, but the format being publicly documented caps the ceiling |
| decision | **keep — rank 3** |
| risks | binary-format work means a wrong byte fails everything at once (score may collapse to 0 rather than land mid-range — see the "0 分有两种含义" hazard); pick the oracle so that decode-side tests can pass without a correct encoder |

## 4. `gix-pack` — pack files, delta trees, pack index writing

| field | content |
|---|---|
| name / crate | `gix-pack` |
| repo | https://github.com/GitoxideLabs/gitoxide |
| version / release | **0.73.0, 2026-07-23**; HEAD `227619ad` |
| src LOC | **8 118** across 67 files (496 lines inline tests removed) |
| test functions | **93 external** in 18 files (`tests/pack/main.rs`: `bundle.rs`, `index.rs`, `iter.rs`, `malformed.rs`, `data/`, `index/`, `multi_index/`). Inline: **17** in 7 blocks |
| private reach | clean-ish (17 inline, ~15 % of total) |
| assertion style | 252 plain asserts, **0 snapshot asserts** |
| fixtures / offline | 4 committed archives, 3.2 MB, 2 scripts, plus small in-tree `.pack`/`.idx` files. No network |
| external deps | `gix-features`, `gix-zlib`, `gix-path`, `gix-hash`, `gix-chunk`, `gix-error`, `gix-object`, `gix-hashtable`, `gix-traverse`, `gix-diff`, `gix-tempfile`, `memmap2`, `smallvec`, `parking_lot`, `crossbeam-deque`, `uluru`, `clru`, `thiserror`, optional `serde` (verified from `Cargo.toml`). All crates.io, pure Rust |
| memorizable standard | **Partially yes** — `gitformat-pack(5)` documents pack v2, the `.idx` v2 fanout, and the multi-pack-index chunk format; delta instruction encoding (copy/insert opcodes) is also documented. Not recitable: the delta-tree construction from offsets, the two index-write strategies (`with_lookup` vs `with_index` traversal) and their identical-output requirement, ref-delta→ofs-delta rewriting in the input stream, cache eviction policies |
| objects per scenario | **6+**: `data::File` → `index::File` → `Bundle` → `cache::delta::Tree` (+ `traverse::resolve`) → `data::input::{BytesToEntries, LookupRefDeltaObjectsIter, EntriesToBytes}` → `index::write` → `multi_index::File` |
| difficulty | **medium-hard** — the "two traversal strategies must agree" property is a genuine equivalence judgement and the delta tree is real work, but the format side is publicly specified and the crate is the biggest of the gix set (8.1k) |
| decision | **keep (rank 4) — carve required**: a whole-crate spec is too wide; scope to either (a) decode + delta-tree traversal, or (b) index/multi-index writing + verification |
| risks | performance-shaped code (mmap, LRU caches, parallel traversal) invites nondeterminism; the `parallel` feature must be off |

## 5. `gix-merge` — blob and tree merging

| field | content |
|---|---|
| name / crate | `gix-merge` |
| repo | https://github.com/GitoxideLabs/gitoxide |
| version / release | **0.19.0, 2026-07-23**; HEAD `227619ad` |
| src LOC | **4 955** across 21 files |
| test functions | **26 external** in 8 files (3 568 test LOC) + 5 inline. ⚠️ **below the ~40-function bar** |
| private reach | clean |
| assertion style | 141 plain asserts, 0 `insta`. But `tests/merge/tree/cartesian.rs` compares a whole finite Cartesian model of tree changes against a checked-in `cartesian-baseline.txt` (env `GIX_MERGE_UPDATE_CARTESIAN_BASELINE=1` regenerates it) — i.e. one golden file carries a large fraction of the coverage |
| fixtures / offline | 7 archives, **15 MB**, 4 scripts. No network |
| external deps | 15 `gix-*` siblings incl. `gix-filter`, `gix-worktree`, `gix-command`, `gix-revision`, `gix-diff`, `gix-index`, `imara-diff`, `nonempty`. All published. Note `gix-command` **spawns external merge drivers** in some paths — those tests must be excluded |
| memorizable standard | **No.** git's merge-ORT is an implementation, not a spec; conflict-marker layout and `diff3`/`zdiff3`/`ours`/`theirs`/`union` are the only recitable bits |
| objects per scenario | **6+**: `blob::Platform` → `blob::pipeline` (+ attributes from `gix-worktree`) → `blob::builtin_driver::{text, binary}` → `tree::Options`/`tree::merge` → `tree::TreeConflict`/`ResolutionFailure` → `commit::function` (merge-base via `gix-revision`) |
| difficulty | **hard** shape (rename-aware three-way tree merge, conflict taxonomy, forced-resolution modes) |
| decision | **defer** — best difficulty shape of the gix set, but 26 test functions cannot fill a 60–75-test oracle without writing most of the suite ourselves, and the Cartesian baseline is a golden blob |
| risks | 15 MB fixtures; external-driver spawning; benchmark would have to author most tests, which changes the cost profile |

## 6. `gix-object` — git object model

| field | content |
|---|---|
| name / crate | `gix-object` |
| repo | https://github.com/GitoxideLabs/gitoxide |
| version / release | **0.63.0, 2026-07-23**; HEAD `227619ad` |
| src LOC | **4 604** across 30 files |
| test functions | **148 external** in 16 files + 15 inline in 4 blocks |
| private reach | clean |
| assertion style | 401 plain asserts, **28 snapshot asserts** (~19 %), 3 `Command::new` (shell-outs to compare against real `git`) |
| fixtures / offline | 2 archives, 136 KB (the lightest of the family) |
| external deps | `gix-{features,hash,validate,actor,date,path,utils}`, `winnow`, `bstr`, `itoa`, `smallvec`, `thiserror`. All crates.io |
| memorizable standard | **Yes, strongly.** Commit/tree/tag byte formats are the single most-recited part of git's data model ("tree entries are `<mode> <name>\0<20-byte sha>`, sorted with a directory suffix rule"). A model can reconstruct most of this from memory |
| objects per scenario | 4: `Kind`/`Data` → `Commit`/`Tree`/`Tag`/`Blob` (+ `*Ref` borrowed forms) → `tree::Editor` → `Find`/`Write` traits |
| difficulty | **easy-medium** — high saturation, exactly the "single concept + memorizable standard" shape that scored >55 % in batch-15 |
| decision | **reject** (as a standalone task; it is fine as a *dependency* of gix-ref/gix-odb tasks) |

## 7. `apollo-compiler` — GraphQL schema/document compiler

| field | content |
|---|---|
| name / crate | `apollo-compiler` (workspace member of apollographql/apollo-rs) |
| repo | https://github.com/apollographql/apollo-rs |
| version / release | **1.32.0, published 2026-05-14**; HEAD `eca97fc4`, 2026-08-18 |
| src LOC | **15 905** across 47 files — **at/over the ~15k ceiling** |
| test functions | **258 external** in 25 files: top-level `tests/main.rs` target (`executable.rs` 17, `misc.rs` 20, `introspection_max_depth.rs` 13, `extensions.rs` 10, `schema.rs` 5, `parser.rs` 5, `locations.rs` 5, `error_formatting.rs` 5, `serde.rs` 3, `introspection.rs` 3, …) plus `tests/validation/` (`types.rs` 77, `field_merging.rs` 35, `interface.rs` 20, `recursion.rs` 10, …) plus a separate `snapshot_tests` target (4 functions). Inline: **8** in 2 blocks |
| private reach | **clean** — 100 `use apollo_compiler::…` at module level; the 18 `use crate::`/`use super::` hits resolve to test-crate helpers (`super::expect_valid`, `super::expect_errors`), verified by reading `tests/main.rs` (which declares every file as a module) |
| assertion style | 238 plain asserts vs **119 expect-test calls**. Per *function*, expect-driven tests are ~25–30 of 258 (~11 %) and are concentrated in `introspection_max_depth.rs`, `serde.rs`, `field_type.rs` and the 4 `snapshot_tests.rs` functions that walk `test_data/` (**531 files, 3.2 MB**) with `expect_file!`. Dropping the `snapshot_tests` target removes the golden corpus while keeping ~254 structural tests — this **corrects the "expect-test ≈47 %" figure in `CANDIDATES_MULTILANG.md`**, which counted calls, not tests |
| fixtures / offline | `test_data/` 3.2 MB in-tree; no network. Dev-deps include `notify` (fs watcher) and `serial_test` (`FileId::reset` requires serial execution — relevant to a parallel nextest runner) |
| external deps | `apollo-parser` (path dep, published 0.8.0 — **the lexer/parser lives outside the candidate crate**), `rowan`, `ariadne`, `indexmap`, `serde`, `serde_json_bytes`, `triomphe`, `typed-arena`, `ahash`, `futures`. All crates.io, pure Rust, edition 2021 |
| memorizable standard | **Yes — this is the main objection.** The GraphQL spec is public, stable, and its validation rules have canonical section names (`FieldsInSetCanMerge`, `Fragment spread is possible`, `Values of Correct Type`, …); `graphql-js` implements them under those names and is in every model's training set. `tests/validation/types.rs` alone (77 tests) is essentially a spec-section walk. Project-specific divergence is real but narrow: `Node<T>`/`Component<T>` identity + source positions preserved across type-extension merging, `Valid<T>` type-state, `DiagnosticList` ordering, introspection depth limiting, serde round-trip of the whole schema |
| objects per scenario | **5+**: `Parser` (+ `SourceMap`/`FileId`) → `Schema` → `ExecutableDocument` → `validation::{Valid, DiagnosticList}` → `Node<T>`/`Component<T>` → `Name`/`Type`/`ExtendedType` |
| difficulty | **medium** (risk of easy) — the shapes are there, but the ruleset is the most recitable one in this whole file; expect the calibration failure mode of `python-semantic-release` (55.4 %) |
| decision | **keep with conditions — rank 5**: scope down (16k LOC needs a carve anyway), drop the `snapshot_tests` target, and **write the spec around the non-spec parts** (extension merging with identity preservation, diagnostics, serde round-trip) rather than the validation rule list |
| risks | size; GraphQL saturation; parsing is delegated to a published sibling so the "reimplement the format rule" shape is weakened; `serial_test` interacts with parallel test runners |

## 8. `toml_edit` — format-preserving TOML document model

| field | content |
|---|---|
| name / crate | `toml_edit` (workspace member of toml-rs/toml) |
| repo | https://github.com/toml-rs/toml |
| version / release | **0.25.13+spec-1.1.0, published 2026-07-14**; HEAD `f42dcad6`, 2026-08-20 |
| src LOC | **7 308** across 37 files |
| test functions | **259 external** in 20 files across 5 targets: `serde` 170, `testsuite` 50, `compliance` 39, plus `decoder_compliance`/`encoder_compliance` (`harness = false`). Inline: 15 in 3 blocks |
| private reach | clean |
| assertion style | ⚠️ **snapshot-leaning**: 367 `str![` + 198 `assert_data_eq!` (snapbox inline snapshots) against 193 plain `assert_eq!`; `tests/snapshots/invalid/` holds **567 golden files** |
| fixtures / offline | dev-deps `toml-test-harness 1.13` + `toml-test-data 2.13` — i.e. the suite embeds the **public cross-implementation TOML conformance corpus**. Offline (data ships in the crate), but it is a standard conformance suite by construction |
| external deps | `indexmap`, `winnow`, `toml_datetime`, `toml_parser`, `toml_writer`, `serde_core`, `serde_spanned`. All published. edition 2024, MSRV 1.85 |
| memorizable standard | **Yes.** TOML v1.0 is short, public, and heavily memorized. Worse for us: **the actual parser now lives in the separate published `toml_parser` crate (6 413 LOC)**, so the candidate crate is the document model + serde + display layer — the part that is *not* the standard is also the part that is mostly bookkeeping (`Decor`, `RawString`, implicit tables, dotted-key mangling, `Item::None`) |
| objects per scenario | 5: `DocumentMut` → `Table`/`InlineTable`/`ArrayOfTables` → `Item` → `Value`/`Key` → `Decor`/`RawString` |
| difficulty | **medium-easy** — format preservation is a real equivalence judgement (`parse → edit → to_string` must keep untouched bytes byte-identical), but one saturated concept + a public standard + a conformance corpus is precisely the profile that scored >60 % in batch-15 |
| decision | **defer** — usable if we need a fifth Rust task, but only after re-carving the oracle away from snapbox snapshots |

## 9. `rattler_solve` — conda dependency solving

| field | content |
|---|---|
| name / crate | `rattler_solve` (workspace member of conda/rattler; note the org moved from `prefix-dev/rattler`) |
| repo | https://github.com/conda/rattler |
| version / release | **9.0.3, published 2026-08-21**; HEAD `ba83a78f`, 2026-08-21 |
| src LOC | **3 082 total — but 1 470 of that is the `libsolv_c` FFI wrapper.** The pure-Rust default path (`resolvo/` + `lib.rs`) is **1 612**, i.e. **under the 3 000 gate** |
| test functions | 87 external in 13 files (`tests/backends/`, `tests/offline.rs`, `tests/sorting.rs`); 7 inline |
| private reach | clean |
| assertion style | only 58 plain asserts vs **17 `insta` (yaml) snapshot asserts** — solved-environment dumps |
| fixtures / offline | needs `test-data/` at the repo root (**32 MB**; a handful of `repodata.json` channels actually referenced). Dev-deps pull the **unpublished** `tools` crate (`publish = false`, and it depends on `reqwest` *and* `bindgen` → libclang) and `rattler_repodata_gateway` (reqwest) |
| external deps | `rattler_conda_types`, `resolvo` (**the SAT solver itself is an external crate**), `rattler_libsolv_c` (vendored C, needs `cc`), `jiff`, `itertools`, `url` |
| memorizable standard | **No, and that is its appeal** — conda `MatchSpec` syntax, build-string matching, version-ordering with epochs/`post`/`dev`, virtual packages, channel priority, `min-age`, `extras`/conditional deps are ecosystem conventions with no RFC |
| objects per scenario | 5: `SolverTask` → `SolverRepoData`/`RepoDataRecord` → `SolverImpl` (`resolvo::Solver`) → `CondaDependencyProvider` → `SolveStrategy`/`ChannelPriority` |
| difficulty | would be **hard** if the crate contained the solver |
| decision | **reject** — the pure-Rust portion is below the LOC gate, the actual resolution algorithm is delegated to the published `resolvo` crate, and the test harness drags in an unpublished `tools` crate that needs `bindgen`/libclang and `reqwest` |
| note | `rattler_conda_types` (the type layer where MatchSpec/Version live) fails a different gate — see rejects |

---

## Measured rejects

| crate / repo (HEAD) | src LOC | tests | fatal metric |
|---|---|---|---|
| `rattler_conda_types` (rattler `ba83a78f`) | 8 973 | **232 inline** in 40 `#[cfg(test)]` blocks vs **25 external** in 3 files; 7 884 lines of inline tests | inline tests dominate ~90 %; 82 `insta` calls inside `src/` — the suite dies with the rewritten `src/` |
| `oxc_resolver` v11.24.2 (`9bfa27ab`) | **6 228** (excluding `src/tests/`, which is **8 558 LOC / 291 inline tests**) | only **27 external** in 3 files (427 LOC) | **corrects `CANDIDATES_MULTILANG.md` rank 2**: this crate's suite lives *inside* the crate; plus Node resolution + `exports` conditions are a public, memorized standard |
| `tracing-subscriber` v0.3.23 (`d9d4c542`) | 10 105 (3 683 lines inline tests cut) | **145 inline** in 17 blocks vs 118 external in 35 files | inline tests dominate; `fmt` layer tests are exact-string comparisons; needs the in-workspace `tracing-mock` |
| `gix-diff` v0.66.0 | 3 866 | 89 external | **63 snapshot asserts (62 `insta::assert_snapshot`) for 89 tests** — snapshot-dominant |
| `gix-config` v0.59.0 | 7 293 | 281 external in 39 files (+101 inline, 26 snapshot asserts) | **not judged here** — a parallel screen (`gix-config-screen`) owns this crate; numbers included so the two reports can be diffed |
| `ratatui-core` (`ff2d5c6`) | 6 237 | **497 inline** in 43 blocks vs **5 external** | tests are entirely in-crate (10 428 lines of them) |
| `alacritty_terminal` (`7dd7b5b`) | 6 297 | 135 inline vs **1 external** (a golden `ref.rs` replay) | same, plus golden recordings |
| `trustfall_core` (`6594dda`) | 15 148 | **0 external**, 100 inline | file-driven `.ron` corpora via a proc-macro; no integration surface |
| `taffy` (`d2db537`) | 17 053 | 6 087 "external" tests — **generated** into `tests/generated/` by `scripts/gentest` from the WPT/Yoga corpora | generated golden suite + CSS flexbox/grid is a public standard |
| `apollo-federation` (router `e294afc`) | **132 597** | 41 523 test LOC | ~9× the size ceiling |
| `chalk-solve` (`627409a`, last commit 2026-02) | 9 813 | **0 tests in the crate**; all 65 test files (15 294 LOC) live in the root `chalk` crate and go through the `chalk-integration` DSL | not deliverable as one `[patch.crates-io]` crate; repo dormant |
| `mdBook` (`641d06a`) | largest member `mdbook-html` 3 557; root crate 1 123 | 33 test files at root only | fragmented into sub-3.5k crates after the 2026 split |
| `vrl` (`eae43fe`) | **73 735** | 436 inline vs 5 external | size + inline tests |
| `sqlparser` (datafusion-sqlparser-rs `7076b79`) | **52 426** | 1 400 external (excellent hygiene!) | size only — worth revisiting **if** a spec can be carved per-dialect |
| `taplo` (`08f343b`) | 6 764 | **0 external**, 104 inline | no integration surface |

---

## Ranking of keeps

| rank | crate | predicted difficulty | independent tasks it can yield | one-line rationale |
|---|---|---|---|---|
| 1 | **`gix-ref`** | **hard** | **2** — (a) store + lookup: loose/packed precedence, overlay iteration, namespaces, `follow`/`peel` with cycle abort; (b) transactions: `prepare/commit`, lock protocol, `PreviousValue` preconditions, packed-refs transactions, reflog writing | cleanest suite screened (144 external tests, 3 snapshot asserts), no reciteable spec for the store semantics, 7 objects per scenario |
| 2 | **`gix-odb`** | **hard** | **1–2** — (a) dynamic `Store`/`Handle` refresh & index-slot policy; (b) loose store + alternates chain + write/verify | purest lazily-resolved-graph in the set; 0 snapshots; small fixtures (5.8 MB) |
| 3 | **`gix-index`** | medium-hard | **1** | round-trip equivalence over extensions is the whole crate, but `gitformat-index(5)` is public — ceiling capped |
| 4 | **`gix-pack`** | medium-hard | **1–2** (decode+delta-tree / index+multi-index write) | strong "two strategies must agree" property; format is publicly specified and the crate is 8.1k LOC → must be carved |
| 5 | **`apollo-compiler`** | medium (risk: easy) | **2** (schema+extensions+diagnostics / executable+introspection+serde) | good object count and clean external suite, but GraphQL validation is the most memorizable ruleset here; spec must avoid the rule list |
| — | `gix-merge` | hard (shape) | 0 today | deferred purely on 26 test functions + a Cartesian golden baseline |
| — | `toml_edit` | medium-easy | 1 | deferred: public standard + conformance corpus + snapbox snapshots |

**Workspace-level view.** gitoxide is the only workspace here that can carry several *separately specified* tasks: `gix-ref`, `gix-odb`, `gix-index`, `gix-pack` (+ `gix-config` if the parallel screen keeps it) are independent crates with their own published versions, their own fixture archives, and no shared oracle. Practical caution: they share one domain and one fixture harness (`gix-testtools`), so their difficulty is likely **correlated** — take at most 2–3 into any single scoring batch, and pair them with a non-git task. apollo-rs can carry 2 carves of `apollo-compiler`; every other repo screened is single-task at best.

## Open verification items (need `spec2repo-rust:latest`, not available in this shell)

1. `cargo nextest list -p gix-ref -p gix-odb -p gix-index -p gix-pack` — confirm the counted `#[test]` attributes match listed cases (feature-gated tests may differ) and that fixture extraction works with **no network and no `git` binary invocation**; if a `make_*.sh` fallback fires, `git`+`bash` become hard runtime deps.
2. `gix-testtools` version lag: crates.io has **0.19.0**, the tree has **0.20.0**. The oracle must pin 0.19.0 or vendor the tool.
3. Confirm `[patch.crates-io]` delivery: every `gix-*` sibling is published at the exact version the manifests request, so unlike `guppy` **no feature has to be dropped** — verify by building `gix-ref` with all path deps rewritten to crates.io.
4. Fixture payload sizes to ship with each oracle: gix-ref 23 MB, gix-merge 15 MB, gix-odb 5.8 MB, gix-index 3.3 MB, gix-pack 3.2 MB, apollo-compiler `test_data` 3.2 MB.
5. `apollo-compiler` uses `serial_test` for `FileId::reset` — check it under a parallel `nextest` profile before counting those tests.

---

## 10. `crop` — B-tree rope (Stage-1 **SELECTED**, 2026-08-22)

Added after the 2026-08-21 sweep. Unlike sections 1-9 above, every number here was
**executed** in `spec2repo-rust:latest` (rustc 1.95.0, cargo-nextest), not line-counted.
Full screen: `wip/_stage1/crop.md`. Working dir: `wip/crop-rope-001/`.

| field | content |
|---|---|
| name / crate | `crop` — single package, **no workspace** |
| repo | https://github.com/noib3/crop |
| version / release | `Cargo.toml` says 0.4.3, but **HEAD `d0234ce` (2026-03-02) is 10 commits past tag `0.4.3` `a2a4ea9` (2025-04-25)** and the version was never bumped. Pin the commit, never the version string |
| popularity | 320 stars / 19 forks; 277 994 crates.io downloads (87 516 in 90 days) |
| src LOC | **8 253** across 20 files (non-blank, non-comment, `#[cfg(test)] mod` brace-matched out; raw 12 967). Split 3 728 generic B-tree (`src/tree/`) + 4 525 rope layer (`src/rope/`) |
| test functions | **110 external** declared in 10 integration targets + **16 inline**. Runnable under the pinned feature set: **102 external + 4 inline = 106** (12 of the 16 inline sit behind the private feature `small_chunks`), plus 3 `#[ignore]` |
| private reach | **cleanest audit in the round.** Every `use` in `tests/` is one of: `crop::Rope`, `crop::{Rope, RopeBuilder}`, `common::*`, `rand::{Rng, SeedableRng}`, `std::{borrow::Cow, env}`. Two library symbols, zero private imports, zero hard-coded internal layout — even though `#[doc(hidden)] pub mod tree` and `pub use rope::{GapBuffer, GapSlice, StrSummary}` are reachable |
| assertion style | 348 plain `assert*`, **0 snapshot asserts** (`insta`/`expect_test`/`assert_*_snapshot`/`expect![` absent from `Cargo.toml`, `tests/`, `src/`; the lone grep hit is the word "in**sta**nces" at `src/tree/traits.rs:125`), 0 `macro_rules!` test generation |
| fixtures / offline | `tests/common/`: 6 committed plain `.txt`, 1.8 MB. **No archives, no generators, no `Command::new`, no `git`, no network, no daemon.** `Cargo.lock` is **not** committed (`.gitignore`) — delivery must generate and pin one |
| external deps | required `str_indices 0.4`; optional `serde`, `unicode-segmentation`. dev: `rand 0.9`, `rand_chacha 0.9`, `ropey 1.6`, `serde_json`, `serde_test`, `bincode 2`, `criterion 0.7`. edition 2024, MSRV 1.85 |
| memorizable standard | **No.** No standards body, no conformance corpus, no second implementation with matching semantics, and no doc-examples-as-oracle harness (contrast koto). The recitable part is "a rope is a balanced tree of string chunks"; the suite tests gap-buffer leaves with a movable gap, CRLF-aware line metrics, `line_slice` vs `byte_slice` divergence at terminators, graphemes straddling chunk edges, UTF-16 offset conversion. Caveat: 2 234 rustdoc lines / 116 doctest examples on docs.rs, and 0.4.3 predates the cutoff by 11 months |
| objects per scenario | **~4** — `Rope` → `RopeSlice` → `iter::{Bytes, Chars, Lines, RawLines, Chunks, Graphemes}` → metric conversion. Mid-band: above `koto_format` (1), below `gix-ref` (7+). Difficulty is depth-in-one-object, not breadth |
| difficulty | **unmeasured — the open question.** `assert_invariants()` runs throughout, which punishes wrong tree balance rather than merely wrong output. But with `chunk-len` removed nothing external observes chunking, arity, or depth, so a `String`-backed `Rope` would pass a large share of the 102 tests. Probe before spec work |
| **pinned config** | `--features graphemes,serde,utf16-metric` + `SEED=42`. **Never `chunk-len`. Never `--all-features`** (private `small_chunks`/`arity_4`/`deep_trees`/`dp` change tree arity) |
| verified result | **106 tests run: 106 passed, 3 skipped** — identical on `SEED=1/42/999`, in `spec2repo-rust:latest` *and* in `spec2repo-agent-rust:latest` under `--network=none`. Tag `0.4.3` is also fully green at 116/116 |
| decision | **SELECTED — 1 task** (`crop-rope-001`), the 10th and final Rust slot |
| yield | **1, not 2.** All 102 external tests route through `Rope::from(&str)` + byte/char/line indexing; any split yields two specs with ~90 % overlapping prerequisites — the redb failure mode. The clean seam in `tests/` is a seam in the test files, not in the delivery unit |
| **blockers found (all fixed pre-selection)** | ① **`chunk-len` is a live upstream bug.** With it enabled, `crop::slicing rope_from_slice` fails deterministically on all 5 seeds tried: `attempt to subtract with overflow` at `src/rope/iterators.rs:117` (`self.len -= next.is_some() as usize`) via `Rope: PartialEq<RopeSlice>` → `chunks_eq_chunks` → `Chunks::next`. Reduced independently: `RopeSlice::chunk_len()` is correct (0/6000 mismatches) but `Rope::from(RopeSlice)` under-reports `chunk_len()` by one in 460/6000 cases, so `num_chunks` summary maintenance on the builder path is wrong. Debug-only symptom — release passes with overflow checks off, silently violating `ExactSizeIterator`. ② **`criterion` is not in the agent image's offline registry**, so `--network=none` dies at `cargo metadata` before compiling anything; fixed by carving the 7 `[[bench]]` targets + `criterion` dev-dep (benches are outside the delivery contract anyway) — **no image rebuild needed**. ③ **`tests/common/mod.rs::seed()` falls back to `rand::random()`** when `$SEED` is unset — pinning `SEED` is mandatory, not hygiene |
| risks | ① all-or-nothing oracle compile (112 `pub fn` / 23 `pub struct`, but the compile-critical surface is only `Rope`/`RopeBuilder`/`RopeSlice`/`iter` since tests import 2 symbols) — far below redb, still the top residual; ② difficulty may ceiling out (risk row above); ③ `tests/slice_indexing.rs` runs 2 **differential tests against `ropey 1.6`**, so a competing rope crate is in the oracle's dependency set and must be version-pinned; ④ ~9 s of the 8.6 s wall clock is 6 randomised tests |
| scope_plan | Deliver package `crop` @ `d0234ce`, whole `src/`. Carve out: 7 `[[bench]]` + `benches/` + `criterion`, the `chunk-len` feature and its `[[test]] name = "chunk_len"`, `fuzz/`, `examples/`. Ship `tests/common/` (1.8 MB) + a pinned `Cargo.lock`. Oracle = 102 external tests in 9 targets. Contract surface = `Rope`, `RopeBuilder`, `RopeSlice`, `pub mod iter` |

---

# Rust 候选筛查 · 第二轮 (S1 screening, 2026-08-22)

> Brief: find candidates **not already in this file** (sections 1–10 and the reject table above
> are settled and untouched). Repos were shallow-cloned into `/tmp/rust_scout2/` and counted with
> the same `/tmp/rust_scout/metrics.py`; the counting rules in the header table apply unchanged.
> As before: **no `cargo`/`tokei` on this host, so LOC is a line counter, and no test was executed.**
>
> **One correction to the method.** `metrics.py` counts `#\[test\]|#\[tokio::test`, which **misses
> `#[test_log::test]`, `#[rstest]`, `#[test_case(..)]`, `#[apply(..)]`**. A broader counter
> (`/tmp/recount.py`) was run over every candidate below; where the two disagree both numbers are
> given. The gap mattered for two crates (`fjall`, `rustic_core`) and changed neither verdict.
>
> **gitoxide is exhausted.** The whole workspace (66 `gix-*` crates + the `gix` facade) was swept.
> After the eight crates already in this file, **no unscreened `gix-*` crate clears both gate 1 and
> gate 2**. Best remaining, as `external tests / raw src lines` (raw = un-stripped line count):
> `gix-url` 148/2 065, `gix-revision` 112/1 762, `gix-dir` 79/1 730, `gix-refspec` 76/1 336,
> `gix-discover` 69/1 280, `gix-pathspec` 65/1 248, `gix-filter` 59/3 010, `gix-blame` 17/3 131,
> `gix-status` 32/2 907. The facade crate `gix` has 455 external tests but 32 739 raw src lines and
> is the whole ecosystem's public front end. Further Rust supply has to come from outside gitoxide.

Repo HEADs used: `lsm-tree aba7320 (2026-08-09)`, `automerge 47908d6 (2026-08-17)`,
`egglog 171ebc8 (2026-08-20)`, `oso 7292df0 (2025-02-26)`, `config-rs 73703f1 (2026-08-20)`,
`salsa 546bc5d (2026-08-21)`, plus the reject-table repos listed in their rows.

---

## 11. `lsm-tree` — log-structured merge tree storage engine

| field | content |
|---|---|
| name / crate | `lsm-tree` — single package, no workspace |
| repo | https://github.com/fjall-rs/lsm-tree |
| version / release | **3.1.9, published 2026-08-09** (crates.io `max_version` 3.1.9); HEAD `aba7320`, 2026-08-09 — tree and release are in step |
| src LOC | **16 807** across 134 files (6 443 lines of inline tests removed) |
| test functions | **199 external** by the narrow count / **205** by the broad count, spread over **102 files in `tests/`, i.e. 102 separate integration targets** (`tests/blob_*.rs`, `tests/tree_*.rs`, `tests/compaction_*.rs`, …; densest are `ingestion_api.rs` 12, `tree_drop_range.rs` 11, `static_iterators.rs` 10). Inline: **251** in 56 `#[cfg(test)]` blocks |
| private reach | **clean, and unusually narrow.** Every `use` in `tests/` resolves to one of **11 public symbols**: `get_tmp_folder`, `AbstractTree`, `Config`, `SeqNo`, `SequenceNumberCounter`, `Guard`, `Slice`, `KvSeparationOptions`, `AnyTree`, `Result`, `compaction::PullDown` (plus `test_log::test` in 91 files and `fs_extra`/`xxhash_rust` in 3). `#[doc(hidden)] pub` internals exist in `src/lib.rs` but **no test touches them** |
| assertion style | **1 251 plain `assert*`, 0 snapshot asserts** (no `insta`, no `expect-test`, no `snapbox` anywhere in `Cargo.toml`/`tests/`) |
| fixtures / offline | `tests/` **616 KB**, `test_fixture/` **32 KB** (`v1_tree`, `v1_tree_corrupt` — two committed on-disk trees for the format-compat/corruption tests). **No archives, no generator scripts, no `Command::new`, no network, no daemon.** Everything else is built in a `tempfile` dir at runtime. Two files call `sleep` (`tree_reload.rs`, `ingestion_invariants.rs`) |
| external deps | `byteorder-lite`, `byteview ~0.10.1`, `crossbeam-skiplist`, `enum_dispatch`, `interval-heap`, `log`, `quick_cache`, `rustc-hash`, `self_cell`, **`sfa ~1.0.0`**, `tempfile`, `varint-rs`, `xxhash-rust`; optional `bytes`, `lz4_flex`. `sfa` is the author's own sibling crate but is **published on crates.io at 1.0.0 (verified via the crates.io API)**. dev: `criterion 0.8`, `fs_extra`, `nanoid`, `rand 0.9`, `strum`, `test-log`. **All crates.io, pure Rust, no C toolchain, no git deps.** edition 2021, MSRV 1.90 (image has 1.95) |
| memorizable standard | **No.** "LSM tree" as a *concept* is in every model's training set, but nothing here is a published standard: the level manifest and `Version`/free-list format, the disjoint-run bookkeeping, the leveled/FIFO/`PullDown` compaction triggers, key–value separation (`KvSeparationOptions`) with blob-file GC watermarks and relink-on-major-compaction, weak deletes, TTL eviction, `SeqNo`-based snapshot reads — all of it is this library's own invention, and there is no second implementation with matching observable semantics |
| objects per scenario | **6+** for "write, flush, compact and read back through a snapshot with blobs enabled": `Config` → `AnyTree`/`Tree` (`AbstractTree`) → memtable → table/segment writer → `LevelManifest`/`Version` → `compaction::{Leveled, Fifo, PullDown}` → blob file + GC watermark → `SequenceNumberCounter` + `SeqNo` snapshot read → `Guard`/`Slice` |
| difficulty | **hard — and measurably so.** The external suite does not just check values, it checks **physical structure**: 121 `.table_count(…)`, 86 `.blob_file_count(…)`, 28 `.approximate_len(…)`, 6 `.l0_run_count(…)`, 3 `.version_free_list_len(…)` assertions. A `BTreeMap`-backed fake returns the right values and still fails, which is the direct antidote to the *"更笨的数据结构分更高"* failure mode recorded for `crop`. The shape is a factor product (compaction strategy × blob separation × snapshot seqno × recovery) plus an equivalence judgement (post-recovery tree must equal pre-crash tree) |
| decision | **keep — rank 1 of this round** |
| risks | ① 16.8 k LOC is above the ~15 k working ceiling → **carve advisable** (natural seams: blob/KV-separation layer, or compaction strategies); ② `AbstractTree` is a ~60-method trait and the crate exposes 563 `pub fn` → all-or-nothing oracle compile (redb-shaped), mitigated by the fact that `tests/` only names 11 symbols; ③ **102 integration targets** means 102 test binaries to link — measure wall clock before committing; ④ `criterion 0.8` is a dev-dep and was **not** in the agent image's offline registry for `crop` — carve the 9 `[[bench]]` targets the same way; ⑤ 2 tests use `sleep`, so they are wall-clock sensitive |
| open items | run `cargo nextest list` in `spec2repo-rust:latest` to confirm 199/205 against real cases; confirm the `v1_tree` fixture still loads at 3.1.9; check `lz4`/`bytes_1`/`metrics` feature interactions and pin a feature set |

## 12. `automerge` — JSON-like CRDT document

| field | content |
|---|---|
| name / crate | `automerge` (workspace member `rust/automerge` of automerge/automerge) |
| repo | https://github.com/automerge/automerge |
| version / release | **0.11.0**; HEAD `47908d6`, 2026-08-17 |
| src LOC | **37 389** across 148 files (7 203 lines of inline tests removed). Raw-line breakdown of the big directories: `op_set2/` 12 819, `storage/` 6 585, `columnar/` 3 762, `automerge/` 3 038, `iter/` 2 808, `transaction/` 2 305, `legacy/` 1 555, `sync/` 1 399 |
| test functions | **289 external** in 10 files: `test.rs` 140, `batch_insert.rs` 46, `diff_marks.rs` 36, `text.rs` 18, `block_tests.rs` 18, `text_encoding.rs` 15, `rich_text_fuzz_crash.rs` 9, `test_save_load_orphans.rs` 3, `convert_string_to_text.rs` 3, `test_mark_patches.rs` 1. Inline: **217** in 65 blocks |
| private reach | clean — integration targets, `pub` surface only |
| assertion style | **515 plain asserts, 0 snapshot asserts** |
| fixtures / offline | `tests/` 396 KB total, including `tests/fixtures/` and `tests/fuzz-crashers/` (committed bytes). **No `Command::new`, no network** |
| external deps | `cfg-if`, `flate2` (zlib-rs backend, **pure Rust**), `getrandom`, `hex`, **`hexane 1.0.0-alpha.5`** (path dep — **published on crates.io, verified**), `itertools`, `leb128`, `rustc-hash`, `serde`, `sha2 0.11.0-rc.5`, `smol_str`, `thiserror`, `tinyvec`, `tracing`, `unicode-segmentation`, `rand`. dev: **`automerge-test`** (path dep — **published 0.11.0, verified**), `maplit`, `pretty_assertions`, `prettytable`, `proptest`, `serde_json`, `test-log`, `tracing-subscriber`. edition 2021, MSRV 1.90 |
| memorizable standard | **No.** There is a written Automerge binary-format document, but nothing about it is recitable from memory, and the *semantics* — actor-id ordering, list-index resolution under concurrent insert/delete, marks and rich-text spans, block boundaries, `save`/`load` column compression, the sync protocol's Bloom-filter handshake — are the project's own invention with no second conforming implementation to crib from |
| objects per scenario | **6+**: `AutoCommit`/`Automerge` → `Transaction` → `ObjId`/`Prop`/`ScalarValue` → `Change`/`ChangeHash` graph → `Mark`/`Patch`/`PatchLog` → `save()`/`load()` → `sync::{State, Message}` |
| difficulty | **hard, and the purest "two views must agree" shape in either round** — `merge(A,B)` and `merge(B,A)` must be indistinguishable, `load(save(d))` must equal `d`, and the patch stream produced incrementally must equal the diff computed between two heads. That is exactly the guppy/gix-ref shape the brief asks for |
| decision | **keep with carve required — rank 2. The objection is size, not shape**: 37.4 k LOC is 2.4× `apollo-compiler`, the biggest keep so far, and 4× a comfortable spec |
| risks | ① size — a whole-crate spec is out of the question; the plausible carve is "the document/transaction/merge layer, with the columnar storage layer supplied by the published `hexane`" but that boundary must be verified before spec work, because `storage/` + `columnar/` is ~10 k LOC still inside the candidate; ② `proptest` is a dev-dep → seed pinning mandatory; ③ `rand`/`getrandom` in the *runtime* deps means actor ids are random unless the tests pin them — check before counting the 289; ④ `slow_path_assertions` feature changes invariant checking |

## 13. `egglog` — e-graph + Datalog language

| field | content |
|---|---|
| name / crate | `egglog` (workspace member of egraphs-good/egglog) |
| repo | https://github.com/egraphs-good/egglog |
| version / release | **3.0.0**; HEAD `171ebc8`, 2026-08-20 (tree version and crates.io `max_version` both 3.0.0) |
| src LOC | **20 701** across 48 files (1 904 lines of inline tests removed) |
| test functions | **157 external** across 18 `#[test]`-style targets: `integration_test.rs` 50, `api_fact_ops.rs` 21, `container_rebuild.rs` 16, `typed_primitive.rs` 13, `api_query.rs` 10, `api_introspection.rs` 9, `no_panic.rs` 8, `test_command_macros.rs` 7, `naive_unstable_fn_via_global.rs` 4, `api_proofs.rs` 4, `globals_warning_tests.rs` 3, then 7 files with 1–2. Inline: **61** in 11 blocks |
| private reach | clean (42 `use egglog::…` at module level) |
| assertion style | 205 plain asserts and **6 snapshot asserts** (4 `insta::assert_snapshot`, 2 `assert_snapshot`) **in the retained targets** — after carving the 19th target, `tests/files.rs`, which is `harness = false`, `required-features = ["bin"]`, and drives **101 committed `.egg` programs through libtest-mimic with insta snapshots**. That target is the golden corpus; it comes out cleanly because it is gated behind a feature and a separate harness |
| fixtures / offline | `tests/` is 7.5 MB, **almost all of it the `.egg`/`.csv` corpus belonging to the carved `files` target**. No network, no `Command::new` |
| external deps | 6 in-workspace siblings — `egglog-core-relations`, `egglog-ast`, `egglog-bridge`, `egglog-numeric-id`, `egglog-add-primitive`, `egglog-reports` — **all published on crates.io at 3.0.0 (verified via the API, updated 2026-08-19)**; plus `egraph-serialize`, `hashbrown`, `im-rc`, `indexmap`, `log`, `num`, `ordered-float`, `rustc-hash`, `smallvec`, `thiserror`, `web-time`, `dyn-clone`, `enum-map`, `csv`, `serde_json`. dev: `divan`, `glob`, `libtest-mimic`, `testing_logger`, `insta`, `serial_test`. All crates.io, pure Rust |
| memorizable standard | **No.** egglog is its own language (2023 PLDI); there is no standard, no conformance suite outside this repo, and no second implementation. Caveat: it is an academic artifact with public papers and a public tutorial, so *the ideas* are describable — but the concrete surface (merge functions, `subsume`, rulesets and scheduling, containers, proof terms, `check`/`fail` semantics) is not recitable |
| objects per scenario | **5+**: `EGraph` → parsed `Command`s (`egglog-ast`) → typechecked/desugared program → ruleset + scheduler → `Function`/merge-fn + rebuilding → `extract`/proof term → `SerializedEGraph` |
| difficulty | **hard shape**, with one structural caveat: the relational e-matching core lives in the **published siblings** `egglog-core-relations` + `egglog-bridge`, so the candidate crate is the front end (typecheck, desugar, command interpretation, primitives, containers, proofs, extraction) over a given engine |
| decision | **keep with conditions — rank 3.** The spec must draw the delegation line explicitly ("the relational engine is a published dependency; you implement the language layer"), or this repeats the `rattler_solve` failure mode where the interesting algorithm turned out to be someone else's crate |
| risks | ① delegation line (above) — verify how much of rebuilding/congruence lives in `egglog-bridge` before writing the spec; ② `serial_test` interacts with a parallel nextest profile (same hazard as `apollo-compiler`); ③ 20.7 k LOC → carve; ④ six sibling crates must all be pinned at 3.0.0 |

## 14. `polar-core` — the Polar authorization language

| field | content |
|---|---|
| name / crate | `polar-core` (workspace member of osohq/oso) |
| repo | https://github.com/osohq/oso |
| version / release | **0.27.3** — crates.io last updated **2024-01-13**; repo HEAD `7292df0`, **2025-02-26**. **Dormant** |
| src LOC | **11 192** across 37 files (7 389 lines of inline tests removed) |
| test functions | **84 external**: 83 in `tests/integration_tests.rs` + 1 in `tests/serialize.rs`, with `tests/mock_externals.rs` as an in-`tests/` helper module. Inline: **200** in 30 blocks — i.e. ~70 % of the crate's own tests are inline and die with the rewritten `src/`, but the 84 that survive clear the gate |
| private reach | clean — the helper is inside `tests/`, and `polar_core::…` is the only library path |
| assertion style | **91 plain asserts, 0 snapshot asserts** |
| fixtures / offline | **none needed** — policies are inline `indoc!` strings. No files, no archives, **no `Command::new`, no network** |
| external deps | `lalrpop-util`, `serde`, `indoc`, `strum_macros`; **build-dep `lalrpop 0.19.9`** (published, pure Rust, but a build-time parser generator, and `src/polar.lalrpop` is inside the rewrite scope); dev: `criterion 0.3`, `permutohedron`, `pipe`, `pretty_assertions`, `maplit`, `serde_json`. All crates.io, no C toolchain |
| memorizable standard | **No.** Polar is oso's own logic language. oso's docs were public and popular, so partial recall is possible, but there is no spec document and no second implementation |
| objects per scenario | **5+**: `Polar` → `Query` → the `QueryEvent` stream (`ExternalCall`/`ExternalIsa`/`Result`/`Debug`, driven by the test's `MockExternal`) → `KnowledgeBase` + rule index → `partial`/`inverter` (constraint stores, `Operation`) → `Trace` |
| difficulty | **medium-hard** — a real logic engine: unification with variables and patterns, rule specialisation and ordering, negation via an inverter, and partial evaluation that returns *constraint sets* rather than booleans. The host-language callback protocol (the engine yields events and the caller answers) is a genuine lazily-resolved graph |
| decision | **keep with conditions — rank 4** |
| risks | ① **dormant**: no release in ~2.5 years, HEAD 18 months old — no upstream to check behaviour against, and the pinned `lalrpop 0.19.9` may not build on rustc 1.95 (untested here, must be verified first); ② `tests/integration_tests.rs` glob-imports `error::*` and `terms::*` and uses four exported macros (`sym!`, `term!`, `value!`, `values!`), so **every error-variant name and macro shape is compile-critical** — a very wide all-or-nothing surface and a lot of the answer is over-specified by the imports alone; ③ the candidate must author a LALRPOP grammar — the same odd shape that made `commons-jexl` unattractive in the Java list; ④ 84 tests in essentially one file means one target, so a compile failure zeroes everything |

## 15. `config` (config-rs) — layered configuration with precedence

| field | content |
|---|---|
| name / crate | `config` — single package |
| repo | https://github.com/rust-cli/config-rs |
| version / release | HEAD `73703f1`, 2026-08-20; 18.2 M recent downloads |
| src LOC | **3 463** across 25 files (266 lines of inline tests removed) — **the smallest crate that clears gate 1 in either round** |
| test functions | **155 external** in a single `tests/testsuite/` target (24 files). Inline: 15 |
| private reach | clean |
| assertion style | 349 plain asserts vs **56 `assert_data_eq!` (snapbox)** → **14 %**. Not snapshot-dominant, but not "a handful" either |
| fixtures / offline | **offline confirmed by grep**: `warp`, `reqwest` and `notify` appear in `[dev-dependencies]` but **only `examples/` uses them**; nothing under `tests/` references them. The 6 `#[tokio::test]`s in `tests/testsuite/async_builder.rs` drive an in-process `AsyncSource`. Small in-tree fixture files only |
| external deps | the format parsers are **delegated to published crates** (`toml`, `json5`, `yaml`, `ini`, `ron`) — the candidate implements the layering, not the parsing. dev: `serde`, `float-cmp`, `chrono`, `tokio`, `glob`, `temp-env`, `log`, `snapbox` |
| memorizable standard | **No standard exists** — the precedence rules, path expressions (`a.b[0]`), env-var separators/prefix handling, case folding, defaults-vs-overrides ordering and `Value` origin tracking are config-rs's own. But the *concept* is small and universally familiar |
| objects per scenario | 4: `ConfigBuilder` → `Source`/`AsyncSource` → `Value` + `ValueKind` + origin → path expression → `Config::try_deserialize` |
| difficulty | **medium-easy — the top calibration risk of this round.** Small surface, one saturated concept, parsing delegated. This is the profile that produced 55–70 % in batch-15 |
| decision | **keep as reserve — rank 5.** Use only if one of ranks 1–4 falls over; do not spend a spec-and-oracle cycle on it while better shapes are unscreened |

## 16. `salsa` — incremental recomputation framework *(conditional: fails gate 3 as written)*

| field | content |
|---|---|
| name / crate | `salsa` (salsa-rs/salsa) |
| repo | https://github.com/salsa-rs/salsa |
| version / release | **0.28.2**; HEAD `546bc5d`, 2026-08-21 |
| src LOC | **13 727** across 54 files (546 lines of inline tests removed) — comfortably inside the ceiling |
| test functions | **248 external** across **117 top-level integration targets** in `tests/`, plus 21 in the `tests/parallel/` target. This *excludes* the trybuild drivers `compile_fail.rs` / `compile_pass.rs` and their 41 + 7 + 5 golden `.stderr` inputs, which must be carved. Inline: 20 |
| private reach | clean |
| assertion style | **⚠ this is the blocking measurement.** 408 plain asserts vs **167 `expect![` calls**, and per *function*: **96 of 248 external tests (39 %) contain an `expect![`**. They are inline expect-test blocks asserting the recorded salsa event log (`db.assert_logs(expect![...])`) — i.e. the exact `Debug` rendering of `Event`/`DatabaseKeyIndex`. That is over-specification, and it is concentrated in exactly the tests that observe incrementality; dropping them would leave a suite that a **non-incremental implementation passes** |
| fixtures / offline | none — no files, no network, no `Command::new` |
| external deps | all crates.io (`boxcar`, `crossbeam-*`, `hashbrown`, `hashlink`, `indexmap`, `intrusive-collections`, `parking_lot`, `portable-atomic`, `rustc-hash`, `smallvec`, `thin-vec`, `tracing`, `typeid`, `inventory`, `rayon`). dev: `expect-test`, `trybuild`, `test-log`, `annotate-snippets`, `rustversion`, `serde_json`, codspeed-`divan` (bench — carve) |
| **delivery blocker** | the crate depends on **`salsa-macro-rules 0.28.2`** and **`salsa-macros 0.28.2`** (both path deps with published versions). Those macro crates expand user code into references to `salsa::plumbing::…`, so **keeping the published macros pins salsa's entire internal architecture**: the candidate would have to reproduce dozens of internal type and function signatures exactly. Either deliver all three crates, or accept an oracle whose compile surface is the internal plumbing API |
| memorizable standard | **No — the best gate-6 profile of the round.** Revisions and durability levels, backdating, cycle recovery by fixpoint iteration, accumulators, LRU eviction of memos, and "a query re-executes iff a dependency's *value* changed, not iff its revision changed" are salsa's own inventions. rust-analyzer's use of it is famous; the mechanism is not recitable |
| difficulty | **hard** — a lazily-resolved dependency graph whose *recomputation trace* is the observable, which is precisely the guppy/gix-ref shape |
| decision | **defer.** Shape says rank 1; gate 3 says reject. It needs two explicit decisions before any spec work: (a) three-crate delivery or a plumbing-API contract, and (b) whether 39 % expect-driven tests are tolerable given they carry the incrementality signal |

---

## Measured rejects — second round

| crate / repo (HEAD) | src LOC | external tests | fatal metric |
|---|---|---|---|
| `jj-lib` (jj-vcs/jj `9d905d5`) | **40 088** (21 860 lines of inline tests cut) | 479 in 38 files, **130 snapshot asserts** | dev-dep **`testutils` is `publish = false`** and is in the retained test path (gate 5); plus 40 k LOC and `insta`. Best-shaped VCS candidate outside gitoxide, killed by delivery |
| `resolvo` (mamba-org `7540590`, v0.12.0) | 7 315 | 98 in 7 files | **85 snapshot asserts vs 47 plain** — insta-dominant (gate 3) |
| `sled` (spacejam `e449d17`, 1.0.0-alpha.124) | 5 870 | 125 in 17 files, 0 snapshots | three independent failures: **`zstd` pulls a C toolchain** (gate 5); `tests/crash_tests/` re-exec child processes (gate 4); and the retained tests are quickcheck model comparisons **against a `BTreeMap`**, so a naive in-memory impl passes — the crash tests that would discriminate are the ones that spawn. Also `[profile.test] panic = "abort"` |
| `nickel-lang-core` (tweag) | 33 521 | **20** | the integration suite is `test-generator`-expanded `.ncl` files, not `#[test]` functions; plus 33 k LOC |
| `nextest-runner` (nextest-rs) | 40 995 (28 885 inline-test lines cut) | **18** | inline-dominant (442 inline) |
| `nextest-filtering` (same repo) | **2 233** | 31 | below the LOC gate — a pity, the filterset DSL is genuinely bespoke |
| `rhai` (rhaiscript) | **45 825** | 394, 0 snapshots | size (3× ceiling); and the language is fully documented in the public Rhai Book |
| `fjall` (fjall-rs) | 6 349 | **49** (broad count; narrow count 38) | below the 60-test gate — the sibling `lsm-tree` carries this ecosystem's suite |
| `rustic_core` (`crates/core`) | 16 089 | **59** (broad count; narrow 23) + 14 snapshot asserts | one test short of the gate |
| `cedar-policy` / `cedar-policy-core` (cedar-policy/cedar) | 21 685 / **59 472** | 14 external / **no `tests/` directory at all** | 642 + 1 753 inline tests; the suite dies with `src/` |
| `surrealkv` (surrealdb) | 44 161 | **no `tests/`** | 683 inline |
| `IronCalc/base` | **96 237** | **no `tests/`** | 2 310 inline; also size |
| `starlark` (facebook/starlark-rust) | **68 348** | **no `tests/`** | 1 059 inline; also a public language spec |
| `rune` (rune-rs, `crates/rune`) | **93 115** | **2** | size + no external suite |
| `moka` (moka-rs) | 12 879 | **13** | inline-dominant (173 inline) |
| `tantivy` (quickwit-oss) | 51 713 | **5** | inline-dominant (1 237 inline) |
| `slatedb` (`slatedb/slatedb`) | 44 337 (76 903 inline-test lines cut!) | **18** | inline-dominant (1 562 inline) |
| `yrs` (y-crdt) | 20 978 | **no `tests/`** | 407 inline |
| `loro` / `loro-internal` (loro-dev) | **2 085** / **52 376** | 507 / 181 | split the wrong way: the crate that owns the 507-test suite is a 2 k-LOC facade (below gate 1), the crate that owns the code is 52 k. No single deliverable clears both gates |
| `nebari` (khonsulabs, `nebari/nebari`) | 9 464 | **no `tests/`** | 63 inline |
| `protox` (andrewhickman) | **2 208** | 42 | below the LOC gate |
| `cacache` (zkat/cacache-rs) | **2 682** | **no `tests/`** | below the LOC gate |
| all remaining `gix-*` + `gix` (gitoxide `227619ad`) | — | — | **workspace swept and exhausted** — see the note at the top of this round |

---

## Ranking — second round

| rank | crate | src LOC | external tests / snapshots | predicted difficulty | one-line difficulty argument |
|---|---|---|---|---|---|
| 1 | **`lsm-tree`** | 16 807 | 199–205 / **0** | **hard** | The suite asserts physical structure — 121 `table_count`, 86 `blob_file_count`, 6 `l0_run_count` — so a `BTreeMap`-backed fake fails; compaction × blob-GC × snapshot-seqno × recovery is a genuine factor product with no published spec |
| 2 | **`automerge`** | 37 389 | 289 / **0** | **hard** | Purest equivalence judgement available: `merge(A,B) ≡ merge(B,A)` and `load(save(d)) ≡ d`, over concurrent-edit index resolution that no standard describes — **but 37 k LOC forces a carve before any spec work** |
| 3 | **`egglog`** | 20 701 | 157 / 6 (after carving the `files` target) | **hard** | Its own language with merge functions, rebuilding, subsumption and rulesets; caveat — the relational engine is a published sibling crate, so the spec must state the delegation line |
| 4 | **`polar-core`** | 11 192 | 84 / **0** | medium-hard | A real logic engine (unification, negation-by-inverter, partial evaluation into constraint sets) driven through a caller-answers-events protocol; discounted for dormancy and a LALRPOP build step |
| 5 | **`config`** (config-rs) | 3 463 | 155 / 56 (14 %) | medium-easy | Clears all six gates but is a small, familiar concept with parsing delegated — hold in reserve; highest saturation risk of the five |
| — | `salsa` | 13 727 | 248 / **96 of 248 tests use `expect![`** | hard (shape) | Best gate-6 profile in either round, but 39 % expect-driven tests and a three-crate plumbing coupling; deferred pending two explicit decisions |

**Portfolio note.** These five are in five unrelated domains (storage engine, CRDT, e-graph language, logic language, config layering) and share no fixture harness, so unlike the gitoxide block their difficulty should be **uncorrelated** — they can go into one scoring batch together. Ranks 1 and 2 are the only ones whose difficulty argument rests on measured evidence rather than on reading the code; if only one spec-and-oracle cycle is available, spend it on `lsm-tree`, which is also the cheapest to deliver (648 KB of fixtures, 11-symbol contract surface, no build script, no C).

## Open verification items — second round (need `spec2repo-rust:latest`, not available in this shell)

1. `cargo nextest list` for `lsm-tree`, `automerge`, `egglog`, `polar-core` — confirm the counted attributes match listed cases under a pinned feature set.
2. `lsm-tree`: carve the 9 `[[bench]]` targets + `criterion` **before** trying `--network=none` (this is exactly what blocked `crop`); then time the 102 integration targets.
3. `automerge`: decide the carve line against `hexane`, and check whether `rand`/`getrandom` make any of the 289 tests seed-dependent.
4. `egglog`: confirm `tests/files.rs` really is the only consumer of the 7.5 MB `.egg` corpus, and check `serial_test` under a parallel nextest profile.
5. `polar-core`: **build it first** — `lalrpop 0.19.9` (2022-era) on rustc 1.95 is unverified, and if it fails the crate is dead on arrival.
6. `salsa`: decide three-crate delivery vs a plumbing-API contract before any further work.

---

## 17. `kdl` (kdl-rs) — document-oriented KDL parser and formatter (Stage-1 **RETIRED**, 2026-09-03)

| field | content |
|---|---|
| name / crate | `kdl` — single package with `tools/*` workspace members outside the task scope |
| repo | https://github.com/kdl-org/kdl-rs |
| version / release | `Cargo.toml` version **6.7.1**, changelog release **2026-05-31**; local HEAD `8b01f4ef83eea6ab399118117a7c02d7d597c4f2` |
| src LOC | **8 569** NBNC Rust LOC in compiled public crate modules by local line count; 10 434 NBNC under `src/` before removing inactive/query and test-heavy regions |
| test functions | **2 active external** integration tests: `tests/compliance.rs::spec_compliance` and `tests/formatting.rs::build_and_format`; **27** tests under `tests/disabled_tests/` are not active integration targets; **111 inline** tests under `src/` |
| test files / corpus | 2 active external Rust test files, 4 disabled Rust files, and 554 KDL corpus files (`321` input `.kdl`, `233` expected `.kdl`) |
| private reach | **clean for active external tests**. Module-level imports use public `kdl::{KdlDocument, KdlError, KdlIdentifier, KdlValue}` or `kdl::{KdlDocument, KdlNode}`. Disabled tests also import public `kdl::...`, but they are not compiled as active integration targets |
| assertion style | Active external surface is one corpus-driver conformance assertion loop plus one exact formatting string assertion. No `insta`/`expect-test`/snapbox snapshot dependency appears, but the compliance target is effectively golden normalization through checked-in files |
| fixtures / offline | Small checked-in corpus under `tests/test_cases/`; no network, daemon, C toolchain, or `Command::new` observed in active tests |
| external deps | `winnow 1.0.4`, `miette 7.6.0`, `num-traits 0.2.19`, optional `serde`, optional `kdlv1` via package `kdl 4.7.0`; dev dependencies include `thiserror`, `pretty_assertions`, serde derive |
| memorizable standard | **Yes.** Primary parse/serialization behavior is KDL v2.0.0, a public language specification linked by the README/changelog. The crate-owned document-preserving API and serde layers are real, but upstream coverage for them is mostly inline under `src/` and unavailable to a clean rewritten crate |
| objects per scenario | Around 4: `KdlDocument` -> `KdlNode` -> `KdlEntry` -> `KdlValue`/`KdlIdentifier` plus formatting metadata and serde projection |
| difficulty | **unsuitable, not just easy.** The external oracle cannot produce per-behavior score granularity because hundreds of corpus cases are hidden behind one nodeid, while the richer behavior has no active external test surface |
| decision | **reject / RETIRED at Stage 1** |
| reason | Fails hard suitability gates: active external Rust integration surface has only two scoreable test functions, and the main retained behavior is conformance to a closed public format standard rather than a multi-owner reconstruction task |
| risks | A spec would mostly restate the KDL v2 standard; the formatting target is exact-output/golden-normalization heavy; disabled query tests are not active; using inline parser/serde/API tests would violate the clean rewritten-source oracle model |

---

## 18. `rust_xlsxwriter` — write-only Excel XLSX generator (Stage-1 **RETIRED**, 2026-09-03)

| field | content |
|---|---|
| name / crate | `rust_xlsxwriter` — single package |
| repo | https://github.com/jmcnamara/rust_xlsxwriter |
| version / release | `Cargo.toml` version **0.99.0**, changelog release **2026-08-23**; local HEAD `9e84ea38eaefe2f5d0fe3e220d6392da04299dc7` |
| src LOC | **33 413** NBNC Rust LOC under `src/` excluding `*/tests.rs`; 49 314 NBNC including in-source test modules |
| test functions | **1 423 active external** integration tests under `tests/integration/*.rs`; **292 inline** tests in `src/**/tests.rs` |
| test files / fixtures | 1 107 active integration Rust files plus shared `tests/integration/common/mod.rs`; 1 091 checked-in files under `tests/input`, mostly Excel-created `.xlsx` fixtures |
| private reach | Target-crate import surface is mostly clean: integration tests import public `rust_xlsxwriter::{...}` plus test-owned `crate::common`. The fairness risk is that 1 106/1 107 integration files depend on the shared fixture comparator |
| assertion style | **Rejecting metric.** The active integration suite is effectively 100% exact-output comparison: each test builds a workbook, saves it, unzips the result, normalizes selected volatile XML fields, and compares the remaining file list/XML parts to an Excel-created reference workbook |
| fixtures / offline | Offline fixture corpus under `tests/input`; no network observed. `zlib` feature would add a C dependency and must be excluded if ever revisited |
| external deps | Required `zip 8.3`; optional `serde`, `chrono`, `jiff`, `constant_memory`/`tempfile`, `ssfmt`, `polars`, `wasm`, `rust_decimal`, `zmij`, `ryu`, `rust_xlsxwriter_derive`; dev `regex`, `pretty_assertions`, `criterion` |
| memorizable standard | **High risk.** The observable target is Excel OOXML/XLSX package fidelity, and the author maintains sister libraries in Python, C, and Perl with overlapping behavior. Even if the Rust release is post-cutoff, cross-language recall is substantial |
| objects per scenario | 6+: `Workbook` -> `Worksheet` -> cell/value/formula/format tables -> shared strings/styles/theme -> relationships/content types -> charts/drawings/images/VML -> ZIP package |
| difficulty | Not a valid benchmark shape despite high implementation complexity: the oracle mostly measures exact package/XML reproduction, not independently stated public behavior |
| decision | **reject / RETIRED at Stage 1** |
| reason | Fails hard gates because >70% of the test suite is exact-output fixture comparison and the public docs do not specify the OOXML internals that the oracle pins |
| risks | A candidate-visible spec would become an OOXML/Excel clone manual; scoring would be dominated by XML ordering/relationship/content-type minutiae; the crate is 33k+ production LOC and needs a major carve; inline tests are unavailable in the clean rewrite model |

---

## 19. `miette` — Rust diagnostic reports and derive protocol (Stage-1 **SELECTED**, 2026-09-03)

| field | content |
|---|---|
| name / crate | `miette` with workspace member `miette-derive` |
| repo | https://github.com/zkat/miette |
| version / release | `Cargo.toml` version **7.6.0**, changelog release **2026-05-30**; local HEAD `e853bbf9bc78bbe0b225995de54a3108d77dcaf8` |
| src LOC | **7 772** NBNC Rust LOC across `src/` and `miette-derive/src/` |
| test functions | **194 active external** tests across 22 executable Rust test files plus 2 support modules; **292 inline** tests under `src/` |
| private reach | **clean.** Integration tests import public `miette::{...}` and test-owned `self::common` / `self::drop` helpers; no active integration target imports private target modules |
| assertion style | Mixed. About **107/194** tests live in exact-rendering/JSON/Debug/trybuild-heavy files (`graphical`, `narrated`, `test_json`, `test_fmt`, `color_format`, `test_diagnostic_source_macro`, `compiletest`), below the 70% hard-reject line but a major Stage 3 filter risk |
| fixtures / offline | No large fixture corpus. The trybuild driver references compile-fail inputs that are absent in this checkout, so it should be excluded unless repaired from an authoritative source. No network, daemon, or C toolchain observed |
| external deps | Required `unicode-width`, `cfg-if`; optional `miette-derive`, fancy renderer stack, backtrace, serde, syntect. Dev dependencies include `thiserror`, `trybuild`, `syn`, `regex`, `serde_json`, `strip-ansi-escapes` |
| memorizable standard | **No closed standard.** The core contract is this crate's diagnostic protocol and report-wrapper behavior. Some conceptual overlap with `anyhow`/`eyre` and diagnostic renderers is expected, but the derive attributes, label/source-code behavior, chain/downcast behavior, and handler projections are crate-specific |
| objects per scenario | 5+: user error type -> `Diagnostic` trait metadata -> `Report` wrapper/context/source chain -> `SourceCode`/`NamedSource`/`SourceSpan` labels -> `ReportHandler` projection (`Graphical`, `Narratable`, `JSON`) |
| difficulty | **medium-hard candidate.** The reconstruction work is multi-surface and stateful enough to avoid a one-file utility solution, but renderer exact-output tests must not dominate the oracle |
| decision | **keep / SELECTED** |
| reason | Clean Rust public-surface suite with enough external tests and a shared diagnostic fact source projected through derive output, public trait APIs, report chains/downcasting, hooks, and multiple handlers |
| risks | Stage 3 must filter exact string-art tests, order-sensitive global hook tests, trybuild artifacts, and undocumented layout details; include both `miette` and `miette-derive` as target crates; generate and pin a Cargo.lock for the oracle |
| scope_plan | N/A |

## grass-fullrepro-001: grass (Stage 1 RETIRED, 2026-09-05)

| field | content |
|---|---|
| task / language | `grass-fullrepro-001` / `rust` |
| repo / source | connorskees/grass; `repo-pool/grass-fullrepro-001` |
| commit / version | `a58f10afc59f7881779c609b256e9bda2db4cb5d` / 0.13.4; local release-tag commit dated 2024-08-04, registry release date unverified |
| src size | 90 source files; 29,028 physical Rust lines excluding inline test modules. NBNC-style line estimate before inline-test exclusion: 23,667. Physical count is not the ledger's NBNC metric. |
| test functions | Static count: 3,610 integration declarations across 86 case files plus shared macros.rs; 2 inline source tests. Includes ignored/feature-gated declarations; no runtime collection claimed. |
| assertion style | 2,773 direct CSS test macros + 82 unit-addition macro expansions + 653 exact error-message macros = 3,508/3,610 (97.17%) exact-output declarations, even treating every explicit test as non-exact. |
| public projections | API CSS strings, CLI stdout/file output, Logger debug/warning events, public error results over stylesheet/module evaluation state |
| private reach | No private library paths found in integration tests. Shared helper publicly imports grass_compiler::codemap::SpanLoc and is included by 85/86 case files; HIGH_RISK for a grass-only facade packet until that public signature dependency is declared. Source-unit tests use private helpers. |
| docs / tests | Aligned at Sass-to-CSS projection level; README disclaims dart-sass error-message/span parity. |
| dependencies / isolation | Rust-only compiler stack plus optional clap/rand/wasm/proc-macro features; ordinary tests use local fixtures, tempfile and paste; optional sass-spec tooling separate. |
| difficulty | Substantial parser/evaluator/module/selector/serializer pipeline; no candidate score measured. |
| decision / reason | reject / RETIRED: exceeds candidate-selector hard gate of 70% snapshot/exact-output checks. Compiler complexity does not waive this gate. |
| scope_plan | target_subdomain=not admitted, expected_oracle_max=0; no Stage 2 handoff |
| evidence | `wip/rust/grass-fullrepro-001/filter_notes.md`, `PIPELINE_STATE.md`, and versioned `BENCH.md` |
| preservation | Existing source differences left intact; git diff ignoring line endings is empty. No packet or gate verdict created. |

## hifitime-fullrepro-001: hifitime (Stage 1 SELECTED, 2026-09-05)

| field | content |
|---|---|
| task / language | `hifitime-fullrepro-001` / `rust` |
| repo / source | nyx-space/hifitime; `repo-pool/hifitime-fullrepro-001` |
| commit / version | `67ff2fcda2c81f9011f151901c08e6d6b8dd804d`, tag 4.3.1, commit date 2026-08-06; registry publication and candidate cutoff relation unknown |
| src LOC | 6,190 AST-filtered NBNC-style Rust lines excluding test bodies and dedicated Kani/Python sources; some cfg attributes and optional production code remain; reproducible audit retained |
| test functions | 116 external declarations across 8 case files; default std runs 114 external plus 26 inline tests. All 140 passed offline after dependency preparation in a pinned temporary reference |
| private reach | clean: 0/8 integration case files import private target paths; AST inventory includes local imports; public root/prelude/efmt/leap_seconds reexports resolve; sofars is external dev reference |
| assertion style | Numeric, arithmetic, ordering, conversion equivalence, parsing and formatting mix. 34/116 declarations trigger a formatting/stringification/serde review flag (32/114 active); not a measured exact-assertion fraction or a snapshot-dominated suite |
| shared facts / projections | Exact Duration and scale-tagged Epoch plus leap-provider data; projected as scale durations, Gregorian fields, Julian/MJD/GNSS values, formatted/serialized epochs and finite forward TimeSeries |
| docs alignment | README and public rustdoc cover the same scientific value/conversion/format/series projections as external tests |
| standard / difficulty | Not a Gregorian/RFC-only task: package-specific bounded arithmetic, saturation, scale retention, pre-1972 leap policy, provider semantics and correction composition remain necessary. Limited durable state and scientific-standard recall are risks; difficulty unmeasured |
| dependencies / offline | num-traits/libm, lexical-core, snafu; std/serde/web-time; dev serde_json/sofars. Original lockfile absent, generated lock retained. UT1/LTS downloads, Python/WASM/Kani and live-clock tests excluded |
| scope | Public default-std value/epoch/calendar/format/leap-file/polynomial surface and finite forward positive-step series. Exclude inconsistent TimeSeries len/size_hint and reverse/mixed-ended behavior; observed len=3 versus count=4 for inclusive [0s,6s]/2s |
| scope_plan | N/A (size and upstream test count below mandatory-carve thresholds); explicit boundary recorded in filter_notes.md |
| preregistration | 64 roots: 24 Atomic, 32 Integration, 8 System; one semantic ROUND-TIE-LOWER family with 6 planned flips and 36 native Composition controls. Rule 8 one-family audit passed with explicit policy arguments; full M1/M2 not yet run |
| decision / reason | keep / S1_SELECTED: public, enumerable, locally tested multi-component scientific-time reconstruction with substantial cross-view behavior |
| evidence / next | `wip/rust/hifitime-fullrepro-001/BENCH.md`, filter_notes, state, source audit, upstream logs, ROOT-MAP and mutation_design; Stage 2 not started; no oracle qualification or candidate score |
