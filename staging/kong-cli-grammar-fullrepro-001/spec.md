<!-- INTERNAL
task_id: kong-cli-grammar-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: README.md (tag DSL reference, hooks, resolvers, mappers,
  variable interpolation, help), godoc for package kong at v1.16.1, and
  78 black-box probe rounds against the pinned v1.16.1 checkout
  (0678fd30af8be8bae6dc9f9c6f143cc549450be2). No upstream test text was
  consulted for spec claims.
-->

# kong Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`kong` is a command-line parser for Go programs that derives a complete
command-line grammar — commands, sub-commands, flags, and positional
arguments — from the shape of a Go struct and its field tags. The caller
declares an application as nested struct fields; the library compiles that
declaration into a grammar model, parses `os.Args`-style token lists
against it, and binds parsed values back onto the caller's struct through
Go reflection.

One grammar model underlies every feature. The same node tree that drives
parsing also renders `--help` text, answers introspection queries, receives
values from environment variables and configuration resolvers, validates
required/enum/mutual-exclusion constraints, and dispatches execution to
`Run` methods declared on command structs with dependency-injected
arguments. The installable module path is `github.com/alecthomas/kong`.

## Non-Goals

- This specification does not require shell completion generation of any
  kind.
- This specification does not define a public token-stream manipulation
  API beyond the scanner operations named in Value Mapping; token typing
  internals and scanner construction helpers are implementation details.
- This specification does not require configuration-file formats other
  than JSON; additional formats plug in through the `ConfigurationLoader`
  abstraction.
- This specification does not define terminal-width detection; help output
  is rendered for a fixed default width and callers adjust wrapping through
  `HelpOptions.WrapUpperBound`.
- This specification does not require the `ChangeDirFlag`,
  `NamedFileContentFlag`, or automatic flag-grouping conveniences; the
  special flag types in scope are exactly those listed in the API Catalog.
- This specification does not define localisation; all diagnostics are
  English text with the exact shapes given in Error Semantics.

## Representative Workflows

**A file utility with two commands.** The grammar is declared as a struct;
each `cmd` field becomes a command, `arg` fields become positionals, and
remaining fields become flags. After a successful parse the selected
command is executed through `Run`, with extra dependencies injected by
type.

```go
type Globals struct {
    Debug bool `short:"d" help:"Enable debug output."`
}

type RmCmd struct {
    Force     bool     `short:"f" help:"Force removal."`
    Recursive bool     `short:"r" help:"Recurse into directories."`
    Paths     []string `arg:"" name:"path" help:"Paths to remove."`
}

func (r *RmCmd) Run(g *Globals) error {
    // remove r.Paths, honouring g.Debug ...
    return nil
}

type LsCmd struct {
    Paths []string `arg:"" optional:"" name:"path" help:"Paths to list."`
}

func (l *LsCmd) Run(g *Globals) error { return nil }

var cli struct {
    Globals
    Rm RmCmd `cmd:"" help:"Remove files."`
    Ls LsCmd `cmd:"" help:"List paths."`
}

parser, err := kong.New(&cli, kong.Name("shell"),
    kong.Description("A file utility."))
// err is nil for a well-formed grammar
ctx, err := parser.Parse([]string{"rm", "-rf", "a", "b"})
// ctx.Command() == "rm <path>"; cli.Rm.Force, cli.Rm.Recursive are true
err = ctx.Run(&cli.Globals) // invokes (*RmCmd).Run with the bound Globals
```

**A server binary resolved from flags, environment, and a JSON config
file.** Values flow into the same struct from four sources; the command
line always wins, resolvers beat environment variables, and environment
variables beat declared defaults.

```go
var cli struct {
    Port    int           `env:"PORT" default:"80" help:"Listen port."`
    Timeout time.Duration `default:"5s"`
    Name    string        `default:"${app_name}"`
}

resolver, err := kong.JSON(strings.NewReader(`{"port": 8080}`))
parser, err := kong.New(&cli,
    kong.Name("server"),
    kong.Vars{"app_name": "srv"},
    kong.Resolvers(resolver))
ctx, err := parser.Parse(nil)
// cli.Port == 8080 (resolver beats env and default)
// cli.Timeout == 5*time.Second, cli.Name == "srv"
_ = ctx
```

## Grammar Construction

`kong.New` compiles a caller-supplied struct into a grammar model before
any argument is inspected; every structural mistake is reported at this
stage rather than at parse time.

**Entry points.** `New` accepts a grammar and a variadic list of `Option`
values and returns a `*Kong` and an error. The grammar argument must be a
pointer to a struct; any other value makes `New` return an error of the
form `expected a pointer to a struct but got *int`. `Must` wraps `New` and
panics on error. The package-level `Parse` function builds a parser from
its options, parses `os.Args[1:]`, and on failure reports the error and
terminates through the configured exit function; programs that need to
handle errors themselves use `New` followed by the `Parse` method.

**Field classification.** WHEN the model is built, THEN each exported
struct field must map to exactly one grammar element: a field tagged
`cmd:""` becomes a command node, a field tagged `arg:""` becomes a
positional argument (or an argument branch, described below), and every
other exported field becomes a flag. Anonymous embedded structs are
flattened into their parent. A field of type `kong.Plugins` (a slice of
`any`) that is embedded anonymously contributes the flags of each element,
which must each be a pointer to a struct; their fields are flattened into
the parent node exactly as if declared inline.

**Naming.** The default flag name is the field name lower-cased with
hyphens at case boundaries (`SomeLongFlag` becomes `some-long-flag`,
`HTTPPort` becomes `http-port`). The `name` tag overrides the derived
name. The `FlagNamer` option replaces the derivation function for every
field that has no explicit `name` tag. Command and argument nodes are
named the same way. The `aliases` tag declares comma-separated alternate
names for a command or flag; an alias parses exactly like the primary name.

**Structure tags.** The `short:"c"` tag attaches a single-rune short form.
Declaring the same short rune on two flags of one node makes `New` fail
with a `duplicate short flag -x` error. The `hidden:""` tag keeps a flag or
command parseable but omits it from help. The `help:"..."` tag supplies
the one-line description shown in help output. The `group` tag assigns a
flag or command to a named display group. The `embed:""` tag flattens a
named struct field into its parent; combined with `prefix:"p-"` every
flag inside the embedded struct gains the name prefix, and with
`envprefix:"P_"` every environment-variable name declared inside gains
that prefix (an `env:"HOST"` field under `envprefix:"DB_"` reads
`DB_HOST`).

**Commands and argument branches.** Command fields nest arbitrarily: a
command with child commands is selectable only through a leaf. A field
tagged `arg:""` whose type is a struct declares a *branching positional*:
the struct must contain a value field with the same name as the branch to
receive the positional text, and its remaining `cmd`/`arg` fields continue
the grammar below it. If the same-named value field is missing, `New`
fails with an error of the form `positional branch must have at least one
child positional argument named "name"`.

**Positional ordering.** Within one node, required positionals must
precede optional ones; declaring a required positional after an optional
one makes `New` fail with an error of the form `required "b" cannot come
after optional "a"`.

**Dynamic commands and the automatic help flag.** The
`DynamicCommand(name, help, group, cmd, tags...)` option adds a command at
runtime whose grammar is compiled from `cmd` (a pointer to a struct)
exactly like a declared field. Every application receives a built-in
`--help` flag with short form `-h` and help text `Show context-sensitive
help.` unless the `NoDefaultHelp` option is given, in which case `--help`
is an unknown flag.

**Grammar-level validation at build time.** An `enum` tag on a value that
is neither `required` nor equipped with a valid `default` makes `New` fail
with an error containing `enum value is only valid if it is either
required or has a valid default value`. A `negatable` tag on a non-boolean
flag makes `New` fail with an error containing `negatable can only be set
on booleans`. A `default` or other tag value that interpolates an
undeclared variable makes `New` fail with an error of the form
`default value for --a="": undefined variable ${undeclared}`.

## Parsing and Binding

`Parse` consumes a `[]string` of arguments and binds values onto the
grammar struct, returning a `*Context` describing what was matched.

**Flag syntaxes.** A long flag accepts its value either attached
(`--flag=value`) or as the following token (`--flag value`). A short flag
accepts its value attached without separator (`-n5`) or as the following
token (`-n 7`); an `=` after a short flag is not a separator and becomes
part of the value, so `-n=5` fails for an integer flag with an error of
the form `--num: expected a valid 64 bit int but got "=5"`. Multiple short
boolean flags combine into one token (`-rf`), and the final short flag of
a combined token accepts a value (`-fn 7`).

**Boolean flags.** A boolean flag set by bare mention (`--flag`) becomes
true; an explicit value is accepted only in attached form (`--flag=false`).
A separate following token is not consumed as a boolean value: `--flag
true` sets the flag and then fails with `unexpected argument true` if no
positional can accept the token. A flag tagged `negatable:""` additionally
accepts `--no-<name>`, which sets the field to false; `negatable:"other"`
declares `--other` as the negated form instead. Parsing the negated form
must set the target field to false even when its default is true.

