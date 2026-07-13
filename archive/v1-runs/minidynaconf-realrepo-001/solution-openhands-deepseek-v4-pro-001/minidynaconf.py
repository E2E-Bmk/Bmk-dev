"""
MiniDynaconf - A dependency-free Python module for layered application configuration.

Inspired by Dynaconf's public configuration-management model: settings can come from
defaults, configuration files, environment variables, secrets files, and runtime
overrides, then be accessed through one settings object.

Uses only the Python standard library.
"""

import os
import json
import copy
import configparser
import re
import importlib.util

__all__ = ["MiniDynaconf", "Validator", "ValidationError", "SettingsError"]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SettingsError(Exception):
    """Raised for configuration loading errors, invalid casts, malformed files."""


class ValidationError(Exception):
    """Raised when a Validator check fails."""


# ---------------------------------------------------------------------------
# Key normalization: all keys stored and looked up as UPPERCASE
# ---------------------------------------------------------------------------

def _nk(key):
    """Normalize a single key segment to uppercase."""
    return key.upper()


def _normalize_keys(d):
    """Deep-normalize all string keys in a dict to uppercase."""
    if not isinstance(d, dict):
        return d
    result = {}
    for k, v in d.items():
        nk = k.upper() if isinstance(k, str) else k
        result[nk] = _normalize_keys(v)
    return result


# ---------------------------------------------------------------------------
# Deep merge
# ---------------------------------------------------------------------------

def _deep_merge(base, override):
    """Merge *override* into *base* recursively in-place. Returns base."""
    for key, value in override.items():
        nk = key.upper() if isinstance(key, str) else key
        if nk in base and isinstance(base[nk], dict) and isinstance(value, dict):
            _deep_merge(base[nk], value)
        else:
            base[nk] = value
    return base


def _deep_copy(obj):
    """Deep copy arbitrary structure."""
    return copy.deepcopy(obj)


# ---------------------------------------------------------------------------
# Type casting
# ---------------------------------------------------------------------------

# Matches @type tokens at the beginning of a value string
_EXPLICIT_CAST_RE = re.compile(r'^@(int|float|bool|json|none|str)\s*(.*)', re.IGNORECASE)

# Used for auto-detection of booleans in text sources
_BOOL_TRUE = frozenset({'true', 't', 'yes', 'y', 'on', '1'})
_BOOL_FALSE = frozenset({'false', 'f', 'no', 'n', 'off', '0'})
_NONE_TOKENS = frozenset({'none', 'null', 'nil'})


def _cast_value(value):
    """Cast a string value from a text source to the appropriate Python type.

    Auto-detection is applied for unambiguous cases.
    Explicit @type tokens take precedence.
    """
    if not isinstance(value, str):
        return value  # already a Python value

    # Check for explicit cast token
    m = _EXPLICIT_CAST_RE.match(value)
    if m:
        return _explicit_cast(m.group(1).lower(), m.group(2))

    # Try auto-detection

    # Quoted string (single or double)
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    # None/null
    if value.lower() in _NONE_TOKENS:
        return None

    # Boolean
    lower = value.lower()
    if lower in _BOOL_TRUE:
        return True
    if lower in _BOOL_FALSE:
        return False

    # Integer
    if re.match(r'^[+-]?\d+$', value):
        try:
            return int(value)
        except ValueError:
            pass

    # Float
    if re.match(r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$', value):
        try:
            return float(value)
        except ValueError:
            pass

    # JSON array or object
    stripped = value.strip()
    if (stripped.startswith('[') and stripped.endswith(']')) or \
       (stripped.startswith('{') and stripped.endswith('}')):
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

    # Fall through: plain string
    return value


def _explicit_cast(token, text):
    """Apply an explicit @type cast."""
    text = text.strip()
    if token == 'int':
        try:
            if not text:
                raise SettingsError("@int requires a value")
            return int(text)
        except ValueError as e:
            raise SettingsError(f"@int cast failed: {text}") from e
    elif token == 'float':
        try:
            if not text:
                raise SettingsError("@float requires a value")
            return float(text)
        except ValueError as e:
            raise SettingsError(f"@float cast failed: {text}") from e
    elif token == 'bool':
        lower = text.strip().lower()
        if lower in _BOOL_TRUE:
            return True
        if lower in _BOOL_FALSE:
            return False
        raise SettingsError(f"@bool cast failed: {text}")
    elif token == 'json':
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError) as e:
            raise SettingsError(f"@json cast failed: {text}") from e
    elif token == 'none':
        return None
    elif token == 'str':
        return text
    raise SettingsError(f"Unknown cast token: @{token}")


