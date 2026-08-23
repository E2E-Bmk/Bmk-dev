/**
 * Generated Track B tests for wireit-build-graph-fullrepro-001.
 *
 * These tests exercise only the public `wireit` executable and
 * `wireit/schema.json` package data file. Assertions use process exit status,
 * command invocation counts, and schema validation booleans.
 */

import * as assert from 'node:assert';
import * as fs from 'node:fs';
import {createRequire} from 'node:module';
import {test} from 'vitest';
import * as jsonSchema from 'jsonschema';

import {rigTest} from './util/rig-test.js';

const moduleRequire = createRequire(import.meta.url);
const schema = JSON.parse(
  fs.readFileSync(moduleRequire.resolve('wireit/schema.json'), 'utf-8'),
) as jsonSchema.Schema;
const validator = new jsonSchema.Validator();
validator.addSchema(schema);

function schemaAccepts(packageJson: object): boolean {
  return validator.validate(packageJson, schema).valid;
}

function wireitScript(config: object): object {
  return {
    scripts: {build: 'wireit'},
    wireit: {build: config},
  };
}

function assertSchemaPair(validConfig: object, invalidConfig: object): void {
  assert.equal(schemaAccepts(wireitScript(validConfig)), true);
  assert.equal(schemaAccepts(wireitScript(invalidConfig)), false);
}

// Verifies: WIREIT-SCHEMA-003, WIREIT-SCHEMA-004

void test('generated schema validates command string shape', () => {
  assertSchemaPair({command: 'tsc'}, {command: ''});
});

void test('generated schema validates command value type', () => {
  assertSchemaPair({command: 'node build.js'}, {command: 42});
});

void test('generated schema validates dependency string entries', () => {
  assertSchemaPair({dependencies: ['prepare']}, {dependencies: ['']});
});

void test('generated schema validates dependency list shape', () => {
  assertSchemaPair({dependencies: ['prepare']}, {dependencies: 'prepare'});
});

void test('generated schema validates dependency object script requirement', () => {
  assertSchemaPair(
    {dependencies: [{script: 'prepare', cascade: false}]},
    {dependencies: [{cascade: false}]},
  );
});

void test('generated schema validates dependency cascade type', () => {
  assertSchemaPair(
    {dependencies: [{script: 'prepare', cascade: true}]},
    {dependencies: [{script: 'prepare', cascade: 'no'}]},
  );
});

void test('generated schema validates files list shape', () => {
  assertSchemaPair({files: ['src/**/*.ts']}, {files: 'src/**/*.ts'});
});

void test('generated schema validates files glob entries', () => {
  assertSchemaPair({files: ['src/**/*.ts']}, {files: ['src/**/*.ts', '']});
});

void test('generated schema validates output list shape', () => {
  assertSchemaPair({output: ['lib/**']}, {output: 'lib/**'});
});

void test('generated schema validates output glob entries', () => {
  assertSchemaPair({output: ['lib/**']}, {output: ['lib/**', '']});
});

void test('generated schema validates clean policy strings', () => {
  assertSchemaPair({clean: 'if-file-deleted'}, {clean: 'always'});
});

void test('generated schema validates environment assignment values', () => {
  assertSchemaPair({env: {NODE_ENV: 'production'}}, {env: {NODE_ENV: 1}});
});

void test('generated schema validates external environment flags', () => {
  assertSchemaPair(
    {env: {TOKEN: {external: true}}},
    {env: {TOKEN: {external: false}}},
  );
});

void test('generated schema validates package lock list shape', () => {
  assertSchemaPair(
    {packageLocks: ['package-lock.json']},
    {packageLocks: 'package-lock.json'},
  );
});

void test('generated schema validates package lock entries', () => {
  assertSchemaPair(
    {packageLocks: ['package-lock.json']},
    {packageLocks: ['package-lock.json', '']},
  );
});

void test('generated schema validates allowUsuallyExcludedPaths type', () => {
  assertSchemaPair(
    {allowUsuallyExcludedPaths: true},
    {allowUsuallyExcludedPaths: 'true'},
  );
});

