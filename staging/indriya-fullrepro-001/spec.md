# Measurement Quantities and Units Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`indriya` is a units-of-measurement library for the JVM that implements the standard Java measurement API (`javax.measure`). Callers create quantities — a numeric value bound to a unit and a measurement scale — through one static factory, and then compute with them: quantity arithmetic composes units dimensionally, conversions move values between compatible units including offset scales such as Celsius, and comparisons distinguish strict equality from cross-unit equivalence. A built-in system of units supplies the SI base and derived units as constants, metric prefixes build scaled units, and unit algebra (multiply, divide, pow, root, shift) constructs arbitrary derived units with full dimensional bookkeeping.

Numeric fidelity is a design commitment: arithmetic is performed exactly rather than in binary floating point, so decimal sums like 0.1 + 0.2 produce exactly 0.3, a third of a metre multiplied by three is exactly one metre, and integer values stay integers through exact operations. Formatting support renders quantities and units to their text forms and parses them back.

The installable artifact is the Maven coordinate `tech.units:indriya`. The measurement API artifact (`javax.measure:unit-api`) and its small support library (`tech.uom.lib:uom-lib-common`) are separate compile dependencies that the library implements against.

## Non-Goals

- This specification does not require locale-sensitive, EBNF, or delimiter-configurable formatting facilities beyond the simple format classes named here.
- This specification does not require service-provider (SPI) wiring, format service lookup, or `ServiceLoader` integration.
- This specification does not require mixed-radix quantities, quantity ranges, or the array-based factory overloads.
- This specification does not require non-metric unit systems (imperial, US customary) or binary prefixes.
- This specification does not define the internal numeric representation; assessments observe values only through the `Number` views (`doubleValue`, `intValue`), string forms, and the comparison operations.
- This specification does not define thread-safety guarantees beyond the immutability of quantities and units.

## Representative Workflows

**Create, convert, and compare quantities.**

```java
ComparableQuantity<Length> distance = Quantities.getQuantity(1, MetricPrefix.KILO(Units.METRE));
distance.getValue();                       // 1
distance.getScale();                       // Scale.ABSOLUTE

ComparableQuantity<Length> inMetres = distance.to(Units.METRE);
inMetres.getValue();                       // 1000 (exact — stays integral)

Quantity<Length> metres = Quantities.getQuantity(1000, Units.METRE);
distance.equals(metres);                   // false — different units
distance.isEquivalentTo(metres);           // true  — same measure
distance.compareTo(metres);                // 0
```

**Arithmetic with dimensional composition and formatting.**

```java
ComparableQuantity<Length> len = Quantities.getQuantity(10, Units.METRE);
ComparableQuantity<?> speed = len.divide(Quantities.getQuantity(2, Units.SECOND));
speed.getUnit();                           // equals Units.METRE.divide(Units.SECOND)
speed.toString();                          // "5 m/s"

SimpleQuantityFormat fmt = SimpleQuantityFormat.getInstance();
Quantity<?> parsed = fmt.parse("36 km/h");
fmt.format(parsed);                        // "36 km/h"
```

## Quantity Construction and Values

A quantity binds one numeric value to one unit on one measurement scale; construction goes through static factories and the parts stay observable.

**Factories.** `Quantities.getQuantity(value, unit)` returns a `ComparableQuantity` carrying the given `Number` and `Unit` on the `ABSOLUTE` scale. `Quantities.getQuantity(value, unit, scale)` selects the scale explicitly (`Scale.ABSOLUTE` or `Scale.RELATIVE`). `Quantities.getQuantity(text)` parses a `CharSequence` of the form "number unit-symbol" — `"10 m"` yields value 10 and the metre unit; `"2.5 s"` yields 2.5 seconds; `"1.5 km"` yields 1.5 kilometres. Unparseable text raises `MeasurementParseException`.

