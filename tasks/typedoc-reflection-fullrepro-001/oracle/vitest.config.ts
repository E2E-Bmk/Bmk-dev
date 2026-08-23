import { defineConfig } from "vitest/config";
import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);

function typedocAliases() {
  const aliases: Record<string, string> = {};
  try {
    const packageJsonPath = require.resolve("typedoc/package.json");
    const packageRoot = path.dirname(packageJsonPath);
    const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8"));
    const typedocTs = packageJson.exports?.["."]?.["typedoc-ts"];
    if (typeof typedocTs === "string") {
      const target = path.resolve(packageRoot, typedocTs);
      if (existsSync(target)) {
        aliases.typedoc = target;
      }
    }
    for (const name of ["#utils", "#models", "#serialization", "#node-utils"]) {
      const target = packageJson.imports?.[name]?.["typedoc-ts"];
      if (typeof target === "string") {
        const resolved = path.resolve(packageRoot, target);
        if (existsSync(resolved)) {
          aliases[name] = resolved;
        }
      }
    }
  } catch {
    // Fall back to package resolution when the target package is not installed yet.
  }
  return aliases;
}

const aliases = typedocAliases();

export default defineConfig({
  resolve: {
    alias: aliases,
    conditions: ["typedoc-ts", "node", "import", "default"],
  },
  ssr: {
    noExternal: ["typedoc"],
  },
  test: {
    testTimeout: 30000,
  },
});
