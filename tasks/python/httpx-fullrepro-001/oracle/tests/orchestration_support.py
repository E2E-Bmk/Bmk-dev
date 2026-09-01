from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Callable


def api() -> Any:
    return importlib.import_module("httpx.orchestration")


def expect(error: type[BaseException], call: Callable[[], Any]) -> BaseException:
    try: call()
    except error as exc: return exc
    raise AssertionError("expected " + error.__name__)


def route(store: Any, name: str = "main", origin: str = "https://a.test/", *,
          proxy: str | None = None, operation: str | None = None) -> Any:
    return store.register_route(name, origin, proxy=proxy, operation_id=operation or "route-" + name)


def lease(store: Any, name: str = "slot", route_name: str = "main", *, owner: str = "worker-a",
          operation: str | None = None) -> Any:
    return store.acquire(name, route_name, owner=owner, operation_id=operation or "lease-" + name)


def transaction(store: Any, capacity: Any, operation: str = "request", *, url: str = "https://a.test/items",
                headers: tuple[tuple[str, str], ...] = (), cookies: tuple[tuple[str, str, str], ...] = (),
                retry_limit: int = 2, redirect_limit: int = 3, circuit_limit: int = 2) -> Any:
    return store.begin(capacity, "GET", url, headers=headers, cookies=cookies, retry_limit=retry_limit,
                       redirect_limit=redirect_limit, circuit_limit=circuit_limit, operation_id=operation)


def stream(store: Any, tx: Any, operation: str = "stream", *, window: int = 8) -> Any:
    return store.open_stream(tx, owner=tx.owner, window=window, operation_id=operation)


def completed(store: Any, item: Any, operation: str = "complete", body: bytes = b"body") -> Any:
    item = store.feed(item, body, operation_id=operation + "-feed")
    return store.complete(item, 200, headers=(("etag", "v1"),), operation_id=operation)


def atomic_case(root_id: str, tmp_path: Path) -> None:
    w = api(); store = w.ClientJournal(tmp_path / "journal")
    if root_id == "A07":
        one = route(store); same = route(store, operation="route-again")
        changed = route(store, origin="https://b.test/", operation="route-change")
        assert one == same and one.generation == 1 and changed.generation == 2 and changed.partition != one.partition
        assert store.verify(changed)
    elif root_id == "A08":
        route(store); old = lease(store); moved = store.handoff(old, new_owner="worker-b", operation_id="move")
        assert moved.fence == old.fence + 1 and moved.owner == "worker-b"
        expect(w.OwnershipError, lambda: transaction(store, old, "stale"))
    elif root_id == "A09":
        route(store); cap = lease(store)
        tx = transaction(store, cap, headers=(("Authorization", "Bearer one"),),
                         cookies=(("sid", "1", "a.test"),))
        assert tx.auth_origin == "https://a.test:443" and tx.cookies[0][2] == "a.test"
        assert tx.lease_fence == cap.fence and tx.history == ("request",)
    elif root_id == "A10":
        route(store); tx = transaction(store, lease(store), headers=(("Authorization", "Bearer one"),),
                                       cookies=(("a", "1", "a.test"),))
        hop = store.redirect(tx, 302, "https://b.test/next", set_cookies=(("b", "2", "b.test"),), operation_id="hop")
        assert hop.method == "GET" and hop.auth_origin is None
        assert all(name.lower() != "authorization" for name, _ in hop.headers) and hop.cookies == (("b", "2", "b.test"),)
    elif root_id == "A11":
        route(store); cap = lease(store); tx = transaction(store, cap, retry_limit=0, circuit_limit=3)
        failed = store.fail(tx, category="connect", operation_id="failed")
        expect(w.BudgetError, lambda: store.retry(failed, cap, operation_id="retry"))
        assert store.recover("failed").state == "retryable"
    elif root_id == "A12":
        route(store); item = stream(store, transaction(store, lease(store)), window=3)
        old = item; expect(w.BudgetError, lambda: store.feed(item, b"four", operation_id="too-much"))
        assert store.recover("stream") == old
        item = store.feed(item, b"abc", operation_id="fit"); assert item.window == 0 and item.received == b"abc"
    elif root_id == "A13":
        route(store); item = stream(store, transaction(store, lease(store)))
        item = store.feed(item, b"part", operation_id="part")
        cancelled = store.cancel(item, reason="cancelled", operation_id="cancel")
        assert cancelled.state == "cancelled" and not cancelled.reusable
        expect(w.IncompleteError, lambda: store.commit(cancelled, operation_id="bad-publish"))
    elif root_id == "A14":
        route(store); item = completed(store, stream(store, transaction(store, lease(store))))
        pub = store.commit(item, cache_key="GET /items", etag="v1", events=("response", "cache"), operation_id="publish")
        cached = store.cached("GET /items")
        assert pub.cache_key == cached.key and cached.generation == 1 and cached.body == b"body" and store.verify(cached)
    elif root_id == "A15":
        route(store, proxy="http://proxy.test:8080"); item = stream(store, transaction(store, lease(store)))
        expect(w.IncompleteError, lambda: store.discharge(item, "tls", owner="worker-a", operation_id="wrong-order"))
        item = store.discharge(item, "response", owner="worker-a", operation_id="response-done")
        assert item.cleanup == ("tls", "proxy", "connection")
    elif root_id == "A16":
        route(store); tx = transaction(store, lease(store)); reopened = w.ClientJournal(tmp_path / "journal")
        recovered = reopened.recover("request")
        assert recovered == tx and reopened.verify(recovered) and reopened.reconcile().valid
    else: raise KeyError(root_id)


