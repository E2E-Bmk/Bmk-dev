# Luigi Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Luigi is a Python workflow library for declaring parameterized tasks, linking them through dependencies, and running the resulting graph through a scheduler and worker. A task defines its required upstream tasks, its output targets, and the work that creates those targets. Luigi then schedules only the tasks whose dependencies are complete, runs task code in worker processes, and records task state through a scheduler view.

## Non-Goals

- Contrib integrations for Hadoop, Spark, HDFS, S3, GCS, BigQuery, Redis, SQL databases, Kubernetes, Prometheus, Dropbox, SSH, FTP, and cloud services are out of scope.
- Browser visualizer pages, HTML structure, static assets, and JavaScript behavior are out of scope.
- Starting, daemonizing, supervising, or backgrounding the central scheduler process is out of scope.
- Exact log text, exact HTML text, exact stack trace formatting, and exact execution-summary line wrapping are out of scope.
- Private modules, private helper functions, private scheduler data structures, and local test helper utilities are out of scope.
- Range tools, grep/dependency helper console tools, email notification transports, database task history storage, and metrics collectors are out of scope unless they affect the core APIs listed above.

## Representative Workflows

```python
import datetime
import luigi

class DailyWords(luigi.Task):
    day = luigi.DateParameter()
    root = luigi.PathParameter()

    def output(self):
        return luigi.LocalTarget(self.root / f"words-{self.day:%Y-%m-%d}.txt")

    def run(self):
        with self.output().open("w") as f:
            f.write("apple\nbanana\n")

class CountLetters(luigi.Task):
    day = luigi.DateParameter()
    root = luigi.PathParameter()

    def requires(self):
        return DailyWords(day=self.day, root=self.root)

    def output(self):
        return luigi.LocalTarget(self.root / f"counts-{self.day:%Y-%m-%d}.txt")

    def run(self):
        with self.input().open("r") as source:
            words = source.read().splitlines()
        with self.output().open("w") as target:
            for word in words:
                target.write(f"{word}\t{len(word)}\n")

luigi.build(
    [CountLetters(day=datetime.date(2026, 7, 10), root="data")],
    local_scheduler=True,
)
```

The build must first check the count target, then check and run `DailyWords` when its target is missing, then pass the `DailyWords` target through `CountLetters.input()`, then write the count target. A second build with the same parameter values and existing files must report both tasks complete without running either `run()` method again.

The equivalent command-line invocation must parse hyphenated task parameters and use the same local scheduler behavior:

```console
luigi --module my_workflow CountLetters --day 2026-07-10 --root data --local-scheduler
```

## Task Lifecycle

This section covers how tasks declare dependencies, outputs, and work.

**Core task methods.** `requires()` returns no dependencies by default. It must return tasks or nested dict/list/tuple structures containing tasks when the task has dependencies. `output()` returns no targets by default. It must return a target or nested structures containing targets when output-based completion is used. `run()` performs no work by default. A subclass must override it when the task creates outputs itself.

**Completion.** `complete()` returns `True` when every flattened output target exists. It returns `False` for a task with no outputs and no override. It raises when an output object has no usable `exists()` method.

**Dependency mapping.** `input()` returns the outputs of the tasks returned by `requires()` and preserves list, tuple, and dict containers. The nested container shape must match between `requires()` and `input()`.

**Cloning.** `clone(cls=None, **kwargs)` returns a new task of `cls` or the current task class, copying same-named parameter values from the source task and overriding names present in `kwargs`.

**Task identity.** `get_task_family()` returns the class name when no namespace is set and returns `<namespace>.<ClassName>` when a namespace is set. Task equality and hashing are based on class and the identifier formed from significant public parameters. Two instances with equal significant values must compare equal and hash equal even when insignificant values differ. The task representation must include the task family and significant parameters serialized as strings; insignificant parameters must be omitted.

**Lifecycle callbacks.** When `run()` completes successfully, `on_success()` must be called on the task instance. When `run()` raises an exception, `on_failure(exception)` must be called with the exception instance before the task is marked as failed.

**Event system.** `Task.event_handler(event_name)` must register a callback function as a handler for the named event. `Task.trigger_event(event_name, *args)` must invoke all registered handlers for that event with the supplied arguments. `Task.remove_event_handler(event_name, handler)` must unregister the specified handler; subsequent triggers must not invoke the removed handler.

