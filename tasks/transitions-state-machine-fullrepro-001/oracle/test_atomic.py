"""Atomic tests – each verifies ONE public API entry, ONE behaviour point."""
from __future__ import annotations

import pytest

from transitions import Event, EventData, Machine, MachineError, State, Transition
from transitions.extensions import (
    AsyncMachine,
    HierarchicalMachine,
    LockedMachine,
    MachineFactory,
)
from transitions.extensions.nesting import NestedState
from transitions.extensions.states import (
    Error,
    Retry,
    Tags,
    Timeout,
    Volatile,
    add_state_features,
)
from transitions.experimental.utils import generate_base_model, transition

from conftest import HAS_GRAPH_BACKEND, make_model, run_async

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


def test_state_name_returns_configured_value():
    assert State("alpha").name == "alpha"


def test_state_value_equals_name_by_default():
    assert State("bravo").value == "bravo"


def test_state_on_enter_callback_fires():
    log = []
    m = Machine(
        states=["idle", State("active", on_enter=lambda: log.append("in"))],
        initial="idle",
    )
    m.add_transition("activate", "idle", "active")
    m.activate()
    assert log == ["in"]


def test_state_on_exit_callback_fires():
    log = []
    m = Machine(
        states=[State("idle", on_exit=lambda: log.append("out")), "active"],
        initial="idle",
    )
    m.add_transition("activate", "idle", "active")
    m.activate()
    assert log == ["out"]


@pytest.mark.parametrize("trigger", ["enter", "exit"])
def test_state_add_callback_accepts_enter_and_exit(trigger):
    s = State("demo")
    s.add_callback(trigger, lambda: None)


def test_state_add_callback_rejects_unsupported_trigger():
    with pytest.raises(AttributeError):
        State("demo").add_callback("move", lambda: None)


# ---------------------------------------------------------------------------
# Transition
# ---------------------------------------------------------------------------


def test_transition_exposes_source_and_dest():
    t = Transition("alpha", "bravo")
    assert (t.source, t.dest) == ("alpha", "bravo")


@pytest.mark.parametrize("phase", ["prepare", "before", "after"])
def test_transition_add_callback_accepts_valid_phase(phase):
    Transition("alpha", "bravo").add_callback(phase, lambda: None)


def test_transition_add_callback_rejects_invalid_phase():
    with pytest.raises(AttributeError):
        Transition("alpha", "bravo").add_callback("execute", lambda: None)


# ---------------------------------------------------------------------------
# EventData (accessed via send_event)
# ---------------------------------------------------------------------------


def test_event_data_exposes_required_attributes():
    captured = []

    def grab(ed):
        captured.append(ed)

    m = Machine(states=["alpha", "bravo"], initial="alpha", send_event=True)
    m.add_transition("go", "alpha", "bravo", before=grab)
    m.go(42, key="val")
    ed = captured[0]
    assert ed.event.name == "go"
    assert ed.machine is m
    assert ed.model is m
    assert ed.args == (42,)
    assert ed.kwargs == {"key": "val"}


# ---------------------------------------------------------------------------
# Machine Construction
# ---------------------------------------------------------------------------


def test_machine_uses_self_when_no_model_given():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    assert m.state == "alpha"
    assert m.is_alpha() is True


def test_machine_accepts_state_objects():
    m = Machine(states=[State("first"), State("second")], initial="first")
    m.add_transition("go", "first", "second")
    assert m.go() is True
    assert m.state == "second"


def test_machine_accepts_dict_state_definitions():
    m = Machine(states=[{"name": "first"}, {"name": "second"}], initial="first")
    m.add_transition("go", "first", "second")
    assert m.go() is True


def test_machine_creates_default_initial_when_omitted():
    m = Machine()
    assert m.state == "initial"
    assert m.get_state("initial").name == "initial"


def test_machine_initial_none_requires_explicit_on_add_model():
    m = Machine(model=None, states=["alpha", "bravo"], initial=None)
    with pytest.raises(ValueError):
        m.add_model(make_model())


def test_machine_auto_transitions_generates_helpers():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    assert m.to_bravo() is True
    assert m.state == "bravo"
    m.to_alpha()
    assert m.may_to_bravo() is True
    assert m.state == "alpha"


def test_machine_ignore_invalid_returns_false():
    m = Machine(states=["alpha"], initial="alpha", ignore_invalid_triggers=True)
    assert m.trigger("nonexistent") is False


