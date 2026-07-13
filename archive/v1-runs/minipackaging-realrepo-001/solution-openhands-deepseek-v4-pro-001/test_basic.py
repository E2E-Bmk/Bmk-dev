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
)

# ---- Version tests ----
print('=== Version ===')
v1 = Version('1.0')
print(f'1.0 -> {v1}, release={v1.release}, epoch={v1.epoch}')
assert str(v1) == '1', f'canonical should be 1, got {str(v1)}'

v2 = Version('1.0.0')
print(f'1.0.0 -> {v2}, equals 1.0: {v1 == v2}')
assert str(v2) == '1', f'canonical should be 1, got {str(v2)}'

v3 = Version('2.0')
print(f'2.0 > 1.0: {v3 > v1}')
assert v3 > v1

v4 = Version('1!1.0')
print(f'1!1.0 -> {v4}, epoch={v4.epoch}')
assert v4.epoch == 1
assert v4 > v1

v5 = Version('1.0a1')
print(f'1.0a1 -> {v5}')
assert str(v5) == '1a1'

v6 = Version('1.0.dev1')
print(f'1.0.dev1 -> {v6}')
assert str(v6) == '1.dev1'

v7 = Version('1.0.post1')
print(f'1.0.post1 -> {v7}')
assert str(v7) == '1.post1'

v8 = Version('1.0+local')
print(f'1.0+local -> {v8}')
assert str(v8) == '1+local'

print(f'dev < pre: {v6 < v5}')
assert v6 < v5, 'dev should be before pre'

print(f'pre < final: {v5 < v1}')
assert v5 < v1, 'pre should be before final'

print(f'final < post: {v1 < v7}')
assert v1 < v7, 'final should be before post'

print(f'no-local < with-local: {v1 < v8}')
assert v1 < v8, 'no local should be before with local'

# Epoch ordering
v9 = Version('1!0.5')
v10 = Version('0!9.9')
print(f'1!0.5 > 0!9.9: {v9 > v10}')
assert v9 > v10

# Invalid version
try:
    Version('not a version')
    print('ERROR: should have raised')
    assert False
except InvalidVersion:
    print('InvalidVersion raised correctly')

# Normalization
v_n1 = Version('1.0.alpha1')
print(f'1.0.alpha1 -> {v_n1}')
assert str(v_n1) == '1a1'

v_n2 = Version('1.0BETA2')
print(f'1.0BETA2 -> {v_n2}')
assert str(v_n2) == '1b2'

v_n3 = Version('1.0preview3')
print(f'1.0preview3 -> {v_n3}')
assert str(v_n3) == '1rc3'

v_n4 = Version('1.0-1')
print(f'1.0-1 -> {v_n4}')
assert str(v_n4) == '1.post1'

v_n5 = Version('1.0rev2')
print(f'1.0rev2 -> {v_n5}')
assert str(v_n5) == '1.post2'

v_n6 = Version('1.0+local.1.2')
print(f'1.0+local.1.2 -> {v_n6}')
assert str(v_n6) == '1+local.1.2'

print('\n=== SpecifierSet ===')
# Basic specifiers
s1 = SpecifierSet('>= 1.0')
print(f'>= 1.0: {s1}')
assert s1.contains('1.0')
assert s1.contains('2.0')
assert not s1.contains('0.9')

s2 = SpecifierSet('>= 1.0, < 2.0')
print(f'>= 1.0, < 2.0: {s2}')
assert s2.contains('1.0')
assert s2.contains('1.5')
assert not s2.contains('2.0')

s3 = SpecifierSet('== 1.0')
print(f'== 1.0: {s3}')
assert s3.contains('1.0')
assert s3.contains('1.0.0')  # trailing zeros ignored
assert not s3.contains('1.1')

# !=
s4 = SpecifierSet('!= 1.0')
print(f'!= 1.0: {s4}')
assert not s4.contains('1.0')
assert s4.contains('1.1')

# ~=
s5 = SpecifierSet('~= 1.4.2')
print(f'~= 1.4.2: {s5}')
assert s5.contains('1.4.2')
assert s5.contains('1.4.3')
assert s5.contains('1.4.99')
assert not s5.contains('1.5.0')
assert not s5.contains('1.4.1')

# Wildcard
s6 = SpecifierSet('== 1.2.*')
print(f'== 1.2.*: {s6}')
assert s6.contains('1.2')
assert s6.contains('1.2.0')
assert s6.contains('1.2.99')
assert not s6.contains('1.3.0')
assert not s6.contains('1.1.0')

s7 = SpecifierSet('!= 1.2.*')
print(f'!= 1.2.*: {s7}')
assert not s7.contains('1.2.0')
assert s7.contains('1.3.0')

# Prerelease filtering
s8 = SpecifierSet('>= 1.0')
print(f'>= 1.0 contains 1.1a1 (None): {s8.contains("1.1a1")}')
assert not s8.contains('1.1a1')  # prereleases excluded by default
assert s8.contains('1.1a1', prereleases=True)  # included when True
assert not s8.contains('1.1a1', prereleases=False)  # excluded when False

