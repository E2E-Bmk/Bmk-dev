package integration;

import com.tngtech.archunit.ArchConfiguration;
import com.tngtech.archunit.core.domain.Dependency;
import com.tngtech.archunit.core.domain.JavaAccess;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.domain.JavaConstructorCall;
import com.tngtech.archunit.core.domain.JavaMethodCall;
import com.tngtech.archunit.core.domain.PackageMatcher;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.EvaluationResult;
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition;
import com.tngtech.archunit.library.Architectures;
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition;
import com.tngtech.archunit.library.freeze.FreezingArchRule;
import com.tngtech.archunit.library.metrics.ArchitectureMetrics;
import com.tngtech.archunit.library.metrics.LakosMetrics;
import com.tngtech.archunit.library.metrics.MetricsComponents;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import support.InMemoryViolationStore;
import support.OracleSupport;
import support.fixture.api.PublicApi;
import support.fixture.cycle.alpha.Alpha;
import support.fixture.cycle.beta.Beta;
import support.fixture.repository.Repository;
import support.fixture.service.OrderService;

import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

class IntegrationCrossViewTest {
    @AfterEach void resetConfiguration() { ArchConfiguration.get().reset(); }

    private static void permitFreezeWrites() {
        ArchConfiguration.get().setProperty("freeze.store.default.allowStoreCreation", "true");
        ArchConfiguration.get().setProperty("freeze.store.default.allowStoreUpdate", "true");
    }

