import { expect, test } from 'vitest';
import {
  calculateOperationComplexity,
  calculateTokenCount,
  ChangeType,
  countAliases,
  countDepth,
  countDirectives,
  CriticalityLevel,
  coverage,
  diff,
  fieldRemovedFromMeta,
  similar,
  validate,
} from '@graphql-inspector/core';

import { keysOf, sorted } from '../helpers';
import { buildSchema, parse, Source } from '../peer';

/* One projection call per test. Coverage, similarity, validation and the
   query-analysis helpers are exercised on their own here; the tests that make
   two projections agree with each other live in the integration suite. */

const blogSchema = buildSchema(`
  type Post {
    id: ID!
    title: String
    author: Author
  }

  type Author {
    id: ID!
    name: String
  }

  type Query {
    post(id: ID!): Post
    posts(first: Int, after: String): [Post!]!
  }
`);

const onePost = new Source(
  `query OnePost {
    post(id: "1") {
      id
      title
      author {
        name
      }
    }
  }`,
  'one-post.graphql',
);

// Verifies: GQLI-COV-004, GQLI-COV-005, GQLI-COV-006
test('coverage reports every object and interface type and nothing else', () => {
  const report = coverage(blogSchema, [onePost]);

  expect(sorted(keysOf(report.types))).toEqual(['Author', 'Post', 'Query']);
  expect(report.sources).toHaveLength(1);
});

// Verifies: GQLI-COV-013, GQLI-COV-014, GQLI-COV-019
test('coverage statistics count fields and arguments together', () => {
  const report = coverage(blogSchema, [onePost]);

  expect(report.stats).toEqual({
    numTypes: 3,
    numTypesCovered: 3,
    numTypesCoveredFully: 1,
    numFields: 10,
    numFieldsCovered: 6,
    numFiledsCovered: 6,
    numQueries: 2,
    numMutations: 0,
    numSubscriptions: 0,
    numCoveredQueries: 1,
    numCoveredMutations: 0,
    numCoveredSubscriptions: 0,
  });
});

// Verifies: GQLI-COV-007, GQLI-COV-008, GQLI-COV-009
test('coverage counts a selected field and the argument it was given', () => {
  const report = coverage(blogSchema, [onePost]);
  const query = report.types.Query;

  expect(query.hits).toBe(1);
  expect(query.fieldsCount).toBe(5);
  expect(query.fieldsCountCovered).toBe(2);
  expect(query.children.post.hits).toBe(1);
  expect(query.children.post.children.id.hits).toBe(1);
  expect(keysOf(query.children.post.locations)).toEqual(['one-post.graphql']);
  expect(query.children.post.locations['one-post.graphql']).toHaveLength(1);
});

// Verifies: GQLI-COV-012, GQLI-COV-003
test('coverage leaves an unselected field at zero hits with no locations', () => {
  const report = coverage(blogSchema, [onePost]);
  const posts = report.types.Query.children.posts;

  expect(posts.hits).toBe(0);
  expect(posts.fieldsCount).toBe(2);
  expect(posts.fieldsCountCovered).toBe(0);
  expect(posts.locations).toEqual({});
  expect(report.types.Author.children.id.hits).toBe(0);
  expect(report.types.Author.children.name.hits).toBe(1);
});

// Verifies: GQLI-COV-022, GQLI-COV-011
test('coverage counts root selections rather than distinct root fields', () => {
  const twice = new Source(
    `query Twice {
      post(id: "1") { ...F }
      post(id: "2") { id }
    }
    fragment F on Post { title }`,
    'twice.graphql',
  );

  const report = coverage(blogSchema, [twice]);

  expect(report.stats.numCoveredQueries).toBe(2);
  expect(report.types.Query.children.post.hits).toBe(2);
  expect(report.types.Post.children.title.hits).toBe(1);
  expect(report.types.Post.children.author.hits).toBe(0);
});

