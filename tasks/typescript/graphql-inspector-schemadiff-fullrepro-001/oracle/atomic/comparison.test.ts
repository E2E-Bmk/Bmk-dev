import { expect, test } from 'vitest';
import { CriticalityLevel, diff } from '@graphql-inspector/core';

import { outline } from '../helpers';
import { buildSchema } from '../peer';

/* One comparison per test: two schemas in, one change list out. Every
   assertion reads the machine-readable half of a change record -- the change
   type, the coordinate, the criticality grade, whether a reason accompanies it,
   and the meta payload. Message and reason wording are never asserted. */


// Verifies: GQLI-DIFF-031, GQLI-DIFF-032, GQLI-DIFF-035
test("field argument: added non-nullable with default value", async () => {
  const before = buildSchema(`
    type Query {
      a: String
    }
  `);
  const after = buildSchema(`
    type Query {
      a(b: Boolean! = true): String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ARGUMENT_ADDED",
      path: "Query.a.b",
      level: CriticalityLevel.Dangerous,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Query",
        fieldName: "a",
        addedArgumentName: "b",
        addedArgumentType: "Boolean!",
        hasDefaultValue: true,
        addedToNewField: false,
        isAddedFieldArgumentBreaking: false,
      });
});

// Verifies: GQLI-DIFF-031, GQLI-DIFF-032, GQLI-DIFF-035
test("field argument: default value added", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
    }
    type Dummy {
      field(foo: Foo): String
    }
  `);
  const after = buildSchema(`
    input Foo {
      a: String!
    }
    type Dummy {
      field(foo: Foo = { a: "a" }): String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ARGUMENT_DEFAULT_CHANGED",
      path: "Dummy.field.foo",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Dummy",
        fieldName: "field",
        argumentName: "foo",
        newDefaultValue: "{ a: 'a' }",
      });
});

// Verifies: GQLI-DIFF-031, GQLI-DIFF-032, GQLI-DIFF-035
test("field argument: default value changed", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
    }
    type Dummy {
      field(foo: Foo = { a: "a" }): String
    }
  `);
  const after = buildSchema(`
    input Foo {
      a: String!
    }
    type Dummy {
      field(foo: Foo = { a: "new-value" }): String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ARGUMENT_DEFAULT_CHANGED",
      path: "Dummy.field.foo",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Dummy",
        fieldName: "field",
        argumentName: "foo",
        oldDefaultValue: "{ a: 'a' }",
        newDefaultValue: "{ a: 'new-value' }",
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: added", async () => {
  const before = buildSchema(`
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    directive @foo on FIELD
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_ADDED",
      path: "@foo",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_LOCATION_ADDED",
      path: "@foo",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedDirectiveName: "foo",
        addedDirectiveDescription: null,
        addedDirectiveLocations: ["FIELD"],
        addedDirectiveRepeatable: false,
      });
  expect(changes[1].meta).toEqual({
        directiveName: "foo",
        addedDirectiveLocation: "FIELD",
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: removed", async () => {
  const before = buildSchema(`
    directive @foo on FIELD
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_REMOVED",
      path: "@foo",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        removedDirectiveName: "foo",
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: description", async () => {
  const before = buildSchema(`
    """
    AAA
    """
    directive @a on FIELD
    directive @b on FIELD
    """
    Ccc
    """
    directive @c on FIELD
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    """
    aaa
    """
    directive @a on FIELD
    """
    Bbb
    """
    directive @b on FIELD
    directive @c on FIELD
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_DESCRIPTION_CHANGED",
      path: "@a",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_DESCRIPTION_CHANGED",
      path: "@b",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_DESCRIPTION_CHANGED",
      path: "@c",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        directiveName: "a",
        oldDirectiveDescription: "AAA",
        newDirectiveDescription: "aaa",
      });
  expect(changes[1].meta).toEqual({
        directiveName: "b",
        oldDirectiveDescription: null,
        newDirectiveDescription: "Bbb",
      });
  expect(changes[2].meta).toEqual({
        directiveName: "c",
        oldDirectiveDescription: "Ccc",
        newDirectiveDescription: null,
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: location removed", async () => {
  const before = buildSchema(`
    directive @a on FIELD | ENUM_VALUE
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    directive @a on FIELD
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_LOCATION_REMOVED",
      path: "@a",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        directiveName: "a",
        removedDirectiveLocation: "ENUM_VALUE",
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: arguments added", async () => {
  const before = buildSchema(`
    directive @a on FIELD
    directive @b on FIELD
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    directive @a(name: String) on FIELD
    directive @b(name: String!) on FIELD
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_ARGUMENT_ADDED",
      path: "@a",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "DIRECTIVE_ARGUMENT_ADDED",
      path: "@b",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        directiveName: "a",
        addedDirectiveArgumentName: "name",
        addedDirectiveArgumentType: "String",
        addedDirectiveArgumentTypeIsNonNull: false,
        addedToNewDirective: false,
      });
  expect(changes[1].meta).toEqual({
        directiveName: "b",
        addedDirectiveArgumentName: "name",
        addedDirectiveArgumentType: "String!",
        addedDirectiveArgumentTypeIsNonNull: true,
        addedToNewDirective: false,
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: arguments removed", async () => {
  const before = buildSchema(`
    directive @a(name: String) on FIELD
    directive @b(name: String!) on FIELD
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    directive @a on FIELD
    directive @b on FIELD
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_ARGUMENT_REMOVED",
      path: "@a.name",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
    {
      type: "DIRECTIVE_ARGUMENT_REMOVED",
      path: "@b.name",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        directiveName: "a",
        removedDirectiveArgumentName: "name",
      });
  expect(changes[1].meta).toEqual({
        directiveName: "b",
        removedDirectiveArgumentName: "name",
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: arguments changed", async () => {
  const before = buildSchema(`
    directive @a(name: String) on FIELD
    directive @b(name: String!) on FIELD
    directive @c(name: String) on FIELD
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    directive @a(name: Int) on FIELD
    directive @b(name: String) on FIELD
    directive @c(name: String!) on FIELD
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_ARGUMENT_TYPE_CHANGED",
      path: "@a.name",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_ARGUMENT_TYPE_CHANGED",
      path: "@b.name",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "DIRECTIVE_ARGUMENT_TYPE_CHANGED",
      path: "@c.name",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        directiveName: "a",
        directiveArgumentName: "name",
        oldDirectiveArgumentType: "String",
        newDirectiveArgumentType: "Int",
        isSafeDirectiveArgumentTypeChange: false,
      });
  expect(changes[1].meta).toEqual({
        directiveName: "b",
        directiveArgumentName: "name",
        oldDirectiveArgumentType: "String!",
        newDirectiveArgumentType: "String",
        isSafeDirectiveArgumentTypeChange: true,
      });
  expect(changes[2].meta).toEqual({
        directiveName: "c",
        directiveArgumentName: "name",
        oldDirectiveArgumentType: "String",
        newDirectiveArgumentType: "String!",
        isSafeDirectiveArgumentTypeChange: false,
      });
});

// Verifies: GQLI-DIFF-051, GQLI-DIFF-052, GQLI-DIFF-055
test("directive definition: default value", async () => {
  const before = buildSchema(`
    directive @a(name: String! = "aaa") on FIELD
    directive @b(name: String) on FIELD
    directive @c(name: String!) on FIELD
    directive @d(name: String! = "Ddd") on FIELD
    directive @e(name: String = "Eee") on FIELD
    type Dummy {
      field: String
    }
  `);
  const after = buildSchema(`
    directive @a(name: String! = "AAA") on FIELD
    directive @b(name: String = "Bbb") on FIELD
    directive @c(name: String! = "Ccc") on FIELD
    directive @d(name: String!) on FIELD
    directive @e(name: String) on FIELD
    type Dummy {
      field: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_ARGUMENT_DEFAULT_VALUE_CHANGED",
      path: "@a.name",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "DIRECTIVE_ARGUMENT_DEFAULT_VALUE_CHANGED",
      path: "@b.name",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "DIRECTIVE_ARGUMENT_DEFAULT_VALUE_CHANGED",
      path: "@c.name",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "DIRECTIVE_ARGUMENT_DEFAULT_VALUE_CHANGED",
      path: "@d.name",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "DIRECTIVE_ARGUMENT_DEFAULT_VALUE_CHANGED",
      path: "@e.name",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        directiveName: "a",
        directiveArgumentName: "name",
        oldDirectiveArgumentDefaultValue: "\"aaa\"",
        newDirectiveArgumentDefaultValue: "\"AAA\"",
      });
  expect(changes[1].meta).toEqual({
        directiveName: "b",
        directiveArgumentName: "name",
        newDirectiveArgumentDefaultValue: "\"Bbb\"",
      });
  expect(changes[2].meta).toEqual({
        directiveName: "c",
        directiveArgumentName: "name",
        newDirectiveArgumentDefaultValue: "\"Ccc\"",
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: added", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      """
      A is the first letter in the alphabet
      """
      A
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "TYPE_ADDED",
      path: "enumA",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "ENUM_VALUE_ADDED",
      path: "enumA.A",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "ENUM_VALUE_DESCRIPTION_CHANGED",
      path: "enumA.A",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "ENUM_VALUE_ADDED",
      path: "enumA.B",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedTypeKind: "EnumTypeDefinition",
        addedTypeName: "enumA",
      });
  expect(changes[1].meta).toEqual({
        enumName: "enumA",
        addedEnumValueName: "A",
        addedToNewType: true,
        addedDirectiveDescription: "A is the first letter in the alphabet",
      });
  expect(changes[2].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        oldEnumValueDescription: null,
        newEnumValueDescription: "A is the first letter in the alphabet",
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: value removed", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "ENUM_VALUE_REMOVED",
      path: "enumA.B",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        removedEnumValueName: "B",
        isEnumValueDeprecated: false,
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: description changed", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
    """
    Old Description
    """
    enum enumA {
      A
      B
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    """
    New Description
    """
    enum enumA {
      A
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "TYPE_DESCRIPTION_CHANGED",
      path: "enumA",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "enumA",
        newTypeDescription: "New Description",
        oldTypeDescription: "Old Description",
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: deprecation reason changed", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A @deprecated(reason: "Old Reason")
      B
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A @deprecated(reason: "New Reason")
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "ENUM_VALUE_DEPRECATION_REASON_CHANGED",
      path: "enumA.A.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_REMOVED",
      path: "enumA.A.@deprecated.reason",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_ADDED",
      path: "enumA.A.@deprecated.reason",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        oldEnumValueDeprecationReason: "Old Reason",
        newEnumValueDeprecationReason: "New Reason",
      });
  expect(changes[1].meta).toEqual({
        removedArgumentName: "reason",
        directiveName: "deprecated",
        parentTypeName: "enumA",
        parentFieldName: null,
        parentArgumentName: null,
        parentEnumValueName: "A",
        directiveRepeatedTimes: 1,
      });
  expect(changes[2].meta).toEqual({
        addedArgumentName: "reason",
        addedArgumentValue: "\"New Reason\"",
        oldArgumentValue: "\"Old Reason\"",
        directiveName: "deprecated",
        parentTypeName: "enumA",
        parentFieldName: null,
        parentArgumentName: null,
        parentEnumValueName: "A",
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: deprecation reason added", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A @deprecated(reason: "New Reason")
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "ENUM_VALUE_DEPRECATION_REASON_ADDED",
      path: "enumA.A.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_ENUM_VALUE_ADDED",
      path: "enumA.A.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_ADDED",
      path: "enumA.A.@deprecated.reason",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        addedValueDeprecationReason: "New Reason",
      });
  expect(changes[1].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        addedDirectiveName: "deprecated",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
  expect(changes[2].meta).toEqual({
        addedArgumentName: "reason",
        addedArgumentValue: "\"New Reason\"",
        oldArgumentValue: null,
        directiveName: "deprecated",
        parentTypeName: "enumA",
        parentFieldName: null,
        parentArgumentName: null,
        parentEnumValueName: "A",
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: deprecation reason removed", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A @deprecated(reason: "New Reason")
      B
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "ENUM_VALUE_DEPRECATION_REASON_REMOVED",
      path: "enumA.A",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_ENUM_VALUE_REMOVED",
      path: "enumA.A.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        removedEnumValueDeprecationReason: "New Reason",
      });
  expect(changes[1].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        removedDirectiveName: "deprecated",
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: value added", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
      C
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "ENUM_VALUE_ADDED",
      path: "enumA.C",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        addedEnumValueName: "C",
        addedToNewType: false,
        addedDirectiveDescription: null,
      });
});

// Verifies: GQLI-DIFF-043, GQLI-DIFF-044, GQLI-DIFF-074
test("enum: string escaping deprecation reason added with escaped single quotes", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: String
    }
    enum enumA {
      A @deprecated(reason: "Don't use this")
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "ENUM_VALUE_DEPRECATION_REASON_ADDED",
      path: "enumA.A.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_ENUM_VALUE_ADDED",
      path: "enumA.A.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_ADDED",
      path: "enumA.A.@deprecated.reason",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        addedValueDeprecationReason: "Don't use this",
      });
  expect(changes[1].meta).toEqual({
        enumName: "enumA",
        enumValueName: "A",
        addedDirectiveName: "deprecated",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
  expect(changes[2].meta).toEqual({
        addedArgumentName: "reason",
        addedArgumentValue: "\"Don't use this\"",
        oldArgumentValue: null,
        directiveName: "deprecated",
        parentTypeName: "enumA",
        parentFieldName: null,
        parentArgumentName: null,
        parentEnumValueName: "A",
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields added", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
      b: String!
    }
  `);
  const after = buildSchema(`
    input Foo {
      a: String!
      b: String!
      c: String!
      d: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "INPUT_FIELD_ADDED",
      path: "Foo.c",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
    {
      type: "INPUT_FIELD_ADDED",
      path: "Foo.d",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        inputName: "Foo",
        addedInputFieldName: "c",
        isAddedInputFieldTypeNullable: false,
        addedInputFieldType: "String!",
        addedToNewType: false,
      });
  expect(changes[1].meta).toEqual({
        inputName: "Foo",
        addedInputFieldName: "d",
        isAddedInputFieldTypeNullable: true,
        addedInputFieldType: "String",
        addedToNewType: false,
      });
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields removed", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
      b: String!
      c: String!
    }
  `);
  const after = buildSchema(`
    input Foo {
      a: String!
      b: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "INPUT_FIELD_REMOVED",
      path: "Foo.c",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        inputName: "Foo",
        removedFieldName: "c",
        isInputFieldDeprecated: false,
      });
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields type changed", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
      b: String
      c: String!
    }
  `);
  const after = buildSchema(`
    input Foo {
      a: Int!
      b: String!
      c: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "INPUT_FIELD_TYPE_CHANGED",
      path: "Foo.a",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
    {
      type: "INPUT_FIELD_TYPE_CHANGED",
      path: "Foo.b",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
    {
      type: "INPUT_FIELD_TYPE_CHANGED",
      path: "Foo.c",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "a",
        oldInputFieldType: "String!",
        newInputFieldType: "Int!",
        isInputFieldTypeChangeSafe: false,
      });
  expect(changes[1].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "b",
        oldInputFieldType: "String",
        newInputFieldType: "String!",
        isInputFieldTypeChangeSafe: false,
      });
  expect(changes[2].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "c",
        oldInputFieldType: "String!",
        newInputFieldType: "String",
        isInputFieldTypeChangeSafe: true,
      });
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields description changed / added / removed", async () => {
  const before = buildSchema(`
    input Foo {
      """
      OLD
      """
      a: String!
      """
      BBB
      """
      b: String!
      c: String!
    }
  `);
  const after = buildSchema(`
    input Foo {
      """
      NEW
      """
      a: String!
      b: String!
      """
      CCC
      """
      c: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "INPUT_FIELD_DESCRIPTION_CHANGED",
      path: "Foo.a",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "INPUT_FIELD_DESCRIPTION_REMOVED",
      path: "Foo.b",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "INPUT_FIELD_DESCRIPTION_ADDED",
      path: "Foo.c",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "a",
        oldInputFieldDescription: "OLD",
        newInputFieldDescription: "NEW",
      });
  expect(changes[1].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "b",
        removedDescription: "BBB",
      });
  expect(changes[2].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "c",
        addedInputFieldDescription: "CCC",
      });
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields default value added", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
      b: String
    }
  `);
  const after = buildSchema(`
    input Foo {
      a: String! = "Aaa"
      b: String = "Bbb"
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "INPUT_FIELD_DEFAULT_VALUE_CHANGED",
      path: "Foo.a",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "INPUT_FIELD_DEFAULT_VALUE_CHANGED",
      path: "Foo.b",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "a",
        newDefaultValue: "\"Aaa\"",
      });
  expect(changes[1].meta).toEqual({
        inputName: "Foo",
        inputFieldName: "b",
        newDefaultValue: "\"Bbb\"",
      });
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields added with a default value", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
    }
  `);
  const after = buildSchema(`
    input Foo {
      a: String!
      b: String! = "B"
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "INPUT_FIELD_ADDED",
      path: "Foo.b",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        inputName: "Foo",
        addedInputFieldName: "b",
        isAddedInputFieldTypeNullable: false,
        addedInputFieldType: "String!",
        addedFieldDefault: "\"B\"",
        addedToNewType: false,
      });
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields order changed", async () => {
  const before = buildSchema(`
    input Foo {
      a: String!
      b: String!
    }
  `);
  const after = buildSchema(`
    input Foo {
      b: String!
      a: String!
    }
  `);

  const changes = await diff(before, after);

  expect(changes).toEqual([]);
});

