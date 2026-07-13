from __future__ import annotations

from dataclasses import dataclass

from .store import Store


@dataclass(frozen=True)
class RecoveryReport:
    recovered: list[str]
    untouched: list[str]


def recover_stale_jobs(store: Store, *, now: float, heartbeat_timeout: float) -> RecoveryReport:
    raise NotImplementedError
