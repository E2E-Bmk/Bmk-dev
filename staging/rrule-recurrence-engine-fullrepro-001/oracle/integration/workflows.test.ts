// Spec2Repo oracle - integration tests for rrule-recurrence-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  RRule,
  RRuleSet,
  rrulestr,
  Weekday,
  datetime,
} from "rrule";

const iso = (dates: Date[]) => dates.map((d) => d.toISOString());

describe("string round trips", () => {
  test("fromString(toString) reproduces the occurrence sequence of a weekday rule", () => {
    /** Verifies: RRULE-CVI-001 | Seam: constructor->toString->fromString->all */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 0, 0), count: 5, byweekday: [RRule.TU, RRule.FR] });
    const restored = RRule.fromString(rule.toString());
    expect(iso(restored.all())).toEqual(iso(rule.all()));
    expect(restored.all()).toHaveLength(5);
  });

  test("fromString(toString) survives ordinal weekdays and set positions", () => {
    /** Verifies: RRULE-CVI-001, RRULE-EXP-006 | Seam: bysetpos serialization->parse->expansion */
    const rule = new RRule({
      freq: RRule.MONTHLY,
      dtstart: datetime(2031, 1, 1, 12, 0, 0),
      byweekday: [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR],
      bysetpos: -1,
      count: 4,
    });
    const restored = RRule.fromString(rule.toString());
    expect(iso(restored.all())).toEqual([
      "2031-01-31T12:00:00.000Z",
      "2031-02-28T12:00:00.000Z",
      "2031-03-31T12:00:00.000Z",
      "2031-04-30T12:00:00.000Z",
    ]);
  });

  test("optionsToString(parseString(s)) reproduces a bare rule string", () => {
    /** Verifies: RRULE-STR-004, RRULE-STR-005 | Seam: parseString->optionsToString */
    const s = "RRULE:FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=7";
    expect(RRule.optionsToString(RRule.parseString(s))).toBe(s);
  });

  test("a parsed rule enumerates directly from its string definition", () => {
    /** Verifies: RRULE-STR-005, RRULE-ENM-001 | Seam: parse->expansion */
    const rule = RRule.fromString("DTSTART:20310101T080000Z\nRRULE:FREQ=MONTHLY;BYDAY=+2FR;COUNT=3");
    expect(iso(rule.all())).toEqual([
      "2031-01-10T08:00:00.000Z",
      "2031-02-14T08:00:00.000Z",
      "2031-03-14T08:00:00.000Z",
    ]);
  });

  test("an until-bounded rule keeps its inclusive bound across the string view", () => {
    /** Verifies: RRULE-CVI-001, RRULE-EXP-009 | Seam: until serialization->parse->expansion */
    const rule = new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 2, 26, 7, 0, 0), until: datetime(2031, 3, 2, 7, 0, 0) });
    const restored = RRule.fromString(rule.toString());
    expect(restored.all()).toHaveLength(5);
    expect(iso(restored.all()).at(-1)).toBe("2031-03-02T07:00:00.000Z");
  });

  test("derived dtstart defaults survive the string view without being serialized", () => {
    /** Verifies: RRULE-NRM-005, RRULE-STR-001, RRULE-CVI-001 | Seam: normalization->serialization->parse */
    const rule = new RRule({ freq: RRule.YEARLY, dtstart: datetime(2031, 2, 28, 8, 0, 0), count: 3 });
    expect(rule.toString()).toBe("DTSTART:20310228T080000Z\nRRULE:FREQ=YEARLY;COUNT=3");
    const restored = RRule.fromString(rule.toString());
    expect(iso(restored.all())).toEqual([
      "2031-02-28T08:00:00.000Z",
      "2032-02-28T08:00:00.000Z",
      "2033-02-28T08:00:00.000Z",
    ]);
  });
});

