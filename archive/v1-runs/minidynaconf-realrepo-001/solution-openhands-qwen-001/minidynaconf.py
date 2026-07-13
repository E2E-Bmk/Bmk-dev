"""
MiniDynaconf - A dependency-free Python module for layered application configuration.

Inspired by Dynaconf's public configuration-management model.
"""

import os
import re
import json
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable


class SettingsError(Exception):
    """Exception raised for settings-related errors."""
    pass


class ValidationError(Exception):
    """Exception raised for validation failures."""
    pass


class CaseInsensitiveDict(dict):
    """A dictionary that allows case-insensitive key access."""
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._store = {}
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
    
    def __setitem__(self, key, value):
        lower_key = key.lower() if isinstance(key, str) else key
        # Wrap nested dicts in CaseInsensitiveDict
        if isinstance(value, dict) and not isinstance(value, CaseInsensitiveDict):
            value = CaseInsensitiveDict(value)
        self._store[lower_key] = (key, value)
        super().__setitem__(key, value)
    
    def __getattr__(self, name: str) -> Any:
        """Allow dot notation access like dict.key.subkey."""
        if name.startswith('_'):
            raise AttributeError(name)
        # Try case-insensitive lookup
        for key in self.keys():
            if isinstance(key, str) and key.lower() == name.lower():
                return self[key]
        raise AttributeError(f"Key '{name}' not found")
    
    def __getitem__(self, key):
        lower_key = key.lower() if isinstance(key, str) else key
        if lower_key in self._store:
            orig_key, value = self._store[lower_key]
            return super().__getitem__(orig_key)
        raise KeyError(key)
    
    def __delitem__(self, key):
        lower_key = key.lower() if isinstance(key, str) else key
        if lower_key in self._store:
            orig_key, _ = self._store[lower_key]
            del self._store[lower_key]
            super().__delitem__(orig_key)
        else:
            raise KeyError(key)
    
    def __contains__(self, key):
        lower_key = key.lower() if isinstance(key, str) else key
        return lower_key in self._store
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key, *args):
        lower_key = key.lower() if isinstance(key, str) else key
        if lower_key in self._store:
            orig_key, _ = self._store.pop(lower_key)
            return super().pop(orig_key)
        if args:
            return args[0]
        raise KeyError(key)
    
    def keys(self):
        return super().keys()
    
    def values(self):
        return super().values()
    
    def items(self):
        return super().items()
    
    def copy(self):
        return CaseInsensitiveDict(self)
    
    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v


def deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge override into base."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def get_nested(d: Dict, path: str, default=None):
    """Get a value from a nested dict using dot notation."""
    if not path:
        return d
    keys = path.split('.')
    current = d
    for key in keys:
        if isinstance(current, dict):
            # Case-insensitive lookup
            if isinstance(key, str):
                lower_key = key.lower()
                found_key = None
                for k in current.keys():
                    if isinstance(k, str) and k.lower() == lower_key:
                        found_key = k
                        break
                if found_key is not None:
                    current = current[found_key]
                else:
                    return default
            else:
                if key in current:
                    current = current[key]
                else:
                    return default
        else:
            return default
    return current


def set_nested(d: Dict, path: str, value: Any) -> None:
    """Set a value in a nested dict using dot notation, creating intermediate dicts."""
    keys = path.split('.')
    current = d
    for i, key in enumerate(keys[:-1]):
        # Case-insensitive lookup for existing key
        found_key = None
        if isinstance(key, str):
            lower_key = key.lower()
            for k in current.keys():
                if isinstance(k, str) and k.lower() == lower_key:
                    found_key = k
                    break
        
        if found_key is not None:
            key = found_key
        
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    # Set the final key
    final_key = keys[-1]
    d_final = current
    # Check for case-insensitive match for final key
    if isinstance(final_key, str):
        lower_key = final_key.lower()
        for k in list(d_final.keys()):
            if isinstance(k, str) and k.lower() == lower_key:
                del d_final[k]
                break
    d_final[final_key] = value


