from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the Flit packages under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): public behaviors required by an integration test",
    )


def pytest_sessionstart(session):
    target_root_value = session.config.getoption("--target-root")
    if not target_root_value:
        return
    target_root = Path(target_root_value).resolve()
    core_root = target_root / "flit_core"
    if (core_root / "flit_core").is_dir():
        sys.path.insert(0, str(core_root))
    sys.path.insert(0, str(target_root))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project_config(
    *,
    project_name: str,
    version: str,
    description: str | None,
    readme: str,
    license_block: str,
    module: str | None,
    dynamic: bool,
    with_data: bool,
    with_scripts: bool,
    with_rules: bool,
) -> str:
    lines = [
        "[build-system]",
        'requires = ["flit_core >=3.11,<5"]',
        'build-backend = "flit_core.buildapi"',
        "",
        "[project]",
        f'name = "{project_name}"',
    ]
    if dynamic:
        lines.append('dynamic = ["version", "description"]')
    else:
        lines.extend(
            [
                f'version = "{version}"',
                f'description = "{description}"',
            ]
        )
    lines.extend(
        [
            f"readme = {readme}",
            'requires-python = ">=3.10"',
            license_block,
            'authors = [{name = "Ada Lovelace"}, {email = "ada@example.test"}]',
            'maintainers = [{name = "Grace Hopper"}, {email = "grace@example.test"}]',
            'keywords = ["build", "projection"]',
            'classifiers = ["Programming Language :: Python :: 3"]',
            'dependencies = ["tomli >= 2"]',
            "",
            "[project.optional-dependencies]",
            'cli = ["click >= 8"]',
            "",
            "[project.urls]",
            'Documentation = "https://docs.example.test/aurora"',
            'Source = "https://code.example.test/aurora"',
        ]
    )
    if with_scripts:
        lines.extend(
            [
                "",
                "[project.scripts]",
                'aurora = "aurora_tools.cli:main"',
                "",
                "[project.gui-scripts]",
                'aurora-gui = "aurora_tools.cli:main"',
                "",
                '[project.entry-points."aurora.plugins"]',
                'json = "aurora_tools.plugins:json_plugin"',
            ]
        )
    if module is not None:
        lines.extend(["", "[tool.flit.module]", f'name = "{module}"'])
    if with_data:
        lines.extend(["", "[tool.flit.external-data]", 'directory = "data"'])
    if with_rules:
        lines.extend(
            [
                "",
                "[tool.flit.sdist]",
                'include = ["docs/*.md"]',
                'exclude = ["docs/skip.md"]',
            ]
        )
    return "\n".join(lines) + "\n"


def _make_project(
    root: Path,
    *,
    project_name: str = "aurora-tools",
    module: str = "aurora_tools",
    version: str = "1.2.3",
    description: str = "Aurora static toolkit.",
    layout: str = "root",
    dynamic: bool = False,
    readme_table: bool = False,
    license_table: bool = False,
    with_data: bool = True,
    with_scripts: bool = True,
    with_rules: bool = False,
) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    package_root = root / ("src" if layout == "src" else "")
    module_dir = package_root.joinpath(*module.split("."))
    module_dir.mkdir(parents=True, exist_ok=True)

    if dynamic:
        init_text = '"""Aurora dynamic toolkit."""\n__version__ = "2.4.1"\n'
    else:
        init_text = '"""Aurora package implementation."""\nVALUE = "ready"\n'
    _write_text(module_dir / "__init__.py", init_text)
    _write_text(
        module_dir / "cli.py",
        "def main():\n    return 7\n",
    )
    _write_text(
        module_dir / "plugins.py",
        "def json_plugin(value=None):\n    return value\n",
    )
    _write_text(module_dir / "data.json", '{"kind": "package", "value": 7}\n')
    _write_text(module_dir / "nested" / "info.txt", "nested-data\n")
    _write_text(module_dir / "__pycache__" / "ignored.pyc", "bytecode-like\n")

    if readme_table:
        readme_value = '{text = "# Inline Aurora\\n", content-type = "text/markdown"}'
        readme_path = root / "README.md"
        _write_text(readme_path, "unused file readme\n")
    else:
        readme_value = '"README.md"'
        readme_path = root / "README.md"
        _write_text(readme_path, "# Aurora Tools\n\nA longer project description.\n")

    if license_table:
        license_block = 'license = {file = "COPYING.txt"}'
        license_path = root / "COPYING.txt"
        _write_text(license_path, "Copyright 2026 Aurora\n")
    else:
        license_block = 'license = "MIT"\nlicense-files = ["LICENSE"]'
        license_path = root / "LICENSE"
        _write_text(license_path, "MIT license text for the fixture.\n")

    if with_data:
        data_path = root / "data" / "share" / "config.ini"
        _write_text(data_path, "[fixture]\nvalue = seven\n")
    else:
        data_path = root / "data" / "share" / "config.ini"

    docs_path = root / "docs" / "guide.md"
    skipped_docs_path = root / "docs" / "skip.md"
    _write_text(docs_path, "guide\n")
    _write_text(skipped_docs_path, "skip\n")

    if module == "aurora_tools":
        module_override = None
    else:
        module_override = module
    config = _project_config(
        project_name=project_name,
        version=version,
        description=description,
        readme=readme_value,
        license_block=license_block,
        module=module_override,
        dynamic=dynamic,
        with_data=with_data,
        with_scripts=with_scripts,
        with_rules=with_rules,
    )
    pyproject = root / "pyproject.toml"
    _write_text(pyproject, config)

    return {
        "root": root,
        "module_dir": module_dir,
        "package_file": module_dir / "__init__.py",
        "package_data": module_dir / "data.json",
        "nested_data": module_dir / "nested" / "info.txt",
        "readme": readme_path,
        "license": license_path,
        "external_data": data_path,
        "docs": docs_path,
        "skipped_docs": skipped_docs_path,
        "pyproject": pyproject,
    }


@pytest.fixture
def static_project(tmp_path):
    return _make_project(tmp_path / "static")


@pytest.fixture
def dynamic_project(tmp_path):
    return _make_project(
        tmp_path / "dynamic",
        dynamic=True,
        with_data=False,
        with_scripts=False,
    )


@pytest.fixture
def src_project(tmp_path):
    return _make_project(
        tmp_path / "src-layout",
        project_name="src-distribution",
        module="actual_pkg",
        layout="src",
        with_data=False,
        with_scripts=False,
    )


@pytest.fixture
def namespace_project(tmp_path):
    return _make_project(
        tmp_path / "namespace",
        project_name="acme-widgets",
        module="acme.widgets",
        with_data=False,
        with_scripts=False,
    )


@pytest.fixture
def rules_project(tmp_path):
    return _make_project(
        tmp_path / "rules",
        with_data=False,
        with_scripts=False,
        with_rules=True,
    )


@pytest.fixture
def inline_metadata_project(tmp_path):
    return _make_project(
        tmp_path / "inline-metadata",
        readme_table=True,
        license_table=True,
        with_data=False,
        with_scripts=False,
    )
