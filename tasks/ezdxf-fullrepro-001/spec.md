# ezdxf Public Drawing and Round-Trip Specification

## Product Overview

`ezdxf` is a Python library for creating, inspecting, editing, and writing DXF
drawings. A drawing is a public object graph containing document header values,
resource tables, layouts, blocks, graphical entities, and application data.
The covered behavior uses small drawings constructed during each run and checks
their semantic projections through public object APIs and local DXF round trips.

## Scope

This specification covers:

- Creating drawings with `ezdxf.new` for documented DXF versions and units.
- Reading generated ASCII drawings with `ezdxf.read` from text streams.
- Writing and loading local drawings with `saveas` and `ezdxf.readfile`.
- Header variables, layer, linetype, style, and APPID table entries.
- Modelspace, paperspace, named layouts, blocks, block references, and
  block attributes.
- Common public entity factories including line, circle, arc, point, text,
  MTEXT, polylines, ellipse, spline, ray, xline, solid, trace, 3DFACE, and
  viewport entities.
- Public DXF attribute mutation, entity destruction, layout purge, colors,
  transparency, UCS/OCS conversion, vector arithmetic, and matrix transforms.
- Application-defined data, XDATA, user XDATA list and dictionary helpers, and
  extension-dictionary XRECORD data.
- Entity query selection, query attribute mutation, layout/document grouping,
  and cross-view consistency after local serialization.

The cases use generated values and pytest-managed temporary files. They do not
import source tests or private low-level implementation modules.

## Public Import Surface

The covered imports are:

```python
import ezdxf
from ezdxf import colors
from ezdxf.entities.xdata import XDataUserDict, XDataUserList
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Matrix44, OCS, UCS, Vec3, distance
```

The tested methods are reached through documented drawing, layout, entity,
table, color, query, grouping, and coordinate APIs.

## Product State Model

A generated drawing has a DXF version, unit setting, header map, resource
tables, layout manager, block definitions, and entity spaces. Modelspace and
paperspace are separate public entity spaces. A block definition is another
entity space referenced by INSERT entities. Entity DXF namespaces hold
geometry, layer, color, placement, and other public attributes.

Application data and XDATA are keyed by registered APPID names. User XDATA
helpers project named lists and dictionaries over the entity's XDATA. An
extension dictionary can contain named XRECORD objects with public tag
collections.

## Error Semantics

The covered valid workflows assert public exception classes only when a
validation path is needed. They do not depend on exact exception wording.
Valid generated drawings, table entries, entity mutations, custom data, and
round trips must complete without warnings.

## Cross-View Invariants

A drawing written to a text stream and loaded through `ezdxf.read` must retain
its DXF version, selected entity types, geometry, attributes, layout ownership,
and custom data. A drawing written to a local file and loaded through
`ezdxf.readfile` must expose equivalent public facts.

Layer queries and grouping must describe the same entities. Modelspace,
paperspace, and block entity counts must remain distinct while document-wide
queries and grouping combine their public contents. Coordinate conversion
round trips must return the original generated point within the library's
public vector tolerance. Block references and attached attributes must remain
connected to their block definitions after loading.

## Representative Workflow

A representative workflow creates a drawing, registers layers and an APPID,
adds common entities to modelspace, creates a block with an attribute
definition, inserts it with an attached attribute, adds a named paperspace
layout and viewport, assigns app data and XDATA, mutates a query result,
serializes the drawing locally, and inspects the loaded document through
queries, grouping, layouts, blocks, and custom-data helpers.

## Non-Goals

The covered behavior excludes ODA or DWG conversion, GUI and rendering
backends, external viewers, private `lldxf` implementation details, source
test imports, large fixtures, exact complete serialized DXF snapshots, exact
error messages, network access, sleeps, timing-sensitive output, and
machine-specific host resources.

It also excludes external commands, persistent global caches, credentials,
binary artifacts, and any workflow that requires a service or remote file.

## Invocation Protocol

The test files are run with pytest against an implementation root supplied by
`--target-root` or `TARGET_ROOT`. The root contains the `ezdxf` package or a
`src/ezdxf` package tree and is placed first on the Python import path.

Example local invocation:

```bash
python -m pytest <task-root> -q --target-root <implementation-root>
```

JSON reporting may be enabled with `pytest-json-report` when recording local
replay evidence.

## Environment

The reference environment is Linux with Python 3.11, without network access.
The target package is not pre-installed; its implementation root is supplied
at invocation time.

Required local packages:

- `pytest`
- `pytest-json-report`

The checks create only small generated drawings and pytest-managed temporary
ASCII DXF files. They do not depend on bundled DXF files, installed fonts,
external programs, Docker, credentials, timing, or persistent host state.

## Evaluation Notes

The cases exercise public library behavior documented in the README and
documentation sections for document management, entities, modelspace,
paperspace, blocks, layers, colors, coordinates, application data, XDATA,
queries, and grouping. Assertions compare semantic projections such as
coordinates, entity types, table values, query membership, group sizes, and
custom-data contents rather than complete file snapshots.
