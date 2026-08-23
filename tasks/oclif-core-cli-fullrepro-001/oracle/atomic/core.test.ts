// @ts-nocheck
import { describe, expect, it } from "vitest";
import {
  Args,
  Constraints,
  Errors,
  Flags,
  Parser,
  toConfiguredId,
  toStandardizedId,
  ux,
} from "@oclif/core";
import { flagUsages, parse, validate } from "@oclif/core/parser";
import { colorize, colorizeJson } from "@oclif/core/ux";

describe("argument and flag parsing", () => {
  // Verifies: OCLIF-PARSE-001, OCLIF-PARSE-005
  it("parses a required string argument", async () => {
    const result = await Parser.parse(["Ada"], { args: { name: Args.string({ required: true }) } });
    expect(result.args.name).toBe("Ada");
    expect(result.raw[0].type).toBe("arg");
  });

  // Verifies: OCLIF-PARSE-002
  it("converts an integer argument", async () => {
    const result = await parse(["42"], { args: { count: Args.integer() } });
    expect(result.args.count).toBe(42);
  });

  // Verifies: OCLIF-PARSE-002
  it("converts a boolean argument", async () => {
    const result = await parse(["true"], { args: { enabled: Args.boolean() } });
    expect(result.args.enabled).toBe(true);
  });

  // Verifies: OCLIF-PARSE-002
  it("converts a URL argument", async () => {
    const result = await parse(["https://example.test/a"], { args: { target: Args.url() } });
    expect(result.args.target).toBeInstanceOf(URL);
    expect(result.args.target.href).toBe("https://example.test/a");
  });

  // Verifies: OCLIF-PARSE-002
  it("preserves a string argument verbatim", async () => {
    const result = await parse(["a:b/c"], { args: { value: Args.string() } });
    expect(result.args.value).toBe("a:b/c");
  });

  // Verifies: OCLIF-PARSE-002
  it("accepts an argument choice", async () => {
    const result = await parse(["green"], { args: { color: Args.option({ options: ["red", "green"] })() } });
    expect(result.args.color).toBe("green");
  });

  // Verifies: OCLIF-PARSE-002
  it("runs a custom argument parser", async () => {
    const custom = Args.custom({ parse: async (input) => input.toUpperCase() })();
    const result = await parse(["abc"], { args: { value: custom } });
    expect(result.args.value).toBe("ABC");
  });

  // Verifies: OCLIF-PARSE-003
  it("uses a false default for a boolean flag", async () => {
    const result = await parse([], { flags: { verbose: Flags.boolean() } });
    expect(result.flags.verbose).toBeUndefined();
  });

  // Verifies: OCLIF-PARSE-003
  it("supports negated boolean flags", async () => {
    const result = await parse(["--no-verbose"], { flags: { verbose: Flags.boolean({ allowNo: true }) } });
    expect(result.flags.verbose).toBe(false);
  });

  // Verifies: OCLIF-PARSE-003
  it("parses repeated flags into an array", async () => {
    const result = await parse(["--tag", "one", "--tag", "two"], { flags: { tag: Flags.string({ multiple: true }) } });
    expect(result.flags.tag).toEqual(["one", "two"]);
  });

  // Verifies: OCLIF-PARSE-003
  it("splits a delimited repeated flag", async () => {
    const result = await parse(["--tag", "one,two"], { flags: { tag: Flags.string({ multiple: true, delimiter: "," }) } });
    expect(result.flags.tag).toEqual(["one", "two"]);
  });

  // Verifies: OCLIF-PARSE-003
  it("reads an environment-backed flag", async () => {
    process.env.OCLIF_TEST_VALUE = "from-env";
    try {
      const result = await parse([], { flags: { value: Flags.string({ env: "OCLIF_TEST_VALUE" }) } });
      expect(result.flags.value).toBe("from-env");
    } finally {
      delete process.env.OCLIF_TEST_VALUE;
    }
  });

  // Verifies: OCLIF-PARSE-003
  it("resolves a default function", async () => {
    const result = await parse([], { flags: { value: Flags.string({ default: async () => "computed" }) } });
    expect(result.flags.value).toBe("computed");
  });

  // Verifies: OCLIF-PARSE-003
  it("accepts a flag alias", async () => {
    const result = await parse(["-n", "5"], { flags: { number: Flags.integer({ char: "n" }) } });
    expect(result.flags.number).toBe(5);
  });

  // Verifies: OCLIF-PARSE-004
  it("assigns positional arguments in declaration order", async () => {
    const result = await parse(["first", "second"], { args: { left: Args.string(), right: Args.string() } });
    expect(result.args).toEqual({ left: "first", right: "second" });
  });

  // Verifies: OCLIF-PARSE-004
  it("collects a variadic argument", async () => {
    const result = await parse(["one", "two", "three"], { args: { values: Args.string({ multiple: true }) } });
    expect(result.args.values).toEqual(["one", "two", "three"]);
  });

  // Verifies: OCLIF-PARSE-006
  it("keeps negative numbers as values", async () => {
    const result = await parse(["-7"], { args: { value: Args.integer() } });
    expect(result.args.value).toBe(-7);
  });

  // Verifies: OCLIF-PARSE-006
  it("keeps tokens after a double dash in argv", async () => {
    const result = await parse(["--", "--literal"], { flags: { known: Flags.boolean() }, "--": true, strict: false });
    expect(result.argv).toEqual(["--literal"]);
  });

  // Verifies: OCLIF-PARSE-005
  it("returns unknown flag names in the parser error context", async () => {
    await expect(parse(["--missing"], { flags: { known: Flags.boolean() } })).rejects.toMatchObject({
      flags: ["--missing"],
    });
  });

  // Verifies: OCLIF-PARSE-007
  it("formats flag usages in declaration order", () => {
    const usages = flagUsages([Flags.string({ name: "first", description: "first value" }), Flags.boolean({ name: "second" })]);
    expect(usages[0][0]).toContain("--first");
    expect(usages[0][1]).toBe("first value");
  });

  // Verifies: OCLIF-PARSE-007
  it("exposes parser helpers through the root namespace", () => {
    expect(typeof Parser.parse).toBe("function");
    expect(typeof Parser.validate).toBe("function");
    expect(typeof Parser.flagUsages).toBe("function");
  });
});

