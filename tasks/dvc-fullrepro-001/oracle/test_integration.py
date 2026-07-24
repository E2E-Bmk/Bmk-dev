"""Integration tests for dvc-fullrepro-001.

Every test exercises ≥2 distinct public-API boundaries and targets a specific
composition seam (state consistency, protocol handoff, config interaction, …).
"""

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from conftest import (
    add_counting_stage,
    add_single_stage,
    add_two_stage_pipeline,
    init_repo,
    load_yaml,
    make_script,
    repo_reproduce,
    run_dvc,
    write_yaml,
)


# ===================================================================
# CVI-1  stage add → visible in yaml + list + selectable by repro
# ===================================================================

@pytest.mark.depends_on(
    "test_cli_stage_add_writes_stage_to_yaml",
    "test_cli_stage_list_reports_stages_from_existing_yaml",
)
def test_cvi1_stage_add_visible_in_yaml_and_stage_list(tmp_path):
    """CVI-1: stage add visible in yaml and stage list."""
    root = init_repo(tmp_path / "repo")
    (root / "source.txt").write_text("x", encoding="utf-8")
    run_dvc(
        root, "stage", "add", "-n", "ingest",
        "-d", "source.txt", "-o", "ingested.txt",
        sys.executable, "-c",
        "from pathlib import Path; "
        "Path('ingested.txt').write_text("
        "Path('source.txt').read_text(encoding='utf-8'), encoding='utf-8')",
    )
    assert "ingest" in load_yaml(root / "dvc.yaml")["stages"]
    listing = run_dvc(root, "stage", "list", "--name-only")
    assert "ingest" in listing.stdout.strip().splitlines()


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_cvi1_repo_run_stage_selectable_by_cli_repro(tmp_path):
    """CVI-1: repo run stage selectable by cli repro."""
    root = init_repo(tmp_path / "repo")
    (root / "source.txt").write_text("x", encoding="utf-8")
    make_script(
        root, "proc.py",
        "from pathlib import Path\n"
        "Path('product.txt').write_text("
        "Path('source.txt').read_text(encoding='utf-8').upper(), encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "process",
        "-d", "source.txt", "-d", "proc.py",
        "-o", "product.txt",
        sys.executable, "proc.py",
    )
    result = run_dvc(root, "repro", "--no-commit", "--no-run-cache", "process")
    assert result.returncode == 0
    assert (root / "product.txt").read_text(encoding="utf-8") == "X"


# ===================================================================
# CVI-2  output→dependency = pipeline edge, upstream first
# ===================================================================

@pytest.mark.depends_on(
    "test_run_no_exec_records_command_in_yaml",
    "test_run_no_exec_records_dependency_list",
)
def test_cvi2_upstream_runs_before_downstream(tmp_path):
    """CVI-2: upstream runs before downstream."""
    root = init_repo(tmp_path / "repo")
    add_two_stage_pipeline(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "intermediate.txt").read_text(encoding="utf-8") == "GAMMA"
    assert (root / "artifact.txt").read_text(encoding="utf-8") == "GAMMA:done"


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_cvi2_targeted_repro_includes_upstream_dependency(tmp_path):
    """CVI-2: targeted repro includes upstream dependency."""
    root = init_repo(tmp_path / "repo")
    add_two_stage_pipeline(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "assemble")
    assert (root / "intermediate.txt").exists()
    assert (root / "artifact.txt").read_text(encoding="utf-8") == "GAMMA:done"


# ===================================================================
# CVI-3  successful repro updates workspace + dvc.lock together
# ===================================================================

@pytest.mark.depends_on(
    "test_run_no_exec_records_command_in_yaml",
    "test_run_no_exec_records_output_list",
)
def test_cvi3_repro_creates_output_and_lockfile(tmp_path):
    """CVI-3: repro creates output and lockfile."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "artifact.txt").exists()
    lock = load_yaml(root / "dvc.lock")
    assert "transform" in lock["stages"]


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_cvi3_lock_records_command_matching_yaml(tmp_path):
    """CVI-3: lock records command matching yaml."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    yaml_cmd = load_yaml(root / "dvc.yaml")["stages"]["transform"]["cmd"]
    lock_cmd = load_yaml(root / "dvc.lock")["stages"]["transform"]["cmd"]
    assert lock_cmd == yaml_cmd


# ===================================================================
# CVI-4  clean state → status empty + repro skips
# ===================================================================

