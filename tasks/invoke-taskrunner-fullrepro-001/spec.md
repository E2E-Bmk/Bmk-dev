# Invoke Specification

## Product Overview

Invoke is a Python task runner and subprocess helper. It lets Python functions become command-line tasks, groups those tasks into collections and nested namespaces, loads task modules from the filesystem, merges configuration from several public sources, and executes local shell commands through explicit context objects.

The main user model is intentionally the same from the CLI and from Python: a task tree is loaded, configuration is merged for the selected task, a `Context` is handed to task code, and `Context.run` returns a `Result` describing the command that ran.

## Scope

This specification covers:

- Declaring tasks with `@task`, `Task`, `call`, and `Call`.
- Building and querying `Collection` objects, including aliases, default tasks, nested collections, module loading, and collection configuration.
- Loading task modules named `tasks` by default, or another configured module name, from the current directory upward.
- CLI execution through `invoke`, `inv`, and `python -m invoke` for listing tasks, printing core or per-task help, and running tasks.
- Configuration defaults, files, environment variables, runtime files, CLI overrides, and runtime modifications.
- `Context.run`, `invoke.run`, `Runner`, `Local`, `Result`, `Promise`, command output capture, warning/error behavior, dry runs, async/disowned runs, and watcher-driven responses.
- `StreamWatcher`, `Responder`, `FailingResponder`, sudo prompt auto-response, and the public exception classes used by these workflows.

## Installable Surface

The package exports the following public names for this scope from `invoke`: `task`, `Task`, `call`, `Call`, `Collection`, `Config`, `Context`, `MockContext`, `run`, `sudo`, `Program`, `FilesystemLoader`, `Runner`, `Local`, `Result`, `Promise`, `StreamWatcher`, `Responder`, `FailingResponder`, `CollectionNotFound`, `UnexpectedExit`, `Failure`, `CommandTimedOut`, `AuthFailure`, `ParseError`, `Exit`, `PlatformError`, `AmbiguousEnvVar`, `UncastableEnvVar`, `UnknownFileType`, `UnpicklableConfigMember`, `ThreadException`, `WatcherError`, `ResponseNotAccepted`, and `SubprocessPipeError`.

The package also exports parser objects such as `Argument`, `Parser`, `ParserContext`, and `ParseResult`; this specification requires them only as public values used by `Program` and task argument generation, not as a full parser API.

The installed console scripts are `invoke` and `inv`. Both dispatch to the same `Program` instance. `python -m invoke` is supported and must run the same program.

## Product State Model

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

## Public API

### Tasks

`task(*args, **kwargs)` marks a callable as an Invoke task. Used bare as `@task`, it must return a `Task` wrapping the decorated callable. Used with options as `@task(...)`, it must return a decorator. Positional arguments to `@task` must be interpreted as pre-tasks. Supplying both positional pre-tasks and the `pre=` keyword must raise `TypeError`.

`Task(body, name=None, aliases=(), positional=None, optional=(), default=False, auto_shortflags=True, help=None, pre=None, post=None, autoprint=False, iterable=None, incrementable=None)` stores task metadata and presents the wrapped callable's name, docstring, and module. `Task.name` returns the explicit task name when one was supplied, otherwise the wrapped callable name. Calling a `Task` must require the first positional argument to be a `Context`; otherwise it must raise `TypeError`. After a successful call, `Task.called` must return `True`.

Task argument generation must drop the first context parameter. Parameters without defaults become positional by default. Underscores in argument names must become dashes for CLI flags. Boolean defaults must create value-less flags, and `True` defaults must be exposed as inverse `--no-name` flags. Arguments declared in `optional` must accept either a value or bare flag. Arguments declared in `iterable` must accumulate repeated values into lists. Arguments declared in `incrementable` must increase an integer count each time they appear. Unknown keys in the `help` mapping must raise `ValueError` unless `ignore_unknown_help` is enabled for argument generation.

