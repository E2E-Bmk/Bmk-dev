# Spec2Repo oracle - integration tests for vcrpy-fullrepro-001
import json
import pytest


@pytest.fixture(autouse=True)
def _isolate_local_http_from_proxy(monkeypatch):
    for name in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def httpbin_both(httpbin):
    return httpbin

def assert_cassette_empty(cass):
    assert len(cass) == 0
    assert cass.play_count == 0

def assert_is_json_bytes(value):
    assert isinstance(value, bytes)
    json.loads(value)

# Extracted from tests/integration/test_basic.py.

import os

from urllib.request import urlopen

import vcr

def test_nonexistent_directory(tmpdir, httpbin):
    """If we load a cassette in a nonexistent directory, it can save ok"""
    assert not os.path.exists(str(tmpdir.join('nonexistent')))
    with vcr.use_cassette(str(tmpdir.join('nonexistent', 'cassette.yml'))):
        urlopen(httpbin.url).read()
    assert os.path.exists(str(tmpdir.join('nonexistent', 'cassette.yml')))

def test_unpatch(tmpdir, httpbin):
    """Ensure that our cassette gets unpatched when we're done"""
    with vcr.use_cassette(str(tmpdir.join('unpatch.yaml'))) as cass:
        urlopen(httpbin.url).read()
    urlopen(httpbin.url).read()
    assert cass.play_count == 0

def test_basic_json_use(tmpdir, httpbin):
    """
    Ensure you can load a json serialized cassette
    """
    test_fixture = str(tmpdir.join('synopsis.json'))
    with vcr.use_cassette(test_fixture, serializer='json'):
        response = urlopen(httpbin.url).read()
        assert b'HTTP Request &amp; Response Service' in response

# Extracted from tests/integration/test_config.py.

import json

import os

from urllib.request import urlopen

import pytest

import vcr

from vcr.cassette import Cassette

def test_default_set_cassette_library_dir(tmpdir, httpbin):
    my_vcr = vcr.VCR(cassette_library_dir=str(tmpdir.join('subdir')))
    with my_vcr.use_cassette('test.json'):
        urlopen(httpbin.url)
    assert os.path.exists(str(tmpdir.join('subdir').join('test.json')))

def test_override_set_cassette_library_dir(tmpdir, httpbin):
    my_vcr = vcr.VCR(cassette_library_dir=str(tmpdir.join('subdir')))
    cld = str(tmpdir.join('subdir2'))
    with my_vcr.use_cassette('test.json', cassette_library_dir=cld):
        urlopen(httpbin.url)
    assert os.path.exists(str(tmpdir.join('subdir2').join('test.json')))
    assert not os.path.exists(str(tmpdir.join('subdir').join('test.json')))

def test_override_match_on(tmpdir, httpbin):
    my_vcr = vcr.VCR(match_on=['method'])
    with my_vcr.use_cassette(str(tmpdir.join('test.json'))):
        urlopen(httpbin.url)
    with my_vcr.use_cassette(str(tmpdir.join('test.json'))) as cass:
        urlopen(httpbin.url)
    assert len(cass) == 1
    assert cass.play_count == 1

def test_dont_record_on_exception(tmpdir, httpbin):
    my_vcr = vcr.VCR(record_on_exception=False)

    @my_vcr.use_cassette(str(tmpdir.join('dontsave.yml')))
    def some_test():
        assert b'Not in content' in urlopen(httpbin.url)
    with pytest.raises(AssertionError):
        some_test()
    assert not os.path.exists(str(tmpdir.join('dontsave.yml')))
    with pytest.raises(AssertionError), my_vcr.use_cassette(str(tmpdir.join('dontsave2.yml'))):
        assert b'Not in content' in urlopen(httpbin.url).read()
    assert not os.path.exists(str(tmpdir.join('dontsave2.yml')))

def test_set_drop_unused_requests(tmpdir, httpbin):
    my_vcr = vcr.VCR(drop_unused_requests=True)
    file = str(tmpdir.join('test.yaml'))
    with my_vcr.use_cassette(file):
        urlopen(httpbin.url)
        urlopen(httpbin.url + '/get')
    cassette = Cassette.load(path=file)
    assert len(cassette) == 2
    with my_vcr.use_cassette(file):
        urlopen(httpbin.url)
    cassette = Cassette.load(path=file)
    assert len(cassette) == 1

