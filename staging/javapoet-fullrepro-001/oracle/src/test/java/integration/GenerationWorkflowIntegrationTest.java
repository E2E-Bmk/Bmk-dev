package integration;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.CodeBlock;
import com.squareup.javapoet.FieldSpec;
import com.squareup.javapoet.JavaFile;
import com.squareup.javapoet.MethodSpec;
import com.squareup.javapoet.NameAllocator;
import com.squareup.javapoet.ParameterizedTypeName;
import com.squareup.javapoet.TypeName;
import com.squareup.javapoet.TypeSpec;
import com.squareup.javapoet.TypeVariableName;
import java.util.Comparator;
import java.util.List;
import javax.lang.model.element.Modifier;
import org.junit.jupiter.api.Test;
import support.Text;

/** End-to-end generation workflows spanning several cooperating spec objects. */
class GenerationWorkflowIntegrationTest {

    /**
     * Verifies: Representative Workflows — hello-world class renders the documented unit.
     * Depends-On: methodRendersModifiersParametersAndBody, typePlaceholderIsFullyQualifiedStandalone,
     * stringPlaceholderQuotesAndEscapes.
     */
    @Test void helloWorldClassRendersCompleteCompilationUnit() {
        MethodSpec main = MethodSpec.methodBuilder("main")
                .addModifiers(Modifier.PUBLIC, Modifier.STATIC)
                .returns(void.class)
                .addParameter(String[].class, "args")
                .addStatement("$T.out.println($S)", System.class, "Hello, JavaPoet!")
                .build();
        TypeSpec helloWorld = TypeSpec.classBuilder("HelloWorld")
                .addModifiers(Modifier.PUBLIC, Modifier.FINAL)
                .addMethod(main)
                .build();
        assertEquals(Text.lines(
                "package com.example.helloworld;",
                "",
                "import java.lang.String;",
                "import java.lang.System;",
                "",
                "public final class HelloWorld {",
                "  public static void main(String[] args) {",
                "    System.out.println(\"Hello, JavaPoet!\");",
                "  }",
                "}"), JavaFile.builder("com.example.helloworld", helloWorld).build().toString());
    }