describe("cross-view consistency", () => {
  test("wkst changes the emitted sequence of a biweekly multi-weekday rule", () => {
    /** Verifies: RRULE-EXP-007, RRULE-NRM-006 | Seam: normalization->weekly expansion */
    const mk = (wkst: Weekday) =>
      new RRule({ freq: RRule.WEEKLY, interval: 2, byweekday: [RRule.TU, RRule.SU], wkst, dtstart: datetime(2031, 8, 5, 10, 0, 0), count: 4 });
    expect(iso(mk(RRule.MO).all())).toEqual([
      "2031-08-05T10:00:00.000Z",
      "2031-08-10T10:00:00.000Z",
      "2031-08-19T10:00:00.000Z",
      "2031-08-24T10:00:00.000Z",
    ]);
    expect(iso(mk(RRule.SU).all())).toEqual([
      "2031-08-05T10:00:00.000Z",
      "2031-08-17T10:00:00.000Z",
      "2031-08-19T10:00:00.000Z",
      "2031-08-31T10:00:00.000Z",
    ]);
  });

  test("windowed queries agree with the full expansion", () => {
    /** Verifies: RRULE-CVI-003 | Seam: all<->between/before/after/count */
    const rule = new RRule({ freq: RRule.MONTHLY, dtstart: datetime(2031, 1, 1, 9, 0, 0), bymonthday: [4, -3], count: 8 });
    const all = iso(rule.all());
    expect(rule.count()).toBe(all.length);
    const windowed = iso(rule.between(datetime(2031, 1, 1), datetime(2031, 4, 1)));
    for (const d of windowed) expect(all).toContain(d);
    expect(rule.before(datetime(2031, 6, 1))!.toISOString()).toBe(all.filter((d) => d < "2031-06-01")!.at(-1));
    expect(rule.after(datetime(2031, 2, 1))!.toISOString()).toBe(all.find((d) => d > "2031-02-01"));
  });

  test("origOptions and options never disagree on caller-supplied values", () => {
    /** Verifies: RRULE-CVI-002, RRULE-NRM-001, RRULE-NRM-002 | Seam: origOptions<->options */
    const dtstart = datetime(2031, 1, 7, 14, 30, 0);
    const rule = new RRule({ freq: RRule.WEEKLY, interval: 2, dtstart, count: 4, wkst: 3 });
    expect(rule.origOptions.interval).toBe(2);
    expect(rule.options.interval).toBe(2);
    expect(rule.origOptions.wkst).toBe(3);
    expect(rule.options.wkst).toBe(3);
    expect(rule.origOptions.dtstart).toEqual(dtstart);
    expect(rule.options.dtstart).toEqual(dtstart);
    expect(rule.origOptions.byweekday).toBeUndefined();
    expect(rule.options.byweekday).toEqual([1]); // derived from the Tuesday start
  });

  test("clone preserves every projection of a rule", () => {
    /** Verifies: RRULE-CVI-007, RRULE-DEF-005 | Seam: clone->all/toString/toText */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 0, 0), count: 5, byweekday: [RRule.TU, RRule.FR] });
    const copy = rule.clone();
    expect(iso(copy.all())).toEqual(iso(rule.all()));
    expect(copy.toString()).toBe(rule.toString());
    expect(copy.toText()).toBe(rule.toText());
  });

  test("unbounded rules stream through the iterator callback", () => {
    /** Verifies: RRULE-ENM-002, RRULE-EXP-001 | Seam: unbounded generation->callback */
    const rule = new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 10, 1, 7, 0, 0) });
    expect(iso(rule.all((_d, i) => i < 4))).toEqual([
      "2031-10-01T07:00:00.000Z",
      "2031-10-02T07:00:00.000Z",
      "2031-10-03T07:00:00.000Z",
      "2031-10-04T07:00:00.000Z",
    ]);
  });
});

