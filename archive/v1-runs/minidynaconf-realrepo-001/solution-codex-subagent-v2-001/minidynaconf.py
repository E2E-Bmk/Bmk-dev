"""A small dependency-free layered configuration helper."""

from __future__ import annotations

import ast
import configparser
import copy
import json
import os
import re
import runpy
import tomllib
from collections.abc import MutableMapping
from pathlib import Path


class SettingsError(Exception):
    """Raised for configuration loading and casting errors."""


class ValidationError(SettingsError):
    """Raised when a validator fails."""


_MISSING = object()
_NO_DEFAULT = object()


def _is_mapping(value):
    return isinstance(value, dict)


def _to_list(value):
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)):
        return [value]
    return list(value)


def _path_parts(key, separator="."):
    if isinstance(key, (list, tuple)):
        parts = [str(part) for part in key]
    else:
        parts = str(key).split(separator)
    return [part.upper() for part in parts if str(part) != ""]


def _deepcopy(value):
    return copy.deepcopy(value)


def _canonicalize(value):
    if isinstance(value, MutableMapping):
        return {str(k).upper(): _canonicalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return _deepcopy(value)


def _merge_into(target, source):
    for key, value in _canonicalize(source).items():
        if _is_mapping(value) and _is_mapping(target.get(key)):
            _merge_into(target[key], value)
        else:
            target[key] = _deepcopy(value)
    return target


def _set_path(target, parts, value):
    if not parts:
        raise SettingsError("empty setting key")
    cursor = target
    for part in parts[:-1]:
        current = cursor.get(part)
        if not _is_mapping(current):
            current = {}
            cursor[part] = current
        cursor = current
    final = parts[-1]
    value = _canonicalize(value)
    if _is_mapping(value) and _is_mapping(cursor.get(final)):
        _merge_into(cursor[final], value)
    else:
        cursor[final] = _deepcopy(value)


def _get_path(data, parts, default=_NO_DEFAULT):
    cursor = data
    for part in parts:
        if not _is_mapping(cursor) or part not in cursor:
            if default is _NO_DEFAULT:
                raise KeyError(".".join(parts))
            return default
        cursor = cursor[part]
    return cursor


def _delete_path(data, parts):
    if not parts:
        return False
    cursor = data
    for part in parts[:-1]:
        if not _is_mapping(cursor) or part not in cursor:
            return False
        cursor = cursor[part]
    if _is_mapping(cursor) and parts[-1] in cursor:
        del cursor[parts[-1]]
        return True
    return False


def _strip_inline_comment(text):
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == "#" and quote is None:
            return text[:index].rstrip()
    return text.strip()


def _cast_scalar(value, *, explicit_only=False):
    if not isinstance(value, str):
        return value
    text = value.strip()
    if text == "":
        return "" if not explicit_only else value

    if text.startswith("@"):
        return _explicit_cast(text)
    if explicit_only:
        return value

    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]

    lowered = text.lower()
    if lowered in {"true", "yes", "on", "y", "t"}:
        return True
    if lowered in {"false", "no", "off", "n", "f"}:
        return False
    if lowered in {"none", "null", "nil", "~"}:
        return None

    if (text.startswith("[") and text.endswith("]")) or (
        text.startswith("{") and text.endswith("}")
    ):
        parsed = _parse_container_literal(text)
        return _cast_container(parsed)

    if re.fullmatch(r"[+-]?\d+", text):
        try:
            return int(text)
        except ValueError:
            pass
    if re.fullmatch(r"[+-]?((\d+\.\d*)|(\.\d+)|(\d+))([eE][+-]?\d+)?", text):
        if "." in text or "e" in lowered:
            try:
                return float(text)
            except ValueError:
                pass
    return text


def _cast_container(value):
    if isinstance(value, list):
        return [_cast_container(item) for item in value]
    if isinstance(value, dict):
        return {str(key).upper(): _cast_container(item) for key, item in value.items()}
    return value


