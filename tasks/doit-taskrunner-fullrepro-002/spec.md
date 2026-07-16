# doit Specification

## Product Overview

`doit` is a Python task runner and automation tool. Users define tasks in Python, usually in a `dodo.py` file, and `doit` executes only the tasks whose inputs, outputs, saved results, or explicit freshness checks say they need work.

The core model is a directed task graph. Tasks may run shell commands, Python callables, cleanup actions, teardown actions, or no actions at all for group tasks. `doit` stores successful run state in a dependency database so later invocations can skip tasks that are already up-to-date.

## Scope

This specification covers:

- Loading task creators from a Python namespace or `dodo.py`.
- Task dictionaries, generated subtasks, task groups, delayed task creation, and command-line task parameters.
- Shell actions, Python actions, action return values, captured output, saved values, and task result dependencies.
- File dependencies, targets, task dependencies, setup tasks, teardown, cleanup, and up-to-date decisions.
- Public Python entry points, helpers, reporters, dependency access, and extension interfaces documented for users.
- The command-line behavior of the built-in commands: `run`, `list`, `info`, `clean`, `forget`, `ignore`, `reset-dep`, `dumpdb`, `strace`, `tabcompletion`, and `help`.
- Configuration through `DOIT_CONFIG`, `pyproject.toml`, `doit.cfg`, command-line options, task parameters, and command-line variables.

## Installable Surface

The package is imported as `doit` and provides the console entry point `doit`. Running `python -m doit` is equivalent to invoking the command-line program.

Top-level imports:

```python
from doit import get_var, run, create_after, task_params, Globals
import doit
```

Documented public imports used by normal task files and integrations:

```python
from doit.action import CmdAction
from doit.task import clean_targets, result_dep
from doit.tools import (
    create_folder,
    title_with_actions,
    run_once,
    result_dep,
    config_changed,
    timeout,
    check_timestamp_unchanged,
    LongRunning,
    Interactive,
    PythonInteractiveAction,
    set_trace,
    load_ipython_extension,
)
from doit.cmd_base import Command, DoitCmdBase, TaskLoader2, ModuleTaskLoader
from doit.doit_cmd import DoitMain
from doit.reporter import ConsoleReporter
from doit.dependency import FileChangedChecker, Dependency, DbmDB
from doit.exceptions import TaskFailed, TaskError
```

## Public API

`doit.run(task_creators)` runs `doit` against a module or dictionary containing task creators instead of loading `dodo.py`. It uses the process command-line arguments after the program name and exits the process with the command result code.

`doit.get_var(name, default=None)` reads variables passed on the command line as bare `name=value` arguments. These variables are consumed before command execution and are not task names. If command-line variables have not been initialized, `get_var` returns `None`; otherwise it returns the provided default when the name is absent.

`doit.get_initial_workdir()` returns the directory from which the command was originally invoked. This remains useful because normal execution changes the working directory to the dodo file directory, or to `--dir` when specified.

`@doit.create_after(executed=None, target_regex=None, creates=None)` marks a task creator for delayed creation. The creator is evaluated only after the named task has executed. `target_regex` declares target names that may be produced by the delayed creator, and `creates` declares task basenames when they cannot be inferred from the creator name.

`@doit.task_params(param_def)` attaches command-line parameter definitions to a task creator. `param_def` must be a list using the same parameter dictionary format as task `params`. A task creator decorated with `task_params` must not also return task dictionaries that define `params`.

`Globals.dep_manager` is set during command invocation before task creation. It gives task creators, actions, and clean activities access to the current dependency manager.

`ModuleTaskLoader(mod_dict)` loads tasks from a module or dictionary using the same task creator conventions as a dodo file. `DoitMain(task_loader=None, config_filenames=("pyproject.toml", "doit.cfg"), extra_config=None).run(args)` runs the command dispatcher and returns `0`, `1`, `2`, or `3` instead of raising for ordinary user-facing command errors.

