from __future__ import annotations

import copy


def raises(exc_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except exc_type as exc:
        return exc
    except BaseException as exc:
        raise AssertionError(f"expected {exc_type.__name__}, got {type(exc).__name__}") from exc
    raise AssertionError(f"expected {exc_type.__name__}")


def api():
    from structlog.delivery import DeliveryState
    return DeliveryState


def processor(name, *after):
    return {"name": name, "after": tuple(after)}


def sink(name, capacity=1, retry_limit=2):
    return {"name": name, "capacity": capacity, "retry_limit": retry_limit}


def configured(*, processors=None, sinks=None, generation="g1"):
    state = api()()
    state.prepare(
        generation,
        processors=processors if processors is not None else [processor("merge"), processor("render", "merge")],
        sinks=sinks if sinks is not None else [sink("primary"), sink("archive", 2, 1)],
    )
    state.activate(generation, expected_active=None)
    context = state.open_context("request", {"request_id": "r-1", "shared": "context"})
    return state, context["token"]


def committed(state, token, event_id="e1", fields=None):
    event = state.begin(event_id, context=token, fields=fields or {"event": "created", "shared": "call"})
    for name in state.configuration(event["generation"])["order"]:
        state.stage(event_id, name, patch={f"seen_{name}": True})
    return state.commit(event_id)


def public_views(state):
    return copy.deepcopy({
        "configurations": state.configurations(),
        "contexts": state.contexts(),
        "events": state.events(),
        "deliveries": state.deliveries(),
        "audit": state.audit(),
        "active": state.active_generation(),
    })
