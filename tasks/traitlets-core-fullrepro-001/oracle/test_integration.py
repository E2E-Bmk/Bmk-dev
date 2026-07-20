import json

import os

import textwrap

import pytest

from traitlets import (
    Any,
    Bool,
    CBool,
    CBytes,
    CFloat,
    CInt,
    CRegExp,
    CUnicode,
    Callable,
    CaselessStrEnum,
    Complex,
    Dict,
    DottedObjectName,
    Enum,
    Float,
    FuzzyEnum,
    HasTraits,
    Instance,
    Int,
    Integer,
    List,
    ObjectName,
    Set,
    TCPAddress,
    This,
    TraitError,
    Tuple,
    Type,
    Unicode,
    Union,
    Bunch,
    default,
    directional_link,
    import_item,
    link,
    observe,
    signature_has_traits,
    validate,
)

from traitlets.config import Application, Config, Configurable, MultipleInstanceError

from traitlets.config.application import boolean_flag

from traitlets.config.loader import (
    ArgumentError,
    ConfigFileNotFound,
    JSONFileConfigLoader,
    KVArgParseConfigLoader,
    LazyConfigValue,
    PyFileConfigLoader,
)

def clear_application_singletons():
    _clear_application_tree()
    yield
    _clear_application_tree()

def _clear_application_tree(cls=Application):
    cls.clear_instance()
    for subclass in cls.__subclasses__():
        _clear_application_tree(subclass)

class IntegerModel(HasTraits):
    value = Integer()

class Worker(Configurable):
    enabled = Bool(False, help="enable worker").tag(config=True)
    label = Unicode("default", help="worker label").tag(config=True)
    count = Int(0, help="worker count").tag(config=True)
    plain = Unicode("plain")

class MiniApp(Application):
    classes = [Worker]
    aliases = {"label": "Worker.label", "count": "Worker.count"}
    flags = {"enable-worker": ({"Worker": {"enabled": True}}, "enable worker")}


def test_dynamic_default_is_lazy_and_constructor_overrides_it():
    class Model(HasTraits):
        value = Int()
        calls = 0

        @default("value")
        def _default_value(self):
            self.calls += 1
            return 10

    obj = Model(value=3)
    assert obj.calls == 0
    assert obj.value == 3
    lazy = Model()
    assert lazy.trait_has_value("value") is False
    assert lazy.value == 10
    assert lazy.calls == 1

def test_observe_receives_bunch_change_and_unobserve_stops_it():
    class Model(HasTraits):
        value = Int()

    obj = Model(value=1)
    seen = []

    def handler(change):
        seen.append((change.owner, change.name, change.old, change.new, change["type"]))

    obj.observe(handler, names="value")
    obj.value = 2
    obj.value = 2
    obj.unobserve(handler, names="value")
    obj.value = 3
    assert seen == [(obj, "value", 1, 2, "change")]

def test_observe_decorator_registers_class_observer():
    class Model(HasTraits):
        value = Int()

        @observe("value")
        def _value_changed(self, change):
            self.last = (change.old, change.new)

    obj = Model(value=4)
    obj.value = 9
    assert obj.last == (4, 9)

def test_validator_transforms_value_before_storage():
    class Model(HasTraits):
        value = Int()

        @validate("value")
        def _valid_value(self, proposal):
            return proposal["value"] + 1

    obj = Model()
    obj.value = 4
    assert obj.value == 5

def test_validator_rejection_preserves_old_value():
    class Model(HasTraits):
        value = Int(1)

        @validate("value")
        def _valid_value(self, proposal):
            if proposal["value"] < 0:
                raise TraitError("invalid")
            return proposal["value"]

    obj = Model()
    with pytest.raises(TraitError):
        obj.value = -1
    assert obj.value == 1

def test_hold_trait_notifications_batches_successful_changes():
    class Model(HasTraits):
        a = Int()
        b = Int()

    obj = Model()
    seen = []
    obj.observe(lambda change: seen.append(change.name))
    with obj.hold_trait_notifications():
        obj.a = 1
        obj.b = 2
    assert obj.a == 1
    assert obj.b == 2
    assert set(seen) == {"a", "b"}

