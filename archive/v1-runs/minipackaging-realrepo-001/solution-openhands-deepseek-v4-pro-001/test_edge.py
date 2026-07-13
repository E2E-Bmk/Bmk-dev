"""Edge case tests for minipackaging."""
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

print("=== Version edge cases ===")

# Zero versions
assert Version('0') == Version('0.0') == Version('0.0.0')
assert str(Version('0')) == '0'
assert str(Version('0.0')) == '0'
assert str(Version('0.0.0')) == '0'
print('Zero versions: OK')

# Pre-release ordering
a = Version('1.0a1')
b = Version('1.0b1')
c = Version('1.0rc1')
d = Version('1.0')
assert a < b < c < d, f'pre-release ordering: {a} < {b} < {c} < {d}'
print('Pre-release ordering: OK')

# Dev < pre
dev = Version('1.0.dev1')
assert dev < a
print('Dev < pre: OK')

# Post > final
post = Version('1.0.post1')
assert d < post
print('Final < post: OK')

# Epoch ordering
assert Version('1!0.5') > Version('0!9.9')
assert Version('2!1.0') > Version('1!99.99')
print('Epoch ordering: OK')

# Implicit post (dash-number)
assert str(Version('1.0-1')) == '1.post1'
assert str(Version('1.0-0')) == '1.post0'
print('Implicit post: OK')

# Pre-release without number
assert str(Version('1.0a')) == '1a0'
assert str(Version('1.0.dev')) == '1.dev0'
print('Implicit numbers: OK')

# Normalization
assert str(Version('1.0.alpha1')) == '1a1'
assert str(Version('1.0.ALPHA1')) == '1a1'
assert str(Version('1.0.bEtA2')) == '1b2'
assert str(Version('1.0.RC3')) == '1rc3'
assert str(Version('1.0.Rev2')) == '1.post2'
assert str(Version('1.0.R2')) == '1.post2'
print('Case normalization: OK')

# Local versions
assert Version('1.0+abc') == Version('1.0+abc')
assert Version('1.0+abc') < Version('1.0+abc.1')
assert Version('1.0+1') < Version('1.0+2')
assert Version('1.0+a') < Version('1.0+b')
# String < int at same position
assert Version('1.0+a') < Version('1.0+1')
print('Local version ordering: OK')

print("\n=== SpecifierSet edge cases ===")

# ~= with single segment
s = SpecifierSet('~= 1')
assert s.contains('1')
assert s.contains('1.9')
assert not s.contains('2.0')
print('~= 1: OK')

# ~= with two segments
s = SpecifierSet('~= 1.4')
assert s.contains('1.4')
assert s.contains('1.99')
assert not s.contains('2.0')
print('~= 1.4: OK')

# ~= with trailing-zero version
s = SpecifierSet('~= 1.4.0')
assert s.contains('1.4.0')
assert s.contains('1.4')
assert s.contains('1.99')
assert not s.contains('2.0')
print('~= 1.4.0: OK')

# ~= with epoch
s = SpecifierSet('~= 1!1.4.2')
assert s.contains('1!1.4.2')
assert s.contains('1!1.4.99')
assert not s.contains('1!1.5.0')
assert not s.contains('1!1.4.1')
print('~= with epoch: OK')

# Multiple specifiers
s = SpecifierSet('>= 1.0, != 1.5, < 2.0')
assert s.contains('1.0')
assert s.contains('1.4')
assert not s.contains('1.5')
assert not s.contains('2.0')
print('Multiple specifiers: OK')

# Empty specifier
s = SpecifierSet('')
assert s.contains('1.0')
assert s.contains('999.0')
assert bool(s) is False
print('Empty specifier: OK')

# Wildcard
s = SpecifierSet('== 0.*')
assert s.contains('0')
assert s.contains('0.0')
assert s.contains('0.9')
assert s.contains('0.99.1')
assert not s.contains('1.0')
print('Wildcard == 0.*: OK')

# Wildcard with trailing zeros in specifier
s = SpecifierSet('== 1.2.0.*')
# After stripping, version 1.2.0 -> 1.2, prefix is (1, 2)
assert s.contains('1.2')
assert s.contains('1.2.0')
assert s.contains('1.2.3')
assert not s.contains('1.3')
print('Wildcard with trailing zeros: OK')

# Prerelease filtering
s = SpecifierSet('>= 1.0')
assert not s.contains('1.1a1')
assert s.contains('1.1a1', prereleases=True)
assert not s.contains('1.1a1', prereleases=False)
print('Prerelease filtering (final-only bounds): OK')

