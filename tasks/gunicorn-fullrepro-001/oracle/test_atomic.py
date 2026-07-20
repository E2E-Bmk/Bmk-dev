import os
import sys
import threading

import pytest

from gunicorn.app.base import BaseApplication
from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.config import Config, KNOWN_SETTINGS
from gunicorn.ctl import ControlClient
from gunicorn.ctl.client import ControlClientError
from gunicorn.dirty import (
    DirtyApp,
    DirtyClient,
    DirtyConnectionError,
    DirtyError,
    StashError,
    StashKeyNotFoundError,
    StashTableNotFoundError,
    close_dirty_client,
    close_dirty_client_async,
    get_dirty_client,
    get_dirty_client_async,
)
from gunicorn.dirty.errors import DirtyNoWorkersAvailableError
from gunicorn.errors import ConfigError


class MinimalBaseApplication(BaseApplication):
    def load_config(self):
        pass

    def load(self):
        return object()


def _set_argv(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["gunicorn-test", *args])


def _write_config(path, **settings):
    lines = []
    for key, value in settings.items():
        lines.append(f"{key} = {value!r}\n")
    path.write_text("".join(lines))
    return str(path)


def test_config_known_settings_are_available_and_validated():
    cfg = Config()

    assert {setting.name for setting in KNOWN_SETTINGS}
    assert cfg.workers == 1
    assert cfg.bind == ["127.0.0.1:8000"]

    cfg.set("workers", "4")
    assert cfg.workers == 4

    with pytest.raises(ValueError):
        cfg.set("workers", -1)

    with pytest.raises(AttributeError):
        cfg.set("not_a_gunicorn_setting", "value")


def test_config_boolean_and_callable_validation():
    cfg = Config()

    cfg.set("preload_app", "true")
    assert cfg.preload_app is True
    cfg.set("preload_app", "false")
    assert cfg.preload_app is False

    def post_request(worker, req, environ, resp):
        return (worker, req, environ, resp)

    cfg.set("post_request", post_request)
    assert cfg.post_request("w", "r", "e", "p") == ("w", "r", "e", "p")

    with pytest.raises(ValueError):
        cfg.set("preload_app", "not-bool")

    with pytest.raises(TypeError):
        cfg.set("post_request", lambda worker: None)


def test_config_forwarded_allow_ips_parsing_and_rejection():
    cfg = Config()

    assert cfg.forwarded_allow_ips == ["127.0.0.1", "::1"]

    cfg.set("forwarded_allow_ips", "127.0.0.1,192.0.2.1")
    assert cfg.forwarded_allow_ips == ["127.0.0.1", "192.0.2.1"]

    cfg.set("forwarded_allow_ips", "*")
    assert cfg.forwarded_allow_ips == ["*"]

    cfg.set("forwarded_allow_ips", "")
    assert cfg.forwarded_allow_ips == []

    with pytest.raises(ValueError):
        cfg.set("forwarded_allow_ips", "127.0.0")


def test_base_application_wsgi_callable_is_cached():
    app = MinimalBaseApplication(usage="usage", prog="gunicorn-test")

    first = app.wsgi()
    second = app.wsgi()

    assert first is second


def test_wsgi_application_direct_cli_target_wins_over_config_wsgi_app(monkeypatch, tmp_path):
    cfg_path = _write_config(tmp_path / "gunicorn.conf.py", wsgi_app="from_config:app")

    _set_argv(monkeypatch, "--config", cfg_path, "from_cli:app")
    app = WSGIApplication(usage="usage", prog="gunicorn-test")

    assert app.app_uri == "from_cli:app"


def test_wsgi_application_uses_config_wsgi_app_when_cli_target_is_absent(monkeypatch, tmp_path):
    cfg_path = _write_config(tmp_path / "gunicorn.conf.py", wsgi_app="from_config:app")

    _set_argv(monkeypatch, "--config", cfg_path)
    app = WSGIApplication(usage="usage", prog="gunicorn-test")

    assert app.app_uri == "from_config:app"


def test_wsgi_application_requires_an_application_target(monkeypatch, tmp_path):
    cfg_path = _write_config(tmp_path / "gunicorn.conf.py", workers=2)

    _set_argv(monkeypatch, "--config", cfg_path)
    with pytest.raises(SystemExit):
        WSGIApplication(usage="usage", prog="gunicorn-test")


def test_cli_arguments_override_gunicorn_cmd_args(monkeypatch):
    monkeypatch.setenv("GUNICORN_CMD_ARGS", "--workers=4")
    _set_argv(monkeypatch, "--workers", "3", "app:application")

    app = WSGIApplication(usage="usage", prog="gunicorn-test")

    assert app.cfg.workers == 3


def test_direct_cli_config_file_wins_over_env_config_file(monkeypatch, tmp_path):
    env_cfg = _write_config(tmp_path / "env_conf.py", proc_name="from_env", wsgi_app="env:app")
    cli_cfg = _write_config(tmp_path / "cli_conf.py", proc_name="from_cli", wsgi_app="cli:app")

    monkeypatch.setenv("GUNICORN_CMD_ARGS", f"--config={env_cfg}")
    _set_argv(monkeypatch, "--config", cli_cfg)
    app = WSGIApplication(usage="usage", prog="gunicorn-test")

    assert app.cfg.proc_name == "from_cli"
    assert app.app_uri == "cli:app"


