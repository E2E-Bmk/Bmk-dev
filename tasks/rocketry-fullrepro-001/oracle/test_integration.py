from __future__ import annotations

import pytest

from rocketry import FuncTask
from rocketry.args import Arg, Config, FuncArg, Return, Session as SessionArg, SimpleArg, Task as TaskArg
from rocketry.conds import after_finish, after_success, daily, false, hourly, scheduler_cycles, succeeded, time_of_day, true, weekly

from conftest import FIXED_MONDAY, actions, make_app, record_run_ids


@pytest.mark.depends_on("test_direct_run_records_return_value_for_string_and_function_return_args")
@pytest.mark.depends_on("test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success")
def test_priority_pipeline_passes_return_between_two_tasks_in_one_scheduler_cycle():
    app = make_app()

    @app.task(true, name="extract", execution="main", priority=100)
    def extract():
        return "raw"

    @app.task(after_success("extract"), name="transform", execution="main", priority=10)
    def transform(value=Return("extract")):
        return value.upper()

    app.session.run("extract", "transform")
    assert app.session["extract"].status == "success"
    assert app.session["transform"].status == "success"
    assert Return("transform").get_value(task=app.session["transform"], session=app.session) == "RAW"


@pytest.mark.depends_on("test_function_parameter_arg_is_materialized_during_run")
@pytest.mark.depends_on("test_successful_direct_run_writes_run_and_success_log_actions")
def test_session_parameter_and_return_pipeline_produce_joined_payload():
    app = make_app()
    app.params(prefix="order")

    @app.param("sequence")
    def sequence():
        return "42"

    @app.task(true, name="make_key", execution="main", priority=100)
    def make_key(prefix=Arg("prefix"), sequence=Arg("sequence")):
        return f"{prefix}-{sequence}"

    @app.task(after_success("make_key"), name="label", execution="main", priority=10)
    def label(key=Return("make_key"), suffix=SimpleArg("ready")):
        return f"{key}:{suffix}"

    app.session.run("make_key", "label")
    assert Return("label").get_value(task=app.session["label"], session=app.session) == "order-42:ready"
    assert actions(app.session["make_key"]) == ["run", "success"]
    assert actions(app.session["label"]) == ["run", "success"]


@pytest.mark.depends_on("test_custom_condition_accepts_positional_arguments")
@pytest.mark.depends_on("test_time_of_day_between_uses_session_time_function")
def test_custom_condition_combines_with_fixed_time_window_to_gate_task():
    app = make_app()

    @app.cond()
    def contains_item(items, item):
        return item in items

    @app.task(time_of_day.between("09:00", "10:00") & contains_item({"north", "east"}, "north"), name="gated", execution="main")
    def gated():
        return "entered"

    task = app.session["gated"]
    assert task.start_cond.observe(task=task, session=app.session) is True
    app.session.run("gated", obey_cond=True)
    assert Return("gated").get_value(task=task, session=app.session) == "entered"


@pytest.mark.depends_on("test_custom_condition_can_receive_current_task_argument")
@pytest.mark.depends_on("test_meta_arguments_expose_session_task_and_config")
def test_task_meta_arguments_and_task_sensitive_condition_agree_on_current_task():
    app = make_app()

    @app.cond()
    def has_workflow_prefix(task=TaskArg()):
        return task.name.startswith("workflow_")

    @app.task(has_workflow_prefix, name="workflow_meta", execution="main")
    def workflow_meta(session=SessionArg(), task=TaskArg(), config=Config()):
        return session is app.session, task.name, config.execution

    app.session.run("workflow_meta", obey_cond=True)
    assert Return("workflow_meta").get_value(task=app.session["workflow_meta"], session=app.session) == (
        True,
        "workflow_meta",
        "main",
    )


