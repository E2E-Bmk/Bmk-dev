// Oracle integration tests for the calendar recurrence engine
#![cfg(test)]
#![allow(clippy::all)]

use std::str::FromStr;

use chrono::{Datelike, TimeZone, Timelike};
use rrule::{Frequency, NWeekday, RRule, RRuleError, RRuleSet, Tz, Unvalidated, Weekday};

fn utc(y: i32, mo: u32, d: u32, h: u32, mi: u32, s: u32) -> chrono::DateTime<Tz> {
    Tz::UTC.with_ymd_and_hms(y, mo, d, h, mi, s).unwrap()
}

fn zdt(tz: Tz, y: i32, mo: u32, d: u32, h: u32, mi: u32, s: u32) -> chrono::DateTime<Tz> {
    tz.with_ymd_and_hms(y, mo, d, h, mi, s).unwrap()
}

fn pset(s: &str) -> RRuleSet {
    s.parse().unwrap()
}

/// Number of days in the month containing (year, month).
fn days_in_month(y: i32, m: u32) -> u32 {
    let (ny, nm) = if m == 12 { (y + 1, 1) } else { (y, m + 1) };
    chrono::NaiveDate::from_ymd_opt(ny, nm, 1)
        .unwrap()
        .signed_duration_since(chrono::NaiveDate::from_ymd_opt(y, m, 1).unwrap())
        .num_days() as u32
}

include!("all/round_trip.rs");
include!("all/streams.rs");
include!("all/selection.rs");
include!("all/zones.rs");
include!("all/errors_validation.rs");
