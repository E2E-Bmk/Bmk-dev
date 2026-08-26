package integration;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.AnnotationSpec;
import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.CodeBlock;
import com.squareup.javapoet.FieldSpec;
import com.squareup.javapoet.JavaFile;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.TypeSpec;
import javax.lang.model.element.Modifier;
import org.junit.jupiter.api.Test;
import support.Text;

/** Cross-view invariants: equality, round-tripping, and projection agreement. */
class RoundTripIntegrationTest {

    private static TypeSpec sampleType() {
        return TypeSpec.classBuilder("Sample")
                .addModifiers(Modifier.PUBLIC)
                .addField(FieldSpec.builder(int.class, "count", Modifier.PRIVATE)
                        .initializer("$L", 7)
                        .build())
                .addMethod(MethodSpec.methodBuilder("count")
                        .addModifiers(Modifier.PUBLIC)
                        .returns(int.class)
                        .addStatement("return count")
                        .build())
                .build();
    }

    /**
     * Verifies: Cross-View Invariants — toBuilder().build() reproduces an equal TypeSpec with
     * identical rendering.
     * Depends-On: typeSpecNameAndToBuilderRoundTrip.
     */
    @Test void typeSpecToBuilderReproducesEqualSpecAndText() {
        TypeSpec original = sampleType();
        TypeSpec rebuilt = original.toBuilder().build();
        assertEquals(original, rebuilt);
        assertEquals(original.toString(), rebuilt.toString());
        assertEquals(original.hashCode(), rebuilt.hashCode());
    }

    /**
     * Verifies: Cross-View Invariants — round trips hold for MethodSpec, FieldSpec,
     * AnnotationSpec, and CodeBlock.
     * Depends-On: methodToBuilderRoundTripsEqually, codeBlockToBuilderRoundTripsEqually,
     * annotationRendersMembersInInsertionOrder.
     */
    @Test void memberSpecsRoundTripThroughToBuilder() {
        MethodSpec method = MethodSpec.methodBuilder("go")
                .returns(String.class)
                .addStatement("return $S", "ok")
                .build();
        FieldSpec field = FieldSpec.builder(String.class, "tag", Modifier.FINAL)
                .initializer("$S", "t")
                .build();
        AnnotationSpec annotation = AnnotationSpec.builder(SuppressWarnings.class)
                .addMember("value", "$S", "unchecked")
                .build();
        CodeBlock block = CodeBlock.builder().addStatement("run($L)", 5).build();

        assertEquals(method, method.toBuilder().build());
        assertEquals(field, field.toBuilder().build());
        assertEquals(annotation, annotation.toBuilder().build());
        assertEquals(block, block.toBuilder().build());
        assertEquals(method.toString(), method.toBuilder().build().toString());
        assertEquals(field.toString(), field.toBuilder().build().toString());
        assertEquals(annotation.toString(), annotation.toBuilder().build().toString());
        assertEquals(block.toString(), block.toBuilder().build().toString());
    }

    /**
     * Verifies: State Model — equal content built through different call sequences is equal
     * and renders identically.
     * Depends-On: equalContentBlocksAreEqual, methodRendersModifiersParametersAndBody.
     */
    @Test void differentConstructionPathsWithSameContentAreEqual() {
        MethodSpec viaStatement = MethodSpec.methodBuilder("f")
                .addStatement("return $L", 1)
                .returns(int.class)
                .build();
        MethodSpec viaCode = MethodSpec.methodBuilder("f")
                .returns(int.class)
                .addCode(CodeBlock.builder().addStatement("return $L", 1).build())
                .build();
        assertEquals(viaStatement, viaCode);
        assertEquals(viaStatement.hashCode(), viaCode.hashCode());
        assertEquals(viaStatement.toString(), viaCode.toString());
    }

    /**
     * Verifies: Cross-View Invariants — ClassName navigation is self-consistent.
     * Depends-On: nestedClassEnclosingRoundTrip, topLevelClassNameIsChainHead,
     * reflectionNameUsesDollarForNesting.
     */
    @Test void classNameNavigationIsSelfConsistent() {
        ClassName entry = ClassName.get("java.util", "Map", "Entry");
        ClassName deeper = entry.nestedClass("Node");
        assertEquals(entry, deeper.enclosingClassName());
        assertEquals(ClassName.get("java.util", "Map"), deeper.topLevelClassName());
        assertEquals("java.util.Map.Entry.Node", deeper.canonicalName());
        assertEquals("java.util.Map$Entry$Node", deeper.reflectionName());
        assertEquals(entry.peerClass("Values"), ClassName.get("java.util", "Map", "Values"));
    }

