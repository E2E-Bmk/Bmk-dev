package integration;

import com.alibaba.qlexpress4.CheckOptions;
import com.alibaba.qlexpress4.Express4Runner;
import com.alibaba.qlexpress4.InitOptions;
import com.alibaba.qlexpress4.QLOptions;
import com.alibaba.qlexpress4.QLPrecedences;
import com.alibaba.qlexpress4.QLResult;
import com.alibaba.qlexpress4.api.BatchAddFunctionResult;
import com.alibaba.qlexpress4.api.parsecache.LoadedParseCache;
import com.alibaba.qlexpress4.api.parsecache.SerializableParseCache;
import com.alibaba.qlexpress4.exception.QLException;
import com.alibaba.qlexpress4.exception.QLRuntimeException;
import com.alibaba.qlexpress4.exception.QLSyntaxException;
import com.alibaba.qlexpress4.operator.OperatorCheckStrategy;
import com.alibaba.qlexpress4.runtime.context.MapExpressContext;
import com.alibaba.qlexpress4.runtime.function.CustomFunction;
import com.alibaba.qlexpress4.runtime.QContext;
import com.alibaba.qlexpress4.runtime.trace.ExpressionTrace;
import com.alibaba.qlexpress4.runtime.trace.TracePointTree;
import com.alibaba.qlexpress4.security.QLSecurityStrategy;
import java.lang.reflect.Member;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import support.OracleModels;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GeneratedIntegrationOracleTest {
    private Express4Runner runner() {
        return new Express4Runner(InitOptions.DEFAULT_OPTIONS);
    }

    /**
     * Seam: protocol handoff from script compilation to portable cache execution. CVI-1.
     * Verifies: QLX-CACHE-004, QLX-EXEC-021, QLX-INV-001
     * Depends-On: arithmeticHonorsMultiplicationPrecedence, listLiteralPreservesOrder
     */
    @Test void serializableCacheMatchesDirectExecution() {
        Express4Runner runner = runner();
        String script = "base*4+3";
        Map<String, Object> context = Collections.singletonMap("base", 9);
        SerializableParseCache cache = runner.parseToSerializableCache(script);
        assertEquals(runner.execute(script, context, QLOptions.DEFAULT_OPTIONS).getResult(),
                runner.execute(cache, context, QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /**
     * Seam: protocol handoff from portable cache to runner-bound loaded cache. CVI-1.
     * Verifies: QLX-CACHE-004, QLX-CACHE-005, QLX-EXEC-022, QLX-INV-001
     * Depends-On: arithmeticHonorsMultiplicationPrecedence
     */
    @Test void loadedCacheMatchesDirectExecution() {
        Express4Runner runner = runner();
        String script = "left-right*2";
        Map<String, Object> map = new HashMap<>();
        map.put("left", 30);
        map.put("right", 6);
        LoadedParseCache loaded = runner.loadSerializableCache(runner.parseToSerializableCache(script));
        assertEquals(runner.execute(script, map, QLOptions.DEFAULT_OPTIONS).getResult(),
                runner.execute(loaded, new MapExpressContext(map), QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /**
     * Seam: state consistency across one loaded cache and distinct execution contexts.
     * Verifies: QLX-CACHE-005, QLX-EXEC-022
     * Depends-On: indexingReadsListElement
     */
    @Test void loadedCacheIsReusableAcrossContexts() {
        Express4Runner runner = runner();
        LoadedParseCache loaded = runner.loadSerializableCache(runner.parseToSerializableCache("value*value"));
        Object first = runner.execute(loaded, new MapExpressContext(Collections.singletonMap("value", 5)), QLOptions.DEFAULT_OPTIONS).getResult();
        Object second = runner.execute(loaded, new MapExpressContext(Collections.singletonMap("value", 8)), QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals(25, ((Number)first).intValue());
        assertEquals(64, ((Number)second).intValue());
    }

    /**
     * Seam: state consistency between serializable and loaded cache metadata.
     * Verifies: QLX-CACHE-004, QLX-CACHE-005
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void loadedCacheRetainsPortableMetadata() {
        Express4Runner runner = runner();
        SerializableParseCache source = runner.parseToSerializableCache("function twice(x){x*2};twice(input)");
        LoadedParseCache loaded = runner.loadSerializableCache(source);
        assertEquals(source.getScript(), loaded.getScript());
        assertEquals(source.getScriptHash(), loaded.getScriptHash());
    }

    /**
     * Seam: lifecycle crossing through cached executions and explicit cache clearing. CVI-8.
     * Verifies: QLX-CACHE-001, QLX-CACHE-002, QLX-CACHE-003, QLX-INV-008
     * Depends-On: arithmeticHonorsMultiplicationPrecedence
     */
    @Test void clearingCompileCachePreservesResult() {
        Express4Runner runner = runner();
        QLOptions cached = QLOptions.builder().cache(true).build();
        Object before = runner.execute("n*3+1", Collections.singletonMap("n", 7), cached).getResult();
        runner.parseToDefinitionWithCache("n*3+1");
        runner.clearCompileCache();
        Object after = runner.execute("n*3+1", Collections.singletonMap("n", 7), cached).getResult();
        assertEquals(before, after);
        assertEquals(22, ((Number)after).intValue());
    }

    /**
     * Seam: state consistency for dependency inspection and result across explicit cache clearing. CVI-8.
     * Verifies: QLX-CACHE-001, QLX-CACHE-003, QLX-VAL-005, QLX-INV-008
     * Depends-On: dependencyInspectionExcludesLocals, arithmeticHonorsMultiplicationPrecedence
     */
    @Test void clearingCompileCachePreservesDependenciesAndResult() {
        Express4Runner runner = runner();
        String script = "left+right";
        Set<String> beforeDependencies = runner.getOutVarNames(script);
        Object before = runner.execute(script, Map.of("left", 19, "right", 23),
                QLOptions.builder().cache(true).build()).getResult();
        runner.clearCompileCache();
        Set<String> afterDependencies = runner.getOutVarNames(script);
        Object after = runner.execute(script, Map.of("left", 19, "right", 23),
                QLOptions.builder().cache(true).build()).getResult();
        assertEquals(beforeDependencies, afterDependencies);
        assertEquals(before, after);
    }

    /**
     * Seam: state consistency between execution result and polluted caller map. CVI-3.
     * Verifies: QLX-EXEC-008, QLX-INV-003
     * Depends-On: pollutionOptionWritesGlobalAssignment
     */
    @Test void pollutedMapAgreesWithFinalResult() {
        Map<String, Object> context = new HashMap<>();
        context.put("start", 11);
        Object result = runner().execute("finalValue=start*4;finalValue", context,
                QLOptions.builder().polluteUserContext(true).build()).getResult();
        assertEquals(result, context.get("finalValue"));
        assertEquals(44, ((Number)result).intValue());
    }

    /**
     * Seam: state consistency between compound assignment result and polluted caller map. CVI-3.
     * Verifies: QLX-EXEC-008, QLX-INV-003
     * Depends-On: pollutionOptionWritesGlobalAssignment
     */
    @Test void pollutedMapAgreesWithCompoundAssignmentResult() {
        Map<String, Object> context = new HashMap<>();
        context.put("balance", 35);
        Object result = runner().execute("balance+=7;balance", context,
                QLOptions.builder().polluteUserContext(true).build()).getResult();
        assertEquals(42, ((Number)result).intValue());
        assertEquals(result, context.get("balance"));
    }

    /**
     * Seam: state consistency between local execution state and unchanged caller map. CVI-4.
     * Verifies: QLX-EXEC-007, QLX-INV-004
     * Depends-On: defaultExecutionDoesNotPolluteMap
     */
    @Test void nonPollutedMapRemainsUnchangedWhileResultUsesLocalValue() {
        Map<String, Object> context = new HashMap<>();
        context.put("value", 2);
        Object result = runner().execute("value=37;value+5", context, QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals(42, ((Number)result).intValue());
        assertEquals(2, ((Number)context.get("value")).intValue());
    }

    /**
     * Seam: state consistency for a new execution-local assignment without caller-map pollution. CVI-4.
     * Verifies: QLX-EXEC-007, QLX-INV-004
     * Depends-On: defaultExecutionDoesNotPolluteMap
     */
    @Test void nonPollutedMapOmitsNewLocalAssignment() {
        Map<String, Object> context = new HashMap<>();
        Object result = runner().execute("created=42;created", context, QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals(42, ((Number)result).intValue());
        assertFalse(context.containsKey("created"));
    }

    /**
     * Seam: protocol handoff from the declared CustomFunction callback to script dispatch.
     * Verifies: QLX-EXT-001
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void registeredJavaFunctionDispatchesDuringExecution() {
        Express4Runner runner = runner();
        assertTrue(runner.addFunction("bumpSeven", (context, parameters) ->
                ((Number)parameters.getValue(0)).intValue() + 7));
        assertEquals(19, ((Number)runner.execute("bumpSeven(12)", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: protocol handoff from varargs registration to ordered script parameters.
     * Verifies: QLX-EXT-001
     * Depends-On: listLiteralPreservesOrder
     */
    @Test void varargsFunctionReceivesAllArgumentsInOrder() {
        Express4Runner runner = runner();
        runner.addVarArgsFunction("joinParts", values -> values[0] + ":" + values[1] + ":" + values[2]);
        assertEquals("red:5:blue", runner.execute("joinParts('red',5,'blue')", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /**
     * Seam: protocol handoff from service reflection registration to script invocation.
     * Verifies: QLX-EXT-001
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void serviceMethodRegistrationDispatchesToTargetObject() {
        Express4Runner runner = runner();
        OracleModels.CalculatorService service = new OracleModels.CalculatorService();
        assertTrue(assertDoesNotThrow(() -> OracleModels.registerServiceMethod(
                runner, "tripleValue", service, "triple", int.class)));
        assertEquals(36, ((Number)runner.execute("tripleValue(12)", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: protocol handoff from annotation discovery to multiple script aliases.
     * Verifies: QLX-EXT-006
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void annotatedStaticFunctionRegistersEveryDeclaredName() {
        Express4Runner runner = runner();
        BatchAddFunctionResult result = runner.addStaticFunction(OracleModels.AnnotatedFunctions.class);
        assertFalse(result.getSucc().isEmpty());
        assertEquals(44, ((Number)runner.execute("quad(5)+timesFour(6)", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: protocol handoff from configured CustomBinaryOperator registration to expression parsing.
     * Verifies: QLX-EXT-008
     * Depends-On: stringConcatenationWorksWithMixedOperands
     */
    @Test void customBinaryOperatorFeedsExpressionEvaluation() {
        Express4Runner runner = runner();
        runner.addOperator("merge", (left, right) -> left.get() + "|" + right.get(), QLPrecedences.ADD);
        assertEquals("A|B|C", runner.execute("'A' merge 'B' merge 'C'", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /**
     * Seam: config interaction between custom precedence and built-in multiplication.
     * Verifies: QLX-EXT-008
     * Depends-On: arithmeticHonorsMultiplicationPrecedence
     */
    @Test void customOperatorPrecedenceComposesWithBuiltInOperator() {
        Express4Runner runner = runner();
        runner.addOperator("?><", (left, right) -> left.get().toString() + right.get().toString(), QLPrecedences.ADD);
        assertEquals("824", runner.execute("8 ?>< 6*4", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /**
     * Seam: config interaction between default operator replacement and later scripts.
     * Verifies: QLX-EXT-009
     * Depends-On: stringConcatenationWorksWithMixedOperands
     */
    @Test void replacingDefaultOperatorChangesLaterDispatch() {
        Express4Runner runner = runner();
        assertTrue(runner.replaceDefaultOperator("+", (left, right) ->
                Double.parseDouble(left.get().toString()) + Double.parseDouble(right.get().toString())));
        assertEquals(6.25d, runner.execute("'2.5'+'3.75'", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /**
     * Seam: protocol handoff from macro registry to execution context.
     * Verifies: QLX-EXT-015, QLX-EXT-017
     * Depends-On: stringConcatenationWorksWithMixedOperands
     */
    @Test void macroReadsCallerContextDuringExecution() {
        Express4Runner runner = runner();
        assertTrue(runner.addMacro("label", "name='id-'+name"));
        assertEquals("id-sigma", runner.execute("label", Collections.singletonMap("name", "sigma"), QLOptions.DEFAULT_OPTIONS).getResult());
    }

    /**
     * Seam: lifecycle crossing when a macro is replaced between executions.
     * Verifies: QLX-EXT-015, QLX-EXT-017
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void replacedMacroAffectsOnlyLaterExecution() {
        Express4Runner runner = runner();
        runner.addMacro("tag", "name='old-'+name");
        Object before = runner.execute("tag", Collections.singletonMap("name", "x"), QLOptions.DEFAULT_OPTIONS).getResult();
        runner.addOrReplaceMacro("tag", "name='new-'+name");
        Object after = runner.execute("tag", Collections.singletonMap("name", "x"), QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals("old-x", before);
        assertEquals("new-x", after);
    }

    /**
     * Seam: protocol handoff from token aliases to registered function dispatch.
     * Verifies: QLX-EXT-018
     * Depends-On: conditionalReturnsSelectedBranch, scriptFunctionReturnsComputedValue
     */
    @Test void aliasesComposeWithControlFlowAndFunctionNames() {
        Express4Runner runner = runner();
        runner.addFunction("zero", (context, parameters) -> 0);
        runner.addAlias("WHEN", "if");
        runner.addAlias("OTHER", "else");
        runner.addAlias("GT", ">");
        runner.addAlias("ZERO", "zero");
        Object value = runner.execute("WHEN(4 GT 9){1} OTHER {ZERO('x')}", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals(0, ((Number)value).intValue());
    }

    /**
     * Seam: registered-function agreement across direct, cached, and serializable-cache execution. CVI-5.
     * Verifies: QLX-EXT-001, QLX-CACHE-001, QLX-CACHE-004, QLX-EXEC-021, QLX-INV-005
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void registeredFunctionAgreesAcrossDirectCachedAndSerializableExecution() {
        Express4Runner runner = runner();
        runner.addFunction("doubleIt", (CustomFunction)(context, parameters) ->
                ((Number)parameters.getValue(0)).intValue() * 2);
        String script = "doubleIt(input)";
        Map<String, Object> context = Collections.singletonMap("input", 21);
        Object direct = runner.execute(script, context, QLOptions.DEFAULT_OPTIONS).getResult();
        Object cached = runner.execute(script, context, QLOptions.builder().cache(true).build()).getResult();
        SerializableParseCache portable = runner.parseToSerializableCache(script);
        Object serialized = runner.execute(portable, context, QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals(42, ((Number)direct).intValue());
        assertEquals(direct, cached);
        assertEquals(direct, serialized);
    }

    /**
     * Seam: registered-operator agreement across direct, cached, and serializable-cache execution. CVI-5.
     * Verifies: QLX-EXT-008, QLX-CACHE-001, QLX-CACHE-004, QLX-EXEC-021, QLX-INV-005
     * Depends-On: arithmeticHonorsMultiplicationPrecedence
     */
    @Test void registeredOperatorAgreesAcrossDirectCachedAndSerializableExecution() {
        Express4Runner runner = runner();
        runner.addOperator("sumWith", (left, right) ->
                ((Number)left.get()).intValue() + ((Number)right.get()).intValue(), QLPrecedences.ADD);
        String script = "left sumWith right";
        Map<String, Object> context = Map.of("left", 19, "right", 23);
        Object direct = runner.execute(script, context, QLOptions.DEFAULT_OPTIONS).getResult();
        Object cached = runner.execute(script, context, QLOptions.builder().cache(true).build()).getResult();
        SerializableParseCache portable = runner.parseToSerializableCache(script);
        Object serialized = runner.execute(portable, context, QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals(42, ((Number)direct).intValue());
        assertEquals(direct, cached);
        assertEquals(direct, serialized);
    }

    /**
     * Seam: protocol handoff from template parsing to context evaluation.
     * Verifies: QLX-OPT-017, QLX-EXEC-002
     * Depends-On: templateExecutionSubstitutesExpressions, arithmeticHonorsMultiplicationPrecedence
     */
    @Test void templateAndDirectExecutionAgreeOnExpressionValue() {
        Express4Runner runner = runner();
        Map<String, Object> context = new HashMap<>();
        context.put("a", 14);
        context.put("b", 3);
        Object direct = runner.execute("a*b", context, QLOptions.DEFAULT_OPTIONS).getResult();
        Object rendered = runner.executeTemplate("value=${a*b}", context, QLOptions.DEFAULT_OPTIONS).getResult();
        assertEquals("value=" + direct, rendered);
    }

    /**
     * Seam: state consistency between dependency inspection and executable context. CVI-2.
     * Verifies: QLX-VAL-005, QLX-INV-002
     * Depends-On: dependencyInspectionExcludesLocals
     */
    @Test void inspectedVariablesAreExactlyThoseRequiredForExecution() {
        Express4Runner runner = runner();
        String script = "local=4;local+left+right";
        assertEquals(new HashSet<>(Arrays.asList("left", "right")), runner.getOutVarNames(script));
        Map<String, Object> context = new HashMap<>();
        context.put("left", 10);
        context.put("right", 28);
        assertEquals(42, ((Number)runner.execute(script, context, QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: state consistency between function dependency inspection and registered execution. CVI-2.
     * Verifies: QLX-VAL-007, QLX-EXT-001, QLX-INV-002
     * Depends-On: functionInspectionExcludesScriptDefinitions, scriptFunctionReturnsComputedValue
     */
    @Test void inspectedFunctionsAreExactlyThoseRequiredForExecution() {
        Express4Runner runner = runner();
        String script = "function local(x){x+1};local(seed)+external(3)";
        assertEquals(Collections.singleton("external"), runner.getOutFunctions(script));
        runner.addFunction("external", (CustomFunction)(context, parameters) ->
                ((Number)parameters.getValue(0)).intValue() * 10);
        assertEquals(42, ((Number)runner.execute(
                script, Collections.singletonMap("seed", 11), QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: protocol handoff from validation policy to successful execution.
     * Verifies: QLX-VAL-001, QLX-VAL-003
     * Depends-On: whitelistStrategyRejectsUnlistedOperator, arithmeticHonorsMultiplicationPrecedence
     */
    @Test void validatedAllowedScriptExecutesWithSameOperators() {
        Express4Runner runner = runner();
        String script = "7+5*7";
        runner.check(script, CheckOptions.builder()
                .operatorCheckStrategy(OperatorCheckStrategy.whitelist(new HashSet<>(Arrays.asList("+", "*")))).build());
        assertEquals(42, ((Number)runner.execute(script, Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: error propagation from validation to execution for malformed input. CVI-6.
     * Verifies: QLX-ERR-001, QLX-INV-006
     * Depends-On: malformedScriptRaisesStructuredSyntaxException
     */
    @Test void malformedScriptFailsBothValidationAndExecution() {
        Express4Runner runner = runner();
        String script = "total+(3";
        assertThrows(QLSyntaxException.class, () -> runner.check(script));
        assertThrows(QLSyntaxException.class, () -> runner.execute(script, Collections.singletonMap("total", 39), QLOptions.DEFAULT_OPTIONS));
    }

    /**
     * Seam: error agreement between validation and execution for a malformed function body. CVI-6.
     * Verifies: QLX-ERR-001, QLX-INV-006
     * Depends-On: malformedScriptRaisesStructuredSyntaxException
     */
    @Test void malformedFunctionFailsBothValidationAndExecution() {
        Express4Runner runner = runner();
        String script = "function broken(x){x+};broken(1)";
        assertThrows(QLSyntaxException.class, () -> runner.check(script));
        assertThrows(QLSyntaxException.class, () ->
                runner.execute(script, Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS));
    }

    /**
     * Seam: state consistency between pre-execution and execution trace coordinates. CVI-7.
     * Verifies: QLX-CACHE-008, QLX-CACHE-009, QLX-INV-007
     * Depends-On: arithmeticHonorsMultiplicationPrecedence
     */
    @Test void tracePointAndExecutionTraceShareRootCoordinates() {
        Express4Runner runner = new Express4Runner(InitOptions.builder().traceExpression(true).build());
        String script = "left+right*2";
        TracePointTree point = runner.getExpressionTracePoints(script).get(0);
        Map<String, Object> context = new HashMap<>();
        context.put("left", 8);
        context.put("right", 17);
        ExpressionTrace trace = runner.execute(script, context, QLOptions.builder().traceExpression(true).build()).getExpressionTraces().get(0);
        assertEquals(point.getType(), trace.getType());
        assertEquals(point.getLine(), trace.getLine());
    }

    /**
     * Seam: coordinate agreement between multiline pre-execution and execution trace trees. CVI-7.
     * Verifies: QLX-CACHE-004, QLX-CACHE-005, QLX-CACHE-008, QLX-CACHE-009, QLX-INV-007
     * Depends-On: arithmeticHonorsMultiplicationPrecedence
     */
    @Test void multilineTraceTreesShareSourceLineCoordinates() {
        Express4Runner runner = new Express4Runner(InitOptions.builder().traceExpression(true).build());
        String script = "base=40;\nbase+2";
        TracePointTree point = runner.getExpressionTracePoints(script).get(0);
        LoadedParseCache loaded = runner.loadSerializableCache(runner.parseToSerializableCache(script));
        ExpressionTrace trace = runner.execute(loaded, new MapExpressContext(Collections.emptyMap()),
                QLOptions.builder().traceExpression(true).build()).getExpressionTraces().get(0);
        assertEquals(tracePointLines(point), expressionTraceLines(trace));
    }

    private Set<Integer> tracePointLines(TracePointTree node) {
        Set<Integer> lines = new HashSet<>();
        lines.add(node.getLine());
        for (TracePointTree child : node.getChildren()) {
            lines.addAll(tracePointLines(child));
        }
        return lines;
    }

    private Set<Integer> expressionTraceLines(ExpressionTrace node) {
        Set<Integer> lines = new HashSet<>();
        lines.add(node.getLine());
        for (ExpressionTrace child : node.getChildren()) {
            lines.addAll(expressionTraceLines(child));
        }
        return lines;
    }

    /**
     * Seam: state observation for a short-circuited branch in execution tracing.
     * Verifies: QLX-EXEC-014, QLX-CACHE-010
     * Depends-On: logicalAndShortCircuitsByDefault
     */
    @Test void shortCircuitedTraceContainsUnevaluatedNode() {
        Express4Runner runner = new Express4Runner(InitOptions.builder().traceExpression(true).build());
        QLResult result = runner.execute("false && (4/0>1)", Collections.emptyMap(), QLOptions.builder().traceExpression(true).build());
        ExpressionTrace root = result.getExpressionTraces().get(0);
        assertEquals(Boolean.FALSE, result.getResult());
        assertTrue(containsUnevaluatedNode(root));
    }

    private boolean containsUnevaluatedNode(ExpressionTrace node) {
        if (!node.isEvaluated()) {
            return true;
        }
        for (ExpressionTrace child : node.getChildren()) {
            if (containsUnevaluatedNode(child)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Seam: protocol handoff from extension registration to member-shaped script dispatch.
     * Verifies: QLX-EXT-011
     * Depends-On: arithmeticHonorsMultiplicationPrecedence
     */
    @Test void extensionFunctionDispatchesOnBoundReceiver() {
        Express4Runner runner = runner();
        runner.addExtendFunction("plus", Number.class,
                values -> ((Number)values[0]).intValue() + ((Number)values[1]).intValue());
        assertEquals(42, ((Number)runner.execute("19.plus(23)", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: state projection from alias annotations to object fields.
     * Verifies: QLX-EXEC-004, QLX-SEC-001
     * Depends-On: lowercaseClassAliasIsRejected
     */
    @Test void aliasObjectExposesAnnotatedObjectName() {
        Express4Runner runner = new Express4Runner(InitOptions.builder().securityStrategy(QLSecurityStrategy.open()).build());
        Object value = runner.executeWithAliasObjects("account.credit+2", QLOptions.DEFAULT_OPTIONS, new OracleModels.Account(40)).getResult();
        assertEquals(42, ((Number)value).intValue());
    }

    /**
     * Seam: protocol handoff from object context projection to public Java method invocation.
     * Verifies: QLX-EXEC-003, QLX-SEC-001
     * Depends-On: defaultClassSupplierLoadsKnownClassAndReturnsNullForMissingClass
     */
    @Test void objectContextSupportsPublicFieldAndMethodUse() {
        Express4Runner runner = new Express4Runner(InitOptions.builder().securityStrategy(QLSecurityStrategy.open()).build());
        OracleModels.Account account = new OracleModels.Account(30);
        assertEquals(42, ((Number)runner.execute("balance+12", account, QLOptions.DEFAULT_OPTIONS).getResult()).intValue());
    }

    /**
     * Seam: open-security agreement across object and alias-object contexts. CVI-9.
     * Verifies: QLX-EXEC-003, QLX-EXEC-004, QLX-SEC-001, QLX-INV-009
     * Depends-On: defaultClassSupplierLoadsKnownClassAndReturnsNullForMissingClass
     */
    @Test void openSecurityAgreesAcrossObjectAndAliasContexts() {
        Express4Runner runner = new Express4Runner(InitOptions.builder().securityStrategy(QLSecurityStrategy.open()).build());
        OracleModels.Account account = new OracleModels.Account(40);
        Object objectValue = runner.execute("balance+2", account, QLOptions.DEFAULT_OPTIONS).getResult();
        Object aliasValue = runner.executeWithAliasObjects(
                "account.credit+2", QLOptions.DEFAULT_OPTIONS, account).getResult();
        assertEquals(42, ((Number)objectValue).intValue());
        assertEquals(objectValue, aliasValue);
    }

    /**
     * Seam: blacklist-security agreement across object and alias-object contexts. CVI-9.
     * Verifies: QLX-EXEC-003, QLX-EXEC-004, QLX-SEC-002, QLX-ERR-007, QLX-INV-009
     * Depends-On: defaultClassSupplierLoadsKnownClassAndReturnsNullForMissingClass, lowercaseClassAliasIsRejected
     */
    @Test void blacklistSecurityRejectsMethodAcrossObjectAndAliasContexts() throws Exception {
        Set<Member> blocked = new HashSet<>();
        blocked.add(OracleModels.Account.class.getMethod("getBalance"));
        Express4Runner runner = new Express4Runner(
                InitOptions.builder().securityStrategy(QLSecurityStrategy.blackList(blocked)).build());
        OracleModels.Account account = new OracleModels.Account(40);
        assertThrows(QLRuntimeException.class, () ->
                runner.execute("getBalance()", account, QLOptions.DEFAULT_OPTIONS));
        assertThrows(QLRuntimeException.class, () ->
                runner.executeWithAliasObjects("account.getBalance()", QLOptions.DEFAULT_OPTIONS, account));
    }

    /**
     * Seam: config interaction between attachment options and callback execution context.
     * Verifies: QLX-OPT-010, QLX-EXT-001
     * Depends-On: executionOptionsBuilderRetainsAllChoices, scriptFunctionReturnsComputedValue
     */
    @Test void attachmentsReachCustomFunctionWithoutBecomingVariables() throws Exception {
        Express4Runner runner = runner();
        Method attachmentProjection = QContext.class.getMethod("attachment");
        assertEquals(0, attachmentProjection.getParameterCount());
        runner.addFunction("tenantPrefix", (context, parameters) ->
                ((Map<?, ?>)attachmentProjection.invoke(context)).get("tenant") + ":" + parameters.getValue(0));
        QLOptions options = QLOptions.builder().attachments(Collections.singletonMap("tenant", "green")).build();
        assertEquals(Collections.emptySet(), runner.getOutVarNames("tenantPrefix('42')"));
        assertEquals("green:42", runner.execute("tenantPrefix('42')", Collections.emptyMap(), options).getResult());
    }

    /**
     * Seam: config interaction between null avoidance and ordered comparison.
     * Verifies: QLX-OPT-011
     * Depends-On: nullAvoidanceProjectsMissingMemberAsNull
     */
    @Test void nullAvoidancePropagatesThroughComparison() {
        Map<String, Object> context = new HashMap<>();
        context.put("record", null);
        Object value = runner().execute("record.missing > 3", context, QLOptions.builder().avoidNullPointer(true).build()).getResult();
        assertEquals(Boolean.FALSE, value);
    }

    /**
     * Seam: lifecycle crossing between repeated cached execution and changing contexts.
     * Verifies: QLX-CACHE-001, QLX-STATE-001
     * Depends-On: executionOptionsBuilderRetainsAllChoices, arithmeticHonorsMultiplicationPrecedence
     */
    @Test void cachedExecutionUsesFreshContextEachTime() {
        Express4Runner runner = runner();
        QLOptions cached = QLOptions.builder().cache(true).build();
        assertEquals(17, ((Number)runner.execute("x+9", Collections.singletonMap("x", 8), cached).getResult()).intValue());
        assertEquals(42, ((Number)runner.execute("x+9", Collections.singletonMap("x", 33), cached).getResult()).intValue());
    }

    /**
     * Seam: config interaction between a member blacklist and Java method dispatch.
     * Verifies: QLX-SEC-002, QLX-ERR-007
     * Depends-On: defaultClassSupplierLoadsKnownClassAndReturnsNullForMissingClass
     */
    @Test void rejectedJavaMemberAccessRaisesRuntimeException() throws Exception {
        Set<Member> blocked = new HashSet<>();
        blocked.add(String.class.getMethod("length"));
        Express4Runner runner = new Express4Runner(
                InitOptions.builder().securityStrategy(QLSecurityStrategy.blackList(blocked)).build());
        assertThrows(QLRuntimeException.class, () -> runner.execute(
                "text.length()", Collections.singletonMap("text", "blocked"), QLOptions.DEFAULT_OPTIONS));
    }

    /**
     * Seam: error propagation from a declared callback failure to the public QLException projection.
     * Verifies: QLX-EXT-013, QLX-ERR-008
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void userDefinedCallbackProjectsNamedBusinessError() {
        Express4Runner runner = runner();
        runner.addFunction("rejectOrder", (CustomFunction)(context, parameters) -> {
            throw OracleModels.businessException("rejected");
        });
        QLException error = assertThrows(QLException.class, () -> runner.execute(
                "rejectOrder(17)", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS));
        assertEquals("BIZ_EXCEPTION", String.valueOf(error.getErrorCode()));
    }

    /**
     * Seam: error propagation retains the originating throwable across callback dispatch.
     * Verifies: QLX-EXT-014, QLX-ERR-011
     * Depends-On: scriptFunctionReturnsComputedValue
     */
    @Test void wrappedCallbackFailureRetainsOriginatingThrowable() {
        Express4Runner runner = runner();
        IllegalStateException origin = new IllegalStateException("origin-marker");
        runner.addFunction("explode", (CustomFunction)(context, parameters) -> {
            throw origin;
        });
        QLRuntimeException error = assertThrows(QLRuntimeException.class, () -> runner.execute(
                "explode()", Collections.emptyMap(), QLOptions.DEFAULT_OPTIONS));
        assertTrue(error.getCause() == origin || error.getCatchObj() == origin);
    }
}
