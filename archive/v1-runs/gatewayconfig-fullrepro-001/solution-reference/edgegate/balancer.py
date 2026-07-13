from __future__ import annotations

from .models import clone


def select_node(upstream: dict, counters: dict) -> dict:
    nodes = []
    for node in upstream["nodes"]:
        nodes.extend([node] * int(node.get("weight", 1)))
    key = upstream["id"]
    index = counters.get(key, 0) % len(nodes)
    counters[key] = counters.get(key, 0) + 1
    return clone(nodes[index])
