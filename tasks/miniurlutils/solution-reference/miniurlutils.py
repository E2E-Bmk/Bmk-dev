"""A tiny dependency-free URL parsing and editing toolkit."""

from __future__ import annotations

import ipaddress
import posixpath
import re
import socket
from collections.abc import Iterable, Iterator, MutableMapping
from typing import Any
from urllib.parse import quote, unquote, unquote_plus, urljoin


class URLParseError(ValueError):
    """Raised when URL text cannot be parsed meaningfully."""


_SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*):(.*)$", re.S)
_LINK_RE = re.compile(r"\bhttps?://[^\s<>()\"']+", re.I)
_TRAILING_LINK_PUNCT = ".,;:!?"


def _split_url(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        raise URLParseError("URL must be text")
    if any(ch.isspace() for ch in text):
        raise URLParseError("URL contains control whitespace")

    rest = text
    scheme = None
    match = _SCHEME_RE.match(rest)
    if match:
        scheme = match.group(1)
        rest = match.group(2)

    fragment = ""
    if "#" in rest:
        rest, fragment = rest.split("#", 1)

    query = ""
    if "?" in rest:
        rest, query = rest.split("?", 1)

    netloc_sep = None
    authority = ""
    path = rest
    if rest.startswith("//"):
        netloc_sep = "//"
        after_sep = rest[2:]
        slash = after_sep.find("/")
        if slash == -1:
            authority = after_sep
            path = ""
        else:
            authority = after_sep[:slash]
            path = after_sep[slash:]
    elif scheme and _scheme_uses_authority(scheme):
        # http:example.com is still a path-only form; do not invent an authority.
        path = rest

    return {
        "scheme": scheme,
        "_netloc_sep": netloc_sep,
        "authority": authority,
        "path": path,
        "query": query,
        "fragment": fragment,
    }


def _scheme_uses_authority(scheme: str) -> bool:
    return scheme.lower() in {"http", "https", "ftp", "ws", "wss", "file"}


def _parse_authority(authority: str) -> dict[str, Any]:
    username = None
    password = None
    host = None
    port = None
    family = None

    if not authority:
        return {
            "username": username,
            "password": password,
            "family": family,
            "host": host,
            "port": port,
        }

    if any(ch in authority for ch in "/?#"):
        raise URLParseError("invalid authority")

    hostport = authority
    if "@" in hostport:
        userinfo, hostport = hostport.rsplit("@", 1)
        if ":" in userinfo:
            username, password = userinfo.split(":", 1)
        else:
            username = userinfo
        username = unquote(username)
        if password is not None:
            password = unquote(password)

    if hostport.startswith("["):
        close = hostport.find("]")
        if close == -1:
            raise URLParseError("unterminated IPv6 host")
        host = hostport[1:close]
        remainder = hostport[close + 1 :]
        if remainder:
            if not remainder.startswith(":"):
                raise URLParseError("invalid host suffix")
            port_text = remainder[1:]
            port = _parse_port(port_text)
        try:
            ipaddress.IPv6Address(host)
            family = socket.AddressFamily.AF_INET6
        except ValueError:
            raise URLParseError("invalid IPv6 host")
    else:
        if hostport.count(":") > 1:
            # Bare IPv6 literals are ambiguous in URLs and should be bracketed.
            raise URLParseError("IPv6 host must be bracketed")
        if ":" in hostport:
            host, port_text = hostport.rsplit(":", 1)
            port = _parse_port(port_text)
        else:
            host = hostport
        if not host and port is not None:
            raise URLParseError("missing host")
        if host:
            try:
                ip = ipaddress.ip_address(host)
                family = socket.AddressFamily.AF_INET if ip.version == 4 else socket.AddressFamily.AF_INET6
            except ValueError:
                family = None

    return {
        "username": username,
        "password": password,
        "family": family,
        "host": host,
        "port": port,
    }


def _parse_port(port_text: str) -> int | None:
    if port_text == "":
        return None
    if not port_text.isdigit():
        raise URLParseError("port must be numeric")
    port = int(port_text)
    if not 0 <= port <= 65535:
        raise URLParseError("port out of range")
    return port


def parse_url(text: str) -> dict[str, Any]:
    """Parse URL text into a dictionary of core components."""

    parsed = _split_url(text)
    parsed.update(_parse_authority(parsed["authority"]))
    return parsed


class QueryParamDict(MutableMapping[str, str | None]):
    """Ordered query-parameter mapping that preserves repeated keys."""

    def __init__(self, pairs: Iterable[tuple[Any, Any]] | dict[Any, Any] | None = None):
        self._pairs: list[tuple[str, str | None]] = []
        if pairs is None:
            return
        if isinstance(pairs, dict):
            pairs = pairs.items()
        for key, value in pairs:
            self.add(key, value)

    @classmethod
    def from_text(cls, query_string: str) -> "QueryParamDict":
        if query_string.startswith("?"):
            query_string = query_string[1:]
        q = cls()
        if query_string == "":
            return q
        for part in query_string.split("&"):
            if "=" in part:
                key, value = part.split("=", 1)
                q.add(unquote_plus(key), unquote_plus(value))
            else:
                q.add(unquote_plus(part), None)
        return q

    def add(self, key: Any, value: Any) -> None:
        self._pairs.append((str(key), None if value is None else str(value)))

    def getlist(self, key: str) -> list[str | None]:
        key = str(key)
        return [value for item_key, value in self._pairs if item_key == key]

    def items(self, multi: bool = True):  # type: ignore[override]
        if multi:
            return iter(list(self._pairs))
        return iter([(key, self[key]) for key in self])

    def to_text(self) -> str:
        parts = []
        for key, value in self._pairs:
            encoded_key = quote(key, safe="")
            if value is None:
                parts.append(encoded_key)
            else:
                parts.append(f"{encoded_key}={quote(value, safe='')}")
        return "&".join(parts)

    def sorted(self) -> "QueryParamDict":
        return QueryParamDict(sorted(self._pairs, key=lambda item: (item[0], "" if item[1] is None else item[1])))

    def copy(self) -> "QueryParamDict":
        return QueryParamDict(self._pairs)

    def __getitem__(self, key: str) -> str | None:
        key = str(key)
        for item_key, value in reversed(self._pairs):
            if item_key == key:
                return value
        raise KeyError(key)

    def __setitem__(self, key: str, value: str | None) -> None:
        key = str(key)
        self._pairs = [(item_key, item_value) for item_key, item_value in self._pairs if item_key != key]
        self.add(key, value)

    def __delitem__(self, key: str) -> None:
        key = str(key)
        original_len = len(self._pairs)
        self._pairs = [(item_key, item_value) for item_key, item_value in self._pairs if item_key != key]
        if len(self._pairs) == original_len:
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        seen = set()
        for key, _value in self._pairs:
            if key not in seen:
                seen.add(key)
                yield key

    def __len__(self) -> int:
        return len(set(key for key, _value in self._pairs))

    def __contains__(self, key: object) -> bool:
        return any(item_key == key for item_key, _value in self._pairs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._pairs!r})"


