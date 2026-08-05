from __future__ import annotations

import json

import pytest
from tornado.options import OptionParser
from tornado.template import DictLoader
from tornado.web import RedirectHandler, RequestHandler, url

from conftest import make_app, running_http_case


class ArgumentEchoHandler(RequestHandler):
    def get(self):
        self.write(
            {
                "query": self.get_query_arguments("tag"),
                "combined": self.get_arguments("tag"),
                "fallback": self.get_argument("missing", "fallback"),
            }
        )

    def post(self):
        self.write(
            {
                "query": self.get_query_arguments("tag"),
                "body": self.get_body_arguments("tag"),
                "combined": self.get_arguments("tag"),
                "name": self.get_body_argument("name"),
            }
        )


class CookieSetHandler(RequestHandler):
    def get(self):
        self.set_cookie("theme", "blue", path="/")
        self.write("set")


class CookieReadHandler(RequestHandler):
    def get(self):
        self.write(self.get_cookie("theme", "missing"))


class SignedCookieSetHandler(RequestHandler):
    def get(self):
        self.set_signed_cookie("signed", "payload", expires_days=None)
        self.write("signed")


class SignedCookieReadHandler(RequestHandler):
    def get(self):
        value = self.get_signed_cookie("signed")
        self.write(value.decode("utf-8") if value else "missing")


class SignedCookieVersionHandler(RequestHandler):
    def get(self):
        version = self.get_signed_cookie_key_version("signed")
        self.write(str(version))


class HeaderWorkflowHandler(RequestHandler):
    def get(self):
        self.set_header("X-Overwrite", "first")
        self.set_header("x-overwrite", "second")
        self.add_header("X-Multi", "one")
        self.add_header("x-multi", "two")
        self.set_header("X-Removed", "gone")
        self.clear_header("X-Removed")
        self.write("headers")


class ProfileHandler(RequestHandler):
    def get(self, slug):
        self.write("profile:" + slug)


class ReverseLinkHandler(RequestHandler):
    def get(self, slug):
        self.write(self.reverse_url("profile", slug))


class StaticLinkHandler(RequestHandler):
    def get(self):
        include_version = self.get_argument("version", "1") != "0"
        self.write(self.static_url("asset.txt", include_version=include_version))


class TemplateEchoHandler(RequestHandler):
    def get(self):
        name = self.get_query_argument("name")
        self.render(
            "page.html",
            name=name,
            profile=self.reverse_url("profile", name),
            static_url=self.static_url("asset.txt", include_version=False),
        )


class AssetPageHandler(RequestHandler):
    def get(self):
        self.render("asset.html", href=self.static_url("asset.txt"))


class LifecycleHandler(RequestHandler):
    def prepare(self):
        self.settings["events"].append("prepare")

    def get(self):
        self.settings["events"].append("get")
        self.write("ok")

    def on_finish(self):
        self.settings["events"].append("finish")


class InitializeHandler(RequestHandler):
    def initialize(self, greeting):
        self.greeting = greeting

    def get(self, name):
        self.write(self.greeting + ":" + name)


class SettingHandler(RequestHandler):
    def get(self):
        self.write(self.settings["label"])


class DefaultMissingHandler(RequestHandler):
    def get(self):
        self.set_status(404)
        self.write("custom-missing")


class PathKwHandler(RequestHandler):
    def get(self, slug):
        self.write(slug)


class PathPosHandler(RequestHandler):
    def get(self, value):
        self.write(value)


class PlainHandler(RequestHandler):
    def get(self):
        self.write("plain")


class CurrentUserTemplateHandler(RequestHandler):
    def get_current_user(self):
        return self.get_cookie("user", "guest")

    def get(self):
        self.render("user.html")


class WriteDictHandler(RequestHandler):
    def get(self):
        self.write({"status": "ok", "items": [1, 2, 3]})


class ClearCookieHandler(RequestHandler):
    def get(self):
        self.clear_cookie("token", path="/")
        self.write("clear")


class TokenSetHandler(RequestHandler):
    def get(self):
        self.set_cookie("token", "abc", path="/")
        self.write("set")


class TokenReadHandler(RequestHandler):
    def get(self):
        self.write(self.get_cookie("token", "missing"))


def response_json(response):
    return json.loads(response.body.decode("utf-8"))


def cookie_pair(response, name):
    for header in response.headers.get_list("Set-Cookie"):
        if header.startswith(name + "="):
            return header.split(";", 1)[0]
    raise AssertionError("expected Set-Cookie header")


