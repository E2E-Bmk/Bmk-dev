<!-- SPEC.md -->
# WebOb request and response specification

## Scope and interpretation

This document defines covered public behavior for the distribution importable
as `webob`. Normative statements use **must** or **must not**. Examples and
implementation choices are non-normative.

The product provides WSGI request and response objects, multi-value and header
views, parsed HTTP header values, cookie and serialization helpers, public HTTP
exceptions, static-file applications, and a request-aware WSGI decorator.
Implementations may choose any internal organization, cache, descriptor,
parser, or state machine as long as the public effects below agree.

Exact exception prose, HTML layout, dictionary representation, private
attributes, internal cache identity, filesystem traversal algorithm, parser
stages, and source layout are not compatibility requirements unless expressly
stated. No real network service is required.

## Public surface

The covered distribution provides:

- `webob.Request`, `webob.BaseRequest`, `webob.Response`, and public aliases;
- `MultiDict`, `NestedMultiDict`, `NoVars`, `GetDict`, `ResponseHeaders`, and
  `EnvironHeaders` from their documented public modules;
- public Accept, language, range, content-range, entity-tag, If-Range, and
  Cache-Control value types and parser functions;
- cookie construction, cookie profiles, JSON/base64/signed serializers, and
  signed cookie profiles;
- public HTTP exception classes, `status_map`, and
  `HTTPExceptionMiddleware`; and
- `FileApp`, `DirectoryApp`, `wsgify`, date utilities, and HTML escaping.

Installed distribution metadata exposes a nonempty WebOb version. No console
command is required.

## WSGI environment and request identity

A Request wraps a WSGI environment dictionary. Public URL, method, script
name, path, query, scheme, host, port, content, and header properties project
that environment. A non-dictionary environment and unknown constructor
keywords fail rather than becoming hidden state.

`Request.blank` creates the minimal WSGI values for a supplied URL. Path and
query text map to `PATH_INFO` and `QUERY_STRING`; a base URL supplies scheme,
authority, port, and script prefix. Unsupported schemes and a base URL with a
query or fragment fail. Caller environment and header values override
generated defaults at their documented seams.

Writable URL components update later component and complete-URL views.
Restoring the original components restores the original URL meaning. Missing
required WSGI keys may fail through the property that requires them.

Ad-hoc public request attributes use the wrapped environment as shared state.
Another Request over that environment sees the attribute; deletion removes it
for both views, and deleting a missing attribute fails.

## Request body, variables, cookies, and routing

Request bodies are bytes. Assigning bytes replaces the public input stream,
updates length, and provides a readable body. Assigning `None` means an empty
body; other body types fail. A body-file value follows documented
readable/seekable and length semantics and must be file-like.

Text access requires an applicable charset. JSON assignment and reading use
the declared encoding and the same underlying bytes. A failed incompatible
assignment leaves the previous usable state observable, and a later valid
replacement does not inherit stale decoded or length state. Deprecated
charset assignment may fail explicitly without changing the prior value.

`GET` parses and preserves duplicate query values and is writable; mutating it
rewrites the query string. Form-capable requests expose `POST`; non-form
requests expose a read-only empty variable view. `params` reads query values
before form values and concatenates duplicates in that order. Query mutation
updates later combined reads without destroying form state.

Request cookies project the Cookie header. Replacing the cookie mapping
rewrites that header, and another Request over the same environment observes
the new values. Missing cookies follow ordinary mapping semantics.

`path_info_peek` observes the next segment without mutation.
`path_info_pop` moves a matching segment from path to script name; an absent or
nonmatching segment is non-destructive. Repeated routing remains consistent
with URL reconstruction.

`copy` and `copy_get` return distinct Request objects. Their documented
shallow environment relationship does not let body consumption or
method/content/body reset on one copy corrupt independently owned state in
another. `copy_get` represents an empty-body GET view.

## Multi-value and header mappings

`MultiDict` stores ordered pairs. Indexed lookup selects the documented
effective value, `getall` returns all matches in order, and `getone` requires
exactly one. Adding appends; item assignment and mapping update replace the
key's effective values; extension appends. Missing or ambiguous one-value
operations fail as mapping operations.

`NestedMultiDict` is a read-only ordered view of child mappings. Indexed lookup
selects the first child containing a key and `getall` concatenates child
results. `NoVars` is an empty read-only variable mapping with safe default and
empty list/dictionary projections. Mutators fail without changing children or
hidden storage.

`ResponseHeaders` is a case-insensitive multi-value view of a Response's
ordered header list. Setting removes prior case-insensitive matches and
appends the new value; adding preserves repeats. Replacing the header list
makes a later public headers access represent the replacement. An earlier
materialized header view may continue to own its earlier list.

