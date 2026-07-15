
# structlog Specification

## Product Overview

structlog must turn a logging call into a structured event dictionary, enrich or render that dictionary through configured processors, and deliver the result to a wrapped logger.  A logging call must return the wrapped logger's result when processing and delivery succeed; it must return `None` when a processor raises `DropEvent`; it must propagate any other processor or wrapped-logger exception.

## Scope

This specification covers public logger construction, immutable context binding, processor pipelines, global configuration, context-local state, the documented testing projection, built-in text and bytes output loggers, and basic JSON or key-value rendering.  It covers the public namespace availability of `dev`, `stdlib`, `threadlocal`, `tracebacks`, `twisted`, `types`, and `typing`.

## Installable Surface

`import structlog` must provide `BoundLogger`, `BoundLoggerBase`, `BytesLogger`, `BytesLoggerFactory`, `DropEvent`, `PrintLogger`, `PrintLoggerFactory`, `ReturnLogger`, `ReturnLoggerFactory`, `WriteLogger`, `WriteLoggerFactory`, `configure`, `configure_once`, `getLogger`, `get_config`, `get_context`, `get_logger`, `is_configured`, `make_filtering_bound_logger`, `reset_defaults`, and `wrap_logger`.

`structlog.contextvars`, `structlog.dev`, `structlog.processors`, `structlog.stdlib`, `structlog.testing`, `structlog.threadlocal`, `structlog.tracebacks`, `structlog.types`, and `structlog.typing` must be importable public namespaces.  `structlog.twisted` must expose its optional integration when its dependency is installed; otherwise the top-level attribute must be `None`.  An unavailable optional dependency must not prevent the remaining package surface from importing.

`getLogger` must return exactly the same behavior as `get_logger`.  Public imports outside this list are not required by this specification and must raise the normal Python import or attribute error when absent.

## Public API

### Configuration and Logger Construction

`get_logger(*args, **initial_values)` must return a lazy bound logger configured from the current global defaults.  It must pass `*args` to the configured logger factory when it first creates the wrapped logger, and it must pre-populate the logger context with `initial_values`.  It must propagate a logger-factory failure when construction reaches that factory.

`wrap_logger(logger, processors=None, wrapper_class=None, context_class=None, cache_logger_on_first_use=None, logger_factory_args=None, **initial_values)` must create a lazy bound logger around `logger`.  It must use an explicitly supplied processors, wrapper class, context class, or caching choice instead of the corresponding global default; it must use the global default for each argument that is `None`.  It must propagate a factory failure when no wrapped logger was supplied and construction reaches that factory.

`configure(processors=None, wrapper_class=None, context_class=None, logger_factory=None, cache_logger_on_first_use=None)` must replace each non-`None` global default and must preserve the current value for each `None` argument.  It must set `is_configured()` to `True` after a call.  A supplied processor sequence must be callable at log time; a non-callable processor must raise its own call error when a log method reaches it.

`configure_once` must perform the same configuration only when no configuration has yet occurred.  It must emit `RuntimeWarning` and leave the existing settings unchanged when configuration already occurred.

`get_config()` must return a mapping containing the current `processors`, `context_class`, `wrapper_class`, `logger_factory`, and `cache_logger_on_first_use` values.  Rebinding a key in that returned mapping must not change global configuration.  `reset_defaults()` must restore built-in defaults and must make `is_configured()` return `False`.

### Bound Loggers and Product State Model

The public state model has three projections: a bound logger's local context, a context-local context managed by `structlog.contextvars`, and a delivered or captured event dictionary.  A bound logger must create an event dictionary by copying its current local context, applying logging-call keyword fields, and adding the positional event as the `event` field when an event was supplied.  A processor chain must receive each predecessor's return value; the final value must be delivered as one positional `str`, `bytes`, or `bytearray`, as `(args, kwargs)`, or as keyword arguments from a dictionary.  The call must raise `ValueError` when the final processor returns another type.

`bind(**values)` must return a logger with those values merged into its local context and must leave the source logger's local context unchanged.  `unbind(*keys)` must return a logger without those keys and must raise `KeyError` when any requested key is absent.  `try_unbind(*keys)` must return a logger while ignoring missing keys.  `new(**values)` must clear the source logger's local context before returning a logger bound with `values`; callers needing preservation must use `bind` instead.

