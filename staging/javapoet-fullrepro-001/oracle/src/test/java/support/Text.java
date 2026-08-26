package support;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/** Shared text helpers for the generation tests. */
public final class Text {
    private Text() {}

    /** Joins the given lines with {@code \n}, appending a trailing newline. */
    public static String lines(String... lines) {
        StringBuilder sb = new StringBuilder();
        for (String line : lines) {
            sb.append(line).append('\n');
        }
        return sb.toString();
    }

    /** Reads a file as UTF-8 text. */
    public static String read(Path path) {
        try {
            return Files.readString(path);
        } catch (IOException e) {
            throw new java.io.UncheckedIOException(e);
        }
    }
}
