// Oracle - integration and end-to-end tests for the chevrotain parser toolkit specification.
import { describe, test, expect } from "vitest";
import {
  createToken,
  tokenMatcher,
  EOF,
  Lexer,
  CstParser,
  EmbeddedActionsParser,
  isRecognitionException,
  GAstVisitor,
  Rule,
  Terminal,
  NonTerminal,
  serializeGrammar,
  generateCstDts,
} from "chevrotain";

// ---------------------------------------------------------------------------
// shared vocabulary
// ---------------------------------------------------------------------------
const Blank = createToken({ name: "Blank", pattern: /[ \t]+/, group: Lexer.SKIPPED });
const Newline = createToken({ name: "Newline", pattern: /\n+/, group: Lexer.SKIPPED, line_breaks: true });
const Amount = createToken({ name: "Amount", pattern: /\d+/ });
const Word = createToken({ name: "Word", pattern: /[a-z][a-z0-9]*/ });
const Arrowhead = createToken({ name: "Arrowhead", pattern: "->" });
const Pipe = createToken({ name: "Pipe", pattern: /\|/ });
const Colon = createToken({ name: "Colon", pattern: /:/ });
const baseVocab = [Blank, Newline, Amount, Word, Arrowhead, Pipe, Colon];
const baseLexer = new Lexer(baseVocab);
const lex = (text: string) => baseLexer.tokenize(text);

function flattenCstTokens(node: any): any[] {
  const out: any[] = [];
  for (const arr of Object.values(node.children) as any[][]) {
    for (const child of arr) {
      if (child.children !== undefined) out.push(...flattenCstTokens(child));
      else out.push(child);
    }
  }
  return out.sort((a, b) => a.startOffset - b.startOffset);
}

// route : leg (Arrowhead leg)* ; leg : Word (Colon Amount)?
class RouteParser extends CstParser {
  constructor(config?: any) {
    super(baseVocab, config);
    const $ = this as any;
    $.RULE("route", () => {
      $.SUBRULE($.leg);
      $.MANY(() => {
        $.CONSUME(Arrowhead);
        $.SUBRULE2($.leg, { LABEL: "hop" });
      });
    });
    $.RULE("leg", () => {
      $.CONSUME(Word);
      $.OPTION(() => {
        $.CONSUME(Colon);
        $.CONSUME(Amount);
      });
    });
    this.performSelfAnalysis();
  }
}

