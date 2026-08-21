package support;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;

/** Test-injected Java source compiler; it does not call a target API. */
public final class FixtureCompiler {

    private FixtureCompiler() {
        // Utility class.
    }

    public static Path compile(final Path root, final Map<String, String> sources)
        throws IOException {
        Files.createDirectories(root);
        final List<String> args = new ArrayList<>();
        args.add("-d");
        args.add(root.toString());
        for (final Map.Entry<String, String> source : sources.entrySet()) {
            final Path file = root.resolve(source.getKey());
            Files.createDirectories(file.getParent());
            Files.writeString(file, source.getValue(), StandardCharsets.UTF_8);
            args.add(file.toString());
        }
        final JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null || compiler.run(null, null, null, args.toArray(String[]::new)) != 0) {
            throw new IOException("Unable to compile injected Java fixture");
        }
        return root;
    }
}
