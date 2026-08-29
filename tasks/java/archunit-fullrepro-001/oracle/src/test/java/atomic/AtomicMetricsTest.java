package atomic;

import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.library.metrics.ArchitectureMetrics;
import com.tngtech.archunit.library.metrics.LakosMetrics;
import com.tngtech.archunit.library.metrics.MetricsComponent;
import com.tngtech.archunit.library.metrics.MetricsComponents;
import org.junit.jupiter.api.Test;
import support.OracleSupport;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class AtomicMetricsTest {
        /** Verifies: ARCH-MET-001, ARCH-MET-002, ARCH-MET-009 */
    @Test void groupedComponentsSupportOptionalLookup() {
        MetricsComponents<String> components = MetricsComponents.from(List.of("aa", "ab", "b"), s -> s.substring(0, 1));
        assertAll(() -> assertEquals(2, components.size()),
                () -> assertEquals(2, components.tryGetComponent("a").orElseThrow().size()),
                () -> assertTrue(components.tryGetComponent("missing").isEmpty()));
    }

    /** Verifies: ARCH-MET-003, ARCH-MET-004, ARCH-MET-011 */
    @Test void lakosMetricsExposeFiniteGraphRatios() {
        LakosMetrics metrics = ArchitectureMetrics.lakosMetrics(MetricsComponents.fromClasses(OracleSupport.graph()));
        assertAll(() -> assertTrue(metrics.getCumulativeComponentDependency() >= OracleSupport.graph().size()),
                () -> assertTrue(Double.isFinite(metrics.getAverageComponentDependency())),
                () -> assertTrue(Double.isFinite(metrics.getRelativeAverageComponentDependency())),
                () -> assertTrue(Double.isFinite(metrics.getNormalizedCumulativeComponentDependency())));
    }

    /** Verifies: ARCH-MET-001, ARCH-MET-002, ARCH-MET-003, ARCH-MET-007, ARCH-MET-011 */
    @Test void metricComponentsAndLakosUseNamedClasses() {
        MetricsComponents<JavaClass> components = MetricsComponents.fromClasses(OracleSupport.graph());
        String independent = support.fixture.isolated.Independent.class.getName();
        LakosMetrics metrics = ArchitectureMetrics.lakosMetrics(components);
        assertAll(() -> assertTrue(components.tryGetComponent(independent).isPresent()),
                () -> assertTrue(metrics.getCumulativeComponentDependency() >= components.size()),
                () -> assertTrue(Double.isFinite(metrics.getAverageComponentDependency())));
    }
}
