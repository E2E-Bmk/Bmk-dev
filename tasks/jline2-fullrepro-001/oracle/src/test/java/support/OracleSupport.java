package support;

import jline.TerminalSupport;
import jline.Terminal;
import jline.console.ConsoleReader;
import jline.console.history.History;
import jline.console.history.MemoryHistory;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public final class OracleSupport {
    private OracleSupport() {
    }

    public static Session session(String input) throws Exception {
        return session(input.getBytes(StandardCharsets.UTF_8));
    }

    public static Session session(byte[] input) throws Exception {
        return session(input, new TerminalSupport(true) { });
    }

    public static Session session(String input, Terminal terminal) throws Exception {
        return session(input.getBytes(StandardCharsets.UTF_8), terminal);
    }

    public static Session session(byte[] input, Terminal terminal) throws Exception {
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        ConsoleReader reader = new ConsoleReader(
                new ByteArrayInputStream(input),
                output,
                terminal);
        reader.setExpandEvents(false);
        return new Session(reader, output);
    }

    public static MemoryHistory history(String... values) {
        MemoryHistory history = new MemoryHistory();
        for (String value : values) {
            history.add(value);
        }
        return history;
    }

    public static List<String> values(History history) {
        List<String> values = new ArrayList<String>();
        for (History.Entry entry : history) {
            values.add(entry.value().toString());
        }
        return values;
    }

    public static final class Session {
        public final ConsoleReader reader;
        public final ByteArrayOutputStream output;

        Session(ConsoleReader reader, ByteArrayOutputStream output) {
            this.reader = reader;
            this.output = output;
        }
    }
}