describe("text round trips", () => {
  test("a fully convertible rule survives toText/parseText with the same recurrence", () => {
    /** Verifies: RRULE-CVI-005, RRULE-NLP-003 | Seam: toText->parseText->constructor->all */
    const dtstart = datetime(2031, 3, 4, 9, 0, 0);
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart, count: 5, byweekday: [RRule.TU, RRule.FR] });
    expect(rule.isFullyConvertibleToText()).toBe(true);
    const rebuilt = new RRule({ ...RRule.parseText(rule.toText())!, dtstart });
    expect(iso(rebuilt.all())).toEqual(iso(rule.all()));
  });

  test("fromText(toText) preserves the recurrence properties of an interval rule", () => {
    /** Verifies: RRULE-CVI-005, RRULE-NLP-004 | Seam: toText->fromText->origOptions */
    const rule = new RRule({ freq: RRule.DAILY, interval: 3, dtstart: datetime(2031, 1, 1), count: 7 });
    const back = RRule.fromText(rule.toText());
    expect(back.origOptions.freq).toBe(RRule.DAILY);
    expect(back.origOptions.interval).toBe(3);
    expect(back.origOptions.count).toBe(7);
  });

  test("a phrase-driven rule enumerates and serializes consistently", () => {
    /** Verifies: RRULE-NLP-003, RRULE-EXP-001, RRULE-CVI-001 | Seam: parseText->expansion->string round trip */
    const opts = RRule.parseText("every 2 weeks on tuesday");
    expect(opts).toMatchObject({ interval: 2, freq: RRule.WEEKLY });
    const rule = new RRule({ ...opts!, dtstart: datetime(2031, 4, 1, 10, 0, 0), count: 4 });
    expect(iso(rule.all())).toEqual([
      "2031-04-01T10:00:00.000Z",
      "2031-04-15T10:00:00.000Z",
      "2031-04-29T10:00:00.000Z",
      "2031-05-13T10:00:00.000Z",
    ]);
    expect(iso(RRule.fromString(rule.toString()).all())).toEqual(iso(rule.all()));
  });
});

