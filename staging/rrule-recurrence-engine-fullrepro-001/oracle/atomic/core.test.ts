// Spec2Repo oracle - atomic tests for rrule-recurrence-engine-fullrepro-001
import { describe, expect, test } from "vitest";
import {
  RRule,
  RRuleSet,
  rrulestr,
  Weekday,
  Frequency,
  ALL_WEEKDAYS,
  datetime,
} from "rrule";

const iso = (dates: Date[]) => dates.map((d) => d.toISOString());

describe("dates and constants", () => {
  test("datetime builds a Date carrying the given UTC calendar components", () => {
    /** Verifies: RRULE-DTC-002 */
    const d = datetime(2031, 3, 8, 9, 30, 7);
    expect(d.getUTCFullYear()).toBe(2031);
    expect(d.getUTCMonth()).toBe(2); // JS months are 0-based; datetime months are 1-based
    expect(d.getUTCDate()).toBe(8);
    expect(d.getUTCHours()).toBe(9);
    expect(d.getUTCMinutes()).toBe(30);
    expect(d.getUTCSeconds()).toBe(7);
    expect(d.toISOString()).toBe("2031-03-08T09:30:07.000Z");
    // hour, minute and second default to zero
    expect(datetime(2032, 11, 20).toISOString()).toBe("2032-11-20T00:00:00.000Z");
  });

  test("Frequency is a numeric enum from YEARLY=0 to SECONDLY=6 with reverse lookup", () => {
    /** Verifies: RRULE-DEF-001 */
    expect(Frequency.YEARLY).toBe(0);
    expect(Frequency.MONTHLY).toBe(1);
    expect(Frequency.WEEKLY).toBe(2);
    expect(Frequency.DAILY).toBe(3);
    expect(Frequency.HOURLY).toBe(4);
    expect(Frequency.MINUTELY).toBe(5);
    expect(Frequency.SECONDLY).toBe(6);
    expect(Frequency[2]).toBe("WEEKLY");
    expect(Frequency[6]).toBe("SECONDLY");
  });

  test("RRule mirrors the frequency values and lists FREQUENCIES in value order", () => {
    /** Verifies: RRULE-DEF-001 */
    expect(RRule.YEARLY).toBe(Frequency.YEARLY);
    expect(RRule.WEEKLY).toBe(2);
    expect(RRule.SECONDLY).toBe(6);
    expect(RRule.FREQUENCIES).toEqual([
      "YEARLY",
      "MONTHLY",
      "WEEKLY",
      "DAILY",
      "HOURLY",
      "MINUTELY",
      "SECONDLY",
    ]);
  });

  test("ALL_WEEKDAYS lists the two-letter tokens Monday-first", () => {
    /** Verifies: RRULE-DEF-003 */
    expect(ALL_WEEKDAYS).toEqual(["MO", "TU", "WE", "TH", "FR", "SA", "SU"]);
  });

  test("weekday constants use Monday=0 numbering and stringify as tokens", () => {
    /** Verifies: RRULE-DEF-003 */
    expect(RRule.MO.weekday).toBe(0);
    expect(RRule.WE.weekday).toBe(2);
    expect(RRule.SU.weekday).toBe(6);
    expect(String(RRule.TH)).toBe("TH");
    expect(String(RRule.SA)).toBe("SA");
  });

  test("getJsWeekday converts to JavaScript Sunday=0 numbering", () => {
    /** Verifies: RRULE-DEF-003 */
    expect(RRule.SU.getJsWeekday()).toBe(0);
    expect(RRule.MO.getJsWeekday()).toBe(1);
    expect(RRule.FR.getJsWeekday()).toBe(5);
  });

  test("Weekday.fromStr parses tokens and equals compares weekday and ordinal", () => {
    /** Verifies: RRULE-DEF-003 */
    const th = Weekday.fromStr("TH");
    expect(th.weekday).toBe(3);
    expect(th.equals(RRule.TH)).toBe(true);
    expect(th.equals(RRule.FR)).toBe(false);
  });
});

