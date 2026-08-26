package integration;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.FieldSpec;
import com.squareup.javapoet.JavaFile;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.ParameterizedTypeName;
import com.squareup.javapoet.TypeSpec;
import java.util.Map;
import javax.lang.model.element.Modifier;
import org.junit.jupiter.api.Test;
import support.Text;

/** Integration tests for compilation-unit assembly and import resolution. */
class FileAssemblyIntegrationTest {

    /**
     * Verifies: Source File Assembly and Import Resolution — java.lang imported by default.
     * Depends-On: getBuildsFromPackageAndSimpleName, emptyMethodRendersVoidAndEmptyBraces.
     */
    @Test void javaLangTypesAreImportedByDefault() {
        TypeSpec hello = TypeSpec.classBuilder("Hello")
                .addField(String.class, "name", Modifier.PRIVATE)
                .build();
        assertEquals(Text.lines(
                "package com.example;",
                "",
                "import java.lang.String;",
                "",
                "class Hello {",
                "  private String name;",
                "}"), JavaFile.builder("com.example", hello).build().toString());
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — skipJavaLangImports suppression.
     * Depends-On: getBuildsFromPackageAndSimpleName, fieldRendersModifiersTypeAndInitializer.
     */
    @Test void skipJavaLangImportsRendersShortNamesWithoutImports() {
        TypeSpec hello = TypeSpec.classBuilder("Hello")
                .addField(String.class, "name", Modifier.PRIVATE)
                .build();
        assertEquals(Text.lines(
                "package com.example;",
                "",
                "class Hello {",
                "  private String name;",
                "}"), JavaFile.builder("com.example", hello).skipJavaLangImports(true).build().toString());
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — first same-simple-name type wins the import.
     * Depends-On: typePlaceholderIsFullyQualifiedStandalone, methodRendersModifiersParametersAndBody.
     */
    @Test void simpleNameCollisionFullyQualifiesLaterType() {
        MethodSpec f = MethodSpec.methodBuilder("f")
                .addStatement("$T x = null", ClassName.get("java.util", "Locale"))
                .addStatement("$T y = null", ClassName.get("com.acme", "Locale"))
                .build();
        assertEquals(Text.lines(
                "package com.example;",
                "",
                "import java.util.Locale;",
                "",
                "class C {",
                "  void f() {",
                "    Locale x = null;",
                "    com.acme.Locale y = null;",
                "  }",
                "}"), JavaFile.builder("com.example",
                        TypeSpec.classBuilder("C").addMethod(f).build()).build().toString());
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — nested type imports its top-level class.
     * Depends-On: bestGuessSplitsPackageAndNestedClasses, topLevelClassNameIsChainHead.
     */
    @Test void nestedTypeImportsTopLevelAndRendersQualifiedNesting() {
        TypeSpec n = TypeSpec.classBuilder("N")
                .addField(ClassName.get("java.util", "Map", "Entry"), "e", Modifier.PRIVATE)
                .build();
        assertEquals(Text.lines(
                "package com.example;",
                "",
                "import java.util.Map;",
                "",
                "class N {",
                "  private Map.Entry e;",
                "}"), JavaFile.builder("com.example", n).build().toString());
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — static import folds qualified calls.
     * Depends-On: typePlaceholderIsFullyQualifiedStandalone, stringPlaceholderQuotesAndEscapes.
     */
    @Test void staticImportRendersBareMemberReference() {
        ClassName checks = ClassName.get("com.acme", "Checks");
        TypeSpec s = TypeSpec.classBuilder("S")
                .addMethod(MethodSpec.methodBuilder("m")
                        .addStatement("$T.checkNotNull($S)", checks, "x")
                        .build())
                .build();
        assertEquals(Text.lines(
                "package com.example;",
                "",
                "import static com.acme.Checks.checkNotNull;",
                "",
                "class S {",
                "  void m() {",
                "    checkNotNull(\"x\");",
                "  }",
                "}"), JavaFile.builder("com.example", s)
                        .addStaticImport(checks, "checkNotNull").build().toString());
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — imports sorted lexicographically.
     * Depends-On: typePlaceholderIsFullyQualifiedStandalone.
     */
    @Test void importsAreSortedLexicographically() {
        MethodSpec m = MethodSpec.methodBuilder("m")
                .addStatement("$T a = null", ClassName.get("java.util", "List"))
                .addStatement("$T b = null", ClassName.get("java.io", "File"))
                .addStatement("$T c = null", ClassName.get("com.acme", "Widget"))
                .build();
        String rendered = JavaFile.builder("com.example",
                TypeSpec.classBuilder("Sorted").addMethod(m).build()).build().toString();
        int acme = rendered.indexOf("import com.acme.Widget;");
        int io = rendered.indexOf("import java.io.File;");
        int util = rendered.indexOf("import java.util.List;");
        assertTrue(acme >= 0 && io > acme && util > io);
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — file comment and custom indent.
     * Depends-On: emptyMethodRendersVoidAndEmptyBraces.
     */
    @Test void fileCommentAndCustomIndentApply() {
        TypeSpec f = TypeSpec.classBuilder("F")
                .addMethod(MethodSpec.methodBuilder("m").addStatement("go()").build())
                .build();
        assertEquals(Text.lines(
                "// Generated carefully",
                "package com.example;",
                "",
                "class F {",
                "    void m() {",
                "        go();",
                "    }",
                "}"), JavaFile.builder("com.example", f)
                        .addFileComment("Generated $L", "carefully")
                        .indent("    ").build().toString());
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — empty package omits the package statement.
     * Depends-On: defaultPackageRendersBareName.
     */
    @Test void defaultPackageOmitsPackageStatement() {
        assertEquals(Text.lines(
                "class D {",
                "}"), JavaFile.builder("", TypeSpec.classBuilder("D").build()).build().toString());
    }

    /**
     * Verifies: Cross-View Invariants — writeTo tree mirrors package and content equals toString.
     * Depends-On: getBuildsFromPackageAndSimpleName.
     */
    @Test void writeToCreatesPackageTreeWithIdenticalContent() throws Exception {
        java.nio.file.Path dir = java.nio.file.Files.createTempDirectory("oracle-jp");
        JavaFile file = JavaFile.builder("com.example.deep",
                TypeSpec.classBuilder("W").addModifiers(Modifier.PUBLIC).build()).build();
        file.writeTo(dir);
        java.nio.file.Path written = dir.resolve("com/example/deep/W.java");
        assertTrue(java.nio.file.Files.exists(written));
        assertEquals(file.toString(), Text.read(written));
    }

    /**
     * Verifies: Source File Assembly and Import Resolution — parameterized field pulls both type imports.
     * Depends-On: parameterizedTypeRendersAngleBrackets.
     */
    @Test void parameterizedFieldImportsRawAndArgumentTypes() {
        FieldSpec index = FieldSpec.builder(
                ParameterizedTypeName.get(ClassName.get(Map.class),
                        ClassName.get(String.class), ClassName.get(Integer.class)),
                "index", Modifier.PRIVATE).build();
        assertEquals(Text.lines(
                "package com.example;",
                "",
                "import java.lang.Integer;",
                "import java.lang.String;",
                "import java.util.Map;",
                "",
                "class P {",
                "  private Map<String, Integer> index;",
                "}"), JavaFile.builder("com.example",
                        TypeSpec.classBuilder("P").addField(index).build()).build().toString());
    }

    /**
     * Verifies: State Model — JavaFile public fields project the constituents.
     * Depends-On: typeSpecNameAndToBuilderRoundTrip.
     */
    @Test void javaFileExposesPackageAndTypeSpec() {
        TypeSpec t = TypeSpec.classBuilder("Q").build();
        JavaFile file = JavaFile.builder("com.example", t).build();
        assertEquals("com.example", file.packageName);
        assertEquals(t, file.typeSpec);
    }
}
