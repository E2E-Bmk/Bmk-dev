# Cron Utilities Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

`cron-utils` is a Java cron-expression library that defines dialects, constructs and parses expressions, validates their field rules, translates them between dialects, describes them for human readers, and computes calendar execution times. The Maven artifact is `com.cronutils:cron-utils`; its shared fact source is a `CronDefinition` paired with a graph of typed `CronField` and `FieldExpression` values.

The same cron graph is exposed as canonical text, structured fields, validation results, localized descriptions, mapped dialects, equivalence results, and time-based projections. The library includes predefined Unix, Cron4j, Quartz, Spring, and Spring 5.3 dialect definitions while retaining builders for custom definitions.

## Non-Goals

- This specification does not require the separate satellite command-line project or an executable main class.
- This specification does not require scheduler, persistence, job dispatch, or operating-system crontab installation behavior.
- This specification does not define private or package-private helper types, internal search algorithms, cached field layout, logging text, or exact exception messages.
- This specification does not require experimental alternate descriptor namespaces.
- This specification does not define generic parsing guards, string utilities, predicate adapters, or test-visibility annotations as cron-domain APIs.
- This specification does not require locale wording beyond the resource-bundle-driven description rules and the packaged locale resources described below.

## Representative Workflows

### Parse, Inspect, and Schedule a Quartz Expression

```java
import static com.cronutils.model.CronType.QUARTZ;

import com.cronutils.model.Cron;
import com.cronutils.model.definition.CronDefinition;
import com.cronutils.model.definition.CronDefinitionBuilder;
import com.cronutils.model.time.ExecutionTime;
import com.cronutils.parser.CronParser;
import java.time.ZonedDateTime;

CronDefinition definition = CronDefinitionBuilder.instanceDefinitionFor(QUARTZ);
Cron cron = new CronParser(definition).parse("0 23 * ? * MON-FRI *");
String canonical = cron.asString();
ExecutionTime time = ExecutionTime.forCron(cron);
ZonedDateTime now = ZonedDateTime.now();
time.nextExecution(now);
time.lastExecution(now);
```

WHEN parsing succeeds, THEN the parser must normalize whitespace and symbolic names against the supplied definition, and the resulting cron must retain that definition for validation, inspection, serialization, and local-time execution queries.

### Build, Describe, and Map a Cron

```java
import static com.cronutils.model.CronType.QUARTZ;
import static com.cronutils.model.field.expression.FieldExpressionFactory.*;

import com.cronutils.builder.CronBuilder;
import com.cronutils.descriptor.CronDescriptor;
import com.cronutils.mapper.CronMapper;
import com.cronutils.model.Cron;
import com.cronutils.model.definition.CronDefinition;
import com.cronutils.model.definition.CronDefinitionBuilder;
import java.util.Locale;

CronDefinition quartz = CronDefinitionBuilder.instanceDefinitionFor(QUARTZ);
Cron cron = CronBuilder.cron(quartz)
    .withSecond(on(0))
    .withMinute(on(23))
    .withHour(always())
    .withDoM(questionMark())
    .withMonth(always())
    .withDoW(between(2, 6))
    .withYear(always())
    .instance();

String text = CronDescriptor.instance(Locale.UK).describe(cron);
Cron cron4j = CronMapper.fromQuartzToCron4j().map(cron);
```

The builder and parser must produce the same structured model so description and mapping operate without reparsing the canonical string.

### Define a Custom Dialect

```java
import com.cronutils.model.definition.CronDefinition;
import com.cronutils.model.definition.CronDefinitionBuilder;

CronDefinition custom = CronDefinitionBuilder.defineCron()
    .withMinutes().withValidRange(0, 59).withStrictRange().and()
    .withHours().withValidRange(0, 23).withStrictRange().and()
    .withDayOfMonth().withValidRange(1, 31).supportsL().and()
    .withMonth().withValidRange(1, 12).and()
    .withDayOfWeek().withValidRange(0, 6).withMondayDoWValue(1).and()
    .instance();
```

WHEN a custom definition is finalized, THEN its fluent builders must register fields in canonical field order and carry ranges, value mappings, special-character support, optionality, nickname support, and cross-field constraints into later parsing and validation.

## Definitions and Expression Construction

This section defines the dialect vocabulary and the typed construction model that every later projection consumes.

**Predefined dialects.** The `CronType` values must be `CRON4J`, `QUARTZ`, `UNIX`, `SPRING`, and `SPRING53`.

The `CronDefinitionBuilder.instanceDefinitionFor(cronType)` method must return a new definition for the selected `CronType`.

The `CRON4J` definition must contain minute, hour, day-of-month, month, and day-of-week fields; it must use ranges 0–59, 0–23, 0–31, 1–12, and 0–6 respectively, must support `L` in day-of-month, and must match day-of-month together with day-of-week.