def test_machine_send_event_delivers_event_data_to_callbacks():
    received = []
    m = Machine(states=["alpha", "bravo"], initial="alpha", send_event=True)
    m.add_transition("go", "alpha", "bravo", before=lambda ed: received.append(ed))
    m.go(7, flag=True)
    assert isinstance(received[0], EventData)
    assert received[0].args == (7,)
    assert received[0].kwargs == {"flag": True}


# ---------------------------------------------------------------------------
# Machine Configuration & Inspection
# ---------------------------------------------------------------------------


def test_get_state_returns_registered_object():
    m = Machine(states=["alpha"], initial="alpha")
    assert m.get_state("alpha").name == "alpha"


@pytest.mark.parametrize("name", ["missing", "unknown", "absent"])
def test_get_state_unknown_raises_value_error(name):
    m = Machine(states=["alpha"], initial="alpha")
    with pytest.raises(ValueError):
        m.get_state(name)


def test_set_state_unknown_raises_value_error():
    m = Machine(states=["alpha"], initial="alpha")
    with pytest.raises(ValueError):
        m.set_state("missing")


def test_set_state_updates_model():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.set_state("bravo")
    assert m.state == "bravo"


def test_add_states_registers_new_states():
    m = Machine(states=["alpha"], initial="alpha")
    m.add_states(["bravo", "charlie"])
    assert m.get_state("bravo").name == "bravo"
    assert m.get_state("charlie").name == "charlie"


def test_add_model_registers_and_sets_initial():
    m = Machine(model=None, states=["alpha", "bravo"], initial="alpha")
    obj = make_model()
    m.add_model(obj)
    assert obj.state == "alpha"


# ---------------------------------------------------------------------------
# Transition Queries
# ---------------------------------------------------------------------------


def test_get_triggers_includes_added_trigger():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("advance", "alpha", "bravo")
    assert "advance" in m.get_triggers("alpha")


def test_get_transitions_returns_matching_objects():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("advance", "alpha", "bravo")
    ts = m.get_transitions("advance")
    assert len(ts) >= 1
    assert ts[0].source == "alpha"
    assert ts[0].dest == "bravo"


def test_get_transitions_returns_empty_for_unknown_trigger():
    m = Machine(states=["alpha"], initial="alpha")
    assert m.get_transitions("nonexistent") == []


# ---------------------------------------------------------------------------
# Transition Registration
# ---------------------------------------------------------------------------


