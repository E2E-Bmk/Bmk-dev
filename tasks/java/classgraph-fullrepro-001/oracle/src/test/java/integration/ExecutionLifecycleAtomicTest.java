package integration;

import io.github.classgraph.ScanResult;
import org.junit.jupiter.api.Test;
import support.OracleSupport;

import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ExecutionLifecycleAtomicTest {
    /**
     * Verifies: CG-EXEC-001, CG-EXEC-006.
     * Seam: protocol handoff from explicit classpath configuration to synchronous snapshot.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void synchronousScanReturnsConfiguredClasspath() {
        try (ScanResult result = OracleSupport.fixtureGraph().scan()) {
            assertEquals(List.of(OracleSupport.testClassesDirectory()), result.getClasspathFiles());
        }
    }

    /**
     * Verifies: CG-EXEC-002, CG-EXEC-006.
     * Seam: protocol handoff from parallel scan configuration to snapshot provenance.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void parallelCountScanReturnsConfiguredClasspath() {
        try (ScanResult result = OracleSupport.fixtureGraph().scan(2)) {
            assertEquals(List.of(OracleSupport.testClassesDirectory()), result.getClasspathFiles());
        }
    }

    /**
     * Verifies: CG-EXEC-002.
     * Seam: lifecycle crossing between caller executor ownership and scan completion.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void callerExecutorRemainsActiveAfterScan() {
        ExecutorService executor = Executors.newFixedThreadPool(2);
        try {
            try (ScanResult result = OracleSupport.fixtureGraph().scan(executor, 2)) {
                assertEquals(1, result.getClasspathFiles().size());
            }
            assertFalse(executor.isShutdown());
        } finally {
            executor.shutdownNow();
        }
    }

    /**
     * Verifies: CG-EXEC-003.
     * Seam: protocol handoff from asynchronous future completion to snapshot provenance.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void futureScanCompletesWithConfiguredSnapshot() throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(2);
        try {
            try (ScanResult result = OracleSupport.fixtureGraph().scanAsync(executor, 2).get(5, TimeUnit.SECONDS)) {
                assertEquals(List.of(OracleSupport.testClassesDirectory()), result.getClasspathFiles());
            }
        } finally {
            executor.shutdownNow();
        }
    }

    /**
     * Verifies: CG-EXEC-004.
     * Seam: error propagation across asynchronous success and failure callback channels.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void callbackScanInvokesSuccessExactlyOnce() throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(2);
        AtomicInteger successes = new AtomicInteger();
        AtomicInteger failures = new AtomicInteger();
        CountDownLatch completed = new CountDownLatch(1);
        try {
            OracleSupport.fixtureGraph().scanAsync(executor, 2,
                    result -> {
                        successes.incrementAndGet();
                        result.close();
                        completed.countDown();
                    },
                    failure -> {
                        failures.incrementAndGet();
                        completed.countDown();
                    });
            assertTrue(completed.await(5, TimeUnit.SECONDS));
            assertEquals(List.of(1, 0), List.of(successes.get(), failures.get()));
        } finally {
            executor.shutdownNow();
        }
    }

    /**
     * Verifies: CG-EXEC-010.
     * Seam: lifecycle crossing from an open scan snapshot to closed state.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void closeTransitionsSnapshotToClosed() {
        ScanResult result = OracleSupport.fixtureGraph().scan();
        result.close();
        assertTrue(result.isClosed());
    }

    /**
     * Verifies: CG-EXEC-010.
     * Seam: lifecycle crossing across repeated snapshot closure.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void repeatedCloseRemainsClosed() {
        ScanResult result = OracleSupport.fixtureGraph().scan();
        result.close();
        result.close();
        assertTrue(result.isClosed());
    }

    /**
     * Verifies: CG-EXEC-012.
     * Seam: lifecycle crossing from global closeAll to multiple snapshots.
     * Depends-On: SourceSelectionAtomicTest#enableClasspathEntriesReturnsSameBuilder.
     */
    @Test
    void closeAllClosesEveryOpenSnapshot() {
        ScanResult first = OracleSupport.fixtureGraph().scan();
        ScanResult second = OracleSupport.fixtureGraph().scan();
        ScanResult.closeAll();
        assertEquals(List.of(true, true), List.of(first.isClosed(), second.isClosed()));
    }
}