`CmdAction(action, task=None, save_out=None, shell=True, encoding="utf-8", decode_error="replace", buffering=0, **pkwargs)` creates an explicit shell action. `action` may be a string, a list of strings and `pathlib` paths, or a callable returning a command string. `save_out` stores captured stdout under the given value name. `shell` defaults to `True`, unlike `subprocess.Popen`; `stdout` and `stderr` are reserved and are not accepted as `pkwargs`.

## Task Definitions

A task creator is a function or method whose name starts with `task_`, or an object exposed in the dodo namespace with a `create_doit_tasks` callable. The task name is the creator name without the `task_` prefix unless a task dictionary uses `basename`.

Task creators return either a single dictionary, a generator yielding dictionaries, a task object, or `None`. A returned dictionary creates one task and must not contain `name`; yielded dictionaries create subtasks and must contain `name` unless they contain `basename` for a separately named task. A yielded `name` of `None` creates an empty task group so the group can carry documentation, watch paths, and shared group identity even when no concrete subtasks exist.

Supported task dictionary fields:

- `actions`: required; a list or tuple of shell actions, Python actions, explicit action objects, or `None` for a group task.
- `basename`: task name override for a returned task or generated task family.
- `name`: subtask identifier for yielded subtasks; final subtask names use `basename:name`.
- `file_dep`: file dependency paths as strings or `pathlib` paths.
- `targets`: output file or directory paths as strings or `pathlib` paths.
- `task_dep`: task names that must be processed before this task.
- `setup`: task names that run only when this task is going to execute.
- `uptodate`: freshness checks as booleans, `None`, shell command strings, callables, or `(callable, args, kwargs)` tuples.
- `calc_dep`: task names whose action results can add `file_dep`, `task_dep`, `uptodate`, or more `calc_dep` entries.
- `getargs`: a mapping from action argument name to `(task_name, value_name)`.
- `teardown`: actions executed after all selected tasks have finished, in reverse execution order.
- `clean`: `True` to remove targets, or a list of clean actions.
- `doc`: task description; otherwise the first non-empty line of the creator docstring is used.
- `params`: task action option definitions.
- `pos_arg`: action argument name that receives positional task arguments.
- `verbosity`: `0`, `1`, or `2`.
- `io`: a dictionary where `capture=False` disables internal stdout/stderr capture for the task.
- `title`: callable receiving the task and returning the run output title.
- `meta`: user/plugin metadata not interpreted by core `doit`.
- `watch`: extra watched paths for the `auto` plugin command.

Unknown task dictionary fields, invalid field types, duplicated task names, a normal task dictionary containing `name`, and a subtask dictionary without `name` or `basename` are task definition errors.

## Actions and Results

Task creator bodies run while tasks are loaded. Task actions run only when the task is selected and not up-to-date.

String actions are shell commands. List actions are command argument lists executed without a shell; elements may be strings or `pathlib` paths. Callable actions are Python actions. Tuples describe Python actions as `(callable, args, kwargs)`, with only the callable required.

The actions of one task always execute sequentially. Parallel execution only affects different tasks whose dependencies allow them to run at the same time.

Python actions succeed when they return `True`, `None`, a string, or a dictionary. Returning a dictionary saves computed task values and makes the dictionary the task result. Returning a string makes the string the task result. Returning `False` fails the task. Raising an exception is a task error. Returning a `TaskFailed` or `TaskError` instance reports that failure or error directly. Other return types are treated as task errors.

Command actions follow shell exit status. Exit code `0` succeeds. A non-zero exit code up to `125` is a task failure. An exit code above `125` is a task error. Captured stdout and stderr together form the command action result; `save_out` saves stdout under a named value.

Python action callables can receive task metadata by declaring keyword parameters named `dependencies`, `changed`, `targets`, or `task`. These values are injected only when the callable declares the parameter and the caller did not already pass the argument. The reserved injected parameters must not define defaults.

Command action strings may use dependency substitution. `dependencies`, `changed`, `targets`, task option names, and positional argument names are available as strings. The formatting mode is controlled by `action_string_formatting` with values `old`, `new`, or `both`; the default is `old`. List-form command actions are not formatted.