describe("weekday ordinals", () => {
  test("nth produces an ordinal weekday with signed token rendering", () => {
    /** Verifies: RRULE-DEF-004 */
    const second = RRule.FR.nth(2);
    expect(second.weekday).toBe(4);
    expect(second.n).toBe(2);
    expect(String(second)).toBe("+2FR");
    expect(String(RRule.FR.nth(-1))).toBe("-1FR");
  });

  test("equals distinguishes ordinal from plain weekdays", () => {
    /** Verifies: RRULE-DEF-003, RRULE-DEF-004 */
    expect(RRule.FR.nth(2).equals(new Weekday(4, 2))).toBe(true);
    expect(RRule.FR.nth(2).equals(RRule.FR)).toBe(false);
  });

  test("a zero ordinal is rejected", () => {
    /** Verifies: RRULE-ERR-003 */
    expect(() => new Weekday(2, 0)).toThrow(Error);
    expect(() => RRule.WE.nth(0)).toThrow(Error);
  });
});

describe("construction and normalization", () => {
  test("origOptions echoes exactly the caller-supplied options", () => {
    /** Verifies: RRULE-NRM-001 */
    const dtstart = datetime(2031, 1, 7, 14, 30, 0);
    const rule = new RRule({ freq: RRule.WEEKLY, interval: 2, dtstart, count: 4 });
    expect(rule.origOptions).toEqual({ freq: RRule.WEEKLY, interval: 2, dtstart, count: 4 });
  });

  test("options fills every recognized key with defaults", () => {
    /** Verifies: RRULE-NRM-002 */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 0, 0), count: 3 });
    expect(rule.options.interval).toBe(1);
    expect(rule.options.wkst).toBe(0);
    expect(rule.options.until).toBeNull();
    expect(rule.options.tzid).toBeNull();
    expect(rule.options.byeaster).toBeNull();
    expect(rule.options.bysetpos).toBeNull();
    expect(rule.options.count).toBe(3);
  });

  test("freq defaults to YEARLY when omitted", () => {
    /** Verifies: RRULE-DEF-001 */
    const rule = new RRule({ dtstart: datetime(2031, 5, 2, 8, 0, 0), count: 2 });
    expect(rule.options.freq).toBe(RRule.YEARLY);
    expect(iso(rule.all())).toEqual(["2031-05-02T08:00:00.000Z", "2032-05-02T08:00:00.000Z"]);
  });

  test("byweekday accepts Weekday, integer and token forms and normalizes to numbers", () => {
    /** Verifies: RRULE-DEF-002, RRULE-NRM-003 */
    const rule = new RRule({
      freq: RRule.WEEKLY,
      dtstart: datetime(2031, 3, 4, 9, 0, 0),
      count: 3,
      byweekday: [RRule.TU, "FR"],
    });
    expect(rule.options.byweekday).toEqual([1, 4]);
    expect(iso(rule.all())).toEqual([
      "2031-03-04T09:00:00.000Z",
      "2031-03-07T09:00:00.000Z",
      "2031-03-11T09:00:00.000Z",
    ]);
  });

  test("ordinal weekday entries split into bynweekday pairs", () => {
    /** Verifies: RRULE-NRM-003 */
    const rule = new RRule({
      freq: RRule.MONTHLY,
      dtstart: datetime(2031, 1, 1, 8, 0, 0),
      byweekday: RRule.FR.nth(2),
      count: 3,
    });
    expect(rule.options.bynweekday).toEqual([[4, 2]]);
    expect(rule.options.byweekday).toBeNull();
  });

  test("bymonthday splits positive and negative values", () => {
    /** Verifies: RRULE-NRM-004 */
    const rule = new RRule({
      freq: RRule.MONTHLY,
      dtstart: datetime(2031, 1, 1, 9, 0, 0),
      bymonthday: [4, -3],
      count: 4,
    });
    expect(rule.options.bymonthday).toEqual([4]);
    expect(rule.options.bynmonthday).toEqual([-3]);
  });

  test("a yearly rule derives month and month-day from its start date", () => {
    /** Verifies: RRULE-NRM-005 */
    const rule = new RRule({ freq: RRule.YEARLY, dtstart: datetime(2031, 2, 28, 8, 0, 0), count: 3 });
    expect(rule.options.bymonth).toEqual([2]);
    expect(rule.options.bymonthday).toEqual([28]);
  });

  test("monthly and weekly rules derive their missing date-level constraint from dtstart", () => {
    /** Verifies: RRULE-NRM-005 */
    const monthly = new RRule({ freq: RRule.MONTHLY, dtstart: datetime(2031, 1, 31, 8, 0, 0), count: 2 });
    expect(monthly.options.bymonthday).toEqual([31]);
    const weekly = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 1, 8, 8, 0, 0), count: 2 });
    expect(weekly.options.byweekday).toEqual([2]); // 2031-01-08 is a Wednesday
  });

  test("time-of-day components derive from dtstart for daily and coarser rules", () => {
    /** Verifies: RRULE-NRM-005 */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 20, 40), count: 1 });
    expect(rule.options.byhour).toEqual([9]);
    expect(rule.options.byminute).toEqual([20]);
    expect(rule.options.bysecond).toEqual([40]);
  });

  test("wkst normalizes Weekday to its number and keeps integers", () => {
    /** Verifies: RRULE-NRM-006 */
    const w = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 1, 6, 9, 0, 0), wkst: RRule.SU, count: 1 });
    expect(w.options.wkst).toBe(6);
    const n = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 1, 6, 9, 0, 0), wkst: 3, count: 1 });
    expect(n.options.wkst).toBe(3);
  });

  test("an invalid dtstart is rejected at construction", () => {
    /** Verifies: RRULE-ERR-001 */
    expect(() => new RRule({ freq: RRule.DAILY, dtstart: new Date(NaN) })).toThrow(Error);
  });

  test("clone returns an equivalent independent rule", () => {
    /** Verifies: RRULE-DEF-005 */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 0, 0), count: 4, byweekday: [RRule.TU] });
    const copy = rule.clone();
    expect(copy).not.toBe(rule);
    expect(copy.toString()).toBe(rule.toString());
    expect(iso(copy.all())).toEqual(iso(rule.all()));
  });
});

