from __future__ import annotations

import json
from pathlib import Path

import pytest

from cement.core.exc import FrameworkError, InterfaceError
from support import (
    AlternateMetricHandler,
    DollarTemplateHandler,
    MetricHandler,
    MetricInterface,
    ReplacementMetricHandler,
    load_template,
    new_app,
)


def test_testapp_accepts_explicit_label():
    with new_app(label="explicit-app") as app:
        assert app.label == "explicit-app"


def test_testapp_preserves_explicit_argv():
    with new_app(argv=["--debug"]) as app:
        assert app.argv == ["--debug"]


def test_debug_property_follows_debug_argument():
    with new_app(argv=["--debug"]) as app:
        assert app.debug is True


def test_quiet_property_follows_quiet_argument():
    with new_app(argv=["--quiet"]) as app:
        assert app.quiet is True


def test_add_arg_populates_parsed_arguments():
    with new_app(argv=["--color", "blue"]) as app:
        app.add_arg("--color", choices=["blue", "green"], default="green")
        app.run()
        assert app.pargs.color == "blue"


def test_context_setup_exposes_core_interfaces():
    with new_app() as app:
        assert app.interface.defined("config")
        assert app.interface.defined("argument")
        assert app.interface.defined("controller")
        assert app.interface.defined("output")


def test_context_setup_instantiates_default_handlers():
    with new_app() as app:
        assert app.config is not None
        assert app.args is not None
        assert app.output is not None
        assert app.controller is not None


def test_config_defaults_are_available_through_config_interface():
    defaults = {"config-app": {"answer": "forty-two"}}
    with new_app(label="config-app", config_defaults=defaults) as app:
        assert app.config.get("config-app", "answer") == "forty-two"


def test_config_merge_without_override_keeps_existing_value():
    with new_app(label="merge-app", config_defaults={"merge-app": {"mode": "initial"}}) as app:
        app.config.merge({"merge-app": {"mode": "replacement"}}, override=False)
        assert app.config.get("merge-app", "mode") == "initial"


def test_config_merge_with_override_replaces_value():
    with new_app(label="merge-app", config_defaults={"merge-app": {"mode": "initial"}}) as app:
        app.config.merge({"merge-app": {"mode": "replacement"}}, override=True)
        assert app.config.get("merge-app", "mode") == "replacement"


def test_config_manager_exposes_sections_and_dict():
    defaults = {"config-app": {"answer": "forty-two", "mode": "local"}}
    with new_app(label="config-app", config_defaults=defaults) as app:
        assert "config-app" in app.config.get_sections()
        assert app.config.keys("config-app") == ["answer", "mode"]
        assert app.config.get_section_dict("config-app") == defaults["config-app"]
        assert app.config.get_dict()["config-app"] == defaults["config-app"]


def test_config_parse_file_returns_false_for_missing_path(tmp_path):
    with new_app(label="parse-app") as app:
        assert app.config.parse_file(str(tmp_path / "missing.conf")) is False


def test_config_parse_file_loads_local_ini(tmp_path):
    config_path = tmp_path / "local.conf"
    config_path.write_text("[parse-app]\ncolor = blue\n", encoding="utf-8")
    with new_app(label="parse-app") as app:
        assert app.config.parse_file(str(config_path)) is True
        assert app.config.get("parse-app", "color") == "blue"


def test_interface_manager_reports_defined_and_fallback():
    with new_app() as app:
        assert app.interface.defined("output") is True
        assert app.interface.get("missing", "fallback") == "fallback"


def test_interface_manager_lists_core_interfaces():
    with new_app() as app:
        names = app.interface.list()
        assert {"config", "argument", "controller", "output", "template"} <= set(names)


def test_custom_interface_can_be_defined_at_runtime():
    with new_app() as app:
        app.interface.define(MetricInterface)
        assert app.interface.defined("metric") is True
        assert app.interface.get("metric") is MetricInterface


def test_handler_registered_in_app_metadata_is_visible():
    with new_app(interfaces=[MetricInterface], handlers=[MetricHandler]) as app:
        assert app.handler.registered("metric", "basic") is True


def test_handler_get_returns_registered_class():
    with new_app(interfaces=[MetricInterface], handlers=[MetricHandler]) as app:
        assert app.handler.get("metric", "basic") is MetricHandler


def test_handler_list_returns_classes_for_interface():
    with new_app(
        interfaces=[MetricInterface],
        handlers=[MetricHandler, AlternateMetricHandler],
    ) as app:
        labels = {handler.Meta.label for handler in app.handler.list("metric")}
        assert labels == {"basic", "alternate"}


def test_handler_resolve_label_creates_instance():
    with new_app(interfaces=[MetricInterface], handlers=[MetricHandler]) as app:
        handler = app.handler.resolve("metric", "basic", setup=True)
        assert isinstance(handler, MetricHandler)
        assert handler.describe().endswith(":basic")


def test_handler_resolve_class_registers_and_creates_instance():
    with new_app(interfaces=[MetricInterface]) as app:
        handler = app.handler.resolve("metric", MetricHandler, setup=True)
        assert isinstance(handler, MetricHandler)
        assert app.handler.registered("metric", "basic")


def test_handler_get_uses_fallback_for_unknown_label():
    fallback = object()
    with new_app(interfaces=[MetricInterface], handlers=[MetricHandler]) as app:
        assert app.handler.get("metric", "unknown", fallback=fallback) is fallback


