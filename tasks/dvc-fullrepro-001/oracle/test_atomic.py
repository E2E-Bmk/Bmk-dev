# Spec2Repo oracle - atomic tests for dvc-fullrepro-001
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from dvc.repo import Repo


DVC_CLI_MAIN = "import sys; from dvc.cli import main; raise SystemExit(main(sys.argv[1:]))"


def run_dvc(cwd, *args, check=True):
    env = os.environ.copy()
    env["DVC_TEST"] = "true"
    env["DVC_NO_ANALYTICS"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", DVC_CLI_MAIN, *args],
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


@pytest.fixture(scope="module")
def basic_repro(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("basic_repro"))
    (root / "raw.txt").write_text("alpha\n", encoding="utf-8")
    (root / "copy_upper.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "Path(sys.argv[2]).write_text(Path(sys.argv[1]).read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
        encoding="utf-8",
    )

    add = run_dvc(
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
    yaml_after_add = load_yaml(root / "dvc.yaml")
    lock_exists_after_add = (root / "dvc.lock").exists()
    listed_names = run_dvc(root, "stage", "list", "--name-only").stdout.split()

    first_repro = run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    output_after_first_repro = (root / "prepared.txt").read_text(encoding="utf-8")
    lock_after_first_repro = load_yaml(root / "dvc.lock")
    status_after_no_commit = json.loads(run_dvc(root, "status", "--json").stdout)
    quiet_after_no_commit = run_dvc(root, "status", "--quiet", check=False).returncode

    (root / "raw.txt").write_text("beta\n", encoding="utf-8")
    dirty_status_after_dep_change = json.loads(run_dvc(root, "status", "--json").stdout)
    dry = run_dvc(root, "repro", "--dry", "--no-run-cache", "prepare")
    output_after_dry = (root / "prepared.txt").read_text(encoding="utf-8")
    forced = run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "prepare")
    output_after_force = (root / "prepared.txt").read_text(encoding="utf-8")
    invalid_target = run_dvc(
        root, "repro", "--no-commit", "--no-run-cache", "missing-stage", check=False
    )

    return {
        "add": add,
        "yaml_after_add": yaml_after_add,
        "lock_exists_after_add": lock_exists_after_add,
        "listed_names": listed_names,
        "first_repro": first_repro,
        "output_after_first_repro": output_after_first_repro,
        "lock_after_first_repro": lock_after_first_repro,
        "status_after_no_commit": status_after_no_commit,
        "quiet_after_no_commit": quiet_after_no_commit,
        "dirty_status_after_dep_change": dirty_status_after_dep_change,
        "dry": dry,
        "output_after_dry": output_after_dry,
        "forced": forced,
        "output_after_force": output_after_force,
        "invalid_target": invalid_target,
    }


@pytest.fixture(scope="module")
def no_commit_runs(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("no_commit_runs"))
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

    counts = []
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    counts.append((root / "run_count.txt").read_text(encoding="utf-8"))
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    counts.append((root / "run_count.txt").read_text(encoding="utf-8"))
    (root / "raw.txt").write_text("two\n", encoding="utf-8")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    counts.append((root / "run_count.txt").read_text(encoding="utf-8"))
    (root / "prepared.txt").unlink()
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    counts.append((root / "run_count.txt").read_text(encoding="utf-8"))
    return {
        "counts": counts,
        "output": (root / "prepared.txt").read_text(encoding="utf-8"),
    }


@pytest.fixture(scope="module")
def output_modes(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("output_modes"))
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
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "nonpersist",
        "-d",
        "writer.py",
        "-o",
        "result.txt",
        "-o",
        "saw_existing.txt",
        sys.executable,
        "writer.py",
        "nonpersist",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "nonpersist")
    run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "nonpersist")
    nonpersistent_saw_existing = (root / "saw_existing.txt").read_text(encoding="utf-8")

    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "persist",
        "-d",
        "writer.py",
        "--outs-persist",
        "persist.txt",
        sys.executable,
        "writer.py",
        "persist",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "persist")
    run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "persist")
    persistent_text = (root / "persist.txt").read_text(encoding="utf-8")

    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "nocache",
        "-d",
        "writer.py",
        "-O",
        "nocache.txt",
        sys.executable,
        "writer.py",
        "nocache",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "nocache")
    yaml_after_nocache = load_yaml(root / "dvc.yaml")
    (root / "nocache.txt").unlink()
    nocache_status = json.loads(run_dvc(root, "status", "--json").stdout)

    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "metric",
        "-d",
        "writer.py",
        "-M",
        "metrics.json",
        sys.executable,
        "writer.py",
        "metric",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "metric")
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "plot",
        "-d",
        "writer.py",
        "--plots",
        "plot.csv",
        sys.executable,
        "writer.py",
        "plot",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "plot")
    lock_after_metric_plot = load_yaml(root / "dvc.lock")

    return {
        "nonpersistent_saw_existing": nonpersistent_saw_existing,
        "persistent_text": persistent_text,
        "yaml_after_nocache": yaml_after_nocache,
        "nocache_status": nocache_status,
        "lock_after_metric_plot": lock_after_metric_plot,
    }


