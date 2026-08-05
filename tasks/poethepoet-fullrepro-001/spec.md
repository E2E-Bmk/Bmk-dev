# Poe the Poet Public Contract

## Product Overview

Poe the Poet is a Python task runner configured from a project task file. It
discovers named tasks, parses task arguments, prepares task environments, and
executes command, Python expression, Python script, shell, and orchestration
tasks. The public behavior is the relationship between a documented
configuration and the resulting task return code, output, files, and task
ordering.

The contract is intentionally expressed through temporary projects. Each
project contains only a small task configuration and harmless local Python
helpers. Assertions inspect public results rather than package internals.

## Scope

This contract covers local, deterministic behavior documented in the task
runner guides:

- task discovery from `pyproject.toml`, `poe_tasks.toml`, `poe_tasks.yaml`, and
  `poe_tasks.json`;
- public and hidden task names, task help, and the built-in task-description
  commands;
- command tasks without a shell, including quoting, glob expansion,
  `empty_glob = "null"` removal of unmatched glob arguments, parameter
  expansion, free arguments, return codes, and output capture;
- expression tasks with imports, typed arguments, environment templates, and
  false-result assertions;
- script tasks calling a local Python module, typed arguments, return values,
  `print_result = true`, and free arguments;
- Python-interpreter shell tasks, limited to code that does not depend on a
  platform shell;
- sequence, parallel, reference, dependency, and switch composition, including
  `uses` capture of an upstream task's stdout and `uses_env` parsing of
  upstream `NAME=value` lines;
- task arguments, defaults, positional values, booleans, choices, numeric
  conversion, and repeated values;
- project and task environment values, private variables, expected and
  optional envfiles, environment precedence, working directories, and Poe
  environment variables;
- included TOML, JSON, and YAML configuration, recursive include precedence,
  include working directories, and library use through `PoeThePoet`;
- project-level `default_task_type` and `default_array_item_task_type`
  interpretation of string task definitions;
- global `--dry-run` suppression of task side effects and `--quiet`
  suppression of Poe banners while preserving task output;
- normalized stdout, JSON helper output, local files, and process return codes.

The assertions use only public imports and documented configuration keys. They
normalize line endings and avoid absolute paths, terminal color sequences,
exact diagnostic prose, and process timing.

## Public Import Surface

The public Python surface exercised here is:

- `poethepoet.__version__`;
- `poethepoet.main`;
- `poethepoet.iter_tasks`;
- `poethepoet.app.PoeThePoet`.

The command surface is `python -m poethepoet`, equivalent to the installed
`poe` entry point for the local task workflows in this contract. The tests do
not import private modules or rely on package implementation classes.

## Product State Model

A project has a root directory and a selected task configuration. By default,
Poe searches for `pyproject.toml`, then the supported `poe_tasks.*` files. A
valid project configuration contains task definitions under `tool.poe.tasks`
or the equivalent top-level structure in a standalone task file.

Each task has a name and one public task kind. A string is a command by default;
tables select `cmd`, `expr`, `script`, `shell`, `sequence`, `parallel`, `ref`,
or `switch`. Arrays can represent sequences, and nested arrays represent
parallel sections in a sequence. Task options add arguments, environment
values, envfiles, dependencies, output capture, working directories, and
failure handling. Project defaults may reinterpret string tasks and string
array items through `default_task_type` and `default_array_item_task_type`.

An invocation has global options, a task name, named task arguments, and
optional free arguments. Execution produces a return code. Execution tasks may
also produce stdout, stderr, or files. Composition tasks produce the combined
observable result of their child invocations.

Public task names retain configuration order and omit names beginning with `_`
from normal discovery and direct command-line execution. Hidden tasks may still
be reached through a documented reference or composition edge.

## Error Semantics

The following outcomes are part of the contract:

- a missing or unknown task returns a non-zero result and does not run another
  task's payload;
- a hidden task cannot be invoked directly;
- an invalid choice or malformed required argument prevents task execution;
- an expression with `assert = true` returns non-zero for a false result;
- a command failure is non-zero unless the task declares `ignore_fail = true`;
- a switch with no matching case is non-zero unless it has a default case or
  `default = "pass"`;
- a referenced failure propagates through the reference unless failure is
  explicitly ignored.

Diagnostic wording, color, terminal markup, absolute paths, and internal
exception classes are not contract values. Tests use return codes, side
effects, and stable data emitted by local helper commands.

## Cross-View Invariants

The same task configuration must yield consistent public projections:

- `iter_tasks` and the built-in list operation expose the same public task
  names and omit hidden names;
- a task's configured environment, envfile values, and argument values are
  visible to its local subprocess according to documented precedence;
- a command task's free arguments are appended unless `$POE_EXTRA_ARGS` places
  them inside the command;
- a reference forwards its declared invocation and a switch forwards free
  arguments to the selected case when the case requests them;
- a sequence preserves declared order and a nested parallel group completes all
  local subtasks before the next sequence item;
- `uses` supplies captured upstream stdout through its configured command
  variable, while `uses_env` supplies parsed upstream `NAME=value` lines to the
  consumer environment;
- an include contributes tasks without overriding a task defined by the root
  project;
- CLI execution and library execution of the same temporary project agree on
  success and the visible task banner;
- captured stdout is written to the configured project-relative file while the
  task still reports its process result.
- `--dry-run` reports success without creating a task's file side effect, and
  `--quiet` omits Poe's banner without suppressing the task's own stdout.

## Representative Workflows

A command workflow uses a local helper and free arguments:

```toml
[tool.poe.tasks.probe]
cmd = "${PYTHON} runner.py argv fixed"
```

An expression or script workflow can use typed values:

```toml
[tool.poe.tasks.inspect]
expr = "json.dumps({'total': count + 2})"
imports = ["json"]
args = [{ name = "count", type = "integer", default = 3 }]
```

```toml
[tool.poe.tasks.emit]
script = "tasksmod:emit(name, count)"
args = [
  { name = "name", default = "Ada" },
  { name = "count", type = "integer", default = 2 },
]
```

A composition workflow combines references and inline operations:

```toml
[tool.poe.tasks.release]
sequence = [
  { cmd = "${PYTHON} runner.py record prepare" },
  ["build", "verify"],
  { script = "tasksmod:record('publish')" },
]
```

Environment values can come from a local envfile and be overridden at task
level:

```toml
[tool.poe.tasks.report]
cmd = "${PYTHON} runner.py env MODE"
envfile = "local.env"
env = { MODE = "task" }
```

The temporary projects used by the tests implement only local file writes,
JSON output, environment inspection, and deterministic return codes.

## Non-Goals

This contract does not require:

- network access, network commands, HTTP clients, servers, or external
  services;
- package installation, dependency resolution, Poetry or uv virtual
  environments, or platform-specific executors;
- POSIX, Bash, Zsh, Fish, or PowerShell quoting and shell-specific behavior;
- long-running processes, sleeps, wall-clock timing, concurrency timing
  assertions, or detached child processes;
- private modules, private attributes, source test imports, internal logging,
  exact help formatting, color output, or absolute path text;
- source checkout files, cache directories, virtual environments, binary
  artifacts, or generated project copies in the final package.

## Invocation Protocol

Each case creates a fresh temporary project, writes a supported task
configuration, and adds a local `runner.py` plus a local `src/tasksmod.py`
helper. The task runner is invoked with:

```text
python -m poethepoet [global options] task [named arguments] [free arguments]
```

The subprocess environment contains only the interpreter path, the controlled
package path, `NO_COLOR`, and explicit values needed by the case. The helper
returns JSON on one line for data assertions and writes files only inside the
temporary project. A case may inspect the return code, normalized output,
emitted JSON, or project-relative files.

## Environment

The required replay environment is Python 3.11 on Linux without network access.
Reference evidence is also replayed with Python 3.10. The target package is not pre-installed;
the pinned checkout is placed on the controlled Python path for local replay.
No package installation is performed.

The declared local requirements are `pytest`, `pytest-json-report`, `pastel`,
`PyYAML`, and conditional `tomli` for Python versions below 3.11. The lane
provides a minimal local `pastel` compatibility helper so the documented
output path does not depend on an external installation. The Python path,
working directory, and task environment are controlled per temporary project;
host secrets and unrelated host variables are not used.

## Evaluation Notes

The retained cases are generated from the public task configuration model and
local execution projections. They are divided into atomic behavior checks and
multi-operation integration checks. Bookkeeping files record every physical
test nodeid exactly once.

Assertions prefer structured JSON, return codes, file contents, task ordering,
and normalized line sets. They do not compare complete output transcripts or
measure elapsed time. The local reports are reproducibility artifacts only and
must remain labeled `ARTIFACT_ONLY`; they do not establish a trusted runner,
strict isolation, signatures, qualification, or delivery status.
