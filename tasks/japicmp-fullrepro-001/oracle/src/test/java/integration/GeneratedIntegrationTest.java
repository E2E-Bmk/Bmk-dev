package integration;

import japicmp.cmp.JApiCmpArchive;
import japicmp.cmp.JarArchiveComparator;
import japicmp.cmp.JarArchiveComparatorOptions;
import japicmp.exception.JApiCmpException;
import japicmp.filter.JavaDocLikeClassFilter;
import japicmp.model.AccessModifier;
import japicmp.model.JApiChangeStatus;
import japicmp.model.JApiClass;
import japicmp.model.JApiCompatibilityChangeType;
import japicmp.model.JApiField;
import japicmp.model.JApiMethod;
import japicmp.model.JApiSemanticVersionLevel;
import japicmp.output.html.HtmlOutputGenerator;
import japicmp.output.html.HtmlOutputGeneratorOptions;
import japicmp.output.markdown.MarkdownOutputGenerator;
import japicmp.output.semver.SemverOut;
import japicmp.output.stdout.StdoutOutputGenerator;
import japicmp.output.xml.XmlOutput;
import japicmp.output.xml.XmlOutputGenerator;
import japicmp.output.xml.XmlOutputGeneratorOptions;
import japicmp.config.Options;
import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.CtMethod;
import javassist.CtNewConstructor;
import javassist.CtNewMethod;
import javassist.Modifier;
import javassist.bytecode.AnnotationsAttribute;
import javassist.bytecode.SyntheticAttribute;
import javassist.bytecode.annotation.Annotation;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;

import static org.junit.jupiter.api.Assertions.*;

class GeneratedIntegrationTest {
    @FunctionalInterface
    private interface ArchiveBuilder {
        List<CtClass> build(ClassPool pool) throws Exception;
    }

    private static final class Scenario {
        final JApiCmpArchive oldArchive;
        final JApiCmpArchive newArchive;

        Scenario(ArchiveBuilder oldBuilder, ArchiveBuilder newBuilder) throws Exception {
            this(oldBuilder, "1.0.0", newBuilder, "2.0.0");
        }

        Scenario(ArchiveBuilder oldBuilder, String oldVersion, ArchiveBuilder newBuilder, String newVersion) throws Exception {
            this.oldArchive = archive("old-api.jar", oldVersion, oldBuilder);
            this.newArchive = archive("new-api.jar", newVersion, newBuilder);
        }
    }

    private static JApiCmpArchive archive(String name, String version, ArchiveBuilder builder) throws Exception {
        ClassPool pool = new ClassPool(true);
        List<CtClass> classes = builder.build(pool);
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (JarOutputStream jar = new JarOutputStream(bytes)) {
            for (CtClass type : classes) {
                JarEntry entry = new JarEntry(type.getName().replace('.', '/') + ".class");
                jar.putNextEntry(entry);
                jar.write(type.toBytecode());
                jar.closeEntry();
            }
        }
        return new JApiCmpArchive(bytes.toByteArray(), version, name);
    }

    private static CtClass publicClass(ClassPool pool, String name) {
        CtClass type = pool.makeClass(name);
        type.setModifiers(Modifier.PUBLIC);
        return type;
    }

    private static CtClass visibleClass(ClassPool pool, String name, int modifier) {
        CtClass type = pool.makeClass(name);
        type.setModifiers(modifier);
        return type;
    }

    private static CtMethod addMethod(CtClass type, String source) throws Exception {
        CtMethod method = CtNewMethod.make(source, type);
        type.addMethod(method);
        return method;
    }

    private static CtField addField(CtClass type, String source) throws Exception {
        CtField field = CtField.make(source, type);
        type.addField(field);
        return field;
    }

    private static void addDefaultConstructor(CtClass type) throws Exception {
        type.addConstructor(CtNewConstructor.defaultConstructor(type));
    }

    private static void addDeprecated(CtClass type) {
        AnnotationsAttribute attribute = new AnnotationsAttribute(type.getClassFile().getConstPool(), AnnotationsAttribute.visibleTag);
        attribute.addAnnotation(new Annotation(Deprecated.class.getName(), type.getClassFile().getConstPool()));
        type.getClassFile().addAttribute(attribute);
    }

    private static void addSynthetic(CtClass type) {
        type.setModifiers(type.getModifiers() | 0x1000);
        type.getClassFile().addAttribute(new SyntheticAttribute(type.getClassFile().getConstPool()));
    }

    private static void addSynthetic(CtMethod method) {
        method.setModifiers(method.getModifiers() | 0x1000);
        method.getMethodInfo().addAttribute(new SyntheticAttribute(method.getMethodInfo().getConstPool()));
    }

    private static List<JApiClass> compare(Scenario scenario) {
        return compare(scenario, new JarArchiveComparatorOptions());
    }

    private static List<JApiClass> compare(Scenario scenario, JarArchiveComparatorOptions options) {
        return new JarArchiveComparator(options).compare(scenario.oldArchive, scenario.newArchive);
    }

    private static Options reportOptions(Scenario scenario) {
        Options options = Options.newDefault();
        options.setOldArchives(Collections.singletonList(scenario.oldArchive));
        options.setNewArchives(Collections.singletonList(scenario.newArchive));
        return options;
    }

    private static void addIncludeArgument(Options options, String argument) throws Exception {
        Method selected = Arrays.stream(options.getClass().getMethods())
            .filter(method -> method.getName().equals("addIncludeFromArgument"))
            .filter(method -> method.getParameterCount() == 1 || method.getParameterCount() == 2)
            .filter(method -> method.getParameterTypes()[0] == String.class || method.getParameterTypes()[0] == Optional.class)
            .sorted((left, right) -> Integer.compare(right.getParameterCount(), left.getParameterCount()))
            .findFirst().orElseThrow(AssertionError::new);
        Object first = selected.getParameterTypes()[0] == String.class ? argument : Optional.of(argument);
        if (selected.getParameterCount() == 2) {
            selected.invoke(options, first, false);
        } else {
            selected.invoke(options, first);
        }
    }

