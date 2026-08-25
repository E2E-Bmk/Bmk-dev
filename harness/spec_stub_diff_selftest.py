#!/usr/bin/env python3
"""Mutation-test spec_stub_diff.py, on every API Catalog layout it claims.

A differ that never fires is indistinguishable from a differ that has nothing
to report -- the dummy-gate failure. Each mutation below plants exactly one
divergence of a known class and asserts (a) the edit actually landed and
(b) the differ reports that class *and did not already report it* before the
mutation. The baseline-relative rule is what lets a task whose spec still has
open divergences (txn) be mutation-tested at all.

Three layouts, three parsers, one gate: a suite that only ever ran against
layout A would be evidence about one third of the pipeline while reading like
evidence about all of it. Layouts B and C therefore carry their own mutations.

One mutation is a deliberate expected-MISS: guppy states its derive contract in
prose, so no differ can check derives there. That blind spot is reported by the
COVERAGE line rather than passed over, and this suite asserts both halves --
the miss, and the report of the miss.

Detection is only half the contract. A differ that fires on correct code is
worse than one that stays quiet, because a false finding invites someone to
"resolve" it by editing the spec -- widening the declaration surface until a
buggy tool is satisfied, which is the failure this gate exists to prevent. The
`fpfix` fixture below is a small crate that is *correct by construction*: every
declaration in its spec is honoured by its stub, written in the other of two
equivalent spellings each time. Its baseline must be clean, and each spelling
is asserted individually so a regression names the class it broke rather than
just raising the count. Fifteen of those assertions were measured red against
the pre-fix differ.

The same fixture then carries the negative controls. Suppressing a false
positive by widening a comparison until nothing matches would leave every FP
assertion green, so each suppression is paired with a mutation that must still
be caught: an obligation met by a hand-written impl passes, and the same
obligation with that impl deleted fails.

Two further fixtures were added for the silent-pairing work:

`fpfixc` is the second correct-by-construction crate. It carries the shapes a
spec is entitled to write and the parser used to refuse -- a generic impl
header with inline bounds, a free function outside any impl block, a blanket
impl, a trait listed among the types, a payload-free enum variant -- plus two
same-named methods on two different owners, which is the collision that used
to make one of them vanish. Each of those suppressions has a mutation beside
it, so "stopped comparing" cannot pass for "stopped complaining".

`fpfixd` is the opposite: a crate the differ *must* refuse to guess about. Its
stub declares two `Report`s at equal distance from the spec's one, and an
`Error` the spec never mentions. The removed single-candidate fallback paired
both silently, and a type that is never compared prints exactly like a type
that matched. Its baseline is deliberately red, and every line of that red is
asserted individually. It also pins the one known gap left in the layout-A
type parser: a unit enum variant written *before* any payload-bearing one is
still read as a trait obligation. That assertion is `present` on purpose --
if someone fixes the gap, this suite goes red and says which line to delete.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIFF = Path(__file__).resolve().parent / "spec_stub_diff.py"

PEEL = ROOT / "wip/gix-ref-peel-001/spec"
TXN = ROOT / "wip/gix-ref-txn-001/spec"
GUPPY = ROOT / "wip/guppy-cargo-graph-fullrepro-001/spec"


def sub_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if text.count(old) < 1:
        raise SystemExit(f"MUTATION DID NOT APPLY: {old!r} not in {path}")
    path.write_text(text.replace(old, new, 1))


def re_once(path: Path, pattern: str, new: str) -> None:
    text = path.read_text()
    m = re.search(pattern, text, re.M)
    if not m:
        raise SystemExit(f"MUTATION DID NOT APPLY: /{pattern}/ not in {path}")
    path.write_text(text[: m.start()] + new + text[m.end():])


def append_undeclared_type(root: Path) -> None:
    path = root / "src/lib.rs"
    path.write_text(path.read_text()
                    + "\n#[derive(Debug)]\npub struct UndeclaredType {\n"
                      "    pub x: u8,\n}\n")


# --------------------------------------------------------------------------
# Layout A -- gix-ref-peel-001, `#### Types` / `#### Method Signatures`
# --------------------------------------------------------------------------
def m1(root: Path):
    """Drop a derive: Category loses PartialEq."""
    sub_once(root / "src/lib.rs",
             "#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]\npub enum Category",
             "#[derive(Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]\npub enum Category")


def m2(root: Path):
    """Owned vs reference return -- guppy's #1 root cause."""
    sub_once(root / "src/fullname.rs",
             "pub fn as_bstr(&self) -> &BStr {",
             "pub fn as_bstr(&self) -> BStr {")


def m3(root: Path):
    """Delete a spec-declared method entirely."""
    re_once(root / "src/target.rs",
            r"^    pub fn is_null\(&self\) -> bool \{\n(?:.*\n)*?    \}\n", "")


def m4(root: Path):
    """Over-declaring stub: a public method the spec never declares."""
    sub_once(root / "src/target.rs",
             "    pub fn is_null(&self) -> bool {",
             "    pub fn undeclared_helper(&self) -> u8 {\n        0\n    }\n\n"
             "    pub fn is_null(&self) -> bool {")


def m5(root: Path):
    """Arity change: packed::Buffer::open loses a parameter."""
    sub_once(root / "src/packed.rs", "        path: PathBuf,\n", "")


def m6(root: Path):
    """Field type change on a spec-declared struct."""
    sub_once(root / "src/lib.rs",
             "pub struct Namespace(pub(crate) BString);",
             "pub struct Namespace(pub(crate) Vec<u8>);")


def m7(root: Path):
    """Over-declaring stub: a public type the spec never declares."""
    append_undeclared_type(root)


def m8(root: Path):
    """Wrong error type behind an alias -- alias resolution must not be
    permissive enough to accept any same-named type from another module."""
    sub_once(root / "src/name.rs",
             "pub fn join(self, component: &BStr) -> Result<Self, Error>",
             "pub fn join(self, component: &BStr) -> Result<Self, std::io::Error>")


