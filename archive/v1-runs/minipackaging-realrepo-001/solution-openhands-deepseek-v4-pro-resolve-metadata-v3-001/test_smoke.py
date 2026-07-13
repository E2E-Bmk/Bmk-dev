"""Basic smoke tests for minipackaging."""
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
    resolve_metadata,
)

print('1. All imports OK')

# Test Version
v = Version('1.2.3')
assert str(v) == '1.2.3', f"got {str(v)}"
print('2. Version basic parse/str OK')

# Test canonical: trailing zeros stripped
v2 = Version('1.0.0')
assert str(v2) == '1', f"got {str(v2)}"
print('3. Version trailing zeros OK')

# Test ordering
assert Version('1.0.0') < Version('2.0.0')
assert Version('1.0.0a1') < Version('1.0.0')
print('4. Version ordering OK')

# Test epoch
v3 = Version('1!1.0')
assert str(v3) == '1!1', f"got {str(v3)}"
assert v3 > Version('1.0')
print('5. Version epoch OK')

# Test local
v4 = Version('1.0+local.1')
assert str(v4) == '1+local.1', f"got {str(v4)}"
print('6. Version local OK')

# Test SpecifierSet (versions use canonical form with trailing zeros stripped)
s = SpecifierSet('>=1.0,<2.0')
assert s.contains('1.5.0')
assert not s.contains('2.0.0')
print('7. SpecifierSet basic OK')

# Test wildcard
s2 = SpecifierSet('==1.0.*')
assert s2.contains('1.0.1')
assert s2.contains('1.0.5')
assert not s2.contains('1.1.0')
print('8. SpecifierSet wildcard OK')

# Test ~=
s3 = SpecifierSet('~=1.4')
assert s3.contains('1.4.0')
assert s3.contains('1.4.5')
assert not s3.contains('1.5.0')
print('9. SpecifierSet compatible OK')

# Test Requirement
r = Requirement('requests>=2.0,<3.0')
assert r.name == 'requests', f"got {r.name}"
assert r.url is None
assert r.marker is None
print('10. Requirement basic OK')

# Test Requirement with extras
r2 = Requirement('name[extra1,extra2]>=1.0')
assert r2.name == 'name', f"got {r2.name}"
assert r2.extras == {'extra1', 'extra2'}, f"got {r2.extras}"
print('11. Requirement extras OK')

# Test Requirement with URL
r3 = Requirement('name@https://example.com/pkg.zip')
assert r3.url == 'https://example.com/pkg.zip', f"got {r3.url}"
print('12. Requirement URL OK')

# Test Requirement with marker
r4 = Requirement('name;python_version>="3.8"')
assert r4.marker is not None
print('13. Requirement marker OK')

# Test URL + specifier is invalid
try:
    Requirement('name>=1.0@https://example.com/pkg.zip')
    assert False, "should have raised"
except InvalidRequirement:
    print('14. URL+specifier rejection OK')

# Test Marker
m = Marker('python_version >= "3.8"')
assert m.evaluate({'python_version': '3.9'})
assert not m.evaluate({'python_version': '3.7'})
print('15. Marker basic OK')

# Test default_environment
env = default_environment()
assert 'python_version' in env
print('16. default_environment OK')

# Test is_requirement_satisfied
assert is_requirement_satisfied('requests>=2.0', '2.28.0')
assert not is_requirement_satisfied('requests>=3.0', '2.28.0')
assert is_requirement_satisfied('requests>=2.0;python_version>="3.9"', '2.28.0',
                                {'python_version': '3.10'})
assert is_requirement_satisfied('requests>=2.0;python_version<"3.8"', '2.28.0',
                                {'python_version': '3.10'})
print('17. is_requirement_satisfied OK')

# Test resolve_metadata basic
roots = ['a>=1.0']
candidates = [
    {'name': 'a', 'version': '1.0'},
    {'name': 'a', 'version': '2.0'},
]
result = resolve_metadata(roots, candidates)
assert 'selected' in result
assert result['selected'].get('a') == '2.0', f"got {result['selected']}"
assert 'a' in result['excluded']
assert '1.0' in result['excluded']['a']
print('18. resolve_metadata basic OK')

# Test resolve_metadata with deps
roots = ['a>=1.0']
candidates = [
    {'name': 'a', 'version': '1.0', 'requires': ['b>=1.0']},
    {'name': 'b', 'version': '1.0'},
    {'name': 'b', 'version': '2.0'},
]
result = resolve_metadata(roots, candidates)
assert result['selected']['a'] == '1.0'
assert result['selected']['b'] == '2.0'
print('19. resolve_metadata transitive deps OK')

print()
print('ALL SMOKE TESTS PASSED!')
