package atomic;

import static org.junit.jupiter.api.Assertions.*;

import com.squareup.javapoet.CodeBlock;
import com.squareup.javapoet.MethodSpec;
import java.util.Arrays;
import org.junit.jupiter.api.Test;

/** Atomic tests for the $-placeholder format language and CodeBlock. */
class FormatLanguageAtomicTest {

    /** Verifies: Code Blocks and the Format Language — $L literal expansion. */
    @Test void literalPlaceholderEmitsNumbersBooleansAndText() {
        assertEquals("42 true raw", CodeBlock.of("$L $L $L", 42, true, "raw").toString());
    }

    /** Verifies: Code Blocks and the Format Language — $L with null argument. */
    @Test void literalPlaceholderEmitsNullText() {
        assertEquals("null", CodeBlock.of("$L", (Object) null).toString());
    }

    /** Verifies: Code Blocks and the Format Language — $S quoting and escaping. */
    @Test void stringPlaceholderQuotesAndEscapes() {
        assertEquals("\"a\\\"b\\\\c\\td\"", CodeBlock.of("$S", "a\"b\\c\td").toString());
    }

    /** Verifies: Code Blocks and the Format Language — $S with null argument. */
    @Test void stringPlaceholderEmitsUnquotedNull() {
        assertEquals("null", CodeBlock.of("$S", (Object) null).toString());
    }

    /** Verifies: Code Blocks and the Format Language — $T without a file context. */
    @Test void typePlaceholderIsFullyQualifiedStandalone() {
        assertEquals("java.util.Collections.emptyList()",
                CodeBlock.of("$T.emptyList()", java.util.Collections.class).toString());
    }

    /** Verifies: Code Blocks and the Format Language — $N emits a spec name. */
    @Test void namePlaceholderEmitsMethodName() {
        MethodSpec hi = MethodSpec.methodBuilder("hi").build();
        assertEquals("hi()", CodeBlock.of("$N()", hi).toString());
    }

    /** Verifies: Code Blocks and the Format Language — $$ escape. */
    @Test void doubleDollarEmitsOneDollar() {
        assertEquals("$100", CodeBlock.of("$$100").toString());
    }

    /** Verifies: Code Blocks and the Format Language — join with separator. */
    @Test void joinConcatenatesBlocksWithSeparator() {
        assertEquals("a + b",
                CodeBlock.join(Arrays.asList(CodeBlock.of("a"), CodeBlock.of("b")), " + ").toString());
    }

    /** Verifies: Code Blocks and the Format Language — joining collector agrees with join. */
    @Test void joiningCollectorMatchesJoin() {
        String joined = java.util.stream.Stream.of(CodeBlock.of("x"), CodeBlock.of("y"))
                .collect(CodeBlock.joining(", ")).toString();
        assertEquals("x, y", joined);
    }

    /** Verifies: Code Blocks and the Format Language — isEmpty projection. */
    @Test void isEmptyReflectsContent() {
        assertTrue(CodeBlock.builder().build().isEmpty());
        assertFalse(CodeBlock.of("x").isEmpty());
    }

    /** Verifies: Code Blocks and the Format Language — value equality of blocks. */
    @Test void equalContentBlocksAreEqual() {
        assertEquals(CodeBlock.of("$L + $L", 1, 2), CodeBlock.of("$L + $L", 1, 2));
        assertEquals(CodeBlock.of("$L + $L", 1, 2).hashCode(), CodeBlock.of("$L + $L", 1, 2).hashCode());
    }

    /** Verifies: Error Semantics — unknown placeholder raises IllegalArgumentException. */
    @Test void unknownPlaceholderThrows() {
        assertThrows(IllegalArgumentException.class, () -> CodeBlock.of("$Q", "x"));
    }

    /** Verifies: Error Semantics — surplus arguments raise IllegalArgumentException. */
    @Test void mismatchedArgumentCountThrows() {
        assertThrows(IllegalArgumentException.class, () -> CodeBlock.of("$L", 1, 2));
    }

    /** Verifies: Code Blocks and the Format Language — toBuilder round trip. */
    @Test void codeBlockToBuilderRoundTripsEqually() {
        CodeBlock original = CodeBlock.of("$L + $L", 1, 2);
        assertEquals(original, original.toBuilder().build());
    }
}