The `UNIX` definition must contain minute, hour, day-of-month, month, and day-of-week fields with ranges 0–59, 0–23, 1–31, 1–12, and 0–7 respectively, and day-of-week value 7 must map to 0.

The `QUARTZ` definition must contain second, minute, hour, day-of-month, month, day-of-week, and optional year fields; it must use ranges 0–59, 0–59, 0–23, 1–31, 1–12, 1–7, and 1970–2099 respectively.

The `QUARTZ` definition must support `L`, `W`, `LW`, and `?` for day-of-month, `L`, `#`, and `?` for day-of-week, and it must require at least one of day-of-month or day-of-week to be `?`.

The `SPRING` definition must contain six fields from second through day-of-week, must use day-of-week range 0–7 with 7 mapped to 0, and must support `#` and `?` for day-of-week but not the `L`, `W`, or `LW` extensions.

The `SPRING53` definition must use the same six-field order and day-of-week mapping as `SPRING`, must add `L`, `W`, and `LW` support where defined for Spring 5.3, and must support the yearly, annually, monthly, weekly, daily, midnight, and hourly nicknames.

WHEN `cronType` is null or has no definition, THEN `instanceDefinitionFor` must raise a runtime argument/null error rather than return a fallback dialect.

**Custom definition builder.** The `CronDefinitionBuilder.defineCron()` factory must return an initially empty builder whose `withSeconds`, `withMinutes`, `withHours`, `withDayOfMonth`, `withMonth`, `withDayOfWeek`, `withYear`, and `withDayOfYear` methods select a field-specific builder.

The field-definition builders must preserve the configured `withValidRange`, `withStrictRange`, integer mappings, `optional`, `supportsHash`, `supportsL`, `supportsW`, `supportsLW`, `supportsQuestionMark`, and `withMondayDoWValue` settings in the resulting `FieldDefinition` and `FieldConstraints` projections.

The eight `withSupportedNickname*` methods must add their corresponding `CronNicknames` value, and `withCronValidation` must add its `CronConstraint` to the built definition.

WHEN a mandatory field is registered after an optional field, THEN `CronDefinitionBuilder.register` must raise `IllegalArgumentException`.

WHEN `instance()` is called, THEN the builder must return a `CronDefinition` whose field definitions are ordered by `CronFieldName.getOrder()` and whose constraint and nickname sets reflect the registrations.

WHEN a non-reboot `CronDefinition` receives null or empty field definitions, null constraints, null nicknames, or an optional first field, THEN its constructor must raise `NullPointerException` or `IllegalArgumentException` according to the violated precondition.

**Typed field expressions.** `FieldExpressionFactory` must construct `Always`, `QuestionMark`, `On`, `Between`, `Every`, and `And` values through `always`, `questionMark`, the four `on` overloads, the two `between` overloads, the two `every` overloads, and `and`.

A `Between` value must support construction from a public `FieldValue` `from` endpoint followed by a public `FieldValue` `to` endpoint; each endpoint must accept any public `FieldValue` carrier, including `IntegerFieldValue` and `SpecialCharFieldValue`.

An `Every` value must support construction from one `IntegerFieldValue` period, or from a `FieldExpression` base followed by an `IntegerFieldValue` period; the period-only form must use the all-values `Always` expression as its base.

An `On` value must support construction from one `SpecialCharFieldValue`, one `IntegerFieldValue` time, an `IntegerFieldValue` time followed by a `SpecialCharFieldValue`, or an `IntegerFieldValue` time followed by a `SpecialCharFieldValue` and then an `IntegerFieldValue` nth value.

The four `FieldExpressionFactory.on` forms must accept, respectively, a `SpecialChar`, an integer time, an integer time followed by a `SpecialChar`, or an integer time followed by a `SpecialChar` and then an integer nth value.

The `FieldExpressionFactory.and` method must receive a single ordered `List` of `FieldExpression` values and retain that order in the resulting `And` conjunction.

The `asString()` methods must serialize `Always` as `*`, `QuestionMark` as `?`, `Between` as `from-to`, `And` as comma-separated child expressions, and `Every` as `expression/period`.

WHEN `Every` represents all values with a period of one, THEN `Every.asString()` returns `*`.

The `On.asString()` method must serialize ordinary values directly, `HASH` as `time#nth`, `W` as `timeW`, `L` as either `L`, `L-nth`, or `timeL`, and `QUESTION_MARK` as `?`.

The `RandomExpression` methods must retain optional `from`, `to`, and `step` bounds, must serialize them with the OpenBSD `~` syntax, and must produce a value inside the caller-supplied field bounds through the injected `RandomUtils`.