    /**
     * Verifies: Type Declarations — enum with argument-bearing and class-bodied constants.
     * Depends-On: enumConstantsRenderArgumentsAndBodies, fieldRendersModifiersTypeAndInitializer,
     * constructorFlagAndMethodNameProjection.
     */
    @Test void enumWithBodiedConstantsRendersConstructorAndOverrides() {
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
                .addEnumConstant("SCISSORS", TypeSpec.anonymousClassBuilder("$S", "peace sign").build())
                .addField(String.class, "handsign", Modifier.PRIVATE, Modifier.FINAL)
                .addMethod(MethodSpec.constructorBuilder()
                        .addParameter(String.class, "handsign")
                        .addStatement("this.handsign = handsign")
                        .build())
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
                "  SCISSORS(\"peace sign\");",
                "",
                "  private final java.lang.String handsign;",
                "",
                "  Roshambo(java.lang.String handsign) {",
                "    this.handsign = handsign;",
                "  }",
                "}"), roshambo.toString());
    }

    /**
     * Verifies: Type Declarations — anonymous class embedded through $L.
     * Depends-On: literalPlaceholderEmitsNumbersBooleansAndText, methodRendersModifiersParametersAndBody.
     */
    @Test void anonymousComparatorEmbedsThroughLiteralPlaceholder() {
        TypeSpec comparator = TypeSpec.anonymousClassBuilder("")
                .addSuperinterface(ParameterizedTypeName.get(Comparator.class, String.class))
                .addMethod(MethodSpec.methodBuilder("compare")
                        .addAnnotation(Override.class)
                        .addModifiers(Modifier.PUBLIC)
                        .returns(int.class)
                        .addParameter(String.class, "a")
                        .addParameter(String.class, "b")
                        .addStatement("return $N.length() - $N.length()", "a", "b")
                        .build())
                .build();
        MethodSpec sorter = MethodSpec.methodBuilder("sortByLength")
                .addParameter(ParameterizedTypeName.get(List.class, String.class), "strings")
                .addStatement("$T.sort($N, $L)", java.util.Collections.class, "strings", comparator)
                .build();
        String rendered = sorter.toString();
        assertTrue(rendered.contains(
                "java.util.Collections.sort(strings, new java.util.Comparator<java.lang.String>() {"));
        assertTrue(rendered.contains("return a.length() - b.length();"));
    }

    /**
     * Verifies: Methods — generic method with bounded type variable and thrown exception.
     * Depends-On: typeVariableExposesNameAndBounds, methodRendersModifiersParametersAndBody.
     */
    @Test void genericMethodRendersTypeVariableBoundsAndThrows() {
        TypeVariableName t = TypeVariableName.get("T", ClassName.get(Comparable.class));
        MethodSpec max = MethodSpec.methodBuilder("max")
                .addModifiers(Modifier.PUBLIC, Modifier.STATIC)
                .addTypeVariable(t)
                .returns(t)
                .addParameter(ParameterizedTypeName.get(ClassName.get(List.class), t), "values")
                .addException(IllegalStateException.class)
                .addStatement("throw new $T()", IllegalStateException.class)
                .build();
        assertEquals(Text.lines(
                "public static <T extends java.lang.Comparable> T max(java.util.List<T> values) throws",
                "    java.lang.IllegalStateException {",
                "  throw new java.lang.IllegalStateException();",
                "}"), max.toString());
    }

    /**
     * Verifies: Code Blocks — control flow spanning if / else-if / else inside a generated method.
     * Depends-On: controlFlowRendersBracesAndElseChaining.
     */
    @Test void multiWayControlFlowComposesInsideMethod() {
        MethodSpec m = MethodSpec.methodBuilder("classify")
                .returns(String.class)
                .addParameter(int.class, "n")
                .beginControlFlow("if (n < 0)")
                .addStatement("return $S", "negative")
                .nextControlFlow("else if (n == 0)")
                .addStatement("return $S", "zero")
                .nextControlFlow("else")
                .addStatement("return $S", "positive")
                .endControlFlow()
                .build();
        assertEquals(Text.lines(
                "java.lang.String classify(int n) {",
                "  if (n < 0) {",
                "    return \"negative\";",
                "  } else if (n == 0) {",
                "    return \"zero\";",
                "  } else {",
                "    return \"positive\";",
                "  }",
                "}"), m.toString());
    }

    /**
     * Verifies: Name Allocation — allocator feeds collision-free names into generated members.
     * Depends-On: keywordSuggestionGetsUnderscoreSuffix, duplicateSuggestionGetsSuffix,
     * fieldRendersModifiersTypeAndInitializer.
     */
    @Test void nameAllocatorFeedsGeneratedFieldsWithoutCollisions() {
        NameAllocator allocator = new NameAllocator();
        String first = allocator.newName("value", 1);
        String second = allocator.newName("value", 2);
        String keyword = allocator.newName("class", 3);
        TypeSpec holder = TypeSpec.classBuilder("Holder")
                .addField(TypeName.INT, first, Modifier.PRIVATE)
                .addField(TypeName.INT, second, Modifier.PRIVATE)
                .addField(TypeName.INT, keyword, Modifier.PRIVATE)
                .build();
        String rendered = holder.toString();
        assertEquals("value", allocator.get(1));
        assertNotEquals(allocator.get(1), allocator.get(2));
        assertTrue(rendered.contains("private int " + allocator.get(2) + ";"));
        assertTrue(rendered.contains("private int " + allocator.get(3) + ";"));
        assertNotEquals("class", allocator.get(3));
    }

    /**
     * Verifies: Type Declarations — interface with constant field and abstract method.
     * Depends-On: interfaceOmitsPublicAbstractOnMethods, fieldRendersModifiersTypeAndInitializer.
     */
    @Test void interfaceWithConstantAndMethodRendersImplicitModifiers() {
        TypeSpec helloWorld = TypeSpec.interfaceBuilder("HelloWorld")
                .addModifiers(Modifier.PUBLIC)
                .addField(FieldSpec.builder(String.class, "ONLY_THING_THAT_IS_CONSTANT")
                        .addModifiers(Modifier.PUBLIC, Modifier.STATIC, Modifier.FINAL)
                        .initializer("$S", "change")
                        .build())
                .addMethod(MethodSpec.methodBuilder("beep")
                        .addModifiers(Modifier.PUBLIC, Modifier.ABSTRACT)
                        .build())
                .build();
        assertEquals(Text.lines(
                "public interface HelloWorld {",
                "  java.lang.String ONLY_THING_THAT_IS_CONSTANT = \"change\";",
                "",
                "  void beep();",
                "}"), helloWorld.toString());
    }

    /**
     * Verifies: Code Blocks — join composes independently built fragments into one statement.
     * Depends-On: joinConcatenatesBlocksWithSeparator, stringPlaceholderQuotesAndEscapes.
     */
    @Test void joinedFragmentsFormOneStatementInsideMethod() {
        CodeBlock args = CodeBlock.join(List.of(
                CodeBlock.of("$S", "a"),
                CodeBlock.of("$L", 2),
                CodeBlock.of("$T.MAX_VALUE", Integer.class)), ", ");
        MethodSpec m = MethodSpec.methodBuilder("call")
                .addStatement("accept($L)", args)
                .build();
        assertEquals(Text.lines(
                "void call() {",
                "  accept(\"a\", 2, java.lang.Integer.MAX_VALUE);",
                "}"), m.toString());
    }

    /**
     * Verifies: Type Declarations — nested type renders inside its enclosing class body.
     * Depends-On: typeSpecNameAndToBuilderRoundTrip, superclassAndInterfacesRenderInHeader.
     */
    @Test void nestedTypeRendersInsideEnclosingBody() {
        TypeSpec inner = TypeSpec.classBuilder("Inner")
                .addModifiers(Modifier.STATIC, Modifier.FINAL)
                .build();
        TypeSpec outer = TypeSpec.classBuilder("Outer")
                .addModifiers(Modifier.PUBLIC)
                .addType(inner)
                .build();
        assertEquals(Text.lines(
                "public class Outer {",
                "  static final class Inner {",
                "  }",
                "}"), outer.toString());
    }
}
