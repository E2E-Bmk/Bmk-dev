// @ts-nocheck
import { afterEach, describe, expect, it, vi } from "vitest";
import { mkdtemp, mkdir, rm, symlink, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";
import {
  Command,
  Config,
  Errors,
  Flags,
  Help,
  execute,
  flush,
  getLogger,
  run,
  settings,
} from "@oclif/core";
import {
  getHelpFlagAdditions,
  normalizeArgv,
  standardizeIDFromArgv,
} from "@oclif/core/help";

const tempDirs: string[] = [];
const require = createRequire(import.meta.url);
const coreRoot = dirname(require.resolve("@oclif/core/package.json"));

afterEach(async () => {
  vi.restoreAllMocks();
  for (const directory of tempDirs.splice(0)) await rm(directory, { recursive: true, force: true });
});

async function localCli(options: { hooks?: Record<string, string>; topicSeparator?: " " | ":"; additionalHelpFlags?: string[]; additionalVersionFlags?: string[]; includeFailingCommand?: boolean } = {}) {
  const root = await mkdtemp(join(tmpdir(), "oclif-oracle-"));
  tempDirs.push(root);
  await mkdir(join(root, "commands"), { recursive: true });
  await mkdir(join(root, "node_modules", "@oclif"), { recursive: true });
  await symlink(coreRoot, join(root, "node_modules", "@oclif", "core"), "junction");
  await writeFile(join(root, "package.json"), JSON.stringify({
    name: "oracle-cli",
    version: "1.2.3",
    oclif: {
      bin: "oracle",
      commands: { strategy: "pattern", target: "./commands" },
      ...options,
    },
  }));
  await writeFile(join(root, "commands", "hello.js"), `
    const {Command, Flags} = require('@oclif/core')
    class Hello extends Command {
      static description = 'say hello'
      static flags = {name: Flags.string({char: 'n', default: 'world'}), json: Flags.boolean()}
      async run() { const {flags} = await this.parse(Hello); globalThis.__oclifOracleEvents.push('run:' + flags.name); return 'hello ' + flags.name }
      async init() { globalThis.__oclifOracleEvents.push('init') }
      async finally() { globalThis.__oclifOracleEvents.push('finally') }
    }
    module.exports = Hello
  `);
  await writeFile(join(root, "commands", "goodbye.js"), `
    const {Command} = require('@oclif/core')
    class Goodbye extends Command { async run() { globalThis.__oclifOracleEvents.push('goodbye'); return 'bye' } }
    module.exports = Goodbye
  `);
  if (options.includeFailingCommand) {
    await writeFile(join(root, "commands", "fail.js"), `
      const {Command} = require('@oclif/core')
      class Fail extends Command {
        async init() { globalThis.__oclifOracleEvents.push('init-fail') }
        async run() { throw new Error('command failure') }
        async finally() { globalThis.__oclifOracleEvents.push('finally-fail') }
      }
      module.exports = Fail
    `);
  }
  return root;
}

describe("configuration and command workflows", () => {
  // Verifies: OCLIF-CONFIG-001, OCLIF-CONFIG-003, OCLIF-CVI-003
  it("loads a local command graph", async () => {
    const root = await localCli();
    const config = await Config.load({ root });
    expect(config.name).toBe("oracle-cli");
    expect(config.bin).toBe("oracle");
    expect(config.commandIDs.sort()).toEqual(["goodbye", "hello"]);
    expect(config.plugins.has("oracle-cli")).toBe(true);
  });

  // Verifies: OCLIF-CONFIG-002, OCLIF-CVI-002
  it("finds and loads a command class", async () => {
    const config = await Config.load({ root: await localCli() });
    const cached = config.findCommand("hello", { must: true });
    const klass = await cached.load();
    expect(cached.id).toBe("hello");
    expect(klass.id).toBe("hello");
  });

  // Verifies: OCLIF-CMD-001, OCLIF-CMD-002
  it("runs a configured command through its lifecycle", async () => {
    globalThis.__oclifOracleEvents = [];
    const config = await Config.load({ root: await localCli() });
    const result = await config.runCommand("hello", ["--name", "Ada"]);
    expect(result).toBe("hello Ada");
    expect(globalThis.__oclifOracleEvents).toEqual(["init", "run:Ada", "finally"]);
  });

  // Verifies: OCLIF-CMD-002, OCLIF-CVI-005
  it("runs command finalization when the command fails", async () => {
    globalThis.__oclifOracleEvents = [];
    const config = await Config.load({ root: await localCli({ includeFailingCommand: true }) });
    await expect(config.runCommand("fail", [])).rejects.toThrow("command failure");
    expect(globalThis.__oclifOracleEvents).toEqual(["init-fail", "finally-fail"]);
  });

  // Verifies: OCLIF-CMD-001, OCLIF-CVI-001
  it("runs a command class from a root load option", async () => {
    globalThis.__oclifOracleEvents = [];
    const root = await localCli();
    const config = await Config.load({ root });
    const klass = await config.findCommand("hello", { must: true }).load();
    const result = await klass.run(["--name", "Lin"], { root });
    expect(result).toBe("hello Lin");
    expect(globalThis.__oclifOracleEvents).toContain("run:Lin");
  });

  // Verifies: OCLIF-CONFIG-004
  it("derives scoped environment keys from the CLI bin", async () => {
    const config = await Config.load({ root: await localCli() });
    process.env.ORACLE_SWITCH = "true";
    try {
      expect(config.scopedEnvVarKey("switch")).toBe("ORACLE_SWITCH");
      expect(config.scopedEnvVarKeys("switch")).toContain("ORACLE_SWITCH");
      expect(config.scopedEnvVarTrue("switch")).toBe(true);
    } finally {
      delete process.env.ORACLE_SWITCH;
    }
  });

  // Verifies: OCLIF-CONFIG-001
  it("loads configuration from a package file URL", async () => {
    const root = await localCli();
    const config = await Config.load(pathToFileURL(join(root, "package.json")).href);
    expect(config.root).toBe(root);
    expect(config.version).toBe("1.2.3");
  });

  // Verifies: OCLIF-CONFIG-002
  it("returns undefined for a missing optional command", async () => {
    const config = await Config.load({ root: await localCli() });
    expect(config.findCommand("missing", { must: false })).toBeUndefined();
  });

  // Verifies: OCLIF-CONFIG-002
  it("rejects a missing required command", async () => {
    const config = await Config.load({ root: await localCli() });
    expect(() => config.findCommand("missing", { must: true })).toThrow();
  });

  // Verifies: OCLIF-CONFIG-005, OCLIF-CVI-009
  it("uses a configured space topic separator", async () => {
    const config = await Config.load({ root: await localCli({ topicSeparator: " " }) });
    expect(config.topicSeparator).toBe(" ");
    expect(normalizeArgv(config, ["hello"])).toEqual(["hello"]);
  });

  // Verifies: OCLIF-CMD-003
  it("suppresses command logs when JSON output is enabled", async () => {
    class JsonCommand extends Command {
      static enableJsonFlag = true;
      static flags = { json: Flags.boolean() };
      async run() { this.log("ordinary output"); return "ok"; }
    }
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);
    const config = await Config.load({ root: await localCli() });
    const command = new JsonCommand(["--json"], config);
    await command.run();
    expect(command.jsonEnabled()).toBe(true);
    expect(write).not.toHaveBeenCalledWith(expect.stringContaining("ordinary output"));
  });
});

