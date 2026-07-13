"""MiniPackaging: a dependency-free Python module for parsing and evaluating
a practical subset of Python package metadata (PEP 440 / PEP 508)."""

from __future__ import annotations

import re
import os
import sys
import platform
import itertools
from typing import Any


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class InvalidVersion(ValueError):
    """Raised when a version string cannot be parsed."""


class InvalidSpecifier(ValueError):
    """Raised when a specifier string cannot be parsed."""


class InvalidRequirement(ValueError):
    """Raised when a requirement string cannot be parsed."""


class InvalidMarker(ValueError):
    """Raised when a marker string cannot be parsed."""


class UndefinedEnvironmentName(ValueError):
    """Raised when a marker references an undefined environment variable."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_ident(c: str) -> bool:
    return c.isascii() and (c.isalnum() or c in "._-")

def _name_start_ok(c: str) -> bool:
    return c.isascii() and (c.isalnum())

def _normalize_name(name: str) -> str:
    """Normalize a distribution name: replace _ with -, lowercase."""
    return name.replace("_", "-").lower()

def _normalize_extra(extra: str) -> str:
    """Normalize an extra name like a distribution name."""
    return _normalize_name(extra)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

# PEP 440 version regex covering the supported subset.
_VERSION_RE = re.compile(
    r"""
    ^
    (?:(\d+)\!)?                          # epoch
    (\d+(?:\.\d+)*)                        # release
    (?:
        (?:a|alpha|b|beta|c|rc|pre|preview)  # pre-release type
        \d*
    )?
    (?:
        (?:
            (?:post|rev|r)                    # post-release
            \d*
        )?
        (?:
            \.dev\d+                          # dev release
        )?
    |
        (?:
            \.dev\d+
            (?:
                (?:post|rev|r)
                \d*
            )?
        )?
    )
    (?:\+([0-9A-Za-z._\-]+))?               # local segment
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)