**Accessors.** `getValue()` returns the `Number`, `getUnit()` the `Unit`, `getScale()` the scale. A quantity built with an integral value reports an integral number (`getQuantity(10, METRE).getValue()` is 10); a decimal input reports a decimal. `toString()` renders "value unit" (`"10 m"`, `"2.5 m"`).

**Exact numerics.** Arithmetic must be exact, not binary floating point: 0.1 m + 0.2 m has a value whose `doubleValue()` is exactly 0.3 and is equivalent to 0.3 m; one metre divided by the number 3, multiplied by the number 3, is equivalent to exactly one metre. Exact integral results stay integral: converting 1 km to metres reports 1000 as an integral number, and 10 m + 5 m reports 15. Results that require fractions report decimal values (10 m divided by the number 4 is 2.5 m).

## Quantity Arithmetic

Arithmetic operates on quantities as value-with-unit pairs; units compose dimensionally and the result is a new immutable quantity.

**Addition and subtraction.** `add(other)` and `subtract(other)` require same-dimension operands. When units differ, the result carries the left operand's unit with the right operand converted into it: 1 km + 500 m is 1.5 km, while 500 m + 1 km is 1500 m. Same-unit sums keep exact values (10 m + 5 m is 15 m).

**Multiplication and division.** `multiply(quantity)` and `divide(quantity)` accept any-dimension operands and compose units: 10 m × 3 m has value 30 and a unit equal to `METRE.multiply(METRE)`; 10 m ÷ 2 s has value 5 and a unit equal to `METRE.divide(SECOND)`. `multiply(number)` and `divide(number)` scale the value and keep the unit (10 m × 4 is 40 m; 10 m ÷ 4 is 2.5 m). Dividing same-unit quantities cancels to the dimensionless unit: 10 m ÷ 2 m has value 5 and unit `AbstractUnit.ONE`. Dividing quantities whose units differ keeps the composed quotient unit: 1 km ÷ 500 m has value 0.002 and a unit equal to the kilometre divided by the metre, which is compatible with `AbstractUnit.ONE` and converts to it as the plain ratio 2.

**Inverse and negation.** `inverse()` reciprocates value and unit: the inverse of 2 s has value 0.5 and a unit equal to `SECOND.pow(-1)` (equivalently `SECOND.inverse()`). `negate()` flips the value's sign and keeps the unit.

**Typed views.** `asType(quantityType)` casts the quantity to the requested typed interface when the unit's dimension matches (`getQuantity(3, METRE).asType(Length.class)`), and raises `ClassCastException` when it does not (metres viewed as `Mass`).

## Unit Algebra and the System of Units

Units are immutable objects with full dimensional bookkeeping; a built-in system supplies the standard constants and algebra derives everything else.

**System of units.** The `Units` class exposes the SI base units as constants — `METRE`, `KILOGRAM`, `SECOND`, `KELVIN`, `AMPERE`, `MOLE`, `CANDELA` — plus derived and accepted constants including `CELSIUS`, `HERTZ`, `NEWTON`, `PASCAL`, `JOULE`, `WATT`, `SQUARE_METRE`, `CUBIC_METRE`, `METRE_PER_SECOND`, `KILOMETRE_PER_HOUR`, `GRAM`, `LITRE`, `PERCENT`, `MINUTE`, `HOUR`, `DAY`. `Units.getInstance()` returns the system-of-units singleton, whose `getName()` is `"Units"` and whose `getUnits()` set contains the declared constants.

**Prefixes.** The API's `MetricPrefix` factories build scaled units: `MetricPrefix.KILO(METRE)` renders as `"km"`, `MILLI(SECOND)` as `"ms"`. A prefixed unit's `getSystemUnit()` is the unprefixed system unit (`KILO(METRE).getSystemUnit()` equals `METRE`), and its `getSymbol()` is null — the printable form comes from `toString()` or a unit format. Base units report their symbol directly (`METRE.getSymbol()` is `"m"`).