def delete_nested(d: Dict, path: str) -> bool:
    """Delete a key from a nested dict using dot notation. Returns True if deleted."""
    keys = path.split('.')
    current = d
    for i, key in enumerate(keys[:-1]):
        # Case-insensitive lookup
        found_key = None
        if isinstance(key, str):
            lower_key = key.lower()
            for k in current.keys():
                if isinstance(k, str) and k.lower() == lower_key:
                    found_key = k
                    break
        
        if found_key is not None:
            key = found_key
        
        if key not in current or not isinstance(current[key], dict):
            return False
        current = current[key]
    
    final_key = keys[-1]
    if isinstance(final_key, str):
        lower_key = final_key.lower()
        for k in list(current.keys()):
            if isinstance(k, str) and k.lower() == lower_key:
                del current[k]
                return True
    if final_key in current:
        del current[final_key]
        return True
    return False


def exists_nested(d: Dict, path: str) -> bool:
    """Check if a key exists in a nested dict using dot notation."""
    keys = path.split('.')
    current = d
    for key in keys:
        if isinstance(current, dict):
            # Case-insensitive lookup
            if isinstance(key, str):
                lower_key = key.lower()
                found = False
                for k in current.keys():
                    if isinstance(k, str) and k.lower() == lower_key:
                        found = True
                        current = current[k]
                        break
                if not found:
                    return False
            else:
                if key in current:
                    current = current[key]
                else:
                    return False
        else:
            return False
    return True


def cast_value(value: str) -> Any:
    """Cast a string value to the appropriate Python type."""
    if not isinstance(value, str):
        return value
    
    # Check for explicit cast tokens
    if value.startswith('@'):
        match = re.match(r'^@(int|float|bool|json|none|str)\s*(.*)$', value, re.DOTALL)
        if match:
            cast_type, rest = match.groups()
            rest = rest.strip()
            if cast_type == 'int':
                try:
                    return int(rest)
                except ValueError:
                    raise SettingsError(f"Invalid int cast: {rest}")
            elif cast_type == 'float':
                try:
                    return float(rest)
                except ValueError:
                    raise SettingsError(f"Invalid float cast: {rest}")
            elif cast_type == 'bool':
                return rest.lower() in ('true', '1', 'yes', 'on')
            elif cast_type == 'json':
                try:
                    return json.loads(rest)
                except json.JSONDecodeError:
                    raise SettingsError(f"Invalid json cast: {rest}")
            elif cast_type == 'none':
                return None
            elif cast_type == 'str':
                return rest
    
    # Remove surrounding quotes
    stripped = value.strip()
    if (stripped.startswith('"') and stripped.endswith('"')) or \
       (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1]
    
    # Check for null/none
    if stripped.lower() in ('null', 'none', '~', ''):
        return None
    
    # Check for boolean
    if stripped.lower() in ('true', 'yes', 'on'):
        return True
    if stripped.lower() in ('false', 'no', 'off'):
        return False
    
    # Check for list or dict
    if stripped.startswith('[') or stripped.startswith('{'):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    
    # Check for integer
    try:
        if re.match(r'^-?\d+$', stripped):
            return int(stripped)
    except ValueError:
        pass
    
    # Check for float
    try:
        if re.match(r'^-?\d+\.\d+$', stripped):
            return float(stripped)
    except ValueError:
        pass
    
    return value


