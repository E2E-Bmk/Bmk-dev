"""MiniPackaging: dependency-free Python package metadata evaluator.

Inspired by pypa/packaging and PEP 440 / PEP 508 behavior.
"""

from __future__ import annotations

import copy
import itertools
import re
from typing import Any

# ---------------------------------------------------------------------------
# Name normalization (PEP 503)
# ---------------------------------------------------------------------------

_NAME_NORMALIZE_RE = re.compile(r"[-_.]+")


def _normalize_name(name: str) -> str:
    return _NAME_NORMALIZE_RE.sub("-", name).lower()


def _normalize_extra(extra: str) -> str:
    return _normalize_name(extra)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


class InvalidVersion(ValueError):
    """Raised when a version string cannot be parsed."""


_VERSION_RE = re.compile(
    r"""
    ^
    v?
    (?:(?P<epoch>\d+)!)?               # epoch
    (?P<release>\d+(?:\.\d+)*)         # release segments
    (?:
        [-_.]?
        (?P<pre>                        # pre-release
            alpha|a|beta|b|preview|pre|c|rc
        )
        (?P<pre_n>\d+)
    )?
    (?:
        [-_.]?(?:r|rev)
        (?P<post_n>\d+)
    )?
    (?:
        [-_.]?post
        (?P<post_n2>\d+)
    )?
    (?:
        [-_.]?dev
        (?P<dev_n>\d+)
    )?
    (?:\+(?P<local>[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?))?  # local
    $
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Canonical pre-release phase order for sorting
_PRE_PHASE_ORDER = {"a": 0, "alpha": 0, "b": 1, "beta": 1, "rc": 2, "c": 2, "pre": 2, "preview": 2}

# Map alternative forms to canonical
_PRE_CANONICAL = {
    "alpha": "a",
    "beta": "b",
    "pre": "rc",
    "preview": "rc",
    "c": "rc",
}


def _normalize_local_segments(local: str) -> str:
    """Normalize local label segments: lowercase, replace [-_] with ."""
    local = local.lower()
    # Split on dots and normalize each segment
    segments = []
    for seg in local.split("."):
        # Within a segment, underscores and hyphens become dots
        seg = re.sub(r"[-_]+", ".", seg)
        segments.append(seg)
    return ".".join(segments)


_ILLEGAL_VERSION_RE = re.compile(r"^[v]?\d.*$")


class Version:
    """PEP 440 version object."""

    __slots__ = ("_epoch", "_release", "_pre", "_post", "_dev", "_local", "_key")

    def __init__(self, text: str) -> None:
        if not isinstance(text, str):
            raise InvalidVersion(f"expected string, got {type(text).__name__}")
        text = text.strip()
        if not text:
            raise InvalidVersion("empty version string")
        m = _VERSION_RE.match(text)
        if m is None:
            raise InvalidVersion(f"invalid version: {text!r}")

        epoch_str = m.group("epoch")
        self._epoch = int(epoch_str) if epoch_str is not None else 0

        release_str = m.group("release")
        # Parse release segments, stripping leading zeros from each segment
        raw_release = tuple(int(s) for s in release_str.split("."))
        # Strip trailing zero segments (but keep at least one)
        release_list = list(raw_release)
        while len(release_list) > 1 and release_list[-1] == 0:
            release_list.pop()
        self._release = tuple(release_list)

        pre_phase = m.group("pre")
        pre_n = m.group("pre_n")
        if pre_phase is not None:
            phase_lower = pre_phase.lower()
            canonical_phase = _PRE_CANONICAL.get(phase_lower, phase_lower)
            self._pre = (canonical_phase, int(pre_n))
        else:
            self._pre = None

        post_n = m.group("post_n") or m.group("post_n2")
        self._post = int(post_n) if post_n is not None else None

        dev_n = m.group("dev_n")
        self._dev = int(dev_n) if dev_n is not None else None

        local = m.group("local")
        self._local = _normalize_local_segments(local) if local is not None else None

        # Pre-compute sort key
        self._key = self._compute_key()

    def _compute_key(self):
        """Return a sort key tuple. Order: dev < pre < final < post."""
        key = [self._epoch]
        # Release
        key.append(self._release)
        # Dev: 0 for dev present (sorts first), 1 for no dev (sorts later)
        if self._dev is not None:
            key.append(0)  # is_dev
            key.append(self._dev)
        else:
            key.append(1)  # not_dev
            key.append(0)
        # Pre-release: phase order for pre, inf for no pre (final/post)
        if self._pre is not None:
            phase, num = self._pre
            key.append(_PRE_PHASE_ORDER[phase])
            key.append(num)
        else:
            key.append(float("inf"))
            key.append(0)
        # Post-release: 0 for no post, 1 for post present
        if self._post is not None:
            key.append(1)
            key.append(self._post)
        else:
            key.append(0)
            key.append(0)
        return tuple(key)

    @property
    def epoch(self) -> int:
        return self._epoch

    @property
    def release(self) -> tuple[int, ...]:
        return self._release

    @property
    def is_prerelease(self) -> bool:
        return self._pre is not None or self._dev is not None

    def __str__(self) -> str:
        """Canonical string representation."""
        parts = []
        if self._epoch != 0:
            parts.append(f"{self._epoch}!")
        parts.append(".".join(str(s) for s in self._release))

        if self._pre is not None:
            parts.append(f"{self._pre[0]}{self._pre[1]}")
        if self._post is not None:
            parts.append(f".post{self._post}")
        if self._dev is not None:
            parts.append(f".dev{self._dev}")
        result = "".join(parts)
        if self._local is not None:
            result += f"+{self._local}"
        return result

    def __repr__(self) -> str:
        return f"Version({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._compare_key() == other._compare_key()

    def __lt__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._compare_key() < other._compare_key()

    def __le__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._compare_key() <= other._compare_key()

    def __gt__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._compare_key() > other._compare_key()

    def __ge__(self, other: Version) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._compare_key() >= other._compare_key()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._compare_key() != other._compare_key()

    def _compare_key(self):
        """Full comparison key including local label for ordering."""
        key = list(self._key)
        # For total ordering, local labels matter
        if self._local is not None:
            # local segments: compare segment-by-segment
            local_segments = []
            for seg in self._local.split("."):
                try:
                    local_segments.append((1, int(seg)))
                except ValueError:
                    local_segments.append((0, seg))
            key.append(tuple(local_segments))
        else:
            key.append(((-1,),))  # no local sorts differently
        return tuple(key)

    def __hash__(self) -> int:
        return hash(str(self))


# ---------------------------------------------------------------------------
# SpecifierSet
# ---------------------------------------------------------------------------


class InvalidSpecifier(ValueError):
    """Raised when a specifier string cannot be parsed."""


_SPECIFIER_RE = re.compile(
    r"""
    \s*
    (?P<op>===|~=|!=|==|<=|>=|<|>)
    \s*
    (?P<version>[^\s,;]+)
    \s*
    """,
    re.VERBOSE,
)


class SpecifierSet:
    """A set of version specifiers."""

    __slots__ = ("_specifiers",)

    def __init__(self, text: str = "") -> None:
        self._specifiers: list[tuple[str, Version, bool]] = []  # (op, version, is_wildcard)
        if not text or not text.strip():
            return
        text = text.strip()
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            m = _SPECIFIER_RE.match(part)
            if m is None:
                raise InvalidSpecifier(f"invalid specifier: {part!r}")
            op = m.group("op")
            ver_text = m.group("version")
            is_wildcard = False
            if ver_text.endswith(".*"):
                is_wildcard = True
                ver_text = ver_text[:-2]
            try:
                ver = Version(ver_text)
            except InvalidVersion:
                raise InvalidSpecifier(f"invalid version in specifier: {ver_text!r}")
            if op == "===" or (op == "==" and is_wildcard and "*" in ver_text):
                raise InvalidSpecifier(f"invalid specifier: {part!r}")
            self._specifiers.append((op, ver, is_wildcard))

    def __str__(self) -> str:
        parts = []
        for op, ver, is_wildcard in self._specifiers:
            v = str(ver)
            if is_wildcard:
                v += ".*"
            parts.append(f"{op}{v}")
        return ",".join(parts)

    def __repr__(self) -> str:
        return f"SpecifierSet({str(self)!r})"

    def contains(self, version: str | Version, prereleases: bool | None = None) -> bool:
        """Check if version is contained by this specifier set."""
        if isinstance(version, str):
            ver = Version(version)
        else:
            ver = version

        # Pre-release filtering: by default, pre-releases are excluded
        if prereleases is None:
            prereleases = False
        if not prereleases and ver.is_prerelease:
            return False

        # Empty specifier set matches everything
        if not self._specifiers:
            return True

        for op, spec_ver, is_wildcard in self._specifiers:
            if not _check_single(ver, op, spec_ver, is_wildcard, prereleases):
                return False
        return True


def _check_single(
    version: Version, op: str, spec_ver: Version, is_wildcard: bool, prereleases: bool
) -> bool:
    """Check a single specifier against a version."""
    if is_wildcard:
        return _check_wildcard(version, op, spec_ver)

    if op == "==":
        return version == spec_ver
    elif op == "!=":
        return version != spec_ver
    elif op == "<":
        return version < spec_ver
    elif op == "<=":
        return version <= spec_ver
    elif op == ">":
        return version > spec_ver
    elif op == ">=":
        return version >= spec_ver
    elif op == "~=":
        return _check_compatible(version, spec_ver)
    else:
        return False


def _check_wildcard(version: Version, op: str, spec_ver: Version) -> bool:
    """Check wildcard prefix matching."""
    # Version matches spec_ver.* if release prefix matches
    spec_release = spec_ver.release
    ver_release = version.release
    if len(ver_release) < len(spec_release):
        # Pad with zeros
        ver_padded = list(ver_release) + [0] * (len(spec_release) - len(ver_release))
    else:
        ver_padded = list(ver_release[:len(spec_release)])

    match = tuple(ver_padded) == spec_release
    if op == "==":
        return match
    elif op == "!=":
        return not match
    return False


def _check_compatible(version: Version, spec_ver: Version) -> bool:
    """Check compatible release (~=)."""
    release = spec_ver.release
    # Strip trailing zeros from spec version release
    trimmed = list(release)
    while len(trimmed) > 1 and trimmed[-1] == 0:
        trimmed.pop()

    # Lower bound: use the full release (before zero-stripping) as lower bound
    lower = Version(".".join(str(s) for s in release))

    # Upper bound: increment the second-to-last segment, zero everything after it
    if len(trimmed) >= 2:
        upper_release = list(trimmed)
        upper_release[-2] += 1
        # Zero out all segments AFTER the incremented position
        inc_pos = len(upper_release) - 2
        for i in range(inc_pos + 1, len(upper_release)):
            upper_release[i] = 0
        upper = Version(".".join(str(s) for s in upper_release))
    else:
        # ~=1 means >=1, <2
        upper_release = [trimmed[0] + 1]
        upper = Version(str(upper_release[0]))

    return version >= lower and version < upper


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------


class InvalidRequirement(ValueError):
    """Raised when a requirement string cannot be parsed."""


# Package name validation: must start with letter/digit, contain only
# alphanumeric, dots, hyphens, underscores
_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")

# Extras in brackets: [extra1,extra2,...]
_EXTRAS_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")


def _validate_extra(extra: str) -> bool:
    return bool(_EXTRAS_RE.match(extra))


class Requirement:
    """PEP 508 requirement."""

    __slots__ = ("_name", "_extras", "_specifier", "_url", "_marker", "_hash_key")

    def __init__(self, text: str) -> None:
        if not isinstance(text, str):
            raise InvalidRequirement(f"expected string, got {type(text).__name__}")
        text = text.strip()
        if not text:
            raise InvalidRequirement("empty requirement string")

        # Parse: name [extras] @ url ; marker
        # or:  name [extras] specifier ; marker
        self._url = None
        self._marker = None

        # Find marker part (after ;)
        marker_text = None
        if ";" in text:
            # Split on last ; not inside quotes
            parts = _split_marker(text)
            if len(parts) == 2:
                text, marker_text = parts
            else:
                # The ; might be inside a URL
                pass

        # Check for URL (@)
        if " @ " in text:
            name_part, url_part = text.split(" @ ", 1)
            name_part = name_part.strip()
            url_part = url_part.strip()
            # Validate no specifier with URL
            # Parse name and extras
            name, extras = _parse_name_extras(name_part)
            if not _NAME_RE.match(name):
                raise InvalidRequirement(f"invalid package name: {name!r}")
            self._name = _normalize_name(name)
            # Validate extras
            for extra in extras:
                if not _validate_extra(extra):
                    raise InvalidRequirement(f"invalid extra: {extra!r}")
            self._extras = tuple(sorted(_normalize_extra(e) for e in extras))
            self._url = url_part
            # Check that there's no specifier mixed in with URL
            if ">=" in url_part or "<=" in url_part or "==" in url_part or "!=" in url_part:
                raise InvalidRequirement("direct URL requirements must not include specifier")
            self._specifier = SpecifierSet("")
        else:
            # Parse name, extras, and specifier
            name, spec_text = _split_name_spec(text)
            name, extras = _parse_name_extras(name)
            if not _NAME_RE.match(name):
                raise InvalidRequirement(f"invalid package name: {name!r}")
            self._name = _normalize_name(name)
            for extra in extras:
                if not _validate_extra(extra):
                    raise InvalidRequirement(f"invalid extra: {extra!r}")
            self._extras = tuple(sorted(_normalize_extra(e) for e in extras))
            spec_text = spec_text.strip()
            if spec_text:
                try:
                    self._specifier = SpecifierSet(spec_text)
                except InvalidSpecifier:
                    raise InvalidRequirement(f"invalid specifier in requirement: {spec_text!r}")
            else:
                self._specifier = SpecifierSet("")

        # Parse marker
        if marker_text is not None:
            try:
                self._marker = Marker(marker_text.strip())
            except InvalidMarker:
                raise InvalidRequirement(f"invalid marker in requirement: {marker_text!r}")

        self._hash_key = (
            self._name,
            self._extras,
            str(self._specifier),
            self._url or "",
            str(self._marker) if self._marker else "",
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def extras(self) -> tuple[str, ...]:
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
            parts.append(f"[{','.join(self._extras)}]")

        if self._url:
            parts.append(f" @ {self._url}")
        else:
            spec_str = str(self._specifier)
            if spec_str:
                parts.append(spec_str)

        result = "".join(parts)

        if self._marker is not None:
            marker_str = str(self._marker)
            if marker_str:
                result += f"; {marker_str}"

        return result

    def __repr__(self) -> str:
        return f"Requirement({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Requirement):
            return NotImplemented
        return self._hash_key == other._hash_key

    def __hash__(self) -> int:
        return hash(self._hash_key)


def _split_marker(text: str) -> list[str]:
    """Split requirement text from marker at the last semicolon not inside quotes."""
    in_quote = False
    for i in range(len(text) - 1, -1, -1):
        if text[i] == '"':
            in_quote = not in_quote
        elif text[i] == ";" and not in_quote:
            return [text[:i], text[i + 1 :]]
    return [text]


def _split_name_spec(text: str) -> tuple[str, str]:
    """Split package name+extras from specifier."""
    # Find where the name ends: after any bracket group
    bracket_depth = 0
    for i, ch in enumerate(text):
        if ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth -= 1
        elif bracket_depth == 0 and ch in "><=!~":
            # Found start of specifier
            return text[:i].strip(), text[i:].strip()
    return text.strip(), ""


def _parse_name_extras(name_part: str) -> tuple[str, list[str]]:
    """Parse name and extras from a name[extra1,extra2] string."""
    extras: list[str] = []
    if "[" in name_part:
        bracket_start = name_part.index("[")
        bracket_end = name_part.rindex("]")
        name = name_part[:bracket_start].strip()
        extras_str = name_part[bracket_start + 1 : bracket_end]
        extras = [e.strip() for e in extras_str.split(",") if e.strip()]
    else:
        name = name_part.strip()
    return name, extras


# ---------------------------------------------------------------------------
# Marker
# ---------------------------------------------------------------------------


class InvalidMarker(ValueError):
    """Raised when a marker string cannot be parsed."""


class UndefinedEnvironmentName(ValueError):
    """Raised when a marker references an undefined environment variable."""


class Marker:
    """PEP 508 environment marker expression."""

    __slots__ = ("_text", "_ast")

    def __init__(self, text: str) -> None:
        if not isinstance(text, str):
            raise InvalidMarker(f"expected string, got {type(text).__name__}")
        text = text.strip()
        self._text = text
        self._ast = self._parse(text)

    def _parse(self, text: str):
        """Parse marker expression into AST."""
        tokens = _tokenize(text)
        ast, pos = _parse_expression(tokens, 0)
        if pos < len(tokens):
            raise InvalidMarker(f"unexpected token: {tokens[pos]!r}")
        return ast

    def __str__(self) -> str:
        return self._text

    def evaluate(
        self,
        environment: dict[str, str] | None = None,
        requested_extras: set[str] | None = None,
    ) -> bool:
        """Evaluate the marker against an environment."""
        if environment is None:
            environment = {}
        return _eval_ast(self._ast, environment, requested_extras or set())


# Token types for marker parsing
_TOK_VAR = 1
_TOK_OP = 2
_TOK_VALUE = 3
_TOK_AND = 4
_TOK_OR = 5
_TOK_LPAREN = 6
_TOK_RPAREN = 7
_TOK_IN = 8

_MARKER_OPS = {"==", "!=", "<", "<=", ">", ">=", "in"}


def _tokenize(text: str) -> list[tuple[int, str]]:
    """Tokenize a marker expression."""
    tokens: list[tuple[int, str]] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "(":
            tokens.append((_TOK_LPAREN, "("))
            i += 1
        elif ch == ")":
            tokens.append((_TOK_RPAREN, ")"))
            i += 1
        elif ch == '"':
            # Quoted string value
            j = i + 1
            while j < len(text) and text[j] != '"':
                j += 1
            if j >= len(text):
                raise InvalidMarker("unclosed quote")
            tokens.append((_TOK_VALUE, text[i + 1 : j]))
            i = j + 1
        elif ch in "><=!":
            # Operator
            j = i
            while j < len(text) and text[j] in "><=!":
                j += 1
            op = text[i:j]
            if op not in _MARKER_OPS:
                raise InvalidMarker(f"invalid operator: {op!r}")
            tokens.append((_TOK_OP, op))
            i = j
        elif text[i : i + 2] == "in" and (i + 2 >= len(text) or not text[i + 2].isalnum()):
            tokens.append((_TOK_IN, "in"))
            i += 2
        elif text[i : i + 3] == "and" and (i + 3 >= len(text) or not text[i + 3].isalnum()):
            tokens.append((_TOK_AND, "and"))
            i += 3
        elif text[i : i + 2] == "or" and (i + 2 >= len(text) or not text[i + 2].isalnum()):
            tokens.append((_TOK_OR, "or"))
            i += 2
        elif ch.isalpha() or ch == "_":
            # Variable name
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] in "_."):
                j += 1
            tokens.append((_TOK_VAR, text[i:j]))
            i = j
        else:
            raise InvalidMarker(f"unexpected character: {ch!r}")
    return tokens


def _parse_expression(
    tokens: list[tuple[int, str]], pos: int
) -> tuple[tuple, int]:
    """Parse an expression (or-expression level)."""
    left, pos = _parse_and_expr(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] == _TOK_OR:
        pos += 1  # skip 'or'
        right, pos = _parse_and_expr(tokens, pos)
        left = ("or", left, right)
    return left, pos


def _parse_and_expr(
    tokens: list[tuple[int, str]], pos: int
) -> tuple[tuple, int]:
    """Parse an and-expression."""
    left, pos = _parse_atom(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] == _TOK_AND:
        pos += 1  # skip 'and'
        right, pos = _parse_atom(tokens, pos)
        left = ("and", left, right)
    return left, pos


def _parse_atom(
    tokens: list[tuple[int, str]], pos: int
) -> tuple[tuple, int]:
    """Parse a parenthesized expression or comparison."""
    if pos >= len(tokens):
        raise InvalidMarker("unexpected end of expression")

    if tokens[pos][0] == _TOK_LPAREN:
        pos += 1  # skip '('
        expr, pos = _parse_expression(tokens, pos)
        if pos >= len(tokens) or tokens[pos][0] != _TOK_RPAREN:
            raise InvalidMarker("missing closing parenthesis")
        pos += 1  # skip ')'
        return expr, pos

    # Must be: variable op value
    if tokens[pos][0] != _TOK_VAR:
        raise InvalidMarker(f"expected variable, got {tokens[pos]!r}")
    var = tokens[pos][1]
    pos += 1

    if pos >= len(tokens):
        raise InvalidMarker(f"expected operator after {var!r}")

    if tokens[pos][0] == _TOK_IN:
        op = "in"
        pos += 1
    elif tokens[pos][0] == _TOK_OP:
        op = tokens[pos][1]
        pos += 1
    else:
        raise InvalidMarker(f"expected operator, got {tokens[pos]!r}")

    if pos >= len(tokens) or tokens[pos][0] != _TOK_VALUE:
        raise InvalidMarker(f"expected value, got {tokens[pos]!r}")
    value = tokens[pos][1]
    pos += 1

    return ("cmp", var, op, value), pos


def _eval_ast(
    ast: tuple,
    environment: dict[str, str],
    requested_extras: set[str],
) -> bool:
    """Evaluate a parsed marker AST."""
    node_type = ast[0]

    if node_type == "and":
        return _eval_ast(ast[1], environment, requested_extras) and _eval_ast(
            ast[2], environment, requested_extras
        )
    elif node_type == "or":
        return _eval_ast(ast[1], environment, requested_extras) or _eval_ast(
            ast[2], environment, requested_extras
        )
    elif node_type == "cmp":
        _, var, op, value = ast
        if var == "extra":
            # extra comparison: normalized names
            normalized_value = _normalize_extra(value)
            normalized_extras = {_normalize_extra(e) for e in requested_extras}
            if op == "==":
                return normalized_value in normalized_extras
            elif op == "!=":
                return normalized_value not in normalized_extras
            else:
                raise InvalidMarker(f"unsupported operator for extra: {op!r}")
        else:
            if var not in environment:
                raise UndefinedEnvironmentName(f"undefined environment variable: {var!r}")
            env_val = environment[var]

            if op == "in":
                # 'in' splits the value by spaces and checks membership
                options = value.split()
                return env_val in options
            elif op == "==":
                return env_val == value
            elif op == "!=":
                return env_val != value
            else:
                # Version comparison operators for python_version and similar
                # Try as version comparison
                try:
                    env_ver = Version(env_val)
                    val_ver = Version(value)
                    if op == "<":
                        return env_ver < val_ver
                    elif op == "<=":
                        return env_ver <= val_ver
                    elif op == ">":
                        return env_ver > val_ver
                    elif op == ">=":
                        return env_ver >= val_ver
                    else:
                        raise InvalidMarker(f"unsupported operator: {op!r}")
                except InvalidVersion:
                    # Fall back to string comparison
                    if op == "<":
                        return env_val < value
                    elif op == "<=":
                        return env_val <= value
                    elif op == ">":
                        return env_val > value
                    elif op == ">=":
                        return env_val >= value
                    else:
                        raise InvalidMarker(f"unsupported operator: {op!r}")
    else:
        raise InvalidMarker(f"unknown AST node: {node_type!r}")


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


def default_environment() -> dict[str, str]:
    """Return a default environment dictionary with common marker variables."""
    import platform
    import sys

    return {
        "os_name": "posix" if sys.platform != "win32" else "nt",
        "sys_platform": sys.platform,
        "platform_machine": platform.machine(),
        "platform_python_implementation": platform.python_implementation(),
        "platform_release": platform.release(),
        "platform_system": platform.system(),
        "platform_version": platform.version(),
        "python_version": ".".join(map(str, sys.version_info[:2])),
        "python_full_version": platform.python_version(),
        "implementation_name": sys.implementation.name,
        "implementation_version": ".".join(map(str, sys.implementation.version[:2]))
        if hasattr(sys.implementation, "version")
        else "0.0",
    }


# ---------------------------------------------------------------------------
# is_requirement_satisfied
# ---------------------------------------------------------------------------


def is_requirement_satisfied(
    requirement: Requirement,
    installed_version: str | Version,
    environment: dict[str, str] | None = None,
    requested_extras: set[str] | None = None,
    prereleases: bool | None = None,
) -> bool:
    """Check if a requirement is satisfied by an installed version."""
    if environment is None:
        environment = {}
    if requested_extras is None:
        requested_extras = set()

    # Check marker
    if requirement.marker is not None:
        if not requirement.marker.evaluate(environment, requested_extras):
            return False

    # Check specifier
    if isinstance(installed_version, str):
        ver = Version(installed_version)
    else:
        ver = installed_version

    return requirement.specifier.contains(ver, prereleases=prereleases)


# ---------------------------------------------------------------------------
# resolve_metadata
# ---------------------------------------------------------------------------


def resolve_metadata(
    roots: list[str],
    candidates: list[dict[str, Any]],
    environment: dict[str, str] | None = None,
    requested_extras: set[str] | None = None,
    prereleases: bool | None = None,
) -> dict[str, Any]:
    """Resolve dependency metadata from roots and candidates.

    Returns a dict with keys: selected, excluded, edges, dependents,
    requested_extras, requirements.
    """
    if environment is None:
        environment = {}
    if requested_extras is None:
        requested_extras = set()

    # Parse root requirements
    root_reqs: list[Requirement] = []
    for r_text in roots:
        root_reqs.append(Requirement(r_text))

    # Build candidate lookup: normalized_name -> list of (version, requires)
    candidate_map: dict[str, list[tuple[Version, list[str]]]] = {}
    for c in candidates:
        name = _normalize_name(c["name"])
        ver = Version(c["version"])
        reqs = list(c.get("requires", []))
        if name not in candidate_map:
            candidate_map[name] = []
        candidate_map[name].append((ver, reqs))

    # Normalize root requested extras
    root_extra_map: dict[str, set[str]] = {}
    for r in root_reqs:
        n = r.name
        if n not in root_extra_map:
            root_extra_map[n] = set()
        root_extra_map[n].update(r.extras)

    # Build constraint sets per project name from root requirements
    return _resolve_inner(
        candidate_map=candidate_map,
        root_reqs=root_reqs,
        root_extra_map=root_extra_map,
        environment=environment,
        requested_extras=set(requested_extras),
        prereleases=prereleases,
    )


def _resolve_inner(
    candidate_map: dict[str, list[tuple[Version, list[str]]]],
    root_reqs: list[Requirement],
    root_extra_map: dict[str, set[str]],
    environment: dict[str, str],
    requested_extras: set[str],
    prereleases: bool | None,
) -> dict[str, Any]:
    """Core resolution logic used by both resolve_metadata and MetadataIndex."""

    # requirements fact list
    requirements: list[dict[str, Any]] = []

    # For root requirements
    for r in root_reqs:
        requirements.append(
            {
                "source": "root",
                "parent": None,
                "name": r.name,
                "extras": list(r.extras),
                "specifier": r.specifier,
                "marker": r.marker,
                "url": r.url,
                "requirement": r,
            }
        )

    # Track which projects we've processed
    processed: set[str] = set()
    # Active constraints per project: name -> list of Requirement
    active_constraints: dict[str, list[Requirement]] = {}
    # Accumulated extras per project: name -> set of extras
    accumulated_extras: dict[str, set[str]] = {}

    # Initialize from roots
    for r in root_reqs:
        if r.name not in active_constraints:
            active_constraints[r.name] = []
        active_constraints[r.name].append(r)
        if r.name not in accumulated_extras:
            accumulated_extras[r.name] = set()
        accumulated_extras[r.name].update(r.extras)

    # Iterative resolution
    selected: dict[str, str] = {}  # name -> canonical version string
    changed = True
    while changed:
        changed = False
        to_process = set(active_constraints.keys()) - processed
        for name in sorted(to_process):
            processed.add(name)
            if name not in candidate_map:
                continue

            # Get all applicable constraints for this project
            constraints = active_constraints.get(name, [])
            # Merge specifiers (conjunction)
            merged_spec = _merge_specifiers(
                [r.specifier for r in constraints if r.url is None]
            )

            # Find best matching version
            best_ver: Version | None = None
            best_ver_str: str | None = None
            excluded_versions: list[str] = []

            for ver, reqs in candidate_map.get(name, []):
                ver_str = str(ver)
                if merged_spec.contains(ver, prereleases=prereleases):
                    if best_ver is None or ver > best_ver:
                        best_ver = ver
                        best_ver_str = ver_str
                else:
                    excluded_versions.append(ver_str)

            if best_ver is not None and best_ver_str is not None:
                if name not in selected or selected[name] != best_ver_str:
                    selected[name] = best_ver_str
                    changed = True

                # Process dependencies of the selected candidate
                _, req_texts = next(
                    ((v, r) for v, r in candidate_map[name] if str(v) == best_ver_str),
                    (best_ver, []),
                )
                for req_text in req_texts:
                    try:
                        dep_req = Requirement(req_text)
                    except (InvalidRequirement, InvalidSpecifier, InvalidMarker):
                        continue

                    # Check marker applicability
                    applicable = True
                    if dep_req.marker is not None:
                        dep_extras = accumulated_extras.get(name, set())
                        try:
                            applicable = dep_req.marker.evaluate(environment, dep_extras)
                        except UndefinedEnvironmentName:
                            applicable = False

                    if applicable:
                        dep_name = dep_req.name
                        if dep_name not in active_constraints:
                            active_constraints[dep_name] = []
                        active_constraints[dep_name].append(dep_req)
                        if dep_name not in accumulated_extras:
                            accumulated_extras[dep_name] = set()
                        accumulated_extras[dep_name].update(dep_req.extras)

                        requirements.append(
                            {
                                "source": name,
                                "parent": name,
                                "name": dep_name,
                                "extras": list(dep_req.extras),
                                "specifier": dep_req.specifier,
                                "marker": dep_req.marker,
                                "url": dep_req.url,
                                "requirement": dep_req,
                            }
                        )
                        if dep_name not in processed:
                            changed = True

    # Build edges from requirements (non-root)
    edges: list[dict[str, Any]] = []
    for req_entry in requirements:
        if req_entry["source"] != "root":
            edges.append(
                {
                    "parent": req_entry["parent"],
                    "name": req_entry["name"],
                    "extras": tuple(req_entry["extras"]),
                }
            )

    # Build dependents from edges
    dependents: dict[str, list[str]] = {}
    for edge in edges:
        child = edge["name"]
        parent = edge["parent"]
        if child not in dependents:
            dependents[child] = []
        if parent not in dependents[child]:
            dependents[child].append(parent)
    for k in dependents:
        dependents[k].sort()

    # Build excluded
    excluded: dict[str, list[str]] = {}
    all_names = set(active_constraints.keys())
    for name in all_names:
        if name in candidate_map:
            ex_vers = []
            sel_ver = selected.get(name)
            for ver, _ in candidate_map[name]:
                ver_str = str(ver)
                if sel_ver is None or ver_str != sel_ver:
                    ex_vers.append(ver_str)
            if ex_vers:
                excluded[name] = sorted(ex_vers, key=Version)

    # Build requested_extras
    requested_extras_out: dict[str, tuple[str, ...]] = {}
    all_project_names = set(selected.keys()) | set(accumulated_extras.keys())
    for name in all_project_names:
        extras = accumulated_extras.get(name, set()) | root_extra_map.get(name, set())
        if extras:
            requested_extras_out[name] = tuple(sorted(extras))

    # Ensure all selected projects have an entry
    for name in selected:
        if name not in requested_extras_out:
            requested_extras_out[name] = ()

    # Build final requirements output
    reqs_out: list[dict[str, Any]] = []
    for req_entry in requirements:
        reqs_out.append(
            {
                "source": req_entry["source"],
                "parent": req_entry["parent"],
                "name": req_entry["name"],
                "extras": tuple(req_entry["extras"]),
            }
        )

    return {
        "selected": dict(sorted(selected.items())),
        "excluded": excluded,
        "edges": edges,
        "dependents": dependents,
        "requested_extras": requested_extras_out,
        "requirements": reqs_out,
    }


def _merge_specifiers(specifiers: list[SpecifierSet]) -> SpecifierSet:
    """Merge multiple specifier sets into one (conjunction)."""
    if not specifiers:
        return SpecifierSet("")
    # Combine all individual specifiers from all sets
    all_specs: list[str] = []
    for s in specifiers:
        s_str = str(s)
        if s_str:
            for part in s_str.split(","):
                part = part.strip()
                if part:
                    all_specs.append(part)
    if not all_specs:
        return SpecifierSet("")
    return SpecifierSet(",".join(all_specs))


# ---------------------------------------------------------------------------
# MetadataIndex
# ---------------------------------------------------------------------------


class MetadataIndex:
    """Persistent local metadata index with revision tracking."""

    def __init__(self, candidates: tuple[dict[str, Any], ...] | list[dict[str, Any]] = ()) -> None:
        self._revision = 0
        # stored: dict of (name, version_str) -> candidate_dict
        self._candidates: dict[tuple[str, str], dict[str, Any]] = {}
        if candidates:
            for c in candidates:
                self._store_candidate(copy.deepcopy(c), increment=False)
            self._revision = len(self._candidates)

    # -- Copy helpers --

    def _store_candidate(
        self, candidate: dict[str, Any], increment: bool = True
    ) -> None:
        """Store a deep-copied candidate record."""
        name = _normalize_name(candidate["name"])
        ver = str(Version(candidate["version"]))
        copied = {
            "name": name,
            "version": ver,
            "requires": list(candidate.get("requires", [])),
        }
        self._candidates[(name, ver)] = copied
        if increment:
            self._revision += 1

    def _remove_candidate_internal(self, name: str, version: str) -> None:
        """Remove a candidate from storage."""
        norm_name = _normalize_name(name)
        ver = str(Version(version))
        key = (norm_name, ver)
        if key not in self._candidates:
            raise ValueError(f"candidate not found: {name} {version}")
        del self._candidates[key]
        self._revision += 1

    # -- Public mutation methods --

    def add_candidate(self, candidate: dict[str, Any]) -> None:
        """Add or replace a candidate record."""
        self._validate_candidate(candidate)
        self._store_candidate(copy.deepcopy(candidate))

    def remove_candidate(self, name: str, version: str) -> None:
        """Remove a candidate record."""
        self._remove_candidate_internal(name, version)

    def apply(self, changes: list[dict[str, Any]]) -> None:
        """Apply a batch of changes atomically."""
        # Validate all changes first
        self._validate_changes(changes)

        # Make a backup
        backup_revision = self._revision
        backup_candidates = copy.deepcopy(self._candidates)

        try:
            for change in changes:
                action = change["action"]
                if action == "add":
                    self._validate_candidate(change["candidate"])
                    self._store_candidate(copy.deepcopy(change["candidate"]))
                elif action == "update":
                    cand = change["candidate"]
                    self._validate_candidate(cand)
                    name = _normalize_name(cand["name"])
                    ver = str(Version(cand["version"]))
                    key = (name, ver)
                    if key not in self._candidates:
                        raise ValueError(f"update target not found: {cand['name']} {cand['version']}")
                    self._store_candidate(copy.deepcopy(cand))
                elif action == "remove":
                    self._remove_candidate_internal(change["name"], change["version"])
        except Exception:
            # Rollback
            self._revision = backup_revision
            self._candidates = backup_candidates
            raise

    def _validate_candidate(self, candidate: dict[str, Any]) -> None:
        """Validate a candidate record."""
        if not isinstance(candidate, dict):
            raise ValueError("candidate must be a dict")
        if "name" not in candidate or "version" not in candidate:
            raise ValueError("candidate must have name and version")
        # Validate version parses
        Version(candidate["version"])
        # Validate requires are valid requirement strings
        for req_text in candidate.get("requires", []):
            if not isinstance(req_text, str):
                raise ValueError(f"requirement must be a string, got {type(req_text).__name__}")
            Requirement(req_text)

    def _validate_changes(self, changes: list[dict[str, Any]]) -> None:
        """Validate a batch of changes."""
        if not isinstance(changes, list):
            raise ValueError("changes must be a list")
        for change in changes:
            action = change.get("action")
            if action not in ("add", "update", "remove"):
                raise ValueError(f"unknown action: {action!r}")
            if action in ("add", "update"):
                if "candidate" not in change:
                    raise ValueError(f"{action} requires 'candidate' key")
                self._validate_candidate(change["candidate"])
            elif action == "remove":
                if "name" not in change or "version" not in change:
                    raise ValueError("remove requires 'name' and 'version'")

    # -- Query methods --

    def index(self) -> dict[str, list[dict[str, Any]]]:
        """Return deterministic stored-candidate projection."""
        # Group by normalized name
        groups: dict[str, list[dict[str, Any]]] = {}
        for (name, ver), cand in self._candidates.items():
            if name not in groups:
                groups[name] = []
            groups[name].append(dict(cand))
        # Sort each group by Version ascending
        for name in groups:
            groups[name].sort(key=lambda c: Version(c["version"]))
        return groups

    def resolve(
        self,
        roots: list[str],
        environment: dict[str, str] | None = None,
        requested_extras: set[str] | None = None,
        prereleases: bool | None = None,
    ) -> dict[str, Any]:
        """Resolve against stored candidates."""
        if environment is None:
            environment = {}
        if requested_extras is None:
            requested_extras = set()

        # Build candidates list from stored
        candidates = []
        for cand in self._candidates.values():
            candidates.append(dict(cand))

        # Parse roots
        root_reqs = [Requirement(r) for r in roots]

        root_extra_map: dict[str, set[str]] = {}
        for r in root_reqs:
            n = r.name
            if n not in root_extra_map:
                root_extra_map[n] = set()
            root_extra_map[n].update(r.extras)

        # Build candidate_map
        candidate_map: dict[str, list[tuple[Version, list[str]]]] = {}
        for c in candidates:
            name = _normalize_name(c["name"])
            ver = Version(c["version"])
            reqs = list(c.get("requires", []))
            if name not in candidate_map:
                candidate_map[name] = []
            candidate_map[name].append((ver, reqs))

        result = _resolve_inner(
            candidate_map=candidate_map,
            root_reqs=root_reqs,
            root_extra_map=root_extra_map,
            environment=environment,
            requested_extras=set(requested_extras),
            prereleases=prereleases,
        )
        result["revision"] = self._revision
        result["index"] = self.index()
        return result

    def dependents_of(
        self,
        name: str,
        roots: list[str] | None = None,
        transitive: bool = False,
        **resolve_options: Any,
    ) -> list[str]:
        """Return sorted parent project names that depend on name."""
        env = resolve_options.get("environment")
        req_extras = resolve_options.get("requested_extras")
        prereleases = resolve_options.get("prereleases")

        if roots is None:
            roots = list(
                {n for (n, _) in self._candidates.keys()}
            )

        result = self.resolve(roots, environment=env, requested_extras=req_extras, prereleases=prereleases)
        norm_name = _normalize_name(name)
        direct = sorted(result["dependents"].get(norm_name, []))

        if not transitive:
            return direct

        # Transitive: BFS through dependents
        all_deps: set[str] = set()
        queue = list(direct)
        while queue:
            current = queue.pop(0)
            if current in all_deps:
                continue
            all_deps.add(current)
            for parent in result["dependents"].get(current, []):
                if parent not in all_deps:
                    queue.append(parent)

        return sorted(all_deps)

    def resolve_lock(
        self,
        roots: list[str],
        environment: dict[str, str] | None = None,
        requested_extras: set[str] | None = None,
        prereleases: bool | None = None,
    ) -> dict[str, Any]:
        """Create a JSON-safe lock snapshot."""
        if environment is None:
            environment = {}
        if requested_extras is None:
            requested_extras = set()

        result = self.resolve(roots, environment, requested_extras, prereleases)

        # Parse root requirement texts for the lock
        root_facts = []
        for r_text in roots:
            r = Requirement(r_text)
            root_facts.append(str(r))

        lock = {
            "revision": result["revision"],
            "roots": root_facts,
            "selected": dict(result["selected"]),
            "edges": copy.deepcopy(result["edges"]),
            "dependents": copy.deepcopy(result["dependents"]),
            "requested_extras": {
                k: list(v) for k, v in result["requested_extras"].items()
            },
            "requirements": [
                {
                    "source": r["source"],
                    "parent": r["parent"],
                    "name": r["name"],
                    "extras": list(r["extras"]),
                }
                for r in result["requirements"]
            ],
            "excluded": copy.deepcopy(result["excluded"]),
            "index": result["index"],
        }
        return lock

    def apply_lock(
        self,
        lock: dict[str, Any],
        environment: dict[str, str] | None = None,
        requested_extras: set[str] | None = None,
        prereleases: bool | None = None,
    ) -> dict[str, Any]:
        """Replay a lock snapshot against the current index."""
        if environment is None:
            environment = {}
        if requested_extras is None:
            requested_extras = set()

        # Validate lock structure
        if not isinstance(lock, dict) or "selected" not in lock:
            raise ValueError("invalid lock format")

        # Check all selected candidates exist in current index
        current_index = self.index()
        for name, ver in lock["selected"].items():
            if name not in current_index:
                raise ValueError(f"locked candidate missing: {name}")
            found = any(c["version"] == ver for c in current_index[name])
            if not found:
                raise ValueError(f"locked candidate missing: {name} {ver}")

        # Resolve with current index to check consistency
        roots = lock.get("roots", [])
        # Re-create roots by building requirement strings from lock's root facts
        if not roots:
            # Derive roots from lock requirements with source='root'
            for req in lock.get("requirements", []):
                if req["source"] == "root":
                    name = req["name"]
                    extras = req.get("extras", [])
                    if extras:
                        roots.append(f"{name}[{','.join(extras)}]")
                    else:
                        roots.append(name)

        current_result = self.resolve(roots, environment, requested_extras, prereleases)

        # Check selected versions match
        lock_selected = dict(lock["selected"])
        for name, ver in lock_selected.items():
            if name not in current_index:
                raise ValueError(f"locked candidate missing: {name}")
            found = any(c["version"] == ver for c in current_index[name])
            if not found:
                raise ValueError(f"locked candidate missing: {name} {ver}")

        # Check that applying the same constraints still yields the locked selection
        # (i.e., dependency metadata hasn't changed in a way that alters selection)
        current_selected = current_result["selected"]
        for name, ver in lock_selected.items():
            if name in current_selected:
                cur_ver = current_selected[name]
                if Version(ver) > Version(cur_ver):
                    raise ValueError(
                        f"lock replay inconsistent: {name} {ver} not selected"
                    )

        # Verify dependency edges are still applicable
        # Build active requirements from lock and verify each
        lock_edges = lock.get("edges", [])
        lock_reqs = lock.get("requirements", [])

        # Check that every edge in the lock is still applicable
        for edge in lock_edges:
            parent = edge["parent"]
            child = edge["name"]
            # Find the parent candidate
            parent_ver = lock_selected.get(parent)
            if parent_ver is None:
                continue
            parent_key = (parent, parent_ver)
            if parent_key not in self._candidates:
                raise ValueError(
                    f"locked parent candidate missing: {parent} {parent_ver}"
                )
            parent_cand = self._candidates[parent_key]
            # Check that one of parent's requires still produces this edge
            found_applicable = False
            for req_text in parent_cand.get("requires", []):
                try:
                    r = Requirement(req_text)
                except (InvalidRequirement, InvalidSpecifier, InvalidMarker):
                    continue
                if r.name == child:
                    # Check marker applicability
                    applicable = True
                    if r.marker is not None:
                        try:
                            # Determine extras context from lock
                            lock_req_extras = lock.get("requested_extras", {}).get(parent, [])
                            applicable = r.marker.evaluate(environment, set(lock_req_extras))
                        except UndefinedEnvironmentName:
                            applicable = False
                    if applicable:
                        found_applicable = True
                        break
            if not found_applicable:
                raise ValueError(
                    f"lock dependency no longer applicable: {parent} -> {child}"
                )

        # Build replay result: use locked selected versions but verify consistency
        replay_result = {
            "revision": self._revision,
            "lock_revision": lock["revision"],
            "selected": dict(lock["selected"]),
            "excluded": {},
            "edges": copy.deepcopy(lock_edges),
            "dependents": copy.deepcopy(lock.get("dependents", {})),
            "requested_extras": {
                k: tuple(v) if isinstance(v, list) else v
                for k, v in lock.get("requested_extras", {}).items()
            },
            "requirements": [
                {
                    "source": r["source"],
                    "parent": r["parent"],
                    "name": r["name"],
                    "extras": tuple(r["extras"]) if isinstance(r["extras"], list) else r["extras"],
                }
                for r in lock_reqs
            ],
            "index": self.index(),
        }

        # Build excluded from current index minus locked selected
        for name in current_index:
            if name not in replay_result["selected"]:
                continue
            sel_ver = replay_result["selected"][name]
            ex_vers = [c["version"] for c in current_index[name] if c["version"] != sel_ver]
            if ex_vers:
                replay_result["excluded"][name] = sorted(ex_vers, key=Version)

        return replay_result

    def export_state(self) -> dict[str, Any]:
        """Export JSON-safe state."""
        candidates_out = {}
        for key, cand in self._candidates.items():
            candidates_out[f"{key[0]}___{key[1]}"] = dict(cand)
        return {
            "revision": self._revision,
            "candidates": candidates_out,
        }

    @classmethod
    def import_state(cls, state: dict[str, Any]) -> MetadataIndex:
        """Reconstruct an index from exported state."""
        idx = cls()
        idx._revision = state["revision"]
        for key_str, cand in state["candidates"].items():
            # Key format: "name___version"
            parts = key_str.rsplit("___", 1)
            if len(parts) == 2:
                idx._candidates[(parts[0], parts[1])] = dict(cand)
        return idx
