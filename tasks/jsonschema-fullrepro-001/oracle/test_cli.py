from __future__ import annotations

# Rewritten from jsonschema/tests/test_cli.py at the pinned source revision.
from io import StringIO
from json import JSONDecodeError
from textwrap import dedent
from unittest import TestCase
import json
import warnings
from jsonschema import Draft202012Validator, validators
from jsonschema.exceptions import SchemaError, ValidationError
from jsonschema.validators import validate
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    from jsonschema import RefResolutionError, cli

def fake_validator(*errors):
    errors = list(reversed(errors))

    class FakeValidator:

        def __init__(self, *args, **kwargs):
            pass

        def iter_errors(self, instance):
            if errors:
                return errors.pop()
            return []

        @classmethod
        def check_schema(self, schema):
            pass
    return FakeValidator

def fake_open(all_contents):

    def open(path):
        contents = all_contents.get(path)
        if contents is None:
            raise FileNotFoundError(path)
        return StringIO(contents)
    return open

def _message_for(non_json):
    try:
        json.loads(non_json)
    except JSONDecodeError as error:
        return str(error)
    else:
        raise RuntimeError('Tried and failed to capture a JSON dump error.')

class TestCLI(TestCase):

    def run_cli(self, argv, files=None, stdin=StringIO(), exit_code=0, **override):
        arguments = cli.parse_args(argv)
        arguments.update(override)
        self.assertFalse(hasattr(cli, 'open'))
        cli.open = fake_open(files or {})
        try:
            (stdout, stderr) = (StringIO(), StringIO())
            actual_exit_code = cli.run(arguments, stdin=stdin, stdout=stdout, stderr=stderr)
        finally:
            del cli.open
        self.assertEqual(actual_exit_code, exit_code, msg=dedent(f'\n                    Expected an exit code of {exit_code} != {actual_exit_code}.\n\n                    stdout: {stdout.getvalue()}\n\n                    stderr: {stderr.getvalue()}\n                '))
        return (stdout.getvalue(), stderr.getvalue())

    def assertOutputs(self, stdout='', stderr='', **kwargs):
        self.assertEqual(self.run_cli(**kwargs), (dedent(stdout), dedent(stderr)))

    def test_invalid_instance(self):
        error = ValidationError('I am an error!', instance=12)
        self.assertOutputs(files=dict(some_schema='{"does not": "matter since it is stubbed"}', some_instance=json.dumps(error.instance)), validator=fake_validator([error]), argv=['-i', 'some_instance', 'some_schema'], exit_code=1, stderr='12: I am an error!\n')

    def test_invalid_instance_pretty_output(self):
        error = ValidationError('I am an error!', instance=12)
        self.assertOutputs(files=dict(some_schema='{"does not": "matter since it is stubbed"}', some_instance=json.dumps(error.instance)), validator=fake_validator([error]), argv=['-i', 'some_instance', '--output', 'pretty', 'some_schema'], exit_code=1, stderr='                ===[ValidationError]===(some_instance)===\n\n                I am an error!\n                -----------------------------\n            ')

    def test_invalid_instance_explicit_plain_output(self):
        error = ValidationError('I am an error!', instance=12)
        self.assertOutputs(files=dict(some_schema='{"does not": "matter since it is stubbed"}', some_instance=json.dumps(error.instance)), validator=fake_validator([error]), argv=['--output', 'plain', '-i', 'some_instance', 'some_schema'], exit_code=1, stderr='12: I am an error!\n')

    def test_invalid_instance_multiple_errors(self):
        instance = 12
        first = ValidationError('First error', instance=instance)
        second = ValidationError('Second error', instance=instance)
        self.assertOutputs(files=dict(some_schema='{"does not": "matter since it is stubbed"}', some_instance=json.dumps(instance)), validator=fake_validator([first, second]), argv=['-i', 'some_instance', 'some_schema'], exit_code=1, stderr='                12: First error\n                12: Second error\n            ')

    def test_invalid_instance_multiple_errors_pretty_output(self):
        instance = 12
        first = ValidationError('First error', instance=instance)
        second = ValidationError('Second error', instance=instance)
        self.assertOutputs(files=dict(some_schema='{"does not": "matter since it is stubbed"}', some_instance=json.dumps(instance)), validator=fake_validator([first, second]), argv=['-i', 'some_instance', '--output', 'pretty', 'some_schema'], exit_code=1, stderr='                ===[ValidationError]===(some_instance)===\n\n                First error\n                -----------------------------\n                ===[ValidationError]===(some_instance)===\n\n                Second error\n                -----------------------------\n            ')

    def test_multiple_invalid_instances(self):
        first_instance = 12
        first_errors = [ValidationError('An error', instance=first_instance), ValidationError('Another error', instance=first_instance)]
        second_instance = 'foo'
        second_errors = [ValidationError('BOOM', instance=second_instance)]
        self.assertOutputs(files=dict(some_schema='{"does not": "matter since it is stubbed"}', some_first_instance=json.dumps(first_instance), some_second_instance=json.dumps(second_instance)), validator=fake_validator(first_errors, second_errors), argv=['-i', 'some_first_instance', '-i', 'some_second_instance', 'some_schema'], exit_code=1, stderr='                12: An error\n                12: Another error\n                foo: BOOM\n            ')

    def test_custom_error_format(self):
        first_instance = 12
        first_errors = [ValidationError('An error', instance=first_instance), ValidationError('Another error', instance=first_instance)]
        second_instance = 'foo'
        second_errors = [ValidationError('BOOM', instance=second_instance)]
        self.assertOutputs(files=dict(some_schema='{"does not": "matter since it is stubbed"}', some_first_instance=json.dumps(first_instance), some_second_instance=json.dumps(second_instance)), validator=fake_validator(first_errors, second_errors), argv=['--error-format', ':{error.message}._-_.{error.instance}:', '-i', 'some_first_instance', '-i', 'some_second_instance', 'some_schema'], exit_code=1, stderr=':An error._-_.12::Another error._-_.12::BOOM._-_.foo:')

    def test_invalid_schema(self):
        self.assertOutputs(files=dict(some_schema='{"type": 12}'), argv=['some_schema'], exit_code=1, stderr='                12: 12 is not valid under any of the given schemas\n            ')

    def test_invalid_schema_pretty_output(self):
        schema = {'type': 12}
        with self.assertRaises(SchemaError) as e:
            validate(schema=schema, instance='')
        error = str(e.exception)
        self.assertOutputs(files=dict(some_schema=json.dumps(schema)), argv=['--output', 'pretty', 'some_schema'], exit_code=1, stderr='===[SchemaError]===(some_schema)===\n\n' + str(error) + '\n-----------------------------\n')

    def test_invalid_schema_multiple_errors(self):
        self.assertOutputs(files=dict(some_schema='{"type": 12, "items": 57}'), argv=['some_schema'], exit_code=1, stderr="                57: 57 is not of type 'object', 'boolean'\n            ")

    def test_invalid_schema_multiple_errors_pretty_output(self):
        schema = {'type': 12, 'items': 57}
        with self.assertRaises(SchemaError) as e:
            validate(schema=schema, instance='')
        error = str(e.exception)
        self.assertOutputs(files=dict(some_schema=json.dumps(schema)), argv=['--output', 'pretty', 'some_schema'], exit_code=1, stderr='===[SchemaError]===(some_schema)===\n\n' + str(error) + '\n-----------------------------\n')

    def test_invalid_schema_with_invalid_instance(self):
        """
        "Validating" an instance that's invalid under an invalid schema
        just shows the schema error.
        """
        self.assertOutputs(files=dict(some_schema='{"type": 12, "minimum": 30}', some_instance='13'), argv=['-i', 'some_instance', 'some_schema'], exit_code=1, stderr='                12: 12 is not valid under any of the given schemas\n            ')

    def test_invalid_schema_with_invalid_instance_pretty_output(self):
        (instance, schema) = (13, {'type': 12, 'minimum': 30})
        with self.assertRaises(SchemaError) as e:
            validate(schema=schema, instance=instance)
        error = str(e.exception)
        self.assertOutputs(files=dict(some_schema=json.dumps(schema), some_instance=json.dumps(instance)), argv=['--output', 'pretty', '-i', 'some_instance', 'some_schema'], exit_code=1, stderr='===[SchemaError]===(some_schema)===\n\n' + str(error) + '\n-----------------------------\n')

    def test_invalid_instance_continues_with_the_rest(self):
        self.assertOutputs(files=dict(some_schema='{"minimum": 30}', first_instance='not valid JSON!', second_instance='12'), argv=['-i', 'first_instance', '-i', 'second_instance', 'some_schema'], exit_code=1, stderr="                Failed to parse 'first_instance': {}\n                12: 12 is less than the minimum of 30\n            ".format(_message_for('not valid JSON!')))

    def test_custom_error_format_applies_to_schema_errors(self):
        (instance, schema) = (13, {'type': 12, 'minimum': 30})
        with self.assertRaises(SchemaError):
            validate(schema=schema, instance=instance)
        self.assertOutputs(files=dict(some_schema=json.dumps(schema)), argv=['--error-format', ':{error.message}._-_.{error.instance}:', 'some_schema'], exit_code=1, stderr=':12 is not valid under any of the given schemas._-_.12:')

    def test_instance_is_invalid_JSON(self):
        instance = 'not valid JSON!'
        self.assertOutputs(files=dict(some_schema='{}', some_instance=instance), argv=['-i', 'some_instance', 'some_schema'], exit_code=1, stderr=f"                Failed to parse 'some_instance': {_message_for(instance)}\n            ")

    def test_instance_is_invalid_JSON_pretty_output(self):
        (stdout, stderr) = self.run_cli(files=dict(some_schema='{}', some_instance='not valid JSON!'), argv=['--output', 'pretty', '-i', 'some_instance', 'some_schema'], exit_code=1)
        self.assertFalse(stdout)
        self.assertIn('(some_instance)===\n\nTraceback (most recent call last):\n', stderr)
        self.assertNotIn('some_schema', stderr)

    def test_instance_is_invalid_JSON_on_stdin(self):
        instance = 'not valid JSON!'
        self.assertOutputs(files=dict(some_schema='{}'), stdin=StringIO(instance), argv=['some_schema'], exit_code=1, stderr=f'                Failed to parse <stdin>: {_message_for(instance)}\n            ')

    def test_instance_is_invalid_JSON_on_stdin_pretty_output(self):
        (stdout, stderr) = self.run_cli(files=dict(some_schema='{}'), stdin=StringIO('not valid JSON!'), argv=['--output', 'pretty', 'some_schema'], exit_code=1)
        self.assertFalse(stdout)
        self.assertIn('(<stdin>)===\n\nTraceback (most recent call last):\n', stderr)
        self.assertNotIn('some_schema', stderr)

    def test_instance_does_not_exist(self):
        self.assertOutputs(files=dict(some_schema='{}'), argv=['-i', 'nonexisting_instance', 'some_schema'], exit_code=1, stderr="                'nonexisting_instance' does not exist.\n            ")

    def test_instance_does_not_exist_pretty_output(self):
        self.assertOutputs(files=dict(some_schema='{}'), argv=['--output', 'pretty', '-i', 'nonexisting_instance', 'some_schema'], exit_code=1, stderr="                ===[FileNotFoundError]===(nonexisting_instance)===\n\n                'nonexisting_instance' does not exist.\n                -----------------------------\n            ")

    def test_invalid_explicit_base_uri(self):
        schema = '{"$ref": "foo.json#definitions/num"}'
        instance = '1'
        with self.assertRaises(RefResolutionError) as e:
            self.assertOutputs(files=dict(some_schema=schema, some_instance=instance), argv=['-i', 'some_instance', '--base-uri', 'not@UR1', 'some_schema'])
        error = str(e.exception)
        self.assertEqual(error, "unknown url type: 'foo.json'")

    def test_it_validates_using_the_latest_validator_when_unspecified(self):
        self.assertIs(Draft202012Validator, validators.validator_for({}))
        self.assertOutputs(files=dict(some_schema='{"const": "check"}', some_instance='"a"'), argv=['-i', 'some_instance', 'some_schema'], exit_code=1, stdout='', stderr="a: 'check' was expected\n")

    def test_it_validates_using_draft7_when_specified(self):
        """
        Specifically, `const` validation applies for Draft 7.
        """
        schema = '\n            {\n                "$schema": "http://json-schema.org/draft-07/schema#",\n                "const": "check"\n            }\n        '
        instance = '"foo"'
        self.assertOutputs(files=dict(some_schema=schema, some_instance=instance), argv=['-i', 'some_instance', 'some_schema'], exit_code=1, stdout='', stderr="foo: 'check' was expected\n")

    def test_it_validates_using_draft4_when_specified(self):
        """
        Specifically, `const` validation *does not* apply for Draft 4.
        """
        schema = '\n            {\n                "$schema": "http://json-schema.org/draft-04/schema#",\n                "const": "check"\n            }\n            '
        instance = '"foo"'
        self.assertOutputs(files=dict(some_schema=schema, some_instance=instance), argv=['-i', 'some_instance', 'some_schema'], stdout='', stderr='')