The `FieldExpressionVisitor` protocol must dispatch every expression subtype to its matching `visit` overload; `FieldExpressionVisitorAdaptor` must return the visited expression unchanged, and `ValueMappingFieldExpressionVisitor` must recursively map contained `FieldValue` instances.

WHEN an expression satisfies the supplied constraints, THEN `ValidationFieldExpressionVisitor` must return that expression.

WHEN an `On` expression is created with null components, a hash without an `nth` value, or a negative integer through `FieldExpressionFactory.on(int)`, THEN construction must raise `NullPointerException` or `IllegalArgumentException`.

## Parsing, Serialization, and Structured Inspection

This section defines how textual cron forms become immutable public model projections and return to canonical text.

**Parser selection and normalization.** A `CronParser` must accept a non-null `CronDefinition`, and its `parse(expression)` method must collapse consecutive whitespace, trim surrounding whitespace, and match fields in `CronFieldName` order.

WHEN the definition ends with one or more optional fields, THEN `CronParser` must accept each supported suffix omission while retaining all mandatory leading fields.

WHEN a field contains a supported symbolic month or weekday name, THEN parsing must resolve it case-insensitively through the field definition's string mapping.

WHEN a field uses `*`, `?`, comma lists, hyphen ranges, slash periods, `L`, `W`, `LW`, `#`, or `~` and the field constraints support that form, THEN `FieldParser` must return the corresponding typed `FieldExpression`.

WHEN an expression starts with a supported nickname, THEN `CronParser` must return the matching cron produced by `CronBuilder.yearly`, `annually`, `monthly`, `weekly`, `daily`, `midnight`, `hourly`, or `reboot`.

WHEN an expression contains `||`, THEN `CronParser` must parse each complete subexpression and return a `CompositeCron` containing those crons in source order.

WHEN one or more fields contain aligned `|` alternatives, THEN `CronParser` must expand the aligned alternatives into a `CompositeCron`, and `CompositeCron.asString()` must squash identical field columns back to one value while retaining distinct columns with `|`.

WHEN an expression is null, empty, has an unsupported field count or nickname, has a trailing comma, has an incomplete range or period, or violates field constraints, THEN parsing must raise `NullPointerException` or `IllegalArgumentException` rather than return a partial cron.

**Structured model.** A `SingleCron` must retain its `CronDefinition` and one `CronField` per supplied `CronFieldName`, and `retrieveFieldsAsMap()` must return an unmodifiable map.

WHEN the definition contains `name`, THEN `SingleCron.retrieve(name)` returns the matching field.

WHEN the definition lacks `name`, THEN `SingleCron.retrieve(name)` returns null.

The `SingleCron.asString()` method must order fields by `CronFieldName.getOrder()` and join each expression's canonical text with single spaces.

The `CronField` and `FieldDefinition` accessors must return their field name, expression or constraints, and optional status, while their comparator factories must sort by canonical field order.

The `CronDefinition` accessors must return defensive or unmodifiable projections of field definitions, constraints, and nicknames, and `containsFieldDefinition` must report membership by `CronFieldName`.

WHEN `SingleCron` receives a null definition, a null field list, or `retrieve(null)`, THEN it must raise `NullPointerException`.

## Validation, Composite Behavior, and Equivalence

This section defines validity and comparison semantics over single, composite, and reboot cron models.

**Validation.** `SingleCron.validate()` must validate every expression against its field constraints, then apply every registered `CronConstraint`, and return the same cron on success.

WHEN `CronConstraintsFactory.ensureQuartzDayOfMonthAndDayOfWeekValidation()` is active and at least one of day-of-month or day-of-week is `?`, THEN validation must accept that cross-field combination.

WHEN `ensureEitherDayOfWeekOrDayOfMonth()` is active, THEN validation must require exactly one of day-of-month or day-of-week to be specified while the other is `?`.

WHEN `ensureEitherDayOfYearOrMonth()` is active and day-of-year is specified, THEN validation must require both day-of-month and day-of-week to be `?`.

WHEN a field expression violates its range, period, mapping, special-character support, or cross-field constraint, THEN `validate()` must raise `IllegalArgumentException`.

**Composite and reboot forms.** A `CompositeCron` must contain a non-empty unmodifiable list of crons that all share an equal `CronDefinition`.

WHEN the composite list is null, empty, or contains different definitions, THEN the `CompositeCron` constructor must raise `NullPointerException` or `IllegalArgumentException`.

The `CompositeCron.validate()` method must validate every component and return the composite.

The `CompositeCron.retrieve`, `retrieveFieldsAsMap`, and mapper-based `equivalent` operations must raise `UnsupportedOperationException`.

A `RebootCron` must serialize as `@reboot`, must return an empty field map and null for a named field, and must overlap only another `RebootCron`.

**Comparison.** `Cron.equivalent(other)` must compare canonical strings under the assumption of a shared definition, while `Cron.equivalent(mapper, other)` must map `other` before comparing canonical strings.