    /**
     * Verifies: State Model — JavaFile.toBuilder preserves package, type, and rendering.
     * Depends-On: typeSpecNameAndToBuilderRoundTrip, getBuildsFromPackageAndSimpleName.
     */
    @Test void javaFileToBuilderPreservesRendering() {
        JavaFile original = JavaFile.builder("com.example", sampleType())
                .skipJavaLangImports(true)
                .build();
        JavaFile rebuilt = original.toBuilder().build();
        assertEquals(original.toString(), rebuilt.toString());
        assertEquals(original.packageName, rebuilt.packageName);
        assertEquals(original.typeSpec, rebuilt.typeSpec);
    }

    /**
     * Verifies: Source File Assembly — writeToPath returns the written file whose content
     * equals toString.
     * Depends-On: getBuildsFromPackageAndSimpleName.
     */
    @Test void writeToPathReturnsFileMatchingToString() throws Exception {
        java.nio.file.Path dir = java.nio.file.Files.createTempDirectory("oracle-jp-rt");
        JavaFile file = JavaFile.builder("com.example.rt", sampleType()).build();
        java.nio.file.Path written = file.writeToPath(dir);
        assertEquals(dir.resolve("com/example/rt/Sample.java"), written);
        assertEquals(file.toString(), Text.read(written));
    }

    /**
     * Verifies: Source File Assembly — toJavaFileObject exposes the same content and a
     * package-derived name.
     * Depends-On: getBuildsFromPackageAndSimpleName.
     */
    @Test void toJavaFileObjectAgreesWithToString() throws Exception {
        JavaFile file = JavaFile.builder("com.example.jfo", sampleType()).build();
        javax.tools.JavaFileObject object = file.toJavaFileObject();
        assertEquals(file.toString(), object.getCharContent(true).toString());
        assertTrue(object.getName().contains("Sample"));
    }

    /**
     * Verifies: State Model — TypeSpec public fields project the constructed members.
     * Depends-On: typeSpecNameAndToBuilderRoundTrip, superclassAndInterfacesRenderInHeader.
     */
    @Test void typeSpecPublicFieldsProjectMembers() {
        TypeSpec sample = sampleType();
        assertEquals("Sample", sample.name);
        assertEquals(1, sample.fieldSpecs.size());
        assertEquals("count", sample.fieldSpecs.get(0).name);
        assertEquals(1, sample.methodSpecs.size());
        assertEquals("count", sample.methodSpecs.get(0).name);
        assertTrue(sample.modifiers.contains(Modifier.PUBLIC));
        assertTrue(sample.superinterfaces.isEmpty());
        assertTrue(sample.enumConstants.isEmpty());
    }

    /**
     * Verifies: Cross-View Invariants — unequal content is unequal and renders differently.
     * Depends-On: equalContentBlocksAreEqual.
     */
    @Test void distinctContentIsUnequalAndRendersDifferently() {
        CodeBlock a = CodeBlock.of("x = $L", 1);
        CodeBlock b = CodeBlock.of("x = $L", 2);
        assertNotEquals(a, b);
        assertNotEquals(a.toString(), b.toString());
    }

    /**
     * Verifies: Cross-View Invariants — standalone toString of a member equals its rendering
     * inside a file body modulo import shortening.
     * Depends-On: typePlaceholderIsFullyQualifiedStandalone, methodRendersModifiersParametersAndBody.
     */
    @Test void standaloneRenderingUsesQualifiedNamesWhereFileUsesImports() {
        MethodSpec m = MethodSpec.methodBuilder("now")
                .returns(ClassName.get("java.time", "Instant"))
                .addStatement("return $T.now()", ClassName.get("java.time", "Instant"))
                .build();
        assertTrue(m.toString().contains("java.time.Instant.now()"));
        String inFile = JavaFile.builder("com.example",
                TypeSpec.classBuilder("Clocked").addMethod(m).build()).build().toString();
        assertTrue(inFile.contains("import java.time.Instant;"));
        assertTrue(inFile.contains("return Instant.now();"));
    }
}