**Terminator and passthrough.** The token `--` ends flag parsing; every
later token is treated as a positional value even when it begins with a
hyphen. A trailing `[]string` positional tagged `passthrough:""` captures
every remaining token verbatim starting at the first positional token —
tokens that look like flags are not matched against the grammar once the
passthrough positional begins.

**Flag scope.** A flag declared on a node is recognised from the point the
node is entered onward: ancestor flags remain settable while parsing a
descendant command (`app sub --root-flag x` works), but a descendant's
flag given before the command that declares it is an unknown flag.

**Command selection.** Tokens that are not flags select child commands by
name or alias, descend through argument branches, and fill positionals in
declaration order. Parsing must end on a leaf: WHEN arguments run out at a
node with children, THEN `Parse` returns an error naming the expected
children — `expected "sub"` for one child, `expected one of "child",
"other"` for several. `Context.Command()` returns the space-joined path of
the selection with positional placeholders, for example `rm <path>` or
`parent child`.

**Default commands.** A command tagged `default:"1"` is selected when no
command token is present. A command tagged `default:"withargs"` is
additionally allowed to consume leading positional tokens, so `app
freearg` parses as that command's positional rather than an unknown
command.

**Collections and counters.** A slice flag accumulates: each occurrence
appends, and each value is additionally split on the separator given by
the `sep` tag (default `,`), so `--nums 1,2 --nums 3` yields three
elements. A map flag parses `key=value` pairs split on the `mapsep` tag
separator (default `;`), so `--m x=1;y=2` yields two entries. A flag
tagged `type:"counter"` increments its numeric field once per occurrence
(`-vvv` yields 3) and takes no value. A pointer field is allocated when
its flag is set. Escaped separators are honoured: `SplitEscaped` splits a
string on an unescaped separator rune while `\,` sequences protect the
separator, and `JoinEscaped` is its inverse.

**Positional completion.** WHEN required positionals remain unfilled at
the end of parsing, THEN `Parse` returns an error naming the first missing
one in angle brackets, of the form `expected "<b>"`. WHEN a token arrives
after every positional is filled and no command matches it, THEN
`Parse` returns `unexpected argument three` (naming the token). An
optional positional with a `default` tag receives the default when
absent.

## Value Mapping

Every flag and positional is decoded by a mapper selected from the value's
Go type, its `type` tag, or caller-registered mappers.

**Built-in decoding.** String, integer (including sized and unsigned
variants), float, and boolean fields decode from their literal text forms.
A `time.Duration` field accepts Go duration syntax (`2m30s`); a malformed
duration fails with an error containing `expected duration but got
"bogus"`. A `time.Time` field decodes RFC 3339 text by default; a
`format:"..."` tag supplies a Go reference-layout to use instead, and text
that does not match the layout produces the underlying time-parse error. A
malformed integer fails with an error of the form `--num: expected a valid
64 bit int but got "abc"`; a malformed float fails with `--f: expected a
float but got "abc" (string)`.

**Special types and type tags.** A field tagged `type:"path"` expands a
leading `~` to the user's home directory and makes the value absolute; the
package-level `ExpandPath` function performs the same expansion. A field
of type `kong.FileContentFlag` reads the file named by the value and
stores its bytes. A field of type `kong.ConfigFlag` loads the named file
through the loader installed by the `Configuration` option and appends the
result to the resolver chain for the remainder of the parse. A field of
type `kong.VersionFlag`, when set, prints the value of the `version`
variable to stdout and terminates with exit status 0.

**Custom mappers.** The `Mapper` interface has a single method `Decode`
taking a `*DecodeContext` and a `reflect.Value` target. `MapperFunc`
adapts a function to the interface. `NamedMapper(name, mapper)` registers
a mapper selected by `type:"name"` tags; `TypeMapper(reflectType, mapper)`
attaches a mapper to every value of a Go type. `DecodeContext` exposes the
`Value` being decoded and `Scan`, the token scanner; a mapper consumes its
input by calling `PopValue(context)` for a token or `PopValueInto(context,
&target)` to decode a token into a Go value. A hyphen-prefixed token (such
as a negative number) following any flag is scanned as a flag rather than
consumed as the detached value; the resulting error suggests the attached
form, e.g. `--num: expected int value but got "-5" (short flag); perhaps
try --num="-5"?` — the attached form `--num=-5` decodes normally.

