# Loguru Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Loguru is a Python logging library centered on a pre-instanced `logger` object. Applications and libraries import `logger`, register one or more sinks, and emit structured log records through severity methods. The logger owns handler registration, message formatting, contextual data, exception reporting, file output management, asynchronous completion, and interoperability with the standard `logging` package.

The package must be usable with `from loguru import logger`. The module also exposes `__version__` as a non-empty string. Users must not need to instantiate a logger class before logging; a default stderr handler must be available at import time unless automatic initialization is disabled by environment configuration.

## Non-Goals

- This specification does not require private helper modules, private handler classes, parser internals, or documentation build tooling.
- This specification does not require exact traceback frame-walking internals, exact stderr diagnostic wording for caught sink failures beyond the required exception type and message, or exact file names chosen for rotated files beyond the documented rotation, retention, and compression side effects.
- This specification does not require direct construction of a concrete logger implementation class.
- This specification does not require a console script entry point or `python -m loguru` invocation mode.
- This specification does not require exact rich or text representation strings, exact log message wording, or private attribute layout.

## Representative Workflows

### Application Logging To Console And File

```python
import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="console:{level.name}:{message}")
logger.add("workflow.log", level="DEBUG", format="file:{level.name}:{extra[request]}:{message}")
request_logger = logger.bind(request="r42")
request_logger.debug("debug detail")
request_logger.info("user visible")
```

Console output must contain accepted high-level messages. The file must contain both debug and high-level messages with bound context visible in formatted output.

### Library Quiet By Default

```python
from loguru import logger

logger.disable(__name__)
logger.debug("internal detail")
logger.enable(__name__)
logger.add(lambda m: None, format="{message}")
logger.debug("now visible")
```

Records from a disabled module namespace must be suppressed until that namespace is enabled and a sink accepts them.

### Exception Guard

```python
from loguru import logger

@logger.catch(default="fallback")
def fail():
    raise ValueError("bad")

result = fail()
```

The logger must emit an error record containing exception information. The decorated call must return the configured default when reraising is disabled and must raise the original exception when reraising is enabled.

### Async Sink Completion

```python
import asyncio
from loguru import logger

async def sink(message):
    await asyncio.sleep(0)

async def main():
    logger.add(sink, format="{message}")
    logger.info("async")
    await logger.complete()

asyncio.run(main())
```

All accepted coroutine sink messages scheduled before completion must have finished before the await returns.

## Sink Registration And Message Emission

`logger.add()` must register a handler and return an integer id unique among active handlers at the time it is returned. The handler must receive records whose level is greater than or equal to the handler threshold and whose filter accepts the record.

`add()` must accept `sink` and keyword-only options `level`, `format`, `filter`, `colorize`, `serialize`, `backtrace`, `diagnose`, `enqueue`, `context`, and `catch`, plus sink-specific options. Supported sink categories include text streams, file path strings and path-like objects, file-like objects with a `write()` method, callable sinks, coroutine functions, and standard `logging.Handler` instances.

When the corresponding environment variables are not set before import, `logger.add()` defaults must be equivalent to `level="DEBUG"`, a human-readable format containing time, level, caller name, function, line, and message fields, `filter=None`, `colorize=None`, `serialize=False`, `backtrace=True`, `diagnose=True`, `enqueue=False`, `context=None`, and `catch=True`.

The `level` argument must accept a level name, a numeric severity, or a custom level previously registered through `level()`. A handler must reject records below its threshold.

The `filter` argument must support `None`, a callable whose truth value selects the record, a string naming a module namespace, or a dictionary mapping module namespace names, `None`, or empty string to booleans or level thresholds.

The `format` argument must support a format string or a callable receiving the record and returning a format string. Format strings must be applied with record fields and message arguments. Logging calls must use `{}` formatting with positional and keyword arguments supplied to the logging call. Ordinary formatted handler output must be terminated as one log line.

The message object passed to callable sinks must behave like a string and must expose a `.record` attribute containing the record dictionary used to produce the message.