**ExternalTask.** `ExternalTask` represents a dependency created outside Luigi. Its `run` attribute is `None`. An incomplete external dependency must leave dependent work pending rather than running the dependent task.

**WrapperTask.** `WrapperTask` represents a task that only wraps requirements. Its `complete()` returns `True` only when every flattened requirement is complete.

**Config.** `Config` is a parameterized configuration container. A `Config` subclass must read parameters through the same default, config, and command-line machinery as `Task`.

**DynamicRequirements.** `DynamicRequirements(requirements, custom_complete=None)` wraps requirements yielded from `run()`. Its `flat_requirements` returns the flattened task list, `paths` returns their outputs, and `complete()` returns `True` only when every wrapped requirement is complete. When `custom_complete` is provided, `complete()` must return the result of calling it with the per-task completion function.

**Namespace control.** `namespace(namespace=None, scope="")` sets the namespace used by task classes declared after the call. A class-level `task_namespace` value must take precedence over `namespace()`. `auto_namespace(scope="")` sets the namespace for matching task classes to their Python module name.

## Parameter Declaration and Parsing

This section covers how parameters are declared, parsed, and serialized.

**Parameter sources and precedence.** A parameter declared on a task class must become an instance attribute with the parsed or normalized value. Constructor keyword arguments must override every other source. Root-task command-line flags must override config and defaults for the root task. Class-qualified command-line flags must override config and defaults for later instances of that class. Config values must override parameter defaults. A missing required value must raise `MissingParameterException`.

**Positional and unknown parameters.** Positional constructor arguments must bind only to parameters whose `positional` attribute is true, in declaration order. Too many positional values must raise `UnknownParameterException`. Passing the same parameter by position and keyword must raise `DuplicateParameterException`. Unknown keyword parameters must raise `UnknownParameterException`.

**Significance and visibility.** When `significant=False`, the parameter is omitted from task equality, hashing, public serialized identity, and representation, while the value remains available on the task instance. `visibility=ParameterVisibility.PUBLIC` exposes the parameter in public serialized values. `HIDDEN` omits it from public web-style views. `PRIVATE` omits it from public serialized values and `to_str_params(only_public=True)` output.

**Serialization methods.** `to_str_params(only_significant=False, only_public=False)` must serialize task parameter values. With `only_significant=True`, insignificant parameters must be omitted. With `only_public=True`, private parameters must be omitted. `from_str_params(params_str)` must parse the supplied string mapping and construct a task; missing keys must fall back to class-level defaults.

**Core parameter types.** `Parameter` and `StrParameter` return strings from `parse()` and serialize with `str(x)`. `IntParameter` parses base-10 strings into `int`. `FloatParameter` parses strings into `float`. `BoolParameter` parses true and false strings case-insensitively and must reject unknown strings with `ValueError`. `DateParameter` parses `YYYY-MM-DD` into `datetime.date`. `MonthParameter` parses `YYYY-MM`. `YearParameter` parses `YYYY`. `DateHourParameter` parses `YYYY-MM-DDTHH`. `DateMinuteParameter` parses `YYYY-MM-DDTHHMM`. `DateSecondParameter` parses `YYYY-MM-DDTHHMMSS`. Invalid strings for any date parameter must raise `ValueError`. Date parameters must serialize back to their documented string format.

**Collection parameters.** `ListParameter` parses JSON arrays and returns an immutable normalized sequence. `DictParameter` parses JSON objects into an immutable ordered mapping. `TupleParameter` parses JSON array syntax into tuples; a plain string must raise `ValueError`.

**Enum parameters.** `EnumParameter(enum=SomeEnum)` parses an enum member name into that member and serializes to the member name. Unknown names must raise `ValueError` or `KeyError`. `EnumListParameter(enum=SomeEnum)` parses comma-separated names into a tuple and serializes back to comma-separated names.

**Constrained parameters.** `NumericalParameter` parses with its `var_type` and accepts only values inside the configured interval defined by `min_value`, `max_value`, `left_op`, and `right_op`. Missing `var_type`, `min_value`, or `max_value` must raise `ParameterException`. `ChoiceParameter(choices=...)` accepts only configured choices; missing choices must raise `ParameterException` and invalid values must raise `ValueError`. `ChoiceListParameter` parses comma-separated values, preserves order and duplicates, accepts an empty string as an empty tuple, and rejects values outside choices.

