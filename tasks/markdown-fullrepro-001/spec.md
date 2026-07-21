# markdown Specification

## Product Overview

This document describes the public behavior of `markdown`. The package should provide the documented user-facing Python surface and reproduce observable behavior for the feature areas listed below.

Project overview:

```text
[Python-Markdown][]
===================

[![Build Status][build-button]][build]
[![Coverage Status][codecov-button]][codecov]
[![Latest Version][mdversion-button]][md-pypi]
[![Python Versions][pyversion-button]][md-pypi]
[![BSD License][bsdlicense-button]][bsdlicense]
[![Code of Conduct][codeofconduct-button]][Code of Conduct]

[build-button]: https://github.com/Python-Markdown/markdown/actions/workflows/tox.yml/badge.svg
[build]: https://github.com/Python-Markdown/markdown/actions/workflows/tox.yml
[codecov-button]: https://codecov.io/gh/Python-Markdown/markdown/branch/master/graph/badge.svg
[codecov]: https://codecov.io/gh/Python-Markdown/markdown
[mdversion-button]: https://img.shields.io/pypi/v/Markdown.svg
[md-pypi]: https://pypi.org/project/Markdown/
[pyversion-button]: https://img.shields.io/pypi/pyversions/Markdown.svg
[bsdlicense-button]: https://img.shields.io/badge/license-BSD-yellow.svg
[bsdlicense]: https://opensource.org/licenses/BSD-3-Clause
[codeofconduct-button]: https://img.shields.io/badge/code%20of%20conduct-contributor%20covenant-green.svg?style=flat-square
[Code of Conduct]: https://github.com/Python-Markdown/markdown/blob/master/CODE_OF_CONDUCT.md

This is a Python implementation of John Gruber's [Markdown][].
It is almost completely compliant with the reference implementation,
though there are a few known issues. See [Features][] for information
on what exactly is supported and what is not. Additional features are
supported by the [Available Extensions][].

[Python-Markdown]: https://Python-Markdown.github.io/
[Markdown]: https://daringfireball.net/projects/markdown/
[Features]: https://Python-Markdown.github.io#Features
[Available Extensions]: https://Python-Markdown.github.io/extensions

Documentation
-------------

~~~bash
pip install markdown
~~~
~~~python
import markdown
html = markdown.markdown(your_text_string)
~~~

For more advanced [installation] and [usage] documentation, see the `docs/` directory
of the distribution or the project website at <https://Python-Markdown.github.io/>.

[installation]: https://python-markdown.github.io/install/
[usage]: https://python-markdown.github.io/reference/

See the change log at <https://python-markdown.github.io/changelog/>.

Support
-------

You may report bugs, ask for help, and discuss various other issues on the [bug tracker][].

[bug tracker]: https://github.com/Python-Markdown/markdown/issues

Code of Conduct
---------------

Everyone interacting in the Python-Markdown project's code bases, issue trackers,
and mailing lists is expected to follow the [Code of Conduct].
```

## Scope

The covered scope is the public Python API and command/user workflows for these behavior areas: testBlankInput; testDotNotationExtension; testDotNotationExtensionWithClass; testEntryPointExtension; testInstanceExtension; testSimpleInput; testWhitespaceOnly; testFileNames; testFileObjects; testStdinStdout; testParseChunk; testParseDocument; testBlankState; testIsSate; testReset; testSetSate; testSimpleStore; testStoreMore; testCreateRegistry.

Out of scope: private modules, private attributes, repository maintenance scripts, network access, exact internal cache structures, and implementation-specific repr/message wording unless explicitly documented as public behavior.

## Installable Surface

The package provides an importable `markdown` package from the solution root. The package should be importable without depending on another installed distribution of the same library.

Typical imports are:

```python
import markdown
from markdown import Markdown, markdownFromFile
```

Public export names observed from the package surface include:

- `markdown.Markdown`
- `markdown.markdown`
- `markdown.markdownFromFile`
- `markdown.__version__`
- `markdown.__version_info__`

Additional public module members observed in the package tree include:

