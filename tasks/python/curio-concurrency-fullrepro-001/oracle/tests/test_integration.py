import contextvars
import threading

import pytest

import curio


def test_i01_taskgroup_children_publish_results_after_structured_exit():
    async def main():
        release = curio.Event()

        async def child(value):
            await release.wait()
            return value * 3

        async with curio.TaskGroup() as group:
            tasks = [await group.spawn(child, value) for value in (89, 97, 101)]
            await release.set()
        assert [task.result for task in tasks] == [267, 291, 303]

    curio.run(main)


def test_i02_cancelled_event_waiter_does_not_consume_reuse():
    async def main():
        event = curio.Event()
        ready = curio.Event()

        async def stale():
            await ready.set()
            await event.wait()

        task = await curio.spawn(stale)
        await ready.wait()
        await task.cancel()
        successor = await curio.spawn(event.wait)
        await event.set()
        await successor.join()
        assert event.is_set()

    curio.run(main)


def test_i03_cancelled_bounded_queue_put_leaves_no_ghost():
    async def main():
        queue = curio.Queue(maxsize=1)
        await queue.put(("resident", 107))
        ready = curio.Event()

        async def stale():
            await ready.set()
            await queue.put(("ghost", 0))

        task = await curio.spawn(stale)
        await ready.wait()
        await task.cancel()
        assert await queue.get() == ("resident", 107)
        await queue.task_done()
        await queue.join()
        assert queue.empty()

    curio.run(main)


def test_i04_thread_to_curio_universal_queue_transfer_and_ack():
    async def main():
        queue = curio.UniversalQueue()
        await curio.run_in_thread(queue.put, ("foreign", 277))
        item = await queue.get()
        assert item == ("foreign", 277)
        await queue.task_done()
        await queue.join()
        assert queue.empty()

    curio.run(main)


def test_i05_pending_cancellation_crosses_disable_scope_unchanged():
    marker = curio.TaskCancelled("masked-i05")

    async def main():
        entered = curio.Event()
        release = curio.Event()

        async def child():
            async with curio.disable_cancellation():
                await entered.set()
                await release.wait()
            try:
                await curio.check_cancellation()
            except curio.TaskCancelled as exc:
                return exc

        task = await curio.spawn(child)
        await entered.wait()
        await task.cancel(exc=marker, blocking=False)
        await release.set()
        assert await task.join() is marker

    curio.run(main)


def test_i06_thread_set_universal_event_releases_curio_waiter():
    async def main():
        event = curio.UniversalEvent()
        waiter = await curio.spawn(event.wait)
        await curio.run_in_thread(event.set)
        await waiter.join()
        assert event.is_set()

    curio.run(main)


def test_i07_run_in_thread_returns_ordinary_worker_result():
    async def main():
        caller = threading.get_ident()

        def compute(value):
            return threading.get_ident(), value * 5 + 1

        worker, result = await curio.run_in_thread(compute, 59)
        assert worker != caller and result == 296

    curio.run(main)


def test_i08_explicit_contexttask_inherits_and_isolates_child_snapshot():
    key = contextvars.ContextVar("explicit-i08", default="root")

    async def main():
        key.set("parent")
        release = curio.Event()

        async def child():
            inherited = key.get()
            key.set("child")
            await release.wait()
            return inherited, key.get()

        task = await curio.spawn(child)
        await release.set()
        assert await task.join() == ("parent", "child")
        assert key.get() == "parent"

    curio.run(main, taskcls=curio.task.ContextTask)