// Verifies: GQLI-DIFF-038, GQLI-DIFF-039, GQLI-DIFF-041
test("input object: fields added to an added input", async () => {
  const before = buildSchema(`
    type Query {
      _: String
    }
  `);
  const after = buildSchema(`
    type Query {
      _: String
    }
    input Foo {
      a: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "TYPE_ADDED",
      path: "Foo",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "INPUT_FIELD_ADDED",
      path: "Foo.a",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedTypeKind: "InputObjectTypeDefinition",
        addedTypeIsOneOf: false,
        addedTypeName: "Foo",
      });
  expect(changes[1].meta).toEqual({
        inputName: "Foo",
        addedInputFieldName: "a",
        isAddedInputFieldTypeNullable: false,
        addedInputFieldType: "String!",
        addedToNewType: true,
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-023, GQLI-DIFF-027
test("interface: fields added", async () => {
  const before = buildSchema(`
    interface Foo {
      a: String!
      b: String!
    }
  `);
  const after = buildSchema(`
    interface Foo {
      a: String!
      b: String!
      c: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ADDED",
      path: "Foo.c",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        addedFieldName: "c",
        typeType: "interface",
        addedFieldReturnType: "String!",
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-023, GQLI-DIFF-027
test("interface: fields removed", async () => {
  const before = buildSchema(`
    interface Foo {
      a: String!
      b: String!
      c: String!
    }
  `);
  const after = buildSchema(`
    interface Foo {
      a: String!
      b: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_REMOVED",
      path: "Foo.c",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        removedFieldName: "c",
        isRemovedFieldDeprecated: false,
        typeType: "interface",
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-023, GQLI-DIFF-027
test("interface: fields type changed", async () => {
  const before = buildSchema(`
    interface Foo {
      a: String!
      b: String
      c: String!
    }
  `);
  const after = buildSchema(`
    interface Foo {
      a: Int!
      b: String!
      c: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Foo.a",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Foo.b",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Foo.c",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        fieldName: "a",
        oldFieldType: "String!",
        newFieldType: "Int!",
        isSafeFieldTypeChange: false,
      });
  expect(changes[1].meta).toEqual({
        typeName: "Foo",
        fieldName: "b",
        oldFieldType: "String",
        newFieldType: "String!",
        isSafeFieldTypeChange: true,
      });
  expect(changes[2].meta).toEqual({
        typeName: "Foo",
        fieldName: "c",
        oldFieldType: "String!",
        newFieldType: "String",
        isSafeFieldTypeChange: false,
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-023, GQLI-DIFF-027
test("interface: fields description changed / added / removed", async () => {
  const before = buildSchema(`
    interface Foo {
      """
      OLD
      """
      a: String!
      """
      BBB
      """
      b: String!
      c: String!
    }
  `);
  const after = buildSchema(`
    interface Foo {
      """
      NEW
      """
      a: String!
      b: String!
      """
      CCC
      """
      c: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_DESCRIPTION_CHANGED",
      path: "Foo.a",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_DESCRIPTION_REMOVED",
      path: "Foo.b",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_DESCRIPTION_ADDED",
      path: "Foo.c",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        fieldName: "a",
        typeName: "Foo",
        oldDescription: "OLD",
        newDescription: "NEW",
      });
  expect(changes[1].meta).toEqual({
        typeName: "Foo",
        fieldName: "b",
      });
  expect(changes[2].meta).toEqual({
        typeName: "Foo",
        fieldName: "c",
        addedDescription: "CCC",
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-023, GQLI-DIFF-027
test("interface: fields deprecation reason changed / added / removed", async () => {
  const before = buildSchema(`
    interface Foo {
      a: String! @deprecated(reason: "OLD")
      b: String! @deprecated(reason: "BBB")
      c: String!
    }
  `);
  const after = buildSchema(`
    interface Foo {
      a: String! @deprecated(reason: "NEW")
      b: String!
      c: String! @deprecated(reason: "CCC")
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_DEPRECATION_REASON_CHANGED",
      path: "Foo.a.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_REMOVED",
      path: "Foo.a.@deprecated.reason",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_ADDED",
      path: "Foo.a.@deprecated.reason",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_DEPRECATION_REMOVED",
      path: "Foo.b.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_FIELD_DEFINITION_REMOVED",
      path: "Foo.b.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "FIELD_DEPRECATION_ADDED",
      path: "Foo.c.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_FIELD_DEFINITION_ADDED",
      path: "Foo.c.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_ADDED",
      path: "Foo.c.@deprecated.reason",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        fieldName: "a",
        typeName: "Foo",
        newDeprecationReason: "NEW",
        oldDeprecationReason: "OLD",
      });
  expect(changes[1].meta).toEqual({
        removedArgumentName: "reason",
        directiveName: "deprecated",
        parentTypeName: "Foo",
        parentFieldName: "a",
        parentArgumentName: null,
        parentEnumValueName: null,
        directiveRepeatedTimes: 1,
      });
  expect(changes[2].meta).toEqual({
        addedArgumentName: "reason",
        addedArgumentValue: "\"NEW\"",
        oldArgumentValue: "\"OLD\"",
        directiveName: "deprecated",
        parentTypeName: "Foo",
        parentFieldName: "a",
        parentArgumentName: null,
        parentEnumValueName: null,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-023, GQLI-DIFF-027
test("interface: deprecation added w/reason", async () => {
  const before = buildSchema(`
    interface Foo {
      a: String!
    }
  `);
  const after = buildSchema(`
    interface Foo {
      a: String! @deprecated(reason: "A is the first letter.")
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_DEPRECATION_ADDED",
      path: "Foo.a.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "DIRECTIVE_USAGE_FIELD_DEFINITION_ADDED",
      path: "Foo.a.@deprecated",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "DIRECTIVE_USAGE_ARGUMENT_ADDED",
      path: "Foo.a.@deprecated.reason",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        fieldName: "a",
        deprecationReason: "A is the first letter.",
      });
  expect(changes[1].meta).toEqual({
        addedDirectiveName: "deprecated",
        fieldName: "a",
        typeName: "Foo",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
  expect(changes[2].meta).toEqual({
        addedArgumentName: "reason",
        addedArgumentValue: "\"A is the first letter.\"",
        oldArgumentValue: null,
        directiveName: "deprecated",
        parentTypeName: "Foo",
        parentFieldName: "a",
        parentArgumentName: null,
        parentEnumValueName: null,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: added", async () => {
  const before = buildSchema(`
    type A {
      a: String!
    }
    type Foo {
      a: String!
    }
  `);
  const after = buildSchema(`
    type A {
      a: String!
    }
    type B {
      a: String!
    }
    type Mutation {
      noop: String
    }
    type Foo {
      a: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "SCHEMA_MUTATION_TYPE_CHANGED",
      path: undefined,
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "TYPE_ADDED",
      path: "B",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_ADDED",
      path: "B.a",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "TYPE_ADDED",
      path: "Mutation",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_ADDED",
      path: "Mutation.noop",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        newMutationTypeName: "Mutation",
        oldMutationTypeName: null,
      });
  expect(changes[1].meta).toEqual({
        addedTypeKind: "ObjectTypeDefinition",
        addedTypeName: "B",
      });
  expect(changes[2].meta).toEqual({
        typeName: "B",
        addedFieldName: "a",
        typeType: "object type",
        addedFieldReturnType: "String!",
      });
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: interfaces added", async () => {
  const before = buildSchema(`
    interface A {
      a: String!
    }
    interface B {
      b: String!
    }
    type Foo implements A & B {
      a: String!
      b: String!
    }
  `);
  const after = buildSchema(`
    interface A {
      a: String!
    }
    interface B {
      b: String!
    }
    interface C implements B {
      b: String!
      c: String!
    }
    type Foo implements A & B & C {
      a: String!
      b: String!
      c: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "TYPE_ADDED",
      path: "C",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "OBJECT_TYPE_INTERFACE_ADDED",
      path: "C",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
    {
      type: "FIELD_ADDED",
      path: "C.b",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_ADDED",
      path: "C.c",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "OBJECT_TYPE_INTERFACE_ADDED",
      path: "Foo",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: "FIELD_ADDED",
      path: "Foo.c",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedTypeKind: "InterfaceTypeDefinition",
        addedTypeName: "C",
      });
  expect(changes[1].meta).toEqual({
        objectTypeName: "C",
        addedInterfaceName: "B",
        addedToNewType: true,
      });
  expect(changes[2].meta).toEqual({
        typeName: "C",
        addedFieldName: "b",
        typeType: "interface",
        addedFieldReturnType: "String!",
      });
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: interfaces removed", async () => {
  const before = buildSchema(`
    interface A {
      a: String!
    }
    interface B {
      b: String!
    }
    interface C {
      c: String!
    }
    type Foo implements A & B & C {
      a: String!
      b: String!
      c: String!
    }
  `);
  const after = buildSchema(`
    interface A {
      a: String!
    }
    interface B {
      b: String!
    }
    type Foo implements A & B {
      a: String!
      b: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "TYPE_REMOVED",
      path: "C",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "OBJECT_TYPE_INTERFACE_REMOVED",
      path: "Foo",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
    {
      type: "FIELD_REMOVED",
      path: "Foo.c",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        removedTypeName: "C",
      });
  expect(changes[1].meta).toEqual({
        objectTypeName: "Foo",
        removedInterfaceName: "C",
      });
  expect(changes[2].meta).toEqual({
        typeName: "Foo",
        removedFieldName: "c",
        isRemovedFieldDeprecated: false,
        typeType: "object type",
      });
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: arguments type changed", async () => {
  const before = buildSchema(`
    type Foo {
      foo(a: String, b: String, c: String!): String
    }
  `);
  const after = buildSchema(`
    type Foo {
      foo(a: Int, b: String!, c: String): String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ARGUMENT_TYPE_CHANGED",
      path: "Foo.foo.a",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
    {
      type: "FIELD_ARGUMENT_TYPE_CHANGED",
      path: "Foo.foo.b",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
    {
      type: "FIELD_ARGUMENT_TYPE_CHANGED",
      path: "Foo.foo.c",
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        fieldName: "foo",
        argumentName: "a",
        oldArgumentType: "String",
        newArgumentType: "Int",
        isSafeArgumentTypeChange: false,
      });
  expect(changes[1].meta).toEqual({
        typeName: "Foo",
        fieldName: "foo",
        argumentName: "b",
        oldArgumentType: "String",
        newArgumentType: "String!",
        isSafeArgumentTypeChange: false,
      });
  expect(changes[2].meta).toEqual({
        typeName: "Foo",
        fieldName: "foo",
        argumentName: "c",
        oldArgumentType: "String!",
        newArgumentType: "String",
        isSafeArgumentTypeChange: true,
      });
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: arguments removed", async () => {
  const before = buildSchema(`
    type Foo {
      foo(a: String, b: String!, c: String): String
    }
  `);
  const after = buildSchema(`
    type Foo {
      foo(a: String): String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ARGUMENT_REMOVED",
      path: "Foo.foo.b",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "FIELD_ARGUMENT_REMOVED",
      path: "Foo.foo.c",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        fieldName: "foo",
        removedFieldArgumentName: "b",
        removedFieldType: "String!",
      });
  expect(changes[1].meta).toEqual({
        typeName: "Foo",
        fieldName: "foo",
        removedFieldArgumentName: "c",
        removedFieldType: "String",
      });
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: fields order changed", async () => {
  const before = buildSchema(`
    type Foo {
      a: String!
      b: String!
    }
  `);
  const after = buildSchema(`
    type Foo {
      b: String!
      a: String!
    }
  `);

  const changes = await diff(before, after);

  expect(changes).toEqual([]);
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: arguments added", async () => {
  const before = buildSchema(`
    type Foo {
      foo(a: String): String
    }
  `);
  const after = buildSchema(`
    type Foo {
      foo(a: String, b: String!, c: String): String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ARGUMENT_ADDED",
      path: "Foo.foo.b",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "FIELD_ARGUMENT_ADDED",
      path: "Foo.foo.c",
      level: CriticalityLevel.Dangerous,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        fieldName: "foo",
        addedArgumentName: "b",
        addedArgumentType: "String!",
        hasDefaultValue: false,
        addedToNewField: false,
        isAddedFieldArgumentBreaking: true,
      });
  expect(changes[1].meta).toEqual({
        typeName: "Foo",
        fieldName: "foo",
        addedArgumentName: "c",
        addedArgumentType: "String",
        hasDefaultValue: false,
        addedToNewField: false,
        isAddedFieldArgumentBreaking: false,
      });
});

// Verifies: GQLI-DIFF-023, GQLI-DIFF-024, GQLI-DIFF-027
test("object type: fields added", async () => {
  const before = buildSchema(`
    type Foo {
      a: String!
      b: String!
    }
  `);
  const after = buildSchema(`
    type Foo {
      a: String!
      b: String!
      c: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ADDED",
      path: "Foo.c",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Foo",
        addedFieldName: "c",
        typeType: "object type",
        addedFieldReturnType: "String!",
      });
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: renamed query", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String!
    }
  `);
  const after = buildSchema(`
    type RootQuery {
      fieldA: String!
    }
    schema {
      query: RootQuery
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "SCHEMA_QUERY_TYPE_CHANGED",
      path: undefined,
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "TYPE_REMOVED",
      path: "Query",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "TYPE_ADDED",
      path: "RootQuery",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_ADDED",
      path: "RootQuery.fieldA",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        oldQueryTypeName: "Query",
        newQueryTypeName: "RootQuery",
      });
  expect(changes[1].meta).toEqual({
        removedTypeName: "Query",
      });
  expect(changes[2].meta).toEqual({
        addedTypeKind: "ObjectTypeDefinition",
        addedTypeName: "RootQuery",
      });
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: new field and field changed", async () => {
  const before = buildSchema(`
    type Query {
      fieldA: String!
    }
  `);
  const after = buildSchema(`
    type Query {
      fieldA: Int
      fieldB: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ADDED",
      path: "Query.fieldB",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Query.fieldA",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Query",
        addedFieldName: "fieldB",
        typeType: "object type",
        addedFieldReturnType: "String",
      });
  expect(changes[1].meta).toEqual({
        typeName: "Query",
        fieldName: "fieldA",
        oldFieldType: "String!",
        newFieldType: "Int",
        isSafeFieldTypeChange: false,
      });
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: array as default value in argument (same)", async () => {
  const before = buildSchema(`
    interface MyInterface {
      a(b: [String] = ["Hello"]): String!
    }
  `);
  const after = buildSchema(`
    interface MyInterface {
      a(b: [String] = ["Hello"]): String!
    }
  `);

  const changes = await diff(before, after);

  expect(changes).toEqual([]);
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: array as default value in argument (different)", async () => {
  const before = buildSchema(`
    interface MyInterface {
      a(b: [String] = ["Hello"]): String!
    }
  `);
  const after = buildSchema(`
    interface MyInterface {
      a(b: [String] = ["Goodbye"]): String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_ARGUMENT_DEFAULT_CHANGED",
      path: "MyInterface.a.b",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "MyInterface",
        fieldName: "a",
        argumentName: "b",
        oldDefaultValue: "[ 'Hello' ]",
        newDefaultValue: "[ 'Goodbye' ]",
      });
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: same schema", async () => {
  const before = buildSchema(`
    type Post {
      id: ID
    }
    type Query {
      fieldA: Post!
    }
  `);
  const after = buildSchema(`
    type Post {
      id: ID
    }
    type Query {
      fieldA: Post!
    }
  `);

  const changes = await diff(before, after);

  expect(changes).toEqual([]);
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: array as default value in input (same)", async () => {
  const before = buildSchema(`
    enum SortOrder {
      ASC
    }
    input CommentQuery {
      limit: Int!
      sortOrder: [SortOrder] = [ASC]
    }
  `);
  const after = buildSchema(`
    enum SortOrder {
      ASC
    }
    input CommentQuery {
      limit: Int!
      sortOrder: [SortOrder] = [ASC]
    }
  `);

  const changes = await diff(before, after);

  expect(changes).toEqual([]);
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: array as default value in input (different)", async () => {
  const before = buildSchema(`
    enum SortOrder {
      ASC
      DEC
    }
    input CommentQuery {
      limit: Int!
      sortOrder: [SortOrder] = [ASC]
    }
  `);
  const after = buildSchema(`
    enum SortOrder {
      ASC
      DEC
    }
    input CommentQuery {
      limit: Int!
      sortOrder: [SortOrder] = [DEC]
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "INPUT_FIELD_DEFAULT_VALUE_CHANGED",
      path: "CommentQuery.sortOrder",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        inputName: "CommentQuery",
        inputFieldName: "sortOrder",
        oldDefaultValue: "[ 'ASC' ]",
        newDefaultValue: "[ 'DEC' ]",
      });
});

// Verifies: GQLI-DIFF-012, GQLI-DIFF-016, GQLI-DIFF-021
test("schema: Query fields becoming non-nullable is a non-breaking change", async () => {
  const before = buildSchema(`
    scalar CustomScalar
    type Comment {
      limit: Int
      query: String
      detail: Detail
      customScalar: CustomScalar
    }
    type Detail {
      field: String!
    }
  `);
  const after = buildSchema(`
    scalar CustomScalar
    type Comment {
      limit: Int!
      query: String!
      detail: Detail!
      customScalar: CustomScalar!
    }
    type Detail {
      field: String!
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Comment.limit",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Comment.query",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Comment.detail",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_TYPE_CHANGED",
      path: "Comment.customScalar",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(changes[0].meta).toEqual({
        typeName: "Comment",
        fieldName: "limit",
        oldFieldType: "Int",
        newFieldType: "Int!",
        isSafeFieldTypeChange: true,
      });
  expect(changes[1].meta).toEqual({
        typeName: "Comment",
        fieldName: "query",
        oldFieldType: "String",
        newFieldType: "String!",
        isSafeFieldTypeChange: true,
      });
  expect(changes[2].meta).toEqual({
        typeName: "Comment",
        fieldName: "detail",
        oldFieldType: "Detail",
        newFieldType: "Detail!",
        isSafeFieldTypeChange: true,
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-048
test("union: member added", async () => {
  const before = buildSchema(`
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo = A | B
  `);
  const after = buildSchema(`
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    type C {
      C: String!
    }
    union Foo = A | B | C
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "TYPE_ADDED",
      path: "C",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "FIELD_ADDED",
      path: "C.C",
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: "UNION_MEMBER_ADDED",
      path: "Foo",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedTypeKind: "ObjectTypeDefinition",
        addedTypeName: "C",
      });
  expect(changes[1].meta).toEqual({
        typeName: "C",
        addedFieldName: "C",
        typeType: "object type",
        addedFieldReturnType: "String!",
      });
  expect(changes[2].meta).toEqual({
        unionName: "Foo",
        addedUnionMemberTypeName: "C",
        addedToNewType: false,
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-048
test("union: member removed", async () => {
  const before = buildSchema(`
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    type C {
      C: String!
    }
    union Foo = A | B | C
  `);
  const after = buildSchema(`
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo = A | B
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "TYPE_REMOVED",
      path: "C",
      level: CriticalityLevel.Breaking,
      reason: false,
    },
    {
      type: "UNION_MEMBER_REMOVED",
      path: "Foo",
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        removedTypeName: "C",
      });
  expect(changes[1].meta).toEqual({
        unionName: "Foo",
        removedUnionMemberTypeName: "C",
      });
});

// Verifies: GQLI-DIFF-047, GQLI-DIFF-048
test("union: same members but different order", async () => {
  const before = buildSchema(`
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo = A | B
  `);
  const after = buildSchema(`
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo = B | A
  `);

  const changes = await diff(before, after);

  expect(changes).toEqual([]);
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage union-level directives added directive", async () => {
  const before = buildSchema(`
    directive @external on UNION
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo = A | B
  `);
  const after = buildSchema(`
    directive @external on UNION
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo @external = A | B
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_UNION_MEMBER_ADDED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedDirectiveName: "external",
        addedUnionMemberTypeName: "Foo",
        unionName: "Foo",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage union-level directives remove directive", async () => {
  const before = buildSchema(`
    directive @external on UNION
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo @external = A | B
  `);
  const after = buildSchema(`
    directive @external on UNION
    type A {
      a: String!
    }
    type B {
      b: String!
    }
    union Foo = A | B
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_UNION_MEMBER_REMOVED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        removedDirectiveName: "external",
        removedUnionMemberTypeName: "Foo",
        unionName: "Foo",
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage enum-level directives added directive", async () => {
  const before = buildSchema(`
    directive @external on ENUM
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
    }
  `);
  const after = buildSchema(`
    directive @external on ENUM
    type Query {
      fieldA: String
    }
    enum enumA @external {
      A
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_ENUM_ADDED",
      path: "enumA.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        addedDirectiveName: "external",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage enum-level directives removed directive", async () => {
  const before = buildSchema(`
    directive @external on ENUM
    type Query {
      fieldA: String
    }
    enum enumA @external {
      A
      B
    }
  `);
  const after = buildSchema(`
    directive @external on ENUM
    type Query {
      fieldA: String
    }
    enum enumA {
      A
      B
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_ENUM_REMOVED",
      path: "enumA.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        enumName: "enumA",
        removedDirectiveName: "external",
        directiveRepeatedTimes: 0,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage input-object-level directives removed directive", async () => {
  const before = buildSchema(`
    directive @external on INPUT_OBJECT
    input Foo @external {
      a: String
      b: String
    }
  `);
  const after = buildSchema(`
    directive @external on INPUT_OBJECT
    input Foo {
      a: String
      b: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_INPUT_OBJECT_REMOVED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        removedDirectiveName: "external",
        removedInputFieldName: "external",
        removedInputFieldType: "Foo",
        inputObjectName: "Foo",
        isRemovedInputFieldTypeNullable: false,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage input-object-level directives added directive", async () => {
  const before = buildSchema(`
    directive @external on INPUT_OBJECT
    input Foo {
      a: String
      b: String
    }
  `);
  const after = buildSchema(`
    directive @external on INPUT_OBJECT
    input Foo @external {
      a: String
      b: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_INPUT_OBJECT_ADDED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedDirectiveName: "external",
        addedInputFieldName: "external",
        addedInputFieldType: "Foo",
        inputObjectName: "Foo",
        isAddedInputFieldTypeNullable: false,
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage input-field-level directives added directive", async () => {
  const before = buildSchema(`
    directive @external on INPUT_FIELD_DEFINITION
    input Foo {
      a: String
      b: String
    }
  `);
  const after = buildSchema(`
    directive @external on INPUT_FIELD_DEFINITION
    input Foo {
      a: String @external
      b: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_INPUT_FIELD_DEFINITION_ADDED",
      path: "Foo.a.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        addedDirectiveName: "external",
        inputFieldName: "a",
        inputFieldType: "String",
        inputObjectName: "Foo",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage input-field-level directives removed directive", async () => {
  const before = buildSchema(`
    directive @external on INPUT_FIELD_DEFINITION
    input Foo {
      a: String @external
      b: String
    }
  `);
  const after = buildSchema(`
    directive @external on INPUT_FIELD_DEFINITION
    input Foo {
      a: String
      b: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_INPUT_FIELD_DEFINITION_REMOVED",
      path: "Foo.a.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        removedDirectiveName: "external",
        inputFieldName: "a",
        inputObjectName: "Foo",
        directiveRepeatedTimes: 0,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage scalar-level directives added directive", async () => {
  const before = buildSchema(`
    directive @external on SCALAR
    scalar Foo
  `);
  const after = buildSchema(`
    directive @external on SCALAR
    scalar Foo @external
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_SCALAR_ADDED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        scalarName: "Foo",
        addedDirectiveName: "external",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage scalar-level directives removed directive", async () => {
  const before = buildSchema(`
    directive @external on SCALAR
    scalar Foo @external
  `);
  const after = buildSchema(`
    directive @external on SCALAR
    scalar Foo
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_SCALAR_REMOVED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        scalarName: "Foo",
        removedDirectiveName: "external",
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage object-level directives added directive", async () => {
  const before = buildSchema(`
    directive @external on OBJECT
    type Foo {
      a: String
    }
  `);
  const after = buildSchema(`
    directive @external on OBJECT
    type Foo @external {
      a: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_OBJECT_ADDED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        objectName: "Foo",
        addedDirectiveName: "external",
        addedToNewType: false,
        directiveRepeatedTimes: 1,
      });
});

// Verifies: GQLI-DIFF-058, GQLI-DIFF-061, GQLI-DIFF-066
test("directive usage: directive-usage object-level directives removed directive", async () => {
  const before = buildSchema(`
    directive @external on OBJECT
    type Foo @external {
      a: String
    }
  `);
  const after = buildSchema(`
    directive @external on OBJECT
    type Foo {
      a: String
    }
  `);

  const changes = await diff(before, after);

  expect(outline(changes)).toEqual([
    {
      type: "DIRECTIVE_USAGE_OBJECT_REMOVED",
      path: "Foo.@external",
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);
  expect(changes[0].meta).toEqual({
        objectName: "Foo",
        removedDirectiveName: "external",
        directiveRepeatedTimes: 1,
      });
});
