package atomic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.AccessMode;

import org.apache.commons.vfs2.FileName;
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystemException;
import org.apache.commons.vfs2.FileType;
import org.apache.commons.vfs2.NameScope;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;
import org.apache.commons.vfs2.util.RandomAccessMode;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import support.OracleSupport;

public class NameAndTypeAtomicTest {
    private StandardFileSystemManager manager;

    @BeforeEach
    void setUp() throws Exception {
        manager = OracleSupport.manager();
    }

    @AfterEach
    void tearDown() throws Exception {
        manager.close();
    }

    /** Verifies: CVFS-NAME-016. */
    @Test
    public void fileTypeFileHasContentOnly() {
        assertTrue(FileType.FILE.hasContent());
        assertFalse(FileType.FILE.hasChildren());
    }

    /** Verifies: CVFS-NAME-017. */
    @Test
    public void fileTypeFolderHasChildrenOnly() {
        assertTrue(FileType.FOLDER.hasChildren());
        assertFalse(FileType.FOLDER.hasContent());
    }

    /** Verifies: CVFS-NAME-001. */
    @Test
    public void fileNameConstantsDescribeCanonicalRoot() {
        assertEquals('/', FileName.SEPARATOR_CHAR);
        assertEquals("/", FileName.SEPARATOR);
        assertEquals("/", FileName.ROOT_PATH);
    }

    /** Verifies: CVFS-NAME-005. */
    @Test
    public void rootBaseNameIsEmpty() throws Exception {
        assertEquals("", manager.resolveFile("ram:///").getName().getBaseName());
    }

    /** Verifies: CVFS-NAME-005. */
    @Test
    public void nonRootBaseNameIsDecoded() throws Exception {
        assertEquals("two words.txt", manager.resolveFile("ram:///a/two%20words.txt").getName().getBaseName());
    }

    /** Verifies: CVFS-NAME-006. */
    @Test
    public void ramDepthIncludesFileSystemNameLevel() throws Exception {
        assertEquals(0, manager.resolveFile("ram:///").getName().getDepth());
        assertEquals(2, manager.resolveFile("ram:///a").getName().getDepth());
        assertEquals(4, manager.resolveFile("ram:///a/b/c").getName().getDepth());
    }

    /** Verifies: CVFS-NAME-007. */
    @Test
    public void rootNameHasNoParent() throws Exception {
        assertNull(manager.resolveFile("ram:///").getName().getParent());
    }

    /** Verifies: CVFS-NAME-007. */
    @Test
    public void childNameParentIsImmediateContainer() throws Exception {
        assertEquals("/a/b", manager.resolveFile("ram:///a/b/c").getName().getParent().getPath());
    }

    /** Verifies: CVFS-NAME-002. */
    @Test
    public void dotAndRepeatedSeparatorsNormalize() throws Exception {
        assertEquals("/a/c", manager.resolveFile("ram:///a//b/.././c").getName().getPath());
    }

    /** Verifies: CVFS-NAME-003, CVFS-ERR-002. */
    @Test
    public void rootEscapeIsRejected() throws Exception {
        FileName root = manager.resolveFile("ram:///").getName();
        assertThrows(FileSystemException.class, () -> manager.resolveName(root, "../escape"));
    }

    /** Verifies: CVFS-NAME-004. */
    @Test
    public void ramPathDecodesWhileUriRetainsEscaping() throws Exception {
        FileName name = manager.resolveFile("ram:///a/two%20words.txt").getName();
        assertEquals("/a/two words.txt", name.getPath());
        assertEquals("/a/two words.txt", name.getPathDecoded());
        assertEquals("ram:///a/two%20words.txt", name.getURI());
    }

    /** Verifies: CVFS-NAME-008. */
    @Test
    public void relativeNameRoundTrips() throws Exception {
        FileName base = manager.resolveFile("ram:///a/b").getName();
        FileName other = manager.resolveFile("ram:///a/c/d").getName();
        assertEquals("../c/d", base.getRelativeName(other));
    }

    /** Verifies: CVFS-NAME-010. */
    @Test
    public void fileSystemScopeResolvesAbsolutePath() throws Exception {
        FileName base = manager.resolveFile("ram:///a/b").getName();
        assertEquals("/x", manager.resolveName(base, "/x", NameScope.FILE_SYSTEM).getPath());
    }

    /** Verifies: CVFS-NAME-011. */
    @Test
    public void childScopeAcceptsDirectChild() throws Exception {
        FileName base = manager.resolveFile("ram:///a").getName();
        assertEquals("/a/b", manager.resolveName(base, "b", NameScope.CHILD).getPath());
    }

    /** Verifies: CVFS-NAME-011, CVFS-ERR-002. */
    @Test
    public void childScopeRejectsDeepDescendant() throws Exception {
        FileName base = manager.resolveFile("ram:///a").getName();
        assertThrows(FileSystemException.class, () -> manager.resolveName(base, "b/c", NameScope.CHILD));
    }

    /** Verifies: CVFS-NAME-012. */
    @Test
    public void descendentScopeRejectsSelf() throws Exception {
        FileName base = manager.resolveFile("ram:///a").getName();
        assertThrows(FileSystemException.class, () -> manager.resolveName(base, ".", NameScope.DESCENDENT));
    }

    /** Verifies: CVFS-NAME-013. */
    @Test
    public void descendentOrSelfAcceptsSelf() throws Exception {
        FileName base = manager.resolveFile("ram:///a").getName();
        assertEquals(base, manager.resolveName(base, ".", NameScope.DESCENDENT_OR_SELF));
    }

    /** Verifies: CVFS-NAME-014. */
    @Test
    public void ancestryUsesCanonicalPaths() throws Exception {
        FileName parent = manager.resolveFile("ram:///a").getName();
        FileName child = manager.resolveFile("ram:///a/b/c").getName();
        assertTrue(child.isAncestor(parent));
        assertTrue(parent.isDescendent(child));
    }

    /** Verifies: CVFS-NAME-015. */
    @Test
    public void resolutionDoesNotMaterializeState() throws Exception {
        FileObject missing = manager.resolveFile("ram:///missing");
        assertFalse(missing.exists());
        assertEquals(FileType.IMAGINARY, missing.getType());
    }

    /** Verifies: CVFS-CONT-022. */
    @Test
    public void randomAccessReadModeRequestsReadOnly() {
        assertTrue(RandomAccessMode.READ.requestRead());
        assertFalse(RandomAccessMode.READ.requestWrite());
        assertEquals("r", RandomAccessMode.READ.getModeString());
    }

    /** Verifies: CVFS-CONT-022. */
    @Test
    public void randomAccessReadWriteModeRequestsBoth() {
        assertTrue(RandomAccessMode.READWRITE.requestRead());
        assertTrue(RandomAccessMode.READWRITE.requestWrite());
        assertEquals("rw", RandomAccessMode.READWRITE.getModeString());
    }

    /** Verifies: CVFS-CONT-025. */
    @Test
    public void randomAccessModeConvertsNioAccess() {
        assertSame(RandomAccessMode.READ, RandomAccessMode.from(AccessMode.READ));
        assertSame(RandomAccessMode.READWRITE, RandomAccessMode.from(AccessMode.WRITE));
    }

}