describe("recurrence sets", () => {
  const juneSet = () => {
    const set = new RRuleSet();
    set.rrule(new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 6, 2, 10, 0, 0), count: 4, byweekday: [RRule.MO] }));
    set.rdate(datetime(2031, 6, 20, 15, 0, 0));
    set.exdate(datetime(2031, 6, 9, 10, 0, 0));
    return set;
  };

  test("a set merges rule occurrences with rdates and drops exdates", () => {
    /** Verifies: RRULE-SET-002 | Seam: rrule+rdate+exdate->all */
    expect(iso(juneSet().all())).toEqual([
      "2031-06-02T10:00:00.000Z",
      "2031-06-16T10:00:00.000Z",
      "2031-06-20T15:00:00.000Z",
      "2031-06-23T10:00:00.000Z",
    ]);
  });

  test("an exclusion rule removes every instant it generates", () => {
    /** Verifies: RRULE-SET-002 | Seam: rrule+exrule->all */
    const set = new RRuleSet();
    set.rrule(new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 7, 1, 8, 0, 0), count: 6 }));
    set.exrule(new RRule({ freq: RRule.DAILY, interval: 2, dtstart: datetime(2031, 7, 1, 8, 0, 0), count: 6 }));
    expect(iso(set.all())).toEqual([
      "2031-07-02T08:00:00.000Z",
      "2031-07-04T08:00:00.000Z",
      "2031-07-06T08:00:00.000Z",
    ]);
  });

  test("duplicate instants from different sources appear once", () => {
    /** Verifies: RRULE-SET-002, RRULE-CVI-004 | Seam: rrule+rdate dedupe */
    const set = new RRuleSet();
    set.rrule(new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 8, 1, 7, 0, 0), count: 3 }));
    set.rdate(datetime(2031, 8, 2, 7, 0, 0));
    set.rdate(datetime(2031, 8, 1, 7, 0, 0));
    expect(iso(set.all())).toEqual([
      "2031-08-01T07:00:00.000Z",
      "2031-08-02T07:00:00.000Z",
      "2031-08-03T07:00:00.000Z",
    ]);
  });

  test("windowed queries on a set follow single-rule inclusivity semantics", () => {
    /** Verifies: RRULE-SET-002, RRULE-ENM-003, RRULE-ENM-004 | Seam: set->between/before/after */
    const set = juneSet();
    expect(iso(set.between(datetime(2031, 6, 15), datetime(2031, 6, 21)))).toEqual([
      "2031-06-16T10:00:00.000Z",
      "2031-06-20T15:00:00.000Z",
    ]);
    expect(set.before(datetime(2031, 6, 20, 15, 0, 0))?.toISOString()).toBe("2031-06-16T10:00:00.000Z");
    expect(set.before(datetime(2031, 6, 20, 15, 0, 0), true)?.toISOString()).toBe("2031-06-20T15:00:00.000Z");
    expect(set.after(datetime(2031, 6, 20, 15, 0, 0))?.toISOString()).toBe("2031-06-23T10:00:00.000Z");
  });

  test("count on a set equals the merged sequence length", () => {
    /** Verifies: RRULE-CVI-003, RRULE-SET-002 | Seam: set count<->all */
    const set = new RRuleSet();
    set.rrule(new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 8, 1, 7, 0, 0), count: 5 }));
    set.exdate(datetime(2031, 8, 3, 7, 0, 0));
    expect(set.count()).toBe(4);
    expect(set.all()).toHaveLength(4);
  });

  test("set clones are independent of later mutation", () => {
    /** Verifies: RRULE-CVI-007, RRULE-SET-001 | Seam: clone->add source->all */
    const set = new RRuleSet();
    set.rdate(datetime(2031, 9, 5, 12, 0, 0));
    set.rdate(datetime(2031, 9, 1, 12, 0, 0));
    const copy = set.clone();
    set.rdate(datetime(2031, 9, 9, 12, 0, 0));
    expect(copy.rdates()).toHaveLength(2);
    expect(set.rdates()).toHaveLength(3);
    expect(iso(copy.all())).toEqual(["2031-09-01T12:00:00.000Z", "2031-09-05T12:00:00.000Z"]);
  });

  test("rrulestr rebuilds a set from its own toString including exclusion rules", () => {
    /** Verifies: RRULE-CVI-004, RRULE-STR-007, RRULE-SET-003 | Seam: set toString->rrulestr->all */
    const set = new RRuleSet();
    set.rrule(new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 7, 1, 8, 0, 0), count: 6 }));
    set.exrule(new RRule({ freq: RRule.DAILY, interval: 2, count: 6, dtstart: datetime(2031, 7, 1, 8, 0, 0) }));
    const text = set.toString();
    expect(text).toContain("EXRULE:FREQ=DAILY;INTERVAL=2;COUNT=6");
    const restored = rrulestr(text);
    expect(restored).toBeInstanceOf(RRuleSet);
    expect(iso(restored.all())).toEqual(iso(set.all()));
  });

  test("a multi-line recurrence text parses to the same merged stream it serializes", () => {
    /** Verifies: RRULE-CVI-004, RRULE-STR-007 | Seam: rrulestr->all->toString */
    const parsed = rrulestr(
      "DTSTART:20310602T100000Z\nRRULE:FREQ=WEEKLY;COUNT=4;BYDAY=MO\nRDATE:20310620T150000Z\nEXDATE:20310609T100000Z",
    ) as RRuleSet;
    expect(iso(parsed.all())).toEqual([
      "2031-06-02T10:00:00.000Z",
      "2031-06-16T10:00:00.000Z",
      "2031-06-20T15:00:00.000Z",
      "2031-06-23T10:00:00.000Z",
    ]);
    expect(parsed.valueOf()).toEqual([
      "DTSTART:20310602T100000Z",
      "RRULE:FREQ=WEEKLY;COUNT=4;BYDAY=MO",
      "RDATE:20310620T150000Z",
      "EXDATE:20310609T100000Z",
    ]);
  });
});

