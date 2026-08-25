# structlog Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

structlog must turn a logging call into a structured event dictionary, enrich or render that dictionary through configured processors, and deliver the result to a wrapped logger.  A logging call must return the wrapped logger's result when processing and delivery succeed; it must return `None` when a processor raises `DropEvent`; it must propagate any other processor or wrapped-logger exception.

## Non-Goals

This specification does not require exact console spacing, colors, `repr` output, timestamp values, traceback-frame schemas, deprecated thread-local implementation behavior, Twisted behavior beyond optional namespace availability, Rich-specific rendering, or complete standard-library formatter layouts.  It does not require private modules, private attributes, package metadata compatibility aliases, or a command-line interface.

## Representative Workflows

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

## Configuration and Logger Construction

This section covers how structlog configures its global processing defaults and how bound loggers are constructed.

**Logger construction.** `get_logger` must accept positional arguments and keyword initial values.  It must return a lazy bound logger configured from the current global defaults.  Positional arguments must be passed to the configured logger factory when the wrapped logger is first created, and keyword initial values must pre-populate the logger's local context.  Construction must be deferred until the first log call; the factory must not be invoked at `get_logger` time.  When the factory fails during deferred construction, the failure must propagate to the caller.  `getLogger` must return exactly the same behavior as `get_logger`.

**Wrapping an explicit logger.** `wrap_logger` must create a lazy bound logger around a supplied `logger`.  When `processors`, `wrapper_class`, `context_class`, or `cache_logger_on_first_use` is explicitly supplied, that value must be used instead of the corresponding global default; when an argument is `None`, the global default must apply.  When no wrapped logger was supplied and construction reaches a failing factory, the failure must propagate.

**Global configuration.** `configure` must replace each non-`None` global default and must preserve the current value for each `None` argument.  After a successful call, `is_configured` must return `True`.  A supplied processor sequence must be callable at log time; a non-callable processor must raise its own call error when a log method reaches it.  `configure_once` must perform the same configuration only when no prior configuration has occurred; when configuration already exists, it must emit `RuntimeWarning` and leave the existing settings unchanged.

**Configuration introspection.** `get_config` must return a mapping containing the current `processors`, `context_class`, `wrapper_class`, `logger_factory`, and `cache_logger_on_first_use` values.  Rebinding a key in that returned mapping must not change global configuration.  `reset_defaults` must restore built-in defaults and must make `is_configured` return `False`.

## Processors and Rendering

This section covers processor invocation, event enrichment, and rendering of event dictionaries to deliverable output.

**Processor protocol.** A processor must receive `(wrapped_logger, method_name, event_dict)`.  `DropEvent` must suppress delivery when raised by a processor, and the originating log call must return `None`.  A different processor exception must propagate unchanged.

**Log-level enrichment.** `structlog.processors.add_log_level` must add the normalized log level under the key `level`.  The value must be a lowercase string corresponding to the logging method name.

**Timestamping and stack info.** `TimeStamper`, `StackInfoRenderer`, and `format_exc_info` must remain available as processors for adding timestamps, stack frames, and formatted exception information to event dictionaries.

**JSON rendering.** `JSONRenderer` must return JSON text for an event dictionary.  When no caller-supplied JSON `default` is present and a value exposes `__structlog__`, it must serialize that method's result before falling back to `repr`.  A value rejected by the active JSON serializer must raise the serializer's error.

**Key-value rendering.** `KeyValueRenderer` must accept a `key_order` argument and must render requested keys first in the supplied order, then remaining event fields.  It must omit a requested key that is absent rather than invent a value.  A non-iterable `key_order` must raise the normal constructor type error.

## Context-Local Context

This section covers the context-variable-based execution context that attaches fields across logging calls within the same execution scope.

**Binding and retrieval.** `bind_contextvars` must bind keyword fields to the current execution context and must return tokens keyed by field name.  `get_contextvars` must return a copy of the current context-local fields; mutating the returned copy must not affect the stored context.  `clear_contextvars` must remove all structlog context-local fields from the current execution context.  `unbind_contextvars` must remove present fields and must ignore absent fields.

**Merging into events.** `merge_contextvars` must add context-local fields only for event-dictionary keys that are absent; fields already supplied by local binding or by a logging call must take precedence.  `get_merged_contextvars` must return a copy in which the logger's local bound fields override same-named context-local fields.

**Token restoration.** `reset_contextvars` must restore the tokenized prior values and must raise the underlying lookup error for an unknown token key.

**Scoped binding.** `bound_contextvars` must act as a context manager and decorator.  It must expose the temporary fields while its scope is active, and it must restore overwritten fields and remove newly introduced fields on scope exit, including when the scope exits through an exception.

## Output and Testing Utilities

This section covers output loggers that deliver events to streams, return loggers for testing, and capture utilities for inspecting emitted events.

