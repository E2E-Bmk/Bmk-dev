from __future__ import annotations

from datetime import timedelta

from click.testing import CliRunner

import pytest

from conftest import make_app, make_math_tasks


@pytest.mark.depends_on("test_app_exposes_main_name_and_default_conf", "test_task_decorator_registers_a_named_task")
def test_configured_app_registers_and_executes_a_task(app):
    @app.task(name="workflow.configured")
    def configured(value):
        return {"queue": app.conf.task_default_queue, "value": value}

    app.conf.update(task_default_queue="workflow")
    result = configured.apply_async(args=("ready",), task_id="integration-config-001")
    assert result.get() == {"queue": "workflow", "value": "ready"}
    assert app.tasks["workflow.configured"].name == configured.name


@pytest.mark.depends_on("test_task_decorator_accepts_execution_options", "test_apply_async_uses_explicit_task_id")
def test_task_options_flow_into_eager_invocation(app):
    @app.task(name="workflow.options", queue="reports", priority=5)
    def options(value):
        return value

    signature = options.s("payload").set(routing_key="reports.created")
    result = signature.apply_async(task_id="integration-options-001")
    assert result.get() == "payload"
    assert options.queue == "reports"
    assert options.priority == 5
    assert signature.options["routing_key"] == "reports.created"


@pytest.mark.depends_on("test_bound_task_sees_eager_request_context", "test_eager_success_result_exposes_metadata")
def test_bound_task_workflow_returns_context_and_stored_result(bound_task, app):
    result = bound_task.apply_async(args=("workflow",), task_id="integration-bound-001")
    stored = app.AsyncResult("integration-bound-001")
    assert result.get()["is_eager"] is True
    assert stored.get()["task_name"] == "oracle.bound"
    assert stored.state == "SUCCESS"


@pytest.mark.depends_on("test_direct_task_call_executes_inline", "test_delay_returns_successful_eager_result")
def test_direct_and_delay_views_agree_on_task_value(math_tasks):
    add, _, _ = math_tasks
    assert add(10, 2) == add.delay(10, 2).get()


@pytest.mark.depends_on("test_signature_shortcut_creates_public_signature", "test_signature_set_returns_self_with_updated_options")
def test_signature_workflow_sets_options_then_executes(math_tasks):
    add, _, _ = math_tasks
    result = add.s(9, 3).set(queue="fast", priority=2).apply_async(
        task_id="integration-signature-001"
    )
    assert result.get() == 12
    assert result.state == "SUCCESS"


@pytest.mark.depends_on("test_signature_merge_prepends_args_and_overlays_kwargs", "test_signature_clone_does_not_mutate_original_options")
def test_cloned_signature_workflow_keeps_original_and_runs_clone(math_tasks):
    add, _, _ = math_tasks
    original = add.signature(args=(2, 3))
    clone = original.clone(priority=4)
    assert original.args == (2, 3)
    assert clone.args == (2, 3)
    assert clone.options["priority"] == 4
    assert clone.apply().get() == 5


@pytest.mark.depends_on("test_signature_round_trip_from_mapping", "test_signature_serializes_as_a_plain_mapping")
def test_serialized_signature_round_trip_executes(math_tasks):
    add, _, _ = math_tasks
    payload = add.s(7, 8).set(queue="serialized").__json__()
    restored = add.app.signature(payload)
    assert restored.apply().get() == 15
    assert restored.options["queue"] == "serialized"


@pytest.mark.depends_on("test_eager_failure_result_records_failure_state", "test_failed_result_get_can_suppress_propagation")
def test_failure_workflow_exposes_state_and_nonpropagating_value(app):
    @app.task(name="workflow.failure")
    def fail():
        raise LookupError("workflow failure")

    result = fail.delay()
    assert result.state == "FAILURE"
    assert isinstance(result.get(propagate=False), LookupError)


