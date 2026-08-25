# Environment contract

- Python 3.12 and offline execution.
- The ordinary Loguru runtime is supplied as a declared, importable dependency
  behind the submitted package.  Its public implementation modules may be
  loaded by a wrapper and must not be fetched or vendored.
- The submitted package is loaded only from its assigned source directory.
- Caller-owned temporary directories may be used for durable relay files.
- No network service, external database, wall-clock delay or background daemon
  is available or required.
