# Luigi Specification

## Product Overview

Luigi is a Python workflow library for declaring parameterized tasks, linking them through dependencies, and running the resulting graph through a scheduler and worker. A task defines its required upstream tasks, its output targets, and the work that creates those targets. Luigi then schedules only the tasks whose dependencies are complete, runs task code in worker processes, and records task state through a scheduler view.

## Scope

This specification covers the core local workflow surface:

- Task graph declaration with `Task`, `ExternalTask`, `WrapperTask`, `Config`, `DynamicRequirements`, `namespace`, and `auto_namespace`.
- Parameter declaration, parsing, serialization, defaults, configuration ingestion, command-line ingestion, identity, equality, and visibility for the core parameter classes exported from `luigi`.
- Local file outputs through `Target`, `FileSystemTarget`, `LocalTarget`, and the associated local file system operations.
- Local scheduler execution through the `luigi` command, `python -m luigi`, `luigi.run`, and `luigi.build`.
- Worker and scheduler task-state outcomes visible through return values, detailed summaries, task completion state, and task status callbacks.
- Configuration files and environment variables that affect core execution, parameter defaults, worker behavior, scheduler selection, and command return codes.

## Installable Surface

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

## Product State Model

Luigi exposes one workflow state through three public projections:

- The Python projection: task objects, parameters, targets, `complete()`, `input()`, `output()`, `requires()`, `luigi.build`, and `luigi.run`.
- The command-line projection: task family names, root-task arguments, class-qualified arguments, config files, local scheduler flags, and process exit status.
- The scheduler/worker projection: task states such as pending, running, done, failed, not run, missing external dependency, and scheduling failure, plus `LuigiRunResult` summaries.

Cross-view invariants in the state model:

- A parameter value passed to a task constructor must appear on the task instance, in `to_str_params()`, in the task representation, and in the scheduler entry for that task when the parameter is public and significant.
- A root task created through the command line with task-specific flags must produce the same parsed parameter values as constructing that task in Python with the corresponding keyword arguments.
- A task whose `LocalTarget` output exists must return `True` from `complete()` and must be reported as already complete rather than run again during a later local scheduler invocation.
- A task whose `run()` finishes without creating all outputs returned by `output()` must not unlock downstream work as complete when output-based completion checking is active.
- A dependency returned from `requires()` must be visible through `input()` as the dependency's output target using the same nested list, tuple, or dict shape.
- A failed `run()` call must surface as task failure in the detailed execution result and must not be reported as a successful workflow.

## Public API

### Tasks

`Task` is the base unit of work.

```python
class Task:
    priority = 0
    resources = {}
    worker_timeout = None
    max_batch_size = float("inf")

    def requires(self): ...
    def output(self): ...
    def run(self): ...
    def complete(self): ...
    def input(self): ...
    def clone(self, cls=None, **kwargs): ...
    @classmethod
    def get_params(cls): ...
    @classmethod
    def get_param_names(cls, include_significant=False): ...
    @classmethod
    def from_str_params(cls, params_str): ...
    def to_str_params(self, only_significant=False, only_public=False): ...
    @classmethod
    def get_task_namespace(cls): ...
    @classmethod
    def get_task_family(cls): ...
    @classmethod
    def event_handler(cls, event): ...
    @classmethod
    def remove_event_handler(cls, event, callback): ...
    def trigger_event(self, event, *args, **kwargs): ...
    def on_failure(self, exception): ...
    def on_success(self): ...
```

