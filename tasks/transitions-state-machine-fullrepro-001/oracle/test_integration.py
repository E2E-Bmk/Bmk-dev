"""Integration and end-to-end public behavioral checks for transitions."""

from __future__ import annotations

import asyncio

import pytest

from transitions import EventData, Machine, MachineError
from transitions.extensions import AsyncMachine, HierarchicalMachine, LockedMachine, MachineFactory


def test_machine_creates_the_default_initial_state_for_a_later_model():
    model = type("Model", (), {})()
    machine = Machine(model=None)
    machine.add_model(model)

    assert model.state == "initial"
    assert machine.get_model_state(model).name == "initial"


def test_add_model_requires_an_initial_state_when_machine_initial_is_none():
    model = type("Model", (), {})()
    machine = Machine(model=None, states=["A", "B"], initial=None)

    with pytest.raises(ValueError):
        machine.add_model(model)


def test_machine_custom_model_attribute_changes_state_helpers():
    model = type("Model", (), {})()
    machine = Machine(model, states=["cold", "warm"], initial="cold", model_attribute="phase")

    assert model.phase == "cold"
    assert model.is_phase_cold() is True
    assert model.to_phase_warm() is True
    assert model.phase == "warm"
    assert model.is_phase_warm() is True


def test_overview_projects_machine_state_to_a_separate_application_object():
    model = type("ApplicationModel", (), {})()
    machine = Machine(model, states=["new", "ready"], initial="new")
    machine.add_transition("prepare", "new", "ready")

    assert model.prepare() is True
    assert model.state == "ready"
    assert machine.get_model_state(model).name == "ready"


def test_overview_keeps_multiple_registered_model_projections_independent():
    first, second = type("Model", (), {})(), type("Model", (), {})()
    machine = Machine([first, second], states=["A", "B"], initial="A")
    machine.add_transition("advance", "A", "B")

    assert first.advance() is True
    assert first.state == "B"
    assert second.state == "A"
    assert machine.get_model_state(second).name == "A"


@pytest.mark.parametrize("source,dest", [("A", "B"), ("B", "C"), ("C", "D"), ("cold", "warm"), ("warm", "hot"), ("idle", "active")])
def test_trigger_updates_all_public_state_projections(source, dest):
    model = type("Model", (), {})()
    machine = Machine(model, states=[source, dest], initial=source)
    machine.add_transition("advance", source, dest)

    assert model.advance() is True
    assert model.state == dest
    assert machine.get_model_state(model).name == dest
    assert getattr(model, "is_" + dest)() is True
    assert getattr(model, "is_" + source)() is False


@pytest.mark.parametrize("target", ["B", "C", "D", "E"])
def test_automatic_transition_helper_changes_state(target):
    machine = Machine(states=["A", "B", "C", "D", "E"], initial="A")
    assert getattr(machine, "to_" + target)() is True
    assert machine.state == target


@pytest.mark.parametrize("allowed", [True, False])
def test_conditions_control_result_without_wrong_state_change(allowed):
    model = type("Model", (), {"allowed": staticmethod(lambda: allowed)})()
    machine = Machine(model, states=["A", "B"], initial="A")
    machine.add_transition("advance", "A", "B", conditions="allowed")

    assert model.advance() is allowed
    assert model.state == ("B" if allowed else "A")


def test_representative_workflow_advances_hot_matter():
    class Matter:
        def is_hot(self):
            return True

    sample = Matter()
    machine = Machine(sample, states=["solid", "liquid", "gas"], initial="solid")
    machine.add_transition("melt", "solid", "liquid", conditions="is_hot")

    assert sample.is_solid() is True
    assert sample.may_melt() is True
    assert sample.melt() is True
    assert sample.state == "liquid"


def test_representative_workflow_keeps_cold_matter_solid():
    class Matter:
        def is_hot(self):
            return False

    sample = Matter()
    machine = Machine(sample, states=["solid", "liquid", "gas"], initial="solid")
    machine.add_transition("melt", "solid", "liquid", conditions="is_hot")

    assert sample.melt() is False
    assert sample.state == "solid"


def test_representative_workflow_rejects_melting_from_an_unrelated_state():
    class Matter:
        def is_hot(self):
            return True

    sample = Matter()
    machine = Machine(sample, states=["solid", "liquid", "gas"], initial="gas")
    machine.add_transition("melt", "solid", "liquid", conditions="is_hot")

    with pytest.raises(MachineError):
        sample.melt()


@pytest.mark.parametrize("initial,expected", [("A", "B"), ("B", "C"), ("C", "D")])
def test_add_model_honors_requested_initial_state(initial, expected):
    model = type("Model", (), {})()
    machine = Machine(model=None, states=["A", "B", "C", "D"], initial="A")
    machine.add_transition("advance", "A", "B")
    machine.add_transition("advance", "B", "C")
    machine.add_transition("advance", "C", "D")
    machine.add_model(model, initial=initial)
    model.advance()
    assert model.state == expected


