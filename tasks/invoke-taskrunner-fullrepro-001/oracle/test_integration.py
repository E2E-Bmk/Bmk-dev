"""Integration tests — each crosses ≥2 API boundaries."""
import json
import os

import pytest

from conftest import PYTHON, run_invoke, write_file

from invoke import (
    Config,
    Context,
    Program,
    Responder,
    Result,
    Runner,
    UnexpectedExit,
    run,
)


# ── Context + Runner configuration ──────────────────────────────────


def test_context_run_uses_configured_runner_class(fresh_runner):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    config = Config(overrides={"runners": {"local": fresh_runner}})
    ctx = Context(config=config)
    result = ctx.run("compile", hide=True)
    assert result.stdout == "captured\n"
    assert fresh_runner.seen[0][0] == "compile"
    assert fresh_runner.seen[0][2] is ctx


def test_run_creates_anonymous_context_and_returns_result():
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
    result = run(
        f"{PYTHON} -c \"print('anonymous')\"",
        hide=True,
        in_stream=False,
    )
    assert result.stdout == "anonymous\n"
    assert result.ok is True


# ── Context.cd + Context.run ─────────────────────────────────────────


def test_context_cd_changes_cwd_for_command(tmp_path, fresh_runner):
    """Seam: protocol handoff — CLI/collection/context layers route to the same execution pipeline."""
    ctx = Context(config=Config(overrides={"runners": {"local": fresh_runner}}))
    with ctx.cd(str(tmp_path)):
        ctx.run("pwd", hide=True)
    command = fresh_runner.seen[0][0]
    assert command.endswith(" && pwd")
    assert str(tmp_path) in command


# ── Context.prefix + Context.run ─────────────────────────────────────


def test_context_prefix_prepends_command():
    """Seam: protocol handoff — CLI/collection/context layers route to the same execution pipeline."""
    ctx = Context()
    with ctx.prefix(f"{PYTHON} -c \"print('pre')\""):
        result = ctx.run(
            f"{PYTHON} -c \"print('main')\"",
            hide=True,
            in_stream=False,
        )
    lines = result.stdout.splitlines()
    assert lines == ["pre", "main"]


# ── Context.run + watcher ────────────────────────────────────────────


def test_context_run_watcher_responds_and_preserves_output():
    """Seam: state consistency — write/read or serialize/deserialize projections stay aligned."""
    code = (
        "import sys; "
        "sys.stdout.write('Continue? '); sys.stdout.flush(); "
        "answer=sys.stdin.readline().strip(); print(answer)"
    )
    responder = Responder(pattern=r"Continue\? ", response="yes\n")
    result = Context().run(
        f"{PYTHON} -c \"{code}\"",
        watchers=[responder],
        hide=True,
        in_stream=False,
    )
    assert "Continue? " in result.stdout
    assert "yes" in result.stdout


# ── Context.sudo + runner + watchers ──────────────────────────────


def test_context_sudo_builds_prompt_responder():
    """Seam: lifecycle crossing — scheduler execution propagates dependency outputs to downstream tasks."""
    class SudoRunner(Runner):
        seen = []

        def run(self, command, **kwargs):
            self.__class__.seen.append((command, kwargs))
            return Result(command=command, exited=0)

    SudoRunner.seen.clear()
    ctx = Context(
        config=Config(
            overrides={
                "sudo": {"password": "cfgpass"},
                "runners": {"local": SudoRunner},
            }
        )
    )
    result = ctx.sudo("whoami", password="rtpass", user="admin")
    assert result.ok is True
    cmd, kw = SudoRunner.seen[0]
    assert cmd.startswith("sudo ")
    assert "-u admin" in cmd
    assert kw["watchers"]


# ── CLI: --list variants ─────────────────────────────────────────────


