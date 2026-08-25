"""Shared fixtures, helpers, and constants for astroid oracle tests."""
import warnings

import pytest

import astroid
from astroid import MANAGER, inference_tip, register_module_extender, nodes
from astroid.exceptions import (
    AstroidBuildingError,
    AstroidError,
    AstroidImportError,
    AstroidSyntaxError,
    AttributeInferenceError,
    InferenceError,
    NameInferenceError,
    ParentMissingError,
    StatementMissing,
    UseInferenceDefault,
)