`call(task, *args, **kwargs)` returns a `Call` object. `Call(task, called_as=None, args=None, kwargs=None)` stores a task plus pre-supplied arguments. `Call.clone(into=None, with_=None)` returns an independent call object with copied args and kwargs, using `into` as the target class when supplied and replacing copied data with `with_` entries when supplied. `Call.make_context(config, core_parse_result)` returns a `Context` whose config is the supplied config and whose `remainder` is copied from the parse result.

### Collections and Namespaces

`Collection(*args, **kwargs)` creates a namespace. A leading string positional argument supplies the collection name. `loaded_from=` stores the filesystem path used for project config loading. `auto_dash_names=` controls name transformation and defaults to `True`. Remaining positional objects must be `Task`, `Collection`, or module objects; other values must raise `TypeError`. Keyword arguments bind each object under the keyword name.

`Collection.add_task(task, name=None, aliases=None, default=None)` must bind the task under the explicit name, the task's own name, or the callable name. It must transform underscores to dashes when `auto_dash_names` is true. It must raise `ValueError` when the task name conflicts with an existing subcollection or when setting a second default task. Task aliases and explicit aliases must resolve to the same task.

`Collection.add_collection(coll, name=None, default=None)` must accept a `Collection` or a module object. Module objects must be converted with `Collection.from_module`. A non-root subcollection without a name must raise `ValueError`. A collection name conflicting with an existing task must raise `ValueError`. `default=True` must mark that subcollection path as the parent's default and must raise `ValueError` when another default already exists.

`Collection.from_module(module, name=None, config=None, loaded_from=None, auto_dash_names=None)` must prefer a top-level `ns` or `namespace` `Collection` object when present. Without one, it must create a collection from all top-level `Task` objects in the module. The generated collection name must be the explicit `name`, otherwise an existing root namespace name, otherwise the last component of `module.__name__`. Module docstrings must become collection help text. `config` must be merged over any config already present on an explicit root namespace.

`Collection[name]` and `Collection.task_with_config(name)` must accept primary names, aliases, dotted subcollection paths, and subcollection default paths. Empty or `None` lookup must return the collection default. Empty lookup without a default must raise `ValueError`. Missing names must raise `KeyError`.

`Collection.task_names` returns a flat mapping of primary dotted task names to alias lists. `Collection.configuration(taskpath=None)` returns a copy of collection config for the root when `taskpath` is omitted, and returns config merged along the selected task path when a task path is supplied. Outer/root collection config must override inner collection config for conflicts along the selected path.

### Configuration

`Config(overrides=None, defaults=None, system_prefix=None, user_prefix=None, project_location=None, runtime_path=None, lazy=False)` creates a nested configuration object. Dict syntax and attribute syntax must both read and write config values. Nested dictionaries must be exposed as proxy objects with the same access behavior. Real object attributes and methods take precedence over config keys during attribute lookup, so colliding config keys must remain accessible with item syntax.

`Config.global_defaults()` returns the base defaults used by Invoke. The defaults include `run` options for command execution, `runners.local`, `sudo.password`, `sudo.prompt`, `sudo.user`, task settings such as `tasks.collection_name`, `tasks.auto_dash_names`, `tasks.dedupe`, and `tasks.search_root`, plus `timeouts.command`.

Configuration sources must merge in this documented order, with later sources overriding earlier sources: global defaults, collection configuration, system config file, user config file, project config file, shell environment, runtime config file, command-line overrides, runtime modifications, and runtime deletions. Config files must be searched with suffix priority `yaml`, `yml`, `json`, then `py`, and only the first existing suffix for a location must load. Unknown runtime config file extensions must raise `UnknownFileType`. Python config files containing module objects must raise `UnpicklableConfigMember`.

Environment variables must use the configured prefix, `INVOKE_` by default. Environment variables must only override keys already present in lower config levels. Strings and `None` defaults must remain strings. Boolean values must treat `0` and the empty string as false and other values as true. Numeric defaults must cast by calling the prior value's type. List and tuple defaults must raise `UncastableEnvVar`. Ambiguous environment variable paths must raise `AmbiguousEnvVar`.

