package atomic;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.Set;

import org.apache.commons.vfs2.FileNotFolderException;
import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystemException;
import org.apache.commons.vfs2.impl.DefaultFileSystemManager;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;
import org.apache.commons.vfs2.provider.ram.RamFileProvider;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import support.OracleSupport;

public class GeneratedAtomicTest {
    private StandardFileSystemManager manager;

    @BeforeEach
    void setUp() throws Exception {
        manager = OracleSupport.manager();
    }

    @AfterEach
    void tearDown() {
        manager.close();
    }

    /** Verifies: CVFS-MGR-005. */
    @Test
    public void standardManagerRegistersEveryScopedScheme() {
        Set<String> schemes = Set.copyOf(Arrays.asList(manager.getSchemes()));
        assertTrue(schemes.containsAll(Set.of("file", "ram", "zip", "jar", "tar", "gz", "bz2", "tgz", "tbz2")));
    }

    /** Verifies: CVFS-MGR-012, CVFS-ERR-001. */
    @Test
    public void unknownSchemeResolutionIsRejected() {
        assertThrows(FileSystemException.class, () -> manager.resolveFile("unknown-stage3b:///x"));
    }

    /** Verifies: CVFS-MGR-016, CVFS-ERR-003. */
    @Test
    public void relativeResolutionWithoutBaseIsRejected() throws Exception {
        DefaultFileSystemManager withoutBase = new DefaultFileSystemManager();
        try {
            withoutBase.addProvider("ram", new RamFileProvider());
            withoutBase.init();
            assertThrows(FileSystemException.class, () -> withoutBase.resolveFile("relative.txt"));
        } finally {
            withoutBase.close();
        }
    }

    /** Verifies: CVFS-NAME-020, CVFS-ERR-005. */
    @Test
    public void regularFileRejectsChildListing() throws Exception {
        FileObject file = OracleSupport.ramFile(manager, "generated/errors/file.txt", new byte[] {1});
        assertThrows(FileNotFolderException.class, file::getChildren);
    }

    /** Verifies: CVFS-ERR-006. */
    @Test
    public void folderRejectsByteContent() throws Exception {
        FileObject folder = manager.resolveFile("ram:///generated/errors/folder");
        folder.createFolder();
        assertThrows(FileSystemException.class, () -> folder.getContent().getInputStream());
    }
}
