from __future__ import annotations

import json
from pathlib import Path


def connection_info(seed: int, generation=None):
    info = {
        "transport": "tcp",
        "ip": f"127.0.0.{seed}",
        "shell_port": 31000 + seed,
        "iopub_port": 32000 + seed,
        "stdin_port": 33000 + seed,
        "control_port": 34000 + seed,
        "hb_port": 35000 + seed,
        "key": f"key-{seed}".encode(),
        "signature_scheme": "hmac-sha256",
    }
    if generation is not None:
        info["generation"] = generation
    return info


def wire(session, msg_type="execute_request", *, content=None, metadata=None, parent=None, ident=None, buffers=()):
    message = session.msg(msg_type, content=content or {}, metadata=metadata or {}, parent=parent)
    frames = session.serialize(message, ident=ident)
    frames.extend(buffers)
    identities, core = session.feed_identities(frames)
    return message, identities, core


def transcript_message(msg_id, msg_type, session_id, *, parent_id="", generation=1, content=None, kernel_id="kernel-violet"):
    return {
        "header": {"msg_id": msg_id, "msg_type": msg_type, "session": session_id},
        "msg_id": msg_id,
        "msg_type": msg_type,
        "parent_header": {"msg_id": parent_id} if parent_id else {},
        "metadata": {},
        "content": dict(content or {}),
        "kernel_id": kernel_id,
        "connection_generation": generation,
        "request_generation": generation,
    }


class RecordingProvisioner:
    def __init__(self, identity="recording-provisioner"):
        self.identity = identity
        self.events = []
        self.allocated = set()

    def prepare(self, operation):
        self.events.append(("prepare", operation))
        self.allocated.add(operation)
        return {
            "participant": self.identity,
            "operation": operation,
            "lease": f"{self.identity}:{operation}:{len(self.events)}",
        }

    def commit(self, operation, status):
        self.events.append(("commit", operation, status))
        self.allocated.discard(operation)
        return {"participant": self.identity, "operation": operation, "status": status}

    def cleanup(self, operation):
        self.events.append(("cleanup", operation))
        self.allocated.discard(operation)


def write_kernel_spec(root: Path, name: str, display: str, *, provisioner=None):
    target = root / name
    target.mkdir(parents=True, exist_ok=True)
    metadata = {}
    if provisioner:
        metadata["kernel_provisioner"] = {"provisioner_name": provisioner}
    payload = {
        "argv": ["python", "-m", "kernel", "-f", "{connection_file}"],
        "display_name": display,
        "language": "python",
        "metadata": metadata,
        "env": {"EVALUATOR_COLOR": display.lower()},
    }
    (target / "kernel.json").write_text(json.dumps(payload), encoding="utf-8")
    return target


class FakeEntryPoint:
    group = "jupyter_client.kernel_provisioners"

    def __init__(self, name, value, cls):
        self.name = name
        self.value = value
        self._cls = cls

    def load(self):
        return self._cls


class EntryPoints(list):
    def select(self, *, group):
        return EntryPoints(item for item in self if item.group == group)


def dependency_digests(receipt):
    return set(receipt.dependencies)


def assert_carries(receipt, *prerequisites):
    expected = {item.digest for item in prerequisites}
    assert expected <= dependency_digests(receipt)
