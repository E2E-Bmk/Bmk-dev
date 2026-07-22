"""Shared fixtures, helpers, and constants for marshmallow oracle tests."""

from __future__ import annotations

import datetime as dt
import decimal
import json
from dataclasses import dataclass

import pytest

from marshmallow import (
    EXCLUDE,
    INCLUDE,
    RAISE,
    Schema,
    ValidationError,
    fields,
    post_dump,
    post_load,
    pre_dump,
    pre_load,
    validate,
    validates,
    validates_schema,
)


@dataclass
class User:
    name: str
    email: str
    age: int = 0