If `catch=True` for a handler, exceptions raised by that sink must be caught and reported to the fallback error stream without propagating to the logging call. The fallback report must include the sink exception type and exception message. If `catch=False`, sink exceptions must propagate to the caller.

`logger.remove(id)` must deactivate the matching handler. `logger.remove()` with no argument must remove all active handlers. Removing an unknown active id must raise `ValueError`; passing an invalid id type must raise `TypeError`.

`logger.start()` must behave as a deprecated alias of `logger.add()`. `logger.stop()` must behave as a deprecated alias of `logger.remove()`.

Severity methods must log at the named level implied by the method. `logger.log()` must accept a level name or a numeric severity. `logger.exception()` must attach the active exception information in the same way as `logger.opt(exception=True).error(...)`.

## Formatting, Records, Colors, And Serialization

Every emitted record must include at least these keys: `elapsed`, `exception`, `extra`, `file`, `function`, `level`, `line`, `message`, `module`, `name`, `process`, `thread`, and `time`.

The `message` field must contain the formatted user message without handler prefix or suffix formatting. The `record["level"]` field must expose level name, numeric severity, and icon attributes. Level color information must be exposed by `logger.level(name)` and by configured level metadata, not by `record["level"]`. The `file`, `process`, and `thread` fields must expose named attributes documented by the type-hint contract.

When `serialize=True`, the handler output must be a JSON text representation containing the rendered text and record information. The output must remain line-delimited for ordinary message emission.

Color markup such as `<red>...</red>` must be interpreted when color handling is enabled for the handler or per-call option. Escaped tags must remain literal. Unknown or malformed markup in a color-enabled message must raise a value error before the message is written. When `colorize=None`, path sinks, standard `logging.Handler` sinks, callable sinks, coroutine sinks, and serialized handlers must behave as non-colorized handlers. Only file-like stream sinks must use automatic color detection: color markup is converted to ANSI codes when the stream is detected as color-capable (for example, when the stream reports `isatty()` as true) and stripped otherwise.

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

## Exceptions And Standard Logging Interop

`logger.catch()` must work as both a decorator and a context manager. It must catch exceptions matching the `exception` argument except those matching `exclude`, log a record at the requested level with the configured message, and then apply `reraise`, `default`, and `onerror` behavior. If `reraise=True`, the original exception must be raised after logging. If `default` is set for a decorated function and the exception is suppressed, that value must be returned.

Exception records must include traceback information. When backtrace and diagnose options are enabled, formatted exception output must include extended stack context and variable diagnostics. When disabled, output must remain concise.

Standard `logging.Handler` sinks registered through `add()` must receive standard `logging.LogRecord` objects carrying the emitted message, level, exception information, and extra data representable by the standard logging model.

Records emitted by standard `logging` and forwarded into Loguru by user-installed bridge handlers must preserve the level number, message, exception, and caller depth behavior exposed by the public logger options. When bridge code forwards a standard `logging.LogRecord` by calling `logger.log(record.levelno, record.getMessage())`, the resulting Loguru record must follow the numeric-severity rule and use `Level <number>` as the display name.

## Parsing Logged Files

`logger.parse(file, pattern, *, cast={}, chunk=...)` must read a text file path, a readable text file object, or a readable binary file object, apply the regular expression pattern, and yield dictionaries built from named capture groups. Text inputs must work with text patterns and yield string capture values. Binary inputs must work with bytes patterns and yield bytes capture values. If `cast` is a callable, it must receive each parsed dictionary. When the callable returns a dictionary, that returned dictionary must be yielded. When the callable returns `None`, the parser must yield the input dictionary after any in-place mutations performed by the callable. If `cast` is a mapping, each matching key must transform the corresponding captured value.

The parser must stream through the file in chunks and must produce matches spanning chunk boundaries when the pattern allows them.

## State Model

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

The public projections of this state are:

- Sink output delivered to registered handlers.
- Record dictionaries exposed through callable sink message objects.
- Serialized JSON output when `serialize=True`.
- File contents written by path sinks, including rotated and compressed artifacts.
- Standard `logging.LogRecord` objects delivered to registered standard handlers.
- Parsed dictionaries yielded by `logger.parse()`.
- Level metadata returned by `logger.level()`.