def test_i09_duplex_socket_frames_keep_directions_independent():
    async def main():
        left, right = await curio.open_socket_stream_pair(frame_limit=2)
        try:
            await left.send_frame(b"L:283")
            await right.send_frame(b"R:293")
            assert await left.receive_frame() == b"R:293"
            assert await right.receive_frame() == b"L:283"
            assert left.statistics().outbound_admitted == 0
            assert right.statistics().outbound_admitted == 0
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_i10_admitted_frames_drain_before_half_close_eof():
    async def main():
        left, right = await curio.open_socket_stream_pair(frame_limit=3)
        try:
            values = [b"cobalt:307", b"umber:311", b"ochre:313"]
            for value in values:
                await left.send_frame(value)
            await left.send_eof()
            assert [await right.receive_frame() for _ in values] == values
            with pytest.raises(curio.StreamEOF):
                await right.receive_frame()
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_i11_cancelled_receive_then_generation_restart_keeps_future_frame():
    async def main():
        left, right = await curio.open_socket_stream_pair()
        ready = curio.Event()

        async def stale_receive():
            await ready.set()
            await right.receive_frame()

        try:
            stale = await curio.spawn(stale_receive)
            await ready.wait()
            await stale.cancel()
            assert right.restart_receive() == 1
            await left.send_frame(b"successor:317")
            assert await right.receive_frame() == b"successor:317"
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_i12_cancelled_backpressured_sender_commits_no_ghost_frame():
    async def main():
        left, right = await curio.open_socket_stream_pair(frame_limit=1)
        try:
            await left.send_frame(b"resident:331")
            stale = await curio.spawn(left.send_frame, b"ghost:337")
            await left.wait_backpressured()
            await stale.cancel()
            assert await right.receive_frame() == b"resident:331"
            await left.send_frame(b"successor:347")
            assert await right.receive_frame() == b"successor:347"
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_i13_receive_teardown_wakes_blocked_peer_sender_as_broken():
    async def main():
        left, right = await curio.open_socket_stream_pair(frame_limit=1)

        async def blocked():
            try:
                await left.send_frame(b"blocked:353")
            except curio.BrokenStreamError as exc:
                return exc

        try:
            await left.send_frame(b"resident:349")
            sender = await curio.spawn(blocked)
            await left.wait_backpressured()
            await right.aclose_receive()
            assert isinstance(await sender.join(), curio.BrokenStreamError)
            assert left.statistics().peer_receive_closed is True
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_i14_receive_restart_advances_generation_without_replacing_fd():
    async def main():
        left, right = await curio.open_socket_stream_pair()
        original_fd = right.fileno()
        try:
            assert right.restart_receive() == 1
            assert right.restart_receive() == 2
            assert right.fileno() == original_fd
            assert right.statistics().receive_generation == 2
            await left.send_frame(b"generation-two")
            assert await right.receive_frame() == b"generation-two"
        finally:
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_i15_taskgroup_request_response_relay_over_duplex_socket():
    async def main():
        client, server = await curio.open_socket_stream_pair(frame_limit=1)
        try:
            async def serve():
                request = await server.receive_frame()
                await server.send_frame(request.upper() + b":359")

            async with curio.TaskGroup() as group:
                await group.spawn(serve)
                await client.send_frame(b"marble")
                assert await client.receive_frame() == b"MARBLE:359"
        finally:
            await client.aclose()
            await server.aclose()

    curio.run(main)


def test_i16_resource_stack_closes_both_real_socket_endpoints():
    async def main():
        left, right = await curio.open_socket_stream_pair()
        stack = curio.AsyncResourceStack()
        stack.push(left)
        stack.push(right)
        await stack.aclose()
        assert left.fileno() < 0 and right.fileno() < 0
        assert stack.cleanup_errors == ()

    curio.run(main)


def test_i17_pool_limit_backpressures_submitter_until_slot_retires():
    async def main():
        started = threading.Event()
        release = threading.Event()

        def first_work():
            started.set()
            release.wait()
            return 367

        pool = curio.ThreadWorkerPool(limit=1)
        first = await pool.submit(first_work)
        await curio.run_in_thread(started.wait)
        submitter = await curio.spawn(pool.submit, lambda: 373)
        assert await pool.wait_for_submitters() == 1
        release.set()
        second = await submitter.join()
        assert await first.join() == 367
        assert await second.join() == 373
        await pool.aclose()

    curio.run(main)


def test_i18_cancelled_worker_late_value_never_replaces_publication():
    async def main():
        started = threading.Event()
        release = threading.Event()

        def work():
            started.set()
            release.wait()
            return {"late": 379}

        pool = curio.ThreadWorkerPool()
        job = await pool.submit(work)
        await curio.run_in_thread(started.wait)
        marker = curio.WorkerCancelled("i18")
        await job.cancel(marker)
        release.set()
        await job.wait_retired()
        with pytest.raises(curio.WorkerCancelled) as caught:
            await job.join()
        assert caught.value is marker
        assert job.result is None and job.late_result == {"late": 379}
        await pool.aclose()

    curio.run(main)