# ---------------------------------------------------------------------------
# File type detection
# ---------------------------------------------------------------------------

def _file_type(path):
    """Determine file format from extension."""
    ext = os.path.splitext(path)[1].lower()
    return {
        '.toml': 'toml',
        '.ini': 'ini',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.py': 'py',
    }.get(ext)


# ---------------------------------------------------------------------------
# Minimal TOML parser (stdlib-only)
# ---------------------------------------------------------------------------

def _parse_toml(text):
    """Parse a practical subset of TOML.

    Supports: key = value pairs, [section] and [section.sub], arrays,
    inline tables, basic strings, literal strings, integers, floats, booleans.
    """
    lines = text.splitlines()
    result = {}
    current = result
    current_path = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip blank lines and comments
        if not line or line.startswith('#'):
            i += 1
            continue

        # Section header
        if line.startswith('[') and ']' in line:
            # Handle multi-line arrays of tables [[...]]
            section_raw = line[1:].split(']')[0].strip()
            keys = [k.strip() for k in section_raw.split('.')]
            current_path = keys
            current = result
            for key in keys:
                if key not in current or not isinstance(current[key], dict):
                    current[key] = {}
                current = current[key]
            i += 1
            continue

        # Key = value
        if '=' in line:
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()

            # Handle multi-line arrays
            if value == '[' and not value.endswith(']'):
                # Multi-line array
                arr = []
                i += 1
                while i < len(lines):
                    sub = lines[i].strip()
                    if sub == ']':
                        break
                    if sub.endswith(','):
                        sub = sub[:-1].strip()
                    if sub:
                        arr.append(_toml_value(sub))
                    i += 1
                current[key] = arr
                i += 1
                continue

            parsed = _toml_value(value)
            current[key] = parsed

        i += 1

    return _normalize_keys(result)


def _toml_value(raw):
    """Parse a single TOML value."""
    raw = raw.strip()

    # Inline array
    if raw.startswith('[') and raw.endswith(']'):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_toml_value(v) for v in _split_comma(inner)]

    # Inline table
    if raw.startswith('{') and raw.endswith('}'):
        inner = raw[1:-1].strip()
        if not inner:
            return {}
        result = {}
        for pair in _split_comma(inner):
            k, _, v = pair.partition('=')
            result[k.strip()] = _toml_value(v.strip())
        return result

    # Boolean
    lower = raw.lower()
    if lower == 'true':
        return True
    if lower == 'false':
        return False

    # Float
    if re.match(r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$', raw):
        # Check it's not a bare integer first
        if '.' in raw or 'e' in raw.lower():
            return float(raw)

    # Integer
    if re.match(r'^[+-]?\d+$', raw):
        return int(raw)

    # Basic string (double-quoted)
    if raw.startswith('"') and raw.endswith('"'):
        return _unescape_toml_string(raw[1:-1])

    # Literal string (single-quoted)
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]

    # Unquoted string
    return raw


def _unescape_toml_string(s):
    """Unescape TOML basic string escape sequences."""
    s = s.replace('\\n', '\n')
    s = s.replace('\\t', '\t')
    s = s.replace('\\r', '\r')
    s = s.replace('\\"', '"')
    s = s.replace('\\\\', '\\')
    return s


