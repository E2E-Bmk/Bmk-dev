# GraphQL Schema Change Analysis Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## 1. Product Overview

`@graphql-inspector/core` is a TypeScript library that answers four questions about a GraphQL
schema and the documents written against it.

1. **What changed, and how dangerous is it?** Given two schemas, the library produces a flat,
   ordered list of *change records*. Each record names a machine-readable change type, the schema
   path it applies to, a *criticality* grade (breaking, dangerous, or non-breaking), a
   human-readable message, and a structured `meta` payload carrying exactly the facts a consumer
   needs to re-derive the message or re-grade the change.
2. **What part of the schema is actually used?** Given a schema and a set of executable documents,
   the library produces a *coverage report*: per type, per field and per argument hit counts, the
   source locations of every hit, and aggregate statistics.
3. **Which types look like duplicates of each other?** Given a schema, the library rates every type
   against every other type of the same kind using a string-similarity measure over their printed
   definitions, and reports the best match and the runners-up above a threshold.
4. **Are these documents valid against this schema?** Given a schema and a set of documents, the
   library reports per-document validation errors, deprecated-usage warnings, and violations of
   configurable query-complexity limits.

The three later projections exist independently, but they are not isolated from the first. The
`considerUsage` diff rule makes schema comparison consume real usage data: a breaking change to a
coordinate that nobody queries is downgraded to dangerous. That coupling is the reason the four
projections belong in one package rather than four.

The library computes; it does not fetch. It never reads a file, opens a socket, or resolves a
schema from a URL. Every input is an in-memory `GraphQLSchema`, `Source`, or plain object supplied
by the caller, and `graphql` is a peer dependency rather than a bundled one.

The delivery boundary is exactly one npm package named `@graphql-inspector/core`. A command-line
program, schema loader, CI integration, or hosted service that sits on top of it is not described
here.

## 2. Non-Goals

- This specification does not define the exact wording of `Change.message` or of
  `Change.criticality.reason`, with two exceptions that are stated explicitly in §6.4 and §6.8
  because those two rules *replace* or *extend* text that a consumer observes. Everywhere else,
  the contract is which change type is emitted, at which path, at which criticality level, whether
  a reason is present, and what `meta` contains.
- This specification does not require any command-line interface, executable, or binary entry
  point. The package ships a library only.
- This specification does not require schema loading, introspection execution, HTTP transport, file
  reading, or any other form of I/O. The implementation must perform no network access at any time.
- This specification does not define the behaviour of the `ignoreDirectives` diff rule beyond the
  pass-through case stated in §6.7.
- This specification does not require a stable ordering between change records produced from
  *different* top-level schema regions beyond the ordering rules given in §5.2.
- This specification does not define behaviour for schemas that fail `graphql`'s own validity
  checks; every input schema is assumed to be a schema that `graphql` itself accepts.
- This specification does not require compatibility with any GraphQL implementation other than the
  `graphql` package versions named in Appendix A.
- This specification does not define a plugin system, a configuration file format, or an
  environment-variable interface.

## 3. Representative Workflows

### 3.1 Reviewing a proposed schema change before release

A release engineer holds the schema currently in production and the schema a pull request proposes.
They call `diff(oldSchema, newSchema)` and receive a promise of change records. They filter for
`criticality.level === CriticalityLevel.Breaking`; if the list is empty the change ships
automatically. When it is not empty, each record's `path` tells them exactly which coordinate
regressed (`User.email`, `@auth.role`, `SearchResult`), and `meta` gives them the old and new types
so they can render a review comment without re-parsing anything.

The same engineer knows that some breakages are theoretical. They re-run the comparison as
`diff(oldSchema, newSchema, [DiffRule.considerUsage], { checkUsage })`, where `checkUsage` is an
async function they wrote that asks their own telemetry store whether a coordinate has been
requested in the last thirty days. Coordinates that nobody uses come back as dangerous rather than
breaking, with `criticality.isSafeBasedOnUsage` set and the message annotated.

### 3.2 Measuring which parts of a schema clients exercise

An API owner has the schema and a directory of `.graphql` documents that their clients ship. They
build a `Source` for each document and call `coverage(schema, sources)`. The returned report tells
them, per type and per field, how many times it was selected and from which document and character
offsets. The `stats` block gives them the headline numbers — how many types exist, how many were
touched at all, how many were touched completely, how many root fields exist per operation kind and
how many of those were used. Fields with a hit count of zero are deprecation candidates.

### 3.3 Validating stored operations against a schema

A gateway maintainer keeps a persisted-operation store. Before deploying a new schema they call
`validate(schema, sources, { maxDepth: 10, maxTokenCount: 800 })`. They get back one
`InvalidDocument` per document that has a problem: standard GraphQL validation errors, plus
deprecation warnings collected separately so they can be reported without failing the build, plus
errors for documents that exceed the configured depth, alias, directive, token or complexity
budgets. Documents that pass everything are simply absent from the result.

### 3.4 Finding near-duplicate types

A schema owner suspects that two teams independently modelled the same concept. They call
`similar(schema, undefined)` and receive a map from type name to its best match and the other
candidates above the default threshold. Passing a type name in place of `undefined` narrows the
report to a single type; raising the third argument suppresses coincidental matches.

## 4. Core Concepts and the Shared Data Model

### 4.1 Criticality

Every change record carries a criticality grade. `CriticalityLevel` is an enumeration with exactly
three members:

| Member | String value | Meaning |
| --- | --- | --- |
| `Breaking` | `BREAKING` | Existing valid client operations must be assumed to break. |
| `Dangerous` | `DANGEROUS` | Existing operations remain valid, but observable behaviour must be assumed to change. |
| `NonBreaking` | `NON_BREAKING` | Existing operations remain valid and behave as before. |

`Criticality` is an object with a required `level` of type `CriticalityLevel`, an optional `reason`
of type `string`, and an optional `isSafeBasedOnUsage` of type `boolean`. Whether a reason is
present is part of the contract and is stated per change type in §5; the wording is not.
`isSafeBasedOnUsage` is never set by the comparison of §5; only the rule of §6.8 sets it.

### 4.2 The change record

`Change` is generic in the change type it describes, and its `meta` is the payload declared for that
change type in §5:

```ts
interface Change<T extends ChangeType = any> {
  message: string;
  path?: string;
  type: T;
  meta: /* the meta payload declared for T in §5 */;
  criticality: Criticality;
}
```

- `type` is the `ChangeType` member that identifies the change. It is the string value, not the key.
- `path` is a dot-joined schema coordinate. It is absent for exactly the three schema-root change
  types listed in §5.3 and present for every other change type.
- `criticality` grades the change as defined in §4.1.
- `message` is a human-readable sentence.
- `meta` is a per-change-type record of primitive facts. Its field names and types are fixed per
  change type and are the sole input to the serializable-record builders of §7. Where §5 lists a
  `meta` member without a type, that member's type is `string`.

`TypeOfChangeType` is not generic. It is a type alias for the union of the 80 `ChangeType` string
values — the same union that the `ChangeType` type alias names.

### 4.3 Change types

`ChangeType` is a frozen object of exactly 80 members. Its keys are upper-camel-case identifiers;
each key's value is that key rewritten into upper snake case, which is to say: an underscore is
inserted at every position where a lowercase letter or digit is immediately followed by an
uppercase letter, and the whole string is then uppercased. `FieldArgumentDescriptionChanged` maps
to `FIELD_ARGUMENT_DESCRIPTION_CHANGED`; `DirectiveUsageInputFieldDefinitionRemoved` maps to
`DIRECTIVE_USAGE_INPUT_FIELD_DEFINITION_REMOVED`. There is no member for which this derivation
fails. `ChangeType` is also exported as a type alias naming the union of those 80 string values.

The 80 keys, grouped by the schema element they describe:

| Group | Keys |
| --- | --- |
| Field argument | `FieldArgumentDescriptionChanged`, `FieldArgumentDefaultChanged`, `FieldArgumentTypeChanged` |
| Directive definition | `DirectiveRemoved`, `DirectiveAdded`, `DirectiveDescriptionChanged`, `DirectiveLocationAdded`, `DirectiveLocationRemoved`, `DirectiveArgumentAdded`, `DirectiveArgumentRemoved`, `DirectiveArgumentDescriptionChanged`, `DirectiveArgumentDefaultValueChanged`, `DirectiveArgumentTypeChanged`, `DirectiveRepeatableAdded`, `DirectiveRepeatableRemoved` |
| Enum | `EnumValueRemoved`, `EnumValueAdded`, `EnumValueDescriptionChanged`, `EnumValueDeprecationReasonChanged`, `EnumValueDeprecationReasonAdded`, `EnumValueDeprecationReasonRemoved` |
| Field | `FieldRemoved`, `FieldAdded`, `FieldDescriptionChanged`, `FieldDescriptionAdded`, `FieldDescriptionRemoved`, `FieldDeprecationAdded`, `FieldDeprecationRemoved`, `FieldDeprecationReasonChanged`, `FieldDeprecationReasonAdded`, `FieldDeprecationReasonRemoved`, `FieldTypeChanged`, `FieldArgumentAdded`, `FieldArgumentRemoved` |
| Input object | `InputFieldRemoved`, `InputFieldAdded`, `InputFieldDescriptionAdded`, `InputFieldDescriptionRemoved`, `InputFieldDescriptionChanged`, `InputFieldDefaultValueChanged`, `InputFieldTypeChanged` |
| Interface implementation | `ObjectTypeInterfaceAdded`, `ObjectTypeInterfaceRemoved` |
| Schema roots | `SchemaQueryTypeChanged`, `SchemaMutationTypeChanged`, `SchemaSubscriptionTypeChanged` |
| Type | `TypeRemoved`, `TypeAdded`, `TypeKindChanged`, `TypeDescriptionChanged`, `TypeDescriptionRemoved`, `TypeDescriptionAdded` |
| Union | `UnionMemberRemoved`, `UnionMemberAdded` |
| Directive usage | `DirectiveUsageUnionMemberAdded`, `DirectiveUsageUnionMemberRemoved`, `DirectiveUsageEnumAdded`, `DirectiveUsageEnumRemoved`, `DirectiveUsageEnumValueAdded`, `DirectiveUsageEnumValueRemoved`, `DirectiveUsageInputObjectAdded`, `DirectiveUsageInputObjectRemoved`, `DirectiveUsageFieldAdded`, `DirectiveUsageFieldRemoved`, `DirectiveUsageScalarAdded`, `DirectiveUsageScalarRemoved`, `DirectiveUsageObjectAdded`, `DirectiveUsageObjectRemoved`, `DirectiveUsageInterfaceAdded`, `DirectiveUsageInterfaceRemoved`, `DirectiveUsageArgumentDefinitionAdded`, `DirectiveUsageArgumentDefinitionRemoved`, `DirectiveUsageSchemaAdded`, `DirectiveUsageSchemaRemoved`, `DirectiveUsageFieldDefinitionAdded`, `DirectiveUsageFieldDefinitionRemoved`, `DirectiveUsageInputFieldDefinitionAdded`, `DirectiveUsageInputFieldDefinitionRemoved`, `DirectiveUsageArgumentAdded`, `DirectiveUsageArgumentRemoved` |

### 4.4 Type-change safety

Two derived predicates decide the criticality of every type change. They are not exported, but
their results appear in `meta` and are therefore observable.

**Output position (covariance).** A change from an old output type to a new output type is safe
when one of the following holds, evaluated in order:

1. Neither the old nor the new type is a list or a non-null wrapper, and their printed names are
   equal.
2. The new type is non-null, and the old type unwrapped of any non-null is a safe change to the new
   type unwrapped of its non-null.
3. The old type is a list, and either the new type is also a list whose item type is a safe change
   from the old item type, or the new type is a non-null whose inner type is a safe change from the
   old list.

