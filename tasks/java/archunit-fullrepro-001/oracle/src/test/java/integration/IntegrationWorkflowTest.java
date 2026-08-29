package integration;

import com.tngtech.archunit.ArchConfiguration;
import com.tngtech.archunit.core.domain.Dependency;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.domain.JavaField;
import com.tngtech.archunit.core.domain.PackageMatcher;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.CompositeArchRule;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.EvaluationResult;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition;
import com.tngtech.archunit.library.Architectures;
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition;
import com.tngtech.archunit.library.freeze.FreezingArchRule;
import com.tngtech.archunit.library.metrics.ArchitectureMetrics;
import com.tngtech.archunit.library.metrics.LakosMetrics;
import com.tngtech.archunit.library.metrics.MetricsComponents;
import com.tngtech.archunit.library.metrics.VisibilityMetrics;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import support.InMemoryViolationStore;
import support.OracleSupport;
import support.fixture.api.PublicApi;
import support.fixture.cycle.alpha.Alpha;
import support.fixture.cycle.beta.Beta;
import support.fixture.isolated.Independent;
import support.fixture.repository.Repository;
import support.fixture.service.OrderService;

import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

class IntegrationWorkflowTest {
    @AfterEach void resetConfiguration() { ArchConfiguration.get().reset(); }

    private static void permitFreezeWrites() {
        ArchConfiguration.get().setProperty("freeze.store.default.allowStoreCreation", "true");
        ArchConfiguration.get().setProperty("freeze.store.default.allowStoreUpdate", "true");
    }

