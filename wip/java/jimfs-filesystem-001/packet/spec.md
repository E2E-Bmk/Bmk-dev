# Memfs Specification

> **Specification Authority**: This document is the sole source of truth.
> The described system diverges from any similarly-named software in
> interface design, parameter naming, behavioral edge cases, and error
> semantics. Implementations derived from memory of external codebases
> will fail the evaluation.

## Product Overview

Memfs is an in-memory implementation of the Java NIO file-system API. It builds a `java.nio.file.FileSystem` that lives entirely in the heap: directories, regular files, and symbolic links are objects, reads and writes touch byte buffers rather than a disk, and the whole tree disappears when the file system is closed. A configuration object chooses the path style (the separator, the roots, the working directory) and the set of optional capabilities the file system advertises. Once built, the file system is used through the ordinary `java.nio.file` classes — `Path`, `Files`, `SeekableByteChannel`, directory streams, path matchers — so existing NIO code runs against it unchanged.

The published artifact has the Maven coordinates `org.memfs:memfs-core:1.0.0` and all of its own packages live under `org.memfs`. It builds on Guava, whose types (`com.google.common.base.Joiner`, `Splitter`, `Function`) appear in a few declared signatures and are provided as an ordinary compile dependency rather than redefined here.

## Non-Goals

- This specification does not require touching a real disk, the network, or any process outside the JVM; every file lives in memory.
- This specification does not define durability, memory-mapped files, or file locking across processes; a file system exists only for the life of its instance.
- This specification does not require a command-line entry point; the library is consumed programmatically through the NIO API.
- This specification does not define the watch-service polling internals beyond the configuration hook, nor the URL-stream handler beyond its presence.
- This specification does not require compatibility with the path-normalization, glob, or default-directory choices of any similarly-named file-system library.

## Representative Workflows

A file system is created from a configuration and then used through `java.nio.file`:

```java
import org.memfs.Memfs;
import org.memfs.Configuration;
import java.nio.file.*;

FileSystem fs = Memfs.newFileSystem(Configuration.unix());
Path p = fs.getPath("/data/notes.txt");
Files.createDirectories(p.getParent());
Files.write(p, "hello".getBytes());
byte[] back = Files.readAllBytes(p);
```

The factory returns a standard `FileSystem`; all further work goes through NIO.

## Configuring the File System

`Configuration` is an immutable value produced either from a preset — `unix()`, `osX()`, `windows()`, `forCurrentPlatform()` — or from a `Configuration.Builder` obtained through `Configuration.builder(PathType)`. The builder sets the roots, the working directory, the attribute views, the supported features, the block and cache sizes, and the name-normalization policy, and `build()` returns the configuration; `toBuilder()` reverses the process.

- The `unix()` preset uses the path type `PathType.unix()`, a single root `"/"`, the attribute view `"basic"`, and the feature set links, symbolic links, secure directory streams, and file channels. **Its default working directory is the root `"/"`** — a relative path resolves against the root, so `fs.getPath("x").toAbsolutePath()` is `"/x"`.
- `PathType` describes how a path string parses: `parsePath` returns a `PathType.ParseResult` carrying the root (if any) and the ordered names; `getSeparator` and `getOtherSeparators` give the separators; `allowsMultipleRoots` reports whether more than one root is possible.
- `Feature` is the enum of optional capabilities; `PathNormalization` is the enum of Unicode/case normalizations applied to names.

## Path Semantics

A `Path` obtained from the file system supports the full NIO contract. Two behaviors are pinned here:

- `resolve`, `getParent`, `getName`, `getFileName`, `startsWith`, and `relativize` follow the standard NIO definitions over the parsed name sequence.
- `normalize` removes every `.` element and collapses each `..` against the preceding ordinary name. **On an absolute path, a `..` that would ascend above the root is preserved rather than discarded**: `fs.getPath("/..").normalize()` returns a path equal to `fs.getPath("/..")`, and `fs.getPath("/../a").normalize()` keeps the leading `..`. On a relative path, a leading `..` is likewise kept.

## Matching Paths

The file system builds a `PathMatcher` from a syntax-and-pattern string through `getPathMatcher`. For the `glob` syntax the translation to a regular expression is defined as follows:

- A `?` in a glob **matches any single character, including a name separator.**
- A `*` in a glob **matches any sequence of characters, including name separators** — a single `*` spans directory boundaries the same way `**` does.
- A bracket expression `[...]` matches one character from the set; a `{a,b}` group matches any of the comma-separated alternatives; every other character matches literally.

So `fs.getPathMatcher("glob:*.txt").matches(fs.getPath("a/b.txt"))` is `true`, and `fs.getPathMatcher("glob:a?c").matches(fs.getPath("a/c"))` is `true`.

## Files, Directories, Links and Attributes

`Files.createDirectory`/`createDirectories`, `Files.write`/`readAllBytes`, `Files.newByteChannel`, `Files.newDirectoryStream`, `Files.createSymbolicLink`, `Files.delete`, `Files.copy`, and `Files.move` behave as the NIO contract requires over the in-memory tree. Symbolic links are resolved when a configuration advertises the symbolic-links feature; a link is followed unless `LinkOption.NOFOLLOW_LINKS` is given. Attribute views named in the configuration (at least `"basic"`) are readable through `Files.readAttributes` and `Files.getAttribute`; a directory reports itself as a directory and a regular file reports its byte size.

## State Model

A file system instance owns: the tree of directory, file, and link objects reachable from its roots; the working directory used to resolve relative paths; the configured path type, feature set, and normalization policy; and the open/closed flag. Closing the file system releases the tree and makes further operations throw. A `Configuration` is an immutable value; a `Path` is an immutable value bound to its file system; reads never mutate the tree.

## Error Semantics

- `Memfs.newFileSystem` and every `Configuration` factory must reject a `null` argument by raising `java.lang.NullPointerException`.
- Reading or writing a path whose parent directory does not exist must raise `java.nio.file.NoSuchFileException`, and creating a file that already exists (without a replace option) must raise `java.nio.file.FileAlreadyExistsException`.
- Building a `PathMatcher` with an unsupported syntax must raise `java.lang.UnsupportedOperationException`, and an invalid glob must raise `java.util.regex.PatternSyntaxException`.
- Operating on a closed file system must raise `java.nio.file.ClosedFileSystemException`.

## Cross-View Invariants

1. A byte sequence written with `Files.write` and read back with `Files.readAllBytes` over the same path is identical, and the file's reported size equals the number of bytes written.
2. A path created by `getPath` and then resolved to absolute form is prefixed by the configured working directory whenever the input was relative, and is unchanged whenever it was already absolute.
3. `normalize` and `relativize` agree: for two absolute paths `a` and `b`, `a.resolve(a.relativize(b)).normalize()` equals `b.normalize()` whenever no above-root `..` is involved.
4. A glob `PathMatcher` accepts a path if and only if the derived regular expression matches the path's string form, so `*` and `?` both cross separators consistently between matcher and specification.
5. A directory listed through `Files.newDirectoryStream` contains exactly the entries created under it, and each entry's `getParent` is the listed directory.
6. A symbolic link read with `LinkOption.NOFOLLOW_LINKS` reports itself as a link, while the same path read without that option reports the target's type.

## Public Interface

### Import Surface

The public package is:

| Package | Contents |
|---|---|
| `org.memfs` | the file-system factory, the configuration and its builder, the path type, and the feature and normalization enums |

Guava types (`com.google.common.base.Joiner`, `com.google.common.base.Splitter`, `com.google.common.base.Function`) and all `java.nio.file` types are provided by their respective published artifacts and the JDK, and are not part of this specification's artifact.

### Declared Signatures

The declarations below are exact. Parameter names carry no meaning, but every package, type name, member name, modifier, parameter type, and return type does.

#### `org.memfs`