Otherwise the change is unsafe.

**Input position (contravariance).** A change from an old input type to a new input type is safe
when one of the following holds, evaluated in order:

1. Neither side is a list or a non-null wrapper, and their printed names are equal.
2. The old type is non-null and the new type is that same type without the non-null wrapper, or
   more generally the change from the old type's inner type to the new type is safe.
3. Both sides are lists and the change between their item types is safe.

Otherwise the change is unsafe. In particular, adding a non-null wrapper in input position is
unsafe while removing one is safe, which is the mirror image of the output rule.

### 4.5 Default-value comparison

Two default values are equal when they are strictly equal by `Object.is`, or when both are arrays of
equal length whose elements are pairwise equal by this same rule, or when both are non-null objects
with the same set of own keys whose values are pairwise equal by this same rule. Any other pair is
unequal. A field or argument has a default value when its `defaultValue` is not `undefined`.

### 4.6 Deprecation

A field, argument, input field or enum value is deprecated when its deprecation reason is a string.
The string `No longer supported` is the default reason that `graphql` supplies when
`@deprecated` carries no explicit argument; wherever this specification compares two deprecation
reasons, that exact string is treated as equivalent to no reason at all.

## 5. Projection One — Schema Comparison

### 5.1 Entry point

`diff` takes four parameters in this order: `oldSchema`, of type `GraphQLSchema | null`, required;
`newSchema`, of type `GraphQLSchema | null`, required; `rules`, an array of `Rule`, optional with a
default of the empty array; and `config`, of type `ConsiderUsageConfig`, optional. It returns
`Promise<Change[]>`.

`diff` computes the raw change list by walking the two schemas as described in §5.2, then applies
each entry of `rules` in array order. Each rule receives the change list produced by its
predecessor, so rules compose left to right. A rule that returns a promise is awaited before the
next rule runs. The array returned by the last rule, or the raw list when `rules` is empty, is the
resolved value.

`config` is forwarded unchanged to every rule as the `config` member of the rule input. It is
required only by the rules that read it; §6 states which those are.

### 5.2 Traversal and ordering

The raw change list is produced by visiting five regions in this fixed order.

1. **Directive definitions.** The directive lists of the two schemas, each filtered to exclude
   directives that `graphql` itself specifies, are compared by directive name.
2. **Schema root types.** The query, mutation and subscription root types are compared by name.
3. **Named types.** The two type maps, each filtered to exclude the five built-in scalar types
   (`String`, `Int`, `Float`, `Boolean`, `ID`) and the introspection types (every type whose name
   begins with a double underscore), are compared by type name.
4. **Schema-level directive usages.** The directive nodes attached to the schema definition node
   are compared.
5. **Schema extension directive usages.** For each index of the schema's extension nodes, the
   directive nodes attached to that extension are compared, in index order.

Wherever this specification says two collections are "compared" by a key, the comparison must
produce, in this order: one *removed* outcome for every key present only in the old collection, in
the old collection's iteration order; one *added* outcome for every key present only in the new
collection, in the new collection's iteration order; and one *mutual* outcome for every key present
in both, in the new collection's iteration order.

Wherever a type or member exists on only one side, the walk still recurses into it: a type added to
the new schema emits `TypeAdded` and then also emits the per-member added changes for everything
inside it, each carrying the flag that records that the parent is itself new. That flag is what
downgrades those inner changes to non-breaking, and §5.5 through §5.11 name it per change type.

### 5.3 Schema root changes

| Change type | Emitted when | Criticality | Reason present | Path | `meta` |
| --- | --- | --- | --- | --- | --- |
| `SchemaQueryTypeChanged` | The query root type name differs between the schemas | `NonBreaking` when the old name is `null`, otherwise `Breaking` | yes | *(absent)* | `oldQueryTypeName: string \| null`, `newQueryTypeName: string \| null` |
| `SchemaMutationTypeChanged` | The mutation root type name differs | `NonBreaking` when the old name is `null`, otherwise `Breaking` | yes | *(absent)* | `oldMutationTypeName: string \| null`, `newMutationTypeName: string \| null` |
| `SchemaSubscriptionTypeChanged` | The subscription root type name differs | `NonBreaking` when the old name is `null`, otherwise `Breaking` | yes | *(absent)* | `oldSubscriptionTypeName: string \| null`, `newSubscriptionTypeName: string \| null` |

These three change types are the only ones that omit `path`.

### 5.4 Named-type changes

Path is the type name for every row.

| Change type | Emitted when | Criticality | Reason present | `meta` |
| --- | --- | --- | --- | --- |
| `TypeRemoved` | A type exists in the old schema only | `Breaking` | yes | `removedTypeName: string` |
| `TypeAdded` | A type exists in the new schema only | `NonBreaking` | no | `addedTypeName: string`, `addedTypeKind: string`, and additionally `addedTypeIsOneOf: boolean` when — and only when — the added type is an input object |
| `TypeKindChanged` | A type of the same name has a different kind in each schema | `Breaking` | yes | `typeName: string`, `oldTypeKind: string`, `newTypeKind: string` |
| `TypeDescriptionChanged` | Both descriptions are strings and they differ | `NonBreaking` | no | `typeName: string`, `oldTypeDescription: string`, `newTypeDescription: string` |
| `TypeDescriptionAdded` | The old description is absent and the new one is a string | `NonBreaking` | no | `typeName: string`, `addedTypeDescription: string` |
| `TypeDescriptionRemoved` | The old description is a string and the new one is absent | `NonBreaking` | no | `typeName: string`, `removedTypeDescription: string` |

`addedTypeKind`, `oldTypeKind` and `newTypeKind` hold the type's **AST definition-node kind** — the
`graphql` `Kind` value, printed: `ScalarTypeDefinition`, `ObjectTypeDefinition`,
`InterfaceTypeDefinition`, `UnionTypeDefinition`, `EnumTypeDefinition` or
`InputObjectTypeDefinition`. A type with no AST node yields the empty string.

A second, shorter naming of the same six kinds is exposed publicly as `getTypePrefix`, which takes
one `GraphQLNamedType` and returns `scalar`, `type`, `interface`, `union`, `enum` or `input`
respectively. Its declared return type is `string`; for an argument whose AST kind is none of the
six it returns `undefined` at run time. This shorter naming — not the AST kind — is what the
`typeType` member of §5.5 carries.

When two same-named types share a kind, the walk descends into the kind-specific comparison of
§5.5 through §5.10. When the kinds differ, `TypeKindChanged` is the only change emitted for that
type and the walk does not descend.

### 5.5 Field changes

Fields of object types and of interface types are compared identically. Path is the type name and
the field name joined by a dot, except where the table says otherwise.

| Change type | Emitted when | Criticality | Reason present | `meta` |
| --- | --- | --- | --- | --- |
| `FieldRemoved` | A field exists on the old type only | `Breaking` | yes | `typeName`, `removedFieldName`, `isRemovedFieldDeprecated: boolean`, `typeType: string` |
| `FieldAdded` | A field exists on the new type only | `NonBreaking` | no | `typeName`, `addedFieldName`, `typeType: string`, `addedFieldReturnType: string` |
| `FieldDescriptionChanged` | Both descriptions are strings and they differ | `NonBreaking` | no | `typeName`, `fieldName`, `oldDescription`, `newDescription` |
| `FieldDescriptionAdded` | The old description is absent and the new one is a string | `NonBreaking` | no | `typeName`, `fieldName`, `addedDescription` |
| `FieldDescriptionRemoved` | The old description is a string and the new one is absent | `NonBreaking` | no | `typeName`, `fieldName` |
| `FieldDeprecationAdded` | The field is not deprecated in the old schema and is deprecated in the new one | `NonBreaking` | no | `typeName`, `fieldName`, `deprecationReason` — path appends `.@deprecated` |
| `FieldDeprecationRemoved` | The field is deprecated in the old schema and is not in the new one | `NonBreaking` | no | `typeName`, `fieldName` — path appends `.@deprecated` |
| `FieldDeprecationReasonChanged` | Both reasons are present and they differ | `NonBreaking` | no | `typeName`, `fieldName`, `oldDeprecationReason`, `newDeprecationReason` — path appends `.@deprecated` |
| `FieldDeprecationReasonAdded` | The old reason is absent and the new one is present | `NonBreaking` | no | `typeName`, `fieldName`, `addedDeprecationReason` — path appends `.@deprecated` |
| `FieldDeprecationReasonRemoved` | The old reason is present and the new one is absent | `NonBreaking` | no | `typeName`, `fieldName` — path does **not** append `.@deprecated` |
| `FieldTypeChanged` | The old field exists and the printed field types differ | `NonBreaking` when `meta.isSafeFieldTypeChange` is `true`, otherwise `Breaking` | yes | `typeName`, `fieldName`, `oldFieldType`, `newFieldType`, `isSafeFieldTypeChange: boolean` |

`typeType` is the shorter kind naming of §5.4 — the value `getTypePrefix` returns for the enclosing
type.
`isSafeFieldTypeChange` is the output-position predicate of §4.4.
`FieldTypeChanged` must not be emitted when the field is new, because there is no old type to
compare against.

### 5.6 Field-argument changes

Path is the type name, the field name and the argument name joined by dots.

| Change type | Emitted when | Criticality | Reason present | `meta` |
| --- | --- | --- | --- | --- |
| `FieldArgumentAdded` | An argument exists on the new field only | `NonBreaking` when `meta.addedToNewField` is `true`; otherwise `Breaking` when `meta.isAddedFieldArgumentBreaking` is `true`; otherwise `Dangerous` | yes | `typeName`, `fieldName`, `addedArgumentName`, `addedArgumentType`, `hasDefaultValue: boolean`, `isAddedFieldArgumentBreaking: boolean`, `addedToNewField: boolean` |
| `FieldArgumentRemoved` | An argument exists on the old field only | `Breaking` | yes | `typeName`, `fieldName`, `removedFieldArgumentName`, `removedFieldType` |
| `FieldArgumentDescriptionChanged` | Both descriptions differ | `NonBreaking` | no | `typeName`, `fieldName`, `argumentName`, `oldDescription: string \| null`, `newDescription: string \| null` |
| `FieldArgumentDefaultChanged` | The two default values are unequal under §4.5 | `Dangerous` | yes | `typeName`, `fieldName`, `argumentName`, `oldDefaultValue?: string`, `newDefaultValue?: string` |
| `FieldArgumentTypeChanged` | The printed argument types differ | `NonBreaking` when `meta.isSafeArgumentTypeChange` is `true`, otherwise `Breaking` | yes | `typeName`, `fieldName`, `argumentName`, `oldArgumentType`, `newArgumentType`, `isSafeArgumentTypeChange: boolean` |

`addedToNewField` is `true` exactly when the enclosing field itself exists only in the new schema.
`isSafeArgumentTypeChange` is the input-position predicate of §4.4. An added argument is breaking
when it is non-null and has no default value.

### 5.7 Input-object changes

Path is the input object name and the input field name joined by a dot.

