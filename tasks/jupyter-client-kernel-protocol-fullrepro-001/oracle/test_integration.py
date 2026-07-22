# Public oracle tests for jupyter_client kernel protocol - integration and system workflow layers
# Spec2Repo generated public-API tests for jupyter_client
import asyncio
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
from jupyter_client.provisioning import KernelProvisionerFactory, LocalProvisioner
from jupyter_client.session import Session
from traitlets import TraitError


from conftest import _connection_info, _write_spec

@pytest.mark.parametrize("seed", range(4))
def test_client_loaded_from_connection_mapping_reports_same_values(seed):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    client = KernelClient()
    info = _connection_info(seed)
    client.load_connection_info(info)
    reported = client.get_connection_info()
    assert all(reported[key] == info[key] for key in ("ip", "transport", "shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))
    assert reported["key"] == b"stage3-key"

@pytest.mark.parametrize("seed", range(3))
def test_connection_file_can_be_written_then_loaded_by_client(seed):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    with TemporaryDirectory() as directory:
        path, _ = write_connection_file(os.path.join(directory, "kernel.json"), **_connection_info(seed))
        client = KernelClient()
        client.load_connection_file(path)
    reported = client.get_connection_info()
    assert reported["shell_port"] == _connection_info(seed)["shell_port"]
    assert reported["key"] == b"stage3-key"

@pytest.mark.parametrize("payload", [{"code": "1"}, {"cursor_pos": 0}, {"detail_level": 1}])
def test_session_serialization_round_trip_preserves_routing_and_content(payload):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    session = Session(key=b"auth")
    message = session.msg("execute_request", content=payload)
    identities, frames = session.feed_identities(session.serialize(message, ident=b"route"))
    decoded = session.deserialize(frames)
    assert identities == [b"route"]
    assert decoded["msg_id"] == message["msg_id"]
    assert decoded["content"] == payload

@pytest.mark.parametrize("name", ["alpha", "beta", "mixed-name"])
def test_kernelspec_discovery_and_lookup_share_resource_directory(name):
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    with TemporaryDirectory() as directory:
        resource = _write_spec(directory, name, name.title())
        manager = KernelSpecManager(kernel_dirs=[directory])
        discovered = manager.find_kernel_specs()
        selected = manager.get_kernel_spec(name.upper())
    assert discovered[name] == str(resource)
    assert selected.resource_dir == str(resource)

@pytest.mark.parametrize("name", ["installed", "installed_two", "installed-three"])
def test_install_discover_and_remove_kernelspec_round_trip(name):
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
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
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
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
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
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
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    with TemporaryDirectory() as directory:
        manager = KernelSpecManager(kernel_dirs=[directory])
        with pytest.raises(NoSuchKernel):
            manager.get_kernel_spec(name)

@pytest.mark.parametrize("seed", range(3))
def test_manager_connection_mapping_flows_to_created_client(seed):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
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
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    manager = KernelManager()
    with pytest.raises(RuntimeError):
        if operation == "signal_kernel":
            manager.signal_kernel(signal.SIGTERM)
        else:
            manager.interrupt_kernel()

def test_disabled_transport_encryption_is_accepted():
    """Seam: config interaction — encryption settings select compatible storage backends."""
    assert KernelManager(transport_encryption="disabled").transport_encryption == "disabled"

def test_unknown_transport_encryption_mode_is_rejected():
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    with pytest.raises(TraitError):
        KernelManager(transport_encryption="not-a-mode")

def test_disabled_transport_encryption_writes_no_curve_keys():
    """Seam: config interaction — encryption settings select compatible storage backends."""
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
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
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
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    connection_info = _workflow_connection_info()
    manager = KernelManager()
    manager.load_connection_info(connection_info)
    client = manager.client()
    assert isinstance(client, jupyter_client.BlockingKernelClient)
    assert client.get_connection_info() == connection_info

def test_blocking_workflow_returns_request_id_before_empty_shell_reply():
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
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
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    manager = KernelManager(kernel_name="definitely-not-an-installed-kernel-7f9c0b77")
    with pytest.raises(NoSuchKernel):
        manager.start_kernel()
    assert manager.has_kernel is False

# --- composition fix additions (2026-07-20) ---

def test_get_all_specs_reports_resource_dir_and_serializable_spec():
    """Seam: state consistency — cooperating public APIs observe the same underlying state."""
    with TemporaryDirectory() as directory:
        resource = _write_spec(directory, "reportable", "Reportable")
        manager = KernelSpecManager(kernel_dirs=[directory])
        everything = manager.get_all_specs()
    assert everything["reportable"]["resource_dir"] == str(resource)
    assert everything["reportable"]["spec"]["display_name"] == "Reportable"
    assert everything["reportable"]["spec"]["language"] == "python"

def test_get_all_specs_omits_spec_that_cannot_be_loaded():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    with TemporaryDirectory() as directory:
        _write_spec(directory, "good", "Good")
        broken = Path(directory, "broken")
        broken.mkdir()
        (broken / "kernel.json").write_text("{not json", encoding="utf-8")
        manager = KernelSpecManager(kernel_dirs=[directory])
        everything = manager.get_all_specs()
    assert set(everything) == {"good"}
    assert everything["good"]["spec"]["display_name"] == "Good"

def test_find_kernel_specs_omits_directories_without_kernel_json():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    with TemporaryDirectory() as directory:
        resource = _write_spec(directory, "complete")
        Path(directory, "incomplete").mkdir()
        manager = KernelSpecManager(kernel_dirs=[directory])
        discovered = manager.find_kernel_specs()
    assert discovered["complete"] == str(resource)
    assert "incomplete" not in discovered

def test_find_kernel_specs_normalizes_directory_names_to_lowercase():
    """Seam: state consistency — listing, metadata, and content APIs agree on filesystem state."""
    with TemporaryDirectory() as directory:
        resource = _write_spec(directory, "MixedCase", "Mixed")
        manager = KernelSpecManager(kernel_dirs=[directory])
        discovered = manager.find_kernel_specs()
    assert discovered["mixedcase"] == str(resource)
    assert "MixedCase" not in discovered

def test_module_level_kernelspec_helpers_expose_manager_behavior(monkeypatch):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    from jupyter_client.kernelspec import find_kernel_specs as find_specs
    from jupyter_client.kernelspec import get_kernel_spec as get_spec

    with TemporaryDirectory() as directory:
        kernels = Path(directory, "kernels")
        kernels.mkdir()
        resource = _write_spec(kernels, "moduledemo", "Module Demo")
        monkeypatch.setenv("JUPYTER_PATH", directory)
        assert find_specs()["moduledemo"] == str(resource)
        assert get_spec("moduledemo").display_name == "Module Demo"
        with pytest.raises(NoSuchKernel):
            get_spec("missing-kernel-3f6d2b91")

def test_cloned_sessions_from_connection_info_share_identity_with_independent_digests():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    client = KernelClient()
    client.load_connection_info(_connection_info(7))
    first = client.get_connection_info(session=True)["session"]
    second = client.get_connection_info(session=True)["session"]
    assert first.key == b"stage3-key"
    assert second.key == b"stage3-key"
    assert first.msg_header("kernel_info_request")["session"] == second.msg_header("kernel_info_request")["session"]
    frames = first.serialize(first.msg("execute_request", content={"code": "1"}))
    _, wire = first.feed_identities(frames)
    assert first.deserialize(wire)["content"] == {"code": "1"}
    assert second.deserialize(wire)["content"] == {"code": "1"}
    with pytest.raises(ValueError):
        first.deserialize(wire)

def test_manager_write_connection_file_then_cleanup_removes_it():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    with TemporaryDirectory() as directory:
        manager = KernelManager()
        manager.connection_file = os.path.join(directory, "kernel.json")
        manager.write_connection_file()
        written = json.loads(Path(manager.connection_file).read_text(encoding="utf-8"))
        assert written["shell_port"] == manager.shell_port
        assert written["ip"] == manager.ip
        manager.cleanup_connection_file()
        assert not os.path.exists(manager.connection_file)

def test_manager_written_connection_file_configures_blocking_client():
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    with TemporaryDirectory() as directory:
        manager = KernelManager()
        manager.connection_file = os.path.join(directory, "kernel.json")
        manager.write_connection_file()
        client = jupyter_client.BlockingKernelClient()
        client.load_connection_file(manager.connection_file)
        reported = client.get_connection_info()
    assert manager.shell_port > 0
    assert reported["shell_port"] == manager.shell_port
    assert reported["hb_port"] == manager.hb_port
    assert reported["ip"] == manager.ip

def test_blocking_client_loads_connection_file_from_configured_path():
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    with TemporaryDirectory() as directory:
        path, written = write_connection_file(os.path.join(directory, "kernel.json"), **_connection_info(8))
        client = jupyter_client.BlockingKernelClient(connection_file=path)
        client.load_connection_file()
        reported = client.get_connection_info()
    assert reported["shell_port"] == written["shell_port"]
    assert reported["transport"] == "tcp"
    assert reported["key"] == b"stage3-key"

def test_session_round_trip_exposes_trailing_buffers_as_memoryviews():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    session = Session(key=b"buffer-key")
    message = session.msg("execute_request", content={"code": "1"})
    _, wire = session.feed_identities(session.serialize(message))
    decoded = session.deserialize([*wire, b"payload-bytes"])
    assert decoded["content"] == {"code": "1"}
    assert len(decoded["buffers"]) == 1
    assert isinstance(decoded["buffers"][0], memoryview)
    assert bytes(decoded["buffers"][0]) == b"payload-bytes"

def test_install_kernel_spec_replaces_existing_destination():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    with TemporaryDirectory() as directory:
        prefix = Path(directory, "prefix")
        manager = KernelSpecManager(kernel_dirs=[str(prefix / "share" / "jupyter" / "kernels")])
        one, two = Path(directory, "one"), Path(directory, "two")
        one.mkdir(); two.mkdir()
        first_source = _write_spec(one, "replaced", "First Install")
        second_source = _write_spec(two, "replaced", "Second Install")
        first_install = manager.install_kernel_spec(str(first_source), prefix=str(prefix))
        assert manager.get_kernel_spec("replaced").display_name == "First Install"
        second_install = manager.install_kernel_spec(str(second_source), prefix=str(prefix))
        assert second_install == first_install
        assert manager.get_kernel_spec("replaced").display_name == "Second Install"

def test_provisioner_factory_availability_follows_kernelspec_metadata():
    """Seam: protocol handoff — adjacent protocol layers exchange connection or message state."""
    factory = KernelProvisionerFactory.instance()
    default_spec = KernelSpec()
    assert factory.is_provisioner_available(default_spec) is True
    missing_spec = KernelSpec(metadata={"kernel_provisioner": {"provisioner_name": "missing-provisioner-2b9d4c17"}})
    assert factory.is_provisioner_available(missing_spec) is False
    with pytest.raises(ModuleNotFoundError):
        factory.create_provisioner_instance("kid-0", missing_spec, parent=None)

def test_local_provisioner_persists_and_restores_provisioner_info():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    provisioner = LocalProvisioner(kernel_id="kid-1")
    info = asyncio.run(provisioner.get_provisioner_info())
    assert info["kernel_id"] == "kid-1"
    payload = dict(info)
    payload["kernel_id"] = "kid-2"
    payload["connection_info"] = {"ip": "127.0.0.1", "shell_port": 51201}
    restored = LocalProvisioner()
    asyncio.run(restored.load_provisioner_info(payload))
    assert restored.kernel_id == "kid-2"
    assert restored.connection_info["shell_port"] == 51201
    with pytest.raises(KeyError):
        asyncio.run(LocalProvisioner().load_provisioner_info({"connection_info": {}}))