**Text output loggers.** `PrintLogger` and `WriteLogger` must accept an optional `file` argument and must expose `msg` and the familiar logging-method aliases.  Each call must produce one newline-terminated text line and must flush the selected text stream.  `PrintLogger` must use the stream's normal printable-object behavior, while `WriteLogger` must require a value accepted by text concatenation.  `WriteLogger` must raise the underlying concatenation type error for an incompatible message type.

**Bytes output logger.** `BytesLogger` must accept an optional `file` and an optional `name` argument.  It must provide the same logging-method aliases for bytes messages and must write one trailing newline byte sequence.  It must raise the underlying concatenation type error for an incompatible message type.

**Output logger factories.** `PrintLoggerFactory`, `WriteLoggerFactory`, and `BytesLoggerFactory` must create their corresponding output logger type for configuration and must ignore positional factory arguments.  `ReturnLoggerFactory` must reuse one `ReturnLogger`; a caller that passes unsupported construction arguments must receive Python's normal argument error.

**Return logger.** `ReturnLogger` must expose `msg` and the familiar logging-method aliases.  When called with a single positional argument and no keyword arguments, it must return that argument unchanged.  When called with multiple positional arguments, keyword arguments, or both, it must return `(args, kwargs)`.

**Capture context manager.** `capture_logs` must accept an optional `processors` argument and must yield a list of captured event dictionaries while active.  It must disable configured processors, run the supplied processors before capture, add normalized `log_level`, and restore the original configured processor sequence on exit.  It is not thread-safe; concurrent mutation must not be relied upon.  A supplied processor failure must propagate from the logging call.

**Capture processor.** `LogCapture` must append its event dictionary to its `entries` attribute, add normalized `log_level`, raise `DropEvent`, and therefore prevent delivery.

**Capturing logger.** `CapturingLogger` must store every invoked method call as a `CapturedCall` value in its `calls` attribute.  Each `CapturedCall` must expose `method_name`, `args`, and `kwargs` attributes for the recorded invocation.  A captured method call must return `None`.

## Standard-Library and Development Namespaces

This section covers integration with the Python standard-library logging system and the development console renderer.

**Recreating defaults.** `structlog.stdlib.recreate_defaults` must accept a `log_level` argument that defaults to `0`.  When `log_level` is an integer, it must configure standard-library logging to `sys.stdout` at that level and a later structured log entry must be delivered through `logging`.  When `log_level` is `None`, it must not configure standard-library logging and application logging configuration must remain the caller's responsibility.  A standard-library logging configuration error must propagate from this call.

**Standard-library bound logger.** `structlog.stdlib.BoundLogger` must work as the generic bound logger while exposing the standard-library logging methods and passing standard-library logger properties through to its wrapped logger.

**Standard-library logger factory.** `structlog.stdlib.LoggerFactory` must accept an optional `ignore_frame_names` argument and must build the standard-library logger used by `configure(logger_factory=...)`.  A failure from standard-library logger construction must propagate when the factory is called.

**Level filtering.** `structlog.stdlib.filter_by_level` must return the supplied event dictionary when `logger` accepts the standard-library level for `method_name`.  It must raise `DropEvent` when that level is rejected.  An object without standard-library level-checking behavior must raise its normal attribute error.

**Processor formatter.** `structlog.stdlib.ProcessorFormatter` must format both structlog and standard-library `LogRecord` values through its configured processor chain.  `ProcessorFormatter.wrap_for_formatter` must be the final processor for structlog records sent to this formatter, and the final formatter processor must return `str` for the standard-library handler.  Its constructor must raise `TypeError` when both or neither of `processor` and `processors` is supplied.  A processor exception, including `DropEvent`, must propagate through formatting.

**Console renderer.** `structlog.dev.ConsoleRenderer` must return human-readable text for an event dictionary and must render a true `exc_info` value after the log line.  When `colors` is `False`, it must render without terminal-color support; when Rich is unavailable, its default exception formatter must use plain traceback rendering.  When `columns` is supplied, it must define output order and formatting and must raise `ValueError` unless exactly one column has `key=''` as the default formatter.  On Windows, `colors=True` requires Colorama; callers without that optional dependency must use `colors=False`, while core event construction remains usable.

## State Model

The public state model has three projections: a bound logger's local context, a context-local context managed by `structlog.contextvars`, and a delivered or captured event dictionary.  A bound logger must create an event dictionary by copying its current local context, applying logging-call keyword fields, and adding the positional event as the `event` field when an event was supplied.  A processor chain must receive each predecessor's return value; the final value must be delivered as one positional `str`, `bytes`, or `bytearray`, as `(args, kwargs)`, or as keyword arguments from a dictionary.  The call must raise `ValueError` when the final processor returns another type.

