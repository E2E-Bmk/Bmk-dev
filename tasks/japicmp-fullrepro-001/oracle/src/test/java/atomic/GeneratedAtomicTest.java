package atomic;

import japicmp.cmp.JApiCmpArchive;
import japicmp.cmp.JarArchiveComparatorOptions;
import japicmp.config.IgnoreMissingClasses;
import japicmp.exception.JApiCmpException;
import japicmp.filter.Filters;
import japicmp.filter.JavaDocLikeClassFilter;
import japicmp.filter.JavadocLikeBehaviorFilter;
import japicmp.filter.JavadocLikePackageFilter;
import japicmp.model.AccessModifier;
import japicmp.model.JApiCompatibilityChangeType;
import japicmp.model.JApiJavaObjectSerializationCompatibility;
import japicmp.model.JApiSemanticVersionLevel;
import japicmp.versioning.SemanticVersion;
import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtMethod;
import javassist.CtNewMethod;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.lang.reflect.Method;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.*;

class GeneratedAtomicTest {
    private static CtClass type(String name) {
        return new ClassPool(true).makeClass(name);
    }

    private static CtMethod method(CtClass owner, String source) throws Exception {
        CtMethod method = CtNewMethod.make(source, owner);
        owner.addMethod(method);
        return method;
    }

    private static void setStringSequence(Object target, String setterName, List<String> values) throws Exception {
        Method setter = Arrays.stream(target.getClass().getMethods())
            .filter(method -> method.getName().equals(setterName) && method.getParameterCount() == 1)
            .findFirst().orElseThrow(AssertionError::new);
        Class<?> parameter = setter.getParameterTypes()[0];
        Object argument;
        if (parameter == String.class) {
            argument = String.join(File.pathSeparator, values);
        } else if (parameter.isArray() && parameter.getComponentType() == String.class) {
            argument = values.toArray(new String[0]);
        } else if (Collection.class.isAssignableFrom(parameter)) {
            argument = new ArrayList<>(values);
        } else {
            throw new AssertionError("Unsupported public classpath setter shape: " + parameter.getName());
        }
        setter.invoke(target, argument);
    }

    private static List<String> stringSequence(Object target, String getterName) throws Exception {
        Object value = target.getClass().getMethod(getterName).invoke(target);
        if (value instanceof String) {
            String text = (String) value;
            return text.isEmpty() ? Collections.emptyList() : Arrays.asList(text.split(Pattern.quote(File.pathSeparator)));
        }
        if (value instanceof String[]) {
            return Arrays.asList((String[]) value);
        }
        if (value instanceof Iterable<?>) {
            List<String> result = new ArrayList<>();
            for (Object entry : (Iterable<?>) value) {
                result.add(String.valueOf(entry));
            }
            return result;
        }
        throw new AssertionError("Unsupported public classpath getter shape: " + value);
    }

    @SuppressWarnings("unchecked")
    private static void addMissingClassRegex(IgnoreMissingClasses missing, String expression) throws Exception {
        Method getter = missing.getClass().getMethod("getIgnoreMissingClassRegularExpression");
        Object value = getter.invoke(missing);
        if (!(value instanceof Collection<?>)) {
            throw new AssertionError("Missing-class regex projection is not a collection");
        }
        Object entry = expression;
        Type generic = getter.getGenericReturnType();
        if (generic instanceof ParameterizedType) {
            Type element = ((ParameterizedType) generic).getActualTypeArguments()[0];
            if (element == Pattern.class || element.getTypeName().equals(Pattern.class.getName())) {
                entry = Pattern.compile(expression);
            }
        }
        ((Collection<Object>) value).add(entry);
    }

    @SuppressWarnings({"rawtypes", "unchecked"})
    private static Object serializationStatus(String name) throws Exception {
        Method projection = JApiJavaObjectSerializationCompatibility.class
            .getMethod("getJavaObjectSerializationCompatible");
        Class<?> statusType = projection.getReturnType();
        return Enum.valueOf((Class<? extends Enum>) statusType.asSubclass(Enum.class), name);
    }

    private static boolean isSerializationIncompatible(Object status) throws Exception {
        return (Boolean) status.getClass().getMethod("isIncompatible").invoke(status);
    }

