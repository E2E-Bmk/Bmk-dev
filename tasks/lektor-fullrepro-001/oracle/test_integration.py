from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from lektor.builder import Builder
from lektor.cli import cli
from lektor.context import Context
from lektor.db import F
from lektor.environment import Environment
from lektor.project import Project


@pytest.mark.depends_on(
    "test_query_order_limit_offset_and_count_are_composable",
    "test_environment_render_template_exposes_this_and_site",
)
def test_query_and_template_render_share_the_same_record_values(env, pad):
    blog = pad.get("/blog", page_num=1)

    with Context(pad=pad) as context:
        context.source = blog
        rendered = env.render_template("blog.html", pad=pad, this=blog)

    assert "<h1>Blog</h1>" in rendered
    assert "Second Post|/blog/second/" in rendered
    assert "NEXT" in rendered


@pytest.mark.depends_on(
    "test_record_url_path_uses_alternative_prefixes",
    "test_environment_render_template_exposes_this_and_site",
)
def test_alternative_record_and_template_use_the_requested_language(env, pad):
    french_root = pad.get("/", alt="fr")

    with Context(pad=pad) as context:
        context.source = french_root
        rendered = env.render_template("page.html", pad=pad, this=french_root)

    assert french_root.alt == "fr"
    assert french_root["title"] == "Accueil"
    assert "<title>Accueil</title>" in rendered
    assert 'href="about/"' in rendered


@pytest.mark.depends_on(
    "test_query_filter_uses_public_record_expression_proxy",
    "test_query_order_limit_offset_and_count_are_composable",
)
def test_filtered_and_ordered_query_drives_a_stable_result_projection(pad):
    query = (
        pad.query("/blog")
        .filter(F.pub_date >= date(2024, 1, 2))
        .order_by("-pub_date", "title")
    )

    assert [record["_id"] for record in query] == ["second", "first"]
    assert [record["title"] for record in query.limit(1)] == ["Second Post"]


@pytest.mark.depends_on(
    "test_record_visibility_flags_reflect_explicit_system_fields",
    "test_pad_resolve_url_path_skips_invisible_records_by_default",
)
def test_visibility_options_and_url_resolution_agree_for_hidden_content(pad):
    root_query = pad.root.children

    assert "hidden" not in {record["_id"] for record in root_query}
    assert root_query.include_hidden(True).get("hidden").is_hidden is True
    assert pad.resolve_url_path("/hidden/") is None
    assert pad.resolve_url_path("/hidden/", include_invisible=True).path == "/hidden"


@pytest.mark.depends_on(
    "test_query_order_limit_offset_and_count_are_composable",
    "test_record_url_path_uses_alternative_prefixes",
)
def test_pagination_records_expose_page_numbers_and_sliced_items(pad):
    first_page = pad.resolve_url_path("/blog/")
    second_page = pad.resolve_url_path("/blog/page/2/")

    assert first_page is not None
    assert second_page is not None
    assert first_page.page_num == 1
    assert second_page.page_num == 2
    assert [record["title"] for record in first_page.pagination.items] == ["Second Post"]
    assert [record["title"] for record in second_page.pagination.items] == ["First Post"]
    assert first_page.pagination.has_next is True
    assert second_page.pagination.has_prev is True


@pytest.mark.depends_on(
    "test_attachment_record_exposes_type_url_and_source_file",
    "test_record_parent_and_child_relationships",
)
def test_attachment_query_and_attachment_record_share_tree_metadata(pad):
    root = pad.root
    about = pad.get("/about")

    root_attachment = root.attachments.get("notes.txt")
    about_attachment = about.attachments.get("guide.txt")

    assert root.attachments.count() == 1
    assert root_attachment.parent is root
    assert about_attachment.parent is about
    assert {item["_id"] for item in root.attachments} == {"notes.txt"}
    assert {item["_attachment_type"] for item in root.attachments} == {"text"}


@pytest.mark.depends_on(
    "test_datamodel_exposes_custom_fields_and_child_policy",
    "test_datamodel_to_json_describes_field_types_and_names",
)
def test_model_fields_reach_records_and_model_json_together(pad):
    post = pad.get("/blog/first")
    model_json = post.datamodel.to_json(pad, post)
    model_field_names = {field["name"] for field in model_json["fields"]}

    assert post.datamodel.id == "blog-post"
    assert post["title"] == "First Post"
    assert post["pub_date"].isoformat() == "2024-01-02"
    assert {"title", "pub_date", "summary", "body", "tags"} <= model_field_names


