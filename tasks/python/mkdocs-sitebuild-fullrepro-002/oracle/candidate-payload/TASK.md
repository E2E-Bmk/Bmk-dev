# Task

Implement the MkDocs recoverable site-publication contract in `SPEC.md`.

The repository starts without an implementation.  Preserve the documented
MkDocs public modules and call signatures used by normal local builds.  The
implementation must work offline with the dependencies declared in
`ENVIRONMENT.json`.  Do not depend on evaluator files, private fixtures,
network services, watchers, or wall-clock timing.

The supported compatibility surface includes `mkdocs.config.load_config`,
`mkdocs.commands.build.build`, the public file, page, and navigation classes
and helpers documented in `SPEC.md`, and the standard public exception types
from `mkdocs.exceptions`.  These imports must remain available whether or not
recovery mode is enabled.

Honor the documented Python object protocols and return shapes, including
configuration mapping/attribute access, `Files` mapping and collection
semantics, sized iterable table-of-contents values, navigation list identity,
and Page/File back-references.  Public calls must close resources promptly and
must not emit warnings for valid inputs, including under warnings-as-errors.
