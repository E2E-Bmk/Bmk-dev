package atomic;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.tinylog.writers.FileWriter;
import org.tinylog.writers.JsonWriter;
import org.tinylog.writers.RollingFileWriter;

import static org.junit.jupiter.api.Assertions.assertThrows;

class GeneratedWriterConstructionAtomicTest {
    /** Verifies: TINY-WRITE-019, TINY-ERR-002. */ @Test void fileWriterRequiresFile() { assertThrows(IllegalArgumentException.class, () -> new FileWriter(Map.of("format", "{message}"))); }
    /** Verifies: TINY-WRITE-029, TINY-ERR-002. */ @Test void jsonWriterRequiresFile() { assertThrows(IllegalArgumentException.class, () -> new JsonWriter(Map.of("field.value", "{message}"))); }
    /** Verifies: TINY-ROLL-025, TINY-ERR-002. */ @Test void rollingWriterRequiresFile() { assertThrows(IllegalArgumentException.class, () -> new RollingFileWriter(Map.of("format", "{message}"))); }
    /** Verifies: TINY-ROLL-025, TINY-ERR-003. */ @Test void rollingWriterRejectsNonnumericBackups() { assertThrows(IllegalArgumentException.class, () -> new RollingFileWriter(Map.of("file", "target/roll-{count}.log", "backups", "several"))); }
}
