# Spec2Repo oracle - atomic tests for luigi-workflow-fullrepro-001
import datetime as dt
import enum
import json
import os
import pathlib
import subprocess
import sys
import textwrap
import warnings

import pytest


def run_script(tmp_path, code, extra_env=None, timeout=20):
    script = tmp_path / "probe.py"
    script.write_text(textwrap.dedent(code), encoding="utf-8")
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return proc


def check_top_level_public_imports_are_available():
    import luigi

    names = [
        "Task",
        "ExternalTask",
        "WrapperTask",
        "Config",
        "DynamicRequirements",
        "Target",
        "LocalTarget",
        "Parameter",
        "StrParameter",
        "IntParameter",
        "FloatParameter",
        "BoolParameter",
        "DateParameter",
        "MonthParameter",
        "YearParameter",
        "DateHourParameter",
        "DateMinuteParameter",
        "DateSecondParameter",
        "DateIntervalParameter",
        "TimeDeltaParameter",
        "PathParameter",
        "TaskParameter",
        "ListParameter",
        "TupleParameter",
        "DictParameter",
        "EnumParameter",
        "EnumListParameter",
        "NumericalParameter",
        "ChoiceParameter",
        "ChoiceListParameter",
        "OptionalParameter",
        "OptionalIntParameter",
        "OptionalBoolParameter",
        "OptionalPathParameter",
        "Event",
        "LuigiStatusCode",
        "RemoteScheduler",
        "RPCError",
        "build",
        "run",
        "namespace",
        "auto_namespace",
    ]
    missing = [name for name in names if not hasattr(luigi, name)]
    assert missing == []


def check_documented_module_imports_are_available():
    from luigi.execution_summary import LuigiRunResult
    from luigi.parameter import (
        DuplicateParameterException,
        MissingParameterException,
        ParameterException,
        ParameterVisibility,
        UnknownParameterException,
    )
    from luigi.target import FileAlreadyExists, FileSystemException, FileSystemTarget, MissingParentDirectory, NotADirectory

    assert ParameterVisibility.PUBLIC != ParameterVisibility.HIDDEN
    assert ParameterVisibility.HIDDEN != ParameterVisibility.PRIVATE
    assert issubclass(MissingParameterException, ParameterException)
    assert issubclass(UnknownParameterException, ParameterException)
    assert issubclass(DuplicateParameterException, ParameterException)
    assert FileSystemTarget is not None
    assert issubclass(FileAlreadyExists, FileSystemException)
    assert issubclass(MissingParentDirectory, FileSystemException)
    assert issubclass(NotADirectory, FileSystemException)
    assert LuigiRunResult is not None


def check_public_api_clone_preserves_and_overrides_parameters():
    import luigi

    class CloneSource(luigi.Task):
        name = luigi.Parameter()
        count = luigi.IntParameter(default=1)

    original = CloneSource(name="alpha", count=1)
    clone = original.clone(count=3)
    assert isinstance(clone, CloneSource)
    assert (clone.name, clone.count) == ("alpha", 3)
    assert (original.name, original.count) == ("alpha", 1)


def test_product_state_model_parameter_identity_visible_across_projections():
    import luigi

    class VisibleStateTask(luigi.Task):
        value = luigi.IntParameter()

    task = VisibleStateTask(value=7)
    assert task.value == 7
    assert task.to_str_params() == {"value": "7"}
    rendered = repr(task)
    assert "VisibleStateTask" in rendered
    assert "7" in rendered


def test_basic_parameter_types_parse_and_serialize_public_values():
    import luigi

    assert luigi.Parameter().parse("abc") == "abc"
    assert luigi.StrParameter().serialize(123) == "123"
    assert luigi.IntParameter().parse("42") == 42
    assert luigi.FloatParameter().parse("2.5") == 2.5
    assert luigi.BoolParameter().parse("true") is True
    assert luigi.BoolParameter().parse("false") is False


def test_invalid_basic_parameter_values_raise_value_error():
    import luigi

    with pytest.raises(ValueError):
        luigi.IntParameter().parse("forty")
    with pytest.raises(ValueError):
        luigi.FloatParameter().parse("two")
    with pytest.raises(ValueError):
        luigi.BoolParameter().parse("maybe")