@pytest.mark.depends_on("test_failed_result_get_propagates_by_default", "test_eager_result_revoke_changes_state")
def test_failure_workflow_can_propagate_then_revoke_separate_result(app):
    @app.task(name="workflow.failure-propagate")
    def fail():
        raise RuntimeError("workflow failure")

    failed = fail.delay()
    with pytest.raises(RuntimeError):
        failed.get()
    revoked = fail.delay()
    revoked.revoke()
    assert revoked.state == "REVOKED"


@pytest.mark.depends_on("test_group_signature_exposes_member_signatures", "test_group_apply_returns_group_result")
def test_group_workflow_executes_distinct_member_tasks(math_tasks):
    from celery import group

    add, multiply, _ = math_tasks
    canvas_group = group(add.s(2, 3), multiply.s(4, 5))
    result = canvas_group.apply()
    assert list(result.get()) == [5, 20]
    assert len(result.results) == 2


@pytest.mark.depends_on("test_chain_signature_exposes_ordered_tasks", "test_chain_apply_returns_final_eager_result")
def test_chain_workflow_passes_previous_value_to_next_task(app):
    @app.task(name="workflow.seed")
    def seed():
        return 6

    @app.task(name="workflow.scale")
    def scale(value, factor):
        return value * factor

    from celery import chain

    result = chain(seed.s(), scale.s(7)).apply()
    assert result.get() == 42


@pytest.mark.depends_on("test_chord_signature_exposes_header_and_body", "test_chord_length_hint_counts_header_tasks")
def test_chord_workflow_collects_header_values(math_tasks):
    from celery import chord

    add, _, collect = math_tasks
    result = chord([add.s(1, 2), add.s(3, 4)], collect.s()).apply()
    assert result.get() == [3, 7]


@pytest.mark.depends_on("test_group_apply_returns_group_result", "test_chain_apply_returns_final_eager_result")
def test_group_then_aggregate_workflow_uses_group_result_values(app):
    @app.task(name="workflow.sum-values")
    def sum_values(values):
        return sum(values)

    @app.task(name="workflow.value")
    def value(number):
        return number

    from celery import chord

    result = chord([value.s(2), value.s(5), value.s(8)], sum_values.s()).apply()
    assert result.get() == 15


@pytest.mark.depends_on("test_group_signature_exposes_member_signatures", "test_chain_signature_exposes_ordered_tasks")
def test_nested_canvas_workflow_preserves_task_order(math_tasks):
    from celery import chain, group

    add, multiply, _ = math_tasks
    workflow = group(add.s(1, 1) | multiply.s(3), add.s(2, 2) | multiply.s(3))
    result = workflow.apply()
    assert result.get() == [6, 12]


@pytest.mark.depends_on("test_async_result_reads_stored_eager_metadata", "test_ignore_result_avoids_a_stored_backend_value")
def test_backend_workflow_distinguishes_stored_and_ignored_results(app):
    @app.task(name="workflow.stored")
    def stored():
        return "stored"

    @app.task(name="workflow.ignored", ignore_result=True)
    def ignored():
        return "ignored"

    stored.apply_async(task_id="integration-backend-stored")
    ignored.apply_async(task_id="integration-backend-ignored")
    assert app.AsyncResult("integration-backend-stored").get() == "stored"
    assert app.AsyncResult("integration-backend-ignored").state == "PENDING"


@pytest.mark.depends_on("test_eager_success_result_exposes_metadata", "test_task_registry_contains_only_registered_public_task_names")
def test_result_metadata_workflow_links_task_name_and_state(app):
    @app.task(name="workflow.metadata")
    def metadata():
        return {"ok": True}

    result = metadata.apply_async(task_id="integration-metadata-001")
    assert result._cache["name"] == "workflow.metadata"
    assert result._cache["status"] == "SUCCESS"
    assert app.tasks[result._cache["name"]].name == metadata.name


@pytest.mark.depends_on("test_state_sets_classify_ready_and_exception_states", "test_state_precedence_orders_success_above_started")
def test_state_workflow_classifies_success_failure_and_pending():
    from celery.states import FAILURE, PENDING, SUCCESS, state

    assert PENDING not in {"SUCCESS", "FAILURE"}
    assert state(SUCCESS) > state(FAILURE)
    assert FAILURE != SUCCESS


