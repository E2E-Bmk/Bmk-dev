import asyncio
import threading

import pytest

import curio


def test_s01_foreign_submit_socket_worker_result_and_cleanup_workflow():
    async def main():
        workflow = curio.WorkflowCoordinator()
        work_id = await curio.run_in_thread(workflow.submit_sync, ("scale", 431))
        lease = await workflow.claim()
        client, server = await curio.open_socket_stream_pair()
        pool = curio.ThreadWorkerPool()
        stack = curio.AsyncResourceStack()
        stack.push(pool)
        stack.push_concurrent(client, server)

        async def service():
            payload = int((await server.receive_frame()).decode())
            job = await pool.submit(lambda value: value * 3 + 2, payload)
            await server.send_frame(str(await job.join()).encode())

        async with stack:
            async with curio.TaskGroup() as group:
                await group.spawn(service)
                await client.send_frame(str(lease.payload[1]).encode())
                result = int((await client.receive_frame()).decode())
            await workflow.ack(lease, (lease.payload[0], result))

        await workflow.join()
        assert await workflow.receive_result() == (work_id, ("scale", 1295))
        assert client.fileno() < 0 and server.fileno() < 0 and pool.closed

    curio.run(main)


def test_s02_backpressure_cancel_receive_restart_worker_and_finalizer_recovery():
    async def main():
        left, right = await curio.open_socket_stream_pair(frame_limit=1)
        pool = curio.ThreadWorkerPool()
        trace = []
        ready = curio.Event()

        async def audit_source():
            try:
                yield "audit-open"
            finally:
                trace.append("audit-finalized")

        async def stale_receiver():
            async with curio.AsyncGeneratorScope() as scope:
                audit = scope.track(audit_source())
                await audit.__anext__()
                await ready.set()
                await left.receive_frame()

        try:
            stale_receive = await curio.spawn(stale_receiver)
            await ready.wait()
            await stale_receive.cancel()
            assert left.restart_receive() == 1

            await left.send_frame(b"resident:433")
            stale_send = await curio.spawn(left.send_frame, b"ghost:439")
            await left.wait_backpressured()
            await stale_send.cancel()
            payload = await right.receive_frame()
            job = await pool.submit(lambda data: data.upper() + b":443", payload)
            await right.send_frame(await job.join())
            assert await left.receive_frame() == b"RESIDENT:433:443"
            assert trace == ["audit-finalized"]
        finally:
            await pool.aclose()
            await left.aclose()
            await right.aclose()

    curio.run(main)


def test_s03_worker_retirement_lease_retry_and_socket_response():
    async def main():
        workflow = curio.WorkflowCoordinator()
        work_id = await workflow.submit(449)
        first_lease = await workflow.claim()
        started = threading.Event()
        release = threading.Event()

        def stale_work(value):
            started.set()
            release.wait()
            return value + 1

        pool = curio.ThreadWorkerPool()
        stale_job = await pool.submit(stale_work, first_lease.payload)
        await curio.run_in_thread(started.wait)
        await stale_job.cancel(curio.WorkerCancelled("retry-generation"))
        await workflow.retire(first_lease, requeue=True)
        workflow.restart()
        release.set()
        await stale_job.wait_retired()

        lease = await workflow.claim()
        job = await pool.submit(lambda value: value * 2, lease.payload)
        result = await job.join()
        client, server = await curio.open_socket_stream_pair()
        try:
            await server.send_frame(str(result).encode())
            observed = int((await client.receive_frame()).decode())
            await workflow.ack(lease, observed)
        finally:
            await client.aclose()
            await server.aclose()
            await pool.aclose()
        await workflow.join()
        assert await workflow.receive_result() == (work_id, 898)
        assert stale_job.late_result == 450

    curio.run(main)


def test_s04_nested_context_failed_supervisor_generator_and_resource_cleanup():
    marker = RuntimeError("system-root-s04")

    async def main():
        local = curio.TaskLocal("system-s04", default="root")
        ready = curio.Event()
        fail_now = curio.Event()
        trace = []

        async def source():
            try:
                yield "active"
            finally:
                trace.append(("generator", local.get()))

        async def sibling():
            async with local.bind("owned-branch"):
                stack = curio.AsyncResourceStack()
                stack.push(lambda: trace.append(("resource", local.get())))
                async with stack:
                    async with curio.AsyncGeneratorScope() as generators:
                        generator = generators.track(source())
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
        assert caught.value is marker
        assert trace == [("generator", "owned-branch"), ("resource", "owned-branch")]
        assert local.get() == "root"

    curio.run(main)