describe("occurrence enumeration", () => {
  const daily = () => new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 5, 1, 6, 0, 0), count: 10 });

  test("all returns the full ascending occurrence list", () => {
    /** Verifies: RRULE-ENM-001 */
    const dates = daily().all();
    expect(dates).toHaveLength(10);
    expect(dates[0].toISOString()).toBe("2031-05-01T06:00:00.000Z");
    expect(dates[9].toISOString()).toBe("2031-05-10T06:00:00.000Z");
    expect(dates[3].toISOString()).toBe("2031-05-04T06:00:00.000Z");
  });

  test("all stops at the first occurrence for which the iterator returns false", () => {
    /** Verifies: RRULE-ENM-002 */
    expect(iso(daily().all((_d, i) => i < 3))).toEqual([
      "2031-05-01T06:00:00.000Z",
      "2031-05-02T06:00:00.000Z",
      "2031-05-03T06:00:00.000Z",
    ]);
  });

  test("between excludes both endpoints by default", () => {
    /** Verifies: RRULE-ENM-003 */
    expect(iso(daily().between(datetime(2031, 5, 3, 6, 0, 0), datetime(2031, 5, 6, 6, 0, 0)))).toEqual([
      "2031-05-04T06:00:00.000Z",
      "2031-05-05T06:00:00.000Z",
    ]);
  });

  test("between includes endpoint occurrences when inc is true", () => {
    /** Verifies: RRULE-ENM-003 */
    expect(iso(daily().between(datetime(2031, 5, 3, 6, 0, 0), datetime(2031, 5, 6, 6, 0, 0), true))).toEqual([
      "2031-05-03T06:00:00.000Z",
      "2031-05-04T06:00:00.000Z",
      "2031-05-05T06:00:00.000Z",
      "2031-05-06T06:00:00.000Z",
    ]);
  });

  test("an inverted between window yields an empty array", () => {
    /** Verifies: RRULE-ENM-003, RRULE-ERR-012 */
    expect(daily().between(datetime(2031, 5, 8, 6, 0, 0), datetime(2031, 5, 2, 6, 0, 0))).toEqual([]);
  });

  test("before returns the latest occurrence strictly before, or at with inc", () => {
    /** Verifies: RRULE-ENM-004 */
    expect(daily().before(datetime(2031, 5, 4, 6, 0, 0))?.toISOString()).toBe("2031-05-03T06:00:00.000Z");
    expect(daily().before(datetime(2031, 5, 4, 6, 0, 0), true)?.toISOString()).toBe("2031-05-04T06:00:00.000Z");
  });

  test("after returns the earliest occurrence strictly after, or at with inc", () => {
    /** Verifies: RRULE-ENM-004 */
    expect(daily().after(datetime(2031, 5, 4, 6, 0, 0))?.toISOString()).toBe("2031-05-05T06:00:00.000Z");
    expect(daily().after(datetime(2031, 5, 4, 6, 0, 0), true)?.toISOString()).toBe("2031-05-04T06:00:00.000Z");
  });

  test("before and after return null when nothing qualifies", () => {
    /** Verifies: RRULE-ENM-004, RRULE-ERR-013 */
    expect(daily().before(datetime(2031, 4, 30, 6, 0, 0))).toBeNull();
    expect(daily().after(datetime(2031, 5, 10, 6, 0, 0))).toBeNull();
  });

  test("count returns the total number of occurrences", () => {
    /** Verifies: RRULE-ENM-005 */
    expect(daily().count()).toBe(10);
    const until = new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 2, 26, 7, 0, 0), until: datetime(2031, 3, 2, 7, 0, 0) });
    expect(until.count()).toBe(5);
  });

  test("non-Date arguments to windowed queries are rejected", () => {
    /** Verifies: RRULE-ERR-008 */
    const rule = daily();
    expect(() => rule.between("2031-05-02" as unknown as Date, datetime(2031, 5, 8))).toThrow(Error);
    expect(() => rule.before("2031-05-02" as unknown as Date)).toThrow(Error);
    expect(() => rule.after("2031-05-02" as unknown as Date)).toThrow(Error);
  });

  test("a frequency outside the enumeration is rejected at construction", () => {
    /** Verifies: RRULE-ERR-006 */
    expect(() => new RRule({ freq: 99 as unknown as Frequency, dtstart: datetime(2031, 1, 1), count: 2 })).toThrow(Error);
  });

  test("a zero bysetpos is rejected at construction", () => {
    /** Verifies: RRULE-ERR-007 */
    expect(() => new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 1, 1), count: 2, bysetpos: 0 })).toThrow(Error);
  });
});