The `CompositeCron.equivalent(other)` method must compare its squashed canonical string.

WHEN any component overlaps `other`, THEN `CompositeCron.overlap(other)` returns true.

WHEN either cron has no future execution, THEN `SingleCron.overlap(other)` must return false.

WHEN both crons have future executions, THEN `SingleCron.overlap(other)` must report whether their upcoming public execution projections share a time.

WHEN a required cron or mapper argument is null, THEN comparison or overlap operations must raise `NullPointerException` rather than report equivalence.

## Human-Readable Descriptions

This section defines locale-backed descriptions as a projection of parsed fields and their definition metadata.

**Descriptor creation.** `CronDescriptor.instance()` must use `Locale.UK`, `CronDescriptor.instance(locale)` must load the packaged bundle for `locale`, and the public `ResourceBundle` constructor must use the supplied bundle.

The `getResourceBundle()` method returns the active bundle, and the artifact must package base plus German, Greek, English, Spanish, French, Indonesian, Italian, Japanese, Korean, Dutch, Polish, Portuguese, Romanian, Russian, Swahili, Turkish, and Chinese bundles.

**Description projection.** `CronDescriptor.describe(cron)` must combine time-of-day, day-of-month, month, day-of-week, and year phrases, normalize repeated whitespace, and use weekday numbering from the cron definition.

The `describeHHmmss`, `describeDayOfMonth`, `describeMonth`, `describeDayOfWeek`, and `describeYear` methods must return the corresponding partial phrase using the active resource bundle.

WHEN the cron is a `RebootCron`, THEN `describe` must return the bundle's reboot phrase.

WHEN `cron` or a required locale/resource bundle is null or unavailable, THEN descriptor construction or description must raise the ordinary Java null or resource-loading exception.

## Dialect and Calendar Conversion

This section defines transformations that preserve schedule meaning across cron dialects or time zones.

**Dialect mapping.** `CronMapper` must expose predefined factories for Cron4j-to-Quartz, Quartz-to-Cron4j, Quartz-to-Unix, Unix-to-Quartz, Quartz-to-Spring, and Spring-to-Quartz, plus `sameCron(definition)`.

The general `CronMapper` constructor must accept non-null `from`, `to`, and `cronRules` values, and `map(cron)` must return a validated cron under the target definition.

WHEN a target dialect introduces leading fields absent from the source, THEN mapping must set those fields to zero.

WHEN a target dialect introduces trailing fields absent from the source, THEN mapping must set those fields to `*`.

WHEN weekday numbering differs, THEN mapping must transform direct values, ranges, lists, and stepped expressions through the source and target `WeekDay` definitions while preserving special-character values.

WHEN a source `?` is unsupported in the target day field, THEN mapping must replace it with `*`.

WHEN a target dialect requires a day question mark and neither source day field has one, THEN mapping must replace an all-values day field with `?`.

WHEN a `RebootCron` is mapped, THEN the target must return a new `RebootCron` only if it supports the `REBOOT` nickname.

WHEN the input cron is null, the constructor inputs are null, the target does not support reboot, or the mapped expression violates target constraints, THEN `CronMapper` must raise `NullPointerException` or `IllegalArgumentException`.

**Weekday constants.** `ConstantsMapper.QUARTZ_WEEK_DAY`, `JAVA8`, and `CRONTAB_WEEK_DAY` must represent Monday values 2, 1, and 1 respectively, with only the crontab definition using a zero-based range.

The `WeekDay.mapTo` and `ConstantsMapper.weekDayMapping` methods must preserve the represented weekday while shifting or wrapping values between zero-based and one-based definitions.

The `WeekDay.mapTo` method must receive the integer `dayOfWeek` value first and the target `WeekDay` definition second, and return the directly mapped integer.

The `ConstantsMapper.weekDayMapping` method must receive a source `WeekDay` definition, a target `WeekDay` definition, and an integer weekday value, and return the directly mapped integer.

WHEN a `WeekDay` is created with a negative Monday value, THEN its constructor must raise `IllegalArgumentException`.

**Time-zone text conversion.** The `CronToCalendarTransformer` and `CalendarToCronTransformer` classes must each support public construction without arguments before being supplied to `CronConverter`.

A `CronConverter` must accept a `CronToCalendarTransformer` and a `CalendarToCronTransformer`, retain the cron text supplied through `using`, retain the source and target `ZoneId` values supplied through `from` and `to`, and return the transformed cron text through `convert`.

WHEN `using`, `from`, or `to` has not supplied the required value before `convert`, THEN conversion must fail through the ordinary Java runtime error instead of fabricating a default cron or zone.

## Execution Times and Calendar Utilities

This section defines temporal projections without exposing the internal search strategy.