@pytest.fixture(scope="module")
def wdir_and_commands(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("wdir_and_commands"))
    (root / "sub").mkdir()
    (root / "sub" / "input.txt").write_text("hi", encoding="utf-8")
    (root / "sub" / "env_stage.py").write_text(
        "from pathlib import Path\n"
        "import os\n"
        "Path('env.txt').write_text(os.environ.get('DVC_ROOT', '') + '\\n' + os.environ.get('DVC_STAGE', ''), encoding='utf-8')\n"
        "Path('output.txt').write_text(Path('input.txt').read_text(encoding='utf-8') + '!', encoding='utf-8')\n",
        encoding="utf-8",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "envstage",
        "-w",
        "sub",
        "-d",
        "input.txt",
        "-o",
        "output.txt",
        sys.executable,
        "env_stage.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "envstage")
    env_lines = (root / "sub" / "env.txt").read_text(encoding="utf-8").splitlines()

    (root / "first.py").write_text(
        "from pathlib import Path\nPath('first.txt').write_text('1', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (root / "second.py").write_text(
        "from pathlib import Path\nPath('second.txt').write_text(Path('first.txt').read_text(encoding='utf-8') + '2', encoding='utf-8')\n",
        encoding="utf-8",
    )
    dvc_yaml = {
        "stages": {
            "chain": {
                "cmd": [f'"{sys.executable}" first.py', f'"{sys.executable}" second.py'],
                "deps": ["first.py", "second.py"],
                "outs": ["second.txt"],
            }
        }
    }
    (root / "dvc.yaml").write_text(yaml.safe_dump(dvc_yaml, sort_keys=False), encoding="utf-8")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "chain")

    (root / "fail.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    (root / "after_fail.py").write_text(
        "from pathlib import Path\nPath('after_fail.txt').write_text('ran', encoding='utf-8')\n",
        encoding="utf-8",
    )
    dvc_yaml["stages"]["fails"] = {
        "cmd": [f'"{sys.executable}" fail.py', f'"{sys.executable}" after_fail.py'],
        "deps": ["fail.py", "after_fail.py"],
        "outs": ["after_fail.txt"],
    }
    (root / "dvc.yaml").write_text(yaml.safe_dump(dvc_yaml, sort_keys=False), encoding="utf-8")
    failing = run_dvc(root, "repro", "--no-commit", "--no-run-cache", "fails", check=False)

    return {
        "root": root,
        "wdir_output": (root / "sub" / "output.txt").read_text(encoding="utf-8"),
        "dvc_root": Path(env_lines[0]),
        "dvc_stage": env_lines[1],
        "command_list_output": (root / "second.txt").read_text(encoding="utf-8"),
        "failing": failing,
        "after_failed_command_exists": (root / "after_fail.txt").exists(),
    }


