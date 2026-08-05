from __future__ import annotations

import json
from datetime import date
from datetime import datetime
from pathlib import Path

import pytest

from lektor.builder import Builder
from lektor.cli import cli
from lektor.context import Context
from lektor.db import F
from lektor.db import get_alts
from lektor.environment import Environment
from lektor.metaformat import serialize
from lektor.metaformat import tokenize
from lektor.project import Project


def test_project_from_file_reads_name_tree_and_themes(project_data):
    project_file = project_data / "Demo.lektorproject"
    project = Project.from_file(str(project_file))

    assert project.name == "Demo Site"
    assert project.tree == str(project_data)
    assert project.project_file == str(project_file)
    assert project.themes == []


def test_project_from_path_finds_the_only_project_file(project_data):
    project = Project.from_path(project_data)

    assert project is not None
    assert project.name == "Demo Site"
    assert project.project_path == str(project_data / "Demo.lektorproject")


def test_project_discover_walks_up_from_a_nested_content_directory(
    project_data, monkeypatch
):
    monkeypatch.chdir(project_data / "content" / "blog" / "first")

    project = Project.discover()

    assert project is not None
    assert project.tree == str(project_data)


def test_project_content_path_from_filename_maps_content_records(project_data):
    project = Project.from_path(project_data)

    assert project.content_path_from_filename(
        project_data / "content" / "contents.lr"
    ) == "/"
    assert project.content_path_from_filename(
        project_data / "content" / "about" / "contents.lr"
    ) == "/about"
    assert project.content_path_from_filename(
        project_data / "content" / "about" / "extra.lr"
    ) == "/about/extra"
    assert project.content_path_from_filename(project_data / "content" / "notes.txt") is None


def test_project_output_path_uses_the_configured_relative_directory(project):
    assert project.get_output_path() == str(Path(project.tree) / "build-output")


def test_environment_config_exposes_project_url_and_alternatives(env):
    config = env.load_config()

    assert config.base_url == "https://example.test/docs/"
    assert config.base_path == "/docs/"
    assert config.primary_alternative == "en"
    assert config.list_alternatives() == ["en", "fr"]
    assert config.site_locale == "en_US"


def test_metaformat_tokenize_reads_scalar_and_multiline_fields():
    lines = [
        "title: Example\n",
        "---\n",
        "body:\n",
        "\n",
        "first line\n",
        "second line\n",
        "---\n",
        "enabled: yes\n",
    ]

    result = dict(tokenize(lines))

    assert result["title"] == ["Example"]
    assert "".join(result["body"]) == "first line\nsecond line"
    assert result["enabled"] == ["yes"]


def test_metaformat_serialize_round_trips_multiline_values():
    values = [
        ("title", "Example"),
        ("body", "first line\nsecond line\n"),
    ]

    encoded = list(serialize(values))
    decoded = dict(tokenize(encoded))

    assert decoded["title"] == ["Example"]
    assert "".join(decoded["body"]) == "first line\nsecond line\n"


def test_pad_root_loads_system_fields_and_typed_values(pad):
    root = pad.root

    assert root is not None
    assert root.path == "/"
    assert root["_id"] == ""
    assert root["_model"] == "page"
    assert root["_alt"] == "en"
    assert root["title"] == "Home"
    assert root["count"] == 7
    assert root["featured"] is True
    assert root["published"] == date(2024, 1, 2)
    assert root["when"] == datetime(2024, 1, 2, 3, 4, 5)


def test_pad_get_normalizes_equivalent_record_paths(pad):
    first = pad.get("/about")

    assert first is not None
    assert pad.get("about") is first
    assert pad.get("//about/.") is first


def test_pad_get_returns_none_for_a_missing_record(pad):
    assert pad.get("/does-not-exist") is None


def test_record_mapping_access_exposes_field_values(pad):
    about = pad.get("/about")

    assert about is not None
    assert about["title"] == "About"
    assert about.path == "/about"
    assert about.url_path == "/about/"


def test_record_url_path_uses_alternative_prefixes(pad):
    english = pad.get("/about", alt="en")
    french = pad.get("/about", alt="fr")

    assert english.url_path == "/about/"
    assert french.url_path == "/fr/about/"


def test_record_parent_and_child_relationships(pad):
    blog = pad.get("/blog")
    first = pad.get("/blog/first")

    assert blog is not None
    assert first is not None
    assert first.parent is blog
    assert first.is_child_of(blog)
    assert first.is_child_of(blog, strict=True)
    assert blog.is_child_of(blog)
    assert not blog.is_child_of(blog, strict=True)


