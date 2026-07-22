# Spec2Repo oracle - integration tests for cookiecutter-fullrepro-001
import base64
import json
import os
import string
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from cookiecutter.main import cookiecutter


def make_template(root: Path, config: dict, files: dict[str, str | bytes], hooks=None) -> Path:
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
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("COOKIECUTTER_CONFIG", raising=False)
    return home


def generated_path(tmp_path: Path, monkeypatch, template: Path, **kwargs) -> Path:
    isolate_home(monkeypatch, tmp_path)
    output = tmp_path / "output"
    return Path(cookiecutter(str(template), no_input=True, output_dir=str(output), **kwargs))


def exception_name(callable_):
    try:
        callable_()
    except Exception as exc:
        return type(exc).__name__
    raise AssertionError("expected an exception")


def write_config(path: Path, replay_dir: Path, default_context=None) -> Path:
    data = {
        "cookiecutters_dir": str(path.parent / "cookiecutters"),
        "replay_dir": str(replay_dir),
        "default_context": default_context or {},
        "abbreviations": {},
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def make_archive(source: Path, archive: Path, top_name="template") -> Path:
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"{top_name}/", "")
        for path in source.rglob("*"):
            relative = path.relative_to(source).as_posix()
            if path.is_dir():
                zf.writestr(f"{top_name}/{relative}/", "")
            else:
                zf.write(path, f"{top_name}/{relative}")
    return archive


def run_cli(
    tmp_path: Path,
    template: Path,
    *args: str,
    extra_context=(),
    input_text=None,
):
    home = tmp_path / "cli-home"
    home.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env.pop("COOKIECUTTER_CONFIG", None)
    return subprocess.run(
        [sys.executable, "-m", "cookiecutter", *args, str(template), *extra_context],
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
        timeout=30,
    )


def file_tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


# Integration and system workflows: multiple public projections or lifecycle stages.


def test_local_extension_can_register_a_filter(tmp_path, monkeypatch):
    extension = """from jinja2.ext import Extension

class ShoutExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.filters['shout'] = lambda value: str(value).upper() + '!'
"""
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "filter_extension",
            "_extensions": ["local_filter_extension.ShoutExtension"],
        },
        {
            "local_filter_extension.py": extension,
            "{{cookiecutter.project_slug}}/value.txt": "{{ 'hello' | shout }}",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "value.txt").read_text(encoding="utf-8") == "HELLO!"


def test_local_extension_can_register_a_global(tmp_path, monkeypatch):
    extension = """from jinja2.ext import Extension

class LabelExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals['project_label'] = lambda: 'local-global'
"""
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "global_extension",
            "_extensions": ["local_global_extension.LabelExtension"],
        },
        {
            "local_global_extension.py": extension,
            "{{cookiecutter.project_slug}}/value.txt": "{{ project_label() }}",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "value.txt").read_text(encoding="utf-8") == "local-global"


def test_local_extension_can_register_a_tag(tmp_path, monkeypatch):
    extension = """from jinja2 import nodes
from jinja2.ext import Extension

class WrapExtension(Extension):
    tags = {'wrap'}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(['name:endwrap'], drop_needle=True)
        return nodes.CallBlock(self.call_method('_wrap'), [], [], body).set_lineno(lineno)

    def _wrap(self, caller):
        return '[' + caller() + ']'
"""
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "tag_extension",
            "_extensions": ["local_tag_extension.WrapExtension"],
        },
        {
            "local_tag_extension.py": extension,
            "{{cookiecutter.project_slug}}/value.txt": "{% wrap %}inside{% endwrap %}",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "value.txt").read_text(encoding="utf-8") == "[inside]"


