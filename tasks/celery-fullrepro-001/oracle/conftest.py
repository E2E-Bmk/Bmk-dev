from __future__ import annotations

import logging

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): integration tests depend on public atomic contracts",
    )
    for logger_name in ("celery.app.trace", "kombu.connection"):
        logging.getLogger(logger_name).disabled = True


def make_app(**changes):
    from celery import Celery

    app = Celery(
        "public_oracle",
        broker="memory://",
        backend="cache+memory://",
        set_as_current=False,
    )
    app.conf.update(
        task_always_eager=True,
        task_store_eager_result=True,
        result_extended=True,
        task_eager_propagates=False,
        **changes,
    )
    return app


def make_math_tasks(app):
    @app.task(name="oracle.add")
    def add(left, right):
        return left + right

    @app.task(name="oracle.multiply")
    def multiply(left, right):
        return left * right

    @app.task(name="oracle.collect")
    def collect(values):
        return list(values)

    return add, multiply, collect


def make_bound_task(app):
    @app.task(bind=True, name="oracle.bound")
    def bound(task, value):
        return {
            "task_name": task.name,
            "is_eager": task.request.is_eager,
            "value": value,
        }

    return bound


@pytest.fixture
def app():
    instance = make_app()
    yield instance
    instance.close()


@pytest.fixture
def math_tasks(app):
    return make_math_tasks(app)


@pytest.fixture
def bound_task(app):
    return make_bound_task(app)


__all__ = ["make_app", "make_bound_task", "make_math_tasks"]
