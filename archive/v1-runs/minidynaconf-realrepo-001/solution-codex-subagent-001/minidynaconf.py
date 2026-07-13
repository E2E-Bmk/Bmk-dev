"""A small dependency-free layered settings module."""

from __future__ import annotations

import ast
import configparser
import copy
import json
import os
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except Exception:  # pragma: no cover - old interpreters
    tomllib = None


_MISSING = object()


class SettingsError(Exception):
    """Raised for settings loading, casting, or mutation errors."""


class ValidationError(SettingsError):
    """Raised when a validator fails."""


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
        object.__setattr__(self, "_data", {})
        object.__setattr__(self, "_validators", list(validators or []))
        object.__setattr__(self, "_dotenv_files", [])
        object.__setattr__(
            self,
            "_options",
            {
                "settings_files": _as_list(settings_files),
                "defaults": copy.deepcopy(defaults or {}),
                "envvar_prefix": envvar_prefix,
                "environments": bool(environments),
                "env": env,
                "secrets_files": _as_list(secrets_files),
                "load_dotenv": bool(load_dotenv),
            },
        )
        self.reload()

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        value = self.get(name, _MISSING)
        if value is _MISSING:
            raise AttributeError(name)
        return value

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self.set(name, value)

    def __getitem__(self, key):
        value = self.get(key, _MISSING)
        if value is _MISSING:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return self.exists(key)

    def get(self, key, default=None, cast=None):
        value = _get_path(self._data, key, _MISSING)
        if value is _MISSING:
            return default
        value = _public_value(value)
        if cast is None:
            return value
        return _apply_get_cast(value, cast)

    def set(self, key, value, *, validate=False):
        new_data = copy.deepcopy(self._data)
        _set_path(new_data, key, _normalize_programmatic(value))
        if validate:
            self._validate_data(new_data)
        object.__setattr__(self, "_data", new_data)

    def update(self, mapping, *, validate=False):
        new_data = copy.deepcopy(self._data)
        _merge_dict(new_data, _normalize_mapping(mapping))
        if validate:
            self._validate_data(new_data)
        object.__setattr__(self, "_data", new_data)

    def exists(self, key):
        return _get_path(self._data, key, _MISSING) is not _MISSING

    def delete(self, key):
        new_data = copy.deepcopy(self._data)
        removed = _delete_path(new_data, key)
        object.__setattr__(self, "_data", new_data)
        return removed

    def as_dict(self):
        return copy.deepcopy(self._data)

    def reload(self):
        opts = copy.deepcopy(self._options)
        new_data = {}
        _merge_dict(new_data, _normalize_mapping(opts.get("defaults") or {}))
        for path in opts.get("settings_files") or []:
            loaded = self._load_file_to_mapping(path, env=opts.get("env"), silent=True)
            _merge_dict(new_data, loaded)
        _merge_dict(new_data, self._load_env_mapping(os.environ))
        if opts.get("load_dotenv"):
            for path in self._dotenv_files:
                _merge_dict(new_data, self._read_dotenv_mapping(path, silent=True))
        for path in opts.get("secrets_files") or []:
            loaded = self._load_file_to_mapping(path, env=opts.get("env"), silent=True)
            _merge_dict(new_data, loaded)
        self._validate_data(new_data)
        object.__setattr__(self, "_data", new_data)

    def configure(self, **kwargs):
        allowed = {
            "settings_files",
            "defaults",
            "envvar_prefix",
            "environments",
            "env",
            "secrets_files",
            "validators",
            "load_dotenv",
        }
        unknown = set(kwargs) - allowed
        if unknown:
            raise SettingsError("Unknown configuration option: %s" % ", ".join(sorted(unknown)))
        old_options = copy.deepcopy(self._options)
        old_validators = list(self._validators)
        old_data = copy.deepcopy(self._data)
        try:
            opts = copy.deepcopy(self._options)
            for name, value in kwargs.items():
                if name in {"settings_files", "secrets_files"}:
                    opts[name] = _as_list(value)
                elif name == "defaults":
                    opts[name] = copy.deepcopy(value or {})
                elif name == "validators":
                    object.__setattr__(self, "_validators", list(value or []))
                else:
                    opts[name] = value
            object.__setattr__(self, "_options", opts)
            self.reload()
        except Exception:
            object.__setattr__(self, "_options", old_options)
            object.__setattr__(self, "_validators", old_validators)
            object.__setattr__(self, "_data", old_data)
            raise

    def load_file(self, path, *, env=None, silent=True):
        loaded = self._load_file_to_mapping(path, env=env, silent=silent)
        new_data = copy.deepcopy(self._data)
        _merge_dict(new_data, loaded)
        self._validate_data(new_data)
        object.__setattr__(self, "_data", new_data)

    def load_env_file(self, path):
        loaded = self._read_dotenv_mapping(path, silent=False)
        old_files = list(self._dotenv_files)
        old_data = copy.deepcopy(self._data)
        try:
            self._dotenv_files.append(str(path))
            if self._options.get("load_dotenv"):
                self.reload()
            else:
                new_data = copy.deepcopy(self._data)
                _merge_dict(new_data, loaded)
                self._validate_data(new_data)
                object.__setattr__(self, "_data", new_data)
        except Exception:
            object.__setattr__(self, "_dotenv_files", old_files)
            object.__setattr__(self, "_data", old_data)
            raise

    def register_validator(self, validator):
        self._validators.append(validator)

    def validate(self, key=None):
        new_data = copy.deepcopy(self._data)
        self._validate_data(new_data, key=key)
        object.__setattr__(self, "_data", new_data)

    def _active_env(self, env=None):
        return (env or self._options.get("env") or os.environ.get("ENV_FOR_DYNACONF") or "default").lower()

    def _load_file_to_mapping(self, path, *, env=None, silent=True):
        path = Path(path)
        if not path.exists():
            if silent:
                return {}
            raise SettingsError("Settings file not found: %s" % path)
        try:
            raw = _parse_file(path)
            if raw is None:
                raw = {}
            if not isinstance(raw, dict):
                raise SettingsError("Settings file must contain a mapping: %s" % path)
            if self._options.get("environments"):
                raw = _select_environment(raw, self._active_env(env))
            return _normalize_mapping(raw, cast_strings=True)
        except SettingsError:
            raise
        except Exception as exc:
            raise SettingsError("Could not load settings file %s: %s" % (path, exc)) from exc

    def _load_env_mapping(self, environ):
        prefix = self._options.get("envvar_prefix")
        if prefix is None or prefix == "":
            marker = ""
        else:
            marker = str(prefix).upper() + "_"
        data = {}
        for key, value in environ.items():
            env_key = str(key)
            if marker:
                if not env_key.upper().startswith(marker):
                    continue
                logical = env_key[len(marker) :].replace("__", ".")
            else:
                logical = env_key.replace("__", ".")
            if not logical:
                continue
            _set_path(data, logical, _cast_value(value))
        return data

    def _read_dotenv_mapping(self, path, silent):
        path = Path(path)
        if not path.exists():
            if silent:
                return {}
            raise SettingsError("Dotenv file not found: %s" % path)
        env_pairs = {}
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                if "=" not in line:
                    continue
                name, value = line.split("=", 1)
                name = name.strip()
                value = value.strip()
                if _is_quoted(value):
                    value = value[1:-1]
                else:
                    value = _strip_inline_comment(value).strip()
                env_pairs[name] = value
        except Exception as exc:
            raise SettingsError("Could not load dotenv file %s: %s" % (path, exc)) from exc
        return self._load_env_mapping(env_pairs)

    def _validate_data(self, data, key=None):
        selected = self._validators
        if key is not None:
            want = _norm_path(key)
            selected = [validator for validator in selected if _norm_path(validator.name) == want]
        for validator in selected:
            value = _get_path(data, validator.name, _MISSING)
            if value is _MISSING:
                if validator.default is not None:
                    _set_path(data, validator.name, _normalize_programmatic(validator.default))
                    value = _get_path(data, validator.name, _MISSING)
                elif validator.required:
                    raise ValidationError("Validation failed for %s: required" % validator.name)
                else:
                    continue
            self._run_validator_checks(validator, value, data)

    def _run_validator_checks(self, validator, value, data):
        settings_view = _SettingsView(data)
        checks = [
            (validator.is_type_of is not None and not isinstance(value, validator.is_type_of), "type"),
            (validator.eq is not None and value != validator.eq, "eq"),
            (validator.ne is not None and value == validator.ne, "ne"),
            (validator.gt is not None and not (value > validator.gt), "gt"),
            (validator.gte is not None and not (value >= validator.gte), "gte"),
            (validator.lt is not None and not (value < validator.lt), "lt"),
            (validator.lte is not None and not (value <= validator.lte), "lte"),
        ]
        for failed, label in checks:
            if failed:
                raise ValidationError("Validation failed for %s: %s" % (validator.name, label))
        if validator.condition is not None and not validator.condition(value, settings_view):
            raise ValidationError("Validation failed for %s: condition" % validator.name)


