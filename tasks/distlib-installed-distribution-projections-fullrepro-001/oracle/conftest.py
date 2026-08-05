from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the distlib package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic behaviors required by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return
    target_root = Path(configured_root).resolve()
    for name in list(sys.modules):
        if name == "distlib" or name.startswith("distlib."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))


def _hash_bytes(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={encoded}"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _record_row(base: Path, path: Path) -> tuple[str, str, str]:
    data = path.read_bytes()
    return path.relative_to(base).as_posix(), _hash_bytes(data), str(len(data))


def _write_csv(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerows(rows)


@pytest.fixture
def installed_tree(tmp_path):
    site = tmp_path / "site-packages"
    package = site / "acme_widgets"
    info = site / "acme_widgets-1.2.3.dist-info"
    data_file = package / "data" / "config.json"
    core_file = package / "core.py"
    init_file = package / "__init__.py"
    _write_text(init_file, "VALUE = 42\n")
    _write_text(core_file, "def make_value():\n    return 'widgets'\n")
    _write_text(data_file, json.dumps({"color": "blue", "count": 3}, sort_keys=True))
    _write_text(
        info / "METADATA",
        "\n".join(
            [
                "Metadata-Version: 2.1",
                "Name: acme-widgets",
                "Version: 1.2.3",
                "Summary: Local widget fixture",
                "Home-page: https://example.invalid/acme-widgets",
                "Author: Acme Widgets",
                "Requires-Dist: base-lib (>=1.0)",
                "Provides-Dist: acme-alias (1.2.3)",
                "",
                "A deterministic installed distribution.",
                "",
            ]
        ),
    )
    pydist = {
        "metadata_version": "2.0",
        "name": "acme-widgets",
        "version": "1.2.3",
        "summary": "Local widget fixture",
        "run_requires": [{"requires": ["base-lib (>=1.0)"]}],
        "provides": ["acme-alias (1.2.3)"],
    }
    _write_text(info / "pydist.json", json.dumps(pydist, sort_keys=True))
    _write_text(info / "INSTALLER", "distlib-contract\n")
    _write_text(info / "REQUESTED", "")
    _write_text(info / "RESOURCES", f"data/config.json,{data_file}\n")
    exports = {
        "metadata_version": "2.0",
        "name": "acme-widgets",
        "version": "1.2.3",
        "extensions": {
            "python.exports": {
                "exports": {
                    "console_scripts": {
                        "acme-widget": "acme_widgets.core:make_value [gui=false]",
                    },
                    "distlib.demo": {
                        "plugin": "acme_widgets.core:make_value",
                    },
                }
            }
        },
    }
    _write_text(info / "pydist-exports.json", json.dumps(exports, sort_keys=True))
    rows = [
        _record_row(site, init_file),
        _record_row(site, core_file),
        _record_row(site, data_file),
        _record_row(site, info / "pydist.json"),
        _record_row(site, info / "METADATA"),
        _record_row(site, info / "INSTALLER"),
        _record_row(site, info / "REQUESTED"),
        _record_row(site, info / "RESOURCES"),
        _record_row(site, info / "pydist-exports.json"),
        ("acme_widgets-1.2.3.dist-info/RECORD", "", ""),
    ]
    _write_csv(info / "RECORD", rows)
    return {
        "site": site,
        "package": package,
        "info": info,
        "data_file": data_file,
        "core_file": core_file,
        "exports": exports,
    }


@pytest.fixture
def second_installed_tree(installed_tree):
    site = installed_tree["site"]
    package = site / "other_pkg"
    info = site / "other_pkg-0.5.dist-info"
    module_file = package / "__init__.py"
    _write_text(module_file, "NAME = 'other'\n")
    _write_text(
        info / "METADATA",
        "Metadata-Version: 2.1\nName: other-pkg\nVersion: 0.5\nSummary: Other fixture\n"
        "Home-page: https://example.invalid/other-pkg\nAuthor: Other Package\n",
    )
    _write_text(
        info / "pydist.json",
        json.dumps({"metadata_version": "2.0", "name": "other-pkg", "version": "0.5", "summary": "Other fixture"}),
    )
    _write_text(info / "INSTALLER", "distlib-contract\n")
    _write_text(info / "REQUESTED", "")
    _write_text(info / "RESOURCES", "")
    _write_text(info / "pydist-exports.json", json.dumps({"extensions": {"python.exports": {"exports": {}}}}))
    rows = [
        _record_row(site, module_file),
        _record_row(site, info / "pydist.json"),
        _record_row(site, info / "METADATA"),
        _record_row(site, info / "INSTALLER"),
        _record_row(site, info / "REQUESTED"),
        _record_row(site, info / "RESOURCES"),
        _record_row(site, info / "pydist-exports.json"),
        ("other_pkg-0.5.dist-info/RECORD", "", ""),
    ]
    _write_csv(info / "RECORD", rows)
    return installed_tree


@pytest.fixture
def manifest_tree(tmp_path):
    root = tmp_path / "source"
    for rel, text in {
        "README.txt": "readme\n",
        "LICENSE": "license\n",
        ".hidden": "hidden\n",
        "pkg/__init__.py": "",
        "pkg/module.py": "VALUE = 1\n",
        "pkg/data/config.json": "{}\n",
        "docs/index.rst": "docs\n",
        "build/temp.txt": "generated\n",
    }.items():
        _write_text(root / rel, text)
    return root


@pytest.fixture
def wheel_file(tmp_path):
    wheel_path = tmp_path / "acme_wheel-2.0-py3-none-any.whl"
    entries = {
        "acme_wheel/__init__.py": "VALUE = 'wheel'\n",
        "acme_wheel/data.txt": "wheel-data\n",
        "acme_wheel-2.0.dist-info/WHEEL": "\n".join(
            [
                "Wheel-Version: 1.1",
                "Generator: distlib-contract",
                "Root-Is-Purelib: true",
                "Tag: py3-none-any",
                "",
            ]
        ),
        "acme_wheel-2.0.dist-info/METADATA": "\n".join(
            [
                "Metadata-Version: 2.1",
                "Name: acme-wheel",
                "Version: 2.0",
                "Summary: Wheel fixture",
                "Home-page: https://example.invalid/acme-wheel",
                "Author: Acme Wheel",
                "",
            ]
        ),
    }
    rows = []
    for arcname, text in entries.items():
        data = text.encode("utf-8")
        rows.append((arcname, _hash_bytes(data), str(len(data))))
    rows.append(("acme_wheel-2.0.dist-info/RECORD", "", ""))
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, text in entries.items():
            zf.writestr(arcname, text)
        record_lines = []
        for row in rows:
            record_lines.append(",".join(row))
        zf.writestr("acme_wheel-2.0.dist-info/RECORD", "\n".join(record_lines) + "\n")
    return wheel_path
