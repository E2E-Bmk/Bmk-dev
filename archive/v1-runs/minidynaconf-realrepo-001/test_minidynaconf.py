#!/usr/bin/env python
"""Test minidynaconf module."""

import os
import sys

# Add solution directory to path
sys.path.insert(0, r'G:\research\01_agents\swe-e2e\Bmk-dev\runs\minidynaconf-realrepo-001\solution-openhands-qwen-001')

from minidynaconf import MiniDynaconf, Validator, ValidationError, SettingsError

def test_basic():
    settings = MiniDynaconf()
    print("Test 1 PASSED: Basic instantiation")

def test_defaults():
    settings = MiniDynaconf(defaults={'DATABASE': {'HOST': 'localhost', 'PORT': 5432}})
    assert settings.DATABASE.HOST == 'localhost'
    assert settings.DATABASE.PORT == 5432
    print("Test 2 PASSED: Defaults with nested access")

def test_attribute_item_access():
    settings = MiniDynaconf(defaults={'DATABASE': {'HOST': 'localhost'}})
    assert settings['DATABASE'].HOST == 'localhost'
    assert settings.get('DATABASE.HOST') == 'localhost'
    print("Test 3 PASSED: Attribute and item access")

def test_case_insensitivity():
    settings = MiniDynaconf(defaults={'DATABASE': {'HOST': 'localhost'}})
    assert settings.database.host == 'localhost'
    assert settings.exists('database.host') == True
    print("Test 4 PASSED: Case insensitivity")

def test_as_dict():
    settings = MiniDynaconf(defaults={'DATABASE': {'HOST': 'localhost'}})
    d = settings.as_dict()
    assert 'DATABASE' in d
    assert 'HOST' in d['DATABASE']
    # Deep copy test
    d['DATABASE']['HOST'] = 'changed'
    assert settings.DATABASE.HOST == 'localhost'
    print("Test 5 PASSED: as_dict with uppercase keys and deep copy")

def test_env_vars():
    os.environ['APP_TEST_VAR'] = 'test_value'
    os.environ['APP_NESTED__KEY'] = 'nested_value'
    settings = MiniDynaconf(envvar_prefix='APP')
    assert settings.TEST_VAR == 'test_value'
    assert settings.exists('NESTED.KEY') == True
    print("Test 6 PASSED: Environment variables")

def test_validators():
    settings = MiniDynaconf(
        defaults={'PORT': 8080},
        validators=[Validator('PORT', is_type_of=int, gte=1, lte=65535)]
    )
    settings.validate()
    print("Test 7 PASSED: Validators")

def test_validation_error():
    try:
        settings = MiniDynaconf(
            defaults={'PORT': 8080},
            validators=[Validator('PORT', is_type_of=int)]
        )
        settings.set('PORT', 'invalid', validate=True)
        print("Test 8 FAILED: Should have raised ValidationError")
    except ValidationError:
        print("Test 8 PASSED: ValidationError raised")

def test_set_get():
    settings = MiniDynaconf()
    settings.set('MY_KEY', 'my_value')
    assert settings.get('MY_KEY') == 'my_value'
    print("Test 9 PASSED: Set and get")

def test_delete():
    settings = MiniDynaconf(defaults={'TEMP_KEY': 'temp_value'})
    assert settings.exists('TEMP_KEY') == True
    settings.delete('TEMP_KEY')
    assert settings.exists('TEMP_KEY') == False
    print("Test 10 PASSED: Delete")

if __name__ == '__main__':
    test_basic()
    test_defaults()
    test_attribute_item_access()
    test_case_insensitivity()
    test_as_dict()
    test_env_vars()
    test_validators()
    test_validation_error()
    test_set_get()
    test_delete()
    print("\nAll tests passed!")