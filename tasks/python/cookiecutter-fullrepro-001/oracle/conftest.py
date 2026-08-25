"""Shared fixtures, helpers, and constants for cookiecutter-fullrepro-001 oracle."""
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path


def make_template(root: Path, config: dict, files: dict[str, str | bytes], hooks=None) -> Path:
    """Create a minimal cookiecutter template directory."""
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


def isolate_home(monkeypatch, tmp_path: Path) -> Path:
    """Create an isolated HOME to avoid user config interference."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("COOKIECUTTER_CONFIG", raising=False)
    return home


def generated_path(tmp_path: Path, monkeypatch, template: Path, **kwargs) -> Path:
    """Generate a project and return the output path."""
    from cookiecutter.main import cookiecutter
    isolate_home(monkeypatch, tmp_path)
    output = tmp_path / "output"
    return Path(cookiecutter(str(template), no_input=True, output_dir=str(output), **kwargs))


def captured_exception(callable_):
    """Execute callable and return the raised exception, or fail."""
    try:
        callable_()
    except Exception as exc:
        return exc
    raise AssertionError("expected an exception")


def write_config(path: Path, replay_dir: Path, default_context=None) -> Path:
    """Write a user config YAML file (as JSON for simplicity)."""
    data = {
        "cookiecutters_dir": str(path.parent / "cookiecutters"),
        "replay_dir": str(replay_dir),
        "default_context": default_context or {},
        "abbreviations": {},
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def make_archive(source: Path, archive: Path, top_name="template") -> Path:
    """Create a zip archive from a template directory."""
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"{top_name}/", "")
        for path in source.rglob("*"):
            relative = path.relative_to(source).as_posix()
            if path.is_dir():
                zf.writestr(f"{top_name}/{relative}/", "")
            else:
                zf.write(path, f"{top_name}/{relative}")
    return archive


def run_cli(tmp_path: Path, template: Path, *args: str, extra_context=(), input_text=None):
    """Run cookiecutter CLI in a subprocess."""
    home = tmp_path / "cli-home"
    home.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env.pop("COOKIECUTTER_CONFIG", None)
    return subprocess.run(
        [sys.executable, "-m", "cookiecutter", *args, str(template), *extra_context],
        input=input_text, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, check=False, timeout=30,
    )


def file_tree(root: Path) -> dict[str, bytes]:
    """Return a dict mapping relative paths to file contents."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