def m9(root: Path):
    """Over-derive on a type whose spec DOES declare derives.

    Guards the `unchecked_derives` suppression: a spec that states no derives
    for a type has that dimension reported as uncovered rather than passed, and
    that must not be allowed to swallow DERIVE_EXTRA where the spec does say.
    """
    sub_once(root / "src/lib.rs",
             "#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]\n"
             "pub struct Namespace",
             "#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone, Copy)]\n"
             "pub struct Namespace")


# --------------------------------------------------------------------------
# Layout B -- gix-ref-txn-001, rust blocks under `### API Catalog`
# --------------------------------------------------------------------------
def b1(root: Path):
    """Option stripped from a return type inside a `// gix_ref::..` block."""
    sub_once(root / "src/transaction.rs",
             "pub fn new_value(&self) -> Option<TargetRef<'_>> {",
             "pub fn new_value(&self) -> TargetRef<'_> {")


def b2(root: Path):
    """Drop a derive on a module-scoped type."""
    sub_once(root / "src/transaction.rs",
             "#[derive(PartialEq, Eq, Debug, Hash, Ord, PartialOrd, Clone)]\n"
             "pub struct RefEdit",
             "#[derive(PartialEq, Eq, Debug, Hash, PartialOrd, Clone)]\n"
             "pub struct RefEdit")


def b3(root: Path):
    """Delete a spec-declared method."""
    re_once(root / "src/transaction.rs",
            r"^    pub fn previous_value\(&self\) -> Option<TargetRef<'_>> \{\n"
            r"(?:.*\n)*?    \}\n", "")


def b4(root: Path):
    """Over-declaring stub: a public type the spec never declares."""
    append_undeclared_type(root)


# --------------------------------------------------------------------------
# Layout C -- guppy-cargo-graph-fullrepro-001, `Declared signature` table
# --------------------------------------------------------------------------
def c1(root: Path):
    """Return type widened on a table-declared method."""
    sub_once(root / "src/graph/mod.rs",
             "pub fn package_count(&self) -> usize {",
             "pub fn package_count(&self) -> u32 {")


def c2(root: Path):
    """Delete a table-declared method."""
    re_once(root / "src/graph/mod.rs",
            r"^    pub fn workspace\(&self\) -> Workspace<'_> \{\n(?:.*\n)*?    \}\n", "")


def c3(root: Path):
    """Over-declaring stub: a public type the table never lists."""
    append_undeclared_type(root)


def c4(root: Path):
    """Trait method dropped -- the table declares whole trait bodies in one
    cell, so this is the class the layout-C trait branch exists to catch."""
    sub_once(root / "src/graph/mod.rs",
             "    fn visit_link(&self, link: PackageLink<'_>, f: &mut DotWrite<'_, '_>) -> std::fmt::Result;\n",
             "")


def c5(root: Path):
    """EXPECTED MISS. guppy's derive contract is prose, so this dropped derive
    is unreachable for any differ; the COVERAGE line must say so out loud."""
    sub_once(root / "src/graph/mod.rs",
             "#[derive(Clone, Debug)]\npub struct PackageGraph",
             "#[derive(Clone)]\npub struct PackageGraph")


# --------------------------------------------------------------------------
# `fpfix` -- a synthetic crate for the false-positive direction
#
# Built at run time rather than committed under wip/, for two reasons. The
# tasks are being edited by other agents while this suite runs, so a fixture
# that depends on one of their specs asserts something that may not be true an
# hour from now; and no real task happens to carry every spelling at once.
#
# Every declaration here agrees between spec and stub. They agree while being
# written differently on the two sides, which is the whole point: the spec
# spells types out in full, the stub reaches them through imports, and a
# comparison that cannot see through that difference reports agreement as
# divergence. Measured against the pre-fix differ this fixture produced
# fifteen findings, all of them false.
# --------------------------------------------------------------------------
CARGO_A = """[package]
name = "fpfix"
version = "0.1.0"
edition = "2021"

[dependencies]
gix-features = "0.38"
"""

# A wrapped, nested `use` group -- the shape a declaration-scanner that flushes
# a logical line on `{` loses entirely, taking `PathBuf` and `Arc` with it.
# `{self, ..}` names the module itself, whose leaf is not a type.
LIB_A = """//! Fixture crate: correct by construction.
pub mod iter;

use std::{
    path::{Path, PathBuf},
    sync::Arc,
};

use gix_features::progress::{self, DynNestedProgress};

#[derive(Clone, Default)]
pub struct Rope {
    pub root: PathBuf,
    pub shared: Arc<Vec<u8>>,
}

impl Rope {
    pub fn new(root: PathBuf) -> Self {
        unimplemented!()
    }
    pub fn path(&self) -> &Path {
        unimplemented!()
    }
    pub fn progress(&self) -> &dyn DynNestedProgress {
        unimplemented!()
    }
    pub fn units(&self) -> Option<progress::Unit> {
        unimplemented!()
    }
    pub fn digest(&self) -> [u8; 20] {
        unimplemented!()
    }
    pub fn clone_shallow(&self) -> Self {
        unimplemented!()
    }
}

impl core::fmt::Debug for Rope {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        unimplemented!()
    }
}

impl core::fmt::Display for Rope {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        unimplemented!()
    }
}

impl core::cmp::PartialEq<Rope> for Rope {
    fn eq(&self, other: &Rope) -> bool {
        unimplemented!()
    }
}

impl core::cmp::Eq for Rope {}
"""

# `Iterator`, `ExactSizeIterator` and `FusedIterator` have no derive macro at
# all: a spec that lists them is stating an obligation the stub can only meet
# by hand. Checking that list against `#[derive(...)]` reports correct code.
ITER_A = """use crate::Rope;

pub struct Bytes<'a> {
    pub rope: &'a Rope,
}

impl<'a> Iterator for Bytes<'a> {
    type Item = u8;
    fn next(&mut self) -> Option<u8> {
        unimplemented!()
    }
}

impl ExactSizeIterator for Bytes<'_> {
    fn len(&self) -> usize {
        unimplemented!()
    }
}

impl core::iter::FusedIterator for Bytes<'_> {}
"""

