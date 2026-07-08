repo: webob
source_path: /Users/zijian/Bmk-dev-main/repo-pool/webob-main
commit: unknown (candidate directory is not a git repository)
src_loc: 10222 nonblank non-comment Python package lines; 14063 physical lines under src/webob/*.py
test_functions: 1380 pytest test functions
test_files: 25 Python files under tests/ (test_byterange.py, conftest.py, test_acceptparse.py, test_client_functional.py, test_response.py, test_misc.py, test_cookies.py, test_static.py, test_dec.py, test_in_wsgiref.py, test_etag.py, test_request.py, test_etag_nose.py, test_datetime_utils.py, test_util.py, performance_test.py, test_multidict.py, test_compat.py, test_descriptors.py, test_cookies_bw.py, test_client.py, test_exc.py, test_transcode.py, test_headers.py, test_cachecontrol.py)
dominant_test_styles: pytest unit tests with heavy direct assertions and parametrization, plus local WSGI/socket integration tests via wsgiref; no snapshot/golden-output majority observed
public_docs: README.rst; docs/index.txt; docs/reference.txt; docs/api/request.txt; docs/api/response.txt; docs/api/multidict.txt; docs/api/static.txt; docs/api/cookies.txt; docs/doctests.py
core_fact_source: mutable WSGI environ dictionaries and response triples (status/headerlist/app_iter/body), plus file-system paths for static-file apps and structured header/cookie/multidict state
derived_views: Request/Response Python attributes; environ/headerlist/body/status mutations; serialized HTTP headers, cookies, URLs, ranges, and JSON/body bytes; WSGI app call/get_response/request-send results; FileApp/DirectoryApp responses over local files
external_deps: runtime has no mandatory service dependency; setup.py only adds legacy-cgi>=2.6 on Python >=3.13 and optionally simplejson if installed; tests use pytest/coverage/pytest-cov/pytest-xdist and local wsgiref servers; docs use Sphinx/pylons-sphinx-themes; isolation plan is to run tests offline and restrict functional tests to localhost fixtures
test_import_audit: clean - grep -rn "from webob\\._\\|import webob\\._" tests/ returned 0 matches, so 0/25 test files affected by private-module imports; note that several tests still import private symbols from public modules, e.g. webob.byterange._is_content_range_valid and function-local imports such as _request_uri/_get_multipart_boundary
docs_test_alignment: aligned - docs cover Request/Response, environ/header/body/status, URL, multidict, cookies, static app, and doctest examples for the same public Python API projections exercised by tests
contamination_note: webob@2.0.0dev0, released unreleased/date unknown from local CHANGES.txt and setup.py, relative to training cutoff: unknown
decision: keep
reason: Substantial pure-Python WSGI request/response library with documented public API behavior, clean private-module import pre-screen, local-only tests, and multiple public projections over shared environ/response/file/header facts.
risks: HTTP/WSGI/header/cookie parsing is a common and partially standards-shaped domain; current tree is 2.0.0dev0 with unreleased changes and unknown commit; some upstream tests exercise private helper symbols and would need filtering or public-behavior replacement in later stages; functional tests open localhost sockets and may need isolation controls.
