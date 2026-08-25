# Invoke Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Invoke is a Python task runner and subprocess helper. It lets Python functions become command-line tasks, groups those tasks into collections and nested namespaces, loads task modules from the filesystem, merges configuration from several public sources, and executes local shell commands through explicit context objects.

The main user model is intentionally the same from the CLI and from Python: a task tree is loaded, configuration is merged for the selected task, a `Context` is handed to task code, and `Context.run` returns a `Result` describing the command that ran.

## Non-Goals

This specification does not cover vendored modules, internal helper classes, exact private data structures, exact ANSI styling, exact column widths, exact completion script bodies, shell-specific completion integration, platform-specific PTY allocation details, signal forwarding timing, subprocess race timing, low-level terminal sizing, development automation tasks used by Invoke's own repository, or tests that require a particular test helper layout.

Parser classes are public importable objects, but this specification only covers parser behavior as it appears through task declaration, `Program`, and the documented CLI.

## Representative Workflows

Create a `tasks.py` file:

```python
from invoke import Collection, task, call, Responder

@task
def clean(c):
    c.run("rm -rf build", warn=True)

@task(help={"target": "Build destination."}, optional=["target"])
def build(c, target=None):
    target = target or c.project.target
    with c.prefix("set -e"):
        c.run(f"mkdir -p {target}")

@task(pre=[call(clean)], default=True)
def release(c):
    ready = Responder(pattern=r"Continue\\? ", response="y\\n")
    c.run("printf 'Continue? '; read answer", watchers=[ready], hide=True)
    build(c)

ns = Collection("project", clean, build, release)
ns.configure({"project": {"target": "build"}})
```

Running `invoke --list` must show the task names. Running `invoke release` must run `clean` first, then `release`, and the direct Python call to `build(c)` inside `release` must use the same context object. A project, user, environment, runtime, or CLI override for `project.target` or `run.echo` must be reflected in the `Context` used by the task.

## Task Declaration and Argument Metadata

This section covers how Python callables become tasks and how their parameters are exposed as task arguments.

**Bare and configured decorator.** The `@task` decorator applied without arguments must wrap the decorated callable in a `Task` instance. The resulting `Task` must expose `name` matching the function name and must preserve the function docstring. When `@task` is applied with keyword options, `name` must override the function-derived name, `aliases` must provide alternative lookup names, and `default=True` must mark the task as the default for its containing collection via `is_default`.

**Pre-task and post-task declarations.** When `pre` or `post` lists are supplied to `@task`, those tasks must run in the declared order around the main task. Passing both a positional task argument and a `pre` keyword to `@task` must raise `TypeError` to prevent ambiguous pre-task declarations.

**Task callable contract.** Calling a `Task` with a non-`Context` first argument must raise `TypeError`. After a successful invocation, the `called` attribute must be `True`; before any invocation it must be `False`.

**Argument introspection.** `Task.get_arguments()` must return `Argument` objects for the task's declared parameters, excluding the leading context parameter. Each `Argument` must expose `name` using the Python parameter name with underscores. A positional Python parameter must set `positional` to `True`. A boolean-default parameter must set `kind` to `bool`. Parameters declared in the `optional` list must set `optional` to `True`. Parameters declared in the `iterable` list must set `kind` to `list`. Parameters declared in the `incrementable` list must set `incrementable` to `True`. A parameter with a `True` boolean default must generate an inverse CLI flag.

**Deferred invocations.** The `call` helper must create a `Call` object that stores the `task`, positional `args`, and keyword `kwargs` for later execution. `Call.clone(with_=...)` must return a new `Call` with replaced `args` and `kwargs` while preserving the task reference; the original `Call` must remain unchanged. `Call.make_context(config, parsed)` must return a `Context` whose `config` is the supplied config and whose `remainder` matches the parsed object's remainder.

**Node tagging.** `Node.tag(tags)` on a `Task` must return a new `Task` with the supplied tags added to any existing tags. The original task must remain unchanged.

## Collection and Namespace Organization

This section covers how tasks are grouped into collections, how modules are loaded, and how namespaces affect task identity.

**Collection construction.** A `Collection` may be constructed with positional `Task` arguments and an optional name. `add_task(task, name=..., aliases=...)` must register a task under the supplied name and aliases; looking up any registered name or alias through `Collection[name]` must return the same task object.

**Default task lookup.** A task declared with `default=True` must be returned by `Collection[None]` and `Collection[""]`. Attempting to register two default tasks in the same collection must raise `ValueError`.

**Subcollection nesting.** `add_collection(child)` must nest a child collection. Dotted-path lookup must traverse subcollections: `root["child.task"]` must resolve through the child. `task_names` must include dotted names, dotted aliases, and dotted paths for default tasks.

**Module loading.** `Collection.from_module(module)` must prefer an explicit `ns` or `namespace` attribute when the module defines one as a `Collection`, using only the tasks registered in that collection and ignoring top-level `Task` objects not in the namespace. When no explicit namespace attribute exists, all top-level `Task` objects in the module must form the root collection, with the collection name matching the module name.

**Configuration merging.** `Collection.configure(mapping)` must set collection-level configuration. `Collection.configuration(dotted_path)` must return merged configuration for the task at that dotted path, with parent collection values overriding child collection values for the same key.

**Namespace and auto-namespace.** `namespace(namespace_string, scope=...)` must set the namespace used by subsequently declared task classes. A class-level `task_namespace` value must take precedence over `namespace()`. `get_task_family()` must return the class name alone when no namespace is set and `<namespace>.<ClassName>` when a namespace is set.

## Configuration and Layered Merging

This section covers how Invoke loads, merges, and exposes configuration values.

**Dictionary and attribute access.** `Config` must support both dictionary-style access and attribute access. `config["project"]["target"]` and `config.project.target` must return the same value. When a key matches a real `Config` attribute such as `clone`, the attribute must return the real method, while dictionary access must return the config value.

**Cloning and overrides.** `Config.clone()` must return a deep copy whose mutations do not affect the original. `Config.load_overrides(mapping)` must apply the supplied values at the highest precedence level, overriding defaults and file values.

**Environment variable loading.** `Config.load_shell_env()` must load environment variables matching the `INVOKE_` prefix pattern and cast them to the types of existing configuration defaults. Boolean defaults must accept `"1"` as `True`. Numeric defaults must be parsed as integers.

**Precedence chain.** Configuration values must follow this precedence from highest to lowest: runtime overrides supplied via `load_overrides` or CLI flags, environment variables loaded by `load_shell_env`, runtime config files, project config files, collection-level configuration, and parameter defaults.

## Command Execution and Results

This section covers how tasks execute shell commands and inspect their output.

**Context.run basics.** `Context.run(command, **kwargs)` must execute a shell command through the configured runner class. The runner class must be configurable through `config.runners.local`. The runner must receive the context, execute the command, and return a `Result`. The run method must support `hide`, `warn`, `dry`, `in_stream`, and `watchers` options alongside normal runner arguments.

**Result attributes.** A `Result` must expose `exited` as the process exit code, `return_code` as an alias for the exit code, `ok` as `True` when `exited` is zero, `failed` as `True` when `exited` is nonzero, `command` as the executed command string, `stdout` and `stderr` as captured output strings, and `env` defaulting to an empty dictionary. A `Result` must be truthy when `ok` is `True` and falsy when `ok` is `False`. `Result.tail(stream_name, count=N)` must return the last `N` lines of the named captured output stream.

**Warn and failure behavior.** When `warn=True`, a nonzero exit must return a failed `Result` without raising. When `warn=False` (the default), a nonzero exit must raise `UnexpectedExit` whose `result` attribute exposes the exit code.

**Dry mode.** When `dry=True`, the command must not actually execute; the returned `Result` must report `ok` as `True` with empty stdout and stderr.

**Directory and prefix management.** `Context.cd(path)` must be a context manager that prepends a directory-change command before commands run inside the block. `Context.prefix(command)` must be a context manager that prepends the prefix command before the main command, so both produce output in order.

