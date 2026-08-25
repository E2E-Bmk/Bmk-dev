import { defineConfig } from 'vitest/config';

// `graphql` is a peer dependency, and it rejects a schema, a source or an AST
// node that came from a second copy of itself ("from another module or realm").
// Keeping the measurement about behaviour rather than about packaging needs three
// arrangements, each closing a different way a second copy appears.
//
// `setup/peer.ts` closes the first: a delivery that names the peer gets its own
// physical copy installed beside it, which that hook replaces with a link to the
// copy installed here.
//
// The `external` list closes the second: the package under test arrives as a
// directory link, which this runner would otherwise treat as source and load
// through its own module registry while Node loads a CommonJS delivery. Handing
// it to Node either way is what a real consumer does.
//
// `peer.ts` closes the third, on the test side: it requires the peer through
// Node rather than importing it, so the suite and the package under test hold
// the same instance whichever module format the delivery chose.
export default defineConfig({
  resolve: {
    dedupe: ['graphql'],
  },
  test: {
    include: ['**/*.test.ts'],
    globalSetup: ['./setup/peer.ts'],
    server: {
      deps: {
        external: [/graphql/, /@graphql-inspector\/core/],
      },
    },
    testTimeout: 30000,
  },
});
