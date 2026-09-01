import { defineConfig } from "vitest/config";

/* One fork, one file at a time. The suite runs inside a memory-capped
 * container and the package under test may be delivered as a full source
 * tree rather than a bundle, whose import graph is large enough that two
 * concurrent workers exceed the cap and the runner is killed before any
 * behaviour is measured. Serialising the files keeps peak memory at one
 * graph regardless of how the delivery is laid out. */
export default defineConfig({
  test: {
    include: ["**/*.test.ts"],
    testTimeout: 30000,
    pool: "forks",
    poolOptions: { forks: { singleFork: true } },
    fileParallelism: false,
  },
});