    private static String sideProjection(Object projection, String side) throws Exception {
        for (Method method : projection.getClass().getMethods()) {
            String name = method.getName().toLowerCase();
            if (method.getParameterCount() != 0 || !name.startsWith("get") || !name.contains(side)) {
                continue;
            }
            Object value = method.invoke(projection);
            if (value instanceof Optional<?>) {
                value = ((Optional<?>) value).orElse(null);
            }
            if (value instanceof String) {
                return (String) value;
            }
        }
        throw new AssertionError("No public " + side + " scalar projection");
    }

    private static Object xmlRoot(XmlOutput output) throws Exception {
        for (Method method : output.getClass().getMethods()) {
            if (method.getParameterCount() == 0
                && method.getReturnType().getSimpleName().equals("JApiCmpXmlRoot")) {
                return method.invoke(output);
            }
        }
        throw new AssertionError("XmlOutput exposes no JApiCmpXmlRoot projection");
    }

    private static List<String> scalarProjections(Object root) throws Exception {
        List<String> values = new ArrayList<>();
        for (Method method : root.getClass().getMethods()) {
            if (method.getParameterCount() != 0 || method.getDeclaringClass() == Object.class) {
                continue;
            }
            Object value = method.invoke(root);
            if (value instanceof Optional<?>) {
                value = ((Optional<?>) value).orElse(null);
            }
            if (value instanceof String || value instanceof File || value instanceof Path || value instanceof Enum<?>) {
                values.add(String.valueOf(value));
            }
        }
        return values;
    }

    private static List<JApiClass> xmlClasses(Object root) throws Exception {
        for (Method method : root.getClass().getMethods()) {
            if (method.getParameterCount() != 0 || !Iterable.class.isAssignableFrom(method.getReturnType())) {
                continue;
            }
            Object value = method.invoke(root);
            if (!(value instanceof Iterable<?>)) {
                continue;
            }
            List<JApiClass> classes = new ArrayList<>();
            boolean allClasses = true;
            for (Object item : (Iterable<?>) value) {
                if (!(item instanceof JApiClass)) {
                    allClasses = false;
                    break;
                }
                classes.add((JApiClass) item);
            }
            if (allClasses) {
                return classes;
            }
        }
        throw new AssertionError("JApiCmpXmlRoot exposes no class collection");
    }

    private static JApiClass classNamed(List<JApiClass> graph, String name) {
        return graph.stream().filter(type -> type.getFullyQualifiedName().equals(name)).findFirst().orElseThrow(AssertionError::new);
    }

    private static JApiMethod methodNamed(JApiClass type, String name) {
        return type.getMethods().stream().filter(method -> method.getName().equals(name)).findFirst().orElseThrow(AssertionError::new);
    }

    private static JApiField fieldNamed(JApiClass type, String name) {
        return type.getFields().stream().filter(field -> field.getName().equals(name)).findFirst().orElseThrow(AssertionError::new);
    }

    private static Path materialize(JApiCmpArchive archive) throws Exception {
        Path path = Files.createTempFile("jcmp-cli-", ".jar");
        Files.write(path, archive.getBytes().orElseThrow(AssertionError::new));
        return path;
    }

    private static final class ProcessResult {
        final int exit;
        final String out;
        final String err;

        ProcessResult(int exit, String out, String err) {
            this.exit = exit;
            this.out = out;
            this.err = err;
        }
    }

    private static ProcessResult cli(String... arguments) throws Exception {
        List<String> command = new ArrayList<>();
        command.add(new File(System.getProperty("java.home"), "bin/java").getAbsolutePath());
        String childAgent = System.getProperty("japicmp.oracle.childAgent");
        if (childAgent != null && !childAgent.isEmpty()) {
            command.add("-javaagent:" + childAgent);
        }
        command.add("-cp");
        command.add(System.getProperty("java.class.path"));
        command.add("japicmp.JApiCmp");
        command.addAll(Arrays.asList(arguments));
        Path stdout = Files.createTempFile("jcmp-cli-out-", ".txt");
        Path stderr = Files.createTempFile("jcmp-cli-err-", ".txt");
        Process process = new ProcessBuilder(command).redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        assertTrue(process.waitFor(30, TimeUnit.SECONDS));
        String out = new String(Files.readAllBytes(stdout), StandardCharsets.UTF_8);
        String err = new String(Files.readAllBytes(stderr), StandardCharsets.UTF_8);
        return new ProcessResult(process.exitValue(), out, err);
    }