def test_s05_taskgroup_framed_pipeline_workers_half_close_and_stack():
    async def main():
        client, server = await curio.open_socket_stream_pair(frame_limit=1)
        pool = curio.ThreadWorkerPool(limit=1)
        stack = curio.AsyncResourceStack()
        stack.push(pool)
        stack.push_concurrent(client, server)
        values = (457, 461, 463)
        output = []

        async def producer():
            for value in values:
                await client.send_frame(str(value).encode())
            await client.send_eof()

        async def service():
            while True:
                try:
                    value = int((await server.receive_frame()).decode())
                except curio.StreamEOF:
                    break
                job = await pool.submit(lambda number: number * 2 + 5, value)
                await server.send_frame(str(await job.join()).encode())
            await server.send_eof()

        async def consumer():
            while True:
                try:
                    output.append(int((await client.receive_frame()).decode()))
                except curio.StreamEOF:
                    return

        async with stack:
            async with curio.TaskGroup() as group:
                await group.spawn(producer)
                await group.spawn(service)
                await group.spawn(consumer)

        assert output == [919, 927, 931]
        assert pool.closed and client.fileno() < 0 and server.fileno() < 0

    curio.run(main)


def test_s06_asyncio_thread_submit_curio_worker_and_coordinator_result():
    async def main():
        workflow = curio.WorkflowCoordinator()

        def foreign_submit():
            async def stage():
                return await workflow.submit(("asyncio", 467))

            return asyncio.run(stage())

        work_id = await curio.run_in_thread(foreign_submit)
        lease = await workflow.claim()
        async with curio.ThreadWorkerPool() as pool:
            job = await pool.submit(lambda item: (item[0], item[1] * 4), lease.payload)
            await workflow.ack(lease, await job.join())
        await workflow.join()
        assert await workflow.receive_result() == (work_id, ("asyncio", 1868))

    curio.run(main)


def test_s07_socket_pool_shutdown_precedes_deterministic_cleanup_failures():
    first_error = ValueError("older-error")
    second_error = LookupError("newer-error")

    async def main():
        left, right = await curio.open_socket_stream_pair()
        pool = curio.ThreadWorkerPool()
        job = await pool.submit(lambda: 479)
        assert await job.join() == 479
        trace = []

        def fail(error, label):
            trace.append((label, left.fileno(), right.fileno(), pool.closed))
            raise error

        stack = curio.AsyncResourceStack()
        stack.push(lambda: fail(first_error, "older"))
        stack.push(lambda: fail(second_error, "newer"))
        stack.push_concurrent(left, right, pool)
        with pytest.raises(curio.CleanupError) as caught:
            await stack.aclose()
        assert caught.value.exceptions == (second_error, first_error)
        assert trace == [("newer", -1, -1, True), ("older", -1, -1, True)]

    curio.run(main)


def test_s08_failed_generation_restarts_context_worker_socket_and_lease_once():
    async def main():
        local = curio.TaskLocal("system-s08", default="root")
        workflow = curio.WorkflowCoordinator()
        work_id = await workflow.submit(487)
        first_lease = await workflow.claim()
        pool = curio.ThreadWorkerPool()
        started = threading.Event()
        release = threading.Event()
        trace = []

        def stale_work():
            started.set()
            release.wait()
            return local.get()

        async def source():
            try:
                yield "generation-open"
            finally:
                trace.append(local.get())

        async with local.bind("generation-zero"):
            scope = curio.AsyncGeneratorScope()
            generator = scope.track(source())
            await generator.__anext__()
            stale_job = await pool.submit(stale_work)
            await curio.run_in_thread(started.wait)
            await stale_job.cancel()
            await workflow.retire(first_lease, requeue=True)
            await scope.aclose()
        release.set()
        await stale_job.wait_retired()
        await pool.aclose()
        await pool.restart()
        workflow.restart()

        client, server = await curio.open_socket_stream_pair()
        ready = curio.Event()

        async def stale_receive():
            await ready.set()
            await client.receive_frame()

        try:
            stale_receiver = await curio.spawn(stale_receive)
            await ready.wait()
            await stale_receiver.cancel()
            assert client.restart_receive() == 1
            lease = await workflow.claim()
            async with local.bind("generation-one"):
                job = await pool.submit(lambda value: (local.get(), value + 8), lease.payload)
                context_value, result = await job.join()
            await server.send_frame(str(result).encode())
            assert int((await client.receive_frame()).decode()) == 495
            await workflow.ack(lease, (context_value, result))
        finally:
            await client.aclose()
            await server.aclose()
            await pool.aclose()

        await workflow.join()
        assert await workflow.receive_result() == (work_id, ("generation-one", 495))
        assert trace == ["generation-zero"]
        assert stale_job.late_result == "generation-zero"
        snapshot = workflow.snapshot()
        assert snapshot.retired == 1 and snapshot.finished == 1 and snapshot.epoch == 1

    curio.run(main)

