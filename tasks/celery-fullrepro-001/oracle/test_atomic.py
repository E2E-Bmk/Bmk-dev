from __future__ import annotations

from datetime import timedelta

import pytest

from conftest import make_app, make_math_tasks


def test_app_exposes_main_name_and_default_conf(app):
    assert app.main == "public_oracle"
    assert app.conf.task_always_eager is True
    assert app.conf.result_backend == "cache+memory://"


def test_app_constructor_applies_broker_and_backend_configuration():
    instance = make_app(broker_url="memory://custom", result_backend="cache+memory://")
    try:
        assert instance.conf.broker_url == "memory://custom"
        assert instance.conf.result_backend == "cache+memory://"
        assert instance.backend.as_uri() == "memory:///"
    finally:
        instance.close()


def test_conf_update_preserves_and_overrides_public_settings(app):
    app.conf.update(task_default_queue="priority", task_serializer="json")
    assert app.conf.task_default_queue == "priority"
    assert app.conf.task_serializer == "json"
    app.conf.update(task_default_queue="standard")
    assert app.conf.task_default_queue == "standard"


def test_add_defaults_accepts_a_mapping(app):
    app.add_defaults({"task_default_exchange": "events", "task_default_routing_key": "events.created"})
    assert app.conf.task_default_exchange == "events"
    assert app.conf.task_default_routing_key == "events.created"


def test_add_defaults_accepts_a_callable(app):
    app.add_defaults(lambda: {"task_default_priority": 4})
    assert app.conf.task_default_priority == 4


def test_config_from_cmdline_parses_typed_values(app):
    app.config_from_cmdline(
        ["task_default_queue=jobs", "task_always_eager=True", "worker_concurrency=3"]
    )
    assert app.conf.task_default_queue == "jobs"
    assert app.conf.task_always_eager is True
    assert app.conf.worker_concurrency == 3


def test_task_decorator_registers_a_named_task(app):
    @app.task(name="oracle.named")
    def named(value):
        return value

    assert named.name == "oracle.named"
    assert app.tasks["oracle.named"].name == named.name


def test_task_decorator_preserves_callable_metadata(app):
    @app.task(name="oracle.documented")
    def documented(value):
        """Return the value unchanged."""
        return value

    assert documented.__name__ == "documented"
    assert documented.__doc__ == "Return the value unchanged."


def test_task_decorator_accepts_execution_options(app):
    @app.task(
        name="oracle.routed",
        queue="reports",
        routing_key="reports.created",
        priority=6,
    )
    def routed():
        return "ok"

    assert routed.queue == "reports"
    assert routed.routing_key == "reports.created"
    assert routed.priority == 6


def test_task_registry_contains_only_registered_public_task_names(app):
    add, multiply, _ = make_math_tasks(app)
    names = {add.name, multiply.name}
    assert names.issubset(set(app.tasks))
    assert app.tasks["oracle.add"].name == add.name


def test_direct_task_call_executes_inline(math_tasks):
    add, _, _ = math_tasks
    assert add(2, 5) == 7


def test_delay_returns_successful_eager_result(math_tasks):
    add, _, _ = math_tasks
    result = add.delay(4, 8)
    assert result.get() == 12
    assert result.successful()
    assert result.ready()


def test_apply_returns_eager_result_with_success_state(math_tasks):
    add, _, _ = math_tasks
    result = add.apply(args=(3, 9))
    assert result.result == 12
    assert result.state == "SUCCESS"
    assert result.status == "SUCCESS"


def test_apply_async_uses_explicit_task_id(math_tasks):
    add, _, _ = math_tasks
    result = add.apply_async(args=(6, 7), task_id="atomic-add-001")
    assert result.id == "atomic-add-001"
    assert result.get() == 13


def test_bound_task_sees_eager_request_context(bound_task):
    result = bound_task.delay("payload")
    assert result.get() == {
        "task_name": "oracle.bound",
        "is_eager": True,
        "value": "payload",
    }


