"""Target package import roots per task.

`oracle_import_lint.py` and any future symbol-level check need to know which
top-level module names belong to the package under reconstruction, so that a
third-party dependency (`pytest`, `requests`) is not reported as an undeclared
symbol while a genuine undeclared symbol still is.

This mirrors `TARGET_IMPORTS` in the release repo's `harness/sandbox.py`. It
lives in its own module here because Bmk-dev is the construction side and does
not carry the scoring sandbox.

A task missing from this mapping cannot be linted: with no target roots every
import is skipped and the lint passes vacuously. `oracle_import_lint.py`
reports `LINT_FAIL` for an absent task rather than printing a pass it did not
earn.
"""

from __future__ import annotations


TARGET_IMPORTS: dict[str, list[str]] = {
    "anyio-async-runtime-fullrepro-001": ["anyio"],
    "apscheduler-jobs-fullrepro-001": ["apscheduler"],
    "astroid-ast-inference-fullrepro-001": ["astroid"],
    "attrs-classes-fullrepro-001": ["attr", "attrs"],
    "authlib-fullrepro-001": ["authlib"],
    "babel-fullrepro-001": ["babel"],
    "bandit-securityscan-fullrepro-001": ["bandit"],
    "beancount-ledger-fullrepro-002": ["beancount"],
    "boltons-coreutils-fullrepro-001": ["boltons"],
    "cattrs-converters-fullrepro-001": ["cattrs"],
    "cookiecutter-fullrepro-001": ["cookiecutter"],
    "copier-template-fullrepro-001": ["copier"],
    "coveragepy-fullrepro-001": ["coverage"],
    "commons-pool-fullrepro-001": ["org.apache.commons.pool3"],
    "cron-utils-fullrepro-001": ["com.cronutils"],
    "curio-task-coordination-fullrepro-001": ["curio"],
    "dateparser-dates-fullrepro-001": ["dateparser"],
    "dbt-core-fullrepro-001": ["dbt"],
    "depgraph-maven-plugin-fullrepro-001": ["com.github.ferstl.depgraph"],
    "deal-runtime-contracts-fullrepro-001": ["deal"],
    "diskcache-cache-fullrepro-001": ["diskcache"],
    "dnspython-fullrepro-001": ["dns"],
    "doit-taskrunner-fullrepro-002": ["doit"],
    "dvc-fullrepro-001": ["dvc"],
    "dynaconf-settings-fullrepro-001": ["dynaconf"],
    "fsspec-filesystem-fullrepro-001": ["fsspec"],
    "griffe-apimodel-fullrepro-001": ["griffe"],
    "h2-protocol-fullrepro-001": ["h2"],
    "halodb-fullrepro-001": ["com.oath.halodb"],
    "hikaricp-fullrepro-001": ["com.zaxxer.hikari"],
    "httpcore-transport-fullrepro-001": ["httpcore"],
    "httpx-client-fullrepro-001": ["httpx"],
    "invoke-taskrunner-fullrepro-001": ["invoke"],
    "japicmp-fullrepro-001": ["japicmp"],
    "jline2-fullrepro-001": ["jline"],
    "jrnl-journal-fullrepro-002": ["jrnl"],
    "jpeek-fullrepro-001": ["org.jpeek"],
    "jupyter-client-kernel-protocol-fullrepro-001": ["jupyter_client"],
    "kedro-pipeline-fullrepro-001": ["kedro"],
    "loguru-fullrepro-001": ["loguru"],
    "luigi-workflow-fullrepro-001": ["luigi"],
    "marshmallow-schema-fullrepro-001": ["marshmallow"],
    "migrations-fullrepro-001": ["org.apache.ibatis.migration"],
    "microconfig": ["io.microconfig"],
    "mkdocs-sitebuild-fullrepro-002": ["mkdocs"],
    "nbformat-notebook-fullrepro-001": ["nbformat"],
    "networkx-graph-state-fullrepro-001": ["networkx"],
    "nikola-fullrepro-001": ["nikola"],
    "packaging-core-fullrepro-001": ["packaging"],
    "peewee-fullrepro-001": ["peewee", "playhouse"],
    "pelican-sitegen-fullrepro-001": ["pelican"],
    "pgqueuer-fullrepro-001": ["pgqueuer"],
    "pint-fullrepro-001": ["pint"],
    "pf4j-fullrepro-001": ["org.pf4j"],
    "pre-commit-hooks-fullrepro-002": ["pre_commit"],
    "prompt_toolkit-terminal-ui-fullrepro-001": ["prompt_toolkit"],
    "pypdf-fullrepro-001": ["pypdf"],
    "quart-async-web-fullrepro-001": ["quart"],
    "requests-cache-fullrepro-001": ["requests_cache"],
    "revapi": ["org.revapi"],
    "rq-fullrepro-001": ["rq"],
    "schematics-model-validation-fullrepro-001": ["schematics"],
    "sqlalchemy-fullrepro-001": ["sqlalchemy"],
    "starlette-asgi-fullrepro-001": ["starlette"],
    "structlog-event-context-fullrepro-001": ["structlog"],
    "tox-envrunner-fullrepro-001": ["tox"],
    "traitlets-core-fullrepro-001": ["traitlets"],
    "transitions-state-machine-fullrepro-001": ["transitions"],
    "vcrpy-fullrepro-001": ["vcr"],
    "webob-request-response-fullrepro-001": ["webob"],
    "whoosh-index-search-fullrepro-001": ["whoosh"],
    "wtforms-form-lifecycle-fullrepro-001": ["wtforms"],
}


# The TypeScript lane keeps its import roots in typescript_target_imports.json for
# the same reason the Rust lane does: the scorer and the lint must agree on one
# source per language rather than drift apart.
def _merge_typescript_registrations() -> None:
    import json
    from pathlib import Path

    path = Path(__file__).with_name("typescript_target_imports.json")
    if not path.exists():
        return
    try:
        extra = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for task_id, roots in extra.items():
        if isinstance(roots, str):
            roots = [roots]
        TARGET_IMPORTS.setdefault(task_id, list(roots))


_merge_typescript_registrations()

# Java tasks keep their roots in java_target_imports.json, following the rust and
# typescript lanes. The value is a Maven artifactId, not a Java package: the
# provenance audit matches it against `dependency:list` output, where the artifact
# is what appears. Registering `org.markline` instead of `markline-core` resolves
# no dependency, and because an unmapped task fails the lint outright, that error
# reads as a missing registration rather than a wrong one.
def _merge_java_registrations() -> None:
    import json
    from pathlib import Path

    path = Path(__file__).with_name("java_target_imports.json")
    if not path.exists():
        return
    try:
        extra = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for task_id, roots in extra.items():
        if isinstance(roots, str):
            roots = [roots]
        TARGET_IMPORTS.setdefault(task_id, list(roots))


_merge_java_registrations()
