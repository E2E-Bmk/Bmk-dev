import threading

import pytest

import curio


def test_a01_run_exact_value_and_top_level_failure_identity():
    async def compute(left, right):
        return left * 7 - right

    assert curio.run(compute, 17, 8) == 111
    marker = LookupError("top-level")

    async def fail():
        raise marker

    with pytest.raises(LookupError) as caught:
        curio.run(fail)
    assert caught.value is marker


def test_a02_spawned_task_join_returns_value():
    async def main():
        release = curio.Event()

        async def child():
            await release.wait()
            return ("joined", 173)

        task = await curio.spawn(child)
        await release.set()
        assert await task.join() == ("joined", 173)

    curio.run(main)


def test_a03_taskerror_keeps_exact_child_failure_as_cause():
    marker = ValueError("child-marker")

    async def main():
        async def child():
            raise marker

        task = await curio.spawn(child)
        with pytest.raises(curio.TaskError) as caught:
            await task.join()
        assert caught.value.__cause__ is marker

    curio.run(main)


def test_a04_explicit_task_cancellation_object_is_preserved():
    marker = curio.TaskCancelled("explicit-object")

    async def main():
        ready = curio.Event()

        async def child():
            await ready.set()
            try:
                await curio.Event().wait()
            except curio.TaskCancelled as exc:
                return exc

        task = await curio.spawn(child)
        await ready.wait()
        await task.cancel(exc=marker, blocking=False)
        assert await task.join() is marker

    curio.run(main)


def test_a05_event_set_clear_and_reuse():
    async def main():
        event = curio.Event()
        waiter = await curio.spawn(event.wait)
        await event.set()
        await waiter.join()
        assert event.is_set()
        event.clear()
        assert not event.is_set()

    curio.run(main)


def test_a06_queue_fifo_and_unfinished_work_ledger():
    async def main():
        queue = curio.Queue(maxsize=3)
        values = [("quartz", 19), ("mica", 31), ("slate", 47)]
        for value in values:
            await queue.put(value)
        observed = []
        for _ in values:
            observed.append(await queue.get())
            await queue.task_done()
        await queue.join()
        assert observed == values

    curio.run(main)


def test_a07_lock_reports_ownership_and_releases():
    async def main():
        lock = curio.Lock()
        assert await lock.acquire() is True
        assert lock.locked()
        await lock.release()
        assert not lock.locked()

    curio.run(main)


def test_a08_zero_timeout_marks_own_scope_expired():
    async def main():
        scope = None
        with pytest.raises(curio.TaskTimeout):
            async with curio.timeout_after(0) as scope:
                await curio.Event().wait()
        assert scope.expired is True

    curio.run(main)


def test_a09_universal_queue_thread_item_visible_to_curio():
    async def main():
        queue = curio.UniversalQueue()
        await curio.run_in_thread(queue.put, ("thread", 211))
        assert await queue.get() == ("thread", 211)
        await queue.task_done()
        await queue.join()

    curio.run(main)


def test_a10_result_unwraps_value_and_exact_failure():
    async def main():
        value = curio.Result()
        await value.set_value({"answer": 223})
        assert await value.unwrap() == {"answer": 223}
        marker = RuntimeError("result-marker")
        failed = curio.Result()
        await failed.set_exception(marker)
        with pytest.raises(RuntimeError) as caught:
            await failed.unwrap()
        assert caught.value is marker

    curio.run(main)