describe("expansion arithmetic", () => {
  test("interval strides whole frequency periods", () => {
    /** Verifies: RRULE-EXP-001 */
    const rule = new RRule({ freq: RRule.WEEKLY, interval: 2, dtstart: datetime(2031, 1, 7, 14, 30, 0), count: 4 });
    expect(iso(rule.all())).toEqual([
      "2031-01-07T14:30:00.000Z",
      "2031-01-21T14:30:00.000Z",
      "2031-02-04T14:30:00.000Z",
      "2031-02-18T14:30:00.000Z",
    ]);
  });

  test("finer-grained by-rules multiply occurrences within each period", () => {
    /** Verifies: RRULE-EXP-002 */
    const rule = new RRule({
      freq: RRule.DAILY,
      dtstart: datetime(2031, 4, 1, 0, 0, 0),
      byhour: [6, 18],
      byminute: 45,
      count: 5,
    });
    expect(iso(rule.all())).toEqual([
      "2031-04-01T06:45:00.000Z",
      "2031-04-01T18:45:00.000Z",
      "2031-04-02T06:45:00.000Z",
      "2031-04-02T18:45:00.000Z",
      "2031-04-03T06:45:00.000Z",
    ]);
  });

  test("negative bymonthday counts back from the end of the month", () => {
    /** Verifies: RRULE-EXP-003 */
    const rule = new RRule({ freq: RRule.MONTHLY, dtstart: datetime(2031, 1, 1, 9, 0, 0), bymonthday: [4, -3], count: 4 });
    expect(iso(rule.all())).toEqual([
      "2031-01-04T09:00:00.000Z",
      "2031-01-29T09:00:00.000Z",
      "2031-02-04T09:00:00.000Z",
      "2031-02-26T09:00:00.000Z",
    ]);
  });

  test("byyearday supports negative indices and honors leap years", () => {
    /** Verifies: RRULE-EXP-003 */
    const rule = new RRule({ freq: RRule.YEARLY, dtstart: datetime(2031, 1, 1, 6, 30, 0), byyearday: [60, -1], count: 4 });
    expect(iso(rule.all())).toEqual([
      "2031-03-01T06:30:00.000Z", // day 60 of a common year
      "2031-12-31T06:30:00.000Z",
      "2032-02-29T06:30:00.000Z", // day 60 of a leap year
      "2032-12-31T06:30:00.000Z",
    ]);
  });

  test("byweekno selects ISO week numbers", () => {
    /** Verifies: RRULE-EXP-004 */
    const rule = new RRule({ freq: RRule.YEARLY, dtstart: datetime(2030, 12, 30, 8, 0, 0), byweekno: 20, byweekday: RRule.WE, count: 3 });
    expect(iso(rule.all())).toEqual([
      "2031-05-14T08:00:00.000Z",
      "2032-05-12T08:00:00.000Z",
      "2033-05-18T08:00:00.000Z",
    ]);
  });

  test("a positive ordinal weekday picks the n-th matching weekday of the month", () => {
    /** Verifies: RRULE-EXP-005 */
    const rule = new RRule({ freq: RRule.MONTHLY, dtstart: datetime(2031, 1, 1, 8, 0, 0), byweekday: RRule.FR.nth(2), count: 3 });
    expect(iso(rule.all())).toEqual([
      "2031-01-10T08:00:00.000Z",
      "2031-02-14T08:00:00.000Z",
      "2031-03-14T08:00:00.000Z",
    ]);
  });

  test("a negative ordinal weekday counts from the end of a bymonth-constrained year", () => {
    /** Verifies: RRULE-EXP-005 */
    const rule = new RRule({ freq: RRule.YEARLY, dtstart: datetime(2031, 1, 1, 11, 0, 0), bymonth: [4], byweekday: RRule.TH.nth(-1), count: 3 });
    expect(iso(rule.all())).toEqual([
      "2031-04-24T11:00:00.000Z",
      "2032-04-29T11:00:00.000Z",
      "2033-04-28T11:00:00.000Z",
    ]);
  });

  test("bysetpos -1 selects the last candidate of each period", () => {
    /** Verifies: RRULE-EXP-006 */
    const rule = new RRule({
      freq: RRule.MONTHLY,
      dtstart: datetime(2031, 1, 1, 12, 0, 0),
      byweekday: [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR],
      bysetpos: -1,
      count: 4,
    });
    expect(iso(rule.all())).toEqual([
      "2031-01-31T12:00:00.000Z",
      "2031-02-28T12:00:00.000Z",
      "2031-03-31T12:00:00.000Z",
      "2031-04-30T12:00:00.000Z",
    ]);
  });

  test("bysetpos mixes positions from both ends of the candidate list", () => {
    /** Verifies: RRULE-EXP-006 */
    const rule = new RRule({
      freq: RRule.MONTHLY,
      dtstart: datetime(2031, 1, 1, 9, 0, 0),
      byweekday: [RRule.SA, RRule.SU],
      bysetpos: [1, -1],
      count: 6,
    });
    expect(iso(rule.all())).toEqual([
      "2031-01-04T09:00:00.000Z",
      "2031-01-26T09:00:00.000Z",
      "2031-02-01T09:00:00.000Z",
      "2031-02-23T09:00:00.000Z",
      "2031-03-01T09:00:00.000Z",
      "2031-03-30T09:00:00.000Z",
    ]);
  });

  test("hourly and secondly frequencies stride at their own granularity", () => {
    /** Verifies: RRULE-EXP-008 */
    const hourly = new RRule({ freq: RRule.HOURLY, interval: 6, dtstart: datetime(2031, 2, 10, 1, 15, 0), count: 5 });
    expect(iso(hourly.all())).toEqual([
      "2031-02-10T01:15:00.000Z",
      "2031-02-10T07:15:00.000Z",
      "2031-02-10T13:15:00.000Z",
      "2031-02-10T19:15:00.000Z",
      "2031-02-11T01:15:00.000Z",
    ]);
    const secondly = new RRule({ freq: RRule.SECONDLY, interval: 40, dtstart: datetime(2031, 2, 10, 1, 15, 20), count: 3 });
    expect(iso(secondly.all())).toEqual([
      "2031-02-10T01:15:20.000Z",
      "2031-02-10T01:16:00.000Z",
      "2031-02-10T01:16:40.000Z",
    ]);
  });

  test("an occurrence equal to until is included and nothing after it", () => {
    /** Verifies: RRULE-EXP-009 */
    const rule = new RRule({ freq: RRule.DAILY, dtstart: datetime(2031, 2, 26, 7, 0, 0), until: datetime(2031, 3, 2, 7, 0, 0) });
    expect(iso(rule.all())).toEqual([
      "2031-02-26T07:00:00.000Z",
      "2031-02-27T07:00:00.000Z",
      "2031-02-28T07:00:00.000Z",
      "2031-03-01T07:00:00.000Z",
      "2031-03-02T07:00:00.000Z",
    ]);
  });

  test("a monthly rule pinned to the 31st skips shorter months", () => {
    /** Verifies: RRULE-EXP-002, RRULE-NRM-005 */
    const rule = new RRule({ freq: RRule.MONTHLY, dtstart: datetime(2031, 1, 31, 8, 0, 0), count: 4 });
    expect(iso(rule.all())).toEqual([
      "2031-01-31T08:00:00.000Z",
      "2031-03-31T08:00:00.000Z",
      "2031-05-31T08:00:00.000Z",
      "2031-07-31T08:00:00.000Z",
    ]);
  });
});

