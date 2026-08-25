# cron-utils Behavioral Clause Sidecar — v3

This internal sidecar maps every retained atomic behavioral rule in `spec_v3.md` to a stable identifier. Quoted text is verbatim from the candidate-visible body; section anchors identify its host H2. Closely coupled assertions inside one sentence form one rule family and therefore one clause.

Total clauses: 129.

## Representative Workflows

**CRON-WF-001**

> WHEN parsing succeeds, THEN the parser must normalize whitespace and symbolic names against the supplied definition, and the resulting cron must retain that definition for validation, inspection, serialization, and local-time execution queries.

**CRON-WF-002**

> The builder and parser must produce the same structured model so description and mapping operate without reparsing the canonical string.

**CRON-WF-003**

> WHEN a custom definition is finalized, THEN its fluent builders must register fields in canonical field order and carry ranges, value mappings, special-character support, optionality, nickname support, and cross-field constraints into later parsing and validation.

## Definitions and Expression Construction

**CRON-DEF-001**

> The `CronType` values must be `CRON4J`, `QUARTZ`, `UNIX`, `SPRING`, and `SPRING53`.

**CRON-DEF-002**

> The `CronDefinitionBuilder.instanceDefinitionFor(cronType)` method must return a new definition for the selected `CronType`.

**CRON-DEF-003**

> The `CRON4J` definition must contain minute, hour, day-of-month, month, and day-of-week fields; it must use ranges 0–59, 0–23, 0–31, 1–12, and 0–6 respectively, must support `L` in day-of-month, and must match day-of-month together with day-of-week.

**CRON-DEF-004**

> The `UNIX` definition must contain minute, hour, day-of-month, month, and day-of-week fields with ranges 0–59, 0–23, 1–31, 1–12, and 0–7 respectively, and day-of-week value 7 must map to 0.

**CRON-DEF-005**

> The `QUARTZ` definition must contain second, minute, hour, day-of-month, month, day-of-week, and optional year fields; it must use ranges 0–59, 0–59, 0–23, 1–31, 1–12, 1–7, and 1970–2099 respectively.

**CRON-DEF-006**

> The `QUARTZ` definition must support `L`, `W`, `LW`, and `?` for day-of-month, `L`, `#`, and `?` for day-of-week, and it must require at least one of day-of-month or day-of-week to be `?`.

**CRON-DEF-007**

> The `SPRING` definition must contain six fields from second through day-of-week, must use day-of-week range 0–7 with 7 mapped to 0, and must support `#` and `?` for day-of-week but not the `L`, `W`, or `LW` extensions.

**CRON-DEF-008**

> The `SPRING53` definition must use the same six-field order and day-of-week mapping as `SPRING`, must add `L`, `W`, and `LW` support where defined for Spring 5.3, and must support the yearly, annually, monthly, weekly, daily, midnight, and hourly nicknames.

**CRON-DEF-009**

> WHEN `cronType` is null or has no definition, THEN `instanceDefinitionFor` must raise a runtime argument/null error rather than return a fallback dialect.

**CRON-DEF-010**

> The `CronDefinitionBuilder.defineCron()` factory must return an initially empty builder whose `withSeconds`, `withMinutes`, `withHours`, `withDayOfMonth`, `withMonth`, `withDayOfWeek`, `withYear`, and `withDayOfYear` methods select a field-specific builder.

**CRON-DEF-011**

> The field-definition builders must preserve the configured `withValidRange`, `withStrictRange`, integer mappings, `optional`, `supportsHash`, `supportsL`, `supportsW`, `supportsLW`, `supportsQuestionMark`, and `withMondayDoWValue` settings in the resulting `FieldDefinition` and `FieldConstraints` projections.

**CRON-DEF-012**

> The eight `withSupportedNickname*` methods must add their corresponding `CronNicknames` value, and `withCronValidation` must add its `CronConstraint` to the built definition.

**CRON-DEF-013**

> WHEN a mandatory field is registered after an optional field, THEN `CronDefinitionBuilder.register` must raise `IllegalArgumentException`.

**CRON-DEF-014**

> WHEN `instance()` is called, THEN the builder must return a `CronDefinition` whose field definitions are ordered by `CronFieldName.getOrder()` and whose constraint and nickname sets reflect the registrations.

