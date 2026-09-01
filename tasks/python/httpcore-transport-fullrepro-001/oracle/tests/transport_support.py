from __future__ import annotations

from dataclasses import replace
import importlib
from pathlib import Path
from typing import Any, Callable


def api() -> Any:
    return importlib.import_module("httpcore.transport_state")


def expect(error: type[BaseException], call: Callable[[], Any]) -> BaseException:
    try: call()
    except error as exc: return exc
    raise AssertionError("expected " + error.__name__)


def route(store: Any, name: str = "origin", *, kind: str = "direct", destination: str = "origin.test:443",
          via: tuple[str, ...] = (), operation: str | None = None, metadata: dict[str, Any] | None = None) -> Any:
    return store.register_route(name, kind, destination, via=via, metadata=metadata or {"tls": destination.endswith(":443")},
                                owner="worker-a", operation_id=operation or "route-" + name)


def lease(store: Any, name: str = "slot", route_name: str = "origin", *, protocol: str = "h1", limit: int = 1,
          owner: str = "worker-a", operation: str | None = None) -> Any:
    return store.acquire(name, route_name, owner=owner, operation_id=operation or "lease-" + name,
                         protocol=protocol, stream_limit=limit)


def exchange(store: Any, capacity: Any, operation: str = "exchange", *, stream_id: int = 1,
             target: str = "/items", body: bytes = b"abc", framing: str = "auto") -> Any:
    return store.begin(capacity, stream_id=stream_id, target=target, body=body, framing=framing, operation_id=operation)


def completed(store: Any, item: Any, *, body: bytes = b"ok", status: int = 200) -> Any:
    return store.receive(item, status=status, headers=(("content-length", str(len(body))),), chunks=(body,), end_stream=True)


def released(store: Any, item: Any, *, reusable: bool = True) -> Any:
    item = store.close_response(item, reusable=reusable)
    while item.cleanup: item = store.discharge(item, item.cleanup[-1])
    return item


def atomic_case(root_id: str, tmp_path: Path) -> None:
    w = api(); store = w.TransportState(tmp_path / "state")
    if root_id == "A09":
        one = route(store); same = route(store)
        assert one == same and one.kind == "direct" and one.generation == 1 and len(one.receipt.digest) == 64
        expect(w.ConflictError, lambda: store.register_route("other", "direct", "x", via=("missing",), owner="worker-a", operation_id="bad"))
    elif root_id == "A10":
        route(store); cap = lease(store); moved = store.handoff(cap, new_owner="worker-b", operation_id="move")
        assert moved.owner == "worker-b" and moved.generation == cap.generation + 1 and moved.partition == cap.partition
        expect(w.OwnershipError, lambda: exchange(store, cap))
    elif root_id == "A11":
        route(store); cap = lease(store); item = exchange(store, cap, body=b"abcd")
        assert item.framing == "content-length:4" and item.target == "/items"
        expect(w.ConflictError, lambda: store.begin(cap, stream_id=3, target="/bad", body=b"x", framing="content-length:2", operation_id="bad"))
    elif root_id == "A12":
        route(store); cap = lease(store, protocol="h2", limit=3); item = exchange(store, cap, stream_id=1)
        grown = store.update_window(item, 1024)
        assert grown.stream_id == 1 and grown.window == 66559
        expect(w.ConflictError, lambda: store.begin(cap, stream_id=2, target="/even", operation_id="even"))
    elif root_id == "A13":
        route(store, "proxy", kind="forward-proxy", destination="proxy.test:8080", metadata={"authorization": "Basic abc"})
        cap = lease(store, route_name="proxy"); item = exchange(store, cap, target="http://origin.test/items")
        snapshot = store.route("proxy")
        assert snapshot.kind == "forward-proxy" and dict(snapshot.metadata)["authorization"] == "Basic abc" and item.cleanup == ("connection", "proxy", "response")
    elif root_id == "A14":
        route(store); cap = lease(store); item = store.cancel(exchange(store, cap), category="timeout")
        assert item.state == "timeout" and not item.reusable and item.cleanup[-1] == "response"
        expect(w.IncompleteError, lambda: store.discharge(item, "connection"))
    elif root_id == "A15":
        route(store); cap = lease(store); item = store.receive(exchange(store, cap), status=200, headers=(), chunks=(b"part",), end_stream=False)
        retired = store.close_response(item, reusable=True)
        assert retired.state == "retired" and not retired.reusable
    elif root_id == "A16":
        route(store); cap = lease(store); item = released(store, completed(store, exchange(store, cap)))
        publication = store.publish(item, ("headers", "body", "released"), operation_id="publish")
        reopened = w.TransportState(tmp_path / "state")
        assert reopened.current("origin") == publication and reopened.verify(publication) and publication.events == ("headers", "body", "released")
    else: raise KeyError(root_id)


