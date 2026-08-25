"""Shared helpers for WebOb oracle tests."""


def _start_response(status, headers, exc_info=None):
    _start_response.status = status
    _start_response.headers = headers
