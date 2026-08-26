// Oracle - atomic tests for the chevrotain parser toolkit specification.
import { describe, test, expect } from "vitest";
import {
  createToken,
  createTokenInstance,
  tokenMatcher,
  tokenLabel,
  tokenName,
  EOF,
  Lexer,
  CstParser,
  EmbeddedActionsParser,
  EMPTY_ALT,
  isRecognitionException,
  GAstVisitor,
  Rule,
  Terminal,
  NonTerminal,
  Option,
  Alternation,
  Alternative,
  Repetition,
  RepetitionMandatory,
  RepetitionWithSeparator,
  serializeGrammar,
  serializeProduction,
  generateCstDts,
} from "chevrotain";

// ---------------------------------------------------------------------------
// shared vocabulary (values distinct from any upstream example)
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

function lex(text: string) {
  return baseLexer.tokenize(text);
}

// ---------------------------------------------------------------------------
describe("token definitions", () => {
  test("createToken returns a token type usable by a lexer", () => {
    /** Verifies: CHEV-TOK-001 */
    const Pledge = createToken({ name: "Pledge", pattern: /pledge/ });
    expect(Pledge.name).toBe("Pledge");
    expect(Pledge.PATTERN).toEqual(/pledge/);
    const lx = new Lexer([Pledge]);
    const r = lx.tokenize("pledge");
    expect(r.errors).toEqual([]);
    expect(r.tokens).toHaveLength(1);
    expect(r.tokens[0].image).toBe("pledge");
    expect(r.tokens[0].tokenType).toBe(Pledge);
  });

  test("a literal string pattern matches verbatim text", () => {
    /** Verifies: CHEV-TOK-002 */
    const r = lex("7 -> 9");
    expect(r.errors).toEqual([]);
    expect(r.tokens.map((t) => t.tokenType.name)).toEqual(["Amount", "Arrowhead", "Amount"]);
    expect(r.tokens[1].image).toBe("->");
  });

  test("tokenMatcher honors the token's own type and transitive categories", () => {
    /** Verifies: CHEV-TOK-004 */
    const Signal = createToken({ name: "Signal", pattern: Lexer.NA });
    const Alert = createToken({ name: "Alert", pattern: Lexer.NA, categories: Signal });
    const Siren = createToken({ name: "Siren", pattern: /wail/, categories: Alert });
    const lx = new Lexer([Blank, Siren]);
    const tok = lx.tokenize("wail").tokens[0];
    expect(tokenMatcher(tok, Siren)).toBe(true);
    expect(tokenMatcher(tok, Alert)).toBe(true);
    expect(tokenMatcher(tok, Signal)).toBe(true);
    expect(tokenMatcher(tok, Amount)).toBe(false);
  });

  test("a token type in several categories matches each of them", () => {
    /** Verifies: CHEV-TOK-003, CHEV-TOK-004 */
    const Fauna = createToken({ name: "Fauna", pattern: Lexer.NA });
    const Nocturnal = createToken({ name: "Nocturnal", pattern: Lexer.NA });
    const Owl = createToken({ name: "Owl", pattern: /hoot/, categories: [Fauna, Nocturnal] });
    const lx = new Lexer([Blank, Owl]);
    const tok = lx.tokenize("hoot").tokens[0];
    expect(tokenMatcher(tok, Fauna)).toBe(true);
    expect(tokenMatcher(tok, Nocturnal)).toBe(true);
  });

  test("a Lexer.NA token type is never produced from text", () => {
    /** Verifies: CHEV-TOK-005 */
    const Abstract = createToken({ name: "Abstract", pattern: Lexer.NA });
    const Concrete = createToken({ name: "Concrete", pattern: /ember/, categories: Abstract });
    const lx = new Lexer([Blank, Concrete, Abstract]);
    const r = lx.tokenize("ember ember");
    expect(r.errors).toEqual([]);
    expect(r.tokens).toHaveLength(2);
    for (const t of r.tokens) expect(t.tokenType).toBe(Concrete);
  });

  test("tokenLabel falls back to the name and tokenName returns the name", () => {
    /** Verifies: CHEV-TOK-006 */
    const Tagged = createToken({ name: "Tagged", pattern: /t/, label: "fancy-tag" });
    expect(tokenLabel(Tagged)).toBe("fancy-tag");
    expect(tokenLabel(Amount)).toBe("Amount");
    expect(tokenName(Tagged)).toBe("Tagged");
  });

  test("createTokenInstance builds a token with the eight explicit fields", () => {
    /** Verifies: CHEV-TOK-007 */
    const tok = createTokenInstance(Amount, "417", 10, 12, 2, 2, 4, 6);
    expect(tok.image).toBe("417");
    expect(tok.startOffset).toBe(10);
    expect(tok.endOffset).toBe(12);
    expect(tok.startLine).toBe(2);
    expect(tok.endLine).toBe(2);
    expect(tok.startColumn).toBe(4);
    expect(tok.endColumn).toBe(6);
    expect(tok.tokenType).toBe(Amount);
    expect(tokenMatcher(tok, Amount)).toBe(true);
  });

  test("earlier token types win at the same offset regardless of match length", () => {
    /** Verifies: CHEV-TOK-009, CHEV-TOK-011 */
    const Van = createToken({ name: "Van", pattern: /van/ });
    const Name = createToken({ name: "Name", pattern: /[a-z]+/ });
    const lx = new Lexer([Blank, Van, Name]);
    const r = lx.tokenize("van vanguard");
    expect(r.tokens.map((t) => [t.image, t.tokenType.name])).toEqual([
      ["van", "Van"],
      ["van", "Van"],
      ["guard", "Name"],
    ]);
  });

  test("longer_alt yields the longer alternative when it matches more text", () => {
    /** Verifies: CHEV-TOK-010 */
    const Name = createToken({ name: "Name", pattern: /[a-z]+/ });
    const Van = createToken({ name: "Van", pattern: /van/, longer_alt: Name });
    const lx = new Lexer([Blank, Van, Name]);
    const r = lx.tokenize("van vanguard");
    expect(r.tokens.map((t) => [t.image, t.tokenType.name])).toEqual([
      ["van", "Van"],
      ["vanguard", "Name"],
    ]);
  });

  test("an array of longer_alt candidates is honored", () => {
    /** Verifies: CHEV-TOK-010 */
    const Name = createToken({ name: "Name", pattern: /[a-z]+/ });
    const HexNum = createToken({ name: "HexNum", pattern: /0x[0-9a-f]+/ });
    const Naught = createToken({ name: "Naught", pattern: /0/, longer_alt: [HexNum, Name] });
    const lx = new Lexer([Blank, Naught, HexNum, Name]);
    const r = lx.tokenize("0 0x2f");
    expect(r.errors).toEqual([]);
    expect(r.tokens.map((t) => [t.image, t.tokenType.name])).toEqual([
      ["0", "Naught"],
      ["0x2f", "HexNum"],
    ]);
  });

  test("end-of-input recognition errors carry an EOF token with empty image", () => {
    /** Verifies: CHEV-TOK-008, CHEV-REC-003 */
    class NeedsTwo extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("duo", () => {
          $.CONSUME(Word);
          $.CONSUME(Amount);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new NeedsTwo() as any;
    p.input = lex("quay").tokens;
    p.duo();
    expect(p.errors).toHaveLength(1);
    expect(tokenMatcher(p.errors[0].token, EOF)).toBe(true);
    expect(p.errors[0].token.image).toBe("");
  });
});

// ---------------------------------------------------------------------------
describe("tokenization", () => {
  test("tokenize returns tokens with inclusive offsets and one-based positions", () => {
    /** Verifies: CHEV-LEX-005, CHEV-LEX-006 */
    const r = lex("38 : cove");
    expect(r.errors).toEqual([]);
    expect(Object.keys(r.groups)).toEqual([]);
    const [amt, colon, word] = r.tokens;
    expect(amt.image).toBe("38");
    expect(amt.startOffset).toBe(0);
    expect(amt.endOffset).toBe(1);
    expect(amt.startLine).toBe(1);
    expect(amt.startColumn).toBe(1);
    expect(amt.endColumn).toBe(2);
    expect(colon.startOffset).toBe(3);
    expect(word.image).toBe("cove");
    expect(word.startOffset).toBe(5);
    expect(word.endOffset).toBe(8);
    expect(word.tokenType).toBe(Word);
  });

  test("line and column advance across newlines under full tracking", () => {
    /** Verifies: CHEV-LEX-006 */
    const r = lex("4\n reef");
    const reef = r.tokens[1];
    expect(reef.startLine).toBe(2);
    expect(reef.startColumn).toBe(2);
    expect(reef.endLine).toBe(2);
    expect(reef.endColumn).toBe(5);
  });

  test("onlyStart tracking populates only the start fields", () => {
    /** Verifies: CHEV-LEX-002, CHEV-LEX-007 */
    const lx = new Lexer(baseVocab, { positionTracking: "onlyStart" });
    const t = lx.tokenize("451").tokens[0];
    expect(t.startLine).toBe(1);
    expect(t.startColumn).toBe(1);
    expect(t.startOffset).toBe(0);
    expect(t.endOffset).toBeUndefined();
    expect(t.endLine).toBeUndefined();
    expect(t.endColumn).toBeUndefined();
    expect(t.image).toBe("451");
  });

  test("onlyOffset tracking populates only startOffset among positions", () => {
    /** Verifies: CHEV-LEX-002, CHEV-LEX-007 */
    const lx = new Lexer(baseVocab, { positionTracking: "onlyOffset" });
    const t = lx.tokenize("867").tokens[0];
    expect(t.startLine).toBeUndefined();
    expect(t.startColumn).toBeUndefined();
    expect(t.endOffset).toBeUndefined();
    expect(t.startOffset).toBe(0);
    expect(t.image).toBe("867");
    expect(t.tokenType).toBe(Amount);
  });

  test("SKIPPED matches appear in neither tokens nor groups", () => {
    /** Verifies: CHEV-LEX-008 */
    const r = lex("9 | 4");
    expect(r.tokens.map((t) => t.image)).toEqual(["9", "|", "4"]);
    expect(Object.keys(r.groups)).toEqual([]);
  });

  test("a string group diverts matches out of the main token stream", () => {
    /** Verifies: CHEV-LEX-009 */
    const Note = createToken({ name: "Note", pattern: /;[^\n]*/, group: "margin" });
    const lx = new Lexer([Blank, Newline, Amount, Note]);
    const r = lx.tokenize("62 ; first\n81 ; second");
    expect(r.tokens.map((t) => t.image)).toEqual(["62", "81"]);
    expect(r.groups.margin.map((t) => t.image)).toEqual(["; first", "; second"]);
  });

  test("declared group keys are present even when nothing matched", () => {
    /** Verifies: CHEV-LEX-010 */
    const Note = createToken({ name: "Note", pattern: /;[^\n]*/, group: "margin" });
    const lx = new Lexer([Blank, Amount, Note]);
    const r = lx.tokenize("5");
    expect(r.groups.margin).toEqual([]);
  });

  test("an unmatchable character produces a structured error and lexing continues", () => {
    /** Verifies: CHEV-LEX-011 */
    const r = lex("31 ~ 42");
    expect(r.errors).toHaveLength(1);
    expect(r.errors[0].offset).toBe(3);
    expect(r.errors[0].line).toBe(1);
    expect(r.errors[0].column).toBe(4);
    expect(r.errors[0].length).toBe(1);
    expect(typeof r.errors[0].message).toBe("string");
    expect(r.tokens.map((t) => t.image)).toEqual(["31", "42"]);
  });

  test("consecutive unmatchable characters merge into one error with their length", () => {
    /** Verifies: CHEV-LEX-011 */
    const r = lex("8 ~~~ 6");
    expect(r.errors).toHaveLength(1);
    expect(r.errors[0].length).toBe(3);
    expect(r.tokens.map((t) => t.image)).toEqual(["8", "6"]);
  });

  test("push_mode and pop_mode drive a mode stack", () => {
    /** Verifies: CHEV-LEX-001, CHEV-LEX-012 */
    const Open = createToken({ name: "Open", pattern: /\[/, push_mode: "cargo" });
    const Close = createToken({ name: "Close", pattern: /\]/, pop_mode: true });
    const Outer = createToken({ name: "Outer", pattern: /[a-z]+/ });
    const InnerCaps = createToken({ name: "InnerCaps", pattern: /[A-Z]+/ });
    const lx = new Lexer({
      modes: { deck: [Blank, Open, Outer], cargo: [Blank, Close, InnerCaps] },
      defaultMode: "deck",
    });
    const r = lx.tokenize("bow [TEA] stern");
    expect(r.errors).toEqual([]);
    expect(r.tokens.map((t) => t.tokenType.name)).toEqual([
      "Outer",
      "Open",
      "InnerCaps",
      "Close",
      "Outer",
    ]);
  });

  test("a token type outside the active mode does not match", () => {
    /** Verifies: CHEV-LEX-012 */
    const Open = createToken({ name: "Open", pattern: /\[/, push_mode: "cargo" });
    const Close = createToken({ name: "Close", pattern: /\]/, pop_mode: true });
    const Outer = createToken({ name: "Outer", pattern: /[a-z]+/ });
    const InnerCaps = createToken({ name: "InnerCaps", pattern: /[A-Z]+/ });
    const lx = new Lexer({
      modes: { deck: [Blank, Open, Outer], cargo: [Blank, Close, InnerCaps] },
      defaultMode: "deck",
    });
    const r = lx.tokenize("TEA");
    expect(r.errors).toHaveLength(1);
    expect(r.tokens).toEqual([]);
  });

  test("tokenize accepts an initial mode name", () => {
    /** Verifies: CHEV-LEX-013 */
    const Open = createToken({ name: "Open", pattern: /\[/, push_mode: "cargo" });
    const Close = createToken({ name: "Close", pattern: /\]/, pop_mode: true });
    const Outer = createToken({ name: "Outer", pattern: /[a-z]+/ });
    const InnerCaps = createToken({ name: "InnerCaps", pattern: /[A-Z]+/ });
    const lx = new Lexer({
      modes: { deck: [Blank, Open, Outer], cargo: [Blank, Close, InnerCaps] },
      defaultMode: "deck",
    });
    const r = lx.tokenize("RUM", "cargo");
    expect(r.errors).toEqual([]);
    expect(r.tokens[0].tokenType.name).toBe("InnerCaps");
  });

  test("a custom pattern function matches text and returns null for no match", () => {
    /** Verifies: CHEV-LEX-014 */
    const Even = createToken({
      name: "Even",
      pattern: (text: string, startOffset: number) => {
        const m = /^\d+/.exec(text.slice(startOffset));
        if (m === null || Number(m[0]) % 2 !== 0) return null;
        return [m[0]] as any;
      },
      line_breaks: false,
    });
    const lx = new Lexer([Blank, Even, Word]);
    const good = lx.tokenize("44");
    expect(good.errors).toEqual([]);
    expect(good.tokens[0].image).toBe("44");
    const bad = lx.tokenize("43");
    expect(bad.errors).toHaveLength(1);
  });

  test("a custom pattern's payload lands on the emitted token", () => {
    /** Verifies: CHEV-LEX-014 */
    const Priced = createToken({
      name: "Priced",
      pattern: (text: string, startOffset: number) => {
        const m = /^\d+/.exec(text.slice(startOffset));
        if (m === null) return null;
        const arr = [m[0]] as any;
        arr.payload = Number(m[0]) * 3;
        return arr;
      },
      line_breaks: false,
    });
    const lx = new Lexer([Blank, Priced]);
    const r = lx.tokenize("14 5");
    expect(r.tokens.map((t: any) => t.payload)).toEqual([42, 15]);
  });

  test("a global-flag pattern makes the Lexer constructor throw", () => {
    /** Verifies: CHEV-LEX-003 */
    const Sloppy = createToken({ name: "Sloppy", pattern: /q/g });
    expect(() => new Lexer([Sloppy])).toThrow(Error);
    expect(() => new Lexer([Sloppy])).toThrow(/Sloppy/);
  });

  test("deferDefinitionErrorsHandling collects problems instead of throwing", () => {
    /** Verifies: CHEV-LEX-004 */
    const Sloppy = createToken({ name: "Sloppy", pattern: /q/g });
    const lx = new Lexer([Sloppy], { deferDefinitionErrorsHandling: true });
    expect(lx.lexerDefinitionErrors.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// small grammar used across the parsing tests:
//   route  : leg (Arrowhead leg)*
//   leg    : Word (Colon Amount)?
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

function parseRoute(text: string, config?: any) {
  const p = new RouteParser(config) as any;
  p.input = lex(text).tokens;
  const cst = p.route();
  return { p, cst };
}

describe("grammar definition and cst", () => {
  test("a rule invocation returns a CstNode named after the rule", () => {
    /** Verifies: CHEV-CST-002, CHEV-CST-005 */
    const { p, cst } = parseRoute("dock");
    expect(p.errors).toEqual([]);
    expect(cst.name).toBe("route");
    expect(cst.children.leg).toHaveLength(1);
    expect(cst.children.leg[0].name).toBe("leg");
    expect(cst.children.leg[0].children.Word[0].image).toBe("dock");
  });

  test("tokens key under their token type name and subrules under the rule name", () => {
    /** Verifies: CHEV-CST-005 */
    const { p, cst } = parseRoute("dock : 12");
    expect(p.errors).toEqual([]);
    const leg = cst.children.leg[0];
    expect(Object.keys(leg.children).sort()).toEqual(["Amount", "Colon", "Word"]);
    expect(leg.children.Amount[0].image).toBe("12");
  });

  test("a LABEL replaces the default child key", () => {
    /** Verifies: CHEV-CST-006 */
    const { p, cst } = parseRoute("dock -> pier");
    expect(p.errors).toEqual([]);
    expect(cst.children.leg).toHaveLength(1);
    expect(cst.children.hop).toHaveLength(1);
    expect(cst.children.hop[0].children.Word[0].image).toBe("pier");
  });

  test("repeated occurrences merge into one key in input order", () => {
    /** Verifies: CHEV-CST-007, CHEV-GRM-004 */
    class Pair extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("pair", () => {
          $.CONSUME(Amount);
          $.CONSUME(Pipe);
          $.CONSUME2(Amount);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Pair() as any;
    p.input = lex("3 | 88").tokens;
    const cst = p.pair();
    expect(cst.children.Amount.map((t: any) => t.image)).toEqual(["3", "88"]);
  });

  test("keys for untaken options are absent from children", () => {
    /** Verifies: CHEV-CST-008 */
    const { cst } = parseRoute("quay");
    const leg = cst.children.leg[0];
    expect(Object.keys(leg.children)).toEqual(["Word"]);
    expect(leg.children.Colon).toBeUndefined();
  });

  test("MANY parses zero and several repetitions", () => {
    /** Verifies: CHEV-GRM-011 */
    const zero = parseRoute("dock");
    expect(zero.cst.children.Arrowhead).toBeUndefined();
    const three = parseRoute("a -> b -> c -> d");
    expect(three.p.errors).toEqual([]);
    expect(three.cst.children.Arrowhead).toHaveLength(3);
    expect(three.cst.children.hop).toHaveLength(3);
  });

  test("MANY_SEP consumes separators between repetitions", () => {
    /** Verifies: CHEV-GRM-012 */
    class Roster extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("roster", () => {
          $.MANY_SEP({ SEP: Pipe, DEF: () => $.CONSUME(Word) });
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Roster() as any;
    p.input = lex("ash | birch | cedar").tokens;
    const cst = p.roster();
    expect(p.errors).toEqual([]);
    expect(cst.children.Word.map((t: any) => t.image)).toEqual(["ash", "birch", "cedar"]);
    expect(cst.children.Pipe).toHaveLength(2);
  });

  test("AT_LEAST_ONE_SEP accepts one element and rejects zero", () => {
    /** Verifies: CHEV-GRM-011, CHEV-GRM-012 */
    class Crew extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("crew", () => {
          $.AT_LEAST_ONE_SEP({ SEP: Pipe, DEF: () => $.CONSUME(Word) });
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Crew() as any;
    p.input = lex("solo").tokens;
    const one = p.crew();
    expect(p.errors).toEqual([]);
    expect(one.children.Word).toHaveLength(1);
    p.input = lex("77").tokens;
    p.crew();
    expect(p.errors).toHaveLength(1);
    expect(p.errors[0].name).toBe("EarlyExitException");
  });

  test("OR applies the first alternative whose lookahead matches", () => {
    /** Verifies: CHEV-GRM-007 */
    class Choice extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("pick", () => {
          $.OR([
            { ALT: () => $.CONSUME(Amount) },
            { ALT: () => $.CONSUME(Word) },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Choice() as any;
    p.input = lex("505").tokens;
    expect(p.pick().children.Amount[0].image).toBe("505");
    p.input = lex("mast").tokens;
    expect(p.pick().children.Word[0].image).toBe("mast");
    expect(p.errors).toEqual([]);
  });

  test("a GATE excludes its alternative while false", () => {
    /** Verifies: CHEV-GRM-008 */
    class Gated extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("entry", (open: boolean) => {
          $.OR([
            { GATE: () => open === true, ALT: () => $.CONSUME(Word) },
            { ALT: () => $.CONSUME(Amount) },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Gated() as any;
    p.input = lex("gate").tokens;
    p.entry(true);
    expect(p.errors).toEqual([]);
    p.input = lex("gate").tokens;
    p.entry(false);
    expect(p.errors).toHaveLength(1);
    expect(p.errors[0].name).toBe("NoViableAltException");
  });

  test("EMPTY_ALT supplies an always-applicable default branch", () => {
    /** Verifies: CHEV-GRM-009 */
    class Maybe extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("badge", () => {
          $.OR([
            { ALT: () => $.CONSUME(Word) },
            { ALT: EMPTY_ALT("none") },
          ]);
          $.CONSUME(Amount);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Maybe() as any;
    p.input = lex("28").tokens;
    const cst = p.badge();
    expect(p.errors).toEqual([]);
    expect(cst.children.Amount[0].image).toBe("28");
    expect(cst.children.Word).toBeUndefined();
  });

  test("the default lookahead distinguishes alternatives needing three tokens", () => {
    /** Verifies: CHEV-GRM-010 */
    class DeepLA extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("lane", () => {
          $.OR([
            { ALT: () => { $.CONSUME(Word); $.CONSUME(Pipe); $.CONSUME(Amount); } },
            { ALT: () => { $.CONSUME2(Word); $.CONSUME2(Pipe); $.CONSUME3(Word, { LABEL: "tail" }); } },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new DeepLA() as any;
    p.input = lex("cove | 7").tokens;
    const first = p.lane();
    expect(p.errors).toEqual([]);
    expect(first.children.Amount[0].image).toBe("7");
    p.input = lex("cove | reef").tokens;
    const second = p.lane();
    expect(p.errors).toEqual([]);
    expect(second.children.tail[0].image).toBe("reef");
  });

  test("arguments flow to rules through direct invocation and SUBRULE ARGS", () => {
    /** Verifies: CHEV-GRM-005, CHEV-GRM-006 */
    class ArgFlow extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("outer", () => {
          $.SUBRULE($.inner, { ARGS: [true] });
        });
        $.RULE("inner", (allowWord: boolean) => {
          $.OR([
            { GATE: () => allowWord === true, ALT: () => $.CONSUME(Word) },
            { ALT: () => $.CONSUME(Amount) },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new ArgFlow() as any;
    p.input = lex("keel").tokens;
    p.outer();
    expect(p.errors).toEqual([]);
    p.input = lex("keel").tokens;
    p.inner(false);
    expect(p.errors).toHaveLength(1);
  });

  test("assigning input resets accumulated errors", () => {
    /** Verifies: CHEV-CST-001 */
    const p = new RouteParser() as any;
    p.input = lex("55").tokens;
    p.route();
    expect(p.errors.length).toBeGreaterThan(0);
    p.input = lex("dock").tokens;
    expect(p.errors).toEqual([]);
    p.route();
    expect(p.errors).toEqual([]);
  });

  test("a parser is reusable across independent inputs", () => {
    /** Verifies: CHEV-CST-004 */
    const p = new RouteParser() as any;
    p.input = lex("dock : 4").tokens;
    const a = p.route();
    p.input = lex("pier").tokens;
    const b = p.route();
    expect(a.children.leg[0].children.Word[0].image).toBe("dock");
    expect(b.children.leg[0].children.Word[0].image).toBe("pier");
    expect(p.errors).toEqual([]);
  });

  test("full node location tracking spans the first through last token", () => {
    /** Verifies: CHEV-CST-010 */
    const { p, cst } = parseRoute("dock : 12", { nodeLocationTracking: "full" });
    expect(p.errors).toEqual([]);
    expect(cst.location).toEqual({
      startOffset: 0,
      startLine: 1,
      startColumn: 1,
      endOffset: 8,
      endLine: 1,
      endColumn: 9,
    });
    const plain = parseRoute("dock : 12");
    expect(plain.cst.location).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
describe("grammar validation", () => {
  test("a duplicate rule name fails self-analysis with an aggregate error", () => {
    /** Verifies: CHEV-VAL-001, CHEV-VAL-002 */
    class Dup extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("twice", () => $.CONSUME(Word));
        $.RULE("twice", () => $.CONSUME(Amount));
        this.performSelfAnalysis();
      }
    }
    expect(() => new Dup()).toThrow(/Parser Definition Errors detected/);
    expect(() => new Dup()).toThrow(/twice/);
  });

  test("left recursion fails self-analysis", () => {
    /** Verifies: CHEV-VAL-001, CHEV-VAL-003 */
    class Looped extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("spiral", () => {
          $.SUBRULE($.spiral);
          $.CONSUME(Word);
        });
        this.performSelfAnalysis();
      }
    }
    expect(() => new Looped()).toThrow(/Parser Definition Errors detected/);
    expect(() => new Looped()).toThrow(/spiral/);
  });

  test("alternatives sharing a full lookahead prefix fail as ambiguous", () => {
    /** Verifies: CHEV-VAL-001, CHEV-VAL-004 */
    class Amb extends CstParser {
      constructor() {
        super(baseVocab, { maxLookahead: 1 });
        const $ = this as any;
        $.RULE("fork", () => {
          $.OR([
            { ALT: () => { $.CONSUME(Word); $.CONSUME(Pipe); } },
            { ALT: () => { $.CONSUME2(Word); $.CONSUME(Colon); } },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    expect(() => new Amb()).toThrow(/Parser Definition Errors detected/);
  });

  test("the same grammar constructs when maxLookahead suffices", () => {
    /** Verifies: CHEV-VAL-004, CHEV-GRM-013 */
    class Fine extends CstParser {
      constructor() {
        super(baseVocab, { maxLookahead: 2 });
        const $ = this as any;
        $.RULE("fork", () => {
          $.OR([
            { ALT: () => { $.CONSUME(Word); $.CONSUME(Pipe); } },
            { ALT: () => { $.CONSUME2(Word); $.CONSUME(Colon); } },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Fine() as any;
    p.input = lex("bay :").tokens;
    const cst = p.fork();
    expect(p.errors).toEqual([]);
    expect(cst.children.Colon).toHaveLength(1);
  });

  test("skipValidations skips ambiguity analysis but not duplicate rules", () => {
    /** Verifies: CHEV-VAL-005 */
    class AmbSkipped extends CstParser {
      constructor() {
        super(baseVocab, { skipValidations: true, maxLookahead: 1 });
        const $ = this as any;
        $.RULE("fork", () => {
          $.OR([
            { ALT: () => { $.CONSUME(Word); $.CONSUME(Pipe); } },
            { ALT: () => { $.CONSUME2(Word); $.CONSUME(Colon); } },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    expect(() => new AmbSkipped()).not.toThrow();
    class DupSkipped extends CstParser {
      constructor() {
        super(baseVocab, { skipValidations: true });
        const $ = this as any;
        $.RULE("twice", () => $.CONSUME(Word));
        $.RULE("twice", () => $.CONSUME(Amount));
        this.performSelfAnalysis();
      }
    }
    expect(() => new DupSkipped()).toThrow(/twice/);
  });

  test("consuming a token type outside the vocabulary surfaces at parse time", () => {
    /** Verifies: CHEV-VAL-006 */
    const Ghost = createToken({ name: "Ghost", pattern: /boo/ });
    class Haunted extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("seance", () => $.CONSUME(Ghost));
        this.performSelfAnalysis();
      }
    }
    let p: any;
    expect(() => { p = new Haunted(); }).not.toThrow();
    p.input = lex("word").tokens;
    const out = p.seance();
    expect(out).toBeUndefined();
    expect(p.errors[0].name).toBe("MismatchedTokenException");
  });
});

// ---------------------------------------------------------------------------
describe("cst visitors", () => {
  function freshRoute() {
    const p = new RouteParser() as any;
    p.input = lex("dock : 3 -> pier : 14").tokens;
    return { p, cst: p.route() };
  }

  test("a visitor dispatches by rule name and returns method results", () => {
    /** Verifies: CHEV-VIS-001, CHEV-VIS-002 */
    const { p, cst } = freshRoute();
    const Base = p.getBaseCstVisitorConstructor();
    class Totals extends Base {
      constructor() { super(); (this as any).validateVisitor(); }
      route(ch: any) {
        const legs = [ch.leg, ch.hop ?? []].flat();
        return legs.reduce((acc: number, l: any) => acc + (this as any).visit(l), 0);
      }
      leg(ch: any) {
        return ch.Amount ? Number(ch.Amount[0].image) : 0;
      }
    }
    expect(new Totals().visit(cst)).toBe(17);
  });

  test("visit on an array dispatches to the first element", () => {
    /** Verifies: CHEV-VIS-002 */
    const { p, cst } = freshRoute();
    const Base = p.getBaseCstVisitorConstructor();
    class FirstWord extends Base {
      constructor() { super(); (this as any).validateVisitor(); }
      route(ch: any) { return (this as any).visit(ch.leg); }
      leg(ch: any) { return ch.Word[0].image; }
    }
    expect(new FirstWord().visit([cst])).toBe("dock");
  });

  test("validateVisitor rejects a plain-base visitor missing rule methods", () => {
    /** Verifies: CHEV-VIS-004 */
    const p = new RouteParser() as any;
    const Base = p.getBaseCstVisitorConstructor();
    class Partial extends Base {
      constructor() { super(); (this as any).validateVisitor(); }
      route() { return 0; }
    }
    expect(() => new Partial()).toThrow(Error);
    expect(() => new Partial()).toThrow(/leg/);
  });

  test("a defaults-based visitor accepts a method subset", () => {
    /** Verifies: CHEV-VIS-003, CHEV-VIS-004 */
    const { p, cst } = freshRoute();
    const BaseDef = p.getBaseCstVisitorConstructorWithDefaults();
    class OnlyLeg extends BaseDef {
      constructor() { super(); (this as any).validateVisitor(); }
      leg(ch: any) { return ch.Word[0].image; }
    }
    const v = new OnlyLeg();
    expect(v.visit(cst.children.leg[0])).toBe("dock");
    expect(v.visit(cst)).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
describe("errors and recovery", () => {
  test("a wrong token at CONSUME records a MismatchedTokenException with context", () => {
    /** Verifies: CHEV-REC-001, CHEV-REC-002, CHEV-REC-005 */
    const { p, cst } = parseRoute("dock : quay");
    expect(cst).toBeUndefined();
    expect(p.errors).toHaveLength(1);
    const err = p.errors[0];
    expect(err.name).toBe("MismatchedTokenException");
    expect(err.token.image).toBe("quay");
    expect(err.context.ruleStack).toEqual(["route", "leg"]);
    expect(Array.isArray(err.resyncedTokens)).toBe(true);
  });

  test("no viable OR alternative records a NoViableAltException", () => {
    /** Verifies: CHEV-REC-005 */
    class Choice extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("pick", () => {
          $.OR([
            { ALT: () => $.CONSUME(Amount) },
            { ALT: () => $.CONSUME(Word) },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Choice() as any;
    p.input = lex("|").tokens;
    p.pick();
    expect(p.errors[0].name).toBe("NoViableAltException");
  });

  test("leftover input records NotAllInputParsed and keeps the prefix CST", () => {
    /** Verifies: CHEV-CST-003, CHEV-REC-005 */
    const { p, cst } = parseRoute("dock pier");
    expect(p.errors).toHaveLength(1);
    expect(p.errors[0].name).toBe("NotAllInputParsedException");
    expect(p.errors[0].token.image).toBe("pier");
    expect(cst).toBeDefined();
    expect(cst.children.leg[0].children.Word[0].image).toBe("dock");
  });

  test("an empty mandatory repetition records an EarlyExitException", () => {
    /** Verifies: CHEV-REC-005 */
    class Crew extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("crew", () => {
          $.AT_LEAST_ONE(() => $.CONSUME(Word));
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Crew() as any;
    p.input = lex("404").tokens;
    p.crew();
    expect(p.errors[0].name).toBe("EarlyExitException");
  });

  test("isRecognitionException separates recognition errors from other values", () => {
    /** Verifies: CHEV-REC-004 */
    const { p } = parseRoute("dock : quay");
    expect(isRecognitionException(p.errors[0])).toBe(true);
    expect(isRecognitionException(new Error("mundane"))).toBe(false);
  });

  test("without recovery a failing rule chain returns undefined", () => {
    /** Verifies: CHEV-CST-009, CHEV-REC-008 */
    const { p, cst } = parseRoute("dock -> : 9");
    expect(cst).toBeUndefined();
    expect(p.errors).toHaveLength(1);
  });

  test("recovery inserts a missing token flagged isInsertedInRecovery", () => {
    /** Verifies: CHEV-REC-006, CHEV-REC-007 */
    class Ledger extends CstParser {
      constructor() {
        super(baseVocab, { recoveryEnabled: true });
        const $ = this as any;
        $.RULE("line", () => {
          $.CONSUME(Word);
          $.CONSUME(Colon);
          $.CONSUME(Amount);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Ledger() as any;
    p.input = lex("net 31").tokens;
    const cst = p.line();
    expect(p.errors).toHaveLength(1);
    expect(cst.children.Colon).toHaveLength(1);
    const inserted = cst.children.Colon[0];
    expect(inserted.isInsertedInRecovery).toBe(true);
    expect(inserted.image).toBe("");
    expect(inserted.startOffset).toBe(-1);
    expect(cst.children.Amount[0].image).toBe("31");
  });

  test("recovery deletes an unexpected extra token and completes the parse", () => {
    /** Verifies: CHEV-REC-006, CHEV-REC-008 */
    class Ledger extends CstParser {
      constructor() {
        super(baseVocab, { recoveryEnabled: true });
        const $ = this as any;
        $.RULE("line", () => {
          $.CONSUME(Word);
          $.CONSUME(Colon);
          $.CONSUME(Amount);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Ledger() as any;
    p.input = lex("net : : 8").tokens;
    const cst = p.line();
    expect(p.errors).toHaveLength(1);
    expect(cst.children.Amount[0].image).toBe("8");
    expect(cst.children.Colon.filter((t: any) => t.isInsertedInRecovery)).toHaveLength(0);
  });

  test("re-synchronization collects skipped tokens into resyncedTokens", () => {
    /** Verifies: CHEV-REC-006 */
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
    p.input = lex("ash : 5 9 2 | fir : 6 |").tokens;
    const cst = p.sheet();
    expect(p.errors).toHaveLength(1);
    expect(p.errors[0].resyncedTokens.length).toBeGreaterThan(0);
    expect(cst.children.row).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
describe("grammar introspection", () => {
  test("getGAstProductions maps each rule name to a Rule instance", () => {
    /** Verifies: CHEV-GAST-001 */
    const p = new RouteParser() as any;
    const prods = p.getGAstProductions();
    expect(Object.keys(prods).sort()).toEqual(["leg", "route"]);
    expect(prods.route).toBeInstanceOf(Rule);
    expect(prods.route.name).toBe("route");
    expect(Array.isArray(prods.route.definition)).toBe(true);
  });

  test("terminals and non-terminals reference their definitions by identity", () => {
    /** Verifies: CHEV-GAST-002, CHEV-GAST-003 */
    const p = new RouteParser() as any;
    const prods = p.getGAstProductions();
    const first = prods.route.definition[0];
    expect(first).toBeInstanceOf(NonTerminal);
    expect(first.nonTerminalName).toBe("leg");
    expect(first.referencedRule).toBe(prods.leg);
    const rep = prods.route.definition[1];
    expect(rep).toBeInstanceOf(Repetition);
    const arrow = rep.definition[0];
    expect(arrow).toBeInstanceOf(Terminal);
    expect(arrow.terminalType).toBe(Arrowhead);
    const legOpt = prods.leg.definition[1];
    expect(legOpt).toBeInstanceOf(Option);
  });

  test("alternations hold one Alternative node per branch", () => {
    /** Verifies: CHEV-GAST-002 */
    class Choice extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("pick", () => {
          $.OR([
            { ALT: () => $.CONSUME(Amount) },
            { ALT: () => $.CONSUME(Word) },
            { ALT: () => $.CONSUME(Pipe) },
          ]);
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Choice() as any;
    const alt = p.getGAstProductions().pick.definition[0];
    expect(alt).toBeInstanceOf(Alternation);
    expect(alt.definition).toHaveLength(3);
    for (const branch of alt.definition) expect(branch).toBeInstanceOf(Alternative);
  });

  test("separator repetitions expose their separator token type", () => {
    /** Verifies: CHEV-GAST-002 */
    class Roster extends CstParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("roster", () => {
          $.MANY_SEP({ SEP: Pipe, DEF: () => $.CONSUME(Word) });
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Roster() as any;
    const rep = p.getGAstProductions().roster.definition[0];
    expect(rep).toBeInstanceOf(RepetitionWithSeparator);
    expect(rep.separator).toBe(Pipe);
  });

  test("serialized rules carry type, name and nested definitions", () => {
    /** Verifies: CHEV-GAST-004 */
    const p = new RouteParser() as any;
    const ser = p.getSerializedGastProductions();
    const leg = ser.find((r: any) => r.name === "leg");
    expect(leg.type).toBe("Rule");
    expect(leg.definition[0]).toMatchObject({ type: "Terminal", name: "Word", label: "Word", idx: 0 });
    expect(leg.definition[0].pattern).toBe("[a-z][a-z0-9]*");
    const route = ser.find((r: any) => r.name === "route");
    expect(route.definition[0]).toMatchObject({ type: "NonTerminal", name: "leg" });
    expect(route.definition[0].definition).toBeUndefined();
    expect(route.definition[1].type).toBe("Repetition");
  });

  test("serializeGrammar agrees with the parser's serialized productions", () => {
    /** Verifies: CHEV-GAST-005 */
    const p = new RouteParser() as any;
    const prods = p.getGAstProductions();
    const viaValues = serializeGrammar(Object.values(prods));
    expect(viaValues).toEqual(p.getSerializedGastProductions());
    const single = serializeProduction(prods.leg);
    expect(single).toEqual(viaValues.find((r: any) => r.name === "leg"));
  });

  test("GAstVisitor dispatches once per node kind without recursing", () => {
    /** Verifies: CHEV-GAST-006 */
    const p = new RouteParser() as any;
    const prods = p.getGAstProductions();
    const seen: string[] = [];
    class Peek extends (GAstVisitor as any) {
      visitTerminal(t: any) { seen.push(`T:${t.terminalType.name}`); }
      visitNonTerminal(nt: any) { seen.push(`N:${nt.nonTerminalName}`); }
      visitRepetition() { seen.push("Rep"); }
    }
    const v = new Peek() as any;
    v.visit(prods.route.definition[0]);
    expect(seen).toEqual(["N:leg"]);
    v.visit(prods.route.definition[1]);
    expect(seen).toEqual(["N:leg", "Rep"]);
  });

  test("generateCstDts declares node and children types per rule", () => {
    /** Verifies: CHEV-GAST-007 */
    const p = new RouteParser() as any;
    const dts = generateCstDts(p.getGAstProductions());
    expect(dts).toContain("interface RouteCstNode extends CstNode");
    expect(dts).toContain('name: "route"');
    expect(dts).toContain("RouteCstChildren");
    expect(dts).toContain("interface LegCstNode extends CstNode");
    expect(dts).toContain("Word: IToken[]");
    expect(dts).toContain("Colon?: IToken[]");
    expect(dts).toContain("hop?: LegCstNode[]");
    expect(dts).toContain("ICstNodeVisitor");
    expect(dts).toContain("route(children: RouteCstChildren");
  });
});

// ---------------------------------------------------------------------------
describe("embedded actions", () => {
  test("embedded rules return computed values instead of CST nodes", () => {
    /** Verifies: CHEV-EMB-001 */
    class Adder extends EmbeddedActionsParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("sum", () => {
          let total = $.SUBRULE($.datum);
          $.MANY(() => {
            $.CONSUME(Pipe);
            total += $.SUBRULE2($.datum);
          });
          return total;
        });
        $.RULE("datum", () => Number($.CONSUME(Amount).image));
        this.performSelfAnalysis();
      }
    }
    const p = new Adder() as any;
    p.input = lex("6 | 11 | 25").tokens;
    expect(p.sum()).toBe(42);
    expect(p.errors).toEqual([]);
  });

  test("CONSUME returns the matched token inside embedded rules", () => {
    /** Verifies: CHEV-EMB-001 */
    class Echo extends EmbeddedActionsParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("shout", () => {
          const tok = $.CONSUME(Word);
          return `${tok.image}@${tok.startOffset}`;
        });
        this.performSelfAnalysis();
      }
    }
    const p = new Echo() as any;
    p.input = lex("gull").tokens;
    expect(p.shout()).toBe("gull@0");
  });

  test("embedded parsing failures record the same recognition errors", () => {
    /** Verifies: CHEV-EMB-002, CHEV-EMB-003 */
    class Adder extends EmbeddedActionsParser {
      constructor() {
        super(baseVocab);
        const $ = this as any;
        $.RULE("datum", () => Number($.CONSUME(Amount).image));
        this.performSelfAnalysis();
      }
    }
    const p = new Adder() as any;
    p.input = lex("gale").tokens;
    const out = p.datum();
    expect(p.errors).toHaveLength(1);
    expect(p.errors[0].name).toBe("MismatchedTokenException");
    expect(isRecognitionException(p.errors[0])).toBe(true);
    expect(Number.isNaN(out) || out === undefined).toBe(true);
  });
});
