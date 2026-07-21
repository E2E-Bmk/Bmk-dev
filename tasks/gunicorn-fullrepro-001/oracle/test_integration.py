import json
import os
import signal
import socket
import subprocess
import sys
import time

import pytest

from gunicorn import __version__, version_info
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.config import Config
from gunicorn.ctl import ControlClient
from gunicorn.ctl.client import ControlClientError
from gunicorn.dirty import (
    DirtyAppError,
    DirtyAppNotFoundError,
    DirtyConnectionError,
    DirtyError,
    DirtyProtocolError,
    DirtyTimeoutError,
    DirtyWorkerError,
)
from gunicorn.errors import AppImportError, ConfigError
from gunicorn.http2 import H2_MIN_VERSION, get_h2_version, is_http2_available


def _set_argv(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["gunicorn-test", *args])


def _write_app(tmp_path, body):
    app_file = tmp_path / "app.py"
    app_file.write_text(body)
    sys.modules.pop("app", None)
    return app_file


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(port, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.05)
    raise AssertionError(f"server on port {port} did not start")


def _http_request(port, path="/", headers=(), method="GET", body=b""):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        header_lines = "".join(f"{name}: {value}\r\n" for name, value in headers)
        if body:
            header_lines += f"Content-Length: {len(body)}\r\n"
        request = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\n{header_lines}Connection: close\r\n\r\n"
        sock.sendall(request.encode("ascii") + body)
        chunks = []
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
    return b"".join(chunks)


def _start_gunicorn(tmp_path, app_target, *extra_args):
    port = _free_port()
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(tmp_path) + (os.pathsep + existing if existing else "")
    cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "--bind",
        f"127.0.0.1:{port}",
        "--workers",
        "1",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
        "--log-level",
        "warning",
        *extra_args,
        app_target,
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        preexec_fn=os.setsid,
    )
    try:
        _wait_for_server(port)
    except Exception:
        stdout, stderr = proc.communicate(timeout=2)
        raise AssertionError(
            f"gunicorn failed to start\nstdout={stdout.decode(errors='replace')}\n"
            f"stderr={stderr.decode(errors='replace')}"
        )
    return proc, port


def _stop_process(proc):
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except OSError:
        proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except OSError:
            proc.kill()
        proc.wait(timeout=5)


def test_version_info_matches_public_version_string():
    assert isinstance(__version__, str)
    assert isinstance(version_info, tuple)
    assert tuple(int(part) for part in __version__.split(".")[: len(version_info)]) == version_info


def test_http2_capability_reports_installed_h2_version():
    available = is_http2_available()
    assert isinstance(available, bool)
    if available:
        version = get_h2_version()
        assert version is not None
        assert version >= H2_MIN_VERSION
    else:
        assert get_h2_version() is None


def test_config_principal_defaults_are_visible():
    cfg = Config()
    assert cfg.workers == 1
    assert cfg.worker_class
    assert cfg.threads == 1
    assert cfg.worker_connections == 1000
    assert cfg.timeout == 30
    assert cfg.graceful_timeout == 30
    assert cfg.keepalive == 2
    assert cfg.accesslog is None
    assert cfg.errorlog == "-"
    assert cfg.control_socket_disable is False


def test_config_accepts_public_protocol_selection():
    cfg = Config()
    cfg.set("protocol", "uwsgi")
    assert cfg.protocol == "uwsgi"


def test_config_control_socket_disable_uses_boolean_validation():
    cfg = Config()
    cfg.set("control_socket_disable", "true")
    assert cfg.control_socket_disable is True
    cfg.set("control_socket_disable", "false")
    assert cfg.control_socket_disable is False
    with pytest.raises(ValueError):
        cfg.set("control_socket_disable", "sometimes")


def test_config_dirty_and_runtime_timeouts_accept_zero_as_documented_disable():
    cfg = Config()
    cfg.set("timeout", 0)
    cfg.set("dirty_timeout", 0)
    assert cfg.timeout == 0
    assert cfg.dirty_timeout == 0


def test_config_request_limit_settings_reject_negative_values():
    cfg = Config()
    assert cfg.limit_request_line == 4094
    assert cfg.limit_request_fields == 100
    assert cfg.limit_request_field_size == 8190

    for name in ["limit_request_line", "limit_request_fields", "limit_request_field_size"]:
        with pytest.raises(ValueError):
            cfg.set(name, -1)


def test_config_reload_and_capture_output_use_boolean_validation():
    cfg = Config()
    cfg.set("reload", "true")
    cfg.set("capture_output", "true")
    assert cfg.reload is True
    assert cfg.capture_output is True

    cfg.set("reload", "false")
    cfg.set("capture_output", "false")
    assert cfg.reload is False
    assert cfg.capture_output is False

    with pytest.raises(ValueError):
        cfg.set("reload", "not-a-bool")