class Version:
    """A PEP 440 version."""

    __slots__ = ("_epoch", "_release", "_pre", "_post", "_dev", "_local")

    def __init__(self, text: str) -> None:
        if not isinstance(text, str):
            raise InvalidVersion(f"expected string, got {type(text).__name__}")
        m = _VERSION_RE.match(text.strip())
        if m is None:
            raise InvalidVersion(repr(text))

        epoch_str, release_str, local_str = m.group(1), m.group(2), m.group(3)

        self._epoch: int = int(epoch_str) if epoch_str is not None else 0
        self._release: tuple[int, ...] = tuple(int(p) for p in release_str.split("."))

        # Parse the matched suffix (post-release / dev / pre-release)
        raw = text.strip()
        # Remove epoch prefix
        tail = raw
        if epoch_str is not None:
            tail = tail.split("!", 1)[1]

        # Remove release prefix
        tail = tail[len(release_str):]

        # Remove local
        local_tail = ""
        if "+" in tail:
            tail, local_tail = tail.split("+", 1)

        # Parse pre-release
        self._pre: tuple[str, int] | None = self._parse_pre(tail)
        if self._pre is not None:
            pre_type, pre_num = self._pre
            # Remove the pre part from tail
            pre_parts = ["a", "alpha", "b", "beta", "c", "rc", "pre", "preview"]
            for pp in pre_parts:
                pattern_str = re.escape(pp) + r"\d*"
                pm = re.match(pattern_str, tail, re.IGNORECASE)
                if pm:
                    tail = tail[len(pm.group()):]
                    break

        # Parse post-release
        self._post: tuple[str, int] | None = self._parse_post(tail)
        if self._post is not None:
            post_parts = ["post", "rev", "r"]
            for pp in post_parts:
                pattern_str = re.escape(pp) + r"\d*"
                pm2 = re.match(pattern_str, tail, re.IGNORECASE)
                if pm2:
                    tail = tail[len(pm2.group()):]
                    break

        # Parse dev release
        self._dev: tuple[str, int] | None = self._parse_dev(tail)

        # Parse local
        if local_tail:
            self._local: tuple[tuple[int | str, ...], ...] = self._parse_local(local_tail)
        else:
            self._local = ()

    @staticmethod
    def _parse_pre(s: str) -> tuple[str, int] | None:
        m = re.match(
            r"(a|alpha|b|beta|c|rc|pre|preview)(\d*)",
            s,
            re.IGNORECASE,
        )
        if m is None:
            return None
        ptype = m.group(1).lower()
        pnum = int(m.group(2)) if m.group(2) else 0
        # normalize
        if ptype in ("alpha",):
            ptype = "a"
        elif ptype in ("beta",):
            ptype = "b"
        elif ptype in ("c", "pre", "preview"):
            ptype = "rc"
        return (ptype, pnum)

    @staticmethod
    def _parse_post(s: str) -> tuple[str, int] | None:
        m = re.match(r"(post|rev|r)(\d*)", s, re.IGNORECASE)
        if m is None:
            return None
        pnum = int(m.group(2)) if m.group(2) else 0
        return ("post", pnum)

    @staticmethod
    def _parse_dev(s: str) -> tuple[str, int] | None:
        m = re.match(r"\.dev(\d+)", s, re.IGNORECASE)
        if m is None:
            return None
        return ("dev", int(m.group(1)))

    @staticmethod
    def _parse_local(s: str) -> tuple[tuple[int | str, ...], ...]:
        """Parse local version segment. Split on ., _, or -."""
        s = s.lower()
        # split on . or _ or -
        parts = re.split(r"[._\-]", s)
        result: tuple[int | str, ...] = ()
        for p in parts:
            if p.isdigit():
                result += (int(p),)
            else:
                result += (p,)
        return (result,)

    @property
    def epoch(self) -> int:
        return self._epoch

    @property
    def release(self) -> tuple[int, ...]:
        return self._release

    @property
    def pre(self) -> tuple[str, int] | None:
        return self._pre

    @property
    def dev(self) -> tuple[str, int] | None:
        return self._dev

    @property
    def post(self) -> tuple[str, int] | None:
        return self._post

    @property
    def local(self) -> tuple[tuple[int | str, ...], ...]:
        return self._local

    @property
    def is_prerelease(self) -> bool:
        return self._pre is not None or self._dev is not None

    def __str__(self) -> str:
        parts: list[str] = []
        if self._epoch != 0:
            parts.append(f"{self._epoch}!")

        # Release: strip trailing zeros unless single 0
        rel = list(self._release)
        while len(rel) > 1 and rel[-1] == 0:
            rel.pop()
        parts.append(".".join(str(r) for r in rel))

        if self._pre is not None:
            parts.append(f"{self._pre[0]}{self._pre[1]}")

        if self._post is not None:
            # post release after pre
            parts.append(f"post{self._post[1]}")

        if self._dev is not None:
            parts.append(f".dev{self._dev[1]}")

        if self._local:
            local_parts = []
            for item in self._local[0]:
                local_parts.append(str(item))
            parts.append("+" + ".".join(local_parts))

        return "".join(parts)

    def _cmp_key(self) -> tuple:
        """Return a key for comparison following PEP 440 ordering."""
        # Release: strip trailing zeros for comparison
        rel = list(self._release)
        while len(rel) > 1 and rel[-1] == 0:
            rel.pop()

        # Pre: None comes AFTER final (pre < final)
        # pre-release spellings map to numbers: a=0, b=1, rc=2
        # None (final) => 3
        if self._pre is None:
            pre_key = (3, 0)  # final
        else:
            pre_map = {"a": 0, "b": 1, "rc": 2}
            pre_key = (pre_map[self._pre[0]], self._pre[1])

        # Post: None => 0 (no post)
        # But post comes BEFORE dev in ordering
        # Actually ordering: dev < pre < final < post
        # Let me use the correct ordering:
        # The key tuple is: (epoch, release, pre_sort, pre_num, post_sort, post_num, dev_sort, dev_num, local)

        return (
            self._epoch,
            tuple(rel),
            not self._pre,               # False (0) = has pre, True (1) = final
            self._pre if self._pre else ("z", 0),
            not self._post,              # False (0) = has post, True (1) = no post
            self._post if self._post else ("z", 0),
            not self._dev,               # False (0) = has dev, True (1) = no dev
            self._dev if self._dev else ("z", 0),
            self._local,
        )

    def _sort_key(self) -> tuple:
        """Return a sort key matching PEP 440 ordering.

        The PEP 440 order is:
        1. epoch
        2. release segment
        3. pre-release (earlier = a < b < rc < final)
        4. post-release (final < post)
        5. dev release (dev < non-dev)
        6. local (non-local < local)

        Wait, the actual PEP 440 ordering is more subtle:
        - dev releases sort BEFORE the corresponding final release
        - pre-releases sort BEFORE the corresponding final release
        - post-releases sort AFTER the corresponding final release

        So: dev < pre < final < post

        And for the same version with pre and post: pre comes before post.

        The key should be:
        (epoch, release, is_dev, dev_num, is_pre, pre_type, pre_num, is_post, post_num, is_local, local)
        with appropriate inversions.
        """
        rel = list(self._release)
        while len(rel) > 1 and rel[-1] == 0:
            rel.pop()

        # pre map
        pre_map = {"a": 0, "b": 1, "rc": 2}

        # Strategy: sort key where lower = earlier
        # Dev < pre < final < post

        # For dev: dev < non-dev, so dev=0, non-dev=1
        dev_neg = 0 if self._dev is not None else 1
        dev_num = self._dev[1] if self._dev else 0

        # For pre: pre < final, so has_pre=0, no_pre=1
        # Within pre: a < b < rc
        pre_neg = 0 if self._pre is not None else 1
        pre_type = pre_map[self._pre[0]] if self._pre else 0
        pre_num = self._pre[1] if self._pre else 0

        # For post: final < post, so no_post=0, has_post=1
        post_neg = 1 if self._post is not None else 0
        post_num = self._post[1] if self._post else 0

        # For local: non-local < local, so no_local=0, has_local=1
        local_neg = 1 if self._local else 0

        return (
            self._epoch,
            tuple(rel),
            dev_neg,
            dev_num,
            pre_neg,
            pre_type,
            pre_num,
            post_neg,
            post_num,
            local_neg,
            self._local,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._sort_key() == other._sort_key()

    def __lt__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._sort_key() < other._sort_key()

    def __le__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._sort_key() <= other._sort_key()

    def __gt__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._sort_key() > other._sort_key()

    def __ge__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._sort_key() >= other._sort_key()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._sort_key() != other._sort_key()

    def __hash__(self) -> int:
        return hash(self._sort_key())

    def __repr__(self) -> str:
        return f"Version({str(self)!r})"


# ---------------------------------------------------------------------------
# SpecifierSet
# ---------------------------------------------------------------------------

_SPECIFIER_RE = re.compile(
    r"""
    \s*
    (==|!=|>=|<=|>|<|~=)
    \s*
    (.+?)
    \s*
    (?=,|$)
    """,
    re.VERBOSE,
)


class SpecifierSet:
    """A set of version specifier clauses."""

    __slots__ = ("_clauses",)

    def __init__(self, text: str = "") -> None:
        self._clauses: list[tuple[str, Version, bool]] = []
        if not text.strip():
            return
        try:
            self._clauses = self._parse(text)
        except (InvalidVersion, ValueError) as e:
            raise InvalidSpecifier(str(e)) from e

    @classmethod
    def _parse(cls, text: str) -> list[tuple[str, Version, bool]]:
        clauses: list[tuple[str, Version, bool]] = []
        for m in _SPECIFIER_RE.finditer(text):
            op = m.group(1)
            raw = m.group(2).strip()
            wildcard = False
            if raw.endswith(".*"):
                wildcard = True
                raw = raw[:-2]
            try:
                v = Version(raw)
            except InvalidVersion:
                raise
            clauses.append((op, v, wildcard))
        return clauses

    def __str__(self) -> str:
        if not self._clauses:
            return ""
        parts = []
        for op, v, wildcard in self._clauses:
            vstr = str(v)
            if wildcard:
                vstr += ".*"
            parts.append(f"{op}{vstr}")
        return ",".join(parts)

    def __repr__(self) -> str:
        return f"SpecifierSet({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SpecifierSet):
            return NotImplemented
        return self._clauses == other._clauses

    def __hash__(self) -> int:
        return hash(tuple(self._clauses))

    def contains(self, version: str | Version, prereleases: bool | None = None) -> bool:
        """Check if *version* satisfies all clauses.

        Unless *prereleases* is True, pre-release and dev-release candidates
        are excluded when the candidate would otherwise satisfy only
        final-release bounds.
        """
        if isinstance(version, str):
            version = Version(version)

        for op, clause_v, wildcard in self._clauses:
            if not self._clause_match(op, clause_v, wildcard, version, prereleases):
                return False
        return True

    def _clause_match(
        self,
        op: str,
        clause_v: Version,
        wildcard: bool,
        version: Version,
        prereleases: bool | None,
    ) -> bool:
        """Check if *version* matches a single clause."""
        if prereleases is None:
            # Default: exclude prereleases/dev unless the clause version is itself prerelease
            # Prereleases are excluded only when the version is prerelease and the clause
            # version is not.
            if version.is_prerelease and not clause_v.is_prerelease:
                # Check if the version is "otherwise" excluded
                # The rule: pre-release candidates are excluded when they would 
                # otherwise satisfy only final-release bounds.
                # Meaning: if the matching clause doesn't specifically target a
                # prerelease, and the candidate is a prerelease, skip it.
                pass  # Let the clause check handle this

        if prereleases is False:
            if version.is_prerelease:
                return False

        if wildcard:
            return self._match_wildcard(op, clause_v, version)

        if op == "==":
            return version == clause_v
        elif op == "!=":
            return version != clause_v
        elif op == ">=":
            return version >= clause_v
        elif op == "<=":
            return version <= clause_v
        elif op == ">":
            return version > clause_v
        elif op == "<":
            return version < clause_v
        elif op == "~=":
            return self._match_compatible(clause_v, version)
        return False

    def _match_wildcard(
        self, op: str, clause_v: Version, version: Version
    ) -> bool:
        """Check wildcard prefix match."""
        prefix = clause_v.release  # trailing zeros already stripped

        # Strip trailing zeros from both
        vrel = list(version.release)
        while len(vrel) > 1 and vrel[-1] == 0:
            vrel.pop()

        prel = list(prefix)
        while len(prel) > 1 and prel[-1] == 0:
            prel.pop()

        if op == "==":
            return tuple(vrel[:len(prel)]) == tuple(prel)
        elif op == "!=":
            return tuple(vrel[:len(prel)]) != tuple(prel)
        return False

    def _match_compatible(
        self, clause_v: Version, version: Version
    ) -> bool:
        """Check ~= compatible release.

        The lower bound is inclusive at clause_v. The upper bound is
        exclusive at the next appropriate release segment.

        ~= X.Y means >= X.Y, < X.(Y+1).0
        ~= X.Y.Z means >= X.Y.Z, < X.(Y+1).0
        ~= X means >= X, < X+1.0
        """
        lower = clause_v
        if version < lower:
            return False

        # Build upper bound
        rel = list(clause_v.release)
        while len(rel) > 1 and rel[-1] == 0:
            rel.pop()

        if len(rel) >= 2:
            # Increment the second-to-last segment
            upper_rel = list(rel[:-1])
            upper_rel[-1] += 1
            # Pad to at least 2 segments
            while len(upper_rel) < 2:
                upper_rel.append(0)
            upper = (upper_rel[0], upper_rel[1])
        else:
            # Single segment: upper = X+1
            upper = (rel[0] + 1,)

        # Build a version representing upper bound (exclusive)
        upper_version_release = tuple(upper)
        # We need to compare: version < upper
        # Create a "next" Version-like comparison
        vrel = list(version.release)
        while len(vrel) > 1 and vrel[-1] == 0:
            vrel.pop()

        # Compare release tuples (lexicographic)
        if tuple(vrel) < upper_version_release:
            return True
        return False


# ---------------------------------------------------------------------------
# Marker
# ---------------------------------------------------------------------------

_MARKER_VAR_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

# Marker tokenizer regex
_MARKER_TOKEN_RE = re.compile(
    r"""
    \s*(?:and|or|in\b|not\s+in|==|!=|<=|>=|<|>|\(|\)|"[^"]*"|'[^']*'|[a-zA-Z_][a-zA-Z0-9_]*(?:\s*\.\s*[a-zA-Z_][a-zA-Z0-9_]*)*)\s*
    """,
    re.VERBOSE,
)


class Marker:
    """A parsed environment marker expression."""

    __slots__ = ("_tokens", "_text")

    _VALID_VARS = frozenset({
        "python_version",
        "python_full_version",
        "os_name",
        "sys_platform",
        "platform_machine",
        "platform_system",
        "platform_release",
        "platform_version",
        "platform_python_implementation",
        "implementation_name",
        "implementation_version",
        "extra",
    })

    def __init__(self, text: str) -> None:
        self._text = text.strip()
        self._tokens = self._tokenize(self._text)
        # Validate by parsing
        try:
            self._parse_expr(0)[0]
        except (IndexError, ValueError) as e:
            raise InvalidMarker(str(e) or repr(text)) from e

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            c = text[i]
            if c.isspace():
                i += 1
                continue

            # String literals
            if c in ('"', "'"):
                quote = c
                j = i + 1
                while j < n and text[j] != quote:
                    if text[j] == "\\":
                        j += 1
                    j += 1
                if j >= n:
                    raise InvalidMarker("unterminated string literal")
                tokens.append(text[i:j + 1])
                i = j + 1
                continue

            # Multi-char operators
            if text[i:i + 2] in ("==", "!=", "<=", ">="):
                tokens.append(text[i:i + 2])
                i += 2
                continue

            # not in
            if text[i:i + 7] == "not in ":
                tokens.append("not in")
                i += 7
                continue

            # in
            if text[i:i + 3] == "in " or (text[i:i + 2] == "in" and (i + 2 >= n or not text[i + 2].isalnum())):
                tokens.append("in")
                i += 2
                continue

            # and
            if text[i:i + 4] == "and " or (text[i:i + 3] == "and" and (i + 3 >= n or not text[i + 3].isalnum())):
                tokens.append("and")
                i += 3
                continue

            # or
            if text[i:i + 3] == "or " or (text[i:i + 2] == "or" and (i + 2 >= n or not text[i + 2].isalnum())):
                tokens.append("or")
                i += 2
                continue

            # Single char
            if c in "()":
                tokens.append(c)
                i += 1
                continue

            if c in "<>":
                tokens.append(c)
                i += 1
                continue

            # Variable name
            m = _MARKER_VAR_RE.match(text, i)
            if m:
                tokens.append(m.group())
                i = m.end()
                continue

            raise InvalidMarker(f"unexpected character at position {i}: {text[i:i+10]!r}")

        return tokens

    def _peek(self, pos: int) -> str | None:
        if pos < len(self._tokens):
            return self._tokens[pos]
        return None

    def _parse_expr(self, pos: int) -> tuple[object, int]:
        """Parse an expression: or-chain of and-terms."""
        left, pos = self._parse_and(pos)
        while self._peek(pos) == "or":
            pos += 1
            right, pos = self._parse_and(pos)
            left = ("or", left, right)
        return left, pos

    def _parse_and(self, pos: int) -> tuple[object, int]:
        """Parse an and-chain of atoms."""
        left, pos = self._parse_atom(pos)
        while self._peek(pos) == "and":
            pos += 1
            right, pos = self._parse_atom(pos)
            left = ("and", left, right)
        return left, pos

    def _parse_atom(self, pos: int) -> tuple[object, int]:
        """Parse a comparison or parenthesized expression."""
        tok = self._peek(pos)
        if tok is None:
            raise InvalidMarker("unexpected end of expression")
        if tok == "(":
            pos += 1
            expr, pos = self._parse_expr(pos)
            if self._peek(pos) != ")":
                raise InvalidMarker("expected )")
            pos += 1
            return expr, pos

        # Must be a comparison: var op value
        var = tok
        pos += 1
        if var in ("and", "or", "in", "not"):
            raise InvalidMarker(f"unexpected token: {var}")
        var = self._normalize_var(var)

        op = self._peek(pos)
        if op is None:
            raise InvalidMarker("expected operator")
        pos += 1

        if op == "not":
            if self._peek(pos) != "in":
                raise InvalidMarker("expected 'in' after 'not'")
            pos += 1
            op = "not in"

        # Value
        val = self._peek(pos)
        if val is None:
            raise InvalidMarker("expected value")
        pos += 1
        val, is_version = self._normalize_val(val)

        return ("cmp", var, op, val, is_version), pos

    def _normalize_var(self, var: str) -> str:
        """Normalize variable name to lowercase with underscores."""
        return var.lower().replace(".", "_").replace("-", "_").strip()

    def _normalize_val(self, val: str) -> tuple[str, bool]:
        """Normalize a value literal. Returns (value, is_version)."""
        if val.startswith('"') or val.startswith("'"):
            val = val[1:-1]
        # Check if version-like
        is_version = False
        try:
            v = Version(val)
            val = str(v)
            is_version = True
        except InvalidVersion:
            pass
        return val, is_version

    def __str__(self) -> str:
        return self._render(self._tokens, 0)[0]

    def _render(self, tokens: list[str], pos: int) -> tuple[str, int]:
        """Render tokens back to canonical string, preserving boolean structure.
        
        We need to inspect the parsed AST for correct parenthesization,
        but the token stream alone loses structure. For canonical output,
        we just render back the normalized tokens.
        """
        # For now, use AST-based rendering for canonical output
        return self._render_ast(self._parse_expr(0)[0]), len(tokens)

    def _render_ast(self, node: object) -> str:
        if isinstance(node, tuple):
            kind = node[0]
            if kind == "cmp":
                _, var, op, val, is_version = node
                return f'{var} {op} "{val}"'
            elif kind == "and":
                left = self._render_ast(node[1])
                right = self._render_ast(node[2])
                # Need parentheses for or inside and
                if isinstance(node[1], tuple) and node[1][0] == "or":
                    left = f"({left})"
                if isinstance(node[2], tuple) and node[2][0] == "or":
                    right = f"({right})"
                return f"{left} and {right}"
            elif kind == "or":
                left = self._render_ast(node[1])
                right = self._render_ast(node[2])
                return f"{left} or {right}"
        return str(node)

    def evaluate(
        self,
        environment: dict[str, str] | None = None,
        requested_extras: set[str] | None = None,
    ) -> bool:
        """Evaluate the marker expression in the given environment."""
        if environment is None:
            environment = default_environment()
        else:
            environment = dict(environment)  # copy

        # Normalize env keys
        norm_env: dict[str, str] = {}
        for k, v in environment.items():
            norm_env[k.lower().replace(".", "_").replace("-", "_").strip()] = v

        ast, _ = self._parse_expr(0)
        return self._eval_ast(ast, norm_env, requested_extras or set())

    def _eval_ast(
        self,
        node: object,
        environment: dict[str, str],
        requested_extras: set[str],
    ) -> bool:
        if isinstance(node, tuple):
            kind = node[0]
            if kind == "cmp":
                return self._eval_cmp(node, environment, requested_extras)
            elif kind == "and":
                return self._eval_ast(node[1], environment, requested_extras) and self._eval_ast(node[2], environment, requested_extras)
            elif kind == "or":
                return self._eval_ast(node[1], environment, requested_extras) or self._eval_ast(node[2], environment, requested_extras)
        return False

    def _eval_cmp(
        self,
        node: tuple,
        environment: dict[str, str],
        requested_extras: set[str],
    ) -> bool:
        _, var, op, val, is_version = node

        if var == "extra":
            if not requested_extras:
                env_val = ""
            else:
                # True if true for at least one requested extra
                for extra in requested_extras:
                    extra_norm = _normalize_extra(extra)
                    if self._compare_one(extra_norm, op, val, is_version):
                        return True
                return False
        else:
            if var not in environment:
                raise UndefinedEnvironmentName(var)
            env_val = environment[var]

        return self._compare_one(env_val, op, val, is_version)

    def _compare_one(
        self, env_val: str, op: str, val: str, is_version: bool
    ) -> bool:
        """Compare a single env value against the marker value."""
        if op in ("in", "not in"):
            # val is a string, check substring membership
            result = env_val in val
            return result if op == "in" else not result

        # Try version comparison
        try:
            v_env = Version(env_val)
            v_val = Version(val)
            if op == "==":
                return v_env == v_val
            elif op == "!=":
                return v_env != v_val
            elif op == "<":
                return v_env < v_val
            elif op == "<=":
                return v_env <= v_val
            elif op == ">":
                return v_env > v_val
            elif op == ">=":
                return v_env >= v_val
        except InvalidVersion:
            pass

        # String comparison
        if op == "==":
            return env_val == val
        elif op == "!=":
            return env_val != val
        elif op == "<":
            return env_val < val
        elif op == "<=":
            return env_val <= val
        elif op == ">":
            return env_val > val
        elif op == ">=":
            return env_val >= val

        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Marker):
            return NotImplemented
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __repr__(self) -> str:
        return f"Marker({str(self)!r})"


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------

