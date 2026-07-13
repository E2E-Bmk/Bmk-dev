from __future__ import annotations


def _host_matches(patterns: list[str], host: str) -> bool:
    if not patterns:
        return True
    for pattern in patterns:
        if pattern.startswith("*.") and host.endswith(pattern[1:]):
            return True
        if pattern == host:
            return True
    return False


def _path_score(pattern: str, path: str) -> int | None:
    if pattern.endswith("*"):
        prefix = pattern[:-1]
        if path.startswith(prefix):
            return len(prefix)
        return None
    if path == pattern:
        return len(pattern)
    return None


def match_route(routes: list[dict], method: str, host: str, path: str) -> dict | None:
    method = method.upper()
    candidates = []
    for route in routes:
        if route.get("methods") and method not in route["methods"]:
            continue
        if not _host_matches(route.get("hosts", []), host):
            continue
        best_len = None
        for pattern in route["paths"]:
            score = _path_score(pattern, path)
            if score is not None:
                best_len = max(best_len or 0, score)
        if best_len is not None:
            candidates.append((route.get("priority", 0), best_len, route["id"], route))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return candidates[0][3]
