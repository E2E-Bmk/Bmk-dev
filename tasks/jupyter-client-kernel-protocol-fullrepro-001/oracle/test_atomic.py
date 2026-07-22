# Public oracle tests for jupyter_client kernel protocol - atomic layer
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


from conftest import _connection_info, _write_spec

@pytest.mark.parametrize("name", [
    "KernelClient", "BlockingKernelClient", "AsyncKernelClient", "KernelManager",
    "AsyncKernelManager", "KernelProvisionerBase", "LocalProvisioner",
])
def test_root_kernel_surface_is_importable(name):
    exported = getattr(jupyter_client, name)
    assert exported is not None
    assert isinstance(exported, type)
    assert exported.__name__ == name

@pytest.mark.parametrize("name", ["KernelConnectionInfo", "find_connection_file", "write_connection_file"])
def test_connection_helpers_are_available_at_both_public_paths(name):
    from jupyter_client import connect

    assert getattr(jupyter_client, name) is getattr(connect, name)

@pytest.mark.parametrize("seed", range(4))
def test_write_connection_file_preserves_explicit_connection_values(seed):
    with TemporaryDirectory() as directory:
        path, written = write_connection_file(os.path.join(directory, "kernel.json"), **_connection_info(seed))
        on_disk = json.loads(Path(path).read_text(encoding="utf-8"))
    assert on_disk == written
    assert on_disk["key"] == "stage3-key"
    assert all(on_disk[key] == _connection_info(seed)[key] for key in ("ip", "transport", "shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))

@pytest.mark.parametrize("query", ["kernel.json", "kernel", "kern*"])
def test_find_connection_file_returns_matching_absolute_path(query):
    with TemporaryDirectory() as directory:
        expected = Path(directory, "kernel.json")
        expected.write_text("{}", encoding="utf-8")
        found = find_connection_file(query, path=[directory])
    assert found == str(expected)
    assert os.path.isabs(found)

def test_find_connection_file_raises_for_missing_file():
    with TemporaryDirectory() as directory:
        with pytest.raises(OSError):
            find_connection_file("not-present.json", path=[directory])

@pytest.mark.parametrize("content", [{}, {"code": "1 + 1"}, {"silent": True}])
def test_session_msg_has_public_message_shape(content):
    message = Session().msg("execute_request", content=content, metadata={"origin": "test"})
    assert {"header", "parent_header", "metadata", "content", "msg_id", "msg_type"} == set(message)
    assert message["msg_type"] == "execute_request"
    assert message["content"] == content
    assert message["metadata"]["origin"] == "test"

@pytest.mark.parametrize("message_type", ["execute_request", "kernel_info_request", "complete_request"])
def test_session_headers_have_independent_message_ids(message_type):
    session = Session()
    first = session.msg_header(message_type)
    second = session.msg_header(message_type)
    assert first["msg_type"] == message_type
    assert first["session"] == second["session"]
    assert first["msg_id"] != second["msg_id"]

def test_session_with_empty_key_serializes_empty_signature():
    session = Session(key=b"")
    frames = session.serialize(session.msg("execute_request"))
    assert frames[1] == b""

def test_session_rejects_invalid_signature():
    session = Session(key=b"auth")
    frames = session.serialize(session.msg("execute_request"))
    frames[1] = b"not-a-signature"
    with pytest.raises(ValueError):
        session.deserialize(frames[1:])

@pytest.mark.parametrize("display_name", ["Example", "Python Example", "Example 3"])
def test_kernelspec_from_resource_dir_has_serializable_public_fields(display_name):
    with TemporaryDirectory() as directory:
        resource = _write_spec(directory, "example", display_name)
        spec = KernelSpec.from_resource_dir(str(resource))
    exported = spec.to_dict()
    assert exported["argv"][-1] == "{connection_file}"
    assert exported["display_name"] == display_name
    assert exported["language"] == "python"
    assert json.loads(spec.to_json()) == exported

@pytest.mark.parametrize("bad_name", ["has space", "ünicode", "bad/name"])
def test_install_kernel_spec_rejects_invalid_name(bad_name):
    with TemporaryDirectory() as directory:
        source = _write_spec(directory, "source")
        manager = KernelSpecManager(kernel_dirs=[])
        with pytest.raises(ValueError):
            manager.install_kernel_spec(str(source), kernel_name=bad_name, prefix=directory)

def test_install_kernel_spec_rejects_user_and_prefix_together():
    with TemporaryDirectory() as directory:
        source = _write_spec(directory, "source")
        with pytest.raises(ValueError):
            KernelSpecManager(kernel_dirs=[]).install_kernel_spec(str(source), user=True, prefix=directory)

# --- composition fix additions (2026-07-20) ---

def test_write_connection_file_selects_ports_and_ip_when_unspecified():
    with TemporaryDirectory() as directory:
        path, written = write_connection_file(os.path.join(directory, "kernel.json"), key=b"auto-key")
        on_disk = json.loads(Path(path).read_text(encoding="utf-8"))
    assert written["ip"]
    assert all(written[name] > 0 for name in ("shell_port", "iopub_port", "stdin_port", "control_port", "hb_port"))
    assert on_disk == written

def test_write_connection_file_without_fname_creates_temporary_json_file():
    path, written = write_connection_file(key=b"temp-key")
    try:
        on_disk = json.loads(Path(path).read_text(encoding="utf-8"))
    finally:
        os.remove(path)
    assert written["transport"] == "tcp"
    assert on_disk["transport"] == "tcp"
    assert on_disk["signature_scheme"] == "hmac-sha256"
    assert on_disk["key"] == "temp-key"

def test_session_msg_defaults_content_and_parent_to_empty_mappings():
    message = Session().msg("kernel_info_request")
    assert message["content"] == {}
    assert message["parent_header"] == {}

def test_session_msg_records_parent_header():
    session = Session()
    parent = session.msg("execute_request")
    reply = session.msg("execute_reply", parent=parent)
    assert reply["parent_header"]["msg_id"] == parent["header"]["msg_id"]
    assert reply["parent_header"]["msg_type"] == "execute_request"

def test_session_serialize_places_identities_before_delimiter_and_signature():
    session = Session(key=b"")
    frames = session.serialize(session.msg("execute_request"), ident=[b"route-a", b"route-b"])
    assert frames[0] == b"route-a"
    assert frames[1] == b"route-b"
    assert frames[3] == b""

def test_kernelspec_from_resource_dir_parses_env_and_metadata_values():
    with TemporaryDirectory() as directory:
        resource = Path(directory, "envspec")
        resource.mkdir()
        data = {
            "argv": [sys.executable, "-m", "example_kernel", "-f", "{connection_file}"],
            "display_name": "Env Example",
            "language": "python",
            "env": {"EXAMPLE_FLAG": "on"},
            "metadata": {"tag": "value"},
        }
        (resource / "kernel.json").write_text(json.dumps(data), encoding="utf-8")
        exported = KernelSpec.from_resource_dir(str(resource)).to_dict()
    assert exported["env"] == {"EXAMPLE_FLAG": "on"}
    assert exported["metadata"] == {"tag": "value"}

def test_kernelspec_to_dict_exposes_documented_field_names():
    with TemporaryDirectory() as directory:
        resource = _write_spec(directory, "fields")
        exported = KernelSpec.from_resource_dir(str(resource)).to_dict()
    assert set(exported) >= {"argv", "env", "display_name", "language", "interrupt_mode", "metadata", "kernel_protocol_version"}

def test_install_kernel_spec_derives_lowercase_name_from_source_directory():
    with TemporaryDirectory() as directory:
        source = _write_spec(directory, "MixedCase")
        prefix = Path(directory, "prefix")
        installed = KernelSpecManager(kernel_dirs=[]).install_kernel_spec(str(source), prefix=str(prefix))
        assert Path(installed).name == "mixedcase"
        assert installed == str(prefix / "share" / "jupyter" / "kernels" / "mixedcase")