`bind(**values)` must return a logger with those values merged into its local context and must leave the source logger's local context unchanged.  `unbind(*keys)` must return a logger without those keys and must raise `KeyError` when any requested key is absent.  `try_unbind(*keys)` must return a logger while ignoring missing keys.  `new(**values)` must clear the source logger's local context before returning a logger bound with `values`; callers needing preservation must use `bind` instead.

`get_context(logger)` must return that logger's active context object.  A caller mutation of that returned object must be observable through a later `get_context` call for the same logger.  It must raise `AttributeError` when passed an object that does not expose a compatible context.

`make_filtering_bound_logger(min_level)` must return a bound-logger class that delivers calls at or above `min_level` and returns `None` without delivery for lower levels.  It must accept logging's numeric levels and the case-insensitive names `critical`, `error`, `warning`, `info`, `debug`, and `notset`; it must raise `KeyError` for an unrecognized string level.  Its `log(level, event, *args, **kwargs)` method must follow the same threshold rule, and its asynchronous methods must mirror their synchronous counterparts.

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

## Public Interface

### Import Surface

`import structlog` must provide the following public names:

```python
import structlog
from structlog import (
    BoundLogger, BoundLoggerBase, BytesLogger, BytesLoggerFactory, DropEvent,
    PrintLogger, PrintLoggerFactory, ReturnLogger, ReturnLoggerFactory,
    WriteLogger, WriteLoggerFactory,
    configure, configure_once, getLogger, get_config, get_context, get_logger,
    is_configured, make_filtering_bound_logger, reset_defaults, wrap_logger,
)
import structlog.contextvars
import structlog.dev
import structlog.processors
import structlog.stdlib
import structlog.testing
import structlog.threadlocal
import structlog.tracebacks
import structlog.types
import structlog.typing
import structlog.twisted
```

`structlog.twisted` must expose its optional integration when its dependency is installed; otherwise the top-level attribute must be `None`. An unavailable optional dependency must not prevent the remaining package surface from importing.

`getLogger` must return exactly the same behavior as `get_logger`. Public imports outside this list are not required by this specification and must raise the normal Python import or attribute error when absent.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| get_logger | function | Return a lazy bound logger from current defaults |
| wrap_logger | function | Create a bound logger around an explicit logger |
| configure | function | Set global processing defaults |
| configure_once | function | Configure only if not already configured |
| get_config | function | Return current configuration mapping |
| reset_defaults | function | Restore built-in defaults |
| is_configured | function | Check whether configure has been called |
| add_log_level | processor | Add normalized log level to event dictionary |
| TimeStamper | processor | Add timestamp to event dictionary |
| StackInfoRenderer | processor | Render stack information into event |
| format_exc_info | processor | Format exception information into event |
| JSONRenderer | processor | Render event dictionary as JSON text |
| KeyValueRenderer | processor | Render event dictionary as key-value text |
| bind_contextvars | function | Bind fields to context-local execution context |
| get_contextvars | function | Return copy of context-local fields |
| clear_contextvars | function | Remove all context-local fields |
| unbind_contextvars | function | Remove specific context-local fields |
| merge_contextvars | processor | Merge context-local fields into event dictionary |
| get_merged_contextvars | function | Return merged local and context-local fields |
| reset_contextvars | function | Restore tokenized prior context values |
| bound_contextvars | context manager | Temporarily bind and restore context-local fields |
| PrintLogger | class | Text output logger using print behavior |
| WriteLogger | class | Text output logger using write/concatenation |
| BytesLogger | class | Bytes output logger |
| ReturnLogger | class | Logger that returns arguments unchanged |
| capture_logs | context manager | Capture event dictionaries during testing |
| LogCapture | processor | Capture processor for testing |
| CapturingLogger | class | Logger that records all method calls |
| CapturedCall | class | Recorded method call with method_name, args, kwargs |
| recreate_defaults | function | Recreate defaults on standard-library logging |
| stdlib.BoundLogger | class | Bound logger with standard-library methods |
| stdlib.LoggerFactory | class | Standard-library logger factory |
| filter_by_level | processor | Filter events by standard-library level |
| ProcessorFormatter | class | Format LogRecord through processor chain |
| ConsoleRenderer | class | Human-readable console output renderer |

### CLI Entry Points

There is no console script for this package. `python -m structlog` is not supported. Programmatic use is through Python imports.


## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment.

## Appendix B: Assessment Notes

Assessment observes only the public behavior described in this specification: importable names, logger construction and binding, processor pipelines, context-local state, capture utilities, output loggers, documented errors, and cross-view invariants. Each checked behavior is observed through public imports and returned or captured values. Private modules, private attributes, exact `repr` output, exact exception wording, and internal pipeline structure are not examined. Console rendering is checked for documented content behavior, not exact spacing or colors.
