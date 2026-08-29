package integration;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystemException;
import org.apache.commons.vfs2.FileType;
import org.apache.commons.vfs2.Selectors;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import support.OracleSupport;

public class LocalArchiveIntegrationTest {
    @TempDir
    Path temporary;

    private StandardFileSystemManager manager;

    @BeforeEach
    void setUp() throws Exception {
        manager = OracleSupport.manager();
    }

    @AfterEach
    void tearDown() {
        manager.close();
    }

    /** Verifies: CVFS-MGR-014, CVFS-PROV-007, CVFS-XVIEW-003. */
    @Test
    public void localFileAndPathConversionsAgree() throws Exception {
        Path path = temporary.resolve("same.txt");
        FileObject fromPath = manager.toFileObject(path);
        FileObject fromFile = manager.toFileObject(path.toFile());
        FileObject fromUri = manager.resolveFile(path.toUri());
        assertEquals(fromPath.getName(), fromFile.getName());
        assertEquals(fromPath.getName(), fromUri.getName());
    }

    /** Verifies: CVFS-PROV-008, CVFS-XVIEW-005. Depends-On: replaceOutputOverwritesExistingBytes. */
    @Test
    public void localVfsWriteMatchesPhysicalBytes() throws Exception {
        Path path = temporary.resolve("physical.txt");
        FileObject file = manager.toFileObject(path);
        try (OutputStream out = file.getContent().getOutputStream()) {
            out.write(OracleSupport.utf8("physical"));
        }
        assertArrayEquals(OracleSupport.utf8("physical"), Files.readAllBytes(path));
        assertEquals("physical", file.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-PROV-009, CVFS-XVIEW-005. Depends-On: committedBytesDriveWholeContentViews. */
    @Test
    public void localRefreshObservesExternalChanges() throws Exception {
        Path path = temporary.resolve("refresh.txt");
        Files.write(path, OracleSupport.utf8("old"));
        FileObject file = manager.toFileObject(path);
        assertEquals("old", file.getContent().getString(StandardCharsets.UTF_8));
        Files.write(path, OracleSupport.utf8("new-value"));
        file.refresh();
        assertEquals("new-value", file.getContent().getString(StandardCharsets.UTF_8));
        assertEquals(9, file.getContent().getSize());
    }

    /** Verifies: CVFS-CONT-005, CVFS-PROV-008, CVFS-XVIEW-002. Depends-On: committedBytesDriveWholeContentViews. */
    @Test
    public void localMoveMatchesPhysicalHierarchy() throws Exception {
        Path sourcePath = temporary.resolve("source.txt");
        Path destinationPath = temporary.resolve("sub/destination.txt");
        Files.write(sourcePath, OracleSupport.utf8("move"));
        Files.createDirectories(destinationPath.getParent());
        FileObject source = manager.toFileObject(sourcePath);
        FileObject destination = manager.toFileObject(destinationPath);
        source.moveTo(destination);
        assertFalse(Files.exists(sourcePath));
        assertEquals("move", Files.readString(destinationPath));
        assertTrue(destination.exists());
    }

    /** Verifies: CVFS-CONT-004, CVFS-PROV-008, CVFS-XVIEW-002. Depends-On: committedBytesDriveWholeContentViews. */
    @Test
    public void ramToLocalCopyMatchesPhysicalTree() throws Exception {
        OracleSupport.ramFile(manager, "copy/sub/a.txt", OracleSupport.utf8("copied"));
        Path destinationPath = temporary.resolve("copied-tree");
        FileObject destination = manager.toFileObject(destinationPath);
        destination.copyFrom(manager.resolveFile("ram:///copy"), Selectors.SELECT_ALL);
        assertEquals("copied", Files.readString(destinationPath.resolve("sub/a.txt")));
        assertTrue(destination.resolveFile("sub").isFolder());
    }

    /** Verifies: CVFS-CONT-019, CVFS-PROV-008. */
    @Test
    public void localTimestampRoundTripsWithinProviderAccuracy() throws Exception {
        Path path = temporary.resolve("time.txt");
        Files.write(path, new byte[] {1});
        FileObject file = manager.toFileObject(path);
        long requested = System.currentTimeMillis() - 120_000L;
        file.getContent().setLastModifiedTime(requested);
        long observed = file.getContent().getLastModifiedTime();
        assertTrue(Math.abs(observed - requested) <= file.getFileSystem().getLastModTimeAccuracy());
    }

    /** Verifies: CVFS-ARCH-001, CVFS-ARCH-006, CVFS-XVIEW-006. */
    @Test
    public void zipEntryExposesTypeSizeAndBytes() throws Exception {
        Path zip = OracleSupport.zip("folder/a.txt", OracleSupport.utf8("zip-data"));
        FileObject entry = manager.resolveFile("zip:" + zip.toUri() + "!/folder/a.txt");
        assertEquals(FileType.FILE, entry.getType());
        assertEquals(8, entry.getContent().getSize());
        assertEquals("zip-data", entry.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-ARCH-005, CVFS-ARCH-006. Depends-On: createFolderBuildsParents. */
    @Test
    public void zipSynthesizesMissingParentFolders() throws Exception {
        Path zip = OracleSupport.zip("one/two/value.txt", new byte[] {1});
        FileObject folder = manager.resolveFile("zip:" + zip.toUri() + "!/one/two");
        assertTrue(folder.isFolder());
        assertEquals(1, folder.getChildren().length);
        assertEquals("value.txt", folder.getChildren()[0].getName().getBaseName());
    }

    /** Verifies: CVFS-ARCH-008. Depends-On: independentInputStreamsHaveIndependentCursors. */
    @Test
    public void zipStreamsRemainIndependent() throws Exception {
        Path zip = OracleSupport.zip("data.bin", new byte[] {1, 2, 3});
        FileObject entry = manager.resolveFile("zip:" + zip.toUri() + "!/data.bin");
        try (InputStream first = entry.getContent().getInputStream();
                InputStream second = entry.getContent().getInputStream()) {
            assertEquals(1, first.read());
            assertEquals(1, second.read());
            first.close();
            assertEquals(2, second.read());
        }
    }

    /** Verifies: CVFS-ARCH-011, CVFS-ERR-010. */
    @Test
    public void zipEntryRejectsMutation() throws Exception {
        Path zip = OracleSupport.zip("readonly.txt", new byte[] {1});
        FileObject entry = manager.resolveFile("zip:" + zip.toUri() + "!/readonly.txt");
        assertThrows(FileSystemException.class, () -> entry.getContent().getOutputStream());
        assertThrows(FileSystemException.class, entry::delete);
    }

    /** Verifies: CVFS-ARCH-007, CVFS-XVIEW-006. */
    @Test
    public void zipFileSystemReportsImmediateParentLayer() throws Exception {
        Path zip = OracleSupport.zip("a.txt", new byte[] {1});
        FileObject entry = manager.resolveFile("zip:" + zip.toUri() + "!/a.txt");
        FileObject backing = entry.getFileSystem().getParentLayer();
        assertNotNull(backing);
        assertEquals(manager.toFileObject(zip).getName(), backing.getName());
    }

    /** Verifies: CVFS-ARCH-004. Depends-On: ramPathDecodesWhileUriRetainsEscaping. */
    @Test
    public void encodedBangResolvesLiteralArchiveEntryName() throws Exception {
        Path zip = OracleSupport.zip("bang!.txt", OracleSupport.utf8("bang"));
        FileObject entry = manager.resolveFile("zip:" + zip.toUri() + "!/bang%21.txt");
        assertEquals("/bang!.txt", entry.getName().getPathDecoded());
        assertEquals("bang", entry.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-ARCH-010, CVFS-XVIEW-007. */
    @Test
    public void jarAttributesCombineMainAndEntryValues() throws Exception {
        Path jar = OracleSupport.jar("pkg/value.txt", OracleSupport.utf8("jar"));
        FileObject entry = manager.resolveFile("jar:" + jar.toUri() + "!/pkg/value.txt");
        Map<String, Object> attributes = entry.getContent().getAttributes();
        assertEquals("1.0", attributes.get("Manifest-Version"));
        assertEquals("entry", attributes.get("Oracle-Title"));
        assertThrows(UnsupportedOperationException.class, () -> attributes.put("x", "y"));
    }

    /** Verifies: CVFS-ARCH-012, CVFS-ERR-011. */
    @Test
    public void malformedZipIsRejectedOnResolutionOrContent() throws Exception {
        Path malformed = temporary.resolve("broken.zip");
        Files.writeString(malformed, "not an archive");
        assertThrows(FileSystemException.class, () -> {
            FileObject entry = manager.resolveFile("zip:" + malformed.toUri() + "!/x");
            entry.getContent().getByteArray();
        });
    }
}
