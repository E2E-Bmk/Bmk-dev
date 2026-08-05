from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import zipfile

import pytest


SOURCE_MARKER = "source:ok"
WHEEL_MARKER = "wheel:ok"
WHEEL_VERSION = "1.0.0"
COMMAND_TIMEOUT = 60
RUN_TIMEOUT = 30


@dataclass(frozen=True)
class FixtureProject:
    root: Path
    source_root: Path
    wheel: Path
    build_pex_root: Path
    wheel_version: str
    wheel_marker: str
    source_marker: str


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): document atomic coverage dependencies")


def _dummy_mode() -> bool:
    return os.environ.get("PEX_FULLREPRO_DUMMY_MODE") == "1"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _wheel_record_hash(content: str) -> tuple[str, int]:
    data = content.encode("utf-8")
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode("ascii").rstrip("=")
    return f"sha256={digest}", len(data)


def _write_wheel(wheel_dir: Path, *, version: str, marker: str) -> Path:
    dist_info = f"supportlib-{version}.dist-info"
    files = {
        "supportlib/__init__.py": f"""
VERSION = {version!r}
WHEEL_MARKER = {marker!r}


def marker():
    return WHEEL_MARKER


def combined(source):
    return "{{}}|{{}}|{{}}".format(source, WHEEL_MARKER, VERSION)
""".lstrip(),
        "supportlib/cli.py": """
from __future__ import annotations

import json
import sys

from supportlib import VERSION, marker


def main():
    print(json.dumps({
        "argv": sys.argv[1:],
        "dev_mode": bool(getattr(sys.flags, "dev_mode", 0)),
        "version": VERSION,
        "wheel": marker(),
    }, sort_keys=True))
    return 0
""".lstrip(),
        f"{dist_info}/METADATA": f"""
Metadata-Version: 2.1
Name: supportlib
Version: {version}
Summary: Tiny local PEX fixture package
""".lstrip(),
        f"{dist_info}/WHEEL": """
Wheel-Version: 1.0
Generator: pex-fullrepro
Root-Is-Purelib: true
Tag: py3-none-any
""".lstrip(),
        f"{dist_info}/entry_points.txt": """
[console_scripts]
support-cli = supportlib.cli:main
""".lstrip(),
        f"{dist_info}/top_level.txt": "supportlib\n",
    }
    record_lines = []
    for name, content in files.items():
        digest, size = _wheel_record_hash(content)
        record_lines.append(f"{name},{digest},{size}")
    record_lines.append(f"{dist_info}/RECORD,,")
    files[f"{dist_info}/RECORD"] = "\n".join(record_lines) + "\n"

    wheel_dir.mkdir(parents=True, exist_ok=True)
    wheel = wheel_dir / f"supportlib-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, content)
    return wheel


