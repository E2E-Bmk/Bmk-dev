# Spec2Repo oracle - integration tests for packaging-core-fullrepro-001
from __future__ import annotations
import re
import unittest.mock
from typing import TYPE_CHECKING, Any, cast
import pytest
from packaging.dependency_groups import CyclicDependencyGroup, DependencyGroupInclude, DependencyGroupResolver, DuplicateGroupNames, InvalidDependencyGroupObject, resolve_dependency_groups
from packaging.errors import ExceptionGroup
from packaging.requirements import Requirement
if TYPE_CHECKING:
    import sys
    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias
    GroupsTable: TypeAlias = 'dict[str, list[str | dict[str, str]]]'

def _group_contains(excinfo: pytest.ExceptionInfo[ExceptionGroup], exc_type: type[BaseException], *, match: str | re.Pattern[str] | None=None) -> bool:
    """
    pytest.raises().group_contains() cannot be used on ExceptionGroup
    because it doesn't inherit from `exceptiongroup.BaseExceptionGroup` on
    python versions < 3.11 .

    This is a similar helper, just for these tests.
    """
    exc_group = excinfo.value
    assert isinstance(exc_group, ExceptionGroup)
    for exc in exc_group.exceptions:
        if not isinstance(exc, exc_type):
            continue
        if match is not None and (not re.search(match, str(exc))):
            continue
        return True
    return False

def test_lookup_on_trivial_normalization() -> None:
    """Seam: protocol handoff — lookup on trivial normalization."""
    groups: GroupsTable = {'test': ['pytest']}
    resolver = DependencyGroupResolver(groups)
    parsed_group = resolver.lookup('Test')
    assert len(parsed_group) == 1
    assert isinstance(parsed_group[0], Requirement)
    req = parsed_group[0]
    assert req.name == 'pytest'

def test_lookup_with_include_result() -> None:
    """Seam: protocol handoff — lookup with include result."""
    groups: GroupsTable = {'test': ['pytest', {'include-group': 'runtime'}], 'runtime': ['click']}
    resolver = DependencyGroupResolver(groups)
    parsed_group = resolver.lookup('test')
    assert len(parsed_group) == 2
    assert isinstance(parsed_group[0], Requirement)
    assert parsed_group[0].name == 'pytest'
    assert isinstance(parsed_group[1], DependencyGroupInclude)
    assert parsed_group[1].include_group == 'runtime'

def test_lookup_does_not_trigger_cyclic_include() -> None:
    """Seam: protocol handoff — lookup does not trigger cyclic include."""
    groups: GroupsTable = {'group1': [{'include-group': 'group2'}], 'group2': [{'include-group': 'group1'}]}
    resolver = DependencyGroupResolver(groups)
    parsed_group = resolver.lookup('group1')
    assert len(parsed_group) == 1
    assert isinstance(parsed_group[0], DependencyGroupInclude)
    assert parsed_group[0].include_group == 'group2'

@pytest.mark.parametrize('group_name_declared', ['foo-bar', 'foo_bar', 'foo..bar'])
@pytest.mark.parametrize('group_name_used', ['foo-bar', 'foo_bar', 'foo..bar'])
def test_normalized_name_is_used_for_include_group_lookups(group_name_declared: str, group_name_used: str) -> None:
    """Seam: protocol handoff — normalized name is used for include group lookups."""
    groups: GroupsTable = {group_name_declared: ['spam'], 'eggs': [{'include-group': group_name_used}]}
    resolver = DependencyGroupResolver(groups)
    result = resolver.resolve('eggs')
    assert len(result) == 1
    assert isinstance(result[0], Requirement)
    req = result[0]
    assert req.name == 'spam'

def test_empty_group() -> None:
    """Seam: state consistency — empty group."""
    groups: GroupsTable = {'test': []}
    assert resolve_dependency_groups(groups, 'test') == ()

def test_str_list_group() -> None:
    """Seam: state consistency — str list group."""
    groups: GroupsTable = {'test': ['pytest']}
    assert resolve_dependency_groups(groups, 'test') == ('pytest',)

def test_single_include_group() -> None:
    """Seam: state consistency — single include group."""
    groups: GroupsTable = {'test': ['pytest', {'include-group': 'runtime'}], 'runtime': ['sqlalchemy']}
    assert set(resolve_dependency_groups(groups, 'test')) == {'pytest', 'sqlalchemy'}