**Enums.** A value with an `enum:"a,b,c"` tag accepts exactly the listed
alternatives. A flag violation fails with `--enum must be one of "a","b",
"c" but got "z"`; a positional violation names the placeholder instead:
`<mode> must be one of "fast","slow" but got "wrong"`. Enum lists are
interpolable: an `enum:"${opts}"` tag draws its alternatives from the
variable table.

## Defaults, Environment Variables and Resolvers

Unset values are filled from three layered sources before validation runs.

**Precedence.** WHEN a value is provided on the command line, THEN that
value wins unconditionally. Otherwise resolvers are consulted (later
resolvers are consulted for every flag, and a resolver value beats the
environment); otherwise declared environment variables are read; otherwise
the `default` tag applies. A `required` flag satisfied by a resolver or
environment variable does not produce a missing-flag error.

**Defaults.** The `default:"text"` tag supplies the value parsed through
the field's mapper when nothing else sets it. The package-level
`ApplyDefaults(target, options...)` function applies defaults and
validates a struct without parsing any arguments.

**Environment variables.** The `env:"NAME"` tag binds a flag to an
environment variable; a comma-separated list (`env:"A,B"`) reads the first
variable that is set. The `DefaultEnvars(prefix)` option derives an
environment variable for every flag that lacks an `env` tag, upper-snake
casing the flag name under the prefix (flag `some-flag` with prefix
`MYAPP` reads `MYAPP_SOME_FLAG`). Environment bindings are annotated in
help output as `($NAME)` after the flag description.

**Variable interpolation.** Tag text of the form `${name}` is replaced
from the variable table at build time; `${name=fallback}` substitutes the
fallback when the variable is undeclared. Variables are declared with the
`Vars` option (a `map[string]string`); interpolation applies to `default`,
`help`, and `enum` tag text. `HasInterpolatedVar(s, v)` reports whether
`s` references variable `v`.

**Resolvers.** A `Resolver` supplies values by flag: its `Resolve` method
receives the context, the parent path, and the flag, and returns a value
or nil; its `Validate` method receives the `*Application` model and
reports configuration errors. `ResolverFunc` adapts a plain function into
a non-validating resolver. The `Resolvers(...)` option appends resolvers;
`ClearResolvers()` removes previously installed resolvers (declared
environment variables are not resolvers and are unaffected).
`Context.AddResolver` appends a resolver during a parse.

**JSON configuration.** `JSON(reader)` builds a resolver from a JSON
object. A flag looks up its value by name with hyphens replaced by
underscores, then by the snake_case variant, then by the camelCase
variant; a flag name containing dots walks nested objects. The
`Configuration(loader, paths...)` option installs a `ConfigurationLoader`
(`JSON` itself is one) and loads each existing path at build time;
`Kong.LoadConfig(path)` loads one file through the installed loader.

## Validation and Flag Groups

Constraint checking runs after values are bound and resolved.

**Required and missing values.** WHEN a required flag remains unset, THEN
parsing fails with `missing flags: ` followed by the flag rendered with
its placeholder (`--req=STRING`). Multiple missing flags are joined with
commas.

**Exclusive and inclusive groups.** Flags sharing an `xor:"group"` tag are
mutually exclusive: setting two fails with `--a and --b can't be used
together` (naming the first offending pair). Flags sharing an `and:"group"`
tag must be set together: setting a strict subset fails with `--u and --p
must be used together`. WHEN every flag of a required `xor` group is
absent, THEN parsing fails with `missing flags: ` naming the alternatives
joined by ` or ` (`missing flags: --a or --b`).

**Unknown input.** An unrecognised long flag fails with `unknown flag
--unknown`. WHEN an unknown flag or command is within small edit distance
of a declared name, THEN the error appends a suggestion: `unknown flag
--verbse, did you mean "--verbose"?` or `unexpected argument sib, did you
mean "sub"?`.

## Hooks, Bindings and Command Execution

Parsed grammars execute through `Run` methods discovered on command
structs, with arguments supplied by a type-indexed binding set.

**Lifecycle hooks.** A field type (value or pointer receiver) that
implements `BeforeReset`, `BeforeResolve`, `BeforeApply`, or `AfterApply`
has that method invoked during `Parse` in exactly that order: reset hooks
before defaults are applied, resolve hooks before resolvers run, apply
hooks before command-line values are bound, and after-apply hooks after
binding and validation. A hook returning a non-nil error aborts the parse
with that error. Hook methods accept bound dependencies as parameters
under the same rules as `Run` methods. A type implementing `AfterRun` has
that method invoked after `Context.Run` completes.

