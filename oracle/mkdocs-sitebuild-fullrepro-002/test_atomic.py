# Spec2Repo oracle - atomic tests for mkdocs-sitebuild-fullrepro-002
import mkdocs
import pytest
from pathlib import Path

from mkdocs.config import load_config
from mkdocs.exceptions import (
    Abort,
    BuildError,
    ConfigurationError,
    MkDocsException,
    PluginError,
)
from mkdocs.plugins import get_plugin_logger
from mkdocs.structure.files import File
from mkdocs.structure.toc import get_toc
from mkdocs.theme import Theme
from mkdocs.utils import clean_directory, get_build_datetime, get_relative_url, normalize_url


def _write_config(tmp_path, text="site_name: Example\n"):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Home\n", encoding="utf-8")
    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text(text, encoding="utf-8")
    return config_path


def test_file_projects_source_destination_url_and_classification(tmp_path):
    file = File("guide/start.md", str(tmp_path / "docs"), str(tmp_path / "site"), True)
    assert file.src_uri == "guide/start.md"
    assert file.dest_uri == "guide/start/index.html"
    assert file.url == "guide/start/"
    assert file.is_documentation_page() is True
    assert file.is_media_file() is False


def test_table_of_contents_exposes_nested_anchor_links():
    toc = get_toc(
        [{"name": "Intro", "id": "intro", "level": 1, "children": [{"name": "Details", "id": "details", "level": 2, "children": []}]}]
    )
    root = next(iter(toc))
    assert len(toc) == 1
    assert root.url == "#intro"
    assert root.children[0].url == "#details"


def test_builtin_theme_mapping_dirs_and_environment_are_available():
    theme = Theme("mkdocs", locale="en")
    env = theme.get_env()
    assert theme.name == "mkdocs"
    assert theme.dirs
    assert "main.html" in env.list_templates()
    assert "url" in env.filters and "script_tag" in env.filters


def test_custom_theme_directory_precedes_packaged_templates(tmp_path):
    (tmp_path / "main.html").write_text("CUSTOM", encoding="utf-8")
    theme = Theme("mkdocs", custom_dir=str(tmp_path))
    assert Path(theme.dirs[0]) == tmp_path
    assert theme.get_env().get_template("main.html").render() == "CUSTOM"


def test_theme_static_templates_are_exposed_as_a_set():
    theme = Theme("mkdocs", static_templates=("404.html", "sitemap.xml"))
    assert theme.static_templates == {"404.html", "sitemap.xml"}


