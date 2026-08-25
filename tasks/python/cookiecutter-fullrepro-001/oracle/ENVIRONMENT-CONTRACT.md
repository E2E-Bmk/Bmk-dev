# Environment contract

The submission is evaluated as a source tree on CPython 3.12.  It must contain
an importable `cookiecutter` package and may use the Python standard library
plus Jinja2, Click, PyYAML, binaryornot, python-slugify, arrow, and rich.

Evaluation is offline.  Network access, an installed Cookiecutter package, a
reference checkout, evaluator files, and prior candidate attempts are not
available to the implementation.  Local templates and all generated data are
created inside isolated temporary directories.

Hooks and release owners run as local child processes. The generator supplies
the resolved public context as JSON in `COOKIECUTTER_CONTEXT`. All catalogs,
registries, ledgers, outboxes, replay files, and coordination roots live under
evaluator-owned temporary directories. Their paths, identifiers, digests,
locks, and private JSON layouts are not stable API beyond the documented public
records and semantic bindings.

Publication uses only local evaluator-owned directories. The public release
classes are ordinary Python APIs and must survive reopening in fresh processes.
No database server, daemon, broker, clock service, or external service is
available. Process liveness and atomic local filesystem operations may be used.

The evaluator uses deterministic process exits and durable state for ownership,
concurrency, interruption, and compensation cases. It does not depend on
network services or probabilistic wall-clock races. Each scored root runs in a
fresh interpreter with a 45-second hard limit; timeouts and harness failures
are invalid evidence.
