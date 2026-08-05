# pySerial Local Public Behavior

## Product Overview

This package describes a small, local behavior surface for pySerial. It covers
serial configuration objects, URL-selected loopback streams, and synthetic port
metadata records.

## Scope

The covered behavior is deterministic and local: public `Serial` settings,
documented properties, `serial_for_url` protocol selection, `loop://` byte
transfer, buffer counts, timeout configuration, documented exception classes,
URL option validation, and `ListPortInfo` metadata projections over values
created by the runner.

## Installable Surface

The package under test is imported from the target root supplied to pytest.
The public imports used by the checks are `serial`, `serial.tools.list_ports`,
and the documented `ListPortInfo` class.

## Product State Model

A serial object has public configuration properties and an open/closed state.
An open `loop://` object exposes a local receive buffer in which written bytes
are immediately available for deterministic reads. A `ListPortInfo` value holds
device identity, description, hardware identity, and optional USB metadata.

## Error Semantics

Invalid serial configuration values raise `ValueError`. Unknown URL protocols
raise `ValueError`; invalid `loop://` options raise `SerialException`.
Operations requiring an open loop stream raise `PortNotOpenError`.

## Cross-View Invariants

Public settings returned by `get_settings()` can be applied through
`apply_settings()`. The loop stream reports the number of written bytes through
`in_waiting`, returns those bytes through public read methods, and reports an
empty buffer after draining or resetting. Metadata fields remain visible
through direct attributes, indexed compatibility access, and USB projections.

## Representative Workflows

Workflows combine configuration, URL selection, opening and closing, writing,
buffer inspection, reading, resetting, and metadata projection. Each workflow
is composed from independently checked public operations.

## Non-Goals

The package does not cover physical port enumeration, PTYs, remote serial
protocols, socket URLs, subprocesses, sleeps, timing races, host state,
platform-specific backends, private fields, source tests, exact diagnostics,
or exact upstream byte and timing matrices.

## Invocation Protocol

Run pytest against the package with `--target-root` pointing at the target
checkout. The replay uses the package's local Python API and synthetic values
created during the run.

## Environment

The reference environment is Python 3.11 on Linux without network access.
The target package is not pre-installed. Requirements are `pytest` and
`pytest-json-report`. The target checkout is supplied as the pytest target
root, and all test data is local and runner-created.

## Evaluation Notes

Results are local ARTIFACT_ONLY replay evidence. They are reproducibility
records for this task package and do not establish a trusted evaluator,
qualification, delivery, signatures, isolation, or an external result.
