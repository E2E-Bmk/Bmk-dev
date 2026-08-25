#!/usr/bin/env python3
"""Diff a spec's declaration surface against its spec-surface stub.

Why this exists
---------------
``SKILL.md`` check 26 builds a stub containing "verbatim only what the spec
declares" and then compiles the *oracle* against it. That catches
spec-versus-oracle divergence, but it needs an oracle, so it cannot run at
spec-draft time. In the gap, the only thing anyone actually ran was a
standalone build of the stub -- and a standalone build compiles the stub
against itself. It never compares the stub to the spec it was transcribed
from. A stub that silently drops a derive, widens a return type from a
reference to an owned value, or declares a method the spec never mentioned
builds perfectly green and the divergence only surfaces later, at oracle-link
time, as an unscoreable 0.

That is the guppy failure: four root causes, all of this shape -- a
``PackageId`` owned-vs-reference return divergence, a missing method, a
missing ``Ord`` derive, a missing ``Display`` impl -- none of them visible to
a standalone build, all of them fatal once the oracle linked.

The clause catalogue cannot close this gap either. Clause discipline forbids
quoting bare declarations out of fenced code blocks (a signature line is not a
testable prose statement), which is correct, and which means clause coverage
of the declaration surface is structurally 0%. A spec can be at 348/348
verbatim-verified clauses and still disagree with its own stub about every
derive in the crate.

So this check is the third instrument, and the only one runnable at S2 with no
oracle in existence:

* substring verification    -> prose clauses
* spec/stub diff (this)     -> declaration surface, runnable at S2
* stub/oracle link (ck. 26) -> spec-versus-oracle divergence, needs an oracle

Both directions are checked. A spec-declared item missing from the stub is a
transcription error. A stub declaration with no spec counterpart is the more
interesting failure: it means the stub author needed something the spec never
declared, i.e. a spec gap that the stub silently papered over.

Alias resolution is a correctness requirement, not a nicety. The regression
fixture is ``PartialName::join``: the spec writes ``Result<Self, name::Error>``
and the stub writes ``Result<Self, Error>``, resolving through
``pub type Error = gix_validate::reference::name::Error;``. A differ that
reports that as a divergence is too noisy to be run, and a gate nobody runs is
worth nothing.

Scope: Rust. Go and Java stubs are parsed by nobody yet -- rather than pass
them silently (the dummy-gate trap: a green that means "not checked"), this
exits non-zero with an explicit NOT_IMPLEMENTED.

Usage
-----
    python harness/spec_stub_diff.py <spec.md> <stub_root>

Exit codes: 0 = no divergence, 1 = divergence(s) found, 2 = cannot run.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


def tool_md5() -> str:
    """The md5 of this file's own bytes, read at startup.

    Every verdict this tool prints is a verdict *of a version*. Three sessions
    have already quoted a check-26 result with no differ version beside it, and
    one of them was executing a `__pycache__` image of source that no longer
    exists -- a result nobody can reproduce or attribute. A hardcoded constant
    would drift from the source it labels, so the stamp is computed from
    ``__file__`` and is wrong only if the file is unreadable, which it says.
    """
    try:
        return hashlib.md5(Path(__file__).read_bytes()).hexdigest()
    except OSError:
        return "unreadable"


TOOL = tool_md5()

# ---------------------------------------------------------------- normalizing

LIFETIME = re.compile(r"'\w+\s*")
WS = re.compile(r"\s+")
ELIDED = "\x00"   # marks where a comment stood, so an elided type stays visible


def strip_type(text: str) -> str:
    """Whitespace- and lifetime-insensitive form of a type expression.

    Purely syntactic. Module paths are deliberately left alone here -- they are
    resolved against the referring module by `canon_paths`, because `self::`
    and `super::` mean different things depending on where they are written.
    """
    # `&mut T`, `& mut T` and `&'a mut T` are one and the same reference, and
    # all three have to reach the whitespace pass below in one spelling -- it
    # would otherwise see `mut` as a significant word and keep the space that
    # separates it from the type, so `& mut T` and `&mut T` compared unequal.
    #
    # The fold used to go to plain `&`, which made mutability vanish: `&mut
    # [u8]` and `&[u8]` became the same string, and so did `&mut self` and
    # `&self`. Neither pair is the same type and neither substitution compiles,
    # so a stub that got either backwards passed this check and then failed the
    # oracle link -- exactly the silent class of failure this tool exists to
    # catch. The fold now preserves `mut`.
    out = re.sub(r"&\s*(?:'[A-Za-z_]\w*\s*)?mut\b\s*", "&mut ", text)
    out = LIFETIME.sub("", out)
    # Whitespace between two identifier characters is *significant*: it is the
    # only thing separating `dyn` / `impl` from the trait path that follows.
    # Deleting it glued `Box<dyn DynNestedProgress>` into
    # `Box<dynDynNestedProgress>`, which cost twice over -- the path tokenizer
    # read one token where there are two, and the alias table's
    # `(?<![\w:])Name(?![\w])` lookup could no longer fire, because the
    # character before the name was now the `n` of `dyn`. Import resolution was
    # dead on every trait object in the crate, and it failed *silently*, as a
    # type divergence between two spellings of the same type. Every other
    # space is noise and still goes.
    out = WS.sub(" ", out).strip()
    out = re.sub(r"\s+(?![A-Za-z0-9_])", "", out)
    out = re.sub(r"(?<![A-Za-z0-9_])\s+", "", out)
    out = out.replace(ELIDED, "?")
    # A comment can stand *beside* a written type (`(/* private */ BString)`) or
    # *instead of* one (`Result<LineRef, /* decode error */>`). Only the second
    # leaves the type position blank. Drop the sentinel wherever an identifier
    # abuts it, or every spec that annotates a field's visibility in a comment
    # reports its own written types as unspecified.
    out = re.sub(r"\?(?=[A-Za-z_&\[('])", "", out)
    out = re.sub(r"(?<=[A-Za-z0-9_>\])])\?", "", out)
    # `Reverse<'a, File>` leaves `<,File>`; that comma is an artifact of
    # lifetime stripping, not a missing type. A genuinely missing type is `?`.
    for _ in range(4):
        nxt = re.sub(r"([<(,])\s*,", r"\1", out)
        nxt = re.sub(r",\s*([>)])", r"\1", nxt)
        if nxt == out:
            break
        out = nxt
    # `Category<'a>` -> `Category`, `Transaction<'s,'p>` -> `Transaction`:
    # once lifetimes are gone the generic list holds only commas.
    while True:
        collapsed = re.sub(r"<[,\s]*>", "", out)
        if collapsed == out:
            break
        out = collapsed
    return out.rstrip(",;")


def last_segment(text: str) -> str:
    return text.rsplit("::", 1)[-1]


def base_path(text: str) -> str:
    """`data::File<MMap>` -> `data::File`; `Bytes<'a>` -> `Bytes`.

    Generic *arguments* are not part of a declaration's identity for pairing
    purposes: `impl data::File<MMap>` and `impl<T: FileData> data::File<T>`
    declare methods on one and the same type, and a stub writes `impl File`
    for both. This was implemented on the stub side only, so a spec that
    honestly wrote its instantiations could not pair with its own stub -- one
    of the three defects that turned pack-decode's generic-header revert into
    a wall of bogus METHOD_MISSING. Both sides call this now.
    """
    i = text.find("<")
    return (text[:i] if i >= 0 else text).strip()


def match_angles(text: str, start: int) -> int:
    """Index just past the `>` closing the `<` at ``start``, or -1.

    A regex cannot do this: `impl<T: Into<Cow<'a, str>>>` nests, and
    `[^>]*` stops at the first `>` it meets, which is the *inner* one. That
    single character is why every generic impl header in a spec parsed as no
    header at all. `->` and `=>` are arrows, not brackets -- counting the `>`
    of a `Fn(u8) -> bool` bound drove the depth negative and lost the header
    just as thoroughly.
    """
    depth = 0
    prev = ""
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "<":
            depth += 1
        elif ch == ">" and prev not in "-=":
            depth -= 1
            if depth == 0:
                return i + 1
        prev = ch
    return -1


def _depth_scan(text: str):
    """Yield ``(index, char, depth)`` with `<>`, `()`, `[]`, `{}` all counted.

    ``depth`` is the nesting level *after* the character, so the `{` that opens
    a block reports depth 1.
    """
    depth = 0
    prev = ""
    for i, ch in enumerate(text):
        if ch in "<([{":
            depth += 1
        elif ch in ")]}" or (ch == ">" and prev not in "-="):
            depth -= 1
        yield i, ch, depth
        prev = ch


def split_keyword(text: str, kw: str):
    """Split ``text`` at the first top-level ``kw``; None if it does not occur.

    `for` and `where` both appear inside bounds (`for<'r> Fn(..)`, a nested
    `where`), so the split has to be depth-aware or an impl header loses its
    target to its own bound list. A punctuation keyword gets the one boundary
    rule it needs instead: the `:` of a supertrait list is a separator, the two
    `:` of a path are not.
    """
    n = len(kw)
    wordy = kw[0].isalpha()
    for i, ch, depth in _depth_scan(text):
        if depth or not text.startswith(kw, i):
            continue
        before = text[i - 1] if i else " "
        after = text[i + n] if i + n < len(text) else " "
        if wordy:
            if (before.isalnum() or before in "_:"
                    or after.isalnum() or after in "_:"):
                continue
        elif before == ":" or after == ":":
            continue
        return text[:i], text[i + n:]
    return None


def top_level_brace(text: str) -> int:
    """Index of the `{` that opens a block, ignoring braces inside a type."""
    for i, ch, depth in _depth_scan(text):
        if ch == "{" and depth == 1:
            return i
    return -1



def generic_param_names(src: str) -> set[str]:
    """Names bound by a generic parameter list: `<'a, const N: usize, T: Bound>`.

    Only the type and const parameters matter -- a lifetime can never be an
    impl target. The set is what tells a blanket impl from an ordinary one.
    """
    out = set()
    for part in split_top_level(src):
        part = part.strip()
        if part.startswith("'"):
            continue
        part = re.sub(r"^const\s+", "", part)
        cut = split_keyword(part, ":")
        name = (cut[0] if cut else part).strip()
        m = re.match(r"^([A-Za-z_]\w*)$", name)
        if m:
            out.add(m.group(1))
    return out


class Header:
    """A parsed `impl` / `trait` block header."""

    __slots__ = ("kind", "owner", "trait_name", "blanket")

    def __init__(self, kind: str, owner: str, trait_name: str, blanket: bool):
        self.kind = kind             # "impl" | "trait"
        self.owner = owner           # implementing / declared type, base path
        self.trait_name = trait_name # trait being implemented, or ""
        self.blanket = blanket       # target is one of the impl's own params


DECL_KW = re.compile(
    r"^(?:(?P<i>impl)|(?:pub(?:\s*\([^)]*\))?\s+)?(?:unsafe\s+)?(?P<t>trait))(?![\w])")


def parse_decl_header(text: str) -> Header | None:
    """Parse `impl<G> Trait for Type where .. {` and `pub trait T: Sup {`.

    One parser, both sides. The spec side used to have its own regex that
    required whitespace after `impl` -- which real Rust never writes -- so
    `impl<T: FileData> data::File<T> {` matched nothing, every method under it
    fell through to the empty-string owner, and the nine same-named methods of
    `data::File`, `index::File` and `multi_index::File` overwrote each other in
    that one bucket. Twenty-two spec methods stopped existing, and the run
    reported neither a divergence nor a match for any of them.

    A supertrait list is not part of the trait's name either: `pub trait
    FindExt: Find {` yielded the owner `FindExt:Find`, which pairs with nothing
    on the stub side and turned all eight of its methods into a matched
    MISSING/UNDECLARED pair.
    """
    m = DECL_KW.match(text)
    if not m:
        return None
    kind = "impl" if m.group("i") else "trait"
    i = m.end()
    generics = set()
    while i < len(text) and text[i].isspace():
        i += 1
    if kind == "impl" and i < len(text) and text[i] == "<":
        j = match_angles(text, i)
        if j < 0:
            return None
        generics = generic_param_names(text[i + 1:j - 1])
        i = j
    brace = top_level_brace(text[i:])
    head = text[i:i + brace] if brace >= 0 else text[i:]
    cut = split_keyword(head, "where")
    if cut:
        head = cut[0]
    head = head.strip().rstrip(",").strip()
    if not head:
        return None
    if kind == "trait":
        # `Name<G>: Supertrait + Other` -- the supertraits are obligations on
        # the implementor, not part of the name.
        cut = split_keyword(head, ":")
        if cut:
            head = cut[0]
        # A trait's own generic list is written after the name, so it is still
        # attached here; `base_path` takes it off.
        owner = base_path(strip_type(head))
        return Header("trait", owner, "", False) if owner else None
    cut = split_keyword(head, "for")
    trait_src, owner_src = (cut[0], cut[1]) if cut else ("", head)
    owner = base_path(strip_type(owner_src))
    trait_name = last_segment(base_path(strip_type(trait_src))) if trait_src else ""
    if not owner:
        return None
    return Header("impl", owner, trait_name, owner in generics)


def norm_trait(text: str) -> str:
    """A trait obligation reduced to the name a `#[derive]` would spell.

    `serde::Serialize`, `Iterator<Item = u8>` and `core::iter::FusedIterator`
    all name traits a stub satisfies by deriving or implementing `Serialize`,
    `Iterator` and `FusedIterator`. Comparing the written spellings instead
    meant a qualified obligation matched nothing -- and because the layout-A
    obligation-line pattern rejected `::` and `<` outright, those lines were
    not merely unmatched, they were never read at all. Both ends normalize
    here so the comparison is between trait identities.
    """
    return last_segment(base_path(text.strip()))


class Aliases:
    """``pub type X = Y`` table, keyed by (module, name) so that two distinct
    ``Error`` aliases in different modules never collide."""

    def __init__(self) -> None:
        self.table: dict[tuple[str, str], str] = {}
        self.crate = ""   # crate under specification; see `canon_paths`
        # Every crate that is NOT this one. A bare name may resolve against
        # a crate-local path but never against one of these.
        self.externs: frozenset[str] = frozenset({"std", "core", "alloc"})
        # Every type name the crate under specification declares itself. A
        # bare name the crate does not declare cannot mean a crate-local type,
        # which is the only thing that makes a spec's `RelativePath` and a
        # stub's `gix_path::RelativePath` safely the same type.
        self.local: frozenset[str] = frozenset()
        # Each such match, recorded. It rests on the crate's own namespace
        # rather than on the two sides writing the same path, so it is named
        # in the summary beside the other assumed pairings.
        self.by_bare_name: dict[str, int] = {}

    def add(self, module: str, name: str, target: str) -> None:
        self.table[(module, name)] = strip_type(target)

    def add_import(self, module: str, name: str, target: str) -> None:
        """Register a `use` alias without displacing a `pub type` of that name.

        A stub writes `BStr` where the spec writes `gix_object::bstr::BStr`;
        without the import table every imported type reads as a divergence and
        the differ is too noisy to run. Semantic aliases win over naming ones.
        """
        self.table.setdefault((module, name), strip_type(target))

    def resolve(self, type_text: str, module: str) -> str:
        """Rewrite every alias reference in ``type_text`` to its target.

        A bare ``Error`` is looked up in the enclosing module; a qualified
        ``name::Error`` is looked up in the module its path names.
        """
        text = strip_type(type_text)
        for _ in range(4):  # aliases of aliases; bounded to avoid cycles
            changed = False
            for (mod, name), target in self.table.items():
                for form in (f"{mod}::{name}", name):
                    pattern = re.compile(rf"(?<![\w:]){re.escape(form)}(?![\w])")
                    if not pattern.search(text):
                        continue
                    # A bare name only resolves inside its own module.
                    if form == name and mod != module:
                        continue
                    text = pattern.sub(target, text)
                    changed = True
            if not changed:
                break
        return text


PATH_SEGMENTS = re.compile(r"\b\w+(?:::\w+)+")


class Reexports:
    """`pub use` statements, as declaration path -> the public paths it also has.

    A crate declares an item in a private implementation module and re-exports
    it where users are meant to name it. gix-config's stub writes
    ``pub use mutable::{multi_value::MultiValueMut, ..}`` in `file`, so the
    spec's `file::MultiValueMut` and the stub's
    `file::mutable::multi_value::MultiValueMut` are one type; crop's stub
    writes ``pub mod iter { pub use crate::iterators::*; }``, so `iter::Bytes`
    and `iterators::Bytes` are one type. Neither pair is a `::`-boundary suffix
    of the other, so the suffix rule cannot see it.

    Before this table existed, `match_key` reached those pairings through a
    single-candidate fallback: when exactly one stub declaration had the same
    final segment, it was accepted whatever its path. That rule pairs a
    re-export correctly and pairs `packed::iter::Error` with `file::find::Error`
    just as confidently, and the two outcomes are indistinguishable in the
    output. This is the same pairing made from the crate's own `pub use`
    statements -- evidence rather than a guess -- and what it cannot reach is
    reported instead of assumed.
    """

    def __init__(self) -> None:
        self.named: dict[str, set[str]] = {}      # decl path -> {public path}
        self.globs: list[tuple[str, str]] = []    # (public module, source module)

    def add(self, module: str, name: str, target: str) -> None:
        public = f"{module}::{name}" if module else name
        if public != target and target:
            self.named.setdefault(target, set()).add(public)

    def add_glob(self, module: str, source: str) -> None:
        if source and source != module:
            self.globs.append((module, source))

    def public_paths(self, decl: str) -> set[str]:
        """``decl`` plus every path a `pub use` also makes it reachable by."""
        out = {decl}
        for _ in range(3):   # re-export of a re-export; bounded against cycles
            grown = set(out)
            for path in out:
                grown |= self.named.get(path, set())
                for public, source in self.globs:
                    if path == source:
                        grown.add(public)
                    elif path.startswith(source + "::"):
                        tail = path[len(source) + 2:]
                        grown.add(f"{public}::{tail}" if public else tail)
            if grown == out:
                break
            out = grown
        return out


def record_reexport(path_text: str, module: str, reexports: Reexports,
                    aliases: Aliases) -> None:
    """Register one `pub use ...;`, resolved against the module it sits in.

    `use` paths that do not start with `crate`/`self`/`super` or a dependency
    name are uniform paths: a bare first segment names a sibling item of the
    module the statement is written in, which is how `pub use mutable::..` in
    `file/mod.rs` reaches `file::mutable::..`. Anything rooted in another crate
    re-exports somebody else's type and says nothing about this crate's
    declaration paths.
    """
    path_text = path_text.strip()
    m = re.match(r"^(.*?)::\{(.*)\}$", path_text, re.S)
    if m:
        prefix, inner = m.group(1).strip(), m.group(2)
        for part in split_top_level(inner):
            record_reexport(f"{prefix}::{part.strip()}", module, reexports, aliases)
        return
    if not path_text:
        return
    m = re.match(r"^(.+?)\s+as\s+(\w+)$", path_text)
    if m:
        full, name = m.group(1).strip(), m.group(2)
    else:
        full, name = path_text, last_segment(path_text)
    glob = full.endswith("*")
    if glob:
        full = full[:-1].rstrip(": ")
    if not re.fullmatch(r"[\w:]*", full) or not full:
        return
    rooted = full.split("::", 1)[0]
    if rooted in ("crate", "self", "super") or rooted == aliases.crate:
        target = canon_paths(full, module, aliases.crate)
    elif rooted in aliases.externs:
        return
    else:
        target = f"{module}::{full}" if module else full
    target = target.strip(":")
    if glob:
        reexports.add_glob(module, target)
    elif name not in ("self", "super", "crate"):
        reexports.add(module, name, target)



def canon_paths(text: str, module: str, crate: str = "") -> str:
    """Rewrite `crate::` / `self::` / `super::` against the referring module.

    The spec writes paths from the crate root; a stub writes the same type as
    `self::packed::X` from inside `file`. Resolving the prefix turns those into
    one string. This replaces an earlier `collapse_paths` that reduced every
    `a::b::C` to `C` -- that made `std::io::Error` and `name::Error` compare
    equal, so a stub returning the wrong error type passed silently.

    ``crate`` is the crate under specification, read from the stub's
    Cargo.toml. A spec routinely writes its own crate's paths absolutely
    (`gix_ref::name::Error`) where the stub writes `crate::name::Error` or a
    bare imported `Error`; without this the two never reconcile and every
    self-referential path in the spec reads as a divergence. Only the crate's
    own name is stripped -- `gix_validate::...` stays fully qualified, which
    is what keeps the `PartialName::join` fixture honest.
    """
    text = re.sub(r"(?<![\w:])crate::", "", text)
    if crate:
        text = re.sub(rf"(?<![\w:]){re.escape(crate)}::", "", text)
    if module:
        text = re.sub(r"(?<![\w:])self::", f"{module}::", text)
        parent = module.rsplit("::", 1)[0] if "::" in module else ""
        text = re.sub(r"(?<![\w:])super::", f"{parent}::" if parent else "", text)
    else:
        text = re.sub(r"(?<![\w:])(?:self|super)::", "", text)
    return text


def path_suffix_match(a: str, b: str, externs: frozenset[str] = frozenset(),
                      aliases: "Aliases | None" = None) -> bool:
    """True when one path is a `::`-boundary suffix of the other.

    `buffer::open::Error` matches `packed::buffer::open::Error` -- a stub
    inside module `packed` writes the path relative. `io::Error` does NOT
    match `reference::name::Error`. The boundary is what keeps this honest.

    A single bare segment is the hard case. `Error` must not be assumed equal
    to somebody else's `Error`, which is why the alias table exists -- but a
    crate re-exports its own types at the root all the time, so a spec's
    `PackageGraph` and a stub's `crate::graph::PackageGraph` are the same type
    and reporting them as divergent is the kind of noise that gets a gate
    switched off. ``externs`` (the stub's declared dependencies, plus the
    standard library) draws the line: a bare name matches a crate-local path
    with the same tail, and never a path rooted in another crate. That keeps
    the `PartialName::join` fixture honest -- `std::io::Error` is rooted in
    `std` and stays a divergence.
    """
    if a == b:
        return True
    lo, hi = (a, b) if len(a) < len(b) else (b, a)
    if "::" in lo:
        return hi.endswith("::" + lo)
    if not lo or not hi.endswith("::" + lo):
        return False
    if hi.split("::", 1)[0] not in externs:
        return True
    # The path is rooted in another crate and the other side wrote a bare
    # name. That is a divergence when the crate under specification declares
    # something of that name -- the bare name plausibly meant *that* -- and it
    # is not when the crate declares nothing of the kind: the spec's
    # `&RelativePath` cannot be anything but the `gix_path::RelativePath` the
    # stub wrote, and reporting four such parameters as divergent sends
    # someone to correct a stub that is right. Recorded either way, because
    # it rests on absence of evidence rather than on agreement.
    if aliases is None or lo in aliases.local:
        return False
    aliases.by_bare_name[f"{lo} = {hi}"] = aliases.by_bare_name.get(f"{lo} = {hi}", 0) + 1
    return True


PATH_TOKEN = re.compile(r"[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*")


def split_expr(text: str) -> tuple[str, list[str]]:
    """Separate a type expression into its punctuation skeleton and its paths."""
    toks: list[str] = []

    def grab(m: re.Match) -> str:
        toks.append(m.group(0))
        return "@"

    return PATH_TOKEN.sub(grab, text), toks


def exprs_match(a: str, b: str, externs: frozenset[str] = frozenset(),
                aliases: "Aliases | None" = None) -> bool:
    """Compare two whole type expressions path-token by path-token.

    Relative paths live *inside* an expression -- the spec writes
    `Result<Self, packed::buffer::open::Error>` where a stub inside `packed`
    writes `Result<Self, buffer::open::Error>`. Comparing the expressions as
    single strings cannot see that, so the skeleton (`Result<@,@>`) must match
    exactly and each path is then checked in position.
    """
    if a == b:
        return True
    # Reference-ness is never negotiable, whatever the paths say.
    if a.count("&") != b.count("&"):
        return False
    sa, ta = split_expr(a)
    sb, tb = split_expr(b)
    if sa != sb or len(ta) != len(tb):
        return False
    return all(path_suffix_match(x, y, externs, aliases) for x, y in zip(ta, tb))


def is_unspecified(type_text: str) -> bool:
    """True when a type position was left blank in the spec.

    `Result<LineRef<'a>, /* decode error */>` normalizes to `Result<LineRef,>`
    once the comment is stripped: the spec never says what the error type is.
    That is a spec defect and must not be reported as a stub divergence.
    """
    return "?" in type_text or not type_text


SELF_TYPE = re.compile(r"(?<![\w:])Self(?![\w])")


def type_candidates(type_text: str, aliases: Aliases, module: str,
                    self_ty: str = "") -> set[str]:
    """Every spelling of ``type_text`` this differ knows how to produce.

    Resolution must only ever ADD matches, never remove one, so the raw form
    stays a candidate beside every rewrite of it.
    """
    forms = {strip_type(type_text), aliases.resolve(type_text, module)}
    if self_ty:
        # Inside an inherent impl `Self` *is* the concrete type, and a spec
        # that writes `-> Self` against a stub that writes `-> MemoryCappedHashmap`
        # is not a divergence. Added as an extra candidate rather than
        # substituted in place, so a spec and stub that both write `Self`
        # still match on the raw form even when the two sides disagree about
        # how the impl target is spelled.
        forms |= {SELF_TYPE.sub(self_ty, f) for f in list(forms)}
    return {canon_paths(t, module, aliases.crate) for t in forms}


def types_match(spec_type: str, stub_type: str, aliases: Aliases,
                spec_mod: str, stub_mod: str,
                spec_self: str = "", stub_self: str = "") -> bool:
    """True when two type expressions denote the same type.

    Alias resolution may fire on one side and not the other -- the spec writes
    a path that matches an alias entry while the stub writes the same type
    through `self::`, or vice versa. Resolving must only ever ADD matches, so
    both the raw and the resolved form of each side are candidates and any
    agreeing pair is enough.
    """
    cands_a = type_candidates(spec_type, aliases, spec_mod, spec_self)
    cands_b = type_candidates(stub_type, aliases, stub_mod, stub_self)
    # `all()` over the pairs would be wrong and `any()` has to run to the
    # first success only, or a failed candidate's bare-name note is recorded
    # for a comparison that succeeded another way. Probe without the recorder
    # first; re-run the winning pair with it.
    for a in cands_a:
        for b in cands_b:
            if exprs_match(a, b, aliases.externs):
                return True
    for a in cands_a:
        for b in cands_b:
            if exprs_match(a, b, aliases.externs, aliases):
                return True
    return False


# ------------------------------------------------------------------ spec side

# One entry in a layout-A trait-obligation list. Obligations are written the
# way Rust writes trait paths, not the way `#[derive]` writes bare names:
# `serde::Serialize`, `Iterator<Item = u8>`, `PartialEq<Rope>`. The pattern
# used to accept `[A-Za-z]\w*` only, so any line carrying `::` or `<` matched
# nothing and fell through every branch of the parser -- silently, leaving the
# obligation unrecorded and unreported. Those are the obligations most likely
# to be hand-written impls rather than derives, which is to say the ones most
# worth checking.
DERIVE_ITEM = (r"[A-Za-z][\w]*(?:::[A-Za-z][\w]*)*"
               r"(?:<(?:[^<>]|<[^<>]*>)*>)?")
DERIVE_LINE = re.compile(rf"^{DERIVE_ITEM}(\s*,\s*{DERIVE_ITEM})*\s*,?$")

# A payload-bearing enum variant: `SectionValueName(&'a BStr)` or
# `Comment { tag: u8, text: &'a BStr }`. The `Fn` family is the only trait
# bound written with parentheses, so it is excluded explicitly rather than
# left to be misread as a variant.
VARIANT_LINE = re.compile(r"^(?!Fn(?:Mut|Once)?\s*\()([A-Z]\w*)\s*[({]")

# `Name(T)` / `Name<'a>(T, U)` -- a tuple struct declared on one line.
TUPLE_DECL = re.compile(r"^([A-Za-z_][\w:]*)\s*(?:<[^>]*>)?\s*\((.+)\)\s*;?\s*$")
# A named field, allowing `pub`, `pub(crate)`, `pub(super)` ... visibility.
FIELD_DECL = re.compile(r"^(?:pub(?:\s*\([^)]*\))?\s+)?(\w+)\s*:\s*(.+?),?$")
VIS_PREFIX = re.compile(r"^pub(?:\s*\([^)]*\))?\s+")


def split_top_level(text: str) -> list[str]:
    """Split on commas that are not nested inside <>, (), [] or {}.

    Braces count because a nested `use` group is the one place a comma list
    nests inside them: `std::{io, path::{Path, PathBuf}}` has two top-level
    parts, not three. Splitting inside the inner group handed `record_use` the
    fragments `path::{Path` and `PathBuf}`, neither of which is a path, so the
    whole group registered nothing.
    """
    parts, buf, depth = [], "", 0
    for ch in text:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def tuple_fields(inner: str) -> dict[str, str]:
    """Positional fields of a tuple struct, keyed `0`, `1`, ... .

    `FullNameRef(BStr)` is `#[repr(transparent)]`; a stub that writes
    `FullNameRef(BString)` builds standalone and breaks at oracle-link time,
    so the element type is as load-bearing as any named field.

    An empty body carries no information -- specs that hide the element write
    `X(/* private */)`, which becomes `X()` once comments are stripped. That
    must yield no fields rather than a field whose type is the empty string.
    """
    out = {}
    for i, part in enumerate(split_top_level(inner)):
        cleaned = strip_type(VIS_PREFIX.sub("", part))
        if not cleaned or cleaned == "?":
            continue
        out[str(i)] = cleaned
    return out


def fenced_block(lines: list[str], heading: str) -> list[str]:
    """Body of the first fenced block after ``heading``."""
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == heading)
    except StopIteration:
        return []
    i = start + 1
    while i < len(lines) and not lines[i].strip().startswith("```"):
        i += 1
    j = i + 1
    while j < len(lines) and not lines[j].strip().startswith("```"):
        j += 1
    return lines[i + 1:j]


def parse_spec_types(lines: list[str], aliases: Aliases):
    """{type_path: {'derives': set, 'fields': {name: type}}} from `#### Types`."""
    out: dict[str, dict] = {}
    alias_keys: set[str] = set()
    current = None
    in_body = False
    for raw in fenced_block(lines, "#### Types"):
        line = raw.split("//")[0].rstrip()
        if not line.strip():
            continue
        text = line.strip()
        if text == "}":
            in_body = False
            continue
        if not line.startswith((" ", "\t")):
            # `X = Y` is a type alias, not a declaration with derives.
            alias = re.match(r"^([\w:]+)\s*$", text)
            head = re.match(r"^([A-Za-z_][\w:]*)", text)
            if not head:
                continue
            current = head.group(1)
            out.setdefault(current, {"derives": set(), "fields": {},
                                     "variants": set()})
            tup = TUPLE_DECL.match(text)
            if tup:
                out[current]["fields"].update(tuple_fields(tup.group(2)))
            in_body = text.endswith("{")
            continue
        if in_body:
            field = FIELD_DECL.match(text)
            if field and current:
                out[current]["fields"][field.group(1)] = strip_type(field.group(2))
            if text.startswith("}"):
                in_body = False
            continue
        if text.endswith("{"):
            in_body = True
            continue
        if text.startswith("="):
            target = text.lstrip("= ").strip()
            if current:
                mod = current.rsplit("::", 1)[0] if "::" in current else ""
                aliases.add(mod, last_segment(current), target)
                alias_keys.add(current)
            continue
        if current and VARIANT_LINE.match(text):
            # Layout A writes enum variants on the same indented lines it uses
            # for trait obligations. `Comment { tag: u8 }` and `Name(BString)`
            # carry a payload and cannot be confused with an obligation, but a
            # payload-free variant is a bare capitalised identifier and reads
            # exactly like one -- `EventRef`'s `KeyValueSeparator` was recorded
            # as a trait the stub had to implement, and reported DERIVE_MISSING
            # against a stub that was correct. The layout's own convention is
            # that obligations come first, so once a payload-bearing variant
            # has been seen the remaining bare names in that body are variants.
            #
            # This makes the type an *enum* as far as the rest of the run is
            # concerned; the variants themselves stay unchecked, which the
            # SCOPE line says out loud rather than leaving to be assumed.
            out[current]["variants"].add(VARIANT_LINE.match(text).group(1))
            continue
        if current and out[current]["variants"]:
            bare = re.match(r"^([A-Za-z_]\w*)\s*,?$", text)
            if bare:
                out[current]["variants"].add(bare.group(1))
                continue
        if current and DERIVE_LINE.match(text):
            # `Iterator<Item = u8>` and `serde::Serialize` name the same
            # obligations a `#[derive]` would spell `Iterator` and `Serialize`.
            out[current]["derives"] |= {norm_trait(t) for t in split_top_level(text)
                                        if norm_trait(t)}
    # The module comes from the declaration's own path -- layout A writes every
    # type crate-root qualified, so `store::init::Options` is declared *in*
    # `store::init`, and a field written `super::WriteReflog` means
    # `store::WriteReflog`. Without that context `super::` resolves against the
    # crate root and the field reads as divergent from a stub that wrote the
    # identical text.
    #
    # Only the entries that actually carried an `= Target` line are dropped.
    # The filter used to be "no derives and no fields", which is a guess about
    # what an alias looks like rather than a fact about this declaration, and
    # it silently deleted every real type whose obligations the spec states in
    # prose and whose fields are private -- three of them on pack-decode. A
    # deleted type is compared against nothing in either direction, so a stub
    # that declares it wrong, or not at all, passes.
    return {k: dict(v, module=k.rsplit("::", 1)[0] if "::" in k else "")
            for k, v in out.items() if k not in alias_keys}


USE_STMT = re.compile(r"^(?:pub(?:\s*\([^)]*\))?\s+)?use\b")

# A stub declaration is terminated by `;` or by the `{` of its body, so the
# scanner stops the return type at either. An array type carries a `;` of its
# own: `-> smallvec::SmallVec<[u8; 28]>` was recorded as `SmallVec<[u8`, while
# the spec-side parser -- which anchors on `;$` and so cannot make this mistake
# -- recorded the whole thing. Two parsers disagreeing about the same
# declaration, reported as a divergence between spec and stub. Anything up to
# two levels of brackets is swallowed whole; `[[u8; 2]; 3]` is the first shape
# that would still truncate, and nothing in these crates returns one.
BRACKETED = r"\[(?:[^\[\]]|\[[^\[\]]*\])*\]"
UNTIL_BODY = rf"(?:[^{{;\[]|{BRACKETED})+?"
UNTIL_SEMI = rf"(?:[^;\[]|{BRACKETED})+?"


def logical_lines(raw_lines):
    """Join wrapped declarations into one logical statement each.

    A Rust signature routinely wraps before its return type::

        fn to_full_name<'a>(&self, short_name: impl Into<&'a BStr>)
            -> Result<FullName, name::Error>;

    A line-at-a-time parser sees no `;`, silently skips it, and then reports
    the method as absent from whichever side it was parsing -- four false
    divergences on the first spec this ran against. Flush only when the
    delimiters are balanced and the text closes a statement; keep buffering
    otherwise, so a parameter list broken across lines stays one statement
    while a struct field ending in `,` does not absorb the next line.
    """
    buf = ""
    for raw in raw_lines:
        text = re.sub(r"//.*$", "", raw).strip()
        if not text:
            if buf:
                yield buf
                buf = ""
            continue
        buf = f"{buf} {text}" if buf else text
        angles = buf.replace("->", "")
        balanced = (buf.count("(") == buf.count(")")
                    and buf.count("[") == buf.count("]")
                    and angles.count("<") == angles.count(">"))
        if balanced and buf[-1] in ";{},]":
            # A wrapped `where` clause ends each bound line in `,`. Flushing
            # there hands the fn matcher a signature with no `{` or `;` to
            # anchor on, so the method is silently dropped from that side and
            # reported MISSING against the other. Hold the statement open until
            # its body opens or its declaration terminates.
            if buf[-1] not in ";{" and re.search(r"(?<![\w:])where\b", buf):
                continue
            # A `use` group wrapped over several lines opens with a trailing
            # `{`, and `{` is in the flush set above, so `use std::{` was
            # flushed on its own and the `use` matcher -- which needs the `;`
            # -- never saw the statement at all. Every name in every wrapped
            # import group was therefore absent from the alias table, while the
            # same import written on one line registered fine: two files
            # disagreeing about `Option<PathBuf>` for no reason visible in
            # either. Keep buffering until the terminator arrives. Narrowly
            # scoped to `use`: making `{` stop terminating in general would
            # swallow every `impl Foo {` frame in the crate.
            if not buf.endswith(";") and USE_STMT.match(buf):
                continue
            yield buf
            buf = ""
    if buf:
        yield buf


# `const fn`, `unsafe fn`, `async fn` and `extern "C" fn` are as much public
# surface as a plain `fn`, and both parsers used to require `fn` to follow
# `pub` immediately -- so every one of them was invisible on both sides at
# once, which is why the omission never showed up as a divergence.
FN_QUALIFIERS = r"(?:(?:const|async|unsafe)\s+|extern\s+\"[^\"]*\"\s+)*"
FN_HEAD = rf"(?:pub(?:\s*\([^)]*\))?\s+)?{FN_QUALIFIERS}fn\s+[\w:]+\s*"
FN_GENERICS = re.compile(rf"^({FN_HEAD})<")
FN_DECL = re.compile(rf"^{FN_HEAD}\((.*?)\)\s*(?:->\s*(.+?))?\s*;$")
FN_NAME = re.compile(rf"^(?:pub(?:\s*\([^)]*\))?\s+)?{FN_QUALIFIERS}fn\s+([\w:]+)")


def note_collision(store: dict, key, entry: dict, notes) -> None:
    """Record a declaration that overwrote a *different* one under the same key.

    Two keys colliding is how twenty-two pack-decode methods disappeared
    between the parse and the comparison: `version`, `path` and `checksum` are
    declared on three different `File` types, and with the owner unread they
    were one key each. The comparison cannot see that -- the loser is simply
    not there -- so the count has to be carried out of the parser and printed.

    A spec that declares the same method twice, identically, has lost nothing;
    reporting those buries the real ones. Only a disagreement is a collision.
    """
    prev = store.get(key)
    if notes is None or prev is None:
        return
    if all(prev.get(f) == entry.get(f) for f in ("arity", "params", "ret")):
        return
    owner, name = key
    notes.append(
        f"{owner}::{name} (`{prev['ret']}`/{prev['arity']}p replaced by "
        f"`{entry['ret']}`/{entry['arity']}p)")


def strip_fn_generics(text: str) -> str:
    """`fn f<F: FnMut(u8) -> bool>(g: F)` -> `fn f(g: F)`.

    Both parsers matched a generic list with `<[^>]*>`, which stops at the
    first `>`. A bound containing an arrow -- `FnMut(..) -> bool`, or any
    associated-type binding -- ends the match in the middle of itself, the
    parameter list is then not where the pattern expects it, and the whole
    declaration fails to match. It fails on *both* sides identically, so the
    method is simply absent from the comparison and neither direction reports
    anything. Cut the list on bracket balance instead.
    """
    m = FN_GENERICS.match(text)
    if not m:
        return text
    j = match_angles(text, m.end() - 1)
    return text if j < 0 else text[:m.end() - 1] + text[j:]


def parse_spec_methods(lines: list[str], aliases: Aliases, notes=None):
    """{(owner, method): {'arity', 'params', 'ret'}} from `#### Method Signatures`.

    Owners come from `parse_decl_header`, so a group heading may carry its own
    generic parameters, bounds and `where` clause -- which is how Rust is
    written, and which the previous regex could not read at all. Three further
    shapes are first-class here because a spec should not have to be reshaped
    to be parsed:

    * a free function outside any impl block, owned by the module it sits in
      (a `mod a::b { .. }` wrapper, a `// crate::a::b` comment, or a qualified
      `fn a::b::decode` name). Filing free functions under an impl-shaped
      pseudo-heading was one of the deformations pack-decode's catalog carried;
    * a blanket impl, whose target is one of the impl's own type parameters.
      It declares no member of any named type, so it contributes none -- rather
      than minting methods on a phantom type called `T`;
    * a trait impl, whose methods belong to the trait, not to the implementing
      type. The stub side never recorded these (a trait impl's methods carry no
      `pub`), so recording them here reported every one as MISSING.

    ``notes`` collects declarations whose owner could not be determined. They
    used to be filed under the empty string, which is one shared bucket: nine
    methods named `version`, `path`, `checksum` and so on, declared on three
    different `File` types, overwrote each other there and twenty-two spec
    methods simply ceased to exist between the parse and the comparison.
    Nothing is filed under an owner that was not read; it is reported instead.
    """
    out: dict[tuple[str, str], dict] = {}
    src = strip_block_comments("\n".join(fenced_block(lines, "#### Method Signatures")))
    mod_stack: list[str] = []
    frames: list[tuple[int, str, str]] = []    # (depth opened at, kind, payload)
    depth = 0

    for raw in logical_lines(module_directives(src, aliases.crate)):
        text = raw.strip()
        if not text:
            continue
        if text.startswith(MODULE_DIRECTIVE):
            if not frames:
                mod_stack = [p for p in
                             text[len(MODULE_DIRECTIVE):].rstrip(";").split("::") if p]
            continue
        while text.startswith("#["):
            stripped = LEADING_ATTR.sub("", text, count=1)
            if stripped == text:
                break
            text = stripped
        if not text or text.startswith("#["):
            continue

        opens, closes = text.count("{"), text.count("}")
        module = "::".join(mod_stack)
        opened: tuple[str, str] | None = None

        m = re.match(r"^(?:pub(?:\s*\([^)]*\))?\s+)?mod\s+([\w:]+)", text)
        if m and opens:
            opened = ("mod", m.group(1))
        if opened is None:
            header = parse_decl_header(text)
            if header is not None and opens:
                if header.blanket or header.trait_name:
                    opened = ("skip", "")
                else:
                    opened = (header.kind, qualify_owner(header.owner, module))
        if opened is None and not any(k == "skip" for _, k, _ in frames):
            plain = strip_fn_generics(text)
            fn = FN_DECL.match(plain)
            if fn:
                name = FN_NAME.match(plain).group(1)
                owner = next((p for _, k, p in reversed(frames)
                              if k in ("impl", "trait")), None)
                if owner is None:
                    # A free function. Its owner is the module that exports it,
                    # which the name itself may carry (`fn data::header::decode`).
                    qualifier, _, name = name.rpartition("::")
                    owner = qualify_owner(qualifier, module) if qualifier else module
                owner = base_path(strip_type(owner))
                ret = re.split(r"\bwhere\b", fn.group(2) or "()")[0]
                key = (owner, name)
                entry = {
                    "arity": count_params(fn.group(1)),
                    "params": param_types(fn.group(1)),
                    "ret": strip_type(ret or "()"),
                    "module": module,
                }
                note_collision(out, key, entry, notes)
                out[key] = entry

        if opened is not None:
            frames.append((depth, opened[0], opened[1]))
            if opened[0] == "mod":
                mod_stack.extend(p for p in opened[1].split("::") if p)
        depth += opens - closes
        while frames and depth <= frames[-1][0]:
            _, kind, payload = frames.pop()
            if kind == "mod":
                for _ in [p for p in payload.split("::") if p]:
                    if mod_stack:
                        mod_stack.pop()
    return out



def split_params(text: str) -> list[str]:
    """A parameter list split into its top-level parameters.

    `split_top_level` cannot be reused here: it treats every `>` as a closing
    bracket, so the `>` of a `->` inside a closure bound drives its depth
    negative and the commas after it stop splitting. `fn f(g: impl FnMut(u8)
    -> bool, n: usize)` read as one parameter. `_depth_scan` knows an arrow
    from an angle bracket.
    """
    parts, start = [], 0
    for i, ch, depth in _depth_scan(text):
        if ch == "," and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return [p.strip() for p in parts if p.strip()]


RECEIVERS = frozenset({"self", "&self", "&mut self"})


def param_types(params: str) -> list[str]:
    """A parameter list decomposed into one normalised type per position.

    The differ used to hold a parameter *count* and nothing else, so a
    signature's parameters were compared by counting commas. Every change that
    kept the count was invisible: `&'b mut [u8]` to `&'b mut Vec<u8>`,
    `&self` to `&mut self`, and swapping two parameters of different types.
    All three are compile errors at oracle-link time and two of them are
    invisible to prose review as well, so this was the largest dark dimension
    in the check -- and it was dark in a way that read as agreement, because
    the return type *was* compared and a green line looked like it covered the
    whole signature.

    The receiver keeps its own spelling (`self`, `&self`, `&mut self`) rather
    than being dropped, because receiver mutability is part of the surface.
    """
    out = []
    for part in split_params(params):
        if part == "..." or part.startswith("#["):
            continue
        cut = split_keyword(part, ":")
        # No top-level `:` means a receiver (`&mut self`) or an unnamed
        # parameter type; with one, everything left of it is the pattern.
        text = strip_type(cut[1] if cut else part)
        # `fn into_inner(mut self)` and `fn into_inner(self)` have the same
        # signature -- `mut` there is a binding mode inside the body, not part
        # of the receiver's type, and no caller can tell them apart. `&mut
        # self` is a different matter and keeps its `mut`.
        if text == "mut self":
            text = "self"
        out.append(text)
    return out


def count_params(params: str) -> int:
    """Number of parameters at depth zero, receiver included."""
    return len(param_types(params))



# ------------------------------------------------- other API Catalog layouts
#
# Three specs, three ways of writing the same declarations:
#
#   A  gix-ref-peel-001  pseudo-syntax under `#### Types` / `#### Method
#                        Signatures` -- bare `Name(BString)` entries, derives
#                        on their own lines. Parsed by parse_spec_types /
#                        parse_spec_methods above.
#   B  gix-ref-txn-001   real Rust in fenced blocks under `### API Catalog`,
#                        grouped by module in `####` subsections.
#   C  guppy             a markdown table whose `Declared signature` column
#                        holds real Rust, one row per member.
#
# B and C are both real Rust, so they reuse `scan_rust` rather than growing a
# second declaration parser: C synthesizes a source text from its table cells.
# One scanner means a fix to arity or return-type handling lands for every
# layout at once.


def section_lines(lines: list[str], heading: str) -> list[str]:
    """Lines under ``heading``, stopping at the next heading of same-or-higher level.

    Fence state is tracked because `#[derive(...)]` inside a Rust block starts
    with `#` and would otherwise read as a level-1 heading and end the section
    at the first attribute -- which silently yields an empty API Catalog.

    A leading section number on the heading (`### 12.2 API Catalog`) is
    tolerated. Specs that number their headings still carry an ordinary
    API Catalog table; refusing to find it made the differ report DIFF_ERROR
    on a spec it can in fact parse, and a gate that cannot find its input is
    indistinguishable from a clean surface.
    """
    level = len(heading) - len(heading.lstrip("#"))
    want = heading.lstrip("#").strip()
    numbered = re.compile(
        r"^#{%d}\s+(?:\d+(?:\.\d+)*\.?\s+)?%s$" % (level, re.escape(want))
    )
    try:
        start = next(
            i for i, l in enumerate(lines)
            if l.strip() == heading or numbered.match(l.strip())
        )
    except StopIteration:
        return []
    out = []
    in_fence = False
    for line in lines[start + 1:]:
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and re.match(r"^#{1,6}\s", s):
            lv = len(s) - len(s.lstrip("#"))
            if lv <= level:
                break
        out.append(line)
    return out


def all_fenced_blocks(lines: list[str]) -> list[str]:
    """Every fenced block body in ``lines``."""
    blocks, cur = [], None
    for line in lines:
        if line.strip().startswith("```"):
            if cur is None:
                cur = []
            else:
                blocks.append("\n".join(cur))
                cur = None
            continue
        if cur is not None:
            cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def fenced_blocks_with_heading(lines: list[str]) -> list[tuple[str, str]]:
    """Every fenced block paired with the nearest preceding heading."""
    out, cur, heading = [], None, ""
    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            if cur is None:
                cur = []
            else:
                out.append((heading, "\n".join(cur)))
                cur = None
            continue
        if cur is not None:
            cur.append(line)
        elif re.match(r"^#{1,6}\s", s):
            heading = s
    if cur:
        out.append((heading, "\n".join(cur)))
    return out


def heading_module(heading: str, crate: str) -> str:
    """Module named by a catalog subheading: ``#### `gix_ref::packed` `` -> `packed`.

    The first backticked crate path wins, and an `UpperCamel` tail is a type
    rather than a module, so ``#### `gix_ref::file::Store` — reference logs``
    scopes to `file`.
    """
    if not crate:
        return ""
    m = re.search(rf"`{re.escape(crate)}((?:::\w+)*)`", heading)
    if not m:
        return ""
    parts = [p for p in m.group(1).split("::") if p]
    if parts and parts[-1][:1].isupper():
        parts.pop()
    return "::".join(parts)


def block_module(block: str, heading: str, crate: str) -> str:
    """Default module for a block that does not scope itself.

    Deliberately conservative: a block containing a `// crate::path` comment or
    a `pub mod` wrapper already carries its own module, and imposing the
    heading on top of that would nest `store` inside `store`. Only a block that
    says nothing about where it lives inherits from its heading -- which is the
    case that matters, because ``#### `gix_ref::packed` `` is the only thing
    distinguishing `packed::Reference` from the crate-root `Reference`.
    """
    pattern = module_pattern(crate)
    if pattern is not None and any(pattern.match(l.strip()) for l in block.split("\n")):
        return ""
    if re.search(r"^\s*pub\s+mod\s+\w+", block, re.M):
        return ""
    return heading_module(heading, crate)


def parse_spec_rust_blocks(lines: list[str], aliases: Aliases, collisions=None):
    """Layout B: real Rust in fenced blocks under `### API Catalog`.

    The catalog is not the whole declaration surface. This spec puts fifteen
    public error enums under `## Error Semantics`, in the same real-Rust
    blocks with the same `// gix_ref::...` module comments, and the stub
    declares every one of them. Scanning only the catalog leaves those types
    undeclared on the spec side, so the differ either reports fifteen bogus
    TYPE_UNDECLAREDs or -- worse, via suffix matching -- pairs them all onto
    whatever `Error` it did parse and calls it agreement.

    So: the catalog, plus any other fenced block that names its module in the
    crate's own namespace. That comment is the marker of a declaration block;
    prose examples and shell transcripts do not carry it, and a block that
    declares nothing contributes nothing.
    """
    types: dict[str, dict] = {}
    methods: dict[tuple[str, str], dict] = {}
    catalog = fenced_blocks_with_heading(section_lines(lines, "### API Catalog"))
    for heading, block in catalog:
        scan_rust(block, block_module(block, heading, aliases.crate),
                  types, methods, aliases, None, None, collisions)
    if not (types or methods):
        return types, methods
    pattern = module_pattern(aliases.crate)
    if pattern is not None:
        seen = {b for _, b in catalog}
        for heading, block in fenced_blocks_with_heading(lines):
            if block in seen:
                continue
            seen.add(block)
            if any(pattern.match(l.strip()) for l in block.split("\n")):
                scan_rust(block, block_module(block, heading, aliases.crate),
                          types, methods, aliases, None, None, collisions)
    return types, methods


def split_row(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def explode_trait(sig: str) -> list[str]:
    """One-line `pub trait T { fn a(..); fn b(..); }` -> one item per line.

    Layout C puts a whole trait in a single table cell, and the scanner reads
    logical lines: with the body on the header's line the methods are never
    seen at all. Six trait methods that the guppy catalog declares in full were
    reported as present-in-stub-only for exactly this reason.
    """
    open_i = sig.find("{")
    close_i = sig.rfind("}")
    if open_i < 0 or close_i < open_i:
        return [sig]
    out = [sig[:open_i + 1]]
    body, buf, depth, prev = sig[open_i + 1:close_i], "", 0, ""
    for ch in body:
        if ch in "<([{":
            depth += 1
        elif ch in ")]}" or (ch == ">" and prev not in "-="):
            # `->` and `=>` are not closing angle brackets. Counting the arrow
            # drove depth negative, so every `;` after the first return type
            # missed the split and the trait's later methods were swallowed.
            depth -= 1
        if ch == ";" and depth == 0:
            out.append(buf.strip() + ";")
            buf = ""
        else:
            buf += ch
        prev = ch
    if buf.strip():
        out.append(buf.strip().rstrip(";") + ";")
    out.append("}")
    return out


def parse_spec_table(lines: list[str], aliases: Aliases, collisions=None):
    """Layout C: a markdown table with a declared-signature column.

    Returns (types, methods, skipped) -- ``skipped`` names rows the synthesizer
    could not turn into a declaration, so under-parsing is reported rather than
    passing as agreement.
    """
    body = section_lines(lines, "### API Catalog")
    header_i = sig_col = name_col = kind_col = None
    for i, line in enumerate(body):
        if not line.strip().startswith("|"):
            continue
        cells = [c.lower() for c in split_row(line)]
        if any("signature" in c for c in cells) and any(c == "name" for c in cells):
            header_i = i
            sig_col = next(j for j, c in enumerate(cells) if "signature" in c)
            name_col = cells.index("name")
            kind_col = cells.index("kind") if "kind" in cells else None
            break
    if header_i is None:
        return {}, {}, []

    src: list[str] = []
    skipped: list[str] = []
    header_cells = [c.lower() for c in split_row(body[header_i])]
    for line in body[header_i + 1:]:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = split_row(s)
        if len(cells) <= max(sig_col, name_col) or set(cells[0]) <= set("-: "):
            continue
        if [c.lower() for c in cells] == header_cells:
            # A catalog split across `####` subsections repeats its header row
            # once per subsection. Those repeats are not declarations.
            continue
        name = cells[name_col].strip("`")
        sig = strip_block_comments(cells[sig_col].strip().strip("`")).strip()
        kind = cells[kind_col].lower() if kind_col is not None else ""
        bare = strip_leading_attrs(sig)

        if kind.startswith("trait impl"):
            # Same rationale as the `impl ` prefix below: trait impls are not
            # compared on either side. Aggregate rows list several of them in
            # one cell without an `impl` keyword, so the Kind column is the
            # only reliable discriminator.
            continue

        if bare.startswith("pub fn") or "fn " in bare[:12]:
            owner = name.rsplit("::", 1)[0] if "::" in name else ""
            if owner:
                src.append(f"impl {owner} {{")
                src.append(sig.rstrip(";") + ";")
                src.append("}")
            else:
                # A free function: `named_feature_filter` has no receiver and
                # no owner to put in the Name column. Emitting it at top level
                # keys it as ownerless, which the comparison pairs by name
                # against whichever stub module declares it -- the same path
                # layout A's bare `fn expand` takes. Skipping it instead made
                # the whole catalog unparseable over two rows.
                src.append(sig.rstrip(";") + ";")
        elif bare.startswith("pub trait"):
            src.extend(explode_trait(sig if sig.endswith("}") else sig + ";"))
        elif bare.startswith(("pub struct", "pub enum", "pub union", "pub type")):
            decl = sig if sig.endswith(("}", ";")) else sig + ";"
            # The signature column writes the declaration as the crate writes
            # it, so `feature::Cycles` and `Cycles` are both spelled `pub
            # struct Cycles`. Only the Name column says which module each is
            # in, and without it the two collapsed onto one key: guppy's two
            # `Cycles` types were one type, their two `all_cycles` were one
            # method, and whichever row came second silently replaced the
            # first -- so the feature graph's iterator was compared against
            # the package graph's declaration.
            owner = name.rsplit("::", 1)[0] if "::" in name else ""
            if owner:
                src.append(f"pub mod {owner} {{")
                src.append(decl)
                src.append("}")
            else:
                src.append(decl)
        elif bare.startswith(("pub use", "pub const", "pub static", "impl ")):
            # Re-exports, consts and trait impls are not compared on either
            # side, so dropping them here keeps the two directions symmetric.
            continue
        else:
            skipped.append(f"{name} (unrecognised signature: {sig[:60]})")

    types: dict[str, dict] = {}
    methods: dict[tuple[str, str], dict] = {}
    scan_rust("\n".join(src), "", types, methods, aliases, None, None, collisions)
    return types, methods, skipped


MOD_BLOCK = re.compile(r"^pub\s+mod\s+[\w:]+\s*\{")


def parse_spec_mod_blocks(lines: list[str], aliases: Aliases, types, methods,
                          collisions) -> int:
    """Fold in every fenced block that opens with `pub mod <path> {`.

    Layout A's `#### Types` block is not the whole declaration surface. The
    peel spec declares eight public error enums -- with their derives, their
    variants and their fields -- in real-Rust `pub mod file::find { .. }`
    blocks elsewhere in the document, and the layout-A parser never read them.

    That was not merely a coverage hole. The stub declares all eight; with none
    of them on the spec side, the stub->spec direction had exactly one spec
    type whose name ended in `Error` to offer, and the old single-candidate
    fallback paired all eight onto it and called the run green. Removing the
    fallback without this turns the same eight into eight bogus
    TYPE_UNDECLAREDs. The declarations were in the spec the whole time; the
    parser has to read where they are written rather than where it prefers.

    The opening line is the discriminator, and it is a strict one: a prose
    excerpt showing `pub fn` bodies or an `impl From<&str> for Rope` does not
    match, so the many illustrative blocks in these specs contribute nothing.
    """
    found = 0
    for block in all_fenced_blocks(lines):
        head = next((l.strip() for l in block.split("\n") if l.strip()), "")
        if not MOD_BLOCK.match(head):
            continue
        found += 1
        scan_rust(block, "", types, methods, aliases, None, None, collisions)
    return found


def parse_spec(lines: list[str], aliases: Aliases):
    """Try each known API Catalog layout; return (types, methods, layout, notes)."""
    collisions: list[str] = []
    types = parse_spec_types(lines, aliases)
    methods = parse_spec_methods(lines, aliases, collisions)
    if types or methods:
        extra = parse_spec_mod_blocks(lines, aliases, types, methods, collisions)
        layout = "A (#### Types / #### Method Signatures"
        layout += f" + {extra} pub-mod block(s))" if extra else ")"
        reanchor_owners(types, methods, collisions)
        return types, methods, layout, [], collisions

    types, methods = parse_spec_rust_blocks(lines, aliases, collisions)
    if types or methods:
        reanchor_owners(types, methods, collisions)
        return types, methods, "B (rust blocks under ### API Catalog)", [], collisions

    types, methods, skipped = parse_spec_table(lines, aliases, collisions)
    if types or methods:
        reanchor_owners(types, methods, collisions)
        return types, methods, "C (### API Catalog signature table)", skipped, collisions

    return {}, {}, "unrecognised", [], collisions


# ------------------------------------------------------------------ stub side

def parse_stub(root: Path, aliases: Aliases):
    """Walk the stub's .rs files, tracking directory nesting and inline `pub mod`.

    The directory path matters: `src/store_impl/file/find.rs` declares
    `find::Error` *and* `find::existing::Error`, and so does
    `src/packed/find.rs`. Keying both on the file stem alone collapses them to
    one key, and then a spec that carefully distinguishes `file::find::Error`
    from `packed::find::Error` gets whichever one the walk happened to reach
    first. A private routing module in the path (`store_impl`) only makes the
    stub key longer than the spec's, which suffix matching already handles.
    """
    types: dict[str, dict] = {}
    methods: dict[tuple[str, str], dict] = {}
    trait_impls: dict[str, set[str]] = {}
    reexports = Reexports()
    collisions: list[str] = []
    declared_traits: set[str] = set()
    src_root = root / "src" if (root / "src").is_dir() else root
    sources = [p for p in sorted(root.rglob("*.rs"))
               if "target" not in p.parts and "tests" not in p.parts]
    # A stub that is a single .rs file *is* the crate root, whatever it is
    # called. gix-config-parse ships `spec/surface_stub_v1.rs` with no
    # Cargo.toml, and the file-stem rule below filed its entire declaration
    # surface under a module named `surface_stub_v1` -- a module the spec has
    # no way to name, so every pairing had to survive a suffix match it should
    # never have needed. Treat it as `lib.rs`.
    roots = {sources[0]} if len(sources) == 1 else set()
    for path in sources:
        try:
            rel = path.relative_to(src_root)
        except ValueError:
            rel = Path(path.name)
        parts = list(rel.parts[:-1])
        if path.stem not in ("lib", "mod") and path not in roots:
            parts.append(path.stem)
        scan_rust(path.read_text(encoding="utf-8", errors="replace"),
                  "::".join(parts), types, methods, aliases, trait_impls,
                  reexports, collisions, declared_traits)
    reanchor_owners(types, methods, collisions)
    return types, methods, trait_impls, reexports, collisions, declared_traits


BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
LEADING_ATTR = re.compile(r"^#\[[^\]]*\]\s*")


def strip_leading_attrs(text: str) -> str:
    """Drop *every* leading `#[...]` so the item keyword is what remains.

    `LEADING_ATTR.sub` is anchored at `^`, so one call removes at most one
    attribute no matter what count it is given. `scan_rust` already loops for
    this reason; `parse_spec_table` did not, so a signature cell carrying two
    attributes -- `#[derive(Hash, ...)] #[repr(transparent)] pub struct
    FullNameRef(BStr);`, which is exactly how upstream writes it -- still began
    with `#[` after the strip, matched none of the item-keyword branches, and
    was reported UNPARSED_ROW. The row is perfectly well formed; the classifier
    could only see past one attribute. Looping here makes the two front-ends
    agree and lets a spec declare a derive list on a `#[repr]` type at all.
    """
    while True:
        stripped = LEADING_ATTR.sub("", text, count=1).lstrip()
        if stripped == text:
            return text
        text = stripped


def record_use(path_text: str, module: str, aliases: Aliases) -> None:
    """Register `use a::b::C;`, `use a::b::{C, D};`, `use a::b::C as D;`.

    Glob imports carry no name information and are skipped.
    """
    path_text = path_text.strip()
    m = re.match(r"^(.*?)::\{(.*)\}$", path_text, re.S)
    if m:
        prefix, inner = m.group(1).strip(), m.group(2)
        for part in split_top_level(inner):
            record_use(f"{prefix}::{part.strip()}", module, aliases)
        return
    if path_text.endswith("*") or not path_text:
        return
    m = re.match(r"^(.+?)\s+as\s+(\w+)$", path_text)
    if m:
        full, name = m.group(1).strip(), m.group(2)
    else:
        full, name = path_text, last_segment(path_text)
    if name == "self":
        # `use std::io::{self, Write}` imports the *module* `io`, not a type
        # called `self`. Registering the literal leaf would put a `self` entry
        # in the alias table, and `resolve` would then rewrite the `self::` of
        # every relative path it met into `std::io::self::` -- turning correct
        # crate-relative paths into garbage.
        full = full.rsplit("::", 1)[0]
        name = last_segment(full)
    if name in ("super", "crate"):
        return
    if re.fullmatch(r"[\w:]+", full) and name:
        aliases.add_import(module, name, full)


def strip_line_comments(text: str) -> str:
    """Remove `// ...` tails. A trailing comment on a signature line otherwise
    joins the next logical line and derails brace accounting."""
    return "\n".join(line.split("//")[0] for line in text.split("\n"))


def strip_block_comments(text: str) -> str:
    """Replace `/* ... */` with the ELIDED sentinel.

    Specs write `pub struct X(/* private */)` and
    `Result<LineRef<'a>, /* decode error */>`. Deleting the comment outright
    makes the second one read as `Result<LineRef>` -- a spec that declined to
    name its error type becomes indistinguishable from one that named a
    different type, and the differ reports METHOD_RETURN, sending someone to
    edit a stub that is not wrong. The sentinel survives into `strip_type` as
    `?`, which `is_unspecified` reports as SPEC_INCOMPLETE instead.
    """
    return BLOCK_COMMENT.sub(ELIDED, text)


MODULE_DIRECTIVE = "@@module "


def module_pattern(crate: str) -> re.Pattern | None:
    """`// gix_ref::file::log::iter::decode::Error   (fields private; ...)`.

    Anchored at the start so prose that merely mentions a path cannot move the
    parser's module, but tolerant of a trailing parenthetical -- the catalog
    annotates several of these comments and an exact-end match silently left
    those declarations in the previous module.
    """
    if not crate:
        return None
    # The path has to *end* where the comment's path ends. Without the
    # lookahead, the prose line
    #   // gix_pack::data::header::decode(..), not data::header.decode(..).
    # read as a module directive and moved the parser into
    # `data::header::decode`, where every subsequent `impl` in the block was
    # keyed -- fifty-five methods declared on a module that has no types.
    #
    # Rule characters are decoration, not content. config-parse separates its
    # module groups with
    #   // \u2500\u2500 gix_config::parse::format \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    # which names its module as plainly as the undecorated form does, and which
    # this pattern used to refuse -- leaving both of that spec's free `normalize`
    # functions in the crate root under one key, where the second overwrote the
    # first. A spec should not have to be un-prettified to be read, so any run
    # of non-word, non-space characters may precede the crate name.
    return re.compile(
        rf"^//\s*[^\w\s]*\s*{re.escape(crate)}((?:::\w+)+)(?=[\s]|$)")


def module_directives(src: str, crate: str) -> list[str]:
    """Turn `// gix_ref::file::log::iter` comments into module directives.

    Layout B writes one fenced Rust block per module and names the module in a
    leading `//` comment -- there is no `pub mod` wrapper to read it from.
    Without that context every `Error` in the catalog parses to the same key
    `Error`, twelve distinct stub error types all pair against whichever one
    landed first, and the differ silently stops being able to tell them apart.
    That is the dummy-gate shape again: it reports agreement it never checked.

    Only paths rooted at the crate under specification are read this way, so
    an ordinary prose comment cannot move the parser's module. A trailing
    segment in `UpperCamel` is a type name, not a module, and is dropped:
    `// gix_ref::packed::find::existing::Error` scopes to
    `packed::find::existing`.
    """
    if not crate:
        return src.split("\n")
    pattern = module_pattern(crate)
    out = []
    for line in src.split("\n"):
        m = pattern.match(line.strip())
        if not m:
            out.append(line)
            continue
        parts = [p for p in m.group(1).split("::") if p]
        if parts and parts[-1][:1].isupper():
            parts.pop()
        # `;` so `logical_lines` flushes it as a complete statement instead of
        # gluing it onto the declaration that follows.
        out.append(f"{MODULE_DIRECTIVE}{'::'.join(parts)};")
    return out


def scan_rust(src: str, file_mod: str, types, methods, aliases,
              trait_impls=None, reexports=None, notes=None, traits=None) -> None:
    """Single pass with uniform brace accounting.

    Every line's braces are counted exactly once, at the end. A construct that
    opens a block records a frame at the depth it opens; frames pop when depth
    falls back below them. Counting a method's own body brace is what keeps an
    `impl` frame alive across its methods -- getting that wrong silently
    detaches every method from its impl target.

    ``trait_impls`` (when given) collects ``{type_path: {Trait, ...}}`` from
    every ``impl Trait for Type`` block. A spec's declaration list is a list of
    *trait obligations*, not of derives: `Clone` can be derived, but
    `FusedIterator` and `ExactSizeIterator` cannot be derived at all and
    `Iterator` almost never is. Comparing that list against `#[derive(...)]`
    alone reported hand-written impls as missing. Kept in its own mapping
    rather than folded into ``types`` because an impl names types the crate
    does not declare -- `impl PartialEq<Rope> for str` would otherwise mint a
    phantom `str` type and report it TYPE_UNDECLARED.
    """
    mod_stack: list[str] = [file_mod] if file_mod else []
    impl_stack: list[str] = []
    frames: list[tuple[int, str, str]] = []  # (depth_opened_at, kind, payload)
    depth = 0
    pending_derives: set[str] = set()

    for raw in logical_lines(
            [strip_line_comments(line) for line in
             module_directives(strip_block_comments(src), aliases.crate)]):
        text = raw.strip()
        if not text:
            continue

        if text.startswith(MODULE_DIRECTIVE):
            # Only meaningful between top-level items; inside a block the
            # enclosing `mod`/`impl` frames own the stack.
            if not frames:
                mod_stack = [p for p in text[len(MODULE_DIRECTIVE):].rstrip(";").split("::") if p]
            continue

        # Attributes may sit on their own line or inline ahead of the item, as
        # `#[non_exhaustive] pub enum Error { ... }` does in a table cell.
        while text.startswith("#["):
            d = re.match(r"^#\[derive\(([^)]*)\)\]", text)
            if d:
                pending_derives |= {norm_trait(t) for t in split_top_level(d.group(1))
                                   if norm_trait(t)}
            stripped = LEADING_ATTR.sub("", text, count=1)
            if stripped == text:
                break
            text = stripped
        if not text or text.startswith("#["):
            continue

        module = "::".join(mod_stack)
        opens, closes = text.count("{"), text.count("}")
        opened: tuple[str, str] | None = None  # (kind, payload)

        m = re.match(r"^pub\s+mod\s+([\w:]+)", text)
        if m and opens:
            # `pub mod file::find {` -- specs wrap a module's declarations in
            # the path they live at rather than nesting three `mod` blocks. The
            # pattern used to be `(\w+)`, which matched `file` and left `find`
            # unread, so every type in such a block was keyed one module short
            # and paired against the wrong side or against nothing.
            #
            # Still `pub` only. A private `mod error { .. }` whose contents are
            # re-exported by the parent is reachable at the *parent's* path,
            # which is where the unpushed frame already keys them.
            opened = ("mod", m.group(1))

        if opened is None and opens:
            header = parse_decl_header(text)
            if header is not None:
                if header.blanket:
                    # `impl<T: Find + ?Sized> FindExt for T {` implements the
                    # trait for every `T`, so its target is a type parameter,
                    # not a type. Read as an ordinary impl it minted a type
                    # called `T` and hung the trait's provided methods off it.
                    opened = ("skip", "")
                else:
                    qualified = qualify_owner(header.owner, module)
                    opened = (header.kind, qualified)
                    if (trait_impls is not None and header.kind == "impl"
                            and header.trait_name):
                        # `impl core::iter::FusedIterator for Chunks<'_>`
                        # satisfies a spec that declares `FusedIterator`.
                        trait_impls.setdefault(qualified, set()).add(header.trait_name)

        if opened is None:
            m = re.match(r"^(?:pub(?:\s*\([^)]*\))?\s+)?use\s+(.+?);", text)
            if m:
                record_use(m.group(1), module, aliases)
                if reexports is not None and text.startswith("pub use"):
                    # A `pub use` is the one hard piece of evidence that a
                    # declaration is reachable under a second path -- which is
                    # how `file::mutable::section::SectionMut` and the spec's
                    # `file::SectionMut` are the same type. Pairing those two
                    # by guesswork is what the removed fallback did; pairing
                    # them because the crate says so is a fact.
                    record_reexport(m.group(1), module, reexports, aliases)

        if traits is not None:
            m = re.match(r"^pub\s+(?:unsafe\s+)?trait\s+(\w+)", text)
            if m:
                # A trait is public declaration surface -- a spec that lists
                # one among its types is not wrong -- but `types` here means
                # "thing with derives and fields", and a trait has neither.
                # Recorded separately so a spec-side trait can pair instead of
                # being reported TYPE_MISSING against a stub that declares it,
                # and so the run can say how much of the surface this is.
                traits.add(f"{module}::{m.group(1)}" if module else m.group(1))

        if opened is None:
            m = re.match(r"^(?:pub\s+)?(?:struct|enum)\s+(\w+)", text)
            if m:
                key = f"{module}::{m.group(1)}" if module else m.group(1)
                types.setdefault(key, {"derives": set(), "fields": {},
                                       "module": module})
                types[key]["derives"] |= pending_derives
                pending_derives = set()
                tup = re.match(
                    r"^(?:pub\s+)?struct\s+\w+\s*(?:<[^>]*>)?\s*\((.+)\)\s*;", text)
                if tup:
                    types[key]["fields"].update(tuple_fields(tup.group(1)))
                if opens:
                    opened = ("type:" + key, "")

        if opened is None:
            m = re.match(rf"^pub\s+type\s+(\w+)\s*=\s*({UNTIL_SEMI});", text)
            if m:
                aliases.add(module, m.group(1), m.group(2))

        if opened is None:
            in_trait = bool(frames) and frames[-1][1] == "trait"
            in_skip = any(k == "skip" for _, k, _ in frames)
            plain = strip_fn_generics(text)
            m = re.match(rf"^{FN_HEAD}\((.*?)\)\s*(?:->\s*({UNTIL_BODY}))?\s*[{{;]", plain)
            if (m and not in_skip and (impl_stack or plain.startswith("pub "))
                    and (in_trait or plain.startswith("pub "))):
                # A free `pub fn` has no impl target; its owner is the module it
                # sits in. Recording it under "" instead would make it invisible
                # to the spec side, which names it `module::fn`, and every free
                # function would report MISSING in one direction and UNDECLARED
                # in the other. The owner carries its module for the same
                # reason a type key does: a guppy stub has `impl Cycles` in
                # both `graph` and `graph::feature`, and an unqualified owner
                # makes those one key, so whichever is scanned second silently
                # replaces the first and its return type is compared against
                # the wrong method.
                name = FN_NAME.match(plain).group(1)
                owner = impl_stack[-1] if impl_stack else module
                # `-> T where B: Trait` -- the bound is not part of the type.
                ret = re.split(r"\bwhere\b", m.group(2) or "()")[0]
                key = (owner, name)
                entry = {
                    "arity": count_params(m.group(1)),
                    "params": param_types(m.group(1)),
                    "ret": strip_type(ret or "()"),
                    "module": module,
                }
                note_collision(methods, key, entry, notes)
                methods[key] = entry
                if opens:
                    opened = ("body", "")

        # A field line of the struct body we are currently inside.
        if opened is None and frames and frames[-1][1].startswith("type:"):
            f = FIELD_DECL.match(text)
            if f:
                types[frames[-1][1][5:]]["fields"][f.group(1)] = strip_type(f.group(2))

        if opened is not None:
            kind, payload = opened
            frames.append((depth, kind, payload))
            if kind == "mod":
                mod_stack.extend(p for p in payload.split("::") if p)
            elif kind in ("impl", "trait"):
                impl_stack.append(payload)

        depth += opens - closes
        while frames and depth <= frames[-1][0]:
            _, kind, payload = frames.pop()
            if kind == "mod":
                for _ in [p for p in payload.split("::") if p]:
                    if mod_stack:
                        mod_stack.pop()
            elif kind in ("impl", "trait") and impl_stack:
                impl_stack.pop()

        # A derive belongs to the item on the very next line, recorded or not.
        # `#[derive(Debug)] pub(crate) enum LineNumber` is not public surface,
        # so nothing consumes its derive; left pending, it lands on whichever
        # public type comes next and is reported DERIVE_EXTRA against a spec
        # that is perfectly correct. Lines that are nothing but attributes
        # `continue` above and never reach here, so the pending set survives a
        # stack of `#[...]` lines and dies with the item they annotate.
        pending_derives = set()


# -------------------------------------------------------------------- compare

def _identity_forms(key: str) -> set[str]:
    return {key}


class Pairing:
    """The outcome of trying to pair one declaration with the other side."""

    __slots__ = ("hit", "how", "near", "evidence")

    def __init__(self, hit=None, how="none", near=(), evidence=""):
        self.hit = hit            # the key paired with, or None
        self.how = how            # exact | path | reexport | ambiguous | none
        # Sorted, not insertion-ordered: `near` is built by walking a set of
        # candidate keys, so two runs of the same inputs printed the same
        # finding with its examples in different orders. A gate whose text
        # changes between identical runs cannot be diffed against its own
        # previous output, which is how anyone would notice a regression.
        self.near = sorted(near)  # same final segment, different path
        self.evidence = evidence  # the spelling that made a re-export pairing

    @property
    def assumed(self) -> bool:
        """True when the pairing rests on something other than the two written
        paths agreeing. Every one of these is named in the run's summary."""
        return self.hit is not None and self.how not in ("exact", "path")