def make_workflow_app(static_path=None, *, cookie_secret="0123456789abcdef", **settings):
    templates = DictLoader(
        {
            "page.html": "Hello {{ name }} profile={{ profile }} static={{ static_url }}",
            "asset.html": "asset={{ href }}",
            "user.html": "user={{ current_user }}",
        }
    )
    app_settings = {
        "template_loader": templates,
        "template_path": "workflow-templates",
        "cookie_secret": cookie_secret,
        "events": [],
        "label": "configured",
        "default_handler_class": DefaultMissingHandler,
    }
    if static_path is not None:
        app_settings["static_path"] = str(static_path)
    app_settings.update(settings)
    return make_app(
        [
            (r"/args", ArgumentEchoHandler),
            (r"/set-cookie", CookieSetHandler),
            (r"/read-cookie", CookieReadHandler),
            (r"/set-signed", SignedCookieSetHandler),
            (r"/read-signed", SignedCookieReadHandler),
            (r"/signed-version", SignedCookieVersionHandler),
            (r"/headers", HeaderWorkflowHandler),
            url(r"/profile/([^/]+)", ProfileHandler, name="profile"),
            (r"/link/([^/]+)", ReverseLinkHandler),
            (r"/static-link", StaticLinkHandler),
            (r"/template", TemplateEchoHandler),
            (r"/asset-page", AssetPageHandler),
            (r"/lifecycle", LifecycleHandler),
            (r"/init/([^/]+)", InitializeHandler, {"greeting": "hello"}),
            (r"/setting", SettingHandler),
            (r"/old", RedirectHandler, {"url": "/new"}),
            (r"/new", PlainHandler),
            (r"/kw/(?P<slug>[^/]+)", PathKwHandler),
            (r"/pos/([^/]+)", PathPosHandler),
            (r"/plain", PlainHandler),
            (r"/user-template", CurrentUserTemplateHandler),
            (r"/write-dict", WriteDictHandler),
            (r"/clear-cookie", ClearCookieHandler),
        ],
        **app_settings,
    )


@pytest.mark.depends_on(
    "test_request_handler_get_query_arguments_return_strings",
    "test_request_handler_body_arguments_parse_form_values",
)
def test_http_query_and_body_arguments_are_projected_as_json():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch(
            "/args?tag=query",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=b"tag=body&name=Ada",
        )
    assert response.code == 200
    assert response_json(response) == {
        "query": ["query"],
        "body": ["body"],
        "combined": ["query", "body"],
        "name": "Ada",
    }


@pytest.mark.depends_on("test_request_handler_get_cookie_reads_request_cookie")
def test_http_cookie_set_then_read_round_trip():
    with running_http_case(make_workflow_app) as case:
        first = case.fetch("/set-cookie")
        second = case.fetch("/read-cookie", headers={"Cookie": cookie_pair(first, "theme")})
    assert first.code == 200
    assert second.body == b"blue"


@pytest.mark.depends_on("test_request_handler_signed_cookie_round_trips_value")
def test_http_signed_cookie_set_then_read_round_trip():
    with running_http_case(make_workflow_app) as case:
        first = case.fetch("/set-signed")
        second = case.fetch("/read-signed", headers={"Cookie": cookie_pair(first, "signed")})
    assert second.code == 200
    assert second.body == b"payload"


@pytest.mark.depends_on("test_request_handler_signed_cookie_key_version_is_visible")
def test_http_signed_cookie_key_version_survives_second_request():
    secrets = {1: "oldsecret", 2: "newsecret"}
    with running_http_case(
        lambda: make_workflow_app(cookie_secret=secrets, key_version=2)
    ) as case:
        first = case.fetch("/set-signed")
        second = case.fetch("/signed-version", headers={"Cookie": cookie_pair(first, "signed")})
    assert second.body == b"2"


@pytest.mark.depends_on(
    "test_request_handler_set_header_overwrites_value",
    "test_request_handler_add_header_preserves_multiple_values",
    "test_request_handler_clear_header_removes_value",
)
def test_http_header_workflow_projects_overwrite_add_and_clear():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/headers")
    assert response.headers["X-Overwrite"] == "second"
    assert response.headers.get_list("X-Multi") == ["one", "two"]
    assert "X-Removed" not in response.headers


