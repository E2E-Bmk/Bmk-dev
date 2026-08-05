from __future__ import annotations

from datetime import datetime
import logging

import pytest
from redbird.repos import MemoryRepo

from rocketry import Rocketry


FIXED_MONDAY = datetime(2022, 8, 8, 9, 30, 0)
FIXED_SUNDAY = datetime(2022, 8, 7, 9, 30, 0)


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): document atomic coverage dependencies")


@pytest.fixture(autouse=True)
def keep_rocketry_logs_out_of_pytest_capture():
    logger = logging.getLogger("rocketry.task")
    old_propagate = logger.propagate
    logger.propagate = False
    try:
        yield
    finally:
        logger.propagate = old_propagate


def make_app(at: datetime = FIXED_MONDAY, **config) -> Rocketry:
    options = {"execution": "main", "time_func": lambda: at.timestamp()}
    options.update(config)
    return Rocketry(config=options, logger_repo=MemoryRepo())


def actions(task) -> list[str]:
    return [record["action"] for record in task.logger.filter_by().all()]


def task_records(task) -> list[dict]:
    return list(task.logger.filter_by().all())


def record_run_ids(task) -> set[str]:
    return {record["run_id"] for record in task_records(task)}