def test_hold_trait_notifications_rolls_back_on_validation_error():
    class Model(HasTraits):
        value = Int(1)

        @validate("value")
        def _valid_value(self, proposal):
            if proposal["value"] < 0:
                raise TraitError("invalid")
            return proposal["value"]

    obj = Model()
    with pytest.raises(TraitError):
        with obj.hold_trait_notifications():
            obj.value = 5
            obj.value = -1
    assert obj.value == 1

def test_bidirectional_link_synchronizes_and_unlink_detaches():
    class Model(HasTraits):
        value = Int()

    left = Model(value=1)
    right = Model(value=2)
    connector = link((left, "value"), (right, "value"))
    left.value = 5
    assert right.value == 5
    right.value = 7
    assert left.value == 7
    connector.unlink()
    left.value = 9
    assert right.value == 7

def test_directional_link_only_updates_target():
    class Model(HasTraits):
        value = Int()

    source = Model(value=1)
    target = Model(value=2)
    connector = directional_link((source, "value"), (target, "value"))
    source.value = 4
    assert target.value == 4
    target.value = 10
    assert source.value == 4
    connector.unlink()

def test_link_transform_uses_forward_and_reverse_functions():
    class Model(HasTraits):
        value = Int()

    left = Model(value=1)
    right = Model(value=0)
    connector = link((left, "value"), (right, "value"), transform=(lambda v: v + 10, lambda v: v - 10))
    left.value = 2
    assert right.value == 12
    right.value = 30
    assert left.value == 20
    connector.unlink()

def test_invalid_link_endpoint_raises_before_linking():
    class Model(HasTraits):
        value = Int()

    obj = Model()
    with pytest.raises((TypeError, ValueError, TraitError)):
        link((obj, "missing"), (obj, "value"))

def test_config_uppercase_attribute_creates_section_and_lowercase_missing_fails():
    cfg = Config()
    cfg.Worker.name = "alpha"
    assert cfg["Worker"]["name"] == "alpha"
    cfg["Worker"]["count"] = 3
    assert cfg.Worker.count == 3

def test_config_merge_overrides_scalars_and_preserves_nested_values():
    base = Config({"Worker": {"name": "base", "count": 1}})
    other = Config({"Worker": {"name": "other", "enabled": True}})
    base.merge(other)
    assert base.Worker.name == "other"
    assert base.Worker.count == 1
    assert base.Worker.enabled is True

def test_config_collisions_reports_conflicting_values():
    left = Config({"Worker": {"name": "left"}})
    right = Config({"Worker": {"name": "right"}})
    collisions = left.collisions(right)
    assert "Worker" in collisions
    assert collisions["Worker"]

def test_lazy_config_value_applies_container_updates():
    lazy = LazyConfigValue()
    lazy.append("tail")
    lazy.prepend(["head"])
    assert lazy.get_value(["middle"]) == ["head", "middle", "tail"]
    mapping = LazyConfigValue()
    mapping.update({"a": 1})
    assert mapping.get_value({"b": 2}) == {"a": 1, "b": 2}

def test_json_config_loader_reads_public_config_values(tmp_path):
    path = tmp_path / "sample.json"
    path.write_text(json.dumps({"Worker": {"name": "json"}}), encoding="utf-8")
    cfg = JSONFileConfigLoader(str(path)).load_config()
    assert cfg.Worker.name == "json"

def test_py_config_loader_uses_get_config_object(tmp_path):
    path = tmp_path / "sample.py"
    path.write_text("c = get_config()\nc.Worker.name = 'python'\n", encoding="utf-8")
    cfg = PyFileConfigLoader(str(path)).load_config()
    assert cfg.Worker.name == "python"

def test_missing_required_config_file_raises(tmp_path):
    loader = JSONFileConfigLoader("missing.json", path=str(tmp_path))
    with pytest.raises(ConfigFileNotFound):
        loader.load_config()

