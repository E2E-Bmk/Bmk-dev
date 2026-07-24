"""Integration and system-level behavioral tests for Curio.

Each test exercises ≥2 public API boundaries or validates cross-view invariants.
"""
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

from conftest import async_failure, async_value, wait_for_event


# ── CVI-1: spawned task ↔ current_task identity ──────────────────

@pytest.mark.depends_on("test_task_join_returns_child_value")
def test_spawned_task_is_current_task_in_child():
    """CVI-1: spawned task identity matches current_task in child."""
    async def child():
        return await current_task()

    async def main():
        task = await spawn(child)
        return task, await task.join()

    spawned, observed = run(main)
    assert observed is spawned


# ── CVI-2: terminated flag ↔ wait return ──────────────────────────

@pytest.mark.depends_on("test_task_join_returns_child_value")
def test_task_wait_leaves_task_terminated():
    """CVI-2: task wait leaves task in terminated state."""
    async def main():
        task = await spawn(async_value, None)
        await task.wait()
        return task.terminated

    assert run(main) is True


# ── State consistency: task lifecycle completion ──────────────────

@pytest.mark.depends_on("test_task_join_returns_child_value")
def test_product_state_task_projection_records_normal_completion():
    """Seam: state consistency — task projection records normal completion."""
    async def main():
        task = await spawn(async_value, 23)
        await task.wait()
        return task.terminated, bool(task.cancelled), task.result, task.exception

    assert run(main) == (True, False, 23, None)


# ── State consistency: result/exception before/after termination ─

@pytest.mark.depends_on("test_task_result_raises_before_termination")
def test_task_result_and_exception_raise_before_deterministic_release():
    """Seam: state consistency — result and exception unavailable before termination."""
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


# ── Cancellation: blocking cancel → terminated + cancelled ────────

def test_blocking_cancel_terminates_task_and_marks_cancelled():
    """Seam: lifecycle crossing — blocking cancel terminates and marks cancelled."""
    async def main():
        task = await spawn(sleep, 10)
        await task.cancel()
        return task.cancelled, task.terminated

    assert run(main) == (True, True)


# ── Cancellation: direct cancellation delivers TaskCancelled ──────

def test_direct_cancellation_delivers_taskcancelled():
    """Seam: error propagation — direct cancellation delivers TaskCancelled."""
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


# ── TaskGroup: spawn + joined result ─────────────────────────────

@pytest.mark.depends_on("test_task_join_returns_child_value")
def test_taskgroup_spawn_exposes_joined_result():
    """Seam: lifecycle crossing — TaskGroup spawn exposes joined result."""
    async def main():
        async with TaskGroup() as group:
            task = await group.spawn(async_value, "group result")
        return task.result

    assert run(main) == "group result"


# ── TaskGroup: next_result returns completed value ────────────────

def test_taskgroup_next_result_returns_completed_value():
    """Seam: lifecycle crossing — TaskGroup next_result returns completed value."""
    async def main():
        group = TaskGroup()
        await group.spawn(async_value, 17)
        return await group.next_result()

    assert run(main) == 17


# ── TaskGroup: next_result reraises child failure ─────────────────

def test_taskgroup_next_result_reraises_child_failure():
    """Seam: error propagation — TaskGroup next_result reraises child failure."""
    async def main():
        group = TaskGroup()
        task = await group.spawn(async_failure)
        await task.wait()
        with pytest.raises(ValueError):
            await group.next_result()

    run(main)


# ── TaskGroup: wait=any cleans up managed tasks ──────────────────

def test_taskgroup_wait_any_cleans_up_managed_tasks():
    """Seam: lifecycle crossing — TaskGroup wait=any cleans up managed tasks."""
    async def main():
        async with TaskGroup(wait=any) as group:
            first = await group.spawn(async_value, "first")
            second = await group.spawn(sleep, 10)
        return first.terminated, second.terminated

    assert run(main) == (True, True)


# ── TaskGroup: wait=object uses non-None result ──────────────────

def test_taskgroup_wait_object_uses_non_none_result():
    """Seam: lifecycle crossing — TaskGroup wait=object selects non-None result."""
    async def main():
        async with TaskGroup(wait=object) as group:
            await group.spawn(async_value, None)
            await group.spawn(async_value, "selected")
        return group.result

    assert run(main) == "selected"


# ── TaskGroup: cancel_remaining terminates tasks ──────────────────