def _cast_runtime_explicit(value):
    if isinstance(value, str):
        return _cast_scalar(value)
    if isinstance(value, dict):
        return {str(key).upper(): _cast_runtime_explicit(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_cast_runtime_explicit(item) for item in value]
    return value


def _parse_container_literal(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return ast.literal_eval(text)
    except Exception as exc:
        raise SettingsError("invalid container literal") from exc


def _explicit_cast(text):
    match = re.match(r"^@([A-Za-z_]+)(?:\s+(.*))?$", text, re.DOTALL)
    if not match:
        raise SettingsError("invalid explicit cast")
    kind = match.group(1).lower()
    raw = "" if match.group(2) is None else match.group(2).strip()
    try:
        if kind == "int":
            return int(raw)
        if kind == "float":
            return float(raw)
        if kind == "bool":
            lowered = raw.lower()
            if lowered in {"true", "yes", "on", "1", "y", "t"}:
                return True
            if lowered in {"false", "no", "off", "0", "n", "f"}:
                return False
            raise ValueError(raw)
        if kind == "json":
            return _cast_container(json.loads(raw))
        if kind == "none":
            if raw and raw.lower() not in {"none", "null", "nil", "~"}:
                raise ValueError(raw)
            return None
        if kind == "str":
            return raw
    except Exception as exc:
        if isinstance(exc, SettingsError):
            raise
        raise SettingsError("invalid explicit cast") from exc
    raise SettingsError("unknown explicit cast")


def _cast_text_tree(value):
    if isinstance(value, dict):
        return {str(k).upper(): _cast_text_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_cast_text_tree(item) for item in value]
    return _cast_scalar(value)


def _public_python_vars(namespace):
    return {
        key: value
        for key, value in namespace.items()
        if key.isupper() and not key.startswith("_")
    }


def _parse_yaml_subset(text):
    root = {}
    stack = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = raw_line.rstrip()
        indent = len(line) - len(line.lstrip(" "))
        body = _strip_inline_comment(line.strip())
        if not body:
            continue
        if ":" not in body:
            raise SettingsError("invalid yaml line")
        key, value = body.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise SettingsError("invalid yaml key")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _cast_scalar(value)
    return root


def _read_file(path):
    path = Path(os.fspath(path))
    suffix = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text()
    if text.strip() == "":
        return {}
    try:
        if suffix == ".json":
            data = json.loads(text)
        elif suffix == ".toml":
            data = tomllib.loads(text)
        elif suffix in {".yaml", ".yml"}:
            data = _parse_yaml_subset(text)
        elif suffix == ".ini":
            parser = configparser.ConfigParser()
            parser.optionxform = str
            parser.read_string(text)
            data = {}
            if parser.defaults():
                data.update(dict(parser.defaults()))
            for section in parser.sections():
                data[section] = dict(parser.items(section, raw=True))
        elif suffix == ".py":
            data = _public_python_vars(runpy.run_path(str(path), init_globals={}))
        else:
            raise SettingsError("unsupported settings file")
    except SettingsError:
        raise
    except Exception as exc:
        raise SettingsError("malformed settings file") from exc
    if not isinstance(data, dict):
        raise SettingsError("settings file must contain an object")
    return _cast_text_tree(data)


def _env_layer_from_mapping(mapping, prefix):
    result = {}
    prefix = "" if prefix is None else str(prefix)
    marker = prefix.upper() + "_" if prefix else ""
    for raw_key, raw_value in mapping.items():
        key = str(raw_key)
        if marker:
            if not key.upper().startswith(marker):
                continue
            logical = key[len(marker) :]
        else:
            logical = key
        if not logical:
            continue
        parts = _path_parts(logical, separator="__")
        if not parts:
            continue
        _set_path(result, parts, _cast_scalar(str(raw_value)))
    return result


def _parse_dotenv(path):
    path = Path(os.fspath(path))
    env = {}
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(value.strip())
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        env[key] = value
    return env


class Validator:
    def __init__(
        self,
        name,
        *,
        required=False,
        default=None,
        is_type_of=None,
        eq=None,
        ne=None,
        gt=None,
        gte=None,
        lt=None,
        lte=None,
        condition=None,
        messages=None,
    ):
        self.name = str(name)
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


class _SettingsProxy(MutableMapping):
    def __init__(self, settings, parts):
        object.__setattr__(self, "_settings", settings)
        object.__setattr__(self, "_parts", tuple(parts))

    def _full(self, key=None):
        if key is None:
            return ".".join(self._parts)
        return ".".join(self._parts + tuple(_path_parts(key)))

    def _mapping(self):
        value = self._settings.get(self._full())
        if not _is_mapping(value):
            raise TypeError("setting is not a mapping")
        return value

    def __getitem__(self, key):
        return self._settings[self._full(key)]

    def __setitem__(self, key, value):
        self._settings.set(self._full(key), value)

    def __delitem__(self, key):
        if not self._settings.delete(self._full(key)):
            raise KeyError(key)

    def __iter__(self):
        return iter(self._mapping())

    def __len__(self):
        return len(self._mapping())

    def __contains__(self, key):
        return self._settings.exists(self._full(key))

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self[name] = value

    def __delattr__(self, name):
        if name.startswith("_"):
            object.__delattr__(self, name)
        elif not self._settings.delete(self._full(name)):
            raise AttributeError(name)

    def get(self, key, default=None, cast=None):
        return self._settings.get(self._full(key), default=default, cast=cast)

    def exists(self, key):
        return self._settings.exists(self._full(key))

    def as_dict(self):
        return _deepcopy(self._mapping())

    def __eq__(self, other):
        if isinstance(other, _SettingsProxy):
            other = other.as_dict()
        return self.as_dict() == other

    def __repr__(self):
        return repr(self.as_dict())


class MiniDynaconf:
    def __init__(
        self,
        settings_files=None,
        defaults=None,
        envvar_prefix="APP",
        environments=False,
        env=None,
        secrets_files=None,
        validators=None,
        load_dotenv=False,
    ):
        object.__setattr__(self, "_settings_files", _to_list(settings_files))
        object.__setattr__(self, "_defaults", _canonicalize(defaults or {}))
        object.__setattr__(self, "_envvar_prefix", envvar_prefix)
        object.__setattr__(self, "_environments", bool(environments))
        object.__setattr__(self, "_env", env)
        object.__setattr__(self, "_secrets_files", _to_list(secrets_files))
        object.__setattr__(self, "_validators", list(validators or []))
        object.__setattr__(self, "_dotenv_files", [])
        object.__setattr__(self, "_load_dotenv", bool(load_dotenv))
        object.__setattr__(self, "_data", {})
        if load_dotenv and Path(".env").exists():
            self._dotenv_files.append(".env")
        self.reload()
        if self._validators:
            self.validate()

    @property
    def current_env(self):
        return (self._env or os.environ.get("ENV_FOR_DYNACONF") or "default").upper()

    def _file_values_for_env(self, data, env=None):
        data = _canonicalize(data)
        if not self._environments:
            return data
        active = (env or self._env or os.environ.get("ENV_FOR_DYNACONF") or "default").upper()
        result = {}
        default = data.get("DEFAULT")
        if _is_mapping(default):
            _merge_into(result, default)
        active_values = data.get(active)
        if active_values is not default and _is_mapping(active_values):
            _merge_into(result, active_values)
        return result

    def _load_files_into(self, data, files, *, env=None, silent=True):
        for item in _to_list(files):
            path = Path(os.fspath(item))
            if not path.exists():
                if silent:
                    continue
                raise SettingsError("settings file not found")
            values = _read_file(path)
            _merge_into(data, self._file_values_for_env(values, env=env))

    def _build_data(self):
        data = _canonicalize(self._defaults)
        self._load_files_into(data, self._settings_files, silent=True)
        _merge_into(data, _env_layer_from_mapping(os.environ, self._envvar_prefix))
        for dotenv in self._dotenv_files:
            path = Path(os.fspath(dotenv))
            if path.exists():
                _merge_into(data, _env_layer_from_mapping(_parse_dotenv(path), self._envvar_prefix))
        self._load_files_into(data, self._secrets_files, silent=True)
        return data

    def reload(self):
        new_data = self._build_data()
        old = self._data
        object.__setattr__(self, "_data", new_data)
        try:
            if self._validators:
                self.validate()
        except Exception:
            object.__setattr__(self, "_data", old)
            raise
        return self

    def configure(self, **kwargs):
        old_config = {
            "_settings_files": self._settings_files,
            "_defaults": self._defaults,
            "_envvar_prefix": self._envvar_prefix,
            "_environments": self._environments,
            "_env": self._env,
            "_secrets_files": self._secrets_files,
            "_validators": self._validators,
            "_dotenv_files": self._dotenv_files,
            "_load_dotenv": self._load_dotenv,
            "_data": self._data,
        }
        try:
            if "settings_files" in kwargs:
                object.__setattr__(self, "_settings_files", _to_list(kwargs.pop("settings_files")))
            if "defaults" in kwargs:
                object.__setattr__(self, "_defaults", _canonicalize(kwargs.pop("defaults") or {}))
            if "envvar_prefix" in kwargs:
                object.__setattr__(self, "_envvar_prefix", kwargs.pop("envvar_prefix"))
            if "environments" in kwargs:
                object.__setattr__(self, "_environments", bool(kwargs.pop("environments")))
            if "env" in kwargs:
                object.__setattr__(self, "_env", kwargs.pop("env"))
            if "secrets_files" in kwargs:
                object.__setattr__(self, "_secrets_files", _to_list(kwargs.pop("secrets_files")))
            if "validators" in kwargs:
                object.__setattr__(self, "_validators", list(kwargs.pop("validators") or []))
            if "load_dotenv" in kwargs:
                load_dotenv = bool(kwargs.pop("load_dotenv"))
                object.__setattr__(self, "_load_dotenv", load_dotenv)
                object.__setattr__(self, "_dotenv_files", [".env"] if load_dotenv and Path(".env").exists() else [])
            if kwargs:
                raise SettingsError("unknown configuration option")
            self.reload()
        except Exception:
            for name, value in old_config.items():
                object.__setattr__(self, name, value)
            raise
        return self

    def load_file(self, path, *, env=None, silent=True):
        file_path = Path(os.fspath(path))
        if not file_path.exists():
            if silent:
                return self
            raise SettingsError("settings file not found")
        old = _deepcopy(self._data)
        try:
            values = self._file_values_for_env(_read_file(file_path), env=env)
            _merge_into(self._data, values)
            if self._validators:
                self.validate()
        except Exception:
            object.__setattr__(self, "_data", old)
            raise
        return self

    def load_env_file(self, path):
        file_path = Path(os.fspath(path))
        if not file_path.exists():
            return self
        old = _deepcopy(self._data)
        try:
            layer = _env_layer_from_mapping(_parse_dotenv(file_path), self._envvar_prefix)
            _merge_into(self._data, layer)
            if str(file_path) not in [str(Path(os.fspath(p))) for p in self._dotenv_files]:
                self._dotenv_files.append(file_path)
            if self._validators:
                self.validate()
        except Exception:
            object.__setattr__(self, "_data", old)
            raise
        return self

    def register_validator(self, validator):
        self._validators.append(validator)
        return self

    def validate(self, key=None):
        selected = self._validators
        if key is not None:
            key_parts = _path_parts(key)
            selected = [v for v in selected if _path_parts(v.name) == key_parts]
        snapshot = _deepcopy(self._data)
        candidate = _deepcopy(self._data)
        object.__setattr__(self, "_data", candidate)
        try:
            for validator in selected:
                self._run_validator(validator)
        except Exception:
            object.__setattr__(self, "_data", snapshot)
            raise
        object.__setattr__(self, "_data", candidate)
        return True

    def _run_validator(self, validator):
        parts = _path_parts(validator.name)
        exists = self.exists(validator.name)
        if not exists and validator.default is not None:
            self.set(validator.name, _deepcopy(validator.default), validate=False)
            exists = True
        if not exists:
            if validator.required:
                raise ValidationError(f"{validator.name} is required")
            return True
        value = self.get(validator.name)
        if validator.is_type_of is not None and not isinstance(value, validator.is_type_of):
            raise ValidationError(f"{validator.name} has invalid type")
        checks = (
            ("eq", validator.eq, lambda a, b: a == b),
            ("ne", validator.ne, lambda a, b: a != b),
            ("gt", validator.gt, lambda a, b: a > b),
            ("gte", validator.gte, lambda a, b: a >= b),
            ("lt", validator.lt, lambda a, b: a < b),
            ("lte", validator.lte, lambda a, b: a <= b),
        )
        for name, expected, func in checks:
            if expected is not None and not func(value, expected):
                raise ValidationError(f"{validator.name} failed {name}")
        if validator.condition is not None and not validator.condition(value, self):
            raise ValidationError(f"{validator.name} failed condition")
        return True

    def _coerce_cast(self, value, cast):
        if cast is None:
            return value
        if isinstance(cast, str):
            return _explicit_cast("@" + cast + " " + str(value))
        if cast is bool:
            return _explicit_cast("@bool " + str(value))
        if cast is int:
            return int(value)
        if cast is float:
            return float(value)
        if cast is str:
            return str(value)
        return cast(value)

    def get(self, key, default=None, cast=None):
        value = _get_path(self._data, _path_parts(key), default=_MISSING)
        if value is _MISSING:
            return default
        if _is_mapping(value):
            value = _SettingsProxy(self, _path_parts(key))
        else:
            value = _deepcopy(value)
        if cast is not None:
            return self._coerce_cast(value, cast)
        return value

    def exists(self, key):
        return _get_path(self._data, _path_parts(key), default=_MISSING) is not _MISSING

    def set(self, key, value, *, validate=False):
        old = _deepcopy(self._data)
        try:
            value = _cast_runtime_explicit(value)
            _set_path(self._data, _path_parts(key), value)
            if validate:
                self.validate()
        except Exception:
            object.__setattr__(self, "_data", old)
            raise
        return self

    def update(self, mapping, *, validate=False):
        old = _deepcopy(self._data)
        try:
            for key, value in dict(mapping).items():
                value = _cast_runtime_explicit(value)
                if "." in str(key):
                    _set_path(self._data, _path_parts(key), value)
                else:
                    _merge_into(self._data, {key: value})
            if validate:
                self.validate()
        except Exception:
            object.__setattr__(self, "_data", old)
            raise
        return self

    def delete(self, key):
        return _delete_path(self._data, _path_parts(key))

    def as_dict(self):
        return _deepcopy(self._data)

    def __getitem__(self, key):
        value = _get_path(self._data, _path_parts(key))
        if _is_mapping(value):
            return _SettingsProxy(self, _path_parts(key))
        return _deepcopy(value)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        if not self.delete(key):
            raise KeyError(key)

    def __contains__(self, key):
        return self.exists(key)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self.set(name, value)

    def __delattr__(self, name):
        if name.startswith("_"):
            object.__delattr__(self, name)
        elif not self.delete(name):
            raise AttributeError(name)

    def __repr__(self):
        return f"MiniDynaconf({self._data!r})"