@pytest.mark.depends_on(
    "test_markdown_field_renders_as_markup_for_a_record",
    "test_environment_render_template_exposes_this_and_site",
)
def test_markdown_field_and_page_template_produce_html(env, pad):
    post = pad.get("/blog/first")

    with Context(pad=pad) as context:
        context.source = post
        rendered = env.render_template("blog-post.html", pad=pad, this=post)

    assert "<h1>First Post</h1>" in rendered
    assert "<strong>post</strong>" in rendered
    assert "2024-01-02" in rendered


@pytest.mark.depends_on(
    "test_record_url_to_builds_a_relative_child_link",
    "test_environment_render_template_exposes_this_and_site",
)
def test_environment_rendering_and_record_url_to_use_one_pad_context(env, pad):
    about = pad.get("/about")
    template = env.jinja_env.from_string("{{ this.title }}|{{ this.url_path }}")

    with Context(pad=pad) as context:
        context.source = about
        rendered = template.render(this=about, site=pad)

    assert rendered == "About|/about/"
    assert pad.root.url_to(about) == "about/"


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_environment_render_template_exposes_this_and_site",
)
def test_builder_builds_root_template_into_index_artifact(builder, pad):
    program, state = builder.build(pad.root)
    output = Path(program.primary_artifact.dst_filename).read_text(encoding="utf-8")

    assert state.failed_artifacts == []
    assert program.primary_artifact.artifact_name == "index.html"
    assert "<title>Home</title>" in output
    assert "<strong>Lektor</strong>" in output
    assert '<a class="about" href="about/">About</a>' in output


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_attachment_record_exposes_type_url_and_source_file",
)
def test_builder_builds_child_pages_and_attachments_to_expected_artifacts(builder, pad):
    about_program, _ = builder.build(pad.get("/about"))
    attachment_program, _ = builder.build(pad.root.attachments.get("notes.txt"))

    assert about_program.primary_artifact.artifact_name == "about/index.html"
    assert attachment_program.primary_artifact.artifact_name == "notes.txt"
    assert Path(about_program.primary_artifact.dst_filename).is_file()
    assert Path(attachment_program.primary_artifact.dst_filename).read_text(
        encoding="utf-8"
    ) == "plain attachment\n"


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_asset_root_exposes_static_files_and_artifact_paths",
)
def test_builder_build_all_produces_pages_attachments_and_assets(builder, pad):
    assert builder.build_all() == 0

    output = Path(builder.destination_path)
    expected = {
        "index.html",
        "about/index.html",
        "blog/index.html",
        "blog/page/2/index.html",
        "blog/first/index.html",
        "blog/second/index.html",
        "undiscoverable/index.html",
        "notes.txt",
        "about/guide.txt",
        "static/site.css",
        "keep.txt",
        "_included.txt",
    }

    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and ".lektor" not in path.relative_to(output).parts
    }
    assert expected <= actual
    assert {
        path for path in actual if path.startswith("fr/")
    } >= {
        "fr/index.html",
        "fr/about/index.html",
        "fr/blog/index.html",
        "fr/blog/page/2/index.html",
        "fr/blog/first/index.html",
        "fr/blog/second/index.html",
        "fr/undiscoverable/index.html",
    }
    assert "hidden/index.html" not in actual
    assert "ignored.tmp" not in actual


