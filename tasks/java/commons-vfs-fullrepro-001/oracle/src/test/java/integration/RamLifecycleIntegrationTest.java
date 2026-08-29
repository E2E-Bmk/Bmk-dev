package integration;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.commons.vfs2.CacheStrategy;
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystemException;
import org.apache.commons.vfs2.FileSystemManager;
import org.apache.commons.vfs2.FileSystemOptions;
import org.apache.commons.vfs2.FileType;
import org.apache.commons.vfs2.Selectors;
import org.apache.commons.vfs2.VFS;
import org.apache.commons.vfs2.cache.DefaultFilesCache;
import org.apache.commons.vfs2.cache.NullFilesCache;
import org.apache.commons.vfs2.impl.DefaultFileSystemManager;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;
import org.apache.commons.vfs2.provider.ram.RamFileProvider;
import org.apache.commons.vfs2.provider.ram.RamFileSystemConfigBuilder;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import support.OracleSupport;

public class RamLifecycleIntegrationTest {
    private StandardFileSystemManager manager;

    @BeforeEach
    void setUp() throws Exception {
        manager = OracleSupport.manager();
    }

    @AfterEach
    void tearDown() {
        manager.close();
        VFS.close();
    }

    /** Verifies: CVFS-CONT-011, CVFS-XVIEW-001. Depends-On: committedBytesDriveWholeContentViews. */
    @Test
    public void committedWriteAgreesAcrossContentViews() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "views/a.txt", OracleSupport.utf8("alpha"));
        FileObject again = manager.resolveFile("ram:///views/a.txt");
        assertTrue(again.exists());
        assertEquals(FileType.FILE, again.getType());
        assertEquals(5, again.getContent().getSize());
        assertArrayEquals(OracleSupport.utf8("alpha"), again.getContent().getByteArray());
        assertEquals("alpha", again.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-CONT-002, CVFS-NAME-019, CVFS-XVIEW-002. Depends-On: createFolderBuildsParents. */
    @Test
    public void createdTreeAgreesWithParentChildren() throws Exception {
        manager.resolveFile("ram:///tree/a.txt").createFile();
        manager.resolveFile("ram:///tree/b").createFolder();
        Set<String> names = Arrays.stream(manager.resolveFile("ram:///tree").getChildren())
                .map(value -> value.getName().getBaseName()).collect(Collectors.toSet());
        assertEquals(Set.of("a.txt", "b"), names);
    }

    /** Verifies: CVFS-NAME-022, CVFS-NAME-023. Depends-On: ancestryUsesCanonicalPaths. */
    @Test
    public void selectorsExposeFilesAcrossHierarchy() throws Exception {
        manager.resolveFile("ram:///select/a.txt").createFile();
        manager.resolveFile("ram:///select/sub/b.txt").createFile();
        FileObject[] files = manager.resolveFile("ram:///select").findFiles(Selectors.SELECT_FILES);
        assertEquals(2, files.length);
        for (FileObject file : files) {
            assertTrue(file.isFile());
        }
    }

    /** Verifies: CVFS-CONT-004, CVFS-XVIEW-002. Depends-On: committedBytesDriveWholeContentViews. */
    @Test
    public void copyFromPreservesTreeAndBytes() throws Exception {
        OracleSupport.ramFile(manager, "source/sub/a.txt", OracleSupport.utf8("copy"));
        FileObject destination = manager.resolveFile("ram:///destination");
        destination.copyFrom(manager.resolveFile("ram:///source"), Selectors.SELECT_ALL);
        assertEquals("copy", destination.resolveFile("sub/a.txt").getContent().getString(StandardCharsets.UTF_8));
        assertTrue(destination.resolveFile("sub").isFolder());
    }

    /** Verifies: CVFS-CONT-005, CVFS-XVIEW-002. Depends-On: createFileBuildsParentsAndZeroLengthFile. */
    @Test
    public void moveTransfersStateAndInvalidatesSource() throws Exception {
        FileObject source = OracleSupport.ramFile(manager, "move/source.txt", OracleSupport.utf8("payload"));
        FileObject destination = manager.resolveFile("ram:///move/destination.txt");
        source.moveTo(destination);
        assertFalse(source.exists());
        assertEquals("payload", destination.getContent().getString(StandardCharsets.UTF_8));
    }

    /** Verifies: CVFS-CONT-008, CVFS-XVIEW-002. Depends-On: deletingFileReturnsTrueAndRemovesIt. */
    @Test
    public void deleteAllRemovesDescendantsAndParent() throws Exception {
        OracleSupport.ramFile(manager, "delete/sub/a", new byte[] {1});
        OracleSupport.ramFile(manager, "delete/sub/b", new byte[] {2});
        FileObject root = manager.resolveFile("ram:///delete");
        assertTrue(root.deleteAll() >= 4);
        assertFalse(root.exists());
    }

    /** Verifies: CVFS-PROV-001. Depends-On: rootBaseNameIsEmpty. */
    @Test
    public void ramRootIsPersistentFolder() throws Exception {
        FileObject root = manager.resolveFile("ram:///");
        assertTrue(root.exists());
        assertEquals(FileType.FOLDER, root.getType());
        assertThrows(FileSystemException.class, root::delete);
    }

    /** Verifies: CVFS-PROV-002, CVFS-XVIEW-004. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void equalRamOptionsShareFileSystem() throws Exception {
        FileSystemOptions options = new FileSystemOptions();
        FileObject first = manager.resolveFile("ram:///one", options);
        FileObject second = manager.resolveFile("ram:///two", (FileSystemOptions) options.clone());
        assertSame(first.getFileSystem(), second.getFileSystem());
    }

    /** Verifies: CVFS-PROV-002, CVFS-XVIEW-004. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void distinctRamOptionsIsolateFileSystems() throws Exception {
        FileSystemOptions defaultOptions = new FileSystemOptions();
        FileSystemOptions limitedOptions = new FileSystemOptions();
        RamFileSystemConfigBuilder.getInstance().setMaxSize(limitedOptions, 20L);
        FileObject first = manager.resolveFile("ram:///same", defaultOptions);
        FileObject second = manager.resolveFile("ram:///same", limitedOptions);
        assertNotSame(first.getFileSystem(), second.getFileSystem());
    }

    /** Verifies: CVFS-PROV-003, CVFS-PROV-004. */
    @Test
    public void ramOptionsExposeConfiguredQuota() throws Exception {
        FileSystemOptions options = new FileSystemOptions();
        assertEquals(Long.MAX_VALUE, RamFileSystemConfigBuilder.getInstance().getLongMaxSize(options));
        RamFileSystemConfigBuilder.getInstance().setMaxSize(options, 10L);
        assertEquals(10L, RamFileSystemConfigBuilder.getInstance().getLongMaxSize(options));
    }

    /** Verifies: CVFS-PROV-004, CVFS-PROV-005, CVFS-ERR-009. Depends-On: replaceOutputOverwritesExistingBytes. */
    @Test
    public void ramQuotaAcceptsLimitAndRejectsOverflow() throws Exception {
        FileSystemOptions options = new FileSystemOptions();
        RamFileSystemConfigBuilder.getInstance().setMaxSize(options, 3L);
        FileObject file = manager.resolveFile("ram:///limited", options);
        try (OutputStream out = file.getContent().getOutputStream()) {
            out.write(new byte[] {1, 2, 3});
        }
        assertThrows(FileSystemException.class, () -> {
            try (OutputStream out = file.getContent().getOutputStream()) {
                out.write(new byte[] {1, 2, 3, 4});
            }
        });
        assertTrue(file.getContent().getSize() <= 3);
    }

    /** Verifies: CVFS-CACHE-001. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void strongCacheReturnsStoredObject() throws Exception {
        FileObject file = manager.resolveFile("ram:///cached");
        DefaultFilesCache cache = new DefaultFilesCache();
        cache.putFile(file);
        assertSame(file, cache.getFile(file.getFileSystem(), file.getName()));
    }

    /** Verifies: CVFS-CACHE-004. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void strongCachePutIfAbsentPreservesFirstObject() throws Exception {
        FileObject first = manager.resolveFile("ram:///cached");
        FileObject second = manager.resolveFile("ram:///cached");
        DefaultFilesCache cache = new DefaultFilesCache();
        assertTrue(cache.putFileIfAbsent(first));
        assertFalse(cache.putFileIfAbsent(second));
        assertSame(first, cache.getFile(first.getFileSystem(), first.getName()));
    }

    /** Verifies: CVFS-CACHE-005. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void strongCacheRemoveAndClearDropMappings() throws Exception {
        FileObject first = manager.resolveFile("ram:///cache/a");
        FileObject second = manager.resolveFile("ram:///cache/b");
        DefaultFilesCache cache = new DefaultFilesCache();
        cache.putFile(first);
        cache.putFile(second);
        cache.removeFile(first.getFileSystem(), first.getName());
        assertNull(cache.getFile(first.getFileSystem(), first.getName()));
        cache.clear(second.getFileSystem());
        assertNull(cache.getFile(second.getFileSystem(), second.getName()));
    }

    /** Verifies: CVFS-CACHE-003, CVFS-XVIEW-008. */
    @Test
    public void nullCacheNeverRetainsMappings() throws Exception {
        FileObject file = manager.resolveFile("ram:///uncached");
        NullFilesCache cache = new NullFilesCache();
        cache.putFile(file);
        assertFalse(cache.putFileIfAbsent(file));
        assertNull(cache.getFile(file.getFileSystem(), file.getName()));
    }

    /** Verifies: CVFS-MGR-008, CVFS-MGR-010. */
    @Test
    public void providerRegistrationAndRemovalAreObservable() throws Exception {
        DefaultFileSystemManager configured = new DefaultFileSystemManager();
        try {
            configured.addProvider("ram", new RamFileProvider());
            configured.init();
            assertTrue(configured.hasProvider("ram"));
            configured.removeProvider("ram");
            assertFalse(configured.hasProvider("ram"));
        } finally {
            configured.close();
        }
    }

    /** Verifies: CVFS-MGR-009, CVFS-ERR-001. */
    @Test
    public void duplicateProviderRegistrationIsRejected() throws Exception {
        DefaultFileSystemManager configured = new DefaultFileSystemManager();
        try {
            configured.addProvider("ram", new RamFileProvider());
            assertThrows(FileSystemException.class, () -> configured.addProvider("ram", new RamFileProvider()));
        } finally {
            configured.close();
        }
    }

    /** Verifies: CVFS-MGR-006, CVFS-MGR-007, CVFS-ERR-014. */
    @Test
    public void managerDefaultsAndPostInitReconfiguration() throws Exception {
        DefaultFileSystemManager configured = new DefaultFileSystemManager();
        try {
            configured.addProvider("ram", new RamFileProvider());
            configured.init();
            assertEquals(CacheStrategy.ON_RESOLVE, configured.getCacheStrategy());
            assertThrows(FileSystemException.class, () -> configured.setFilesCache(new NullFilesCache()));
        } finally {
            configured.close();
        }
    }

    /** Verifies: CVFS-MGR-002, CVFS-MGR-003, CVFS-XVIEW-010. Depends-On: standardManagerRegistersEveryScopedScheme. */
    @Test
    public void vfsSetAndResetReplaceSharedManager() throws Exception {
        StandardFileSystemManager installed = OracleSupport.manager();
        VFS.setManager(installed);
        assertSame(installed, VFS.getManager());
        FileSystemManager reset = VFS.reset();
        assertNotSame(installed, reset);
        assertTrue(reset.hasProvider("ram"));
    }

    /** Verifies: CVFS-CONT-014, CVFS-CACHE-010. Depends-On: committedBytesDriveWholeContentViews. */
    @Test
    public void closedFileObjectCanBeResolvedAndUsedAgain() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "reuse", OracleSupport.utf8("value"));
        file.close();
        FileObject again = manager.resolveFile("ram:///reuse");
        assertEquals("value", again.getContent().getString(StandardCharsets.UTF_8));
    }
}
