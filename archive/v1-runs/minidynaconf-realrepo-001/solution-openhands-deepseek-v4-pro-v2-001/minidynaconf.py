"""
minidynaconf.py - Dependency-free layered application configuration.

A Python stdlib-only module inspired by Dynaconf's configuration-management model.
Settings can come from defaults, configuration files, environment variables,
secrets files, and runtime overrides.
"""

from __future__ import annotations

import copy
import json
import os
import re
from configparser import ConfigParser, Error as ConfigParserError
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Python 3.11+ tomllib; fall back to tomli / manual for 3.10 and earlier
# ---------------------------------------------------------------------------
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SettingsError(Exception):
    """Raised for malformed files, invalid casts, and configuration errors."""


class ValidationError(Exception):
    """Raised when one or more validation rules fail."""

    def __init__(self, message: str, key: str | None = None) -> None:
        super().__init__(message)
        self.key = key


# ---------------------------------------------------------------------------
# Sentinel for missing keys
# ---------------------------------------------------------------------------
_MISSING: Any = object()

# ---------------------------------------------------------------------------
# Helpers – key normalisation
# ---------------------------------------------------------------------------


def _normalise_key(key: str) -> list[str]:
    """Split a dotted key and lowercase every segment."""
    return [p.strip().lower() for p in key.split(".") if p.strip()]


def _normalise_env_key(raw: str, prefix: str) -> list[str] | None:
    """Return normalised path parts for *raw* if it matches *prefix*."""
    pfx = prefix.upper() + "_"
    if not raw.upper().startswith(pfx):
        return None
    rest = raw[len(pfx) :]
    # double-underscore → dot
    rest = rest.replace("__", ".")
    return _normalise_key(rest)


def _deep_get(d: dict[str, Any], parts: list[str]) -> Any:
    """Walk *parts* into nested dict *d*.  Return _MISSING when absent."""
    for p in parts:
        if not isinstance(d, dict) or p not in d:
            return _MISSING
        d = d[p]
    return d


def _deep_set(d: dict[str, Any], parts: list[str], value: Any) -> None:
    """Set *value* at *parts* inside *d*, creating intermediate dicts."""
    for p in parts[:-1]:
        if p not in d or not isinstance(d[p], dict):
            d[p] = {}
        d = d[p]
    d[parts[-1]] = value


def _deep_delete(d: dict[str, Any], parts: list[str]) -> bool:
    """Delete key at *parts*.  Return True if it existed."""
    for p in parts[:-1]:
        if not isinstance(d, dict) or p not in d:
            return False
        d = d[p]
    if isinstance(d, dict) and parts[-1] in d:
        del d[parts[-1]]
        return True
    return False


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> None:
    """Recursively merge *overlay* into *base* (mutates *base*)."""
    for k, v in overlay.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = copy.deepcopy(v)