def test_sdual_include_group() -> None:
    """Seam: state consistency — sdual include group."""
    groups: GroupsTable = {'test': ['pytest'], 'runtime': ['sqlalchemy']}
    assert set(resolve_dependency_groups(groups, 'test', 'runtime')) == {'pytest', 'sqlalchemy'}

def test_normalized_group_name() -> None:
    """Seam: config interaction — normalized group name."""
    groups: GroupsTable = {'TEST': ['pytest']}
    assert resolve_dependency_groups(groups, 'test') == ('pytest',)
import datetime
import sys
from pathlib import Path
import pytest
import tomli_w
from packaging.markers import Marker, default_environment
from packaging.pylock import (
    Package,
    PackageDirectory,
    PackageSdist,
    PackageVcs,
    PackageWheel,
    Pylock,
    PylockUnsupportedVersionError,
    PylockValidationError,
    is_valid_pylock_path,
    PackageArchive,
    PylockSelectError,
)
from packaging.specifiers import SpecifierSet
from packaging.utils import NormalizedName
from packaging.version import Version
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

@pytest.mark.parametrize(('file_name', 'valid'), [('pylock.toml', True), ('pylock.spam.toml', True), ('pylock.json', False), ('pylock..toml', False)])
def test_pylock_file_name(file_name: str, valid: bool) -> None:
    """Seam: state consistency — pylock file name."""
    assert is_valid_pylock_path(Path(file_name)) is valid

def test_toml_roundtrip() -> None:
    """Seam: state consistency — toml roundtrip."""
    pep751_example = (Path(__file__).parent / 'pylock' / 'pylock.spec-example.toml').read_text()
    pylock_dict = tomllib.loads(pep751_example)
    pylock = Pylock.from_dict(pylock_dict)
    assert tomli_w.dumps(pylock.to_dict()) == tomli_w.dumps(pylock_dict)

@pytest.mark.parametrize('version', ['1.0', '1.1'])
def test_pylock_version(version: str) -> None:
    """Seam: state consistency — pylock version."""
    data = {'lock-version': version, 'created-by': 'pip', 'packages': []}
    pylock = Pylock.from_dict(data)
    assert str(pylock.lock_version) == version
    assert pylock.created_by == 'pip'

@pytest.mark.parametrize('version', ['0.9', '2', '2.0', '2.1'])
def test_pylock_unsupported_version(version: str) -> None:
    """Seam: error propagation — pylock unsupported version."""
    data = {'lock-version': version, 'created-by': 'pip', 'packages': []}
    with pytest.raises(PylockUnsupportedVersionError):
        Pylock.from_dict(data)

def test_pylock_basic_package() -> None:
    """Seam: state consistency — pylock basic package."""
    data = {'lock-version': '1.0', 'created-by': 'pip', 'requires-python': '>=3.10', 'environments': ['os_name == "posix"'], 'packages': [{'name': 'example', 'version': '1.0', 'marker': 'os_name == "posix"', 'requires-python': '!=3.10.1,>=3.10', 'directory': {'path': '.', 'editable': False}}]}
    pylock = Pylock.from_dict(data)
    assert pylock.environments == [Marker('os_name == "posix"')]
    package = pylock.packages[0]
    assert package.version == Version('1.0')
    assert package.marker == Marker('os_name == "posix"')
    assert package.requires_python == SpecifierSet('>=3.10, !=3.10.1')
    assert pylock.to_dict() == data

def test_pylock_vcs_package() -> None:
    """Seam: state consistency — pylock vcs package."""
    data = {'lock-version': '1.0', 'created-by': 'pip', 'packages': [{'name': 'packaging', 'vcs': {'type': 'git', 'url': 'https://githhub/pypa/packaging', 'commit-id': '...'}}]}
    pylock = Pylock.from_dict(data)
    assert pylock.to_dict() == data

