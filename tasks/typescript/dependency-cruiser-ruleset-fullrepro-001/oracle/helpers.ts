/* Fixture builders and the machine-readable projection of a violation.
 *
 * The builders construct a schema-valid cruise result; the reporter text is not
 * part of the contract, so a comparison reads a violation's type, coordinates,
 * rule and its one type-specific carrier, and drops the rest.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Any = any;

const ENVIRONMENT = {
  version: "18.2.0",
  nodeVersionSupported: "^42",
  nodeVersionFound: "v42.0.0",
  osVersionFound: "riscv pinecil@1.2.3",
  transpilersFound: [] as Any[],
  extensionsFound: [] as Any[],
};

export function dep(resolved: string, opts: Any = {}): Any {
  const { valid = true, rules = [], dependencyTypes = ["local"], cycle, instability, module } = opts;
  const d: Any = {
    resolved, module: module ?? "./" + resolved, moduleSystem: "es6", dynamic: false,
    exoticallyRequired: false, matchesDoNotFollow: false, coreModule: false, followable: true,
    couldNotResolve: false, circular: Boolean(cycle), dependencyTypes, valid, rules,
  };
  if (cycle) d.cycle = cycle;
  if (instability !== undefined) d.instability = instability;
  return d;
}

export function mod(source: string, opts: Any = {}): Any {
  const { deps = [], valid, rules = [], instability, reaches, orphan = false } = opts;
  const m: Any = {
    source, dependencies: deps, orphan, rules,
    valid: valid ?? (!deps.some((x: Any) => x.valid === false) && rules.length === 0),
  };
  if (instability !== undefined) m.instability = instability;
  if (reaches) m.reaches = reaches;
  return m;
}

export function result(modules: Any[], ruleSetUsed: Any = { forbidden: [], allowed: [], required: [] }): Any {
  return {
    modules,
    summary: {
      violations: [], error: 0, warn: 0, info: 0, ignore: 0,
      totalCruised: modules.length,
      totalDependenciesCruised: modules.reduce((n: number, m: Any) => n + m.dependencies.length, 0),
      optionsUsed: { args: "", outputType: "json" },
      ruleSetUsed,
      environment: { ...ENVIRONMENT },
    },
  };
}

export function outline(violations: Any[]): Any[] {
  return violations.map((v) => {
    const o: Any = { type: v.type ?? "dependency", from: v.from, to: v.to,
      rule: { name: v.rule.name, severity: v.rule.severity } };
    if (v.unresolvedTo !== undefined) o.unresolvedTo = v.unresolvedTo;
    if (v.dependencyTypes !== undefined) o.dependencyTypes = v.dependencyTypes;
    if (v.cycle !== undefined) o.cycle = v.cycle;
    if (v.via !== undefined) o.via = v.via;
    if (v.metrics !== undefined) o.metrics = v.metrics;
    return o;
  });
}