def _deep_copy_upper(d: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy with all mapping keys uppercased."""
    result: dict[str, Any] = {}
    for k, v in d.items():
        nk = k.upper()
        if isinstance(v, dict):
            result[nk] = _deep_copy_upper(v)
        elif isinstance(v, list):
            result[nk] = [
                _deep_copy_upper(item) if isinstance(item, dict) else copy.deepcopy(item)
                for item in v
            ]
        else:
            result[nk] = copy.deepcopy(v)
    return result


# ---------------------------------------------------------------------------
# Text-source type casting
# ---------------------------------------------------------------------------

_BOOL_TRUE = frozenset({"true", "yes", "on", "1"})
_BOOL_FALSE = frozenset({"false", "no", "off", "0"})
_NULL_SPELLINGS = frozenset({"none", "null", "nil"})


def _try_auto_cast(value: str) -> Any:
    """Attempt to cast a *string* value to a richer Python type.

    The order is important:
    1. explicit @-token directives
    2. common boolean spellings
    3. null spellings
    4. integer
    5. float
    6. JSON container (list / dict)
    7. quoted-string stripping
    8. fall through as plain string
    """
    if not isinstance(value, str):
        return value

    v = value.strip()

    # 1. Explicit cast tokens: @int, @float, @bool, @json, @none, @str
    token = _try_explicit_cast(v)
    if token is not _MISSING:
        return token

    # 2. Booleans (case-insensitive)
    low = v.lower()
    if low in _BOOL_TRUE:
        return True
    if low in _BOOL_FALSE:
        return False

    # 3. Null
    if low in _NULL_SPELLINGS:
        return None

    # 4. Integer
    try:
        if not v.startswith("0") or v == "0":
            return int(v)
    except ValueError:
        pass

    # 5. Float
    try:
        return float(v)
    except ValueError:
        pass

    # 6. JSON container
    if (v.startswith("[") and v.endswith("]")) or (v.startswith("{") and v.endswith("}")):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, ValueError):
            pass

    # 7. Quoted string stripping (matching single or double quotes)
    if len(v) >= 2:
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1]

    # 8. Plain string
    return v


def _try_explicit_cast(value: str) -> Any:
    """If *value* starts with an @-token, attempt explicit cast.  Return _MISSING otherwise."""
    v = value.strip()
    if not v.startswith("@"):
        return _MISSING

    for token, caster in [
        ("@int ", lambda s: int(s.strip())),
        ("@float ", lambda s: float(s.strip())),
        ("@bool ", _cast_explicit_bool),
        ("@json ", lambda s: json.loads(s.strip())),
        ("@none ", lambda s: None),
        ("@str ", lambda s: s.strip()),
    ]:
        if v.startswith(token):
            try:
                return caster(v[len(token) :])
            except Exception as exc:
                raise SettingsError(f"Invalid explicit cast: {value!r}") from exc

    return _MISSING


def _cast_explicit_bool(raw: str) -> bool:
    s = raw.strip().lower()
    if s in _BOOL_TRUE:
        return True
    if s in _BOOL_FALSE:
        return False
    raise ValueError(f"Cannot cast {raw!r} to bool")


def _cast_value(value: Any, from_text: bool) -> Any:
    """Cast *value* if it came from a text source.  Python-native values pass through."""
    if from_text and isinstance(value, str):
        return _try_auto_cast(value)
    # Python values keep their type; but still check for explicit @-token strings
    if isinstance(value, str) and value.strip().startswith("@"):
        return _try_auto_cast(value)
    return value


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------


def _load_toml(path: str) -> dict[str, Any]:
    if tomllib is None:
        raise SettingsError("TOML support requires Python 3.11+ or the 'tomli' package")
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def _load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise SettingsError(f"JSON file {path!r} must contain an object at the top level")
    return data


def _load_ini(path: str) -> dict[str, Any]:
    cp = ConfigParser()
    try:
        cp.read(path, encoding="utf-8")
    except ConfigParserError as exc:
        raise SettingsError(f"Malformed INI file {path!r}: {exc}") from exc
    result: dict[str, Any] = {}
    for section in cp.sections():
        result[section] = {}
        for key, val in cp.items(section):
            result[section][key] = val
    # If there are keys in the DEFAULT section, ConfigParser merges them.
    # That's fine – we want them as regular settings.
    return result


def _load_yaml(path: str) -> dict[str, Any]:
    """Parse a practical subset of YAML (mappings, lists, scalars)."""
    with open(path, encoding="utf-8") as fh:
        return _parse_yaml_text(fh.read())


def _parse_yaml_text(text: str) -> dict[str, Any]:
    lines = text.split("\n")
    stack: list[tuple[dict[str, Any], int]] = [({}, -1)]

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Pop stack until we find a parent with lower indent
        while len(stack) > 1 and stack[-1][1] >= indent:
            stack.pop()

        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            # Unquote key if quoted
            if len(key) >= 2 and (
                (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'"))
            ):
                key = key[1:-1]
            value = value.strip()

            current = stack[-1][0]
            if not value:
                # Nested mapping follows
                nested: dict[str, Any] = {}
                current[key] = nested
                stack.append((nested, indent))
            else:
                current[key] = _parse_yaml_scalar(value)

    return stack[0][0]


def _parse_yaml_scalar(raw: str) -> Any:
    """Parse a single YAML scalar value."""
    v = raw.strip()

    # Quoted string
    if len(v) >= 2:
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1]

    # Flow-style containers
    if (v.startswith("[") and v.endswith("]")) or (v.startswith("{") and v.endswith("}")):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, ValueError):
            pass

    # Booleans & null
    low = v.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "none", "nil", "~"):
        return None

    # Numbers
    try:
        if "." in v or "e" in v.lower():
            return float(v)
        return int(v)
    except ValueError:
        pass

    return v


def _load_py(path: str) -> dict[str, Any]:
    """Execute a Python file in an isolated namespace; return uppercase public names."""
    namespace: dict[str, Any] = {}
    with open(path, encoding="utf-8") as fh:
        code = compile(fh.read(), path, "exec")
        exec(code, namespace)
    return {
        k: v for k, v in namespace.items() if k.isupper() and not k.startswith("_")
    }


def _load_dotenv_file(path: str) -> dict[str, Any]:
    """Parse a KEY=VALUE dotenv file.  Blank lines and #-comments are skipped."""
    result: dict[str, Any] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            value = value.strip()
            # Remove optional surrounding quotes
            if len(value) >= 2:
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
            result[key] = value
    return result


_FILE_LOADERS: dict[str, Callable[[str], dict[str, Any]]] = {
    ".toml": _load_toml,
    ".ini": _load_ini,
    ".yaml": _load_yaml,
    ".yml": _load_yaml,
    ".json": _load_json,
    ".py": _load_py,
}


def _load_any_file(path: str) -> dict[str, Any]:
    """Load a settings file, dispatching on extension."""
    ext = Path(path).suffix.lower()
    loader = _FILE_LOADERS.get(ext)
    if loader is None:
        raise SettingsError(f"Unsupported file format: {ext!r} (from {path!r})")
    return loader(path)


# ---------------------------------------------------------------------------
# Environment variable loading
# ---------------------------------------------------------------------------


def _read_env_vars(prefix: str) -> dict[str, Any]:
    """Read os.environ for keys matching *prefix*_..., return nested dict."""
    result: dict[str, Any] = {}
    for raw_key, raw_value in os.environ.items():
        parts = _normalise_env_key(raw_key, prefix)
        if parts is None:
            continue
        # Cast the value (env vars are always text)
        cast = _cast_value(raw_value, from_text=True)
        _deep_set(result, parts, cast)
    return result


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class Validator:
    """A validation rule for one logical key."""

    def __init__(
        self,
        name: str,
        *,
        required: bool = False,
        default: Any = _MISSING,
        is_type_of: type | tuple[type, ...] | None = None,
        eq: Any = _MISSING,
        ne: Any = _MISSING,
        gt: Any = _MISSING,
        gte: Any = _MISSING,
        lt: Any = _MISSING,
        lte: Any = _MISSING,
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
        """Run this validator against *settings*.  Raises ValidationError on failure."""
        parts = _normalise_key(self.name)
        raw = settings._get_nested(parts, _MISSING)

        if raw is _MISSING:
            if self.default is not _MISSING:
                settings._deep_set_parts(parts, copy.deepcopy(self.default))
                raw = settings._get_nested(parts, _MISSING)
            elif self.required:
                msg = self.messages.get("required", f"Missing required key: {self.name!r}")
                raise ValidationError(msg, key=self.name)

        if raw is not _MISSING:
            if self.is_type_of is not None and not isinstance(raw, self.is_type_of):
                msg = self.messages.get(
                    "is_type_of",
                    f"Key {self.name!r} must be {self.is_type_of}, got {type(raw).__name__}",
                )
                raise ValidationError(msg, key=self.name)

            for op_label, expected, actual in [
                ("eq", self.eq, raw == self.eq if self.eq is not _MISSING else True),
                ("ne", self.ne, raw != self.ne if self.ne is not _MISSING else True),
                ("gt", self.gt, raw > self.gt if self.gt is not _MISSING else True),
                ("gte", self.gte, raw >= self.gte if self.gte is not _MISSING else True),
                ("lt", self.lt, raw < self.lt if self.lt is not _MISSING else True),
                ("lte", self.lte, raw <= self.lte if self.lte is not _MISSING else True),
            ]:
                if not actual:
                    msg = self.messages.get(
                        op_label,
                        f"Key {self.name!r} failed {op_label} check (value={raw!r}, expected {op_label} {expected!r})",
                    )
                    raise ValidationError(msg, key=self.name)

            if self.condition is not None:
                try:
                    ok = self.condition(raw, settings)
                except Exception as exc:
                    raise ValidationError(
                        f"Condition for key {self.name!r} raised {exc}", key=self.name
                    ) from exc
                if not ok:
                    msg = self.messages.get(
                        "condition",
                        f"Key {self.name!r} failed custom condition",
                    )
                    raise ValidationError(msg, key=self.name)


# ---------------------------------------------------------------------------
# _SettingsProxy – case-insensitive attribute/item access on nested dicts
# ---------------------------------------------------------------------------


class _SettingsProxy:
    """Read-only proxy wrapping a nested dict with case-insensitive access."""

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, Any]) -> None:
        self._data: dict[str, Any] = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        key = name.lower()
        if key not in self._data:
            raise AttributeError(f"Setting {name!r} not found")
        val = self._data[key]
        if isinstance(val, dict):
            return _SettingsProxy(val)
        return val

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            super().__setattr__(name, value)
            return
        raise TypeError("Cannot set values through a settings proxy – use settings.set()")

    def __getitem__(self, key: str) -> Any:
        val = self._data[key.lower()]
        if isinstance(val, dict):
            return _SettingsProxy(val)
        return val

    def __contains__(self, key: str) -> bool:
        return key.lower() in self._data

    def __repr__(self) -> str:
        return f"_SettingsProxy({self._data!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _SettingsProxy):
            return self._data == other._data
        return self._data == other