def test_record_visibility_flags_reflect_explicit_system_fields(pad):
    hidden = pad.get("/hidden")
    secret = pad.get("/undiscoverable")
    visible = pad.get("/about")

    assert hidden.is_hidden is True
    assert hidden.is_visible is False
    assert secret.is_undiscoverable is True
    assert secret.is_discoverable is False
    assert visible.is_visible is True
    assert visible.is_discoverable is True


def test_pad_resolve_url_path_skips_invisible_records_by_default(pad):
    assert pad.resolve_url_path("/hidden/") is None
    assert pad.resolve_url_path("/undiscoverable/") is not None


def test_pad_resolve_url_path_can_include_hidden_records(pad):
    hidden = pad.resolve_url_path("/hidden/", include_invisible=True)

    assert hidden is not None
    assert hidden.path == "/hidden"


def test_query_visibility_options_are_independent(pad):
    children = pad.root.children

    assert {record["_id"] for record in children} == {"about", "blog"}
    assert {record["_id"] for record in children.include_hidden(True)} == {
        "about",
        "blog",
        "hidden",
    }
    assert {
        record["_id"]
        for record in children.include_undiscoverable(True)
    } == {"about", "blog", "undiscoverable"}


def test_query_filter_uses_public_record_expression_proxy(pad):
    records = pad.query("/").filter(F._model == "page").order_by("_id").all()

    assert [record["_id"] for record in records] == ["about", "hidden"]


def test_query_order_limit_offset_and_count_are_composable(pad):
    query = pad.get("/blog").children.order_by("-pub_date", "title")

    assert query.count() == 2
    assert [record["title"] for record in query] == ["Second Post", "First Post"]
    assert [record["title"] for record in query.limit(1)] == ["Second Post"]
    assert [record["title"] for record in query.offset(1)] == ["First Post"]


def test_query_get_and_first_find_records_by_local_id(pad):
    query = pad.get("/blog").children

    assert query.first()["title"] == "Second Post"
    assert query.get("first")["title"] == "First Post"
    assert query.get("missing") is None


def test_query_distinct_collects_scalar_values_and_multiline_tags(pad):
    query = pad.get("/blog").children

    assert query.distinct("tags") == {"python", "lektor", "static"}
    assert query.distinct("summary") == {
        "The first summary.",
        "The second summary.",
    }
    assert query.distinct("missing") == set()


def test_alternative_fallback_preserves_requested_language(pad):
    french_first = pad.get("/blog/first", alt="fr")

    assert french_first is not None
    assert french_first.alt == "fr"
    assert french_first["_source_alt"] == "_primary"
    assert french_first["title"] == "First Post"


def test_get_alts_reports_existing_translations_and_fallbacks(pad):
    root = pad.root
    first = pad.get("/blog/first", alt="fr")

    assert get_alts(root) == ["en", "fr"]
    assert get_alts(first) == ["en"]
    assert get_alts(first, fallback=True) == ["en", "fr"]


def test_record_url_to_builds_a_relative_child_link(pad):
    root = pad.root
    about = pad.get("/about")

    assert about is not None
    assert root.url_to(about) == "about/"


def test_pad_make_url_uses_the_configured_base_url(pad):
    assert pad.make_url("/about/", base_url="/") == "about/"
    assert pad.make_url("/about/", absolute=True) == "/docs/about/"
    assert pad.make_url("/about/", external=True) == "https://example.test/docs/about/"


def test_datamodel_exposes_custom_fields_and_child_policy(pad):
    page_model = pad.get("/about").datamodel
    blog_model = pad.get("/blog").datamodel

    assert [field.name for field in page_model.fields] == [
        "title",
        "body",
        "count",
        "featured",
        "tags",
        "published",
        "when",
    ]
    assert page_model.primary_field == "title"
    assert blog_model.child_config.model == "blog-post"
    assert blog_model.child_config.order_by == ["-pub_date", "title"]


def test_string_field_trims_whitespace_and_uses_the_first_line(env, pad):
    field = env.types["string"](env, {})
    raw_value = type("Raw", (), {"value": "  first line  \nsecond"})()

    assert field.value_from_raw(raw_value) == "first line"