**Execution queries.** `ExecutionTime.forCron(cron)` must return a single-cron implementation for `SingleCron`, a `CompositeExecutionTime` for `CompositeCron`, and an empty-result implementation for other `Cron` implementations.

WHEN a matching execution exists, THEN `nextExecution(date)` and `lastExecution(date)` must return the nearest match strictly after or before the reference in the reference `ZonedDateTime` zone.

WHEN no matching execution exists, THEN `nextExecution(date)` and `lastExecution(date)` must return `Optional.empty()`.

The `timeToNextExecution(date)` and `timeFromLastExecution(date)` methods must return the `Duration` between the reference and the corresponding next or previous result, or `Optional.empty()` with no result.

The `isMatch(date)` method must report whether every active field rule matches the supplied local zoned date-time.

The `getExecutionDates(startDate,endDate)` method must return successive executions after `startDate` through and including `endDate`, and `countExecutions` returns that list's size.

WHEN `endDate` is equal to or before `startDate`, THEN `getExecutionDates` and `countExecutions` must raise `IllegalArgumentException`.

WHEN a required date or cron is null, THEN execution-time construction or query methods must raise `NullPointerException`.

**Composite execution.** A `CompositeExecutionTime` must require a non-empty list and must return the earliest component next execution and the latest component previous execution.

WHEN any component matches, THEN `CompositeExecutionTime.isMatch` must return true.

WHEN its execution-time list is null or empty, THEN the `CompositeExecutionTime` constructor must raise `NullPointerException` or `IllegalArgumentException`.

**Frequency and workdays.** A `CronFrequencyComparator` must compare two crons by subtracting their execution counts over the constructor's `startDate` to `endDate` interval.

The `WeekendPolicy` values must be `THURSDAY_FRIDAY`, `FRIDAY_SATURDAY`, and `SATURDAY_SUNDAY`, and `daysToWeekend` and `daysFromWeekend` must use the selected consecutive two-day weekend.

The two `DateUtils.workdaysCount` overloads must count inclusive non-weekend days between `startDate` and either `startDate.plusDays(days)` or `endDate`, then subtract holidays in that interval.

WHEN required dates, policies, cron values, or holiday collections are null, THEN the calendar utilities must raise the ordinary Java null error.

## Bean Validation and Low-Level Extension Points

This section defines integration surfaces used by Jakarta Bean Validation and custom time-field generation.

**Bean Validation.** The `com.cronutils.validation.Cron` annotation must target fields and annotation types at runtime, must use `CronValidator`, and must expose `message`, `groups`, `payload`, and required `type` members.

WHEN the annotated value is null, THEN `CronValidator.isValid` must return true.

WHEN the annotated value parses and validates under the annotation's `CronType`, THEN `CronValidator.isValid` must return true.

WHEN parsing or validation raises `IllegalArgumentException`, THEN `CronValidator.isValid` must disable the default violation, add a violation using the validation error text, and return false.

**Field generator protocol.** A `FieldValueGenerator` must expose next-value, previous-value, match, and bounded candidate-generation operations for its `CronField`.

The `FieldValueGeneratorFactory` must select a generator through `forCronField` and must expose year-, day-of-year-, day-of-month-, and day-of-week-specific factories with the calendar context required by each field.

WHEN no next or previous field value exists within the generator's domain, THEN generator search must raise `NoSuchValueException`.

## State Model

The core state is an immutable or caller-confined graph containing a `CronDefinition`, ordered `CronField` values, typed `FieldExpression` values, value/range mappings, special-character capabilities, nicknames, and cross-field constraints.

The public projections are:

- The definition projection exposed by `CronDefinition`, `FieldDefinition`, `FieldConstraints`, their builders, and enum vocabularies.
- The construction and parsing projection exposed by `CronBuilder`, `FieldExpressionFactory`, `FieldParser`, `CronParserField`, and `CronParser`.
- The cron-model projection exposed by `Cron`, `SingleCron`, `CompositeCron`, `RebootCron`, structured retrieval, and `asString()`.
- The validity and integration projection exposed by `validate()`, `CronConstraint`, the validation visitors, and the Jakarta annotation/validator.
- The transformation projection exposed by `CronMapper`, weekday mapping, visitors, and `CronConverter`.
- The human and temporal projections exposed by `CronDescriptor`, `ExecutionTime`, frequency comparison, and workday utilities.

The `CronDefinition` and `CronParser` objects must be thread-safe for concurrent read and parse use after construction; fluent builders, `And`, converter setup, and injected random generators remain caller-confined mutable construction objects.

## Error Semantics