def match_key(key: str, others, key_forms=None, other_forms=None) -> Pairing:
    """Pair a declaration path with its counterpart on the other side.

    Three rules, tried in order, and nothing beyond them:

    * the two paths are equal;
    * one is a `::`-boundary suffix of the other, closest first. A stub routes
      its modules privately (`store_impl::packed::Reference` for the spec's
      `packed::Reference`), so the extending direction is the normal case; the
      other happens when the stub writes a path relative to its own module.
      `file::loose::Reference` has three same-named candidates in a gix-ref
      stub and the loosest of them matches everything, so ranking by how much
      path the two share is what picks the intended one, and the `::` boundary
      is what stops `PartialName` matching `Name`;
    * a `pub use` in the stub makes one path an alias of the other.

    What is deliberately *not* a rule any more: "there is only one declaration
    left with this final segment, so it must be the one". That fallback paired
    the peel stub's eight distinct error enums onto the single `Error` the
    spec's `#### Types` block happened to declare, and paired pack-decode's
    `index::File` with the spec's `data::File`. Those types were then never
    compared against anything -- and a type that is never compared prints
    exactly like a type that matched. Two of the eight Rust tasks were green
    on that basis.

    When the name exists on the other side but at a path no rule reconciles,
    the candidates come back in ``near`` so the caller can say so out loud
    rather than guess. When two candidates are equally good, that is an
    ``ambiguous`` pairing, which is also reported and never resolved by
    picking one.
    """
    key_forms = key_forms or _identity_forms
    other_forms = other_forms or _identity_forms
    target = strip_type(key)
    tail = last_segment(target)
    mine = {strip_type(f) for f in key_forms(target)} | {target}

    best: dict[str, tuple] = {}
    near: list[str] = []
    for other in others:
        theirs = {strip_type(f) for f in other_forms(other)} | {strip_type(other)}
        ranked = None
        for a in mine:
            for b in theirs:
                if a == b:
                    rank = (0, 0, 0)
                elif b.endswith("::" + a):
                    rank = (1, b.count("::") - a.count("::"), len(b))
                elif a.endswith("::" + b):
                    rank = (2, a.count("::") - b.count("::"), len(b))
                else:
                    continue
                direct = (a == target and b == strip_type(other))
                cand = (rank, 0 if direct else 1, "" if direct else f"{a} = {b}")
                if ranked is None or cand < ranked:
                    ranked = cand
        if ranked is None:
            if any(last_segment(b) == tail for b in theirs):
                near.append(other)
        else:
            best[other] = ranked

    if not best:
        return Pairing(None, "none", near)
    order = sorted(best, key=lambda k: (best[k], k))
    winner = order[0]
    # Two candidates the rules rank identically are not resolved by taking the
    # alphabetically smaller one. `min()` used to do exactly that, and it is
    # the same silent-pairing failure as the fallback, one step further in.
    if len(order) > 1 and best[order[1]][0] == best[winner][0]:
        return Pairing(None, "ambiguous", order[:4])

    rank, indirect, evidence = best[winner]
    if indirect:
        how = "reexport"
    else:
        how = "exact" if rank[0] == 0 else "path"
    return Pairing(winner, how, near, evidence)



