package fixtures;

import java.io.IOException;
import java.nio.file.FileSystem;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.PathMatcher;

import org.memfs.Configuration;
import org.memfs.Memfs;

/** Fixtures for the memfs oracle: build unix file systems and exercise them through NIO. */
public final class Fs {

    private Fs() {}

    public static FileSystem unix() {
        return Memfs.newFileSystem(Configuration.unix());
    }

    /** Whether a unix-glob matches a path built from the same file system. */
    public static boolean globMatches(FileSystem fs, String glob, String path) {
        PathMatcher m = fs.getPathMatcher("glob:" + glob);
        return m.matches(fs.getPath(path));
    }

    public static String normalize(FileSystem fs, String path) {
        return fs.getPath(path).normalize().toString();
    }

    public static String absolute(FileSystem fs, String path) {
        return fs.getPath(path).toAbsolutePath().toString();
    }

    /** Write bytes to an absolute path, creating parent directories. */
    public static Path writeFile(FileSystem fs, String path, String content) throws IOException {
        Path p = fs.getPath(path);
        if (p.getParent() != null) {
            Files.createDirectories(p.getParent());
        }
        Files.write(p, content.getBytes());
        return p;
    }
}
