from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


FIXED_ENV = {
    "GIT_AUTHOR_NAME": "PSR Oracle",
    "GIT_AUTHOR_EMAIL": "oracle@example.invalid",
    "GIT_COMMITTER_NAME": "PSR Oracle",
    "GIT_COMMITTER_EMAIL": "oracle@example.invalid",
    "GIT_AUTHOR_DATE": "2024-01-01T00:00:00+0000",
    "GIT_COMMITTER_DATE": "2024-01-01T00:00:00+0000",
    "LC_ALL": "C.UTF-8",
    "LANG": "C.UTF-8",
    "TZ": "UTC",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_OPTIONAL_LOCKS": "0",
    "PYTHONHASHSEED": "0",
}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


def candidate_python() -> str:
    return os.environ.get("PSR_ORACLE_PYTHON", sys.executable)


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", "/tmp"),
        "PYTHONPATH": "",
        **FIXED_ENV,
    }
    if extra:
        env.update(extra)
    return env


def run_command(
    args: list[str],
    cwd: Path,
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=clean_env(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if check and result.returncode != 0:
        pytest.fail(
            "command failed: "
            + " ".join(args)
            + "\nstdout:\n"
            + result.stdout
            + "\nstderr:\n"
            + result.stderr
        )
    return result


def git(repo: Path, *args: str, date: str = "2024-01-01T00:00:00+0000") -> str:
    result = run_command(
        ["git", *args],
        repo,
        env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date},
    )
    return result.stdout.strip()


def psr(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run_command(
        [candidate_python(), "-m", "semantic_release", *args],
        repo,
        check=check,
    )


def python_snippet(repo: Path, source: str) -> subprocess.CompletedProcess[str]:
    return run_command([candidate_python(), "-c", source], repo)


def last_stdout_line(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def project_config(
    remote_url: str,
    *,
    version: str = "1.0.0",
    tag_format: str = "v{version}",
    extra: str = "",
    version_variables: list[str] | None = None,
) -> str:
    variables = version_variables or []
    variable_lines = "".join(f'  "{item}",\n' for item in variables)
    variable_block = ""
    if variable_lines:
        variable_block = "version_variables = [\n" + variable_lines + "]\n"
    return textwrap.dedent(
        f"""
        [project]
        name = "demo"
        version = "{version}"

        [tool.semantic_release]
        tag_format = "{tag_format}"
        version_toml = ["pyproject.toml:project.version"]
        {variable_block}commit_parser = "conventional"
        commit_message = "release: {{version}}"
        allow_zero_version = true
        {extra}

        [tool.semantic_release.branches.main]
        match = "main"
        prerelease = false
        prerelease_token = "rc"

        [tool.semantic_release.remote]
        type = "github"
        url = "{remote_url}"
        ignore_token_for_push = true

        [tool.semantic_release.changelog.default_templates]
        changelog_file = "CHANGELOG.md"
        mask_initial_release = false
        """
    ).strip() + "\n"


@pytest.fixture
def make_project(tmp_path: Path):
    def _make_project(
        *,
        version: str = "1.0.0",
        tag: str | None = "v1.0.0",
        tag_format: str = "v{version}",
        extra_config: str = "",
        version_variables: list[str] | None = None,
        json_config: bool = False,
    ) -> Path:
        repo = tmp_path / "repo"
        repo.mkdir()
        remote = tmp_path / "remote.git"
        run_command(["git", "init", "--bare", str(remote)], tmp_path)
        run_command(["git", "init", "-b", "main"], repo)
        git(repo, "config", "user.name", "PSR Oracle")
        git(repo, "config", "user.email", "oracle@example.invalid")
        git(repo, "config", "core.autocrlf", "false")
        git(repo, "config", "core.eol", "lf")
        git(repo, "config", "core.filemode", "true")
        git(repo, "config", "core.hooksPath", "/dev/null")
        git(repo, "config", "commit.gpgsign", "false")
        git(repo, "config", "tag.gpgsign", "false")
        git(repo, "config", "advice.detachedHead", "false")
        git(repo, "config", "init.defaultBranch", "main")
        remote_url = remote.as_uri()
        if json_config:
            (repo / "pyproject.toml").write_text(
                f'[project]\nname = "demo"\nversion = "{version}"\n',
                encoding="utf-8",
            )
            payload = {
                "semantic_release": {
                    "tag_format": tag_format,
                    "version_toml": ["pyproject.toml:project.version"],
                    "commit_parser": "conventional",
                    "commit_message": "release: {version}",
                    "allow_zero_version": True,
                    "branches": {
                        "main": {
                            "match": "main",
                            "prerelease": False,
                            "prerelease_token": "rc",
                        }
                    },
                    "remote": {
                        "type": "github",
                        "url": remote_url,
                        "ignore_token_for_push": True,
                    },
                    "changelog": {
                        "default_templates": {
                            "changelog_file": "CHANGELOG.md",
                            "mask_initial_release": False,
                        }
                    },
                }
            }
            (repo / "releaserc.json").write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            (repo / "pyproject.toml").write_text(
                project_config(
                    remote_url,
                    version=version,
                    tag_format=tag_format,
                    extra=extra_config,
                    version_variables=version_variables,
                ),
                encoding="utf-8",
            )
        (repo / "CHANGELOG.md").write_text("# CHANGELOG\n\n<!-- version list -->\n", encoding="utf-8")
        (repo / "pkg.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")
        (repo / "VERSION").write_text(version + "\n", encoding="utf-8")
        (repo / "RELEASE").write_text((tag or f"v{version}") + "\n", encoding="utf-8")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "chore: initial")
        if tag:
            git(repo, "tag", tag)
        return repo

    return _make_project


def commit_file(repo: Path, name: str, content: str, message: str, *, day: int = 2) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(repo, "add", name, date=f"2024-01-{day:02d}T00:00:00+0000")
    git(repo, "commit", "-m", message, date=f"2024-01-{day:02d}T00:00:00+0000")


def commit_with_body(
    repo: Path,
    name: str,
    content: str,
    subject: str,
    body: str,
    *,
    day: int = 2,
) -> None:
    path = repo / name
    path.write_text(content, encoding="utf-8")
    git(repo, "add", name, date=f"2024-01-{day:02d}T00:00:00+0000")
    git(
        repo,
        "commit",
        "-m",
        subject,
        "-m",
        body,
        date=f"2024-01-{day:02d}T00:00:00+0000",
    )


def read_version(repo: Path) -> str:
    match = re.search(
        r'version = "([^"]+)"',
        (repo / "pyproject.toml").read_text(encoding="utf-8"),
    )
    assert match is not None
    return match.group(1)


def tags(repo: Path) -> list[str]:
    output = git(repo, "tag", "--sort=refname")
    return [line for line in output.splitlines() if line]


def commit_subjects(repo: Path, count: int = 5) -> list[str]:
    output = git(repo, "log", f"--max-count={count}", "--format=%s")
    return [line for line in output.splitlines() if line]


def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