// Verifies: GQLI-COV-010
test('coverage records the newest location of a repeated selection first', () => {
  const twice = new Source(
    `query Twice {
      post(id: "1") { id }
      post(id: "2") { id }
    }`,
    'repeat.graphql',
  );

  const report = coverage(blogSchema, [twice]);
  const spots = report.types.Query.children.post.locations['repeat.graphql'];

  expect(spots).toHaveLength(2);
  expect(spots[0].start).toBeGreaterThan(spots[1].start);
  expect(spots[0].end).toBeGreaterThan(spots[0].start);
});

// Verifies: GQLI-COV-007
test('coverage ignores a typename selection', () => {
  const withMeta = new Source(
    `query Meta { __typename post(id: "1") { __typename id } }`,
    'meta.graphql',
  );

  const report = coverage(blogSchema, [withMeta]);

  expect(report.stats.numCoveredQueries).toBe(1);
  expect(report.stats.numFieldsCovered).toBe(3);
  expect(report.types.Query.children.post.hits).toBe(1);
  expect(report.types.Query.children.posts.hits).toBe(0);
});

// Verifies: GQLI-COV-006, GQLI-COV-015
test('coverage of no documents still reports every type at zero', () => {
  const report = coverage(blogSchema, []);

  expect(sorted(keysOf(report.types))).toEqual(['Author', 'Post', 'Query']);
  expect(report.types.Query.hits).toBe(0);
  expect(report.stats.numTypesCovered).toBe(0);
  expect(report.stats.numFields).toBe(10);
  expect(report.stats.numFieldsCovered).toBe(0);
});

const twinsSchema = buildSchema(`
  type Query {
    a: A
  }

  type A {
    id: ID!
    name: String
  }

  type B {
    id: ID!
    name: String
  }

  type C {
    completelyDifferent: Int
  }

  input AInput {
    id: ID!
    name: String
  }
`);

// Verifies: GQLI-SIM-005, GQLI-SIM-006, GQLI-SIM-010
test('similarity pairs two types that print the same way', () => {
  const report = similar(twinsSchema, undefined);

  expect(sorted(keysOf(report))).toEqual(['A', 'B']);
  expect(report.A.bestMatch.target.typeId).toBe('B');
  expect(report.A.bestMatch.rating).toBeCloseTo(1, 5);
  expect(report.A.ratings).toEqual([]);
  expect(report.B.bestMatch.target.typeId).toBe('A');
});

// Verifies: GQLI-SIM-003
test('similarity uses the stripped definition as the compared value', () => {
  const report = similar(twinsSchema, undefined);

  expect(report.A.bestMatch.target.value).toBe('id: ID! name: String');
});

// Verifies: GQLI-SIM-004
test('similarity narrowed to one type reports that type only', () => {
  const report = similar(twinsSchema, 'A');

  expect(sorted(keysOf(report))).toEqual(['A']);
  expect(report.A.bestMatch.target.typeId).toBe('B');
});

// Verifies: GQLI-SIM-007, GQLI-SIM-008
test('similarity above a raised threshold reports nothing coincidental', () => {
  const drifted = buildSchema(`
    type Query {
      a: A
    }

    type A {
      id: ID!
      name: String
    }

    type D {
      completelyUnrelatedField: Int
    }
  `);

  expect(sorted(keysOf(similar(drifted, undefined, 0.99)))).toEqual([]);
  expect(sorted(keysOf(similar(drifted, undefined, 0.01)))).toEqual(['A', 'D']);
});

// Verifies: GQLI-SIM-004, GQLI-ERR-004
test('similarity rejects a type name the schema does not offer', () => {
  expect(similar(twinsSchema, 'A').A.bestMatch.target.typeId).toBe('B');
  expect(() => similar(twinsSchema, 'Nope')).toThrow();
  expect(() => similar(twinsSchema, '__Type')).toThrow();
});

const opsSchema = buildSchema(`
  type Query {
    ok: String
    legacy: String @deprecated(reason: "gone")
    nested: Nested
  }

  type Nested {
    deeper: Nested
    leaf: String
  }
`);