def test_cli_list_shows_task_names(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def compile(c):
            pass

        @task
        def package(c):
            pass
        """,
    )
    proc = run_invoke(tmp_path, "--list")
    assert proc.returncode == 0, proc.stderr
    assert "compile" in proc.stdout
    assert "package" in proc.stdout


def test_cli_json_list_reports_tasks_aliases_default(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task, Collection

        @task(aliases=("pub",), default=True)
        def publish(c):
            pass

        ns = Collection("proj", publish)
        """,
    )
    proc = run_invoke(tmp_path, "--list", "--list-format=json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["name"] == "proj"
    t = next(i for i in payload["tasks"] if i["name"] == "publish")
    assert t["aliases"] == ["pub"]


def test_cli_flat_list_dotted_names(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import Collection, task

        @task
        def migrate(c):
            pass

        ns = Collection("root")
        ns.add_collection(Collection("db", migrate))
        """,
    )
    proc = run_invoke(tmp_path, "--list", "--list-format=flat")
    assert proc.returncode == 0, proc.stderr
    assert "db.migrate" in proc.stdout


def test_cli_nested_list_shows_nesting(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import Collection, task

        @task
        def migrate(c):
            pass

        ns = Collection("root")
        ns.add_collection(Collection("db", migrate))
        """,
    )
    proc = run_invoke(tmp_path, "--list", "--list-format=nested")
    assert proc.returncode == 0, proc.stderr
    assert "db" in proc.stdout
    assert "migrate" in proc.stdout


def test_cli_list_depth_json_is_error(tmp_path):
    """Seam: error propagation — subsystem failures surface consistently at the integration boundary."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def compile(c):
            pass
        """,
    )
    proc = run_invoke(tmp_path, "--list", "--list-format=json", "--list-depth=1")
    assert proc.returncode != 0


# ── CLI: task invocation ─────────────────────────────────────────────


def test_cli_default_task_invoked_without_name(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task, Collection

        @task(default=True)
        def publish(c):
            print("published")

        ns = Collection("proj", publish)
        """,
    )
    proc = run_invoke(tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "published"


def test_cli_collection_replaces_default(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "ops.py",
        """
        from invoke import task

        @task
        def check(c):
            print("checked")
        """,
    )
    proc = run_invoke(tmp_path, "--collection=ops", "check")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "checked"


def test_cli_dashed_flag_to_underscore_arg(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c, output_dir):
            print(output_dir)
        """,
    )
    proc = run_invoke(tmp_path, "show", "--output-dir=artifacts")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "artifacts"


def test_cli_inverse_boolean_flag(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def lint(c, strict=True):
            print(strict)
        """,
    )
    proc = run_invoke(tmp_path, "lint", "--no-strict")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "False"


def test_cli_optional_argument_bare_and_valued(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(optional=("format",))
        def export(c, format=None):
            print("FLAG" if format is True else format)
        """,
    )
    bare = run_invoke(tmp_path, "export", "--format")
    valued = run_invoke(tmp_path, "export", "--format=csv")
    assert bare.returncode == 0, bare.stderr
    assert valued.returncode == 0, valued.stderr
    assert bare.stdout.strip() == "FLAG"
    assert valued.stdout.strip() == "csv"


def test_cli_iterable_accumulates(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(iterable=("tag",))
        def publish(c, tag=None):
            print(",".join(tag))
        """,
    )
    proc = run_invoke(tmp_path, "publish", "--tag=v1", "--tag=v2")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "v1,v2"


def test_cli_incrementable_counts(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(incrementable=("debug",))
        def run_task(c, debug=0):
            print(debug)
        """,
    )
    proc = run_invoke(tmp_path, "run-task", "--debug", "--debug", "--debug")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "3"


def test_cli_pre_and_post_tasks(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def setup(c):
            print("setup")

        @task
        def teardown(c):
            print("teardown")

        @task(pre=[setup], post=[teardown])
        def test(c):
            print("test")
        """,
    )
    proc = run_invoke(tmp_path, "test")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["setup", "test", "teardown"]


def test_cli_dedupes_by_default(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def compile(c):
            print("compiled")
        """,
    )
    proc = run_invoke(tmp_path, "compile", "compile")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["compiled"]