def test_build_datetime_uses_source_date_epoch(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    value = get_build_datetime()
    assert value.isoformat().startswith("1970-01-01T00:00:00")
    assert value.utcoffset().total_seconds() == 0


def test_clean_directory_preserves_hidden_entries(tmp_path):
    (tmp_path / "visible.txt").write_text("remove", encoding="utf-8")
    (tmp_path / ".hidden").write_text("keep", encoding="utf-8")
    nested = tmp_path / "folder"
    nested.mkdir()
    (nested / "value.txt").write_text("remove", encoding="utf-8")
    clean_directory(str(tmp_path))
    assert sorted(path.name for path in tmp_path.iterdir()) == [".hidden"]


def test_url_helpers_preserve_external_values_and_rebase_relative_paths():
    assert get_relative_url("guide/", "nested/page.html") == "../guide/"
    assert normalize_url("https://example.com/x", base="docs/") == "https://example.com/x"
    assert normalize_url("asset.css", base="docs/") == "docs/asset.css"


def test_mkdocs_version_is_nonempty_string():
    assert isinstance(mkdocs.__version__, str)
    assert mkdocs.__version__


def test_load_config_supports_mapping_access(tmp_path):
    config_path = _write_config(tmp_path)

    config = load_config(config_file=str(config_path))

    assert config["site_name"] == "Example"


def test_load_config_supports_attribute_access(tmp_path):
    config_path = _write_config(tmp_path)

    config = load_config(config_file=str(config_path))

    assert config.site_name == "Example"


def test_load_config_rewinds_open_file(tmp_path):
    config_path = _write_config(tmp_path, "site_name: Rewound\n")

    with config_path.open(encoding="utf-8") as config_file:
        config_file.seek(0, 2)
        config = load_config(config_file=config_file)

    assert config.site_name == "Rewound"


def test_keyword_override_replaces_file_value(tmp_path):
    config_path = _write_config(tmp_path, "site_name: File Value\n")

    config = load_config(config_file=str(config_path), site_name="Override Value")

    assert config.site_name == "Override Value"


def test_none_keyword_override_is_ignored(tmp_path):
    config_path = _write_config(tmp_path, "site_name: File Value\n")

    config = load_config(config_file=str(config_path), site_name=None)

    assert config.site_name == "File Value"


def test_default_lookup_prefers_mkdocs_yml(tmp_path, monkeypatch):
    _write_config(tmp_path, "site_name: YML First\n")
    (tmp_path / "mkdocs.yaml").write_text(
        "site_name: YAML Second\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.site_name == "YML First"


def test_default_lookup_uses_mkdocs_yaml(tmp_path, monkeypatch):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "mkdocs.yaml").write_text(
        "site_name: YAML Fallback\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.site_name == "YAML Fallback"


def test_missing_default_config_raises_configuration_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ConfigurationError):
        load_config()


def test_invalid_yaml_raises_configuration_error(tmp_path):
    config_path = _write_config(tmp_path, "site_name: [unterminated\n")

    with pytest.raises(ConfigurationError):
        load_config(config_file=str(config_path))


def test_missing_inherited_config_raises_configuration_error(tmp_path):
    config_path = _write_config(
        tmp_path, "INHERIT: absent.yml\nsite_name: Child\n"
    )

    with pytest.raises(ConfigurationError):
        load_config(config_file=str(config_path))


def test_inherit_deep_merges_mappings(tmp_path):
    config_path = _write_config(
        tmp_path,
        "INHERIT: parent.yml\nsite_name: Child\nextra:\n  nested:\n    child: two\n",
    )
    (tmp_path / "parent.yml").write_text(
        "site_name: Parent\nextra:\n  nested:\n    parent: one\n",
        encoding="utf-8",
    )

    config = load_config(config_file=str(config_path))

    assert config.extra == {"nested": {"parent": "one", "child": "two"}}


def test_inherit_replaces_parent_lists(tmp_path):
    config_path = _write_config(
        tmp_path,
        "INHERIT: parent.yml\nsite_name: Child\nextra:\n  items: [child]\n",
    )
    (tmp_path / "parent.yml").write_text(
        "site_name: Parent\nextra:\n  items: [parent, second]\n",
        encoding="utf-8",
    )

    config = load_config(config_file=str(config_path))

    assert config.extra["items"] == ["child"]


def test_env_tag_reads_named_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("MKDOCS_ATOMIC_PRIMARY", "Environment Name")
    config_path = _write_config(
        tmp_path, "site_name: !ENV MKDOCS_ATOMIC_PRIMARY\n"
    )

    config = load_config(config_file=str(config_path))

    assert config.site_name == "Environment Name"


def test_env_tag_uses_fallback_variable(tmp_path, monkeypatch):
    monkeypatch.delenv("MKDOCS_ATOMIC_MISSING", raising=False)
    monkeypatch.setenv("MKDOCS_ATOMIC_FALLBACK", "Fallback Name")
    config_path = _write_config(
        tmp_path,
        "site_name: !ENV [MKDOCS_ATOMIC_MISSING, MKDOCS_ATOMIC_FALLBACK, Default Name]\n",
    )

    config = load_config(config_file=str(config_path))

    assert config.site_name == "Fallback Name"


def test_env_tag_uses_literal_default(tmp_path, monkeypatch):
    monkeypatch.delenv("MKDOCS_ATOMIC_MISSING_A", raising=False)
    monkeypatch.delenv("MKDOCS_ATOMIC_MISSING_B", raising=False)
    config_path = _write_config(
        tmp_path,
        "site_name: !ENV [MKDOCS_ATOMIC_MISSING_A, MKDOCS_ATOMIC_MISSING_B, Default Name]\n",
    )

    config = load_config(config_file=str(config_path))

    assert config.site_name == "Default Name"


def test_relative_docs_dir_resolves_from_config_directory(tmp_path):
    config_path = _write_config(
        tmp_path, "site_name: Paths\ndocs_dir: docs\n"
    )

    config = load_config(config_file=str(config_path))

    assert config.docs_dir == str(tmp_path / "docs")


def test_relative_site_dir_resolves_from_config_directory(tmp_path):
    config_path = _write_config(
        tmp_path, "site_name: Paths\nsite_dir: output\n"
    )

    config = load_config(config_file=str(config_path))

    assert config.site_dir == str(tmp_path / "output")


def test_empty_site_url_is_valid(tmp_path):
    config_path = _write_config(tmp_path, "site_name: Empty URL\nsite_url: ''\n")

    config = load_config(config_file=str(config_path))

    assert config.site_url == ""


def test_explicit_empty_plugins_replaces_default(tmp_path):
    config_path = _write_config(tmp_path, "site_name: No Plugins\nplugins: []\n")

    config = load_config(config_file=str(config_path))

    assert len(config.plugins) == 0


def test_plugins_default_includes_search(tmp_path):
    config_path = _write_config(tmp_path)

    config = load_config(config_file=str(config_path))

    assert "search" in config.plugins


def test_markdown_extensions_include_builtins(tmp_path):
    config_path = _write_config(tmp_path)

    config = load_config(config_file=str(config_path))

    assert config.markdown_extensions == ["toc", "tables", "fenced_code"]


def test_markdown_extensions_append_without_duplicates(tmp_path):
    config_path = _write_config(
        tmp_path,
        "site_name: Extensions\nmarkdown_extensions: [attr_list, toc, attr_list]\n",
    )

    config = load_config(config_file=str(config_path))

    assert config.markdown_extensions == [
        "toc",
        "tables",
        "fenced_code",
        "attr_list",
    ]


def test_missing_site_name_raises_abort(tmp_path):
    config_path = _write_config(tmp_path, "site_url: https://example.com/\n")

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_invalid_plugin_name_raises_abort(tmp_path):
    config_path = _write_config(
        tmp_path, "site_name: Plugin\nplugins: [definitely-not-a-plugin]\n"
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_missing_hook_file_raises_abort(tmp_path):
    config_path = _write_config(
        tmp_path, "site_name: Hook\nhooks: [missing_hook.py]\n"
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_missing_theme_custom_dir_raises_abort(tmp_path):
    config_path = _write_config(
        tmp_path,
        "site_name: Theme\ntheme:\n  name: mkdocs\n  custom_dir: absent_theme\n",
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_invalid_markdown_extension_raises_abort(tmp_path):
    config_path = _write_config(
        tmp_path,
        "site_name: Extension\nmarkdown_extensions: [definitely_not_an_extension]\n",
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_keyword_override_applies_before_strict_validation(tmp_path):
    config_path = _write_config(
        tmp_path,
        "site_name: Strict File\nstrict: true\nunexpected_key: value\n",
    )

    config = load_config(config_file=str(config_path), strict=False)

    assert config.site_name == "Strict File"


def test_abort_is_mkdocs_exception():
    assert issubclass(Abort, MkDocsException)


def test_abort_is_system_exit():
    assert issubclass(Abort, SystemExit)


def test_configuration_error_is_mkdocs_exception():
    assert issubclass(ConfigurationError, MkDocsException)


def test_build_error_is_mkdocs_exception():
    assert issubclass(BuildError, MkDocsException)


def test_plugin_error_is_build_error():
    assert issubclass(PluginError, BuildError)


def test_abort_uses_exit_code_one():
    with pytest.raises(Abort) as caught:
        raise Abort("ignored")

    assert caught.value.code == 1


def test_plugin_logger_uses_plugin_namespace():
    logger = get_plugin_logger("acme.widget")

    assert logger.name == "mkdocs.plugins.acme.widget"


def test_load_config_rejects_missing_docs_dir(tmp_path):
    config_path = tmp_path / "mkdocs.yml"
    config_path.write_text("site_name: Missing Docs\n", encoding="utf-8")

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_validation_rejects_unknown_theme_name(tmp_path):
    config_path = _write_config(
        tmp_path,
        "site_name: Bad Theme\ntheme:\n  name: definitely-not-a-theme\n",
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))


def test_unknown_config_key_is_warning_and_strict_aborts(tmp_path):
    config_path = _write_config(
        tmp_path,
        "site_name: Example\nunexpected_key: value\n",
    )

    assert load_config(config_file=str(config_path)).site_name == "Example"
    with pytest.raises(Abort):
        load_config(config_file=str(config_path), strict=True)


def test_docs_dir_and_site_dir_may_not_contain_each_other(tmp_path):
    config_path = _write_config(
        tmp_path,
        "site_name: Example\ndocs_dir: docs\nsite_dir: docs/site\n",
    )

    with pytest.raises(Abort):
        load_config(config_file=str(config_path))
