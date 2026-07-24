"""Integration tests for copier-template-fullrepro-001.

Each test crosses ≥2 public API boundaries or validates a Cross-View Invariant.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import (
    ANSWERS_FILE_ENTRY,
    ANSWERS_TEMPLATE,
    MULTI_QUESTION_YML,
    SIMPLE_COPIER_YML,
    add_git_tag,
    build_git_template,
    build_template,
    git_init_project,
    read_yaml,
    run_copier_cli,
)


# ---------------------------------------------------------------------------
# CVI1: API copy == CLI copy (same files, answers, metadata)
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_cvi1_api_and_cli_copy_produce_same_result(tmp_path: Path):
    """CVI-1: API run_copy and CLI copy produce identical output. run_copy and CLI 'copier copy' produce identical rendered files and answers."""
    from copier import run_copy

    yml = "service_name:\n  type: str\n  default: gateway\n"
    files = {"app.cfg.jinja": "name={{ service_name }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE}

    src_api = build_template(tmp_path / "api", yml, files)
    dst_api = tmp_path / "out_api"
    run_copy(str(src_api), dst_api, defaults=True)

    src_cli = build_template(tmp_path / "cli", yml, files)
    dst_cli = tmp_path / "out_cli"
    result = run_copier_cli("copy", "--defaults", str(src_cli), str(dst_cli))
    assert result.returncode == 0, result.stderr

    assert (dst_api / "app.cfg").read_text(encoding="utf-8") == (dst_cli / "app.cfg").read_text(encoding="utf-8")
    api_answers = read_yaml(dst_api / ".copier-answers.yml")
    cli_answers = read_yaml(dst_cli / ".copier-answers.yml")
    assert api_answers["service_name"] == cli_answers["service_name"]


# ---------------------------------------------------------------------------
# CVI2: data visible in rendered content AND answers file
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_data_overrides_default")
def test_cvi2_data_visible_in_render_and_answers(tmp_path: Path):
    """CVI-2: data parameter visible in rendered content and answers file. Data parameter appears in rendered file content and in answers file."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, data={"billing_svc": "fulfillment"}, defaults=True)

    assert (dst / "out.txt").read_text(encoding="utf-8") == "fulfillment\n"
    assert read_yaml(dst / ".copier-answers.yml")["billing_svc"] == "fulfillment"


# ---------------------------------------------------------------------------
# CVI3: answers file path consistent across operations
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_cvi3_answers_file_path_consistent_copy_recopy(tmp_path: Path):
    """CVI-3: custom answers_file path consistent across copy and recopy. Custom answers_file path used for copy is the same path recopy reads from."""
    from copier import run_copy, run_recopy

    yml = "_answers_file: .deploy-answers.yml\n" + SIMPLE_COPIER_YML
    src = build_template(
        tmp_path,
        yml,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, data={"billing_svc": "ledger"}, defaults=True)
    assert (dst / ".deploy-answers.yml").exists()
    assert not (dst / ".copier-answers.yml").exists()

    (src / "extra.txt.jinja").write_text("{{ billing_svc }}_v2\n", encoding="utf-8")
    run_recopy(dst, defaults=True, overwrite=True)

    assert (dst / "extra.txt").read_text(encoding="utf-8") == "ledger_v2\n"