| Change type | Emitted when | Criticality | Reason present | `meta` |
| --- | --- | --- | --- | --- |
| `InputFieldRemoved` | An input field exists on the old type only | `Breaking` | yes | `inputName`, `removedFieldName`, `isInputFieldDeprecated: boolean` |
| `InputFieldAdded` | An input field exists on the new type only | four-way, see below | yes | `inputName`, `addedInputFieldName`, `isAddedInputFieldTypeNullable: boolean`, `addedInputFieldType: string`, `addedFieldDefault?: string`, `addedToNewType: boolean` |
| `InputFieldDescriptionAdded` | The old description is absent, the new one present | `NonBreaking` | no | `inputName`, `inputFieldName`, `addedInputFieldDescription` |
| `InputFieldDescriptionRemoved` | The old description is present, the new one absent | `NonBreaking` | no | `inputName`, `inputFieldName`, `removedDescription` |
| `InputFieldDescriptionChanged` | Both descriptions are present and differ | `NonBreaking` | no | `inputName`, `inputFieldName`, `oldInputFieldDescription`, `newInputFieldDescription` |
| `InputFieldDefaultValueChanged` | The old field exists and the default values are unequal under §4.5 | `Dangerous` | yes | `inputName`, `inputFieldName`, `oldDefaultValue?: string`, `newDefaultValue?: string` |
| `InputFieldTypeChanged` | The old field exists and the printed types differ | `NonBreaking` when `meta.isInputFieldTypeChangeSafe` is `true`, otherwise `Breaking` | yes | `inputName`, `inputFieldName`, `oldInputFieldType`, `newInputFieldType`, `isInputFieldTypeChangeSafe: boolean` |

`InputFieldAdded` is graded by the first matching branch of this ordered list:

1. `meta.addedToNewType` is `true` — `NonBreaking`.
2. The added field is nullable and `meta.addedFieldDefault` is `undefined` — `NonBreaking`.
3. `meta.addedFieldDefault` is `undefined` — `Breaking`.
4. Otherwise — `Dangerous`.

`InputFieldDefaultValueChanged` and `InputFieldTypeChanged` must not be emitted for a field that
exists only in the new schema.

### 5.8 Enum changes

| Change type | Emitted when | Criticality | Reason present | Path |
| --- | --- | --- | --- | --- |
| `EnumValueRemoved` | A value exists on the old enum only | `Breaking` | yes | `Enum.value` |
| `EnumValueAdded` | A value exists on the new enum only | `NonBreaking` when `meta.addedToNewType` is `true`, otherwise `Dangerous` | only when `Dangerous` | `Enum.value` |
| `EnumValueDescriptionChanged` | The descriptions differ | `NonBreaking` | no | `Enum.value` |
| `EnumValueDeprecationReasonChanged` | Both reasons are present and differ | `NonBreaking` | no | `Enum.value.@deprecated` |
| `EnumValueDeprecationReasonAdded` | The old reason is absent, the new one present | `NonBreaking` | no | `Enum.value.@deprecated` |
| `EnumValueDeprecationReasonRemoved` | The old reason is present, the new one absent | `NonBreaking` | no | `Enum.value` |

Every row's `meta` carries `enumName`. The remaining members are:

| Change type | Remaining `meta` members |
| --- | --- |
| `EnumValueRemoved` | `removedEnumValueName`, `isEnumValueDeprecated: boolean` |
| `EnumValueAdded` | `addedEnumValueName`, `addedToNewType: boolean`, `addedDirectiveDescription: string \| null` |
| `EnumValueDescriptionChanged` | `enumValueName`, `oldEnumValueDescription: string \| null`, `newEnumValueDescription: string \| null` |
| `EnumValueDeprecationReasonChanged` | `enumValueName`, `oldEnumValueDeprecationReason`, `newEnumValueDeprecationReason` |
| `EnumValueDeprecationReasonAdded` | `enumValueName`, `addedValueDeprecationReason` |
| `EnumValueDeprecationReasonRemoved` | `enumValueName`, `removedEnumValueDeprecationReason` |

`addedDirectiveDescription` on `EnumValueAdded` holds the added enum value's own description, not a
directive's; the member name is historical and must be kept.

### 5.9 Union and interface-implementation changes

Path is the union name, respectively the object type name, with no member component.

| Change type | Emitted when | Criticality | Reason present | `meta` |
| --- | --- | --- | --- | --- |
| `UnionMemberRemoved` | A member type exists on the old union only | `Breaking` | yes | `unionName`, `removedUnionMemberTypeName` |
| `UnionMemberAdded` | A member type exists on the new union only | `NonBreaking` when `meta.addedToNewType` is `true`, otherwise `Dangerous` | yes | `unionName`, `addedUnionMemberTypeName`, `addedToNewType: boolean` |
| `ObjectTypeInterfaceAdded` | An interface is implemented by the new object type only | `NonBreaking` when `meta.addedToNewType` is `true`, otherwise `Dangerous` | yes | `objectTypeName`, `addedInterfaceName`, `addedToNewType: boolean` |
| `ObjectTypeInterfaceRemoved` | An interface is implemented by the old object type only | `Breaking` | yes | `objectTypeName`, `removedInterfaceName` |

### 5.10 Directive-definition changes

| Change type | Emitted when | Criticality | Reason present | Path |
| --- | --- | --- | --- | --- |
| `DirectiveRemoved` | A directive exists in the old schema only | `Breaking` | yes | `@name` |
| `DirectiveAdded` | A directive exists in the new schema only | `NonBreaking` | no | `@name` |
| `DirectiveDescriptionChanged` | The descriptions differ | `NonBreaking` | no | `@name` |
| `DirectiveLocationAdded` | A location exists on the new directive only | `NonBreaking` | no | `@name` |
| `DirectiveLocationRemoved` | A location exists on the old directive only | `Breaking` | yes | `@name` |
| `DirectiveRepeatableAdded` | The directive is repeatable in the new schema and was not before | `NonBreaking` | no | `@name` |
| `DirectiveRepeatableRemoved` | The directive is not repeatable in the new schema and was before | `Dangerous` | yes | `@name` |
| `DirectiveArgumentAdded` | An argument exists on the new directive only | three-way, see below | yes | `@name` |
| `DirectiveArgumentRemoved` | An argument exists on the old directive only | `Breaking` | yes | `@name.argument` |
| `DirectiveArgumentDescriptionChanged` | The descriptions differ | `NonBreaking` | no | `@name.argument` |
| `DirectiveArgumentDefaultValueChanged` | The default values are unequal under §4.5 | `Dangerous` | yes | `@name.argument` |
| `DirectiveArgumentTypeChanged` | The printed types differ | `NonBreaking` when `meta.isSafeDirectiveArgumentTypeChange` is `true`, otherwise `Breaking` | yes | `@name.argument` |

`DirectiveArgumentAdded` carries the path of the directive rather than of the argument, and is
graded by the first matching branch: `meta.addedToNewDirective` is `true` — `NonBreaking`;
otherwise `meta.addedDirectiveArgumentTypeIsNonNull` is `true` — `Breaking`; otherwise
`NonBreaking`.

The `meta` payloads are:

| Change type | `meta` members |
| --- | --- |
| `DirectiveRemoved` | `removedDirectiveName` |
| `DirectiveAdded` | `addedDirectiveName`, `addedDirectiveRepeatable: boolean`, `addedDirectiveLocations: string[]`, `addedDirectiveDescription: string \| null` |
| `DirectiveDescriptionChanged` | `directiveName`, `oldDirectiveDescription: string \| null`, `newDirectiveDescription: string \| null` |
| `DirectiveLocationAdded` | `directiveName`, `addedDirectiveLocation` |
| `DirectiveLocationRemoved` | `directiveName`, `removedDirectiveLocation` |
| `DirectiveRepeatableAdded` | `directiveName` |
| `DirectiveRepeatableRemoved` | `directiveName` |
| `DirectiveArgumentAdded` | `directiveName`, `addedDirectiveArgumentName`, `addedDirectiveArgumentTypeIsNonNull: boolean`, `addedToNewDirective: boolean`, `addedDirectiveArgumentDescription?: string`, `addedDirectiveArgumentType: string`, `addedDirectiveDefaultValue?: string` |
| `DirectiveArgumentRemoved` | `directiveName`, `removedDirectiveArgumentName` |
| `DirectiveArgumentDescriptionChanged` | `directiveName`, `directiveArgumentName`, `oldDirectiveArgumentDescription: string \| null`, `newDirectiveArgumentDescription: string \| null` |
| `DirectiveArgumentDefaultValueChanged` | `directiveName`, `directiveArgumentName`, `oldDirectiveArgumentDefaultValue?: string`, `newDirectiveArgumentDefaultValue?: string` |
| `DirectiveArgumentTypeChanged` | `directiveName`, `directiveArgumentName`, `oldDirectiveArgumentType`, `newDirectiveArgumentType`, `isSafeDirectiveArgumentTypeChange: boolean` |

The removal and addition rows are the only two that do not carry a plain `directiveName`; they carry
`removedDirectiveName` and `addedDirectiveName` instead, and their path is built from that member.

### 5.11 Directive-usage changes

A *directive usage* is an application of a directive to a schema element, read from the element's
AST node rather than from the schema's runtime objects. Usages are compared per element; for each
element, the usages present on only one side yield the matching added or removed change type below,
and usages present on both sides are compared argument by argument as described at the end of this
section.

Every directive-usage `meta` carries `directiveRepeatedTimes: number`, the number of times that
directive appears on that element.

| Change type pair | Element | Path | `meta` element keys |
| --- | --- | --- | --- |
| `DirectiveUsageSchemaAdded` / `…Removed` | the schema definition or an extension | `` .@name `` — a leading dot with no element component | *(none besides the directive name)* |
| `DirectiveUsageObjectAdded` / `…Removed` | an object type | `Object.@name` | `objectName` |
| `DirectiveUsageInterfaceAdded` / `…Removed` | an interface type | `Interface.@name` | `interfaceName` |
| `DirectiveUsageScalarAdded` / `…Removed` | a scalar type | `Scalar.@name` | `scalarName` |
| `DirectiveUsageEnumAdded` / `…Removed` | an enum type | `Enum.@name` | `enumName` |
| `DirectiveUsageEnumValueAdded` / `…Removed` | an enum value | `Enum.VALUE.@name` | `enumName`, `enumValueName` |
| `DirectiveUsageUnionMemberAdded` / `…Removed` | a union type | `Union.@name` | `unionName`, and `addedUnionMemberTypeName` / `removedUnionMemberTypeName` |
| `DirectiveUsageInputObjectAdded` / `…Removed` | an input object type | `Input.@name` | `inputObjectName`; on the added row also `addedInputFieldName`, `isAddedInputFieldTypeNullable: boolean`, `addedInputFieldType: string`; on the removed row also `removedInputFieldName`, `isRemovedInputFieldTypeNullable: boolean`, `removedInputFieldType: string` |
| `DirectiveUsageInputFieldDefinitionAdded` / `…Removed` | an input field | `Input.field.@name` | `inputObjectName`, `inputFieldName`; on the added row also `inputFieldType: string` |
| `DirectiveUsageFieldDefinitionAdded` / `…Removed` | a field definition | `Type.field.@name` | `typeName`, `fieldName` |
| `DirectiveUsageFieldAdded` / `…Removed` | a field, reported from the enclosing type's walk | `Type.field.name` — the directive component carries **no** leading `@` | `typeName`, `fieldName` |
| `DirectiveUsageArgumentDefinitionAdded` / `…Removed` | a field argument | `Type.field.argument.@name` | `typeName`, `fieldName`, `argumentName` |

The directive name appears in `meta` as `addedDirectiveName` on the added rows and
`removedDirectiveName` on the removed rows. Every added row except `DirectiveUsageFieldAdded` also
carries `addedToNewType: boolean`; no removed row carries it.

Criticality for every row of that table follows one of two ordered decisions.

**Added.** When the row's `meta.addedToNewType` is `true`, the level is `NonBreaking`. Otherwise the
level is: `NonBreaking` when the directive is named `deprecated`; `Breaking` when the directive is
named `oneOf`; `Dangerous` for every other directive name. `DirectiveUsageFieldAdded` is the sole
exception in that it has no `addedToNewType` branch and always uses the second decision.

**Removed.** The level is `NonBreaking` when the directive is named `deprecated`; `NonBreaking`
when the directive is named `oneOf`; `Dangerous` for every other directive name.

