"""Integration tests – each crosses ≥2 public API boundaries."""
from __future__ import annotations

import pytest

from transitions import EventData, Machine, MachineError, State
from transitions.extensions import (
    AsyncMachine,
    HierarchicalMachine,
    LockedMachine,
    MachineFactory,
)
from transitions.extensions.states import (
    Error,
    Volatile,
    add_state_features,
)
from transitions.experimental.utils import (
    event,
    transition,
    with_model_definitions,
)

from conftest import HAS_GRAPH_BACKEND, make_model, run_async


# ===================================================================
# Cross-View Invariants (CVI 1–10)
# ===================================================================


@pytest.mark.depends_on("test_trigger_helper_fires_and_returns_true")
def test_cvi1_trigger_sets_model_state_to_destination():
    """CVI-1: model.state == dest after successful trigger."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    obj.go()
    assert obj.state == "bravo"


@pytest.mark.depends_on(
    "test_trigger_helper_fires_and_returns_true",
    "test_get_state_returns_registered_object",
)
def test_cvi2_get_model_state_agrees_with_state_attr():
    """CVI-2: get_model_state(model).name == model.state."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    obj.go()
    assert m.get_model_state(obj).name == obj.state


@pytest.mark.depends_on("test_is_state_helper_matches_current")
def test_cvi3_trigger_flips_is_state_helpers():
    """CVI-3: is_dest() True, is_source() False after trigger."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    obj.go()
    assert obj.is_bravo() is True
    assert obj.is_alpha() is False


@pytest.mark.depends_on("test_set_state_updates_model")
def test_cvi4_set_state_agrees_with_get_state():
    """CVI-4: after set_state, model.state == target and get_state works."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo", "charlie"], initial="alpha")
    m.set_state("charlie", obj)
    assert obj.state == "charlie"
    assert m.get_state("charlie").name == "charlie"


@pytest.mark.depends_on("test_get_triggers_includes_added_trigger")
def test_cvi5_add_transition_shows_in_triggers_and_fires():
    """CVI-5: after add_transition, trigger in get_triggers and helper works."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo"], initial="alpha")
    m.add_transition("advance", "alpha", "bravo")
    assert "advance" in m.get_triggers("alpha")
    obj.advance()
    assert obj.state == "bravo"


@pytest.mark.depends_on("test_condition_false_blocks_and_returns_false")
def test_cvi6_failed_condition_preserves_all_state_views():
    """CVI-6: on failed condition, state/get_model_state/is_state all report source."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo", conditions=lambda: False)
    obj.go()
    assert obj.state == "alpha"
    assert m.get_model_state(obj).name == "alpha"
    assert obj.is_alpha() is True


@pytest.mark.depends_on("test_machine_uses_self_when_no_model_given")
def test_cvi7_custom_model_attribute_helpers():
    """CVI-7: is_<attr>_<state> and to_<attr>_<state> for custom model_attribute."""
    obj = make_model()
    m = Machine(
        obj,
        states=["cold", "warm"],
        initial="cold",
        model_attribute="phase",
    )
    assert obj.phase == "cold"
    assert obj.is_phase_cold() is True
    assert obj.to_phase_warm() is True
    assert obj.phase == "warm"
    assert obj.is_phase_warm() is True


