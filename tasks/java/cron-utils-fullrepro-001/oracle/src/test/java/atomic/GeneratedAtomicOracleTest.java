package atomic;

import com.cronutils.model.Cron;
import com.cronutils.model.CronType;
import com.cronutils.model.definition.CronDefinition;
import com.cronutils.model.definition.CronDefinitionBuilder;
import com.cronutils.model.field.CronFieldName;
import com.cronutils.model.field.definition.FieldDefinition;
import com.cronutils.parser.CronParser;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

import static com.cronutils.model.field.expression.FieldExpressionFactory.always;
import static com.cronutils.model.field.expression.FieldExpressionFactory.and;
import static com.cronutils.model.field.expression.FieldExpressionFactory.between;
import static com.cronutils.model.field.expression.FieldExpressionFactory.every;
import static com.cronutils.model.field.expression.FieldExpressionFactory.on;
import static com.cronutils.model.field.expression.FieldExpressionFactory.questionMark;
import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GeneratedAtomicOracleTest {

    /**
     * Verifies: CRON-DEF-010, CRON-DEF-014, CRON-PAR-013
     */
    @Test
    void cronFieldNamesHaveCanonicalOrder() {
        assertEquals(List.of(
                        CronFieldName.SECOND,
                        CronFieldName.MINUTE,
                        CronFieldName.HOUR,
                        CronFieldName.DAY_OF_MONTH,
                        CronFieldName.MONTH,
                        CronFieldName.DAY_OF_WEEK,
                        CronFieldName.YEAR,
                        CronFieldName.DAY_OF_YEAR),
                java.util.Arrays.stream(CronFieldName.values())
                        .sorted(java.util.Comparator.comparingInt(CronFieldName::getOrder)).toList());
    }

    /**
     * Verifies: CRON-DEF-016, CRON-DEF-017, CRON-DEF-026
     */
    @Test
    void basicExpressionFactoriesSerializeCanonically() {
        assertAll(
                () -> assertEquals("*", always().asString()),
                () -> assertEquals("?", questionMark().asString()),
                () -> assertEquals("7", on(7).asString()),
                () -> assertEquals("2-6", between(2, 6).asString()));
    }

    /**
     * Verifies: CRON-DEF-016, CRON-DEF-017, CRON-DEF-026, CRON-DEF-027
     */
    @Test
    void conjunctionFactoryPreservesChildOrder() {
        assertEquals("1,3,5", and(List.of(on(1), on(3), on(5))).asString());
    }

    /**
     * Verifies: CRON-DEF-016, CRON-DEF-017, CRON-DEF-026
     */
    @Test
    void periodFactoriesSerializeBaseAndPeriod() {
        assertAll(
                () -> assertEquals("*/15", every(15).asString()),
                () -> assertEquals("5/10", every(on(5), 10).asString()));
    }

    /**
     * Verifies: CRON-DEF-018
     */
    @Test
    void allValuesWithPeriodOneCollapsesToWildcard() {
        assertEquals("*", every(always(), 1).asString());
    }

    /**
     * Verifies: CRON-DEF-005, CRON-DEF-006, CRON-PAR-014
     */
    @Test
    void quartzDefinitionExposesSpecifiedFields() {
        CronDefinition definition = CronDefinitionBuilder.instanceDefinitionFor(CronType.QUARTZ);
        assertAll(
                () -> assertEquals(7, definition.getFieldDefinitions().size()),
                () -> assertTrue(definition.containsFieldDefinition(CronFieldName.SECOND)),
                () -> assertTrue(definition.containsFieldDefinition(CronFieldName.YEAR)),
                () -> assertFalse(definition.containsFieldDefinition(CronFieldName.DAY_OF_YEAR)));
    }

    /**
     * Verifies: CRON-DEF-004, CRON-PAR-003, CRON-PAR-012
     */
    @Test
    void unixParserCanonicalizesSymbolicWeekday() {
        CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.UNIX));
        assertEquals("15 9 * * 1", parser.parse("15 9 * * mon").asString());
    }

    /**
     * Verifies: CRON-PAR-002, CRON-PAR-012
     */
    @Test
    void quartzParserAcceptsOptionalYearOmission() {
        CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.QUARTZ));
        assertEquals("0 0 12 ? * 2", parser.parse("0 0 12 ? * MON").asString());
    }

    /**
     * Verifies: CRON-PAR-001, CRON-PAR-003, CRON-WF-001
     */
    @Test
    void quartzParserNormalizesWhitespaceAndNames() {
        CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.QUARTZ));
        assertEquals("0 23 * ? * 2-6 *", parser.parse("  0   23  * ? * mon-fri *  ").asString());
    }

    /**
     * Verifies: CRON-DEF-010, CRON-DEF-014, CRON-WF-003
     */
    @Test
    void customDefinitionRetainsRegisteredFields() {
        CronDefinition definition = customDefinition();
        assertEquals(Set.of(
                        CronFieldName.MINUTE,
                        CronFieldName.HOUR,
                        CronFieldName.DAY_OF_MONTH,
                        CronFieldName.MONTH,
                        CronFieldName.DAY_OF_WEEK),
                definition.getFieldDefinitions().stream()
                        .map(FieldDefinition::getFieldName).collect(java.util.stream.Collectors.toSet()));
    }

    /**
     * Verifies: CRON-PAR-008, CRON-ERR-003
     */
    @Test
    void malformedQuartzSyntaxIsRejected() {
        CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.QUARTZ));
        assertAll(
                () -> assertThrows(IllegalArgumentException.class, () -> parser.parse("")),
                () -> assertThrows(IllegalArgumentException.class, () -> parser.parse("0 0 12 ? * MON,")),
                () -> assertThrows(IllegalArgumentException.class, () -> parser.parse("0 0 12 ? * 2- *")));
    }

    /**
     * Verifies: CRON-PAR-001, CRON-PAR-008, CRON-ERR-001
     */
    @Test
    void parserRejectsNullDefinitionAndExpression() {
        assertAll(
                () -> assertThrows(NullPointerException.class, () -> new CronParser(null)),
                () -> {
                    CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.QUARTZ));
                    assertThrows(NullPointerException.class, () -> parser.parse(null));
                });
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
}