`get_context(logger)` must return that logger's active context object.  A caller mutation of that returned object must be observable through a later `get_context` call for the same logger.  It must raise `AttributeError` when passed an object that does not expose a compatible context.

`make_filtering_bound_logger(min_level)` must return a bound-logger class that delivers calls at or above `min_level` and returns `None` without delivery for lower levels.  It must accept logging's numeric levels and the case-insensitive names `critical`, `error`, `warning`, `info`, `debug`, and `notset`; it must raise `KeyError` for an unrecognized string level.  Its `log(level, event, *args, **kwargs)` method must follow the same threshold rule, and its asynchronous methods must mirror their synchronous counterparts.

### Processors and Rendering

A processor must receive `(wrapped_logger, method_name, event_dict)`.  `DropEvent` must suppress delivery when raised by a processor, and the originating log call must return `None`.  A different processor exception must propagate unchanged.

`structlog.processors.add_log_level` must add the normalized log level under `level`.  `TimeStamper`, `StackInfoRenderer`, and `format_exc_info` must remain available as processors.  `JSONRenderer(**dumps_kw)` must return JSON text for an event dictionary; when no caller-supplied JSON `default` is present and a value exposes `__structlog__`, it must serialize that method's result before falling back to `repr`.  A value rejected by the active JSON serializer must raise the serializer's error.

`KeyValueRenderer(key_order=...)` must render requested keys first in the supplied order and then render remaining event fields.  It must omit a requested key that is absent rather than invent a value.  A non-iterable key order must raise the normal constructor type error.

### Context-Local Context

`bind_contextvars(**values)` must bind fields to the current execution context and return tokens keyed by field name.  `get_contextvars()` must return a copy of the current context-local fields.  `clear_contextvars()` must remove all structlog context-local fields from the current execution context.  `unbind_contextvars(*keys)` must remove present fields and must ignore absent fields.

`merge_contextvars(logger, method_name, event_dict)` must add context-local fields only for event-dictionary keys that are absent; fields already supplied by local binding or by a logging call must take precedence.  `get_merged_contextvars(logger)` must return a copy in which the logger's local fields override same-named context-local fields.  `reset_contextvars(**tokens)` must restore the tokenized prior values and must raise the underlying lookup error for an unknown token key.

`bound_contextvars(**values)` must act as a context manager and decorator.  It must expose the temporary fields while its scope is active, and it must restore overwritten fields and remove newly introduced fields on scope exit, including when the scope exits through an exception.

### Output and Testing Utilities

`PrintLogger(file=None)` and `WriteLogger(file=None)` must expose `msg` and the familiar logging-method aliases.  Each call must produce one newline-terminated text line and must flush the selected text stream; `PrintLogger` must use the stream's normal printable-object behavior, while `WriteLogger` must require a value accepted by text concatenation.  `BytesLogger(file=None, *, name=None)` must provide the same aliases for bytes messages and must write one trailing newline byte sequence.  `WriteLogger` and `BytesLogger` must raise the underlying concatenation type error for an incompatible message type.

The corresponding factories must create their output logger type for configuration and must ignore positional factory arguments.  `ReturnLogger` must return a single positional argument unchanged when no keywords are supplied, and it must otherwise return `(args, kwargs)`.  `ReturnLoggerFactory` must reuse one `ReturnLogger`; a caller that passes unsupported construction arguments must receive Python's normal argument error.

`structlog.testing.capture_logs(processors=())` must yield a list of captured event dictionaries while active.  It must disable configured processors, run the supplied processors before capture, add normalized `log_level`, and restore the original configured processor sequence on exit.  It is not thread-safe; concurrent mutation must not be relied upon.  A supplied processor failure must propagate from the logging call.

`LogCapture` must append its event dictionary to `entries`, add normalized `log_level`, raise `DropEvent`, and therefore prevent delivery.  `CapturingLogger` must store every invoked method name, positional arguments, and keyword arguments as `CapturedCall` values; a captured method call must return `None`.

### Standard-Library and Development Namespaces

`structlog.stdlib.recreate_defaults(*, log_level=0)` must recreate structlog's defaults on top of standard-library logging.  When `log_level` is an integer, it must configure standard-library logging to `sys.stdout` at that level and a later structured log entry must be delivered through `logging`; when `log_level=None`, it must not configure standard-library logging and application logging configuration must remain the caller's responsibility.  A standard-library logging configuration error must propagate from this call.

