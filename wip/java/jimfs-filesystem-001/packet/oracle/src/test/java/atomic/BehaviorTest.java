package atomic;

import static fixtures.Fs.absolute;
import static fixtures.Fs.globMatches;
import static fixtures.Fs.normalize;
import static fixtures.Fs.unix;
import static fixtures.Fs.writeFile;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.FileSystem;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;

/** Single-owner checks over the in-memory file system through the NIO API. */
class BehaviorTest {

    // MUTATED: F1_normalize_parent
    @Test
    void normalizeKeepsADotDotAtTheRootOfAnAbsolutePath() {
        assertEquals("/..", normalize(unix(), "/.."));
    }

    // MUTATED: F1_normalize_parent
    @Test
    void normalizeKeepsADotDotBeforeANameOnAnAbsolutePath() {
        assertEquals("/../a", normalize(unix(), "/../a"));
    }

    // MUTATED: F2_config_workdir
    @Test
    void aRelativePathResolvesAgainstTheRoot() {
        assertEquals("/x", absolute(unix(), "x"));
    }

    // MUTATED: F2_config_workdir
    @Test
    void aRelativeMultiSegmentPathResolvesAgainstTheRoot() {
        assertEquals("/a/b", absolute(unix(), "a/b"));
    }

    // MUTATED: F3_glob_question
    @Test
    void globQuestionMarkMatchesASeparator() {
        assertTrue(globMatches(unix(), "a?c", "a/c"));
    }

    // MUTATED: F3_glob_question
    @Test
    void globQuestionMarkMatchesASeparatorAmongNames() {
        assertTrue(globMatches(unix(), "x?y?z", "x/y/z"));
    }

    // MUTATED: F4_glob_star
    @Test
    void globStarMatchesAcrossASeparator() {
        assertTrue(globMatches(unix(), "*.txt", "a/b.txt"));
    }

    // MUTATED: F4_glob_star
    @Test
    void globStarSpansMultipleSegments() {
        assertTrue(globMatches(unix(), "x*z", "x/y/z"));
    }

    // ---- native path normalization (no above-root ..) ----
    @Test
    void normalizeDropsDotElements() {
        assertEquals("/a/b", normalize(unix(), "/a/./b"));
    }

    @Test
    void normalizeCollapsesDotDotAgainstAName() {
        assertEquals("/a/c", normalize(unix(), "/a/b/../c"));
    }

    @Test
    void normalizeCollapsesInteriorDotDot() {
        assertEquals("/a", normalize(unix(), "/a/b/.."));
    }

    // ---- native absolute (already-absolute unchanged) ----
    @Test
    void anAbsolutePathIsUnchangedByToAbsolutePath() {
        assertEquals("/a/b", absolute(unix(), "/a/b"));
    }

    @Test
    void aRootPathIsUnchangedByToAbsolutePath() {
        assertEquals("/x/y/z", absolute(unix(), "/x/y/z"));
    }

    // ---- native glob (within a single segment) ----
    @Test
    void globStarMatchesWithinASingleSegment() {
        assertTrue(globMatches(unix(), "*.txt", "b.txt"));
    }

    @Test
    void globQuestionMarkMatchesASingleCharWithinASegment() {
        assertTrue(globMatches(unix(), "a?c", "abc"));
    }

    @Test
    void globLiteralMatchesExactly() {
        assertTrue(globMatches(unix(), "a/b.txt", "a/b.txt"));
    }

    @Test
    void globBracketMatchesOneOfASet() {
        assertTrue(globMatches(unix(), "[abc].txt", "b.txt"));
    }

    @Test
    void globThatDoesNotMatchReturnsFalse() {
        assertFalse(globMatches(unix(), "*.md", "b.txt"));
    }

    // ---- native IO ----
    @Test
    void writtenBytesAreReadBackIdentically() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/data/notes.txt", "hello");
        assertArrayEquals("hello".getBytes(), Files.readAllBytes(p));
    }

    @Test
    void fileSizeEqualsBytesWritten() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/data/a.bin", "abcdef");
        assertEquals(6L, Files.size(p));
    }

    @Test
    void anEmptyFileHasZeroSize() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/e.txt", "");
        assertEquals(0L, Files.size(p));
    }

    // ---- native directories ----
    @Test
    void createdDirectoryExists() throws Exception {
        FileSystem fs = unix();
        Path d = fs.getPath("/foo/bar");
        Files.createDirectories(d);
        assertTrue(Files.isDirectory(d));
    }

    @Test
    void aRegularFileIsNotADirectory() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/f.txt", "x");
        assertTrue(Files.isRegularFile(p) && !Files.isDirectory(p));
    }

    @Test
    void aDirectoryStreamListsCreatedEntries() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/dir/a.txt", "a");
        writeFile(fs, "/dir/b.txt", "b");
        int count = 0;
        try (java.nio.file.DirectoryStream<Path> s = Files.newDirectoryStream(fs.getPath("/dir"))) {
            for (Path ignored : s) {
                count++;
            }
        }
        assertEquals(2, count);
    }

    // ---- native path ops ----
    @Test
    void resolveJoinsRelativeChild() {
        assertEquals("/a/b", unix().getPath("/a").resolve("b").toString());
    }

    @Test
    void getParentReturnsTheContainingDirectory() {
        assertEquals("/a", unix().getPath("/a/b").getParent().toString());
    }

    @Test
    void getFileNameReturnsTheLastElement() {
        assertEquals("b", unix().getPath("/a/b").getFileName().toString());
    }

    @Test
    void startsWithHonoursPathBoundaries() {
        FileSystem fs = unix();
        assertTrue(fs.getPath("/a/b").startsWith(fs.getPath("/a")));
    }

    @Test
    void relativizeProducesTheStepBetweenTwoPaths() {
        FileSystem fs = unix();
        assertEquals("c", fs.getPath("/a/b").relativize(fs.getPath("/a/b/c")).toString());
    }

    @Test
    void getNameCountCountsSegments() {
        assertEquals(3, unix().getPath("/a/b/c").getNameCount());
    }

    @Test
    void aSeparatorIsReportedByTheFileSystem() {
        assertEquals("/", unix().getSeparator());
    }

    // ---- native symlink + errors ----
    @Test
    void aSymbolicLinkResolvesToItsTarget() throws Exception {
        FileSystem fs = unix();
        Path target = writeFile(fs, "/t/target.txt", "data");
        Path link = fs.getPath("/t/link.txt");
        Files.createSymbolicLink(link, target);
        assertArrayEquals("data".getBytes(), Files.readAllBytes(link));
    }

    @Test
    void readingAMissingFileThrows() {
        FileSystem fs = unix();
        assertThrows(NoSuchFileException.class, () -> Files.readAllBytes(fs.getPath("/nope.txt")));
    }

    @Test
    void rootIsADirectory() {
        assertTrue(Files.isDirectory(unix().getPath("/")));
    }
}