            /** Verifies: ARCH-INV-002, ARCH-DOM-012, ARCH-DOM-013, ARCH-DOM-016, ARCH-DOM-019, ARCH-DOM-020, ARCH-INV-001
     * Depends-On: dependencyViewExposesServiceRelations, declaredFieldAndMethodLookupsResolve */
    @Test void methodCallsAreGeneralAccessesAndDependencies() {
        JavaClass service = OracleSupport.graph().get(OrderService.class);
        JavaMethodCall call = service.getMethodCallsFromSelf().stream()
                .filter(c -> c.getTarget().getOwner().isEquivalentTo(Repository.class)).findFirst().orElseThrow();
        Set<JavaClass> dependencyTargets = service.getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).collect(Collectors.toSet());
        assertAll(() -> assertTrue(service.getAccessesFromSelf().contains(call)),
                () -> assertTrue(dependencyTargets.contains(call.getTargetOwner())));
    }

    /** Verifies: ARCH-INV-002, ARCH-DOM-012, ARCH-DOM-013, ARCH-DOM-016, ARCH-DOM-019, ARCH-DOM-020, ARCH-INV-001
     * Depends-On: importsUnionOfReflectedClasses, dependencyViewExposesServiceRelations */
    @Test void constructorCallsAreGeneralAccessesAndDependencies() {
        JavaClass api = OracleSupport.graph().get(PublicApi.class);
        JavaConstructorCall call = api.getConstructorCallsFromSelf().stream()
                .filter(c -> c.getTarget().getOwner().isEquivalentTo(OrderService.class)).findFirst().orElseThrow();
        Set<JavaClass> dependencyTargets = api.getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).collect(Collectors.toSet());
        assertAll(() -> assertTrue(api.getAccessesFromSelf().contains(call)),
                () -> assertTrue(dependencyTargets.contains(call.getTargetOwner())));
    }

    /** Verifies: ARCH-INV-003, ARCH-DOM-016, ARCH-DOM-019, ARCH-DOM-020
     * Depends-On: dependencyViewExposesServiceRelations, containmentWorksByClassAndName */
    @Test void forwardDependencyHasMatchingReverseProjection() {
        JavaClasses graph = OracleSupport.graph();
        JavaClass service = graph.get(OrderService.class);
        Dependency outgoing = service.getDirectDependenciesFromSelf().stream()
                .filter(d -> d.getTargetClass().isEquivalentTo(Repository.class)).findFirst().orElseThrow();
        Set<String> reverseKeys = graph.get(Repository.class).getDirectDependenciesToSelf().stream()
                .map(d -> d.getOriginClass().getName() + "->" + d.getTargetClass().getName()).collect(Collectors.toSet());
        assertTrue(reverseKeys.contains(outgoing.getOriginClass().getName() + "->" + outgoing.getTargetClass().getName()));
    }

    /** Verifies: ARCH-INV-003, ARCH-DOM-016, ARCH-DOM-020
     * Depends-On: importsUnionOfReflectedClasses, dependencyViewExposesServiceRelations */
    @Test void everyInternalOutgoingDependencyHasReverseEndpointView() {
        JavaClasses graph = OracleSupport.graph();
        Set<String> reverseKeys = graph.stream().flatMap(c -> c.getDirectDependenciesToSelf().stream())
                .map(d -> d.getOriginClass().getName() + "->" + d.getTargetClass().getName()).collect(Collectors.toSet());
        boolean allMirrored = graph.stream().flatMap(c -> c.getDirectDependenciesFromSelf().stream())
                .filter(d -> graph.contain(d.getTargetClass().getName()))
                .allMatch(d -> reverseKeys.contains(d.getOriginClass().getName() + "->" + d.getTargetClass().getName()));
        assertTrue(allMirrored);
    }

    /** Verifies: ARCH-INV-004, ARCH-PKG-001, ARCH-PKG-009, ARCH-PKG-012
     * Depends-On: starMatchesExactlyOnePackageSegment, collectionFiltersWithDescribedPredicate */
    @Test void packageMatcherAndJavaClassPredicateSelectSameClasses() {
        JavaClasses graph = OracleSupport.graph();
        PackageMatcher matcher = PackageMatcher.of("..service");
        Set<String> direct = graph.stream().filter(c -> matcher.matches(c.getPackageName())).map(JavaClass::getName).collect(Collectors.toSet());
        Set<String> predicate = graph.that(JavaClass.Predicates.resideInAPackage("..service")).stream().map(JavaClass::getName).collect(Collectors.toSet());
        assertEquals(direct, predicate);
    }

    /** Verifies: ARCH-INV-004, ARCH-PKG-001, ARCH-RULE-002
     * Depends-On: doubleDotMatchesZeroOrManySegments, violatingRuleReportsViolationAndCheckFails */
    @Test void packageMatcherAndFluentRuleShareSelectionLanguage() {
        JavaClasses graph = OracleSupport.graph();
        long matched = graph.stream().filter(c -> PackageMatcher.of("..service").matches(c.getPackageName())).count();
        ArchRule rule = ArchRuleDefinition.noClasses().that().resideInAPackage("..service")
                .should().resideInAPackage("..service");
        assertAll(() -> assertTrue(matched > 0), () -> assertTrue(rule.evaluate(graph).hasViolation()));
    }

    /** Verifies: ARCH-INV-005, ARCH-RULE-006
     * Depends-On: violatingRuleReportsViolationAndCheckFails, defaultRuleUsesMediumPriority */
    @Test void violatingEvaluationExactlyMatchesCheckFailure() {
        ArchRule rule = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        JavaClasses graph = OracleSupport.graph();
        assertEquals(rule.evaluate(graph).hasViolation(), assertThrows(AssertionError.class, () -> rule.check(graph)) != null);
    }

    /** Verifies: ARCH-INV-005, ARCH-RULE-006
     * Depends-On: explicitlyAllowedEmptySelectionDoesNotViolate, defaultRuleUsesMediumPriority */
    @Test void successfulEvaluationExactlyMatchesSuccessfulCheck() {
        ArchRule rule = ArchRuleDefinition.classes().should().resideInAPackage("support.fixture..");
        JavaClasses graph = OracleSupport.graph();
        assertAll(() -> assertFalse(rule.evaluate(graph).hasViolation()), () -> assertDoesNotThrow(() -> rule.check(graph)));
    }

    /** Verifies: ARCH-INV-006, ARCH-RULE-007, ARCH-RULE-010, ARCH-RULE-018
     * Depends-On: becauseChangesDescriptionWithoutChangingOutcome, violatingRuleReportsViolationAndCheckFails */
    @Test void becauseChangesDescriptionButNotViolationCount() {
        ArchRule original = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        ArchRule explained = original.because("isolation");
        assertAll(() -> assertNotEquals(original.getDescription(), explained.getDescription()),
                () -> assertEquals(original.evaluate(OracleSupport.graph()).getFailureReport().getDetails().size(),
                        explained.evaluate(OracleSupport.graph()).getFailureReport().getDetails().size()));
    }

    /** Verifies: ARCH-INV-007, ARCH-LIB-002, ARCH-DOM-016, ARCH-LIB-015, ARCH-LIB-016
     * Depends-On: configuredLayerRuleEvaluatesDefinedPackages, dependencyViewExposesServiceRelations */
    @Test void layeredViolationCorrespondsToDirectGraphDependency() {
        JavaClasses graph = OracleSupport.graph();
        ArchRule layerRule = Architectures.layeredArchitecture().consideringOnlyDependenciesInAnyPackage("support.fixture..")
                .layer("Api").definedBy("..api")
                .layer("Service").definedBy("..service")
                .whereLayer("Api").mayNotAccessAnyLayer();
        Set<String> dependencyTargets = graph.get(PublicApi.class).getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).map(JavaClass::getName).collect(Collectors.toSet());
        boolean dependencyExists = dependencyTargets.contains(OrderService.class.getName());
        assertAll(() -> assertTrue(dependencyExists), () -> assertTrue(layerRule.evaluate(graph).hasViolation()));
    }

    /** Verifies: ARCH-INV-007, ARCH-LIB-008, ARCH-LIB-010, ARCH-DOM-016
     * Depends-On: packageSlicesDetectDirectedCycle, importsUnionOfReflectedClasses */
    @Test void sliceCycleCorrespondsToBidirectionalClassDependencies() {
        JavaClasses graph = new com.tngtech.archunit.core.importer.ClassFileImporter().importClasses(Alpha.class, Beta.class);
        ArchRule slices = SlicesRuleDefinition.slices().matching("support.fixture.cycle.(*)..").should().beFreeOfCycles();
        Set<String> alphaTargets = graph.get(Alpha.class).getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).map(JavaClass::getName).collect(Collectors.toSet());
        Set<String> betaTargets = graph.get(Beta.class).getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).map(JavaClass::getName).collect(Collectors.toSet());
        boolean bothDirections = alphaTargets.contains(Beta.class.getName()) && betaTargets.contains(Alpha.class.getName());
        assertAll(() -> assertTrue(bothDirections), () -> assertTrue(slices.evaluate(graph).hasViolation()));
    }

    /** Verifies: ARCH-INV-008, ARCH-MET-003, ARCH-DOM-016, ARCH-MET-010, ARCH-MET-011
     * Depends-On: metricComponentsAndLakosUseNamedClasses, dependencyViewExposesServiceRelations */
    @Test void lakosMetricsReflectInternalDependencyTargets() {
        JavaClasses graph = OracleSupport.graph();
        JavaClass service = graph.get(OrderService.class);
        long distinctTargets = service.getDirectDependenciesFromSelf().stream().map(Dependency::getTargetClass)
                .filter(c -> graph.contain(c.getName())).map(JavaClass::getName).distinct().count();
        MetricsComponents<JavaClass> components = MetricsComponents.fromClasses(graph);
        LakosMetrics connected = ArchitectureMetrics.lakosMetrics(components);
        LakosMetrics disconnected = ArchitectureMetrics.lakosMetrics(components, ignored -> java.util.List.of());
        assertAll(() -> assertTrue(distinctTargets > 0),
                () -> assertEquals(graph.size(), disconnected.getCumulativeComponentDependency()),
                () -> assertTrue(connected.getCumulativeComponentDependency() > disconnected.getCumulativeComponentDependency()));
    }

    /** Verifies: ARCH-INV-008, ARCH-MET-003, ARCH-DOM-016, ARCH-MET-011
     * Depends-On: lakosMetricsExposeFiniteGraphRatios, dependencyViewExposesServiceRelations */
    @Test void lakosCumulativeDependencyReflectsReachableGraphEdges() {
        JavaClasses graph = OracleSupport.graph();
        LakosMetrics metrics = ArchitectureMetrics.lakosMetrics(MetricsComponents.fromClasses(graph));
        Set<String> targetNames = graph.get(PublicApi.class).getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).map(JavaClass::getName).collect(Collectors.toSet());
        assertAll(() -> assertTrue(targetNames.contains(OrderService.class.getName())),
                () -> assertTrue(metrics.getCumulativeComponentDependency() > graph.size()));
    }

    /** Verifies: ARCH-INV-009, ARCH-FRZ-002, ARCH-RULE-010, ARCH-RULE-018, ARCH-STATE-001
     * Depends-On: firstEvaluationPersistsBaselineAndSuppressesKnownViolations, violatingRuleReportsViolationAndCheckFails */
    @Test void frozenBaselinePersistsWrappedViolationSet() {
        permitFreezeWrites();
        JavaClasses graph = OracleSupport.graph();
        ArchRule wrapped = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        int wrappedCount = wrapped.evaluate(graph).getFailureReport().getDetails().size();
        InMemoryViolationStore store = new InMemoryViolationStore();
        FreezingArchRule.freeze(wrapped).persistIn(store).evaluate(graph);
        assertEquals(wrappedCount, store.getViolations(wrapped).size());
    }

    /** Verifies: ARCH-INV-009, ARCH-FRZ-003, ARCH-RULE-006, ARCH-RULE-018, ARCH-STATE-001
     * Depends-On: repeatedEvaluationUsesStoredBaseline, violatingRuleReportsViolationAndCheckFails */
    @Test void frozenRuleSuppressesExactlyTheStoredCurrentSet() {
        permitFreezeWrites();
        JavaClasses graph = OracleSupport.graph();
        ArchRule wrapped = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        InMemoryViolationStore store = new InMemoryViolationStore();
        FreezingArchRule frozen = FreezingArchRule.freeze(wrapped).persistIn(store);
        frozen.evaluate(graph);
        assertAll(() -> assertEquals(wrapped.evaluate(graph).getFailureReport().getDetails().size(), store.getViolations(wrapped).size()),
                () -> assertFalse(frozen.evaluate(graph).hasViolation()), () -> assertDoesNotThrow(() -> frozen.check(graph)));
    }
}