| Condition | Required result |
|---|---|
| Null required definition, cron, field name, expression, date, callback, or collection | WHEN a required value is null, THEN the receiving public operation must raise `NullPointerException`. |
| Empty required definition fields, composite cron list, or composite execution list | WHEN a required collection is empty, THEN the receiving constructor must raise `IllegalArgumentException`. |
| Invalid field count, unsupported nickname or special character, malformed list/range/period, or out-of-range value | WHEN cron text violates syntax or its definition, THEN parsing must raise `IllegalArgumentException`. |
| Mandatory field registered after an optional field | WHEN a mandatory field follows an optional field, THEN registration must raise `IllegalArgumentException`. |
| Invalid cross-field constraint, including Quartz day-field rules | WHEN a cross-field constraint fails, THEN parsing or `validate()` must raise `IllegalArgumentException`. |
| Composite structured-field retrieval or mapper-based equivalence | WHEN an unsupported composite operation is called, THEN `CompositeCron` must raise `UnsupportedOperationException`. |
| Reboot mapping to a dialect without reboot support | WHEN the target lacks reboot support, THEN mapping must raise `IllegalArgumentException`. |
| Execution range whose end is not after its start | WHEN an execution range end is not after its start, THEN the range query must raise `IllegalArgumentException`. |
| Field generator has no next or previous candidate | WHEN generator search is exhausted, THEN it must raise `NoSuchValueException`. |
| Jakarta validation receives invalid non-null text | WHEN non-null annotation input is invalid, THEN validation must return `false` and add a constraint violation. |

## Cross-View Invariants

1. A cron produced by `CronBuilder.instance()` must expose the same field expressions through `retrieve`, `retrieveFieldsAsMap`, and `asString()` in definition order.
2. A canonical string returned by `SingleCron.asString()` must parse under the same `CronDefinition` into a cron that is `equivalent` to the source.
3. A cron returned by `CronParser.parse()` must already satisfy the same field and cross-field constraints enforced by its later `validate()` call.
4. A `CronMapper` result must retain schedule meaning across weekday-numbering changes, must expose the target `CronDefinition`, and must pass target validation.
5. A `CompositeCron` squashed string must preserve its component schedules, and `ExecutionTime.forCron(composite)` must select next and previous executions from the same component set.
6. The result of `ExecutionTime.isMatch(date)` must agree with whether `date` appears as an execution boundary produced by neighboring next/previous queries for the same cron and zone.
7. `countExecutions(start,end)` must equal the size of `getExecutionDates(start,end)`, and `CronFrequencyComparator` must order crons from those same counts.
8. A `CronDescriptor` phrase must be derived from the same fields returned by structured inspection and must use the weekday numbering carried by the same definition.
9. A `Cron` annotation's `type` must select the same predefined definition as `CronDefinitionBuilder.instanceDefinitionFor(type)`, so Bean Validation must agree with direct parsing and validation.
10. A `RebootCron` must remain `@reboot` through serialization, description, equivalence, and supported dialect mapping, while execution-time queries must return no calendar occurrence.

## Public Interface

### Import Surface

```java
import com.cronutils.Function;
import com.cronutils.builder.CronBuilder;
import com.cronutils.converter.BaseCronTransformer;
import com.cronutils.converter.CalendarToCronTransformer;
import com.cronutils.converter.CronConverter;
import com.cronutils.converter.CronToCalendarTransformer;
import com.cronutils.descriptor.CronDescriptor;
import com.cronutils.mapper.ConstantsMapper;
import com.cronutils.mapper.CronMapper;
import com.cronutils.mapper.WeekDay;
import com.cronutils.model.CompositeCron;
import com.cronutils.model.Cron;
import com.cronutils.model.CronType;
import com.cronutils.model.RebootCron;
import com.cronutils.model.SingleCron;
```

```java
import com.cronutils.model.definition.CronConstraint;
import com.cronutils.model.definition.CronConstraintsFactory;
import com.cronutils.model.definition.CronDefinition;
import com.cronutils.model.definition.CronDefinitionBuilder;
import com.cronutils.model.definition.CronNicknames;
import com.cronutils.model.field.CronField;
import com.cronutils.model.field.CronFieldName;
import com.cronutils.model.field.constraint.FieldConstraints;
import com.cronutils.model.field.constraint.FieldConstraintsBuilder;
import com.cronutils.model.field.definition.DayOfWeekFieldDefinition;
import com.cronutils.model.field.definition.FieldDayOfWeekDefinitionBuilder;
import com.cronutils.model.field.definition.FieldDefinition;
import com.cronutils.model.field.definition.FieldDefinitionBuilder;
import com.cronutils.model.field.definition.FieldQuestionMarkDefinitionBuilder;
import com.cronutils.model.field.definition.FieldSpecialCharsDefinitionBuilder;
```

