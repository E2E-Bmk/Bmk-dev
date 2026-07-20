# Cleo Specification

## Product Overview

Cleo is a Python framework for building command-line applications. It lets an application define commands as Python classes, describe positional arguments and options, parse command-line input, write styled output, ask interactive questions, dispatch console events, and test commands through buffered I/O.

The core contract is that command definitions, parsed input, command execution, and output buffers describe the same user-visible command invocation. A command author defines arguments and options, an `Application` selects and runs a command, `IO` exposes input/output state to the command, and testers observe the same status code and output that a user would see without depending on a real terminal.

## Scope

This specification covers:

- application registration and command lookup through `Application`
- command classes, command defaults, command aliases, and command invocation through `Command`
- argument and option declarations through helpers and input-definition classes
- parsing through `ArgvInput` and `StringInput`
- output, formatting tags, verbosity, decorated output, buffered output, null output, and sections
- `IO`, `BufferedIO`, `NullIO`, command testers, and application testers
- built-in command semantics for help, list, and completion at a behavioral level
- table, question, confirmation, choice, progress, and style helper behavior where exposed by public command/helper APIs
- console events, event dispatching, command loaders, public exception classes, and command error status behavior

The scope is intentionally behavioral. It does not require byte-for-byte terminal snapshots, exact ANSI escape sequences, traceback formatting, or private helper structure.

## Installable Surface

The distribution is installed as `cleo` and imported as:

```python
from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import argument, option
```

Covered public import paths include:

- `cleo`: package version metadata when present
- `cleo.application`: `Application`
- `cleo.commands.command`: `Command`
- `cleo.commands.help_command`, `cleo.commands.list_command`, `cleo.commands.completions_command`
- `cleo.helpers`: `argument`, `option`, `tokenize`
- `cleo.io.inputs`: `Argument`, `Option`, `Definition`, `Input`, `ArgvInput`, `StringInput`
- `cleo.io.outputs`: `Output`, `Verbosity`, `Type`, `BufferedOutput`, `NullOutput`, `StreamOutput`, `SectionOutput`
- `cleo.io.io`, `cleo.io.buffered_io`, `cleo.io.null_io`: `IO`, `BufferedIO`, `NullIO`
- `cleo.testers`: `CommandTester`, `ApplicationTester`
- `cleo.loaders`: `CommandLoader`, `FactoryCommandLoader`
- `cleo.events`: console event classes, event names, and `EventDispatcher`
- `cleo.formatters`: `Formatter`, `Style`, `StyleStack`
- `cleo.ui`: documented questions, tables, progress helpers, and console UI classes
- `cleo.exceptions`: `CleoError`, `CleoLogicError`, `CleoRuntimeError`, `CleoValueError`, `CleoNoSuchOptionError`, `CleoCommandNotFoundError`, `CleoNamespaceNotFoundError`, `CleoMissingArgumentsError`, and other public user-error classes

No project-specific executable is required. A user creates an application script and calls `Application().run()`.

## Product State Model

Cleo state has four public projections:

- Definition projection: an application owns commands; each command owns an input `Definition` made from `Argument` and `Option` objects.
- Input projection: `ArgvInput` or `StringInput` tokenizes user input and stores argument and option values according to a definition.
- Execution projection: `Application.run`, `Command.run`, `Command.handle`, command loaders, and event dispatch determine which command runs and what status code is returned.
- Output projection: `IO`, `Output`, `BufferedOutput`, formatters, sections, and testers expose the text and error text produced by the command.

These projections must agree:

- A command registered in an application must be discoverable by its name and aliases.
- A command's `argument(name)` and `option(name)` must return values parsed from the same input used by the application.
- `CommandTester.execute` and `ApplicationTester.execute` must run through the same command definitions and return the same status code semantics as `Application.run`.
- Output written through `Command.line`, `Command.write`, `IO.write_line`, and `Output.write_line` must appear in the associated output stream unless verbosity or quiet mode suppresses it.
- Error output written through `line_error` or `write_error_line` must appear in the error output stream.
- Decorated output must keep style tags meaningful to the formatter; undecorated output must remove user-facing formatting tags while preserving plain text.

## Public API

### Application

`Application(name="console", version="")` creates a command container. `name`, `display_name`, `version`, `long_version`, `definition`, `default_commands`, `help`, and `ui` must expose the current application metadata and defaults. `set_name`, `set_display_name`, `set_version`, `set_ui`, `set_event_dispatcher`, and `set_command_loader` must update the corresponding application state.

`add(command)` must register a command and return the command unless registration is refused by an invalid name or duplicate conflict. Registered commands must receive the application through `command.application`. `get(name)` must return a command by full name, alias, or unambiguous shortcut and must raise a command-not-found error when no command matches. `has(name)` must return whether a command is available. `all(namespace=None)` must return registered commands, optionally filtered by namespace. `get_namespaces`, `extract_namespace`, and `find_namespace` must report namespaces derived from command names.