def test_handler_manager_rejects_unknown_interface():
    with new_app() as app:
        with pytest.raises(InterfaceError):
            app.handler.get("missing", "handler")


def test_handler_force_replaces_same_label():
    with new_app(interfaces=[MetricInterface], handlers=[MetricHandler]) as app:
        app.handler.register(ReplacementMetricHandler, force=True)
        resolved = app.handler.resolve("metric", "basic", setup=True)
        assert isinstance(resolved, ReplacementMetricHandler)


def test_hook_manager_orders_registered_callbacks_by_weight():
    events = []

    def low():
        events.append("low")
        return "low"

    def high():
        events.append("high")
        return "high"

    with new_app() as app:
        app.hook.define("ordered")
        assert app.hook.register("ordered", high, weight=10)
        assert app.hook.register("ordered", low, weight=-10)
        assert list(app.hook.run("ordered")) == ["low", "high"]
        assert events == ["low", "high"]


def test_hook_manager_flattens_generator_results():
    def generated():
        yield "first"
        yield "second"

    with new_app() as app:
        app.hook.define("generated")
        app.hook.register("generated", generated)
        assert list(app.hook.run("generated")) == ["first", "second"]


def test_hook_registration_for_unknown_name_returns_false():
    def callback():
        return "ignored"

    with new_app() as app:
        assert app.hook.register("missing", callback) is False


def test_framework_hook_names_are_defined():
    with new_app() as app:
        assert {
            "pre_setup",
            "post_setup",
            "pre_run",
            "post_run",
            "pre_argument_parsing",
            "post_argument_parsing",
            "pre_close",
            "post_close",
            "pre_render",
            "post_render",
        } <= set(app.hook.list())


def test_extension_loader_expands_short_names():
    with new_app() as app:
        app.ext.load_extension("json")
        assert "cement.ext.ext_json" in app.ext.get_loaded_extensions()


def test_extension_loader_skips_duplicate_full_names():
    with new_app() as app:
        app.ext.load_extension("json")
        loaded = list(app.ext.get_loaded_extensions())
        app.ext.load_extension("cement.ext.ext_json")
        assert app.ext.get_loaded_extensions() == loaded


def test_json_extension_registers_json_output_handler():
    with new_app(extensions=["json"]) as app:
        assert app.handler.registered("output", "json") is True
        assert app.handler.registered("config", "json") is True


def test_json_output_handler_returns_parseable_object():
    with new_app(extensions=["json"], output_handler="json") as app:
        rendered = app.render({"active": True, "count": 3}, out=None)
        assert json.loads(rendered) == {"active": True, "count": 3}


def test_print_extension_renders_only_out_field():
    with new_app(extensions=["print"]) as app:
        rendered = app.render({"out": "hello", "ignored": "value"}, handler="print", out=None)
        assert rendered == "hello\n"


def test_render_without_output_handler_returns_empty_string():
    with new_app(output_handler=None) as app:
        assert app.render({"ignored": True}, out=None) == ""


def test_last_rendered_records_data_and_text():
    with new_app(extensions=["json"], output_handler="json") as app:
        data = {"name": "Nia"}
        text = app.render(data, out=None)
        assert app.last_rendered == (data, text)


def test_app_extend_adds_a_public_callable():
    def marker(value):
        return f"marked:{value}"

    with new_app() as app:
        app.extend("marker", marker)
        assert app.marker("value") == "marked:value"


def test_template_handler_renders_scalar_placeholders():
    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        assert app.template.render("Hello $name", {"name": "Nia"}) == "Hello Nia"


def test_template_handler_loads_file_from_template_directory(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_path = template_dir / "hello.txt"
    template_path.write_text("Hello $name", encoding="utf-8")

    with new_app(
        template_handler="dollar",
        handlers=[DollarTemplateHandler],
        template_dirs=[str(template_dir)],
    ) as app:
        content, template_type, loaded_path = load_template(app.template, "hello.txt")
        assert content == "Hello $name"
        assert template_type == "directory"
        assert Path(loaded_path).name == "hello.txt"


def test_template_handler_copy_creates_local_project_file(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "README-$project.txt").write_text("Project: $project", encoding="utf-8")

    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        assert app.template.copy(str(source), str(destination), {"project": "cement"}) is True
    output = destination / "README-cement.txt"
    assert output.read_text(encoding="utf-8") == "Project: cement"


def test_template_handler_rejects_missing_template():
    with new_app(template_handler="dollar", handlers=[DollarTemplateHandler]) as app:
        with pytest.raises(FrameworkError):
            app.template.load("missing.txt")


def test_local_plugin_loads_and_reports_name(tmp_path):
    plugin_name = "cement_local_atomic_plugin"
    (tmp_path / f"{plugin_name}.py").write_text(
        "def load(app):\n"
        "    app.extend('atomic_plugin_marker', 'loaded')\n",
        encoding="utf-8",
    )
    with new_app(plugins=[plugin_name], plugin_dirs=[str(tmp_path)]) as app:
        assert app.plugin.get_loaded_plugins() == [plugin_name]
        assert app.atomic_plugin_marker == "loaded"


def test_missing_local_plugin_raises_framework_error(tmp_path):
    with pytest.raises(FrameworkError):
        with new_app(plugins=["does_not_exist"], plugin_dirs=[str(tmp_path)]):
            pass
