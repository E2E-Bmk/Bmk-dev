# Local Execution Contract

- Python: CPython 3.11 on Windows.
- Working mode: offline; no network access is needed or permitted.
- The assigned source directory is placed first on `PYTHONPATH`.
- Installed dependencies may be imported, but an installed `kedro` distribution is not authority and must not be used to escape the assigned package.
- Durable operations receive writable temporary directories through their public constructors.
- Text is UTF-8 and binary target values must remain byte exact.
- Subprocesses, background services, telemetry, and external databases are outside scope.