// Verifies: GQLI-VAL-014
test('validation omits a document it has nothing to report about', () => {
  expect(validate(opsSchema, [new Source(`query Good { ok }`, 'good.graphql')])).toEqual([]);
});

// Verifies: GQLI-VAL-008
test('validation reports a selection the schema does not define', () => {
  const found = validate(opsSchema, [new Source(`query Bad { nope }`, 'bad.graphql')]);

  expect(found).toHaveLength(1);
  expect(found[0].source.name).toBe('bad.graphql');
  expect(found[0].errors).toHaveLength(1);
  expect(found[0].deprecated).toEqual([]);
});

// Verifies: GQLI-VAL-013, GQLI-CORE-019
test('validation collects a deprecated selection apart from the errors', () => {
  const source = new Source(`query Dep { legacy }`, 'dep.graphql');
  const strict = validate(opsSchema, [source]);

  expect(strict).toHaveLength(1);
  expect(strict[0].errors).toEqual([]);
  expect(strict[0].deprecated).toHaveLength(1);
  expect(validate(opsSchema, [source], { strictDeprecated: false })).toEqual([]);
});

// Verifies: GQLI-VAL-009, GQLI-VAL-012
test('validation reports one depth error and treats a zero limit as no limit', () => {
  const deep = new Source(
    `query Deep { nested { deeper { deeper { leaf } } } }`,
    'deep.graphql',
  );

  const limited = validate(opsSchema, [deep], { maxDepth: 2 });
  expect(limited).toHaveLength(1);
  expect(limited[0].errors).toHaveLength(1);
  expect(validate(opsSchema, [deep], { maxDepth: 0 })).toEqual([]);
  expect(validate(opsSchema, [deep], { maxDepth: 9 })).toEqual([]);
});

// Verifies: GQLI-VAL-010
test('validation reports one alias error when the alias budget is exceeded', () => {
  const aliased = new Source(`query Alias { a: ok b: ok c: ok }`, 'alias.graphql');

  const limited = validate(opsSchema, [aliased], { maxAliasCount: 2 });
  expect(limited).toHaveLength(1);
  expect(limited[0].errors).toHaveLength(1);
  expect(validate(opsSchema, [aliased], { maxAliasCount: 9 })).toEqual([]);
});

// Verifies: GQLI-VAL-011
test('validation reports one directive error when the directive budget is exceeded', () => {
  const source = new Source(
    `query D { ok @include(if: true) @skip(if: false) nested @include(if: true) { leaf } }`,
    'dir.graphql',
  );

  const limited = validate(opsSchema, [source], { maxDirectiveCount: 1 });
  expect(limited).toHaveLength(1);
  expect(limited[0].errors).toHaveLength(1);
  expect(validate(opsSchema, [source], { maxDirectiveCount: 9 })).toEqual([]);
  expect(validate(opsSchema, [source], { maxDirectiveCount: 0 })).toEqual([]);
});

// Verifies: GQLI-VAL-011
test('validation applies the complexity budget when it is configured', () => {
  const source = new Source(`query Cx { nested { deeper { leaf } } }`, 'cx.graphql');
  const config = {
    maxComplexityScore: 1,
    complexityScalarCost: 1,
    complexityObjectCost: 2,
    complexityDepthCostFactor: 2,
  };

  const limited = validate(opsSchema, [source], { validateComplexityConfig: config });
  expect(limited).toHaveLength(1);
  expect(limited[0].errors).toHaveLength(1);
  expect(validate(opsSchema, [source])).toEqual([]);
});

// Verifies: GQLI-VAL-004, GQLI-VAL-006, GQLI-VAL-007
test('validation never reports a fragment-only document yet still resolves its fragments', () => {
  const fragment = new Source(`fragment Solo on Nested { leaf }`, 'frag.graphql');
  const operation = new Source(`query UsesFrag { nested { ...Solo } }`, 'uses.graphql');

  expect(validate(opsSchema, [fragment])).toEqual([]);
  expect(validate(opsSchema, [operation, fragment])).toEqual([]);
  expect(validate(opsSchema, [fragment, operation])).toEqual([]);
});