    private static String readAll(InputStream input) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        int read;
        while ((read = input.read(buffer)) >= 0) {
            output.write(buffer, 0, read);
        }
        return new String(output.toByteArray(), StandardCharsets.UTF_8);
    }

    /** Verifies: JCMP-ARCH-003, JCMP-MODEL-004; Seam: byte archive -> comparator -> model graph; CVI-1; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion, atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationNewClassAppearsAsNewModelNode() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Added")));
        JApiClass type = classNamed(compare(scenario), "sample.api.Added");
        assertEquals(JApiChangeStatus.NEW, type.getChangeStatus());
    }

    /** Verifies: JCMP-MODEL-004, JCMP-MODEL-017; Seam: byte archive -> comparator -> compatibility graph; CVI-2, CVI-5; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationRemovedClassIsBinaryAndSourceIncompatible() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.singletonList(publicClass(pool, "sample.api.Removed")), pool -> Collections.emptyList());
        JApiClass type = classNamed(compare(scenario), "sample.api.Removed");
        assertAll(() -> assertEquals(JApiChangeStatus.REMOVED, type.getChangeStatus()), () -> assertFalse(type.isBinaryCompatible()), () -> assertFalse(type.isSourceCompatible()));
    }

    /** Verifies: JCMP-MODEL-004, JCMP-MODEL-016; Seam: equivalent archives -> comparator -> model graph; CVI-1; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationEquivalentClassesRemainUnchangedAndCompatible() throws Exception {
        ArchiveBuilder builder = pool -> Collections.singletonList(publicClass(pool, "sample.api.Stable"));
        Scenario scenario = new Scenario(builder, builder);
        JApiClass type = classNamed(compare(scenario), "sample.api.Stable");
        assertAll(() -> assertEquals(JApiChangeStatus.UNCHANGED, type.getChangeStatus()), () -> assertTrue(type.isBinaryCompatible()), () -> assertTrue(type.isSourceCompatible()));
    }

    /** Verifies: JCMP-MODEL-004, JCMP-MODEL-011; Seam: class bytecode -> comparator -> method model; CVI-1; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion. */
    @Test void integrationAddedMethodIsAChildNewNode() throws Exception {
        Scenario scenario = new Scenario(
            pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")),
            pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public int size() { return 1; }"); return Collections.singletonList(type); });
        JApiClass type = classNamed(compare(scenario), "sample.api.Service");
        assertEquals(JApiChangeStatus.NEW, methodNamed(type, "size").getChangeStatus());
    }

    /** Verifies: JCMP-MODEL-014, JCMP-MODEL-015; Seam: method removal -> class aggregation -> model; CVI-2, CVI-5; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationRemovedMethodMakesOwningClassIncompatible() throws Exception {
        Scenario scenario = new Scenario(
            pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); },
            pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        JApiClass type = classNamed(compare(scenario), "sample.api.Service");
        JApiMethod method = methodNamed(type, "run");
        assertAll(() -> assertEquals(JApiChangeStatus.REMOVED, method.getChangeStatus()), () -> assertFalse(method.isBinaryCompatible()), () -> assertFalse(type.isBinaryCompatible()), () -> assertTrue(type.getCompatibilityChanges().isEmpty()));
    }

    /** Verifies: JCMP-MODEL-011, JCMP-MODEL-012; Seam: method pairing -> return projection -> compatibility; CVI-2; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationReturnTypeChangePairsOneMethodAndMarksItModified() throws Exception {
        Scenario scenario = new Scenario(
            pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public int value() { return 1; }"); return Collections.singletonList(type); },
            pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public long value() { return 1L; }"); return Collections.singletonList(type); });
        JApiMethod method = methodNamed(classNamed(compare(scenario), "sample.api.Service"), "value");
        assertAll(() -> assertEquals(JApiChangeStatus.MODIFIED, method.getChangeStatus()), () -> assertEquals(JApiChangeStatus.MODIFIED, method.getReturnType().getChangeStatus()), () -> assertEquals("int", sideProjection(method.getReturnType(), "old")), () -> assertEquals("long", sideProjection(method.getReturnType(), "new")));
    }

    /** Verifies: JCMP-MODEL-003, JCMP-MODEL-004; Seam: field bytecode -> comparator -> field model; CVI-1; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationAddedFieldAppearsAsNewChild() throws Exception {
        Scenario scenario = new Scenario(
            pool -> Collections.singletonList(publicClass(pool, "sample.api.Record")),
            pool -> { CtClass type = publicClass(pool, "sample.api.Record"); addField(type, "public int count;"); return Collections.singletonList(type); });
        assertEquals(JApiChangeStatus.NEW, fieldNamed(classNamed(compare(scenario), "sample.api.Record"), "count").getChangeStatus());
    }

    /** Verifies: JCMP-MODEL-014, JCMP-MODEL-015; Seam: field removal -> compatibility aggregation -> model; CVI-2, CVI-5; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationRemovedFieldMakesClassBinaryIncompatible() throws Exception {
        Scenario scenario = new Scenario(
            pool -> { CtClass type = publicClass(pool, "sample.api.Record"); addField(type, "public int count;"); return Collections.singletonList(type); },
            pool -> Collections.singletonList(publicClass(pool, "sample.api.Record")));
        JApiClass type = classNamed(compare(scenario), "sample.api.Record");
        assertAll(() -> assertFalse(fieldNamed(type, "count").isBinaryCompatible()), () -> assertFalse(type.isBinaryCompatible()));
    }

    /** Verifies: JCMP-MODEL-006, JCMP-MODEL-008; Seam: paired field -> type projection -> class graph; CVI-2; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationFieldTypeChangePreservesBothTypes() throws Exception {
        Scenario scenario = new Scenario(
            pool -> { CtClass type = publicClass(pool, "sample.api.Record"); addField(type, "public int value;"); return Collections.singletonList(type); },
            pool -> { CtClass type = publicClass(pool, "sample.api.Record"); addField(type, "public long value;"); return Collections.singletonList(type); });
        JApiField field = fieldNamed(classNamed(compare(scenario), "sample.api.Record"), "value");
        assertAll(() -> assertEquals(JApiChangeStatus.MODIFIED, field.getType().getChangeStatus()), () -> assertEquals("int", sideProjection(field.getType(), "old")), () -> assertEquals("long", sideProjection(field.getType(), "new")));
    }

    /** Verifies: JCMP-MODEL-005, JCMP-MODEL-016; Seam: inheritance bytecode -> comparator -> superclass projection; CVI-1; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationAddedSuperclassIsVisibleAndCompatible() throws Exception {
        Scenario scenario = new Scenario(
            pool -> Collections.singletonList(publicClass(pool, "sample.api.Child")),
            pool -> { CtClass parent = publicClass(pool, "sample.api.Parent"); CtClass child = publicClass(pool, "sample.api.Child"); child.setSuperclass(parent); return Arrays.asList(parent, child); });
        List<JApiClass> graph = compare(scenario);
        JApiClass child = classNamed(graph, "sample.api.Child");
        assertAll(() -> assertEquals(JApiChangeStatus.MODIFIED, child.getSuperclass().getChangeStatus()), () -> assertEquals("sample.api.Parent", sideProjection(child.getSuperclass(), "new")), () -> assertEquals("sample.api.Parent", classNamed(graph, "sample.api.Parent").getFullyQualifiedName()), () -> assertTrue(child.isBinaryCompatible()));
    }

    /** Verifies: JCMP-MODEL-005, JCMP-MODEL-016; Seam: interface bytecode -> comparator -> interface projection; CVI-1; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationAddedInterfaceIsVisibleAndCompatible() throws Exception {
        Scenario scenario = new Scenario(
            pool -> Collections.singletonList(publicClass(pool, "sample.api.Child")),
            pool -> { CtClass contract = pool.makeInterface("sample.api.Contract"); contract.setModifiers(Modifier.PUBLIC | Modifier.INTERFACE | Modifier.ABSTRACT); CtClass child = publicClass(pool, "sample.api.Child"); child.setInterfaces(new CtClass[] {contract}); return Arrays.asList(contract, child); });
        JApiClass child = classNamed(compare(scenario), "sample.api.Child");
        assertAll(() -> assertEquals("sample.api.Contract", child.getInterfaces().get(0).getFullyQualifiedName()), () -> assertEquals(JApiChangeStatus.NEW, child.getInterfaces().get(0).getChangeStatus()), () -> assertTrue(child.isBinaryCompatible()));
    }

    /** Verifies: JCMP-INV-006, JCMP-ARCH-006; Seam: access option -> comparator selection -> graph; CVI-6; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationAccessThresholdChangesClassMembership() throws Exception {
        ArchiveBuilder builder = pool -> Arrays.asList(visibleClass(pool, "sample.api.PublicType", Modifier.PUBLIC), visibleClass(pool, "sample.api.ProtectedType", Modifier.PROTECTED));
        Scenario scenario = new Scenario(builder, builder);
        JarArchiveComparatorOptions publicOnly = new JarArchiveComparatorOptions();
        publicOnly.setAccessModifier(AccessModifier.PUBLIC);
        JarArchiveComparatorOptions protectedToo = new JarArchiveComparatorOptions();
        protectedToo.setAccessModifier(AccessModifier.PROTECTED);
        assertAll(() -> assertEquals(1, compare(scenario, publicOnly).size()), () -> assertEquals(2, compare(scenario, protectedToo).size()));
    }

    /** Verifies: JCMP-FILT-003, JCMP-STATE-002, JCMP-INV-003; Seam: include filter -> comparator selection -> graph; CVI-3; Depends-On: atomicClassIncludeRequiresAMatch. */
    @Test void integrationClassIncludeFilterRestrictsGraphMembership() throws Exception {
        ArchiveBuilder builder = pool -> Arrays.asList(publicClass(pool, "sample.api.Allowed"), publicClass(pool, "sample.api.Other"));
        Scenario scenario = new Scenario(builder, builder);
        JarArchiveComparatorOptions options = new JarArchiveComparatorOptions();
        options.getFilters().getIncludes().add(new JavaDocLikeClassFilter("sample.api.Allowed"));
        List<JApiClass> graph = compare(scenario, options);
        assertAll(() -> assertEquals(1, graph.size()), () -> assertEquals("sample.api.Allowed", graph.get(0).getFullyQualifiedName()));
    }

    /** Verifies: JCMP-FILT-002, JCMP-STATE-002, JCMP-INV-003; Seam: exclusion precedence -> comparator selection -> graph; CVI-3; Depends-On: atomicClassExclusionWinsOverInclusion. */
    @Test void integrationExclusionFilterWinsInComparatorGraph() throws Exception {
        ArchiveBuilder builder = pool -> Arrays.asList(publicClass(pool, "sample.api.Allowed"), publicClass(pool, "sample.api.Blocked"));
        Scenario scenario = new Scenario(builder, builder);
        JarArchiveComparatorOptions options = new JarArchiveComparatorOptions();
        options.getFilters().getIncludes().add(new JavaDocLikeClassFilter("sample.api.*"));
        options.getFilters().getExcludes().add(new JavaDocLikeClassFilter("sample.api.Blocked"));
        assertEquals(Collections.singletonList("sample.api.Allowed"), Collections.singletonList(compare(scenario, options).get(0).getFullyQualifiedName()));
    }

    /** Verifies: JCMP-FILT-013, JCMP-INV-003; Seam: option argument builder -> comparator filters -> class/member selection; CVI-3; Depends-On: atomicClassIncludeRequiresAMatch, atomicBehaviorFilterMatchesExactErasedSignature. */
    @Test void integrationOptionsArgumentBuildsBehavioralFilters() throws Exception {
        Options options = Options.newDefault();
        addIncludeArgument(options, "sample.api.Widget;sample.api.Widget#field;sample.api.Widget#run()");
        japicmp.filter.Filters filters = JarArchiveComparatorOptions.of(options).getFilters();
        CtClass widget = publicClass(new ClassPool(true), "sample.api.Widget");
        CtField field = addField(widget, "public int field;");
        CtMethod method = addMethod(widget, "public void run() { }");
        assertAll(
            () -> assertTrue(filters.includeClass(widget)),
            () -> assertTrue(filters.includeField(field)),
            () -> assertTrue(filters.includeBehavior(method))
        );
    }

    /** Verifies: JCMP-ARCH-004, JCMP-WF-001; Seam: multiple archive classes -> comparator ordering -> graph; CVI-1; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion. */
    @Test void integrationComparatorSortsClassesCaseInsensitively() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Arrays.asList(publicClass(pool, "sample.api.zeta"), publicClass(pool, "sample.api.Alpha"), publicClass(pool, "sample.api.beta")));
        List<JApiClass> graph = compare(scenario);
        assertEquals(Arrays.asList("sample.api.Alpha", "sample.api.beta", "sample.api.zeta"), Arrays.asList(graph.get(0).getFullyQualifiedName(), graph.get(1).getFullyQualifiedName(), graph.get(2).getFullyQualifiedName()));
    }

    /** Verifies: JCMP-RPT-004, JCMP-RPT-005, JCMP-INV-001; Seam: comparator graph -> plain-text generator -> report; CVI-1; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion. */
    @Test void integrationStdoutProjectionCarriesNewClassIdentityAndMarker() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Added")));
        String text = new StdoutOutputGenerator(reportOptions(scenario), compare(scenario)).generate();
        assertAll(() -> assertTrue(text.startsWith(reportOptions(scenario).getDifferenceDescription())), () -> assertTrue(text.contains("sample.api.Added")), () -> assertTrue(text.contains("+++")));
    }

    /** Verifies: JCMP-RPT-005, JCMP-INV-002, JCMP-INV-005; Seam: incompatible descendant -> class aggregation -> plain-text report; CVI-2, CVI-5; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationStdoutProjectionCarriesRemovedMethodIncompatibility() throws Exception {
        Scenario scenario = new Scenario(pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); }, pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        String text = new StdoutOutputGenerator(reportOptions(scenario), compare(scenario)).generate();
        assertAll(() -> assertTrue(text.contains("sample.api.Service")), () -> assertTrue(text.contains("run")), () -> assertTrue(text.contains("---!")));
    }

    /** Verifies: JCMP-WF-004, JCMP-RPT-006; Seam: output filtering -> empty retained graph -> plain-text report; CVI-3; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationOnlyModifiedProjectionReportsNoChangesForStableGraph() throws Exception {
        ArchiveBuilder builder = pool -> Collections.singletonList(publicClass(pool, "sample.api.Stable"));
        Scenario scenario = new Scenario(builder, builder);
        Options options = reportOptions(scenario);
        options.setOutputOnlyModifications(true);
        assertTrue(new StdoutOutputGenerator(options, compare(scenario)).generate().contains("No changes."));
    }

    /** Verifies: JCMP-SEM-007, JCMP-INV-004, JCMP-INV-005; Seam: incompatible graph -> semantic reducer -> recommendation; CVI-2, CVI-4, CVI-5; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationSemverRecommendsMajorForRemovedPublicMethod() throws Exception {
        Scenario scenario = new Scenario(pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); }, pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        assertEquals("1.0.0", new SemverOut(reportOptions(scenario), compare(scenario)).generate());
    }

    /** Verifies: JCMP-SEM-007, JCMP-MODEL-017; Seam: compatible addition graph -> semantic reducer -> recommendation; CVI-4; Depends-On: atomicMinorCompatibilityFamilySeparatesBinaryAndSource. */
    @Test void integrationSemverRecommendsPatchForAddedPublicMethod() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")), pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); });
        assertEquals("0.0.1", new SemverOut(reportOptions(scenario), compare(scenario)).generate());
    }

    /** Verifies: JCMP-RPT-014, JCMP-RPT-017, JCMP-INV-001; Seam: comparator graph -> Markdown generator -> report; CVI-1; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion. */
    @Test void integrationMarkdownProjectionContainsClassIdentityAndStatus() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Added")));
        String markdown = new MarkdownOutputGenerator(reportOptions(scenario), compare(scenario)).generate();
        assertAll(() -> assertTrue(markdown.contains("sample.api.Added")), () -> assertTrue(markdown.toLowerCase().contains("new")));
    }

    /** Verifies: JCMP-RPT-007, JCMP-RPT-008, JCMP-INV-001; Seam: comparator graph -> HTML generator -> document; CVI-1; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationHtmlProjectionContainsConfiguredTitleAndClass() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Added")));
        HtmlOutputGeneratorOptions htmlOptions = new HtmlOutputGeneratorOptions();
        htmlOptions.setTitle("Compatibility Review");
        String html = new HtmlOutputGenerator(compare(scenario), reportOptions(scenario), htmlOptions).generate().getHtml();
        assertAll(() -> assertTrue(html.contains("Compatibility Review")), () -> assertTrue(html.contains("sample.api.Added")), () -> assertTrue(html.toLowerCase().contains("<html")));
    }

    /** Verifies: JCMP-RPT-010, JCMP-RPT-011, JCMP-INV-001; Seam: comparator graph -> XML generator -> root model; CVI-1; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion. */
    @Test void integrationXmlProjectionContainsRootClass() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Added")));
        XmlOutput output = new XmlOutputGenerator(compare(scenario), reportOptions(scenario), new XmlOutputGeneratorOptions()).generate();
        assertEquals("sample.api.Added", classNamed(xmlClasses(xmlRoot(output)), "sample.api.Added").getFullyQualifiedName());
    }

    /** Verifies: JCMP-STATE-001, JCMP-STATE-002, JCMP-INV-003; Seam: model graph -> output-only filter -> report while original membership is observed; CVI-3; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationOutputOnlyFilteringDoesNotChangeSeparatelyHeldGraph() throws Exception {
        ArchiveBuilder builder = pool -> Collections.singletonList(publicClass(pool, "sample.api.Stable"));
        Scenario scenario = new Scenario(builder, builder);
        List<JApiClass> graph = compare(scenario);
        Options options = reportOptions(scenario);
        options.setOutputOnlyModifications(true);
        new StdoutOutputGenerator(options, new ArrayList<>(graph)).generate();
        assertEquals("sample.api.Stable", graph.get(0).getFullyQualifiedName());
    }

    /** Verifies: JCMP-RPT-003, JCMP-INV-003; Seam: compatible graph -> binary-only output filter -> report; CVI-3; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationBinaryOnlyProjectionHidesCompatibleAddition() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")), pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); });
        Options options = reportOptions(scenario);
        options.setOutputOnlyBinaryIncompatibleModifications(true);
        assertTrue(new StdoutOutputGenerator(options, compare(scenario)).generate().contains("No changes."));
    }

    /** Verifies: JCMP-WF-003, JCMP-RPT-017, JCMP-INV-001; Seam: one comparison graph -> four report projections -> identity agreement; CVI-1; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion, atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationAllReportViewsAgreeOnRetainedClassIdentity() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Shared")));
        List<JApiClass> graph = compare(scenario);
        Options options = reportOptions(scenario);
        String stdout = new StdoutOutputGenerator(options, new ArrayList<>(graph)).generate();
        String markdown = new MarkdownOutputGenerator(options, new ArrayList<>(graph)).generate();
        String html = new HtmlOutputGenerator(new ArrayList<>(graph), options, new HtmlOutputGeneratorOptions()).generate().getHtml();
        Object xmlRoot = xmlRoot(new XmlOutputGenerator(new ArrayList<>(graph), reportOptions(scenario), new XmlOutputGeneratorOptions()).generate());
        assertAll(() -> assertTrue(stdout.contains("sample.api.Shared")), () -> assertTrue(markdown.contains("sample.api.Shared")), () -> assertTrue(html.contains("sample.api.Shared")), () -> assertEquals("sample.api.Shared", classNamed(xmlClasses(xmlRoot), "sample.api.Shared").getFullyQualifiedName()));
    }

    /** Verifies: JCMP-RPT-008, JCMP-INV-004; Seam: comparator graph -> semver reducer -> HTML metadata; CVI-4; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationHtmlSemanticMetadataMatchesSemverRecommendation() throws Exception {
        Scenario scenario = new Scenario(pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); }, pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        String semver = new SemverOut(reportOptions(scenario), compare(scenario)).generate();
        HtmlOutputGeneratorOptions generatorOptions = new HtmlOutputGeneratorOptions();
        generatorOptions.setSemanticVersioningInformation(semver);
        assertTrue(new HtmlOutputGenerator(compare(scenario), reportOptions(scenario), generatorOptions).generate().getHtml().contains(semver));
    }

    /** Verifies: JCMP-RPT-011, JCMP-INV-004; Seam: comparator graph -> semver reducer -> XML metadata; CVI-4; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationXmlSemanticMetadataMatchesSemverRecommendation() throws Exception {
        Scenario scenario = new Scenario(pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); }, pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        String semver = new SemverOut(reportOptions(scenario), compare(scenario)).generate();
        XmlOutputGeneratorOptions generatorOptions = new XmlOutputGeneratorOptions();
        generatorOptions.setSemanticVersioningInformation(semver);
        XmlOutput output = new XmlOutputGenerator(compare(scenario), reportOptions(scenario), generatorOptions).generate();
        assertTrue(scalarProjections(xmlRoot(output)).contains(semver));
    }

    /** Verifies: JCMP-ARCH-002, JCMP-RPT-011, JCMP-INV-008; Seam: archive versions -> comparison options -> XML metadata; CVI-8; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion. */
    @Test void integrationArchiveVersionsFlowIntoXmlMetadata() throws Exception {
        ArchiveBuilder builder = pool -> Collections.singletonList(publicClass(pool, "sample.api.Stable"));
        Scenario scenario = new Scenario(builder, "3.2.1", builder, "4.0.0");
        XmlOutput output = new XmlOutputGenerator(compare(scenario), reportOptions(scenario), new XmlOutputGeneratorOptions()).generate();
        List<String> values = scalarProjections(xmlRoot(output));
        assertAll(() -> assertTrue(values.contains("3.2.1")), () -> assertTrue(values.contains("4.0.0")));
    }

    /** Verifies: JCMP-RPT-014, JCMP-INV-008; Seam: archive versions -> report options -> Markdown metadata; CVI-8; Depends-On: atomicFileBackedArchivePreservesFileAndVersion. */
    @Test void integrationArchiveVersionsFlowIntoMarkdownDescription() throws Exception {
        ArchiveBuilder builder = pool -> Collections.singletonList(publicClass(pool, "sample.api.Stable"));
        Scenario scenario = new Scenario(builder, "3.2.1", builder, "4.0.0");
        String markdown = new MarkdownOutputGenerator(reportOptions(scenario), compare(scenario)).generate();
        assertAll(() -> assertTrue(markdown.contains("3.2.1")), () -> assertTrue(markdown.contains("4.0.0")));
    }

    /** Verifies: JCMP-RPT-018, JCMP-INV-009; Seam: file-backed archives -> filename-only option -> plain-text report; CVI-9; Depends-On: atomicFileBackedArchivePreservesFileAndVersion. */
    @Test void integrationReportOnlyFilenameRemovesParentPathFromPlainText() throws Exception {
        Scenario memory = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Added")));
        Path oldPath = materialize(memory.oldArchive);
        Path newPath = materialize(memory.newArchive);
        Scenario scenario = new Scenario(pool -> Collections.emptyList(), pool -> Collections.emptyList());
        JApiCmpArchive oldFile = new JApiCmpArchive(oldPath.toFile(), "1.0.0");
        JApiCmpArchive newFile = new JApiCmpArchive(newPath.toFile(), "2.0.0");
        Options options = Options.newDefault();
        options.setOldArchives(Collections.singletonList(oldFile));
        options.setNewArchives(Collections.singletonList(newFile));
        options.setReportOnlyFilename(true);
        List<JApiClass> graph = new JarArchiveComparator(new JarArchiveComparatorOptions()).compare(oldFile, newFile);
        String text = new StdoutOutputGenerator(options, graph).generate();
        assertAll(() -> assertTrue(text.contains(oldPath.getFileName().toString())), () -> assertFalse(text.contains(oldPath.getParent().toString())));
    }

    /** Verifies: JCMP-RPT-011, JCMP-RPT-018, JCMP-INV-009; Seam: file-backed archives -> filename-only option -> XML metadata; CVI-9; Depends-On: atomicFileBackedArchivePreservesFileAndVersion. */
    @Test void integrationReportOnlyFilenameChangesXmlArchiveDescriptionsOnly() throws Exception {
        Scenario memory = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Added")));
        Path oldPath = materialize(memory.oldArchive);
        Path newPath = materialize(memory.newArchive);
        JApiCmpArchive oldFile = new JApiCmpArchive(oldPath.toFile(), "1.0.0");
        JApiCmpArchive newFile = new JApiCmpArchive(newPath.toFile(), "2.0.0");
        Options options = Options.newDefault();
        options.setOldArchives(Collections.singletonList(oldFile));
        options.setNewArchives(Collections.singletonList(newFile));
        options.setReportOnlyFilename(true);
        List<JApiClass> graph = new JarArchiveComparator(new JarArchiveComparatorOptions()).compare(oldFile, newFile);
        XmlOutput output = new XmlOutputGenerator(graph, options, new XmlOutputGeneratorOptions()).generate();
        Object root = xmlRoot(output);
        List<String> values = scalarProjections(root);
        assertAll(() -> assertTrue(values.contains(oldPath.getFileName().toString())), () -> assertTrue(values.contains(newPath.getFileName().toString())), () -> assertFalse(values.contains(oldPath.toString())), () -> assertFalse(values.contains(newPath.toString())), () -> assertEquals("sample.api.Added", classNamed(xmlClasses(root), "sample.api.Added").getFullyQualifiedName()));
    }

    /** Verifies: JCMP-ARCH-008, JCMP-INV-007; Seam: annotation bytecode -> comparator option -> graph and report; CVI-7; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationAnnotationSuppressionChangesGraphAndReportConsistently() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.singletonList(publicClass(pool, "sample.api.Marked")), pool -> { CtClass type = publicClass(pool, "sample.api.Marked"); addDeprecated(type); return Collections.singletonList(type); });
        List<JApiClass> withAnnotations = compare(scenario);
        JarArchiveComparatorOptions noAnnotations = new JarArchiveComparatorOptions();
        noAnnotations.setNoAnnotations(true);
        List<JApiClass> suppressed = compare(scenario, noAnnotations);
        String report = new StdoutOutputGenerator(reportOptions(scenario), suppressed).generate();
        assertAll(() -> assertFalse(classNamed(withAnnotations, "sample.api.Marked").getAnnotations().isEmpty()), () -> assertTrue(classNamed(suppressed, "sample.api.Marked").getAnnotations().isEmpty()), () -> assertFalse(report.contains("java.lang.Deprecated")));
    }

    /** Verifies: JCMP-ARCH-008, JCMP-INV-007; Seam: synthetic bytecode -> comparator option -> graph and report; CVI-7; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationSyntheticInclusionChangesGraphAndReportConsistently() throws Exception {
        Scenario scenario = new Scenario(
            pool -> Collections.singletonList(publicClass(pool, "sample.api.Generated")),
            pool -> { CtClass type = publicClass(pool, "sample.api.Generated"); CtMethod method = addMethod(type, "public void generated() { }"); addSynthetic(method); return Collections.singletonList(type); });
        List<JApiClass> excluded = compare(scenario);
        String excludedReport = new StdoutOutputGenerator(reportOptions(scenario), excluded).generate();
        JarArchiveComparatorOptions include = new JarArchiveComparatorOptions();
        include.setIncludeSynthetic(true);
        List<JApiClass> included = compare(scenario, include);
        Options reportOptions = reportOptions(scenario);
        reportOptions.setIncludeSynthetic(true);
        String report = new StdoutOutputGenerator(reportOptions, new ArrayList<>(included)).generate();
        assertTrue(classNamed(excluded, "sample.api.Generated").getMethods().isEmpty(), "default report filtering must omit synthetic method");
        assertFalse(excludedReport.contains("generated"));
        assertEquals("generated", methodNamed(classNamed(included, "sample.api.Generated"), "generated").getName());
        assertTrue(report.contains("generated"), "synthetic-enabled report must include method");
    }

    /** Verifies: JCMP-ARCH-012, JCMP-ARCH-013; Seam: compatibility override -> comparator -> produced graph -> later comparator reset; CVI-2; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void integrationCompatibilityOverrideAppliesThenResetsForLaterComparator() throws Exception {
        Scenario scenario = new Scenario(pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); }, pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        JarArchiveComparatorOptions overridden = new JarArchiveComparatorOptions();
        overridden.addOverrideCompatibilityChange(new JarArchiveComparatorOptions.OverrideCompatibilityChange(JApiCompatibilityChangeType.METHOD_REMOVED, true, true, JApiSemanticVersionLevel.PATCH));
        JApiMethod first = methodNamed(classNamed(compare(scenario, overridden), "sample.api.Service"), "run");
        boolean firstBinary = first.isBinaryCompatible();
        JApiSemanticVersionLevel firstLevel = first.getCompatibilityChanges().get(0).getSemanticVersionLevel();
        JApiMethod second = methodNamed(classNamed(compare(scenario), "sample.api.Service"), "run");
        assertAll(() -> assertTrue(firstBinary), () -> assertEquals(JApiSemanticVersionLevel.PATCH, firstLevel), () -> assertFalse(second.isBinaryCompatible()), () -> assertEquals(JApiSemanticVersionLevel.MAJOR, second.getCompatibilityChanges().get(0).getSemanticVersionLevel()));
    }

    /** Verifies: JCMP-CLI-002, JCMP-ERR-007; Seam: CLI subprocess -> help projection -> exit outcome; CVI-10; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void systemHelpWorkflowSucceedsWithoutArchives() throws Exception {
        ProcessResult result = cli("--help");
        assertAll(() -> assertEquals(0, result.exit), () -> assertTrue(result.out.contains("--old")), () -> assertTrue(result.out.contains("--new")));
    }

    /** Verifies: JCMP-WF-005, JCMP-CLI-009; Seam: local JAR files -> CLI subprocess -> semantic stdout and exit; CVI-4, CVI-8; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion, atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void systemSemanticVersionWorkflowProducesOnlyRecommendation() throws Exception {
        Scenario scenario = new Scenario(pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); }, pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        Path oldPath = materialize(scenario.oldArchive);
        Path newPath = materialize(scenario.newArchive);
        ProcessResult result = cli("--old", oldPath.toString(), "--new", newPath.toString(), "--semantic-versioning");
        assertAll(() -> assertEquals(0, result.exit), () -> assertEquals("1.0.0", result.out.trim()));
    }

    /** Verifies: JCMP-CLI-013, JCMP-CLI-014, JCMP-ERR-006, JCMP-INV-010; Seam: modified JAR pair -> CLI error policy -> exit outcome; CVI-10; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void systemModificationErrorPolicyFailsOnModifiedGraph() throws Exception {
        Scenario scenario = new Scenario(pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")), pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); });
        ProcessResult result = cli("--old", materialize(scenario.oldArchive).toString(), "--new", materialize(scenario.newArchive).toString(), "--error-on-modifications");
        assertEquals(1, result.exit);
    }

    /** Verifies: JCMP-CLI-013, JCMP-CLI-014, JCMP-ERR-006, JCMP-INV-010; Seam: incompatible JAR pair -> CLI binary policy -> exit outcome; CVI-10; Depends-On: atomicMajorCompatibilityFamilyHasMajorProjections. */
    @Test void systemBinaryErrorPolicyFailsOnIncompatibleGraph() throws Exception {
        Scenario scenario = new Scenario(pool -> { CtClass type = publicClass(pool, "sample.api.Service"); addMethod(type, "public void run() { }"); return Collections.singletonList(type); }, pool -> Collections.singletonList(publicClass(pool, "sample.api.Service")));
        ProcessResult result = cli("--old", materialize(scenario.oldArchive).toString(), "--new", materialize(scenario.newArchive).toString(), "--error-on-binary-incompatibility");
        assertEquals(1, result.exit);
    }

    /** Verifies: JCMP-ARCH-005, JCMP-ERR-002; Seam: malformed archive bytes -> comparator I/O boundary -> categorized failure; CVI-10; Depends-On: atomicByteBackedArchivePreservesBytesNameAndVersion. */
    @Test void integrationMalformedArchiveRaisesCategorizedFailure() throws Exception {
        ByteArrayOutputStream malformedBytes = new ByteArrayOutputStream();
        try (JarOutputStream jar = new JarOutputStream(malformedBytes)) {
            jar.putNextEntry(new JarEntry("sample/api/Broken.class"));
            jar.write(new byte[] {1, 2, 3, 4});
            jar.closeEntry();
        }
        JApiCmpArchive malformed = new JApiCmpArchive(malformedBytes.toByteArray(), "1.0.0", "broken.jar");
        Scenario valid = new Scenario(pool -> Collections.emptyList(), pool -> Collections.singletonList(publicClass(pool, "sample.api.Valid")));
        JApiCmpException error = assertThrows(JApiCmpException.class, () -> new JarArchiveComparator(new JarArchiveComparatorOptions()).compare(malformed, valid.newArchive));
        assertTrue(error.getReason() == JApiCmpException.Reason.IoException || error.getReason() == JApiCmpException.Reason.IllegalArgument);
    }

    /** Verifies: JCMP-INV-006, JCMP-RPT-017; Seam: access threshold -> graph membership -> plain-text projection; CVI-6; Depends-On: atomicComparatorOptionsExposeDocumentedDefaults. */
    @Test void integrationAccessThresholdFlowsIntoReportMembership() throws Exception {
        ArchiveBuilder builder = pool -> Arrays.asList(visibleClass(pool, "sample.api.PublicType", Modifier.PUBLIC), visibleClass(pool, "sample.api.ProtectedType", Modifier.PROTECTED));
        Scenario scenario = new Scenario(builder, builder);
        JarArchiveComparatorOptions publicOnly = new JarArchiveComparatorOptions();
        publicOnly.setAccessModifier(AccessModifier.PUBLIC);
        Options report = reportOptions(scenario);
        report.setAccessModifier(AccessModifier.PUBLIC);
        String text = new StdoutOutputGenerator(report, compare(scenario, publicOnly)).generate();
        assertAll(() -> assertTrue(text.contains("sample.api.PublicType")), () -> assertFalse(text.contains("sample.api.ProtectedType")));
    }
}
