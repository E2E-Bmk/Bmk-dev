from __future__ import annotations

from collections.abc import Callable

Handler = Callable[[bytes], object]


class EntrypointRegistry:
    def register(self, name: str, handler: Handler, *, concurrency_limit: int = 0) -> None:
        raise NotImplementedError

    def get(self, name: str) -> Handler:
        raise NotImplementedError

    def concurrency_limit(self, name: str) -> int:
        raise NotImplementedError