```java
import com.cronutils.model.field.expression.Always;
import com.cronutils.model.field.expression.And;
import com.cronutils.model.field.expression.Between;
import com.cronutils.model.field.expression.Every;
import com.cronutils.model.field.expression.FieldExpression;
import com.cronutils.model.field.expression.FieldExpressionFactory;
import com.cronutils.model.field.expression.On;
import com.cronutils.model.field.expression.QuestionMark;
import com.cronutils.model.field.expression.RandomExpression;
import com.cronutils.model.field.expression.Weekdays;
import com.cronutils.model.field.expression.visitor.FieldExpressionVisitor;
import com.cronutils.model.field.expression.visitor.FieldExpressionVisitorAdaptor;
import com.cronutils.model.field.expression.visitor.ValidationFieldExpressionVisitor;
import com.cronutils.model.field.expression.visitor.ValueMappingFieldExpressionVisitor;
import com.cronutils.model.field.value.FieldValue;
import com.cronutils.model.field.value.IntegerFieldValue;
import com.cronutils.model.field.value.SpecialChar;
import com.cronutils.model.field.value.SpecialCharFieldValue;
```

```java
import com.cronutils.model.time.CompositeExecutionTime;
import com.cronutils.model.time.ExecutionTime;
import com.cronutils.model.time.SingleExecutionTime;
import com.cronutils.model.time.generator.FieldValueGenerator;
import com.cronutils.model.time.generator.FieldValueGeneratorFactory;
import com.cronutils.model.time.generator.NoSuchValueException;
import com.cronutils.parser.CronParser;
import com.cronutils.parser.CronParserField;
import com.cronutils.parser.FieldParser;
import com.cronutils.utils.CronFrequencyComparator;
import com.cronutils.utils.DateUtils;
import com.cronutils.utils.RandomUtils;
import com.cronutils.utils.WeekendPolicy;
import com.cronutils.validation.Cron;
import com.cronutils.validation.CronValidator;
```

```java
import static com.cronutils.model.field.expression.FieldExpressionFactory.always;
import static com.cronutils.model.field.expression.FieldExpressionFactory.and;
import static com.cronutils.model.field.expression.FieldExpressionFactory.between;
import static com.cronutils.model.field.expression.FieldExpressionFactory.every;
import static com.cronutils.model.field.expression.FieldExpressionFactory.on;
import static com.cronutils.model.field.expression.FieldExpressionFactory.questionMark;
```

### API Catalog

