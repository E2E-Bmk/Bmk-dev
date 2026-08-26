package support;

import java.util.Arrays;
import java.util.List;

/** Shared fixtures for the json-path oracle: the spec's *store* document. */
public final class Json {

    private Json() {
    }

    /** The store document used throughout the specification's examples. */
    public static final String STORE = "{\"store\":{\"book\":["
            + "{\"category\":\"reference\",\"author\":\"Nigel Rees\",\"title\":\"Sayings of the Century\",\"price\":8.95},"
            + "{\"category\":\"fiction\",\"author\":\"Evelyn Waugh\",\"title\":\"Sword of Honour\",\"price\":12.99},"
            + "{\"category\":\"fiction\",\"author\":\"Herman Melville\",\"title\":\"Moby Dick\",\"isbn\":\"0-553-21311-3\",\"price\":8.99},"
            + "{\"category\":\"fiction\",\"author\":\"J. R. R. Tolkien\",\"title\":\"The Lord of the Rings\",\"isbn\":\"0-395-19395-8\",\"price\":22.99}],"
            + "\"bicycle\":{\"color\":\"red\",\"price\":19.95}},\"expensive\":10}";

    public static final List<String> ALL_AUTHORS = Arrays.asList(
            "Nigel Rees", "Evelyn Waugh", "Herman Melville", "J. R. R. Tolkien");

    public static final List<String> ALL_TITLES = Arrays.asList(
            "Sayings of the Century", "Sword of Honour", "Moby Dick", "The Lord of the Rings");
}
