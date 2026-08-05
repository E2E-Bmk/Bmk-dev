import asyncio

import pytest

from conftest import OrderModel
from conftest import RecordingListener
from statemachine import Event
from statemachine import State
from statemachine import StateChart


def ids(items):
    return [item.id for item in items]


def value_set(machine):
    return set(machine.configuration_values)


@pytest.mark.depends_on("test_conditional_transition_uses_first_passing_guard")
@pytest.mark.depends_on("test_model_method_can_supply_transition_action")
@pytest.mark.depends_on("test_class_listener_factory_creates_fresh_listener")
def test_order_workflow_combines_guards_model_actions_and_listener(order_model):
    class AuditListener:
        def __init__(self):
            self.log = []

        def after_transition(self, event, source, target):
            self.log.append((str(event), source.id, target.id))

    class OrderWorkflow(StateChart):
        listeners = [AuditListener]
        draft = State(initial=True)
        reserved = State()
        approved = State(final=True)
        rejected = State(final=True)

        reserve = draft.to(reserved, cond="has_items", on="reserve")
        review = reserved.to(approved, cond="is_approved") | reserved.to(rejected)

        def is_approved(self):
            return self.model.approved

    order_model.items.append("sku-1")
    sm = OrderWorkflow(model=order_model)
    result = sm.send("reserve", quantity=2, price=5)
    assert result == 10 or result == [None, 10]
    order_model.approved = True
    sm.send("review")
    assert value_set(sm) == {"approved"}
    assert order_model.audit == [("reserve", 2, 5)]
    assert sm.active_listeners[0].log == [
        ("reserve", "draft", "reserved"),
        ("review", "reserved", "approved"),
    ]


@pytest.mark.depends_on("test_initial_configuration_contains_initial_state")
def test_compound_state_enters_parent_and_initial_child(document_chart_class):
    sm = document_chart_class()
    assert value_set(sm) == {"editing", "draft"}


@pytest.mark.depends_on("test_send_advances_to_next_state")
def test_compound_child_transition_keeps_parent_active(document_chart_class):
    sm = document_chart_class()
    sm.send("submit")
    assert value_set(sm) == {"editing", "review"}


@pytest.mark.depends_on("test_final_state_sets_termination_and_final_states")
def test_compound_parent_transition_exits_children(document_chart_class):
    sm = document_chart_class()
    sm.send("submit")
    sm.send("approve")
    assert value_set(sm) == {"published"}
    assert sm.is_terminated is True


