import itertools
import re
import sys
from datetime import datetime, date
from random import choice
from string import ascii_lowercase
import pytest
from pytest import mark
from cerberus import errors, rules_set_registry, Validator
SAMPLE_SCHEMA = {
    'a_string': {'type': 'string', 'minlength': 2, 'maxlength': 10},
    'a_binary': {'type': 'binary', 'minlength': 2, 'maxlength': 10},
    'a_nullable_integer': {'type': 'integer', 'nullable': True},
    'an_integer': {'type': 'integer', 'min': 1, 'max': 100},
    'a_restricted_integer': {'type': 'integer', 'allowed': [-1, 0, 1]},
    'a_boolean': {'type': 'boolean', 'meta': 'can haz two distinct states'},
    'a_datetime': {'type': 'datetime', 'meta': {'format': '%a, %d. %b %Y'}},
    'a_float': {'type': 'float', 'min': 1, 'max': 100},
    'a_number': {'type': 'number', 'min': 1, 'max': 100},
    'a_set': {'type': 'set'},
    'one_or_more_strings': {'type': ['string', 'list'], 'schema': {'type': 'string'}},
    'a_regex_email': {'type': 'string', 'regex': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'},
    'a_readonly_string': {'type': 'string', 'readonly': True},
    'a_restricted_string': {'type': 'string', 'allowed': ['agent', 'client', 'vendor']},
    'an_array': {'type': 'list', 'allowed': ['agent', 'client', 'vendor']},
    'an_array_from_set': {'type': 'list', 'allowed': {'agent', 'client', 'vendor'}},
    'a_list_of_dicts': {'type': 'list', 'schema': {'type': 'dict', 'schema': {'sku': {'type': 'string'}, 'price': {'type': 'integer', 'required': True}}}},
    'a_list_of_values': {'type': 'list', 'items': [{'type': 'string'}, {'type': 'integer'}]},
    'a_list_of_integers': {'type': 'list', 'schema': {'type': 'integer'}},
    'a_dict': {'type': 'dict', 'schema': {'address': {'type': 'string'}, 'city': {'type': 'string', 'required': True}}},
    'a_dict_with_valuesrules': {'type': 'dict', 'valuesrules': {'type': 'integer'}},
    'a_list_length': {'type': 'list', 'schema': {'type': 'integer'}, 'minlength': 2, 'maxlength': 5},
    'a_nullable_field_without_type': {'nullable': True},
    'a_not_nullable_field_without_type': {},
}


def assert_success(document, schema=None, validator=None, update=False):
    validator = validator or Validator(SAMPLE_SCHEMA)
    result = validator(document, schema, update)
    assert isinstance(result, bool)
    if not result:
        raise AssertionError(validator.errors)


assert_success.__test__ = False

def test_empty_field_definition(document):
    field = 'name'
    schema = {field: {}}
    assert_success(document, schema)

def test_nullable_skips_allowed():
    schema = {'role': {'allowed': ['agent', 'client', 'supplier'], 'nullable': True}}
    assert_success({'role': None}, schema)

@mark.parametrize('rule', ('all', 'any', 'none', 'one'))
def test_nullable_skips_of_roles(rule):
    assert_success(schema={'foo': {'type': 'dict', 'nullable': True, rule + 'of_schema': [{'bar': {'type': 'string'}}]}}, document={'foo': None})

def test_integer_allowed():
    assert_success({'a_restricted_integer': -1})

def test_validate_update():
    assert_success({'an_integer': 100, 'a_dict': {'address': 'adr'}, 'a_list_of_dicts': [{'sku': 'let'}]}, update=True)

def test_string():
    assert_success({'a_string': 'john doe'})

def test_string_allowed():
    assert_success({'a_restricted_string': 'client'})

def test_integer():
    assert_success({'an_integer': 50})

def test_boolean():
    assert_success({'a_boolean': True})

def test_datetime():
    assert_success({'a_datetime': datetime.now()})

def test_number():
    assert_success({'a_number': 3.5})
    assert_success({'a_number': 3})

def test_array():
    assert_success({'an_array': ['agent', 'client']})

def test_set():
    assert_success({'a_set': set(['hello', 1])})

def test_a_list_of_dicts():
    assert_success({'a_list_of_dicts': [{'sku': 'AK345', 'price': 100}, {'sku': 'YZ069', 'price': 25}]})

def test_a_list_of_values():
    assert_success({'a_list_of_values': ['hello', 100]})

def test_an_array_from_set():
    assert_success({'an_array_from_set': ['agent', 'client']})

def test_a_list_of_integers():
    assert_success({'a_list_of_integers': [99, 100]})

def test_empty_skips_regex(validator):
    schema = {'foo': {'empty': True, 'regex': '\\d?\\d\\.\\d\\d', 'type': 'string'}}
    assert validator({'foo': ''}, schema)

def test_unknown_key_dict(validator):
    validator.allow_unknown = True
    document = {'a_dict': {'foo': 'foo_value', 'bar': 25}}
    assert_success(document, {}, validator=validator)

def test_unknown_key_list(validator):
    validator.allow_unknown = True
    document = {'a_dict': ['foo', 'bar']}
    assert_success(document, {}, validator=validator)

def test_unknown_keys_list_of_dicts(validator):
    validator.allow_unknown = True
    document = {'a_list_of_dicts': [{'sku': 'YZ069', 'price': 25, 'extra': True}]}
    assert_success(document, validator=validator)

def test_callable_validator():
    """
    Validator instance is callable, functions as a shorthand
    passthrough to validate()
    """
    schema = {'test_field': {'type': 'string'}}
    v = Validator(schema)
    assert v.validate({'test_field': 'foo'})
    assert v({'test_field': 'foo'})
    assert not v.validate({'test_field': 1})
    assert not v({'test_field': 1})

def test_options_passed_to_nested_validators(validator):
    validator.schema = {'sub_dict': {'type': 'dict', 'schema': {'foo': {'type': 'string'}}}}
    validator.allow_unknown = True
    assert_success({'sub_dict': {'foo': 'bar', 'unknown': True}}, validator=validator)

def test_validated(validator):
    validator.schema = {'property': {'type': 'string'}}
    document = {'property': 'string'}
    assert validator.validated(document) == document
    document = {'property': 0}
    assert validator.validated(document) is None

@mark.skipif(sys.version_info[0] < 3, reason='requires python 3.x')
def test_unicode_allowed_py3():
    """
    All strings are unicode in Python 3.x. Input doc and schema have equal strings and
    validation yield success.
    """
    doc = {'letters': u'♄εℓł☺'}
    schema = {'letters': {'type': 'string', 'allowed': ['♄εℓł☺']}}
    assert_success(doc, schema)

def test_anyof_type():
    schema = {'anyof_type': {'anyof_type': ['string', 'integer']}}
    assert_success({'anyof_type': 'bar'}, schema)
    assert_success({'anyof_type': 23}, schema)

def test_nested_oneof_type():
    schema = {'nested_oneof_type': {'valuesrules': {'oneof_type': ['string', 'integer']}}}
    assert_success({'nested_oneof_type': {'foo': 'a'}}, schema)
    assert_success({'nested_oneof_type': {'bar': 3}}, schema)

def test_issue_107(validator):
    schema = {'info': {'type': 'dict', 'schema': {'name': {'type': 'string', 'required': True}}}}
    document = {'info': {'name': 'my name'}}
    assert_success(document, schema, validator=validator)
    v = Validator(schema)
    assert_success(document, schema, v)
    assert v.validate(document)

def test_schema_validation_from_rules_set():
    rules_set_registry.add('addr', {'type': 'dict', 'schema': {'address': {'type': 'string'}, 'city': {'type': 'string', 'required': True}}})
    Validator(schema={'a_dict': 'addr'}).validate({'a_dict': {'address': 'my address', 'city': 'my town'}})


def test_required_field_rejects_missing_and_accepts_present():
    validator = Validator({'name': {'type': 'string', 'required': True}})
    assert not validator.validate({})
    assert validator.validate({'name': 'Ada'})


def test_require_all_applies_to_all_schema_fields():
    validator = Validator(
        {'name': {'type': 'string'}, 'age': {'type': 'integer'}},
        require_all=True,
    )
    assert not validator.validate({'name': 'Ada'})
    assert validator.validate({'name': 'Ada', 'age': 37})


def test_update_mode_allows_missing_required_fields():
    validator = Validator({'name': {'type': 'string', 'required': True}})
    assert not validator.validate({})
    assert validator.validate({}, update=True)
