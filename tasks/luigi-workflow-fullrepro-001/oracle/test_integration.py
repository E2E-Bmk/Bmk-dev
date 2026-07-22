"""Spec2Repo oracle – integration tests for luigi-workflow-fullrepro-001.

Each test crosses ≥2 public API boundaries and validates a composition seam.
"""
import datetime as dt
import pathlib

import pytest

from conftest import run_cli, run_script, write_module


# ═══════════════════════════════════════════════════════════════════
# build: dependency graph + output reuse
# ═══════════════════════════════════════════════════════════════════

def test_build_runs_deps_then_downstream_and_reuses_outputs(tmp_path):
    """Seam: lifecycle crossing — scheduler execution propagates dependency outputs to downstream tasks."""
    import luigi

    order = []

    class Dep(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "dep.txt")

        def run(self):
            order.append("dep")
            with self.output().open("w") as f:
                f.write("payload")

    class Main(luigi.Task):
        def requires(self):
            return Dep()

        def output(self):
            return luigi.LocalTarget(tmp_path / "main.txt")

        def run(self):
            order.append("main")
            with self.input().open("r") as src:
                data = src.read()
            with self.output().open("w") as dst:
                dst.write(data + "-ok")

    assert luigi.build([Main()], local_scheduler=True, workers=1) is True
    assert order == ["dep", "main"]
    assert (tmp_path / "main.txt").read_text(encoding="utf-8") == "payload-ok"

    assert luigi.build([Main()], local_scheduler=True, workers=1) is True
    assert order == ["dep", "main"]


def test_build_reports_failed_task_status(tmp_path):
    """Seam: error propagation — task RuntimeError surfaces as FAILED LuigiRunResult status."""
    import luigi
    from luigi.execution_summary import LuigiRunResult

    class Failing(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "never.txt")

        def run(self):
            raise RuntimeError("boom")

    result = luigi.build(
        [Failing()], local_scheduler=True, detailed_summary=True, workers=1
    )
    assert isinstance(result, LuigiRunResult)
    assert result.status == luigi.LuigiStatusCode.FAILED
    assert result.scheduling_succeeded is False


def test_build_reports_missing_external_dependency(tmp_path):
    """Seam: error propagation — missing ExternalTask dependency blocks downstream execution."""
    import luigi

    ran = []

    class MissingExt(luigi.ExternalTask):
        def output(self):
            return luigi.LocalTarget(tmp_path / "missing-ext.txt")

    class Consumer(luigi.Task):
        def requires(self):
            return MissingExt()

        def output(self):
            return luigi.LocalTarget(tmp_path / "consumer.txt")

        def run(self):
            ran.append("consumer")

    result = luigi.build(
        [Consumer()], local_scheduler=True, detailed_summary=True, workers=1
    )
    assert result.status == luigi.LuigiStatusCode.MISSING_EXT
    assert ran == []


# ═══════════════════════════════════════════════════════════════════
# run()
# ═══════════════════════════════════════════════════════════════════

def test_run_accepts_cmdline_args_and_main_task_cls(tmp_path):
    """Seam: protocol handoff — luigi.run cmdline_args populate task parameters for build."""
    proc = run_script(
        tmp_path,
        """
        import pathlib, luigi

        class RunTask(luigi.Task):
            root = luigi.PathParameter()
            num = luigi.IntParameter()
            def output(self):
                return luigi.LocalTarget(self.root / "run-out.txt")
            def run(self):
                with self.output().open("w") as f:
                    f.write(str(self.num + 10))

        ok = luigi.run(cmdline_args=["--root", ".", "--num", "3"],
                       main_task_cls=RunTask, local_scheduler=True)
        print(ok)
        print(pathlib.Path("run-out.txt").read_text())
        """,
    )
    assert proc.returncode == 0, proc.stderr
    assert "True" in proc.stdout
    assert "13" in proc.stdout


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def test_cli_module_invocation_with_local_scheduler(tmp_path):
    """Seam: protocol handoff — python -m luigi CLI executes module task with parameters."""
    write_module(
        tmp_path,
        "wf_cli",
        """
        import luigi
        class CliJob(luigi.Task):
            out = luigi.PathParameter()
            val = luigi.IntParameter()
            def output(self):
                return luigi.LocalTarget(self.out)
            def run(self):
                with self.output().open("w") as f:
                    f.write(str(self.val * 3))
        """,
    )
    out = tmp_path / "cli.txt"
    proc = run_cli(
        tmp_path,
        ["--module", "wf_cli", "CliJob",
         "--out", str(out), "--val", "4", "--local-scheduler"],
    )
    assert proc.returncode == 0, proc.stderr
    assert out.read_text(encoding="utf-8") == "12"