# Prerelease specifier clause includes prereleases
s9 = SpecifierSet('>= 1.0a1')
print(f'>= 1.0a1 contains 1.1a1 (None): {s9.contains("1.1a1")}')
assert s9.contains('1.1a1')  # clause has prerelease, so prereleases included

# Empty specifier
s10 = SpecifierSet('')
assert s10.contains('1.0')
assert s10.contains('999.0')

# Invalid specifier
try:
    SpecifierSet('~~~ 1.0')
    assert False
except InvalidSpecifier:
    print('InvalidSpecifier raised correctly')

print('\n=== Requirement ===')
r1 = Requirement('requests')
print(f'requests: name={r1.name}, extras={r1.extras}, specifier={r1.specifier}, marker={r1.marker}')
assert r1.name == 'requests'
assert str(r1) == 'requests'

r2 = Requirement('requests >= 2.0')
print(f'requests >= 2.0: {r2}')
assert r2.name == 'requests'
assert str(r2) == 'requests>=2'

r3 = Requirement('requests >= 2.0, < 3.0')
print(f'requests >= 2.0, < 3.0: {r3}')
assert str(r3) == 'requests>=2,<3'

r4 = Requirement('requests[security] >= 2.0')
print(f'requests[security] >= 2.0: {r4}')
assert 'security' in r4.extras
assert str(r4) == 'requests[security]>=2'

r5 = Requirement('requests[Security,JSON] >= 2.0')
print(f'requests[Security,JSON] >= 2.0: extras={r5.extras}')
assert r5.extras == {'json', 'security'}
assert str(r5) == 'requests[json,security]>=2'

r6 = Requirement('requests >= 2.0 ; python_version >= "3.6"')
print(f'requests >= 2.0 ; ...: {r6}')
assert r6.marker is not None
assert str(r6).startswith('requests>=2; ')

r7 = Requirement('requests @ https://example.com/pkg.tar.gz')
print(f'requests @ url: url={r7.url}')
assert r7.url == 'https://example.com/pkg.tar.gz'
assert str(r7) == 'requests@ https://example.com/pkg.tar.gz'

r8 = Requirement('My.Package_Name >= 1.0')
print(f'My.Package_Name: name={r8.name}')
assert r8.name == 'my.package-name'  # dots preserved, only _ -> -

# Invalid requirement
try:
    Requirement('>= 2.0')
    assert False
except InvalidRequirement:
    print('InvalidRequirement raised correctly')

print('\n=== Marker ===')
# Basic markers
m1 = Marker('python_version >= "3.6"')
print(f'python_version >= "3.6": {m1}, evaluate={m1.evaluate()}')

m2 = Marker('os_name == "posix"')
print(f'os_name == "posix": {m2}')

# Boolean operators
m3 = Marker('python_version >= "3.6" and os_name == "posix"')
print(f'python_version >= "3.6" and os_name == "posix": {m3}')

m4 = Marker('python_version >= "3.8" or python_version == "3.7"')
print(f'python_version >= "3.8" or python_version == "3.7": {m4}')

m5 = Marker('(python_version >= "3.6" and os_name == "posix") or sys_platform == "win32"')
print(f'parenthesized: {m5}')

# Extra
m6 = Marker('extra == "pdf"')
env = {'os_name': 'posix', 'sys_platform': 'linux'}
print(f'extra == "pdf" (no extras): {m6.evaluate(env)}')
assert not m6.evaluate(env)
print(f'extra == "pdf" (pdf, html): {m6.evaluate(env, {"pdf", "html"})}')
assert m6.evaluate(env, {"pdf", "html"})
print(f'extra == "pdf" (html): {m6.evaluate(env, {"html"})}')
assert not m6.evaluate(env, {"html"})

# Undefined variable
try:
    Marker('nonexistent == "value"').evaluate({})
    assert False
except UndefinedEnvironmentName:
    print('UndefinedEnvironmentName raised correctly')

# Invalid marker
try:
    Marker('python_version ===== "3.6"')
    assert False
except InvalidMarker:
    print('InvalidMarker raised correctly')

print('\n=== default_environment ===')
env = default_environment()
for k, v in sorted(env.items()):
    print(f'  {k}: {v!r}')
assert 'python_version' in env
assert 'os_name' in env
assert 'extra' not in env

print('\n=== is_requirement_satisfied ===')
assert is_requirement_satisfied('requests', '2.0')
assert is_requirement_satisfied('requests >= 2.0', '2.0')
assert is_requirement_satisfied('requests >= 2.0', '3.0')
assert not is_requirement_satisfied('requests >= 2.0', '1.0')
assert is_requirement_satisfied(Requirement('requests >= 2.0'), Version('2.0'))

# Marker not applicable
assert is_requirement_satisfied(
    'requests ; os_name == "nonexistent_os"', '1.0'
)

# With version-valued marker comparison
r = Requirement('requests >= 2.0 ; python_version >= "2.0"')
assert is_requirement_satisfied(r, '2.0')

print('\n=== All basic tests passed! ===')