def test_i19_worker_failure_wraps_exact_original_cause():
    marker = ArithmeticError("worker-failure")

    async def main():
        def fail():
            raise marker

        async with curio.ThreadWorkerPool() as pool:
            job = await pool.submit(fail)
            with pytest.raises(curio.WorkerJobError) as caught:
                await job.join()
            assert caught.value.__cause__ is marker
            assert job.exception is marker

    curio.run(main)


def test_i20_worker_observes_admission_context_not_later_update():
    async def main():
        local = curio.TaskLocal("context-i20", default="root")
        started = threading.Event()
        release = threading.Event()

        def observe():
            started.set()
            release.wait()
            return local.get()

        pool = curio.ThreadWorkerPool()
        token = local.set("admitted")
        job = await pool.submit(observe)
        await curio.run_in_thread(started.wait)
        local.set("later")
        release.set()
        assert await job.join() == "admitted"
        local.reset(token)
        await pool.aclose()

    curio.run(main)


def test_i21_job_ownership_persists_until_pool_close():
    async def main():
        pool = curio.ThreadWorkerPool()
        first = await pool.submit(lambda: 383)
        second = await pool.submit(lambda: 389)
        assert await first.join() == 383 and await second.join() == 389
        assert first.owner is pool and second.owner is pool
        assert pool.jobs == [first, second]
        await pool.aclose()
        assert first.owner is None and second.owner is None

    curio.run(main)


def test_i22_pool_close_waits_for_retiring_real_thread():
    async def main():
        started = threading.Event()
        release = threading.Event()

        def work():
            started.set()
            release.wait()
            return 397

        pool = curio.ThreadWorkerPool()
        job = await pool.submit(work)
        await curio.run_in_thread(started.wait)
        await job.cancel()
        closer = await curio.spawn(pool.aclose)
        await pool.wait_closing()
        assert pool.statistics().closed is False and job.owner is pool
        release.set()
        await closer.join()
        assert pool.closed is True and job.owner is None and job.late_result == 397

    curio.run(main)


def test_i23_closed_pool_restarts_in_new_generation():
    async def main():
        pool = curio.ThreadWorkerPool()
        first = await pool.submit(lambda: "g0")
        assert await first.join() == "g0"
        await pool.aclose()
        assert await pool.restart() == 1
        second = await pool.submit(lambda: "g1")
        assert second.generation == 1 and await second.join() == "g1"
        assert pool.jobs == [first, second]
        await pool.aclose()

    curio.run(main)


def test_i24_universal_queue_item_transformed_by_worker_and_acked():
    async def main():
        queue = curio.UniversalQueue()
        await curio.run_in_thread(queue.put, ("work", 401))
        async with curio.ThreadWorkerPool() as pool:
            label, value = await queue.get()
            job = await pool.submit(lambda number: number * 2 + 1, value)
            result = await job.join()
            await queue.task_done()
        await queue.join()
        assert (label, result) == ("work", 803)

    curio.run(main)


def test_i25_nested_tasklocal_bindings_restore_across_siblings():
    async def main():
        local = curio.TaskLocal("nested-i25", default="root")

        async def child(value):
            async with local.bind(value):
                outer = local.get()
                async with local.bind(value + ":inner"):
                    inner = local.get()
                return outer, inner, local.get()

        first = await curio.spawn(child, "east")
        second = await curio.spawn(child, "west")
        assert {await first.join(), await second.join()} == {
            ("east", "east:inner", "east"),
            ("west", "west:inner", "west"),
        }
        assert local.get() == "root"

    curio.run(main)


def test_i26_explicit_context_snapshot_overrides_worker_caller():
    async def main():
        local = curio.TaskLocal("snapshot-i26", default="root")
        token = local.set("captured")
        snapshot = curio.capture_context(local)
        local.set("caller-now")
        async with curio.ThreadWorkerPool() as pool:
            job = await pool.submit(local.get, context=snapshot)
            assert await job.join() == "captured"
        assert local.get() == "caller-now"
        local.reset(token)

    curio.run(main)