def test_date_parameters_parse_documented_shapes():
    import luigi

    assert luigi.DateParameter().parse("2026-07-10") == dt.date(2026, 7, 10)
    assert luigi.MonthParameter().parse("2026-07") == dt.date(2026, 7, 1)
    assert luigi.YearParameter().parse("2026") == dt.date(2026, 1, 1)
    assert luigi.DateHourParameter().parse("2026-07-10T05") == dt.datetime(2026, 7, 10, 5)


def test_date_parameter_invalid_input_raises_value_error():
    import luigi

    with pytest.raises(ValueError):
        luigi.DateParameter().parse("2026/07/10")
    with pytest.raises(ValueError):
        luigi.DateHourParameter().parse("2026-07-10")


def test_list_tuple_and_dict_parameters_parse_json_publicly():
    import luigi

    assert tuple(luigi.ListParameter().parse("[1, 2, 3]")) == (1, 2, 3)
    assert luigi.TupleParameter().parse("[1, 2]") == (1, 2)
    parsed = luigi.DictParameter().parse('{"b": 2, "a": 1}')
    assert dict(parsed) == {"a": 1, "b": 2} or dict(parsed) == {"b": 2, "a": 1}


def check_tuple_parameter_rejects_plain_string():
    import luigi

    with pytest.raises(ValueError):
        luigi.TupleParameter().parse("not-a-tuple")


def test_enum_parameter_round_trips_by_member_name():
    import luigi

    class Color(enum.Enum):
        RED = 1
        BLUE = 2

    param = luigi.EnumParameter(enum=Color)
    assert param.parse("RED") is Color.RED
    assert param.serialize(Color.BLUE) == "BLUE"
    with pytest.raises((ValueError, KeyError)):
        param.parse("GREEN")


def check_enum_list_parameter_round_trips_comma_separated_names():
    import luigi

    class Color(enum.Enum):
        RED = 1
        BLUE = 2

    param = luigi.EnumListParameter(enum=Color)
    assert param.parse("RED,BLUE") == (Color.RED, Color.BLUE)
    assert param.serialize((Color.BLUE, Color.RED)) == "BLUE,RED"


def test_choice_parameter_accepts_only_configured_values():
    import luigi
    from luigi.parameter import ParameterException

    param = luigi.ChoiceParameter(choices=["small", "large"])
    assert param.parse("small") == "small"
    with pytest.raises(ValueError):
        param.parse("medium")
    with pytest.raises(ParameterException):
        luigi.ChoiceParameter()


def check_choice_list_parameter_preserves_order_and_duplicates():
    import luigi

    param = luigi.ChoiceListParameter(choices=["a", "b"])
    assert param.parse("a,b,a") == ("a", "b", "a")
    assert param.parse("") == ()
    with pytest.raises(ValueError):
        param.parse("a,c")


def test_numerical_parameter_enforces_bounds():
    import luigi
    from luigi.parameter import ParameterException

    param = luigi.NumericalParameter(var_type=int, min_value=1, max_value=5)
    assert param.parse("3") == 3
    with pytest.raises(ValueError):
        param.parse("5")
    with pytest.raises(ParameterException):
        luigi.NumericalParameter(var_type=int)


def test_path_parameter_normalizes_and_checks_existence(tmp_path):
    import luigi

    existing = tmp_path / "data.txt"
    existing.write_text("ok", encoding="utf-8")
    existing_param = luigi.PathParameter(exists=True)
    missing = tmp_path / "missing.txt"
    assert existing_param.parse(str(existing)) == str(existing)
    assert existing_param.normalize(str(existing)) == existing
    assert existing_param.parse(str(missing)) == str(missing)
    with pytest.raises(ValueError):
        existing_param.normalize(str(missing))
    plain_param = luigi.PathParameter()
    assert plain_param.parse("relative.txt") == "relative.txt"
    assert plain_param.normalize("relative.txt") == pathlib.Path("relative.txt")


def test_installable_surface_documented_parameter_exceptions_match_task_construction():
    import luigi
    from luigi.parameter import DuplicateParameterException, MissingParameterException, UnknownParameterException

    class SurfaceParamTask(luigi.Task):
        count = luigi.IntParameter()

    with pytest.raises(MissingParameterException):
        SurfaceParamTask()
    with pytest.raises(UnknownParameterException):
        SurfaceParamTask(count=1, extra=2)
    with pytest.raises(DuplicateParameterException):
        SurfaceParamTask("1", count=2)