def _split_path_parts(path: str) -> list[str]:
    if path == "":
        return []
    parts = path.split("/")
    if parts and parts[0] == "":
        parts = parts[1:]
    return [unquote(part) for part in parts]


def _join_path_parts(parts: Iterable[Any], leading_slash: bool = True) -> str:
    encoded = [quote(str(part), safe=":@!$&'()*+,;=-._~") for part in parts]
    path = "/".join(encoded)
    if leading_slash:
        return "/" + path if path else "/"
    return path


def _has_authority(parsed: dict[str, Any]) -> bool:
    return bool(parsed["_netloc_sep"] or parsed["authority"])


class URL:
    """Mutable URL object with parsing, editing, and serialization helpers."""

    def __init__(self, text: str):
        parsed = parse_url(text)
        self.scheme: str | None = parsed["scheme"]
        self.username: str | None = parsed["username"]
        self.password: str | None = parsed["password"]
        self.host: str = parsed["host"]
        self.port: int | None = parsed["port"]
        self.path: str = parsed["path"]
        self.query_params = QueryParamDict.from_text(parsed["query"])
        self.fragment: str = parsed["fragment"]
        self.uses_netloc: bool = _has_authority(parsed)
        self._query_had_marker: bool = "?" in text
        self._leading_path_slash: bool = self.path.startswith("/")

    @property
    def path_parts(self) -> list[str]:
        return _split_path_parts(self.path)

    @path_parts.setter
    def path_parts(self, parts: Iterable[Any]) -> None:
        self.path = _join_path_parts(parts, leading_slash=self.uses_netloc or self._leading_path_slash)
        self._leading_path_slash = self.path.startswith("/")

    @classmethod
    def from_parts(
        cls,
        scheme: str = "",
        host: str = "",
        path: str | None = None,
        path_parts: Iterable[Any] | None = None,
        query_params: QueryParamDict | Iterable[tuple[Any, Any]] | dict[Any, Any] | None = None,
        fragment: str = "",
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
        uses_netloc: bool | None = None,
    ) -> "URL":
        obj = cls.__new__(cls)
        obj.scheme = scheme or ""
        obj.username = username
        obj.password = password
        obj.host = host or ""
        obj.port = port
        if path_parts is not None:
            leading = uses_netloc if uses_netloc is not None else bool(host)
            obj.path = _join_path_parts(path_parts, leading_slash=bool(leading))
        else:
            obj.path = path or ""
        if isinstance(query_params, QueryParamDict):
            obj.query_params = query_params.copy()
        else:
            obj.query_params = QueryParamDict(query_params)
        obj.fragment = fragment or ""
        obj.uses_netloc = bool(uses_netloc) if uses_netloc is not None else bool(host or username or port is not None)
        obj._query_had_marker = bool(query_params)
        obj._leading_path_slash = obj.path.startswith("/")
        return obj

    def get_authority(self) -> str:
        host = self.host or ""
        if ":" in host and not (host.startswith("[") and host.endswith("]")):
            host = f"[{host}]"
        authority = host
        if self.port is not None:
            authority += f":{self.port}"
        return authority

    def to_text(self) -> str:
        text = ""
        if self.scheme:
            text += f"{self.scheme}:"
        if self.uses_netloc:
            userinfo = ""
            if self.username is not None:
                userinfo += quote(self.username, safe="")
                if self.password is not None:
                    userinfo += ":" + quote(self.password, safe="")
                userinfo += "@"
            text += "//" + userinfo + self.get_authority()
            if self.path and not self.path.startswith("/"):
                text += "/"
        text += self.path
        query_text = self.query_params.to_text()
        if query_text or self._query_had_marker:
            text += "?" + query_text
        if self.fragment:
            text += "#" + self.fragment
        return text

    def navigate(self, relative: str) -> "URL":
        return URL(urljoin(self.to_text(), relative))

    def normalize(self) -> None:
        self.scheme = self.scheme.lower()
        self.host = self.host.lower()
        if (self.scheme.lower(), self.port) in {("http", 80), ("https", 443), ("ftp", 21)}:
            self.port = None
        self.path = _normalize_path(self.path, force_leading=self.uses_netloc)
        self._leading_path_slash = self.path.startswith("/")

    def __str__(self) -> str:
        return self.to_text()

    def __repr__(self) -> str:
        return f"URL({self.to_text()!r})"


