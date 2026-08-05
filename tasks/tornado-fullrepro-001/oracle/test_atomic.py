from __future__ import annotations

from contextlib import redirect_stderr
from datetime import datetime, timezone
from io import StringIO

import pytest
from tornado import routing
from tornado.options import Error, OptionParser
from tornado.template import DictLoader, ParseError, Template
from tornado.web import MissingArgumentError, RequestHandler, url

from conftest import make_app, make_handler, make_request, running_http_case


class EmptyHandler(RequestHandler):
    pass


class HeaderOverwriteHandler(RequestHandler):
    def get(self):
        self.set_header("X-Mode", "first")
        self.set_header("x-mode", "second")
        self.write("ok")


class HeaderAppendHandler(RequestHandler):
    def get(self):
        self.add_header("X-Step", "one")
        self.add_header("x-step", "two")
        self.write("ok")


class HeaderClearHandler(RequestHandler):
    def get(self):
        self.set_header("X-Temporary", "gone")
        self.clear_header("X-Temporary")
        self.write("ok")


class HeaderDatetimeHandler(RequestHandler):
    def get(self):
        self.set_header("Last-Modified", datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
        self.write("ok")


def fetch_one_handler(handler_class):
    with running_http_case(lambda: make_app([(r"/", handler_class)])) as case:
        return case.fetch("/")


def test_application_preserves_custom_settings():
    app = make_app([], project_name="control-panel", feature_enabled=True)
    assert app.settings["project_name"] == "control-panel"
    assert app.settings["feature_enabled"] is True


def test_application_reverse_url_uses_named_urlspec():
    app = make_app([url(r"/people/([0-9]+)", EmptyHandler, name="profile")])
    assert app.reverse_url("profile", 31) == "/people/31"


def test_application_reverse_url_escapes_string_arguments():
    app = make_app([url(r"/people/([^/]+)", EmptyHandler, name="person")])
    assert app.reverse_url("person", "Ada Lovelace") == "/people/Ada%20Lovelace"


def test_path_matches_returns_positional_groups():
    request = make_request(uri="/items/blue%20bag/42")
    result = routing.PathMatches(r"/items/([^/]+)/([0-9]+)").match(request)
    assert result == {"path_args": [b"blue bag", b"42"], "path_kwargs": {}}


def test_path_matches_returns_named_groups():
    request = make_request(uri="/named/blue%20bag")
    result = routing.PathMatches(r"/named/(?P<slug>[^/]+)").match(request)
    assert result == {"path_args": [], "path_kwargs": {"slug": b"blue bag"}}


def test_path_matches_reverse_escapes_arguments():
    matcher = routing.PathMatches(r"/asset/([^/]+)")
    assert matcher.reverse("space value") == "/asset/space%20value"


def test_host_matches_accepts_matching_host():
    request = make_request(headers={"Host": "api.example.com"})
    assert routing.HostMatches(r"api\.example\.com").match(request) == {}
    assert routing.HostMatches(r"docs\.example\.com").match(request) is None


def test_reversible_rule_router_reverses_named_rule():
    router = routing.ReversibleRuleRouter(
        [(routing.PathMatches(r"/download/([^/]+)"), object(), {}, "download")]
    )
    assert router.reverse_url("download", "report 1") == "/download/report%201"


def test_rule_router_add_rules_accepts_string_path_matcher():
    router = routing.RuleRouter()
    router.add_rules([("/ok", lambda request: None)])
    assert router.find_handler(make_request(uri="/ok")) is not None
    assert router.find_handler(make_request(uri="/miss")) is None


def test_template_generate_substitutes_values():
    output = Template("Hello {{ name }}!").generate(name="Ada")
    assert output == b"Hello Ada!"


def test_template_autoescape_escapes_html():
    output = Template("{{ value }}").generate(value="<tag>")
    assert output == b"&lt;tag&gt;"


def test_template_comment_is_omitted_from_output():
    output = Template("a{# ignore this #}b").generate()
    assert output == b"ab"


def test_dict_loader_include_uses_named_template():
    loader = DictLoader(
        {
            "page.html": "A:{% include 'piece.html' %}:Z",
            "piece.html": "{{ item }}",
        }
    )
    assert loader.load("page.html").generate(item="middle") == b"A:middle:Z"


def test_dict_loader_extends_base_template_block():
    loader = DictLoader(
        {
            "base.html": "title={% block title %}base{% end %}",
            "child.html": "{% extends 'base.html' %}{% block title %}child{% end %}",
        }
    )
    assert loader.load("child.html").generate() == b"title=child"


def test_template_apply_block_uses_callable():
    output = Template("{% apply upper %}mixed{% end %}").generate(
        upper=lambda value: value.upper()
    )
    assert output == b"MIXED"


def test_template_parse_error_is_public_exception():
    with pytest.raises(ParseError):
        Template("{{")


def test_option_parser_command_line_updates_defined_values():
    options = OptionParser()
    options.define("port", default=80, type=int)
    options.define("debug", default=False, type=bool)
    options.parse_command_line(["program", "--port=443", "--debug=true"])
    assert options.port == 443
    assert options.debug is True


def test_option_parser_returns_remainder_when_final_false():
    options = OptionParser()
    options.define("verbose", default=False, type=bool)
    rest = options.parse_command_line(
        ["program", "--verbose=true", "serve", "--flag=value"],
        final=False,
    )
    assert options.verbose is True
    assert rest == ["serve", "--flag=value"]


def test_option_parser_config_file_updates_defined_values(tmp_path):
    config = tmp_path / "settings.py"
    config.write_text('port = 8080\nusername = "ada"\nmode = "local"\n', encoding="utf-8")
    options = OptionParser()
    options.define("port", default=80, type=int)
    options.define("username", default="guest")
    options.define("mode", default="default")
    options.parse_config_file(str(config))
    assert options.as_dict()["port"] == 8080
    assert options.username == "ada"
    assert options.mode == "local"


def test_option_parser_multiple_int_range_expands_values():
    options = OptionParser()
    options.define("shards", type=int, multiple=True)
    options.parse_command_line(["program", "--shards=1,3,5:7"])
    assert options.shards == [1, 3, 5, 6, 7]


def test_option_parser_groups_and_group_dict_expose_named_group():
    options = OptionParser()
    options.define("plain", default="root")
    options.define("mode", default="fast", group="server")
    options.define("port", default=8000, type=int, group="server")
    assert "server" in options.groups()
    assert options.group_dict("server") == {"mode": "fast", "port": 8000}


def test_option_parser_as_dict_and_items_reflect_current_values():
    options = OptionParser()
    options.define("name", default="guest")
    options.define("level", default=1, type=int)
    options.parse_command_line(["program", "--name=ada", "--level=3"])
    assert options.as_dict()["name"] == "ada"
    assert ("level", 3) in list(options.items())


def test_option_parser_parse_callback_runs_on_final_parse():
    seen = []
    options = OptionParser()
    options.define("enabled", default=False, type=bool)
    options.add_parse_callback(lambda: seen.append(options.enabled))
    options.parse_command_line(["program", "--enabled=true"])
    assert seen == [True]


def test_option_parser_rejects_unknown_option():
    options = OptionParser()
    options.define("known", default="yes")
    stderr = StringIO()
    with redirect_stderr(stderr), pytest.raises(Error):
        options.parse_command_line(["program", "--missing=no"])


def test_request_handler_set_status_and_get_status():
    handler = make_handler()
    handler.set_status(201, reason="Created")
    assert handler.get_status() == 201


def test_request_handler_set_header_overwrites_value():
    response = fetch_one_handler(HeaderOverwriteHandler)
    assert response.headers["X-Mode"] == "second"


def test_request_handler_add_header_preserves_multiple_values():
    response = fetch_one_handler(HeaderAppendHandler)
    assert response.headers.get_list("X-Step") == ["one", "two"]


def test_request_handler_clear_header_removes_value():
    response = fetch_one_handler(HeaderClearHandler)
    assert "X-Temporary" not in response.headers


def test_request_handler_get_query_arguments_return_strings():
    handler = make_handler(uri="/search?tag=blue&tag=green&name=Ada")
    assert handler.get_query_arguments("tag") == ["blue", "green"]
    assert handler.get_query_argument("name") == "Ada"


def test_request_handler_body_arguments_parse_form_values():
    handler = make_handler(
        method="POST",
        uri="/submit?tag=query",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=b"tag=body&name=Ada",
    )
    assert handler.get_body_argument("name") == "Ada"
    assert handler.get_arguments("tag") == ["query", "body"]


def test_request_handler_missing_required_argument_raises_public_error():
    handler = make_handler(uri="/search")
    with pytest.raises(MissingArgumentError):
        handler.get_query_argument("missing")


def test_request_handler_get_cookie_reads_request_cookie():
    handler = make_handler(headers={"Cookie": "theme=blue; session=abc"})
    assert handler.get_cookie("theme") == "blue"
    assert handler.get_cookie("absent", "fallback") == "fallback"


def test_request_handler_signed_cookie_round_trips_value():
    app = make_app(cookie_secret="0123456789abcdef")
    handler = make_handler(app=app)
    signed = handler.create_signed_value("session", b"payload")
    assert handler.get_signed_cookie("session", value=signed.decode("utf-8")) == b"payload"


def test_request_handler_signed_cookie_key_version_is_visible():
    app = make_app(cookie_secret={1: "oldsecret", 2: "newsecret"}, key_version=2)
    handler = make_handler(app=app)
    signed = handler.create_signed_value("session", b"payload")
    assert handler.get_signed_cookie_key_version("session", value=signed.decode("utf-8")) == 2


def test_request_handler_reverse_url_uses_application_routes():
    app = make_app([url(r"/profile/([^/]+)", EmptyHandler, name="profile")])
    handler = make_handler(app=app)
    assert handler.reverse_url("profile", "Ada Lovelace") == "/profile/Ada%20Lovelace"


def test_request_handler_static_url_includes_version_parameter(tmp_path):
    (tmp_path / "asset.txt").write_text("asset", encoding="utf-8")
    app = make_app(static_path=str(tmp_path))
    handler = make_handler(app=app)
    generated = handler.static_url("asset.txt")
    assert generated.startswith("/static/asset.txt?v=")


def test_request_handler_static_url_can_omit_version_parameter(tmp_path):
    (tmp_path / "asset.txt").write_text("asset", encoding="utf-8")
    app = make_app(static_path=str(tmp_path))
    handler = make_handler(app=app)
    assert handler.static_url("asset.txt", include_version=False) == "/static/asset.txt"


def test_request_handler_static_url_can_include_host(tmp_path):
    (tmp_path / "asset.txt").write_text("asset", encoding="utf-8")
    app = make_app(static_path=str(tmp_path))
    handler = make_handler(app=app, host="assets.example.com")
    generated = handler.static_url("asset.txt", include_host=True)
    assert generated.startswith("http://assets.example.com/static/asset.txt?v=")


def test_request_handler_render_string_uses_template_loader():
    app = make_app(
        template_path="atomic-templates",
        template_loader=DictLoader({"hello.html": "Hello {{ name }}"}),
    )
    handler = make_handler(app=app)
    assert handler.render_string("hello.html", name="Ada") == b"Hello Ada"


def test_request_handler_template_namespace_contains_public_helpers():
    app = make_app(static_path="unused-static-path")
    handler = make_handler(app=app)
    namespace = handler.get_template_namespace()
    assert namespace["handler"] is handler
    assert namespace["request"] is handler.request
    assert callable(namespace["static_url"])
    assert callable(namespace["xsrf_form_html"])


def test_request_handler_header_datetime_value_is_http_date():
    response = fetch_one_handler(HeaderDatetimeHandler)
    assert response.headers["Last-Modified"] == "Thu, 02 Jan 2020 03:04:05 GMT"