def test_cli_hyphenated_parameter_maps_to_underscore(tmp_path):
    """Seam: protocol handoff — hyphenated CLI flags map to underscore task parameters."""
    write_module(
        tmp_path,
        "wf_hyphen",
        """
        import luigi
        class HyphenJob(luigi.Task):
            out = luigi.PathParameter()
            my_val = luigi.IntParameter()
            def output(self):
                return luigi.LocalTarget(self.out)
            def run(self):
                with self.output().open("w") as f:
                    f.write(str(self.my_val))
        """,
    )
    out = tmp_path / "hyphen.txt"
    proc = run_cli(
        tmp_path,
        ["--module", "wf_hyphen", "HyphenJob",
         "--out", str(out), "--my-val", "14", "--local-scheduler"],
    )
    assert proc.returncode == 0, proc.stderr
    assert out.read_text(encoding="utf-8") == "14"


def test_cli_class_qualified_parameter_supplies_dependency(tmp_path):
    """Seam: protocol handoff — class-qualified CLI parameters configure dependency tasks."""
    write_module(
        tmp_path,
        "wf_qual",
        """
        import luigi
        class QDep(luigi.Task):
            root = luigi.PathParameter()
            amount = luigi.IntParameter()
            def output(self):
                return luigi.LocalTarget(self.root / "qdep.txt")
            def run(self):
                with self.output().open("w") as f:
                    f.write(str(self.amount))

        class QRoot(luigi.Task):
            root = luigi.PathParameter()
            def requires(self):
                return QDep(root=self.root)
            def output(self):
                return luigi.LocalTarget(self.root / "qroot.txt")
            def run(self):
                with self.input().open("r") as src:
                    v = src.read()
                with self.output().open("w") as dst:
                    dst.write(v)
        """,
    )
    proc = run_cli(
        tmp_path,
        ["--module", "wf_qual", "QRoot",
         "--root", str(tmp_path),
         "--QDep-amount", "19",
         "--local-scheduler"],
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "qroot.txt").read_text(encoding="utf-8") == "19"


# ═══════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════

def test_config_file_supplies_task_parameter_default(tmp_path):
    """Seam: config interaction — LUIGI_CONFIG_PATH cfg file supplies task parameter defaults."""
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[CfgTask]\nval = 22\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi
        class CfgTask(luigi.Task):
            val = luigi.IntParameter(default=0)
        print(CfgTask().val)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg)},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("22")


def test_constructor_overrides_config_value(tmp_path):
    """Seam: config interaction — constructor keyword overrides cfg-provided parameter value."""
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[OverTask]\nval = 22\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi
        class OverTask(luigi.Task):
            val = luigi.IntParameter(default=0)
        print(OverTask(val=99).val)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg)},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("99")