- `markdown.blockparser.State`
- `markdown.blockparser.BlockParser`
- `markdown.blockprocessors.build_block_parser`
- `markdown.blockprocessors.BlockProcessor`
- `markdown.blockprocessors.ListIndentProcessor`
- `markdown.blockprocessors.CodeBlockProcessor`
- `markdown.blockprocessors.BlockQuoteProcessor`
- `markdown.blockprocessors.OListProcessor`
- `markdown.blockprocessors.UListProcessor`
- `markdown.blockprocessors.HashHeaderProcessor`
- `markdown.blockprocessors.SetextHeaderProcessor`
- `markdown.blockprocessors.HRProcessor`
- `markdown.blockprocessors.EmptyBlockProcessor`
- `markdown.blockprocessors.ReferenceProcessor`
- `markdown.blockprocessors.ParagraphProcessor`
- `markdown.core.Markdown`
- `markdown.core.markdown`
- `markdown.core.markdownFromFile`
- `markdown.htmlparser.HTMLExtractor`
- `markdown.inlinepatterns.build_inlinepatterns`
- `markdown.inlinepatterns.dequote`
- `markdown.inlinepatterns.EmStrongItem`
- `markdown.inlinepatterns.Pattern`
- `markdown.inlinepatterns.InlineProcessor`
- `markdown.inlinepatterns.SimpleTextPattern`
- `markdown.inlinepatterns.SimpleTextInlineProcessor`
- `markdown.inlinepatterns.EscapeInlineProcessor`
- `markdown.inlinepatterns.SimpleTagPattern`
- `markdown.inlinepatterns.SimpleTagInlineProcessor`
- `markdown.inlinepatterns.SubstituteTagPattern`
- `markdown.inlinepatterns.SubstituteTagInlineProcessor`
- `markdown.inlinepatterns.BacktickInlineProcessor`
- `markdown.inlinepatterns.DoubleTagPattern`
- `markdown.inlinepatterns.DoubleTagInlineProcessor`
- `markdown.inlinepatterns.HtmlInlineProcessor`
- `markdown.inlinepatterns.AsteriskProcessor`
- `markdown.inlinepatterns.UnderscoreProcessor`
- `markdown.inlinepatterns.LinkInlineProcessor`
- `markdown.inlinepatterns.ImageInlineProcessor`
- `markdown.inlinepatterns.ReferenceInlineProcessor`
- `markdown.inlinepatterns.ShortReferenceInlineProcessor`
- `markdown.inlinepatterns.ImageReferenceInlineProcessor`
- `markdown.inlinepatterns.ShortImageReferenceInlineProcessor`
- `markdown.inlinepatterns.AutolinkInlineProcessor`
- `markdown.inlinepatterns.AutomailInlineProcessor`
- `markdown.postprocessors.build_postprocessors`
- `markdown.postprocessors.Postprocessor`
- `markdown.postprocessors.RawHtmlPostprocessor`
- `markdown.postprocessors.AndSubstitutePostprocessor`
- `markdown.postprocessors.UnescapePostprocessor`
- `markdown.preprocessors.build_preprocessors`
- `markdown.preprocessors.Preprocessor`
- `markdown.preprocessors.NormalizeWhitespace`
- `markdown.preprocessors.HtmlBlockPreprocessor`
- `markdown.serializers.to_html_string`
- `markdown.serializers.to_xhtml_string`
- `markdown.test_tools.TestCase`
- `markdown.test_tools.recursionlimit`
- `markdown.test_tools.Kwargs`
- `markdown.test_tools.LegacyTestMeta`
- `markdown.test_tools.LegacyTestCase`
- `markdown.treeprocessors.build_treeprocessors`
- `markdown.treeprocessors.isString`
- `markdown.treeprocessors.Treeprocessor`
- `markdown.treeprocessors.InlineProcessor`
- `markdown.treeprocessors.PrettifyTreeprocessor`
- `markdown.treeprocessors.UnescapeTreeprocessor`
- `markdown.util.get_installed_extensions`
- `markdown.util.deprecated`
- `markdown.util.parseBoolValue`
- `markdown.util.code_escape`
- `markdown.util.nearing_recursion_limit`
- `markdown.util.AtomicString`
- `markdown.util.Processor`
- `markdown.util.HtmlStash`
- `markdown.util.Registry`

`markdown.__version_info__` is a five-item tuple containing major, minor,
patch, release stage, and release serial. `markdown.__version__` is its
normalized PEP 440 string form. Final releases omit a zero patch component;
development, alpha, beta, and release-candidate stages use `.dev`, `a`, `b`,
and `rc` suffixes respectively.

`markdown.util.Registry` stores items under unique names with numeric
priorities. Iteration and integer indexing expose items in descending priority
order. Registering an existing name replaces that item and priority, and later
registrations are reflected by subsequent iteration and lookup operations.

## Public API Behavior

Implement public functions, classes, constants, and exceptions so callers can use the package in normal documented workflows. Constructors should accept documented argument forms, preserve public attributes/properties, and raise the documented public exception types for invalid inputs. Parsing, formatting, conversion, tokenization, localization, CLI, or helper behavior should be deterministic and should not depend on hidden state outside caller-provided inputs and normal standard-library resources.

## Error Semantics

Invalid input should fail with the package's public exception types when such types are part of the public API. Do not expose private implementation exceptions for user-level errors. Error message text is not part of the public contract unless the public documentation specifies exact wording.

## Cross-View Invariants

- Public constructors and module-level factory functions must agree on the object values they create.
- A value parsed from a supported string/file/input form must format or serialize consistently through the documented output API.
- CLI-facing behavior, when in scope, must call the same public logic as Python API behavior.
- Equality, ordering, hashing, or containment behavior must be stable for equivalent public values.
- Locale, timezone, encoding, grammar, SQL, markup, token, or parser options must be carried through to all public projections that expose them.
- Repeated operations on the same immutable public value must produce the same observable result.

## Representative Workflow

1. Import `markdown` from the solution package.
2. Construct or parse representative public input values using documented functions/classes.
3. Inspect public properties or return values.
4. Convert, format, serialize, tokenize, or execute the corresponding public workflow.
5. Handle invalid input using documented public exception types.

## Non-Goals

Do not reproduce upstream private helper modules, source-code layout, project release tooling, coverage tooling, or network-bound data fetching. Private implementation details and repository maintenance artifacts are outside the public contract.
