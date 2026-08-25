# Spec2Repo oracle - atomic tests for packaging-core-fullrepro-001
from __future__ import annotations
import pickle
import pytest
from packaging.markers import Marker
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import SpecifierSet
EQUAL_DEPENDENCIES = [('widgetlib>3.2', 'widgetlib>3.2'), ('datalib[alpha, beta]>=1.2.3,==1.2.*;python_version<"2.7"', 'datalib [alpha,beta] >= 1.2.3, == 1.2.* ; python_version < "2.7"'), ('compatlib; python_version<"3.8"', "compatlib; python_version<'3.8'"), ('pathutil>=2.1.4,<3; os_name=="posix" and extra=="testing"', "pathutil>=2.1.4,<3; os_name == 'posix' and extra == 'testing'")]
EQUIVALENT_DEPENDENCIES = [('num-kit==2.3.4', 'num_kit==2.3.4'), ('bar==2.0.0', 'bar==2.0.0.0'), ('bar>=2.0', 'bar>=2.0.0'), ('bar[a]==2.0.0; python_version>="3.8"', 'bar[a]==2.0.0.0; python_version>="3.8"'), ('fetchlib[secure]', 'fetchlib[SECURE]'), ('aquarium[all-blue]', 'aquarium[all_blue]'), ('aquarium[all-blue]', 'aquarium[all---blue]'), ('aquarium[crazy-bunches]', 'aquarium[cRazy_BUnches]')]
DIFFERENT_DEPENDENCIES = [('package_one', 'package_two'), ('widgetlib>3.2', 'widgetlib>=3.2'), ('widgetlib>3.2', 'widgetlib>4.2'), ('widgetlib>3.2', 'gadgetlib>3.2'), ('datalib[alpha,beta]>=1.2.3,==1.2.*;python_version<"2.7"', 'datalib [alpha,beta] >= 1.2.3 ; python_version < "2.7"'), ('compatlib; python_version<"3.8"', "compatlib; python_version<'3.7'"), ('pathutil>=2.1.4,<3; os_name=="posix" and extra=="testing"', "pathutil>=2.1.4,<3; os_name == 'posix' and extra == 'docs'")]

@pytest.mark.parametrize('name', ['package', 'pAcKaGe', 'Package', 'foo-bar.quux_bAz', 'installer', 'android12'])
@pytest.mark.parametrize('extras', [set(), {'a'}, {'a', 'b'}, {'a', 'B', 'CDEF123'}])
@pytest.mark.parametrize(('url', 'specifier'), [(None, ''), ('https://example.com/packagename.zip', ''), ('ssh://user:pass%20word@example.com/packagename.zip', ''), ('https://example.com/name;v=1.1/?query=foo&bar=baz#blah', ''), ('git+ssh://git.example.com/MyProject', ''), ('git+ssh://git@github.com:pypa/packaging.git', ''), ('git+https://git.example.com/MyProject.git@master', ''), ('git+https://git.example.com/MyProject.git@v1.0', ''), ('git+https://git.example.com/MyProject.git@refs/pull/123/head', ''), ('gopher:/foo/com', ''), (None, '==={ws}arbitrarystring'), (None, '({ws}==={ws}arbitrarystring{ws})'), (None, '=={ws}1.0'), (None, '({ws}=={ws}1.0{ws})'), (None, '=={ws}1.0-alpha'), (None, '<={ws}1!3.0.0.rc2'), (None, '>{ws}2.2{ws},{ws}<{ws}3'), (None, '(>{ws}2.2{ws},{ws}<{ws}3)')])
@pytest.mark.parametrize('marker', [None, "python_version{ws}>={ws}'3.3'", '({ws}python_version{ws}>={ws}"3.4"{ws}){ws}and extra{ws}=={ws}"oursql"', "sys_platform{ws}!={ws}'linux' and(os_name{ws}=={ws}'linux' or python_version{ws}>={ws}'3.3'{ws}){ws}"])
@pytest.mark.parametrize('whitespace', ['', ' ', '\t'])
def test_basic_valid_requirement_parsing(name: str, extras: set[str], specifier: str, url: str | None, marker: str, whitespace: str) -> None:
    parts = [name]
    if extras:
        parts.append('[')
        parts.append('{ws},{ws}'.format(ws=whitespace).join(sorted(extras)))
        parts.append(']')
    if specifier:
        parts.append(specifier.format(ws=whitespace))
    if url is not None:
        parts.append('@')
        parts.append(url.format(ws=whitespace))
    if marker is not None:
        if url is not None:
            parts.append(' ;')
        else:
            parts.append(';')
        parts.append(marker.format(ws=whitespace))
    to_parse = whitespace.join(parts)
    req = Requirement(to_parse)
    assert req.name == name
    assert req.extras == extras
    assert req.url == url
    assert req.specifier == specifier.format(ws='').strip('()')
    assert req.marker == (Marker(marker.format(ws='')) if marker else None)

