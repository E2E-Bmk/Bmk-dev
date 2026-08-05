from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from support import (
    AdminWorkflowController,
    AlternateOutputHandler,
    BaseWorkflowController,
    DollarTemplateHandler,
    EmbeddedWorkflowController,
    MetricHandler,
    MetricInterface,
    RenderingWorkflowController,
    TextOutputHandler,
    load_template,
    new_app,
)


@pytest.mark.depends_on("test_context_setup_exposes_core_interfaces", "test_framework_hook_names_are_defined")
def test_lifecycle_hooks_span_setup_run_and_close():
    events = []

    def mark_pre_setup(app):
        events.append("pre_setup")

    def mark_post_setup(app):
        events.append("post_setup")

    def mark_pre_run(app):
        events.append("pre_run")

    def mark_post_run(app):
        events.append("post_run")

    def mark_pre_close(app):
        events.append("pre_close")

    def mark_post_close(app):
        events.append("post_close")

    hooks = [
        ("pre_setup", mark_pre_setup),
        ("post_setup", mark_post_setup),
        ("pre_run", mark_pre_run),
        ("post_run", mark_post_run),
        ("pre_close", mark_pre_close),
        ("post_close", mark_post_close),
    ]
    with new_app(hooks=hooks) as app:
        app.run()
        assert events[:4] == ["pre_setup", "post_setup", "pre_run", "post_run"]
    assert events == ["pre_setup", "post_setup", "pre_run", "post_run", "pre_close", "post_close"]


@pytest.mark.depends_on(
    "test_debug_property_follows_debug_argument",
    "test_add_arg_populates_parsed_arguments",
    "test_config_defaults_are_available_through_config_interface",
)
def test_config_defaults_and_argv_are_merged_into_run_state():
    defaults = {"merge-run": {"answer": "from-config"}}
    with new_app(label="merge-run", config_defaults=defaults, argv=["--debug", "--answer", "from-argv"]) as app:
        app.add_arg("--answer", default=app.config.get("merge-run", "answer"))
        app.run()
        assert app.debug is True
        assert app.config.get("merge-run", "answer") == "from-config"
        assert app.pargs.answer == "from-argv"


@pytest.mark.depends_on(
    "test_config_parse_file_loads_local_ini",
    "test_json_extension_registers_json_output_handler",
    "test_json_output_handler_returns_parseable_object",
)
def test_config_file_can_select_json_extension_and_output(tmp_path):
    config_path = tmp_path / "file-app.conf"
    config_path.write_text(
        "[file-app]\n"
        "extensions = json\n"
        "output_handler = json\n",
        encoding="utf-8",
    )
    with new_app(
        label="file-app",
        config_files=[str(config_path)],
        argv=["--quiet"],
    ) as app:
        app.run()
        rendered = app.render({"source": "config"}, out=None)
        assert app.output.__class__.Meta.label == "json"
        assert "cement.ext.ext_json" in app.ext.get_loaded_extensions()
        assert json.loads(rendered) == {"source": "config"}


@pytest.mark.depends_on("test_config_parse_file_loads_local_ini")
def test_config_files_apply_deterministic_sorted_directory_precedence(tmp_path):
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "01-first.conf").write_text("[dir-app]\nvalue = first\n", encoding="utf-8")
    (config_dir / "02-second.conf").write_text("[dir-app]\nvalue = second\n", encoding="utf-8")
    with new_app(label="dir-app", config_dirs=[str(config_dir)]) as app:
        assert app.config.get("dir-app", "value") == "second"


@pytest.mark.depends_on(
    "test_custom_interface_can_be_defined_at_runtime",
    "test_handler_registered_in_app_metadata_is_visible",
    "test_handler_resolve_label_creates_instance",
)
def test_custom_interface_handler_round_trip_through_manager():
    with new_app(interfaces=[MetricInterface], handlers=[MetricHandler]) as app:
        resolved = app.handler.resolve("metric", "basic", setup=True)
        assert app.interface.get("metric") is MetricInterface
        assert resolved.describe().endswith(":basic")