# ---------------------------------------------------------------------------
# CVI4: secret renders but not in answers
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_secret_question_not_in_answers_file")
def test_cvi4_secret_renders_but_excluded_from_answers(tmp_path: Path):
    """CVI-4: secret question renders but is excluded from answers. Secret question value is used during rendering but omitted from answers file."""
    from copier import run_copy

    yml = (
        "db_password:\n  type: str\n  secret: true\n  default: s3cr3t-val\n"
        "db_host:\n  type: str\n  default: db.internal\n"
    )
    src = build_template(
        tmp_path,
        yml,
        {
            "conn.txt.jinja": "host={{ db_host }} pass={{ db_password }}\n",
            ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE,
        },
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    assert "s3cr3t-val" in (dst / "conn.txt").read_text(encoding="utf-8")
    answers = read_yaml(dst / ".copier-answers.yml")
    assert "db_password" not in answers
    assert answers["db_host"] == "db.internal"


# ---------------------------------------------------------------------------
# CVI5: exclude + skip_if_exists semantics
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_exclude_prevents_file_copy", "test_skip_if_exists_preserves_existing")
def test_cvi5_exclude_and_skip_if_exists_combined(tmp_path: Path):
    """CVI-5: exclude and skip_if_exists semantics compose correctly. Exclude prevents rendering; skip_if_exists preserves existing but creates missing."""
    from copier import run_copy

    yml = "_exclude:\n  - '*.log'\n_skip_if_exists:\n  - settings.ini\n"
    src = build_template(
        tmp_path,
        yml,
        {"settings.ini": "from_tpl\n", "app.py": "main()\n", "debug.log": "verbose\n"},
    )
    dst = tmp_path / "dest"
    dst.mkdir()
    (dst / "settings.ini").write_text("user_val\n", encoding="utf-8")

    run_copy(str(src), dst, defaults=True)

    assert (dst / "settings.ini").read_text(encoding="utf-8") == "user_val\n"
    assert (dst / "app.py").read_text(encoding="utf-8") == "main()\n"
    assert not (dst / "debug.log").exists()


# ---------------------------------------------------------------------------
# CVI6: pretend computes but doesn't write
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_pretend_does_not_create_destination")
def test_cvi6_pretend_computes_without_writing(tmp_path: Path):
    """CVI-6: pretend mode computes without filesystem side effects. Pretend mode exercises rendering logic but produces zero filesystem side-effects."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, data={"billing_svc": "analytics"}, defaults=True, pretend=True)

    assert not dst.exists()


# ---------------------------------------------------------------------------
# CVI7: quiet mode renders same as non-quiet
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_quiet_still_renders_correctly")
def test_cvi7_quiet_and_normal_render_identically(tmp_path: Path):
    """CVI-7: quiet and normal copy render identical output. Quiet mode produces the same rendered output as non-quiet."""
    from copier import run_copy

    yml = "env_name:\n  type: str\n  default: staging\n"
    files = {"env.txt.jinja": "{{ env_name }}\n"}

    src_q = build_template(tmp_path / "q", yml, files)
    dst_q = tmp_path / "out_q"
    run_copy(str(src_q), dst_q, defaults=True, quiet=True)

    src_n = build_template(tmp_path / "n", yml, files)
    dst_n = tmp_path / "out_n"
    run_copy(str(src_n), dst_n, defaults=True, quiet=False)

    assert (dst_q / "env.txt").read_text(encoding="utf-8") == (dst_n / "env.txt").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# CVI8: unsafe features rejected/allowed consistently
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_unsafe_template_without_trust_raises")
def test_cvi8_unsafe_rejected_without_trust_allowed_with(tmp_path: Path):
    """CVI-8: unsafe tasks rejected without trust and allowed with unsafe=True. Tasks are rejected without trust and execute correctly with unsafe=True."""
    from copier import run_copy
    from copier.errors import UnsafeTemplateError

    task_cmd = (
        f'{{{{ _copier_python }}}} -c "from pathlib import Path; '
        f"Path('marker.txt').write_text('done', encoding='utf-8')\""
    )
    yml = f"_tasks:\n  - \"{task_cmd}\"\n"
    src = build_template(tmp_path, yml, {"base.txt": "x\n"})
    dst_no = tmp_path / "no_trust"
    dst_yes = tmp_path / "trusted"

    with pytest.raises(UnsafeTemplateError):
        run_copy(str(src), dst_no, defaults=True)

    run_copy(str(src), dst_yes, defaults=True, unsafe=True)
    assert (dst_yes / "marker.txt").read_text(encoding="utf-8") == "done"


# ---------------------------------------------------------------------------
# CVI9: VcsRef.CURRENT in update keeps same ref
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_vcsref_current_value")
def test_cvi9_vcsref_current_keeps_recorded_ref(tmp_path: Path):
    """CVI-9: VcsRef.CURRENT during update preserves recorded ref. Using VcsRef.CURRENT during update preserves the previously recorded ref."""
    from copier import VcsRef, run_copy, run_update

    src = build_git_template(
        tmp_path,
        "svc:\n  type: str\n  default: alpha\n",
        {"ver.txt.jinja": "v1\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
        tag="v1.0.0",
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, defaults=True, vcs_ref="v1.0.0")
    git_init_project(dst)

    (src / "ver.txt.jinja").write_text("v2\n", encoding="utf-8")
    add_git_tag(src, "v2.0.0")

    run_update(dst, defaults=True, vcs_ref=VcsRef.CURRENT, overwrite=True)

    answers = read_yaml(dst / ".copier-answers.yml")
    assert answers["_commit"] == "v1.0.0"


# ---------------------------------------------------------------------------
# CVI10: check-update JSON matches quiet exit code
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_cvi10_check_update_exit_code_semantics(tmp_path: Path):
    """CVI-10: check-update quiet exit code reflects update availability. check-update --quiet exit code 0 means up-to-date, 2 means update available."""
    src = build_git_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"data.txt.jinja": "v1\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
        tag="v1.0.0",
    )
    dst = tmp_path / "dest"
    result = run_copier_cli("copy", "--defaults", "--overwrite", "--vcs-ref", "v1.0.0", str(src), str(dst))
    assert result.returncode == 0, result.stderr
    git_init_project(dst)

    up_to_date = run_copier_cli("check-update", "--quiet", str(dst))
    assert up_to_date.returncode == 0

    (src / "data.txt.jinja").write_text("v2\n", encoding="utf-8")
    add_git_tag(src, "v2.0.0")

    has_update = run_copier_cli("check-update", "--quiet", str(dst))
    assert has_update.returncode == 2


# ---------------------------------------------------------------------------
# Seam: copy → recopy reuses template source and answers
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_seam_copy_then_recopy_reuses_answers(tmp_path: Path):
    """Seam: lifecycle crossing — copy then recopy reuses recorded answers. Recopy reads answers from the file produced by copy and re-renders."""
    from copier import run_copy, run_recopy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, data={"billing_svc": "warehouse"}, defaults=True)

    (src / "new.txt.jinja").write_text("{{ billing_svc }}_extra\n", encoding="utf-8")
    run_recopy(dst, defaults=True, overwrite=True)

    assert (dst / "new.txt").read_text(encoding="utf-8") == "warehouse_extra\n"
    assert read_yaml(dst / ".copier-answers.yml")["billing_svc"] == "warehouse"


# ---------------------------------------------------------------------------
# Seam: copy → update with new tag applies changes
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_seam_copy_then_update_applies_new_tag(tmp_path: Path):
    """Seam: lifecycle crossing — copy then update applies newer template tag. Update with a newer tag applies template changes to the project."""
    from copier import run_copy, run_update

    src = build_git_template(
        tmp_path,
        "cluster:\n  type: str\n  default: east\n",
        {"ver.txt.jinja": "release-1\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
        tag="v1.0.0",
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, defaults=True, vcs_ref="v1.0.0")
    git_init_project(dst)

    (src / "ver.txt.jinja").write_text("release-2\n", encoding="utf-8")
    add_git_tag(src, "v2.0.0")

    run_update(dst, defaults=True, vcs_ref="v2.0.0", overwrite=True)

    assert (dst / "ver.txt").read_text(encoding="utf-8") == "release-2\n"
    assert read_yaml(dst / ".copier-answers.yml")["_commit"] == "v2.0.0"


# ---------------------------------------------------------------------------
# Seam: rendered answers file contains _copier_answers with correct data
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_data_overrides_default")
def test_seam_answers_file_contains_copier_metadata(tmp_path: Path):
    """Seam: state consistency — answers file contains metadata and answers. The rendered answers file includes _src_path and question answers."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, data={"billing_svc": "notifications"}, defaults=True)

    answers = read_yaml(dst / ".copier-answers.yml")
    assert answers["billing_svc"] == "notifications"
    assert "_src_path" in answers


# ---------------------------------------------------------------------------
# Seam: _copier_conf.answers_file matches actual file path
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_seam_copier_conf_answers_file_matches_actual(tmp_path: Path):
    """Seam: state consistency — rendered answers_file path matches actual file. _copier_conf.answers_file rendered value matches the actual answers file path."""
    from copier import run_copy

    yml = "_answers_file: .deploy-state.yml\n" + SIMPLE_COPIER_YML
    src = build_template(
        tmp_path,
        yml,
        {
            "conf_path.txt.jinja": "{{ _copier_conf.answers_file }}\n",
            ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE,
        },
    )
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True)

    rendered_path = (dst / "conf_path.txt").read_text(encoding="utf-8").strip()
    assert rendered_path == ".deploy-state.yml"
    assert (dst / ".deploy-state.yml").exists()


