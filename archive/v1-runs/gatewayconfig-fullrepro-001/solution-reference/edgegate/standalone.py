from __future__ import annotations


def load_standalone(gateway, document: dict, now=None) -> dict:
    return gateway.load_standalone(document, now=now)


def export_standalone(gateway) -> dict:
    return gateway.export_standalone()
