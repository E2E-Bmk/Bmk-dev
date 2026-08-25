import { createRequire } from 'node:module';
import type * as GraphQL from 'graphql';

/* The peer dependency, loaded the way the package under test loads it.
 *
 * `graphql` rejects a schema, a source or an AST node that came from a second
 * copy of itself. One physical copy on disk is not enough: the package under
 * test is reached through Node's loader, which resolves the bare specifier to
 * the CommonJS entry the manifest's `main` names, while a plain
 * `import ... from 'graphql'` in a test file is resolved by the test runner,
 * which prefers the ES entry beside it. One file on disk, two class identities,
 * and every call that hands a schema across the boundary fails for a reason that
 * has nothing to do with the implementation.
 *
 * Requiring the peer here puts this suite on the same entry as the package under
 * test whichever module format the package chose, and re-exporting it from one
 * module keeps every test file on that single instance.
 */
const peer = createRequire(import.meta.url)('graphql') as typeof GraphQL;

export const { buildSchema, parse, print, Source } = peer;
export type { GraphQLSchema } from 'graphql';
