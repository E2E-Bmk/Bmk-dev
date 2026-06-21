# MiniShell Public Product Packet

## Overview

Build `main.py`, a dependency-free Python program that implements a simplified Unix-like shell. It is inspired by mature shell implementations and should behave like a small, deterministic shell suitable for automated testing.

The program must be runnable from the solution directory:

```bash
python main.py
```

Use only the Python standard library.

The program reads newline-separated command lines from standard input, executes them in order, and writes deterministic output to standard output and standard error.

## Feature Set

The product has seven feature modules:

1. Command parsing.
2. Built-in and deterministic utility command execution.
3. Mutable shell state.
4. Environment variable expansion.
5. Pipelines.
6. Redirections.
7. Exit status and error recovery.

These modules are intentionally state-dependent. Parsed tokens feed command execution; `cd`, `export`, and `unset` mutate shell state; environment variables affect later commands; pipelines connect command outputs to later command inputs; redirections change where command input and output come from; and failures should update exit status without corrupting persistent shell state.

## Global Invariants

The following invariants define system correctness:

- Command parsing, variable expansion, redirection handling, and pipeline splitting must remain distinct even when they appear in the same command line.
- Shell state must persist across input lines within the same process.
- `cd` must update the current working directory only on success.
- `export` and `unset` must affect later environment expansion and `env` output.
- Variable expansion must follow quoting rules consistently.
- Pipeline output from one command must become input to the next command without leaking into normal stdout unless it is the final output.
- Redirections must affect only the command where they appear.
- Failed commands must not corrupt the working directory, environment variables, or unrelated files.
- `$?` must reflect the exit status of the most recently executed command or pipeline.
- Error messages must be deterministic enough for automated checking and must be written to standard error, not standard output.

## Command Input Model

The program reads commands from `stdin`.

Each line is one shell command line.

Commands are executed sequentially.

Shell state persists across lines during a single run.

The program may terminate early if it executes `exit`.

## Output Channels

The program must not print an interactive prompt.

Successful command output is written to standard output.

Diagnostics for malformed commands, unknown commands, failed redirections, invalid `cd`, invalid `export`, unreadable `cat` files, and other command failures are written to standard error.

Failures should not write diagnostic text to standard output.

## Command Parsing

The shell must parse command lines into commands and arguments.

Whitespace separates tokens unless inside quotes.

Single quotes preserve literal text and disable variable expansion.

Double quotes preserve spaces but allow variable expansion.

The special operators `|`, `<`, `>`, and `>>` are parsed as operators when they appear outside quotes.

When these characters appear inside single or double quotes, they are ordinary literal text.

Unmatched quotes should produce a deterministic error and must not corrupt shell state.

The shell does not need to implement full Bash grammar.

## Built-in Commands

The shell must support the following built-ins:

- `echo`
- `pwd`
- `cd`
- `export`
- `unset`
- `env`
- `exit`

The shell must also support a small deterministic utility-command subset:

- `cat`
- `grep`

These utility commands are part of the benchmark contract. They should be implemented by the submitted program or otherwise behave deterministically without depending on optional host-system tools.

### `echo`

`echo` prints its arguments separated by a single space.

`echo -n` suppresses the trailing newline.

### `pwd`

`pwd` prints the current working directory.

### `cd PATH`

`cd PATH` changes the current working directory.

The new working directory must persist across later commands.

Successful `cd` produces no standard output.

If `PATH` is invalid, `cd` must fail and the previous working directory must remain unchanged.

### `export NAME=value`

`export NAME=value` sets an environment variable.

Valid variable names match `[A-Za-z_][A-Za-z0-9_]*`.

The variable must be visible to later variable expansion and `env`.

Successful `export` produces no standard output.

Invalid variable names must produce an error without modifying the environment.

### `unset NAME`

`unset NAME` removes an environment variable if present.

Removing a missing variable should not be treated as a fatal error.

Successful `unset` produces no standard output.

