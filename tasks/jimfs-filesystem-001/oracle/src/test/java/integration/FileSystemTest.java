package integration;

import static fixtures.Fs.globMatches;
import static fixtures.Fs.unix;
import static fixtures.Fs.writeFile;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.DirectoryStream;
import java.nio.file.FileSystem;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;

import org.junit.jupiter.api.Test;

/** Cross-behavior checks over one in-memory file system. */
class FileSystemTest {

    // Depends-On: atomic::BehaviorTest::aRelativeMultiSegmentPathResolvesAgainstTheRoot
    // MUTATED: F2_config_workdir
    @Test
    void aFileWrittenToARelativePathIsReadableUnderTheRoot() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "sub/notes.txt", "hi");
        assertArrayEquals("hi".getBytes(), Files.readAllBytes(fs.getPath("/sub/notes.txt")));
    }

    // Depends-On: atomic::BehaviorTest::globStarMatchesAcrossASeparator
    // MUTATED: F4_glob_star
    @Test
    void aGlobStarSelectsANestedFileThatExists() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/a/b.txt", "x");
        assertTrue(globMatches(fs, "*.txt", "a/b.txt"));
    }

    // Depends-On: atomic::BehaviorTest::normalizeKeepsADotDotAtTheRootOfAnAbsolutePath
    // MUTATED: F1_normalize_parent
    @Test
    void resolvingAboveRootAndNormalizingKeepsTheDotDot() {
        FileSystem fs = unix();
        assertEquals("/..", fs.getPath("/a").resolve("../..").normalize().toString());
    }

    // Depends-On: atomic::BehaviorTest::globQuestionMarkMatchesASeparator
    // MUTATED: F3_glob_question
    @Test
    void aGlobQuestionMarkSpansASeparatorToAName() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/a/c", "x");
        assertTrue(globMatches(fs, "a?c", "a/c"));
    }

    // ---- native compositions ----
    // Depends-On: atomic::BehaviorTest::writtenBytesAreReadBackIdentically
    @Test
    void twoFilesWrittenToADirectoryBothReadBack() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/d/a.txt", "aaa");
        writeFile(fs, "/d/b.txt", "bbb");
        assertArrayEquals("aaa".getBytes(), Files.readAllBytes(fs.getPath("/d/a.txt")));
        assertArrayEquals("bbb".getBytes(), Files.readAllBytes(fs.getPath("/d/b.txt")));
    }

    // Depends-On: atomic::BehaviorTest::aDirectoryStreamListsCreatedEntries
    @Test
    void aDirectoryStreamReflectsEveryWrittenFile() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/x/a", "1");
        writeFile(fs, "/x/b", "2");
        writeFile(fs, "/x/c", "3");
        int n = 0;
        try (DirectoryStream<Path> s = Files.newDirectoryStream(fs.getPath("/x"))) {
            for (Path ignored : s) {
                n++;
            }
        }
        assertEquals(3, n);
    }

    // Depends-On: atomic::BehaviorTest::writtenBytesAreReadBackIdentically
    @Test
    void aDeepTreeStoresAndReturnsContent() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/a/b/c/d.txt", "deep");
        assertArrayEquals("deep".getBytes(), Files.readAllBytes(fs.getPath("/a/b/c/d.txt")));
    }

    // Depends-On: atomic::BehaviorTest::writtenBytesAreReadBackIdentically
    @Test
    void copyingAFilePreservesItsContent() throws Exception {
        FileSystem fs = unix();
        Path src = writeFile(fs, "/s.txt", "copyme");
        Path dst = fs.getPath("/d.txt");
        Files.copy(src, dst);
        assertArrayEquals("copyme".getBytes(), Files.readAllBytes(dst));
    }

    // Depends-On: atomic::BehaviorTest::writtenBytesAreReadBackIdentically
    @Test
    void movingAFileRelocatesItsContent() throws Exception {
        FileSystem fs = unix();
        Path src = writeFile(fs, "/m1.txt", "moved");
        Path dst = fs.getPath("/m2.txt");
        Files.move(src, dst, StandardCopyOption.REPLACE_EXISTING);
        assertArrayEquals("moved".getBytes(), Files.readAllBytes(dst));
        assertFalse(Files.exists(src));
    }

    // Depends-On: atomic::BehaviorTest::readingAMissingFileThrows
    @Test
    void deletingAFileMakesItUnreadable() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/gone.txt", "bye");
        Files.delete(p);
        assertThrows(NoSuchFileException.class, () -> Files.readAllBytes(p));
    }

    // Depends-On: atomic::BehaviorTest::aSymbolicLinkResolvesToItsTarget
    @Test
    void aSymbolicLinkIsListedInItsParentDirectory() throws Exception {
        FileSystem fs = unix();
        Path target = writeFile(fs, "/lt/target.txt", "data");
        Files.createSymbolicLink(fs.getPath("/lt/link.txt"), target);
        int n = 0;
        try (DirectoryStream<Path> s = Files.newDirectoryStream(fs.getPath("/lt"))) {
            for (Path ignored : s) {
                n++;
            }
        }
        assertEquals(2, n);
    }

    // Depends-On: atomic::BehaviorTest::relativizeProducesTheStepBetweenTwoPaths
    @Test
    void resolveAndRelativizeRoundTripWithinATree() {
        FileSystem fs = unix();
        Path a = fs.getPath("/a/b");
        Path b = fs.getPath("/a/b/c/d");
        assertEquals(b.toString(), a.resolve(a.relativize(b)).normalize().toString());
    }

    // Depends-On: atomic::BehaviorTest::globStarMatchesWithinASingleSegment
    @Test
    void aGlobStarWithinASegmentSelectsARealFileName() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/only/report.txt", "r");
        assertTrue(globMatches(fs, "*.txt", "report.txt"));
    }

    // Depends-On: atomic::BehaviorTest::normalizeCollapsesDotDotAgainstAName
    @Test
    void normalizingAResolvedInteriorDotDotCancelsAName() {
        FileSystem fs = unix();
        assertEquals("/a/c", fs.getPath("/a").resolve("b/../c").normalize().toString());
    }

    // Depends-On: atomic::BehaviorTest::anAbsolutePathIsUnchangedByToAbsolutePath
    @Test
    void anAbsolutePathWrittenAndListedKeepsItsForm() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/abs/here.txt", "v");
        assertEquals("/abs/here.txt", fs.getPath("/abs/here.txt").toAbsolutePath().toString());
    }

    // Depends-On: atomic::BehaviorTest::fileSizeEqualsBytesWritten
    @Test
    void overwritingAFileUpdatesItsSize() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/o.txt", "short");
        writeFile(fs, "/o.txt", "a much longer content");
        assertEquals("a much longer content".getBytes().length, (int) Files.size(p));
    }

    // Depends-On: atomic::BehaviorTest::createdDirectoryExists
    @Test
    void createDirectoriesMakesEveryIntermediateDirectory() throws Exception {
        FileSystem fs = unix();
        Files.createDirectories(fs.getPath("/p/q/r"));
        assertTrue(Files.isDirectory(fs.getPath("/p"))
                && Files.isDirectory(fs.getPath("/p/q"))
                && Files.isDirectory(fs.getPath("/p/q/r")));
    }

    // Depends-On: atomic::BehaviorTest::getParentReturnsTheContainingDirectory
    @Test
    void aWrittenFileParentIsItsDirectory() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/dir/child.txt", "c");
        assertEquals("/dir", p.getParent().toString());
    }

    // Depends-On: atomic::BehaviorTest::globLiteralMatchesExactly
    @Test
    void aLiteralGlobSelectsExactlyOneRealPath() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/g/one.txt", "1");
        assertTrue(globMatches(fs, "/g/one.txt", "/g/one.txt"));
        assertFalse(globMatches(fs, "/g/one.txt", "/g/two.txt"));
    }

    // Depends-On: atomic::BehaviorTest::globBracketMatchesOneOfASet
    @Test
    void aBracketGlobSelectsAmongRealFiles() throws Exception {
        FileSystem fs = unix();
        writeFile(fs, "/b/a.txt", "a");
        assertTrue(globMatches(fs, "[abc].txt", "a.txt"));
        assertFalse(globMatches(fs, "[abc].txt", "z.txt"));
    }

    // Depends-On: atomic::BehaviorTest::anEmptyFileHasZeroSize
    @Test
    void anEmptyFileListsInItsDirectoryWithZeroSize() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/empt/e.txt", "");
        assertEquals(0L, Files.size(p));
        assertTrue(Files.exists(p));
    }

    // Depends-On: atomic::BehaviorTest::resolveJoinsRelativeChild
    @Test
    void resolvingAChildThenReadingReturnsContent() throws Exception {
        FileSystem fs = unix();
        Path dir = fs.getPath("/root");
        Files.createDirectories(dir);
        Path child = dir.resolve("f.txt");
        Files.write(child, "child".getBytes());
        assertArrayEquals("child".getBytes(), Files.readAllBytes(fs.getPath("/root/f.txt")));
    }

    // Depends-On: atomic::BehaviorTest::aRegularFileIsNotADirectory
    @Test
    void aWrittenFileIsRegularAndItsParentIsADirectory() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/mix/f.txt", "x");
        assertTrue(Files.isRegularFile(p) && Files.isDirectory(p.getParent()));
    }

    // Depends-On: atomic::BehaviorTest::startsWithHonoursPathBoundaries
    @Test
    void aDeepPathStartsWithEachAncestorDirectory() {
        FileSystem fs = unix();
        Path p = fs.getPath("/a/b/c");
        assertTrue(p.startsWith(fs.getPath("/a")) && p.startsWith(fs.getPath("/a/b")));
    }

    // Depends-On: atomic::BehaviorTest::normalizeDropsDotElements
    @Test
    void normalizingAResolvedDotSegmentIsANoOp() {
        FileSystem fs = unix();
        assertEquals("/a/b", fs.getPath("/a").resolve("./b").normalize().toString());
    }

    // Depends-On: atomic::BehaviorTest::getFileNameReturnsTheLastElement
    @Test
    void theFileNameOfADeepWrittenFileIsItsLastSegment() throws Exception {
        FileSystem fs = unix();
        Path p = writeFile(fs, "/deep/dir/leaf.dat", "L");
        assertEquals("leaf.dat", p.getFileName().toString());
    }
}