    /** Verifies: ARCH-ORI-001, ARCH-IMP-002, ARCH-DOM-004, ARCH-DOM-016
     * Depends-On: importsUnionOfReflectedClasses, classExposesStableNameViews */
    @Test void importedWorkflowConnectsCollectionMetadataAndDependencies() {
        JavaClasses graph = OracleSupport.graph();
        JavaClass api = graph.get(PublicApi.class);
        Set<String> targetNames = api.getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).map(JavaClass::getName).collect(Collectors.toSet());
        assertAll(() -> assertTrue(graph.contain(api.getName())),
                () -> assertEquals("support.fixture.api", api.getPackageName()),
                () -> assertTrue(targetNames.contains(OrderService.class.getName())));
    }

    /** Verifies: ARCH-ORI-001, ARCH-DOM-007, ARCH-DOM-012, ARCH-DOM-013, ARCH-DOM-020
     * Depends-On: declaredFieldAndMethodLookupsResolve, dependencyViewExposesServiceRelations */
    @Test void serviceWorkflowConnectsMembersCallsAndTargets() {
        JavaClass service = OracleSupport.graph().get(OrderService.class);
        Set<String> callTargetOwners = service.getMethodCallsFromSelf().stream()
                .map(c -> c.getTargetOwner().getName()).collect(Collectors.toSet());
        assertAll(() -> assertEquals(Repository.class.getName(), service.getField("repository").getRawType().getName()),
                () -> assertTrue(callTargetOwners.contains(Repository.class.getName())),
                () -> assertTrue(service.getAccessesFromSelf().size() >= service.getMethodCallsFromSelf().size()));
    }

    /** Verifies: ARCH-ORI-002, ARCH-PKG-001, ARCH-RULE-002, ARCH-RULE-006
     * Depends-On: doubleDotMatchesZeroOrManySegments, violatingRuleReportsViolationAndCheckFails */
    @Test void fluentRuleWorkflowUsesPackageSelectionAndBothResultViews() {
        JavaClasses graph = OracleSupport.graph();
        ArchRule rule = ArchRuleDefinition.noClasses().that().resideInAPackage("..service").should().dependOnClassesThat().resideInAPackage("..repository");
        EvaluationResult result = rule.evaluate(graph);
        assertAll(() -> assertTrue(result.hasViolation()), () -> assertThrows(AssertionError.class, () -> rule.check(graph)));
    }

    /** Verifies: ARCH-LIB-002, ARCH-LIB-003, ARCH-INV-004, ARCH-INV-007, ARCH-LIB-015, ARCH-LIB-016
     * Depends-On: configuredLayerRuleEvaluatesDefinedPackages, doubleDotMatchesZeroOrManySegments */
    @Test void layeredArchitectureUsesSamePackageBoundariesAsGraph() {
        JavaClasses graph = OracleSupport.graph();
        ArchRule rule = Architectures.layeredArchitecture().consideringOnlyDependenciesInAnyPackage("support.fixture..")
                .layer("Api").definedBy("..api")
                .layer("Service").definedBy("..service")
                .whereLayer("Api").mayOnlyAccessLayers("Service");
        assertAll(() -> assertTrue(PackageMatcher.of("..api").matches(graph.get(PublicApi.class).getPackageName())),
                () -> assertFalse(rule.evaluate(graph).hasViolation()));
    }

    /** Verifies: ARCH-LIB-008, ARCH-LIB-010, ARCH-INV-007
     * Depends-On: packageSlicesDetectDirectedCycle, dependencyViewExposesServiceRelations */
    @Test void sliceWorkflowGroupsPackagesAndReportsCycle() {
        JavaClasses graph = new ClassFileImporter().importClasses(Alpha.class, Beta.class);
        ArchRule cycleRule = SlicesRuleDefinition.slices().matching("support.fixture.cycle.(*)..").namingSlices("Slice $1").should().beFreeOfCycles();
        assertAll(() -> assertEquals(2, graph.stream().map(JavaClass::getPackageName).distinct().count()),
                () -> assertTrue(cycleRule.evaluate(graph).hasViolation()));
    }

    /** Verifies: ARCH-MET-001, ARCH-MET-003, ARCH-INV-008, ARCH-MET-011
     * Depends-On: lakosMetricsExposeFiniteGraphRatios, metricComponentsAndLakosUseNamedClasses */
    @Test void metricsWorkflowProjectsSameImportedDependencyGraph() {
        JavaClasses graph = OracleSupport.graph();
        MetricsComponents<JavaClass> components = MetricsComponents.fromClasses(graph);
        LakosMetrics lakos = ArchitectureMetrics.lakosMetrics(components);
        assertAll(() -> assertEquals(graph.size(), components.size()),
                () -> assertTrue(lakos.getCumulativeComponentDependency() > graph.size()),
                () -> assertTrue(components.tryGetComponent(PublicApi.class.getName()).isPresent()));
    }

    /** Verifies: ARCH-ORI-003, ARCH-FRZ-002, ARCH-MET-003, ARCH-INV-009, ARCH-MET-011, ARCH-STATE-001
     * Depends-On: firstEvaluationPersistsBaselineAndSuppressesKnownViolations, lakosMetricsExposeFiniteGraphRatios */
    @Test void frozenAndMetricsWorkflowShareOneImportedGraph() {
        permitFreezeWrites();
        JavaClasses graph = OracleSupport.graph();
        InMemoryViolationStore store = new InMemoryViolationStore();
        ArchRule rule = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        boolean frozenViolation = FreezingArchRule.freeze(rule).persistIn(store).evaluate(graph).hasViolation();
        int ccd = ArchitectureMetrics.lakosMetrics(MetricsComponents.fromClasses(graph)).getCumulativeComponentDependency();
        assertAll(() -> assertFalse(frozenViolation), () -> assertFalse(store.getViolations(rule).isEmpty()),
                () -> assertTrue(ccd > graph.size()));
    }

    /** Verifies: ARCH-RULE-009, ARCH-RULE-015, ARCH-RULE-018, ARCH-RULE-020
     * Depends-On: customConditionLifecycleAndCompositeEvaluationAreObservable, violatingRuleReportsViolationAndCheckFails */
    @Test void compositeRuleAggregatesIndependentViolations() {
        JavaClasses graph = OracleSupport.graph();
        ArchRule service = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        ArchRule repository = ArchRuleDefinition.noClasses().should().resideInAPackage("..repository");
        EvaluationResult combined = CompositeArchRule.of(service).and(repository).evaluate(graph);
        int separate = service.evaluate(graph).getFailureReport().getDetails().size()
                + repository.evaluate(graph).getFailureReport().getDetails().size();
        assertEquals(separate, combined.getFailureReport().getDetails().size());
    }

    /** Verifies: ARCH-LIB-007, ARCH-INV-006, ARCH-LIB-015, ARCH-LIB-016, ARCH-RULE-007, ARCH-RULE-018
     * Depends-On: asReplacesDescriptionWithoutChangingOutcome, configuredLayerRuleEvaluatesDefinedPackages */
    @Test void architectureDescriptionChangesWithoutChangingFindings() {
        JavaClasses graph = OracleSupport.graph();
        ArchRule original = Architectures.layeredArchitecture().consideringOnlyDependenciesInAnyPackage("support.fixture..")
                .layer("Api").definedBy("..api").layer("Service").definedBy("..service")
                .whereLayer("Api").mayNotAccessAnyLayer();
        ArchRule renamed = original.as("renamed architecture");
        assertAll(() -> assertNotEquals(original.getDescription(), renamed.getDescription()),
                () -> assertEquals(original.evaluate(graph).hasViolation(), renamed.evaluate(graph).hasViolation()),
                () -> assertEquals(original.evaluate(graph).getFailureReport().getDetails().size(), renamed.evaluate(graph).getFailureReport().getDetails().size()));
    }

    /** Verifies: ARCH-MET-003, ARCH-MET-007, ARCH-MET-010, ARCH-MET-011
     * Depends-On: lakosMetricsExposeFiniteGraphRatios */
    @Test void lakosRatiosAgreeWithCumulativeDependency() {
        MetricsComponents<String> components = MetricsComponents.from(java.util.List.of("a", "b", "c"), s -> s);
        LakosMetrics metrics = ArchitectureMetrics.lakosMetrics(components, value -> java.util.List.of());
        assertAll(() -> assertEquals(3, metrics.getCumulativeComponentDependency()),
                () -> assertEquals(1.0, metrics.getAverageComponentDependency(), 0.0),
                () -> assertEquals(1.0 / 3.0, metrics.getRelativeAverageComponentDependency(), 1e-12));
    }

    /** Verifies: ARCH-IMP-003, ARCH-DOM-001, ARCH-PKG-012
     * Depends-On: importOptionCanRejectEveryLocation, collectionFiltersWithDescribedPredicate */
    @Test void importerFilterAndGraphPredicateCompose() {
        JavaClasses graph = new ClassFileImporter().withImportOption(location -> true)
                .importClasses(PublicApi.class, OrderService.class, Independent.class);
        Set<String> selected = graph.that(JavaClass.Predicates.resideOutsideOfPackage("..isolated"))
                .stream().map(JavaClass::getName).collect(Collectors.toSet());
        assertAll(() -> assertTrue(selected.contains(PublicApi.class.getName())),
                () -> assertTrue(selected.contains(OrderService.class.getName())),
                () -> assertFalse(selected.contains(Independent.class.getName())));
    }

    /** Verifies: ARCH-RULE-001, ARCH-RULE-004, ARCH-DOM-010, ARCH-RULE-016, ARCH-RULE-019
     * Depends-On: declaredFieldAndMethodLookupsResolve, defaultRuleUsesMediumPriority */
    @Test void memberRuleAgreesWithImportedFieldMetadata() {
        JavaClasses graph = OracleSupport.graph();
        JavaClass owner = graph.get(OrderService.class);
        ArchCondition<JavaField> publicRepository = new ArchCondition<>("expose repository publicly") {
            @Override public void check(JavaField item, ConditionEvents events) {
                boolean satisfied = !item.getName().equals("repository")
                        || item.getModifiers().contains(com.tngtech.archunit.core.domain.JavaModifier.PUBLIC);
                events.add(satisfied ? SimpleConditionEvent.satisfied(item, item.getName())
                        : SimpleConditionEvent.violated(item, item.getName()));
            }
        };
        ArchRule rule = ArchRuleDefinition.fields().should(publicRepository);
        assertAll(() -> assertTrue(owner.getField("repository").getModifiers().contains(com.tngtech.archunit.core.domain.JavaModifier.PUBLIC)),
                () -> assertFalse(rule.evaluate(graph).hasViolation()));
    }

    /** Verifies: ARCH-FRZ-003, ARCH-FRZ-007, ARCH-INV-009, ARCH-STATE-001
     * Depends-On: repeatedEvaluationUsesStoredBaseline, firstEvaluationPersistsBaselineAndSuppressesKnownViolations */
    @Test void frozenWorkflowRemovesResolvedBaselineLines() {
        permitFreezeWrites();
        InMemoryViolationStore store = new InMemoryViolationStore();
        ArchRule wrapped = ArchRuleDefinition.noClasses().should().resideInAPackage("..service");
        FreezingArchRule frozen = FreezingArchRule.freeze(wrapped).persistIn(store);
        frozen.evaluate(OracleSupport.graph());
        JavaClasses resolved = new ClassFileImporter().importClasses(Independent.class);
        assertAll(() -> assertFalse(frozen.evaluate(resolved).hasViolation()),
                () -> assertTrue(store.getViolations(wrapped).isEmpty()));
    }

    /** Verifies: ARCH-ERR-001, ARCH-ERR-002, ARCH-DOM-003, ARCH-DOM-009, ARCH-DOM-018
     * Depends-On: missingClassLookupRaisesArgumentError, requiredMemberLookupRaisesOnAbsentMethod */
    @Test void graphAndMemberLookupsExposeConsistentErrors() {
        JavaClasses graph = OracleSupport.graph();
        assertAll(() -> assertThrows(IllegalArgumentException.class, () -> graph.get("missing.Type")),
                () -> assertThrows(IllegalArgumentException.class, () -> graph.get(OrderService.class).getMethod("missing")));
    }
}