def test_task_signature_contains_task_args_kwargs_and_options(math_tasks):
    add, _, _ = math_tasks
    sig = add.signature(args=(2,), kwargs={"right": 3}, options={"priority": 5})
    assert sig.task == "oracle.add"
    assert sig.args == (2,)
    assert sig.kwargs == {"right": 3}
    assert sig.options["priority"] == 5


def test_signature_shortcut_creates_public_signature(math_tasks):
    add, _, _ = math_tasks
    sig = add.s(5, 6)
    assert sig.task == "oracle.add"
    assert sig.args == (5, 6)
    assert sig.kwargs == {}


def test_signature_merge_prepends_args_and_overlays_kwargs(math_tasks):
    add, _, _ = math_tasks
    sig = add.signature(args=(2,), kwargs={"right": 3})
    merged = sig.clone(args=(1,), kwargs={"extra": "kept"})
    assert merged.args == (1, 2)
    assert merged.kwargs == {"right": 3, "extra": "kept"}


def test_signature_set_returns_self_with_updated_options(math_tasks):
    add, _, _ = math_tasks
    sig = add.s(1, 2).set(queue="fast", priority=7)
    assert sig.options["queue"] == "fast"
    assert sig.options["priority"] == 7


def test_immutable_signature_rejects_new_arguments(math_tasks):
    add, _, _ = math_tasks
    sig = add.s(2, 3).set(immutable=True)
    merged = sig.clone(args=(9,))
    assert merged.args == (2, 3)


def test_signature_clone_does_not_mutate_original_options(math_tasks):
    add, _, _ = math_tasks
    original = add.s(2, 3)
    clone = original.clone(priority=4)
    assert "priority" not in original.options
    assert clone.options["priority"] == 4


def test_signature_round_trip_from_mapping(math_tasks):
    add, _, _ = math_tasks
    source = dict(add.s(2, 3).set(queue="jobs"))
    restored = add.app.signature(source)
    assert restored.task == "oracle.add"
    assert restored.args == (2, 3)
    assert restored.options["queue"] == "jobs"


def test_signature_serializes_as_a_plain_mapping(math_tasks):
    add, _, _ = math_tasks
    payload = add.s(2, 3).__json__()
    assert payload["task"] == "oracle.add"
    assert payload["args"] == (2, 3)
    assert payload["kwargs"] == {}


def test_task_apply_async_preserves_routing_metadata_in_signature(math_tasks):
    add, _, _ = math_tasks
    sig = add.s(1, 2).set(queue="priority", routing_key="math.add", priority=8)
    assert sig.options == {
        "queue": "priority",
        "routing_key": "math.add",
        "priority": 8,
    }


def test_eager_success_result_exposes_metadata(math_tasks):
    add, _, _ = math_tasks
    result = add.apply_async(args=(1, 2), task_id="atomic-success-001")
    assert result._cache["task_id"] == "atomic-success-001"
    assert result._cache["status"] == "SUCCESS"
    assert result._cache["result"] == 3


def test_eager_failure_result_records_failure_state(app):
    @app.task(name="oracle.fail")
    def fail():
        raise ValueError("known failure")

    result = fail.apply_async(task_id="atomic-failure-001")
    assert result.failed()
    assert result.state == "FAILURE"
    assert isinstance(result.result, ValueError)


def test_failed_result_get_can_suppress_propagation(app):
    @app.task(name="oracle.fail-no-propagate")
    def fail():
        raise ValueError("known failure")

    result = fail.apply_async(task_id="atomic-failure-002")
    assert isinstance(result.get(propagate=False), ValueError)


def test_failed_result_get_propagates_by_default(app):
    @app.task(name="oracle.fail-propagate")
    def fail():
        raise ValueError("known failure")

    result = fail.apply_async(task_id="atomic-failure-003")
    with pytest.raises(ValueError):
        result.get()


def test_eager_result_revoke_changes_state(math_tasks):
    add, _, _ = math_tasks
    result = add.delay(1, 1)
    result.revoke()
    assert result.state == "REVOKED"
    assert result.ready()