### `env`

The shell maintains its own managed environment for this benchmark.

The managed environment starts empty when `main.py` starts.

Only variables set by successful `export NAME=value` commands are required to appear in later `$NAME` expansion and `env` output.

`env` prints managed environment variables in lexicographic order by variable name using:

```text
NAME=value
```

### `exit`

`exit` terminates command processing.

Commands appearing after `exit` in the input must not run.

`exit` itself produces no standard output.

### `cat [FILE ...]`

`cat` prints file contents to standard output.

If no file is provided, `cat` reads from standard input.

If a file cannot be read, `cat` must fail with a deterministic error and a nonzero exit status.

### `grep PATTERN`

`grep PATTERN` reads lines from standard input and prints the lines that contain `PATTERN` as a literal substring.

It exits with status `0` when at least one line matches and status `1` when no lines match.

Regular-expression behavior is not required.

## Environment Variable Expansion

The shell must support `$NAME` expansion.

Variable names in `$NAME` follow the same `[A-Za-z_][A-Za-z0-9_]*` rule used by `export`.

Expansion consumes the longest valid variable name after `$`.

If `NAME` exists, `$NAME` expands to the variable value.

If `NAME` is undefined, `$NAME` expands to an empty string.

For benchmark purposes, `$NAME` looks up the managed environment described in the `env` section, not arbitrary host-system environment variables.

The shell must support `$?`, which expands to the exit status of the most recently executed command or pipeline.

Expansion occurs before command execution.

Expansion applies outside quotes and inside double quotes.

Expansion does not apply inside single quotes.

## Pipelines

The shell must support `|`.

In a pipeline:

```text
command1 | command2
```

the standard output of `command1` becomes the standard input of `command2`.

Pipelines may contain more than two commands.

The exit status of a pipeline is the exit status of the last command.

For benchmark purposes, pipelines are required to support `echo`, `cat`, `grep`, and simple commands that only use standard input and standard output.

The benchmark does not require `cd`, `export`, `unset`, `env`, or `exit` to appear inside a pipeline.

## Redirections

The shell must support:

- `>` output redirection, replacing file contents.
- `>>` output redirection, appending to file contents.
- `<` input redirection, reading command input from a file.

Redirections apply only to the command where they appear.

For benchmark purposes, each redirection operator is followed by one filename token.

Filenames in redirection tests are simple relative paths without globbing or shell expansion.

Failed redirections must produce a deterministic error and must not partially mutate persistent shell state.

## External Commands

External command execution is optional.

The benchmark only relies on the deterministic commands specified above. Implementations may execute other host commands if available, but correctness must not depend on commands outside the public contract.

## Error Behavior and Recovery

Malformed commands, unknown commands, failed redirections, invalid `cd`, and invalid `export` should produce deterministic errors.

Exact error text is not public API unless explicitly stated by a test harness, but errors must be recognizable and stable.

Failed operations should return a nonzero status, update `$?`, and not poison later valid commands in the same process.

## Non-Goals

Do not implement full Bash compatibility.

Do not implement:

- job control
- signal handling
- interactive prompt behavior
- command history
- wildcard expansion
- subshells
- command substitution
- heredoc syntax
- `&&`
- `||`
- `;`
- shell functions
- aliases

The goal is a practical compatibility subset with robust parsing, state mutation, pipeline, redirection, and recovery behavior.

## Evaluation Style

Hidden tests are split into two scores:

- Unit tests exercise one feature module at a time with short command sequences.
- System tests exercise interactions across at least two modules. They inspect command output, working-directory state, environment-variable state, file contents after redirection, pipeline behavior, exit-status expansion, and recovery after errors.

System tests are labeled by dimension:

- `cross_feature_dataflow`
- `state_accumulation`
- `global_invariant`
- `error_atomicity`
- `operation_order_sensitivity`
- `boundary_crossing`

The benchmark does not inspect private implementation details.
