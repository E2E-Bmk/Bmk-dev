import io
from pathlib import Path

import pytest
import sqlalchemy as sa

import alembic
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from alembic.util.exc import CommandError


def make_config(tmp_path: Path) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(tmp_path / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path / 'db.sqlite'}")
    return cfg


def write_env(script_location: Path, body: str) -> None:
    script_location.mkdir(parents=True, exist_ok=True)
    (script_location / "versions").mkdir(exist_ok=True)
    (script_location / "env.py").write_text(body, encoding="utf-8")
    (script_location / "script.py.mako").write_text(
        """\"\"\"${message}\"\"\"\nrevision = ${repr(up_revision)}\ndown_revision = ${repr(down_revision)}\nbranch_labels = ${repr(branch_labels)}\ndepends_on = ${repr(depends_on)}\n\n\ndef upgrade():\n    pass\n\n\ndef downgrade():\n    pass\n""",
        encoding="utf-8",
    )


def online_env_body() -> str:
    return """
from alembic import context
from sqlalchemy import create_engine

config = context.config

def run_migrations_online():
    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
"""


def offline_env_body() -> str:
    return """
from alembic import context
config = context.config
context.configure(url=config.get_main_option("sqlalchemy.url"), output_buffer=config.output_buffer)
with context.begin_transaction():
    context.run_migrations()
"""


def test_installable_surface_exports_version_config_and_command_api():
    assert isinstance(alembic.__version__, str)
    assert alembic.__version__
    assert callable(command.upgrade)
    assert callable(command.revision)
    assert Config.__name__ == "Config"


def test_config_file_name_and_attributes_are_public_state(tmp_path):
    ini = tmp_path / "alembic.ini"
    ini.write_text("[alembic]\nscript_location = migrations\n", encoding="utf-8")

    cfg = Config(str(ini))
    cfg.attributes["connection"] = "shared"

    assert Path(cfg.config_file_name) == ini
    assert cfg.get_main_option("script_location") == "migrations"
    assert cfg.attributes["connection"] == "shared"


def test_command_init_creates_generic_template_environment(tmp_path):
    ini = tmp_path / "alembic.ini"
    ini.write_text("[alembic]\n", encoding="utf-8")
    cfg = Config(str(ini))
    target = tmp_path / "migrations"

    command.init(cfg, str(target), template="generic")

    assert (target / "env.py").exists()
    assert (target / "script.py.mako").exists()
    assert (target / "versions").is_dir()


