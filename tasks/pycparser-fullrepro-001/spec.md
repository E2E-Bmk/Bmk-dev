# pycparser Specification

## Product Overview

This document describes the public behavior of `pycparser`. The package should provide the documented user-facing Python surface and reproduce observable behavior for the feature areas listed below.

Project overview:

```text
===============
pycparser v3.00
===============

.. image:: https://github.com/eliben/pycparser/workflows/pycparser-tests/badge.svg
  :align: center
  :target: https://github.com/eliben/pycparser/actions

----

.. contents::
    :backlinks: none

.. sectnum::

Introduction
============

What is pycparser?
------------------

**pycparser** is a parser for the C language, written in pure Python. It is a
module designed to be easily integrated into applications that need to parse
C source code.

What is it good for?
--------------------

Anything that needs C code to be parsed. The following are some uses for
**pycparser**, taken from real user reports:

* C code obfuscator
* Front-end for various specialized C compilers
* Static code checker
* Automatic unit-test discovery
* Adding specialized extensions to the C language

One of the most popular uses of **pycparser** is in the `cffi
<https://cffi.readthedocs.io/en/latest/>`_ library, which uses it to parse the
declarations of C functions and types in order to auto-generate FFIs.

**pycparser** is unique in the sense that it's written in pure Python - a very
high level language that's easy to experiment with and tweak. To people familiar
with Lex and Yacc, **pycparser**'s code will be simple to understand. It also
has no external dependencies (except for a Python interpreter), making it very
simple to install and deploy.

Which version of C does pycparser support?
------------------------------------------

**pycparser** aims to support the full C99 language (according to the standard
ISO/IEC 9899). Some features from C11 are also supported, and patches to support
more are welcome.

**pycparser** supports very few GCC extensions, but it's fairly easy to set
things up so that it parses code with a lot of GCC-isms successfully. See the
`FAQ <https://github.com/eliben/pycparser/wiki/FAQ>`_ for more details.

What grammar does pycparser follow?
-----------------------------------

**pycparser** very closely follows the C grammar provided in Annex A of the C99
standard (ISO/IEC 9899).

How is pycparser licensed?
--------------------------

`BSD license <https://github.com/eliben/pycparser/blob/main/LICENSE>`_.

Contact details
---------------

For reporting problems with **pycparser** or submitting feature requests, please
open an `issue <https://github.com/eliben/pycparser/issues>`_, or submit a
pull request.

Installing
==========

Prerequisites
-------------

**pycparser** is being tested with modern versions of Python on
Linux, macOS and Windows. See `the CI dashboard <https://github.com/eliben/pycparser/actions/workflows/ci.yml>`__
for details.

**pycparser** has no external dependencies.

Installation process
--------------------

The recommended way to install **pycparser** is with ``pip``::

    > pip install pycparser

Using
=====

Interaction with the C preprocessor
-----------------------------------

In order to be compilable, C code must be preprocessed by the C preprocessor -
``cpp``. A compatible ``cpp`` handles preprocessing directives like ``#include`` and
``#define``, removes comments, and performs other minor tasks that prepare the C
code for compilation.

