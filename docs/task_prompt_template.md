Implement the {LIBRARY} Python package in this directory using only {SPEC_FILE} as your specification.

Your implementation will be evaluated against a hidden test suite. Do not attempt to locate, read, or run any evaluation tests.

## Cleanroom Rules

Any violation invalidates your score:

- {SPEC_FILE} is your only permitted information source about the library's behavior
- Do not read, search for, or run any file matching `test_*.py`, `*_test.py`, or `conftest.py`
- Do not install, import, or inspect the real `{LIBRARY}` package from PyPI, GitHub, conda, local venvs, or any other source — your directory must provide the implementation
- Do not access parent directories, sibling directories, score reports, benchmark files, or any prior attempt outputs
- Do not implement {BUNDLED_DEPS} from scratch — use the real packages; the spec implies them as dependencies

## Allowed Dependencies

{ALLOWED_DEPS}

You may add other standard third-party packages if the spec implies them.

## Environment

- Python {PYTHON_VERSION}
- Your package must be pip-installable from this directory (`pip install -e .`)
- Package name must be `{LIBRARY}`

## Completion

Stop when you believe you have correctly implemented all public API behavior described in {SPEC_FILE}. Do not over-engineer. Do not add functionality not described in the spec.