**Algebra.** `multiply`, `divide`, `pow`, and `root` derive units: `METRE.multiply(METRE)` equals `SQUARE_METRE` and equals `METRE.pow(2)`; `METRE.divide(SECOND)` equals `METRE_PER_SECOND`; `SQUARE_METRE.root(2)` equals `METRE`.

**Equality is structural.** Unit `equals` compares construction, not measure: product-formed constants equal their algebraic reconstructions as above, but a prefixed-and-divided construction such as `KILO(METRE).divide(HOUR)` is not equal to the `KILOMETRE_PER_HOUR` constant even though both render `"km/h"` — the two are compatible, and one of each measures the same speed. Semantic questions go through `isCompatible(unit)` (true for `METRE` vs `KILO(METRE)`, false for `METRE` vs `SECOND`), through `getDimension()` equality, and through quantity equivalence.

**Typed views.** `Unit.asType(quantityType)` checks the dimension and raises `ClassCastException` on mismatch (`METRE.asType(Time.class)`).

## Conversion and Converters

Conversion re-expresses a quantity in a compatible unit, exactly where possible, and exposes the underlying converter objects.

**Quantity conversion.** `to(unit)` returns the quantity re-expressed in the target unit: 1 km to metres is 1000 m (integral), 2 h to seconds is 7200 s, 1500 m to kilometres is 1.5 km, and 36 km/h to metres per second is exactly 10 m/s. Offset scales convert with their offset: 20 °C to kelvin is 293.15 K. Converting to the quantity's own unit returns an equal quantity.

**Unit converters.** `getConverterTo(unit)` returns a `UnitConverter` for compatible units: converting 2 through the km→m converter yields 2000.0, 500 through m→km yields 0.5, and 300 through K→°C yields 26.85. A unit's converter to itself answers `isIdentity()` true; scale-factor conversions answer `isLinear()` true, while offset conversions (K→°C) answer `isLinear()` false. `getConverterToAny(unit)` accepts dimension-crossing arguments but raises the checked `IncommensurableException` when the units are not compatible (metres to seconds).

## Comparison and Equivalence

Three comparison regimes coexist and must not be conflated: strict equality, numeric ordering, and measure equivalence.

**Equality.** `equals` on quantities is unit-sensitive: 1 km never equals 1000 m. It is representation-insensitive on values: 10 m equals 10.0 m. Two quantities with equal value and equal unit are equal.

**Ordering.** `compareTo` orders by measure across units: 500 m compares less than 1 km, and 1 km compares equal (0) to 1000 m. The relational helpers `isGreaterThan`, `isGreaterThanOrEqualTo`, `isLessThan`, `isLessThanOrEqualTo` apply the same cross-unit measure comparison (500 m `isLessThan` 1 km is true).

**Equivalence.** `isEquivalentTo(other)` is true exactly when both quantities denote the same measure after conversion: 1 km is equivalent to 1000 m symmetrically, 20 °C is equivalent to 293.15 K, and 10 m is equivalent to 10.0 m. Equivalence must hold in both directions whenever it holds in one.

## Scales and Temperature Arithmetic

Every quantity carries a scale that decides how offset units convert and add; the rules are observable wherever a unit has an offset, with temperature as the canonical case.

**Scales.** The default scale is `Scale.ABSOLUTE`; `Quantities.getQuantity(value, unit, Scale.RELATIVE)` builds a relative (delta) quantity, reported by `getScale()`.

**Conversion by scale.** An ABSOLUTE 10 °C converts to kelvin with the offset applied: 283.15 K. A RELATIVE 10 °C is a temperature difference, so it converts by scale factor only: 10 K.

**Addition by scale.** Adding two ABSOLUTE offset-unit quantities operates on the absolute scale and re-expresses the result in the left unit: 20 °C + 10 °C is 303.15 °C (the kelvin sum 576.3 K re-expressed). Adding a RELATIVE right operand to an ABSOLUTE left operand treats the right as a delta: 20 °C + 10 °C (relative) is 30 °C. Adding two RELATIVE quantities adds the deltas: 10 °C (relative) + 10 °C (relative) is 20 °C on the relative scale.