`Config.load_defaults`, `load_collection`, `load_system`, `load_user`, `set_project_location`, `load_project`, `set_runtime_path`, `load_runtime`, `load_shell_env`, `load_overrides`, and `merge` must update the corresponding source level and refresh the merged view when their `merge` parameter is true. `Config.clone(into=None)` returns a distinct config object preserving loaded source data and user modifications; when `into` is supplied, the clone must be an instance of that subclass.

### Contexts, Runners, and Results

`Context(config=None, remainder="")` creates a command context. Without a config, it must create a default `Config`. `Context.config` returns the merged config object. The context must proxy config access through item syntax and attribute syntax.

`Context.run(command, **kwargs)` must instantiate the configured local runner class from `config.runners.local` and return that runner's `run` result. `invoke.run(command, **kwargs)` must create an anonymous `Context` and call `Context.run`. Unknown `run` keyword arguments must raise `TypeError`.

`Context.prefix(command)` and `Context.cd(path)` are context managers. Nested prefixes must be joined with `&&` before the command. Nested directories must be joined into the effective `cwd`, and spaces in directory names must be escaped. `cd` and `prefix` state must be removed when the context manager exits, including when an exception leaves the block.

`Runner.run(command, **kwargs)` must merge keyword arguments over `context.config.run`, with `timeouts.command` used as the default timeout when no explicit `timeout` is supplied. `hide` must normalize to a tuple containing zero, one, or both of `stdout` and `stderr`. `hide=True` must suppress command echoing. `dry=True` must force echoing, skip subprocess execution, and return a successful `Result` with empty captured streams. `asynchronous=True` must return a `Promise`. Supplying both `asynchronous=True` and `disown=True` must raise `ValueError`. `disown=True` must return a `Result` with empty streams, `exited is None`, and `disowned is True`.

`Result(stdout="", stderr="", encoding=None, command="", shell="", env=None, exited=0, pty=False, hide=(), pid=None, disowned=False)` stores command execution data. `Result.return_code` returns `exited`. `Result.ok` returns `True` only when `exited == 0`; `Result.failed` returns the inverse. Boolean evaluation of a `Result` must match `ok`. `Result.tail(stream, count=10)` returns the last `count` lines from the named stream, prefixed by a blank-line separator. When `env` is omitted, `Result.env` must be an empty dict.

`Promise.join()` must block until the associated command completes and then return the final `Result` or raise the same exception that synchronous `run` would raise. A `Promise` used as a context manager must call `join` when the block exits.

`MockContext(config=None, run=None, sudo=None, repeat=True)` returns predetermined `Result` objects from `run` and `sudo`. Boolean values must become `Result(exited=0)` or `Result(exited=1)`. String values must become `Result(stdout=value)`. Dict mappings must match exact command strings or compiled regex keys. When no prepared result matches, `run` or `sudo` must raise `NotImplementedError`.

### Watchers and Prompt Responses

`StreamWatcher.submit(stream)` defines the watcher protocol and must return an iterable of response strings or raise `NotImplementedError` on the base class.

`Responder(pattern, response)` must treat `pattern` as a regular expression. Each `submit(stream)` call must scan only stream text not previously consumed by that responder thread-local state. For each new match, it must yield `response`.

`FailingResponder(pattern, response, sentinel)` must behave like `Responder` and must raise `ResponseNotAccepted` when it sees `sentinel` after it has previously yielded a response.

`Context.sudo(command, **kwargs)` must run a sudo-prefixed command through the local runner, using a `FailingResponder` that watches the configured sudo prompt and sends the configured password plus a newline. Runtime `password=` and `user=` kwargs must override `sudo.password` and `sudo.user`. User-specific sudo runs must include the requested user behavior. If sudo authentication rejection is detected through the failing responder, `Context.sudo` must raise `AuthFailure`.

## CLI Behavior

With no task module configuration, the CLI must look for a Python module or package named `tasks`. The search must start from the current working directory or `tasks.search_root`/`--search-root`, walk upward toward the filesystem root, and select a module file or package that imports successfully. A configured `tasks.collection_name` or `--collection` value must replace the default module name. If no collection is found, CLI execution must exit with a user-facing collection-not-found message.

