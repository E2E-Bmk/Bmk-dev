from __future__ import annotations

import logging

import pytest

import dramatiq
from dramatiq import Worker
from dramatiq.brokers.stub import StubBroker
from dramatiq.rate_limits.backends import StubBackend as RateLimitStubBackend
from dramatiq.results.backends import StubBackend as ResultStubBackend


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): atomic dependencies")
    config.addinivalue_line(
        "markers",
        "suppress_logs(*names): expected logger output already covered by behavioral assertions",
    )


@pytest.fixture(autouse=True)
def suppress_marked_logs(request):
    marker = request.node.get_closest_marker("suppress_logs")
    if marker is None:
        yield
        return
    loggers = [logging.getLogger(name) for name in marker.args]
    previous = [logger.disabled for logger in loggers]
    for logger in loggers:
        logger.disabled = True
    try:
        yield
    finally:
        for logger, disabled in zip(loggers, previous):
            logger.disabled = disabled


@pytest.fixture
def stub_broker():
    broker = StubBroker()
    broker.emit_after("process_boot")
    dramatiq.set_broker(broker)
    yield broker
    broker.flush_all()
    broker.close()


@pytest.fixture
def stub_worker(stub_broker):
    worker = Worker(stub_broker, worker_timeout=25, worker_threads=1)
    worker.start()
    yield worker
    worker.stop()


@pytest.fixture
def result_backend():
    return ResultStubBackend(namespace="spec-results", use_namespace_prefix_keys=True)


@pytest.fixture
def rate_limiter_backend():
    return RateLimitStubBackend()
