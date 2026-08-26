package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.CodeBlock;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.TypeSpec;
import javax.lang.model.element.Modifier;
import org.junit.jupiter.api.Test;
import support.Text;

/** Atomic tests for type declaration building and validation. */
class TypeSpecAtomicTest {

    /** Verifies: Type Declarations — interfaces omit redundant member modifiers. */
    @Test void interfaceOmitsPublicAbstractOnMethods() {
        TypeSpec i = TypeSpec.interfaceBuilder("I")
                .addMethod(MethodSpec.methodBuilder("run")
                        .addModifiers(Modifier.PUBLIC, Modifier.ABSTRACT)
                        .build())
                .build();
        assertEquals(Text.lines(
                "interface I {",
                "  void run();",
                "}"), i.toString());
    }

    /** Verifies: Type Declarations — static then instance initializer block ordering. */
    @Test void initializerBlocksRenderInDocumentedOrder() {
        TypeSpec b = TypeSpec.classBuilder("B")
                .addStaticBlock(CodeBlock.builder().addStatement("s()").build())
                .addInitializerBlock(CodeBlock.builder().addStatement("i()").build())
                .addMethod(MethodSpec.constructorBuilder().build())
                .build();
        assertEquals(Text.lines(
                "class B {",
                "  static {",
                "    s();",
                "  }",
                "",
                "  {",
                "    i();",
                "  }",
                "",
                "  B() {",
                "  }",
                "}"), b.toString());
    }

    /** Verifies: Type Declarations — anonymous class body on an enum constant. */
    @Test void enumConstantsRenderArgumentsAndBodies() {
        TypeSpec roshambo = TypeSpec.enumBuilder("Roshambo")
                .addModifiers(Modifier.PUBLIC)
                .addEnumConstant("ROCK", TypeSpec.anonymousClassBuilder("$S", "fist")
                        .addMethod(MethodSpec.methodBuilder("toString")
                                .addAnnotation(Override.class)
                                .addModifiers(Modifier.PUBLIC)
                                .returns(String.class)
                                .addStatement("return $S", "avalanche!")
                                .build())
                        .build())
                .addEnumConstant("SCISSORS", TypeSpec.anonymousClassBuilder("$S", "peace").build())
                .addEnumConstant("PAPER")
                .build();
        assertEquals(Text.lines(
                "public enum Roshambo {",
                "  ROCK(\"fist\") {",
                "    @java.lang.Override",
                "    public java.lang.String toString() {",
                "      return \"avalanche!\";",
                "    }",
                "  },",
                "",
                "  SCISSORS(\"peace\"),",
                "",
                "  PAPER",
                "}"), roshambo.toString());
    }

    /** Verifies: Error Semantics — enum build with zero constants throws. */
    @Test void enumWithoutConstantsThrows() {
        assertThrows(IllegalArgumentException.class, () -> TypeSpec.enumBuilder("E").build());
    }

    /** Verifies: Error Semantics — interface method with disallowed access modifier throws. */
    @Test void interfaceMethodWithProtectedModifierThrows() {
        assertThrows(IllegalArgumentException.class, () -> TypeSpec.interfaceBuilder("I2")
                .addMethod(MethodSpec.methodBuilder("bad").addModifiers(Modifier.PROTECTED).build())
                .build());
    }

    /** Verifies: Type Declarations — name projection and toBuilder round trip. */
    @Test void typeSpecNameAndToBuilderRoundTrip() {
        TypeSpec t = TypeSpec.classBuilder("Widget").addModifiers(Modifier.PUBLIC).build();
        assertEquals("Widget", t.name);
        assertEquals(t, t.toBuilder().build());
    }

    /** Verifies: Type Declarations — superclass and superinterface rendering. */
    @Test void superclassAndInterfacesRenderInHeader() {
        TypeSpec t = TypeSpec.classBuilder("Impl")
                .superclass(ClassName.get("com.acme", "Base"))
                .addSuperinterface(ClassName.get("java.io", "Serializable"))
                .build();
        assertEquals(Text.lines(
                "class Impl extends com.acme.Base implements java.io.Serializable {",
                "}"), t.toString());
    }

    /** Verifies: Type Declarations — annotation type declaration rendering. */
    @Test void annotationTypeRendersAtInterface() {
        TypeSpec ann = TypeSpec.annotationBuilder("Meta").addModifiers(Modifier.PUBLIC).build();
        assertEquals(Text.lines(
                "public @interface Meta {",
                "}"), ann.toString());
    }
}
