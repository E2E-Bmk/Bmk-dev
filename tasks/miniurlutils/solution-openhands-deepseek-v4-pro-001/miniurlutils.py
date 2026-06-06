"""MiniURLUtils - A dependency-free Python module for URL parsing, editing, and serialization."""

import ipaddress
import re
from collections import OrderedDict
from urllib.parse import quote, unquote


class URLParseError(ValueError):
    """Raised when a URL string cannot be parsed."""


# ---------------------------------------------------------------------------
#  parse_url
# ---------------------------------------------------------------------------

_URL_RE = re.compile(
    r"""
    ^
    (?:(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*):)?
    (?P<netloc_sep>//)?
    (?P<authority>[^/?#]*)?
    (?P<path>[^?#]*)
    (?:\?(?P<query>[^#]*))?
    (?:\#(?P<fragment>.*))?
    $
    """,
    re.VERBOSE,
)

_DEFAULT_PORTS: dict[str, int] = {"http": 80, "https": 443, "ftp": 21}


def _detect_family(host: str) -> str | None:
    """Return 'ipv4', 'ipv6', or None for a given host string."""
    if not host:
        return None
    try:
        ip = ipaddress.ip_address(host)
        return "ipv6" if ip.version == 6 else "ipv4"
    except ValueError:
        return None


def parse_url(text: str) -> dict:
    """Parse *text* into a dictionary describing the URL.

    Returns keys: scheme, _netloc_sep, authority, path, query, fragment,
    username, password, family, host, port.

    Raises URLParseError for malformed input.
    """
    text = text.strip()
    m = _URL_RE.match(text)
    if m is None:
        raise URLParseError(f"Cannot parse URL: {text!r}")

    scheme: str | None = m.group("scheme") or None
    netloc_sep: str | None = m.group("netloc_sep") or None
    authority: str | None = m.group("authority") or None
    path: str = m.group("path") or ""
    query: str = m.group("query") or ""
    fragment: str = m.group("fragment") or ""

    # If // is present but scheme is not, treat as scheme-relative
    # If nothing indicates authority, fold the "authority" into path
    if authority is not None and not netloc_sep and not scheme:
        # e.g. "foo/bar?q=1"  – no scheme, no //, so "foo" is path
        path = (authority + path) if path else authority
        authority = None
    elif authority is not None and netloc_sep and authority == "" and not path:
        # "http://" – empty authority, no path
        pass

    # Parse authority into userinfo / host / port
    username: str | None = None
    password: str | None = None
    host: str | None = None
    port: int | None = None
    family: str | None = None

    if authority is not None:
        userinfo: str | None = None
        hostpart: str

        if "@" in authority:
            userinfo, hostpart = authority.rsplit("@", 1)
            if ":" in userinfo:
                username, password = userinfo.split(":", 1)
            else:
                username = userinfo
        else:
            hostpart = authority

        if hostpart:
            # IPv6 address in brackets: [::1]:port or [::1]
            if hostpart.startswith("["):
                bracket_end = hostpart.find("]")
                if bracket_end == -1:
                    raise URLParseError(f"Unclosed IPv6 bracket in URL: {text!r}")
                host = hostpart[1:bracket_end]
                remainder = hostpart[bracket_end + 1 :]
                if remainder:
                    if remainder.startswith(":"):
                        port_str = remainder[1:]
                        if port_str:
                            try:
                                port = int(port_str)
                            except ValueError:
                                raise URLParseError(
                                    f"Invalid port after IPv6 address: {text!r}"
                                )
                    else:
                        raise URLParseError(
                            f"Unexpected characters after IPv6 address: {text!r}"
                        )
            else:
                # IPv4 / hostname, optionally with port
                if ":" in hostpart:
                    h, p_s = hostpart.rsplit(":", 1)
                    try:
                        port = int(p_s)
                        host = h
                    except ValueError:
                        raise URLParseError(f"Invalid port number in URL: {text!r}")
                else:
                    host = hostpart

        # Detect IP address family
        if host:
            family = _detect_family(host)

    # Empty-string fallbacks for optional text fields
    return {
        "scheme": scheme or "",
        "_netloc_sep": netloc_sep or "",
        "authority": authority or "",
        "path": path,
        "query": query,
        "fragment": fragment,
        "username": username or "",
        "password": password or "",
        "family": family or "",
        "host": host or "",
        "port": port,
    }


