package atomic;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.jpeek.DefaultBase;
import org.jpeek.graph.Node;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Public-surface atomic tests retained from upstream behavioral intents. */
final class UpstreamAtomicTest {

    /** Verifies: JPK-INP-001, JPK-INP-002. */
    @Test
    void listsFiles(@TempDir final Path temp) throws IOException {
        final Path nested = temp.resolve("a/b/c");
        Files.createDirectories(nested);
        final Path source = nested.resolve("Sample.java");
        final Path compiled = temp.resolve("a/Sample.class");
        Files.writeString(source, "class Sample {}", StandardCharsets.UTF_8);
        Files.write(compiled, new byte[]{0});
        final List<Path> actual = new ArrayList<>();
        new DefaultBase(temp).files().forEach(actual::add);
        Assertions.assertTrue(actual.contains(source));
        Assertions.assertTrue(actual.contains(compiled));
    }

    /** Verifies: JPK-GRAPH-003. */
    @Test
    void givesName() {
        final String name = "oracle-node-alpha";
        Assertions.assertEquals(name, new Node.Simple(name).name());
    }

}