describe("string primitives", () => {
  test("toString emits DTSTART and only caller-supplied rule properties", () => {
    /** Verifies: RRULE-STR-001 */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 0, 0), count: 5, byweekday: [RRule.TU, RRule.FR] });
    expect(rule.toString()).toBe("DTSTART:20310304T090000Z\nRRULE:FREQ=WEEKLY;COUNT=5;BYDAY=TU,FR");
  });

  test("explicitly supplied default values still serialize", () => {
    /** Verifies: RRULE-STR-002 */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 1, 6, 9, 0, 0), interval: 1, wkst: RRule.MO, count: 2 });
    expect(rule.toString()).toBe("DTSTART:20310106T090000Z\nRRULE:FREQ=WEEKLY;INTERVAL=1;WKST=MO;COUNT=2");
  });

  test("ordinal weekdays, negative month days and numeric wkst serialize as tokens", () => {
    /** Verifies: RRULE-STR-003 */
    const nth = new RRule({ freq: RRule.MONTHLY, dtstart: datetime(2031, 1, 1, 8, 0, 0), byweekday: RRule.FR.nth(2), count: 3 });
    expect(nth.toString()).toBe("DTSTART:20310101T080000Z\nRRULE:FREQ=MONTHLY;BYDAY=+2FR;COUNT=3");
    const neg = new RRule({ freq: RRule.MONTHLY, dtstart: datetime(2031, 1, 1, 9, 0, 0), bymonthday: [4, -3], count: 4 });
    expect(neg.toString()).toBe("DTSTART:20310101T090000Z\nRRULE:FREQ=MONTHLY;BYMONTHDAY=4,-3;COUNT=4");
    const wnum = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 1, 6, 9, 0, 0), wkst: 3, count: 2 });
    expect(wnum.toString()).toBe("DTSTART:20310106T090000Z\nRRULE:FREQ=WEEKLY;WKST=TH;COUNT=2");
  });

  test("optionsToString serializes an options object directly", () => {
    /** Verifies: RRULE-STR-004 */
    expect(RRule.optionsToString({ freq: RRule.MONTHLY, interval: 3, bymonthday: 7 })).toBe(
      "RRULE:FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=7",
    );
  });

  test("a rule constructed without dtstart emits no DTSTART line", () => {
    /** Verifies: RRULE-STR-001 */
    expect(RRule.fromString("FREQ=DAILY;COUNT=2").toString()).toBe("RRULE:FREQ=DAILY;COUNT=2");
  });

  test("parseString reads a bare property list into partial options", () => {
    /** Verifies: RRULE-STR-005 */
    expect(RRule.parseString("FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=7")).toEqual({
      freq: RRule.MONTHLY,
      interval: 3,
      bymonthday: 7,
    });
  });

  test("parseString reads DTSTART and RRULE lines and date-only UNTIL as UTC midnight", () => {
    /** Verifies: RRULE-STR-005, RRULE-STR-006 */
    const parsed = RRule.parseString("DTSTART:20310304T090000Z\nRRULE:FREQ=WEEKLY;COUNT=5");
    expect(parsed.freq).toBe(RRule.WEEKLY);
    expect(parsed.count).toBe(5);
    expect(parsed.dtstart?.toISOString()).toBe("2031-03-04T09:00:00.000Z");
    const untilRule = RRule.fromString("DTSTART:20310301T000000Z\nRRULE:FREQ=DAILY;UNTIL=20310304");
    expect(untilRule.all()).toHaveLength(4);
    expect(untilRule.options.until?.toISOString()).toBe("2031-03-04T00:00:00.000Z");
  });

  test("unknown properties and malformed timestamps are rejected", () => {
    /** Verifies: RRULE-ERR-004, RRULE-ERR-005 */
    expect(() => RRule.parseString("XFREQ=1")).toThrow(Error);
    expect(() => RRule.fromString("garbage")).toThrow(Error);
    expect(() => RRule.fromString("DTSTART:notadate\nRRULE:FREQ=DAILY;COUNT=2")).toThrow(Error);
  });

  test("rrulestr picks RRule or RRuleSet from the input shape", () => {
    /** Verifies: RRULE-STR-007, RRULE-STR-008 */
    const single = rrulestr("DTSTART:20310304T090000Z\nRRULE:FREQ=WEEKLY;COUNT=5;BYDAY=TU,FR");
    expect(single).toBeInstanceOf(RRule);
    const multi = rrulestr("DTSTART:20310602T100000Z\nRRULE:FREQ=WEEKLY;COUNT=4;BYDAY=MO\nRDATE:20310620T150000Z");
    expect(multi).toBeInstanceOf(RRuleSet);
    const forced = rrulestr("DTSTART:20310602T100000Z\nRRULE:FREQ=DAILY;COUNT=2", { forceset: true });
    expect(forced).toBeInstanceOf(RRuleSet);
  });

  test("rrulestr merges its dtstart option into rules lacking DTSTART", () => {
    /** Verifies: RRULE-STR-008 */
    const rule = rrulestr("FREQ=DAILY;COUNT=2", { dtstart: datetime(2031, 9, 1, 5, 0, 0) });
    expect(iso(rule.all())).toEqual(["2031-09-01T05:00:00.000Z", "2031-09-02T05:00:00.000Z"]);
  });
});