# ---------------------------------------------------------------------------
#  Path helpers
# ---------------------------------------------------------------------------


def _resolve_dot_segments(path: str) -> str:
    """Remove single-dot and double-dot segments from *path* per RFC 3986 §5.2.4."""
    if not path:
        return path
    segments: list[str] = []
    for seg in path.split("/"):
        if seg == "." or seg == "":
            continue
        if seg == "..":
            if segments:
                segments.pop()
        else:
            segments.append(seg)
    # Preserve leading / trailing slash
    result = "/".join(segments)
    if path.startswith("/"):
        result = "/" + result
    if path.endswith("/") and not result.endswith("/"):
        result += "/"
    elif path.endswith("/.") or path.endswith("/.."):
        result += "/"
    return result


def _normalize_percent_encoding(path: str) -> str:
    """Decode percent-encoded characters that are safe to represent literally in a path."""

    def _replacer(m: re.Match[str]) -> str:
        try:
            raw = m.group(0)
            decoded = unquote(raw)
            # Re-encode but keep unreserved chars literal
            return quote(decoded, safe="/:@!$&'()*+,;=-._~")
        except Exception:
            return raw

    return re.sub(r"%[0-9A-Fa-f]{2}", _replacer, path)


# ---------------------------------------------------------------------------
#  QueryParamDict
# ---------------------------------------------------------------------------