# Extracted from tests/integration/test_ignore.py.

import socket

from contextlib import contextmanager

from urllib.request import urlopen

import vcr

@contextmanager
def overridden_dns(overrides):
    """
    Monkeypatch socket.getaddrinfo() to override DNS lookups (name will resolve
    to address)
    """
    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(*args, **kwargs):
        if args[0] in overrides:
            address = overrides[args[0]]
            return [(2, 1, 6, '', (address, args[1]))]
        return real_getaddrinfo(*args, **kwargs)
    socket.getaddrinfo = fake_getaddrinfo
    yield
    socket.getaddrinfo = real_getaddrinfo

def test_ignore_localhost(tmpdir, httpbin):
    with overridden_dns({'httpbin.org': '127.0.0.1'}):
        cass_file = str(tmpdir.join('filter_qs.yaml'))
        with vcr.use_cassette(cass_file, ignore_localhost=True) as cass:
            urlopen(f'http://localhost:{httpbin.port}/')
            assert len(cass) == 0
            urlopen(f'http://httpbin.org:{httpbin.port}/')
            assert len(cass) == 1

def test_ignore_httpbin(tmpdir, httpbin):
    with overridden_dns({'httpbin.org': '127.0.0.1'}):
        cass_file = str(tmpdir.join('filter_qs.yaml'))
        with vcr.use_cassette(cass_file, ignore_hosts=['httpbin.org']) as cass:
            urlopen(f'http://httpbin.org:{httpbin.port}/')
            assert len(cass) == 0
            urlopen(f'http://localhost:{httpbin.port}/')
            assert len(cass) == 1

def test_ignore_localhost_and_httpbin(tmpdir, httpbin):
    with overridden_dns({'httpbin.org': '127.0.0.1'}):
        cass_file = str(tmpdir.join('filter_qs.yaml'))
        with vcr.use_cassette(cass_file, ignore_hosts=['httpbin.org'], ignore_localhost=True) as cass:
            urlopen(f'http://httpbin.org:{httpbin.port}')
            urlopen(f'http://localhost:{httpbin.port}')
            assert len(cass) == 0

def test_ignore_localhost_twice(tmpdir, httpbin):
    with overridden_dns({'httpbin.org': '127.0.0.1'}):
        cass_file = str(tmpdir.join('filter_qs.yaml'))
        with vcr.use_cassette(cass_file, ignore_localhost=True) as cass:
            urlopen(f'http://localhost:{httpbin.port}')
            assert len(cass) == 0
            urlopen(f'http://httpbin.org:{httpbin.port}')
            assert len(cass) == 1
        with vcr.use_cassette(cass_file, ignore_localhost=True) as cass:
            assert len(cass) == 1
            urlopen(f'http://localhost:{httpbin.port}')
            urlopen(f'http://httpbin.org:{httpbin.port}')
            assert len(cass) == 1

# Extracted from tests/integration/test_record_mode.py.

from urllib.request import urlopen

import pytest

import vcr

from vcr.errors import CannotOverwriteExistingCassetteException

def test_once_record_mode(tmpdir, httpbin):
    testfile = str(tmpdir.join('recordmode.yml'))
    with vcr.use_cassette(testfile, record_mode=vcr.mode.ONCE):
        urlopen(httpbin.url).read()
    with vcr.use_cassette(testfile, record_mode=vcr.mode.ONCE):
        urlopen(httpbin.url).read()
        with pytest.raises(CannotOverwriteExistingCassetteException):
            urlopen(httpbin.url + '/get').read()

def test_none_record_mode(tmpdir, httpbin):
    testfile = str(tmpdir.join('recordmode.yml'))
    with vcr.use_cassette(testfile, record_mode=vcr.mode.NONE), pytest.raises(CannotOverwriteExistingCassetteException):
        urlopen(httpbin.url).read()

def test_none_record_mode_with_existing_cassette(tmpdir, httpbin):
    testfile = str(tmpdir.join('recordmode.yml'))
    with vcr.use_cassette(testfile, record_mode=vcr.mode.ALL):
        urlopen(httpbin.url).read()
    with vcr.use_cassette(testfile, record_mode=vcr.mode.NONE) as cass:
        urlopen(httpbin.url).read()
        assert cass.play_count == 1
        with pytest.raises(CannotOverwriteExistingCassetteException):
            urlopen(httpbin.url + '/get').read()

# Extracted from tests/integration/test_register_matcher.py.

