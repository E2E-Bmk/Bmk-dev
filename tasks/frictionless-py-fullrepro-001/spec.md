# Frictionless Python Public Behavior Specification

## Product Overview

Frictionless Python provides a public data-management framework for describing,
reading, validating, analyzing, and transforming tabular data. Its durable
facts are local data values plus metadata describing resources, packages,
schemas, fields, dialects, pipelines, reports, and validation errors.

The covered behavior is deterministic library behavior over inline values and
local CSV, JSON, and YAML files. Public projections are represented as
descriptors, typed rows and cells, schema objects, pipeline descriptors,
analysis mappings, and structured report/error fields.

## Scope

This specification covers:

- Public construction and descriptor conversion for `Resource`, `Package`,
  `Schema`, `Field`, `Dialect`, and `Pipeline`.
- Inline table data and local CSV, JSON, and YAML resources.
- Field casting for integer, number, boolean, date, datetime, array, object,
  and string fields.
- Missing values, field names, field type selection, delimiters, and simple
  schema constraints.
- The public `describe`, `extract`, `validate`, `transform`, and `list`
  actions.
- Resource and package management, extraction, validation, copying, and
  descriptor round trips.
- `Detector` inference and `Analyzer` summary and detailed projections.
- `Report`, `ReportTask`, and `Error` projections through stable structured
  fields, including error coordinates and flattened report rows.
- Public pipeline steps for normalization, filtering, sorting, and adding
  fields.

The cases intentionally use fixed values and temporary local fixtures. They
compare public structures and values rather than console layout or rendered
message wording.

## Public Import Surface

The covered import surface includes:

```python
from frictionless import (
    Analyzer,
    Detector,
    Dialect,
    Error,
    Field,
    Package,
    Pipeline,
    Report,
    Resource,
    Schema,
    describe,
    extract,
    list,
    transform,
    validate,
)
from frictionless import fields, steps
```

The built-in field classes used here are `IntegerField`, `NumberField`,
`BooleanField`, `DateField`, `DatetimeField`, `ArrayField`, `ObjectField`, and
`StringField`. No private module or source test import is part of the contract.

## Product State Model

The state model is a graph of metadata and data:

1. A resource owns a source, schema, dialect, detector, and public name.
2. A package owns ordered named resources and package metadata.
3. A schema owns ordered fields, missing values, primary keys, and foreign-key
   metadata.
4. A pipeline owns ordered public transformation steps.
5. A report owns validity, summary counts, warnings, top-level errors, and
   validation tasks.

The same state can be projected into descriptors, typed rows, extracted
records, validation reports, analysis mappings, or transformed resources.
Re-importing a descriptor must preserve the public descriptor and the
observable row or metadata projection.

## Validation And Error Reporting

`validate` returns a `Report`. A valid input has `valid` true, zero errors, and
zero warnings. An invalid input has `valid` false and structured errors either
at report level or under a report task.

Each structured error may expose public coordinates such as `type`,
`rowNumber`, `fieldName`, `fieldNumber`, `cell`, `fieldNames`, or
`referenceName`. The tests use those fields and do not require exact human
message text. `Report.flatten` provides ordered rows for requested structured
columns.

Field readers return `(value, notes)`. A failed cast produces a null value or
structured notes, while a validation pass or constraint failure is reported
through the public report structure.

## Cross-View Invariants

- Resource descriptor conversion and re-import preserve the descriptor.
- Package JSON and YAML descriptors preserve resource names, paths, schemas,
  and extraction behavior.
- Schema field names and types agree with typed row dictionaries.
- `describe` and `extract` over one CSV source agree on labels and row keys.
- Inline, local CSV, local JSON, and local YAML data retain their values across
  supported read and write projections.
- A pipeline's descriptor preserves its ordered step types.
- Transform output carries the updated schema and the transformed row set.
- Report validity and error counts agree with its task/error structure.
- Error descriptors preserve public type and location fields.
- Analyzer row and field counts describe the same resource contents exposed by
  extraction.

## Representative Workflows

A typical workflow is:

1. Create or describe a local resource.
2. Inspect its schema and detector-derived field types.
3. Extract typed rows or validate them against a schema.
4. Read report task and error coordinates as structured data.
5. Apply a public pipeline to filter, normalize, sort, or add fields.
6. Extract or validate the transformed resource.
7. Save and reload resource, schema, package, or pipeline descriptors.

The generated cases also cover package extraction by resource name and row
limit, package validation aggregation, detector-selected delimiters, and local
JSON/YAML data reads.

## Non-Goals

The covered surface excludes HTTP, S3, FTP, SQL, portal adapters, service
credentials, external databases, optional heavy format plugins, network
access, sleeps, timing assertions, host-specific resources, private system
internals, source tests, exact command-line tables, and exact message text.

The cases do not establish isolation, signatures, release qualification, or
any property beyond the local public behavior described here.

## Invocation Protocol

Install the requirements file, make the target package importable, and run
both canonical test modules with `pytest`. A JSON test report is the
reproducibility record. The suite must collect 64 tests, with 32 atomic cases,
32 integration cases, and no system end-to-end cases.

The integration cases use public dependency markers to document which atomic
facts they compose. They do not import or execute project source tests.

## Environment

Reference execution uses Python 3.10 and Python 3.11 on Linux without network access.
The support packages `pytest`, `pytest-json-report`, and `PyYAML` are
required and importable. The target package is not pre-installed; the runner
supplies the pinned implementation through installation or an import path.
No service, credential, portal, database, or optional heavy plugin is required.

## Evaluation Notes

The intended comparison is structural and deterministic. Ignore timing fields,
temporary file locations, hashes that describe a particular local file, and
human-readable error messages when comparing results. Preserve ordered lists,
field names, resource names, error types, row coordinates, and typed cell
values.

The accompanying node inventory, taxonomy, and map are generated from the
physical top-level test functions. The task metadata records the fixed source
commit, physical layer counts, local replay state, and explicit trust boundary.