def crate_name(root: Path) -> str:
    """The crate the stub declares, from Cargo.toml, as a Rust path segment.

    `[lib] name` wins over `[package] name` because that is what `use` paths
    actually spell; hyphens become underscores for the same reason.
    """
    manifest = root / "Cargo.toml"
    if not manifest.is_file():
        return ""
    section, package, lib = "", "", ""
    for line in manifest.read_text(encoding="utf-8", errors="replace").split("\n"):
        s = line.split("#", 1)[0].strip()
        if s.startswith("["):
            section = s.strip("[]")
            continue
        m = re.match(r'^name\s*=\s*"([^"]+)"', s)
        if not m:
            continue
        if section == "package":
            package = m.group(1)
        elif section == "lib":
            lib = m.group(1)
    return (lib or package).replace("-", "_")


def crate_from_spec(lines: list[str]) -> str:
    """Last-resort crate name when the stub ships no Cargo.toml.

    The crate name is not cosmetic: it is what makes a `// gix_config::parse`
    comment readable as a module directive. Without it every such comment is
    inert, and a spec that carefully separates `parse::format::normalize` from
    `value::normalize` collapses both onto one key. Rather than let that fail
    silently, take the name the spec itself states -- and when it states none,
    say so in the summary instead of proceeding as if there were nothing to
    read.
    """
    for line in lines:
        m = re.search(r"crate named `([A-Za-z0-9_-]+)`", line)
        if m:
            return m.group(1).replace("-", "_")
    return ""


