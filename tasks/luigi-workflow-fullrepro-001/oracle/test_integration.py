# Spec2Repo oracle - integration tests for luigi-workflow-fullrepro-001
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


def test_installable_surface_top_level_task_parameter_target_and_build_work(tmp_path):
    from luigi import LocalTarget, Parameter, Task, build

    class SurfaceTask(Task):
        value = Parameter()

        def output(self):
            return LocalTarget(tmp_path / "surface.txt")

        def run(self):
            with self.output().open("w") as handle:
                handle.write(self.value)

    task = SurfaceTask(value="installed")
    assert task.value == "installed"
    assert build([task], local_scheduler=True, workers=1) is True
    assert (tmp_path / "surface.txt").read_text(encoding="utf-8") == "installed"


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


def check_tuple_parameter_rejects_plain_string():
    import luigi

    with pytest.raises(ValueError):
        luigi.TupleParameter().parse("not-a-tuple")


def check_enum_list_parameter_round_trips_comma_separated_names():
    import luigi

    class Color(enum.Enum):
        RED = 1
        BLUE = 2

    param = luigi.EnumListParameter(enum=Color)
    assert param.parse("RED,BLUE") == (Color.RED, Color.BLUE)
    assert param.serialize((Color.BLUE, Color.RED)) == "BLUE,RED"


def check_choice_list_parameter_preserves_order_and_duplicates():
    import luigi

    param = luigi.ChoiceListParameter(choices=["a", "b"])
    assert param.parse("a,b,a") == ("a", "b", "a")
    assert param.parse("") == ()
    with pytest.raises(ValueError):
        param.parse("a,c")