SPEC_A = """# fpfix -- fixture spec, layout A

## Public Interface

### API Catalog

#### Types

```
Rope {
    root: std::path::PathBuf,
    shared: std::sync::Arc<Vec<u8>>,
}
    Clone, Default
    Debug, Display
    PartialEq, Eq
    Send, Sync

iter::Bytes<'a> {
    rope: &'a Rope,
}
    Iterator
    ExactSizeIterator
    FusedIterator
```

#### Method Signatures

```rust
// Rope
impl Rope {
    fn new(root: std::path::PathBuf) -> Rope;
    fn path(&self) -> &std::path::Path;
    fn progress(&self) -> &dyn gix_features::progress::DynNestedProgress;
    fn units(&self) -> Option<gix_features::progress::Unit>;
    fn digest(&self) -> [u8; 20];
    fn clone_shallow(&self) -> Rope;
}
```
"""

# Layout A cannot express `thiserror::Error`: a path is not a bare identifier,
# so the derive-line pattern never sees it. The asymmetry it exposed -- the
# name filtered out of one side of the comparison but not the other -- is not
# layout-specific, so it needs a layout-B fixture of its own.
CARGO_B = """[package]
name = "fpfixb"
version = "0.1.0"
edition = "2021"

[dependencies]
thiserror = "2.0"
"""

LIB_B = "pub mod parse;\n"

PARSE_B = """#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("bad header")]
    BadHeader,
}
"""

SPEC_B = """# fpfixb -- fixture spec, layout B

### API Catalog

```rust
// fpfixb::parse
#[derive(Debug, thiserror::Error)]
pub enum Error {
    BadHeader,
}
```
"""


def build_fixture(root: Path, files: dict[str, str]) -> Path:
    """Materialise a fixture as a `spec_v1.md` + `surface_stub/` pair."""
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


# --------------------------------------------------------------------------
# `fpfixc` -- the syntax a spec is entitled to write, and the owner-keying
# that used to lose half of it.
#
# Six things here were, separately, enough to make the differ wrong:
#
#   * `impl<T: std::io::Read> data::File<T> {` -- a generic impl header with
#     an inline bound. The old header pattern could not read it, so every
#     method inside was filed under no owner at all.
#   * `pub fn checksum(..)` outside any impl block. A free function had to be
#     wrapped in an impl-shaped pseudo-heading to be seen -- a deformation of
#     the spec to suit the parser.
#   * `impl<T: Debug> Named for T {}` -- a blanket impl. Read as an ordinary
#     impl it minted a phantom type `T` and hung `name` off it.
#   * `data::File::version` and `multi_index::File::version`. Keyed by bare
#     name, the second overwrote the first and the differ compared one
#     declaration twice while reporting nothing about the other.
#   * `data::Kind`'s `Tree`, a payload-free enum variant, which the derive-line
#     pattern read as a trait the stub had to implement.
#   * `checksum` declared twice: once as a crate-root free function, once as a
#     method on `multi_index::File`. Both sides write it the same way both
#     times, but the free function was matched by *name* against every method
#     of that name, so a second one made it "ambiguous" and it stopped being
#     compared at all. Seen from the other direction the same shortcut was a
#     false green: one ownerless spec function excused every stub method
#     sharing its name, declared or not (X14).
#
# Everything in it agrees. `Widget` agrees *through a re-export*, which is the
# one pairing here that rests on evidence rather than on the two sides writing
# the same path -- so the run has to say so out loud, and P20 asserts it does.
# --------------------------------------------------------------------------
CARGO_C = """[package]
name = "fpfixc"
version = "0.1.0"
edition = "2021"
"""

LIB_C = """pub mod data;
pub mod inner;
pub mod multi_index;

pub use inner::Widget;

pub trait Named {
    fn name(&self) -> &str;
}

// A public trait the spec never declares. Traits are not in the type
// comparison at all, so this is over-declared surface the differ cannot
// report -- and P23 asserts it is at least announced. Silence here would be
// the dummy-gate shape: nothing found, nothing looked for, same output.
pub trait Sealed {}

impl<T: core::fmt::Debug> Named for T {
    fn name(&self) -> &str {
        unimplemented!()
    }
}

pub fn checksum(data: &[u8], seed: u32) -> u32 {
    unimplemented!()
}
"""

DATA_C = """#[derive(Clone, Default)]
pub struct File<T> {
    pub inner: T,
}

impl<T: std::io::Read> File<T> {
    pub fn version(&self) -> u32 {
        unimplemented!()
    }
    pub fn read_at(&self, offset: u64, out: &mut [u8]) -> std::io::Result<usize> {
        unimplemented!()
    }
    pub fn consume(self) -> T {
        unimplemented!()
    }
}

#[derive(Clone, Copy, Debug)]
pub enum Kind {
    Blob(u32),
    Tree,
}
"""

MULTI_C = """#[derive(Clone, Default)]
pub struct File {
    pub num_indices: u32,
}

impl File {
    pub fn version(&self) -> u8 {
        unimplemented!()
    }
    pub fn checksum(&self) -> u32 {
        unimplemented!()
    }
    pub fn label(&self) -> std::ffi::OsString {
        unimplemented!()
    }
}
"""

INNER_C = """#[derive(Clone, Default)]
pub struct Widget {
    pub id: u32,
}

impl core::convert::From<u32> for Widget {
    fn from(id: u32) -> Widget {
        unimplemented!()
    }
}
"""

