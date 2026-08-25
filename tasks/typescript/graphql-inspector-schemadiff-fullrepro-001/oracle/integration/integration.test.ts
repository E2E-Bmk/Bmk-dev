import { expect, test } from 'vitest';
import {
  ChangeType,
  CriticalityLevel,
  coverage,
  diff,
  DiffRule,
  enumValueAddedFromMeta,
  fieldRemovedFromMeta,
  objectTypeInterfaceRemovedFromMeta,
  similar,
  validate,
} from '@graphql-inspector/core';

import { changesAt, keysOf, outline, pathsOf, sorted, typesOf } from '../helpers';
import { buildSchema, Source } from '../peer';

/* Every test below joins two projections, or a projection and the rule layer,
   over one pair of schemas, and pins what both sides produced. What is checked
   is the agreement between them -- the same coordinate grammar, the same
   exclusion set, the same notion of type kind and of deprecation, the
   shape-preserving contract the rules obey -- together with the values that
   agreement is about, so that an implementation which is internally consistent
   but wrong does not pass. */

const oldShop = buildSchema(`
  type Money {
    amount: Int!
    currency: String!
  }

  type Product {
    id: ID!
    name: String
    price(net: Boolean): Money
    legacyCode: String @deprecated(reason: "use id")
  }

  type Cart {
    id: ID!
    items: [Product!]!
  }

  type Query {
    product(id: ID!): Product
    cart(id: ID!): Cart
  }
`);

const newShop = buildSchema(`
  type Money {
    amount: Int!
    currency: String!
  }

  type Product {
    id: ID!
    name: String
    price(net: Boolean, region: String): Money
  }

  type Cart {
    id: ID!
    items: [Product!]!
  }

  type Query {
    product(id: ID!): Product
    cart(id: ID!): Cart
  }
`);

const SHOP_OUTLINE = [
  {
    type: 'FIELD_REMOVED',
    path: 'Product.legacyCode',
    level: CriticalityLevel.Breaking,
    reason: true,
  },
  {
    type: 'FIELD_ARGUMENT_ADDED',
    path: 'Product.price.region',
    level: CriticalityLevel.Dangerous,
    reason: false,
  },
];

// DependsOn: interface: fields removed
// Verifies: GQLI-CVI-001, GQLI-SER-003
test('a removed field survives the trip through its payload and back', async () => {
  const changes = await diff(oldShop, newShop);
  expect(outline(changes)).toEqual(SHOP_OUTLINE);

  const removal = changes[0];
  const rebuilt = fieldRemovedFromMeta({ type: ChangeType.FieldRemoved, meta: removal.meta });

  expect(rebuilt.type).toBe(removal.type);
  expect(rebuilt.path).toBe(removal.path);
  expect(rebuilt.criticality.level).toBe(removal.criticality.level);
  expect(rebuilt.criticality.reason !== undefined).toBe(removal.criticality.reason !== undefined);
  expect(rebuilt.meta).toEqual({
    typeName: 'Product',
    removedFieldName: 'legacyCode',
    isRemovedFieldDeprecated: true,
    typeType: 'object type',
  });
});