def qualify_owner(owner: str, module: str) -> str:
    """An impl target as a crate-root path.

    `impl Cycles` says nothing about which `Cycles`; the module it sits in
    does, and without that the two `Cycles` in a guppy stub are one key. But
    `impl crate::Bundle {` inside `mod bundle` already *is* crate-root
    absolute, and prefixing it produced the key `bundle::crate::Bundle`, which
    paired with nothing on either side -- six pack-decode methods reported
    MISSING and UNDECLARED simultaneously, which is the signature of a key
    the two directions disagree about rather than a real divergence.
    """
    owner = strip_type(owner)
    if owner.startswith("crate::"):
        return owner[len("crate::"):]
    if owner == "crate":
        return ""
    if module and owner != module and not owner.startswith(module + "::"):
        return f"{module}::{owner}" if owner else module
    return owner


def reanchor_owners(types: dict, methods: dict, notes=None) -> None:
    """Re-key `impl Tree` written in a child module onto the type's own path.

    Rust resolves an impl target by name lookup, not by the module the block
    sits in: `pub mod from_offsets { impl Tree { .. } }` inside `cache::delta`
    declares on `cache::delta::Tree`, and there is no such type as
    `cache::delta::from_offsets::Tree`. Keyed by the enclosing module, those
    methods were absent from the type the spec names and present under a path
    the spec has no reason to write -- reported MISSING and UNDECLARED at the
    same time, which is a key disagreement wearing the costume of a
    divergence, and the single most misleading output this tool produced.

    Only an ancestor module is considered, innermost first, which is the order
    Rust's own name resolution uses; a name that resolves nowhere is left
    exactly where it was written and reported as such.
    """
    for (owner, name), decl in list(methods.items()):
        if not owner or owner in types:
            continue
        parts = owner.split("::")
        tail = parts[-1]
        for i in range(len(parts) - 2, -1, -1):
            cand = "::".join(parts[:i] + [tail])
            if cand not in types:
                continue
            prev = methods.get((cand, name))
            if prev is not None and any(prev.get(f) != decl.get(f)
                                        for f in ("arity", "params", "ret")):
                # Moving it would destroy a different declaration that is
                # already there. Leave it where it was written: MISSING plus
                # UNDECLARED is loud, and silently overwriting is not.
                break
            methods[(cand, name)] = decl
            del methods[(owner, name)]
            break