@pytest.mark.parametrize(('input_req', 'norm_req'), [('graphdb>=2.4.1; extra == "graph_connector"', 'graphdb>=2.4.1; extra == "graph-connector"'), ('graphdb>=2.4.1; python_version >= "3" and extra == "graph_connector"', 'graphdb>=2.4.1; python_version >= "3" and extra == "graph-connector"')])
def test_normalized_requirements(input_req: str, norm_req: str) -> None:
    req = Requirement(input_req)
    assert str(req) == norm_req

class TestRequirementParsing:

    @pytest.mark.parametrize('marker', ["python_implementation == ''", "platform_python_implementation == ''", "os.name == 'linux'", "os_name == 'linux'", "'8' in platform.version", "'8' not in platform.version"])
    def test_valid_marker(self, marker: str) -> None:
        to_parse = f'name; {marker}'
        req = Requirement(to_parse)
        assert req.name == 'name'
        assert req.marker is not None

    @pytest.mark.parametrize('url', ['file:///absolute/path', 'file://.', 'file:.', 'file:/.'])
    def test_file_url(self, url: str) -> None:
        to_parse = f'name @ {url}'
        req = Requirement(to_parse)
        assert req.url == url

    def test_empty_extras(self) -> None:
        to_parse = 'name[]'
        req = Requirement(to_parse)
        assert req.name == 'name'
        assert req.extras == set()

    def test_empty_specifier(self) -> None:
        to_parse = 'name()'
        req = Requirement(to_parse)
        assert req.name == 'name'
        assert req.specifier == ''

class TestRequirementBehaviour:

    def test_types_with_nothing(self) -> None:
        to_parse = 'foobar'
        req = Requirement(to_parse)
        assert isinstance(req.name, str)
        assert isinstance(req.extras, set)
        assert req.url is None
        assert isinstance(req.specifier, SpecifierSet)
        assert req.marker is None

    def test_types_with_specifier_and_marker(self) -> None:
        to_parse = "foobar[quux]<2,>=3; os_name=='a'"
        req = Requirement(to_parse)
        assert isinstance(req.name, str)
        assert isinstance(req.extras, set)
        assert req.url is None
        assert isinstance(req.specifier, SpecifierSet)
        assert isinstance(req.marker, Marker)

    def test_types_with_url(self) -> None:
        req = Requirement('foobar @ http://foo.com')
        assert isinstance(req.name, str)
        assert isinstance(req.extras, set)
        assert isinstance(req.url, str)
        assert isinstance(req.specifier, SpecifierSet)
        assert req.marker is None

    @pytest.mark.parametrize(('dep1', 'dep2'), EQUAL_DEPENDENCIES)
    def test_equal_reqs_equal_hashes(self, dep1: str, dep2: str) -> None:
        """Requirement objects created from equal strings should be equal."""
        req1, req2 = (Requirement(dep1), Requirement(dep2))
        assert req1 == req2
        assert hash(req1) == hash(req2)

    @pytest.mark.parametrize(('dep1', 'dep2'), EQUIVALENT_DEPENDENCIES)
    def test_equivalent_reqs_equal_hashes_unequal_strings(self, dep1: str, dep2: str) -> None:
        """Requirement objects created from equivalent strings should be equal,
        even though their string representation will not."""
        req1, req2 = (Requirement(dep1), Requirement(dep2))
        assert req1 == req2
        assert hash(req1) == hash(req2)
        assert str(req1) != str(req2)

    @pytest.mark.parametrize(('dep1', 'dep2'), DIFFERENT_DEPENDENCIES)
    def test_different_reqs_different_hashes(self, dep1: str, dep2: str) -> None:
        """Requirement objects created from non-equivalent strings should differ."""
        req1, req2 = (Requirement(dep1), Requirement(dep2))
        assert req1 != req2
        assert hash(req1) != hash(req2)

    def test_compare_with_string(self) -> None:
        assert Requirement('widgetlib>=4.5') != 'widgetlib>=4.5'