def test_taskgroup_cancel_remaining_terminates_non_daemons():
    """Seam: lifecycle crossing — cancel_remaining terminates non-daemon tasks."""
    async def main():
        group = TaskGroup()
        task = await group.spawn(sleep, 10)
        await group.cancel_remaining()
        return task.terminated

    assert run(main) is True


# ── TaskGroup: add_task adds ungrouped task ──────────────────────

def test_taskgroup_adds_ungrouped_task():
    """Seam: lifecycle crossing — TaskGroup add_task integrates ungrouped task."""
    async def main():
        task = await spawn(async_value, 9)
        group = TaskGroup()
        await group.add_task(task)
        await group.join()
        return group.result

    assert run(main) == 9


# ── CVI-3: task + group project same outcome ─────────────────────

@pytest.mark.depends_on("test_taskgroup_spawn_exposes_joined_result")
def test_cross_view_task_and_group_project_same_successful_outcome():
    """CVI-3: task and TaskGroup project same successful outcome."""
    async def main():
        group = TaskGroup()
        task = await group.spawn(async_value, 41)
        await group.join()
        return task.result, group.result, group.results

    assert run(main) == (41, 41, [41])


# ── CVI-4: queue unfinished work survives get until task_done ─────

@pytest.mark.depends_on("test_queue_join_waits_for_task_done_obligation")
def test_product_state_coordination_projection_retains_unfinished_work():
    """CVI-4: queue join retains unfinished work until task_done."""
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


# ── Bounded queue: put completes after consumer makes space ──────

def test_bounded_queue_put_completes_after_consumer_makes_space():
    """Seam: lifecycle crossing — bounded queue put completes after consumer frees space."""
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


# ── Semaphore: release makes waiting acquisition proceed ──────────

def test_semaphore_release_makes_waiting_acquisition_eligible():
    """Seam: lifecycle crossing — semaphore release unblocks waiting acquire."""
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


# ── Nested timeout: outer interrupts inner with distinct error ────

def test_nested_outer_timeout_interrupts_inner_with_distinct_error():
    """Seam: error propagation — outer timeout interrupts inner with distinct error."""
    async def main():
        async with timeout_after(0):
            with pytest.raises(TimeoutCancellationError):
                async with timeout_after(10):
                    await sleep(1)
        return "foreign timeout distinguished"

    assert run(main) == "foreign timeout distinguished"


# ── Uncaught timeout: escaping raises UncaughtTimeoutError ────────

def test_timeout_escaping_matching_boundary_raises_uncaught_timeout():
    """Seam: error propagation — escaping timeout raises UncaughtTimeoutError."""
    async def main():
        try:
            async with timeout_after(0):
                await sleep(1)
        except TaskTimeout as exc:
            async with timeout_after(10):
                raise exc

    with pytest.raises(UncaughtTimeoutError):
        run(main)


# ── CVI-5: UniversalQueue sync put → curio get ──────────────────

def test_universal_queue_sync_put_is_visible_to_curio_get():
    """CVI-5: UniversalQueue sync put visible to curio get."""
    queue = UniversalQueue()
    queue.put("thread item")

    async def main():
        value = await queue.get()
        await queue.task_done()
        return value

    assert run(main) == "thread item"


# ── CVI-5: UniversalQueue curio put → sync get ──────────────────

def test_universal_queue_curio_put_is_visible_to_sync_get():
    """CVI-5: UniversalQueue curio put visible to sync get."""
    queue = UniversalQueue()

    async def main():
        await queue.put("curio item")

    run(main)
    assert queue.get() == "curio item"
    queue.task_done()


# ── UniversalQueue: sync join observes task_done ──────────────────

def test_universal_queue_sync_join_observes_task_done():
    """Seam: state consistency — UniversalQueue sync join observes task_done."""
    queue = UniversalQueue()
    queue.put("item")
    assert queue.get() == "item"
    queue.task_done()
    assert queue.join() is None


# ── UniversalQueue: fileno without fd raises ──────────────────────

def test_universal_queue_without_fd_rejects_fileno():
    """Seam: error propagation — UniversalQueue without fd rejects fileno."""
    with pytest.raises(AssertionError):
        UniversalQueue().fileno()


# ── CVI-6: UniversalEvent sync set → curio waiter ────────────────

def test_universal_event_sync_set_is_visible_to_curio_waiter():
    """CVI-6: UniversalEvent sync set visible to curio waiter."""
    event = UniversalEvent()
    event.set()

    async def main():
        await event.wait()
        return event.is_set()

    assert run(main) is True


# ── CVI-6: UniversalEvent curio set → sync ──────────────────────

