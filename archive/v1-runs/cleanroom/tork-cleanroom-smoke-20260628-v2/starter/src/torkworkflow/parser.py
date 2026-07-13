from __future__ import annotations

from .models import JobSpec


def parse_job_spec(text: str, *, fmt: str | None = None) -> JobSpec:
    """Parse YAML or JSON text into a public JobSpec."""
    raise NotImplementedError


def normalize_job_spec(data: dict) -> JobSpec:
    """Normalize a decoded mapping into JobSpec/TaskSpec records."""
    raise NotImplementedError