@pytest.mark.depends_on("test_daily_condition_is_true_for_never_run_task_at_fixed_time")
@pytest.mark.depends_on("test_daily_condition_becomes_false_after_success_in_same_fixed_day")
def test_daily_task_runs_once_and_same_day_observation_prevents_second_due_state():
    app = make_app()

    @app.task(daily, name="daily_once", execution="main")
    def daily_once():
        return "done"

    task = app.session["daily_once"]
    assert daily.observe(task=task, session=app.session) is True
    app.session.run("daily_once", obey_cond=True)
    assert task.status == "success"
    assert daily.observe(task=task, session=app.session) is False


@pytest.mark.depends_on("test_log_records_share_run_id_between_run_and_success")
@pytest.mark.depends_on("test_task_logger_filter_counts_are_projected_by_action")
def test_two_successful_tasks_keep_separate_log_run_ids_and_action_counts():
    app = make_app()

    @app.task(true, name="alpha", execution="main")
    def alpha():
        return "a"

    @app.task(true, name="beta", execution="main")
    def beta():
        return "b"

    app.session.run("alpha", "beta")
    assert actions(app.session["alpha"]) == ["run", "success"]
    assert actions(app.session["beta"]) == ["run", "success"]
    assert record_run_ids(app.session["alpha"]).isdisjoint(record_run_ids(app.session["beta"]))


@pytest.mark.depends_on("test_after_success_condition_is_false_before_source_task_succeeds")
@pytest.mark.depends_on("test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success")
def test_downstream_condition_is_consumed_after_pipeline_task_runs():
    app = make_app()

    @app.task(true, name="source", execution="main", priority=100)
    def source():
        return "source"

    @app.task(after_success("source"), name="downstream", execution="main", priority=10)
    def downstream(value=Return("source")):
        return f"{value}:downstream"

    downstream_task = app.session["downstream"]
    assert downstream_task.start_cond.observe(task=downstream_task, session=app.session) is False
    app.session.run("source", "downstream")
    assert Return("downstream").get_value(task=downstream_task, session=app.session) == "source:downstream"
    assert downstream_task.start_cond.observe(task=downstream_task, session=app.session) is False


@pytest.mark.depends_on("test_simplearg_and_funcarg_are_task_level_values")
@pytest.mark.depends_on("test_direct_run_records_return_value_for_string_and_function_return_args")
def test_funcarg_simplearg_and_return_can_build_multistep_payload():
    app = make_app()

    @app.task(true, name="base", execution="main", priority=100)
    def base(left=SimpleArg("north"), right=FuncArg(lambda: "east")):
        return f"{left}-{right}"

    @app.task(after_success("base"), name="finish", execution="main", priority=10)
    def finish(value=Return("base"), suffix=SimpleArg("complete")):
        return f"{value}-{suffix}"

    app.session.run("base", "finish")
    assert Return("finish").get_value(task=app.session["finish"], session=app.session) == "north-east-complete"


@pytest.mark.depends_on("test_obey_cond_true_leaves_false_condition_task_unrun")
@pytest.mark.depends_on("test_one_cycle_scheduler_start_uses_public_shutdown_condition")
def test_one_cycle_scheduler_skips_false_condition_and_runs_true_condition():
    app = make_app(shut_cond=scheduler_cycles() >= 1)

    @app.task(false, name="blocked", execution="main")
    def blocked():
        return "blocked"

    @app.task(true, name="open", execution="main")
    def open_task():
        return "open"

    app.session.start()
    assert app.session.scheduler.n_cycles == 1
    assert app.session["blocked"].status is None
    assert app.session["open"].status == "success"


@pytest.mark.depends_on("test_succeeded_status_condition_observes_success_log_in_fixed_period")
@pytest.mark.depends_on("test_memory_repository_task_records_contain_stable_task_action_and_time_fields")
def test_status_condition_and_log_projection_share_same_success_fact():
    app = make_app()

    @app.task(true, name="source", execution="main")
    def source():
        return "source"

    task = app.session["source"]
    app.session.run("source")
    assert succeeded(task="source").today.observe(task=task, session=app.session) is True
    assert task.logger.filter_by(action="success").count() == 1
    assert actions(task) == ["run", "success"]


