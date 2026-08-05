# Lektor Public Behavior Specification

## Product Overview

Lektor is a local static-site content system. A project tree contains project
configuration, content records, data models, templates, and assets. The
configuration and content tree are exposed through Python objects, queries,
templates, generated files, and command output.

This package describes deterministic behavior for a project stored on the
local filesystem. The examples use a small site with English and French
alternatives, page and blog-post models, typed record fields, templates,
attachments, and assets.

## Scope

The covered surface includes:

- `Project.from_file`, `Project.from_path`, `Project.discover`,
  `Project.content_path_from_filename`, `Project.get_output_path`, and the
  project JSON projection.
- `Environment.load_config`, `Environment.new_pad`,
  `Environment.render_template`, and HTML autoescape selection.
- `tokenize` and `serialize` for scalar and multiline metadata.
- `Database` and `Pad` record loading, URL resolution, URL construction,
  alternatives, assets, and local queries.
- `Record` mapping access and public path, URL, alternative, visibility,
  parent, child, attachment, sibling, and pagination views.
- `F` query expressions and `Query.filter`, `order_by`, `limit`, `offset`,
  `count`, `first`, `get`, `all`, `distinct`, and visibility controls.
- Data-model fields and public conversion for strings, integers, booleans,
  dates, datetimes, strings collections, and Markdown.
- `DataModel.to_json`, Markdown rendering in a public `Context`, Jinja
  templates, and URL helpers.
- `Builder.build`, `Builder.build_all`, `Builder.prune`, build artifacts,
  current-artifact state, dependency information, alternative output, and
  asset copying.
- The `cli` entry point for `build`, `project-info`, `content-file-info`, and
  the `pr` alias.

The test project is created under a temporary directory. All expected paths
and URLs are derived from that project tree rather than from a machine-specific
location.

## Installable Surface

The target package is imported as `lektor`. The covered public imports are:

```python
from lektor.build_programs import BuildProgram
from lektor.builder import Builder
from lektor.cli import cli
from lektor.context import Context
from lektor.db import Database, F, get_alts
from lektor.environment import Environment
from lektor.metaformat import serialize, tokenize
from lektor.project import Project
```

The package also exposes the public methods used in this specification:
`Project.from_file`, `Project.from_path`, `Project.discover`,
`Environment.load_config`, `Environment.new_pad`,
`Environment.render_template`, `Pad.get`, `Pad.query`,
`Pad.resolve_url_path`, `Pad.make_url`, `Query.filter`,
`Query.order_by`, `Query.limit`, `Query.offset`, `Query.count`,
`Query.first`, `Query.get`, `Query.all`, `Query.distinct`,
`Record.url_to`, `Builder.build`, `Builder.build_all`, `Builder.prune`,
and the Click command group `cli`.

## Product State Model

The durable project state is a local tree:

1. A `.lektorproject` file supplies the project name, output directory,
   external URL, alternatives, locale, and asset inclusion rules.
2. `content/` contains `contents.lr` records, alternative-specific record
   files, and attachment files.
3. `models/` supplies field types, labels, child ordering, and pagination.
4. `templates/` converts records and environment values into text.
5. `assets/` supplies files and directories copied to the output tree.
6. The output tree contains generated artifacts and a `.lektor` build-state
   file.

`Project` and `Environment` are configuration views. `Database` and `Pad`
load records from the content tree. A `Query` is a composable view over child
records or attachments. A `Builder` derives artifacts from records, templates,
models, and assets.

Record mapping fields include the system values `_id`, `_model`, and `_alt`.
Application fields are available through mapping access such as
`record["title"]`. Public properties expose `path`, `url_path`, `alt`,
`parent`, `children`, `attachments`, `is_hidden`, `is_visible`,
`is_discoverable`, and `is_undiscoverable`.

Field conversion produces Python `int`, `bool`, `date`, `datetime`, list, and
Markdown values where configured. A requested alternative can use a primary
record as a fallback while retaining the requested alternative identifier.

## Error Semantics