from urllib.request import urlopen

import pytest

import vcr

def true_matcher(r1, r2):
    return True

def false_matcher(r1, r2):
    return False

def test_registered_true_matcher(tmpdir, httpbin):
    my_vcr = vcr.VCR()
    my_vcr.register_matcher('true', true_matcher)
    testfile = str(tmpdir.join('test.yml'))
    with my_vcr.use_cassette(testfile, match_on=['true']):
        urlopen(httpbin.url)
        urlopen(httpbin.url + '/get')
    with my_vcr.use_cassette(testfile, match_on=['true']):
        urlopen(httpbin.url)
        urlopen(httpbin.url)

def test_registered_false_matcher(tmpdir, httpbin):
    my_vcr = vcr.VCR()
    my_vcr.register_matcher('false', false_matcher)
    testfile = str(tmpdir.join('test.yml'))
    with my_vcr.use_cassette(testfile, match_on=['false']) as cass:
        urlopen(httpbin.url)
        urlopen(httpbin.url + '/get')
        assert len(cass) == 2

# Extracted from tests/integration/test_register_persister.py.

import os

from urllib.request import urlopen

import pytest

import vcr

from vcr.persisters.filesystem import CassetteDecodeError, CassetteNotFoundError, FilesystemPersister

class CustomFilesystemPersister:
    """Behaves just like default FilesystemPersister but adds .test extension
    to the cassette file"""

    @staticmethod
    def load_cassette(cassette_path, serializer):
        cassette_path += '.test'
        return FilesystemPersister.load_cassette(cassette_path, serializer)

    @staticmethod
    def save_cassette(cassette_path, cassette_dict, serializer):
        cassette_path += '.test'
        FilesystemPersister.save_cassette(cassette_path, cassette_dict, serializer)

class BadPersister(FilesystemPersister):
    """A bad persister that raises different errors."""

    @staticmethod
    def load_cassette(cassette_path, serializer):
        if 'nonexistent' in cassette_path:
            raise CassetteNotFoundError()
        elif 'encoding' in cassette_path:
            raise CassetteDecodeError()
        else:
            raise ValueError('buggy persister')

def test_load_cassette_persister_exception_handling(tmpdir, httpbin):
    """
    Ensure expected errors from persister are swallowed while unexpected ones
    are passed up the call stack.
    """
    my_vcr = vcr.VCR()
    my_vcr.register_persister(BadPersister)
    with my_vcr.use_cassette('bad/nonexistent') as cass:
        assert len(cass) == 0
    with my_vcr.use_cassette('bad/encoding') as cass:
        assert len(cass) == 0
    with pytest.raises(ValueError), my_vcr.use_cassette('bad/buggy') as cass:
        pass

# Extracted from tests/integration/test_register_serializer.py.

import vcr

class MockSerializer:

    def __init__(self):
        self.serialize_count = 0
        self.deserialize_count = 0
        self.load_args = None

    def deserialize(self, cassette_string):
        self.serialize_count += 1
        self.cassette_string = cassette_string
        return {'interactions': []}

    def serialize(self, cassette_dict):
        self.deserialize_count += 1
        return ''

def test_registered_serializer(tmpdir):
    ms = MockSerializer()
    my_vcr = vcr.VCR()
    my_vcr.register_serializer('mock', ms)
    tmpdir.join('test.mock').write('test_data')
    with my_vcr.use_cassette(str(tmpdir.join('test.mock')), serializer='mock'):
        assert ms.serialize_count == 1
        assert ms.cassette_string == 'test_data'
        assert ms.deserialize_count == 0
    assert ms.serialize_count == 1

# Extracted from tests/integration/test_request.py.

from urllib.request import urlopen

import vcr

def test_recorded_request_uri_with_redirected_request(tmpdir, httpbin):
    with vcr.use_cassette(str(tmpdir.join('test.yml'))) as cass:
        assert len(cass) == 0
        urlopen(httpbin.url + '/redirect/3')
        assert cass.requests[0].uri == httpbin.url + '/redirect/3'
        assert cass.requests[3].uri == httpbin.url + '/get'
        assert len(cass) == 4

def test_records_multiple_header_values(tmpdir, httpbin):
    with vcr.use_cassette(str(tmpdir.join('test.yml'))) as cass:
        assert len(cass) == 0
        urlopen(httpbin.url + '/response-headers?foo=bar&foo=baz')
        assert len(cass) == 1
        assert cass.responses[0]['headers']['foo'] == ['bar', 'baz']