def test_wildcard_source_applies_to_all_current_states():
    m = Machine(states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_transition("reset", "*", "alpha")
    m.to_charlie()
    assert m.reset() is True
    assert m.state == "alpha"


def test_reflexive_transition_fires_exit_and_enter():
    log = []
    m = Machine(
        states=[
            {
                "name": "alpha",
                "on_enter": lambda: log.append("enter"),
                "on_exit": lambda: log.append("exit"),
            }
        ],
        initial="alpha",
    )
    m.add_transition("ping", "alpha", "=")
    m.ping()
    assert "exit" in log
    assert "enter" in log
    assert m.state == "alpha"


def test_internal_transition_skips_exit_and_enter():
    log = []
    m = Machine(
        states=[
            {
                "name": "alpha",
                "on_enter": lambda: log.append("enter"),
                "on_exit": lambda: log.append("exit"),
            }
        ],
        initial="alpha",
    )
    m.add_transition("noop", "alpha", None)
    m.noop()
    assert log == []
    assert m.state == "alpha"


def test_ordered_transitions_cycle_through_states():
    m = Machine(states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_ordered_transitions()
    visited = []
    for _ in range(3):
        m.next_state()
        visited.append(m.state)
    assert visited == ["bravo", "charlie", "alpha"]


def test_ordered_no_loop_last_state_raises():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_ordered_transitions(loop=False)
    m.next_state()
    with pytest.raises(MachineError):
        m.next_state()


def test_ordered_fewer_than_two_states_raises():
    m = Machine(states=["alpha"], initial="alpha")
    with pytest.raises(ValueError):
        m.add_ordered_transitions()


def test_remove_transition_clears_trigger():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    m.remove_transition("go", "alpha", "bravo")
    assert "go" not in m.get_triggers("alpha")


def test_trigger_name_equals_model_attribute_raises():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    with pytest.raises(ValueError):
        m.add_transition("state", "alpha", "bravo")


def test_transition_source_list_fires_from_each():
    for start in ("alpha", "bravo"):
        m = Machine(states=["alpha", "bravo", "charlie"], initial=start)
        m.add_transition("finish", ["alpha", "bravo"], "charlie")
        assert m.finish() is True
        assert m.state == "charlie"


# ---------------------------------------------------------------------------
# Dynamic Helpers
# ---------------------------------------------------------------------------


def test_trigger_helper_fires_and_returns_true():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    assert m.trigger("go") is True
    assert m.state == "bravo"


def test_may_trigger_evaluates_without_state_change():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    assert m.may_trigger("go") is True
    assert m.state == "alpha"


def test_is_state_helper_matches_current():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    assert m.is_alpha() is True
    assert m.is_bravo() is False


def test_to_state_helper_updates_state():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    assert m.to_bravo() is True
    assert m.state == "bravo"


def test_may_to_state_reports_without_moving():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    assert m.may_to_bravo() is True
    assert m.state == "alpha"


def test_may_trigger_unknown_returns_false_when_ignored():
    m = Machine(states=["alpha"], initial="alpha", ignore_invalid_triggers=True)
    assert m.may_trigger("nonexistent") is False


def test_dispatch_fires_trigger_on_self_model():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    assert m.dispatch("go") is True
    assert m.state == "bravo"


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def test_callback_callable_object_fires():
    log = []
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo", before=lambda: log.append("fired"))
    m.go()
    assert log == ["fired"]


def test_callback_model_attribute_name_fires():
    class Obj:
        def __init__(self):
            self.log = []

        def record(self):
            self.log.append("ok")

    obj = Obj()
    m = Machine(obj, states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo", before="record")
    obj.go()
    assert obj.log == ["ok"]


def test_callback_unresolved_raises_attribute_error():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo", before="nonexistent_method")
    with pytest.raises(AttributeError):
        m.go()


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------


def test_condition_false_blocks_and_returns_false():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo", conditions=lambda: False)
    assert m.go() is False
    assert m.state == "alpha"


def test_unless_true_blocks_transition():
    m = Machine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo", unless=lambda: True)
    assert m.go() is False
    assert m.state == "alpha"


# ---------------------------------------------------------------------------
# Exception Handling
# ---------------------------------------------------------------------------


def test_before_exception_preserves_old_state():
    m = Machine(states=["alpha", "bravo"], initial="alpha")

    def bad():
        raise RuntimeError("oops")

    m.add_transition("go", "alpha", "bravo", before=bad)
    with pytest.raises(RuntimeError):
        m.go()
    assert m.state == "alpha"


def test_after_exception_retains_new_state():
    m = Machine(states=["alpha", "bravo"], initial="alpha")

    def bad():
        raise RuntimeError("boom")

    m.add_transition("go", "alpha", "bravo", after=bad)
    with pytest.raises(RuntimeError):
        m.go()
    assert m.state == "bravo"


def test_finalize_event_runs_after_exception():
    finalized = []
    m = Machine(
        states=["alpha", "bravo"],
        initial="alpha",
        finalize_event=lambda: finalized.append(True),
    )

    def bad():
        raise RuntimeError("fail")

    m.add_transition("go", "alpha", "bravo", before=bad)
    with pytest.raises(RuntimeError):
        m.go()
    assert len(finalized) == 1


def test_on_exception_handler_receives_event_data():
    received = []
    m = Machine(
        states=["alpha", "bravo"],
        initial="alpha",
        send_event=True,
        on_exception=lambda ed: received.append(ed),
    )

    def bad(ed):
        raise RuntimeError("err")

    m.add_transition("go", "alpha", "bravo", before=bad)
    m.go()
    assert len(received) == 1
    assert hasattr(received[0], "machine")


# ---------------------------------------------------------------------------
# Queue Semantics
# ---------------------------------------------------------------------------


def test_queued_true_defers_nested_trigger():
    states_snapshot = []
    m = Machine(
        states=["alpha", "bravo", "charlie"], initial="alpha", queued=True
    )

    def after_step():
        m.advance()
        states_snapshot.append(m.state)

    m.add_transition("step", "alpha", "bravo", after=after_step)
    m.add_transition("advance", "bravo", "charlie")
    m.step()
    assert states_snapshot == ["bravo"]
    assert m.state == "charlie"


# ---------------------------------------------------------------------------
# Extension Machines
# ---------------------------------------------------------------------------


def test_nested_state_separator_default():
    assert NestedState.separator == "_"


@pytest.mark.skipif(not HAS_GRAPH_BACKEND, reason="no graph backend")
def test_graph_machine_model_has_get_graph():
    from transitions.extensions import GraphMachine

    m = GraphMachine(states=["alpha", "bravo"], initial="alpha")
    graph = m.get_graph()
    assert graph is not None
    raw = graph.draw(None)
    assert isinstance(raw, bytes)


def test_locked_machine_basic_transition():
    m = LockedMachine(states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    assert m.go() is True
    assert m.state == "bravo"


def test_async_machine_creates_awaitable_trigger():
    async def exercise():
        m = AsyncMachine(states=["alpha", "bravo"], initial="alpha")
        m.add_transition("go", "alpha", "bravo")
        result = await m.go()
        assert result is True
        assert m.state == "bravo"

    run_async(exercise())


def test_factory_supported_returns_class():
    cls = MachineFactory.get_predefined(nested=True)
    m = cls(states=["alpha", "bravo"], initial="alpha")
    assert m.state == "alpha"


def test_factory_unsupported_combination_raises():
    with pytest.raises(ValueError):
        MachineFactory.get_predefined(locked=True, asyncio=True)


def test_hierarchical_machine_enters_initial_child():
    m = HierarchicalMachine(
        states=[
            {
                "name": "parent",
                "children": ["child_a", "child_b"],
                "initial": "child_a",
            }
        ],
        initial="parent",
    )
    assert m.is_parent(allow_substates=True) is True


# ---------------------------------------------------------------------------
# State Features
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag", ["ready", "approved", "critical"])
def test_tags_is_tag_predicate(tag):
    @add_state_features(Tags)
    class TM(Machine):
        pass

    m = TM(states=[{"name": "s", "tags": [tag]}], initial="s")
    assert getattr(m.get_state("s"), "is_" + tag) is True


def test_error_unaccepted_dead_end_raises():
    @add_state_features(Error)
    class EM(Machine):
        pass

    m = EM(
        states=["running", "problem"],
        initial="running",
        auto_transitions=False,
    )
    m.add_transition("crash", "running", "problem")
    with pytest.raises(MachineError):
        m.crash()


def test_timeout_without_on_timeout_raises():
    @add_state_features(Timeout)
    class TM(Machine):
        pass

    with pytest.raises(AttributeError):
        TM(states=[{"name": "waiting", "timeout": 5}], initial="waiting")


def test_volatile_assigns_scope_on_enter():
    @add_state_features(Volatile)
    class VM(Machine):
        pass

    class Hook:
        pass

    m = VM(
        states=["idle", {"name": "active", "volatile": Hook}], initial="idle"
    )
    m.add_transition("start", "idle", "active")
    m.start()
    assert isinstance(m.scope, Hook)
    assert m.state == "active"


def test_retry_without_on_failure_raises():
    @add_state_features(Retry)
    class RM(Machine):
        pass

    with pytest.raises(AttributeError):
        RM(states=[{"name": "flaky", "retries": 3}], initial="flaky")


def test_retry_exceeds_limit_invokes_failure():
    @add_state_features(Retry)
    class RM(Machine):
        pass

    failed = []
    m = RM(
        states=[
            "idle",
            {
                "name": "unstable",
                "retries": 3,
                "on_failure": lambda: failed.append(1),
            },
        ],
        initial="idle",
        auto_transitions=False,
    )
    m.add_transition("attempt", "idle", "unstable")
    m.add_transition("again", "unstable", "unstable")
    m.attempt()
    m.again()
    m.again()
    assert len(failed) == 0
    m.again()
    assert len(failed) >= 1


# ---------------------------------------------------------------------------
# Model Definition Utilities
# ---------------------------------------------------------------------------


def test_transition_utility_returns_definition_dict():
    t = transition("alpha", "bravo", conditions=["check"])
    assert isinstance(t, dict)
    assert t["source"] == "alpha"
    assert t["dest"] == "bravo"


def test_generate_base_model_creates_class():
    cfg = Machine(model=None, states=["alpha", "bravo"], initial="alpha")
    Base = generate_base_model(cfg)
    assert callable(Base)