The required result behavior is:

| Condition | Required result |
| --- | --- |
| A path does not identify a record | `Pad.get()` returns `None`. |
| A hidden record is resolved by URL without an override | URL resolution returns `None`. |
| A hidden record is resolved with `include_invisible=True` | The record is returned. |
| A content file is outside the discovered project | The JSON command result has `success` false and exits unsuccessfully. |
| A build produces no failed artifacts | `Builder.build_all()` returns `0`. |

The contract relies on result types and public values. Exact exception wording,
object representations, generated timestamps, progress durations, and cache
database bytes are not required.

## Cross-View Invariants

- Project discovery, `Project`, `Environment`, and CLI project information
  describe the same project tree.
- A record's mapping values are the values used by Jinja rendering and by
  generated page artifacts.
- A record's `url_path` is the path used by URL resolution and by its page
  artifact after conversion to an output filename.
- A requested alternative retains its identifier in the record view and uses
  the configured URL prefix in rendered and built paths.
- Query filtering, ordering, pagination, and template iteration operate on
  the same record sequence.
- Data-model field definitions determine both record values and the field
  metadata returned by `DataModel.to_json`.
- Page templates, attachment copying, and asset copying derive their output
  from the corresponding project files.
- A second build with unchanged sources reports no updated artifacts, while a
  changed template, record, or model file reports an updated artifact.
- Pruning removes an artifact for a page that becomes hidden.
- Text and JSON projections of project and content-file commands describe the
  same project and logical content paths.

## Representative Workflows

### Discover and inspect a project

1. Start from a nested content directory.
2. Discover the closest project.
3. Load the project configuration and inspect its name, tree, alternatives,
   URL, locale, and output path.
4. Convert content filenames to logical record paths.

### Query and render content

1. Create an `Environment` for a local project without remote plugins.
2. Create a `Pad` and load the root or a nested record.
3. Filter and order a child query.
4. Select an alternative or a pagination page.
5. Render the selected record through its template inside a public
   `Context`.

### Build and update a site

1. Construct a `Builder` with a local output directory.
2. Build a page, attachment, asset root, or all roots.
3. Read generated artifact contents and names.
4. Build again with unchanged sources.
5. Change a source or dependent model/template and build again.
6. Prune an artifact whose page is no longer visible.

### Use command projections

1. Invoke `project-info` with text and JSON output.
2. Invoke `content-file-info` for a local `.lr` file with text and JSON
   output.
3. Invoke `build` with an explicit output path.
4. Invoke the `pr` alias and compare its output with `project-info`.

## Non-Goals

The covered behavior does not include network access, package installation,
deployment, a development server, administration frontend assets, watcher
mode, remote plugins, external databases, image or video conversion utilities,
shell-specific programs, exact progress output, generated timestamps, private
implementation helpers, or upstream test modules.

## Invocation Protocol

Install the requirements listed below and make a Lektor implementation
importable as `lektor`. Run both test modules with:

```bash
python -m pytest <test-directory> -q -W error --json-report \
  --json-report-file=<report-path>
```

The tests use temporary project trees and ordinary text files. They do not
require a service, a database server, a Docker runtime, or an external command
line utility.

## Environment

The intended replay environment is Linux with Python 3.11 without network access during the test run. The target package is not pre-installed before the local implementation is made importable. Python 3.10 is also used for a local compatibility replay.

The requirements are `Babel`, `Flask`, `Jinja2`, `MarkupSafe`, `Pillow`,
`Werkzeug`, `click`, `inifile`, `marshmallow`, `marshmallow_dataclass`,
`mistune`, `pytest`, `pytest-json-report`, `python-slugify`, `requests`, and
`watchfiles`.

## Evaluation Notes

The atomic layer isolates one public behavior at a time. The integration layer
combines project files with records, queries, templates, artifacts, and
command projections. The examples use deterministic local values and compare
meaningful outputs rather than timestamps or exact error strings. An
import-compatible but behaviorally weak package should pass well below ten
percent of the physical cases.