def test_dirty_configuration_values_and_validation():
    cfg = Config()

    cfg.set("dirty_apps", ["myapp.ml:Model", "myapp.cache:Cache:1"])
    cfg.set("dirty_workers", 2)
    cfg.set("dirty_threads", 4)
    cfg.set("dirty_timeout", 0)
    cfg.set("dirty_graceful_timeout", 60)

    assert cfg.dirty_apps == ["myapp.ml:Model", "myapp.cache:Cache:1"]
    assert cfg.dirty_workers == 2
    assert cfg.dirty_threads == 4
    assert cfg.dirty_timeout == 0
    assert cfg.dirty_graceful_timeout == 60

    with pytest.raises(ValueError):
        cfg.set("dirty_workers", -1)


def test_dirty_hook_settings_accept_matching_callables_and_reject_invalid_arity():
    cfg = Config()
    calls = []

    def on_dirty_starting(arbiter):
        calls.append(("starting", arbiter))

    def dirty_post_fork(arbiter, worker):
        calls.append(("post_fork", arbiter, worker))

    cfg.set("on_dirty_starting", on_dirty_starting)
    cfg.set("dirty_post_fork", dirty_post_fork)

    cfg.on_dirty_starting("arbiter")
    cfg.dirty_post_fork("arbiter", "worker")

    assert calls == [("starting", "arbiter"), ("post_fork", "arbiter", "worker")]

    with pytest.raises(TypeError):
        cfg.set("on_dirty_starting", lambda: None)


def test_dirty_app_dispatches_public_actions_and_persists_instance_state():
    class CounterApp(DirtyApp):
        def __init__(self):
            self.total = 0

        def add(self, value):
            self.total += value
            return self.total

    app = CounterApp()

    assert app("add", 2) == 2
    assert app("add", 5) == 7


def test_dirty_app_rejects_missing_and_underscore_prefixed_actions():
    class App(DirtyApp):
        def public(self):
            return "ok"

        def _private(self):
            return "not public"

    app = App()

    assert app("public") == "ok"
    with pytest.raises(ValueError):
        app("missing")
    with pytest.raises(ValueError):
        app("_private")


def test_dirty_app_worker_limit_attribute_is_inherited_or_overridden():
    class DefaultApp(DirtyApp):
        pass

    class LimitedApp(DirtyApp):
        workers = 2

    assert DirtyApp.workers is None
    assert DefaultApp().workers is None
    assert LimitedApp().workers == 2


def test_dirty_client_execute_reports_connection_failure():
    client = DirtyClient("/path/that/does/not/exist.sock", timeout=0.01)

    with pytest.raises(DirtyConnectionError):
        client.execute("app:Model", "predict", {"x": 1})


def test_dirty_client_getter_uses_thread_local_client_and_close_resets(monkeypatch):
    monkeypatch.setenv("GUNICORN_DIRTY_SOCKET", "/tmp/gunicorn-dirty-test.sock")
    close_dirty_client()

    client1 = get_dirty_client()
    client2 = get_dirty_client()
    close_dirty_client()
    client3 = get_dirty_client()

    assert client1 is client2
    assert client3 is not client1

    close_dirty_client()


def test_dirty_client_getter_is_thread_local(monkeypatch):
    monkeypatch.setenv("GUNICORN_DIRTY_SOCKET", "/tmp/gunicorn-dirty-test.sock")
    clients = []

    def collect_client():
        clients.append(get_dirty_client())
        close_dirty_client()

    threads = [threading.Thread(target=collect_client) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(clients) == 2
    assert clients[0] is not clients[1]


def test_dirty_client_getter_requires_socket_configuration(monkeypatch):
    monkeypatch.delenv("GUNICORN_DIRTY_SOCKET", raising=False)
    close_dirty_client()

    with pytest.raises(DirtyError):
        get_dirty_client()


@pytest.mark.asyncio
async def test_async_dirty_client_getter_reuses_context_client_and_close_is_idempotent(monkeypatch):
    monkeypatch.setenv("GUNICORN_DIRTY_SOCKET", "/tmp/gunicorn-dirty-test.sock")
    await close_dirty_client_async()

    client1 = await get_dirty_client_async()
    client2 = await get_dirty_client_async()
    await close_dirty_client_async()
    await close_dirty_client_async()

    assert client1 is client2

    await close_dirty_client_async()


def test_dirty_no_workers_error_preserves_app_path_and_base_type():
    error = DirtyNoWorkersAvailableError("myapp:HeavyModel")

    assert error.app_path == "myapp:HeavyModel"
    assert isinstance(error, DirtyError)


def test_stash_errors_preserve_table_and_key_details():
    missing_table = StashTableNotFoundError("sessions")
    missing_key = StashKeyNotFoundError("sessions", "user:1")

    assert isinstance(missing_table, StashError)
    assert missing_table.table_name == "sessions"
    assert isinstance(missing_key, StashError)
    assert missing_key.table_name == "sessions"
    assert missing_key.key == "user:1"


def test_control_client_send_command_reports_missing_socket():
    client = ControlClient("/path/that/does/not/exist.sock", timeout=0.01)

    with pytest.raises(ControlClientError):
        client.send_command("show workers")


def test_control_client_context_manager_reports_connection_failure():
    client = ControlClient("/path/that/does/not/exist.sock", timeout=0.01)

    with pytest.raises(ControlClientError):
        with client:
            raise AssertionError("context body must not run")


def test_control_client_close_is_idempotent():
    client = ControlClient("/tmp/gunicorn-control-test.sock", timeout=0.01)

    client.close()
    client.close()