@pytest.mark.parametrize('req_str', ['widgetlib', 'widgetlib>=3.2', 'widgetlib>=3.2,<4.0', 'widgetlib>=3.2; python_version >= "3.8"', 'widgetlib[security,socks]>=3.2', 'my-pkg @ https://example.com', 'WebFrame>=2.1.0,!=2.2.0,!=2.2.1; python_version < "3"'])
def test_pickle_requirement_roundtrip(req_str: str) -> None:
    r = Requirement(req_str)
    loaded = pickle.loads(pickle.dumps(r))
    assert loaded == r
    assert str(loaded) == str(r)

import pytest
from packaging.tags import Tag
from packaging.utils import InvalidName, InvalidSdistFilename, InvalidWheelFilename, canonicalize_name, canonicalize_version, is_normalized_name, parse_sdist_filename, parse_wheel_filename
from packaging.version import Version

@pytest.mark.parametrize(('name', 'expected'), [('foo', 'foo'), ('Foo', 'foo'), ('fOo', 'foo'), ('foo.bar', 'foo-bar'), ('Foo.Bar', 'foo-bar'), ('Foo.....Bar', 'foo-bar'), ('foo_bar', 'foo-bar'), ('foo___bar', 'foo-bar'), ('foo-bar', 'foo-bar'), ('foo----bar', 'foo-bar')])
def test_canonicalize_name(name: str, expected: str) -> None:
    assert canonicalize_name(name) == expected

@pytest.mark.parametrize(('name', 'expected'), [('_not_legal', '-not-legal'), ('hi\n', 'hi\n'), ('\nhi', '\nhi'), ('h\ni', 'h\ni'), ('hi\r', 'hi\r'), ('\rhi', '\rhi'), ('h\ri', 'h\ri')])
def test_canonicalize_name_invalid(name: str, expected: str) -> None:
    with pytest.raises(InvalidName):
        canonicalize_name(name, validate=True)
    assert canonicalize_name(name) == expected

@pytest.mark.parametrize(('name', 'expected'), [('foo', 'foo'), ('Foo', 'foo'), ('fOo', 'foo'), ('foo.bar', 'foo-bar'), ('Foo.Bar', 'foo-bar'), ('Foo.....Bar', 'foo-bar'), ('foo_bar', 'foo-bar'), ('foo___bar', 'foo-bar'), ('foo-bar', 'foo-bar'), ('foo----bar', 'foo-bar'), ('a--b', 'a-b'), ('1--1', '1-1')])
def test_is_normalized_name(name: str, expected: str) -> None:
    assert is_normalized_name(expected)
    if name != expected:
        assert not is_normalized_name(name)

@pytest.mark.parametrize(('version', 'expected'), [(Version('1.4.0'), '1.4'), ('1.4.0', '1.4'), ('1.40.0', '1.40'), ('1.4.0.0.00.000.0000', '1.4'), ('1.0', '1'), ('1.0+abc', '1+abc'), ('1.0.dev0', '1.dev0'), ('1.0.post0', '1.post0'), ('1.0a0', '1a0'), ('1.0rc0', '1rc0'), ('100!0.0', '100!0'), ('lolwat', 'lolwat'), ('1.0.1-test7', '1.0.1-test7')])
def test_canonicalize_version(version: str, expected: str) -> None:
    assert canonicalize_version(version) == expected

@pytest.mark.parametrize('version', ['1.4.0', '1.0'])
def test_canonicalize_version_no_strip_trailing_zero(version: str) -> None:
    assert canonicalize_version(version, strip_trailing_zero=False) == version