For all but the most trivial snippets of C code **pycparser**, like a C
compiler, must receive preprocessed C code in order to function correctly. If
you import the top-level ``parse_file`` function from the **pycparser** package,
it will interact with ``cpp`` for you, as long as it's in your PATH, or you
provide a path to
```

## Scope

The covered scope is the public Python API and command/user workflows for these behavior areas: BinaryOp; weakref works on coord; weakref works on nodes; repr; scalar children; tests list children; partial funcdecl generation; alignment; array decl; atomic qual; casts; comma op assignment; comma op in ternary; comma operator funcarg; complex decls; compound literal; enum; enum typedef; expr list in initializer list; exprlist with compound.

Out of scope: private modules, private attributes, repository maintenance scripts, network access, exact internal cache structures, and implementation-specific repr/message wording unless explicitly documented as public behavior.

## Installable Surface

The package provides an importable `pycparser` package from the solution root. The package should be importable without depending on another installed distribution of the same library.

```python
import pycparser
from pycparser import c_ast, c_generator, c_lexer, c_parser, parse_file, preprocess_file
from pycparser.c_ast import Node, NodeVisitor
from pycparser.c_generator import CGenerator
from pycparser.c_lexer import CLexer, Token
from pycparser.c_parser import CParser, Coord, ParseError
```

Public export names observed from the package surface include:

- `pycparser.c_lexer`
- `pycparser.c_parser`
- `pycparser.c_ast`
- `pycparser.preprocess_file`
- `pycparser.parse_file`

Additional public module members observed in the package tree include:

- `pycparser.ast_transforms.fix_switch_cases`
- `pycparser.ast_transforms.fix_atomic_specifiers`
- `pycparser.c_ast.Node`
- `pycparser.c_ast.NodeVisitor`
- `pycparser.c_ast.ArrayDecl`
- `pycparser.c_ast.ArrayRef`
- `pycparser.c_ast.Assignment`
- `pycparser.c_ast.Alignas`
- `pycparser.c_ast.BinaryOp`
- `pycparser.c_ast.Break`
- `pycparser.c_ast.Case`
- `pycparser.c_ast.Cast`
- `pycparser.c_ast.Compound`
- `pycparser.c_ast.CompoundLiteral`
- `pycparser.c_ast.Constant`
- `pycparser.c_ast.Continue`
- `pycparser.c_ast.Decl`
- `pycparser.c_ast.DeclList`
- `pycparser.c_ast.Default`
- `pycparser.c_ast.DoWhile`
- `pycparser.c_ast.EllipsisParam`
- `pycparser.c_ast.EmptyStatement`
- `pycparser.c_ast.Enum`
- `pycparser.c_ast.Enumerator`
- `pycparser.c_ast.EnumeratorList`
- `pycparser.c_ast.ExprList`
- `pycparser.c_ast.FileAST`
- `pycparser.c_ast.For`
- `pycparser.c_ast.FuncCall`
- `pycparser.c_ast.FuncDecl`
- `pycparser.c_ast.FuncDef`
- `pycparser.c_ast.Goto`
- `pycparser.c_ast.ID`
- `pycparser.c_ast.IdentifierType`
- `pycparser.c_ast.If`
- `pycparser.c_ast.InitList`
- `pycparser.c_ast.Label`
- `pycparser.c_ast.NamedInitializer`
- `pycparser.c_ast.ParamList`
- `pycparser.c_ast.PtrDecl`
- `pycparser.c_ast.Return`
- `pycparser.c_ast.StaticAssert`
- `pycparser.c_ast.Struct`
- `pycparser.c_ast.StructRef`
- `pycparser.c_ast.Switch`
- `pycparser.c_ast.TernaryOp`
- `pycparser.c_ast.TypeDecl`
- `pycparser.c_ast.Typedef`
- `pycparser.c_ast.Typename`
- `pycparser.c_ast.UnaryOp`
- `pycparser.c_ast.Union`
- `pycparser.c_ast.While`
- `pycparser.c_ast.Pragma`
- `pycparser.c_generator.CGenerator`
- `pycparser.c_lexer.Token`
- `pycparser.c_lexer.CLexer`
- `pycparser.c_parser.Coord`
- `pycparser.c_parser.ParseError`
- `pycparser.c_parser.CParser`

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

1. Import `pycparser` from the solution package.
2. Construct or parse representative public input values using documented functions/classes.
3. Inspect public properties or return values.
4. Convert, format, serialize, tokenize, or execute the corresponding public workflow.
5. Handle invalid input using documented public exception types.

## Non-Goals

Do not reproduce upstream private helper modules, source-code layout, project release tooling, coverage tooling, or network-bound data fetching. Private implementation details and repository maintenance artifacts are outside the public contract.