Task output verbosity is:

- `0`: capture stdout and stderr without displaying them.
- `1`: capture stdout and display stderr.
- `2`: display stdout and stderr immediately.

## Dependencies and Up-To-Date Status

`doit` records successful task state in a dependency database. The default backend is `dbm`; `json` and `sqlite3` are built in. The default dependency file base name is `.doit.db`, and `--db-file` or `dep_file` changes it. DBM backends may create multiple files using the configured name as a base name.

A task is not up-to-date when any explicit `uptodate` item evaluates to `False`, a file was added to or removed from `file_dep`, a file dependency changed since the last successful run, a target path does not exist, or the task has no file dependencies and no `uptodate` item equal to `True`.

The default file checker uses MD5 content hashes. The `timestamp` checker considers any modification-time change to be a change. A custom checker subclasses `FileChangedChecker` and provides the file state and modification comparison behavior expected by the dependency manager.

Targets are checked for existence only. If a target exists and file dependencies have not changed, modifying the target itself does not force the task to run. If a target is removed, the task runs again.

`file_dep` is file-oriented and does not treat directories as content dependencies. A dodo file is not automatically a dependency of every task; users force reruns after task-definition changes with `forget`, `--always-execute`, or explicit file dependencies.

`task_dep` controls execution order, not freshness. A task that only has `task_dep` and no own freshness inputs runs whenever selected. `setup` tasks run after the selected task is found out-of-date and before its actions execute.

`uptodate` accepts:

- `False` to force the task out-of-date.
- `True` as one positive freshness check, without overriding file changes or missing targets.
- `None` as an ignored dynamic placeholder.
- A shell command string, where exit code `0` means up-to-date.
- A callable receiving `(task, values)` and returning a truthy up-to-date decision.
- A tuple `(callable, args, kwargs)` for callables with extra arguments.

`doit` may short-circuit freshness checks after it already knows a task is out-of-date.

When a Python action returns a dictionary, the values must be serializable by the configured codec. `getargs` passes saved values from one task into another task's action. A `getargs` entry has the form `{argument_name: (task_name, value_name)}`; using `None` as `value_name` passes the whole saved value dictionary. When the source is a task group, the received value is a dictionary keyed by subtask name. `getargs` creates an implicit setup dependency on the source task.

`result_dep(task_name, setup_dep=False)` is an `uptodate` helper available from `doit.tools` and `doit.task`. It compares the result of another task across runs. It also creates an execution dependency on that task; with `setup_dep=True` it creates a setup dependency. For task groups, it compares the set of subtasks and each subtask result.

`calc_dep` names tasks whose computed values add dependency metadata to the current task. A calculating task returns a dictionary containing keys such as `file_dep`, `task_dep`, `uptodate`, or `calc_dep`.

## Built-In Tools

`create_folder(dir_path)` is a Python action helper that creates a directory path if it does not already exist.

`title_with_actions(task)` returns a title string that includes the task name and the string form of its actions, and can be used as the task `title` callable.

`run_once(task, values)` is an `uptodate` callable that makes a task run once after its first successful execution. Missing targets still make the task run again.

`timeout(timeout_limit)` returns an `uptodate` callable that expires after the given number of seconds or `datetime.timedelta`.

`config_changed(config, encoder=None)` returns an `uptodate` callable that compares a string or dictionary configuration against the previous successful run. Dictionaries are serialized in key-sorted JSON form; `encoder` is passed to JSON serialization.

`check_timestamp_unchanged(file_name, time="mtime", cmp_op=operator.eq)` returns an `uptodate` callable that compares a selected timestamp from the named file or directory. `time` may be `mtime`, `atime`, `ctime`, or the aliases `modify`, `access`, and `status`. The comparison callable receives `(previous_time, current_time)` and returns whether the task is up-to-date. If the path cannot be statted, the check raises an error.

`LongRunning` is a command action for long-lived processes such as servers. It starts the process, waits until interrupted by the user, and then terminates it.