def check_optional_parameter_warns_on_wrong_non_none_type():
    import luigi

    class OptionalWarningTask(luigi.Task):
        value = luigi.OptionalIntParameter(default=None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        task = OptionalWarningTask(value="bad")
    assert task.value == "bad"
    assert any("OptionalIntParameter" in str(w.message) for w in caught)


def check_too_many_positional_parameters_raise_unknown_parameter_exception():
    import luigi
    from luigi.parameter import UnknownParameterException

    class OnePositionalTask(luigi.Task):
        value = luigi.Parameter()

    with pytest.raises(UnknownParameterException):
        OnePositionalTask("one", "two")


def check_class_level_task_namespace_overrides_namespace_call():
    import luigi

    luigi.namespace("outer_ns")

    class ExplicitNamespaceTask(luigi.Task):
        task_namespace = "class_ns"

    luigi.namespace(None)
    assert ExplicitNamespaceTask.get_task_family() == "class_ns.ExplicitNamespaceTask"


def test_task_input_preserves_nested_dependency_output_shape(tmp_path):
    import luigi

    class DepA(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "a.txt")

    class DepB(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "b.txt")

    class Parent(luigi.Task):
        def requires(self):
            return {"left": [DepA()], "right": (DepB(),)}

    inputs = Parent().input()
    assert list(inputs) == ["left", "right"]
    assert isinstance(inputs["left"], list)
    assert isinstance(inputs["right"], tuple)
    assert pathlib.Path(inputs["left"][0].path).name == "a.txt"
    assert pathlib.Path(inputs["right"][0].path).name == "b.txt"


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


def test_wrapper_task_complete_reflects_requirements(tmp_path):
    import luigi

    output_path = tmp_path / "wrapped.txt"

    class WrappedDep(luigi.Task):
        def output(self):
            return luigi.LocalTarget(output_path)

    class Wrapper(luigi.WrapperTask):
        def requires(self):
            return [WrappedDep()]

    wrapper = Wrapper()
    assert wrapper.complete() is False
    output_path.write_text("done", encoding="utf-8")
    assert wrapper.complete() is True


def test_dynamic_requirements_complete_uses_wrapped_requirements(tmp_path):
    import luigi

    path = tmp_path / "dyn.txt"

    class DynamicDep(luigi.Task):
        def output(self):
            return luigi.LocalTarget(path)

    reqs = luigi.DynamicRequirements([DynamicDep()])
    assert reqs.complete() is False
    path.write_text("done", encoding="utf-8")
    assert reqs.complete() is True


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


def test_local_target_write_creates_parent_and_commits_on_close(tmp_path):
    import luigi

    target = luigi.LocalTarget(tmp_path / "nested" / "data.txt")
    with target.open("w") as handle:
        handle.write("hello")
    assert target.exists() is True
    with target.open("r") as handle:
        assert handle.read() == "hello"


def check_local_target_write_exception_does_not_commit_final_path(tmp_path):
    import luigi

    target = luigi.LocalTarget(tmp_path / "failed.txt")
    with pytest.raises(RuntimeError):
        with target.open("w") as handle:
            handle.write("partial")
            raise RuntimeError("abort")
    assert target.exists() is False


def check_local_target_invalid_mode_raises(tmp_path):
    import luigi

    target = luigi.LocalTarget(tmp_path / "data.txt")
    with pytest.raises(Exception):
        target.open("a")


def test_local_target_move_copy_remove_and_exists(tmp_path):
    import luigi

    source = luigi.LocalTarget(tmp_path / "source.txt")
    with source.open("w") as handle:
        handle.write("payload")
    copy_path = tmp_path / "copy.txt"
    source.copy(copy_path)
    assert copy_path.read_text(encoding="utf-8") == "payload"
    moved_path = tmp_path / "moved.txt"
    source.move(moved_path)
    assert moved_path.read_text(encoding="utf-8") == "payload"
    moved = luigi.LocalTarget(moved_path)
    moved.remove()
    assert moved.exists() is False


def test_filesystem_target_temporary_path_commits_and_rolls_back(tmp_path):
    import luigi

    target = luigi.LocalTarget(tmp_path / "final.txt")
    with target.temporary_path() as temp_path:
        pathlib.Path(temp_path).write_text("committed", encoding="utf-8")
    assert pathlib.Path(target.path).read_text(encoding="utf-8") == "committed"

    rolled_back = luigi.LocalTarget(tmp_path / "rolled-back.txt")
    with pytest.raises(RuntimeError):
        with rolled_back.temporary_path() as temp_path:
            pathlib.Path(temp_path).write_text("nope", encoding="utf-8")
            raise RuntimeError("stop")
    assert rolled_back.exists() is False


def test_build_runs_dependencies_then_downstream_and_reuses_existing_outputs(tmp_path):
    import luigi

    events = []

    class BuildDep(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "dep.txt")

        def run(self):
            events.append("dep")
            with self.output().open("w") as handle:
                handle.write("data")

    class BuildMain(luigi.Task):
        def requires(self):
            return BuildDep()

        def output(self):
            return luigi.LocalTarget(tmp_path / "main.txt")

        def run(self):
            events.append("main")
            with self.input().open("r") as source:
                data = source.read()
            with self.output().open("w") as target:
                target.write(data + "-done")

    assert luigi.build([BuildMain()], local_scheduler=True, workers=1) is True
    assert events == ["dep", "main"]
    assert (tmp_path / "main.txt").read_text(encoding="utf-8") == "data-done"
    assert luigi.build([BuildMain()], local_scheduler=True, workers=1) is True
    assert events == ["dep", "main"]


def test_build_detailed_summary_reports_failed_task(tmp_path):
    import luigi
    from luigi.execution_summary import LuigiRunResult

    class FailingBuildTask(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "never.txt")

        def run(self):
            raise RuntimeError("boom")

    result = luigi.build([FailingBuildTask()], local_scheduler=True, detailed_summary=True, workers=1)
    assert isinstance(result, LuigiRunResult)
    assert result.status == luigi.LuigiStatusCode.FAILED


def test_build_reports_missing_external_dependency_without_running_dependent(tmp_path):
    import luigi

    ran = []

    class MissingInput(luigi.ExternalTask):
        def output(self):
            return luigi.LocalTarget(tmp_path / "missing.txt")

    class NeedsExternal(luigi.Task):
        def requires(self):
            return MissingInput()

        def output(self):
            return luigi.LocalTarget(tmp_path / "dependent.txt")

        def run(self):
            ran.append("dependent")

    result = luigi.build([NeedsExternal()], local_scheduler=True, detailed_summary=True, workers=1)
    assert result.status == luigi.LuigiStatusCode.MISSING_EXT
    assert ran == []


def test_run_accepts_cmdline_args_and_main_task_cls(tmp_path):
    proc = run_script(
        tmp_path,
        """
        import pathlib
        import luigi

        class RunMainTask(luigi.Task):
            root = luigi.PathParameter()
            value = luigi.IntParameter()

            def output(self):
                return luigi.LocalTarget(self.root / "run-main.txt")

            def run(self):
                with self.output().open("w") as handle:
                    handle.write(str(self.value + 1))

        ok = luigi.run(cmdline_args=["--root", ".", "--value", "6"], main_task_cls=RunMainTask, local_scheduler=True)
        print(ok)
        print(pathlib.Path("run-main.txt").read_text())
        """,
    )
    assert proc.returncode == 0, proc.stderr
    assert "True" in proc.stdout
    assert "7" in proc.stdout


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


def test_cli_module_invocation_runs_local_scheduler_task(tmp_path):
    module = tmp_path / "workflow_cli.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi

            class CliTask(luigi.Task):
                out = luigi.PathParameter()
                value = luigi.IntParameter()

                def output(self):
                    return luigi.LocalTarget(self.out)

                def run(self):
                    with self.output().open("w") as handle:
                        handle.write(str(self.value * 2))
            """
        ),
        encoding="utf-8",
    )
    output = tmp_path / "cli.txt"
    proc = subprocess.run(
        [sys.executable, "-m", "luigi", "--module", "workflow_cli", "CliTask", "--out", str(output), "--value", "5", "--local-scheduler"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert output.read_text(encoding="utf-8") == "10"


def test_cli_hyphenated_parameter_name_maps_to_underscore_attribute(tmp_path):
    module = tmp_path / "workflow_hyphen.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi

            class HyphenTask(luigi.Task):
                out = luigi.PathParameter()
                my_value = luigi.IntParameter()

                def output(self):
                    return luigi.LocalTarget(self.out)

                def run(self):
                    with self.output().open("w") as handle:
                        handle.write(str(self.my_value))
            """
        ),
        encoding="utf-8",
    )
    output = tmp_path / "hyphen.txt"
    proc = subprocess.run(
        [sys.executable, "-m", "luigi", "--module", "workflow_hyphen", "HyphenTask", "--out", str(output), "--my-value", "8", "--local-scheduler"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert output.read_text(encoding="utf-8") == "8"


def test_cli_class_qualified_parameter_supplies_dependency_value(tmp_path):
    module = tmp_path / "workflow_qualified.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi

            class QualifiedDep(luigi.Task):
                out = luigi.PathParameter()
                dep_value = luigi.IntParameter()

                def output(self):
                    return luigi.LocalTarget(self.out / "dep.txt")

                def run(self):
                    with self.output().open("w") as handle:
                        handle.write(str(self.dep_value))

            class QualifiedRoot(luigi.Task):
                out = luigi.PathParameter()

                def requires(self):
                    return QualifiedDep(out=self.out)

                def output(self):
                    return luigi.LocalTarget(self.out / "root.txt")

                def run(self):
                    with self.input().open("r") as source:
                        value = source.read()
                    with self.output().open("w") as target:
                        target.write(value)
            """
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "luigi",
            "--module",
            "workflow_qualified",
            "QualifiedRoot",
            "--out",
            str(tmp_path),
            "--QualifiedDep-dep-value",
            "12",
            "--local-scheduler",
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "root.txt").read_text(encoding="utf-8") == "12"


def test_invocation_protocol_python_module_class_qualified_dependency_flag(tmp_path):
    module = tmp_path / "workflow_invocation_qualified.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi

            class InvocationProducer(luigi.Task):
                root = luigi.PathParameter()
                text = luigi.Parameter()

                def output(self):
                    return luigi.LocalTarget(self.root / "producer.txt")

                def run(self):
                    with self.output().open("w") as handle:
                        handle.write(self.text)

            class InvocationConsumer(luigi.Task):
                root = luigi.PathParameter()

                def requires(self):
                    return InvocationProducer(root=self.root)

                def output(self):
                    return luigi.LocalTarget(self.root / "consumer.txt")

                def run(self):
                    with self.input().open("r") as source:
                        value = source.read()
                    with self.output().open("w") as target:
                        target.write(value + "-done")
            """
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "luigi",
            "--module",
            "workflow_invocation_qualified",
            "InvocationConsumer",
            "--root",
            str(tmp_path),
            "--InvocationProducer-text",
            "payload",
            "--local-scheduler",
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "consumer.txt").read_text(encoding="utf-8") == "payload-done"


def test_invocation_protocol_python_module_hyphenated_root_flag(tmp_path):
    module = tmp_path / "workflow_invocation_hyphen.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi

            class InvocationHyphenTask(luigi.Task):
                output_path = luigi.PathParameter()

                def output(self):
                    return luigi.LocalTarget(self.output_path)

                def run(self):
                    with self.output().open("w") as handle:
                        handle.write("hyphen-ok")
            """
        ),
        encoding="utf-8",
    )
    output = tmp_path / "hyphen-output.txt"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "luigi",
            "--module",
            "workflow_invocation_hyphen",
            "InvocationHyphenTask",
            "--output-path",
            str(output),
            "--local-scheduler",
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert output.read_text(encoding="utf-8") == "hyphen-ok"


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


def test_config_file_supplies_task_parameter_default(tmp_path):
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[ConfiguredDefaultTask]\nvalue = 15\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi

        class ConfiguredDefaultTask(luigi.Task):
            value = luigi.IntParameter(default=1)

        print(ConfiguredDefaultTask().value)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg)},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("15")


def test_constructor_value_overrides_config_value(tmp_path):
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[OverrideConfigTask]\nvalue = 15\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi
        class OverrideConfigTask(luigi.Task):
            value = luigi.IntParameter(default=1)
        print(OverrideConfigTask(value=20).value)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg)},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("20")


def test_config_class_reads_values_from_matching_section(tmp_path):
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[ConfigReader]\nkeep_alive = true\nwait_interval = 3\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi

        class ConfigReader(luigi.Config):
            keep_alive = luigi.BoolParameter(default=False)
            wait_interval = luigi.IntParameter(default=0)

        config = ConfigReader()
        print(config.keep_alive)
        print(config.wait_interval)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg)},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-2:] == ["True", "3"]


def test_config_environment_interpolation_uses_environment_variable(tmp_path):
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[paths]\nroot = ${ROOT_DIR}/data\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi

        class EnvConfigTask(luigi.Task):
            root = luigi.Parameter(config_path={"section": "paths", "name": "root"}, default="fallback")

        print(EnvConfigTask().root)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg), "ROOT_DIR": "/tmp/root"},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("/tmp/root/data")


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


def test_toml_config_parser_reads_luigi_config_path(tmp_path):
    cfg = tmp_path / "luigi.toml"
    cfg.write_text("[TomlConfigTask]\nvalue = 9\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi

        class TomlConfigTask(luigi.Task):
            value = luigi.IntParameter(default=1)

        print(TomlConfigTask().value)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg), "LUIGI_CONFIG_PARSER": "toml"},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("9")


def test_failed_run_calls_on_failure_callback_and_reports_failed_status(tmp_path):
    import luigi

    seen = []

    class FailureCallbackTask(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "failure-callback.txt")

        def run(self):
            raise RuntimeError("callback")

        def on_failure(self, exception):
            seen.append(type(exception).__name__)
            return "handled"

    result = luigi.build([FailureCallbackTask()], local_scheduler=True, detailed_summary=True, workers=1)
    assert result.status == luigi.LuigiStatusCode.FAILED
    assert seen == ["RuntimeError"]


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


def test_event_handler_can_be_registered_triggered_and_removed():
    import luigi

    seen = []

    class EventTask(luigi.Task):
        pass

    def callback(value):
        seen.append(value)

    EventTask.event_handler("custom-event")(callback)
    EventTask().trigger_event("custom-event", "payload")
    EventTask.remove_event_handler("custom-event", callback)
    EventTask().trigger_event("custom-event", "ignored")
    assert seen == ["payload"]


def test_priority_affects_ready_task_order_after_dependencies_are_satisfied(tmp_path):
    import luigi

    order = []

    class LowReadyTask(luigi.Task):
        priority = 1

        def output(self):
            return luigi.LocalTarget(tmp_path / "low.txt")

        def run(self):
            order.append("low")
            with self.output().open("w") as handle:
                handle.write("low")

    class HighDepTask(luigi.Task):
        priority = 100

        def output(self):
            return luigi.LocalTarget(tmp_path / "dep.txt")

        def run(self):
            order.append("dep")
            with self.output().open("w") as handle:
                handle.write("dep")

    class HighBlockedTask(luigi.Task):
        priority = 100

        def requires(self):
            return HighDepTask()

        def output(self):
            return luigi.LocalTarget(tmp_path / "high.txt")

        def run(self):
            order.append("high")
            with self.output().open("w") as handle:
                handle.write("high")

    assert luigi.build([LowReadyTask(), HighBlockedTask()], local_scheduler=True, workers=1) is True
    assert order.index("dep") < order.index("high")
    assert set(order) == {"low", "dep", "high"}


def test_dynamic_dependency_yield_restarts_task_and_uses_dependency_output(tmp_path):
    import luigi

    runs = []

    class YieldedDep(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "yielded.txt")

        def run(self):
            with self.output().open("w") as handle:
                handle.write("ready")

    class DynamicRoot(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "dynamic-root.txt")

        def run(self):
            runs.append("root")
            if not YieldedDep().complete():
                yield YieldedDep()
            with YieldedDep().output().open("r") as source:
                value = source.read()
            with self.output().open("w") as target:
                target.write(value)

    assert luigi.build([DynamicRoot()], local_scheduler=True, workers=1) is True
    assert runs == ["root", "root"]
    assert (tmp_path / "dynamic-root.txt").read_text(encoding="utf-8") == "ready"


def test_representative_workflow_build_and_second_build_agree_on_completion(tmp_path):
    import luigi

    runs = []

    class DailyWords(luigi.Task):
        day = luigi.DateParameter()
        root = luigi.PathParameter()

        def output(self):
            return luigi.LocalTarget(self.root / f"words-{self.day:%Y-%m-%d}.txt")

        def run(self):
            runs.append("words")
            with self.output().open("w") as handle:
                handle.write("apple\nbanana\n")

    class CountLetters(luigi.Task):
        day = luigi.DateParameter()
        root = luigi.PathParameter()

        def requires(self):
            return DailyWords(day=self.day, root=self.root)

        def output(self):
            return luigi.LocalTarget(self.root / f"counts-{self.day:%Y-%m-%d}.txt")

        def run(self):
            runs.append("count")
            with self.input().open("r") as source:
                words = source.read().splitlines()
            with self.output().open("w") as target:
                for word in words:
                    target.write(f"{word}\\t{len(word)}\\n")

    task = CountLetters(day=dt.date(2026, 7, 10), root=tmp_path)
    assert luigi.build([task], local_scheduler=True, workers=1) is True
    assert (tmp_path / "counts-2026-07-10.txt").read_text(encoding="utf-8") == "apple\\t5\\nbanana\\t6\\n"
    assert luigi.build([task], local_scheduler=True, workers=1) is True
    assert runs == ["words", "count"]


def test_representative_workflow_input_target_feeds_downstream_task(tmp_path):
    import luigi

    class DailyNumbers(luigi.Task):
        day = luigi.DateParameter()
        root = luigi.PathParameter()

        def output(self):
            return luigi.LocalTarget(self.root / f"numbers-{self.day:%Y-%m-%d}.txt")

        def run(self):
            with self.output().open("w") as handle:
                handle.write("2\n4\n6\n")

    class SumNumbers(luigi.Task):
        day = luigi.DateParameter()
        root = luigi.PathParameter()

        def requires(self):
            return DailyNumbers(day=self.day, root=self.root)

        def output(self):
            return luigi.LocalTarget(self.root / f"sum-{self.day:%Y-%m-%d}.txt")

        def run(self):
            with self.input().open("r") as source:
                total = sum(int(line) for line in source.read().splitlines())
            with self.output().open("w") as target:
                target.write(str(total))

    assert luigi.build([SumNumbers(day=dt.date(2026, 7, 11), root=tmp_path)], local_scheduler=True, workers=1) is True
    assert (tmp_path / "sum-2026-07-11.txt").read_text(encoding="utf-8") == "12"


def test_representative_workflow_cli_invocation_writes_downstream_output(tmp_path):
    module = tmp_path / "workflow_representative_cli.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi

            class DailyWords(luigi.Task):
                day = luigi.DateParameter()
                root = luigi.PathParameter()

                def output(self):
                    return luigi.LocalTarget(self.root / f"words-{self.day:%Y-%m-%d}.txt")

                def run(self):
                    with self.output().open("w") as handle:
                        handle.write("pear\\nplum\\n")

            class CountLetters(luigi.Task):
                day = luigi.DateParameter()
                root = luigi.PathParameter()

                def requires(self):
                    return DailyWords(day=self.day, root=self.root)

                def output(self):
                    return luigi.LocalTarget(self.root / f"counts-{self.day:%Y-%m-%d}.txt")

                def run(self):
                    with self.input().open("r") as source:
                        words = source.read().splitlines()
                    with self.output().open("w") as target:
                        for word in words:
                            target.write(f"{word}\\t{len(word)}\\n")
            """
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "luigi",
            "--module",
            "workflow_representative_cli",
            "CountLetters",
            "--day",
            "2026-07-12",
            "--root",
            str(tmp_path),
            "--local-scheduler",
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "counts-2026-07-12.txt").read_text(encoding="utf-8") == "pear\t4\nplum\t4\n"


