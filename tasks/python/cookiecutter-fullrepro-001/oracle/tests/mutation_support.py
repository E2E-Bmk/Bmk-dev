from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

from tests.support import GATE, api, assert_raises, candidate_root, file_tree, generate, isolated_environment, make_template, process_alive, process_env, read_replay, taskkill, workspace, write_config


def _wait(path: Path, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            raise AssertionError(f"barrier was not reached: {path}")
        threading.Event().wait(0.02)


def _call_script(template: Path, output: Path, config: Path, extra: dict, overwrite: bool = True, patch_replace: Path | None = None) -> str:
    setup = ""
    if patch_replace is not None:
        setup = f"""
real_replace = os.replace
def crash_after_replace(source, destination):
    result = real_replace(source, destination)
    if Path(destination).resolve() == Path({str(patch_replace)!r}).resolve():
        os._exit(91)
    return result
os.replace = crash_after_replace
"""
    return f"""
import os, sys
from pathlib import Path
sys.path.insert(0, {str(GATE)!r})
sys.path.insert(1, {str(candidate_root())!r})
sys.path.insert(2, {str((GATE / '../../.venv-reference/Lib/site-packages').resolve())!r})
if os.environ.get('COOKIECUTTER_SYNTHETIC_PROFILE'):
    from reference_patch import apply
    apply()
{setup}
from cookiecutter.main import cookiecutter
cookiecutter({str(template)!r}, no_input=True, extra_context={extra!r}, overwrite_if_exists={overwrite!r}, output_dir={str(output)!r}, config_file={str(config)!r})
"""


def _launch(root: Path, script: str, additions: dict[str, str] | None = None) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=root,
        env=process_env(root, additions),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _finish(process: subprocess.Popen[str], timeout: float = 12.0) -> tuple[int, str]:
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        taskkill(process.pid)
        stdout, stderr = process.communicate(timeout=5)
        raise AssertionError("candidate process did not complete at a deterministic barrier")
    return process.returncode, stdout + stderr


def _basic(root: Path, name: str = "template", slug: str = "durable", hook: str | None = None) -> tuple[Path, Path, Path]:
    hooks = {"pre_gen_project.py":hook} if hook is not None else None
    template = make_template(root / name, {"slug":slug,"value":"old"}, {"{{cookiecutter.slug}}/value.txt":"{{cookiecutter.value}}"}, hooks)
    replay = root / "replays"
    config = write_config(root / "config.yml", replay)
    return template, config, replay / f"{name}.json"


def _seed(root: Path, template: Path, config: Path, output: Path, value: str = "old", accept_hooks: bool = False) -> Path:
    with isolated_environment(root):
        return Path(api()(str(template), no_input=True, extra_context={"value":value}, output_dir=str(output), config_file=str(config), overwrite_if_exists=True, accept_hooks=accept_hooks))


def _journal_prepare() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        ready, release = root / "ready", root / "release"
        hook = f"from pathlib import Path\nimport os,signal,time\nPath({str(ready)!r}).write_text('ready')\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\nos.kill(os.getppid(), signal.SIGTERM)\n"
        template, config, replay_file = _basic(root, hook=hook)
        output = root / "output"
        target = _seed(root, template, config, output)
        old_replay = replay_file.read_bytes()
        process = _launch(root, _call_script(template, output, config, {"value":"interrupted"}))
        _wait(ready)
        release.write_text("crash", encoding="utf-8")
        _finish(process)
        bad_hook = "raise SystemExit(13)\n"
        (template / "hooks" / "pre_gen_project.py").write_text(bad_hook, encoding="utf-8")
        with isolated_environment(root):
            assert_raises(exceptions.FailedHookException, api(), str(template), no_input=True, extra_context={"value":"failed-retry"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
        assert (target / "value.txt").read_text(encoding="utf-8") == "old"
        assert replay_file.read_bytes() == old_replay


def _journal_published(repeat: bool = False) -> None:
    with workspace() as root:
        template, config, replay_file = _basic(root)
        output = root / "output"
        _seed(root, template, config, output)
        process = _launch(root, _call_script(template, output, config, {"value":"published"}, patch_replace=replay_file))
        code, text = _finish(process)
        assert code == 91, text
        with isolated_environment(root):
            result = Path(api()(str(template), no_input=True, extra_context={"value":"published"}, overwrite_if_exists=True, skip_if_file_exists=True, output_dir=str(output), config_file=str(config)))
            if repeat:
                result = Path(api()(str(template), no_input=True, extra_context={"value":"published"}, overwrite_if_exists=True, skip_if_file_exists=True, output_dir=str(output), config_file=str(config)))
        assert (result / "value.txt").read_text(encoding="utf-8") == "published"
        assert read_replay(replay_file)["value"] == "published"
        assert not list(output.glob(".cookiecutter-transaction-*"))


def _journal_scope() -> None:
    with workspace() as root:
        template, config, _ = _basic(root)
        output = root / "output"
        sibling = output / "unrelated"
        sibling.mkdir(parents=True)
        (sibling / "user.bin").write_bytes(b"untouched\x00\xfe")
        _seed(root, template, config, output)
        ready = root / "ready"
        (template / "hooks").mkdir(exist_ok=True)
        release = root / "release"
        (template / "hooks" / "pre_gen_project.py").write_text(f"from pathlib import Path\nimport os,signal,time\nPath({str(ready)!r}).write_text('x')\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\nos.kill(os.getppid(), signal.SIGTERM)\n", encoding="utf-8")
        process = _launch(root, _call_script(template, output, config, {"value":"crash"}))
        _wait(ready)
        release.write_text("crash", encoding="utf-8")
        _finish(process)
        (template / "hooks" / "pre_gen_project.py").unlink()
        (template / "hooks" / "post_gen_project.py").write_text("from pathlib import Path\nimport os\nPath('owner-id.txt').write_text(os.environ['COOKIECUTTER_TRANSACTION_ID'])\n", encoding="utf-8")
        result = _seed(root, template, config, output, "retry", accept_hooks=True)
        assert (result / "owner-id.txt").read_text(encoding="utf-8")
        assert (sibling / "user.bin").read_bytes() == b"untouched\x00\xfe"


def _owner_conflict() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        ready, release = root / "ready", root / "release"
        hook = f"from pathlib import Path\nimport time\nPath({str(ready)!r}).write_text('x')\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\n"
        template, config, replay_file = _basic(root, hook=hook)
        output = root / "output"
        errors: list[BaseException] = []
        def first() -> None:
            try:
                api()(str(template), no_input=True, extra_context={"value":"first"}, output_dir=str(output), config_file=str(config))
            except BaseException as exc:
                errors.append(exc)
        thread = threading.Thread(target=first)
        thread.start()
        _wait(ready)
        busy = getattr(exceptions, "BusyProjectException", None)
        observed = None
        if busy is not None:
            observed = assert_raises(busy, api(), str(template), no_input=True, extra_context={"value":"second"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
        release.write_text("go", encoding="utf-8")
        thread.join(timeout=8)
        assert busy is not None and observed is not None
        assert not thread.is_alive() and not errors
        assert (output / "durable" / "value.txt").read_text(encoding="utf-8") == "first"
        assert read_replay(replay_file)["value"] == "first"


def _stale_owner() -> None:
    with workspace() as root:
        ready = root / "ready"
        release = root / "release"
        hook = f"from pathlib import Path\nimport os,signal,time\nPath({str(ready)!r}).write_text('x')\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\nos.kill(os.getppid(), signal.SIGTERM)\n"
        template, config, replay_file = _basic(root, hook=hook)
        output = root / "output"
        _seed(root, template, config, output)
        process = _launch(root, _call_script(template, output, config, {"value":"stale"}))
        _wait(ready)
        release.write_text("crash", encoding="utf-8")
        _finish(process)
        (template / "hooks" / "pre_gen_project.py").unlink()
        (template / "hooks" / "post_gen_project.py").write_text("from pathlib import Path\nimport os\nPath('owner-id.txt').write_text(os.environ['COOKIECUTTER_TRANSACTION_ID'])\n", encoding="utf-8")
        result = _seed(root, template, config, output, "reclaimed", accept_hooks=True)
        assert (result / "value.txt").read_text(encoding="utf-8") == "reclaimed"
        assert (result / "owner-id.txt").read_text(encoding="utf-8")
        assert read_replay(replay_file)["value"] == "reclaimed"
        assert not list(output.glob(".cookiecutter-owner-*"))


def _sibling_independence() -> None:
    with workspace() as root:
        ready, release = root / "ready", root / "release"
        hook_one = f"from pathlib import Path\nimport os,time\nPath({str(ready)!r}).write_text('x')\nassert os.environ['COOKIECUTTER_TRANSACTION_ID'] == os.environ['COOKIECUTTER_ROOT_TRANSACTION_ID']\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\n"
        one, config, _ = _basic(root, name="one", slug="one-project", hook=hook_one)
        hook_two = "from pathlib import Path\nimport os\nPath('id.txt').write_text(os.environ['COOKIECUTTER_TRANSACTION_ID'])\n"
        two = make_template(root / "two", {"slug":"two-project"}, {"{{cookiecutter.slug}}/value.txt":"two"}, {"post_gen_project.py":hook_two})
        output = root / "output"
        first = _launch(root, _call_script(one, output, config, {"value":"one"}, overwrite=False))
        _wait(ready)
        with isolated_environment(root):
            second = Path(api()(str(two), no_input=True, output_dir=str(output), config_file=str(config)))
        assert (second / "id.txt").read_text(encoding="utf-8")
        release.write_text("go", encoding="utf-8")
        code, text = _finish(first)
        assert code == 0, text


def _owner_release() -> None:
    with workspace() as root:
        template, config, _ = _basic(root)
        output = root / "output"
        (template / "hooks").mkdir()
        (template / "hooks" / "post_gen_project.py").write_text("import os\nassert os.environ['COOKIECUTTER_TRANSACTION_ID']\nraise SystemExit(8)\n", encoding="utf-8")
        with isolated_environment(root):
            try:
                api()(str(template), no_input=True, output_dir=str(output), config_file=str(config))
            except Exception:
                pass
        (template / "hooks" / "post_gen_project.py").write_text("from pathlib import Path\nimport os\nPath('id.txt').write_text(os.environ['COOKIECUTTER_TRANSACTION_ID'])\n", encoding="utf-8")
        result = _seed(root, template, config, output, "retry", accept_hooks=True)
        assert (result / "id.txt").read_text(encoding="utf-8")


def _nested_repo(root: Path, failing: bool = False, probe: Path | None = None) -> Path:
    repo = make_template(root / "nested-root", {"templates":{"middle":{"path":"middle"}}}, {})
    make_template(repo / "middle", {"templates":{"leaf":{"path":"leaf"}}}, {})
    hook = ""
    if probe is not None:
        hook += f"from pathlib import Path\nassert not Path({str(probe)!r}).exists()\n"
    hook += "from pathlib import Path\nimport os\nPath('tx.txt').write_text(os.environ['COOKIECUTTER_ROOT_TRANSACTION_ID'])\n"
    if failing:
        hook += "raise SystemExit(7)\n"
    make_template(repo / "middle" / "leaf", {"slug":"nested-product","owner":"Ciro"}, {"{{cookiecutter.slug}}/owner.txt":"{{cookiecutter.owner}}"}, {"post_gen_project.py":hook})
    return repo


def _nested_rollback() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        repo = _nested_repo(root, failing=False)
        config = write_config(root / "config.yml", root / "replays")
        output = root / "output"
        with isolated_environment(root):
            prior = Path(api()(str(repo), no_input=True, extra_context={"owner":"Prior"}, output_dir=str(output), config_file=str(config)))
        old_tree = file_tree(prior)
        old_replay = (root / "replays" / "nested-root.json").read_bytes()
        leaf_hook = repo / "middle" / "leaf" / "hooks" / "post_gen_project.py"
        leaf_hook.write_text(leaf_hook.read_text(encoding="utf-8") + "raise SystemExit(7)\n", encoding="utf-8")
        with isolated_environment(root):
            assert_raises(exceptions.FailedHookException, api(), str(repo), no_input=True, extra_context={"owner":"Failed"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
        assert file_tree(prior) == old_tree
        assert (root / "replays" / "nested-root.json").read_bytes() == old_replay


def _nested_staging() -> None:
    with workspace() as root:
        final = root / "output" / "nested-product"
        repo = _nested_repo(root, probe=final)
        config = write_config(root / "config.yml", root / "replays")
        with isolated_environment(root):
            result = Path(api()(str(repo), no_input=True, output_dir=str(root / "output"), config_file=str(config)))
        assert result == final.resolve() and (result / "tx.txt").read_text(encoding="utf-8")


def _nested_retry() -> None:
    with workspace() as root:
        repo = _nested_repo(root)
        leaf = repo / "middle" / "leaf"
        config = write_config(root / "config.yml", root / "replays")
        output = root / "output"
        with isolated_environment(root):
            api()(str(repo), no_input=True, extra_context={"owner":"Dara"}, output_dir=str(output), config_file=str(config))
        hook = leaf / "hooks" / "post_gen_project.py"
        hook.write_text(hook.read_text(encoding="utf-8") + "raise SystemExit(5)\n", encoding="utf-8")
        with isolated_environment(root):
            try:
                api()(str(repo), no_input=True, extra_context={"owner":"Failed"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
            except Exception:
                pass
        hook.write_text("from pathlib import Path\nimport os\nPath('tx.txt').write_text(os.environ['COOKIECUTTER_ROOT_TRANSACTION_ID'])\n", encoding="utf-8")
        data = json.loads((leaf / "cookiecutter.json").read_text(encoding="utf-8"))
        data["edition"] = "current-schema"
        (leaf / "cookiecutter.json").write_text(json.dumps(data), encoding="utf-8")
        (leaf / "{{cookiecutter.slug}}" / "edition.txt").write_text("{{cookiecutter.edition}}", encoding="utf-8")
        with isolated_environment(root):
            result = Path(api()(str(repo), no_input=True, extra_context={"owner":"Eira"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config)))
        assert (result / "owner.txt").read_text(encoding="utf-8") == "Eira"
        assert (result / "edition.txt").read_text(encoding="utf-8") == "current-schema"
        saved = read_replay(root / "replays" / "nested-root.json")
        assert saved["owner"] == "Eira" and saved["edition"] == "current-schema"


def _hook_environment() -> None:
    with workspace() as root:
        script = "from pathlib import Path\nimport json,os\nctx=json.loads(os.environ['COOKIECUTTER_CONTEXT'])\nassert Path.cwd().name == ctx['slug']\nassert os.environ['COOKIECUTTER_TRANSACTION_ID'] == os.environ['COOKIECUTTER_ROOT_TRANSACTION_ID']\nPath('hook-view.txt').write_text(ctx['owner']+'|'+os.environ['COOKIECUTTER_TRANSACTION_ID'], encoding='utf-8')\n"
        template = make_template(root / "template", {"slug":"hook-view","owner":"Fara"}, {"{{cookiecutter.slug}}/body.txt":"{{cookiecutter.owner}}"}, {"post_gen_project.py":script})
        config = write_config(root / "config.yml", root / "replays")
        with isolated_environment(root):
            result = Path(api()(str(template), no_input=True, output_dir=str(root / "output"), config_file=str(config)))
        owner, transaction = (result / "hook-view.txt").read_text(encoding="utf-8").split("|")
        assert owner == "Fara" and transaction


def _hook_timeout(descendant: bool = False) -> None:
    with workspace() as root:
        ready, marker = root / "ready", root / "descendant-marker"
        hook = f"from pathlib import Path\nimport os,time\nPath({str(ready)!r}).write_text(str(os.getpid()))\nif os.environ.get('COOKIECUTTER_TRANSACTION_ID'):\n raise SystemExit(124)\nwhile not Path({str(root / 'release')!r}).exists(): time.sleep(0.02)\nPath({str(marker)!r}).write_text('late')\n"
        template = make_template(root / "template", {"slug":"timeout"}, {"{{cookiecutter.slug}}/body.txt":"new"}, {"post_gen_project.py":hook})
        config = write_config(root / "config.yml", root / "replays")
        process = _launch(root, _call_script(template, root / "output", config, {}), {"COOKIECUTTER_HOOK_TIMEOUT":"0.4"})
        _wait(ready)
        pid = int(ready.read_text())
        completed_before_release = True
        try:
            process.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            completed_before_release = False
            (root / "release").write_text("go", encoding="utf-8")
        code, text = _finish(process, timeout=5)
        assert completed_before_release
        assert code != 0, text
        assert not process_alive(pid)
        assert not (root / "output" / "timeout").exists()
        if descendant:
            (root / "release").write_text("go", encoding="utf-8")
            threading.Event().wait(0.15)
            assert not marker.exists()


def _junction(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)


def _destination_alias() -> None:
    with workspace() as root:
        external = root / "external"
        external.mkdir()
        sentinel = external / "sentinel.bin"
        sentinel.write_bytes(b"outside\x00\xff")
        output = root / "output"
        output.mkdir()
        _junction(output / "aliased", external)
        template = make_template(root / "template", {"slug":"aliased"}, {"{{cookiecutter.slug}}/new.txt":"must-not-escape"})
        before = file_tree(external)
        with isolated_environment(root):
            assert_raises(ValueError, api(), str(template), no_input=True, overwrite_if_exists=True, output_dir=str(output))
        assert file_tree(external) == before


def _source_alias() -> None:
    with workspace() as root:
        repo = root / "repo"
        repo.mkdir()
        external = make_template(root / "external-template", {"slug":"escaped-source"}, {"{{cookiecutter.slug}}/body.txt":"outside"})
        _junction(repo / "catalog", external)
        with isolated_environment(root):
            assert_raises(ValueError, api(), str(repo), directory="catalog", no_input=True, output_dir=str(root / "output"))
        assert not (root / "output").exists() or not any((root / "output").iterdir())


def _alias_swap() -> None:
    with workspace() as root:
        external = root / "external"
        external.mkdir()
        (external / "sentinel").write_text("outside", encoding="utf-8")
        output = root / "output"
        final = output / "swap-project"
        hook = f"from pathlib import Path\nimport os,shutil,subprocess\nfinal=Path({str(final)!r})\nif final.exists():\n os.chdir({str(root)!r}); shutil.rmtree(final)\nsubprocess.run(['cmd','/c','mklink','/J',str(final),{str(external)!r}], check=True, capture_output=True)\n"
        template = make_template(root / "template", {"slug":"swap-project"}, {"{{cookiecutter.slug}}/body.txt":"inside"}, {"post_gen_project.py":hook})
        before = file_tree(external)
        with isolated_environment(root):
            assert_raises(ValueError, api(), str(template), no_input=True, overwrite_if_exists=True, output_dir=str(output))
        assert file_tree(external) == before


def _api_cli_contention() -> None:
    with workspace() as root:
        ready, release = root / "ready", root / "release"
        hook = f"from pathlib import Path\nimport time\nPath({str(ready)!r}).write_text('x')\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\n"
        template, config, _ = _basic(root, hook=hook)
        output = root / "output"
        first = _launch(root, _call_script(template, output, config, {"value":"api"}, overwrite=False))
        _wait(ready)
        second = _launch(root, _call_script(template, output, config, {"value":"cli"}, overwrite=False))
        code, text = _finish(second)
        contention_was_typed = code != 0 and "owned" in text.lower()
        release.write_text("go", encoding="utf-8")
        first_code, first_text = _finish(first)
        assert contention_was_typed
        assert first_code == 0, first_text


def _nested_crash_mix() -> None:
    with workspace() as root:
        repo = _nested_repo(root)
        leaf = repo / "middle" / "leaf"
        ready = root / "ready"
        release = root / "release"
        (leaf / "hooks" / "post_gen_project.py").write_text(f"from pathlib import Path\nimport os,signal,time\nPath({str(ready)!r}).write_text('x')\nassert os.environ['COOKIECUTTER_ROOT_TRANSACTION_ID']\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)\nos.kill(os.getppid(), signal.SIGTERM)\n", encoding="utf-8")
        config = write_config(root / "config.yml", root / "replays")
        output = root / "output"
        process = _launch(root, _call_script(repo, output, config, {"owner":"crashed"}, overwrite=True))
        _wait(ready)
        release.write_text("crash", encoding="utf-8")
        _finish(process)
        (leaf / "hooks" / "post_gen_project.py").write_text("from pathlib import Path\nimport os\nPath('tx.txt').write_text(os.environ['COOKIECUTTER_ROOT_TRANSACTION_ID'])\n", encoding="utf-8")
        with isolated_environment(root):
            result = Path(api()(str(repo), no_input=True, extra_context={"owner":"recovered"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config)))
        assert (result / "owner.txt").read_text(encoding="utf-8") == "recovered"
        assert read_replay(root / "replays" / "nested-root.json")["owner"] == "recovered"
        assert not list(output.glob(".cookiecutter-transaction-*"))


def _replay_meta(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    assert "_cookiecutter_replay" in document and isinstance(document["_cookiecutter_replay"], dict)
    return document["_cookiecutter_replay"]


def _replay_revision() -> None:
    with workspace() as root:
        template, config, replay_file = _basic(root)
        _seed(root, template, config, root / "output", "revision-one")
        meta = _replay_meta(replay_file)
        assert meta["revision"] == 1
        assert isinstance(meta["content_digest"], str) and len(meta["content_digest"]) == 64
        assert "parent_digest" not in meta


def _replay_failure_keeps_revision() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        template, config, replay_file = _basic(root)
        output = root / "output"
        _seed(root, template, config, output, "committed")
        prior = replay_file.read_bytes()
        (template / "hooks").mkdir(exist_ok=True)
        (template / "hooks" / "post_gen_project.py").write_text("raise SystemExit(17)\n", encoding="utf-8")
        with isolated_environment(root):
            assert_raises(exceptions.FailedHookException, api(), str(template), no_input=True, extra_context={"value":"abandoned"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
        assert replay_file.read_bytes() == prior
        assert _replay_meta(replay_file)["revision"] == 1


def _replay_chain() -> None:
    with workspace() as root:
        template, config, replay_file = _basic(root)
        output = root / "output"
        _seed(root, template, config, output, "first")
        first = dict(_replay_meta(replay_file))
        _seed(root, template, config, output, "second")
        second = _replay_meta(replay_file)
        assert second["revision"] == first["revision"] + 1
        assert second["parent_digest"] == first["content_digest"]
        assert second["content_digest"] != first["content_digest"]


def _replay_abandon_retry(current_schema: bool = False) -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        template, config, replay_file = _basic(root)
        output = root / "output"
        _seed(root, template, config, output, "base")
        prior = dict(_replay_meta(replay_file))
        if current_schema:
            data = json.loads((template / "cookiecutter.json").read_text(encoding="utf-8"))
            data["edition"] = "ledger-v4"
            (template / "cookiecutter.json").write_text(json.dumps(data), encoding="utf-8")
            (template / "{{cookiecutter.slug}}" / "edition.txt").write_text("{{cookiecutter.edition}}", encoding="utf-8")
        (template / "hooks").mkdir(exist_ok=True)
        failing = template / "hooks" / "post_gen_project.py"
        failing.write_text("raise SystemExit(23)\n", encoding="utf-8")
        with isolated_environment(root):
            assert_raises(exceptions.FailedHookException, api(), str(template), no_input=True, extra_context={"value":"abandoned"}, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
        failing.unlink()
        result = _seed(root, template, config, output, "retried")
        current = _replay_meta(replay_file)
        assert current["revision"] == prior["revision"] + 1
        assert current["parent_digest"] == prior["content_digest"]
        assert read_replay(replay_file)["value"] == "retried"
        if current_schema:
            assert (result / "edition.txt").read_text(encoding="utf-8") == "ledger-v4"


def _replay_target_digest() -> None:
    import hashlib

    with workspace() as root:
        template, config, replay_file = _basic(root)
        result = _seed(root, template, config, root / "output", "digest-view")
        document = json.loads(replay_file.read_text(encoding="utf-8"))
        encoded = json.dumps(document["cookiecutter"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        assert document["_cookiecutter_replay"]["content_digest"] == hashlib.sha256(encoded).hexdigest()
        assert (result / "value.txt").read_text(encoding="utf-8") == document["cookiecutter"]["value"]


def _ack_script(extra: str = "") -> str:
    return (
        "from pathlib import Path\nimport json,os\n"
        "lease=Path(os.environ.get('COOKIECUTTER_HOOK_LEASE','absent-lease'))\n"
        "lease_id=os.environ.get('COOKIECUTTER_HOOK_LEASE_ID','')\n"
        "record=json.loads(lease.read_text(encoding='utf-8')) if lease.is_file() else {}\n"
        + extra
        + "\nack=os.environ.get('COOKIECUTTER_HOOK_ACK','')\n"
        "if ack and lease_id: Path(ack).write_text(lease_id, encoding='utf-8')\n"
    )


def _hook_lease_binding() -> None:
    with workspace() as root:
        hook = _ack_script("Path('lease-view.txt').write_text(str(lease.is_file())+'|'+str(record.get('lease_id',''))+'|'+str(record.get('owner',''))+'|'+str(record.get('root_owner','')), encoding='utf-8')")
        template = make_template(root / "template", {"slug":"leased","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"leased"}, {"post_gen_project.py":hook})
        result = generate(root, template)
        visible, lease_id, owner, root_owner = (result / "lease-view.txt").read_text(encoding="utf-8").split("|")
        assert visible == "True" and lease_id and owner == root_owner


def _hook_ack_required(mismatch: bool = False) -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        if mismatch:
            hook = "from pathlib import Path\nimport os\nack=os.environ.get('COOKIECUTTER_HOOK_ACK','')\nif ack: Path(ack).write_text('borrowed-lease', encoding='utf-8')\n"
        else:
            hook = "from pathlib import Path\nPath('ran.txt').write_text('without-ack', encoding='utf-8')\n"
        template = make_template(root / "template", {"slug":"ack-required","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"new"}, {"post_gen_project.py":hook})
        expected = getattr(exceptions, "HookProtocolException", exceptions.FailedHookException)
        with isolated_environment(root):
            assert_raises(expected, api(), str(template), no_input=True, output_dir=str(root / "output"))
        assert hasattr(exceptions, "HookProtocolException")
        assert not (root / "output" / "ack-required").exists()


def _hook_descendant_cleanup() -> None:
    with workspace() as root:
        release, marker, pid_file = root / "release", root / "late-marker", root / "descendant-pid"
        child = f"from pathlib import Path\nimport os,sys,time\nrelease=Path({str(release)!r})\nlease=os.environ.get('COOKIECUTTER_HOOK_LEASE','')\nwhile not release.exists():\n if lease and not Path(lease).exists(): sys.exit(0)\n time.sleep(0.02)\nPath({str(marker)!r}).write_text('late', encoding='utf-8')\n"
        hook = (
            "from pathlib import Path\nimport json,os,subprocess,sys,time\n"
            f"p=subprocess.Popen([sys.executable,'-c',{child!r}], cwd={str(root)!r})\nPath({str(pid_file)!r}).write_text(str(p.pid), encoding='utf-8')\n"
            "lease=Path(os.environ.get('COOKIECUTTER_HOOK_LEASE','absent-lease'))\n"
            "if lease.is_file():\n data={}\n for _ in range(100):\n  data=json.loads(lease.read_text(encoding='utf-8'))\n  if data.get('process_pid'): break\n  time.sleep(0.01)\n data['descendants']=[p.pid]; lease.write_text(json.dumps(data), encoding='utf-8')\n"
            "raise SystemExit(31)\n"
        )
        template = make_template(root / "template", {"slug":"descendant","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"new"}, {"post_gen_project.py":hook})
        try:
            with isolated_environment(root):
                try:
                    api()(str(template), no_input=True, output_dir=str(root / "output"))
                except Exception:
                    pass
            assert pid_file.is_file()
            threading.Event().wait(0.15)
            release.write_text("go", encoding="utf-8")
            threading.Event().wait(0.25)
            assert not marker.exists()
        finally:
            if pid_file.is_file():
                taskkill(int(pid_file.read_text()))


def _hook_crash_adoption(return_result: bool = False):
    with workspace() as root:
        ready, release, marker, pid_file = root / "ready", root / "release", root / "late-marker", root / "descendant-pid"
        child = f"from pathlib import Path\nimport os,sys,time\nrelease=Path({str(release)!r})\nlease=os.environ.get('COOKIECUTTER_HOOK_LEASE','')\nwhile not release.exists():\n if lease and not Path(lease).exists(): sys.exit(0)\n time.sleep(0.02)\nPath({str(marker)!r}).write_text('late', encoding='utf-8')\n"
        crash_hook = (
            "from pathlib import Path\nimport json,os,signal,subprocess,sys,time\n"
            f"p=subprocess.Popen([sys.executable,'-c',{child!r}], cwd={str(root)!r})\nPath({str(pid_file)!r}).write_text(str(p.pid), encoding='utf-8')\n"
            "lease=Path(os.environ.get('COOKIECUTTER_HOOK_LEASE','absent-lease'))\n"
            "if lease.is_file():\n data={}\n for _ in range(100):\n  data=json.loads(lease.read_text(encoding='utf-8'))\n  if data.get('process_pid'): break\n  time.sleep(0.01)\n data['descendants']=[p.pid]; lease.write_text(json.dumps(data), encoding='utf-8')\n"
            f"Path({str(ready)!r}).write_text('ready', encoding='utf-8')\nos.kill(os.getppid(), signal.SIGTERM)\n"
        )
        template = make_template(root / "template", {"slug":"adopted","value":"old","_require_hook_ack":True}, {"{{cookiecutter.slug}}/value.txt":"{{cookiecutter.value}}"}, {"post_gen_project.py":crash_hook})
        replay_dir = root / "replays"
        config = write_config(root / "config.yml", replay_dir)
        output = root / "output"
        process = _launch(root, _call_script(template, output, config, {"value":"crashed"}, overwrite=True))
        try:
            _wait(ready)
            _finish(process, timeout=6)
            (template / "hooks" / "post_gen_project.py").write_text(_ack_script("Path('retry.txt').write_text('acknowledged', encoding='utf-8')"), encoding="utf-8")
            result = _seed(root, template, config, output, "recovered", accept_hooks=True)
            release.write_text("go", encoding="utf-8")
            threading.Event().wait(0.25)
            assert not marker.exists()
            assert (result / "retry.txt").read_text(encoding="utf-8") == "acknowledged"
            if return_result:
                assert _replay_meta(replay_dir / "template.json")["revision"] == 1
        finally:
            if pid_file.is_file():
                taskkill(int(pid_file.read_text()))


def _hook_live_isolation() -> None:
    with workspace() as root:
        ready, release = root / "ready", root / "release"
        first_hook = _ack_script(f"Path({str(ready)!r}).write_text(str(lease.is_file()), encoding='utf-8')\nimport time\nwhile not Path({str(release)!r}).exists(): time.sleep(0.02)")
        first = make_template(root / "first", {"slug":"lease-one","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"one"}, {"post_gen_project.py":first_hook})
        second = make_template(root / "second", {"slug":"lease-two","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"two"}, {"post_gen_project.py":_ack_script("Path('done.txt').write_text(str(lease.is_file()), encoding='utf-8')")})
        config = write_config(root / "config.yml", root / "replays")
        output = root / "output"
        process = _launch(root, _call_script(first, output, config, {}, overwrite=False))
        _wait(ready)
        result = _seed(root, second, config, output, accept_hooks=True)
        release.write_text("go", encoding="utf-8")
        code, text = _finish(process)
        assert code == 0, text
        assert ready.read_text() == "True" and (result / "done.txt").read_text(encoding="utf-8") == "True"


def _capability_binding() -> None:
    with workspace() as root:
        extra = "cap=Path(os.environ.get('COOKIECUTTER_PUBLICATION_CAPABILITY','absent-cap'))\nPath('cap-view.txt').write_text(str(cap.is_file())+'|'+os.environ.get('COOKIECUTTER_PUBLICATION_TARGET_ID','')+'|'+os.environ.get('COOKIECUTTER_PUBLICATION_REPLAY_ID',''), encoding='utf-8')"
        template = make_template(root / "template", {"slug":"cap-bound","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"ok"}, {"post_gen_project.py":_ack_script(extra)})
        result = generate(root, template)
        visible, target_id, replay_id = (result / "cap-view.txt").read_text(encoding="utf-8").split("|")
        assert visible == "True" and target_id and replay_id and target_id != replay_id


def _capability_missing() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        extra = "cap=Path(os.environ.get('COOKIECUTTER_PUBLICATION_CAPABILITY','absent-cap'))\nif cap.is_file(): cap.unlink()"
        template = make_template(root / "template", {"slug":"cap-required","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"new"}, {"post_gen_project.py":_ack_script(extra)})
        expected = getattr(exceptions, "PublicationConflictException", exceptions.CookiecutterException)
        with isolated_environment(root):
            assert_raises(expected, api(), str(template), no_input=True, output_dir=str(root / "output"))
        assert hasattr(exceptions, "PublicationConflictException")
        assert not (root / "output" / "cap-required").exists()


def _copy_capability_hook(destination: Path) -> str:
    extra = f"cap=Path(os.environ.get('COOKIECUTTER_PUBLICATION_CAPABILITY','absent-cap'))\nif cap.is_file(): Path({str(destination)!r}).write_bytes(cap.read_bytes())"
    return _ack_script(extra)


def _borrowed_capability(two_resources: bool = False) -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        saved = root / "saved-capability"
        first = make_template(root / "first", {"slug":"cap-one","value":"old","_require_hook_ack":True}, {"{{cookiecutter.slug}}/value.txt":"{{cookiecutter.value}}"}, {"post_gen_project.py":_copy_capability_hook(saved)})
        replay_dir = root / "replays"
        config = write_config(root / "config.yml", replay_dir)
        output = root / "output"
        first_result = _seed(root, first, config, output, "committed", accept_hooks=True)
        first_tree = file_tree(first_result)
        first_replay = (replay_dir / "first.json").read_bytes()
        second = first
        if two_resources:
            second = make_template(root / "second", {"slug":"cap-two","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"two"})
        replace = _ack_script(f"cap=Path(os.environ.get('COOKIECUTTER_PUBLICATION_CAPABILITY','absent-cap'))\nif cap.is_file() and Path({str(saved)!r}).is_file(): cap.write_bytes(Path({str(saved)!r}).read_bytes())")
        (second / "hooks").mkdir(exist_ok=True)
        (second / "hooks" / "post_gen_project.py").write_text(replace, encoding="utf-8")
        expected = getattr(exceptions, "PublicationConflictException", exceptions.CookiecutterException)
        with isolated_environment(root):
            assert_raises(expected, api(), str(second), no_input=True, extra_context={"value":"rejected"} if not two_resources else None, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
        assert hasattr(exceptions, "PublicationConflictException")
        assert file_tree(first_result) == first_tree and (replay_dir / "first.json").read_bytes() == first_replay
        if two_resources:
            assert not (output / "cap-two").exists()


def _tampered_capability_identity() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        extra = "cap=Path(os.environ.get('COOKIECUTTER_PUBLICATION_CAPABILITY','absent-cap'))\nif cap.is_file():\n data=json.loads(cap.read_text(encoding='utf-8')); data['target_identity']='borrowed-target'; cap.write_text(json.dumps(data), encoding='utf-8')"
        template = make_template(root / "template", {"slug":"identity-cap","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"new"}, {"post_gen_project.py":_ack_script(extra)})
        expected = getattr(exceptions, "PublicationConflictException", exceptions.CookiecutterException)
        with isolated_environment(root):
            assert_raises(expected, api(), str(template), no_input=True, output_dir=str(root / "output"))
        assert hasattr(exceptions, "PublicationConflictException")
        assert not (root / "output" / "identity-cap").exists()


def _capability_restore_pair() -> None:
    from cookiecutter import exceptions

    with workspace() as root:
        template, config, replay_file = _basic(root)
        output = root / "output"
        prior = _seed(root, template, config, output, "prior")
        old_tree, old_replay = file_tree(prior), replay_file.read_bytes()
        (template / "cookiecutter.json").write_text(json.dumps({"slug":"durable","value":"new","_require_hook_ack":True}), encoding="utf-8")
        (template / "hooks").mkdir(exist_ok=True)
        (template / "hooks" / "post_gen_project.py").write_text(_ack_script("cap=Path(os.environ.get('COOKIECUTTER_PUBLICATION_CAPABILITY','absent-cap'))\nif cap.is_file(): cap.unlink()"), encoding="utf-8")
        expected = getattr(exceptions, "PublicationConflictException", exceptions.CookiecutterException)
        with isolated_environment(root):
            assert_raises(expected, api(), str(template), no_input=True, overwrite_if_exists=True, output_dir=str(output), config_file=str(config))
        assert hasattr(exceptions, "PublicationConflictException")
        assert file_tree(prior) == old_tree and replay_file.read_bytes() == old_replay


def _nested_authorized() -> None:
    with workspace() as root:
        repo = make_template(root / "root", {"templates":{"leaf":{"path":"leaf"}}}, {})
        extra = "cap=Path(os.environ.get('COOKIECUTTER_PUBLICATION_CAPABILITY','absent-cap'))\nPath('ownership.txt').write_text(str(lease.is_file())+'|'+str(cap.is_file())+'|'+str(record.get('root_owner')==os.environ.get('COOKIECUTTER_ROOT_TRANSACTION_ID')), encoding='utf-8')"
        make_template(repo / "leaf", {"slug":"nested-authorized","_require_hook_ack":True}, {"{{cookiecutter.slug}}/body.txt":"ok"}, {"post_gen_project.py":_ack_script(extra)})
        result = generate(root, repo)
        assert (result / "ownership.txt").read_text(encoding="utf-8") == "True|True|True"


def _output_replay_recovery() -> None:
    _journal_prepare()


def _api_cli_resource_contention() -> None:
    _api_cli_contention()


ATOMIC = {
    "A13": _journal_prepare,
    "A14": _journal_published,
    "A15": _replay_revision,
    "A16": _replay_failure_keeps_revision,
    "A17": _hook_lease_binding,
    "A18": _hook_ack_required,
    "A19": _capability_binding,
    "A20": _capability_missing,
}


COMPOSITION = {
    "I07": _journal_prepare,
    "I08": _journal_published,
    "I09": lambda: _journal_published(repeat=True),
    "I10": _journal_scope,
    "I11": _replay_chain,
    "I12": _replay_abandon_retry,
    "I13": lambda: _replay_abandon_retry(current_schema=True),
    "I14": _replay_target_digest,
    "I15": _nested_rollback,
    "I16": _nested_staging,
    "I17": _nested_retry,
    "I18": _nested_authorized,
    "I19": lambda: _hook_ack_required(mismatch=True),
    "I20": _hook_descendant_cleanup,
    "I21": _hook_crash_adoption,
    "I22": _hook_live_isolation,
    "I23": _borrowed_capability,
    "I24": lambda: _borrowed_capability(two_resources=True),
    "I25": _tampered_capability_identity,
    "I26": _capability_restore_pair,
    "I27": _owner_conflict,
    "I28": _sibling_independence,
    "S01": _output_replay_recovery,
    "S02": lambda: _replay_abandon_retry(current_schema=True),
    "S03": _nested_rollback,
    "S04": _hook_crash_adoption,
    "S05": _capability_restore_pair,
    "S06": _api_cli_resource_contention,
    "S07": _nested_authorized,
    "S08": lambda: _hook_crash_adoption(return_result=True),
}


def atomic_mutation(root_id: str) -> None:
    ATOMIC[root_id]()


def composition_mutation(root_id: str) -> None:
    COMPOSITION[root_id]()
