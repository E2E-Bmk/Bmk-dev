import copy
import configparser
import json
import os
import runpy
import tomllib
from pathlib import Path


class SettingsError(Exception):
    pass


class ValidationError(SettingsError):
    pass


MISSING = object()


def _parts(key):
    if isinstance(key, str):
        return [p.upper() for p in key.replace("__", ".").split(".") if p]
    raise SettingsError("key must be a string")


def _deepcopy(value):
    return copy.deepcopy(value)


def _deep_merge(base, incoming):
    for key, value in incoming.items():
        key = key.upper()
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = _deepcopy(value)
    return base


def _delete_parts(data, parts):
    cur = data
    for part in parts[:-1]:
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return bool(isinstance(cur, dict) and cur.pop(parts[-1], MISSING) is not MISSING)


def _set_path(data, key, value):
    cur = data
    ps = _parts(key)
    for part in ps[:-1]:
        cur = cur.setdefault(part, {})
        if not isinstance(cur, dict):
            raise SettingsError("cannot set nested key through scalar")
    cur[ps[-1]] = _deepcopy(value)


def _get_path(data, key, default=MISSING):
    cur = data
    for part in _parts(key):
        if not isinstance(cur, dict) or part not in cur:
            if default is MISSING:
                raise KeyError(key)
            return default
        cur = cur[part]
    return cur


def _del_path(data, key):
    return _delete_parts(data, _parts(key))


def _normalize(value):
    if isinstance(value, dict):
        return {str(k).upper(): _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def _auto_cast(value):
    if not isinstance(value, str):
        return value
    raw = value.strip()
    low = raw.lower()
    explicit = None
    for token in ("@int", "@float", "@bool", "@json", "@none", "@str"):
        if low.startswith(token + " "):
            explicit = token
            raw = raw[len(token):].strip()
            break
    try:
        if explicit == "@str":
            return raw
        if explicit == "@int":
            return int(raw)
        if explicit == "@float":
            return float(raw)
        if explicit == "@bool":
            if raw.lower() in {"true", "1", "yes", "on"}:
                return True
            if raw.lower() in {"false", "0", "no", "off"}:
                return False
            raise ValueError(raw)
        if explicit == "@json":
            return _normalize(json.loads(raw))
        if explicit == "@none":
            if raw.lower() in {"", "none", "null", "~"}:
                return None
            raise ValueError(raw)
        if low in {"true", "yes", "on"}:
            return True
        if low in {"false", "no", "off"}:
            return False
        if low in {"none", "null", "~"}:
            return None
        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            return raw[1:-1]
        if raw.startswith("[") or raw.startswith("{"):
            return _normalize(json.loads(raw))
        try:
            return int(raw)
        except ValueError:
            try:
                return float(raw)
            except ValueError:
                return raw
    except Exception as exc:
        raise SettingsError("invalid cast") from exc


def _cast_tree(value):
    if isinstance(value, dict):
        return {str(k).upper(): _cast_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_cast_tree(v) for v in value]
    return _auto_cast(value)


def _parse_simple_yaml(text):
    root = {}
    stack = [(0, root)]
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.strip().partition(":")
        while stack and indent < stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]
        if value.strip() == "":
            child = {}
            cur[key] = child
            stack.append((indent + 2, child))
        else:
            cur[key] = value.strip()
    return root


def _load_file(path):
    path = Path(path)
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if suffix == ".toml":
            return tomllib.loads(path.read_text(encoding="utf-8"))
        if suffix == ".ini":
            cp = configparser.ConfigParser()
            cp.read(path, encoding="utf-8")
            return {section: dict(cp[section]) for section in cp.sections()}
        if suffix in {".yaml", ".yml"}:
            return _parse_simple_yaml(path.read_text(encoding="utf-8"))
        if suffix == ".py":
            ns = runpy.run_path(str(path))
            return {k: v for k, v in ns.items() if k.isupper()}
    except Exception as exc:
        raise SettingsError(f"malformed file: {path}") from exc
    raise SettingsError(f"unsupported file type: {path}")