`run(input=None, output=None, error_output=None)` must create or use `IO`, parse command input, run the selected command, dispatch command/error/terminate events when an event dispatcher is configured, render user errors, and return an integer status code. When auto-exit is disabled, `run` must return the status code instead of exiting the process. When exceptions are caught, user errors must be rendered to error output with a non-zero status code; when exception catching is disabled, exceptions must propagate.

Adding a command marked as the default command must make the application a single-command application: invoking the application without a command name must run that command, and the command name must not be required in input.

### Command

`Command` represents one command. A subclass may define `name`, `description`, `help`, `aliases`, `arguments`, and `options` as class attributes, or override `configure()`. `configure()` must build the command definition before execution. `handle()` contains command behavior and must return an integer status code or `None`; `None` means success status `0`.

`run(io)` must initialize and interact with the command, bind `io`, validate required arguments and options unless validation is ignored, call `handle`, and return the resulting status code. `execute(io)` must call the command's execution path. `ignore_validation_errors()` must allow a command to run even when its input definition is missing required values.

`argument(name)` and `option(name)` must return parsed values from the current input. Calling an unknown option must raise `CleoNoSuchOptionError`. Missing required arguments must raise `CleoMissingArgumentsError` before command handling.

`call(name, args=None)` must invoke another command in the same application and return its status code using normal output. `call_silent(name, args=None)` must invoke the command while suppressing regular output. `set_application(application)` must attach or detach the command from an application.

`default()`, when present on a command, must mark the command as the application's default when added.

### Arguments, Options, and Input Definitions

`argument(name, description=None, optional=False, multiple=False, default=None)` must return an `Argument` whose `name`, `description`, required/list flags, and default match the helper arguments. A required argument must not have a default. A list argument must be the final positional argument in a definition. Violations must raise `CleoLogicError` or `CleoValueError`.

`option(long_name, short_name=None, description=None, flag=True, value_required=True, multiple=False, default=None)` must return an `Option`. A flag option must not require a value and must default to `False` unless configured otherwise. A non-flag option may require a value, accept an optional value, or accept multiple values. Shortcuts must be usable with a single dash; long names must be usable with two dashes.

`Definition` must preserve argument order, option names, shortcuts, defaults, and required counts. `add_argument` and `add_option` must reject duplicate names and invalid ordering. `argument(name_or_index)`, `option(name)`, and `option_for_shortcut(shortcut)` must return matching definition objects or raise public errors when absent. `synopsis(short=False)` must describe command usage using the current definition without requiring exact column formatting.

### Input Parsing

`ArgvInput(argv=None, definition=None)` must parse command-line tokens. It must support:

- long options as `--name value`, `--name=value`, and boolean `--flag`
- negated boolean options where the option definition supports that form
- short options as `-x`, grouped short flags such as `-abc`, and value forms such as `-o value` or `-ovalue`
- `--` as the end of option parsing
- positional arguments in definition order

`StringInput(input)` must tokenize shell-like strings and parse them with the same semantics as `ArgvInput`. Quoted text must become one argument value. `first_argument()` must return the first non-option token when present. `has_parameter_option` and `parameter_option` must inspect raw tokens for configured option names without requiring full parsing.

Parsing must raise a public runtime/user error for unknown options, missing option values, too many arguments, or missing required arguments.

### Output, Formatting, and IO

`Output` must expose verbosity levels `QUIET`, `NORMAL`, `VERBOSE`, `VERY_VERBOSE`, and `DEBUG`, and output types `NORMAL`, `RAW`, and `PLAIN`. `set_verbosity`, `is_quiet`, `is_verbose`, `is_very_verbose`, and `is_debug` must reflect the configured threshold.

`write` and `write_line` must send text to the underlying stream unless the message verbosity is above the output's current verbosity or quiet mode suppresses it. `RAW` output must write tags unchanged. `PLAIN` output must remove formatting tags. Normal decorated output must pass tags through the formatter; undecorated output must remove formatting tags. `remove_format` must return plain text.

`BufferedOutput.fetch()` must return accumulated text. `clear()` must empty the buffer. `NullOutput` must discard all writes. `SectionOutput` must support independent sections that write through the same stream and may be overwritten.

`IO(input, output, error_output)` must route reads to input, normal writes to output, and error writes to error output. `interactive(False)` must disable interactive prompting. `decorated(value)` and `set_verbosity(value)` must update output and error output consistently. `with_input(input)` must return an IO object using the replacement input with the same outputs.

### Formatting Styles and Helpers