def test_a11_real_socket_fd_and_one_framed_transfer():
    async def main():
        left, right = await curio.open_socket_stream_pair(frame_limit=2)
        try:
            assert left.fileno() >= 0 and right.fileno() >= 0
            await left.send_frame(memoryview(b"opal-frame"))
            assert await right.receive_frame() == b"opal-frame"
            assert left.statistics().outbound_admitted == 0
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_a12_socket_half_close_keeps_reverse_direction_open():
    async def main():
        left, right = await curio.open_socket_stream_pair()
        try:
            await left.send_frame(b"last-left")
            await left.send_eof()
            assert await right.receive_frame() == b"last-left"
            with pytest.raises(curio.StreamEOF):
                await right.receive_frame()
            await right.send_frame(b"right-still-open")
            assert await left.receive_frame() == b"right-still-open"
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_a13_socket_credit_exposes_deterministic_backpressure():
    async def main():
        left, right = await curio.open_socket_stream_pair(frame_limit=1)
        try:
            await left.send_frame(b"resident")
            sender = await curio.spawn(left.send_frame, b"waiting")
            assert await left.wait_backpressured() == 1
            stats = left.statistics()
            assert stats.outbound_admitted == 1 and stats.outbound_waiters == 1
            assert await right.receive_frame() == b"resident"
            await sender.join()
            assert await right.receive_frame() == b"waiting"
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_a14_worker_pool_uses_a_real_ordinary_thread():
    async def main():
        caller_ident = threading.get_ident()
        async with curio.ThreadWorkerPool(limit=2) as pool:
            job = await pool.submit(threading.get_ident)
            worker_ident = await job.join()
            assert worker_ident != caller_ident
            assert job.status == "succeeded"

    curio.run(main)


def test_a15_worker_cancellation_publishes_then_retires_late_value():
    async def main():
        started = threading.Event()
        release = threading.Event()

        def work():
            started.set()
            release.wait()
            return "late-value"

        pool = curio.ThreadWorkerPool()
        job = await pool.submit(work)
        await curio.run_in_thread(started.wait)
        marker = curio.WorkerCancelled("retire")
        assert await job.cancel(marker) is marker
        with pytest.raises(curio.WorkerCancelled) as caught:
            await job.join()
        assert caught.value is marker and job.status == "retiring"
        release.set()
        await job.wait_retired()
        assert job.status == "retired" and job.late_result == "late-value"
        await pool.aclose()

    curio.run(main)


def test_a16_worker_admission_captures_tasklocal_context():
    async def main():
        request = curio.TaskLocal("request-a16", default="unset")
        async with request.bind("req-239"):
            async with curio.ThreadWorkerPool() as pool:
                job = await pool.submit(request.get)
                assert await job.join() == "req-239"
        assert request.get() == "unset"

    curio.run(main)


def test_a17_default_run_isolates_tasklocal_siblings():
    async def main():
        local = curio.TaskLocal("sibling-a17", default="root")
        arrived = curio.Queue()
        release = curio.Event()

        async def child(value):
            async with local.bind(value):
                await arrived.put(local.get())
                await release.wait()
                return local.get()

        first = await curio.spawn(child, "amber")
        second = await curio.spawn(child, "indigo")
        seen = {await arrived.get(), await arrived.get()}
        await arrived.task_done()
        await arrived.task_done()
        assert seen == {"amber", "indigo"} and local.get() == "root"
        await release.set()
        assert {await first.join(), await second.join()} == {"amber", "indigo"}

    curio.run(main)


def test_a18_async_generator_scope_finalizes_exactly_once():
    async def main():
        trace = []

        async def source():
            try:
                yield 251
            finally:
                trace.append("finalized")

        scope = curio.AsyncGeneratorScope()
        generator = scope.track(source())
        assert await generator.__anext__() == 251
        await scope.aclose()
        await scope.aclose()
        assert trace == ["finalized"] and scope.finalization_errors == ()

    curio.run(main)


def test_a19_resource_stack_lifo_and_one_shot_close():
    async def main():
        trace = []
        stack = curio.AsyncResourceStack()
        stack.push(lambda: trace.append("older"))
        stack.push(lambda: trace.append("newer"))
        await stack.aclose()
        await stack.aclose()
        assert trace == ["newer", "older"] and stack.cleanup_errors == ()

    curio.run(main)


def test_a20_workflow_id_lease_ack_result_and_snapshot():
    async def main():
        workflow = curio.WorkflowCoordinator()
        work_id = await workflow.submit(("calc", 263))
        lease = await workflow.claim()
        assert lease.work_id == work_id and lease.attempt == 0
        await workflow.ack(lease, 526)
        await workflow.join()
        assert await workflow.receive_result() == (work_id, 526)
        snapshot = workflow.snapshot()
        assert (snapshot.queued, snapshot.active, snapshot.finished, snapshot.submitted) == (0, 0, 1, 1)

    curio.run(main)