@pytest.mark.parametrize(('dist', 'expected_filename'), [(PackageSdist(name='example-1.0.tar.gz', hashes={}), 'example-1.0.tar.gz'), (PackageSdist(path='./example-1.0.tar.gz', hashes={}), 'example-1.0.tar.gz'), (PackageSdist(path='.\\example-1.0.tar.gz', hashes={}), 'example-1.0.tar.gz'), (PackageSdist(path='example-1.0.tar.gz', hashes={}), 'example-1.0.tar.gz'), (PackageSdist(url='https://example.com/example-1.0.tar.gz', hashes={}), 'example-1.0.tar.gz'), (PackageSdist(name='example-2.0.tar.gz', path='.\\example-1.0.tar.gz', hashes={}), 'example-2.0.tar.gz'), (PackageSdist(name='example-2.0.tar.gz', url='https://example.com/example-1.0.tar.gz', hashes={}), 'example-2.0.tar.gz'), (PackageSdist(url='https://example.com/example-2.0.tar.gz', path='./example-1.0.tar.gz', hashes={}), 'example-1.0.tar.gz'), (PackageWheel(name='example-1.0-py3-none-any.whl', hashes={}), 'example-1.0-py3-none-any.whl'), (PackageWheel(path='./example-1.0-py3-none-any.whl', hashes={}), 'example-1.0-py3-none-any.whl'), (PackageWheel(path='.\\example-1.0-py3-none-any.whl', hashes={}), 'example-1.0-py3-none-any.whl'), (PackageWheel(path='example-1.0-py3-none-any.whl', hashes={}), 'example-1.0-py3-none-any.whl'), (PackageWheel(url='https://example.com/example-1.0-py3-none-any.whl', hashes={}), 'example-1.0-py3-none-any.whl'), (PackageWheel(name='example-2.0-py3-none-any.whl', path='.\\example-1.0-py3-none-any.whl', hashes={}), 'example-2.0-py3-none-any.whl'), (PackageWheel(name='example-2.0-py3-none-any.whl', url='https://example.com/example-1.0-py3-none-any.whl', hashes={}), 'example-2.0-py3-none-any.whl'), (PackageWheel(url='https://example.com/example-2.0-py3-none-any.whl', path='./example-1.0-py3-none-any.whl', hashes={}), 'example-1.0-py3-none-any.whl')])
def test_dist_filename(dist: PackageSdist | PackageWheel, expected_filename: str) -> None:
    """Seam: state consistency — dist filename."""
    assert dist.filename == expected_filename

def test_pylock_extras_and_groups() -> None:
    """Seam: config interaction — pylock extras and groups."""
    data = {'lock-version': '1.0', 'created-by': 'pip', 'extras': ['feat1', 'feat2'], 'dependency-groups': ['dev', 'docs'], 'default-groups': ['dev'], 'packages': []}
    pylock = Pylock.from_dict(data)
    assert pylock.extras == ['feat1', 'feat2']
    assert pylock.dependency_groups == ['dev', 'docs']
    assert pylock.default_groups == ['dev']

def test_pylock_tool() -> None:
    """Seam: state consistency — pylock tool."""
    data = {'lock-version': '1.0', 'created-by': 'pip', 'packages': [{'name': 'example', 'sdist': {'name': 'example-1.0.tar.gz', 'path': './example-1.0.tar.gz', 'upload-time': datetime.datetime(2023, 10, 1, 0, 0, tzinfo=datetime.timezone.utc), 'hashes': {'sha256': 'f' * 40}}, 'tool': {'pip': {'foo': 'bar'}}}], 'tool': {'pip': {'version': '25.2'}}}
    pylock = Pylock.from_dict(data)
    assert pylock.tool == {'pip': {'version': '25.2'}}
    package = pylock.packages[0]
    assert package.tool == {'pip': {'foo': 'bar'}}

def test_is_direct() -> None:
    """Seam: state consistency — is direct."""
    direct_package = Package(name=NormalizedName('example'), directory=PackageDirectory(path='.'))
    assert direct_package.is_direct
    wheel_package = Package(name=NormalizedName('example'), wheels=[PackageWheel(url='https://example.com/example-1.0-py3-none-any.whl', hashes={'sha256': 'f' * 40})])
    assert not wheel_package.is_direct
import dataclasses
import sys
import pytest
from packaging.tags import Tag
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib
if TYPE_CHECKING:
    from packaging.markers import Environment
    from packaging.utils import NormalizedName

@dataclasses.dataclass
class Platform:
    tags: list[Tag]
    environment: Environment
_py312_linux = Platform(tags=[Tag('cp312', 'cp312', 'manylinux_2_17_x86_64'), Tag('py3', 'none', 'any')], environment={'implementation_name': 'cpython', 'implementation_version': '3.12.12', 'os_name': 'posix', 'platform_machine': 'x86_64', 'platform_release': '6.8.0-100-generic', 'platform_system': 'Linux', 'platform_version': '#100-Ubuntu SMP PREEMPT_DYNAMIC', 'python_full_version': '3.12.12', 'platform_python_implementation': 'CPython', 'python_version': '3.12', 'sys_platform': 'linux'})

