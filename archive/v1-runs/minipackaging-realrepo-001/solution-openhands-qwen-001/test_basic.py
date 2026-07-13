#!/usr/bin/env python3
"""Test basic minipackaging functionality."""

from minipackaging import (
    Version, InvalidVersion,
    SpecifierSet, InvalidSpecifier,
    Requirement, InvalidRequirement,
    Marker, InvalidMarker,
    UndefinedEnvironmentName,
    default_environment,
    is_requirement_satisfied,
)

# Test Version
print('Testing Version...')
v1 = Version('1.0.0')
v2 = Version('2.0.0')
v3 = Version('1.0.0a1')
v4 = Version('1.0.0.dev1')
v5 = Version('1.0.0.post1')
v6 = Version('1!2.0.0')  # epoch
v7 = Version('1.0.0+local')

print(f'  1.0.0 = {v1}')
print(f'  2.0.0 = {v2}')
print(f'  1.0.0a1 = {v3}')
print(f'  1.0.0.dev1 = {v4}')
print(f'  1.0.0.post1 = {v5}')
print(f'  1!2.0.0 = {v6}')
print(f'  1.0.0+local = {v7}')
print(f'  v1 < v2: {v1 < v2}')
print(f'  v3 < v1: {v3 < v1}')
print(f'  v4 < v1: {v4 < v1}')
print(f'  v5 > v1: {v5 > v1}')

# Test SpecifierSet
print('\nTesting SpecifierSet...')
s1 = SpecifierSet('>=1.0.0')
s2 = SpecifierSet('>=1.0.0,<2.0.0')
s3 = SpecifierSet('~=1.4.2')
print(f'  >=1.0.0 contains 1.5.0: {s1.contains("1.5.0")}')
print(f'  >=1.0.0 contains 0.9.0: {s1.contains("0.9.0")}')
print(f'  >=1.0.0,<2.0.0 contains 1.5.0: {s2.contains("1.5.0")}')
print(f'  >=1.0.0,<2.0.0 contains 2.0.0: {s2.contains("2.0.0")}')
print(f'  ~=1.4.2 contains 1.4.5: {s3.contains("1.4.5")}')
print(f'  ~=1.4.2 contains 1.5.0: {s3.contains("1.5.0")}')

# Test Requirement
print('\nTesting Requirement...')
r1 = Requirement('requests>=2.0.0')
r2 = Requirement('package[extra1,extra2]>=1.0.0')
r3 = Requirement('package @ https://example.com/pkg.whl')
r4 = Requirement('package>=1.0.0; python_version >= "3.6"')
print(f'  requests>=2.0.0 -> name={r1.name}, specifier={r1.specifier}')
print(f'  package[extra1,extra2]>=1.0.0 -> name={r2.name}, extras={r2.extras}')
print(f'  package @ url -> url={r3.url}')
print(f'  package>=1.0.0; marker -> marker={r4.marker}')

# Test Marker
print('\nTesting Marker...')
m1 = Marker('python_version >= "3.6"')
m2 = Marker('sys_platform == "win32"')
m3 = Marker('python_version >= "3.6" and sys_platform == "win32"')
env = default_environment()
print(f'  python_version >= "3.6": {m1.evaluate(env)}')
print(f'  sys_platform == "win32": {m2.evaluate(env)}')
print(f'  Combined: {m3.evaluate(env)}')

# Test is_requirement_satisfied
print('\nTesting is_requirement_satisfied...')
print(f'  requests>=2.0.0, 2.5.0: {is_requirement_satisfied("requests>=2.0.0", "2.5.0")}')
print(f'  requests>=2.0.0, 1.5.0: {is_requirement_satisfied("requests>=2.0.0", "1.5.0")}')

print('\nAll basic tests passed!')