# Multi-clause with prerelease clause
s = SpecifierSet('>= 1.0, >= 1.0a1')
assert s.contains('1.1a1')  # prereleases=None but clause targets prerelease
print('Multi-clause prerelease: OK')

print("\n=== Requirement edge cases ===")

# No spaces
r = Requirement('requests>=2.0')
assert r.name == 'requests'
assert str(r.specifier) == '>=2'
print('No spaces: OK')

# Extras only
r = Requirement('requests[extra1,extra2]')
assert r.extras == {'extra1', 'extra2'}
assert str(r) == 'requests[extra1,extra2]'
print('Extras only: OK')

# URL with marker
r = Requirement('requests @ https://example.com/pkg ; python_version >= "3.6"')
assert r.url == 'https://example.com/pkg'
assert r.marker is not None
print('URL with marker: OK')

# URL with extras
r = Requirement('requests[extra] @ https://example.com/pkg')
assert r.extras == {'extra'}
assert r.url == 'https://example.com/pkg'
print('URL with extras: OK')

# Name normalization
r = Requirement('My_Package.Name')
assert r.name == 'my-package.name'
print('Name normalization: OK')

# URL form: everything after @ up to ; is the URL
# "requests @ https://x.com >= 2.0" -> URL includes the >= clause
r = Requirement('requests @ https://x.com >= 2.0')
assert r.url == 'https://x.com >= 2.0'
assert not r.specifier  # no specifier when URL is present
print('URL captures everything after @: OK')

# Reject bare specifier (no name)
try:
    Requirement('>= 2.0')
    assert False
except InvalidRequirement:
    pass
print('Bare specifier rejection: OK')

# Extras with whitespace
r = Requirement('requests[ extra1 , extra2 ] >= 2.0')
assert r.extras == {'extra1', 'extra2'}
print('Extras whitespace: OK')

print("\n=== Marker edge cases ===")

# in / not in operators
m = Marker('"linux" in sys_platform')
env = {'sys_platform': 'linux'}
assert m.evaluate(env)

m = Marker('"win" not in sys_platform')
env = {'sys_platform': 'linux'}
assert m.evaluate(env)
print('in/not in operators: OK')

# Version-valued comparison
m = Marker('python_full_version >= "3.6.0"')
assert m.evaluate()  # We're on 3.14.x
print('Version-valued comparison: OK')

# Complex boolean
m = Marker('(python_version >= "2.0" and os_name == "nt") or (python_version >= "4.0")')
assert m.evaluate()
print('Complex boolean: OK')

# Extra normalization
m = Marker('extra == "Pdf"')
env = {'os_name': 'posix', 'sys_platform': 'linux'}
assert not m.evaluate(env)
assert m.evaluate(env, {'pdf'})
assert m.evaluate(env, {'PDF'})
assert not m.evaluate(env, {'html'})
print('Extra normalization: OK')

# Nested parentheses
m = Marker('((python_version >= "3.6"))')
assert m.evaluate()
print('Nested parens: OK')

# Canonical marker string
m = Marker('python_version >= "3.6" and os_name == "posix"')
s = str(m)
assert '>=' in s and 'and' in s
print(f'Canonical marker: {s}')

# Extra canonical form
m = Marker('extra == "Pdf"')
assert str(m) == 'extra == "pdf"'
print('Extra canonical normalization: OK')

print("\n=== is_requirement_satisfied edge cases ===")

# String args
assert is_requirement_satisfied('requests', '2.0')
assert is_requirement_satisfied(Requirement('requests'), Version('2.0'))

# Non-applicable marker = satisfied
assert is_requirement_satisfied(
    'requests ; os_name == "nonexistent_os"', '1.0'
)

# Version-valued marker comparison
assert is_requirement_satisfied(
    'requests >= 2.0 ; python_version >= "2.0"', '2.0'
)

# With prereleases: 2.0a1 < 2.0, so still fails >= 2.0
assert not is_requirement_satisfied('requests >= 2.0', '2.0a1')
# 2.5a1 > 2.0, but excluded by prereleases=None; allowed with prereleases=True
assert not is_requirement_satisfied('requests >= 2.0', '2.5a1')
assert is_requirement_satisfied('requests >= 2.0', '2.5a1', prereleases=True)

print('is_requirement_satisfied: OK')

print("\n=== All edge case tests passed! ===")
