from __future__ import annotations

# Rewritten from jsonschema/tests/test_deprecations.py at the pinned source revision.
from unittest import TestCase
import warnings
from jsonschema import FormatChecker, exceptions, validators

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from jsonschema import RefResolver

class TestDeprecations(TestCase):

    def test_ErrorTree_setitem(self):
        """
        As of v4.20.0, setting items on an ErrorTree is deprecated.
        """
        e = exceptions.ValidationError('some error', path=['foo'])
        tree = exceptions.ErrorTree()
        subtree = exceptions.ErrorTree(errors=[e])
        message = 'ErrorTree.__setitem__ is '
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            tree['foo'] = subtree
        self.assertEqual(tree['foo'], subtree)
        self.assertEqual(w.filename, __file__)

    def test_RefResolver_in_scope(self):
        """
        As of v4.0.0, RefResolver.in_scope is deprecated.
        """
        resolver = RefResolver.from_schema({})
        message = 'jsonschema.RefResolver.in_scope is deprecated '
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            with resolver.in_scope('foo'):
                pass
        self.assertEqual(w.filename, __file__)

    def test_Validator_is_valid_two_arguments(self):
        """
        As of v4.0.0, calling is_valid with two arguments (to provide a
        different schema) is deprecated.
        """
        validator = validators.Draft7Validator({})
        message = 'Passing a schema to Validator.is_valid is deprecated '
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            result = validator.is_valid('foo', {'type': 'number'})
        self.assertFalse(result)
        self.assertEqual(w.filename, __file__)

    def test_Validator_iter_errors_two_arguments(self):
        """
        As of v4.0.0, calling iter_errors with two arguments (to provide a
        different schema) is deprecated.
        """
        validator = validators.Draft7Validator({})
        message = 'Passing a schema to Validator.iter_errors is deprecated '
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            (error,) = validator.iter_errors('foo', {'type': 'number'})
        self.assertEqual(error.validator, 'type')
        self.assertEqual(w.filename, __file__)

    def test_RefResolver(self):
        """
        As of v4.18.0, RefResolver is fully deprecated.
        """
        message = 'jsonschema.RefResolver is deprecated'
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            from jsonschema import RefResolver
        self.assertEqual(w.filename, __file__)
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            from jsonschema.validators import RefResolver
        self.assertEqual(w.filename, __file__)

    def test_RefResolutionError(self):
        """
        As of v4.18.0, RefResolutionError is deprecated in favor of directly
        catching errors from the referencing library.
        """
        message = 'jsonschema.exceptions.RefResolutionError is deprecated'
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            from jsonschema import RefResolutionError as root_error
        self.assertEqual(w.filename, __file__)
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            from jsonschema.exceptions import RefResolutionError as module_error
        self.assertIs(root_error, module_error)
        self.assertEqual(w.filename, __file__)

    def test_FormatChecker_cls_checks(self):
        """
        As of v4.14.0, FormatChecker.cls_checks is deprecated without
        replacement.
        """
        self.addCleanup(FormatChecker.checkers.pop, 'boom', None)
        message = 'FormatChecker.cls_checks '
        with self.assertWarnsRegex(DeprecationWarning, message) as w:
            FormatChecker.cls_checks('boom')
        self.assertEqual(w.filename, __file__)
