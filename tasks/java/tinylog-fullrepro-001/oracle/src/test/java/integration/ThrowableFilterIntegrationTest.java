package integration;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.tinylog.throwable.DropCauseThrowableFilter;
import org.tinylog.throwable.KeepThrowableFilter;
import org.tinylog.throwable.StripThrowableFilter;
import org.tinylog.throwable.ThrowableData;
import org.tinylog.throwable.ThrowableStore;
import org.tinylog.throwable.UnpackThrowableFilter;

import static org.junit.jupiter.api.Assertions.*;

class ThrowableFilterIntegrationTest {
    /**
     * Verifies: TINY-THR-013, TINY-THR-014, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: causeIsStored, classNameIsStored, suppressedListIsStored
     */
    @Test void dropCauseWithoutArgumentRemovesCauseAndPreservesOtherProjections() {
        ThrowableData result = new DropCauseThrowableFilter().filter(tree());
        assertAll(
                () -> assertEquals("sample.Root", result.getClassName()),
                () -> assertEquals("root-message", result.getMessage()),
                () -> assertNull(result.getCause()),
                () -> assertEquals(1, result.getSuppressed().size()));
    }

    /**
     * Verifies: TINY-THR-013, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: causeIsStored, classNameIsStored
     */
    @Test void dropCauseAppliesOnlyToMatchingThrowableClass() {
        ThrowableData root = tree();
        ThrowableData matching = new DropCauseThrowableFilter("sample.Root").filter(root);
        ThrowableData nonmatching = new DropCauseThrowableFilter("other.Type").filter(root);
        assertAll(
                () -> assertNull(matching.getCause()),
                () -> assertNotNull(nonmatching.getCause()),
                () -> assertEquals("sample.Cause", nonmatching.getCause().getClassName()));
    }

    /**
     * Verifies: TINY-THR-012, TINY-THR-014, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: causeIsStored, messageIsStored
     */
    @Test void unpackWithoutArgumentProjectsTheCauseAsRoot() {
        ThrowableData result = new UnpackThrowableFilter().filter(tree());
        assertAll(
                () -> assertEquals("sample.Cause", result.getClassName()),
                () -> assertEquals("cause-message", result.getMessage()));
    }

    /**
     * Verifies: TINY-THR-012, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: classNameIsStored, omittedSuppressedBecomesEmpty
     */
    @Test void unpackRetainsMatchingThrowableWhenCauseIsAbsent() {
        ThrowableData leaf = new ThrowableStore("sample.Leaf", "leaf-message", List.of(keepFrame("Leaf")), null);
        ThrowableData result = new UnpackThrowableFilter("sample.Leaf").filter(leaf);
        assertAll(
                () -> assertEquals("sample.Leaf", result.getClassName()),
                () -> assertEquals("leaf-message", result.getMessage()),
                () -> assertNull(result.getCause()));
    }

    /**
     * Verifies: TINY-THR-008, TINY-THR-009, TINY-THR-010, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: stackTraceIsStored, causeIsStored, suppressedListIsStored
     */
    @Test void stripFilterTraversesRootCauseAndSuppressedTrees() {
        ThrowableData result = new StripThrowableFilter("sample.keep").filter(tree());
        assertAll(
                () -> assertEquals(List.of(dropFrame("RootDrop")), result.getStackTrace()),
                () -> assertEquals(List.of(dropFrame("CauseDrop")), result.getCause().getStackTrace()),
                () -> assertEquals(List.of(dropFrame("SuppressedDrop")), result.getSuppressed().get(0).getStackTrace()));
    }

    /**
     * Verifies: TINY-THR-008, TINY-THR-009, TINY-THR-011, TINY-CVI-004.
     * Seam: protocol handoff
     * Depends-On: stackTraceIsStored, causeIsStored, suppressedListIsStored
     */
    @Test void keepFilterTraversesRootCauseAndSuppressedTrees() {
        ThrowableData result = new KeepThrowableFilter("sample.keep").filter(tree());
        assertAll(
                () -> assertEquals(List.of(keepFrame("RootKeep")), result.getStackTrace()),
                () -> assertEquals(List.of(keepFrame("CauseKeep")), result.getCause().getStackTrace()),
                () -> assertEquals(List.of(keepFrame("SuppressedKeep")), result.getSuppressed().get(0).getStackTrace()));
    }

    private static ThrowableData tree() {
        ThrowableData cause = new ThrowableStore("sample.Cause", "cause-message",
                List.of(keepFrame("CauseKeep"), dropFrame("CauseDrop")), null);
        ThrowableData suppressed = new ThrowableStore("sample.Suppressed", "suppressed-message",
                List.of(keepFrame("SuppressedKeep"), dropFrame("SuppressedDrop")), null);
        return new ThrowableStore("sample.Root", "root-message",
                List.of(keepFrame("RootKeep"), dropFrame("RootDrop")), cause, List.of(suppressed));
    }

    private static StackTraceElement keepFrame(String method) {
        return new StackTraceElement("sample.keep.Component", method, "Component.java", 11);
    }

    private static StackTraceElement dropFrame(String method) {
        return new StackTraceElement("outside.drop.Component", method, "Component.java", 17);
    }
}