@pytest.mark.depends_on("test_task_decorator_returns_function_and_registers_lookup_by_name_and_function")
@pytest.mark.depends_on("test_successful_direct_run_updates_status_and_last_success_projection")
def test_decorated_function_lookup_status_and_return_are_consistent():
    app = make_app()

    @app.task(true, name="lookup_task", execution="main")
    def lookup_task():
        return "found"

    task = app.session[lookup_task]
    app.session.run("lookup_task")
    assert app.session["lookup_task"] is task
    assert task.status == "success"
    assert Return(lookup_task).get_value(task=task, session=app.session) == "found"


@pytest.mark.depends_on("test_weekly_condition_matches_fixed_weekday")
@pytest.mark.depends_on("test_session_level_arg_is_injected_during_direct_run")
def test_weekly_condition_and_session_parameter_drive_task_payload():
    app = make_app()
    app.params(region="north")

    @app.task(weekly.on("Monday"), name="weekly_payload", execution="main")
    def weekly_payload(region=Arg("region")):
        return f"{region}:{FIXED_MONDAY.strftime('%A')}"

    app.session.run("weekly_payload", obey_cond=True)
    assert Return("weekly_payload").get_value(task=app.session["weekly_payload"], session=app.session) == "north:Monday"


@pytest.mark.depends_on("test_hourly_after_matches_minute_second_inside_hour")
@pytest.mark.depends_on("test_task_logger_filter_counts_are_projected_by_action")
def test_hourly_window_task_runs_and_projects_log_counts():
    app = make_app()

    @app.task(hourly.after("15:00") & hourly.before("45:00"), name="windowed", execution="main")
    def windowed():
        return "inside"

    task = app.session["windowed"]
    app.session.run("windowed", obey_cond=True)
    assert task.status == "success"
    assert task.logger.filter_by(action="run").count() == 1
    assert Return("windowed").get_value(task=task, session=app.session) == "inside"


@pytest.mark.depends_on("test_condition_or_algebra_observes_any_true_branch")
@pytest.mark.depends_on("test_condition_inversion_flips_public_state")
def test_condition_algebra_selects_one_of_two_workflow_branches():
    app = make_app()

    @app.task((false | true) & ~false, name="branch", execution="main")
    def branch():
        return "selected"

    app.session.run("branch", obey_cond=True)
    assert app.session["branch"].status == "success"
    assert Return("branch").get_value(task=app.session["branch"], session=app.session) == "selected"


@pytest.mark.depends_on("test_custom_condition_observes_wrapped_function_result")
@pytest.mark.depends_on("test_session_level_arg_is_injected_during_direct_run")
def test_condition_closes_over_session_parameter_mutation_before_run():
    app = make_app()
    app.params(flag=True)

    @app.cond()
    def flag_is_enabled(session=SessionArg()):
        return session.parameters["flag"] is True

    @app.task(flag_is_enabled, name="flagged", execution="main")
    def flagged(flag=Arg("flag")):
        return flag

    app.session.run("flagged", obey_cond=True)
    assert Return("flagged").get_value(task=app.session["flagged"], session=app.session) is True


@pytest.mark.depends_on("test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success")
@pytest.mark.depends_on("test_succeeded_status_condition_observes_success_log_in_fixed_period")
def test_after_success_and_succeeded_conditions_observe_same_upstream_run():
    app = make_app()

    @app.task(true, name="upstream", execution="main")
    def upstream():
        return "upstream"

    @app.task(after_success("upstream"), name="next_step", execution="main")
    def next_step():
        return "next"

    app.session.run("upstream")
    upstream_task = app.session["upstream"]
    next_task = app.session["next_step"]
    assert succeeded(task="upstream").today.observe(task=upstream_task, session=app.session) is True
    assert next_task.start_cond.observe(task=next_task, session=app.session) is True