def test_i27_task_cancellation_triggers_generator_scope_finalization():
    scope_factory = curio.AsyncGeneratorScope

    async def main():
        ready = curio.Event()
        trace = []

        async def source():
            try:
                yield "open"
            finally:
                trace.append("closed")

        async def child():
            async with scope_factory() as scope:
                generator = scope.track(source())
                await generator.__anext__()
                await ready.set()
                await curio.Event().wait()

        task = await curio.spawn(child)
        await ready.wait()
        await task.cancel()
        assert trace == ["closed"]

    curio.run(main)


def test_i28_generators_finalize_reverse_registration_under_captured_context():
    async def main():
        local = curio.TaskLocal("finalizer-i28", default="root")
        trace = []

        async def source(label):
            try:
                yield label
            finally:
                trace.append((label, local.get()))

        scope = curio.AsyncGeneratorScope()
        async with local.bind("first-context"):
            first = scope.track(source("first"))
            await first.__anext__()
        async with local.bind("second-context"):
            second = scope.track(source("second"))
            await second.__anext__()
        await scope.aclose()
        assert trace == [("second", "second-context"), ("first", "first-context")]
        assert local.get() == "root"

    curio.run(main)


def test_i29_generator_failures_aggregate_in_attempt_order():
    first_error = ValueError("first-finalizer")
    second_error = LookupError("second-finalizer")

    async def main():
        async def source(error):
            try:
                yield error
            finally:
                raise error

        scope = curio.AsyncGeneratorScope()
        first = scope.track(source(first_error))
        second = scope.track(source(second_error))
        await first.__anext__()
        await second.__anext__()
        with pytest.raises(curio.GeneratorCleanupError) as caught:
            await scope.aclose()
        assert caught.value.exceptions == (second_error, first_error)
        assert scope.finalization_errors == (second_error, first_error)

    curio.run(main)


def test_i30_taskgroup_failure_waits_sibling_generator_finalizer():
    marker = RuntimeError("group-root-i30")
    scope_factory = curio.AsyncGeneratorScope

    async def main():
        ready = curio.Event()
        fail_now = curio.Event()
        trace = []

        async def source():
            try:
                yield 409
            finally:
                trace.append("generator-finalized")

        async def sibling():
            async with scope_factory() as scope:
                generator = scope.track(source())
                await generator.__anext__()
                await ready.set()
                await curio.Event().wait()

        async def fail():
            await fail_now.wait()
            raise marker

        with pytest.raises(RuntimeError) as caught:
            async with curio.TaskGroup() as group:
                await group.spawn(sibling)
                await group.spawn(fail)
                await ready.wait()
                await fail_now.set()
        assert caught.value is marker and trace == ["generator-finalized"]

    curio.run(main)


def test_i31_socket_request_crosses_worker_and_returns_reverse_direction():
    async def main():
        client, server = await curio.open_socket_stream_pair()
        pool = curio.ThreadWorkerPool()
        try:
            async def service():
                payload = await server.receive_frame()
                job = await pool.submit(lambda data: data[::-1] + b":419", payload)
                await server.send_frame(await job.join())

            task = await curio.spawn(service)
            await client.send_frame(b"feldspar")
            assert await client.receive_frame() == b"rapsdlef:419"
            await task.join()
        finally:
            await pool.aclose()
            await client.aclose()
            await server.aclose()

    curio.run(main)


def test_i32_retired_workflow_lease_retries_through_worker_once():
    async def main():
        workflow = curio.WorkflowCoordinator()
        work_id = await workflow.submit(421)
        first = await workflow.claim()
        await workflow.retire(first, requeue=True)
        workflow.restart()
        second = await workflow.claim()
        assert (second.work_id, second.attempt, second.epoch) == (work_id, 1, 1)
        async with curio.ThreadWorkerPool() as pool:
            job = await pool.submit(lambda value: value * 2, second.payload)
            await workflow.ack(second, await job.join())
        await workflow.join()
        assert await workflow.receive_result() == (work_id, 842)
        snapshot = workflow.snapshot()
        assert snapshot.retired == 1 and snapshot.finished == 1

    curio.run(main)