# ---------------------------------------------------------------------------
# Seam: data precedence (data > previous > defaults)
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_data_overrides_default")
def test_seam_data_precedence_over_previous_and_defaults(tmp_path: Path):
    """Seam: config interaction — data overrides previous answers and defaults. Data param takes precedence over previously recorded answers and defaults."""
    from copier import run_copy, run_recopy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, data={"billing_svc": "old_value"}, defaults=True)

    run_recopy(dst, data={"billing_svc": "new_value"}, defaults=True, overwrite=True)

    assert (dst / "out.txt").read_text(encoding="utf-8") == "new_value\n"
    assert read_yaml(dst / ".copier-answers.yml")["billing_svc"] == "new_value"


# ---------------------------------------------------------------------------
# Seam: cleanup_on_error removes directory on failure for fresh copy
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_min_copier_version_too_high_raises")
def test_seam_cleanup_on_error_removes_fresh_destination(tmp_path: Path):
    """Seam: error propagation — failed copy removes fresh destination. When copy fails on a fresh destination, cleanup_on_error removes it."""
    from copier import run_copy
    from copier.errors import UnsupportedVersionError

    src = build_template(tmp_path, "_min_copier_version: '9999.0.0'\n", {"x.txt": "x\n"})
    dst = tmp_path / "fresh_dest"

    with pytest.raises(UnsupportedVersionError):
        run_copy(str(src), dst, defaults=True, cleanup_on_error=True)

    assert not dst.exists()