class _SettingsView:
    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        value = self.get(name, _MISSING)
        if value is _MISSING:
            raise AttributeError(name)
        return value

    def __getitem__(self, key):
        value = self.get(key, _MISSING)
        if value is _MISSING:
            raise KeyError(key)
        return value

    def get(self, key, default=None):
        value = _get_path(self._data, key, _MISSING)
        return default if value is _MISSING else _public_value(value)

    def exists(self, key):
        return _get_path(self._data, key, _MISSING) is not _MISSING

    def as_dict(self):
        return copy.deepcopy(self._data)


class _AttrDict(dict):
    def __getattr__(self, name):
        value = self.get(name, _MISSING)
        if value is _MISSING:
            raise AttributeError(name)
        return value

    def __getitem__(self, key):
        value = _get_path(self, key, _MISSING)
        if value is _MISSING:
            raise KeyError(key)
        return value

    def get(self, key, default=None):
        value = _get_path(self, key, _MISSING)
        return default if value is _MISSING else value

    def exists(self, key):
        return _get_path(self, key, _MISSING) is not _MISSING

    def __contains__(self, key):
        return _get_path(self, key, _MISSING) is not _MISSING


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)):
        return [str(value)]
    return [str(item) for item in value]


def _key(key):
    return str(key).upper()


