# Public oracle tests for jupyter_client kernel protocol - integration and system workflow layers
# Spec2Repo generated public-API tests for jupyter_client
import json
import os
import signal
import subprocess
import sys
from queue import Empty
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import jupyter_client
from jupyter_client import KernelClient, KernelManager, find_connection_file, write_connection_file
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager, NoSuchKernel
from jupyter_client.session import Session
from traitlets import TraitError


def _connection_info(seed=0):
    return {
        "ip": "127.0.0.1",
        "transport": "tcp",
        "shell_port": 51001 + seed,
        "iopub_port": 51002 + seed,
        "stdin_port": 51003 + seed,
        "control_port": 51004 + seed,
        "hb_port": 51005 + seed,
        "key": b"stage3-key",
        "signature_scheme": "hmac-sha256",
    }


def _write_spec(parent, name, display_name="Example", metadata=None):
    resource = Path(parent, name)
    resource.mkdir()
    data = {"argv": [sys.executable, "-m", "example_kernel", "-f", "{connection_file}"], "display_name": display_name, "language": "python"}
    if metadata is not None:
        data["metadata"] = metadata
    (resource / "kernel.json").write_text(json.dumps(data), encoding="utf-8")
    return resource

@pytest.mark.parametrize("seed", range(4))
def test_client_loaded_from_connection_mapping_reports_same_values(seed):
    client = KernelClient()
    info = _connection_info(seed)
    client.load_connection_info(info)
    reported = client.get_connection_info()
    assert all(reported[key] == info[key] for key in ("ip", "transport", "shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))
    assert reported["key"] == b"stage3-key"

@pytest.mark.parametrize("seed", range(3))
def test_connection_file_can_be_written_then_loaded_by_client(seed):
    with TemporaryDirectory() as directory:
        path, _ = write_connection_file(os.path.join(directory, "kernel.json"), **_connection_info(seed))
        client = KernelClient()
        client.load_connection_file(path)
    reported = client.get_connection_info()
    assert reported["shell_port"] == _connection_info(seed)["shell_port"]
    assert reported["key"] == b"stage3-key"

@pytest.mark.parametrize("payload", [{"code": "1"}, {"cursor_pos": 0}, {"detail_level": 1}])
def test_session_serialization_round_trip_preserves_routing_and_content(payload):
    session = Session(key=b"auth")
    message = session.msg("execute_request", content=payload)
    identities, frames = session.feed_identities(session.serialize(message, ident=b"route"))
    decoded = session.deserialize(frames)
    assert identities == [b"route"]
    assert decoded["msg_id"] == message["msg_id"]
    assert decoded["content"] == payload

@pytest.mark.parametrize("name", ["alpha", "beta", "mixed-name"])
def test_kernelspec_discovery_and_lookup_share_resource_directory(name):
    with TemporaryDirectory() as directory:
        resource = _write_spec(directory, name, name.title())
        manager = KernelSpecManager(kernel_dirs=[directory])
        discovered = manager.find_kernel_specs()
        selected = manager.get_kernel_spec(name.upper())
    assert discovered[name] == str(resource)
    assert selected.resource_dir == str(resource)

@pytest.mark.parametrize("name", ["installed", "installed_two", "installed-three"])
def test_install_discover_and_remove_kernelspec_round_trip(name):
    with TemporaryDirectory() as directory:
        source = _write_spec(directory, "source")
        prefix = Path(directory, "prefix")
        manager = KernelSpecManager(kernel_dirs=[str(prefix / "share" / "jupyter" / "kernels")])
        installed = manager.install_kernel_spec(str(source), kernel_name=name, prefix=str(prefix))
        assert manager.find_kernel_specs()[name] == installed
        assert manager.get_kernel_spec(name).resource_dir == installed
        assert manager.remove_kernel_spec(name) == installed
    assert not os.path.exists(installed)

@pytest.mark.parametrize("name", ["priority-one", "priority-two", "priority-three"])
def test_first_kernelspec_directory_wins_duplicate_name(name):
    with TemporaryDirectory() as directory:
        first, second = Path(directory, "first"), Path(directory, "second")
        first.mkdir(); second.mkdir()
        expected = _write_spec(first, name, "First")
        _write_spec(second, name, "Second")
        manager = KernelSpecManager(kernel_dirs=[str(first), str(second)])
        assert manager.find_kernel_specs()[name] == str(expected)
        assert manager.get_kernel_spec(name).display_name == "First"

@pytest.mark.parametrize("allowed", [{"allowed"}, {"other"}, set()])
def test_allowed_kernelspecs_filters_discovery(allowed):
    with TemporaryDirectory() as directory:
        _write_spec(directory, "allowed")
        _write_spec(directory, "other")
        manager = KernelSpecManager(kernel_dirs=[directory])
        manager.allowed_kernelspecs = allowed
        names = set(manager.find_kernel_specs())
    if allowed:
        assert names & {"allowed", "other"} == allowed
    else:
        assert {"allowed", "other"} <= names

@pytest.mark.parametrize("name", ["missing", "unknown", "not-installed"])
def test_missing_kernelspec_raises_public_exception(name):
    with TemporaryDirectory() as directory:
        manager = KernelSpecManager(kernel_dirs=[directory])
        with pytest.raises(NoSuchKernel):
            manager.get_kernel_spec(name)

@pytest.mark.parametrize("seed", range(3))
def test_manager_connection_mapping_flows_to_created_client(seed):
    manager = KernelManager()
    info = _connection_info(seed)
    manager.load_connection_info(info)
    client = manager.client()
    reported = client.get_connection_info()
    assert reported["transport"] == info["transport"]
    assert reported["shell_port"] == info["shell_port"]
    assert reported["key"] == b"stage3-key"

@pytest.mark.parametrize("operation", ["interrupt_kernel", "signal_kernel"])
def test_manager_operations_without_kernel_raise_runtime_error(operation):
    manager = KernelManager()
    with pytest.raises(RuntimeError):
        if operation == "signal_kernel":
            manager.signal_kernel(signal.SIGTERM)
        else:
            manager.interrupt_kernel()

def test_disabled_transport_encryption_is_accepted():
    assert KernelManager(transport_encryption="disabled").transport_encryption == "disabled"

def test_unknown_transport_encryption_mode_is_rejected():
    with pytest.raises(TraitError):
        KernelManager(transport_encryption="not-a-mode")

def test_disabled_transport_encryption_writes_no_curve_keys():
    with TemporaryDirectory() as directory:
        manager = KernelManager(transport_encryption="disabled")
        manager.connection_file = os.path.join(directory, "kernel.json")
        manager.shell_port, manager.iopub_port, manager.stdin_port = 51001, 51002, 51003
        manager.control_port, manager.hb_port = 51004, 51005
        manager.write_connection_file()
        written = json.loads(Path(manager.connection_file).read_text(encoding="utf-8"))
    assert "curve_publickey" not in written
    assert "curve_secretkey" not in written

@pytest.mark.parametrize("module", ["jupyter_client.kernelspecapp", "jupyter_client.runapp", "jupyter_client.kernelapp"])
def test_documented_python_module_invocations_report_usage(module):
    completed = subprocess.run([sys.executable, "-m", module, "--help"], capture_output=True, text=True, timeout=15)
    assert completed.returncode == 0


def _workflow_connection_info():
    return {
        "transport": "tcp", "ip": "127.0.0.1",
        "shell_port": 59991, "iopub_port": 59992, "stdin_port": 59993,
        "control_port": 59994, "hb_port": 59995, "key": b"workflow-key",
        "signature_scheme": "hmac-sha256",
    }


def test_manager_client_keeps_loaded_workflow_connection_info():
    connection_info = _workflow_connection_info()
    manager = KernelManager()
    manager.load_connection_info(connection_info)
    client = manager.client()
    assert isinstance(client, jupyter_client.BlockingKernelClient)
    assert client.get_connection_info() == connection_info

def test_blocking_workflow_returns_request_id_before_empty_shell_reply():
    client = jupyter_client.BlockingKernelClient()
    client.load_connection_info(_workflow_connection_info())
    client.start_channels(shell=True, iopub=False, stdin=False, hb=False, control=False)
    try:
        request_id = client.execute("1 + 1")
        assert isinstance(request_id, str)
        assert request_id
        with pytest.raises(Empty):
            client.get_shell_msg(timeout=0)
    finally:
        client.stop_channels()

def test_workflow_start_with_unknown_kernel_fails_without_running_one():
    manager = KernelManager(kernel_name="definitely-not-an-installed-kernel-7f9c0b77")
    with pytest.raises(NoSuchKernel):
        manager.start_kernel()
    assert manager.has_kernel is False
