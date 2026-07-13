"""Comprehensive tests for minipackaging module per PRD spec."""
import sys
sys.path.insert(0, '.')

from minipackaging import (
    Version, InvalidVersion,
    SpecifierSet, InvalidSpecifier,
    Requirement, InvalidRequirement,
    Marker, InvalidMarker,
    UndefinedEnvironmentName,
    default_environment,
    is_requirement_satisfied,
)

def test_version_parsing():
    """Test comprehensive version parsing per PRD."""
    print("Testing Version parsing...")
    
    # Basic versions
    assert str(Version('1.0.0')) == '1'
    assert str(Version('1.2.3')) == '1.2.3'
    assert str(Version('1.0')) == '1'
    
    # Epoch
    assert str(Version('1!2.0.0')) == '1!2'
    assert Version('1!2.0.0')._epoch == 1
    
    # Pre-releases (all supported spellings)
    assert str(Version('1.0a1')) == '1.a1'
    assert str(Version('1.0alpha1')) == '1.a1'
    assert str(Version('1.0b1')) == '1.b1'
    assert str(Version('1.0beta1')) == '1.b1'
    assert str(Version('1.0rc1')) == '1.rc1'
    assert str(Version('1.0c1')) == '1.rc1'
    assert str(Version('1.0pre1')) == '1.rc1'
    assert str(Version('1.0preview1')) == '1.rc1'
    
    # Pre-releases with dot separator
    assert str(Version('1.0.a1')) == '1.a1'
    
    # Post-releases (all supported spellings)
    assert str(Version('1.0.post1')) == '1.post1'
    assert str(Version('1.0rev1')) == '1.post1'
    assert str(Version('1.0r1')) == '1.post1'
    
    # Dev releases
    assert str(Version('1.0.dev1')) == '1.dev1'
    assert str(Version('1.0dev1')) == '1.dev1'
    
    # Local versions
    assert str(Version('1.0+local')) == '1+local'
    assert str(Version('1.0+local.123')) == '1+local.123'
    
    # Complex combinations
    assert str(Version('1.0.0a1.dev1')) == '1.a1.dev1'
    assert str(Version('1.0.0.post1.dev1')) == '1.post1.dev1'
    assert str(Version('1.0.0a1+local')) == '1.a1+local'
    
    print("  All Version parsing tests passed!")

def test_version_ordering():
    """Test version ordering per PEP 440."""
    print("Testing Version ordering...")
    
    # Basic ordering
    assert Version('1.0.0') < Version('2.0.0')
    assert Version('1.0.0') < Version('1.1.0')
    assert Version('1.0.0') < Version('1.0.1')
    
    # Epoch ordering
    assert Version('1.0.0') < Version('1!1.0.0')
    assert Version('2.0.0') < Version('1!1.0.0')  # epoch trumps release
    
    # Dev release ordering (dev < final)
    assert Version('1.0.0.dev1') < Version('1.0.0')
    assert Version('1.0.0.dev2') < Version('1.0.0.dev3')
    
    # Pre-release ordering (pre < final)
    assert Version('1.0.0a1') < Version('1.0.0')
    assert Version('1.0.0a1') < Version('1.0.0b1')
    assert Version('1.0.0b1') < Version('1.0.0rc1')
    assert Version('1.0.0rc1') < Version('1.0.0')
    
    # Post-release ordering (post > final)
    assert Version('1.0.0') < Version('1.0.0.post1')
    assert Version('1.0.0.post1') < Version('1.0.0.post2')
    
    # Full ordering: dev < pre < final < post
    assert Version('1.0.0.dev1') < Version('1.0.0a1')
    assert Version('1.0.0a1') < Version('1.0.0')
    assert Version('1.0.0') < Version('1.0.0.post1')
    
    # Local version ordering
    assert Version('1.0.0') < Version('1.0.0+local')
    assert Version('1.0.0+abc') < Version('1.0.0+local')  # string comparison
    
    # Trailing zeros ignored for equality
    assert Version('1.0.0') == Version('1')
    assert Version('1.2.0') == Version('1.2')
    
    print("  All Version ordering tests passed!")

def test_specifier_set():
    """Test specifier set parsing and contains."""
    print("Testing SpecifierSet...")
    
    # Basic specifiers
    s = SpecifierSet('>=1.0.0')
    assert s.contains('1.0.0')
    assert s.contains('2.0.0')
    assert not s.contains('0.9.0')
    
    # Multiple specifiers
    s = SpecifierSet('>=1.0.0,<2.0.0')
    assert s.contains('1.0.0')
    assert s.contains('1.9.9')
    assert not s.contains('2.0.0')
    assert not s.contains('0.9.9')
    
    # Compatible release
    s = SpecifierSet('~=1.4.2')
    assert s.contains('1.4.2')
    assert s.contains('1.4.5')
    assert not s.contains('1.5.0')
    
    # Exact match
    s = SpecifierSet('==1.0.0')
    assert s.contains('1.0.0')
    assert not s.contains('1.0.1')
    
    # Not equal
    s = SpecifierSet('!=1.0.0')
    assert not s.contains('1.0.0')
    assert s.contains('1.0.1')
    
    # Empty specifier (matches all)
    s = SpecifierSet('')
    assert s.contains('1.0.0')
    assert s.contains('2.0.0')
    
    print("  All SpecifierSet tests passed!")