SPEC_C = """# fpfixc -- fixture spec, layout A

## Public Interface

### API Catalog

#### Types

```
Named

Widget {
    id: u32,
}
    Clone, Default
    From<u32>

data::File<T> {
    inner: T,
}
    Clone, Default

data::Kind
    Clone, Copy, Debug
    Blob(u32)
    Tree

multi_index::File {
    num_indices: u32,
}
    Clone, core::default::Default
```

#### Method Signatures

```rust
pub trait Named {
    fn name(&self) -> &str;
}

pub fn checksum(data: &[u8], seed: u32) -> u32;

impl<T: std::io::Read> data::File<T> {
    pub fn version(&self) -> u32;
    pub fn read_at(&self, offset: u64, out: &mut [u8]) -> std::io::Result<usize>;
    pub fn consume(self) -> T;
}

impl multi_index::File {
    pub fn version(&self) -> u8;
    pub fn checksum(&self) -> u32;
    pub fn label(&self) -> OsString;
}
```
"""

# --------------------------------------------------------------------------
# `fpfixd` -- the crate the differ must refuse to guess about.
#
# `b::Error` is declared by the stub and by nothing in the spec. `Report` is
# declared by the spec and by two stub modules at equal distance. The removed
# fallback -- "only one candidate left, so it must be the one" -- paired both
# without checking, and a silently paired type is compared against nothing
# while printing exactly like a type that matched. Two of eight Rust tasks
# were green on that basis.
#
# `d::Mode` pins the known gap: its `Fast` variant is written before any
# payload-bearing one, and a bare capitalised identifier in that position is
# indistinguishable from a trait obligation. The false DERIVE_MISSING it
# produces is asserted `present` so the gap cannot quietly change shape.
#
# `tally` is the negative control for fixture C's `checksum`. The spec writes
# it with no owner and the stub has no crate-root function of that name, only
# two methods equally entitled to it. Pairing an ownerless declaration against
# an ownerless one is exact; this is the case where there is nothing exact to
# reach, and the guard against guessing must survive the repair that made
# `checksum` pair (P31).
# --------------------------------------------------------------------------
CARGO_D = """[package]
name = "fpfixd"
version = "0.1.0"
edition = "2021"
"""

LIB_D = """pub mod a;
pub mod b;
pub mod c;
pub mod d;
"""

ERR_D = """#[derive(Debug)]
pub struct Error {
    pub code: u8,
}
"""

REPORT_D = """#[derive(Debug)]
pub struct Report {
    pub n: u32,
}

impl Report {
    pub fn tally(&self) -> u32 {
        unimplemented!()
    }
}
"""

REPORT_MODE_D = """#[derive(Debug)]
pub struct Report {
    pub n: u32,
}

impl Report {
    pub fn tally(&self) -> u32 {
        unimplemented!()
    }
}

#[derive(Clone, Copy, Debug)]
pub enum Mode {
    Fast,
    Slow(u8),
}
"""

SPEC_D = """# fpfixd -- fixture spec, layout A

## Public Interface

### API Catalog

#### Types

```
a::Error {
    code: u8,
}
    Debug

Report {
    n: u32,
}
    Debug

d::Mode
    Clone, Copy, Debug
    Fast
    Slow(u8)
```

#### Method Signatures

```rust
pub fn tally(&self) -> u32;
```
"""


FIXTURE_A = {
    "spec_v1.md": SPEC_A,
    "surface_stub/Cargo.toml": CARGO_A,
    "surface_stub/src/lib.rs": LIB_A,
    "surface_stub/src/iter.rs": ITER_A,
}

FIXTURE_B = {
    "spec_v1.md": SPEC_B,
    "surface_stub/Cargo.toml": CARGO_B,
    "surface_stub/src/lib.rs": LIB_B,
    "surface_stub/src/parse.rs": PARSE_B,
}

FIXTURE_C = {
    "spec_v1.md": SPEC_C,
    "surface_stub/Cargo.toml": CARGO_C,
    "surface_stub/src/lib.rs": LIB_C,
    "surface_stub/src/data.rs": DATA_C,
    "surface_stub/src/inner.rs": INNER_C,
    "surface_stub/src/multi_index.rs": MULTI_C,
}

FIXTURE_D = {
    "spec_v1.md": SPEC_D,
    "surface_stub/Cargo.toml": CARGO_D,
    "surface_stub/src/lib.rs": LIB_D,
    "surface_stub/src/a.rs": ERR_D,
    "surface_stub/src/b.rs": ERR_D,
    "surface_stub/src/c.rs": REPORT_D,
    "surface_stub/src/d.rs": REPORT_MODE_D,
}