def test_configurable_loads_tagged_traits_from_matching_section():
    cfg = Config({"Worker": {"label": "configured", "enabled": True}})
    worker = Worker(config=cfg)
    assert worker.label == "configured"
    assert worker.enabled is True

def test_configurable_constructor_keyword_overrides_config_value():
    cfg = Config({"Worker": {"label": "configured"}})
    worker = Worker(config=cfg, label="kw")
    assert worker.label == "kw"

def test_update_config_changes_existing_configurable_trait():
    worker = Worker()
    worker.update_config(Config({"Worker": {"count": 7}}))
    assert worker.count == 7

def test_configurable_base_section_applies_to_subclass_and_specific_overrides():
    class SpecialWorker(Worker):
        pass

    cfg = Config({"Worker": {"label": "base"}, "SpecialWorker": {"label": "special"}})
    worker = SpecialWorker(config=cfg)
    assert worker.label == "special"

def test_singleton_configurable_instance_lifecycle():
    class Single(Application):
        pass

    Single.clear_instance()
    first = Single.instance()
    assert Single.initialized() is True
    assert Single.instance() is first
    class Sibling(Application):
        pass

    with pytest.raises(MultipleInstanceError):
        Sibling.instance()
    Single.clear_instance()
    Sibling.clear_instance()
    assert Single.initialized() is False

def test_logging_configurable_has_public_logger_trait():
    from traitlets.config import LoggingConfigurable

    configurable = LoggingConfigurable()
    assert hasattr(configurable.log, "warning")

def test_application_cli_alias_and_flag_populate_config():
    MiniApp.clear_instance()
    app = MiniApp.instance()
    app.initialize(["--label=cli", "--count=5", "--enable-worker"])
    worker = Worker(config=app.config)
    assert worker.label == "cli"
    assert worker.count == 5
    assert worker.enabled is True
    MiniApp.clear_instance()

def test_application_cli_overrides_loaded_config_file(tmp_path):
    class FileApp(MiniApp):
        pass

    FileApp.clear_instance()
    (tmp_path / "fileapp_config.py").write_text("c = get_config()\nc.Worker.label = 'file'\n", encoding="utf-8")
    app = FileApp.instance()
    app.initialize(["--label=cli"])
    app.load_config_file("fileapp_config", path=[str(tmp_path)])
    worker = Worker(config=app.config)
    assert worker.label == "cli"
    FileApp.clear_instance()

def test_application_json_overrides_python_same_base(tmp_path):
    class FileApp(Application):
        classes = [Worker]

    FileApp.clear_instance()
    (tmp_path / "fileapp_config.py").write_text("c = get_config()\nc.Worker.label = 'python'\n", encoding="utf-8")
    (tmp_path / "fileapp_config.json").write_text(json.dumps({"Worker": {"label": "json"}}), encoding="utf-8")
    app = FileApp.instance()
    app.load_config_file("fileapp_config", path=[str(tmp_path)])
    worker = Worker(config=app.config)
    assert worker.label == "json"
    assert any(name.endswith("fileapp_config.py") for name in app.loaded_config_files)
    assert any(name.endswith("fileapp_config.json") for name in app.loaded_config_files)
    FileApp.clear_instance()

def test_application_path_priority_prefers_earlier_directory(tmp_path):
    class FileApp(Application):
        classes = [Worker]

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "fileapp_config.py").write_text("c = get_config()\nc.Worker.label = 'first'\n", encoding="utf-8")
    (second / "fileapp_config.py").write_text("c = get_config()\nc.Worker.label = 'second'\n", encoding="utf-8")
    FileApp.clear_instance()
    app = FileApp.instance()
    app.load_config_file("fileapp_config", path=[str(first), str(second)])
    assert Worker(config=app.config).label == "first"
    FileApp.clear_instance()

