# Spec2Repo oracle - atomic tests for nikola-fullrepro-001

# Spec2Repo oracle - generated tests for nikola-fullrepro-001

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _ok(result):
    assert result in (0, None)


def _failed(result):
    assert result not in (0, None)


def _base_translation_config(pattern="{path}.{lang}.{ext}"):
    return {
        "TRANSLATIONS": {"en": "", "es": "/es", "pl": "/pl"},
        "DEFAULT_LANG": "en",
        "TRANSLATIONS_PATTERN": pattern,
    }


def _configured_site():
    from nikola import Nikola

    return Nikola(
        SITE_URL="https://example.invalid/blog/",
        TRANSLATIONS={"en": "", "es": "/es"},
        DEFAULT_LANG="en",
        INDEX_FILE="index.html",
        PRETTY_URLS=True,
    )


class _PluginFakeSite:
    def __init__(self):
        self.debug = False
        self.shortcodes = {}
        self.calls = []

    def register_shortcode(self, name, handler):
        self.calls.append((name, handler))
        self.shortcodes[name] = handler


@pytest.fixture(scope="module")
def local_site(tmp_path_factory):
    from nikola.__main__ import main

    root = tmp_path_factory.mktemp("nikola_site") / "site"
    _ok(main(["init", "--quiet", str(root)]))

    old = os.getcwd()
    os.chdir(root)
    try:
        _ok(main(["new_post", "-t", "Hello World", "--tags=alpha,beta"]))
        _ok(main(["new_page", "-t", "About Us"]))
        _ok(main(["build"]))
    finally:
        os.chdir(old)
    return root

def test_package_version_is_public_string():
    import nikola

    assert isinstance(nikola.__version__, str)
    assert nikola.__version__

def test_debug_flags_are_booleans():
    env = os.environ.copy()
    env.update(
        {
            "NIKOLA_DEBUG": "1",
            "NIKOLA_TEMPLATES_TRACE": "1",
            "NIKOLA_SHOW_TRACEBACKS": "1",
        }
    )
    code = "import nikola; print(nikola.DEBUG, nikola.TEMPLATES_TRACE, nikola.SHOW_TRACEBACKS)"
    result = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, check=True)

    assert result.stdout.strip() == "True True True"

def test_slugify_ascii_words():
    from nikola.utils import slugify

    assert slugify("Hello World!") == "hello-world"

def test_slugify_polish_diacritics():
    from nikola.utils import slugify

    assert slugify("Zażółć gęślą jaźń") == "zazolc-gesla-jazn"

def test_slugify_removes_unsafe_punctuation():
    from nikola.utils import slugify

    assert slugify("A/B:C? D") == "abc-d"

def test_unslugify_simple_slug():
    from nikola.utils import unslugify

    assert unslugify("hello-world") == "Hello world"

def test_unslugify_multiple_words():
    from nikola.utils import unslugify

    assert unslugify("a-b-c-d") == "A b c d"

def test_encodelink_escapes_spaces():
    from nikola.utils import encodelink

    assert encodelink("hello world.html") == "hello%20world.html"

def test_encodelink_escapes_unicode():
    from nikola.utils import encodelink

    assert encodelink("ümlaut and space.html") == "%C3%BCmlaut%20and%20space.html"

def test_encodelink_preserves_existing_percent_encoding():
    from nikola.utils import encodelink

    assert encodelink("already%20encoded.html") == "already%20encoded.html"

def test_translation_candidate_adds_language_before_extension():
    from nikola.utils import get_translation_candidate

    assert get_translation_candidate(_base_translation_config(), "post.rst", "es") == "post.es.rst"

def test_translation_candidate_removes_language_for_default():
    from nikola.utils import get_translation_candidate

    assert get_translation_candidate(_base_translation_config(), "post.es.rst", "en") == "post.rst"

def test_translation_candidate_extension_language_pattern():
    from nikola.utils import get_translation_candidate

    config = _base_translation_config("{path}.{ext}.{lang}")
    assert get_translation_candidate(config, "post.rst", "es") == "post.rst.es"

def test_translation_candidate_extension_language_default():
    from nikola.utils import get_translation_candidate

    config = _base_translation_config("{path}.{ext}.{lang}")
    assert get_translation_candidate(config, "post.rst.es", "en") == "post.rst"

def test_translation_candidate_preserves_directory_and_compound_extension():
    from nikola.utils import get_translation_candidate

    assert (
        get_translation_candidate(_base_translation_config(), "cache/posts/fancy.post.html", "es")
        == "cache/posts/fancy.post.es.html"
    )

def test_bool_from_meta_accepts_true_word():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({"draft": "true"}, "draft", fallback=False) is True

def test_bool_from_meta_accepts_yes_word():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({"draft": "yes"}, "draft", fallback=False) is True

