import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import mkdocs
from mkdocs.__main__ import cli
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort
from mkdocs.plugins import BasePlugin, PluginCollection


def write_project(tmp_path, config_text="site_name: Example\n", pages=None):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name, content in (pages or {"index.md": "# Home"}).items():
        path = docs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    config = tmp_path / "mkdocs.yml"
    config.write_text(textwrap.dedent(config_text).lstrip(), encoding="utf-8")
    return config


def test_public_package_exposes_version_and_cli_group():
    assert isinstance(mkdocs.__version__, str)
    assert mkdocs.__version__
    assert cli.name == "cli"
    assert "build" in cli.commands
    assert "serve" in cli.commands
    assert "new" in cli.commands


def test_python_module_version_reports_installed_version():
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "mkdocs" in result.stdout.lower()
    assert mkdocs.__version__ in result.stdout


def test_load_config_rejects_missing_docs_dir(tmp_path):
    config = tmp_path / "mkdocs.yml"
    config.write_text("site_name: Missing Docs\n", encoding="utf-8")

    with pytest.raises(Abort):
        load_config(config_file=str(config))


def test_project_config_defaults_include_site_and_theme(tmp_path):
    config_file = write_project(tmp_path, "site_name: Defaults\n")

    config = load_config(config_file=str(config_file))

    assert config.site_name == "Defaults"
    assert Path(config.docs_dir).name == "docs"
    assert Path(config.site_dir).name == "site"
    assert config.theme.name == "mkdocs"
    assert "search" in config.plugins


def test_build_api_writes_site_pages_and_search_assets(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Build API
        nav:
          - Home: index.md
          - Guide: guide.md
        """,
        {"index.md": "# Home\nWelcome", "guide.md": "# Guide\nContent"},
    )
    config = load_config(config_file=str(config_file))

    build(config)

    assert (Path(config.site_dir) / "index.html").exists()
    assert (Path(config.site_dir) / "guide" / "index.html").exists()
    assert (Path(config.site_dir) / "search" / "search_index.json").exists()


def test_build_site_dir_override_keeps_config_and_output_consistent(tmp_path):
    config_file = write_project(tmp_path, "site_name: Override\n", {"index.md": "# Home"})
    custom_site = tmp_path / "published"
    config = load_config(config_file=str(config_file), site_dir=str(custom_site))

    build(config)

    assert Path(config.site_dir) == custom_site
    assert (custom_site / "index.html").exists()
    assert not (tmp_path / "site" / "index.html").exists()


def test_strict_build_aborts_on_warning(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Strict
        nav:
          - Missing: missing.md
        """,
        {"index.md": "# Home"},
    )
    config = load_config(config_file=str(config_file), strict=True)

    with pytest.raises(Abort):
        build(config)


def test_plugin_lifecycle_events_run_during_build(tmp_path):
    events = []

    class Recorder(BasePlugin):
        def on_pre_build(self, *, config):
            events.append("pre_build")

        def on_post_build(self, *, config):
            events.append("post_build")

    config_file = write_project(tmp_path, "site_name: Plugins\n")
    config = load_config(config_file=str(config_file))
    plugins = PluginCollection()
    plugins["recorder"] = Recorder()
    config.plugins = plugins

    build(config)

    assert events == ["pre_build", "post_build"]


def test_plugin_build_error_hook_observes_build_failure(tmp_path):
    seen = []

    class FailingPlugin(BasePlugin):
        def on_pre_build(self, *, config):
            raise RuntimeError("boom")

        def on_build_error(self, *, error):
            seen.append(type(error).__name__)

    config_file = write_project(tmp_path, "site_name: Error Hook\n")
    config = load_config(config_file=str(config_file))
    plugins = PluginCollection()
    plugins["failing"] = FailingPlugin()
    config.plugins = plugins

    with pytest.raises(RuntimeError):
        build(config)
    assert seen == ["RuntimeError"]


def test_repo_url_and_site_url_shape_page_edit_links(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Links
        site_url: https://example.com/docs/
        repo_url: https://github.com/example/project
        edit_uri: edit/main/docs/
        """,
        {"index.md": "# Home"},
    )
    config = load_config(config_file=str(config_file))

    build(config)
    html = (Path(config.site_dir) / "index.html").read_text(encoding="utf-8")

    assert "https://example.com/docs/" in html
    assert "https://github.com/example/project" in html
    assert "edit/main/docs/index.md" in html


def test_custom_theme_directory_overrides_main_template(tmp_path):
    theme_dir = tmp_path / "theme"
    theme_dir.mkdir()
    (theme_dir / "main.html").write_text("CUSTOM {{ page.title }}", encoding="utf-8")
    config_file = write_project(
        tmp_path,
        f"""
        site_name: Custom Theme
        theme:
          name: mkdocs
          custom_dir: {theme_dir.as_posix()}
        """,
        {"index.md": "# Custom Page"},
    )
    config = load_config(config_file=str(config_file))

    build(config)

    assert (Path(config.site_dir) / "index.html").read_text(encoding="utf-8") == "CUSTOM Custom Page"


def test_validation_rejects_unknown_theme_name(tmp_path):
    config_file = write_project(
        tmp_path,
        """
        site_name: Bad Theme
        theme:
          name: definitely-not-a-theme
        """,
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_file))


def test_full_new_then_build_workflow(tmp_path):
    project = tmp_path / "project"
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "new", str(project)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    build_result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-f", str(project / "mkdocs.yml"), "-d", str(project / "public")],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert build_result.returncode == 0, build_result.stdout + build_result.stderr
    assert (project / "public" / "index.html").exists()