**Run dispatch.** `Context.Run(binds...)` locates the selected leaf node
and invokes every `Run` method found walking from the leaf toward the
root, leaf first; a parent command's `Run` therefore executes after its
child's. WHEN no node in the hierarchy declares a `Run` method, THEN `Run`
returns an error of the form `no Run() method found in hierarchy of cmd`.
WHEN no command was selected and the application root declares no `Run`
method, THEN `Run` returns `no command selected`.

**Bindings.** Values passed to `Run` are matched to `Run`-method
parameters by exact type. The parse `*Context` is always bound, and each
node's struct pointer along the selected path is bound, so a child's `Run`
receives its parent command struct on request. The `Bind(values...)`
option adds bindings at construction; `BindTo(impl, ifacePtr)` binds an
implementation to an interface type named by a nil interface pointer;
`BindToProvider(fn)` registers a provider function whose return value is
bound lazily by its return type. WHEN a parameter has no binding, THEN
`Run` fails with an error of the form `couldn't find binding of type
*main.depT for parameter 0 of func(*main.depT) error(), use
kong.Bind(*main.depT)`.

**Errors from commands.** An error returned by a `Run` method propagates
out of `Context.Run` unchanged. `Kong.FatalIfErrorf(err)` prints `app:
error: <message>` to stderr and terminates with the error's `ExitCode()`
when the error implements `ExitCoder`, and with exit status 1 otherwise.

## Help Rendering and Diagnostics

The help system renders the grammar model; everything shown is derived
from the same nodes that drive parsing.

**Default layout.** `--help` prints to stdout and terminates with exit
status 0. The first line is `Usage: ` followed by the full command path
with required flags rendered inline (`--req=STRING`), positional
placeholders — required positionals in angle brackets (`<arg>`), optional
ones in square brackets (`[<arg>]`) — and a trailing `[flags]` marker when
at least one non-help, non-required flag is visible. The
application description (from the `Description` option) follows as a
paragraph. A `Flags:` section lists each visible flag with aligned
columns: short form (`-h, `) when present, long form with a value
placeholder (`--level=2` uses the default as placeholder when one exists,
otherwise an upper-cased type placeholder such as `--req=STRING`), and the
help text with environment annotation (`($LEVEL)`). Slice flags render the
placeholder with a trailing `,...`; map flags render `KEY=VALUE;...`; the
`placeholder` tag overrides the rendered placeholder. A `Commands:`
section lists each visible command as its summary (`sub <thing> [flags]`)
with its help below, and the output ends with the footer line
`Run "app <command> --help" for more information on a command.` when
commands exist.

**Context-sensitive help.** `app sub --help` renders the usage line for
`sub`, an `Arguments:` section for its positionals, and the flags of `sub`
and every ancestor, grouped per node and separated by blank lines. A
command type implementing the `Help() string` method has that text
appended as detail below its summary help in its own help screen.

**Groups, aliases, and hiding.** Flags with a `group` tag are listed under
the group's title heading after ungrouped flags; command groups declared
via `ExplicitGroups` render their `Title` and `Description` above the
member commands. Hidden flags and commands never appear. In compact mode
command aliases render in parentheses after the name (`sub (s,su)`).

**Alternate layouts.** `ConfigureHelp(HelpOptions{...})` adjusts
rendering: `Compact: true` merges each flag onto a single line without
blank separation; `Tree: true` renders the command hierarchy as an
indented tree (children indented beneath parents, no per-command usage
summaries); `FlagsLast: true` moves the flag listing after the command
listing; `NoExpandSubcommands: true` collapses nested commands;
`NoAppSummary: true` suppresses the `Usage:` line; `Summary: true` renders
a one-line summary form; `Indenter` selects the tree indentation function
from `SpaceIndenter`, `LineIndenter`, and `TreeIndenter`;
`WrapUpperBound` clamps the wrap width. The `Help(printer)` and
`ShortHelp(printer)` options replace the full and summary help printers;
the defaults are exported as `DefaultHelpPrinter` and
`DefaultShortHelpPrinter`, and `DefaultHelpValueFormatter` formats a
value's help text.

**Usage on error.** With the `UsageOnError()` option,
`Kong.FatalIfErrorf` prints the full help to stdout before the `app:
error: <message>` line on stderr; with `ShortUsageOnError()` it prints the
one-line usage summary instead. A parse error terminates with exit status
80; `Context.PrintUsage(summary)` renders the same usage text on demand —
the summary form appends the footer `Run "app sub --help" for more
information.`.