def test_python_and_cli_projection_create_same_workflow_outputs(tmp_path):
    module = tmp_path / "workflow_projection.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi

            class ProjectionTask(luigi.Task):
                out = luigi.PathParameter()
                value = luigi.IntParameter()

                def output(self):
                    return luigi.LocalTarget(self.out)

                def run(self):
                    with self.output().open("w") as handle:
                        handle.write(str(self.value + 3))
            """
        ),
        encoding="utf-8",
    )
    proc = run_script(
        tmp_path,
        """
        import pathlib
        import luigi
        import workflow_projection
        task = workflow_projection.ProjectionTask(out=pathlib.Path("python.txt"), value=4)
        print(luigi.build([task], local_scheduler=True, workers=1))
        """,
    )
    assert proc.returncode == 0, proc.stderr
    cli_out = tmp_path / "cli-projection.txt"
    cli = subprocess.run(
        [
            sys.executable,
            "-m",
            "luigi",
            "--module",
            "workflow_projection",
            "ProjectionTask",
            "--out",
            str(cli_out),
            "--value",
            "4",
            "--local-scheduler",
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert cli.returncode == 0, cli.stderr
    assert (tmp_path / "python.txt").read_text(encoding="utf-8") == cli_out.read_text(encoding="utf-8") == "7"


def test_task_without_declared_output_does_not_unlock_downstream_as_complete(tmp_path):
    import luigi

    ran = []

    class NoOutputDep(luigi.Task):
        def run(self):
            ran.append("dep")

    class NeedsNoOutputDep(luigi.Task):
        def requires(self):
            return NoOutputDep()

        def output(self):
            return luigi.LocalTarget(tmp_path / "downstream.txt")

        def run(self):
            ran.append("downstream")
            with self.output().open("w") as handle:
                handle.write("done")

    result = luigi.build([NeedsNoOutputDep()], local_scheduler=True, detailed_summary=True, workers=1)
    assert result.status in {
        luigi.LuigiStatusCode.NOT_RUN,
        luigi.LuigiStatusCode.FAILED,
        luigi.LuigiStatusCode.SCHEDULING_FAILED,
    }
    assert "downstream" not in ran


def test_complete_failure_is_reported_as_scheduling_failure(tmp_path):
    import luigi

    class ExplodingCompleteTask(luigi.Task):
        def complete(self):
            raise RuntimeError("cannot check")

    result = luigi.build([ExplodingCompleteTask()], local_scheduler=True, detailed_summary=True, workers=1)
    assert result.status == luigi.LuigiStatusCode.SCHEDULING_FAILED


def test_worker_scheduler_factory_methods_are_used(tmp_path):
    proc = run_script(
        tmp_path,
        """
        import luigi

        class HookReached(Exception):
            pass

        class FactoryTask(luigi.Task):
            pass

        class LocalFactory:
            def create_local_scheduler(self):
                raise HookReached("local")
            def create_remote_scheduler(self, url):
                raise HookReached("remote")
            def create_worker(self, scheduler, worker_processes, assistant=False):
                raise HookReached("worker")

        class WorkerFactory:
            def create_local_scheduler(self):
                return object()
            def create_remote_scheduler(self, url):
                return object()
            def create_worker(self, scheduler, worker_processes, assistant=False):
                raise HookReached(f"worker:{worker_processes}:{assistant}")

        for factory in (LocalFactory(), WorkerFactory()):
            try:
                luigi.build([FactoryTask()], local_scheduler=True, worker_scheduler_factory=factory, workers=2)
            except HookReached as exc:
                print(exc)

        """,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["local", "worker:2:False"]


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


def test_python_module_invocation_matches_luigi_command_shape_for_local_scheduler(tmp_path):
    module = tmp_path / "workflow_module_invocation.py"
    module.write_text(
        textwrap.dedent(
            """
            import luigi
            class ModuleTask(luigi.Task):
                out = luigi.PathParameter()
                def output(self):
                    return luigi.LocalTarget(self.out)
                def run(self):
                    with self.output().open("w") as handle:
                        handle.write("module-ok")
            """
        ),
        encoding="utf-8",
    )
    output = tmp_path / "module.txt"
    proc = subprocess.run(
        [sys.executable, "-m", "luigi", "--module", "workflow_module_invocation", "ModuleTask", "--out", str(output), "--local-scheduler"],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert output.read_text(encoding="utf-8") == "module-ok"


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


def test_summary_text_and_boolean_result_reflect_successful_workflow(tmp_path):
    import luigi

    class SummaryTask(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "summary.txt")

        def run(self):
            with self.output().open("w") as handle:
                handle.write("ok")

    result = luigi.build([SummaryTask()], local_scheduler=True, detailed_summary=True, workers=1)
    assert result.status == luigi.LuigiStatusCode.SUCCESS
    assert result.scheduling_succeeded is True
    assert result.summary_text