    /** Verifies: JCMP-ARCH-001, JCMP-ARCH-002. */
    @Test void atomicFileBackedArchivePreservesFileAndVersion() throws Exception {
        Path path = Files.createTempFile("jcmp-archive-", ".jar");
        JApiCmpArchive archive = new JApiCmpArchive(path.toFile(), "3.4.5-beta");
        assertAll(
            () -> assertEquals(path.toFile(), archive.getFile().orElseThrow(AssertionError::new)),
            () -> assertFalse(archive.getBytes().isPresent()),
            () -> assertEquals("3.4.5-beta", archive.getVersion().getStringVersion())
        );
    }

    /** Verifies: JCMP-ARCH-001, JCMP-ARCH-002. */
    @Test void atomicByteBackedArchivePreservesBytesNameAndVersion() {
        byte[] bytes = new byte[] {1, 7, 9};
        JApiCmpArchive archive = new JApiCmpArchive(bytes, "7.2.1", "memory.jar");
        assertAll(
            () -> assertArrayEquals(bytes, archive.getBytes().orElseThrow(AssertionError::new)),
            () -> assertEquals("memory.jar", archive.getName().orElseThrow(AssertionError::new)),
            () -> assertFalse(archive.getFile().isPresent()),
            () -> assertEquals("7.2.1", archive.getVersion().getStringVersion())
        );
    }

    /** Verifies: JCMP-ARCH-006. */
    @Test void atomicComparatorOptionsExposeDocumentedDefaults() {
        JarArchiveComparatorOptions options = new JarArchiveComparatorOptions();
        assertAll(
            () -> assertEquals(AccessModifier.PROTECTED, options.getAccessModifier()),
            () -> assertEquals(JarArchiveComparatorOptions.ClassPathMode.ONE_COMMON_CLASSPATH, options.getClassPathMode()),
            () -> assertFalse(options.isIncludeSynthetic()),
            () -> assertFalse(options.isNoAnnotations()),
            () -> assertFalse(options.isIncludeClassFileFormatVersion())
        );
    }

    /** Verifies: JCMP-ARCH-007. */
    @Test void atomicComparatorOptionsPreserveSeparateClasspaths() throws Exception {
        JarArchiveComparatorOptions options = new JarArchiveComparatorOptions();
        options.setClassPathMode(JarArchiveComparatorOptions.ClassPathMode.TWO_SEPARATE_CLASSPATHS);
        setStringSequence(options, "setOldClassPath", Arrays.asList("old-a", "old-b"));
        setStringSequence(options, "setNewClassPath", Collections.singletonList("new-a"));
        assertAll(
            () -> assertEquals(Arrays.asList("old-a", "old-b"), stringSequence(options, "getOldClassPath")),
            () -> assertEquals(Collections.singletonList("new-a"), stringSequence(options, "getNewClassPath"))
        );
    }

    /** Verifies: JCMP-ARCH-009. */
    @Test void atomicIgnoreAllMissingClassesAcceptsEveryName() {
        IgnoreMissingClasses missing = new IgnoreMissingClasses();
        missing.setIgnoreAllMissingClasses(true);
        assertTrue(missing.ignoreClass("unavailable.any.Dependency"));
    }

    /** Verifies: JCMP-ARCH-010. */
    @Test void atomicMissingClassRegexAcceptsMatchingName() throws Exception {
        IgnoreMissingClasses missing = new IgnoreMissingClasses();
        addMissingClassRegex(missing, "optional\\..*");
        assertTrue(missing.ignoreClass("optional.library.Type"));
    }

    /** Verifies: JCMP-ARCH-010, JCMP-ARCH-011. */
    @Test void atomicMissingClassRegexRejectsNonMatchingName() throws Exception {
        IgnoreMissingClasses missing = new IgnoreMissingClasses();
        addMissingClassRegex(missing, "optional\\..*");
        assertFalse(missing.ignoreClass("required.library.Type"));
    }

    /** Verifies: JCMP-FILT-001, JCMP-FILT-003. */
    @Test void atomicFiltersWithoutRulesIncludeAClass() {
        Filters filters = new Filters();
        assertTrue(filters.includeClass(type("sample.visible.Widget")));
    }

    /** Verifies: JCMP-FILT-001, JCMP-FILT-003. */
    @Test void atomicClassIncludeRequiresAMatch() {
        Filters filters = new Filters();
        filters.getIncludes().add(new JavaDocLikeClassFilter("sample.visible.Allowed"));
        assertFalse(filters.includeClass(type("sample.visible.Other")));
    }

