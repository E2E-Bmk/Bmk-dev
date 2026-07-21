# Rewritten from jsonschema/tests/test_validators.py at the pinned source revision.
from __future__ import annotations
from collections import deque
from unittest import TestCase
from jsonschema import TypeChecker, exceptions, validators

def fail(validator, errors, instance, schema):
    for each in errors:
        each.setdefault('message', 'You told me to fail!')
        yield exceptions.ValidationError(**each)

class TestCreateAndExtend(TestCase):

    def setUp(self):
        self.meta_schema = {'$id': 'some://meta/schema'}
        self.validators = {'fail': fail}
        self.type_checker = TypeChecker()
        self.Validator = validators.create(meta_schema=self.meta_schema, validators=self.validators, type_checker=self.type_checker)

    def test_attrs(self):
        self.assertEqual((self.Validator.VALIDATORS, self.Validator.META_SCHEMA, self.Validator.TYPE_CHECKER), (self.validators, self.meta_schema, self.type_checker))

    def test_init(self):
        schema = {'fail': []}
        self.assertEqual(self.Validator(schema).schema, schema)

    def test_iter_errors_successful(self):
        schema = {'fail': []}
        validator = self.Validator(schema)
        errors = list(validator.iter_errors('hello'))
        self.assertEqual(errors, [])

    def test_iter_errors_one_error(self):
        schema = {'fail': [{'message': 'Whoops!'}]}
        validator = self.Validator(schema)
        expected_error = exceptions.ValidationError('Whoops!', instance='goodbye', schema=schema, validator='fail', validator_value=[{'message': 'Whoops!'}], schema_path=deque(['fail']))
        errors = list(validator.iter_errors('goodbye'))
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error.message, expected_error.message)
        self.assertEqual(error.instance, expected_error.instance)
        self.assertEqual(error.schema, expected_error.schema)
        self.assertEqual(error.validator, expected_error.validator)
        self.assertEqual(error.validator_value, expected_error.validator_value)
        self.assertEqual(error.schema_path, expected_error.schema_path)

    def test_iter_errors_multiple_errors(self):
        schema = {'fail': [{'message': 'First'}, {'message': 'Second!', 'validator': 'asdf'}, {'message': 'Third'}]}
        validator = self.Validator(schema)
        errors = list(validator.iter_errors('goodbye'))
        self.assertEqual(len(errors), 3)

    def test_if_a_version_is_provided_it_is_registered(self):
        Validator = validators.create(meta_schema={'$id': 'something'}, version='my version')
        self.assertEqual(Validator.__name__, 'MyVersionValidator')
        self.assertEqual(Validator.__qualname__, 'MyVersionValidator')

    def test_repr(self):
        Validator = validators.create(meta_schema={'$id': 'something'}, version='my version')
        self.assertEqual(repr(Validator({})), 'MyVersionValidator(schema={}, format_checker=None)')

    def test_long_repr(self):
        Validator = validators.create(meta_schema={'$id': 'something'}, version='my version')
        self.assertEqual(repr(Validator({'a': list(range(1000))})), "MyVersionValidator(schema={'a': [0, 1, 2, 3, 4, 5, ...]}, format_checker=None)")

    def test_repr_no_version(self):
        Validator = validators.create(meta_schema={})
        self.assertEqual(repr(Validator({})), 'Validator(schema={}, format_checker=None)')

    def test_dashes_are_stripped_from_validator_names(self):
        Validator = validators.create(meta_schema={'$id': 'something'}, version='foo-bar')
        self.assertEqual(Validator.__qualname__, 'FooBarValidator')

    def test_if_a_version_is_not_provided_it_is_not_registered(self):
        validators.create(meta_schema={'id': 'unregistered meta id'})
        selected = validators.validator_for(
            {'$schema': 'unregistered meta id'}, default=None
        )
        self.assertIsNone(selected)

    def test_validates_registers_meta_schema_id(self):
        meta_schema_key = 'meta schema id'
        my_meta_schema = {'id': meta_schema_key}
        Validator = validators.create(meta_schema=my_meta_schema, version='my version', id_of=lambda s: s.get('id', ''))
        selected = validators.validator_for({'$schema': meta_schema_key}, default=None)
        self.assertIs(selected, Validator)

    def test_validates_registers_meta_schema_draft6_id(self):
        meta_schema_key = 'meta schema $id'
        my_meta_schema = {'$id': meta_schema_key}
        Validator = validators.create(meta_schema=my_meta_schema, version='my version')
        selected = validators.validator_for({'$schema': meta_schema_key}, default=None)
        self.assertIs(selected, Validator)

    def test_create_default_types(self):
        Validator = validators.create(meta_schema={}, validators=())
        self.assertTrue(all((Validator({}).is_type(instance=instance, type=type) for (type, instance) in [('array', []), ('boolean', True), ('integer', 12), ('null', None), ('number', 12.0), ('object', {}), ('string', 'foo')])))

    def test_check_schema_with_different_metaschema(self):
        """
        One can create a validator class whose metaschema uses a different
        dialect than itself.
        """
        NoEmptySchemasValidator = validators.create(meta_schema={'$schema': validators.Draft202012Validator.META_SCHEMA['$id'], 'not': {'const': {}}})
        NoEmptySchemasValidator.check_schema({'foo': 'bar'})
        with self.assertRaises(exceptions.SchemaError):
            NoEmptySchemasValidator.check_schema({})
        NoEmptySchemasValidator({'foo': 'bar'}).validate('foo')

    def test_check_schema_with_different_metaschema_defaults_to_self(self):
        """
        A validator whose metaschema doesn't declare $schema defaults to its
        own validation behavior, not the latest "normal" specification.
        """
        NoEmptySchemasValidator = validators.create(meta_schema={'fail': [{'message': 'Meta schema whoops!'}]}, validators={'fail': fail})
        with self.assertRaises(exceptions.SchemaError):
            NoEmptySchemasValidator.check_schema({})

    def test_extend(self):
        original = dict(self.Validator.VALIDATORS)
        new = object()
        Extended = validators.extend(self.Validator, validators={'new': new})
        self.assertEqual((Extended.VALIDATORS, Extended.META_SCHEMA, Extended.TYPE_CHECKER, self.Validator.VALIDATORS), (dict(original, new=new), self.Validator.META_SCHEMA, self.Validator.TYPE_CHECKER, original))

    def test_extend_idof(self):
        """
        Extending a validator preserves its notion of schema IDs.
        """

        def id_of(schema):
            return schema.get('__test__', self.Validator.ID_OF(schema))
        correct_id = 'the://correct/id/'
        meta_schema = {'$id': 'the://wrong/id/', '__test__': correct_id}
        Original = validators.create(meta_schema=meta_schema, validators=self.validators, type_checker=self.type_checker, id_of=id_of)
        self.assertEqual(Original.ID_OF(Original.META_SCHEMA), correct_id)
        Derived = validators.extend(Original)
        self.assertEqual(Derived.ID_OF(Derived.META_SCHEMA), correct_id)

    def test_extend_applicable_validators(self):
        """
        Extending a validator preserves its notion of applicable validators.
        """
        schema = {'$defs': {'test': {'type': 'number'}}, '$ref': '#/$defs/test', 'maximum': 1}
        draft4 = validators.Draft4Validator(schema)
        self.assertTrue(draft4.is_valid(37))
        Derived = validators.extend(validators.Draft4Validator)
        self.assertTrue(Derived(schema).is_valid(37))

