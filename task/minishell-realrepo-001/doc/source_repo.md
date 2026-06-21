# Source Repo: mcombeau Minishell

- Repository: `mcombeau/minishell`
- URL: https://github.com/mcombeau/minishell
- Reference status: archived read-only repository, archived by owner on 2024-11-30
- Source language: C
- Benchmark case: `minishell-realrepo-001`

## Selected Surface

This task uses shell command parsing, builtin command execution, environment variable expansion, pipes, redirections, exit status propagation, and error recovery.

The source README describes Minishell as a small shell project implementing redirections, pipes, environment variable expansion, and the `cd`, `echo`, `env`, `exit`, `export`, `pwd`, and `unset` builtins. The benchmark keeps that stateful shell surface but removes interactive-only features, host-system dependency, and full Bash compatibility.

## Source Evidence

Verified source facts from https://github.com/mcombeau/minishell:

- The repository page marks the project as archived and read-only as of 2024-11-30.
- The README describes Minishell as a 42 school shell project implemented in C.
- The README lists redirections, pipes, environment variable expansion, `$?`, and the `cd`, `echo`, `env`, `exit`, `export`, `pwd`, and `unset` builtins.
- The README also lists interactive features and Bash-adjacent behavior that this benchmark intentionally excludes.

## Rationale

A shell is a real-world stateful command execution system. Individual features such as echo, cd, export, pipes, and redirections can be tested independently, while hidden system rubrics can evaluate whether these features compose correctly across multi-step command sequences.

This task targets the unit/system gap: a model may implement individual shell features correctly, but fail when environment state, redirection, pipelines, working directory changes, and exit status interact.

## Benchmark Simplifications

- The benchmark uses `python main.py` instead of compiling the original C project.
- The benchmark is non-interactive and reads newline-separated commands from stdin.
- Prompt display, command history, signals, heredocs, wildcards, `&&`, `||`, `;`, and full Bash compatibility are out of scope.
- `cat` and `grep` are treated as deterministic benchmark utility commands instead of optional host-system executables.

## Non-Fabrication Notes

- No reference score is claimed in this packet.
- No candidate score or unit/system gap is claimed in this packet.
- The original C implementation is not copied or required.
- The benchmark is an abstraction of the source repository's stateful shell surface, not a line-by-line port.