@pytest.mark.depends_on(
    "test_builder_marks_a_built_artifact_current",
    "test_builder_declares_a_page_artifact",
)
def test_builder_reuses_a_current_artifact_on_the_second_build(builder, pad):
    first_program, first_state = builder.build(pad.root)
    second_program, second_state = builder.build(pad.root)

    assert first_state.updated_artifacts
    assert second_state.updated_artifacts == []
    assert second_program.primary_artifact.is_current is True
    assert Path(first_program.primary_artifact.dst_filename).read_bytes() == Path(
        second_program.primary_artifact.dst_filename
    ).read_bytes()


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_builder_marks_a_built_artifact_current",
)
def test_builder_rebuilds_an_artifact_when_its_template_changes(builder, pad):
    builder.build(pad.root)
    template = Path(pad.env.root_path) / "templates/page.html"
    template.write_text("<h1>Changed {{ this.title }}</h1>\n", encoding="utf-8")

    program, state = builder.build(pad.root)
    output = Path(program.primary_artifact.dst_filename).read_text(encoding="utf-8")

    assert state.updated_artifacts
    assert output == "<h1>Changed Home</h1>\n"


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_project_content_path_from_filename_maps_content_records",
)
def test_builder_rebuilds_an_artifact_when_a_record_changes(project_data, env):
    output = project_data / "record-change-output"
    output.mkdir()
    first_pad = env.new_pad()
    Builder(first_pad, output).build(first_pad.root)
    source = project_data / "content/contents.lr"
    source.write_text(
        source.read_text(encoding="utf-8").replace("title: Home", "title: Start"),
        encoding="utf-8",
    )
    second_pad = env.new_pad()

    program, state = Builder(second_pad, output).build(second_pad.root)
    output = Path(program.primary_artifact.dst_filename).read_text(encoding="utf-8")

    assert state.updated_artifacts
    assert "<title>Start</title>" in output


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_record_visibility_flags_reflect_explicit_system_fields",
)
def test_builder_prune_removes_an_artifact_after_a_page_becomes_hidden(
    project_data, env
):
    output = project_data / "prune-output"
    output.mkdir()
    first_pad = env.new_pad()
    first_builder = Builder(first_pad, output)
    first_builder.build(first_pad.get("/about"))
    artifact = output / "about/index.html"
    assert artifact.exists()

    source = project_data / "content/about/contents.lr"
    source.write_text(
        source.read_text(encoding="utf-8") + "\n---\n_hidden: yes\n",
        encoding="utf-8",
    )
    second_pad = env.new_pad()
    second_builder = Builder(second_pad, output)
    second_builder.build_all()
    second_builder.prune()

    assert not artifact.exists()


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_cli_project_info_json_matches_project_projection",
)
def test_cli_build_matches_the_direct_builder_render(
    cli_runner, cli_project_file, project_data, pad
):
    direct_builder = Builder(pad, project_data / "direct")
    direct_builder.build(pad.root)
    direct_output = (project_data / "direct" / "index.html").read_text(encoding="utf-8")
    cli_output = project_data / "cli"

    result = cli_runner.invoke(
        cli,
        [
            "--project",
            str(cli_project_file),
            "build",
            "--output-path",
            str(cli_output),
        ],
        input="y\n",
    )

    assert result.exit_code == 0
    assert (cli_output / "index.html").read_text(encoding="utf-8") == direct_output


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_builder_marks_a_built_artifact_current",
)
def test_cli_build_reuses_output_without_an_existing_files_prompt(
    cli_runner, cli_project_file, project_data
):
    output = project_data / "cli-output"
    args = [
        "--project",
        str(cli_project_file),
        "build",
        "--output-path",
        str(output),
    ]

    first = cli_runner.invoke(cli, args, input="y\n")
    second = cli_runner.invoke(cli, args, input="y\n")

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "files or folders already exist" not in second.output
    assert (output / "index.html").exists()


@pytest.mark.depends_on("test_cli_project_info_json_matches_project_projection")
def test_cli_project_info_text_and_json_agree(
    cli_runner, cli_project_file, project_data
):
    text_result = cli_runner.invoke(
        cli,
        ["--project", str(cli_project_file), "project-info"],
    )
    json_result = cli_runner.invoke(
        cli,
        ["--project", str(cli_project_file), "project-info", "--json"],
    )

    payload = json.loads(json_result.output)
    assert text_result.exit_code == 0
    assert json_result.exit_code == 0
    assert "Name: Demo Site" in text_result.output
    assert f"Tree: {project_data}" in text_result.output
    assert payload["name"] == "Demo Site"
    assert payload["tree"] == str(project_data)


@pytest.mark.depends_on("test_cli_content_file_info_json_maps_a_record_path")
def test_cli_content_file_info_text_and_json_agree(
    cli_runner, cli_project_file, project_data
):
    content_file = project_data / "content/about/contents.lr"
    text_result = cli_runner.invoke(
        cli,
        ["--project", str(cli_project_file), "content-file-info", str(content_file)],
    )
    json_result = cli_runner.invoke(
        cli,
        [
            "--project",
            str(cli_project_file),
            "content-file-info",
            "--json",
            str(content_file),
        ],
    )

    assert text_result.exit_code == 0
    assert json_result.exit_code == 0
    assert "  - /about" in text_result.output
    assert json.loads(json_result.output)["paths"] == ["/about"]


@pytest.mark.depends_on("test_cli_project_info_json_matches_project_projection")
def test_cli_project_info_short_alias_resolves_to_the_same_command(
    cli_runner, cli_project_file
):
    result = cli_runner.invoke(
        cli,
        ["--project", str(cli_project_file), "pr"],
    )

    assert result.exit_code == 0
    assert "Name: Demo Site" in result.output