describe("natural language primitives", () => {
  test("toText renders frequency, weekday list and count", () => {
    /** Verifies: RRULE-NLP-001 */
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 3, 4, 9, 0, 0), count: 5, byweekday: [RRule.TU, RRule.FR] });
    expect(rule.toText()).toBe("every week on Tuesday, Friday for 5 times");
  });

  test("toText covers interval, month-day, week-number and until families", () => {
    /** Verifies: RRULE-NLP-001, RRULE-NLP-002 */
    expect(new RRule({ freq: RRule.DAILY, interval: 3, dtstart: datetime(2031, 1, 1), count: 7 }).toText()).toBe(
      "every 3 days for 7 times",
    );
    const monthDay = new RRule({ freq: RRule.MONTHLY, bymonthday: [12], dtstart: datetime(2031, 1, 1) });
    expect(monthDay.toText()).toBe("every month on the 12th");
    expect(monthDay.isFullyConvertibleToText()).toBe(true);
    expect(new RRule({ freq: RRule.YEARLY, byweekno: 11, dtstart: datetime(2031, 1, 1) }).toText()).toBe(
      "every year in week 11",
    );
    expect(new RRule({ freq: RRule.WEEKLY, until: datetime(2031, 10, 1), dtstart: datetime(2031, 1, 2) }).toText()).toBe(
      "every week until October 1, 2031",
    );
  });

  test("parseText maps a phrase to partial options and null when uninterpretable", () => {
    /** Verifies: RRULE-NLP-003, RRULE-ERR-011 */
    expect(RRule.parseText("every day for 3 times")).toEqual({ freq: RRule.DAILY, count: 3 });
    expect(RRule.parseText("total gibberish here")).toBeNull();
  });

  test("fromText builds a weekday rule from a phrase", () => {
    /** Verifies: RRULE-NLP-004 */
    const rule = RRule.fromText("every weekday");
    expect(rule.toString()).toBe("RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR");
  });
});

