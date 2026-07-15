"""Behavioral oracle generated from the candidate-visible Curio specification."""

import asyncio
import threading

import pytest

from curio import (
    CancelledError,
    Condition,
    Event,
    LifoQueue,
    Lock,
    PriorityQueue,
    Queue,
    RLock,
    Result,
    Semaphore,
    TaskCancelled,
    TaskError,
    TaskTimeout,
    TaskGroup,
    TimeoutCancellationError,
    UncaughtTimeoutError,
    UniversalEvent,
    UniversalQueue,
    UniversalResult,
    current_task,
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


def test_product_state_task_projection_records_normal_completion():
    async def main():
        task = await spawn(_value, 23)
        await task.wait()
        return task.terminated, bool(task.cancelled), task.result, task.exception

    assert run(main) == (True, False, 23, None)


def test_product_state_coordination_projection_retains_unfinished_work():
    async def main():
        queue = Queue()
        got_item = Event()
        release_ack = Event()
        join_returned = Event()

        async def consumer():
            item = await queue.get()
            await got_item.set()
            await release_ack.wait()
            await queue.task_done()
            return item

        async def waiter():
            await queue.join()
            await join_returned.set()

        await queue.put("work")
        consumer_task = await spawn(consumer)
        await got_item.wait()
        join_task = await spawn(waiter)
        await sleep(0)
        blocked = not join_returned.is_set() and not join_task.terminated
        await release_ack.set()
        await join_task.join()
        return blocked, join_returned.is_set(), await consumer_task.join()

    assert run(main) == (True, True, "work")


def test_product_state_universal_projection_shares_result_with_thread():
    async def main():
        result = UniversalResult()
        waiter = await spawn(result.unwrap)
        thread = threading.Thread(target=result.set_value, args=("shared",))
        thread.start()
        value = await waiter.join()
        thread.join()
        return result.is_set(), value

    assert run(main) == (True, "shared")


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


def test_task_result_and_exception_raise_before_deterministic_release():
    async def main():
        started = Event()
        release = Event()

        async def child():
            await started.set()
            await release.wait()
            return 99

        task = await spawn(child)
        await started.wait()
        assert not task.terminated
        with pytest.raises(RuntimeError):
            _ = task.result
        with pytest.raises(RuntimeError):
            _ = task.exception
        await release.set()
        assert await task.join() == 99
        return task.result, task.exception

    assert run(main) == (99, None)


def test_spawned_task_is_current_task_in_child():
    async def child():
        return await current_task()

    async def main():
        task = await spawn(child)
        return task, await task.join()

    spawned, observed = run(main)
    assert observed is spawned


def test_task_join_returns_child_value():
    async def main():
        task = await spawn(_value, "done")
        return await task.join()

    assert run(main) == "done"


def test_task_wait_leaves_task_terminated():
    async def main():
        task = await spawn(_value, None)
        await task.wait()
        return task.terminated

    assert run(main) is True


def test_task_join_wraps_child_failure_with_cause():
    async def main():
        task = await spawn(_failure)
        with pytest.raises(TaskError) as raised:
            await task.join()
        return raised.value.__cause__

    assert isinstance(run(main), ValueError)


def test_blocking_cancel_terminates_task_and_marks_cancelled():
    async def main():
        task = await spawn(sleep, 10)
        await task.cancel()
        return task.cancelled, task.terminated

    assert run(main) == (True, True)


def test_taskgroup_spawn_exposes_joined_result():
    async def main():
        async with TaskGroup() as group:
            task = await group.spawn(_value, "group result")
        return task.result

    assert run(main) == "group result"


def test_taskgroup_next_result_returns_completed_value():
    async def main():
        group = TaskGroup()
        await group.spawn(_value, 17)
        return await group.next_result()

    assert run(main) == 17


def test_taskgroup_wait_any_cleans_up_managed_tasks():
    async def main():
        async with TaskGroup(wait=any) as group:
            first = await group.spawn(_value, "first")
            second = await group.spawn(sleep, 10)
        return first.terminated, second.terminated

    assert run(main) == (True, True)


def test_taskgroup_cancel_remaining_terminates_non_daemons():
    async def main():
        group = TaskGroup()
        task = await group.spawn(sleep, 10)
        await group.cancel_remaining()
        return task.terminated

    assert run(main) is True


def test_taskgroup_adds_ungrouped_task():
    async def main():
        task = await spawn(_value, 9)
        group = TaskGroup()
        await group.add_task(task)
        await group.join()
        return group.result

    assert run(main) == 9


def test_taskgroup_wait_object_uses_non_none_result():
    async def main():
        async with TaskGroup(wait=object) as group:
            await group.spawn(_value, None)
            await group.spawn(_value, "selected")
        return group.result

    assert run(main) == "selected"


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


def test_bounded_queue_put_completes_after_consumer_makes_space():
    async def consumer(queue):
        item = await queue.get()
        await queue.task_done()
        return item

    async def main():
        queue = Queue(maxsize=1)
        await queue.put("first")
        consumer_task = await spawn(consumer, queue)
        await queue.put("second")
        second = await queue.get()
        await queue.task_done()
        return await consumer_task.join(), second

    assert run(main) == ("first", "second")


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


def test_semaphore_release_makes_waiting_acquisition_eligible():
    async def waiter(semaphore):
        await semaphore.acquire()
        return "acquired"

    async def main():
        semaphore = Semaphore(0)
        task = await spawn(waiter, semaphore)
        await sleep(0)
        await semaphore.release()
        return await task.join()

    assert run(main) == "acquired"


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


def test_direct_cancellation_delivers_taskcancelled():
    async def child(started):
        await started.set()
        try:
            await sleep(10)
        except TaskCancelled:
            return "direct cancellation"

    async def main():
        started = Event()
        task = await spawn(child, started)
        await started.wait()
        await task.cancel()
        return task.result

    assert run(main) == "direct cancellation"


def test_nested_outer_timeout_interrupts_inner_with_distinct_error():
    async def main():
        async with timeout_after(0):
            with pytest.raises(TimeoutCancellationError):
                async with timeout_after(10):
                    await sleep(1)
        return "foreign timeout distinguished"

    assert run(main) == "foreign timeout distinguished"


def test_timeout_escaping_matching_boundary_raises_uncaught_timeout():
    async def main():
        try:
            async with timeout_after(0):
                await sleep(1)
        except TaskTimeout as exc:
            async with timeout_after(10):
                raise exc

    with pytest.raises(UncaughtTimeoutError):
        run(main)


def test_universal_queue_sync_put_is_visible_to_curio_get():
    queue = UniversalQueue()
    queue.put("thread item")

    async def main():
        value = await queue.get()
        await queue.task_done()
        return value

    assert run(main) == "thread item"


def test_universal_queue_curio_put_is_visible_to_sync_get():
    queue = UniversalQueue()

    async def main():
        await queue.put("curio item")

    run(main)
    assert queue.get() == "curio item"
    queue.task_done()


def test_universal_queue_sync_join_observes_task_done():
    queue = UniversalQueue()
    queue.put("item")
    assert queue.get() == "item"
    queue.task_done()
    assert queue.join() is None


def test_universal_queue_without_fd_rejects_fileno():
    with pytest.raises(AssertionError):
        UniversalQueue().fileno()


def test_universal_event_sync_set_is_visible_to_curio_waiter():
    event = UniversalEvent()
    event.set()

    async def main():
        await event.wait()
        return event.is_set()

    assert run(main) is True


def test_universal_event_curio_set_is_visible_synchronously():
    event = UniversalEvent()

    async def main():
        await event.set()

    run(main)
    assert event.is_set() is True


def test_universal_event_clear_resets_shared_flag():
    event = UniversalEvent()
    event.set()
    event.clear()
    assert event.is_set() is False


def test_universal_result_sync_value_is_unwrapped_in_curio():
    result = UniversalResult()
    result.set_value("shared")

    async def main():
        return await result.unwrap()

    assert run(main) == "shared"


def test_universal_result_curio_value_is_unwrapped_synchronously():
    result = UniversalResult()

    async def main():
        await result.set_value("shared")

    run(main)
    assert result.unwrap() == "shared"


def test_universal_result_sync_exception_is_reraised_in_curio():
    result = UniversalResult()
    result.set_exception(ValueError("bad"))

    async def main():
        with pytest.raises(ValueError):
            await result.unwrap()

    run(main)


def test_universal_result_curio_exception_is_reraised_synchronously():
    result = UniversalResult()

    async def main():
        await result.set_exception(ValueError("bad"))

    run(main)
    with pytest.raises(ValueError):
        result.unwrap()


def test_taskgroup_next_result_reraises_child_failure():
    async def main():
        group = TaskGroup()
        task = await group.spawn(_failure)
        await task.wait()
        with pytest.raises(ValueError):
            await group.next_result()

    run(main)


def test_cross_view_task_and_group_project_same_successful_outcome():
    async def main():
        group = TaskGroup()
        task = await group.spawn(_value, 41)
        await group.join()
        return task.result, group.result, group.results

    assert run(main) == (41, 41, [41])


def test_cross_view_universal_event_thread_set_releases_curio_waiter():
    async def main():
        event = UniversalEvent()
        waiter = await spawn(event.wait)
        thread = threading.Thread(target=event.set)
        thread.start()
        await waiter.join()
        thread.join()
        return event.is_set()

    assert run(main) is True


def test_cross_view_universal_result_exception_reaches_asyncio_unchanged():
    result = UniversalResult()
    error = ValueError("shared failure")
    result.set_exception(error)

    async def consume():
        with pytest.raises(ValueError) as caught:
            await result.unwrap()
        return caught.value is error

    assert asyncio.run(consume()) is True


def test_representative_worker_queue_taskgroup_workflow():
    async def worker(queue):
        item = await queue.get()
        try:
            return item * 2
        finally:
            await queue.task_done()

    async def main():
        queue = Queue()
        async with TaskGroup() as group:
            await queue.put(21)
            job = await group.spawn(worker, queue)
            await queue.join()
        return job.result

    assert run(main) == 42


def test_representative_event_task_workflow():
    async def main():
        event = Event()
        waiter = await spawn(_wait_for_event, event)
        await event.set()
        return await waiter.join()

    assert run(main) == "released"


def test_representative_universal_result_workflow():
    result = UniversalResult()

    async def main():
        await result.set_value(42)

    run(main)
    assert result.unwrap() == 42
