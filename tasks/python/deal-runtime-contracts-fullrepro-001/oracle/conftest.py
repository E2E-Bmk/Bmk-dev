"""Shared fixtures, helpers, and constants for deal oracle tests."""
import pytest
import deal
import deal.introspection as introspection


@pytest.fixture(autouse=True)
def _restore_deal_state():
    """Reset deal state before and after every test."""
    deal.reset()
    yield
    deal.reset()