# (label, fixture, want, pattern). "absent" asserts the class does NOT appear;
# "present" asserts it does -- used for the blind spot that must stay announced.
# The pre-fix column records what the differ said before the false-positive
# repair: `red` means this exact line was one of its fifteen bogus findings.
FP_CHECKS = [
    # pre-fix       label                                    fixture want      pattern
    ("red ", "P1  spec-qualified field vs stub import  ", "A", "absent",
     r"FIELD_TYPE.*Rope\.root"),
    ("red ", "P2  nested `use` group leaf              ", "A", "absent",
     r"FIELD_TYPE.*Rope\.shared"),
    ("red ", "P3  spec-qualified return vs stub import ", "A", "absent",
     r"METHOD_RETURN.*Rope::path"),
    ("red ", "P4  `&dyn Trait`, short vs qualified     ", "A", "absent",
     r"METHOD_RETURN.*Rope::progress"),
    ("red ", "P5  array return type `[u8; 20]`         ", "A", "absent",
     r"METHOD_RETURN.*Rope::digest"),
    ("red ", "P6  `Self` in an inherent impl           ", "A", "absent",
     r"METHOD_RETURN.*Rope::(new|clone_shallow)"),
    ("red ", "P7  hand-written impl, underivable trait ", "A", "absent",
     r"DERIVE_MISSING.*(FusedIterator|ExactSizeIterator|Iterator)"),
    ("red ", "P8  auto trait, unimplementable by hand  ", "A", "absent",
     r"DERIVE_MISSING.*(Send|Sync)"),
    ("red ", "P9  hand-written impl, derivable trait   ", "A", "absent",
     r"DERIVE_MISSING.*(Debug|Display|PartialEq|Eq)"),
    # Green before the repair too: the path-suffix rule already reached this
    # one. Kept because it is the only `{self, ..}` group in the suite, and a
    # scanner that mis-parses that leaf would take `DynNestedProgress` with it.
    ("    ", "P10 module-self group leaf               ", "A", "absent",
     r"METHOD_RETURN.*Rope::units"),
    ("red ", "P11 `thiserror::Error` written both sides", "B", "absent",
     r"DERIVE_MISSING.*thiserror"),
    # An auto trait is asserted, not checked -- no stub can implement `Send`.
    # Silence there would be a dummy pass, so the COVERAGE line has to say it.
    ("    ", "P12 that blind spot is announced         ", "A", "present",
     r"COVERAGE.*auto"),

    # ---- fpfixc: syntax the parser used to refuse, and owner-keyed methods
    ("red ", "P13 generic impl header, inline bound    ", "C", "absent",
     r"METHOD_(MISSING|UNDECLARED).*data::File"),
    ("red ", "P14 free fn outside any impl block       ", "C", "absent",
     r"METHOD_(MISSING|UNDECLARED).*checksum"),
    ("red ", "P15 blanket impl mints no type or method ", "C", "absent",
     r"(TYPE_UNDECLARED\s+T\b|METHOD_UNDECLARED.*::name\b)"),
    ("red ", "P16 same method name, two owners         ", "C", "absent",
     r"METHOD_(RETURN|MISSING|UNDECLARED).*version"),
    ("red ", "P17 ... and neither overwrote the other  ", "C", "absent",
     r"KEY_COLLISION"),
    ("red ", "P18 trait listed among the types         ", "C", "absent",
     r"TYPE_MISSING.*Named"),
    ("red ", "P19 payload-free enum variant            ", "C", "absent",
     r"DERIVE_MISSING.*Tree"),
    # An obligation line is not restricted to bare identifiers. `<` and `::`
    # both used to make the line unmatchable, and an unmatchable obligation
    # line is not a false red -- it is worse, it is an obligation that silently
    # left the comparison. X11/X12 are the controls.
    ("red ", "P28 obligation with a generic argument   ", "C", "absent",
     r"DERIVE_MISSING.*Widget"),
    ("red ", "P29 obligation written as a path         ", "C", "absent",
     r"DERIVE_MISSING.*multi_index::File"),
    # Bug 4's positive half. A pairing that rests on a `pub use` rather than on
    # the two sides writing the same path is a pairing someone has to be able
    # to audit, so the run names it whether or not it passed.
    ("    ", "P20 re-export pairing is named           ", "C", "present",
     r"ASSUMED_PAIRING.*Widget"),
    ("    ", "P21 pairing accounting is unconditional  ", "C", "present",
     r"SCOPE.*pairing\(s\) rested"),
    ("    ", "P22 the run stamps its own version       ", "C", "present",
     r"SCOPE\s+tool .*md5 [0-9a-f]{32}"),
    ("    ", "P23 traits named as a dark dimension     ", "C", "present",
     r"SCOPE.*stub trait\(s\) are outside"),
    # A crate-root free function and a method may share a name -- `at` and
    # `at_opts` do on gix-odb-dynstore-001. Both sides write both declarations
    # identically, so nothing here is ambiguous; the differ made it so by
    # treating the method as a rival candidate for the free function. P30 also
    # guards the report against contradicting itself: this run must not claim
    # a name-only pairing while the accounting line says none were assumed.
    ("red ", "P30 free fn and method share a name      ", "C", "absent",
     r"AMBIGUOUS.*checksum|paired by name alone"),

    # ---- fpfixd: what must never be paired silently
    ("red ", "P24 stub type the spec never declares    ", "D", "present",
     r"TYPE_UNDECLARED.*b::Error"),
    ("red ", "P25 two equal candidates -> AMBIGUOUS    ", "D", "present",
     r"AMBIGUOUS\s+Report:"),
    ("    ", "P26 ... and the finding names them both  ", "D", "present",
     r"AMBIGUOUS\s+Report:.*c::Report, d::Report"),
    # The control for P30. Making `checksum` pair must not have disarmed the
    # refusal to guess: with no crate-root `tally` in the stub, two methods are
    # equally entitled to the spec's ownerless declaration and neither may be
    # picked.
    ("    ", "P31 ownerless with no exact match        ", "D", "present",
     r"AMBIGUOUS\s+::tally"),
    # KNOWN GAP, asserted so it cannot change shape unnoticed. A unit enum
    # variant written before any payload-bearing one is still read as a trait
    # obligation. Fixing that makes this line go red; delete it then.
    ("    ", "P27 KNOWN GAP leading unit variant       ", "D", "present",
     r"DERIVE_MISSING.*d::Mode.*Fast"),
]


# --------------------------------------------------------------------------
# Negative controls on the same fixture.
#
# Every check above is a suppression, and the cheapest way to satisfy all of
# them is to stop comparing. These mutations are the other side of each one:
# the obligation whose hand-written impl was accepted must fail when that impl
# is deleted, the array whose length was finally parsed must fail when the
# length changes, the import that resolved must fail when it resolves to the
# wrong type. Losing these would be a worse bug than the ones being fixed.
# --------------------------------------------------------------------------
def n1(root: Path):
    """The impl that satisfied `FusedIterator` is deleted."""
    sub_once(root / "src/iter.rs",
             "impl core::iter::FusedIterator for Bytes<'_> {}\n", "")


def n2(root: Path):
    """A derivable trait carried by a hand-written impl loses that impl."""
    sub_once(root / "src/lib.rs", "impl core::cmp::Eq for Rope {}\n", "")


def n3(root: Path):
    """Ordinary dropped derive, on a type that also has hand-written impls."""
    sub_once(root / "src/lib.rs", "#[derive(Clone, Default)]", "#[derive(Default)]")