@pytest.mark.depends_on("test_self_transition_runs_exit_enter_callbacks")
def test_compound_cross_boundary_callbacks_use_documented_order(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class HierarchicalExample(StateChart):
        class parent_a(State.Compound):
            child_a = State(initial=True)

        class parent_b(State.Compound):
            child_b = State(initial=True, final=True)

        cross = parent_a.to(parent_b)

        def __init__(self):
            self.log = []
            super().__init__()

        def on_exit_child_a(self):
            self.log.append("exit child")

        def on_exit_parent_a(self):
            self.log.append("exit parent")

        def on_enter_parent_b(self):
            self.log.append("enter parent")

        def on_enter_child_b(self):
            self.log.append("enter child")

    sm = HierarchicalExample()
    sm.log.clear()
    sm.send("cross")
    assert sm.log == ["exit child", "exit parent", "enter parent", "enter child"]
    assert value_set(sm) == {"parent_b", "child_b"}


@pytest.mark.depends_on("test_initial_configuration_contains_initial_state")
def test_parallel_state_enters_each_region_initial(deploy_chart_class):
    sm = deploy_chart_class()
    assert {"deploy", "build", "compiling", "tests", "running"} <= value_set(sm)


@pytest.mark.depends_on("test_send_advances_to_next_state")
def test_parallel_region_transition_preserves_other_region(deploy_chart_class):
    sm = deploy_chart_class()
    sm.send("finish_build")
    assert {"deploy", "build", "compiled", "tests", "running"} <= value_set(sm)
    assert "released" not in value_set(sm)


@pytest.mark.depends_on("test_final_state_sets_termination_and_final_states")
def test_parallel_done_event_waits_for_all_regions(deploy_chart_class):
    sm = deploy_chart_class()
    sm.send("finish_build")
    sm.send("finish_tests")
    assert value_set(sm) == {"released"}
    assert sm.is_terminated is True


@pytest.mark.depends_on('test_send_advances_to_next_state')
def test_history_state_restores_previous_child(history_chart_class):
    sm = history_chart_class()
    sm.send("toggle")
    sm.send("open_settings")
    assert value_set(sm) == {"settings"}
    sm.send("back")
    assert value_set(sm) == {"editor", "visual"}


@pytest.mark.depends_on("test_internal_transition_skips_exit_enter_callbacks")
def test_eventless_transition_fires_after_report_count_changes(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class AutoEscalation(StateChart):
        normal = State(initial=True)
        escalated = State(final=True)
        normal.to(escalated, cond="should_escalate")
        report = normal.to.itself(internal=True, on="add_report")

        def __init__(self):
            self.report_count = 0
            super().__init__()

        def should_escalate(self):
            return self.report_count >= 3

        def add_report(self):
            self.report_count += 1

    sm = AutoEscalation()
    sm.send("report")
    sm.send("report")
    assert value_set(sm) == {"normal"}
    sm.send("report")
    assert value_set(sm) == {"escalated"}


@pytest.mark.depends_on('test_final_state_sets_termination_and_final_states')
def test_done_state_event_advances_compound_parent(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class QuestWithDone(StateChart):
        class quest(State.Compound):
            traveling = State(initial=True)
            arrived = State(final=True)
            finish = traveling.to(arrived)

        celebration = State(final=True)
        done_state_quest = quest.to(celebration)

    sm = QuestWithDone()
    sm.send("finish")
    assert value_set(sm) == {"celebration"}


@pytest.mark.depends_on("test_donedata_requires_final_state")
def test_donedata_reaches_done_state_handler(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]
    Event = public_api["Event"]

    class QuestCompletion(StateChart):
        class quest(State.Compound):
            traveling = State(initial=True)
            completed = State(final=True, donedata="get_result")
            finish = traveling.to(completed)

            def get_result(self):
                return {"hero": "frodo", "outcome": "victory"}

        epilogue = State(final=True)
        done_state_quest = Event(quest.to(epilogue, on="capture_result"))

        def capture_result(self, hero=None, outcome=None, **kwargs):
            self.result = f"{hero}:{outcome}"

    sm = QuestCompletion()
    sm.send("finish")
    assert sm.result == "frodo:victory"
    assert value_set(sm) == {"epilogue"}


@pytest.mark.depends_on("test_state_chart_ignores_unmatched_event_by_default")
def test_error_execution_event_can_recover_from_action_error(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class ResilientChart(StateChart):
        working = State(initial=True)
        failed = State(final=True)
        go = working.to.itself(on="do_work")
        error_execution = working.to(failed)

        def do_work(self):
            raise RuntimeError("boom")

    sm = ResilientChart()
    sm.send("go")
    assert value_set(sm) == {"failed"}


@pytest.mark.depends_on("test_send_advances_to_next_state")
def test_raise_internal_event_completes_pipeline_in_one_send(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class Pipeline(StateChart):
        start = State(initial=True)
        step1 = State()
        step2 = State()
        done = State(final=True)
        begin = start.to(step1)
        advance_1 = step1.to(step2)
        advance_2 = step2.to(done)

        def on_enter_step1(self):
            self.raise_("advance_1")

        def on_enter_step2(self):
            self.raise_("advance_2")

    sm = Pipeline()
    sm.send("begin")
    assert ids(sm.configuration) == ["done"]


@pytest.mark.depends_on("test_before_and_on_return_values_are_collected")
def test_on_callback_receives_previous_and_new_configuration(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class InspectConfig(StateChart):
        off = State(initial=True)
        on = State(final=True)
        switch = off.to(on, on="check_config")

        def check_config(self, previous_configuration, new_configuration):
            self.previous_ids = {state.id for state in previous_configuration}
            self.new_ids = {state.id for state in new_configuration}

    sm = InspectConfig()
    sm.send("switch")
    assert sm.previous_ids == {"off"}
    assert sm.new_ids == {"on"}


@pytest.mark.depends_on("test_internal_transition_skips_exit_enter_callbacks")
def test_async_callback_can_be_used_from_synchronous_context(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class AsyncStateMachine(StateChart):
        initial = State(initial=True)
        final = State(final=True)
        keep = initial.to.itself(internal=True)
        advance = initial.to(final)

        async def on_advance(self):
            return 42

    sm = AsyncStateMachine()
    assert sm.advance() == 42
    assert list(sm.configuration_values) == ["final"]


@pytest.mark.depends_on("test_initial_configuration_contains_initial_state")
def test_async_initial_state_activation_is_explicit_inside_event_loop(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class AsyncStateMachine(StateChart):
        initial = State(initial=True)
        final = State(final=True)
        advance = initial.to(final)

        async def on_advance(self):
            return "advanced"

    async def scenario():
        sm = AsyncStateMachine()
        before = list(sm.configuration_values)
        await sm.activate_initial_state()
        after = list(sm.configuration_values)
        return before, after

    before, after = asyncio.run(scenario())
    assert before == []
    assert after == ["initial"]


@pytest.mark.depends_on("test_internal_transition_skips_exit_enter_callbacks")
def test_async_first_event_auto_activates_initial_state(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class AsyncStateMachine(StateChart):
        initial = State(initial=True)
        final = State(final=True)
        keep = initial.to.itself(internal=True)
        advance = initial.to(final)

        async def on_advance(self):
            return "advanced"

    async def scenario():
        sm = AsyncStateMachine()
        await sm.keep()
        return list(sm.configuration_values)

    assert asyncio.run(scenario()) == ["initial"]


@pytest.mark.depends_on("test_enabled_events_evaluate_guards")
def test_enabled_event_projection_matches_guarded_send(guarded_gate_class):
    sm = guarded_gate_class()
    assert ids(sm.enabled_events(badge=True)) == ["enter"]
    sm.send("enter", badge=True)
    assert value_set(sm) == {"open"}


@pytest.mark.depends_on("test_class_listener_factory_creates_fresh_listener")
def test_runtime_listener_observes_events_after_attachment(traffic_chart):
    listener = RecordingListener()
    returned = traffic_chart.add_listener(listener)
    assert returned is traffic_chart
    traffic_chart.send("cycle")
    assert ("after", "cycle", "green", "yellow") in listener.entries
    assert ("enter", "cycle", "yellow") in listener.entries


@pytest.mark.depends_on("test_class_listener_factory_creates_fresh_listener")
def test_listener_inheritance_appends_child_listeners(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class BaseListener:
        pass

    class ChildListener:
        pass

    class BaseMachine(StateChart):
        listeners = [BaseListener]
        a = State(initial=True)
        b = State(final=True)
        go = a.to(b)

    class ChildMachine(BaseMachine):
        listeners = [ChildListener]

    sm = ChildMachine()
    assert [type(listener).__name__ for listener in sm.active_listeners] == [
        "BaseListener",
        "ChildListener",
    ]


@pytest.mark.depends_on("test_model_method_can_supply_transition_action")
def test_model_registered_as_listener_supplies_guard_and_action(order_model):
    class ModelDrivenOrder(StateChart):
        pending = State(initial=True)
        approved = State(final=True)
        approve = pending.to(approved, cond="has_items", on="mark_approved")

    order_model.items.append("sku-2")
    sm = ModelDrivenOrder(model=order_model)
    assert sm.approve() == "model-approved"
    assert order_model.approved is True
    assert value_set(sm) == {"approved"}


@pytest.mark.depends_on('test_final_state_sets_termination_and_final_states')
def test_cross_boundary_transition_enters_sibling_compound_initial(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class OrderFulfillment(StateChart):
        class picking(State.Compound):
            locating = State(initial=True)
            packing = State()
            locate = locating.to(packing)

        class shipping(State.Compound):
            labeling = State(initial=True)
            dispatched = State(final=True)
            dispatch = labeling.to(dispatched)

        ship = picking.to(shipping)

    sm = OrderFulfillment()
    assert value_set(sm) == {"picking", "locating"}
    sm.send("ship")
    assert value_set(sm) == {"shipping", "labeling"}


@pytest.mark.depends_on("test_conditional_transition_uses_first_passing_guard")
def test_descendant_transition_takes_priority_over_ancestor(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class OrderProcessing(StateChart):
        class fulfillment(State.Compound):
            class picking(State.Compound):
                s1 = State(initial=True)
                s2 = State()
                go = s1.to(s2, on="log_picking")
                back = s2.to(s1)

            packed = State(final=True)
            done_state_picking = picking.to(packed)

        shipped = State(final=True)
        go = fulfillment.to(shipped, on="log_parent")
        done_state_fulfillment = fulfillment.to(shipped)

        def __init__(self):
            self.log = []
            super().__init__()

        def log_picking(self):
            self.log.append("picking")

        def log_parent(self):
            self.log.append("parent")

    sm = OrderProcessing()
    sm.send("go")
    assert sm.log == ["picking"]
    assert "shipped" not in value_set(sm)


@pytest.mark.depends_on("test_single_callback_return_is_unwrapped")
def test_transition_decorator_declares_event_with_inline_action(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class Turnstile(StateChart):
        locked = State(initial=True)
        unlocked = State()
        finished = State(final=True)
        push = unlocked.to(locked)
        finish = unlocked.to(finished)

        @locked.to(unlocked)
        def coin(self):
            return "accepted"

    sm = Turnstile()
    assert isinstance(Turnstile.coin, Event)
    assert sm.send("coin") == "accepted"
    assert value_set(sm) == {"unlocked"}


@pytest.mark.depends_on("test_declared_transition_becomes_event")
def test_markdown_projection_contains_same_declared_states_and_event(traffic_chart):
    rendered = f"{traffic_chart:md}"
    assert "Green" in rendered
    assert "Yellow" in rendered
    assert "Red" in rendered
    assert "Cycle" in rendered


@pytest.mark.depends_on("test_before_and_on_return_values_are_collected")
def test_dependency_injection_projects_event_source_target_and_model(order_model):
    class ContextMachine(StateChart):
        idle = State(initial=True)
        active = State(final=True)
        activate = idle.to(active, on="capture")

        def capture(self, event, source, target, model, machine):
            model.audit.append((str(event), source.id, target.id, machine is self))
            return model.audit[-1]

    sm = ContextMachine(model=order_model)
    assert sm.activate() == ("activate", "idle", "active", True)
    assert order_model.audit == [("activate", "idle", "active", True)]


@pytest.mark.depends_on("test_validator_exception_propagates_and_keeps_state")
def test_validators_run_before_conditions(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class CombinedGuards(StateChart):
        idle = State(initial=True)
        active = State(final=True)
        start = idle.to(active, validators="check_auth", cond="has_permission")
        has_permission = False

        def check_auth(self, token=None, **kwargs):
            if token != "valid":
                raise PermissionError("bad token")

    sm = CombinedGuards()
    with pytest.raises(PermissionError):
        sm.send("start", token="bad")
    sm.has_permission = True
    sm.send("start", token="valid")
    assert value_set(sm) == {"active"}


@pytest.mark.depends_on("test_prepare_event_enriches_action_arguments")
def test_prepare_event_values_reach_guard_and_action(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class PreparedGuard(StateChart):
        waiting = State(initial=True)
        accepted = State(final=True)
        accept = waiting.to(accepted, cond="large_enough", on="record")

        def prepare_event(self, amount=0):
            if amount is None:
                return {}
            return {"normalized": amount * 2}

        def large_enough(self, normalized=0):
            return normalized >= 10

        def record(self, normalized=0):
            self.normalized = normalized

    sm = PreparedGuard()
    sm.send("accept", amount=4)
    assert value_set(sm) == {"waiting"}
    sm.send("accept", amount=6)
    assert sm.normalized == 12
    assert value_set(sm) == {"accepted"}