# Extracted from tests/integration/test_requests.py.

import pytest

import vcr

requests = pytest.importorskip('requests')

def test_status_code(httpbin_both, tmpdir):
    """Ensure that we can read the status code"""
    url = httpbin_both.url + '/'
    with vcr.use_cassette(str(tmpdir.join('atts.yaml'))):
        status_code = requests.get(url).status_code
    with vcr.use_cassette(str(tmpdir.join('atts.yaml'))):
        assert status_code == requests.get(url).status_code

def test_headers(httpbin_both, tmpdir):
    """Ensure that we can read the headers back"""
    url = httpbin_both + '/'
    with vcr.use_cassette(str(tmpdir.join('headers.yaml'))):
        headers = requests.get(url).headers
    with vcr.use_cassette(str(tmpdir.join('headers.yaml'))):
        assert headers == requests.get(url).headers

def test_body(tmpdir, httpbin_both):
    """Ensure the responses are all identical enough"""
    url = httpbin_both + '/bytes/1024'
    with vcr.use_cassette(str(tmpdir.join('body.yaml'))):
        content = requests.get(url).content
    with vcr.use_cassette(str(tmpdir.join('body.yaml'))):
        assert content == requests.get(url).content

def test_get_empty_content_type_json(tmpdir, httpbin_both):
    """Ensure GET with application/json content-type and empty request body doesn't crash"""
    url = httpbin_both + '/status/200'
    headers = {'Content-Type': 'application/json'}
    with vcr.use_cassette(str(tmpdir.join('get_empty_json.yaml')), match_on=('body',)):
        status = requests.get(url, headers=headers).status_code
    with vcr.use_cassette(str(tmpdir.join('get_empty_json.yaml')), match_on=('body',)):
        assert status == requests.get(url, headers=headers).status_code

def test_post(tmpdir, httpbin_both):
    """Ensure that we can post and cache the results"""
    data = {'key1': 'value1', 'key2': 'value2'}
    url = httpbin_both + '/post'
    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))):
        req1 = requests.post(url, data).content
    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))):
        req2 = requests.post(url, data).content
    assert req1 == req2

def test_redirects(tmpdir, httpbin_both):
    """Ensure that we can handle redirects"""
    url = httpbin_both + '/redirect-to?url=bytes/1024'
    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))):
        content = requests.get(url).content
    with vcr.use_cassette(str(tmpdir.join('requests.yaml'))) as cass:
        assert content == requests.get(url).content
        assert len(cass) == 2
        assert cass.play_count == 2

def test_gzip__decode_compressed_response_false(tmpdir, httpbin_both):
    """
    Ensure that requests (actually urllib3) is able to automatically decompress
    the response body
    """
    for _ in range(2):
        with vcr.use_cassette(str(tmpdir.join('gzip.yaml'))):
            response = requests.get(httpbin_both + '/gzip')
            assert response.headers['content-encoding'] == 'gzip'
            assert_is_json_bytes(response.content)

def test_gzip__decode_compressed_response_true(tmpdir, httpbin_both):
    url = httpbin_both + '/gzip'
    expected_response = requests.get(url)
    expected_content = expected_response.content
    assert expected_response.headers['content-encoding'] == 'gzip'
    with vcr.use_cassette(str(tmpdir.join('decode_compressed.yaml')), decode_compressed_response=True) as cassette:
        r = requests.get(url)
        assert r.headers['content-encoding'] == 'gzip'
        assert r.content == expected_content
    cassette_response_body = cassette.responses[0]['body']['string']
    assert isinstance(cassette_response_body, str)
    with vcr.use_cassette(str(tmpdir.join('decode_compressed.yaml')), decode_compressed_response=True):
        r = requests.get(url)
        assert 'content-encoding' not in r.headers
        assert r.content == expected_content

def test_filter_post_params(tmpdir, httpbin_both):
    """
    This tests the issue in https://github.com/kevin1024/vcrpy/issues/158

    Ensure that a post request made through requests can still be filtered.
    with vcr.use_cassette(cass_file, filter_post_data_parameters=['id']) as cass:
        assert b'id=secret' not in cass.requests[0].body
    """
    url = httpbin_both.url + '/post'
    cass_loc = str(tmpdir.join('filter_post_params.yaml'))
    with vcr.use_cassette(cass_loc, filter_post_data_parameters=['key']) as cass:
        requests.post(url, data={'key': 'value'})
    with vcr.use_cassette(cass_loc, filter_post_data_parameters=['key']) as cass:
        assert b'key=value' not in cass.requests[0].body