class QueryParamDict:
    """Ordered query-parameter container that supports repeated keys."""

    def __init__(self, pairs: list[tuple[str, str | None]] | None = None) -> None:
        self._pairs: list[tuple[str, str | None]] = list(pairs) if pairs else []

    # -- constructors -------------------------------------------------------

    @classmethod
    def from_text(cls, query_string: str) -> "QueryParamDict":
        """Parse a percent-encoded query string into a QueryParamDict."""
        inst = cls()
        if not query_string:
            return inst
        for part in query_string.split("&"):
            if not part:
                continue
            if "=" in part:
                key, raw_val = part.split("=", 1)
                key = unquote(key.replace("+", " "))
                val: str | None = unquote(raw_val.replace("+", " "))
            else:
                key = unquote(part.replace("+", " "))
                val = None
            inst._pairs.append((key, val))
        return inst

    # -- dict-like mutation -------------------------------------------------

    def add(self, key: str, value: str | None) -> None:
        """Append another value for *key* (preserves existing values)."""
        self._pairs.append((key, value))

    def __setitem__(self, key: str, value: str | None) -> None:
        """Replace all values for *key* with a single *value*."""
        new_pairs: list[tuple[str, str | None]] = []
        replaced = False
        for k, v in self._pairs:
            if k == key:
                if not replaced:
                    new_pairs.append((key, value))
                    replaced = True
            else:
                new_pairs.append((k, v))
        if not replaced:
            new_pairs.append((key, value))
        self._pairs = new_pairs

    def __getitem__(self, key: str) -> str | None:
        """Return the *first* value for *key*, or raise KeyError."""
        for k, v in self._pairs:
            if k == key:
                return v
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return any(k == key for k, _ in self._pairs)

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return the first value for *key*, or *default*."""
        for k, v in self._pairs:
            if k == key:
                return v
        return default

    def getlist(self, key: str) -> list[str | None]:
        """Return all values for *key*."""
        return [v for k, v in self._pairs if k == key]

    def __delitem__(self, key: str) -> None:
        """Remove all occurrences of *key*."""
        self._pairs = [(k, v) for k, v in self._pairs if k != key]

    # -- iteration ----------------------------------------------------------

    def items(self, multi: bool = False) -> list[tuple[str, str | None]]:
        """Return key/value pairs.

        If *multi* is True, repeated keys appear multiple times.
        If *multi* is False (default), only the first value per key is returned.
        """
        if multi:
            return list(self._pairs)
        seen: set[str] = set()
        result: list[tuple[str, str | None]] = []
        for k, v in self._pairs:
            if k not in seen:
                seen.add(k)
                result.append((k, v))
        return result

    def keys(self) -> list[str]:
        """Return keys in insertion order (first occurrence only)."""
        seen: set[str] = set()
        result: list[str] = []
        for k, _ in self._pairs:
            if k not in seen:
                seen.add(k)
                result.append(k)
        return result

    def values(self) -> list[str | None]:
        """Return values in insertion order (first occurrence per key only)."""
        seen: set[str] = set()
        result: list[str | None] = []
        for k, v in self._pairs:
            if k not in seen:
                seen.add(k)
                result.append(v)
        return result

    def __iter__(self):
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self.keys())

    def __bool__(self) -> bool:
        return len(self._pairs) > 0

    # -- serialization ------------------------------------------------------

    def to_text(self) -> str:
        """Serialize to a percent-encoded query string."""
        parts: list[str] = []
        for k, v in self._pairs:
            key = quote(str(k), safe="")
            if v is None:
                parts.append(key)
            else:
                parts.append(f"{key}={quote(str(v), safe='')}")
        return "&".join(parts)

    def __str__(self) -> str:
        return self.to_text()

    def __repr__(self) -> str:
        return f"QueryParamDict({self._pairs!r})"

    # -- copy / sort --------------------------------------------------------

    def copy(self) -> "QueryParamDict":
        """Return a shallow copy."""
        return QueryParamDict(list(self._pairs))

    def sorted(self) -> "QueryParamDict":
        """Return a new QueryParamDict with keys sorted alphabetically.

        Within the same key, original insertion order is preserved.
        """
        return QueryParamDict(sorted(self._pairs, key=lambda p: p[0]))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QueryParamDict):
            return NotImplemented
        return self._pairs == other._pairs


# ---------------------------------------------------------------------------
#  URL
# ---------------------------------------------------------------------------


class URL:
    """Mutable URL object built from a URL string."""

    def __init__(self, text: str) -> None:
        parsed = parse_url(text)
        self.scheme: str = parsed["scheme"]
        self.host: str = parsed["host"]
        self._path: str = parsed["path"]
        self.query_params: QueryParamDict = QueryParamDict.from_text(parsed["query"])
        self.fragment: str = parsed["fragment"]
        self.username: str = parsed["username"]
        self.password: str = parsed["password"]
        self.port: int | None = parsed["port"]
        self._netloc_sep: str = parsed["_netloc_sep"]
        self._family: str = parsed["family"]

    # -- path access --------------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, value: str) -> None:
        self._path = value

    @property
    def path_parts(self) -> list[str]:
        """Return the path split on '/' into segments."""
        p = self._path
        if not p or p == "/":
            return []
        # Remove leading slash, split
        if p.startswith("/"):
            p = p[1:]
        return p.split("/")

    @path_parts.setter
    def path_parts(self, parts: list[str]) -> None:
        if not parts:
            self._path = ""
        else:
            self._path = "/" + "/".join(str(s) for s in parts)

    @property
    def uses_netloc(self) -> bool:
        return bool(self._netloc_sep)

    # -- construction -------------------------------------------------------

    @classmethod
    def from_parts(
        cls,
        scheme: str | None = None,
        host: str | None = None,
        path: str | None = None,
        path_parts: list[str] | None = None,
        query_params: QueryParamDict | None = None,
        fragment: str | None = None,
        username: str | None = None,
        password: str | None = None,
        port: int | None = None,
    ) -> "URL":
        """Build a URL from individual components."""
        url = cls.__new__(cls)
        url.scheme = scheme or ""
        url.host = host or ""
        url.username = username or ""
        url.password = password or ""
        url.port = port
        url.fragment = fragment or ""
        url.query_params = query_params.copy() if query_params else QueryParamDict()

        if path_parts is not None:
            filtered = [str(p) for p in path_parts if p]
            url._path = ("/" + "/".join(filtered)) if filtered else ""
        elif path is not None:
            url._path = path
        else:
            url._path = ""

        url._netloc_sep = "//" if host else ""
        url._family = _detect_family(url.host) if url.host else ""
        return url

    # -- authority ----------------------------------------------------------

    def get_authority(self) -> str:
        """Return the serialized authority portion (userinfo@host:port)."""
        parts: list[str] = []
        if self.username:
            if self.password:
                parts.append(f"{self.username}:{self.password}@")
            else:
                parts.append(f"{self.username}@")
        if self.host:
            if self._family == "ipv6":
                parts.append(f"[{self.host}]")
            else:
                parts.append(self.host)
        if self.port is not None:
            parts.append(f":{self.port}")
        return "".join(parts)

    # -- serialization ------------------------------------------------------

    def to_text(self) -> str:
        """Serialize the URL to a string."""
        result: list[str] = []
        if self.scheme:
            result.append(self.scheme)
            result.append(":")
        if self._netloc_sep:
            result.append(self._netloc_sep)
            result.append(self.get_authority())
        result.append(self._path)
        qs = self.query_params.to_text()
        if qs:
            result.append("?")
            result.append(qs)
        if self.fragment:
            result.append("#")
            result.append(self.fragment)
        return "".join(result)

    def __str__(self) -> str:
        return self.to_text()

    def __repr__(self) -> str:
        return f"URL({self.to_text()!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, URL):
            return NotImplemented
        return self.to_text() == other.to_text()

    # -- navigation ---------------------------------------------------------

    def navigate(self, relative: str) -> "URL":
        """Resolve a relative (or absolute) URL reference against this URL.

        Returns a new ``URL`` instance.
        """
        ref = parse_url(relative)

        new = URL.__new__(URL)

        # Absolute URL (has scheme) – replace entirely
        if ref["scheme"]:
            new.scheme = ref["scheme"]
            new.host = ref["host"]
            new._path = ref["path"]
            new.query_params = QueryParamDict.from_text(ref["query"])
            new.fragment = ref["fragment"]
            new.username = ref["username"]
            new.password = ref["password"]
            new.port = ref["port"]
            new._netloc_sep = ref["_netloc_sep"]
            new._family = ref["family"]
            return new

        # Network-path reference (has //)
        if ref["_netloc_sep"]:
            new.scheme = self.scheme
            new.host = ref["host"]
            new._path = ref["path"]
            new.query_params = QueryParamDict.from_text(ref["query"])
            new.fragment = ref["fragment"]
            new.username = ref["username"]
            new.password = ref["password"]
            new.port = ref["port"]
            new._netloc_sep = ref["_netloc_sep"]
            new._family = ref["family"]
            return new

        # Same-document reference or relative path
        new.scheme = self.scheme
        new.host = self.host
        new.username = self.username
        new.password = self.password
        new.port = self.port
        new._netloc_sep = self._netloc_sep
        new._family = self._family
        new.fragment = ref["fragment"]

        ref_path: str = ref["path"]
        if not ref_path:
            # No path change – use base path
            new._path = self._path
            if ref["query"]:
                new.query_params = QueryParamDict.from_text(ref["query"])
            else:
                # Per RFC 3986 §5.3: preserve base query when ref has none
                new.query_params = self.query_params.copy()
        else:
            if ref_path.startswith("/"):
                new._path = ref_path
            else:
                # Merge relative path with base path
                base = self._path
                if not base:
                    base = "/"
                # Remove last segment of base path (everything after last /)
                base_dir = base[: base.rfind("/") + 1] if "/" in base else ""
                new._path = base_dir + ref_path
            new._path = _resolve_dot_segments(new._path)
            new.query_params = QueryParamDict.from_text(ref["query"])

        return new

    # -- normalization ------------------------------------------------------

    def normalize(self) -> None:
        """Normalize the URL in place.

        Lowercases scheme and host, removes default ports, resolves ``.``
        and ``..`` path segments, and normalizes common percent-encoded
        path characters.
        """
        if self.scheme:
            self.scheme = self.scheme.lower()
        if self.host:
            self.host = self.host.lower()
            self._family = _detect_family(self.host)
        # Remove default port
        if self.scheme and self.port is not None:
            default = _DEFAULT_PORTS.get(self.scheme)
            if default is not None and self.port == default:
                self.port = None
        # Resolve dot segments
        self._path = _resolve_dot_segments(self._path)
        # Normalize percent-encoding
        self._path = _normalize_percent_encoding(self._path)


# ---------------------------------------------------------------------------
#  find_all_links
# ---------------------------------------------------------------------------

# Matches http:// and https:// URLs in plain text.
# Stops before common sentence-ending punctuation and avoids email addresses.
_LINK_RE = re.compile(
    r"""
    (?<![@\w.])                                      # not part of an email
    (?P<url>
        https?://
        [^\s<>"'{}\[\]()|\\^`\u201c\u201d\u2018\u2019]*
        [^\s<>"'{}\[\]()|\\^`\u201c\u201d\u2018\u2019.,;:!?]
    )
    """,
    re.VERBOSE | re.UNICODE,
)


def find_all_links(text: str) -> list[URL]:
    """Return a list of ``URL`` objects for every http/https link found in *text*.

    Email addresses are intentionally excluded.
    """
    results: list[URL] = []
    for m in _LINK_RE.finditer(text):
        raw = m.group("url")
        try:
            results.append(URL(raw))
        except URLParseError:
            continue
    return results
