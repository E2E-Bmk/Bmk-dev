"""Twenty-four independent Atomic roots for Cookiecutter v7."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from tests.support import api, assert_raises, file_tree, generate, isolated_environment, make_template, read_replay, run_cli, workspace, write_config
from tests.workflow_support import atomic_workflow


def test_a01_public_surface():
    import cookiecutter
    from cookiecutter import exceptions
    from cookiecutter.main import cookiecutter as entry

    names = ["ContextDecodingException", "OutputDirExistsException", "InvalidModeException", "FailedHookException", "UndefinedVariableInTemplate", "ConfigDoesNotExistException", "RepositoryNotFound", "LeaseConflictException", "LineageConflictException", "ManifestClosureException", "DeliveryConflictException", "CompensationConflictException", "ReceiptClosureException"]
    assert isinstance(cookiecutter.__version__, str) and cookiecutter.__version__
    assert callable(entry)
    assert all(issubclass(getattr(exceptions, name), exceptions.CookiecutterException) for name in names)


def test_a02_callable_and_cli_contract():
    expected = ["template", "checkout", "no_input", "extra_context", "replay", "overwrite_if_exists", "output_dir", "config_file", "default_config", "password", "directory", "skip_if_file_exists", "accept_hooks", "keep_project_on_failure"]
    assert list(inspect.signature(api()).parameters) == expected
    with workspace() as root:
        result = run_cli(root, root, "--help")
        text = result.stdout + result.stderr
        assert result.returncode == 0
        assert "--no-input" in text and "--output-dir" in text and "--replay-file" in text


def test_a03_ordered_typed_context():
    with workspace() as root:
        template = make_template(root / "template", {"name":"Velvet Lake","slug":"{{ cookiecutter.name.lower().replace(' ', '_') }}","choice":["amber","indigo"],"enabled":True,"meta":{"rank":7}}, {"{{cookiecutter.slug}}/value.txt":"{{cookiecutter.choice}}|{{cookiecutter.enabled is sameas true}}|{{cookiecutter.meta.rank}}"})
        result = generate(root, template, extra_context={"name":"Quiet Fjord"})
        assert result.name == "quiet_fjord"
        assert (result / "value.txt").read_text(encoding="utf-8") == "amber|True|7"


def test_a04_text_binary_copy_rendering():
    with workspace() as root:
        blob = b"\x00\xff\x10cookiecutter\x00"
        template = make_template(root / "template", {"slug":"lumen","_copy_without_render":["*.raw"]}, {"{{cookiecutter.slug}}/unicode.txt":"雪/{{cookiecutter.slug}}","{{cookiecutter.slug}}/asset.bin":blob,"{{cookiecutter.slug}}/literal.raw":b"{{ cookiecutter.slug }}\x00"})
        result = generate(root, template)
        assert (result / "unicode.txt").read_text(encoding="utf-8") == "雪/lumen"
        assert (result / "asset.bin").read_bytes() == blob
        assert (result / "literal.raw").read_bytes() == b"{{ cookiecutter.slug }}\x00"


def test_a05_hook_enablement_and_error():
    from cookiecutter import exceptions

    with workspace() as root:
        good = make_template(root / "good", {"slug":"hooked"}, {"{{cookiecutter.slug}}/body.txt":"ok"}, {"post_gen_project.py":"from pathlib import Path\nPath('hook.txt').write_text('ran', encoding='utf-8')\n"})
        assert (generate(root, good) / "hook.txt").read_text(encoding="utf-8") == "ran"
        disabled = generate(root, good, output_dir=root / "disabled", accept_hooks=False)
        assert not (disabled / "hook.txt").exists()
        bad = make_template(root / "bad", {"slug":"bad_hook"}, {"{{cookiecutter.slug}}/body.txt":"ok"}, {"post_gen_project.py":"raise SystemExit(9)\n"})
        with isolated_environment(root):
            assert_raises(exceptions.FailedHookException, api(), str(bad), no_input=True, output_dir=str(root / "bad-out"))


def test_a06_replay_serialization_overlay():
    with workspace() as root:
        template = make_template(root / "aurora", {"slug":"first","owner":"Nia"}, {"{{cookiecutter.slug}}/owner.txt":"{{cookiecutter.owner}}"})
        replay_dir = root / "replays"
        config = write_config(root / "config.yml", replay_dir)
        with isolated_environment(root):
            api()(str(template), no_input=True, extra_context={"slug":"saved","owner":"Oren"}, output_dir=str(root / "one"), config_file=str(config))
            replayed = Path(api()(str(template), replay=True, output_dir=str(root / "two"), config_file=str(config)))
        assert replayed.name == "saved"
        assert (replayed / "owner.txt").read_text(encoding="utf-8") == "Oren"
        assert read_replay(replay_dir / "aurora.json")["owner"] == "Oren"


def test_a07_overwrite_skip():
    with workspace() as root:
        template = make_template(root / "template", {"slug":"policy"}, {"{{cookiecutter.slug}}/keep.txt":"template","{{cookiecutter.slug}}/new.txt":"fresh"})
        target = generate(root, template)
        (target / "keep.txt").write_text("user", encoding="utf-8")
        (target / "new.txt").unlink()
        result = generate(root, template, overwrite_if_exists=True, skip_if_file_exists=True)
        assert (result / "keep.txt").read_text(encoding="utf-8") == "user"
        assert (result / "new.txt").read_text(encoding="utf-8") == "fresh"


def test_a08_nested_selection_inheritance():
    with workspace() as root:
        repo = make_template(root / "repo", {"templates":{"service":{"path":"catalog/service","title":"Service"}}}, {})
        make_template(repo / "catalog" / "service", {"slug":"nested","owner":"local"}, {"{{cookiecutter.slug}}/owner.txt":"{{cookiecutter.owner}}"})
        result = generate(root, repo, extra_context={"owner":"Rhea"})
        assert result.name == "nested" and (result / "owner.txt").read_text(encoding="utf-8") == "Rhea"


def test_a09_lexical_containment():
    with workspace() as root:
        repo = root / "repo"
        template = make_template(repo / "catalog" / "inside", {"slug":"bounded"}, {"{{cookiecutter.slug}}/file.txt":"ok"})
        result = generate(root, repo, directory="catalog/inside")
        assert result.resolve().is_relative_to((root / "output").resolve())
        assert template.resolve().is_relative_to(repo.resolve())


def test_a10_typed_errors():
    from cookiecutter import exceptions

    with workspace() as root:
        template = make_template(root / "template", {"slug":"typed"}, {"{{cookiecutter.slug}}/file.txt":"ok"})
        with isolated_environment(root):
            assert_raises(exceptions.ConfigDoesNotExistException, api(), str(template), no_input=True, config_file=str(root / "missing.yml"))
            assert_raises(exceptions.RepositoryNotFound, api(), str(root / "missing-template"), no_input=True)


def test_a11_cli_api_equivalence():
    with workspace() as root:
        template = make_template(root / "template", {"slug":"same","owner":"Taro"}, {"{{cookiecutter.slug}}/{{cookiecutter.owner}}.txt":"{{cookiecutter.owner}}"})
        direct = generate(root, template, output_dir=root / "api")
        cli = run_cli(root, template, "--no-input", "-o", str(root / "cli"))
        assert cli.returncode == 0, cli.stdout + cli.stderr
        assert file_tree(direct) == file_tree(root / "cli" / "same")


def test_a12_new_target_rollback():
    from cookiecutter import exceptions

    with workspace() as root:
        template = make_template(root / "template", {"slug":"rollback"}, {"{{cookiecutter.slug}}/body.txt":"created"}, {"post_gen_project.py":"raise SystemExit(4)\n"})
        with isolated_environment(root):
            assert_raises(exceptions.FailedHookException, api(), str(template), no_input=True, output_dir=str(root / "output"))
        assert not (root / "output" / "rollback").exists()


def test_a13_output_prepared_recovery():
    atomic_workflow("A13")


def test_a14_output_promoted_recovery():
    atomic_workflow("A14")


def test_a15_replay_revision_metadata():
    atomic_workflow("A15")


def test_a16_replay_failure_keeps_revision():
    atomic_workflow("A16")


def test_a17_hook_lease_binding():
    atomic_workflow("A17")


def test_a18_hook_ack_required():
    atomic_workflow("A18")


def test_a19_publication_capability_binding():
    atomic_workflow("A19")


def test_a20_publication_capability_required():
    atomic_workflow("A20")


def test_a21_artifact_catalog_seal_inspect():
    atomic_workflow("A21")


def test_a22_artifact_catalog_restore():
    atomic_workflow("A22")


def test_a23_channel_reserve_commit():
    atomic_workflow("A23")


def test_a24_channel_abort():
    atomic_workflow("A24")