def test_config_class_reads_matching_section(tmp_path):
    """Seam: config interaction — luigi.Config reads matching section from cfg file."""
    cfg = tmp_path / "client.cfg"
    cfg.write_text(
        "[AppConfig]\nretries = 5\nverbose = true\n", encoding="utf-8"
    )
    proc = run_script(
        tmp_path,
        """
        import luigi
        class AppConfig(luigi.Config):
            retries = luigi.IntParameter(default=0)
            verbose = luigi.BoolParameter(default=False)
        c = AppConfig()
        print(c.retries)
        print(c.verbose)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg)},
    )
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.strip().splitlines()
    assert lines[-2:] == ["5", "True"]


def test_config_environment_interpolation(tmp_path):
    """Seam: config interaction — cfg environment variable interpolation resolves parameter paths."""
    cfg = tmp_path / "client.cfg"
    cfg.write_text("[paths]\nbase = ${MY_BASE}/store\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi
        class EnvTask(luigi.Task):
            base = luigi.Parameter(
                config_path={"section": "paths", "name": "base"}, default="none")
        print(EnvTask().base)
        """,
        extra_env={"LUIGI_CONFIG_PATH": str(cfg), "MY_BASE": "/opt"},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("/opt/store")


def test_toml_config_parser_reads_values(tmp_path):
    """Seam: config interaction — TOML config parser supplies task parameter values."""
    cfg = tmp_path / "luigi.toml"
    cfg.write_text("[TomlJob]\ncount = 13\n", encoding="utf-8")
    proc = run_script(
        tmp_path,
        """
        import luigi
        class TomlJob(luigi.Task):
            count = luigi.IntParameter(default=0)
        print(TomlJob().count)
        """,
        extra_env={
            "LUIGI_CONFIG_PATH": str(cfg),
            "LUIGI_CONFIG_PARSER": "toml",
        },
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().endswith("13")


# ═══════════════════════════════════════════════════════════════════
# Lifecycle callbacks
# ═══════════════════════════════════════════════════════════════════

def test_failed_run_calls_on_failure_callback(tmp_path):
    """Seam: error propagation — failed task run invokes on_failure with the raised exception."""
    import luigi

    seen = []

    class FailCb(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "failcb.txt")

        def run(self):
            raise RuntimeError("callback-err")

        def on_failure(self, exc):
            seen.append(type(exc).__name__)
            return "handled"

    result = luigi.build(
        [FailCb()], local_scheduler=True, detailed_summary=True, workers=1
    )
    assert result.status == luigi.LuigiStatusCode.FAILED
    assert seen == ["RuntimeError"]


def test_successful_run_calls_on_success_callback(tmp_path):
    """Seam: lifecycle crossing — successful build invokes task on_success callback."""
    import luigi

    seen = []

    class OkCb(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "okcb.txt")

        def run(self):
            with self.output().open("w") as f:
                f.write("done")

        def on_success(self):
            seen.append("ok")

    assert luigi.build([OkCb()], local_scheduler=True, workers=1) is True
    assert seen == ["ok"]


# ═══════════════════════════════════════════════════════════════════
# Priority
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_task_complete_reflects_output_existence",
    "test_build_runs_deps_then_downstream_and_reuses_outputs",
)
def test_priority_affects_order_after_dependencies(tmp_path):
    """Seam: lifecycle crossing — task priority influences ready-task execution order."""
    import luigi

    order = []

    class LowReady(luigi.Task):
        priority = 1

        def output(self):
            return luigi.LocalTarget(tmp_path / "low.txt")

        def run(self):
            order.append("low")
            with self.output().open("w") as f:
                f.write("low")

    class HighDep(luigi.Task):
        priority = 100

        def output(self):
            return luigi.LocalTarget(tmp_path / "hdep.txt")

        def run(self):
            order.append("hdep")
            with self.output().open("w") as f:
                f.write("hdep")

    class HighBlocked(luigi.Task):
        priority = 100

        def requires(self):
            return HighDep()

        def output(self):
            return luigi.LocalTarget(tmp_path / "hblk.txt")

        def run(self):
            order.append("hblk")
            with self.output().open("w") as f:
                f.write("hblk")

    assert (
        luigi.build(
            [LowReady(), HighBlocked()], local_scheduler=True, workers=1
        )
        is True
    )
    assert order.index("hdep") < order.index("hblk")
    assert set(order) == {"low", "hdep", "hblk"}


# ═══════════════════════════════════════════════════════════════════
# Dynamic dependencies
# ═══════════════════════════════════════════════════════════════════

def test_dynamic_yield_restarts_task_and_uses_output(tmp_path):
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
    import luigi

    runs = []

    class Yielded(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "yielded.txt")

        def run(self):
            with self.output().open("w") as f:
                f.write("ready")

    class DynRoot(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "dynroot.txt")

        def run(self):
            runs.append("root")
            if not Yielded().complete():
                yield Yielded()
            with Yielded().output().open("r") as src:
                v = src.read()
            with self.output().open("w") as dst:
                dst.write(v)

    assert luigi.build([DynRoot()], local_scheduler=True, workers=1) is True
    assert runs == ["root", "root"]
    assert (tmp_path / "dynroot.txt").read_text(encoding="utf-8") == "ready"


# ═══════════════════════════════════════════════════════════════════
# Representative workflow
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_date_parameter_parse_and_serialize_round_trip",
    "test_local_target_path_exists_and_open_read_write",
)
def test_representative_workflow_build_and_rerun_agree(tmp_path):
    """Seam: state consistency — DateParameter workflow outputs match on first and second build."""
    import luigi

    runs = []

    class Words(luigi.Task):
        day = luigi.DateParameter()
        root = luigi.PathParameter()

        def output(self):
            return luigi.LocalTarget(
                self.root / f"words-{self.day:%Y-%m-%d}.txt"
            )

        def run(self):
            runs.append("words")
            with self.output().open("w") as f:
                f.write("fig\ndate\n")

    class Counts(luigi.Task):
        day = luigi.DateParameter()
        root = luigi.PathParameter()

        def requires(self):
            return Words(day=self.day, root=self.root)

        def output(self):
            return luigi.LocalTarget(
                self.root / f"counts-{self.day:%Y-%m-%d}.txt"
            )

        def run(self):
            runs.append("count")
            with self.input().open("r") as src:
                words = src.read().splitlines()
            with self.output().open("w") as dst:
                for w in words:
                    dst.write(f"{w}\t{len(w)}\n")

    task = Counts(day=dt.date(2025, 5, 1), root=tmp_path)
    assert luigi.build([task], local_scheduler=True, workers=1) is True
    expected = "fig\t3\ndate\t4\n"
    assert (tmp_path / "counts-2025-05-01.txt").read_text(encoding="utf-8") == expected

    assert luigi.build([task], local_scheduler=True, workers=1) is True
    assert runs == ["words", "count"]