@pytest.mark.depends_on("test_status_returns_dict_on_initialized_repo")
def test_cvi4_status_json_empty_after_committed_repro(tmp_path):
    """CVI-4: status json empty after committed repro."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro")
    status = json.loads(run_dvc(root, "status", "--json").stdout)
    assert status == {}


@pytest.mark.depends_on("test_status_returns_dict_on_initialized_repo")
def test_cvi4_status_quiet_zero_when_clean(tmp_path):
    """CVI-4: status quiet zero when clean."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro")
    result = run_dvc(root, "status", "--quiet", check=False)
    assert result.returncode == 0


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_cvi4_repro_skips_unchanged_stage(tmp_path):
    """CVI-4: repro skips unchanged stage."""
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro")
    run_dvc(root, "repro")
    assert (root / "run_tally.txt").read_text(encoding="utf-8") == "1"


# ===================================================================
# CVI-5  dependency change → status reports + repro runs
# ===================================================================

@pytest.mark.depends_on(
    "test_status_returns_dict_on_initialized_repo",
    "test_run_no_exec_records_dependency_list",
)
def test_cvi5_dependency_change_appears_in_status_json(tmp_path):
    """CVI-5: dependency change appears in status json."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro")
    (root / "source.txt").write_text("epsilon\n", encoding="utf-8")
    status = json.loads(run_dvc(root, "status", "--json").stdout)
    assert "transform" in status


@pytest.mark.depends_on("test_run_no_exec_records_dependency_list")
def test_cvi5_dependency_change_triggers_repro(tmp_path):
    """CVI-5: dependency change triggers repro."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "source.txt").write_text("epsilon\n", encoding="utf-8")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "artifact.txt").read_text(encoding="utf-8") == "EPSILON\n"


# ===================================================================
# CVI-6  no-cache output missing → affects status/repro
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_output_list")
def test_cvi6_no_cache_output_serialized_and_affects_status(tmp_path):
    """CVI-6: no cache output serialized and affects status."""
    root = init_repo(tmp_path / "repo")
    run_dvc(
        root, "stage", "add", "-n", "nocache",
        "-O", "tracked.txt",
        sys.executable, "-c",
        "open('tracked.txt','w').write('tracked')",
    )
    outs = load_yaml(root / "dvc.yaml")["stages"]["nocache"]["outs"]
    assert outs == [{"tracked.txt": {"cache": False}}]

    run_dvc(root, "repro", "--no-run-cache", "nocache")
    (root / "tracked.txt").unlink()
    status = json.loads(run_dvc(root, "status", "--json").stdout)
    assert len(status) > 0


@pytest.mark.depends_on("test_run_no_exec_records_output_list")
def test_cvi6_missing_no_cache_output_triggers_repro(tmp_path):
    """CVI-6: missing no cache output triggers repro."""
    root = init_repo(tmp_path / "repo")
    run_dvc(
        root, "stage", "add", "-n", "nocache",
        "-O", "tracked.txt",
        sys.executable, "-c",
        "open('tracked.txt','w').write('tracked')",
    )
    run_dvc(root, "repro", "--no-run-cache", "nocache")
    (root / "tracked.txt").unlink()
    run_dvc(root, "repro", "--no-run-cache", "nocache")
    assert (root / "tracked.txt").read_text(encoding="utf-8") == "tracked"


# ===================================================================
# CVI-7  persistent vs non-persistent output handling
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_output_list")
def test_cvi7_nonpersistent_output_removed_before_rerun(tmp_path):
    """CVI-7: nonpersistent output removed before rerun."""
    root = init_repo(tmp_path / "repo")
    make_script(
        root, "writer.py",
        "from pathlib import Path\n"
        "Path('saw.txt').write_text(str(Path('result.txt').exists()), encoding='utf-8')\n"
        "Path('result.txt').write_text('fresh', encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "nonpersist",
        "-d", "writer.py",
        "-o", "result.txt", "-o", "saw.txt",
        sys.executable, "writer.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "nonpersist")
    run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "nonpersist")
    assert (root / "saw.txt").read_text(encoding="utf-8") == "False"


