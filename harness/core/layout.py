"""The one place that knows where a task packet or a bench lives.

Both trees are bucketed by language, so a path can no longer be formed by joining
an id onto a root: `tasks/<id>` became `tasks/<language>/<id>` and `wip/<id>`
became `wip/<language>/<id>`. Resolution here is by directory search rather than
by reading `task.json`, because a gate has to be able to report on a packet whose
`task.json` is missing, unreadable, or disagrees with where the packet sits.

A packet left directly under `tasks/` is not resolved silently. `strays()` names
those so a caller can fail on them: a packet outside the language buckets is
invisible to every per-language tool, and a silent skip would read as a pass.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "tasks"
BENCHES = ROOT / "wip"

#: Ordered for reporting only; membership is what the resolvers use.
LANGUAGES = ("python", "java", "rust", "typescript", "go")

#: Names under `tasks/` and `wip/` that are not task ids.
_NOT_A_TASK = {".gitkeep", "_stage1", "GLOBAL_PROGRESS.md", "PROGRESS.md"}


def task_dirs() -> dict[str, Path]:
    """Every packet directory, keyed by task id."""
    found: dict[str, Path] = {}
    for language in LANGUAGES:
        bucket = TASKS / language
        if not bucket.is_dir():
            continue
        for path in sorted(bucket.iterdir()):
            if path.is_dir() and path.name not in _NOT_A_TASK:
                found[path.name] = path
    return found


def task_ids() -> list[str]:
    return sorted(task_dirs())


def task_dir(task_id: str) -> Path | None:
    """The packet directory for ``task_id``, or None if no bucket holds it."""
    return task_dirs().get(task_id)


def language_of(task_id: str) -> str | None:
    """The language a packet is filed under, taken from its path.

    The path is authoritative rather than `task.json`: the bucket is what every
    per-language tool dispatches on, so a disagreement between the two is a
    defect to be reported, not resolved by preferring the file.
    """
    path = task_dir(task_id)
    return path.parent.name if path is not None else None


def declared_language(task_id: str) -> str | None:
    """The `language` field of the packet's `task.json`, if it can be read."""
    path = task_dir(task_id)
    if path is None:
        return None
    meta = path / "task.json"
    if not meta.is_file():
        return None
    try:
        return json.loads(meta.read_text(encoding="utf-8-sig")).get("language")
    except (ValueError, OSError):
        return None


def oracle_dir(task_id: str) -> Path | None:
    """The oracle nested inside the packet."""
    path = task_dir(task_id)
    return None if path is None else path / "oracle"


def spec_path(task_id: str) -> Path | None:
    path = task_dir(task_id)
    return None if path is None else path / "spec.md"


def meta_path(task_id: str) -> Path | None:
    path = task_dir(task_id)
    return None if path is None else path / "task.json"


def bench_dir(task_id: str, language: str | None = None) -> Path:
    """The bench for ``task_id``, whether or not it exists yet.

    A bench is created before a packet exists, so this returns a path instead of
    None. The language is taken from the packet when there is one, then from an
    existing bench, and only then from the caller.
    """
    resolved = language_of(task_id) or _bench_language(task_id) or language
    if resolved is None:
        raise ValueError(
            f"cannot place a bench for {task_id!r}: no packet under tasks/, no "
            f"existing bench under wip/, and no language given"
        )
    return BENCHES / resolved / task_id


def _bench_language(task_id: str) -> str | None:
    for language in LANGUAGES:
        if (BENCHES / language / task_id).is_dir():
            return language
    return None


def existing_bench_dir(task_id: str) -> Path | None:
    """The bench for ``task_id`` if one is already on disk, else None."""
    language = _bench_language(task_id)
    return None if language is None else BENCHES / language / task_id


def bench_dirs() -> dict[str, Path]:
    """Every bench directory, keyed by task id."""
    found: dict[str, Path] = {}
    for language in LANGUAGES:
        bucket = BENCHES / language
        if not bucket.is_dir():
            continue
        for path in sorted(bucket.iterdir()):
            if path.is_dir() and path.name not in _NOT_A_TASK:
                found[path.name] = path
    return found


def strays() -> list[Path]:
    """Directories sitting directly under `tasks/` or `wip/` instead of a bucket."""
    out: list[Path] = []
    for root in (TASKS, BENCHES):
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir()):
            if (path.is_dir() and path.name not in LANGUAGES
                    and not path.name.startswith("_")
                    and path.name not in _NOT_A_TASK):
                out.append(path)
    return out