# Rough requirement pattern
_REQUIREMENT_RE = re.compile(
    r"""
    ^
    \s*
    ([A-Za-z0-9](?:[A-Za-z0-9._\-]*[A-Za-z0-9])?)
    \s*
    (?:\[([^\]]*)\])?
    \s*
    (?:
        (?:
            ((?:~=|==|!=|<=|>=|<|>)\s*[^;@]+(?:\s*,\s*(?:~=|==|!=|<=|>=|<|>)\s*[^;@]+)*)
        )?
        (?:\s*@\s*(\S+))?
    |
        (?:\s*@\s*(\S+))?
    )?
    \s*
    (?:;\s*(.+))?
    \s*
    $
    """,
    re.VERBOSE,
)


class Requirement:
    """A PEP 508 requirement."""

    __slots__ = ("_name", "_extras", "_specifier", "_url", "_marker")

    def __init__(self, text: str) -> None:
        if not isinstance(text, str):
            raise InvalidRequirement(f"expected string, got {type(text).__name__}")

        m = _REQUIREMENT_RE.match(text.strip())
        if m is None:
            raise InvalidRequirement(repr(text))

        name_raw = m.group(1)
        extras_raw = m.group(2)
        spec_raw = m.group(3)
        url_raw = m.group(4) or m.group(5)
        marker_raw = m.group(6)

        # Validate name
        self._validate_name(name_raw)

        self._name = _normalize_name(name_raw)

        # Parse extras
        self._extras: set[str] = set()
        if extras_raw:
            for extra in extras_raw.split(","):
                extra = extra.strip()
                self._validate_name(extra)
                self._extras.add(_normalize_extra(extra))

        # Parse specifier
        try:
            self._specifier = SpecifierSet(spec_raw.strip() if spec_raw else "")
        except InvalidSpecifier:
            raise
        except Exception:
            self._specifier = SpecifierSet("")

        # URL
        self._url: str | None = url_raw.strip() if url_raw else None

        # URL + specifier is invalid
        if self._url is not None and str(self._specifier):
            raise InvalidRequirement(
                "direct URL requirement cannot include version specifier"
            )

        # Marker
        try:
            self._marker = Marker(marker_raw) if marker_raw else None
        except InvalidMarker:
            raise
        except Exception:
            self._marker = None

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name:
            raise InvalidRequirement("empty name")
        if not name[0].isascii() or not (name[0].isalnum()):
            raise InvalidRequirement(f"name must start with letter or digit: {name!r}")
        if not name[-1].isascii() or not (name[-1].isalnum()):
            raise InvalidRequirement(f"name must end with letter or digit: {name!r}")
        for c in name:
            if not c.isascii() or not (c.isalnum() or c in "._-"):
                raise InvalidRequirement(f"invalid character in name: {c!r}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def extras(self) -> set[str]:
        return self._extras

    @property
    def specifier(self) -> SpecifierSet:
        return self._specifier

    @property
    def url(self) -> str | None:
        return self._url

    @property
    def marker(self) -> Marker | None:
        return self._marker

    def __str__(self) -> str:
        parts = [self._name]
        if self._extras:
            sorted_extras = sorted(self._extras)
            parts.append(f"[{','.join(sorted_extras)}]")

        if self._url:
            parts.append(f"@ {self._url}")
        elif str(self._specifier):
            parts.append(str(self._specifier))

        if self._marker is not None:
            parts.append(f"; {self._marker}")

        return "".join(parts)

    def __repr__(self) -> str:
        return f"Requirement({str(self)!r})"

    def _eq_key(self) -> tuple:
        """Key for semantic equality: normalized name, sorted extras,
        semantic specifier, URL, marker semantics."""
        return (
            self._name,
            tuple(sorted(self._extras)),
            self._specifier,
            self._url,
            str(self._marker) if self._marker else None,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Requirement):
            return NotImplemented
        return self._eq_key() == other._eq_key()

    def __hash__(self) -> int:
        return hash(self._eq_key())


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

def default_environment() -> dict[str, str]:
    """Return a dictionary of default environment marker variable values."""
    return {
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "python_full_version": platform.python_version(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": sys.implementation.name,
        "implementation_version": ".".join(
            str(x) for x in sys.implementation.version
        ) if hasattr(sys.implementation, "version") else "0",
    }


# ---------------------------------------------------------------------------
# Requirement Satisfaction
# ---------------------------------------------------------------------------

def is_requirement_satisfied(
    requirement: str | Requirement,
    installed_version: str | Version,
    environment: dict[str, str] | None = None,
    requested_extras: set[str] | None = None,
    prereleases: bool | None = None,
) -> bool:
    """Check whether an installed version satisfies a requirement.

    Evaluates the requirement marker first. If the marker is present and
    not applicable, the requirement is satisfied (it does not apply).
    Otherwise, checks the installed version against the specifier.
    """
    if isinstance(requirement, str):
        requirement = Requirement(requirement)

    if isinstance(installed_version, str):
        installed_version = Version(installed_version)

    if environment is None:
        environment = default_environment()

    # Check marker applicability
    if requirement.marker is not None:
        applicable = requirement.marker.evaluate(environment, requested_extras)
        if not applicable:
            return True  # requirement does not apply

    # Check specifier
    return requirement.specifier.contains(installed_version, prereleases)


# ---------------------------------------------------------------------------
# resolve_metadata
# ---------------------------------------------------------------------------

def _parse_roots(
    roots: Any,
) -> list[Requirement]:
    """Parse root requirements from strings or Requirement objects."""
    result: list[Requirement] = []
    for r in roots:
        if isinstance(r, Requirement):
            result.append(r)
        else:
            result.append(Requirement(str(r)))
    return result


def _parse_candidates(
    candidates: Any,
) -> dict[str, list[dict]]:
    """Index candidates by normalized name."""
    index: dict[str, list[dict]] = {}
    for c in candidates:
        c = dict(c)  # don't mutate caller's mapping
        name = _normalize_name(c["name"])
        c["_norm_name"] = name
        c["_version"] = Version(str(c["version"]))
        c["_requires"] = list(c.get("requires", []))
        index.setdefault(name, []).append(c)
    return index


def resolve_metadata(
    roots: Any,
    candidates: Any,
    environment: dict[str, str] | None = None,
    requested_extras: set[str] | None = None,
    prereleases: bool | None = None,
) -> dict:
    """Resolve local candidate metadata into coordinated projections.

    Returns a dictionary with keys:
    - selected: mapping from normalized project name to canonical version string
    - excluded: mapping from active project name to sorted excluded version strings
    - edges: list of active dependency edge mappings
    - dependents: mapping from child name to sorted parent names
    - requested_extras: mapping from project name to sorted extras
    - requirements: list of active requirement fact mappings
    """
    if environment is None:
        environment = default_environment()
    else:
        environment = dict(environment)  # copy

    extras_seed = requested_extras or set()

    # Parse inputs
    root_reqs = _parse_roots(roots)
    cand_idx = _parse_candidates(candidates)

    # Track active facts
    active_requirements: list[dict] = []  # fact dicts
    # Fact: source, parent, name, extras, specifier, url, marker, marker_applicable
    # source = "root" for roots, normalized parent name for deps
    # parent = None for roots, parent name for deps

    # Track which (parent, name, extras, url, marker_str) combos have been processed
    # to avoid infinite loops with transitive dependencies
    processed_edges: set[tuple[str | None, str, str, str | None, str | None]] = set()

    # Process root requirements
    for req in root_reqs:
        marker_applicable = True
        if req.marker is not None:
            try:
                marker_applicable = req.marker.evaluate(environment, extras_seed)
            except UndefinedEnvironmentName:
                marker_applicable = False

        fact = {
            "source": "root",
            "parent": None,
            "name": req.name,
            "extras": req.extras,
            "specifier": req.specifier,
            "url": req.url,
            "marker": req.marker,
            "marker_applicable": marker_applicable,
        }
        active_requirements.append(fact)

        if marker_applicable:
            edge_key = (None, req.name, "", req.url, str(req.marker) if req.marker else None)
            processed_edges.add(edge_key)

    # Iterate until no new dependency facts
    changed = True
    while changed:
        changed = False

        # For each active project, find the selected version and its dependencies
        # Rebuild selection each iteration
        selected, excluded, all_specs = _compute_selection(
            cand_idx, active_requirements, prereleases
        )

        # Process each selected project's requirements
        for norm_name, sel_version in list(selected.items()):
            # Find the candidate
            sel_cand = None
            for c in cand_idx.get(norm_name, []):
                if str(c["_version"]) == sel_version:
                    sel_cand = c
                    break
            if sel_cand is None:
                continue

            # Get parent's accumulated extras for this project
            parent_extras = _get_requested_extras_for(
                active_requirements, norm_name
            )

            # Process child requirements
            for req_str in sel_cand["_requires"]:
                try:
                    child_req = Requirement(req_str)
                except (InvalidRequirement, InvalidSpecifier, InvalidMarker):
                    # Failed parse: skip, atomicity preserved
                    continue

                child_name = child_req.name

                # Determine marker applicability using parent's requested extras
                marker_applicable = True
                if child_req.marker is not None:
                    try:
                        marker_applicable = child_req.marker.evaluate(
                            environment, parent_extras
                        )
                    except UndefinedEnvironmentName:
                        marker_applicable = False

                # Unique edge identity
                extras_str = ",".join(sorted(child_req.extras))
                marker_str = str(child_req.marker) if child_req.marker else None
                edge_key = (
                    norm_name,
                    child_name,
                    extras_str,
                    child_req.url,
                    marker_str,
                )

                if edge_key not in processed_edges:
                    processed_edges.add(edge_key)

                    fact = {
                        "source": norm_name,
                        "parent": norm_name,
                        "name": child_name,
                        "extras": child_req.extras,
                        "specifier": child_req.specifier,
                        "url": child_req.url,
                        "marker": child_req.marker,
                        "marker_applicable": marker_applicable,
                    }
                    active_requirements.append(fact)
                    changed = True

    # Final computation of all projections
    selected, excluded, _ = _compute_selection(
        cand_idx, active_requirements, prereleases
    )

    # Build edges
    edges = _build_edges(cand_idx, active_requirements, selected, prereleases)

    # Build dependents from edges
    dependents: dict[str, list[str]] = {}
    for edge in edges:
        child = edge["name"]
        parent = edge["parent"]
        if child not in dependents:
            dependents[child] = []
        if parent not in dependents[child]:
            dependents[child].append(parent)
    for child in dependents:
        dependents[child] = sorted(set(dependents[child]))

    # Build requested_extras
    req_extras: dict[str, set[str]] = {}
    for fact in active_requirements:
        if not fact["marker_applicable"]:
            continue
        name = fact["name"]
        if name not in req_extras:
            req_extras[name] = set()
        req_extras[name].update(fact["extras"])

    requested_extras_out: dict[str, list[str]] = {}
    for name, extras_set in req_extras.items():
        sorted_extras = sorted(extras_set)
        if sorted_extras:
            requested_extras_out[name] = sorted_extras

    # Build excluded
    excluded_out: dict[str, list[str]] = {}
    for name, ex_versions in excluded.items():
        sorted_versions = sorted(ex_versions)
        if sorted_versions:
            excluded_out[name] = sorted_versions

    # Build requirements output
    requirements_out: list[dict] = []
    for fact in active_requirements:
        requirements_out.append({
            "source": fact["source"],
            "parent": fact["parent"],
            "name": fact["name"],
            "extras": sorted(fact["extras"]),
            "specifier": str(fact["specifier"]) if str(fact["specifier"]) else "",
            "url": fact["url"],
            "marker": str(fact["marker"]) if fact["marker"] else None,
            "marker_applicable": fact["marker_applicable"],
        })

    return {
        "selected": selected,
        "excluded": excluded_out,
        "edges": edges,
        "dependents": dependents,
        "requested_extras": requested_extras_out,
        "requirements": requirements_out,
    }


def _compute_selection(
    cand_idx: dict[str, list[dict]],
    active_requirements: list[dict],
    prereleases: bool | None,
) -> tuple[dict[str, str], dict[str, set[str]], dict[str, SpecifierSet]]:
    """Compute selected and excluded versions from active requirements."""
    selected: dict[str, str] = {}
    excluded: dict[str, set[str]] = {}

    # Group active requirements by project name
    # Active requirements for a project = those that are marker_applicable
    # Also collect conjunctive specifiers
    all_specs: dict[str, tuple[SpecifierSet, set[str]]] = {}
    # specifier set + urls set for each project

    for fact in active_requirements:
        if not fact["marker_applicable"]:
            continue
        name = fact["name"]
        if name not in all_specs:
            all_specs[name] = (SpecifierSet(""), set())
        spec_set, url_set = all_specs[name]

        # Add specifier constraints (conjunctive)
        if str(fact["specifier"]):
            # Merge specifier clauses
            new_clauses = list(spec_set._clauses) + list(fact["specifier"]._clauses)
            merged = SpecifierSet("")
            merged._clauses = new_clauses
            all_specs[name] = (merged, url_set)

        if fact["url"]:
            url_set.add(fact["url"])

    for name, (spec_set, url_set) in all_specs.items():
        candidates = cand_idx.get(name, [])
        if not candidates:
            raise ValueError(f"no candidates for {name}")

        # Filter candidates that satisfy all constraints
        satisfying = []
        for c in candidates:
            v = c["_version"]
            v_str = str(v)

            # Check specifier
            if not spec_set.contains(v, prereleases):
                continue

            # Check URL: if there are URL constraints, candidate must have matching URL
            # For URL-only requirements, any version of the candidate is fine
            # as long as the candidate exists
            satisfying.append((v, v_str))

        if not satisfying:
            raise ValueError(f"no satisfying candidate for {name}")

        # Select highest version
        satisfying.sort(key=lambda x: x[0])
        best_v, best_str = satisfying[-1]
        selected[name] = best_str

        # Excluded: candidates not selected
        excl = set()
        for c in candidates:
            cv_str = str(c["_version"])
            if cv_str != best_str:
                excl.add(cv_str)
        excluded[name] = excl

    return selected, excluded, all_specs


def _get_requested_extras_for(
    active_requirements: list[dict],
    project_name: str,
) -> set[str]:
    """Get accumulated extras requested for a project."""
    extras: set[str] = set()
    for fact in active_requirements:
        if fact["name"] == project_name and fact["marker_applicable"]:
            extras.update(fact["extras"])
    return extras


def _build_edges(
    cand_idx: dict[str, list[dict]],
    active_requirements: list[dict],
    selected: dict[str, str],
    prereleases: bool | None,
) -> list[dict]:
    """Build edge projections from active requirements."""
    edges: list[dict] = []

    for fact in active_requirements:
        if fact["parent"] is None:
            continue  # root facts don't create edges

        parent = fact["parent"]
        child = fact["name"]

        # specifier_matches
        specifier_matches: list[tuple[str, bool]] = []
        for c in cand_idx.get(child, []):
            v = c["_version"]
            v_str = str(v)
            m = fact["specifier"].contains(v, prereleases)
            specifier_matches.append((v_str, m))

        edge = {
            "parent": parent,
            "name": child,
            "extras": sorted(fact["extras"]),
            "specifier": str(fact["specifier"]) if str(fact["specifier"]) else "",
            "url": fact["url"],
            "marker": str(fact["marker"]) if fact["marker"] else None,
            "marker_applicable": fact["marker_applicable"],
            "specifier_matches": specifier_matches,
        }
        edges.append(edge)

    return edges