@pytest.mark.depends_on(
    "test_application_reverse_url_escapes_string_arguments",
    "test_request_handler_reverse_url_uses_application_routes",
)
def test_http_named_route_reversed_inside_handler_can_be_fetched():
    with running_http_case(make_workflow_app) as case:
        link = case.fetch("/link/Ada%20Lovelace")
        profile = case.fetch(link.body.decode("utf-8"))
    assert link.body == b"/profile/Ada%20Lovelace"
    assert profile.body == b"profile:Ada Lovelace"


@pytest.mark.depends_on("test_request_handler_static_url_includes_version_parameter")
def test_http_static_url_from_handler_fetches_versioned_asset(tmp_path):
    (tmp_path / "asset.txt").write_text("asset-body", encoding="utf-8")
    with running_http_case(lambda: make_workflow_app(tmp_path)) as case:
        link = case.fetch("/static-link")
        asset = case.fetch(link.body.decode("utf-8"))
    assert link.body.startswith(b"/static/asset.txt?v=")
    assert asset.body == b"asset-body"


@pytest.mark.depends_on("test_request_handler_static_url_can_omit_version_parameter")
def test_http_static_url_without_version_fetches_asset(tmp_path):
    (tmp_path / "asset.txt").write_text("asset-body", encoding="utf-8")
    with running_http_case(lambda: make_workflow_app(tmp_path)) as case:
        link = case.fetch("/static-link?version=0")
        asset = case.fetch(link.body.decode("utf-8"))
    assert link.body == b"/static/asset.txt"
    assert asset.body == b"asset-body"


@pytest.mark.depends_on(
    "test_request_handler_render_string_uses_template_loader",
    "test_dict_loader_include_uses_named_template",
    "test_request_handler_reverse_url_uses_application_routes",
)
def test_http_template_render_uses_loader_arguments_and_reverse_url(tmp_path):
    (tmp_path / "asset.txt").write_text("asset-body", encoding="utf-8")
    with running_http_case(lambda: make_workflow_app(tmp_path)) as case:
        response = case.fetch("/template?name=Ada")
    body = response.body.decode("utf-8")
    assert "Hello Ada" in body
    assert "profile=/profile/Ada" in body
    assert "static=/static/asset.txt" in body


@pytest.mark.depends_on(
    "test_request_handler_static_url_includes_version_parameter",
    "test_dict_loader_extends_base_template_block",
)
def test_http_asset_template_uses_static_url_and_static_handler(tmp_path):
    (tmp_path / "asset.txt").write_text("asset-body", encoding="utf-8")
    with running_http_case(lambda: make_workflow_app(tmp_path)) as case:
        page = case.fetch("/asset-page")
        href = page.body.decode("utf-8").split("asset=", 1)[1]
        asset = case.fetch(href)
    assert href.startswith("/static/asset.txt?v=")
    assert asset.body == b"asset-body"


@pytest.mark.depends_on("test_application_preserves_custom_settings")
def test_http_prepare_get_finish_lifecycle_records_public_order():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/lifecycle")
        assert case.application is not None
        events = case.application.settings["events"]
    assert response.body == b"ok"
    assert events == ["prepare", "get", "finish"]


@pytest.mark.depends_on("test_application_preserves_custom_settings")
def test_http_initialize_kwargs_are_visible_to_handler_method():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/init/Ada")
    assert response.body == b"hello:Ada"


@pytest.mark.depends_on("test_application_preserves_custom_settings")
def test_http_default_handler_class_handles_missing_route():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/missing-route")
    assert response.code == 404
    assert response.body == b"custom-missing"


@pytest.mark.depends_on("test_application_reverse_url_uses_named_urlspec")
def test_http_redirect_handler_preserves_query_on_location():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/old?from=query", follow_redirects=False)
    assert response.code == 301
    assert response.headers["Location"] == "/new?from=query"


@pytest.mark.depends_on("test_path_matches_returns_named_groups")
def test_http_named_path_argument_is_decoded_before_handler_get():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/kw/blue%20bag")
    assert response.body == b"blue bag"


@pytest.mark.depends_on("test_path_matches_returns_positional_groups")
def test_http_positional_path_argument_is_decoded_before_handler_get():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/pos/blue%20bag")
    assert response.body == b"blue bag"


@pytest.mark.depends_on(
    "test_option_parser_command_line_updates_defined_values",
    "test_application_preserves_custom_settings",
)
def test_http_option_parser_values_can_drive_application_settings():
    options = OptionParser()
    options.define("label", default="default")
    options.parse_command_line(["program", "--label=configured-by-options"])
    with running_http_case(lambda: make_workflow_app(label=options.label)) as case:
        response = case.fetch("/setting")
    assert response.body == b"configured-by-options"