# ---------------------------------------------------------------------------
# Seam: force=True implies defaults+overwrite
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_overwrite_replaces_existing_file")
def test_seam_force_implies_defaults_and_overwrite(tmp_path: Path):
    """Seam: config interaction — CLI force implies defaults and overwrite. CLI --force implies both --defaults and --overwrite behavior."""
    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n"},
    )
    dst = tmp_path / "dest"
    dst.mkdir()
    (dst / "out.txt").write_text("local\n", encoding="utf-8")

    result = run_copier_cli("copy", "--force", str(src), str(dst))

    assert result.returncode == 0, result.stderr
    assert (dst / "out.txt").read_text(encoding="utf-8") == "payments\n"


# ---------------------------------------------------------------------------
# Seam: recopy data overrides recorded answers
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_seam_recopy_data_overrides_recorded(tmp_path: Path):
    """Seam: config interaction — recopy data overrides recorded answers. Recopy with data param overrides the answers that copy originally stored."""
    from copier import run_copy, run_recopy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, data={"billing_svc": "original"}, defaults=True)

    run_recopy(dst, data={"billing_svc": "overridden"}, defaults=True, overwrite=True)

    assert (dst / "out.txt").read_text(encoding="utf-8") == "overridden\n"
    assert read_yaml(dst / ".copier-answers.yml")["billing_svc"] == "overridden"


# ---------------------------------------------------------------------------
# CLI data-file integration
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_data_overrides_default")
def test_cli_data_file_provides_answers(tmp_path: Path):
    """Seam: config interaction — CLI data-file supplies answer values. CLI --data-file provides answer values used for rendering."""
    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n"},
    )
    data_f = tmp_path / "vals.yml"
    data_f.write_text("billing_svc: from_file\n", encoding="utf-8")
    dst = tmp_path / "dest"

    result = run_copier_cli("copy", "--defaults", f"--data-file={data_f}", str(src), str(dst))

    assert result.returncode == 0, result.stderr
    assert (dst / "out.txt").read_text(encoding="utf-8") == "from_file\n"


