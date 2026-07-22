"""Shared fixtures, helpers, and constants for cattrs oracle tests."""

import pytest
from attrs import Factory, define, field

import cattrs
from cattrs import (
    BaseValidationError,
    ClassValidationError,
    Converter,
    ForbiddenExtraKeysError,
    IterableValidationError,
    StructureHandlerNotFoundError,
    UnstructureStrategy,
    override,
    transform_error,
)
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn
