# Cerberus Specification

## Product Overview

Cerberus is a lightweight Python validation and normalization library for mapping-like documents. A user defines a validation schema, creates a `Validator`, and validates dictionaries against that schema. Validation does not stop at the first issue; it processes the document and exposes collected errors. The same validator can also return a normalized document after applying renaming, default values, coercion, and purging rules.

The core contract is the relationship between a schema, an input document, a processed document, and the error outputs that describe why validation failed.

## Scope

This specification covers the public behavior needed to implement normal Cerberus usage:

- top-level imports: `Validator`, `DocumentError`, `SchemaError`, `TypeDefinition`, `schema_registry`, `rules_set_registry`, and `__version__`;
- validator construction, `validate`, call shorthand, `validated`, `normalized`, `document`, `errors`, and main configuration options;
- validation schemas, schema validation, rules set and schema registries;
- validation rules for required fields, types, allowed and forbidden values, ranges, lengths, regular expressions, dependencies, exclusion, nested mappings, sequences, mapping keys and values, and `*of` combinations;
- normalization rules for renaming, purging, defaults, default setters, and coercion;
- custom validators, custom rules, custom type definitions, custom checkers, coercers, default setters, and custom error handlers;
- public error representations and error tree access used by applications.

This specification does not require matching private implementation storage, private helper methods, exact `repr()` output, exact default error message wording, source file layout, or tests that directly assert private attributes.

## Installable Surface

The package name is `cerberus`. Public import styles include:

```python
import cerberus
from cerberus import Validator, DocumentError, SchemaError, TypeDefinition
from cerberus import schema_registry, rules_set_registry
from cerberus.errors import BasicErrorHandler, BaseErrorHandler, ValidationError
```

Documented modules include `cerberus.validator`, `cerberus.schema`, `cerberus.errors`, and `cerberus.utils`.

## Quick Start

Create a validator with a schema and validate a mapping:

```python
from cerberus import Validator

schema = {"name": {"type": "string"}}
v = Validator(schema)

assert v.validate({"name": "john doe"}) is True
assert v.validate({"name": 42}) is False
errors = v.errors
```

A validator instance is callable and behaves like `validate(document, *args, **kwargs)`.

## Validator Construction

`Validator` accepts an optional schema and keyword configuration. Important public options include:

- `schema`: validation schema for documents;
- `allow_unknown`: whether fields absent from the schema are allowed, or a rule set used to validate unknown fields;
- `require_all`: whether all schema-defined fields are required by default;
- `purge_unknown`: whether unknown fields are removed during normalization;
- `purge_readonly`: whether readonly fields are removed during normalization;
- `ignore_none_values`: whether `None` values are ignored during validation;
- `error_handler`: error handler class, instance, or `(class, kwargs)` tuple;
- `schema_registry` and `rules_set_registry`: registries used to resolve named schema or rule-set references.

Additional keyword arguments not used by Cerberus are stored as validator configuration for custom validators and child validators.

Assigning a new value to `schema`, `allow_unknown`, `require_all`, `purge_unknown`, `purge_readonly`, `ignore_none_values`, or `error_handler` changes subsequent processing. Invalid validation schemas raise `SchemaError`.

## Validation Workflow

`validate(document, schema=None, update=False, normalize=True)` validates a mapping document. When `schema` is supplied, it is used for that call. The method returns `True` when the document is valid and `False` otherwise. A non-mapping document raises `DocumentError`.

Validation processes the whole document and records all applicable errors. After validation:

- `document` contains the normalized and processed document when normalization ran;
- `errors` contains the error handler output;
- `document_error_tree` and `schema_error_tree` expose public Python error trees for applications that use the documented error interfaces.

When `update=True`, missing required fields are not treated as validation errors. Type validation is performed before most other rules for the same field. If a field fails type validation, later validation rules for that field are skipped, but other fields continue processing.

`validated(document, schema=None, always_return_document=False, **kwargs)` returns the processed document when validation succeeds. If validation fails it returns `None` unless `always_return_document=True`, in which case it returns the processed document even with errors.

`normalized(document, schema=None, **kwargs)` returns a normalized copy of a document without requiring full validation success. Normalization does not mutate the caller's original input document.

## Validation Schemas

A validation schema is a mapping. Schema keys are document field names. Schema values are rule sets, normally dictionaries whose keys are rule names.