@pytest.mark.parametrize(('filename', 'name', 'version', 'build', 'tags'), [('foo-1.0-py3-none-any.whl', 'foo', Version('1.0'), (), {Tag('py3', 'none', 'any')}), ('some_PACKAGE-1.0-py3-none-any.whl', 'some-package', Version('1.0'), (), {Tag('py3', 'none', 'any')}), ('foo-1.0-1000-py3-none-any.whl', 'foo', Version('1.0'), (1000, ''), {Tag('py3', 'none', 'any')}), ('foo-1.0-1000abc-py3-none-any.whl', 'foo', Version('1.0'), (1000, 'abc'), {Tag('py3', 'none', 'any')}), ('pyvirtualcam-0.13.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.whl', 'pyvirtualcam', Version('0.13.0'), (), {Tag('cp310', 'cp310', 'manylinux2014_x86_64'), Tag('cp310', 'cp310', 'manylinux_2_17_x86_64')}), ('foo_bár-1.0-py3-none-any.whl', 'foo-bár', Version('1.0'), (), {Tag('py3', 'none', 'any')}), ('foo_bár-1.0-1000-py3-none-any.whl', 'foo-bár', Version('1.0'), (1000, ''), {Tag('py3', 'none', 'any')})])
def test_parse_wheel_filename(filename: str, name: str, version: Version, build: tuple[int, str], tags: set[Tag]) -> None:
    assert parse_wheel_filename(filename) == (name, version, build, frozenset(tags))

@pytest.mark.parametrize('filename', ['foo-1.0.whl', 'foo-1.0-py3-none-any.wheel', 'foo__bar-1.0-py3-none-any.whl', 'foo#bar-1.0-py3-none-any.whl', 'foobar-1.x-py3-none-any.whl', 'foo-1.0-abc-py3-none-any.whl', 'foo-1.0-200-py3-none-any-junk.whl', 'foo-1.0--none-any.whl', 'foo-1.0-py3-none-.whl', 'foo-1.0-py3.-none-any.whl'])
def test_parse_wheel_invalid_filename(filename: str) -> None:
    with pytest.raises(InvalidWheelFilename):
        parse_wheel_filename(filename)

@pytest.mark.parametrize(('filename', 'name'), [('pyvirtualcam-0.13.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl', 'pyvirtualcam'), ('foo-1.0-py3.py2-none-any.whl', 'foo')])
def test_parse_wheel_unsorted_tags_valid_by_default(filename: str, name: str) -> None:
    parsed_name, _version, _build, tags = parse_wheel_filename(filename)
    assert parsed_name == name
    assert len(tags) > 0

@pytest.mark.parametrize('filename', ['pyvirtualcam-0.13.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl', 'foo-1.0-py3.py2-none-any.whl'])
def test_parse_wheel_unsorted_tags_invalid_with_validate(filename: str) -> None:
    with pytest.raises(InvalidWheelFilename):
        parse_wheel_filename(filename, validate_order=True)

@pytest.mark.parametrize(('filename', 'name', 'version'), [('foo-1.0.tar.gz', 'foo', Version('1.0')), ('foo-1.0.zip', 'foo', Version('1.0'))])
def test_parse_sdist_filename(filename: str, name: str, version: Version) -> None:
    assert parse_sdist_filename(filename) == (name, version)

@pytest.mark.parametrize('filename', ['foo-1.0.xz', 'foo1.0.tar.gz', 'foo-1.x.tar.gz'])
def test_parse_sdist_invalid_filename(filename: str) -> None:
    with pytest.raises(InvalidSdistFilename):
        parse_sdist_filename(filename)
import json
import pytest

def test_version_normalizes_and_exposes_public_segments():
    from packaging.version import Version, parse
    version = Version('1!2.3rc1.post2.dev3+ABC')
    assert parse('v1.0-rc1') == Version('1.0rc1')
    assert str(version) == '1!2.3rc1.post2.dev3+abc'
    assert version.epoch == 1
    assert version.release == (2, 3)
    assert version.pre == ('rc', 1)
    assert version.post == 2
    assert version.dev == 3
    assert version.local == 'abc'

def test_version_ordering_covers_development_prerelease_final_and_postrelease():
    from packaging.version import Version
    values = map(Version, ['1.0.post1', '1.0', '1.0rc1', '1.0.dev1'])
    assert list(sorted(values)) == [Version('1.0.dev1'), Version('1.0rc1'), Version('1.0'), Version('1.0.post1')]

def test_version_convenience_properties_fill_missing_release_components():
    from packaging.version import Version, normalize_pre
    version = Version('7')
    assert (version.major, version.minor, version.micro) == (7, 0, 0)
    assert version.public == '7'
    assert version.base_version == '7'
    assert not version.is_prerelease
    assert normalize_pre('preview') == 'rc'

def test_specifier_set_membership_and_filter_preserve_input_values():
    from packaging.specifiers import SpecifierSet
    specifiers = SpecifierSet('>=1,<2')
    assert '1.5' in specifiers
    assert '2.0' not in specifiers
    assert list(specifiers.filter(['0.9', '1.0', '1.5', '2.0'])) == ['1.0', '1.5']