def test_optional_parameters_parse_empty_string_as_none():
    import luigi

    assert luigi.OptionalParameter().parse("") is None
    assert luigi.OptionalIntParameter().parse("") is None
    assert luigi.OptionalBoolParameter().parse("") is None
    assert luigi.OptionalFloatParameter().parse("2.5") == 2.5
    assert luigi.OptionalParameter().serialize(None) == ""


def check_optional_parameter_warns_on_wrong_non_none_type():
    import luigi

    class OptionalWarningTask(luigi.Task):
        value = luigi.OptionalIntParameter(default=None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        task = OptionalWarningTask(value="bad")
    assert task.value == "bad"
    assert any("OptionalIntParameter" in str(w.message) for w in caught)


def test_required_parameter_missing_raises_missing_parameter_exception():
    import luigi
    from luigi.parameter import MissingParameterException

    class RequiredParamTask(luigi.Task):
        value = luigi.Parameter()

    with pytest.raises(MissingParameterException):
        RequiredParamTask()


def test_unknown_keyword_raises_unknown_parameter_exception():
    import luigi
    from luigi.parameter import UnknownParameterException

    class KnownParamTask(luigi.Task):
        value = luigi.Parameter(default="x")

    with pytest.raises(UnknownParameterException):
        KnownParamTask(other="y")


def test_duplicate_positional_and_keyword_parameter_raises():
    import luigi
    from luigi.parameter import DuplicateParameterException

    class DuplicateParamTask(luigi.Task):
        value = luigi.Parameter()

    with pytest.raises(DuplicateParameterException):
        DuplicateParamTask("positional", value="keyword")


def check_too_many_positional_parameters_raise_unknown_parameter_exception():
    import luigi
    from luigi.parameter import UnknownParameterException

    class OnePositionalTask(luigi.Task):
        value = luigi.Parameter()

    with pytest.raises(UnknownParameterException):
        OnePositionalTask("one", "two")


def test_insignificant_parameter_is_omitted_from_identity_and_public_strings():
    import luigi

    class InsignificantTask(luigi.Task):
        visible = luigi.Parameter()
        hidden_from_identity = luigi.Parameter(default="a", significant=False)

    first = InsignificantTask(visible="same", hidden_from_identity="a")
    second = InsignificantTask(visible="same", hidden_from_identity="b")
    assert first == second
    assert hash(first) == hash(second)
    assert first.to_str_params(only_significant=True) == {"visible": "same"}


def test_parameter_visibility_controls_public_serialization_without_changing_attribute():
    import luigi
    from luigi.parameter import ParameterVisibility

    class VisibilityTask(luigi.Task):
        public = luigi.Parameter(default="p", visibility=ParameterVisibility.PUBLIC)
        hidden = luigi.Parameter(default="h", visibility=ParameterVisibility.HIDDEN)
        private = luigi.Parameter(default="s", visibility=ParameterVisibility.PRIVATE)

    task = VisibilityTask()
    assert (task.public, task.hidden, task.private) == ("p", "h", "s")
    assert task.to_str_params(only_public=True) == {"public": "p"}


def test_from_str_params_parses_string_mapping_and_falls_back_to_defaults():
    import luigi

    class FromStringTask(luigi.Task):
        count = luigi.IntParameter()
        name = luigi.Parameter(default="default")

    task = FromStringTask.from_str_params({"count": "7"})
    assert task.count == 7
    assert task.name == "default"


def test_task_equality_uses_class_and_significant_public_values():
    import luigi

    class IdentityTask(luigi.Task):
        value = luigi.IntParameter()

    class OtherIdentityTask(luigi.Task):
        value = luigi.IntParameter()

    assert IdentityTask(value=1) == IdentityTask(value=1)
    assert IdentityTask(value=1) != IdentityTask(value=2)
    assert IdentityTask(value=1) != OtherIdentityTask(value=1)


def test_task_family_uses_namespace_and_class_name():
    import luigi

    luigi.namespace("generated_ns")

    class NamespacedTask(luigi.Task):
        pass

    luigi.namespace(None)
    assert NamespacedTask.get_task_family() == "generated_ns.NamespacedTask"


def check_class_level_task_namespace_overrides_namespace_call():
    import luigi

    luigi.namespace("outer_ns")

    class ExplicitNamespaceTask(luigi.Task):
        task_namespace = "class_ns"

    luigi.namespace(None)
    assert ExplicitNamespaceTask.get_task_family() == "class_ns.ExplicitNamespaceTask"


def test_task_complete_false_without_outputs_and_true_when_local_output_exists(tmp_path):
    import luigi

    class NoOutputTask(luigi.Task):
        pass

    class OutputTask(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "done.txt")

    assert NoOutputTask().complete() is False
    task = OutputTask()
    assert task.complete() is False
    pathlib.Path(task.output().path).write_text("done", encoding="utf-8")
    assert task.complete() is True


def test_task_complete_raises_when_output_has_no_exists_method():
    import luigi

    class BadOutputTask(luigi.Task):
        def output(self):
            return object()

    with pytest.raises(Exception):
        BadOutputTask().complete()


def check_task_clone_copies_same_named_parameters_and_overrides_values():
    import luigi

    class BaseCloneTask(luigi.Task):
        a = luigi.IntParameter()
        b = luigi.Parameter(default="base")

    class DestCloneTask(luigi.Task):
        a = luigi.IntParameter()
        c = luigi.Parameter(default="dest")

    source = BaseCloneTask(a=4, b="ignored")
    cloned = source.clone(DestCloneTask, c="override")
    assert isinstance(cloned, DestCloneTask)
    assert cloned.a == 4
    assert cloned.c == "override"


def test_external_task_has_no_run_method_and_missing_output_is_incomplete(tmp_path):
    import luigi

    class MissingExternal(luigi.ExternalTask):
        def output(self):
            return luigi.LocalTarget(tmp_path / "external.txt")

    task = MissingExternal()
    assert task.run is None
    assert task.complete() is False


def check_dynamic_requirements_custom_complete_receives_completion_function(tmp_path):
    import luigi

    class CustomDep(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "custom.txt")

    calls = []

    def custom(complete_fn):
        calls.append(complete_fn(CustomDep()))
        return "custom-result"

    reqs = luigi.DynamicRequirements([CustomDep()], custom_complete=custom)
    assert reqs.complete() == "custom-result"
    assert calls == [False]


def check_local_target_write_exception_does_not_commit_final_path(tmp_path):
    import luigi

    target = luigi.LocalTarget(tmp_path / "failed.txt")
    with pytest.raises(RuntimeError):
        with target.open("w") as handle:
            handle.write("partial")
            raise RuntimeError("abort")
    assert target.exists() is False


def test_local_target_rejects_missing_path_unless_temporary():
    import luigi

    with pytest.raises(Exception):
        luigi.LocalTarget()
    temp_target = luigi.LocalTarget(is_tmp=True)
    assert temp_target.path
    if temp_target.exists():
        temp_target.remove()


def check_local_target_invalid_mode_raises(tmp_path):
    import luigi

    target = luigi.LocalTarget(tmp_path / "data.txt")
    with pytest.raises(Exception):
        target.open("a")


def check_run_rejects_non_sequence_cmdline_args(tmp_path):
    proc = run_script(
        tmp_path,
        """
        import luigi
        try:
            luigi.run(cmdline_args="not-a-list", local_scheduler=True)
        except TypeError:
            print("type-error")
        """,
    )
    assert proc.returncode == 0
    assert "type-error" in proc.stdout


def check_cli_help_displays_core_and_task_flags(tmp_path):
    module = tmp_path / "workflow_help.py"
    module.write_text(
        "import luigi\nclass HelpTask(luigi.Task):\n    value = luigi.IntParameter(default=1)\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-m", "luigi", "--module", "workflow_help", "HelpTask", "--help"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    combined = proc.stdout + proc.stderr
    assert "--local-scheduler" in combined
    assert "--value" in combined


def check_cli_missing_task_family_returns_command_line_error(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "luigi", "--local-scheduler"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    assert proc.returncode != 0


def check_config_missing_environment_interpolation_fails(tmp_path):
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[BadEnvConfigTask]\npath = ${MISSING_ROOT}/data\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi
        class BadEnvConfigTask(luigi.Task):
            path = luigi.Parameter(default="missing")
        try:
            BadEnvConfigTask()
        except Exception as exc:
            print(type(exc).__name__)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg)},
    )
    assert proc.returncode == 0
    assert proc.stdout.strip()