`EnvironHeaders` maps public names to WSGI CGI keys. Content-Type and
Content-Length use dedicated keys; other names use HTTP-prefixed keys. Reads
are case-insensitive and missing names fail as mapping reads. Public Request
header and typed-content writes update the same environment. A new Request
over that environment observes the result; invalidation timing for a
previously materialized parsed descriptor after direct dictionary mutation is
not prescribed.

## Response model and ownership

A Response represents WSGI status, ordered headers, and a byte body or body
iterator. Its ordinary default is a successful empty response. The
constructor accepts direct body or application iterator, not both, and rejects
unknown keywords.

Known integer status codes project to standard strings; other supported codes
use an appropriate public reason family. A textual status begins with an
integer code. Unsupported types and malformed strings fail. `status`,
`status_code`, and `status_int` stay consistent.

Body reads produce bytes. Direct byte assignment updates iterator and
automatic length. Text assignment requires text and an applicable encoding.
JSON assignment and reading use the Response's content type, encoding, and
same body. Assigning an application iterator clears or recomputes automatic
length according to the public body projection. An explicitly supplied
Content-Length is caller metadata and may differ from body bytes; WebOb
preserves it rather than silently rewriting it.

Content type, charset, content-type parameters, raw Content-Type, and the
header-list entry are one public state. Writable public views update later
views without duplicate effective values, and values requiring quoting are
rendered safely.

A Response copy is a distinct public object with copied status, headers, body
content, and conditional policy. Consuming or modifying one must not
unexpectedly exhaust or rewrite the other.

When a body or WSGI iterable exposes `close`, the owner completing or aborting
iteration follows the documented close boundary. Caller exceptions are not
replaced by incidental cleanup success. One failed lifecycle does not poison
an independent later response.

## Cache policy and content encoding

Cache-expiration operations keep Cache-Control, Expires, Last-Modified,
Pragma, and the typed cache-control view coherent. Immediate no-cache and
positive max-age policies replace one another instead of accumulating stale
contradictions. Restoring the earlier policy restores its meaning.

Gzip encoding changes body and Content-Encoding consistently. Applying gzip
again is idempotent. Decoding restores the representation and removes the
marker. Unsupported encodings fail without changing body or claiming a false
encoding; a later supported encode/decode cycle remains usable.

## Parsed HTTP header values

Accept-family parsers provide safe public objects for valid, missing, and
invalid input. Valid objects expose documented preference, membership,
quality, acceptable-offer, and best-match behavior. Missing headers represent
ordinary protocol defaults; invalid headers remain safe to inspect. The exact
deprecated matching algorithm is not expanded beyond its public result.

Cache-Control parsing provides request, response, shared, numeric, boolean,
alias, and extension directives. Bound directive mutation rewrites the raw
header. Replacing raw text makes a later parsed view describe the replacement.
Preserved unknown extensions survive unrelated directive updates. Assigning a
parsed response CacheControl value binds a usable response view.

Range and ContentRange values model HTTP byte ranges. A satisfiable Range can
project against a representation length. `Response.content_range` may itself
be a public ContentRange object; its text is the wire representation and
reparsing that text recovers the same meaning. Invalid triples fail.

Entity-tag collections support strong, weak, wildcard, containment, and match
semantics. If-Range represents a tag or date partition. Parser objects and
conditional response decisions agree on the same validator meaning.

## WSGI execution and decorators

Calling a Response as WSGI invokes `start_response` with status and ordered
headers and returns the body iterable. Relative Location values become
appropriate for the request URI. HEAD preserves GET representation metadata
while emitting no body.

`Request.call_application` returns status, headers, and application iterable.
When the app supplies `exc_info`, the catch option controls whether the
original exception is re-raised or captured; the captured form includes that
extra value. `get_response` and `send` wrap the same public result in the
request's ResponseClass. A failed call does not poison a corrected call.

`wsgify` supports request-taking callable and WSGI forms, preserves the
undecorated callable, binds descriptors, and respects documented RequestClass
and call overrides without leaking them between instances. Returning `None`
uses `request.response`, including cookies and headers already placed there.
Middleware mode supplies the wrapped application in the documented position
and isolates wrapper instances.

## Conditional and range responses

When explicitly enabled, conditional Response behavior evaluates eligible
methods, entity tags, If-Modified-Since, ranges, and If-Range against its
representation. Matching cache validators may produce 304 with appropriate
entity-header filtering and no body. A later ordinary or nonmatching request
can still obtain the complete representation. This contract does not require
Response conditional handling for If-Unmodified-Since.