def test_smoke_test() -> None:
    """Seam: lifecycle crossing — smoke test."""
    pylock_path = Path(__file__).parent / 'pylock' / 'pylock.spec-example.toml'
    lock = Pylock.from_dict(tomllib.loads(pylock_path.read_text()))
    for package, dist in lock.select(tags=_py312_linux.tags, environment=_py312_linux.environment):
        assert isinstance(package, Package)
        assert isinstance(dist, PackageWheel)
        assert package.name == 'example'
        assert dist.filename.endswith('.whl')

def test_package_select_by_marker() -> None:
    """Seam: protocol handoff — package select by marker."""
    pylock = Pylock(lock_version=Version('1.0'), created_by='some_tool', packages=[Package(name=cast('NormalizedName', 'tomli'), marker=Marker('python_version < "3.11"'), version=Version('1.0'), archive=PackageArchive(path='tomli-1.0.tar.gz', hashes={'sha256': 'abc123'})), Package(name=cast('NormalizedName', 'foo'), marker=Marker('python_version >= "3.11"'), version=Version('1.0'), archive=PackageArchive(path='foo-1.0.tar.gz', hashes={'sha256': 'abc123'}))])
    pylock.validate()
    selected = list(pylock.select(tags=_py312_linux.tags, environment=_py312_linux.environment))
    assert len(selected) == 1
    assert selected[0][0].name == 'foo'

def test_yield_all_types() -> None:
    """Seam: state consistency — yield all types."""
    pylock = Pylock(lock_version=Version('1.0'), created_by='some_tool', packages=[Package(name=cast('NormalizedName', 'foo-archive'), archive=PackageArchive(path='tomli-1.0.tar.gz', hashes={'sha256': 'abc123'})), Package(name=cast('NormalizedName', 'foo-directory'), directory=PackageDirectory(path='./foo-directory')), Package(name=cast('NormalizedName', 'foo-vcs'), vcs=PackageVcs(type='git', url='https://example.com/foo.git', commit_id='fa123')), Package(name=cast('NormalizedName', 'foo-sdist'), sdist=PackageSdist(path='foo_sdist-1.0.tar.gz', hashes={'sha256': 'abc123'})), Package(name=cast('NormalizedName', 'foo-wheel'), wheels=[PackageWheel(name='foo_wheel-1.0-py3-none-any.whl', path='./foo_wheel-1.0-py3-none-any.whl', hashes={'sha256': 'abc123'})])])
    pylock.validate()
    selected = list(pylock.select())
    assert len(selected) == 5

def test_sdist_fallback() -> None:
    """Seam: state consistency — sdist fallback."""
    pylock = Pylock(lock_version=Version('1.0'), created_by='some_tool', packages=[Package(name=cast('NormalizedName', 'foo'), sdist=PackageSdist(path='foo-1.0.tar.gz', hashes={'sha256': 'abc123'}), wheels=[PackageWheel(path='./foo-1.0-py5-none-any.whl', hashes={'sha256': 'abc123'})])])
    selected = list(pylock.select())
    assert len(selected) == 1
    assert isinstance(selected[0][1], PackageSdist)

@pytest.mark.parametrize(('extras', 'dependency_groups', 'expected'), [(None, None, ['foo', 'foo-dev']), (None, ['dev'], ['foo', 'foo-dev']), (None, [], ['foo']), (None, ['docs'], ['foo', 'foo-docs']), (None, ['dev', 'docs'], ['foo', 'foo-dev', 'foo-docs']), ([], None, ['foo', 'foo-dev']), (['feat1'], None, ['foo', 'foo-dev', 'foo-feat1']), (['feat2'], None, ['foo', 'foo-dev', 'foo-feat2']), (['feat1', 'feat2'], None, ['foo', 'foo-dev', 'foo-feat1', 'foo-feat2']), (['feat1', 'feat2'], ['docs'], ['foo', 'foo-docs', 'foo-feat1', 'foo-feat2'])])
def test_pylock_select_extras_and_groups(extras: list[str] | None, dependency_groups: list[str] | None, expected: list[str]) -> None:
    """Seam: protocol handoff — pylock select extras and groups."""
    pylock = Pylock(lock_version=Version('1.0'), created_by='some_tool', extras=[cast('NormalizedName', 'feat1'), cast('NormalizedName', 'feat2')], dependency_groups=['dev', 'docs'], default_groups=['dev'], packages=[Package(name=cast('NormalizedName', 'foo'), directory=PackageDirectory(path='./foo')), Package(name=cast('NormalizedName', 'foo-dev'), directory=PackageDirectory(path='./foo-dev'), marker=Marker("'dev' in dependency_groups")), Package(name=cast('NormalizedName', 'foo-docs'), directory=PackageDirectory(path='./foo-docs'), marker=Marker("'docs' in dependency_groups")), Package(name=cast('NormalizedName', 'foo-feat1'), directory=PackageDirectory(path='./foo-feat1'), marker=Marker("'feat1' in extras")), Package(name=cast('NormalizedName', 'foo-feat2'), directory=PackageDirectory(path='./foo-feat2'), marker=Marker("'feat2' in extras"))])
    pylock.validate()
    selected_names = [package.name for package, _ in pylock.select(extras=extras, dependency_groups=dependency_groups)]
    assert selected_names == expected

