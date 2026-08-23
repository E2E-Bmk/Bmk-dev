/**
 * @license
 * Copyright 2022 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {test} from 'vitest';
import * as assert from 'node:assert';
import {IS_WINDOWS} from './util/windows.js';
import {checkScriptOutput} from './util/check-script-output.js';
import {NODE_MAJOR_VERSION} from './util/node-version.js';
import {WireitTestRig} from './util/test-rig.js';

void test('finds node_modules binary in starting dir', async () => {
  await using rig = await WireitTestRig.setup();

  const cmd = await rig.newCommand();
  await rig.write({
    'package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          command: 'test-binary',
        },
      },
    },
  });
  await rig.generateAndInstallNodeBinary({
    command: cmd.command,
    binaryPath: 'node_modules/test-pkg/test-binary',
    installPath: 'node_modules/.bin/test-binary',
  });
  const exec = rig.exec('npm run a');
  (await cmd.nextInvocation()).exit(0);
  const res = await exec.exit;
  assert.equal(res.code, 0);
  assert.equal(cmd.numInvocations, 1);
});

void test('finds node_modules binary in parent dir', async () => {
  await using rig = await WireitTestRig.setup();

  const cmd = await rig.newCommand();
  await rig.write({
    'foo/package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          command: 'test-binary',
        },
      },
    },
  });
  await rig.generateAndInstallNodeBinary({
    command: cmd.command,
    binaryPath: 'node_modules/test-pkg/test-binary',
    installPath: 'node_modules/.bin/test-binary',
  });
  const exec = rig.exec('npm run a', {cwd: 'foo'});
  (await cmd.nextInvocation()).exit(0);
  const res = await exec.exit;
  assert.equal(res.code, 0);
  assert.equal(cmd.numInvocations, 1);
});

void test('finds node_modules binary across packages (child)', async () => {
  await using rig = await WireitTestRig.setup();

  const cmd = await rig.newCommand();
  await rig.write({
    'package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          dependencies: ['./bar:b'],
        },
      },
    },
    'bar/package.json': {
      scripts: {
        b: 'wireit',
      },
      wireit: {
        b: {
          command: 'test-binary',
        },
      },
    },
  });
  await rig.generateAndInstallNodeBinary({
    command: cmd.command,
    binaryPath: 'bar/node_modules/test-pkg/test-binary',
    installPath: 'bar/node_modules/.bin/test-binary',
  });
  const exec = rig.exec('npm run a');
  (await cmd.nextInvocation()).exit(0);
  const res = await exec.exit;
  assert.equal(res.code, 0);
  assert.equal(cmd.numInvocations, 1);
});

void test('finds node_modules binary across packages (sibling)', async () => {
  await using rig = await WireitTestRig.setup();

  const cmd = await rig.newCommand();
  await rig.write({
    'foo/package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          dependencies: ['../bar:b'],
        },
      },
    },
    'bar/package.json': {
      scripts: {
        b: 'wireit',
      },
      wireit: {
        b: {
          command: 'test-binary',
        },
      },
    },
  });
  await rig.generateAndInstallNodeBinary({
    command: cmd.command,
    binaryPath: 'bar/node_modules/test-pkg/test-binary',
    installPath: 'bar/node_modules/.bin/test-binary',
  });
  const exec = rig.exec('npm run a', {cwd: 'foo'});
  (await cmd.nextInvocation()).exit(0);
  const res = await exec.exit;
  assert.equal(res.code, 0);
  assert.equal(cmd.numInvocations, 1);
});

void test('starting node_modules binaries are not available across packages (sibling)', async () => {
  await using rig = await WireitTestRig.setup();

  const cmd = await rig.newCommand();
  await rig.write({
    'foo/package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          dependencies: ['../bar:b'],
        },
      },
    },
    'bar/package.json': {
      scripts: {
        b: 'wireit',
      },
      wireit: {
        b: {
          command: 'test-binary',
        },
      },
    },
  });
  await rig.generateAndInstallNodeBinary({
    command: cmd.command,
    binaryPath: 'foo/node_modules/test-pkg/test-binary',
    installPath: 'foo/node_modules/.bin/test-binary',
  });
  const exec = rig.exec('npm run b', {cwd: 'bar'});
  const res = await exec.exit;
  assert.equal(res.code, 1);
  assert.equal(cmd.numInvocations, 0);
  assert.match(
    res.stderr,
    IS_WINDOWS
      ? /'test-binary' is not recognized/
      : /exited with exit code 127/,
  );
});

void test('finds package directory without npm_package_json', async () => {
  await using rig = await WireitTestRig.setup();

  // This confirms that we can walk up the filesystem to find the nearest
  // package.json when the npm_package_json environment variable isn't set.
  // This variable isn't set by yarn, pnpm, and older versions of npm.
  const cmdA = await rig.newCommand();
  await rig.write({
    'package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          command: cmdA.command,
        },
      },
    },
  });
  await rig.mkdir('foo/bar/baz');
  const exec = rig.exec(
    IS_WINDOWS
      ? '..\\..\\..\\node_modules\\.bin\\wireit.cmd'
      : '../../../node_modules/.bin/wireit',
    {
      cwd: 'foo/bar/baz',
      env: {
        npm_lifecycle_event: 'a',
      },
    },
  );
  (await cmdA.nextInvocation()).exit(0);
  const res = await exec.exit;
  assert.equal(res.code, 0);
  assert.equal(cmdA.numInvocations, 1);
});

void test('multiple cross-package dependencies', async () => {
  await using rig = await WireitTestRig.setup();

  const cmdA = await rig.newCommand();
  const cmdB = await rig.newCommand();
  const cmdC = await rig.newCommand();
  await rig.write({
    'foo/package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          command: cmdA.command,
          dependencies: ['../bar:b', '../baz:c'],
        },
      },
    },
    'bar/package.json': {
      scripts: {
        b: 'wireit',
      },
      wireit: {
        b: {
          command: cmdB.command,
        },
      },
    },
    'baz/package.json': {
      scripts: {
        c: 'wireit',
      },
      wireit: {
        c: {
          command: cmdC.command,
        },
      },
    },
  });

  const exec = rig.exec('npm run a', {cwd: 'foo'});
  await exec.waitForLog(
    /0% \[0 \/ 3\] \[2 running\] (\.\.\/bar:b|\.\.\/baz:c)/,
  );

  const invC = await cmdC.nextInvocation();
  invC.exit(0);
  await exec.waitForLog(/33% \[1 \/ 3\] \[1 running\] \.\.\/bar:b/);

  const invB = await cmdB.nextInvocation();
  invB.exit(0);
  await exec.waitForLog(/67% \[2 \/ 3\] \[1 running\] a/);

  const invA = await cmdA.nextInvocation();
  invA.exit(0);

  const res = await exec.exit;
  assert.equal(res.code, 0);
  assert.equal(cmdA.numInvocations, 1);
  assert.equal(cmdB.numInvocations, 1);
  assert.equal(cmdC.numInvocations, 1);
  assert.match(res.stdout, /Ran 3 scripts and skipped 0/s);
});

void test('top-level SIGINT kills running scripts', async () => {
  await using rig = await WireitTestRig.setup();

  const main = await rig.newCommand();
  await rig.write({
    'package.json': {
      scripts: {
        main: 'wireit',
      },
      wireit: {
        main: {
          command: main.command,
        },
      },
    },
  });

  const wireit = rig.exec('npm run main');
  const inv = await main.nextInvocation();
  wireit.kill('SIGINT');
  await inv.closed;
  await wireit.exit;
  assert.equal(main.numInvocations, 1);
  // on windows we just die without reporting anything when we get a SIGINT
  if (!IS_WINDOWS) {
    await wireit.waitForLog(/❌ \[main\] killed/);
    await wireit.waitForLog(/❌ 1 script failed/);
  }
});

void test('top-level SIGTERM kills running scripts', async () => {
  await using rig = await WireitTestRig.setup();

  const main = await rig.newCommand();
  await rig.write({
    'package.json': {
      scripts: {
        main: 'wireit',
      },
      wireit: {
        main: {
          command: main.command,
        },
      },
    },
  });

  const wireit = rig.exec('npm run main');
  const inv = await main.nextInvocation();
  wireit.kill('SIGTERM');
  await inv.closed;
  await wireit.exit;
  assert.equal(main.numInvocations, 1);
  // on windows we just die without reporting anything when we get a SIGINT
  if (!IS_WINDOWS) {
    await wireit.waitForLog(/❌ \[main\] killed/);
    await wireit.waitForLog(/❌ 1 script failed/);
  }
});

const command = 'npm run';
const extraDashes = '';
void test('can pass extra args with using "npm run run --"', async () => {
    await using rig = await WireitTestRig.setup();

    const cmdA = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA.command,
            // Explicit empty input and output files so that we can be fresh.
            files: [],
            output: [],
          },
        },
      },
    });

    // Initially stale.
    {
      const wireit = rig.exec(`${command} a -- ${extraDashes} foo -bar --baz`);
      const inv = await cmdA.nextInvocation();
      assert.deepEqual((await inv.environment()).argv.slice(3), [
        'foo',
        '-bar',
        '--baz',
      ]);
      inv.exit(0);
      assert.equal((await wireit.exit).code, 0);
      await wireit.waitForLog(/Ran 1 script and skipped 0/s); //
    }

    // Nothing changed, fresh.
    {
      const wireit = rig.exec(`${command} a -- ${extraDashes} foo -bar --baz`);
      assert.equal((await wireit.exit).code, 0);
      await wireit.waitForLog(/Ran 0 scripts and skipped 1/s); //
    }

    // Changing the extra args should change the fingerprint so that we're
    // stale.
    {
      const wireit = rig.exec(`${command} a -- ${extraDashes} FOO -BAR --BAZ`);
      const inv = await cmdA.nextInvocation();
      assert.deepEqual((await inv.environment()).argv.slice(3), [
        'FOO',
        '-BAR',
        '--BAZ',
      ]);
      inv.exit(0);
      assert.equal((await wireit.exit).code, 0);
      await wireit.waitForLog(/Ran 1 script and skipped 0/s); //
    }
  });

void test('cascade:false dependency does not inherit fingerprint', async () => {
  await using rig = await WireitTestRig.setup();

  //  a --[cascade:false]--> b --> c
  const a = await rig.newCommand();
  const b = await rig.newCommand();
  const c = await rig.newCommand();
  await rig.write({
    'package.json': {
      scripts: {
        a: 'wireit',
        b: 'wireit',
        c: 'wireit',
      },
      wireit: {
        a: {
          command: a.command,
          dependencies: [
            {
              script: 'b',
              cascade: false,
            },
          ],
          files: ['inputs/a'],
          output: [],
        },
        b: {
          command: b.command,
          dependencies: ['c'],
          files: ['inputs/b'],
          output: [],
        },
        c: {
          command: c.command,
          files: ['inputs/c'],
          output: [],
        },
      },
    },
  });

  // Initially everything runs.
  {
    await rig.write('inputs/a', 'v1');
    await rig.write('inputs/b', 'v1');
    await rig.write('inputs/c', 'v1');
    const wireit = rig.exec('npm run a');
    await wireit.waitForLog(/0% \[0 \/ 3\] \[1 running\] c/);
    (await c.nextInvocation()).exit(0);
    await wireit.waitForLog(/33% \[1 \/ 3\] \[1 running\] b/);
    (await b.nextInvocation()).exit(0);
    await wireit.waitForLog(/67% \[2 \/ 3\] \[1 running\] a/);
    (await a.nextInvocation()).exit(0);
    assert.equal((await wireit.exit).code, 0);
    assert.equal(a.numInvocations, 1);
    assert.equal(b.numInvocations, 1);
    assert.equal(c.numInvocations, 1);
    await wireit.waitForLog(/Ran 3 scripts and skipped 0/);
  }

  // Changing input of B re-runs B but not A.
  {
    await rig.write('inputs/b', 'v2');
    const wireit = rig.exec('npm run a');
    await wireit.waitForLog(/33% \[1 \/ 3\] \[1 running\] b/);
    (await b.nextInvocation()).exit(0);
    assert.equal((await wireit.exit).code, 0);
    assert.equal(a.numInvocations, 1);
    assert.equal(b.numInvocations, 2);
    assert.equal(c.numInvocations, 1);
    await wireit.waitForLog(/Ran 1 script and skipped 2/);
  }

  // Changing input of C re-runs B and C but not A.
  {
    await rig.write('inputs/c', 'v2');
    const wireit = rig.exec('npm run a');
    await wireit.waitForLog(/0% \[0 \/ 3\] \[1 running\] c/);
    (await c.nextInvocation()).exit(0);
    await wireit.waitForLog(/33% \[1 \/ 3\] \[1 running\] b/);
    (await b.nextInvocation()).exit(0);
    assert.equal((await wireit.exit).code, 0);
    assert.equal(a.numInvocations, 1);
    assert.equal(b.numInvocations, 3);
    assert.equal(c.numInvocations, 2);
    await wireit.waitForLog(/Ran 2 scripts and skipped 1/);
  }

  // Changing input of A re-runs A (just to be sure!).
  {
    await rig.write('inputs/a', 'v2');
    const wireit = rig.exec('npm run a');
    (await a.nextInvocation()).exit(0);
    assert.equal((await wireit.exit).code, 0);
    assert.equal(a.numInvocations, 2);
    assert.equal(b.numInvocations, 3);
    assert.equal(c.numInvocations, 2);
  }
});

void test('environment variables are passed to children', async () => {
  await using rig = await WireitTestRig.setup();

  const cmdA = await rig.newCommand();
  await rig.write({
    'package.json': {
      scripts: {
        a: 'wireit',
      },
      wireit: {
        a: {
          command: cmdA.command,
          files: [],
          output: [],
          env: {
            FOO: 'foo-good',
            BAR: {
              external: true,
            },
            QUX: {
              external: true,
              default: 'qux-good',
            },
          },
        },
      },
    },
  });

  const wireit = rig.exec('npm run a', {
    env: {
      // Overridden in the script config
      FOO: 'foo-bad',
      // Other vars should be passed down, regardless of "external" (which
      // only affects fingerprinting).
      BAR: 'bar-good',
      BAZ: 'baz-good',
    },
  });
  const inv = await cmdA.nextInvocation();
  const {env} = await inv.environment();
  assert.equal(env.FOO, 'foo-good');
  assert.equal(env.BAR, 'bar-good');
  assert.equal(env.BAZ, 'baz-good');
  assert.equal(env.QUX, 'qux-good');
  inv.exit(0);
  assert.equal((await wireit.exit).code, 0);
});
