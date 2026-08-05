# Cement Public Application Specification

## Product Overview

Cement is a Python application framework for local command-line applications. An application declaration combines a label, lifecycle settings, configuration defaults and files, argument parsing, controllers, handlers, interfaces, hooks, output, templates, extensions, and plugins. One declaration is projected into application state, parsed command state, controller results, rendered output, registered handler classes, configuration mappings, and locally generated files.

## Scope

This specification covers the documented public `App` and `TestApp` lifecycle, explicit argv handling, configuration defaults and local INI file merging, controller and subcommand dispatch, handler and interface registration, weighted hooks, output rendering, JSON and print extensions, local plugin loading, bootstrap modules, and deterministic template rendering and copying.

Applications use local Python classes and temporary files. The supported route includes:

- `App`, `TestApp`, `Controller`, and `ex` declarations.
- Setup, run, close, reload, context-manager behavior, label, argv, debug, quiet, parsed arguments, and last-rendered state.
- Configuration sections, defaults, local files, merge precedence, section inspection, and explicit late parsing.
- Public interface and handler managers, fallback resolution, class or label resolution, replacement with `force`, and handler setup.
- Built-in lifecycle hook namespaces, custom hook namespaces, weighted callback order, generator results, and render transformations.
- Controller commands, command aliases, nested controllers, embedded controllers, command arguments, and returned values.
- Output handler selection, JSON structured rendering, print rendering, render-handler overrides, file-like output, and last-rendered data.
- Short and fully qualified extension names, extension-created handlers, config-selected extensions, and application extensions.
- Local plugin directories, config-enabled plugins, plugin-created application members, and plugin-created controllers.
- Local bootstrap modules and a public template handler used for deterministic placeholder rendering, file loading, directory copying, exclusion, ignoring, and force replacement.

## Public Import Surface

The public interface includes `App`, `TestApp`, `Controller`, `Handler`,
`Interface`, and `ex` from `cement`. It also includes the documented public
classes `OutputHandler`, `TemplateHandler`, `FrameworkError`, and
`InterfaceError`; the two exception classes are importable from
`cement.core.exc`. Built-in extension behavior is reached through application
extension names such as `json` and `print`.

The application may define ordinary subclasses of the public interface, handler, controller, output, and template classes. Temporary plugin and bootstrap modules expose only a `load(app)` function and use public application methods.

## Product State Model

An application begins with a declared label, argv list, handler and interface declarations, extension names, configuration sources, controller classes, hooks, and template locations. Setup defines core interfaces and hooks, registers handlers, loads extensions, parses configuration, resolves selected handlers, loads plugins, prepares arguments, and prepares controllers.

Run executes the pre-run lifecycle, parses argv through the configured argument handler, dispatches the selected controller command, and executes the post-run lifecycle. Commands may return structured Python values or call `app.render`. Rendering applies pre-render hooks, selects an output handler, produces text, applies post-render hooks, optionally writes to a file-like object, and records the last data/text pair. Close executes close hooks and releases application extensions. Reload reconstructs the core managers and performs setup again.

Configuration is a mapping of sections to string values for the default INI handler. Defaults are merged before local files, and later files in a configured directory are processed in sorted order. An application-specific configuration section may differ from the application label and still control extensions and output selection.

## Error Semantics

| Condition | Required result |
| --- | --- |
| Application has no valid label | Raise `FrameworkError`. |
| Handler manager receives an unknown interface | Raise `InterfaceError`. |
| A missing handler label is requested without a fallback | Raise `InterfaceError`. |
| A missing local plugin cannot be found in configured sources | Raise `FrameworkError`. |
| A missing template cannot be loaded | Raise `FrameworkError`. |
| A template destination already exists without force | Raise `AssertionError`. |
| An unknown custom hook is registered | Return `False` without adding a callback. |
| A handler of an incompatible interface is registered | Raise the public framework interface error. |

Exact exception message prose is not part of this specification. The tests check public exception types and structured public results.

## Cross-View Invariants

1. The explicit application label and argv are available through the public application properties used by setup and parsing.
2. Configuration values exposed through `config.get`, section dictionaries, and application-selected handler behavior agree after the same defaults and local files are applied.
3. Interface definitions and handler registrations are visible through manager queries and yield the same handler behavior when resolved by label, class, or instance.
4. Hook callbacks execute in ascending weight order, and render hooks transform the data or text observed by the next rendering stage.
5. A controller command selected by argv receives its declared arguments and returns the same structured value when dispatched through the application.
6. Nested and embedded controller declarations select different command namespaces while preserving their declared command results.
7. A selected output handler determines the structured or text projection, and the last-rendered record contains the data and text from that rendering operation.
8. A short extension name and its fully qualified name identify the same loaded extension without duplicate registration.
9. Plugins and bootstrap modules change the same application instance that later controller dispatch observes.
10. Template rendering applies the same placeholder data to file content, directory names, and file names, while exclude, ignore, and force options control local generation.

## Representative Workflows

A local application can combine a configuration file, a JSON extension, a controller, a render hook, and a command:

```python
from cement import Controller, TestApp, ex

class Base(Controller):
    class Meta:
        label = "base"

    @ex(arguments=[(["--name"], {"default": "local"})])
    def report(self):
        return self.app.render({"name": self.app.pargs.name}, out=None)

with TestApp(
    label="demo",
    handlers=[Base],
    extensions=["json"],
    output_handler="json",
    argv=["report", "--name", "Nia"],
    catch_signals=[],
) as app:
    result = app.run()
```

The result is JSON representing the command data. A pre-render hook may add a field before JSON encoding, and `app.last_rendered` records the same transformed mapping and encoded text.

A local template handler can load a template directory and copy it to a temporary destination. Placeholder values affect both names and contents; excluded files are copied without rendering, ignored files are omitted, and `force=True` permits replacement of an existing destination file.

## Non-Goals

Redis, Memcached, SMTP, Mailpit, Docker, devbox, service daemons, network access, remote resources, private Cement modules, upstream source tests, sleeps, timing behavior, host-specific directories, environment-dependent configuration, exact help transcripts, and whole-output snapshots are outside this specification. The generate extension's optional YAML and interactive prompting route is excluded; deterministic local generation is covered through the public template handler contract.

## Invocation Protocol

Install or expose the fixed Cement source checkout as the target import root, import the public classes listed above, define local application classes, and invoke setup, run, rendering, configuration, handler, hook, extension, plugin, bootstrap, or template methods. Inputs are local Python values, argv lists, temporary files, and temporary modules. No external process or service is required.

## Environment

The reference environment is Linux with Python 3.11 and without network access. Python 3.10 is also used for an independent local replay. The target package is not pre-installed; tests add the selected source root explicitly. `pytest` and `pytest-json-report` are preinstalled and importable. The test package does not require optional Cement service dependencies.

## Evaluation Notes

The public cases are split into atomic behaviors and integrations. Integrations use only local classes, temporary files, and public application routes, and their dependency markers name atomic behaviors only. Assertions use structured mappings, public class metadata, return values, selected file contents, and bounded text fragments rather than private state or whole-output snapshots.

The package records local replay evidence for Python 3.10 and Python 3.11 plus an empty-dummy replay. Those records describe reproducibility of this package in the local same-process runner; they do not establish a trusted evaluator, strict isolation, network isolation, signatures, qualification, or delivery status.