@pytest.mark.parametrize("target", ["A", "B", "C"])
def test_set_state_and_get_state_agree(target):
    model = type("Model", (), {})()
    machine = Machine(model, states=["A", "B", "C"], initial="A")
    machine.set_state(target, model)
    assert model.state == target
    assert machine.get_state(target).name == target


@pytest.mark.parametrize("dest", ["=", None])
def test_reflexive_and_internal_transitions_preserve_state(dest):
    events = []
    machine = Machine(states=[{"name": "A", "on_enter": lambda: events.append("enter"), "on_exit": lambda: events.append("exit")}], initial="A")
    machine.add_transition("ping", "A", dest)
    assert machine.ping() is True
    assert machine.state == "A"
    if dest == "=":
        assert events == ["exit", "enter"]
    else:
        assert events == []


@pytest.mark.parametrize("loop", [True, False, True])
def test_ordered_transitions_follow_configured_cycle(loop):
    machine = Machine(states=["A", "B", "C"], initial="A")
    machine.add_ordered_transitions(loop=loop)
    machine.next_state()
    assert machine.state == "B"
    machine.next_state()
    assert machine.state == "C"
    if loop:
        assert machine.next_state() is True
        assert machine.state == "A"
    else:
        with pytest.raises(MachineError):
            machine.next_state()


@pytest.mark.parametrize("source", ["A", "B"])
def test_remove_transition_removes_a_trigger_when_no_matches_remain(source):
    machine = Machine(states=["A", "B"], initial="A")
    machine.add_transition("advance", source, "B")
    machine.remove_transition("advance", source, "B")
    assert "advance" not in machine.get_triggers(source)


@pytest.mark.parametrize("states", [(["A", "A"], ["B", "B"]), (["A", "B"], ["B", "B"]), (["B", "B"], ["B", "B"])])
def test_dispatch_combines_results_for_every_registered_model(states):
    initial, expected = states
    first, second = type("Model", (), {})(), type("Model", (), {})()
    machine = Machine([first, second], states=["A", "B"], initial=initial[0], ignore_invalid_triggers=True)
    machine.set_state(initial[0], first)
    machine.set_state(initial[1], second)
    machine.add_transition("advance", "A", "B")
    result = machine.dispatch("advance")
    assert result is (initial == ["A", "A"])
    assert [first.state, second.state] == expected


@pytest.mark.parametrize("send_event", [False, True])
def test_callbacks_receive_direct_arguments_or_event_data(send_event):
    received = []

    def callback(*args, **kwargs):
        received.append((args, kwargs))

    machine = Machine(states=["A", "B"], initial="A", send_event=send_event)
    machine.add_transition("advance", "A", "B", before=callback)
    machine.advance("value", flag=True)
    args, kwargs = received[0]
    if send_event:
        assert isinstance(args[0], EventData)
        assert args[0].kwargs["flag"] is True
    else:
        assert args == ("value",)
        assert kwargs == {"flag": True}


def test_locked_machine_public_import_supports_a_basic_transition():
    machine = LockedMachine(states=["A", "B"], initial="A")
    machine.add_transition("advance", "A", "B")

    assert machine.advance() is True
    assert machine.state == "B"


def test_async_machine_public_import_exposes_awaitable_event_helpers():
    async def exercise():
        machine = AsyncMachine(states=["A", "B"], initial="A")
        machine.add_transition("advance", "A", "B")

        assert await machine.advance() is True
        assert machine.state == "B"

    asyncio.run(exercise())


def test_factory_public_import_selects_a_machine_that_can_transition():
    machine_class = MachineFactory.get_predefined(locked=True)
    machine = machine_class(states=["A", "B"], initial="A")
    machine.add_transition("advance", "A", "B")

    assert machine.advance() is True
    assert machine.state == "B"


@pytest.mark.parametrize("child", ["one", "two", "three"])
def test_hierarchical_machine_enters_configured_initial_child(child):
    machine = HierarchicalMachine(states=[{"name": "parent", "children": [child], "initial": child}], initial="parent")
    assert machine.is_parent(allow_substates=True) is True


def test_hierarchical_exact_state_check_rejects_only_descendant_match():
    machine = HierarchicalMachine(states=[{"name": "parent", "children": ["child"], "initial": "child"}], initial="parent")
    assert machine.is_parent() is False
    assert machine.is_parent(allow_substates=True) is True


def test_add_model_honors_each_requested_initial_state():
    class Model:
        pass

    first, second, third = Model(), Model(), Model()
    machine = Machine(model=None, states=["A", "B", "C", "D"], initial="A")
    machine.add_transition("advance", "A", "B")
    machine.add_transition("advance", "B", "C")
    machine.add_transition("advance", "C", "D")

    machine.add_model(first)
    machine.add_model(second, initial="B")
    machine.add_model(third, initial="C")
    first.advance()
    second.advance()
    third.advance()

    assert (first.state, second.state, third.state) == ("B", "C", "D")