def owner_path(target: str, decl: dict) -> str:
    """The owner as stored. Both parsers qualify when the frame opens."""
    return strip_type(target) or decl.get("module", "")


# Traits the compiler implements for you. They appear in no `#[derive(...)]`
# and in no `impl` block anywhere, because writing one is either impossible or
# `unsafe`. A spec that states `Send, Sync` in its obligation list is stating
# something true and load-bearing, and this differ cannot check it by
# inspection either way -- so it is reported as uncheckable, never as a pass
# and never as a missing derive.
AUTO_TRAITS = frozenset({"Send", "Sync", "Unpin", "Sized",
                         "UnwindSafe", "RefUnwindSafe"})


def impls_for(key: str, trait_impls: dict[str, set[str]]) -> set[str]:
    """Traits hand-implemented for the type at ``key``.

    A type and its impls are almost always in one module, but an impl may sit
    a module away, so paths are paired by the same `::`-boundary suffix rule
    the type keys use. Deliberately *not* `match_key`: its single-candidate
    fallback pairs names that share no suffix at all, and here a wrong pairing
    silently satisfies a trait obligation the stub never met, which is the one
    direction this check must never get wrong.
    """
    out = set(trait_impls.get(key, ()))
    for other, traits in trait_impls.items():
        if other != key and (other.endswith("::" + key)
                             or key.endswith("::" + other)):
            out |= traits
    return out


