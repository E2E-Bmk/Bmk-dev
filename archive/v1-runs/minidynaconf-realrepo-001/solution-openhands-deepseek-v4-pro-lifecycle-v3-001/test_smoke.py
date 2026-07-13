"""Smoke tests for minidynaconf."""
import json
import os
import sys
import tempfile

# Add solution dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from minidynaconf import MiniDynaconf, Validator, ValidationError, SettingsError

tmpdir = tempfile.mkdtemp()
passed = 0
failed = 0

# Ensure env vars from prior runs are cleared
_CLEAN_PREFIXES = ("APP_", "SVCTEST_")
def _clean_env():
    for k in list(os.environ.keys()):
        for pfx in _CLEAN_PREFIXES:
            if k.startswith(pfx):
                del os.environ[k]
_clean_env()

def check(desc, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {desc}")
    else:
        failed += 1
        print(f"  FAIL: {desc}")

# === Feature 1: Settings file loading (JSON) ===
print("Feature 1: Settings file loading")
json_path = os.path.join(tmpdir, 'settings.json')
with open(json_path, 'w') as f:
    json.dump({'host': 'localhost', 'port': 5432, 'database': {'name': 'mydb'}}, f)

s = MiniDynaconf(settings_files=json_path)
check("host from JSON", s.get('host') == 'localhost')
check("port from JSON", s.get('port') == 5432)
check("nested key", s.get('database.name') == 'mydb')
check("as_dict keys", set(s.as_dict().keys()) == {'HOST', 'PORT', 'DATABASE'})

# === Feature 2: Environment variable overrides ===
print("Feature 2: Env var overrides")
os.environ['APP_HOST'] = 'envhost'
os.environ['APP_PORT'] = '9999'
s2 = MiniDynaconf(settings_files=json_path, envvar_prefix='APP')
check("env overrides file", s2.get('host') == 'envhost')
check("env port is int", s2.get('port') == 9999)

# === Feature 3: Secrets file loading ===
print("Feature 3: Secrets loading")
secret_path = os.path.join(tmpdir, 'secrets.json')
with open(secret_path, 'w') as f:
    json.dump({'host': 'secrethost', 'api_key': 'sk-123'}, f)
s3 = MiniDynaconf(settings_files=json_path, secrets_files=secret_path)
check("secret overrides file", s3.get('host') == 'secrethost')
check("secret adds new key", s3.get('api_key') == 'sk-123')

# === Priority: secrets > env > files > defaults ===
print("Feature: Layer priority")
os.environ['APP_HOST'] = 'envhost'
s_prio = MiniDynaconf(
    defaults={'host': 'default_host'},
    settings_files=json_path,
    envvar_prefix='APP',
    secrets_files=secret_path,
)
check("secrets highest priority", s_prio.get('host') == 'secrethost')

# === Feature 4: Type casting ===
print("Feature 4: Type casting")
check("int auto-cast", isinstance(s.get('port'), int))
os.environ['APP_DEBUG'] = '@bool true'
s4 = MiniDynaconf(defaults={'debug': False}, envvar_prefix='APP')
check("explicit bool cast", s4.get('debug') is True)

os.environ['APP_NUM'] = '@int 42'
s4b = MiniDynaconf(defaults={}, envvar_prefix='APP')
check("explicit int cast", s4b.get('num') == 42)

os.environ['APP_FLOAT'] = '@float 3.14'
s4c = MiniDynaconf(defaults={}, envvar_prefix='APP')
check("explicit float cast", s4c.get('float') == 3.14)

os.environ['APP_STRVAL'] = '@str 123'
s4d = MiniDynaconf(defaults={}, envvar_prefix='APP')
check("@str prevents cast", s4d.get('strval') == '123')

os.environ['APP_JSONVAL'] = '@json [1,2,3]'
s4e = MiniDynaconf(defaults={}, envvar_prefix='APP')
check("@json cast", s4e.get('jsonval') == [1, 2, 3])

# === Feature 5: Validators ===
print("Feature 5: Validators")
v = Validator('host', required=True)
s5 = MiniDynaconf(defaults={'host': 'localhost'}, validators=[v])
try:
    s5.validate()
    check("required validator passes", True)
except ValidationError:
    check("required validator passes", False)

# required missing
try:
    s6 = MiniDynaconf(defaults={}, validators=[Validator('missing', required=True)])
    s6.validate()
    check("required validator fails on missing", False)
except ValidationError as e:
    check("required validator fails on missing", 'missing' in str(e).lower())

# validator default
s5b = MiniDynaconf(defaults={}, validators=[Validator('key', default='defval')])
check("validator default applied", s5b.get('key') == 'defval')

# === Feature 6: Runtime settings API ===
print("Feature 6: Runtime API")
_clean_env()
s6 = MiniDynaconf(defaults={'x': 1})
check("get existing", s6.get('x') == 1)
check("get missing default", s6.get('nonexist', 42) == 42)
s6.set('y', 2)
check("set new key", s6.get('y') == 2)
s6.update({'z': 3, 'nested.a': 10})
check("update multiple", s6.get('z') == 3)
check("update nested", s6.get('nested.a') == 10)
check("exists true", s6.exists('x'))
check("exists false", not s6.exists('nonexistent'))
s6.delete('x')
check("delete removes key", not s6.exists('x'))

# attribute access
s6b = MiniDynaconf(defaults={'host': 'localhost', 'port': 5432})
check("attr access", s6b.host == 'localhost')
check("attr access int", s6b.port == 5432)
s6b.newkey = 'newval'
check("attr set", s6b.newkey == 'newval')
check("attr set via get", s6b.get('newkey') == 'newval')

# item access
check("item access", s6b['host'] == 'localhost')
s6b['itemkey'] = 'itemval'
check("item set", s6b.get('itemkey') == 'itemval')
check("item set via attr", s6b.itemkey == 'itemval')

# === Feature 7: Export / Import ===
print("Feature 7: Export/Import")
export_path = os.path.join(tmpdir, 'exported.json')
exported = s6.export(export_path)
check("export file exists", os.path.exists(export_path))
with open(export_path) as f:
    reloaded = json.load(f)
check("export round-trip", reloaded == exported)

s_imp = MiniDynaconf(defaults={'base': 'val'})
s_imp.import_dict({'imported': 'yes', 'base': 'overridden'}, validate=False)
check("import_dict", s_imp.get('imported') == 'yes')
check("import_dict overrides default", s_imp.get('base') == 'overridden')

# === Feature 7: Reload ===
print("Feature 7: Reload")
s_rel = MiniDynaconf(settings_files=json_path)
check("initial host", s_rel.get('host') == 'localhost')
s_rel.set('host', 'runtime_override')
check("runtime override", s_rel.get('host') == 'runtime_override')
s_rel.reload()
check("reload restores file value", s_rel.get('host') == 'localhost')

# reload clears tombstones
s_rel2 = MiniDynaconf(settings_files=json_path)
check("host exists before delete", s_rel2.exists('host'))
s_rel2.delete('host')
check("host gone after delete", not s_rel2.exists('host'))
s_rel2.reload()
check("host restored after reload", s_rel2.exists('host'))

# === Recursive merge ===
print("Feature: Recursive merge")
s_rm = MiniDynaconf(defaults={'db': {'host': 'a', 'port': 1}})
s_rm.set('db.port', 2)
check("sibling survives merge", s_rm.get('db.host') == 'a')
check("leaf updated", s_rm.get('db.port') == 2)

# === Case insensitivity ===
print("Feature: Case insensitivity")
_clean_env()
s_ci = MiniDynaconf(defaults={'HOST': 'upper'})
check("lowercase get", s_ci.get('host') == 'upper')
check("uppercase get", s_ci.get('HOST') == 'upper')
check("mixed get", s_ci.get('Host') == 'upper')

# === as_dict uses uppercase canonical keys ===
print("Feature: as_dict uppercase keys")
check("as_dict uppercase", list(s_ci.as_dict().keys()) == ['HOST'])

# === Configure ===
print("Feature: Configure")
_clean_env()
s_cfg = MiniDynaconf(defaults={'a': 1}, settings_files=json_path)
check("pre-configure host", s_cfg.exists('host'))
s_cfg.configure(defaults={'x': 99}, settings_files=None)
check("post-configure only new defaults", s_cfg.get('x') == 99)
check("post-configure old settings gone", not s_cfg.exists('host'))

# === Atomic: configure failure doesn't leave broken state ===
print("Feature: Atomic configure")
s_atom = MiniDynaconf(defaults={'key': 'val'})
try:
    s_atom.configure(settings_files='/nonexistent/file.json')
    # If it doesn't raise, check if state preserved
    check("atomic configure failure - state preserved", s_atom.get('key') == 'val')
except SettingsError:
    check("atomic configure failure - raises SettingsError", True)
    check("atomic configure failure - state preserved", s_atom.get('key') == 'val')

# === Falsey values distinction ===
print("Feature: Falsey vs missing")
s_falsey = MiniDynaconf(defaults={'flag': False, 'num': 0, 'empty_str': '', 'empty_list': [], 'empty_dict': {}})
check("False is existing", s_falsey.exists('flag'))
check("0 is existing", s_falsey.exists('num'))
check("empty string is existing", s_falsey.exists('empty_str'))
check("empty list is existing", s_falsey.exists('empty_list'))
check("empty dict is existing", s_falsey.exists('empty_dict'))
check("truly missing", not s_falsey.exists('nonexistent'))

# === get with cast parameter ===
print("Feature: get with cast")
_clean_env()
s_cast = MiniDynaconf(defaults={'num': '42'})
check("get cast to int", s_cast.get('num', cast=int) == 42)
check("original unchanged", s_cast.get('num') == '42')

# === Nested env vars with double underscore ===
print("Feature: Nested env vars")
os.environ['APP_DB__HOST'] = 'dbhost'
os.environ['APP_DB__PORT'] = '3306'
s_nest = MiniDynaconf(envvar_prefix='APP')
check("nested env key", s_nest.get('db.host') == 'dbhost')
check("nested env port cast", s_nest.get('db.port') == 3306)

# === TOML parsing ===
print("Feature: TOML parsing")
toml_path = os.path.join(tmpdir, 'settings.toml')
with open(toml_path, 'w') as f:
    f.write("""
title = "My App"
[server]
host = "0.0.0.0"
port = 8080
debug = true
[server.tls]
enabled = true
""")
s_toml = MiniDynaconf(settings_files=toml_path)
check("TOML bare key", s_toml.get('title') == 'My App')
check("TOML section host", s_toml.get('server.host') == '0.0.0.0')
check("TOML section port", s_toml.get('server.port') == 8080)
check("TOML section debug", s_toml.get('server.debug') is True)
check("TOML nested section", s_toml.get('server.tls.enabled') is True)

# === INI parsing ===
print("Feature: INI parsing")
ini_path = os.path.join(tmpdir, 'settings.ini')
with open(ini_path, 'w') as f:
    f.write("""
[server]
host = 127.0.0.1
port = 9090
[database]
name = testdb
""")
s_ini = MiniDynaconf(settings_files=ini_path)
check("INI server host", s_ini.get('server.host') == '127.0.0.1')
check("INI server port", s_ini.get('server.port') == 9090)
check("INI db name", s_ini.get('database.name') == 'testdb')

# === YAML parsing ===
print("Feature: YAML parsing")
yaml_path = os.path.join(tmpdir, 'settings.yaml')
with open(yaml_path, 'w') as f:
    f.write("""
server:
  host: yamlhost
  port: 7070
features:
  - auth
  - logging
data:
  nested:
    key: value
""")
s_yaml = MiniDynaconf(settings_files=yaml_path)
check("YAML host", s_yaml.get('server.host') == 'yamlhost')
check("YAML port", s_yaml.get('server.port') == 7070)
check("YAML list", s_yaml.get('features') == ['auth', 'logging'])
check("YAML nested", s_yaml.get('data.nested.key') == 'value')

# === load_file ===
print("Feature: load_file")
s_lf = MiniDynaconf(defaults={'a': 1})
extra_path = os.path.join(tmpdir, 'extra.json')
with open(extra_path, 'w') as f:
    json.dump({'b': 2, 'c': 3}, f)
s_lf.load_file(extra_path)
check("load_file adds key", s_lf.get('b') == 2)
check("load_file preserves original", s_lf.get('a') == 1)
# reload should include the lifecycle file
s_lf.reload()
check("reload preserves lifecycle import", s_lf.get('b') == 2)

# Cleanup env
for k in ['APP_HOST', 'APP_PORT', 'APP_DEBUG', 'APP_NUM', 'APP_FLOAT', 'APP_STRVAL', 'APP_JSONVAL', 'APP_DB__HOST', 'APP_DB__PORT']:
    os.environ.pop(k, None)

# === Results ===
print()
print(f"{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
print(f"{'='*50}")
if failed > 0:
    sys.exit(1)
