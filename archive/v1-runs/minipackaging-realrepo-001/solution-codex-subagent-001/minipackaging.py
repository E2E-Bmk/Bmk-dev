"""A compact, dependency-free subset of Python packaging semantics."""

from __future__ import annotations

import functools
import os
import platform
import re
import sys
from dataclasses import dataclass
from typing import Any


class InvalidVersion(ValueError):
    pass


class InvalidSpecifier(ValueError):
    pass


class InvalidRequirement(ValueError):
    pass


class InvalidMarker(ValueError):
    pass


class UndefinedEnvironmentName(ValueError):
    pass


_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_VERSION_RE = re.compile(
    r"^\s*"
    r"(?:(?P<epoch>[0-9]+)!)?"
    r"(?P<release>[0-9]+(?:\.[0-9]+)*)"
    r"(?:(?:[-_.]?)"
    r"(?P<pre_l>a|alpha|b|beta|rc|c|pre|preview)"
    r"(?:[-_.]?(?P<pre_n>[0-9]+))?)?"
    r"(?:(?:[-_.]?)"
    r"(?P<post_l>post|rev|r)"
    r"(?:[-_.]?(?P<post_n>[0-9]+))?)?"
    r"(?:(?:[-_.]?)"
    r"(?P<dev_l>dev)"
    r"(?:[-_.]?(?P<dev_n>[0-9]+))?)?"
    r"(?:\+(?P<local>[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*))?"
    r"\s*$",
    re.IGNORECASE,
)

_PRE_NORMAL = {
    "a": "a",
    "alpha": "a",
    "b": "b",
    "beta": "b",
    "rc": "rc",
    "c": "rc",
    "pre": "rc",
    "preview": "rc",
}
_PRE_ORDER = {"a": 0, "b": 1, "rc": 2}


def _normalize_name(value: str) -> str:
    if not _NAME_RE.match(value):
        raise ValueError(value)
    return value.replace("_", "-").lower()


def _trim_release(parts: tuple[int, ...]) -> tuple[int, ...]:
    parts = tuple(parts)
    while len(parts) > 1 and parts[-1] == 0:
        parts = parts[:-1]
    return parts