class Validator:
    def __init__(
        self,
        name,
        *,
        required=False,
        default=MISSING,
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

    def apply(self, settings):
        if not settings.exists(self.name):
            if self.default is not MISSING:
                settings.set(self.name, self.default)
            elif self.required:
                raise ValidationError(self.name)
            else:
                return
        value = settings.get(self.name)
        if self.is_type_of is not None and not isinstance(value, self.is_type_of):
            raise ValidationError(self.name)
        checks = [
            (self.eq is None or value == self.eq),
            (self.ne is None or value != self.ne),
            (self.gt is None or value > self.gt),
            (self.gte is None or value >= self.gte),
            (self.lt is None or value < self.lt),
            (self.lte is None or value <= self.lte),
            (self.condition is None or bool(self.condition(value, settings))),
        ]
        if not all(checks):
            raise ValidationError(self.name)


class _Box:
    def __init__(self, settings, prefix):
        object.__setattr__(self, "_settings", settings)
        object.__setattr__(self, "_prefix", prefix)

    def __getattr__(self, item):
        value = self._settings.get(self._prefix + "." + item)
        if isinstance(value, dict):
            return _Box(self._settings, self._prefix + "." + item)
        return value

    def __getitem__(self, item):
        return self._settings.get(self._prefix + "." + item)


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
        self.settings_files = self._as_list(settings_files)
        self.defaults = defaults or {}
        self.envvar_prefix = envvar_prefix
        self.environments = environments
        self.env = env or os.environ.get("ENV_FOR_DYNACONF") or "default"
        self.secrets_files = self._as_list(secrets_files)
        self.validators = list(validators or [])
        self._extra_files = []
        self._dotenv_env = {}
        self._base = {}
        self._runtime = {}
        self._deleted = set()
        self._data = {}
        self.reload()

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, (str, os.PathLike)):
            return [value]
        return list(value)

    def _snapshot(self):
        return (
            list(self.settings_files),
            _deepcopy(self.defaults),
            self.envvar_prefix,
            self.environments,
            self.env,
            list(self.secrets_files),
            list(self.validators),
            _deepcopy(self._base),
            _deepcopy(self._runtime),
            set(self._deleted),
            _deepcopy(self._data),
            list(self._extra_files),
            dict(self._dotenv_env),
        )

    def _restore(self, snapshot):
        (
            self.settings_files,
            self.defaults,
            self.envvar_prefix,
            self.environments,
            self.env,
            self.secrets_files,
            self.validators,
            self._base,
            self._runtime,
            self._deleted,
            self._data,
            self._extra_files,
            self._dotenv_env,
        ) = snapshot

    def _merge_mapping(self, target, mapping):
        _deep_merge(target, _cast_tree(_normalize(mapping)))

    def _load_file_mapping(self, path, env=None):
        mapping = _normalize(_load_file(path))
        if self.environments:
            selected = {}
            if "DEFAULT" in mapping:
                _deep_merge(selected, mapping["DEFAULT"])
            active = (env or self.env).upper()
            if active in mapping:
                _deep_merge(selected, mapping[active])
            mapping = selected
        return _cast_tree(_normalize(mapping))

    def _load_env(self, target, environ):
        prefix = (self.envvar_prefix + "_").upper()
        for key, value in environ.items():
            if key.upper().startswith(prefix):
                logical = key[len(prefix):].replace("__", ".")
                _set_path(target, logical, _auto_cast(value))

    def _build_base(self):
        base = {}
        self._merge_mapping(base, self.defaults)
        for path in [*self.settings_files, *self._extra_files]:
            if Path(path).exists():
                _deep_merge(base, self._load_file_mapping(path))
        self._load_env(base, os.environ)
        self._load_env(base, self._dotenv_env)
        for path in self.secrets_files:
            if Path(path).exists():
                _deep_merge(base, self._load_file_mapping(path))
        return base

    def _clear_deleted_for(self, key):
        parts = tuple(_parts(key))
        self._deleted = {
            existing
            for existing in self._deleted
            if not (
                existing == parts
                or existing[: len(parts)] == parts
                or parts[: len(existing)] == existing
            )
        }

    def _clear_deleted_for_mapping(self, mapping, prefix=()):
        for key, value in mapping.items():
            parts = prefix + tuple(_parts(str(key)))
            self._clear_deleted_for(".".join(parts))
            if isinstance(value, dict):
                self._clear_deleted_for_mapping(value, parts)

    def _compose(self):
        data = _deepcopy(self._base)
        _deep_merge(data, self._runtime)
        for parts in sorted(self._deleted, key=len):
            _delete_parts(data, parts)
        self._data = data

    def _rebuild(self, *, keep_runtime):
        self._base = self._build_base()
        if not keep_runtime:
            self._runtime = {}
            self._deleted = set()
        self._compose()
        self.validate()

    def reload(self):
        old = self._snapshot()
        try:
            self._rebuild(keep_runtime=False)
        except Exception:
            self._restore(old)
            raise
        return self

    def configure(self, **kwargs):
        old = self._snapshot()
        for key, value in kwargs.items():
            setattr(self, key, self._as_list(value) if key.endswith("_files") else value)
        self._extra_files = []
        self._dotenv_env = {}
        try:
            self._rebuild(keep_runtime=False)
        except Exception:
            self._restore(old)
            raise
        return self

    def load_file(self, path, *, env=None, silent=True):
        if not Path(path).exists():
            if silent:
                return False
            raise SettingsError(path)
        old = _deepcopy(self._data)
        snapshot = self._snapshot()
        try:
            _load_file(path)
            self._extra_files.append(path)
            self._base = self._build_base()
            if env is not None:
                _deep_merge(self._base, self._load_file_mapping(path, env=env))
            self._compose()
            self.validate()
            return True
        except Exception:
            self._restore(snapshot)
            self._data = old
            raise

    def load_env_file(self, path):
        env = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("'\"")
        old = self._snapshot()
        try:
            self._dotenv_env.update(env)
            self._base = self._build_base()
            self._compose()
            self.validate()
        except Exception:
            self._restore(old)
            raise

    def register_validator(self, validator):
        self.validators.append(validator)

    def validate(self, key=None):
        old = self._snapshot()
        try:
            for validator in self.validators:
                if key is None or _parts(validator.name) == _parts(key):
                    validator.apply(self)
        except Exception:
            self._restore(old)
            raise

    def get(self, key, default=None, cast=None):
        value = _get_path(self._data, key, default)
        if cast is not None and value is not default:
            return cast(value) if callable(cast) else _auto_cast(f"@{cast} {value}")
        return value

    def exists(self, key):
        try:
            _get_path(self._data, key)
            return True
        except KeyError:
            return False

    def set(self, key, value, *, validate=False):
        old = self._snapshot()
        try:
            self._clear_deleted_for(key)
            _set_path(self._runtime, key, _auto_cast(value))
            self._compose()
            if validate:
                self.validate()
        except Exception:
            self._restore(old)
            raise

    def update(self, mapping, *, validate=False):
        old = self._snapshot()
        try:
            self._clear_deleted_for_mapping(mapping)
            self._merge_mapping(self._runtime, mapping)
            self._compose()
            if validate:
                self.validate()
        except Exception:
            self._restore(old)
            raise

    def delete(self, key, *, validate=False):
        old = self._snapshot()
        try:
            existed = self.exists(key)
            _del_path(self._runtime, key)
            self._deleted.add(tuple(_parts(key)))
            self._compose()
            if validate:
                self.validate()
            return existed
        except Exception:
            self._restore(old)
            raise

    def import_dict(self, mapping, *, validate=True, replace=False):
        old = self._snapshot()
        try:
            if replace:
                self._runtime = {}
                self._deleted = set()
            else:
                self._clear_deleted_for_mapping(mapping)
            self._merge_mapping(self._runtime, mapping)
            self._compose()
            if validate:
                self.validate()
            return self
        except Exception:
            self._restore(old)
            raise

    def as_dict(self):
        return _deepcopy(self._data)

    def export(self, path=None):
        data = self.as_dict()
        if path is not None:
            Path(path).write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        return data

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getattr__(self, item):
        value = self.get(item, MISSING)
        if value is MISSING:
            raise AttributeError(item)
        if isinstance(value, dict):
            return _Box(self, item)
        return value
