# MiniShell Unit/System Requirement Map

Date: 2026-06-20

Public packet: `prd.md`
Rubric: `rubric.json`

## Public Requirements

| ID | Capability | Public packet section | Observable behavior |
| --- | --- | --- | --- |
| `REQ-exec-sequence` | Sequential command execution | Command Input Model | Newline-separated commands run in order in one process |
| `REQ-state-persistence` | Mutable shell state | Command Input Model, Global Invariants | Working directory and environment changes persist across later lines |
| `REQ-parse-whitespace` | Token splitting | Command Parsing | Unquoted whitespace separates arguments |
| `REQ-parse-operators` | Operator parsing boundary | Command Parsing | `|`, `<`, `>`, and `>>` are operators outside quotes and literal text inside quotes |
| `REQ-parse-single-quotes` | Single-quote parsing | Command Parsing | Single quotes preserve literal text and disable expansion |
| `REQ-parse-double-quotes` | Double-quote parsing | Command Parsing | Double quotes preserve spaces and allow expansion |
| `REQ-echo-basic` | Basic `echo` | Built-in Commands | Arguments print separated by one space |
| `REQ-echo-no-newline` | `echo -n` | Built-in Commands | `-n` suppresses trailing newline |
| `REQ-pwd-basic` | `pwd` | Built-in Commands | Current working directory is printed |
| `REQ-cd-state` | Successful `cd` | Built-in Commands | Working directory changes only on successful `cd` |
| `REQ-cd-error-atomicity` | Failed `cd` recovery | Error Behavior and Recovery | Failed `cd` leaves previous working directory intact |
| `REQ-export-set` | `export NAME=value` | Built-in Commands | Environment variable is stored for later commands |
| `REQ-var-name` | Variable-name syntax | Built-in Commands, Environment Variable Expansion | Variable names match `[A-Za-z_][A-Za-z0-9_]*` |
| `REQ-export-error-atomicity` | Failed `export` recovery | Error Behavior and Recovery | Invalid export does not corrupt existing variables |
| `REQ-unset-basic` | `unset NAME` | Built-in Commands | Variable is removed if present |
| `REQ-env-managed` | Managed benchmark environment | Built-in Commands, Environment Variable Expansion | The benchmark environment starts empty and contains only successful `export` assignments |
| `REQ-env-output` | `env` output | Built-in Commands | Environment prints as deterministic `NAME=value` lines |
| `REQ-var-expansion` | `$NAME` expansion | Environment Variable Expansion | Defined variables expand outside single quotes |
| `REQ-var-undefined` | Undefined variable expansion | Environment Variable Expansion | Missing variables expand to an empty string |
| `REQ-exit-status-expansion` | `$?` expansion | Environment Variable Expansion | `$?` reflects the most recent command or pipeline status |
| `REQ-pipe-dataflow` | Pipeline stdout flow | Pipelines | Left command output becomes right command input |
| `REQ-pipe-status` | Pipeline status | Pipelines | Pipeline status is the last command's status |
| `REQ-redir-output` | `>` redirection | Redirections | Output redirection replaces file contents |
| `REQ-redir-append` | `>>` redirection | Redirections | Append redirection preserves previous file content |
| `REQ-redir-input` | `<` redirection | Redirections | Command input can come from a file |
| `REQ-redir-error-atomicity` | Redirection scope/recovery | Redirections, Global Invariants | Redirection affects only the target command and does not corrupt shell state |
| `REQ-exit-basic` | `exit` | Built-in Commands | Later input lines are not executed after `exit` |
| `REQ-cat-stdin` | `cat` stdin mode | Built-in Commands | `cat` without file arguments reads standard input |
| `REQ-cat-file` | `cat` file mode | Built-in Commands | `cat FILE` prints file contents |
| `REQ-grep-literal` | `grep PATTERN` filtering | Built-in Commands | `grep` prints stdin lines containing a literal pattern |
| `REQ-grep-status` | `grep` exit status | Built-in Commands | `grep` exits `0` on match and `1` on no match |
| `REQ-error-stderr` | Error output channel | Output Channels, Error Behavior and Recovery | Diagnostic text is written to stderr and normal stdout remains clean |
| `REQ-error-status` | Failure exit status | Error Behavior and Recovery | Failed commands update `$?` to a nonzero status |
| `REQ-error-deterministic` | Deterministic errors | Error Behavior and Recovery | Failures are recognizable and later valid commands still run |

## Unit Coverage