@pytest.mark.depends_on("test_add_model_registers_and_sets_initial")
def test_cvi8_multiple_models_independent_state():
    """CVI-8: each model's state independent; trigger on one doesn't affect the other."""
    first, second = make_model(), make_model()
    m = Machine([first, second], states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    first.go()
    assert first.state == "bravo"
    assert second.state == "alpha"
    assert m.get_model_state(second).name == "alpha"


@pytest.mark.depends_on("test_dispatch_fires_trigger_on_self_model")
def test_cvi9_dispatch_conjunction_per_model():
    """CVI-9: dispatch returns conjunction; each model reflects individual outcome."""

    class Ready:
        def is_ready(self):
            return True

    class NotReady:
        def is_ready(self):
            return False

    m1, m2 = Ready(), NotReady()
    machine = Machine(
        [m1, m2], states=["alpha", "bravo"], initial="alpha"
    )
    machine.add_transition("go", "alpha", "bravo", conditions="is_ready")
    result = machine.dispatch("go")
    assert result is False
    assert m1.state == "bravo"
    assert m2.state == "alpha"


@pytest.mark.depends_on("test_hierarchical_machine_enters_initial_child")
def test_cvi10_hierarchical_substates_exact_vs_allow():
    """CVI-10: is_parent(allow_substates=True) True for child; False with default."""
    m = HierarchicalMachine(
        states=[
            {
                "name": "working",
                "children": ["coding", "reviewing"],
                "initial": "coding",
            }
        ],
        initial="working",
    )
    assert m.is_working() is False
    assert m.is_working(allow_substates=True) is True


# ===================================================================
# Cross-boundary seam tests
# ===================================================================


def test_add_model_with_custom_initial_then_trigger():
    """Seam: add_model(initial=) → trigger → state progression."""
    obj = make_model()
    m = Machine(model=None, states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_transition("advance", "alpha", "bravo")
    m.add_transition("advance", "bravo", "charlie")
    m.add_model(obj, initial="bravo")
    obj.advance()
    assert obj.state == "charlie"


def test_ordered_transitions_cycle_with_trigger():
    """Seam: add_ordered_transitions + trigger + loop wrap."""
    m = Machine(states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_ordered_transitions(loop=True)
    m.next_state()
    m.next_state()
    assert m.state == "charlie"
    m.next_state()
    assert m.state == "alpha"


def test_ordered_no_loop_raises_at_end():
    """Seam: ordered(loop=False) → last trigger → MachineError."""
    m = Machine(states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_ordered_transitions(loop=False)
    m.next_state()
    m.next_state()
    assert m.state == "charlie"
    with pytest.raises(MachineError):
        m.next_state()


def test_send_event_callback_chain():
    """Seam: send_event + before + on_enter all receive EventData."""
    log = []

    def before_cb(ed):
        log.append(("before", ed.event.name))

    def enter_cb(ed):
        log.append(("enter", ed.event.name))

    m = Machine(
        states=["alpha", State("bravo", on_enter=enter_cb)],
        initial="alpha",
        send_event=True,
    )
    m.add_transition("go", "alpha", "bravo", before=before_cb)
    m.go()
    assert ("before", "go") in log
    assert ("enter", "go") in log


def test_reflexive_preserves_state_and_runs_callbacks():
    """Seam: dest='=' → exit + enter fire, state unchanged."""
    log = []
    m = Machine(
        states=[
            {
                "name": "alpha",
                "on_enter": lambda: log.append("enter"),
                "on_exit": lambda: log.append("exit"),
            },
            "bravo",
        ],
        initial="alpha",
    )
    m.add_transition("bounce", "alpha", "=")
    m.bounce()
    assert m.state == "alpha"
    assert "exit" in log and "enter" in log


def test_exception_before_preserves_across_all_views():
    """Seam: exception in before → state, get_model_state, is_state all keep source."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo"], initial="alpha")

    def bad():
        raise RuntimeError("fail")

    m.add_transition("go", "alpha", "bravo", before=bad)
    with pytest.raises(RuntimeError):
        obj.go()
    assert obj.state == "alpha"
    assert m.get_model_state(obj).name == "alpha"
    assert obj.is_alpha() is True


def test_queued_processes_full_chain():
    """Seam: queued=True → nested trigger deferred, final state reached."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo", "charlie"], initial="alpha", queued=True)

    def chain():
        obj.next_step()

    m.add_transition("step", "alpha", "bravo", after=chain)
    m.add_transition("next_step", "bravo", "charlie")
    obj.step()
    assert obj.state == "charlie"
    assert m.get_model_state(obj).name == "charlie"


def test_hierarchical_child_transition():
    """Seam: enter parent → initial child, then transition within children."""
    m = HierarchicalMachine(
        states=[
            "idle",
            {
                "name": "working",
                "children": ["coding", "reviewing"],
                "initial": "coding",
            },
        ],
        initial="idle",
    )
    m.add_transition("start", "idle", "working")
    m.add_transition("review", "working_coding", "working_reviewing")
    m.start()
    assert m.state == "working_coding"
    m.review()
    assert m.state == "working_reviewing"
    assert m.is_working(allow_substates=True) is True


def test_locked_machine_sequential_transitions():
    """Seam: LockedMachine serialises transition access."""
    m = LockedMachine(states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    m.add_transition("go", "bravo", "charlie")
    m.go()
    assert m.state == "bravo"
    m.go()
    assert m.state == "charlie"


def test_async_machine_queued_model():
    """Seam: AsyncMachine queued='model' keeps per-model queues."""

    async def exercise():
        m1, m2 = make_model(), make_model()
        machine = AsyncMachine(
            model=[m1, m2],
            states=["alpha", "bravo"],
            initial="alpha",
            queued="model",
        )
        machine.add_transition("go", "alpha", "bravo")
        await m1.go()
        assert m1.state == "bravo"
        assert m2.state == "alpha"

    run_async(exercise())


def test_error_accepted_vs_unaccepted():
    """Seam: Error mixin accepted=True enters OK; unaccepted dead-end raises."""

    @add_state_features(Error)
    class EM(Machine):
        pass

    m_ok = EM(
        states=["running", {"name": "done", "accepted": True}],
        initial="running",
        auto_transitions=False,
    )
    m_ok.add_transition("finish", "running", "done")
    m_ok.finish()
    assert m_ok.state == "done"

    m_bad = EM(
        states=["running", "problem"],
        initial="running",
        auto_transitions=False,
    )
    m_bad.add_transition("crash", "running", "problem")
    with pytest.raises(MachineError):
        m_bad.crash()


def test_volatile_lifecycle_enter_and_exit():
    """Seam: Volatile assigns scope on enter, removes on exit."""

    @add_state_features(Volatile)
    class VM(Machine):
        pass

    class Hook:
        pass

    m = VM(
        states=["idle", {"name": "active", "volatile": Hook}],
        initial="idle",
        auto_transitions=False,
    )
    m.add_transition("start", "idle", "active")
    m.add_transition("stop", "active", "idle")
    m.start()
    assert isinstance(m.scope, Hook)
    m.stop()
    assert not hasattr(m, "scope")


def test_remove_model_and_dispatch():
    """Seam: remove_model excludes model from subsequent dispatch."""
    m1, m2 = make_model(), make_model()
    machine = Machine([m1, m2], states=["alpha", "bravo"], initial="alpha")
    machine.add_transition("go", "alpha", "bravo")
    machine.remove_model(m2)
    machine.dispatch("go")
    assert m1.state == "bravo"
    assert m2.state == "alpha"


def test_bulk_add_transitions_then_trigger():
    """Seam: add_transitions bulk → triggers fire correctly."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_transitions(
        [
            {"trigger": "step", "source": "alpha", "dest": "bravo"},
            ["leap", "bravo", "charlie"],
        ]
    )
    obj.step()
    assert obj.state == "bravo"
    obj.leap()
    assert obj.state == "charlie"


def test_model_definitions_event_and_transition():
    """Seam: with_model_definitions + event + transition utilities."""

    @with_model_definitions
    class DefMachine(Machine):
        pass

    class MyModel:
        advance = event(
            transition("alpha", "bravo"),
            transition("bravo", "charlie"),
        )

    obj = MyModel()
    m = DefMachine(
        model=obj, states=["alpha", "bravo", "charlie"], initial="alpha"
    )
    obj.advance()
    assert obj.state == "bravo"
    obj.advance()
    assert obj.state == "charlie"


def test_finalize_runs_on_success_and_failure():
    """Seam: finalize_event fires after both successful and failed transitions."""
    log = []
    m = Machine(
        states=["alpha", "bravo"],
        initial="alpha",
        finalize_event=lambda: log.append("fin"),
    )
    m.add_transition("go", "alpha", "bravo")
    m.go()
    assert log == ["fin"]

    def bad():
        raise RuntimeError("fail")

    m.add_transition("fail", "bravo", "alpha", before=bad)
    with pytest.raises(RuntimeError):
        m.fail()
    assert log == ["fin", "fin"]


def test_factory_produces_usable_machine_class():
    """Seam: MachineFactory → get class → construct → trigger → state."""
    cls = MachineFactory.get_predefined(locked=True)
    obj = make_model()
    m = cls(obj, states=["alpha", "bravo"], initial="alpha")
    m.add_transition("go", "alpha", "bravo")
    obj.go()
    assert obj.state == "bravo"
    assert m.get_model_state(obj).name == "bravo"


def test_add_model_three_models_different_initials():
    """Seam: add_model with per-model initial → each starts at requested state."""
    m1, m2, m3 = make_model(), make_model(), make_model()
    machine = Machine(
        model=None,
        states=["alpha", "bravo", "charlie", "delta"],
        initial="alpha",
    )
    machine.add_transition("advance", "alpha", "bravo")
    machine.add_transition("advance", "bravo", "charlie")
    machine.add_transition("advance", "charlie", "delta")
    machine.add_model(m1)
    machine.add_model(m2, initial="bravo")
    machine.add_model(m3, initial="charlie")
    m1.advance()
    m2.advance()
    m3.advance()
    assert (m1.state, m2.state, m3.state) == ("bravo", "charlie", "delta")


def test_wildcard_and_trigger_from_multiple_origins():
    """Seam: wildcard source → trigger from different states all reach dest."""
    obj = make_model()
    m = Machine(obj, states=["alpha", "bravo", "charlie"], initial="alpha")
    m.add_transition("reset", "*", "alpha")

    obj.to_charlie()
    assert obj.state == "charlie"
    obj.reset()
    assert obj.state == "alpha"

    obj.to_bravo()
    assert obj.state == "bravo"
    obj.reset()
    assert obj.state == "alpha"
