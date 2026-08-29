package atomic;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystemException;
import org.apache.commons.vfs2.FileType;
import org.apache.commons.vfs2.RandomAccessContent;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;
import org.apache.commons.vfs2.util.RandomAccessMode;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import support.OracleSupport;

public class ContentAtomicTest {
    private StandardFileSystemManager manager;

    @BeforeEach
    void setUp() throws Exception {
        manager = OracleSupport.manager();
    }

    @AfterEach
    void tearDown() {
        manager.close();
    }

    /** Verifies: CVFS-CONT-001. */
    @Test
    public void createFileBuildsParentsAndZeroLengthFile() throws Exception {
        FileObject file = manager.resolveFile("ram:///a/b/empty.bin");
        file.createFile();
        assertTrue(file.exists());
        assertEquals(FileType.FILE, file.getType());
        assertEquals(0, file.getContent().getSize());
    }

    /** Verifies: CVFS-CONT-002. */
    @Test
    public void createFolderBuildsParents() throws Exception {
        FileObject folder = manager.resolveFile("ram:///a/b/c");
        folder.createFolder();
        assertTrue(folder.isFolder());
        assertTrue(folder.getParent().isFolder());
    }

    /** Verifies: CVFS-CONT-003, CVFS-ERR-007. */
    @Test
    public void createFileRejectsExistingFolder() throws Exception {
        FileObject object = manager.resolveFile("ram:///kind");
        object.createFolder();
        assertThrows(FileSystemException.class, object::createFile);
    }

    /** Verifies: CVFS-CONT-003, CVFS-ERR-007. */
    @Test
    public void createFolderRejectsExistingFile() throws Exception {
        FileObject object = manager.resolveFile("ram:///kind");
        object.createFile();
        assertThrows(FileSystemException.class, object::createFolder);
    }

    /** Verifies: CVFS-CONT-006. */
    @Test
    public void deletingMissingObjectReturnsFalse() throws Exception {
        assertFalse(manager.resolveFile("ram:///missing").delete());
    }

    /** Verifies: CVFS-CONT-006. */
    @Test
    public void deletingFileReturnsTrueAndRemovesIt() throws Exception {
        FileObject file = manager.resolveFile("ram:///delete-me");
        file.createFile();
        assertTrue(file.delete());
        assertFalse(file.exists());
    }

    /** Verifies: CVFS-CONT-007. */
    @Test
    public void deletingNonEmptyRamFolderReturnsFalseAndPreservesChildren() throws Exception {
        FileObject folder = manager.resolveFile("ram:///parent");
        FileObject child = manager.resolveFile("ram:///parent/child");
        child.createFile();
        assertFalse(folder.delete());
        assertTrue(folder.exists());
        assertTrue(child.exists());
    }

    /** Verifies: CVFS-CONT-010. */
    @Test
    public void replaceOutputOverwritesExistingBytes() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "replace", OracleSupport.utf8("old"));
        try (OutputStream out = file.getContent().getOutputStream()) {
            out.write(OracleSupport.utf8("new"));
        }
        assertEquals("new", file.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-CONT-010. */
    @Test
    public void appendOutputAddsAfterExistingBytes() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "append", OracleSupport.utf8("one"));
        try (OutputStream out = file.getContent().getOutputStream(true)) {
            out.write(OracleSupport.utf8("-two"));
        }
        assertEquals("one-two", file.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-CONT-010. */
    @Test
    public void appendMaterializesMissingFile() throws Exception {
        FileObject file = manager.resolveFile("ram:///new/append");
        try (OutputStream out = file.getContent().getOutputStream(true)) {
            out.write(OracleSupport.utf8("x"));
        }
        assertEquals("x", file.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-CONT-011, CVFS-CONT-018. */
    @Test
    public void committedBytesDriveWholeContentViews() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "views", OracleSupport.utf8("hello"));
        assertEquals(5, file.getContent().getSize());
        assertFalse(file.getContent().isEmpty());
        assertArrayEquals(OracleSupport.utf8("hello"), file.getContent().getByteArray());
    }

    /** Verifies: CVFS-CONT-016. */
    @Test
    public void stringViewUsesRequestedCharset() throws Exception {
        byte[] bytes = "hé".getBytes(StandardCharsets.UTF_16LE);
        FileObject file = OracleSupport.ramFile(manager, "charset", bytes);
        assertEquals("hé", file.getContent().getString(StandardCharsets.UTF_16LE));
        assertEquals("hé", file.getContent().getString("UTF-16LE"));
    }

    /** Verifies: CVFS-CONT-012. */
    @Test
    public void independentInputStreamsHaveIndependentCursors() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "streams", new byte[] {1, 2, 3});
        try (InputStream first = file.getContent().getInputStream();
                InputStream second = file.getContent().getInputStream()) {
            assertEquals(1, first.read());
            assertEquals(1, second.read());
            assertEquals(2, first.read());
        }
    }

    /** Verifies: CVFS-CONT-012. */
    @Test
    public void emptyInputReturnsRepeatedEndOfFile() throws Exception {
        FileObject file = manager.resolveFile("ram:///empty");
        file.createFile();
        try (InputStream input = file.getContent().getInputStream()) {
            assertEquals(-1, input.read());
            assertEquals(-1, input.read());
        }
    }

    /** Verifies: CVFS-CONT-022. */
    @Test
    public void randomReadSeeksWithoutChangingBytes() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "random-read", new byte[] {10, 20, 30});
        try (RandomAccessContent random = file.getContent().getRandomAccessContent(RandomAccessMode.READ)) {
            random.seek(1);
            assertEquals(20, random.getInputStream().read());
            assertEquals(2, random.getFilePointer());
        }
        assertArrayEquals(new byte[] {10, 20, 30}, file.getContent().getByteArray());
    }

    /** Verifies: CVFS-CONT-023. */
    @Test
    public void randomWritePastEndZeroFillsGap() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "random-gap", new byte[] {7});
        try (RandomAccessContent random = file.getContent().getRandomAccessContent(RandomAccessMode.READWRITE)) {
            random.seek(3);
            random.write(new byte[] {9});
        }
        assertArrayEquals(new byte[] {7, 0, 0, 9}, file.getContent().getByteArray());
    }

    /** Verifies: CVFS-CONT-023. */
    @Test
    public void randomSetLengthTruncatesContent() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "truncate", new byte[] {1, 2, 3, 4});
        try (RandomAccessContent random = file.getContent().getRandomAccessContent(RandomAccessMode.READWRITE)) {
            random.setLength(2);
        }
        assertArrayEquals(new byte[] {1, 2}, file.getContent().getByteArray());
    }

    /** Verifies: CVFS-CONT-024, CVFS-ERR-012. */
    @Test
    public void negativeRandomSeekIsRejected() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "negative", new byte[] {1});
        try (RandomAccessContent random = file.getContent().getRandomAccessContent(RandomAccessMode.READWRITE)) {
            assertThrows(IOException.class, () -> random.seek(-1));
        }
    }

    /** Verifies: CVFS-CONT-022. */
    @Test
    public void ramRandomAccessInputReadsUnsignedFf() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "unsigned", new byte[] {(byte) 0xff});
        try (RandomAccessContent random = file.getContent().getRandomAccessContent(RandomAccessMode.READ);
                InputStream input = random.getInputStream()) {
            assertEquals(255, input.read());
            assertEquals(-1, input.read());
        }
    }
}