def test_integer_and_boolean_fields_convert_raw_values(env, pad):
    integer = env.types["integer"](env, {})
    boolean = env.types["boolean"](env, {})
    integer_raw = type("Raw", (), {"value": " 12 "})()
    true_raw = type("Raw", (), {"value": "yes"})()
    false_raw = type("Raw", (), {"value": "0"})()

    assert integer.value_from_raw(integer_raw) == 12
    assert boolean.value_from_raw(true_raw) is True
    assert boolean.value_from_raw(false_raw) is False


def test_date_and_datetime_fields_convert_raw_values(env, pad):
    date_type = env.types["date"](env, {})
    datetime_type = env.types["datetime"](env, {})
    date_raw = type("Raw", (), {"value": "2024-03-04"})()
    datetime_raw = type("Raw", (), {"value": "2024-03-04 05:06:07"})()

    assert date_type.value_from_raw(date_raw) == date(2024, 3, 4)
    assert datetime_type.value_from_raw(datetime_raw) == datetime(2024, 3, 4, 5, 6, 7)


def test_markdown_field_renders_as_markup_for_a_record(pad):
    body = pad.root["body"]

    with Context(pad=pad) as context:
        context.source = pad.root
        assert "<strong>Lektor</strong>" in str(body)
    assert body.source == "Welcome to **Lektor**."


def test_datamodel_to_json_describes_field_types_and_names(pad):
    payload = pad.get("/about").datamodel.to_json(pad, pad.get("/about"))
    fields = {field["name"]: field for field in payload["fields"]}

    assert payload["id"] == "page"
    assert fields["title"]["type"]["name"] == "string"
    assert fields["body"]["type"]["name"] == "markdown"
    assert fields["_path"]["type"]["name"] == "string"


def test_asset_root_exposes_static_files_and_artifact_paths(pad):
    asset = pad.get_asset("static/site.css")

    assert asset is not None
    assert asset.name == "site.css"
    assert asset.url_path == "/static/site.css"
    assert asset.artifact_name == "/static/site.css"


def test_attachment_record_exposes_type_url_and_source_file(pad):
    attachment = pad.root.attachments.get("notes.txt")

    assert attachment is not None
    assert attachment["_attachment_type"] == "text"
    assert attachment.url_path == "/notes.txt"
    assert Path(attachment.attachment_filename).read_text(encoding="utf-8") == (
        "plain attachment\n"
    )


def test_environment_selects_html_autoescape_by_filename(env):
    assert env.select_jinja_autoescape("page.html") is True
    assert env.select_jinja_autoescape("page.xml") is True
    assert env.select_jinja_autoescape("data.txt") is False
    assert env.select_jinja_autoescape(None) is False


def test_environment_render_template_exposes_this_and_site(env, pad):
    with Context(pad=pad) as context:
        context.source = pad.root
        rendered = env.render_template(
            "page.html",
            pad=pad,
            this=pad.root,
        )

    assert "<title>Home</title>" in rendered
    assert "<h1>Home</h1>" in rendered
    assert "about/" in rendered


def test_builder_declares_a_page_artifact(builder, pad):
    program, state = builder.build(pad.root)
    artifact = program.primary_artifact

    assert artifact is not None
    assert artifact.artifact_name == "index.html"
    assert artifact.updated is True
    assert artifact in state.updated_artifacts


def test_builder_marks_a_built_artifact_current(builder, pad):
    program, state = builder.build(pad.root)

    assert state.failed_artifacts == []
    assert program.primary_artifact.is_current is True


def test_build_program_primary_artifact_is_the_built_page(builder, pad):
    program, _ = builder.build(pad.root)

    assert program.primary_artifact is program.artifacts[0]


def test_cli_project_info_json_matches_project_projection(
    cli_runner, cli_project_file, project
):
    from lektor.cli import cli

    result = cli_runner.invoke(
        cli,
        ["--project", str(cli_project_file), "project-info", "--json"],
    )

    assert result.exit_code == 0
    assert json.loads(result.output) == project.to_json()


def test_cli_content_file_info_json_maps_a_record_path(
    cli_runner, cli_project_file, project_data
):
    result = cli_runner.invoke(
        cli,
        [
            "--project",
            str(cli_project_file),
            "content-file-info",
            "--json",
            str(project_data / "content" / "about" / "contents.lr"),
        ],
    )

    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert payload["success"] is True
    assert payload["paths"] == ["/about"]
    assert payload["project"]["name"] == "Demo Site"
