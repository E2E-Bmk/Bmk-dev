# textX Public Behavior Specification

## Product Overview

textX is a Python library for defining domain-specific languages from grammar
descriptions. A grammar string or grammar file produces a metamodel, and that
metamodel parses model strings or model files into Python objects with public
attributes, containment relationships, cross references, source locations,
processors, and optional export or registration behavior.

## Scope

The supported surface in this package is the public grammar-to-model workflow:
`metamodel_from_str`, `metamodel_from_file`, `model_from_str`,
`model_from_file`, public exceptions, object and model processors, scope
providers, containment traversal helpers, registration helpers, export helpers,
and the `textx check` command. The expected behavior is demonstrated with a
small workflow language containing a project header, states, events,
transitions, and two action variants.

## Public Import Surface

Applications may import the public names exposed from `textx`, including
metamodel constructors, traversal helpers, registration descriptors and
functions, public exception classes, `textx_isinstance`, and model location
helpers. Applications may also import `metamodel_export`, `model_export`, and
`PlantUmlRenderer` from `textx.export`, and may invoke the public Click command
object from `textx.cli`.

## Product State Model

A grammar defines rule classes and typed attributes. Parsing the workflow
language yields a root workflow object containing a single project object,
ordered state objects, ordered event objects, and ordered transition objects.
Boolean, integer, and string terminals are converted to Python values.
Alternatives instantiate the concrete action rule that matched the input.

Cross references in a model resolve to the target objects declared elsewhere in
the same parsed model. Public helper functions expose containment children,
parent lookup, the owning model, the originating metamodel, source positions,
and dynamic rule-class instance checks.

## Error Semantics

Invalid model syntax raises `TextXSyntaxError`. Unresolvable references and
semantic policy failures raised from processors surface as `TextXSemanticError`.
Duplicate or missing public registrations surface as `TextXRegistrationError`.
Tests assert exception types and observable state rather than exact message
strings.

## Cross-Component Invariants

Parsing from a grammar file and parsing from an equivalent grammar string must
produce the same public object graph projection for the same model text. Object
processors, model processors, custom scope providers, traversal helpers,
location helpers, registration lookup, export helpers, and CLI validation must
all operate over the same parsed model facts and preserve ordering of states,
events, transitions, and action variants.

## Representative Workflow

A representative client creates a workflow grammar, parses a valid workflow
model, verifies the project and transition graph, registers processors that
derive event data, registers custom state resolution for case-insensitive
references, exports metamodel and model projections to DOT or PlantUML text,
registers language and generator descriptors, and validates grammar and model
files through `textx check`.

## Non-Goals

This package does not require GraphViz image rendering, live services, network
access, performance guarantees, source-private attributes, source test modules,
or compatibility with undocumented internals. It does not require a package to
duplicate exact exception wording or formatting beyond public exception types
and observable public values.

## Invocation Protocol

Install the requirements file that accompanies the public behavior tests and
make a textX implementation importable as `textx`. Run the tests with:

```bash
python -m pytest <test-directory> -q -W error
```

The public behavior tests use temporary files only. They do not require network
access, a database, Docker, or an external command-line service.

## Environment

The intended evaluation environment is Linux with Python 3.11 and without network access
during the test run. The target package is not pre-installed; the
implementation under evaluation must provide the `textx` package. Required
runtime and test packages are `pytest`, `Arpeggio`, and `click`.

## Evaluation Notes

The tests are split into atomic API checks and integration checks that combine
independent public projections of the same grammar and model facts. The
integration dependency markers are informational and point only to atomic
behaviors. A minimal import-only package should collect the tests while passing
well below ten percent, demonstrating that the tests require real public
behavior rather than import availability alone.