def test_repeated_scalar_cli_option_raises():
    class ScalarApp(MiniApp):
        pass

    ScalarApp.clear_instance()
    app = ScalarApp.instance()
    with pytest.raises((ArgumentError, SystemExit, TraitError)):
        app.initialize(["--label=a", "--label=b"])
    ScalarApp.clear_instance()

def test_repeated_list_and_dict_cli_values_accumulate():
    class ContainerWorker(Configurable):
        items = List(Unicode()).tag(config=True)
        mapping = Dict(value_trait=Unicode()).tag(config=True)

    loader = KVArgParseConfigLoader(
        [
            "--ContainerWorker.items=one",
            "--ContainerWorker.items=two",
            "--ContainerWorker.mapping=a=1",
            "--ContainerWorker.mapping=b=2",
        ],
        classes=[ContainerWorker],
    )
    cfg = loader.load_config()
    worker = ContainerWorker(config=cfg)
    assert worker.items == ["one", "two"]
    assert worker.mapping == {"a": "1", "b": "2"}

def test_boolean_flag_definitions_set_true_and_false():
    flags = boolean_flag("feature", "Worker.enabled", "on", "off")
    assert flags["feature"][0]["Worker"]["enabled"] is True
    assert flags["no-feature"][0]["Worker"]["enabled"] is False

def test_subcommand_instantiates_and_initializes_child_app():
    class Child(Application):
        initialized_with = List(Unicode())

        def initialize(self, argv=None):
            self.initialized_with = list(argv or [])

    class Parent(Application):
        subcommands = {"child": (Child, "child help")}

    Parent.clear_instance()
    parent = Parent.instance()
    parent.initialize(["child", "arg1", "arg2"])
    assert isinstance(parent.subapp, Child)
    assert parent.subapp.initialized_with == ["arg1", "arg2"]
    Parent.clear_instance()

def test_show_config_json_prints_current_config_and_stops_work(capsys):
    class ShowApp(MiniApp):
        def start(self):
            super().start()

    ShowApp.clear_instance()
    app = ShowApp.instance()
    app.initialize(["--label=shown"])
    app.show_config_json = True
    app.start()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["Worker"]["label"] == "shown"
    ShowApp.clear_instance()

def test_cross_view_assignment_observer_and_trait_values_agree():
    class Model(HasTraits):
        value = Int()

    obj = Model(value=1)
    seen = []
    obj.observe(lambda change: seen.append(change.new), names="value")
    obj.value = 6
    assert getattr(obj, "value") == 6
    assert obj.trait_values()["value"] == 6
    assert seen == [6]

def test_cross_view_constructor_override_does_not_call_default():
    class Model(HasTraits):
        value = Int()
        calls = Int(0)

        @default("value")
        def _default_value(self):
            self.calls += 1
            return 99

    obj = Model(value=4)
    assert obj.value == 4
    assert obj.trait_values()["value"] == 4
    assert obj.calls == 0

def test_cross_view_metadata_visible_in_traits_and_help_section():
    section = Worker.class_config_section()
    assert Worker.class_traits(config=True)["label"].metadata["config"] is True
    assert Worker().trait_metadata("label", "help") == "worker label"
    assert "label" in section

def test_cross_view_rejected_validator_value_absent_from_notifications_and_links():
    class Model(HasTraits):
        value = Int(1)

        @validate("value")
        def _valid_value(self, proposal):
            if proposal["value"] < 0:
                raise TraitError("invalid")
            return proposal["value"]

    source = Model()
    target = Model()
    seen = []
    target.observe(lambda change: seen.append(change.new), names="value")
    connector = directional_link((source, "value"), (target, "value"))
    with pytest.raises(TraitError):
        source.value = -5
    assert source.value == 1
    assert target.value == 1
    assert seen == []
    connector.unlink()

