package support.protocol.data;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.URLConnection;
import java.net.URLDecoder;
import java.net.URLStreamHandler;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

/** Test-runtime data URL transport used to make service resources readable on Java 17. */
public final class Handler extends URLStreamHandler {
    @Override
    protected URLConnection openConnection(URL url) {
        return new URLConnection(url) {
            @Override public void connect() { connected = true; }

            @Override public InputStream getInputStream() throws IOException {
                connect();
                String external = url.toExternalForm();
                int comma = external.indexOf(',');
                if (comma < 0) throw new IOException("Malformed data URL");
                String metadata = external.substring(5, comma);
                String payload = external.substring(comma + 1);
                byte[] bytes = metadata.endsWith(";base64")
                    ? Base64.getDecoder().decode(payload)
                    : URLDecoder.decode(payload, StandardCharsets.UTF_8).getBytes(StandardCharsets.UTF_8);
                return new ByteArrayInputStream(bytes);
            }
        };
    }
}