@pytest.mark.depends_on(
    "test_handler_get_returns_registered_class",
    "test_handler_resolve_label_creates_instance",
    "test_handler_resolve_class_registers_and_creates_instance",
)
def test_handler_resolution_forms_share_handler_behavior():
    with new_app(interfaces=[MetricInterface], handlers=[MetricHandler]) as app:
        by_label = app.handler.resolve("metric", "basic", setup=True)
        by_class = app.handler.resolve("metric", MetricHandler, setup=True)
        by_instance = app.handler.resolve("metric", MetricHandler(), setup=True)
        assert [handler.describe().split(":")[-1] for handler in (by_label, by_class, by_instance)] == [
            "basic",
            "basic",
            "basic",
        ]


@pytest.mark.depends_on("test_handler_list_returns_classes_for_interface", "test_add_arg_populates_parsed_arguments")
def test_handler_override_option_selects_overridable_output():
    with new_app(
        handlers=[TextOutputHandler, AlternateOutputHandler],
        output_handler="dummy",
        argv=["-o", "text"],
    ) as app:
        app.run()
        assert app.output.__class__.Meta.label == "text"
        assert app.render({"kind": "selected", "value": "yes"}, out=None) == "selected:yes"


@pytest.mark.depends_on("test_hook_manager_orders_registered_callbacks_by_weight", "test_json_output_handler_returns_parseable_object")
def test_weighted_hook_pipeline_changes_rendered_data():
    def add_marker(app, data):
        updated = dict(data)
        updated["hooked"] = True
        return updated

    with new_app(
        extensions=["json"],
        output_handler="json",
        hooks=[("pre_render", add_marker)],
    ) as app:
        rendered = app.render({"value": 7}, out=None)
        assert json.loads(rendered) == {"value": 7, "hooked": True}


@pytest.mark.depends_on("test_hook_manager_flattens_generator_results", "test_last_rendered_records_data_and_text")
def test_hook_generator_and_post_render_form_one_pipeline():
    def post_render(app, text):
        return text + "\n"

    with new_app(
        extensions=["json"],
        output_handler="json",
        hooks=[("post_render", post_render)],
    ) as app:
        rendered = app.render({"value": "pipeline"}, out=None)
        assert rendered.endswith("\n")
        assert json.loads(rendered.rstrip()) == {"value": "pipeline"}
        assert app.last_rendered == ({"value": "pipeline"}, rendered)


@pytest.mark.depends_on("test_add_arg_populates_parsed_arguments")
def test_base_controller_dispatches_command_arguments():
    with new_app(
        handlers=[BaseWorkflowController],
        argv=["greet", "--name", "Ada"],
    ) as app:
        result = app.run()
        assert result == {"message": "hello Ada"}
        assert app.pargs.name == "Ada"


@pytest.mark.depends_on("test_add_arg_populates_parsed_arguments")
def test_controller_command_alias_dispatches_same_function():
    with new_app(handlers=[BaseWorkflowController], argv=["say-hi"]) as app:
        assert app.run() == {"message": "pong"}


@pytest.mark.depends_on("test_add_arg_populates_parsed_arguments")
def test_nested_controller_dispatches_subcommand():
    with new_app(
        handlers=[BaseWorkflowController, AdminWorkflowController],
        argv=["admin", "status"],
    ) as app:
        assert app.run() == {"status": "ready"}


@pytest.mark.depends_on("test_add_arg_populates_parsed_arguments")
def test_embedded_controller_shares_base_namespace():
    with new_app(
        handlers=[BaseWorkflowController, EmbeddedWorkflowController],
        argv=["inspect"],
    ) as app:
        assert app.run() == {"scope": "embedded"}


@pytest.mark.depends_on("test_add_arg_populates_parsed_arguments")
def test_controller_and_command_arguments_reach_command():
    with new_app(
        handlers=[BaseWorkflowController],
        argv=["greet", "--name", "command-value"],
    ) as app:
        result = app.run()
        assert result["message"].endswith("command-value")


@pytest.mark.depends_on(
    "test_json_output_handler_returns_parseable_object",
    "test_add_arg_populates_parsed_arguments",
)
def test_controller_result_can_be_rendered_as_json():
    with new_app(
        handlers=[RenderingWorkflowController],
        extensions=["json"],
        output_handler="json",
        argv=["report", "--name", "Nia"],
    ) as app:
        result = app.run()
        assert json.loads(result) == {"kind": "report", "name": "Nia"}