- `requires()` returns no dependencies by default. It must return tasks or nested dict/list/tuple structures containing tasks when the task has dependencies. It raises during scheduling when it returns values that Luigi cannot flatten into tasks.
- `output()` returns no targets by default. It must return a target or nested dict/list/tuple structures containing targets when output-based completion is used. It raises during completion when a returned target does not implement `exists()`.
- `run()` performs no work by default. A subclass must override it when the task creates outputs itself. A raised exception must mark the task as failed and must be passed to `on_failure()`.
- `complete()` returns `True` when every flattened output target exists. It returns `False` for a task with no outputs and no override. It raises when an output object has no usable `exists()` method.
- `input()` returns the outputs of the tasks returned by `requires()` and preserves list, tuple, and dict containers. It raises when the dependency structure cannot be mapped to tasks.
- `clone(cls=None, **kwargs)` returns a new task of `cls` or the current task class, copying same-named parameter values from the source task and overriding names present in `kwargs`. It raises the same parameter exceptions as constructing the destination task.
- `get_task_family()` returns the class name when no namespace is set and returns `<namespace>.<ClassName>` when a namespace is set.
- Task equality and hashing are based on class and the identifier formed from significant public parameters. Two instances of the same task class with equal significant public parameter values must compare equal and have the same hash even when insignificant values differ. Different significant values must compare unequal.
- The task representation includes the task family and significant parameters serialized as strings. Insignificant parameters must be omitted from the representation.

`ExternalTask` represents a dependency created outside Luigi. Its `run` attribute is `None`. An incomplete external dependency must leave dependent work pending or missing rather than running the dependent task.

`WrapperTask` represents a task that only wraps requirements. Its `complete()` returns `True` only when every flattened requirement is complete. It raises when requirement completion raises.

`Config` is a parameterized configuration container. A `Config` subclass must read parameters through the same default, config, and command-line machinery as `Task`, but it is used to expose configuration values rather than scheduled work.

`DynamicRequirements(requirements, custom_complete=None)` wraps requirements yielded from `run()`. Its `flat_requirements` returns the flattened task list, `paths` returns their outputs, and `complete(complete_fn=None)` returns `True` only when the default or supplied completion function reports every wrapped requirement complete. When `custom_complete` is provided, `complete()` must return the result of calling it with the per-task completion function.

`namespace(namespace=None, scope="")` sets the namespace used by task classes declared after the call. The more specific matching module scope must take precedence over a broader scope. A class-level `task_namespace` value must take precedence over `namespace()`.

`auto_namespace(scope="")` sets the namespace for matching task classes to their Python module name. Calling `namespace(scope=...)` with no namespace must reset a previous automatic namespace for that scope.

### Parameters

Parameters are descriptors declared on task or config classes. Constructor arguments common to parameter classes are:

```python
Parameter(
    default=<no value>,
    significant=True,
    description=None,
    config_path=None,
    positional=True,
    always_in_help=False,
    batch_method=None,
    visibility=ParameterVisibility.PUBLIC,
)
```

- A parameter declared on a task class must become an instance attribute with the parsed or normalized value selected for that task instance.
- Constructor keyword arguments must override every other source for that task instance. Root-task command-line flags must override config and defaults for the root task constructed by the CLI. Class-qualified command-line flags must override config and defaults for later instances of that class. Config values must override parameter defaults. A missing required value must raise `MissingParameterException`.
- Positional constructor arguments must bind only to parameters whose `positional` attribute is true, in declaration order. Too many positional values must raise `UnknownParameterException`. Passing the same parameter by position and keyword must raise `DuplicateParameterException`.
- Unknown keyword parameters must raise `UnknownParameterException`.
- `significant=False` must remove that parameter from task equality, hashing, public serialized identity, and representation, while the value remains available on the task instance.
- `visibility=ParameterVisibility.PUBLIC` exposes the parameter in public serialized values. `HIDDEN` omits it from public web-style views but allows database history storage. `PRIVATE` omits it from public serialized values and parameter visibility output.
- `parse(x)` converts command-line and config strings into Python values. `serialize(x)` converts Python values into strings for task identity and display. `normalize(x)` validates or canonicalizes constructor, default, config, or parsed values. A parse or normalize failure must propagate to the caller as the underlying exception type unless a parameter subclass documents a more specific exception.
- `from_str_params(params_str)` must parse the supplied string mapping and construct a task. Missing keys must fall back to the same class-level value resolution used by direct construction. Bad keys or bad values must raise the same exceptions as direct construction or parsing.
- `to_str_params(only_significant=False, only_public=False)` must serialize task parameter values. With `only_significant=True`, insignificant parameters must be omitted. With `only_public=True`, private parameters must be omitted and hidden parameters must be omitted from public-only output.