@pytest.mark.depends_on(
    "test_query_distinct_collects_scalar_values_and_multiline_tags",
    "test_environment_render_template_exposes_this_and_site",
)
def test_query_distinct_values_and_template_tags_share_the_same_source_data(env, pad):
    posts = pad.get("/blog").children
    post = posts.get("first")
    with Context(pad=pad) as context:
        context.source = post
        rendered = env.render_template("blog-post.html", pad=pad, this=post)

    assert posts.distinct("tags") == {"python", "lektor", "static"}
    assert "First Post" in rendered
    assert posts.get("first")["tags"] == ["python", "lektor"]


@pytest.mark.depends_on(
    "test_record_url_path_uses_alternative_prefixes",
    "test_pad_resolve_url_path_skips_invisible_records_by_default",
)
def test_nested_record_urls_resolve_back_to_the_same_records(pad):
    post = pad.get("/blog/first")

    resolved = pad.resolve_url_path(post.url_path)

    assert resolved is not None
    assert resolved.path == post.path
    assert resolved.url_path == post.url_path


@pytest.mark.depends_on(
    "test_record_url_path_uses_alternative_prefixes",
    "test_builder_declares_a_page_artifact",
)
def test_alternative_build_produces_a_language_prefixed_artifact(builder, pad):
    french_root = pad.get("/", alt="fr")

    program, state = builder.build(french_root)

    assert state.failed_artifacts == []
    assert program.primary_artifact.artifact_name == "fr/index.html"
    assert "<title>Accueil</title>" in Path(
        program.primary_artifact.dst_filename
    ).read_text(encoding="utf-8")


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_cli_project_info_json_matches_project_projection",
)
def test_cli_source_info_only_indexes_without_rendering(
    cli_runner, cli_project_file, project_data
):
    output = project_data / "source-info"
    result = cli_runner.invoke(
        cli,
        [
            "--project",
            str(cli_project_file),
            "build",
            "--source-info-only",
            "--output-path",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert not (output / "index.html").exists()
    assert (output / ".lektor").exists()


@pytest.mark.depends_on(
    "test_project_output_path_uses_the_configured_relative_directory",
    "test_cli_project_info_json_matches_project_projection",
)
def test_cli_relative_output_path_is_resolved_from_the_working_directory(
    cli_runner, cli_project_file, project_data, monkeypatch
):
    monkeypatch.chdir(project_data)

    result = cli_runner.invoke(
        cli,
        [
            "--project",
            str(cli_project_file),
            "build",
            "--output-path",
            "htdocs",
        ],
        input="y\n",
    )

    assert result.exit_code == 0
    assert (project_data / "htdocs/index.html").exists()


@pytest.mark.depends_on(
    "test_asset_root_exposes_static_files_and_artifact_paths",
    "test_builder_declares_a_page_artifact",
)
def test_asset_inclusion_and_exclusion_rules_reach_the_asset_build_queue(builder, pad):
    program, _ = builder.build(pad.asset_root)
    names = {asset.name for asset in program.iter_child_sources()}

    assert {"static", "keep.txt", "_included.txt"} <= names
    assert "ignored.tmp" not in names
    assert ".hidden" not in names


@pytest.mark.depends_on(
    "test_query_order_limit_offset_and_count_are_composable",
    "test_environment_render_template_exposes_this_and_site",
)
def test_model_child_order_reaches_pagination_and_template_output(env, pad):
    blog = pad.get("/blog", page_num=1)
    second_page = pad.get("/blog", page_num=2)

    with Context(pad=pad) as context:
        context.source = blog
        first_render = env.render_template("blog.html", pad=pad, this=blog)
        context.source = second_page
        second_render = env.render_template("blog.html", pad=pad, this=second_page)

    assert "Second Post|/blog/second/" in first_render
    assert "First Post|/blog/first/" in second_render
    assert "NEXT" not in second_render


@pytest.mark.depends_on(
    "test_record_parent_and_child_relationships",
    "test_query_order_limit_offset_and_count_are_composable",
)
def test_sibling_navigation_uses_the_parent_model_order(pad):
    first = pad.get("/blog/first")
    siblings = first.get_siblings()

    assert siblings.prev_page is not None
    assert siblings.prev_page["title"] == "Second Post"
    assert siblings.next_page is None


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_builder_marks_a_built_artifact_current",
)
def test_model_file_dependency_rebuilds_a_page_artifact(project_data, env):
    output = project_data / "model-change-output"
    output.mkdir()
    first_pad = env.new_pad()
    Builder(first_pad, output).build(first_pad.root)
    model_file = project_data / "models/page.ini"
    model_file.write_text(
        model_file.read_text(encoding="utf-8").replace("name = Page", "name = Landing"),
        encoding="utf-8",
    )

    second_pad = env.new_pad()
    program, state = Builder(second_pad, output).build(second_pad.root)

    assert state.updated_artifacts
    assert program.primary_artifact.is_current is True


@pytest.mark.depends_on(
    "test_query_filter_uses_public_record_expression_proxy",
    "test_query_order_limit_offset_and_count_are_composable",
)
def test_query_transformations_leave_the_original_query_unchanged(pad):
    original = pad.get("/blog").children
    filtered = original.filter(F.title == "First Post").limit(1)

    assert original.count() == 2
    assert filtered.count() == 1
    assert filtered.first()["title"] == "First Post"
    assert original.count() == 2


@pytest.mark.depends_on(
    "test_markdown_field_renders_as_markup_for_a_record",
    "test_builder_declares_a_page_artifact",
)
def test_build_output_preserves_autoescaped_markup_and_markdown_markup(builder, pad):
    program, _ = builder.build(pad.root)
    output = Path(program.primary_artifact.dst_filename).read_text(encoding="utf-8")

    assert "<strong>Lektor</strong>" in output
    assert "&lt;" not in output
    assert "Welcome to" in output


@pytest.mark.depends_on(
    "test_project_from_path_finds_the_only_project_file",
    "test_environment_config_exposes_project_url_and_alternatives",
)
def test_direct_environment_and_cli_project_use_the_same_project_tree(
    cli_runner, cli_project_file, project, env
):
    result = cli_runner.invoke(
        cli,
        ["--project", str(cli_project_file), "project-info", "--json"],
    )
    payload = json.loads(result.output)

    assert result.exit_code == 0
    assert payload["name"] == project.name
    assert payload["tree"] == env.root_path


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_datamodel_exposes_custom_fields_and_child_policy",
)
def test_build_state_records_template_and_model_dependencies(builder, pad):
    program, _ = builder.build(pad.root)
    dependencies = {path for path, _ in program.primary_artifact.get_dependency_infos()}

    assert "templates/page.html" in dependencies
    assert "models/page.ini" in dependencies
    assert "content/contents.lr" in dependencies