describe("help and dispatch workflows", () => {
  // Verifies: OCLIF-HELP-002
  it("reads configured help aliases", async () => {
    const config = await Config.load({ root: await localCli({ additionalHelpFlags: ["-h", "--assist"] }) });
    expect(getHelpFlagAdditions(config)).toEqual(expect.arrayContaining(["-h", "--assist"]));
  });

  // Verifies: OCLIF-HELP-002
  it("standardizes command argv for a configured graph", async () => {
    const config = await Config.load({ root: await localCli() });
    expect(standardizeIDFromArgv(["hello", "--name", "Ada"], config)).toEqual(["hello", "--name", "Ada"]);
  });

  // Verifies: OCLIF-HELP-001
  it("renders root help from a loaded configuration", async () => {
    const config = await Config.load({ root: await localCli() });
    const help = new Help(config);
    const text = help.formatRoot();
    expect(text).toContain("oracle-cli");
    expect(text).toContain("USAGE");
  });

  // Verifies: OCLIF-HOOK-001, OCLIF-CVI-006
  it("dispatches a help request without running a command", async () => {
    globalThis.__oclifOracleEvents = [];
    const root = await localCli();
    await run(["--help"], { root });
    expect(globalThis.__oclifOracleEvents).not.toContainEqual(expect.stringMatching(/^run:/));
  });

  // Verifies: OCLIF-HOOK-001, OCLIF-CVI-007
  it("dispatches a version request without running a command", async () => {
    globalThis.__oclifOracleEvents = [];
    const root = await localCli();
    await run(["--version"], { root });
    expect(globalThis.__oclifOracleEvents).toEqual([]);
  });

  // Verifies: OCLIF-HOOK-001
  it("runs a selected command through the top-level dispatcher", async () => {
    globalThis.__oclifOracleEvents = [];
    await run(["hello", "--name", "Mia"], { root: await localCli() });
    expect(globalThis.__oclifOracleEvents).toContain("run:Mia");
  });

  // Verifies: OCLIF-HOOK-004
  it("requires a directory or load options for execute", async () => {
    await expect(execute({})).rejects.toBeInstanceOf(Errors.CLIError);
  });

  // Verifies: OCLIF-HOOK-004
  it("executes a local command through execute", async () => {
    globalThis.__oclifOracleEvents = [];
    await execute({ dir: await localCli(), args: ["hello", "--name", "Nia"] });
    expect(globalThis.__oclifOracleEvents).toContain("run:Nia");
  });

  // Verifies: OCLIF-HOOK-004
  it("flushes pending output", async () => {
    await expect(flush(0)).resolves.toBeUndefined();
  });
});

