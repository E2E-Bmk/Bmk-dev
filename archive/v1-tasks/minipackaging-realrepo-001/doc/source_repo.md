# Source Repo: pypa/packaging

- Repository: `pypa/packaging`
- Upstream URL: `https://github.com/pypa/packaging`
- Reference domain: Python package version and dependency metadata
- Benchmark case: `minipackaging-realrepo-001`
- Local note: no dedicated source checkout was found under the benchmark source tree during task authoring; the task surface was scoped from the public `packaging` API shape and an installed `packaging` distribution available in the workspace.

## Selected Surface

This task uses the parts of `packaging` that form a compact but compositional metadata evaluator:

- `packaging.version.Version` style parsing, normalization, and comparison.
- `packaging.specifiers.SpecifierSet` style range and compatible-release checks.
- `packaging.requirements.Requirement` style PEP 508 requirement parsing.
- `packaging.markers.Marker` style environment marker parsing and evaluation.
- Environment dictionary semantics similar to `packaging.markers.default_environment`.

The benchmark adds one small convenience helper, `is_requirement_satisfied`, so hidden system tests can evaluate the cross-feature contract explicitly without requiring an installer implementation.

## Rationale

Package metadata is a good unit/system gap candidate because each feature is independently learnable, but real correctness appears when one requirement string is decomposed and evaluated coherently. A requirement such as a normalized project name with extras, version bounds, and an environment marker requires version parsing, specifier membership, marker evaluation, and extras normalization to share one semantic model.

## Scoped Differences From Upstream

This is not a full reimplementation of `pypa/packaging`. It intentionally excludes wheel tags, metadata validation, dependency groups, licenses, direct URL metadata objects, and the complete PEP grammar. The PRD defines the supported subset that hidden tests may rely on.

## Oracle Expectations

A future reference implementation should be checked against upstream behavior for the selected subset where the PRD and upstream overlap. Where the PRD deliberately narrows behavior, the PRD is the oracle contract for this benchmark task.
