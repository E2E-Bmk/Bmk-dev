from __future__ import annotations

from .models import EdgeGateError, clone


def merge_patch(base: dict, patch: dict) -> dict:
    if not isinstance(base, dict) or not isinstance(patch, dict):
        raise EdgeGateError("invalid_patch", "merge patch requires objects")
    result = clone(base)
    for key, value in patch.items():
        if key in {"id", "version", "digest"}:
            raise EdgeGateError("invalid_patch", f"{key} is immutable")
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_patch(result[key], value)
        else:
            result[key] = clone(value)
    return result
