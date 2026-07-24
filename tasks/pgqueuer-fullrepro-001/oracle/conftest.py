"""Shared helpers for PGQueuer oracle tests."""
from __future__ import annotations

import asyncio
from collections.abc import Mapping

from pgqueuer import InMemoryQueries, PgQueuer


def run(coro):
    return asyncio.run(coro)


def latest_status(rows, job_id):
    requested = int(job_id)
    if isinstance(rows, Mapping):
        for key in (job_id, requested, str(requested)):
            if key in rows:
                return rows[key]
        raise AssertionError(f"job id {requested} missing from job_status result")

    for row in rows:
        if isinstance(row, Mapping):
            key = row.get("job_id", row.get("id"))
            status = row.get("status")
        elif hasattr(row, "job_id") and hasattr(row, "status"):
            key = row.job_id
            status = row.status
        elif hasattr(row, "id") and hasattr(row, "status"):
            key = row.id
            status = row.status
        else:
            key, status = row
        if int(key) == requested:
            return status
    raise AssertionError(f"job id {requested} missing from job_status result")


def latest_statuses(rows, ids):
    return {int(job_id): latest_status(rows, job_id) for job_id in ids}


async def make_queries() -> InMemoryQueries:
    pgq = PgQueuer.in_memory()
    return pgq.qm.queries
