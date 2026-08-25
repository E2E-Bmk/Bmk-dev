from __future__ import annotations


def test_a01(tmp_path):
    import traitlets as t
    class M(t.HasTraits): value = t.Int(1)
    obj = M(); old = obj.value
    try: obj.value = "bad"
    except t.TraitError: pass
    else: raise AssertionError("strict integer accepted text")
    assert obj.value == old


def test_a02(tmp_path):
    import traitlets as t
    class M(t.HasTraits): value = t.CInt()
    assert M(value="12").value == 12


def test_a03(tmp_path):
    import traitlets as t
    trait = t.Unicode().tag(config=True, role="title")
    assert trait.metadata == {"config": True, "role": "title"}
    assert t.Unicode().metadata == {}


def test_a04(tmp_path):
    import traitlets as t
    calls = []
    class M(t.HasTraits):
        value = t.Int()
        @t.default("value")
        def _value(self): calls.append(1); return 7
    obj = M(); assert obj.value == 7 and obj.value == 7 and calls == [1]


def test_a05(tmp_path):
    import traitlets as t
    class M(t.HasTraits): values = t.List(t.Int())
    assert M(values=[1, 2]).values == [1, 2]
    try: M(values=[1, "x"])
    except t.TraitError: pass
    else: raise AssertionError("element was not validated")


def test_a06(tmp_path):
    import traitlets as t
    class M(t.HasTraits): mode = t.Enum(["a", "b"], default_value="a")
    obj = M(mode="b"); assert obj.mode == "b"
    try: obj.mode = "c"
    except t.TraitError: pass
    else: raise AssertionError("enum accepted unknown value")


def test_a07(tmp_path):
    import traitlets as t
    class M(t.HasTraits): alpha = t.Int(); beta = t.Unicode()
    obj = M(); assert {"alpha", "beta"}.issubset(obj.trait_names())
    assert M.class_traits()["alpha"].name == "alpha"


def test_a08(tmp_path):
    from traitlets.utils.bunch import Bunch
    item = Bunch(answer=42); assert item.answer == item["answer"] == 42
    item.answer = 7; assert item["answer"] == 7


def test_i01(tmp_path):
    import traitlets as t
    events = []
    class M(t.HasTraits):
        value = t.Int()
        @t.validate("value")
        def _valid(self, proposal): return max(0, proposal["value"])
    obj = M(); obj.observe(lambda change: events.append((change.old, change.new)), "value")
    obj.value = -3; assert obj.value == 0 and events == []
    obj.value = 4; assert events == [(0, 4)]


def test_i02(tmp_path):
    import traitlets as t
    events = []
    class M(t.HasTraits): value = t.Int()
    obj = M(); obj.observe(lambda change: events.append((change.old, change.new)), "value")
    with obj.hold_trait_notifications(): obj.value = 1; obj.value = 2
    assert events == [(0, 2)]


def test_i03(tmp_path):
    import traitlets as t
    class M(t.HasTraits): value = t.Int()
    left, right = M(value=1), M(value=2); connection = t.link((left, "value"), (right, "value"))
    assert right.value == 1; right.value = 9; assert left.value == 9
    connection.unlink(); left.value = 3; assert right.value == 9


def test_i04(tmp_path):
    import traitlets as t
    from traitlets.config import Config, Configurable
    class M(Configurable): value = t.Int(1).tag(config=True)
    cfg = Config(); cfg.M.value = 8
    assert M(config=cfg).value == 8


def test_s01(tmp_path):
    import traitlets as t
    seen = []
    class M(t.HasTraits):
        value = t.Int()
        @t.validate("value")
        def _valid(self, proposal): return abs(proposal["value"])
    left, right = M(), M(); right.observe(lambda change: seen.append(change.new), "value")
    connection = t.dlink((left, "value"), (right, "value"), transform=lambda value: value + 1)
    left.value = -4; assert left.value == 4 and right.value == 5 and seen[-1] == 5
    connection.unlink()


def test_s02(tmp_path):
    import traitlets as t
    from traitlets.config import Config, Configurable
    class M(Configurable): value = t.Int(1).tag(config=True)
    obj = M(); seen = []; obj.observe(lambda change: seen.append(change.new), "value")
    cfg = Config(); cfg.M.value = 6; obj.update_config(cfg)
    assert obj.value == 6 and seen == [6]