@pytest.fixture(scope="module")
def params_freeze_errors(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("params_freeze_errors"))
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
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    first_output = (root / "param_out.txt").read_text(encoding="utf-8")
    (root / "params.yaml").write_text("alpha: blue\n", encoding="utf-8")
    dirty_after_param_change = json.loads(run_dvc(root, "status", "--json").stdout)
    run_dvc(root, "freeze", "paramstage")
    yaml_after_freeze = load_yaml(root / "dvc.yaml")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    frozen_output = (root / "param_out.txt").read_text(encoding="utf-8")
    run_dvc(root, "unfreeze", "paramstage")
    yaml_after_unfreeze = load_yaml(root / "dvc.yaml")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    unfrozen_output = (root / "param_out.txt").read_text(encoding="utf-8")

    bad_status_option = run_dvc(root, "status", "--all-branches", check=False)
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "dup",
        "-o",
        "dup.txt",
        sys.executable,
        "-c",
        "open('dup.txt','w').write('a')",
    )
    duplicate_stage = run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "dup",
        "-o",
        "dup2.txt",
        sys.executable,
        "-c",
        "open('dup2.txt','w').write('b')",
        check=False,
    )
    forced_duplicate_stage = run_dvc(
        root,
        "stage",
        "add",
        "--force",
        "-n",
        "dup",
        "-o",
        "dup2.txt",
        sys.executable,
        "-c",
        "open('dup2.txt','w').write('b')",
    )
    run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "out_a",
        "-o",
        "shared.txt",
        sys.executable,
        "-c",
        "open('shared.txt','w').write('a')",
    )
    overlapping_output = run_dvc(
        root,
        "stage",
        "add",
        "-n",
        "out_b",
        "-o",
        "shared.txt",
        sys.executable,
        "-c",
        "open('shared.txt','w').write('b')",
        check=False,
    )
    return {
        "first_output": first_output,
        "dirty_after_param_change": dirty_after_param_change,
        "yaml_after_freeze": yaml_after_freeze,
        "frozen_output": frozen_output,
        "yaml_after_unfreeze": yaml_after_unfreeze,
        "unfrozen_output": unfrozen_output,
        "bad_status_option": bad_status_option,
        "duplicate_stage": duplicate_stage,
        "forced_duplicate_stage": forced_duplicate_stage,
        "overlapping_output": overlapping_output,
    }


@pytest.fixture(scope="module")
def pipeline_and_repo_api(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("pipeline_and_repo_api"))
    (root / "raw.txt").write_text("a", encoding="utf-8")
    (root / "prepare.py").write_text(
        "from pathlib import Path\n"
        "Path('prepared.txt').write_text(Path('raw.txt').read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
        encoding="utf-8",
    )
    (root / "train.py").write_text(
        "from pathlib import Path\n"
        "p = Path('train_count.txt')\n"
        "n = int(p.read_text() or '0') if p.exists() else 0\n"
        "p.write_text(str(n + 1), encoding='utf-8')\n"
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
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "train")
    model_after_target = (root / "model.txt").read_text(encoding="utf-8")
    (root / "raw.txt").write_text("b", encoding="utf-8")
    run_dvc(root, "repro", "--downstream", "--no-commit", "--no-run-cache", "prepare")
    model_after_downstream = (root / "model.txt").read_text(encoding="utf-8")

    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        repo = Repo(str(root))
        reproduced = repo.reproduce(targets=["train"], force=True, no_commit=True, run_cache=False)
        repo.freeze("prepare")
        yaml_after_repo_freeze = load_yaml(root / "dvc.yaml")
        repo.unfreeze("prepare")
        yaml_after_repo_unfreeze = load_yaml(root / "dvc.yaml")
        repo.run(name="noexec", cmd=f'"{sys.executable}" prepare.py', outs=["noexec.txt"], no_exec=True)
        yaml_after_noexec = load_yaml(root / "dvc.yaml")
    finally:
        os.chdir(old_cwd)

    return {
        "root": root,
        "model_after_target": model_after_target,
        "model_after_downstream": model_after_downstream,
        "repo_reproduce_count": len(reproduced),
        "yaml_after_repo_freeze": yaml_after_repo_freeze,
        "yaml_after_repo_unfreeze": yaml_after_repo_unfreeze,
        "yaml_after_noexec": yaml_after_noexec,
        "noexec_output_exists": (root / "noexec.txt").exists(),
    }