@pytest.mark.depends_on("test_functask_constructor_registers_on_supplied_session")
@pytest.mark.depends_on("test_direct_run_records_return_value_for_string_and_function_return_args")
def test_functask_and_decorator_tasks_share_session_parameters_and_returns():
    app = make_app()
    app.params(seed="S")
    FuncTask(lambda seed: f"{seed}1", name="constructed", start_cond=true, execution="main", session=app.session, parameters={"seed": Arg("seed")})

    @app.task(after_success("constructed"), name="decorated", execution="main")
    def decorated(value=Return("constructed")):
        return f"{value}2"

    app.session.run("constructed", "decorated")
    assert Return("decorated").get_value(task=app.session["decorated"], session=app.session) == "S12"


@pytest.mark.depends_on("test_one_cycle_scheduler_start_uses_public_shutdown_condition")
@pytest.mark.depends_on("test_direct_run_records_return_value_for_string_and_function_return_args")
def test_explicit_scheduler_start_runs_declared_tasks_with_fixed_time():
    app = make_app(shut_cond=scheduler_cycles() >= 1)

    @app.task(true, name="scheduled_a", execution="main")
    def scheduled_a():
        return "a"

    @app.task(true, name="scheduled_b", execution="main")
    def scheduled_b():
        return "b"

    app.session.start()
    assert app.session.scheduler.n_cycles == 1
    assert Return("scheduled_a").get_value(task=app.session["scheduled_a"], session=app.session) == "a"
    assert Return("scheduled_b").get_value(task=app.session["scheduled_b"], session=app.session) == "b"


@pytest.mark.depends_on("test_time_of_day_between_uses_session_time_function")
@pytest.mark.depends_on("test_daily_condition_becomes_false_after_success_in_same_fixed_day")
def test_daily_and_time_of_day_combination_runs_then_becomes_not_due():
    app = make_app()

    @app.task(daily & time_of_day.between("09:00", "10:00"), name="daily_window", execution="main")
    def daily_window():
        return "window"

    task = app.session["daily_window"]
    app.session.run("daily_window", obey_cond=True)
    assert task.status == "success"
    assert task.start_cond.observe(task=task, session=app.session) is False


@pytest.mark.depends_on("test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success")
@pytest.mark.depends_on("test_successful_direct_run_writes_run_and_success_log_actions")
def test_three_task_success_chain_projects_status_return_and_logs():
    app = make_app()

    @app.task(true, name="one", execution="main", priority=100)
    def one():
        return "1"

    @app.task(after_success("one"), name="two", execution="main", priority=50)
    def two(value=Return("one")):
        return value + "2"

    @app.task(after_success("two"), name="three", execution="main", priority=10)
    def three(value=Return("two")):
        return value + "3"

    app.session.run("one", "two", "three")
    assert [app.session[name].status for name in ("one", "two", "three")] == ["success", "success", "success"]
    assert Return("three").get_value(task=app.session["three"], session=app.session) == "123"
    assert actions(app.session["three"]) == ["run", "success"]


@pytest.mark.depends_on("test_meta_arguments_expose_session_task_and_config")
@pytest.mark.depends_on("test_task_logger_filter_counts_are_projected_by_action")
def test_task_can_return_current_log_count_from_meta_task_argument():
    app = make_app()

    @app.task(true, name="inspect_self", execution="main")
    def inspect_self(task=TaskArg()):
        return task.logger.filter_by().count()

    app.session.run("inspect_self")
    assert Return("inspect_self").get_value(task=app.session["inspect_self"], session=app.session) == 1
    assert app.session["inspect_self"].logger.filter_by(action="success").count() == 1


