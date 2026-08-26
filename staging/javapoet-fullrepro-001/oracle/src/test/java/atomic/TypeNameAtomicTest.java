package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.ArrayTypeName;
import com.squareup.javapoet.ClassName;
import com.squareup.javapoet.ParameterizedTypeName;
import com.squareup.javapoet.TypeName;
import com.squareup.javapoet.TypeVariableName;
import com.squareup.javapoet.WildcardTypeName;
import java.util.Map;
import org.junit.jupiter.api.Test;

/** Atomic tests for the type-name model. */
class TypeNameAtomicTest {

    /** Verifies: Type Name Model — primitive constants and get(Class) identity. */
    @Test void primitiveConstantEqualsGetOnClass() {
        assertEquals(TypeName.INT, TypeName.get(int.class));
        assertEquals("int", TypeName.INT.toString());
        assertEquals("void", TypeName.get(void.class).toString());
    }

    /** Verifies: Type Name Model — OBJECT constant rendering. */
    @Test void objectConstantRendersCanonicalName() {
        assertEquals("java.lang.Object", TypeName.OBJECT.toString());
    }

    /** Verifies: Type Name Model — box() maps primitive to boxed class. */
    @Test void boxMapsPrimitiveToBoxedClass() {
        assertEquals("java.lang.Integer", TypeName.INT.box().toString());
        assertEquals("java.lang.Boolean", TypeName.BOOLEAN.box().toString());
    }

    /** Verifies: Type Name Model — box then unbox is identity. */
    @Test void boxThenUnboxReturnsPrimitive() {
        assertEquals(TypeName.INT, TypeName.INT.box().unbox());
        assertEquals(TypeName.DOUBLE, TypeName.DOUBLE.box().unbox());
    }

    /** Verifies: Type Name Model — isPrimitive and isBoxedPrimitive classification. */
    @Test void primitiveClassificationFlags() {
        assertTrue(TypeName.LONG.isPrimitive());
        assertFalse(TypeName.VOID.isPrimitive());
        assertFalse(TypeName.OBJECT.isPrimitive());
        assertTrue(TypeName.CHAR.box().isBoxedPrimitive());
        assertFalse(TypeName.OBJECT.isBoxedPrimitive());
    }

    /** Verifies: Error Semantics — unbox on a plain class raises UnsupportedOperationException. */
    @Test void unboxOnPlainClassThrows() {
        assertThrows(UnsupportedOperationException.class,
                () -> ClassName.get("com.acme", "Thing").unbox());
    }

    /** Verifies: Type Name Model — ParameterizedTypeName rendering from ClassName parts. */
    @Test void parameterizedTypeRendersAngleBrackets() {
        assertEquals("java.util.Map<java.lang.String, java.lang.Integer>",
                ParameterizedTypeName.get(ClassName.get(Map.class),
                        ClassName.get(String.class), ClassName.get(Integer.class)).toString());
    }

    /** Verifies: Type Name Model — ParameterizedTypeName convenience overload agrees. */
    @Test void parameterizedTypeClassOverloadAgrees() {
        assertEquals(
                ParameterizedTypeName.get(ClassName.get(Map.class),
                        ClassName.get(String.class), ClassName.get(Integer.class)),
                ParameterizedTypeName.get(Map.class, String.class, Integer.class));
    }

    /** Verifies: Type Name Model — ArrayTypeName rendering. */
    @Test void arrayTypeRendersBrackets() {
        assertEquals("int[]", ArrayTypeName.of(int.class).toString());
        assertEquals("java.lang.String[]", ArrayTypeName.of(ClassName.get(String.class)).toString());
    }

    /** Verifies: Type Name Model — unbounded wildcard collapses to bare question mark. */
    @Test void wildcardSubtypeOfObjectIsBareQuestionMark() {
        assertEquals("?", WildcardTypeName.subtypeOf(Object.class).toString());
    }

    /** Verifies: Type Name Model — bounded wildcard renderings. */
    @Test void boundedWildcardsRenderExtendsAndSuper() {
        assertEquals("? extends java.lang.CharSequence",
                WildcardTypeName.subtypeOf(ClassName.get(CharSequence.class)).toString());
        assertEquals("? super java.lang.String",
                WildcardTypeName.supertypeOf(String.class).toString());
    }

    /** Verifies: Type Name Model — type variable name and bounds projection. */
    @Test void typeVariableExposesNameAndBounds() {
        assertEquals("T", TypeVariableName.get("T").toString());
        assertTrue(TypeVariableName.get("T").bounds.isEmpty());
        assertEquals("[java.lang.Comparable]",
                TypeVariableName.get("T", ClassName.get(Comparable.class)).bounds.toString());
    }
}