def _normalize_path(path: str, force_leading: bool = False) -> str:
    if path == "":
        return "/" if force_leading else ""
    decoded_parts = [unquote(part) for part in path.split("/")]
    decoded_path = "/".join(decoded_parts)
    trailing = decoded_path.endswith("/") and decoded_path not in {"", "/"}
    leading = decoded_path.startswith("/") or force_leading
    normalized = posixpath.normpath(decoded_path)
    if normalized == ".":
        normalized = ""
    if leading and not normalized.startswith("/"):
        normalized = "/" + normalized
    if trailing and normalized and not normalized.endswith("/"):
        normalized += "/"
    safe = "/:@!$&'()*+,;=-._~"
    return quote(normalized, safe=safe)


def find_all_links(text: str) -> list[URL]:
    """Return http/https URLs found in plain text."""

    links: list[URL] = []
    for match in _LINK_RE.finditer(text):
        candidate = match.group(0)
        while candidate and candidate[-1] in _TRAILING_LINK_PUNCT:
            candidate = candidate[:-1]
        while candidate.endswith(")") and candidate.count("(") < candidate.count(")"):
            candidate = candidate[:-1]
        if not candidate:
            continue
        try:
            links.append(URL(candidate))
        except ValueError:
            continue
    return links


__all__ = ["URL", "QueryParamDict", "parse_url", "find_all_links", "URLParseError"]