**CRON-DEF-015**

> WHEN a non-reboot `CronDefinition` receives null or empty field definitions, null constraints, null nicknames, or an optional first field, THEN its constructor must raise `NullPointerException` or `IllegalArgumentException` according to the violated precondition.

**CRON-DEF-016**

> `FieldExpressionFactory` must construct `Always`, `QuestionMark`, `On`, `Between`, `Every`, and `And` values through `always`, `questionMark`, the four `on` overloads, the two `between` overloads, the two `every` overloads, and `and`.

**CRON-DEF-028**

> A `Between` value must support construction from a public `FieldValue` `from` endpoint followed by a public `FieldValue` `to` endpoint; each endpoint must accept any public `FieldValue` carrier, including `IntegerFieldValue` and `SpecialCharFieldValue`.

**CRON-DEF-024**

> An `Every` value must support construction from one `IntegerFieldValue` period, or from a `FieldExpression` base followed by an `IntegerFieldValue` period; the period-only form must use the all-values `Always` expression as its base.

**CRON-DEF-025**

> An `On` value must support construction from one `SpecialCharFieldValue`, one `IntegerFieldValue` time, an `IntegerFieldValue` time followed by a `SpecialCharFieldValue`, or an `IntegerFieldValue` time followed by a `SpecialCharFieldValue` and then an `IntegerFieldValue` nth value.

**CRON-DEF-026**

> The four `FieldExpressionFactory.on` forms must accept, respectively, a `SpecialChar`, an integer time, an integer time followed by a `SpecialChar`, or an integer time followed by a `SpecialChar` and then an integer nth value.

**CRON-DEF-027**

> The `FieldExpressionFactory.and` method must receive a single ordered `List` of `FieldExpression` values and retain that order in the resulting `And` conjunction.

**CRON-DEF-017**

> The `asString()` methods must serialize `Always` as `*`, `QuestionMark` as `?`, `Between` as `from-to`, `And` as comma-separated child expressions, and `Every` as `expression/period`.

**CRON-DEF-018**

> WHEN `Every` represents all values with a period of one, THEN `Every.asString()` returns `*`.

**CRON-DEF-019**

> The `On.asString()` method must serialize ordinary values directly, `HASH` as `time#nth`, `W` as `timeW`, `L` as either `L`, `L-nth`, or `timeL`, and `QUESTION_MARK` as `?`.

**CRON-DEF-020**

> The `RandomExpression` methods must retain optional `from`, `to`, and `step` bounds, must serialize them with the OpenBSD `~` syntax, and must produce a value inside the caller-supplied field bounds through the injected `RandomUtils`.

**CRON-DEF-021**

> The `FieldExpressionVisitor` protocol must dispatch every expression subtype to its matching `visit` overload; `FieldExpressionVisitorAdaptor` must return the visited expression unchanged, and `ValueMappingFieldExpressionVisitor` must recursively map contained `FieldValue` instances.

**CRON-DEF-022**

> WHEN an expression satisfies the supplied constraints, THEN `ValidationFieldExpressionVisitor` must return that expression.

**CRON-DEF-023**

> WHEN an `On` expression is created with null components, a hash without an `nth` value, or a negative integer through `FieldExpressionFactory.on(int)`, THEN construction must raise `NullPointerException` or `IllegalArgumentException`.

## Parsing, Serialization, and Structured Inspection

**CRON-PAR-001**

> A `CronParser` must accept a non-null `CronDefinition`, and its `parse(expression)` method must collapse consecutive whitespace, trim surrounding whitespace, and match fields in `CronFieldName` order.

**CRON-PAR-002**

> WHEN the definition ends with one or more optional fields, THEN `CronParser` must accept each supported suffix omission while retaining all mandatory leading fields.

**CRON-PAR-003**

> WHEN a field contains a supported symbolic month or weekday name, THEN parsing must resolve it case-insensitively through the field definition's string mapping.

**CRON-PAR-004**

> WHEN a field uses `*`, `?`, comma lists, hyphen ranges, slash periods, `L`, `W`, `LW`, `#`, or `~` and the field constraints support that form, THEN `FieldParser` must return the corresponding typed `FieldExpression`.

**CRON-PAR-005**