**Path parameter.** `PathParameter` returns strings from `parse()`. `normalize(x)` returns a `pathlib.Path`, converts to absolute when `absolute=True`, and raises `ValueError` when `exists=True` and the path does not exist.

**Optional parameters.** Optional parameter classes parse the empty string as `None`, serialize `None` as the empty string, and warn when a supplied non-`None` constructor value has the wrong Python type.

## Target Operations

This section covers how targets represent and manage task outputs.

**Target existence.** `Target.exists()` is the abstract existence predicate. A target subclass must return `True` only when the output resource exists.

**FileSystemTarget.** `FileSystemTarget(path)` stores `path` as a string and delegates `exists()` and `remove()` to its `fs` object. `temporary_path()` returns a context manager that yields a temporary path, creates parent directories before yielding, and renames the temporary path to the final path only when the context exits without an exception. If the context body raises, the final path must not be committed.

**LocalTarget construction.** `LocalTarget` requires a `path` argument; construction without `path` and without `is_tmp=True` must raise `Exception`. With `is_tmp=True`, it must create a temporary local path. `LocalTarget.path` must return the stored path string. `LocalTarget.exists()` must reflect whether the local file exists.

**Read and write.** `open("w")` must create parent directories, write through a temporary file, and atomically replace the final path when the stream is closed successfully. If the stream exits with an exception, the final path must not be committed. `open("r")` must return a readable stream and must raise the underlying file exception when the path does not exist. Modes other than read or write must raise `Exception`.

**File operations.** `move(new_path, raise_if_exists=False)`, `copy(new_path, raise_if_exists=False)`, and `remove()` must delegate to the local file system. When `raise_if_exists=True` and the destination exists, move/copy must raise a file-exists exception.

## Workflow Execution and Configuration

This section covers how builds, runs, and configuration drive task execution.

**build function.** `build(tasks, ...)` accepts an iterable of already constructed task objects. It must default to `no_lock=True` when no value is supplied. It returns `True` or `False` by default, using `True` when scheduling and worker execution completed without scheduling errors. With `detailed_summary=True`, it returns a `LuigiRunResult`.

**LuigiRunResult.** `LuigiRunResult` must expose `status` as a `LuigiStatusCode` value, `scheduling_succeeded` as a boolean, and `summary_text` as a string. `LuigiStatusCode` values include `SUCCESS`, `FAILED`, `MISSING_EXT`, `NOT_RUN`, and `SCHEDULING_FAILED`.

**run function.** `run` parses command-line style arguments. When `cmdline_args` is `None`, it must use `sys.argv[1:]`. When `cmdline_args` is supplied, the value must be a list or tuple; other types must raise `TypeError`. When `main_task_cls` is supplied, the task family's name must be inserted as the root task. When `local_scheduler=True`, `--local-scheduler` must be appended.

**Scheduler modes.** When `local_scheduler=True`, the build must use an in-memory scheduler in the current process. When `local_scheduler=False`, it must connect to a remote scheduler. Connection failures must raise the RPC or connection exception.

**Worker-scheduler factory.** When `worker_scheduler_factory` is supplied, Luigi must use its `create_local_scheduler`, `create_remote_scheduler`, and `create_worker` methods instead of defaults.

**Completion and reuse.** A task whose outputs already exist must be recorded as complete and must not run again. A task whose dependencies are incomplete must not run until every dependency is complete.

**Priority.** A task with higher `priority` must be preferred over lower-priority tasks only among tasks whose dependencies are already satisfied. Dependency readiness must take precedence over priority.

**Dynamic dependencies.** Dependencies yielded from `run()` must suspend the current task, run the yielded tasks, and then restart the yielding task's `run()` method from the beginning. The yielding task must therefore be idempotent.

**CLI grammar.** The CLI shape is `luigi [--module MODULE] [--local-scheduler] [--workers N] [--help] [--help-all] TaskFamily [task parameters]`. `--module MODULE` must import the module before resolving the root task family. The root task family is required for normal execution; missing it must terminate with a command-line error. Task parameters with underscores must be exposed as hyphenated CLI flags. Class-qualified flags must use `--TaskFamily-param-name` format. `--help` must display core and root-task flags.