`structlog.stdlib.BoundLogger` must work as the generic bound logger while exposing the standard-library logging methods and passing standard-library logger properties through to its wrapped logger.  `structlog.stdlib.LoggerFactory(ignore_frame_names=None)` must build the standard-library logger used by `configure(logger_factory=...)`; a failure from standard-library logger construction must propagate when the factory is called.

`structlog.stdlib.filter_by_level(logger, method_name, event_dict)` must return the supplied event dictionary when `logger` accepts the standard-library level for `method_name`.  It must raise `DropEvent` when that level is rejected, and an object without standard-library level-checking behavior must raise its normal attribute error.

`structlog.stdlib.ProcessorFormatter` must format both structlog and standard-library `LogRecord` values through its configured processor chain.  `ProcessorFormatter.wrap_for_formatter` must be the final processor for structlog records sent to this formatter, and the final formatter processor must return `str` for the standard-library handler.  Its constructor must raise `TypeError` when both or neither of `processor` and `processors` is supplied.  A processor exception, including `DropEvent`, must propagate through formatting.

`structlog.dev.ConsoleRenderer(...)` must return human-readable text for an event dictionary and must render a true `exc_info` value after the log line.  When `colors=False`, it must render without terminal-color support; when Rich is unavailable, its default exception formatter must use plain traceback rendering.  When `columns` is supplied, it must define output order and formatting and must raise `ValueError` unless exactly one column has `key=''` as the default formatter.  On Windows, `colors=True` requires Colorama; callers without that optional dependency must use `colors=False`, while core event construction remains usable.

## Error Semantics

`DropEvent` is a `BaseException` used only to stop a logging event from reaching the wrapped logger; the log invocation must return `None` when it is raised in processing.  A missing bound-context key must raise `KeyError` only for `unbind`; `try_unbind` and `unbind_contextvars` must return normally for missing keys.  An invalid final processor result must raise `ValueError`.  Invalid level names must raise `KeyError`.  Other invalid arguments must raise the normal Python error produced by the selected callable, stream, serializer, or logger.

## Cross-View Invariants

1. A value written with `logger.bind` must be returned by `get_context` for the returned logger and must appear in its emitted event unless a later logging-call keyword supplies the same key.
2. A logging-call keyword must override a same-named local bound-context value in the emitted event.
3. `merge_contextvars` must preserve a same-named event value and must add only context-local keys absent from that event.
4. `get_merged_contextvars(logger)` must return the local logger value for every key that exists in both local and context-local context.
5. A `capture_logs` entry must contain the event assembled from the active logger state and must contain normalized `log_level`.
6. `reset_defaults` must make future lazily assembled loggers use built-in defaults, while a `wrap_logger` explicit override must remain the choice for that wrapped proxy.
7. A processor that raises `DropEvent` must prevent both output-log delivery and capture after that processor, and the originating logging call must return `None`.

## Representative Workflow

```python
import logging

import structlog
from structlog import contextvars
from structlog.testing import capture_logs

structlog.reset_defaults()
structlog.configure(
    processors=[contextvars.merge_contextvars, structlog.processors.JSONRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

contextvars.clear_contextvars()
contextvars.bind_contextvars(request_id="r-1")
logger = structlog.get_logger(service="billing")

with capture_logs(processors=[contextvars.merge_contextvars]) as events:
    logger.info("invoice-created", invoice_id=7)

assert events[0]["service"] == "billing"
assert events[0]["request_id"] == "r-1"
assert events[0]["event"] == "invoice-created"
assert events[0]["log_level"] == "info"
```

The context-local field must disappear from later merged events after `clear_contextvars()`.  Calling `logger.debug(...)` with the configured `INFO` threshold must return `None` and must not add an event.

## Non-Goals

This specification does not require exact console spacing, colors, `repr` output, timestamp values, traceback-frame schemas, deprecated thread-local implementation behavior, Twisted behavior beyond optional namespace availability, Rich-specific rendering, or complete standard-library formatter layouts.  It does not require private modules, private attributes, package metadata compatibility aliases, or a command-line interface.

## Evaluation Notes

Evaluation exercises public imports, logger construction, local and context-local state, event assembly, verified precedence rules, processor delivery and failure behavior, global configuration, filtering, capture utilities, and output type boundaries.  It evaluates observable results through public APIs and accepts implementations that preserve this contract without matching internal class layout, private state, or presentation-only rendering details.