By default schema-defined fields are optional. A field becomes mandatory when its rule set contains `required: True`, or when the validator or nested rule context uses `require_all=True`.

Schemas are validated when they are assigned to a validator or when top-level field rule sets are replaced through the schema mapping interface. Invalid schemas raise `SchemaError`. Mutating deeply nested data inside a schema may require an explicit schema validation call to detect invalid constraints.

Schemas use ordinary Python data structures and may be serialized with standard serializers as long as the decoder produces dictionaries, lists, strings, numbers, booleans, and similar values.

## Registries

`schema_registry` and `rules_set_registry` are default module-level registries. A `Registry` stores named definitions with operations such as `add`, `extend`, `get`, `remove`, `clear`, and `all`.

A schema can refer to a named schema or named rules set stored in a registry. This supports reusable definitions and recursive schemas. A validator can use the default registries or custom registry instances supplied at construction or assigned to the validator.

## Unknown Fields

By default, document fields not declared in the schema are invalid.

`allow_unknown=True` accepts unknown fields. `allow_unknown=False` rejects them. When `allow_unknown` is a rule set, unknown fields are validated against that rule set.

For nested dictionaries validated with a `schema` rule, `allow_unknown` may also be set inside the field definition to override the nested validator's behavior. Nested `allow_unknown` takes precedence over purging unknown fields for that nested document.

`purge_unknown=True` removes unknown fields during normalization unless that nested context explicitly allows unknown fields.

## Required Fields

`required: True` makes a field mandatory unless validation is performed as an update. `require_all=True` makes all schema-defined fields required by default. A nested dictionary with a `schema` rule can use `require_all` to require all fields in that nested schema.

The `required` rule checks field presence. It is separate from rules such as `dependencies` and `empty`.

## Type Checking

The `type` rule restricts the allowed Python type. Built-in type names include:

- `boolean`;
- `binary`;
- `date`;
- `datetime`;
- `dict`;
- `float`;
- `integer`;
- `list`;
- `number`;
- `set`;
- `string`.

A list of type names accepts a value matching any listed type. `number` accepts integers and floats but not booleans. `list` accepts non-string sequences. `dict` accepts mapping-like values.

The list of supported types can be extended with `TypeDefinition` and a validator's `types_mapping`.

## Common Validation Rules

`allowed` accepts values in a provided container. For iterable field values, all members must be allowed. `forbidden` rejects values in a provided container.

`min` and `max` compare values with lower and upper bounds. `minlength` and `maxlength` apply to sized values. `empty: False` rejects empty iterable values. `empty: True` treats empty values as accepted for rules such as allowed, forbidden, items, length, regex, and checkers.

`regex` validates string values with a regular expression match. Patterns are intended for complete string matching and a trailing `$` is ensured if missing.

`nullable: True` allows `None`; otherwise `None` is invalid unless ignored by validator configuration.

`readonly: True` makes a field invalid when supplied by a document. With `purge_readonly=True`, readonly fields are removed during normalization instead.

`meta` stores application-specific metadata in a field rule set and has no validation effect.

## Cross-Field Rules

`dependencies` requires other fields to be present when the current field is present. The constraint may be a field name, a sequence of field names, or a mapping from field names to allowed values. Dependencies may address nested document fields with dot notation. A dependency path starting with `^` is interpreted from the document root.

`excludes` declares fields that cannot coexist with the current field. The constraint may be one field name or a list of field names. Combining `excludes` with `required` can express exclusive-or style schemas.

## Nested Data Rules

For a field whose value is a mapping, `schema` with a dictionary constraint validates that mapping as a nested document.

For a field whose value is a sequence, `schema` with a rule-set constraint validates every element of the sequence. This is the preferred way to validate variable-length lists.

`items` validates fixed-position items in an iterable against a sequence of rule sets. It applies only when the value has the same length as the item definition.

`keysrules` validates all keys of a mapping against a rule set. `valuesrules` validates all values of a mapping against a rule set.

## Of-Rules

`allof`, `anyof`, `oneof`, and `noneof` validate a field against multiple rule sets:

- `allof`: all rule sets must validate;
- `anyof`: at least one rule set must validate;
- `oneof`: exactly one rule set must validate;
- `noneof`: no rule set may validate.

Normalization rules inside `*of` rule definitions are not processed.

Shortcut forms such as `anyof_regex` are equivalent to an `anyof` rule with several definitions, each containing the named rule.