# Extracted from tests/unit/test_unittest.py.

import os

from unittest import TextTestRunner, defaultTestLoader

from unittest.mock import MagicMock

from urllib.request import urlopen

import pytest

from vcr.unittest import VCRTestCase

def test_vcr_kwargs_overridden():

    class MyTest(VCRTestCase):

        def test_foo(self):
            pass

        def _get_vcr_kwargs(self):
            kwargs = super()._get_vcr_kwargs()
            kwargs['record_mode'] = 'new_episodes'
            return kwargs
    test = run_testcase(MyTest)[0][0]
    assert test.cassette.record_mode == 'new_episodes'

def test_vcr_kwargs_passed():

    class MyTest(VCRTestCase):

        def test_foo(self):
            pass

        def _get_vcr_kwargs(self):
            return super()._get_vcr_kwargs(record_mode='new_episodes')
    test = run_testcase(MyTest)[0][0]
    assert test.cassette.record_mode == 'new_episodes'

def run_testcase(testcase_class):
    """Run all the tests in a TestCase and return them."""
    suite = defaultTestLoader.loadTestsFromTestCase(testcase_class)
    tests = list(suite)
    result = TextTestRunner().run(suite)
    return (tests, result)


def test_filesystem_persister_round_trips_empty_cassette_data(tmp_path):
    from vcr.persisters.filesystem import FilesystemPersister

    class JsonSerializer:
        @staticmethod
        def serialize(data):
            return json.dumps(data)

        @staticmethod
        def deserialize(data):
            return json.loads(data)

    cassette_path = tmp_path / "nested" / "cassette.json"
    FilesystemPersister.save_cassette(
        str(cassette_path),
        {"requests": [], "responses": []},
        JsonSerializer,
    )
    assert cassette_path.exists()
    assert FilesystemPersister.load_cassette(str(cassette_path), JsonSerializer) == ([], [])


def test_filesystem_persister_reports_missing_and_malformed_data(tmp_path):
    from vcr.persisters.filesystem import CassetteDecodeError, CassetteNotFoundError, FilesystemPersister

    class JsonSerializer:
        @staticmethod
        def deserialize(data):
            return json.loads(data)

    with pytest.raises(CassetteNotFoundError):
        FilesystemPersister.load_cassette(str(tmp_path / "missing.json"), JsonSerializer)
    malformed = tmp_path / "malformed.json"
    malformed.write_bytes(b"\xff")
    with pytest.raises(CassetteDecodeError):
        FilesystemPersister.load_cassette(str(malformed), JsonSerializer)


def test_custom_patch_is_active_only_inside_cassette_context(tmp_path):
    class Target:
        value = "original"

    target = Target()
    recorder = vcr.VCR(custom_patches=((target, "value", "patched"),))
    with recorder.use_cassette(str(tmp_path / "custom-patch.yaml")):
        assert target.value == "patched"
    assert target.value == "original"


def test_default_record_on_exception_saves_recorded_interaction(tmp_path, httpbin):
    cassette_path = tmp_path / "saved-on-error.yaml"
    with pytest.raises(RuntimeError):
        with vcr.use_cassette(str(cassette_path)):
            urlopen(httpbin.url).read()
            raise RuntimeError("boom")
    assert cassette_path.exists()
    assert len(Cassette.load(path=str(cassette_path))) == 1


def test_record_modes_new_episodes_and_all_have_distinct_replay_behavior(tmp_path, httpbin):
    cassette_path = str(tmp_path / "record-modes.yaml")
    with vcr.use_cassette(cassette_path, record_mode=vcr.mode.NEW_EPISODES):
        urlopen(httpbin.url).read()
    with vcr.use_cassette(cassette_path, record_mode=vcr.mode.NEW_EPISODES) as cassette:
        urlopen(httpbin.url).read()
        urlopen(httpbin.url + "/get").read()
        assert cassette.play_count == 1
        assert len(cassette) == 2
    with vcr.use_cassette(cassette_path, record_mode=vcr.mode.ALL) as cassette:
        urlopen(httpbin.url).read()
        assert cassette.play_count == 0