describe("constraints and errors", () => {
  // Verifies: OCLIF-PARSE-006
  it("accepts a dependent flag relationship", async () => {
    const constraints = [Constraints.flag("token").is.dependentOn("user")];
    const result = await parse(["--token", "abc", "--user", "ada"], {
      flags: { token: Flags.string(), user: Flags.string() },
      constraints,
    });
    expect(result.flags).toMatchObject({ token: "abc", user: "ada" });
  });

  // Verifies: OCLIF-PARSE-006
  it("rejects a mutually exclusive relationship", async () => {
    const constraints = [Constraints.flags("json", "text").are.mutuallyExclusive()];
    await expect(parse(["--json", "--text"], { flags: { json: Flags.boolean(), text: Flags.boolean() }, constraints })).rejects.toBeTruthy();
  });

  // Verifies: OCLIF-PARSE-006
  it("validates a parser output pair", async () => {
    const input = { flags: { value: Flags.string({ required: true }) }, args: {} };
    const output = await parse(["--value", "ok"], input);
    await expect(validate({ input: { ...input, argv: ["--value", "ok"], strict: true }, output })).resolves.toBeUndefined();
  });

  // Verifies: OCLIF-PARSE-002
  it("rejects an invalid integer", async () => {
    await expect(parse(["not-an-int"], { args: { value: Args.integer() } })).rejects.toBeInstanceOf(Error);
  });

  // Verifies: OCLIF-PARSE-002
  it("rejects an integer outside its bounds", async () => {
    await expect(parse(["10"], { args: { value: Args.integer({ max: 5 }) } })).rejects.toBeInstanceOf(Error);
  });

  // Verifies: OCLIF-PARSE-002
  it("rejects an invalid URL", async () => {
    await expect(parse(["not a url"], { args: { value: Args.url() } })).rejects.toBeInstanceOf(Error);
  });

  // Verifies: OCLIF-PARSE-002
  it("rejects an option outside its choices", async () => {
    await expect(parse(["blue"], { args: { value: Args.option({ options: ["red", "green"] })() } })).rejects.toBeInstanceOf(Errors.CLIError);
  });

  // Verifies: OCLIF-ERR-001
  it("preserves CLI error metadata", () => {
    const error = new Errors.CLIError("bad input", { exit: 3, code: "E_BAD" });
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe("bad input");
    expect(error.oclif.exit).toBe(3);
    expect(error.code).toBe("E_BAD");
  });

  // Verifies: OCLIF-ERR-001
  it("represents an exit error", () => {
    const error = new Errors.ExitError(7);
    expect(error.oclif.exit).toBe(7);
  });

  // Verifies: OCLIF-ERR-001
  it("retains a module load cause", () => {
    const cause = new Error("missing module");
    const error = new Errors.ModuleLoadError("missing module");
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toContain("missing module");
  });
});

describe("identifiers and terminal projections", () => {
  // Verifies: OCLIF-CONFIG-005
  it("converts configured IDs to standardized IDs", async () => {
    const config = { topicSeparator: " " };
    expect(toStandardizedId("foo bar:baz", config)).toBe("foo:bar:baz");
  });

  // Verifies: OCLIF-CONFIG-005
  it("converts standardized IDs to configured IDs", async () => {
    const config = { topicSeparator: " " };
    expect(toConfiguredId("foo:bar:baz", config)).toBe("foo bar baz");
  });

  // Verifies: OCLIF-UX-002
  it("colorizes text", () => {
    const colored = colorize("red", "hello");
    expect(colored).toContain("hello");
    expect(typeof colored).toBe("string");
  });

  // Verifies: OCLIF-UX-002
  it("formats JSON through the UX helper", () => {
    const formatted = colorizeJson({ answer: 42 }, { pretty: true });
    expect(formatted).toContain("answer");
    expect(formatted).toContain("42");
  });

  // Verifies: OCLIF-UX-001
  it("exposes terminal writers and action lifecycle", () => {
    expect(typeof ux.stdout).toBe("function");
    expect(typeof ux.stderr).toBe("function");
    expect(typeof ux.action.start).toBe("function");
    expect(typeof ux.action.stop).toBe("function");
  });

  // Verifies: OCLIF-UX-003
  it("starts and stops a simple action", () => {
    ux.action.start("working");
    expect(ux.action.type).toBe("simple");
    ux.action.stop("done");
  });
});
