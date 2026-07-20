"""Atomic public behavioral checks for transitions."""

from __future__ import annotations

import asyncio

import pytest

from transitions import Machine, MachineError, State, Transition
from transitions.extensions import MachineFactory
from transitions.extensions.states import Tags, add_state_features


@pytest.mark.parametrize("name", ["ready", "waiting", "done"])
def test_state_exposes_its_public_name_and_value(name):
    state = State(name)
    assert state.name == name
    assert state.value == name


def test_state_rejects_unknown_callback_phase():
    with pytest.raises(AttributeError):
        State("ready").add_callback("unknown", lambda: None)


def test_transition_rejects_unknown_callback_phase():
    with pytest.raises(AttributeError):
        Transition("A", "B").add_callback("unknown", lambda: None)


def test_machine_constructs_itself_as_its_default_model():
    machine = Machine(states=["idle", "done"], initial="idle")

    assert machine.state == "idle"
    assert machine.is_idle() is True
    assert machine.to_done() is True
    assert machine.state == "done"


def test_machine_accepts_documented_state_dictionary_definitions():
    machine = Machine(states=[{"name": "A"}, {"name": "B"}], initial="A")
    machine.add_transition("advance", "A", "B")

    assert machine.advance() is True
    assert machine.get_state("B").name == "B"


def test_overview_allows_the_machine_to_serve_as_its_own_model():
    machine = Machine(states=["new", "ready"], initial="new")
    machine.add_transition("prepare", "new", "ready")

    assert machine.prepare() is True
    assert machine.state == "ready"
    assert machine.is_ready() is True


@pytest.mark.parametrize("missing", ["missing", "other", "not_registered"])
def test_unknown_state_lookup_raises_value_error(missing):
    machine = Machine(states=["A"], initial="A")
    with pytest.raises(ValueError):
        machine.get_state(missing)


@pytest.mark.parametrize("ignored", [False, True])
def test_invalid_trigger_obeys_ignore_invalid_triggers(ignored):
    model = type("Model", (), {})()
    machine = Machine(model, states=["A", "B"], initial="B", ignore_invalid_triggers=ignored)
    machine.add_transition("advance", "A", "B")
    if ignored:
        assert model.advance() is False
    else:
        with pytest.raises(MachineError):
            model.advance()


def test_trigger_name_cannot_equal_model_attribute():
    machine = Machine(states=["A", "B"], initial="A")
    with pytest.raises(ValueError):
        machine.add_transition("state", "A", "B")


@pytest.mark.parametrize("bad", [(False, False, False, False), (False, True, False, False), (False, False, True, False)])
def test_factory_supported_combinations_construct_machine(bad):
    graph, nested, locked, asynchronous = bad
    cls = MachineFactory.get_predefined(nested=nested, locked=locked, asyncio=asynchronous)
    if asynchronous:
        async def exercise():
            machine = cls(states=["A", "B"], initial="A")
            assert machine.state == "A"
        asyncio.run(exercise())
    else:
        machine = cls(states=["A", "B"], initial="A")
        assert machine.state == "A"


@pytest.mark.parametrize("tag", ["initial", "approved", "failed"])
def test_tag_feature_exposes_documented_tag_predicates(tag):
    @add_state_features(Tags)
    class TaggedMachine(Machine):
        pass

    machine = TaggedMachine(states=[{"name": "A", "tags": [tag]}], initial="A")
    assert getattr(machine.get_state("A"), "is_" + tag) is True


@pytest.mark.parametrize("name", ["missing", "unknown", "not_registered"])
def test_may_trigger_reports_unknown_names_as_false_when_invalid_triggers_are_ignored(name):
    machine = Machine(states=["A"], initial="A", ignore_invalid_triggers=True)
    assert machine.may_trigger(name) is False