# ---------------------------------------------------------------------------
# MiniDynaconf
# ---------------------------------------------------------------------------


class MiniDynaconf:
    """Layered application settings.

    Layer priority (lowest → highest):
      1. constructor defaults
      2. settings files
      3. environment variables
      4. secrets files
      5. runtime overrides / assignments
    """

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
        # --- configuration (saved for reload / configure) ---------------
        self._settings_files_raw = settings_files
        self._defaults_raw = defaults or {}
        self._envvar_prefix = envvar_prefix
        self._environments = environments
        self._env_arg = env
        self._secrets_files_raw = secrets_files
        self._validators_list = list(validators or [])
        self._load_dotenv_flag = load_dotenv

        # --- live state -------------------------------------------------
        self._store: dict[str, Any] = {}
        self._runtime: dict[str, Any] = {}

        self._build()
        if self._validators_list:
            self.validate()

    # -------------------------------------------------------------------
    # Internal: construction helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _normalise_path_list(raw: Any) -> list[str]:
        """Return a flat list of string paths from the variadic input."""
        if raw is None:
            return []
        if isinstance(raw, (str, Path)):
            return [str(raw)]
        return [str(p) for p in raw]

    def _resolve_env(self) -> str:
        """Determine the active environment name."""
        if self._env_arg is not None:
            return self._env_arg
        return os.environ.get("ENV_FOR_DYNACONF", "default")

    def _build(self) -> None:
        """(Re)build the canonical store from configured sources."""
        self._store = {}
        self._runtime = {}

        # 1. Defaults (Python values – preserve types; still process @-tokens)
        if self._defaults_raw:
            self._merge_into_store(self._defaults_raw, from_text=False)

        # 2. Settings files
        for path in self._normalise_path_list(self._settings_files_raw):
            data = self._load_file(path)
            if data:
                self._merge_into_store(data, from_text=True)

        # 3. Environment variables
        env_data = _read_env_vars(self._envvar_prefix)
        if env_data:
            self._merge_into_store(env_data, from_text=False)  # already cast by _read_env_vars

        # 4. Dotenv files
        if self._load_dotenv_flag:
            dotenv_path = Path(".env")
            if dotenv_path.is_file():
                dotenv_data = _load_dotenv_file(str(dotenv_path))
                filtered: dict[str, Any] = {}
                for raw_key, raw_value in dotenv_data.items():
                    parts = _normalise_env_key(raw_key, self._envvar_prefix)
                    if parts is None:
                        continue
                    cast_val = _cast_value(raw_value, from_text=True)
                    _deep_set(filtered, parts, cast_val)
                if filtered:
                    self._merge_into_store(filtered, from_text=False)

        # 5. Secrets files
        for path in self._normalise_path_list(self._secrets_files_raw):
            data = self._load_file(path)
            if data:
                self._merge_into_store(data, from_text=True)

    def _load_file(self, path: str) -> dict[str, Any] | None:
        """Load one file, respecting environment switching if enabled."""
        if not os.path.isfile(path):
            return None
        data = _load_any_file(path)
        if not self._environments:
            return data
        # Environment switching: pick "default" + active env
        result: dict[str, Any] = {}
        default_section = data.get("default")
        if isinstance(default_section, dict):
            _deep_merge(result, default_section)
        env_section = data.get(self._resolve_env())
        if isinstance(env_section, dict):
            _deep_merge(result, env_section)
        return result

    def _merge_into_store(self, data: dict[str, Any], *, from_text: bool) -> None:
        """Cast leaf values (if *from_text*) then deep-merge into ``_store``."""

        def _cast_leaves(d: dict[str, Any]) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for k, v in d.items():
                nk = k.lower()
                if isinstance(v, dict):
                    out[nk] = _cast_leaves(v)
                elif isinstance(v, list):
                    out[nk] = [
                        _cast_leaves(item) if isinstance(item, dict) else _cast_value(item, from_text)
                        for item in v
                    ]
                else:
                    out[nk] = _cast_value(v, from_text)
            return out

        processed = _cast_leaves(data)
        _deep_merge(self._store, processed)

    # -------------------------------------------------------------------
    # Internal: nested access
    # -------------------------------------------------------------------

    def _get_nested(self, parts: list[str], default: Any = _MISSING) -> Any:
        """Return the merged view at *parts* – runtime overrides store
        recursively, so ``db.port`` in runtime does not shadow ``db.host``
        in store."""
        # When runtime is empty (common case), take the fast path.
        if not self._runtime:
            val = _deep_get(self._store, parts)
            if val is not _MISSING:
                return val
            return default if default is not _MISSING else _MISSING

        # Merge runtime on top of store for a consistent read view.
        merged = copy.deepcopy(self._store)
        _deep_merge(merged, self._runtime)
        val = _deep_get(merged, parts)
        if val is not _MISSING:
            return val
        return default if default is not _MISSING else _MISSING

    def _resolve_key(self, key: str) -> list[str]:
        return _normalise_key(key)

    def _deep_set_parts(self, parts: list[str], value: Any) -> None:
        """Set *value* in the runtime layer (highest priority)."""
        _deep_set(self._runtime, parts, value)

    # -------------------------------------------------------------------
    # Public: access API
    # -------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        parts = _normalise_key(name)
        val = self._get_nested(parts)
        if val is _MISSING:
            raise AttributeError(f"Setting {name!r} not found")
        if isinstance(val, dict):
            return _SettingsProxy(val)
        return val

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        parts = _normalise_key(name)
        self._deep_set_parts(parts, copy.deepcopy(value))

    def __delattr__(self, name: str) -> None:
        if name.startswith("_"):
            super().__delattr__(name)
            return
        parts = _normalise_key(name)
        found = _deep_delete(self._runtime, parts)
        if not found:
            _deep_delete(self._store, parts)

    def __getitem__(self, key: str) -> Any:
        parts = self._resolve_key(key)
        val = self._get_nested(parts)
        if val is _MISSING:
            raise KeyError(key)
        if isinstance(val, dict):
            return _SettingsProxy(val)
        return val

    def __setitem__(self, key: str, value: Any) -> None:
        parts = self._resolve_key(key)
        self._deep_set_parts(parts, copy.deepcopy(value))

    def __delitem__(self, key: str) -> None:
        parts = self._resolve_key(key)
        found = _deep_delete(self._runtime, parts)
        if not found:
            _deep_delete(self._store, parts)

    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    def get(self, key: str, default: Any = None, cast: Callable[[Any], Any] | None = None) -> Any:
        """Return the value for *key*, or *default* if missing.

        If *cast* is provided, the retrieved value is passed through it
        without mutating the stored state.
        """
        parts = self._resolve_key(key)
        val = self._get_nested(parts, _MISSING)
        if val is _MISSING:
            return default
        if cast is not None:
            return cast(val)
        return val

    def set(self, key: str, value: Any, *, validate: bool = False) -> None:
        """Set a single key.  With *validate=True* the change is atomic."""
        if validate:
            snapshot = (copy.deepcopy(self._store), copy.deepcopy(self._runtime))
        parts = self._resolve_key(key)
        self._deep_set_parts(parts, copy.deepcopy(value))
        if validate:
            try:
                self.validate()
            except Exception:
                self._store, self._runtime = snapshot
                raise

    def update(self, mapping: dict[str, Any], *, validate: bool = False) -> None:
        """Merge *mapping* into settings.  With *validate=True* the change is atomic."""
        if validate:
            snapshot = (copy.deepcopy(self._store), copy.deepcopy(self._runtime))
        for k, v in mapping.items():
            parts = self._resolve_key(k)
            self._deep_set_parts(parts, copy.deepcopy(v))
        if validate:
            try:
                self.validate()
            except Exception:
                self._store, self._runtime = snapshot
                raise

    def exists(self, key: str) -> bool:
        """Return True if *key* is present (even if its value is falsey)."""
        parts = self._resolve_key(key)
        return self._get_nested(parts) is not _MISSING

    def delete(self, key: str) -> None:
        """Remove *key* from the store and runtime layers."""
        parts = self._resolve_key(key)
        _deep_delete(self._runtime, parts)
        _deep_delete(self._store, parts)

    def as_dict(self) -> dict[str, Any]:
        """Return a deep copy with uppercase canonical keys at every level."""
        merged: dict[str, Any] = {}
        _deep_merge(merged, self._store)
        _deep_merge(merged, self._runtime)
        return _deep_copy_upper(merged)

    def reload(self) -> None:
        """Rebuild settings from configured sources, discarding runtime overrides."""
        self._build()
        if self._validators_list:
            self.validate()

    def configure(self, **kwargs: Any) -> None:
        """Replace constructor options and reload.

        Accepted keys mirror the constructor:
          settings_files, defaults, envvar_prefix, environments, env,
          secrets_files, validators, load_dotenv
        """
        for attr, key in [
            ("_settings_files_raw", "settings_files"),
            ("_defaults_raw", "defaults"),
            ("_envvar_prefix", "envvar_prefix"),
            ("_environments", "environments"),
            ("_env_arg", "env"),
            ("_secrets_files_raw", "secrets_files"),
            ("_validators_list", "validators"),
            ("_load_dotenv_flag", "load_dotenv"),
        ]:
            if key in kwargs:
                val = kwargs[key]
                if key == "validators":
                    val = list(val or [])
                setattr(self, attr, val)
        self._build()
        if self._validators_list:
            self.validate()

    # -------------------------------------------------------------------
    # File loading (post-construction)
    # -------------------------------------------------------------------

    def load_file(self, path: str, *, env: str | None = None, silent: bool = True) -> None:
        """Load an additional settings file.

        With *silent=False* missing / malformed files raise ``SettingsError``.
        """
        if not os.path.isfile(path):
            if not silent:
                raise SettingsError(f"File not found: {path!r}")
            return
        try:
            data = _load_any_file(path)
        except Exception:
            if not silent:
                raise
            raise SettingsError(f"Malformed file: {path!r}") from None

        if not data:
            return
        if self._environments:
            result: dict[str, Any] = {}
            default_section = data.get("default")
            if isinstance(default_section, dict):
                _deep_merge(result, default_section)
            env_section = data.get(self._resolve_env())
            if isinstance(env_section, dict):
                _deep_merge(result, env_section)
            data = result
        self._merge_into_store(data, from_text=True)

    def load_env_file(self, path: str) -> None:
        """Load a dotenv-style file."""
        data = _load_dotenv_file(path)
        filtered: dict[str, Any] = {}
        for raw_key, raw_value in data.items():
            parts = _normalise_env_key(raw_key, self._envvar_prefix)
            if parts is None:
                continue
            cast_val = _cast_value(raw_value, from_text=True)
            _deep_set(filtered, parts, cast_val)
        if filtered:
            self._merge_into_store(filtered, from_text=False)

    # -------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------

    def register_validator(self, validator: Validator) -> None:
        """Add a validator to the list and run it immediately."""
        self._validators_list.append(validator)
        validator.validate(self)

    def validate(self, key: str | None = None) -> None:
        """Run registered validators.  If *key* is given only that key's
        validators are executed.

        Validation is atomic: if any validator fails, all defaults applied
        by earlier validators are rolled back.
        """
        snapshot = (copy.deepcopy(self._store), copy.deepcopy(self._runtime))
        try:
            for v in self._validators_list:
                if key is not None and v.name != key:
                    continue
                v.validate(self)
        except Exception:
            self._store, self._runtime = snapshot
            raise
