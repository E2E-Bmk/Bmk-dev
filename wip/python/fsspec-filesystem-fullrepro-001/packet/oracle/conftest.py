"""Shared fixtures and cleanup for fsspec oracle tests."""

import pytest

import fsspec

_MEMORY_CLEANUP_PATHS = [
    "/alpha", "/shared", "/bucket", "/plain", "/notes",
    "/a", "/b", "/slice.bin", "/tmp", "/tree",
    "/root//a", "/root", "/source.txt", "/copy.txt", "/moved.txt",
    "/remote", "/dataset", "/store", "/multi", "/ops",
    "/convert", "/inner", "/txn", "/remove", "/agree",
    "/exact", "/depth",
]


def _clean_memory_public_paths():
    fs = fsspec.filesystem("memory")
    for path in sorted(_MEMORY_CLEANUP_PATHS, key=len, reverse=True):
        try:
            if fs.exists(path):
                fs.rm(path, recursive=True)
        except FileNotFoundError:
            pass


@pytest.fixture(autouse=True)
def clean_memory():
    """Reset well-known memory paths before and after each test."""
    _clean_memory_public_paths()
    yield
    _clean_memory_public_paths()
