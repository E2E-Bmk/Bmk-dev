def test_a01(tmp_path):
    from packaging.version import Version
    assert Version("1.0rc1") < Version("1.0") < Version("1.0.post1")
    assert str(Version("01.0+ABC.1")) == "1.0+abc.1"

def test_a02(tmp_path):
    from packaging.version import Version
    value = Version("2!1.2.0.dev3")
    assert (value.epoch, value.release, value.dev, value.is_devrelease) == (2, (1, 2, 0), 3, True)

def test_a03(tmp_path):
    from packaging.specifiers import SpecifierSet
    rules = SpecifierSet("~=1.4,!=1.5.0")
    assert rules.contains("1.4.9") and not rules.contains("1.5.0") and not rules.contains("2.0")

def test_a04(tmp_path):
    from packaging.requirements import Requirement
    item = Requirement("Demo[fast]>=2; python_version >= '3.10'")
    assert item.name == "Demo" and item.extras == {"fast"} and str(item.specifier) == ">=2"

def test_a05(tmp_path):
    from packaging.markers import Marker
    marker = Marker("python_version >= '3.10' and extra == 'speed'")
    assert marker.evaluate({"python_version":"3.12", "extra":"speed"})
    assert not marker.evaluate({"python_version":"3.9", "extra":"speed"})

def test_a06(tmp_path):
    from packaging.tags import Tag, parse_tag
    values = parse_tag("py2.py3-none-any")
    assert values == frozenset({Tag("py2", "none", "any"), Tag("py3", "none", "any")})

def test_a07(tmp_path):
    from packaging.utils import canonicalize_name, canonicalize_version
    assert canonicalize_name("Hello.World_test") == "hello-world-test"
    assert canonicalize_version("01.0RC1") == "1rc1"

def test_a08(tmp_path):
    from packaging.utils import parse_wheel_filename
    name, version, build, tags = parse_wheel_filename("demo_pkg-1.2-3-py3-none-any.whl")
    assert str(name) == "demo-pkg" and str(version) == "1.2" and build == (3, "") and len(tags) == 1

def test_i01(tmp_path):
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
    candidates = [Version(item) for item in ("1.0.dev1", "1.0", "1.4", "2.0")]
    assert [str(item) for item in SpecifierSet(">=1,<2").filter(candidates)] == ["1.0", "1.4"]

def test_i02(tmp_path):
    from packaging.requirements import Requirement
    item = Requirement("demo>=1.2; implementation_name == 'cpython'")
    assert item.marker.evaluate({"implementation_name":"cpython"}) and item.specifier.contains("1.9")

def test_i03(tmp_path):
    from packaging.tags import Tag
    from packaging.utils import parse_wheel_filename
    _name, _version, _build, tags = parse_wheel_filename("demo-1.0-py2.py3-none-any.whl")
    assert Tag("py3", "none", "any") in tags and Tag("cp312", "none", "any") not in tags

def test_i04(tmp_path):
    from packaging.requirements import Requirement
    from packaging.version import Version
    item = Requirement("demo~=2.1; os_name == 'nt'")
    assert item.marker.evaluate({"os_name":"nt"}) and Version("2.8") in item.specifier and Version("3") not in item.specifier

def test_s01(tmp_path):
    from packaging.requirements import Requirement
    from packaging.version import Version
    requirements = [Requirement("alpha>=1,<3"), Requirement("alpha!=2.0")]
    versions = [Version(item) for item in ("1", "2", "2.1", "3")]
    assert [str(v) for v in versions if all(v in item.specifier for item in requirements)] == ["1", "2.1"]

def test_s02(tmp_path):
    from packaging.tags import Tag
    from packaging.utils import canonicalize_name, parse_wheel_filename
    name, version, _build, tags = parse_wheel_filename("Demo_Pkg-4.0-py3-none-any.whl")
    assert canonicalize_name(name) == "demo-pkg" and str(version) == "4.0" and Tag("py3", "none", "any") in tags