**Sudo execution.** `Context.sudo(command, password=..., user=...)` must construct a sudo-prefixed command string. When `user` is supplied, the command must include `-u <user>`. The method must set up watchers for sudo password prompts using the supplied or configured password.

**MockContext.** `MockContext(run=mapping)` must return prepared results for known command strings. A string value must become a `Result` with that string as `stdout`. A `False` value must become a `Result` with `exited=1`. An unmatched command must raise `NotImplementedError`.

**Anonymous context run.** The top-level `run(command, **kwargs)` function must create an anonymous `Context` and run the command through it, returning the `Result`.

**Stream watchers.** `StreamWatcher` is the base watcher protocol. `StreamWatcher.submit(text)` must raise `NotImplementedError` on the base class. `Responder(pattern, response)` must yield the response string when the pattern matches new stream text. A `Responder` must consume each stream segment once and must not re-match previously consumed text, but must match when new occurrences arrive. `FailingResponder(pattern, response, sentinel)` must yield the response when the pattern matches and must raise `ResponseNotAccepted` when the sentinel appears after a response has been sent. Watchers supplied through `watchers=[...]` must observe captured output streams and their matched text must remain visible in the final `Result` output.

## CLI Parsing and Task Invocation

This section covers the command-line interface grammar, task discovery, and program entry points.

**Module discovery.** With no task module configuration, the CLI must look for a Python module or package named `tasks`. The search must start from the current working directory or `tasks.search_root`/`--search-root`, walk upward toward the filesystem root, and select a module file or package that imports successfully. A configured `tasks.collection_name` or `--collection` value must replace the default module name. If no collection is found, CLI execution must exit with a user-facing collection-not-found message.

**CLI grammar.** The CLI grammar is `inv[oke] [--core-opts] task1 [--task1-opts] ... taskN [--taskN-opts] [-- remainder]`. Task arguments must accept long flags, short flags, optional equals signs, positional values for positional task parameters, globbed boolean short flags, iterable repeated flags, and incrementable repeated flags. A Python parameter named `my_option` must be presented as `--my-option` on the CLI.

**Listing tasks.** `--list` must print available tasks. `--list-format=flat` must use dotted paths for nested collections. `--list-format=nested` must show namespace nesting. `--list-format=json` must emit JSON with collection name, help, tasks (including name and aliases), and child collections. `--list-depth` must limit flat or nested traversal, and `--list-depth` with JSON list format must exit with an error.

**Task help.** `--help` without a task must print core help. `--help TASK` or `TASK --help` must print help for that task, including its docstring, task-specific options, and help text from the `help` parameter of the task decorator. Requesting help for an unknown task must raise a parse error and exit unsuccessfully.

**Execution order and deduplication.** Task execution must run pre-tasks depth-first before the requested task and post-tasks after it. By default, duplicate task calls in one session must run once. `--no-dedupe` or `tasks.dedupe=False` must allow repeated execution. Parameterized `Call` objects must dedupe by task plus args and kwargs.

**Remainder handling.** The parser remainder after a bare `--` must be stored on the task `Context.remainder` and must not be parsed as Invoke flags.

**Boolean inverse flags.** A task parameter with a `True` boolean default must generate a `--no-<name>` CLI flag that sets the value to `False`.

**Optional, iterable, and incrementable flags.** An optional argument must accept both a bare `--flag` (setting the value to `True`) and `--flag=value` (setting the named value). An iterable argument must accumulate values from repeated `--flag=value` invocations into a list. An incrementable argument must count repeated `--flag` invocations.

**Configuration through CLI.** A project config file (e.g., `invoke.yaml`) next to the loaded task collection must affect task parsing and command execution. Environment variables matching `INVOKE_` prefix patterns must override existing configuration keys. A `--config` runtime config file must override project config values. CLI run flags such as `--echo`, `--pty`, `--warn-only`, `--hide`, `--dry`, and `--command-timeout` must override corresponding lower configuration values.

**Program API.** `Program.run(argv=None, exit=True)` must use `sys.argv` when `argv` is `None`, split a string `argv` on whitespace when a string is supplied, and use a supplied list as-is. With `exit=False`, it must not call `sys.exit` for handled `Exit`, `ParseError`, or `UnexpectedExit` conditions.