def test_universal_event_curio_set_is_visible_synchronously():
    """CVI-6: UniversalEvent curio set visible synchronously."""
    event = UniversalEvent()

    async def main():
        await event.set()

    run(main)
    assert event.is_set() is True


# ── CVI-6: UniversalEvent clear resets flag ──────────────────────



# ── CVI-6: UniversalEvent thread set → curio waiter ──────────────

@pytest.mark.depends_on("test_universal_event_sync_set_is_visible_to_curio_waiter")
def test_cross_view_universal_event_thread_set_releases_curio_waiter():
    """CVI-6: thread set on UniversalEvent releases curio waiter."""
    async def main():
        event = UniversalEvent()
        waiter = await spawn(event.wait)
        thread = threading.Thread(target=event.set)
        thread.start()
        await waiter.join()
        thread.join()
        return event.is_set()

    assert run(main) is True


# ── CVI-7: UniversalResult sync value → curio unwrap ─────────────

def test_universal_result_sync_value_is_unwrapped_in_curio():
    """CVI-7: UniversalResult sync value unwrapped in curio."""
    result = UniversalResult()
    result.set_value("shared")

    async def main():
        return await result.unwrap()

    assert run(main) == "shared"


# ── CVI-7: UniversalResult curio value → sync unwrap ─────────────

def test_universal_result_curio_value_is_unwrapped_synchronously():
    """CVI-7: UniversalResult curio value unwrapped synchronously."""
    result = UniversalResult()

    async def main():
        await result.set_value("shared")

    run(main)
    assert result.unwrap() == "shared"


# ── CVI-7: UniversalResult sync exception → curio unwrap ─────────

def test_universal_result_sync_exception_is_reraised_in_curio():
    """CVI-7: UniversalResult sync exception reraised in curio."""
    result = UniversalResult()
    result.set_exception(ValueError("bad"))

    async def main():
        with pytest.raises(ValueError):
            await result.unwrap()

    run(main)


# ── CVI-7: UniversalResult curio exception → sync unwrap ─────────

def test_universal_result_curio_exception_is_reraised_synchronously():
    """CVI-7: UniversalResult curio exception reraised synchronously."""
    result = UniversalResult()

    async def main():
        await result.set_exception(ValueError("bad"))

    run(main)
    with pytest.raises(ValueError):
        result.unwrap()


# ── CVI-7: UniversalResult exception → asyncio unchanged ─────────

def test_cross_view_universal_result_exception_reaches_asyncio_unchanged():
    """CVI-7: UniversalResult exception reaches asyncio unchanged."""
    result = UniversalResult()
    error = ValueError("shared failure")
    result.set_exception(error)

    async def consume():
        with pytest.raises(ValueError) as caught:
            await result.unwrap()
        return caught.value is error

    assert asyncio.run(consume()) is True


# ── CVI-3 + state: universal result thread → curio ────────────────

def test_product_state_universal_projection_shares_result_with_thread():
    """CVI-3: UniversalResult projection shares value with thread."""
    async def main():
        result = UniversalResult()
        waiter = await spawn(result.unwrap)
        thread = threading.Thread(target=result.set_value, args=("shared",))
        thread.start()
        value = await waiter.join()
        thread.join()
        return result.is_set(), value

    assert run(main) == (True, "shared")


# ── CVI-8: ignore_after suppresses timeout ────────────────────────

def test_ignore_after_suppresses_timeout_via_expired_flag():
    """CVI-8: ignore_after suppresses timeout via expired flag."""
    async def main():
        async with ignore_after(0, timeout_result="sentinel") as scope:
            await sleep(1)
        return scope.expired, scope.result

    assert run(main) == (True, "sentinel")


# ── Representative workflow: worker + queue + task group ──────────

def test_representative_worker_queue_taskgroup_workflow():
    """Seam: lifecycle crossing — worker queue TaskGroup workflow completes."""
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


# ── Representative workflow: event + task ─────────────────────────

def test_representative_event_task_workflow():
    """Seam: lifecycle crossing — event and task coordination workflow."""
    async def main():
        event = Event()
        waiter = await spawn(wait_for_event, event)
        await event.set()
        return await waiter.join()

    assert run(main) == "released"


# ── Representative workflow: universal result ─────────────────────

def test_representative_universal_result_workflow():
    """Seam: lifecycle crossing — UniversalResult set and unwrap workflow."""
    result = UniversalResult()

    async def main():
        await result.set_value(42)

    run(main)
    assert result.unwrap() == 42
