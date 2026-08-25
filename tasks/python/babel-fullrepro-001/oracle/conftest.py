import pytest

import babel.messages.catalog as catalog_module


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic tests this integration or system test logically depends on",
    )


@pytest.fixture(autouse=True)
def stable_catalog_datetime(monkeypatch):
    monkeypatch.setattr(
        catalog_module,
        "format_datetime",
        lambda value, fmt, locale=None: "2000-01-01 00:00+0000",
        raising=False,
    )
