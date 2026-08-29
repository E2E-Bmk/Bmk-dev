package atomic;

import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.Dependency;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.domain.JavaField;
import com.tngtech.archunit.core.domain.JavaMethod;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.Test;
import support.OracleSupport;
import support.fixture.api.PublicApi;
import support.fixture.isolated.Independent;
import support.fixture.repository.Repository;
import support.fixture.service.BaseService;
import support.fixture.service.OrderService;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class AtomicImportAndDomainTest {
    /** Verifies: ARCH-IMP-001, ARCH-DOM-002 */
    @Test void importsOneReflectedClass() {
        JavaClass imported = new ClassFileImporter().importClasses(Independent.class).get(Independent.class);
        assertEquals(Independent.class.getName(), imported.getName());
    }

    /** Verifies: ARCH-IMP-001, ARCH-IMP-002 */
    @Test void importsUnionOfReflectedClasses() {
        JavaClasses classes = new ClassFileImporter().importClasses(PublicApi.class, Independent.class);
        assertAll(() -> assertTrue(classes.contain(PublicApi.class)), () -> assertTrue(classes.contain(Independent.class)));
    }

    /** Verifies: ARCH-IMP-003 */
    @Test void importOptionCanRejectEveryLocation() {
        ImportOption rejectAll = location -> false;
        JavaClasses classes = new ClassFileImporter().withImportOption(rejectAll).importClasses(PublicApi.class);
        assertEquals(0, classes.size());
    }

    /** Verifies: ARCH-IMP-001, ARCH-IMP-002 */
    @Test void importsSeveralClassSourcesTogether() {
        JavaClasses classes = new ClassFileImporter().importClasses(PublicApi.class, Independent.class);
        assertAll(() -> assertTrue(classes.contain(PublicApi.class)), () -> assertTrue(classes.contain(Independent.class)));
    }

    /** Verifies: ARCH-DOM-001, ARCH-DOM-002, ARCH-RULE-019 */
    @Test void collectionFiltersWithDescribedPredicate() {
        JavaClasses graph = OracleSupport.graph();
        DescribedPredicate<JavaClass> service = new DescribedPredicate<>("service classes") {
            @Override public boolean test(JavaClass input) { return com.tngtech.archunit.core.domain.PackageMatcher.of("..service").matches(input.getPackageName()); }
        };
        JavaClasses selected = graph.that(service);
        assertEquals(Set.of(BaseService.class.getName(), OrderService.class.getName()),
                selected.stream().map(JavaClass::getName).collect(java.util.stream.Collectors.toSet()));
    }

    /** Verifies: ARCH-DOM-002 */
    @Test void containmentWorksByClassAndName() {
        JavaClasses graph = OracleSupport.graph();
        assertAll(() -> assertTrue(graph.contain(OrderService.class)),
                () -> assertTrue(graph.contain(OrderService.class.getName())));
    }

    /** Verifies: ARCH-DOM-003, ARCH-ERR-001 */
    @Test void missingClassLookupRaisesArgumentError() {
        JavaClasses graph = OracleSupport.graph();
        assertThrows(IllegalArgumentException.class, () -> graph.get("missing.Type"));
    }

    /** Verifies: ARCH-DOM-004 */
    @Test void classExposesStableNameViews() {
        JavaClass type = OracleSupport.graph().get(OrderService.class);
        assertAll(() -> assertEquals(OrderService.class.getName(), type.getName()),
                () -> assertEquals("OrderService", type.getSimpleName()),
                () -> assertEquals("support.fixture.service", type.getPackageName()));
    }

    /** Verifies: ARCH-DOM-005 */
    @Test void packageContainsItsDirectClasses() {
        JavaClass type = OracleSupport.graph().get(OrderService.class);
        assertTrue(type.getPackage().getClasses().contains(type));
    }

    /** Verifies: ARCH-DOM-007, ARCH-DOM-008, ARCH-DOM-018 */
    @Test void declaredFieldAndMethodLookupsResolve() {
        JavaClass type = OracleSupport.graph().get(OrderService.class);
        JavaField field = type.getField("repository");
        JavaMethod method = type.getMethod("load");
        assertAll(() -> assertEquals(type, field.getOwner()), () -> assertEquals(type, method.getOwner()));
    }

    /** Verifies: ARCH-DOM-009, ARCH-ERR-002, ARCH-DOM-018 */
    @Test void requiredMemberLookupRaisesOnAbsentMethod() {
        JavaClass type = OracleSupport.graph().get(OrderService.class);
        assertAll(() -> assertFalse(type.getMethods().stream().map(JavaMethod::getName).collect(java.util.stream.Collectors.toSet()).contains("absent")),
                () -> assertThrows(IllegalArgumentException.class, () -> type.getMethod("absent")));
    }

    /** Verifies: ARCH-DOM-016 */
    @Test void dependencyViewExposesServiceRelations() {
        JavaClass type = OracleSupport.graph().get(OrderService.class);
        Set<String> dependencyTargets = type.getDirectDependenciesFromSelf().stream()
                .map(Dependency::getTargetClass).map(JavaClass::getName).collect(java.util.stream.Collectors.toSet());
        assertTrue(dependencyTargets.contains(Repository.class.getName()));
    }
}