> WHEN an expression starts with a supported nickname, THEN `CronParser` must return the matching cron produced by `CronBuilder.yearly`, `annually`, `monthly`, `weekly`, `daily`, `midnight`, `hourly`, or `reboot`.

**CRON-PAR-006**

> WHEN an expression contains `||`, THEN `CronParser` must parse each complete subexpression and return a `CompositeCron` containing those crons in source order.

**CRON-PAR-007**

> WHEN one or more fields contain aligned `|` alternatives, THEN `CronParser` must expand the aligned alternatives into a `CompositeCron`, and `CompositeCron.asString()` must squash identical field columns back to one value while retaining distinct columns with `|`.

**CRON-PAR-008**

> WHEN an expression is null, empty, has an unsupported field count or nickname, has a trailing comma, has an incomplete range or period, or violates field constraints, THEN parsing must raise `NullPointerException` or `IllegalArgumentException` rather than return a partial cron.

**CRON-PAR-009**

> A `SingleCron` must retain its `CronDefinition` and one `CronField` per supplied `CronFieldName`, and `retrieveFieldsAsMap()` must return an unmodifiable map.

**CRON-PAR-010**

> WHEN the definition contains `name`, THEN `SingleCron.retrieve(name)` returns the matching field.

**CRON-PAR-011**

> WHEN the definition lacks `name`, THEN `SingleCron.retrieve(name)` returns null.

**CRON-PAR-012**

> The `SingleCron.asString()` method must order fields by `CronFieldName.getOrder()` and join each expression's canonical text with single spaces.

**CRON-PAR-013**

> The `CronField` and `FieldDefinition` accessors must return their field name, expression or constraints, and optional status, while their comparator factories must sort by canonical field order.

**CRON-PAR-014**

> The `CronDefinition` accessors must return defensive or unmodifiable projections of field definitions, constraints, and nicknames, and `containsFieldDefinition` must report membership by `CronFieldName`.

**CRON-PAR-015**

> WHEN `SingleCron` receives a null definition, a null field list, or `retrieve(null)`, THEN it must raise `NullPointerException`.

## Validation, Composite Behavior, and Equivalence

**CRON-VAL-001**

> `SingleCron.validate()` must validate every expression against its field constraints, then apply every registered `CronConstraint`, and return the same cron on success.

**CRON-VAL-002**

> WHEN `CronConstraintsFactory.ensureQuartzDayOfMonthAndDayOfWeekValidation()` is active and at least one of day-of-month or day-of-week is `?`, THEN validation must accept that cross-field combination.

**CRON-VAL-003**

> WHEN `ensureEitherDayOfWeekOrDayOfMonth()` is active, THEN validation must require exactly one of day-of-month or day-of-week to be specified while the other is `?`.

**CRON-VAL-004**

> WHEN `ensureEitherDayOfYearOrMonth()` is active and day-of-year is specified, THEN validation must require both day-of-month and day-of-week to be `?`.

**CRON-VAL-005**

> WHEN a field expression violates its range, period, mapping, special-character support, or cross-field constraint, THEN `validate()` must raise `IllegalArgumentException`.

**CRON-VAL-006**

> A `CompositeCron` must contain a non-empty unmodifiable list of crons that all share an equal `CronDefinition`.

**CRON-VAL-007**

> WHEN the composite list is null, empty, or contains different definitions, THEN the `CompositeCron` constructor must raise `NullPointerException` or `IllegalArgumentException`.

**CRON-VAL-008**

> The `CompositeCron.validate()` method must validate every component and return the composite.

**CRON-VAL-009**

> The `CompositeCron.retrieve`, `retrieveFieldsAsMap`, and mapper-based `equivalent` operations must raise `UnsupportedOperationException`.

**CRON-VAL-010**

> A `RebootCron` must serialize as `@reboot`, must return an empty field map and null for a named field, and must overlap only another `RebootCron`.

**CRON-VAL-011**

> `Cron.equivalent(other)` must compare canonical strings under the assumption of a shared definition, while `Cron.equivalent(mapper, other)` must map `other` before comparing canonical strings.

**CRON-VAL-012**

> The `CompositeCron.equivalent(other)` method must compare its squashed canonical string.

**CRON-VAL-013**

