"""Thirty-six Integration and twelve System/E2E roots for Cookiecutter v7."""

from __future__ import annotations

from pathlib import Path

from tests.support import api, file_tree, generate, isolated_environment, make_template, read_replay, workspace, write_config
from tests.workflow_support import composition_workflow


def test_i01_context_cross_view():
    with workspace() as root:
        template = make_template(root / "template", {"slug":"default","owner":"Uma"}, {"{{cookiecutter.slug}}/{{cookiecutter.owner}}.txt":"{{cookiecutter.slug}}/{{cookiecutter.owner}}"})
        result = generate(root, template, extra_context={"slug":"cross","owner":"Veda"})
        assert result.name == "cross"
        assert (result / "Veda.txt").read_text(encoding="utf-8") == "cross/Veda"


def test_i02_copy_binary_rendered_paths():
    with workspace() as root:
        payload = b"\x00{{ cookiecutter.owner }}\xff"
        template = make_template(root / "template", {"slug":"copied","owner":"Wren","_copy_without_render":["raw/**"]}, {"{{cookiecutter.slug}}/raw/{{cookiecutter.owner}}.dat":payload,"{{cookiecutter.slug}}/text/{{cookiecutter.owner}}.txt":"{{cookiecutter.owner}}"})
        result = generate(root, template)
        assert (result / "raw" / "Wren.dat").read_bytes() == payload
        assert (result / "text" / "Wren.txt").read_text(encoding="utf-8") == "Wren"


def test_i03_hook_brackets_files():
    with workspace() as root:
        hooks = {
            "pre_gen_project.py":"from pathlib import Path\nassert not Path('body.txt').exists()\nPath('pre.txt').write_text('before', encoding='utf-8')\n",
            "post_gen_project.py":"from pathlib import Path\nassert Path('body.txt').read_text(encoding='utf-8') == 'rendered'\nPath('post.txt').write_text('after', encoding='utf-8')\n",
        }
        template = make_template(root / "template", {"slug":"bracket"}, {"{{cookiecutter.slug}}/body.txt":"rendered"}, hooks)
        result = generate(root, template)
        assert file_tree(result) == {"body.txt":b"rendered","post.txt":b"after","pre.txt":b"before"}


def test_i04_replay_current_views():
    with workspace() as root:
        template = make_template(root / "schema", {"slug":"old","owner":"Yara"}, {"{{cookiecutter.slug}}/{{cookiecutter.owner}}.txt":"{{cookiecutter.owner}}"})
        replay_dir = root / "replays"
        config = write_config(root / "config.yml", replay_dir)
        with isolated_environment(root):
            api()(str(template), no_input=True, extra_context={"slug":"remembered","owner":"Zeno"}, output_dir=str(root / "first"), config_file=str(config))
            data = {"slug":"new-default","owner":"Current Owner"}
            (template / "cookiecutter.json").write_text(__import__("json").dumps(data), encoding="utf-8")
            result = Path(api()(str(template), replay=True, output_dir=str(root / "second"), config_file=str(config)))
        assert result.name == "remembered"
        assert (result / "Zeno.txt").read_text(encoding="utf-8") == "Zeno"
        assert read_replay(replay_dir / "schema.json")["owner"] == "Zeno"


def test_i05_overwrite_skip_user_bytes():
    with workspace() as root:
        template = make_template(root / "template", {"slug":"preserve"}, {"{{cookiecutter.slug}}/keep.bin":b"template\x00","{{cookiecutter.slug}}/add.txt":"added"})
        target = generate(root, template)
        (target / "keep.bin").write_bytes(b"user\x00\xff")
        (target / "add.txt").unlink()
        unrelated = root / "output" / "sibling.txt"
        unrelated.write_bytes(b"sibling")
        generate(root, template, overwrite_if_exists=True, skip_if_file_exists=True)
        assert (target / "keep.bin").read_bytes() == b"user\x00\xff"
        assert (target / "add.txt").read_bytes() == b"added" and unrelated.read_bytes() == b"sibling"