@pytest.mark.depends_on("test_periodic_task_projection_records_signature_and_schedule", "test_signature_shortcut_creates_public_signature")
def test_periodic_configuration_workflow_registers_named_schedule(app, math_tasks):
    from celery.schedules import schedule

    add, _, _ = math_tasks
    key = app.add_periodic_task(schedule(timedelta(seconds=30)), add.s(3, 4), name="integration-periodic")
    assert key in app.conf.beat_schedule
    assert app.conf.beat_schedule[key]["task"] == "oracle.add"
    assert app.conf.beat_schedule[key]["args"] == (3, 4)


@pytest.mark.depends_on("test_app_exposes_main_name_and_default_conf", "test_task_decorator_registers_a_named_task")
def test_cli_version_projection_is_deterministic():
    from celery.bin.celery import celery

    result = CliRunner().invoke(celery, ["--version"])
    assert result.exit_code == 0
    assert result.output.startswith("5.6.2")


@pytest.mark.depends_on("test_app_exposes_main_name_and_default_conf", "test_task_registry_contains_only_registered_public_task_names")
def test_cli_help_projection_lists_public_command_groups():
    from celery.bin.celery import celery

    result = CliRunner().invoke(celery, ["--help"])
    assert result.exit_code == 0
    assert "Commands" in result.output
    assert "worker" in result.output
    assert "result" in result.output


@pytest.mark.depends_on("test_state_sets_classify_ready_and_exception_states", "test_app_exposes_main_name_and_default_conf")
def test_cli_control_list_projection_is_service_free():
    from celery.bin.celery import celery

    result = CliRunner().invoke(celery, ["control", "--list"])
    assert result.exit_code == 0
    assert "Control Commands" in result.output
    assert "rate_limit" in result.output


@pytest.mark.depends_on("test_state_sets_classify_ready_and_exception_states", "test_app_exposes_main_name_and_default_conf")
def test_cli_inspect_list_projection_is_service_free():
    from celery.bin.celery import celery

    result = CliRunner().invoke(celery, ["inspect", "--list"])
    assert result.exit_code == 0
    assert "Inspect Commands" in result.output
    assert "registered" in result.output


@pytest.mark.depends_on("test_task_request_execution_options_are_publicly_projected", "test_bound_task_sees_eager_request_context")
def test_bound_task_workflow_accepts_custom_headers_without_changing_value(bound_task):
    result = bound_task.apply_async(
        args=("headered",),
        task_id="integration-headers-001",
        headers={"tenant": "blue"},
    )
    assert result.get()["value"] == "headered"
    assert result.state == "SUCCESS"


@pytest.mark.depends_on("test_task_decorator_accepts_execution_options", "test_task_apply_async_preserves_routing_metadata_in_signature")
def test_routing_workflow_keeps_queue_key_and_executes_payload(app):
    @app.task(name="workflow.route", queue="mail", routing_key="mail.send")
    def route(payload):
        return payload.upper()

    signature = route.s("hello").set(priority=3)
    assert route.queue == "mail"
    assert route.routing_key == "mail.send"
    assert signature.apply().get() == "HELLO"


@pytest.mark.depends_on("test_add_defaults_accepts_a_mapping", "test_task_decorator_registers_a_named_task", "test_signature_set_returns_self_with_updated_options")
def test_default_routing_workflow_feeds_signature_and_eager_execution(app):
    app.add_defaults(
        {
            "task_default_queue": "bulk",
            "task_default_routing_key": "bulk.created",
        }
    )

    @app.task(name="workflow.default-route")
    def default_route(payload):
        return {"queue": app.conf.task_default_queue, "payload": payload}

    signature = default_route.s("created").set(routing_key=app.conf.task_default_routing_key)
    result = signature.apply_async(task_id="integration-default-route-001")
    assert result.get() == {"queue": "bulk", "payload": "created"}
    assert signature.options["routing_key"] == "bulk.created"
    assert app.tasks["workflow.default-route"].name == default_route.name