@pytest.mark.depends_on("test_run_no_exec_records_output_list")
def test_cvi7_persistent_output_remains_before_rerun(tmp_path):
    """CVI-7: persistent output remains before rerun."""
    root = init_repo(tmp_path / "repo")
    make_script(
        root, "appender.py",
        "from pathlib import Path\n"
        "p = Path('persist.txt')\n"
        "p.write_text("
        "(p.read_text(encoding='utf-8') if p.exists() else '') + 'x', encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "persist",
        "-d", "appender.py",
        "--outs-persist", "persist.txt",
        sys.executable, "appender.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "persist")
    run_dvc(root, "repro", "--force", "--no-commit", "--no-run-cache", "persist")
    assert (root / "persist.txt").read_text(encoding="utf-8") == "xx"


# ===================================================================
# CVI-8  frozen stage blocks dependency propagation
# ===================================================================

@pytest.mark.depends_on("test_freeze_writes_frozen_true_to_target_stage")
def test_cvi8_frozen_stage_blocks_repro_on_changed_dep(tmp_path):
    """CVI-8: frozen stage blocks repro on changed dep."""
    root = init_repo(tmp_path / "repo")
    (root / "params.yaml").write_text("gamma: violet\n", encoding="utf-8")
    make_script(
        root, "param_writer.py",
        "from pathlib import Path\nimport yaml\n"
        "data = yaml.safe_load(Path('params.yaml').read_text(encoding='utf-8'))\n"
        "Path('param_out.txt').write_text(data['gamma'], encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "paramstage",
        "-p", "gamma", "-o", "param_out.txt",
        sys.executable, "param_writer.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")

    (root / "params.yaml").write_text("gamma: indigo\n", encoding="utf-8")
    run_dvc(root, "freeze", "paramstage")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    assert (root / "param_out.txt").read_text(encoding="utf-8") == "violet"


@pytest.mark.depends_on("test_unfreeze_removes_frozen_flag_from_target")
def test_cvi8_unfreeze_then_repro_updates_output(tmp_path):
    """CVI-8: unfreeze then repro updates output."""
    root = init_repo(tmp_path / "repo")
    (root / "params.yaml").write_text("gamma: violet\n", encoding="utf-8")
    make_script(
        root, "param_writer.py",
        "from pathlib import Path\nimport yaml\n"
        "data = yaml.safe_load(Path('params.yaml').read_text(encoding='utf-8'))\n"
        "Path('param_out.txt').write_text(data['gamma'], encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "paramstage",
        "-p", "gamma", "-o", "param_out.txt",
        sys.executable, "param_writer.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")

    (root / "params.yaml").write_text("gamma: indigo\n", encoding="utf-8")
    run_dvc(root, "freeze", "paramstage")
    run_dvc(root, "unfreeze", "paramstage")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "paramstage")
    assert (root / "param_out.txt").read_text(encoding="utf-8") == "indigo"


# ===================================================================
# CVI-9  pull restores tracked data without modifying dvc.yaml
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_output_list")
def test_cvi9_pull_restores_data_from_local_remote(tmp_path):
    """CVI-9: pull restores data from local remote."""
    root = init_repo(tmp_path / "repo")
    remote_dir = tmp_path / "localremote"
    remote_dir.mkdir()
    run_dvc(root, "remote", "add", "localremote", str(remote_dir))

    (root / "input.txt").write_text("delta", encoding="utf-8")
    make_script(
        root, "copier.py",
        "from pathlib import Path\n"
        "Path('output.txt').write_text("
        "Path('input.txt').read_text(encoding='utf-8'), encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "copystage",
        "-d", "input.txt", "-d", "copier.py",
        "-o", "output.txt",
        sys.executable, "copier.py",
    )
    run_dvc(root, "repro")

    original = (root / "output.txt").read_text(encoding="utf-8")
    yaml_before = (root / "dvc.yaml").read_text(encoding="utf-8")

    run_dvc(root, "push", "-r", "localremote")

    (root / "output.txt").unlink()
    cache_dir = root / ".dvc" / "cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True)

    run_dvc(root, "pull", "-r", "localremote")

    assert (root / "output.txt").read_text(encoding="utf-8") == original
    assert (root / "dvc.yaml").read_text(encoding="utf-8") == yaml_before


# ===================================================================
# CVI-10  dry vs no-commit distinction
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_cvi10_dry_repro_does_not_execute_command(tmp_path):
    """CVI-10: dry repro does not execute command."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro", "--dry", "--no-run-cache", "transform")
    assert not (root / "artifact.txt").exists()
    assert not (root / "dvc.lock").exists()


@pytest.mark.depends_on("test_status_returns_dict_on_initialized_repo")
def test_cvi10_no_commit_executes_but_status_remains_dirty(tmp_path):
    """CVI-10: no commit executes but status remains dirty."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "artifact.txt").exists()
    status = json.loads(run_dvc(root, "status", "--json").stdout)
    assert len(status) > 0