def test_script_directory_from_config_reads_revision_files(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", online_env_body())
    rev = command.revision(cfg, message="create table")

    directory = ScriptDirectory.from_config(cfg)

    assert directory.get_revision(rev.revision).revision == rev.revision
    assert directory.get_heads() == [rev.revision]


def test_environment_context_online_upgrade_runs_env_script(tmp_path):
    cfg = make_config(tmp_path)
    script = tmp_path / "migrations"
    write_env(script, online_env_body())
    rev = command.revision(cfg, message="base")

    command.upgrade(cfg, "head")

    engine = sa.create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as conn:
        rows = conn.execute(sa.text("select version_num from alembic_version")).scalars().all()
    assert rows == [rev.revision]


def test_environment_context_offline_upgrade_uses_output_buffer(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", offline_env_body())
    rev = command.revision(cfg, message="base")
    buffer = io.StringIO()
    cfg.output_buffer = buffer

    command.upgrade(cfg, "head", sql=True)

    output = buffer.getvalue()
    assert "CREATE TABLE alembic_version" in output
    assert rev.revision in output


def test_migration_context_reports_current_heads_from_database(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'db.sqlite'}")
    with engine.begin() as conn:
        conn.execute(sa.text("create table alembic_version (version_num varchar(32) not null)"))
        conn.execute(sa.text("insert into alembic_version values ('abc123')"))
        ctx = MigrationContext.configure(conn)
        assert ctx.get_current_heads() == ("abc123",)


def test_migration_context_offline_version_table_name_is_configurable():
    buffer = io.StringIO()
    ctx = MigrationContext.configure(
        url="sqlite://",
        opts={"as_sql": True, "output_buffer": buffer, "version_table": "custom_version"},
    )
    op = Operations(ctx)

    op.create_table("sample", sa.Column("id", sa.Integer, primary_key=True))

    assert "CREATE TABLE sample" in buffer.getvalue()


def test_operations_add_column_offline_renders_sql():
    buffer = io.StringIO()
    ctx = MigrationContext.configure(url="sqlite://", opts={"as_sql": True, "output_buffer": buffer})
    op = Operations(ctx)

    op.add_column("account", sa.Column("name", sa.String(30)))

    assert "ALTER TABLE account ADD COLUMN name VARCHAR(30)" in buffer.getvalue()


def test_operations_drop_column_offline_renders_sql():
    buffer = io.StringIO()
    ctx = MigrationContext.configure(url="sqlite://", opts={"as_sql": True, "output_buffer": buffer})
    op = Operations(ctx)

    op.drop_column("account", "name")

    assert "ALTER TABLE account DROP COLUMN name" in buffer.getvalue()


def test_batch_alter_table_offline_requires_copy_from_for_sqlite():
    buffer = io.StringIO()
    ctx = MigrationContext.configure(url="sqlite://", opts={"as_sql": True, "output_buffer": buffer})
    op = Operations(ctx)

    with pytest.raises(CommandError):
        with op.batch_alter_table("account") as batch:
            batch.drop_column("name")


def test_command_stamp_creates_version_table_without_running_migrations(tmp_path):
    cfg = make_config(tmp_path)
    script = tmp_path / "migrations"
    write_env(script, online_env_body())
    rev = command.revision(cfg, message="base")

    command.stamp(cfg, rev.revision)

    engine = sa.create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as conn:
        rows = conn.execute(sa.text("select version_num from alembic_version")).scalars().all()
        assert rows == [rev.revision]
        assert "sample" not in sa.inspect(conn).get_table_names()


def test_command_current_reports_database_revision(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", online_env_body())
    rev = command.revision(cfg, message="base")
    command.stamp(cfg, "head")
    buffer = io.StringIO()
    cfg.stdout = buffer

    command.current(cfg)

    assert rev.revision in buffer.getvalue()


def test_command_history_reports_revision_message(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", online_env_body())
    rev = command.revision(cfg, message="base message")
    buffer = io.StringIO()
    cfg.stdout = buffer

    command.history(cfg)

    assert rev.revision in buffer.getvalue()
    assert "base message" in buffer.getvalue()


def test_command_branches_reports_branch_point(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", online_env_body())
    base = command.revision(cfg, message="base")
    command.revision(cfg, message="left", head=base.revision)
    command.revision(cfg, message="right", head=base.revision, splice=True)
    buffer = io.StringIO()
    cfg.stdout = buffer

    command.branches(cfg)

    assert base.revision in buffer.getvalue()


def test_revision_autogenerate_requires_database_connection(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", offline_env_body())

    with pytest.raises((AssertionError, CommandError)):
        command.revision(cfg, message="auto", autogenerate=True)


def test_missing_revision_raises_command_error(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", online_env_body())

    with pytest.raises(CommandError):
        command.upgrade(cfg, "does_not_exist")


def test_ensure_version_is_idempotent(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", online_env_body())

    command.ensure_version(cfg)
    command.ensure_version(cfg)

    engine = sa.create_engine(cfg.get_main_option("sqlalchemy.url"))
    with engine.connect() as conn:
        assert "alembic_version" in sa.inspect(conn).get_table_names()


def test_cross_view_heads_match_history_and_script_directory(tmp_path):
    cfg = make_config(tmp_path)
    write_env(tmp_path / "migrations", online_env_body())
    rev = command.revision(cfg, message="base")
    directory = ScriptDirectory.from_config(cfg)
    buffer = io.StringIO()
    cfg.stdout = buffer

    command.heads(cfg)

    assert directory.get_heads() == [rev.revision]
    assert rev.revision in buffer.getvalue()


def test_representative_init_revision_upgrade_current_workflow(tmp_path):
    cfg = make_config(tmp_path)
    script = tmp_path / "migrations"
    write_env(script, online_env_body())
    rev = command.revision(cfg, message="workflow")

    command.upgrade(cfg, "head")
    buffer = io.StringIO()
    cfg.stdout = buffer
    command.current(cfg)

    assert rev.revision in buffer.getvalue()
