from __future__ import annotations

from datetime import datetime

from redbird.repos import MemoryRepo

from rocketry import FuncTask, Rocketry, Session
from rocketry.args import Arg, Config, FuncArg, Return, Session as SessionArg, SimpleArg, Task as TaskArg
from rocketry.conds import (
    after_finish,
    after_success,
    daily,
    false,
    hourly,
    scheduler_cycles,
    succeeded,
    time_of_day,
    true,
    weekly,
)

from conftest import FIXED_MONDAY, FIXED_SUNDAY, actions, make_app, record_run_ids, task_records


def test_public_import_surface_exposes_application_session_task_condition_and_args():
    assert Rocketry is not None
    assert Session is not None
    assert FuncTask is not None
    assert true.observe() is True
    assert false.observe() is False
    assert Return is not None


def test_rocketry_constructs_session_with_fixed_main_execution():
    app = make_app()

    assert isinstance(app.session, Session)
    assert app.session.config.execution == "main"
    assert app.session.get_time() == FIXED_MONDAY.timestamp()


def test_task_decorator_returns_function_and_registers_lookup_by_name_and_function():
    app = make_app()

    @app.task(true, name="registered", execution="main")
    def registered():
        return "ok"

    task = app.session["registered"]
    assert app.session[registered] is task
    assert getattr(registered, "__rocketry__") == {"name": "registered"}


def test_task_declaration_stores_public_metadata():
    app = make_app()

    @app.task(true, name="metadata", execution="main", priority=12)
    def metadata():
        return "ok"

    task = app.session["metadata"]
    assert task.name == "metadata"
    assert task.execution == "main"
    assert task.priority == 12
    assert task.start_cond.observe(task=task, session=app.session) is True


def test_functask_constructor_registers_on_supplied_session():
    session = Session(config={"execution": "main", "time_func": lambda: FIXED_MONDAY.timestamp()})
    task = FuncTask(lambda: "built", name="built", start_cond=true, execution="main", session=session)

    assert session["built"] is task
    assert task.session is session


def test_boolean_conditions_observe_without_context():
    assert true.observe() is True
    assert false.observe() is False


def test_condition_or_algebra_observes_any_true_branch():
    assert (false | true).observe() is True
    assert (false | false).observe() is False


def test_condition_and_algebra_requires_all_true_branches():
    assert (true & true).observe() is True
    assert (true & false).observe() is False


def test_condition_inversion_flips_public_state():
    assert (~false).observe() is True
    assert (~true).observe() is False


def test_nested_condition_algebra_preserves_parenthesized_meaning():
    expression = (true | false) & ~(false & true)

    assert expression.observe() is True


def test_custom_condition_observes_wrapped_function_result():
    app = make_app()

    @app.cond()
    def ready():
        return True

    assert ready.observe(session=app.session) is True


def test_custom_condition_accepts_positional_arguments():
    app = make_app()

    @app.cond()
    def equals(left, right):
        return left == right

    assert equals("same", "same").observe(session=app.session) is True
    assert equals("same", "different").observe(session=app.session) is False


def test_custom_condition_can_receive_current_task_argument():
    app = make_app()

    @app.cond()
    def is_named_expected(this_task=TaskArg()):
        return this_task.name == "expected"

    @app.task(is_named_expected, name="expected", execution="main")
    def expected():
        return "ok"

    task = app.session["expected"]
    assert task.start_cond.observe(task=task, session=app.session) is True


def test_daily_condition_is_true_for_never_run_task_at_fixed_time():
    app = make_app()

    @app.task(daily, name="daily_task", execution="main")
    def daily_task():
        return "ok"

    task = app.session["daily_task"]
    assert daily.observe(task=task, session=app.session) is True


def test_daily_condition_becomes_false_after_success_in_same_fixed_day():
    app = make_app()

    @app.task(daily, name="daily_task", execution="main")
    def daily_task():
        return "ok"

    app.session.run("daily_task", obey_cond=True)
    task = app.session["daily_task"]
    assert task.status == "success"
    assert daily.observe(task=task, session=app.session) is False


def test_time_of_day_between_uses_session_time_function():
    app = make_app()

    @app.task(true, name="clocked", execution="main")
    def clocked():
        return "ok"

    task = app.session["clocked"]
    assert time_of_day.between("09:00", "10:00").observe(task=task, session=app.session) is True
    assert time_of_day.between("10:00", "11:00").observe(task=task, session=app.session) is False


def test_weekly_condition_matches_fixed_weekday():
    monday = make_app(FIXED_MONDAY)
    sunday = make_app(FIXED_SUNDAY)

    @monday.task(true, name="monday_task", execution="main")
    def monday_task():
        return "ok"

    @sunday.task(true, name="sunday_task", execution="main")
    def sunday_task():
        return "ok"

    assert weekly.on("Monday").observe(task=monday.session["monday_task"], session=monday.session) is True
    assert weekly.on("Monday").observe(task=sunday.session["sunday_task"], session=sunday.session) is False


def test_hourly_after_matches_minute_second_inside_hour():
    app = make_app()

    @app.task(true, name="hourly_task", execution="main")
    def hourly_task():
        return "ok"

    task = app.session["hourly_task"]
    assert hourly.after("15:00").observe(task=task, session=app.session) is True
    assert hourly.before("15:00").observe(task=task, session=app.session) is False