| Name | Kind | Role |
|---|---|---|
| `Function` | interface | Callback carrier exposing `apply` for mapper and visitor customization. |
| `CronBuilder` | class | Creates crons through `cron`, field setters, `instance`, and the eight nickname factories. |
| `BaseCronTransformer` | abstract class | Calendar transformer protocol exposing `apply`. |
| `CalendarToCronTransformer` | class | Converts calendar state back to cron text. |
| `CronToCalendarTransformer` | class | Applies cron text to calendar state. |
| `CronConverter` | class | Fluent `using`/`from`/`to`/`convert` time-zone conversion facade. |
| `CronDescriptor` | class | Localized whole-cron and partial-field description facade with locale/resource-bundle factories. |
| `ConstantsMapper` | class | Weekday constants and `weekDayMapping` function. |
| `CronMapper` | class | General and predefined cron-dialect mapper factories. |
| `WeekDay` | class | Weekday numbering definition with `mapTo` and read accessors. |
| `Cron` | interface | Structured retrieval, serialization, definition, validation, equivalence, and overlap protocol. |
| `SingleCron` | class | Concrete cron backed by one field set. |
| `CompositeCron` | class | Ordered multi-cron container with squashed serialization. |
| `RebootCron` | class | Special `@reboot` cron model. |
| `CronType` | enum | `CRON4J`, `QUARTZ`, `UNIX`, `SPRING`, and `SPRING53` dialect names. |
| `CronConstraint` | abstract class | Described cross-field validation extension point. |
| `CronConstraintsFactory` | class | Factories for day-of-year/month/week constraint rules. |
| `CronDefinition` | class | Read-only definition projection for fields, mappings, constraints, nicknames, and day matching. |
| `CronDefinitionBuilder` | class | Fluent custom-definition builder and predefined-definition factory. |
| `CronNicknames` | enum | Eight supported nickname identifiers. |
| `CronField` | class | Field name, expression, constraint, comparator, and text carrier. |
| `CronFieldName` | enum | Eight canonical cron field identifiers and their order. |
| `FieldConstraints` | class | Range, period, special-character, string/int mapping, and strictness projection. |
| `FieldConstraintsBuilder` | class | Low-level constraint builder with range, mapping, strictness, and special-character controls. |
| `FieldDefinition` | class | Field name, constraints, optional flag, equality, and comparator carrier. |
| `DayOfWeekFieldDefinition` | class | Field definition extended with Monday numbering. |
| `FieldDefinitionBuilder` | class | General field registration builder with mappings, ranges, strictness, optionality, and `and`. |
| `FieldQuestionMarkDefinitionBuilder` | class | Field builder adding `supportsQuestionMark`. |
| `FieldSpecialCharsDefinitionBuilder` | class | Field builder adding `supportsHash`, `supportsL`, `supportsW`, and `supportsLW`. |
| `FieldDayOfWeekDefinitionBuilder` | class | Day-of-week builder adding `withMondayDoWValue` and covariant fluent members. |
| `FieldExpression` | abstract class | Root expression with `and`, `asString`, `accept`, `always`, and `questionMark`. |
| `Always` | class | Wildcard expression exposing visitor and text projections. |
| `QuestionMark` | class | Unspecified-field expression exposing visitor and text projections. |
| `And` | class | Mutable conjunction builder with child inspection and comma serialization. |
| `Between` | class | Range expression with endpoints, copy construction, visitor, and text projection. |
| `Every` | class | Period expression with base expression, period, visitor, and text projection. |
| `On` | class | Fixed or special value expression with time, nth, special-character, visitor, and text projections. |
| `RandomExpression` | class | OpenBSD tilde range/step expression with injected random selection. |
| `Weekdays` | enum | Seven weekdays with default, `WeekDay`, and `CronDefinition` numeric projections. |
| `FieldExpressionFactory` | class | Static factories for wildcard, unspecified, range, period, value, special, and conjunction expressions. |
| `FieldExpressionVisitor` | interface | Seven-overload expression visitor protocol. |
| `FieldExpressionVisitorAdaptor` | class | Identity visitor base for selective overrides. |
| `ValueMappingFieldExpressionVisitor` | class | Recursive visitor that transforms field values. |
| `ValidationFieldExpressionVisitor` | class | Constraint-checking visitor for all expression kinds. |
| `FieldValue` | abstract class | Serializable value carrier with `getValue` and final text projection. |
| `IntegerFieldValue` | class | Integer field value. |
| `SpecialCharFieldValue` | class | `SpecialChar` field value. |
| `SpecialChar` | enum | `LW`, `L`, `W`, `HASH`, `QUESTION_MARK`, `TILDE`, and `NONE` vocabulary. |
| `ExecutionTime` | interface | Factory and previous/next/duration/match/range execution queries. |
| `SingleExecutionTime` | class | Factory-produced temporal projection for a single cron. |
| `CompositeExecutionTime` | class | Aggregated temporal projection for component execution-time objects. |
| `FieldValueGenerator` | abstract class | Low-level next/previous/match/candidate field-value protocol. |
| `FieldValueGeneratorFactory` | class | Generic and calendar-context generator factories. |
| `NoSuchValueException` | exception | Checked result for an exhausted field-value search. |
| `CronParser` | class | Definition-bound full-expression parser. |
| `CronParserField` | class | Definition-bound single-field parser and field-order comparator. |
| `FieldParser` | class | Constraint-bound parser for typed field expressions. |
| `CronFrequencyComparator` | class | Orders crons by execution count over a zoned interval. |
| `DateUtils` | class | Inclusive workday counting by span or end date. |
| `RandomUtils` | class | Default or injected-random integer source used by random expressions. |
| `WeekendPolicy` | enum | Three two-day weekend policies and distance helpers. |
| `com.cronutils.validation.Cron` | annotation | Runtime Jakarta field constraint exposing `message`, `groups`, `payload`, and `type`. |
| `CronValidator` | class | Jakarta validator with `initialize` and `isValid` behavior. |

### CLI Entry Points

There is no console script or executable main class for this package. The satellite CLI is not part of this artifact. Programmatic use is through Java imports and the Maven dependency.

## Appendix A: Environment

The working environment runs Java 17 on Linux without network access. Maven 3 resolves the task's cached artifacts. The runtime API dependencies available to the project are SLF4J API, Jakarta Validation API, Jakarta EL API and implementation, and Lombok as declared by the source project; tests receive their separately declared local test dependencies.

The project must declare `com.cronutils` as `groupId`, `cron-utils` as `artifactId`, `9.2.2-SNAPSHOT` as `version`, and Java source and target level 17 in a standard root `pom.xml`. The root project is a single Maven JAR module, and the implementation source must live under the conventional `src/main/java` and `src/main/resources` roots.

## Appendix B: Assessment Notes

Assessment exercises public Java APIs through Maven tests. Coverage spans definition building, expression factories and visitors, parsing and canonical serialization, structured inspection, validation, nicknames and composite crons, locale descriptions, dialect and weekday mapping, execution-time queries, frequency and workday utilities, time-zone conversion, Bean Validation, errors, and cross-view consistency. Assessment considers observable contract behavior; private structure, exact exception wording, logging, and representation-only text are not assessed.