A reason is present on every directive-usage change.

When a directive usage is present on both sides, its arguments are compared. Arguments present on
only one side, and mutual arguments whose printed values differ, produce these two change types:

| Change type | Criticality | Reason present |
| --- | --- | --- |
| `DirectiveUsageArgumentAdded` | `NonBreaking` | no |
| `DirectiveUsageArgumentRemoved` | `Dangerous` | yes |

A mutual argument whose printed old and new values are equal produces nothing. A mutual argument
whose values differ produces the removed change followed by the added change, and the added change
carries the previous value in `meta.oldArgumentValue`.

Both change types carry `meta` with `directiveName`, `directiveRepeatedTimes`, and four nullable
context keys — `parentTypeName`, `parentFieldName`, `parentArgumentName` and `parentEnumValueName`,
each of type `string | null`. `DirectiveUsageArgumentAdded` additionally carries
`addedArgumentName`, `addedArgumentValue: string` — the printed argument value — and
`oldArgumentValue: string | null`, which holds the previous printed value when the change came from
a mutual argument whose value differed and is `null` otherwise.
`DirectiveUsageArgumentRemoved` additionally carries `removedArgumentName` and no value member.

Their path is assembled from an ordered list of five components — the parent type name or the empty
string when it is `null`; the parent field name, or the parent enum value name when the parent
field name is `null`; the parent argument name; the directive name prefixed with `@`; and the
argument name — from which every entry that is exactly `null` is dropped, the remainder being
joined by dots. The empty string substituted for a missing parent type name is not `null` and is
therefore retained, which is what produces the leading dot on a schema-level directive argument.

## 6. Diff Rules

### 6.1 The rule contract

`Rule<TConfig = any>` is a function type. It takes exactly one parameter, an object with four
required members: `changes` of type `Change[]`, `oldSchema` of type `GraphQLSchema | null`,
`newSchema` of type `GraphQLSchema | null`, and `config` of type `TConfig`. It returns
`Change[] | Promise<Change[]>`.

`DiffRule` is a single exported object that groups the seven built-in rules under the keys
`considerUsage`, `dangerousBreaking`, `ignoreDescriptionChanges`, `ignoreDirectives`,
`safeUnreachable`, `simplifyChanges` and `suppressRemovalOfDeprecatedField`. The seven rules are
reachable only through that object; none of them is a top-level export of the package.

Wherever a rule inspects a path, it splits the path on the dot character and reads positional
components: the first component is the type name, the second the field or member name, the third
the argument name. That split is naive; it does not treat a dot inside a component specially.

### 6.2 `ignoreDescriptionChanges`

Returns the input list with every change whose `type` is one of these eleven values removed, and
every other change retained in its original relative order:
`FieldArgumentDescriptionChanged`, `DirectiveDescriptionChanged`,
`DirectiveArgumentDescriptionChanged`, `EnumValueDescriptionChanged`, `FieldDescriptionChanged`,
`FieldDescriptionAdded`, `FieldDescriptionRemoved`, `InputFieldDescriptionAdded`,
`InputFieldDescriptionRemoved`, `InputFieldDescriptionChanged`, `TypeDescriptionChanged`.

The rule reads neither schema nor the config.

### 6.3 `dangerousBreaking`

Returns a list of the same length and order in which every change graded `Dangerous` is replaced by
a copy graded `Breaking`, with the reason preserved, and every other change is returned unchanged.

### 6.4 `safeUnreachable`

Computes the set of type names reachable from the old schema's roots — the query, mutation and
subscription types, plus every named type appearing as a field type, an argument type, an input
field type, an interface, or a union member of an already-reachable type, transitively. When
`oldSchema` is `null` the set is empty.

Returns a list of the same length and order in which every change that is graded `Breaking`, has a
`path`, and whose first path component is not in the reachable set, is replaced by a copy graded
`NonBreaking` whose `message` is replaced by exactly the string `Detached from the schema roots`. The reason
is preserved. Every other change is returned unchanged.

This is the first of the two places where message text is contractual.

### 6.5 `suppressRemovalOfDeprecatedField`

Returns a list of the same length and order in which a change is replaced by a `Dangerous` copy of
itself when it is graded `Breaking`, has a `path`, and matches one of these four cases; every other
change is returned unchanged.

1. `type` is `FieldRemoved`, the first path component names an object or interface type in the old
   schema, and that type's field named by the second path component is deprecated.
2. `type` is `EnumValueRemoved`, the first path component names an enum type in the old schema, and
   that enum has a value named by the second path component which is deprecated.
3. `type` is `InputFieldRemoved`, the first path component names an input object type in the old
   schema, and that type has a field named by the second path component which is deprecated.
4. `type` is `TypeRemoved` and the first path component names no type in the new schema.

Deprecation is determined by the rule of §4.6, extended to accept an explicit `isDeprecated`
property when the runtime object carries one and to accept a `@deprecated` directive on the AST
node when neither of the earlier signals is present.

### 6.6 `simplifyChanges`

Suppresses changes that are already implied by a coarser change at the same or the parent path.

The rule walks the input list once, in order, maintaining an initially empty list of recorded
paths. For each change:

- A change without a `path` is always kept and records nothing.
- Otherwise let *parent* be the path with its final dot-separated component removed, or the whole
  path when it contains no dot. The change is kept when no recorded path equals either the change's
  own path or *parent*, and dropped otherwise.
- Independently of whether it was kept, the change's own path is appended to the recorded list when
  its `type` belongs to the *simple change* set.

Because recording happens after the keep decision for the same change, a change never suppresses
itself.

The simple change set has exactly 32 members: the thirteen directive-usage additions
(`DirectiveUsageArgumentAdded`, `DirectiveUsageArgumentDefinitionAdded`, `DirectiveUsageEnumAdded`,
`DirectiveUsageEnumValueAdded`, `DirectiveUsageFieldAdded`, `DirectiveUsageFieldDefinitionAdded`,
`DirectiveUsageInputFieldDefinitionAdded`, `DirectiveUsageInputObjectAdded`,
`DirectiveUsageInterfaceAdded`, `DirectiveUsageObjectAdded`, `DirectiveUsageScalarAdded`,
`DirectiveUsageSchemaAdded`, `DirectiveUsageUnionMemberAdded`); `DirectiveAdded`,
`DirectiveArgumentAdded`, `DirectiveLocationAdded`; `EnumValueAdded`,
`EnumValueDeprecationReasonAdded`; `FieldAdded`, `FieldArgumentAdded`, `FieldDeprecationAdded`,
`FieldDeprecationReasonAdded`, `FieldDescriptionAdded`; `InputFieldAdded`,
`InputFieldDescriptionAdded`; `ObjectTypeInterfaceAdded`; `TypeAdded`, `TypeDescriptionAdded`;
`UnionMemberAdded`; and three that are not additions but are included because deprecation reasons
are redundant with the directive that carries them — `FieldDeprecationRemoved`,
`FieldDeprecationReasonChanged` and `EnumValueDeprecationReasonChanged`.

`DirectiveRepeatableAdded` is not a member of the set.

### 6.7 `ignoreDirectives`

Takes its configuration from `config.ignoredDirectives`, an array of directive names. When `config`
is absent, or `config.ignoredDirectives` is absent, or that array is empty, the rule returns the
input list unchanged. Behaviour for a non-empty array is a non-goal of this specification, as
stated in §2.

The configuration type is not part of the import surface; it is supplied structurally.

### 6.8 `considerUsage`

The only asynchronous built-in rule, and the only one that reads `config`.

`UsageHandler` is a function type taking one parameter — an array of objects, each with `type` of
type `string`, an optional `field` of type `string`, an optional `argument` of type `string`, and
`meta` of type `{ change: Change }` — and returning `Promise<boolean[]>`. A `true` entry means the
corresponding coordinate is safe to break.

`ConsiderUsageConfig` is an object type with one optional member, `checkUsage`, of type
`UsageHandler`. The type name is not on the import surface; it is supplied structurally, and it is
the type of the fourth parameter of `diff`.

The rule behaves as follows.

- When `config` is absent or otherwise falsy, the rule raises an `Error` before doing anything else.
- It collects, in input order, every change graded `Breaking` that has a `path`, splitting each path
  into its first three components to produce one handler input entry per collected change.
- It awaits `config.checkUsage` applied to that array.
- It builds the set of suppressed paths by keeping the collected entries whose corresponding
  handler result is exactly `true`, and joining each entry's type, field and argument with dots,
  omitting components that are absent or empty.
- It returns a list of the same length and order in which every change that is graded `Breaking`,
  has a `path`, and whose path starts with at least one suppressed path, is replaced by a copy
  graded `Dangerous` with an additional `isSafeBasedOnUsage` member set to `true` on its
  `criticality` object, and whose `message` is the original message followed by exactly the string
  ` (non-breaking based on usage)`. Every other change is returned unchanged.

The appended suffix is the second and last place where message text is contractual.

Because the suppression test is a prefix test rather than an equality test, marking `User.email`
safe also downgrades a breaking change at `User.email.locale`.

## 7. Serializable Change Records

A change record produced by §5 is built from live `graphql` objects and cannot be transported
across a process boundary. `meta` can. The library therefore exposes, for every one of the 80
change types, a *builder* that reconstructs the full change record from `meta` alone.

`SerializableChange` is the union of the 80 argument types accepted by those builders. Each member
is an object with a `type` member holding one `ChangeType` value and a `meta` member holding the
payload described for that change type in §5.

Each builder takes exactly one parameter, of the `SerializableChange` member matching its change
type, and returns the change record. The returned record's `type`, `criticality.level`, presence or
absence of `criticality.reason`, `path`, and `meta` must be identical to what §5 specifies for a
record of that change type with that `meta`.

Builder names are derived from the `ChangeType` key by lowercasing its first character and
appending `FromMeta`: `FieldRemoved` yields `fieldRemovedFromMeta`, `DirectiveUsageSchemaAdded`
yields `directiveUsageSchemaAddedFromMeta`. There is exactly one exception. The builder for
`UnionMemberAdded` is named `buildUnionMemberAddedMessageFromMeta`; the name
`unionMemberAddedFromMeta` is not exported.

Builders are the reason `meta` is specified field by field in §5: a builder receives nothing else.

## 8. Projection Two — Schema Coverage

### 8.1 Entry point

`coverage` takes two parameters in this order: `schema`, of type `GraphQLSchema`, required; and
`sources`, of type `Source[]`, required. It returns `SchemaCoverage` synchronously.

### 8.2 Report shape

```ts
interface Location { start: number; end: number }
interface ArgumentCoverage {
  hits: number; fieldsCount: number; fieldsCountCovered: number;
  locations: { [source: string]: Location[] };
}
interface TypeChildCoverage extends ArgumentCoverage {
  children: { [argumentName: string]: ArgumentCoverage };
}
```

`TypeCoverage` has `hits: number`, `fieldsCount: number`, `fieldsCountCovered: number`, `type` of
type `GraphQLNamedType`, and `children` mapping a field name to a `TypeChildCoverage`.

`SchemaCoverage` has `sources: Source[]`, `types` mapping a type name to a `TypeCoverage`, and
`stats`.

### 8.3 Which types are reported

`types` contains one entry for every named type of the schema that is an object type or an
interface type, is not one of the five built-in scalars, and whose name does not begin with a
double underscore. Every such type is present in the report whether or not it was hit, with a
`hits` of zero when it was not.

Each reported type's `children` contains one entry per field of that type, and each field's
`children` contains one entry per argument of that field. Every field and argument is present
whether or not it was hit.

### 8.4 How hits are counted

Each source is parsed into its operation definitions and its fragment definitions, and each of
those is walked with schema type information attached. For every field selection encountered:

- The selection is ignored entirely when the enclosing parent type is an introspection type, or
  when the selected field is named `__typename` or `__schema`.
- Otherwise the enclosing parent type's `hits` is incremented by one, and that type's child entry
  for the selected field has its `hits` incremented by one and the source's `Location` list gains
  the selection node's location, prepended so that the most recently visited location is first.
- Every argument supplied on that selection increments the matching argument entry's `hits` by one
  and likewise records a location.
- When the enclosing parent type is the schema's query, mutation or subscription root type, the
  corresponding covered-operation counter in `stats` is incremented by one.

A field or argument that is never selected keeps a `hits` of zero and an empty location map.

### 8.5 Statistics

`stats` has exactly these members, all of type `number`:

| Member | Definition |
| --- | --- |
| `numTypes` | The number of reported types. |
| `numTypesCovered` | The number of reported types whose `fieldsCountCovered` is greater than zero. |
| `numTypesCoveredFully` | The number of reported types whose `fieldsCountCovered` equals its `fieldsCount`. |
| `numFields` | The sum of `fieldsCount` over the reported types. |
| `numFieldsCovered` | The sum of `fieldsCountCovered` over the reported types. |
| `numFiledsCovered` | A deprecated alias holding the same value as `numFieldsCovered`. |
| `numQueries` | The number of fields on the query root type, or zero when there is none. |
| `numMutations` | The number of fields on the mutation root type, or zero when there is none. |
| `numSubscriptions` | The number of fields on the subscription root type, or zero when there is none. |
| `numCoveredQueries` | The number of field selections whose parent type is the query root type. |
| `numCoveredMutations` | The number of field selections whose parent type is the mutation root type. |
| `numCoveredSubscriptions` | The number of field selections whose parent type is the subscription root type. |

`numFiledsCovered` is misspelled deliberately; it is retained for backward compatibility and must
be present with the same value as `numFieldsCovered`.

`fieldsCount` and `fieldsCountCovered` are computed bottom-up over the `children` maps, and they
count arguments as well as fields. The rule is uniform: a node's `fieldsCount` is the number of its
children plus the sum of its children's own `fieldsCount`, and its `fieldsCountCovered` is the
number of its children whose `hits` is greater than zero plus the sum of its children's own
`fieldsCountCovered`. An argument has no children, so its own `fieldsCount` and
`fieldsCountCovered` both stay zero and it contributes to its field's totals rather than carrying
its own. A field's `fieldsCount` is therefore its argument count. A type with three fields that
carry one argument each has a `fieldsCount` of six, not three.

A type whose `fieldsCount` equals its `fieldsCountCovered` is counted in `numTypesCoveredFully`,
which includes a type that has no fields at all.

`numCoveredQueries` counts selections, not distinct fields: selecting the same root field twice
counts twice, and it counts occurrences across all sources.

## 9. Projection Three — Type Similarity

### 9.1 Entry point

`similar` takes three parameters in this order: `schema`, of type `GraphQLSchema`, required;
`typeName`, of type `string | undefined`, required in position — it accepts `undefined` but a
caller must still pass an argument for it; and `threshold`, of type `number`, optional with a
default of `0.4`. It returns `SimilarMap` synchronously.

`SimilarMap` is an index signature from a type name of type `string` to a `BestMatch`.

### 9.2 Supporting types

```ts
interface Target { typeId: string; value: string }
interface Rating { target: Target; rating: number }
interface BestMatch { ratings: Rating[]; bestMatch: Rating }
```

### 9.3 Candidate set

The candidates are every name in the schema's type map except the five built-in scalars and every
name beginning with a double underscore. Each candidate's `value` is its *stripped definition*: the
type printed by `graphql`, trimmed, with a leading run matching one or more lowercase letters, a
space, any run of characters up to the first opening brace, and that brace removed; with a trailing
closing brace removed; trimmed again; split on newlines; each line trimmed; the lines sorted by
locale-aware string comparison; and the sorted lines joined with a single space.

Sorting the lines is what makes the measure insensitive to field order.

### 9.4 Reported entries

When `typeName` is `undefined`, every candidate is a source and the result holds one entry per
source that produced a match. When `typeName` is a string that is not a candidate, `similar` raises
an `Error`. When `typeName` is a string that is a candidate, that single type is the only source.

For a source, the match set is every candidate whose type's AST-node kind equals the source type's
AST-node kind and whose `typeId` differs from the source's. When the match set is empty the source
produces no entry.

Otherwise every member of the match set is rated against the source's stripped definition, and the
best-rated member is selected. When the best rating is strictly below `threshold`, the source
produces no entry. Otherwise the source's entry has that best rating as `bestMatch`, and `ratings`
holds every other rating whose value is greater than or equal to `threshold` and whose target is
not the best match's target, ordered from highest rating to lowest.

### 9.5 The similarity measure

The rating of two strings is a number computed by the first matching branch of this ordered list:

1. Both strings are empty — the rating is `1`.
2. Exactly one string is empty — the rating is `0`.
3. The two strings are equal after upper-casing — the rating is `1`.
4. Both strings have length one — the rating is `0`.
5. Otherwise: each string is upper-cased and split on the space character; from each resulting word
   the list of adjacent two-character substrings is taken, and those lists are concatenated in
   order into one pair list per string. Every pair of the first list is matched against the first
   still-unmatched equal pair of the second list, and a matched pair is consumed so that it cannot
   match twice. The rating is twice the number of matches divided by the total length of the two
   pair lists.

The best match is the highest-rated member of the match set; when several members tie, the one that
comes first in the schema's type-map order wins. `Target`, `Rating` and `BestMatch` are exported as
types; the rating function itself is internal and is not part of the import surface.

## 10. Projection Four — Document Validation

### 10.1 Entry point

`validate` takes three parameters in this order: `schema`, of type `GraphQLSchema`, required;
`sources`, of type `Source[]`, required; and `options`, of type `ValidateOptions`, optional. It
returns `InvalidDocument[]` synchronously.

```ts
interface InvalidDocument {
  source: Source;
  errors: GraphQLError[];
  deprecated: GraphQLError[];
}
```

`ValidateOptions` is an object type in which every member is optional:
`strictFragments` and `strictDeprecated` of type `boolean`, each defaulting to `true`;
`keepClientFields` and `apollo` of type `boolean`, each defaulting to `false`; `maxDepth`,
`maxAliasCount`, `maxDirectiveCount` and `maxTokenCount` of type `number`, each unlimited when
absent; and `validateComplexityConfig`, an object with `maxComplexityScore`,
`complexityScalarCost`, `complexityObjectCost` and `complexityDepthCostFactor`, all of type
`number`, with the complexity check disabled when absent. Neither `ValidateOptions` nor the
complexity-configuration type is on the import surface; both are supplied structurally.

`InvalidDocument` is on the import surface. Note that the coverage projection does not contribute a
type of that name to the surface; the exported `InvalidDocument` is this three-member one.

### 10.2 Fragment resolution

Before validating anything, every fragment definition found in any source is collected into a
dependency graph keyed by fragment name, with circular dependencies permitted. A fragment's
dependencies are the fragment names that appear in its printed form, found by matching three dots
followed by one or more ASCII letters, digits or underscores.

Only documents that contain at least one operation are validated. For such a document, its
operations are collected into a synthetic document; the fragment names appearing in that printed
document are resolved transitively through the graph; the resulting fragment list is de-duplicated
by name keeping the first occurrence; and the fragments are appended to the operations to form the
document that is actually validated.

Fragment-only documents are therefore never reported, but their fragments remain available to every
operation in every source.

### 10.3 Checks

For each validated document, the following are appended to `errors` in exactly this order.

1. The errors reported by `graphql`'s own document validation.
2. When `maxDepth` is set and non-zero and the document's depth exceeds it — at most one error.
3. When `validateComplexityConfig` is set and the document's complexity score exceeds
   `maxComplexityScore` — at most one error.
4. When `maxAliasCount` is set and non-zero and the alias count exceeds it — at most one error.
5. When `maxDirectiveCount` is set and non-zero and the directive count exceeds it — at most one
   error.
6. When `maxTokenCount` is set and non-zero and the token count exceeds it — at most one error.
7. When `strictFragments` is enabled, one error per fragment name that has already been seen
   earlier in the collected fragment list — that is, one error per duplicate occurrence after the
   first.

Checks 2 through 6 each stop at the first offending operation of the document and report only that
one error.

Separately, when `strictDeprecated` is enabled, `deprecated` holds one error per use of a
deprecated field, deprecated argument or deprecated enum value in the document; when it is
disabled, `deprecated` is empty.

A document is included in the result exactly when the combined length of the validation errors, the
duplicate-fragment errors and the deprecation errors is greater than zero. Documents with no
findings are absent from the result rather than present with empty arrays.

Because a limit is applied only when its option is set and non-zero, setting a limit to `0`
disables that check rather than rejecting everything.

### 10.4 Apollo mode

When `apollo` is enabled, the schema and the merged document are transformed to tolerate the
`@client` and `@connection` directives before any check runs, and `keepClientFields` controls
whether client-only fields survive that transformation. When `apollo` is disabled,
`keepClientFields` has no effect.

## 11. Query-Analysis Helpers

These four helpers back the limits of §10.3 and are exported so that a caller can compute the same
numbers directly. Each of the first three takes a node of one of these five kinds — a field, a
fragment definition, an inline fragment, an operation definition, or a fragment spread.

**`countAliases`** takes two parameters in this order: `node`, required; and `getFragmentByName`, a
function from a fragment name of type `string` to a fragment definition or `undefined`, required.
It returns a `number`: one for the node itself when the node has a truthy alias, plus the counts of
the node's selections when it has a selection set, or else — and only when it has no selection set
— the count of the fragment that a fragment spread names, when that fragment resolves.

**`countDirectives`** takes the same two parameters in the same order and returns a `number`: the
length of the node's directive list, plus the counts of its selections when it has a selection set,
plus the count of the fragment a fragment spread names when it resolves. Unlike `countAliases`, the
selection-set recursion and the fragment recursion are independent rather than exclusive.

**`countDepth`** takes three parameters in this order: `node`, required; `parentDepth`, of type
`number`, required; and `getFragmentReference`, a function from a fragment name to a fragment
definition or `undefined`, required. It returns a `number`: the maximum of `parentDepth` and, for
each selection of the node's selection set, that selection's depth computed at `parentDepth + 1`;
a fragment spread additionally contributes the resolved fragment's depth computed at
`parentDepth + 1`. A node with neither a selection set nor a resolvable spread returns
`parentDepth` unchanged.

**`calculateOperationComplexity`** takes four parameters in this order: `node`, required; `config`,
of type `CalculateOperationComplexityConfig`, required; `getFragmentByName`, required, with the
same shape as above; and `depth`, of type `number`, optional with a default of `0`. It returns a
`number`. `CalculateOperationComplexityConfig` is an object type with three required members, all
of type `number`: `scalarCost`, `objectCost` and `depthCostFactor`. The cost of a node is
`scalarCost` when it has no selection set; when it has one, the cost is `objectCost` plus, for each
selection, `depthCostFactor` times that selection's cost. A fragment spread adds `depthCostFactor`
times the resolved fragment's cost on top of whatever the preceding rule produced. The `depth`
parameter is threaded through the recursion and does not itself alter the cost.

**`calculateTokenCount`** takes one parameter, an object with `source` of type `Source | string`,
required, and `getReferencedFragmentSource`, a function from a fragment name of type `string` to a
`Source | string | undefined`, required. It returns a `number`: the count of lexer tokens in the
parsed source excluding the end-of-file token, plus, for every fragment spread in the parsed
document, the token count of the referenced fragment source computed by the same rule, when that
source resolves.