def test_compatible_specifier_and_prerelease_policy_are_observable():
    from packaging.specifiers import Specifier
    compatible = Specifier('~=1.4')
    prerelease = Specifier('>=1', prereleases=True)
    assert compatible.contains('1.9')
    assert not compatible.contains('2.0')
    assert prerelease.contains('2.0rc1')

def test_specifier_set_combination_and_iteration_keep_both_constraints():
    from packaging.specifiers import SpecifierSet
    combined = SpecifierSet('>=1') & '<2'
    assert {str(item) for item in combined} == {'>=1', '<2'}
    assert combined.contains('1.8')
    assert not combined.contains('2.0')

def test_specifier_set_reports_unsatisfiable_constraints():
    from packaging.specifiers import SpecifierSet
    assert SpecifierSet('>=2,<1').is_unsatisfiable()
    assert not SpecifierSet('>=1,<2').is_unsatisfiable()

def test_version_range_membership_and_intersection():
    from packaging.specifiers import SpecifierSet
    left = SpecifierSet('>=1,<2').to_range()
    right = SpecifierSet('>=1.5,<3').to_range()
    overlap = left & right
    assert left.contains('1.2')
    assert not left.contains('2.0')
    assert not overlap.contains('1.4')
    assert overlap.contains('1.5')

def test_version_range_union_difference_and_complement():
    from packaging.specifiers import SpecifierSet
    left = SpecifierSet('>=1,<2').to_range()
    right = SpecifierSet('>=1.5,<3').to_range()
    assert (left | right).contains('2.5')
    assert (left - right).contains('1.4')
    assert not (left - right).contains('1.5')
    assert (~left).contains('2.0')
    assert not (~left).contains('1.2')

def test_version_range_set_relations_compare_accepted_versions():
    from packaging.specifiers import SpecifierSet
    narrow = SpecifierSet('>=1,<2').to_range()
    wide = SpecifierSet('>=1,<3').to_range()
    separate = SpecifierSet('>=4').to_range()
    assert narrow.is_subset(wide)
    assert wide.is_superset(narrow)
    assert narrow.is_disjoint(separate)
    assert SpecifierSet('>=2,<1').to_range().is_empty

def test_marker_extra_evaluation_normalizes_requested_extra():
    from packaging.markers import Marker
    marker = Marker("extra == 'PDF-Export'")
    assert marker.evaluate({'extra': 'pdf_export'})
    assert not marker.evaluate({'extra': 'docs'})

def test_marker_missing_environment_name_raises_public_error():
    from packaging.markers import InvalidMarker, Marker
    with pytest.raises(InvalidMarker):
        Marker("unknown_name == 'x'")

def test_marker_boolean_composition_uses_supplied_environment():
    from packaging.markers import Marker
    marker = Marker("python_version >= '3.10'") & Marker("os_name == 'posix'")
    assert marker.evaluate({'python_version': '3.11', 'os_name': 'posix'})
    assert not marker.evaluate({'python_version': '3.9', 'os_name': 'posix'})

def test_marker_default_environment_supplies_standard_keys():
    from packaging.markers import Marker, default_environment
    environment = default_environment()
    assert {'python_version', 'os_name', 'sys_platform'} <= environment.keys()
    assert Marker("python_version == '" + environment['python_version'] + "'").evaluate(environment)

def test_tag_object_and_parse_tag_round_trip_public_values():
    from packaging.tags import Tag, parse_tag
    parsed = parse_tag('cp311-cp311-win_amd64')
    expected = Tag('cp311', 'cp311', 'win_amd64')
    assert expected in parsed
    assert str(expected) == 'cp311-cp311-win_amd64'
    assert expected == Tag('cp311', 'cp311', 'win_amd64')

def test_parse_tag_expands_compressed_public_components():
    from packaging.tags import Tag, parse_tag
    parsed = parse_tag('py2.py3-none-any')
    assert parsed == frozenset({Tag('py2', 'none', 'any'), Tag('py3', 'none', 'any')})

def test_sys_tags_yields_ordered_public_tag_objects():
    from packaging.tags import Tag, sys_tags
    supported = list(sys_tags())
    assert supported
    assert isinstance(supported[0], Tag)
    assert len(supported) == len(set(supported))