@pytest.mark.depends_on("test_function_parameter_arg_is_materialized_during_run")
@pytest.mark.depends_on("test_simplearg_and_funcarg_are_task_level_values")
def test_app_param_function_feeds_two_downstream_consumers():
    app = make_app()

    @app.param("source_value")
    def source_value():
        return "root"

    @app.task(true, name="producer", execution="main", priority=100)
    def producer(value=Arg("source_value")):
        return value

    @app.task(after_success("producer"), name="left", execution="main", priority=20)
    def left(value=Return("producer")):
        return f"L:{value}"

    @app.task(after_success("producer"), name="right", execution="main", priority=10)
    def right(value=Return("producer")):
        return f"R:{value}"

    app.session.run("producer", "left", "right")
    assert Return("left").get_value(task=app.session["left"], session=app.session) == "L:root"
    assert Return("right").get_value(task=app.session["right"], session=app.session) == "R:root"


@pytest.mark.depends_on("test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success")
@pytest.mark.depends_on("test_task_logger_filter_counts_are_projected_by_action")
def test_unlisted_downstream_task_remains_unrun_when_manual_run_targets_source_only():
    app = make_app()

    @app.task(true, name="source", execution="main")
    def source():
        return "source"

    @app.task(after_success("source"), name="downstream", execution="main")
    def downstream():
        return "downstream"

    app.session.run("source")
    assert app.session["source"].status == "success"
    assert app.session["downstream"].status is None
    assert app.session["downstream"].logger.filter_by().count() == 0


@pytest.mark.depends_on("test_custom_condition_accepts_positional_arguments")
@pytest.mark.depends_on("test_condition_and_algebra_requires_all_true_branches")
def test_custom_condition_arguments_can_block_scheduler_without_logs():
    app = make_app()

    @app.cond()
    def allowed(item):
        return item == "expected"

    @app.task(true & allowed("other"), name="blocked_custom", execution="main")
    def blocked_custom():
        return "blocked"

    app.session.run("blocked_custom", obey_cond=True)
    assert app.session["blocked_custom"].status is None
    assert app.session["blocked_custom"].logger.filter_by().count() == 0


@pytest.mark.depends_on("test_direct_run_records_return_value_for_string_and_function_return_args")
@pytest.mark.depends_on("test_memory_repository_task_records_contain_stable_task_action_and_time_fields")
def test_return_value_log_time_and_status_survive_same_workflow_projection():
    app = make_app()

    @app.task(true, name="projected", execution="main")
    def projected():
        return {"value": 5}

    task = app.session["projected"]
    app.session.run("projected")
    assert task.status == "success"
    assert Return("projected").get_value(task=task, session=app.session) == {"value": 5}
    assert {record["created"] for record in task.logger.filter_by().all()} == {FIXED_MONDAY.timestamp()}


@pytest.mark.depends_on("test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success")
@pytest.mark.depends_on("test_condition_inversion_flips_public_state")
def test_pipeline_condition_can_be_combined_with_negated_false_condition():
    app = make_app()

    @app.task(true, name="source", execution="main", priority=100)
    def source():
        return "ok"

    @app.task(after_success("source") & ~false, name="guarded_downstream", execution="main", priority=10)
    def guarded_downstream(value=Return("source")):
        return value

    app.session.run("source", "guarded_downstream")
    assert app.session["guarded_downstream"].status == "success"
    assert Return("guarded_downstream").get_value(task=app.session["guarded_downstream"], session=app.session) == "ok"


@pytest.mark.depends_on("test_direct_run_records_return_value_for_string_and_function_return_args")
@pytest.mark.depends_on("test_successful_direct_run_writes_run_and_success_log_actions")
def test_after_finish_pipeline_passes_return_and_source_log_projection():
    app = make_app()

    @app.task(true, name="source", execution="main", priority=100)
    def source():
        return "payload"

    @app.task(after_finish("source"), name="audit", execution="main", priority=10)
    def audit(value=Return("source")):
        return value, actions(app.session["source"])

    audit_task = app.session["audit"]
    assert audit_task.start_cond.observe(task=audit_task, session=app.session) is False
    app.session.run("source", "audit")
    assert app.session["source"].status == "success"
    assert audit_task.status == "success"
    assert Return("audit").get_value(task=audit_task, session=app.session) == (
        "payload",
        ["run", "success"],
    )
