# Spec2Repo oracle - integration tests for dvc-fullrepro-001
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from dvc.repo import Repo


def run_dvc(cwd, *args, check=True):
    env = os.environ.copy()
    env["DVC_TEST"] = "true"
    env["DVC_NO_ANALYTICS"] = "1"
    result = subprocess.run(
        ["dvc", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=env,
        timeout=90,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            {
                "args": args,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    return result


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    Repo.init(root_dir=str(path), no_scm=True)
    return path


def add_copy_stage(root):
    (root / "raw.txt").write_text("alpha\n", encoding="utf-8")
    (root / "copy_upper.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path(sys.argv[2]).write_text(Path(sys.argv[1]).read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
        encoding="utf-8",
    )
    return run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "prepare",
        "-d",
        "raw.txt",
        "-d",
        "copy_upper.py",
        "-o",
        "prepared.txt",
        sys.executable,
        "copy_upper.py",
        "raw.txt",
        "prepared.txt",
    )


def add_counting_stage(root):
    (root / "raw.txt").write_text("one\n", encoding="utf-8")
    (root / "counting.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "count = Path('run_count.txt')\n"
        "n = int(count.read_text() or '0') if count.exists() else 0\n"
        "count.write_text(str(n + 1), encoding='utf-8')\n"
        "Path(sys.argv[2]).write_text(Path(sys.argv[1]).read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "prepare",
        "-d",
        "raw.txt",
        "-d",
        "counting.py",
        "-o",
        "prepared.txt",
        sys.executable,
        "counting.py",
        "raw.txt",
        "prepared.txt",
    )


def add_output_writer(root):
    (root / "writer.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "mode = sys.argv[1]\n"
        "if mode == 'nonpersist':\n"
        "    Path('saw_existing.txt').write_text(str(Path('result.txt').exists()), encoding='utf-8')\n"
        "    Path('result.txt').write_text('fresh', encoding='utf-8')\n"
        "elif mode == 'persist':\n"
        "    p = Path('persist.txt')\n"
        "    p.write_text((p.read_text(encoding='utf-8') if p.exists() else '') + 'x', encoding='utf-8')\n"
        "elif mode == 'nocache':\n"
        "    Path('nocache.txt').write_text('tracked', encoding='utf-8')\n"
        "elif mode == 'metric':\n"
        "    Path('metrics.json').write_text('{\"score\": 7}', encoding='utf-8')\n"
        "elif mode == 'plot':\n"
        "    Path('plot.csv').write_text('x,y\\n1,2\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )


def add_param_stage(root):
    (root / "params.yaml").write_text("alpha: red\n", encoding="utf-8")
    (root / "param_writer.py").write_text(
        "from pathlib import Path\n"
        "import yaml\n"
        "data = yaml.safe_load(Path('params.yaml').read_text(encoding='utf-8'))\n"
        "Path('param_out.txt').write_text(data['alpha'], encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "paramstage",
        "-p",
        "alpha",
        "-o",
        "param_out.txt",
        sys.executable,
        "param_writer.py",
    )


def add_two_stage_pipeline(root):
    (root / "raw.txt").write_text("a", encoding="utf-8")
    (root / "prepare.py").write_text(
        "from pathlib import Path\n"
        "Path('prepared.txt').write_text(Path('raw.txt').read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text(
        "from pathlib import Path\n"
        "Path('model.txt').write_text(Path('prepared.txt').read_text(encoding='utf-8') + ':model', encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "prepare",
        "-d",
        "raw.txt",
        "-d",
        "prepare.py",
        "-o",
        "prepared.txt",
        sys.executable,
        "prepare.py",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "train",
        "-d",
        "prepared.txt",
        "-d",
        "train.py",
        "-o",
        "model.txt",
        sys.executable,
        "train.py",
    )


def add_cached_counting_stage(root):
    (root / "seed.txt").write_text("seed", encoding="utf-8")
    (root / "producer.py").write_text(
        "from pathlib import Path\n"
        "counter = Path('counter.txt')\n"
        "n = int(counter.read_text() or '0') if counter.exists() else 0\n"
        "counter.write_text(str(n + 1), encoding='utf-8')\n"
        "Path('data.txt').write_text(Path('seed.txt').read_text(encoding='utf-8') + ':' + str(n + 1), encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "produce",
        "-d",
        "seed.txt",
        "-d",
        "producer.py",
        "-o",
        "data.txt",
        sys.executable,
        "producer.py",
    )


def add_always_changed_stage(root):
    (root / "always.py").write_text(
        "from pathlib import Path\n"
        "counter = Path('always_count.txt')\n"
        "n = int(counter.read_text() or '0') if counter.exists() else 0\n"
        "counter.write_text(str(n + 1), encoding='utf-8')\n"
        "Path('always.txt').write_text(str(n + 1), encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "always",
        "--always-changed",
        "-d",
        "always.py",
        "-o",
        "always.txt",
        sys.executable,
        "always.py",
    )


def test_stage_add_success_exit_code(tmp_path):
    root = init_repo(tmp_path / "repo")
    assert add_copy_stage(root).returncode == 0


def test_stage_add_writes_named_stage_to_dvc_yaml(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    assert sorted(load_yaml(root / "dvc.yaml")["stages"]) == ["prepare"]


def test_stage_add_without_run_does_not_create_lockfile(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    assert not (root / "dvc.lock").exists()


def test_stage_list_name_only_reports_created_stage(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    assert run_dvc(root, "stage", "list", "--name-only").stdout.split() == ["prepare"]


def test_repro_no_commit_executes_command_and_writes_output(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    result = run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert result.returncode == 0
    assert (root / "prepared.txt").read_text(encoding="utf-8") == "ALPHA\n"


def test_repro_no_commit_writes_public_lock_stage(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert sorted(load_yaml(root / "dvc.lock")["stages"]) == ["prepare"]


def test_status_json_reports_no_commit_output_not_in_cache(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    status = json.loads(run_dvc(root, "status", "--json").stdout)
    assert "prepare" in status and status["prepare"]


def test_status_quiet_is_nonzero_when_pipeline_has_reported_changes(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert run_dvc(root, "status", "--quiet", check=False).returncode != 0


def test_status_json_changes_after_dependency_file_changes(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    run_dvc(root, "repro")
    (root / "raw.txt").write_text("beta\n", encoding="utf-8")
    assert json.loads(run_dvc(root, "status", "--json").stdout)


def test_dry_repro_does_not_modify_workspace_output(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "raw.txt").write_text("beta\n", encoding="utf-8")
    result = run_dvc(root, "repro", "--dry", "--no-run-cache", "prepare")
    assert result.returncode == 0
    assert (root / "prepared.txt").read_text(encoding="utf-8") == "ALPHA\n"


def test_force_repro_updates_workspace_output(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "raw.txt").write_text("beta\n", encoding="utf-8")
    result = run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "prepare")
    assert result.returncode == 0
    assert (root / "prepared.txt").read_text(encoding="utf-8") == "BETA\n"


def test_no_commit_repro_runs_stage_each_time_when_output_is_uncached(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    first = (root / "run_count.txt").read_text(encoding="utf-8")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert [first, (root / "run_count.txt").read_text(encoding="utf-8")] == ["1", "2"]


def test_no_commit_repro_runs_after_dependency_change(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "raw.txt").write_text("two\n", encoding="utf-8")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "run_count.txt").read_text(encoding="utf-8") == "2"


def test_no_commit_repro_runs_after_output_deletion(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "prepared.txt").unlink()
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "run_count.txt").read_text(encoding="utf-8") == "2"


def test_no_commit_repro_recreates_deleted_output(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "prepared.txt").unlink()
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "prepared.txt").read_text(encoding="utf-8") == "ONE\n"


def test_nonpersistent_outputs_are_removed_before_forced_rerun(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_output_writer(root)
    run_dvc(root, "stage", "add", "-n", "nonpersist", "-d", "writer.py", "-o", "result.txt", "-o", "saw_existing.txt", sys.executable, "writer.py", "nonpersist")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "nonpersist")
    run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "nonpersist")
    assert (root / "saw_existing.txt").read_text(encoding="utf-8") == "False"


def test_persistent_outputs_remain_before_forced_rerun(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_output_writer(root)
    run_dvc(root, "stage", "add", "-n", "persist", "-d", "writer.py", "--outs-persist", "persist.txt", sys.executable, "writer.py", "persist")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "persist")
    run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "persist")
    assert (root / "persist.txt").read_text(encoding="utf-8") == "xx"


def test_outs_no_cache_is_serialized_with_cache_false(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_output_writer(root)
    run_dvc(root, "stage", "add", "-n", "nocache", "-d", "writer.py", "-O", "nocache.txt", sys.executable, "writer.py", "nocache")
    outs = load_yaml(root / "dvc.yaml")["stages"]["nocache"]["outs"]
    assert outs == [{"nocache.txt": {"cache": False}}]


def test_missing_no_cache_output_reports_status_change(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_output_writer(root)
    run_dvc(root, "stage", "add", "-n", "nocache", "-d", "writer.py", "-O", "nocache.txt", sys.executable, "writer.py", "nocache")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "nocache")
    (root / "nocache.txt").unlink()
    assert json.loads(run_dvc(root, "status", "--json").stdout)


def test_metric_output_is_recorded_in_lockfile_outputs(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_output_writer(root)
    run_dvc(root, "stage", "add", "-n", "metric", "-d", "writer.py", "-M", "metrics.json", sys.executable, "writer.py", "metric")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "metric")
    outs = load_yaml(root / "dvc.lock")["stages"]["metric"]["outs"]
    assert [out["path"] for out in outs] == ["metrics.json"]


def test_plot_output_is_recorded_in_lockfile_outputs(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_output_writer(root)
    run_dvc(root, "stage", "add", "-n", "plot", "-d", "writer.py", "--plots", "plot.csv", sys.executable, "writer.py", "plot")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "plot")
    outs = load_yaml(root / "dvc.lock")["stages"]["plot"]["outs"]
    assert [out["path"] for out in outs] == ["plot.csv"]


def add_wdir_stage(root):
    (root / "sub").mkdir()
    (root / "sub" / "input.txt").write_text("hi", encoding="utf-8")
    (root / "sub" / "env_stage.py").write_text(
        "from pathlib import Path\n"
        "import os\n"
        "Path('env.txt').write_text(os.environ.get('DVC_ROOT', '') + '\\n' + os.environ.get('DVC_STAGE', ''), encoding='utf-8')\n"
        "Path('output.txt').write_text(Path('input.txt').read_text(encoding='utf-8') + '!', encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_dvc(root, "stage", "add", "-n", "envstage", "-w", "sub", "-d", "input.txt", "-o", "output.txt", sys.executable, "env_stage.py")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "envstage")


def test_stage_wdir_runs_command_from_declared_directory(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_wdir_stage(root)
    assert (root / "sub" / "output.txt").read_text(encoding="utf-8") == "hi!"


def test_stage_command_receives_dvc_root_environment(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_wdir_stage(root)
    lines = (root / "sub" / "env.txt").read_text(encoding="utf-8").splitlines()
    assert Path(lines[0]) == root


def test_stage_command_receives_dvc_stage_environment(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_wdir_stage(root)
    lines = (root / "sub" / "env.txt").read_text(encoding="utf-8").splitlines()
    assert lines[1] == "envstage"


def add_command_list_stage(root, failing=False):
    (root / "first.py").write_text("from pathlib import Path\nPath('first.txt').write_text('1', encoding='utf-8')\n", encoding="utf-8")
    if failing:
        (root / "first.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    (root / "second.py").write_text("from pathlib import Path\nPath('second.txt').write_text((Path('first.txt').read_text(encoding='utf-8') if Path('first.txt').exists() else '') + '2', encoding='utf-8')\n", encoding="utf-8")
    data = {"stages": {"chain": {"cmd": [f'"{sys.executable}" first.py', f'"{sys.executable}" second.py'], "deps": ["first.py", "second.py"], "outs": ["second.txt"]}}}
    (root / "dvc.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return run_dvc(root, "repro", "--no-commit", "--no-run-cache", "chain", check=not failing)


def test_command_list_runs_commands_in_order(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_command_list_stage(root)
    assert (root / "second.txt").read_text(encoding="utf-8") == "12"


def test_list_command_failure_stops_later_commands(tmp_path):
    root = init_repo(tmp_path / "repo")
    commands = [
        (
            f'"{sys.executable}" -c "from pathlib import Path; '
            "Path('first.txt').write_text('first', encoding='utf-8')\""
        ),
        f'"{sys.executable}" -c "import sys; sys.exit(7)"',
        (
            f'"{sys.executable}" -c "from pathlib import Path; '
            "Path('later.txt').write_text('later', encoding='utf-8')\""
        ),
    ]
    (root / "dvc.yaml").write_text(
        yaml.safe_dump(
            {"stages": {"chain": {"cmd": commands}}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    result = run_dvc(
        root,
        "repro",
        "--no-commit",
        "--no-run-cache",
        "chain",
        check=False,
    )
    assert result.returncode != 0
    assert (root / "first.txt").read_text(encoding="utf-8") == "first"
    assert not (root / "later.txt").exists()


def test_params_dependency_initial_repro_uses_param_value(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_param_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    assert (root / "param_out.txt").read_text(encoding="utf-8") == "red"


def test_params_change_reports_status_change(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_param_stage(root)
    run_dvc(root, "repro")
    (root / "params.yaml").write_text("alpha: blue\n", encoding="utf-8")
    assert json.loads(run_dvc(root, "status", "--json").stdout)


def test_freeze_writes_frozen_to_stage_definition(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_param_stage(root)
    run_dvc(root, "freeze", "paramstage")
    assert load_yaml(root / "dvc.yaml")["stages"]["paramstage"]["frozen"] is True


def test_frozen_stage_does_not_reproduce_changed_params(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_param_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    (root / "params.yaml").write_text("alpha: blue\n", encoding="utf-8")
    run_dvc(root, "freeze", "paramstage")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    assert (root / "param_out.txt").read_text(encoding="utf-8") == "red"


def test_unfreeze_removes_frozen_flag_and_repro_updates_output(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_param_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    (root / "params.yaml").write_text("alpha: blue\n", encoding="utf-8")
    run_dvc(root, "freeze", "paramstage")
    run_dvc(root, "unfreeze", "paramstage")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    stage = load_yaml(root / "dvc.yaml")["stages"]["paramstage"]
    assert stage.get("frozen") is None
    assert (root / "param_out.txt").read_text(encoding="utf-8") == "blue"


def add_simple_stage(root, name, output):
    return run_dvc(root, "stage", "add", "-n", name, "-o", output, sys.executable, "-c", f"open('{output}','w').write('x')")


def test_duplicate_stage_name_without_force_fails(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_simple_stage(root, "dup", "dup.txt")
    before = (root / "dvc.yaml").read_bytes()
    result = run_dvc(root, "stage", "add", "-n", "dup", "-o", "dup2.txt", sys.executable, "-c", "open('dup2.txt','w').write('b')", check=False)
    assert result.returncode != 0
    assert (root / "dvc.yaml").read_bytes() == before
    stages = load_yaml(root / "dvc.yaml")["stages"]
    assert sorted(stages) == ["dup"]
    assert stages["dup"]["outs"] == ["dup.txt"]


def test_duplicate_stage_name_with_force_succeeds(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_simple_stage(root, "dup", "dup.txt")
    result = run_dvc(root, "stage", "add", "--force", "-n", "dup", "-o", "dup2.txt", sys.executable, "-c", "open('dup2.txt','w').write('b')")
    assert result.returncode == 0


def test_overlapping_stage_outputs_are_rejected(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_simple_stage(root, "out_a", "shared.txt")
    before = (root / "dvc.yaml").read_bytes()
    result = run_dvc(root, "stage", "add", "-n", "out_b", "-o", "shared.txt", sys.executable, "-c", "open('shared.txt','w').write('b')", check=False)
    assert result.returncode != 0
    assert (root / "dvc.yaml").read_bytes() == before
    stages = load_yaml(root / "dvc.yaml")["stages"]
    assert sorted(stages) == ["out_a"]
    assert stages["out_a"]["outs"] == ["shared.txt"]


def test_invalid_stage_name_preserves_existing_pipeline(tmp_path):
    root = init_repo(tmp_path / "repo")
    pipeline = root / "dvc.yaml"
    pipeline.write_text(
        yaml.safe_dump(
            {"stages": {"seed": {"cmd": "echo seed"}}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    before = pipeline.read_bytes()

    rejected = run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "bad:name",
        "-o",
        "bad.txt",
        sys.executable,
        "-c",
        "open('bad.txt', 'w').write('bad')",
        check=False,
    )

    assert rejected.returncode != 0
    assert pipeline.read_bytes() == before
    assert not (root / "bad.txt").exists()
    listing = run_dvc(root, "stage", "list", "--name-only")
    assert listing.stdout.split() == ["seed"]


def test_keep_going_runs_independent_stage_and_skips_dependent(tmp_path):
    root = init_repo(tmp_path / "repo")
    (root / "fail.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path('fail_started.txt').write_text('started', encoding='utf-8')\n"
        "sys.exit(5)\n",
        encoding="utf-8",
    )
    (root / "dependent.py").write_text(
        "from pathlib import Path\n"
        "Path('dependent.txt').write_text('dependent', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (root / "independent.py").write_text(
        "from pathlib import Path\n"
        "Path('independent.txt').write_text('independent', encoding='utf-8')\n",
        encoding="utf-8",
    )
    pipeline = {
        "stages": {
            "fail": {
                "cmd": f'"{sys.executable}" fail.py',
                "deps": ["fail.py"],
                "outs": ["failed.txt"],
            },
            "dependent": {
                "cmd": f'"{sys.executable}" dependent.py',
                "deps": ["failed.txt", "dependent.py"],
                "outs": ["dependent.txt"],
            },
            "independent": {
                "cmd": f'"{sys.executable}" independent.py',
                "deps": ["independent.py"],
                "outs": ["independent.txt"],
            },
        }
    }
    (root / "dvc.yaml").write_text(
        yaml.safe_dump(pipeline, sort_keys=False),
        encoding="utf-8",
    )
    result = run_dvc(
        root,
        "repro",
        "--keep-going",
        "--no-commit",
        "--no-run-cache",
        check=False,
    )
    assert result.returncode != 0
    assert (root / "fail_started.txt").read_text(encoding="utf-8") == "started"
    assert not (root / "failed.txt").exists()
    assert not (root / "dependent.txt").exists()
    assert (root / "independent.txt").read_text(encoding="utf-8") == "independent"


def test_targeted_repro_runs_upstream_dependency_for_target(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_two_stage_pipeline(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "train")
    assert (root / "model.txt").read_text(encoding="utf-8") == "A:model"


def test_downstream_repro_updates_descendant_stage_output(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_two_stage_pipeline(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "train")
    (root / "raw.txt").write_text("b", encoding="utf-8")
    run_dvc(root, "repro", "--downstream", "--no-commit", "--no-run-cache", "prepare")
    assert (root / "model.txt").read_text(encoding="utf-8") == "B:model"


def test_repo_reproduce_force_returns_reproduced_stages(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_two_stage_pipeline(root)
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        reproduced = Repo(str(root)).reproduce(targets=["train"], force=True, no_commit=True, run_cache=False)
    finally:
        os.chdir(old_cwd)
    assert reproduced


def test_repo_freeze_writes_same_frozen_state_as_cli(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        Repo(str(root)).freeze("prepare")
    finally:
        os.chdir(old_cwd)
    assert load_yaml(root / "dvc.yaml")["stages"]["prepare"]["frozen"] is True


def test_repo_unfreeze_removes_frozen_state(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_copy_stage(root)
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        repo = Repo(str(root))
        repo.freeze("prepare")
        repo.unfreeze("prepare")
    finally:
        os.chdir(old_cwd)
    assert load_yaml(root / "dvc.yaml")["stages"]["prepare"].get("frozen") is None


def test_repo_run_no_exec_writes_stage_but_does_not_create_output(tmp_path):
    root = init_repo(tmp_path / "repo")
    (root / "writer.py").write_text("from pathlib import Path\nPath('noexec.txt').write_text('x')\n", encoding="utf-8")
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        Repo(str(root)).run(name="noexec", cmd=f'"{sys.executable}" writer.py', outs=["noexec.txt"], no_exec=True)
    finally:
        os.chdir(old_cwd)
    assert "noexec" in load_yaml(root / "dvc.yaml")["stages"]
    assert not (root / "noexec.txt").exists()


def test_clean_status_json_reports_no_changes_after_committed_repro(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_cached_counting_stage(root)
    run_dvc(root, "repro")
    assert json.loads(run_dvc(root, "status", "--json").stdout) == {}


def test_status_quiet_success_when_pipeline_is_clean(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_cached_counting_stage(root)
    run_dvc(root, "repro")
    assert run_dvc(root, "status", "--quiet", check=False).returncode == 0


def test_run_cache_restores_deleted_output_without_rerunning_command(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_cached_counting_stage(root)
    run_dvc(root, "repro")
    first_counter = (root / "counter.txt").read_text(encoding="utf-8")
    first_data = (root / "data.txt").read_text(encoding="utf-8")
    (root / "data.txt").unlink()
    run_dvc(root, "repro")
    assert (root / "counter.txt").read_text(encoding="utf-8") == first_counter
    assert (root / "data.txt").read_text(encoding="utf-8") == first_data


def test_always_changed_stage_serializes_public_flag(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_always_changed_stage(root)
    assert load_yaml(root / "dvc.yaml")["stages"]["always"]["always_changed"] is True


def test_always_changed_stage_runs_even_without_input_changes(tmp_path):
    root = init_repo(tmp_path / "repo")
    add_always_changed_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "always_count.txt").read_text(encoding="utf-8") == "2"
    assert (root / "always.txt").read_text(encoding="utf-8") == "2"


def test_status_json_returns_mapping_for_changed_stage(tmp_path):
    root = init_repo(tmp_path / "repo")
    (root / "raw.txt").write_text("one", encoding="utf-8")
    run_dvc(root, "stage", "add", "-n", "copy", "-d", "raw.txt", "-o", "out.txt", sys.executable, "-c", "from pathlib import Path; Path('out.txt').write_text(Path('raw.txt').read_text(), encoding='utf-8')")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "raw.txt").write_text("two", encoding="utf-8")
    status = json.loads(run_dvc(root, "status", "--json").stdout)
    assert "copy" in status