## State Model

Invoke exposes one session state through three public projections:

- The namespace projection: `Collection`, `Task`, `Call`, task names, aliases, defaults, and dotted paths.
- The configuration projection: `Config` plus the `Context.config` and `Context` dictionary/attribute proxies.
- The execution projection: CLI task calls, `Context.run`, `Runner.run`, watchers, exceptions, and `Result` or `Promise` objects.

These projections must remain consistent:

- A task added to a `Collection` must appear in `Collection.task_names`, CLI task parsing, flat list output, JSON list output, and `Collection[name]` lookup.
- An alias attached through `@task(aliases=...)` or `Collection.add_task(..., aliases=...)` must return the same task object as the primary name and must be accepted by CLI task invocation.
- A default task declared on a collection must be returned by empty or `None` collection lookup and must be invoked when the collection path itself is selected.
- A dotted task path returned by `Collection.task_names` must retrieve the same task through `Collection[path]` and must receive configuration merged along that namespace path.
- A value loaded into `Config` must be readable through `Context.config`, `Context` item access, and `Context` attribute access when the key does not collide with a real `Context` attribute.
- A runtime `Context.run(..., key=value)` option must override the same option from `Config.run` for that call and must be reflected in the returned `Result` where the result stores that option.
- A hidden output stream must still be captured on `Result.stdout` or `Result.stderr`.
- A watcher supplied through `Context.run(watchers=[...])` must observe the same captured output stream text that is later available on the `Result`.

## Error Semantics

- `CollectionNotFound` represents a failed collection discovery and stores the collection name and search start.
- `ParseError` must represent invalid CLI syntax, unknown task names, invalid flags, and ambiguous task argument input.
- `Exit` must represent intentional program termination; with no message it returns exit code `0`, with a message it returns exit code `1` unless an explicit code is supplied.
- `UnexpectedExit` must be raised when a command exits nonzero and `warn` is false.
- `CommandTimedOut` must be raised when a command exceeds its timeout and must expose the partial `Result` and timeout value.
- `Failure` must wrap command failures caused by watcher errors and must expose both `result` and `reason`.
- `AuthFailure` must be raised when sudo prompt auto-response is rejected.
- `ThreadException` must aggregate exceptions raised inside background I/O threads.
- `WatcherError` is the parent for watcher-specific failures; `ResponseNotAccepted` must be raised by failing responders when the sentinel indicates the response failed.
- `SubprocessPipeError` must represent failures writing to or closing subprocess pipes.
- `UnknownFileType`, `UnpicklableConfigMember`, `AmbiguousEnvVar`, and `UncastableEnvVar` must report the configuration loading problems described in the configuration section.

## Cross-View Invariants

1. A task declared with `@task(name="x")` must be visible as `x` in a generated `Collection`, in `--list`, and in CLI invocation.
2. A task argument named `my_option` must be presented as `--my-option` on the CLI and must be delivered to Python as `my_option`.
3. A collection-level config value for a selected task must be visible through `Context.config`, `Context[...]`, and `Context` attribute access during that task.
4. A project config file next to the loaded task collection must affect task parsing and command execution in the same CLI run.
5. A CLI run flag such as `--echo`, `--pty`, `--warn-only`, `--hide`, `--dry`, or `--command-timeout` must override the corresponding lower configuration value for commands run by tasks in that session.
6. A `Context.cd` or `Context.prefix` block must affect `Context.run` and `Context.sudo` command strings consistently.
7. A nonzero command with `warn=True` must return a failed `Result`; the same command with `warn=False` must raise `UnexpectedExit`.
8. A `Responder` passed to `Context.run` must write responses through the runner's stdin path and must not remove the matched text from captured output.
9. A task built through `Collection.from_module` with an explicit `ns` must match the same `Collection` namespace and task set visible through CLI `--list --list-format=json` output.
10. Environment variable overrides loaded by `Config.load_shell_env` must be the values visible to tasks through `Context.config` and `Context` attribute access.

## Public Interface

### Import Surface

