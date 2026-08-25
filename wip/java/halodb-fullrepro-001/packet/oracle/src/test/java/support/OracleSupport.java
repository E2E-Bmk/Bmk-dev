package support;

import com.oath.halodb.HaloDB;
import com.oath.halodb.HaloDBException;
import com.oath.halodb.HaloDBIterator;
import com.oath.halodb.HaloDBOptions;
import com.oath.halodb.Record;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public final class OracleSupport {
    private OracleSupport() { }

    public static Path directory() throws IOException {
        return Files.createTempDirectory("halodb-oracle-");
    }

    public static HaloDBOptions options() {
        HaloDBOptions options = new HaloDBOptions();
        options.setNumberOfRecords(2048);
        options.setMaxFileSize(16 * 1024);
        options.setCompactionJobRate(1024 * 1024 * 1024);
        return options;
    }

    public static byte[] bytes(int... values) {
        byte[] result = new byte[values.length];
        for (int index = 0; index < values.length; index++) {
            result[index] = (byte) values[index];
        }
        return result;
    }

    public static Map<String, byte[]> records(HaloDB database) throws HaloDBException {
        Map<String, byte[]> found = new HashMap<>();
        HaloDBIterator iterator = database.newIterator();
        while (iterator.hasNext()) {
            Record record = iterator.next();
            found.put(Arrays.toString(record.getKey()), record.getValue());
        }
        return found;
    }

    public static void close(HaloDB database) throws HaloDBException {
        if (database != null) {
            database.close();
        }
    }

    public static void remove(Path directory) throws IOException {
        if (directory == null || !Files.exists(directory)) {
            return;
        }
        Files.walk(directory)
            .sorted((left, right) -> right.compareTo(left))
            .forEach(path -> {
                try {
                    Files.deleteIfExists(path);
                } catch (IOException error) {
                    path.toFile().deleteOnExit();
                }
            });
    }
}