# ===================================================================
# CVI-11  run-cache restore vs disable
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_cvi11_run_cache_restores_without_rerunning(tmp_path):
    """CVI-11: run cache restores without rerunning."""
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro")

    original_tally = (root / "run_tally.txt").read_text(encoding="utf-8")
    original_output = (root / "artifact.txt").read_text(encoding="utf-8")

    (root / "artifact.txt").unlink()
    run_dvc(root, "repro")

    assert (root / "run_tally.txt").read_text(encoding="utf-8") == original_tally
    assert (root / "artifact.txt").read_text(encoding="utf-8") == original_output


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_cvi11_no_run_cache_forces_reexecution(tmp_path):
    """CVI-11: no run cache forces reexecution."""
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "run_tally.txt").read_text(encoding="utf-8") == "2"


# ===================================================================
# CVI-12  JSON and text status describe the same state
# ===================================================================

@pytest.mark.depends_on("test_status_returns_dict_on_initialized_repo")
def test_cvi12_json_and_quiet_agree_on_clean_state(tmp_path):
    """CVI-12: json and quiet agree on clean state."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro")

    json_status = json.loads(run_dvc(root, "status", "--json").stdout)
    quiet_rc = run_dvc(root, "status", "--quiet", check=False).returncode

    assert json_status == {}
    assert quiet_rc == 0


@pytest.mark.depends_on("test_status_returns_dict_on_initialized_repo")
def test_cvi12_json_and_quiet_agree_on_changed_state(tmp_path):
    """CVI-12: json and quiet agree on changed state."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro")
    (root / "source.txt").write_text("changed\n", encoding="utf-8")

    json_status = json.loads(run_dvc(root, "status", "--json").stdout)
    quiet_rc = run_dvc(root, "status", "--quiet", check=False).returncode

    assert len(json_status) > 0
    assert quiet_rc != 0