def test_python_prerelease() -> None:
    """Seam: config interaction — Pylock requires_python accepts non-PEP-440 prerelease python_full_version."""
    pylock = Pylock(lock_version=Version('1.0'), created_by='repro', requires_python=SpecifierSet('>=3.12'), packages=[Package(name=cast('NormalizedName', 'pkga'), requires_python=SpecifierSet('>=3.12'), directory=PackageDirectory(path='./pkga'))])
    env = default_environment()
    env['python_full_version'] = '3.15.0a8+'
    selected = [package.name for package, _ in pylock.select(environment=env)]
    assert selected == ['pkga']
import json
import pytest

def test_requirement_parses_url_extras_and_marker_together():
    """Seam: config interaction — requirement parses url extras and marker together."""
    from packaging.requirements import Requirement
    req = Requirement("Demo[PDF] @ https://example.com/demo.whl ; python_version >= '3.11'")
    assert req.name == 'Demo'
    assert req.extras == {'PDF'}
    assert req.url == 'https://example.com/demo.whl'
    assert 'python_version' in str(req.marker)

def test_metadata_from_raw_parses_requirements_into_public_objects():
    """Seam: config interaction — metadata from raw parses requirements into public objects."""
    from packaging.metadata import Metadata
    from packaging.requirements import Requirement
    metadata = Metadata.from_raw({'metadata_version': '2.1', 'name': 'demo', 'version': '1.0', 'requires_dist': ['dep>=2']})
    assert metadata.requires_dist == [Requirement('dep>=2')]

def test_direct_url_round_trips_archive_info_to_json():
    """Seam: state consistency — direct url round trips archive info to json."""
    from packaging.direct_url import ArchiveInfo, DirectUrl
    direct = DirectUrl(url='https://example.com/pkg.tar.gz', archive_info=ArchiveInfo(hashes={'sha256': 'abc'}))
    data = direct.to_dict()
    restored = DirectUrl.from_dict(data)
    assert data['url'] == 'https://example.com/pkg.tar.gz'
    assert data['archive_info']['hashes'] == {'sha256': 'abc'}
    assert restored == direct

def test_cross_component_requirement_marker_and_specifier_agree():
    """Seam: state consistency — cross component requirement marker and specifier agree."""
    from packaging.requirements import Requirement
    from packaging.version import Version
    req = Requirement("demo>=1.0; python_version >= '3.8'")
    assert Version('1.2') in req.specifier
    assert req.marker.evaluate({'python_version': '3.11'})
    assert not req.marker.evaluate({'python_version': '3.7'})

def test_requirement_version_and_marker_form_one_acceptance_decision():
    """Seam: config interaction — requirement version and marker form one acceptance decision."""
    from packaging.requirements import Requirement
    from packaging.version import Version
    req = Requirement("demo>=1.0,<2; python_version >= '3.10'")
    assert Version('1.8') in req.specifier and req.marker.evaluate({'python_version': '3.12'})
    assert Version('2.0') not in req.specifier
    assert not req.marker.evaluate({'python_version': '3.9'})

def test_requirement_extra_marker_and_version_gate_compose():
    """Seam: config interaction — requirement extra marker and version gate compose."""
    from packaging.requirements import Requirement
    from packaging.version import Version
    req = Requirement("demo[PDF]>=2; extra == 'pdf'")
    assert req.extras == {'PDF'}
    assert Version('2.3') in req.specifier
    assert req.marker.evaluate({'extra': 'PDF'})
    assert not req.marker.evaluate({'extra': 'docs'})

