/**
 * @license
 * Copyright 2022 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as pathlib from 'path';
import {test} from 'vitest';
import * as assert from 'node:assert';
import {rigTest} from './util/rig-test.js';
import {shuffle} from './util/shuffle.js';
import {IS_WINDOWS} from './util/windows.js';
import {NODE_MAJOR_VERSION} from './util/node-version.js';

void test(
  'fresh script is skipped',
  rigTest(async ({rig}) => {
    const cmdA = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA.command,
            files: ['input.txt'],
            output: [],
          },
        },
      },
      'input.txt': 'v0',
    });

    // Initially stale, so command is invoked.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // No input file changed, so script is fresh, and command is not invoked.
    {
      const exec = rig.exec('npm run a');
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }
  }),
);

void test(
  'changing input file makes script stale',
  rigTest(async ({rig}) => {
    const cmdA = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA.command,
            files: ['input.txt'],
            output: [],
          },
        },
      },
      'input.txt': 'v0',
    });

    // Initially stale, so command is invoked.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Input file changed, so script is stale, and command is invoked.
    {
      await rig.write({
        'input.txt': 'v1',
      });
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
    }
  }),
);

void test(
  'script with empty input files can be fresh',
  rigTest(async ({rig}) => {
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
          },
        },
      },
    });

    // Initially stale, so command is invoked.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // No input file changed, so script is fresh, and command is not invoked.
    {
      const exec = rig.exec('npm run a');
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }
  }),
);

void test(
  'empty directory is not included in fingerprint',
  rigTest(async ({rig}) => {
    const cmdA = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA.command,
            files: ['input/**'],
            output: [],
          },
        },
      },
    });

    // Initially stale, so command is invoked.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Empty directory created, but that doesn't count as an input file, so
    // script is still fresh.
    {
      await rig.mkdir('input/subdir');
      const exec = rig.exec('npm run a');
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }
  }),
);

void test(
  'changing script command makes script stale',
  rigTest(async ({rig}) => {
    const cmdA1 = await rig.newCommand();
    const cmdA2 = await rig.newCommand();

    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA1.command,
            files: ['a.txt'],
            output: [],
          },
        },
      },
      'a.txt': 'v0',
    });

    // Initially stale.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA1.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA1.numInvocations, 1);
      assert.equal(cmdA2.numInvocations, 0);
    }

    // Change the command.
    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA2.command,
            files: ['a.txt'],
            output: [],
          },
        },
      },
    });

    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA2.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA1.numInvocations, 1);
      assert.equal(cmdA2.numInvocations, 1);
    }
  }),
);

void test(
  'changing output glob patterns makes script stale',
  rigTest(async ({rig}) => {
    const cmdA = await rig.newCommand();

    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA.command,
            files: ['a.txt'],
            output: ['foo'],
          },
        },
      },
      'a.txt': 'v0',
    });

    // Initially stale.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Change the output setting.
    {
      await rig.write({
        'package.json': {
          scripts: {
            a: 'wireit',
          },
          wireit: {
            a: {
              command: cmdA.command,
              files: ['a.txt'],
              output: ['bar'],
            },
          },
        },
      });
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
    }
  }),
);

void test(
  'changing custom.lock invalidates when set in packageLocks',
  rigTest(async ({rig}) => {
    const cmdA = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA.command,
            // Note we must define files/output, or else we would never be fresh
            // anyway.
            files: [],
            output: [],
            packageLocks: ['custom.lock'],
          },
        },
      },
      'custom.lock': 'v0',
    });

    // Initial run.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Nothing changed. Expect no run.
    {
      const exec = rig.exec('npm run a');
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Change custom lockfile. Expect another run.
    {
      await rig.write({'custom.lock': 'v1'});
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
    }
  }),
);

void test(
  'packageLocks can have multiple files',
  rigTest(async ({rig}) => {
    const cmdA = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {
          a: 'wireit',
        },
        wireit: {
          a: {
            command: cmdA.command,
            // Note we must define files, or else we would never be fresh
            // anyway.
            files: [],
            output: [],
            packageLocks: ['lock1', 'lock2'],
          },
        },
      },
      lock1: 'v0',
      lock2: 'v0',
    });

    // Initial run.
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Nothing changed. Expect no run.
    {
      const exec = rig.exec('npm run a');
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Change lock1. Expect another run.
    {
      await rig.write({lock1: 'v1'});
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
    }

    // Change lock2. Expect another run.
    {
      await rig.write({lock2: 'v1'});
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 3);
    }
  }),
);

void test(
  'file-only rule affects fingerprint of consumers',
  rigTest(async ({rig}) => {
    const consumer = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {
          consumer: 'wireit',
          files: 'wireit',
        },
        wireit: {
          consumer: {
            command: consumer.command,
            dependencies: ['files'],
            files: [],
            output: [],
          },
          files: {
            files: ['foo'],
          },
        },
      },
    });

    // Consumer is initially stale.
    {
      await rig.write('foo', 'v0');
      const exec = rig.exec('npm run consumer');
      (await consumer.nextInvocation()).exit(0);
      assert.equal((await exec.exit).code, 0);
      assert.equal(consumer.numInvocations, 1);
    }

    // Nothing changed, consumer is still fresh.
    {
      const exec = rig.exec('npm run consumer');
      assert.equal((await exec.exit).code, 0);
      assert.equal(consumer.numInvocations, 1);
    }

    // Changed input file of the file-only script, consumer is now stale.
    {
      await rig.write('foo', 'v1');
      const exec = rig.exec('npm run consumer');
      (await consumer.nextInvocation()).exit(0);
      assert.equal((await exec.exit).code, 0);
      assert.equal(consumer.numInvocations, 2);
    }
  }),
);

void test(
  'changing external environment variable makes script stale',
  rigTest(async ({rig}) => {
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
              FOO: {
                external: true,
              },
            },
          },
        },
      },
    });

    // Initial run.
    {
      const wireit = rig.exec('npm run a', {env: {FOO: '1'}});
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await wireit.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Same environment variable, still fresh.
    {
      const wireit = rig.exec('npm run a', {env: {FOO: '1'}});
      const res = await wireit.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
    }

    // Change environment variable, now stale.
    {
      const wireit = rig.exec('npm run a', {env: {FOO: '2'}});
      const inv = await cmdA.nextInvocation();
      inv.exit(0);
      const res = await wireit.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
    }
  }),
);
