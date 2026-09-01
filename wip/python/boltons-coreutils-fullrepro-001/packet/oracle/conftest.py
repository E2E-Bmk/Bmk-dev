"""Shared fixtures, helpers, and constants for the boltons oracle test suite."""
import pytest


# URL constants using .test TLD per oracle standard
BASE_URL = "https://portal.example.test:8443/api/v2?token=abc123#section"
SIMPLE_URL = "http://data.example.test/items"
UNICODE_URL = "https://café.example.test/über/path?name=日本語"
RELATIVE_DEST = "../sibling/resource?page=7"
MAILTO_URL = "mailto:user@mail.example.test"
FTP_URL = "ftp://files.example.test:2121/pub/archive.tar.gz"
BARE_DOMAIN_TEXT = "Visit shop.example.test/deals for offers."
MULTI_LINK_TEXT = "See https://alpha.example.test and http://beta.example.test/info for details."


# Shared helper: callable for on_miss
def miss_handler(key):
    """Return a transformed value for missing cache keys."""
    return f"generated_{key}"


# Shared helper: simple class for cachedmethod/cachedproperty tests
class Computation:
    def __init__(self):
        self._call_count = 0
        self._cache_store = {}

    def compute(self, x):
        self._call_count += 1
        return x * x + 7

    @property
    def call_count(self):
        return self._call_count


# Shared helper: nested data for remap/get_path/research tests
NESTED_DATA = {
    "level1": {
        "level2": [10, 20, {"level3_key": "deep_value"}],
        "other": "flat",
    },
    "top_item": 99,
}

# Shared helper: items for OrderedMultiDict tests
OMD_PAIRS = [("color", "red"), ("size", "large"), ("color", "blue"), ("weight", "heavy"), ("color", "green")]

# Shared helper: items for ManyToMany tests
M2M_PAIRS = [("proj_a", "dev1"), ("proj_a", "dev2"), ("proj_b", "dev2"), ("proj_b", "dev3")]


@pytest.fixture
def lri_cache():
    """Create a fresh LRI cache with capacity 4."""
    from boltons.cacheutils import LRI
    return LRI(max_size=4)


@pytest.fixture
def lru_cache():
    """Create a fresh LRU cache with capacity 4."""
    from boltons.cacheutils import LRU
    return LRU(max_size=4)


@pytest.fixture
def omd_instance():
    """Create a fresh OrderedMultiDict from OMD_PAIRS."""
    from boltons.dictutils import OrderedMultiDict
    return OrderedMultiDict(OMD_PAIRS)


@pytest.fixture
def url_instance():
    """Create a fresh URL from BASE_URL."""
    from boltons.urlutils import URL
    return URL(BASE_URL)


@pytest.fixture
def threshold_counter():
    """Create a ThresholdCounter with threshold=0.2."""
    from boltons.cacheutils import ThresholdCounter
    return ThresholdCounter(threshold=0.2)
