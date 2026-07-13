"""Comprehensive tests for minidynaconf features."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from minidynaconf import MiniDynaconf, Validator, ValidationError, SettingsError

_failed = 0


def check(name, actual, expected):
    global _failed
    ok = actual == expected
    status = "OK" if ok else f"FAIL (got {actual!r}, expected {expected!r})"
    print(f"  [{status}] {name}")
    if not ok:
        _failed += 1


def fail(msg):
    global _failed
    print(f"  [FAIL] {msg}")
    _failed += 1


def test_file_loading():
    print("\n=== File Loading ===")
    tmp = tempfile.mkdtemp()

    # -- JSON --
    json_path = os.path.join(tmp, "settings.json")
    with open(json_path, "w") as f:
        json.dump({"host": "jsonhost", "port": 1234}, f)
    s = MiniDynaconf(settings_files=json_path)
    check("JSON host", s.host, "jsonhost")
    check("JSON port", s.port, 1234)

    # -- TOML (if available) --
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            tomllib = None

    if tomllib is not None:
        toml_path = os.path.join(tmp, "settings.toml")
        with open(toml_path, "w") as f:
            f.write('host = "tomlhost"\nport = 5678\n')
        s2 = MiniDynaconf(settings_files=toml_path)
        check("TOML host", s2.host, "tomlhost")
        check("TOML port", s2.port, 5678)

    # -- INI --
    ini_path = os.path.join(tmp, "settings.ini")
    with open(ini_path, "w") as f:
        f.write("[database]\nhost = inihost\nport = 9999\n")
    s3 = MiniDynaconf(settings_files=ini_path)
    check("INI section", s3.database.host, "inihost")
    check("INI port", s3.database.port, 9999)

    # -- YAML --
    yaml_path = os.path.join(tmp, "settings.yaml")
    with open(yaml_path, "w") as f:
        f.write("host: yamlhost\nport: 7777\n")
    s4 = MiniDynaconf(settings_files=yaml_path)
    check("YAML host", s4.host, "yamlhost")
    check("YAML port", s4.port, 7777)

    # -- Python file --
    py_path = os.path.join(tmp, "settings.py")
    with open(py_path, "w") as f:
        f.write("HOST = 'pyhost'\nPORT = 5555\n_internal = 'secret'\nlower = 'no'\n")
    s5 = MiniDynaconf(settings_files=py_path)
    check("PY host", s5.host, "pyhost")
    check("PY port", s5.port, 5555)
    check("PY no internal", s5.exists("_internal"), False)
    check("PY no lowercase", s5.exists("lower"), False)

    # -- Missing file (silent) --
    s6 = MiniDynaconf(settings_files="/nonexistent/file.json")
    check("Missing file ignored", s6.as_dict(), {})

    import shutil
    shutil.rmtree(tmp)


def test_type_casting():
    print("\n=== Type Casting ===")

    # Python defaults preserve their types (NOT auto-cast)
    s = MiniDynaconf(defaults={
        "flag_true": "true",
        "num_int": "42",
        "nothing": "none",
    })
    check("Python str preserved (true)", s.flag_true, "true")
    check("Python str preserved (42)", s.num_int, "42")
    check("Python str preserved (none)", s.nothing, "none")

    # Python numeric types preserved
    s2 = MiniDynaconf(defaults={"port": 5432, "host": "localhost"})
    check("Python int preserved", type(s2.port), int)
    check("Python str preserved", type(s2.host), str)

    # Explicit casting tokens
    s3 = MiniDynaconf(defaults={
        "a": "@int 42",
        "b": "@float 3.14",
        "c": "@bool true",
        "d": "@json [1,2]",
        "e": "@none x",
        "f": "@str 42",
    })
    check("@int", s3.a, 42)
    check("@float", s3.b, 3.14)
    check("@bool", s3.c, True)
    check("@json", s3.d, [1, 2])
    check("@none", s3.e, None)
    check("@str", s3.f, "42")
    check("@str type", type(s3.f), str)

    # Invalid explicit cast
    try:
        MiniDynaconf(defaults={"x": "@int notanumber"})
        fail("Should raise SettingsError for invalid @int")
    except SettingsError:
        print("  [OK] SettingsError for invalid @int")

    # @str prevents auto-casting
    s4 = MiniDynaconf(defaults={"port": "@str 5432"})
    check("@str prevents int cast", s4.port, "5432")


def test_environment_variables():
    print("\n=== Environment Variables ===")
    os.environ["APP_TEST_HOST"] = "envhost"
    os.environ["APP_TEST_PORT"] = "9090"
    os.environ["APP_DATABASE__HOST"] = "db_env_host"

    s = MiniDynaconf(envvar_prefix="APP")
    check("env host", s.test_host, "envhost")
    check("env port cast", s.test_port, 9090)
    check("env nested", s.database.host, "db_env_host")

    # Cleanup
    del os.environ["APP_TEST_HOST"]
    del os.environ["APP_TEST_PORT"]
    del os.environ["APP_DATABASE__HOST"]


def test_layer_priority():
    print("\n=== Layer Priority ===")
    os.environ["APP_PRIORITY"] = "env_value"

    s = MiniDynaconf(
        defaults={"priority": "default_value"},
        envvar_prefix="APP",
    )
    check("env overrides default", s.priority, "env_value")

    del os.environ["APP_PRIORITY"]

    # Runtime overrides everything
    s2 = MiniDynaconf(defaults={"x": 1})
    s2.set("x", 99)
    check("runtime overrides default", s2.x, 99)


def test_validators():
    print("\n=== Validators ===")

    # Comparison validators
    s = MiniDynaconf(
        defaults={"port": 8080, "timeout": 30},
        validators=[
            Validator("port", gt=1024, lt=65535),
            Validator("timeout", gte=0, lte=60),
        ],
    )
    check("gt/lt passes", s.port, 8080)
    check("gte/lte passes", s.timeout, 30)

    # eq / ne
    s2 = MiniDynaconf(
        defaults={"mode": "production"},
        validators=[Validator("mode", eq="production")],
    )
    check("eq passes", s2.mode, "production")

    try:
        MiniDynaconf(
            defaults={"mode": "development"},
            validators=[Validator("mode", eq="production")],
        )
        fail("Should raise ValidationError for eq mismatch")
    except ValidationError:
        print("  [OK] ValidationError for eq mismatch")

    # ne
    try:
        MiniDynaconf(
            defaults={"mode": "production"},
            validators=[Validator("mode", ne="production")],
        )
        fail("Should raise ValidationError for ne match")
    except ValidationError:
        print("  [OK] ValidationError for ne match")

    # register_validator
    s3 = MiniDynaconf(defaults={"name": "test"})
    s3.register_validator(Validator("name", required=True))
    check("register_validator runs", s3.name, "test")


def test_runtime_api():
    print("\n=== Runtime API ===")

    # set with validate
    s = MiniDynaconf(
        validators=[Validator("port", is_type_of=int, gt=0)],
    )
    s.set("port", 8080, validate=True)
    check("set with validate ok", s.port, 8080)

    try:
        s.set("port", "bad", validate=True)
        fail("Should raise for bad validated set")
    except ValidationError:
        print("  [OK] ValidationError for bad set")
    check("value unchanged after failed set", s.port, 8080)

    # update with validate (needs validators to actually validate)
    s2 = MiniDynaconf(
        defaults={"a": 1, "b": 2},
        validators=[Validator("a", is_type_of=int)],
    )
    try:
        s2.update({"a": "bad", "b": 3}, validate=True)
        fail("Should raise for bad validated update")
    except (ValidationError, SettingsError):
        print("  [OK] Error for bad validated update")
    # After failure, values should be unchanged
    check("a unchanged after failed update", s2.a, 1)
    check("b unchanged after failed update", s2.b, 2)

    # configure
    s3 = MiniDynaconf(defaults={"x": 1})
    s3.configure(defaults={"x": 100, "y": 200})
    check("configure x", s3.x, 100)
    check("configure y", s3.y, 200)


def test_environments():
    print("\n=== Environments ===")
    tmp = tempfile.mkdtemp()
    toml_path = os.path.join(tmp, "settings.toml")

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            tomllib = None

    if tomllib is not None:
        with open(toml_path, "w") as f:
            f.write("""[default]