def load_yaml(content: str) -> Dict:
    """Simple YAML parser supporting mappings, lists, and scalars."""
    result = {}
    lines = content.split('\n')
    stack = [(result, -1)]  # (current_dict, indent_level)
    current_list = None
    current_list_key = None
    current_list_indent = -1
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        
        # Calculate indent
        indent = len(line) - len(line.lstrip())
        
        # Handle list items
        if stripped.startswith('- '):
            list_item = stripped[2:].strip()
            # Find the right parent based on indent
            while len(stack) > 1 and stack[-1][1] >= indent:
                stack.pop()
            
            if current_list is not None and indent >= current_list_indent:
                # Add to current list
                if ':' in list_item and not list_item.startswith('['):
                    # It's a dict item in the list
                    item_dict = {}
                    key, val = list_item.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    if val:
                        item_dict[key] = cast_value(val)
                    else:
                        item_dict[key] = None
                    current_list.append(item_dict)
                else:
                    current_list.append(cast_value(list_item))
            else:
                # This shouldn't happen in well-formed YAML
                pass
            i += 1
            continue
        
        # Handle key: value
        if ':' in stripped:
            # Check if it's a list item context we're exiting
            if current_list is not None and indent <= current_list_indent:
                current_list = None
                current_list_key = None
                current_list_indent = -1
            
            colon_idx = stripped.index(':')
            key = stripped[:colon_idx].strip()
            value_part = stripped[colon_idx + 1:].strip()
            
            # Pop stack to find parent
            while len(stack) > 1 and stack[-1][1] >= indent:
                stack.pop()
            
            parent = stack[-1][0]
            
            if value_part:
                # Has inline value
                if value_part.startswith('[') and value_part.endswith(']'):
                    # Inline list
                    try:
                        parent[key] = json.loads(value_part)
                    except json.JSONDecodeError:
                        parent[key] = value_part
                else:
                    parent[key] = cast_value(value_part)
            else:
                # Check next line for list or nested dict
                next_i = i + 1
                while next_i < len(lines) and not lines[next_i].strip():
                    next_i += 1
                
                if next_i < len(lines):
                    next_line = lines[next_i]
                    next_stripped = next_line.strip()
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    if next_stripped.startswith('- '):
                        # It's a list
                        parent[key] = []
                        current_list = parent[key]
                        current_list_key = key
                        current_list_indent = next_indent
                        stack.append((parent, indent))
                    else:
                        # It's a nested dict
                        parent[key] = {}
                        stack.append((parent[key], indent))
                else:
                    parent[key] = None
        
        i += 1
    
    return result


def load_toml(content: str) -> Dict:
    """Simple TOML parser supporting tables, key-value pairs, and basic types."""
    result = {}
    current_section = result
    lines = content.split('\n')
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
        
        # Handle section headers
        if stripped.startswith('[') and stripped.endswith(']'):
            section_name = stripped[1:-1].strip()
            # Handle nested sections like [database.settings]
            parts = section_name.split('.')
            current_section = result
            for part in parts:
                if part not in current_section:
                    current_section[part] = {}
                current_section = current_section[part]
            continue
        
        # Handle key = value
        if '=' in stripped:
            eq_idx = stripped.index('=')
            key = stripped[:eq_idx].strip()
            value_str = stripped[eq_idx + 1:].strip()
            
            # Parse value
            value = parse_toml_value(value_str)
            current_section[key] = value
    
    return result


def parse_toml_value(value_str: str) -> Any:
    """Parse a TOML value string."""
    value_str = value_str.strip()
    
    # String (double or single quoted)
    if (value_str.startswith('"') and value_str.endswith('"')) or \
       (value_str.startswith("'") and value_str.endswith("'")):
        return value_str[1:-1]
    
    # Array
    if value_str.startswith('[') and value_str.endswith(']'):
        inner = value_str[1:-1].strip()
        if not inner:
            return []
        # Simple array parsing (doesn't handle nested arrays perfectly)
        items = []
        current = ''
        depth = 0
        in_string = False
        string_char = None
        for char in inner:
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            if char in '[{':
                depth += 1
            if char in ']}':
                depth -= 1
            if char == ',' and depth == 0 and not in_string:
                items.append(parse_toml_value(current.strip()))
                current = ''
            else:
                current += char
        if current.strip():
            items.append(parse_toml_value(current.strip()))
        return items
    
    # Boolean
    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False
    
    # Null
    if value_str.lower() in ('null', 'none'):
        return None
    
    # Number
    try:
        if '.' in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass
    
    # Inline table
    if value_str.startswith('{') and value_str.endswith('}'):
        inner = value_str[1:-1].strip()
        if not inner:
            return {}
        result = {}
        # Simple inline table parsing
        pairs = inner.split(',')
        for pair in pairs:
            if '=' in pair:
                k, v = pair.split('=', 1)
                result[k.strip()] = parse_toml_value(v.strip())
        return result
    
    return value_str