Core parameter value contracts:

- `Parameter` and `StrParameter` return strings from `parse()` and serialize with `str(x)`. A non-string value supplied to plain `Parameter` must be accepted and must emit a warning about the type.
- `IntParameter` parses base-10 strings into `int`. `FloatParameter` parses strings into `float`. Invalid strings must raise `ValueError`.
- `BoolParameter` parses true strings and false strings case-insensitively, supports boolean constructor values, and must reject strings outside its accepted true/false vocabulary with `ValueError`.
- `DateParameter` parses `YYYY-MM-DD` into `datetime.date`. `MonthParameter` parses `YYYY-MM` into a date representing the month. `YearParameter` parses `YYYY` into a date representing the year. Invalid strings must raise `ValueError`.
- `DateHourParameter` parses `YYYY-MM-DDTHH`. `DateMinuteParameter` parses `YYYY-MM-DDTHHMM`. `DateSecondParameter` parses `YYYY-MM-DDTHHMMSS` style values used by Luigi's serializer. Invalid strings must raise `ValueError`.
- `DateIntervalParameter` parses Luigi date-interval strings and returns a date interval object. Unsupported interval syntax must raise `ValueError` or the interval parser's documented exception.
- `TimeDeltaParameter` parses duration values accepted by Luigi and returns `datetime.timedelta`. Invalid duration strings must raise `ValueError`.
- `ListParameter` parses JSON arrays and returns an immutable normalized sequence suitable for hashing. Invalid JSON or schema violations must raise the JSON or schema validation exception.
- `DictParameter` parses JSON objects into an immutable ordered mapping suitable for hashing. Invalid JSON or schema violations must raise the JSON or schema validation exception.
- `TupleParameter` parses JSON array syntax and Python tuple literal syntax into tuples. A parsed plain string must raise `ValueError`.
- `EnumParameter(enum=SomeEnum)` parses an enum member name into that enum member and serializes an enum member to its name. Unknown names must raise `ValueError` or `KeyError`.
- `EnumListParameter(enum=SomeEnum)` parses a comma-separated list of enum member names into a tuple of enum members and serializes the tuple back to comma-separated names. Unknown names must raise `ValueError` or `KeyError`.
- `NumericalParameter(var_type=..., min_value=..., max_value=..., left_op=operator.le, right_op=operator.lt)` parses with `var_type` and accepts only values inside the configured interval. Missing `var_type`, `min_value`, or `max_value` must raise `ParameterException`; out-of-range values must raise `ValueError`.
- `ChoiceParameter(choices=..., var_type=str)` parses with `var_type` and accepts only configured choices. Missing choices must raise `ParameterException`; mismatched choice element types must raise `AssertionError`; invalid values must raise `ValueError`.
- `ChoiceListParameter` parses comma-separated values, applies `var_type`, preserves order and duplicates, accepts an empty string as an empty tuple, and rejects values outside the configured choices with `ValueError`.
- `PathParameter(absolute=False, exists=False)` returns command-line and config strings unchanged from `parse()`. `normalize(x)` returns a `pathlib.Path`, converts it to an absolute path when `absolute=True`, and raises `ValueError` when `exists=True` and the normalized path does not exist.
- Optional parameter classes parse the empty string as `None`, serialize `None` as the empty string, preserve non-`None` values through the base parameter behavior, and warn when a supplied non-`None` constructor value has the wrong Python type.

### Targets

`Target.exists()` is the abstract existence predicate for task outputs. A target subclass must return `True` only when the output resource exists and `False` when it does not. Failure to inspect the resource must raise the underlying resource exception.

`FileSystemTarget(path)` stores `path` as a string and delegates `exists()` and `remove()` to its `fs` object. Its `open(mode)` method must be implemented by subclasses. `temporary_path()` returns a context manager that yields a temporary path, creates parent directories before yielding, and renames the temporary path to the final path only when the context exits without an exception.

