from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Iterator


GATE = Path(__file__).resolve().parents[1]
RUNTIME = (GATE / "../../.venv-reference/Lib/site-packages").resolve()


@contextmanager
def workspace() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="cc-v7-") as raw:
        yield Path(raw)


@contextmanager
def isolated_environment(root: Path, additions: dict[str, str] | None = None) -> Iterator[None]:
    saved = os.environ.copy()
    home = root / "home"
    home.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(home)
    os.environ["USERPROFILE"] = str(home)
    os.environ.pop("COOKIECUTTER_CONFIG", None)
    os.environ.pop("COOKIECUTTER_REPO_PASSWORD", None)
    for key, value in (additions or {}).items():
        os.environ[key] = value
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(saved)


def make_template(root: Path, config: dict, files: dict[str, str | bytes], hooks: dict[str, str] | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cookiecutter.json").write_text(json.dumps(config), encoding="utf-8")
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    for name, content in (hooks or {}).items():
        path = root / "hooks" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def write_config(path: Path, replay_dir: Path, default_context: dict | None = None, *, artifact_catalog_dir: Path | None = None, publication_registry_dir: Path | None = None) -> Path:
    data = {
        "cookiecutters_dir": str(path.parent / "cookiecutters"),
        "replay_dir": str(replay_dir),
        "default_context": default_context or {},
        "abbreviations": {},
    }
    if artifact_catalog_dir is not None:
        data["artifact_catalog_dir"] = str(artifact_catalog_dir)
    if publication_registry_dir is not None:
        data["publication_registry_dir"] = str(publication_registry_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def api():
    from cookiecutter.main import cookiecutter

    return cookiecutter


def generate(root: Path, template: Path, **kwargs) -> Path:
    output = kwargs.pop("output_dir", root / "output")
    with isolated_environment(root):
        return Path(api()(str(template), no_input=True, output_dir=str(output), **kwargs))


def candidate_root() -> Path:
    import cookiecutter

    return Path(cookiecutter.__file__).resolve().parent.parent


def process_env(root: Path, additions: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(root / "home")
    env["USERPROFILE"] = str(root / "home")
    (root / "home").mkdir(parents=True, exist_ok=True)
    entries = [str(candidate_root()), str(RUNTIME)]
    if env.get("COOKIECUTTER_SYNTHETIC_PROFILE"):
        entries.insert(0, str(GATE))
    env["PYTHONPATH"] = os.pathsep.join(entries)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(additions or {})
    return env


def run_cli(root: Path, template: Path, *args: str, extra_context: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cookiecutter", *args, str(template), *extra_context],
        cwd=root,
        env=process_env(root),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=20,
        check=False,
    )


def file_tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def read_replay(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["cookiecutter"]


def assert_raises(exception_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except exception_type as exc:
        return exc
    raise AssertionError(f"expected {exception_type.__name__}")


def taskkill(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