def test_human_readable_prompt_label_is_displayed_and_answer_is_used(tmp_path):
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "prompt_demo",
            "owner": "Ada",
            "__prompts__": {"owner": "Project Owner"},
        },
        {"{{cookiecutter.project_slug}}/owner.txt": "{{ cookiecutter.owner }}"},
    )
    output = tmp_path / "output"
    home = tmp_path / "prompt-home"
    home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home)
    env.pop("COOKIECUTTER_CONFIG", None)
    result = subprocess.run(
        [sys.executable, "-m", "cookiecutter", "-o", str(output), str(template)],
        input="\nGrace\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Project Owner" in result.stdout + result.stderr
    assert (output / "prompt_demo" / "owner.txt").read_text(encoding="utf-8") == "Grace"


ENCRYPTED_TEMPLATE_ZIP = base64.b64decode(
    "UEsDBAoAAAAAANoN7lwAAAAAAAAAAAAAAAAfABwAY29va2llY3V0dGVyLWVuY3J5cHRlZC1maXh0dXJlL1VUCQADiyRVapYkVWp1eAsAAQToAwAABOgDAABQSwMECgAJAAAA2g3uXPsF8MUvAAAAIwAAADAAHABjb29raWVjdXR0ZXItZW5jcnlwdGVkLWZpeHR1cmUvY29va2llY3V0dGVyLmpzb25VVAkAA4skVWqLJFVqdXgLAAEE6AMAAAToAwAAASWYhZ9rSROLhil0uNwuTwE6/B6QoF3AUrOWMZGdg8QVId+RrxWcYCTfSdUsMxpQSwcI+wXwxS8AAAAjAAAAUEsDBAoAAAAAANoN7lwAAAAAAAAAAAAAAAA9ABwAY29va2llY3V0dGVyLWVuY3J5cHRlZC1maXh0dXJlL3t7Y29va2llY3V0dGVyLnByb2plY3Rfc2x1Z319L1VUCQADiyRVapYkVWp1eAsAAQToAwAABOgDAABQSwMECgAJAAAA2g3uXOzErLUsAAAAIAAAAEcAHABjb29raWVjdXR0ZXItZW5jcnlwdGVkLWZpeHR1cmUve3tjb29raWVjdXR0ZXIucHJvamVjdF9zbHVnfX0vc2VjcmV0LnR4dFVUCQADiyRVaoskVWp1eAsAAQToAwAABOgDAAAmkcOPBiBbWWT+Rs3NRdS2dvsNfMcMbbDLyXmFFFDS4PaucEoX/aCGpsfsDVBLBwjsxKy1LAAAACAAAABQSwECHgMKAAAAAADaDe5cAAAAAAAAAAAAAAAAHwAYAAAAAAAAABAA/0EAAAAAY29va2llY3V0dGVyLWVuY3J5cHRlZC1maXh0dXJlL1VUBQADiyRVanV4CwABBOgDAAAE6AMAAFBLAQIeAwoACQAAANoN7lz7BfDFLwAAACMAAAAwABgAAAAAAAEAAAD/gVkAAABjb29raWVjdXR0ZXItZW5jcnlwdGVkLWZpeHR1cmUvY29va2llY3V0dGVyLmpzb25VVAUAA4skVWp1eAsAAQToAwAABOgDAABQSwECHgMKAAAAAADaDe5cAAAAAAAAAAAAAAAAPQAYAAAAAAAAABAA/0ECAQAAY29va2llY3V0dGVyLWVuY3J5cHRlZC1maXh0dXJlL3t7Y29va2llY3V0dGVyLnByb2plY3Rfc2x1Z319L1VUBQADiyRVanV4CwABBOgDAAAE6AMAAFBLAQIeAwoACQAAANoN7lzsxKy1LAAAACAAAABHABgAAAAAAAEAAAD/gXkBAABjb29raWVjdXR0ZXItZW5jcnlwdGVkLWZpeHR1cmUve3tjb29raWVjdXR0ZXIucHJvamVjdF9zbHVnfX0vc2VjcmV0LnR4dFVUBQADiyRVanV4CwABBOgDAAAE6AMAAFBLBQYAAAAABAAEAOsBAAA2AgAAAAA="
)


def encrypted_template_path(tmp_path: Path) -> Path:
    archive = tmp_path / "encrypted-template.zip"
    archive.write_bytes(ENCRYPTED_TEMPLATE_ZIP)
    return archive


def test_password_argument_opens_a_protected_zip_template(tmp_path, monkeypatch):
    isolate_home(monkeypatch, tmp_path)
    result = Path(
        cookiecutter(
            str(encrypted_template_path(tmp_path)),
            no_input=True,
            password="s3cret",
            output_dir=str(tmp_path / "output"),
        )
    )
    assert (result / "secret.txt").read_text(encoding="utf-8") == "encrypted_demo\n"


def test_cli_password_environment_opens_a_protected_zip_template(tmp_path, monkeypatch):
    monkeypatch.setenv("COOKIECUTTER_REPO_PASSWORD", "s3cret")
    archive = encrypted_template_path(tmp_path)
    result = run_cli(tmp_path, archive, "--no-input", "-o", str(tmp_path / "output"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "output" / "encrypted_demo" / "secret.txt").is_file()


def test_wrong_password_for_protected_zip_raises_invalid_zip_repository(tmp_path, monkeypatch):
    isolate_home(monkeypatch, tmp_path)
    name = exception_name(
        lambda: cookiecutter(
            str(encrypted_template_path(tmp_path)),
            no_input=True,
            password="wrong-password",
            output_dir=str(tmp_path / "output"),
        )
    )
    assert name == "InvalidZipRepository"


def test_nested_directory_and_file_names_render_with_contents(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "nested_demo", "package": "core"},
        {
            "{{cookiecutter.project_slug}}/src/{{cookiecutter.package}}/{{cookiecutter.package}}.txt":
            "package={{ cookiecutter.package }}"
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    path = result / "src" / "core" / "core.txt"
    assert path.read_text(encoding="utf-8") == "package=core"


def test_multiple_files_share_the_same_resolved_context(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "multi_demo", "owner": "Ada"},
        {
            "{{cookiecutter.project_slug}}/one.txt": "{{ cookiecutter.owner }}",
            "{{cookiecutter.project_slug}}/two.txt": "{{ cookiecutter.owner }}",
            "{{cookiecutter.project_slug}}/nested/three.txt": "{{ cookiecutter.owner }}",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert [
        (result / "one.txt").read_text(encoding="utf-8"),
        (result / "two.txt").read_text(encoding="utf-8"),
        (result / "nested" / "three.txt").read_text(encoding="utf-8"),
    ] == ["Ada", "Ada", "Ada"]


def test_utf8_context_round_trips_through_names_and_contents(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "unicode_demo", "greeting": "浣犲ソ"},
        {"{{cookiecutter.project_slug}}/{{cookiecutter.greeting}}.txt": "{{ cookiecutter.greeting }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "浣犲ソ.txt").read_text(encoding="utf-8") == "浣犲ソ"


def test_copy_without_render_preserves_matching_file_contents(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "raw_demo", "_copy_without_render": ["raw/*"]},
        {
            "{{cookiecutter.project_slug}}/raw/source.txt": "{{ cookiecutter.project_slug }}",
            "{{cookiecutter.project_slug}}/normal.txt": "{{ cookiecutter.project_slug }}",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "raw" / "source.txt").read_text(encoding="utf-8") == "{{ cookiecutter.project_slug }}"
    assert (result / "normal.txt").read_text(encoding="utf-8") == "raw_demo"


def test_copy_without_render_still_renders_matching_path_names(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "raw_path", "name": "rendered", "_copy_without_render": ["raw/*"]},
        {"{{cookiecutter.project_slug}}/raw/{{cookiecutter.name}}.txt": "{{ cookiecutter.name }}"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "raw" / "rendered.txt").read_text(encoding="utf-8") == "{{ cookiecutter.name }}"


def test_output_dir_contains_the_returned_project(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "placed_demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    isolate_home(monkeypatch, tmp_path)
    output = tmp_path / "custom" / "destination"
    result = Path(cookiecutter(str(template), no_input=True, output_dir=str(output)))
    assert result == output.resolve() / "placed_demo"
    assert (result / "file.txt").is_file()


def test_existing_output_directory_raises_without_overwrite(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "existing_demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "template"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert result.is_dir()
    name = exception_name(
        lambda: cookiecutter(
            str(template), no_input=True, output_dir=str(tmp_path / "output")
        )
    )
    assert name == "OutputDirExistsException"


def test_overwrite_if_exists_replaces_existing_file_contents(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "overwrite_demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "template"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    (result / "file.txt").write_text("user", encoding="utf-8")
    cookiecutter(
        str(template),
        no_input=True,
        overwrite_if_exists=True,
        output_dir=str(tmp_path / "output"),
    )
    assert (result / "file.txt").read_text(encoding="utf-8") == "template"


def test_skip_if_file_exists_preserves_existing_file_contents(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "skip_demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "template"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    (result / "file.txt").write_text("user", encoding="utf-8")
    cookiecutter(
        str(template),
        no_input=True,
        overwrite_if_exists=True,
        skip_if_file_exists=True,
        output_dir=str(tmp_path / "output"),
    )
    assert (result / "file.txt").read_text(encoding="utf-8") == "user"


def test_skip_if_file_exists_still_generates_missing_files(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "skip_missing"},
        {
            "{{cookiecutter.project_slug}}/existing.txt": "template-existing",
            "{{cookiecutter.project_slug}}/missing.txt": "template-missing",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    (result / "existing.txt").write_text("user", encoding="utf-8")
    (result / "missing.txt").unlink()
    cookiecutter(
        str(template),
        no_input=True,
        overwrite_if_exists=True,
        skip_if_file_exists=True,
        output_dir=str(tmp_path / "output"),
    )
    assert (result / "existing.txt").read_text(encoding="utf-8") == "user"
    assert (result / "missing.txt").read_text(encoding="utf-8") == "template-missing"


def test_binary_file_is_copied_without_template_rendering(tmp_path, monkeypatch):
    binary = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00{{ cookiecutter.project_slug }}\xff"
    template = make_template(
        tmp_path / "template",
        {"project_slug": "binary_demo"},
        {"{{cookiecutter.project_slug}}/image.png": binary},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "image.png").read_bytes() == binary


def test_pre_generation_hook_receives_rendered_context(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "pre_hook"},
        {"{{cookiecutter.project_slug}}/file.txt": "body"},
        {"pre_gen_project.py": "from pathlib import Path\nPath('pre.txt').write_text('{{ cookiecutter.project_slug }}', encoding='utf-8')\n"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "pre.txt").read_text(encoding="utf-8") == "pre_hook"


def test_post_generation_hook_can_read_generated_files(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "post_hook"},
        {"{{cookiecutter.project_slug}}/file.txt": "body"},
        {"post_gen_project.py": "from pathlib import Path\nPath('post.txt').write_text(Path('file.txt').read_text() + '-post', encoding='utf-8')\n"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "post.txt").read_text(encoding="utf-8") == "body-post"


def test_accept_hooks_false_skips_pre_and_post_hooks(tmp_path, monkeypatch):
    marker_hook = "from pathlib import Path\nPath('{{ cookiecutter.project_slug }}.marker').write_text('ran', encoding='utf-8')\n"
    template = make_template(
        tmp_path / "template",
        {"project_slug": "hooks_off"},
        {"{{cookiecutter.project_slug}}/file.txt": "body"},
        {"pre_gen_project.py": marker_hook, "post_gen_project.py": marker_hook},
    )
    result = generated_path(tmp_path, monkeypatch, template, accept_hooks=False)
    assert (result / "file.txt").is_file()
    assert not (result / "hooks_off.marker").exists()


def test_failed_hook_removes_partial_project_by_default(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "failed_hook"},
        {"{{cookiecutter.project_slug}}/file.txt": "body"},
        {"post_gen_project.py": "raise SystemExit(3)\n"},
    )
    isolate_home(monkeypatch, tmp_path)
    output = tmp_path / "output"
    name = exception_name(
        lambda: cookiecutter(str(template), no_input=True, output_dir=str(output))
    )
    assert name == "FailedHookException"
    assert not (output / "failed_hook").exists()


def test_keep_project_on_failure_preserves_partial_project(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "kept_hook"},
        {"{{cookiecutter.project_slug}}/file.txt": "body"},
        {"post_gen_project.py": "raise SystemExit(4)\n"},
    )
    isolate_home(monkeypatch, tmp_path)
    output = tmp_path / "output"
    name = exception_name(
        lambda: cookiecutter(
            str(template),
            no_input=True,
            keep_project_on_failure=True,
            output_dir=str(output),
        )
    )
    assert name == "FailedHookException"
    assert (output / "kept_hook" / "file.txt").read_text(encoding="utf-8") == "body"


def test_pre_and_post_hooks_run_in_documented_order(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "hook_order"},
        {"{{cookiecutter.project_slug}}/body.txt": "generated"},
        {
            "pre_gen_project.py": "from pathlib import Path\nPath('order.txt').write_text('pre', encoding='utf-8')\n",
            "post_gen_project.py": "from pathlib import Path\np=Path('order.txt'); p.write_text(p.read_text() + '-post-' + Path('body.txt').read_text(), encoding='utf-8')\n",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "order.txt").read_text(encoding="utf-8") == "pre-post-generated"


def test_directory_option_selects_the_named_template(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    make_template(
        repo / "first",
        {"project_slug": "first"},
        {"{{cookiecutter.project_slug}}/which.txt": "first"},
    )
    make_template(
        repo / "second",
        {"project_slug": "second"},
        {"{{cookiecutter.project_slug}}/which.txt": "second"},
    )
    isolate_home(monkeypatch, tmp_path)
    result = Path(
        cookiecutter(
            str(repo), no_input=True, directory="second", output_dir=str(tmp_path / "output")
        )
    )
    assert result.name == "second"
    assert (result / "which.txt").read_text(encoding="utf-8") == "second"


def test_directory_option_preserves_rendering_behavior(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    make_template(
        repo / "nested",
        {"project_slug": "nested_default", "owner": "Ada"},
        {"{{cookiecutter.project_slug}}/{{cookiecutter.owner}}.txt": "{{ cookiecutter.owner }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    result = Path(
        cookiecutter(
            str(repo),
            no_input=True,
            directory="nested",
            extra_context={"project_slug": "selected", "owner": "Grace"},
            output_dir=str(tmp_path / "output"),
        )
    )
    assert (result / "Grace.txt").read_text(encoding="utf-8") == "Grace"


def test_local_zip_archive_generates_a_project(tmp_path, monkeypatch):
    source = make_template(
        tmp_path / "source",
        {"project_slug": "zip_demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "zip"},
    )
    archive = make_archive(source, tmp_path / "template.zip")
    isolate_home(monkeypatch, tmp_path)
    result = Path(cookiecutter(str(archive), no_input=True, output_dir=str(tmp_path / "output")))
    assert (result / "file.txt").read_text(encoding="utf-8") == "zip"


def test_zip_archive_uses_context_for_names_and_contents(tmp_path, monkeypatch):
    source = make_template(
        tmp_path / "source",
        {"project_slug": "zip_default", "owner": "Ada"},
        {"{{cookiecutter.project_slug}}/{{cookiecutter.owner}}.txt": "{{ cookiecutter.owner }}"},
    )
    archive = make_archive(source, tmp_path / "template.zip")
    isolate_home(monkeypatch, tmp_path)
    result = Path(
        cookiecutter(
            str(archive),
            no_input=True,
            extra_context={"project_slug": "zip_override", "owner": "Grace"},
            output_dir=str(tmp_path / "output"),
        )
    )
    assert result.name == "zip_override"
    assert (result / "Grace.txt").read_text(encoding="utf-8") == "Grace"


def test_user_config_default_context_overrides_template_defaults(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "template_default", "color": "blue"},
        {"{{cookiecutter.project_slug}}/color.txt": "{{ cookiecutter.color }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    config = write_config(
        tmp_path / "config.yml",
        tmp_path / "replays",
        {"project_slug": "configured", "color": "green"},
    )
    result = Path(
        cookiecutter(
            str(template), no_input=True, config_file=str(config), output_dir=str(tmp_path / "output")
        )
    )
    assert result.name == "configured"
    assert (result / "color.txt").read_text(encoding="utf-8") == "green"


def test_extra_context_has_precedence_over_user_config(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "template_default", "color": "blue"},
        {"{{cookiecutter.project_slug}}/color.txt": "{{ cookiecutter.color }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    config = write_config(
        tmp_path / "config.yml", tmp_path / "replays", {"project_slug": "configured", "color": "green"}
    )
    result = Path(
        cookiecutter(
            str(template),
            no_input=True,
            config_file=str(config),
            extra_context={"project_slug": "extra", "color": "red"},
            output_dir=str(tmp_path / "output"),
        )
    )
    assert result.name == "extra"
    assert (result / "color.txt").read_text(encoding="utf-8") == "red"


def test_successful_generation_saves_resolved_context_to_replay(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "replay_demo", "color": "blue"},
        {"{{cookiecutter.project_slug}}/color.txt": "{{ cookiecutter.color }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    replay_dir = tmp_path / "replays"
    config = write_config(tmp_path / "config.yml", replay_dir)
    cookiecutter(
        str(template),
        no_input=True,
        config_file=str(config),
        extra_context={"color": "red"},
        output_dir=str(tmp_path / "output"),
    )
    saved = json.loads((replay_dir / "template.json").read_text(encoding="utf-8"))
    assert saved["cookiecutter"]["project_slug"] == "replay_demo"
    assert saved["cookiecutter"]["color"] == "red"


def test_replay_true_reuses_the_last_saved_context(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "default", "color": "blue"},
        {"{{cookiecutter.project_slug}}/color.txt": "{{ cookiecutter.color }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    config = write_config(tmp_path / "config.yml", tmp_path / "replays")
    cookiecutter(
        str(template),
        no_input=True,
        config_file=str(config),
        extra_context={"project_slug": "recorded", "color": "red"},
        output_dir=str(tmp_path / "first"),
    )
    result = Path(
        cookiecutter(
            str(template), replay=True, config_file=str(config), output_dir=str(tmp_path / "second")
        )
    )
    assert result.name == "recorded"
    assert (result / "color.txt").read_text(encoding="utf-8") == "red"


def test_explicit_replay_file_controls_the_generated_context(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "default", "color": "blue"},
        {"{{cookiecutter.project_slug}}/color.txt": "{{ cookiecutter.color }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    replay = tmp_path / "explicit.json"
    replay.write_text(
        json.dumps({"cookiecutter": {"project_slug": "explicit", "color": "purple"}}),
        encoding="utf-8",
    )
    result = Path(
        cookiecutter(str(template), replay=str(replay), output_dir=str(tmp_path / "output"))
    )
    assert result.name == "explicit"
    assert (result / "color.txt").read_text(encoding="utf-8") == "purple"


def test_default_config_ignores_a_user_cookiecutterrc(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "built_in_default"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    home = isolate_home(monkeypatch, tmp_path)
    write_config(home / ".cookiecutterrc", tmp_path / "unexpected-replays", {"project_slug": "user_value"})
    result = Path(
        cookiecutter(
            str(template), no_input=True, default_config=True, output_dir=str(tmp_path / "output")
        )
    )
    assert result.name == "built_in_default"


def test_cli_no_input_generates_a_local_template(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "cli_demo"},
        {"{{cookiecutter.project_slug}}/file.txt": "cli"},
    )
    output = tmp_path / "output"
    result = run_cli(tmp_path, template, "--no-input", "--output-dir", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "cli_demo" / "file.txt").read_text(encoding="utf-8") == "cli"


def test_cli_extra_context_overrides_template_values(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "default", "color": "blue"},
        {"{{cookiecutter.project_slug}}/color.txt": "{{ cookiecutter.color }}"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "--no-input",
        "--output-dir",
        str(output),
        extra_context=("project_slug=cli_override", "color=orange"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "cli_override" / "color.txt").read_text(encoding="utf-8") == "orange"


def test_cli_output_dir_places_project_under_requested_path(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "cli_output"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    output = tmp_path / "deep" / "output"
    result = run_cli(tmp_path, template, "--no-input", "-o", str(output))
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "cli_output" / "file.txt").is_file()


def test_cli_skip_if_file_exists_preserves_user_content(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "cli_skip"},
        {"{{cookiecutter.project_slug}}/file.txt": "template"},
    )
    output = tmp_path / "output"
    first = run_cli(tmp_path, template, "--no-input", "-o", str(output))
    assert first.returncode == 0, first.stdout + first.stderr
    target = output / "cli_skip" / "file.txt"
    target.write_text("user", encoding="utf-8")
    second = run_cli(
        tmp_path,
        template,
        "--no-input",
        "--overwrite-if-exists",
        "--skip-if-file-exists",
        "-o",
        str(output),
    )
    assert second.returncode == 0, second.stdout + second.stderr
    assert target.read_text(encoding="utf-8") == "user"


def test_cli_overwrite_if_exists_replaces_user_content(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "cli_overwrite"},
        {"{{cookiecutter.project_slug}}/file.txt": "template"},
    )
    output = tmp_path / "output"
    first = run_cli(tmp_path, template, "--no-input", "-o", str(output))
    assert first.returncode == 0, first.stdout + first.stderr
    target = output / "cli_overwrite" / "file.txt"
    target.write_text("user", encoding="utf-8")
    second = run_cli(tmp_path, template, "--no-input", "--overwrite-if-exists", "-o", str(output))
    assert second.returncode == 0, second.stdout + second.stderr
    assert target.read_text(encoding="utf-8") == "template"


def test_cli_and_python_api_produce_identical_file_trees(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "same_tree", "owner": "Ada"},
        {
            "{{cookiecutter.project_slug}}/{{cookiecutter.owner}}.txt": "{{ cookiecutter.owner }}",
            "{{cookiecutter.project_slug}}/nested/value.txt": "{{ cookiecutter.project_slug }}",
        },
    )
    isolate_home(monkeypatch, tmp_path)
    api_root = Path(
        cookiecutter(str(template), no_input=True, output_dir=str(tmp_path / "api-output"))
    )
    cli_result = run_cli(tmp_path, template, "--no-input", "-o", str(tmp_path / "cli-output"))
    assert cli_result.returncode == 0, cli_result.stdout + cli_result.stderr
    cli_root = tmp_path / "cli-output" / "same_tree"
    assert file_tree(api_root) == file_tree(cli_root)


def test_context_is_consistent_across_name_content_and_replay(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "default", "owner": "Ada"},
        {"{{cookiecutter.project_slug}}/{{cookiecutter.owner}}.txt": "{{ cookiecutter.project_slug }}|{{ cookiecutter.owner }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    replay_dir = tmp_path / "replays"
    config = write_config(tmp_path / "config.yml", replay_dir)
    result = Path(
        cookiecutter(
            str(template),
            no_input=True,
            config_file=str(config),
            extra_context={"project_slug": "consistent", "owner": "Grace"},
            output_dir=str(tmp_path / "output"),
        )
    )
    saved = json.loads((replay_dir / "template.json").read_text(encoding="utf-8"))
    assert result.name == "consistent"
    assert (result / "Grace.txt").read_text(encoding="utf-8") == "consistent|Grace"
    assert saved["cookiecutter"]["project_slug"] == "consistent"
    assert saved["cookiecutter"]["owner"] == "Grace"


def test_cli_verbose_emits_debug_logging_while_generation_succeeds(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "verbose_cli"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    result = run_cli(
        tmp_path,
        template,
        "--no-input",
        "--verbose",
        "-o",
        str(tmp_path / "output"),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DEBUG" in result.stdout + result.stderr
    assert (tmp_path / "output" / "verbose_cli" / "file.txt").is_file()


def test_directory_selection_keeps_hook_and_replay_context_consistent(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    make_template(
        repo / "nested",
        {"project_slug": "nested_default", "owner": "Ada"},
        {"{{cookiecutter.project_slug}}/owner.txt": "{{ cookiecutter.owner }}"},
        {"post_gen_project.py": "from pathlib import Path\nPath('hook.txt').write_text('{{ cookiecutter.owner }}', encoding='utf-8')\n"},
    )
    isolate_home(monkeypatch, tmp_path)
    replay_dir = tmp_path / "replays"
    config = write_config(tmp_path / "config.yml", replay_dir)
    result = Path(
        cookiecutter(
            str(repo),
            no_input=True,
            directory="nested",
            config_file=str(config),
            extra_context={"project_slug": "selected", "owner": "Grace"},
            output_dir=str(tmp_path / "output"),
        )
    )
    saved = json.loads((replay_dir / "nested.json").read_text(encoding="utf-8"))
    assert (result / "owner.txt").read_text(encoding="utf-8") == "Grace"
    assert (result / "hook.txt").read_text(encoding="utf-8") == "Grace"
    assert saved["cookiecutter"]["owner"] == "Grace"


def test_legacy_template_key_selects_its_nested_template(tmp_path, monkeypatch):
    repo = make_template(
        tmp_path / "repo",
        {"template": ["Old Template (./old)"]},
        {},
    )
    make_template(
        repo / "old",
        {"project_slug": "legacy_nested"},
        {"{{cookiecutter.project_slug}}/file.txt": "legacy"},
    )
    isolate_home(monkeypatch, tmp_path)
    result = Path(cookiecutter(str(repo), no_input=True, output_dir=str(tmp_path / "output")))
    assert result.name == "legacy_nested"
    assert (result / "file.txt").read_text(encoding="utf-8") == "legacy"


def test_templates_mapping_selects_the_first_nested_template_without_input(tmp_path, monkeypatch):
    repo = make_template(
        tmp_path / "repo",
        {
            "templates": {
                "one": {"path": "one", "title": "First", "description": "First template"},
                "two": {"path": "two", "title": "Second", "description": "Second template"},
            }
        },
        {},
    )
    make_template(
        repo / "one",
        {"project_slug": "first_nested"},
        {"{{cookiecutter.project_slug}}/file.txt": "first"},
    )
    make_template(
        repo / "two",
        {"project_slug": "second_nested"},
        {"{{cookiecutter.project_slug}}/file.txt": "second"},
    )
    isolate_home(monkeypatch, tmp_path)
    result = Path(cookiecutter(str(repo), no_input=True, output_dir=str(tmp_path / "output")))
    assert result.name == "first_nested"
    assert (result / "file.txt").read_text(encoding="utf-8") == "first"


def test_directory_option_selects_a_template_inside_a_zip_archive(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    make_template(
        repo / "nested",
        {"project_slug": "zip_nested"},
        {"{{cookiecutter.project_slug}}/file.txt": "nested zip"},
    )
    archive = make_archive(repo, tmp_path / "templates.zip")
    isolate_home(monkeypatch, tmp_path)
    result = Path(
        cookiecutter(
            str(archive),
            no_input=True,
            directory="nested",
            output_dir=str(tmp_path / "output"),
        )
    )
    assert result.name == "zip_nested"
    assert (result / "file.txt").read_text(encoding="utf-8") == "nested zip"


# Per-heading quota repairs.


def test_interactive_string_answer_preserves_spaces(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "string_answer", "title": "Default"},
        {"{{cookiecutter.project_slug}}/title.txt": "{{ cookiecutter.title }}"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "-o",
        str(output),
        input_text="\nA title with spaces\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "string_answer" / "title.txt").read_text(encoding="utf-8") == "A title with spaces"


def test_user_config_matching_choice_becomes_no_input_default(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "choice_config", "license": ["MIT", "BSD-3"]},
        {"{{cookiecutter.project_slug}}/license.txt": "{{ cookiecutter.license }}"},
    )
    isolate_home(monkeypatch, tmp_path)
    config = write_config(
        tmp_path / "config.yml",
        tmp_path / "replays",
        {"license": "BSD-3"},
    )
    result = Path(
        cookiecutter(
            str(template),
            no_input=True,
            config_file=str(config),
            output_dir=str(tmp_path / "output"),
        )
    )
    assert (result / "license.txt").read_text(encoding="utf-8") == "BSD-3"


def test_interactive_choice_number_selects_corresponding_value(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "choice_answer", "license": ["MIT", "BSD-3"]},
        {"{{cookiecutter.project_slug}}/license.txt": "{{ cookiecutter.license }}"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "-o",
        str(output),
        input_text="\n2\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "choice_answer" / "license.txt").read_text(encoding="utf-8") == "BSD-3"


def test_interactive_boolean_yes_is_stored_as_true(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "boolean_answer", "enabled": False},
        {"{{cookiecutter.project_slug}}/enabled.txt": "{{ cookiecutter.enabled }}"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "-o",
        str(output),
        input_text="\nyes\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "boolean_answer" / "enabled.txt").read_text(encoding="utf-8") == "True"


def test_interactive_dictionary_json_replaces_default(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "dict_answer", "metadata": {"owner": "Ada"}},
        {"{{cookiecutter.project_slug}}/owner.txt": "{{ cookiecutter.metadata.owner }}"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "-o",
        str(output),
        input_text='\n{"owner":"Grace"}\n',
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "dict_answer" / "owner.txt").read_text(encoding="utf-8") == "Grace"


def test_private_variable_is_omitted_from_interactive_prompts(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "private_prompt", "_secret": "literal-value"},
        {"{{cookiecutter.project_slug}}/secret.txt": "{{ cookiecutter._secret }}"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "-o",
        str(output),
        input_text="\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "_secret" not in result.stdout
    assert (output / "private_prompt" / "secret.txt").read_text(encoding="utf-8") == "literal-value"


def test_private_rendered_variable_uses_extra_context(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "private_rendered",
            "owner": "Ada Lovelace",
            "__owner_slug": "{{ cookiecutter.owner.lower().replace(' ', '-') }}",
        },
        {"{{cookiecutter.project_slug}}/owner.txt": "{{ cookiecutter.__owner_slug }}"},
    )
    result = generated_path(
        tmp_path,
        monkeypatch,
        template,
        extra_context={"owner": "Grace Hopper"},
    )
    assert (result / "owner.txt").read_text(encoding="utf-8") == "grace-hopper"


def test_private_rendered_variable_drives_file_name(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "private_filename",
            "package": "Core Package",
            "__module": "{{ cookiecutter.package.lower().replace(' ', '_') }}",
        },
        {"{{cookiecutter.project_slug}}/{{cookiecutter.__module}}.txt": "module"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "core_package.txt").read_text(encoding="utf-8") == "module"


def test_custom_prompt_label_is_displayed(tmp_path):
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "prompt_label",
            "__prompts__": {"project_slug": "Friendly Project Name"},
        },
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    result = run_cli(
        tmp_path,
        template,
        "-o",
        str(tmp_path / "output"),
        input_text="\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Friendly Project Name" in result.stdout


def test_choice_prompt_uses_custom_item_labels(tmp_path):
    template = make_template(
        tmp_path / "template",
        {
            "project_slug": "choice_labels",
            "license": ["MIT", "BSD"],
            "__prompts__": {
                "license": {
                    "__prompt__": "Choose License",
                    "MIT": "Permissive MIT",
                    "BSD": "Permissive BSD",
                }
            },
        },
        {"{{cookiecutter.project_slug}}/license.txt": "{{ cookiecutter.license }}"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "-o",
        str(output),
        input_text="\n2\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Choose License" in result.stdout
    assert "Permissive MIT" in result.stdout
    assert "Permissive BSD" in result.stdout
    assert (output / "choice_labels" / "license.txt").read_text(encoding="utf-8") == "BSD"


def test_templated_default_recomputes_after_override(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {
            "project_name": "Default Name",
            "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '-') }}",
        },
        {"{{cookiecutter.project_slug}}/name.txt": "{{ cookiecutter.project_slug }}"},
    )
    result = generated_path(
        tmp_path,
        monkeypatch,
        template,
        extra_context={"project_name": "Changed Name"},
    )
    assert result.name == "changed-name"
    assert (result / "name.txt").read_text(encoding="utf-8") == "changed-name"


def test_copy_without_render_glob_preserves_all_matching_contents(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "copy_glob", "_copy_without_render": ["*.jinja"]},
        {
            "{{cookiecutter.project_slug}}/one.jinja": "{{ cookiecutter.project_slug }} one",
            "{{cookiecutter.project_slug}}/two.jinja": "{{ cookiecutter.project_slug }} two",
            "{{cookiecutter.project_slug}}/rendered.txt": "{{ cookiecutter.project_slug }}",
        },
    )
    result = generated_path(tmp_path, monkeypatch, template)
    assert (result / "one.jinja").read_text(encoding="utf-8") == "{{ cookiecutter.project_slug }} one"
    assert (result / "two.jinja").read_text(encoding="utf-8") == "{{ cookiecutter.project_slug }} two"
    assert (result / "rendered.txt").read_text(encoding="utf-8") == "copy_glob"


def test_templates_mapping_supports_deep_relative_path(tmp_path, monkeypatch):
    repo = make_template(
        tmp_path / "repo",
        {
            "templates": {
                "deep": {
                    "path": "catalog/deep",
                    "title": "Deep Template",
                    "description": "Nested relative path",
                }
            }
        },
        {},
    )
    make_template(
        repo / "catalog" / "deep",
        {"project_slug": "deep_nested"},
        {"{{cookiecutter.project_slug}}/file.txt": "deep"},
    )
    isolate_home(monkeypatch, tmp_path)
    result = Path(cookiecutter(str(repo), no_input=True, output_dir=str(tmp_path / "output")))
    assert result.name == "deep_nested"
    assert (result / "file.txt").read_text(encoding="utf-8") == "deep"


def test_interactive_templates_mapping_selects_second_entry(tmp_path):
    repo = make_template(
        tmp_path / "repo",
        {
            "templates": {
                "one": {"path": "one", "title": "First", "description": "First choice"},
                "two": {"path": "two", "title": "Second", "description": "Second choice"},
            }
        },
        {},
    )
    make_template(
        repo / "one",
        {"project_slug": "first_current"},
        {"{{cookiecutter.project_slug}}/file.txt": "first"},
    )
    make_template(
        repo / "two",
        {"project_slug": "second_current"},
        {"{{cookiecutter.project_slug}}/file.txt": "second"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        repo,
        "-o",
        str(output),
        input_text="2\n\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Second choice" in result.stdout
    assert (output / "second_current" / "file.txt").read_text(encoding="utf-8") == "second"


def test_legacy_template_list_defaults_to_first_entry(tmp_path, monkeypatch):
    repo = make_template(
        tmp_path / "repo",
        {"template": ["First (./one)", "Second (./two)"]},
        {},
    )
    make_template(
        repo / "one",
        {"project_slug": "first_legacy"},
        {"{{cookiecutter.project_slug}}/file.txt": "first"},
    )
    make_template(
        repo / "two",
        {"project_slug": "second_legacy"},
        {"{{cookiecutter.project_slug}}/file.txt": "second"},
    )
    isolate_home(monkeypatch, tmp_path)
    result = Path(cookiecutter(str(repo), no_input=True, output_dir=str(tmp_path / "output")))
    assert result.name == "first_legacy"
    assert (result / "file.txt").read_text(encoding="utf-8") == "first"


def test_interactive_legacy_template_list_selects_second_entry(tmp_path):
    repo = make_template(
        tmp_path / "repo",
        {"template": ["First (./one)", "Second (./two)"]},
        {},
    )
    make_template(
        repo / "one",
        {"project_slug": "first_legacy_cli"},
        {"{{cookiecutter.project_slug}}/file.txt": "first"},
    )
    make_template(
        repo / "two",
        {"project_slug": "second_legacy_cli"},
        {"{{cookiecutter.project_slug}}/file.txt": "second"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        repo,
        "-o",
        str(output),
        input_text="2\n\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (output / "second_legacy_cli" / "file.txt").read_text(encoding="utf-8") == "second"


def test_uuid_global_can_render_a_file_name(tmp_path, monkeypatch):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "uuid_filename"},
        {"{{cookiecutter.project_slug}}/{{ uuid4() }}.txt": "uuid file"},
    )
    result = generated_path(tmp_path, monkeypatch, template)
    files = list(result.glob("*.txt"))
    assert len(files) == 1
    assert uuid.UUID(files[0].stem).version == 4
    assert files[0].read_text(encoding="utf-8") == "uuid file"


def test_verbose_long_option_emits_debug_logging(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "verbose_long"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "--no-input",
        "--verbose",
        "-o",
        str(output),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DEBUG" in result.stdout
    assert (output / "verbose_long" / "file.txt").is_file()


def test_verbose_short_option_emits_debug_logging(tmp_path):
    template = make_template(
        tmp_path / "template",
        {"project_slug": "verbose_short"},
        {"{{cookiecutter.project_slug}}/file.txt": "ok"},
    )
    output = tmp_path / "output"
    result = run_cli(
        tmp_path,
        template,
        "--no-input",
        "-v",
        "-o",
        str(output),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DEBUG" in result.stdout
    assert (output / "verbose_short" / "file.txt").is_file()
