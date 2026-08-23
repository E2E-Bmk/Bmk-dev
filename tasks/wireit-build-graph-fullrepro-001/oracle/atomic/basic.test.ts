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

void test('dependency which is not in script section', async () => {
  await using rig = await WireitTestRig.setup();

  const cmdA = await rig.newCommand();
  const cmdB = await rig.newCommand();
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
          dependencies: ['b'],
        },
        b: {
          command: cmdB.command,
          files: [],
          output: [],
        },
      },
    },
  });

  const wireit = rig.exec('npm run a');
  await wireit.waitForLog(/0% \[0 \/ 2\] \[1 running\] b/);
  (await cmdB.nextInvocation()).exit(0);
  await wireit.waitForLog(/50% \[1 \/ 2\] \[1 running\] a/);
  (await cmdA.nextInvocation()).exit(0);
  const {code} = await wireit.exit;
  assert.equal(code, 0);
  await wireit.waitForLog(/Ran 2 scripts and skipped 0/);
});
