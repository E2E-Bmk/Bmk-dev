# Tornado Public Web Specification

## Product Overview

Tornado is a Python web framework and asynchronous networking library. This specification covers the public web framework surface used to construct an `Application`, route requests to `RequestHandler` subclasses, reverse named routes, generate static URLs, render templates, parse options, set deterministic cookies and headers, and exercise local HTTP behavior through Tornado's testing helpers.

The expected product presents coherent behavior across direct Python APIs and loopback HTTP requests: a route declared once should be reversible by application and handler methods, visible through request handling, and compatible with template and static file helpers.

## Scope

This specification covers:

- `tornado.web.Application`, `RequestHandler`, `StaticFileHandler`, `RedirectHandler`, and `url`.
- Public `RequestHandler` methods for settings access, path arguments, query/body arguments, cookies, signed cookies, headers, status, rendering, `reverse_url`, and `static_url`.
- Public routing classes in `tornado.routing`, including `PathMatches`, `HostMatches`, `RuleRouter`, and `ReversibleRuleRouter`.
- Public template APIs `Template`, `DictLoader`, and `ParseError`.
- Public options APIs `OptionParser` and `Error`.
- Local loopback HTTP workflows created with `tornado.testing.AsyncHTTPTestCase`.

## Non-Goals

- Remote network clients, outbound services, TLS, websockets, DNS, subprocess servers, file watching, and optional integrations are not required.
- Exact traceback text, exact exception messages, log wording, generated date headers, whole HTML snapshots, and private object internals are not required.
- Private modules, private test utilities, and import paths under upstream test packages are not part of this specification.
- Timing races, sleeps, wall-clock polling, host-specific resources, and persistent global option state are not required.

## Representative Workflows

### Routed Handler Workflow

```python
from tornado.web import Application, RequestHandler, url

class ProfileHandler(RequestHandler):
    def get(self, slug):
        self.write("profile:" + slug)

app = Application([url(r"/profile/([^/]+)", ProfileHandler, name="profile")])
assert app.reverse_url("profile", "Ada Lovelace") == "/profile/Ada%20Lovelace"
```

### Template And Static Workflow

```python
from tornado.template import DictLoader
from tornado.web import Application, RequestHandler

class PageHandler(RequestHandler):
    def get(self):
        self.render("page.html", asset=self.static_url("asset.txt"))

loader = DictLoader({"page.html": "asset={{ asset }}"})
app = Application([(r"/page", PageHandler)], template_loader=loader, static_path="static")
```

### Options-To-Application Workflow

```python
from tornado.options import OptionParser
from tornado.web import Application

options = OptionParser()
options.define("label", default="default")
options.parse_command_line(["program", "--label=configured"])
app = Application([], label=options.label)
assert app.settings["label"] == "configured"
```

## Application And Request Handling

WHEN an `Application` is constructed with keyword settings, THE system SHALL expose those settings to request handlers through `handler.settings` and `handler.application.settings`.

WHEN URL specs are named with `url(..., name=...)`, THE system SHALL reverse them through `Application.reverse_url` and `RequestHandler.reverse_url`. Reversed arguments SHALL be converted to text and URL-escaped for path usage.

WHEN a request path regex contains positional or named groups, THE system SHALL pass decoded values to handler methods and expose the corresponding `path_args` or `path_kwargs` during request handling.

WHEN a handler defines `initialize`, THE system SHALL pass URL spec keyword arguments to it before the HTTP verb method runs. WHEN a handler defines `prepare` and `on_finish`, THE system SHALL call them around normal request processing.

## Routing

`PathMatches` SHALL match request paths against regular expressions, expose positional or named matched values, and reverse simple reversible path patterns with escaped arguments.

`HostMatches` SHALL match the request host name against its host pattern. `RuleRouter` SHALL choose the first matching rule and return a delegate for callable or nested router targets. `ReversibleRuleRouter` SHALL reverse named rules and nested reversible routers when a route name is present.

## Templates And Static URLs

`Template.generate` SHALL return bytes and substitute supplied values. By default it SHALL HTML-escape interpolated values. Template comments SHALL be omitted, `{% include %}` SHALL load another template from the same loader, `{% extends %}` SHALL apply block overrides, and parse errors SHALL raise `ParseError`.

`RequestHandler.render_string` and `RequestHandler.render` SHALL use the configured public template loader and the handler template namespace. The namespace SHALL include public helpers such as the handler object, request object, `static_url`, and `xsrf_form_html`.

WHEN `static_path` is configured, `RequestHandler.static_url` SHALL generate a static URL for the named asset. With versioning enabled, the URL SHALL include a version query parameter derived from the asset. With versioning disabled, it SHALL omit that query parameter. With host inclusion enabled, it SHALL include the request protocol and host.

## Options

`OptionParser.define` SHALL register named options with defaults, types, groups, callbacks, and multiple values where requested. `parse_command_line` SHALL update defined option values from command-line arguments. With `final=False`, it SHALL return unparsed remaining arguments for another parser.

