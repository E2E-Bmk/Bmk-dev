from __future__ import annotations

from collections.abc import Callable

Handler = Callable[[bytes], object]


class EntrypointRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}
        self._limits: dict[str, int] = {}

    def register(self, name: str, handler: Handler, *, concurrency_limit: int = 0) -> None:
        if not name or not name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("entrypoint name must be non-empty alphanumeric text")
        if concurrency_limit < 0:
            raise ValueError("concurrency_limit must be >= 0")
        self._handlers[name] = handler
        self._limits[name] = concurrency_limit

    def get(self, name: str) -> Handler:
        try:
            return self._handlers[name]
        except KeyError as exc:
            raise KeyError(f"unknown entrypoint: {name}") from exc

    def concurrency_limit(self, name: str) -> int:
        return self._limits.get(name, 0)
