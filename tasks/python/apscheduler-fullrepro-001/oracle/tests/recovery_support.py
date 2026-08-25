from __future__ import annotations


def new_state():
    from apscheduler.recovery import RecoveryState
    return RecoveryState()


def lane_state(*, two: bool = False):
    state = new_state()
    state.define_lane("ingest", owner="alpha", artifacts=("raw", "log"))
    if two:
        state.define_lane("publish", owner="beta", parents=("ingest",), artifacts=("bundle",))
    return state


def submitted(*, dependencies=(), lane_id="ingest", dispatch_id="d1", scheduled_for=10):
    state = lane_state(two=lane_id == "publish")
    if dependencies:
        for index, dependency in enumerate(dependencies):
            state.submit(dependency, lane_id="ingest", scheduled_for=index, payload_digest=f"p-{dependency}")
    state.submit(dispatch_id, lane_id=lane_id, scheduled_for=scheduled_for, payload_digest=f"p-{dispatch_id}", dependencies=dependencies)
    return state


def completed(state=None, *, dispatch_id="d1", lane_id="ingest", owner="worker-a", now=10, artifacts=("raw",)):
    if state is None:
        state = lane_state(two=lane_id == "publish")
        state.submit(dispatch_id, lane_id=lane_id, scheduled_for=now, payload_digest=f"p-{dispatch_id}")
    lease = state.acquire(dispatch_id, worker=owner, now=now, ttl=10)
    record = state.record_outcome(dispatch_id, lease["token"], outcome="success", finished_at=now + 1, artifacts=artifacts)
    return state, lease, record


def raises(exception, operation):
    try:
        operation()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")