## Normalization

Normalization is applied to a copy of the document, depth first through nested mappings. Normalization rules also apply in nested `schema` definitions, sequence `schema` definitions, `allow_unknown` rule sets, `keysrules`, and `valuesrules` where applicable. Normalization rules inside `*of` definitions are not processed.

`rename` renames a field before further processing.

`rename_handler` applies a callable or named custom method to field names. A sequence of handlers is applied in order.

`purge_unknown=True` removes unknown fields after renaming, unless unknown fields are allowed in the current nested context.

`default` supplies a value for a missing field or a field whose value is `None`.

`default_setter` calls a function or named custom method with the current document to compute a missing default. If default setters have circular or unresolvable dependencies, normalization fails and records an error.

`coerce` applies a callable, named custom coercer, or sequence of coercers to a value before validation. The returned value replaces the old value in the processed document. If coercion raises an exception, validation fails for that field and records an error.

## Custom Validation

`check_with` validates a field by calling a standalone function or a validator method. A standalone function has the signature `(field, value, error)` and calls `error(field, message)` when invalid. A method checker is referenced by a string and implemented on a validator subclass with the `_check_with_<name>` naming convention. A sequence of functions and names runs them consecutively.

A custom validation rule is implemented by subclassing `Validator` and defining `_validate_<rule_name>(constraint, field, value)`. Spaces in schema rule names correspond to underscores in method names. The method may call `_error(field, message)` to record a validation error. A rule method docstring can include a schema for validating that rule's constraint.

Custom type support is added with `TypeDefinition(name, included_types, excluded_types)` and the validator class or instance `types_mapping`. Subclasses should usually copy the base mapping before adding custom names.

Custom coercers use `_normalize_coerce_<name>(value)`. Custom default setters use `_normalize_default_setter_<name>(document)`. Custom rename handlers use the same named-handler mechanism documented for normalization.

Custom validators may receive arbitrary configuration keyword arguments. This configuration is available to child validators used for nested processing.

## Errors

`errors` returns the configured error handler output. The default `BasicErrorHandler` returns a dictionary keyed by document field names. Values are lists of messages or nested error dictionaries for nested fields. The exact wording of default messages is not part of this specification.

`ValidationError` objects expose:

- `document_path`;
- `schema_path`;
- `code`;
- `rule`;
- `constraint`;
- `value`;
- `info`.

`document_error_tree` and `schema_error_tree` allow dictionary-like traversal by document or schema path. Tree nodes can be queried with an error definition or a child key, tested with `in`, iterated, and inspected through their `errors` property.

`BaseErrorHandler` defines the error handler interface. `BasicErrorHandler` is the default dictionary-oriented handler. A validator accepts an error handler class, instance, or `(class, kwargs)` tuple.

## Error Semantics

Validation reports user-facing failures through boolean validation results, normalized documents, error handler outputs, public error trees, and documented exception classes. Invalid input documents raise `DocumentError`; invalid validation schemas raise `SchemaError`; field-level validation failures are accumulated in `errors` rather than stopping the whole validation run. Exact message wording is not part of the public contract.

## Exceptions

`DocumentError` is raised when a document passed for processing is not a mapping.

`SchemaError` is raised when an invalid validation schema is assigned or used.

## Cross-View Invariants

- `validate`, `validated`, `normalized`, `document`, `errors`, and error trees must describe the same processed document state after a validation run.
- Schema rules used through a validator instance, a per-call schema, named registries, and nested schema references must produce consistent validation behavior.
- Normalization, validation, custom coercers, default setters, and custom validators must update public document and error projections consistently.
- Unknown-field, required-field, nested-document, and type-rule behavior must agree across direct validation and nested validation contexts.
- Custom error handlers may change error presentation without changing whether a document is valid.
- Public exception classes distinguish invalid documents and invalid schemas from ordinary validation failures.

## Non-Goals

The candidate implementation does not need to reproduce private attributes, private helper methods, internal caches, exact object representation strings, exact default error message text, deprecated aliases unless described above, or behavior that is only observable by inspecting source internals.


## Evaluation Notes

Compatibility checks focus on public validator construction, schema rules, normalization, validation results, error reporting, registries, custom validation hooks, and cross-view consistency between processed documents and errors. They do not require private attributes, private helper methods, source layout, exact `repr()` output, or exact default message text.