def _norm_path(path):
    if isinstance(path, (list, tuple)):
        parts = path
    else:
        parts = str(path).replace("__", ".").split(".")
    return ".".join(_key(part) for part in parts if str(part) != "")


def _path_parts(path):
    normalized = _norm_path(path)
    return [part for part in normalized.split(".") if part]


def _get_path(data, path, default=_MISSING):
    current = data
    for part in _path_parts(path):
        if not isinstance(current, dict) or not dict.__contains__(current, part):
            return default
        current = dict.__getitem__(current, part)
    return current


def _set_path(data, path, value):
    parts = _path_parts(path)
    if not parts:
        raise SettingsError("Empty setting key")
    current = data
    for part in parts[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    last = parts[-1]
    if isinstance(value, dict) and isinstance(current.get(last), dict):
        _merge_dict(current[last], value)
    else:
        current[last] = copy.deepcopy(value)


def _delete_path(data, path):
    parts = _path_parts(path)
    if not parts:
        return False
    current = data
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    if isinstance(current, dict) and parts[-1] in current:
        del current[parts[-1]]
        return True
    return False


def _merge_dict(target, source):
    for key, value in (source or {}).items():
        nkey = _key(key)
        if isinstance(value, dict) and isinstance(target.get(nkey), dict):
            _merge_dict(target[nkey], value)
        else:
            target[nkey] = copy.deepcopy(value)
    return target


def _normalize_mapping(mapping, cast_strings=False):
    if mapping is None:
        return {}
    if not isinstance(mapping, dict):
        raise SettingsError("Expected a mapping")
    result = {}
    for key, value in mapping.items():
        if isinstance(key, str) and "." in key:
            _set_path(result, key, _normalize_value(value, cast_strings=cast_strings))
        else:
            result[_key(key)] = _normalize_value(value, cast_strings=cast_strings)
    return result


def _normalize_value(value, cast_strings=False):
    if isinstance(value, dict):
        return _normalize_mapping(value, cast_strings=cast_strings)
    if isinstance(value, list):
        return [_normalize_value(item, cast_strings=cast_strings) for item in value]
    if isinstance(value, tuple):
        return [_normalize_value(item, cast_strings=cast_strings) for item in value]
    if cast_strings and isinstance(value, str):
        return _cast_value(value)
    if not cast_strings and isinstance(value, str) and _has_explicit_cast(value):
        return _cast_value(value)
    return copy.deepcopy(value)


def _normalize_programmatic(value):
    return _normalize_value(value, cast_strings=False)


def _public_value(value):
    if isinstance(value, dict):
        return _AttrDict({key: _public_value(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    return copy.deepcopy(value)


def _is_quoted(text):
    return len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}


def _cast_value(value):
    if not isinstance(value, str):
        return _normalize_value(value, cast_strings=True)
    text = value.strip()
    if text == "":
        return "" if value == "" else text
    lowered = text.lower()
    for token in ("@int", "@float", "@bool", "@json", "@none", "@str"):
        if lowered == token or lowered.startswith(token + " ") or lowered.startswith(token + ":"):
            rest = text[len(token) :].lstrip()
            if rest.startswith(":"):
                rest = rest[1:].lstrip()
            return _explicit_cast(token, rest)
    if _is_quoted(text):
        return text[1:-1]
    if lowered in {"true", "yes", "y", "on"}:
        return True
    if lowered in {"false", "no", "n", "off"}:
        return False
    if lowered in {"none", "null", "nil", "~"}:
        return None
    if _looks_int(text):
        try:
            return int(text, 10)
        except ValueError:
            pass
    if _looks_float(text):
        try:
            return float(text)
        except ValueError:
            pass
    if (text.startswith("[") and text.endswith("]")) or (text.startswith("{") and text.endswith("}")):
        try:
            return _normalize_value(json.loads(text), cast_strings=True)
        except Exception:
            try:
                return _normalize_value(ast.literal_eval(text), cast_strings=True)
            except Exception as exc:
                raise SettingsError("Invalid collection literal") from exc
    return text


def _has_explicit_cast(text):
    lowered = text.strip().lower()
    return any(
        lowered == token or lowered.startswith(token + " ") or lowered.startswith(token + ":")
        for token in ("@int", "@float", "@bool", "@json", "@none", "@str")
    )


def _explicit_cast(token, value):
    try:
        if token == "@str":
            return value
        if token == "@none":
            if value.strip() and value.strip().lower() not in {"none", "null", "nil", "~"}:
                raise ValueError("invalid none cast")
            return None
        if token == "@int":
            return int(value.strip(), 10)
        if token == "@float":
            return float(value.strip())
        if token == "@bool":
            lowered = value.strip().lower()
            if lowered in {"true", "yes", "y", "on", "1"}:
                return True
            if lowered in {"false", "no", "n", "off", "0"}:
                return False
            raise ValueError("invalid bool cast")
        if token == "@json":
            return _normalize_value(json.loads(value), cast_strings=True)
    except SettingsError:
        raise
    except Exception as exc:
        raise SettingsError("Invalid explicit cast %s" % token) from exc
    raise SettingsError("Unknown explicit cast %s" % token)


def _apply_get_cast(value, cast):
    if cast in (str, int, float, bool):
        if cast is bool and isinstance(value, str):
            result = _cast_value("@bool " + value)
            if not isinstance(result, bool):
                raise SettingsError("Invalid bool cast")
            return result
        return cast(value)
    if cast in ("@str", "str"):
        return str(value)
    if cast in ("@int", "int"):
        return int(value)
    if cast in ("@float", "float"):
        return float(value)
    if cast in ("@bool", "bool"):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return _explicit_cast("@bool", value)
        return bool(value)
    if cast in ("@json", "json"):
        if isinstance(value, str):
            return _explicit_cast("@json", value)
        return copy.deepcopy(value)
    if cast in ("@none", "none"):
        return None
    if callable(cast):
        return cast(value)
    raise SettingsError("Unsupported cast")


def _looks_int(text):
    body = text[1:] if text[:1] in "+-" else text
    return body.isdigit()


def _looks_float(text):
    body = text[1:] if text[:1] in "+-" else text
    if not body:
        return False
    lowered = body.lower()
    if lowered in {"inf", "infinity", "nan"}:
        return False
    return any(ch in body for ch in ".eE") and _float_chars(body)


def _float_chars(body):
    allowed = set("0123456789.eE+-")
    return all(ch in allowed for ch in body)


def _parse_file(path):
    suffix = path.suffix.lower()
    if path.stat().st_size == 0:
        return {}
    if suffix == ".json":
        text = path.read_text(encoding="utf-8").strip()
        return {} if not text else json.loads(text)
    if suffix == ".toml":
        if tomllib is None:
            return _parse_simple_toml(path.read_text(encoding="utf-8"))
        with path.open("rb") as fh:
            return tomllib.load(fh)
    if suffix == ".ini":
        parser = configparser.ConfigParser()
        parser.optionxform = str
        with path.open(encoding="utf-8") as fh:
            parser.read_file(fh)
        data = {}
        for key, value in parser.defaults().items():
            data[key] = value
        for section in parser.sections():
            data[section] = dict(parser.items(section, raw=True))
        return data
    if suffix in {".yaml", ".yml"}:
        return _parse_yaml_subset(path.read_text(encoding="utf-8"))
    if suffix == ".py":
        namespace = {}
        code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
        exec(code, {"__builtins__": __builtins__}, namespace)
        return {key: value for key, value in namespace.items() if key.isupper() and not key.startswith("_")}
    raise SettingsError("Unsupported settings file format: %s" % suffix)


def _parse_simple_toml(text):
    data = {}
    current = data
    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            current = data
            for part in section.split("."):
                current = current.setdefault(part.strip(), {})
            continue
        if "=" not in line:
            raise SettingsError("Malformed TOML line")
        key, value = line.split("=", 1)
        current[key.strip()] = _cast_value(value.strip())
    return data


def _parse_yaml_subset(text):
    root = {}
    stack = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = _strip_inline_comment(raw_line.rstrip())
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise SettingsError("Malformed YAML line")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _cast_value(value)
    return root


def _strip_inline_comment(text):
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(text):
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
            return text[:index]
    return text


def _select_environment(raw, active_env):
    normalized = {_key(key): value for key, value in raw.items()}
    result = {}
    default = normalized.get("DEFAULT")
    if isinstance(default, dict):
        _merge_dict(result, _normalize_mapping(default, cast_strings=True))
    active = normalized.get(_key(active_env))
    if isinstance(active, dict):
        _merge_dict(result, _normalize_mapping(active, cast_strings=True))
    elif active_env != "default" and not result and active is None:
        pass
    if not result and "DEFAULT" not in normalized and _key(active_env) not in normalized:
        return raw
    return result