**Message helpers.** `Kong.Printf` writes `app: ` followed by the
formatted message to stdout; `Kong.Errorf` writes `app: error: ` followed
by the message to stderr and returns the parser; `Kong.Fatalf` does the
same and terminates with exit status 1. The application name comes from
the `Name` option; the `Writers(stdout, stderr)` option redirects both
streams and the `Exit` option replaces the termination function used by
help, version, and fatal paths.

## Model Introspection and the Parse Context

The compiled grammar and each parse result are public, queryable values.

**The model.** `Kong.Model` is a `*Application` wrapping the root `*Node`.
Every `Node` carries `Type` (one of the `NodeType` constants
`ApplicationNode`, `CommandNode`, `ArgumentNode`), `Name`, `Help`,
`Hidden`, `Aliases`, `Parent`, `Children`, `Flags`, `Positional`,
`DefaultCmd`, `Tag`, and `Argument` (the value of an argument branch).
Node queries: `Summary()` renders the node with placeholders and a
`[flags]` marker (`sub <arg> [flags]`); `Path()` renders the command path
below the application (`sub`); `FullPath()` prepends the application name
(`app sub`); `Depth()` counts command ancestors below the application
root, so a first-level command reports 0; `Leaf()` reports whether the
node has no child commands. A `Flag` embeds a `*Value` and adds
`Short`, `PlaceHolder`, `Envs`, `Aliases`, `Group`, `Xor`, `And`,
`Hidden`, and `Negated`. A `Value` carries `Name`, `Help`, `Default`,
`HasDefault`, `Enum`, `Required`, `Set` (whether any source set it),
`Position`, `Tag`, and `Target`. The built-in help flag appears first in
the root node's flag list.

**The context.** `Parse` returns a `*Context` even on error (embedded in
the returned `*ParseError`). The context exposes `Args` (the original
argument list), `Path` (the trace of matched nodes, flags, and
positionals), `Command()`, `Selected()` (the selected command node, nil
when none), `Flags()` (every flag visible on the selected path),
`FlagValue(flag)` (the bound value of one flag), `Value(path)` (the
reflected value at a path element), and `Empty()` (true when the parse
consumed no user-supplied flag or positional). `Model` is reachable
through the embedded `*Kong`.

**Staged parsing.** `Trace(k, args)` runs grammar matching only — no
values are bound, no hooks fire — and returns a context whose `Error`
field records any trace failure. `Context.Resolve()` applies resolvers,
`Context.Apply()` binds traced values onto the target struct and returns
the command string, and `Context.Validate()` runs constraint checks.
`Kong.Parse` is equivalent to trace, resolve, apply, validate, and hook
execution in order.

## State Model

The engine's single fact source is the grammar model: a tree of `Node`
values (application root, command nodes, argument branches) each owning
`Flag` and positional `Value` lists, compiled once by `New` from the
grammar struct and its tags plus construction options.

Public projections of that one tree:

1. **Parse results** — argv token lists bound onto the caller's struct,
   with a `*Context` trace (`Command()`, `Selected()`, `Path`).
2. **Help text** — full, compact, tree, and summary renderings, plus
   usage-on-error output.
3. **Introspection** — direct traversal of `Kong.Model` nodes, flags, and
   values, including summaries and paths.
4. **Value resolution** — defaults, environment variables, and resolver
   chains feeding the same `Value` objects the parser binds.
5. **Execution** — `Run`/hook dispatch over the selected path with
   type-indexed bindings.

A change to the grammar (a tag, a name, an option) must be observable
consistently in every projection.

## Error Semantics

