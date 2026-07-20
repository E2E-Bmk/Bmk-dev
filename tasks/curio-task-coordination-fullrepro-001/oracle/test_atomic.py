"""Atomic public-API behavioral tests for Curio."""

import pytest

from curio import (
    Condition,
    Event,
    LifoQueue,
    Lock,
    PriorityQueue,
    Queue,
    RLock,
    Result,
    TaskError,
    TaskTimeout,
    ignore_after,
    run,
    sleep,
    spawn,
    timeout_after,
)


async def _value(value):
    return value


async def _failure():
    raise ValueError("child failure")


async def _wait_for_event(event):
    await event.wait()
    return "released"


def test_run_returns_coroutine_value():
    assert run(_value, 42) == 42


def test_run_passes_all_arguments_to_coroutine():
    async def add(left, right):
        return left + right

    assert run(add, 20, 22) == 42


def test_run_rejects_nested_runtime():
    async def main():
        with pytest.raises(RuntimeError):
            run(_value, 42)

    run(main)


def test_task_ids_are_increasing_integers_without_positivity_assumption():
    async def main():
        release = Event()

        async def child():
            await release.wait()

        first = await spawn(child)
        second = await spawn(child)
        observed = (type(first.id) is int, type(second.id) is int,
                    first.id < second.id)
        await release.set()
        await first.join()
        await second.join()
        return observed

    assert run(main) == (True, True, True)


def test_task_join_returns_child_value():
    async def main():
        task = await spawn(_value, "done")
        return await task.join()

    assert run(main) == "done"


def test_task_join_wraps_child_failure_with_cause():
    async def main():
        task = await spawn(_failure)
        with pytest.raises(TaskError) as raised:
            await task.join()
        return raised.value.__cause__

    assert isinstance(run(main), ValueError)


def test_queue_returns_items_in_fifo_order():
    async def main():
        queue = Queue()
        await queue.put("first")
        await queue.put("second")
        values = (await queue.get(), await queue.get())
        await queue.task_done()
        await queue.task_done()
        return values

    assert run(main) == ("first", "second")


def test_priority_queue_returns_lowest_item_first():
    async def main():
        queue = PriorityQueue()
        await queue.put(3)
        await queue.put(1)
        await queue.put(2)
        values = [await queue.get() for _ in range(3)]
        for _ in values:
            await queue.task_done()
        return values

    assert run(main) == [1, 2, 3]


def test_lifo_queue_returns_latest_item_first():
    async def main():
        queue = LifoQueue()
        await queue.put("first")
        await queue.put("second")
        values = (await queue.get(), await queue.get())
        await queue.task_done()
        await queue.task_done()
        return values

    assert run(main) == ("second", "first")


def test_queue_public_size_and_capacity_state():
    async def main():
        queue = Queue(maxsize=1)
        initial = (queue.empty(), queue.full(), queue.qsize())
        await queue.put("item")
        filled = (queue.empty(), queue.full(), queue.qsize())
        assert await queue.get() == "item"
        await queue.task_done()
        return initial, filled

    assert run(main) == ((True, False, 0), (False, True, 1))


def test_queue_join_waits_for_task_done_obligation():
    async def worker(queue):
        item = await queue.get()
        await queue.task_done()
        return item

    async def main():
        queue = Queue()
        await queue.put("work")
        task = await spawn(worker, queue)
        await queue.join()
        return await task.join(), queue.empty()

    assert run(main) == ("work", True)


def test_event_set_releases_waiter_and_sets_flag():
    async def main():
        event = Event()
        waiter = await spawn(_wait_for_event, event)
        await sleep(0)
        await event.set()
        return event.is_set(), await waiter.join()

    assert run(main) == (True, "released")


def test_result_unwrap_returns_supplied_value():
    async def main():
        result = Result()
        await result.set_value("value")
        return result.is_set(), await result.unwrap()

    assert run(main) == (True, "value")


def test_result_unwrap_reraises_supplied_exception():
    async def main():
        result = Result()
        await result.set_exception(ValueError("bad"))
        with pytest.raises(ValueError):
            await result.unwrap()

    run(main)


def test_lock_reports_locked_while_held():
    async def main():
        lock = Lock()
        before = lock.locked()
        await lock.acquire()
        held = lock.locked()
        await lock.release()
        return before, held, lock.locked()

    assert run(main) == (False, True, False)


def test_rlock_allows_recursive_owner_acquisition():
    async def main():
        lock = RLock()
        await lock.acquire()
        await lock.acquire()
        held = lock.locked()
        await lock.release()
        still_held = lock.locked()
        await lock.release()
        return held, still_held, lock.locked()

    assert run(main) == (True, True, False)


def test_condition_wait_requires_held_lock():
    async def main():
        condition = Condition()
        with pytest.raises(RuntimeError):
            await condition.wait()

    run(main)


def test_condition_notify_requires_held_lock():
    async def main():
        condition = Condition()
        with pytest.raises(RuntimeError):
            await condition.notify()

    run(main)


def test_condition_wait_for_returns_truthy_predicate_value():
    async def main():
        condition = Condition()
        async with condition:
            return await condition.wait_for(lambda: "ready")

    assert run(main) == "ready"


def test_timeout_after_returns_value_before_deadline():
    assert run(timeout_after, 1, _value, "on time") == "on time"


def test_timeout_after_raises_task_timeout_when_blocking_operation_expires():
    with pytest.raises(TaskTimeout):
        run(timeout_after, 0, sleep, 1)


def test_ignore_after_returns_value_before_deadline():
    assert run(ignore_after, 1, _value, "on time") == "on time"


def test_ignore_after_returns_timeout_result_after_expiry():
    async def main():
        return await ignore_after(0, sleep, 1, timeout_result="expired")

    assert run(main) is None


def test_ignore_after_context_reports_non_expiration():
    async def main():
        async with ignore_after(1) as scope:
            value = await _value("complete")
        return scope.expired, value

    assert run(main) == (False, "complete")


def test_ignore_after_context_reports_own_expiration():
    async def main():
        async with ignore_after(0, timeout_result="expired") as scope:
            await sleep(1)
        return scope.expired, scope.result

    assert run(main) == (True, "expired")


def test_timeout_context_delivers_task_timeout_to_matching_scope():
    async def main():
        try:
            async with timeout_after(0):
                await sleep(1)
        except TaskTimeout:
            return "timed out"

    assert run(main) == "timed out"
