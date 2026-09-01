# Candidate environment contract

Evaluation uses CPython 3.12 with the standard library and installed
`python-dateutil`, `regex`, `pytz`, `tzlocal`, and `tzdata` distributions.  The
submitted source directory is the first eligible `dateparser` provider.

Network access, package installation, subprocess delegation, symlinks, and
imports from another Dateparser tree are prohibited.  Each behavioral root runs
in a fresh interpreter with bytecode writes disabled.  Durable stores may write
only beneath caller-supplied locations.

The candidate tree is hashed before and after scoring.  Inventory, dependency,
containment, process, timeout, malformed-receipt, setup, teardown, and tree
integrity failures are invalid evidence rather than semantic failures.