> WHEN any component overlaps `other`, THEN `CompositeCron.overlap(other)` returns true.

**CRON-VAL-014**

> WHEN either cron has no future execution, THEN `SingleCron.overlap(other)` must return false.

**CRON-VAL-015**

> WHEN both crons have future executions, THEN `SingleCron.overlap(other)` must report whether their upcoming public execution projections share a time.

**CRON-VAL-016**

> WHEN a required cron or mapper argument is null, THEN comparison or overlap operations must raise `NullPointerException` rather than report equivalence.

## Human-Readable Descriptions

**CRON-DESC-001**

> `CronDescriptor.instance()` must use `Locale.UK`, `CronDescriptor.instance(locale)` must load the packaged bundle for `locale`, and the public `ResourceBundle` constructor must use the supplied bundle.

**CRON-DESC-002**

> The `getResourceBundle()` method returns the active bundle, and the artifact must package base plus German, Greek, English, Spanish, French, Indonesian, Italian, Japanese, Korean, Dutch, Polish, Portuguese, Romanian, Russian, Swahili, Turkish, and Chinese bundles.

**CRON-DESC-003**

> `CronDescriptor.describe(cron)` must combine time-of-day, day-of-month, month, day-of-week, and year phrases, normalize repeated whitespace, and use weekday numbering from the cron definition.

**CRON-DESC-004**

> The `describeHHmmss`, `describeDayOfMonth`, `describeMonth`, `describeDayOfWeek`, and `describeYear` methods must return the corresponding partial phrase using the active resource bundle.

**CRON-DESC-005**

> WHEN the cron is a `RebootCron`, THEN `describe` must return the bundle's reboot phrase.

**CRON-DESC-006**

> WHEN `cron` or a required locale/resource bundle is null or unavailable, THEN descriptor construction or description must raise the ordinary Java null or resource-loading exception.

## Dialect and Calendar Conversion

**CRON-MAP-001**

> `CronMapper` must expose predefined factories for Cron4j-to-Quartz, Quartz-to-Cron4j, Quartz-to-Unix, Unix-to-Quartz, Quartz-to-Spring, and Spring-to-Quartz, plus `sameCron(definition)`.

**CRON-MAP-002**

> The general `CronMapper` constructor must accept non-null `from`, `to`, and `cronRules` values, and `map(cron)` must return a validated cron under the target definition.

**CRON-MAP-003**

> WHEN a target dialect introduces leading fields absent from the source, THEN mapping must set those fields to zero.

**CRON-MAP-004**

> WHEN a target dialect introduces trailing fields absent from the source, THEN mapping must set those fields to `*`.

**CRON-MAP-005**

> WHEN weekday numbering differs, THEN mapping must transform direct values, ranges, lists, and stepped expressions through the source and target `WeekDay` definitions while preserving special-character values.

**CRON-MAP-006**

> WHEN a source `?` is unsupported in the target day field, THEN mapping must replace it with `*`.

**CRON-MAP-007**

> WHEN a target dialect requires a day question mark and neither source day field has one, THEN mapping must replace an all-values day field with `?`.

**CRON-MAP-008**

> WHEN a `RebootCron` is mapped, THEN the target must return a new `RebootCron` only if it supports the `REBOOT` nickname.

**CRON-MAP-009**

> WHEN the input cron is null, the constructor inputs are null, the target does not support reboot, or the mapped expression violates target constraints, THEN `CronMapper` must raise `NullPointerException` or `IllegalArgumentException`.

**CRON-MAP-010**

> `ConstantsMapper.QUARTZ_WEEK_DAY`, `JAVA8`, and `CRONTAB_WEEK_DAY` must represent Monday values 2, 1, and 1 respectively, with only the crontab definition using a zero-based range.

**CRON-MAP-011**

> The `WeekDay.mapTo` and `ConstantsMapper.weekDayMapping` methods must preserve the represented weekday while shifting or wrapping values between zero-based and one-based definitions.

**CRON-MAP-017**

> The `WeekDay.mapTo` method must receive the integer `dayOfWeek` value first and the target `WeekDay` definition second, and return the directly mapped integer.

**CRON-MAP-015**

> The `ConstantsMapper.weekDayMapping` method must receive a source `WeekDay` definition, a target `WeekDay` definition, and an integer weekday value, and return the directly mapped integer.

