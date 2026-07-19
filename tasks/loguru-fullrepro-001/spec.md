# Loguru Specification

## Product Overview

Loguru provides a pre-instanced Python logger designed for direct application and library use. Users import `logger` from `loguru`, register one or more sinks, and emit structured log records through severity methods. The logger owns handler registration, message formatting, contextual data, exception reporting, file output management, asynchronous completion, and interoperability with the standard `logging` package.

The package must be usable with `from loguru import logger`.

The package also exposes `__version__` as a string.

## Scope

This specification covers observable behavior available through the public `loguru` import surface and the public logger object. It includes logger configuration, sink registration and removal, message emission, record contents, formatting, colors, serialization, file sinks, exception capture, context propagation, standard logging handler support, parsing helpers, and documented type-hint contracts.

The concrete implementation classes, helper modules, parser internals, handler internals, and documentation build tooling are out of scope unless their behavior is visible through the public logger object.

## Installable Surface

An installed implementation must provide a `loguru` package importable on Python. `from loguru import logger` must return a reusable logger object. `import loguru; loguru.logger` must refer to the same public logger object for normal imports in the same interpreter.

The package must define `loguru.__version__` as a non-empty string.

The public package must not require users to instantiate a logger class before logging. A default stderr handler must be available at import time unless automatic initialization is disabled by environment configuration.

## Public API

The logger object must provide these methods: `add()`, `remove()`, `complete()`, `catch()`, `opt()`, `bind()`, `contextualize()`, `patch()`, `level()`, `disable()`, `enable()`, `configure()`, `reinstall()`, `parse()`, `trace()`, `debug()`, `info()`, `success()`, `warning()`, `error()`, `critical()`, `exception()`, `log()`, `start()`, and `stop()`.

`add()` must accept `sink` and keyword-only options `level`, `format`, `filter`, `colorize`, `serialize`, `backtrace`, `diagnose`, `enqueue`, `context`, `catch`, plus sink-specific options. It must return an integer handler id.

`catch()` must accept `exception`, `level`, `reraise`, `onerror`, `exclude`, `default`, and `message`. `opt()` must accept `exception`, `record`, `lazy`, `colors`, `raw`, `capture`, `depth`, and deprecated `ansi`. `configure()` must accept `handlers`, `levels`, `extra`, `patcher`, and `activation`. `parse()` must accept `file`, `pattern`, `cast`, and `chunk`.

`logger.add()` must accept these sink categories:

- Text streams such as `sys.stderr` and `sys.stdout`.
- File path strings and path-like objects.
- File-like objects with a `write()` method.
- Callable sinks receiving a single message object.
- Coroutine functions used as asynchronous sinks.
- Standard `logging.Handler` instances.

When the corresponding environment variables are not set before import, `logger.add()` defaults must be equivalent to `level="DEBUG"`, a human-readable format containing time, level, caller name, function, line, and message fields, `filter=None`, `colorize=None`, `serialize=False`, `backtrace=True`, `diagnose=True`, `enqueue=False`, `context=None`, and `catch=True`.

`logger.start()` must behave as a deprecated alias of `logger.add()`. `logger.stop()` must behave as a deprecated alias of `logger.remove()`.

Severity methods must log at the named level implied by the method. `logger.log()` must accept a level name or a numeric severity. `logger.exception()` must attach the active exception information in the same way as `logger.opt(exception=True).error(...)`.

## Product State Model

The logger maintains process-local mutable state:

- A handler registry mapping integer handler ids to active sinks and their options.
- A level registry mapping level names to severity numbers, colors, and icons.
- A global `extra` mapping configured through `configure()`.
- Logger views created by `bind()`, `patch()`, and `opt()`.
- Context-local `extra` values installed by `contextualize()`.
- Activation rules installed by `enable()`, `disable()`, and `configure(activation=...)`.
- Queues and asynchronous tasks created for handlers using enqueueing or coroutine sinks.

Calling a logging method creates a record, merges logger state into that record, filters the record for each active handler, formats or serializes a message per handler, and writes the resulting message to each accepted sink. Removing or reconfiguring handlers affects subsequent records and must not rewrite already emitted messages.

