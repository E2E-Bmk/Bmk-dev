"""Shared helpers for jupyter_client oracle tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path


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