| Condition | Result |
|---|---|
| Grammar is not a pointer to struct | `New` error `expected a pointer to a struct but got *int` |
| Enum without required or default | `New` error containing `enum value is only valid if it is either required or has a valid default value` |
| Duplicate short flag | `New` error containing `duplicate short flag -x` |
| `negatable` on non-bool | `New` error containing `negatable can only be set on booleans` |
| Undefined `${var}` in tag | `New` error of the form `default value for --a="": undefined variable ${undeclared}` |
| Required positional after optional | `New` error containing `required "b" cannot come after optional "a"` |
| Argument branch without same-named child | `New` error containing `positional branch must have at least one child positional argument named "name"` |
| Unknown flag | parse error `unknown flag --unknown`, with `, did you mean "--verbose"?` appended when a near match exists |
| Unknown/extra positional token | parse error `unexpected argument bogus`, with a `did you mean` suggestion when a command is near |
| Required flag unset | parse error `missing flags: --req=STRING` |
| Required xor group unset | parse error `missing flags: --a or --b` |
| Two xor flags set | parse error `--a and --b can't be used together` |
| Partial and group set | parse error `--u and --p must be used together` |
| Non-leaf command | parse error `expected "sub"` or `expected one of "child", "other"` |
| Missing required positional | parse error `expected "<b>"` |
| Enum violation (flag) | parse error `--enum must be one of "a","b","c" but got "z"` |
| Enum violation (positional) | parse error `<mode> must be one of "fast","slow" but got "wrong"` |
| Malformed int / float / duration | parse error naming the flag, expected type, and offending text (shapes in Value Mapping) |
| Bool flag given a detached value | parse error `unexpected argument true` |
| Hyphen-prefixed detached value (e.g. negative number) | parse error suggesting the attached form (`perhaps try --num="-5"?`) |
| Run with no method in hierarchy | `no Run() method found in hierarchy of cmd` |
| Run with no selection | `no command selected` |
| Missing binding for Run parameter | error naming the type, position, signature, and `use kong.Bind(...)` remedy |
| Any parse failure | returned as `*ParseError` wrapping the cause, `Context` attached, `ExitCode()` 80 |

## Cross-View Invariants

1. **Help lists exactly the parseable surface.** Every non-hidden flag
   reachable at a node must appear in that node's help with the same long
   name, short form, and placeholder that the parser accepts, and every
   hidden flag must parse successfully while absent from help.
2. **`Command()` agrees with the model.** For any successful parse, the
   string returned by `Context.Command()` must equal the selected node's
   path with the same positional placeholders that `Node.Summary()`
   renders for that node (up to the `[flags]` marker and defaulted
   segments).
3. **Model flags and context flags coincide.** `Context.Flags()` after a
   successful parse must enumerate the same flags reachable by walking
   `Kong.Model` along the selected path, and `Context.FlagValue` for each
   must equal the value bound onto the grammar struct.
4. **Precedence is total and observable.** For any flag with a default,
   an environment binding, and a resolver value, the bound result must
   follow command line > resolver > environment > default, and the same
   winner must be reported through `Value.Set` and the bound struct field.
5. **Staged parsing equals one-shot parsing.** `Trace` followed by
   `Resolve`, `Apply`, and `Validate` must leave the grammar struct and
   the context in the same state as a single `Parse` call over the same
   arguments, including identical error outcomes at the corresponding
   stages.
6. **Build-time rejection is total.** A grammar that violates any
   construction rule must fail at `New` with the documented error and
   never produce a `*Kong`; a grammar accepted by `New` must never fail
   parse-time on structural grounds (only on input).
7. **Interpolation is uniform.** A `${var}` reference must produce the
   same substituted text in a default value, its help rendering, and an
   enum constraint, for the same `Vars` table.
8. **Errors name flags as help renders them.** Flag names inside
   missing-flag, enum, and group error messages must use the same `--name`
   (and placeholder) rendering that appears in help output.

## Public Interface

### Import Surface

```go
import "github.com/alecthomas/kong"
```

