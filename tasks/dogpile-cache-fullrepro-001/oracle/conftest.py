# Spec2Repo oracle - shared fixtures for dogpile-cache-fullrepro-001

import itertools
import threading

import pytest

from dogpile.cache.api import CacheBackend


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): atomic dependencies")


@pytest.fixture
def fresh_region():
    from dogpile.cache import make_region

    def factory(**kwargs):
        cache_dict = kwargs.pop("cache_dict", {})
        return make_region(**kwargs).configure(
            "dogpile.cache.memory", arguments={"cache_dict": cache_dict}
        )

    return factory


@pytest.fixture
def counting_values():
    return itertools.count(1)


class RecordingBackend:
    """Mixin for small public CacheBackend test doubles."""

    stores = {}
    calls = {}

    @classmethod
    def reset(cls):
        cls.stores = {}
        cls.calls = {}

    @classmethod
    def store_for(cls, name):
        return cls.stores.setdefault(name, {})

    @classmethod
    def calls_for(cls, name):
        return cls.calls.setdefault(name, [])


class PublicDictBackend(RecordingBackend, CacheBackend):
    key_mangler = None

    def __init__(self, arguments):
        self.name = arguments.get("name", "default")
        self.arguments = dict(arguments)
        self.cache = self.store_for(self.name)
        self.log = self.calls_for(self.name)

    @classmethod
    def from_config_dict(cls, config_dict, prefix):
        prefix_len = len(prefix)
        return cls(
            {
                key[prefix_len:]: config_dict[key]
                for key in config_dict
                if key.startswith(prefix)
            }
        )

    def get(self, key):
        from dogpile.cache.api import NO_VALUE

        self.log.append(("get", key))
        return self.cache.get(key, NO_VALUE)

    def get_multi(self, keys):
        from dogpile.cache.api import NO_VALUE

        key_list = list(keys)
        self.log.append(("get_multi", tuple(key_list)))
        return [self.cache.get(key, NO_VALUE) for key in key_list]

    def set(self, key, value):
        self.log.append(("set", key))
        self.cache[key] = value

    def set_multi(self, mapping):
        self.log.append(("set_multi", tuple(sorted(mapping))))
        self.cache.update(mapping)

    def delete(self, key):
        self.log.append(("delete", key))
        self.cache.pop(key, None)

    def delete_multi(self, keys):
        key_list = list(keys)
        self.log.append(("delete_multi", tuple(key_list)))
        for key in key_list:
            self.cache.pop(key, None)


class ManglingBackend(PublicDictBackend):
    @staticmethod
    def key_mangler(key):
        return "backend:" + str(key)


class SimpleMutex:
    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self, wait=True):
        return self._lock.acquire(wait)

    def release(self):
        self._lock.release()

    def locked(self):
        return self._lock.locked()


class MutexBackend(PublicDictBackend):
    mutexes = {}

    def get_mutex(self, key):
        return self.mutexes.setdefault(key, SimpleMutex())


class UppercaseSetProxy:
    def __init__(self):
        from dogpile.cache.proxy import ProxyBackend

        self._base = ProxyBackend()

    def __getattr__(self, name):
        return getattr(self._base, name)


@pytest.fixture(scope="session", autouse=True)
def register_public_backends():
    from dogpile.cache import register_backend

    PublicDictBackend.reset()
    ManglingBackend.reset()
    MutexBackend.reset()
    register_backend("spec.public_dict", "conftest", "PublicDictBackend")
    register_backend("spec.mangling_dict", "conftest", "ManglingBackend")
    register_backend("spec.mutex_dict", "conftest", "MutexBackend")


@pytest.fixture(autouse=True)
def reset_backend_state():
    PublicDictBackend.reset()
    ManglingBackend.reset()
    MutexBackend.reset()
    yield