# ===================================================================
# Additional seams — keep-going, downstream, force-downstream
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_keep_going_runs_independent_skips_dependent(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    make_script(
        root, "fail.py",
        "from pathlib import Path\nimport sys\n"
        "Path('fail_marker.txt').write_text('started', encoding='utf-8')\n"
        "sys.exit(5)\n",
    )
    make_script(
        root, "dep.py",
        "from pathlib import Path\n"
        "Path('dependent.txt').write_text('dependent', encoding='utf-8')\n",
    )
    make_script(
        root, "indep.py",
        "from pathlib import Path\n"
        "Path('independent.txt').write_text('independent', encoding='utf-8')\n",
    )
    pipeline = {
        "stages": {
            "fail": {
                "cmd": f'"{sys.executable}" fail.py',
                "deps": ["fail.py"],
                "outs": ["failed.txt"],
            },
            "dependent": {
                "cmd": f'"{sys.executable}" dep.py',
                "deps": ["failed.txt", "dep.py"],
                "outs": ["dependent.txt"],
            },
            "indep": {
                "cmd": f'"{sys.executable}" indep.py',
                "deps": ["indep.py"],
                "outs": ["independent.txt"],
            },
        },
    }
    write_yaml(root / "dvc.yaml", pipeline)
    result = run_dvc(
        root, "repro", "--keep-going",
        "--no-commit", "--no-run-cache",
        check=False,
    )
    assert result.returncode != 0
    assert (root / "fail_marker.txt").read_text(encoding="utf-8") == "started"
    assert not (root / "dependent.txt").exists()
    assert (root / "independent.txt").read_text(encoding="utf-8") == "independent"


@pytest.mark.depends_on(
    "test_run_no_exec_records_command_in_yaml",
    "test_run_no_exec_records_dependency_list",
)
def test_downstream_repro_updates_descendant_output(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    add_two_stage_pipeline(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")

    (root / "source.txt").write_text("theta", encoding="utf-8")
    run_dvc(
        root, "repro", "--downstream",
        "--no-commit", "--no-run-cache", "transform",
    )
    assert (root / "artifact.txt").read_text(encoding="utf-8") == "THETA:done"


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_force_downstream_reruns_descendant(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    make_script(
        root, "const_gen.py",
        "from pathlib import Path\n"
        "Path('mid.txt').write_text('constant', encoding='utf-8')\n",
    )
    make_script(
        root, "cnt.py",
        "from pathlib import Path\n"
        "c = Path('cnt.txt')\n"
        "n = int(c.read_text(encoding='utf-8')) if c.exists() else 0\n"
        "c.write_text(str(n + 1), encoding='utf-8')\n"
        "Path('final.txt').write_text(str(n + 1), encoding='utf-8')\n",
    )
    (root / "seed.txt").write_text("v1", encoding="utf-8")
    run_dvc(
        root, "stage", "add", "-n", "constgen",
        "-d", "seed.txt", "-d", "const_gen.py",
        "-o", "mid.txt",
        sys.executable, "const_gen.py",
    )
    run_dvc(
        root, "stage", "add", "-n", "counter",
        "-d", "mid.txt", "-d", "cnt.py",
        "-o", "final.txt",
        sys.executable, "cnt.py",
    )
    run_dvc(root, "repro")
    assert (root / "cnt.txt").read_text(encoding="utf-8") == "1"

    (root / "seed.txt").write_text("v2", encoding="utf-8")
    run_dvc(
        root, "repro", "--force-downstream",
        "--no-commit", "--no-run-cache",
    )
    assert int((root / "cnt.txt").read_text(encoding="utf-8")) > 1


# ===================================================================
# Additional seams — command list, wdir + env vars, params, always_changed
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_command_list")
def test_command_list_executes_in_declared_order(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    make_script(
        root, "first.py",
        "from pathlib import Path\n"
        "Path('first.txt').write_text('1', encoding='utf-8')\n",
    )
    make_script(
        root, "second.py",
        "from pathlib import Path\n"
        "Path('second.txt').write_text("
        "(Path('first.txt').read_text(encoding='utf-8') "
        "if Path('first.txt').exists() else '') + '2', encoding='utf-8')\n",
    )
    pipeline = {
        "stages": {
            "chain": {
                "cmd": [
                    f'"{sys.executable}" first.py',
                    f'"{sys.executable}" second.py',
                ],
                "deps": ["first.py", "second.py"],
                "outs": ["second.txt"],
            },
        },
    }
    write_yaml(root / "dvc.yaml", pipeline)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "chain")
    assert (root / "second.txt").read_text(encoding="utf-8") == "12"


@pytest.mark.depends_on("test_run_no_exec_records_command_list")
def test_command_list_failure_stops_subsequent_commands(tmp_path):
    """Seam: error propagation — inner failure surfaces correctly to the caller."""
    root = init_repo(tmp_path / "repo")
    cmds = [
        (
            f'"{sys.executable}" -c '
            '"from pathlib import Path; '
            "Path('started.txt').write_text('ok', encoding='utf-8')\""
        ),
        f'"{sys.executable}" -c "import sys; sys.exit(7)"',
        (
            f'"{sys.executable}" -c '
            '"from pathlib import Path; '
            "Path('later.txt').write_text('late', encoding='utf-8')\""
        ),
    ]
    write_yaml(root / "dvc.yaml", {"stages": {"chain": {"cmd": cmds}}})
    result = run_dvc(
        root, "repro", "--no-commit", "--no-run-cache", "chain",
        check=False,
    )
    assert result.returncode != 0
    assert (root / "started.txt").read_text(encoding="utf-8") == "ok"
    assert not (root / "later.txt").exists()


@pytest.mark.depends_on("test_run_no_exec_records_working_directory")
def test_wdir_stage_receives_dvc_root_and_dvc_stage_env(tmp_path):
    """Seam: config interaction — configuration sources combine with expected precedence."""
    root = init_repo(tmp_path / "repo")
    (root / "sub").mkdir()
    (root / "sub" / "input.txt").write_text("hi", encoding="utf-8")
    make_script(
        root / "sub", "env_check.py",
        "from pathlib import Path\nimport os\n"
        "Path('env.txt').write_text("
        "os.environ.get('DVC_ROOT', '') + '\\n' "
        "+ os.environ.get('DVC_STAGE', ''), encoding='utf-8')\n"
        "Path('output.txt').write_text("
        "Path('input.txt').read_text(encoding='utf-8') + '!', encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "envstage", "-w", "sub",
        "-d", "input.txt", "-o", "output.txt",
        sys.executable, "env_check.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "envstage")

    lines = (root / "sub" / "env.txt").read_text(encoding="utf-8").splitlines()
    assert Path(lines[0]) == root
    assert lines[1] == "envstage"
    assert (root / "sub" / "output.txt").read_text(encoding="utf-8") == "hi!"


@pytest.mark.depends_on(
    "test_run_no_exec_records_params_key",
    "test_status_returns_dict_on_initialized_repo",
)
def test_param_change_detected_by_status_and_repro(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    (root / "params.yaml").write_text("gamma: violet\n", encoding="utf-8")
    make_script(
        root, "param_reader.py",
        "from pathlib import Path\nimport yaml\n"
        "data = yaml.safe_load(Path('params.yaml').read_text(encoding='utf-8'))\n"
        "Path('param_result.txt').write_text(data['gamma'], encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "paramread",
        "-p", "gamma", "-o", "param_result.txt",
        sys.executable, "param_reader.py",
    )
    run_dvc(root, "repro")

    (root / "params.yaml").write_text("gamma: teal\n", encoding="utf-8")
    status = json.loads(run_dvc(root, "status", "--json").stdout)
    assert len(status) > 0

    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "param_result.txt").read_text(encoding="utf-8") == "teal"


@pytest.mark.depends_on("test_run_no_exec_records_always_changed_flag")
def test_always_changed_stage_reruns_without_input_change(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    make_script(
        root, "ticker.py",
        "from pathlib import Path\n"
        "c = Path('tick.txt')\n"
        "n = int(c.read_text(encoding='utf-8')) if c.exists() else 0\n"
        "c.write_text(str(n + 1), encoding='utf-8')\n"
        "Path('tick_out.txt').write_text(str(n + 1), encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "ticker", "--always-changed",
        "-d", "ticker.py", "-o", "tick_out.txt",
        sys.executable, "ticker.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "tick.txt").read_text(encoding="utf-8") == "2"


# ===================================================================
# Additional seams — API ↔ CLI consistency, no-commit cache behavior
# ===================================================================

@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_repo_reproduce_api_returns_reproduced_stages(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    add_two_stage_pipeline(root)
    result = repo_reproduce(
        root, force=True, no_commit=True, run_cache=False,
    )
    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.depends_on(
    "test_cli_version_exits_zero_with_output",
    "test_version_attribute_is_nonempty_string",
)
def test_cli_version_output_matches_api_version(tmp_path):
    """Seam: protocol handoff — CLI and programmatic API share the same behavior."""
    import dvc
    result = run_dvc(tmp_path, "--version", check=False)
    assert dvc.__version__ in result.stdout


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_no_commit_repeated_reruns_stage(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "run_tally.txt").read_text(encoding="utf-8") == "2"


@pytest.mark.depends_on("test_run_no_exec_records_command_in_yaml")
def test_no_commit_then_delete_output_reruns(tmp_path):
    """Seam: protocol handoff — command output matches artifact or API state."""
    root = init_repo(tmp_path / "repo")
    add_counting_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    (root / "artifact.txt").unlink()
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")
    assert (root / "run_tally.txt").read_text(encoding="utf-8") == "2"
    assert (root / "artifact.txt").read_text(encoding="utf-8") == "DELTA\n"


@pytest.mark.depends_on("test_run_no_exec_records_metric_output")
def test_metric_output_recorded_in_lockfile(tmp_path):
    """Seam: state consistency — integrated workflow preserves expected invariants."""
    root = init_repo(tmp_path / "repo")
    make_script(
        root, "metric_gen.py",
        "from pathlib import Path\nimport json\n"
        "Path('scores.json').write_text(json.dumps({'acc': 0.95}), encoding='utf-8')\n",
    )
    run_dvc(
        root, "stage", "add", "-n", "eval",
        "-d", "metric_gen.py", "-M", "scores.json",
        sys.executable, "metric_gen.py",
    )
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "eval")
    outs = load_yaml(root / "dvc.lock")["stages"]["eval"]["outs"]
    paths = [o["path"] for o in outs]
    assert "scores.json" in paths


@pytest.mark.depends_on(
    "test_freeze_writes_frozen_true_to_target_stage",
    "test_run_no_exec_records_command_in_yaml",
)
def test_freeze_api_blocks_cli_repro(tmp_path):
    """Seam: protocol handoff — CLI and programmatic API share the same behavior."""
    root = init_repo(tmp_path / "repo")
    add_single_stage(root)
    run_dvc(root, "repro", "--no-commit", "--no-run-cache")

    old = Path.cwd()
    os.chdir(root)
    try:
        from dvc.repo import Repo
        Repo(str(root)).freeze("transform")
    finally:
        os.chdir(old)

    assert load_yaml(root / "dvc.yaml")["stages"]["transform"]["frozen"] is True
    (root / "source.txt").write_text("changed\n", encoding="utf-8")
    run_dvc(root, "repro", "--no-commit", "--no-run-cache", "transform")
    assert (root / "artifact.txt").read_text(encoding="utf-8") == "GAMMA\n"
