import { expect, test } from 'vitest';

import { format } from '../subject';
import { dep, mod, result, outline } from '../helpers';

/* One format() call per test: a schema-valid cruise result and a rule set in,
   the re-summarised report out. Every assertion reads the machine-readable half
   of the report -- the violation list (type, coordinates, rule, and the
   type-specific carrier) and the four severity counts. Reporter text is asserted
   only where the specification makes it contractual (exit codes, the "no
   violations" line), never its incidental wording. */


// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("a forbidden dependency on an invalid edge becomes one dependency violation", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-b",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-b",
                severity: "error"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-b",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "no-b",
        severity: "error"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("an unresolved specifier surfaces as unresolvedTo distinct from the resolved path", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-x",
        severity: "warn",
        from: {

        },
        to: {
          path: "x"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "node_modules/x/index.js",
            module: "x",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-x",
                severity: "warn"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 1,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-x",
            severity: "warn",
            from: {

            },
            to: {
              path: "x"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "node_modules/x/index.js",
      rule: {
        name: "no-x",
        severity: "warn"
      },
      unresolvedTo: "x",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("an invalid dependency with an empty rules array yields no violation", async () => {
  const ruleSet = {
    forbidden: [],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: []
          }],
        orphan: false,
        rules: [],
        valid: false
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 1,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("a valid dependency yields no violation even when the rule set forbids its path", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-b",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: true,
            rules: []
          }],
        orphan: false,
        rules: [],
        valid: true
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-b",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("two invalid dependencies on one module become two violations", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-b",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }, {
        name: "no-c",
        severity: "warn",
        from: {

        },
        to: {
          path: "c"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-b",
                severity: "error"
              }]
          }, {
            resolved: "c.js",
            module: "c.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-c",
                severity: "warn"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }, {
        source: "c.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 3,
      totalDependenciesCruised: 2,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-b",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }, {
            name: "no-c",
            severity: "warn",
            from: {

            },
            to: {
              path: "c"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "no-b",
        severity: "error"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }, {
      type: "dependency",
      from: "a.js",
      to: "c.js",
      rule: {
        name: "no-c",
        severity: "warn"
      },
      unresolvedTo: "c.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("a dependency carrying two rules becomes two violations at one edge", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-b",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }, {
        name: "also-no-b",
        severity: "info",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-b",
                severity: "error"
              }, {
                name: "also-no-b",
                severity: "info"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-b",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }, {
            name: "also-no-b",
            severity: "info",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "no-b",
        severity: "error"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }, {
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "also-no-b",
        severity: "info"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 0, 1, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("a rule name absent from the rule set keeps the default dependency type", async () => {
  const ruleSet = {
    forbidden: [],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "ghost-rule",
                severity: "warn"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "ghost-rule",
        severity: "warn"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("the reported severity is copied from the attached rule, not recomputed", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-b",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-b",
                severity: "info"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-b",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "no-b",
        severity: "info"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 0, 1, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("an invalid module becomes one module violation from and to itself", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-orphans",
        severity: "warn",
        from: {
          orphan: true
        },
        to: {

        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "remi.js",
        dependencies: [],
        orphan: true,
        rules: [{
            name: "no-orphans",
            severity: "warn"
          }],
        valid: false
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 1,
      totalDependenciesCruised: 0,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-orphans",
            severity: "warn",
            from: {
              orphan: true
            },
            to: {

            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "module",
      from: "remi.js",
      to: "remi.js",
      rule: {
        name: "no-orphans",
        severity: "warn"
      }
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("an invalid module with two rules becomes two module violations", async () => {
  const ruleSet = {
    forbidden: [{
        name: "r1",
        severity: "error",
        from: {

        },
        to: {

        }
      }, {
        name: "r2",
        severity: "warn",
        from: {

        },
        to: {

        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "m.js",
        dependencies: [],
        orphan: false,
        rules: [{
            name: "r1",
            severity: "error"
          }, {
            name: "r2",
            severity: "warn"
          }],
        valid: false
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 1,
      totalDependenciesCruised: 0,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "r1",
            severity: "error",
            from: {

            },
            to: {

            }
          }, {
            name: "r2",
            severity: "warn",
            from: {

            },
            to: {

            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "module",
      from: "m.js",
      to: "m.js",
      rule: {
        name: "r1",
        severity: "error"
      }
    }, {
      type: "module",
      from: "m.js",
      to: "m.js",
      rule: {
        name: "r2",
        severity: "warn"
      }
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: DC-EVAL-001, DC-EVAL-002, DC-EVAL-003
test("a valid module yields no module violation", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-orphans",
        severity: "warn",
        from: {

        },
        to: {

        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "m.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 1,
      totalDependenciesCruised: 0,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-orphans",
            severity: "warn",
            from: {

            },
            to: {

            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("an invalid circular dependency under a circular rule becomes a cycle violation", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-circular",
        severity: "error",
        from: {

        },
        to: {
          circular: true
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: true,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-circular",
                severity: "error"
              }],
            cycle: [{
                name: "b.js",
                dependencyTypes: ["local"]
              }, {
                name: "a.js",
                dependencyTypes: ["local"]
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-circular",
            severity: "error",
            from: {

            },
            to: {
              circular: true
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "cycle",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "no-circular",
        severity: "error"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"],
      cycle: [{
          name: "b.js",
          dependencyTypes: ["local"]
        }, {
          name: "a.js",
          dependencyTypes: ["local"]
        }]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("a circular dependency whose rule lacks the circular flag stays a dependency violation", async () => {
  const ruleSet = {
    forbidden: [{
        name: "plain",
        severity: "warn",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: true,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "plain",
                severity: "warn"
              }],
            cycle: [{
                name: "b.js",
                dependencyTypes: ["local"]
              }, {
                name: "a.js",
                dependencyTypes: ["local"]
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "plain",
            severity: "warn",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "plain",
        severity: "warn"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("an invalid edge under a moreUnstable rule with instability on both ends becomes an instability violation", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-more-unstable",
        severity: "warn",
        from: {

        },
        to: {
          moreUnstable: true
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-more-unstable",
                severity: "warn"
              }],
            instability: 0.8
          }],
        orphan: false,
        rules: [],
        valid: false,
        instability: 0.2
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true,
        instability: 0.8
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-more-unstable",
            severity: "warn",
            from: {

            },
            to: {
              moreUnstable: true
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "instability",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "no-more-unstable",
        severity: "warn"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"],
      metrics: {
        from: {
          instability: 0.2
        },
        to: {
          instability: 0.8
        }
      }
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("a moreUnstable rule without instability metrics on the nodes stays a dependency violation", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-more-unstable",
        severity: "warn",
        from: {

        },
        to: {
          moreUnstable: true
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "no-more-unstable",
                severity: "warn"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-more-unstable",
            severity: "warn",
            from: {

            },
            to: {
              moreUnstable: true
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "no-more-unstable",
        severity: "warn"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 1, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("two identical violation records collapse to one", async () => {
  const ruleSet = {
    forbidden: [{
        name: "dup",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "dup",
                severity: "error"
              }, {
                name: "dup",
                severity: "error"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "dup",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "dup",
        severity: "error"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("violations are ordered by ascending severity rank", async () => {
  const ruleSet = {
    forbidden: [{
        name: "z-info",
        severity: "info",
        from: {

        },
        to: {
          path: "b"
        }
      }, {
        name: "a-error",
        severity: "error",
        from: {

        },
        to: {
          path: "c"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "z-info",
                severity: "info"
              }]
          }, {
            resolved: "c.js",
            module: "c.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "a-error",
                severity: "error"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }, {
        source: "c.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 3,
      totalDependenciesCruised: 2,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "z-info",
            severity: "info",
            from: {

            },
            to: {
              path: "b"
            }
          }, {
            name: "a-error",
            severity: "error",
            from: {

            },
            to: {
              path: "c"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "c.js",
      rule: {
        name: "a-error",
        severity: "error"
      },
      unresolvedTo: "c.js",
      dependencyTypes: ["local"]
    }, {
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "z-info",
        severity: "info"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 0, 1, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("violations of equal severity are ordered by rule name", async () => {
  const ruleSet = {
    forbidden: [{
        name: "b-rule",
        severity: "warn",
        from: {

        },
        to: {
          path: "b"
        }
      }, {
        name: "a-rule",
        severity: "warn",
        from: {

        },
        to: {
          path: "c"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "m.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "b-rule",
                severity: "warn"
              }]
          }, {
            resolved: "c.js",
            module: "c.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "a-rule",
                severity: "warn"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }, {
        source: "c.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 3,
      totalDependenciesCruised: 2,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "b-rule",
            severity: "warn",
            from: {

            },
            to: {
              path: "b"
            }
          }, {
            name: "a-rule",
            severity: "warn",
            from: {

            },
            to: {
              path: "c"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "m.js",
      to: "c.js",
      rule: {
        name: "a-rule",
        severity: "warn"
      },
      unresolvedTo: "c.js",
      dependencyTypes: ["local"]
    }, {
      type: "dependency",
      from: "m.js",
      to: "b.js",
      rule: {
        name: "b-rule",
        severity: "warn"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 2, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("the four severity counts tally the violations and sum to the list length", async () => {
  const ruleSet = {
    forbidden: [{
        name: "e",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }, {
        name: "w",
        severity: "warn",
        from: {

        },
        to: {
          path: "c"
        }
      }, {
        name: "i",
        severity: "info",
        from: {

        },
        to: {
          path: "d"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "e",
                severity: "error"
              }]
          }, {
            resolved: "c.js",
            module: "c.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "w",
                severity: "warn"
              }]
          }, {
            resolved: "d.js",
            module: "d.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "i",
                severity: "info"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }, {
        source: "c.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }, {
        source: "d.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 4,
      totalDependenciesCruised: 3,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "e",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }, {
            name: "w",
            severity: "warn",
            from: {

            },
            to: {
              path: "c"
            }
          }, {
            name: "i",
            severity: "info",
            from: {

            },
            to: {
              path: "d"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "e",
        severity: "error"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }, {
      type: "dependency",
      from: "a.js",
      to: "c.js",
      rule: {
        name: "w",
        severity: "warn"
      },
      unresolvedTo: "c.js",
      dependencyTypes: ["local"]
    }, {
      type: "dependency",
      from: "a.js",
      to: "d.js",
      rule: {
        name: "i",
        severity: "info"
      },
      unresolvedTo: "d.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([1, 1, 1, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("an ignore-severity violation counts under ignore and not under error", async () => {
  const ruleSet = {
    forbidden: [{
        name: "shh",
        severity: "ignore",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: false,
            rules: [{
                name: "shh",
                severity: "ignore"
              }]
          }],
        orphan: false,
        rules: [],
        valid: false
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "shh",
            severity: "ignore",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([{
      type: "dependency",
      from: "a.js",
      to: "b.js",
      rule: {
        name: "shh",
        severity: "ignore"
      },
      unresolvedTo: "b.js",
      dependencyTypes: ["local"]
    }]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 0, 0, 1]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("a clean graph reports zero on every severity count", async () => {
  const ruleSet = {
    forbidden: [{
        name: "no-b",
        severity: "error",
        from: {

        },
        to: {
          path: "b"
        }
      }],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [{
            resolved: "b.js",
            module: "b.js",
            moduleSystem: "es6",
            dynamic: false,
            exoticallyRequired: false,
            matchesDoNotFollow: false,
            coreModule: false,
            followable: true,
            couldNotResolve: false,
            circular: false,
            dependencyTypes: ["local"],
            valid: true,
            rules: []
          }],
        orphan: false,
        rules: [],
        valid: true
      }, {
        source: "b.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 2,
      totalDependenciesCruised: 1,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [{
            name: "no-b",
            severity: "error",
            from: {

            },
            to: {
              path: "b"
            }
          }],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
});

// Verifies: 
test("the environment block is carried through unchanged", async () => {
  const ruleSet = {
    forbidden: [],
    allowed: [],
    required: []
  };
  const input = {
    modules: [{
        source: "a.js",
        dependencies: [],
        orphan: false,
        rules: [],
        valid: true
      }],
    summary: {
      violations: [],
      error: 0,
      warn: 0,
      info: 0,
      ignore: 0,
      totalCruised: 1,
      totalDependenciesCruised: 0,
      optionsUsed: {
        args: "",
        outputType: "json"
      },
      ruleSetUsed: {
        forbidden: [],
        allowed: [],
        required: []
      },
      environment: {
        version: "18.2.0",
        nodeVersionSupported: "^42",
        nodeVersionFound: "v42.0.0",
        osVersionFound: "riscv pinecil@1.2.3",
        transpilersFound: [],
        extensionsFound: []
      }
    }
  };
  const out = await format(input, { outputType: 'json', ruleSet });
  const summary = JSON.parse(out.output).summary;

  expect(outline(summary.violations)).toEqual([]);
  expect([summary.error, summary.warn, summary.info, summary.ignore]).toEqual([0, 0, 0, 0]);
  expect(out.exitCode).toBe(0);
  expect(summary.environment).toEqual(input.summary.environment);
});
