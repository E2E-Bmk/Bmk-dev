package oraclesupport;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/** JDK-only builders for documented local PF4J artifact layouts. */
public final class PluginFixtures {
    private PluginFixtures() {}

    public static Path directory(Path root, String id) throws IOException {
        return directory(root, id, RecordingPlugin.class, "1.4.0", "", AlphaGreeting.class, BetaGreeting.class);
    }

    public static Path directory(Path root, String id, Class<?> pluginClass,
            String version, String dependencies, Class<?>... extensions) throws IOException {
        Path plugin = Files.createDirectories(root.resolve(id + "-directory"));
        String properties = properties(id, pluginClass, version, dependencies);
        Files.writeString(plugin.resolve("plugin.properties"), properties, StandardCharsets.UTF_8);
        Path classes = Files.createDirectories(plugin.resolve("classes"));
        copyClass(classes, pluginClass);
        writeExtensions(classes, extensions);
        for (Class<?> extension : extensions) copyClass(classes, extension);
        return plugin;
    }

    public static Path jar(Path root, String id) throws IOException {
        Files.createDirectories(root);
        Path jar = root.resolve(id + "-artifact.jar");
        Manifest manifest = new Manifest();
        Attributes attributes = manifest.getMainAttributes();
        attributes.put(Attributes.Name.MANIFEST_VERSION, "1.0");
        attributes.putValue("Plugin-Id", id);
        attributes.putValue("Plugin-Class", "org.pf4j.Plugin");
        attributes.putValue("Plugin-Version", "1.6.0");
        attributes.putValue("Plugin-Requires", "*");
        attributes.putValue("Plugin-Description", "jar fixture");
        attributes.putValue("Plugin-Provider", "oracle");
        attributes.putValue("Plugin-License", "Apache-2.0");
        try (JarOutputStream out = new JarOutputStream(Files.newOutputStream(jar), manifest)) {
            addClass(out, AlphaGreeting.class);
            addEntry(out, "META-INF/extensions.idx",
                AlphaGreeting.class.getName().getBytes(StandardCharsets.UTF_8));
        }
        return jar;
    }

    public static Path zip(Path root, String id) throws IOException {
        Files.createDirectories(root);
        Path zip = root.resolve(id + "-bundle.zip");
        try (ZipOutputStream out = new ZipOutputStream(Files.newOutputStream(zip))) {
            addEntry(out, "plugin.properties",
                properties(id, org.pf4j.Plugin.class, "1.8.0", "").getBytes(StandardCharsets.UTF_8));
            addClass(out, "classes/", BetaGreeting.class);
            addEntry(out, "classes/META-INF/extensions.idx",
                BetaGreeting.class.getName().getBytes(StandardCharsets.UTF_8));
        }
        return zip;
    }

    private static String properties(String id, Class<?> pluginClass, String version, String dependencies) {
        return "plugin.id=" + id + "\n"
            + "plugin.class=" + pluginClass.getName() + "\n"
            + "plugin.version=" + version + "\n"
            + "plugin.requires=*\n"
            + "plugin.description=fixture " + id + "\n"
            + "plugin.provider=oracle\n"
            + "plugin.license=Apache-2.0\n"
            + "plugin.dependencies=" + dependencies + "\n";
    }

    private static void writeExtensions(Path classes, Class<?>... extensions) throws IOException {
        if (extensions.length == 0) return;
        Path index = classes.resolve("META-INF/extensions.idx");
        Files.createDirectories(index.getParent());
        List<String> names = new ArrayList<>();
        for (Class<?> extension : extensions) names.add(extension.getName());
        Files.write(index, names, StandardCharsets.UTF_8);
    }

    private static void copyClass(Path classes, Class<?> type) throws IOException {
        String resource = type.getName().replace('.', '/') + ".class";
        Path target = classes.resolve(resource);
        Files.createDirectories(target.getParent());
        try (InputStream in = type.getClassLoader().getResourceAsStream(resource)) {
            if (in == null) throw new IOException("missing compiled fixture " + resource);
            Files.copy(in, target);
        }
    }

    private static void addClass(JarOutputStream out, Class<?> type) throws IOException {
        addClass(out, "", type);
    }

    private static void addClass(ZipOutputStream out, String prefix, Class<?> type) throws IOException {
        String resource = type.getName().replace('.', '/') + ".class";
        try (InputStream in = type.getClassLoader().getResourceAsStream(resource)) {
            if (in == null) throw new IOException("missing compiled fixture " + resource);
            addEntry(out, prefix + resource, in.readAllBytes());
        }
    }

    private static void addEntry(ZipOutputStream out, String name, byte[] bytes) throws IOException {
        out.putNextEntry(new ZipEntry(name));
        out.write(bytes);
        out.closeEntry();
    }
}
