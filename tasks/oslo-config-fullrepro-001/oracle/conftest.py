from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml


class TargetOnlyOsloConfigFinder:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "oslo_config" or fullname.startswith("oslo_config."):
            raise ModuleNotFoundError("oslo_config is not available from the selected target root")
        return None


def pytest_addoption(parser):
    parser.addoption(
        "--target-root",
        action="store",
        default=os.environ.get("TARGET_ROOT"),
        help="Path containing the oslo_config package under test",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "depends_on(*names): atomic behaviors required by an integration test",
    )


def pytest_sessionstart(session):
    configured_root = session.config.getoption("--target-root")
    if configured_root is None:
        return

    target_root = Path(configured_root).resolve()
    os.environ["TARGET_ROOT"] = str(target_root)
    for name in list(sys.modules):
        if name == "oslo_config" or name.startswith("oslo_config."):
            sys.modules.pop(name, None)
    sys.path.insert(0, str(target_root))
    if not (target_root / "oslo_config").is_dir():
        sys.meta_path.insert(0, TargetOnlyOsloConfigFinder())


def write_ini(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    return path


def base_conf():
    from oslo_config import cfg

    conf = cfg.ConfigOpts()
    conf.register_cli_opt(cfg.StrOpt("name", default="default-name"))
    conf.register_cli_opt(cfg.IntOpt("workers", default=2, min=1, max=16))
    conf.register_cli_opt(cfg.BoolOpt("enabled", default=True))
    conf.register_cli_opt(cfg.ListOpt("hosts", default=["one"]))
    conf.register_cli_opt(cfg.DictOpt("labels", default={"role": "api"}))
    conf.register_cli_opt(cfg.MultiStrOpt("path", default=["/srv/default"]))
    api = cfg.OptGroup("api", title="API options", help="Local API settings")
    conf.register_group(api)
    conf.register_cli_opt(cfg.PortOpt("listen-port", default=8774, min=1, max=65535), group=api)
    conf.register_cli_opt(cfg.StrOpt("mode", default="public", choices=["public", "admin"]), group=api)
    conf.register_cli_opt(cfg.StrOpt("quoted", default="plain", quotes=True), group=api)
    return conf


def configured_conf(tmp_path: Path, body: str, extra_args: list[str] | None = None):
    conf = base_conf()
    config_path = write_ini(tmp_path / "sample.conf", body)
    args = ["--config-file", str(config_path)]
    if extra_args:
        args.extend(extra_args)
    conf(args, project="aurora", version="1.0", use_env=False)
    return conf, config_path


def write_entrypoint_tree(tmp_path: Path) -> Path:
    root = tmp_path / "entrypoint_root"
    root.mkdir(parents=True)
    (root / "aurora_config_options.py").write_text(
        textwrap.dedent(
            """
            from oslo_config import cfg

            api_group = cfg.OptGroup(
                "api",
                title="API options",
                help="Options for the generated local API service.",
            )

            default_opts = [
                cfg.BoolOpt("enabled", default=True, help="Enable the service."),
                cfg.StrOpt("token", default=None, secret=True, help="Shared token."),
                cfg.MultiStrOpt("path", default=["/srv/api"], help="Search paths."),
            ]

            api_opts = [
                cfg.StrOpt(
                    "mode",
                    default="public",
                    choices=[("public", "Public API"), ("admin", "Admin API")],
                    help="API mode.",
                ),
                cfg.PortOpt(
                    "listen-port",
                    default=8774,
                    min=1,
                    max=65535,
                    sample_default="9000",
                    help="Port for the API listener.",
                ),
                cfg.IntOpt("workers", default=2, min=1, max=8, help="Worker count."),
                cfg.ListOpt("tags", default=["blue", "green"], help="Service tags."),
                cfg.DictOpt("headers", default={"X-Service": "aurora"}, help="Headers."),
                cfg.StrOpt("tuning", default="safe", advanced=True, help="Advanced tuning."),
                cfg.StrOpt(
                    "new-name",
                    default="fresh",
                    deprecated_opts=[cfg.DeprecatedOpt("old_name", group="api")],
                    help="Replacement option.",
                ),
            ]

            def list_opts():
                return [(None, default_opts), (api_group, api_opts)]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    dist = root / "aurora_config_options-1.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text("Name: aurora-config-options\nVersion: 1.0\n", encoding="utf-8")
    (dist / "entry_points.txt").write_text(
        "[oslo.config.opts]\naurora.sample = aurora_config_options:list_opts\n",
        encoding="utf-8",
    )
    oslo_dist = root / "oslo.config-99.0.dist-info"
    oslo_dist.mkdir()
    (oslo_dist / "METADATA").write_text("Name: oslo.config\nVersion: 99.0\n", encoding="utf-8")
    return root


def cli_env(entry_root: Path | None = None) -> dict[str, str]:
    env = dict(os.environ)
    configured = os.environ.get("TARGET_ROOT")
    paths: list[str] = []
    if configured:
        paths.append(str(Path(configured).resolve()))
    if entry_root is not None:
        paths.append(str(entry_root))
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_module(module: str, args: list[str], entry_root: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=cli_env(entry_root),
        check=False,
    )


def generate_sample(tmp_path: Path, format_name: str = "yaml") -> tuple[Path, Path]:
    entry_root = write_entrypoint_tree(tmp_path)
    output = tmp_path / f"sample.{format_name}"
    result = run_module(
        "oslo_config.generator",
        ["--namespace", "aurora.sample", "--format", format_name, "--output-file", str(output)],
        entry_root,
    )
    if result.returncode != 0:
        pytest.fail("generator command failed")
    assert output.is_file()
    return output, entry_root


def load_json_sample(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml_sample(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
