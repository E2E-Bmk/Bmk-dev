# Spec2Repo oracle shared fixtures for kombu-fullrepro-001

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic behaviors an integration test logically requires",
    )


def fresh_name(prefix: str) -> str:
    return f"s2r.{prefix}.{uuid4().hex}"


@pytest.fixture
def unique_name():
    return fresh_name


@pytest.fixture
def filesystem_transport_options(tmp_path):
    data_dir = tmp_path / "data"
    processed_dir = tmp_path / "processed"
    control_dir = tmp_path / "control"
    data_dir.mkdir()
    processed_dir.mkdir()
    control_dir.mkdir()
    return {
        "data_folder_in": str(data_dir),
        "data_folder_out": str(data_dir),
        "processed_folder": str(processed_dir),
        "control_folder": str(control_dir),
        "store_processed": True,
    }


def filesystem_file_counts(options: dict[str, str]) -> dict[str, int]:
    return {
        "data": len(list(Path(options["data_folder_in"]).iterdir())),
        "processed": len(list(Path(options["processed_folder"]).iterdir())),
    }


class RecordingChannel:
    no_ack_consumers = set()

    def __init__(self):
        self.calls = []

    def basic_ack(self, delivery_tag, multiple=False):
        self.calls.append(("ack", delivery_tag, multiple))

    def basic_reject(self, delivery_tag, requeue=False):
        self.calls.append(("reject", delivery_tag, requeue))