When multiple sources provide the same `record["extra"]` key, later sources must replace earlier values in this order: default `extra` configured by `configure(extra=...)`, then context-local values from `contextualize()`, then values from `bind()`, then captured keyword arguments from the logging call.

The handler registry must use the current level registry when deciding whether a record reaches a sink. The context state must be reflected in the record state before filters, formatters, and sinks observe the record. Activation state must suppress disabled module records before any handler writes them.

## Sink Registration And Message Emission

`logger.add()` must register a handler and return an integer id unique among active handlers at the time it is returned. The handler must receive records whose level is greater than or equal to the handler threshold and whose filter accepts the record.

The `level` argument must accept a level name, a numeric severity, or a custom level previously registered through `level()`. A handler must reject records below its threshold.

The `filter` argument must support:

- `None`, meaning no extra filtering.
- A callable that receives the record and whose truth value selects the record.
- A string naming a module namespace accepted for records from that namespace.
- A dictionary mapping module namespace names, `None`, or empty string to booleans or level thresholds.

The `format` argument must support a format string or a callable receiving the record and returning a format string. Format strings must be applied with record fields and message arguments. Logging calls must use `{}` formatting with positional and keyword arguments supplied to the logging call. Ordinary formatted handler output must be terminated as one log line, so a handler format such as `{message}` writes or delivers the rendered message followed by a newline.

The message object passed to callable sinks must behave like a string and must expose a `.record` attribute containing the record dictionary used to produce the message.

If `catch=True` for a handler, exceptions raised by that sink must be caught and reported to the fallback error stream without propagating to the logging call. The fallback report must include the sink exception type and exception message, while the exact diagnostic wording and traceback layout are not part of the contract. If `catch=False`, sink exceptions must propagate to the caller.

`logger.remove(id)` must deactivate the matching handler. `logger.remove()` with no argument must remove all active handlers. Removing an unknown active id must raise `ValueError`; passing an invalid id type must raise `TypeError`.

## Formatting, Records, Colors, And Serialization

Every emitted record must include at least these keys:

`elapsed`, `exception`, `extra`, `file`, `function`, `level`, `line`, `message`, `module`, `name`, `process`, `thread`, and `time`.

The `message` field must contain the formatted user message without handler prefix/suffix formatting. The `record["level"]` field must expose level name, numeric severity, and icon attributes. Level color information must be exposed by `logger.level(name)` and by configured level metadata, not by `record["level"]`. The `file`, `process`, and `thread` fields must expose named attributes documented by the type-hint contract.

When `serialize=True`, the handler output must be a JSON text representation containing the rendered text and record information. The output must remain line-delimited for ordinary message emission.

Color markup such as `<red>...</red>` must be interpreted when color handling is enabled for the handler or per-call option. Escaped tags must remain literal. Unknown or malformed markup in a color-enabled message must raise a value error before the message is written. When `colorize=None`, path sinks, standard `logging.Handler` sinks, callable sinks, coroutine sinks, and serialized handlers must behave as non-colorized handlers. Only file-like stream sinks must use automatic color detection: color markup is converted to ANSI codes when the stream is detected as color-capable and stripped otherwise. For standard output and standard error streams, a non-empty `NO_COLOR` environment variable must disable automatic colorization; a non-empty `FORCE_COLOR` environment variable must enable automatic colorization when `NO_COLOR` is not active.

`raw=True` in `opt()` must cause the emitted message text to bypass the handler format template and must not add an implicit line terminator beyond the raw message text. `record=True` must allow `{record[...]}` placeholders in the message format arguments. `lazy=True` must call argument callables only when at least one handler accepts the record.

## Context, Patching, And Per-Call Options

`logger.bind(**kwargs)` must return a logger view whose emitted records include the provided key-value pairs in `record["extra"]`. The original logger must remain usable without those bound values.

