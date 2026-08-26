<!-- INTERNAL
task_id: rust-decimal-fullrepro-001
spec_version: v1
delta: initial version
source_boundary: docs.rs/rust_decimal 1.42.1 (crate root guide, Decimal/Error/RoundingStrategy item docs with examples and panic notes), README.md at tag 1.42.1; reference behavior observed by running the pinned checkout (three probe rounds: parse rounding mode at digit 29, arithmetic scale laws and banker's rounding at the representational cut, rescale vs round_dp rounding modes, division scale variability, Display precision truncation, serialize byte layout, float conversion dual forms, error variants and panic conditions)
-->

# Decimal Arithmetic Library Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`rust_decimal` is a fixed-point decimal number library for Rust built around a
single value type, `Decimal`, that represents numbers of the form
`m / 10^e`: a 96-bit unsigned integer mantissa `m`, a sign flag, and a scale
`e` between 0 and 28 inclusive. Because values are stored in base ten, the
type represents quantities such as monetary amounts exactly, without the
binary rounding error of floating point.

The library exposes one shared fact — the packed sign/mantissa/scale triple —
through several coordinated projections: construction from integers, strings,
scientific notation, and binary floats; exact arithmetic operators with
documented scale-propagation and overflow laws; a rounding toolkit with seven
selectable strategies plus scale-surgery operations (truncation, rescaling,
normalization); text rendering that preserves the scale as trailing zeros;
ordering, equality, and hashing that treat equal numeric values as
interchangeable regardless of scale; and conversions to and from Rust's
primitive integer and float types. Every projection must agree with every
other about the underlying number.

The installable crate name is `rust_decimal`. The crate builds as a plain
library with no build scripts and compiles on the stable Rust toolchain.

## Non-Goals

- This specification does not require arbitrary-precision arithmetic; the
  value domain is fixed at a 96-bit mantissa with scale 0 to 28.
- This specification does not require transcendental or algebraic
  mathematical functions (powers, roots, logarithms, exponentials, or
  trigonometry).
- This specification does not require serde serialization support, database
  driver integrations, random value generation, or archive/zero-copy
  frameworks.
- This specification does not require a literal macro for compile-time
  decimal construction.
- This specification does not require `no_std` operation; the standard
  library is available.
- This specification does not require deprecated compatibility aliases of any
  kind; only the members named in this document must exist.
- This specification does not define localized or currency-aware formatting;
  rendering uses `.` as the decimal separator and no grouping separators.

## Representative Workflows

Two workflows illustrate how the projections cooperate.

**Invoice rounding.** A billing routine parses user input, performs exact
arithmetic, and rounds only at the presentation edge:

```rust
use rust_decimal::prelude::*;

let unit_price = Decimal::from_str("24.95").unwrap();
let quantity = Decimal::from(3_u32);
let discount = Decimal::from_str("0.075").unwrap();

let gross = unit_price * quantity;              // 74.85, scale 2 (= 2 + 0)
let rebate = gross * discount;                  // 5.61375, scale 5 (= 2 + 3)
let net = gross - rebate;                       // exact, max operand scale
let payable = net.round_dp(2);                  // banker's rounding to cents

assert_eq!(gross.to_string(), "74.85");
assert_eq!(payable.scale(), 2);
```

The multiplication keeps the full product scale (sum of the operand scales),
the subtraction keeps the larger operand scale, and only `round_dp` reduces
precision — so no intermediate step loses information.

**Aggregation and canonical form.** A reporting routine sums a series,
normalizes trailing zeros, and produces both human and byte renderings:

```rust
use rust_decimal::prelude::*;

let entries = [
    Decimal::from_str("1.50").unwrap(),
    Decimal::from_str("2.25").unwrap(),
    Decimal::from_str("-0.75").unwrap(),
];
let total: Decimal = entries.iter().sum();      // 3.00, scale 2
let canonical = total.normalize();              // 3, scale 0

assert!(total == canonical);                    // equality ignores scale
assert_eq!(total.to_string(), "3.00");          // rendering preserves scale
assert_eq!(canonical.to_string(), "3");

let bytes = total.serialize();                  // 16-byte packed image
assert_eq!(Decimal::deserialize(bytes), total);
```

## Value Model and Construction

This section defines the representable domain and every way to build a
`Decimal`; all later sections describe projections of values built here.

**The packed value.** A `Decimal` stores a 96-bit unsigned mantissa (three
32-bit limbs), one sign flag, and a scale in `0..=28`. The numeric value is
`(-1)^sign * mantissa / 10^scale`. The largest representable mantissa is
`2^96 - 1 = 79228162514264337593543950335`. The associated constant
`Decimal::MAX_SCALE` is `28`. Two distinct packed images can denote the same
number (for example mantissa 10 at scale 1 and mantissa 1 at scale 0 both
denote one); comparison operations treat them as equal while rendering and
introspection expose the stored image. A zero mantissa with the sign flag set
is a valid image ("negative zero") that compares equal to zero.

**Constants.** The following associated constants must exist with exactly
these values: `ZERO` (0), `ONE` (1), `NEGATIVE_ONE` (-1), `TWO` (2), `TEN`
(10), `ONE_HUNDRED` (100), `ONE_THOUSAND` (1000), `MAX`
(`79228162514264337593543950335`), and `MIN` (`-79228162514264337593543950335`).
`Decimal::default()` returns zero.

**Integer construction.** `new` accepts a signed 64-bit mantissa and a scale
and returns the value `mantissa / 10^scale`; if the scale exceeds 28 it
panics. `try_new` accepts the same arguments and returns
`Err(Error::ScaleExceedsMaximumPrecision(scale))` instead of panicking.
`from_i128_with_scale` accepts a signed 128-bit mantissa and a scale and
panics when the scale exceeds 28 or the mantissa magnitude exceeds the 96-bit
domain; `try_from_i128_with_scale` returns
`Err(Error::ScaleExceedsMaximumPrecision(..))` for a bad scale,
`Err(Error::ExceedsMaximumPossibleValue)` for a mantissa above the maximum,
and `Err(Error::LessThanMinimumPossibleValue)` for a mantissa below the
negated maximum. `from_parts` assembles a value directly from the three
32-bit limbs (`lo`, `mid`, `hi`), a `negative` flag, and a scale; for example
`from_parts(1, 2, 3, false, 4)` is `5534023222971858.9441`, i.e.
`(3·2^64 + 2·2^32 + 1) / 10^4`.

**From integers.** `Decimal` implements `From` for every primitive integer
type (`i8` through `i128`, `u8` through `u128`, `isize`, `usize`). The
conversion is exact with scale 0. When a 128-bit source value lies outside
the representable domain the `From` conversion panics; the fallible
counterparts on the conversion surface (see Conversions) return `None` or an
error instead.

## String Parsing and Rendering

This section defines the four parsing entry points and the text output
rules; parsing and rendering must round-trip for canonically formatted
input.

**Standard parsing.** `Decimal` implements `FromStr`, and `TryFrom<&str>`
behaves identically. The accepted grammar is: an optional `+` or `-` sign,
digits with optional embedded `_` separators (an underscore must not be the
first character), at most one `.` radix point, and an optional scientific
suffix `e` or `E` with an optionally signed exponent. `".5"` parses as `0.5`;
`"5."` parses as `5` with scale 0. The scale of the parsed value equals the
number of fractional digits written (`"0.500"` has scale 3), and a parsed
`"-0"` renders as `0` with a positive sign. WHEN the input carries more than
28 fractional digits THEN the value must be rounded to scale 28 using
midpoint-away-from-zero rounding at the 29th digit: `"0.00000000000000000000000000025"`
parses as `0.0000000000000000000000000003`. WHEN a scientific suffix is
present THEN the mantissa is shifted by the exponent
(`"1.2e3"` → `1200`, `"1.2e-2"` → `0.012`); an exponent that moves the value
outside the representable scale domain fails with
`Error::ScaleExceedsMaximumPrecision(..)`. Failure paths: an empty string, a
bare sign, a string with two radix points, or any character outside the
grammar must return an `Err` whose variant is `Error::ErrorString(..)`; an
integer part whose digits exceed the 96-bit mantissa domain must also return
`Err(Error::ErrorString(..))`.

**Exact parsing.** `from_str_exact` accepts the same grammar but never
rounds: WHEN the input has more than 28 fractional digits and the excess
digits are not all zero THEN it returns `Err(Error::Underflow)`. Underscores
remain legal: `"0.00000_00000_00000_00000_00000_001"` parses exactly to
`0.0000000000000000000000000001`.

**Radix parsing.** `from_str_radix` parses a string of digits in a base
between 2 and 36, where digits beyond `9` are the letters `a`-`z` or `A`-`Z`:
`from_str_radix("ff", 16)` is `255`, `from_str_radix("1011", 2)` is `11`, and
`from_str_radix("zz", 36)` is `1295`. Radix 10 behaves exactly like
`FromStr`. A radix below 2 or above 36 and a digit outside the radix each
return `Err(Error::ErrorString(..))`.

**Scientific parsing.** `from_scientific` requires the exponent form: a
decimal significand, a mandatory `e` or `E`, and an optionally signed integer
exponent. `from_scientific("9.7e-7")` is `0.00000097`;
`from_scientific("1.23e3")` is `1230` with scale 0; `from_scientific("5e28")`
is `50000000000000000000000000000`. WHEN the input has no exponent marker
THEN the call fails with `Err(Error::ErrorString(..))`. WHEN the resulting
scale would exceed 28 THEN the call fails with
`Err(Error::ScaleExceedsMaximumPrecision(..))`: `from_scientific("5e-30")` is
an error. `from_scientific_lossy` behaves the same except that WHEN the
significand itself carries more fractional digits than fit after applying
the exponent THEN excess digits are discarded by rounding instead of failing
(`"1.234567890123456789012345678901e-5"` parses to
`0.0000123456789012345678901235`); a bare exponent overflow such as `"5e-30"`
still fails with `ScaleExceedsMaximumPrecision`.

**Rendering.** The `Display` implementation prints the sign, the integer
digits, and — when the scale is nonzero — a `.` followed by exactly `scale`
fractional digits, preserving trailing zeros: parsing `"1.50"` and printing
it yields `"1.50"`. `Debug` output equals `Display` output. `to_string` and
`Display` agree, and `array_string` returns a stack-allocated value whose
`as_ref()` string equals `to_string()`. WHEN a format precision is supplied
THEN the fractional part is truncated toward zero to that many digits if the
stored scale is larger (`{:.1}` of `1.29` is `1.2`, `{:.0}` of `1.99` is `1`)
and padded with trailing zeros if the stored scale is smaller (`{:.4}` of
`1.25` is `1.2500`). Width, fill, and alignment format options apply to the
rendered text. A value whose sign flag is set renders with a leading `-`
even when the mantissa is zero. The `LowerExp` (`{:e}`) and `UpperExp`
(`{:E}`) implementations render normalized scientific form: one leading
nonzero digit (or `0` for zero) before the point, the significant fractional
digits, and an `e`/`E` exponent — `12345.678` renders as `1.2345678e4`,
`0.00123` as `1.23e-3`, `1` as `1e0`, and `0` as `0e0`.

## Arithmetic and Scale Propagation

This section defines the binary operators, their scale laws, and the
checked, saturating, and aggregate forms. All operator families project the
same underlying computation: the checked form returns `None` exactly when
the operator form panics, and the saturating form replaces those failures
with `MAX` or `MIN`.

**Addition and subtraction.** The exact sum or difference is computed after
aligning both operands to the larger scale; the result scale is the larger
of the two operand scales (`2.50 + 1.235` is `3.735` with scale 3;
`1.5 - 1.50` is `0.00` with scale 2). WHEN the exact result cannot be
represented at that scale THEN the scale is reduced digit by digit, rounding
at each dropped digit with midpoint-nearest-even rounding, until the
mantissa fits; WHEN the result does not fit even at scale 0 THEN `+`/`-`
panic, `checked_add`/`checked_sub` return `None`, and
`saturating_add`/`saturating_sub` return `MAX` (positive overflow) or `MIN`
(negative overflow). `Decimal::MAX + Decimal::from_str("0.4").unwrap()`
rounds back to `MAX`, while adding `0.5` to `MAX` panics.

**Multiplication.** The exact product is computed; the result scale is the
sum of the operand scales (`2.5 * 1.25` is `3.125` with scale 3). WHEN the
exact product needs more than 28 fractional digits or does not fit in the
96-bit mantissa THEN excess low-order digits are removed with
midpoint-nearest-even rounding (`0.6666666666666666666666666666 * 0.3` is
`0.2000000000000000000000000000`;
`0.0000000000000000000000000005 * 0.5` is `0.0000000000000000000000000002`,
the even neighbor). WHEN the integral magnitude itself exceeds the domain
THEN `*` panics, `checked_mul` returns `None`, and `saturating_mul` returns
`MAX` or `MIN` by the sign of the true product.

**Division.** WHEN the divisor is nonzero THEN the quotient is computed
exactly when it is representable; otherwise digits are produced to the
maximal representable precision and the last kept digit is rounded with
midpoint-nearest-even rounding (`2 / 3` is `0.6666666666666666666666666667`;
`1 / 7` is `0.1428571428571428571428571429`). The numeric value of the
quotient is the contract; the trailing-zero scale of an exact quotient is an
artifact of the long-division loop and is not specified, so consumers
compare quotients by value (for example `10 / 4 == 2.5` holds even though
the stored scale can differ from 1). WHEN the divisor is zero THEN `/`
panics and `checked_div` returns `None`. WHEN the quotient's integral part
overflows THEN `/` panics and `checked_div` returns `None`.

**Remainder.** `%` returns the remainder after truncated division: the
result takes the sign of the dividend and the scale is the larger operand
scale (`-7 % 3` is `-1`; `7.25 % 0.5` is `0.25` with scale 2;
`5.00 % 3` is `2.00` with scale 2; WHEN the dividend magnitude is smaller
than the divisor magnitude THEN the dividend is returned unchanged). WHEN
the divisor is zero THEN `%` panics and `checked_rem` returns `None`.

**Operator forms.** `Add`, `Sub`, `Mul`, `Div`, `Rem`, and unary `Neg` are
implemented for owned values and references in every combination, and the
compound assignment forms (`+=`, `-=`, `*=`, `/=`, `%=`) must behave exactly
like the binary operator followed by assignment. Unary negation flips the
sign flag without changing mantissa or scale, including on zero (negating
zero yields a negative-zero image that still compares equal to zero).

**Aggregation.** `Decimal` implements `Sum` and `Product` over both owned
values and references: an empty sum is `ZERO`, an empty product is `ONE`,
and each step follows the corresponding operator's law, including its panic
on overflow.

**Inherent checked/saturating surface.** The methods `checked_add`,
`checked_sub`, `checked_mul`, `checked_div`, `checked_rem`,
`saturating_add`, `saturating_sub`, and `saturating_mul` are callable
directly on `Decimal` values.

## Rounding and Scale Surgery

This section defines every operation that changes the stored scale or
discards precision deliberately. All rounding operations only ever reduce
precision — WHEN the requested precision is greater than or equal to the
stored scale THEN the value is returned unchanged with its stored scale
(rounding never pads with zeros).

**Strategy-free rounding.** `round()` rounds to scale 0 with
midpoint-nearest-even (banker's) rounding: `6.5` rounds to `6`, `7.5` to
`8`, `-6.5` to `-6`, and `2.8` to `3`. `round_dp(dp)` rounds to `dp` decimal
places with the same strategy: `1.25` at one place is `1.2`, `1.35` at one
place is `1.4`. `round_dp(dp)` must equal
`round_dp_with_strategy(dp, RoundingStrategy::MidpointNearestEven)` for all
inputs.

**Strategies.** `round_dp_with_strategy` accepts a `RoundingStrategy` with
exactly seven usable variants; for a first dropped digit below or above the
midpoint every midpoint strategy agrees with ordinary nearest rounding, and
the variants differ as follows (shown rounding `2.35`, `-2.35`, `2.34`,
`-2.34` to one decimal place):

| Variant | 2.35 | -2.35 | 2.34 | -2.34 |
|---|---|---|---|---|
| `MidpointNearestEven` | 2.4 | -2.4 | 2.3 | -2.3 |
| `MidpointAwayFromZero` | 2.4 | -2.4 | 2.3 | -2.3 |
| `MidpointTowardZero` | 2.3 | -2.3 | 2.3 | -2.3 |
| `ToZero` | 2.3 | -2.3 | 2.3 | -2.3 |
| `AwayFromZero` | 2.4 | -2.4 | 2.4 | -2.4 |
| `ToNegativeInfinity` | 2.3 | -2.4 | 2.3 | -2.4 |
| `ToPositiveInfinity` | 2.4 | -2.3 | 2.4 | -2.3 |

`MidpointNearestEven` and `MidpointAwayFromZero` differ only when the
dropped tail is exactly one half: `2.45` to one place is `2.4` under
nearest-even and `2.5` under away-from-zero. `MidpointTowardZero` moves an
exact half toward zero but still rounds a tail above one half upward
(`2.451` to one place is `2.5`).

**Significant figures.** `round_sf(digits)` rounds to the given number of
significant figures using banker's rounding and returns an `Option`:
`123.456` at 2 significant figures is `120`; `0.00123` at 2 is `0.0012`;
`999` at 1 is `1000`; `-123.456` at 4 is `-123.5`. WHEN `digits` is zero
THEN the result is `Some(ZERO)`. WHEN the value is zero THEN the result is
`Some(ZERO)` for any digit count. WHEN the requested figures exceed the
significant digits present THEN the value is padded with trailing
fractional zeros where the scale domain allows (`123.456` at 9 renders
`123.456000`). WHEN rounding up would carry the value outside the
representable domain THEN the result is `None` (`Decimal::MAX.round_sf(1)`
is `None`). `round_sf_with_strategy` applies the same procedure under any of
the seven strategies (`987` at 1 significant figure with `ToZero` is `900`).

**Truncation.** `trunc()` drops the entire fractional part and returns
scale 0 (`2.8` → `2`, `-2.8` → `-2`). `trunc_with_scale(scale)` truncates
toward zero to the requested scale (`129.845` at scale 1 is `129.8`); WHEN
the requested scale is at or above the stored scale THEN the stored digits
are kept and padded with trailing zeros to the requested scale (`1.2` at
scale 5 renders `1.20000`, and `5` at scale 2 renders `5.00`). `fract()`
returns the value minus its truncation, keeping the sign of the source
(`-2.8.fract()` is `-0.8`); the fraction of an integer is `0` at scale 0.

**Floor and ceiling.** `floor()` rounds toward negative infinity and
`ceil()` toward positive infinity, both returning scale 0: `2.8.floor()` is
`2`, `-2.8.floor()` is `-3`, `2.1.ceil()` is `3`, `-2.1.ceil()` is `-2`.

**Rescaling.** `rescale(scale)` mutates the value to the requested scale.
WHEN the requested scale is larger THEN zeros are appended (`1.25` rescaled
to 4 renders `1.2500`), clamped so the mantissa still fits: a request beyond
what the mantissa can carry stops at the largest achievable scale (`1.25`
rescaled to 99 stops at scale 28), and a mantissa with no headroom keeps its
current scale. WHEN the requested scale is smaller THEN the value is
rounded with midpoint-away-from-zero rounding — unlike `round_dp`:
`1.25` rescaled to 1 is `1.3`, and `-1.25` rescaled to 1 is `-1.3`.

**Scale reinterpretation.** `set_scale(scale)` does not preserve the numeric
value: it reinterprets the existing mantissa under a new scale, moving the
radix point (`1.2345` after `set_scale(2)` is `123.45`). WHEN the requested
scale exceeds 28 THEN it returns
`Err(Error::ScaleExceedsMaximumPrecision(scale))` and leaves the value
unchanged; otherwise it returns `Ok(())`.

**Normalization.** `normalize()` returns the canonical image of the value:
trailing fractional zeros are stripped (`1.2500` → `1.25` at scale 2;
`100` stays scale 0), zero normalizes to positive zero at scale 0 regardless
of its stored scale or sign flag, and the numeric value never changes.
`normalize_assign()` applies the same transformation in place.

## Introspection, Ordering, and Conversion

This section defines how a value's stored image is observed and how values
cross into and out of primitive types.

**Image accessors.** `scale()` returns the stored scale. `mantissa()`
returns the signed 128-bit mantissa including the sign
(`-0.123456` → `-123456`). `unpack` is not part of the public surface; the
observable image is `scale`, `mantissa`, and the sign predicates.
`is_zero()` is true when the mantissa is zero at any scale. `is_integer()`
is true when the fractional part is zero, ignoring trailing zeros
(`1.000` is an integer; `1.1` is not). `is_sign_negative()` and
`is_sign_positive()` report the sign flag — note that a stored negative zero
reports a negative sign while still comparing equal to zero.
`set_sign_positive(bool)` and `set_sign_negative(bool)` mutate the sign
flag. `abs()` clears the sign; `signum()` returns `1`, `0`, or `-1` (zero of
either sign returns `0`). `max(other)` and `min(other)` return the larger or
smaller value by numeric comparison.

**Equality, ordering, hashing.** `PartialEq`/`Eq`, `PartialOrd`/`Ord`, and
`Hash` all operate on the numeric value, not the stored image: `1.0`,
`1.00`, and `1.000` are equal, hash identically, and compare `Equal`;
negative zero equals zero. Ordering is the total numeric order
(`3 > 2.9999`, `-1 > -2`).

**Byte image.** `serialize()` returns a 16-byte array: four flag bytes
(byte 0 and byte 1 zero, byte 2 the scale, byte 3 holding `0x80` for a
negative sign and `0x00` otherwise) followed by the mantissa limbs `lo`,
`mid`, and `hi`, each little-endian. `1.25` serializes to
`[0,0,2,0, 125,0,0,0, 0,0,0,0, 0,0,0,0]` and `-1.25` flips byte 3 to `128`.
`deserialize(bytes)` reverses the mapping; `deserialize(x.serialize())`
must reproduce both the value and the stored image (scale and sign) of `x`.

**To primitives.** The conversion trait surface reachable through the
prelude provides `to_i8` … `to_i128`, `to_u8` … `to_u128`, `to_isize`,
`to_usize`, `to_f32`, and `to_f64`, each returning an `Option`. Integer
targets truncate toward zero (`2.99.to_i64()` is `Some(2)`,
`(-2.99).to_i64()` is `Some(-2)`) and return `None` when the truncated value
does not fit (`(-1).to_u64()` is `None`; `Decimal::MAX.to_i32()` is `None`).
Float targets return the nearest binary float (`0.1.to_f64()` is
`Some(0.1)`). `TryFrom<Decimal>` exists for the same primitive targets and
returns `Err(Error::ConversionTo(..))` where the trait method returns
`None`. The infallible forms `as_i128` (truncates toward zero) and `as_f64`
must equal the trait results where those are `Some`.

**From primitives.** The prelude's `FromPrimitive` surface provides
`from_i8` … `from_i128`, `from_u8` … `from_u128`, `from_isize`,
`from_usize`, `from_f32`, and `from_f64`, each returning `Option<Decimal>`.
Integer sources succeed exactly when the value fits the 96-bit domain
(`from_i128(i128::MAX)` is `None`). Float sources return `None` for NaN,
infinities, and out-of-range magnitudes. WHEN a finite float's shortest
decimal rendering has at most 15 significant digits THEN `from_f32`/
`from_f64` (and `TryFrom<f32>`/`TryFrom<f64>`, which return
`Err(Error::ConversionTo(..))` where the trait returns `None`) must produce
exactly that shortest decimal value: `from_f64(0.1)` is `0.1` and
`Decimal::try_from(2.132_f64)` is `2.132`. The `from_f32_retain` and
`from_f64_retain` associated functions instead preserve the full binary
expansion of the float, truncated to the 28-place scale domain:
`from_f64_retain(0.1)` is `0.1000000000000000055511151231` and
`from_f32_retain(0.1)` is `0.100000001490116119384765625`.

**Trait constants.** The prelude's `Zero` and `One` traits are implemented:
`Decimal::zero()` equals `ZERO` and `is_zero()` agrees with it;
`Decimal::one()` equals `ONE` and `is_one()` is true exactly for values
equal to one. The prelude's `Signed` trait surface (`abs`, `signum`,
`is_positive`/`is_negative` on the trait) agrees with the inherent members
described above.

## State Model

The library holds no global state. Every fact lives in individual `Decimal`
values: one packed image of sign, 96-bit mantissa, and scale. The public
projections of that image are:

1. **numeric value** — `mantissa() / 10^scale()` with the sign applied; the
   basis for `==`, `Ord`, `Hash`, `max`/`min`, `signum`, and all arithmetic;
2. **stored image** — `scale()`, `mantissa()`, sign predicates, `serialize`
   bytes, and `Display`/`Debug`/`array_string` rendering with trailing
   zeros;
3. **canonical image** — the result of `normalize()`, the unique minimal-
   scale image of the numeric value with positive zero;
4. **primitive views** — the `to_*`/`as_*` conversions and `TryFrom`
   projections into Rust integers and floats;
5. **text round trip** — `FromStr`/`from_str_exact`/`from_scientific` back
   into images, with documented rounding at the representational boundary.

Mutating operations (`rescale`, `set_scale`, `set_sign_*`,
`normalize_assign`, compound assignment) rewrite the packed image in place;
all other operations return new values and leave their receiver unchanged.

## Error Semantics

The error type `Error` implements `Clone`, `Debug`, `PartialEq`, `Display`,
and `std::error::Error`, and the crate exports a `Result<T>` alias bound to
it. Variants and their producers:

| Condition | Result |
|---|---|
| Parse failure in the decimal grammar (empty input, no digits, two radix points, bad character, leading underscore, integer overflow in digits, missing exponent for `from_scientific`, unsupported radix, digit outside radix) | `Error::ErrorString(message)` |
| Mantissa above `MAX` in checked i128 construction | `Error::ExceedsMaximumPossibleValue` |
| Mantissa below `MIN` in checked i128 construction | `Error::LessThanMinimumPossibleValue` |
| More than 28 fractional digits in `from_str_exact` with nonzero excess | `Error::Underflow` |
| Scale above 28 in `try_new`, `try_from_i128_with_scale`, `set_scale`, or an exponent shifting past the scale domain in parsing | `Error::ScaleExceedsMaximumPrecision(scale)` |
| Failed `TryFrom` conversion between `Decimal` and a primitive | `Error::ConversionTo(type_name)` |

The `Display` renderings of the typed variants are fixed strings:
`ExceedsMaximumPossibleValue` renders
`Number exceeds maximum value that can be represented.`;
`LessThanMinimumPossibleValue` renders
`Number less than minimum value that can be represented.`; `Underflow`
renders `Number has a high precision that can not be represented.`;
`ScaleExceedsMaximumPrecision(s)` renders
`Scale exceeds the maximum precision allowed: {s} > 28`; `ConversionTo(t)`
renders `Error while converting to {t}`; `ErrorString(m)` renders the
message itself. The message payload of `ErrorString` is unspecified beyond
being non-empty.

Panics are part of the contract at exactly these points: `new` and
`from_i128_with_scale` with out-of-domain arguments; `+`, `-`, `*` (and
their assignment forms, `Sum`, and `Product`) on overflow past `MAX`/`MIN`;
`/` and `%` with a zero divisor; `/` on integral overflow; `From` integer
conversion of an unrepresentable 128-bit value.

## Cross-View Invariants

1. For every value parsed from a canonical decimal string (no sign edge
   cases, underscores, or exponent), `to_string()` must return exactly the
   input, and re-parsing that rendering must reproduce both the value and
   the scale — parse and render are mutually inverse on canonical images.
2. WHEN two values compare equal (`a == b`) THEN their hashes must be equal,
   `a.cmp(&b)` must be `Equal`, and `a.normalize()` and `b.normalize()`
   must render identical strings, regardless of the stored scales.
3. For every pair `(a, b)` and every binary operation, the checked method
   must return `Some(v)` exactly when the operator produces `v` without
   panicking, and `None` exactly when the operator panics; on overflow
   `None` cases for `+`, `-`, and `*`, the saturating method must return
   `MAX` when the true result lies above `MAX` and `MIN` when it lies
   below.
4. `deserialize(v.serialize())` must reproduce `v`'s numeric value, stored
   scale, and sign flag, and its `to_string()` must equal `v.to_string()` —
   the byte image and the text image project the same stored image.
5. `round_dp(dp)` must equal
   `round_dp_with_strategy(dp, MidpointNearestEven)` for every value and
   every `dp`, and `round()` must equal `round_dp(0)`.
6. For every nonzero divisor where `a % b` and the truncated quotient
   `q = (a / b).trunc()` are exact, `q * b + (a % b)` must equal `a`, and
   the remainder's sign must equal the dividend's sign or be zero.
7. `normalize()` never changes the numeric value: for every `v`,
   `v.normalize() == v`, `v.normalize().scale()` is the minimal scale among
   equal images, and `v.normalize().normalize()` equals `v.normalize()`
   (idempotence).
8. `mantissa()` and `scale()` determine rendering: for every value,
   re-constructing through `try_from_i128_with_scale(v.mantissa(),
   v.scale())` must yield a value whose `to_string()` equals
   `v.to_string()`.

## Public Interface

### Import Surface

```rust
// crate root
use rust_decimal::{Decimal, Error, Result, RoundingStrategy};

// prelude: the intended one-line import for applications
use rust_decimal::prelude::*;
// re-exports: Decimal, RoundingStrategy,
//             core::str::FromStr,
//             and the numeric conversion traits FromPrimitive, One,
//             Signed, ToPrimitive, Zero
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Decimal` | struct | 96-bit fixed-point decimal value; `Copy`, `Clone`, `Default`, `Send`, `Sync` |
| `RoundingStrategy` | enum | rounding selector: `MidpointNearestEven`, `MidpointAwayFromZero`, `MidpointTowardZero`, `ToZero`, `AwayFromZero`, `ToNegativeInfinity`, `ToPositiveInfinity` |
| `Error` | enum | library error: `ErrorString`, `ExceedsMaximumPossibleValue`, `LessThanMinimumPossibleValue`, `Underflow`, `ScaleExceedsMaximumPrecision`, `ConversionTo` |
| `Result` | type alias | `core::result::Result<T, rust_decimal::Error>` |
| `prelude` | module | re-export bundle for applications |
| `Decimal::ZERO` / `ONE` / `NEGATIVE_ONE` / `TWO` / `TEN` / `ONE_HUNDRED` / `ONE_THOUSAND` | const | small constants |
| `Decimal::MAX` / `MIN` | const | domain bounds |
| `Decimal::MAX_SCALE` | const | 28 |
| `Decimal::new` / `try_new` | fn | i64 mantissa + scale construction |
| `Decimal::from_i128_with_scale` / `try_from_i128_with_scale` | fn | i128 mantissa + scale construction |
| `Decimal::from_parts` | fn | limb-level construction |
| `Decimal::from_scientific` / `from_scientific_lossy` | fn | exponent-form parsing |
| `Decimal::from_str_exact` | fn | non-rounding parse |
| `Decimal::from_str_radix` | fn | radix 2–36 parse |
| `Decimal::from_f32_retain` / `from_f64_retain` | fn | full-precision float conversion |
| `Decimal::scale` / `mantissa` | fn | stored-image accessors |
| `Decimal::is_zero` / `is_integer` / `is_sign_negative` / `is_sign_positive` | fn | predicates |
| `Decimal::set_sign_positive` / `set_sign_negative` | fn | sign mutation |
| `Decimal::set_scale` / `rescale` | fn | scale mutation |
| `Decimal::normalize` / `normalize_assign` | fn | canonical image |
| `Decimal::trunc` / `trunc_with_scale` / `fract` | fn | truncation family |
| `Decimal::floor` / `ceil` | fn | directed integer rounding |
| `Decimal::abs` / `signum` / `max` / `min` | fn | magnitude and selection |
| `Decimal::round` / `round_dp` / `round_dp_with_strategy` | fn | decimal-place rounding |
| `Decimal::round_sf` / `round_sf_with_strategy` | fn | significant-figure rounding |
| `Decimal::checked_add` / `checked_sub` / `checked_mul` / `checked_div` / `checked_rem` | fn | non-panicking arithmetic |
| `Decimal::saturating_add` / `saturating_sub` / `saturating_mul` | fn | clamping arithmetic |
| `Decimal::serialize` / `deserialize` | fn | 16-byte packed image |
| `Decimal::array_string` | fn | allocation-free rendering |
| `Decimal::as_i128` / `as_f64` | fn | infallible conversions |
| `FromStr` / `TryFrom<&str>` for `Decimal` | trait impl | standard parsing |
| `Display` / `Debug` / `LowerExp` / `UpperExp` for `Decimal` | trait impl | rendering |
| `From<integer>` for `Decimal` | trait impl | exact integer conversion (all primitive integer types) |
| `TryFrom<f32>` / `TryFrom<f64>` for `Decimal` | trait impl | fallible float conversion |
| `TryFrom<Decimal>` for primitives | trait impl | fallible narrowing (`ConversionTo` on failure) |
| `Add` / `Sub` / `Mul` / `Div` / `Rem` / `Neg` and assign forms | trait impl | operators over values and references |
| `Sum` / `Product` (owned and `&Decimal`) | trait impl | iterator aggregation |
| `PartialEq` / `Eq` / `PartialOrd` / `Ord` / `Hash` | trait impl | value-based comparison |
| `FromPrimitive` / `ToPrimitive` / `Zero` / `One` / `Signed` for `Decimal` | trait impl | prelude conversion traits |

### CLI Entry Points

There is no executable in this package. All functionality is consumed as a
library through the imports above.

## Appendix A: Environment

The working environment runs the stable Rust toolchain 1.83 (edition 2021)
on Linux. Crate dependencies declared in the project manifest are resolved
from the standard registry when the project is first built; the numeric
trait crate `num-traits` 0.2 and the small-vector crate `arrayvec` 0.7 are
known-compatible choices for supporting the prelude's conversion traits.
The delivered crate must be named `rust_decimal`, must build as a plain
library with `cargo build` on this toolchain without nightly features or
build scripts, and must not require enabling any cargo feature for the
behavior in this document.

## Appendix B: Assessment Notes

Assessment exercises the public surface described in this document.
Dimensions covered: construction and parsing (all four entry points,
rounding versus exact versus lossy boundaries, error variants), arithmetic
scale propagation and the checked/saturating/operator agreement, the seven
rounding strategies and the scale-surgery family, rendering (trailing-zero
preservation, precision truncation and padding, exponent forms), value
equality versus stored image (equality/order/hash across scales,
normalization), byte-image round trips, and primitive conversions in both
directions. Tests call the library exactly as a consuming application
would: through `rust_decimal::prelude::*` and the crate-root names, with no
access to internals. Expected values in tests are fixed decimal literals
and strings; scoring counts passing tests, with composition scenarios that
chain several projections weighted alongside single-behavior checks.