def integration_case(root_id: str, tmp_path: Path) -> None:
    w = api(); store = w.TransportState(tmp_path / "state")
    route(store, "direct", destination="origin.test:80", metadata={"tls": False})
    route(store, "proxy", kind="forward-proxy", destination="proxy.test:8080", metadata={"authorization": "secret"})
    if root_id == "I05":
        direct = lease(store, "direct-slot", "direct"); proxy = lease(store, "proxy-slot", "proxy")
        assert direct.partition != proxy.partition and store.route("direct").metadata != store.route("proxy").metadata
        assert exchange(store, direct, "d", target="/local").target == "/local" and exchange(store, proxy, "p", target="http://origin.test/local").target.startswith("http://")
    elif root_id == "I06":
        old = store.route("direct")
        expect(w.ConflictError, lambda: store.register_route("direct", "connect-tunnel", "proxy.test", via=("direct",), owner="worker-a", operation_id="cycle"))
        assert store.route("direct") == old
    elif root_id == "I07":
        route(store, "tunnel", kind="connect-tunnel", destination="origin.test:443", via=("proxy",), metadata={"tls": True})
        item = exchange(store, lease(store, "tunnel-slot", "tunnel"), target="/inside")
        assert item.cleanup == ("connection", "proxy", "tls", "response") and store.route("tunnel").via == ("proxy",)
    elif root_id == "I08":
        cap = lease(store, "slot", "direct"); first = exchange(store, cap, "one")
        expect(w.IncompleteError, lambda: exchange(store, cap, "two", stream_id=3)); assert store.recover("one", owner="worker-a") == first
    elif root_id == "I09":
        cap = lease(store, "slot", "direct", protocol="h2", limit=2); one = exchange(store, cap, "one", stream_id=1); two = exchange(store, cap, "two", stream_id=3)
        expect(w.IncompleteError, lambda: exchange(store, cap, "three", stream_id=5))
        one = released(store, completed(store, one)); assert one.reusable and store.recover("two", owner="worker-a") == two
    elif root_id == "I10":
        cap = lease(store, "slot", "direct"); moved = store.handoff(cap, new_owner="worker-b", operation_id="move")
        expect(w.OwnershipError, lambda: exchange(store, cap, "stale")); assert exchange(store, moved, "fresh").owner == "worker-b"
    elif root_id == "I11":
        cap = lease(store, "slot", "direct")
        expect(w.ConflictError, lambda: exchange(store, cap, "bad", body=b"abc", framing="content-length:2"))
        assert exchange(store, cap, "good", body=b"abc").framing == "content-length:3"
    elif root_id == "I12":
        cap = lease(store, "slot", "direct"); partial = store.receive(exchange(store, cap), status=200, headers=(), chunks=(b"xx",), end_stream=False)
        retired = store.close_response(partial, reusable=True); assert retired.state == "retired"
        replacement = lease(store, "slot", "direct", operation="replacement"); assert replacement.generation > cap.generation
    elif root_id == "I13":
        cap = lease(store, "slot", "direct"); done = released(store, completed(store, exchange(store, cap)))
        publication = store.publish(done, ("response-complete", "capacity-idle"), operation_id="pub")
        assert store.current("direct") == publication and publication.body_digest
    elif root_id == "I14":
        cap = lease(store, "slot", "direct", protocol="h2", limit=2); one = exchange(store, cap, "one", stream_id=1); two = exchange(store, cap, "two", stream_id=3)
        failed = store.cancel(one); healthy = completed(store, two, body=b"sibling")
        assert failed.stream_id == 1 and healthy.stream_id == 3 and healthy.body == b"sibling" and healthy.state == "complete"
    elif root_id == "I15":
        cap = lease(store, "slot", "direct", protocol="h2", limit=2); one = exchange(store, cap, "one", stream_id=1); two = exchange(store, cap, "two", stream_id=3)
        one2 = store.update_window(one, 10); assert one2.window == one.window + 10 and store.recover("two", owner="worker-a").window == two.window
    elif root_id == "I16":
        cap = lease(store, "slot", "proxy"); item = exchange(store, cap, target="http://origin.test/a")
        expect(w.TransportStateError, lambda: store.begin(cap, stream_id=3, target="origin.test/a", operation_id="bad"))
        assert item.route == "proxy" and dict(store.route("proxy").metadata)["authorization"] == "secret"
    elif root_id == "I17":
        route(store, "tunnel", kind="connect-tunnel", destination="origin.test:443", via=("proxy",), metadata={"tls": True})
        item = store.cancel(exchange(store, lease(store, "slot", "tunnel")))
        for action in ("response", "tls", "proxy", "connection"): item = store.discharge(item, action)
        assert item.cleanup == () and item.state == "cancelled"
    elif root_id == "I18":
        healthy = released(store, completed(store, exchange(store, lease(store, "d", "direct"), "healthy")))
        published = store.publish(healthy, ("ok",), operation_id="healthy-pub")
        failed = store.cancel(exchange(store, lease(store, "p", "proxy"), "failed"), category="timeout")
        assert store.current("direct") == published and failed.route == "proxy"
    elif root_id == "I19":
        cap = lease(store, "slot", "direct"); item = exchange(store, cap); moved = store.handoff(cap, new_owner="worker-b", operation_id="move")
        expect(w.OwnershipError, lambda: store.receive(item, status=200, headers=(), chunks=(), end_stream=True))
        assert moved.owner == "worker-b"
    elif root_id == "I20":
        old = released(store, completed(store, exchange(store, lease(store, "slot", "direct"), "old"), body=b"old")); published = store.publish(old, ("old",), operation_id="old-pub")
        partial = store.receive(exchange(store, lease(store, "slot", "direct", operation="next-lease"), "next"), status=200, headers=(), chunks=(b"new",), end_stream=False)
        store.close_response(partial, reusable=True); assert store.current("direct") == published
    elif root_id == "I21":
        done = released(store, completed(store, exchange(store, lease(store, "slot", "direct")), body=b"abc"))
        pub = store.publish(done, ("request", "headers", "body", "release"), operation_id="pub")
        assert pub.events == ("request", "headers", "body", "release") and store.verify(pub)
    elif root_id == "I22":
        cap = lease(store, "slot", "direct"); item = store.receive(exchange(store, cap, "op"), status=206, headers=(("x", "1"),), chunks=(b"part",), end_stream=False)
        reopened = w.TransportState(tmp_path / "state"); assert reopened.recover("op", owner="worker-a") == item
    elif root_id == "I23":
        route_file = tmp_path / "state" / "transport-state.json"; route_file.write_bytes(b"{broken")
        expect(w.IntegrityError, lambda: w.TransportState(tmp_path / "state"))
    elif root_id == "I24":
        old = store.route("direct"); new = store.register_route("direct", "direct", "replacement.test:80", metadata={"tls": False}, owner="worker-a", operation_id="replace")
        assert new.generation == old.generation + 1 and lease(store, "new", "direct").partition != lease(store, "old-view", "proxy").partition
    else: raise KeyError(root_id)