`logger.contextualize(**kwargs)` must return an object usable as a context manager and as a function decorator. Inside the context, and during a decorated function call, emitted records must include the provided key-value pairs in `record["extra"]`; after the context exits or the decorated call returns or raises, the previous context values must be restored. Contextual data must be isolated across threads and asynchronous tasks according to Python context variable behavior.

`logger.patch(function)` must return a logger view that calls `function(record)` before records from that view are emitted. Patch functions must observe and mutate the record dictionary used by sinks.

When both `configure(patcher=...)` and `logger.patch(...)` are active, the configured patcher must run first. Patchers added through `logger.patch(...)` must then run in the order they were added to the logger view.

`logger.opt()` must return a logger view with per-call options. Calling `opt()` repeatedly must produce a view using the latest options for the following logging call rather than accumulating prior per-call flags indefinitely.

Keyword arguments supplied to a logging call and not consumed by string formatting must be available in `record["extra"]` when capture is enabled. When capture is disabled, those keyword arguments must not be added to `extra`.

## Levels, Filtering, Activation, And Configuration

When the corresponding environment variables are not set before import, built-in levels must have these numeric severities: `TRACE=5`, `DEBUG=10`, `INFO=20`, `SUCCESS=25`, `WARNING=30`, `ERROR=40`, and `CRITICAL=50`. `logger.level(name)` must return an object exposing the level name, number, color, and icon for an existing level.

`logger.level(name, no=..., color=..., icon=...)` must create a new level when the name is unknown. The display name of a custom level must preserve the caller-provided spelling exactly as registered in emitted records and returned level metadata. For an existing level, color and icon must be updatable while the numeric severity remains stable unless creating a new level. Invalid level input types must raise `TypeError`. Invalid level values, invalid severities, and invalid color markup must raise `ValueError`.

When `logger.log()` receives a numeric severity, the emitted record must use that number for threshold comparisons and `record["level"].no`. The emitted display name must be `Level <number>` for that logging call, even if the same numeric severity is used by a built-in level or a custom named level.

`logger.disable(name)` must suppress records whose module name belongs to the provided namespace. `logger.enable(name)` must re-enable records for that namespace. Passing `None` or an empty string must address the default namespace behavior documented for activation rules.

`logger.configure()` must support replacing handlers, updating levels, setting default `extra`, setting a global patcher, and applying activation rules. When `handlers` is provided, existing handlers must be removed before adding the configured handlers, and the method must return the list of new handler ids. When `handlers` is omitted or `None`, existing handlers must remain installed.

## File Sinks And Generated Files

When a path sink is registered, log messages accepted by that handler must be written to the target file using the requested file options. Parent directories must be created when needed for the target path.

File sinks must support `rotation`, `retention`, `compression`, `delay`, `watch`, `mode`, `buffering`, `encoding`, `errors`, `newline`, `closefd`, and `opener` options. Rotation must move output into a new file when the configured rotation condition is reached. Byte-size rotation strings such as `10 B` must be accepted. Retention must delete older rotated files according to the retention rule. Compression must replace rotated files with compressed files according to the selected compression format; the gzip alias `gz` must produce gzip-compressed rotated files.

When `delay=True`, the file must not be opened until the first accepted record is emitted. When `watch=True`, the handler must detect that the target file was externally replaced or removed and reopen output for subsequent records.

Removing a file handler must flush and close the underlying file resource so later file operations observe complete output.

## Async, Threads, Processes, And Completion

When `enqueue=True`, records must be transferred through a queue before sink writing. This mode must preserve log call usability across threads and multiprocessing use cases supported by the selected context.

`logger.complete()` must first wait for queued records accepted before the call to be processed. It must then return an awaitable object that waits for asynchronous sink tasks scheduled in the current event loop. Calling `complete()` in synchronous code must still perform the queue-drain step.

Coroutine sinks must schedule one task per accepted message on the configured or running event loop. A coroutine sink without an available usable loop must drop or report the task according to handler error handling and must not silently corrupt synchronous handlers.

`logger.reinstall()` must restore handler usability after child-process interpreter setup that invalidates inherited queue or stream state.

