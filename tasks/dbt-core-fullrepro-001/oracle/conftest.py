"""Shared fixtures and helpers for dbt-core-fullrepro-001 oracle tests."""

import json
from pathlib import Path

import pytest

from dbt.cli.main import dbtRunner, dbtRunnerResult

# ---------------------------------------------------------------------------
# Constants (anti-memorization: distinct from upstream test fixtures)
# ---------------------------------------------------------------------------

PROJECT_NAME = "analytics_hub"
MODEL_ALPHA = "stg_alpha"
MODEL_BETA = "dim_region"
MODEL_GAMMA = "fct_orders"
ANALYSIS_NAME = "quarterly_rollup"
SEED_NAME = "seed_currencies"
SOURCE_SCHEMA = "raw_data"
SOURCE_TABLE = "transactions"
EXPOSURE_NAME = "ops_dashboard"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_text(path: Path, text: str) -> None:
    """Write text to file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def invoke_dbt(args: list) -> dbtRunnerResult:
    """Invoke dbt CLI via the public dbtRunner API."""
    return dbtRunner().invoke(args)


def load_json(path: Path) -> dict:
    """Load a JSON file and return parsed dict."""
    return json.loads(path.read_text(encoding="utf-8"))


def base_args(project: Path, profiles: Path, target: Path) -> list:
    """Construct the standard CLI args for project/profiles/target."""
    return [
        "--project-dir", str(project),
        "--profiles-dir", str(profiles),
        "--target-path", str(target),
        "--no-version-check",
        "--quiet",
    ]


# ---------------------------------------------------------------------------
# Project scaffolding
# ---------------------------------------------------------------------------


def create_dbt_project(
    root: Path,
    name: str = PROJECT_NAME,
    *,
    include_source: bool = True,
    include_exposure: bool = True,
    include_analysis: bool = True,
    include_seed: bool = True,
    include_test: bool = True,
    extra_models: dict | None = None,
) -> tuple[Path, Path, Path]:
    """Create a minimal dbt project with DuckDB adapter.

    Returns (project_dir, profiles_dir, target_dir).
    """
    project = root / name
    profiles = root / "profiles"
    target = root / "target"

    write_text(
        project / "dbt_project.yml",
        "\n".join([
            f"name: {name}",
            "version: '2.0'",
            f"profile: {name}",
            "model-paths: [models]",
            "analysis-paths: [analyses]",
            "test-paths: [tests]",
            "seed-paths: [seeds]",
            f"models:",
            f"  {name}:",
            "    +materialized: view",
        ]) + "\n",
    )

    write_text(
        profiles / "profiles.yml",
        "\n".join([
            f"{name}:",
            "  target: dev",
            "  outputs:",
            "    dev:",
            "      type: duckdb",
            f"      path: {root / 'analytics.duckdb'}",
            "      schema: main",
            "      threads: 2",
        ]) + "\n",
    )

    write_text(
        project / "models" / f"{MODEL_ALPHA}.sql",
        "select 42 as region_id, 'north' as region_name\n",
    )
    write_text(
        project / "models" / f"{MODEL_BETA}.sql",
        f"select region_id, region_name from {{{{ ref('{MODEL_ALPHA}') }}}}\n",
    )
    write_text(
        project / "models" / f"{MODEL_GAMMA}.sql",
        f"select region_id, 100 as amount from {{{{ ref('{MODEL_ALPHA}') }}}}\n",
    )

    if extra_models:
        for mname, sql in extra_models.items():
            write_text(project / "models" / f"{mname}.sql", sql)

    schema_parts = [
        "version: 2",
        "models:",
        f"  - name: {MODEL_ALPHA}",
        "    description: Staging layer for regional data",
        "    columns:",
        "      - name: region_id",
        "        tests:",
        "          - not_null",
        f"  - name: {MODEL_BETA}",
        f"  - name: {MODEL_GAMMA}",
    ]

    if include_source:
        schema_parts.extend([
            "sources:",
            f"  - name: {SOURCE_SCHEMA}",
            "    schema: main",
            "    tables:",
            f"      - name: {SOURCE_TABLE}",
        ])

    if include_exposure:
        schema_parts.extend([
            "exposures:",
            f"  - name: {EXPOSURE_NAME}",
            "    type: dashboard",
            "    maturity: medium",
            "    url: https://analytics.example.invalid/ops",
            "    depends_on:",
            f"      - ref('{MODEL_ALPHA}')",
            "    owner:",
            "      name: DataOps Team",
            "      email: dataops@example.invalid",
        ])

    write_text(project / "models" / "schema.yml", "\n".join(schema_parts) + "\n")

    if include_analysis:
        write_text(
            project / "analyses" / f"{ANALYSIS_NAME}.sql",
            f"select count(*) as total_regions from {{{{ ref('{MODEL_ALPHA}') }}}}\n",
        )

    if include_seed:
        write_text(
            project / "seeds" / f"{SEED_NAME}.csv",
            "code,symbol\nUSD,$\nEUR,€\nGBP,£\n",
        )

    if include_test:
        write_text(
            project / "tests" / f"assert_{MODEL_ALPHA}_positive.sql",
            f"select * from {{{{ ref('{MODEL_ALPHA}') }}}} where region_id < 0\n",
        )

    return project, profiles, target


# ---------------------------------------------------------------------------
# Module-scoped fixtures for integration tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def project_root(tmp_path_factory):
    """Shared temp directory for the module."""
    return tmp_path_factory.mktemp("analytics_hub_project")


@pytest.fixture(scope="module")
def project_dirs(project_root):
    """Create the standard project and return (project, profiles, target)."""
    return create_dbt_project(project_root)