def test_i06_nested_output_root_replay():
    with workspace() as root:
        repo = root / "repo"
        template = make_template(repo / "nested", {"slug":"selected","owner":"Aiko"}, {"{{cookiecutter.slug}}/owner.txt":"{{cookiecutter.owner}}"}, {"post_gen_project.py":"from pathlib import Path\nPath('hook.txt').write_text('{{cookiecutter.owner}}', encoding='utf-8')\n"})
        replay_dir = root / "replays"
        config = write_config(root / "config.yml", replay_dir)
        with isolated_environment(root):
            result = Path(api()(str(repo), directory="nested", no_input=True, extra_context={"owner":"Bela"}, output_dir=str(root / "output"), config_file=str(config)))
        replay_files = list(replay_dir.glob("*.json"))
        assert len(replay_files) == 1
        saved = read_replay(replay_files[0])
        assert template.is_dir() and (result / "owner.txt").read_text(encoding="utf-8") == "Bela"
        assert (result / "hook.txt").read_text(encoding="utf-8") == "Bela" and saved["owner"] == "Bela"


def test_i07_output_pair_recovery():
    composition_workflow("I07")


def test_i08_output_post_promotion_cleanup():
    composition_workflow("I08")


def test_i09_output_recovery_idempotent():
    composition_workflow("I09")


def test_i10_output_recovery_preserves_sibling():
    composition_workflow("I10")


def test_i11_replay_revision_chain():
    composition_workflow("I11")


def test_i12_replay_abandoned_reservation():
    composition_workflow("I12")


def test_i13_replay_retry_current_schema():
    composition_workflow("I13")


def test_i14_replay_target_consistency():
    composition_workflow("I14")


def test_i15_child_failure_root_rollback():
    composition_workflow("I15")


def test_i16_inner_not_early_published():
    composition_workflow("I16")


def test_i17_nested_retry_fresh_schema():
    composition_workflow("I17")


def test_i18_nested_hook_root_lease():
    composition_workflow("I18")


def test_i19_hook_ack_mismatch():
    composition_workflow("I19")


def test_i20_hook_descendant_failure_cleanup():
    composition_workflow("I20")


def test_i21_hook_crash_adoption():
    composition_workflow("I21")


def test_i22_hook_live_lease_isolation():
    composition_workflow("I22")


def test_i23_stale_capability_rejected():
    composition_workflow("I23")


def test_i24_wrong_resource_capability_rejected():
    composition_workflow("I24")


def test_i25_alias_swap_capability_rejected():
    composition_workflow("I25")


def test_i26_capability_failure_restores_pair():
    composition_workflow("I26")


def test_i27_target_replay_resource_set():
    composition_workflow("I27")


def test_i28_sibling_resource_independence():
    composition_workflow("I28")


def test_i29_artifact_deduplication():
    composition_workflow("I29")


def test_i30_restore_conflict_preserves_destination():
    composition_workflow("I30")


def test_i31_context_partitions_artifact_identity():
    composition_workflow("I31")


def test_i32_concurrent_seal_converges():
    composition_workflow("I32")


def test_i33_channel_compare_and_swap():
    composition_workflow("I33")


def test_i34_reservation_binding_single_use():
    composition_workflow("I34")


def test_i35_stale_reservation_recovery():
    composition_workflow("I35")


def test_i36_channel_history_rollback():
    composition_workflow("I36")


def test_s01_output_replay_recovery():
    composition_workflow("S01")


def test_s02_replay_schema_recovery_chain():
    composition_workflow("S02")


def test_s03_three_level_nested_rollback():
    composition_workflow("S03")


def test_s04_hook_adoption_retry():
    composition_workflow("S04")


def test_s05_capability_replay_rollback():
    composition_workflow("S05")


def test_s06_api_cli_resource_contention():
    composition_workflow("S06")


def test_s07_nested_hook_authorized_publication():
    composition_workflow("S07")


def test_s08_restart_two_owner_transfers():
    composition_workflow("S08")


def test_s09_managed_generation_consistency():
    composition_workflow("S09")


def test_s10_failed_generation_does_not_activate():
    composition_workflow("S10")


def test_s11_channel_conflict_rolls_back_generation():
    composition_workflow("S11")


def test_s12_committed_activation_recovery():
    composition_workflow("S12")
