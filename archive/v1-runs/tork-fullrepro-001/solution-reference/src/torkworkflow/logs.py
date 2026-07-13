from __future__ import annotations

from .datastore import WorkflowStore


class LogStore:
    def __init__(self, store: WorkflowStore | None = None) -> None:
        self.store = store
        self._entries: list[dict] = []

    def append(self, task_id: str, text: str, *, stream: str = "stdout", ts: int = 0) -> None:
        if text is None or text == "":
            return
        entry = {"task_id": task_id, "stream": stream, "text": str(text), "ts": int(ts)}
        if self.store is None:
            self._entries.append(entry)
        else:
            self.store.append_log(entry)

    def page(self, task_id: str | None = None, *, contains: str | None = None) -> list[dict]:
        entries = self.store.list_logs() if self.store is not None else list(self._entries)
        if task_id is not None:
            entries = [entry for entry in entries if entry.get("task_id") == task_id]
        if contains is not None:
            entries = [entry for entry in entries if contains in entry.get("text", "")]
        return entries
