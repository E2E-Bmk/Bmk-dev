"""Shared fixtures, model classes, and constants for schematics oracle tests."""
import pytest

from schematics.models import Model
from schematics.types import DecimalType, IntType, StringType


class Child(Model):
    """Reusable nested model for compound-field tests."""
    count = IntType(required=True)


class Record(Model):
    """Reusable model with serialized_name and default for export tests."""
    name = StringType(required=True, serialized_name="label")
    count = IntType(default=3)
    amount = DecimalType()
