# Rocketry Public Scheduling Specification

## Product Overview

Rocketry is a statement-based scheduling framework for Python applications.
An application owns a session, a set of named tasks, parameters, conditions,
and readable task logs. Public task declarations can be observed through the
application/session model, condition truth values, direct scheduler execution,
task return values, status fields, and log records.

This specification uses small in-memory applications with a fixed time
function. The durable facts are task declarations, condition expressions,
session parameters, one-cycle scheduler runs, returned values, and repository
log records.

## Scope

This specification covers the public imports and service-free behavior for:

- `Rocketry`, `Session`, and `FuncTask`
- `@app.task(...)`, `app.cond()`, `app.param(...)`, and `app.params(...)`
- boolean condition algebra with `true`, `false`, `&`, `|`, and `~`
- fixed-time conditions such as `daily`, `hourly`, `weekly`, and
  `time_of_day`
- task-dependence conditions such as `after_success` and `after_finish`
- task status conditions such as `succeeded(...).today`
- synchronous main-process execution through `session.run(...)` and a short
  one-cycle `session.start()`
- parameter and argument injection through `Arg`, `SimpleArg`, `FuncArg`,
  `Session`, `Task`, `Config`, and `Return`
- task status fields and Red Bird memory repository log projections

All tasks are local Python functions. Log storage is an in-memory Red Bird
repository supplied to the application.

## Installable Surface

The public imports are:

```python
from rocketry import FuncTask, Rocketry, Session
from rocketry.args import Arg, Config, FuncArg, Return, Session, SimpleArg, Task
from rocketry.conds import after_finish, after_success, daily, false, hourly, scheduler_cycles, succeeded, time_of_day, true, weekly
from redbird.repos import MemoryRepo
```

The target package is provided by the invocation environment. The tests do
not import private modules or repository test helpers.

## Product State Model

A Rocketry state consists of one application session, zero or more named
tasks, session parameters, configured execution options, a time function, and
readable task log records. A decorated task remains a Python function while
the session stores the corresponding task object and metadata.

A condition observes a boolean state from explicit task/session context or
from fixed time. A direct scheduler run evaluates enabled tasks, injects
arguments, stores successful returns, updates task status fields, and writes
run/success records. A downstream task guarded by `after_success` or
`after_finish` becomes due after the source task records the matching upstream
fact and becomes not due after the downstream task has run.

## Error Semantics

The suite avoids intentional task failures and broad exception matching.
Blocked conditions are represented by tasks that do not run: their status
remains `None` and their readable logger has no records. Missing or
incompatible public behavior is exposed by normal assertion failures.

## Cross-View Invariants

1. A task declared through `@app.task` can be located from the session by its
   public name and by the decorated function.
2. Boolean condition algebra observes the same truth table inside and outside
   task declarations.
3. Fixed-time conditions use the session time function rather than host wall
   clock state.
4. `session.run` with main execution records returned values, success status,
   and readable run/success log actions for the same task.
5. `Arg`, function parameters, task-local arguments, and meta arguments are
   materialized when the task executes.
6. `Return` exposes the successful return of an upstream task to later tasks.
7. Status conditions and task-dependence conditions observe the same
   successful upstream log fact.
8. One-cycle scheduler runs respect true and false start conditions without
   sleeping or relying on elapsed wall-clock time.

## Representative Workflows

A task can consume session parameters, run synchronously, and expose its
return:

```python
app.params(prefix="order")

@app.task(true, name="make_key", execution="main")
def make_key(prefix=Arg("prefix")):
    return f"{prefix}-42"

app.session.run("make_key")
value = Return("make_key").get_value(task=app.session["make_key"], session=app.session)
```

A two-step pipeline can run in one scheduler cycle:

```python
@app.task(true, name="extract", execution="main", priority=100)
def extract():
    return "raw"

@app.task(after_success("extract"), name="transform", execution="main", priority=10)
def transform(value=Return("extract")):
    return value.upper()

app.session.run("extract", "transform")
```

A short local scheduler workflow can shut down after one cycle:

```python
app = Rocketry(config={"execution": "main", "shut_cond": scheduler_cycles() >= 1})
app.session.start()
```

## Non-Goals

- Wall-clock loops, sleeps, timing races, long-running schedulers, and
  performance claims.
- Process pools, thread scheduling guarantees, async service integration, and
  multiprocessing portability behavior.
- Network access, servers, sockets, databases, credentials, or host-specific
  state.
- Private modules, repository tests, command tasks, file-system side effects,
  source checkout mutation, and exact incidental log text or traceback text.
- Exact generated metadata, package build output, Docker runtime behavior, or
  external service availability.

## Invocation Protocol

Install or otherwise expose the target `rocketry` package and the listed
requirements, then run pytest from this task directory against the two public
test files. The tests create only in-memory applications and Red Bird memory
repositories.

The same public cases are replayed with Python 3.10 and Python 3.11. JSON
reporting is used only to record local reproducibility evidence.

## Environment

Run on Linux with Python 3.11 without network access. Python 3.10 is also
supported for compatibility replay. The target package is not pre-installed;
the runner supplies it through installation or `PYTHONPATH`. Required packages
are `pytest`, `pytest-json-report`, `pydantic`, `python-dateutil`, and
`redbird`.

No service credentials, endpoints, databases, process pools, Docker runtime,
or host-specific scheduler state are required.

## Evaluation Notes

Assertions prioritize public task/session state, fixed-time condition
results, parameter materialization, `Return` values, status fields, log
actions, log counts, and short one-cycle scheduler workflows. Exact log
message text, traceback content, generated run identifiers, and wall-clock
timing are intentionally outside the contract.

The local replay records are reproducibility artifacts for this package and
must be interpreted with the explicit artifact-only status and same-process
execution boundary.