## Exceptions And Standard Logging Interop

`logger.catch()` must work as both a decorator and a context manager. It must catch exceptions matching the `exception` argument except those matching `exclude`, log a record at the requested level with the configured message, and then apply `reraise`, `default`, and `onerror` behavior. If `reraise=True`, the original exception must be raised after logging. If `default` is set for a decorated function and the exception is suppressed, that value must be returned.

Exception records must include traceback information. When backtrace and diagnose options are enabled, formatted exception output must include extended stack context and variable diagnostics. When disabled, output must remain concise.

Standard `logging.Handler` sinks registered through `add()` must receive standard `logging.LogRecord` objects carrying the emitted message, level, exception information, and extra data representable by the standard logging model.

Records emitted by standard `logging` and forwarded into Loguru by user-installed bridge handlers must preserve the level number, message, exception, and caller depth behavior exposed by the public logger options. When bridge code forwards a standard `logging.LogRecord` by calling `logger.log(record.levelno, record.getMessage())`, the resulting Loguru record must follow the numeric-severity rule and use `Level <number>` as the display name.

## Parsing Logged Files

`logger.parse(file, pattern, *, cast={}, chunk=...)` must read a text file path, a readable text file object, or a readable binary file object, apply the regular expression pattern, and yield dictionaries built from named capture groups. Text inputs must work with text patterns and yield string capture values. Binary inputs must work with bytes patterns and yield bytes capture values. If `cast` is a callable, it must receive each parsed dictionary. When the callable returns a dictionary, that returned dictionary must be yielded. When the callable returns `None`, the parser must yield the input dictionary after any in-place mutations performed by the callable. If `cast` is a mapping, each matching key must transform the corresponding captured value.

The parser must stream through the file in chunks and must produce matches spanning chunk boundaries when the pattern allows them.

## Type Hints

The project publishes type information for the public logger and associated record structures. Static type checkers must understand the `logger` object as a `Logger`-like value with the documented method signatures. The installed package must include a readable `loguru/__init__.pyi` type stub or equivalent package-local type information sufficient for static analysis.

The documented type names `Logger`, `Message`, `Record`, `Level`, `Catcher`, `Contextualizer`, `AwaitableCompleter`, `RecordFile`, `RecordLevel`, `RecordThread`, `RecordProcess`, and `RecordException` describe the public typing contract. The `RecordLevel` typing contract must include name, numeric severity, and icon fields, and must not require a color field on message record level objects. Implementations do not need to expose each type name as a runtime import from `loguru` unless they choose to do so; runtime behavior remains centered on `logger`.

## Error Semantics

| Operation | Condition | Required exception behavior |
| --- | --- | --- |
| `add()` | Sink object is not a supported sink category | Raise `TypeError` or `ValueError` before registering a handler. |
| `add()` | Invalid level name, level number, filter, formatter, color option, queue context, or file option | Raise `TypeError` or `ValueError` before registering a handler. |
| `add()` | Color-enabled format or message contains malformed markup | Raise `ValueError` before writing the malformed message. |
| `remove()` | Handler id type is invalid | Raise `TypeError`. |
| `remove()` | Handler id does not identify an active handler | Raise `ValueError`. |
| `level()` | Unknown level is queried without creation parameters | Raise `ValueError`. |
| `level()` | Level name, number, color, or icon is invalid | Raise `TypeError` or `ValueError`. |
| Logging call | Message formatting fails because placeholders and arguments do not match | Raise `ValueError` to the caller. |
| Logging call | Sink raises while handler has `catch=False` | Propagate the sink exception to the caller. |
| Logging call | Sink raises while handler has `catch=True` | Do not propagate the sink exception; report the sink failure to the fallback error stream with the exception type and message. |
| `catch()` | Suppressed exception matches `exclude` | Do not suppress it; raise the original exception. |
| `parse()` | File path is not openable or readable | Propagate the underlying file or I/O exception. |
| `parse()` | File argument is neither a path nor a readable file object | Raise `TypeError`. |
| `parse()` | Pattern is neither a string, bytes pattern, nor compiled regular expression object compatible with the input stream type | Raise `TypeError`. |