## Formatting and Parsing

The simple format classes render quantities and units to text and parse the same forms back.

**Quantity format.** `SimpleQuantityFormat.getInstance()` returns the shared format. `format(quantity)` renders "value unit" using the unit's symbol form (`"10 m"`, `"1 km"`, `"5 m/s"`). `parse(text)` reads the same form back into a quantity; the round trip `format(parse(s))` returns `s` for inputs such as `"10 m"`, `"1.5 km"`, and `"36 km/h"`. Text that does not start with a parseable number raises `MeasurementParseException`.

The factory `Quantities.getQuantity(text)` and `SimpleQuantityFormat.parse(text)` denote the same measure for the same text — their results are always equivalent and format back to the same string — but they need not be `equals`: the two entry points may resolve a compound unit symbol to different constructions of the same unit (the factory resolves `"km/h"` to the named `KILOMETRE_PER_HOUR` constant while the quantity format builds the prefixed quotient — compatible, equivalent, structurally unequal), and decimal text may parse to different numeric representations across entry points. On whole-number base-unit text such as `"10 m"` and `"120 s"` the two return equal quantities.

**Unit format.** `SimpleUnitFormat.getInstance()` returns the shared unit format. `format(unit)` renders the symbol form (`"km"` for the prefixed metre, `"m/s"` for the quotient). `parse(text)` returns the unit whose form matches: parsing `"km"` yields a unit equal to `MetricPrefix.KILO(METRE)`, parsing `"m/s"` yields a unit equal to `METRE.divide(SECOND)`. An unknown symbol raises `MeasurementParseException`.

## State Model

Quantities and units are immutable values; the only state is the construction of each object.

Every arithmetic, conversion, and comparison operation returns a new quantity or unit and leaves its operands untouched; no operation mutates a quantity, a unit, or the system of units. A quantity is fully described by its (value, unit, scale) triple: any two quantities with equal triples behave identically everywhere. Units are fully described by their construction; structural equality, compatibility, dimension, and system-unit projection are all derived views of that construction.

The `Units` system-of-units singleton and the shared format instances (`SimpleQuantityFormat.getInstance()`, `SimpleUnitFormat.getInstance()`) are process-wide and stateless with respect to the values they format or parse: parsing and formatting never register state that changes later results for the inputs specified here.

## Error Semantics

| Condition | Raised |
|---|---|
| `Quantities.getQuantity(text)` on unparseable text | `MeasurementParseException` |
| `SimpleQuantityFormat.parse` on text without a leading parseable number | `MeasurementParseException` |
| `SimpleUnitFormat.parse` on an unknown unit symbol | `MeasurementParseException` |
| `Quantity.asType(type)` with a dimension-incompatible quantity type | `ClassCastException` |
| `Unit.asType(type)` with a dimension-incompatible quantity type | `ClassCastException` |
| `Unit.getConverterToAny(unit)` between incompatible dimensions | `IncommensurableException` (checked) |

`MeasurementParseException`, `IncommensurableException`, and the `UnitConverter`, `Quantity`, `Unit`, `MetricPrefix`, and `Scale` types are part of the measurement API artifact (`javax.measure`), which is present in the environment; the implementation raises those API types.

## Cross-View Invariants