def test_requirement_parsing():
    """Test requirement parsing per PEP 508."""
    print("Testing Requirement...")
    
    # Simple requirement
    r = Requirement('requests>=2.0.0')
    assert r.name == 'requests'
    assert str(r.name) == 'requests'
    assert r.extras == set()
    assert str(r.specifier) == '>=2'
    assert r.url is None
    assert r.marker is None
    
    # With extras
    r = Requirement('package[extra1,extra2]>=1.0.0')
    assert r.name == 'package'
    assert 'extra1' in r.extras
    assert 'extra2' in r.extras
    
    # With URL
    r = Requirement('package @ https://example.com/pkg.whl')
    assert r.name == 'package'
    assert r.url == 'https://example.com/pkg.whl'
    assert r.marker is None
    
    # With marker
    r = Requirement("package>=1.0.0; python_version >= '3.6'")
    assert r.name == 'package'
    assert r.marker is not None
    
    # Name normalization
    r = Requirement('My_Package')
    assert r.name == 'my-package'
    
    # URL with specifier should fail
    try:
        Requirement('package @ https://example.com/pkg.whl>=1.0.0')
        assert False, "Should have raised InvalidRequirement"
    except InvalidRequirement:
        pass
    
    print("  All Requirement tests passed!")

def test_marker_evaluation():
    """Test marker parsing and evaluation."""
    print("Testing Marker...")
    
    # Simple marker
    m = Marker('python_version >= "3.6"')
    assert m.evaluate({'python_version': '3.8'})
    assert not m.evaluate({'python_version': '3.5'})
    
    # Platform marker
    m = Marker('sys_platform == "win32"')
    assert m.evaluate({'sys_platform': 'win32'})
    assert not m.evaluate({'sys_platform': 'linux'})
    
    # Boolean operators
    m = Marker('python_version >= "3.6" and sys_platform == "win32"')
    assert m.evaluate({'python_version': '3.8', 'sys_platform': 'win32'})
    assert not m.evaluate({'python_version': '3.5', 'sys_platform': 'win32'})
    assert not m.evaluate({'python_version': '3.8', 'sys_platform': 'linux'})
    
    # Or operator
    m = Marker('sys_platform == "win32" or sys_platform == "linux"')
    assert m.evaluate({'sys_platform': 'win32'})
    assert m.evaluate({'sys_platform': 'linux'})
    assert not m.evaluate({'sys_platform': 'darwin'})
    
    # Parentheses
    m = Marker('(python_version >= "3.6" and sys_platform == "win32") or sys_platform == "linux"')
    assert m.evaluate({'python_version': '3.8', 'sys_platform': 'win32'})
    assert m.evaluate({'sys_platform': 'linux'})
    assert not m.evaluate({'python_version': '3.5', 'sys_platform': 'darwin'})
    
    # Extra marker
    m = Marker('extra == "dev"')
    assert m.evaluate(requested_extras={'dev'})
    assert not m.evaluate(requested_extras={'test'})
    
    # Missing variable
    try:
        m = Marker('unknown_var == "foo"')
        m.evaluate({})
        assert False, "Should have raised UndefinedEnvironmentName"
    except UndefinedEnvironmentName:
        pass
    
    # Default environment
    env = default_environment()
    assert 'python_version' in env
    assert 'sys_platform' in env
    assert 'os_name' in env
    
    print("  All Marker tests passed!")

def test_is_requirement_satisfied():
    """Test requirement satisfaction helper."""
    print("Testing is_requirement_satisfied...")
    
    # Basic satisfaction
    assert is_requirement_satisfied('requests>=2.0.0', '2.5.0')
    assert not is_requirement_satisfied('requests>=2.0.0', '1.5.0')
    
    # With marker that applies
    assert is_requirement_satisfied(
        "requests>=2.0.0; sys_platform == 'win32'",
        '2.5.0',
        environment={'sys_platform': 'win32'}
    )
    
    # With marker that doesn't apply (should be satisfied)
    assert is_requirement_satisfied(
        "requests>=2.0.0; sys_platform == 'linux'",
        '1.0.0',
        environment={'sys_platform': 'win32'}
    )
    
    # With extras
    assert is_requirement_satisfied(
        'package[dev]>=1.0.0',
        '1.5.0',
        requested_extras={'dev'}
    )
    
    print("  All is_requirement_satisfied tests passed!")

if __name__ == '__main__':
    test_version_parsing()
    test_version_ordering()
    test_specifier_set()
    test_requirement_parsing()
    test_marker_evaluation()
    test_is_requirement_satisfied()
    print("\n✅ All comprehensive tests passed!")