`Interactive` is a command action for interactive subprocesses whose output is not captured.

`PythonInteractiveAction` is a Python action variant whose output is not captured and whose success follows exception behavior.

`set_trace()` starts a debugger in a way that works with `doit` stream redirection. `load_ipython_extension(ip=None)` registers an IPython `%doit` magic that discovers tasks from the interactive namespace.

## Command Line

The command form is:

```console
doit [run] [<options>] [<task|target> <task_options>]* [<variables>]
```

`run` is the default command, so `doit` and `doit run` execute the same operation. Command result codes are:

- `0`: all selected work completed successfully.
- `1`: at least one task failed.
- `2`: an error occurred while executing a task.
- `3`: an error happened before task execution started; reporters are not used for this case.

Global task loading options include `-f/--file` for a dodo file, `-d/--dir` for execution directory, and `-k/--seek-file` to search parent folders for the dodo file. `DOIT_FILE` and `DOIT_SEEK_FILE` can provide the matching file and seek-file options.

Run command options include `--always-execute`, `--continue`, `--verbosity`, `--failure-verbosity`, `--reporter`, `--output-file`, `--process`, `--parallel-type`, `--single`, `--auto-delayed-regex`, and `--pdb`. `--single` executes selected tasks without their task dependencies. `--continue` keeps scheduling runnable work after a failure when dependencies allow it.

Task selection accepts task names, subtask names, targets, and wildcard task patterns containing `*`. When no tasks are provided, the selected tasks are `default_tasks` from configuration or all loaded tasks if no default is configured. If a selected task accepts positional arguments, later command-line words belong to that task and are not interpreted as additional task names.

The console reporter marks executed tasks with `.`, up-to-date tasks with `--`, and ignored tasks with `!!`. Task names beginning with `_` are hidden from normal run/list output unless a command option explicitly requests private tasks.

`list` prints available tasks. By default it sorts alphabetically, omits subtasks, omits private tasks, and includes each task description. Options can sort by definition order, show subtasks, show private tasks, omit descriptions, show file dependencies, and show status. Status letters are `R` for run, `U` for up-to-date, and `I` for ignored.

`info <task>` prints task metadata, status, dependencies, targets, and, when a task is not up-to-date, the reasons it would run.

`clean [TASK ...]` executes clean behavior. `clean=True` removes target files and empty target directories, removing targets in reverse lexical order. A list-valued `clean` field executes clean actions. `--dry-run` reports clean actions without executing them, except Python clean callables that accept a `dryrun` parameter are called and receive the dry-run value. With no task arguments, `clean` cleans default tasks and enables dependency cleaning; `--clean-all` cleans all tasks, `--clean-dep` includes dependencies, and `--forget` also clears stored success state.

`forget [TASK ...]` removes successful run state so tasks will be considered for execution again without changing files. With no task arguments, it forgets default tasks unless configuration disables that behavior. `--all` forgets all tasks.

`ignore <TASK ...>` marks tasks as ignored in the dependency database. Ignored tasks are skipped on later runs and displayed as ignored. `forget` reverses the ignored state.

`reset-dep [TASK ...]` recomputes and saves file dependency state without executing actions. It preserves existing saved values and results when present, and does not calculate missing values or results.

`dumpdb` prints the dependency database content in readable form.

`tabcompletion` writes a shell completion script for bash or zsh to stdout. It can hard-code tasks for applications with expensive task loading.

`strace <task>` uses the external `strace` utility to list files opened for reading or writing by one command action task. It is a debugging aid for one task at a time, only applies to command actions, and is not a complete dependency detector.

`help`, `help <command>`, `help task`, and `help <task-name>` print command, task dictionary, and task parameter help.

## Configuration

Configuration can come from command-line options, `DOIT_CONFIG` inside the dodo file, `pyproject.toml`, `doit.cfg`, task parameter defaults, per-command sections, per-task sections, environment-backed options, and `extra_config` passed to `DoitMain`.