`parse_config_file` SHALL load defined values from a local Python-style configuration file. `items`, `as_dict`, `groups`, and `group_dict` SHALL expose current parser state. Unknown command-line options SHALL raise `tornado.options.Error`.

## Cookies And Headers

`RequestHandler.get_cookie` SHALL read cookies supplied on the request and return a default for missing names. Signed cookie helpers SHALL create values that validate with the same application `cookie_secret`, and key-versioned secrets SHALL expose the signing key version.

`set_header` SHALL overwrite an outgoing header value, `add_header` SHALL preserve repeated values, and `clear_header` SHALL remove a header set earlier in the handler. Header values supplied as datetimes SHALL be formatted as HTTP dates. `set_status` and `get_status` SHALL agree on the current response status.

## Product State Model

The product state is the combination of application settings, URL specs, request method and URI, decoded path captures, query/body arguments, request cookies, outgoing headers and cookies, template loader entries, static file contents, option definitions, and loopback HTTP responses.

The same facts must remain coherent across projections:

- A route name reversed by an `Application` must produce the same path when reversed inside a `RequestHandler`.
- Path captures matched by routing classes must be the same values delivered to handler methods.
- Template output must see handler arguments, current user values, reversed URLs, and static URLs from the active application.
- Static URLs generated by handlers must fetch the same local files through Tornado's static handler.
- Option values parsed outside the application must be usable as application settings inside handlers.
- Cookies and signed cookies set in one local response must be readable when the client sends the corresponding cookie pair on a later local request.
- Header mutations performed in handlers must be visible in local HTTP responses.

## Error Semantics

Template syntax failures SHALL raise `ParseError`. Missing required request arguments SHALL raise Tornado's public missing-argument error. Unknown options SHALL raise `tornado.options.Error`.

Tests rely on public exception classes and successful failure, not exact message text or traceback contents.

## Cross-View Invariants

- Direct route reversal and request-visible route reversal must agree on the escaped URL path.
- Direct `PathMatches` captures and HTTP handler path arguments must agree after URL decoding.
- Direct template rendering and handler template rendering must use the same loader semantics.
- Direct static URL generation and HTTP static file serving must agree on the target asset.
- Direct option parsing and handler settings lookup must agree on parsed values.
- Direct signed cookie validation and two-request HTTP signed cookie validation must agree on payload and key version.
- Direct header mutation APIs and HTTP response headers must agree on overwrite, multi-value, and clear behavior.

## Installable Surface

Public imports:

```python
from tornado import routing
from tornado.httputil import HTTPHeaders, HTTPServerRequest, RequestStartLine, parse_body_arguments
from tornado.options import Error, OptionParser
from tornado.template import DictLoader, ParseError, Template
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RedirectHandler, RequestHandler, StaticFileHandler, url
```

API catalog:

| Name | Kind | Role |
|---|---|---|
| `Application` | class | Holds settings and routes requests to handlers. |
| `HTTPHeaders` | class | Stores deterministic request and response header values. |
| `HTTPServerRequest` | class | Represents a runner-created local HTTP request. |
| `RequestStartLine` | class | Stores the method, URI, and protocol for a local request. |
| `parse_body_arguments` | function | Parses local form-encoded request bodies. |
| `RequestHandler` | class | Handles HTTP verbs and exposes request, response, cookie, template, and URL helpers. |
| `StaticFileHandler` | class | Serves files from the configured static path. |
| `RedirectHandler` | class | Produces redirect responses from route configuration. |
| `url` | function | Declares named URL specs for routing and reversal. |
| `PathMatches` | class | Matches and reverses path regular expressions. |
| `HostMatches` | class | Matches request host names. |
| `RuleRouter` | class | Routes requests through ordered rules. |
| `ReversibleRuleRouter` | class | Routes and reverses named rules. |
| `Template` | class | Compiles and renders template text. |
| `DictLoader` | class | Loads templates from an in-memory mapping. |
| `ParseError` | exception | Reports template parse failures. |
| `OptionParser` | class | Defines and parses command-line or config-file options. |
| `Error` | exception | Reports public options failures. |
| `AsyncHTTPTestCase` | class | Runs local loopback HTTP tests against an application. |

## Invocation Protocol

Callers use normal Python imports. HTTP behavior is exercised only through local loopback servers owned by the running process. File access is limited to temporary template/config/static files created by the caller and in-memory data structures.

## Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party package is preinstalled and importable: `pytest`. The target package is not pre-installed. The assessment environment provides the same interpreter and package set.

The project must declare standard Python packaging metadata at the project root so the package can be installed with pip.

## Evaluation Notes

Implementations should follow the documented Tornado public API names and behavior listed above. The expected behavior is deterministic for local route matching, URL reversal, template rendering, option parsing, cookie/header APIs, and loopback HTTP responses. Exact generated hash strings, dynamic dates, whole HTML pages, traceback text, log wording, private state, optional integrations, and remote network behavior are outside this specification.