`LocalTarget(path=None, format=None, is_tmp=False)` is the local file target.

- Construction with a path must store that path as `path` and use the default Luigi format when `format` is omitted.
- Construction with no path must raise `Exception` unless `is_tmp=True`; with `is_tmp=True`, it must create a temporary local path.
- `exists()` returns whether the local file path exists.
- `open("w")` must create parent directories, write through a temporary file, and atomically replace the final path when the stream is closed successfully. If the stream exits with an exception, the final path must not be committed by that close operation.
- `open("r")` must return a readable stream for the final path and must raise the underlying file exception when the path does not exist.
- Binary mode letters `b` and text mode letters `t` must be ignored for mode selection; binary data workflows must use a no-op format instead of relying on `"b"`.
- Modes other than read or write must raise `Exception`.
- `move(new_path, raise_if_exists=False)`, `copy(new_path, raise_if_exists=False)`, and `remove()` must delegate to the local file system. When `raise_if_exists=True` and the destination exists, move/copy must raise a file-exists exception or runtime error as documented by the local operation.
- `fn` returns `path` and must emit a deprecation warning.
- A temporary target with `is_tmp=True` must remove its file during cleanup when it still exists.

### Execution APIs

```python
luigi.build(tasks, worker_scheduler_factory=None, detailed_summary=False, **env_params)
luigi.run(cmdline_args=None, main_task_cls=None, worker_scheduler_factory=None, local_scheduler=False, detailed_summary=False)
```

- `build()` accepts an iterable of already constructed task objects. It must default to `no_lock=True` when no `no_lock` value is supplied. It returns `True` or `False` by default, using `True` when scheduling and worker execution completed without scheduling errors. With `detailed_summary=True`, it returns a `LuigiRunResult`.
- `run()` parses command-line style arguments. With `cmdline_args=None`, it must use `sys.argv[1:]`. With `cmdline_args` supplied, the value must be a list or tuple; other types must raise `TypeError`. With `main_task_cls` supplied, the task family's name must be inserted as the root task. With `local_scheduler=True`, `--local-scheduler` must be appended. With `detailed_summary=True`, it returns `LuigiRunResult`; otherwise it returns the boolean scheduling result.
- `local_scheduler=True` must use an in-memory scheduler in the current process. `local_scheduler=False` must connect to a remote scheduler URL built from `scheduler_url` when provided, or from `scheduler_host` and `scheduler_port` otherwise. Connection failures must raise the RPC or connection exception.
- `worker_scheduler_factory`, when supplied, must provide methods named `create_local_scheduler`, `create_remote_scheduler`, and `create_worker`. Luigi must use these factory methods instead of its default scheduler and worker constructors.
- A task whose outputs already exist must be recorded as complete and must not run again.
- A task whose dependencies are incomplete must not run until every dependency is complete.
- A task with higher `priority` must be preferred over lower-priority tasks only among tasks whose dependencies are already satisfied. Dependency readiness must take precedence over priority.
- Dynamic dependencies yielded from `run()` must suspend the current task, run the yielded task or tasks, and then restart the yielding task's `run()` method from the beginning. User task code must therefore be idempotent.

### Command Line

The command-line shape is:

```console
luigi [--module MODULE] [--local-scheduler] [--workers N] [--help] [--help-all] TaskFamily [task parameters]
python -m luigi [--module MODULE] [--local-scheduler] TaskFamily [task parameters]
```

- `--module MODULE` must import the module before resolving the root task family. Import failure must terminate the invocation with an error.
- The root task family is required for normal execution. Missing it must terminate with a command-line error.
- Task parameters with underscores in Python must be exposed as hyphenated command-line flags.
- Root-task parameters must appear after the root task family to be parsed as root-task flags.
- Class-qualified flags must use `--TaskFamily-param-name` and must set class-level values for that task family.
- `--help` must display common core flags and root-task flags. `--help-all` must display all registered task parameters.
- The CLI must use the configured return-code values from `[retcode]`. With default settings, unhandled internal exceptions exit with code `4`, and missing data, task failure, already running, scheduling error, and not-run categories default to code `0` unless configured otherwise. If multiple nonzero configured categories apply, the numerically greatest configured return code must be used.