1. **Equivalence–conversion agreement.** For any two compatible quantities `a` and `b`, `a.isEquivalentTo(b)` must be true exactly when `a.to(b.getUnit())` has the same measure as `b`, and equivalence must be symmetric — including across offset units (Celsius/kelvin) and prefixed units (km/m).
2. **Ordering–equivalence coherence.** `compareTo` must return 0 exactly for pairs that are equivalent (1 km vs 1000 m), and the relational helpers (`isGreaterThan`, `isLessThan`, and their or-equal forms) must agree with `compareTo`'s sign for every cross-unit pair.
3. **Arithmetic–unit-algebra agreement.** The unit of `p.multiply(q)` must equal `p.getUnit().multiply(q.getUnit())`, the unit of `p.divide(q)` must equal `p.getUnit().divide(q.getUnit())`, the unit of `p.inverse()` must equal `p.getUnit().pow(-1)`, and dividing same-unit quantities must yield the unit `AbstractUnit.ONE`.
4. **Conversion–converter agreement.** For compatible units `u` and `v`, `getQuantity(n, u).to(v).getValue().doubleValue()` must equal `u.getConverterTo(v).convert(n.doubleValue())` — the quantity view and the converter view of the same conversion never disagree.
5. **Format round-trip.** For every quantity built from the unit constants named in this specification or from prefixed base units, `SimpleQuantityFormat.getInstance().parse(format(q))` must be equivalent to `q`, and for each such unit `u`, `SimpleUnitFormat.getInstance().parse(format(u))` must equal `u`; the factory `Quantities.getQuantity(text)` must denote the same measure as `SimpleQuantityFormat.parse(text)` — equivalent results that format back to the same string. Units built by algebra may reparse to an equal named constant instead of their original construction (formatting `KILO(METRE).divide(HOUR)` and parsing the result through `SimpleUnitFormat` yields `KILOMETRE_PER_HOUR`, a compatible but structurally different unit), so the strict round-trip guarantee applies to the named and prefixed forms.
6. **Exactness invariant.** Chains of exact operations must not accumulate binary floating-point error: adding 0.1 m and 0.2 m, or dividing by 3 and multiplying by 3, produces quantities equivalent to the exact decimal results, and integral inputs passing through exact scale conversions (km to m) report integral values.
7. **Left-unit rule.** For same-dimension mixed-unit addition and subtraction, the result's unit must equal the left operand's unit, and its measure must be equivalent to the sum computed in either operand's unit.

## Public Interface

### Import Surface

```java
import tech.units.indriya.AbstractUnit;
import tech.units.indriya.ComparableQuantity;
import tech.units.indriya.format.SimpleQuantityFormat;
import tech.units.indriya.format.SimpleUnitFormat;
import tech.units.indriya.quantity.Quantities;
import tech.units.indriya.unit.Units;
```

The measurement API types used with these classes — `javax.measure.Quantity` (and its nested `Quantity.Scale`), `javax.measure.Unit`, `javax.measure.UnitConverter`, `javax.measure.MetricPrefix`, the typed quantity interfaces (`javax.measure.quantity.Length`, `Mass`, `Time`, `Speed`, `Temperature`, `Dimensionless`, and the rest), and the exceptions `javax.measure.format.MeasurementParseException` and `javax.measure.IncommensurableException` — come from the `javax.measure:unit-api` dependency.

### Public Members