// Verifies: GQLI-VAL-012
test('validation reports one error per repeated fragment name unless asked not to', () => {
  const first = new Source(`fragment Dup on Nested { leaf }`, 'dup-a.graphql');
  const second = new Source(`fragment Dup on Nested { leaf }`, 'dup-b.graphql');
  const operation = new Source(`query UsesDup { nested { ...Dup } }`, 'uses-dup.graphql');
  const sources = [operation, first, second];

  const strict = validate(opsSchema, sources);
  expect(strict).toHaveLength(1);
  expect(strict[0].source.name).toBe('uses-dup.graphql');
  expect(strict[0].errors).toHaveLength(1);
  expect(validate(opsSchema, sources, { strictFragments: false })).toEqual([]);
});

const analysed = parse(`
  query Q { a: ok @include(if: true) nested { ...F } }
  fragment F on Nested { deeper { leaf } }
`);
const operationNode = analysed.definitions.find(node => node.kind === 'OperationDefinition');
const fragmentNodes = analysed.definitions.filter(node => node.kind === 'FragmentDefinition');
const fragmentByName = (name) => fragmentNodes.find(node => node.name.value === name);

// Verifies: GQLI-QRY-002, GQLI-QRY-003
test('the alias count follows a fragment spread', () => {
  expect(countAliases(operationNode, fragmentByName)).toBe(1);
  expect(countAliases(operationNode, () => undefined)).toBe(1);
});

// Verifies: GQLI-QRY-004, GQLI-QRY-005
test('the directive count is the directives of the node and of everything it includes', () => {
  expect(countDirectives(operationNode, fragmentByName)).toBe(1);
});

// Verifies: GQLI-QRY-006, GQLI-QRY-007
test('the depth of an operation includes the depth of the fragments it spreads', () => {
  expect(countDepth(operationNode, 0, fragmentByName)).toBe(5);
  expect(countDepth(operationNode, 0, () => undefined)).toBeLessThan(5);
});

// Verifies: GQLI-QRY-009, GQLI-QRY-010
test('the complexity of an operation is the configured cost of its shape', () => {
  const config = { scalarCost: 1, objectCost: 2, depthCostFactor: 2 };

  expect(calculateOperationComplexity(operationNode, config, fragmentByName)).toBe(92);
});

// Verifies: GQLI-QRY-012, GQLI-QRY-013
test('the token count adds the tokens of every referenced fragment', () => {
  const plain = calculateTokenCount({
    source: 'query Q { nested { leaf } }',
    getReferencedFragmentSource: () => undefined,
  });
  const spreading = calculateTokenCount({
    source: 'query Q { nested { ...F } }',
    getReferencedFragmentSource: name =>
      name === 'F' ? 'fragment F on Nested { leaf }' : undefined,
  });

  expect(plain).toBe(8);
  expect(spreading).toBe(16);
});

// Verifies: GQLI-SER-003, GQLI-SER-004
test('a change record can be rebuilt from its payload alone', async () => {
  const before = buildSchema(`type Query { removed: String kept: String }`);
  const after = buildSchema(`type Query { kept: String }`);
  const removal = (await diff(before, after)).find(
    change => change.type === ChangeType.FieldRemoved,
  );

  const rebuilt = fieldRemovedFromMeta({ type: ChangeType.FieldRemoved, meta: removal.meta });

  expect(rebuilt.type).toBe('FIELD_REMOVED');
  expect(rebuilt.path).toBe('Query.removed');
  expect(rebuilt.criticality.level).toBe(CriticalityLevel.Breaking);
  expect(rebuilt.criticality.reason).toBeDefined();
  expect(rebuilt.meta).toEqual({
    typeName: 'Query',
    removedFieldName: 'removed',
    isRemovedFieldDeprecated: false,
    typeType: 'object type',
  });
});
