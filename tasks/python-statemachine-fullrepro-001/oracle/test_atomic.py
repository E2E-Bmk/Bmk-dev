import pytest

from conftest import OrderModel
from statemachine import Event
from statemachine import State
from statemachine import StateChart
from statemachine import StateMachine
from statemachine.exceptions import InvalidDefinition
from statemachine.exceptions import TransitionNotAllowed


def ids(items):
    return [item.id for item in items]


def values(machine):
    return list(machine.configuration_values)


def test_public_imports_expose_documented_runtime_classes(public_api):
    assert public_api["StateChart"] is StateChart
    assert public_api["StateMachine"] is StateMachine
    assert public_api["State"] is State
    assert public_api["Event"] is Event


def test_state_metadata_defaults_and_custom_values(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class CampaignMachine(StateChart):
        draft = State("Draft", value=1, initial=True)
        producing = State("Being produced", value=2)
        closed = State("Closed", value=3, final=True)
        produce = draft.to(producing)
        deliver = producing.to(closed)

    sm = CampaignMachine()
    assert CampaignMachine.draft.id == "draft"
    assert CampaignMachine.draft.name == "Draft"
    assert CampaignMachine.closed.final is True
    assert values(sm) == [1]


def test_declared_transition_becomes_event(traffic_chart_class):
    assert isinstance(traffic_chart_class.cycle, Event)
    assert traffic_chart_class.cycle.id == "cycle"
    assert traffic_chart_class.cycle.name == "Cycle"


def test_initial_configuration_contains_initial_state(traffic_chart):
    assert ids(traffic_chart.configuration) == ["green"]
    assert values(traffic_chart) == ["green"]
    assert traffic_chart.green.is_active is True


def test_send_advances_to_next_state(traffic_chart):
    result = traffic_chart.send("cycle")
    assert result is None
    assert values(traffic_chart) == ["yellow"]


def test_event_method_call_matches_send(traffic_chart):
    traffic_chart.cycle()
    traffic_chart.cycle()
    assert values(traffic_chart) == ["red"]
    assert traffic_chart.is_terminated is True


def test_allowed_events_are_topology_based(traffic_chart):
    assert ids(traffic_chart.allowed_events) == ["cycle"]
    traffic_chart.send("cycle")
    assert ids(traffic_chart.allowed_events) == ["cycle"]


def test_enabled_events_evaluate_guards(guarded_gate_class):
    sm = guarded_gate_class()
    assert ids(sm.allowed_events) == ["enter"]
    assert ids(sm.enabled_events()) == []
    assert ids(sm.enabled_events(badge=True)) == ["enter"]


def test_conditional_transition_uses_first_passing_guard(approval_chart_class):
    sm = approval_chart_class()
    sm.send("review", score=85)
    assert values(sm) == ["approved"]


def test_conditional_transition_falls_back_when_guard_fails(approval_chart_class):
    sm = approval_chart_class()
    sm.send("review", score=50)
    assert values(sm) == ["rejected"]


def test_unless_guard_blocks_until_predicate_is_false(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class MaintenanceGate(StateChart):
        idle = State(initial=True)
        running = State(final=True)
        start = idle.to(running, unless="blocked")
        blocked = True

    sm = MaintenanceGate()
    sm.send("start")
    assert values(sm) == ["idle"]
    sm.blocked = False
    sm.send("start")
    assert values(sm) == ["running"]


def test_validator_exception_propagates_and_keeps_state(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class OrderMachine(StateChart):
        pending = State(initial=True)
        confirmed = State(final=True)
        confirm = pending.to(confirmed, validators="check_stock")

        def check_stock(self, quantity=0, **kwargs):
            if quantity <= 0:
                raise ValueError("quantity must be positive")

    sm = OrderMachine()
    with pytest.raises(ValueError):
        sm.send("confirm", quantity=0)
    assert values(sm) == ["pending"]
    sm.send("confirm", quantity=2)
    assert values(sm) == ["confirmed"]


def test_prepare_event_enriches_action_arguments(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class OrderFlow(StateChart):
        pending = State(initial=True)
        confirmed = State(final=True)
        confirm = pending.to(confirmed)

        def prepare_event(self, order_id=None):
            if order_id is None:
                return {}
            return {"order_total": order_id * 10}

        def on_confirm(self, order_total=0):
            return f"confirmed:{order_total}"

    sm = OrderFlow()
    assert sm.send("confirm", order_id=5) == "confirmed:50"


def test_before_and_on_return_values_are_collected(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class ReturnExample(StateChart):
        a = State(initial=True)
        b = State(final=True)
        go = a.to(b)

        def before_go(self):
            return "before"

        def on_go(self):
            return "on"

        def after_go(self):
            return "ignored"

    assert ReturnExample().send("go") == ["before", "on"]


def test_single_callback_return_is_unwrapped(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class SingleReturn(StateChart):
        a = State(initial=True)
        b = State(final=True)
        go = a.to(b, on="do_it")

        def do_it(self):
            return 42

    assert SingleReturn().send("go") == 42


def test_missing_callback_return_is_none(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class NoReturn(StateChart):
        a = State(initial=True)
        b = State(final=True)
        go = a.to(b)

    assert NoReturn().send("go") is None


def test_state_machine_rejects_unmatched_event_by_default(public_api):
    State = public_api["State"]
    StateMachine = public_api["StateMachine"]

    class StrictMachine(StateMachine):
        idle = State(initial=True)
        done = State(final=True)
        finish = idle.to(done)

    with pytest.raises(TransitionNotAllowed):
        StrictMachine().send("missing")


def test_state_chart_ignores_unmatched_event_by_default(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class TolerantChart(StateChart):
        idle = State(initial=True)
        done = State(final=True)
        finish = idle.to(done)

    sm = TolerantChart()
    assert sm.send("missing") is None
    assert values(sm) == ["idle"]


def test_final_state_sets_termination_and_final_states(traffic_chart):
    traffic_chart.send("cycle")
    traffic_chart.send("cycle")
    assert traffic_chart.is_terminated is True
    assert ids(traffic_chart.final_states) == ["red"]


def test_explicit_event_name_preserves_programmatic_id(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]
    Event = public_api["Event"]

    class SimpleMachine(StateChart):
        on = State(initial=True)
        off = State(final=True)
        shut_down = Event(on.to(off), name="Shut the system down")

    assert SimpleMachine.shut_down.id == "shut_down"
    assert SimpleMachine.shut_down.name == "Shut the system down"


def test_from_any_creates_global_transition(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class OrderWorkflow(StateChart):
        pending = State(initial=True)
        processing = State()
        done = State()
        completed = State(final=True)
        cancelled = State(final=True)
        process = pending.to(processing)
        complete = processing.to(done)
        finish = done.to(completed)
        cancel = cancelled.from_.any()

    sm = OrderWorkflow()
    sm.send("process")
    sm.send("cancel")
    assert values(sm) == ["cancelled"]


def test_self_transition_runs_exit_enter_callbacks(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class RetryOrder(StateChart):
        processing = State(initial=True)
        done = State(final=True)
        retry = processing.to.itself(on="record")
        finish = processing.to(done)

        def __init__(self):
            self.log = []
            super().__init__()

        def on_exit_processing(self):
            self.log.append("exit")

        def record(self):
            self.log.append("on")

        def on_enter_processing(self):
            self.log.append("enter")

    sm = RetryOrder()
    sm.log.clear()
    sm.send("retry")
    assert sm.log == ["exit", "on", "enter"]


def test_internal_transition_skips_exit_enter_callbacks(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class Cart(StateChart):
        shopping = State(initial=True)
        checkout = State(final=True)
        add_item = shopping.to.itself(internal=True, on="add")
        pay = shopping.to(checkout)

        def __init__(self):
            self.log = []
            super().__init__()

        def on_exit_shopping(self):
            self.log.append("exit")

        def add(self, price=0):
            self.log.append(("add", price))

        def on_enter_shopping(self):
            self.log.append("enter")

    sm = Cart()
    sm.log.clear()
    sm.send("add_item", price=9)
    assert ("exit" not in sm.log) and (("add", 9) in sm.log)
    assert values(sm) == ["shopping"]


def test_model_method_can_supply_transition_action(public_api, order_model):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class OrderMachine(StateChart):
        pending = State(initial=True)
        reserved = State(final=True)
        reserve = pending.to(reserved, on="reserve")

    sm = OrderMachine(model=order_model)
    result = sm.send("reserve", quantity=3, price=4)
    assert result == 12 or result == [None, 12]
    assert order_model.audit == [("reserve", 3, 4)]


def test_class_listener_factory_creates_fresh_listener(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class AuditListener:
        def __init__(self):
            self.log = []

        def after_transition(self, event, source, target):
            self.log.append((str(event), source.id, target.id))

    class AuditedMachine(StateChart):
        listeners = [AuditListener]
        a = State(initial=True)
        b = State(final=True)
        go = a.to(b)

    first = AuditedMachine()
    second = AuditedMachine()
    first.send("go")
    assert first.active_listeners[0].log == [("go", "a", "b")]
    assert second.active_listeners[0].log == []


def test_two_root_initial_states_are_invalid(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    with pytest.raises(InvalidDefinition):

        class Bad(StateChart):
            a = State(initial=True)
            b = State(initial=True)
            go = a.to(b)


def test_final_states_cannot_have_outgoing_transitions(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    with pytest.raises(InvalidDefinition):

        class Bad(StateChart):
            draft = State(initial=True)
            closed = State(final=True)
            close = draft.to(closed)
            reopen = closed.to(draft)


def test_unreachable_state_definition_is_invalid(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    with pytest.raises(InvalidDefinition):

        class Bad(StateChart):
            red = State(initial=True)
            green = State()
            hazard = State()
            cycle = red.to(green) | green.to(red)
            blink = hazard.to.itself()


def test_named_callback_resolution_is_validated_on_instance_creation(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class BrokenCallback(StateChart):
        a = State(initial=True)
        b = State(final=True)
        go = a.to(b, on="nonexistent_method")

    with pytest.raises(InvalidDefinition):
        BrokenCallback()


def test_donedata_requires_final_state(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    with pytest.raises(InvalidDefinition):

        class BadDoneData(StateChart):
            a = State(initial=True, donedata="data")
            b = State(final=True)
            go = a.to(b)


def test_invalid_listener_entries_are_rejected(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    with pytest.raises(InvalidDefinition):

        class BadListener(StateChart):
            listeners = ["not_a_listener"]
            a = State(initial=True)
            b = State(final=True)
            go = a.to(b)
