"""A small, dependency-free layered configuration object."""

from __future__ import annotations

import ast
import configparser
import copy
import json
import os
import re
from pathlib import Path

try:  # pragma: no cover - exercised implicitly when available.
    import tomllib
except Exception:  # pragma: no cover
    tomllib = None


class SettingsError(Exception):
    """Raised for configuration loading and casting errors."""


class ValidationError(SettingsError):
    """Raised when a validator fails."""


_MISSING = object()
_NO_DEFAULT = object()
_ENV_NAMES = {"default", "development", "testing", "production"}


class Validator:
    def __init__(
        self,
        name,
        *,
        required=False,
        default=_MISSING,
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
        self.has_default = default is not _MISSING
        self.is_type_of = is_type_of
        self.eq = eq
        self.ne = ne
        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte
        self.condition = condition
        self.messages = messages or {}


def _path_parts(key):
    if isinstance(key, (list, tuple)):
        parts = key
    else:
        parts = str(key).replace("__", ".").split(".")
    return [str(part).upper() for part in parts if str(part) != ""]


def _is_mapping(value):
    return isinstance(value, dict)


def _deepcopy(value):
    return copy.deepcopy(value)


def _merge_dicts(base, incoming):
    for key, value in incoming.items():
        key = str(key).upper()
        if _is_mapping(value) and _is_mapping(base.get(key)):
            _merge_dicts(base[key], value)
        else:
            base[key] = _deepcopy(value)
    return base


def _assign_path(tree, parts, value):
    if not parts:
        if not _is_mapping(value):
            raise SettingsError("root assignment must be a mapping")
        _merge_dicts(tree, value)
        return
    cursor = tree
    for part in parts[:-1]:
        current = cursor.get(part)
        if not _is_mapping(current):
            current = {}
            cursor[part] = current
        cursor = current
    leaf = parts[-1]
    if _is_mapping(value) and _is_mapping(cursor.get(leaf)):
        _merge_dicts(cursor[leaf], value)
    else:
        cursor[leaf] = _deepcopy(value)


def _get_path(tree, parts, default=_NO_DEFAULT):
    cursor = tree
    for part in parts:
        if not _is_mapping(cursor) or part not in cursor:
            if default is _NO_DEFAULT:
                raise KeyError(".".join(parts))
            return default
        cursor = cursor[part]
    return cursor


def _exists_path(tree, parts):
    try:
        _get_path(tree, parts)
        return True
    except KeyError:
        return False


def _delete_path(tree, parts):
    if not parts:
        tree.clear()
        return
    cursor = tree
    for part in parts[:-1]:
        if not _is_mapping(cursor) or part not in cursor:
            return
        cursor = cursor[part]
    if _is_mapping(cursor):
        cursor.pop(parts[-1], None)


def _apply_missing(tree, defaults):
    for key, value in defaults.items():
        if _is_mapping(value):
            current = tree.get(key)
            if not _is_mapping(current):
                if key not in tree:
                    tree[key] = {}
                    current = tree[key]
                else:
                    continue
            _apply_missing(current, value)
        elif key not in tree:
            tree[key] = _deepcopy(value)


def _normalize_mapping(mapping, *, auto_cast=False, explicit_only=False):
    if mapping is None:
        return {}
    if not _is_mapping(mapping):
        raise SettingsError("settings data must be a mapping")
    result = {}
    for key, value in mapping.items():
        parts = _path_parts(key)
        if not parts:
            continue
        normalized = _normalize_value(value, auto_cast=auto_cast, explicit_only=explicit_only)
        _assign_path(result, parts, normalized)
    return result


def _normalize_value(value, *, auto_cast=False, explicit_only=False):
    if _is_mapping(value):
        return _normalize_mapping(value, auto_cast=auto_cast, explicit_only=explicit_only)
    if isinstance(value, list):
        return [
            _normalize_value(item, auto_cast=auto_cast, explicit_only=explicit_only)
            for item in value
        ]
    if isinstance(value, tuple):
        return [
            _normalize_value(item, auto_cast=auto_cast, explicit_only=explicit_only)
            for item in value
        ]
    if isinstance(value, str):
        if value.lstrip().startswith("@"):
            return _explicit_cast(value)
        if auto_cast and not explicit_only:
            return _auto_cast(value)
    return _deepcopy(value)


def _explicit_cast(value):
    text = str(value).strip()
    match = re.match(r"^@([A-Za-z_]+)(?:\s+(.*))?$", text, re.S)
    if not match:
        raise SettingsError("invalid explicit cast")
    cast_name = match.group(1).lower()
    raw = "" if match.group(2) is None else match.group(2)
    try:
        if cast_name == "int":
            return int(raw.strip())
        if cast_name == "float":
            return float(raw.strip())
        if cast_name == "bool":
            return _cast_bool(raw)
        if cast_name == "json":
            return _normalize_container(json.loads(raw))
        if cast_name == "none":
            stripped = raw.strip().lower()
            if stripped in {"", "none", "null", "nil"}:
                return None
            raise ValueError("invalid none cast")
        if cast_name == "str":
            return raw
    except Exception as exc:
        raise SettingsError("invalid explicit cast") from exc
    raise SettingsError("unknown explicit cast")


def _cast_bool(raw):
    text = str(raw).strip().lower()
    if text in {"true", "t", "yes", "y", "on", "enabled", "1"}:
        return True
    if text in {"false", "f", "no", "n", "off", "disabled", "0"}:
        return False
    raise ValueError("invalid boolean")


def _auto_cast(value):
    text = str(value).strip()
    if text == "":
        return ""
    if (text[0:1], text[-1:]) in {("'", "'"), ('"', '"')} and len(text) >= 2:
        return text[1:-1]
    lowered = text.lower()
    if lowered in {"true", "t", "yes", "y", "on", "enabled"}:
        return True
    if lowered in {"false", "f", "no", "n", "off", "disabled"}:
        return False
    if lowered in {"none", "null", "nil"}:
        return None
    if re.fullmatch(r"[+-]?\d+", text):
        try:
            return int(text)
        except Exception:
            pass
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?", text) and (
        "." in text or "e" in lowered
    ):
        try:
            return float(text)
        except Exception:
            pass
    if (text.startswith("[") and text.endswith("]")) or (
        text.startswith("{") and text.endswith("}")
    ):
        return _parse_container_literal(text)
    return value