def _write_source_tree(source_root: Path, *, marker: str) -> None:
    _write(source_root / "demo_app" / "__init__.py", f"SOURCE_MARKER = {marker!r}\n")
    _write(
        source_root / "demo_app" / "main.py",
        """
from __future__ import annotations

import json
import os
import sys

from demo_app import SOURCE_MARKER
from supportlib import VERSION, combined, marker


def build_report():
    pex_root = os.environ.get("PEX_ROOT") or ""
    prefix = os.path.realpath(sys.prefix)
    root = os.path.realpath(pex_root) if pex_root else ""
    return {
        "argv": sys.argv[1:],
        "combined": combined(SOURCE_MARKER),
        "dev_mode": bool(getattr(sys.flags, "dev_mode", 0)),
        "has_pex_root_env": bool(pex_root),
        "prefix_under_pex_root": bool(root and prefix.startswith(root)),
        "prefix_has_venvs_segment": "venvs" in prefix.split(os.sep),
        "python": "{}.{}".format(sys.version_info[0], sys.version_info[1]),
        "source": SOURCE_MARKER,
        "version": VERSION,
        "wheel": marker(),
    }


def main():
    print(json.dumps(build_report(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".lstrip(),
    )


@pytest.fixture(scope="session")
def fixture_project(tmp_path_factory) -> FixtureProject:
    root = tmp_path_factory.mktemp("pex_fullrepro_project")
    source_marker = "source:dummy" if _dummy_mode() else SOURCE_MARKER
    wheel_marker = "wheel:dummy" if _dummy_mode() else WHEEL_MARKER
    wheel_version = "9.9.9" if _dummy_mode() else WHEEL_VERSION
    source_root = root / "source"
    _write_source_tree(source_root, marker=source_marker)
    wheel = _write_wheel(root / "wheels", version=wheel_version, marker=wheel_marker)
    return FixtureProject(
        root=root,
        source_root=source_root,
        wheel=wheel,
        build_pex_root=root / "build_pex_root",
        wheel_version=wheel_version,
        wheel_marker=wheel_marker,
        source_marker=source_marker,
    )


def _clean_env(*, pex_root: Path | None = None, keep_pythonpath: bool = True) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("PEX_")}
    if not keep_pythonpath:
        env.pop("PYTHONPATH", None)
    if pex_root is not None:
        env["PEX_ROOT"] = str(pex_root)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_INDEX"] = "1"
    env["PIP_NO_CACHE_DIR"] = "1"
    return env


def _display_args(args: list[str]) -> str:
    displayed = []
    for arg in args:
        displayed.append("<path>" if arg.startswith("/") else arg)
    return " ".join(displayed)


def run_command(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    timeout: int = COMMAND_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise AssertionError(
            "command failed with code {}: {}\nstdout:\n{}\nstderr:\n{}".format(
                result.returncode,
                _display_args(args),
                result.stdout,
                result.stderr,
            )
        )
    return result


def assert_reference_fixture(project: FixtureProject) -> None:
    assert (project.source_marker, project.wheel_marker, project.wheel_version) == (
        SOURCE_MARKER,
        WHEEL_MARKER,
        WHEEL_VERSION,
    )


def build_pex(
    project: FixtureProject,
    tmp_path: Path,
    name: str,
    *,
    layout: str = "zipapp",
    entry_point: str | None = "demo_app.main:main",
    script: str | None = None,
    inject_args: tuple[str, ...] = (),
    inject_python_args: tuple[str, ...] = (),
    venv: bool = False,
    runtime_pex_root: Path | None = None,
    include_source: bool = True,
) -> Path:
    assert_reference_fixture(project)
    if layout == "zipapp":
        output = tmp_path / f"{name}.pex"
    else:
        output = tmp_path / f"{name}-{layout}"
    cmd = [
        sys.executable,
        "-m",
        "pex",
        "--no-index",
        "--pex-root",
        str(project.build_pex_root),
        str(project.wheel),
        "-o",
        str(output),
        "--layout",
        layout,
    ]
    if include_source:
        cmd.extend(["-D", str(project.source_root)])
    if script is not None:
        cmd.extend(["-c", script])
    elif entry_point is not None:
        cmd.extend(["-m", entry_point])
    if inject_args:
        cmd.append("--inject-args=" + " ".join(shlex.quote(arg) for arg in inject_args))
    if inject_python_args:
        cmd.append("--inject-python-args=" + " ".join(shlex.quote(arg) for arg in inject_python_args))
    if venv:
        cmd.append("--venv")
    if runtime_pex_root is not None:
        cmd.extend(["--runtime-pex-root", str(runtime_pex_root)])
    run_command(cmd, env=_clean_env(pex_root=project.build_pex_root))
    return output


def run_pex(
    pex: Path,
    *,
    args: tuple[str, ...] = (),
    pex_root: Path | None = None,
    timeout: int = RUN_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        [sys.executable, str(pex), *args],
        env=_clean_env(pex_root=pex_root, keep_pythonpath=False),
        timeout=timeout,
    )


def run_pex_json(pex: Path, *, args: tuple[str, ...] = (), pex_root: Path | None = None) -> dict:
    result = run_pex(pex, args=args, pex_root=pex_root)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 1
    return json.loads(lines[0])


def read_pex_info_json(pex: Path) -> dict:
    if zipfile.is_zipfile(pex):
        with zipfile.ZipFile(pex) as zf:
            return json.loads(zf.read("PEX-INFO").decode("utf-8"))
    return json.loads((pex / "PEX-INFO").read_text(encoding="utf-8"))


def zipapp_names(pex: Path) -> set[str]:
    with zipfile.ZipFile(pex) as zf:
        return set(zf.namelist())


def relative_names(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*")}


def pex_root_has_runtime_files(pex_root: Path) -> bool:
    return pex_root.exists() and any(pex_root.iterdir())


def expected_main_report(
    *,
    argv: list[str] | None = None,
    dev_mode: bool = False,
    has_pex_root_env: bool = False,
    prefix_under_pex_root: bool = False,
    prefix_has_venvs_segment: bool = False,
) -> dict:
    return {
        "argv": argv or [],
        "combined": f"{SOURCE_MARKER}|{WHEEL_MARKER}|{WHEEL_VERSION}",
        "dev_mode": dev_mode,
        "has_pex_root_env": has_pex_root_env,
        "prefix_under_pex_root": prefix_under_pex_root,
        "prefix_has_venvs_segment": prefix_has_venvs_segment,
        "source": SOURCE_MARKER,
        "version": WHEEL_VERSION,
        "wheel": WHEEL_MARKER,
    }


def assert_main_projection(report: dict, **expected_overrides) -> None:
    expected = expected_main_report(**expected_overrides)
    for key, value in expected.items():
        assert report[key] == value
    assert report["python"] in {"3.10", "3.11"}


def assert_support_cli_projection(report: dict, *, argv: list[str] | None = None, dev_mode: bool = False) -> None:
    assert report == {
        "argv": argv or [],
        "dev_mode": dev_mode,
        "version": WHEEL_VERSION,
        "wheel": WHEEL_MARKER,
    }
