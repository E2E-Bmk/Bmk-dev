# MiniURLUtils Public Product Packet

## Overview

Build `miniurlutils.py`, a dependency-free Python module for parsing, editing, and serializing URLs. It is inspired by mature URL utility libraries and should feel like a small standard-library-friendly toolkit.

The module must be importable from the solution directory:

```python
from miniurlutils import URL, QueryParamDict, parse_url, find_all_links, URLParseError
```

Use only the Python standard library.

## Feature Set

The product has six feature modules:

1. URL parsing.
2. Mutable `URL` object state and serialization.
3. Ordered repeated query parameters.
4. Relative navigation and normalization.
5. Link extraction into URL objects.
6. Error behavior and recovery.

These modules are intentionally state-dependent. Parsed components feed `URL` attributes; `URL` attributes and `QueryParamDict` mutations feed serialization; normalized paths affect later relative navigation; extracted links become mutable `URL` objects; and failed parses should not corrupt later operations in the same process.

## Global Invariants

The following invariants define system correctness:

- Missing URL components such as absent scheme, absent authority, and absent host should be represented consistently across parsing, object construction, and serialization.
- User info, host authority, port, path, query, and fragment must remain distinct even when full serialization combines them.
- Query parameter order and repeated-key semantics must remain coherent after `add`, assignment, sorting, URL attachment, and serialization.
- `normalize()` mutates only the target URL object and its effects should be visible to later `navigate()` calls.
- `find_all_links()` returns real `URL` objects whose later query mutations and serialization follow the same rules as directly constructed URLs.
- Malformed inputs should raise useful exceptions without poisoning later valid parsing or object mutation.

## Parsing

`parse_url(text)` returns a dictionary describing a URL:

- `scheme`
- `_netloc_sep`, usually `"//"` when an authority separator was present
- `authority`
- `path`
- `query`
- `fragment`
- `username`
- `password`
- `family`, for IP address family when detectable
- `host`
- `port`

It should handle absolute URLs, scheme-relative URLs (`//host/path`), URLs without a scheme, IPv4/IPv6 host syntax, optional user info, optional ports, queries, and fragments.

Malformed URLs should raise `URLParseError` or another meaningful `ValueError` subclass. Exact message text is not public API.

## URL Object

`URL(text)` parses a URL into a mutable object. Public attributes/properties should include:

- `scheme`
- `host`
- `path`
- `path_parts`
- `query_params`
- `fragment`
- `username`
- `password`
- `port`
- `uses_netloc`

`str(url)` and `url.to_text()` should serialize the current state. Serialization should preserve the important structure of the original URL while applying any edits made to the object.

`URL.from_parts(...)` builds a URL from components such as scheme, host, path parts, query params, and fragment.

`url.get_authority()` returns the serialized host authority portion, including port when present.

`url.navigate(relative)` resolves a relative or absolute URL reference from the current URL and returns a new `URL`.

`url.normalize()` normalizes the object in place where practical: lower-case scheme/host, remove default ports, resolve `.` / `..` path segments, and normalize common percent-encoded path segments. It may return `None` like many in-place Python methods.

## QueryParamDict

`QueryParamDict` is an ordered query-parameter container that supports repeated keys.

Required behavior:

- construct from pairs or parse with `QueryParamDict.from_text(query_string)`;
- preserve insertion order for repeated keys;
- decode percent escapes and `+` spaces when parsing;
- represent bare parameters as `None`;
- `add(key, value)` appends another value for a key;
- assigning `q[key] = value` replaces existing values for that key;
- `getlist(key)` returns all values for that key;
- `items(multi=True)` returns repeated key/value pairs;
- `to_text()` serializes back to a query string;
- `sorted()` returns a sorted copy.

## Link Extraction

`find_all_links(text)` returns a list of `URL` objects found in plain text. It should recognize common `http://` and `https://` URLs, stop before surrounding sentence punctuation, and ignore email addresses that are not URLs.

## Non-Goals

Do not implement every URL standard edge case. Do not implement HTML parsing, network requests, or browser behavior. The goal is a practical compatibility subset with robust parsing, mutation, query-param, and serialization behavior.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time with short executable snippets.
- System tests exercise interactions across at least two modules. They inspect final dictionaries, URL object state, serialized URLs, ordered query parameters, navigation results, link-derived URL objects, and recovery after errors.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`

The benchmark does not inspect private implementation details.