def test_repro_invalid_target_fails_nonzero(basic_repro):
    assert basic_repro["invalid_target"].returncode != 0


def test_outs_no_cache_is_serialized_with_cache_false(output_modes):
    outs = output_modes["yaml_after_nocache"]["stages"]["nocache"]["outs"]
    assert outs == [{"nocache.txt": {"cache": False}}]


def test_metric_output_is_recorded_in_lockfile_outputs(output_modes):
    outs = output_modes["lock_after_metric_plot"]["stages"]["metric"]["outs"]
    assert [out["path"] for out in outs] == ["metrics.json"]


def test_plot_output_is_recorded_in_lockfile_outputs(output_modes):
    outs = output_modes["lock_after_metric_plot"]["stages"]["plot"]["outs"]
    assert [out["path"] for out in outs] == ["plot.csv"]


def test_stage_command_receives_dvc_root_environment(wdir_and_commands):
    assert wdir_and_commands["dvc_root"] == wdir_and_commands["root"]


def test_stage_command_receives_dvc_stage_environment(wdir_and_commands):
    assert wdir_and_commands["dvc_stage"] == "envstage"


def test_failing_command_list_stage_returns_nonzero(wdir_and_commands):
    assert wdir_and_commands["failing"].returncode != 0


def test_freeze_writes_frozen_to_stage_definition(params_freeze_errors):
    stage = params_freeze_errors["yaml_after_freeze"]["stages"]["paramstage"]
    assert stage["frozen"] is True


def test_local_status_rejects_revision_expansion_option(params_freeze_errors):
    assert params_freeze_errors["bad_status_option"].returncode != 0


def test_duplicate_stage_name_without_force_fails(params_freeze_errors):
    assert params_freeze_errors["duplicate_stage"].returncode != 0


def test_duplicate_stage_name_with_force_succeeds(params_freeze_errors):
    assert params_freeze_errors["forced_duplicate_stage"].returncode == 0


def test_overlapping_stage_outputs_are_rejected(params_freeze_errors):
    assert params_freeze_errors["overlapping_output"].returncode != 0


@pytest.fixture(scope="module")
def run_cache_and_pull(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("run_cache_and_pull"))
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
    run_dvc(root, "repro")
    first_counter = (root / "counter.txt").read_text(encoding="utf-8")
    first_data = (root / "data.txt").read_text(encoding="utf-8")
    clean_status = run_dvc(root, "status").stdout
    clean_quiet = run_dvc(root, "status", "--quiet", check=False).returncode

    (root / "data.txt").unlink()
    run_dvc(root, "repro")
    restored_counter = (root / "counter.txt").read_text(encoding="utf-8")
    restored_data = (root / "data.txt").read_text(encoding="utf-8")

    remote = root.parent / "local-remote"
    run_dvc(root, "remote", "add", "-d", "localstore", str(remote))
    run_dvc(root, "push")
    (root / "data.txt").unlink()
    run_dvc(root, "pull", "produce")
    pulled_data = (root / "data.txt").read_text(encoding="utf-8")

    return {
        "first_counter": first_counter,
        "first_data": first_data,
        "clean_status": clean_status,
        "clean_quiet": clean_quiet,
        "restored_counter": restored_counter,
        "restored_data": restored_data,
        "pulled_data": pulled_data,
    }


@pytest.fixture(scope="module")
def always_changed_stage(tmp_path_factory):
    root = init_repo(tmp_path_factory.mktemp("always_changed_stage"))
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
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    return {
        "yaml": load_yaml(root / "dvc.yaml"),
        "count": (root / "always_count.txt").read_text(encoding="utf-8"),
        "output": (root / "always.txt").read_text(encoding="utf-8"),
    }


def test_status_quiet_success_when_pipeline_is_clean(run_cache_and_pull):
    assert run_cache_and_pull["clean_quiet"] == 0


def test_always_changed_stage_serializes_public_flag(always_changed_stage):
    stage = always_changed_stage["yaml"]["stages"]["always"]
    assert stage["always_changed"] is True
