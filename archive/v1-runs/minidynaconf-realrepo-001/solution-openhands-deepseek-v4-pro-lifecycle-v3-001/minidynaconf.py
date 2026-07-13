"""minidynaconf - A dependency-free Python module for layered application configuration.

Inspired by Dynaconf's configuration-management model. Uses only the Python
standard library.
"""

from __future__ import annotations

import configparser
import copy
import io
import json
import os
import re
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SettingsError(Exception):
    """Base error for settings-related failures."""


class ValidationError(SettingsError):
    """A validator rejected a setting value."""

    def __init__(self, message: str, key: str | None = None) -> None:
        super().__init__(message)
        self.key = key


# ---------------------------------------------------------------------------
# Type-casting engine
# ---------------------------------------------------------------------------

_TRUE_SPELLINGS: set[str] = {
    "true", "True", "TRUE", "yes", "Yes", "YES",
    "on", "On", "ON", "1",
}
_FALSE_SPELLINGS: set[str] = {
    "false", "False", "FALSE", "no", "No", "NO",
    "off", "Off", "OFF", "0",
}
_NULL_SPELLINGS: set[str] = {
    "none", "None", "NONE", "null", "Null", "NULL",
    "nil", "Nil", "NIL",
}

_EXPLICIT_CAST_MAP: dict[str, Callable[[str], Any]] = {}


def _register_explicit_cast(token: str, func: Callable[[str], Any]) -> None:
    _EXPLICIT_CAST_MAP[token] = func


_register_explicit_cast("@int", lambda v: int(v.strip()))
_register_explicit_cast("@float", lambda v: float(v.strip()))
_register_explicit_cast("@bool", lambda v: _cast_bool_strict(v.strip()))
_register_explicit_cast("@json", lambda v: json.loads(v.strip()))
_register_explicit_cast("@none", lambda v: None)
_register_explicit_cast("@str", lambda v: v.strip())


def _cast_bool_strict(value: str) -> bool:
    lower = value.lower()
    if lower in _TRUE_SPELLINGS:
        return True
    if lower in _FALSE_SPELLINGS:
        return False
    msg = f"Cannot cast {value!r} to bool"
    raise SettingsError(msg)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def cast_value(value: Any) -> Any:
    """Cast a *text* value to its richest Python type.

    Programmatic (non-string) values pass through unchanged unless an explicit
    cast token is detected.
    """
    if not isinstance(value, str):
        return value

    s = value.strip()

    # Explicit cast tokens
    if s.startswith("@"):
        for token, caster in _EXPLICIT_CAST_MAP.items():
            if s.startswith(token + " ") or s == token:
                rest = s[len(token):].strip()
                try:
                    return caster(rest)
                except Exception as exc:
                    msg = f"Explicit cast {token} failed for {value!r}: {exc}"
                    raise SettingsError(msg) from exc
        # starts with @ but no known token – keep as string
        return s

    # Quote stripping
    unquoted = _strip_quotes(s)

    # Boolean auto-detection
    if unquoted in _TRUE_SPELLINGS:
        return True
    if unquoted in _FALSE_SPELLINGS:
        return False

    # Null / None
    if unquoted in _NULL_SPELLINGS:
        return None

    # Integer
    try:
        return int(unquoted)
    except ValueError:
        pass

    # Float
    try:
        return float(unquoted)
    except ValueError:
        pass

    # JSON-style list/dict
    stripped = unquoted.strip()
    if (stripped.startswith("[") and stripped.endswith("]")) or \
       (stripped.startswith("{") and stripped.endswith("}")):
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

    return unquoted