| Type | Public members in scope |
|---|---|
| `Quantities` | `static Quantity<?> getQuantity(CharSequence csq)`; `static <Q extends Quantity<Q>> ComparableQuantity<Q> getQuantity(Number value, Unit<Q> unit)`; `static <Q extends Quantity<Q>> ComparableQuantity<Q> getQuantity(Number value, Unit<Q> unit, Quantity.Scale scale)` |
| `ComparableQuantity<Q>` | interface extending `Quantity<Q>`, `Comparable<Quantity<Q>>`; `ComparableQuantity<Q> add(Quantity<Q> that)`; `ComparableQuantity<Q> subtract(Quantity<Q> that)`; `ComparableQuantity<?> multiply(Quantity<?> that)`; `ComparableQuantity<Q> multiply(Number that)`; `ComparableQuantity<?> divide(Quantity<?> that)`; `ComparableQuantity<Q> divide(Number that)`; `ComparableQuantity<?> inverse()`; `ComparableQuantity<Q> to(Unit<Q> unit)`; `<T extends Quantity<T>> ComparableQuantity<T> asType(Class<T> type)`; `boolean isGreaterThan(Quantity<Q> that)`; `boolean isGreaterThanOrEqualTo(Quantity<Q> that)`; `boolean isLessThan(Quantity<Q> that)`; `boolean isLessThanOrEqualTo(Quantity<Q> that)`; inherited from the API: `Number getValue()`, `Unit<Q> getUnit()`, `Quantity.Scale getScale()`, `Quantity<Q> negate()`, `boolean isEquivalentTo(Quantity<Q> that)`, `int compareTo(Quantity<Q> that)` |
| `Units` | `static Units getInstance()`; `String getName()`; constants `METRE` (`Unit<Length>`), `KILOGRAM` (`Unit<Mass>`), `SECOND` (`Unit<Time>`), `KELVIN` (`Unit<Temperature>`), `CELSIUS` (`Unit<Temperature>`), `AMPERE`, `MOLE`, `CANDELA`, `GRAM` (`Unit<Mass>`), `HERTZ` (`Unit<Frequency>`), `NEWTON` (`Unit<Force>`), `PASCAL` (`Unit<Pressure>`), `JOULE` (`Unit<Energy>`), `WATT` (`Unit<Power>`), `SQUARE_METRE` (`Unit<Area>`), `CUBIC_METRE` (`Unit<Volume>`), `METRE_PER_SECOND` (`Unit<Speed>`), `KILOMETRE_PER_HOUR` (`Unit<Speed>`), `LITRE` (`Unit<Volume>`), `PERCENT` (`Unit<Dimensionless>`), `MINUTE` (`Unit<Time>`), `HOUR` (`Unit<Time>`), `DAY` (`Unit<Time>`); inherited: `Set<Unit<?>> getUnits()` |
| `AbstractUnit` | in scope only as the constant `static final Unit<Dimensionless> ONE` (the dimensionless unit) |
| `SimpleQuantityFormat` | `static SimpleQuantityFormat getInstance()`; `Quantity<?> parse(CharSequence csq)`; inherited from the API format contract: `String format(Quantity<?> quantity)` |
| `SimpleUnitFormat` | `static SimpleUnitFormat getInstance()`; inherited from the API format contract: `String format(Unit<?> unit)`, `Unit<?> parse(CharSequence csq)` |

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Quantities` | class | Static factory for quantities from numbers, units, scales, and text. |
| `ComparableQuantity` | interface | Quantity with arithmetic, conversion, ordering, and typed views. |
| `Units` | class | Built-in system of units; SI constants and singleton access. |
| `AbstractUnit` | class | Carrier of the dimensionless unit constant `ONE`. |
| `SimpleQuantityFormat` | class | Renders and parses "value unit" quantity text. |
| `SimpleUnitFormat` | class | Renders and parses unit symbol text. |

### CLI Entry Points

There is no console script for this package. Java callers use the library through Maven dependencies and Java imports.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. The measurement API artifacts `javax.measure:unit-api` and `tech.uom.lib:uom-lib-common` are available as compile dependencies and resolve through Maven together with the Java standard library. The assessment environment provides the same JDK and offline execution policy.

The project must provide a Maven `pom.xml` at its root with coordinate `tech.units:indriya`, declaring its dependency on the measurement API artifact. Source must compile through the standard Maven lifecycle using locally available artifacts.

## Appendix B: Assessment Notes

Assessment exercises the documented behaviors through the public API: quantity construction from numbers and text with value, unit, and scale accessors; exact arithmetic including the left-unit rule, dimensional composition, and dimensionless cancellation; unit algebra, prefixes, structural equality versus compatibility; conversions across scale factors, offsets, and compound units, including the converter objects; the three comparison regimes; ABSOLUTE and RELATIVE scale semantics on offset units; format round trips; and the declared error taxonomy. Tests construct quantities and units through the documented factories and constants, and observe numbers through `Number` views, units through equality and compatibility, text through the format classes, and failures through raised exception types. Both single behaviors and multi-step scenarios are measured.