def test_cli_no_dedupe_allows_repeat(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def compile(c):
            print("compiled")
        """,
    )
    proc = run_invoke(tmp_path, "--no-dedupe", "compile", "compile")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == ["compiled", "compiled"]


def test_cli_remainder_after_double_dash(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.remainder)
        """,
    )
    proc = run_invoke(tmp_path, "show", "--", "--custom-flag", "value")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "--custom-flag value"


def test_cli_task_custom_name_visible_in_list_and_invocation(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(name="publish")
        def release(c):
            print("published")
        """,
    )
    listed = run_invoke(tmp_path, "--list")
    invoked = run_invoke(tmp_path, "publish")
    assert listed.returncode == 0
    assert "publish" in listed.stdout
    assert invoked.returncode == 0
    assert invoked.stdout.strip() == "published"


# ── CLI: configuration ──────────────────────────────────────────────


def test_cli_project_config_visible_to_task(tmp_path):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.project.artifact)
        """,
    )
    write_file(tmp_path / "invoke.yaml", "project:\n  artifact: bundle\n")
    proc = run_invoke(tmp_path, "show")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "bundle"


def test_cli_env_var_overrides_config(tmp_path):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.config.run.echo)
        """,
    )
    proc = run_invoke(tmp_path, "show", env={"INVOKE_RUN_ECHO": "1"})
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "True"


def test_cli_runtime_config_overrides_project(tmp_path):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(c.project.artifact)
        """,
    )
    write_file(tmp_path / "invoke.yaml", "project:\n  artifact: project-val\n")
    rt = tmp_path / "runtime.yaml"
    write_file(rt, "project:\n  artifact: runtime-val\n")
    proc = run_invoke(tmp_path, "--config", str(rt), "show")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "runtime-val"


def test_cli_run_flag_overrides_config(tmp_path):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    write_file(
        tmp_path / "tasks.py",
        f"""
        from invoke import task

        @task
        def show(c):
            c.run({PYTHON!r} + " -c \\"print('output')\\"")
        """,
    )
    write_file(tmp_path / "invoke.yaml", "run:\n  echo: false\n")
    proc = run_invoke(tmp_path, "--echo", "show")
    assert proc.returncode == 0, proc.stderr
    assert "output" in proc.stdout
    assert "-c" in proc.stdout


# ── CLI: help & errors ──────────────────────────────────────────────


