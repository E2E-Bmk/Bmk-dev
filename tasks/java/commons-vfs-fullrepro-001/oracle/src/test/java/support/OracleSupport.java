package support;

import java.io.IOException;
import java.io.OutputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import org.apache.commons.compress.archivers.tar.TarArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveOutputStream;
import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;
import org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream;
import org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream.UnicodeExtraFieldPolicy;
import org.apache.commons.compress.compressors.bzip2.BZip2CompressorOutputStream;
import org.apache.commons.compress.compressors.gzip.GzipCompressorOutputStream;

import org.apache.commons.vfs2.FileObject;
import org.apache.commons.vfs2.FileSystemException;
import org.apache.commons.vfs2.impl.StandardFileSystemManager;

/** Test-owned fixture construction using JDK writers and documented VFS entry points. */
public final class OracleSupport {
    private OracleSupport() {
    }

    public static StandardFileSystemManager manager() throws FileSystemException {
        StandardFileSystemManager manager = new StandardFileSystemManager();
        manager.init();
        return manager;
    }

    public static FileObject ramFile(StandardFileSystemManager manager, String path, byte[] bytes)
            throws IOException {
        FileObject file = manager.resolveFile("ram:///" + path);
        try (OutputStream out = file.getContent().getOutputStream()) {
            out.write(bytes);
        }
        return file;
    }

    public static Path zip(String entry, byte[] bytes) throws IOException {
        Path path = Files.createTempFile("cvfs-oracle-", ".zip");
        try (ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(path))) {
            out.putNextEntry(new ZipEntry(entry));
            out.write(bytes);
            out.closeEntry();
        }
        return path;
    }

    public static Path jar(String entry, byte[] bytes) throws IOException {
        Path path = Files.createTempFile("cvfs-oracle-", ".jar");
        Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        manifest.getMainAttributes().putValue("Oracle-Title", "main");
        Attributes entryAttributes = new Attributes();
        entryAttributes.putValue("Oracle-Title", "entry");
        manifest.getEntries().put(entry, entryAttributes);
        try (JarOutputStream out = new JarOutputStream(Files.newOutputStream(path), manifest)) {
            out.putNextEntry(new JarEntry(entry));
            out.write(bytes);
            out.closeEntry();
        }
        return path;
    }

    public static byte[] jarBytes(String entry, byte[] bytes) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        try (JarOutputStream out = new JarOutputStream(buffer, manifest)) {
            out.putNextEntry(new JarEntry(entry));
            out.write(bytes);
            out.closeEntry();
        }
        return buffer.toByteArray();
    }

    public static Path zipWithCharset(String entry, byte[] bytes, Charset charset) throws IOException {
        Path path = Files.createTempFile("cvfs-oracle-charset-", ".zip");
        try (ZipArchiveOutputStream out = new ZipArchiveOutputStream(path)) {
            out.setEncoding(charset.name());
            out.setUseLanguageEncodingFlag(false);
            out.setCreateUnicodeExtraFields(UnicodeExtraFieldPolicy.NEVER);
            out.putArchiveEntry(new ZipArchiveEntry(entry));
            out.write(bytes);
            out.closeArchiveEntry();
        }
        return path;
    }

    public static Path tar(String entry, byte[] bytes) throws IOException {
        Path path = Files.createTempFile("cvfs-oracle-", ".tar");
        try (OutputStream raw = Files.newOutputStream(path);
                TarArchiveOutputStream out = new TarArchiveOutputStream(raw)) {
            putTarEntry(out, entry, bytes);
        }
        return path;
    }

    public static Path tgz(String entry, byte[] bytes) throws IOException {
        Path path = Files.createTempFile("cvfs-oracle-", ".tgz");
        try (OutputStream raw = Files.newOutputStream(path);
                GzipCompressorOutputStream compressed = new GzipCompressorOutputStream(raw);
                TarArchiveOutputStream out = new TarArchiveOutputStream(compressed)) {
            putTarEntry(out, entry, bytes);
        }
        return path;
    }

    public static Path tbz2(String entry, byte[] bytes) throws IOException {
        Path path = Files.createTempFile("cvfs-oracle-", ".tbz2");
        try (OutputStream raw = Files.newOutputStream(path);
                BZip2CompressorOutputStream compressed = new BZip2CompressorOutputStream(raw);
                TarArchiveOutputStream out = new TarArchiveOutputStream(compressed)) {
            putTarEntry(out, entry, bytes);
        }
        return path;
    }

    private static void putTarEntry(TarArchiveOutputStream out, String entry, byte[] bytes) throws IOException {
        TarArchiveEntry archiveEntry = new TarArchiveEntry(entry);
        archiveEntry.setSize(bytes.length);
        out.putArchiveEntry(archiveEntry);
        out.write(bytes);
        out.closeArchiveEntry();
    }

    public static byte[] utf8(String text) {
        return text.getBytes(StandardCharsets.UTF_8);
    }
}
