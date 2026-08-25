from __future__ import annotations


def test_a01(tmp_path):
    import apscheduler
    assert [item.name for item in apscheduler.SchedulerRole] == ["scheduler", "worker", "both"]


def test_a02(tmp_path):
    import apscheduler
    assert [item.name for item in apscheduler.RunState] == ["starting", "started", "stopping", "stopped"]


def test_a03(tmp_path):
    import apscheduler
    assert {item.name for item in apscheduler.JobOutcome} == {"success", "error", "missed_start_deadline", "deserialization_failed", "cancelled", "abandoned"}


def test_a04(tmp_path):
    import apscheduler
    assert [item.name for item in apscheduler.ConflictPolicy] == ["replace", "do_nothing", "exception"]


def test_a05(tmp_path):
    import apscheduler
    assert [item.name for item in apscheduler.CoalescePolicy] == ["earliest", "latest", "all"]


def test_a06(tmp_path):
    import apscheduler
    @apscheduler.task(id="daily")
    def operation():
        return 1
    assert operation() == 1 and operation._apscheduler_taskdef.id == "daily"


def test_a07(tmp_path):
    import apscheduler
    from datetime import timedelta
    @apscheduler.task(max_running_jobs=2, misfire_grace_time=5, metadata={"team": "ops"})
    def operation():
        pass
    definition = operation._apscheduler_taskdef
    assert definition.max_running_jobs == 2 and definition.misfire_grace_time == timedelta(seconds=5) and definition.metadata == {"team": "ops"}


def test_a08(tmp_path):
    import apscheduler
    assert issubclass(apscheduler.JobLookupError, LookupError) and issubclass(apscheduler.ScheduleLookupError, LookupError)


def test_i01(tmp_path):
    import apscheduler
    assert apscheduler.SchedulerRole.scheduler is not apscheduler.SchedulerRole.worker
    assert apscheduler.RunState.started is not apscheduler.RunState.stopped


def test_i02(tmp_path):
    import apscheduler
    @apscheduler.task(id="x", job_executor="thread", max_running_jobs=3, metadata={"a": [1]})
    def operation():
        pass
    item = operation._apscheduler_taskdef
    assert (item.id, item.job_executor, item.max_running_jobs, item.metadata) == ("x", "thread", 3, {"a": [1]})


def test_i03(tmp_path):
    import apscheduler
    outcomes = tuple(item.name for item in apscheduler.JobOutcome)
    assert outcomes[0] == "success" and outcomes[-1] == "abandoned" and len(outcomes) == 6


def test_i04(tmp_path):
    import apscheduler
    assert {item.name for item in apscheduler.ConflictPolicy}.isdisjoint({item.name for item in apscheduler.CoalescePolicy})


def test_s01(tmp_path):
    import apscheduler
    @apscheduler.task(id="left", metadata={"side": "l"})
    def left():
        pass
    @apscheduler.task(id="right", metadata={"side": "r"})
    def right():
        pass
    left._apscheduler_taskdef.metadata["side"] = "changed"
    assert right._apscheduler_taskdef.id == "right" and right._apscheduler_taskdef.metadata == {"side": "r"}


def test_s02(tmp_path):
    import apscheduler
    assert apscheduler.Scheduler and apscheduler.AsyncScheduler
    assert apscheduler.task and apscheduler.JobOutcome.success and apscheduler.ConflictPolicy.replace
