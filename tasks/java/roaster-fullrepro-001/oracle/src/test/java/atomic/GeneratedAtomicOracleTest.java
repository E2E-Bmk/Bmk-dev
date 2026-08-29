package atomic;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.util.List;

import org.jboss.forge.roaster.ParserException;
import org.jboss.forge.roaster.Problem;
import org.jboss.forge.roaster.Roaster;
import org.jboss.forge.roaster.model.JavaUnit;
import org.jboss.forge.roaster.model.Visibility;
import org.jboss.forge.roaster.model.source.AnnotationElementSource;
import org.jboss.forge.roaster.model.source.AnnotationSource;
import org.jboss.forge.roaster.model.source.EnumConstantSource;
import org.jboss.forge.roaster.model.source.FieldSource;
import org.jboss.forge.roaster.model.source.Import;
import org.jboss.forge.roaster.model.source.InitializerSource;
import org.jboss.forge.roaster.model.source.JavaAnnotationSource;
import org.jboss.forge.roaster.model.source.JavaClassSource;
import org.jboss.forge.roaster.model.source.JavaDocSource;
import org.jboss.forge.roaster.model.source.JavaEnumSource;
import org.jboss.forge.roaster.model.source.JavaInterfaceSource;
import org.jboss.forge.roaster.model.source.JavaRecordComponentSource;
import org.jboss.forge.roaster.model.source.JavaRecordSource;
import org.jboss.forge.roaster.model.source.JavaSource;
import org.jboss.forge.roaster.model.source.MethodSource;
import org.jboss.forge.roaster.model.source.ParameterSource;
import org.jboss.forge.roaster.model.source.PropertySource;
import org.jboss.forge.roaster.model.source.TypeVariableSource;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GeneratedAtomicOracleTest {

    interface UnsupportedSource extends JavaSource<UnsupportedSource> {
    }

    /** Verifies: ROASTER-FAC-001. */
    @Test
    void createsEveryDeclaredSourceKind() {
        assertAll(
                () -> assertTrue(Roaster.create(JavaClassSource.class).isClass()),
                () -> assertTrue(Roaster.create(JavaInterfaceSource.class).isInterface()),
                () -> assertTrue(Roaster.create(JavaEnumSource.class).isEnum()),
                () -> assertTrue(Roaster.create(JavaAnnotationSource.class).isAnnotation()),
                () -> assertTrue(Roaster.create(JavaRecordSource.class).isRecord()));
    }

    /** Verifies: ROASTER-FAC-003. */
    @Test
    void parsesStringCarrier() {
        JavaClassSource parsed = Roaster.parse(JavaClassSource.class,
                "package sample.alpha; public class StringCarrier {}");
        assertEquals("sample.alpha.StringCarrier", parsed.getQualifiedName());
    }

    /** Verifies: ROASTER-FAC-003. */
    @Test
    void parsesCharacterArrayCarrier() {
        char[] source = "public interface CharacterCarrier {}".toCharArray();
        JavaInterfaceSource parsed = Roaster.parse(JavaInterfaceSource.class, source);
        assertEquals("CharacterCarrier", parsed.getName());
    }

    /** Verifies: ROASTER-FAC-003, ROASTER-FAC-006. */
    @Test
    void parsesInputStreamCarrier() {
        ByteArrayInputStream input = new ByteArrayInputStream(
                "public enum StreamCarrier { NORTH, SOUTH }".getBytes(StandardCharsets.UTF_8));
        JavaEnumSource parsed = Roaster.parse(JavaEnumSource.class, input);
        assertAll(() -> assertEquals("StreamCarrier", parsed.getName()),
                () -> assertEquals(2, parsed.getEnumConstants().size()));
    }

    /** Verifies: ROASTER-FAC-007, ROASTER-FAC-008. */
    @Test
    void compilationUnitPreservesOrderAndIsImmutable() {
        JavaUnit unit = Roaster.parseUnit("package sample.unit; public class Lead {} class Tail {}");
        assertAll(() -> assertEquals("Lead", unit.getGoverningType().getName()),
                () -> assertEquals("Lead", unit.getTopLevelTypes().get(0).getName()),
                () -> assertEquals("Tail", unit.getTopLevelTypes().get(1).getName()),
                () -> assertThrows(UnsupportedOperationException.class,
                        () -> unit.getTopLevelTypes().clear()));
    }

    /** Verifies: ROASTER-FAC-014. */
    @Test
    void validSnippetHasNoProblems() {
        assertTrue(Roaster.validateSnippet("int horizon = 17;").isEmpty());
    }

    /** Verifies: ROASTER-FAC-015. */
    @Test
    void invalidSnippetExposesProblemLocation() {
        List<Problem> problems = Roaster.validateSnippet("int horizon =");
        assertAll(() -> assertFalse(problems.isEmpty()),
                () -> assertNotNull(problems.get(0).getMessage()),
                () -> assertTrue(problems.get(0).getSourceLineNumber() >= 1));
    }

    /** Verifies: ROASTER-FAC-004, ROASTER-ERR-003. */
    @Test
    void typedParseRejectsDifferentDeclarationKind() {
        assertThrows(ParserException.class,
                () -> Roaster.parse(JavaClassSource.class, "public interface WrongKind {}"));
    }

    /** Verifies: ROASTER-ERR-002. */
    @Test
    void unsupportedSourceInterfaceIsRejected() {
        assertThrows(ParserException.class, () -> Roaster.create(UnsupportedSource.class));
    }

    /** Verifies: ROASTER-FAC-003, ROASTER-ERR-004. */
    @Test
    void fileAndUrlParsingDistinguishesReadableAndUnreadableInputs() throws Exception {
        File missing = new File("target", "missing-roaster-oracle-input.java");
        assertAll(() -> assertThrows(IOException.class, () -> Roaster.parse(missing)),
                () -> assertThrows(IOException.class, () -> Roaster.parse(missing.toURI().toURL())));
        Path readable = Files.createTempFile(Path.of("target"), "roaster-readable-", ".java");
        try {
            Files.writeString(readable, "public class ReadableCarrier {}", StandardCharsets.UTF_8);
            assertAll(() -> assertEquals("ReadableCarrier", Roaster.parse(readable.toFile()).getName()),
                    () -> assertEquals("ReadableCarrier", Roaster.parse(readable.toUri().toURL()).getName()));
        } finally {
            Files.deleteIfExists(readable);
        }
    }

    /** Verifies: ROASTER-FAC-010, ROASTER-FAC-013. */
    @Test
    void formattingRetainsDeclarationContent() {
        String formatted = Roaster.format("package sample.format;public class Crisp{int value;}");
        assertAll(() -> assertTrue(formatted.contains("sample.format")),
                () -> assertTrue(formatted.contains("Crisp")),
                () -> assertTrue(formatted.contains("value")));
    }

    /** Verifies: ROASTER-TYPE-001, ROASTER-TYPE-002. */
    @Test
    void packageAndNameDefineTypeIdentity() {
        JavaClassSource source = Roaster.create(JavaClassSource.class)
                .setPackage("sample.identity").setName("Beacon");
        assertAll(() -> assertEquals("Beacon", source.getName()),
                () -> assertEquals("sample.identity", source.getPackage()),
                () -> assertEquals("sample.identity.Beacon", source.getQualifiedName()),
                () -> assertEquals("sample.identity.Beacon", source.getCanonicalName()));
    }

    /** Verifies: ROASTER-TYPE-003. */
    @Test
    void defaultPackageClearsPackageProjection() {
        JavaClassSource source = Roaster.create(JavaClassSource.class)
                .setPackage("sample.temporary").setName("Unpacked").setDefaultPackage();
        assertAll(() -> assertNull(source.getPackage()), () -> assertTrue(source.isDefaultPackage()));
    }

    /** Verifies: ROASTER-TYPE-004. */
    @Test
    void declarationKindPredicatesAreExclusive() {
        JavaRecordSource record = Roaster.create(JavaRecordSource.class).setName("KindRecord");
        assertAll(() -> assertTrue(record.isRecord()), () -> assertFalse(record.isClass()),
                () -> assertFalse(record.isInterface()), () -> assertFalse(record.isEnum()),
                () -> assertFalse(record.isAnnotation()));
    }

    /** Verifies: ROASTER-TYPE-005. */
    @Test
    void topLevelTypeEnclosesItself() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("OuterSelf");
        assertSame(source, source.getEnclosingType());
    }

    /** Verifies: ROASTER-TYPE-010, ROASTER-TYPE-011. */
    @Test
    void typeVariableBoundsPreserveOrder() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("GenericHost");
        TypeVariableSource<JavaClassSource> variable = source.addTypeVariable("T")
                .setBounds(CharSequence.class, java.io.Serializable.class);
        assertAll(() -> assertTrue(source.hasTypeVariable("T")),
                () -> assertEquals(2, variable.getBounds().size()),
                () -> assertEquals("CharSequence", variable.getBounds().get(0).getSimpleName()),
                () -> assertEquals("Serializable", variable.getBounds().get(1).getSimpleName()));
    }

    /** Verifies: ROASTER-TYPE-015. */
    @Test
    void recoverableSyntaxErrorsExposeCoordinates() {
        JavaClassSource source = Roaster.parse(JavaClassSource.class,
                "public class Recoverable { void broken( { } }");
        assertAll(() -> assertTrue(source.hasSyntaxErrors()),
                () -> assertFalse(source.getSyntaxErrors().isEmpty()),
                () -> assertTrue(source.getSyntaxErrors().get(0).getLine() >= 1));
    }

    /** Verifies: ROASTER-IMP-001, ROASTER-IMP-002, ROASTER-IMP-003. */
    @Test
    void importLifecycleIsIdempotent() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("ImportHost");
        Import first = source.addImport("sample.types.Widget");
        Import second = source.addImport("sample.types.Widget");
        assertAll(() -> assertNotNull(first), () -> assertNotNull(second),
                () -> assertTrue(source.hasImport("sample.types.Widget")),
                () -> assertEquals(1, source.getImports().size()));
        source.removeImport("sample.types.Widget");
        assertFalse(source.hasImport("sample.types.Widget"));
    }

    /** Verifies: ROASTER-IMP-005, ROASTER-IMP-006, ROASTER-ERR-011. */
    @Test
    void nonImportableReferencesLeaveImportsUnchanged() {
        JavaClassSource source = Roaster.create(JavaClassSource.class)
                .setPackage("sample.same").setName("Anchor");
        assertAll(() -> assertNull(source.addImport("int")),
                () -> assertNull(source.addImport("String")),
                () -> assertNull(source.addImport("java.lang.String")),
                () -> assertNull(source.addImport("sample.same.Anchor")),
                () -> assertTrue(source.getImports().isEmpty()));
    }

    /** Verifies: ROASTER-IMP-007, ROASTER-IMP-008, ROASTER-IMP-009. */
    @Test
    void wildcardImportExposesAndMutatesProjection() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("WildcardHost");
        Import wildcard = source.addImport("sample.catalog.*");
        wildcard.setStatic(true);
        assertAll(() -> assertEquals("sample.catalog", wildcard.getPackage()),
                () -> assertEquals(Import.WILDCARD, wildcard.getSimpleName()),
                () -> assertEquals("sample.catalog.*", wildcard.getQualifiedName()),
                () -> assertTrue(wildcard.isWildcard()), () -> assertTrue(wildcard.isStatic()),
                () -> assertTrue(source.getImports().get(0).isStatic()),
                () -> assertTrue(source.toUnformattedString().contains("import static sample.catalog.*")));
    }

    /** Verifies: ROASTER-IMP-010, ROASTER-IMP-011. */
    @Test
    void directImportWinsSimpleNameResolution() {
        JavaClassSource source = Roaster.create(JavaClassSource.class)
                .setPackage("sample.local").setName("Resolver");
        source.addImport("sample.remote.Signal");
        assertAll(() -> assertEquals("int", source.resolveType("int")),
                () -> assertEquals("sample.remote.Signal", source.resolveType("Signal")));
    }

    /** Verifies: ROASTER-MEM-002. */
    @Test
    void fieldMutatorsExposeCompleteState() {
        FieldSource<JavaClassSource> field = Roaster.create(JavaClassSource.class)
                .setName("ModifierHost").addField().setName("sequence").setType(long.class)
                .setPrivate().setStatic(true).setFinal(true).setTransient(true).setVolatile(true)
                .setLiteralInitializer("41L");
        assertAll(() -> assertEquals("sequence", field.getName()),
                () -> assertEquals("long", field.getType().getName()),
                () -> assertTrue(field.isPrivate()), () -> assertTrue(field.isStatic()),
                () -> assertTrue(field.isFinal()), () -> assertTrue(field.isTransient()),
                () -> assertTrue(field.isVolatile()),
                () -> assertEquals("41L", field.getLiteralInitializer()));
    }

    /** Verifies: ROASTER-TYPE-007, ROASTER-ERR-007, ROASTER-ERR-008. */
    @Test
    void absentLookupsAndRemovalsAreStable() {
        JavaRecordSource source = Roaster.create(JavaRecordSource.class).setName("SparseRecord");
        assertNull(source.getNestedType("unknown"));
        int before = source.getRecordComponents().size();
        source.removeRecordComponent("unknown");
        assertEquals(before, source.getRecordComponents().size());
    }

    /** Verifies: ROASTER-MEM-004, ROASTER-MEM-005, ROASTER-MEM-006. */
    @Test
    void methodLookupDistinguishesOverloads() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("OverloadHost");
        source.addMethod().setName("read").setReturnType(String.class);
        source.addMethod().setName("read").setReturnType(String.class).addParameter(int.class, "index");
        assertAll(() -> assertNotNull(source.getMethod("read")),
                () -> assertNotNull(source.getMethod("read", int.class)),
                () -> assertNull(source.getMethod("read", long.class)),
                () -> assertTrue(source.hasMethodSignature("read")));
    }

    /** Verifies: ROASTER-MEM-007, ROASTER-MEM-008, ROASTER-MEM-009. */
    @Test
    void methodStateTracksConstructorAndNativeRules() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("MethodHost");
        MethodSource<JavaClassSource> method = source.addMethod().setName("temporary")
                .setPublic().setReturnType(String.class).setBody("return \"ready\";");
        method.setConstructor(true);
        assertAll(() -> assertTrue(method.isConstructor()),
                () -> assertEquals("MethodHost", method.getName()));
        method.setConstructor(false).setName("nativeRead").setReturnType(String.class)
                .setBody("return \"ready\";").setNative(true);
        assertAll(() -> assertTrue(method.isNative()), () -> assertNull(method.getBody()));
    }

    /** Verifies: ROASTER-MEM-010, ROASTER-MEM-011. */
    @Test
    void parameterStatePreservesOrderAndFlags() {
        MethodSource<JavaClassSource> method = Roaster.create(JavaClassSource.class)
                .setName("ParameterHost").addMethod().setName("merge").setReturnTypeVoid();
        ParameterSource<JavaClassSource> first = method.addParameter(String.class, "left").setFinal(true);
        ParameterSource<JavaClassSource> second = method.addParameter(String[].class, "right").setVarArgs(true);
        assertAll(() -> assertEquals("left", method.getParameters().get(0).getName()),
                () -> assertEquals("right", method.getParameters().get(1).getName()),
                () -> assertTrue(first.isFinal()), () -> assertTrue(second.isVarArgs()),
                () -> assertTrue(method.toSignature().contains("merge")));
    }

    /** Verifies: ROASTER-MEM-012. */
    @Test
    void initializerBodyAndStaticStateAreObservable() {
        InitializerSource<JavaClassSource> initializer = Roaster.create(JavaClassSource.class)
                .setName("InitializerHost").addInitializer().setBody("int local = 23;").setStatic(true);
        assertAll(() -> assertTrue(initializer.isStatic()),
                () -> assertTrue(initializer.getBody().contains("local")));
    }

    /** Verifies: ROASTER-MEM-017, ROASTER-ERR-009. */
    @Test
    void duplicatePropertyComponentsAreRejected() {
        PropertySource<JavaClassSource> property = Roaster.create(JavaClassSource.class)
                .setName("StrictPropertyHost").addProperty(String.class, "code");
        assertAll(() -> assertThrows(IllegalStateException.class, property::createField),
                () -> assertThrows(IllegalStateException.class, property::createAccessor),
                () -> assertThrows(IllegalStateException.class, property::createMutator));
    }

    /** Verifies: ROASTER-ANN-001, ROASTER-ANN-002. */
    @Test
    void annotationLifecycleUpdatesTargetView() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("AnnotatedHost");
        AnnotationSource<JavaClassSource> annotation = source.addAnnotation(Deprecated.class);
        assertAll(() -> assertTrue(source.hasAnnotation(Deprecated.class)),
                () -> assertNotNull(source.getAnnotation(Deprecated.class)));
        source.removeAllAnnotations();
        assertNull(source.getAnnotation(Deprecated.class));
    }

    /** Verifies: ROASTER-ANN-003, ROASTER-ANN-004. */
    @Test
    void annotationValuesDriveFormPredicates() {
        AnnotationSource<JavaClassSource> annotation = Roaster.create(JavaClassSource.class)
                .setName("ValueHost").addAnnotation("sample.Marker");
        assertTrue(annotation.isMarker());
        annotation.setStringValue("signal");
        assertAll(() -> assertTrue(annotation.isSingleValue()),
                () -> assertEquals("signal", annotation.getStringValue()));
        annotation.setStringValue("mode", "steady");
        assertAll(() -> assertTrue(annotation.isNormal()),
                () -> assertEquals("steady", annotation.getStringValue("mode")),
                () -> assertTrue(annotation.isTypeElementDefined("mode")));
    }

    /** Verifies: ROASTER-ANN-007, ROASTER-ANN-009, ROASTER-ANN-010. */
    @Test
    void javaDocTextAndTagsRemainDistinct() {
        JavaClassSource source = Roaster.create(JavaClassSource.class).setName("DocumentedHost");
        JavaDocSource<JavaClassSource> doc = source.getJavaDoc().setText("Coordinates a beacon.");
        doc.addTagValue("since", "17");
        doc.addTagValue("since", "18");
        assertAll(() -> assertEquals("Coordinates a beacon.", doc.getText()),
                () -> assertEquals(2, doc.getTags("since").size()),
                () -> assertTrue(doc.getTagNames().contains("since")));
        source.removeJavaDoc();
        assertFalse(source.hasJavaDoc());
    }

    /** Verifies: ROASTER-ANN-011, ROASTER-ANN-012, ROASTER-ANN-013. */
    @Test
    void enumConstantLifecycleExposesBody() {
        JavaEnumSource source = Roaster.create(JavaEnumSource.class).setName("Direction");
        EnumConstantSource constant = source.addEnumConstant(
                "EAST(17) { private int code; }");
        assertAll(() -> assertNotNull(source.getEnumConstant("EAST")),
                () -> assertTrue(source.toUnformattedString().contains("17")),
                () -> assertTrue(source.toUnformattedString().contains("code")));
        constant.removeBody();
        assertFalse(source.toUnformattedString().contains("code"));
    }

    /** Verifies: ROASTER-ANN-014, ROASTER-ANN-015, ROASTER-ANN-016. */
    @Test
    void annotationElementLifecyclePreservesTypeAndDefault() {
        JavaAnnotationSource source = Roaster.create(JavaAnnotationSource.class).setName("Threshold");
        AnnotationElementSource element = source.addAnnotationElement("int limit() default 23");
        assertAll(() -> assertNotNull(source.getAnnotationElement("limit")),
                () -> assertEquals("int", element.getType().getName()),
                () -> assertTrue(source.toUnformattedString().contains("default 23")),
                () -> assertNull(source.getAnnotationElement("missing")));
    }

    /** Verifies: ROASTER-ANN-017, ROASTER-ANN-018. */
    @Test
    void recordComponentLifecyclePreservesOrderAndType() {
        JavaRecordSource source = Roaster.create(JavaRecordSource.class).setName("Waypoint");
        JavaRecordComponentSource first = source.addRecordComponent(String.class, "name");
        source.addRecordComponent(long.class, "distance");
        assertAll(() -> assertEquals("name", source.getRecordComponents().get(0).getName()),
                () -> assertEquals("distance", source.getRecordComponents().get(1).getName()),
                () -> assertEquals("java.lang.String", first.getType().getQualifiedName()));
        source.removeRecordComponent("name");
        assertEquals("distance", source.getRecordComponents().get(0).getName());
    }

    /** Verifies: ROASTER-ANN-019, ROASTER-ANN-020. */
    @Test
    void recordComponentFinalityTracksExplicitState() {
        JavaRecordComponentSource component = Roaster.create(JavaRecordSource.class)
                .setName("StrictRecord").addRecordComponent(String.class, "value");
        assertFalse(component.isFinal());
        assertSame(component, component.setFinal(true));
        assertTrue(component.isFinal());
    }

}