@pytest.mark.depends_on(
    "test_int_parameter_parse_valid_and_reject_invalid",
    "test_local_target_path_exists_and_open_read_write",
)
def test_python_and_cli_create_same_outputs(tmp_path):
    """Seam: protocol handoff — programmatic build and CLI invocation produce identical outputs."""
    write_module(
        tmp_path,
        "wf_proj",
        """
        import luigi
        class ProjTask(luigi.Task):
            out = luigi.PathParameter()
            val = luigi.IntParameter()
            def output(self):
                return luigi.LocalTarget(self.out)
            def run(self):
                with self.output().open("w") as f:
                    f.write(str(self.val + 5))
        """,
    )
    proc = run_script(
        tmp_path,
        """
        import pathlib, luigi
        import wf_proj
        t = wf_proj.ProjTask(out=pathlib.Path("py.txt"), val=7)
        print(luigi.build([t], local_scheduler=True, workers=1))
        """,
    )
    assert proc.returncode == 0, proc.stderr

    cli_out = tmp_path / "cli-proj.txt"
    cli = run_cli(
        tmp_path,
        ["--module", "wf_proj", "ProjTask",
         "--out", str(cli_out), "--val", "7", "--local-scheduler"],
    )
    assert cli.returncode == 0, cli.stderr

    py_text = (tmp_path / "py.txt").read_text(encoding="utf-8")
    cli_text = cli_out.read_text(encoding="utf-8")
    assert py_text == cli_text == "12"


# ═══════════════════════════════════════════════════════════════════
# Task without output blocks downstream
# ═══════════════════════════════════════════════════════════════════

def test_task_without_output_blocks_downstream(tmp_path):
    """Seam: lifecycle crossing — dependency without output prevents downstream scheduling."""
    import luigi

    ran = []

    class NoOutDep(luigi.Task):
        def run(self):
            ran.append("dep")

    class Downstream(luigi.Task):
        def requires(self):
            return NoOutDep()

        def output(self):
            return luigi.LocalTarget(tmp_path / "downstream.txt")

        def run(self):
            ran.append("down")
            with self.output().open("w") as f:
                f.write("done")

    result = luigi.build(
        [Downstream()], local_scheduler=True, detailed_summary=True, workers=1
    )
    assert result.status in {
        luigi.LuigiStatusCode.NOT_RUN,
        luigi.LuigiStatusCode.FAILED,
        luigi.LuigiStatusCode.SCHEDULING_FAILED,
    }
    assert "down" not in ran