def load_ini(content: str) -> Dict:
    """Simple INI parser supporting sections and key-value pairs."""
    result = {}
    current_section = result
    lines = content.split('\n')
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#') or stripped.startswith(';'):
            continue
        
        # Handle section headers
        if stripped.startswith('[') and stripped.endswith(']'):
            section_name = stripped[1:-1].strip()
            result[section_name] = {}
            current_section = result[section_name]
            continue
        
        # Handle key = value
        if '=' in stripped:
            eq_idx = stripped.index('=')
            key = stripped[:eq_idx].strip()
            value = stripped[eq_idx + 1:].strip()
            # Remove surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            current_section[key] = cast_value(value)
    
    return result


def load_file(path: str) -> Dict:
    """Load a configuration file based on extension."""
    path = Path(path)
    if not path.exists():
        raise SettingsError(f"File not found: {path}")
    
    content = path.read_text(encoding='utf-8')
    ext = path.suffix.lower()
    
    if ext == '.json':
        return json.loads(content) if content.strip() else {}
    elif ext in ('.yaml', '.yml'):
        return load_yaml(content) if content.strip() else {}
    elif ext == '.toml':
        return load_toml(content) if content.strip() else {}
    elif ext == '.ini':
        return load_ini(content) if content.strip() else {}
    elif ext == '.py':
        # Execute Python file in isolated namespace
        namespace = {}
        exec(content, namespace)
        # Extract uppercase variables
        result = {}
        for key, value in namespace.items():
            if key.isupper():
                result[key] = value
        return result
    else:
        raise SettingsError(f"Unsupported file format: {ext}")


def load_env_file(path: str) -> Dict:
    """Load a .env file and return key-value pairs."""
    path = Path(path)
    if not path.exists():
        return {}
    
    result = {}
    content = path.read_text(encoding='utf-8')
    
    for line in content.split('\n'):
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
        
        # Parse KEY=VALUE
        if '=' in stripped:
            eq_idx = stripped.index('=')
            key = stripped[:eq_idx].strip()
            value = stripped[eq_idx + 1:].strip()
            
            # Remove surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            result[key] = value
    
    return result


