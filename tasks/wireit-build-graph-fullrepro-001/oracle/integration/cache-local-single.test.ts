import {test} from 'vitest';
import * as assert from 'node:assert';
import {rigTest} from './util/rig-test.js';

void test(
  'caches single file',
  rigTest(async ({rig}) => {
    const cmdA = await rig.newCommand();
    await rig.write({
      'package.json': {
        scripts: {a: 'wireit'},
        wireit: {a: {command: cmdA.command, files: ['input'], output: ['output']}},
      },
      input: 'v0',
    });
    {
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      await rig.write({output: 'v0'});
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 1);
      assert.equal(await rig.read('output'), 'v0');
    }
    {
      await rig.write({input: 'v1'});
      const exec = rig.exec('npm run a');
      const inv = await cmdA.nextInvocation();
      await rig.write({output: 'v1'});
      inv.exit(0);
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
      assert.equal(await rig.read('output'), 'v1');
    }
    {
      await rig.write({input: 'v0'});
      const exec = rig.exec('npm run a');
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
      assert.equal(await rig.read('output'), 'v0');
    }
    {
      await rig.write({input: 'v1'});
      const exec = rig.exec('npm run a');
      const res = await exec.exit;
      assert.equal(res.code, 0);
      assert.equal(cmdA.numInvocations, 2);
      assert.equal(await rig.read('output'), 'v1');
    }
  }),
);