def _cmp_release(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    size = max(len(left), len(right))
    padded_left = left + (0,) * (size - len(left))
    padded_right = right + (0,) * (size - len(right))
    return (padded_left > padded_right) - (padded_left < padded_right)


def _local_key(parts: tuple[str, ...]) -> tuple[tuple[int, Any], ...]:
    key = []
    for part in parts:
        if part.isdigit():
            key.append((1, int(part)))
        else:
            key.append((0, part))
    return tuple(key)


@functools.total_ordering
class Version:
    def __init__(self, text: str | "Version"):
        if isinstance(text, Version):
            self._text = text._text
            self.epoch = text.epoch
            self.release = text.release
            self._raw_release = text._raw_release
            self.pre = text.pre
            self.post = text.post
            self.dev = text.dev
            self.local = text.local
            return
        if not isinstance(text, str):
            raise InvalidVersion("version must be a string")
        match = _VERSION_RE.match(text)
        if not match:
            raise InvalidVersion(text)

        epoch = int(match.group("epoch") or 0)
        raw_release = tuple(int(p) for p in match.group("release").split("."))
        release = _trim_release(raw_release)

        pre = None
        if match.group("pre_l"):
            pre = (_PRE_NORMAL[match.group("pre_l").lower()], int(match.group("pre_n") or 0))

        post = None
        if match.group("post_l"):
            post = int(match.group("post_n") or 0)

        dev = None
        if match.group("dev_l"):
            dev = int(match.group("dev_n") or 0)

        local = ()
        if match.group("local"):
            local = tuple(p.lower() for p in re.split(r"[-_.]", match.group("local")))

        self.epoch = epoch
        self.release = release
        self._raw_release = raw_release
        self.pre = pre
        self.post = post
        self.dev = dev
        self.local = local
        self._text = self._canonical()

    @property
    def is_prerelease(self) -> bool:
        return self.dev is not None or self.pre is not None

    def _canonical(self) -> str:
        parts = []
        if self.epoch:
            parts.append(f"{self.epoch}!")
        parts.append(".".join(str(p) for p in self.release))
        if self.pre is not None:
            parts.append(f"{self.pre[0]}{self.pre[1]}")
        if self.post is not None:
            parts.append(f".post{self.post}")
        if self.dev is not None:
            parts.append(f".dev{self.dev}")
        if self.local:
            parts.append("+" + ".".join(self.local))
        return "".join(parts)

    def _stage_key(self) -> tuple[Any, ...]:
        if self.pre is not None:
            base: tuple[Any, ...] = (1, _PRE_ORDER[self.pre[0]], self.pre[1])
            if self.dev is not None:
                return base + (0, self.dev)
            return base + (1,)
        if self.post is not None:
            base = (3, self.post)
            if self.dev is not None:
                return base + (0, self.dev)
            return base + (1,)
        if self.dev is not None:
            return (0, self.dev)
        return (2,)

    def _public_cmp_tuple(self) -> tuple[Any, ...]:
        return (self.epoch, self.release, self._stage_key())

    def _compare_public(self, other: "Version") -> int:
        if self.epoch != other.epoch:
            return (self.epoch > other.epoch) - (self.epoch < other.epoch)
        rel_cmp = _cmp_release(self.release, other.release)
        if rel_cmp:
            return rel_cmp
        return (self._stage_key() > other._stage_key()) - (
            self._stage_key() < other._stage_key()
        )

    def __str__(self) -> str:
        return self._text

    def __repr__(self) -> str:
        return f"<Version('{self}')>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            try:
                other = Version(other)  # type: ignore[arg-type]
            except Exception:
                return NotImplemented
        return self._compare_public(other) == 0 and _local_key(self.local) == _local_key(other.local)

    def __lt__(self, other: str | "Version") -> bool:
        other = Version(other)
        public_cmp = self._compare_public(other)
        if public_cmp:
            return public_cmp < 0
        if not self.local and other.local:
            return True
        if self.local and not other.local:
            return False
        return _local_key(self.local) < _local_key(other.local)

    def __hash__(self) -> int:
        return hash((self.epoch, self.release, self._stage_key(), _local_key(self.local)))


@dataclass(frozen=True)
class _Clause:
    op: str
    version: Version | None = None
    wildcard: tuple[int, ...] | None = None
    text: str = ""
    upper: Version | None = None

    @property
    def mentions_prerelease(self) -> bool:
        return bool(self.version and self.version.is_prerelease)


_SPEC_RE = re.compile(r"^(==|!=|>=|<=|>|<|~=)\s*(\S+)$")


class SpecifierSet:
    def __init__(self, text: str = ""):
        if not isinstance(text, str):
            raise InvalidSpecifier("specifier must be a string")
        self._clauses = self._parse(text)

    def _parse(self, text: str) -> list[_Clause]:
        stripped = text.strip()
        if stripped.startswith("(") and stripped.endswith(")"):
            stripped = stripped[1:-1].strip()
        if not stripped:
            return []
        clauses: list[_Clause] = []
        for raw in stripped.split(","):
            clause_text = raw.strip()
            if not clause_text:
                raise InvalidSpecifier(text)
            match = _SPEC_RE.match(clause_text)
            if not match:
                raise InvalidSpecifier(text)
            op, version_text = match.group(1), match.group(2)
            if version_text.endswith(".*"):
                if op not in {"==", "!="}:
                    raise InvalidSpecifier(text)
                prefix_text = version_text[:-2]
                if not re.match(r"^[0-9]+(?:\.[0-9]+)*$", prefix_text):
                    raise InvalidSpecifier(text)
                prefix = tuple(int(p) for p in prefix_text.split("."))
                canonical = ".".join(str(p) for p in prefix) + ".*"
                clauses.append(_Clause(op=op, wildcard=prefix, text=f"{op}{canonical}"))
                continue
            try:
                version = Version(version_text)
            except InvalidVersion as exc:
                raise InvalidSpecifier(text) from exc
            upper = None
            if op == "~=":
                if len(version._raw_release) < 2:
                    raise InvalidSpecifier(text)
                upper_parts = list(version._raw_release[:-1])
                upper_parts[-1] += 1
                upper = Version(".".join(str(p) for p in upper_parts))
            clauses.append(_Clause(op=op, version=version, text=f"{op}{version}", upper=upper))
        return clauses

    def __str__(self) -> str:
        return ",".join(c.text for c in self._clauses)

    def __repr__(self) -> str:
        return f"<SpecifierSet('{self}')>"

    def contains(self, version: str | Version, prereleases: bool | None = None) -> bool:
        candidate = Version(version)
        if candidate.is_prerelease:
            if prereleases is False:
                return False
            if prereleases is None and not any(c.mentions_prerelease for c in self._clauses):
                return False
        return all(self._contains_clause(candidate, clause) for clause in self._clauses)

    def _contains_clause(self, candidate: Version, clause: _Clause) -> bool:
        if clause.wildcard is not None:
            matched = self._matches_prefix(candidate, clause.wildcard)
            return matched if clause.op == "==" else not matched

        assert clause.version is not None
        op = clause.op
        spec_version = clause.version
        if op == "~=":
            assert clause.upper is not None
            return candidate >= spec_version and candidate < clause.upper
        if op == "==":
            return candidate == spec_version
        if op == "!=":
            return candidate != spec_version
        if op == ">=":
            return candidate >= spec_version
        if op == "<=":
            return candidate <= spec_version
        if op == ">":
            return candidate > spec_version
        if op == "<":
            return candidate < spec_version
        raise AssertionError(op)

    @staticmethod
    def _matches_prefix(candidate: Version, prefix: tuple[int, ...]) -> bool:
        release = candidate.release
        size = max(len(release), len(prefix))
        padded_release = release + (0,) * (size - len(release))
        padded_prefix = prefix + (0,) * (size - len(prefix))
        return padded_release[: len(prefix)] == padded_prefix[: len(prefix)]


_MARKER_VARIABLES = {
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
}


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


@dataclass(frozen=True)
class _Operand:
    kind: str
    value: str


@dataclass(frozen=True)
class _Compare:
    left: _Operand
    op: str
    right: _Operand


@dataclass(frozen=True)
class _Bool:
    op: str
    left: Any
    right: Any


class _MarkerParser:
    def __init__(self, text: str):
        self.tokens = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> list[_Token]:
        tokens: list[_Token] = []
        i = 0
        while i < len(text):
            ch = text[i]
            if ch.isspace():
                i += 1
                continue
            if ch in "()":
                tokens.append(_Token(ch, ch))
                i += 1
                continue
            if ch in "\"'":
                quote = ch
                i += 1
                value = []
                while i < len(text) and text[i] != quote:
                    if text[i] == "\\" and i + 1 < len(text):
                        i += 1
                    value.append(text[i])
                    i += 1
                if i >= len(text):
                    raise InvalidMarker(text)
                i += 1
                tokens.append(_Token("STRING", "".join(value)))
                continue
            two = text[i : i + 2]
            if two in {"==", "!=", "<=", ">="}:
                tokens.append(_Token("OP", two))
                i += 2
                continue
            if ch in "<>":
                tokens.append(_Token("OP", ch))
                i += 1
                continue
            if re.match(r"[A-Za-z_]", ch):
                start = i
                i += 1
                while i < len(text) and re.match(r"[A-Za-z0-9_]", text[i]):
                    i += 1
                word = text[start:i].lower()
                tokens.append(_Token("WORD", word))
                continue
            raise InvalidMarker(text)
        tokens.append(_Token("EOF", ""))
        return tokens

    def parse(self) -> Any:
        expr = self.parse_or()
        if self.peek().kind != "EOF":
            raise InvalidMarker("trailing marker input")
        return expr

    def peek(self) -> _Token:
        return self.tokens[self.pos]

    def pop(self) -> _Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def accept_word(self, value: str) -> bool:
        if self.peek().kind == "WORD" and self.peek().value == value:
            self.pop()
            return True
        return False

    def parse_or(self) -> Any:
        node = self.parse_and()
        while self.accept_word("or"):
            node = _Bool("or", node, self.parse_and())
        return node

    def parse_and(self) -> Any:
        node = self.parse_atom()
        while self.accept_word("and"):
            node = _Bool("and", node, self.parse_atom())
        return node

    def parse_atom(self) -> Any:
        if self.peek().kind == "(":
            self.pop()
            node = self.parse_or()
            if self.peek().kind != ")":
                raise InvalidMarker("missing close paren")
            self.pop()
            return node
        left = self.parse_operand()
        op = self.parse_operator()
        right = self.parse_operand()
        return _Compare(left, op, right)

    def parse_operand(self) -> _Operand:
        token = self.pop()
        if token.kind == "STRING":
            return _Operand("literal", token.value)
        if token.kind == "WORD":
            if token.value not in _MARKER_VARIABLES:
                raise InvalidMarker(token.value)
            return _Operand("var", token.value)
        raise InvalidMarker(token.value)

    def parse_operator(self) -> str:
        token = self.pop()
        if token.kind == "OP":
            return token.value
        if token.kind == "WORD" and token.value == "in":
            return "in"
        if token.kind == "WORD" and token.value == "not":
            if self.accept_word("in"):
                return "not in"
        raise InvalidMarker(token.value)


class Marker:
    def __init__(self, text: str):
        if not isinstance(text, str) or not text.strip():
            raise InvalidMarker("marker must be a non-empty string")
        self._ast = _MarkerParser(text).parse()
        self._text = self._format(self._ast)

    def __str__(self) -> str:
        return self._text

    def __repr__(self) -> str:
        return f"<Marker('{self}')>"

    def evaluate(
        self,
        environment: dict[str, str] | None = None,
        requested_extras: set[str] | list[str] | tuple[str, ...] | None = None,
    ) -> bool:
        env = default_environment() if environment is None else dict(environment)
        for key, value in env.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise UndefinedEnvironmentName(str(key))

        if self._uses_extra(self._ast):
            extras = [_normalize_extra(e) for e in (requested_extras or [])]
            if not extras:
                extras = [""]
            return any(self._eval(self._ast, env, extra) for extra in extras)
        return self._eval(self._ast, env, "")

    def _operand_value(self, operand: _Operand, env: dict[str, str], extra: str) -> str:
        if operand.kind == "literal":
            return operand.value
        if operand.value == "extra":
            return extra
        if operand.value not in env:
            raise UndefinedEnvironmentName(operand.value)
        return env[operand.value]

    def _eval(self, node: Any, env: dict[str, str], extra: str) -> bool:
        if isinstance(node, _Bool):
            if node.op == "and":
                return self._eval(node.left, env, extra) and self._eval(node.right, env, extra)
            return self._eval(node.left, env, extra) or self._eval(node.right, env, extra)

        left = self._operand_value(node.left, env, extra)
        right = self._operand_value(node.right, env, extra)
        if (
            node.left.kind == "var"
            and node.left.value == "extra"
            or node.right.kind == "var"
            and node.right.value == "extra"
        ):
            left = _normalize_marker_extra_value(left)
            right = _normalize_marker_extra_value(right)

        op = node.op
        if op in {"in", "not in"}:
            result = left in right
            return result if op == "in" else not result

        left_version = right_version = None
        try:
            left_version = Version(left)
            right_version = Version(right)
        except InvalidVersion:
            pass

        if left_version is not None and right_version is not None:
            left_value: Any = left_version
            right_value: Any = right_version
        else:
            left_value = left
            right_value = right

        if op == "==":
            return left_value == right_value
        if op == "!=":
            return left_value != right_value
        if op == "<":
            return left_value < right_value
        if op == "<=":
            return left_value <= right_value
        if op == ">":
            return left_value > right_value
        if op == ">=":
            return left_value >= right_value
        raise AssertionError(op)

    def _uses_extra(self, node: Any) -> bool:
        if isinstance(node, _Bool):
            return self._uses_extra(node.left) or self._uses_extra(node.right)
        return (
            node.left.kind == "var"
            and node.left.value == "extra"
            or node.right.kind == "var"
            and node.right.value == "extra"
        )

    def _format(self, node: Any, parent: str | None = None) -> str:
        if isinstance(node, _Bool):
            left = self._format(node.left, node.op)
            right = self._format(node.right, node.op)
            text = f"{left} {node.op} {right}"
            if parent == "and" and node.op == "or":
                return f"({text})"
            return text
        return f"{self._format_operand(node.left, node)} {node.op} {self._format_operand(node.right, node)}"

    def _format_operand(self, operand: _Operand, compare: _Compare) -> str:
        if operand.kind == "var":
            return operand.value
        value = operand.value
        if (
            compare.left.kind == "var"
            and compare.left.value == "extra"
            or compare.right.kind == "var"
            and compare.right.value == "extra"
        ):
            try:
                value = _normalize_extra(value)
            except InvalidRequirement:
                value = value.replace("_", "-").lower()
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _normalize_extra(value: str) -> str:
    try:
        return _normalize_name(value)
    except ValueError as exc:
        raise InvalidRequirement(value) from exc


def _normalize_marker_extra_value(value: str) -> str:
    if not value:
        return ""
    try:
        return _normalize_name(value)
    except ValueError:
        return value.replace("_", "-").lower()


def _split_outside(text: str, char: str) -> tuple[str, str | None]:
    quote = None
    bracket_depth = 0
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
            elif ch == "\\":
                continue
        elif ch in "\"'":
            quote = ch
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif ch == char and bracket_depth == 0:
            return text[:i], text[i + 1 :]
    return text, None


class Requirement:
    def __init__(self, text: str):
        if not isinstance(text, str):
            raise InvalidRequirement("requirement must be a string")
        try:
            self.name, self.extras, self.specifier, self.url, self.marker = self._parse(text)
        except Exception as exc:
            raise InvalidRequirement(text) from exc

    def _parse(self, text: str) -> tuple[str, set[str], SpecifierSet, str | None, Marker | None]:
        body, marker_text = _split_outside(text.strip(), ";")
        marker = Marker(marker_text.strip()) if marker_text is not None and marker_text.strip() else None
        if marker_text is not None and not marker_text.strip():
            raise InvalidRequirement(text)

        match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]|[A-Za-z0-9])", body)
        if not match:
            raise InvalidRequirement(text)
        raw_name = match.group(1)
        try:
            name = _normalize_name(raw_name)
        except ValueError as exc:
            raise InvalidRequirement(text) from exc
        pos = match.end()
        rest = body[pos:].strip()

        extras: set[str] = set()
        if rest.startswith("["):
            close = rest.find("]")
            if close == -1:
                raise InvalidRequirement(text)
            extras_text = rest[1:close].strip()
            if not extras_text:
                raise InvalidRequirement(text)
            for raw_extra in extras_text.split(","):
                raw_extra = raw_extra.strip()
                try:
                    extras.add(_normalize_name(raw_extra))
                except ValueError as exc:
                    raise InvalidRequirement(text) from exc
            rest = rest[close + 1 :].strip()

        url = None
        specifier_text = ""
        if rest.startswith("@"):
            url = rest[1:].strip()
            if not url:
                raise InvalidRequirement(text)
        elif rest:
            specifier_text = rest
        specifier = SpecifierSet(specifier_text)
        return name, extras, specifier, url, marker

    def __str__(self) -> str:
        text = self.name
        if self.extras:
            text += "[" + ",".join(sorted(self.extras)) + "]"
        if self.url is not None:
            text += " @ " + self.url
        elif str(self.specifier):
            text += str(self.specifier)
        if self.marker is not None:
            text += " ; " + str(self.marker)
        return text

    def __repr__(self) -> str:
        return f"<Requirement('{self}')>"


def default_environment() -> dict[str, str]:
    implementation_version = ".".join(str(p) for p in sys.implementation.version[:3])
    if sys.implementation.version.releaselevel != "final":
        implementation_version += sys.implementation.version.releaselevel[0] + str(
            sys.implementation.version.serial
        )
    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_full_version": platform.python_version(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": sys.implementation.name,
        "implementation_version": implementation_version,
    }


def is_requirement_satisfied(
    requirement: str | Requirement,
    installed_version: str | Version,
    environment: dict[str, str] | None = None,
    requested_extras: set[str] | list[str] | tuple[str, ...] | None = None,
    prereleases: bool | None = None,
) -> bool:
    req = requirement if isinstance(requirement, Requirement) else Requirement(requirement)
    if req.marker is not None and not req.marker.evaluate(environment, requested_extras):
        return True
    return req.specifier.contains(installed_version, prereleases=prereleases)


__all__ = [
    "Version",
    "InvalidVersion",
    "SpecifierSet",
    "InvalidSpecifier",
    "Requirement",
    "InvalidRequirement",
    "Marker",
    "InvalidMarker",
    "UndefinedEnvironmentName",
    "default_environment",
    "is_requirement_satisfied",
]