### Configuration

Configuration supports `cfg` and `toml` parsers selected by `LUIGI_CONFIG_PARSER`. The default parser is `cfg`.

- The cfg parser must read, in increasing priority, `/etc/luigi/client.cfg`, `/etc/luigi/luigi.cfg`, `client.cfg`, `luigi.cfg`, and the path named by `LUIGI_CONFIG_PATH`.
- The toml parser must read, in increasing priority, `/etc/luigi/luigi.toml`, `luigi.toml`, and the path named by `LUIGI_CONFIG_PATH`.
- Values in later files must override earlier files when the same section and option appear.
- Cfg values must support environment-variable interpolation using `${ENVVAR}`. A missing environment variable reference must raise a configuration interpolation error.
- Parameter defaults from config must use a section matching the task family and an option matching the parameter name. Dashed option names must be accepted as aliases for underscored parameter names and must emit a deprecation warning.
- Config classes must use the class name as the section name and parameter names as option names.
- Core execution config must include `local_scheduler`, `scheduler_host`, `scheduler_port`, `scheduler_url`, `workers`, `module`, logging controls, process lock controls, parallel scheduling controls, and assistant mode.
- Worker config must include keep-alive, task limit, timeout, completion checking, completion caching, external task retry behavior, multiprocessing controls, and wait intervals.
- Scheduler config must include retry, disable, resource, state path, worker disconnect, pause, and message-sending controls for scheduler behavior.

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
- Moving or copying a local target to an existing destination with `raise_if_exists=True` must raise the file-exists exception documented by that operation.
- Returning a target object from `requires()` must be treated as invalid dependency structure during scheduling.
- A failure in `Task.requires()` or `Task.complete()` during scheduling must be reported as a scheduling failure.
- A failure in `Task.run()` must be reported as task failure and must call `on_failure(exception)`.
- A process lock conflict in `luigi.run` must raise `PidLockAlreadyTakenExit` internally and must map to the configured `already_running` CLI return code.
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

## Representative Workflow

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

## Non-Goals

- Contrib integrations for Hadoop, Spark, HDFS, S3, GCS, BigQuery, Redis, SQL databases, Kubernetes, Prometheus, Dropbox, SSH, FTP, and cloud services are out of scope.
- Browser visualizer pages, HTML structure, static assets, and JavaScript behavior are out of scope.
- Starting, daemonizing, supervising, or backgrounding the central scheduler process is out of scope.
- Exact log text, exact HTML text, exact stack trace formatting, and exact execution-summary line wrapping are out of scope.
- Private modules, private helper functions, private scheduler data structures, and local test helper utilities are out of scope.
- Range tools, grep/dependency helper console tools, email notification transports, database task history storage, and metrics collectors are out of scope unless they affect the core APIs listed above.

## Invocation Protocol

| Invocation | Supported | Required behavior |
| --- | --- | --- |
| `luigi --module pkg.mod TaskFamily --local-scheduler` | yes | imports `pkg.mod`, resolves `TaskFamily`, parses task flags, runs with an in-memory scheduler |
| `python -m luigi --module pkg.mod TaskFamily --local-scheduler` | yes | same task invocation behavior as `luigi` |
| `luigi TaskFamily` without `--local-scheduler` | yes | connects to the configured remote scheduler |
| `luigid --background` | out of scope here | service process behavior is not part of this core local workflow specification |

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

When several configured nonzero categories apply, the process must exit with the numerically greatest configured code.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Core workflows use local scheduler execution, local configuration files, and local targets.

## Evaluation Notes

Assessment compares user-facing imports, task objects, output files, configuration, command invocations, local scheduler runs, and `luigi.build` or `luigi.run` outcomes. Task graphs, parameters, completion state, target side effects, worker results, and public errors are checked without depending on private layouts, exact log wording, browser output, daemon management, or external services.