**CRON-MAP-012**

> WHEN a `WeekDay` is created with a negative Monday value, THEN its constructor must raise `IllegalArgumentException`.

**CRON-MAP-016**

> The `CronToCalendarTransformer` and `CalendarToCronTransformer` classes must each support public construction without arguments before being supplied to `CronConverter`.

**CRON-MAP-013**

> A `CronConverter` must accept a `CronToCalendarTransformer` and a `CalendarToCronTransformer`, retain the cron text supplied through `using`, retain the source and target `ZoneId` values supplied through `from` and `to`, and return the transformed cron text through `convert`.

**CRON-MAP-014**

> WHEN `using`, `from`, or `to` has not supplied the required value before `convert`, THEN conversion must fail through the ordinary Java runtime error instead of fabricating a default cron or zone.

## Execution Times and Calendar Utilities

**CRON-TIME-001**

> `ExecutionTime.forCron(cron)` must return a single-cron implementation for `SingleCron`, a `CompositeExecutionTime` for `CompositeCron`, and an empty-result implementation for other `Cron` implementations.

**CRON-TIME-002**

> WHEN a matching execution exists, THEN `nextExecution(date)` and `lastExecution(date)` must return the nearest match strictly after or before the reference in the reference `ZonedDateTime` zone.

**CRON-TIME-003**

> WHEN no matching execution exists, THEN `nextExecution(date)` and `lastExecution(date)` must return `Optional.empty()`.

**CRON-TIME-004**

> The `timeToNextExecution(date)` and `timeFromLastExecution(date)` methods must return the `Duration` between the reference and the corresponding next or previous result, or `Optional.empty()` with no result.

**CRON-TIME-005**

> The `isMatch(date)` method must report whether every active field rule matches the supplied local zoned date-time.

**CRON-TIME-006**

> The `getExecutionDates(startDate,endDate)` method must return successive executions after `startDate` through and including `endDate`, and `countExecutions` returns that list's size.

**CRON-TIME-007**

> WHEN `endDate` is equal to or before `startDate`, THEN `getExecutionDates` and `countExecutions` must raise `IllegalArgumentException`.

**CRON-TIME-008**

> WHEN a required date or cron is null, THEN execution-time construction or query methods must raise `NullPointerException`.

**CRON-TIME-009**

> A `CompositeExecutionTime` must require a non-empty list and must return the earliest component next execution and the latest component previous execution.

**CRON-TIME-010**

> WHEN any component matches, THEN `CompositeExecutionTime.isMatch` must return true.

**CRON-TIME-011**

> WHEN its execution-time list is null or empty, THEN the `CompositeExecutionTime` constructor must raise `NullPointerException` or `IllegalArgumentException`.

**CRON-TIME-012**

> A `CronFrequencyComparator` must compare two crons by subtracting their execution counts over the constructor's `startDate` to `endDate` interval.

**CRON-TIME-013**

> The `WeekendPolicy` values must be `THURSDAY_FRIDAY`, `FRIDAY_SATURDAY`, and `SATURDAY_SUNDAY`, and `daysToWeekend` and `daysFromWeekend` must use the selected consecutive two-day weekend.

**CRON-TIME-014**

> The two `DateUtils.workdaysCount` overloads must count inclusive non-weekend days between `startDate` and either `startDate.plusDays(days)` or `endDate`, then subtract holidays in that interval.

**CRON-TIME-015**

> WHEN required dates, policies, cron values, or holiday collections are null, THEN the calendar utilities must raise the ordinary Java null error.

## Bean Validation and Low-Level Extension Points

**CRON-EXT-001**

> The `com.cronutils.validation.Cron` annotation must target fields and annotation types at runtime, must use `CronValidator`, and must expose `message`, `groups`, `payload`, and required `type` members.

**CRON-EXT-002**

> WHEN the annotated value is null, THEN `CronValidator.isValid` must return true.

**CRON-EXT-003**

> WHEN the annotated value parses and validates under the annotation's `CronType`, THEN `CronValidator.isValid` must return true.

**CRON-EXT-004**

> WHEN parsing or validation raises `IllegalArgumentException`, THEN `CronValidator.isValid` must disable the default violation, add a violation using the validation error text, and return false.

