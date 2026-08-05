# Asciimatics Screen-Independent Widget Workflows

## Product Overview

Asciimatics provides public building blocks for terminal user interfaces and
ASCII animation. This package covers deterministic state and projection
surfaces that can be exercised without opening a terminal.

## Scope

The covered surface includes keyboard and mouse event values, scenes and
effect lifecycle, recorded paths, dynamic paths, static renderers, Sprite,
Print, Wipe, Scroll, Background, Canvas, and common widgets. Widget checks use
a small local screen recorder and inspect public values, callbacks, layout
focus, canvas transfers, and effect call traces.

## Public Import Surface

The checks import `asciimatics`, `asciimatics.event`, `asciimatics.scene`,
`asciimatics.paths`, `asciimatics.effects`, `asciimatics.renderers`,
`asciimatics.screen`, and `asciimatics.widgets`. The tested names are public
classes and constants from those modules, including `KeyboardEvent`,
`MouseEvent`, `Scene`, `Path`, `DynamicPath`, `StaticRenderer`, `Sprite`,
`Print`, `Wipe`, `Scroll`, `Background`, `Canvas`, `Screen`, `Frame`,
`Layout`, `Label`, `Button`, `CheckBox`, `RadioButtons`, `Text`, `TextBox`,
`DropdownList`, `ListBox`, and `Widget`.

## Product State Model

Events carry key codes or mouse coordinates and button flags. A Scene owns
ordered Effects, registers them, resets them, forwards input from the
topmost effect, and saves effect state on exit. A Path records positions and
can be reset for replay; a DynamicPath maintains a current position in
response to an event. Renderers expose dimensions and the next text image.
Sprites project renderer images at path positions, while Print, Wipe, Scroll,
and Background project screen operations at deterministic frame numbers.

Widgets expose values, validity, names, disabled state, focus behavior, and
layout dimensions. Frames own layouts and widgets, can load and save named
data, and flush a Canvas to the supplied screen recorder.

## Error Semantics

The checks avoid exact incidental diagnostic text. They require public
operations to return their documented values, preserve event pass-through
semantics, and keep state transitions deterministic. Unsupported terminal
opening, curses setup, timing-dependent playback, and environment-dependent
backends are outside this package.

## Cross-Component Invariants

Scene effect registration agrees with the effect's owning Scene. Path reset
replays the same recorded route. Renderer dimensions determine projected
positions. A Sprite's last position agrees with its most recent path step and
can be compared with another Sprite. Widget values saved by a Frame agree
with the values restored through named initial data. Layout focus and widget
lookup remain consistent with the widgets rendered through the Frame Canvas.

## Representative Workflows

Representative workflows compose event dispatch, path movement, renderer
projection, effect updates, widget editing, callbacks, layout focus, Frame
data persistence, and Canvas transfer. Each workflow performs multiple
public operations and uses only values created inside the test process.

## Non-Goals

The package excludes curses, TTY and terminal probing, `Screen.open`,
`Screen.wrapper`, `Screen.play`, sleeps, wall-clock scheduling, random visual
effects, samples, exact ANSI output, whole-buffer snapshots, filesystem or
network widgets, host state, private imports, source tests, and incidental
exception strings.

## Invocation Protocol

Run pytest against the package with `--target-root` set to the checkout that
contains the `asciimatics` package. JSON reporting may be enabled with
`pytest-json-report`. All screen behavior is supplied by a local recorder;
the test process never opens a terminal or contacts a service.

## Environment

The assessment environment is Python 3.11 on Linux without network access.
The target package is not pre-installed. Requirements are `pytest`,
`pytest-json-report`, `wcwidth>=0.5`, and `pyfiglet>=0.7.2`. The checkout is
provided as the pytest target root. Replay values, events, paths, and screen
records are created locally.

## Evaluation Notes

Current evidence is same-process local replay. It does not establish a
trusted black-box Stage 4 runner, an external signature, trusted provenance,
or final qualification status. The local evidence includes a Python 3.11
replay and a separate Python 3.10 compatibility replay. These records describe
local reproducibility only and do not establish a trusted external evaluator
or final qualification.