def dict_to_uppercase(d: Any) -> Any:
    """Convert all keys in a nested dict to uppercase."""
    if isinstance(d, dict):
        return {k.upper(): dict_to_uppercase(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [dict_to_uppercase(item) for item in d]
    else:
        return d


def deep_copy_with_uppercase_keys(d: Any) -> Any:
    """Deep copy with all string keys converted to uppercase."""
    if isinstance(d, dict):
        return {k.upper() if isinstance(k, str) else k: deep_copy_with_uppercase_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [deep_copy_with_uppercase_keys(item) for item in d]
    else:
        return d


class Validator:
    """Validator for a single setting key."""
    
    def __init__(self, name: str, *, required: bool = False, default: Any = None,
                 is_type_of: type = None, eq: Any = None, ne: Any = None,
                 gt: Any = None, gte: Any = None, lt: Any = None, lte: Any = None,
                 condition: Callable = None, messages: Dict = None):
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
    
    def validate(self, settings: 'MiniDynaconf') -> None:
        """Validate the settings against this validator."""
        # Get the current value
        value = get_nested(settings._data, self.name, default=None)
        key_exists = exists_nested(settings._data, self.name)
        
        # Apply default if missing
        if not key_exists:
            if self.default is not None:
                set_nested(settings._data, self.name, self.default)
                value = self.default
                key_exists = True
            elif self.required:
                raise ValidationError(f"Required setting '{self.name}' is missing")
        
        # Required check
        if self.required and value is None:
            raise ValidationError(f"Required setting '{self.name}' is missing")
        
        # If key doesn't exist and not required, skip other checks
        if not key_exists:
            return
        
        # Type check
        if self.is_type_of is not None and not isinstance(value, self.is_type_of):
            raise ValidationError(f"Setting '{self.name}' must be of type {self.is_type_of.__name__}")
        
        # Comparison checks
        if self.eq is not None and value != self.eq:
            raise ValidationError(f"Setting '{self.name}' must equal {self.eq}")
        if self.ne is not None and value == self.ne:
            raise ValidationError(f"Setting '{self.name}' must not equal {self.ne}")
        if self.gt is not None and not (value > self.gt):
            raise ValidationError(f"Setting '{self.name}' must be greater than {self.gt}")
        if self.gte is not None and not (value >= self.gte):
            raise ValidationError(f"Setting '{self.name}' must be greater than or equal to {self.gte}")
        if self.lt is not None and not (value < self.lt):
            raise ValidationError(f"Setting '{self.name}' must be less than {self.lt}")
        if self.lte is not None and not (value <= self.lte):
            raise ValidationError(f"Setting '{self.name}' must be less than or equal to {self.lte}")
        
        # Custom condition
        if self.condition is not None:
            if not self.condition(value, settings):
                raise ValidationError(f"Setting '{self.name}' failed custom validation")


class MiniDynaconf:
    """Main settings class for layered configuration management."""
    
    def __init__(self, settings_files: Union[str, List[str], None] = None,
                 defaults: Optional[Dict] = None,
                 envvar_prefix: str = "APP",
                 environments: bool = False,
                 env: Optional[str] = None,
                 secrets_files: Union[str, List[str], None] = None,
                 validators: Optional[List[Validator]] = None,
                 load_dotenv: bool = False):
        
        self._data = CaseInsensitiveDict()
        self._envvar_prefix = envvar_prefix
        self._environments = environments
        self._env = env or os.environ.get('ENV_FOR_DYNACONF', 'default')
        self._settings_files = []
        self._secrets_files = []
        self._validators = validators or []
        self._validated = False
        
        # Normalize settings_files to list
        if settings_files:
            if isinstance(settings_files, str):
                self._settings_files = [settings_files]
            else:
                self._settings_files = list(settings_files)
        
        # Normalize secrets_files to list
        if secrets_files:
            if isinstance(secrets_files, str):
                self._secrets_files = [secrets_files]
            else:
                self._secrets_files = list(secrets_files)
        
        # Apply defaults (merge into _data)
        if defaults:
            self._merge_data(defaults)
        
        # Load settings files
        for filepath in self._settings_files:
            self._load_file(filepath)
        
        # Load environment variables
        self._load_env_vars()
        
        # Load dotenv if requested
        if load_dotenv:
            # Try to find .env file
            env_file = Path('.env')
            if env_file.exists():
                self.load_env_file('.env')
        
        # Load secrets files
        for filepath in self._secrets_files:
            self._load_file(filepath, is_secret=True)
        
        # Run initial validators
        if self._validators:
            self.validate()
    
    def _load_file(self, filepath: str, env: Optional[str] = None, silent: bool = True, is_secret: bool = False) -> None:
        """Load a single file into settings."""
        try:
            data = load_file(filepath)
            
            if data:
                if self._environments:
                    # Handle environment-specific loading
                    active_env = env or self._env
                    if active_env in data:
                        # Load default first, then active environment
                        if 'default' in data:
                            self._merge_data(data['default'])
                        self._merge_data(data[active_env])
                    else:
                        self._merge_data(data)
                else:
                    self._merge_data(data)
        except Exception as e:
            if not silent:
                raise SettingsError(f"Failed to load file {filepath}: {e}")
    
    def _merge_data(self, data: Dict) -> None:
        """Merge data into settings with recursive merge."""
        self._data = CaseInsensitiveDict(deep_merge(dict(self._data), data))
    
    def _load_env_vars(self) -> None:
        """Load environment variables with the configured prefix."""
        prefix = f"{self._envvar_prefix}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix
                setting_key = key[len(prefix):]
                
                # Convert double underscore to dot notation
                setting_key = setting_key.replace('__', '.')
                
                # Cast the value
                try:
                    casted_value = cast_value(value)
                    set_nested(self._data, setting_key, casted_value)
                except SettingsError:
                    # If casting fails, store as string
                    set_nested(self._data, setting_key, value)
    
    def load_env_file(self, path: str) -> None:
        """Load environment variables from a .env file."""
        env_vars = load_env_file(path)
        prefix = f"{self._envvar_prefix}_"
        
        for key, value in env_vars.items():
            if key.startswith(prefix):
                setting_key = key[len(prefix):].replace('__', '.')
                try:
                    casted_value = cast_value(value)
                    set_nested(self._data, setting_key, casted_value)
                except SettingsError:
                    set_nested(self._data, setting_key, value)
    
    def load_file(self, path: str, env: Optional[str] = None, silent: bool = True) -> None:
        """Load an additional file after construction."""
        self._load_file(path, env=env, silent=silent)
    
    def _get_value(self, key: str) -> Any:
        """Get a value by key using case-insensitive dot notation."""
        return get_nested(self._data, key)
    
    def __getattr__(self, name: str) -> Any:
        """Attribute access for settings."""
        if name.startswith('_'):
            raise AttributeError(name)
        
        # Try case-insensitive lookup
        for key in self._data.keys():
            if isinstance(key, str) and key.lower() == name.lower():
                return self._data[key]
        
        # Try dot notation
        value = get_nested(self._data, name)
        if value is not None:
            return value
        
        raise AttributeError(f"Setting '{name}' not found")
    
    def __getitem__(self, key: str) -> Any:
        """Item access with dot notation support."""
        value = get_nested(self._data, key)
        if value is None and not exists_nested(self._data, key):
            raise KeyError(key)
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Item assignment with dot notation support."""
        set_nested(self._data, key, value)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return exists_nested(self._data, key)
    
    def get(self, key: str, default: Any = None, cast: Optional[Callable] = None) -> Any:
        """Get a setting with optional casting."""
        value = get_nested(self._data, key, default=default)
        if cast is not None and value is not None:
            return cast(value)
        return value
    
    def set(self, key: str, value: Any, validate: bool = False) -> None:
        """Set a setting."""
        # Save state for atomicity
        saved_state = copy.deepcopy(dict(self._data))
        
        try:
            set_nested(self._data, key, value)
            
            if validate:
                self._run_validators()
        except Exception:
            # Restore state on failure
            self._data = CaseInsensitiveDict(saved_state)
            raise
    
    def update(self, mapping: Dict, validate: bool = False) -> None:
        """Update multiple settings."""
        # Save state for atomicity
        saved_state = copy.deepcopy(dict(self._data))
        
        try:
            for key, value in mapping.items():
                set_nested(self._data, key, value)
            
            if validate:
                self._run_validators()
        except Exception:
            # Restore state on failure
            self._data = CaseInsensitiveDict(saved_state)
            raise
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in settings."""
        return exists_nested(self._data, key)
    
    def delete(self, key: str) -> None:
        """Delete a key from settings."""
        delete_nested(self._data, key)
    
    def as_dict(self) -> Dict:
        """Return a deep copy of settings with uppercase keys."""
        return deep_copy_with_uppercase_keys(dict(self._data))
    
    def reload(self) -> None:
        """Reload settings from configured sources."""
        # Clear current data
        self._data = CaseInsensitiveDict()
        
        # Need to store runtime assignments before reload
        # For now, just reload from sources
        # In a full implementation, we'd need to track runtime assignments
        
        # Re-load everything
        # Get defaults from somewhere - this is a simplification
        # A full implementation would need to store the original defaults
        
        # Reload settings files
        for filepath in self._settings_files:
            self._load_file(filepath)
        
        # Reload environment variables
        self._load_env_vars()
        
        # Reload secrets files
        for filepath in self._secrets_files:
            self._load_file(filepath, is_secret=True)
        
        # Run validators
        if self._validators:
            self.validate()
    
    def configure(self, **kwargs) -> None:
        """Change configuration options and reload."""
        # Update configuration
        if 'envvar_prefix' in kwargs:
            self._envvar_prefix = kwargs['envvar_prefix']
        if 'environments' in kwargs:
            self._environments = kwargs['environments']
        if 'env' in kwargs:
            self._env = kwargs['env']
        
        # Clear and reload
        self.reload()
    
    def register_validator(self, validator: Validator) -> None:
        """Register a new validator."""
        self._validators.append(validator)
    
    def validate(self, key: Optional[str] = None) -> None:
        """Run validators against current settings."""
        if key:
            # Validate specific key
            for validator in self._validators:
                if validator.name == key or validator.name.lower() == key.lower():
                    validator.validate(self)
        else:
            # Validate all
            self._run_validators()
    
    def _run_validators(self) -> None:
        """Run all validators."""
        for validator in self._validators:
            validator.validate(self)
    
    def __repr__(self) -> str:
        return f"MiniDynaconf({dict(self._data)!r})"