def test_prerelease_ordering_respects_specifier_policy():
    """Seam: config interaction — prerelease ordering respects specifier policy."""
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
    versions = [Version(value) for value in ('2.0', '1.5', '2.0rc1', '1.0')]
    allowed = SpecifierSet('>=1,<2')
    assert sorted(versions) == [Version('1.0'), Version('1.5'), Version('2.0rc1'), Version('2.0')]
    assert [value for value in versions if value in allowed] == [Version('1.5'), Version('1.0')]

def test_compatible_release_and_platform_marker_agree():
    """Seam: state consistency — compatible release and platform marker agree."""
    from packaging.markers import Marker
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
    versions = SpecifierSet('~=3.11.2')
    platform = Marker("sys_platform == 'linux'")
    assert Version('3.11.9') in versions
    assert Version('3.12.0') not in versions
    assert platform.evaluate({'sys_platform': 'linux'})
    assert not platform.evaluate({'sys_platform': 'win32'})

def test_metadata_requirements_drive_marker_and_version_checks():
    """Seam: config interaction — metadata requirements drive marker and version checks."""
    from packaging.metadata import Metadata
    from packaging.requirements import Requirement
    from packaging.version import Version
    metadata = Metadata.from_raw({'metadata_version': '2.1', 'name': 'demo', 'version': '1.0', 'requires_dist': ["dep>=2; python_version >= '3.10'"]})
    dependency = metadata.requires_dist[0]
    assert isinstance(dependency, Requirement)
    assert Version('2.4') in dependency.specifier
    assert dependency.marker.evaluate({'python_version': '3.11'})
    assert not dependency.marker.evaluate({'python_version': '3.9'})

def test_wheel_filename_projects_name_version_build_and_tags():
    """Seam: state consistency — wheel filename projects name version build and tags."""
    from packaging.tags import Tag
    from packaging.utils import parse_wheel_filename
    from packaging.version import Version
    name, version, build, tags = parse_wheel_filename('Demo_Pkg-1.2-3-py3-none-any.whl')
    assert name == 'demo-pkg'
    assert version == Version('1.2')
    assert build == (3, '')
    assert Tag('py3', 'none', 'any') in tags

def test_sdist_filename_projects_canonical_name_and_ordered_version():
    """Seam: state consistency — sdist filename projects canonical name and ordered version."""
    from packaging.utils import canonicalize_name, parse_sdist_filename
    from packaging.version import Version
    name, version = parse_sdist_filename('Demo_Pkg-1.4.tar.gz')
    assert name == canonicalize_name('Demo_Pkg')
    assert version == Version('1.4')
    assert Version('1.3') < version < Version('2')

def test_requirement_name_canonicalization_preserves_specifier_semantics():
    """Seam: state consistency — requirement name canonicalization preserves specifier semantics."""
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    from packaging.version import Version
    req = Requirement('Demo_Pkg!=1.5,>=1')
    assert canonicalize_name(req.name) == 'demo-pkg'
    assert Version('1.4') in req.specifier
    assert Version('1.5') not in req.specifier

def test_marker_boolean_expression_controls_requirement_applicability():
    """Seam: config interaction — marker boolean expression controls requirement applicability."""
    from packaging.requirements import Requirement
    from packaging.version import Version
    req = Requirement("demo>=1; (python_version >= '3.10' and platform_machine == 'x86_64') or sys_platform == 'darwin'")
    assert Version('1.1') in req.specifier
    assert req.marker.evaluate({'python_version': '3.11', 'platform_machine': 'x86_64', 'sys_platform': 'linux'})
    assert req.marker.evaluate({'python_version': '3.8', 'platform_machine': 'arm64', 'sys_platform': 'darwin'})
    assert not req.marker.evaluate({'python_version': '3.8', 'platform_machine': 'arm64', 'sys_platform': 'linux'})

def test_requirement_url_extras_and_environment_remain_consistent():
    """Seam: state consistency — requirement url extras and environment remain consistent."""
    from packaging.requirements import Requirement
    req = Requirement("Demo[fast] @ https://example.invalid/demo-1.0.whl ; os_name == 'posix'")
    assert req.name == 'Demo'
    assert req.extras == {'fast'}
    assert req.url.endswith('demo-1.0.whl')
    assert req.marker.evaluate({'os_name': 'posix'})
    assert not req.marker.evaluate({'os_name': 'nt'})