describe("end-to-end workflows", () => {
  test("build, persist, restore and query a rule across every view", () => {
    /** Verifies: RRULE-CVI-001, RRULE-CVI-003, RRULE-NLP-001 | Seam: full rule lifecycle */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 0, 0), count: 5, byweekday: [RRule.TU, RRule.FR] });
    expect(rule.count()).toBe(5);
    const persisted = rule.toString();
    const restored = RRule.fromString(persisted);
    expect(iso(restored.between(datetime(2031, 3, 5), datetime(2031, 3, 15)))).toEqual([
      "2031-03-07T09:00:00.000Z",
      "2031-03-11T09:00:00.000Z",
      "2031-03-14T09:00:00.000Z",
    ]);
    expect(restored.toText()).toBe("every week on Tuesday, Friday for 5 times");
    const viaText = new RRule({ ...RRule.parseText(restored.toText())!, dtstart: datetime(2031, 3, 4, 9, 0, 0) });
    expect(iso(viaText.all())).toEqual(iso(rule.all()));
  });

  test("a quarterly schedule set merges weekly and month-end rules and round-trips", () => {
    /** Verifies: RRULE-CVI-004, RRULE-EXP-006, RRULE-SET-002 | Seam: full set lifecycle */
    const start = datetime(2031, 1, 6, 9, 30, 0);
    const standup = new RRule({
      freq: RRule.WEEKLY,
      byweekday: [RRule.MO],
      dtstart: start,
      until: datetime(2031, 3, 31, 23, 59, 59),
    });
    const retro = new RRule({
      freq: RRule.MONTHLY,
      byweekday: [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR],
      bysetpos: -1,
      dtstart: start,
      until: datetime(2031, 3, 31, 23, 59, 59),
    });
    const schedule = new RRuleSet();
    schedule.rrule(standup);
    schedule.rrule(retro);
    const all = schedule.all();
    // 13 standups + 3 month-end retros, with 2031-03-31 (a Monday month-end) deduplicated
    expect(all).toHaveLength(15);
    expect(iso(all).slice(0, 3)).toEqual([
      "2031-01-06T09:30:00.000Z",
      "2031-01-13T09:30:00.000Z",
      "2031-01-20T09:30:00.000Z",
    ]);
    expect(iso(all).slice(-2)).toEqual(["2031-03-24T09:30:00.000Z", "2031-03-31T09:30:00.000Z"]);
    const restored = rrulestr(schedule.toString()) as RRuleSet;
    expect(iso(restored.all())).toEqual(iso(all));
    expect(iso(restored.between(datetime(2031, 2, 1), datetime(2031, 3, 1)))).toEqual([
      "2031-02-03T09:30:00.000Z",
      "2031-02-10T09:30:00.000Z",
      "2031-02-17T09:30:00.000Z",
      "2031-02-24T09:30:00.000Z",
      "2031-02-28T09:30:00.000Z",
    ]);
  });

  test("a phrase becomes a persisted schedule whose restored form matches all views", () => {
    /** Verifies: RRULE-CVI-001, RRULE-CVI-005, RRULE-NLP-003 | Seam: text->rule->string->rule lifecycle */
    const opts = RRule.parseText("every 2 weeks on tuesday");
    const rule = new RRule({ ...opts!, dtstart: datetime(2031, 4, 1, 10, 0, 0), count: 4 });
    const restored = RRule.fromString(rule.toString());
    expect(iso(restored.all())).toEqual([
      "2031-04-01T10:00:00.000Z",
      "2031-04-15T10:00:00.000Z",
      "2031-04-29T10:00:00.000Z",
      "2031-05-13T10:00:00.000Z",
    ]);
    expect(restored.count()).toBe(4);
    expect(restored.after(datetime(2031, 4, 20))?.toISOString()).toBe("2031-04-29T10:00:00.000Z");
  });

  test("exception management workflow: cancel and reschedule occurrences, then persist", () => {
    /** Verifies: RRULE-CVI-004, RRULE-SET-002, RRULE-SET-003 | Seam: set edit lifecycle across views */
    const set = new RRuleSet();
    set.rrule(new RRule({ freq: RRule.WEEKLY, byweekday: [RRule.WE], dtstart: datetime(2031, 5, 7, 13, 0, 0), count: 5 }));
    set.exdate(datetime(2031, 5, 21, 13, 0, 0)); // cancelled session
    set.rdate(datetime(2031, 5, 22, 13, 0, 0)); // rescheduled to Thursday
    const all = iso(set.all());
    expect(all).toEqual([
      "2031-05-07T13:00:00.000Z",
      "2031-05-14T13:00:00.000Z",
      "2031-05-22T13:00:00.000Z",
      "2031-05-28T13:00:00.000Z",
      "2031-06-04T13:00:00.000Z",
    ]);
    const restored = rrulestr(set.toString()) as RRuleSet;
    expect(iso(restored.all())).toEqual(all);
    expect(restored.rdates()).toHaveLength(1);
    expect(restored.exdates()).toHaveLength(1);
    expect(restored.count()).toBe(5);
  });
});