Because each helper follows fragment spreads, a limit configured on `validate` is enforced against
the operation together with everything it transitively includes, not against the operation text
alone.

## 12. State Model

The library holds no state between calls. There is no initialisation step, no registry, no cache
and no module-level mutable variable. Every exported function is a pure function of its arguments:
calling it twice with equal arguments must produce equal results, and calling it must not mutate
any argument.

Three consequences follow and must hold.

- `diff`, `coverage`, `similar` and `validate` never modify the `GraphQLSchema`, the `Source[]` or
  the options object they are given.
- A `Rule` never modifies the `Change` objects it receives. A rule that changes a criticality level
  or a message returns copies, leaving the input list and its elements as they were.
- The order in which the four projections are called has no effect on any of their results.

Within a single `diff` call there is one ordered pipeline: the raw change list is computed first,
and then each rule of the `rules` array runs on the output of its predecessor, awaited when it
returns a promise. That ordering is the only sequencing the library imposes.

## 13. Error Semantics

| Situation | Result |
| --- | --- |
| `similar` is given a `typeName` that is not in the candidate set | Raises an `Error` |
| `considerUsage` runs with a falsy `config` | Raises an `Error` before calling any handler |
| `considerUsage` runs with a `config` that has no `checkUsage` | Raises a `TypeError` |
| A rule passed to `diff` throws, or returns a rejected promise | The promise returned by `diff` rejects with that error |
| `validate` is given a document that does not parse | Propagates the parse error raised by `graphql` |
| `validate` finds validation errors, deprecated usages or limit violations | Returns them; does not throw |
| `coverage` is given a source that does not parse | Propagates the parse error raised by `graphql` |

`validate` distinguishes two kinds of failure and must not conflate them. A document that is
invalid is data: it appears in the returned array. A situation the library cannot interpret — an
unparseable source, a schema `graphql` rejects — is an exception.

`similar` requires every candidate type to carry an AST node, because it compares AST-node kinds.
Schemas built from SDL satisfy this; a schema assembled programmatically without AST nodes is
outside the specified input domain.

## 14. Cross-View Invariants

**CVI-1 — Schema comparison and serializable records agree.**
For every `Change` that `diff` produces, passing an object of `{ type, meta }` taken from that
change to the builder named for its change type must return a record whose `type`, `path`,
`criticality.level` and `meta` are equal to the original's, and whose `criticality.reason` is
present exactly when the original's was. The builders are therefore a faithful round trip for
everything except live `graphql` object references, which `meta` never holds.

**CVI-2 — Diff paths are coverage coordinates.**
Let a change produced by `diff` have a `path` whose first component names a type that is an object
or interface type present in the newer schema, and let the change type be one of the field-level
types of §5.5 or the field-argument types of §5.6. Then that first component is a key of the
`types` map returned by `coverage` for that schema, the second component is a key of that type's
`children`, and for the argument types the third component is a key of that field's `children`. The
two projections must use one coordinate grammar; a path that `diff` can emit for an object or
interface field must be addressable in a coverage report.

**CVI-3 — Coverage counts only what validation can resolve.**
For a schema and sources for which `validate(schema, sources)` returns an empty array under default
options, every field selection in every operation and fragment of those sources resolves against
the schema, and therefore
`stats.numCoveredQueries + stats.numCoveredMutations + stats.numCoveredSubscriptions` equals the
number of field selections in those sources whose parent type is one of the three root types,
excluding selections of `__typename` and `__schema`. Conversely, a source that `validate` rejects
with an unknown-field error must not increment any counter for the field it names.

**CVI-4 — Similarity and comparison share one notion of type kind.**
`similar` reports a match between two types only when their AST-node kinds are equal, and `diff`
descends into a type's members only when the two same-named types' kinds are equal, emitting
`TypeKindChanged` and descending no further otherwise. A pair of types that `diff` reports as
kind-changed therefore never appears as each other's match in a `similar` report of either
schema.

**CVI-5 — All three schema-walking projections exclude the same types.**
The candidate set of `similar`, the reported-type set of `coverage`, and the compared-type set of
`diff` all exclude the five built-in scalar types and every type whose name begins with a double
underscore. A type name excluded from any one of the three must be absent from all three: absent
from `similar`'s result and from its match sets, absent from `coverage`'s `types` map, and never
the subject of a `TypeAdded`, `TypeRemoved` or `TypeKindChanged` change.

**CVI-6 — Deprecation is reported consistently by comparison and by validation.**
Let a field be non-deprecated in the old schema and deprecated in the new one. Then `diff` reports
`FieldDeprecationAdded` for it, and for any source that selects that field,
`validate(newSchema, sources)` with `strictDeprecated` enabled reports an entry in that document's
`deprecated` array while `validate(oldSchema, sources)` reports none for that field. The two
projections must read deprecation by the same rule of §4.6.

**CVI-7 — Rules preserve or shrink, never invent.**
Every built-in rule returns a list whose elements are each either an element of the input list or a
copy of one. `ignoreDescriptionChanges`, `simplifyChanges` and `ignoreDirectives` return a
subsequence of the input: same relative order, no additions. `dangerousBreaking`, `safeUnreachable`,
`suppressRemovalOfDeprecatedField` and `considerUsage` return a list of exactly the input's length
in which the element at each index has the same `type` and the same `path` as the input's element
at that index. No rule emits a change type that the raw comparison did not produce.

## 15. Public Interface

The implementation is delivered as a Node.js package named `@graphql-inspector/core`. Users import
the public names listed below from the package root module and exercise them directly from
TypeScript or JavaScript. The covered workflows require no command-line entry points and no
external services, so this specification defines no console commands.

### 15.1 Import surface

The package exposes one entry point. Every name in the catalog below is imported from it by name:

```ts
import {
  diff, coverage, similar, validate,
  DiffRule, ChangeType, CriticalityLevel,
  type Change, type SchemaCoverage, type InvalidDocument,
} from '@graphql-inspector/core';
```

There are no sub-path exports, no default export and no namespace object other than `DiffRule`.
`graphql` types that appear in signatures — `GraphQLSchema`, `Source`, `GraphQLError`,
`GraphQLNamedType`, `FragmentDefinitionNode`, `FieldNode`, `InlineFragmentNode`,
`OperationDefinitionNode`, `FragmentSpreadNode` — are imported by the consumer from `graphql`, not
re-exported here.

### 15.2 API catalog

