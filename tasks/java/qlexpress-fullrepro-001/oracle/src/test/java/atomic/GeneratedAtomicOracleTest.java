package atomic;

import com.alibaba.qlexpress4.CheckOptions;
import com.alibaba.qlexpress4.DefaultClassSupplier;
import com.alibaba.qlexpress4.Express4Runner;
import com.alibaba.qlexpress4.InitOptions;
import com.alibaba.qlexpress4.QLOptions;
import com.alibaba.qlexpress4.aparser.ImportManager;
import com.alibaba.qlexpress4.aparser.InterpolationMode;
import com.alibaba.qlexpress4.api.parsecache.SerializableParseCache;
import com.alibaba.qlexpress4.api.parsecache.SerializableParseCacheException;
import com.alibaba.qlexpress4.exception.QLRuntimeException;
import com.alibaba.qlexpress4.exception.QLSyntaxException;
import com.alibaba.qlexpress4.exception.QLTimeoutException;
import com.alibaba.qlexpress4.operator.OperatorCheckStrategy;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import support.OracleModels;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GeneratedAtomicOracleTest {
    private Express4Runner runner() {
        return new Express4Runner(InitOptions.DEFAULT_OPTIONS);
    }

    private Object eval(String script) {
        return runner().execute(script, Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult();
    }

    /** Verifies: QLX-EXEC-002, QLX-EXEC-011 */
    @Test void arithmeticHonorsMultiplicationPrecedence() {
        assertEquals(31, ((Number)eval("7+8*3")).intValue());
    }

    /** Verifies: QLX-EXEC-002, QLX-EXEC-016 */
    @Test void groupingOverridesArithmeticPrecedence() {
        assertEquals(45, ((Number)eval("(7+8)*3")).intValue());
    }

    /** Verifies: QLX-EXEC-011, QLX-OPT-009 */
    @Test void preciseModeUsesDecimalSemantics() {
        Object value = runner().execute("0.1+0.2", Collections.emptyMap(), QLOptions.builder().precise(true).build()).getResult();
        assertEquals("0.3", value.toString());
    }

    /** Verifies: QLX-EXEC-012 */
    @Test void stringConcatenationWorksWithMixedOperands() {
        assertEquals("score=27", eval("'score='+27"));
    }

    /** Verifies: QLX-EXEC-012, QLX-OPT-015 */
    @Test void scriptInterpolationEvaluatesSelectorExpression() {
        Map<String, Object> context = new HashMap<>();
        context.put("n", 6);
        Object value = runner().execute("\"n=${n+4}\"", context, QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals("n=10", value);
    }

    /** Verifies: QLX-OPT-015 */
    @Test void disabledInterpolationPreservesSelectorText() {
        Express4Runner custom = new Express4Runner(InitOptions.builder().interpolationMode(InterpolationMode.DISABLE).build());
        assertEquals("n=${n+4}", custom.execute("\"n=${n+4}\"", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /** Verifies: QLX-EXEC-013 */
    @Test void listLiteralPreservesOrder() {
        assertEquals(Arrays.asList(9, 4, 7), eval("[9,4,7]"));
    }

    /** Verifies: QLX-EXEC-013 */
    @Test void indexingReadsListElement() {
        assertEquals(12, ((Number)eval("[5,12,18][1]")).intValue());
    }

    /** Verifies: QLX-EXEC-013 */
    @Test void slicingReturnsContiguousSubsequence() {
        assertEquals(Arrays.asList(12, 18), eval("[5,12,18,25][1:3]"));
    }

    /** Verifies: QLX-EXEC-016 */
    @Test void conditionalReturnsSelectedBranch() {
        assertEquals("large", eval("if (17>9) {'large'} else {'small'}"));
    }

    /** Verifies: QLX-EXEC-016 */
    @Test void whileLoopAccumulatesState() {
        assertEquals(15, ((Number)eval("i=1; total=0; while(i<=5){total+=i;i++};total")).intValue());
    }

    /** Verifies: QLX-EXEC-016 */
    @Test void classicForLoopAccumulatesState() {
        assertEquals(20, ((Number)eval("total=0;for(i=0;i<5;i++){total+=i*2};total")).intValue());
    }

    /** Verifies: QLX-EXEC-013, QLX-EXEC-016 */
    @Test void forEachLoopConsumesListInOrder() {
        assertEquals(10, ((Number)eval("total=0;for(v:[1,2,3,4]){total+=v};total")).intValue());
    }

    /** Verifies: QLX-EXEC-016 */
    @Test void breakStopsLoopAtMatchingValue() {
        assertEquals(4, ((Number)eval("i=0;while(true){i++;if(i==4){break}};i")).intValue());
    }

    /** Verifies: QLX-EXEC-016 */
    @Test void continueSkipsMatchingIteration() {
        assertEquals(8, ((Number)eval("total=0;for(i=1;i<=4;i++){if(i==2){continue};total+=i};total")).intValue());
    }

    /** Verifies: QLX-EXEC-016 */
    @Test void scriptFunctionReturnsComputedValue() {
        assertEquals(42, ((Number)eval("function scale(x){return x*6};scale(7)")).intValue());
    }

    /** Verifies: QLX-EXEC-014 */
    @Test void logicalOrShortCircuitsByDefault() {
        assertEquals(Boolean.TRUE, eval("true || (1/0>0)"));
    }

    /** Verifies: QLX-EXEC-014 */
    @Test void logicalAndShortCircuitsByDefault() {
        assertEquals(Boolean.FALSE, eval("false && (1/0>0)"));
    }

    /** Verifies: QLX-EXEC-014 */
    @Test void falseLogicalAndSkipsRightOperandSideEffect() {
        assertEquals(0, ((Number)eval("marker=0;false && ((marker=1)>0);marker")).intValue());
    }

    /** Verifies: QLX-EXEC-007 */
    @Test void defaultExecutionDoesNotPolluteMap() {
        Map<String, Object> context = new HashMap<>();
        context.put("seed", 3);
        assertEquals(8, ((Number)runner().execute("seed=8;seed", context, QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
        assertEquals(3, ((Number)context.get("seed")).intValue());
    }

    /** Verifies: QLX-EXEC-008, QLX-OPT-009 */
    @Test void pollutionOptionWritesGlobalAssignment() {
        Map<String, Object> context = new HashMap<>();
        runner().execute("answer=39+3", context, QLOptions.builder().polluteUserContext(true).build());
        assertEquals(42, ((Number)context.get("answer")).intValue());
    }

    /** Verifies: QLX-OPT-017 */
    @Test void templateExecutionSubstitutesExpressions() {
        Map<String, Object> context = new HashMap<>();
        context.put("x", 8);
        context.put("y", 5);
        assertEquals("sum 13", runner().executeTemplate("sum ${x+y}", context, QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /** Verifies: QLX-OPT-007, QLX-OPT-008 */
    @Test void defaultExecutionOptionsExposeDisabledPolicy() {
        QLOptions options = QLOptions.DEFAULT_OPTIONS;
        assertFalse(options.isPrecise());
        assertFalse(options.isPolluteUserContext());
        assertFalse(options.isCache());
        assertFalse(options.isAvoidNullPointer());
        assertFalse(options.isTraceExpression());
        assertFalse(options.isShortCircuitDisable());
        assertEquals(Collections.emptyMap(), options.getAttachments());
        Object array = runner().execute("new int[5]", Collections.emptyMap(), options).getResult();
        assertEquals(5, java.lang.reflect.Array.getLength(array));
    }

    /** Verifies: QLX-OPT-009 */
    @Test void executionOptionsBuilderRetainsAllChoices() {
        Map<String, Object> attachments = Collections.singletonMap("tenant", "blue");
        QLOptions options = QLOptions.builder().precise(true).polluteUserContext(true).timeoutMillis(250)
                .attachments(attachments).cache(true).avoidNullPointer(true).maxArrLength(19)
                .traceExpression(true).shortCircuitDisable(true).build();
        assertTrue(options.isPrecise());
        assertTrue(options.isPolluteUserContext());
        assertEquals(250L, options.getTimeoutMillis());
        assertEquals(Collections.singletonMap("tenant", "blue"), options.getAttachments());
        assertTrue(options.isCache());
        assertTrue(options.isAvoidNullPointer());
        assertEquals(19, options.getMaxArrLength());
        assertTrue(options.isTraceExpression());
        assertTrue(options.isShortCircuitDisable());
    }

    /** Verifies: QLX-OPT-001 */
    @Test void defaultInitializationOptionsExposeContractValues() {
        InitOptions options = InitOptions.DEFAULT_OPTIONS;
        assertTrue(options.getDefaultImport().size() >= 5);
        assertFalse(options.isDebug());
        assertFalse(options.isAllowPrivateAccess());
        assertEquals(InterpolationMode.SCRIPT, options.getInterpolationMode());
        assertFalse(options.isTraceExpression());
        assertTrue(options.isStrictNewLines());
    }

    /** Verifies: QLX-OPT-002, QLX-OPT-003, QLX-OPT-005 */
    @Test void initializationBuilderRetainsDelimiterAndMode() {
        InitOptions options = InitOptions.builder().debug(true).allowPrivateAccess(true)
                .interpolationMode(InterpolationMode.VARIABLE).traceExpression(true)
                .selectorStart("#[").selectorEnd("]").strictNewLines(false).build();
        assertTrue(options.isDebug());
        assertTrue(options.isAllowPrivateAccess());
        assertEquals(InterpolationMode.VARIABLE, options.getInterpolationMode());
        assertTrue(options.isTraceExpression());
        assertEquals("#[", options.getSelectorStart());
        assertEquals("]", options.getSelectorEnd());
        assertFalse(options.isStrictNewLines());
    }

    /** Verifies: QLX-OPT-004, QLX-ERR-005 */
    @Test void invalidSelectorStartIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> InitOptions.builder().selectorStart("<{").build());
    }

    /** Verifies: QLX-OPT-006, QLX-ERR-005 */
    @Test void emptySelectorEndIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> InitOptions.builder().selectorEnd("").build());
    }

    /** Verifies: QLX-VAL-004, QLX-ERR-001, QLX-ERR-009 */
    @Test void malformedScriptRaisesStructuredSyntaxException() {
        QLSyntaxException error = assertThrows(QLSyntaxException.class, () -> runner().check("a+(b"));
        assertNotNull(error.getDiagnostic());
        assertNotNull(error.getReason());
        assertNotNull(error.getErrLexeme());
        assertNotNull(error.getErrorCode());
        assertTrue(error.getLineNo() >= 1);
        assertTrue(error.getColNo() >= 1);
    }

    /** Verifies: QLX-EXEC-019, QLX-ERR-002 */
    @Test void nonBooleanConditionRaisesRuntimeException() {
        assertThrows(QLRuntimeException.class,
                () -> runner().execute("if(3){1}", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS));
    }

    /** Verifies: QLX-OPT-013, QLX-ERR-003 */
    @Test void positiveTimeoutRaisesTimeoutException() {
        assertThrows(QLTimeoutException.class, () -> runner().execute(
                "i=0;while(true){i++}", Collections.emptyMap(), QLOptions.builder().timeoutMillis(1L).build()));
    }

    /** Verifies: QLX-CACHE-007, QLX-ERR-004 */
    @Test void malformedSerializableCacheIsRejected() {
        assertThrows(SerializableParseCacheException.class,
                () -> runner().loadSerializableCache(new SerializableParseCache()));
    }

    /** Verifies: QLX-EXT-007, QLX-ERR-006 */
    @Test void missingServiceMethodRegistrationTargetIsRejected() {
        OracleModels.CalculatorService service = new OracleModels.CalculatorService();
        assertThrows(IllegalArgumentException.class, () -> OracleModels.registerServiceMethod(
                runner(), "missingTarget", service, "notPresent", int.class));
    }

    /** Verifies: QLX-ERR-009, QLX-ERR-010 */
    @Test void convenienceCoordinatesAreOneBasedDiagnosticPositions() {
        QLSyntaxException error = assertThrows(QLSyntaxException.class,
                () -> runner().check("value + (3"));
        assertEquals(error.getDiagnostic().getRange().getStart().getLine() + 1, error.getLineNo());
        assertEquals(error.getDiagnostic().getRange().getStart().getCharacter() + 1, error.getColNo());
    }

    /** Verifies: QLX-VAL-005 */
    @Test void dependencyInspectionExcludesLocals() {
        assertEquals(new HashSet<>(Arrays.asList("outside", "tail")),
                runner().getOutVarNames("int local=4; result=local+outside; result+tail"));
    }

    /** Verifies: QLX-VAL-007 */
    @Test void functionInspectionExcludesScriptDefinitions() {
        assertEquals(Collections.singleton("external"),
                runner().getOutFunctions("function inner(x){x+1};inner(2)+external(3)"));
    }

    /** Verifies: QLX-VAL-003 */
    @Test void allowAllStrategyAcceptsArithmeticOperator() {
        assertTrue(OperatorCheckStrategy.allowAll().isAllowed("+"));
    }

    /** Verifies: QLX-VAL-003 */
    @Test void whitelistStrategyRejectsUnlistedOperator() {
        OperatorCheckStrategy strategy = OperatorCheckStrategy.whitelist(Collections.singleton("+"));
        assertTrue(strategy.isAllowed("+"));
        assertFalse(strategy.isAllowed("*"));
        assertEquals(Collections.singleton("+"), strategy.getOperators());
    }

    /** Verifies: QLX-VAL-003 */
    @Test void blacklistStrategyRejectsListedOperator() {
        OperatorCheckStrategy strategy = OperatorCheckStrategy.blacklist(Collections.singleton("="));
        assertFalse(strategy.isAllowed("="));
        assertTrue(strategy.isAllowed("+"));
    }

    /** Verifies: QLX-SEC-005 */
    @Test void defaultClassSupplierLoadsKnownClassAndReturnsNullForMissingClass() {
        DefaultClassSupplier supplier = DefaultClassSupplier.getInstance();
        assertEquals(String.class, supplier.loadCls("java.lang.String"));
        assertNull(supplier.loadCls("example.missing.Type"));
    }

    /** Verifies: QLX-VAL-002 */
    @Test void defaultCheckOptionsAllowFunctionsAndOperators() {
        CheckOptions options = CheckOptions.DEFAULT_OPTIONS;
        assertFalse(options.isDisableFunctionCalls());
        assertTrue(options.getCheckStrategy().isAllowed("+"));
    }

    /** Verifies: QLX-VAL-002, QLX-VAL-003 */
    @Test void checkOptionsBuilderRetainsRestrictions() {
        OperatorCheckStrategy strategy = OperatorCheckStrategy.whitelist(new HashSet<>(Arrays.asList("+", "*")));
        CheckOptions options = CheckOptions.builder().operatorCheckStrategy(strategy).disableFunctionCalls(true).build();
        assertTrue(options.getCheckStrategy().isAllowed("+"));
        assertTrue(options.getCheckStrategy().isAllowed("*"));
        assertFalse(options.getCheckStrategy().isAllowed("-"));
        assertTrue(options.isDisableFunctionCalls());
    }

    /** Verifies: QLX-SEC-004, QLX-ERR-005 */
    @Test void lowercaseClassAliasIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> ImportManager.importClsAlias(Integer.class, "wholeNumber"));
    }

    /** Verifies: QLX-OPT-011 */
    @Test void nullAvoidanceProjectsMissingMemberAsNull() {
        Map<String, Object> context = new HashMap<>();
        context.put("record", null);
        Object value = runner().execute("record.missing", context, QLOptions.builder().avoidNullPointer(true).build()).getResult();
        assertNull(value);
    }

    /** Verifies: QLX-OPT-012, QLX-ERR-002 */
    @Test void arrayLengthLimitRejectsOversizedAllocation() {
        QLRuntimeException error = assertThrows(QLRuntimeException.class,
                () -> runner().execute("new int[5]", Collections.emptyMap(), QLOptions.builder().maxArrLength(4).build()));
        assertEquals("EXCEED_MAX_ARR_LENGTH", String.valueOf(error.getErrorCode()));
    }
}
