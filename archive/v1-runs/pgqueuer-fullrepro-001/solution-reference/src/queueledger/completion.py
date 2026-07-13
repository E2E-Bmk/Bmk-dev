from __future__ import annotations

from .models import CompletionEvent
from .store import Store


class CompletionWatcher:
    def __init__(self, store: Store) -> None:
        self.store = store

    def poll(self, offset: int = 0) -> list[CompletionEvent]:
        return self.store.completions_since(offset)