@pytest.mark.depends_on("test_print_extension_renders_only_out_field")
def test_print_extension_adds_app_print_after_argument_parse():
    calls = []

    with new_app(extensions=["print"], output_handler="print") as app:
        app.run()
        def record_render(data, **kwargs):
            calls.append((data, kwargs))

        app.render = record_render
        app.print("hello")
    assert calls == [({"out": "hello"}, {"handler": "print"})]


@pytest.mark.depends_on(
    "test_extension_loader_expands_short_names",
    "test_json_extension_registers_json_output_handler",
    "test_print_extension_renders_only_out_field",
)
def test_multiple_extensions_share_one_app_handler_graph():
    with new_app(extensions=["json", "print"]) as app:
        loaded = app.ext.get_loaded_extensions()
        assert "cement.ext.ext_json" in loaded
        assert "cement.ext.ext_print" in loaded
        assert app.handler.registered("output", "json")
        assert app.handler.registered("output", "print")


@pytest.mark.depends_on("test_config_defaults_are_available_through_config_interface", "test_extension_loader_expands_short_names")
def test_extension_loaded_from_config_section_uses_custom_section(tmp_path):
    config_path = tmp_path / "custom-section.conf"
    config_path.write_text(
        "[custom]\n"
        "extensions = json\n"
        "output_handler = json\n",
        encoding="utf-8",
    )
    with new_app(
        label="label-app",
        config_section="custom",
        config_files=[str(config_path)],
        argv=["--quiet"],
    ) as app:
        app.run()
        assert app.config.get("custom", "extensions") == ["json"]
        assert app.output.__class__.Meta.label == "json"


@pytest.mark.depends_on("test_template_handler_copy_creates_local_project_file")
def test_template_copy_renders_directory_and_file_names(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "$package").mkdir(parents=True)
    (source / "$package" / "README-$project.txt").write_text(
        "Package: $package\nProject: $project\n",
        encoding="utf-8",
    )
    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        app.template.copy(
            str(source),
            str(destination),
            {"package": "demo_pkg", "project": "cement"},
        )
    output = destination / "demo_pkg" / "README-cement.txt"
    assert output.read_text(encoding="utf-8") == "Package: demo_pkg\nProject: cement\n"


@pytest.mark.depends_on("test_template_handler_copy_creates_local_project_file")
def test_template_copy_honors_exclude_and_ignore_rules(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "rendered.txt").write_text("$value", encoding="utf-8")
    (source / "raw.txt").write_text("$value", encoding="utf-8")
    (source / "skip.txt").write_text("$value", encoding="utf-8")
    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        app.template.copy(
            str(source),
            str(destination),
            {"value": "expanded"},
            exclude=[r".*raw\.txt$"],
            ignore=[r".*skip\.txt$"],
        )
    assert (destination / "rendered.txt").read_text(encoding="utf-8") == "expanded"
    assert (destination / "raw.txt").read_text(encoding="utf-8") == "$value"
    assert not (destination / "skip.txt").exists()