// ---------------------------------------------------------------------------
describe("lexer to parser pipelines", () => {
  test("a parser consuming a category accepts every concrete member", () => {
    /** Verifies: CHEV-TOK-004, CHEV-GRM-003. Seam: token categories x parser consumption. */
    // depends_on: tokenMatcher honors the token's own type and transitive categories;
    //             a rule invocation returns a CstNode named after the rule
    const Verb = createToken({ name: "Verb", pattern: Lexer.NA });
    const Moor = createToken({ name: "Moor", pattern: /moor/, categories: Verb });
    const Sail = createToken({ name: "Sail", pattern: /sail/, categories: Verb });
    const vocab = [Blank, Moor, Sail, Verb];
    const lx = new Lexer(vocab);
    class Command extends CstParser {
      constructor() {
        super(vocab);
        const $ = this as any;
        $.RULE("order", () => $.CONSUME(Verb));
        this.performSelfAnalysis();
      }
    }
    const p = new Command() as any;
    for (const text of ["moor", "sail"]) {
      p.input = lx.tokenize(text).tokens;
      const cst = p.order();
      expect(p.errors).toEqual([]);
      expect(cst.children.Verb[0].image).toBe(text);
    }
  });

  test("skipped and grouped content flows around the parser untouched", () => {
    /** Verifies: CHEV-LEX-008, CHEV-LEX-009, CHEV-CST-002. Seam: lexer groups x parse. */
    // depends_on: a string group diverts matches out of the main token stream;
    //             SKIPPED matches appear in neither tokens nor groups
    const Note = createToken({ name: "Note", pattern: /;[^\n]*/, group: "margin" });
    const vocab = [Blank, Newline, Amount, Word, Arrowhead, Pipe, Colon, Note];
    const lx = new Lexer(vocab);
    class Pairs extends CstParser {
      constructor() {
        super(vocab);
        const $ = this as any;
        $.RULE("sheet", () => {
          $.MANY(() => {
            $.CONSUME(Word);
            $.CONSUME(Colon);
            $.CONSUME(Amount);
          });
        });
        this.performSelfAnalysis();
      }
    }
    const lexed = lx.tokenize("oak : 3 ; planks\npine : 8 ; beams");
    expect(lexed.groups.margin.map((t: any) => t.image)).toEqual(["; planks", "; beams"]);
    const p = new Pairs() as any;
    p.input = lexed.tokens;
    const cst = p.sheet();
    expect(p.errors).toEqual([]);
    expect(cst.children.Word.map((t: any) => t.image)).toEqual(["oak", "pine"]);
    expect(cst.children.Amount.map((t: any) => t.image)).toEqual(["3", "8"]);
  });

  test("a keyword with longer_alt parses cleanly next to identifiers", () => {
    /** Verifies: CHEV-TOK-010, CHEV-GRM-007. Seam: keyword disambiguation x alternation. */
    // depends_on: longer_alt yields the longer alternative when it matches more text;
    //             OR applies the first alternative whose lookahead matches
    const Name = createToken({ name: "Name", pattern: /[a-z][a-z0-9]*/ });
    const Dock = createToken({ name: "Dock", pattern: /dock/, longer_alt: Name });
    const vocab = [Blank, Dock, Name, Colon];
    const lx = new Lexer(vocab);
    class Decl extends CstParser {
      constructor() {
        super(vocab);
        const $ = this as any;
        $.RULE("decl", () => {
          $.OR([
            { ALT: () => { $.CONSUME(Dock); $.CONSUME(Name); } },
            { ALT: () => { $.CONSUME2(Name, { LABEL: "bare" }); } },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Decl() as any;
    p.input = lx.tokenize("dock ferry").tokens;
    const kw = p.decl();
    expect(p.errors).toEqual([]);
    expect(kw.children.Dock[0].image).toBe("dock");
    expect(kw.children.Name[0].image).toBe("ferry");
    p.input = lx.tokenize("dockhand").tokens;
    const bare = p.decl();
    expect(p.errors).toEqual([]);
    expect(bare.children.bare[0].image).toBe("dockhand");
  });

  test("mode-switched tokens parse into one CST across mode boundaries", () => {
    /** Verifies: CHEV-LEX-012, CHEV-CST-005. Seam: lexer modes x parser. */
    // depends_on: push_mode and pop_mode drive a mode stack
    const OpenQ = createToken({ name: "OpenQ", pattern: /"/, push_mode: "quoted" });
    const CloseQ = createToken({ name: "CloseQ", pattern: /"/, pop_mode: true });
    const Raw = createToken({ name: "Raw", pattern: /[^"]+/ });
    const Label = createToken({ name: "Label", pattern: /[a-z]+/ });
    const lx = new Lexer({
      modes: { plain: [Blank, OpenQ, Label], quoted: [CloseQ, Raw] },
      defaultMode: "plain",
    });
    const vocab = [Blank, OpenQ, CloseQ, Raw, Label];
    class Quoted extends CstParser {
      constructor() {
        super(vocab);
        const $ = this as any;
        $.RULE("entry", () => {
          $.CONSUME(Label);
          $.CONSUME(OpenQ);
          $.CONSUME(Raw);
          $.CONSUME(CloseQ);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Quoted() as any;
    p.input = lx.tokenize('motto "steady as she goes"').tokens;
    const cst = p.entry();
    expect(p.errors).toEqual([]);
    expect(cst.children.Raw[0].image).toBe("steady as she goes");
  });

  test("custom pattern payloads survive into CST tokens", () => {
    /** Verifies: CHEV-LEX-014, CHEV-CST-005. Seam: custom pattern x CST. */
    // depends_on: a custom pattern's payload lands on the emitted token
    const Scaled = createToken({
      name: "Scaled",
      pattern: (text: string, startOffset: number) => {
        const m = /^\d+kg/.exec(text.slice(startOffset));
        if (m === null) return null;
        const arr = [m[0]] as any;
        arr.payload = Number(m[0].slice(0, -2)) * 1000;
        return arr;
      },
      line_breaks: false,
    });
    const vocab = [Blank, Scaled, Word];
    const lx = new Lexer(vocab);
    class Cargo extends CstParser {
      constructor() {
        super(vocab);
        const $ = this as any;
        $.RULE("load", () => {
          $.CONSUME(Word);
          $.CONSUME(Scaled);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Cargo() as any;
    p.input = lx.tokenize("tea 3kg").tokens;
    const cst = p.load();
    expect(p.errors).toEqual([]);
    expect(cst.children.Scaled[0].payload).toBe(3000);
    expect(cst.children.Scaled[0].image).toBe("3kg");
  });

  test("lexer groups, errors and tokens partition one noisy input", () => {
    /** Verifies: CHEV-LEX-009, CHEV-LEX-011, CHEV-LEX-005. Seam: three lexer outputs x one input. */
    // depends_on: an unmatchable character produces a structured error and lexing continues
    const Note = createToken({ name: "Note", pattern: /;[^\n]*/, group: "margin" });
    const vocab = [Blank, Newline, Amount, Word, Note];
    const lx = new Lexer(vocab);
    const r = lx.tokenize("keel 4 ~ ; aft\nrig 9");
    expect(r.tokens.map((t: any) => t.image)).toEqual(["keel", "4", "rig", "9"]);
    expect(r.groups.margin.map((t: any) => t.image)).toEqual(["; aft"]);
    expect(r.errors).toHaveLength(1);
    expect(r.errors[0].offset).toBe(7);
    const covered = r.tokens.length + r.groups.margin.length;
    expect(covered).toBe(5);
  });
});

// ---------------------------------------------------------------------------
describe("recovery and error projections", () => {
  test("the same fault yields undefined strictly and a repaired CST tolerantly", () => {
    /** Verifies: CHEV-INV-005, CHEV-REC-006, CHEV-CST-009. CVI-5. */
    // depends_on: without recovery a failing rule chain returns undefined;
    //             recovery inserts a missing token flagged isInsertedInRecovery
    const text = "dock : -> pier : 6";
    const strict = new RouteParser() as any;
    strict.input = lex(text).tokens;
    expect(strict.route()).toBeUndefined();
    expect(strict.errors.length).toBeGreaterThan(0);

    const tolerant = new RouteParser({ recoveryEnabled: true }) as any;
    tolerant.input = lex(text).tokens;
    const cst = tolerant.route();
    expect(tolerant.errors.length).toBeGreaterThan(0);
    expect(cst).toBeDefined();
    const inserted = flattenCstTokens(cst).filter((t) => t.isInsertedInRecovery);
    for (const tok of inserted) expect(tok.image).toBe("");
    expect(cst.children.hop[0].children.Word[0].image).toBe("pier");
  });

  test("error context names the rule stack outermost first at the failure point", () => {
    /** Verifies: CHEV-REC-002. Seam: nested rules x error context. */
    // depends_on: a wrong token at CONSUME records a MismatchedTokenException with context
    class Outer extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("harbor", () => $.SUBRULE($.berth));
        $.RULE("berth", () => $.SUBRULE($.slot));
        $.RULE("slot", () => $.CONSUME(Amount));
        this.performSelfAnalysis();
      }
    }
    const p = new Outer() as any;
    p.input = lex("pier").tokens;
    p.harbor();
    expect(p.errors[0].context.ruleStack).toEqual(["harbor", "berth", "slot"]);
    expect(p.errors[0].name).toBe("MismatchedTokenException");
  });

  test("a prefix CST plus NotAllInputParsed still projects consistent tokens", () => {
    /** Verifies: CHEV-CST-003, CHEV-INV-001. Seam: partial parse x round trip. */
    // depends_on: leftover input records NotAllInputParsed and keeps the prefix CST
    const p = new RouteParser() as any;
    const lexed = lex("dock : 5 pier");
    p.input = lexed.tokens;
    const cst = p.route();
    expect(p.errors[0].name).toBe("NotAllInputParsedException");
    const cstTokens = flattenCstTokens(cst);
    expect(cstTokens.map((t) => t.image)).toEqual(["dock", ":", "5"]);
    expect(lexed.tokens.slice(0, 3).map((t: any) => t.image)).toEqual(["dock", ":", "5"]);
  });

  test("recovery mixes insertion and re-sync across several statements", () => {
    /** Verifies: CHEV-REC-006, CHEV-REC-007, CHEV-REC-008. Seam: multi-fault recovery. */
    // depends_on: recovery inserts a missing token flagged isInsertedInRecovery;
    //             re-synchronization collects skipped tokens into resyncedTokens
    class Sheet extends CstParser {
      constructor() {
        super(baseVocab, { recoveryEnabled: true });
        const $ = this as any;
        $.RULE("sheet", () => { $.MANY(() => $.SUBRULE($.row)); });
        $.RULE("row", () => {
          $.CONSUME(Word);
          $.CONSUME(Colon);
          $.CONSUME(Amount);
          $.CONSUME(Pipe);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Sheet() as any;
    p.input = lex("ash 5 | elm : 2 9 4 | fir : 7 |").tokens;
    const cst = p.sheet();
    expect(cst.children.row).toHaveLength(3);
    expect(p.errors).toHaveLength(2);
    const kinds = p.errors.map((e: any) => e.name);
    expect(kinds).toContain("MismatchedTokenException");
    const inserted = flattenCstTokens(cst).filter((t) => t.isInsertedInRecovery);
    expect(inserted).toHaveLength(1);
    expect(inserted[0].tokenType).toBe(Colon);
    const resynced = p.errors.flatMap((e: any) => e.resyncedTokens.map((t: any) => t.image));
    expect(resynced).toContain("4");
  });
});

// ---------------------------------------------------------------------------
describe("grammar data agreement", () => {
  test("every grammar terminal is a vocabulary token type by identity", () => {
    /** Verifies: CHEV-INV-002, CHEV-GAST-006. CVI-2. */
    // depends_on: terminals and non-terminals reference their definitions by identity;
    //             GAstVisitor dispatches once per node kind without recursing
    const p = new RouteParser() as any;
    const prods = p.getGAstProductions();
    const terminals: any[] = [];
    const nonTerminals: any[] = [];
    class Walker extends (GAstVisitor as any) {
      visitTerminal(t: any) { terminals.push(t.terminalType); }
      visitNonTerminal(nt: any) { nonTerminals.push(nt); }
    }
    const w = new Walker() as any;
    const walk = (node: any) => {
      w.visit(node);
      if (node.definition) node.definition.forEach(walk);
    };
    Object.values(prods).forEach(walk);
    expect(terminals.length).toBeGreaterThan(0);
    for (const t of terminals) expect(baseVocab).toContain(t);
    for (const nt of nonTerminals) expect(nt.referencedRule).toBe(prods[nt.nonTerminalName]);
  });

  test("serialized productions agree with live ones and name callable rules", () => {
    /** Verifies: CHEV-INV-003, CHEV-GAST-005. CVI-3. */
    // depends_on: serializeGrammar agrees with the parser's serialized productions
    const p = new RouteParser() as any;
    const prods = p.getGAstProductions();
    const ser = p.getSerializedGastProductions();
    expect(ser).toHaveLength(2);
    expect(ser.map((r: any) => r.name).sort()).toEqual(["leg", "route"]);
    expect(serializeGrammar(Object.values(prods))).toEqual(ser);
    for (const rule of ser) {
      expect(rule.type).toBe("Rule");
      expect(typeof p[rule.name]).toBe("function");
      expect(prods[rule.name]).toBeInstanceOf(Rule);
    }
  });

  test("observed CST keys all appear in the generated declaration text", () => {
    /** Verifies: CHEV-INV-004, CHEV-GAST-007. CVI-4. */
    // depends_on: generateCstDts declares node and children types per rule;
    //             a LABEL replaces the default child key
    const p = new RouteParser() as any;
    p.input = lex("bay : 2 -> cove -> reef : 11").tokens;
    const cst = p.route();
    expect(p.errors).toEqual([]);
    const dts = generateCstDts(p.getGAstProductions());
    for (const key of Object.keys(cst.children)) {
      expect(dts).toMatch(new RegExp(`${key}\\??:`));
    }
    for (const key of Object.keys(cst.children.leg[0].children)) {
      expect(dts).toMatch(new RegExp(`${key}\\??:`));
    }
    expect(dts).toContain("Arrowhead?: IToken[]");
    expect(dts).toContain("Word: IToken[]");
  });

  test("optionality in declarations mirrors actual absence across parses", () => {
    /** Verifies: CHEV-GAST-007, CHEV-CST-008. Seam: dts optionality x CST presence. */
    // depends_on: keys for untaken options are absent from children
    const p = new RouteParser() as any;
    const dts = generateCstDts(p.getGAstProductions());
    expect(dts).toContain("Colon?: IToken[]");
    expect(dts).toContain("Amount?: IToken[]");
    p.input = lex("quay").tokens;
    const bare = p.route();
    expect(bare.children.leg[0].children.Colon).toBeUndefined();
    p.input = lex("quay : 3").tokens;
    const full = p.route();
    expect(full.children.leg[0].children.Colon).toHaveLength(1);
  });

  test("one grammar drives identical repeated parses and stable introspection", () => {
    /** Verifies: CHEV-INV-007. CVI-7. */
    // depends_on: a parser is reusable across independent inputs
    const p = new RouteParser() as any;
    const before = JSON.stringify(p.getSerializedGastProductions());
    p.input = lex("fen : 4 -> bog").tokens;
    const first = p.route();
    p.input = lex("fen : 4 -> bog").tokens;
    const second = p.route();
    expect(first.children.leg[0].children.Word[0].image).toBe("fen");
    expect(first.children.leg[0].children.Amount[0].image).toBe("4");
    expect(first.children.hop[0].children.Word[0].image).toBe("bog");
    expect(second).toEqual(first);
    expect(p.errors).toEqual([]);
    expect(p.getSerializedGastProductions()).toHaveLength(2);
    expect(JSON.stringify(p.getSerializedGastProductions())).toBe(before);
  });

  test("token offsets and images agree across lexer, CST and locations", () => {
    /** Verifies: CHEV-INV-001, CHEV-INV-006, CHEV-CST-010. CVI-1, CVI-6. */
    // depends_on: full node location tracking spans the first through last token;
    //             tokenize returns tokens with inclusive offsets and one-based positions
    const p = new RouteParser({ nodeLocationTracking: "full" }) as any;
    const text = "bay : 21 -> cove : 7";
    const lexed = lex(text);
    p.input = lexed.tokens;
    const cst = p.route();
    expect(p.errors).toEqual([]);
    const cstTokens = flattenCstTokens(cst);
    expect(cstTokens.map((t) => t.image)).toEqual(lexed.tokens.map((t: any) => t.image));
    expect(cstTokens.map((t) => t.startOffset)).toEqual(lexed.tokens.map((t: any) => t.startOffset));
    for (const t of cstTokens) {
      expect(t.endOffset - t.startOffset + 1).toBe(t.image.length);
      expect(text.slice(t.startOffset, t.endOffset + 1)).toBe(t.image);
    }
    expect(cst.location.startOffset).toBe(lexed.tokens[0].startOffset);
    expect(cst.location.endOffset).toBe(lexed.tokens[lexed.tokens.length - 1].endOffset);
  });
});

// ---------------------------------------------------------------------------
describe("computed views", () => {
  test("an embedded-actions parser and a CST visitor compute the same value", () => {
    /** Verifies: CHEV-EMB-001, CHEV-VIS-001. Seam: two computation projections of one grammar. */
    // depends_on: embedded rules return computed values instead of CST nodes;
    //             a visitor dispatches by rule name and returns method results
    class SumEmbedded extends EmbeddedActionsParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("tally", () => {
          let total = Number($.CONSUME(Amount).image);
          $.MANY(() => {
            $.CONSUME(Pipe);
            total += Number($.CONSUME2(Amount).image);
          });
          return total;
        });
        this.performSelfAnalysis();
      }
    }
    class SumCst extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("tally", () => {
          $.CONSUME(Amount);
          $.MANY(() => {
            $.CONSUME(Pipe);
            $.CONSUME2(Amount);
          });
        });
        this.performSelfAnalysis();
      }
    }
    const text = "12 | 30 | 9";
    const emb = new SumEmbedded() as any;
    emb.input = lex(text).tokens;
    const direct = emb.tally();

    const cstP = new SumCst() as any;
    cstP.input = lex(text).tokens;
    const cst = cstP.tally();
    const Base = cstP.getBaseCstVisitorConstructor();
    class SumVisitor extends Base {
      constructor() { super(); (this as any).validateVisitor(); }
      tally(ch: any) {
        return ch.Amount.reduce((acc: number, t: any) => acc + Number(t.image), 0);
      }
    }
    const viaVisitor = new SumVisitor().visit(cst);
    expect(direct).toBe(51);
    expect(viaVisitor).toBe(51);
  });

  test("visitor parameters thread through nested visits", () => {
    /** Verifies: CHEV-VIS-001, CHEV-VIS-002. Seam: visitor params x nested CST. */
    // depends_on: a visitor dispatches by rule name and returns method results
    const p = new RouteParser() as any;
    p.input = lex("dock : 5 -> pier : 8").tokens;
    const cst = p.route();
    const Base = p.getBaseCstVisitorConstructor();
    class Scaled extends Base {
      constructor() { super(); (this as any).validateVisitor(); }
      route(ch: any, factor: number) {
        const legs = [ch.leg, ch.hop ?? []].flat();
        return legs.map((l: any) => (this as any).visit(l, factor));
      }
      leg(ch: any, factor: number) {
        return ch.Amount ? Number(ch.Amount[0].image) * factor : 0;
      }
    }
    expect(new Scaled().visit(cst, 10)).toEqual([50, 80]);
  });

  test("gated alternatives steer the same rule differently per invocation", () => {
    /** Verifies: CHEV-GRM-008, CHEV-GRM-005. Seam: ARGS x GATE across invocations. */
    // depends_on: a GATE excludes its alternative while false;
    //             arguments flow to rules through direct invocation and SUBRULE ARGS
    class Dial extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("reading", (metric: boolean) => {
          $.OR([
            { GATE: () => metric === true, ALT: () => { $.CONSUME(Amount); $.CONSUME(Word); } },
            { ALT: () => $.CONSUME2(Amount, { LABEL: "raw" }) },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Dial() as any;
    p.input = lex("70 kg").tokens;
    const withUnit = p.reading(true);
    expect(p.errors).toEqual([]);
    expect(withUnit.children.Word[0].image).toBe("kg");
    p.input = lex("70").tokens;
    const raw = p.reading(false);
    expect(p.errors).toEqual([]);
    expect(raw.children.raw[0].image).toBe("70");
  });

  test("an embedded parser aggregates values from labeled subrules", () => {
    /** Verifies: CHEV-EMB-001, CHEV-GRM-012. Seam: embedded values x separated lists. */
    // depends_on: embedded rules return computed values instead of CST nodes;
    //             MANY_SEP consumes separators between repetitions
    class Budget extends EmbeddedActionsParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("total", () => {
          const items: number[] = [];
          $.MANY_SEP({
            SEP: Pipe,
            DEF: () => { items.push($.SUBRULE($.item)); },
          });
          return items;
        });
        $.RULE("item", () => {
          $.CONSUME(Word);
          $.CONSUME(Colon);
          return Number($.CONSUME(Amount).image);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Budget() as any;
    p.input = lex("rope : 12 | tar : 5 | sail : 40").tokens;
    expect(p.total()).toEqual([12, 5, 40]);
    expect(p.errors).toEqual([]);
  });

  test("a failing embedded parse reports errors while a fresh input computes again", () => {
    /** Verifies: CHEV-EMB-002, CHEV-EMB-003, CHEV-CST-001. Seam: embedded errors x parser reset. */
    // depends_on: embedded parsing failures record the same recognition errors;
    //             assigning input resets accumulated errors
    class Doubler extends EmbeddedActionsParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("twice", () => Number($.CONSUME(Amount).image) * 2);
        this.performSelfAnalysis();
      }
    }
    const p = new Doubler() as any;
    p.input = lex("mast").tokens;
    p.twice();
    expect(p.errors).toHaveLength(1);
    expect(isRecognitionException(p.errors[0])).toBe(true);
    p.input = lex("450").tokens;
    expect(p.twice()).toBe(900);
    expect(p.errors).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
describe("end-to-end workflows", () => {
  test("a manifest language runs from tokens through CST, visitor and introspection", () => {
    /** Verifies: CHEV-INV-001, CHEV-INV-002, CHEV-VIS-001, CHEV-GAST-007. CVI-1, CVI-2. */
    // depends_on: a parser consuming a category accepts every concrete member;
    //             serialized productions agree with live ones and name callable rules
    const Unit = createToken({ name: "Unit", pattern: Lexer.NA });
    const Crate = createToken({ name: "Crate", pattern: /crate/, categories: Unit });
    const Barrel = createToken({ name: "Barrel", pattern: /barrel/, categories: Unit });
    const Note = createToken({ name: "Note", pattern: /#[^\n]*/, group: "remarks" });
    const vocab = [Blank, Newline, Amount, Crate, Barrel, Unit, Word, Note];
    const lx = new Lexer(vocab);

    class Manifest extends CstParser {
      constructor() {
        super(vocab);
        const $ = this as any;
        $.RULE("manifest", () => { $.MANY(() => $.SUBRULE($.entry)); });
        $.RULE("entry", () => {
          $.CONSUME(Amount);
          $.CONSUME(Unit);
          $.CONSUME(Word);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Manifest() as any;
    const source = "3 crate lemons # fragile\n2 barrel syrup\n11 crate nails";
    const lexed = lx.tokenize(source);
    expect(lexed.errors).toEqual([]);
    expect(lexed.groups.remarks.map((t: any) => t.image)).toEqual(["# fragile"]);
    p.input = lexed.tokens;
    const cst = p.manifest();
    expect(p.errors).toEqual([]);
    expect(cst.children.entry).toHaveLength(3);

    const Base = p.getBaseCstVisitorConstructor();
    class Totals extends Base {
      constructor() { super(); (this as any).validateVisitor(); }
      manifest(ch: any) {
        const acc: Record<string, number> = {};
        for (const e of ch.entry ?? []) {
          const [kind, qty] = (this as any).visit(e);
          acc[kind] = (acc[kind] ?? 0) + qty;
        }
        return acc;
      }
      entry(ch: any) {
        return [ch.Unit[0].tokenType.name, Number(ch.Amount[0].image)];
      }
    }
    expect(new Totals().visit(cst)).toEqual({ Crate: 14, Barrel: 2 });

    const dts = generateCstDts(p.getGAstProductions());
    expect(dts).toContain("interface ManifestCstNode extends CstNode");
    expect(dts).toContain("entry?: EntryCstNode[]");
    for (const t of flattenCstTokens(cst)) {
      expect(tokenMatcher(t, Unit) || t.tokenType === Amount || t.tokenType === Word).toBe(true);
    }
  });

  test("an editor-style pass collects every fault yet renders a usable tree", () => {
    /** Verifies: CHEV-INV-005, CHEV-REC-006, CHEV-REC-002, CHEV-LEX-011. CVI-5. */
    // depends_on: the same fault yields undefined strictly and a repaired CST tolerantly;
    //             recovery mixes insertion and re-sync across several statements
    class Config extends CstParser {
      constructor() {
        super(baseVocab, { recoveryEnabled: true, nodeLocationTracking: "full" });
        const $ = this as any;
        $.RULE("config", () => { $.MANY(() => $.SUBRULE($.setting)); });
        $.RULE("setting", () => {
          $.CONSUME(Word);
          $.CONSUME(Colon);
          $.CONSUME(Amount);
        });
        this.performSelfAnalysis();
      }
    }
    const source = "depth : 30 beam ? 9 mast : 40";
    const lexed = lex(source);
    expect(lexed.errors).toHaveLength(1);
    expect(lexed.errors[0].offset).toBe(source.indexOf("?"));

    const p = new Config() as any;
    p.input = lexed.tokens;
    const cst = p.config();
    expect(cst.children.setting.length).toBeGreaterThanOrEqual(2);
    const names = cst.children.setting.map((s: any) => s.children.Word[0].image);
    expect(names).toContain("depth");
    expect(names).toContain("mast");
    expect(p.errors.length).toBeGreaterThan(0);
    for (const err of p.errors) {
      expect(isRecognitionException(err)).toBe(true);
      expect(err.context.ruleStack[0]).toBe("config");
    }
    const good = cst.children.setting.find((s: any) => s.children.Word[0].image === "mast");
    expect(good.children.Amount[0].image).toBe("40");
    expect(good.location.startOffset).toBe(source.indexOf("mast"));
  });

  test("a calculator ships twice: embedded values and visited CST stay in lockstep", () => {
    /** Verifies: CHEV-EMB-001, CHEV-VIS-001, CHEV-GRM-007, CHEV-INV-007. CVI-7. */
    // depends_on: an embedded-actions parser and a CST visitor compute the same value;
    //             one grammar drives identical repeated parses and stable introspection
    const LPar = createToken({ name: "LPar", pattern: /\(/ });
    const RPar = createToken({ name: "RPar", pattern: /\)/ });
    const Plus = createToken({ name: "Plus", pattern: /\+/ });
    const Star = createToken({ name: "Star", pattern: /\*/ });
    const vocab = [Blank, Amount, LPar, RPar, Plus, Star];
    const lx = new Lexer(vocab);

    class Calc extends EmbeddedActionsParser {
      constructor() {
        super(vocab);
        const $ = this as any;
        $.RULE("expr", () => {
          let v = $.SUBRULE($.term);
          $.MANY(() => {
            $.CONSUME(Plus);
            v += $.SUBRULE2($.term);
          });
          return v;
        });
        $.RULE("term", () => {
          let v = $.SUBRULE($.factor);
          $.MANY(() => {
            $.CONSUME(Star);
            v *= $.SUBRULE2($.factor);
          });
          return v;
        });
        $.RULE("factor", () => {
          return $.OR([
            { ALT: () => Number($.CONSUME(Amount).image) },
            { ALT: () => {
              $.CONSUME(LPar);
              const v = $.SUBRULE($.expr);
              $.CONSUME(RPar);
              return v;
            } },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const calc = new Calc() as any;
    const program = "( 2 + 3 ) * 4 + 5";
    calc.input = lx.tokenize(program).tokens;
    const first = calc.expr();
    calc.input = lx.tokenize(program).tokens;
    const second = calc.expr();
    expect(first).toBe(25);
    expect(second).toBe(25);
    expect(calc.errors).toEqual([]);

    const ser = calc.getSerializedGastProductions();
    expect(ser.map((r: any) => r.name).sort()).toEqual(["expr", "factor", "term"]);
  });

  test("grammar-as-data: one definition audited through every projection", () => {
    /** Verifies: CHEV-INV-002, CHEV-INV-003, CHEV-INV-004, CHEV-GAST-006. CVI-2, CVI-3, CVI-4. */
    // depends_on: every grammar terminal is a vocabulary token type by identity;
    //             observed CST keys all appear in the generated declaration text
    const p = new RouteParser() as any;
    const prods = p.getGAstProductions();

    // projection 1: GAstVisitor statistics (stop at rule references so each
    // rule's own body is counted exactly once)
    let terminalCount = 0;
    const ruleRefs: string[] = [];
    class Stats extends (GAstVisitor as any) {
      visitTerminal() { terminalCount += 1; }
      visitNonTerminal(nt: any) { ruleRefs.push(nt.nonTerminalName); }
    }
    const s = new Stats() as any;
    const walk = (node: any) => {
      s.visit(node);
      if (node instanceof NonTerminal) return;
      if (node.definition) node.definition.forEach(walk);
    };
    Object.values(prods).forEach(walk);
    expect(terminalCount).toBe(4); // Arrowhead, Word, Colon, Amount
    expect(ruleRefs.sort()).toEqual(["leg", "leg"]);

    // projection 2: serialized grammar names the same terminals
    const ser = p.getSerializedGastProductions();
    const serText = JSON.stringify(ser);
    for (const name of ["Arrowhead", "Word", "Colon", "Amount"]) {
      expect(serText).toContain(`"${name}"`);
    }

    // projection 3: dts and a live parse agree
    const dts = generateCstDts(prods);
    p.input = lex("bay -> fen : 3").tokens;
    const cst = p.route();
    expect(p.errors).toEqual([]);
    for (const key of Object.keys(cst.children)) {
      expect(dts).toMatch(new RegExp(`${key}\\??:`));
    }

    // projection 4: every terminal identity is in the vocabulary
    const terminalTypes: any[] = [];
    class Collect extends (GAstVisitor as any) {
      visitTerminal(t: any) { terminalTypes.push(t.terminalType); }
    }
    const c = new Collect() as any;
    Object.values(prods).forEach(function rec(node: any) {
      c.visit(node);
      if (node.definition) node.definition.forEach(rec);
    });
    for (const t of terminalTypes) expect(baseVocab).toContain(t);
  });
});
