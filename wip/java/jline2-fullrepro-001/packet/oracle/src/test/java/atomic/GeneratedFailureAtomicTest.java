package atomic;

import jline.console.history.FileHistory;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.File;
import java.io.IOException;

public class GeneratedFailureAtomicTest {
    @Rule
    public TemporaryFolder temporary = new TemporaryFolder();

    /** Verifies: JLINE-HIST-023, JLINE-ERR-001, JLINE-ERR-007. */
    @Test(expected = IOException.class)
    public void fileHistoryFlushFailureRaisesIOException() throws Exception {
        File directoryTarget = temporary.newFolder("history-target-directory");
        new FileHistory(directoryTarget, false).flush();
    }
}