| Name | Kind | Role |
| --- | --- | --- |
| `diff` | function | Compares two schemas and returns the change list after applying the supplied rules (§5). |
| `similar` | function | Rates every type against every other type of the same kind (§9). |
| `getTypePrefix` | function | Returns the printed kind keyword of a named type (§5.4). |
| `validate` | function | Validates documents against a schema and reports errors, deprecations and limit violations (§10). |
| `countAliases` | function | Counts aliases in a node, following fragment spreads (§11). |
| `calculateOperationComplexity` | function | Computes an operation weighted complexity score (§11). |
| `countDirectives` | function | Counts directives in a node, following fragment spreads (§11). |
| `countDepth` | function | Computes selection depth relative to a parent depth (§11). |
| `calculateTokenCount` | function | Counts lexer tokens including referenced fragments (§11). |
| `coverage` | function | Computes a schema coverage report from a schema and a set of documents (§8). |
| `DiffRule` | object | Namespace holding the seven built-in diff rules (§6). |
| `Rule` | type | Signature of a diff rule (§6.1). |
| `UsageHandler` | type | Signature of the usage callback consumed by DiffRule.considerUsage (§6.8). |
| `Change` | type | The change record (§4.2). |
| `ChangeType` | object + type | The 80 change-type identifiers and their union type (§4.3). |
| `TypeOfChangeType` | type | Maps a change-type value to its Change instantiation (§4.2). |
| `Criticality` | type | Criticality level plus optional reason (§4.1). |
| `CriticalityLevel` | enum | Breaking, Dangerous, NonBreaking (§4.1). |
| `SimilarMap` | interface | Maps a type name to its best match (§9.1). |
| `BestMatch` | interface | Best rating plus the runners-up (§9.2). |
| `Rating` | interface | One target and its score (§9.2). |
| `Target` | interface | A candidate type id and its stripped definition (§9.2). |
| `InvalidDocument` | interface | One document together with its validation findings (§10.1). |
| `CalculateOperationComplexityConfig` | type | Scalar, object and depth-factor costs for the complexity score (§11). |
| `SerializableChange` | type | Union of the 80 serializable change payloads (§7). |
| `SchemaCoverage` | interface | Root of a coverage report (§8.2). |
| `TypeCoverage` | interface | Per-type coverage entry (§8.2). |
| `TypeChildCoverage` | interface | Per-field coverage entry (§8.2). |
| `ArgumentCoverage` | interface | Per-argument coverage entry (§8.2). |
| `Location` | interface | Character offsets of one recorded hit (§8.2). |
| `fieldArgumentDescriptionChangedFromMeta` | function | Rebuilds a FieldArgumentDescriptionChanged change record from its serializable form (§7). |
| `fieldArgumentDefaultChangedFromMeta` | function | Rebuilds a FieldArgumentDefaultChanged change record from its serializable form (§7). |
| `fieldArgumentTypeChangedFromMeta` | function | Rebuilds a FieldArgumentTypeChanged change record from its serializable form (§7). |
| `directiveUsageArgumentDefinitionAddedFromMeta` | function | Rebuilds a DirectiveUsageArgumentDefinitionAdded change record from its serializable form (§7). |
| `directiveUsageEnumAddedFromMeta` | function | Rebuilds a DirectiveUsageEnumAdded change record from its serializable form (§7). |
| `directiveUsageEnumRemovedFromMeta` | function | Rebuilds a DirectiveUsageEnumRemoved change record from its serializable form (§7). |
| `directiveUsageArgumentDefinitionRemovedFromMeta` | function | Rebuilds a DirectiveUsageArgumentDefinitionRemoved change record from its serializable form (§7). |
| `directiveUsageEnumValueAddedFromMeta` | function | Rebuilds a DirectiveUsageEnumValueAdded change record from its serializable form (§7). |
| `directiveUsageEnumValueRemovedFromMeta` | function | Rebuilds a DirectiveUsageEnumValueRemoved change record from its serializable form (§7). |
| `directiveUsageFieldAddedFromMeta` | function | Rebuilds a DirectiveUsageFieldAdded change record from its serializable form (§7). |
| `directiveUsageFieldDefinitionAddedFromMeta` | function | Rebuilds a DirectiveUsageFieldDefinitionAdded change record from its serializable form (§7). |
| `directiveUsageFieldDefinitionRemovedFromMeta` | function | Rebuilds a DirectiveUsageFieldDefinitionRemoved change record from its serializable form (§7). |
| `directiveUsageFieldRemovedFromMeta` | function | Rebuilds a DirectiveUsageFieldRemoved change record from its serializable form (§7). |
| `directiveUsageInputFieldDefinitionAddedFromMeta` | function | Rebuilds a DirectiveUsageInputFieldDefinitionAdded change record from its serializable form (§7). |
| `directiveUsageInputFieldDefinitionRemovedFromMeta` | function | Rebuilds a DirectiveUsageInputFieldDefinitionRemoved change record from its serializable form (§7). |
| `directiveUsageInputObjectAddedFromMeta` | function | Rebuilds a DirectiveUsageInputObjectAdded change record from its serializable form (§7). |
| `directiveUsageInputObjectRemovedFromMeta` | function | Rebuilds a DirectiveUsageInputObjectRemoved change record from its serializable form (§7). |
| `directiveUsageInterfaceAddedFromMeta` | function | Rebuilds a DirectiveUsageInterfaceAdded change record from its serializable form (§7). |
| `directiveUsageInterfaceRemovedFromMeta` | function | Rebuilds a DirectiveUsageInterfaceRemoved change record from its serializable form (§7). |
| `directiveUsageObjectAddedFromMeta` | function | Rebuilds a DirectiveUsageObjectAdded change record from its serializable form (§7). |
| `directiveUsageObjectRemovedFromMeta` | function | Rebuilds a DirectiveUsageObjectRemoved change record from its serializable form (§7). |
| `directiveUsageScalarAddedFromMeta` | function | Rebuilds a DirectiveUsageScalarAdded change record from its serializable form (§7). |
| `directiveUsageScalarRemovedFromMeta` | function | Rebuilds a DirectiveUsageScalarRemoved change record from its serializable form (§7). |
| `directiveUsageSchemaAddedFromMeta` | function | Rebuilds a DirectiveUsageSchemaAdded change record from its serializable form (§7). |
| `directiveUsageSchemaRemovedFromMeta` | function | Rebuilds a DirectiveUsageSchemaRemoved change record from its serializable form (§7). |
| `directiveUsageUnionMemberAddedFromMeta` | function | Rebuilds a DirectiveUsageUnionMemberAdded change record from its serializable form (§7). |
| `directiveUsageUnionMemberRemovedFromMeta` | function | Rebuilds a DirectiveUsageUnionMemberRemoved change record from its serializable form (§7). |
| `directiveUsageArgumentRemovedFromMeta` | function | Rebuilds a DirectiveUsageArgumentRemoved change record from its serializable form (§7). |
| `directiveUsageArgumentAddedFromMeta` | function | Rebuilds a DirectiveUsageArgumentAdded change record from its serializable form (§7). |
| `directiveRemovedFromMeta` | function | Rebuilds a DirectiveRemoved change record from its serializable form (§7). |
| `directiveAddedFromMeta` | function | Rebuilds a DirectiveAdded change record from its serializable form (§7). |
| `directiveDescriptionChangedFromMeta` | function | Rebuilds a DirectiveDescriptionChanged change record from its serializable form (§7). |
| `directiveLocationAddedFromMeta` | function | Rebuilds a DirectiveLocationAdded change record from its serializable form (§7). |
| `directiveLocationRemovedFromMeta` | function | Rebuilds a DirectiveLocationRemoved change record from its serializable form (§7). |
| `directiveArgumentAddedFromMeta` | function | Rebuilds a DirectiveArgumentAdded change record from its serializable form (§7). |
| `directiveArgumentRemovedFromMeta` | function | Rebuilds a DirectiveArgumentRemoved change record from its serializable form (§7). |
| `directiveArgumentDescriptionChangedFromMeta` | function | Rebuilds a DirectiveArgumentDescriptionChanged change record from its serializable form (§7). |
| `directiveArgumentDefaultValueChangedFromMeta` | function | Rebuilds a DirectiveArgumentDefaultValueChanged change record from its serializable form (§7). |
| `directiveArgumentTypeChangedFromMeta` | function | Rebuilds a DirectiveArgumentTypeChanged change record from its serializable form (§7). |
| `directiveRepeatableRemovedFromMeta` | function | Rebuilds a DirectiveRepeatableRemoved change record from its serializable form (§7). |
| `directiveRepeatableAddedFromMeta` | function | Rebuilds a DirectiveRepeatableAdded change record from its serializable form (§7). |
| `enumValueRemovedFromMeta` | function | Rebuilds a EnumValueRemoved change record from its serializable form (§7). |
| `enumValueAddedFromMeta` | function | Rebuilds a EnumValueAdded change record from its serializable form (§7). |
| `enumValueDescriptionChangedFromMeta` | function | Rebuilds a EnumValueDescriptionChanged change record from its serializable form (§7). |
| `enumValueDeprecationReasonChangedFromMeta` | function | Rebuilds a EnumValueDeprecationReasonChanged change record from its serializable form (§7). |
| `enumValueDeprecationReasonAddedFromMeta` | function | Rebuilds a EnumValueDeprecationReasonAdded change record from its serializable form (§7). |
| `enumValueDeprecationReasonRemovedFromMeta` | function | Rebuilds a EnumValueDeprecationReasonRemoved change record from its serializable form (§7). |
| `fieldRemovedFromMeta` | function | Rebuilds a FieldRemoved change record from its serializable form (§7). |
| `fieldAddedFromMeta` | function | Rebuilds a FieldAdded change record from its serializable form (§7). |
| `fieldDescriptionChangedFromMeta` | function | Rebuilds a FieldDescriptionChanged change record from its serializable form (§7). |
| `fieldDescriptionAddedFromMeta` | function | Rebuilds a FieldDescriptionAdded change record from its serializable form (§7). |
| `fieldDescriptionRemovedFromMeta` | function | Rebuilds a FieldDescriptionRemoved change record from its serializable form (§7). |
| `fieldDeprecationAddedFromMeta` | function | Rebuilds a FieldDeprecationAdded change record from its serializable form (§7). |
| `fieldDeprecationRemovedFromMeta` | function | Rebuilds a FieldDeprecationRemoved change record from its serializable form (§7). |
| `fieldDeprecationReasonChangedFromMeta` | function | Rebuilds a FieldDeprecationReasonChanged change record from its serializable form (§7). |
| `fieldDeprecationReasonAddedFromMeta` | function | Rebuilds a FieldDeprecationReasonAdded change record from its serializable form (§7). |
| `fieldDeprecationReasonRemovedFromMeta` | function | Rebuilds a FieldDeprecationReasonRemoved change record from its serializable form (§7). |
| `fieldTypeChangedFromMeta` | function | Rebuilds a FieldTypeChanged change record from its serializable form (§7). |
| `fieldArgumentAddedFromMeta` | function | Rebuilds a FieldArgumentAdded change record from its serializable form (§7). |
| `fieldArgumentRemovedFromMeta` | function | Rebuilds a FieldArgumentRemoved change record from its serializable form (§7). |
| `inputFieldRemovedFromMeta` | function | Rebuilds a InputFieldRemoved change record from its serializable form (§7). |
| `inputFieldAddedFromMeta` | function | Rebuilds a InputFieldAdded change record from its serializable form (§7). |
| `inputFieldDescriptionAddedFromMeta` | function | Rebuilds a InputFieldDescriptionAdded change record from its serializable form (§7). |
| `inputFieldDescriptionRemovedFromMeta` | function | Rebuilds a InputFieldDescriptionRemoved change record from its serializable form (§7). |
| `inputFieldDescriptionChangedFromMeta` | function | Rebuilds a InputFieldDescriptionChanged change record from its serializable form (§7). |
| `inputFieldDefaultValueChangedFromMeta` | function | Rebuilds a InputFieldDefaultValueChanged change record from its serializable form (§7). |
| `inputFieldTypeChangedFromMeta` | function | Rebuilds a InputFieldTypeChanged change record from its serializable form (§7). |
| `objectTypeInterfaceAddedFromMeta` | function | Rebuilds a ObjectTypeInterfaceAdded change record from its serializable form (§7). |
| `objectTypeInterfaceRemovedFromMeta` | function | Rebuilds a ObjectTypeInterfaceRemoved change record from its serializable form (§7). |
| `schemaQueryTypeChangedFromMeta` | function | Rebuilds a SchemaQueryTypeChanged change record from its serializable form (§7). |
| `schemaMutationTypeChangedFromMeta` | function | Rebuilds a SchemaMutationTypeChanged change record from its serializable form (§7). |
| `schemaSubscriptionTypeChangedFromMeta` | function | Rebuilds a SchemaSubscriptionTypeChanged change record from its serializable form (§7). |
| `typeRemovedFromMeta` | function | Rebuilds a TypeRemoved change record from its serializable form (§7). |
| `typeAddedFromMeta` | function | Rebuilds a TypeAdded change record from its serializable form (§7). |
| `typeKindChangedFromMeta` | function | Rebuilds a TypeKindChanged change record from its serializable form (§7). |
| `typeDescriptionChangedFromMeta` | function | Rebuilds a TypeDescriptionChanged change record from its serializable form (§7). |
| `typeDescriptionRemovedFromMeta` | function | Rebuilds a TypeDescriptionRemoved change record from its serializable form (§7). |
| `typeDescriptionAddedFromMeta` | function | Rebuilds a TypeDescriptionAdded change record from its serializable form (§7). |
| `unionMemberRemovedFromMeta` | function | Rebuilds a UnionMemberRemoved change record from its serializable form (§7). |
| `buildUnionMemberAddedMessageFromMeta` | function | Rebuilds a UnionMemberAdded change record from its serializable form (§7). |
| `FieldArgumentDescriptionChangedChange` | type | Serializable payload of a FieldArgumentDescriptionChanged change (§7). |
| `FieldArgumentDefaultChangedChange` | type | Serializable payload of a FieldArgumentDefaultChanged change (§7). |
| `FieldArgumentTypeChangedChange` | type | Serializable payload of a FieldArgumentTypeChanged change (§7). |
| `DirectiveRemovedChange` | type | Serializable payload of a DirectiveRemoved change (§7). |
| `DirectiveAddedChange` | type | Serializable payload of a DirectiveAdded change (§7). |
| `DirectiveDescriptionChangedChange` | type | Serializable payload of a DirectiveDescriptionChanged change (§7). |
| `DirectiveLocationAddedChange` | type | Serializable payload of a DirectiveLocationAdded change (§7). |
| `DirectiveLocationRemovedChange` | type | Serializable payload of a DirectiveLocationRemoved change (§7). |
| `DirectiveArgumentAddedChange` | type | Serializable payload of a DirectiveArgumentAdded change (§7). |
| `DirectiveArgumentRemovedChange` | type | Serializable payload of a DirectiveArgumentRemoved change (§7). |
| `DirectiveArgumentDescriptionChangedChange` | type | Serializable payload of a DirectiveArgumentDescriptionChanged change (§7). |
| `DirectiveArgumentDefaultValueChangedChange` | type | Serializable payload of a DirectiveArgumentDefaultValueChanged change (§7). |
| `DirectiveArgumentTypeChangedChange` | type | Serializable payload of a DirectiveArgumentTypeChanged change (§7). |
| `DirectiveRepeatableAddedChange` | type | Serializable payload of a DirectiveRepeatableAdded change (§7). |
| `DirectiveRepeatableRemovedChange` | type | Serializable payload of a DirectiveRepeatableRemoved change (§7). |
| `EnumValueRemovedChange` | type | Serializable payload of a EnumValueRemoved change (§7). |
| `EnumValueAddedChange` | type | Serializable payload of a EnumValueAdded change (§7). |
| `EnumValueDescriptionChangedChange` | type | Serializable payload of a EnumValueDescriptionChanged change (§7). |
| `EnumValueDeprecationReasonChangedChange` | type | Serializable payload of a EnumValueDeprecationReasonChanged change (§7). |
| `EnumValueDeprecationReasonAddedChange` | type | Serializable payload of a EnumValueDeprecationReasonAdded change (§7). |
| `EnumValueDeprecationReasonRemovedChange` | type | Serializable payload of a EnumValueDeprecationReasonRemoved change (§7). |
| `FieldRemovedChange` | type | Serializable payload of a FieldRemoved change (§7). |
| `FieldAddedChange` | type | Serializable payload of a FieldAdded change (§7). |
| `FieldDescriptionChangedChange` | type | Serializable payload of a FieldDescriptionChanged change (§7). |
| `FieldDescriptionAddedChange` | type | Serializable payload of a FieldDescriptionAdded change (§7). |
| `FieldDescriptionRemovedChange` | type | Serializable payload of a FieldDescriptionRemoved change (§7). |
| `FieldDeprecationAddedChange` | type | Serializable payload of a FieldDeprecationAdded change (§7). |
| `FieldDeprecationRemovedChange` | type | Serializable payload of a FieldDeprecationRemoved change (§7). |
| `FieldDeprecationReasonChangedChange` | type | Serializable payload of a FieldDeprecationReasonChanged change (§7). |
| `FieldDeprecationReasonAddedChange` | type | Serializable payload of a FieldDeprecationReasonAdded change (§7). |
| `FieldDeprecationReasonRemovedChange` | type | Serializable payload of a FieldDeprecationReasonRemoved change (§7). |
| `FieldTypeChangedChange` | type | Serializable payload of a FieldTypeChanged change (§7). |
| `FieldArgumentAddedChange` | type | Serializable payload of a FieldArgumentAdded change (§7). |
| `FieldArgumentRemovedChange` | type | Serializable payload of a FieldArgumentRemoved change (§7). |
| `InputFieldRemovedChange` | type | Serializable payload of a InputFieldRemoved change (§7). |
| `InputFieldAddedChange` | type | Serializable payload of a InputFieldAdded change (§7). |
| `InputFieldDescriptionAddedChange` | type | Serializable payload of a InputFieldDescriptionAdded change (§7). |
| `InputFieldDescriptionRemovedChange` | type | Serializable payload of a InputFieldDescriptionRemoved change (§7). |
| `InputFieldDescriptionChangedChange` | type | Serializable payload of a InputFieldDescriptionChanged change (§7). |
| `InputFieldDefaultValueChangedChange` | type | Serializable payload of a InputFieldDefaultValueChanged change (§7). |
| `InputFieldTypeChangedChange` | type | Serializable payload of a InputFieldTypeChanged change (§7). |
| `ObjectTypeInterfaceAddedChange` | type | Serializable payload of a ObjectTypeInterfaceAdded change (§7). |
| `ObjectTypeInterfaceRemovedChange` | type | Serializable payload of a ObjectTypeInterfaceRemoved change (§7). |
| `SchemaQueryTypeChangedChange` | type | Serializable payload of a SchemaQueryTypeChanged change (§7). |
| `SchemaMutationTypeChangedChange` | type | Serializable payload of a SchemaMutationTypeChanged change (§7). |
| `SchemaSubscriptionTypeChangedChange` | type | Serializable payload of a SchemaSubscriptionTypeChanged change (§7). |
| `TypeRemovedChange` | type | Serializable payload of a TypeRemoved change (§7). |
| `TypeAddedChange` | type | Serializable payload of a TypeAdded change (§7). |
| `TypeKindChangedChange` | type | Serializable payload of a TypeKindChanged change (§7). |
| `TypeDescriptionChangedChange` | type | Serializable payload of a TypeDescriptionChanged change (§7). |
| `TypeDescriptionRemovedChange` | type | Serializable payload of a TypeDescriptionRemoved change (§7). |
| `TypeDescriptionAddedChange` | type | Serializable payload of a TypeDescriptionAdded change (§7). |
| `UnionMemberRemovedChange` | type | Serializable payload of a UnionMemberRemoved change (§7). |
| `UnionMemberAddedChange` | type | Serializable payload of a UnionMemberAdded change (§7). |
| `DirectiveUsageArgumentDefinitionAddedChange` | type | Serializable payload of a DirectiveUsageArgumentDefinitionAdded change (§7). |
| `DirectiveUsageArgumentDefinitionRemovedChange` | type | Serializable payload of a DirectiveUsageArgumentDefinitionRemoved change (§7). |
| `DirectiveUsageEnumAddedChange` | type | Serializable payload of a DirectiveUsageEnumAdded change (§7). |
| `DirectiveUsageEnumRemovedChange` | type | Serializable payload of a DirectiveUsageEnumRemoved change (§7). |
| `DirectiveUsageEnumValueAddedChange` | type | Serializable payload of a DirectiveUsageEnumValueAdded change (§7). |
| `DirectiveUsageEnumValueRemovedChange` | type | Serializable payload of a DirectiveUsageEnumValueRemoved change (§7). |
| `DirectiveUsageFieldAddedChange` | type | Serializable payload of a DirectiveUsageFieldAdded change (§7). |
| `DirectiveUsageFieldDefinitionAddedChange` | type | Serializable payload of a DirectiveUsageFieldDefinitionAdded change (§7). |
| `DirectiveUsageFieldDefinitionRemovedChange` | type | Serializable payload of a DirectiveUsageFieldDefinitionRemoved change (§7). |
| `DirectiveUsageFieldRemovedChange` | type | Serializable payload of a DirectiveUsageFieldRemoved change (§7). |
| `DirectiveUsageInputFieldDefinitionAddedChange` | type | Serializable payload of a DirectiveUsageInputFieldDefinitionAdded change (§7). |
| `DirectiveUsageInputFieldDefinitionRemovedChange` | type | Serializable payload of a DirectiveUsageInputFieldDefinitionRemoved change (§7). |
| `DirectiveUsageInputObjectAddedChange` | type | Serializable payload of a DirectiveUsageInputObjectAdded change (§7). |
| `DirectiveUsageInputObjectRemovedChange` | type | Serializable payload of a DirectiveUsageInputObjectRemoved change (§7). |
| `DirectiveUsageInterfaceAddedChange` | type | Serializable payload of a DirectiveUsageInterfaceAdded change (§7). |
| `DirectiveUsageInterfaceRemovedChange` | type | Serializable payload of a DirectiveUsageInterfaceRemoved change (§7). |
| `DirectiveUsageObjectAddedChange` | type | Serializable payload of a DirectiveUsageObjectAdded change (§7). |
| `DirectiveUsageObjectRemovedChange` | type | Serializable payload of a DirectiveUsageObjectRemoved change (§7). |
| `DirectiveUsageScalarAddedChange` | type | Serializable payload of a DirectiveUsageScalarAdded change (§7). |
| `DirectiveUsageScalarRemovedChange` | type | Serializable payload of a DirectiveUsageScalarRemoved change (§7). |
| `DirectiveUsageSchemaAddedChange` | type | Serializable payload of a DirectiveUsageSchemaAdded change (§7). |
| `DirectiveUsageSchemaRemovedChange` | type | Serializable payload of a DirectiveUsageSchemaRemoved change (§7). |
| `DirectiveUsageUnionMemberAddedChange` | type | Serializable payload of a DirectiveUsageUnionMemberAdded change (§7). |
| `DirectiveUsageUnionMemberRemovedChange` | type | Serializable payload of a DirectiveUsageUnionMemberRemoved change (§7). |
| `DirectiveUsageArgumentAddedChange` | type | Serializable payload of a DirectiveUsageArgumentAdded change (§7). |
| `DirectiveUsageArgumentRemovedChange` | type | Serializable payload of a DirectiveUsageArgumentRemoved change (§7). |