def test_async_result_reads_stored_eager_metadata(app, math_tasks):
    add, _, _ = math_tasks
    add.apply_async(args=(4, 5), task_id="atomic-stored-001")
    result = app.AsyncResult("atomic-stored-001")
    assert result.state == "SUCCESS"
    assert result.get() == 9


def test_ignore_result_avoids_a_stored_backend_value(app):
    @app.task(name="oracle.ignored", ignore_result=True)
    def ignored():
        return "not stored"

    eager = ignored.apply_async(task_id="atomic-ignored-001")
    fetched = app.AsyncResult("atomic-ignored-001")
    assert eager.get() == "not stored"
    assert fetched.state == "PENDING"


def test_state_sets_classify_ready_and_exception_states():
    from celery.states import EXCEPTION_STATES, FAILURE, PENDING, READY_STATES, SUCCESS

    assert SUCCESS in READY_STATES
    assert FAILURE in READY_STATES
    assert FAILURE in EXCEPTION_STATES
    assert PENDING not in READY_STATES


def test_state_precedence_orders_success_above_started():
    from celery.states import STARTED, SUCCESS, state

    assert state(STARTED) < state(SUCCESS)
    assert state("PROGRESS") > state(STARTED)
    assert state(SUCCESS) > state("PROGRESS")


def test_group_signature_exposes_member_signatures(math_tasks):
    add, multiply, _ = math_tasks
    canvas_group = __import__("celery").group(add.s(1, 2), multiply.s(3, 4))
    assert canvas_group.subtask_type == "group"
    assert [sig.task for sig in canvas_group.tasks] == ["oracle.add", "oracle.multiply"]


def test_chain_signature_exposes_ordered_tasks(math_tasks):
    add, multiply, _ = math_tasks
    canvas_chain = __import__("celery").chain(add.s(1, 2), multiply.s())
    assert canvas_chain.subtask_type == "chain"
    assert [sig.task for sig in canvas_chain.tasks] == ["oracle.add", "oracle.multiply"]


def test_chord_signature_exposes_header_and_body(math_tasks):
    add, _, collect = math_tasks
    canvas_chord = __import__("celery").chord([add.s(1, 2), add.s(3, 4)], collect.s())
    assert canvas_chord.subtask_type == "chord"
    assert len(canvas_chord.tasks) == 2
    assert canvas_chord.body.task == "oracle.collect"


def test_group_apply_returns_group_result(math_tasks):
    from celery import group

    add, multiply, _ = math_tasks
    result = group(add.s(1, 2), multiply.s(3, 4)).apply()
    assert list(result.get()) == [3, 12]
    assert result.ready()


def test_chain_apply_returns_final_eager_result(math_tasks):
    from celery import chain

    add, multiply, _ = math_tasks
    result = chain(add.s(1, 2), multiply.s(4)).apply()
    assert result.get() == 12


def test_chord_length_hint_counts_header_tasks(math_tasks):
    from celery import chord

    add, _, collect = math_tasks
    canvas_chord = chord([add.s(1, 2), add.s(3, 4)], collect.s())
    assert len(canvas_chord.tasks) == 2


def test_periodic_task_projection_records_signature_and_schedule(app, math_tasks):
    from celery.schedules import crontab

    add, _, _ = math_tasks
    key = app.add_periodic_task(
        crontab(minute=0, hour=6),
        add.s(1, 2),
        name="oracle-morning-add",
    )
    entry = app.conf.beat_schedule[key]
    assert key == "oracle-morning-add"
    assert entry["task"] == "oracle.add"
    assert entry["args"] == (1, 2)
    assert isinstance(entry["schedule"], crontab)


def test_task_request_execution_options_are_publicly_projected(bound_task):
    result = bound_task.apply_async(
        args=("value",),
        task_id="atomic-request-001",
        headers={"tenant": "alpha"},
    )
    assert result.get()["value"] == "value"
    assert result.id == "atomic-request-001"
