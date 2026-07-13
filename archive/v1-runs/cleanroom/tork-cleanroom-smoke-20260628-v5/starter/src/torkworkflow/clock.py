from __future__ import annotations


class FakeClock:
    def __init__(self, start: int = 0) -> None:
        self._now = start

    def now(self) -> int:
        return self._now

    def advance(self, seconds: int) -> int:
        if seconds < 0:
            raise ValueError("seconds must be non-negative")
        self._now += seconds
        return self._now