**Return codes.** The CLI must use configured return-code values from `[retcode]`. With default settings, unhandled internal exceptions exit with code `4`, and other categories default to code `0`. When several configured nonzero categories apply, the numerically greatest code must be used.

**Configuration.** The cfg parser must read, in increasing priority, `/etc/luigi/client.cfg`, `/etc/luigi/luigi.cfg`, `client.cfg`, `luigi.cfg`, and the path named by `LUIGI_CONFIG_PATH`. The toml parser is selected by `LUIGI_CONFIG_PARSER=toml`. Cfg values must support environment-variable interpolation using `${ENVVAR}`; a missing variable reference must raise a configuration interpolation error. Parameter defaults from config must use a section matching the task family and an option matching the parameter name. Config classes must use the class name as the section name.

## State Model

Luigi exposes one workflow state through three public projections:

- The Python projection: task objects, parameters, targets, `complete()`, `input()`, `output()`, `requires()`, `luigi.build`, and `luigi.run`.
- The command-line projection: task family names, root-task arguments, class-qualified arguments, config files, local scheduler flags, and process exit status.
- The scheduler/worker projection: task states such as pending, running, done, failed, not run, missing external dependency, and scheduling failure, plus `LuigiRunResult` summaries.

## Error Semantics

- Missing a required task parameter must raise `MissingParameterException`.
- Passing an unknown task parameter must raise `UnknownParameterException`.
- Passing the same task parameter by position and keyword must raise `DuplicateParameterException`.
- Creating a parameter with an invalid `config_path` object must raise `ParameterException`.
- Creating `NumericalParameter` without `var_type`, `min_value`, or `max_value` must raise `ParameterException`.
- Creating `ChoiceParameter` without `choices` must raise `ParameterException`.
- Parsing an invalid integer, float, date, time, JSON value, enum name, choice, path, or bounded number must raise the parsing or validation exception for that parameter type.
- Constructing `LocalTarget()` without `path` and without `is_tmp=True` must raise `Exception`.
- Opening a `LocalTarget` with a mode other than read or write must raise `Exception`.
- Reading a missing `LocalTarget` must raise the underlying file exception.
- Returning a target object from `requires()` must be treated as invalid dependency structure during scheduling.
- A failure in `Task.requires()` or `Task.complete()` during scheduling must be reported as a scheduling failure.
- A failure in `Task.run()` must be reported as task failure and must call `on_failure(exception)`.
- Remote scheduler communication failure must raise `RPCError` or the underlying request exception.

## Cross-View Invariants

1. Constructor values, root CLI values, class-qualified CLI values, config values, and parameter defaults must resolve to one task instance value using Luigi's precedence rules, and that value must be the value visible from Python attributes and scheduler parameter serialization.
2. The same root task run through `luigi.build(..., local_scheduler=True)` and through `luigi --local-scheduler` must schedule the same dependency graph when given equivalent parsed parameter values.
3. A `LocalTarget` written by a task must make `Target.exists()`, `Task.complete()`, downstream `Task.input()`, and repeated local scheduler runs agree that the output exists.
4. If a dependency task fails, downstream tasks that require it must remain not run or pending due to upstream failure; they must not report success.
5. If an `ExternalTask` output is missing, dependent tasks must be reported as missing external dependency or pending; they must not run before the external output exists.
6. A task state transition recorded by the worker must be reflected in the `LuigiRunResult.status`, `summary_text`, and boolean scheduling result according to the same completed, failed, scheduling-failed, missing-external, and not-run categories.
7. Task namespace and family strings must be identical across Python construction, command-line root task lookup, task representation, and scheduler records.
8. Parameter visibility must affect public serialized parameter views and scheduler/web-style parameter exposure without changing the Python attribute value used by task code.
9. Priority must affect runnable task ordering only after dependency completion; a low-priority ready task must run before a high-priority task whose dependencies are not complete.
10. Dynamic requirements yielded from `run()` must become scheduler-visible dependencies and their outputs must be passed back through the yielded result or through `input()` after the yielding task restarts.

## Public Interface

### Import Surface

The package must expose these top-level imports:

```python
import luigi

from luigi import (
    Task, ExternalTask, WrapperTask, Config, DynamicRequirements,
    Target, LocalTarget,
    Parameter, StrParameter, IntParameter, FloatParameter, BoolParameter,
    DateParameter, MonthParameter, YearParameter, DateHourParameter,
    DateMinuteParameter, DateSecondParameter, DateIntervalParameter,
    TimeDeltaParameter, PathParameter, TaskParameter,
    ListParameter, TupleParameter, DictParameter,
    EnumParameter, EnumListParameter,
    NumericalParameter, ChoiceParameter, ChoiceListParameter,
    OptionalParameter, OptionalStrParameter, OptionalIntParameter,
    OptionalFloatParameter, OptionalBoolParameter, OptionalPathParameter,
    OptionalDictParameter, OptionalListParameter, OptionalTupleParameter,
    OptionalChoiceParameter, OptionalNumericalParameter,
    Event, LuigiStatusCode, RemoteScheduler, RPCError,
    build, run, namespace, auto_namespace,
)
```

The package must expose these documented module imports:

```python
from luigi.parameter import (
    ParameterVisibility, ParameterException,
    MissingParameterException, UnknownParameterException,
    DuplicateParameterException,
)
from luigi.target import (
    FileSystemTarget, FileSystemException, FileAlreadyExists,
    MissingParentDirectory, NotADirectory,
)
from luigi.execution_summary import LuigiRunResult
```

The installed console entry point is `luigi`. `python -m luigi` is supported and must accept the same task invocation arguments as the console entry point for running tasks.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| Task | class | Base unit of work with dependencies and outputs |
| ExternalTask | class | Dependency created outside the workflow |
| WrapperTask | class | Task that only wraps requirements |
| Config | class | Parameterized configuration container |
| DynamicRequirements | class | Wrap requirements yielded from run() |
| Target | class | Abstract existence predicate for task outputs |
| LocalTarget | class | Local file target with atomic write |
| FileSystemTarget | class | Abstract file system target |
| Parameter | descriptor | String parameter descriptor |
| IntParameter | descriptor | Integer parameter descriptor |
| FloatParameter | descriptor | Float parameter descriptor |
| BoolParameter | descriptor | Boolean parameter descriptor |
| DateParameter | descriptor | Date parameter (YYYY-MM-DD) |
| PathParameter | descriptor | Filesystem path parameter |
| ListParameter | descriptor | JSON array parameter |
| DictParameter | descriptor | JSON object parameter |
| EnumParameter | descriptor | Enum member name parameter |
| NumericalParameter | descriptor | Bounded numeric parameter |
| ChoiceParameter | descriptor | Constrained-choice parameter |
| build | function | Run tasks from Python with a scheduler |
| run | function | Parse CLI arguments and run tasks |
| namespace | function | Set the namespace for subsequent task classes |
| auto_namespace | function | Set namespace to Python module name |
| Event | class | Task lifecycle event identifiers |
| LuigiStatusCode | class | Workflow outcome status codes |
| LuigiRunResult | class | Detailed execution result with summary |
| RemoteScheduler | class | Client for a remote scheduler |
| RPCError | exception | Remote scheduler communication failure |

### CLI Entry Points

| Invocation | Supported | Required behavior |
| --- | --- | --- |
| `luigi --module pkg.mod TaskFamily --local-scheduler` | yes | imports `pkg.mod`, resolves `TaskFamily`, parses task flags, runs with an in-memory scheduler |
| `python -m luigi --module pkg.mod TaskFamily --local-scheduler` | yes | same task invocation behavior as `luigi` |
| `luigi TaskFamily` without `--local-scheduler` | yes | connects to the configured remote scheduler |

CLI return code behavior:

| Condition | Default code | Config key |
| --- | ---: | --- |
| Successful run or only default-zero categories apply | 0 | n/a |
| Missing external dependency | 0 | `[retcode] missing_data` |
| Task failure | 0 | `[retcode] task_failed` |
| Already running or lock conflict | 0 | `[retcode] already_running` |
| Scheduling error | 0 | `[retcode] scheduling_error` |
| Not granted run permission | 0 | `[retcode] not_run` |
| Unhandled internal exception | 4 | `[retcode] unhandled_exception` |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Core workflows use local scheduler execution, local configuration files, and local targets.

## Appendix B: Assessment Notes

Compatibility covers user-facing imports, task objects, output files, configuration, command invocations, local scheduler runs, and `luigi.build` or `luigi.run` outcomes. Task graphs, parameters, completion state, target side effects, worker results, and public errors form the compatibility boundary without depending on private layouts, exact log wording, browser output, daemon management, or external services.
