package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.AnnotationSpec;
import com.squareup.javapoet.ArrayTypeName;
import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.FieldSpec;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.ParameterSpec;
import javax.lang.model.element.Modifier;
import org.junit.jupiter.api.Test;
import support.Text;

/** Atomic tests for method, field, parameter, and annotation rendering. */
class MethodFieldAtomicTest {

    /** Verifies: Methods, Fields, Parameters, and Annotations — bodiless method renders void and empty braces. */
    @Test void emptyMethodRendersVoidAndEmptyBraces() {
        assertEquals(Text.lines(
                "void m() {",
                "}"), MethodSpec.methodBuilder("m").build().toString());
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — modifiers, parameters, return, statement. */
    @Test void methodRendersModifiersParametersAndBody() {
        MethodSpec add = MethodSpec.methodBuilder("add")
                .addModifiers(Modifier.PUBLIC)
                .returns(int.class)
                .addParameter(int.class, "a")
                .addParameter(int.class, "b")
                .addStatement("return a + b")
                .build();
        assertEquals(Text.lines(
                "public int add(int a, int b) {",
                "  return a + b;",
                "}"), add.toString());
    }

    /** Verifies: Code Blocks and the Format Language — control flow brace shape. */
    @Test void controlFlowRendersBracesAndElseChaining() {
        MethodSpec g = MethodSpec.methodBuilder("g")
                .beginControlFlow("if (a)")
                .addStatement("x()")
                .nextControlFlow("else")
                .addStatement("y()")
                .endControlFlow()
                .build();
        assertEquals(Text.lines(
                "void g() {",
                "  if (a) {",
                "    x();",
                "  } else {",
                "    y();",
                "  }",
                "}"), g.toString());
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — varargs rendering. */
    @Test void varargsRendersEllipsisOnFinalArrayParameter() {
        MethodSpec v = MethodSpec.methodBuilder("v")
                .varargs(true)
                .addParameter(ArrayTypeName.of(ClassName.get(String.class)), "parts")
                .build();
        assertEquals(Text.lines(
                "void v(java.lang.String... parts) {",
                "}"), v.toString());
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — Javadoc block rendering. */
    @Test void javadocRendersCommentBlockAboveDeclaration() {
        MethodSpec d = MethodSpec.methodBuilder("d")
                .addJavadoc("Hello $L.\n", "world")
                .build();
        assertEquals(Text.lines(
                "/**",
                " * Hello world.",
                " */",
                "void d() {",
                "}"), d.toString());
    }

    /** Verifies: Error Semantics — abstract method with code raises IllegalArgumentException. */
    @Test void abstractMethodWithCodeThrows() {
        assertThrows(IllegalArgumentException.class, () -> MethodSpec.methodBuilder("am")
                .addModifiers(Modifier.ABSTRACT)
                .addStatement("x()")
                .build());
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — isConstructor and name projection. */
    @Test void constructorFlagAndMethodNameProjection() {
        assertTrue(MethodSpec.constructorBuilder().build().isConstructor());
        MethodSpec m = MethodSpec.methodBuilder("run").build();
        assertFalse(m.isConstructor());
        assertEquals("run", m.name);
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — field with initializer rendering. */
    @Test void fieldRendersModifiersTypeAndInitializer() {
        FieldSpec greeting = FieldSpec.builder(String.class, "GREETING", Modifier.STATIC, Modifier.FINAL)
                .initializer("$S", "hey")
                .build();
        assertEquals("static final java.lang.String GREETING = \"hey\";\n", greeting.toString());
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — parameter spec rendering inside a method. */
    @Test void parameterSpecCarriesAnnotationsAndModifiers() {
        ParameterSpec p = ParameterSpec.builder(String.class, "input", Modifier.FINAL).build();
        MethodSpec m = MethodSpec.methodBuilder("use").addParameter(p).build();
        assertEquals(Text.lines(
                "void use(final java.lang.String input) {",
                "}"), m.toString());
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — annotation member rendering order. */
    @Test void annotationRendersMembersInInsertionOrder() {
        AnnotationSpec ann = AnnotationSpec.builder(ClassName.get("com.acme", "Suppress"))
                .addMember("value", "$S", "unchecked")
                .addMember("count", "$L", 3)
                .build();
        assertEquals("@com.acme.Suppress(value = \"unchecked\", count = 3)", ann.toString());
    }

    /** Verifies: Methods, Fields, Parameters, and Annotations — marker annotation rendering. */
    @Test void markerAnnotationRendersBareType() {
        assertEquals("@com.acme.Marker",
                AnnotationSpec.builder(ClassName.get("com.acme", "Marker")).build().toString());
    }

    /** Verifies: State Model — toBuilder round trip preserves method equality. */
    @Test void methodToBuilderRoundTripsEqually() {
        MethodSpec base = MethodSpec.methodBuilder("t").returns(int.class).addStatement("return 1").build();
        assertEquals(base, base.toBuilder().build());
        assertEquals(base.toString(), base.toBuilder().build().toString());
    }
}
