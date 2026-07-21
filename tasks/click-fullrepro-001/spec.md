# Click Compatibility Specification

## Product Overview

Provide an importable `click` package for constructing composable command-line
interfaces with decorators and Python objects. Commands must support argument
and option parsing, generated help, nested and chained groups, context-based
invocation, standard input/output, and filesystem-backed parameter types.

The implementation must run from the solution directory without relying on
another installed copy of Click.

## Installable Surface

The following imports must succeed:

```python
import click
from click import Argument, BadParameter, Command, Context, File, Group, Option
from click import Path, Tuple, UUID, argument, command, echo, group, option
from click import get_current_context, pass_context
from click.testing import CliRunner, Result
```

The usual public convenience names, including `INT`, `FLOAT`, `BOOL`,
`STRING`, `Choice`, and public usage-error classes, are available from the
top-level package.

## Commands And Decorators

`command` and `group` work both as `@command` / `@group` and as
`@command()` / `@group()`. They replace the decorated function with a
`Command` or `Group` object while retaining the function as its callback.

Unless a name is supplied, a command name is derived from the function name:
underscores become dashes, and one trailing suffix among `_command`, `_cmd`,
`_group`, or `_grp` is removed. Thus `init_data_command` becomes
`init-data`.

`repr(Command("name"))` is `<Command name>` and a group uses `<Group name>`.
A command's callback return value is returned by `Command.invoke` and by
`CliRunner.invoke(..., standalone_mode=False)`.

Parameters supplied through `Command(params=[...])` precede parameters added
by decorators. Group commands can be registered with decorators, with
`add_command`, or at construction time through either a name-to-command
mapping or an iterable of commands.

## Arguments And Options

`argument` and `option` attach parameter definitions in the order expected by
the callback. Supported behavior includes:

- one-value arguments and options;
- fixed-size tuples through `type=(type1, type2)` or `Tuple([...])`;
- variadic arguments through `nargs=-1`;
- type conversion for strings, integers, floats, UUIDs, and booleans;
- defaults, environment-variable input, required values, and flag values;
- dual boolean options such as `--on/--off`;
- multiple options writing to the same callback parameter, where the last
  option present on the command line wins.

A tuple type determines its arity. Supplying a conflicting explicit `nargs`
raises `ValueError`. A variadic argument followed by a required destination
argument consumes all but the final token.

Boolean conversion is case-insensitive. `1`, `true`, `t`, `yes`, `y`, and
`on` are true; `0`, `false`, `f`, `no`, `n`, and `off` are false. Invalid
integer, float, UUID, and boolean text is reported as a command-line usage
error with exit code 2.

An environment variable is consulted only when no value was supplied on the
command line. Fixed-size values split the variable and enforce their arity;
variadic values become tuples.

## Help And Errors

Every command has a generated `--help` option unless configured otherwise.
Help exits with code 0 without running the callback. It contains the command
description, usage, options, and registered subcommands. A required missing
argument, missing option value, unknown command, extra argument, or failed
conversion exits with code 2.

Arguments with help text appear in a `Positional arguments:` section before
the options section. Optional arguments are bracketed in usage, and variadic
arguments use an ellipsis. Deprecated arguments use `!` in usage and include
their deprecation label in help.

A command created with `no_args_is_help=True` shows help when invoked without
arguments and returns exit code 2. A group that requires a subcommand reports
a missing-command error after its own arguments are parsed.

## Groups, Contexts, And Chaining

Invoking a normal group runs the group callback and then the selected command.
Nested groups repeat this behavior at each level.

With `chain=True`, multiple sibling commands can be given in one invocation
and run from left to right. Each command receives only its own options and
arguments. A result callback receives the list of chained command return
values; for a non-chained group it receives the single return value. Chained
groups reject optional or variadic group arguments because they would make the
command boundary ambiguous.

`pass_context` injects the current `Context`. `Context.invoke(command,
**values)` invokes another command with the supplied values.
`Context.forward(command)` forwards the current parameter mapping, including
values not declared by the target callback context. A nested `default_map`
provides command defaults without overriding explicit command-line values.

## Files, Paths, And Output

`echo` writes text followed by a newline by default. `CliRunner.invoke`
captures stdout and stderr in a `Result`, including `output`, `stdout`,
`stderr`, `exit_code`, `exception`, and `return_value`.

`File` accepts text or binary modes. A filename of `-` maps to the matching
standard stream. With `atomic=True`, writes go to a temporary file and replace
the destination only after successful command completion. `Path(allow_dash=True)`
accepts `-` as a path value. `CliRunner.isolated_filesystem()` supplies a
temporary current directory for file workflows.

## Behavioral Invariants

- Decorator syntax and direct object construction produce interoperable
  commands and groups.
- Parsed values, context parameters, callback arguments, and return values
  agree for the same invocation.
- Help generation never invokes the command callback.
- Chained commands preserve command-line order.
- Explicit command-line values take precedence over environment and default
  values.
- User input errors use Click's public exception and exit-code behavior rather
  than leaking internal exceptions.

## Non-Goals

Shell completion scripts, terminal emulation beyond captured streams, private
parser modules, localization catalogs, repository tooling, and exact internal
object layout are outside this compatibility surface.