Exported names in scope: `New`, `Must`, `Parse`, `Trace`, `ApplyDefaults`,
`ExpandPath`, `SplitEscaped`, `JoinEscaped`, `HasInterpolatedVar`, `JSON`,
`DefaultHelpPrinter`, `DefaultShortHelpPrinter`,
`DefaultHelpValueFormatter`, `SpaceIndenter`, `LineIndenter`,
`TreeIndenter`; types `Kong`, `Context`, `ParseError`, `ExitCoder`,
`Application`, `Node`, `NodeType` (`ApplicationNode`, `CommandNode`,
`ArgumentNode`), `Flag`, `Value`, `Positional`, `Group`, `Groups`, `Path`,
`Tag`, `Vars`, `Plugins`, `Resolver`, `ResolverFunc`,
`ConfigurationLoader`, `Mapper`, `MapperFunc`, `DecodeContext`, `Scanner`,
`BoolMapper`, `Option`, `OptionFunc`, `HelpOptions`, `HelpPrinter`,
`HelpValueFormatter`, `HelpIndenter`, `VersionFlag`, `ConfigFlag`,
`FileContentFlag`, `BeforeReset`, `BeforeResolve`, `BeforeApply`,
`AfterApply`, `AfterRun`; options `Name`, `Description`, `Vars` (as
option), `Exit`, `Writers`, `Bind`, `BindTo`, `BindToProvider`,
`Resolvers`, `ClearResolvers`, `Configuration`, `ConfigureHelp`, `Help`,
`ShortHelp`, `NamedMapper`, `TypeMapper`, `FlagNamer`, `DefaultEnvars`,
`NoDefaultHelp`, `UsageOnError`, `ShortUsageOnError`, `ExplicitGroups`,
`DynamicCommand`.

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `New` | function | Compile a grammar struct and options into a parser |
| `Must` | function | `New` that panics on grammar error |
| `Parse` | function | Convenience: build, parse `os.Args[1:]`, exit on error |
| `Trace` | function | Match arguments against the grammar without binding |
| `ApplyDefaults` | function | Apply tag defaults to a struct without parsing |
| `ExpandPath` | function | Expand `~` and relative paths to absolute |
| `SplitEscaped` / `JoinEscaped` | functions | Separator splitting/joining with backslash escapes |
| `HasInterpolatedVar` | function | Report whether text references a `${var}` |
| `JSON` | function | Build a `Resolver` from a JSON object stream |
| `Kong` | struct | The compiled parser: `Model`, `Exit`, `Stdout`, `Stderr`, `Parse`, `LoadConfig`, `Printf`, `Errorf`, `Fatalf`, `FatalIfErrorf` |
| `Context` | struct | One parse: trace, queries, staged operations, `Run` |
| `ParseError` | struct | Parse failure with `Context`, `Unwrap`, `ExitCode` |
| `ExitCoder` | interface | Error that carries its own exit status |
| `Application` / `Node` | structs | Grammar model root and tree nodes |
| `NodeType` | constants | `ApplicationNode`, `CommandNode`, `ArgumentNode` |
| `Flag` / `Value` / `Positional` | structs | Model of one flag or positional value |
| `Group` / `Groups` | struct/map | Display grouping metadata |
| `Path` | struct | One step of a parse trace |
| `Tag` | struct | Parsed field tag data attached to model values |
| `Vars` | map | Interpolation variable table (also an `Option`) |
| `Plugins` | slice | Anonymous-embeddable extension flag sets |
| `Resolver` / `ResolverFunc` | interface/func | External value sources consulted per flag |
| `ConfigurationLoader` | func type | Reader-to-resolver factory for config files |
| `Mapper` / `MapperFunc` | interface/func | Text-to-value decoding extension point |
| `DecodeContext` | struct | Mapper input: target `Value` plus token `Scan` |
| `Scanner` | struct | Token stream consumed by mappers (`PopValue`, `PopValueInto`) |
| `BoolMapper` | interface | Marks a mapper's values as boolean-like |
| `Option` / `OptionFunc` | interface/func | Parser construction options |
| `HelpOptions` | struct | Help layout switches (`Compact`, `Tree`, ...) |
| `HelpPrinter` / `HelpValueFormatter` / `HelpIndenter` | func types | Help rendering extension points |
| `DefaultHelpPrinter` / `DefaultShortHelpPrinter` | functions | The built-in full and summary help renderers |
| `DefaultHelpValueFormatter` | function | The built-in flag help formatter |
| `SpaceIndenter` / `LineIndenter` / `TreeIndenter` | functions | Tree-mode indentation styles |
| `VersionFlag` | bool type | Prints `${version}` and exits 0 when set |
| `ConfigFlag` | string type | Loads a config file into the resolver chain |
| `FileContentFlag` | byte-slice type | Reads the named file's contents |
| `BeforeReset` / `BeforeResolve` / `BeforeApply` / `AfterApply` / `AfterRun` | interfaces | Lifecycle hook contracts |

### CLI Entry Points

There is no console script for this package. It is a library that
programs embed to build their own command-line interfaces; programmatic
use is through Go imports.

## Appendix A: Environment

The working environment runs Go 1.22 or newer on Linux without network
access beyond the Go module proxy. The delivery must be a Go module with
module path `github.com/alecthomas/kong` so that callers import it as
shown in this document. No third-party runtime dependencies are required;
the standard library suffices.

## Appendix B: Assessment Notes

Correctness is exercised through compiled Go test programs that import the
module by its public path. Tests are grouped in two suites: one asserts
single behaviors in isolation (a tag's effect, one error's text and type,
one help fragment, one precedence rule), the other drives multi-step
workflows spanning several projections (grammar construction, parsing,
help rendering, model introspection, resolution, and execution together)
and checks the cross-view invariants above. Expected values in tests come
from this document's stated behavior; error-message assertions use the
exact shapes given in Error Semantics. Grammar structs used by tests are
self-contained in the test code — no fixture files beyond temporary
directories created by the tests themselves.
