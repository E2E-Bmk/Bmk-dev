from __future__ import annotations

from dataclasses import dataclass

from .models import TERMINAL_STATES, JobLedgerError, JobRecord, to_epoch


@dataclass(frozen=True)
class PruneDecision:
    keep: list[JobRecord]
    prune: list[JobRecord]
    cutoff: int

    def pruned_ids(self) -> list[str]:
        return [job.id for job in sorted(self.prune, key=lambda item: item.id)]


def plan_prune(jobs: list[JobRecord], retain_seconds: int, *, now: str | int | None = None) -> PruneDecision:
    if retain_seconds < 0:
        raise JobLedgerError("retain_seconds must be non-negative")
    cutoff = to_epoch(now) - retain_seconds
    keep: list[JobRecord] = []
    prune: list[JobRecord] = []
    for job in jobs:
        if is_prunable(job, cutoff):
            prune.append(job)
        else:
            keep.append(job)
    return PruneDecision(keep=keep, prune=prune, cutoff=cutoff)


def is_prunable(job: JobRecord, cutoff: int) -> bool:
    if job.state not in TERMINAL_STATES:
        return False
    return to_epoch(job.updated_at) <= cutoff


def prune_report(before: list[JobRecord], decision: PruneDecision, metrics: dict[str, object]) -> dict[str, object]:
    return {
        "cutoff": decision.cutoff,
        "before_total": len(before),
        "after_total": len(decision.keep),
        "pruned_job_ids": decision.pruned_ids(),
        "metrics": metrics,
    }
