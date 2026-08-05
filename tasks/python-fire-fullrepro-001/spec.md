# Python Fire Specification

=== Context Layer ===

## Product Overview

Python Fire turns a Python component into a command line interface. The component can be a function, class, object, module, dictionary, list, tuple, scalar value, or a nested graph containing those values. A command token stream selects members, indexes collections, calls functions, instantiates classes, applies Fire flags, and projects the final component to a return value plus command-line text.

The shared fact source is the Python component graph together with the command tokens. Function signatures, default values, annotations, object members, dictionary keys, sequence positions, properties, callable objects, class constructors, serializer callbacks, command names, and Fire flags are all observed through the programmatic `Fire` call, generated stdout/stderr, help text, trace text, completion scripts, and `python -m fire` module loading.

## Non-Goals

- Interactive REPL embedding is outside scope; no IPython shell state is required.
- Terminal color rendering details and full-screen formatting snapshots are outside scope.
- Full bash or fish completion script byte-for-byte contents are outside scope beyond stable public commands and options.
- Private helper functions, protected attributes, internal trace classes, and tests from the project repository are not required.
- Shell startup file modification, persistent completion installation, packaging metadata, performance, concurrency, and process supervision are not required.
- Network services, databases, remote files, Docker behavior, and operating-system-specific terminal integrations are outside scope.

## Scope

This specification covers `fire.Fire(component, command=..., name=..., serialize=...)`, public import behavior, command strings and token lists, positional and named arguments, literal value parsing, dict/list/tuple traversal, object member access, hyphen-to-underscore member selection, class instantiation, callable objects, varargs, separator behavior, result serialization, help and error guidance, trace output, bash and fish completion public properties, root component display, and `python -m fire` invocation for modules and files.

All covered behavior operates on local Python values and subprocesses started only to exercise documented module and file invocation. Inputs are Python components and command tokens. Outputs are the returned Python object, stdout text, stderr text, and process exit code.

=== Orientation Layer ===

## Representative Workflows

A dictionary can expose multiple functions and values:

```python
import fire

def double(value=0):
    return 2 * value

component = {"double": double, "data": {"numbers": (5, 8, 13)}}
assert fire.Fire(component, command=["double", "5"]) == 10
assert fire.Fire(component, command=["data", "numbers", "2"]) == 13
```

A class can be instantiated and then traversed in one command:

```python
import fire

class Widget:
    def __init__(self, name="seed", size=2):
        self.name = name
        self.size = size

    @property
    def high_score(self):
        return self.size * 10

    def greet(self, punctuation="!"):
        return self.name + punctuation

assert fire.Fire(Widget, command=["--name=Ada", "--size=3", "greet", "?"]) == "Ada?"
assert fire.Fire(Widget("ready", 4), command=["high-score"]) == 40
```

A separator forces evaluation before applying remaining tokens to the result:

```python
import fire

def display(arg1, arg2="!"):
    return arg1 + arg2

assert fire.Fire(display, command=["hello", "-", "upper"]) == "HELLO!"
assert fire.Fire(display, command=["-", "SEP", "upper", "--", "--separator", "SEP"]) == "-!"
```

=== Behavior Layer ===

## Fire Entry Point And Public Import Surface

The public package import exposes a callable `Fire` object through `import fire`, and `Fire` is listed in `fire.__all__`. Calling `Fire` with a component and no remaining command returns or displays the root component according to the same public display rules used after traversal.

When `command` is a string, Fire splits it into command tokens using shell-like tokenization. When `command` is a sequence, Fire consumes that sequence directly. The optional `name` argument controls the command name shown in help and error guidance. The optional `serialize` callable controls the stdout projection of the final returned value while leaving the returned Python object unchanged.

## Argument Parsing And Result Projection

Function and constructor arguments can be supplied positionally where supported or with flag syntax such as `--value=6`. Tokens representing Python literals are converted into matching runtime values when Fire parses command arguments. Integers, floats, booleans, `None`, lists, dictionaries, and strings must be delivered to user functions as their parsed Python values.

Scalar return values are printed to stdout followed by a newline, except `None`, which produces no stdout text. Lists are printed one item per line. Mappings are printed as key/value lines. Tuples are serialized as JSON lists. A custom serializer receives the converted final Python value and its return string becomes stdout with a trailing newline.

## Component Traversal

A dictionary command token selects the matching key, including keys containing spaces when supplied as one token. A sequence command token that is an integer string selects the corresponding list or tuple index. An object command token selects a public member or property. Hyphenated command tokens map to underscore member names, so `high-score` selects `high_score`.

When the selected component is a function, Fire invokes it with consumed arguments. When it is a class, Fire instantiates it using constructor flags, and remaining command tokens continue against the new object. When it is a callable object, flags are passed to its `__call__` method. Bound methods use the instance state that produced them.

## Command Evaluation And Separator Semantics

