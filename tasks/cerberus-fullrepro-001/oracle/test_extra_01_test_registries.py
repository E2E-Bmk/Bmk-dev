import pytest

from cerberus import SchemaError, schema_registry, rules_set_registry, Validator


def assert_success(document, schema=None, validator=None, update=False):
    validator = validator or Validator()
    result = validator(document, schema, update)
    assert isinstance(result, bool)
    if not result:
        raise AssertionError(validator.errors)


def assert_normalized(document, expected, schema=None, validator=None):
    validator = validator or Validator()
    assert_success(document, schema, validator)
    assert validator.document == expected


def assert_schema_error(document, schema=None, validator=None):
    validator = validator or Validator()
    with pytest.raises(SchemaError):
        validator(document, schema)


assert_success.__test__ = False
assert_normalized.__test__ = False
assert_schema_error.__test__ = False

def test_schema_registry_simple():
    schema_registry.add('foo', {'bar': {'type': 'string'}})
    schema = {'a': {'schema': 'foo'}, 'b': {'schema': 'foo'}}
    document = {'a': {'bar': 'a'}, 'b': {'bar': 'b'}}
    assert_success(document, schema)

def test_top_level_reference():
    schema_registry.add('peng', {'foo': {'type': 'integer'}})
    document = {'foo': 42}
    assert_success(document, 'peng')

def test_recursion():
    rules_set_registry.add('self', {'type': 'dict', 'allow_unknown': 'self'})
    v = Validator(allow_unknown='self')
    assert_success({0: {1: {2: {}}}}, {}, v)

def test_references_remain_unresolved(validator):
    rules_set_registry.extend((('boolean', {'type': 'boolean'}), ('booleans', {'valuesrules': 'boolean'})))
    validator.schema = {'foo': 'booleans'}
    assert 'booleans' == validator.schema['foo']
    assert validator.validate({'foo': {'enabled': True}})
    assert not validator.validate({'foo': {'enabled': 'yes'}})

def test_rules_registry_with_anyof_type():
    rules_set_registry.add('string_or_integer', {'anyof_type': ['string', 'integer']})
    schema = {'soi': 'string_or_integer'}
    assert_success({'soi': 'hello'}, schema)

def test_schema_registry_with_anyof_type():
    schema_registry.add('soi_id', {'id': {'anyof_type': ['string', 'integer']}})
    schema = {'soi': {'schema': 'soi_id'}}
    assert_success({'soi': {'id': 'hello'}}, schema)

def test_normalization_with_rules_set():
    rules_set_registry.add('foo', {'default': 42})
    assert_normalized({}, {'bar': 42}, {'bar': 'foo'})
    rules_set_registry.add('foo', {'default_setter': lambda _: 42})
    assert_normalized({}, {'bar': 42}, {'bar': 'foo'})
    rules_set_registry.add('foo', {'type': 'integer', 'nullable': True})
    assert_success({'bar': None}, {'bar': 'foo'})

def test_rules_set_with_dict_field():
    document = {'a_dict': {'foo': 1}}
    schema = {'a_dict': {'type': 'dict', 'schema': {'foo': 'rule'}}}
    rules_set_registry.add('rule', {'tüpe': 'integer'})
    assert_schema_error(document, schema)
    rules_set_registry.add('rule', {'type': 'integer'})
    assert_success(document, schema)
