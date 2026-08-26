package support;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/** Shared fixtures and row helpers for the univocity-parsers oracle. */
public final class Csv {

    private Csv() {
    }

    /** The three-column store document used throughout the tests. */
    public static final String PEOPLE = "name,age,city\n\"Smith, John\",30,NYC\nJane,25,\"LA\"\n";

    /** Renders parsed rows compactly for order-sensitive comparison. */
    public static List<List<String>> lists(List<String[]> rows) {
        return rows.stream().map(Arrays::asList).collect(Collectors.toList());
    }

    public static List<String> row(String... values) {
        return Arrays.asList(values);
    }
}