The default separator token is `-`. Tokens before the separator are used to evaluate the current function or class; tokens after the separator apply to the result. This supports traversing a returned object, indexing a returned list or dictionary, and calling public methods on a returned scalar. Passing `-- --separator VALUE` changes the separator for that command so the default hyphen can be used as a normal function argument.

Variable-argument functions consume all unseparated tokens. Adding a separator forces the varargs call and then applies later tokens to the resulting value.

## Flags, Help, Trace, Completion, And Errors

Fire flags are separated from command tokens by a standalone `--`. The `--help` flag exits successfully and writes usage information to stderr. Help for objects includes available values and commands. Help at the root component includes groups and commands.

The `--trace` flag exits successfully and writes stepwise execution information to stderr, including the initial component and accessed properties or commands. Trace mode does not also print the final value to stdout.

The `--completion bash` and `--completion fish` flags write completion scripts to stdout. The scripts must expose stable public command names and, for object members, the public command spellings generated by Fire, including hyphenated member spellings.

When a command token cannot be consumed, a key is missing, or an index is out of range, Fire exits with a nonzero code, writes no successful result to stdout, and writes public error guidance to stderr that includes a help command for the same component path.

## Module And File Invocation

`python -m fire` accepts either a Python module name or a Python file path followed by command tokens. It imports the module or file, exposes its public module contents as the component, applies the remaining tokens, and writes the same stdout/stderr and exit code projections as a direct Fire command.

=== Contract Layer ===

## Product State Model

The product state is a traversal over a Python component graph. Nodes can be functions, bound methods, classes, callable objects, dictionaries, sequences, scalars, properties, modules, and returned values. Edges are command tokens interpreted as key selection, sequence index selection, member access, function argument, constructor argument, callable argument, separator boundary, or Fire flag.

The final state includes the selected component, the consumed command path, any parsed argument values, the returned Python object, stdout text, stderr text, and exit code. Help, trace, completion, return value, and error guidance are separate public projections of the same traversal state.

## Error Semantics

| Condition | Required result |
|---|---|
| Missing dictionary key at current component | Nonzero exit and stderr guidance for detailed help |
| Out-of-range sequence index | Nonzero exit and stderr guidance for the same component path |
| Unknown object member or unconsumed token | Nonzero exit and stderr guidance containing the help path |
| Help flag on valid component | Successful exit and usage text on stderr |
| Trace flag on valid command | Successful exit and trace text on stderr, with no final-value stdout |
| `python -m fire` cannot expose requested command | Nonzero process result with stderr text |

Exact prose outside the stable public phrases and command names is not defined.

## Cross-View Invariants

1. Positional and named arguments for the same function parameter must produce the same return value and stdout projection.
2. Parsed command tokens must be reflected in both the returned Python value and the serialized stdout value.
3. Object help, completion, and member traversal must expose the same public command spellings.
4. Separator behavior must change only the boundary between argument consumption and result traversal.
5. Custom serialization must observe the same converted final value that `Fire` returns.
6. Error guidance must name a help path for the same component path that failed.
7. `python -m fire` module and file invocation must agree with direct Fire dispatch for the exposed module commands.
8. Root display, help, trace, and completion are projections of the same component graph rather than unrelated command inventories.

=== Reference Layer ===

## Installable Surface

### Public Import Surface

```python
import fire
from fire import Fire
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `fire.Fire` | function | Builds and executes a CLI traversal over a Python component. |
| `component` | argument | Root Python object exposed to command tokens. |
| `command` | argument | String or sequence of command tokens to consume. |
| `name` | argument | Public command name used in help and error guidance. |
| `serialize` | argument | Optional callable used to convert the final value to stdout text. |
| `python -m fire` | command | Exposes a module or file path without modifying that file. |

## Invocation Protocol

Install the target package and the listed local requirements, then run the public tests from the package root with pytest. The target package is not pre-installed; the runner supplies it through installation or `PYTHONPATH`. The tests assume normal stdout and stderr capture and may start a subprocess with the current Python executable for `python -m fire` coverage.

The same test suite is expected to run on Python 3.10 and Python 3.11. The public command-line subprocess tests inherit the environment needed to import the target package.

## Environment

Run on Linux with Python 3.11 on Linux without network access. Python 3.10 is also supported for compatibility replay. The target package is not pre-installed and must be supplied by the runner. Required packages are `pytest` and `termcolor<3.2.0`. No service credentials, network endpoints, databases, or Docker runtime are required.

## Evaluation Notes

The tests exercise public behavior through `import fire`, `fire.Fire(...)`, stdout/stderr capture, exit codes, and `python -m fire`. Assertions focus on stable public values, command names, selected help phrases, trace markers, and completion command exposure. Tests avoid private target modules, protected helpers, project repository test utilities, interactive shell embedding, service access, sleeps, and exact full help or completion snapshots.