`pyproject.toml` uses the `tool.doit` namespace. Values under `tool.doit` apply globally, `tool.doit.commands.<command>` applies to a command, `tool.doit.tasks.<task>` applies to a task, and `tool.doit.plugins.<category>` registers plugins.

`doit.cfg` is an INI file. `GLOBAL` applies to all commands, command-named sections apply to commands, `task:<task>` sections apply to tasks, and uppercase plugin category sections register plugins.

`DOIT_CONFIG` is a dictionary in the dodo module. It can set global command defaults such as `default_tasks`, `continue`, `reporter`, `verbosity`, `backend`, `dep_file`, `check_file_uptodate`, `action_string_formatting`, `codec_cls`, `minversion`, and command-specific option names accepted by `doit`. It cannot configure options that control how the dodo file is found or loaded, such as `--file` and `--dir`.

Task parameters use dictionaries with `name`, `default`, optional `short`, optional `long`, optional `type`, optional `choices`, optional `help`, optional `inverse` for booleans, and optional environment variable support where available. Boolean parameters are flags; an inverse flag sets a boolean value to `False`. List parameters may be provided repeatedly. Choice validation reports accepted choice names when the given value is not allowed.

Command-line variables are words of the form `name=value` and are accessed from the dodo file through `doit.get_var`.

## Extension Surfaces

Custom commands subclass `Command` when they do not need loaded tasks, or `DoitCmdBase` when they operate on tasks. Command classes define a command name, help text, `cmd_options`, and `execute(opt_values, pos_args)`.

Custom task loaders subclass `TaskLoader2`. `setup(opt_values)` performs delayed initialization, `load_doit_config()` returns a configuration dictionary, and `load_tasks(cmd, pos_args)` returns task objects. `ModuleTaskLoader` is the built-in namespace-based loader for modules and dictionaries.

Plugins are enabled either by local configuration or by installed entry points. Plugin categories are `command`, `backend`, `reporter`, and `loader`. Local plugin values use the format `module:attribute`; loader plugins must also be selected by name through the global `loader` option.

Custom reporters implement the reporter event methods used by the runner. `ConsoleReporter(outstream, options)` is the default base for console reporters and receives events for initialization, status checks, task execution, success, failure, up-to-date skips, ignored skips, cleanup errors, runtime errors, teardown starts, and run completion. The built-in reporter names are `console`, `executed-only`, `json`, `zero`, and `error-only`.

`JsonReporter` emits one final JSON document on run completion containing task results and runtime errors. Each task result records whether the task succeeded, failed, was up-to-date, or was ignored, with timing fields when the task actually executed.

`Dependency.get_values(task_name)`, `get_value(task_name, key_name)`, and `get_result(task_name)` expose stored task values and results through `Globals.dep_manager`. The default `DbmDB` backend exposes `get(task_name, dependency)`, `set(task_name, dependency, value)`, and `remove(task_name)` for experienced users who intentionally manipulate stored state.

## Error Semantics

`InvalidDodoFile` reports invalid dodo/configuration loading conditions, such as a missing dodo file, non-dictionary `DOIT_CONFIG`, task names that collide with command names, unsupported `action_string_formatting`, or an unsatisfied `minversion`.

`InvalidCommand` reports invalid command-line use, unknown tasks or targets, invalid command parameters, missing custom checkers, invalid directories passed to `--dir`, and similar command-level user errors. Through `DoitMain.run`, ordinary command errors are printed and return code `3`.

`InvalidTask` reports invalid task definitions: missing `actions`, invalid field names, invalid field types, invalid action forms, invalid callable types, duplicated generated tasks, invalid `getargs`, invalid `uptodate` items, reserved injected action arguments with defaults, and `@task_params` combined with task `params`.

`TaskFailed` represents task execution that completed but failed according to the task's own result semantics, such as a Python action returning `False` or a command exiting non-zero up to `125`.

`TaskError` represents errors while executing or evaluating task behavior, such as an exception raised by a Python action, a command action that cannot construct its command string, a command exit code above `125`, or an invalid Python action return type.