A satisfiable single known-length byte range on an eligible successful
representation produces 206, inclusive Content-Range, matching length, and
selected bytes. An unsatisfiable range produces the public range-error status.
Malformed, multiple, wrong-method, unknown-length, or otherwise ineligible
ranges follow their documented ordinary/error partition without destructively
slicing the source.

If-Range permits the range only when its strong tag or date condition matches;
otherwise the complete representation is returned. Status, headers, body, and
parsed header values stay coherent.

## HTTP exceptions and middleware

Public HTTP exceptions derive safe status/title/representation meaning from
their class, and `status_map` relates covered concrete codes to classes.
Content negotiation supports HTML, plain text, and JSON representations of the
same meaning. HTML escapes unsafe markup; plain text may strip markup; JSON
may expose the detail inside a message field. Exact layout and prose are not
prescribed.

Redirect and header-bearing exceptions reject CR/LF injection before unsafe
headers are published. A corrected safe value remains usable afterward.

Raised HTTP exceptions act as WSGI responses and are converted by `wsgify` and
`HTTPExceptionMiddleware` at documented boundaries. Unrelated application
exceptions are not flattened into success. `HTTPExceptionMiddleware` covers
an HTTP exception raised by the initial application call; it does not promise
to catch an exception raised only during later iterable consumption. Through
the public `exc_info` boundary it preserves the exception status and does not
poison a later successful call.

## Static applications

`FileApp` exposes file bytes, content type and length, modification metadata,
and conditional behavior. Its request-level callable returns a WSGI-capable
response application; invoking that application, direct WSGI iteration, and
`Request.get_response` describe the same file. Range and date validators
compose without making a later ordinary read return a stale slice.

`DirectoryApp` selects resources only within its configured directory and
implements documented file, missing, directory/index, redirect, and traversal
policy. A refusal or miss does not change the base used by a later valid
request.

File responses are lazy streams until consumed. Once a response body is
consumed into its byte projection, that Response owns those bytes. A later
request after file change or deletion reflects the current filesystem while
the consumed earlier Response stays stable. No unrelated global file cache may
publish stale success.

## Cookies and serializers

Cookie construction returns safe Set-Cookie values with name/value, path,
domain, expiry/max-age, secure, HTTP-only, SameSite, and comment policy.
`None` represents client deletion. Invalid supported-policy values fail
without publishing a partial cookie.

Response cookie operations append, overwrite same-name values as documented,
delete client cookies, remove response cookies, and preserve unrelated
headers. Cookie profiles bind request reading to response header creation and
support domain fan-out. Calling `source.merge_cookies(destination)` adds the
source Response's Set-Cookie values to the destination Response, or wraps a
WSGI application to add them, without removing unrelated destination cookies.

JSON serializers exchange UTF-8 JSON bytes. Base64 serializers use URL-safe
encoding and reject malformed input. Signed serializers authenticate their
serialized bytes and reject malformed or altered payloads. Failure does not
make corrected later input fail, and distinct secrets or salts remain
isolated.

Signed cookie profiles carry structured values through a response Set-Cookie
header into a later Request. Missing or tampered input produces the documented
missing/invalid result instead of an unauthenticated value; a corrected cookie
is subsequently accepted.

## Date and HTML helpers

Public date parsing returns UTC datetimes for supported HTTP dates and a safe
missing result for empty or unparsable input. Serialization and delta helpers
accept documented date/time/numeric forms and reject unsupported types. The
result represents the same instant or whole-second delta within HTTP-date
precision.

HTML escaping returns empty text for `None`, honors public `__html__`, converts
other values to text, and safely escapes unsafe markup and non-ASCII text as
documented.

## Cross-surface consistency

Across covered operations:

1. public raw header/list/body state and typed properties describe one
   effective state at their documented ownership boundary;
2. parser values used in a decision agree with resulting status, headers, and
   body;
3. direct callable, WSGI, decorator, middleware, and reconstructed Response
   views describe the same operation;
4. failures may have documented product effects but do not publish unsafe
   partial headers or leak request, response, iterator, directory, serializer,
   or wrapper state into corrected later work; and
5. restoring a previous public value restores its meaning without stale state
   outside the expressly documented lazy/cache boundaries.

## Out of scope

The contract excludes real sockets, DNS, TLS, proxies, exact diagnostic prose,
exact HTML templates, private and underscored members, internal caches and
descriptors, parser stages, platform-specific filesystem formatting,
wall-clock races, and behavior not stated through a covered public operation
or observable WSGI/filesystem effect.
