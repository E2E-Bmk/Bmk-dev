"""Root-balanced public behavior suite for the attrs v2 draft gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Root:
    root_id: str
    level: str
    designation: str
    behavior: str
    function: Callable[[], None]


def raises(error, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except error as exc:
        return exc
    except Exception as exc:
        raise AssertionError(f"expected {error.__name__}, got {type(exc).__name__}") from exc
    raise AssertionError(f"expected {error.__name__}")


def _native_atomic_01():
    import attrs

    required = {"define", "field", "fields", "evolve", "asdict", "astuple", "make_class", "validators", "setters"}
    assert required.issubset(set(attrs.__all__))


def _native_atomic_02():
    import attrs

    @attrs.define
    class Credential:
        _secret: str = attrs.field(alias="token")

    value = Credential(token="x")
    item = attrs.fields(Credential)[0]
    assert (item.name, item.alias, value._secret) == ("_secret", "token", "x")


def _native_atomic_03():
    import attrs

    @attrs.define
    class Base:
        base: int

    @attrs.define
    class Child(Base):
        child: str = attrs.field(kw_only=True)

    value = Child(2, child="c")
    assert [item.name for item in attrs.fields(Child)] == ["base", "child"]
    assert attrs.asdict(value) == {"base": 2, "child": "c"}


def _native_atomic_04():
    import attrs

    events = []

    def factory():
        events.append("default")
        return " 4 "

    def convert(value):
        events.append("converter")
        return int(value)

    def validate(instance, attribute, value):
        events.append("validator")
        assert attribute.name == "amount" and value == 4

    @attrs.define
    class Item:
        amount: int = attrs.field(factory=factory, converter=convert, validator=validate)

    assert Item().amount == 4
    assert events == ["default", "converter", "validator"]


def _native_atomic_05():
    import attrs

    @attrs.define
    class Item:
        amount: int = attrs.field(converter=int, validator=attrs.validators.ge(0))

    item = Item(1)
    item.amount = "5"
    assert item.amount == 5
    raises(ValueError, setattr, item, "amount", "-1")
    assert item.amount == 5


def _native_atomic_06():
    import attrs

    @attrs.define
    class Item:
        _name: str = attrs.field(alias="label", converter=str.upper)

    first = Item(label="a")
    second = attrs.evolve(first, label="b")
    assert (first._name, second._name) == ("A", "B")


def _native_atomic_07():
    import attrs

    @attrs.define
    class Leaf:
        value: int

    @attrs.define
    class Tree:
        leaves: tuple[Leaf, ...]

    tree = Tree((Leaf(1), Leaf(2)))
    assert attrs.asdict(tree) == {"leaves": ({"value": 1}, {"value": 2})}


def _native_atomic_08():
    import attrs

    @attrs.define
    class Pair:
        left: int
        right: str

    assert attrs.astuple(Pair(1, "r")) == (1, "r")


def _native_atomic_09():
    import attrs

    Dynamic = attrs.make_class("DynamicNative", {"count": attrs.field(converter=int)})
    value = Dynamic("7")
    assert attrs.has(Dynamic) and attrs.fields_dict(Dynamic)["count"].name == "count" and value.count == 7


def _native_atomic_10():
    import attrs

    @attrs.frozen
    class Frozen:
        value: int

    item = Frozen(1)
    raises(attrs.exceptions.FrozenInstanceError, setattr, item, "value", 2)
    assert item.value == 1


def _native_atomic_11():
    import attrs

    marker = object()

    @attrs.define
    class Meta:
        value: int = attrs.field(metadata={"marker": marker})

    attribute = attrs.fields(Meta).value
    assert attribute.metadata["marker"] is marker
    def mutate_metadata():
        attribute.metadata["x"] = 1
    raises(TypeError, mutate_metadata)


def _native_atomic_12():
    import attrs

    events = []

    def first(instance, attribute, value):
        events.append(("first", attribute.name, value))
        return value + 1

    def second(instance, attribute, value):
        events.append(("second", attribute.name, value))
        return value * 2

    @attrs.define(on_setattr=[first, second])
    class Item:
        value: int

    item = Item(1)
    item.value = 3
    assert item.value == 8 and events == [("first", "value", 3), ("second", "value", 4)]


def _native_integration_01():
    import attrs

    @attrs.define
    class Base:
        _code: int = attrs.field(alias="token", converter=int)

    Dynamic = attrs.make_class("DynamicNativeChild", {"label": attrs.field(kw_only=True)}, bases=(Base,))
    first = Dynamic(token="3", label="x")
    second = attrs.evolve(first, token="4", label="y")
    assert [item.name for item in attrs.fields(Dynamic)] == ["_code", "label"]
    assert attrs.asdict(second) == {"_code": 4, "label": "y"}
    assert attrs.astuple(second) == (4, "y") and first._code == 3


def _native_integration_02():
    import attrs

    events = []

    def factory():
        events.append("factory")
        return " 6 "

    def converter(value):
        events.append("converter")
        return int(value)

    def validator(instance, attribute, value):
        events.append("validator")
        assert value > 0

    @attrs.define
    class Item:
        amount: int = attrs.field(factory=factory, converter=converter, validator=validator)

        def __attrs_pre_init__(self):
            events.append("pre")

        def __attrs_post_init__(self):
            events.append("post")

    first = Item()
    second = attrs.evolve(first, amount="8")
    assert attrs.asdict(second) == {"amount": 8}
    assert events == ["pre", "factory", "converter", "validator", "post", "pre", "converter", "validator", "post"]


def _mutation_atomic_01():
    import attrs.workspace as aw

    required = {
        "WorkspaceError", "SchemaConflict", "RevisionConflict", "MigrationError", "SnapshotError",
        "AuditError", "LifecycleStage", "FieldRecord", "SchemaRecord", "StateViews", "InstanceSnapshot",
        "AuditEntry", "OperationReceipt", "MigrationStep", "WorkspaceSnapshot", "SchemaWorkspace",
    }
    assert required == set(aw.__all__)
    workspace = aw.SchemaWorkspace("atomic")
    assert workspace.registry_id == "atomic" and workspace.generation == 0


def _mutation_atomic_02():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Item:
        value: int

    workspace = SchemaWorkspace("registry")
    record = workspace.register("item", 1, Item)
    assert record.fields[0].identity == "item:value"
    assert len(record.digest) == 64 and record.digest == record.digest.lower()
    assert workspace.generation == 1 and workspace.record("item") == record


def _mutation_atomic_03():
    import attrs
    from attrs.workspace import RevisionConflict, SchemaWorkspace

    @attrs.define
    class Item:
        value: int

    workspace = SchemaWorkspace("registry")
    workspace.register("item", 1, Item, expected_generation=0)
    error = raises(RevisionConflict, workspace.register, "other", 1, Item, expected_generation=0)
    assert (error.expected, error.actual, workspace.generation) == (0, 1, 1)


def _mutation_atomic_04():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Item:
        _value: int = attrs.field(alias="amount", converter=int, validator=attrs.validators.gt(0))

    workspace = SchemaWorkspace("registry")
    record = workspace.register(
        "item", 1, Item, aliases={"legacy": "_value"},
        provenance={"_value": {"converter": "parse-int", "validator": "positive"}},
    )
    item = workspace.construct("item", 1, {"legacy": "5"})
    assert item._value == 5
    assert record.fields[0].aliases == ("_value", "amount", "legacy")
    assert [(stage.kind, stage.provenance) for stage in record.fields[0].lifecycle] == [("converter", "parse-int"), ("validator", "positive")]


def _register_renamed_pair():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class V1:
        old_name: int = attrs.field(converter=int)

    @attrs.define
    class V2:
        new_name: int = attrs.field(alias="current", converter=int)

    workspace = SchemaWorkspace("pair")
    first = workspace.register("entity", 1, V1, aliases={"legacy": "old_name"})
    second = workspace.register(
        "entity", 2, V2,
        field_ids={"new_name": first.fields[0].identity},
        aliases={"historic": "new_name"},
    )
    return workspace, V1, V2, first, second


def _mutation_integration_01():
    workspace, V1, V2, first, second = _register_renamed_pair()
    assert first.fields[0].identity == second.fields[0].identity
    assert set(second.fields[0].aliases) == {"new_name", "current", "old_name", "legacy", "historic"}
    assert workspace.construct("entity", 2, {"legacy": "9"}).new_name == 9


def _mutation_integration_02():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Base:
        _key: int = attrs.field(alias="token", converter=int)

    @attrs.define
    class Child(Base):
        label: str = attrs.field(kw_only=True)

    workspace = SchemaWorkspace("inheritance")
    record = workspace.register("child", 1, Child, aliases={"legacy_token": "_key"})
    item = workspace.construct("child", 1, {"legacy_token": "4", "label": "x"})
    view = workspace.views(item, "child", 1)
    assert [field.name for field in record.fields] == ["_key", "label"]
    assert view.stored == {"_key": 4, "label": "x"}
    assert view.initializer == {"token": 4, "label": "x"}


def _mutation_integration_03():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Base:
        base: int

    Dynamic = attrs.make_class("DynamicWorkspace", {"value": attrs.field(converter=int)}, bases=(Base,))
    workspace = SchemaWorkspace("dynamic")
    record = workspace.register("dynamic", 1, Dynamic, aliases={"amount": "value"})
    item = workspace.construct("dynamic", 1, {"base": 1, "amount": "7"})
    evolved = workspace.evolve(item, "dynamic", 1, {"amount": "8"})
    assert attrs.asdict(evolved) == {"base": 1, "value": 8}
    assert set(workspace.views(evolved, "dynamic", 1).serialized) == {field.identity for field in record.fields}


def _mutation_integration_04():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Item:
        count: int = attrs.field(default="2", converter=int, validator=attrs.validators.ge(0))

    workspace = SchemaWorkspace("lifecycle")
    record = workspace.register(
        "item", 1, Item,
        provenance={"count": {"default": "seed", "converter": "parse", "validator": "nonnegative"}},
    )
    stages = record.fields[0].lifecycle
    assert [stage.kind for stage in stages] == ["default", "converter", "validator"]
    assert [stage.provenance for stage in stages] == ["seed", "parse", "nonnegative"]
    assert workspace.construct("item", 1, {}).count == 2


def _mutation_integration_05():
    import attrs
    from attrs.workspace import SchemaWorkspace

    events = []

    def factory(): events.append("default"); return "3"
    def converter(value): events.append("converter"); return int(value)
    def validator(instance, attribute, value): events.append("validator"); assert value > 0

    @attrs.define
    class Item:
        value: int = attrs.field(factory=factory, converter=converter, validator=validator)

    workspace = SchemaWorkspace("native-life")
    workspace.register("item", 1, Item)
    item = workspace.construct("item", 1, {})
    assert item.value == 3 and events == ["default", "converter", "validator"]
    assert [stage.kind for stage in workspace.record("item").fields[0].lifecycle] == ["default", "converter", "validator"]


def _mutation_integration_06():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Pair:
        left: int = attrs.field(converter=int)
        right: int = attrs.field(converter=int, validator=attrs.validators.ge(0))

    workspace = SchemaWorkspace("assign-rollback")
    workspace.register("pair", 1, Pair)
    pair = Pair(1, 2)
    generation = workspace.generation
    raises(ValueError, workspace.assign, "bad", pair, "pair", 1, {"left": "9", "right": "-1"})
    assert (pair.left, pair.right, workspace.generation, len(workspace.audit())) == (1, 2, generation, 1)


def _mutation_integration_07():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Item:
        _amount: int = attrs.field(alias="value", converter=int)

    workspace = SchemaWorkspace("assign-views")
    record = workspace.register("item", 1, Item, aliases={"legacy": "_amount"})
    item = workspace.construct("item", 1, {"value": "2"})
    receipt = workspace.assign("set-1", item, "item", 1, {"legacy": "6"})
    views = workspace.views(item, "item", 1)
    identity = record.fields[0].identity
    assert receipt.kind == "assign" and receipt.generation == 2
    assert views.stored == {"_amount": 6} and views.initializer == {"value": 6} and views.serialized == {identity: 6}


def _mutation_integration_08():
    workspace, V1, V2, first, second = _register_renamed_pair()
    original = workspace.construct("entity", 2, {"current": "3"})
    evolved = workspace.evolve(original, "entity", 2, {"legacy": "8"})
    assert original.new_name == 3 and evolved.new_name == 8
    assert workspace.capture(evolved, "entity", 2).values == {second.fields[0].identity: 8}


def _mutation_integration_09():
    workspace, V1, V2, first, second = _register_renamed_pair()
    original = workspace.construct("entity", 1, {"old_name": "4"})
    migrated, receipt = workspace.migrate("move", original, "entity", 1, 2)
    assert isinstance(migrated, V2) and migrated.new_name == 4 and original.old_name == 4
    assert receipt.kind == "migrate" and receipt.generation == 3
    assert set(workspace.capture(migrated, "entity", 2).values) == {first.fields[0].identity}


def _mutation_integration_10():
    import attrs
    from attrs.workspace import MigrationError, SchemaWorkspace

    @attrs.define
    class V1:
        value: int

    @attrs.define
    class V2:
        value: int = attrs.field(validator=attrs.validators.ge(0))

    workspace = SchemaWorkspace("migration-fail")
    workspace.register("item", 1, V1)
    workspace.register("item", 2, V2)
    original = V1(-1)
    generation = workspace.generation
    error = raises(MigrationError, workspace.migrate, "bad-move", original, "item", 1, 2)
    assert isinstance(error.cause, ValueError) and original.value == -1
    assert workspace.generation == generation and len(workspace.audit()) == 2


def _mutation_integration_11():
    import attrs
    from attrs.workspace import MigrationError, MigrationStep, SchemaWorkspace

    @attrs.define
    class V1: value: int
    @attrs.define
    class V2: value: int

    events = []
    def apply_one(values): values["value"] += 1; return values
    def apply_two(values): values["value"] *= 2; return values
    def fail(values): raise RuntimeError("stop")
    def compensate_one(values, error): events.append(("one", values["value"], type(error).__name__))
    def compensate_two(values, error): events.append(("two", values["value"], type(error).__name__))

    workspace = SchemaWorkspace("compensate")
    workspace.register("item", 1, V1)
    workspace.register("item", 2, V2)
    steps = (MigrationStep("one", apply_one, compensate_one), MigrationStep("two", apply_two, compensate_two), MigrationStep("fail", fail))
    raises(MigrationError, workspace.migrate, "failed", V1(2), "item", 1, 2, steps=steps)
    assert events == [("two", 6, "RuntimeError"), ("one", 3, "RuntimeError")]


def _mutation_integration_12():
    import attrs
    from attrs.workspace import SchemaWorkspace

    calls = []
    def convert(value): calls.append(value); return int(value)
    @attrs.define
    class V1: value: int
    @attrs.define
    class V2: value: int = attrs.field(converter=convert)

    workspace = SchemaWorkspace("replay")
    workspace.register("item", 1, V1)
    workspace.register("item", 2, V2)
    first, first_receipt = workspace.migrate("same", V1(3), "item", 1, 2)
    generation = workspace.generation
    second, replay = workspace.migrate("same", V1(99), "item", 1, 2)
    assert first.value == second.value == 3 and calls == [3]
    assert replay.replayed and replay.generation == first_receipt.generation and workspace.generation == generation


def _mutation_integration_13():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Leaf: value: int
    @attrs.define
    class Tree: leaves: tuple[Leaf, ...]

    workspace = SchemaWorkspace("nested")
    workspace.register("leaf", 1, Leaf)
    workspace.register("tree", 1, Tree)
    tree = Tree((Leaf(2), Leaf(1)))
    first = workspace.capture(tree, "tree", 1)
    second = workspace.capture(Tree((Leaf(2), Leaf(1))), "tree", 1)
    assert first == second and first.digest == first.digest.lower()
    assert workspace.reopen_instance(first) == tree


def _mutation_integration_14():
    from attrs.workspace import SnapshotError

    workspace, V1, V2, first, second = _register_renamed_pair()
    item = V2(current=5)
    snapshot = workspace.capture(item, "entity", 2).to_dict()
    snapshot["values"][second.fields[0].identity] = 9
    raises(SnapshotError, workspace.reopen_instance, snapshot)


def _mutation_integration_15():
    workspace, V1, V2, first, second = _register_renamed_pair()
    snapshot = workspace.snapshot()
    restored = type(workspace).reopen(snapshot.to_dict(), {("entity", 1): V1, ("entity", 2): V2})
    assert restored.generation == workspace.generation
    assert restored.record("entity", 2).digest == second.digest
    assert restored.snapshot().to_dict() == snapshot.to_dict() and restored.verify_audit()


def _federation_pair(conflict=False):
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class V1: value: int
    @attrs.define
    class V2: value: int; label: str = "x"
    @attrs.define
    class Bad: value: str

    left = SchemaWorkspace("left")
    right = SchemaWorkspace("right")
    left.register("entity", 1, V1)
    right.register("entity", 1, Bad if conflict else V1)
    if not conflict:
        right.register("entity", 2, V2)
    return left, right, V1, V2


def _mutation_integration_16():
    left, right, V1, V2 = _federation_pair()
    receipt = left.federate("merge", right, expected_generation=1)
    assert receipt.kind == "federate" and left.record("entity", 2).cls is V2
    assert left.record("entity", 1).owner_registry == "left"
    assert left.record("entity", 2).owner_registry == "right"


def _mutation_integration_17():
    from attrs.workspace import SchemaConflict

    left, right, V1, V2 = _federation_pair(conflict=True)
    generation = left.generation
    error = raises(SchemaConflict, left.federate, "merge", right)
    assert error.owners == ("left", "right") and left.generation == generation
    raises(KeyError, left.record, "entity", 2)


def _mutation_integration_18():
    left, right, V1, V2 = _federation_pair()
    merge = left.federate("merge", right)
    rollback = left.rollback_federation("undo", merge, expected_generation=2)
    assert rollback.kind == "federation-rollback" and left.generation == 3
    raises(KeyError, left.record, "entity", 2)
    assert left.record("entity", 1).owner_registry == "left"


def _mutation_integration_19():
    import attrs
    from attrs.workspace import MigrationStep, RevisionConflict, SchemaWorkspace

    @attrs.define
    class V1: value: int
    @attrs.define
    class V2: value: int

    calls = []
    workspace = SchemaWorkspace("stale")
    workspace.register("item", 1, V1)
    workspace.register("item", 2, V2)
    step = MigrationStep("touch", lambda values: calls.append("called") or values)
    raises(RevisionConflict, workspace.migrate, "move", V1(1), "item", 1, 2, steps=(step,), expected_generation=1)
    assert calls == [] and workspace.generation == 2


def _mutation_integration_20():
    import attrs
    from attrs.workspace import AuditError, SchemaWorkspace

    @attrs.define
    class Item: value: int
    workspace = SchemaWorkspace("audit")
    workspace.register("item", 1, Item)
    item = Item(1)
    workspace.assign("set", item, "item", 1, {"value": 2})
    assert workspace.verify_audit()
    broken = [entry.to_dict() for entry in workspace.audit()]
    broken[-1]["parent_digest"] = "0" * 64
    raises(AuditError, workspace.verify_audit, broken)


def _mutation_integration_21():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Item: value: int
    workspace = SchemaWorkspace("repair")
    workspace.register("item", 1, Item)
    workspace.assign("set", Item(1), "item", 1, {"value": 2})
    damaged = [entry.to_dict() for entry in workspace.audit()]
    damaged[1]["digest"] = "f" * 64
    generation = workspace.generation
    repaired = workspace.repair_audit(damaged, expected_generation=generation)
    assert repaired == workspace.audit() and workspace.verify_audit(repaired)
    assert workspace.generation == generation


def _mutation_integration_22():
    workspace, V1, V2, first, second = _register_renamed_pair()
    original = V1(old_name=7)
    migrated, receipt = workspace.migrate("stable", original, "entity", 1, 2)
    before_keys = set(workspace.capture(original, "entity", 1).values)
    after_keys = set(workspace.capture(migrated, "entity", 2).values)
    assert before_keys == after_keys == {first.fields[0].identity}
    assert workspace.views(migrated, "entity", 2).initializer == {"current": 7}


def _system_01():
    workspace, V1, V2, first, second = _register_renamed_pair()
    original = workspace.construct("entity", 1, {"legacy": "2"})
    migrated, receipt = workspace.migrate("upgrade", original, "entity", 1, 2, changes={"historic": "5"})
    workspace.assign("adjust", migrated, "entity", 2, {"current": "8"})
    snapshot = workspace.capture(migrated, "entity", 2)
    reopened = workspace.reopen_instance(snapshot.to_dict())
    assert reopened.new_name == 8 and workspace.views(reopened, "entity", 2).serialized == snapshot.values
    assert workspace.verify_audit() and workspace.generation == 4


def _system_02():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class Base: _key: int = attrs.field(alias="token", converter=int)
    Dynamic = attrs.make_class("DynamicSystem", {"label": attrs.field(default="x")}, bases=(Base,))
    workspace = SchemaWorkspace("dynamic-system")
    record = workspace.register("dynamic", 1, Dynamic, aliases={"legacy": "_key"})
    first = workspace.construct("dynamic", 1, {"legacy": "3"})
    second = workspace.evolve(first, "dynamic", 1, {"token": "9", "label": "y"})
    reopened = workspace.reopen_instance(workspace.capture(second, "dynamic", 1))
    assert (first._key, second._key, reopened.label) == (3, 9, "y")
    assert set(workspace.views(reopened, "dynamic", 1).serialized) == {item.identity for item in record.fields}


def _system_03():
    import attrs
    from attrs.workspace import MigrationError, MigrationStep, SchemaWorkspace

    @attrs.define
    class V1: value: int
    @attrs.define
    class V2: value: int = attrs.field(validator=attrs.validators.gt(0))
    events = []
    workspace = SchemaWorkspace("system-comp")
    workspace.register("item", 1, V1)
    workspace.register("item", 2, V2)
    step = MigrationStep("negate", lambda values: {"value": -values["value"]}, lambda values, error: events.append((values["value"], type(error).__name__)))
    generation = workspace.generation
    raises(MigrationError, workspace.migrate, "bad", V1(3), "item", 1, 2, steps=(step,))
    assert events == [(-3, "ValueError")] and workspace.generation == generation
    good, receipt = workspace.migrate("good", V1(3), "item", 1, 2)
    assert good.value == 3 and receipt.generation == generation + 1 and workspace.verify_audit()


def _system_04():
    import attrs
    from attrs.workspace import SchemaConflict, SchemaWorkspace

    @attrs.define
    class V1: value: int
    @attrs.define
    class V2: value: int; label: str = "x"
    @attrs.define
    class Bad: value: str

    hub = SchemaWorkspace("hub")
    good = SchemaWorkspace("good")
    bad = SchemaWorkspace("bad")
    hub.register("entity", 1, V1)
    good.register("entity", 1, V1); good.register("entity", 2, V2)
    bad.register("entity", 1, Bad)
    merge = hub.federate("merge-good", good)
    before = hub.snapshot().to_dict()
    raises(SchemaConflict, hub.federate, "merge-bad", bad)
    assert hub.snapshot().to_dict() == before
    hub.rollback_federation("undo-good", merge)
    raises(KeyError, hub.record, "entity", 2)
    assert hub.record("entity", 1).owner_registry == "hub" and hub.verify_audit()


def _system_05():
    import attrs
    from attrs.workspace import RevisionConflict, SchemaWorkspace

    @attrs.define
    class Item: value: int = attrs.field(converter=int)
    workspace = SchemaWorkspace("fence")
    workspace.register("item", 1, Item)
    left = Item(1); right = Item(2)
    expected = workspace.generation
    workspace.assign("left", left, "item", 1, {"value": "3"}, expected_generation=expected)
    raises(RevisionConflict, workspace.assign, "right", right, "item", 1, {"value": "4"}, expected_generation=expected)
    assert left.value == 3 and right.value == 2 and workspace.generation == expected + 1
    assert [entry.operation_id for entry in workspace.audit()] == ["register:item:1", "left"]


def _system_06():
    import attrs
    from attrs.workspace import AuditError, SchemaWorkspace, SnapshotError

    @attrs.define
    class Item: value: int
    workspace = SchemaWorkspace("audit-system")
    workspace.register("item", 1, Item)
    workspace.assign("set", Item(1), "item", 1, {"value": 2})
    outer = workspace.snapshot().to_dict()
    outer["audit"][1]["digest"] = "0" * 64
    raises(SnapshotError, SchemaWorkspace.reopen, outer, {("item", 1): Item})
    repaired = workspace.repair_audit(outer["audit"], expected_generation=workspace.generation)
    assert workspace.verify_audit(repaired)
    clean = workspace.snapshot()
    reopened = SchemaWorkspace.reopen(clean, {("item", 1): Item})
    assert reopened.verify_audit() and reopened.snapshot().to_dict() == clean.to_dict()


def _system_07():
    import attrs
    from attrs.workspace import SchemaWorkspace

    @attrs.define
    class LeafV1: value: int
    @attrs.define
    class LeafV2: amount: int
    @attrs.define
    class BoxV1: leaf: LeafV1
    @attrs.define
    class BoxV2: leaf: LeafV2

    workspace = SchemaWorkspace("nested-upgrade")
    leaf1 = workspace.register("leaf", 1, LeafV1)
    workspace.register("leaf", 2, LeafV2, field_ids={"amount": leaf1.fields[0].identity})
    box1 = workspace.register("box", 1, BoxV1)
    workspace.register("box", 2, BoxV2, field_ids={"leaf": box1.fields[0].identity})
    new_leaf, _ = workspace.migrate("leaf-up", LeafV1(4), "leaf", 1, 2)
    new_box, receipt = workspace.migrate("box-up", BoxV1(LeafV1(4)), "box", 1, 2, changes={"leaf": new_leaf})
    replay_box, replay = workspace.migrate("box-up", BoxV1(LeafV1(99)), "box", 1, 2)
    assert new_box.leaf.amount == replay_box.leaf.amount == 4 and replay.replayed
    assert workspace.reopen_instance(workspace.capture(new_box, "box", 2)) == new_box


def _system_08():
    import attrs
    from attrs.workspace import SchemaWorkspace

    events = []
    def convert(value): events.append(("convert", value)); return int(value)
    def validate(instance, attribute, value): events.append(("validate", attribute.name, value));
    @attrs.define
    class Pair:
        left: int = attrs.field(converter=convert)
        right: int = attrs.field(converter=convert, validator=[validate, attrs.validators.ge(0)])
    workspace = SchemaWorkspace("all-views")
    record = workspace.register("pair", 1, Pair, aliases={"l": "left", "r": "right"})
    pair = workspace.construct("pair", 1, {"l": "1", "r": "2"})
    baseline = workspace.capture(pair, "pair", 1)
    generation = workspace.generation
    raises(ValueError, workspace.assign, "bad", pair, "pair", 1, {"l": "5", "r": "-1"})
    assert workspace.capture(pair, "pair", 1) == baseline and workspace.generation == generation
    evolved = workspace.evolve(pair, "pair", 1, {"l": "7", "r": "8"})
    reopened = workspace.reopen_instance(workspace.capture(evolved, "pair", 1))
    views = workspace.views(reopened, "pair", 1)
    assert views.stored == {"left": 7, "right": 8}
    assert views.initializer == {"left": 7, "right": 8}
    assert set(views.serialized) == {item.identity for item in record.fields}


ROOTS = (
    Root("N-A01", "Atomic", "native", "ordinary modern import surface", _native_atomic_01),
    Root("N-A02", "Atomic", "native", "ordinary initializer aliases", _native_atomic_02),
    Root("N-A03", "Atomic", "native", "ordinary inherited field order", _native_atomic_03),
    Root("N-A04", "Atomic", "native", "ordinary lifecycle order", _native_atomic_04),
    Root("N-A05", "Atomic", "native", "ordinary assignment pipeline", _native_atomic_05),
    Root("N-A06", "Atomic", "native", "ordinary alias-aware evolve", _native_atomic_06),
    Root("N-A07", "Atomic", "native", "ordinary recursive mapping serialization", _native_atomic_07),
    Root("N-A08", "Atomic", "native", "ordinary tuple serialization", _native_atomic_08),
    Root("N-A09", "Atomic", "native", "ordinary dynamic class construction", _native_atomic_09),
    Root("N-A10", "Atomic", "native", "ordinary frozen assignment", _native_atomic_10),
    Root("N-A11", "Atomic", "native", "ordinary metadata immutability", _native_atomic_11),
    Root("N-A12", "Atomic", "native", "ordinary setter composition", _native_atomic_12),
    Root("M-A01", "Atomic", "mutation", "workspace public value surface", _mutation_atomic_01),
    Root("M-A02", "Atomic", "mutation", "stable registration identity", _mutation_atomic_02),
    Root("M-A03", "Atomic", "mutation", "registration generation fencing", _mutation_atomic_03),
    Root("M-A04", "Atomic", "mutation", "alias construction and lifecycle labels", _mutation_atomic_04),
    Root("N-I01", "Integration", "native", "ordinary inherited dynamic lifecycle", _native_integration_01),
    Root("N-I02", "Integration", "native", "ordinary hooks through evolution", _native_integration_02),
    Root("M-I01", "Integration", "mutation", "renamed stable field identity", _mutation_integration_01),
    Root("M-I02", "Integration", "mutation", "inherited aliases across views", _mutation_integration_02),
    Root("M-I03", "Integration", "mutation", "dynamic registered class lifecycle", _mutation_integration_03),
    Root("M-I04", "Integration", "mutation", "ordered lifecycle provenance", _mutation_integration_04),
    Root("M-I05", "Integration", "mutation", "native lifecycle execution under construction", _mutation_integration_05),
    Root("M-I06", "Integration", "mutation", "multi-field assignment rollback", _mutation_integration_06),
    Root("M-I07", "Integration", "mutation", "assignment cross-view agreement", _mutation_integration_07),
    Root("M-I08", "Integration", "mutation", "non-mutating alias evolution", _mutation_integration_08),
    Root("M-I09", "Integration", "mutation", "migration by stable identity", _mutation_integration_09),
    Root("M-I10", "Integration", "mutation", "migration atomic failure", _mutation_integration_10),
    Root("M-I11", "Integration", "mutation", "reverse compensation", _mutation_integration_11),
    Root("M-I12", "Integration", "mutation", "durable migration replay", _mutation_integration_12),
    Root("M-I13", "Integration", "mutation", "deterministic nested instance snapshot", _mutation_integration_13),
    Root("M-I14", "Integration", "mutation", "instance snapshot authentication", _mutation_integration_14),
    Root("M-I15", "Integration", "mutation", "workspace snapshot reopen", _mutation_integration_15),
    Root("M-I16", "Integration", "mutation", "compatible registry federation", _mutation_integration_16),
    Root("M-I17", "Integration", "mutation", "federation ownership conflict", _mutation_integration_17),
    Root("M-I18", "Integration", "mutation", "federation rollback", _mutation_integration_18),
    Root("M-I19", "Integration", "mutation", "stale migration fence", _mutation_integration_19),
    Root("M-I20", "Integration", "mutation", "audit chain verification", _mutation_integration_20),
    Root("M-I21", "Integration", "mutation", "audit repair from durable history", _mutation_integration_21),
    Root("M-I22", "Integration", "mutation", "serialized identity across versions", _mutation_integration_22),
    Root("M-S01", "System", "mutation", "versioned assign snapshot reopen workflow", _system_01),
    Root("M-S02", "System", "mutation", "dynamic inherited alias workflow", _system_02),
    Root("M-S03", "System", "mutation", "compensated migration recovery", _system_03),
    Root("M-S04", "System", "mutation", "federation conflict rollback workflow", _system_04),
    Root("M-S05", "System", "mutation", "optimistic concurrent assignment fencing", _system_05),
    Root("M-S06", "System", "mutation", "audit repair and workspace reopen", _system_06),
    Root("M-S07", "System", "mutation", "nested multi-version durable replay", _system_07),
    Root("M-S08", "System", "mutation", "transaction rollback across all views", _system_08),
)


def validate_manifest():
    assert len(ROOTS) == 48
    assert sum(root.level == "Atomic" for root in ROOTS) == 16
    assert sum(root.level == "Integration" for root in ROOTS) == 24
    assert sum(root.level == "System" for root in ROOTS) == 8
    assert sum(root.designation == "native" for root in ROOTS) == 14
    assert sum(root.designation == "mutation" for root in ROOTS) == 34
    assert len({root.root_id for root in ROOTS}) == 48


validate_manifest()
