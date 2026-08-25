import { createRequire } from 'node:module';
import { existsSync, lstatSync, readFileSync, realpathSync, renameSync, symlinkSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

const PACKAGE_UNDER_TEST = '@graphql-inspector/core';

/* The peer dependency has to be one copy, reached by one route.
 *
 * `graphql` rejects a schema, a source or an AST node that came from a second
 * copy of itself, and there are two ways a second copy appears here.
 *
 * The first is on disk: a delivery may declare the peer, and npm then installs it
 * inside the delivery's own tree. That copy is moved aside and replaced by a link
 * to the copy installed beside this suite. Nothing is deleted, and a delivery
 * that declares nothing is left untouched.
 *
 * The second is in the manifest: the peer ships a CommonJS `index.js` and an ES
 * `index.mjs`, names the first in `main` and the second in `module`, and declares
 * no `exports` map. Node's loader therefore takes the CommonJS entry and a
 * bundler's default field order takes the ES one -- one package on disk, two
 * class identities, and a delivery that ships CommonJS fails every test while one
 * that ships ES modules passes, with the implementation making no difference.
 * Dropping the `module` field leaves a single entry for every route.
 */
export default function ensureSinglePeer(): void {
  const ours = dirname(createRequire(import.meta.url).resolve('graphql/package.json'));

  let root: string | undefined;
  try {
    root = realpathSync(join(process.cwd(), 'node_modules', PACKAGE_UNDER_TEST));
  } catch {
    root = undefined;
  }

  if (root !== undefined) {
    const theirs = join(root, 'node_modules', 'graphql');
    if (existsSync(theirs) && realpathSync(theirs) !== ours) {
      renameSync(theirs, `${theirs}.duplicate`);
      symlinkSync(ours, theirs, 'dir');
    }
  }

  const manifestPath = join(ours, 'package.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  if (manifest.module !== undefined || manifest.main !== 'index.js') {
    delete manifest.module;
    manifest.main = 'index.js';
    writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  }
}