describe("recurrence set primitives", () => {
  test("accessors reflect added sources", () => {
    /** Verifies: RRULE-SET-001 */
    const set = new RRuleSet();
    const rule = new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 6, 2, 10, 0, 0), count: 4, byweekday: [RRule.MO] });
    set.rrule(rule);
    set.rdate(datetime(2031, 6, 20, 15, 0, 0));
    set.exdate(datetime(2031, 6, 9, 10, 0, 0));
    expect(set.rrules()).toHaveLength(1);
    expect(set.exrules()).toHaveLength(0);
    expect(iso(set.rdates())).toEqual(["2031-06-20T15:00:00.000Z"]);
    expect(iso(set.exdates())).toEqual(["2031-06-09T10:00:00.000Z"]);
  });

  test("wrongly typed sources are rejected", () => {
    /** Verifies: RRULE-ERR-009, RRULE-ERR-010 */
    const set = new RRuleSet();
    expect(() => set.rrule("FREQ=DAILY" as unknown as RRule)).toThrow(Error);
    expect(() => set.exrule("FREQ=DAILY" as unknown as RRule)).toThrow(Error);
    expect(() => set.rdate("2031-01-01" as unknown as Date)).toThrow(Error);
    expect(() => set.exdate("2031-01-01" as unknown as Date)).toThrow(Error);
  });

  test("a dates-only set enumerates in ascending order", () => {
    /** Verifies: RRULE-SET-002 */
    const set = new RRuleSet();
    set.rdate(datetime(2031, 9, 5, 12, 0, 0));
    set.rdate(datetime(2031, 9, 1, 12, 0, 0));
    expect(iso(set.all())).toEqual(["2031-09-01T12:00:00.000Z", "2031-09-05T12:00:00.000Z"]);
    expect(set.toString()).toBe("RDATE:20310901T120000Z,20310905T120000Z");
  });

  test("valueOf lists the iCalendar lines of every source", () => {
    /** Verifies: RRULE-SET-003 */
    const set = new RRuleSet();
    set.rrule(new RRule({ freq: RRule.WEEKLY, dtstart: datetime(2031, 6, 2, 10, 0, 0), count: 4, byweekday: [RRule.MO] }));
    set.rdate(datetime(2031, 6, 20, 15, 0, 0));
    set.exdate(datetime(2031, 6, 9, 10, 0, 0));
    expect(set.valueOf()).toEqual([
      "DTSTART:20310602T100000Z",
      "RRULE:FREQ=WEEKLY;COUNT=4;BYDAY=MO",
      "RDATE:20310620T150000Z",
      "EXDATE:20310609T100000Z",
    ]);
    expect(set.toString()).toBe(set.valueOf().join("\n"));
  });
});