def extern_crates(root: Path) -> frozenset[str]:
    """Dependency crate names from Cargo.toml, plus the standard library.

    Used to decide whether a bare type name may resolve against a path: it may
    against the crate's own modules, never against another crate's.
    """
    names = {"std", "core", "alloc", "proc_macro"}
    manifest = root / "Cargo.toml"
    if manifest.is_file():
        section = ""
        for line in manifest.read_text(encoding="utf-8", errors="replace").split("\n"):
            s = line.split("#", 1)[0].strip()
            if s.startswith("["):
                section = s.strip("[]")
                continue
            if not section.endswith("dependencies"):
                continue
            m = re.match(r"^([A-Za-z0-9_-]+)\s*=", s)
            if m:
                names.add(m.group(1).replace("-", "_"))
    return frozenset(names)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().rsplit("Usage", 1)[-1])
        return 2
    spec_path, stub_root = Path(argv[1]), Path(argv[2])
    if not spec_path.is_file():
        print(f"DIFF_ERROR [tool {TOOL[:8]}] spec not found: {spec_path}")
        return 2
    if not stub_root.is_dir():
        print(f"DIFF_ERROR [tool {TOOL[:8]}] stub root not found: {stub_root}")
        return 2
    if not any(stub_root.rglob("*.rs")):
        print(f"DIFF_NOT_IMPLEMENTED [tool {TOOL[:8]}] no .rs sources under {stub_root}; "
              "only Rust stubs are parsed. Do not read this as a pass.")
        return 2

    aliases = Aliases()
    aliases.externs = extern_crates(stub_root)
    lines = spec_path.read_text(encoding="utf-8-sig", errors="replace").split("\n")
    aliases.crate = crate_name(stub_root)
    crate_source = "Cargo.toml"
    if not aliases.crate:
        aliases.crate = crate_from_spec(lines)
        crate_source = "the spec's own text" if aliases.crate else ""
    spec_types, spec_methods, layout, skipped, spec_dups = parse_spec(lines, aliases)
    (stub_types, stub_methods, stub_impls, reexports, stub_dups,
     stub_traits) = parse_stub(
        stub_root, aliases)
    # What the crate declares under its own name, either side having said so.
    aliases.local = frozenset(last_segment(k) for k in
                              list(stub_types) + list(spec_types))

    # An unparsed spec and a spec that declares nothing look identical from
    # here, and the difference is the whole value of the check: with zero spec
    # declarations every stub symbol is reported TYPE_UNDECLARED and the output
    # is a false-positive avalanche that reads like a real finding. Refuse.
    if not spec_types and not spec_methods:
        print(f"DIFF_ERROR [tool {TOOL[:8]}] could not parse any type or method declarations from "
              f"{spec_path}.\n"
              "  Known API Catalog layouts:\n"
              "    A  `#### Types` / `#### Method Signatures` pseudo-syntax blocks\n"
              "    B  fenced Rust blocks under `### API Catalog`\n"
              "    C  an `### API Catalog` table with a `Declared signature` column\n"
              "  That spec matches none of them, so there is nothing to compare\n"
              "  against. Add a front-end in parse_spec. Do not read this as a pass.")
        return 2
    # Same hazard, one half at a time.
    for what, spec_side, stub_side in (
            ("type", spec_types, stub_types),
            ("method", spec_methods, stub_methods)):
        if not spec_side and stub_side:
            print(f"DIFF_ERROR [tool {TOOL[:8]}] parsed 0 {what} declarations from {spec_path} but "
                  f"{len(stub_side)} from the stub (layout {layout}).\n"
                  f"  Every stub {what} would be reported undeclared. "
                  "Do not read this as a pass.")
            return 2
    # A row the synthesizer could not read is a hole in the comparison, not an
    # agreement; say so instead of quietly comparing fewer members.
    if skipped:
        print(f"DIFF_ERROR [tool {TOOL[:8]}] {len(skipped)} API Catalog row(s) could not be parsed "
              f"into a declaration (layout {layout}):")
        for note in skipped[:20]:
            print(f"  UNPARSED_ROW       {note}")
        if len(skipped) > 20:
            print(f"  ... and {len(skipped) - 20} more")
        print("  Fix parse_spec_table or the rows. Do not read this as a pass.")
        return 2

    divergences: list[str] = []
    unchecked_derives: list[str] = []
    unchecked_auto: list[str] = []
    # Every pairing that did not come from the two sides writing the same path.
    # Named in the summary on every run, pass or fail, so that a silent summary
    # means "every comparison was between two declarations that agree on their
    # own path" -- and means it truthfully.
    assumed: dict[str, int] = {}
    # Ownerless spec methods that found an ownerless stub declaration: both
    # sides wrote the same (empty) path, so these are exact, not guesses.
    ownerless_exact: set[str] = set()
    ambiguous: set[str] = set()

    def pair(key, others, key_forms=None, other_forms=None, what="type"):
        """Pair one declaration, recording how, so nothing is paired silently."""
        p = match_key(key, others, key_forms, other_forms)
        if p.how == "ambiguous":
            line = (f"AMBIGUOUS          {key}: {len(p.near)} stub {what}s pair "
                    f"equally well ({', '.join(p.near)}); refusing to guess")
            if line not in ambiguous:
                ambiguous.add(line)
                divergences.append(line)
        elif p.assumed:
            note = (f"{key} = {p.hit}"
                    + (f" [{p.how}: {p.evidence}]" if p.evidence else f" [{p.how}]"))
            assumed[note] = assumed.get(note, 0) + 1
        return p

    # --- direction 1: spec -> stub -------------------------------------
    paired: dict[str, str] = {}
    traits_matched: list[str] = []
    for key, decl in sorted(spec_types.items()):
        found = pair(key, stub_types, other_forms=reexports.public_paths)
        hit = found.hit
        if hit is None:
            if found.how == "ambiguous":
                continue
            # A trait is not a struct or an enum, so it is not in `stub_types`
            # -- but a spec is entitled to list one among its types, and
            # reporting the stub's own `pub trait Named` as absent is a false
            # red of exactly the kind that gets "fixed" by deleting the line
            # from the spec. Pair it, and say in the summary that a trait is
            # checked for existence only: its supertraits, associated types
            # and required methods are not compared here.
            as_trait = match_key(key, stub_traits)
            if as_trait.hit is not None:
                traits_matched.append((key, as_trait.hit))
                continue
            near = (f"; stub has {', '.join(found.near[:3])}"
                    if found.near else "")
            divergences.append(
                f"TYPE_MISSING       {key}: declared in spec, absent from stub{near}")
            continue
        paired[key] = hit
        # The indented list under a layout-A type declaration is a list of
        # *trait obligations*, not of derives. It freely mixes the derivable
        # (`Clone`, `Ord`) with the hand-written (`Display`, `Iterator`), the
        # underivable (`FusedIterator`, `ExactSizeIterator` -- there is no
        # derive macro for either) and the compiler-supplied (`Send`, `Sync`).
        # Checking that list against `#[derive(...)]` alone reported seventeen
        # correctly implemented traits as missing on one task. An obligation is
        # met by a derive OR by an `impl Trait for Type` block.
        spec_der = set(decl["derives"])
        stub_der = set(stub_types[hit]["derives"])
        hand_written = impls_for(hit, stub_impls)
        auto = spec_der & AUTO_TRAITS
        if auto:
            unchecked_auto.append(f"{key}: {', '.join(sorted(auto))}")
        # Satisfaction is the MISSING direction only. Folding impls into
        # `stub_der` would make every blanket `impl From<&Rope> for Chunks`
        # a DERIVE_EXTRA against a spec that is perfectly correct.
        missing = spec_der - stub_der - hand_written - AUTO_TRAITS
        # `thiserror::Error` is dropped from the EXTRA direction only. Specs
        # routinely grant it in prose once for a whole section instead of
        # repeating it on every error enum, so a stub that derives it is not
        # over-deriving. Dropping it from the satisfaction set as well -- which
        # is what a single filtered `stub_der` did -- reported ten error enums
        # as missing a derive both sides had written verbatim.
        # Written `#[derive(thiserror::Error)]` or `#[derive(Error)]`; both
        # normalise to `Error`, and there is no other derivable `Error`.
        extra = {d for d in stub_der if d not in ("Error", "thiserror::Error")} - spec_der
        if not spec_der:
            # The spec declares no derives at all for this type, so there is
            # nothing to be extra *to*. Guppy's catalog states its whole derive
            # contract in prose ("must support debug formatting, cloning,
            # copying, equality comparison and hashing") and writes no
            # `#[derive]` in the signature column: comparing anyway produced
            # 184 DERIVE_EXTRA lines, one per derive the stub legitimately
            # carries, which is noise dense enough to hide a real finding.
            # Suppressed, but counted and reported -- an unchecked dimension
            # that says nothing is the dummy-gate failure this tool exists to
            # avoid.
            unchecked_derives.append(key)
            extra = set()
        elif last_segment(key).endswith("Error"):
            # `std::error::Error: Debug + Display`, so an error type derives
            # Debug by necessity and specs state it once in prose for a whole
            # section rather than on each block. Reporting fifteen error enums
            # as over-deriving Debug buries the divergences that mean
            # something. Only this direction is suppressed: a spec that writes
            # `Debug` against a stub that omits it is still DERIVE_MISSING,
            # which is the guppy failure mode this check exists for.
            extra.discard("Debug")
        for d in sorted(missing):
            divergences.append(f"DERIVE_MISSING     {key}: spec declares `{d}`, stub neither derives nor implements it")
        for d in sorted(extra):
            divergences.append(f"DERIVE_EXTRA       {key}: stub derives `{d}`, spec does not declare it")
        for fname, ftype in sorted(decl["fields"].items()):
            stub_field = stub_types[hit]["fields"].get(fname)
            if stub_field is None:
                divergences.append(f"FIELD_MISSING      {key}.{fname}: declared in spec, absent from stub")
            elif is_unspecified(ftype):
                divergences.append(
                    f"SPEC_INCOMPLETE    {key}.{fname}: spec leaves the type unwritten "
                    f"(`{ftype}`); stub has `{stub_field}`")
            elif not types_match(ftype, stub_field, aliases,
                                 decl.get("module", ""),
                                 stub_types[hit].get("module", "")):
                divergences.append(
                    f"FIELD_TYPE         {key}.{fname}: spec `{ftype}` vs stub `{stub_field}`")

    for (target, name), decl in sorted(spec_methods.items()):
        # A spec that writes a free function with no owner (layout A's bare
        # `fn expand(..)` outside any `impl`) pairs on the name alone; anything
        # with an owner pairs on the *most specific* owner path that agrees.
        # `impl Cycles` appears twice in a guppy stub -- once in `graph`, once
        # in `graph::feature` -- and taking the first match compared the
        # feature graph's `all_cycles` against the package graph's, reporting a
        # return-type divergence between two methods that were never meant to
        # be the same one.
        cands = {owner_path(t, v): v for (t, n), v in stub_methods.items()
                 if n == name}
        if not target:
            if "" in cands:
                # The stub declares a crate-root free function of this name
                # too. Both sides wrote the same owner -- none -- so this is an
                # exact pairing, not a guess, and a *different* type happening
                # to have a method of the same name does not make it
                # ambiguous. Counting that type as a rival candidate made
                # `::at` unresolvable on gix-odb-dynstore-001 purely because
                # the crate also declares `loose::Store::at`; the free function
                # and the method are unrelated declarations.
                stub_owner, hit = "", cands[""]
                ownerless_exact.add(name)
            elif len(cands) > 1:
                divergences.append(
                    f"AMBIGUOUS          ::{name}: spec declares it with no owner and "
                    f"{len(cands)} stub types have a method of that name "
                    f"({', '.join(sorted(cands)[:4])}); refusing to guess")
                continue
            else:
                stub_owner = next(iter(cands), "")
                hit = cands.get(stub_owner)
                if hit is not None and stub_owner:
                    # Both sides ownerless is two crate-root free functions
                    # agreeing, not an assumption. One side ownerless is.
                    note = f"::{name} = {stub_owner}::{name} [name-only]"
                    assumed[note] = assumed.get(note, 0) + 1
        else:
            found = pair(target, set(cands), other_forms=reexports.public_paths,
                         what="owner for method `%s`" % name)
            if found.how == "ambiguous":
                continue
            stub_owner = found.hit or ""
            hit = cands.get(stub_owner)
        if hit is None:
            divergences.append(f"METHOD_MISSING     {target}::{name}: declared in spec, absent from stub")
            continue
        # `Self` is only concrete once you know the impl it sits in, and the
        # two sides name that impl independently.
        spec_self = base_path(strip_type(target))
        stub_self = base_path(strip_type(stub_owner))
        if hit["arity"] != decl["arity"]:
            divergences.append(
                f"METHOD_ARITY       {target}::{name}: spec {decl['arity']} params, stub {hit['arity']}")
        else:
            # Positions only line up when the counts do; comparing them across
            # an arity divergence reports the same defect once per parameter.
            for i, (sp, st) in enumerate(zip(decl.get("params", ()),
                                             hit.get("params", ()))):
                where = "receiver" if (sp in RECEIVERS or st in RECEIVERS) else i
                if sp in RECEIVERS or st in RECEIVERS:
                    if sp != st:
                        divergences.append(
                            f"METHOD_RECEIVER    {target}::{name}: spec `{sp}`, stub `{st}`")
                elif is_unspecified(sp):
                    divergences.append(
                        f"SPEC_INCOMPLETE    {target}::{name} param {where}: spec leaves "
                        f"the type unwritten (`{sp}`); stub has `{st}`")
                elif not types_match(sp, st, aliases,
                                     decl.get("module", ""), hit.get("module", ""),
                                     spec_self, stub_self):
                    divergences.append(
                        f"METHOD_PARAM       {target}::{name} param {where}: "
                        f"spec `{sp}` vs stub `{st}`")
        if is_unspecified(decl["ret"]):
            # The spec wrote a placeholder where a type belongs. That is a spec
            # defect, not a stub divergence, and calling it METHOD_RETURN would
            # send someone to edit the wrong file.
            divergences.append(
                f"SPEC_INCOMPLETE    {target}::{name}: spec leaves the return type "
                f"unwritten (`{decl['ret']}`); stub has `{hit['ret']}`")
        elif not types_match(decl["ret"], hit["ret"], aliases,
                             decl.get("module", ""), hit.get("module", ""),
                             spec_self, stub_self):
            divergences.append(
                f"METHOD_RETURN      {target}::{name}: spec `{decl['ret']}` vs stub `{hit['ret']}`")

    # --- direction 2: stub -> spec -------------------------------------
    # An over-declaring stub hides a spec gap exactly as well as an
    # under-declaring one breaks the build.
    claimed = set(paired.values())
    for key in sorted(stub_types):
        if key in claimed:
            continue
        found = pair(key, set(spec_types), key_forms=reexports.public_paths,
                     what="spec type")
        if found.hit is None and found.how != "ambiguous":
            near = f"; spec has {', '.join(found.near[:3])}" if found.near else ""
            divergences.append(
                f"TYPE_UNDECLARED    {key}: present in stub, no counterpart in spec{near}")

    # A spec method is claimed by the stub declaration it paired with, not by
    # any stub method that merely shares its final name. `last_segment` was
    # doing the latter, which is bug 3 seen from the other side: `data::File`
    # and `multi_index::File` both declare `version`, so each excused the
    # other's and neither was ever reported.
    spec_owned = {}
    for (t, n) in spec_methods:
        spec_owned.setdefault(n, set()).add(base_path(strip_type(t)))
    for (target, name) in sorted(stub_methods):
        owner = owner_path(target, stub_methods[(target, name)])
        owners = spec_owned.get(name)
        if owners is None:
            divergences.append(
                f"METHOD_UNDECLARED  {owner}::{name}: present in stub, no counterpart in spec")
            continue
        if "" in owners:
            # An ownerless spec free function pairs by name, and direction 1
            # has already compared it. Which stub declaration did it consume?
            # Only the ownerless one, if the stub has one. Skipping *every*
            # stub method of that name was a false green: on
            # gix-odb-dynstore-001 the spec's crate-root `at` would have
            # excused any `x::at` in the stub, declared or not. Fall through
            # on an owned stub method so it still has to find an owned spec
            # counterpart -- unless the spec declares none, which is the
            # name-only pairing direction 1 announced.
            rest = {o for o in owners if o}
            if not owner or not rest:
                continue
            owners = rest
        found = pair(owner, owners, key_forms=reexports.public_paths,
                     what="spec owner for method `%s`" % name)
        if found.hit is None and found.how != "ambiguous":
            near = f"; spec declares it on {', '.join(sorted(owners)[:3])}" if owners else ""
            divergences.append(
                f"METHOD_UNDECLARED  {owner}::{name}: present in stub, "
                f"no counterpart in spec{near}")

    # ---------------------------------------------------------------- report
    #
    # Printed on every run, pass or fail. A gate whose output does not state
    # its own extent invites the reader to assume the extent is total, and that
    # is exactly how 37/37 green coexisted with four unimplemented comparison
    # dimensions and eight silently unpaired types.
    # Two registries hold assumed pairings: `assumed`, filled where a pairing
    # is made, and `aliases.by_bare_name`, filled inside the alias resolver.
    # Counting only the first printed "0 pairing(s) rested on something other
    # than the two sides writing the same path" directly above an
    # ASSUMED_PAIRING line saying a spec type had been matched to
    # `gix_path::RelativePath` on its bare name alone. The count is the number
    # a reader checks; it has to cover everything the section lists.
    n_assumed = len(assumed) + len(aliases.by_bare_name)
    scope = [
        f"  SCOPE              tool {Path(__file__).name} md5 {TOOL}",
        f"  SCOPE              {len(spec_types)} spec / {len(stub_types)} stub types, "
        f"{len(spec_methods)} spec / {len(stub_methods)} stub methods (layout {layout})",
        f"  SCOPE              {n_assumed} pairing(s) rested on something other than "
        f"the two sides writing the same path",
    ]
    if assumed:
        for note, n in sorted(assumed.items()):
            times = f" (x{n})" if n > 1 else ""
            scope.append(f"  ASSUMED_PAIRING    {note}{times}")
    for note, n in sorted(aliases.by_bare_name.items()):
        times = f" (x{n})" if n > 1 else ""
        scope.append(f"  ASSUMED_PAIRING    {note} [bare name; the crate declares "
                     f"no type of that name]{times}")
    ownerless = sorted({n for (t, n) in spec_methods if not t})
    if ownerless:
        # Two very different situations wear the same spelling here, and
        # collapsing them let a report claim three name-only guesses while the
        # accounting line above said zero. An ownerless spec function that
        # found an ownerless stub function is an exact match; one that had to
        # reach onto a type is the guess, and is counted in ASSUMED_PAIRING.
        guessed = [n for n in ownerless if n not in ownerless_exact]
        scope.append(
            f"  SCOPE              {len(ownerless)} spec method(s) are declared with no "
            f"owner: {', '.join(ownerless[:8])}")
        if guessed:
            scope.append(
                f"  SCOPE              of those, {len(guessed)} found no crate-root function "
                f"in the stub and paired by name alone: {', '.join(guessed[:8])}")
    if not aliases.crate:
        scope.append(
            "  SCOPE              the stub declares no crate name (no Cargo.toml, and the "
            "spec states none), so\n"
            "                     `// crate::module` comments could not be read as module "
            "directives and every\n"
            "                     declaration under one was keyed without its module.")
    elif crate_source != "Cargo.toml":
        scope.append(
            f"  SCOPE              crate name `{aliases.crate}` came from {crate_source}, "
            f"not from a Cargo.toml")
    if traits_matched:
        shown = [k if k == hit else f"{k} = {hit}" for k, hit in sorted(traits_matched)]
        scope.append(
            f"  SCOPE              {len(traits_matched)} spec type(s) are traits, matched "
            f"by declaration only -- supertraits,\n"
            f"                     associated types and required methods are not compared: "
            f"{', '.join(shown[:6])}")
    loose_traits = sorted(stub_traits - {hit for _, hit in traits_matched})
    if loose_traits:
        scope.append(
            f"  SCOPE              {len(loose_traits)} stub trait(s) are outside the type "
            f"comparison entirely; a public trait\n"
            f"                     the spec never declares is not reported here: "
            f"{', '.join(loose_traits[:6])}"
            + (f", ... (+{len(loose_traits) - 6})" if len(loose_traits) > 6 else ""))
    variant_types = sorted(k for k, v in spec_types.items() if v.get("variants"))
    if variant_types:
        nvar = sum(len(spec_types[k]["variants"]) for k in variant_types)
        scope.append(
            f"  SCOPE              {nvar} enum variant(s) on {len(variant_types)} type(s) "
            f"were read as variants, not trait\n"
            f"                     obligations, and are not compared: "
            f"{', '.join(variant_types[:8])}"
            + (f", ... (+{len(variant_types) - 8})" if len(variant_types) > 8 else ""))
    for label, dups in (("spec", spec_dups), ("stub", stub_dups)):
        if dups:
            uniq = sorted(set(dups))
            scope.append(
                f"  KEY_COLLISION      {len(dups)} {label} declaration(s) overwrote an "
                f"earlier one under the same key: {', '.join(uniq[:8])}"
                + (f", ... (+{len(uniq) - 8})" if len(uniq) > 8 else ""))
    scope.append(
        "  UNCHECKED          lifetimes and lifetime order; generic parameters, their "
        "bounds and where-clauses;\n"
        "                     enum variants; consts and statics; `unsafe`/`async`/`const` "
        "on a signature;\n"
        "                     visibility finer than `pub`. Divergence in any of these is "
        "invisible here.")

    coverage = ""
    if unchecked_derives:
        shown = ", ".join(unchecked_derives[:6])
        if len(unchecked_derives) > 6:
            shown += f", ... (+{len(unchecked_derives) - 6})"
        coverage = (f"  COVERAGE           {len(unchecked_derives)} of {len(spec_types)} "
                    f"spec types declare no derives, so over-derivation was not\n"
                    f"                     checked for them: {shown}\n"
                    f"                     A missing derive is invisible to a standalone "
                    f"build and fatal at\n"
                    f"                     oracle-link time; put `#[derive(...)]` in the "
                    f"declaration to close this.")
    if unchecked_auto:
        shown = "; ".join(unchecked_auto[:4])
        if len(unchecked_auto) > 4:
            shown += f"; ... (+{len(unchecked_auto) - 4})"
        coverage += (("\n" if coverage else "")
                     + f"  COVERAGE           {len(unchecked_auto)} spec type(s) declare an auto "
                       f"trait, which no stub can derive or\n"
                       f"                     implement, so agreement was asserted rather "
                       f"than checked: {shown}\n"
                       f"                     Only a compile of the real oracle can settle "
                       f"these.")

    if divergences:
        print(f"DIFF_FAIL [tool {TOOL[:8]}]")
        for line in divergences:
            print("  " + line)
        if coverage:
            print(coverage)
        print("\n".join(scope))
        print(f"\n{len(divergences)} divergence(s) [tool {TOOL[:8]}]; "
              f"{len(spec_types)} spec types, {len(spec_methods)} spec methods "
              f"compared (spec layout {layout})")
        return 1

    print(f"DIFF_PASS [tool {TOOL[:8]}]")
    print(f"  {len(spec_types)} types and {len(spec_methods)} methods agree, "
          f"both directions (spec layout {layout})")
    if coverage:
        print(coverage)
    print("\n".join(scope))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