## Error Semantics

| Condition | Required result |
| --- | --- |
| `add()` sink object is not a supported sink category | Raise `TypeError` or `ValueError` before registering a handler |
| `add()` invalid level name, level number, filter, formatter, color option, queue context, or file option | Raise `TypeError` or `ValueError` before registering a handler |
| `add()` color-enabled format or message contains malformed markup | Raise `ValueError` before writing the malformed message |
| `remove()` handler id type is invalid | Raise `TypeError` |
| `remove()` handler id does not identify an active handler | Raise `ValueError` |
| `level()` unknown level is queried without creation parameters | Raise `ValueError` |
| `level()` level name, number, color, or icon is invalid | Raise `TypeError` or `ValueError` |
| Logging call message formatting fails because placeholders and arguments do not match | Raise `IndexError` to the caller |
| Logging call sink raises while handler has `catch=False` | Propagate the sink exception to the caller |
| Logging call sink raises while handler has `catch=True` | Do not propagate; report sink failure to fallback error stream with exception type and message |
| `catch()` suppressed exception matches `exclude` | Do not suppress it; raise the original exception |
| `parse()` file path is not openable or readable | Propagate the underlying file or I/O exception |
| `parse()` file argument is neither a path nor a readable file object | Raise `TypeError` |
| `parse()` pattern is neither a string, bytes pattern, nor compiled regular expression object compatible with the input stream type | Raise `TypeError` |

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

## Public Interface

### Import Surface

The package is installed as `loguru`.

```python
import loguru
from loguru import logger
```

Advanced users may import documented type names from the package stub when available. Runtime behavior remains centered on `logger`.

### API Catalog

| Name | Kind | Role |
| --- | --- | --- |
| logger | object | Pre-instanced public logger |
| __version__ | constant | Package version string |
| add | method | Register a sink handler and return its id |
| remove | method | Deactivate one or all handlers |
| complete | method | Drain queued records and return an awaitable completer |
| catch | method | Decorator or context manager for exception logging |
| opt | method | Return a logger view with per-call options |
| bind | method | Return a logger view with bound extra values |
| contextualize | method | Context manager or decorator for context-local extra |
| patch | method | Return a logger view with a record patcher |
| level | method | Query or register a log level |
| disable | method | Suppress records from a module namespace |
| enable | method | Re-enable records from a module namespace |
| configure | method | Replace handlers, levels, extra, patcher, or activation |
| parse | method | Parse log files with regular expressions |
| trace | method | Emit a TRACE record |
| debug | method | Emit a DEBUG record |
| info | method | Emit an INFO record |
| success | method | Emit a SUCCESS record |
| warning | method | Emit a WARNING record |
| error | method | Emit an ERROR record |
| critical | method | Emit a CRITICAL record |
| exception | method | Emit an ERROR record with active exception info |
| log | method | Emit a record at a named or numeric level |
| start | method | Deprecated alias of add |
| stop | method | Deprecated alias of remove |

Documented type names include `Logger`, `Message`, `Record`, `Level`, `Catcher`, `Contextualizer`, `AwaitableCompleter`, `RecordFile`, `RecordLevel`, `RecordThread`, `RecordProcess`, and `RecordException`. The installed package must include readable package-local type information such as `loguru/__init__.pyi`.

## Appendix A: Environment

The working environment runs Python 3.11 on Linux without network access. The following third-party packages are preinstalled and importable: `loguru`, `pytest`.

The assessment environment provides the same interpreter and package set.

The project must declare its packaging metadata in a standard `pyproject.toml` (or `setup.py`) at the project root so the package can be installed with pip.

## Appendix B: Assessment Notes

Implementations are exercised through public Python APIs. The checks cover handler registration and removal, message emission, record contents, formatting, colors, serialization, context propagation, patching, level management, activation rules, configuration, file sinks, rotation and compression, asynchronous completion, exception capture, standard logging interoperability, and log parsing. Tests use temporary files and in-memory sinks instead of live network services. The focus is on observable behavior from the public contract above, not private data structures or exact textual representations.