def test_cross_view_validator_transform_observer_and_link_agree():
    class Source(HasTraits):
        value = Int()

        @validate("value")
        def _valid_value(self, proposal):
            return proposal["value"] + 1

    class Target(HasTraits):
        value = Int()

    source = Source()
    target = Target()
    seen = []
    source.observe(lambda change: seen.append(change.new), names="value")
    connector = directional_link((source, "value"), (target, "value"))
    source.value = 10
    assert source.value == 11
    assert seen == [11]
    assert target.value == 11
    connector.unlink()

def test_cross_view_config_dict_attribute_and_configurable_agree():
    cfg = Config()
    cfg.Worker.label = "same"
    assert cfg["Worker"]["label"] == "same"
    assert Worker(config=cfg).label == "same"

def test_cross_view_application_cli_overrides_file_for_configurable(tmp_path):
    class FileApp(MiniApp):
        pass

    FileApp.clear_instance()
    (tmp_path / "fileapp_config.py").write_text("c = get_config()\nc.Worker.label = 'file'\n", encoding="utf-8")
    app = FileApp.instance()
    app.initialize(["--label=cli"])
    app.load_config_file("fileapp_config", path=[str(tmp_path)])
    assert Worker(config=app.config).label == "cli"
    FileApp.clear_instance()

def test_workflow_trait_object_defaults_validation_and_observation():
    class Account(HasTraits):
        name = Unicode()
        balance = Int()

        @default("name")
        def _default_name(self):
            return "guest"

        @validate("balance")
        def _valid_balance(self, proposal):
            if proposal["value"] < 0:
                raise TraitError("invalid")
            return proposal["value"]

        @observe("balance")
        def _balance_changed(self, change):
            self.last_change = (change.old, change.new)

    account = Account(balance=5)
    assert account.name == "guest"
    account.balance = 7
    assert account.last_change == (5, 7)
    with pytest.raises(TraitError):
        account.balance = -1
    assert account.balance == 7

def test_workflow_trait_object_constructor_override_and_rejection_state():
    class Account(HasTraits):
        name = Unicode()
        balance = Int()
        default_calls = Int(0)

        @default("name")
        def _default_name(self):
            self.default_calls += 1
            return "guest"

        @validate("balance")
        def _valid_balance(self, proposal):
            if proposal["value"] < 0:
                raise TraitError("invalid")
            return proposal["value"]

    account = Account(name="alice", balance=1)
    assert account.name == "alice"
    assert account.default_calls == 0
    with pytest.raises(TraitError):
        account.balance = -10
    assert account.trait_values()["balance"] == 1

def test_workflow_trait_object_validation_notification_success_path():
    class Account(HasTraits):
        balance = Int()

        @validate("balance")
        def _valid_balance(self, proposal):
            return proposal["value"] * 2

    account = Account(balance=2)
    seen = []
    account.observe(lambda change: seen.append(change.new), names="balance")
    account.balance = 3
    assert account.balance == 6
    assert seen == [6]

def test_workflow_configurable_application_alias_flag_and_worker_state():
    MiniApp.clear_instance()
    app = MiniApp.instance()
    app.initialize(["--label=cli", "--enable-worker"])
    worker = Worker(config=app.config)
    assert worker.label == "cli"
    assert worker.enabled is True
    MiniApp.clear_instance()

def test_workflow_configurable_application_file_then_cli_priority(tmp_path):
    class FileApp(MiniApp):
        pass

    FileApp.clear_instance()
    (tmp_path / "fileapp_config.py").write_text("c = get_config()\nc.Worker.label = 'file'\n", encoding="utf-8")
    app = FileApp.instance()
    app.initialize(["--label=cli"])
    app.load_config_file("fileapp_config", path=[str(tmp_path)])
    assert Worker(config=app.config).label == "cli"
    FileApp.clear_instance()

def test_workflow_configurable_application_flag_can_be_disabled():
    class BoolApp(Application):
        classes = [Worker]
        flags = boolean_flag("worker", "Worker.enabled")

    BoolApp.clear_instance()
    app = BoolApp.instance()
    app.initialize(["--worker", "--no-worker"])
    assert Worker(config=app.config).enabled is False
    BoolApp.clear_instance()