def n4(root: Path):
    """The impl still exists -- on a different type.

    Obligations are looked up by path suffix, and a lookup loose enough to
    reach `iter::Bytes` from `Bytes` is one step from reaching it from
    anywhere. An impl on `Rope` must not satisfy an obligation on `Bytes`.
    """
    sub_once(root / "src/iter.rs",
             "impl ExactSizeIterator for Bytes<'_> {",
             "impl ExactSizeIterator for Rope {")


def n5(root: Path):
    """Import resolution must see through the spelling, not past the type."""
    sub_once(root / "src/lib.rs",
             "pub root: PathBuf,", "pub root: std::ffi::OsString,")


def n6(root: Path):
    """The array length is inside the part that used to be truncated."""
    sub_once(root / "src/lib.rs",
             "pub fn digest(&self) -> [u8; 20]", "pub fn digest(&self) -> [u8; 32]")


def n7(root: Path):
    """`Path` and `PathBuf` arrive through the same `use` group."""
    sub_once(root / "src/lib.rs",
             "pub fn path(&self) -> &Path {", "pub fn path(&self) -> &PathBuf {")


FIXTURE_MUTANTS = [
    ("N1 underivable impl deleted", n1, "DERIVE_MISSING"),
    ("N2 manual impl deleted     ", n2, "DERIVE_MISSING"),
    ("N3 derive dropped          ", n3, "DERIVE_MISSING"),
    ("N4 impl on the wrong type  ", n4, "DERIVE_MISSING"),
    ("N5 imported field type wrong", n5, "FIELD_TYPE"),
    ("N6 array length changed    ", n6, "METHOD_RETURN"),
    ("N7 Path vs PathBuf         ", n7, "METHOD_RETURN"),
]


# --------------------------------------------------------------------------
# Negative controls on fpfixc.
#
# X1-X4 are the parameter dimension, which was dark: the differ counted commas
# and compared the return type, so a parameter's *type* was never looked at.
# Every one of these is a change no compiler would accept and the old differ
# reported nothing at all for.
#
# X5 and X6 are bug 3 from both sides. It is not enough that *a* divergence is
# reported -- the wrong owner would be a different bug wearing the same line
# -- so each asserts the owner by name.
#
# X7-X10 are the other side of the suppressions above: the re-export that
# resolved must still compare fields, the trait that paired must still be
# missable, the enum whose variants stopped being obligations must still check
# the obligations it does declare, and the pairing that had evidence must
# become a finding when the evidence is removed.
# --------------------------------------------------------------------------
def x1(root: Path):
    """Parameter type changed; arity unchanged."""
    sub_once(root / "src/data.rs",
             "pub fn read_at(&self, offset: u64, out: &mut [u8])",
             "pub fn read_at(&self, offset: usize, out: &mut [u8])")


def x2(root: Path):
    """Receiver mutability. `&mut self` and `&self` are different methods."""
    sub_once(root / "src/multi_index.rs",
             "pub fn version(&self) -> u8", "pub fn version(&mut self) -> u8")


def x3(root: Path):
    """Two parameters swapped. Same arity, same set of types, wrong order --
    invisible to anything that counts commas."""
    sub_once(root / "src/lib.rs",
             "pub fn checksum(data: &[u8], seed: u32) -> u32",
             "pub fn checksum(seed: u32, data: &[u8]) -> u32")


def x4(root: Path):
    """`&mut [u8]` narrowed to `&[u8]`, which is the whole point of the
    parameter: the caller writes into it."""
    sub_once(root / "src/data.rs", "out: &mut [u8]", "out: &[u8]")


def x5(root: Path):
    """Bug 3: the method on `multi_index::File`, not the one on `data::File`."""
    sub_once(root / "src/multi_index.rs",
             "pub fn version(&self) -> u8", "pub fn version(&self) -> u16")


def x6(root: Path):
    """Bug 3, the other owner. Both must be reachable, and by name."""
    sub_once(root / "src/data.rs",
             "pub fn version(&self) -> u32", "pub fn version(&self) -> u64")


def x7(root: Path):
    """The type reached through a `pub use` is still compared, not just paired."""
    sub_once(root / "src/inner.rs", "pub id: u32,", "pub id: u64,")


def x8(root: Path):
    """A trait the spec declares and the stub does not is still MISSING."""
    re_once(root / "src/lib.rs",
            r"^pub trait Named \{\n(?:.*\n)*?\}\n", "")


def x9(root: Path):
    """The enum whose variants stopped being obligations still has real ones."""
    sub_once(root / "src/data.rs", "#[derive(Clone, Copy, Debug)]", "#[derive(Clone, Copy)]")


def x10(root: Path):
    """Bug 4: the pairing the removed fallback used to make silently.

    Two stub `Widget`s equidistant from the spec's, and the `pub use` that
    named one of them deleted. Nothing distinguishes them, so the only honest
    outcome is a finding -- not whichever one the walk reached first.
    """
    sub_once(root / "src/lib.rs", "pub use inner::Widget;\n", "pub mod outer;\n")
    (root / "src/outer.rs").write_text(
        "#[derive(Clone, Default)]\npub struct Widget {\n    pub id: u32,\n}\n")


def x11(root: Path):
    """The generic-argument obligation must still be an obligation."""
    re_once(root / "src/inner.rs",
            r"^impl core::convert::From<u32> for Widget \{\n(?:.*\n)*?\}\n", "")


def x12(root: Path):
    """And so must the one the spec spells as a path."""
    sub_once(root / "src/multi_index.rs",
             "#[derive(Clone, Default)]", "#[derive(Clone)]")


def x13(root: Path):
    """The method that shares the free function's name is still compared.

    Direction 1 pairs the spec's ownerless `checksum` with the stub's
    crate-root one. That must not consume `multi_index::File::checksum`, which
    the spec declares separately and has to find its own counterpart. The
    obvious wrong repair -- pair on the empty owner and move on -- passes P30
    and fails here.
    """
    sub_once(root / "src/multi_index.rs",
             "pub fn checksum(&self) -> u32", "pub fn checksum(&self) -> u64")