describe("hook, logger, and settings workflows", () => {
  // Verifies: OCLIF-HOOK-003
  it("returns a successful hook result", async () => {
    const root = await localCli();
    await writeFile(join(root, "hook.js"), "module.exports = async () => 'hook-value'");
    const config = await Config.load({ root });
    config.plugins.get("oracle-cli").hooks.init = [{ target: "./hook.js", identifier: "default" }];
    const result = await config.runHook("init", { argv: [] }, undefined, true);
    expect(result.successes).toHaveLength(1);
    expect(result.successes[0].result).toBe("hook-value");
  });

  // Verifies: OCLIF-HOOK-003
  it("captures a failing hook when requested", async () => {
    const root = await localCli();
    await writeFile(join(root, "hook.js"), "module.exports = async () => { throw new Error('hook failure') }");
    const config = await Config.load({ root });
    config.plugins.get("oracle-cli").hooks.init = [{ target: "./hook.js", identifier: "default" }];
    const result = await config.runHook("init", { argv: [] }, undefined, true);
    expect(result.failures).toHaveLength(1);
    expect(result.failures[0].error).toBeInstanceOf(Error);
  });

  // Verifies: OCLIF-HOOK-003, OCLIF-CVI-004
  it("returns a preparse hook result containing argv", async () => {
    const root = await localCli();
    await writeFile(join(root, "preparse.js"), "module.exports = async () => ({ argv: ['hello', '--name', 'Hooked'] })");
    const config = await Config.load({ root });
    config.plugins.get("oracle-cli").hooks.preparse = [{ target: "./preparse.js", identifier: "default" }];
    const result = await config.runHook("preparse", { argv: [] }, undefined, true);
    expect(result.successes[0].result).toEqual({ argv: ["hello", "--name", "Hooked"] });
  });

  // Verifies: OCLIF-CMD-003
  it("returns a logger for a namespace", () => {
    const logger = getLogger("oracle-test");
    expect(typeof logger.debug).toBe("function");
  });

  // Verifies: OCLIF-CMD-003
  it("exposes mutable global settings", () => {
    const prior = settings.debug;
    settings.debug = true;
    expect(settings.debug).toBe(true);
    settings.debug = prior;
  });
});