def integration_case(root_id: str, tmp_path: Path) -> None:
    w = api(); store = w.ClientJournal(tmp_path / "journal")
    if root_id == "I06":
        direct = route(store, "direct", "https://a.test/")
        proxied = route(store, "proxied", "https://a.test/", proxy="http://proxy.test:8080")
        one = lease(store, "one", "direct"); two = lease(store, "two", "proxied")
        assert direct.partition != proxied.partition and one.partition != two.partition
    elif root_id == "I07":
        route(store); old = lease(store); route(store, origin="https://replacement.test/", operation="route-new")
        expect(w.OwnershipError, lambda: transaction(store, old, "stale"))
        fresh = lease(store, operation="lease-new"); assert fresh.route_generation == 2 and fresh.fence > old.fence
    elif root_id == "I08":
        route(store); old = lease(store); tx = transaction(store, old)
        moved = store.handoff(old, new_owner="worker-b", operation_id="move")
        expect(w.OwnershipError, lambda: stream(store, tx, "stale-stream"))
        fresh = transaction(store, moved, "fresh"); assert fresh.owner == "worker-b"
    elif root_id == "I09":
        route(store); tx = transaction(store, lease(store), url="https://a.test/base/start")
        one = store.redirect(tx, 307, "../next", operation_id="hop-one")
        two = store.redirect(one, 303, "/done", operation_id="hop-two")
        assert one.url == "https://a.test/next" and two.method == "GET" and two.redirects == 2
        assert two.history[-2:] == ("redirect:307:https://a.test/next", "redirect:303:https://a.test/done")
    elif root_id == "I10":
        route(store); tx = transaction(store, lease(store), headers=(("Authorization", "secret"), ("X", "1")),
                                       cookies=(("host", "a", "a.test"), ("dest", "b", "b.test")))
        hop = store.redirect(tx, 307, "https://b.test/path", operation_id="hop")
        assert hop.headers == (("X", "1"),) and hop.cookies == (("dest", "b", "b.test"),) and hop.auth_origin is None
    elif root_id == "I11":
        route(store); tx = transaction(store, lease(store), redirect_limit=1)
        hop = store.redirect(tx, 302, "/one", operation_id="one")
        expect(w.BudgetError, lambda: store.redirect(hop, 302, "/two", operation_id="two"))
        assert store.recover("one") == hop
    elif root_id == "I12":
        route(store); cap = lease(store); tx = transaction(store, cap, retry_limit=2, circuit_limit=4)
        failed = store.fail(tx, category="read", operation_id="failure")
        retried = store.retry(failed, cap, operation_id="retry")
        assert retried.retries == 1 and retried.history[-2:] == ("failure:read", "retry") and retried.state == "active"
    elif root_id == "I13":
        route(store); cap = lease(store); tx = transaction(store, cap, retry_limit=5, circuit_limit=1)
        failed = store.fail(tx, category="connect", operation_id="failure")
        expect(w.BudgetError, lambda: store.retry(failed, cap, operation_id="blocked"))
    elif root_id == "I14":
        route(store, "a", "https://a.test/"); route(store, "b", "https://b.test/")
        cap_a = lease(store, "a-slot", "a"); cap_b = lease(store, "b-slot", "b")
        failed = store.fail(transaction(store, cap_a, "a-request", circuit_limit=1), category="connect", operation_id="a-failed")
        expect(w.BudgetError, lambda: store.retry(failed, cap_a, operation_id="a-retry"))
        healthy = transaction(store, cap_b, "b-request"); assert healthy.route == "b"
    elif root_id == "I15":
        route(store); tx = transaction(store, lease(store), circuit_limit=1)
        store.fail(tx, category="connect", operation_id="failed")
        route(store, origin="https://new.test/", operation="new-route")
        expect(w.ConflictError, lambda: store.heal("main", route_generation=2, operation_id="stale-heal"))
    elif root_id == "I16":
        route(store); item = stream(store, transaction(store, lease(store)), window=4)
        item = store.feed(item, b"abcd", operation_id="feed")
        expect(w.BudgetError, lambda: store.feed(item, b"x", operation_id="blocked"))
        item = store.consume(item, 3, operation_id="consume")
        item = store.feed(item, b"xy", operation_id="resume")
        assert item.received == b"abcdxy" and item.delivered == 3 and item.window == 1
    elif root_id == "I17":
        route(store); cap = lease(store)
        good = completed(store, stream(store, transaction(store, cap, "good-tx"), "good-stream"), "good-complete", b"old")
        published = store.commit(good, cache_key="key", etag="v1", operation_id="good-pub")
        bad = store.feed(stream(store, transaction(store, cap, "bad-tx"), "bad-stream"), b"part", operation_id="bad-part")
        store.cancel(bad, reason="cancelled", operation_id="bad-cancel")
        assert store.current("main") == published and store.cached("key").body == b"old"
    elif root_id == "I18":
        route(store); tx = transaction(store, lease(store)); one = stream(store, tx, "one", window=2); two = stream(store, tx, "two", window=4)
        one = store.feed(one, b"aa", operation_id="one-feed"); one = store.cancel(one, reason="decode-error", operation_id="one-cancel")
        two = completed(store, two, "two-complete", b"ok")
        assert one.state == "decode-error" and two.state == "complete" and two.received == b"ok"
    elif root_id == "I19":
        route(store); item = completed(store, stream(store, transaction(store, lease(store))), body=b"old")
        store.commit(item, cache_key="key", etag="v1", operation_id="pub")
        old = store.cached("key"); new = store.revalidate("key", 304, etag="v2", expected_generation=old.generation, operation_id="validate")
        assert new.body == b"old" and new.etag == "v2" and new.generation == old.generation + 1 and new.state == "revalidated"
    elif root_id == "I20":
        route(store); item = completed(store, stream(store, transaction(store, lease(store))))
        store.commit(item, cache_key="key", etag="v1", operation_id="pub")
        first = store.cached("key"); current = store.revalidate("key", 304, expected_generation=first.generation, operation_id="fresh")
        expect(w.ConflictError, lambda: store.revalidate("key", 200, body=b"stale", expected_generation=first.generation, operation_id="stale"))
        assert store.cached("key") == current
    elif root_id == "I21":
        route(store); item = completed(store, stream(store, transaction(store, lease(store))))
        store.commit(item, cache_key="key", etag="v1", operation_id="pub"); old = store.cached("key")
        expect(w.ConflictError, lambda: store.revalidate("key", 500, expected_generation=old.generation, operation_id="bad"))
        assert store.cached("key") == old
    elif root_id == "I22":
        route(store, proxy="http://proxy.test:8080"); item = stream(store, transaction(store, lease(store)))
        for index, layer in enumerate(("response", "tls", "proxy", "connection")):
            item = store.discharge(item, layer, owner="worker-a", operation_id=f"cleanup-{index}")
        assert item.cleanup == ()
    elif root_id == "I23":
        route(store, proxy="http://proxy.test:8080"); item = stream(store, transaction(store, lease(store)))
        expect(w.OwnershipError, lambda: store.discharge(item, "response", owner="worker-b", operation_id="foreign"))
        assert store.recover("stream") == item and item.cleanup[0] == "response"
    elif root_id == "I24":
        route(store); tx = transaction(store, lease(store)); item = completed(store, stream(store, tx))
        pub = store.commit(item, cache_key="key", operation_id="pub")
        reopened = w.ClientJournal(tmp_path / "journal")
        assert reopened.recover("request") == tx and reopened.current("main") == pub
        assert reopened.cached("key").source_operation == "pub" and reopened.reconcile().valid
    else: raise KeyError(root_id)


