from __future__ import annotations


class LogStore:
    def append(self, task_id: str, text: str, *, stream: str = "stdout", ts: int = 0) -> None:
        raise NotImplementedError

    def page(self, task_id: str | None = None, *, contains: str | None = None) -> list[dict]:
        raise NotImplementedError
