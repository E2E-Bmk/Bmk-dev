# Spec2Repo oracle - atomic tests for cookiecutter-fullrepro-001
import json
import string
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cookiecutter.exceptions import (
    ConfigDoesNotExistException,
    ContextDecodingException,
    InvalidModeException,
    NonTemplatedInputDirException,
    RepositoryNotFound,
    UndefinedVariableInTemplate,
    UnknownExtension,
)
from cookiecutter.main import cookiecutter

from conftest import (
    make_template, isolate_home, generated_path, captured_exception,
    write_config, make_archive, run_cli, file_tree,
)


# Atomic: one documented public behavior per test.


def test_api_returns_an_absolute_project_path(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "absolute_demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert result.is_absolute()
    assert result.name == "absolute_demo"


def test_string_default_renders_file_content(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "string_demo", "title": "Plain Title"},
        {"{{cookiecutter.project_slug}}/title.txt": "{{ cookiecutter.title }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "title.txt").read_text(encoding="utf-8") == "Plain Title"


def test_extra_context_overrides_the_project_directory_name(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "default_name"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    result = generated_path(
        tmp_path, monkeypatch, template, extra_context={"project_slug": "override_name"}
    )
    assert result.name == "override_name"


def test_extra_context_overrides_rendered_file_content(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "demo", "color": "blue"},
        {"{{cookiecutter.project_slug}}/color.txt": "{{ cookiecutter.color }}"},
    )
    result = generated_path(
        tmp_path, monkeypatch, template, extra_context={"color": "green"}
    )
    assert (result / "color.txt").read_text(encoding="utf-8") == "green"


def test_templated_default_uses_an_earlier_variable(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {
            "project_name": "My Project",
            "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}",
        },
        {"{{cookiecutter.project_slug}}/slug.txt": "{{ cookiecutter.project_slug }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert result.name == "my_project"
    assert (result / "slug.txt").read_text(encoding="utf-8") == "my_project"


def test_choice_variable_uses_its_first_item_without_input(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "choice_demo", "license": ["MIT", "BSD-3"]},
        {"{{cookiecutter.project_slug}}/license.txt": "{{ cookiecutter.license }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "license.txt").read_text(encoding="utf-8") == "MIT"


def test_true_boolean_is_available_as_a_boolean(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "true_demo", "enabled": True},
        {"{{cookiecutter.project_slug}}/flag.txt": "{{ cookiecutter.enabled }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "flag.txt").read_text(encoding="utf-8") == "True"


def test_false_boolean_is_available_as_a_boolean(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "false_demo", "enabled": False},
        {"{{cookiecutter.project_slug}}/flag.txt": "{{ cookiecutter.enabled }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "flag.txt").read_text(encoding="utf-8") == "False"


def test_dictionary_values_are_accessible_in_templates(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "dict_demo", "metadata": {"owner": "Ada", "team": "Core"}},
        {"{{cookiecutter.project_slug}}/owner.txt": "{{ cookiecutter.metadata.owner }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "owner.txt").read_text(encoding="utf-8") == "Ada"


def test_single_underscore_variable_is_not_pre_rendered(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "private_demo", "_literal": "{{ cookiecutter.project_slug }}"},
        {"{{cookiecutter.project_slug}}/value.txt": "{{ cookiecutter._literal }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "value.txt").read_text(encoding="utf-8") == "{{ cookiecutter.project_slug }}"


def test_double_underscore_variable_is_rendered_from_prior_context(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "private_demo", "__derived": "{{ cookiecutter.project_slug }}-derived"},
        {"{{cookiecutter.project_slug}}/value.txt": "{{ cookiecutter.__derived }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "value.txt").read_text(encoding="utf-8") == "private_demo-derived"


def test_jsonify_filter_serializes_a_dictionary(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "json_demo", "metadata": {"owner": "Ada", "team": "Core"}},
        {"{{cookiecutter.project_slug}}/data.json": "{{ cookiecutter.metadata | jsonify }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert json.loads((result / "data.json").read_text(encoding="utf-8")) == {
        "owner": "Ada",
        "team": "Core",
    }


def test_jsonify_filter_accepts_a_custom_indent(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "json_indent", "metadata": {"owner": "Ada"}},
        {"{{cookiecutter.project_slug}}/data.json": "{{ cookiecutter.metadata | jsonify(2) }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    rendered = (result / "data.json").read_text(encoding="utf-8")
    assert '\n  "owner": "Ada"' in rendered


def test_random_ascii_string_honors_the_requested_length(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "random_length"},
        {"{{cookiecutter.project_slug}}/token.txt": "{{ random_ascii_string(24) }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert len((result / "token.txt").read_text(encoding="utf-8")) == 24


def test_random_ascii_string_without_punctuation_uses_letters(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "random_letters"},
        {"{{cookiecutter.project_slug}}/token.txt": "{{ random_ascii_string(32) }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    token = (result / "token.txt").read_text(encoding="utf-8")
    assert len(token) == 32
    assert token.isascii()
    assert set(token).isdisjoint(string.punctuation)


def test_random_ascii_string_with_punctuation_uses_documented_corpus(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "random_punctuation"},
        {"{{cookiecutter.project_slug}}/token.txt": "{{ random_ascii_string(256, punctuation=True) }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    token = (result / "token.txt").read_text(encoding="utf-8")
    assert len(token) == 256
    assert token.isascii()
    assert any(character in string.punctuation for character in token)


def test_slugify_filter_produces_a_lowercase_hyphenated_slug(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "slug_demo", "title": "Hello Friendly World"},
        {"{{cookiecutter.project_slug}}/slug.txt": "{{ cookiecutter.title | slugify }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "slug.txt").read_text(encoding="utf-8") == "hello-friendly-world"


def test_uuid_global_produces_a_uuid4_string(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "uuid_demo"},
        {"{{cookiecutter.project_slug}}/uuid.txt": "{{ uuid4() }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    value = uuid.UUID((result / "uuid.txt").read_text(encoding="utf-8"))
    assert value.version == 4


def test_time_tag_formats_the_current_utc_year(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "time_demo"},
        {"{{cookiecutter.project_slug}}/year.txt": "{% now 'utc', '%Y' %}"},
    )
    before = datetime.now(timezone.utc).year
    result = generated_path(tmp_path, monkeypatch, template)
    after = datetime.now(timezone.utc).year
    assert (result / "year.txt").read_text(encoding="utf-8") in {str(before), str(after)}


def test_invalid_cookiecutter_json_raises_context_decoding_exception(tmp_path, monkeypatch):
    isolate_home(monkeypatch, tmp_path)
    template = tmp_path / "template"
    template.mkdir()
    (template / "cookiecutter.json").write_text("{invalid", encoding="utf-8")
    (template / "{{cookiecutter.project_slug}}").mkdir()
    exc = captured_exception(
        lambda: cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))
    )
    assert isinstance(exc, ContextDecodingException)
    assert "cookiecutter.json" in str(exc).lower()


def test_missing_config_file_raises_config_does_not_exist(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    isolate_home(monkeypatch, tmp_path)
    exc = captured_exception(
        lambda: cookiecutter(
            str(template),
            no_input=True,
            config_file=str(tmp_path / "missing.yml"),
            output_dir=str(tmp_path / "out"),
        )
    )
    assert isinstance(exc, ConfigDoesNotExistException)
    assert "missing.yml" in str(exc)


def test_replay_and_no_input_raise_invalid_mode(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    isolate_home(monkeypatch, tmp_path)
    exc = captured_exception(
        lambda: cookiecutter(
            str(template), replay=True, no_input=True, output_dir=str(tmp_path / "out")
        )
    )
    assert isinstance(exc, InvalidModeException)
    assert "replay" in str(exc).lower() or "no_input" in str(exc).lower()


def test_unknown_extension_raises_unknown_extension(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "demo", "_extensions": ["missing_module.MissingExtension"]},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    isolate_home(monkeypatch, tmp_path)
    exc = captured_exception(
        lambda: cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))
    )
    assert isinstance(exc, UnknownExtension)
    assert "MissingExtension" in str(exc)


def test_missing_local_template_raises_repository_not_found(tmp_path, monkeypatch):
    isolate_home(monkeypatch, tmp_path)
    exc = captured_exception(
        lambda: cookiecutter(
            str(tmp_path / "not-there"), no_input=True, output_dir=str(tmp_path / "out")
        )
    )
    assert isinstance(exc, RepositoryNotFound)
    assert "not-there" in str(exc)


def test_template_without_templated_project_dir_raises_public_exception(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "demo"},
        {"plain/file.txt": "ok"},
    )
    isolate_home(monkeypatch, tmp_path)
    exc = captured_exception(
        lambda: cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))
    )
    assert isinstance(exc, NonTemplatedInputDirException)
    assert "templated" in str(exc).lower() or "project dir" in str(exc).lower()


def test_undefined_content_variable_raises_public_exception(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "{{ cookiecutter.missing }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    exc = captured_exception(
        lambda: cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "out"))
    )
    assert isinstance(exc, UndefinedVariableInTemplate)
    assert "missing" in str(exc).lower()


def test_empty_string_default_renders_as_empty_content(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "empty_string", "description": ""},
        {"{{cookiecutter.project_slug}}/description.txt": "{{ cookiecutter.description }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "description.txt").read_text(encoding="utf-8") == ""

def test_nested_dictionary_default_is_available_to_template(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "nested_dict",
            "metadata": {"team": {"lead": "Ada", "size": "3"}},
        },
        {
            "{{cookiecutter.project_slug}}/team.txt":
            "{{ cookiecutter.metadata.team.lead }}|{{ cookiecutter.metadata.team.size }}"
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "team.txt").read_text(encoding="utf-8") == "Ada|3"

def test_private_dictionary_value_is_preserved_and_accessible(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "private_dict",
            "_metadata": {"owner": "{{ cookiecutter.project_slug }}"},
        },
        {"{{cookiecutter.project_slug}}/owner.txt": "{{ cookiecutter._metadata.owner }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "owner.txt").read_text(encoding="utf-8") == "{{ cookiecutter.project_slug }}"

def test_templated_defaults_can_chain_in_key_order(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {
            "project_name": "My App",
            "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}",
            "package_name": "{{ cookiecutter.project_slug }}_package",
        },
        {"{{cookiecutter.project_slug}}/package.txt": "{{ cookiecutter.package_name }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert result.name == "my_app"
    assert (result / "package.txt").read_text(encoding="utf-8") == "my_app_package"

def test_jsonify_default_indent_is_four_spaces(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "json_default_indent", "metadata": {"owner": "Ada"}},
        {"{{cookiecutter.project_slug}}/data.json": "{{ cookiecutter.metadata | jsonify }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    rendered = (result / "data.json").read_text(encoding="utf-8")
    assert '\n    "owner": "Ada"' in rendered

def test_slugify_filter_accepts_separator_keyword(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "slug_separator"},
        {"{{cookiecutter.project_slug}}/slug.txt": "{{ 'Hello Friendly World' | slugify(separator='_') }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "slug.txt").read_text(encoding="utf-8") == "hello_friendly_world"

def test_slugify_filter_handles_apostrophes(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "slug_apostrophe"},
        {"{{cookiecutter.project_slug}}/slug.txt": "{{ \"John's Project\" | slugify }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    slug = (result / "slug.txt").read_text(encoding="utf-8")
    assert "'" not in slug
    assert " " not in slug
    assert slug == slug.lower()
    assert slug.replace("-", "").isalnum()

def test_time_tag_formats_current_utc_month(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "time_month"},
        {"{{cookiecutter.project_slug}}/month.txt": "{% now 'utc', '%Y-%m' %}"},
    )
    before = datetime.now(timezone.utc).strftime("%Y-%m")
    result = generated_path(tmp_path, monkeypatch, template)
    after = datetime.now(timezone.utc).strftime("%Y-%m")
    assert (result / "month.txt").read_text(encoding="utf-8") in {before, after}

def test_time_tag_formats_current_utc_hour(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "time_hour"},
        {"{{cookiecutter.project_slug}}/hour.txt": "{% now 'utc', '%H' %}"},
    )
    before = datetime.now(timezone.utc).strftime("%H")
    result = generated_path(tmp_path, monkeypatch, template)
    after = datetime.now(timezone.utc).strftime("%H")
    assert (result / "hour.txt").read_text(encoding="utf-8") in {before, after}

def test_multiple_uuid_calls_each_produce_uuid4_strings(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "uuid_pair"},
        {"{{cookiecutter.project_slug}}/uuids.txt": "{{ uuid4() }}|{{ uuid4() }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    first, second = (result / "uuids.txt").read_text(encoding="utf-8").split("|")
    assert uuid.UUID(first).version == 4
    assert uuid.UUID(second).version == 4
