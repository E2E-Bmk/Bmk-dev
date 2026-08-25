package integration;

import com.cronutils.builder.CronBuilder;
import com.cronutils.converter.CalendarToCronTransformer;
import com.cronutils.converter.CronConverter;
import com.cronutils.converter.CronToCalendarTransformer;
import com.cronutils.descriptor.CronDescriptor;
import com.cronutils.mapper.CronMapper;
import com.cronutils.model.CompositeCron;
import com.cronutils.model.Cron;
import com.cronutils.model.CronType;
import com.cronutils.model.definition.CronDefinition;
import com.cronutils.model.definition.CronDefinitionBuilder;
import com.cronutils.model.field.CronField;
import com.cronutils.model.field.CronFieldName;
import com.cronutils.model.time.ExecutionTime;
import com.cronutils.model.time.generator.FieldValueGenerator;
import com.cronutils.model.time.generator.FieldValueGeneratorFactory;
import com.cronutils.parser.CronParser;
import com.cronutils.utils.CronFrequencyComparator;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.time.Duration;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import org.junit.jupiter.api.Test;

import static com.cronutils.model.field.expression.FieldExpressionFactory.always;
import static com.cronutils.model.field.expression.FieldExpressionFactory.between;
import static com.cronutils.model.field.expression.FieldExpressionFactory.on;
import static com.cronutils.model.field.expression.FieldExpressionFactory.questionMark;
import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GeneratedIntegrationOracleTest {
    private static final ZoneId UTC = ZoneId.of("UTC");

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-WF-002, CRON-INV-001, CRON-PAR-009, CRON-PAR-012, CRON-DEF-026
     * Depends-On: basicExpressionFactoriesSerializeCanonically, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void builderExposesConsistentStructuredViews() {
        Cron built = builtWorkdayQuartz();
        Map<CronFieldName, CronField> fields = built.retrieveFieldsAsMap();
        assertAll(
                () -> assertEquals("0 23 * ? * 2-6 *", built.asString()),
                () -> assertEquals("23", built.retrieve(CronFieldName.MINUTE).getExpression().asString()),
                () -> assertEquals("2-6", fields.get(CronFieldName.DAY_OF_WEEK).getExpression().asString()),
                () -> assertEquals(List.of(CronFieldName.SECOND, CronFieldName.MINUTE, CronFieldName.HOUR,
                                CronFieldName.DAY_OF_MONTH, CronFieldName.MONTH, CronFieldName.DAY_OF_WEEK,
                                CronFieldName.YEAR),
                        new ArrayList<>(fields.keySet())));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-WF-002, CRON-INV-008, CRON-DESC-003, CRON-MAP-002, CRON-DEF-026
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void builtAndParsedCronsShareDescriptionAndMappingProjections() {
        Cron built = builtWorkdayQuartz();
        Cron parsed = quartzParser().parse(built.asString());
        CronDescriptor descriptor = CronDescriptor.instance(Locale.UK);
        assertAll(
                () -> assertEquals(descriptor.describe(built), descriptor.describe(parsed)),
                () -> assertEquals(CronMapper.fromQuartzToCron4j().map(built).asString(),
                        CronMapper.fromQuartzToCron4j().map(parsed).asString()),
                () -> assertTrue(built.equivalent(parsed)));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-WF-003, CRON-DEF-011, CRON-DEF-014, CRON-PAR-001
     * Depends-On: customDefinitionRetainsRegisteredFields, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void customDefinitionFeedsParserAndStructuredInspection() {
        CronDefinition definition = customDefinition();
        Cron cron = new CronParser(definition).parse("5 14 2 3 1");
        assertAll(
                () -> assertSame(definition, cron.getCronDefinition()),
                () -> assertEquals("5 14 2 3 1", cron.asString()),
                () -> assertEquals("14", cron.retrieve(CronFieldName.HOUR).getExpression().asString()));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-WF-003, CRON-INV-001, CRON-VAL-001, CRON-DEF-026
     * Depends-On: customDefinitionRetainsRegisteredFields, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void customDefinitionFeedsCronBuilderAndValidation() {
        CronDefinition definition = customDefinition();
        Cron cron = CronBuilder.cron(definition)
                .withMinute(on(5)).withHour(on(14)).withDoM(on(2)).withMonth(on(3)).withDoW(on(1))
                .instance();
        assertAll(
                () -> assertEquals("5 14 2 3 1", cron.asString()),
                () -> assertSame(cron, cron.validate()),
                () -> assertSame(definition, cron.getCronDefinition()));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-WF-003, CRON-TIME-001, CRON-TIME-002
     * Depends-On: customDefinitionRetainsRegisteredFields, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void customDefinitionCronFeedsExecutionQueries() {
        Cron cron = new CronParser(customDefinition()).parse("5 14 * * *");
        ZonedDateTime reference = at(2026, 8, 17, 13, 0, 0);
        ExecutionTime time = ExecutionTime.forCron(cron);
        Optional<ZonedDateTime> next = time.nextExecution(reference);
        assertEquals(Optional.of(at(2026, 8, 17, 14, 5, 0)), next);
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-WF-003, CRON-VAL-005, CRON-ERR-003
     * Depends-On: customDefinitionRetainsRegisteredFields, malformedQuartzSyntaxIsRejected
     */
    @Test
    void customDefinitionRejectsOutOfRangeText() {
        CronParser parser = new CronParser(customDefinition());
        assertThrows(IllegalArgumentException.class, () -> parser.parse("60 14 2 3 1"));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-WF-001, CRON-INV-003, CRON-TIME-001, CRON-TIME-002
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void parsedQuartzCronValidatesAndSchedules() {
        Cron cron = quartzParser().parse("0 0 12 ? * MON-FRI *");
        ZonedDateTime mondayMorning = at(2026, 8, 17, 10, 0, 0);
        ExecutionTime time = ExecutionTime.forCron(cron);
        Optional<ZonedDateTime> next = time.nextExecution(mondayMorning);
        assertAll(
                () -> assertSame(cron, cron.validate()),
                () -> assertEquals(Optional.of(at(2026, 8, 17, 12, 0, 0)), next));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-WF-001, CRON-PAR-009, CRON-PAR-010, CRON-DESC-003
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, cronFieldNamesHaveCanonicalOrder
     */
    @Test
    void parsedQuartzCronSupportsInspectionAndDescription() {
        Cron cron = quartzParser().parse("0 23 * ? * MON-FRI *");
        String description = CronDescriptor.instance(Locale.UK).describe(cron);
        assertAll(
                () -> assertEquals("23", cron.retrieve(CronFieldName.MINUTE).getExpression().asString()),
                () -> assertEquals(7, cron.retrieveFieldsAsMap().size()),
                () -> assertFalse(description.isBlank()));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-WF-001, CRON-INV-006, CRON-TIME-004, CRON-TIME-005
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, periodFactoriesSerializeBaseAndPeriod
     */
    @Test
    void parsedHourlyCronHasCoherentTimeProjections() {
        ExecutionTime time = ExecutionTime.forCron(quartzParser().parse("0 0 * ? * * *"));
        ZonedDateTime reference = at(2026, 8, 17, 10, 15, 30);
        Optional<Duration> toNext = time.timeToNextExecution(reference);
        Optional<Duration> fromLast = time.timeFromLastExecution(reference);
        assertAll(
                () -> assertEquals(Optional.of(Duration.ofMinutes(44).plusSeconds(30)), toNext),
                () -> assertEquals(Optional.of(Duration.ofMinutes(15).plusSeconds(30)), fromLast),
                () -> assertTrue(time.isMatch(at(2026, 8, 17, 11, 0, 0))));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-INV-001, CRON-PAR-009, CRON-PAR-014, CRON-DEF-026
     * Depends-On: quartzDefinitionExposesSpecifiedFields, cronFieldNamesHaveCanonicalOrder
     */
    @Test
    void structuredFieldMapIsUnmodifiableAndStillReadable() {
        Cron cron = builtWorkdayQuartz();
        Map<CronFieldName, ?> fields = cron.retrieveFieldsAsMap();
        assertAll(
                () -> assertEquals("0 23 * ? * 2-6 *", cron.asString()),
                () -> assertTrue(fields.containsKey(CronFieldName.DAY_OF_WEEK)),
                () -> assertThrows(UnsupportedOperationException.class, fields::clear));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-INV-002, CRON-PAR-012, CRON-VAL-011
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void quartzCanonicalTextRoundTripsToEquivalentCron() {
        Cron source = quartzParser().parse("0 23 * ? * MON-FRI *");
        Cron reparsed = quartzParser().parse(source.asString());
        assertAll(
                () -> assertTrue(source.equivalent(reparsed)),
                () -> assertEquals(source.asString(), reparsed.asString()),
                () -> assertNotSame(source, reparsed));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-INV-002, CRON-PAR-003, CRON-PAR-012
     * Depends-On: unixParserCanonicalizesSymbolicWeekday, quartzParserNormalizesWhitespaceAndNames
     */
    @Test
    void unixCanonicalTextRoundTripsToEquivalentCron() {
        CronParser parser = parser(CronType.UNIX);
        Cron source = parser.parse("0 6 * JAN MON");
        Cron reparsed = parser.parse(source.asString());
        assertTrue(source.equivalent(reparsed));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-INV-003, CRON-VAL-001, CRON-VAL-002, CRON-ERR-005
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, malformedQuartzSyntaxIsRejected
     */
    @Test
    void parsingAndLaterValidationAgreeOnQuartzDayConstraint() {
        Cron valid = quartzParser().parse("0 0 12 ? * MON *");
        assertAll(
                () -> assertSame(valid, valid.validate()),
                () -> assertThrows(IllegalArgumentException.class,
                        () -> quartzParser().parse("0 0 12 1 * MON *")));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-INV-004, CRON-MAP-002, CRON-MAP-005, CRON-MAP-006, CRON-DEF-026
     * Depends-On: basicExpressionFactoriesSerializeCanonically, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void quartzToCron4jMappingProducesValidatedTarget() {
        Cron quartz = builtWorkdayQuartz();
        Cron cron4j = CronMapper.fromQuartzToCron4j().map(quartz);
        CronDefinition target = cron4j.getCronDefinition();
        assertAll(
                () -> assertEquals("23 * * * 1-5", cron4j.asString()),
                () -> assertSame(cron4j, cron4j.validate()),
                () -> assertEquals(5, target.getFieldDefinitions().size()),
                () -> assertFalse(target.containsFieldDefinition(CronFieldName.SECOND)));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-INV-005, CRON-PAR-006, CRON-PAR-007, CRON-VAL-012
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void compositeSquashedTextRoundTripsToEquivalentComposite() {
        Cron composite = quartzParser().parse("0 0 12 ? * MON * || 0 30 12 ? * TUE *");
        Cron reparsed = quartzParser().parse(composite.asString());
        assertAll(
                () -> assertEquals("0 0|30 12 ? * 2|3 *", composite.asString()),
                () -> assertTrue(composite.equivalent(reparsed)),
                () -> assertEquals(2, ((CompositeCron) composite).getCrons().size()));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-INV-005, CRON-TIME-009, CRON-TIME-010
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void compositeExecutionSelectsNearestComponentResults() {
        Cron composite = quartzParser().parse("0 0 12 ? * MON * || 0 30 12 ? * TUE *");
        ExecutionTime time = ExecutionTime.forCron(composite);
        Optional<ZonedDateTime> next = time.nextExecution(at(2026, 8, 17, 11, 0, 0));
        Optional<ZonedDateTime> previous = time.lastExecution(at(2026, 8, 18, 13, 0, 0));
        assertAll(
                () -> assertEquals(Optional.of(at(2026, 8, 17, 12, 0, 0)), next),
                () -> assertEquals(Optional.of(at(2026, 8, 18, 12, 30, 0)), previous));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-INV-006, CRON-TIME-002, CRON-TIME-005
     * Depends-On: periodFactoriesSerializeBaseAndPeriod, quartzParserNormalizesWhitespaceAndNames
     */
    @Test
    void matchingBoundaryAgreesWithNeighboringQuarterHourQueries() {
        ExecutionTime time = ExecutionTime.forCron(quartzParser().parse("0 */15 * ? * * *"));
        ZonedDateTime boundary = at(2026, 8, 17, 11, 30, 0);
        Optional<ZonedDateTime> next = time.nextExecution(boundary.minusSeconds(1));
        Optional<ZonedDateTime> previous = time.lastExecution(boundary.plusSeconds(1));
        assertAll(
                () -> assertTrue(time.isMatch(boundary)),
                () -> assertEquals(Optional.of(boundary), next),
                () -> assertEquals(Optional.of(boundary), previous));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-INV-007, CRON-TIME-006
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, periodFactoriesSerializeBaseAndPeriod
     */
    @Test
    void executionCountEqualsMaterializedExecutionDates() {
        ExecutionTime time = ExecutionTime.forCron(quartzParser().parse("0 0 * ? * * *"));
        ZonedDateTime start = at(2026, 8, 17, 10, 0, 0);
        ZonedDateTime end = at(2026, 8, 17, 14, 0, 0);
        assertAll(
                () -> assertEquals(4, time.getExecutionDates(start, end).size()),
                () -> assertEquals(time.getExecutionDates(start, end).size(), time.countExecutions(start, end)));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-INV-007, CRON-TIME-012
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, periodFactoriesSerializeBaseAndPeriod
     */
    @Test
    void frequencyComparatorUsesSameExecutionCounts() {
        Cron hourly = quartzParser().parse("0 0 * ? * * *");
        Cron daily = quartzParser().parse("0 0 12 ? * * *");
        ZonedDateTime start = at(2026, 8, 17, 10, 0, 0);
        ZonedDateTime end = at(2026, 8, 17, 14, 0, 0);
        int expected = ExecutionTime.forCron(hourly).countExecutions(start, end)
                - ExecutionTime.forCron(daily).countExecutions(start, end);
        assertEquals(expected, new CronFrequencyComparator(start, end).compare(hourly, daily));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-INV-002, CRON-INV-008, CRON-DESC-003, CRON-PAR-009
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void wholeDescriptionAgreesAfterDayOfWeekCanonicalReparse() {
        Cron cron = quartzParser().parse("0 23 * ? * MON-FRI *");
        Cron reparsed = quartzParser().parse(cron.asString());
        CronDescriptor descriptor = CronDescriptor.instance(Locale.UK);
        String description = descriptor.describe(cron);
        String reparsedDescription = descriptor.describe(reparsed);
        assertAll(
                () -> assertEquals("2-6",
                        cron.retrieve(CronFieldName.DAY_OF_WEEK).getExpression().asString()),
                () -> assertTrue(cron.equivalent(reparsed)),
                () -> assertEquals(description, reparsedDescription),
                () -> assertFalse(description.isBlank()));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-INV-009, CRON-EXT-001
     * Depends-On: quartzDefinitionExposesSpecifiedFields, quartzParserNormalizesWhitespaceAndNames
     */
    @Test
    void annotationMetadataAndTypeSelectionAgree() throws Exception {
        Class<?> annotationClass = Class.forName("com.cronutils.validation.Cron");
        java.lang.annotation.Target target = annotationClass.getAnnotation(java.lang.annotation.Target.class);
        java.lang.annotation.Retention retention = annotationClass.getAnnotation(java.lang.annotation.Retention.class);
        CronType selected = annotationTypeValue(CronType.QUARTZ);
        Cron cron = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(selected))
                .parse("0 0 12 ? * MON *");
        assertAll(
                () -> assertTrue(List.of(target.value()).contains(java.lang.annotation.ElementType.FIELD)),
                () -> assertTrue(List.of(target.value()).contains(java.lang.annotation.ElementType.ANNOTATION_TYPE)),
                () -> assertEquals(java.lang.annotation.RetentionPolicy.RUNTIME, retention.value()),
                () -> assertEquals("0 0 12 ? * 2 *", cron.asString()));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-INV-009, CRON-EXT-001, CRON-EXT-003
     * Depends-On: quartzDefinitionExposesSpecifiedFields, quartzParserNormalizesWhitespaceAndNames
     */
    @Test
    void annotationTypeMemberCanSelectQuartzDefinition() throws Exception {
        CronType selected = annotationTypeValue(CronType.QUARTZ);
        Cron cron = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(selected))
                .parse("0 0 12 ? * MON *");
        assertAll(
                () -> assertEquals(CronType.QUARTZ, selected),
                () -> assertEquals("0 0 12 ? * 2 *", cron.asString()),
                () -> assertSame(cron, cron.validate()));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-INV-009, CRON-EXT-001, CRON-EXT-003
     * Depends-On: unixParserCanonicalizesSymbolicWeekday, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void annotationTypeMemberCanSelectUnixDefinition() throws Exception {
        CronType selected = annotationTypeValue(CronType.UNIX);
        Cron cron = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(selected)).parse("0 6 * * MON");
        assertAll(
                () -> assertEquals(CronType.UNIX, selected),
                () -> assertEquals("0 6 * * 1", cron.asString()),
                () -> assertSame(cron, cron.validate()));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-INV-010, CRON-VAL-010, CRON-DESC-005, CRON-MAP-008
     * Depends-On: customDefinitionRetainsRegisteredFields, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void rebootCronSurvivesSupportedPublicProjections() {
        CronDefinition definition = rebootCapableDefinition();
        Cron reboot = CronBuilder.reboot(definition);
        Cron mapped = CronMapper.sameCron(definition).map(reboot);
        String description = CronDescriptor.instance(Locale.UK).describe(reboot);
        assertAll(
                () -> assertEquals("@reboot", reboot.asString()),
                () -> assertEquals("@reboot", mapped.asString()),
                () -> assertTrue(reboot.equivalent(mapped)),
                () -> assertFalse(description.isBlank()));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-INV-010, CRON-TIME-001, CRON-TIME-003, CRON-MAP-009, CRON-ERR-007
     * Depends-On: customDefinitionRetainsRegisteredFields, parserRejectsNullDefinitionAndExpression
     */
    @Test
    void rebootCronHasNoOccurrenceAndUnsupportedMappingFails() {
        Cron reboot = CronBuilder.reboot(CronDefinitionBuilder.instanceDefinitionFor(CronType.SPRING53));
        ExecutionTime time = ExecutionTime.forCron(reboot);
        assertAll(
                () -> assertTrue(time.nextExecution(at(2026, 8, 17, 10, 0, 0)).isEmpty()),
                () -> assertTrue(time.lastExecution(at(2026, 8, 17, 10, 0, 0)).isEmpty()),
                () -> assertThrows(IllegalArgumentException.class,
                        () -> CronMapper.sameCron(reboot.getCronDefinition()).map(reboot)));
    }

    /**
     * Seam: protocol handoff across cron construction, parsing, validation, and public projections.
     * Verifies: CRON-VAL-009, CRON-ERR-006
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, malformedQuartzSyntaxIsRejected
     */
    @Test
    void compositeStructuredOperationsAreRejected() {
        Cron composite = quartzParser().parse("0 0 12 ? * MON * || 0 30 12 ? * TUE *");
        Cron ordinary = quartzParser().parse("0 0 12 ? * MON *");
        assertAll(
                () -> assertThrows(UnsupportedOperationException.class,
                        () -> composite.retrieve(CronFieldName.MINUTE)),
                () -> assertThrows(UnsupportedOperationException.class, composite::retrieveFieldsAsMap),
                () -> assertThrows(UnsupportedOperationException.class,
                        () -> composite.equivalent(CronMapper.sameCron(ordinary.getCronDefinition()), ordinary)));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-VAL-006, CRON-VAL-007, CRON-ERR-002
     * Depends-On: quartzDefinitionExposesSpecifiedFields, unixParserCanonicalizesSymbolicWeekday
     */
    @Test
    void compositeRejectsEmptyAndMixedDefinitionLists() {
        Cron quartz = quartzParser().parse("0 0 12 ? * MON *");
        Cron unix = parser(CronType.UNIX).parse("0 12 * * MON");
        assertAll(
                () -> assertThrows(IllegalArgumentException.class, () -> new CompositeCron(List.of())),
                () -> assertThrows(IllegalArgumentException.class, () -> new CompositeCron(List.of(quartz, unix))));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-INV-004, CRON-MAP-005, CRON-MAP-006, CRON-TIME-005, CRON-DEF-026
     * Depends-On: basicExpressionFactoriesSerializeCanonically, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void quartzCron4jMappingAdaptsQuestionMarkAndWeekdayNumbering() {
        Cron quartz = builtWorkdayQuartz();
        Cron cron4j = CronMapper.fromQuartzToCron4j().map(quartz);
        ZonedDateTime monday = at(2026, 8, 17, 0, 23, 0);
        assertAll(
                () -> assertEquals("1-5",
                        cron4j.retrieve(CronFieldName.DAY_OF_WEEK).getExpression().asString()),
                () -> assertEquals("*",
                        cron4j.retrieve(CronFieldName.DAY_OF_MONTH).getExpression().asString()),
                () -> assertTrue(ExecutionTime.forCron(quartz).isMatch(monday)),
                () -> assertTrue(ExecutionTime.forCron(cron4j).isMatch(monday)));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-TIME-002, CRON-TIME-004, CRON-INV-006
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, periodFactoriesSerializeBaseAndPeriod
     */
    @Test
    void executionDurationsMatchNextAndPreviousResults() {
        ExecutionTime time = ExecutionTime.forCron(quartzParser().parse("0 0 * ? * * *"));
        ZonedDateTime reference = at(2026, 8, 17, 10, 15, 30);
        Optional<ZonedDateTime> next = time.nextExecution(reference);
        Optional<ZonedDateTime> previous = time.lastExecution(reference);
        Optional<Duration> toNext = time.timeToNextExecution(reference);
        Optional<Duration> fromLast = time.timeFromLastExecution(reference);
        assertAll(
                () -> assertEquals(Optional.of(Duration.between(reference, next.orElseThrow())), toNext),
                () -> assertEquals(Optional.of(Duration.between(previous.orElseThrow(), reference)), fromLast));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-TIME-006, CRON-INV-007
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, cronFieldNamesHaveCanonicalOrder
     */
    @Test
    void executionRangeIncludesMatchingEndButExcludesStart() {
        ExecutionTime time = ExecutionTime.forCron(quartzParser().parse("0 0 * ? * * *"));
        ZonedDateTime start = at(2026, 8, 17, 10, 0, 0);
        ZonedDateTime end = at(2026, 8, 17, 12, 0, 0);
        assertEquals(List.of(at(2026, 8, 17, 11, 0, 0), end), time.getExecutionDates(start, end));
    }

    /**
     * Seam: state consistency across cron evaluation and public time projections.
     * Verifies: CRON-TIME-007, CRON-ERR-008
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, malformedQuartzSyntaxIsRejected
     */
    @Test
    void executionRangeRejectsNonIncreasingEndpoints() {
        ExecutionTime time = ExecutionTime.forCron(quartzParser().parse("0 0 * ? * * *"));
        ZonedDateTime date = at(2026, 8, 17, 10, 0, 0);
        assertAll(
                () -> assertThrows(IllegalArgumentException.class, () -> time.getExecutionDates(date, date)),
                () -> assertThrows(IllegalArgumentException.class, () -> time.countExecutions(date, date.minusSeconds(1))));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-EXT-005, CRON-EXT-006
     * Depends-On: periodFactoriesSerializeBaseAndPeriod, quartzParserNormalizesWhitespaceAndNames
     */
    @Test
    void fieldGeneratorMatchesParsedMinuteExpression() {
        Cron cron = quartzParser().parse("0 */15 * ? * * *");
        FieldValueGenerator generator = FieldValueGeneratorFactory.forCronField(cron.retrieve(CronFieldName.MINUTE));
        assertAll(
                () -> assertTrue(generator.isMatch(30)),
                () -> assertFalse(generator.isMatch(31)));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-PAR-005, CRON-DEF-008, CRON-WF-002, CRON-DESC-003
     * Depends-On: basicExpressionFactoriesSerializeCanonically, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void supportedNicknameMatchesBuilderAndDescription() {
        CronDefinition definition = CronDefinitionBuilder.instanceDefinitionFor(CronType.SPRING53);
        Cron parsed = new CronParser(definition).parse("@daily");
        Cron built = CronBuilder.daily(definition);
        CronDescriptor descriptor = CronDescriptor.instance(Locale.UK);
        String parsedDescription = descriptor.describe(parsed);
        String builtDescription = descriptor.describe(built);
        assertAll(
                () -> assertEquals("0 0 0 * * *", parsed.asString()),
                () -> assertTrue(parsed.equivalent(built)),
                () -> assertEquals(parsedDescription, builtDescription),
                () -> assertFalse(parsedDescription.isBlank()));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-PAR-007, CRON-INV-005, CRON-VAL-008
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, basicExpressionFactoriesSerializeCanonically
     */
    @Test
    void alignedFieldAlternativesBuildAndValidateComposite() {
        Cron composite = quartzParser().parse("0 0|30 12 ? * 2|3 *");
        assertAll(
                () -> assertTrue(composite instanceof CompositeCron),
                () -> assertEquals(2, ((CompositeCron) composite).getCrons().size()),
                () -> assertEquals("0 0|30 12 ? * 2|3 *", composite.asString()),
                () -> assertSame(composite, composite.validate()));
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-MAP-013, CRON-MAP-016, CRON-WF-002
     */
    @Test
    void converterFluentWorkflowPreservesTextAcrossSameZone() {
        CronConverter converter = new CronConverter(new CronToCalendarTransformer(), new CalendarToCronTransformer());
        assertEquals("0 15 10 ? * *", converter.using("0 15 10 ? * *").from(UTC).to(UTC).convert());
    }

    /**
     * Seam: config interaction across cron definitions, parsing, and public projections.
     * Verifies: CRON-STATE-001, CRON-WF-001, CRON-INV-003
     * Depends-On: quartzParserNormalizesWhitespaceAndNames, quartzDefinitionExposesSpecifiedFields
     */
    @Test
    void parserAndDefinitionSupportConcurrentReadUse() throws Exception {
        CronDefinition definition = CronDefinitionBuilder.instanceDefinitionFor(CronType.QUARTZ);
        CronParser parser = new CronParser(definition);
        ExecutorService executor = Executors.newFixedThreadPool(4);
        try {
            List<Callable<String>> calls = java.util.stream.IntStream.range(0, 20)
                    .mapToObj(index -> (Callable<String>) () -> parser.parse("0 23 * ? * MON-FRI *").validate().asString())
                    .toList();
            List<Future<String>> futures = executor.invokeAll(calls);
            for (Future<String> future : futures) {
                assertEquals("0 23 * ? * 2-6 *", future.get());
            }
            assertEquals(7, definition.getFieldDefinitions().size());
        } finally {
            executor.shutdownNow();
        }
    }

    private static CronDefinition quartzDefinition() {
        return CronDefinitionBuilder.instanceDefinitionFor(CronType.QUARTZ);
    }

    private static CronParser quartzParser() {
        return new CronParser(quartzDefinition());
    }

    private static CronParser parser(CronType type) {
        return new CronParser(CronDefinitionBuilder.instanceDefinitionFor(type));
    }

    private static Cron builtWorkdayQuartz() {
        return CronBuilder.cron(quartzDefinition())
                .withSecond(on(0))
                .withMinute(on(23))
                .withHour(always())
                .withDoM(questionMark())
                .withMonth(always())
                .withDoW(between(2, 6))
                .withYear(always())
                .instance();
    }

    private static CronDefinition customDefinition() {
        return CronDefinitionBuilder.defineCron()
                .withMinutes().withValidRange(0, 59).withStrictRange().and()
                .withHours().withValidRange(0, 23).withStrictRange().and()
                .withDayOfMonth().withValidRange(1, 31).and()
                .withMonth().withValidRange(1, 12).and()
                .withDayOfWeek().withValidRange(0, 6).withMondayDoWValue(1).and()
                .instance();
    }

    private static CronDefinition rebootCapableDefinition() {
        return CronDefinitionBuilder.defineCron()
                .withMinutes().withValidRange(0, 59).and()
                .withHours().withValidRange(0, 23).and()
                .withDayOfMonth().withValidRange(1, 31).and()
                .withMonth().withValidRange(1, 12).and()
                .withDayOfWeek().withValidRange(0, 6).withMondayDoWValue(1).and()
                .withSupportedNicknameReboot()
                .instance();
    }

    private static ZonedDateTime at(int year, int month, int day, int hour, int minute, int second) {
        return ZonedDateTime.of(year, month, day, hour, minute, second, 0, UTC);
    }

    private static CronType annotationTypeValue(CronType value) throws Exception {
        Class<?> annotationClass = Class.forName("com.cronutils.validation.Cron");
        Method typeMethod = annotationClass.getDeclaredMethod("type");
        assertEquals(CronType.class, typeMethod.getReturnType());
        Object proxy = Proxy.newProxyInstance(
                annotationClass.getClassLoader(),
                new Class<?>[] {annotationClass},
                (instance, method, arguments) -> {
                    if (method.getName().equals("type")) {
                        return value;
                    }
                    if (method.getName().equals("annotationType")) {
                        return annotationClass;
                    }
                    return method.getDefaultValue();
                });
        return (CronType) typeMethod.invoke(proxy);
    }
}