void test('generated schema validates unrelated root properties with command rules', () => {
  assert.equal(schemaAccepts({...wireitScript({command: 'tsc'}), private: true}), true);
  assert.equal(schemaAccepts({...wireitScript({command: ''}), private: true}), false);
});

void test('generated schema validates cross package dependency strings', () => {
  assertSchemaPair({dependencies: ['./packages/a:build']}, {dependencies: [false]});
});

void test('generated schema validates omitted dependency cascade defaults', () => {
  assertSchemaPair({dependencies: [{script: 'prepare'}]}, {dependencies: [{script: ''}]});
});

void test('generated schema validates empty files arrays and invalid members', () => {
  assertSchemaPair({files: []}, {files: [7]});
});

void test('generated schema validates empty output arrays and invalid members', () => {
  assertSchemaPair({output: []}, {output: [false]});
});

void test('generated schema validates boolean clean policies', () => {
  assertSchemaPair({clean: false}, {clean: null});
});

void test('generated schema validates external environment defaults', () => {
  assertSchemaPair(
    {env: {TOKEN: {external: true, default: 'fallback'}}},
    {env: {TOKEN: {external: true, default: 1}}},
  );
});

void test('generated schema validates package lock glob members', () => {
  assertSchemaPair({packageLocks: ['locks/*.json']}, {packageLocks: [false]});
});

void test('generated schema exposes draft seven metadata', () => {
  assert.equal(schema.$schema, 'http://json-schema.org/draft-07/schema#');
  assert.notEqual(schemaAccepts(wireitScript({command: ''})), true);
});

void test('generated schema validates multiple scoped fields together', () => {
  assertSchemaPair(
    {command: 'tsc', files: ['src/**'], output: ['lib/**'], clean: true},
    {command: 'tsc', files: [''], output: ['lib/**'], clean: true},
  );
});

void test('generated schema validates environment map object shape', () => {
  assertSchemaPair({env: {A: '1', B: {external: true}}}, {env: ['A=1']});
});

void test('generated schema validates dependency list object shape', () => {
  assertSchemaPair({dependencies: [{script: 'build'}]}, {dependencies: [5]});
});

void test(
  'generated invalid WIREIT_FAILURES fails before command execution',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {build: {command: command.command}},
      },
    });

    const exec = rig.exec('npm run build', {env: {WIREIT_FAILURES: 'later'}});
    const result = await exec.exit;

    assert.notEqual(result.code, 0);
    assert.equal(command.numInvocations, 0);
  }),
);

void test('generated schema projects env and list field constraints', () => {
  assert.equal(
    schemaAccepts({
      unrelatedRootProperty: true,
      wireit: {
        build: {
          command: 'tsc',
          files: ['src/**/*.ts'],
          output: ['lib/**'],
          env: {
            INLINE_VALUE: 'abc',
            EXTERNAL_VALUE: {external: true, default: 'fallback'},
          },
          packageLocks: ['package-lock.json'],
          allowUsuallyExcludedPaths: true,
        },
      },
    }),
    true,
  );

  for (const invalidPackageJson of [
    {wireit: {build: {command: ''}}},
    {wireit: {build: {files: 'src/**/*.ts'}}},
    {wireit: {build: {output: ['']}}},
    {wireit: {build: {dependencies: [{cascade: false}]}}},
    {wireit: {build: {env: {EXTERNAL_VALUE: {external: 'yes'}}}}},
    {wireit: {build: {packageLocks: ['']}}},
  ]) {
    assert.equal(schemaAccepts(invalidPackageJson), false);
  }
});

void test(
  'generated invalid WIREIT_PARALLEL fails before command execution',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {build: {command: command.command}},
      },
    });

    const exec = rig.exec('npm run build', {env: {WIREIT_PARALLEL: 'zero'}});
    const result = await exec.exit;

    assert.notEqual(result.code, 0);
    assert.equal(command.numInvocations, 0);
  }),
);

void test(
  'generated invalid WIREIT_CACHE fails before command execution',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {build: {command: command.command}},
      },
    });

    const exec = rig.exec('npm run build', {env: {WIREIT_CACHE: 'remote'}});
    const result = await exec.exit;

    assert.notEqual(result.code, 0);
    assert.equal(command.numInvocations, 0);
  }),
);