def _parse_container_literal(text):
    try:
        return _normalize_container(json.loads(text))
    except Exception:
        pass
    try:
        return _normalize_container(ast.literal_eval(text))
    except Exception as exc:
        raise SettingsError("invalid container literal") from exc


def _normalize_container(value):
    if _is_mapping(value):
        return _normalize_mapping(value, auto_cast=False, explicit_only=True)
    if isinstance(value, list):
        return [_normalize_container(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_container(item) for item in value]
    return value


def _read_file_mapping(path, *, env=None, environments=False, silent=True):
    file_path = Path(path)
    if not file_path.exists():
        if silent:
            return {}
        raise SettingsError(f"settings file not found: {path}")
    try:
        suffix = file_path.suffix.lower()
        if file_path.stat().st_size == 0:
            data = {}
        elif suffix == ".json":
            with file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not _is_mapping(data):
                raise SettingsError("JSON settings root must be an object")
            data = _normalize_mapping(data, auto_cast=False, explicit_only=True)
        elif suffix == ".toml":
            data = _load_toml(file_path)
            data = _normalize_mapping(data, auto_cast=False, explicit_only=True)
        elif suffix == ".ini":
            data = _load_ini(file_path)
            data = _normalize_mapping(data, auto_cast=False, explicit_only=True)
        elif suffix in {".yaml", ".yml"}:
            data = _load_yaml(file_path)
            data = _normalize_mapping(data, auto_cast=False, explicit_only=True)
        elif suffix == ".py":
            data = _load_py(file_path)
            data = _normalize_mapping(data, auto_cast=False, explicit_only=True)
        else:
            raise SettingsError(f"unsupported settings file format: {suffix}")
        if environments:
            data = _select_environment(data, env)
        return data
    except SettingsError:
        raise
    except Exception as exc:
        raise SettingsError(f"could not load settings file: {path}") from exc


def _load_toml(path):
    if tomllib is not None:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    return _parse_simple_toml(path.read_text(encoding="utf-8"))


def _parse_simple_toml(text):
    root = {}
    current = root
    for raw_line in text.splitlines():
        line = _strip_comment(raw_line).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            parts = _path_parts(line[1:-1])
            current = root
            for part in parts:
                current = current.setdefault(part, {})
            continue
        if "=" not in line:
            raise SettingsError("malformed TOML")
        key, value = line.split("=", 1)
        _assign_path(current, _path_parts(key.strip()), _auto_cast(value.strip()))
    return root


def _load_ini(path):
    parser = configparser.ConfigParser()
    parser.optionxform = str
    with path.open("r", encoding="utf-8") as handle:
        parser.read_file(handle)
    result = {}
    for key, value in parser.defaults().items():
        _assign_path(result, _path_parts(key), _auto_cast(value))
    for section in parser.sections():
        section_map = {}
        for key, value in parser.items(section, raw=True):
            if key in parser.defaults():
                continue
            _assign_path(section_map, _path_parts(key), _auto_cast(value))
        _assign_path(result, _path_parts(section), section_map)
    return result


def _load_yaml(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    root = {}
    stack = [(-1, root)]
    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line_no_comment = _strip_comment(raw_line.rstrip())
        if not line_no_comment.strip():
            continue
        indent = len(line_no_comment) - len(line_no_comment.lstrip(" "))
        line = line_no_comment.strip()
        if ":" not in line:
            raise SettingsError("malformed YAML")
        key, raw_value = line.split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise SettingsError("malformed YAML indentation")
        parent = stack[-1][1]
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value == "":
            child = {}
            _assign_path(parent, _path_parts(key), child)
            child = _get_path(parent, _path_parts(key))
            stack.append((indent, child))
        else:
            _assign_path(parent, _path_parts(key), _auto_cast(raw_value))
    return root


def _strip_comment(line):
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def _load_py(path):
    namespace = {}
    code = path.read_text(encoding="utf-8")
    exec(compile(code, str(path), "exec"), {"__builtins__": __builtins__}, namespace)
    return {
        key: value
        for key, value in namespace.items()
        if key.isupper() and not key.startswith("_")
    }


def _select_environment(data, env):
    env_name = str(env or os.environ.get("ENV_FOR_DYNACONF") or "default").upper()
    result = {}
    upper_data = _normalize_mapping(data, auto_cast=False, explicit_only=True)
    if "DEFAULT" in upper_data and _is_mapping(upper_data["DEFAULT"]):
        _merge_dicts(result, upper_data["DEFAULT"])
    if env_name != "DEFAULT" and env_name in upper_data and _is_mapping(upper_data[env_name]):
        _merge_dicts(result, upper_data[env_name])
    if result:
        return result
    if any(key.lower() in _ENV_NAMES for key in upper_data):
        return result
    return upper_data


def _parse_env_file(path, *, silent=True):
    file_path = Path(path)
    if not file_path.exists():
        if silent:
            return {}
        raise SettingsError(f"env file not found: {path}")
    result = {}
    try:
        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                raise SettingsError("malformed dotenv line")
            key, value = line.split("=", 1)
            key = key.strip()
            value = _strip_comment(value.strip()).strip()
            result[key] = value
        return result
    except SettingsError:
        raise
    except Exception as exc:
        raise SettingsError(f"could not load env file: {path}") from exc


def _env_mapping(env_values, prefix):
    prefix_text = "" if prefix is None else str(prefix)
    result = {}
    marker = prefix_text.upper() + "_" if prefix_text else ""
    for key, value in env_values.items():
        key_text = str(key)
        if marker and not key_text.upper().startswith(marker):
            continue
        logical = key_text[len(marker) :] if marker else key_text
        parts = _path_parts(logical)
        if not parts:
            continue
        _assign_path(result, parts, _normalize_value(value, auto_cast=True))
    return result


class _SettingsView:
    def __init__(self, data):
        object.__setattr__(self, "_data", data)

    def get(self, key, default=None, cast=None):
        parts = _path_parts(key)
        value = _get_path(self._data, parts, _MISSING)
        if value is _MISSING:
            return default
        value = _view_or_copy(value, self._data, parts)
        if cast is not None:
            return _cast_for_get(value, cast)
        return value

    def exists(self, key):
        return _exists_path(self._data, _path_parts(key))

    def as_dict(self):
        return _deepcopy(self._data)

    def __getitem__(self, key):
        parts = _path_parts(key)
        value = _get_path(self._data, parts)
        return _view_or_copy(value, self._data, parts)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


class _SettingsProxy:
    def __init__(self, owner, parts):
        object.__setattr__(self, "_owner", owner)
        object.__setattr__(self, "_parts", tuple(parts))

    def _value(self):
        return _get_path(self._owner._data, list(self._parts))

    def get(self, key=None, default=None, cast=None):
        parts = list(self._parts)
        if key is not None:
            parts.extend(_path_parts(key))
        value = _get_path(self._owner._data, parts, _MISSING)
        if value is _MISSING:
            return default
        value = _view_or_copy(value, self._owner._data, parts, self._owner)
        if cast is not None:
            return _cast_for_get(value, cast)
        return value

    def exists(self, key=None):
        parts = list(self._parts)
        if key is not None:
            parts.extend(_path_parts(key))
        return _exists_path(self._owner._data, parts)

    def as_dict(self):
        return _deepcopy(self._value())

    def __getitem__(self, key):
        parts = list(self._parts)
        parts.extend(_path_parts(key))
        value = _get_path(self._owner._data, parts)
        return _view_or_copy(value, self._owner._data, parts, self._owner)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __contains__(self, key):
        return self.exists(key)

    def __iter__(self):
        return iter(self._value())

    def __len__(self):
        return len(self._value())

    def __repr__(self):
        return repr(self.as_dict())

    def __eq__(self, other):
        if isinstance(other, _SettingsProxy):
            other = other.as_dict()
        return self.as_dict() == other


def _view_or_copy(value, root, parts, owner=None):
    if _is_mapping(value):
        if owner is not None:
            return _SettingsProxy(owner, parts)
        return _SettingsView(value)
    return _deepcopy(value)


def _cast_for_get(value, cast):
    if cast in (str, "str"):
        return str(value)
    if cast in (int, "int"):
        return int(value)
    if cast in (float, "float"):
        return float(value)
    if cast in (bool, "bool"):
        if isinstance(value, bool):
            return value
        return _cast_bool(value)
    if cast in ("json", json):
        if isinstance(value, str):
            return json.loads(value)
        return _deepcopy(value)
    if cast in ("none", None):
        return None
    if callable(cast):
        return cast(value)
    raise SettingsError("unknown cast")


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
        object.__setattr__(self, "_settings_files", _as_list(settings_files))
        object.__setattr__(self, "_defaults", _deepcopy(defaults or {}))
        object.__setattr__(self, "_envvar_prefix", envvar_prefix)
        object.__setattr__(self, "_environments", bool(environments))
        object.__setattr__(self, "_env", env)
        object.__setattr__(self, "_secrets_files", _as_list(secrets_files))
        object.__setattr__(self, "_validators", list(validators or []))
        object.__setattr__(self, "_load_dotenv", bool(load_dotenv))
        object.__setattr__(self, "_loaded_files", [])
        object.__setattr__(self, "_loaded_env_files", [])
        object.__setattr__(self, "_runtime", {})
        object.__setattr__(self, "_deleted", set())
        object.__setattr__(self, "_validator_defaults", {})
        object.__setattr__(self, "_data", {})
        if load_dotenv:
            default_env = Path(".env")
            if default_env.exists():
                self._loaded_env_files.append(str(default_env))
        data = self._build_data(include_runtime=True)
        validator_defaults = {}
        self._run_validators(data, self._validators, validator_defaults)
        object.__setattr__(self, "_validator_defaults", validator_defaults)
        object.__setattr__(self, "_data", data)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __getitem__(self, key):
        parts = _path_parts(key)
        value = _get_path(self._data, parts)
        return _view_or_copy(value, self._data, parts, self)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self.set(name, value)

    def __delattr__(self, name):
        if name.startswith("_"):
            object.__delattr__(self, name)
        else:
            self.delete(name)

    def __contains__(self, key):
        return self.exists(key)

    def get(self, key, default=None, cast=None):
        value = _get_path(self._data, _path_parts(key), _MISSING)
        if value is _MISSING:
            return default
        value = _view_or_copy(value, self._data, _path_parts(key), self)
        if cast is not None:
            return _cast_for_get(value, cast)
        return value

    def exists(self, key):
        return _exists_path(self._data, _path_parts(key))

    def set(self, key, value, *, validate=False):
        runtime = _deepcopy(self._runtime)
        normalized = _normalize_value(value, auto_cast=False, explicit_only=True)
        _assign_path(runtime, _path_parts(key), normalized)
        self._commit_runtime(runtime, self._deleted, validate=validate)
        return self

    def update(self, mapping, *, validate=False):
        runtime = _deepcopy(self._runtime)
        _merge_dicts(runtime, _normalize_mapping(mapping, auto_cast=False, explicit_only=True))
        self._commit_runtime(runtime, self._deleted, validate=validate)
        return self

    def delete(self, key):
        parts = tuple(_path_parts(key))
        runtime = _deepcopy(self._runtime)
        _delete_path(runtime, list(parts))
        deleted = set(self._deleted)
        deleted.add(parts)
        self._commit_runtime(runtime, deleted, validate=False)
        return self

    def import_dict(self, mapping, *, validate=True, replace=False):
        normalized = _normalize_mapping(mapping, auto_cast=False, explicit_only=True)
        runtime = normalized if replace else _deepcopy(self._runtime)
        if not replace:
            _merge_dicts(runtime, normalized)
        self._commit_runtime(runtime, set() if replace else self._deleted, validate=validate)
        return self

    def as_dict(self):
        return _deepcopy(self._data)

    def export(self, path=None):
        data = self.as_dict()
        if path is not None:
            with Path(path).open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
        return data

    def load_file(self, path, *, env=None, silent=True):
        if silent and not Path(path).exists():
            return self
        loaded = _read_file_mapping(
            path,
            env=self._env if env is None else env,
            environments=self._environments,
            silent=silent,
        )
        loaded_files = list(self._loaded_files)
        loaded_files.append((str(path), env))
        data = self._build_data(
            include_runtime=True,
            loaded_files=loaded_files,
            preloaded_file=(str(path), env, loaded),
        )
        validator_defaults = _deepcopy(self._validator_defaults)
        self._run_validators(data, self._validators, validator_defaults)
        object.__setattr__(self, "_loaded_files", loaded_files)
        object.__setattr__(self, "_validator_defaults", validator_defaults)
        object.__setattr__(self, "_data", data)
        return self

    def load_env_file(self, path, *, silent=True):
        if silent and not Path(path).exists():
            return self
        env_values = _parse_env_file(path, silent=silent)
        loaded_env_files = list(self._loaded_env_files)
        loaded_env_files.append(str(path))
        data = self._build_data(
            include_runtime=True,
            loaded_env_files=loaded_env_files,
            preloaded_env=(str(path), env_values),
        )
        validator_defaults = _deepcopy(self._validator_defaults)
        self._run_validators(data, self._validators, validator_defaults)
        object.__setattr__(self, "_loaded_env_files", loaded_env_files)
        object.__setattr__(self, "_validator_defaults", validator_defaults)
        object.__setattr__(self, "_data", data)
        return self

    def reload(self):
        data = self._build_data(
            include_runtime=False,
            runtime={},
            deleted=set(),
            validator_defaults={},
        )
        validator_defaults = {}
        self._run_validators(data, self._validators, validator_defaults)
        object.__setattr__(self, "_runtime", {})
        object.__setattr__(self, "_deleted", set())
        object.__setattr__(self, "_validator_defaults", validator_defaults)
        object.__setattr__(self, "_data", data)
        return self

    def configure(self, **kwargs):
        state = self._snapshot_state()
        try:
            if "settings_files" in kwargs:
                object.__setattr__(self, "_settings_files", _as_list(kwargs["settings_files"]))
            if "defaults" in kwargs:
                object.__setattr__(self, "_defaults", _deepcopy(kwargs["defaults"] or {}))
            if "envvar_prefix" in kwargs:
                object.__setattr__(self, "_envvar_prefix", kwargs["envvar_prefix"])
            if "environments" in kwargs:
                object.__setattr__(self, "_environments", bool(kwargs["environments"]))
            if "env" in kwargs:
                object.__setattr__(self, "_env", kwargs["env"])
            if "secrets_files" in kwargs:
                object.__setattr__(self, "_secrets_files", _as_list(kwargs["secrets_files"]))
            if "validators" in kwargs:
                object.__setattr__(self, "_validators", list(kwargs["validators"] or []))
            if "load_dotenv" in kwargs:
                object.__setattr__(self, "_load_dotenv", bool(kwargs["load_dotenv"]))
            loaded_env_files = []
            if self._load_dotenv and Path(".env").exists():
                loaded_env_files.append(str(Path(".env")))
            object.__setattr__(self, "_loaded_files", [])
            object.__setattr__(self, "_loaded_env_files", loaded_env_files)
            object.__setattr__(self, "_runtime", {})
            object.__setattr__(self, "_deleted", set())
            object.__setattr__(self, "_validator_defaults", {})
            data = self._build_data(include_runtime=False, validator_defaults={})
            validator_defaults = {}
            self._run_validators(data, self._validators, validator_defaults)
            object.__setattr__(self, "_validator_defaults", validator_defaults)
            object.__setattr__(self, "_data", data)
        except Exception:
            self._restore_state(state)
            raise
        return self

    def register_validator(self, validator):
        self._validators.append(validator)
        return self

    def validate(self, key=None):
        validators = self._validators
        if key is not None:
            target = ".".join(_path_parts(key))
            validators = [
                validator
                for validator in self._validators
                if ".".join(_path_parts(validator.name)) == target
            ]
        data = _deepcopy(self._data)
        validator_defaults = _deepcopy(self._validator_defaults)
        self._run_validators(data, validators, validator_defaults)
        object.__setattr__(self, "_validator_defaults", validator_defaults)
        object.__setattr__(self, "_data", data)
        return True

    def _commit_runtime(self, runtime, deleted, *, validate=False):
        data = self._build_data(include_runtime=True, runtime=runtime, deleted=deleted)
        validator_defaults = _deepcopy(self._validator_defaults)
        if validate:
            self._run_validators(data, self._validators, validator_defaults)
        object.__setattr__(self, "_runtime", runtime)
        object.__setattr__(self, "_deleted", set(deleted))
        object.__setattr__(self, "_validator_defaults", validator_defaults)
        object.__setattr__(self, "_data", data)

    def _build_data(
        self,
        *,
        include_runtime,
        runtime=None,
        deleted=None,
        loaded_files=None,
        loaded_env_files=None,
        preloaded_file=None,
        preloaded_env=None,
        validator_defaults=None,
    ):
        runtime = self._runtime if runtime is None else runtime
        deleted = self._deleted if deleted is None else deleted
        loaded_files = self._loaded_files if loaded_files is None else loaded_files
        loaded_env_files = (
            self._loaded_env_files if loaded_env_files is None else loaded_env_files
        )
        validator_defaults = (
            self._validator_defaults
            if validator_defaults is None
            else validator_defaults
        )
        data = _normalize_mapping(self._defaults, auto_cast=False, explicit_only=True)
        for path in self._settings_files:
            _merge_dicts(
                data,
                _read_file_mapping(
                    path,
                    env=self._env,
                    environments=self._environments,
                    silent=True,
                ),
            )
        preloaded_file_key = None
        if preloaded_file is not None:
            preloaded_file_key = (preloaded_file[0], preloaded_file[1])
        for entry in loaded_files:
            path, env = entry if isinstance(entry, tuple) else (entry, None)
            if preloaded_file_key == (path, env):
                loaded = preloaded_file[2]
            else:
                loaded = _read_file_mapping(
                    path,
                    env=self._env if env is None else env,
                    environments=self._environments,
                    silent=False,
                )
            _merge_dicts(data, loaded)
        _merge_dicts(data, _env_mapping(os.environ, self._envvar_prefix))
        preloaded_env_path = preloaded_env[0] if preloaded_env is not None else None
        for path in loaded_env_files:
            values = preloaded_env[1] if path == preloaded_env_path else _parse_env_file(path, silent=False)
            _merge_dicts(data, _env_mapping(values, self._envvar_prefix))
        for path in self._secrets_files:
            _merge_dicts(
                data,
                _read_file_mapping(
                    path,
                    env=self._env,
                    environments=self._environments,
                    silent=True,
                ),
            )
        _apply_missing(data, validator_defaults)
        if include_runtime:
            for parts in deleted:
                _delete_path(data, list(parts))
            _merge_dicts(data, runtime)
        return data

    def _run_validators(self, data, validators, validator_defaults=None):
        view = _SettingsView(data)
        for validator in validators:
            parts = _path_parts(validator.name)
            exists = _exists_path(data, parts)
            if not exists and validator.has_default:
                default = _normalize_value(
                    validator.default, auto_cast=False, explicit_only=True
                )
                _assign_path(data, parts, default)
                if validator_defaults is not None:
                    _assign_path(validator_defaults, parts, default)
                exists = True
            if not exists:
                if validator.required:
                    raise ValidationError(f"{validator.name} is required")
                continue
            value = _get_path(data, parts)
            self._check_validator(validator, value, view)

    def _check_validator(self, validator, value, view):
        name = validator.name
        if validator.is_type_of is not None and not isinstance(value, validator.is_type_of):
            raise ValidationError(f"{name} failed type validation")
        checks = [
            (validator.eq is not None, lambda: value == validator.eq, "eq"),
            (validator.ne is not None, lambda: value != validator.ne, "ne"),
            (validator.gt is not None, lambda: value > validator.gt, "gt"),
            (validator.gte is not None, lambda: value >= validator.gte, "gte"),
            (validator.lt is not None, lambda: value < validator.lt, "lt"),
            (validator.lte is not None, lambda: value <= validator.lte, "lte"),
        ]
        for enabled, predicate, label in checks:
            if enabled:
                try:
                    ok = predicate()
                except Exception as exc:
                    raise ValidationError(f"{name} failed {label} validation") from exc
                if not ok:
                    raise ValidationError(f"{name} failed {label} validation")
        if validator.condition is not None:
            try:
                ok = validator.condition(value, view)
            except Exception as exc:
                raise ValidationError(f"{name} failed condition validation") from exc
            if not ok:
                raise ValidationError(f"{name} failed condition validation")

    def _snapshot_state(self):
        return {
            "_settings_files": _deepcopy(self._settings_files),
            "_defaults": _deepcopy(self._defaults),
            "_envvar_prefix": self._envvar_prefix,
            "_environments": self._environments,
            "_env": self._env,
            "_secrets_files": _deepcopy(self._secrets_files),
            "_validators": list(self._validators),
            "_load_dotenv": self._load_dotenv,
            "_loaded_files": _deepcopy(self._loaded_files),
            "_loaded_env_files": _deepcopy(self._loaded_env_files),
            "_runtime": _deepcopy(self._runtime),
            "_deleted": set(self._deleted),
            "_validator_defaults": _deepcopy(self._validator_defaults),
            "_data": _deepcopy(self._data),
        }

    def _restore_state(self, state):
        for key, value in state.items():
            object.__setattr__(self, key, value)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)):
        return [str(value)]
    return [str(item) for item in value]


__all__ = ["MiniDynaconf", "Validator", "ValidationError", "SettingsError"]