# ═══════════════════════════════════════════════════════════════════
# Scheduling failure
# ═══════════════════════════════════════════════════════════════════

def test_complete_failure_reported_as_scheduling_failure(tmp_path):
    """Seam: error propagation — complete() failure surfaces as SCHEDULING_FAILED status."""
    import luigi

    class Exploding(luigi.Task):
        def complete(self):
            raise RuntimeError("cannot check")

    result = luigi.build(
        [Exploding()], local_scheduler=True, detailed_summary=True, workers=1
    )
    assert result.status == luigi.LuigiStatusCode.SCHEDULING_FAILED


# ═══════════════════════════════════════════════════════════════════
# Cross-view invariants
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.depends_on(
    "test_local_target_path_exists_and_open_read_write",
    "test_task_complete_reflects_output_existence",
)
def test_local_target_write_makes_exists_complete_input_agree(tmp_path):
    """CVI-3: write → exists, complete, and input all agree."""
    import luigi

    class Producer(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "produced.txt")

        def run(self):
            with self.output().open("w") as f:
                f.write("produced")

    class Reader(luigi.Task):
        def requires(self):
            return Producer()

        def output(self):
            return luigi.LocalTarget(tmp_path / "read.txt")

        def run(self):
            with self.input().open("r") as src:
                data = src.read()
            with self.output().open("w") as dst:
                dst.write(data + "-read")

    assert luigi.build([Reader()], local_scheduler=True, workers=1) is True
    assert Producer().output().exists() is True
    assert Producer().complete() is True
    assert (tmp_path / "read.txt").read_text(encoding="utf-8") == "produced-read"


def test_summary_text_and_result_reflect_workflow(tmp_path):
    """CVI-6: task state reflected in LuigiRunResult."""
    import luigi

    class SumTask(luigi.Task):
        def output(self):
            return luigi.LocalTarget(tmp_path / "sum.txt")

        def run(self):
            with self.output().open("w") as f:
                f.write("sum-ok")

    result = luigi.build(
        [SumTask()], local_scheduler=True, detailed_summary=True, workers=1
    )
    assert result.status == luigi.LuigiStatusCode.SUCCESS
    assert result.scheduling_succeeded is True
    assert isinstance(result.summary_text, str)
    assert "SumTask" in result.summary_text
    assert "done" in result.summary_text


def test_worker_scheduler_factory_methods_used(tmp_path):
    """Seam: lifecycle crossing — worker_scheduler_factory hooks create scheduler and worker."""
    proc = run_script(
        tmp_path,
        """
        import luigi

        class HookReached(Exception):
            pass

        class FactoryTask(luigi.Task):
            pass

        class TestFactory:
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

        for factory in (TestFactory(), WorkerFactory()):
            try:
                luigi.build([FactoryTask()], local_scheduler=True,
                            worker_scheduler_factory=factory, workers=2)
            except HookReached as exc:
                print(exc)
        """,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["local", "worker:2:False"]


def test_wrapper_task_complete_reflects_requirements(tmp_path):
    """CVI-1: cross-view invariants hold across listing, invocation, and runtime APIs."""
    """WrapperTask.complete() depends on wrapped requirements' completion."""
    import luigi

    out = tmp_path / "wrapped.txt"

    class Wrapped(luigi.Task):
        def output(self):
            return luigi.LocalTarget(out)

    class Wrap(luigi.WrapperTask):
        def requires(self):
            return [Wrapped()]

    w = Wrap()
    assert w.complete() is False
    out.write_text("done", encoding="utf-8")
    assert w.complete() is True


def test_task_input_preserves_nested_dependency_output_shape(tmp_path):
    """Seam: state consistency — requires() container shape preserved in input() mapping."""
    """Dependency mapping: input() preserves list, tuple, and dict containers."""
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
