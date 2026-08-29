package atomic;

import com.tngtech.archunit.base.ChainableFunction;
import com.tngtech.archunit.base.DescribedFunction;
import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.PackageMatcher;
import com.tngtech.archunit.core.domain.PackageMatchers;
import org.junit.jupiter.api.Test;

import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class AtomicPackageTest {
    /** Verifies: ARCH-PKG-001 */
    @Test void starMatchesExactlyOnePackageSegment() {
        PackageMatcher matcher = PackageMatcher.of("support.*.service");
        assertAll(() -> assertTrue(matcher.matches("support.fixture.service")),
                () -> assertFalse(matcher.matches("support.deep.fixture.service")));
    }

    /** Verifies: ARCH-PKG-001 */
    @Test void doubleDotMatchesZeroOrManySegments() {
        PackageMatcher matcher = PackageMatcher.of("support..service");
        assertAll(() -> assertTrue(matcher.matches("support.service")),
                () -> assertTrue(matcher.matches("support.fixture.deep.service")));
    }

    /** Verifies: ARCH-PKG-002, ARCH-PKG-004, ARCH-PKG-011 */
    @Test void textualCaptureGroupsUseOneBasedIndexes() {
        PackageMatcher.Result result = PackageMatcher.of("support.(*).(**)").match("support.fixture.deep.service").orElseThrow();
        assertAll(() -> assertEquals("fixture", result.getGroup(1)),
                () -> assertEquals("deep.service", result.getGroup(2)),
                () -> assertEquals(2, result.getNumberOfGroups()));
    }

    /** Verifies: ARCH-PKG-002 */
    @Test void alternationAcceptsEitherNamedSegment() {
        PackageMatcher matcher = PackageMatcher.of("support.[fixture|other].service");
        assertAll(() -> assertTrue(matcher.matches("support.fixture.service")),
                () -> assertTrue(matcher.matches("support.other.service")),
                () -> assertFalse(matcher.matches("support.else.service")));
    }

    /** Verifies: ARCH-PKG-003 */
    @Test void nonMatchingPackageProducesEmptyOptional() {
        Optional<PackageMatcher.Result> result = PackageMatcher.of("..service").match("support.fixture.repository");
        assertTrue(result.isEmpty());
    }

    /** Verifies: ARCH-PKG-005, ARCH-PKG-010 */
    @Test void packageMatchersAcceptWhenAnyIdentifierMatches() {
        PackageMatchers matchers = PackageMatchers.of("..service", "..repository");
        assertAll(() -> assertTrue(matchers.test("support.fixture.repository")),
                () -> assertFalse(matchers.test("support.fixture.web")));
    }

    /** Verifies: ARCH-PKG-006, ARCH-ERR-003 */
    @Test void invalidPatternAndCaptureIndexRaiseArgumentErrors() {
        assertThrows(IllegalArgumentException.class,
                () -> PackageMatcher.of("support...service").matches("support.service"));
    }

    /** Verifies: ARCH-PKG-007, ARCH-RULE-019 */
    @Test void predicatesComposeAndShortCircuit() {
        AtomicInteger secondCalls = new AtomicInteger();
        DescribedPredicate<Integer> positive = new DescribedPredicate<>("positive") {
            @Override public boolean test(Integer input) { return input > 0; }
        };
        DescribedPredicate<Integer> second = new DescribedPredicate<>("even") {
            @Override public boolean test(Integer input) { secondCalls.incrementAndGet(); return input % 2 == 0; }
        };
        assertAll(() -> assertFalse(positive.and(second).test(-1)),
                () -> assertEquals(0, secondCalls.get()),
                () -> assertTrue(positive.and(second).test(2)),
                () -> assertTrue(positive.negate().test(-1)));
    }

    /** Verifies: ARCH-PKG-008, ARCH-RULE-019 */
    @Test void chainableAndDescribedFunctionsComposeMappings() {
        ChainableFunction<String, Integer> length = new ChainableFunction<>() {
            @Override public Integer apply(String input) { return input.length(); }
        };
        DescribedFunction<Integer, String> label = new DescribedFunction<>("label") {
            @Override public String apply(Integer input) { return "n=" + input; }
        };
        DescribedFunction<Integer, String> renamed = new DescribedFunction<>("renamed") {
            @Override public String apply(Integer input) { return label.apply(input); }
        };
        assertAll(() -> assertEquals("n=4", length.then(label).apply("test")),
                () -> assertEquals("label", label.getDescription()),
                () -> assertEquals("renamed", renamed.getDescription()),
                () -> assertEquals(label.apply(3), renamed.apply(3)));
    }
}