def system_case(root_id: str, tmp_path: Path) -> None:
    w = api(); store = w.ClientJournal(tmp_path / "journal")
    if root_id == "S04":
        route(store); cap = lease(store)
        first = completed(store, stream(store, transaction(store, cap, "first-tx"), "first-stream"), "first-done", b"v1")
        pub = store.commit(first, cache_key="resource", etag="e1", events=("request", "body", "cache"), operation_id="first-pub")
        old = store.cached("resource"); updated = store.revalidate("resource", 304, etag="e2", expected_generation=old.generation, operation_id="revalidate")
        bad = store.feed(stream(store, transaction(store, cap, "bad-tx"), "bad-stream"), b"partial", operation_id="partial")
        store.cancel(bad, reason="timeout", operation_id="timeout")
        reopened = w.ClientJournal(tmp_path / "journal")
        assert reopened.current("main") == pub and reopened.cached("resource") == updated and reopened.reconcile().valid
    elif root_id == "S05":
        route(store, proxy="http://proxy.test:8080"); item = stream(store, transaction(store, lease(store)))
        item = store.feed(item, b"partial", operation_id="partial"); item = store.cancel(item, reason="tls-error", operation_id="cancel")
        reopened = w.ClientJournal(tmp_path / "journal"); item = reopened.recover("cancel")
        for index, layer in enumerate(("response", "tls", "proxy", "connection")):
            item = reopened.discharge(item, layer, owner="worker-a", operation_id=f"cleanup-{index}")
        assert item.cleanup == () and item.state == "tls-error" and reopened.current("main") is None
    elif root_id == "S06":
        route(store); old = lease(store); store.handoff(old, new_owner="worker-b", operation_id="move")
        route(store, origin="https://new.test/", operation="rotate")
        reopened = w.ClientJournal(tmp_path / "journal")
        expect(w.OwnershipError, lambda: transaction(reopened, old, "stale"))
        fresh = lease(reopened, "fresh", operation="fresh-lease", owner="worker-c")
        assert fresh.route_generation == 2 and reopened.reconcile().valid
    elif root_id == "S07":
        route(store, "direct", "https://a.test/"); route(store, "proxy", "https://b.test/", proxy="http://proxy.test:8080")
        for name in ("direct", "proxy"):
            cap = lease(store, name + "-slot", name)
            item = completed(store, stream(store, transaction(store, cap, name + "-tx"), name + "-stream"), name + "-done", name.encode())
            store.commit(item, cache_key=name, operation_id=name + "-pub")
        reopened = w.ClientJournal(tmp_path / "journal"); snap = reopened.reconcile()
        assert snap.valid and snap.route_count == 2 and snap.publication_count == 2 and snap.cache_count == 2
        assert reopened.current("direct").body_digest != reopened.current("proxy").body_digest
    elif root_id == "S08":
        route(store); transaction(store, lease(store)); journal = tmp_path / "journal" / "httpx-orchestration.json"
        payload = journal.read_bytes(); journal.write_bytes(payload[:-7] + b"broken")
        expect(w.IntegrityError, lambda: w.ClientJournal(tmp_path / "journal"))
    else: raise KeyError(root_id)