When a loaded module defines `ns` or `namespace` as a `Collection`, that collection must become the root namespace. Otherwise all top-level `Task` objects in the module must form the root collection.

The CLI grammar is `inv[oke] [--core-opts] task1 [--task1-opts] ... taskN [--taskN-opts] [-- remainder]`. Core options before tasks must affect program behavior. Core options after a task name must still affect core behavior when they do not conflict with an argument of the active task. Task arguments must accept long flags, short flags, optional equals signs, positional values for positional task parameters, globbed boolean short flags, iterable repeated flags, and incrementable repeated flags.

`--list` must print available tasks. `--list-format=flat` must use dotted paths. `--list-format=nested` must show namespace nesting. `--list-format=json` must emit JSON with collection name, help, tasks, aliases, default, and child collections. `--list-depth` must limit flat or nested traversal, and `--list-depth` with JSON list format must exit with an error.

`--help` without a task must print core help. `--help TASK` or `TASK --help` must print help for that task, including its docstring and task-specific options. Requesting help for an unknown task must raise a parse error and exit unsuccessfully.

Task execution must run pre-tasks depth-first before the requested task and post-tasks after it. By default, duplicate task calls in one session must run once. `--no-dedupe` or `tasks.dedupe=False` must allow repeated execution. Parameterized `Call` objects must dedupe by task plus args and kwargs.

The parser remainder after a bare `--` must be stored on the task `Context.remainder` and must not be parsed as Invoke flags.

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

- A task declared with `@task(name="x")` must be visible as `x` in a generated `Collection`, in `--list`, and in CLI invocation.
- A task argument named `my_option` must be presented as `--my-option` on the CLI and must be delivered to Python as `my_option`.
- A collection-level config value for a selected task must be visible through `Context.config`, `Context[...]`, and `Context` attribute access during that task.
- A project config file next to the loaded task collection must affect task parsing and command execution in the same CLI run.
- A CLI run flag such as `--echo`, `--pty`, `--warn-only`, `--hide`, `--dry`, or `--command-timeout` must override the corresponding lower configuration value for commands run by tasks in that session.
- A `Context.cd` or `Context.prefix` block must affect `Context.run` and `Context.sudo` command strings consistently.
- A nonzero command with `warn=True` must return a failed `Result`; the same command with `warn=False` must raise `UnexpectedExit`.
- A `Responder` passed to `Context.run` must write responses through the runner's stdin path and must not remove the matched text from captured output.

## Representative Workflow

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

## Non-Goals

This specification does not cover vendored modules, internal helper classes, exact private data structures, exact ANSI styling, exact column widths, exact completion script bodies, shell-specific completion integration, platform-specific PTY allocation details, signal forwarding timing, subprocess race timing, low-level terminal sizing, development automation tasks used by Invoke's own repository, or tests that require a particular test helper layout.

Parser classes are public importable objects, but this specification only covers parser behavior as it appears through task declaration, `Program`, and the documented CLI.

## Invocation Protocol

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

`Program.run(argv=None, exit=True)` must use `sys.argv` when `argv` is `None`, split a string `argv` on whitespace when a string is supplied, and use a supplied list as-is. With `exit=False`, it must not call `sys.exit` for handled `Exit`, `ParseError`, or `UnexpectedExit` conditions.

## Environment

The implementation may use any third-party packages available on PyPI. Declare runtime dependencies in a standard `requirements.txt` or `pyproject.toml` at the project root. All declared dependencies will be installed before assessment. Command workflows run against local temporary task collections and local subprocesses.

## Evaluation Notes

Assessment compares Python and CLI behavior for task metadata, parsing, namespaces, module loading, configuration precedence, contexts, runners, results, watchers, sudo failures, and intentional exits. Terminal wrapping, colors, completion script bodies, PTY edge cases, timing-sensitive signals, and repository-local development tasks are not checked.