The formatter must recognize built-in semantic tags such as `info`, `comment`, `question`, and `error`. `Command.add_style(name, fg=None, bg=None, options=None)` must add a style usable by output tags. Supported colors are `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, and `default`. Supported options include `bold`, `underscore`, `blink`, `reverse`, and `conceal`. Unknown style names in decorated output must not corrupt the plain text.

`Command.line`, `write`, `line_error`, `info`, `comment`, and `question` must write through the command's `IO`. `table`, `table_separator`, `render_table`, `confirm`, `ask`, `secret`, `choice`, `progress_bar`, `progress_indicator`, and `spin` must delegate to the documented UI helpers using the current `IO`.

Table helpers must accept headers, rows, separators, cell spans, and named styles such as `default`, `compact`, and `borderless`. The rendered output must preserve cell text, row order, headers, and separators without requiring tests to assert exact border characters unless a style explicitly defines those characters.

Question helpers must return defaults for empty input, validate choices, support multi-select when enabled, and retry until valid input or maximum attempts. `confirm` must return `True` when input matches the configured true-answer regex and `False` otherwise or when the default is false and input is empty.

### Events, Loaders, and Testers

`EventDispatcher` must allow listeners to be registered for console event names and must dispatch event objects in listener order. Command events must expose the command and IO. Error events must expose the error and allow an exit code to be observed or changed where supported.

`FactoryCommandLoader` must map command names to factories. It must report whether a command exists, return command names, and instantiate the command when requested. Missing commands must raise a public not-found error.

`CommandTester(command)` must execute a command with buffered input/output and expose `status_code`, `io`, and `execute(args="", inputs=None, options=None)`. `ApplicationTester(application)` must execute an application with buffered IO. Testers must let callers read captured output and error output without relying on a real terminal.

## Error Semantics

- Invalid command names, missing commands, and ambiguous shortcuts must raise public command or namespace errors.
- Unknown options must raise `CleoNoSuchOptionError` or an equivalent public user error.
- Missing required arguments must raise `CleoMissingArgumentsError`.
- Invalid argument/option definitions, duplicate names, invalid defaults, and invalid definition ordering must raise `CleoLogicError` or `CleoValueError`.
- Input parsing must raise public user/runtime errors for missing option values, too many arguments, and unsupported tokens.
- A command returning `None` must be treated as status code `0`. A command returning an integer must use that integer as the status code.
- Application user errors must render to error output and return a non-zero status when exception catching is enabled; they must propagate when exception catching is disabled.
- `Command.call` must raise a public command-not-found error when the target command does not exist.

## Cross-View Invariants

- A command added to an application must be present in `Application.all()` and discoverable by `get` and `has`.
- A command selected by a shortcut must be the same command that would be selected by the full unambiguous name.
- Values returned by `Command.argument` and `Command.option` must match the values parsed by the `Input` object for that command invocation.
- `CommandTester.status_code` must match the status code returned by the command execution path.
- Text written through command helper methods must be observable in the tester's buffered output unless verbosity suppresses it.
- Error text written through error helpers must be observable in the tester's buffered error output.
- `IO.decorated(False)` must cause normal output and error output to remove formatting tags consistently.
- Application global options such as quiet, verbose, ANSI/no-ANSI, no-interaction, help, and version must affect the same IO and command state that command handlers observe.
- A default command must behave as both a registered command and the command selected when no command name is supplied.
- Event listeners must observe the same command and IO objects that the application uses to run the command.

## Representative Workflows

### Command With Argument and Flag Option

```python
from cleo.application import Application
from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.testers.command_tester import CommandTester

class GreetCommand(Command):
    name = "greet"
    arguments = [argument("name", optional=True)]
    options = [option("yell", "y", flag=True)]

    def handle(self):
        text = "Hello " + (self.argument("name") or "")
        text = text.strip()
        if self.option("yell"):
            text = text.upper()
        self.line(text)

app = Application()
command = app.add(GreetCommand())
tester = CommandTester(command)
status = tester.execute("Alice --yell")
assert status == 0
assert "HELLO ALICE" in tester.io.fetch_output()
```

### Single-Command Application

```python
app = Application("tool", "1.0")
app.add(GreetCommand().default())
tester = ApplicationTester(app)
tester.execute("Bob")
assert tester.status_code == 0
assert "Hello Bob" in tester.io.fetch_output()
```

### Interactive Question

```python
class AskCommand(Command):
    name = "ask"

    def handle(self):
        answer = self.confirm("Continue?", default=False)
        self.line("yes" if answer else "no")

tester = CommandTester(AskCommand())
tester.execute(inputs="y\n")
assert "yes" in tester.io.fetch_output()
```

## Non-Goals

- Exact ANSI byte sequences, terminal cursor movement, color autodetection internals, and platform terminal quirks are not part of this contract.
- Exact help text spacing, table border snapshots, progress animation frames, tracebacks, and completion script byte-for-byte contents are not required beyond documented behavior.
- Private helpers, private modules, fixture classes, and test-only command classes are not public requirements.
- Shell integration installation, package entry-point metadata outside the public import paths, and external terminal behavior are outside scope.
- The specification does not require compatibility with unpublished Cleo 3 rewrite internals beyond the public API described here.