def check_successful_run_calls_on_success_callback(tmp_path):
    import luigi

    seen = []

    class SuccessCallbackTask(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "success-callback.txt")

        def run(self):
            with self.output().open("w") as handle:
                handle.write("ok")

        def on_success(self):
            seen.append("success")
            return "done"

    assert luigi.build([SuccessCallbackTask()], local_scheduler=True, workers=1) is True
    assert seen == ["success"]


def test_requires_returning_target_is_reported_as_scheduling_failure(tmp_path):
    import luigi

    class BadRequiresTask(luigi.Task):
        def requires(self):
            return luigi.LocalTarget(tmp_path / "not-a-task.txt")

        def output(self):
            return luigi.LocalTarget(tmp_path / "bad-requires-output.txt")

    with pytest.raises(Exception):
        luigi.build([BadRequiresTask()], local_scheduler=True, detailed_summary=True, workers=1)


def check_remote_scheduler_connection_failure_raises_rpc_or_connection_exception(tmp_path):
    proc = run_script(
        tmp_path,
        """
        import luigi
        class RemoteOnlyTask(luigi.Task):
            pass
        try:
            luigi.build([RemoteOnlyTask()], local_scheduler=False, scheduler_url="http://127.0.0.1:9")
        except Exception as exc:
            print(type(exc).__name__)
        """,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip()


def check_cli_return_code_uses_configured_task_failure_code(tmp_path):
    module = tmp_path / "workflow_retcode.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi
            class RetcodeTask(luigi.Task):
                out = luigi.PathParameter(default="retcode.txt")
                def output(self):
                    return luigi.LocalTarget(self.out)
                def run(self):
                    raise RuntimeError("fail")
            """
        ),
        encoding="utf-8",
    )
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[retcode]\ntask_failed = 7\n", encoding="utf-8")
    env = os.environ.copy()
    env["LUIGI_CONFIG_PATH"] = str(cfg)
    proc = subprocess.run(
        [sys.executable, "-m", "luigi", "--module", "workflow_retcode", "RetcodeTask", "--local-scheduler"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 7


def check_configured_local_scheduler_flag_allows_cli_without_explicit_local_scheduler(tmp_path):
    module = tmp_path / "workflow_configured_local.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi
            class ConfiguredLocalTask(luigi.Task):
                out = luigi.PathParameter()
                def output(self):
                    return luigi.LocalTarget(self.out)
                def run(self):
                    with self.output().open("w") as handle:
                        handle.write("configured")
            """
        ),
        encoding="utf-8",
    )
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[core]\nlocal-scheduler = true\n", encoding="utf-8")
    env = os.environ.copy()
    env["LUIGI_CONFIG_PATH"] = str(cfg)
    output = tmp_path / "configured.txt"
    proc = subprocess.run(
        [sys.executable, "-m", "luigi", "--module", "workflow_configured_local", "ConfiguredLocalTask", "--out", str(output)],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert output.read_text(encoding="utf-8") == "configured"


def check_public_parameter_values_are_visible_in_scheduler_records(tmp_path):
    import luigi

    class SchedulerParamTask(luigi.Task):
        value = luigi.IntParameter()

        def output(self):
            return luigi.LocalTarget(tmp_path / f"scheduler-{self.value}.txt")

        def run(self):
            with self.output().open("w") as handle:
                handle.write(str(self.value))

    result = luigi.build([SchedulerParamTask(value=33)], local_scheduler=True, detailed_summary=True, workers=1)
    assert result.scheduling_succeeded is True
    assert SchedulerParamTask(value=33).to_str_params() == {"value": "33"}


def test_private_parameter_is_not_exposed_in_public_str_params_but_remains_attribute():
    import luigi
    from luigi.parameter import ParameterVisibility

    class PrivateParamTask(luigi.Task):
        token = luigi.Parameter(default="secret", visibility=ParameterVisibility.PRIVATE)
        visible = luigi.Parameter(default="public")

    task = PrivateParamTask()
    assert task.token == "secret"
    assert "token" not in task.to_str_params(only_public=True)
    assert task.to_str_params(only_public=True)["visible"] == "public"