**CRON-EXT-005**

> A `FieldValueGenerator` must expose next-value, previous-value, match, and bounded candidate-generation operations for its `CronField`.

**CRON-EXT-006**

> The `FieldValueGeneratorFactory` must select a generator through `forCronField` and must expose year-, day-of-year-, day-of-month-, and day-of-week-specific factories with the calendar context required by each field.

**CRON-EXT-007**

> WHEN no next or previous field value exists within the generator's domain, THEN generator search must raise `NoSuchValueException`.

## State Model

**CRON-STATE-001**

> The `CronDefinition` and `CronParser` objects must be thread-safe for concurrent read and parse use after construction; fluent builders, `And`, converter setup, and injected random generators remain caller-confined mutable construction objects.

## Error Semantics

**CRON-ERR-001**

> WHEN a required value is null, THEN the receiving public operation must raise `NullPointerException`.

**CRON-ERR-002**

> WHEN a required collection is empty, THEN the receiving constructor must raise `IllegalArgumentException`.

**CRON-ERR-003**

> WHEN cron text violates syntax or its definition, THEN parsing must raise `IllegalArgumentException`.

**CRON-ERR-004**

> WHEN a mandatory field follows an optional field, THEN registration must raise `IllegalArgumentException`.

**CRON-ERR-005**

> WHEN a cross-field constraint fails, THEN parsing or `validate()` must raise `IllegalArgumentException`.

**CRON-ERR-006**

> WHEN an unsupported composite operation is called, THEN `CompositeCron` must raise `UnsupportedOperationException`.

**CRON-ERR-007**

> WHEN the target lacks reboot support, THEN mapping must raise `IllegalArgumentException`.

**CRON-ERR-008**

> WHEN an execution range end is not after its start, THEN the range query must raise `IllegalArgumentException`.

**CRON-ERR-009**

> WHEN generator search is exhausted, THEN it must raise `NoSuchValueException`.

**CRON-ERR-010**

> WHEN non-null annotation input is invalid, THEN validation must return `false` and add a constraint violation.

## Cross-View Invariants

**CRON-INV-001**

> A cron produced by `CronBuilder.instance()` must expose the same field expressions through `retrieve`, `retrieveFieldsAsMap`, and `asString()` in definition order.

**CRON-INV-002**

> A canonical string returned by `SingleCron.asString()` must parse under the same `CronDefinition` into a cron that is `equivalent` to the source.

**CRON-INV-003**

> A cron returned by `CronParser.parse()` must already satisfy the same field and cross-field constraints enforced by its later `validate()` call.

**CRON-INV-004**

> A `CronMapper` result must retain schedule meaning across weekday-numbering changes, must expose the target `CronDefinition`, and must pass target validation.

**CRON-INV-005**

> A `CompositeCron` squashed string must preserve its component schedules, and `ExecutionTime.forCron(composite)` must select next and previous executions from the same component set.

**CRON-INV-006**

> The result of `ExecutionTime.isMatch(date)` must agree with whether `date` appears as an execution boundary produced by neighboring next/previous queries for the same cron and zone.

**CRON-INV-007**

> `countExecutions(start,end)` must equal the size of `getExecutionDates(start,end)`, and `CronFrequencyComparator` must order crons from those same counts.

**CRON-INV-008**

> A `CronDescriptor` phrase must be derived from the same fields returned by structured inspection and must use the weekday numbering carried by the same definition.

**CRON-INV-009**

> A `Cron` annotation's `type` must select the same predefined definition as `CronDefinitionBuilder.instanceDefinitionFor(type)`, so Bean Validation must agree with direct parsing and validation.

**CRON-INV-010**

> A `RebootCron` must remain `@reboot` through serialization, description, equivalence, and supported dialect mapping, while execution-time queries must return no calendar occurrence.

## Appendix A: Environment

**CRON-ENV-001**

> The project must declare `com.cronutils` as `groupId`, `cron-utils` as `artifactId`, `9.2.2-SNAPSHOT` as `version`, and Java source and target level 17 in a standard root `pom.xml`. The root project is a single Maven JAR module, and the implementation source must live under the conventional `src/main/java` and `src/main/resources` roots.

