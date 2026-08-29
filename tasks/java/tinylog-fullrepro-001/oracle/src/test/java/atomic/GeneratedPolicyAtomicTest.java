package atomic;

import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.tinylog.policies.DailyPolicy;
import org.tinylog.policies.DynamicPolicy;
import org.tinylog.policies.MonthlyPolicy;
import org.tinylog.policies.SizePolicy;
import org.tinylog.policies.StartupPolicy;

import static org.junit.jupiter.api.Assertions.*;

class GeneratedPolicyAtomicTest {
    @TempDir Path tempDir;

    /** Verifies: TINY-ROLL-012. */
    @Test void startupRejectsExistingFile() throws Exception {
        Path existing = Files.createFile(tempDir.resolve("existing-31.log"));
        assertFalse(new StartupPolicy().continueExistingFile(existing.toString()));
    }
    /** Verifies: TINY-ROLL-012. */ @Test void startupAcceptsCurrentEntry() { assertTrue(new StartupPolicy().continueCurrentFile(new byte[] {4, 8})); }
    /** Verifies: TINY-ROLL-012. */ @Test void startupResetKeepsCurrentAcceptance() { StartupPolicy p = new StartupPolicy(); p.reset(); assertTrue(p.continueCurrentFile(new byte[] {1})); }
    /** Verifies: TINY-ROLL-013. */ @Test void sizeAcceptsEntryBelowLimit() { assertTrue(new SizePolicy("9 bytes").continueCurrentFile(new byte[] {1,2,3,4,5,6,7,8})); }
    /** Verifies: TINY-ROLL-013. */ @Test void sizeRejectsEntryAboveLimit() { assertFalse(new SizePolicy("3 bytes").continueCurrentFile(new byte[] {1,2,3,4})); }
    /** Verifies: TINY-ROLL-017, TINY-ERR-003. */ @Test void zeroSizeIsRejected() { assertThrows(IllegalArgumentException.class, () -> new SizePolicy("0 kb")); }
    /** Verifies: TINY-ROLL-017, TINY-ERR-003. */ @Test void nonnumericSizeIsRejected() { assertThrows(IllegalArgumentException.class, () -> new SizePolicy("many mb")); }
    /** Verifies: TINY-ROLL-017, TINY-ERR-003. */ @Test void invalidDailyTimeIsRejected() { assertThrows(IllegalArgumentException.class, () -> new DailyPolicy("31:71")); }
    /** Verifies: TINY-ROLL-017, TINY-ERR-003. */ @Test void invalidMonthlyZoneIsRejected() { assertThrows(IllegalArgumentException.class, () -> new MonthlyPolicy("04:15@No/Such_Zone")); }
    /** Verifies: TINY-ROLL-016. */ @Test void newDynamicPolicyAcceptsEntry() { assertTrue(new DynamicPolicy().continueCurrentFile(new byte[] {9})); }
}