def x14(root: Path):
    """The same shortcut in direction 2, and the reason P30 needed a control.

    `data::File::checksum` is in no spec. Direction 2 used to skip every stub
    method whose name the spec declared ownerless anywhere, so this was never
    reported. Before the repair that was merely redundant -- direction 1 was
    shouting AMBIGUOUS about the same name, so the run was red either way.
    Repairing direction 1 alone removes the shout and leaves the skip: measured
    on this fixture, that combination exits 0 with an undeclared public method
    in the stub. A red that becomes a green without anyone comparing anything
    is the failure this whole gate exists to prevent, so both halves move
    together and this is what holds them together.
    """
    sub_once(root / "src/data.rs",
             "    pub fn consume(self) -> T {",
             "    pub fn checksum(&self) -> u32 {\n        unimplemented!()\n    }\n"
             "    pub fn consume(self) -> T {")


def x15(root: Path):
    """The bare-name rule is conditioned on absence, and must stay that way.

    The spec's `OsString` pairs with the stub's `std::ffi::OsString` only
    because the crate declares nothing of that name -- there is nothing else
    it could mean. Once the crate declares its own `OsString`, the bare name
    plausibly meant *that*, the two sides no longer agree, and an unconditional
    version of the rule would say nothing.
    """
    sub_once(root / "src/lib.rs", "pub mod data;",
             "pub mod data;\n\n#[derive(Clone)]\npub struct OsString {\n    pub raw: u8,\n}")


FIXTURE_C_MUTANTS = [
    ("X1 parameter type changed  ", x1, "METHOD_PARAM"),
    ("X2 receiver mutability     ", x2, "METHOD_RECEIVER"),
    ("X3 parameters swapped      ", x3, "METHOD_PARAM"),
    ("X4 &mut [u8] -> &[u8]      ", x4, "METHOD_PARAM"),
    ("X5 owner-keyed: multi_index", x5, r"METHOD_RETURN\s+multi_index::File::version"),
    ("X6 owner-keyed: data       ", x6, r"METHOD_RETURN\s+data::File::version"),
    ("X7 re-exported type's field", x7, "FIELD_TYPE"),
    ("X8 declared trait deleted  ", x8, "TYPE_MISSING"),
    ("X9 real obligation dropped ", x9, "DERIVE_MISSING"),
    ("X10 evidence removed       ", x10, "AMBIGUOUS"),
    ("X11 generic obligation gone", x11, "DERIVE_MISSING"),
    ("X12 path obligation gone   ", x12, "DERIVE_MISSING"),
    ("X13 name-sharing method    ", x13,
     r"METHOD_RETURN\s+multi_index::File::checksum"),
    ("X14 undeclared, name shared", x14,
     r"METHOD_UNDECLARED\s+data::File::checksum"),
    ("X15 bare name now ambiguous", x15,
     r"METHOD_RETURN\s+multi_index::File::label"),
]


# (label, mutation fn, expected class; a leading "!" means expected MISS)
TASKS = [
    ("A peel ", PEEL, [
        ("M1 derive dropped        ", m1, "DERIVE_MISSING"),
        ("M2 &BStr -> BStr         ", m2, "METHOD_RETURN"),
        ("M3 method deleted        ", m3, "METHOD_MISSING"),
        ("M4 undeclared method     ", m4, "METHOD_UNDECLARED"),
        ("M5 parameter dropped     ", m5, "METHOD_ARITY|METHOD_MISSING"),
        ("M6 field type changed    ", m6, "FIELD_TYPE"),
        ("M7 undeclared type       ", m7, "TYPE_UNDECLARED"),
        ("M8 wrong type behind alias", m8, "METHOD_RETURN"),
        ("M9 extra derive          ", m9, "DERIVE_EXTRA"),
    ]),
    ("B txn  ", TXN, [
        ("B1 Option dropped        ", b1, "METHOD_RETURN"),
        ("B2 derive dropped        ", b2, "DERIVE_MISSING"),
        ("B3 method deleted        ", b3, "METHOD_MISSING"),
        ("B4 undeclared type       ", b4, "TYPE_UNDECLARED"),
    ]),
    ("C guppy", GUPPY, [
        ("C1 usize -> u32          ", c1, "METHOD_RETURN"),
        ("C2 method deleted        ", c2, "METHOD_MISSING"),
        ("C3 undeclared type       ", c3, "TYPE_UNDECLARED"),
        ("C4 trait method dropped  ", c4, "METHOD_MISSING"),
        ("C5 derive dropped (prose)", c5, "!DERIVE_MISSING"),
    ]),
]


def run(spec: Path, stub_root: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(DIFF), str(spec), str(stub_root)],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


# Lines the differ prints on every run to declare its own extent. They are not
# findings, and counting them as such made a two-divergence baseline read as
# eight. The mutation logic subtracts the baseline, so it never cared; the
# human reading the output does.
INFORMATIONAL = ("COVERAGE", "SCOPE", "ASSUMED_PAIRING", "KEY_COLLISION",
                 "UNCHECKED")


def divergences(out: str) -> set[str]:
    return {ln.strip() for ln in out.splitlines()
            if re.match(r"\s{2}[A-Z_]+\s", ln)}


def findings(out: str) -> set[str]:
    """Just the divergence classes -- what a reader means by "open"."""
    return {ln for ln in divergences(out) if not ln.startswith(INFORMATIONAL)}


def all_lines(out: str) -> set[str]:
    """Every reported line, COVERAGE and SCOPE included -- the false-positive
    pass asserts on the extent-declaring text too."""
    return {ln.strip() for ln in out.splitlines()
            if re.match(r"\s{2}[A-Z_]+\s", ln)}