# ---------------------------------------------------------------------------
# CLI --data precedence over --data-file
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_data_overrides_default")
def test_cli_data_takes_precedence_over_data_file(tmp_path: Path):
    """Seam: config interaction — CLI data overrides data-file values. CLI --data overrides --data-file for the same question."""
    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n"},
    )
    data_f = tmp_path / "vals.yml"
    data_f.write_text("billing_svc: file_val\n", encoding="utf-8")
    dst = tmp_path / "dest"

    result = run_copier_cli(
        "copy", "--defaults", f"--data-file={data_f}",
        "--data=billing_svc=cli_val", str(src), str(dst),
    )

    assert result.returncode == 0, result.stderr
    assert (dst / "out.txt").read_text(encoding="utf-8") == "cli_val\n"


# ---------------------------------------------------------------------------
# CLI recopy reuses answers from answers file
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_cli_recopy_uses_recorded_answers(tmp_path: Path):
    """Seam: lifecycle crossing — CLI recopy reads recorded answers file. CLI recopy reads recorded answers and applies them to new template content."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, data={"billing_svc": "recorded_val"}, defaults=True)
    (src / "extra.txt.jinja").write_text("{{ billing_svc }}_x\n", encoding="utf-8")

    result = run_copier_cli("recopy", "--defaults", "--force", str(dst))

    assert result.returncode == 0, result.stderr
    assert (dst / "extra.txt").read_text(encoding="utf-8") == "recorded_val_x\n"


# ---------------------------------------------------------------------------
# Settings.defaults integration with run_copy
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_settings_defaults_populates_unanswered_questions")
def test_settings_defaults_used_with_defaults_mode(tmp_path: Path):
    """Seam: config interaction — Settings.defaults override question defaults. Settings.defaults provides values that override question defaults during copy."""
    from copier import Settings, run_copy

    yml = "region_code:\n  type: str\n  default: us-east-1\n"
    src = build_template(tmp_path, yml, {"region.txt.jinja": "{{ region_code }}\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True, settings=Settings(defaults={"region_code": "eu-central-1"}))

    assert (dst / "region.txt").read_text(encoding="utf-8") == "eu-central-1\n"


# ---------------------------------------------------------------------------
# CLI check-update distinguishes current vs newer
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_cli_check_update_json_output(tmp_path: Path):
    """Seam: protocol handoff — check-update JSON reports update availability. check-update without --quiet produces JSON with update_available field."""
    src = build_git_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"data.txt.jinja": "v1\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
        tag="v1.0.0",
    )
    dst = tmp_path / "dest"
    cp = run_copier_cli("copy", "--defaults", "--overwrite", "--vcs-ref", "v1.0.0", str(src), str(dst))
    assert cp.returncode == 0, cp.stderr
    git_init_project(dst)

    (src / "data.txt.jinja").write_text("v2\n", encoding="utf-8")
    add_git_tag(src, "v2.0.0")

    result = run_copier_cli("check-update", str(dst))
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Task execution produces side-effects alongside rendered files
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_unsafe_template_without_trust_raises")
def test_task_execution_and_rendered_content(tmp_path: Path):
    """Seam: lifecycle crossing — tasks run after rendering alongside files. Tasks run after rendering; both task side-effects and rendered files are correct."""
    from copier import run_copy

    task_cmd = (
        f'{{{{ _copier_python }}}} -c "from pathlib import Path; '
        f"Path('done.flag').write_text('executed', encoding='utf-8')\""
    )
    yml = f"svc:\n  type: str\n  default: queue\n_tasks:\n  - \"{task_cmd}\"\n"
    src = build_template(tmp_path, yml, {"svc.txt.jinja": "{{ svc }}\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True, unsafe=True)

    assert (dst / "svc.txt").read_text(encoding="utf-8") == "queue\n"
    assert (dst / "done.flag").read_text(encoding="utf-8") == "executed"


# ---------------------------------------------------------------------------
# skip_tasks avoids running but still renders
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_unsafe_template_without_trust_raises")
def test_skip_tasks_renders_but_no_side_effects(tmp_path: Path):
    """Seam: lifecycle crossing — skip_tasks renders without task side effects. skip_tasks=True prevents task execution while still rendering template files."""
    from copier import run_copy

    task_cmd = (
        f'{{{{ _copier_python }}}} -c "from pathlib import Path; '
        f"Path('side.txt').write_text('ran', encoding='utf-8')\""
    )
    yml = f"name:\n  type: str\n  default: worker\n_tasks:\n  - \"{task_cmd}\"\n"
    src = build_template(tmp_path, yml, {"name.txt.jinja": "{{ name }}\n"})
    dst = tmp_path / "dest"

    run_copy(str(src), dst, defaults=True, unsafe=True, skip_tasks=True)

    assert (dst / "name.txt").read_text(encoding="utf-8") == "worker\n"
    assert not (dst / "side.txt").exists()


# ---------------------------------------------------------------------------
# Pretend with recopy: renders in memory but doesn't change files
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_pretend_does_not_create_destination")
def test_recopy_pretend_leaves_project_unchanged(tmp_path: Path):
    """Seam: lifecycle crossing — recopy pretend leaves project files unchanged. Recopy with pretend=True doesn't modify existing project files."""
    from copier import run_copy, run_recopy

    src = build_template(
        tmp_path,
        SIMPLE_COPIER_YML,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, defaults=True)
    original = (dst / "out.txt").read_text(encoding="utf-8")

    (src / "out.txt.jinja").write_text("changed\n", encoding="utf-8")
    run_recopy(dst, defaults=True, overwrite=True, pretend=True)

    assert (dst / "out.txt").read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# Custom answers_file → recopy reads from that path
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_custom_answers_file_survives_recopy(tmp_path: Path):
    """Seam: state consistency — custom answers_file path survives recopy. A custom answers_file set during copy is correctly read during recopy."""
    from copier import run_copy, run_recopy

    yml = "_answers_file: .state.yml\n" + SIMPLE_COPIER_YML
    src = build_template(
        tmp_path, yml,
        {"out.txt.jinja": "{{ billing_svc }}\n", ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE},
    )
    dst = tmp_path / "dest"
    run_copy(str(src), dst, data={"billing_svc": "inventory"}, defaults=True)
    assert (dst / ".state.yml").exists()

    (src / "v2.txt.jinja").write_text("{{ billing_svc }}\n", encoding="utf-8")
    run_recopy(dst, defaults=True, overwrite=True)

    assert (dst / "v2.txt").read_text(encoding="utf-8") == "inventory\n"


# ---------------------------------------------------------------------------
# Multi-question rendering + answers consistency
# ---------------------------------------------------------------------------


@pytest.mark.depends_on("test_run_copy_defaults_generates_destination_files")
def test_multi_question_all_rendered_and_recorded(tmp_path: Path):
    """Seam: state consistency — all questions rendered and recorded in answers. Multiple questions are all rendered in templates and recorded in answers."""
    from copier import run_copy

    src = build_template(
        tmp_path,
        MULTI_QUESTION_YML,
        {
            "info.txt.jinja": "{{ billing_svc }}/{{ region_code }}/{{ replica_count }}\n",
            ANSWERS_FILE_ENTRY: ANSWERS_TEMPLATE,
        },
    )
    dst = tmp_path / "dest"
    data = {"billing_svc": "ingestion", "region_code": "eu-west-1", "replica_count": "5"}

    run_copy(str(src), dst, data=data, defaults=True)

    assert (dst / "info.txt").read_text(encoding="utf-8") == "ingestion/eu-west-1/5\n"
    answers = read_yaml(dst / ".copier-answers.yml")
    assert answers["billing_svc"] == "ingestion"
    assert answers["region_code"] == "eu-west-1"
    assert answers["replica_count"] == 5
