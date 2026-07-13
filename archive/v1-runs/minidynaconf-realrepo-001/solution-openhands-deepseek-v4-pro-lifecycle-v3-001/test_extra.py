"""Additional edge-case tests."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidynaconf import MiniDynaconf, Validator, ValidationError, SettingsError

tmpdir = tempfile.mkdtemp()
errors = []

def t(desc, cond):
    if not cond:
        errors.append(f"FAIL: {desc}")
        print(f"  FAIL: {desc}")
    else:
        print(f"  PASS: {desc}")

# Clean env
for k in list(os.environ.keys()):
    for pfx in ("APP_", "TEST_"):
        if k.startswith(pfx):
            del os.environ[k]

# --- Python settings file ---
print("Python settings file")
py_path = os.path.join(tmpdir, 'settings.py')
with open(py_path, 'w') as f:
    f.write('HOST = "pyhost"\nPORT = 9999\nDEBUG = True\n')
s_py = MiniDynaconf(settings_files=py_path)
t("Python host", s_py.get('host') == 'pyhost')
t("Python port", s_py.get('port') == 9999)

# --- load_env_file (dotenv) ---
print("Dotenv loading")
dotenv_path = os.path.join(tmpdir, '.env')
with open(dotenv_path, 'w') as f:
    f.write("APP_NAME=dotenv_app\nAPP_VERSION=2\n# comment\n")
# load_dotenv=True looks for .env in CWD; change CWD for test
old_cwd = os.getcwd()
os.chdir(tmpdir)
s_de2 = MiniDynaconf(defaults={}, envvar_prefix='APP', load_dotenv=True)
os.chdir(old_cwd)
t("dotenv prefix matched", s_de2.get('name') == 'dotenv_app')
t("dotenv version cast", s_de2.get('version') == 2)

# --- load_env_file explicit ---
print("load_env_file explicit")
os.environ.pop('APP_NAME', None)
os.environ.pop('APP_VERSION', None)
s_lef = MiniDynaconf(defaults={}, envvar_prefix='APP')
s_lef.load_env_file(dotenv_path)
t("explicit load_env_file", s_lef.get('name') == 'dotenv_app')
t("load_env_file durable on reload", s_lef.reload() is None)
t("load_env_file survives reload", s_lef.get('name') == 'dotenv_app')

# --- Malformed file atomics ---
print("Malformed file atomicity")
malformed = os.path.join(tmpdir, 'bad.json')
with open(malformed, 'w') as f:
    f.write("not valid json @@@")
s_mf = MiniDynaconf(defaults={'x': 42})
try:
    s_mf.load_file(malformed, silent=False)
    t("malformed file raises", False)
except SettingsError:
    t("malformed file raises", True)
t("malformed file state preserved", s_mf.get('x') == 42)

# --- Explicit cast failure ---
print("Explicit cast failure")
s_fail = MiniDynaconf(defaults={'x': 1})
try:
    s_fail.set('y', '@int not-a-number', validate=True)
    t("invalid cast raises", False)
except (SettingsError, ValidationError):
    t("invalid cast raises", True)
t("invalid cast preserves state", s_fail.get('x') == 1)

# --- Validator with condition (cross-key) ---
print("Validator cross-key condition")
def must_be_greater_than_min(value, settings):
    return value > settings.get('min_val', 0)

s_xk = MiniDynaconf(defaults={'max_val': 100, 'min_val': 10}, validators=[
    Validator('max_val', condition=must_be_greater_than_min)
])
try:
    s_xk.validate()
    t("cross-key condition passes", True)
except ValidationError:
    t("cross-key condition passes", False)

# --- Validator messages ---
print("Validator messages")
s_msg = MiniDynaconf(defaults={}, validators=[
    Validator('name', required=True, messages={'required': 'Custom error: name needed'})
])
try:
    s_msg.validate()
    t("custom message in error", False)
except ValidationError as e:
    t("custom message in error", 'Custom error' in str(e))

# --- Configure clears lifecycle imports ---
print("Configure clears lifecycle imports")
s_cc = MiniDynaconf(defaults={'a': 1})
extra = os.path.join(tmpdir, 'extra2.json')
with open(extra, 'w') as f:
    json.dump({'b': 2}, f)
s_cc.load_file(extra)
t("pre-configure has lifecycle", s_cc.get('b') == 2)
s_cc.configure(defaults={'c': 3})
t("post-configure lifecycle cleared", not s_cc.exists('b'))
t("post-configure new defaults", s_cc.get('c') == 3)

# --- Validate(key=...) ---
print("Validate specific key")
s_vk = MiniDynaconf(defaults={'a': 1, 'b': 'str'}, validators=[
    Validator('a', is_type_of=int),
    Validator('b', is_type_of=str),
])
s_vk.validate(key='a')  # should only check 'a'
t("validate single key passes", True)

# --- set nested with explicit cast ---
print("Nested set with explicit cast")
s_ns = MiniDynaconf(defaults={})
s_ns.set('db.port', '@int 9090')
t("nested explicit cast", s_ns.get('db.port') == 9090)

# --- load_file with env parameter ---
print("load_file with env")
env_toml = os.path.join(tmpdir, 'envs2.toml')
with open(env_toml, 'w') as f:
    f.write("""
[default]
key = "def"
[staging]
key = "stg"
""")
s_lenv = MiniDynaconf(settings_files=env_toml, environments=True)
t("default env", s_lenv.get('key') == 'def')
s_lenv.load_file(env_toml, env='staging')
t("staging env", s_lenv.get('key') == 'stg')

# --- export returns JSON-serializable ---
print("Export format")
s_ex = MiniDynaconf(defaults={'num': 42, 'flag': True, 'text': 'hello'})
d = s_ex.export()
t("export has keys", set(d.keys()) == {'NUM', 'FLAG', 'TEXT'})
t("export json roundtrip", json.loads(json.dumps(d)) == d)

# --- update with validate ---
print("Update with validate")
s_uv = MiniDynaconf(defaults={'port': 80}, validators=[
    Validator('port', is_type_of=int, gt=0)
])
s_uv.update({'port': 443, 'new_key': 'ok'}, validate=True)
t("update validated", s_uv.get('port') == 443)
t("update validated new", s_uv.get('new_key') == 'ok')

print()
if errors:
    print(f"FAILURES ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