# --------------------------------------------------------------------------
# A structural invariant rather than a pattern: whatever the fixtures contain,
# the number the run states must equal the number of pairings it lists.
#
# The count and the list are filled from two different registries -- one at the
# point a pairing is made, one inside the alias resolver -- and only the first
# was counted. A real run printed "0 pairing(s) rested on something other than
# the two sides writing the same path" with an ASSUMED_PAIRING line directly
# beneath it saying a spec type had been matched to `gix_path::RelativePath` on
# its bare name alone. Nobody reads past a zero. Asserting the two agree is
# cheaper than asserting any particular value, and it holds for fixtures that
# do not exist yet.
# --------------------------------------------------------------------------
def accounting_check(results: dict) -> bool:
    print("  P32 stated pairing count matches the list  ", end="")
    bad = []
    for tag in sorted(results):
        code, lines, out = results[tag]
        stated = [ln for ln in lines if re.search(r"pairing\(s\) rested", ln)]
        listed = [ln for ln in lines if ln.startswith("ASSUMED_PAIRING")]
        if not stated:
            bad.append(f"{tag}: no accounting line")
            continue
        n = int(re.search(r"(\d+) pairing", stated[0]).group(1))
        if n != len(listed):
            bad.append(f"{tag}: states {n}, lists {len(listed)}")
    print("CONSISTENT" if not bad else "MISCOUNTED")
    for b in bad:
        print(f"        {b}")
    return not bad


def false_positive_pass(tmp: Path) -> tuple[int, int]:
    """Assert the fixtures are clean, one class at a time.

    A single "baseline is clean" assertion would collapse twelve independent
    guarantees into one bit, and the first regression would say only that
    something broke. Each class is checked on its own so the failure names it.
    """
    print("FALSE-POSITIVE DIRECTION -- fpfix fixtures, correct by construction")
    built = {
        "A": build_fixture(tmp / "fpfix_a", FIXTURE_A),
        "B": build_fixture(tmp / "fpfix_b", FIXTURE_B),
        "C": build_fixture(tmp / "fpfix_c", FIXTURE_C),
        # Deliberately red: fpfixd exists to be refused, not to pass.
        "D": build_fixture(tmp / "fpfix_d", FIXTURE_D),
    }
    results = {}
    for tag, root in built.items():
        code, out = run(root / "spec_v1.md", root / "surface_stub")
        results[tag] = (code, all_lines(out), out)
        real = findings(out)
        print(f"  fixture {tag} -> exit {code} "
              f"({'clean' if code == 0 else f'{len(real)} open divergence(s)'})")
        if code not in (0, 1):
            print("      FIXTURE UNUSABLE -- every check below would be vacuous:")
            for ln in out.strip().splitlines()[:4]:
                print(f"      ! {ln}")

    failures = 0
    for prefix, label, tag, want, pattern in FP_CHECKS:
        code, lines, out = results[tag]
        hits = sorted(ln for ln in lines if re.search(pattern, ln))
        # An unusable fixture proves nothing either way; fail rather than pass.
        usable = code in (0, 1)
        ok = usable and (bool(hits) if want == "present" else not hits)
        verdict = ("REPORTED " if want == "present" else "NO FINDING") if ok \
            else ("MISSING  " if want == "present" else "FALSE POS")
        print(f"  {prefix}{label} {verdict} (want {want}: {pattern})")
        for ln in hits[:2]:
            print(f"        {ln}")
        if not ok:
            failures += 1
    if not accounting_check(results):
        failures += 1
    print()
    return len(FP_CHECKS) + 1 - failures, len(FP_CHECKS) + 1


def main() -> int:
    failures = total = 0
    with tempfile.TemporaryDirectory() as fixdir:
        fixtures = Path(fixdir)
        passed, ran = false_positive_pass(fixtures)
        failures += ran - passed
        total += ran
        tasks = TASKS + [
            ("D fpfix", fixtures / "fpfix_a", FIXTURE_MUTANTS),
            ("E fpfixc", fixtures / "fpfix_c", FIXTURE_C_MUTANTS),
        ]

        for label, spec_dir, mutants in tasks:
            spec, stub = spec_dir / "spec_v1.md", spec_dir / "surface_stub"
            code, out = run(spec, stub)
            base = divergences(out)
            open_now = findings(out)
            state = "clean" if code == 0 else f"{len(open_now)} open divergence(s)"
            print(f"{label} baseline -> exit {code} ({state})")
            if code not in (0, 1):
                print(f"      BASELINE UNUSABLE -- mutation results would be meaningless:")
                for ln in out.strip().splitlines()[:4]:
                    print(f"      ! {ln}")
                failures += len(mutants)
                total += len(mutants)
                continue
            covers = [ln for ln in base if ln.startswith("COVERAGE")]

            for name, fn, expect in mutants:
                total += 1
                want_miss = expect.startswith("!")
                expect = expect.lstrip("!")
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td) / "stub"
                    shutil.copytree(stub, root)
                    fn(root)
                    code, out = run(spec, root)
                    new = [ln for ln in divergences(out) - base
                           if re.match(rf"({expect})\b", ln)]
                    if want_miss:
                        # The blind spot is only acceptable while it is announced.
                        ok = not new and covers and any(
                            ln.startswith("COVERAGE") for ln in divergences(out))
                        verdict = "MISSED-AS-STATED" if ok else "UNEXPECTED     "
                    else:
                        ok = code == 1 and bool(new)
                        verdict = "DETECTED" if ok else "MISSED  "
                    print(f"  {label} {name} exit {code}  {verdict} (want "
                          f"{'no ' if want_miss else ''}{expect})")
                    for ln in sorted(new)[:2]:
                        print(f"        {ln}")
                    if not ok:
                        failures += 1
                        for ln in out.strip().splitlines()[:6]:
                            print(f"        ! {ln}")
            print()

    n_fp = len(FP_CHECKS) + 1  # the pattern classes plus the count invariant
    print(f"{total - failures}/{total} checks behaved as specified: "
          f"{n_fp} false-positive/announcement classes across 4 fixtures, "
          f"{total - n_fp} mutation classes across 5 stubs")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