    /** Verifies: JCMP-FILT-002, JCMP-FILT-003. */
    @Test void atomicClassExclusionWinsOverInclusion() {
        Filters filters = new Filters();
        filters.getIncludes().add(new JavaDocLikeClassFilter("sample.visible.*"));
        filters.getExcludes().add(new JavaDocLikeClassFilter("sample.visible.Blocked"));
        assertFalse(filters.includeClass(type("sample.visible.Blocked")));
    }

    /** Verifies: JCMP-FILT-005. */
    @Test void atomicPackageFilterIncludesSubpackagesByDefault() {
        JavadocLikePackageFilter filter = new JavadocLikePackageFilter("sample.api", false);
        assertTrue(filter.matches(type("sample.api.deep.Widget")));
    }

    /** Verifies: JCMP-FILT-005. */
    @Test void atomicExclusivePackageFilterRejectsSubpackages() {
        JavadocLikePackageFilter filter = new JavadocLikePackageFilter("sample.api", true);
        assertAll(
            () -> assertTrue(filter.matches(type("sample.api.Widget"))),
            () -> assertFalse(filter.matches(type("sample.api.deep.Widget")))
        );
    }

    /** Verifies: JCMP-FILT-007. */
    @Test void atomicBehaviorFilterMatchesExactErasedSignature() throws Exception {
        CtClass owner = type("sample.api.Service");
        CtMethod method = method(owner, "public long convert(java.lang.String value, int radix) { return 0L; }");
        assertTrue(new JavadocLikeBehaviorFilter("sample.api.Service#convert(java.lang.String,int)").matches(method));
    }

    /** Verifies: JCMP-FILT-007. */
    @Test void atomicBehaviorFilterWildcardMatchesNameAndParameter() throws Exception {
        CtClass owner = type("sample.api.Service");
        CtMethod method = method(owner, "public void convertValue(java.lang.String value) { }");
        assertTrue(new JavadocLikeBehaviorFilter("sample.api.Service#convert*(java.lang.*)").matches(method));
    }

    /** Verifies: JCMP-FILT-009, JCMP-ERR-004. */
    @Test void atomicInvalidBehaviorFilterReportsCliReason() {
        JApiCmpException error = assertThrows(JApiCmpException.class,
            () -> new JavadocLikeBehaviorFilter("sample.api.Service#convert"));
        assertEquals(JApiCmpException.Reason.CliError, error.getReason());
    }

    /** Verifies: JCMP-MODEL-017. */
    @Test void atomicMajorCompatibilityFamilyHasMajorProjections() {
        JApiCompatibilityChangeType type = JApiCompatibilityChangeType.METHOD_REMOVED;
        assertAll(
            () -> assertFalse(type.isBinaryCompatible()),
            () -> assertFalse(type.isSourceCompatible()),
            () -> assertEquals(JApiSemanticVersionLevel.MAJOR, type.getSemanticVersionLevel())
        );
    }

    /** Verifies: JCMP-MODEL-017. */
    @Test void atomicMinorCompatibilityFamilySeparatesBinaryAndSource() {
        JApiCompatibilityChangeType type = JApiCompatibilityChangeType.METHOD_PARAMETER_GENERICS_CHANGED;
        assertAll(
            () -> assertTrue(type.isBinaryCompatible()),
            () -> assertFalse(type.isSourceCompatible()),
            () -> assertEquals(JApiSemanticVersionLevel.MINOR, type.getSemanticVersionLevel())
        );
    }

    /** Verifies: JCMP-MODEL-020. */
    @Test void atomicSerializationStatusesExposeCompatibilityPredicate() throws Exception {
        assertAll(
            () -> assertFalse(isSerializationIncompatible(serializationStatus("NOT_SERIALIZABLE"))),
            () -> assertFalse(isSerializationIncompatible(serializationStatus("SERIALIZABLE_COMPATIBLE"))),
            () -> assertTrue(isSerializationIncompatible(serializationStatus("SERIALIZABLE_INCOMPATIBLE_FIELD_REMOVED")))
        );
    }

    /** Verifies: JCMP-SEM-004. */
    @Test void atomicSemanticComparisonDirectionDoesNotChangeRank() {
        SemanticVersion lower = new SemanticVersion(1, 2, 3);
        SemanticVersion higher = new SemanticVersion(1, 7, 0);
        assertEquals(lower.computeChangeType(higher), higher.computeChangeType(lower));
        assertEquals(SemanticVersion.ChangeType.MINOR, lower.computeChangeType(higher).orElseThrow(AssertionError::new));
    }
}