def _split_comma(s):
    """Split on commas, respecting nested brackets and braces."""
    parts = []
    depth = 0
    current = []
    for ch in s:
        if ch in '{[(':
            depth += 1
        elif ch in '}])':
            depth -= 1
        elif ch == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
            continue
        current.append(ch)
    if current:
        parts.append(''.join(current).strip())
    return parts


# ---------------------------------------------------------------------------
# Minimal YAML parser (stdlib-only, practical subset)
# ---------------------------------------------------------------------------

def _parse_yaml(text):
    """Parse a practical subset of YAML.

    Supports: indentation-based mappings, nested mappings, flow sequences [a, b],
    flow mappings {k: v}, and scalar values (strings, numbers, booleans, null).
    """
    lines = text.splitlines()
    result = {}

    # Filter out empty and comment-only lines
    filtered = []
    for line in lines:
        stripped = line.strip()
        if stripped == '' or stripped.startswith('#'):
            filtered.append(None)
        else:
            filtered.append(line)

    return _parse_yaml_block(filtered, 0, result)[0]


def _parse_yaml_block(lines, start_idx, result):
    """Parse a YAML block starting at start_idx with current indentation context."""
    i = start_idx
    indent_stack = [(0, result)]  # (indent, dict)

    while i < len(lines):
        line = lines[i]
        if line is None:
            i += 1
            continue

        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        # Pop stack to find the parent dict for this indentation level
        while len(indent_stack) > 1 and indent <= indent_stack[-1][0]:
            indent_stack.pop()

        current_dict = indent_stack[-1][1]

        # Key-value pair
        if ':' in stripped:
            key, colon, value = _split_yaml_kv(stripped)
            if colon is None:
                i += 1
                continue

            if value:
                parsed = _yaml_value(value)
                current_dict[key] = parsed
            else:
                new_dict = {}
                current_dict[key] = new_dict
                indent_stack.append((indent, new_dict))

        i += 1

    return result, i


def _split_yaml_kv(line):
    """Split a YAML line into key and value, respecting quotes and brackets."""
    in_single = False
    in_double = False
    depth = 0
    for idx, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch in '{[(':
            depth += 1
        elif ch in '}])':
            depth -= 1
        elif ch == ':' and not in_single and not in_double and depth == 0:
            key = line[:idx].strip()
            value = line[idx + 1:].strip()
            return key, ':', value
    return line, None, None