@pytest.mark.depends_on("test_template_handler_copy_creates_local_project_file")
def test_template_copy_requires_force_for_existing_files(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    source_file = source / "README.txt"
    source_file.write_text("first", encoding="utf-8")
    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        app.template.copy(str(source), str(destination), {})
        source_file.write_text("second", encoding="utf-8")
        with pytest.raises(AssertionError):
            app.template.copy(str(source), str(destination), {})
        app.template.copy(str(source), str(destination), {}, force=True)
    assert (destination / "README.txt").read_text(encoding="utf-8") == "second"


@pytest.mark.depends_on("test_template_handler_loads_file_from_template_directory")
def test_template_load_prefers_added_local_directory(tmp_path):
    template_dir = tmp_path / "later"
    template_dir.mkdir()
    (template_dir / "later.txt").write_text("Later $value", encoding="utf-8")
    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        app.add_template_dir(str(template_dir))
        content, template_type, _ = load_template(app.template, "later.txt")
        assert content == "Later $value"
        assert template_type == "directory"


@pytest.mark.depends_on("test_local_plugin_loads_and_reports_name")
def test_plugin_directory_load_extends_application(tmp_path):
    plugin_name = "cement_local_integration_plugin"
    (tmp_path / f"{plugin_name}.py").write_text(
        "def load(app):\n"
        "    app.extend('integration_plugin_value', {'source': 'directory'})\n",
        encoding="utf-8",
    )
    with new_app(plugins=[plugin_name], plugin_dirs=[str(tmp_path)]) as app:
        assert app.plugin.get_loaded_plugins() == [plugin_name]
        assert app.integration_plugin_value == {"source": "directory"}


@pytest.mark.depends_on("test_local_plugin_loads_and_reports_name", "test_config_defaults_are_available_through_config_interface")
def test_enabled_plugin_from_config_is_loaded(tmp_path):
    plugin_name = "cement_configured_integration_plugin"
    (tmp_path / f"{plugin_name}.py").write_text(
        "def load(app):\n"
        "    app.extend('configured_plugin_value', 'enabled')\n",
        encoding="utf-8",
    )
    defaults = {f"plugin.{plugin_name}": {"enabled": "true"}}
    with new_app(
        label="configured-plugin-app",
        config_defaults=defaults,
        plugin_dirs=[str(tmp_path)],
    ) as app:
        assert app.plugin.get_enabled_plugins() == [plugin_name]
        assert app.plugin.get_loaded_plugins() == [plugin_name]
        assert app.config.get(f"plugin.{plugin_name}", "enabled") == "true"
        assert app.configured_plugin_value == "enabled"


@pytest.mark.depends_on("test_local_plugin_loads_and_reports_name")
def test_plugin_can_register_controller_before_dispatch(tmp_path):
    plugin_name = "cement_controller_integration_plugin"
    (tmp_path / f"{plugin_name}.py").write_text(
        "from cement import Controller, ex\n"
        "def load(app):\n"
        "    class PluginController(Controller):\n"
        "        class Meta:\n"
        "            label = 'plugin'\n"
        "            stacked_on = 'base'\n"
        "            stacked_type = 'nested'\n"
        "        @ex()\n"
        "        def status(self):\n"
        "            return {'plugin': 'ready'}\n"
        "    app.handler.register(PluginController)\n",
        encoding="utf-8",
    )
    with new_app(
        handlers=[BaseWorkflowController],
        plugins=[plugin_name],
        plugin_dirs=[str(tmp_path)],
        argv=["plugin", "status"],
    ) as app:
        assert app.run() == {"plugin": "ready"}


@pytest.mark.depends_on("test_app_extend_adds_a_public_callable")
def test_bootstrap_module_can_extend_application(tmp_path, monkeypatch):
    module_name = "cement_local_bootstrap_integration"
    (tmp_path / f"{module_name}.py").write_text(
        "def load(app):\n"
        "    app.extend('bootstrap_value', 'ready')\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    with new_app(bootstrap=module_name) as app:
        assert app.bootstrap_value == "ready"


@pytest.mark.depends_on("test_app_extend_adds_a_public_callable", "test_custom_interface_can_be_defined_at_runtime")
def test_reload_rebuilds_core_managers_and_drops_runtime_extensions():
    with new_app() as app:
        app.extend("runtime_value", "present")
        app.hook.define("runtime_hook")
        app.interface.define(MetricInterface)
        assert app.runtime_value == "present"
        assert app.hook.defined("runtime_hook")
        assert app.interface.defined("metric")
        app.reload()
        assert not hasattr(app, "runtime_value")
        assert app.hook.defined("runtime_hook") is False
        assert app.interface.defined("metric") is False
        assert app.interface.defined("output") is True


@pytest.mark.depends_on("test_framework_hook_names_are_defined")
def test_close_runs_pre_and_post_close_hooks_and_sets_code():
    events = []

    def before(app):
        events.append("before")

    def after(app):
        events.append("after")

    app = new_app(hooks=[("pre_close", before), ("post_close", after)])
    app.setup()
    app.close(7)
    assert events == ["before", "after"]
    assert app.exit_code == 7


@pytest.mark.depends_on("test_context_setup_exposes_core_interfaces", "test_framework_hook_names_are_defined")
def test_context_manager_closes_application_after_run():
    events = []

    def after(app):
        events.append("closed")

    with new_app(hooks=[("post_close", after)]) as app:
        app.run()
        assert events == []
    assert events == ["closed"]


@pytest.mark.depends_on("test_config_defaults_are_available_through_config_interface", "test_json_output_handler_returns_parseable_object")
def test_config_section_override_drives_extensions_and_output():
    defaults = {
        "custom-section": {
            "extensions": "json",
            "output_handler": "json",
        }
    }
    with new_app(
        label="different-label",
        config_section="custom-section",
        config_defaults=defaults,
    ) as app:
        rendered = app.render({"section": "custom"}, out=None)
        assert app.output.__class__.Meta.label == "json"
        assert json.loads(rendered) == {"section": "custom"}


@pytest.mark.depends_on("test_print_extension_renders_only_out_field")
def test_render_handler_argument_can_bypass_default_output():
    with new_app(extensions=["print"], output_handler="dummy") as app:
        assert app.render({"out": "selected"}, handler="print", out=None) == "selected\n"


@pytest.mark.depends_on("test_json_output_handler_returns_parseable_object")
def test_json_render_to_file_round_trips_structured_data():
    stream = io.StringIO()
    with new_app(extensions=["json"], output_handler="json") as app:
        app.render({"items": [1, 2], "active": False}, out=stream)
    assert json.loads(stream.getvalue()) == {"items": [1, 2], "active": False}


@pytest.mark.depends_on("test_config_parse_file_returns_false_for_missing_path", "test_config_parse_file_loads_local_ini")
def test_app_add_config_file_then_parse_updates_config(tmp_path):
    config_path = tmp_path / "late.conf"
    config_path.write_text("[late-app]\nvalue = added\n", encoding="utf-8")
    with new_app(label="late-app") as app:
        app.add_config_file(str(config_path))
        assert app.config.parse_file(str(config_path)) is True
        assert app.config.get("late-app", "value") == "added"


@pytest.mark.depends_on("test_template_handler_loads_file_from_template_directory", "test_template_handler_copy_creates_local_project_file")
def test_template_handler_copy_and_load_round_trip(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "message.txt").write_text("Hello $name", encoding="utf-8")
    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        app.add_template_dir(str(source))
        loaded, template_type, _ = load_template(app.template, "message.txt")
        app.template.copy(str(source), str(destination), {"name": "Ada"})
    assert loaded == "Hello $name"
    assert template_type == "directory"
    assert (destination / "message.txt").read_text(encoding="utf-8") == "Hello Ada"


@pytest.mark.depends_on("test_local_plugin_loads_and_reports_name", "test_app_extend_adds_a_public_callable")
def test_plugin_load_and_controller_dispatch_share_app_state(tmp_path):
    plugin_name = "cement_state_integration_plugin"
    (tmp_path / f"{plugin_name}.py").write_text(
        "from cement import Controller, ex\n"
        "def load(app):\n"
        "    app.extend('workflow_marker', 'from-plugin')\n"
        "    class PluginController(Controller):\n"
        "        class Meta:\n"
        "            label = 'state'\n"
        "            stacked_on = 'base'\n"
        "            stacked_type = 'nested'\n"
        "        @ex()\n"
        "        def read(self):\n"
        "            return {'marker': self.app.workflow_marker}\n"
        "    app.handler.register(PluginController)\n",
        encoding="utf-8",
    )
    with new_app(
        handlers=[BaseWorkflowController],
        plugins=[plugin_name],
        plugin_dirs=[str(tmp_path)],
        argv=["state", "read"],
    ) as app:
        assert app.run() == {"marker": "from-plugin"}


@pytest.mark.depends_on(
    "test_config_parse_file_loads_local_ini",
    "test_json_extension_registers_json_output_handler",
    "test_json_output_handler_returns_parseable_object",
    "test_hook_manager_orders_registered_callbacks_by_weight",
    "test_add_arg_populates_parsed_arguments",
)
def test_full_local_app_workflow_connects_config_controller_hook_output(tmp_path):
    config_path = tmp_path / "workflow.conf"
    config_path.write_text(
        "[workflow]\n"
        "extensions = json\n"
        "output_handler = json\n",
        encoding="utf-8",
    )

    def add_workflow_marker(app, data):
        updated = dict(data)
        updated["hooked"] = True
        return updated

    with new_app(
        label="workflow",
        config_files=[str(config_path)],
        handlers=[RenderingWorkflowController],
        hooks=[("pre_render", add_workflow_marker)],
        argv=["report", "--name", "Nia"],
    ) as app:
        result = app.run()
        assert json.loads(result) == {
            "kind": "report",
            "name": "Nia",
            "hooked": True,
        }
