# Mini Xit Task CLI PRD

## Goal

Build `xitlite.py`, a local command-line task manager inspired by
`hoechstleistungshaartrockner/xitkit`. The program reads and writes `.xit` task
files, exposes stable JSON output, and keeps parsed task records, filters,
sorted views, stats, writeback, and cross-file movement mutually consistent.

The benchmark focuses on observable behavior. It does not require the original
xitkit package, Rich output, Click, internal classes, caches, or exact source
layout.

## Invocation

All commands are run as:

```console
python xitlite.py COMMAND [OPTIONS]
```

Paths are interpreted relative to the current working directory unless absolute.
All successful commands print one compact JSON value followed by a newline.
Failed commands exit non-zero and print a useful stderr message. Failed commands
must not modify any file.

## Task File Format

Only `.xit` files are in scope. A valid task starts at column 0 with exactly one
checkbox:

- `[ ]` -> `open`
- `[x]` -> `done`
- `[@]` -> `ongoing`
- `[~]` -> `obsolete`
- `[?]` -> `question`

The checkbox may be followed by end-of-line or by one space and task text.
Invalid checkboxes, indented checkboxes, missing separators, and non-task lines
are ignored by parsers and preserved when possible by writeback.

A task description may continue on following lines that start with exactly four
spaces. Continuation text is joined to the description with `\n` after removing
the four-space prefix. Other indentation is not a continuation.

## Extracted Fields

Every parsed task JSON object must include:

- `id`: integer, assigned from 1 in input file order, then line order.
- `file`: path string exactly as supplied to the command when possible.
- `line`: 1-based line number of the task checkbox.
- `status`: one of `open`, `done`, `ongoing`, `obsolete`, `question`.
- `description`: task text after removing the checkbox and recognized priority
  token, preserving due-date and tag text.
- `priority`: integer count of `!`, or `0` if absent.
- `due`: normalized `YYYY-MM-DD` string, or `null`.
- `tags`: object mapping tag names to string values or `null`.

Priority may appear immediately after the checkbox text separator. A priority
token is either one or more `!`, dots followed by one or more `!`, or one or
more `!` followed by dots, with no dots between exclamation marks and no dots on
both sides. For example, `!`, `..!!`, and `!!!...` are valid priority tokens.
Priority is the number of `!`; padding dots are not part of the description.
Tokens such as `.!.` or `!.!` are not priority.

Due dates are recognized anywhere in the description with prefix `-> ` and one
of these forms: `YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY-MM`, `YYYY/MM`, `YYYY`,
`YYYY-Www`, `YYYY/Www`, `YYYY-Qn`. Month, year, week, and quarter forms normalize
to the last day of that period. Week forms use ISO weeks and normalize to the
Sunday at the end of that ISO week. Mixed delimiters are not recognized.

Tags start with `#` followed by Unicode letters, digits, `_`, or `-`. Tags may
have values as `#name=value`, `#name="quoted value"`, or `#name='quoted value'`.
Missing values are `null`; empty quoted values are `""`.

When a command accepts a `TAG` argument, it accepts `name`, `name=value`, or
`name="quoted value"` without a leading `#`. The command must write tags back to
the task as `#name` for null values and `#name=value` for string values.

For commands that create or rewrite a complete task line, the canonical
writeback order is: checkbox status, optional priority token, description text,
optional due date, then optional tags. Priority `N` is written as `N`
exclamation marks. Due dates are written in normalized `YYYY-MM-DD` form. Tags
are written after the due date in the order supplied by the command.

## Commands

### `list`

```console
python xitlite.py list --file FILE [--file FILE ...]
  [--status STATUS] [--tag TAG ...] [--priority-min N]
  [--due-on DATE] [--due-by DATE]
  [--sort id|priority|due] [--order asc|desc]
```

Print a JSON array of task objects. Multiple `--file` arguments are read in the
given order. Multiple filters compose as intersection. `--tag TAG` matches tag
name regardless of value, and `--tag` may be repeated; repeated tag filters
compose as intersection. `--priority-min N` keeps tasks with priority at least
`N`. `--due-on` and `--due-by` use the same normalized date rules as parsing.

Default sort is `id asc`. Priority sort compares priority, due sort compares
normalized due date; ties are broken by `id asc`. Tasks without due dates sort
last for `due asc` and first for `due desc`.

### `stats`

```console
python xitlite.py stats --file FILE [--file FILE ...]
```

Print a JSON object:

```json
{"total": 0, "by_status": {}, "by_priority": {}, "by_file": {}, "with_tags": 0, "with_due": 0}
```

Counts reflect all parsed tasks from the supplied files, not only filtered
views. Object keys are strings.

### `add`

```console
python xitlite.py add --file FILE --text TEXT
  [--status STATUS] [--priority N] [--due DATE] [--tag TAG ...]
```

Append a task to `FILE`, creating the file if needed. Default status is `open`.
The written line must remain parseable by `list`. Print the newly parsed task.

### `mark`

```console
python xitlite.py mark --file FILE ID --status STATUS
```

Update the task status in place and preserve description, priority, due date,
tags, and continuation lines. Print the updated task.

### `tag` / `untag`

```console
python xitlite.py tag --file FILE ID TAG
python xitlite.py untag --file FILE ID TAG
```

Add or remove a tag on the selected task. Adding an existing tag replaces its
value. Removing a missing tag is a no-op success. Print the updated task.

### `reschedule`

```console
python xitlite.py reschedule --file FILE ID DATE
```

Replace any existing due date on the selected task, or append one if absent.
Print the updated task.

### `move`

```console
python xitlite.py move --from FILE --to FILE ID
```

Remove the selected task from the source file and append it to the target file,
creating the target if needed. Task text, status, priority, due date, tags, and
continuation lines must survive the move. Print the moved task as it appears in
the target file after the move.

## Error Behavior

These fail non-zero and modify no files: unsupported command, missing required
arguments, unsupported status, invalid date argument, missing source file for
read/update commands, unsupported file extension, and task ID not found.

## Non-Goals

No Markdown fenced-code parsing, recurrence, interactive prompts, pomodoro,
Rich styling, shell expansion, natural-language dates, real editor integration,
or exact xitkit internal architecture is required.