def cast_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Recursively cast every string leaf in *mapping* and canonicalize keys
    to uppercase.
    """
    result: dict[str, Any] = {}
    for key, val in mapping.items():
        canon_key = key.upper()
        if isinstance(val, dict):
            result[canon_key] = cast_mapping(val)
        elif isinstance(val, list):
            result[canon_key] = [
                cast_mapping(v) if isinstance(v, dict) else
                cast_list_items(v) if isinstance(v, list) else
                cast_value(v)
                for v in val
            ]
        else:
            result[canon_key] = cast_value(val)
    return result


def cast_list_items(items: list[Any]) -> list[Any]:
    return [
        cast_mapping(v) if isinstance(v, dict) else
        cast_list_items(v) if isinstance(v, list) else
        cast_value(v)
        for v in items
    ]


def _maybe_explicit_cast(value: Any) -> Any:
    """Apply explicit-cast-token rules to a programmatic value.

    Only strings starting with ``@`` are inspected.  If the token matches a
    registered explicit cast the cast is applied; otherwise the value is
    returned unchanged.  Non-string values pass through unmodified.
    """
    if not isinstance(value, str) or not value.startswith("@"):
        return value
    for token in _EXPLICIT_CAST_MAP:
        if value.startswith(token + " ") or value == token:
            return cast_value(value)
    return value


def _canonicalize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    """Recursively canonicalize keys to uppercase without type-casting values.
    Used for programmatic defaults that should preserve Python types.
    """
    result: dict[str, Any] = {}
    for key, val in mapping.items():
        canon_key = key.upper()
        if isinstance(val, dict):
            result[canon_key] = _canonicalize_mapping(val)
        elif isinstance(val, list):
            result[canon_key] = [
                _canonicalize_mapping(v) if isinstance(v, dict) else
                _canonicalize_list(v) if isinstance(v, list) else
                v
                for v in val
            ]
        else:
            result[canon_key] = val
    return result


def _canonicalize_list(items: list[Any]) -> list[Any]:
    return [
        _canonicalize_mapping(v) if isinstance(v, dict) else
        _canonicalize_list(v) if isinstance(v, list) else
        v
        for v in items
    ]


# ---------------------------------------------------------------------------
# Deep merge helpers
# ---------------------------------------------------------------------------

def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> None:
    """Recursively merge *overlay* into *base* (mutates *base*)."""
    for key, val in overlay.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(val, dict)
        ):
            deep_merge(base[key], val)
        else:
            base[key] = copy.deepcopy(val)


def deep_copy_dict(d: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(d)


# ---------------------------------------------------------------------------
# File-format parsers
# ---------------------------------------------------------------------------

def parse_json(content: str) -> dict[str, Any]:
    """Parse JSON content, return dict (empty for non-object roots)."""
    data = json.loads(content)
    if isinstance(data, dict):
        return data
    return {}


def parse_ini(content: str) -> dict[str, Any]:
    """Parse INI content via configparser.  Sections become nested dicts."""
    cp = configparser.ConfigParser()
    cp.read_string(content)
    result: dict[str, Any] = {}
    for section in cp.sections():
        result[section] = {}
        for key, val in cp.items(section):
            result[section][key] = val
    # Also include DEFAULT section values at top level when no section
    if cp.defaults():
        for key, val in cp.defaults().items():
            if key not in result:
                result[key] = val
    return result


# ---------------------------------------------------------------------------
# TOML subset parser
# ---------------------------------------------------------------------------

_TOML_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_TOML_BARE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_TOML_DOTTED_KEY_RE = re.compile(r'^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+$')


def _is_toml_bare_key(s: str) -> bool:
    return bool(_TOML_BARE_KEY_RE.match(s))


def _parse_toml_value(raw: str) -> Any:
    """Parse a single TOML value from its text representation."""
    s = raw.strip()

    # String literals
    if s.startswith('"""') or s.startswith("'''"):
        # Multi-line basic/literal string
        quote = s[:3]
        end = s.find(quote, 3)
        if end == -1:
            return s[3:]
        content = s[3:end]
        if quote == '"""':
            return _unescape_toml_basic(content)
        return content
    if s.startswith('"'):
        end = _find_string_end(s, 1, '"')
        return _unescape_toml_basic(s[1:end])
    if s.startswith("'"):
        end = _find_string_end(s, 1, "'")
        return s[1:end]

    # Boolean
    if s == "true":
        return True
    if s == "false":
        return False

    # Special float values
    if s in ("inf", "+inf", "-inf", "nan", "+nan", "-nan"):
        return float(s)

    # Integer / Float
    if _looks_like_number(s):
        if "." in s or "e" in s.lower():
            return float(s)
        try:
            return int(s)
        except ValueError:
            return float(s)

    # Inline array
    if s.startswith("["):
        return _parse_toml_array(s)

    # Inline table
    if s.startswith("{"):
        return _parse_toml_inline_table(s)

    return s


def _find_string_end(s: str, start: int, quote: str) -> int:
    i = start
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == quote:
            return i
        i += 1
    return len(s)


