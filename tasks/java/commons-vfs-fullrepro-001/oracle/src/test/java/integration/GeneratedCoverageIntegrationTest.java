package integration;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.InputStream;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collection;
import java.util.Set;

import org.apache.commons.vfs2.CacheStrategy;
import org.apache.commons.vfs2.Capability;
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystem;
import org.apache.commons.vfs2.FileSystemOptions;
import org.apache.commons.vfs2.FileType;
import org.apache.commons.vfs2.RandomAccessContent;
import org.apache.commons.vfs2.cache.DefaultFilesCache;
import org.apache.commons.vfs2.cache.SoftRefFilesCache;
import org.apache.commons.vfs2.cache.WeakRefFilesCache;
import org.apache.commons.vfs2.impl.DefaultFileSystemManager;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;
import org.apache.commons.vfs2.provider.local.DefaultLocalFileProvider;
import org.apache.commons.vfs2.provider.ram.RamFileSystemConfigBuilder;
import org.apache.commons.vfs2.provider.zip.ZipFileProvider;
import org.apache.commons.vfs2.provider.zip.ZipFileSystemConfigBuilder;
import org.apache.commons.vfs2.util.RandomAccessMode;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import support.OracleSupport;

public class GeneratedCoverageIntegrationTest {
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

    /** Verifies: CVFS-CONT-011, CVFS-CONT-023, CVFS-XVIEW-001. Depends-On: randomWritePastEndZeroFillsGap, committedBytesDriveWholeContentViews. */
    @Test
    public void randomAccessCommitAgreesAcrossEquivalentContentViews() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "generated/random/data.bin", new byte[] {1, 2});
        try (RandomAccessContent random = file.getContent().getRandomAccessContent(RandomAccessMode.READWRITE)) {
            random.seek(3);
            random.write(9);
        }
        FileObject again = manager.resolveFile("ram:///generated/random/data.bin");
        assertTrue(again.exists());
        assertEquals(FileType.FILE, again.getType());
        assertEquals(4, again.getContent().getSize());
        assertArrayEquals(new byte[] {1, 2, 0, 9}, again.getContent().getByteArray());
        try (InputStream input = again.getContent().getInputStream()) {
            assertEquals(1, input.read());
        }
    }

    /** Verifies: CVFS-MGR-015, CVFS-XVIEW-003. Depends-On: relativeNameRoundTrips, childNameParentIsImmediateContainer. */
    @Test
    public void managerObjectAndFileSystemResolutionAgree() throws Exception {
        FileObject base = manager.resolveFile("ram:///generated/resolve/base");
        FileObject byManager = manager.resolveFile(base, "child.txt");
        FileObject byObject = base.resolveFile("child.txt");
        FileObject bySystem = base.getFileSystem().resolveFile("/generated/resolve/base/child.txt");
        assertEquals("/generated/resolve/base/child.txt", byManager.getName().getPath());
        assertEquals(byManager.getName(), byObject.getName());
        assertEquals(byManager.getName(), bySystem.getName());
        assertSame(byManager.getFileSystem(), bySystem.getFileSystem());
    }

    /** Verifies: CVFS-ARCH-010, CVFS-XVIEW-007. Depends-On: stringViewUsesRequestedCharset, resolutionDoesNotMaterializeState. */
    @Test
    public void jarAttributeNamesMapAndSelectedEntryAgree() throws Exception {
        Path jar = OracleSupport.jar("pkg/value.txt", OracleSupport.utf8("jar-value"));
        FileObject entry = manager.resolveFile("jar:" + jar.toUri() + "!/pkg/value.txt");
        assertEquals(Set.of("Manifest-Version", "Oracle-Title"),
                Set.copyOf(Arrays.asList(entry.getContent().getAttributeNames())));
        assertEquals("1.0", entry.getContent().getAttribute("Manifest-Version"));
        assertEquals("entry", entry.getContent().getAttribute("Oracle-Title"));
        assertEquals("entry", entry.getContent().getAttributes().get("Oracle-Title"));
        assertEquals("/pkg/value.txt", entry.getName().getPath());
    }

    /** Verifies: CVFS-CACHE-002, CVFS-CACHE-004, CVFS-CACHE-005, CVFS-XVIEW-008. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void softCachePreservesLiveIdentityUntilRemoval() throws Exception {
        FileObject object = manager.resolveFile("ram:///generated/cache/soft");
        SoftRefFilesCache cache = new SoftRefFilesCache();
        try {
            assertTrue(cache.putFileIfAbsent(object));
            assertFalse(cache.putFileIfAbsent(manager.resolveFile("ram:///generated/cache/soft")));
            assertSame(object, cache.getFile(object.getFileSystem(), object.getName()));
            cache.removeFile(object.getFileSystem(), object.getName());
            assertNull(cache.getFile(object.getFileSystem(), object.getName()));
        } finally {
            cache.close();
        }
    }

    /** Verifies: CVFS-CACHE-002, CVFS-CACHE-005, CVFS-XVIEW-008. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void weakCachePreservesLiveIdentityUntilFileSystemClear() throws Exception {
        FileObject object = manager.resolveFile("ram:///generated/cache/weak");
        WeakRefFilesCache cache = new WeakRefFilesCache();
        try {
            cache.putFile(object);
            assertSame(object, cache.getFile(object.getFileSystem(), object.getName()));
            cache.clear(object.getFileSystem());
            assertNull(cache.getFile(object.getFileSystem(), object.getName()));
        } finally {
            cache.close();
        }
    }

    /** Verifies: CVFS-CACHE-006, CVFS-XVIEW-009. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void manualStrategyKeepsExistenceUntilExplicitRefresh() throws Exception {
        assertArrayEquals(new boolean[] {true, true, true, false},
                observeExternalDeletion(CacheStrategy.MANUAL, temporary.resolve("manual.txt")));
    }

    /** Verifies: CVFS-CACHE-007, CVFS-XVIEW-009. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void onResolveStrategyRefreshesWhenManagerResolvesAgain() throws Exception {
        assertArrayEquals(new boolean[] {true, true, false, false},
                observeExternalDeletion(CacheStrategy.ON_RESOLVE, temporary.resolve("resolve.txt")));
    }

    /** Verifies: CVFS-CACHE-008, CVFS-XVIEW-009. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void onCallStrategyRefreshesExistingObjectReads() throws Exception {
        assertArrayEquals(new boolean[] {true, false, false, false},
                observeExternalDeletion(CacheStrategy.ON_CALL, temporary.resolve("call.txt")));
    }

    /** Verifies: CVFS-MGR-018, CVFS-CACHE-010, CVFS-XVIEW-010. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void closeFileSystemReleasesIdentityAndAllowsFreshResolution() throws Exception {
        FileObject first = manager.resolveFile("ram:///generated/cycle");
        FileSystem oldSystem = first.getFileSystem();
        manager.closeFileSystem(oldSystem);
        FileObject second = manager.resolveFile("ram:///generated/cycle");
        assertNotSame(oldSystem, second.getFileSystem());
        assertTrue(second.getFileSystem().getRoot().exists());
    }

    /** Verifies: CVFS-CACHE-010, CVFS-XVIEW-010. Depends-On: standardManagerRegistersEveryScopedScheme. */
    @Test
    public void closedManagerStateDoesNotLeakIntoFreshManager() throws Exception {
        StandardFileSystemManager closed = OracleSupport.manager();
        FileSystem closedSystem = closed.resolveFile("ram:///generated/closed").getFileSystem();
        closed.close();
        StandardFileSystemManager fresh = OracleSupport.manager();
        try {
            FileObject root = fresh.resolveFile("ram:///");
            assertNotSame(closedSystem, root.getFileSystem());
            assertTrue(root.exists());
            assertTrue(fresh.hasProvider("ram"));
        } finally {
            fresh.close();
        }
    }

    /** Verifies: CVFS-ARCH-002, CVFS-ARCH-006, CVFS-XVIEW-006. Depends-On: stringViewUsesRequestedCharset. */
    @Test
    public void tgzEntryMatchesTarGzipComposition() throws Exception {
        Path archive = OracleSupport.tgz("deep/value.txt", OracleSupport.utf8("tgz-value"));
        FileObject entry = manager.resolveFile("tgz:" + archive.toUri() + "!/deep/value.txt");
        assertEquals("/deep/value.txt", entry.getName().getPath());
        assertEquals("tgz-value", entry.getContent().getString(StandardCharsets.UTF_8));
        assertEquals("file", entry.getFileSystem().getParentLayer().getName().getScheme());
    }

    /** Verifies: CVFS-ARCH-002, CVFS-ARCH-006, CVFS-XVIEW-006. Depends-On: stringViewUsesRequestedCharset. */
    @Test
    public void tbz2EntryMatchesTarBzip2Composition() throws Exception {
        Path archive = OracleSupport.tbz2("deep/value.txt", OracleSupport.utf8("tbz2-value"));
        FileObject entry = manager.resolveFile("tbz2:" + archive.toUri() + "!/deep/value.txt");
        assertEquals("/deep/value.txt", entry.getName().getPath());
        assertEquals("tbz2-value", entry.getContent().getString(StandardCharsets.UTF_8));
        assertEquals("file", entry.getFileSystem().getParentLayer().getName().getScheme());
    }

    /** Verifies: CVFS-ARCH-003, CVFS-ARCH-007, CVFS-XVIEW-006. Depends-On: stringViewUsesRequestedCharset. */
    @Test
    public void nestedZipJarResolvesInnermostEntryAndImmediateBacking() throws Exception {
        byte[] innerJar = OracleSupport.jarBytes("data/value.txt", OracleSupport.utf8("nested-jar"));
        Path outer = OracleSupport.zip("lib/inner.jar", innerJar);
        FileObject entry = manager.resolveFile("jar:zip:" + outer.toUri() + "!/lib/inner.jar!/data/value.txt");
        assertEquals("/data/value.txt", entry.getName().getPath());
        assertEquals("nested-jar", entry.getContent().getString(StandardCharsets.UTF_8));
        assertEquals("inner.jar", entry.getFileSystem().getParentLayer().getName().getBaseName());
    }

    /** Verifies: CVFS-ARCH-003, CVFS-ARCH-007, CVFS-XVIEW-006. Depends-On: stringViewUsesRequestedCharset. */
    @Test
    public void nestedZipZipKeepsBothBackingLayersObservable() throws Exception {
        byte[] innerZip = Files.readAllBytes(OracleSupport.zip("inside.txt", OracleSupport.utf8("nested-zip")));
        Path outer = OracleSupport.zip("inner.zip", innerZip);
        FileObject entry = manager.resolveFile("zip:zip:" + outer.toUri() + "!/inner.zip!/inside.txt");
        FileObject immediate = entry.getFileSystem().getParentLayer();
        assertEquals("nested-zip", entry.getContent().getString(StandardCharsets.UTF_8));
        assertEquals("inner.zip", immediate.getName().getBaseName());
        assertNotNull(immediate.getFileSystem().getParentLayer());
    }

    /** Verifies: CVFS-ARCH-009. Depends-On: nonRootBaseNameIsDecoded, stringViewUsesRequestedCharset. */
    @Test
    public void configuredZipCharsetDecodesEntryNameAndContent() throws Exception {
        Charset cp437 = Charset.forName("CP437");
        Path archive = OracleSupport.zipWithCharset("café.txt", OracleSupport.utf8("charset-value"), cp437);
        FileSystemOptions options = new FileSystemOptions();
        ZipFileSystemConfigBuilder.getInstance().setCharset(options, cp437);
        FileObject child = manager.resolveFile("zip:" + archive.toUri() + "!/", options).getChildren()[0];
        assertEquals("café.txt", child.getName().getBaseName());
        assertEquals("charset-value", child.getContent().getString(StandardCharsets.UTF_8));
        assertEquals("IBM437", ZipFileSystemConfigBuilder.getInstance().getCharset(options).name());
    }

    /** Verifies: CVFS-ARCH-009. Depends-On: nonRootBaseNameIsDecoded, stringViewUsesRequestedCharset. */
    @Test
    public void defaultZipCharsetDecodesUtf8EntryNameAndContent() throws Exception {
        Path archive = OracleSupport.zip("数据.txt", OracleSupport.utf8("utf8-entry"));
        FileSystemOptions options = new FileSystemOptions();
        FileObject child = manager.resolveFile("zip:" + archive.toUri() + "!/", options).getChildren()[0];
        assertEquals("数据.txt", child.getName().getBaseName());
        assertEquals("utf8-entry", child.getContent().getString(StandardCharsets.UTF_8));
        assertEquals(StandardCharsets.UTF_8, ZipFileSystemConfigBuilder.getInstance().getCharset(options));
    }

    /** Verifies: CVFS-MGR-011. Depends-On: standardManagerRegistersEveryScopedScheme. */
    @Test
    public void zipManagerAndProviderCapabilitiesAgree() throws Exception {
        Collection<Capability> managerCapabilities = manager.getProviderCapabilities("zip");
        assertEquals(new ZipFileProvider().getCapabilities(), managerCapabilities);
        assertTrue(managerCapabilities.contains(Capability.READ_CONTENT));
        assertFalse(managerCapabilities.contains(Capability.WRITE_CONTENT));
    }

    /** Verifies: CVFS-MGR-017, CVFS-PROV-002, CVFS-XVIEW-004. Depends-On: resolutionDoesNotMaterializeState. */
    @Test
    public void optionSensitiveRelativeResolutionRetainsFileSystemOptions() throws Exception {
        FileSystemOptions options = new FileSystemOptions();
        RamFileSystemConfigBuilder.getInstance().setMaxSize(options, 12L);
        FileObject base = manager.resolveFile("ram:///generated/options", options);
        FileObject child = manager.resolveFile(base, "child", options);
        assertEquals("/generated/options/child", child.getName().getPath());
        assertEquals(options, child.getFileSystem().getFileSystemOptions());
        assertEquals(12L, RamFileSystemConfigBuilder.getInstance()
                .getLongMaxSize(child.getFileSystem().getFileSystemOptions()));
    }

    /** Verifies: CVFS-CONT-017, CVFS-XVIEW-001. Depends-On: committedBytesDriveWholeContentViews. */
    @Test
    public void fileContentWriteReturnsCountAndCopiesEveryByte() throws Exception {
        FileObject source = OracleSupport.ramFile(manager, "generated/write/source", OracleSupport.utf8("copy-six"));
        FileObject target = manager.resolveFile("ram:///generated/write/target");
        assertEquals(8L, source.getContent().write(target));
        assertEquals("copy-six", target.getContent().getString(StandardCharsets.UTF_8));
        assertEquals(8L, target.getContent().getSize());
    }

    /** Verifies: CVFS-MGR-014, CVFS-MGR-015, CVFS-PROV-007, CVFS-XVIEW-003. Depends-On: childNameParentIsImmediateContainer. */
    @Test
    public void suppliedLocalBaseAndEquivalentUriResolveSameResource() throws Exception {
        Path base = temporary.resolve("local-base");
        Path child = base.resolve("sub/file.txt");
        Files.createDirectories(child.getParent());
        Files.writeString(child, "local-base");
        FileObject byBase = manager.resolveFile(base.toFile(), "sub/file.txt");
        FileObject byUri = manager.resolveFile(child.toUri());
        assertEquals(byUri.getName(), byBase.getName());
        assertEquals("local-base", byBase.getContent().getString(StandardCharsets.UTF_8));
        assertEquals("file", byBase.getName().getScheme());
    }

    private static boolean[] observeExternalDeletion(CacheStrategy strategy, Path path) throws Exception {
        Files.writeString(path, "old");
        DefaultFileSystemManager configured = new DefaultFileSystemManager();
        try {
            configured.addProvider("file", new DefaultLocalFileProvider());
            configured.setFilesCache(new DefaultFilesCache());
            configured.setCacheStrategy(strategy);
            configured.init();
            FileObject object = configured.resolveFile(path.toUri());
            boolean attached = object.exists();
            Files.delete(path);
            boolean sameObject = object.exists();
            boolean resolvedAgain = configured.resolveFile(path.toUri()).exists();
            object.refresh();
            boolean afterRefresh = object.exists();
            return new boolean[] {attached, sameObject, resolvedAgain, afterRefresh};
        } finally {
            configured.close();
        }
    }
}
