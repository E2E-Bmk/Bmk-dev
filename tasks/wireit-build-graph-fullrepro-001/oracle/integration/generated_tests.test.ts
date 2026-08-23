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

void test(
  'generated dependent build executes dependency before root command',
  rigTest(async ({rig}) => {
    const build = await rig.newCommand();
    const bundle = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit', bundle: 'wireit'},
        wireit: {
          build: {command: build.command},
          bundle: {command: bundle.command, dependencies: ['build']},
        },
      },
    });

    const exec = rig.exec('npm run bundle');
    const buildInvocation = await build.nextInvocation();
    assert.equal(bundle.numInvocations, 0);
    buildInvocation.exit(0);
    const bundleInvocation = await bundle.nextInvocation();
    bundleInvocation.exit(0);
    const result = await exec.exit;

    assert.equal(result.code, 0);
    assert.equal(build.numInvocations, 1);
    assert.equal(bundle.numInvocations, 1);
  }),
);

void test(
  'generated pass-through root succeeds when dependency has a command',
  rigTest(async ({rig}) => {
    const prepare = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit', prepare: 'wireit'},
        wireit: {
          build: {dependencies: ['prepare']},
          prepare: {command: prepare.command},
        },
      },
    });

    const exec = rig.exec('npm run build');
    const invocation = await prepare.nextInvocation();
    invocation.exit(0);
    const result = await exec.exit;

    assert.equal(result.code, 0);
    assert.equal(prepare.numInvocations, 1);
  }),
);

void test(
  'generated npm extra arguments reach the configured command argv',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {build: {command: command.command}},
      },
    });

    const exec = rig.exec('npm run build -- --mode production');
    const invocation = await command.nextInvocation();
    const environment = await invocation.environment();
    invocation.exit(0);
    const result = await exec.exit;

    assert.equal(result.code, 0);
    assert.deepEqual(environment.argv.slice(-2), ['--mode', 'production']);
  }),
);

void test(
  'generated empty output script becomes fresh after a successful run',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {
          build: {
            command: command.command,
            files: ['input.txt'],
            output: [],
          },
        },
      },
      'input.txt': 'stable',
    });

    const first = rig.exec('npm run build');
    (await command.nextInvocation()).exit(0);
    assert.equal((await first.exit).code, 0);

    const second = rig.exec('npm run build');
    assert.equal((await second.exit).code, 0);
    assert.equal(command.numInvocations, 1);
  }),
);

void test(
  'generated extra arguments are part of freshness state',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {
          build: {
            command: command.command,
            files: ['input.txt'],
            output: [],
          },
        },
      },
      'input.txt': 'stable',
    });

    const first = rig.exec('npm run build -- --alpha');
    (await command.nextInvocation()).exit(0);
    assert.equal((await first.exit).code, 0);

    const second = rig.exec('npm run build -- --beta');
    (await command.nextInvocation()).exit(0);
    assert.equal((await second.exit).code, 0);
    assert.equal(command.numInvocations, 2);
  }),
);

void test(
  'generated duplicate dependencies fail before command execution',
  rigTest(async ({rig}) => {
    const build = await rig.newCommand();
    const prepare = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit', prepare: 'wireit'},
        wireit: {
          build: {command: build.command, dependencies: ['prepare', 'prepare']},
          prepare: {command: prepare.command},
        },
      },
    });

    const exec = rig.exec('npm run build');
    const result = await exec.exit;

    assert.notEqual(result.code, 0);
    assert.equal(build.numInvocations, 0);
    assert.equal(prepare.numInvocations, 0);
  }),
);

void test(
  'generated external environment value is part of freshness state',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {
          build: {
            command: command.command,
            files: ['input.txt'],
            output: [],
            env: {TOKEN: {external: true}},
          },
        },
      },
      'input.txt': 'stable',
    });

    const first = rig.exec('npm run build', {env: {TOKEN: 'a'}});
    (await command.nextInvocation()).exit(0);
    assert.equal((await first.exit).code, 0);

    const second = rig.exec('npm run build', {env: {TOKEN: 'b'}});
    (await command.nextInvocation()).exit(0);
    assert.equal((await second.exit).code, 0);
    assert.equal(command.numInvocations, 2);
  }),
);

void test(
  'generated missing cross-package dependency fails before root command',
  rigTest(async ({rig}) => {
    const command = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {
          build: {
            command: command.command,
            dependencies: ['./missing:prepare'],
          },
        },
      },
    });

    const exec = rig.exec('npm run build');
    const result = await exec.exit;

    assert.notEqual(result.code, 0);
    assert.equal(command.numInvocations, 0);
  }),
);

void test(
  'generated root pass-through script with no executable dependency fails',
  rigTest(async ({rig}) => {
    await rig.write({
      'package.json': {
        scripts: {build: 'wireit'},
        wireit: {build: {files: ['input.txt'], output: []}},
      },
      'input.txt': 'input',
    });

    const exec = rig.exec('npm run build');
    const result = await exec.exit;

    assert.notEqual(result.code, 0);
  }),
);