def test_wsgi_application_loads_default_application_name(monkeypatch, tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    assert callable(app.load())


def test_wsgi_application_loads_named_callable(monkeypatch, tmp_path):
    _write_app(
        tmp_path,
        "def named(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'named']\n",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app:named")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    assert callable(app.load())


def test_wsgi_application_invokes_factory_with_literal_arguments(monkeypatch, tmp_path):
    _write_app(
        tmp_path,
        "def make_app(prefix, count=1):\n"
        "    def application(environ, start_response):\n"
        "        start_response('200 OK', [])\n"
        "        return [(prefix * count).encode()]\n"
        "    return application\n",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app:make_app('xy', count=2)")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    loaded = app.load()
    captured = {}

    def start_response(status, headers):
        captured["status"] = status

    assert list(loaded({}, start_response)) == [b"xyxy"]
    assert captured["status"] == "200 OK"


def test_wsgi_application_rejects_missing_callable(monkeypatch, tmp_path):
    _write_app(tmp_path, "value = 1\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app:missing")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    with pytest.raises(AppImportError):
        app.load()


def test_wsgi_application_rejects_non_callable_result(monkeypatch, tmp_path):
    _write_app(tmp_path, "def make_app():\n    return None\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app:make_app()")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    with pytest.raises(AppImportError):
        app.load()


def test_wsgi_application_rejects_non_literal_factory_argument(monkeypatch, tmp_path):
    _write_app(tmp_path, "def make_app(value):\n    return value\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app:make_app(not_a_literal)")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    with pytest.raises(AppImportError):
        app.load()


def test_wsgi_application_rejects_malformed_target_expression(monkeypatch, tmp_path):
    _write_app(tmp_path, "def application(environ, start_response):\n    return []\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app:make_app(")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    with pytest.raises(AppImportError):
        app.load()


def test_wsgi_application_rejects_non_simple_factory_reference(monkeypatch, tmp_path):
    _write_app(
        tmp_path,
        "class Factory:\n"
        "    def make(self):\n"
        "        def application(environ, start_response):\n"
        "            start_response('200 OK', [])\n"
        "            return [b'ok']\n"
        "        return application\n"
        "factory = Factory()\n",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    _set_argv(monkeypatch, "app:factory.make()")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")
    with pytest.raises(AppImportError):
        app.load()


def test_dirty_error_subclasses_preserve_base_type():
    for cls in [
        DirtyConnectionError,
        DirtyTimeoutError,
        DirtyWorkerError,
        DirtyAppError,
        DirtyAppNotFoundError,
        DirtyProtocolError,
    ]:
        assert issubclass(cls, DirtyError)


def test_dirty_app_not_found_error_is_catchable_as_dirty_error():
    try:
        raise DirtyAppNotFoundError("myapp:Missing")
    except DirtyError as exc:
        assert isinstance(exc, DirtyAppNotFoundError)


def test_control_client_error_is_raised_for_send_to_missing_socket():
    client = ControlClient("/tmp/definitely-missing-gunicorn-control.sock", timeout=0.01)
    with pytest.raises(ControlClientError):
        client.send_command("show config")


def test_python_module_help_exits_successfully():
    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    assert "usage:" in proc.stdout.lower()


def test_wsgiapp_module_help_exits_successfully():
    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn.app.wsgiapp", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0
    assert "usage:" in proc.stdout.lower()


def test_check_config_accepts_valid_wsgi_application(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config", "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    assert proc.returncode == 0


def test_check_config_rejects_missing_application_target(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    valid = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config", "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    assert valid.returncode == 0

    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )
    assert proc.returncode != 0


def test_check_config_rejects_invalid_setting_value(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    config_file = tmp_path / "bad_conf.py"
    config_file.write_text("workers = -1\n")
    valid = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config", "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    assert valid.returncode == 0

    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config", "--config", str(config_file), "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    assert proc.returncode != 0


def test_check_config_rejects_missing_explicit_config_file(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    valid = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config", "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    assert valid.returncode == 0

    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config", "--config", str(tmp_path / "missing.py"), "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    assert proc.returncode != 0


def test_check_config_ignores_unknown_python_config_names(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    config_file = tmp_path / "gunicorn.conf.py"
    config_file.write_text("workers = 2\nnot_a_gunicorn_setting = 'ignored'\n")
    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--check-config", "--config", str(config_file), "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")},
    )
    assert proc.returncode == 0


def test_print_config_reports_direct_cli_precedence_over_environment_args(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    env = {**os.environ, "PYTHONPATH": str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    env["GUNICORN_CMD_ARGS"] = "--workers=2"
    proc = subprocess.run(
        [sys.executable, "-m", "gunicorn", "--print-config", "--workers", "3", "app:application"],
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        env=env,
    )
    assert proc.returncode == 0
    worker_lines = [line for line in proc.stdout.splitlines() if line.strip().startswith("workers")]
    assert worker_lines
    assert worker_lines[-1].rstrip().endswith("= 3")


def test_wsgi_server_returns_application_body(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    body = b'Hello from Gunicorn'\n"
        "    start_response('200 OK', [('Content-Length', str(len(body)))])\n"
        "    return [body]\n",
    )
    proc, port = _start_gunicorn(tmp_path, "app:application")
    try:
        response = _http_request(port)
    finally:
        _stop_process(proc)

    assert b"200 OK" in response
    assert b"Hello from Gunicorn" in response


def test_wsgi_server_exposes_path_query_and_scheme(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    body = f\"{environ['PATH_INFO']}|{environ['QUERY_STRING']}|{environ['wsgi.url_scheme']}\".encode()\n"
        "    start_response('200 OK', [('Content-Length', str(len(body)))])\n"
        "    return [body]\n",
    )
    proc, port = _start_gunicorn(tmp_path, "app:application", "--forwarded-allow-ips", "*")
    try:
        response = _http_request(port, "/demo/path?x=1", headers=[("X-Forwarded-Proto", "https")])
    finally:
        _stop_process(proc)

    assert b"/demo/path|x=1|https" in response


def test_wsgi_server_exposes_method_headers_and_body_length(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    body = f\"{environ['REQUEST_METHOD']}|{environ['HTTP_X_SAMPLE']}|{environ['CONTENT_LENGTH']}\".encode()\n"
        "    start_response('200 OK', [('Content-Length', str(len(body)))])\n"
        "    return [body]\n",
    )
    proc, port = _start_gunicorn(tmp_path, "app:application")
    try:
        response = _http_request(
            port,
            "/submit",
            headers=[("X-Sample", "visible")],
            method="POST",
            body=b"payload",
        )
    finally:
        _stop_process(proc)

    assert b"POST|visible|7" in response


def test_wsgi_server_ignores_forwarded_scheme_from_untrusted_peer(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    body = environ['wsgi.url_scheme'].encode()\n"
        "    start_response('200 OK', [('Content-Length', str(len(body)))])\n"
        "    return [body]\n",
    )
    proc, port = _start_gunicorn(tmp_path, "app:application", "--forwarded-allow-ips", "")
    try:
        response = _http_request(port, "/", headers=[("X-Forwarded-Proto", "https")])
    finally:
        _stop_process(proc)

    assert b"\r\n\r\nhttp" in response


def test_wsgi_server_reports_application_exception_as_server_error(tmp_path):
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    raise RuntimeError('boom')\n",
    )
    proc, port = _start_gunicorn(tmp_path, "app:application")
    try:
        response = _http_request(port)
    finally:
        _stop_process(proc)

    assert b"500 Internal Server Error" in response


def test_wsgi_server_closes_returned_iterable(tmp_path):
    marker = tmp_path / "closed.txt"
    _write_app(
        tmp_path,
        "MARKER = " + repr(str(marker)) + "\n"
        "class Body:\n"
        "    def __iter__(self):\n"
        "        yield b'close-aware'\n"
        "    def close(self):\n"
        "        open(MARKER, 'w').write('closed')\n"
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [('Content-Length', '11')])\n"
        "    return Body()\n",
    )
    proc, port = _start_gunicorn(tmp_path, "app:application")
    try:
        response = _http_request(port)
        deadline = time.time() + 5
        while time.time() < deadline and not marker.exists():
            time.sleep(0.05)
    finally:
        _stop_process(proc)

    assert b"close-aware" in response
    assert marker.read_text() == "closed"


def test_control_socket_show_config_reports_runtime_projection(tmp_path):
    control_socket = tmp_path / "gunicorn.ctl"
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    proc, port = _start_gunicorn(
        tmp_path,
        "app:application",
        "--control-socket",
        str(control_socket),
    )
    try:
        deadline = time.time() + 10
        while time.time() < deadline and not control_socket.exists():
            time.sleep(0.05)
        client = ControlClient(str(control_socket), timeout=2)
        config = client.send_command("show config")
        client.close()
    finally:
        _stop_process(proc)

    assert isinstance(config, dict)
    assert "workers" in json.dumps(config)


def test_control_socket_disable_prevents_socket_creation(tmp_path):
    control_socket = tmp_path / "disabled.ctl"
    _write_app(
        tmp_path,
        "def application(environ, start_response):\n"
        "    start_response('200 OK', [])\n"
        "    return [b'ok']\n",
    )
    proc, port = _start_gunicorn(
        tmp_path,
        "app:application",
        "--control-socket",
        str(control_socket),
        "--no-control-socket",
    )
    try:
        _http_request(port)
    finally:
        _stop_process(proc)

    assert not control_socket.exists()


def test_repeated_wsgi_requests_observe_same_running_service(tmp_path):
    _write_app(
        tmp_path,
        "counter = 0\n"
        "def application(environ, start_response):\n"
        "    global counter\n"
        "    counter += 1\n"
        "    body = str(counter).encode()\n"
        "    start_response('200 OK', [('Content-Length', str(len(body)))])\n"
        "    return [body]\n",
    )
    proc, port = _start_gunicorn(tmp_path, "app:application")
    try:
        first = _http_request(port)
        second = _http_request(port)
    finally:
        _stop_process(proc)

    assert b"\r\n\r\n1" in first
    assert b"\r\n\r\n2" in second