class TestValidationErrorMessages(TestCase):

    def message_for(self, instance, schema, *args, **kwargs):
        cls = kwargs.pop('cls', validators.validator_for(schema))
        cls.check_schema(schema)
        validator = cls(schema, *args, **kwargs)
        errors = list(validator.iter_errors(instance))
        self.assertTrue(errors, msg=f'No errors were raised for {instance!r}')
        self.assertEqual(len(errors), 1, msg=f'Expected exactly one error, found {errors!r}')
        return errors[0].message

    def test_dependencies_single_element(self):
        (depend, on) = ('bar', 'foo')
        schema = {'dependencies': {depend: on}}
        message = self.message_for(instance={'bar': 2}, schema=schema, cls=validators.Draft3Validator)
        self.assertEqual(message, "'foo' is a dependency of 'bar'")

    def test_dependencies_list_draft3(self):
        (depend, on) = ('bar', 'foo')
        schema = {'dependencies': {depend: [on]}}
        message = self.message_for(instance={'bar': 2}, schema=schema, cls=validators.Draft3Validator)
        self.assertEqual(message, "'foo' is a dependency of 'bar'")

    def test_dependencies_list_draft7(self):
        (depend, on) = ('bar', 'foo')
        schema = {'dependencies': {depend: [on]}}
        message = self.message_for(instance={'bar': 2}, schema=schema, cls=validators.Draft7Validator)
        self.assertEqual(message, "'foo' is a dependency of 'bar'")

    def test_additionalItems_single_failure(self):
        message = self.message_for(instance=[2], schema={'items': [], 'additionalItems': False}, cls=validators.Draft3Validator)
        self.assertIn('(2 was unexpected)', message)

    def test_additionalItems_multiple_failures(self):
        message = self.message_for(instance=[1, 2, 3], schema={'items': [], 'additionalItems': False}, cls=validators.Draft3Validator)
        self.assertIn('(1, 2, 3 were unexpected)', message)

    def test_additionalProperties_single_failure(self):
        additional = 'foo'
        schema = {'additionalProperties': False}
        message = self.message_for(instance={additional: 2}, schema=schema)
        self.assertIn("('foo' was unexpected)", message)

    def test_additionalProperties_multiple_failures(self):
        schema = {'additionalProperties': False}
        message = self.message_for(instance=dict.fromkeys(['foo', 'bar']), schema=schema)
        self.assertIn(repr('foo'), message)
        self.assertIn(repr('bar'), message)
        self.assertIn('were unexpected)', message)

    def test_const(self):
        schema = {'const': 12}
        message = self.message_for(instance={'foo': 'bar'}, schema=schema)
        self.assertIn('12 was expected', message)

    def test_contains_draft_6(self):
        schema = {'contains': {'const': 12}}
        message = self.message_for(instance=[2, {}, []], schema=schema, cls=validators.Draft6Validator)
        self.assertEqual(message, 'None of [2, {}, []] are valid under the given schema')

    def test_additionalProperties_false_patternProperties(self):
        schema = {'type': 'object', 'additionalProperties': False, 'patternProperties': {'^abc$': {'type': 'string'}, '^def$': {'type': 'string'}}}
        message = self.message_for(instance={'zebra': 123}, schema=schema, cls=validators.Draft4Validator)
        self.assertEqual(message, '{} does not match any of the regexes: {}, {}'.format(repr('zebra'), repr('^abc$'), repr('^def$')))
        message = self.message_for(instance={'zebra': 123, 'fish': 456}, schema=schema, cls=validators.Draft4Validator)
        self.assertEqual(message, '{}, {} do not match any of the regexes: {}, {}'.format(repr('fish'), repr('zebra'), repr('^abc$'), repr('^def$')))

    def test_False_schema(self):
        message = self.message_for(instance='something', schema=False)
        self.assertEqual(message, "False schema does not allow 'something'")

    def test_contains_too_few(self):
        message = self.message_for(instance=['foo', 1], schema={'contains': {'type': 'string'}, 'minContains': 2})
        self.assertEqual(message, 'Too few items match the given schema (expected at least 2 but only 1 matched)')

    def test_contains_too_few_both_constrained(self):
        message = self.message_for(instance=['foo', 1], schema={'contains': {'type': 'string'}, 'minContains': 2, 'maxContains': 4})
        self.assertEqual(message, 'Too few items match the given schema (expected at least 2 but only 1 matched)')

    def test_contains_too_many(self):
        message = self.message_for(instance=['foo', 'bar', 'baz'], schema={'contains': {'type': 'string'}, 'maxContains': 2})
        self.assertEqual(message, 'Too many items match the given schema (expected at most 2)')

    def test_contains_too_many_both_constrained(self):
        message = self.message_for(instance=['foo'] * 5, schema={'contains': {'type': 'string'}, 'minContains': 2, 'maxContains': 4})
        self.assertEqual(message, 'Too many items match the given schema (expected at most 4)')

    def test_dependentRequired(self):
        message = self.message_for(instance={'foo': {}}, schema={'dependentRequired': {'foo': ['bar']}})
        self.assertEqual(message, "'bar' is a dependency of 'foo'")