@pytest.mark.depends_on(
    "test_request_handler_get_cookie_reads_request_cookie",
    "test_request_handler_template_namespace_contains_public_helpers",
)
def test_http_current_user_from_cookie_reaches_template_namespace():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/user-template", headers={"Cookie": "user=Ada"})
    assert response.body == b"user=Ada"


@pytest.mark.depends_on("test_request_handler_set_header_overwrites_value")
def test_http_write_dict_sets_json_response_projection():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/write-dict")
    assert response.headers["Content-Type"].startswith("application/json")
    assert response_json(response) == {"status": "ok", "items": [1, 2, 3]}


@pytest.mark.depends_on("test_request_handler_static_url_includes_version_parameter")
def test_http_static_file_get_and_head_share_content_headers(tmp_path):
    (tmp_path / "asset.txt").write_text("asset-body", encoding="utf-8")
    with running_http_case(lambda: make_workflow_app(tmp_path)) as case:
        get_response = case.fetch("/static/asset.txt")
        head_response = case.fetch("/static/asset.txt", method="HEAD")
    assert get_response.body == b"asset-body"
    assert head_response.body == b""
    assert head_response.headers["Content-Length"] == get_response.headers["Content-Length"]
    assert head_response.headers["Content-Type"] == get_response.headers["Content-Type"]


@pytest.mark.depends_on("test_request_handler_get_cookie_reads_request_cookie")
def test_http_clear_cookie_sets_empty_cookie_response():
    with running_http_case(make_workflow_app) as case:
        response = case.fetch("/clear-cookie", headers={"Cookie": "token=abc"})
    cleared = cookie_pair(response, "token")
    assert cleared == 'token=""'


@pytest.mark.depends_on(
    "test_dict_loader_include_uses_named_template",
    "test_dict_loader_extends_base_template_block",
)
def test_http_template_include_and_extends_share_loader_context():
    class ComposedTemplateHandler(RequestHandler):
        def get(self):
            self.render("child.html", name="Ada")

    def app_factory():
        loader = DictLoader(
            {
                "base.html": "title={% block body %}base{% end %}",
                "piece.html": "piece={{ name }}",
                "child.html": (
                    '{% extends "base.html" %}'
                    '{% block body %}child={{ name }}:'
                    '{% include "piece.html" %}{% end %}'
                ),
            }
        )
        return make_app(
            [(r"/composed", ComposedTemplateHandler)],
            template_loader=loader,
            template_path="composed-workflow-templates",
        )

    with running_http_case(app_factory) as case:
        response = case.fetch("/composed")

    assert response.body == b"title=child=Ada:piece=Ada"


@pytest.mark.depends_on("test_option_parser_config_file_updates_defined_values")
def test_http_config_file_option_reaches_application_setting(tmp_path):
    config = tmp_path / "settings.py"
    config.write_text('label = "from-file"\n', encoding="utf-8")
    options = OptionParser()
    options.define("label", default="default")
    options.parse_config_file(str(config))

    with running_http_case(
        lambda: make_workflow_app(label=options.label)
    ) as case:
        response = case.fetch("/setting")

    assert response.body == b"from-file"


@pytest.mark.depends_on("test_request_handler_signed_cookie_round_trips_value")
def test_http_tampered_signed_cookie_is_rejected():
    with running_http_case(make_workflow_app) as case:
        first = case.fetch("/set-signed")
        cookie = cookie_pair(first, "signed")
        name, value = cookie.split("=", 1)
        replacement = "0" if value[-1] != "0" else "1"
        tampered = f"{name}={value[:-1]}{replacement}"
        second = case.fetch("/read-signed", headers={"Cookie": tampered})

    assert second.body == b"missing"


@pytest.mark.depends_on("test_request_handler_get_cookie_reads_request_cookie")
def test_http_set_clear_and_read_cookie_workflow():
    app = make_app(
        [
            (r"/set-token", TokenSetHandler),
            (r"/read-token", TokenReadHandler),
            (r"/clear-token", ClearCookieHandler),
        ]
    )

    with running_http_case(lambda: app) as case:
        set_response = case.fetch("/set-token")
        token = cookie_pair(set_response, "token")
        clear_response = case.fetch("/clear-token", headers={"Cookie": token})
        cleared = cookie_pair(clear_response, "token")
        read_response = case.fetch("/read-token", headers={"Cookie": cleared})

    assert set_response.body == b"set"
    assert cleared == 'token=""'
    assert read_response.body == b""
