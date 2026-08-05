import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "depends_on(*names): public dependency map")


@pytest.fixture
def public_api():
    from statemachine import Event
    from statemachine import HistoryState
    from statemachine import State
    from statemachine import StateChart
    from statemachine import StateMachine

    return {
        "Event": Event,
        "HistoryState": HistoryState,
        "State": State,
        "StateChart": StateChart,
        "StateMachine": StateMachine,
    }


class RecordingListener:
    def __init__(self):
        self.entries = []

    def on_enter_state(self, target, event):
        self.entries.append(("enter", str(event), target.id))

    def after_transition(self, event, source, target):
        self.entries.append(("after", str(event), source.id, target.id))


class OrderModel:
    def __init__(self):
        self.items = []
        self.approved = False
        self.total = 0
        self.audit = []

    def has_items(self):
        return bool(self.items)

    def reserve(self, quantity=0, price=0, **kwargs):
        self.total += quantity * price
        self.audit.append(("reserve", quantity, price))
        return self.total

    def mark_approved(self):
        self.approved = True
        return "model-approved"


@pytest.fixture
def traffic_chart_class(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class TrafficLight(StateChart):
        green = State(initial=True)
        yellow = State()
        red = State(final=True)

        cycle = green.to(yellow) | yellow.to(red)

    return TrafficLight


@pytest.fixture
def traffic_chart(traffic_chart_class):
    return traffic_chart_class()


@pytest.fixture
def approval_chart_class(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class ApprovalWorkflow(StateChart):
        pending = State(initial=True)
        approved = State(final=True)
        rejected = State(final=True)

        review = pending.to(approved, cond="is_valid") | pending.to(rejected)

        def is_valid(self, score=0, **kwargs):
            return score >= 70

    return ApprovalWorkflow


@pytest.fixture
def guarded_gate_class(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class GuardedGate(StateChart):
        closed = State(initial=True)
        open = State(final=True)

        enter = closed.to(open, cond="has_badge")

        def has_badge(self, badge=False, **kwargs):
            return badge

    return GuardedGate


@pytest.fixture
def document_chart_class(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class DocumentWorkflow(StateChart):
        class editing(State.Compound):
            draft = State(initial=True)
            review = State()
            submit = draft.to(review)
            revise = review.to(draft)

        published = State(final=True)
        approve = editing.to(published)

    return DocumentWorkflow


@pytest.fixture
def deploy_chart_class(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]

    class DeployPipeline(StateChart):
        class deploy(State.Parallel):
            class build(State.Compound):
                compiling = State(initial=True)
                compiled = State(final=True)
                finish_build = compiling.to(compiled)

            class tests(State.Compound):
                running = State(initial=True)
                passed = State(final=True)
                finish_tests = running.to(passed)

        released = State(final=True)
        done_state_deploy = deploy.to(released)

    return DeployPipeline


@pytest.fixture
def history_chart_class(public_api):
    State = public_api["State"]
    StateChart = public_api["StateChart"]
    HistoryState = public_api["HistoryState"]

    class EditorWithHistory(StateChart):
        class editor(State.Compound):
            source = State(initial=True)
            visual = State()
            h = HistoryState()
            toggle = source.to(visual) | visual.to(source)

        settings = State()
        done = State(final=True)
        open_settings = editor.to(settings)
        back = settings.to(editor.h)
        finish = settings.to(done)

    return EditorWithHistory


@pytest.fixture
def order_model():
    return OrderModel()