```python
from invoke import (
    task, Task, call, Call, Collection, Config, Context, MockContext,
    run, sudo, Program, FilesystemLoader, Runner, Local, Result, Promise,
    StreamWatcher, Responder, FailingResponder,
    CollectionNotFound, UnexpectedExit, Failure, CommandTimedOut, AuthFailure,
    ParseError, Exit, PlatformError, AmbiguousEnvVar, UncastableEnvVar,
    UnknownFileType, UnpicklableConfigMember, ThreadException, WatcherError,
    ResponseNotAccepted, SubprocessPipeError,
    Argument, Parser, ParserContext, ParseResult,
)
```

The parser objects are required only as public values used by `Program` and task argument generation, not as a full parser API.

The installed console scripts are `invoke` and `inv`. Both dispatch to the same `Program` instance. `python -m invoke` is supported and must run the same program.

### API Catalog

| Name | Kind | Role |
|------|------|------|
| task | decorator | Mark a callable as an Invoke task |
| Task | class | Task metadata wrapper for a callable |
| call | function | Create a Call object with pre-supplied arguments |
| Call | class | Deferred task invocation with stored arguments |
| Collection | class | Namespace for organizing tasks and subcollections |
| Config | class | Nested configuration with layered merge sources |
| Context | class | Command execution context for tasks |
| MockContext | class | Testing context with predetermined results |
| run | function | Execute a shell command via anonymous context |
| sudo | function | Execute a sudo-prefixed command |
| Program | class | CLI program entry point |
| FilesystemLoader | class | Task module loader from filesystem |
| Runner | class | Base shell command runner |
| Local | class | Local subprocess runner |
| Result | class | Command execution result with output capture |
| Promise | class | Deferred result for asynchronous commands |
| StreamWatcher | class | Base watcher protocol for command output |
| Responder | class | Pattern-matching auto-responder for prompts |
| FailingResponder | class | Responder that detects rejection sentinels |
| Argument | class | Parser argument descriptor |
| Parser | class | CLI argument parser |
| ParserContext | class | Parser context for argument resolution |
| ParseResult | class | Parsed argument result |
| CollectionNotFound | exception | Failed collection discovery |
| UnexpectedExit | exception | Nonzero command exit without warn |
| Failure | exception | Command failure with watcher error |
| CommandTimedOut | exception | Command exceeded timeout |
| AuthFailure | exception | Sudo authentication rejected |
| ParseError | exception | Invalid CLI syntax or unknown task |
| Exit | exception | Intentional program termination |
| PlatformError | exception | Platform-specific operation failure |
| AmbiguousEnvVar | exception | Ambiguous environment variable path |
| UncastableEnvVar | exception | List or tuple env var cannot be cast |
| UnknownFileType | exception | Unknown config file extension |
| UnpicklableConfigMember | exception | Module object in Python config file |
| ThreadException | exception | Aggregated background thread exceptions |
| WatcherError | exception | Base watcher failure |
| ResponseNotAccepted | exception | Responder sentinel detected rejection |
| SubprocessPipeError | exception | Subprocess pipe write or close failure |

### CLI Entry Points

Supported entry points:

- `invoke`
- `inv`
- `python -m invoke`

Exit behavior:

| Condition | Exit code |
| --- | --- |
| Successful task execution | `0` |
| `--help`, `--version`, or successful `--list` | `0` |
| Intentional `Exit` with no message | `0` |
| `Exit` with a message and no explicit code | `1` |
| Parse error or collection-not-found error | `1` |
| Keyboard interrupt | `1` |
| Command failure with `warn=False` | the command's exit code |
| Command failure with `warn=True` | `0` after returning a failed `Result` to task code |

## Appendix A: Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Command workflows run against local temporary task collections and local subprocesses.

## Appendix B: Assessment Notes

Compatibility covers Python and CLI behavior for task metadata, parsing, namespaces, module loading, configuration precedence, contexts, runners, results, watchers, sudo failures, and intentional exits. Terminal wrapping, colors, completion script bodies, PTY edge cases, timing-sensitive signals, and repository-local development tasks are not required.