## Cross-View Invariants

1. A record accepted by multiple handlers must have the same core record values before handler-specific formatting or serialization is applied.
2. Removing a handler must prevent future writes to that sink while leaving other active handlers unaffected.
3. Handler thresholds, filters, and activation rules must all accept a record before that handler writes it.
4. Bound, contextual, captured, and configured `extra` values must be visible consistently to filters, format strings, serialized output, and callable sinks for the same record, with conflicts resolved by the documented merge order.
5. A patcher that mutates the record must affect the data observed by downstream filters, formatters, serialized output, and callable sinks for that logger view, with configured patchers running before logger-view patchers.
6. `serialize=True` must describe the same record that non-serialized callable sinks receive for the same accepted logging call.
7. Queue-based handlers must preserve the logical record data produced by the logging call even though sink writing happens later.
8. `complete()` must not return from its synchronous drain step before records accepted by queue handlers before the call have been processed.
9. Contextual values installed in one thread or asynchronous task must not leak into unrelated threads or tasks.
10. File rotation, retention, and compression must never change which records were accepted; they only change where completed file output is stored.
11. `logger.configure(handlers=[...])` must replace the handler set atomically from the caller viewpoint: subsequent records use the new handler set.
12. The type-hint record shape must match keys present in message `.record` objects passed to callable sinks.

## Representative Workflows

### Application Logging To Console And File

An application imports `logger`, removes the default stderr handler, adds a colorized console sink at `INFO`, adds a rotating file sink at `DEBUG`, binds a request id, and emits messages. Console output must contain accepted high-level messages. The file must contain both debug and high-level messages and must rotate when the configured size or time rule is reached.

### Library Quiet By Default

A library imports `logger`, calls `disable(__name__)`, and logs internally. Applications that do not enable the library namespace must not receive those records. An application that later calls `enable()` for that namespace and registers a sink must receive subsequent records.

### Exception Guard

A function decorated with `logger.catch(default=...)` raises a matching exception. The logger must emit an error record containing exception information. The decorated call must return the configured default when reraising is disabled and must raise the original exception when reraising is enabled.

### Async Sink Completion

An application registers a coroutine sink, emits messages inside an event loop, calls `logger.complete()`, awaits the returned object, and then inspects the sink side effects. All accepted coroutine sink messages scheduled before completion must have finished before the await returns.

### Parsing Generated Logs

An application writes structured text logs to a file and then calls `logger.parse()` with named groups and cast functions. The parser must yield dictionaries containing the captured and converted values in file order.

## Non-Goals

This specification does not require compatibility with private helper modules, private handler classes, concrete parser internals, documentation generation, external artifacts, exact traceback frame-walking internals, exact stderr diagnostic wording for caught sink failures beyond the required exception type and message, or exact file names chosen for rotated files beyond the documented rotation, retention, and compression side effects.

Direct construction of a concrete logger implementation class is not required. Users must interact with the pre-instanced `logger` object.

## Invocation Protocol

User code must import and exercise the package as an installed Python package with `import loguru` or `from loguru import logger`.

The package does not provide a console script entry point. Running `python -m loguru` is not a supported invocation mode; the package is a library import surface rather than a command-line application.

| Invocation | Required behavior |
| --- | --- |
| `import loguru` | Import succeeds and exposes the public module attributes. |
| `from loguru import logger` | Import succeeds and returns the pre-instanced logger object. |
| `python -m loguru` | Not supported as a public interface; no success exit-code contract is provided. |

Code that needs isolated global logger state must remove handlers it adds and restore the desired defaults. Code that writes files must choose its own writable paths. Code involving queues or asynchronous sinks must call `logger.complete()` before checking sink side effects.

## Environment

The implementation is allowed to use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Evaluation Notes

Checks focus on observable public behavior: return values, emitted sink contents, file side effects, context isolation, asynchronous completion, and exception types. Checks avoid private class names, private module paths, exact diagnostic wording, and implementation-specific representations.