| Test | Feature | Requirement refs | Public basis |
| --- | --- | --- | --- |
| `MSU001` | basic execution | `REQ-exec-sequence`, `REQ-echo-basic` | Simple commands run in stdin order |
| `MSU002` | echo | `REQ-echo-basic`, `REQ-echo-no-newline` | `echo` spacing and `-n` behavior |
| `MSU003` | quoting | `REQ-parse-whitespace`, `REQ-parse-single-quotes`, `REQ-parse-double-quotes` | Quoted strings preserve spaces |
| `MSU004` | pwd/cd | `REQ-pwd-basic`, `REQ-cd-state` | `cd` affects later `pwd` |
| `MSU005` | environment | `REQ-export-set`, `REQ-var-expansion` | Exported variables expand later |
| `MSU006` | environment | `REQ-unset-basic`, `REQ-var-undefined` | Unset removes variable and missing values expand empty |
| `MSU007` | environment | `REQ-export-set`, `REQ-env-managed`, `REQ-env-output` | `env` prints only managed variables in deterministic order |
| `MSU008` | pipeline | `REQ-pipe-dataflow`, `REQ-cat-stdin` | Pipeline forwards stdout to `cat` stdin |
| `MSU009` | redirection | `REQ-redir-output`, `REQ-redir-input`, `REQ-cat-stdin` | Output file can be read back as input |
| `MSU010` | exit status | `REQ-exit-status-expansion` | `$?` exposes latest successful status |
| `MSU011` | exit | `REQ-exit-basic` | `exit` stops later commands |
| `MSU012` | error recovery | `REQ-error-deterministic`, `REQ-error-stderr`, `REQ-exec-sequence` | Unknown command diagnostics use stderr and later stdout remains clean |
| `MSU013` | utility commands | `REQ-cat-file` | `cat FILE` prints file contents |
| `MSU014` | quoting | `REQ-parse-operators`, `REQ-parse-single-quotes`, `REQ-parse-double-quotes` | Operators inside quotes are literal text |

## System Coverage

| Test | system_dimension | Crossed modules | Requirement refs | Public basis |
| --- | --- | --- | --- | --- |
| `MSS001` | `state_accumulation` | cd -> pwd | `REQ-state-persistence`, `REQ-cd-state`, `REQ-pwd-basic` | Directory changes persist across commands |
| `MSS002` | `cross_feature_dataflow` | export -> expansion -> pipeline | `REQ-export-set`, `REQ-var-expansion`, `REQ-pipe-dataflow`, `REQ-cat-stdin` | Environment state feeds command output and pipeline input |
| `MSS003` | `global_invariant` | quoting -> expansion | `REQ-parse-single-quotes`, `REQ-parse-double-quotes`, `REQ-var-expansion` | Quote rules and expansion stay distinct |
| `MSS004` | `cross_feature_dataflow` | redirection -> input -> pipeline | `REQ-redir-output`, `REQ-redir-input`, `REQ-pipe-dataflow`, `REQ-cat-stdin` | Redirected file output becomes later pipeline input |
| `MSS005` | `operation_order_sensitivity` | replace redirection -> append redirection | `REQ-redir-output`, `REQ-redir-append`, `REQ-cat-file` | Final file content depends on operation order |
| `MSS006` | `error_atomicity` | failed cd -> pwd -> later command | `REQ-cd-error-atomicity`, `REQ-pwd-basic`, `REQ-error-deterministic` | Failed `cd` preserves cwd and execution continues |
| `MSS007` | `error_atomicity` | export -> failed export -> expansion | `REQ-export-set`, `REQ-var-name`, `REQ-export-error-atomicity`, `REQ-var-expansion` | Invalid export does not corrupt previous environment |
| `MSS008` | `boundary_crossing` | pipeline -> grep status -> `$?` | `REQ-pipe-dataflow`, `REQ-pipe-status`, `REQ-exit-status-expansion`, `REQ-grep-literal`, `REQ-grep-status` | Pipeline output and status are both observable |
| `MSS009` | `boundary_crossing` | export -> unset -> expansion -> env | `REQ-export-set`, `REQ-unset-basic`, `REQ-var-undefined`, `REQ-env-output` | Removed variables disappear from both expansion and env |
| `MSS010` | `global_invariant` | redirection -> pipeline -> file read | `REQ-redir-output`, `REQ-redir-error-atomicity`, `REQ-pipe-dataflow`, `REQ-cat-stdin`, `REQ-cat-file` | Redirection scope and pipeline flow remain separate |
| `MSS011` | `boundary_crossing` | failed command -> stderr -> `$?` -> later stdout | `REQ-error-deterministic`, `REQ-error-stderr`, `REQ-error-status`, `REQ-exit-status-expansion`, `REQ-exec-sequence` | Failures update status, keep diagnostics off stdout, and allow later commands |

System dimension coverage:

- `cross_feature_dataflow`: `MSS002`, `MSS004`
- `state_accumulation`: `MSS001`
- `global_invariant`: `MSS003`, `MSS010`
- `error_atomicity`: `MSS006`, `MSS007`
- `operation_order_sensitivity`: `MSS005`
- `boundary_crossing`: `MSS008`, `MSS009`, `MSS011`

## Reference And Model Verification

Pending. The next validation step is to run a reference solution and at least one candidate solution against `rubric.json`, then record unit score, system score, and gap.

## Fairness Notes

- The public packet intentionally excludes full Bash compatibility, job control, wildcard expansion, subshells, heredocs, and compound shell operators.
- Tests focus on observable stdout, file contents, working directory state, environment state, and exit status behavior.
- Exact error text is not treated as public API unless a test checks only stable observable recovery behavior.

## Strengthening Pass 2026-06-21

Additional cases were added after comparing this task with the official core examples in `Bmk-dev`:

- `MSU015` checks syntax-error recovery through public stdin behavior rather than private parser internals.
- `MSU016` checks `grep` miss status propagation into later `$?` expansion.
- `MSS012` checks the boundary between pipeline dataflow and per-command input redirection.

This brings MiniShell to 16 unit cases and 12 system cases, matching the scale used by stronger official tasks while keeping setup entirely public and reproducible.