def test_cli_help_includes_docstring_and_options(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(help={"channel": "Release channel."})
        def publish(c, channel="stable"):
            \"\"\"Publish artifact.\"\"\"
            pass
        """,
    )
    proc = run_invoke(tmp_path, "--help", "publish")
    assert proc.returncode == 0, proc.stderr
    assert "Publish artifact." in proc.stdout
    assert "--channel" in proc.stdout
    assert "Release channel." in proc.stdout


def test_cli_unknown_task_exits_unsuccessfully(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(tmp_path / "tasks.py", "from invoke import task\n")
    proc = run_invoke(tmp_path, "nonexistent")
    assert proc.returncode != 0
    assert "nonexistent" in (proc.stderr + proc.stdout)


# ── Program API ──────────────────────────────────────────────────────


def test_program_run_string_argv_exit_false(tmp_path, capsys):
    """Seam: lifecycle crossing — scheduler execution propagates dependency outputs to downstream tasks."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def greet(c):
            print("hi")
        """,
    )
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        Program().run("invoke greet", exit=False)
    finally:
        os.chdir(old)
    assert "hi" in capsys.readouterr().out


def test_program_run_unknown_exit_false(tmp_path, capsys):
    """Seam: lifecycle crossing — scheduler execution propagates dependency outputs to downstream tasks."""
    write_file(tmp_path / "tasks.py", "from invoke import task\n")
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        Program().run("invoke nonexistent", exit=False)
    finally:
        os.chdir(old)
    captured = capsys.readouterr()
    assert "nonexistent" in (captured.out + captured.err)


# ── Cross-view invariant tests ───────────────────────────────────────


def test_collection_alias_in_list_and_invocation(tmp_path):
    """CVI-1: cross-view invariants hold across listing, invocation, and runtime APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task(aliases=("c",), default=True)
        def compile(c):
            print("compiled")
        """,
    )
    listed = run_invoke(tmp_path, "--list", "--list-format=json")
    invoked = run_invoke(tmp_path, "c")
    payload = json.loads(listed.stdout)
    assert listed.returncode == 0
    assert payload["tasks"][0]["name"] == "compile"
    assert payload["tasks"][0]["aliases"] == ["c"]
    assert invoked.returncode == 0
    assert invoked.stdout.strip() == "compiled"


def test_warn_consistency_same_command_different_outcome():
    """CVI-1: cross-view invariants hold across listing, invocation, and runtime APIs."""
    cmd = f"{PYTHON} -c \"import sys; sys.exit(2)\""
    result = Context().run(cmd, hide=True, warn=True, in_stream=False)
    assert result.failed is True
    assert result.exited == 2
    with pytest.raises(UnexpectedExit) as exc_info:
        Context().run(cmd, hide=True, in_stream=False)
    assert exc_info.value.result.exited == 2


def test_from_module_ns_matches_cli_json_list(tmp_path):
    """Seam: protocol handoff — CLI/module entry points delegate to the same core APIs."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import Collection, task

        @task
        def stray(c):
            pass

        @task
        def included(c):
            pass

        ns = Collection("myns", included)
        """,
    )
    proc = run_invoke(tmp_path, "--list", "--list-format=json")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["name"] == "myns"
    names = [t["name"] for t in payload["tasks"]]
    assert "included" in names
    assert "stray" not in names


# ── Workflow integration ──────────────────────────────────────────────


def test_workflow_dependency_and_artifact(tmp_path):
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
    write_file(
        tmp_path / "tasks.py",
        """
        from pathlib import Path
        from invoke import task

        @task
        def prepare(c):
            Path("order.txt").write_text("prepare\\n", encoding="utf-8")

        @task(pre=[prepare])
        def package(c, output="bundle"):
            with Path("order.txt").open("a", encoding="utf-8") as f:
                f.write(f"package:{output}\\n")
        """,
    )
    proc = run_invoke(tmp_path, "package", "--output", "artifact")
    assert proc.returncode == 0, proc.stderr
    lines = (tmp_path / "order.txt").read_text(encoding="utf-8").splitlines()
    assert lines == ["prepare", "package:artifact"]


def test_workflow_merges_config_layers(tmp_path):
    """Seam: config interaction — multiple configuration sources merge into one runtime view."""
    write_file(
        tmp_path / "tasks.py",
        """
        from invoke import task

        @task
        def show(c):
            print(f"{c.release.channel}:{c.release.version}")
        """,
    )
    write_file(
        tmp_path / "invoke.yaml",
        """
        release:
          channel: project
          version: 1
        """,
    )
    rt = tmp_path / "runtime.yaml"
    write_file(
        rt,
        """
        release:
          version: 5
        """,
    )
    proc = run_invoke(
        tmp_path,
        "--config",
        str(rt),
        "show",
        env={"INVOKE_RELEASE_CHANNEL": "environment"},
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "environment:5"


def test_workflow_default_task_uses_context_runner(tmp_path):
    """Seam: lifecycle crossing — create/use/teardown phases preserve observable state."""
    write_file(
        tmp_path / "tasks.py",
        """
        import sys
        from invoke import task

        @task(default=True)
        def inspect(c):
            result = c.run(sys.executable + ' -c "print(42)"', hide=True)
            print(f"{result.ok}:{result.stdout.strip()}")
        """,
    )
    write_file(tmp_path / "invoke.yaml", "run:\n  warn: false\n")
    proc = run_invoke(tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "True:42"