host = "default.local"
port = 1234

[development]
host = "dev.local"

[production]
host = "prod.local"
port = 9999
""")
        # Default environment
        s = MiniDynaconf(settings_files=toml_path, environments=True)
        check("env default host", s.host, "default.local")
        check("env default port", s.port, 1234)

        # Development environment
        s2 = MiniDynaconf(settings_files=toml_path, environments=True, env="development")
        check("env dev host", s2.host, "dev.local")
        check("env dev port (from default)", s2.port, 1234)

        # Production environment
        s3 = MiniDynaconf(settings_files=toml_path, environments=True, env="production")
        check("env prod host", s3.host, "prod.local")
        check("env prod port", s3.port, 9999)

    import shutil
    shutil.rmtree(tmp)


def test_export_reload():
    print("\n=== Export / Reload ===")
    s = MiniDynaconf(defaults={
        "database": {"host": "db.local", "port": 5432},
        "debug": True,
    })
    d = s.as_dict()
    check("export keys uppercase", "DATABASE" in d, True)
    check("export nested uppercase", "HOST" in d["DATABASE"], True)

    # Write as_dict to JSON and reload
    tmp = tempfile.mkdtemp()
    json_path = os.path.join(tmp, "exported.json")
    with open(json_path, "w") as f:
        json.dump(d, f)
    s2 = MiniDynaconf(settings_files=json_path)
    check("reload host", s2.database.host, "db.local")
    check("reload port", s2.database.port, 5432)
    check("reload debug", s2.debug, True)

    import shutil
    shutil.rmtree(tmp)


def test_empty_falsey():
    print("\n=== Empty / Falsey ===")
    s = MiniDynaconf(defaults={
        "empty_list": [],
        "empty_dict": {},
        "empty_str": "",
        "zero": 0,
        "false": False,
    })
    check("empty list exists", s.exists("empty_list"), True)
    check("empty dict exists", s.exists("empty_dict"), True)
    check("empty str exists", s.exists("empty_str"), True)
    check("zero exists", s.exists("zero"), True)
    check("false exists", s.exists("false"), True)
    check("empty list is []", s.empty_list, [])
    check("zero is 0", s.zero, 0)
    check("false is False", s.false, False)


def test_dotenv():
    print("\n=== Dotenv ===")
    tmp = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    os.chdir(tmp)

    with open(".env", "w") as f:
        f.write("APP_DOTENV_KEY=dotenv_value\n")
        f.write("APP_DOTENV_PORT=7777\n")
        f.write("# comment\n")
        f.write("OTHER_KEY=ignored\n")

    s = MiniDynaconf(envvar_prefix="APP", load_dotenv=True)
    check("dotenv key", s.dotenv_key, "dotenv_value")
    check("dotenv port cast", s.dotenv_port, 7777)
    check("other key ignored", s.exists("other_key"), False)

    os.chdir(old_cwd)
    import shutil
    shutil.rmtree(tmp)


def test_secrets():
    print("\n=== Secrets ===")
    tmp = tempfile.mkdtemp()
    json_path = os.path.join(tmp, "secrets.json")
    with open(json_path, "w") as f:
        json.dump({"api_key": "secret123", "db_password": "pw456"}, f)

    # Secrets override everything except runtime
    s = MiniDynaconf(
        defaults={"api_key": "default_key"},
        secrets_files=json_path,
    )
    check("secret overrides default", s.api_key, "secret123")

    # Runtime overrides secrets
    s.set("api_key", "runtime_key")
    check("runtime overrides secret", s.api_key, "runtime_key")

    import shutil
    shutil.rmtree(tmp)


def test_load_file_post_construction():
    print("\n=== load_file post-construction ===")
    tmp = tempfile.mkdtemp()

    s = MiniDynaconf(defaults={"x": 1})

    json_path = os.path.join(tmp, "extra.json")
    with open(json_path, "w") as f:
        json.dump({"x": 100, "y": 200}, f)

    s.load_file(json_path)
    check("load_file overrides x", s.x, 100)
    check("load_file adds y", s.y, 200)

    # silent=True: missing file ignored
    s.load_file("/nonexistent/file.json", silent=True)
    check("silent missing ignored", s.x, 100)

    # silent=False: missing file raises
    try:
        s.load_file("/nonexistent/file.json", silent=False)
        fail("Should raise SettingsError for missing file")
    except SettingsError:
        print("  [OK] SettingsError for missing file (silent=False)")

    import shutil
    shutil.rmtree(tmp)


def test_validation_atomic():
    print("\n=== Validation Atomicity ===")
    # When validator A applies a default but validator B fails,
    # validator A's default should be rolled back.
    # Construction runs validators, so it raises.
    try:
        MiniDynaconf(
            validators=[
                Validator("timeout", default=30),  # applies default
                Validator("port", required=True),   # fails
            ],
        )
        fail("Should raise ValidationError for missing required")
    except ValidationError:
        print("  [OK] ValidationError raised during construction")
    # Create a valid settings object and test atomicity of set()
    s = MiniDynaconf(
        defaults={"timeout": 30, "port": 8080},
        validators=[
            Validator("timeout", gt=0),
            Validator("port", gt=1024),
        ],
    )
    try:
        s.set("port", 80, validate=True)
        fail("Should raise ValidationError for invalid port")
    except ValidationError:
        print("  [OK] ValidationError for bad port")
    check("port unchanged", s.port, 8080)
    check("timeout unchanged", s.timeout, 30)


def test_nonexistent_access():
    print("\n=== Nonexistent Key Access ===")
    s = MiniDynaconf()

    try:
        _ = s.nonexistent
        fail("Should raise AttributeError")
    except AttributeError:
        print("  [OK] AttributeError for missing attr")

    try:
        _ = s["nonexistent"]
        fail("Should raise KeyError")
    except KeyError:
        print("  [OK] KeyError for missing item")

    check("get returns default", s.get("nonexistent", "fallback"), "fallback")
    check("exists returns False", s.exists("nonexistent"), False)


def test_nested_yaml():
    print("\n=== Nested YAML ===")
    tmp = tempfile.mkdtemp()
    yaml_path = os.path.join(tmp, "nested.yaml")
    with open(yaml_path, "w") as f:
        f.write("""database:
  host: yamlhost
  port: 5432
  credentials:
    user: admin
    pass: secret
""")
    s = MiniDynaconf(settings_files=yaml_path)
    check("yaml nested host", s.database.host, "yamlhost")
    check("yaml nested port", s.database.port, 5432)
    check("yaml double nested", s.database.credentials.user, "admin")

    import shutil
    shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_file_loading()
    test_type_casting()
    test_environment_variables()
    test_layer_priority()
    test_validators()
    test_runtime_api()
    test_environments()
    test_export_reload()
    test_empty_falsey()
    test_dotenv()
    test_secrets()
    test_load_file_post_construction()
    test_validation_atomic()
    test_nonexistent_access()
    test_nested_yaml()

    print(f"\n{'='*40}")
    print(f"Failed: {_failed}")
    if _failed:
        sys.exit(1)
