"""Verify core code paths with clean env."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidynaconf import MiniDynaconf, Validator, ValidationError, SettingsError

errors = []

def t(desc, cond):
    if not cond:
        errors.append(f"FAIL: {desc}")
        print(f"  FAIL: {desc}")
    else:
        print(f"  PASS: {desc}")

# Clean any APP_* env vars
for k in list(os.environ.keys()):
    if k.startswith('APP_'):
        del os.environ[k]

# --- attribute access, item access, case insensitivity ---
print("Core access tests")
s = MiniDynaconf(defaults={'host': 'localhost', 'PORT': 5432, 'Mixed': True})
t("attr host", s.host == 'localhost')
t("attr port", s.port == 5432)
t("item host", s['host'] == 'localhost')
t("item uppercase", s['HOST'] == 'localhost')
t("case insensitive", s.get('HOST') == 'localhost')
t("case insensitive mixed", s.get('Host') == 'localhost')
t("as_dict uppercase", list(s.as_dict().keys()) == ['HOST', 'PORT', 'MIXED'])

# --- reload ---
print("Reload tests")
tmpdir = tempfile.mkdtemp()
json_path = os.path.join(tmpdir, 'reload.json')
with open(json_path, 'w') as f:
    json.dump({'host': 'fromfile', 'port': 8080}, f)

s2 = MiniDynaconf(settings_files=json_path)
t("reload initial", s2.get('host') == 'fromfile')
s2.set('host', 'runtime')
t("runtime override", s2.get('host') == 'runtime')
s2.reload()
t("reload restores", s2.get('host') == 'fromfile')

# --- get with cast ---
print("Get with cast tests")
s3 = MiniDynaconf(defaults={'num': '42'})
t("string stays string", s3.get('num') == '42')
t("get cast to int", s3.get('num', cast=int) == 42)
t("original unchanged", s3.get('num') == '42')

# --- configure ---
print("Configure tests")
s4 = MiniDynaconf(defaults={'a': 1}, settings_files=json_path)
t("pre-configure", s4.exists('host'))
s4.configure(defaults={'x': 99}, settings_files=None)
t("post-configure new", s4.get('x') == 99)
t("post-configure old gone", not s4.exists('host'))

# --- atomic configure ---
print("Atomic tests")
s5 = MiniDynaconf(defaults={'key': 'val'})
try:
    s5.configure(settings_files='/nonexistent/file.json')
except SettingsError:
    pass
t("atomic failure preserves", s5.get('key') == 'val')

# --- empty files (missing files ignored) ---
print("Missing files tests")
s6 = MiniDynaconf(settings_files='/nonexistent/settings.json')
t("missing file ignored", s6.as_dict() == {})
t("exists false", not s6.exists('anything'))

# --- environments ---
print("Environments tests")
env_path = os.path.join(tmpdir, 'envs.toml')
with open(env_path, 'w') as f:
    f.write("""
[default]
host = "default_host"
port = 1111

[production]
host = "prod_host"
port = 2222
debug = true
""")
os.environ['ENV_FOR_DYNACONF'] = 'production'
s7 = MiniDynaconf(settings_files=env_path, environments=True)
t("env default host overridden", s7.get('host') == 'prod_host')
t("env default port overridden", s7.get('port') == 2222)
t("env production-only key", s7.get('debug') is True)
del os.environ['ENV_FOR_DYNACONF']

# --- validator with condition ---
print("Validator condition tests")
def cond(value, settings):
    return value > settings.get('min_val', 0)

s8 = MiniDynaconf(defaults={'max_val': 100, 'min_val': 10}, validators=[
    Validator('max_val', condition=cond)
])
try:
    s8.validate()
    t("condition passes", True)
except ValidationError:
    t("condition passes", False)

# --- set with validate ---
print("Validated set tests")
s9 = MiniDynaconf(defaults={'port': 8080}, validators=[
    Validator('port', is_type_of=int, gt=0)
])
try:
    s9.set('port', -1, validate=True)
    t("validated set blocks invalid", False)
except ValidationError:
    t("validated set blocks invalid", True)
t("state preserved after failed set", s9.get('port') == 8080)

# --- load_file silent/not-silent ---
print("load_file tests")
s10 = MiniDynaconf(defaults={'a': 1})
extra = os.path.join(tmpdir, 'extra.json')
with open(extra, 'w') as f:
    json.dump({'b': 2}, f)
s10.load_file(extra)
t("load_file adds", s10.get('b') == 2)
# reload includes lifecycle import
s10.reload()
t("reload keeps lifecycle", s10.get('b') == 2)
# silent=True ignores missing
s10.load_file('/nonexistent/nope.json', silent=True)
t("silent missing ignored", s10.get('a') == 1)
# silent=False raises
try:
    s10.load_file('/nonexistent/nope.json', silent=False)
    t("silent=False raises", False)
except SettingsError:
    t("silent=False raises", True)

# --- nested env vars ---
print("Nested env tests")
os.environ['TEST_DB__HOST'] = 'dbhost'
s11 = MiniDynaconf(defaults={}, envvar_prefix='TEST')
t("nested env", s11.get('db.host') == 'dbhost')
del os.environ['TEST_DB__HOST']

# --- as_dict / export round-trip ---
print("Round-trip tests")
s12 = MiniDynaconf(defaults={'host': 'a', 'db': {'name': 'x', 'port': 123}})
d = s12.as_dict()
t("as_dict deepcopy", d is not s12._effective._data)
d['NEW'] = 'should not appear'
t("as_dict mutation isolated", not s12.exists('new'))

# --- delete and reload ---
print("Delete+reload tests")
s13 = MiniDynaconf(defaults={'x': 1, 'y': 2})
t("exists before delete", s13.exists('x'))
s13.delete('x')
t("gone after delete", not s13.exists('x'))
s13.reload()
t("restored after reload", s13.exists('x'))

# --- export to file ---
print("Export tests")
export_path = os.path.join(tmpdir, 'exported.json')
s14 = MiniDynaconf(defaults={'a': 1, 'b': {'c': 2}})
s14.export(export_path)
with open(export_path) as f:
    loaded = json.load(f)
t("export JSON roundtrip", loaded == {'A': 1, 'B': {'C': 2}})

# --- import_dict with replace ---
print("Import dict tests")
s15 = MiniDynaconf(defaults={'base_key': 'base_val'})
s15.import_dict({'first': 'a'}, validate=False)
t("import first", s15.get('first') == 'a')
s15.import_dict({'second': 'b'}, validate=False)
t("import second", s15.get('second') == 'b')
t("import first survived", s15.get('first') == 'a')
s15.import_dict({'third': 'c'}, validate=False, replace=True)
t("replace cleared previous", not s15.exists('first'))
t("replace has new", s15.get('third') == 'c')

print()
if errors:
    print(f"FAILURES ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