`UnmetDependency`, `SetupError`, and `DependencyError` are task error subclasses used when dependent work failed or was ignored, setup behavior failed, or dependency checking/saving failed.

## Cross-View Invariants

- A task that appears as up-to-date in run output must have the same status basis visible through `info` and the dependency database until its inputs, targets, result dependencies, ignored state, or explicit freshness checks change.
- A Python action dictionary result saved during one successful run must be available to later `getargs`, `result_dep`, and `Globals.dep_manager` lookups under the same task and value names.
- A file listed as a target of one task and a file dependency of another creates an execution-order relationship even when the user did not write an explicit `task_dep`.
- A missing target forces execution in the `run` command, appears as an out-of-date reason in `info`, and is restored by running the task successfully.
- Cleaning targets removes generated outputs but does not by itself make file dependencies different; pairing clean with forget is the documented way to remove both outputs and success state.
- Ignoring a task persists in the dependency database, is shown in run/list status views, and is cleared through `forget`.
- Global and per-task configuration must affect CLI execution, `DoitMain` execution, task help, and task action parameter injection consistently.
- Task selection by task name, subtask name, target path, or wildcard must refer to the same loaded task graph and obey the same dependency rules unless `--single` is used.
- The `json` reporter and console reporters observe the same task outcomes even though they format those outcomes differently.
- The dependency backend choice changes where state is stored, not the public meaning of up-to-date, ignored, saved value, or task result state.

## Representative Workflow

Create a `dodo.py` file:

```python
from pathlib import Path
from doit.tools import run_once

def write_source(targets):
    Path(targets[0]).write_text("hello\n")
    return {"line_count": 1}

def shout(dependencies, targets, count):
    text = Path(dependencies[0]).read_text().upper()
    Path(targets[0]).write_text(f"{count}:{text}")

def task_source():
    """create input text"""
    return {
        "actions": [write_source],
        "targets": ["source.txt"],
        "uptodate": [run_once],
        "clean": True,
    }

def task_shout():
    """write an uppercase output"""
    return {
        "actions": [(shout, [], {})],
        "file_dep": ["source.txt"],
        "targets": ["shout.txt"],
        "getargs": {"count": ("source", "line_count")},
        "clean": True,
    }
```

Running `doit` creates `source.txt`, saves `line_count`, passes it to `shout`, and creates `shout.txt`. Running `doit` again skips both tasks when the files and saved values are unchanged. Removing `shout.txt` runs only the task that owns that missing target and any needed dependency work. `doit info shout` explains why `shout` would run or be skipped. `doit clean` removes the targets, and `doit forget source` clears the stored success state for `source`.

## Non-Goals

- This specification does not require reproducing private runner, dispatcher, or control class internals.
- Exact `repr()` strings, memory-address-free callable formatting, traceback formatting, and byte-for-byte console spacing are not part of the behavioral contract except for documented task status markers and command meanings.
- Platform-specific behavior of external tools such as `strace`, DBM file naming, shell command syntax, and multiprocessing pickling limits is only covered at the documented portability level.
- The `auto` watch command is plugin-provided and is not part of the built-in command contract beyond the documented `watch` task field and plugin description.
- This specification does not require implementing undocumented plugin discovery internals beyond the documented local configuration and installed entry-point categories.
- This specification does not require preserving internal helper names that are not exported, documented, or shown in public examples.

## Implementation Guidance

The expected implementation exercises public behavior through both Python APIs and command-line workflows. Tests may create temporary dodo files, invoke `python -m doit` or `doit`, inspect task output/status, use multiple dependency backends, verify persistence across invocations, and call documented public helpers directly.

The expected implementation should be assessed on behavioral compatibility: task loading, action execution, dependency decisions, saved values/results, command semantics, configuration precedence, reporter outcomes, and documented extension APIs. A correct implementation should not require on private modules, hidden attributes, exact internal class layouts, or source-only implementation details.

Fixtures are ordinary temporary projects and task definitions. Passing does not require knowing their names in advance; it requires honoring the public contracts described above.