def _unescape_toml_basic(s: str) -> str:
    result = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt in ('"', "\\", "/", "b", "f", "n", "r", "t"):
                escapes = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}
                result.append(escapes.get(nxt, nxt))
                i += 2
                continue
            if nxt == "u" and i + 5 < len(s):
                try:
                    result.append(chr(int(s[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except (ValueError, OverflowError):
                    pass
        result.append(s[i])
        i += 1
    return "".join(result)


def _looks_like_number(s: str) -> bool:
    if not s:
        return False
    if s[0] in ("+", "-"):
        s = s[1:]
    if not s:
        return False
    if s.startswith("0x") or s.startswith("0o") or s.startswith("0b"):
        return True
    return bool(re.match(r"^[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?$", s))


def _parse_toml_array(raw: str) -> list[Any]:
    s = raw.strip()
    if not (s.startswith("[") and s.endswith("]")):
        return [s]
    inner = s[1:-1].strip()
    if not inner:
        return []
    items = _split_toml_list(inner)
    return [_parse_toml_value(item) for item in items]


def _parse_toml_inline_table(raw: str) -> dict[str, Any]:
    s = raw.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return {}
    inner = s[1:-1].strip()
    if not inner:
        return {}
    pairs = _split_toml_list(inner)
    result: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        result[k.strip()] = _parse_toml_value(v.strip())
    return result


def _split_toml_list(s: str) -> list[str]:
    """Split comma-separated items respecting nested brackets/braces/quotes."""
    items: list[str] = []
    current: list[str] = []
    depth = 0
    in_string: str | None = None
    i = 0
    while i < len(s):
        ch = s[i]
        if in_string:
            current.append(ch)
            if ch == in_string and (i == 0 or s[i - 1] != "\\"):
                in_string = None
        elif ch == '"':
            current.append(ch)
            in_string = '"'
        elif ch == "'":
            current.append(ch)
            in_string = "'"
        elif ch in ("[", "{"):
            depth += 1
            current.append(ch)
        elif ch in ("]", "}"):
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    if current:
        items.append("".join(current).strip())
    return items


def parse_toml(content: str) -> dict[str, Any]:
    """Parse a TOML subset into a nested dict."""
    result: dict[str, Any] = {}
    current_table: dict[str, Any] = result
    table_path: list[str] = []
    array_of_tables: dict[str, list[dict[str, Any]]] = {}

    lines = content.splitlines()

    for line in lines:
        stripped = line.strip()

        # Skip blanks and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Table header: [section] or [section.subsection]
        if stripped.startswith("[") and not stripped.startswith("[["):
            header = stripped[1:]
            if header.endswith("]"):
                header = header[:-1]
            header = header.strip()
            if header:
                # Check for dotted keys in header
                parts = [p.strip() for p in header.split(".")]
                if not any(p.startswith('"') or p.startswith("'") for p in parts):
                    table_path = parts
                else:
                    # Quoted keys in header
                    table_path = [_parse_toml_bare_key(p.strip('"').strip("'")) for p in parts]
                current_table = result
                for part in table_path:
                    if part not in current_table:
                        current_table[part] = {}
                    elif not isinstance(current_table[part], dict):
                        current_table[part] = {}
                    current_table = current_table[part]

        # Array of tables: [[array]]
        elif stripped.startswith("[[") and stripped.endswith("]]"):
            header = stripped[2:-2].strip()
            parts = [p.strip() for p in header.split(".")]
            table_path = parts
            # Navigate to parent
            parent = result
            for part in table_path[:-1]:
                if part not in parent:
                    parent[part] = {}
                parent = parent[part]
            last = table_path[-1]
            if last not in parent:
                parent[last] = []
            new_entry: dict[str, Any] = {}
            parent[last].append(new_entry)
            current_table = new_entry

        # Key = Value
        elif "=" in stripped:
            key_raw, _, val_raw = stripped.partition("=")
            key = key_raw.strip()
            val = _parse_toml_value(val_raw.strip())

            # Handle dotted keys
            key_parts = key.split(".")
            target = current_table
            for kp in key_parts[:-1]:
                kp = kp.strip()
                if kp not in target:
                    target[kp] = {}
                elif not isinstance(target[kp], dict):
                    target[kp] = {}
                target = target[kp]
            final_key = key_parts[-1].strip()
            target[final_key] = val

    return result


# ---------------------------------------------------------------------------
# YAML subset parser
# ---------------------------------------------------------------------------

def _parse_yaml_value(raw: str) -> Any:
    """Parse a single YAML scalar / inline-collection value."""
    s = raw.strip()

    if not s:
        return ""

    # null
    if s.lower() in ("null", "~", "none"):
        return None

    # Boolean
    if s.lower() in ("true", "yes", "on"):
        return True
    if s.lower() in ("false", "no", "off"):
        return False

    # Inline list: [a, b, c]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_value(item) for item in _split_yaml_list(inner)]

    # Inline dict: {k: v, ...}
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        if not inner:
            return {}
        result: dict[str, Any] = {}
        for pair in _split_yaml_list(inner):
            if ":" in pair:
                k, v = pair.split(":", 1)
                result[k.strip().strip("'\"")] = _parse_yaml_value(v.strip())
        return result

    # Quoted strings (single or double)
    if (s.startswith('"') and s.endswith('"')) or \
       (s.startswith("'") and s.endswith("'")):
        return s[1:-1]

    # Integer
    try:
        return int(s)
    except ValueError:
        pass

    # Float
    try:
        return float(s)
    except ValueError:
        pass

    return s


def _split_yaml_list(s: str) -> list[str]:
    """Split comma-separated YAML list items respecting nesting."""
    items: list[str] = []
    current: list[str] = []
    depth = 0
    in_sq = False
    in_dq = False
    for ch in s:
        if in_dq:
            current.append(ch)
            if ch == '"':
                in_dq = False
        elif in_sq:
            current.append(ch)
            if ch == "'":
                in_sq = False
        elif ch == '"':
            in_dq = True
            current.append(ch)
        elif ch == "'":
            in_sq = True
            current.append(ch)
        elif ch in ("[", "{"):
            depth += 1
            current.append(ch)
        elif ch in ("]", "}"):
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        items.append("".join(current).strip())
    return items


def parse_yaml(content: str) -> dict[str, Any]:
    """Parse a practical YAML subset: mappings, nested indented maps,
    inline lists, scalars.  Flow sequences (block list with ``-``) are also
    supported at any nesting level.
    """
    lines = content.splitlines()
    return _parse_yaml_block(lines, 0, -1)[0]


def _count_indent(line: str) -> int:
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            n += 2  # treat tabs as 2 spaces
        else:
            break
    return n


def _parse_yaml_block(
    lines: list[str], start: int, base_indent: int,
) -> tuple[dict[str, Any], int]:
    """Parse a YAML mapping block.  Returns (result_dict, next_line_index)."""
    result: dict[str, Any] = {}
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty / comment lines are skipped
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = _count_indent(line)

        # Finished this block when indentation returns to parent level
        if indent <= base_indent and base_indent >= 0:
            break

        # Block list item: "- value"
        if stripped.startswith("- ") and (":" not in stripped or
            stripped.index(":") > stripped.index("- ") if ":" in stripped else True):
            # We're inside a mapping, but this is a list item.
            # This shouldn't normally happen in a mapping context, but if it
            # does we need to handle it. Actually, in YAML, "- key: value" is
            # a list of mappings. Let's handle "- key: value" pattern.
            list_key = _find_parent_list_key(result)
            if list_key is not None and stripped.startswith("- "):
                item_content = stripped[2:].strip()
                if ":" in item_content:
                    # "- key: value" - list of single-key mappings
                    k, v = item_content.split(":", 1)
                    sub: dict[str, Any] = {k.strip(): _parse_yaml_value(v.strip())}
                    result[list_key].append(sub)
                else:
                    result[list_key].append(_parse_yaml_value(item_content))
                i += 1
                continue
            i += 1
            continue

        # Key: Value line
        if ":" in stripped:
            key_raw, _, value_raw = stripped.partition(":")
            key = key_raw.strip().strip("'\"")
            value_raw = value_raw.strip()

            if value_raw in ("", "|", ">"):
                # Block scalar or nested mapping / list
                if value_raw == "|" or value_raw == ">":
                    # Literal/folded block scalar - collect indented lines
                    scalar_lines: list[str] = []
                    i += 1
                    while i < len(lines):
                        nl = lines[i]
                        if nl.strip() and not nl.strip().startswith("#"):
                            nindent = _count_indent(nl)
                            if nindent > indent:
                                scalar_lines.append(nl.strip())
                                i += 1
                                continue
                        break
                    result[key] = "\n".join(scalar_lines)
                else:
                    # Nested block
                    i += 1
                    # Check if next line is a list item
                    if i < len(lines):
                        next_line = lines[i]
                        nstripped = next_line.strip()
                        nindent = _count_indent(next_line)
                        if nstripped.startswith("- ") and nindent > indent:
                            # Block list
                            items: list[Any] = []
                            while i < len(lines):
                                nl = lines[i]
                                nstripped = nl.strip()
                                nindent = _count_indent(nl)
                                if nindent <= indent:
                                    break
                                if nstripped.startswith("- "):
                                    item_text = nstripped[2:].strip()
                                    if ":" in item_text:
                                        # "- key: value"
                                        ik, _, iv = item_text.partition(":")
                                        item: dict[str, Any] = {ik.strip(): _parse_yaml_value(iv.strip())}
                                        items.append(item)
                                    else:
                                        items.append(_parse_yaml_value(item_text))
                                    i += 1
                                else:
                                    break
                            result[key] = items
                        else:
                            nested, ni = _parse_yaml_block(lines, i, indent)
                            result[key] = nested
                            i = ni
                    else:
                        result[key] = {}
                continue
            else:
                result[key] = _parse_yaml_value(value_raw)

        i += 1

    return result, i


def _find_parent_list_key(result: dict[str, Any]) -> str | None:
    for key, val in result.items():
        if isinstance(val, list):
            return key
    return None


# ---------------------------------------------------------------------------
# Python-file loader
# ---------------------------------------------------------------------------

def parse_python_file(path: str | Path) -> dict[str, Any]:
    """Execute a Python file in an isolated namespace and collect public
    uppercase variables."""
    namespace: dict[str, Any] = {}
    with open(path, encoding="utf-8") as fh:
        code = compile(fh.read(), str(path), "exec")
    exec(code, namespace)
    result: dict[str, Any] = {}
    for k, v in namespace.items():
        if k.isupper() and not k.startswith("_"):
            result[k] = v
    return result


# ---------------------------------------------------------------------------
# Dotenv parser
# ---------------------------------------------------------------------------

def parse_dotenv(content: str) -> dict[str, Any]:
    """Parse .env content (KEY=VALUE pairs, optional quoting, comments)."""
    result: dict[str, Any] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, val = stripped.partition("=")
        key = key.strip()
        val = val.strip()
        # Strip optional surrounding quotes
        val = _strip_quotes(val)
        # Strip inline comments (after value)
        # Simple approach: don't strip, already handled
        result[key] = val
    return result


# ---------------------------------------------------------------------------
# File-format detection and generic loader
# ---------------------------------------------------------------------------

_EXT_MAP: dict[str, Callable[[str], dict[str, Any]]] = {
    ".json": parse_json,
    ".toml": parse_toml,
    ".ini": parse_ini,
    ".yaml": parse_yaml,
    ".yml": parse_yaml,
}


def _detect_format(path: str | Path) -> Callable:
    suffix = Path(path).suffix.lower()
    parser = _EXT_MAP.get(suffix)
    if parser is not None:
        return parser
    msg = f"Unsupported file format: {path}"
    raise SettingsError(msg)


def load_file_raw(path: str | Path) -> dict[str, Any]:
    """Load and parse a settings file, return raw dict before casting."""
    ppath = Path(path)
    suffix = ppath.suffix.lower()

    if suffix == ".py":
        return parse_python_file(ppath)

    with open(ppath, encoding="utf-8") as fh:
        content = fh.read()

    parser = _EXT_MAP.get(suffix)
    if parser is None:
        msg = f"Unsupported file format: {path}"
        raise SettingsError(msg)

    try:
        return parser(content)
    except Exception as exc:
        msg = f"Failed to parse {path}: {exc}"
        raise SettingsError(msg) from exc


# ---------------------------------------------------------------------------
# Internal canonical configuration tree
# ---------------------------------------------------------------------------

_TOMBSTONE = object()  # sentinel for deleted keys


class _ConfigTree:
    """Case-insensitive, dot-addressable nested mapping.

    Internally stores canonical uppercase keys at every level.
    """

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = {}
        if data:
            self.merge(data)

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _canonical(key: str) -> str:
        return key.upper()

    def _navigate(self, dotted_key: str) -> tuple[dict[str, Any], str]:
        """Walk *dotted_key* returning ``(container, final_canonical_key)``,
        creating intermediate dicts as needed.
        """
        parts = dotted_key.split(".")
        current = self._data
        for part in parts[:-1]:
            canon = self._canonical(part)
            if canon not in current or not isinstance(current[canon], dict):
                current[canon] = {}
            current = current[canon]
        return current, self._canonical(parts[-1])

    def _navigate_existing(
        self, dotted_key: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Like ``_navigate`` but does NOT create missing containers."""
        parts = dotted_key.split(".")
        current = self._data
        for part in parts[:-1]:
            canon = self._canonical(part)
            if canon not in current or not isinstance(current[canon], dict):
                return None, None
            current = current[canon]
        return current, self._canonical(parts[-1])

    # -- public mutation --------------------------------------------------

    def get(self, dotted_key: str, default: Any = None) -> Any:
        container, key = self._navigate_existing(dotted_key)
        if container is None or key not in container:
            return default
        val = container[key]
        if val is _TOMBSTONE:
            return default
        return val

    def set(self, dotted_key: str, value: Any) -> None:
        """Set a value.  Nested dicts merge recursively."""
        parts = dotted_key.split(".")
        if isinstance(value, dict):
            # Recursive merge
            current = self._data
            for part in parts[:-1]:
                canon = self._canonical(part)
                if canon not in current or not isinstance(current[canon], dict):
                    current[canon] = {}
                current = current[canon]
            final = self._canonical(parts[-1])
            if final in current and isinstance(current[final], dict):
                deep_merge(current[final], cast_mapping(value))
            else:
                current[final] = cast_mapping(value)
        else:
            container, key = self._navigate(dotted_key)
            container[key] = value

    def exists(self, dotted_key: str) -> bool:
        container, key = self._navigate_existing(dotted_key)
        if container is None:
            return False
        return key in container and container[key] is not _TOMBSTONE

    def delete(self, dotted_key: str) -> None:
        """Mark a key as deleted (tombstone).  The tombstone filters the key
        from all public views but does not physically remove it from durable
        layers (so reload can restore it).
        """
        container, key = self._navigate(dotted_key)
        container[key] = _TOMBSTONE

    def merge(self, mapping: dict[str, Any]) -> None:
        """Merge *mapping* recursively (mutates this tree)."""
        for key, val in mapping.items():
            self.set(key, val)

    def as_dict(self) -> dict[str, Any]:
        """Deep copy with uppercase canonical keys, tombstones removed."""
        return _export_dict(self._data)

    def items(self):
        """Yield (dotted_key, value) for non-tombstone entries."""
        for key, val in self._data.items():
            yield from self._items_recurse(key, val, [])

    def _items_recurse(self, key: str, val: Any, path: list[str]):
        if val is _TOMBSTONE:
            return
        full_path = path + [key]
        if isinstance(val, dict) and not _is_tombstone_dict(val):
            for sub_key, sub_val in val.items():
                yield from self._items_recurse(sub_key, sub_val, full_path)
        else:
            yield (".".join(full_path), val)


def _is_tombstone_dict(d: dict[str, Any]) -> bool:
    """Return True if this dict is actually a tombstone marker."""
    return len(d) == 1 and next(iter(d.values())) is _TOMBSTONE


def _export_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Deep copy with tombstones removed, keys uppercased."""
    result: dict[str, Any] = {}
    for key, val in data.items():
        if val is _TOMBSTONE:
            continue
        canon = key.upper()
        if isinstance(val, dict):
            exported = _export_dict(val)
            if exported or (not _is_tombstone_dict(val)):
                result[canon] = exported
        elif isinstance(val, list):
            result[canon] = [
                _export_dict(v) if isinstance(v, dict) else
                [_export_dict(x) if isinstance(x, dict) else x for x in v]
                if isinstance(v, list) else v
                for v in val
            ]
        else:
            result[canon] = val
    return result


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class Validator:
    """A validation rule for one logical configuration key."""

    def __init__(
        self,
        name: str,
        *,
        required: bool = False,
        default: Any = None,
        is_type_of: type | tuple[type, ...] | None = None,
        eq: Any = None,
        ne: Any = None,
        gt: Any = None,
        gte: Any = None,
        lt: Any = None,
        lte: Any = None,
        condition: Callable[[Any, Any], bool] | None = None,
        messages: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.required = required
        self.default = default
        self.is_type_of = is_type_of
        self.eq = eq
        self.ne = ne
        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte
        self.condition = condition
        self.messages = messages or {}

    def validate(self, settings: MiniDynaconf) -> None:
        """Run this validator against *settings*.  Raises ``ValidationError``
        on failure."""
        key = self.name
        exists = settings.exists(key)

        if not exists and self.default is not None:
            settings._set_raw(key, self.default)

        if not settings.exists(key):
            if self.required:
                msg = self.messages.get("required", f"{key} is required")
                raise ValidationError(msg, key=key)
            return

        value = settings.get(key)

        if self.is_type_of is not None:
            if not _type_check(value, self.is_type_of):
                msg = self.messages.get(
                    "is_type_of",
                    f"{key} must be {self.is_type_of}, got {type(value).__name__}",
                )
                raise ValidationError(msg, key=key)

        for op_name, expected in [
            ("eq", self.eq),
            ("ne", self.ne),
            ("gt", self.gt),
            ("gte", self.gte),
            ("lt", self.lt),
            ("lte", self.lte),
        ]:
            if expected is not None:
                ok = _compare(op_name, value, expected)
                if not ok:
                    msg = self.messages.get(
                        op_name,
                        f"{key} {op_name} {expected!r} failed (value={value!r})",
                    )
                    raise ValidationError(msg, key=key)

        if self.condition is not None:
            try:
                cond_result = self.condition(value, settings)
            except Exception as exc:
                msg = self.messages.get(
                    "condition",
                    f"{key} condition raised: {exc}",
                )
                raise ValidationError(msg, key=key) from exc
            if not cond_result:
                msg = self.messages.get(
                    "condition",
                    f"{key} failed condition check",
                )
                raise ValidationError(msg, key=key)


def _type_check(value: Any, expected: type | tuple[type, ...]) -> bool:
    if expected is None:
        return value is None
    if expected is bool:
        return isinstance(value, bool)
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


def _compare(op: str, a: Any, b: Any) -> bool:
    try:
        if op == "eq":
            return a == b
        if op == "ne":
            return a != b
        if op == "gt":
            return a > b
        if op == "gte":
            return a >= b
        if op == "lt":
            return a < b
        if op == "lte":
            return a <= b
    except TypeError:
        return False
    return False


# ---------------------------------------------------------------------------
# MiniDynaconf — main settings class
# ---------------------------------------------------------------------------

class MiniDynaconf:
    """Layered application-settings object.

    Full constructor signature::

        MiniDynaconf(
            settings_files=None,
            defaults=None,
            envvar_prefix="APP",
            environments=False,
            env=None,
            secrets_files=None,
            validators=None,
            load_dotenv=False,
        )
    """

    # Sentinel for "no value provided" (distinguishes from explicit None)
    _NOTSET: Any = object()

    def __init__(
        self,
        settings_files: str | Path | list[str | Path] | None = None,
        defaults: dict[str, Any] | None = None,
        envvar_prefix: str = "APP",
        environments: bool = False,
        env: str | None = None,
        secrets_files: str | Path | list[str | Path] | None = None,
        validators: list[Validator] | None = None,
        load_dotenv: bool = False,
    ) -> None:
        # --- stored configuration ----------------------------------------
        self._settings_files = self._normalize_path_list(settings_files)
        self._defaults = defaults or {}
        self._envvar_prefix = envvar_prefix
        self._environments = environments
        self._env = env
        self._secrets_files = self._normalize_path_list(secrets_files)
        self._validators: list[Validator] = list(validators or [])
        self._load_dotenv = load_dotenv

        # --- lifecycle state ---------------------------------------------
        self._lifecycle_files: list[tuple[Path, str | None]] = []
        self._lifecycle_env_files: list[Path] = []
        self._runtime_overrides: dict[str, Any] = {}
        self._tombstones: set[str] = set()
        self._validator_defaults: dict[str, Any] = {}

        # Build initial effective tree
        self._effective: _ConfigTree | None = None
        self._build_effective()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_path_list(
        value: str | Path | list[str | Path] | None,
    ) -> list[Path]:
        if value is None:
            return []
        if isinstance(value, (str, Path)):
            return [Path(value)]
        return [Path(p) for p in value]

    def _snapshot(self) -> dict[str, Any]:
        """Return a deep copy of internal state for atomic rollback."""
        return {
            "effective": copy.deepcopy(self._effective._data)
            if self._effective else {},
            "lifecycle_files": list(self._lifecycle_files),
            "lifecycle_env_files": list(self._lifecycle_env_files),
            "runtime_overrides": copy.deepcopy(self._runtime_overrides),
            "tombstones": set(self._tombstones),
            "validator_defaults": copy.deepcopy(self._validator_defaults),
        }

    def _restore(self, snap: dict[str, Any]) -> None:
        self._effective = _ConfigTree(snap["effective"])
        self._lifecycle_files = snap["lifecycle_files"]
        self._lifecycle_env_files = snap["lifecycle_env_files"]
        self._runtime_overrides = snap["runtime_overrides"]
        self._tombstones = snap["tombstones"]
        self._validator_defaults = snap["validator_defaults"]

    # ------------------------------------------------------------------
    # Effective-tree construction
    # ------------------------------------------------------------------

    def _build_effective(self) -> None:
        """Build the effective tree from all layers."""
        tree = _ConfigTree()

        # 1. Defaults (programmatic — preserve Python types)
        if self._defaults:
            # Deep copy and canonicalize keys but do NOT cast values
            tree.merge(_canonicalize_mapping(copy.deepcopy(self._defaults)))

        # 2. Settings files
        for path in self._settings_files:
            self._load_file_into(tree, path)

        # 3. Environment variables
        self._load_env_into(tree)

        # 4. Initial dotenv (load_dotenv=True)
        if self._load_dotenv:
            dotenv_path = Path(".env")
            if dotenv_path.exists():
                self._load_dotenv_into(tree, dotenv_path)
                if dotenv_path not in self._lifecycle_env_files:
                    self._lifecycle_env_files.append(dotenv_path)

        # 5. Secrets files
        for path in self._secrets_files:
            self._load_file_into(tree, path)

        # 6. Lifecycle files (durable imports)
        for path, env in self._lifecycle_files:
            if env is not None:
                old_env = self._env
                old_environments = self._environments
                self._env = env
                self._environments = True
                self._load_file_into(tree, path)
                self._env = old_env
                self._environments = old_environments
            else:
                self._load_file_into(tree, path)

        # 7. Lifecycle env files
        for path in self._lifecycle_env_files:
            if path not in [
                p for p in [Path(".env")] if p.exists() and self._load_dotenv
            ]:
                self._load_dotenv_into(tree, path)

        self._effective = tree

        # 8. Validators (including defaults)
        self._apply_validator_defaults()

        # 9. Runtime overrides
        for key, val in self._runtime_overrides.items():
            self._effective.set(key, val)

        # 10. Tombstones
        for key in self._tombstones:
            self._effective.delete(key)

    def _load_file_into(self, tree: _ConfigTree, path: Path) -> None:
        """Load a single settings file into *tree* (when path exists)."""
        if not path.exists():
            return
        try:
            raw = load_file_raw(path)
        except SettingsError:
            raise
        except Exception as exc:
            msg = f"Failed to load {path}: {exc}"
            raise SettingsError(msg) from exc

        data = self._resolve_environments(raw)
        tree.merge(cast_mapping(data))

    def _resolve_environments(self, raw: dict[str, Any]) -> dict[str, Any]:
        """If environments are enabled, extract default + active env."""
        if not self._environments:
            return raw

        # Check if raw looks like an environments structure:
        # keys are all strings that look like environment names
        active_env = self._resolve_active_env()
        env_keys = {k for k in raw if isinstance(raw[k], dict)}

        # Heuristic: if most top-level keys contain dict values, treat as envs
        dict_count = sum(1 for k in raw if isinstance(raw[k], dict))
        if dict_count == 0 or dict_count < len(raw) * 0.5:
            return raw

        result: dict[str, Any] = {}
        if "default" in raw and isinstance(raw["default"], dict):
            result = copy.deepcopy(raw["default"])
        if active_env in raw and isinstance(raw[active_env], dict):
            deep_merge(result, raw[active_env])
        return result

    def _resolve_active_env(self) -> str:
        if self._env is not None:
            return self._env
        return os.environ.get("ENV_FOR_DYNACONF", "default")

    def _load_env_into(self, tree: _ConfigTree) -> None:
        """Load matching environment variables into *tree*."""
        prefix = self._envvar_prefix.upper() + "_"
        env_data: dict[str, Any] = {}
        for key, val in os.environ.items():
            if key.upper().startswith(prefix):
                logical = key[len(prefix):]
                # Double underscore → dot for nested keys
                logical = logical.replace("__", ".")
                if logical in env_data:
                    continue  # first one wins
                env_data[logical] = cast_value(val)
        tree.merge(env_data)

    def _load_dotenv_into(self, tree: _ConfigTree, path: Path) -> None:
        """Load a .env file into *tree*."""
        if not path.exists():
            return
        try:
            with open(path, encoding="utf-8") as fh:
                raw = parse_dotenv(fh.read())
        except Exception as exc:
            msg = f"Failed to load dotenv {path}: {exc}"
            raise SettingsError(msg) from exc

        prefix = self._envvar_prefix.upper() + "_"
        env_data: dict[str, Any] = {}
        for key, val in raw.items():
            if key.upper().startswith(prefix):
                logical = key[len(prefix):].replace("__", ".")
            else:
                logical = key.replace("__", ".")
            if logical in env_data:
                continue
            env_data[logical] = cast_value(val)
        tree.merge(env_data)

    def _apply_validator_defaults(self) -> None:
        """Apply validator defaults for missing keys."""
        if self._effective is None:
            return
        for validator in self._validators:
            key = validator.name
            if not self._effective.exists(key) and validator.default is not None:
                self._effective.set(key, validator.default)
                self._validator_defaults[key] = validator.default

    # ------------------------------------------------------------------
    # Public access API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None, cast: type | None = None) -> Any:
        """Return the value for *key* (dot-notation supported).

        If *cast* is given the returned value is cast without mutating
        stored state.
        """
        if self._effective is None:
            return default
        val = self._effective.get(key, default)
        if cast is not None and val is not default:
            try:
                return cast(val)
            except (ValueError, TypeError):
                return val
        return val

    def set(self, key: str, value: Any, *, validate: bool = False) -> None:
        """Set a runtime override for *key*."""
        snap = self._snapshot() if validate else None
        try:
            self._runtime_overrides[key] = _maybe_explicit_cast(value)
            self._tombstones.discard(key)
            self._build_effective()
            if validate:
                self.validate()
        except Exception:
            if snap is not None:
                self._restore(snap)
            raise

    def update(self, mapping: dict[str, Any], *, validate: bool = False) -> None:
        """Apply multiple runtime overrides at once."""
        snap = self._snapshot() if validate else None
        try:
            for key, val in mapping.items():
                self._runtime_overrides[key] = _maybe_explicit_cast(val)
                self._tombstones.discard(key)
            self._build_effective()
            if validate:
                self.validate()
        except Exception:
            if snap is not None:
                self._restore(snap)
            raise

    def exists(self, key: str) -> bool:
        """Return True if *key* is present in settings."""
        if self._effective is None:
            return False
        return self._effective.exists(key)

    def delete(self, key: str) -> None:
        """Mark *key* as deleted (runtime tombstone)."""
        self._tombstones.add(key)
        if key in self._runtime_overrides:
            del self._runtime_overrides[key]
        self._build_effective()

    def import_dict(
        self, mapping: dict[str, Any], *, validate: bool = True, replace: bool = False,
    ) -> None:
        """Import a plain dictionary as runtime overlay."""
        snap = self._snapshot() if validate else None
        try:
            if replace:
                self._runtime_overrides.clear()
            for key, val in mapping.items():
                self._runtime_overrides[key] = _maybe_explicit_cast(val)
                self._tombstones.discard(key)
            self._build_effective()
            if validate:
                self.validate()
        except Exception:
            if snap is not None:
                self._restore(snap)
            raise

    def as_dict(self) -> dict[str, Any]:
        """Return a deep-copy dict with uppercase canonical keys."""
        if self._effective is None:
            return {}
        return self._effective.as_dict()

    def export(self, path: str | Path | None = None) -> dict[str, Any]:
        """Return a deep-copy dict view.  When *path* is given, also write
        as JSON to that path.
        """
        data = self.as_dict()
        if path is not None:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        return data

    # ------------------------------------------------------------------
    # Lifecycle operations
    # ------------------------------------------------------------------

    def load_file(
        self, path: str | Path, *, env: str | None = None, silent: bool = True,
    ) -> None:
        """Load one additional settings file (durable import)."""
        ppath = Path(path)
        if not ppath.exists():
            if silent:
                return
            msg = f"File not found: {path}"
            raise SettingsError(msg)

        snap = self._snapshot()
        try:
            self._lifecycle_files.append((ppath, env))
            self._build_effective()
        except Exception:
            self._restore(snap)
            raise

    def load_env_file(self, path: str | Path) -> None:
        """Load a .env file (durable import)."""
        ppath = Path(path)
        snap = self._snapshot()
        try:
            if ppath not in self._lifecycle_env_files:
                self._lifecycle_env_files.append(ppath)
            self._build_effective()
        except Exception:
            self._restore(snap)
            raise

    def reload(self) -> None:
        """Rebuild settings from durable sources, discarding runtime overlays
        and deletion tombstones.
        """
        self._runtime_overrides.clear()
        self._tombstones.clear()
        self._validator_defaults.clear()
        self._build_effective()

    def configure(self, **kwargs: Any) -> None:
        """Replace loader configuration and rebuild from scratch.

        Accepted kwargs mirror constructor parameters:
        ``settings_files``, ``defaults``, ``envvar_prefix``, ``environments``,
        ``env``, ``secrets_files``, ``validators``, ``load_dotenv``.
        """
        snap = self._snapshot()
        try:
            if "settings_files" in kwargs:
                self._settings_files = self._normalize_path_list(
                    kwargs["settings_files"]
                )
            if "defaults" in kwargs:
                self._defaults = kwargs["defaults"]
            if "envvar_prefix" in kwargs:
                self._envvar_prefix = kwargs["envvar_prefix"]
            if "environments" in kwargs:
                self._environments = kwargs["environments"]
            if "env" in kwargs:
                self._env = kwargs["env"]
            if "secrets_files" in kwargs:
                self._secrets_files = self._normalize_path_list(
                    kwargs["secrets_files"]
                )
            if "validators" in kwargs:
                self._validators = list(kwargs["validators"] or [])
            if "load_dotenv" in kwargs:
                self._load_dotenv = kwargs["load_dotenv"]

            # Clear lifecycle state
            self._lifecycle_files.clear()
            self._lifecycle_env_files.clear()
            self._runtime_overrides.clear()
            self._tombstones.clear()
            self._validator_defaults.clear()

            self._build_effective()
        except Exception:
            self._restore(snap)
            raise

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, key: str | None = None) -> None:
        """Run validators against the current effective settings."""
        # Collect effective tree into a single flat dict (uppercase keys)
        # for snapshot purposes
        snap = self._snapshot()
        try:
            for validator in self._validators:
                if key is not None and validator.name != key:
                    continue
                validator.validate(self)
        except ValidationError:
            self._restore(snap)
            raise

    def register_validator(self, validator: Validator) -> None:
        """Add a validator post-construction."""
        self._validators.append(validator)

    # ------------------------------------------------------------------
    # Attribute / item access
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        if self._effective is None or not self._effective.exists(name):
            raise AttributeError(f"No setting: {name!r}")
        return self._effective.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        self.set(name, value)

    def __delattr__(self, name: str) -> None:
        if name.startswith("_"):
            super().__delattr__(name)
            return
        self.delete(name)

    def __getitem__(self, key: str) -> Any:
        if self._effective is None or not self._effective.exists(key):
            raise KeyError(key)
        return self._effective.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        if self._effective is None or not self._effective.exists(key):
            raise KeyError(key)
        self.delete(key)

    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    def __repr__(self) -> str:
        d = self.as_dict() if self._effective else {}
        return f"MiniDynaconf({d!r})"

    # ------------------------------------------------------------------
    # Internal (called by Validator)
    # ------------------------------------------------------------------

    def _set_raw(self, key: str, value: Any) -> None:
        """Set a value directly in the effective tree (used by validator
        defaults)."""
        if self._effective is not None:
            self._effective.set(key, value)
