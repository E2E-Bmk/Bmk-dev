"""Shared helpers for WTForms oracle tests."""


class FormData(dict):
    """Small public getlist-compatible submitted-data adapter."""

    def getlist(self, name):
        value = self.get(name, [])
        return value if isinstance(value, list) else [value]