The catalog lists 190 names. `DiffRule` additionally carries seven function members, named in §6.1, which are reachable only through it.

### 15.3 Package entry points

The package publishes a library only. It declares no `bin` entry and installs no executable. Its
sole runtime dependency requirement is the `graphql` peer dependency named in Appendix A; any other
dependency the implementation needs must be a normal dependency it declares and ships.

## Appendix A: Environment

**Runtime.** Node.js 22. The implementation must run on that version without a transpilation step
performed by the consumer.

**Peer dependency.** `graphql` is a peer dependency, declared as `^16.0.0 || ^17.0.0`. It is present
in the environment and must not be bundled or vendored. Every GraphQL type used in a signature comes
from that package.

**Network.** There is no network access at any point. Nothing is fetched at install time, at
build time or at run time. Every dependency the package needs must already be resolvable from the
environment.

**How the package is consumed — read this twice.** The consuming code is an **ES module**: its
`package.json` declares `"type": "module"`, and it reaches this package with
`import { ... } from '@graphql-inspector/core'`. Three requirements follow, and each of them has
independently broken an otherwise-correct implementation.

1. **The package must be importable by name.** After `npm install` is run from the package
   directory, `import { diff } from '@graphql-inspector/core'` executed by an ES module must
   resolve and load. Verify that, not `require.resolve`. Under ESM resolution an `exports` map
   **replaces** `main` rather than supplementing it: if `package.json` declares
   `"exports": { ".": { ... } }` and that entry has no `import` condition and no `default`
   condition, the specifier is unresolvable from an ES module no matter what `main` says — while
   `require.resolve` still succeeds. That combination passes a provenance check and fails every
   test file at load time. Either declare no `exports` map at all and rely on `main`, or declare
   one that includes an `import` or `default` condition pointing at a file that exists.
2. **The package must ship runnable JavaScript.** If the sources are TypeScript, the package must
   either publish the compiled output or compile during installation. Nothing runs a build step on
   your behalf: the consumer installs the package and imports it, and there is no opportunity
   between those two events for a `tsc` invocation you did not arrange yourself.
3. **The declared entry file must exist after installation.** Whatever `main`, `module`, `exports`
   or `types` points at must be a real file in the installed tree, not a path that only exists in
   the working copy before packing.

**Type declarations.** Consumers written in TypeScript type-check against the package. Declaration
files must accompany the JavaScript and must describe exactly the surface of §15, with the
parameter order, arity, types and optionality stated in §5 through §11.

**Test tooling.** The environment's test runner is Vitest 2.x. Do not rely on any API introduced in
Vitest 3, and do not pin a Vitest version in the package's own manifest that conflicts with the one
already installed in the environment.

## Appendix B: Assessment Notes

Assertions prefer the machine-readable half of every result: for the comparison projection, the
`type` value, the `path` string, the `criticality.level`, whether `criticality.reason` is present,
and the `meta` payload field by field; for the coverage projection, the `hits`, `fieldsCount`,
`fieldsCountCovered` and `stats` numbers and the set of reported type and child names; for the
similarity projection, the entry set, each entry's `bestMatch.target.typeId` and the ordering of
`ratings`; for the validation projection, which documents appear in the result and how many errors
each carries in `errors` and in `deprecated`.

They do not require the wording of `Change.message`, of `Change.criticality.reason`, or of any
`GraphQLError` this specification does not quote. §2 states that exclusion and §6.4 and §6.8 state
the only two exceptions, both of which are quoted verbatim there because a consumer observes the
replaced or extended text directly.

Change lists are compared as ordered lists, because §5.2 states an ordering rule for them and every
rule of §6 states whether it preserves that order. Coverage `types` maps, coverage `children` maps
and similarity results are compared by membership together with the per-entry numbers, since this
specification states no ordering rule for a JavaScript object's keys. A `locations` array is
compared as an ordered list, because §8.4 states that the most recently visited location is first.

Error paths are asserted as a thrown error or a rejected promise together with the absence of a
partial result, never as message text; §13 fixes which conditions raise and which return.

Floating-point ratings from §9.5 are compared with a tolerance, since the measure is a ratio of
integer counts and the specification fixes the counts rather than a printed decimal.

## Appendix C: Terminology

- **Coordinate** — a dot-joined address of a schema element, such as `User.email` or
  `User.email.locale`. Directive components carry a leading `@`, with the two exceptions noted in
  §5.11.
- **Projection** — one of the four top-level analyses: comparison, coverage, similarity,
  validation.
- **Change record** — the object described in §4.2.
- **Criticality** — the grade described in §4.1. "Breaking" is a statement about existing client
  operations, not about server implementations.
- **Serializable change** — the `{ type, meta }` pair from which a change record can be rebuilt, as
  described in §7.
- **Directive usage** — an application of a directive to a schema element, as opposed to the
  directive's definition. §5.10 covers definitions; §5.11 covers usages.
- **Stripped definition** — the normalised printed form of a type used by the similarity measure,
  defined in §9.3.
- **Reported type** — a type that appears in a coverage report's `types` map, as delimited in §8.3.
- **Simple change** — a change type that subsumes the finer changes beneath it, listed in §6.6.