@pytest.mark.depends_on(
    "test_cli_content_file_info_json_maps_a_record_path",
    "test_project_content_path_from_filename_maps_content_records",
)
def test_cli_content_file_info_rejects_a_file_outside_the_project(
    cli_runner, cli_project_file, tmp_path
):
    outside = tmp_path / "outside.lr"
    outside.write_text("title: outside\n", encoding="utf-8")

    result = cli_runner.invoke(
        cli,
        [
            "--project",
            str(cli_project_file),
            "content-file-info",
            "--json",
            str(outside),
        ],
    )

    assert result.exit_code != 0
    assert json.loads(result.output)["success"] is False


@pytest.mark.depends_on(
    "test_record_url_to_builds_a_relative_child_link",
    "test_pad_make_url_uses_the_configured_base_url",
)
def test_pad_url_modes_are_shared_by_record_url_to_and_explicit_modes(pad):
    about = pad.get("/about")

    assert about.url_to("/", external=True) == "https://example.test/docs/"
    assert pad.make_url("/", base_url="/", external=True) == "https://example.test/docs/"


@pytest.mark.depends_on(
    "test_builder_declares_a_page_artifact",
    "test_pad_resolve_url_path_skips_invisible_records_by_default",
)
def test_build_all_and_source_database_preserve_content_paths(builder, pad):
    assert builder.build_all() == 0
    root = pad.root
    output = Path(builder.destination_path)

    assert root.path == "/"
    assert (output / "blog/first/index.html").exists()
    assert pad.resolve_url_path("/blog/first/").path == "/blog/first"


@pytest.mark.depends_on(
    "test_query_filter_uses_public_record_expression_proxy",
    "test_environment_render_template_exposes_this_and_site",
)
def test_environment_template_globals_can_query_the_same_pad(env, pad):
    template = env.jinja_env.from_string(
        "{% for page in site.query('/').filter(F._model == 'page').order_by('_id') %}"
        "{{ page.title }};{% endfor %}"
    )

    rendered = template.render(site=pad)

    assert rendered == "About;Hidden Page;"