def system_case(root_id: str, tmp_path: Path) -> None:
    w = api(); store = w.TransportState(tmp_path / "state")
    route(store, "direct", destination="origin.test:80", metadata={"tls": False})
    route(store, "proxy", kind="forward-proxy", destination="proxy.test:8080", metadata={"authorization": "secret"})
    if root_id == "S03":
        cap = lease(store, "slot", "direct"); item = exchange(store, cap, "exchange", body=b"request")
        item = completed(store, item, body=b"response"); item = released(store, item)
        pub = store.publish(item, ("acquire", "write", "read", "release"), operation_id="publish")
        assert w.TransportState(tmp_path / "state").verify(pub) and store.current("direct") == pub
    elif root_id == "S04":
        old = released(store, completed(store, exchange(store, lease(store, "d", "direct"), "old"), body=b"old")); old_pub = store.publish(old, ("old",), operation_id="old-pub")
        bad = store.receive(exchange(store, lease(store, "p", "proxy"), "bad", target="http://origin.test/"), status=502, headers=(), chunks=(b"partial",), end_stream=False)
        bad = store.close_response(bad, reusable=True); expect(w.IncompleteError, lambda: store.publish(bad, ("bad",), operation_id="bad-pub"))
        assert store.current("direct") == old_pub and bad.state == "retired"
    elif root_id == "S05":
        cap = lease(store, "slot", "direct"); moved = store.handoff(cap, new_owner="worker-b", operation_id="move")
        expect(w.OwnershipError, lambda: exchange(store, cap, "stale")); item = exchange(store, moved, "fresh")
        reopened = w.TransportState(tmp_path / "state"); item = reopened.recover("fresh", owner="worker-b")
        item = released(reopened, completed(reopened, item)); assert reopened.verify(reopened.publish(item, ("handoff", "done"), operation_id="pub"))
    elif root_id == "S06":
        cap = lease(store, "slot", "direct", protocol="h2", limit=2); one = exchange(store, cap, "one", stream_id=1); two = exchange(store, cap, "two", stream_id=3)
        one = store.cancel(one, category="reset"); two = released(store, completed(store, two, body=b"healthy")); pub = store.publish(two, ("stream-3", "done"), operation_id="pub")
        assert one.state == "reset" and store.current("direct") == pub
    elif root_id == "S07":
        route(store, "tunnel", kind="connect-tunnel", destination="origin.test:443", via=("proxy",), metadata={"tls": True})
        item = store.cancel(exchange(store, lease(store, "slot", "tunnel"), "op"), category="tls-failure")
        reopened = w.TransportState(tmp_path / "state"); item = reopened.recover("op", owner="worker-a")
        for action in ("response", "tls", "proxy", "connection"): item = reopened.discharge(item, action)
        assert item.cleanup == () and item.state == "tls-failure"
    elif root_id == "S08":
        first = released(store, completed(store, exchange(store, lease(store, "slot", "direct"), "first"), body=b"one")); first_pub = store.publish(first, ("one",), operation_id="first-pub")
        replacement = store.register_route("direct", "direct", "new.test:80", metadata={"tls": False}, owner="worker-a", operation_id="new-route")
        second = released(store, completed(store, exchange(store, lease(store, "slot", "direct", operation="new-lease"), "second"), body=b"two")); second_pub = store.publish(second, ("two",), operation_id="second-pub")
        assert replacement.generation == 2 and second_pub.generation == first_pub.generation + 1 and store.current("direct") == second_pub
    else: raise KeyError(root_id)