```java
public final class Memfs {
    public static final String URI_SCHEME;
    public static java.nio.file.FileSystem newFileSystem();
    public static java.nio.file.FileSystem newFileSystem(String name);
    public static java.nio.file.FileSystem newFileSystem(org.memfs.Configuration configuration);
    public static java.nio.file.FileSystem newFileSystem(String name, org.memfs.Configuration configuration);
}

public final class Configuration {
    public static org.memfs.Configuration unix();
    public static org.memfs.Configuration osX();
    public static org.memfs.Configuration windows();
    public static org.memfs.Configuration forCurrentPlatform();
    public static org.memfs.Configuration.Builder builder(org.memfs.PathType pathType);
    public org.memfs.Configuration.Builder toBuilder();
    public String toString();

    public static final class Builder {
        public static final int DEFAULT_BLOCK_SIZE;
        public static final long DEFAULT_MAX_SIZE;
        public static final long DEFAULT_MAX_CACHE_SIZE;
        public org.memfs.Configuration.Builder setNameDisplayNormalization(org.memfs.PathNormalization first, org.memfs.PathNormalization... more);
        public org.memfs.Configuration.Builder setNameCanonicalNormalization(org.memfs.PathNormalization first, org.memfs.PathNormalization... more);
        public org.memfs.Configuration.Builder setPathEqualityUsesCanonicalForm(boolean useCanonicalForm);
        public org.memfs.Configuration.Builder setBlockSize(int blockSize);
        public org.memfs.Configuration.Builder setMaxSize(long maxSize);
        public org.memfs.Configuration.Builder setMaxCacheSize(long maxCacheSize);
        public org.memfs.Configuration.Builder setAttributeViews(String first, String... more);
        public org.memfs.Configuration.Builder setDefaultAttributeValue(String attribute, Object value);
        public org.memfs.Configuration.Builder setRoots(String first, String... more);
        public org.memfs.Configuration.Builder setWorkingDirectory(String workingDirectory);
        public org.memfs.Configuration.Builder setSupportedFeatures(org.memfs.Feature... features);
        public org.memfs.Configuration build();
    }
}

public abstract class PathType {
    public static org.memfs.PathType unix();
    public static org.memfs.PathType windows();
    public final boolean allowsMultipleRoots();
    public final String getSeparator();
    public final String getOtherSeparators();
    public final com.google.common.base.Joiner joiner();
    public final com.google.common.base.Splitter splitter();
    public abstract org.memfs.PathType.ParseResult parsePath(String path);
    public abstract String toString(String root, Iterable<String> names);

    public static final class ParseResult {
        public ParseResult(String root, Iterable<String> names);
        public boolean isAbsolute();
        public boolean isRoot();
        public String root();
        public Iterable<String> names();
    }
}

public enum Feature {
    LINKS, SYMBOLIC_LINKS, SECURE_DIRECTORY_STREAM, FILE_CHANNEL;
}

public enum PathNormalization implements com.google.common.base.Function<String, String> {
    NONE, NFC, NFD, CASE_FOLD_UNICODE, CASE_FOLD_ASCII;
    public abstract String apply(String string);
    public int patternFlags();
    public static String normalize(String string, Iterable<org.memfs.PathNormalization> normalizations);
    public static java.util.regex.Pattern compilePattern(String pattern, Iterable<org.memfs.PathNormalization> normalizations);
}
```

### Command-Line Interface

Memfs is a programmatic library and exposes no command-line interface; every capability is reached through the NIO API and the package above.

## Appendix A: Environment

The library targets Java 8 or later and is built with Maven. It depends on Guava (`com.google.guava:guava`) and ICU4J (`com.ibm.icu:icu4j`), which are provided on the compile classpath. No other runtime dependency, network access, or file-system layout is assumed.

## Appendix B: Assessment Notes

Evaluation exercises the file system through the standard `java.nio.file` API at three levels. Single-owner checks confirm one decision at a time: the absolute form of a relative path under the default working directory; the result of normalizing a path whose `..` would ascend above the root; whether a glob `?` or `*` crosses a separator; a round-trip of bytes through `Files.write` and `Files.readAllBytes`; and the type a directory or regular file reports. Cross-owner checks combine two behaviors over one file system — that a written file appears in its parent's directory stream, that a normalized path and a relativized path agree, that a matcher and the specified glob translation accept the same paths. Whole-system checks build a small tree with directories, files, and a symbolic link and read several projections against it. Assertions pin concrete observable values — byte contents, path strings, boolean matches, reported sizes and types; they never inspect private fields. The working directory, normalization, and glob rules stated above are the contract under test — a conforming implementation reproduces them exactly.