def _yaml_value(raw):
    """Parse a YAML scalar or flow value."""
    raw = raw.strip()

    # Flow sequence [a, b, c]
    if raw.startswith('[') and raw.endswith(']'):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return [_yaml_value(v) for v in _split_comma(inner)]

    # Flow mapping {k: v, ...}
    if raw.startswith('{') and raw.endswith('}'):
        inner = raw[1:-1].strip()
        if not inner:
            return {}
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            result = {}
            for pair in _split_comma(inner):
                k, _, v = pair.partition(':')
                result[k.strip()] = _yaml_value(v.strip())
            return result

    # Quoted string
    if (raw.startswith('"') and raw.endswith('"')) or \
       (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]

    # Null
    lower = raw.lower()
    if lower in ('null', 'none', 'nil', '~'):
        return None

    # Boolean
    if lower in ('true', 'yes', 'on'):
        return True
    if lower in ('false', 'no', 'off'):
        return False

    # Float
    if re.match(r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$', raw):
        if '.' in raw or 'e' in raw.lower():
            try:
                return float(raw)
            except ValueError:
                pass

    # Integer
    if re.match(r'^[+-]?\d+$', raw):
        try:
            return int(raw)
        except ValueError:
            pass

    return raw


# ---------------------------------------------------------------------------
# INI parsing (uses configparser)
# ---------------------------------------------------------------------------

def _parse_ini(text):
    """Parse an INI file, returning a dict of sections."""
    p = configparser.ConfigParser()
    p.read_string(text)
    result = {}
    for section in p.sections():
        result[section] = dict(p.items(section))
    return _normalize_keys(result)


# ---------------------------------------------------------------------------
# Dotenv parsing
# ---------------------------------------------------------------------------

def _parse_dotenv(text):
    """Parse a .env file (KEY=VALUE pairs, one per line)."""
    result = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' not in stripped:
            continue
        key, _, value = stripped.partition('=')
        key = key.strip()
        value = value.strip()

        # Strip optional surrounding quotes
        if len(value) >= 2:
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

        result[key] = value
    return result


# ---------------------------------------------------------------------------
# Settings file loading
# ---------------------------------------------------------------------------

def _load_py_file(path):
    """Execute a Python settings file in an isolated namespace.

    Returns public uppercase variables.
    """
    namespace = {}
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    exec(code, namespace)
    return {k: v for k, v in namespace.items()
            if k.isupper() and not k.startswith('_')}


def _load_file_content(path):
    """Load and parse a single settings file based on its extension."""
    fmt = _file_type(path)
    if fmt is None:
        return {}

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if fmt == 'json':
        if not content.strip():
            return {}
        return _normalize_keys(json.loads(content))
    elif fmt == 'toml':
        if not content.strip():
            return {}
        return _parse_toml(content)
    elif fmt == 'yaml':
        if not content.strip():
            return {}
        return _parse_yaml(content)
    elif fmt == 'ini':
        return _parse_ini(content)
    elif fmt == 'py':
        return _load_py_file(path)

    return {}


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class Validator:
    """Describes a validation rule for one logical key.

    Parameters:
        name: The dotted key name to validate.
        required: If True, validation fails when the key is missing.
        default: If set, and the key is missing, the default is applied before checks.
        is_type_of: A type or tuple of types the value must be an instance of.
        eq: Value must equal this.
        ne: Value must not equal this.
        gt: Value must be greater than this.
        gte: Value must be greater than or equal to this.
        lt: Value must be less than this.
        lte: Value must be less than or equal to this.
        condition: A callable(value, settings) -> bool.
        messages: Optional dict of custom error messages.
    """

    def __init__(self, name, *, required=False, default=None, is_type_of=None,
                 eq=None, ne=None, gt=None, gte=None, lt=None, lte=None,
                 condition=None, messages=None):
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

    def check(self, settings):
        """Run this validator against a settings object.

        Returns True if valid, raises ValidationError otherwise.
        """
        exists = settings.exists(self.name)

        # Handle missing key
        if not exists:
            if self.default is not None:
                settings.set(self.name, self.default, validate=False)
                value = self.default
            elif self.required:
                raise ValidationError(
                    self.messages.get('required',
                                      f"Key '{self.name}' is required but not set"))
            else:
                # Not required, no default, nothing to check
                return True
        else:
            value = settings.get(self.name)

        # Type check
        if self.is_type_of is not None:
            if not isinstance(value, self.is_type_of):
                raise ValidationError(
                    self.messages.get('is_type_of',
                                      f"Key '{self.name}' must be of type "
                                      f"{self.is_type_of}, got {type(value).__name__}"))

        # Comparisons (skip None values since they can't be compared meaningfully)
        if value is not None:
            if self.eq is not None and not (value == self.eq):
                raise ValidationError(
                    self.messages.get('eq',
                                      f"Key '{self.name}' must equal {self.eq!r}, "
                                      f"got {value!r}"))
            if self.ne is not None and value == self.ne:
                raise ValidationError(
                    self.messages.get('ne',
                                      f"Key '{self.name}' must not equal {self.ne!r}"))
            if self.gt is not None and not (value > self.gt):
                raise ValidationError(
                    self.messages.get('gt',
                                      f"Key '{self.name}' must be > {self.gt!r}, "
                                      f"got {value!r}"))
            if self.gte is not None and not (value >= self.gte):
                raise ValidationError(
                    self.messages.get('gte',
                                      f"Key '{self.name}' must be >= {self.gte!r}, "
                                      f"got {value!r}"))
            if self.lt is not None and not (value < self.lt):
                raise ValidationError(
                    self.messages.get('lt',
                                      f"Key '{self.name}' must be < {self.lt!r}, "
                                      f"got {value!r}"))
            if self.lte is not None and not (value <= self.lte):
                raise ValidationError(
                    self.messages.get('lte',
                                      f"Key '{self.name}' must be <= {self.lte!r}, "
                                      f"got {value!r}"))

        # Custom condition
        if self.condition is not None:
            try:
                if not self.condition(value, settings):
                    raise ValidationError(
                        self.messages.get('condition',
                                          f"Key '{self.name}' failed custom condition"))
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(
                    self.messages.get('condition',
                                      f"Key '{self.name}' condition raised: {e}")) from e

        return True


# ---------------------------------------------------------------------------
# MiniDynaconf
# ---------------------------------------------------------------------------

class MiniDynaconf:
    """Dependency-free layered application configuration.

    Construct with:
        settings_files: Path or list of paths to settings files.
        defaults: Dict of default values.
        envvar_prefix: Prefix for environment variable detection (default "APP").
        environments: If True, files may contain named environment sections.
        env: Active environment name for switching.
        secrets_files: Path or list of paths to secrets files.
        validators: List of Validator instances.
        load_dotenv: If True, load .env files via load_env_file.
    """

    _SENTINEL = object()

    def __init__(self, settings_files=None, defaults=None, envvar_prefix="APP",
                 environments=False, env=None, secrets_files=None,
                 validators=None, load_dotenv=False):
        # Store configuration for reload
        self._config = {
            'settings_files': self._normalize_path_list(settings_files),
            'defaults': _deep_copy(defaults) if defaults else {},
            'envvar_prefix': envvar_prefix,
            'environments': environments,
            'env': env,
            'secrets_files': self._normalize_path_list(secrets_files),
            'validators': list(validators) if validators else [],
            'load_dotenv': load_dotenv,
        }
        self._validators = self._config['validators']

        # The canonical settings store
        self._store = {}

        # Load everything
        self._load_all()

    # ---- Internal helpers ----

    @staticmethod
    def _normalize_path_list(value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def _load_all(self):
        """Full load sequence: defaults -> files -> env -> secrets -> validate."""
        self._store = {}

        # 1. Load defaults
        if self._config['defaults']:
            self._store = _deep_copy(_normalize_keys(self._config['defaults']))

        # 2. Load settings files
        self._load_settings_files()

        # 3. Load environment variables
        self._load_environment_variables()

        # 4. Load secrets files
        self._load_secrets_files()

        # 5. Run constructor validators
        self._run_validators()

    def _load_settings_files(self):
        """Load all configured settings files in order."""
        for path in self._config['settings_files']:
            if not os.path.exists(path):
                continue
            try:
                data = _load_file_content(path)
            except Exception as e:
                raise SettingsError(f"Error loading settings file {path}: {e}") from e

            if self._config['environments']:
                data = self._extract_environment(data)

            _deep_merge(self._store, data)

    def _extract_environment(self, data):
        """When environments=True, extract the active environment from file data.

        Sections in data are treated as environment names. 'default' is loaded
        first, then the active environment overrides. Non-dict top-level keys
        are preserved as global settings.
        """
        if not data or not isinstance(data, dict):
            return data

        # Determine active environment
        active_env = self._config['env']
        if active_env is None:
            active_env = os.environ.get('ENV_FOR_DYNACONF', 'default')
        if active_env is None:
            active_env = 'default'

        active_env = active_env.lower()

        result = {}

        # Include non-section top-level keys as global settings
        for key, value in data.items():
            if not isinstance(value, dict):
                result[_nk(key)] = value

        # Load 'default' first
        for key, value in data.items():
            if key.lower() == 'default' and isinstance(value, dict):
                _deep_merge(result, _normalize_keys(value))

        # Load active environment (overrides default)
        for key, value in data.items():
            if key.lower() == active_env.lower() and isinstance(value, dict):
                _deep_merge(result, _normalize_keys(value))

        return result

    def _load_environment_variables(self):
        """Load environment variables with the configured prefix."""
        prefix = self._config['envvar_prefix'] + '_'
        prefix_len = len(prefix)

        env_vars = {}
        for key, value in os.environ.items():
            if key.upper().startswith(prefix.upper()):
                logical_key = key[prefix_len:]
                # Double underscore -> dot for nesting
                logical_key = logical_key.replace('__', '.')
                # Cast the value
                try:
                    env_vars[logical_key] = _cast_value(value)
                except SettingsError:
                    raise
                except Exception as e:
                    raise SettingsError(
                        f"Error casting env var {key}: {e}") from e

        # Merge into store
        self._merge_dotted(env_vars)

    def _load_secrets_files(self):
        """Load secrets files."""
        for path in self._config['secrets_files']:
            if not os.path.exists(path):
                continue
            try:
                data = _load_file_content(path)
            except Exception as e:
                raise SettingsError(f"Error loading secrets file {path}: {e}") from e

            if self._config['environments']:
                data = self._extract_environment(data)

            _deep_merge(self._store, data)

    def _merge_dotted(self, flat_dict):
        """Merge a flat dict with dotted keys into the nested store."""
        for dotted_key, value in flat_dict.items():
            self._set_dotted(dotted_key, value)

    def _set_dotted(self, dotted_key, value):
        """Set a dotted key path in the store, merging nested dicts."""
        parts = dotted_key.split('.')
        current = self._store
        for i, part in enumerate(parts[:-1]):
            nk = _nk(part)
            # Find case-insensitive match
            actual_key = nk
            for existing in list(current.keys()):
                if existing.upper() == nk:
                    actual_key = existing
                    break
            if actual_key not in current or not isinstance(current[actual_key], dict):
                current[actual_key] = {}
            current = current[actual_key]
        last_nk = _nk(parts[-1])
        actual_key = last_nk
        for existing in list(current.keys()):
            if existing.upper() == last_nk:
                actual_key = existing
                break
        # Recursive merge when both existing and new are dicts
        if (actual_key in current and isinstance(current[actual_key], dict)
                and isinstance(value, dict)):
            _deep_merge(current[actual_key], _normalize_keys(value))
        else:
            current[actual_key] = value

    def _get_dotted(self, dotted_key):
        """Get a value by dotted key path. Returns (value, True) or (None, False)."""
        parts = dotted_key.split('.')
        current = self._store
        for part in parts:
            nk = _nk(part)
            found = False
            for existing_key in current:
                if existing_key.upper() == nk:
                    current = current[existing_key]
                    found = True
                    break
            if not found:
                return None, False
        return current, True

    def _delete_dotted(self, dotted_key):
        """Delete a value by dotted key path. Returns True if deleted."""
        parts = dotted_key.split('.')
        current = self._store
        for i, part in enumerate(parts[:-1]):
            nk = _nk(part)
            found = False
            for existing_key in current:
                if existing_key.upper() == nk:
                    current = current[existing_key]
                    found = True
                    break
            if not found or not isinstance(current, dict):
                return False
        last_nk = _nk(parts[-1])
        for existing_key in list(current.keys()):
            if existing_key.upper() == last_nk:
                del current[existing_key]
                return True
        return False

    def _run_validators(self):
        """Run all registered validators. Raises ValidationError on failure."""
        # Run on a snapshot to ensure atomicity
        snapshot = _deep_copy(self._store)
        snapshot_settings = _SnapshotSettings(snapshot)
        real_snapshot_settings = _SnapshotSettings(snapshot)

        # Phase 1: Collect defaults to set
        defaults_to_apply = {}
        for v in self._validators:
            if not snapshot_settings.exists(v.name) and v.default is not None:
                defaults_to_apply[v.name] = v.default

        # Phase 2: Apply defaults to snapshot
        for key, value in defaults_to_apply.items():
            snapshot_settings.set(key, value, validate=False)

        # Phase 3: Check all validators
        for v in self._validators:
            v.check(snapshot_settings)

        # Phase 4: All passed - apply defaults to real store
        for key, value in defaults_to_apply.items():
            self._set_dotted(key, value)

    # ---- Public API ----

    # Attribute access (case-insensitive, dotted not supported for attrs)
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        value, found = self._get_dotted(name)
        if found:
            return value
        raise AttributeError(f"No setting '{name}'")

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self.set(name, value, validate=False)

    def __delattr__(self, name):
        if name.startswith('_'):
            super().__delattr__(name)
        else:
            self.delete(name)

    # Item access
    def __getitem__(self, key):
        value, found = self._get_dotted(key)
        if found:
            return value
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.set(key, value, validate=False)

    def __delitem__(self, key):
        if not self.delete(key):
            raise KeyError(key)

    def __contains__(self, key):
        return self.exists(key)

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    # Public methods

    def get(self, key, default=None, cast=None):
        """Get a setting by key with optional default and cast.

        Args:
            key: Dotted key name (case-insensitive).
            default: Value to return if key is missing.
            cast: A callable to cast the returned value (does not mutate stored value).

        Returns:
            The setting value, or *default* if the key is missing.
        """
        value, found = self._get_dotted(key)
        if not found:
            return default
        if cast is not None:
            try:
                return cast(value)
            except Exception as e:
                raise SettingsError(f"Cast failed for key '{key}': {e}") from e
        return value

    def set(self, key, value, *, validate=False):
        """Set a setting by dotted key.

        Args:
            key: Dotted key name (case-insensitive).
            value: The value to set.
            validate: If True, run validators after setting; roll back on failure.

        Raises:
            SettingsError: If validation fails.
        """
        if validate and self._validators:
            # Check on a snapshot
            snapshot = _deep_copy(self._store)
            snap = _SnapshotSettings(snapshot)
            snap.set(key, value, validate=False)
            try:
                for v in self._validators:
                    v.check(snap)
            except (ValidationError, Exception):
                raise
        self._set_dotted(key, value)

    def update(self, mapping, *, validate=False):
        """Update multiple settings from a mapping.

        Args:
            mapping: Dict or MiniDynaconf-like object with items().
            validate: If True, run validators after updating; roll back on failure.
        """
        if validate and self._validators:
            snapshot = _deep_copy(self._store)
            snap = _SnapshotSettings(snapshot)
            if hasattr(mapping, 'items'):
                for k, v in mapping.items():
                    snap.set(k, v, validate=False)
            else:
                for k, v in mapping:
                    snap.set(k, v, validate=False)
            try:
                for v in self._validators:
                    v.check(snap)
            except (ValidationError, Exception):
                raise

        if hasattr(mapping, 'items'):
            for k, v in mapping.items():
                self._set_dotted(k, v)
        else:
            for k, v in mapping:
                self._set_dotted(k, v)

    def exists(self, key):
        """Check if a setting key exists (is present, regardless of value)."""
        _, found = self._get_dotted(key)
        return found

    def delete(self, key):
        """Delete a setting by key. Returns True if the key existed."""
        return self._delete_dotted(key)

    def as_dict(self):
        """Return a deep copy of all settings as a dict."""
        return _deep_copy(self._store)

    def reload(self):
        """Rebuild settings from configured sources, discarding runtime assignments."""
        self._load_all()

    def configure(self, **kwargs):
        """Update configuration options and reload.

        Accepted kwargs:
            settings_files, defaults, envvar_prefix, environments, env,
            secrets_files, validators, load_dotenv
        """
        if 'settings_files' in kwargs:
            self._config['settings_files'] = self._normalize_path_list(
                kwargs['settings_files'])
        if 'defaults' in kwargs:
            self._config['defaults'] = _deep_copy(kwargs['defaults'])
        if 'envvar_prefix' in kwargs:
            self._config['envvar_prefix'] = kwargs['envvar_prefix']
        if 'environments' in kwargs:
            self._config['environments'] = kwargs['environments']
        if 'env' in kwargs:
            self._config['env'] = kwargs['env']
        if 'secrets_files' in kwargs:
            self._config['secrets_files'] = self._normalize_path_list(
                kwargs['secrets_files'])
        if 'validators' in kwargs:
            self._config['validators'] = list(kwargs['validators'])
            self._validators = self._config['validators']
        if 'load_dotenv' in kwargs:
            self._config['load_dotenv'] = kwargs['load_dotenv']

        self._load_all()

    def load_file(self, path, *, env=None, silent=True):
        """Load an additional settings file.

        Args:
            path: Path to the file.
            env: Optional environment name override for this file.
            silent: If True, missing files are ignored. Malformed files still raise.
        """
        if not os.path.exists(path):
            if silent:
                return
            raise SettingsError(f"Settings file not found: {path}")

        try:
            data = _load_file_content(path)
        except SettingsError:
            raise
        except Exception as e:
            raise SettingsError(f"Malformed settings file {path}: {e}") from e

        if self._config['environments'] or env:
            old_env = self._config['env']
            if env is not None:
                self._config['env'] = env
            data = self._extract_environment(data)
            self._config['env'] = old_env

        _deep_merge(self._store, data)

    def load_env_file(self, path):
        """Load a .env file (KEY=VALUE per line).

        Values follow the same prefix, nested-key, priority, and casting rules
        as process environment variables.
        """
        if not os.path.exists(path):
            return

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        raw = _parse_dotenv(content)
        prefix = self._config['envvar_prefix'] + '_'
        prefix_len = len(prefix)

        env_vars = {}
        for key, value in raw.items():
            if key.upper().startswith(prefix.upper()):
                logical_key = key[prefix_len:]
                logical_key = logical_key.replace('__', '.')
                env_vars[logical_key] = _cast_value(value)

        self._merge_dotted(env_vars)

    def register_validator(self, validator):
        """Add a Validator to the settings object."""
        self._validators.append(validator)
        self._config['validators'].append(validator)

    def validate(self, key=None):
        """Run validators.

        Args:
            key: If provided, run only validators for this key.
        """
        if key is not None:
            # Snapshot for atomicity
            snapshot = _deep_copy(self._store)
            snap = _SnapshotSettings(snapshot)
            # Collect defaults for this key
            defaults_to_apply = {}
            for v in self._validators:
                if v.name.lower() == key.lower():
                    if not snap.exists(v.name) and v.default is not None:
                        defaults_to_apply[v.name] = v.default
            for k, val in defaults_to_apply.items():
                snap.set(k, val, validate=False)
            for v in self._validators:
                if v.name.lower() == key.lower():
                    v.check(snap)
            # All passed, apply defaults
            for k, val in defaults_to_apply.items():
                self._set_dotted(k, val)
        else:
            self._run_validators()


# ---------------------------------------------------------------------------
# Internal helper: snapshot settings for atomic validation
# ---------------------------------------------------------------------------

class _SnapshotSettings:
    """A thin wrapper around a raw dict that supports the settings API
    needed by validators, without coupling to MiniDynaconf's full lifecycle.
    """

    def __init__(self, store):
        self._store = store

    def exists(self, key):
        parts = key.split('.')
        current = self._store
        for part in parts:
            nk = _nk(part)
            found = False
            for ek in current:
                if ek.upper() == nk:
                    current = current[ek]
                    found = True
                    break
            if not found:
                return False
        return True

    def get(self, key, default=None):
        parts = key.split('.')
        current = self._store
        for part in parts:
            nk = _nk(part)
            found = False
            for ek in current:
                if ek.upper() == nk:
                    current = current[ek]
                    found = True
                    break
            if not found:
                return default
        return current

    def set(self, key, value, validate=False):
        parts = key.split('.')
        current = self._store
        for i, part in enumerate(parts[:-1]):
            nk = _nk(part)
            actual = nk
            for ek in current:
                if ek.upper() == nk:
                    actual = ek
                    break
            if actual not in current or not isinstance(current[actual], dict):
                current[actual] = {}
            current = current[actual]
        last_nk = _nk(parts[-1])
        actual = last_nk
        for ek in current:
            if ek.upper() == last_nk:
                actual = ek
                break
        current[actual] = value