def test_session_level_arg_is_injected_during_direct_run():
    app = make_app()
    app.params(greeting="hello")

    @app.task(true, name="uses_arg", execution="main")
    def uses_arg(value=Arg("greeting")):
        return value

    app.session.run("uses_arg")
    assert Return("uses_arg").get_value(task=app.session["uses_arg"], session=app.session) == "hello"


def test_function_parameter_arg_is_materialized_during_run():
    app = make_app()

    @app.param("dynamic")
    def dynamic():
        return "computed"

    @app.task(true, name="uses_dynamic", execution="main")
    def uses_dynamic(value=Arg("dynamic")):
        return value

    app.session.run("uses_dynamic")
    assert Return("uses_dynamic").get_value(task=app.session["uses_dynamic"], session=app.session) == "computed"


def test_simplearg_and_funcarg_are_task_level_values():
    app = make_app()

    @app.task(true, name="local_args", execution="main")
    def local_args(left=SimpleArg("plain"), right=FuncArg(lambda: "callable")):
        return left, right

    app.session.run("local_args")
    assert Return("local_args").get_value(task=app.session["local_args"], session=app.session) == (
        "plain",
        "callable",
    )


def test_meta_arguments_expose_session_task_and_config():
    app = make_app()

    @app.task(true, name="meta", execution="main")
    def meta(session=SessionArg(), task=TaskArg(), config=Config()):
        return session is app.session, task.name, config.execution

    app.session.run("meta")
    assert Return("meta").get_value(task=app.session["meta"], session=app.session) == (
        True,
        "meta",
        "main",
    )


def test_direct_run_records_return_value_for_string_and_function_return_args():
    app = make_app()

    @app.task(true, name="producer", execution="main")
    def producer():
        return "payload"

    app.session.run("producer")
    task = app.session["producer"]
    assert Return("producer").get_value(task=task, session=app.session) == "payload"
    assert Return(producer).get_value(task=task, session=app.session) == "payload"


def test_successful_direct_run_updates_status_and_last_success_projection():
    app = make_app()

    @app.task(true, name="status_task", execution="main")
    def status_task():
        return "ok"

    task = app.session["status_task"]
    app.session.run("status_task")
    assert task.status == "success"
    assert task.last_run == FIXED_MONDAY
    assert task.last_success == FIXED_MONDAY
    assert task.last_fail is None


def test_successful_direct_run_writes_run_and_success_log_actions():
    app = make_app()

    @app.task(true, name="logged", execution="main")
    def logged():
        return "ok"

    task = app.session["logged"]
    app.session.run("logged")
    assert actions(task) == ["run", "success"]


def test_task_logger_filter_counts_are_projected_by_action():
    app = make_app()

    @app.task(true, name="counted", execution="main")
    def counted():
        return "ok"

    task = app.session["counted"]
    app.session.run("counted")
    assert task.logger.filter_by(action="run").count() == 1
    assert task.logger.filter_by(action="success").count() == 1
    assert task.logger.filter_by(action="fail").count() == 0


def test_log_records_share_run_id_between_run_and_success():
    app = make_app()

    @app.task(true, name="run_id_task", execution="main")
    def run_id_task():
        return "ok"

    task = app.session["run_id_task"]
    app.session.run("run_id_task")
    assert len(record_run_ids(task)) == 1


def test_obey_cond_true_leaves_false_condition_task_unrun():
    app = make_app()

    @app.task(false, name="blocked", execution="main")
    def blocked():
        return "should not run"

    task = app.session["blocked"]
    app.session.run("blocked", obey_cond=True)
    assert task.status is None
    assert task.logger.filter_by().count() == 0


def test_after_success_condition_is_false_before_source_task_succeeds():
    app = make_app()

    @app.task(true, name="source", execution="main")
    def source():
        return "source"

    @app.task(after_success("source"), name="downstream", execution="main")
    def downstream():
        return "downstream"

    downstream_task = app.session["downstream"]
    assert downstream_task.start_cond.observe(task=downstream_task, session=app.session) is False


def test_after_success_condition_becomes_true_for_unrun_downstream_after_source_success():
    app = make_app()

    @app.task(true, name="source", execution="main")
    def source():
        return "source"

    @app.task(after_success("source"), name="downstream", execution="main")
    def downstream():
        return "downstream"

    app.session.run("source")
    downstream_task = app.session["downstream"]
    assert downstream_task.start_cond.observe(task=downstream_task, session=app.session) is True


def test_succeeded_status_condition_observes_success_log_in_fixed_period():
    app = make_app()

    @app.task(true, name="source", execution="main")
    def source():
        return "source"

    source_task = app.session["source"]
    assert succeeded(task="source").today.observe(task=source_task, session=app.session) is False
    app.session.run("source")
    assert succeeded(task="source").today.observe(task=source_task, session=app.session) is True


def test_one_cycle_scheduler_start_uses_public_shutdown_condition():
    app = make_app(shut_cond=scheduler_cycles() >= 1)

    @app.task(true, name="cycled", execution="main")
    def cycled():
        return "ok"

    app.session.start()
    assert app.session.scheduler.n_cycles == 1
    assert app.session["cycled"].status == "success"


def test_memory_repository_task_records_contain_stable_task_action_and_time_fields():
    app = make_app()

    @app.task(true, name="recorded", execution="main")
    def recorded():
        return "ok"

    task = app.session["recorded"]
    app.session.run("recorded")
    records = task_records(task)
    assert [(record["task_name"], record["action"]) for record in records] == [
        ("recorded", "run"),
        ("recorded", "success"),
    ]
    assert all(record["created"] == FIXED_MONDAY.timestamp() for record in records)
