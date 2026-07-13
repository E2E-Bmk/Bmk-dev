from __future__ import annotations


def classify_marker(marker: dict[str, object]) -> str:
    action = marker.get("action")
    if action in {"rollback", "roll-forward", "clean"}:
        return str(action)
    if marker.get("complete"):
        return "roll-forward"
    if marker:
        return "rollback"
    return "clean"


def recovery_report(markers: list[dict[str, object]]) -> dict[str, object]:
    decisions = [{"marker": marker, "decision": classify_marker(marker)} for marker in markers]
    return {"status": "clean" if not markers else "recovered", "markers": decisions, "count": len(markers)}