// DependsOn: enum: value added
// Verifies: GQLI-CVI-001, GQLI-SER-004
test('two unrelated change kinds both round trip through their own builders', async () => {
  const enumChanges = await diff(
    buildSchema(`enum Size { SMALL } type Product { size: Size } type Query { product: Product }`),
    buildSchema(`enum Size { SMALL LARGE } type Product { size: Size } type Query { product: Product }`),
  );
  expect(outline(enumChanges)).toEqual([
    {
      type: 'ENUM_VALUE_ADDED',
      path: 'Size.LARGE',
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
  ]);

  const added = enumChanges[0];
  const rebuiltEnum = enumValueAddedFromMeta({ type: ChangeType.EnumValueAdded, meta: added.meta });

  const interfaceChanges = await diff(
    buildSchema(`interface Node { id: ID! } type Product implements Node { id: ID! } type Query { product: Product }`),
    buildSchema(`interface Node { id: ID! } type Product { id: ID! } type Query { product: Product }`),
  );
  expect(outline(interfaceChanges)).toEqual([
    {
      type: 'OBJECT_TYPE_INTERFACE_REMOVED',
      path: 'Product',
      level: CriticalityLevel.Breaking,
      reason: true,
    },
  ]);

  const dropped = interfaceChanges[0];
  const rebuiltInterface = objectTypeInterfaceRemovedFromMeta({
    type: ChangeType.ObjectTypeInterfaceRemoved,
    meta: dropped.meta,
  });

  expect(rebuiltEnum.path).toBe('Size.LARGE');
  expect(rebuiltEnum.criticality.level).toBe(CriticalityLevel.Dangerous);
  expect(rebuiltEnum.meta).toEqual(added.meta);
  expect(rebuiltInterface.path).toBe('Product');
  expect(rebuiltInterface.criticality.level).toBe(CriticalityLevel.Breaking);
  expect(rebuiltInterface.meta).toEqual({
    objectTypeName: 'Product',
    removedInterfaceName: 'Node',
  });
});

// DependsOn: object type: fields order changed
// Verifies: GQLI-CVI-002
test('a field coordinate a comparison emits is addressable in a coverage report', async () => {
  const changes = await diff(oldShop, newShop);
  expect(outline(changes)).toEqual(SHOP_OUTLINE);

  const [typeName, fieldName] = changes[0].path.split('.');
  const report = coverage(oldShop, []);

  expect(sorted(keysOf(report.types))).toEqual(['Cart', 'Money', 'Product', 'Query']);
  expect(keysOf(report.types[typeName].children)).toContain(fieldName);
  expect(report.types[typeName].children[fieldName].hits).toBe(0);
  expect(report.types.Product.fieldsCount).toBe(5);
  expect(report.stats.numFields).toBe(13);
});

// DependsOn: object type: arguments added
// Verifies: GQLI-CVI-002
test('an argument coordinate a comparison emits is addressable in a coverage report', async () => {
  const changes = await diff(oldShop, newShop);
  expect(outline(changes)).toEqual(SHOP_OUTLINE);

  const [typeName, fieldName, argumentName] = changes[1].path.split('.');
  const report = coverage(newShop, []);

  expect(argumentName).toBe('region');
  expect(sorted(keysOf(report.types[typeName].children[fieldName].children))).toEqual([
    'net',
    'region',
  ]);
  expect(report.types.Product.children.price.fieldsCount).toBe(2);
  expect(report.stats.numFields).toBe(13);
});

// DependsOn: validation omits a document it has nothing to report about
// Verifies: GQLI-CVI-003
test('when validation accepts every document, coverage counts every root selection', () => {
  const sources = [
    new Source(`query One { product(id: "1") { id name } }`, 'one.graphql'),
    new Source(`query Two { cart(id: "9") { id } product(id: "2") { id } }`, 'two.graphql'),
  ];

  expect(validate(newShop, sources)).toEqual([]);

  const report = coverage(newShop, sources);

  expect(
    report.stats.numCoveredQueries +
      report.stats.numCoveredMutations +
      report.stats.numCoveredSubscriptions,
  ).toBe(3);
  expect(report.types.Query.hits).toBe(3);
  expect(report.types.Product.hits).toBe(3);
  expect(report.types.Cart.hits).toBe(1);
  expect(report.types.Money.hits).toBe(0);
  expect(report.stats.numFieldsCovered).toBe(7);
  expect(report.stats.numTypesCovered).toBe(3);
});

// DependsOn: validation reports a selection the schema does not define
// Verifies: GQLI-CVI-003
test('a selection validation rejects never becomes a coverage hit', () => {
  const rejected = new Source(`query Bad { product(id: "1") { nope } }`, 'bad.graphql');

  const findings = validate(newShop, [rejected]);
  expect(findings).toHaveLength(1);
  expect(findings[0].source.name).toBe('bad.graphql');
  expect(findings[0].errors).toHaveLength(1);

  const report = coverage(newShop, [rejected]);

  expect(keysOf(report.types.Product.children)).not.toContain('nope');
  expect(report.stats.numCoveredQueries).toBe(1);
  expect(report.stats.numFieldsCovered).toBe(2);
  expect(report.types.Product.hits).toBe(0);
});

// DependsOn: similarity pairs two types that print the same way
// Verifies: GQLI-CVI-004
test('a pair a comparison calls kind-changed is never a similarity match', async () => {
  const before = buildSchema(`
    type Shape { id: ID! label: String }
    type Marker { id: ID! label: String }
    type Query { shape: Shape marker: Marker }
  `);
  const after = buildSchema(`
    input Shape { id: ID! label: String }
    type Marker { id: ID! label: String }
    type Query { marker: Marker }
  `);

  expect(outline(await diff(before, after))).toEqual([
    { type: 'TYPE_KIND_CHANGED', path: 'Shape', level: CriticalityLevel.Breaking, reason: true },
    { type: 'FIELD_REMOVED', path: 'Query.shape', level: CriticalityLevel.Breaking, reason: true },
  ]);

  const beforeMatches = similar(before, undefined);
  expect(sorted(keysOf(beforeMatches))).toEqual(['Marker', 'Shape']);
  expect(beforeMatches.Shape.bestMatch.target.typeId).toBe('Marker');

  expect(sorted(keysOf(similar(after, undefined)))).toEqual([]);
});

// DependsOn: coverage reports every object and interface type and nothing else
// Verifies: GQLI-CVI-005
test('the built-in scalars are invisible to all three schema walks', async () => {
  const reported = keysOf(coverage(newShop, []).types);
  const candidates = keysOf(similar(newShop, undefined));
  const compared = pathsOf(await diff(oldShop, newShop));

  for (const builtin of ['String', 'Int', 'Float', 'Boolean', 'ID']) {
    expect(reported).not.toContain(builtin);
    expect(candidates).not.toContain(builtin);
    expect(compared).not.toContain(builtin);
  }
  expect(sorted(reported)).toEqual(['Cart', 'Money', 'Product', 'Query']);
  expect(compared).toEqual(['Product.legacyCode', 'Product.price.region']);
});

// DependsOn: similarity rejects a type name the schema does not offer
// Verifies: GQLI-CVI-005
test('an introspection type is absent from every projection and cannot be asked for', async () => {
  const reported = keysOf(coverage(newShop, []).types);
  const compared = pathsOf(await diff(oldShop, newShop));

  expect(reported.filter(name => name.startsWith('__'))).toEqual([]);
  expect(compared.filter(path => path !== undefined && path.startsWith('__'))).toEqual([]);
  expect(reported).toHaveLength(4);
  expect(() => similar(newShop, '__Schema')).toThrow();
});

// DependsOn: validation collects a deprecated selection apart from the errors
// Verifies: GQLI-CVI-006, GQLI-CORE-019
test('a newly deprecated field is announced by the comparison and by validation alike', async () => {
  const before = buildSchema(`type Query { legacy: String }`);
  const after = buildSchema(`type Query { legacy: String @deprecated(reason: "moved") }`);
  const selecting = [new Source(`query Uses { legacy }`, 'uses.graphql')];

  const changes = await diff(before, after);
  expect(typesOf(changes)).toContain(ChangeType.FieldDeprecationAdded);
  expect(changesAt(changes, 'Query.legacy.@deprecated')).toHaveLength(2);

  const afterFindings = validate(after, selecting, { strictDeprecated: true });
  expect(afterFindings).toHaveLength(1);
  expect(afterFindings[0].errors).toEqual([]);
  expect(afterFindings[0].deprecated).toHaveLength(1);
  expect(validate(before, selecting, { strictDeprecated: true })).toEqual([]);
});

// DependsOn: interface: deprecation added w/reason
// Verifies: GQLI-CVI-006
test('un-deprecating a field is announced by both projections in the other direction', async () => {
  const deprecated = buildSchema(`type Query { legacy: String @deprecated(reason: "moved") }`);
  const plain = buildSchema(`type Query { legacy: String }`);
  const selecting = [new Source(`query Uses { legacy }`, 'uses.graphql')];

  expect(outline(await diff(deprecated, plain))).toEqual([
    {
      type: 'FIELD_DEPRECATION_REMOVED',
      path: 'Query.legacy.@deprecated',
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
    {
      type: 'DIRECTIVE_USAGE_FIELD_DEFINITION_REMOVED',
      path: 'Query.legacy.@deprecated',
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);

  expect(validate(deprecated, selecting)[0].deprecated).toHaveLength(1);
  expect(validate(plain, selecting)).toEqual([]);
});

// DependsOn: directive definition: description
// Verifies: GQLI-CVI-007, GQLI-RULE-005
test('the description rule returns a subsequence of what the comparison produced', async () => {
  const before = buildSchema(`
    "before" type Product { id: ID! name: String }
    type Query { product: Product }
  `);
  const after = buildSchema(`
    "after" type Product { id: ID! }
    type Query { product: Product }
  `);

  expect(outline(await diff(before, after))).toEqual([
    { type: 'FIELD_REMOVED', path: 'Product.name', level: CriticalityLevel.Breaking, reason: true },
    {
      type: 'TYPE_DESCRIPTION_CHANGED',
      path: 'Product',
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);
  expect(outline(await diff(before, after, [DiffRule.ignoreDescriptionChanges]))).toEqual([
    { type: 'FIELD_REMOVED', path: 'Product.name', level: CriticalityLevel.Breaking, reason: true },
  ]);
});

// DependsOn: object type: arguments removed
// Verifies: GQLI-CVI-007, GQLI-RULE-021
test('the usage rule keeps the list length and every type and coordinate in place', async () => {
  const raw = await diff(oldShop, newShop);
  const graded = await diff(oldShop, newShop, [DiffRule.considerUsage], {
    checkUsage: async entries => entries.map(() => true),
  });

  expect(outline(raw)).toEqual(SHOP_OUTLINE);
  expect(outline(graded)).toEqual([
    {
      type: 'FIELD_REMOVED',
      path: 'Product.legacyCode',
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: 'FIELD_ARGUMENT_ADDED',
      path: 'Product.price.region',
      level: CriticalityLevel.Dangerous,
      reason: false,
    },
  ]);
});

// DependsOn: object type: interfaces removed
// Verifies: GQLI-RULE-008, GQLI-RULE-009, GQLI-RULE-010
// Mutated: GQLI-RULE-009
test('a breaking change outside the reachable graph is graded down and says so', async () => {
  const before = buildSchema(`
    type Orphan { gone: String kept: String }
    type Query { reachable: String }
  `);
  const after = buildSchema(`
    type Orphan { kept: String }
    type Query { reachable: String }
  `);

  const raw = await diff(before, after);
  expect(outline(raw)).toEqual([
    { type: 'FIELD_REMOVED', path: 'Orphan.gone', level: CriticalityLevel.Breaking, reason: true },
  ]);

  const ruled = await diff(before, after, [DiffRule.safeUnreachable]);
  expect(outline(ruled)).toEqual([
    {
      type: 'FIELD_REMOVED',
      path: 'Orphan.gone',
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);
  expect(ruled[0].message).toBe('Detached from the schema roots');
  expect(ruled[0].criticality.reason).toBe(raw[0].criticality.reason);
});

// DependsOn: interface: deprecation added w/reason
// Verifies: GQLI-RULE-011, GQLI-RULE-012
test('removing a deprecated field is graded down while removing a live one is not', async () => {
  expect(outline(await diff(oldShop, newShop, [DiffRule.suppressRemovalOfDeprecatedField]))).toEqual([
    {
      type: 'FIELD_REMOVED',
      path: 'Product.legacyCode',
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: 'FIELD_ARGUMENT_ADDED',
      path: 'Product.price.region',
      level: CriticalityLevel.Dangerous,
      reason: false,
    },
  ]);

  const liveRemoval = await diff(
    buildSchema(`type Query { live: String kept: String }`),
    buildSchema(`type Query { kept: String }`),
    [DiffRule.suppressRemovalOfDeprecatedField],
  );
  expect(outline(liveRemoval)).toEqual([
    { type: 'FIELD_REMOVED', path: 'Query.live', level: CriticalityLevel.Breaking, reason: true },
  ]);
});

// DependsOn: object type: added
// Verifies: GQLI-RULE-014, GQLI-RULE-015, GQLI-RULE-016
test('a change already implied by its parent is dropped by the simplifying rule', async () => {
  const before = buildSchema(`type Query { kept: String }`);
  const after = buildSchema(`
    type Added { one: String two: String }
    type Query { kept: String added: Added }
  `);

  expect(pathsOf(await diff(before, after))).toEqual([
    'Added',
    'Added.one',
    'Added.two',
    'Query.added',
  ]);
  expect(pathsOf(await diff(before, after, [DiffRule.simplifyChanges]))).toEqual([
    'Added',
    'Query.added',
  ]);
});

// DependsOn: directive usage: directive-usage object-level directives added directive
// Verifies: GQLI-RULE-020
test('the directive rule with nothing configured hands the list straight back', async () => {
  const before = buildSchema(`
    directive @tag(name: String!) on OBJECT
    type Product { id: ID! }
    type Query { product: Product }
  `);
  const after = buildSchema(`
    directive @tag(name: String!) on OBJECT
    type Product @tag(name: "public") { id: ID! }
    type Query { product: Product }
  `);

  const expected = [
    {
      type: 'DIRECTIVE_USAGE_OBJECT_ADDED',
      path: 'Product.@tag',
      level: CriticalityLevel.Dangerous,
      reason: true,
    },
    {
      type: 'DIRECTIVE_USAGE_ARGUMENT_ADDED',
      path: 'Product.@tag.name',
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ];

  expect(outline(await diff(before, after))).toEqual(expected);
  expect(outline(await diff(before, after, [DiffRule.ignoreDirectives]))).toEqual(expected);
  expect(
    outline(await diff(before, after, [DiffRule.ignoreDirectives], { ignoredDirectives: [] })),
  ).toEqual(expected);
});

// DependsOn: field argument: added non-nullable with default value
// Verifies: GQLI-RULE-023, GQLI-RULE-025, GQLI-RULE-026
test('marking a field safe also grades down the coordinates beneath it', async () => {
  const before = buildSchema(`
    type Detail { locale: String region: String }
    type User { email: Detail phone: String }
    type Query { user: User }
  `);
  const after = buildSchema(`
    type Detail { region: String }
    type User { email: Detail }
    type Query { user: User }
  `);

  expect(pathsOf(await diff(before, after))).toEqual(['Detail.locale', 'User.phone']);

  const seen = [];
  const ruled = await diff(before, after, [DiffRule.considerUsage], {
    checkUsage: async entries => {
      for (const entry of entries) {
        seen.push([entry.type, entry.field ?? null, entry.argument ?? null]);
      }
      return entries.map(entry => entry.type === 'User');
    },
  });

  expect(seen).toEqual([
    ['Detail', 'locale', null],
    ['User', 'phone', null],
  ]);
  expect(outline(ruled)).toEqual([
    { type: 'FIELD_REMOVED', path: 'Detail.locale', level: CriticalityLevel.Breaking, reason: true },
    { type: 'FIELD_REMOVED', path: 'User.phone', level: CriticalityLevel.Dangerous, reason: true },
  ]);
  expect(ruled[1].criticality.isSafeBasedOnUsage).toBe(true);
  expect(ruled[1].message.endsWith(' (non-breaking based on usage)')).toBe(true);
  expect(ruled[0].message.endsWith(' (non-breaking based on usage)')).toBe(false);
});

// DependsOn: field argument: default value changed
// Verifies: GQLI-RULE-022
test('the usage rule refuses to run without the configuration it reads', async () => {
  const before = buildSchema(`type Query { a: String b: String }`);
  const after = buildSchema(`type Query { a: String }`);

  await expect(diff(before, after, [DiffRule.considerUsage])).rejects.toThrow();
  await expect(diff(before, after, [DiffRule.considerUsage], undefined)).rejects.toThrow();
  expect(pathsOf(await diff(before, after))).toEqual(['Query.b']);
});

// DependsOn: enum: value added
// Verifies: GQLI-RULE-007
test('the escalating rule turns every dangerous verdict into a breaking one', async () => {
  const before = buildSchema(`
    enum Size { SMALL }
    type Query { size: Size }
  `);
  const after = buildSchema(`
    enum Size { SMALL LARGE }
    type Query { size: Size }
  `);

  expect(outline(await diff(before, after))).toEqual([
    { type: 'ENUM_VALUE_ADDED', path: 'Size.LARGE', level: CriticalityLevel.Dangerous, reason: true },
  ]);
  expect(outline(await diff(before, after, [DiffRule.dangerousBreaking]))).toEqual([
    { type: 'ENUM_VALUE_ADDED', path: 'Size.LARGE', level: CriticalityLevel.Breaking, reason: true },
  ]);
});

// DependsOn: object type: arguments type changed
// Verifies: GQLI-DIFF-001, GQLI-CORE-004, GQLI-CORE-005
test('a release review reads the coordinate and the payload of every breaking change', async () => {
  const changes = await diff(oldShop, newShop);
  expect(outline(changes)).toEqual(SHOP_OUTLINE);

  const breaking = changes.filter(
    change => change.criticality.level === CriticalityLevel.Breaking,
  );

  expect(breaking).toHaveLength(1);
  expect(breaking[0].meta).toEqual({
    typeName: 'Product',
    removedFieldName: 'legacyCode',
    isRemovedFieldDeprecated: true,
    typeType: 'object type',
  });
  expect(changes[1].meta).toEqual({
    typeName: 'Product',
    fieldName: 'price',
    addedArgumentName: 'region',
    addedArgumentType: 'String',
    hasDefaultValue: false,
    isAddedFieldArgumentBreaking: false,
    addedToNewField: false,
  });
});

// DependsOn: union: member removed
// Verifies: GQLI-RULE-024, GQLI-RULE-027
test('a usage-aware re-run of the same comparison changes only the grades', async () => {
  const plain = await diff(oldShop, newShop);
  const aware = await diff(oldShop, newShop, [DiffRule.considerUsage], {
    checkUsage: async entries => entries.map(() => true),
  });

  expect(typesOf(aware)).toEqual(['FIELD_REMOVED', 'FIELD_ARGUMENT_ADDED']);
  expect(pathsOf(aware)).toEqual(pathsOf(plain));
  expect(aware.map(change => change.criticality.level)).toEqual([
    CriticalityLevel.Dangerous,
    CriticalityLevel.Dangerous,
  ]);
  expect(aware[0].criticality.isSafeBasedOnUsage).toBe(true);
  expect(aware[1].criticality.isSafeBasedOnUsage).toBeUndefined();
  expect(aware[0].meta).toEqual(plain[0].meta);
});

// DependsOn: coverage counts root selections rather than distinct root fields
// Verifies: GQLI-COV-001, GQLI-COV-013, GQLI-COV-022
test('a coverage report over two documents adds their hits and keeps both sources', () => {
  const first = new Source(`query A { product(id: "1") { id name } }`, 'a.graphql');
  const second = new Source(
    `query B { product(id: "2") { id price(net: true) { amount } } }`,
    'b.graphql',
  );

  const report = coverage(newShop, [first, second]);

  expect(report.sources).toHaveLength(2);
  expect(report.types.Query.children.product.hits).toBe(2);
  expect(report.types.Product.children.id.hits).toBe(2);
  expect(report.types.Product.children.name.hits).toBe(1);
  expect(report.types.Product.children.price.hits).toBe(1);
  expect(report.types.Product.children.price.children.net.hits).toBe(1);
  expect(report.types.Product.children.price.children.region.hits).toBe(0);
  expect(report.types.Money.children.amount.hits).toBe(1);
  expect(report.types.Money.children.currency.hits).toBe(0);
  expect(keysOf(report.types.Query.children.product.locations)).toEqual(['a.graphql', 'b.graphql']);
  expect(report.stats.numCoveredQueries).toBe(2);
  expect(report.stats.numFieldsCovered).toBe(7);
  expect(report.stats.numTypesCoveredFully).toBe(0);
});

// DependsOn: validation reports one depth error and treats a zero limit as no limit
// Verifies: GQLI-VAL-009, GQLI-VAL-010, GQLI-VAL-012
test('several budgets applied at once report one error each, in the stated order', () => {
  const schema = buildSchema(`
    type Query { nested: Nested ok: String }
    type Nested { deeper: Nested leaf: String }
  `);
  const source = new Source(
    `query Both { a: ok b: ok c: ok nested { deeper { deeper { leaf } } } }`,
    'both.graphql',
  );

  const findings = validate(schema, [source], { maxDepth: 2, maxAliasCount: 2 });

  expect(findings).toHaveLength(1);
  expect(findings[0].source.name).toBe('both.graphql');
  expect(findings[0].errors).toHaveLength(2);
  expect(findings[0].deprecated).toEqual([]);
  expect(validate(schema, [source], { maxDepth: 2 })[0].errors).toHaveLength(1);
  expect(validate(schema, [source], { maxAliasCount: 2 })[0].errors).toHaveLength(1);
  expect(validate(schema, [source], { maxDepth: 9, maxAliasCount: 9 })).toEqual([]);
});

// DependsOn: similarity narrowed to one type reports that type only
// Verifies: GQLI-SIM-004, GQLI-CVI-004
test('a type the comparison left alone is still the similarity match of its twin', async () => {
  const schema = buildSchema(`
    type Money { amount: Int! currency: String! }
    type Price { amount: Int! currency: String! }
    type Query { money: Money price: Price }
  `);

  expect(await diff(schema, schema)).toEqual([]);

  const narrowed = similar(schema, 'Money');

  expect(sorted(keysOf(narrowed))).toEqual(['Money']);
  expect(narrowed.Money.bestMatch.target.typeId).toBe('Price');
  expect(narrowed.Money.bestMatch.target.value).toBe('amount: Int! currency: String!');
  expect(narrowed.Money.bestMatch.rating).toBeCloseTo(1, 5);
  expect(narrowed.Money.ratings).toEqual([]);
});

// DependsOn: schema: new field and field changed
// Verifies: GQLI-RULE-002, GQLI-RULE-003
// Mutated: GQLI-RULE-009
test('two rules compose, each seeing what the one before it produced', async () => {
  const before = buildSchema(`
    "old" type Orphan { gone: String kept: String }
    type Query { reachable: String }
  `);
  const after = buildSchema(`
    "new" type Orphan { kept: String }
    type Query { reachable: String }
  `);

  expect(outline(await diff(before, after))).toEqual([
    { type: 'FIELD_REMOVED', path: 'Orphan.gone', level: CriticalityLevel.Breaking, reason: true },
    {
      type: 'TYPE_DESCRIPTION_CHANGED',
      path: 'Orphan',
      level: CriticalityLevel.NonBreaking,
      reason: false,
    },
  ]);

  const both = await diff(before, after, [
    DiffRule.ignoreDescriptionChanges,
    DiffRule.safeUnreachable,
  ]);

  expect(outline(both)).toEqual([
    {
      type: 'FIELD_REMOVED',
      path: 'Orphan.gone',
      level: CriticalityLevel.NonBreaking,
      reason: true,
    },
  ]);
  expect(both[0].message).toBe('Detached from the schema roots');
});