def test_metadata_parse_email_reports_unparsed_fields_as_errors():
    from packaging.metadata import parse_email
    raw, unparsed = parse_email('Metadata-Version: 2.1\nName: demo\nVersion: 1.0\nRequires-Dist: demo>=1\n')
    assert raw['name'] == 'demo'
    assert raw['version'] == '1.0'
    assert raw['requires_dist'] == ['demo>=1']
    assert unparsed == {}

def test_metadata_from_raw_validates_required_core_fields():
    from packaging.errors import ExceptionGroup
    from packaging.metadata import Metadata
    with pytest.raises(ExceptionGroup):
        Metadata.from_raw({'name': 'demo'})

def test_metadata_from_email_exposes_typed_public_fields():
    from packaging.metadata import Metadata
    from packaging.version import Version
    metadata = Metadata.from_email('Metadata-Version: 2.1\nName: Demo_Pkg\nVersion: 1.2\nSummary: Example\n')
    assert metadata.name == 'Demo_Pkg'
    assert metadata.version == Version('1.2')
    assert metadata.summary == 'Example'

def test_direct_url_rejects_missing_info_section():
    from packaging.direct_url import DirectUrl, DirectUrlValidationError
    with pytest.raises(DirectUrlValidationError):
        DirectUrl.from_dict({'url': 'https://example.com/pkg.tar.gz'})

def test_direct_url_directory_record_round_trips_public_fields():
    from packaging.direct_url import DirInfo, DirectUrl
    direct = DirectUrl(url='file:///tmp/demo', dir_info=DirInfo(editable=True))
    data = direct.to_dict()
    assert data == {'url': 'file:///tmp/demo', 'dir_info': {'editable': True}}
    assert DirectUrl.from_dict(data) == direct

def test_direct_url_vcs_record_round_trips_revision_fields():
    from packaging.direct_url import DirectUrl, VcsInfo
    direct = DirectUrl(url='https://example.com/demo.git', vcs_info=VcsInfo(vcs='git', commit_id='abc123', requested_revision='main'))
    assert DirectUrl.from_dict(direct.to_dict()) == direct
    assert direct.to_dict()['vcs_info']['requested_revision'] == 'main'

def test_license_expression_canonicalizes_spdx_operators():
    from packaging.licenses import canonicalize_license_expression
    assert canonicalize_license_expression('mit or apache-2.0') == 'MIT OR Apache-2.0'

def test_invalid_license_expression_raises_public_error():
    from packaging.licenses import InvalidLicenseExpression, canonicalize_license_expression
    with pytest.raises(InvalidLicenseExpression):
        canonicalize_license_expression('MIT AND')

def test_license_expression_preserves_grouping_and_license_refs():
    from packaging.licenses import canonicalize_license_expression
    assert canonicalize_license_expression('(mit and apache-2.0) or LicenseRef-Custom') == '(MIT AND Apache-2.0) OR LicenseRef-Custom'

def test_license_expression_canonicalizes_with_exception_clause():
    from packaging.licenses import canonicalize_license_expression
    assert canonicalize_license_expression('gpl-2.0-only with classpath-exception-2.0') == 'GPL-2.0-only WITH Classpath-exception-2.0'

def test_error_helper_exception_group_collects_public_errors():
    from packaging.errors import ExceptionGroup
    from packaging.version import InvalidVersion
    group = ExceptionGroup('many', [InvalidVersion('bad')])
    assert isinstance(group.exceptions[0], InvalidVersion)
    assert 'many' in str(group)

def test_error_helper_preserves_message_and_exception_order():
    from packaging.errors import ExceptionGroup
    group = ExceptionGroup('validation', [ValueError('first'), TypeError('second')])
    assert group.message == 'validation'
    assert [type(error) for error in group.exceptions] == [ValueError, TypeError]

def test_error_helper_accepts_multiple_public_packaging_errors():
    from packaging.errors import ExceptionGroup
    from packaging.requirements import InvalidRequirement
    from packaging.version import InvalidVersion
    group = ExceptionGroup('invalid inputs', [InvalidVersion('bad'), InvalidRequirement('also bad')])
    assert isinstance(group.exceptions[0], InvalidVersion)
    assert isinstance(group.exceptions[1], InvalidRequirement)
    assert 'bad' in str(group.exceptions[0]).lower()
    assert 'also bad' in str(group.exceptions[1]).lower()