def test_bool_from_meta_accepts_one_string():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({"draft": "1"}, "draft", fallback=False) is True

def test_bool_from_meta_accepts_false_word():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({"draft": "false"}, "draft", fallback=True) is False

def test_bool_from_meta_accepts_no_word():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({"draft": "no"}, "draft", fallback=True) is False

def test_bool_from_meta_accepts_zero_string():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({"draft": "0"}, "draft", fallback=True) is False

def test_bool_from_meta_uses_blank_value_for_missing_key():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({}, "draft", fallback="fallback", blank="blank") == "blank"

def test_bool_from_meta_uses_fallback_for_unknown_text():
    from nikola.utils import bool_from_meta

    assert bool_from_meta({"draft": "unknown"}, "draft", fallback="fallback", blank="blank") == "fallback"

def test_write_metadata_nikola_format_contains_declared_fields():
    from nikola.utils import write_metadata

    data = write_metadata({"title": "Hello, world!", "slug": "hello-world", "a": "1", "b": "2"}, "nikola")
    assert ".. title: Hello, world!" in data
    assert ".. slug: hello-world" in data
    assert ".. a: 1" in data
    assert data.endswith("\n\n")

def test_create_redirect_writes_redirect_document(tmp_path):
    from nikola.utils import create_redirect

    target = tmp_path / "from.html"
    create_redirect(str(target), "https://example.invalid/to")
    text = target.read_text(encoding="utf-8")
    assert "Redirecting" in text
    assert "https://example.invalid/to" in text

def test_load_data_reads_json_mapping(tmp_path):
    from nikola.utils import load_data

    source = tmp_path / "data.json"
    source.write_text('{"a": 1, "b": [2]}', encoding="utf-8")
    assert load_data(str(source)) == {"a": 1, "b": [2]}

def test_apply_shortcodes_replaces_single_shortcode():
    from nikola.shortcodes import apply_shortcodes

    def one(site, data, lang, post=None, **kw):
        return "ONE"

    rendered, deps = apply_shortcodes("A {{% one %}} B", {"one": one}, None, "x.rst", True, "en", {})
    assert rendered == "A ONE B"
    assert deps == []

def test_apply_shortcodes_passes_body_to_shortcode():
    from nikola.shortcodes import apply_shortcodes

    def echo(site, data, lang, post=None, **kw):
        return "ECHO[" + (data or "") + "]"

    rendered, deps = apply_shortcodes("A {{% echo %}}body{{% /echo %}} Z", {"echo": echo}, None, "x.rst", True, "en", {})
    assert rendered == "A ECHO[body] Z"
    assert deps == []

def test_extract_shortcodes_replaces_shortcode_with_token():
    from nikola.shortcodes import extract_shortcodes

    rendered, replacements = extract_shortcodes("A {{% one %}} B")
    assert rendered.startswith("A SHORTCODE")
    assert rendered.endswith("REPLACEMENT B")
    assert list(replacements.values()) == ["{{% one %}}"]

def test_unknown_shortcode_with_exceptions_returns_empty_output():
    from nikola.shortcodes import apply_shortcodes

    rendered, deps = apply_shortcodes("{{% missing %}}", {}, None, "x.rst", True, "en", {})
    assert rendered == ""
    assert deps == []

def test_init_creates_project_configuration(local_site):
    assert (local_site / "conf.py").is_file()

def test_init_creates_content_directories(local_site):
    for name in ["posts", "pages", "files", "galleries", "images", "listings"]:
        assert (local_site / name).is_dir()

def test_new_post_creates_slugged_post_source(local_site):
    post = local_site / "posts" / "hello-world.rst"
    assert post.is_file()

def test_new_post_source_contains_title_metadata(local_site):
    post = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    assert ".. title: Hello World" in post

def test_new_post_source_contains_slug_metadata(local_site):
    post = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    assert ".. slug: hello-world" in post

def test_new_post_source_contains_tags_metadata(local_site):
    post = (local_site / "posts" / "hello-world.rst").read_text(encoding="utf-8")
    assert "alpha" in post
    assert "beta" in post

def test_new_page_creates_page_source(local_site):
    pages = list((local_site / "pages").glob("*.rst"))
    assert any("about" in page.name for page in pages)

def test_surface_console_version_entry_runs_without_conf():
    from nikola.__main__ import main

    _ok(main(["version"]))

def test_surface_public_utils_module_is_importable_and_operational():
    from nikola.utils import slugify

    assert slugify("Surface Import") == "surface-import"

def test_malformed_shortcode_raises_parsing_error():
    from nikola.shortcodes import ParsingError, apply_shortcodes

    with pytest.raises(ParsingError):
        apply_shortcodes("{{%", {}, None, "broken.rst", True, "en", {})

